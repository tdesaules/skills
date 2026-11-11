# Validate, operate and diagnose

## Host preflight

Identify OS/architecture and versions before selecting commands. The baseline
normalizes arm64 to aarch64, uses KVM on Linux and HVF on macOS, q35 for x86_64
and virt for aarch64. Check native QEMU support and firmware rather than silently
falling back to TCG or claiming all host/guest combinations were tested.

Check go-task, KCL, Butane, the selected `qemu-system-*`, `qemu-img`, jq, curl,
gpgv, `shasum` or `sha256sum`, unxz, SSH and the shell/helper requirements.
Upstream `check` omits some lifecycle dependencies and also contacts FCOS stream
metadata. It is useful, not a complete offline preflight. Inspect sudo availability
for actual commands; do not create broad passwordless-sudo rules as a shortcut.

Linux needs KVM, NetworkManager `br-qemu` with shared IPv4, bridge-helper permission
via `/etc/qemu/bridge.conf`, and working host/guest mDNS/firewall routing. Upstream
tasks activate/deactivate an existing profile; they do not provision it. Check its
actual owner and use chezmoi for managed host changes. macOS uses `vmnet-shared`;
aarch64 additionally needs a usable EDK2 pflash path. `qemu_edk2_path` is a KCL
option, not automatically a forwarded Task CLI variable: verify argument plumbing.
Require an available SSH key recognized by the selected config; baseline discovers
`id_ed25519.pub` and `id_rsa.pub`. Preserve the target's SSH policy.

## Render before boot

1. Initialize local config without overwriting it. Persist identity in the intended
   directory. For tests use an isolated source copy, HOME, fixed fixture UUID and
   empty tokens, with Beszel omitted; do not evaluate personal host config.
2. Evaluate `config.k` to JSON and render `butane-render.k --path_selector butane`.
   Pass the same `taskfile_dir`, `qemu_butane_user_name`, `qemu_butane_user_id`,
   `qemu_host_arch`, `qemu_host_os` and needed credential/firmware options to both.
   Ensure the shell's PWD used for rendering names the target project root.
3. Run `butane --strict` on the resulting Butane file. Inspect selected fields for
   correct users, hostname, mount tags, workspace path, provisioning units and
   required project tools without dumping secrets. Check QEMU launch paths too.
4. Make render invalidation include `templates.k`, project recipe changes and
   relevant copy/option inputs. Baseline `build-butane.sources` omits templates and
   copied-file contents, so changing them may leave stale output. Do not claim an
   up-to-date cache is proof of correct regeneration.

Check KCL filesystem-access compatibility too. With CLI 0.13.3, the analyzed
baseline failed with `path ... escapes module root` while probing the Homebrew
firmware candidate, even for an x86_64 render. Host HOME file probes can have the
same constraint. Do not misdiagnose this as invalid project configuration or invent
an unsupported sandbox flag. Resolve the runtime/tool-version contract explicitly.
An isolated render fixture can use a module-local HOME and explicit dummy firmware
path to exercise the schema, but that does not resolve real-host provisioning or
validate the firmware. Record that limitation separately.

Generated Ignition changes do not reprovision an existing installed guest. Preserve
guest-only data before an intended rebuild; use the lifecycle's disposal path and
retain identity. Re-running `up` or rebooting alone is not a config refresh.

## Runtime acceptance

Use the target wrapper if integrated; otherwise run from the agreed project root
with `task -t .devenv/taskfile.qemu.yaml <task>`. Internal tasks are not a public
standalone render API; use direct KCL/Butane commands for render-only validation.

- Start with `up attach=false` for automation. It still performs checks, download,
  SHA-256/GPG image verification, render, launch, SSH and provisioning waits, and
  staged-update reboot; it skips only the final interactive SSH attachment.
- Verify image download/verification failures block use of the disk. Keep release
  and both architecture checksums consistent; do not disable verification to boot.
  The GitHub Actions advisory-scanning policy does not waive this runtime check.
- Verify `status` against the actual VM process and identity. Baseline status only
  checks PID liveness; it is not a health or PID-ownership proof. Its reported image
  path also differs from the actual `qemu.qcow2` launch path; inspect the latter.
- Reach `<uuid>.local` over SSH; verify `install-system-pkgs.service` and
  `run-topgrade.service` completed successfully and any required reboot finished.
- Access the guest workspace to trigger automount, confirm it represents the target
  checkout, and verify intended write ownership without broad chmod changes.
- Run the project's existing build/test/smoke command there with bounded execution.
  Noninteractive SSH does not source interactive mise activation; use an explicit
  `mise exec -- <command>` or the project's configured executable path when needed.
- For services, verify their health endpoint/socket from the intended client, not
  just the existence of a unit or container. Cockpit is normally on port 9090.

Record native platform and observed outcomes. Render tests for a second platform
do not constitute boot qualification. If acceleration, networking or credentials
are unavailable, finish source/render checks and name the exact runtime blocker.

## Operations and troubleshooting

| Operation/symptom | Action |
| --- | --- |
| Routine shutdown | `stop`; retain config, identity and guest disk |
| Disposable rebuild | `down`, then `up`; guest-only data is lost |
| Generated config changed, guest unchanged | Ignition is first-boot provisioning; plan a rebuild |
| Wrong source in guest | Inspect PWD, include dir, explicit project path and QEMU fsdev |
| SSH never ready | Inspect serial log, UUID/hostname agreement, bridge/mDNS and authorized keys |
| Tool provisioning failed | Read guest journal for install-system-pkgs and run-topgrade |
| Required copied file absent | Check source existence and render invalidation |
| QEMU not starting | Verify architecture, acceleration, EDK2, sudo and launch path quoting |

`logs` tails indefinitely; use bounded log reads in automation. Preserve logs on
failure. Inspect `down` before describing its effects: the baseline force-stops,
may deactivate the shared bridge if no other VM uses it, cleans matching Beszel
records, deletes qemu.qcow2/PID/log and config.bu/config.ign, but retains `.uuid`,
`config.k`, the workspace directory and downloaded image cache. Do not replace it
with `rm -rf ~/.qemu` or delete unrelated VM identities. Confirm process ownership
before stopping a PID from a stale pidfile.
