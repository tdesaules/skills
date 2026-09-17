# Containerfile templates

Vetted multi-stage patterns. Replace `<digest>` with `skopeo inspect --format '{{.Digest}}' docker://<image:tag>`. All final stages run as UID 65532 (`nonroot` in distroless) unless noted. Adjust `EXPOSE`, entrypoint, and healthcheck to the app.

Shared tail for every template (labels are set at build time):

```dockerfile
ARG VERSION=dev REVISION=unknown CREATED=1970-01-01T00:00:00Z
LABEL org.opencontainers.image.title="app" \
      org.opencontainers.image.description="..." \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${REVISION}" \
      org.opencontainers.image.created="${CREATED}" \
      org.opencontainers.image.source="https://git.example.com/org/app" \
      org.opencontainers.image.licenses="Apache-2.0"
```

Build with: `podman build --build-arg VERSION=$(git describe --tags --always) --build-arg REVISION=$(git rev-parse HEAD) --build-arg CREATED=$(date -u +%Y-%m-%dT%H:%M:%SZ) -t app:dev .`

## Go → scratch

```dockerfile
ARG GO_VERSION=1.23
FROM --platform=$BUILDPLATFORM docker.io/library/golang:${GO_VERSION}-bookworm@<digest> AS build
WORKDIR /src
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=bind,source=go.mod,target=go.mod,z \
    --mount=type=bind,source=go.sum,target=go.sum,z \
    go mod download -x
COPY . .
ARG TARGETOS TARGETARCH
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 GOOS=${TARGETOS} GOARCH=${TARGETARCH} \
    go build -trimpath -ldflags='-s -w -buildid=' -o /out/app ./cmd/app
RUN echo 'nonroot:x:65532:65532:nonroot:/:/sbin/nologin' > /out/passwd && \
    echo 'nonroot:x:65532:' > /out/group

FROM scratch AS runtime
COPY --from=build /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=build /usr/share/zoneinfo /usr/share/zoneinfo
COPY --from=build /out/passwd /etc/passwd
COPY --from=build /out/group /etc/group
COPY --from=build --chown=65532:65532 /out/app /app
USER 65532:65532
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 CMD ["/app", "healthz"]
ENTRYPOINT ["/app"]
```

Notes: `-buildid=` plus `--timestamp 0` gives reproducible layers. If the app needs `time.LoadLocation`, keep zoneinfo; otherwise drop it. `HEALTHCHECK` requires a `healthz` subcommand in the binary; otherwise remove and rely on orchestrator probes. Verified with podman 5.8 / buildah 1.43 on SELinux: builds to a 5.8 MB image, runs as UID 65532; `HEALTHCHECK` only survives with `podman build --format docker`.

## Rust → scratch (musl) or distroless/cc (glibc)

```dockerfile
ARG RUST_VERSION=1.82
FROM docker.io/library/rust:${RUST_VERSION}-bookworm@<digest> AS build
RUN rustup target add x86_64-unknown-linux-musl
WORKDIR /src
COPY Cargo.toml Cargo.lock ./
RUN mkdir src && echo 'fn main(){}' > src/main.rs && \
    --mount=type=cache,target=/usr/local/cargo/registry \
    cargo build --release --target x86_64-unknown-linux-musl && rm -rf src
COPY src ./src
RUN --mount=type=cache,target=/usr/local/cargo/registry \
    --mount=type=cache,target=/src/target \
    cargo build --release --target x86_64-unknown-linux-musl && \
    cp target/x86_64-unknown-linux-musl/release/app /out-app

FROM scratch AS runtime
COPY --from=build /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=build --chown=65532:65532 /out-app /app
USER 65532:65532
ENTRYPOINT ["/app"]
```

When crates need glibc/OpenSSL (`openssl-sys` without `vendored`), build for the default target and use `FROM gcr.io/distroless/cc-debian12:nonroot` instead of scratch. For multi-arch, map `TARGETARCH` to the Rust triple in a small `case` statement.

## Node → distroless/nodejs

```dockerfile
ARG NODE_VERSION=22
FROM docker.io/library/node:${NODE_VERSION}-bookworm-slim@<digest> AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --omit=dev --ignore-scripts

FROM deps AS build
RUN --mount=type=cache,target=/root/.npm npm ci --ignore-scripts
COPY . .
RUN npm run build && npm prune --omit=dev

FROM gcr.io/distroless/nodejs${NODE_VERSION}-debian12:nonroot AS runtime
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build --chown=65532:65532 /app/node_modules ./node_modules
COPY --from=build --chown=65532:65532 /app/dist ./dist
COPY --from=build --chown=65532:65532 /app/package.json ./
USER 65532:65532
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD ["/nodejs/bin/node", "dist/healthz.js"]
CMD ["dist/index.js"]
```

