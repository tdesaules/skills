---
name: commit
description: |-
  Stage and commit changes proactively, one commit per logical unit (stage only concerned files, meaningful subject plus why-body). Use when committing changes, staging files, splitting a diff, or fixing local history with amend/fixup.
  Examples:
  - user: "commit these changes" → inspect, group, stage paths, commit per unit
  - user: "should this be one commit or two" → split by independently revertable unit
  - user: "fix the last commit message" → amend or fixup without touching remote
license: GPL-3.0-or-later
compatibility: opencode
metadata:
  audience: developers
  workflow: git-commit-workflow
---

# Commit

## What I do

- Inspect the working tree (`status`, `diff`, recent `log`) and group changes by logical unit
- Stage only the files concerned by one unit, then commit with a meaningful subject plus a why-body
- Split mixed diffs into independently revertable commits
- Fix local history with `amend`/`fixup`, never touching pushed history

## When to use me

Use me when committing changes, staging files, splitting a diff, or fixing a commit message or content locally.
Use ONLY for the local commit workflow. Not for push, pull requests, changelogs, or branching strategy. For message *format* rules, load the `conventionalcommits` skill.
Proactive by default: inspect, stage, and commit without asking, unless a guardrail below stops me — then report instead of committing.

## Prerequisite

Load the `conventionalcommits` skill first (single source of truth for message format). Never duplicate its format rules here.

## Workflow

1. **Inspect.** Run `git status --short`, `git diff --stat` (plus full `git diff` when needed), and `git log --oneline -10` for repo style.
2. **Group.** Split changes by logical unit of change: each group independently revertable without breaking the others. Unrelated formatting vs real fix → separate commits. New capability vs repo docs → separate commits.
3. **Stage.** `git add <explicit paths>` per group. Never `git add -A` / `git commit -a` unless the whole tree is verified as one unit.
4. **Draft.** One subject (imperative, concise, repo style) plus a body explaining *why*, not a narration of the diff. Ambiguous split → propose the groups and wait for confirmation.
5. **Verify, then commit.** Re-read `git diff --cached`; confirm no secrets and hooks green; commit. Then `git show --stat HEAD` as a sanity check.

## Proactive guardrails (stop and report)

- Empty diff for the group — nothing to commit.
- Possible secret staged (tokens, private keys, credentials) — never commit secrets.
- Hook rejects and the failure is not clearly fixable — never bypass with `--no-verify` unless explicitly asked.
- Commit would rewrite pushed history — stop; propose a new commit instead.
- Split is genuinely ambiguous — propose groups with draft messages and wait.

## Amend and fixup (local history only)

- Allowed only when the commits are unpublished: verify no upstream contains them (e.g. `git status -sb` shows no tracking ahead/behind confusion — when in doubt, ask).
- `git commit --amend` to correct the last commit's message or content.
- `fixup` + `git rebase -i --autosquash` to fold a fix into an older local commit.
- Never amend, fixup, rebase, or force-push history others may have pulled.

## Anti-patterns

- One lump commit ("update", "wip", "various fixes") for mixed changes.
- Staging everything blindly, sweeping unrelated files into a scoped commit.
- Subject paraphrasing the diff instead of stating intent; body narrating lines instead of reasons.
- Committing generated artifacts or local-only files that belong in `.gitignore`.
- Implicit push after committing — pushing stays manual unless explicitly requested.

## References

- Conventional Commits v1.0.0: https://www.conventionalcommits.org/en/v1.0.0/
- Companion skill for format rules: `conventionalcommits` (load by ID)
