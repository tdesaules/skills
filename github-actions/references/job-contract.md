# Six-job CI contract

Apply this contract to the user's repositories covered by SKILL.md. Keep exactly
six job IDs in `.github/workflows/main.yml`, workflow name `main`. Matrix instances
do not add job IDs. Implement business operations with dedicated Docker actions,
retaining the documented infrastructure/Buildah exceptions. Do not invent action
paths, versions, digests, credentials or runner labels to fill a template.

Security is advisory throughout this contract, as defined by the security policy
linked from SKILL.md. Run selected checks but retain findings/errors separately
from functional job success; no security-only outcome blocks CI or publication.

## Event routing

Use a required `workflow_dispatch` choice input `mode` with `prepare` (default) and
`maintenance`. Both manual modes require `refs/heads/main`; reject another ref
with an explicit failure in the selected entry job, not a silently green all-skipped
run. A schedule uses the default branch and runs maintenance only. No PR trigger.
Validate tags as SemVer without `v`; reject disallowed prereleases per release policy.

| Event | check | lint | build | test | release | maintenance |
| --- | --- | --- | --- | --- | --- | --- |
| Branch push | Plan changed work (`development`) | Selected checks | Changed images | Selected candidates/published images | Skip | Skip |
| Dispatch prepare on main | Plan release (`prepare`) | Full applicable catalog checks | Images changed since prior release | Complete intended release set | Prepare, only if version bump | Skip |
| Valid tag push | Validate tag/catalog (`publish`) | Full applicable catalog checks | Skip | Complete release set at published digests | Verify/publish GitHub Release | Skip |
| Schedule | Skip | Skip | Skip | Skip | Skip | All maintenance operations |
| Dispatch maintenance on main | Skip | Skip | Skip | Skip | Skip | All maintenance operations |

For development: docs-only changes run appropriate docs checks, metadata-only
changes test existing image digests, scan-policy-only changes scan existing digests
without rebuild. A genuinely empty selection emits false flags and empty matrices;
only check runs. In prepare mode, no version bump is a successful explicit no-op:
emit the reason and empty phase selections, with no publication or tag creation.
On a first release, require the configured initial version and build all components.

## Shared plan and interfaces

check is the sole source of selection for development/prepare/publish. Emit these
job outputs through action outputs mapped to `jobs.check.outputs`:

| Output | Type / meaning |
| --- | --- |
| `mode` | `development`, `prepare`, or `publish` |
| `source_sha` | Exact checked-out source commit; never a mutable branch name |
| `version` | Next catalog version for prepare, tag version for publish; empty for development/no bump |
| `has_lint` | String `true` iff lint_matrix has entries |
| `has_images` | String `true` iff build_matrix has entries; always false on tags |
| `has_tests` | String `true` iff test_matrix has entries |
| `has_release` | String `true` only for a nonempty-version prepare/publish plan |
| `lint_matrix` | JSON object with include entries: `id`, `action_path`, `runner`, `files` (array of literal paths) |
| `build_matrix` | JSON object with include entries: `component`, `directory`, `arch`, `runner` |
| `test_matrix` | JSON object with include entries: `component`, `arch`, `runner`, `source`, `digest`, `runtime_test`, `scan` |
| `plan_artifact` | Unique name of the uploaded plan artifact |

Use `source: candidate` for test entries consuming this run's build archives;
`digest` is then empty. Use `source: published` with a verified immutable digest
for unchanged, metadata-only, scan-only, and tag verification entries. The two
test flags are JSON booleans; at least one must be true. Every build entry must
have a matching candidate test entry with both flags true. Prepare/publish must
cover the complete expected component/platform set, testing and scanning reused
published images as well as new candidates. A selected phase is never optional.

Empty matrices are `{"include":[]}`; gate the job before matrix expansion. Booleans
in job outputs are strings, so compare to `'true'` rather than testing truthiness.
Use JSON serialization for filenames (including spaces); never split on whitespace.
The lint entry's action_path identifies the expected implementation for plan
validation; it is not a dynamic uses expression. GitHub step uses references must
be literal. Declare each specialized action explicitly and select its step with
`if: matrix.id == '...'`; reject unknown IDs/paths rather than dispatching arbitrary tools.
For large file lists/matrices, partition within GitHub's limits or transport file
lists via the plan artifact with an explicit action input contract; do not truncate.

