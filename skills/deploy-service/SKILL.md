---
name: deploy-service
user_invocable: true
description: Guided workflow for deploying a new service to the homelab — generates stack YAML, Caddyfile entry, and env vars
---

# /deploy-service

Guided workflow for adding a new service to the homelab. Generates the stack file, Caddyfile entry, and env var placeholders, then deploys and verifies.

## Usage

```
/deploy-service                        → interactive: asks for all details
/deploy-service <name>                 → prompts for remaining details
/deploy-service <name> --dry-run       → generate files but don't deploy
```

## Steps

### Step 1: Collect inputs

Ask the user for (or accept as arguments):

| Input | Example | Notes |
|---|---|---|
| Service name | `twenty` | lowercase, used as container name and Caddy matcher |
| Docker image | `twentyhq/twenty:latest` | include tag |
| Internal port | `3000` | port the container listens on |
| Subdomain | `crm` | results in `crm.dirtydata.studio` |
| Stack category | `dev-tools` | which stack file to add to, or `new` to create one |
| Networks | `homelab-backend` | comma-separated; `homelab-frontend` if Caddy-accessible |
| Env vars needed | `TWENTY_PG_URL, SECRET_KEY` | vars to add to `.env` |
| Memory limit | `512m` | container memory limit |
| Data directory | `/data` | path inside container for volume mount |

### Step 2: Check for conflicts

- Verify no existing container is named `<service-name>` in any stack file
- Verify `<subdomain>.dirtydata.studio` is not already in the Caddyfile
- If conflict found: report it and stop

### Step 3: Generate stack YAML snippet

```yaml
  <name>:
    image: <image>
    container_name: <name>
    restart: unless-stopped
    mem_limit: <mem_limit>
    networks:
      - <network>
    volumes:
      - <name>_data:<data_dir>
    environment:
      - KEY=${KEY}

volumes:
  <name>_data:
```

If adding to an existing stack file, show the user where to insert this snippet. If creating a new stack file, generate the full file with the `networks:` section at the bottom.

### Step 4: Generate Caddyfile entry

Production block:
```caddy
    # <Name>
    @<name> host <subdomain>.dirtydata.studio
    handle @<name> {
        reverse_proxy <name>:<port>
    }
```

Staging block (add to `staging-*.dirtydata.studio:80`):
```caddy
    # <Name> - staging
    @<name> host staging-<subdomain>.dirtydata.studio
    handle @<name> {
        basicauth {
            admin $2a$14$.miEhVq37ZQSwhe5KgDLk.CdzKyNNueb0gH3jZ0OwcrvdmX3biU4K
        }
        reverse_proxy <name>-staging:<port>
    }
```

### Step 5: Show env var placeholders

List any env vars that need to be added to `.env`:
```
# <Service name>
<VAR_1>=
<VAR_2>=
```

Prompt the user: "Add these to `.env` before continuing, then press Enter."

### Step 6: Deploy (unless --dry-run)

```bash
# Apply the stack change
docker compose -f stacks/<stack>.yml --env-file .env up -d <name>

# Reload Caddy
docker exec caddy caddy reload --config /etc/caddy/Caddyfile

# Verify container is running
docker ps | grep <name>

# Verify internal connectivity
docker exec caddy wget -qO- http://<name>:<port>/ 2>&1 | head -5
```

### Step 7: Verify

- Container status: `docker ps | grep <name>`
- Caddy can reach it: `docker exec caddy wget -qO- http://<name>:<port>/`
- External URL responds: (inform user to check `http://<subdomain>.dirtydata.studio` from their browser)

### Step 8: Sync primitives

Run `/sync-homelab` to update `.claude/rules/homelab-services.md` with the new service.

### Step 9: Commit

```bash
git add internal/caddy/Caddyfile stacks/<stack>.yml
git commit -m "<TICKET>: Add <name> service"
```

Use the active Jira ticket key if one exists.

### Step 10: Report

```
/deploy-service complete
  Container: <name> (running)
  External URL: http://<subdomain>.dirtydata.studio
  Stack: stacks/<stack>.yml
  Caddy: reloaded
  homelab-services.md: updated
```

## Notes

- Always use `--env-file .env` — vars are silently blank otherwise
- The container must be on a network Caddy is on (`homelab-frontend` or `homelab-backend`)
- Memory limit is required — don't omit it; match other services in the same stack
- `docker restart caddy` is not needed after `caddy reload` — reload is non-disruptive
