# helm CLI cheatsheet (v3 / v4)

Check first: `helm version --short` (`v3.x` or `v4.x`). Without a local binary: `podman run --rm -v "$PWD":/apps:Z -v ~/.kube:/root/.kube:Z docker.io/alpine/helm:4.3.0 <args>` (pin the tag).

## Flag differences v3 → v4

| v3                                   | v4                                                   |
| ------------------------------------ | ---------------------------------------------------- |
| `--atomic`                           | `--rollback-on-failure` (old flag warns)             |
| `--force`                            | `--force-replace`                                    |
| `helm registry login https://reg`    | `helm registry login reg` (domain only)              |
| `--post-renderer ./bin`              | `--post-renderer <plugin-name>` (plugins only)       |
| client-side apply                    | server-side apply default for new installs; `--server-side=false` to opt out; existing releases keep their method |
| `--wait` (readiness heuristics)      | `--wait` uses kstatus (richer readiness)             |
| `helm template --hide-notes`         | deprecated no-op                                     |
| `helm install oci://reg/chart --version 1.2.3` | plus `oci://reg/chart@sha256:...` by digest |
| single `-f` values docs              | multi-document values files supported                |

## Chart development

```bash
helm create app                                  # scaffold with canonical helpers
helm lint --strict ./app                         # add -f ci/<case>-values.yaml per scenario
helm template rel ./app --debug                  # render offline; --debug keeps output on error
helm template rel ./app -f values-prod.yaml --kube-version 1.30 \
  --api-versions gateway.networking.k8s.io/v1 > /tmp/rendered.yaml
helm template rel ./app --show-only templates/deployment.yaml
helm template rel ./app --set image.tag=1.2.3 --set-string podAnnotations.rev=1234
helm install rel ./app --dry-run=server -n app   # API validation; --dry-run=client skips lookup/validation
helm show values ./app; helm show chart ./app; helm show crds ./app
helm dependency update ./app                     # writes Chart.lock and charts/*.tgz
helm dependency build ./app                      # from Chart.lock (CI)
helm dependency list ./app
helm package ./app --version 1.4.0 --app-version 2.3.1 -d dist/
SOURCE_DATE_EPOCH=$(git log -1 --pretty=%ct) helm package ./app     # reproducible archive
helm package --sign --key 'Team' --keyring ~/.gnupg/pubring.gpg ./app && helm verify dist/app-1.4.0.tgz
```

Useful plugins: `helm plugin install https://github.com/databus23/helm-diff`, `helm-unittest/helm-unittest`, `norwoodj/helm-docs` (values table from comments), `chart-testing` (`ct lint`, `ct install`), `kubeconform` for schema validation of rendered output.

## Release lifecycle

```bash
helm upgrade --install rel ./app -n app --create-namespace -f values-prod.yaml \
  --wait --wait-for-jobs --timeout 5m --rollback-on-failure      # v3: --atomic
helm status rel -n app --show-resources
helm history rel -n app --max 20
helm get values rel -n app [--all] [--revision N]
helm get manifest rel -n app | kubectl diff -f -                  # what would change if re-applied
helm diff upgrade rel ./app -f values-prod.yaml -n app            # plugin; --three-way-merge
helm rollback rel 7 -n app --wait
helm test rel -n app --logs
helm uninstall rel -n app --keep-history                          # keeps release Secrets for audit
helm list -A --all --date --reverse
```

Values precedence (last wins): chart `values.yaml` → `-f a.yaml` → `-f b.yaml` → `--set` / `--set-string` / `--set-file` / `--set-json`. `--reuse-values` merges previous release values and ignores new chart defaults; `--reset-values` (default) uses chart defaults; `--reset-then-reuse-values` (v3.14+) reads new defaults then previous overrides.

`--set` syntax: `a.b=1`, `list={x,y}`, `list[0].name=x`, escape dots `key\.with\.dots=v`, null `key=null` to delete a default, `--set-string tag=1.10` to avoid float coercion, `--set-file cert=./tls.crt`, `--set-json 'env=[{"name":"A","value":"1"}]'`.

## OCI registries and repos

