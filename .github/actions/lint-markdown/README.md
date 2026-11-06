# Markdown lint action

Native Docker action with no inputs. The fixed Go entrypoint invokes the bundled
markdownlint-cli2 on Markdown files, including action documentation, excluding
node_modules and evaluation workspaces. The checkout's .markdownlint.json controls
layout rules. Exit 1 reports violations; execution is read-only and offline.

Build from this folder's Containerfile; Dockerfile is its GitHub-compatible symlink.
Qualification checks clean input and a trailing-whitespace defect.
See [shared qualification and publication instructions](../README.md).
