---
globs:
  - "**/*"
---

# Homelab Services Reference

Canonical reference for all deployed homelab services. Loaded in every session.
Source of truth for service names, URLs, and ports: `internal/caddy/Caddyfile` and `stacks/`.

---

## Service Catalog

### Production Services (in Caddyfile)

| Service | Container | External URL | Internal host:port | Purpose | Primary access pattern |
|---|---|---|---|---|---|
| Homepage | homepage | home.dirtydata.studio | homepage:3000 | Service dashboard | Web UI |
| Portainer | portainer | portainer.dirtydata.studio | portainer:9000 | Docker management | Web UI + REST API |
| Uptime Kuma | uptime-kuma | status.dirtydata.studio | uptime-kuma:3001 | Uptime monitoring | Web UI + REST API |
| Open-WebUI | open-webui | chat.dirtydata.studio | open-webui:8080 | Chat UI for Ollama | Web UI |
| Ollama | ollama | ollama.dirtydata.studio | ollama:11434 | Local LLM inference | REST `/api/generate`, `/api/chat` |
| Code-Server | code-server | code.dirtydata.studio | code-server:8080 | Browser VSCode | Web UI |
| Grafana | grafana | grafana.dirtydata.studio | grafana:3000 | Metrics dashboards | Web UI; HTTP API `/api/` |
| MLflow | mlflow | mlflow.dirtydata.studio | mlflow:5000 | ML experiment tracking | REST API + web UI |
| n8n | n8n | n8n.dirtydata.studio | n8n:5678 | Workflow automation | REST `/api/v1/` + web UI |
| Jellyfin | jellyfin | jellyfin.dirtydata.studio | jellyfin:8096 | Media server | REST API |
| Sonarr | sonarr | sonarr.dirtydata.studio | sonarr:8989 | TV show management | REST API v3 |
| Radarr | radarr | radarr.dirtydata.studio | radarr:7878 | Movie management | REST API v3 |
| Prowlarr | prowlarr | prowlarr.dirtydata.studio | prowlarr:9696 | Indexer management | REST API v1 |
| Mealie | mealie | mealie.dirtydata.studio | mealie:9000 | Recipe manager | REST API |
| Home Assistant | homeassistant | hass.dirtydata.studio | homeassistant:8123 | Home automation | REST API + long-lived tokens |
| Homebridge | homebridge | homebridge.dirtydata.studio | homebridge:8581 | HomeKit bridge | Web UI |
| Twenty CRM | twenty-server | crm.dirtydata.studio | twenty-server:3000 | Self-hosted CRM | Web UI + REST API |
| Jira-Graph | jira-graph | jira.dirtydata.studio | jira-graph:8090 | Dependency visualization (Jira-backed) | FastAPI REST `/api/graph` |
| SearXNG | searxng | search.dirtydata.studio | searxng:8080 | Private search | REST `/search?q=` |
| FreshRSS | freshrss | rss.dirtydata.studio | freshrss:80 | RSS reader | Web UI + Fever API |
| Calibre-Web | calibre-web | books.dirtydata.studio | calibre-web:8083 | Ebook library | Web UI |
| Radicale | radicale | dav.dirtydata.studio | radicale:5232 | CalDAV/CardDAV | CalDAV protocol |
| Immich | immich-server | photos.dirtydata.studio | immich-server:2283 | Photo management | REST API |
| Nextcloud | nextcloud | cloud.dirtydata.studio | nextcloud:80 | File storage | WebDAV + REST |
| MCP Gateway | mcp-uptime-kuma-http | mcp.dirtydata.studio | mcp-uptime-kuma-http:3100 | MCP server for Claude.ai | Streamable HTTP `/mcp` |

### Infrastructure Services (internal only / not in production Caddyfile)

| Service | Container | External URL | Internal host:port | Purpose | Primary access pattern |
|---|---|---|---|---|---|
| Prometheus | prometheus | (internal only) | prometheus:9090 | Metrics scraping | HTTP API `/api/v1/query` |
| Alertmanager | alertmanager | (internal only) | alertmanager:9093 | Alert routing | HTTP API |
| postgres-memory | postgres-memory | host: localhost:5432 | postgres-memory:5432 | Agent memory + Jira data | asyncpg / psql |
| MinIO | minio | (staging only) | minio:9000 (S3), minio:9001 (console) | Object storage | AWS S3 API; bucket `jira-activity` |
| qBittorrent | qbittorrent | host: localhost:8081 | gluetun:8080 | Torrent client (VPN via gluetun) | Web API `/api/v2/` |
| Claude Remote | claude-remote | claude.ai/code (no direct port) | outbound HTTPS only | Claude Code Remote Control server | claude.ai/code + Claude mobile app |

### API Gateway (`api.dirtydata.studio`)

| Path prefix | Strips prefix | Routes to |
|---|---|---|
| `/ollama/*` | yes | ollama:11434 |
| `/mlflow/*` | yes | mlflow:5000 |

