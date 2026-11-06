# Compose and Quadlet templates

The named PostgreSQL/Adminer images below illustrate application interfaces, not
allowlist approval. Check their build recipes/provenance against the base-image
allowlist in SKILL.md before selecting them. If their bases are unlisted or unknown,
report that gap and use a verified project-built equivalent when implementing the
stack. Preserve entrypoints, users, data paths, and initialization contracts when
rebuilding; replacing an application with a bare allowed base is not sufficient.

Illustrative Compose/Quadlet patterns; resolve image placeholders and validate with the installed provider. `podman compose` delegates to another tool: confirm support for `--wait`, `watch`, and newer Compose fields before use. These snippets are not evidence of a tested deployment.

## Hardened app + PostgreSQL

`compose.yaml`:

```yaml
name: myapp

x-hardening: &hardening
  read_only: true
  cap_drop: [ALL]
  security_opt:
    - no-new-privileges:true
  pids_limit: 256
  tmpfs:
    - /tmp

services:
  app:
    <<: *hardening
    image: registry.example.com/org/app:${APP_TAG:-dev}
    build:
      context: .
      target: runtime
      args:
        VERSION: ${APP_TAG:-dev}
    pull_policy: build
    user: "65532:65532"
    init: false
    environment:
      DATABASE_URL_FILE: /run/secrets/database_url
      LOG_LEVEL: ${LOG_LEVEL:-info}
    secrets:
      - database_url
    ports:
      - "127.0.0.1:8080:8080"
    networks:
      - front
      - back
    depends_on:
      db:
        condition: service_healthy
        restart: true
      migrate:
        condition: service_completed_successfully
    healthcheck:
      test: ["CMD", "/app", "healthz"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 10s
      start_interval: 2s
    mem_limit: 512m
    cpus: 1.0
    restart: unless-stopped

  migrate:
    <<: *hardening
    image: registry.example.com/org/app:${APP_TAG:-dev}
    user: "65532:65532"
    command: ["migrate"] # assumes ENTRYPOINT ["/app"]
    environment:
      DATABASE_URL_FILE: /run/secrets/database_url
    secrets:
      - database_url
    networks: [back]
    depends_on:
      db:
        condition: service_healthy
    restart: "no"

  db:
    image: docker.io/library/postgres:16-alpine@sha256:<digest>
    # Keep the image entrypoint's initialization user for a new volume.
    cap_drop: [ALL]
    cap_add: [CHOWN, DAC_OVERRIDE, FOWNER, SETGID, SETUID]
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
      - /run/postgresql
    environment:
      POSTGRES_DB: app
      POSTGRES_USER: app
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password
    volumes:
      - db-data:/var/lib/postgresql/data
    networks: [back]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d app"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 15s
    shm_size: 128m
    restart: unless-stopped

networks:
  front: {}
  back:
    internal: true

volumes:
  db-data: {}

secrets:
  db_password:
    file: ./secrets/db_password
  database_url:
    file: ./secrets/database_url
```

Notes: resolve image placeholders first. Build the app image before starting the migration service; it must share the resulting tag. Confirm DATABASE_URL_FILE is implemented by the app. Ports bind to loopback and the database's internal network has no egress. Keep secret files untracked. For fresh Postgres volumes, test entrypoint initialization and ownership before forcing a non-root user; for preinitialized volumes, use the verified UID and reduce capabilities accordingly.

## Dev override

`compose.override.yaml` (merged automatically by `up`; use `-f compose.yaml -f compose.prod.yaml` to skip it):

```yaml
services:
  app:
    build:
      target: dev
    read_only: false
    ports:
      - "8080:8080"
      - "9229:9229"
    environment:
      LOG_LEVEL: debug
    develop:
      watch:
        - action: sync
          path: ./src
          target: /app/src
        - action: rebuild
          path: package.json
    entrypoint: [] # clear a production /app entrypoint for this Node-specific dev stage
    command: ["npm", "run", "dev"]

  db:
    ports:
      - "127.0.0.1:5432:5432"

  adminer:
    image: docker.io/library/adminer:4@sha256:<digest>
    profiles: [debug]
    ports:
      - "127.0.0.1:8081:8080"
    networks: [back, front]
```