Notes: distroless nodejs sets `ENTRYPOINT ["/nodejs/bin/node"]`, so `CMD` holds the script. Native modules compiled against glibc work; alpine-built ones do not. Use `pnpm fetch`/`pnpm install --frozen-lockfile --prod` variants with the same stage split.

## Python → distroless/python3 (venv)

```dockerfile
ARG PY_VERSION=3.12
FROM docker.io/library/python:${PY_VERSION}-slim-bookworm@<digest> AS build
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=0
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
WORKDIR /src
RUN python -m venv /venv
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip /venv/bin/pip install -r requirements.txt
COPY . .
RUN /venv/bin/pip install --no-deps .

FROM gcr.io/distroless/python3-debian12:nonroot AS runtime
COPY --from=build --chown=65532:65532 /venv /venv
ENV PATH=/venv/bin:$PATH PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
USER 65532:65532
EXPOSE 8000
ENTRYPOINT ["/venv/bin/python", "-m", "app"]
```

Notes: the venv's `python` symlink points at the distroless interpreter only if the minor version matches (`3.12` here matches distroless debian12). Prefer `uv` (`uv sync --frozen --no-dev`, `UV_PROJECT_ENVIRONMENT=/venv`) when the project uses it. Packages with compiled extensions requiring system libs (psycopg2 non-binary, lxml) need `distroless/base` plus copying `.so` files, or `python:*-slim` as a documented step down.

## Java → distroless/java or jlink runtime

```dockerfile
ARG JDK_VERSION=21
FROM docker.io/eclipse-temurin:${JDK_VERSION}-jdk-jammy@<digest> AS build
WORKDIR /src
COPY mvnw pom.xml ./
COPY .mvn .mvn
RUN --mount=type=cache,target=/root/.m2 ./mvnw -B -q dependency:go-offline
COPY src ./src
RUN --mount=type=cache,target=/root/.m2 ./mvnw -B -q package -DskipTests && \
    mv target/*.jar /app.jar

FROM gcr.io/distroless/java${JDK_VERSION}-debian12:nonroot AS runtime
WORKDIR /app
COPY --from=build --chown=65532:65532 /app.jar ./app.jar
USER 65532:65532
EXPOSE 8080
ENV JAVA_TOOL_OPTIONS="-XX:MaxRAMPercentage=75 -XX:+ExitOnOutOfMemoryError"
CMD ["app.jar"]
```

Notes: distroless java sets `ENTRYPOINT ["/usr/bin/java","-jar"]`. For a smaller image, run `jlink --add-modules $(jdeps --print-module-deps app.jar) --strip-debug --no-man-pages --no-header-files --compress=zip-6 --output /jre` in the build stage and copy `/jre` onto `distroless/base-debian12:nonroot`. Spring Boot: extract layers (`java -Djarmode=layertools -jar app.jar extract`) and copy `dependencies/`, `spring-boot-loader/`, `snapshot-dependencies/`, `application/` as separate `COPY` layers.

## Static site → nginx-unprivileged

```dockerfile
FROM docker.io/library/node:22-bookworm-slim@<digest> AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --ignore-scripts
COPY . .
RUN npm run build

FROM docker.io/nginxinc/nginx-unprivileged:1.27-alpine@<digest> AS runtime
COPY --from=build --chown=101:101 /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
USER 101
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD ["/usr/bin/wget", "-qO-", "http://127.0.0.1:8080/"]
```

Notes: `nginx-unprivileged` listens on 8080 and runs as UID 101; keep `pid /tmp/nginx.pid` defaults. For `read_only: true` mount tmpfs on `/tmp` and `/var/cache/nginx`.

## Dev stage variant

Add a `dev` stage sharing the deps stage, selected with `--target dev` / `build.target: dev`, to keep toolchain and hot reload out of the runtime image:

```dockerfile
FROM deps AS dev
RUN --mount=type=cache,target=/root/.npm npm ci
CMD ["npm", "run", "dev"]
```

## `.containerignore` baseline

```
.git
.gitignore
.github
**/.env
**/.env.*
!**/.env.example
**/node_modules
**/__pycache__
**/*.pyc
target/
dist/
build/
coverage/
*.md
!README.md
Containerfile*
Dockerfile*
compose*.y*ml
.containerignore
.dockerignore
.idea
.vscode
*.swp
```

Keep exactly one of `.containerignore`/`.dockerignore` (podman uses `.containerignore` when both exist; docker only reads `.dockerignore`). Symlink one to the other if both engines are used.
