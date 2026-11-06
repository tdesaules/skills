---
name: github-actions
description: >-
  Use when creating, reviewing, or debugging GitHub Actions workflows or action.yml:
  main.yml orchestration, changed-file matrices, dedicated Docker actions with
  scratch runtimes, GHCR publication, and release routing. Apply the user's catalog
  and Pantavisor CI conventions. Not for standalone Containerfiles, generic Git
  operations, or GitLab CI.
license: GPL-3.0-or-later
compatibility: Local validation requires actionlint; hosted execution and publication require GitHub access and appropriate runners/credentials.
---

# GitHub Actions

## Scope

Design workflow orchestration and action interfaces using the user's repository
conventions below. They are deliberate project policy, not GitHub or Agent Skills
requirements. Apply them to `tdesaules/github-actions`, the user's shared action
catalogs, and Pantavisor projects unless the user or repository instructions
explicitly override them. Do not generalize away these conventions for portability.

When selecting, building, or reviewing container images, consult the companion
`container` skill when available for the collection's base-image allowlist and
build/runtime procedure. Cover Docker actions, job/service containers, and images
launched by steps. Prebuilt application/tool images require recipe/provenance
checks, not substitution with a bare base. If the companion is unavailable,
preserve existing references and report the policy check as unresolved; workflow
routing and syntax checks remain independently usable.

## Repository contract

- Use one `.github/workflows/main.yml`, named `main`, with exactly six jobs:
  `check`, `lint`, `build`, `test`, `release`, `maintenance`. Detection and matrix
  outputs come from `check`; keep construction and qualification separate.
- Trigger branch/tag `push`, manual preparation on `main` via `workflow_dispatch`,
  and scheduled maintenance. No `pull_request` trigger unless requested. Permit
  direct pushes to `main`; force-push protection belongs to repository settings.
- Development selects work from changes; release verifies the complete release
  set rather than only the push diff; schedules run maintenance only. Route manual
  maintenance separately so it cannot enter release preparation.
- Host catalog sources at `https://github.com/tdesaules/github-actions`; publish
  dedicated images to `ghcr.io/tdesaules/github-actions/<image>`. The repository's
  `/actions` page is the execution UI, not the image registry.
- Give each specialized operation its own directory, `action.yml`, `Containerfile`,
  fixed-operation Go executable, README, and tests. Put linters under `lint/<linter>/`.
  Do not introduce a generic runtime operation selector.
- Build each action's own image in multiple stages ending in **`FROM scratch`**.
  Copy its complete runtime closure, including interpreters/libraries when the tool
  needs them, certificates, configuration and licenses. Apply the `container`
  allowlist to builders/donor images too; the scratch rule is a stricter catalog
  runtime choice. Report missing runtime dependencies instead of silently changing bases.
- Released actions use `runs.using: docker` and verified `docker://...@sha256:...`
  references. Invoke operations with named, direct `uses:` steps; keep conditions,
  matrices, permissions and artifact transfer visible. Host Python, `docker run`,
  or composite host-script wrappers are not substitutes for these catalog actions.
- Qualify native AMD64/ARM64 images on hosted runners, then publish the exact
  tested archives/index without reconstruction. Distinguish implementation, image
  qualification/publication, workflow activation and observed hosted execution.
- Version the catalog globally with Git tags/GitHub Releases such as `1.2.3`, no
  `v` prefix. Reserve catalog SemVer for Git, not image tags; do not publish catalog
  images under SemVer or `latest` aliases. Keep upstream tool versions intact and
  document technical signature tags separately. Reuse unchanged image digests.
- Keep Buildah, Skopeo, Syft, Grype and Cosign containerized. Use **Grype, not Trivy**,
  with the `high` severity gate and fail-closed advisory evidence. Schedule
  containerized Renovate/rescans, with dedicated bot credentials and no duplicate
  hosted Renovate App execution.
- Prefer rootless Podman for local diagnostics. Use approved PowerShell verb–noun
  operation names and lowercase `taskfile.yml` for optional tooling; consumers must
  not need Task. Leave Pantavisor consumer repositories unchanged unless requested.

## Agreed exceptions and reuse

- Official checkout, artifact upload/download, and App-token actions may remain
  Node actions pinned by commit. Inspect `runs.using`; `uses:` alone proves nothing.
- Preserve the narrow qualified Buildah composite launcher: `vfs`, `chroot`, inner
  `--network=host`, scoped seccomp/AppArmor options. Do not extend it to arbitrary
  engine launchers, socket mounts, privileged mode, extra capabilities, or daemon changes.
- Use composites to assemble `uses:` calls only when that reuse is needed; do not
  hide individual checks in a dispatcher. Reusable workflows delegate whole jobs
  only when requested. A job container requires a genuine whole-job environment.
- Outside this catalog contract, an explicitly chosen Podman/Python composite can
  be valid GitHub syntax. Distinguish that validity from compliance with this policy.
