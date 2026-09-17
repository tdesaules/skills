---
name: helm
description: |-
  Create, template, review, and operate Helm charts (Chart.yaml, values.yaml, values.schema.json, templates/_helpers.tpl, hooks, tests, subcharts, OCI registries) and run the helm CLI (install, upgrade, template, lint, rollback, diff). Use when writing or fixing a Helm chart, a Go template under templates/, a values file, or debugging a helm release or rendering error.
  Examples:
  - user: "create a helm chart for this API" → helm create then trim, flat documented values, namespaced helpers, standard labels, schema, NOTES, test
  - user: "helm upgrade failed, nil pointer evaluating interface" → helm template --debug, locate the unguarded .Values path, fix with with/default/required
  - user: "review this chart" → checklist with file:line evidence: pinned image tag, selectors, RBAC split, dependency ranges, CRDs in crds/
license: GPL-3.0-or-later
compatibility: opencode
metadata:
  audience: developers-devops
  workflow: helm-chart-author-lint-release
---

# Helm

## What I do

- Scaffold and structure charts (`Chart.yaml`, `values.yaml`, `values.schema.json`, `templates/`, `crds/`, `charts/`, `NOTES.txt`, `templates/tests/`)
- Write Go templates that follow the Helm best-practice guide: namespaced `define`s, standard labels, immutable selectors, guarded values, `include | nindent`
- Design values files that are flat, documented, `--set`-friendly, and schema-validated
- Manage dependencies, hooks, CRDs, library charts, and OCI packaging/distribution
- Operate releases with the `helm` CLI (v3 and v4 flag differences), and debug rendering, upgrade, and rollback failures with command output as evidence

## When to use me

Use me when creating or fixing a Helm chart, a template under `templates/`, a values file, `Chart.yaml` dependencies, or when a `helm install|upgrade|template|lint` command fails.
Use ONLY for Helm charts and releases. Not for raw `kubectl` manifests or Kustomize overlays without Helm, not for building the container image the chart deploys (load the `container` skill), not for cluster provisioning.
Ask clarifying questions when the target Helm major version, the Kubernetes version range, or whether the chart is an application, library, or umbrella chart is unclear.

## Architecture facts that drive decisions

- Helm is a client + Go library talking to the Kubernetes API; no in-cluster component. Release state (rendered manifest, values, chart) is stored as a `Secret` of type `helm.sh/release.v1` in the release namespace; each revision is a new Secret (`helm history`).
- Rendering happens client-side: `.Values` (merged: chart `values.yaml` < `-f` files in order < `--set`), `.Release.{Name,Namespace,Service,IsInstall,IsUpgrade,Revision}`, `.Chart.*`, `.Capabilities.{KubeVersion,APIVersions}`, `.Files`, `.Template.{Name,BasePath}`. Sprig functions minus `env`/`expandenv`, plus `include`, `required`, `tpl`, `lookup`, `toYaml`, `fromYaml`.
- Resources from the chart and all subcharts are aggregated, sorted by kind (`kind_sorter.go`: Namespace, NetworkPolicy, ResourceQuota, LimitRange, PodSecurityPolicy, PodDisruptionBudget, ServiceAccount, Secret, SecretList, ConfigMap, StorageClass, PersistentVolume, PersistentVolumeClaim, CustomResourceDefinition, ClusterRole, ..., Service, DaemonSet, Pod, ReplicationController, ReplicaSet, Deployment, HorizontalPodAutoscaler, StatefulSet, Job, CronJob, IngressClass, Ingress, APIService) then by name, and applied in one pass. Anything needing a wait between resources is a hook, not a template.
- `crds/` is applied before rendering, only on install, never templated, never upgraded or deleted (`--skip-crds` to bypass). CRD lifecycle after install is manual or a separate chart.
- Hooks (`helm.sh/hook: pre-install,post-upgrade,...`) run outside the release: not tracked, not deleted on uninstall unless `helm.sh/hook-delete-policy` (`before-hook-creation` default, `hook-succeeded`, `hook-failed`). Jobs/Pods block until completion; ordering by `helm.sh/hook-weight` (string, ascending).
- Upgrade applies a 3-way merge (old manifest, new manifest, live object) in Helm 3; Helm 4 defaults new releases to server-side apply (field ownership; `--server-side` to override) and keeps the previous method on upgrades of existing releases.
- Helm 4 renames `--atomic` → `--rollback-on-failure`, `--force` → `--force-replace`; `helm registry login` takes a domain only; post-renderers are plugins; chart installs by OCI digest (`oci://reg/app@sha256:...`) are supported; `apiVersion: v2` charts are unchanged, `v3` charts are experimental (`HELM_EXPERIMENTAL_CHART_V3=1`). Detect with `helm version --short` before writing commands.

