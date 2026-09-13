---
name: chezmoi
description: Manage dotfiles with chezmoi (add, edit, status, diff, apply, update, templates, scripts). Use when editing dotfiles, chezmoi source state, .tmpl files, .chezmoiscripts, or .chezmoiexternal.
license: GPL-3.0-or-later
compatibility: opencode
metadata:
  audience: dotfiles-maintainers
  workflow: chezmoi-apply-verify
---

# Chezmoi

Use ONLY for chezmoi-managed dotfiles. Not for bare-git or symlink-only setups.

## Concepts

- `destination dir`: what chezmoi manages (usually `~`).
- `source dir`: where chezmoi stores desired state (default `~/.local/share/chezmoi`, override with `-S` or `sourceDir`).
- `source state`: regular files/dirs in source dir; state encoded in filenames.
- `target state`: desired destination computed from source state + config + data.
- `working tree`: git checkout; often equals source dir.
- `config file`: machine data (default `~/.config/chezmoi/chezmoi.toml`).

## Safe daily workflow

```bash
chezmoi doctor            # on any surprise, run first
chezmoi status            # what `apply` would change (quick summary)
chezmoi diff              # what `apply` would change (full diff)
chezmoi apply [target...] # write target state to destination
chezmoi edit $FILE        # edit source file for $FILE, then `apply` separately
chezmoi edit --apply $FILE
chezmoi edit --watch $FILE
chezmoi update            # `git pull --autostash --rebase` in source dir + `apply`
chezmoi cd                # subshell in source dir for manual `run_*`/rename work
```

Rules:

- Preview before apply: `status` then `diff`, then `apply`.
- Prefer `chezmoi edit` over hand-editing source files: it checks template syntax on quit.
- Use `chezmoi data` to inspect template variables, `chezmoi cat $FILE` to print the rendered target without writing, `chezmoi execute-template '{{ .chezmoi.hostname }}'` to debug fragments.
- Never run `sed`/`gsub` over `*.tmpl` files expecting rendered output; `{{ }}` directives must be preserved.
- Commit with normal git in the source dir (`git add/commit/push`); treat `autoCommit`/`autoPush` with care (a plain-text secret would be pushed).

## Source state attributes

State is encoded in source filenames. Order of prefixes matters; rename or use `chezmoi chattr`.

Common prefixes: `dot_` (`.foo`), `private_` (remove group/other perms), `readonly_`, `empty_`, `executable_` (`+x`), `exact_` (prune unmanaged), `create_`/`modify_`/`remove_` (file lifecycle), `symlink_`, `run_` (script), `once_`/`onchange_` + `before_`/`after_` (script lifecycle). Common suffix: `.tmpl` (render as template).

Examples:

- `dot_gitconfig.tmpl` -> `~/.gitconfig` (templated)
- `private_dot_ssh/private_config` -> `~/.ssh/config` (mode `0600`)
- `dot_local/bin/executable_tool` -> `~/.local/bin/tool` (`+x`)
- `run_onchange_after_01-systemd.sh.tmpl` -> script, re-runs only when rendered content changes, after file updates

## Special files and directories (evaluation order)

1. `.chezmoiroot` — alternate source-state path.
2. `.chezmoi.<format>.tmpl` — generates config on `init` / `--init`.
3. `.chezmoidata.<format>` or `.chezmoidata/` — template data, read before rendering.
4. `.chezmoitemplates/` — shared partials, always parsed as templates.
5. `.chezmoiignore` — patterns chezmoi must not deploy (e.g. `README.md`, templates dir).
6. `.chezmoiremove` — targets to remove on `apply`.
7. `.chezmoiexternal.<format>` / `.chezmoiexternals/` — archives or git repos materialized as source state (`type = "archive" | "git-repo"`, `exact`, `stripComponents`, `include`).
8. `.chezmoiversion` — minimum chezmoi version; operation aborts if older.

Keep meta files (`README.md`, `LICENSE`, templates helpers) in `.chezmoiignore` so they never deploy.

## Scripts

Files with prefix `run_` execute on `apply`, in lexical order. Use numeric ordering (`01-`, `02-`, ... `99-`).

- `run_` — every `apply`.
- `run_once_` — once per unique rendered content (hash stored in `scriptState`).
- `run_onchange_` — when rendered content changes (hash stored in `entryState`).
- `run_once_before_` / `run_onchange_after_` — position relative to file updates.
- Suffix `.tmpl` renders first; empty/whitespace-only output skips execution (useful for OS gating).

