# Native Docker actions and their OCI images

## One operation, one action, one image

Keep the interface, executable, image recipe and tests together:

```text
lint/hadolint/
  action.yml
  Containerfile
  main.go
  README.md
  main_test.go
```

Implement a fixed operation in each Go entrypoint. Do not multiplex tools through
an `operation` or arbitrary `command` input. Shared implementation packages are
allowed; each public action still owns its entrypoint, Containerfile and image.

Build with multiple stages and finish with `FROM scratch`. Copy only the required
runtime closure; an interpreter or compiler may be the actual tool of a test
action, but unrelated build tooling must not leak into its runtime. Pin external
bases and select a qualified USER/output-ownership contract. Use the `container`
skill for the full build-file procedure instead of duplicating it here.

Store sources in `https://github.com/tdesaules/github-actions`. Publish each image
to `ghcr.io/tdesaules/github-actions/<image>`, with native AMD64/ARM64 variants and
an immutable index digest. `/actions` is the repository's execution UI, not the
source location or image registry.

## Native invocation contract

Illustrative metadata; resolve the image name and real digest before use:

```yaml
name: Test Containerfile
description: Lint explicit Containerfile paths
inputs:
  files:
    description: Nonempty JSON array of literal file paths
    required: true
runs:
  using: docker
  image: docker://ghcr.io/tdesaules/github-actions/<image>@sha256:<verified-digest>
  args:
    - --files=${{ inputs.files }}
```

The workflow calls the action directly:

```yaml
- name: Hadolint
  if: needs.check.outputs.hadolint-changed == 'true'
  uses: ./lint/hadolint
  with:
    files: ${{ needs.check.outputs.hadolint-files }}
```

GitHub starts the container on the Linux/Docker runner and mounts the workspace.
Use an explicit workspace/path contract and return outputs through `GITHUB_OUTPUT`.
Forward inputs through literal arguments or environment variables; CLI flags take
precedence over `INPUT_*` values, then defaults. Keep credentials environment-only
and ephemeral. Preserve spaces, reject malformed inputs and propagate failures.

The GitHub tutorial's `image: Dockerfile` is also a valid native Docker action,
but it builds on invocation. This catalog's released actions instead use
prebuilt, qualified `docker://...@sha256:...` references. Keep `Containerfile` as
the source recipe; never invent a digest to bypass prerequisite publication.

## Git references are not image versions

A consumer can call `tdesaules/github-actions/lint/hadolint@1.2.0`. That selects
the repository's Git tag and its `action.yml`; the metadata then selects the OCI
image by digest. A full commit SHA provides stronger consumer pinning, with the
human-readable version recorded alongside it.

Local `uses: ./lint/hadolint` uses the checked-out files and has no `@REF` suffix.
The Git tag versions the whole catalog, not an individual subdirectory. Keep
upstream tool versions distinct from catalog versions. Retain unchanged image
digests across catalog releases; do not publish SemVer or `latest` image aliases.

## Explicit exceptions and adjacent abstractions

- Keep official checkout, artifact transfer and App-token actions as pinned Node
  actions. Report them as infrastructure exceptions rather than claiming every
  `uses:` is Docker-based.
- Keep the qualified Buildah composite launcher as the narrow container-runtime
  exception. Preserve its storage/isolation/network/security profile; do not add
  privileged mode, extra capabilities, generalized socket mounts or daemon changes.
- A composite may assemble `uses:` calls when needed, but must not hide individual
  linters behind a dispatcher or wrap Python/engine commands to simulate the target.
- Outside this catalog contract, an explicitly requested Podman composite is valid
  GitHub syntax. Document its Linux/Bash/Podman and filesystem requirements rather
  than claiming it is a native Docker action or the default for this catalog.
- Use reusable workflows only for whole-job delegation. Call them with
  `jobs.<id>.uses`, not within steps; a calling job cannot also define steps.
- A job container provides a whole-job environment, not a dedicated action per
  operation. Check Node/libc/shell compatibility for official actions and remove
  migration-only environments when their purpose ends.

Nested local `uses: ./...` paths resolve from the caller checkout. They do not
automatically follow the remote action's repository or inherit its release ref.
Use explicit remote references or deliberately check out the catalog when needed.

## Qualification and activation

Test the exact candidate archive on its native architecture, then execute its
generated native action metadata on GitHub. Use an isolated candidate registry
without a host engine-store assumption. Keep each tool invocation visible in the
workflow and preserve the checksum/receipt boundary between `build` and `test`.

Cover clean/invalid/missing/duplicate inputs, paths with spaces, permission errors,
source immutability, exit codes and writable outputs. State whether read-only
behavior was established by a filesystem mount or by unprivileged permissions;
do not present one as evidence of the other. Keep public reports uploader-readable
while keeping keys and internal signing configuration out of report artifacts.

After qualification, publish and verify the images, update real digest references,
activate the direct workflow calls, remove temporary host bridges and exercise
the affected hosted jobs. Passing image tests or publishing an image alone does
not demonstrate that the workflow actually uses it.

Official references:
- https://docs.github.com/en/actions/tutorials/use-containerized-services/create-a-docker-container-action
- https://docs.github.com/en/actions/sharing-automations/creating-actions/creating-a-composite-action
- https://docs.github.com/en/actions/sharing-automations/reusing-workflows
