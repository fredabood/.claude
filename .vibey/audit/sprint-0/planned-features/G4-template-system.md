# G4: Ticket Template System Design Review

**Task ID:** 01KFXJB0QW9HFRV9GTSTVH4Z5G
**Phase:** G4: Planned Features
**Date:** 2026-01-29

## Executive Summary

Review of the Ticket Template System track (01KD63P4NHSQJ9ZVYGR6MR9JW9) covering 6 planned sprints for standardized development workflows. The track will implement a template engine for task creation with variable substitution, inheritance, and versioning. Existing foundation includes 30+ handoff templates using Jinja2 in `vibey/content/templates/` and ContentType.TEMPLATE in the content models. Key finding: Remote template sharing requires a central template repository with version sync, team namespaces, and conflict resolution for collaborative template development.

## Methodology

**Files Analyzed:**
- `.vibey/roadmap/tracks/01KD63P4NHSQJ9ZVYGR6MR9JW9.yaml` - Track definition
- `vibey/operations/content/models.py:1-245` - ContentType and ContentMetadata
- `vibey/operations/content/loader.py:1-292` - ContentLoader
- `vibey/mcp/resources/handoffs.py:1-551` - HandoffResourceProvider (template pattern)
- `vibey/content/templates/` - 31 existing template files

## Findings

### 2. Template Data Model Table

| Field | Type | Required | Purpose | Inheritance |
|-------|------|----------|---------|-------------|
| `id` | string | Yes | Unique template identifier | None |
| `name` | string | Yes | Human-readable display name | Override allowed |
| `version` | string | Yes | Semantic version (1.0.0) | None |
| `type` | string | No | Template category (handoff, task, sprint) | None |
| `description` | string | No | Template purpose description | Override allowed |
| `tags` | list | No | Categorization tags | Merge with parent |
| `from_agent` | string | No | Source agent for handoffs | None |
| `to_agents` | list | No | Target agents for handoffs | Override allowed |
| `purpose` | string | No | Template intent | None |
| `variables` | list | No | Variable definitions | Merge with parent |
| `extends` | string | No | Parent template ID | None |
| `project_types` | list | No | Applicable project types (ml, api, web-app) | None |

### 3. Variable Substitution Table

| Variable Type | Syntax | Default | Validation | Example |
|---------------|--------|---------|------------|---------|
| Simple | `{{ variable }}` | None | Required check | `{{ sprint_name }}` |
| Optional | `{{ variable or 'default' }}` | Fallback value | None | `{{ config.roles.test_engineer or 'QA' }}` |
| Conditional | `{% if condition %}...{% endif %}` | N/A | Boolean eval | `{% if config.project.type == 'ml' %}` |
| Loop | `{% for item in list %}...{% endfor %}` | Empty list | Iterable check | `{% for risk in risks %}` |
| Filter | `{{ variable \| filter }}` | None | Filter exists | `{{ name \| lower }}` |
| Config Access | `{{ config.path.to.value }}` | None | Path validation | `{{ config.quality_gates.security_score_minimum }}` |

### 4. Instantiation Flow Diagram (ASCII)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TEMPLATE INSTANTIATION FLOW                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ 1. SELECTION    │       │ 2. RESOLUTION   │       │ 3. VARIABLES    │
│ - Search by ID  │──────▶│ - Load template │──────▶│ - Validate req  │
│ - Search by tag │       │ - Resolve extend│       │ - Apply defaults│
│ - Search by type│       │ - Merge parents │       │ - Type coerce   │
└─────────────────┘       └─────────────────┘       └────────┬────────┘
                                                             │
                          ┌──────────────────────────────────┘
                          │
                          ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ 6. HOOKS        │◀──────│ 5. CREATION     │◀──────│ 4. RENDER       │
│ - Post-create   │       │ - Write YAML    │       │ - Jinja2 render │
│ - Validate      │       │ - Update roadmap│       │ - Strip FM      │
│ - Notify        │       │ - Link to sprint│       │ - Format output │
└─────────────────┘       └─────────────────┘       └─────────────────┘
        │
        │ Return task/sprint/track
        ▼
