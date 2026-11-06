---
name: container
description: >-
  Use when creating, reviewing, or debugging Containerfile/Dockerfile builds,
  compose.yaml stacks, OCI images, or Podman Quadlet services. Diagnose oversized
  images, cache misses, startup failures, permissions, and multi-platform builds.
  Covers container build/runtime work, not Helm charts or GitHub workflow routing.
license: GPL-3.0-or-later
compatibility: Requires a compatible container engine; Podman preferred when no engine is prescribed. Registry operations require network access.
---

# OCI containers

## Scope and defaults

Build and operate images and single-host stacks. Use the repository's existing
engine; default to rootless Podman when choosing a new one. Detect tool versions
and the Compose provider before using engine-specific flags. Do not replace a
working Docker/containerd setup solely to apply a preference.

## Base-image allowlist

Use only these base repositories for new or changed image builds, in **every
stage**, including builders, development, test, and runtime stages:

| Allowed base | Reference |
| --- | --- |
| `quay.io/fedora/fedora-minimal` | https://quay.io/repository/fedora/fedora-minimal |
| `quay.io/fedora/fedora` | https://quay.io/repository/fedora/fedora |
| `scratch` | https://hub.docker.com/_/scratch |
| `docker.io/library/alpine` | https://hub.docker.com/_/alpine |
| `docker.io/chainguard/wolfi-base` | https://hub.docker.com/r/chainguard/wolfi-base |
| `docker.io/redhat/ubi10-micro` | https://hub.docker.com/r/redhat/ubi10-micro |
| `docker.io/redhat/ubi10-minimal` | https://hub.docker.com/r/redhat/ubi10-minimal |

This is a collection policy, not an OCI requirement. Match exact repository names,
not registry-wide prefixes; tags/digests must resolve within the allowed repository.
Use `FROM scratch` literally: it is an empty base, not a pullable/tagged image.
Resolve supported tags, digests and architectures rather than assuming availability.

Install required toolchains/runtimes into an allowed base instead of using official
language images or distroless. Choose scratch for a verified static closure; otherwise
select an allowed base with compatible libc, packages, and runtime dependencies.
Full Fedora is allowed when build/debug needs justify it. Micro images may lack a
package manager: assemble their runtime closure in a compatible build stage.

Check external `COPY --from=<image>` and image-backed mounts too; do not bypass the
list with an unapproved donor image. Named local stages may inherit approved stages.
For project-derived images, verify the recipe/provenance resolves to allowed bases.

The list governs bases, not the names of resulting application images. Compose,
Quadlet, Helm workloads and prebuilt CI tools still need their application software.
Do not substitute a bare base for PostgreSQL or a linter. Report existing unlisted
bases or unknown provenance; propose a compatible rebuild rather than silently
treating them as approved. Only an explicit user exception can widen this list.

## Workflow

1. Inspect build files, lockfiles, ignore rules, compose/Quadlet definitions, and
   app startup behavior. Identify platforms, dynamic libraries, interpreter, TLS
   roots, timezone data, filesystem writes, and health endpoints.
2. Classify the actual task and preserve working interfaces. For builds, choose
   the smallest allowed base that satisfies those requirements; apply the allowlist
   to build stages and external image sources as well as the runtime.
   A dev/debug image may legitimately retain a toolchain.
3. Write named build stages; install dependencies from lockfiles before copying
   source. Keep build-only tooling and credentials out of the runtime. Use secret
   mounts rather than secret ARG/ENV/COPY instructions.
4. Use exec-form entrypoints, a tested non-root UID, appropriate ownership, and
   explicit writable paths. Choose hardening based on the app, not a blanket
   `read_only` setting that prevents startup.
5. Resolve actual base tags/digests and platforms when reproducibility is required.
   Never fabricate digests or transplant a template's old runtime version blindly.
6. Build and run a task-relevant smoke check. Inspect image configuration/history,
   test writable paths and health behavior, and validate compose with the installed
   provider. Test the actual target architectures for multi-platform work.
7. Compare results to the requested outcome: size, startup, output, permissions,
   or reproducibility. Report base-image policy compliance and unknown provenance;
   distinguish this from an actual build/smoke-test result.

## Gotchas

- A `# syntax=` frontend or `RUN --mount` option supported by BuildKit may be
  rejected or behave differently in Buildah. Do not assume options are ignored.
  Prefer portable `COPY` for lockfiles; use SELinux options only where supported.
- BuildKit automatic platform arguments are builder-specific. Inspect support and
  supply explicit build args when cross-compiling; declaring an ARG alone is not
  proof it has the intended value. Do not mix host-architecture dependencies into
  target binaries.
- A venv copied from another image needs the same interpreter ABI, executable path,
  and system libraries. Matching the distro name alone is insufficient.
- Scratch has no shell or curl. Health commands must exist in the final image.
  OCI format does not standardize Docker HEALTHCHECK; with Podman use Docker image
  format if the embedded check must survive, or declare it in the runtime/orchestrator.
- Docker reads `.dockerignore`; Podman prefers `.containerignore` when both exist.
  Use `.dockerignore` for a shared baseline and avoid accidentally excluding build
  inputs such as README files needed by package metadata.
- Compose `depends_on` short form orders startup, not readiness. Use health or
  successful-completion conditions when required and confirm provider support.
- Compose `command` replaces CMD, not ENTRYPOINT. With `ENTRYPOINT ["/app"]`, use
  `command: ["migrate"]`, not `["/app", "migrate"]`.
- Rootless bind mounts involve both UID mapping and SELinux labels. Diagnose both;
  do not fix them with recursive chmod 777 or broad privileges.
- Jobs/hosts do not share an image store. Promote exact tested archives/digests;
  preserve all manifests for multi-platform copies.

## References to load on demand

- [Build templates](references/containerfile-templates.md): when writing a build;
  illustrative patterns, not prequalified images.
- [Compose and Quadlet](references/compose-templates.md): for stack/service setup;
  adapt the image entrypoint, data ownership, and provider capabilities.
- [CLI recipes](references/cli-cheatsheet.md): for engine operations and debugging.

## Validation and output

For Podman, start with `podman build -t app:dev .`,
`podman image inspect app:dev`, and an application-specific `podman run --rm`
smoke command. Use the installed engine's equivalent where appropriate. For a
service, wait on bounded readiness and always clean up only the test resources
created by this task. Run `podman compose config` or `docker compose config` for
stack edits; a parsed configuration is not evidence of healthy startup.

Return changed paths, relevant commands/results, and unresolved runtime needs.
For reviews use `file:line → defect → consequence → correction`. Treat hardening
preferences as recommendations unless the target's contract makes them required.

Sources:

- https://docs.podman.io/en/latest/markdown/podman-build.1.html
- https://docs.docker.com/build/building/best-practices/
- https://github.com/compose-spec/compose-spec/blob/main/spec.md