```bash
helm registry login registry.example.com          # v4: domain only; uses ~/.config/helm/registry/config.json
helm push dist/app-1.4.0.tgz oci://registry.example.com/charts
helm pull oci://registry.example.com/charts/app --version 1.4.0 [--untar]
helm show chart oci://registry.example.com/charts/app --version 1.4.0
helm install rel oci://registry.example.com/charts/app --version 1.4.0
helm install rel oci://registry.example.com/charts/app@sha256:<digest>      # v4 digest pin
skopeo inspect docker://registry.example.com/charts/app:1.4.0                # chart manifest (media type application/vnd.cncf.helm.config.v1+json)
cosign sign registry.example.com/charts/app@sha256:<digest>

helm repo add org https://charts.example.com && helm repo update
helm search repo org/ -l --devel
helm repo index dist/ --url https://charts.example.com [--merge index.yaml]
```

Chart versions in OCI tags: `+` (build metadata) becomes `_` in the tag.

## Debugging recipes

Rendering error `nil pointer evaluating interface {}.foo`:

```bash
helm template rel ./app --debug 2>&1 | grep -n 'error\|line'
grep -rn '\.Values\.<parent>\.' templates/           # every access needs with/default/if on the parent
```

Fix: `{{- with .Values.parent }}{{ .foo }}{{- end }}` or `{{ (.Values.parent | default dict).foo }}` or define the default in `values.yaml`.

`error converting YAML to JSON: yaml: line N: did not find expected key`: indentation from `toYaml` without `nindent`, or `indent` used mid-line. Render with `--debug` and inspect line N of the *rendered* output; `--show-only` narrows the file.

`Error: execution error at (...): <required message>`: the `required` value is unset; pass it or fix defaults. Check that no `#` comment precedes the line.

Schema failure `values don't meet the specifications of the schema(s)`: read the JSON pointer in the message; run `helm template --set <key>=<good>` to confirm; check subchart schemas too (they apply to merged values).

`Error: INSTALLATION FAILED: cannot re-use a name that is still in use`: `helm list -A --all` (release may be in another namespace or `failed`); `helm uninstall` or `upgrade --install`.

`Error: UPGRADE FAILED: another operation (install/upgrade/rollback) is in progress`: `helm history rel`; `helm rollback rel <last deployed>`; as a last resort delete the `pending-*` release Secret `sh.helm.release.v1.rel.vN`.

Field is immutable (`spec.selector`, StatefulSet `volumeClaimTemplates`, Job spec): selector labels changed between versions. Revert the selector helper; for a real change, deploy under a new release name or recreate the workload (`kubectl delete deploy --cascade=orphan` then upgrade).

`--wait` timed out: `kubectl -n app get pods -l app.kubernetes.io/instance=rel`, `kubectl describe pod`, image pull or probe failures; `helm status --show-resources`.

Resources exist but were not created by this release (`invalid ownership metadata`): adopt with annotations `meta.helm.sh/release-name`, `meta.helm.sh/release-namespace` and label `app.kubernetes.io/managed-by: Helm`, then upgrade.

CRD not found during install of a chart whose `templates/` create CRs: move CRDs to `crds/`, or install the CRD chart first; `--dry-run` cannot validate CRs of CRDs in `crds/`.

Wrong API version for the cluster: `helm template --kube-version` / `--api-versions` to reproduce; guard with `{{- if .Capabilities.APIVersions.Has "policy/v1/PodDisruptionBudget" }}`.

Subchart value not applied: values must be under the subchart key (or `alias`); `global.*` flows down only; verify with `helm template --debug` (prints computed values) or `helm get values --all`.

## Inspecting a running release

```bash
kubectl -n app get secret -l owner=helm,name=rel --sort-by=.metadata.creationTimestamp
kubectl -n app get secret sh.helm.release.v1.rel.v3 -o jsonpath='{.data.release}' | base64 -d | base64 -d | gunzip | jq '.chart.metadata, .config'
```

## Environment

`HELM_NAMESPACE`, `HELM_KUBECONTEXT`, `KUBECONFIG`, `HELM_CACHE_HOME`, `HELM_CONFIG_HOME`, `HELM_DATA_HOME` (plugins in `$HELM_DATA_HOME/plugins`), `HELM_DEBUG=1`, `HELM_EXPERIMENTAL_CHART_V3=1` (v4 experimental charts). `helm env` prints them.