The plan artifact contains schema_version, mode, source_sha, version, comparison
range, selection reasons, expected components/platforms, verified published digests,
and planned archive/result names. It is generated evidence, **not** a committed
catalog manifest/lockfile. Reject duplicate keys, missing components, unresolved
ownership, or inconsistent flags/matrices. Use the same selector for reuse checks.

## check

- **Inputs:** event/ref, immutable checkout, required Git history, source/action
  definitions, tool configs, previous release and bump policy when applicable.
- **Work:** validate event/ref/version, identify actual languages and dependencies,
  detect changed paths including renames/deletions, compute selection and validate
  the plan. Verify action/image ownership and referenced metadata shape. Resolve
  existing published digests as needed; do not run linters, builds, or full scans.
- **Outputs:** the scalar/matrix outputs above and a source-bound plan artifact;
  a summary explains skipped phases and no-bump decisions.
- **Success:** complete, reproducible, internally consistent plan for the exact
  source. Missing Git history or an invalid release/tag is failure, not empty work.
- **Permissions:** source read and only required registry read; no publishing keys.

## lint

- **Inputs:** check plan and lint_matrix; `needs: [check]`. Run only after check
  succeeds and has_lint is true. Each matrix entry invokes a named specialized action.
- **Work:** check only existing applicable inputs: actionlint for workflows,
  action metadata validation separately, ShellCheck for shell, Hadolint for build
  recipes, and repository-defined formatting/static checks for Go/Python/Markdown/
  YAML/TOML as present. Do not install or run a language linter without its inputs.
  Distinguish extensionless scripts and domain-specific .conf files from generic formats.
- **Outputs:** uniquely named linter reports and exit results, retained on failure.
- **Success:** every selected check passes. Formatting fixes, unit/runtime tests,
  image builds and vulnerability scans belong elsewhere. Use read-only permissions.

## build

- **Inputs:** build_matrix/plan, source checkout; `needs: [check, lint]`. Require
  successful check and lint, or lint skipped only when has_lint is false.
- **Work:** use the dedicated Buildah action and the qualified launcher profile to
  build each selected component natively on AMD64/ARM64. Enforce the container
  base allowlist and final scratch closure. Use bounded matrices with fail-fast false.
- **Outputs:** one OCI archive per component/platform and an untested receipt:
  schema_version, source_sha, component, arch, candidate/version identity,
  archive filename, SHA-256 checksum, workflow run/attempt, and `tested: false`.
- **Success:** complete expected archive set, checksums and valid receipts. No image
  qualification marker, production registry push, signing, tag, or GitHub Release.
  Candidate transport in an isolated test registry is not release publication.

## test

- **Inputs:** test_matrix/plan, exact build artifacts or pinned published images;
  `needs: [check, lint, build]`. Permit skipped build only when has_images is false.
  Lint's selected-or-empty rule still applies. No tests selected means skip the job.
- **Work:** verify source/component/platform and checksums before execution. Run
  relevant unit/contract tests and native action runtime tests for runtime_test
  entries: valid/invalid/missing inputs, exit codes, spaces, read-only inputs,
  writable output ownership and actual output interfaces. Build and test any
  test-only harness separately; never rebuild the candidate being qualified.
- **Scanning:** attempt Syft SBOMs and Grype reports for scan entries; report DB
  freshness, high/critical findings, advisory uncertainty and tool errors without
  failing the job. Use isolated non-blocking security steps and retain real outcomes.
  Recheck archive integrity after tests/scans; artifact mismatches remain blocking.
- **Outputs:** candidate entries produce qualified archives/receipts with
  `tested: true` after required functional tests and exact-artifact checks succeed,
  with separate advisory security status. Published-image entries
  produce digest-bound verification reports, not new candidate publication receipts.
  Scan-only work never claims runtime qualification. Use unique per-entry artifacts,
  not colliding matrix outputs.
- **Success:** all selected functional checks succeed with a complete, unambiguous
  qualification evidence set. Missing functional results, skipped required tests or
  stale/mismatched receipts block release; scan findings, missing SBOMs and security
  tool failures do not. A scan-only entry reports errors without claiming runtime
  qualification. Record hosted execution separately from container-only tests.

## release

- **Inputs:** plan and all required lint/qualification evidence;
  `needs: [check, lint, build, test]`. Run only for has_release=true in prepare or
  publish mode; never on a branch push or maintenance event.
