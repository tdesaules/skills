# Dedicated CI actions

Each child folder owns a fixed-operation Go entrypoint, native Docker action
metadata and a multistage Containerfile ending in scratch. `Dockerfile` is a
symlink to Containerfile for GitHub's source-action loader, not another recipe.
Builders use the allowlisted Alpine repository pinned by digest. Each final image
contains only its executable and package-managed runtime closure, not the compiler.

| Action | Fixed operation | Planned published image |
| --- | --- | --- |
| check | Skill metadata, evaluation JSON, local Markdown paths | ghcr.io/tdesaules/github-actions/skills-check |
| lint-python | Ruff syntax/import/name/whitespace checks | ghcr.io/tdesaules/github-actions/skills-lint-python |
| lint-markdown | Markdown layout checks | ghcr.io/tdesaules/github-actions/skills-lint-markdown |
| lint-workflow | actionlint for main.yml | ghcr.io/tdesaules/github-actions/skills-lint-workflow |
| test-python | Both validator unit suites | ghcr.io/tdesaules/github-actions/skills-test-python |

No action accepts an arbitrary command or operation selector. Each runs from the
checked-out repository and returns the underlying tool's exit code. They require
Linux/Docker on GitHub; rootless Podman is used for local qualification. Sources
can be mounted read-only, runtime networking is unnecessary, and temporary files
use /tmp. Full-worktree checks intentionally avoid a change selector for this small
collection, including new branches, deletions, configuration changes and tags.

## Bootstrap and publication status

Metadata currently uses native `image: Dockerfile` actions. GitHub builds each
tool image at invocation; these are not host/composite script wrappers. This is a
source-bootstrap state, **not the completed prebuilt-image catalog contract**.
The main workflow exercises AMD64 and ARM64 natively after the user pushes it.
Local AMD64 testing alone is not native ARM64 or hosted-action qualification.

Publication needs GHCR write access and native qualification of both variants.
Do not invent a digest or reuse the old catalog's non-allowlisted builder images.
The GitHub credentials available during implementation lack write:packages; no
registry credentials, image publication, or remote workflow execution is implied.

## Qualify exact artifacts

From a clean checkout on each native platform:

```bash
python3 .github/scripts/qualify_ci_actions.py --output /absolute/external/skills-ci
```

This builds each dedicated image, runs the actual checks offline/read-only, checks
that an intentional defect returns failure, and saves the exact images as OCI
archives with checksummed source-bound receipts. It never pushes. Dirty-source
receipts are diagnostic only; rerun from the intended committed revision before
publication. Inspect failure logs: a failing negative test must be caused by the
intentional defect, not a broken runtime. Keep all native reports and archives.

After both platforms pass from matching sources, transfer the archives without
rebuilding, verify their checksums/receipts, publish the native manifests and index
to the planned GHCR names, and obtain actual remote digests. Keep security scans
and signing advisory, as defined by the GitHub Actions skill.

Replace each action's `runs.image` with its verified `docker://...@sha256:...`
index reference, verify access for the repository's runner identity, and exercise
the workflow again. Removing the source-build bootstrap requires **all five**
images to be published and both native hosted variants observed. Keep Containerfiles
as build sources; never treat changing metadata alone as publishing an image.
