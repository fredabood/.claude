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

## NAS mount dependencies

The NAS at `/Volumes/Personal-Drive` is an SMB share that does NOT auto-mount after reboot.
Several stacks have bind mounts to NAS paths — these are **commented out by default** to prevent
containers from failing when the NAS isn't mounted.

**Before any `docker compose up` on a stack with NAS mounts:**
1. Check if NAS is mounted: `mount | grep Personal-Drive`
2. If not mounted and the stack needs NAS data: run `./internal/scripts/mount-unas.sh` first
3. Uncomment the NAS mount lines in the stack file before recreating
4. After container starts, verify NAS data is accessible inside: `docker exec <container> ls <mount-path>`

**Stacks with NAS mount dependencies:**
| Stack | Service | NAS path | Purpose |
|-------|---------|----------|---------|
| `nextcloud-stack.yml` | nextcloud, nextcloud-cron | `/Volumes/Personal-Drive/homelab/google-drive` | Google Drive mirror |
| `privacy-stack.yml` | calibre-web | `$CALIBRE_LIBRARY_PATH`, `$GUTENBERG_MIRROR_PATH` | Book library |
| `data-platform-stack.yml` | n8n | `/Volumes/Personal-Drive/homelab/google-drive` | NAS access for workflows |
| `wikipedia-stack.yml` | kiwix, eventstreams-daemon | `/Volumes/Personal-Drive/homelab/wikipedia` | Wikipedia data |

**CRITICAL: Never add NAS bind mounts while rclone is actively writing to the same NAS path.**
Docker Desktop crashes when containers have NAS SMB bind mounts during active writes (FUSE/gRPC
bridge overwhelmed). Sequence: finish rclone writes → mount NAS → add container mounts.

## Networking changes

- New services behind Caddy must bind to `0.0.0.0` (not `127.0.0.1`)
- Debug 502s with `docker exec caddy wget -qO- http://<svc>:<port>/` before changing config
- Docker network names: `homelab-frontend`, `homelab-backend`, `homelab-data`, `homelab-monitoring`
- Confirm a service is on the correct network before declaring a routing issue fixed

## Compose env-var strictness (LAB-965)

Every `${VAR}` reference in `stacks/*.yml` must carry an explicit posture:

- `${VAR:?VAR required}` — credentials, tokens, DSN components, webhook URLs, and
  environment-specific paths/hosts (`HOMELAB_DATA_PATH`, `HOMELAB_REPO_PATH`, …).
  Compose FAILS LOUDLY instead of silently interpolating an empty string.
- `${VAR:-<default>}` — genuinely optional vars with a safe default; use `${VAR:-}`
  + `# optional` comment for integrations that may be unset (e.g. DATABRICKS_*).
- Non-colon `${VAR?msg}` — rare: var must EXIST but may legitimately be empty
  (e.g. ANTHROPIC_API_KEY placeholder).

Verification pattern for any change: `docker compose -f <stack> --env-file .env config`
must exit 0 AND diff empty against the pre-change resolved config; a probe with
`--env-file /dev/null` must fail naming a required variable. Note: compose prints
"variable is not set" warnings from `.env`-internal interpolation even when resolution
succeeds — trust the resolved config, not warning absence.

**Every `:?`-required var must also exist in `.env.tpl`** (op:// ref or non-secret
literal). `inject-secrets.sh` regenerates `.env` wholesale with `--force`, so a var
present only in the live `.env` (or surviving only in a running container's env) is a
redeploy time bomb — LAB-1124 found `JIRA_GRAPH_WRITE_ALLOWED`/`JIRA_GRAPH_SERVICE_TOKEN`
this way. After adding a required var to a stack, add it to `.env.tpl` in the same change
and verify with a fresh inject + `compose config`.