┌─────────────────┐
│ CREATED ENTITY  │
│ - ID assigned   │
│ - Linked        │
│ - Ready to work │
└─────────────────┘
```

### 5. Template Storage Table

| Storage Location | Organization | Discovery | Access |
|------------------|--------------|-----------|--------|
| `vibey/content/templates/` | Package bundled | Package introspection | Read-only |
| `vibey/content/templates/handoffs/` | By handoff type | Glob `*.md` | Read-only |
| `.vibey/templates/` | Project custom | Glob all | Read/Write |
| `.vibey/templates/tasks/` | Task templates | By task type | Read/Write |
| `.vibey/templates/sprints/` | Sprint templates | By sprint type | Read/Write |
| `.vibey/templates/tracks/` | Track templates | By track type | Read/Write |
| Unity Catalog (remote) | Team namespace | Delta Lake query | Team ACL |

### 6. Remote Sharing Strategy

| Feature | Local Behavior | Remote Behavior | Sync Method |
|---------|----------------|-----------------|-------------|
| Template Creation | Write to .vibey/templates/ | Upload to central repo | Push on create |
| Template Discovery | Scan local + package | Query Delta Lake | Cached pull |
| Template Update | Edit local file | Version bump, upload | Push with conflict check |
| Template Inheritance | Resolve local chain | Resolve across repos | Fetch parent on demand |
| Team Templates | N/A | Namespace isolation | Team ACL |
| Public Templates | N/A | Curated library | Read-only pull |
| Template Variables | JSON Schema locally | Schema in Unity Catalog | Schema sync |

**Remote Template Architecture:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      REMOTE TEMPLATE SHARING                                 │
└─────────────────────────────────────────────────────────────────────────────┘

  LOCAL                                    DATABRICKS
  ─────                                    ──────────

┌─────────────────┐                    ┌─────────────────┐
│ Package         │                    │ Central Repo    │
│ Templates       │                    │ (Delta Lake)    │
│ (read-only)     │                    │                 │
└─────────────────┘                    │ ┌─────────────┐ │
                                       │ │ Team A      │ │
┌─────────────────┐                    │ │ namespace   │ │
│ Project         │◀───── Pull ───────▶│ └─────────────┘ │
│ Templates       │                    │                 │
│ (.vibey/)       │                    │ ┌─────────────┐ │
└─────────────────┘                    │ │ Team B      │ │
        │                              │ │ namespace   │ │
        │ Create/Edit                  │ └─────────────┘ │
        ▼                              │                 │
┌─────────────────┐                    │ ┌─────────────┐ │
│ Local Changes   │───── Push ────────▶│ │ Public      │ │
└─────────────────┘                    │ │ (curated)   │ │
                                       │ └─────────────┘ │
                                       └─────────────────┘
```

### 7. Version Management Table

| Aspect | Local | Remote | Conflict Resolution |
|--------|-------|--------|---------------------|
| Version Scheme | Semantic (1.0.0) | Semantic + timestamp | Higher wins |
| Storage | File content | Delta Lake row | Version history |
| History | Git history | Delta time travel | Both available |
| Rollback | Git checkout | Delta restore | Manual select |
| Deprecation | Remove file | Mark deprecated | Warn on use |
| Breaking Changes | Manual tracking | Schema evolution | Migration scripts |
| Draft/Published | N/A | Status column | Draft invisible |
| Approval Flow | N/A | Review required | Owner approval |

### Existing Template Infrastructure

| Component | Files | Purpose |
|-----------|-------|---------|
| ContentType.TEMPLATE | `models.py:22` | Template type enum |
| get_templates_dir() | `content/__init__.py` | Template directory accessor |
| HandoffResourceProvider | `handoffs.py:1-551` | MCP resource for handoffs |
| HandoffVariable | `handoffs.py:36-44` | Variable definition model |
| HandoffDefinition | `handoffs.py:47-95` | Template definition model |
| Jinja2 Templates | `templates/*.j2` | Reusable Jinja templates |
| Handoff Templates | `templates/handoffs/` | 30 handoff templates |

### Template Categories Inventory

| Category | Count | Purpose | Example |
|----------|-------|---------|---------|
| Handoffs | 21 | Agent-to-agent communication | sprint-plan-template.md |
| Jinja2 | 3 | Reusable components | agent.md.j2, workflow.md.j2 |
| Config | 6 | Configuration scaffolds | CLAUDE.md.template |
| State | 1 | Sprint state tracking | sprint-state.yaml.template |

## Remote Mode Implications

| Finding | Recommendation | Effort | Priority |
|---------|----------------|--------|----------|
| 6 sprints planned, 0 tasks | Can start design phase | L | Medium |
| 31 existing templates | Migrate to structured model | M | High |
| Jinja2 already in use | Keep Jinja2 for rendering | - | N/A |
| No remote sharing | Add Unity Catalog storage | M | High |
| No versioning system | Implement semantic versioning | M | Medium |
| No team namespaces | Design namespace isolation | M | Medium |
| HandoffResourceProvider exists | Extend for all template types | S | Medium |
| ContentType.TEMPLATE defined | Build on existing model | S | High |

## Verification Checklist

- [x] Deliverable file exists at specified path: PASS
- [x] Template data model table lists >= 5 fields: PASS (12 fields)
- [x] Variable substitution table lists >= 3 variable types: PASS (6 types)
- [x] ASCII instantiation flow diagram present: PASS
- [x] Remote sharing strategy addresses team sharing: PASS (namespace isolation)

## References

- `.vibey/roadmap/tracks/01KD63P4NHSQJ9ZVYGR6MR9JW9.yaml:1-76` - Track definition
- Track progress: 0% complete, 6 sprints, 0 tasks
- `vibey/operations/content/models.py:17-27` - ContentType enum
- `vibey/mcp/resources/handoffs.py:36-95` - HandoffVariable, HandoffDefinition
- `vibey/content/templates/` - 31 existing template files
- Strategic value: Standardize workflows, ensure quality gates, reduce manual creation