Best practices:

- All scripts must be idempotent, including `once`/`onchange`.
- Gate portability in the template, not the shell: `{{- if eq .chezmoi.os "linux" }}...{{ end }}` or tool-presence booleans computed from `lookPath`.
- Re-run when a dependency changes by hashing it into the script:
  `# {{ include "path/to/dependency" | sha256sum }}`
  Add one hash line per file that must trigger a re-run.
- External archives cannot be hashed via `include`; hash their resolved version (e.g. release tag) instead.
- Include a `#!` line; no need to set `+x` in source.
- Reset state only deliberately:
  `chezmoi state delete-bucket --bucket=entryState` (onchange),
  `chezmoi state delete-bucket --bucket=scriptState` (once).
- Flag scripts needing `sudo` or interaction clearly; keep a final always-run `run_after_99-*` idempotent if bootstrap markers are needed.

## Templating

A file is a template if it has suffix `.tmpl` or lives under `.chezmoitemplates/`. Syntax is Go `text/template` + `sprig` + chezmoi functions.

Data precedence (later wins): `.chezmoi.*` (OS, arch, hostname, `osRelease`) < `.chezmoidata/*` (your structured config) < `[data]` section of config file.

```gotemplate
{{ .chezmoi.hostname }}                    {{/* machine value */}}
{{ .chezmoi.osRelease.versionID }}         {{/* e.g. Fedora release */}}
{{ .mysection.key }}                       {{/* from .chezmoidata/mysection.yaml */}}
{{- if eq .chezmoi.os "linux" }} ... {{ end }}
{{- if and (eq .chezmoi.os "linux") (ne .email "me@home.org") }} ... {{ end }}
# {{ include "other-file" | sha256sum }}
{{ includeTemplate "logging.tmpl" }}       {{/* shared helper, no data */}}
{{ template "part.tmpl" . }}               {{/* pass current data */}}
{{ template "alacritty" (dict "fontsize" 12 "font" "DejaVu Sans") }}
```

Rules:

- Put structured values (paths, ports, names) in `.chezmoidata/*.yaml`, access as `{{ .section.key }}`; do not inline them across templates.
- Share helpers via `.chezmoitemplates/` (logging, colors) and `include` them; do not hand-roll per-script variants.
- Create templates with `chezmoi add --template $FILE` or `chezmoi chattr +template $FILE`.
- Trim whitespace deliberately with `{{-` / `-}}`.

## Secrets

Never hardcode tokens. Use a password-manager template function with `| trim`:

```gotemplate
{{ gopass "path/to/entry" | trim }}
{{ gopass `path/with/special-chars` | trim }}
```

Mark secret-bearing files `private_` and set `redact = true` on secret env vars so they do not leak via env dumps.

## Externals and rate limits

- Prefer static archive URLs; pin versions where reproducibility matters.
- Functions resolving "latest release" call the GitHub API and exhaust the unauthenticated rate limit fast. Run applies with `GITHUB_TOKEN` set when externals use them.

## Anti-patterns

- Editing the wrong clone: confirm the working source dir first (`chezmoi source-path`), then edit there.
- `apply` without `diff`, especially with `sudo`/`once` scripts pending.
- Non-idempotent scripts or scripts without hash triggers for their inputs.
- `exact_` dirs without understanding prune semantics.
- Enabling `autoPush` on a public repo while secrets could be added in plain text.

## References

- Command overview: https://www.chezmoi.io/user-guide/command-overview/
- Daily operations: https://www.chezmoi.io/user-guide/daily-operations/
- Scripts: https://www.chezmoi.io/user-guide/use-scripts-to-perform-actions/
- Templating: https://www.chezmoi.io/user-guide/templating/
- Concepts: https://www.chezmoi.io/reference/concepts/
- Source state attributes: https://www.chezmoi.io/reference/source-state-attributes/
- Special files/dirs: https://www.chezmoi.io/reference/special-files/

## Registration note

This file lives at `opencode/chezmoi/SKILL.md`, outside OpenCode's default scan paths. Register it in `opencode.json`:

```json
{ "$schema": "https://opencode.ai/config.json",
  "skills": { "paths": ["opencode"] } }
```

Then quit and restart opencode (config is loaded once at startup).
