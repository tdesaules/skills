# Portability and skill review

## Subsequent runtime-base policy change

At the user's request, scratch is now preferred when suitable, not mandatory for
every catalog action. Actions needing interpreters, libraries, build tools or a
complete environment may use another compatible base from the container allowlist.
This is a general rule, not a KAS-specific exception. Multistage dedicated images
and all-stage/donor allowlisting remain required. Historical references below to
mandatory scratch runtimes are superseded by this change.

## Subsequent security policy change

At the user's request, GitHub Actions security reporting is now non-blocking:
Syft/Grype, advisory reviews, Cosign signing/verification and security-report upload
findings or errors do not gate CI/release. The previous high/fail-closed gate in
the historical review below is superseded. Functional tests, exact-artifact checks
and publication operations remain blocking; base-image selection rules remain.
See the policy linked from github-actions/SKILL.md for status/reporting semantics.

## Correction after user review

The initial migration generalized personal policies too broadly. At the user's
request, github-actions now restores the main.yml/six-job contract, event policy,
dedicated Go/Docker actions with scratch runtimes, Grype/high gate, tag conventions,
personal GHCR registry, and agreed launcher/infrastructure exceptions. Commit again
defaults to proactive implementation commits, requires conventionalcommits, and
always writes a why-body. Agent Skills portability does not require removing these
conventions. Container and Helm's contextual guidance was explicitly accepted;
the subsequently requested seven-base allowlist remains in force. The skill-authoring
guide now explicitly preserves scoped user policies and documented dependencies.

The findings below describe the initial review; claims about making these policies
generic or companions optional are historical and superseded by this correction.

## Scope

Reviewed all seven original SKILL.md files, their nine supporting reference files,
README, and AGENTS.md against the Agent Skills specification and its quickstart,
best-practices, description, evaluation, and script guides. Original paths below
refer to the pre-migration tree; all skills now reside at repository root.

## Findings and corrections

| Original location | Finding / impact | Correction |
| --- | --- | --- |
| All frontmatters; README; AGENTS.md | `compatibility: opencode` and client-specific layout/instructions obscure portability | Root-level skill folders, actual tool prerequisites, client-neutral installation |
| All descriptions | Long mandatory Examples blocks spend startup context; adjacent skills overlap | Short intent-based activation descriptions, near-miss boundaries, examples/evals outside metadata |
| `opencode/skill/SKILL.md:45–90` | Words confused with tokens; third-person/Examples/heading rules presented as format rules; client discovery assumptions | Specification-aligned authoring workflow; optional fields including allowed-tools; separate format, discovery, activation, quality |
| `opencode/commit/SKILL.md:29–55`; `opencode/conventionalcommits/SKILL.md:116–123` | Proactive vs explicit-only policies conflict; mandatory companion; weak publication check; unrelated index risk | Scope-based authorization, independent installation, cached-diff inspection, publication uncertainty handling |
| `opencode/commit/SKILL.md:38`; `opencode/conventionalcommits/SKILL.md:51` | Splitting docs/tests solely by file category breaks cohesive commits | Group independently revertible intent, keeping necessary tests/docs with implementation |
| `opencode/github-actions/SKILL.md:35–110` and its references | Personal registry, fixed six jobs, no PR trigger, Docker-only operations, scanner/vendor rules imposed on other repos | General reuse/event/runner decisions; retain dependency, artifact, retry, signing and race expertise |
| `opencode/container/SKILL.md:79–115` | Unsupported mount/frontend assumptions and universal ignore-file choices | Builder detection, portable lockfile COPY, explicit platform handling, shared dockerignore baseline |
| `opencode/container/references/containerfile-templates.md:51–130` | Unsupported verification claim; misplaced Rust RUN mount; incompatible Python venv assumption | Illustrative status, valid cached RUN build without dummy source, matching Python runtime and ABI/path guidance |
| `opencode/container/references/compose-templates.md:64,77,184,260,276` | Duplicate executable argument; fresh-volume UID risk; Docker/Podman option confusion; wrong memory key/Quadlet enable guidance | CMD-only migration args, initialization ownership guidance, provider distinctions, systemd MemoryMax and generated-unit startup |
| `opencode/helm/SKILL.md:112–129` | Guards can still dereference missing parents; hook examples depend on resources not yet created | Parent guarding, zero/false preservation, lifecycle-aware hook dependencies |
| `opencode/helm/references/chart-templates.md:535–540,692–705,793–795` | PDB zero omitted, pre-install ServiceAccount dependency, unsupported helmignore negation | hasKey checks with mutual-exclusion guidance, existing hook account contract, explicit ignore patterns |
| `opencode/helm/references/helm-cli-cheatsheet.md:35,57,111` | Reproducibility/default-value/debug-output claims too broad | Remove unsupported guarantee, explicit value-reuse choice, inspect actual rendered/release data |
| `opencode/chezmoi/SKILL.md:47–60,133,146` | Interactive editor assumptions, include/render confusion, unsupported blanket redaction advice | Direct source edits plus rendering, template helper distinction, explicit output handling and task scope |
| Collection | No reusable format validator or per-skill evaluation corpus | Read-only Python validator with pinned dependencies and failure tests; 28 task cases and 42 activation queries |

## Design choices

- Kept the seven existing names to avoid unnecessary migration breakage.
- Retained useful domain references but removed stale personal-contract fixtures;
  GitHub Actions now has portable cases in `evals/evals.json`.
- Reduced the Container and Helm main files to decision procedures; detailed
  snippets stay on demand. No universal requirement for particular body headings.
- Scripts use Python; guidance supports pinned `go run` tools when appropriate.
  No runtime wrapper is added where an existing CLI already provides the operation.
- Repository/license wording now agrees with the skills' GPL-3.0-or-later declarations.

## Verification boundary

Observed during this review:

- Local format/link validator: 7 skills valid, no warnings.
- Official skills-ref at upstream revision `83021e2be457a9b6679148719c1f6074f0ad975e`: all 7 skills valid.
- Validator unit tests: valid metadata, malformed/duplicate YAML, invalid types and
  lengths, missing/escaping links, code examples, and missing/invalid UTF-8 files pass.
- Evaluation JSON: all 7 documents parse, skill names and case IDs match; 28
  behavioral cases and 42 labeled activation queries.
- Git whitespace check passes.

Reproduction commands are documented in README. The PyPI `skills-ref==0.1.0`
package exposed a different executable in this environment; the official check
therefore used the pinned upstream source rather than assuming package-name identity.

Per-skill JSON cases are evaluation inputs, not observed results. No isolated
old/new model benchmark, automatic-discovery test, live deployment, full image
build matrix, or registry publication is implied by this review. Domain snippets
must be adapted and exercised in their target environment before use.

## Reference basis

- https://agentskills.io/specification
- https://agentskills.io/skill-creation/quickstart
- https://agentskills.io/skill-creation/best-practices
- https://agentskills.io/skill-creation/optimizing-descriptions
- https://agentskills.io/skill-creation/evaluating-skills
- https://agentskills.io/skill-creation/using-scripts
