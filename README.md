# skills

Personal OpenCode skills collection (GPL-3.0, see `LICENSE`).

Layout is `opencode/<skill>/SKILL.md`; nesting allowed
(e.g. `opencode/git/conventionalcommits/SKILL.md`).

## Skills

| Skill                                            | What it does                                                        |
| ------------------------------------------------ | ------------------------------------------------------------------- |
| [chezmoi](opencode/chezmoi/SKILL.md)              | Manage dotfiles with chezmoi: safe apply workflow, templates, scripts, secrets |
| [conventionalcommits](opencode/git/conventionalcommits/SKILL.md) | Write Conventional Commits messages: types, scopes, breaking changes, splitting |
| [commit](opencode/git/commit/SKILL.md) | Stage and commit proactively, one commit per logical unit; local amend/fixup |
| [skill](opencode/skill/SKILL.md)                 | Write, review, and test OpenCode skills: frontmatter, selectivity, output contract, 4-case testing |

## Use these skills

This repo lives outside OpenCode's default scan paths, so register it:

```json
{ "$schema": "https://opencode.ai/config.json",
  "skills": { "paths": ["opencode"] } }
```

(`paths` entries are relative to the declaring config; absolute paths also
work.) Then quit and restart opencode — config loads once at startup.

Alternatives: clone this repo (or a subdir) directly into
`~/.config/opencode/skills/` or `.opencode/skills/`, which OpenCode scans
automatically.

## Contribute

- One folder per skill, file named exactly `SKILL.md`, folder name ==
  frontmatter `name` (`^[a-z0-9]+(-[a-z0-9]+)*$`, 1–64 chars).
- `description` 1–1024 chars: what + when, trigger keywords first, plus an
  `Examples:` block mapping user utterances to behavior.
- Body opens with `## What I do` / `## When to use me`; imperative voice;
  detail goes in `references/`.
- Full authoring guidance: [opencode/skill/SKILL.md](opencode/skill/SKILL.md).
- Commits follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).
