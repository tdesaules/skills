# Skill validation cases

## Trigger selectivity

Expected matches:
1. "Create a Docker linter action with its own scratch image on GHCR."
2. "Review why my release job is skipped when lint has no changed files."
3. "Generate a matrix for changed images in my GitHub action catalog."

Expected non-matches:
1. "Reduce the size of this standalone Containerfile." → container skill.
2. "Write a GitLab CI pipeline." → outside this skill's platform scope.
3. "Rename the last Git commit." → commit/conventionalcommits skills.

Ambiguous: "Make this build reusable." Inspect whether the request concerns a
step/action, jobs, or the build tool itself before choosing a GitHub abstraction.

## Behavioral fixtures

Run the same prompts with and without this skill in an environment where skill
loading can be controlled. Compare concrete findings/artifacts, not claims of
success. These are test specifications, not evidence that such runs occurred.

### Positive: wrong abstraction

Fixture:

```yaml
jobs:
  lint:
    uses: example/catalog/.github/workflows/yaml.yml@1.0.0
    steps:
      - run: echo "extra lint"
```

Prompt: "Review this workflow; I need reusable yamllint plus my own steps."
Expected: identify that a reusable-workflow call job cannot define steps, cite the
fixture location, and propose a step-level action or separate jobs. Do not claim
an OCI image requires a reusable workflow.

### Negative: valid native catalog action

Fixture: `lint/hadolint/action.yml` declares `runs.using: docker` with a verified
GHCR digest, a dedicated Go entrypoint and a multistage Containerfile ending in
`scratch`. Its workflow step calls it directly with explicit inputs and an `if`.
Expected: accept the architecture; do not propose a composite engine launcher or
a generic lint dispatcher. Do not manufacture defects merely because the path
is local or the action uses a prebuilt image instead of `image: Dockerfile`.

### Positive: regression to a host wrapper

Fixture: the catalog's lint job invokes `python3 scripts/lint.py`, or delegates
to a composite containing `podman run`, while a dedicated Docker action exists.
Expected: cite the offending step, replace it with the specialized action and
preserve visible file selection. Retain only the stated infrastructure/Buildah
exceptions. Image publication alone must not be reported as workflow activation.

### Boundary: explicitly chosen external composite

Fixture in a different repository with an explicitly chosen Podman contract:
a composite with `runs.using: composite`, a Bash step launching an image
through Podman, quoted environment inputs, and an explicit documented Linux/Podman
runner requirement. Prompt: "Is using an image in this composite valid?"
Expected: identify it as valid GitHub syntax, distinguish it from this catalog's
native Docker target and review its actual contract. Do not silently change the
explicitly requested external architecture or advertise it as the catalog default.

### Positive: misplaced qualification marker

Fixture: `build` writes `tested: true`, `test` rebuilds the image from source, or
release publishes after failed/skipped required tests.
Expected: introduce/restore the six-job build/test boundary, verify untested
receipts before execution and archive integrity after scans, then emit qualification
metadata. Keep exact archives, native AMD64/ARM64, bounded matrices and failure gates.

### Positive: catalog or version confusion

Fixture: a proposed central image manifest/lockfile, a single runtime command
dispatcher, or publishing catalog images under `1.2.3`/`latest` tags.
Expected: discover ownership/dependencies from source and action metadata, keep a
fixed-operation image per action, and distinguish Git `uses: ...@1.2.3` from the
OCI digest in `runs.image`. Verify multistage `scratch` recipes rather than merely
checking that a Containerfile exists.

### Positive: incomplete artifacts or private fixture upload

Fixture: a run has more than 100 artifacts, the downloader retrieves one page,
or a report glob includes root-owned private signing configuration.
Expected: retain fail-closed completeness checks, correct pagination, make public
reports uploader-readable and exclude private files. Never bypass validation or
apply recursive chmod 777. Require observed hosted evidence before declaring CI fixed.

### Ambiguous: signing configuration absent

Prompt: "Make my containerized Cosign action sign release images."
Fixture: no issuer/identity policy, registry permissions or runner config supplied.
Expected: inspect available configuration, identify the consequential missing
inputs, explain required OIDC/registry wiring, and avoid fabricated secrets or
unverified success claims.

### Boundary: publication without authorization

Prompt: "Review only this catalog's release workflow."
Fixture: valid local workflow and OCI manifests available; no request to publish.
Expected: review with file/line evidence; do not push images, tags, commits or
release records merely to demonstrate the workflow.

## Local structural validation

Check folder/name equality, frontmatter YAML, name regex, description length and
Examples block, required scope headings, README entry, and local reference links.
Actionlint can validate the intentionally invalid YAML fixture separately to
confirm the underlying GitHub syntax defect. Such validation does not prove model
behavior, skill auto-discovery, real GitHub execution, or registry publication.
