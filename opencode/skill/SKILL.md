---
name: skill
description: |-
  Write, review, and fix OpenCode skills (SKILL.md frontmatter, description, body, references, testing). Use when creating a new skill, updating an existing skill, or debugging skill discovery and loading.
  Examples:
  - user: "create a skill for reviewing pull requests" → scaffold folder, frontmatter, scope sections, workflow, validation
  - user: "why doesn't my skill load" → diagnose file path, ID, description, and permissions layer by layer
  - user: "improve this skill description" → selective rewrite plus match/no-match checks
license: GPL-3.0-or-later
compatibility: opencode
metadata:
  audience: skill-authors
  workflow: skill-authoring
---

# Skill

## What I do

- Scaffold new skills: folder, frontmatter, scope sections, workflow, validation
- Review descriptions for selectivity (right triggers, no hijacking)
- Give bodies an output contract (inputs, procedure, checkable result)
- Split supporting material into `references/` and test with positive/negative/ambiguous/boundary cases

## When to use me

Use me when creating a new skill, updating an existing skill, or debugging why a skill never loads or loads at the wrong time.
Use ONLY for OpenCode skill authoring, not for agents, commands, MCP servers, or plugins.
Ask clarifying questions if the skill's trigger utterances or its boundary with neighboring skills is unclear.

## Anatomy

```
<skill-id>/
├── SKILL.md        # required: frontmatter + instructions
├── scripts/        # optional: deterministic executables (run, not read into context)
├── references/     # optional: docs loaded on demand (schemas, policies, cheatsheets)
└── assets/         # optional: output material (templates, images, boilerplate)
```

Progressive disclosure: metadata (~100 words, always in context) → `SKILL.md` body (<5k words, on load) → bundled files (only when read or executed). Keep the body lean; move detail to `references/`.

## Frontmatter

| Field           | Rule (OpenCode v1)                                                        |
| --------------- | ------------------------------------------------------------------------- |
| `name`          | Required. Folder name == `name`. `^[a-z0-9]+(-[a-z0-9]+)*$`, 1–64 chars. |
| `description`   | Required. 1–1024 chars, third person. No skill without one is advertised. |
| `license`       | Optional. Only a rights label you can actually grant.                     |
| `compatibility` | Optional, e.g. `opencode`.                                                |
| `metadata`      | Optional string-string map (`audience`, `workflow`, ...).                 |

Quote the description if it contains `": "`. Unknown fields are ignored.

## Description selectivity

Name an object, an activity, and a stage of work — not a topic. Compare "Helps with databases" with "Review database migrations for data loss, locking, and recovery constraints before deployment."

- Front-load literal keywords the user would type (commands, filenames, error text).
- Append an `Examples:` block mapping utterances to behavior (see this skill's frontmatter).
- Self-test: write three requests that should match and three that should not. If both lists feel equally relevant, narrow the description or split the skill. Gate adjacent topics with "Use ONLY when...".

## Body

- Open with `## What I do` / `## When to use me` scope sections.
- Write imperative, verb-first instructions ("Inspect X, then do Y"), not second-person advice.
- Structure around decisions with an output contract: what to read, what to check, what evidence each finding needs, where to stop. A finding without evidence and consequence is unverifiable.
- Keep instructions and references distinct: main decision process in `SKILL.md`; large material in `references/` with a line stating when to read each file. If a reference exceeds ~10k words, add grep patterns. Never duplicate content between body and references.
- Scripts are for repeated or deterministic work (document inputs, outputs, file effects). Assets are output material, never context.

## Discovery and registration

Default scan paths: `.opencode/skills/`, `~/.config/opencode/skills/`, `.claude/skills/`, `.agents/skills/` (global + project). File must be `SKILL.md` in its own folder.

Skills outside those paths (like this repo's `opencode/` dir) need explicit registration, then a restart (config loads once at startup):

```json
{ "$schema": "https://opencode.ai/config.json",
  "skills": { "paths": ["opencode"] } }
```

Notes:

- In v1 (incl. 1.18.x) the ID is the folder and must equal `name`; duplicate IDs across sources: last source wins, so avoid collisions unless overriding on purpose.
- v2 changes the shape (`skills` becomes an array, IDs are path-derived, frontmatter `name` is display-only). Check `opencode --version` before applying v2-only advice.
- Only ID + name + description are advertised per model step; the body loads on demand via the `skill` tool. Supporting files never auto-load.

## Diagnose the correct layer

- Skill absent → file path (`SKILL.md` all caps?), folder/`name` match, valid YAML, registered path, unique ID, `skill` permission (`deny` hides it).
- Loads at wrong time → description too broad or missing `Examples:`; re-run one positive and one negative prompt after each change.
- Loads but performs poorly → procedure lacks an output contract or contradicts a reference.
- Command inside fails → project toolchain problem, not a skill problem.

Verify loading explicitly: ask to load the skill by ID and report its required output format, without running the task. An answer from the name alone proves nothing.

## Testing

Test behavior, not polish. Build a tiny fixture with one intentional defect and run four cases:

| Case      | Example                              | Expected                          |
| --------- | ------------------------------------ | --------------------------------- |
| Positive  | Fixture contains the defect          | Reported with evidence            |
| Negative  | Fixture is clean                     | No manufactured defect            |
| Ambiguous | Required value undocumented          | Missing info stated, not guessed  |
| Boundary  | Request touches out-of-scope actions | Stops at the requested boundary   |

Compare against a no-skill baseline with the same prompt, repeat runs that matter, and inspect artifacts (diffs, files, checks) — never trust a final "validated" message alone. Turn recurring failures into regression fixtures: smallest reproducing input, one instruction change, re-run a passing case to catch over-correction.

## Anti-patterns

- Detailed body compensating for a vague description (or vice versa).
- Keyword stuffing that hijacks unrelated tasks.
- Duplicated content in body and `references/`.
- Unverified `license` labels; invented file paths; tokens or private data in fixtures.
- Changing every layer at once when only one layer failed.

## References

- Skills (v1): https://opencode.ai/docs/skills/
- Skills (v2): https://opencode.ai/v2/docs/skills
- SKILL.md format: https://opencodeskills.dev/guides/skill-md-format/
- Discovery and loading: https://opencodeskills.dev/guides/discovery-and-loading/
- Testing skills: https://opencodeskills.dev/guides/test-opencode-skills/
