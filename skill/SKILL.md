---
name: skill
description: >-
  Use when creating, reviewing, or refactoring Agent Skills (SKILL.md), improving
  their activation descriptions, organizing references and scripts, or designing
  skill evaluations. Diagnose missing discovery separately from poor triggering
  or output quality. Not for general agent configuration, MCP servers, or plugins.
license: GPL-3.0-or-later
---

# Author Agent Skills

## Scope

Create portable skills following the Agent Skills specification. Treat client
discovery paths and tool names as integration details, not format requirements.

Portability between agents does not require generic behavior between users.
Preserve explicit repository/user conventions (workflow layout, tools, registries,
commit policy) during refactors. Label their scope separately from platform rules;
do not remove or relax them without the user's instruction.

## Workflow

1. Read the user's real examples, corrections, project artifacts, and existing
   skill. Identify one coherent task, its inputs, expected outputs, and boundaries.
   Do not replace domain expertise with generic best-practice lists.
2. Create `<name>/SKILL.md`: YAML frontmatter followed by Markdown instructions.
   Keep scripts, references, and assets inside that folder. Prefer standalone skills,
   but preserve intentional companion dependencies: document them and how to load
   or read them without a client-specific tool ID. Do not silently make them optional.
3. Write a concise description beginning with when to use the skill. Include user
   intent and near-miss boundaries; keep examples in the body or evals instead of
   spending startup context on long example lists.
4. Write a short procedure with defaults, decision points, non-obvious gotchas,
   verification, and an observable output contract. Be precise where operations
   are fragile; allow judgment elsewhere. Avoid restating basic domain knowledge.
5. Put detailed material in `references/`; link directly from SKILL.md and say when
   to read each file. Use paths relative to the skill root. Avoid reference chains.
   Keep SKILL.md below 500 lines and approximately 5,000 tokens (recommendations,
   not hard validity constraints). Assets are output resources, not instructions.
6. Bundle a script only for recurring deterministic work. Follow
   [script interfaces](references/scripts.md) when adding one. Prefer Python for
   small utilities and `go run` for Go tools; reuse the project's existing tooling.
7. Validate structure, inspect local links, then run behavioral evaluations using
   [the evaluation protocol](references/evaluation.md). Fix failures and rerun the
   affected cases plus a passing regression. Stop when gains stop being meaningful.

## Frontmatter contract

| Field | Constraint |
| --- | --- |
| `name` | Required, 1–64 lowercase alphanumeric/hyphen characters; no leading, trailing or consecutive hyphens; matches the containing folder. Use ASCII names for broad client compatibility. |
| `description` | Required, nonempty, at most 1,024 characters; says what and when. |
| `license` | Optional rights label or bundled license reference; only claim rights you can grant. |
| `compatibility` | Optional, 1–500 characters describing actual environment requirements. Omit for pure guidance. |
| `metadata` | Optional string-to-string map. |
| `allowed-tools` | Optional space-separated string; experimental and client-dependent. Does not grant permissions by itself. |

Use YAML block scalars for descriptions containing colons. Put custom properties
under `metadata`; do not rely on every client ignoring unknown top-level fields.

The Markdown body has no prescribed headings. What I do/When to use me sections,
an Examples block in the description, and third-person descriptions are not format
requirements. Follow the description guide's concise imperative activation phrasing;
include examples where they improve decisions, usually in the body or evaluations.

## Validation script

Run from this skill's directory, passing the target skill or collection explicitly:

```bash
uv run scripts/validate.py /absolute/path/to/skill
uv run scripts/validate.py --collection /absolute/path/to/collection
```

Requires Python 3.10+ and uv (or Python with the pinned PyYAML dependency installed).
The script is read-only, emits JSON, and exits 0 for valid input, 1 for validation
failures, 2 for command-line misuse. It checks format and local Markdown links,
not model behavior, external URLs, or token counts. Cross-check with the official
`skills-ref validate <skill-directory>` when available.

## Diagnose the correct layer

- Absent: inspect the actual client's discovery configuration, folder layout,
  frontmatter, duplicate names, and permissions. Consult its versioned docs.
- Wrong activation: inspect the description and observe actual SKILL.md loading
  in fresh-session traces; a plausible answer is not evidence of activation.
- Poor output: inspect procedure, missing expertise, references, and task artifacts.
- Command failure: inspect runtime/dependencies rather than rewriting the trigger.

## Output

Report changed paths, structural checks and results, behavioral cases actually run,
and remaining failures. For reviews use `file:line → defect → impact → correction`.
Separate recommended improvements from specification violations. Never label
authored eval cases or a static validator result as measured effectiveness.

## Sources

- [Specification](https://agentskills.io/specification)
- [Quickstart](https://agentskills.io/skill-creation/quickstart)
- [Best practices](https://agentskills.io/skill-creation/best-practices)
- [Descriptions](https://agentskills.io/skill-creation/optimizing-descriptions)
- [Evaluations](https://agentskills.io/skill-creation/evaluating-skills)
- [Scripts](https://agentskills.io/skill-creation/using-scripts)
