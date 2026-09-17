# Chart templates

Canonical blocks derived from `helm create` (Helm 4.x, `pkg/chart/v2/util/create.go`) plus hardening and hook/test patterns. `<CHARTNAME>` is the chart name; `helm create` substitutes it automatically. Verified with `helm lint --strict` and `helm template` on Helm v4.3.0.

## Chart.yaml

```yaml
apiVersion: v2
name: <CHARTNAME>
description: A Helm chart for <app>
type: application
version: 0.1.0
appVersion: "1.16.0"
kubeVersion: ">=1.27.0-0"
keywords: [api, backend]
home: https://example.com/app
sources:
  - https://git.example.com/org/app
maintainers:
  - name: Team
    email: team@example.com
dependencies:
  - name: postgresql
    version: ~16.2.0
    repository: oci://registry-1.docker.io/bitnamicharts
    condition: postgresql.enabled
annotations:
  artifacthub.io/license: Apache-2.0
```

## _helpers.tpl

```gotemplate
{{/*
Expand the name of the chart.
*/}}
{{- define "<CHARTNAME>.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name (63 chars max, DNS spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "<CHARTNAME>.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Chart name and version as used by the chart label.
*/}}
{{- define "<CHARTNAME>.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "<CHARTNAME>.labels" -}}
helm.sh/chart: {{ include "<CHARTNAME>.chart" . }}
{{ include "<CHARTNAME>.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- with .Values.commonLabels }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{/*
Selector labels (immutable: never add version or release-specific labels here)
*/}}
{{- define "<CHARTNAME>.selectorLabels" -}}
app.kubernetes.io/name: {{ include "<CHARTNAME>.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Service account name
*/}}
{{- define "<CHARTNAME>.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "<CHARTNAME>.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Image reference: repository[:tag|@digest]; tag defaults to appVersion.
*/}}
{{- define "<CHARTNAME>.image" -}}
{{- $registry := default .Values.image.registry (.Values.global | default dict).imageRegistry -}}
{{- $repo := .Values.image.repository -}}
{{- if $registry }}{{ $repo = printf "%s/%s" $registry $repo }}{{ end -}}
{{- if .Values.image.digest -}}
{{ printf "%s@%s" $repo .Values.image.digest }}
{{- else -}}
{{ printf "%s:%s" $repo (default .Chart.AppVersion .Values.image.tag) }}
{{- end -}}
{{- end }}
```

## values.yaml (hardened defaults)

```yaml
# replicaCount is the number of pods when autoscaling.enabled is false.
replicaCount: 1

# image defines the container image. tag defaults to .Chart.AppVersion; digest wins over tag when set.
image:
  registry: ""
  repository: registry.example.com/org/app
  tag: ""
  digest: ""
  pullPolicy: IfNotPresent

# imagePullSecrets lists Secret names for private registries.
imagePullSecrets: []
# nameOverride replaces the chart name in resource names.
nameOverride: ""
# fullnameOverride replaces the full resource name.
fullnameOverride: ""
# commonLabels are added to every resource.
commonLabels: {}
# commonAnnotations are added to every resource.
commonAnnotations: {}

# serviceAccount controls the ServiceAccount used by the pods.
serviceAccount:
  create: true
  automount: false
  annotations: {}
  name: ""

# rbac controls whether Role/RoleBinding are created.
rbac:
  create: true

# podAnnotations are added to the pod template.
podAnnotations: {}
# podLabels are added to the pod template (not to selectors).
podLabels: {}

# podSecurityContext is the pod-level security context.
podSecurityContext:
  runAsNonRoot: true
  runAsUser: 65532
  runAsGroup: 65532
  fsGroup: 65532
  seccompProfile:
    type: RuntimeDefault

# securityContext is the container-level security context.
securityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop: ["ALL"]

# containerPort is the port the application listens on inside the container.
containerPort: 8080

# service exposes the pods inside the cluster; targetPort refers to the named container port.
service:
  type: ClusterIP
  port: 80
  annotations: {}

# ingress exposes the service through an Ingress controller.
ingress:
  enabled: false
  className: ""
  annotations: {}
  hosts:
    - host: chart-example.local
      paths:
        - path: /
          pathType: Prefix
  tls: []

# httpRoute exposes the service through Gateway API.
httpRoute:
  enabled: false
  annotations: {}
  parentRefs:
    - name: gateway
      sectionName: http
  hostnames: [chart-example.local]
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /

# resources are the container requests and limits.
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    memory: 256Mi

# livenessProbe / readinessProbe / startupProbe are passed through to the container.
livenessProbe:
  httpGet:
    path: /healthz
    port: http
readinessProbe:
  httpGet:
    path: /readyz
    port: http
startupProbe: {}

# autoscaling configures a HorizontalPodAutoscaler; replicaCount is ignored when enabled.
autoscaling:
  enabled: false
  minReplicas: 1
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80
  targetMemoryUtilizationPercentage: ""

# podDisruptionBudget limits voluntary disruptions.
podDisruptionBudget:
  enabled: false
  minAvailable: 1

# env is a list of extra environment variables (name/value or valueFrom).
env: []
# envFrom is a list of ConfigMap/Secret refs.
envFrom: []
# existingSecret is the name of a pre-created Secret with app credentials; leave empty to disable.
existingSecret: ""

# volumes and volumeMounts are passed through to the pod/container.
volumes:
  - name: tmp
    emptyDir: {}
volumeMounts:
  - name: tmp
    mountPath: /tmp

nodeSelector: {}
tolerations: []
affinity: {}
topologySpreadConstraints: []
```