## Workflow

1. **Inspect.** `helm version --short`; find `Chart.yaml`, `values*.yaml`, `templates/`, `Chart.lock`, `charts/`, `crds/`, `.helmignore`, `ci/*-values.yaml`. Read the workload's image, ports, config, and secrets needs. Note the target `kubeVersion` and whether Gateway API, PDB, HPA v2 exist (`kubectl api-versions`).
2. **Classify.** New chart / template change / values design / dependency / release operation / debugging. One at a time.
3. **Scaffold** new charts with `helm create <name>` (canonical `_helpers.tpl`, labels, `serviceAccountName` helper, HPA, Ingress, HTTPRoute, NOTES, test), then delete what the app does not need rather than writing helpers from memory.
4. **Design values**, then **templates**, then **metadata** (rules below).
5. **Validate** with commands, never by reading alone:
   - `helm lint --strict <chart>` (and `-f ci/<case>-values.yaml` per documented scenario)
   - `helm template rel <chart> --debug -f values.yaml | tee rendered.yaml` (render offline); `helm template --kube-version 1.29 --api-versions gateway.networking.k8s.io/v1` to exercise `.Capabilities`
   - `helm install rel <chart> --dry-run=server --namespace ns` when a cluster is reachable (validates against the API; CRDs from `crds/` cannot be dry-run)
   - Schema: `helm lint` and `helm template` enforce `values.schema.json`; test a bad value to confirm it fails
   - Optional: `kubeconform -strict -summary rendered.yaml`, `helm unittest <chart>`, `ct lint --charts <chart>`, `helm-docs`
6. **Report** each finding as `file:line` → rule → consequence → fix. For release operations, paste `helm status`/`helm history` output.

## Chart structure and metadata

```
<chart>/
  Chart.yaml            # apiVersion v2, name, version (SemVer 2), appVersion (quoted), type, kubeVersion, dependencies
  Chart.lock            # generated by helm dependency update; commit it
  values.yaml           # defaults, every key documented
  values.schema.json    # JSON Schema (draft-07) for .Values
  .helmignore           # .git, ci/, *.md except README, tests
  README.md             # what, prerequisites, values table
  crds/                 # plain YAML CRDs, not templated
  charts/               # dependency archives or unpacked subcharts
  templates/
    _helpers.tpl        # all {{ define "<chart>.xxx" }} blocks
    NOTES.txt           # short post-install text, templated
    deployment.yaml service.yaml serviceaccount.yaml ...   # one kind per file, dashed names
    tests/test-connection.yaml
```

- `name`: DNS-1123 label (lowercase, digits, `-`, ≤63); directory name equals `name`.
- `version`: chart SemVer, bump on every change (patch for template fixes, minor for new values, major for breaking value changes). `appVersion`: quoted string, informational; use as default image tag.
- `type: application` (default) or `library` (no rendered resources, only `define`s; consumed via `dependencies`).
- `kubeVersion: ">=1.27.0-0"` when templates use APIs with a minimum version. Prefer `.Capabilities.APIVersions.Has "autoscaling/v2"` guards over hard-failing.
- `dependencies`: `version: ~1.2.3` (patch range; `~1.2.3-0` to include pre-releases), `repository: https://...` or `oci://...` or `"@alias"`, `condition: <name>.enabled` for optional subcharts, `tags` for grouped features, `alias` for the same chart twice, `import-values` for exported child defaults. Run `helm dependency update` and commit `Chart.lock`; `helm dependency build` in CI.
- Do not set `metadata.namespace` in templates; Helm applies `--namespace`. Exception: cross-namespace resources with a stated reason.

