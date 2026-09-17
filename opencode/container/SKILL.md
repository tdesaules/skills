---
name: container
description: |-
  Write, review, and optimize Containerfile/Dockerfile, compose.yaml, and OCI image workflows with podman, buildah, skopeo, nerdctl (multi-stage builds, scratch or distroless final image, rootless, non-root USER, OCI labels, healthcheck). Use when creating or fixing a Containerfile, Dockerfile, .containerignore, compose file, Quadlet unit, `podman build`/`run`, image size, or container hardening.
  Examples:
  - user: "write a Containerfile for this Go service" → multi-stage build, static binary, FROM scratch, numeric USER, OCI labels
  - user: "my image is 1.2 GB, shrink it" → inspect layers, split build/runtime stages, distroless runtime, cache mounts
  - user: "add a compose file for app + postgres" → compose-spec (no version key), healthcheck, depends_on condition, secrets, internal network
license: GPL-3.0-or-later
compatibility: opencode
metadata:
  audience: developers-devops
  workflow: containerfile-compose-build-verify
---

# Container

## What I do

- Write and review `Containerfile`/`Dockerfile` as multi-stage builds whose final stage is `scratch` or distroless whenever the runtime allows it
- Write and review `compose.yaml` against the Compose Specification (services, networks, volumes, configs, secrets, profiles, include)
- Drive builds and images with the daemonless toolchain first: `podman`, `buildah`, `skopeo`, `nerdctl`/containerd; give the `docker` equivalent only when needed
- Harden images and runtime (non-root, read-only rootfs, dropped capabilities, pinned digests, OCI labels, SBOM, signatures)
- Diagnose build failures, cache misses, oversized images, and startup/health issues with evidence from the tools

## When to use me

Use me when creating or fixing a Containerfile, Dockerfile, `.containerignore`/`.dockerignore`, compose file, Podman Quadlet unit, or when running/inspecting images with podman, buildah, skopeo, nerdctl, or docker.
Use ONLY for OCI images, build files, compose, and single-host runtimes. Not for Kubernetes manifests or Helm charts (load the `helm` skill), not for CI pipeline YAML beyond the build/push commands.
Ask clarifying questions when the language/runtime of the app, the target platforms, or the intended orchestrator (compose vs Quadlet vs Kubernetes) is unclear.

## Tool preference

| Task              | Preferred (daemonless, rootless)             | Docker equivalent            |
| ----------------- | -------------------------------------------- | ---------------------------- |
| Build             | `podman build` / `buildah build`             | `docker build` / `buildx`    |
| Run               | `podman run`                                 | `docker run`                 |
| Compose           | `podman compose` (delegates to `docker-compose`/`podman-compose`) | `docker compose` |
| Copy/inspect/sync | `skopeo copy|inspect|sync|list-tags`         | `docker pull|push|inspect`   |
| containerd hosts  | `nerdctl build|run|compose` (`ctr` for debug only) | `docker`               |
| Multi-arch        | `podman build --platform a,b --manifest`, `podman manifest push` | `buildx --platform` |
| Services on host  | Quadlet (`.container`, `.pod`, `.network`, `.volume`) | compose + restart policy |

Detect the engine before proposing commands: `command -v podman buildah skopeo nerdctl docker`; `podman info --format '{{.Host.Security.Rootless}} {{.Store.GraphDriverName}}'`. On a machine where `docker` is a podman alias, write `podman`.
Use Docker when a feature is Docker-only and required: BuildKit-exclusive frontends (`# syntax=` directives beyond what buildah accepts), Compose Deploy/Swarm semantics, Docker Scout. State the reason.

## Workflow

1. **Inspect.** Locate `Containerfile*`, `Dockerfile*`, `compose*.y*ml`, `.containerignore`/`.dockerignore`, Quadlet files (`*.container`, `~/.config/containers/systemd/`). Read the app's build system (go.mod, Cargo.toml, package.json, pyproject.toml, pom.xml) to determine runtime needs: static binary, dynamic libs, interpreter, TLS roots, timezone data, shell.
2. **Classify.** New build file / review existing / debug failure / compose stack / runtime hardening / image distribution. Handle one at a time.
3. **Decide the final base** with the tree below, then write stages.
4. **Apply** the Containerfile and compose rules. Keep a `.containerignore`.
5. **Validate** with commands, not by reading:
   - `podman build --pull=newer -t app:dev .` (build succeeds) and `podman build --target <stage>` for intermediate stages
   - `podman image inspect app:dev --format '{{.Size}} {{.User}} {{.Config.Entrypoint}} {{.Config.Cmd}} {{.Config.Labels}}'`
   - `podman image tree app:dev` and `podman history --no-trunc app:dev` (layer sizes, leaked secrets in history)
   - `podman run --rm app:dev <smoke command>`; `podman run --rm -d --name t app:dev && sleep 5 && podman healthcheck run t && podman logs t; podman rm -f t`
   - `podman compose config` (or `podman compose -f compose.yaml config --quiet`) for compose validity
   - `skopeo inspect docker://<ref>` before pulling a base; `skopeo inspect --raw docker://<ref> | jq .manifests[].platform` for multi-arch
   - Optional if installed: `hadolint Containerfile`, `trivy image app:dev`, `podman build --sbom=syft ...`
