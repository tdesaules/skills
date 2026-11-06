---
name: helm
description: >-
  Use when creating or reviewing Helm charts, editing Chart.yaml, chart values or
  Go templates, or diagnosing Helm render, install, upgrade, and rollback failures.
  Covers schema validation, dependencies, hooks, CRDs, and OCI chart distribution.
  Does not apply to unrelated templates, raw Kubernetes manifests, or Kustomize alone.
license: GPL-3.0-or-later
compatibility: Requires Helm; cluster operations additionally require Kubernetes access and the intended context/namespace.
---

# Helm charts and releases

## Scope

Author, render, review, and operate Helm charts. Inspect `helm version --short`
before choosing commands; verify version-sensitive flags with installed help.
Use offline checks for chart edits and the intended cluster/context only for
requested release operations.

For container image selection, construction, or base-image review, consult the
companion `container` skill when available: it owns this collection's base-image
allowlist and build/runtime procedure. Apply it to application, init, hook, and test
images when selecting or rebuilding them. Application image names need not equal
base names; verify their recipe/provenance instead of substituting a bare base.
If the companion is unavailable, preserve existing references and report the policy
check as unresolved; ordinary chart rendering does not depend on installing it.

## Workflow

1. Inspect Chart.yaml, values, schema, templates, Chart.lock, CRDs, CI scenarios,
   and existing release commands. Determine the supported Kubernetes versions,
   chart type, image interface, dependencies, and secrets contract.
2. For new charts, start with `helm create <name>` then remove unused resources.
   Preserve existing values/interfaces during refactors. Keep chart SemVer separate
   from quoted informational appVersion; follow the repository's release policy.
3. Design documented values and schema around actual overrides. Use maps for named
   entries, quote strings, retain boolean/numeric types, and accept existing Secrets.
   Add passthroughs only when useful rather than building an unused universal chart.
4. Write namespaced helpers and consistent labels. Keep selectors stable across
   upgrades, without version labels. Match pod labels to selectors. Use `include`
   with `nindent`, preserve the root context inside `range`, and guard optional parents.
5. Resolve dependencies with `helm dependency update` only when updating constraints;
   use `helm dependency build` to reproduce Chart.lock. Keep plain CRDs in `crds/`
   when using Helm's install-only CRD handling; document their separate lifecycle.
6. Run `helm lint --strict <chart>` and `helm template rel <chart>` for defaults and
   supported values scenarios. Exercise invalid values and optional absent parents.
   Render supported kube/API versions explicitly when capability logic changes.
7. For authorized release work, inspect current status/history/values, preview the
   change, run the version-appropriate command, then verify status and rollout.
   A successful local render is not proof of API validity or release readiness.

## Gotchas

- `default`/`required` do not rescue `.Values.parent.child` if evaluating `parent`
  already failed. Bind `parent | default dict`, use `with`, or schema validation.
- `default` and `with` treat false/zero as empty. Use `hasKey` where explicit false
  or zero is meaningful (for example PDB `minAvailable: 0`).
- A pre-install hook runs before ordinary chart resources: it cannot depend on a
  ServiceAccount, Secret, or database created later in the same install. Use existing
  dependencies, ordered hook resources, or an appropriate post-install design.
- `lookup` cannot preserve an existing Secret in offline rendering. Prefer supplied
  existing Secrets for deterministic GitOps; test server-side behavior separately.
- CRDs in `crds/` are not templated or normally upgraded/deleted by Helm. Dry-run
  does not register new CRDs so dependent custom resources may not validate.
- `.helmignore` is not .gitignore: negation patterns are unsupported. Do not exclude
  all Markdown then try `!README.md`; use explicit exclusions.
- `helm template` success checks rendering, not every Kubernetes schema. Use a
  schema validator with required CRD schemas or a suitable cluster dry-run, and
  document missing schemas. A dry-run is still not a rollout test.
- Changing immutable selectors, deleting release Secrets, adopting resources, or
  replacing StatefulSets has operational consequences. Diagnose the actual error
  before proposing a migration; do not use these as generic repair commands.

## References to load on demand

- [Chart patterns](references/chart-templates.md): helpers, workload templates,
  schema, hooks, and tests. Read relevant headings only; snippets require adaptation.
- [CLI recipes](references/helm-cli-cheatsheet.md): release/debug/registry operations
  and major-version differences. Confirm flags against the installed version.

## Output

For reviews return `file:line → defect → consequence → correction` and distinguish
errors from optional style. For changes report chart files, commands and results,
values/API coverage, and any untested cluster path. Never reproduce secret values
from rendered manifests or release output in the report.

Sources:

- https://helm.sh/docs/chart_best_practices/
- https://helm.sh/docs/chart_template_guide/
- https://helm.sh/docs/topics/charts_hooks/
- https://helm.sh/docs/helm/
