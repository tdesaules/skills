# Integrate and distribute the runtime

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

## Dependency layout

Preserve an existing installation method. For a new Git target, prefer a pinned
submodule at `.devenv` when consistent with the repository's dependency conventions.
Record the upstream URL and gitlink; document `git submodule update --init --recursive`
for fresh clones. Do not follow a moving branch at every `up`.

If the project uses vendored sources instead, copy only the required tracked source
files, helpers and upstream license, record the upstream commit and local patches,
and document the update procedure. Do not introduce a nested unmanaged clone or
depend on the author's absolute checkout path. Use the Git companion for mutations.

Keep the runtime internally named `taskfile.qemu.yaml`: recursive `status` calls
refer to that name. Integrate into the target's existing Taskfile; for a new root
entrypoint use lowercase `taskfile.yml`. Do not rename an existing `taskfile.yaml`
or replace its tasks merely for this preference.

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

## Shareable versus local configuration

Keep a project-specific recipe, for example `dev/devenv.config.k`, in target Git.
It is an initialization source copied into `.devenv/config.k`; its `.schema` import
resolves there, not at the recipe's storage location. Document that distinction.
Provide an init operation that copies only when the destination is absent and
otherwise preserves user changes. Treat later recipe updates as an explicit merge
or refresh, not an overwrite on every startup.

Ignore generated paths at their actual location: `config.k`, `config.bu`,
`config.ign`, `.uuid` and `.task` within the runtime directory; include root `.task`
if the wrapper creates it. A submodule has its own ignore rules. Do not broadly
ignore `.devenv` when its source or gitlink must be committed. Keep qcow2 images,
PID/log files and credentials out of Git. Preserve license notices when vendoring.

Fresh-clone acceptance: initialize the pinned dependency, initialize local config,
run host checks, render, start, reach the shared project and run its smoke command.
Dependency updates must preserve personal config/identity and record the new pin;
FCOS updates require matching release and checksums for both native architectures.