6. **Report** each finding as `file:line` → rule → consequence → fix. Do not claim "validated" without pasting the command output.

## Final base image decision

Pick the smallest base that runs the artifact. Justify any step down the list.

1. **`scratch`** — static binaries: Go (`CGO_ENABLED=0 go build -trimpath -ldflags='-s -w'`), Rust (`--target x86_64-unknown-linux-musl`), Zig, C with `-static`. Copy in from the build stage: the binary, `/etc/ssl/certs/ca-certificates.crt` if it makes TLS calls, `/usr/share/zoneinfo` if it needs local time, a minimal `/etc/passwd`+`/etc/group` line for a numeric non-root user. No shell → `HEALTHCHECK` must use the binary itself (`--health-cmd ["/app","healthz"]`) or be set by the orchestrator.
2. **Distroless** (`gcr.io/distroless/*`, prefer `:nonroot` or `-debian12:nonroot`): `static` (like scratch + certs + tzdata + passwd), `base` (glibc, libssl), `cc` (libgcc, for Rust/C++ dynamic), `java21`, `nodejs22`, `python3`. Alternatives with the same intent: `cgr.dev/chainguard/*` (Wolfi), `registry.access.redhat.com/ubi9/ubi-micro`.
3. **Minimal distro** (`debian:*-slim`, `alpine:*`, `ubi9-minimal`) — only when the runtime needs a package manager, a shell for an entrypoint script, or a libc the app cannot avoid. Note musl vs glibc pitfalls for Python wheels and Node native modules.
4. **Full distro** — reject unless the user gives a reason (debugging image, dev container); tag it distinctly.

Never end a production image with the build toolchain (compilers, SDKs, `git`, `curl`) present. If a build stage needs a package manager, keep it in that stage.

## Containerfile rules

Layout (top to bottom):

```dockerfile
# syntax=docker/dockerfile:1        # optional; buildah ignores unknown frontends safely
ARG GO_VERSION=1.23
FROM docker.io/library/golang:${GO_VERSION}-bookworm@sha256:<digest> AS build
WORKDIR /src
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=bind,source=go.sum,target=go.sum,z \
    --mount=type=bind,source=go.mod,target=go.mod,z \
    go mod download -x
COPY . .
ARG TARGETOS TARGETARCH
RUN --mount=type=cache,target=/go/pkg/mod --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 GOOS=$TARGETOS GOARCH=$TARGETARCH go build -trimpath -ldflags='-s -w' -o /out/app ./cmd/app

FROM scratch AS runtime
COPY --from=build /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=build --chown=65532:65532 /out/app /app
USER 65532:65532
EXPOSE 8080
ENTRYPOINT ["/app"]
LABEL org.opencontainers.image.source="https://example.com/repo" \
      org.opencontainers.image.licenses="MIT"
```