## Values rules

- camelCase keys starting lowercase (`replicaCount`, `serviceAccount.create`); no hyphens, no uppercase initial (reserved for built-ins).
- Flat over nested unless a group is large and one key is mandatory. Maps over lists for anything users override with `--set` (`servers.foo.port` beats `servers[0].port`).
- Quote every string; leave integers and booleans bare; in `env:` values quote numbers (they must be strings). Store large ints as strings and cast with `int` if YAML float coercion bites.
- Document every key with a comment starting with the key name: `# replicaCount is the number of pods when autoscaling is disabled`. Use `# -- description` (helm-docs) if the repo already does.
- `image: {repository, tag: "", pullPolicy: IfNotPresent, digest: ""}`; default the tag to `.Chart.AppVersion`; never `latest`. Offer `global.imageRegistry` and `imagePullSecrets` for umbrella charts.
- Split `serviceAccount: {create, name, annotations, automount}` from `rbac: {create}`; default `rbac.create: true`.
- `resources: {}` by default with commented example, or explicit requests when the chart owns the app; always `podSecurityContext`/`securityContext` keys with hardened commented defaults (`runAsNonRoot`, `readOnlyRootFilesystem`, `allowPrivilegeEscalation: false`, `capabilities.drop: [ALL]`, `seccompProfile.type: RuntimeDefault`).
- Never put secrets in `values.yaml` defaults. Accept `existingSecret` names; generate with `randAlphaNum` only inside a `lookup`-guarded block so upgrades do not rotate them.
- Provide `nameOverride`, `fullnameOverride`, `commonLabels`, `commonAnnotations`, `podAnnotations`, `podLabels`, `nodeSelector`, `tolerations`, `affinity`, `topologySpreadConstraints`, `extraEnv`, `extraVolumes`, `extraVolumeMounts` as passthroughs rendered with `toYaml | nindent`.
- Ship `values.schema.json`: types, `enum` for `service.type`, `required` for mandatory keys, `additionalProperties: false` on well-known objects. Schema applies to the merged `.Values`, subchart schemas too.

## Template rules

