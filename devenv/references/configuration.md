# Adapt the environment to the project

## KCL contract

The local configuration imports `.schema as schema` and binds
`config = schema.Qemu { ... }`. Use `option('qemu_butane_user_name')` for guest
paths; `_usr` is not defined. Read host paths with `file.read_env('HOME')` after
importing `file`, not an uninjected `option('HOME')`.

Initialize `.devenv/config.k` from the submodule's `.devenv/exemple.config.k` only
when absent, then adapt it directly. Remove irrelevant demo files, services and
personal paths from the new local config; retain defaults and additions required
by the project. Choose CPU/RAM/disk from the workload, not the example's values.
Existing config.k is user-owned and must not be replaced by the example on reruns.

| Field | Meaning and adaptation |
| --- | --- |
| `hardware.cpu` | Native vCPUs; do not assume one is sufficient for builds |
| `hardware.memory.size/unit` | Memory, typically M or G |
| `hardware.disk.size/unit` | Writable guest disk; use G with the baseline's resize arithmetic |
| `butane.custom_pkgs` | Additional RPMs layered using rpm-ostree, not host packages |
| `butane.custom_mise_tools` | Tool/version map merged with defaults; derive versions from target manifests/locks |
| `butane.custom_files` | Inline guest files with absolute path and decimal mode |
| `butane.custom_copies` | Host text files baked into Ignition, not live synchronization |
| `butane.units +=` | Append units while retaining default provisioning/mount units |
| `butane.github.token` | Optional value from `option('github_token')`, not a committed literal |
| `butane.beszel` | Optional monitoring; omit when not needed |

Defaults include Git, Terra repository integration, mise, topgrade, Cockpit and
Podman integration; starship/fastfetch use floating versions. Do not describe the
whole environment as reproducible solely because its runtime commit is pinned.
Record project tool versions and the resolved FCOS release. Avoid layering tools
twice when the project's mise configuration already owns their version.

## Files, users and services

Butane modes are decimal: 420 = 0644, 384 = 0600, 493 = 0755, 288 = 0440.
Inspect rendered ownership rather than assuming every file defaults to the user;
specify user/group where necessary, especially for system-owned service files.
The renderer moves `core` to UID 2000 to avoid the common host-UID 1000 collision.
Preserve that intent and detect actual collisions, including a host UID of 2000.

Copies are read with `file.read` at render time; missing sources are silently
filtered out by the baseline. Explicitly validate required sources. Host edits do
not update baked copies in a running VM. Shared project files, by contrast, are
writable host files: guest edits affect the target checkout immediately.

Append project services with dependencies on their real prerequisites (network,
workspace mount, installed tools), not merely on a running VM. Use
`ConditionVirtualization=vm` for VM-specific units; `qemu` alone excludes KVM/HVF.
Keep reusable unit/file bodies in `templates.k` when modifying the runtime itself.
For project Quadlets/Compose use the container companion and validate image
provenance, ports, data ownership and actual readiness. Do not copy upstream's
demo Alpine sleeper, example host paths or README's nginx image as project defaults.

## Local credentials and monitoring

The baseline automatically copies existing host OpenCode config and auth files
into Ignition and can embed GitHub/Beszel tokens. Account for these actual inputs:
use a disposable HOME and dummy credentials for render tests, avoid printing full
KCL datasets/rendered files and redact command logs. The baseline logs token-bearing
render commands; remove/redact such logging in an integration before running it
with real credentials. Keep generated secret-bearing files local with restricted
permissions; Git ignores alone do not restrict local access.

Beszel is opt-in. The agent is a Quadlet in WebSocket mode with `DISABLE_SSH=true`,
hub key, token and UUID system name. The Taskfile can authenticate to the hub and
create a token while evaluating variables; rendering/dry-run is not necessarily
side-effect free. Inspect host API URL separately from guest `HUB_URL`: the baseline
constructs the former from localhost and the configured port. A localhost URL in
the guest does not refer to the host. Verify reachability instead of inheriting the
example bridge IP or macOS URL. Diagnose missing credentials without displaying them.

Keep the existing development defaults explicit (including passwordless guest sudo,
the demo `dev` account, permissive SELinux and QEMU `cache=unsafe`). They describe
a disposable local development system, not a production VM configuration.