- **FROM**: fully qualified (`docker.io/library/...`, `registry.access.redhat.com/...`) so podman does not depend on `registries.conf` short-name resolution; pin `tag@sha256:...` for production (resolve with `skopeo inspect --format '{{.Digest}}' docker://ref`). Name every stage with `AS`. Only `ARG` may precede the first `FROM`; `ARG`s declared before `FROM` are out of scope inside stages unless redeclared.
- **Order for cache**: install dependencies from lockfiles before copying the source tree; copy the least-changing files first. Use `--mount=type=cache` for package caches (`/go/pkg/mod`, `/root/.npm`, `/root/.cache/pip`, `/usr/local/cargo/registry`, `/var/cache/apt`), `--mount=type=bind` for read-only inputs used by a single `RUN`, `--mount=type=secret,id=...` for tokens (never `ARG`/`ENV` for secrets: they persist in `podman history`). On SELinux-enforcing hosts (`getenforce`), bind mounts from the context need `,z` (`--mount=type=bind,source=go.mod,target=go.mod,z`) or the step fails with `permission denied`; docker ignores the flag, so it is safe to keep.
- **RUN**: one logical step per instruction; chain with `&&` and `\`; `set -eux` (or `set -o pipefail` when piping, with a shell that supports it: `RUN ["/bin/bash","-c","set -o pipefail && ..."]`); heredocs `RUN <<EOF ... EOF` for multi-command steps. `apt-get update && apt-get install -y --no-install-recommends pkg=ver && rm -rf /var/lib/apt/lists/*` in the same layer. Sort package lists alphabetically. `RUN --network=none` when everything is vendored, for reproducibility.
- **COPY over ADD**; `ADD` only for remote URLs with `--checksum=sha256:...` or local tar extraction. `COPY --from=<stage>` and `--chown=<uid>:<gid>` (numeric) for runtime artifacts. `COPY --chmod=` instead of a later `RUN chmod`.
- **USER**: numeric `uid:gid` (`65532:65532` matches distroless `nonroot`; `1001` for OpenShift-friendly arbitrary UID). Create the user in the build stage or copy a one-line `/etc/passwd`; add `--no-log-init` to `useradd` (large UID sparse-file bug). Put `USER` after every root-only step and before `ENTRYPOINT`. Do not use `sudo`/`gosu` in the final stage unless an init-as-root-then-drop pattern is required and stated.
- **WORKDIR** absolute; never `RUN cd`.
- **ENTRYPOINT** exec form (JSON array) for the binary; **CMD** exec form for default args. Shell form (`ENTRYPOINT app`) wraps in `/bin/sh -c` → PID 1 is `sh`, signals are not forwarded, and scratch/distroless has no `sh`. Use `--init`/`init: true` or `tini` only when the app spawns children it does not reap.
- **HEALTHCHECK** `--interval --timeout --start-period --retries CMD [...]` with a binary present in the final image (`["/app","healthz"]`, `["/usr/bin/wget","-qO-","http://127.0.0.1:8080/healthz"]`); without shell, avoid `CMD-SHELL`. The OCI image format has no healthcheck field: `podman build` (default `--format oci`) drops it with a warning; pass `--format docker` when the check must ship in the image, otherwise define it in compose/Quadlet (`healthcheck:` / `HealthCmd=`). Kubernetes ignores it either way (use probes).
- **EXPOSE** documents ports; publishing is `-p`/`ports:`.
- **ENV** only for runtime configuration that must persist (PATH, `PGDATA`, `NODE_ENV=production`); never for build-only values (use `ARG`) or secrets. Remember `ENV` layers survive later `unset`.
- **LABEL**: use the OCI namespace `org.opencontainers.image.{title,description,version,revision,created,source,url,documentation,vendor,licenses,authors,base.name,base.digest}`; `created`/`revision`/`version` come from `--build-arg` or `--label` at build time, not hardcoded. `org.label-schema.*` is superseded.
- **Multi-arch**: declare `ARG TARGETOS TARGETARCH TARGETPLATFORM BUILDPLATFORM` inside the stage that uses them (podman does not auto-populate). Cross-compile in the build stage (`FROM --platform=$BUILDPLATFORM ... AS build`) rather than emulate. Publish with `podman build --platform linux/amd64,linux/arm64 --manifest reg/app:tag . && podman manifest push --all reg/app:tag`.
- **Reproducibility**: `podman build --timestamp 0` / `--source-date-epoch`, `--omit-history` when history leaks paths; pin digests and package versions; `--no-cache --pull` for a clean rebuild.
- **`.containerignore`** (podman prefers it over `.dockerignore` if both exist): `.git`, `**/node_modules`, `target/`, `dist/`, `*.md`, `compose*.y*ml`, `Containerfile*`, `.env*`, IDE dirs, test fixtures. Both files use the same syntax; keep one.

## Compose rules (Compose Specification)

- **No `version:` key** (obsolete; a warning at best). Set top-level `name:` for a stable project name (resources are prefixed by it and labeled `com.docker.compose.project`).
- **`image:` fully qualified with tag or digest**; when `build:` is present too, `pull_policy: build` (or `missing`) decides. Use `build.target:` to pick the runtime stage and `build.args`/`build.secrets`/`build.cache_from`/`build.platforms` instead of shell wrappers.
- **Startup order**: `depends_on` long form with `condition: service_healthy` (needs `healthcheck` on the dependency) or `service_completed_successfully` for migrations; `restart: true` to restart dependents on dependency update. Short form only orders creation.
- **`healthcheck`**: `test: ["CMD", ...]` when the image has no shell, `CMD-SHELL` otherwise; set `interval`, `timeout`, `retries`, `start_period`, `start_interval`. Disable an image's check with `disable: true` only deliberately.
- **Hardening per service**: `user: "65532:65532"`, `read_only: true` + `tmpfs: [/tmp, /run]`, `cap_drop: [ALL]` then `cap_add` the minimum (`NET_BIND_SERVICE`), `security_opt: ["no-new-privileges:true"]`, `init: true` when needed, `pids_limit`, `mem_limit`/`cpus` (or `deploy.resources.limits` when the platform honors `deploy`). `privileged: true` and `network_mode: host` require a stated reason.
- **Networks**: define named networks; put databases on a back-tier network with `internal: true`; only edge services on the front tier and only they get `ports:`. Use `expose:` for inter-service ports. Service names are DNS names; add `aliases` when a client expects another hostname.
- **Data**: named `volumes:` for state; bind mounts (`type: bind`) only for dev source or host config; add `:Z`/`:z` (or `bind.selinux`) on SELinux hosts. Never store state in the container layer.
- **Config and secrets**: `configs:` for files rendered from the repo (`file:` or `content:` inline), `secrets:` for credentials (`file:` or `environment:`), mounted at `/run/secrets/<name>`; prefer `*_FILE` env vars supported by the image (`POSTGRES_PASSWORD_FILE`) over passing secrets in `environment:`. `.env` is for interpolation (`${VAR:-default}`, `${VAR:?required}`), not for shipping secrets; commit `.env.example` only.
- **Environments**: one `compose.yaml` plus `compose.override.yaml` (auto-merged) for dev; `profiles: [debug]` for optional services (`--profile debug`); `include:` to split large stacks; `extends:` for shared service fragments; `x-` extension fields with YAML anchors (`x-common: &common ...`, `<<: *common`) for repeated blocks.
- **Dev loop**: `develop.watch` (`sync`, `rebuild`, `sync+restart`) instead of bind-mounting the whole tree when the runtime image has no toolchain.
- **Podman specifics**: `podman compose` shells out to `docker-compose` or `podman-compose`; rootless port < 1024 needs `sysctl net.ipv4.ip_unprivileged_port_start`; `userns_mode: keep-id` to match host UID on bind mounts. For long-running services on a single host prefer Quadlet units (systemd-managed, `AutoUpdate=registry`, `podman auto-update`) over `restart: always`.
- Validate with `podman compose config` and start with `podman compose up -d --wait` (returns when healthchecks pass).

## Runtime and distribution

- **Rootless first**: `podman run` as a regular user; `--userns=keep-id` for bind mounts owned by the host user; `--userns=auto` for isolation. Volume labels `:Z` (private) / `:z` (shared) on SELinux.
- **Run flags mirroring compose hardening**: `--read-only --tmpfs /tmp --cap-drop=ALL --security-opt=no-new-privileges --user 65532:65532 --pids-limit 256 --memory 512m --health-cmd ...`.
- **Quadlet** (`~/.config/containers/systemd/app.container` rootless, `/etc/containers/systemd/` root): `[Container] Image=... PublishPort= Volume=name.volume:/data:Z Network=app.network HealthCmd= AutoUpdate=registry`, `[Service] Restart=on-failure`, `[Install] WantedBy=default.target`; then `systemctl --user daemon-reload && systemctl --user start app`. Debug with `/usr/lib/systemd/system-generators/podman-system-generator --user --dryrun`.
- **Kubernetes bridge**: `podman kube generate <ctr|pod> > pod.yaml`, `podman kube play pod.yaml`; hand-off to `helm` skill for charts.
- **Registry ops without a daemon**: `skopeo copy docker://src docker://dst` (`--all` for every platform, `--preserve-digests`), `skopeo sync` for mirrors/air-gap (`--dest dir`), `skopeo list-tags`, `skopeo inspect --config`, `skopeo delete`. Login via `podman login` (auth in `$XDG_RUNTIME_DIR/containers/auth.json`).
- **Supply chain**: `podman build --sbom=syft --sbom-output sbom.json`, `podman image sign`/`podman push --sign-by-sigstore-private-key`, verify with `policy.json` + `registries.d`; `cosign sign|verify` where the org uses sigstore. Pin base digests; rebuild on schedule (`--pull=newer`).
- **Export/import**: `podman save --format oci-archive`, `podman load`, `podman build --output type=local,dest=out` to extract artifacts from a stage.

