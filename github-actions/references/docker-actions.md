# Docker action contracts

For this user's catalog, use a dedicated native Docker action for each specialized
operation, following the repository contract in SKILL.md. It requires a supported
Linux runner with Docker. A composite launching Podman is a different interface,
allowed only within the stated exception or an explicitly different repository contract.

## Layout and image

Co-locate `action.yml`, `Containerfile`, a fixed-operation Go executable, README,
and tests. Put linters under `lint/<linter>/`. Shared implementation packages are
allowed, but each public action owns its executable/image; do not expose an
arbitrary command or operation selector. CLI flags override explicitly forwarded
INPUT_* values, then documented defaults.

Use the companion container skill's base-image allowlist for all stages and external
image sources; verify the ancestry of prebuilt action images. Build in multiple
stages ending in FROM scratch. Copy the complete required runtime closure: static
binary, or executable plus its interpreter/dynamic libraries and required files.
Do not silently replace the scratch runtime when closure is incomplete. Check the
actual Docker action workspace/UID behavior; do not mechanically copy an application
image's non-root settings without testing writable outputs on the runner.

```yaml
name: Lint files
description: Lint an explicit list of files
inputs:
  files:
    description: JSON array of literal paths
    required: true
runs:
  using: docker
  image: docker://ghcr.io/tdesaules/github-actions/IMAGE@sha256:VERIFIED_DIGEST
  args:
    - --files=${{ inputs.files }}
```

Resolve placeholders before use. `image: Dockerfile` is valid GitHub syntax but
builds on invocation; released catalog actions use prebuilt, qualified digest
references, published before use. Git references such as
`uses: tdesaules/github-actions/lint/hadolint@1.2.0` version the interface; `runs.image`
selects the runtime. A full commit SHA pins the action source more strongly than a tag.

## Interface and qualification

- Forward declared inputs explicitly; do not assume Docker/composite actions
  receive automatic `INPUT_*` mappings. Validate JSON/paths and preserve spaces.
- Write outputs through `GITHUB_OUTPUT`; propagate tool failures. Keep credentials
  out of command-line arguments, logs, artifacts, and image build arguments.
- Test missing/invalid inputs, native architectures, read-only input behavior,
  output ownership, and uploader readability. Container tests are not hosted-action tests.
- For a prebuilt release, test exact candidate archives, push those artifacts,
  resolve registry digests, update metadata, then exercise the published action.
- Publish support for new inputs/outputs before activating dependent callers;
  editing action.yml cannot change the executable behind its pinned digest.

## Other boundaries

Keep the infrastructure Node actions and narrow Buildah launcher exceptions from
SKILL.md. Use composites only for the agreed step composition and reusable workflows
only for requested whole-job delegation. Preserve the Buildah vfs/chroot/network
and scoped security profile; do not broaden privileges to conceal a build failure.
Outside this user's contract, acknowledge explicitly chosen valid abstractions
without presenting them as the catalog default.

Official references:
- https://docs.github.com/en/actions/tutorials/use-containerized-services/create-a-docker-container-action
- https://docs.github.com/en/actions/sharing-automations/creating-actions/creating-a-composite-action
- https://docs.github.com/en/actions/sharing-automations/reusing-workflows
