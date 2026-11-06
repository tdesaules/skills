# Workflow lint action

Native Docker action with no inputs. The fixed Go entrypoint runs bundled
actionlint on .github/workflows/main.yml. ShellCheck/Pyflakes integrations are
disabled because this workflow has no run steps. Only the constant-false condition
warning is ignored for reserved jobs. Other errors propagate as exit 1.

Build from this folder's Containerfile; Dockerfile is its GitHub-compatible symlink.
Qualification checks the actual workflow and rejects an empty jobs mapping.
See [shared qualification and publication instructions](../README.md).
