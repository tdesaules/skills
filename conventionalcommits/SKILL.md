---
name: conventionalcommits
description: >-
  Use when drafting or reviewing Conventional Commits messages, choosing feat/fix
  or another type and scope, or describing BREAKING CHANGE footers. Interpret a
  supplied diff to explain message choices. Covers message semantics, not staging,
  committing, rewriting history, or configuring release automation.
license: GPL-3.0-or-later
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
Inspect the supplied diff before asking; ask only when the missing intent changes the message.

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

The specification makes the body optional; this user's `commit` workflow requires
a why-body on every commit. Follow that stricter convention when creating messages
for the workflow. Message-format guidance does not disable its proactive behavior.

## Rules

1. `feat` = new feature (SemVer MINOR). `fix` = bug fix (SemVer PATCH).
2. Breaking change (SemVer MAJOR) = `!` in prefix and/or `BREAKING CHANGE: <description>` footer. Applies to any type.
3. Matching is case-insensitive, except `BREAKING CHANGE` which MUST be uppercase.
4. Prefer one logical change per commit. A feature with its tests and docs remains one unit; multiple file types do not require a split.
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

Propose independently revertible groups for unrelated changes. Keep necessary tests and docs with their implementation. This is message advice, not authorization to stage or commit.

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

## Workflow and output

1. Read the supplied change summary/diff and repository message conventions. If
   inspecting Git, include the staged diff; do not assume the working diff is the commit.
2. Identify intent, affected public interface, and any breaking change. Do not invent
   issue references or infer a breaking change merely from a large diff.
3. Choose a type and optional scope. Distinguish specification requirements from
   local style: lowercase types, imperative wording, and 72-character subjects are
   conventions; types beyond feat/fix do not have an inherent SemVer effect.
4. Return the proposed message in a code block with a short rationale when ambiguous.
   Check punctuation, footer syntax, and whether the breaking description explains
   impact/migration. Do not modify the index or history for message-only requests.

## References

- Spec v1.0.0: https://www.conventionalcommits.org/en/v1.0.0/
- Commitlint conventional types: https://github.com/conventional-changelog/commitlint/tree/master/@commitlint/config-conventional
- Git trailers: https://git-scm.com/docs/git-interpret-trailers
- SemVer: https://semver.org