- One resource per file, file named `<purpose>-<kind>.yaml` or `<kind>.yaml` in dashed lowercase; helper-only files start with `_` and end `.tpl`.
- Every `define` is namespaced with the chart name: `{{- define "mychart.fullname" -}}`. Use `include`, not `template`, so output can be piped: `{{- include "mychart.labels" . | nindent 4 }}`.
- Standard labels via a helper on every resource: `helm.sh/chart`, `app.kubernetes.io/name`, `app.kubernetes.io/instance`, `app.kubernetes.io/version`, `app.kubernetes.io/managed-by`; optional `component`, `part-of`. Selectors (`spec.selector.matchLabels`, Service `selector`) use only `app.kubernetes.io/name` + `app.kubernetes.io/instance` — selectors are immutable, version labels must not be in them.
- Guard optional values: `{{- with .Values.x }} ... {{- toYaml . | nindent 8 }} {{- end }}`, `{{ default "x" .Values.y }}`, `{{ required "values.z is required" .Values.z }}`. Accessing `.Values.a.b` when `a` is nil panics (`nil pointer evaluating interface {}.b`).
- Whitespace: `{{-` / `-}}` chomping, spaces inside braces (`{{ .foo }}`), two-space indent, minimal blank lines in output. `nindent` after `toYaml`/`include`; `indent` only when already on a new line.
- Quote strings `{{ .Values.name | quote }}`; never quote ports/replicas. Wrap dynamic names with `| trunc 63 | trimSuffix "-"`.
- Roll pods on config change: `checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}` in pod template annotations. Avoid `randAlphaNum` in annotations unless a restart every upgrade is intended.
- Conditional resources wrap the whole file: `{{- if .Values.ingress.enabled -}} ... {{- end }}`. Use `.Capabilities.APIVersions.Has` for API fallbacks; `.Capabilities.KubeVersion.GitVersion` for `semverCompare`.
- `tpl` to render user-supplied template strings (`{{ tpl .Values.extraConfig . }}`) and `.Files.Get`/`.Files.Glob` + `tpl` for config files under the chart (not `templates/`). Binary: `.Files.Get | b64enc`.
- Comments: `{{- /* */ -}}` for template docs (never rendered, safe around `required`); `#` YAML comments only when they should appear in `--debug` output. Never `#`-comment out a line containing `{{ required ... }}`.
- Hooks: Job with `helm.sh/hook`, `helm.sh/hook-weight: "0"` explicit, `helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded`, `backoffLimit`, `ttlSecondsAfterFinished`, and the chart labels. Use `pre-upgrade,pre-install` for migrations; keep the migration image pinned to the same tag as the app.
- Tests: `templates/tests/*.yaml` Pods with `helm.sh/hook: test`, `restartPolicy: Never`, hitting the Service by name; run with `helm test rel`.
- `helm.sh/resource-policy: keep` on PVCs or Secrets that must survive uninstall; document that they become orphaned.
- Library charts: `type: library`, only `_*.tpl`, consumers `include "lib.util" (list . "mychart.override")` and merge with `mergeOverwrite`.
- Subchart values are namespaced (`subchart.key`), `global.*` flows down only. Use `import-values` rather than duplicating defaults.

## Release operations

```bash
helm dependency update ./chart && helm lint --strict ./chart
helm template rel ./chart -f values-prod.yaml > /tmp/rendered.yaml
helm upgrade --install rel ./chart -n app --create-namespace -f values-prod.yaml \
  --wait --timeout 5m --rollback-on-failure        # Helm 3: --atomic
helm history rel -n app; helm get values rel -n app; helm get manifest rel -n app
helm rollback rel <revision> -n app --wait
helm uninstall rel -n app --keep-history
```

- Use `upgrade --install` for idempotent pipelines; `--wait` waits for Deployments/StatefulSets/Jobs readiness (Helm 4 uses kstatus for richer status); `--timeout` bounds it; `--rollback-on-failure` reverts automatically.
- `--reuse-values` merges the last release's values (not the chart's new defaults) and silently keeps removed keys; prefer `--reset-values` + explicit `-f`/`--set`, or `--reset-then-reuse-values`.
- `--set` for scalars only; `--set-string` to force strings; `--set-file` for file contents; `--set-json` for structured. Lists via `{a,b}` or `key[0]=`.
- Diff before applying: `helm diff upgrade rel ./chart -f values-prod.yaml` (plugin) or `helm template ... | kubectl diff -f -`.
- Stuck `pending-upgrade`/`pending-install`: `helm history`; rollback to last `deployed` revision or delete the release Secret only as last resort.
- Packaging: `SOURCE_DATE_EPOCH=$(git log -1 --pretty=%ct) helm package ./chart --version X --app-version Y` (reproducible), `helm push chart-X.tgz oci://registry.example.com/charts`, `helm registry login registry.example.com` (domain only in v4), install by digest `oci://...@sha256:...`. `helm show values|chart|crds oci://...` to inspect. Classic repos: `helm repo index`, `helm repo add|update`, `helm search repo -l`.
- Signing: `helm package --sign --key ... --keyring ...` + `helm verify`, or `cosign sign` the OCI artifact.

## Review checklist

Each finding needs `file:line`, the violated rule, the consequence, and the fix.

