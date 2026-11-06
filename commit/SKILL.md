---
name: commit
description: >-
  Use when staging or committing Git changes, completing implementation work with
  proactive commits, splitting mixed diffs, or amending/fixing up unpublished local
  history. Commit one logical unit at a time with a subject and why-body. Load
  conventionalcommits first; message-only requests remain its scope.
license: GPL-3.0-or-later
compatibility: Requires Git, the conventionalcommits companion skill, and the repository's configured checks and hooks.
---

# Local commit workflow

## Scope

Proactive by default: after implementation work, inspect, group, stage and commit
the task's changes without asking for routine approval. Include one logical unit
per commit and a meaningful subject plus a body explaining why. Respect explicit
review-only, proposal-only, or no-commit requests and repository restrictions.
Stop on empty groups, secrets, unresolved hook/check failures, genuinely ambiguous
ownership/splits, or a rewrite of published history. Pushing remains a separate task.

## Required companion

Load and read `conventionalcommits` before drafting or creating commits; it is the
single source of truth for message format. Use the client's skill-loading mechanism
or read the installed companion's SKILL.md directly, without assuming a specific
tool name or installation path. If unavailable, report the missing prerequisite
instead of silently skipping it. Install both skills together.

## Workflow

1. Inspect `git status --short`, `git diff`, `git diff --cached`, and
   `git log --oneline -10`. Read repository instructions. Account for pre-existing
   staged changes, untracked files, and partially staged files before touching the index.
2. Group changes by independently revertible intent. Keep a feature with its
   necessary tests/docs; separate unrelated formatting. Explain genuinely ambiguous
   groups before staging rather than guessing ownership.
3. Stage explicit paths per group; stage only the intended hunks in mixed files.
   Use an index-only patch when no interactive terminal is available. Do not reset,
   overwrite, or include unrelated staged work. If the current index cannot be
   safely separated with the available tools, report the conflict.
4. Follow the loaded conventionalcommits skill. Draft a concise imperative subject
   and **always include a body explaining why** the change is needed, not a narration
   of changed lines. Do not invent rationale; resolve missing consequential intent.
5. Run the relevant checks. Re-read `git diff --cached` and its scope before committing.
   Stop on an empty group, credentials, or unresolved check/hook failures. Do not
   bypass hooks. If a hook modifies files, inspect and stage only intended fixes.
6. Commit each unit, then inspect `git show --stat HEAD` and `git status --short`.
   Confirm the committed content and that unrelated work remains intact.

## Amend and fixup

Only rewrite history when the request/policy authorizes it and the commits are
known to be unpublished. Inspect upstream configuration and
`git branch -r --contains <commit>`; absence from cached remote refs is not proof
of non-publication when refs are stale or another remote exists. If uncertain,
ask or create a new commit when that satisfies the request.

Use `git commit --amend` for the last local commit or a fixup plus autosquash for
older local commits. Use a noninteractive sequence editor only with an inspected,
explicit rebase plan. Never infer unpublished status from `git status -sb` alone.

## Output

Report commit hashes and subjects, checks run, and remaining changes/blockers.
For a proposal-only request, return groups and draft messages without changing Git.
