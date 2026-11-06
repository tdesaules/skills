---
name: chezmoi
description: >-
  Use when managing chezmoi dotfiles: adding files, previewing or applying changes,
  writing host-specific templates, run scripts, or external dependencies. Diagnose
  source/target drift and render failures. Applies to chezmoi-managed files, not
  arbitrary .tmpl files or bare Git and symlink-based dotfile setups.
license: GPL-3.0-or-later
compatibility: Requires chezmoi; Git for source history and configured secret providers when used.
metadata:
  audience: dotfiles-maintainers
  workflow: chezmoi-apply-verify
---

# Chezmoi

## What I do

- Guide the safe chezmoi workflow: `doctor`, `status`, `diff`, then `apply`
- Explain source state attributes (`dot_`, `private_`, `executable_`, `run_*`, `.tmpl`)
- Help write templates, `run_onchange_`/`run_once_` scripts, externals, and secret handling
- Provide copy-pasteable commands for daily dotfile operations

## When to use me

Use me when editing chezmoi-managed dotfiles, source-state templates/scripts, or externals.
Use ONLY for chezmoi-managed dotfiles, not for bare-git or symlink-only setups.
Ask clarifying questions if it is unclear whether the files are chezmoi-managed or which target machine is concerned.

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
chezmoi edit "$FILE"      # interactive editor; prefer direct source edits in noninteractive agents
chezmoi edit --apply "$FILE"
chezmoi edit --watch "$FILE" # interactive local workflow only
chezmoi update            # `git pull --autostash --rebase` in source dir + `apply`
chezmoi cd                # subshell in source dir for manual `run_*`/rename work
```

Rules:

- Preview before apply: `status` then `diff`, then `apply`.
- In a noninteractive agent, resolve `chezmoi source-path "$FILE"`, edit that source
  with available file tools, then render/preview. Use `chezmoi edit` only with a usable editor.
- Use `chezmoi data` to inspect template variables, `chezmoi cat $FILE` to print the rendered target without writing, `chezmoi execute-template '{{ .chezmoi.hostname }}'` to debug fragments.
- Never run `sed`/`gsub` over `*.tmpl` files expecting rendered output; `{{ }}` directives must be preserved.
- Inspect `autoCommit`/`autoPush` before mutating commands. Commit or push only within
  the user's request and repository policy; an apply preview does not authorize either.

## Source state attributes

State is encoded in source filenames. Order of prefixes matters; rename or use `chezmoi chattr`.

Common prefixes: `dot_` (`.foo`), `private_` (remove group/other perms), `readonly_`, `empty_`, `executable_` (`+x`), `exact_` (prune unmanaged), `create_`/`modify_`/`remove_` (file lifecycle), `symlink_`, `run_` (script), `once_`/`onchange_` + `before_`/`after_` (script lifecycle). Common suffix: `.tmpl` (render as template).

Examples:

- `dot_gitconfig.tmpl` -> `~/.gitconfig` (templated)
- `private_dot_ssh/private_config` -> `~/.ssh/config` (mode `0600`)
- `dot_local/bin/executable_tool` -> `~/.local/bin/tool` (`+x`)
- `run_onchange_after_01-systemd.sh.tmpl` -> script, re-runs only when rendered content changes, after file updates

## Special files and directories

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
{{ .mysection.key }}                       {{/* data must define a mysection map */}}
{{- if eq .chezmoi.os "linux" }} ... {{ end }}
{{- if and (eq .chezmoi.os "linux") (ne .email "me@home.org") }} ... {{ end }}
# {{ include "other-file" | sha256sum }}
{{ includeTemplate "logging.tmpl" }}       {{/* shared helper, no data */}}
{{ template "part.tmpl" . }}               {{/* pass current data */}}
{{ template "alacritty" (dict "fontsize" 12 "font" "DejaVu Sans") }}
```

Rules:

- Put structured values in `.chezmoidata/*.yaml`; define the actual map hierarchy
  in file contents. A filename does not automatically introduce a template namespace.
- Share rendered helpers via `.chezmoitemplates/` and `template`/`includeTemplate`;
  `include` reads source content and does not by itself render that content as a template.
- Create templates with `chezmoi add --template $FILE` or `chezmoi chattr +template $FILE`.
- Trim whitespace deliberately with `{{-` / `-}}`.

## Secrets

Never hardcode tokens. Use a password-manager template function with `| trim`:

```gotemplate
{{ gopass "path/to/entry" | trim }}
{{ gopass `path/with/special-chars` | trim }}
```

Mark secret-bearing files `private_`. Rendering and diffing may expose secret values;
inspect only the relevant output and redact it in reports. Do not assume a generic
`redact = true` setting protects arbitrary environment variables or command output.

## Externals and rate limits

- Prefer static archive URLs; pin versions where reproducibility matters.
- Functions resolving "latest release" call the GitHub API and exhaust the unauthenticated rate limit fast. Run applies with `GITHUB_TOKEN` set when externals use them.

## Anti-patterns

- Editing the wrong clone: confirm the working source dir first (`chezmoi source-path`), then edit there.
- `apply` without `diff`, especially with `sudo`/`once` scripts pending.
- Non-idempotent scripts or scripts without hash triggers for their inputs.
- `exact_` dirs without understanding prune semantics.
- Enabling `autoPush` on a public repo while secrets could be added in plain text.

## Validation and output

Confirm the actual source and target paths before editing. Render changed templates
with `chezmoi cat` or `execute-template`, inspect targeted status/diff, then apply
only when requested. Recheck targeted status after apply. Use `doctor` for environment
failures. Exercise scripts in an isolated source/destination before modifying the
real home directory; an apply can execute scripts as well as write files.

Report source files changed, destination scope, preview/render results, and whether
apply actually ran. For review findings include file/line, effect, and correction.
Example: "Make my Git identity host-specific" → inspect current data, template the
managed gitconfig, render for the target host, preview, and report unresolved values.

## References

- Command overview: https://www.chezmoi.io/user-guide/command-overview/
- Daily operations: https://www.chezmoi.io/user-guide/daily-operations/
- Scripts: https://www.chezmoi.io/user-guide/use-scripts-to-perform-actions/
- Templating: https://www.chezmoi.io/user-guide/templating/
- Concepts: https://www.chezmoi.io/reference/concepts/
- Source state attributes: https://www.chezmoi.io/reference/source-state-attributes/
- Special files/dirs: https://www.chezmoi.io/reference/special-files/
