# AGENTS.md

Skills repo (GPL-3.0). Layout: `opencode/<skill>/SKILL.md`, flat — no nesting
(OpenCode v1 discovers a single level under each registered path).

## Response style

- Keep responses **short and concise**. No preamble/postamble, no fluff.

## Skills (non-standard path)

- Files here are **not** auto-discovered: OpenCode only scans `.opencode/skills/`,
  `~/.config/opencode/skills/`, `.claude/skills/`, `.agents/skills/`.
  Consumers must register this repo's dir and restart opencode:
  `{"skills": {"paths": ["opencode"]}}` (+ `"$schema": "https://opencode.ai/config.json"`).
- Per skill, all required, verified before commit:
  - `SKILL.md` all caps, folder name == frontmatter `name`,
    `^[a-z0-9]+(-[a-z0-9]+)*$` (1–64 chars).
  - `description` 1–1024 chars, third person, covers what + when, front-loads
    literal trigger keywords the user would type, plus an `Examples:` block
    mapping utterances to behavior.
  - Optional: `license: GPL-3.0-or-later`, `compatibility: opencode`,
    `metadata` (string-string map).
- Body convention: `## What I do` / `## When to use me` scope sections first
  (per https://opencode.ai/docs/skills/), gate with "Use ONLY when..." for
  adjacent topics. Imperative voice, output contract, detail in `references/`.
- Authoring guidance lives in-skill: `opencode/skill/SKILL.md` (anatomy,
  selectivity self-test, layer-by-layer diagnosis, 4-case testing).
- Validate: `python3 -c` check on name/dir-match/regex + `len(description)`.

## Git workflow

- **Conventional Commits** (`feat:`, `fix:`, `docs:`, `refactor:`, `chore:`).
  Skill available: `opencode/conventionalcommits/SKILL.md`.
- Commit workflow (inspect, stage per unit, verify, amend/fixup): see
  `opencode/commit/SKILL.md`. Proactive commits allowed, but stop on
  empty diff, secrets, hook failure, or pushed history.
- Commit only when explicitly requested. **Never push** — user pushes manually.
- When adding a skill, also add its row to `README.md`.
