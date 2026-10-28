# Change selection and dynamic matrices

## Discover components from source

Derive stable component names, source directories, image ownership and platforms
from actual action metadata and Containerfiles. Derive dependencies from COPY/ADD,
shared source imports and action references. Do not introduce a central catalogue
manifest/lockfile or catalogue-level `catalog/`, `config/`, `security/` trees.
Keep necessary tool configurations at the root. Reject duplicate owners and
missing source relationships; incidental Containerfiles are not automatically
publishable actions. State any conservative fallback for unresolved dependencies.

Parse local COPY/ADD sources, including JSON/quoted paths, spaces, wildcards and
directories, and RUN bind mounts sourced from the build context. Distinguish these
from remote ADD downloads and COPY/mount sources referring to another stage or
image. Apply the builder's ignore-file precedence and negation semantics. Include
deleted source paths and both sides of renames without requiring the old file to
exist. Select conservatively when variable sources cannot be resolved; do not
silently omit dependencies. Test root files such as LICENSE as well as shared code.

Use the same current selector implementation in matrix generation, publication
planning and artifact-reuse validation. A planner carrying a stale embedded selector
can disagree with the workflow even when both validate successfully in isolation.

Selection policy:

| Change/event | Selection |
| --- | --- |
| Image recipe/dependency | That image, its tests and action integration |
| Action metadata only | Native tests against the published digest, without rebuilding |
| Tool configuration | Its relevant checks/tests |
| Vulnerability policy/review | Affected published-image scans, without rebuilding unless build inputs also changed |
| Shared helper/base | Source-derived dependants |
| Docs only | Text/Markdown checks, no image build |
| Removed component | Removal/reference validation, no missing-directory build |
| Release preparation | Changed components since previous release, plus catalog-wide coherence |
| Release tag | Validate all release references, regardless of tag push diff |
| Schedule | Maintenance set, no push-diff selection |

For branch pushes compare event `before` and `after`; handle the zero SHA on new
branches explicitly. For new branches, fetch the default branch and use a defined
merge-base policy. Fetch required objects/history instead of silently falling back
to `HEAD~1`. For release preparation use the previous release range. Parse Git's
NUL-delimited output, include both sides of renames, and handle deleted files without
trying to lint nonexistent paths. Filter actual text files, including extensionless
scripts; do not recursively scan ignored Yocto checkouts/build products.

## Outputs and job conditions

Emit a JSON object such as:

```json
{"include":[{"image":"lint-example","directory":"lint/example","arch":"amd64","runner":"ubuntu-24.04","rebuild":true,"scan":true}]}
```

Also emit `has_images=true` or `false` as an explicit string output. Guard the
matrix job with it. A matrix entry is an independent job instance, not a parallel
step. Use `max-parallel` to bound runner/disk pressure and `fail-fast: false` when
all independent results are useful. Available runners and account concurrency
limits still cap actual parallelism. GitHub currently limits a matrix to 256 jobs;
check current platform limits before designing larger catalogs.

Be precise with `needs`: skipped dependencies can suppress downstream jobs even
when a file-change expression looks true. A job that allows lint to be skipped
but rejects failures/cancellation can use a condition shaped like:

```yaml
if: >-
  ${{ !cancelled() && needs.check.result == 'success' &&
      (needs.lint.result == 'success' || needs.lint.result == 'skipped') &&
      needs.check.outputs.has_images == 'true' }}
```

Include every required dependency in `needs`, and tighten release conditions to
require its necessary validations. Do not use `always()` alone for publication.
Workflow-level path filters cannot express all job/step dependencies and release
exceptions; avoid filtering out events needed to compute the selection.

## Separate construction and qualification

Keep `check`, `lint`, `build`, `test`, `release`, `maintenance` as six jobs in
`main.yml`. Derive selection before checks; keep native AMD64/ARM64 matrices
bounded and non-fail-fast. Use direct specialized actions inside both phases.

