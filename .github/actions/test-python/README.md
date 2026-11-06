# Python validator tests action

Native Docker action with no inputs. The fixed Go entrypoint runs
`python3 -B tests/run.py`, discovering the skill validator and repository validator
suites. Python and required dependencies are bundled. Sources remain read-only;
temporary fixtures use the image's writable /tmp. Test failures return exit 1.

Build from this folder's Containerfile; Dockerfile is its GitHub-compatible symlink.
Qualification runs the real suites, then confirms an injected test failure propagates.
See [shared qualification and publication instructions](../README.md).
