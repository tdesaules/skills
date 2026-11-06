# Repository CI

`.github/workflows/main.yml` runs on branch/tag pushes and manual dispatch, without
a pull_request trigger. All jobs have read-only repository permissions. Checkout
is pinned by commit and does not persist credentials. Business operations use
dedicated native Docker actions, not host commands or composite dispatchers.

## Repository-specific job scope

This source collection has no application artifact or release automation. Its
explicit adaptation of the six-job convention is:

| Job | Current responsibility |
| --- | --- |
| check | Full skill/frontmatter validation, evaluation schema checks, local documentation paths |
| lint | Python correctness/whitespace, Markdown layout, workflow syntax |
| build | Declared and skipped: no distributed application artifact |
| test | Both Python validator suites; allows build to be intentionally skipped |
| release | Declared and skipped: no automated skill release/publication |
| maintenance | Declared and skipped: no implicit Renovate or external-link schedule |

check, lint and test run on ubuntu-24.04 and ubuntu-24.04-arm. A failed check/lint
blocks tests; an intentionally skipped build does not. Full checks avoid coupling
test coverage to a changed-file classifier. Manual dispatch verifies the selected
ref; it does not prepare a release. No catalog release inputs/outputs or empty
artifacts are fabricated just to imitate an image-producing repository.

Tool-image construction currently occurs through native source actions; those
builds are CI infrastructure bootstrap, not outputs of the reserved build job.
See [action qualification/publication](../.github/actions/README.md) for the exact
remaining transition to published digest-pinned images. This CI is not remotely
qualified until the user pushes it and both native runner variants execute.

## Checks and limits

- Existing skill validator checks frontmatter and internal Markdown links.
- `.github/scripts/check_repository.py` checks eval IDs, required strings, boolean trigger
  labels, duplicate JSON keys, fixture paths, skill-name matching and orphan evals.
  It parses Markdown links/reference links/images across skills, docs, root Markdown
  and action docs, checking local file/directory paths and repository escapes.
- External HTTP links, HTML links and URL fragment/heading anchors are not checked.
  JSON checks cover syntax/schema, final newlines and trailing whitespace, without
  forcing a pretty-printing style on evaluation data.
- Ruff's root config checks syntax, imports/names and whitespace without an unrelated
  formatting rewrite. Markdownlint's root config checks a small explicit layout set;
  tutorial examples are not linted as actual application YAML or Containerfiles.
- Actionlint ignores only its constant-false condition warning, because the three
  reserved jobs are deliberately disabled; workflow syntax/expression errors still fail.
- Python tests exercise valid/invalid inputs, escaping paths and broken links.
  Agent activation/quality evaluations remain manual with isolated contexts.
- No security audit or signature requirement blocks this CI. Any future security
  steps must follow the collection's non-blocking policy.

## Local reproduction

```bash
uv run .github/scripts/check_repository.py .
uv run --with PyYAML==6.0.3 --with markdown-it-py==4.0.0 --with mdurl==0.1.2 python tests/run.py
python3 .github/scripts/qualify_ci_actions.py --output /absolute/external/skills-ci
```

The first two commands need Python 3.10+ and uv; qualification additionally needs
Git and rootless Podman. Builds fetch pinned tools/packages; action execution is
tested offline. Archive and receipt output belongs outside the checkout.
Do not push this repository automatically; the user controls Git pushes.

Repository-only CI helpers live in `.github/scripts/`. The scripts bundled under
`skill/scripts/` belong to the installable authoring skill and stay with that skill.
Action entrypoints and image recipes remain under `.github/actions/`.