## values.schema.json (excerpt)

```json
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "replicaCount": { "type": "integer", "minimum": 0 },
    "containerPort": { "type": "integer", "minimum": 1, "maximum": 65535 },
    "image": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "registry": { "type": "string" },
        "repository": { "type": "string", "minLength": 1 },
        "tag": { "type": "string" },
        "digest": { "type": "string", "pattern": "^$|^sha256:[a-f0-9]{64}$" },
        "pullPolicy": { "type": "string", "enum": ["Always", "IfNotPresent", "Never"] }
      },
      "required": ["repository"]
    },
    "service": {
      "type": "object",
      "properties": {
        "type": { "type": "string", "enum": ["ClusterIP", "NodePort", "LoadBalancer"] },
        "port": { "type": "integer", "minimum": 1, "maximum": 65535 }
      }
    },
    "autoscaling": {
      "type": "object",
      "properties": {
        "enabled": { "type": "boolean" },
        "minReplicas": { "type": "integer", "minimum": 1 },
        "maxReplicas": { "type": "integer", "minimum": 1 }
      }
    }
  },
  "required": ["image", "service"]
}
```

## templates/deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "<CHARTNAME>.fullname" . }}
  labels:
    {{- include "<CHARTNAME>.labels" . | nindent 4 }}
  {{- with .Values.commonAnnotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "<CHARTNAME>.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
        {{- with .Values.podAnnotations }}
        {{- toYaml . | nindent 8 }}
        {{- end }}
      labels:
        {{- include "<CHARTNAME>.labels" . | nindent 8 }}
        {{- with .Values.podLabels }}
        {{- toYaml . | nindent 8 }}
        {{- end }}
    spec:
      {{- with .Values.imagePullSecrets }}
      imagePullSecrets:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      serviceAccountName: {{ include "<CHARTNAME>.serviceAccountName" . }}
      automountServiceAccountToken: {{ .Values.serviceAccount.automount }}
      {{- with .Values.podSecurityContext }}
      securityContext:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      containers:
        - name: {{ .Chart.Name }}
          {{- with .Values.securityContext }}
          securityContext:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          image: {{ include "<CHARTNAME>.image" . | quote }}
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: {{ .Values.containerPort }}
              protocol: TCP
          {{- with .Values.env }}
          env:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          {{- if or .Values.envFrom .Values.existingSecret }}
          envFrom:
            {{- with .Values.existingSecret }}
            - secretRef:
                name: {{ . }}
            {{- end }}
            {{- with .Values.envFrom }}
            {{- toYaml . | nindent 12 }}
            {{- end }}
          {{- end }}
          {{- with .Values.livenessProbe }}
          livenessProbe:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          {{- with .Values.readinessProbe }}
          readinessProbe:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          {{- with .Values.startupProbe }}
          startupProbe:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          {{- with .Values.resources }}
          resources:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          {{- with .Values.volumeMounts }}
          volumeMounts:
            {{- toYaml . | nindent 12 }}
          {{- end }}
      {{- with .Values.volumes }}
      volumes:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.affinity }}
      affinity:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.topologySpreadConstraints }}
      topologySpreadConstraints:
        {{- toYaml . | nindent 8 }}
      {{- end }}
```

Note: `containerPort` must be an integer. The Service targets the *named* port `http`, so keep a dedicated `containerPort` value rather than reusing `service.port` or a name (verified: reusing a name renders `containerPort: http`, rejected by the API).

## templates/service.yaml

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "<CHARTNAME>.fullname" . }}
  labels:
    {{- include "<CHARTNAME>.labels" . | nindent 4 }}
  {{- with .Values.service.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
spec:
  type: {{ .Values.service.type }}
  ports:
    - port: {{ .Values.service.port }}
      targetPort: http
      protocol: TCP
      name: http
  selector:
    {{- include "<CHARTNAME>.selectorLabels" . | nindent 4 }}
```

