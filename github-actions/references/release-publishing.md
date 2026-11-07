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

## Versioning and release notes

Use the companion `conventionalcommits` skill for commit semantics and `commit`
for Git mutations; load/read them when performing that work. This skill owns the
release policy, not those companions. Apply these explicit git-cliff bump rules:

- `feat` → minor; `fix` or `perf` → patch. The `perf` mapping is a user convention,
  not a requirement of Conventional Commits.
- `!` or a `BREAKING CHANGE` footer takes precedence for every commit type:
  major at/after 1.0.0, minor before 1.0.0. Highest applicable bump wins.
- Other types alone do not trigger a release. Never filter out breaking commits
  merely because their type is normally hidden from the changelog.
- During initial repository/application development, keep the project version at
  0.1.0 without automatically creating releases. Make the first official release
  an explicit transition to 1.0.0. Never republish or move an existing 0.1.0 tag.
  If a project explicitly opts into published 0.x releases before that transition,
  apply the pre-1.0 breaking-change rule above.

Configure the repository's pinned git-cliff version explicitly for these rules;
do not assume its defaults implement `perf` or pre-1.0 behavior. Verify version
calculation using fixtures for feat, fix, perf, breaking changes of any type,
mixed commits, no bump, initial development and the explicit 1.0.0 transition.
Keep bump detection separate from release-note filtering.

Generate Markdown notes with git-cliff following **Keep a Changelog**: dated
version headings (`YYYY-MM-DD`), nonempty `Added`, `Changed`, `Deprecated`,
`Removed`, `Fixed`, and `Security` sections, and comparison links. Use `Added`
for features, `Fixed` for fixes, and `Changed` for performance improvements;
classify deprecations, removals and security fixes by actual impact. Notes are
user-facing summaries, not raw commit logs. Hide routine internal changes unless
they affect users; explicitly highlight breaking changes and migration steps.
Maintain an `Unreleased` section when keeping a repository CHANGELOG.md.

Publish directly after validation: no draft or prerelease by default, and reject
prerelease tags under this policy. Mark the newest stable version as GitHub's
latest release explicitly; an older maintenance release must not replace it.

## Optional assets and OCI distribution

The following release assets are optional but recommended when applicable. Select
them for the project; do not require every project to produce every asset.
Optional public attachments do not make functional tests or internal integrity
and qualification evidence optional.

| Asset | Recommended publication |
| --- | --- |
| Source | GitHub's automatic ZIP/tar.gz archives; avoid duplicate uploads |
| Binaries/installers | Direct GitHub Release downloads per supported OS/architecture, with README/licenses; OCI copies optional |
| Container images | Native OCI images/indexes in GHCR using Buildah/Skopeo; link immutable digests in notes, no archive attachment by default |
| Helm charts | Helm's native OCI publication and media types; no generic ORAS rewrapping |
| Ecosystem packages | Preserve the ecosystem's native format, tooling and registry |
| SBOMs | SPDX JSON per distributed image/platform or binary, bound to its digest/checksum; optional release attachments |
| Checksums | SHA256SUMS covering distributed release files, excluding itself/signatures; OCI objects already have digests |
| Provenance | Source/workflow-bound attestations using the relevant native tooling and OCI association where supported |
| Security scans | Detailed timestamped CI artifacts, with summary/run links in the release |
| Test reports | Detailed CI artifacts and execution links rather than default release attachments |
| Evidence collection | Optional generated release-evidence.json with source/final commits, tag, platforms, digests, checksums and test/attestation links |
| Signatures | Cosign for images; signed checksums for binaries when a signing identity is configured |

**OCI is the default distribution mechanism for published generic artifacts that
lack a suitable native publication mechanism.** Use ORAS to push/pull these artifacts
with explicit artifact/media types and immutable digest references. Preserve payload
formats (for example SPDX JSON); do not disguise arbitrary files as container images.
Keep native container, Helm and ecosystem tooling, and direct binary downloads as
the exceptions above. Use subject/referrer associations for supporting metadata
where the registry supports them; verify registry/client behavior before relying on
discovery. Preserve Cosign's signature/attestation conventions rather than inventing
generic ORAS wrappers for them.

