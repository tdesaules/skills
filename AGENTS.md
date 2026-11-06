# Repository instructions

## Editing skills

- Skills live at root `<name>/SKILL.md`; `opencode/` is the retired layout.
  Keep resources inside each skill; document intentional companion dependencies
  without assuming client-specific tool IDs. Install commit with conventionalcommits.
- Read `skill/SKILL.md` for authoring rules. Keep skills agent-neutral;
  `compatibility` names actual runtime requirements, not OpenCode. Fixed headings
  and frontmatter Examples blocks are not required.
- Skill Markdown links must stay inside that skill folder; the validator resolves
  them relative to the containing Markdown file. Update README's table for skill additions/removals.
- Prefer Python or `go run` for utilities; script interface guidance is in
  `skill/references/scripts.md`.
- `commit` owns Git mutation; `conventionalcommits` owns message semantics.
  Commit proactively by default, load conventionalcommits first, and include a why-body.
- Agent portability does not mean removing user conventions. Preserve the GitHub
  Actions main.yml/six-job/Docker/Grype contract and the container allowlist.
  Prefer scratch where suitable; complete runtime environments may use other allowed bases.
- Security reporting in GitHub Actions is advisory, including tool/signature errors;
  keep functional tests and exact-artifact/publication failures blocking.

## Verification

From repository root, with Python 3.10+ and uv:

```bash
uv run skill/scripts/validate.py --collection .
uv run skill/scripts/validate.py ./helm # focused skill check
uv run --with PyYAML==6.0.3 python -m unittest discover -s skill/scripts
uv run .github/scripts/check_repository.py .
uv run --with PyYAML==6.0.3 --with markdown-it-py==4.0.0 --with mdurl==0.1.2 python tests/run.py
```

- Append `-k test_links_missing_escape_and_valid` to the unittest command for one test.
  Discovery's `-s skill/scripts` is needed for the test's `from validate import validate`.
- The validator declares PyYAML via PEP 723; the unittest invocation needs its own
  `--with` dependency. First use may download packages.
- Collection validation scans only immediate `*/SKILL.md` files. It does not check
  evaluation JSON, root documentation links, external URLs, or skill behavior.
- For the official validator, use README's pinned upstream installation command;
  the PyPI `skills-ref==0.1.0` package exposed a different executable during review.
- `evals/evals.json` contains test specifications, not benchmark results. Follow
  `docs/evaluation.md` for isolated comparisons; templates in references also require
  target-environment validation before claiming they work.

## CI infrastructure

- This repo's six-job adaptation is in docs/ci.md: check/lint/test run fully;
  build/release/maintenance are deliberately skipped, with no publication side effects.
- `.github/actions/*/Dockerfile` symlinks select their Containerfile for native
  source-action bootstrap. Do not replace them with host/composite scripts.
- Keep repository-only CI helpers under `.github/scripts/`; skill-bundled scripts
  stay in their own `<skill>/scripts/` directory.
- `.github/scripts/qualify_ci_actions.py --output <external-directory>` builds/tests/archives
  exact native images. Publication requires both native platforms and actual GHCR
  digests; source-action CI is not the completed prebuilt-image catalog contract.

## Git

Use Conventional Commits and the proactive workflow in `commit/SKILL.md` unless the
request limits the task to review/proposal. **Never push**; the user pushes manually.
