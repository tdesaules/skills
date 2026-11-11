# Integrate the .devenv Git submodule

## Source baseline

This guidance was derived from qemu-dev-env commit
`c60632ccee08750adc5c6531efccfbaee9a06eae`. Reinspect the revision being integrated;
the commit identifies the analysis baseline, not a mandatory forever pin or a
claim of successful VM qualification.

| Source | Responsibility |
| --- | --- |
| `taskfile.qemu.yaml` | Downloads, validation, render, bridge activation, lifecycle and readiness |
| `schema.k` | Hardware, FCOS release/checksums, QEMU command, default provisioning |
| `templates.k` | Guest files, systemd units and optional Beszel Quadlet |
| `butane-render.k` | KCL-to-Butane projection and guest users |
| `exemple.config.k` | Upstream example; French spelling is intentional |
| `scripts/utils.sh` | Task logging/error helpers |

Do not import upstream AGENTS.md wholesale into the target: instructions for
maintaining the runtime are not necessarily instructions for the application.

## Submodule contract

Use the `thales-genai-lab` integration as the reference pattern, in an existing or
new target repository. `.devenv` is a Git submodule, not a copied runtime directory
or an unmanaged nested clone. Its `.gitmodules` entry is:

```ini
[submodule ".devenv"]
    path = .devenv
    url = https://github.com/tdesaules/qemu-dev-env.git
```

Inspect existing state first. If absent, use the Git companion to add the submodule
with `git submodule add https://github.com/tdesaules/qemu-dev-env.git .devenv`.
If registered but uninitialized, use `git submodule update --init --recursive -- .devenv`.
Do not overwrite an existing directory or register the same submodule twice.
The parent records `.gitmodules` and the gitlink commit; configuration remains local
inside the submodule. No new clone of the target is required to add this integration.
Do not introduce vendoring or a second recipe directory unless explicitly requested.

Keep the runtime internally named `taskfile.qemu.yaml`: recursive `status` calls
refer to that name. Integrate into the target's existing Taskfile; for a new root
entrypoint use lowercase `taskfile.yml`. Do not rename an existing `taskfile.yaml`
or replace its tasks merely for this preference.

The reference include is:

```yaml
includes:
  devenv:
    taskfile: ./.devenv/taskfile.qemu.yaml
    dir: ./.devenv
```

Merge it into the existing Taskfile. Validate the actual path behavior described
below rather than treating this include as proof of correct workspace sharing.
Add root `up` calling `devenv:up` with `attach: "false"`, `down` calling
`devenv:down`, and `ssh` calling `devenv:ssh` where these names are available.
Preserve existing tasks on conflicts. A project `dev` task can sequence VM startup,
project bootstrap and SSH. Zed/OpenCode tasks are optional project conveniences;
do not copy the lab's cluster/secrets bootstrap into unrelated projects.

Desired interface: `task devenv:check`, `task devenv:up attach=false`,
`task devenv:status`, `task devenv:ssh`, `task devenv:logs`, `task devenv:mgmt`,
`task devenv:stop`, `task devenv:down`. go-task is a real dependency of this runtime;
the unrelated catalog policy making Task optional is not applicable here.

## Two path roots, one stable identity

Do not paste an include block without checking its resulting paths:

- `TASKFILE_DIR` / KCL `taskfile_dir` must locate `.devenv` configuration and `.uuid`.
- Host `PWD` in `schema.k` supplies the source of the writable `workspace` 9p share.
  It must resolve to the target project root, not `.devenv`, the agent's checkout
  or the directory from which the user happened to invoke Task.
- The guest mount is `/var/home/<user>/workspace`; the VM state share is
  `/var/home/<user>/.qemu`. Runtime state is `~/.qemu/<uuid>/` on the host.

An include with `dir: ./.devenv` can make the wrong directory become the workspace.
Running at the target root instead also requires fixing/confirming all renderer
arguments: the baseline's `build-butane` omits `taskfile_dir`, host OS and architecture,
although `kcl_dataset` passes them. These stages must use the same explicit values
and persisted identity. Inspect both, plus recursive Task invocations.

Choose a consistent execution directory and propagate the roots explicitly. When
adapting the runtime, an explicit project-root option is preferable to guessing
from a parent directory; update schema and both render invocations together. Quote
paths through Task, KCL and QEMU shell construction; the baseline joins command
options into a string, so paths with spaces require real verification or a fix.
Do not advertise arbitrary-path support based only on YAML parsing.

Write `.uuid` before renders that depend on it, retain it across stop/start and
normal rebuilds, and verify that QEMU name, MAC-derived identity, workspace,
hostname and SSH destination agree. Missing `.uuid` invokes random UUID generation
in KCL; separate unpersisted evaluations can disagree. Never delete another
checkout's identity or reuse a copied identity for a second VM.

If a pinned submodule needs fixes, retain them as an explicit upstream commit or
a documented reproducible patch mechanism consistent with the target. A dirty
submodule or an unavailable local-only commit is not a distributable integration.
Report remote availability as unresolved if publishing the prerequisite is outside
authorization; do not silently push it.

## Local config.k and updates

Create `.devenv/config.k` from `.devenv/exemple.config.k` only if absent. Adapt that
local file directly to the target's hardware, packages, mise tools, files and units.
Preserve an existing config and merge requested changes deliberately. The submodule
already ignores config.k; do not force-add it or require a tracked duplicate in the
parent. Document the project-specific configuration and setup in the target README.
A tracked recipe or generator may be added only when requested, not as a condition
for completing the standard integration.

Ignore generated paths at their actual location: `config.k`, `config.bu`,
`config.ign`, `.uuid` and `.task` within the runtime directory; include root `.task`
if the wrapper creates it. A submodule has its own ignore rules. Do not broadly
ignore `.devenv` when its source or gitlink must be committed. Keep qcow2 images,
PID/log files and credentials out of Git.

Acceptance in the target checkout: initialize the submodule and local config,
run host checks, render, start, reach the shared project and run its smoke command.
On another checkout, the same setup requires submodule initialization and creation
of its own ignored config.k; Git does not transport personal config or VM state.

Keep updates explicit, separate from `up`: the lab exposes `task git:sub-module`
in `taskfile.git.yaml`, runs `git submodule update --remote .devenv`, then records
the changed gitlink in a parent commit. Adapt this interface to target Git policy,
including approval requirements and a why-body; never push automatically. Inspect
submodule changes before updating and preserve config/identity. FCOS updates belong
to the runtime and require matching release and checksums for both architectures.
