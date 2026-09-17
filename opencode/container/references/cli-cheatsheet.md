# CLI cheatsheet: podman / buildah / skopeo / nerdctl vs docker

## Engine detection

```bash
command -v podman buildah skopeo nerdctl docker
podman info --format '{{.Host.Security.Rootless}} {{.Store.GraphDriverName}} {{.Host.CgroupsVersion}}'
docker --version            # "podman version ..." means docker is a podman alias
nerdctl info --format '{{.Driver}}'
```

## Command mapping

| Intent                        | podman / buildah / skopeo                                        | docker                                   | nerdctl                          |
| ----------------------------- | ---------------------------------------------------------------- | ---------------------------------------- | -------------------------------- |
| Build                         | `podman build -t app:dev .`                                      | `docker build -t app:dev .`              | `nerdctl build -t app:dev .`     |
| Build a stage                 | `podman build --target build .`                                  | `docker build --target build .`          | same                             |
| Build arg / secret            | `podman build --build-arg K=V --secret id=tok,src=./tok .`       | `docker build --build-arg K=V --secret id=tok,src=./tok .` | same           |
| Fresh base + no cache         | `podman build --pull=always --no-cache .`                        | `docker build --pull --no-cache .`       | same                             |
| Multi-arch to manifest        | `podman build --platform linux/amd64,linux/arm64 --manifest reg/app:t . && podman manifest push --all reg/app:t` | `docker buildx build --platform linux/amd64,linux/arm64 --push -t reg/app:t .` | `nerdctl build --platform ... --output type=image,push=true` |
| Export stage files            | `podman build --target build --output type=local,dest=out .`     | `docker build --target build -o out .`   | `nerdctl build -o type=local,dest=out .` |
| SBOM                          | `podman build --sbom=syft --sbom-output sbom.json .`             | `docker buildx build --sbom=true .`      | —                                |
| Reproducible                  | `podman build --timestamp 0 --omit-history .`                    | `SOURCE_DATE_EPOCH=0 docker buildx build --output type=image,rewrite-timestamp=true .` | — |
| Run hardened                  | `podman run --rm --read-only --tmpfs /tmp --cap-drop=ALL --security-opt=no-new-privileges --user 65532:65532 --pids-limit 256 -m 512m -p 127.0.0.1:8080:8080 app:dev` | same flags | same flags |
| Bind mount, keep host UID     | `podman run --userns=keep-id -v ./data:/data:Z app`              | `docker run -u $(id -u):$(id -g) -v ./data:/data app` | `nerdctl run -v ./data:/data app` |
| Healthcheck now               | `podman healthcheck run <ctr>`                                   | `docker inspect --format '{{.State.Health.Status}}' <ctr>` | `nerdctl inspect ...` |
| Inspect image config          | `podman image inspect app:dev --format '{{.User}} {{.Config.Entrypoint}} {{.Config.Cmd}}'` | `docker image inspect ...` | `nerdctl image inspect ...` |
| Layers / history              | `podman image tree app:dev`; `podman history --no-trunc app:dev` | `docker history --no-trunc app:dev`      | `nerdctl history app:dev`        |
| Size                          | `podman images --format '{{.Repository}}:{{.Tag}} {{.Size}}'`    | `docker images`                          | `nerdctl images`                 |
| Inspect remote (no pull)      | `skopeo inspect docker://reg/app:t`; `--config`; `--raw`         | `docker manifest inspect reg/app:t`      | —                                |
| Resolve digest                | `skopeo inspect --format '{{.Digest}}' docker://reg/app:t`       | `docker buildx imagetools inspect reg/app:t` | —                            |
| List tags                     | `skopeo list-tags docker://reg/app`                              | —                                        | —                                |
| Copy registry→registry        | `skopeo copy --all docker://src docker://dst`                    | `docker pull && docker tag && docker push` | `nerdctl pull/tag/push`        |
| Mirror / air-gap              | `skopeo sync --src docker --dest dir reg/app ./mirror`; `skopeo sync --src dir --dest docker ./mirror reg2/` | `docker save` / `docker load` | `nerdctl save/load` |
| Save / load                   | `podman save --format oci-archive -o app.tar app:dev`; `podman load -i app.tar` | `docker save/load`             | `nerdctl save/load`              |
| Login                         | `podman login reg` (auth in `$XDG_RUNTIME_DIR/containers/auth.json`) | `docker login reg`                   | `nerdctl login reg`              |
| Sign / verify                 | `podman push --sign-by-sigstore-private-key key reg/app:t`; policy in `/etc/containers/policy.json` | `cosign sign reg/app@sha256:...` | `nerdctl push --sign=cosign` |
| Compose                       | `podman compose up -d --wait`; `podman compose config`           | `docker compose up -d --wait`            | `nerdctl compose up -d`          |
| Systemd service               | Quadlet `.container` + `systemctl --user daemon-reload`          | `restart: always` in compose             | —                                |
| Kubernetes YAML               | `podman kube generate ctr > pod.yaml`; `podman kube play pod.yaml` | —                                      | —                                |
| Prune                         | `podman system prune -a --volumes`                               | `docker system prune -a --volumes`       | `nerdctl system prune -a`        |
| Cleanup build leftovers       | `podman ps --all --external`; `buildah rm --all`                 | `docker builder prune`                   | `nerdctl builder prune`          |

