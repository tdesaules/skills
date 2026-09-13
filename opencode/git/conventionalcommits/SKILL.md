---
name: conventionalcommits
description: |-
  Write clear conventional commit messages and check message format (feat, fix, scope, BREAKING CHANGE). Use when committing changes, choosing a commit type, or deciding how to split a diff into commits.
  Examples:
  - user: "commit these changes" → format as a conventional commit with the right type and scope
  - user: "what type for a typo fix" → fix vs docs vs chore guidance
  - user: "should this be one commit or two" → split by logical unit of change, not by file
license: GPL-3.0-or-later
compatibility: opencode
metadata:
  audience: developers
  workflow: git-commit-message
---

# Conventional Commits

## What I do

- Draft commit messages in `<type>[scope][!]: <description>` format with optional body and footers
- Choose the right type (`feat`, `fix`, `docs`, `refactor`, `chore`, ...) and flag breaking changes (`!` / `BREAKING CHANGE:`)
- Review a staged diff and propose a correctly scoped, concise subject line

## When to use me

Use me when creating git commits, writing commit messages, or checking message format.
Use ONLY for commit messages per Conventional Commits v1.0.0, not for changelogs, versioning tooling, or branching strategy.
Ask clarifying questions if the change spans multiple logical units or the correct type/scope is ambiguous.

## Format

```
<type>[optional scope][optional !]: <description>

[optional body]

[optional footer(s)]
```

- `type`: noun such as `feat`, `fix` (others allowed: `build`, `chore`, `ci`, `docs`, `style`, `refactor`, `perf`, `test`, `revert`).
- `scope`: optional noun in parentheses, e.g. `feat(parser): ...`.
- `!`: optional, immediately before `:`, marks a breaking change.
- `description`: required short summary after `": "`.
- `body`: optional, one blank line after description, free-form paragraphs.
- `footers`: optional, one blank line after body; each is `Token: value` or `Token # value` (git-trailer style). Token uses `-` instead of spaces, except `BREAKING CHANGE` (uppercase, may contain a space; `BREAKING-CHANGE` is synonymous).

## Rules

1. `feat` = new feature (SemVer MINOR). `fix` = bug fix (SemVer PATCH).
2. Breaking change (SemVer MAJOR) = `!` in prefix and/or `BREAKING CHANGE: <description>` footer. Applies to any type.
3. Matching is case-insensitive, except `BREAKING CHANGE` which MUST be uppercase.
4. One logical change per commit; if a change fits two types, split it.
5. Keep the subject concise (aim <= 72 chars), imperative mood, no trailing period.

## Type lookup

Pick the type matching what changed, not how it felt to write:

| type       | when to use it                                              |
| ---------- | ----------------------------------------------------------- |
| `feat`     | new user-visible capability                                 |
| `fix`      | corrects broken behavior                                    |
| `docs`     | documentation only (a typo fix in prose is `docs`, not `fix`) |
| `style`    | formatting only, no logic change                            |
| `refactor` | restructures code without changing behavior                 |
| `perf`     | performance improvement without behavior change             |
| `test`     | tests only                                                  |
| `build`    | build system, dependencies, tooling config                  |
| `ci`       | CI pipeline configuration                                   |
| `chore`    | maintenance fitting nowhere else                            |
| `revert`   | reverts a previous commit                                   |

## Splitting changes into commits

Split by logical unit of change: each commit revertible independently without breaking the others. Separate an unrelated formatting pass from a real fix. On a large mixed diff, propose the groups and ask for confirmation instead of committing one lump.

## Examples

```
feat: allow provided config object to extend other configs

BREAKING CHANGE: `extends` key in config file is now used for extending other config files
```

```
feat!: send an email to the customer when a product is shipped
```

```
feat(api)!: send an email to the customer when a product is shipped
```

```
docs: correct spelling of CHANGELOG
```

```
feat(lang): add Polish language
```

```
fix: prevent racing of requests

Introduce a request id and a reference to latest request. Dismiss
incoming responses other than from latest request.

Remove timeouts which were used to mitigate the racing issue but are
obsolete now.

Reviewed-by: Z
Refs: #123
```

```
revert: let us never again speak of the noodle incident

Refs: 676104e, a215868
```

## Agent commit workflow

- Before committing, inspect `git status`, `git diff`, and `git log --oneline -10`.
- Stage only intended files; never commit secrets.
- Write a concise subject line matching the repo's existing style (`type[(scope)]: subject`).
- Only commit, amend, push, or open PRs when explicitly requested. Do not skip hooks, force-push, or create empty commits unless asked.
- If hooks reject the commit, fix the issue and create a new commit.

## References

- Spec v1.0.0: https://www.conventionalcommits.org/en/v1.0.0/
- Commitlint conventional types: https://github.com/conventional-changelog/commitlint/tree/master/@commitlint/config-conventional
- Git trailers: https://git-scm.com/docs/git-interpret-trailers
- SemVer: https://semver.org

## Registration note

This file lives at `opencode/git/conventionalcommits/SKILL.md`, outside OpenCode's default scan paths. Register it in `opencode.json`:

```json
{ "$schema": "https://opencode.ai/config.json",
  "skills": { "paths": ["opencode"] } }
```

Then quit and restart opencode (config is loaded once at startup).
