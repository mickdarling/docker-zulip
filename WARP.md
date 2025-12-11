# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is the **docker-zulip** repository, which provides the official Docker container image for running a [Zulip server](https://zulip.com) in production. The project uses a multi-stage Docker build process to create production-ready images.

**Current versions:**
- Zulip: 11.4
- Docker image: 11.4-0
- PostgreSQL: 14

## Architecture

### Container Stack

The application consists of 5 main containers orchestrated via Docker Compose:

1. **zulip** - Main application server (Ubuntu 24.04-based)
   - Runs Nginx, Django application server, queue workers
   - Exposed ports: 25 (email), 80 (HTTP), 443 (HTTPS)
   
2. **database** - PostgreSQL 14 with Zulip extensions
   - Uses `zulip/zulip-postgresql:14` image
   
3. **rabbitmq** - RabbitMQ 4.1 for async task queue
   
4. **redis** - Redis for caching and rate limiting
   
5. **memcached** - Memcached for session/cache storage with SASL authentication

### Build Process

The Dockerfile implements a 2-stage build:

**Stage 1 (build):** 
- Clones Zulip from Git at specified ref (default: 11.4)
- Provisions development environment
- Runs `tools/build-release-tarball` to create production tarball

**Stage 2 (production):**
- Starts from clean Ubuntu base
- Installs production tarball
- Copies custom files from `custom_zulip_files/` (overlay mechanism)
- Runs Zulip installer with Docker-specific puppet classes

### Configuration System

The `entrypoint.sh` script dynamically generates Zulip configuration files (`settings.py` and `zulip-secrets.conf`) from environment variables in `docker-compose.yml`:

- `SETTING_*` variables → `/etc/zulip/settings.py`
- `SECRETS_*` variables → `/etc/zulip/zulip-secrets.conf`
- Direct environment variables configure Docker-specific behavior

For manual configuration, set `MANUAL_CONFIGURATION: "True"` and `LINK_SETTINGS_TO_DATA: "True"` to provide your own config files.

### Data Persistence

Uses Docker managed volumes (as of version 6.0-0):
- `zulip` - Uploaded files, backups, certs
- `postgresql-14` - Database data
- `rabbitmq` - RabbitMQ data
- `redis` - Redis data

All persistent data is mounted under `/data` in the zulip container.

## Common Commands

### Starting and Stopping

```bash
# Pull latest images and start all containers
docker compose pull
docker compose up

# Start in background (detached mode)
docker compose up -d

# Stop all containers
docker compose stop

# View running containers
docker compose ps

# View logs
docker compose logs -f zulip
```

### Building

```bash
# Build custom image from local changes
docker compose build

# Build from specific Git ref (edit docker-compose.yml first)
docker compose build zulip
```

### Management Commands

```bash
# Get a root shell in the zulip container
docker compose exec zulip bash

# Run Zulip management commands as zulip user
docker compose exec -u zulip zulip \
    /home/zulip/deployments/current/manage.py <command>

# Examples:
docker compose exec -u zulip zulip \
    /home/zulip/deployments/current/manage.py list_realms

docker compose exec -u zulip zulip \
    /home/zulip/deployments/current/manage.py generate_realm_creation_link
```

### Upgrading

```bash
# Standard upgrade process
docker pull zulip/docker-zulip:<new-version>
# Update image version in docker-compose.yml
docker compose stop
docker compose up
docker compose rm  # Clean up old containers
```

For PostgreSQL major version upgrades, use the included helper:
```bash
./upgrade-postgresql
```

### Testing Custom Changes

To test modifications before submitting to upstream:

1. Place modified files in `custom_zulip_files/` matching the path structure from zulip/zulip
2. Run `docker compose build` - files will be overlaid during build
3. Test with `docker compose up`

Example: To modify `scripts/setup/generate-self-signed-cert`, place it at:
```
custom_zulip_files/scripts/setup/generate-self-signed-cert
```

## Development Workflow

### Linting and Testing

```bash
# Shellcheck (via CircleCI orb)
shellcheck entrypoint.sh certbot-deploy-hook upgrade-postgresql

# Hadolint (Dockerfile linting) 
hadolint Dockerfile

# Prettier (markdown formatting)
prettier --write **/*.md

# Helm chart testing
ct lint --chart-dirs kubernetes/chart --target-branch main --lint-conf lintconf.yaml
```

### CI/CD Pipeline

