---
description: Behavioral rules for Docker/infrastructure operations — dry-run first, verify after, staging before production
globs:
  - "**/*"
---

# Operations — Infrastructure Behavioral Rules

When working with Docker stacks, Caddy, or any infrastructure component, follow these rules
automatically. These complement the conventions in `homelab-services.md` with enforceable behavior.

## Docker stack operations

**Before any `docker compose up` or config change:**
1. Run `docker compose ps` to check current running state
2. Run `docker compose -f stacks/<name>.yml --env-file .env config` to validate the compose file
3. Only proceed if config validates cleanly

**Always pass `--env-file .env`:**
```bash
docker compose -f stacks/<name>.yml --env-file .env up -d
```
Never omit `--env-file .env` — variables silently blank otherwise.

**After any `docker compose up` or restart:**
- Check logs: `docker logs <container> --tail 50`
- Confirm the container is running: `docker compose ps`
- Do not declare success until logs show no errors

## Caddy / reverse proxy changes

After any Caddyfile edit:
1. Validate config: `docker exec caddy caddy validate --config /etc/caddy/Caddyfile`
2. Reload: `docker exec caddy caddy reload --config /etc/caddy/Caddyfile`
3. Verify internal connectivity: `docker exec caddy wget -qO- http://<container>:<port>/`
4. Only declare success after the internal connectivity check passes

## Staging-first principle

For any non-trivial production change:
1. Apply the change to the staging replica (`*-staging`) first
2. Verify the staging service works as expected
3. Then apply to production

Skip staging-first only for: emergency fixes, changes with no staging equivalent, or when the
user explicitly says to skip.

## Production safety

- Never run `docker rm`, `docker stop`, or `docker volume rm` on production containers without
  explicit confirmation from the user — the `docker-safety-check.sh` hook enforces this
- Never force-recreate a production container if you haven't verified the image builds cleanly first
- If a container fails to start after an update, check logs before attempting fixes — don't
  blindly retry

## Networking changes

- New services behind Caddy must bind to `0.0.0.0` (not `127.0.0.1`)
- Debug 502s with `docker exec caddy wget -qO- http://<svc>:<port>/` before changing config
- Docker network names: `homelab-frontend`, `homelab-backend`, `homelab-data`, `homelab-monitoring`
- Confirm a service is on the correct network before declaring a routing issue fixed
