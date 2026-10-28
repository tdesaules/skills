---
name: github-actions
description: |
  GitHub Actions workflows and action.yml authoring, review, and troubleshooting: native Docker container actions, dedicated multistage scratch images on GHCR, change detection, separate build/test matrices, releases, and permissions. Applies when implementing or reviewing GitHub CI/CD orchestration or a shared action catalog; not standalone Containerfiles or GitLab CI.
  Examples:
  - user: "share a linter using my OCI image" → native Docker action with its own image pinned by digest
  - user: "build only changed images with a matrix" → source-derived selection, empty matrices and artifact transfer
  - user: "prepare a release then push its tag" → version calculation, immutable image references, trigger credentials and race checks
  - user: "why was this job skipped" → inspect event filters, needs results and job/step conditions
license: GPL-3.0-or-later
compatibility: opencode
---

## What I do

- Design and implement GitHub workflows and reusable actions with precise responsibilities.
- Package each specialized operation as a native Docker action with its own OCI image.
- Select checks/builds from changed files and separate construction from native qualification.
- Coordinate image publication, SBOMs, signatures, catalog versions, and GitHub Releases.
- Review event routing, dependency conditions, permissions, artifacts, and bootstrap behavior.

## When to use me

Use ONLY when the task concerns GitHub Actions orchestration, `.github/workflows/`, `action.yml`, or a GitHub-hosted action catalog. Do not load for generic Git operations, standalone container construction, Kubernetes deployment design, or GitLab CI alone.

Use `container` for Containerfile/image construction details, `conventionalcommits` for commit semantics, and `skill` for modifying this skill. Do not duplicate their instructions here.

## Inspect first

1. Read repository instructions, Git status, existing workflows, action metadata, build scripts, and release configuration.
2. Inventory tracked and relevant untracked files, excluding ignored dependencies and outputs. Detect scripts by shebang/path as well as extension. Do not prescribe TOML lint when no TOML exists; distinguish BitBake `.conf`, LXC `.conf.in`, Shell `.script`, and `Containerfile.tools`.
3. Identify runner OS/architecture, hosted versus self-hosted, available container engine, registry ownership, authentication, and expected artifacts. Do not assume Podman exists on every runner or Docker exists on a Podman-only host.
4. Establish event policy, version source, publication targets, and whether the caller wants step-level reuse or whole-job reuse. Resolve missing consequential inputs rather than inventing credentials or registry digests.

## Target architecture for this user's catalog

Apply this contract to `https://github.com/tdesaules/github-actions` and use it as the default for this user's shared action catalogs. The repository hosts source and action metadata; its `/actions` page shows workflow executions. Publish images to `ghcr.io/tdesaules/github-actions/<image>`.

1. Give every specialized operation its own directory, `action.yml`, `Containerfile`, fixed-operation Go executable, README and tests. Place linters under `lint/<linter>/`. Do not expose a runtime operation-selector argument.
2. Build each action's **own OCI image** using a **multistage Containerfile with a final `FROM scratch` stage**. Copy only the executable and required runtime dependencies, certificates/configuration and licenses. Follow the `container` skill for construction details.
3. Declare `runs.using: docker` and `runs.image: docker://ghcr.io/...@sha256:<verified-digest>` in the released action. Forward documented inputs explicitly through `runs.args` or environment variables; keep secrets out of argv. CLI flags override `INPUT_*`, then documented defaults.
4. Invoke operations directly with named `uses:` steps. Keep conditions, jobs, matrices, permissions and artifact transfer visible in the workflow. Do not replace an operation with host Python, `docker run`, a generic dispatcher, or a composite merely wrapping a host script.
5. Build and test natively on hosted AMD64/ARM64 runners. Publish the exact qualified archives and index to GHCR without reconstruction. Pin the resulting immutable digests in action metadata before releasing the catalog.
6. Use a Git tag or commit to version the action interface (`tdesaules/github-actions/lint/hadolint@1.2.0`). A local `uses: ./lint/hadolint` uses the checked-out revision. Neither is an OCI image version; reserve catalog SemVer for Git tags/GitHub Releases.

