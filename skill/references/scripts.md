# Script interfaces

Use a script when repeated traces reveal deterministic work being reinvented.
Reuse an existing CLI before adding a wrapper. Prefer Python for small data/file
utilities and `go run` for Go tooling; keep shell commands simple.

## Runtime and dependencies

- Python standard-library scripts run with `python3 scripts/name.py`.
- For external Python dependencies, declare a PEP 723 block with requires-python
  and pinned dependencies; run with `uv run scripts/name.py`. State that uv is an
  additional prerequisite; ordinary python does not install inline dependencies.
- For an existing Go CLI, use `go run module/path/cmd/tool@vX.Y.Z`. Resolve a real
  version before writing the invocation. For bundled standard-library Go code,
  `go run scripts/tool.go` suffices; dependency-bearing programs need documented
  module files and versions. Avoid `@latest` in reproducible workflows.
- Network/cache access may be required on the first run. Do not describe dependency
  resolution as a network-free operation.

## Contract

1. Accept explicit arguments/stdin; never wait on a TTY prompt.
2. Implement concise `--help` including examples, input/output paths, side effects,
   dependencies, and exit codes.
3. Send JSON or other structured data to stdout and diagnostics to stderr. Keep
   output bounded or offer pagination/an explicit output file for large datasets.
4. Validate inputs before effects; reject ambiguous values with corrective errors.
5. Make retries idempotent where practical. Add preview/dry-run for state-changing
   batch operations when needed; do not add confirmation machinery to read-only checks.
6. Test normal inputs, malformed/missing inputs, spaces in paths, failures, and
   retry behavior. Check actual artifacts/exit codes, not just final agent prose.

Reference scripts with skill-root-relative paths. When the target is in another
working directory, resolve the script location explicitly and pass the target as
an argument rather than accidentally validating the skill's own directory.
