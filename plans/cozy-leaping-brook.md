# Plan: Add Taxonomy Label Visualization to jira-graph

## Context

The jira-graph Cytoscape.js app visualizes Jira tickets as a dependency graph. Nodes are currently colored by status category (To Do=blue, In Progress=amber, Done=green). Every LAB ticket has two taxonomy labels — **work pattern** (scraper, agent, workflow, deployment, pipeline, migration, platform) and **infrastructure layer** (L1-platform, L2-services, L3-framework, L4-domain) — but the graph has no visual indication of these.

The goal is to encode both taxonomy dimensions visually on nodes while preserving the existing status-color encoding.

---

## Visual Encoding

| Dimension | Visual Channel | Rationale |
|-----------|---------------|-----------|
| **Status category** | Background color (existing) | Keep — most important dimension |
| **Infrastructure layer** (4 values) | Node shape | Strongest remaining pre-attentive channel; only 4 values maps well to distinct shapes |
| **Work pattern** (7 values) | Border width + style | Secondary channel; 7 combinations of width/style are distinguishable on inspection |

### Layer → Shape

| Layer | Shape | Why |
|-------|-------|-----|
| `L1-platform` | `rectangle` | Flat, foundational |
| `L2-services` | `roundrectangle` | Current default — most tickets are L2, so graph looks the same |
| `L3-framework` | `barrel` | Rounded sides suggest a wrapping container |
| `L4-domain` | `diamond` | Visually distinct, topmost layer |
| (none) | `roundrectangle` | Graceful default |

### Work Pattern → Border

| Pattern | Width | Style | Visual |
|---------|-------|-------|--------|
| `scraper` | 3 | dashed | Medium dashed |
| `agent` | 4 | dotted | Thick dotted |
| `workflow` | 3 | solid | Medium solid |
| `deployment` | 3 | double | Medium double |
| `pipeline` | 4 | dashed | Thick dashed |
| `migration` | 4 | double | Thick double |
| `platform` | 3 | dotted | Medium dotted |
| (none) | 2 | solid | Current default |

### Stale node conflict

Current `node.stale` overrides border-style to dashed. Change it to only override `border-color` to orange — the work pattern border style stays visible, and the orange color signals staleness.

### Epic nodes

Epic compound parents do NOT get taxonomy encoding. They serve as visual containers and changing their shape would break layout. The taxonomy classes are only added to child (leaf) nodes.

---

## Changes by File

### 1. Backend: `submodules/jira-graph/services/graph_service.py`

- Add constants `WORK_PATTERNS` and `INFRA_LAYERS` (sets of valid label strings)
- Add `_extract_taxonomy(labels: list[str]) -> tuple[str | None, str | None]` — parses labels array, returns (work_pattern, infra_layer)
- Add `_taxonomy_classes(wp, layer) -> str` — returns e.g. `"wp-agent layer-L2-services"` or `""`
- In the child-node loop (line 53-77): extract taxonomy from `row["labels"]`, add `work_pattern` and `infra_layer` to `node_data`, append taxonomy classes to the `classes` string
- Epic node loop (line 32-51): unchanged — no taxonomy classes on epics

### 2. Frontend types: `submodules/jira-graph/frontend/src/types.ts`

- Add to `CyNode.data`: `work_pattern?: string | null` and `infra_layer?: string | null`

### 3. Frontend graph: `submodules/jira-graph/frontend/src/graph.ts`

- Add 3 layer shape selectors (L1, L3, L4 — L2 uses default roundrectangle) in the `initGraph` style array, after status selectors
- Add 7 work-pattern border selectors (`node.wp-scraper`, `node.wp-agent`, etc.)
- Simplify `node.stale` to only set `border-color: #f97316` (remove border-style/border-width overrides)

### 4. Frontend filters: `submodules/jira-graph/frontend/src/filters.ts`

- Add `initMultiSelect("filter-work-pattern", ...)` and `initMultiSelect("filter-layer", ...)` calls in `initFilters`
- Export `populateWorkPatternDropdown(patterns: string[])` and `populateLayerDropdown(layers: string[])`
- Extend `getClientFilters()` return to include `workPatterns: string[]` and `layers: string[]`

### 5. Frontend main: `submodules/jira-graph/frontend/src/main.ts`

- Import new populate functions
- In `extractDropdownOptions`: collect `work_pattern` and `infra_layer` values from nodes, call populate functions
- In `applyClientFilters`: add work-pattern and layer filtering to the visibility check (null values hidden when filter active)

### 6. HTML: `submodules/jira-graph/frontend/index.html`

- Add two multi-select dropdowns (`filter-work-pattern`, `filter-layer`) in the filter bar after `filter-type`
- Add legend container div inside `#main-content`

### 7. CSS: `submodules/jira-graph/frontend/src/styles.css`

- Add legend positioning (absolute, bottom-left of `#main-content`, z-index 10)
- Legend sections styling (~30 lines)

### 8. New file: `submodules/jira-graph/frontend/src/legend.ts`

- Export `initLegend()` — renders three sections: Status (colors), Layer (shapes), Pattern (borders)
- Small CSS shape swatches for each layer shape
- Border-style swatches for each work pattern
- Toggle button to show/hide

### 9. Tests: `submodules/jira-graph/tests/test_services.py`

- Add test: labels with both dimensions → correct classes and data fields
- Add test: labels with only one dimension → partial classes
- Add test: no labels → no taxonomy classes, fields are null
- Add test: epic nodes → no taxonomy classes regardless of labels
- Existing tests: update `classes` assertion in `test_build_graph_with_nodes` (now includes empty taxonomy suffix)

---

## Verification

1. **Backend tests**: `cd submodules/jira-graph && python -m pytest tests/ -v` — all pass including new taxonomy tests
2. **Frontend build**: `cd frontend && npm run build` — compiles without errors
3. **Docker rebuild**: `docker compose -f stacks/jira-graph-stack.yml --env-file .env up --force-recreate jira-graph -d`
4. **Visual check**: Open `jira.dirtydata.studio`, verify:
   - LAB tickets with labels show distinct shapes (L1=rectangle, L3=barrel, L4=diamond)
   - LAB tickets with work pattern labels show distinct border styles
   - Tickets without labels look identical to current (roundrectangle, 2px solid)
   - Epic containers are unchanged
   - Stale nodes have orange border color but preserve pattern border style
5. **Filter check**: Work Pattern and Layer dropdowns filter nodes correctly; unlabeled nodes hidden when filter active
6. **Legend**: Collapsible legend in bottom-left shows all three encoding dimensions
7. **Detail panel**: Labels still shown in detail panel on click (existing `issue.labels` display)