Keep these explicit, agreed exceptions:
- Official checkout, artifact upload/download and GitHub App-token actions can remain Node actions, pinned by commit. `uses:` alone does not prove an action is Docker-based; inspect `runs.using`.
- Keep the narrow Buildah composite launcher with its qualified Docker profile. Preserve `vfs`, `chroot`, inner `--network=host` and scoped seccomp/AppArmor options. Do not generalize this exception into arbitrary engine launchers, explicit socket mounts, privileged mode, extra capabilities or daemon-wide changes.

Do not call the target achieved while business-operation `run:` steps or temporary bridges remain. Distinguish implemented actions, qualified/published images, activated workflow calls and successful hosted execution. If unpublished prerequisites require a transition, record its removal condition and complete activation after publication; a green intermediate CI is not completion.

## Choose the reuse boundary

- Default to **native Docker actions** for the catalog's operations. They require supported Linux/Docker runners; this is distinct from a composite invoking Podman.
- Use a composite to assemble `uses:` calls only when that reuse boundary is explicitly needed. Keep individual linters and checks visible; do not hide them behind a generic dispatcher. Outside this catalog contract, a caller can explicitly choose a documented Podman composite; it is valid GitHub syntax, not the default target here.
- Use a reusable workflow for whole-job delegation only when requested; call it through `jobs.<id>.uses`, not `steps`. Preserve the catalog's agreed trigger policy.
- Use a job container only for a genuinely required whole-job environment. Check Shell/Node/libc compatibility; it does not convert host commands into dedicated Docker actions. Remove migration-only job containers when their purpose is resolved.

Read [docker-actions.md](references/docker-actions.md) for action/image layout, invocation, version references and the limited composite boundary.

## Design execution and selection

1. Treat workflow → jobs → steps as the execution hierarchy. Steps are sequential; independent jobs or matrix instances provide parallelism. Use `needs` for dependencies, not an invented GitHub `stage` abstraction.
2. Keep event routing in the workflow and tool execution in the action. Expose explicit inputs/outputs; separate build, scan, push, sign, and verify operations.
3. Discover components from source directories, `action.yml` and Containerfile inputs/dependencies. Do not add a central catalog manifest/lockfile or catalog-level `catalog/`, `config/`, `security/` trees. Keep necessary tool configuration at the repository root. Compute the Git diff before checks, preserving renames/deletions and configuration/shared-source dependants.
4. Emit both a nonempty/empty indicator and valid matrix JSON. Avoid starting a matrix with no work. Bound concurrency and retain independent results with `fail-fast: false` when appropriate.
5. Examine skipped dependencies explicitly: a skipped `lint` must not accidentally suppress a required build. Use dependency-result checks and status functions deliberately; do not use unconditional `always()` to publish after failures or cancellation.
6. Transfer files through uniquely named artifacts, and small scalar values through outputs. Never assume separate jobs share an engine image store or workspace. Aggregate matrix digests from per-component result artifacts, not colliding matrix outputs.
7. Keep `build` and `test` separate. `build` emits archives and checksum receipts with `tested: false`; `test` verifies them, executes native candidates and negative/permission cases, generates SBOMs/scans, rechecks integrity and only then emits `tested: true`. Never rebuild a catalog image in `test`; synthetic builds for testing Buildah itself are allowed.
8. Reuse the published digest for metadata-only changes; documentation-only changes select documentation checks. Use an isolated job registry for native candidates, without a host image-store assumption or generalized socket access. Preserve TLS for external publication; restrict private HTTP to the documented fixture transport.

Read [dynamic-matrices.md](references/dynamic-matrices.md) for diff selection, matrix outputs, dependency conditions, and runner constraints.

## Publication and supply chain

