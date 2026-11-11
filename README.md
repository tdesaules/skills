# Agent Skills

Portable [Agent Skills](https://agentskills.io/) for development and operations.
Each root-level folder contains `SKILL.md`, optional references/scripts, and
evaluation cases. Explicit companion dependencies are documented below. Licensed GPL-3.0-or-later;
see [LICENSE](LICENSE).

## Skills

| Skill | Scope |
| --- | --- |
| [chezmoi](chezmoi/SKILL.md) | Managed dotfiles, templates, scripts, preview/apply |
| [commit](commit/SKILL.md) | Proactive local commits, required why-body, unpublished history; requires conventionalcommits |
| [conventionalcommits](conventionalcommits/SKILL.md) | Message types, scopes, breaking changes; no Git mutation |
| [container](container/SKILL.md) | OCI builds, Compose, Quadlet, runtime diagnosis |
| [github-actions](github-actions/SKILL.md) | Separate CI/release/maintenance workflows, dedicated Docker actions, allowlisted runtime bases, GHCR releases |
| [helm](helm/SKILL.md) | Charts, values, templates, dependencies, releases |
| [skill](skill/SKILL.md) | Portable skill authoring, validation, evaluation |

The `container` skill owns the base-image allowlist (all build and runtime stages).
`helm` and `github-actions` refer to it for image-selection/build policy. Application
images are checked through their recipes/provenance rather than renamed to base
images. See [the policy](container/SKILL.md#base-image-allowlist) for exact repositories.

Agent portability preserves personal repository conventions. `github-actions`
uses separate main.yml/release.yml/maintenance.yml workflows, no PR trigger by default, dedicated Go/Docker
actions with needs-based allowlisted runtimes, advisory Grype reporting, no-v Git tags, and the personal
GHCR namespace. These are project choices, not Agent Skills or GitHub requirements.
Prefer scratch where suitable; actions requiring a complete environment may use
another base from the container allowlist without a tool-specific exception.
The [workflow contract](github-actions/references/job-contract.md) defines event
routing, dependencies, inputs/outputs, artifacts, and success criteria per job.
The [security policy](github-actions/references/security-policy.md) keeps SBOMs,
scans, advisory reviews, signing and signature verification non-blocking, with
visible findings/errors. Functional tests and exact-artifact/publication failures
remain blocking; a successful CI is not a security approval.
`commit` loads `conventionalcommits` before proactively committing implementation
work with a subject and why-body; explicit review-only/no-commit requests take priority.

## Install

The format is agent-independent; discovery paths and permissions belong to the
client. Check the supported skill directory or external-path registration in your
client's documentation. For a client supporting project `.agents/skills/`, copy
selected **whole folders** from this repository:

```bash
mkdir -p /path/to/project/.agents/skills
cp -R /path/to/this-repository/helm /path/to/project/.agents/skills/
```

Keep `references/` and `scripts/` with SKILL.md. Do not overwrite an existing skill
of the same name without reviewing it. Reload discovery as your client requires,
then verify that its execution trace actually loads the intended SKILL.md.
An agent without automatic discovery can read the skill and resolve its references
directly; that does not test automatic activation.

Install `commit` and `conventionalcommits` together: the companion is required,
not an optional message-format fallback. When using the collection's image policy,
also make `container` available to `helm` and `github-actions`.

### Migration from `opencode/`

The former `opencode/<name>/` folders now live at `<name>/`. Update external-path
registrations pointing to `.../skills/opencode` to `.../skills`, or replace copied
installations with the new whole folders. Remove stale duplicate registrations.
Client configuration syntax is version-specific; no OpenCode configuration is
required by this collection. Skill names are unchanged.

## Validate

The [CI workflow](docs/ci.md) uses dedicated Docker actions for repository checks,
lint and unit tests. Its source-action bootstrap still needs native ARM64/hosted
qualification and GHCR publication before transition to prebuilt digest references.

```bash
uv run .github/scripts/check_repository.py .
uv run --with PyYAML==6.0.3 --with markdown-it-py==4.0.0 --with mdurl==0.1.2 python tests/run.py
```

From the repository root (Python 3.10+ and [uv](https://docs.astral.sh/uv/) required):

```bash
uv run skill/scripts/validate.py --collection .
uv run --with PyYAML==6.0.3 python -m unittest discover -s skill/scripts
```

The read-only validator declares its pinned dependency inline, emits JSON, and
checks frontmatter plus explicit local Markdown links. First execution may download
dependencies. Exit codes: 0 valid, 1 validation failure, 2 command-line misuse.
Run `--help` for individual-skill validation. It does not execute domain tools,
check external links, count model tokens, or measure agent behavior.

The official [skills-ref](https://github.com/agentskills/agentskills/tree/main/skills-ref)
validator can also check each folder with `skills-ref validate ./helm`.
For the exact upstream revision used in this review:

```bash
uvx --from 'git+https://github.com/agentskills/agentskills.git@83021e2be457a9b6679148719c1f6074f0ad975e#subdirectory=skills-ref' skills-ref validate ./helm
```

This upstream installation requires Python 3.11+, Git, and initial network access.

## Evaluate

Every skill has `evals/evals.json`: behavioral cases and six labeled activation
queries, including near-misses. GitHub Actions also covers the workflow contract's
routing, release phases, maintenance isolation and artifact gates. These are **test specifications**, not
published benchmark results. Follow [the evaluation guide](docs/evaluation.md)
for fresh-session runs, baselines, grading, and description optimization.

See [the review report](docs/review.md) for findings corrected in this migration
and the limits of verification. Templates remain illustrative until adapted and
tested with the target application's tools, versions, and environment.

## Contribute

Follow [AGENTS.md](AGENTS.md) and the [authoring skill](skill/SKILL.md).
Keep changes grounded in actual workflows and failure cases. Use concise activation
descriptions, load detailed references on demand, and document intended companion
dependencies. Preserve user conventions during portability refactors. Use Python or `go run` for reusable utilities, with explicit runtimes,
pinned dependencies, noninteractive interfaces, and meaningful failure checks.

The specification defines the file format; body headings, evaluation JSON layout,
and repository layout are conventions. Use Conventional Commits for repository history.