Implement ORAS operations as dedicated Docker actions under the existing catalog
contract. This publication default does not require OCI transport for intermediate
job files or temporary CI reports. Generated evidence is not a committed catalog
manifest/lockfile. Document CI artifact retention for linked reports.

For selected assets, verify identity/integrity and publish the exact qualified bytes;
publication errors remain blocking. SBOM/scan/signature generation and verification
remain advisory: report missing outputs and real errors, never fabricate evidence
or block release solely for those security-tool failures.

## Publish exact qualified artifacts

For a catalog whose metadata pins prebuilt action images:

1. Capture the intended source commit and previous release. Derive a version using
   git-cliff/Conventional Commits and the policy above; distinguish initial development,
   the explicit first official release, and no-bump cases.
2. Build selected components and transfer source-bound archives/checksums to tests.
   Qualify exact AMD64/ARM64 artifacts through functional action tests and integrity
   checks; attempt Syft/Grype reporting as non-blocking steps. Do not rebuild in test.
3. Push those artifacts, capture registry digests, and attempt non-blocking signing
   and signature verification. Preserve the multi-platform index rather than publishing only the
   current runner's native platform.
4. Update action digest references in a single writer; preserve unchanged digests.
   Check that all referenced images are accessible to intended consumers.
5. Recheck main's captured revision and tag absence before committing digest/notes
   updates. Create `chore(release): prepare X.Y.Z` with a why-body for the actual
   digest/notes/version changes, then create an annotated `X.Y.Z` tag pointing to
   that final commit. Atomically push the final commit and new tag in the authorized release
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

- Use one shared bot GitHub App for release preparation and Renovate (for example,
  `niri-tonic-bot` in the niri-tonic organization). Configure the Actions variable
  `BOT_APP_ID` with its App ID and the Actions secret `BOT_APP_PRIVATE_KEY` with
  the complete PEM private key. Organization-level values must authorize each
  consuming repository. These names replace `RELEASE_APP_ID` and
  `RELEASE_APP_PRIVATE_KEY`; no personal access token or `RENOVATE_TOKEN` is needed.
- Install the App on the selected repositories. Each release-preparation or
  maintenance job calls `actions/create-github-app-token` pinned to a verified
  commit, with `app-id: ${{ vars.BOT_APP_ID }}`,
  `private-key: ${{ secrets.BOT_APP_PRIVATE_KEY }}`,
  `owner: ${{ github.repository_owner }}`, and
  `repositories: ${{ github.event.repository.name }}`. Pass that step's temporary
  token directly to the consuming action; never persist it in artifacts or reuse
  a token across jobs. Preserve the token action's automatic revocation.
- For the shared release/Renovate App, configure repository **Contents, Pull
  requests, Issues and Workflows: read/write**, and **Actions: read**. Renovate's
  supported App setup also lists **Commit statuses and Checks: read/write**,
  **Administration and Dependabot alerts: read**, and organization **Members:
  read**. Grant merge-queue permissions only when using merge queues. Confirm the
  current Renovate platform requirements and approve changed installation
  permissions. Webhooks are unnecessary for an App used only by these workflows.
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

Schedule containerized Renovate with the shared bot App's job-local installation
token described above; disable duplicate
hosted Renovate App execution before enabling it. Inspect manager/file coverage,
validate configuration, and run an authenticated dry-run when authorized.
Distinguish valid configuration, successful authentication, actual
dependency extraction, and observed PR creation. Keep caches, keys, and signing
configuration out of public report artifacts.

## Evidence

Report runner/platform coverage, actual digests, command results, and hosted run
links only when observed. Explicitly mark untested registry/signing/remote paths.

Sources:

- https://docs.renovatebot.com/modules/platform/github/#running-as-a-github-app
- https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows
- https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/about-security-hardening-with-openid-connect
- https://docs.sigstore.dev/cosign/signing/signing_with_containers/
- https://keepachangelog.com/en/1.1.0/
- https://git-cliff.org/docs/configuration/bump/
- https://oras.land/docs/