- [ ] `Chart.yaml`: `apiVersion: v2`, DNS-1123 name equals directory, SemVer `version`, quoted `appVersion`, `type`, `kubeVersion` when APIs need it, dependency ranges `~x.y.z` with `condition`, `Chart.lock` committed
- [ ] Image reference: `repository:tag|@digest`, tag defaults to `.Chart.AppVersion`, no `latest`, `pullPolicy` from values, `imagePullSecrets` passthrough
- [ ] Labels via namespaced helper on every resource; selectors limited to name + instance and unchanged across versions
- [ ] No `metadata.namespace`; names truncated to 63; all `define`s namespaced
- [ ] Every `.Values.a.b` access guarded (`with`/`default`/`required`); `required` messages name the key
- [ ] `values.yaml`: camelCase, documented per key, quoted strings, maps not lists for overridables, no secrets, hardened security context defaults, `resources` documented
- [ ] `values.schema.json` present and rejects a wrong type/enum (tested)
- [ ] `serviceAccount` and `rbac` keys split; `serviceAccountName` helper; least-privilege Role/ClusterRole
- [ ] Probes (`readiness`, `liveness`, optional `startup`) exposed via values; PDB and HPA optional with `enabled`; HPA disables `replicas`
- [ ] Config changes roll pods (`checksum/*` annotation); no unintended `randAlphaNum` churn
- [ ] Hooks have weight and delete policy; migrations idempotent; CRDs in `crds/`, not templated
- [ ] `NOTES.txt` short and correct for each `service.type`/ingress mode; `templates/tests/` present
- [ ] `helm lint --strict` and `helm template --debug` pass for default and `ci/*-values.yaml`

## Anti-patterns

- `image: nginx:latest`, or a tag hardcoded in a template instead of values/`appVersion`.
- `{{ define "fullname" }}` without chart prefix; `template` instead of `include`; `{{.Values.x}}` without spaces/guards.
- Version labels inside `selector.matchLabels` (upgrade fails: field is immutable).
- `namespace: {{ .Release.Namespace }}` in every resource (breaks `helm template | kubectl apply -n`).
- Secrets with plain defaults in `values.yaml`; passwords in `--set` committed to CI logs.
- CRDs in `templates/` (races with CRs; deleted on uninstall) or templated CRDs in `crds/` (not rendered).
- `helm upgrade --reuse-values` in pipelines; `--force` on StatefulSets; `--recreate-pods`.
- Giant nested values requiring `if .Values.a` at every level; lists where users need `--set`.
- `#` YAML comment over a `required` line; `randAlphaNum` in a pod annotation.
- `helm template` output committed as manifests while still calling it a chart.
- Writing Docker/Containerfile advice here instead of loading the `container` skill.

## References

Read on demand:

- `references/chart-templates.md` — canonical `_helpers.tpl`, Deployment/Service/ServiceAccount/Ingress/HTTPRoute from `helm create` (Helm 4), hook Job, test Pod, `values.schema.json`, hardened `values.yaml` blocks, library chart pattern. Read when writing or reviewing templates.
- `references/helm-cli-cheatsheet.md` — v3/v4 command matrix, debugging recipes (rendering errors, stuck releases, schema failures), OCI registry and repo workflows, plugins. Read when the user asks for commands or an operation fails.

Docs and source:

- Charts: https://helm.sh/docs/topics/charts/
- Best practices: https://helm.sh/docs/chart_best_practices/
- Chart template guide: https://helm.sh/docs/chart_template_guide/
- Tips and tricks: https://helm.sh/docs/howto/charts_tips_and_tricks/
- Hooks: https://helm.sh/docs/topics/charts_hooks/ — Tests: https://helm.sh/docs/topics/chart_tests/
- Helm 4 overview and changelog: https://helm.sh/docs/overview/
- CLI reference: https://helm.sh/docs/helm/
- `helm create` scaffold source: https://github.com/helm/helm/blob/main/pkg/chart/v2/util/create.go
- Install order: https://github.com/helm/helm/blob/main/pkg/release/v1/util/kind_sorter.go
- Kubernetes recommended labels: https://kubernetes.io/docs/concepts/overview/working-with-objects/common-labels/
- Sprig functions: https://masterminds.github.io/sprig/