## templates/serviceaccount.yaml and RBAC

```yaml
{{- if .Values.serviceAccount.create -}}
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ include "<CHARTNAME>.serviceAccountName" . }}
  labels:
    {{- include "<CHARTNAME>.labels" . | nindent 4 }}
  {{- with .Values.serviceAccount.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
automountServiceAccountToken: {{ .Values.serviceAccount.automount }}
{{- end }}
```

`templates/role.yaml` (only what the app needs):

```yaml
{{- if .Values.rbac.create -}}
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: {{ include "<CHARTNAME>.fullname" . }}
  labels:
    {{- include "<CHARTNAME>.labels" . | nindent 4 }}
rules:
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: {{ include "<CHARTNAME>.fullname" . }}
  labels:
    {{- include "<CHARTNAME>.labels" . | nindent 4 }}
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: {{ include "<CHARTNAME>.fullname" . }}
subjects:
  - kind: ServiceAccount
    name: {{ include "<CHARTNAME>.serviceAccountName" . }}
    namespace: {{ .Release.Namespace }}
{{- end }}
```

(`namespace` in a RoleBinding subject is required by the API and is the accepted exception to the "no namespace" rule.)

## templates/hpa.yaml and pdb.yaml

```yaml
{{- if .Values.autoscaling.enabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "<CHARTNAME>.fullname" . }}
  labels:
    {{- include "<CHARTNAME>.labels" . | nindent 4 }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "<CHARTNAME>.fullname" . }}
  minReplicas: {{ .Values.autoscaling.minReplicas }}
  maxReplicas: {{ .Values.autoscaling.maxReplicas }}
  metrics:
    {{- with .Values.autoscaling.targetCPUUtilizationPercentage }}
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: {{ . }}
    {{- end }}
    {{- with .Values.autoscaling.targetMemoryUtilizationPercentage }}
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: {{ . }}
    {{- end }}
{{- end }}
```

```yaml
{{- if .Values.podDisruptionBudget.enabled }}
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: {{ include "<CHARTNAME>.fullname" . }}
  labels:
    {{- include "<CHARTNAME>.labels" . | nindent 4 }}
spec:
  {{- with .Values.podDisruptionBudget.minAvailable }}
  minAvailable: {{ . }}
  {{- end }}
  {{- with .Values.podDisruptionBudget.maxUnavailable }}
  maxUnavailable: {{ . }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "<CHARTNAME>.selectorLabels" . | nindent 6 }}
{{- end }}
```

## templates/ingress.yaml (helm create)

```yaml
{{- if .Values.ingress.enabled -}}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "<CHARTNAME>.fullname" . }}
  labels:
    {{- include "<CHARTNAME>.labels" . | nindent 4 }}
  {{- with .Values.ingress.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
spec:
  {{- with .Values.ingress.className }}
  ingressClassName: {{ . }}
  {{- end }}
  {{- if .Values.ingress.tls }}
  tls:
    {{- range .Values.ingress.tls }}
    - hosts:
        {{- range .hosts }}
        - {{ . | quote }}
        {{- end }}
      secretName: {{ .secretName }}
    {{- end }}
  {{- end }}
  rules:
    {{- range .Values.ingress.hosts }}
    - host: {{ .host | quote }}
      http:
        paths:
          {{- range .paths }}
          - path: {{ .path }}
            {{- with .pathType }}
            pathType: {{ . }}
            {{- end }}
            backend:
              service:
                name: {{ include "<CHARTNAME>.fullname" $ }}
                port:
                  number: {{ $.Values.service.port }}
          {{- end }}
    {{- end }}
{{- end }}
```

Inside `range`, `.` is the item; use `$` to reach the root context.

## templates/httproute.yaml (Gateway API, helm create)

```yaml
{{- if .Values.httpRoute.enabled -}}
{{- $fullName := include "<CHARTNAME>.fullname" . -}}
{{- $svcPort := .Values.service.port -}}
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: {{ $fullName }}
  labels:
    {{- include "<CHARTNAME>.labels" . | nindent 4 }}
  {{- with .Values.httpRoute.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
spec:
  parentRefs:
    {{- toYaml .Values.httpRoute.parentRefs | nindent 4 }}
  {{- with .Values.httpRoute.hostnames }}
  hostnames:
    {{- toYaml . | nindent 4 }}
  {{- end }}
  rules:
    {{- range .Values.httpRoute.rules }}
    - matches:
        {{- toYaml .matches | nindent 8 }}
      {{- with .filters }}
      filters:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      backendRefs:
        - name: {{ $fullName }}
          port: {{ $svcPort }}
          weight: 1
    {{- end }}
{{- end }}
```

## templates/configmap.yaml with file include

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "<CHARTNAME>.fullname" . }}
  labels:
    {{- include "<CHARTNAME>.labels" . | nindent 4 }}