- `build`: construct selected images with the published Buildah action and emit
  OCI archives plus checksums/source-bound receipts with `tested: false`.
- `test`: download and verify those receipts, test the exact candidate runtime
  and native action interfaces, retain positive/negative/permission diagnostics,
  generate SBOMs and scan at `high`, recheck integrity, then emit `tested: true`.
- Do not rebuild catalog images in `test`. Synthetic builds are appropriate when
  testing Buildah itself. Metadata-only selection uses existing published images.
- `release`: require successful qualification for selected work. Handle empty
  selections, separately validated artifact reuse and tag verification explicitly.

Keep `scan` independent of `rebuild`; rebuilding requires qualification scans, but
a review-policy change need not rebuild. For scan-only work, retrieve the native
variant from the immutable published index and retain an archive for SBOM/review
and scanning. Verify platform and image ownership, preserve its digest, and refuse
to overwrite a build archive. Retain diagnostics even on scan failure. Do not emit
new `tested: true` publication metadata or qualified publication archives for
scan-only work. Keep the `high` gate and evidence checks identical to build scans.

Use an isolated job service to transfer candidates by digest. Keep external
publication TLS-verified and private HTTP limited to the documented fixture
transport. Do not request generalized socket mounts or alter the host daemon.

## Artifacts and aggregation

Jobs may land on different runners. Even on persistent self-hosted infrastructure,
do not assume a shared workspace or engine store. Transfer untested archives from
`build` to `test`, and qualified archives with SBOMs/reports/metadata to release.
Keep build receipts distinct from qualification markers. Use unique
names containing component, platform and relevant execution identity. Avoid local
tags shared by concurrent builds on the same host.

A matrix job output named `digest` is not a deterministic map of image digests:
instances overwrite the same output key and completion order is not guaranteed.
Upload one result file per component/platform, then aggregate in a non-matrix step
or job after all required instances finish. Reject missing/duplicate results and
verify they belong to the intended source commit/version before publication.

Never use concurrent matrix outputs or a shared catalog lockfile as the publication
record. Aggregate per-component qualification artifacts in the release job using
an action. Require the exact source revision and expected component/architecture
set; reject incomplete or duplicate results.

Test artifact listing beyond 100 entries: two build/test matrices can span several
API pages. Check the pinned downloader's pagination and checksum behavior. Make
public reports readable by the uploader despite differing container/runner UIDs.
Exclude ephemeral keys and private signing configuration from broad report globs.
On partial retries, preserve candidate identity and derive the complete expected
component/architecture set from the intended release source. Successful results
may come from different attempts of the same source run; selecting only the last
attempt can discard required results. Use stable per-component/platform/run names
with explicit overwrite semantics, or select the latest compatible legacy attempt
per key. Never fall back to an older success after a newer result failed validation.

Paginate listings and select immutable artifact IDs, not a broad download pattern.
Reject missing, expired or ambiguous results. Recheck source-run completion,
success, revision and attempt after selection to detect a concurrent rerun. Verify
downloaded archive hashes, qualification markers, exact revision, uniform candidate
version and expected set again before publication. IDs alone do not prove content
integrity, and results from incompatible runs must not be combined to pass validation.

For multi-platform images, preserve the platform manifests and publish an index;
do not accidentally release only the runner's native platform after an archive
round trip. Treat registry digests as authoritative after push.

## Regression cases

Test ordinary pushes, new branches, root commits/no prior release, renames,
deletions, spaces in filenames, action-only changes, config changes, shared
dependencies, empty selection and malformed action/image relationships. Test job routing
for success, skipped lint, failed lint, cancelled build and tag events. Unit tests
of a selector do not replace a real GitHub run of job/step conditions.

Official references:
- https://docs.github.com/en/actions/using-jobs/using-a-matrix-for-your-jobs
- https://docs.github.com/en/actions/using-jobs/defining-outputs-for-jobs
- https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions
