# Repository check action

Native Docker action with no inputs. The fixed Go entrypoint runs
`python3 -B .github/scripts/check_repository.py .` in the caller checkout.
Python, PyYAML and Markdown parsing dependencies are bundled; no runtime network
or source writes are needed. Exit 1 reports invalid metadata/evaluations/links.

Build from this folder's Containerfile; Dockerfile is its GitHub-compatible symlink.
The qualification script tests clean input and malformed evaluation JSON.
See [shared qualification and publication instructions](../README.md).