data:
  app.yaml: |
    {{- tpl (.Files.Get "config/app.yaml") . | nindent 4 }}
  {{- with .Values.extraConfig }}
  extra.yaml: |
    {{- tpl . $ | nindent 4 }}
  {{- end }}
```

`config/app.yaml` lives at the chart root (not under `templates/`) and may contain `{{ .Values.x }}` rendered by `tpl`.

## Secret: generate once, keep on upgrade

```yaml
{{- if not .Values.existingSecret -}}
{{- $name := printf "%s-credentials" (include "<CHARTNAME>.fullname" .) -}}
{{- $existing := lookup "v1" "Secret" .Release.Namespace $name -}}
apiVersion: v1
kind: Secret
metadata:
  name: {{ $name }}
  labels:
    {{- include "<CHARTNAME>.labels" . | nindent 4 }}
  annotations:
    helm.sh/resource-policy: keep
type: Opaque
data:
  {{- if $existing }}
  password: {{ index $existing.data "password" }}
  {{- else }}
  password: {{ randAlphaNum 32 | b64enc }}
  {{- end }}
{{- end }}
```

`lookup` returns an empty map during `helm template` and `--dry-run=client`, so a fresh value renders there; on a live install/upgrade it preserves the existing one.

## Hook Job (migration)

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ include "<CHARTNAME>.fullname" . }}-migrate
  labels:
    {{- include "<CHARTNAME>.labels" . | nindent 4 }}
  annotations:
    helm.sh/hook: pre-install,pre-upgrade
    helm.sh/hook-weight: "0"
    helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded
spec:
  backoffLimit: 2
  ttlSecondsAfterFinished: 600
  template:
    metadata:
      labels:
        {{- include "<CHARTNAME>.selectorLabels" . | nindent 8 }}
        app.kubernetes.io/component: migrate
    spec:
      restartPolicy: Never
      serviceAccountName: {{ include "<CHARTNAME>.serviceAccountName" . }}
      {{- with .Values.podSecurityContext }}
      securityContext:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      containers:
        - name: migrate
          image: {{ include "<CHARTNAME>.image" . | quote }}
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          args: ["migrate"]
          {{- with .Values.securityContext }}
          securityContext:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          {{- with .Values.existingSecret }}
          envFrom:
            - secretRef:
                name: {{ . }}
          {{- end }}
```

## templates/tests/test-connection.yaml

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: "{{ include "<CHARTNAME>.fullname" . }}-test-connection"
  labels:
    {{- include "<CHARTNAME>.labels" . | nindent 4 }}
  annotations:
    helm.sh/hook: test
    helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded
spec:
  restartPolicy: Never
  securityContext:
    runAsNonRoot: true
    runAsUser: 65532
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: wget
      image: docker.io/library/busybox:1.36
      command: ["wget"]
      args: ["-qO-", "{{ include "<CHARTNAME>.fullname" . }}:{{ .Values.service.port }}/healthz"]
      securityContext:
        allowPrivilegeEscalation: false
        capabilities:
          drop: ["ALL"]
```

## templates/NOTES.txt (trimmed)

```gotemplate
{{ .Chart.Name }} {{ .Chart.Version }} (app {{ .Chart.AppVersion }}) released as {{ .Release.Name }} in {{ .Release.Namespace }}.

{{- if .Values.ingress.enabled }}
URLs:
{{- range .Values.ingress.hosts }}
  http{{ if $.Values.ingress.tls }}s{{ end }}://{{ .host }}
{{- end }}
{{- else }}
Port-forward:
  kubectl -n {{ .Release.Namespace }} port-forward svc/{{ include "<CHARTNAME>.fullname" . }} 8080:{{ .Values.service.port }}
{{- end }}

Verify: helm test {{ .Release.Name }} -n {{ .Release.Namespace }}
```

## Library chart pattern

`lib/Chart.yaml`: `type: library`, `templates/_deployment.tpl`:

```gotemplate
{{- define "lib.deployment" -}}
{{- $ctx := index . 0 -}}
{{- $override := index . 1 -}}
{{- $base := fromYaml (include "lib.deployment.tpl" $ctx) -}}
{{- $custom := fromYaml (include $override $ctx) -}}
{{- toYaml (mergeOverwrite $base $custom) -}}
{{- end -}}
```

Consumer `templates/deployment.yaml`: `{{- include "lib.deployment" (list . "app.deployment") -}}` with `{{- define "app.deployment" -}}` providing only the differing fields. Declare the library in `dependencies` with a `file://` or repository URL.

## .helmignore additions

```
ci/
*.md
!README.md
tests/
.git/
.github/
*.swp
*.bak
```
