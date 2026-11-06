# Python lint action

Native Docker action with no inputs. The fixed Go entrypoint runs
`ruff check --no-cache .`, using the checkout's ruff.toml.
Ruff is bundled; execution needs neither network nor source writes.
Exit 1 reports lint violations.

Build from this folder's Containerfile; Dockerfile is its GitHub-compatible symlink.
Qualification checks clean input and an intentionally undefined Python name.
See [shared qualification and publication instructions](../README.md).
