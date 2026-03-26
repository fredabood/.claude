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

## Status Workflow (INFORMATIONAL — not a label)

Status is a native Jira field, not a label dimension. This section documents the target workflow
so all agents and rules share a consistent understanding.

| Status | Category | Description | Entry trigger | Exit trigger |
|---|---|---|---|---|
| `To Do` | New | Queued, not started | Ticket created | Agent picks up work |
| `In Progress` | In Progress | Active implementation | Agent starts (transition 21) | Implementation + tests done |
| `Work Complete` | Done | Code + tests + post-mortem done | CI gates pass | Doc review verified |
| `Doc Review Complete` | Done | Docs + memory updates reviewed. Fully closed. | Doc review passes | Terminal |
| `Won't Do` | Done | Cancelled or abandoned | Manual decision | Terminal |

**Valid transitions:**

```
To Do ──→ In Progress ──→ Work Complete ──→ Doc Review Complete
  │                                │
  └──→ Won't Do ←─────────────────┘  (from any non-terminal status)
```

**Transition IDs:** Use `getTransitionsForJiraIssue` at runtime to discover IDs — do not hardcode.
New statuses (Work Complete, Doc Review Complete, Won't Do) are created by LAB-628.
Until LAB-628 lands, the existing 2-status workflow (In Progress → Done) remains active.

---

## Planned (CALCULATED — not a label)

A ticket is **Planned** when it has both:
1. An `## Acceptance Criteria` section in the description
2. An implementation plan posted as a Jira comment (contains `## Implementation Plan` or numbered plan sections)

| Value | Meaning |
|---|---|
| `true` | Both criteria and plan exist — ready for work queue consideration |
| `false` | Missing criteria, plan, or both — needs planning before pickup |

**Detection logic (agent-side):**
1. `getJiraIssue` → inspect `description` for `Acceptance Criteria` heading
2. Fetch issue comments → search for plan comment (heading or structured numbered sections)
3. Both present = Planned

This is calculated at read time, not stored as a Jira field. See `.claude/rules/label-taxonomy.md` (this file) as the canonical definition.

---

## Blocked (CALCULATED — not a label)

A ticket is **Blocked** when it has at least one unresolved inward "Blocks" link — i.e., another ticket that must finish first but hasn't.

| Value | Meaning |
|---|---|
| `true` | At least one blocker is not in status category "Done" |
| `false` | No blockers, or all blockers are Done |

**Detection logic (agent-side):**
1. `getJiraIssue` → inspect `issuelinks`
2. For each link with `type.inward == "is blocked by"`: check the linked issue's `statusCategory.name`
3. If any blocker is not `"Done"` → Blocked = true

This is calculated at read time, not stored as a Jira field.

---

## Agent Work Queue

The agent work queue consists of tickets eligible for autonomous pickup:

```
Eligible = status:"To Do" AND Planned:true AND Blocked:false
```

**JQL base query:**
```
project = <KEY> AND status = "To Do" AND description ~ "Acceptance Criteria"
  ORDER BY priority DESC, created ASC
```

**Agent-side filtering (after JQL results):**
1. **Plan check:** Verify a plan comment exists (inspect comments for plan structure)
2. **Blocker check:** Verify no unresolved inward "Blocks" links (all blockers Done)
3. **Assignment check:** If `Assigned Agent` field is set and ≠ current agent, skip

**Pickup protocol:**
1. Query the work queue using the JQL + agent-side filters above
2. Select the highest-priority eligible ticket
3. Set `Assigned Agent` to the current session identifier (requires custom field from LAB-628; until then, post assignment as a Jira comment)
4. Transition to "In Progress"
5. Post context comment with session timestamp

**Priority within the queue:** Priority field (descending) → created date (ascending, oldest first).

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