- If bootstrap requires temporary bridges, document their removal condition and
  finish activation after publication. A green transitional CI is not completion.

## Six-job execution contract

Read [the job contract](references/job-contract.md) when creating or changing
main.yml, job conditions, outputs, or release routing. It defines the required
event matrix, needs graph, output names, artifacts, and success criteria.

| Job | Responsibility | needs |
| --- | --- | --- |
| `check` | Validate source/event policy and emit a deterministic execution plan | none |
| `lint` | Run selected static checks; no release builds or runtime qualification | `check` |
| `build` | Build selected native candidates; emit untested archives/receipts | `check`, `lint` |
| `test` | Test exact candidates or published digests, generate SBOMs and scans | `check`, `lint`, `build` |
| `release` | Prepare images/references/tag, or verify a tag and publish the GitHub Release | `check`, `lint`, `build`, `test` |
| `maintenance` | Scheduled/manual Renovate, rescans and link checks, independently | none |

Require every selected dependency to succeed. A skipped dependency is acceptable
only when check explicitly declared that phase empty. Tags never rebuild images;
maintenance never enters release. Never treat skipped required tests as success.

## Workflow

1. Read instructions, existing workflows/actions, build tools, release configuration,
   and the affected source. Identify event, runner OS/architecture, container engine,
   credentials, and intended outputs. Distinguish review-only from implementation
   or actual publication requests.
2. Apply the repository contract and agreed exceptions. Inventory actual source
   languages and scripts, including extensionless files; do not prescribe checks
   for nonexistent inputs. Resolve consequential missing runner/credential inputs.
3. Implement the six-job execution contract, keeping routing, dependencies,
   conditions, matrices and permissions visible. Discover components from source, action metadata
   and build dependencies; do not add a central catalog manifest/lockfile or
   catalog-level `catalog/`, `config/`, `security/` trees. Keep tool config at the root.
   `build` emits archives/receipts with `tested: false`; `test` verifies and executes
   those artifacts, generates SBOMs/scans, rechecks integrity, then emits `tested: true`.
4. Validate source selection and skipped/failed/cancelled dependencies. Use
   [dynamic matrices](references/dynamic-matrices.md) for changed-file workflows.
5. For container actions, read [Docker action contracts](references/docker-actions.md).
   Verify runner support, inputs/outputs, workspace permissions, and the actual image.
6. For releases or maintenance, read [publication](references/release-publishing.md).
   Publish the tested artifact rather than rebuilding it; never invent a digest.
7. Run appropriate local checks and targeted fixtures; exercise remote paths only
   within the task's authorization and available access. Report evidence separately
   for syntax validation, image tests, hosted execution, and publication.

Use the same selector for matrices, publication plans and artifact-reuse validation.
Keep scan-only work distinct from rebuilding and from new publication qualification.
Before remote work, check the source-push identity's workflow permissions separately
from job, release-App, signing and Renovate identities; do not expose tokens.

## Gotchas

- A reusable workflow is called by `jobs.<id>.uses`; that job cannot also have steps.
- `uses:` does not imply a Docker action. Inspect `runs.using` and `runs.image`.
- Local nested `uses: ./...` resolves from the caller workspace, not automatically
  from a remote action's repository. Check out required sources explicitly.
- Separate jobs do not share a workspace or engine store. Transfer artifacts;
  aggregate matrix results from unique files rather than colliding output names.
- Skipped `needs` can suppress downstream jobs. Use explicit dependency results
  and status functions; never use `always()` alone to authorize publication.
- Inputs from events are untrusted: pass them via environment/arguments rather
  than interpolating expressions into shell source. Avoid executing untrusted PR
  code in privileged `pull_request_target` contexts. Scope tokens per job.
- Git tag filters are globs, not SemVer validators. A release tag must select
  qualified source/artifacts, not merely match a glob.
- A tag push made with ordinary `GITHUB_TOKEN` generally does not trigger another
  workflow. Choose a documented dispatch or scoped App-token flow when needed.

## Validation and output

Use the repository's actionlint version; if a Go-based one-off is needed, run a
verified pinned `go run github.com/rhysd/actionlint/cmd/actionlint@<version>`.
Resolve the version first, never execute placeholders. Actionlint checks workflow
syntax/expressions, not every action interface or hosted behavior.

Test relevant cases: empty matrices, missing history, renames/deletions, shared
dependencies, skipped and failed jobs, invalid inputs, filenames with spaces,
artifact ownership, partial retries, and release races. Keep reports on failures.

Audit all six jobs for business-operation `run:` steps and temporary bridges.
Inspect every action's actual runtime, dedicated multistage scratch recipe and
native variants. Test artifact pagination and exclude private signing material.

Return `file:line → defect → consequence → correction` for reviews. For edits,
return changed paths, commands/results, evidence locations, and external setup
still needed. Do not publish merely to demonstrate a review finding.