The project uses GitHub Actions with the following workflows:
- **dockerfile.yaml** - Hadolint, build, push to GHCR, Helm testing in Kind
- **prettier.yaml** - Markdown formatting validation
- **shell-test.yaml** - Shell script validation
- **spelling.yaml** - Spell checking

Pull requests trigger:
1. Dockerfile linting with hadolint
2. Docker build and push to `ghcr.io/<repo>:pr-<number>`
3. Helm chart docs generation and validation
4. Helm chart installation test in Kind cluster

## Key Files and Their Purposes

- **entrypoint.sh** - Container initialization script; generates config, handles migrations, sets up services
- **docker-compose.yml** - Service orchestration and configuration
- **Dockerfile** - 2-stage build definition
- **upgrade-postgresql** - Helper script for PostgreSQL major version migrations
- **certbot-deploy-hook** - Let's Encrypt certificate renewal hook
- **custom_zulip_files/** - Overlay directory for testing upstream changes
- **kubernetes/manual/** - Manual Kubernetes deployment YAMLs
- **kubernetes/chart/zulip/** - Helm chart for Kubernetes deployment

## Configuration Notes

### Required Settings

For production, these environment variables must be configured in `docker-compose.yml`:
- `SETTING_EXTERNAL_HOST` - Domain users will access
- `SETTING_ZULIP_ADMINISTRATOR` - Admin email for system notifications
- All `POSTGRES_PASSWORD` / `SECRETS_postgres_password` pairs
- All `RABBITMQ_DEFAULT_PASS` / `SECRETS_rabbitmq_password` pairs  
- All `MEMCACHED_PASSWORD` / `SECRETS_memcached_password` pairs
- All `REDIS_PASSWORD` / `SECRETS_redis_password` pairs
- `SECRETS_secret_key` - 50+ character random string (critical - never change in production)
- Email configuration: `SETTING_EMAIL_*` variables

### Reverse Proxy Support

When behind a load balancer/reverse proxy:
- Set `LOADBALANCER_IPS` to comma-separated list of proxy IPs/CIDRs
- Proxy must provide `X-Forwarded-For` and `X-Forwarded-Proto` headers
- For HTTP-only (with SSL termination at proxy): `DISABLE_HTTPS: "True"`

### SSL Certificates

Three options:
1. Self-signed (default): `SSL_CERTIFICATE_GENERATION: "self-signed"`
2. Let's Encrypt: `SSL_CERTIFICATE_GENERATION: "certbot"`
3. Custom: Place certs in `/opt/docker/zulip/zulip/certs/`

## Important Patterns

### Secret Management
- Secrets are synced to container on every boot
- Database/RabbitMQ passwords only read on first container creation
- To change database password after first boot: run `ALTER ROLE` in PostgreSQL OR rebuild database

### Volume Management
- Since version 6.0-0, uses Docker managed volumes (not host paths)
- Migration from host paths requires copying data into managed volumes
- Always backup volumes before upgrades

### Queue Workers
- Auto-detects available memory to choose multiprocess vs multithreaded mode
- Override with `QUEUE_WORKERS_MULTIPROCESS: "true"/"false"`
- Multithreaded saves ~1.5GB RAM

### Boolean Normalization
`entrypoint.sh` accepts flexible boolean values for env vars:
- True: `true`, `enable`, `enabled`, `yes`, `y`, `1`, `on`
- False: `false`, `disable`, `disabled`, `no`, `n`, `0`, `off`

## Troubleshooting

Common issues:
1. Container fails to start - Check `docker compose logs zulip` for configuration errors
2. New Zulip settings not working - May need to add to `entrypoint.sh`, or use `ZULIP_CUSTOM_SETTINGS`
3. PostgreSQL connection issues - Ensure `SECRETS_postgres_password` matches `POSTGRES_PASSWORD`
4. Email not working - Verify all `SETTING_EMAIL_*` variables are correct

## Kubernetes Deployment

Two options:
1. **Manual**: Use `kubernetes/manual/zulip-rc.yml` and `zulip-svc.yml`
2. **Helm**: Use chart at `kubernetes/chart/zulip/`

For Helm installation:
```bash
helm repo add groundhog2k https://groundhog2k.github.io/helm-charts/
helm install zulip ./kubernetes/chart/zulip
```

## Project Links

- Main Zulip docs: https://zulip.readthedocs.io/
- Docker Hub: https://hub.docker.com/r/zulip/docker-zulip
- Community support: https://chat.zulip.org/#narrow/stream/31-production-help
- Upstream Zulip repo: https://github.com/zulip/zulip