Run: `podman compose up --watch`, `podman compose --profile debug up -d adminer`.

## Splitting large stacks

```yaml
name: platform
include:
  - path: ./services/api/compose.yaml
    project_directory: ./services/api
    env_file: ./services/api/.env
  - ./services/worker/compose.yaml
```

Shared service fragments via `extends`:

```yaml
services:
  worker:
    extends:
      file: common.yaml
      service: python-base
    command: ["python", "-m", "worker"]
```

## Rootless podman notes

- Prefer high host ports for rootless services; changing the host's privileged-port policy is a separate administrative decision.
- Bind mounts owned by the host user: `userns_mode: keep-id` is Podman-specific and must not be assumed valid or silently ignored by Docker.
- SELinux: `volumes: ["./conf:/etc/app:ro,Z"]` or long syntax `bind: { selinux: Z }`.
- Pods: `podman compose` maps each service to a container on a shared network; for a true pod use `podman kube play` or Quadlet `.pod`.

## Quadlet equivalent (systemd-managed, single host)

`~/.config/containers/systemd/myapp.network`:

```ini
[Network]
NetworkName=myapp
Internal=false
```

`~/.config/containers/systemd/myapp-db.volume`:

```ini
[Volume]
VolumeName=myapp-db
```

`~/.config/containers/systemd/myapp-db.container`:

```ini
[Unit]
Description=myapp PostgreSQL

[Container]
Image=docker.io/library/postgres:16-alpine
ContainerName=myapp-db
Network=myapp.network
Volume=myapp-db.volume:/var/lib/postgresql/data:Z
Secret=myapp-db-password,type=env,target=POSTGRES_PASSWORD
Environment=POSTGRES_DB=app
Environment=POSTGRES_USER=app
HealthCmd=pg_isready -U app -d app
HealthInterval=10s
HealthStartPeriod=15s
HealthOnFailure=kill
Notify=healthy
ReadOnly=true
Tmpfs=/tmp
Tmpfs=/run/postgresql
NoNewPrivileges=true
DropCapability=ALL
AddCapability=CHOWN DAC_OVERRIDE FOWNER SETGID SETUID
AutoUpdate=registry

[Service]
Restart=on-failure
TimeoutStartSec=300

[Install]
WantedBy=default.target
```

`~/.config/containers/systemd/myapp.container`:

```ini
[Unit]
Description=myapp
Requires=myapp-db.service
After=myapp-db.service

[Container]
Image=registry.example.com/org/app:1.4.2
ContainerName=myapp
Network=myapp.network
PublishPort=127.0.0.1:8080:8080
User=65532
Group=65532
ReadOnly=true
Tmpfs=/tmp
NoNewPrivileges=true
DropCapability=ALL
PidsLimit=256
Secret=myapp-database-url,type=mount,target=/run/secrets/database_url
Environment=DATABASE_URL_FILE=/run/secrets/database_url
HealthCmd=/app healthz
HealthInterval=30s
HealthOnFailure=kill
Notify=healthy
AutoUpdate=registry

[Service]
Restart=on-failure
MemoryMax=512M

[Install]
WantedBy=default.target
```

Create secrets once: `printf '%s' "$PW" | podman secret create myapp-db-password -`. Then run `systemctl --user daemon-reload` and `systemctl --user start myapp.service`. Generated Quadlet services are transient; their boot activation comes from the source file's [Install] section rather than enabling the generated service. Enable unattended updates only if requested. Debug generation with the installed podman-system-generator's `--user --dryrun` options.

Rootless units require `loginctl enable-linger $USER` to run without an active session.
