# Release publication and maintenance

## Establish policy

Apply the repository contract from SKILL.md: main.yml with six jobs, branch/tag
push, main-only manual preparation, and maintenance-only schedules; no PR trigger
unless requested. Route manual maintenance separately. Publish catalog images to
ghcr.io/tdesaules/github-actions/<image>. Use global catalog SemVer tags without a
v prefix for Git/GitHub Releases; no catalog SemVer/latest aliases for images.
Validate SemVer separately from tag globs. These are user conventions, not platform
requirements; preserve explicit user/repository overrides.

Use the six-job contract linked from SKILL.md for dispatch modes, needs, outputs
and gates. Prepare mode builds changed images and qualifies the complete intended
release set, including reused digests. Tag mode skips build, tests the complete
published set, then verifies/publishes the GitHub Release. A no-bump preparation
is an explicit successful no-op; maintenance routes only to its independent job.

## Publish exact qualified artifacts

For a catalog whose metadata pins prebuilt action images:

1. Capture the intended source commit and previous release. Derive a version using
   git-cliff/Conventional Commits and the explicit bump policy; handle first release
   and no-bump cases without inventing an initial version.
2. Build selected components and transfer source-bound archives/checksums to tests.
   Qualify exact AMD64/ARM64 artifacts through functional action tests and integrity
   checks; attempt Syft/Grype reporting as non-blocking steps. Do not rebuild in test.
3. Push those artifacts, capture registry digests, and attempt non-blocking signing
   and signature verification. Preserve the multi-platform index rather than publishing only the
   current runner's native platform.
4. Update action digest references in a single writer; preserve unchanged digests.
   Check that all referenced images are accessible to intended consumers.
5. Recheck main's captured revision and tag absence before committing digest/notes
   updates. Atomically push the final commit and new tag in the authorized release
   flow. Serialize finalization and reject races without moving an existing release tag.
6. On release, verify references and publish notes/assets. Do not rebuild solely
   because a tag event occurred.

Image source and final metadata-update commit can differ. Record both explicitly.
Git tags version action source; OCI digests identify executable images. Keep upstream
tool versions distinct. Document technical Cosign signature tags separately from
forbidden catalog-version/latest aliases.

Implement planning, publication, signing, verification and finalization as explicit
uses steps backed by dedicated Docker actions. Keep official token/artifact actions
as exceptions. A host Python/gh publisher or engine shell block is not completion;
remove transitional bridges and exercise the activated path on GitHub.

On retry, reuse only complete artifacts bound to the intended revision/version.
Reject conflicting immutable identities and document partial-publication cleanup.
Paginate artifact listings and verify hashes, expected component/platform sets,
qualification markers, and compatible run attempts before promotion.

## Authentication and conditions

- Events created with normal `GITHUB_TOKEN` generally do not trigger new runs;
  workflow/repository dispatch are documented exceptions. Choose explicit dispatch
  or an appropriately scoped App token for chained release events.
- Source push, job token, registry publishing, signing, and dependency-update
  credentials serve different purposes. Verify their actual permissions separately.
- Use minimum job permissions. For keyless signing, grant `id-token: write` to the
  signing job and test token acquisition from its actual container/runtime.
- Check signature identity and issuer, not merely presence; report invalid, missing
  or unavailable signatures without blocking publication. Preserve actual outcomes.
- Scope concurrency so development cancellation cannot interrupt publication.
  A concurrency group does not prevent external pushes: recheck captured revisions.
- Publication requires successful functional and artifact validations, not clean
  scans or successful signing. A review request does not
  authorize pushing commits, tags, images, or release records.

## Maintenance

Use containerized Syft and Grype (not Trivy) as non-blocking security operations.
Highlight high/critical findings and document database freshness. Report absent,
ambiguous or altered advisory evidence as unresolved, not as a successful review
and not as a CI failure. Retain real exit codes/diagnostics while allowing the
job and release to continue, following the security policy linked from SKILL.md.
Rescan published
digests without rebuilding when only vulnerability data or review policy changed.

Schedule containerized Renovate with dedicated bot/App credentials; disable duplicate
hosted Renovate App execution before enabling it. Inspect manager/file coverage,
validate configuration, and run an authenticated dry-run when authorized.
Distinguish valid configuration, successful authentication, actual
dependency extraction, and observed PR creation. Keep caches, keys, and signing
configuration out of public report artifacts.

## Evidence

Report runner/platform coverage, actual digests, command results, and hosted run
links only when observed. Explicitly mark untested registry/signing/remote paths.

Sources:
- https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows
- https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/about-security-hardening-with-openid-connect
- https://docs.sigstore.dev/cosign/signing/signing_with_containers/
