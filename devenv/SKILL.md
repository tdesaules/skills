---
name: devenv
description: >-
  Use when adding, distributing, configuring, or troubleshooting a repository-local
  QEMU development environment using the qemu-dev-env Git submodule at .devenv:
  local config.k, Fedora CoreOS, KCL, Butane, Ignition, Task integration, shared
  workspace, SSH and VM lifecycle. Adapt the VM
  to the target project's tools and services. Not for Nix devenv, Python virtualenvs,
  standalone containers, production VM fleets, or QEMU emulator development.
license: GPL-3.0-or-later
compatibility: Integration requires Git and qemu-dev-env sources. Rendering requires KCL and Butane; VM operation requires go-task, QEMU, host virtualization/networking, SSH, jq, curl, GPG verification and xz tools on Linux or macOS.
---

# Repository QEMU development environment

## Scope and companions

Make a target repository usable inside a disposable Fedora CoreOS QEMU VM using
`tdesaules/qemu-dev-env` as a Git submodule at `.devenv`, following the integration
used in `thales-genai-lab`. Configure `.devenv/config.k` locally from the submodule's
`exemple.config.k`, include its Taskfile under `devenv:`, and expose appropriate
root tasks. Deliver that integration in the existing target repository, with
operating instructions and evidence of what actually works. These are the user's
development conventions, not universal QEMU requirements. Respect explicit target
repository overrides. Do not substitute Nix, a devcontainer or a generic VM manager.

Read the selected qemu-dev-env revision before adapting it; this skill does not
vendor its implementation or promise compatibility with every future revision.

- Use `container` for project containers, Compose or Quadlets, including image
  provenance and the collection's base-image allowlist. Fedora CoreOS qcow2 is a
  VM disk, not an OCI base image. If that companion is unavailable, report the
  container policy check as unresolved rather than substituting a bare base image.
- Use `chezmoi` only for host configuration actually managed by chezmoi, notably
  the Linux bridge/helper/firewall. Repository integration does not own host dotfiles.
- Use `github-actions` when CI or release workflows are requested. Providing a
  local development VM does not itself require publishing images or changing CI.
- For Git mutation, load `conventionalcommits` then `commit`; retain the target's
  commit policy. Do not push unless explicitly authorized and permitted by it.
- Use `helm` only for actual chart work inside the environment. Installing tools
  does not authorize deployment to a cluster.

## Workflow

1. Read target instructions, Git status, README, Task/mise files, language manifests,
   locks, build/test commands and service definitions. Identify the target root,
   existing `.devenv`, host OS/architecture, available acceleration, and project
   resource needs. Inspect existing integration before choosing a new layout.
2. Locate the supplied qemu-dev-env checkout or resolve its upstream revision.
   Read its Taskfile, schema, renderer and templates, not only its README. Record
   URL, commit and local modifications. Never copy its personal `config.k`, `.uuid`,
   `.task`, rendered configuration or VM disk into the target.
3. Read [submodule integration](references/integration.md). Add or initialize the
   `.devenv` Git submodule and record its commit in the parent; integrate Task
   without replacing existing commands. Preserve the
   internal `taskfile.qemu.yaml` name and verify target-root sharing independently
   of the runtime's working directory. Document submodule initialization and updates.
4. Read [project configuration](references/configuration.md). Derive packages,
   tool versions, hardware and optional services from the project. Keep the
   configuration in `.devenv/config.k`, ignored by the submodule and user-owned.
   Initialize from `.devenv/exemple.config.k` only when absent, then adapt it to
   the project. Do not retain irrelevant demo services or personal host paths.
   A separate tracked recipe or config generator is optional, only when requested.
5. Read [validation and lifecycle](references/validation.md) before rendering or
   operating a VM. Validate paths, stable identity, both KCL argument sets and
   generated files before launch. Run a noninteractive startup when VM execution
   is in scope, then test the actual project in the guest workspace.
6. Document prerequisites, initialization, start/connect/stop/destroy, configuration
   refresh and troubleshooting in the target README or `docs/devenv.md`. Explain
   where guest-only data and shared source live. Preserve existing local config
   and identity on reruns; use `stop` for routine shutdown, `down` for disposal.
7. Review the diff and run applicable checks. Report render validation, host checks,
   VM startup, provisioning and project smoke tests as separate evidence. Commit
   the integration according to the target's policy, including `.gitmodules`, the
   submodule gitlink, root tasks and docs, not local config or runtime state.

## Deliverable contract

A completed integration includes:

- A `.devenv` Git submodule with its URL and recorded commit in the parent repository.
- A local `.devenv/config.k` adapted to required tools/resources, kept out of Git.
- Task integration under `devenv:` and project-appropriate root lifecycle entrypoints.
- Documented non-overwriting configuration setup and explicit submodule updates.
- Correct target-root sharing, stable per-checkout identity and scoped ignore rules.
- A guest build/test or service smoke command based on the project's own interface.
- Validation results and precise unresolved host/runtime prerequisites.

An installed dependency is not a configured VM; successful rendering is not a boot;
SSH availability is not successful provisioning. Do not claim macOS/ARM64 success
from Linux/x86_64 checks or call the environment ready without the guest checks.

For reviews use `file:line → defect → consequence → correction`. For changes return
paths, runtime revision, setup/operation commands, tests run and any remaining blocker.

## Sources

- [qemu-dev-env](https://github.com/tdesaules/qemu-dev-env)
- [Task includes](https://taskfile.dev/docs/guide#including-other-taskfiles)
- [Fedora CoreOS provisioning](https://docs.fedoraproject.org/en-US/fedora-coreos/producing-ign/)