## Review checklist

Each finding needs `file:line`, the violated rule, the consequence, and the fix.

Containerfile:
- [ ] Multi-stage; final stage is scratch/distroless or justified
- [ ] Every `FROM` fully qualified, tagged, digest-pinned for prod; stages named
- [ ] Dependency layers before source copy; cache mounts for package managers
- [ ] No secret via `ARG`/`ENV`/`COPY`; `--mount=type=secret` where needed
- [ ] `USER` numeric non-root before `ENTRYPOINT`; files `--chown`ed accordingly
- [ ] `ENTRYPOINT`/`CMD` exec form; no shell form on shell-less bases
- [ ] `HEALTHCHECK` present and runnable in the final image (or explicitly delegated to the orchestrator)
- [ ] `apt/apk/dnf` install + cleanup in one layer, `--no-install-recommends`, versions pinned
- [ ] OCI `org.opencontainers.image.*` labels; no `MAINTAINER`
- [ ] `.containerignore` excludes VCS, deps, build output, env files
- [ ] `TARGETARCH` declared where used; cross-compile instead of emulation

Compose:
- [ ] No `version:`; `name:` set
- [ ] `depends_on` long form with conditions; healthchecks on dependencies
- [ ] `user`, `read_only`, `cap_drop: [ALL]`, `no-new-privileges`, resource limits
- [ ] Back-tier `internal: true`; `ports:` only on edge services
- [ ] Named volumes for state; SELinux labels on bind mounts
- [ ] Secrets via `secrets:`/`*_FILE`, not `environment:`
- [ ] `podman compose config` passes

