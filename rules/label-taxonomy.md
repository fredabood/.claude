# Work Taxonomy — Label Classification

Every Jira ticket requires exactly one **work pattern** label and one **infrastructure layer** label.
These labels drive decomposition templates, agent routing, and dependency validation.

> Design rationale: `submodules/memory/homelab/decisions/work-taxonomy.md`

---

## Dimension 1: Work Pattern (REQUIRED — exactly one)

| Label | Description | Keyword hints |
|---|---|---|
| `scraper` | Data scraper or API connector — fetch external data into storage | scrape, crawl, fetch, ingest, connector, API client |
| `agent` | AI agent with tool-use — autonomous task execution | agent, AI, LLM, tool-use, autonomous, chat |
| `workflow` | n8n workflow or scheduled automation | n8n, workflow, automation, schedule, trigger, webhook |
| `deployment` | Deploy, configure, or operate a service | deploy, service, stack, container, Caddy route, Docker |
| `pipeline` | Data pipeline — transform, enrich, or aggregate data | pipeline, ETL, medallion, transform, schema, data quality |
| `migration` | Migrate data or consolidate systems | migrate, consolidate, export, import, decommission, move |
| `platform` | Platform or infrastructure change | infrastructure, Docker, security, networking, monitoring, backup, DNS |

## Dimension 2: Infrastructure Layer (REQUIRED — exactly one)

| Label | Scope | Examples |
|---|---|---|
| `L1-platform` | Foundation everything else depends on | Docker, Caddy, networking, DNS, Cloudflare, Tailscale, security, backup, OS, storage |
| `L2-services` | Running services shared across domains | PostgreSQL, Ollama, n8n, Grafana, MinIO, pgvector, MLflow, Open WebUI, MCP servers, Prometheus |
| `L3-framework` | Reusable components that domain apps build on | Scraper framework, agent runtime, Claude Code primitives, n8n workflow patterns |
| `L4-domain` | Business logic specific to one project | REAL deal scoring, GAME game logic, COS email triage, HOME automations, FOOD recipe workflow |

**Key property:** A ticket at Layer N may depend on tickets at Layers 1 through N-1, but never on Layer N+1.

## Dimension 3: Data Source (OPTIONAL)

For scraper and pipeline work, add a `source:` prefixed label identifying the external system.
Examples: `source:rentcast`, `source:gmail`, `source:bsa-online`

---

## Ticket Placement Decision Tree

```
How many L4 domain projects consume this work's output?

  ZERO (generic infrastructure) → LAB
    Running service? → L2 epic
    Platform/infra? → L1 epic

  ONE (single domain) → That domain's project (L4)
    Cross-project Blocks link to LAB if it touches shared infra.

  MULTIPLE (shared across domains) → LAB as L3 framework
    Blocks links FROM this LAB ticket TO domain tickets that depend on it.
```

**Promotion rule:** single-consumer → multi-consumer = move ticket to LAB L3.

## Project-Layer Mapping

| Project | Layers | Scope |
|---|---|---|
| **LAB** | L1, L2, L3 | Homelab platform — infra, services, frameworks |
| **REAL** | L4 | Real estate investing |
| **COS** | L4 | AI personal assistant |
| **GAME** | L4 | Autonomous game studio |
| **HOME** | L4 | Smart home automation |
| **FOOD** | L4 | Recipe/cooking workflows |
| **WEB** | L4 | Personal website |

---

## Decomposition Templates

When a ticket matches a work pattern, offer the standard decomposition. User can always override.

### Scraper (4 steps)
1. Configure credentials / evaluate API access
2. Build scraper — fetch raw data to storage
3. Design schema + transformation for normalized data
4. Schedule execution (n8n) + add monitoring

### Agent (5 steps)
1. Document agent architecture + tool interface spec
2. Create tool functions for data access
3. Build agent (MVP)
4. Add tests + error handling
5. Document + monitoring

### Workflow (3 steps)
1. Design workflow (inputs, triggers, nodes)
2. Implement + test
3. Schedule + monitor

### Deployment (5 steps)
1. Research — evaluate image, config, resource needs
2. Stack file + environment config
3. Caddy route + staging deployment
4. Production deployment + homepage + monitoring
5. Document operations runbook

### Pipeline (5 steps)
1. Schema design (source → normalized → derived)
2. Ingestion layer (raw data landing)
3. Transformation layer (entity resolution, enrichment)
4. Business logic layer (scoring, ranking, aggregation)
5. Validation + data quality checks

### Migration (5 steps)
1. Audit current state
2. Export / extract data
3. Import / transform to target
4. Verify completeness + functional test
5. Decommission source (if applicable)

### Platform (4 steps)
1. Research / design
2. Implement change
3. Test (staging-first for production changes)
4. Document

---

## Agent Routing

| Work Pattern | Primary Agent | Secondary Agents |
|---|---|---|
| `scraper` | `data-engineer` | `security-reviewer`, `test-engineer` |
| `agent` | `architecture-reviewer` | `test-engineer`, `security-reviewer` |
| `workflow` | `n8n-designer` | `observability-reviewer` |
| `deployment` | `homelab-ops` | `security-reviewer`, `observability-reviewer` |
| `pipeline` | `data-engineer` | `test-engineer` |
| `migration` | `data-engineer` | `homelab-ops` |
| `platform` | `homelab-ops` | `security-reviewer`, `architecture-reviewer` |

---

## Dependency Direction

1. **Cross-project Blocks links** flow downward: L1 → L2 → L3 → L4
2. **Within-project Blocks links** flow through the template: step 1 → step 2 → step 3
3. **Relates links** for shared-concern connections (not sequential)
4. **No circular dependencies** — if found, decomposition is wrong
