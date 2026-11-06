# Non-blocking security policy

Run security operations and expose their real outcomes, but do not make their
findings, missing evidence, or operational failures a CI/release gate. This applies
to development, manual preparation, tag publication, and maintenance.

## Advisory operations

- Syft SBOM generation and publication of security reports.
- Grype vulnerability scans, DB refresh/freshness checks, and advisory reviews.
- Cosign signing, attestations, and signature/identity/issuer verification.
- Additional security-only audits or scanners introduced into the workflow.

Highlight high/critical vulnerabilities; `high` is a reporting priority, not a
failure threshold. Do not configure Grype's severity exit gate merely to suppress
it later. If a tool/action nevertheless returns failure, retain the exit status
and diagnostics and continue. Missing signing credentials, a stale DB, a scanner
outage or an invalid/missing signature must be visible without preventing release.
Do not relabel unavailable or failed checks as clean, signed, or verified.

## Step-level implementation

1. Keep security operations in dedicated named steps, with bounded timeouts and
   `continue-on-error: true` at the **step** level when their actions can fail.
   Do not apply it to whole jobs, mixed functional/security steps, image pushes,
   Git writes, or functional tests. Split mixed actions so failures can be classified.
2. Use `steps.<id>.outcome` and explicit tool outputs to capture the real result;
   `conclusion` may be success after continue-on-error and is not security evidence.
   Do not hide failures with an unreported `|| true`.
3. Generate a per-component/platform summary with tool, operation, subject digest,
   status (`clean`, `findings`, `error`, `not_run`), severity counts when known,
   error/reason, and report paths. For signing, use `signed`/`verified` only when
   observed; otherwise record `error`/`not_run`. Never fabricate a missing report.
4. Attempt diagnostic upload even after a security failure; isolate security-report
   upload from mandatory candidate archives/receipts. Missing security artifacts
   and upload errors are non-blocking and surfaced in the job summary/annotations.
5. Do not feed security outcome into job conditions, publication gates, release
   completeness checks, or a final aggregate exit failure. Aggregate it separately
   from the functional result. A scan-only test entry may finish successfully with
   warnings/error status and must not emit a new functional qualification receipt.

Required checks in branch protection must consume the advisory jobs' normal
non-blocking result, not a separate fail-on-findings status. Do not add an approval
gate, severity exception workflow, or mandatory remediation to restore blocking.

## Still required for correct execution

Keep the configured base allowlist, needs-based runtime selection, digest pinning, minimum
permissions, and secret-handling instructions as construction/configuration rules.
This change does not authorize choosing unlisted bases or leaking secrets.
Security audit reports about those rules remain advisory; report deviations plainly.

Build/functional lint/test failures, missing candidate archives, checksum or source/
platform mismatches, incomplete functional qualification, invalid routing, release
races, and failed registry/Git/GitHub publication remain blocking operational errors.
Registry access needed to publish an image differs from optional signing credentials.
The exact-artifact checks ensure the tested program is the one being released; do
not disable them together with scanners.

## Receipts and maintenance

`tested: true` is emitted after required functional tests and exact-artifact checks
succeed, regardless of security findings/errors. Record security status separately;
it must not be interpreted as a qualification or promotion requirement. A release
may be unsigned or have findings: state that accurately in its evidence/summary.

In maintenance, scanner/SBOM/review failures produce warnings and reports, not job
failure. Renovate operation failures and non-security link-check failures still
affect the maintenance result. Do not mark a skipped Renovate operation successful.
