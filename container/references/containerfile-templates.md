# Allowlisted Containerfile patterns

Apply the base-image allowlist in this skill's SKILL.md to every stage and external
image source. Examples below are illustrative, not prequalified artifacts. Replace
`<tag>` and `<digest>` with verified values (`<digest>` includes `sha256:`). Check
package/runtime versions against the project's requirements before building.

## Go: Alpine builder → scratch

```dockerfile
FROM docker.io/library/alpine:<tag>@<digest> AS build
RUN apk add --no-cache go ca-certificates tzdata
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -trimpath -ldflags='-s -w' -o /out/app ./cmd/app

FROM scratch AS runtime
COPY --from=build /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt
COPY --from=build --chown=65532:65532 /out/app /app
USER 65532:65532
EXPOSE 8080
ENTRYPOINT ["/app"]
```

Check the packaged Go version and the project's toolchain requirements. This is a
native build; add explicit cross-compilation arguments only after checking builder
support. CGO-dependent apps need a compatible runtime instead of blindly disabling
CGO. Copy zoneinfo or passwd/group data only if the program needs it. Scratch has
no shell: a healthcheck must use a real app subcommand or an external runtime probe.

## Python: matching Alpine stages

```dockerfile
FROM docker.io/library/alpine:<tag>@<digest> AS python-base
RUN apk add --no-cache python3

FROM python-base AS build
RUN apk add --no-cache py3-pip python3-dev build-base
WORKDIR /src
RUN python3 -m venv /venv
COPY requirements.txt ./
RUN /venv/bin/pip install -r requirements.txt
COPY . .
RUN /venv/bin/pip install --no-deps .

FROM python-base AS runtime
COPY --from=build /venv /venv
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
USER 65532:65532
WORKDIR /app
ENTRYPOINT ["/venv/bin/python", "-m", "app"]
```

Use the project's actual lockfile/install procedure. Shared ancestry preserves
interpreter paths and version; still verify native extension libraries and writable
directories. Alpine uses musl: if dependencies require glibc, choose an allowed
glibc base and its package tooling rather than importing a disallowed Python image.

## Other stacks

| Stack | Build/runtime procedure |
| --- | --- |
| Rust | Install Rust/Cargo and the required linker in an allowed builder. Build with the lockfile; verify static linkage before scratch, otherwise retain the required shared-library closure on a compatible allowed base. |
| Node | Install the required Node/npm versions in an allowed base, install from the lockfile, build, then copy production dependencies/output into a matching Node-equipped allowed runtime. Set the entrypoint explicitly; no inherited distroless entrypoint exists. |
| Java | Install a compatible JDK in an allowed builder and use the project wrapper. Use an allowed runtime with a matching JRE, or copy a verified jlink runtime and its system-library dependencies. |
| Static site | Build assets with Node on an allowed builder; install/configure the HTTP server on an allowed runtime. Configure non-root ports and writable pid/cache paths explicitly rather than relying on nginx-unprivileged image defaults. |

For Fedora/UBI/Wolfi, inspect the chosen image's package manager, repositories,
package names, and architectures; do not assume every minimal/micro base provides
the full distribution's package tools. Verify the requested runtime version is
available. If no allowed base satisfies the requirements, report the precise gap
instead of substituting an unlisted base.

## Labels and runtime checks

Set actual project values at build time, including the license the project grants:

```dockerfile
ARG VERSION=dev REVISION=unknown
LABEL org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${REVISION}" \
      org.opencontainers.image.source="https://git.example.com/org/app"
```

Test non-root startup, required filesystem writes, TLS roots, and health commands.
Keep compilers in build/dev stages. Promote the tested artifact instead of rebuilding.
Matching an allowed base alone does not prove ABI compatibility or reproducibility.

## Shared ignore baseline

Use `.dockerignore` when supporting Docker and Podman; Podman prefers a separate
`.containerignore` if present. Adapt exclusions to required build inputs:

```text
.git
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
.idea
.vscode
```

Keep README, manifests, lockfiles, build scripts and assets when packaging needs
them. Exclude generated output only when the build regenerates it inside the image.