- **Gate:** reject failed/cancelled dependencies and any skipped selected phase.
  Reconcile exact expected component/platform results, paginate artifact listings,
  validate checksums and compatible source/run attempts. Matrix success alone is
  insufficient. Allow skipped build on tags or metadata-only preparation; required
  tests must still succeed.
- **Prepare:** publish exact qualified new archives/index to the personal GHCR
  namespace, attempt non-blocking Cosign signing/verification of remote digests,
  preserve exact verified reused image digests,
  update action references/notes with one writer, recheck main and tag absence,
  then atomically push the final commit plus no-v SemVer tag. Use the trigger
  credential flow documented by the release policy. Do not create the GitHub
  Release here; the tag run does that.
- **Publish (tag):** verify tag/version/source policy, all published image references
  and complete functional test evidence. Attempt advisory signature/attestation
  verification without gating publication on its result; create/update only
  the matching GitHub Release notes/assets idempotently. Never rebuild images,
  mint a new tag, move an existing tag, or republish replacement images.
- **Outputs:** release evidence with image source commits, final catalog commit,
  version/tag, verified registry digests, actual signing/verification outcomes, and observed release URL
  when created. Reused images retain their own proven source commit; the later
  reference-update commit must not be misrepresented as their build source.
- **Success:** published artifacts and references are verified, all writes match
  the captured source/version, and no incomplete set is promoted. Scope contents,
  packages and OIDC permissions to the operations used. Serialize release writes
  with cancel-in-progress false; still detect main advancing outside the workflow.

## maintenance

- **Inputs:** schedule or explicit mode=maintenance on main, current catalog image
  digests, dependency configurations, dedicated Renovate credentials and scan policy.
  No needs: this job must not depend on the five intentionally skipped jobs.
- **Work:** validate its own ref/mode, run containerized Renovate, refresh vulnerability
  data and rescan published native images with Syft/Grype, and check external links.
  Run independent operations even if another fails, then aggregate their status;
  retain true outcomes and reports. Only non-security failures affect job success.
  Check permissions and duplicate
  hosted-App execution before dependency updates.
- **Outputs:** manager/extraction/update summaries, digest-bound scan/SBOM reports,
  freshness metadata, link-check results and actual dependency PR links if created.
- **Success:** planned non-security operations ran and passed; security operations
  can report findings/errors without failing maintenance. Missing Renovate credentials
  or a skipped Renovate step is not successful maintenance. Existing no-PR workflow
  triggers do not prohibit Renovate from creating dependency PRs.
- **Effects:** dependency-update branches/PRs only for Renovate; no image builds,
  release preparation, image promotion, catalog tags, or GitHub Release creation.
  Use separate bot credentials and concurrency group from release.

## Conditions and failure semantics

Use explicit status functions to avoid GitHub's implicit success condition when a
dependency can intentionally be skipped. For example, the build job uses:

```yaml
needs: [check, lint]
if: >-
  ${{ !cancelled() && needs.check.result == 'success' &&
      needs.check.outputs.has_images == 'true' &&
      ((needs.check.outputs.has_lint == 'true' && needs.lint.result == 'success') ||
       (needs.check.outputs.has_lint == 'false' && needs.lint.result == 'skipped')) }}
strategy:
  fail-fast: false
  matrix: ${{ fromJSON(needs.check.outputs.build_matrix) }}
```

Apply the same selected=true → success / selected=false → skipped rule for build
in test, and for lint/build/test in release. Require check success and the target
phase's selection flag. Include all inspected jobs directly in needs. Never accept
a skipped selected job or unconditional always() for publication. Apply
continue-on-error only to dedicated advisory security steps, never functional
qualification or a whole job. Use their outcome for reporting, not their coerced
conclusion. Limit always() to diagnostic cleanup/upload steps.

## Acceptance scenarios

Before calling a generated CI complete, verify routing for: empty change set,
docs-only, metadata-only, scan-only, changed image, first release, no-bump preparation,
valid/invalid tag, skipped unselected lint, skipped selected lint, failed/cancelled
tests, manual wrong-ref requests, schedule and manual maintenance. Check both native
platforms, missing/duplicate artifacts, partial retry, and main advancing during
preparation. Static workflow validation does not prove hosted conditions executed.