The staging API gateway (`staging-api.dirtydata.studio`) additionally routes `/s3/*`.

---

## MCP Server Capabilities

| Server | What it can do | Key use cases |
|---|---|---|
| atlassian | Create/edit/transition Jira issues, add comments, create issue links, search via JQL | All Jira ops — project `LAB` at fredabood.atlassian.net |
| slack | Send/read messages, search channels, create/update canvases | Notifications, async comms, status updates |
| obsidian | Read/write/search vault notes | Knowledge base at `submodules/memory/` |
| google-workspace | Gmail, Calendar, Contacts | Email, scheduling |
| postgres-cos | Read-only SQL on `agent_memory` DB | Query `jira.*` schema, inspect data |

---

## Data Store Schemas

### postgres-memory (`agent_memory` database)

- **`jira` schema:** `issues`, `issue_links`, `sprints`, `status_transitions`, `sync_metadata`, `activity_log`, `issue_changelog` — active, used by jira-graph
- **`plane` schema:** (archived) mirror of jira schema from Plane CE experiment — 30-day retention then drop
- **`public` schema:** pgvector tables for embeddings, `migration_key_map` (Jira↔Plane ID mapping), `plane_to_jira_key_map` (reverse migration mapping)
- **Connection (from host):** `postgresql://postgres@localhost:5432/agent_memory`
- **Connection (from container):** `postgresql://postgres@postgres-memory:5432/agent_memory`
- **MCP postgres-cos is read-only.** For writes: `docker exec postgres-memory psql -U postgres -d agent_memory`

### MinIO (S3-compatible)

- **S3 API:** `minio:9000` (internal) — AWS S3 SDK compatible
- **Console:** `minio:9001` (internal)
- **Known buckets:** `jira-activity` (legacy n8n sync payloads)
- **Client:** use `mc` (MinIO client) inside containers, or AWS SDK with `endpoint_url=http://minio:9000`

### n8n

- **SQLite DB:** `/home/node/.n8n/database.sqlite` inside the `n8n` container — use REST API instead
- **REST API:** `n8n:5678/api/v1/` — use for reading/writing workflows
- **Known workflow IDs:** full-sync `0NyujISFScfFNexz`, webhook-receiver `KTTljDaHkVbEMfUI`

---

## Docker / Infrastructure Conventions

### Stack files

- All stacks are in `stacks/` — always run with `--env-file .env` (vars silently blank otherwise):
  ```bash
  docker compose -f stacks/<name>.yml --env-file .env up -d
  ```
- Stack files by category:
  - `core-stack.yml` — MinIO, core services
  - `llm-stack.yml` — Ollama, Open-WebUI
  - `monitoring-stack.yml` — Prometheus, Alertmanager, Grafana, Loki
  - `memory-stack.yml` — postgres-memory
  - `data-platform-stack.yml` — MLflow, n8n, qBittorrent (via gluetun)
  - `media-stack.yml` — Jellyfin, Sonarr, Radarr, Prowlarr, Mealie
  - `crm-stack.yml` — Twenty CRM
  - `jira-graph-stack.yml` — jira-graph (dependency visualization, reads from jira.* schema)
  - `smarthome-stack.yml` — Home Assistant, Homebridge
  - `privacy-stack.yml` — SearXNG, FreshRSS, Calibre-Web, Radicale
  - `immich-stack.yml` — Immich
  - `nextcloud-stack.yml` — Nextcloud
  - `dev-tools-stack.yml` — Code-Server
  - `claude-remote-stack.yml` — Claude Code web terminal (Tailscale-only)
  - `mcp-stack.yml` — MCP servers
  - `staging-stack.yml` — all staging replicas

### Restart vs rebuild

- `docker restart <container>` — soft restart, same image, picks up env var changes
- `docker compose -f stacks/<name>.yml --env-file .env up --force-recreate <service>` — picks up rebuilt image

### Networking

- Services behind Caddy **must bind to `0.0.0.0`** (not 127.0.0.1)
- Debug 502s: `docker exec caddy wget -qO- http://<container>:<port>/` to verify internal connectivity
- Docker network names: `homelab-frontend`, `homelab-backend`, `homelab-data`, `homelab-monitoring`
- Container name == service name in Caddyfile (e.g. `n8n` container ↔ `n8n:5678` in Caddyfile)

### Staging mirrors

Every production service has a staging mirror at `staging-<name>.dirtydata.studio` with basicauth.
Staging containers are named `<service>-staging` (e.g. `n8n-staging`, `ollama-staging`).

### Safety

- `docker stop/rm/rmi/kill` on production containers is intercepted by the `.claude/hooks/docker-safety-check.sh` safety hook
- Never use `docker rm` on production containers without explicit confirmation
- Staging containers (`*-staging`) can be manipulated freely