## Anti-patterns

- `FROM node:latest` / `FROM ubuntu` untagged, short names relying on registry search.
- Single-stage image shipping compilers, `git`, `curl`, test files.
- `COPY . .` before dependency install (cache busts on every edit); no ignore file.
- `RUN apt-get update` in its own layer; `apt-get upgrade` in images.
- `ENV TOKEN=...`, `ARG PASSWORD`, `COPY .env /app/.env`.
- Running as root "because it works"; `chmod -R 777`.
- `CMD service nginx start` (daemonizes, container exits); shell-form entrypoints on scratch.
- `HEALTHCHECK CMD curl ...` on an image without `curl`.
- `version: "3.8"` in compose; `links:`; `depends_on` short form to wait for a DB; `restart: always` as a substitute for a healthcheck.
- `privileged: true`, `network_mode: host`, mounting `/var/run/docker.sock` without a stated reason.
- Suggesting `docker` commands on a podman host, or `docker-compose` v1 syntax.

## References

Read on demand:

- `references/containerfile-templates.md` — vetted multi-stage templates per stack (Go, Rust, Node, Python, Java, static site) and a `.containerignore` baseline. Read when writing a new Containerfile.
- `references/compose-templates.md` — hardened app + database stack, dev override, profiles, Quadlet equivalent. Read when writing a compose file or Quadlet unit.
- `references/cli-cheatsheet.md` — podman/buildah/skopeo/nerdctl ↔ docker mapping, debugging recipes, multi-arch and registry workflows. Read when the user asks for commands or a build fails.

Specs and docs:

- Containerfile(5): https://github.com/containers/common/blob/main/docs/Containerfile.5.md
- containerignore(5): https://github.com/containers/common/blob/main/docs/containerignore.5.md
- OCI image spec annotations: https://github.com/opencontainers/image-spec/blob/main/annotations.md
- Docker build best practices: https://docs.docker.com/build/building/best-practices/
- podman-build(1): https://docs.podman.io/en/latest/markdown/podman-build.1.html
- podman-systemd.unit(5) (Quadlet): https://docs.podman.io/en/latest/markdown/podman-systemd.unit.5.html
- Buildah: https://github.com/containers/buildah/tree/main/docs
- Skopeo: https://github.com/containers/skopeo/tree/main/docs
- containerd / nerdctl: https://github.com/containerd/containerd/tree/main/docs, https://github.com/containerd/nerdctl
- Compose Specification: https://github.com/compose-spec/compose-spec/blob/main/spec.md
- Distroless: https://github.com/GoogleContainerTools/distroless