- Keep Buildah, Skopeo, Syft, Grype and Cosign containerized. Use Grype rather than Trivy; preserve the `high` gate and fail-closed advisory evidence rather than suppressing failures to pass CI.
- Publish exactly the tested image; transfer an OCI archive/layout between jobs instead of silently rebuilding. Preserve multi-platform contents when applicable.
- Obtain the registry digest after push. Sign and verify that digest; validate expected identity and issuer for keyless signatures. Test how GitHub OIDC reaches a containerized signer instead of assuming all environment variables are forwarded.
- Publish required images before tagging a catalog whose actions pin those images. Test action execution against candidates during development and against published references before catalog release.
- Keep bootstrap independent of uncreated action tags/images. Check local action resolution carefully; nested local `uses: ./...` paths resolve from the caller workspace, not automatically from the remote action's repository.
- Use minimum job permissions; isolate registry credentials on persistent runners. Keep secrets out of build args, logs, caches, and artifacts.
- Distinguish image digests, ORAS component digests, and local image IDs. Do not treat an executable OCI image as a substitute for a producer's rootfs/contract artifact.

Read [release-publishing.md](references/release-publishing.md) for preparation, tag-triggered release, retries, races, and maintenance.

## User conventions, not GitHub requirements

Apply these defaults to this user's catalog and Pantavisor projects unless repository instructions or the request override them:

- One `.github/workflows/main.yml`, named `main`, with six jobs: `check`, `lint`, `build`, `test`, `release`, `maintenance`. Keep construction and qualification independent; pass detection/matrix outputs from `check` and require qualification before publication.
- Events: branch/tag `push`, manual preparation on `main` through `workflow_dispatch`, and scheduled maintenance. No `pull_request` trigger unless requested. Direct pushes to `main` remain permitted; force-push protection belongs to repository settings.
- Development selects checks/builds from changes; release validates the release set rather than only the push diff; schedule runs maintenance only.
- Catalog Git tags have no `v` prefix (`1.2.3`). Keep local candidate identities separate from release versions; do not publish catalog images under SemVer or `latest` tags. Do not rewrite upstream tool versions. Validate SemVer beyond GitHub's tag globs; document technical signature tags required by registry behavior separately.
- Co-locate each action and its dedicated image definition in the catalog; publish separate images. Start with a global catalog version. Image changes need not rebuild unchanged components.
- Prefer rootless Podman for local diagnostics, not host commands in workflow steps. Schedule containerized Renovate and rescans; require dedicated bot credentials and disable duplicate hosted Renovate App execution before enabling updates.
- Use approved PowerShell verb–noun operation names and lowercase `taskfile.yml` for optional local tooling. Consumers must not need Task. Leave Pantavisor consumer repositories unchanged unless explicitly requested.

## Validation and output contract

1. Run actionlint on workflows, validate action metadata, and run the relevant Shell/Python/Containerfile checks. Do not claim actionlint alone validates every action interface.
2. Test changed-file selection, new branches, deletions/renames, shared dependencies, no-op matrices, and skipped/failed dependencies.
3. Build actual candidate images and test the action with valid and invalid inputs. Check exit-code propagation, filenames with spaces, read-only inputs, writable output ownership, and report paths.
4. Validate SBOM/scan outputs. Test signing and registry operations only when credentials/access exist; mark unexercised remote paths explicitly.
5. For release changes, test first release, no version bump, partial failure/retry, moving `main`, and bootstrap without published dependencies.
6. Report **changed files, commands/results, evidence locations, and remaining external setup**. In reviews, provide `file:line → defect → consequence → correction`. Distinguish local tests from GitHub execution and actual publication; never call an unexecuted workflow qualified.
7. Audit all six jobs for remaining `run:` steps and inspect every local action's runtime/image. Validate multistage scratch definitions and native variants. Exercise artifact collections beyond one API page, verify uploader readability of public reports, and exclude private signing configuration/keys. Confirm which jobs actually executed before claiming the full lifecycle works.

Use [validation-cases.md](references/validation-cases.md) when evaluating this skill's selectivity and behavior. Do not claim automatic skill discovery was tested merely because its Markdown/frontmatter validates.
