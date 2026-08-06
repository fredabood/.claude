# Homepage Dashboard — Sync Convention

The homepage dashboard lives at `homelab-data/homepage/` and is the canonical entry point at
`dirtydata.studio`. **It must stay in sync with deployed services.** This rule defines when and
how to update it automatically.

## When to update the homepage

Update `services.yaml` (and `settings.yaml` if a new group is needed) **in the same commit** as
the service change whenever:

| Trigger | Action |
|---------|--------|
| New Caddy route added (`internal/caddy/Caddyfile`) | Add service entry to services.yaml |
| Caddy route removed | Remove service entry from services.yaml |
| Stack deprecated or service removed | Remove service entry from services.yaml |
| Subdomain/hostname changed | Update `href` in services.yaml |
| New stack file added with externally-routed services | Add entries; create new group if needed |

Never leave services.yaml out of sync with the Caddyfile. If a service has a Caddy route and a
non-deprecated stack file, it belongs on the homepage.

## What goes on the homepage

**Include** a service if:
- It has a Caddy `reverse_proxy` route in `internal/caddy/Caddyfile`
- Its stack file is not deprecated (not listed in `stacks/DEPRECATED_STACKS.md`)

**Do NOT include:**
- Internal-only services with no Caddy route (Prometheus, Alertmanager, Loki, databases, MCP servers)
- Deprecated stacks
- Health-check or API-gateway-only endpoints unless they have a meaningful UI

## Group assignments

| Group | Services | columns |
|-------|----------|---------|
| Management | Portainer, Uptime Kuma, Grafana (if routed) | 2–3 |
| AI Services | Open WebUI, Ollama | 2–3 |
| Development | Code Server, MLflow, n8n, Plane, Jira Graph | 3–4 |
| Storage | MinIO Console, S3 API | 2 |
| Media | Jellyfin, Sonarr, Radarr, Prowlarr, qBittorrent, Mealie | 5–6 |
| Privacy | Nextcloud, Immich, SearXNG, FreshRSS, Calibre-Web, Radicale | 3 |
| Smart Home | Home Assistant, Homebridge | 2 |

If a new service doesn't fit any existing group, **propose a new group to the user** before
adding it. Update `settings.yaml` layout section when adding a new group.

## Caddyfile ↔ homepage invariant

These two files must stay consistent:
- `internal/caddy/Caddyfile` — source of truth for what's externally accessible
- `homelab-data/homepage/services.yaml` — source of truth for what's shown on the dashboard

When modifying the Caddyfile, scan the diff for added/removed routes and update services.yaml
accordingly. When modifying a stack file, check whether any Caddy routes are affected.

**Documented deviation (LAB-1008):** the **Jira Graph** tile (Development) has NO Caddy route —
Tailscale-only at `https://freds-mac-mini.tailc05760.ts.net:8443` (via `tailscale serve`; the app
is a GitHub writer per #1001 S5 and must not be publicly reachable). Do not "fix" by re-adding a
Caddy route.

**Documented deviation (LAB-1018):** the **Omnigent** tile (AI Services) has NO Caddy route by
design — its `href` is the tailnet HTTPS hostname (`https://freds-mac-mini.tailc05760.ts.net`,
via `tailscale serve`), resolvable only from tailnet devices. Omnigent surfaces are
Tailscale-bound only (#1015 audit BLOCKER); do not "fix" this by adding a Caddy route.

## Icon convention

Use Simple Icons (`si-<name>`) where available — check simpleicons.org.
Fall back to Material Design Icons (`mdi-<name>`).

Common mappings:
| Service | Icon |
|---------|------|
| Portainer | `si-portainer` |
| Uptime Kuma | `si-uptimekuma` |
| Open WebUI | `si-openai` |
| Ollama | `si-ollama` |
| Grafana | `si-grafana` |
| Nextcloud | `si-nextcloud` |
| Immich | `mdi-image-multiple` |
| SearXNG | `si-searxng` |
| FreshRSS | `mdi-rss` |
| Calibre-Web | `mdi-bookshelf` |
| Radicale | `mdi-calendar-sync` |
| qBittorrent | `si-qbittorrent` |
| Jira Graph | `mdi-graph` |

## URL format

All `href` values must use `https://` — not `http://`.

## settings.yaml layout

When a new group is added, add a corresponding entry under `layout:` in `settings.yaml`:

```yaml
layout:
  NewGroupName:
    style: row
    columns: 3
```

## Commit convention

Homepage-only fixes:
```
LAB-XXX: Sync homepage with deployed services
```

Homepage update bundled with a service change:
```
LAB-XXX: Add <service> — include homepage entry
```