Buildah-only: scripted image assembly without a Containerfile — `ctr=$(buildah from scratch); mnt=$(buildah mount $ctr); cp app $mnt/; buildah config --entrypoint '["/app"]' --user 65532 $ctr; buildah commit --rm $ctr app:dev`. Useful for distro-less images from package sets (`dnf --installroot=$mnt`).

## Debugging recipes

Build fails at a `RUN` step:

```bash
podman build --target <previous-stage> -t dbg .
podman run --rm -it --entrypoint /bin/sh dbg          # only if the stage has a shell
podman build --no-cache --log-level=debug . 2>&1 | tail -50
```

Container exits immediately:

```bash
podman run --rm app:dev; echo "exit=$?"
podman image inspect app:dev --format '{{.Config.Entrypoint}} {{.Config.Cmd}} {{.User}} {{.Config.WorkingDir}}'
podman run --rm --entrypoint /app app:dev --help      # confirm the binary runs
podman logs <ctr>; podman inspect <ctr> --format '{{.State.ExitCode}} {{.State.Error}}'
```

Permission denied on volume: SELinux (`:Z`), UID mismatch (`--userns=keep-id` or `chown` on host), or `read_only` without tmpfs. Check `podman inspect <ctr> --format '{{.ProcessLabel}} {{.MountLabel}}'` and `ls -Z`.

Image too big:

```bash
podman image tree app:dev
podman history --no-trunc --format '{{.Size}}\t{{.CreatedBy}}' app:dev | sort -h | tail
podman run --rm --entrypoint /bin/sh app:dev -c 'du -xsh /* 2>/dev/null | sort -h'   # if shell present
```

Look for: package caches in a layer, `COPY . .` including `.git`/`node_modules`, build toolchain in final stage, separate `RUN chmod/chown` duplicating files (fix with `COPY --chmod/--chown`).

Healthcheck failing: `container ... has no defined healthcheck` (exit 125) means the image was built in OCI format, which has no healthcheck field: rebuild with `podman build --format docker` or set it at run time (`--health-cmd`, compose `healthcheck:`, Quadlet `HealthCmd=`). Otherwise `podman healthcheck run <ctr>; echo $?`, `podman inspect <ctr> --format '{{json .State.Health}}' | jq`. Verify the command exists in the image (`podman run --rm --entrypoint ls app:dev /usr/bin/wget`).

Cache misses: reorder so lockfile copy precedes source copy; ensure `.containerignore` excludes files that change every build; use `--mount=type=cache`; check `podman build` output for `--> Using cache`.

Rootless networking: `podman info --format '{{.Host.NetworkBackend}}'` (netavark/pasta). Ports < 1024 need `net.ipv4.ip_unprivileged_port_start`. Container-to-host: `host.containers.internal`.

Short-name resolution error (`short-name "x" did not resolve to an alias`): use a fully qualified name in `FROM`/`image:`.

## Multi-arch workflow

```bash
sudo dnf install qemu-user-static   # or apt install qemu-user-static binfmt-support; only for RUN emulation
podman manifest rm reg/app:1.4.2 2>/dev/null || true
podman build --platform linux/amd64,linux/arm64 --manifest reg/app:1.4.2 .
podman manifest inspect reg/app:1.4.2 | jq '.manifests[].platform'
podman manifest push --all reg/app:1.4.2 docker://reg/app:1.4.2
skopeo inspect --raw docker://reg/app:1.4.2 | jq '.manifests[].platform'
```

Prefer cross-compilation (`FROM --platform=$BUILDPLATFORM ... AS build` + `ARG TARGETARCH`) so only the final `COPY` differs per platform and no emulation runs.

## Registry promotion

```bash
digest=$(skopeo inspect --format '{{.Digest}}' docker://reg/app:1.4.2)
skopeo copy --all --preserve-digests docker://reg/app@${digest} docker://prod-reg/app:1.4.2
skopeo copy --all docker://prod-reg/app:1.4.2 docker://prod-reg/app:stable
```

Promote by digest; retag on the destination. Never rebuild for promotion.
