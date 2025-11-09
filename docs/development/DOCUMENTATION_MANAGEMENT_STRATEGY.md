# Documentation Management Strategy - Holistic Review

**Date:** 2025-11-09
**Status:** Proposal
**Purpose:** Analyze current documentation practices and propose improvements for organizational standardization

---

## Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [Problems Identified](#problems-identified)
3. [Proposed Hierarchical Structure](#proposed-hierarchical-structure)
4. [Tradeoff Analysis](#tradeoff-analysis)
5. [Implementation Recommendations](#implementation-recommendations)
6. [Migration Plan](#migration-plan)
7. [Impact Assessment](#impact-assessment)

---

## Current State Analysis

### Documentation Storage Today

**Three Separate Storage Locations:**

```
vibey/
├── docs/                          # Framework & project documentation
│   ├── development/               # Research, analyses, architectural decisions (14 files)
│   ├── sprints/                   # Sprint plans (4 files)
│   ├── examples/                  # Examples
│   └── [other categories]
│
├── .vibey/                        # Roadmap system (source of truth)
│   ├── roadmap.yaml               # Master roadmap
│   ├── tracks/                    # Track definitions (10 files)
│   ├── sprints/                   # Sprint state (5 files)
│   ├── tasks/                     # Task state (4 files)
│   ├── sprint_docs/               # Sprint-specific docs (inconsistent)
│   ├── sprint_summaries/          # Completed sprint summaries (4 files)
│   ├── track_summaries/           # Completed track summaries (1 file)
│   └── summaries/                 # Task/dependency summaries (4 files)
│
└── .claude/                       # Deployment (generated)
    └── [deployed framework files]
```

### Current Documentation Types & Locations

| Documentation Type | Current Location | Associated With | Model Context Tracking |
|-------------------|------------------|-----------------|------------------------|
| **Research Reports** | `docs/development/` | Ad-hoc | ❌ No tracking |
| **Architectural Decisions** | `docs/development/` | Ad-hoc | ❌ No tracking |
| **Platform Analyses** | `docs/development/` | Sometimes tracks | ❌ Implicit only |
| **Sprint Plans** | `docs/sprints/` OR `.vibey/sprint_docs/` | Sprints | ⚠️ Inconsistent |
| **Sprint Summaries** | `.vibey/sprint_summaries/` | Sprints | ✅ Yes |
| **Track Summaries** | `.vibey/track_summaries/` | Tracks | ✅ Yes |
| **Task Summaries** | `.vibey/summaries/task_summaries/` | Tasks | ✅ Yes |
| **Dependency Summaries** | `.vibey/summaries/dependency_summaries/` | Tasks | ✅ Yes |
| **Implementation Plans** | `docs/development/` | Sometimes tracks | ❌ Implicit only |
| **Gap Analyses** | `docs/development/` | Sometimes tracks | ❌ Implicit only |

### Examples of Documentation Created During Roadmap Execution

**Track: mcp-server**
- `docs/development/MCP_VS_ADAPTER_STRATEGY.md` - Strategic analysis
- ✅ Linked in `mcp-server.yaml` via `metadata.design_doc`
- ❌ Not in hierarchical structure near the track

**Track: roadmap-system**
- `docs/development/ROADMAP_OBJECT_HIERARCHY.md` - Design document
- `docs/development/ROADMAP_IMPLEMENTATION_PLAN.md` - Implementation plan
- `docs/development/ROADMAP_INTEGRATION_GAP.md` - Gap analysis
- ❌ No links in track YAML files
- ❌ Scattered across flat `docs/development/` directory

**Track: core-framework, Sprint 2**
- `docs/development/PLATFORM_AGNOSTIC_ARCHITECTURE.md` - Architecture guide
- `docs/development/PLATFORM_ADAPTER_PATTERN.md` - Design pattern
- `docs/development/YAML_MARKDOWN_SEPARATION.md` - Design document
- `docs/sprints/core-framework-2-plan.md` - Sprint plan
- `.vibey/sprint_docs/core-framework/core-framework-2/task-*.md` - Task docs
- `.vibey/sprint_summaries/core-framework-2-COMPLETED.md` - Sprint summary (doesn't exist yet)
- ❌ Spread across 3 locations (docs/development, docs/sprints, .vibey/sprint_docs)

### Current Linking Mechanisms

**Track → Documentation:**
```yaml
# .vibey/tracks/mcp-server.yaml
metadata:
  design_doc: docs/development/MCP_VS_ADAPTER_STRATEGY.md
  implementation_plan: null
  notes: |
    Long-form context and strategic rationale
```

**Sprint → Documentation:**
- ❌ No explicit linking in sprint YAML files
- Sprint plans sometimes in `docs/sprints/`, sometimes in `.vibey/sprint_docs/`

**Task → Documentation:**
- ❌ No explicit linking in task YAML files
- Task summaries in `.vibey/summaries/task_summaries/`

---

## Problems Identified

### 1. Documentation Fragmentation

**Problem:** Research reports, analyses, and architectural decisions are scattered across multiple locations with inconsistent naming and organization.

**Impact:**
- Hard to find related documentation
- No standard location for sprint-level or task-level research
- Model context must search multiple directories
- Difficult to understand what documentation exists for a given roadmap object

**Examples:**
- Sprint plans: Some in `docs/sprints/`, some in `.vibey/sprint_docs/`
- Architecture docs: All in flat `docs/development/` directory
- Task docs: Sometimes in `.vibey/sprint_docs/`, sometimes nowhere

### 2. Weak Model Context Tracking

**Problem:** Documentation created during task execution is not systematically associated with the roadmap objects (track/sprint/task) that generated it.

**Impact:**
- When resuming a task, AI must search for related context
- No standard "context" directory per task
- Research/analyses created during execution are not preserved alongside task state
- Loss of valuable decision-making context

**Examples:**
- MCP strategy document created for `mcp-server` track, but only loosely linked via `design_doc` field
- Platform research created for multiple tracks, no clear association
- Task-level graphs, analyses, research have no standard storage location

### 3. Inconsistent Storage Patterns

**Problem:** Different types of documentation follow different organizational patterns.

**Current Patterns:**
- **Summaries:** Consistently stored in `.vibey/[type]_summaries/`
- **Sprint docs:** Inconsistently stored (docs/sprints OR .vibey/sprint_docs)
- **Research/analyses:** All in flat `docs/development/` directory
- **Task context:** No standard location

### 4. No Project Documentation Tracking

**Problem:** User project documentation (outside Vibey framework) is not tracked or linked to roadmap objects.

**Impact:**
- When a sprint/task modifies project documentation, that relationship isn't captured
- Can't answer "which sprints impacted README.md?"
- Can't generate "documentation changelog" from roadmap activity
- No way to require documentation updates as part of sprint completion

**Example:**
- Sprint adds new feature → requires updating user-facing docs
- Relationship not tracked → documentation updates may be forgotten

### 5. Flat Directory Structure Limitations

**Problem:** `docs/development/` is a flat directory with 14+ files and growing.

**Impact:**
- Difficult to browse and discover related documents
- No clear grouping by track or sprint
- File naming carries organizational burden (e.g., `ROADMAP_INTEGRATION_GAP.md`)
- Scales poorly as more tracks/sprints are added

---

## Proposed Hierarchical Structure

### Directory Layout

```
.vibey/                                 # Vibey internal workspace (SOURCE OF TRUTH)
├── config/                             # Configuration
├── templates/                          # Templates
└── roadmap/                            # Roadmap hierarchy (internal)
    ├── .sync-manifest.json             # Tracks synchronized files
    ├── table_of_contents.json          # Root: tracks overview
    ├── roadmap.yaml                    # Master roadmap (YAML = source of truth)
    ├── roadmap.md                      # Human-readable view (generated)
    │
    ├── /track1
    │   ├── table_of_contents.json      # Track: sprints overview (generated)
    │   ├── track1.yaml                 # Track definition (YAML = source)
    │   ├── track1.md                   # Track overview (generated)
    │   ├── track1-COMPLETED.md         # Track summary (generated on completion)
    │   └── /context                    # Track-level research/analyses
    │       ├── design.md               # Strategic analysis
    │       ├── architecture.md         # Architecture decision
    │       └── implementation-plan.md  # Implementation plan
    │
    ├── /track2
    │   ├── table_of_contents.json
    │   ├── track2.yaml
    │   ├── track2.md
    │   │
    │   ├── /sprint1
    │   │   ├── table_of_contents.json  # Sprint: tasks overview (generated)
    │   │   ├── sprint1.yaml            # Sprint state (YAML = source)
    │   │   ├── sprint1.md              # Sprint plan (generated)
    │   │   ├── sprint1-COMPLETED.md    # Sprint summary (generated on completion)
    │   │   ├── /context                # Sprint-level research/planning
    │   │   │   ├── sprint-design.md
    │   │   │   └── api-exploration.md
    │   │   │
    │   │   ├── /task1
    │   │   │   ├── task1.yaml          # Task state (YAML = source)
    │   │   │   ├── task1.md            # Task description (generated)
    │   │   │   └── /context            # Task-level execution context
    │   │   │       ├── analysis.md     # Analysis during execution
    │   │   │       ├── research.md     # Research findings
    │   │   │       ├── graphs.json     # Data artifacts
    │   │   │       └── decisions.md    # Decision log
    │   │   │
    │   │   └── /task2
    │   │       ├── task2.yaml
    │   │       ├── task2.md
    │   │       └── /context
    │   │
    │   ├── /sprint2
    │   │   ├── [same structure as sprint1]
    │   │
    │   └── /sprint3
    │
    └── /track3

docs/                                   # User-facing documentation (SYNCHRONIZED)
├── /reference                          # Framework reference (if framework project)
│   └── ai-reference.md
│
├── /roadmap                            # Roadmap documentation (synchronized from .vibey)
│   ├── roadmap.md                      # Synchronized from .vibey/roadmap/
│   ├── /track1
│   │   ├── track1.md                   # Synchronized
│   │   ├── track1-COMPLETED.md         # Synchronized
│   │   └── [context files]             # Selectively synchronized
│   └── /track2
│       ├── track2.md                   # Synchronized
│       └── /sprint1
│           ├── sprint1.md              # Synchronized
│           └── sprint1-COMPLETED.md    # Synchronized
│
└── [user project documentation]        # User's own docs
    ├── README.md
    ├── README.md.meta.json             # Tracks roadmap impacts
    └── API.md
```

**Key Points:**
- **`.vibey/roadmap/`** = Source of truth (all files, YAML state, internal workspace)
- **`docs/roadmap/`** = Public view (synchronized markdown files only)
- **YAML files** = Source of truth, live in `.vibey/`, never synchronized
- **JSON TOC files** = Navigation aids, live in `.vibey/`, never synchronized
- **Markdown files** = Generated views, synchronized to `docs/` for user browsing
- **Context directories** = Allowed at track, sprint, AND task levels

### Key Structural Elements

#### 1. Table of Contents (JSON)

**Purpose:** Navigation aid showing hierarchy context and children.

**Root Level** (`/docs/roadmap/table_of_contents.json`):
```json
{
  "level": "roadmap",
  "parent": null,
  "current": {
    "id": "vibey-framework-v2",
    "name": "Vibey Multi-Platform Agent Framework",
    "files": {
      "yaml": "roadmap.yaml",
      "markdown": "roadmap.md"
    }
  },
  "children": [
    {
      "type": "track",
      "id": "core-framework",
      "name": "Core Framework Enhancements",
      "path": "core-framework/",
      "status": "completed"
    },
    {
      "type": "track",
      "id": "mcp-server",
      "name": "MCP Server Foundation",
      "path": "mcp-server/",
      "status": "not_started"
    }
  ],
  "metadata": {
    "generated": "2025-11-09T14:00:00Z",
    "tracks_total": 10,
    "tracks_completed": 4
  }
}
```

**Track Level** (`/docs/roadmap/mcp-server/table_of_contents.json`):
```json
{
  "level": "track",
  "parent": {
    "type": "roadmap",
    "path": "../"
  },
  "current": {
    "id": "mcp-server",
    "name": "MCP Server Foundation",
    "files": {
      "yaml": "mcp-server.yaml",
      "markdown": "mcp-server.md",
      "summary": "mcp-server-COMPLETED.md"
    },
    "context": [
      "context/MCP_VS_ADAPTER_STRATEGY.md",
      "context/mcp-protocol-research.md"
    ]
  },
  "children": [
    {
      "type": "sprint",
      "id": "mcp-server-1",
      "name": "MCP Protocol & Core Implementation",
      "path": "mcp-server-1/",
      "status": "not_started"
    },
    {
      "type": "sprint",
      "id": "mcp-server-2",
      "name": "Integration, Testing & Documentation",
      "path": "mcp-server-2/",
      "status": "not_started"
    }
  ],
  "metadata": {
    "sprints_total": 2,
    "sprints_completed": 0,
    "tasks_total": 9,
    "tasks_completed": 0
  }
}
```

**Sprint Level** (`/docs/roadmap/mcp-server/mcp-server-1/table_of_contents.json`):
```json
{
  "level": "sprint",
  "parent": {
    "type": "track",
    "id": "mcp-server",
    "path": "../"
  },
  "current": {
    "id": "mcp-server-1",
    "name": "MCP Protocol & Core Implementation",
    "files": {
      "yaml": "mcp-server-1.yaml",
      "markdown": "mcp-server-1.md",
      "summary": "mcp-server-1-COMPLETED.md"
    }
  },
  "children": [
    {
      "type": "task",
      "id": "mcp-server-1-task-001",
      "name": "Research MCP specification",
      "path": "task-001/",
      "status": "not_started"
    },
    {
      "type": "task",
      "id": "mcp-server-1-task-002",
      "name": "Design Vibey MCP server architecture",
      "path": "task-002/",
      "status": "not_started"
    }
  ],
  "metadata": {
    "tasks_total": 5,
    "tasks_completed": 0
  }
}
```

#### 2. Context Directories

**Track-level context** (`/docs/roadmap/[track-id]/context/`):
- Strategic analyses
- Architecture decisions
- Implementation plans
- Platform research
- Gap analyses

**Sprint-level context** (if needed):
- Currently not common, but structure supports it

**Task-level context** (`/docs/roadmap/[track-id]/[sprint-id]/[task-id]/context/`):
- Research conducted during task execution
- Analyses created for the task
- Graphs, diagrams, data files
- Decision logs
- Code exploration summaries

#### 3. Markdown Views

**Purpose:** Human-readable summaries generated from YAML + context.

**Track Markdown** (`track.md`):
- Overview of track goals
- Current status and progress
- List of sprints with status
- Links to context documents
- Timeline and milestones

**Sprint Markdown** (`sprint.md`):
- Sprint plan and goals
- Task breakdown
- Dependencies and blockers
- Estimated vs actual duration

**Task Markdown** (`task.md`):
- Task description
- Acceptance criteria
- Context links
- Progress notes

#### 4. Summary Documents

**Completion Summaries:**
- `[track-id]-COMPLETED.md` - Generated when track completes
- `[sprint-id]-COMPLETED.md` - Generated when sprint completes
- Contains: achievements, lessons learned, metrics

---

## Tradeoff Analysis

### Benefits of Hierarchical Structure

#### ✅ 1. Co-location of Related Information

**Benefit:** All documentation for a roadmap object lives alongside its definition.

**Example:**
```
/docs/roadmap/mcp-server/
├── mcp-server.yaml           # Definition
├── mcp-server.md             # Overview
└── context/
    └── MCP_VS_ADAPTER_STRATEGY.md  # Strategic analysis
```

**vs Current:**
```
.vibey/tracks/mcp-server.yaml  # Definition
docs/development/MCP_VS_ADAPTER_STRATEGY.md  # Analysis (separate location)
```

**Impact:**
- Easier to find all relevant documentation
- Clear association between roadmap object and its context
- Better for model context loading (read entire directory)

#### ✅ 2. Scalability

**Benefit:** Structure scales naturally as roadmap grows.

**Current Problem:**
- `docs/development/` has 14 files, will have 50+ after more tracks
- Flat directory becomes unmanageable

**Hierarchical Solution:**
- Each track/sprint/task has its own context directory
- Scales to hundreds of tracks without directory bloat

#### ✅ 3. Standardized Context Storage

**Benefit:** Every task has a `context/` directory for execution artifacts.

**Current Problem:**
- No standard place for task-level research/analyses
- Model context scattered or lost

**Example:**
```
/docs/roadmap/mcp-server/mcp-server-1/task-001/
├── task-001.yaml
├── task-001.md
└── context/
    ├── mcp-spec-research.md     # Research during execution
    ├── sdk-comparison.md         # Analysis created
    └── architecture-sketch.json  # Design artifacts
```

**Impact:**
- AI can systematically save execution context
- Context preserved for future reference
- Can resume task with full context

#### ✅ 4. Better Model Context Discovery

**Benefit:** AI can load context hierarchically based on current scope.

**Loading Patterns:**
- Working on task → Load task context + sprint context + track context
- Planning sprint → Load track context + sprint overview
- Strategic decision → Load track context + roadmap overview

**Example Query:**
"Load all context for task mcp-server-1-task-001"
→ Reads: `/docs/roadmap/mcp-server/mcp-server-1/task-001/context/*`

#### ✅ 5. Table of Contents Navigation

**Benefit:** Each level has JSON manifest showing hierarchy.

**Use Cases:**
- AI can navigate hierarchy programmatically
- Generate breadcrumbs (Roadmap > Track > Sprint > Task)
- List all children at each level
- Understand parent-child relationships

**Example:**
```python
# Load TOC to find all tasks in a sprint
toc = json.load('/docs/roadmap/mcp-server/mcp-server-1/table_of_contents.json')
tasks = [child['path'] for child in toc['children'] if child['type'] == 'task']
```

#### ✅ 6. Project Documentation Tracking

**Benefit:** Can link project docs to roadmap objects that impact them.

**Structure:**
```
/docs/project_documentation/
├── README.md
├── README.md.meta.json    # Metadata about which roadmap objects impact this file
└── API.md
    └── API.md.meta.json
```

**Metadata Example:**
```json
{
  "file": "README.md",
  "impacted_by": [
    {
      "roadmap_object": "mcp-server/mcp-server-1/task-003",
      "type": "task",
      "change_type": "added_section",
      "section": "MCP Server Setup",
      "date": "2025-11-09"
    },
    {
      "roadmap_object": "core-framework/core-framework-2",
      "type": "sprint",
      "change_type": "major_rewrite",
      "date": "2025-11-09"
    }
  ]
}
```

**Benefits:**
- Track which sprints/tasks modify which docs
- Generate documentation changelog
- Ensure documentation updates in sprint completion criteria

---

### Drawbacks and Costs

#### ❌ 1. Migration Effort

**Cost:** Moving existing files to new structure.

**Effort Estimate:**
- Move `.vibey/tracks/` → `/docs/roadmap/[track-id]/`
- Move `.vibey/sprints/` → `/docs/roadmap/[track-id]/[sprint-id]/`
- Move `.vibey/tasks/` → `/docs/roadmap/[track-id]/[sprint-id]/[task-id]/`
- Move `docs/development/` files → appropriate `/context/` directories
- Generate all `table_of_contents.json` files
- Generate all `.md` views from YAML

**Time:** 1-2 days of implementation + testing

**Risk:** Breaking existing scripts that reference old paths

#### ❌ 2. Path Length and Nesting

**Cost:** Deeper directory hierarchies mean longer file paths.

**Example:**
```
# Current
.vibey/tracks/mcp-server.yaml

# Proposed
docs/roadmap/mcp-server/mcp-server.yaml
```

**Deeper nesting for tasks:**
```
# Proposed
docs/roadmap/mcp-server/mcp-server-1/task-001/task-001.yaml
docs/roadmap/mcp-server/mcp-server-1/task-001/context/research.md
```

**Impact:**
- More verbose paths in code
- Requires more `../` for relative paths
- File operations slightly more complex

**Mitigation:**
- Use path helper functions
- Store paths in constants
- Use absolute paths from repo root

#### ❌ 3. File Duplication (YAML + JSON + MD)

**Cost:** Each roadmap object has 3+ files (YAML, MD, TOC JSON).

**Current:**
- `mcp-server.yaml` (track definition)

**Proposed:**
- `mcp-server.yaml` (source of truth)
- `mcp-server.md` (generated human view)
- `table_of_contents.json` (generated navigation)

**Impact:**
- More files to maintain
- Risk of inconsistency if not generated
- Slightly larger repo size

**Mitigation:**
- MD and JSON are **generated**, not hand-edited
- Single source of truth (YAML)
- Generation happens automatically via CLI

#### ❌ 4. Cognitive Overhead

**Cost:** More structure to learn and remember.

**Current:**
- Simple: YAML files in `.vibey/[type]/`

**Proposed:**
- Hierarchical: Navigate track → sprint → task
- Multiple file types per object
- Context directories to manage

**Impact:**
- Steeper learning curve
- More decisions about where to put files
- Need documentation about structure

**Mitigation:**
- Clear conventions and examples
- CLI commands abstract structure (`vibey roadmap add-context`)
- Generated TOC helps navigation

#### ❌ 5. Git Diff Noise

**Cost:** Moving files creates large diffs, losing history.

**Impact:**
- `git log` shows file moves, not real changes
- Harder to track evolution of specific files
- One-time disruption to git history

**Mitigation:**
- Use `git mv` to preserve history
- Do migration in dedicated commit
- Use `git log --follow` to track moved files

---

### Comparison: Flat vs Hierarchical

| Aspect | Current (Flat) | Proposed (Hierarchical) |
|--------|---------------|------------------------|
| **Findability** | ❌ Search required | ✅ Navigate by hierarchy |
| **Scalability** | ❌ 50+ files in one directory | ✅ Distributed across structure |
| **Context Association** | ⚠️ Manual linking | ✅ Co-located |
| **Model Context Loading** | ❌ Must search multiple locations | ✅ Load by directory |
| **Path Complexity** | ✅ Short paths | ❌ Longer paths |
| **Migration Cost** | ✅ No migration | ❌ 1-2 days effort |
| **Learning Curve** | ✅ Simple | ❌ More structure |
| **File Count** | ✅ Fewer files | ❌ More files (generated) |
| **Navigation** | ❌ Manual | ✅ TOC JSON |
| **Project Doc Tracking** | ❌ No support | ✅ Metadata system |

---

## Implementation Recommendations

### Recommendation: **ADOPT HIERARCHICAL STRUCTURE** (with phased migration)

**Rationale:**
1. **Scalability is critical** - Current flat structure doesn't scale to 10+ tracks
2. **Model context benefits are high** - Systematic context storage improves AI effectiveness
3. **Migration cost is manageable** - 1-2 days of work for long-term benefits
4. **Aligns with roadmap vision** - Structure reflects conceptual hierarchy

### Phased Implementation

#### Phase 1: New Tracks (Immediate)

**Approach:** New tracks use hierarchical structure, existing tracks stay flat.

**Benefits:**
- No migration disruption
- Test new structure with real usage
- Learn and refine before full migration

**Implementation:**
- Modify `vibey deploy` to generate hierarchical structure for new tracks
- Update roadmap CLI to support both structures
- Document new structure conventions

**Timeline:** 1 week

#### Phase 2: Migration Script (1 month out)

**Approach:** Create automated migration script for existing tracks.

**Script Capabilities:**
- Move `.vibey/tracks/` → `/docs/roadmap/[track-id]/`
- Move `.vibey/sprints/` → `/docs/roadmap/[track-id]/[sprint-id]/`
- Move `.vibey/tasks/` → `/docs/roadmap/[track-id]/[sprint-id]/[task-id]/`
- Detect and move related docs from `docs/development/` → `/context/`
- Generate all `table_of_contents.json` files
- Generate all `.md` views from YAML
- Update all internal path references

**Timeline:** 1 week to develop, test on copy of repo

#### Phase 3: Full Migration (2 months out)

**Approach:** Run migration script, update all tooling.

**Steps:**
1. Create backup of entire repo
2. Run migration script
3. Update all Python scripts to use new paths
4. Update documentation
5. Test all CLI commands
6. Commit migration

**Timeline:** 2-3 days

---

### Specific Design Decisions

#### 1. Location: `.vibey/roadmap/` (Internal) + `/docs/` (User-Facing Copy)

**Recommendation:** Use `.vibey/roadmap/` as source of truth, synchronize user-facing docs to `/docs/`

**Rationale:**
- `.vibey/` is Vibey's internal workspace - users should not navigate here
- Vibey manages roadmap state and execution context in `.vibey/roadmap/`
- User-facing project documentation lives in `/docs/` (or user-configured location)
- Vibey synchronizes relevant documentation from `.vibey/` → `/docs/` as needed

**Structure:**
```
.vibey/
├── config/          # Source configuration
├── templates/       # Source templates
└── roadmap/         # Roadmap hierarchy (SOURCE OF TRUTH)
    ├── table_of_contents.json
    ├── roadmap.yaml
    ├── roadmap.md   # Generated
    └── [track directories...]

docs/                # User-facing documentation (synchronized from .vibey)
├── reference/       # Framework reference (if Vibey framework project)
├── roadmap/         # User-facing roadmap view (COPY from .vibey/roadmap/)
│   ├── roadmap.md   # Synchronized from .vibey
│   └── [selected track/sprint docs...]
└── [user project documentation]
```

**Synchronization Rules:**
- `.vibey/roadmap/` = Internal workspace (all roadmap files, YAML, execution context)
- `/docs/roadmap/` = Public view (selected markdown files synchronized for user review)
- Users never edit `.vibey/` directly
- Vibey CLI commands operate on `.vibey/roadmap/`
- Sync happens automatically or via `vibey roadmap sync-docs`

#### 2. Table of Contents Format: JSON vs YAML vs MD

**Recommendation:** Use JSON

**Rationale:**
- Programmatic consumption (AI, scripts)
- Faster parsing than YAML
- Simpler structure (no complex types)
- Standard for manifests (package.json, tsconfig.json)

**Decision:** ✅ APPROVED

#### 3. Generated Files: MD + JSON

**Recommendation:** Generate both `.md` and `table_of_contents.json`, commit to git

**Rationale:**
- YAML is source of truth (machine-readable, state tracking)
- MD is human-readable view (GitHub rendering, review)
- JSON is navigation aid (programmatic traversal)
- Committing generated files: Easier GitHub browsing, model context, no generation delays

**Generation Triggers:**
- On roadmap state updates (task complete, sprint start, etc.)
- On-demand via `vibey roadmap generate-docs`

**Decision:** ✅ APPROVED - Commit generated files to git

#### 4. Context Directory Structure

**Recommendation:** Allow `/context/` directories at track, sprint, AND task levels

**Rationale:**
- Track-level context: Strategic analyses, architectural decisions, implementation plans
- Sprint-level context: Sprint-wide research, design docs, planning artifacts
- Task-level context: Execution artifacts, task-specific research, analysis during work
- Flat structure within each `/context/` (no sub-directories)
- Easy to list all context for AI loading at each level

**Examples:**

**Track-level context:**
```
.vibey/roadmap/mcp-server/
├── mcp-server.yaml
├── mcp-server.md
└── context/
    ├── MCP_VS_ADAPTER_STRATEGY.md    # Strategic analysis
    ├── mcp-protocol-research.md       # Protocol research
    └── architecture-overview.md       # High-level architecture
```

**Sprint-level context:**
```
.vibey/roadmap/mcp-server/mcp-server-1/
├── mcp-server-1.yaml
├── mcp-server-1.md
└── context/
    ├── sprint-design.md               # Sprint design doc
    └── api-exploration.md             # Sprint-wide API research
```

**Task-level context:**
```
.vibey/roadmap/mcp-server/mcp-server-1/task-001/
├── task-001.yaml
├── task-001.md
└── context/
    ├── mcp-spec-analysis.md           # Task execution research
    ├── sdk-comparison.json            # Task artifacts
    └── implementation-notes.md        # Task decisions
```

**Decision:** ✅ APPROVED - Support context at all three levels

#### 5. Documentation Synchronization Strategy

**Problem:** Users need to see roadmap documentation, but shouldn't navigate `.vibey/` directly.

**Solution:** Vibey synchronizes selected documentation from `.vibey/roadmap/` to user-facing `/docs/` directory.

**Synchronization Mechanism:**

```
Source:              .vibey/roadmap/mcp-server/context/MCP_VS_ADAPTER_STRATEGY.md
Synchronized to:     docs/roadmap/mcp-server/MCP_VS_ADAPTER_STRATEGY.md

Source:              .vibey/roadmap/mcp-server/mcp-server.md
Synchronized to:     docs/roadmap/mcp-server.md
```

**What Gets Synchronized:**
- ✅ Markdown files (`.md`) - Human-readable documentation
- ✅ Completion summaries (`*-COMPLETED.md`)
- ❌ YAML files (`.yaml`) - Internal state, not user-facing
- ❌ JSON files (`.json`) - Internal navigation, not user-facing
- ⚠️ Context files - Selectively synchronized based on configuration

**Synchronization Modes:**

1. **Automatic Sync** (on state changes):
   ```bash
   # Happens automatically when:
   - Task completes
   - Sprint completes
   - Track completes
   - Context added via CLI
   ```

2. **Manual Sync**:
   ```bash
   # Sync all documentation
   vibey roadmap sync-docs --all

   # Sync specific track
   vibey roadmap sync-docs --track mcp-server

   # Sync only summaries
   vibey roadmap sync-docs --summaries-only
   ```

3. **Selective Sync** (configuration-driven):
   ```yaml
   # .vibey/config/project.yaml
   documentation:
     sync:
       enabled: true
       target_dir: docs/roadmap  # Where to sync
       include_patterns:
         - "**/*.md"               # All markdown files
         - "**/*-COMPLETED.md"     # Completion summaries
       exclude_patterns:
         - "**/context/internal-*" # Exclude internal context
       sync_on:
         - task_complete
         - sprint_complete
         - track_complete
         - context_add
   ```

**Sync Manifest** (tracks what's synchronized):
```json
// .vibey/roadmap/.sync-manifest.json
{
  "last_sync": "2025-11-09T14:00:00Z",
  "target_directory": "docs/roadmap",
  "synchronized_files": [
    {
      "source": ".vibey/roadmap/mcp-server/mcp-server.md",
      "target": "docs/roadmap/mcp-server.md",
      "last_synced": "2025-11-09T14:00:00Z",
      "checksum": "abc123"
    },
    {
      "source": ".vibey/roadmap/mcp-server/context/MCP_VS_ADAPTER_STRATEGY.md",
      "target": "docs/roadmap/mcp-server/MCP_VS_ADAPTER_STRATEGY.md",
      "last_synced": "2025-11-09T14:00:00Z",
      "checksum": "def456"
    }
  ]
}
```

**Benefits:**
- Users can browse roadmap docs in familiar `/docs/` location
- `.vibey/` remains internal workspace
- Selective synchronization prevents information overload
- Sync manifest enables incremental updates (only sync changed files)

**Decision:** ✅ APPROVED - Implement synchronization from `.vibey/roadmap/` to `/docs/roadmap/`

#### 6. Project Documentation Tracking

**Recommendation:** Use `.meta.json` sidecar files

**Rationale:**
- Non-intrusive (doesn't modify original files)
- Separate concerns (doc content vs metadata)
- Easy to parse and update programmatically

**Example:**
```
docs/project_documentation/
├── README.md
├── README.md.meta.json    # Metadata
├── API.md
└── API.md.meta.json       # Metadata
```

**Metadata Schema:**
```json
{
  "file": "README.md",
  "tracked_since": "2025-11-09T14:00:00Z",
  "impacted_by": [
    {
      "roadmap_object_type": "task",
      "roadmap_object_id": "mcp-server-1-task-003",
      "roadmap_object_path": "docs/roadmap/mcp-server/mcp-server-1/task-003",
      "change_type": "added_section",
      "section": "MCP Server Setup",
      "description": "Added setup instructions for MCP server",
      "date": "2025-11-09T15:30:00Z",
      "committed": true,
      "commit_sha": "abc123"
    }
  ],
  "current_owners": ["mcp-server", "core-framework"],
  "last_updated_by_roadmap": "2025-11-09T15:30:00Z"
}
```

**CLI Support:**
```bash
# Link project doc to current task
vibey roadmap link-doc README.md --change-type "added_section" --section "MCP Server Setup"

# List all docs impacted by a sprint
vibey roadmap list-docs --sprint mcp-server-1

# Generate documentation changelog
vibey roadmap doc-changelog
```

---

## Migration Plan

### Pre-Migration

**Goals:**
- Validate approach with new track
- Build migration tooling
- Document new structure

**Tasks:**
1. Create new track using hierarchical structure (test pattern)
2. Build migration script (handles all current roadmap objects)
3. Test migration on copy of repo
4. Document new structure in framework docs
5. Update CLI to support both structures (backward compatibility)

**Duration:** 1-2 weeks

### Migration Execution

**Goals:**
- Move all existing roadmap files to hierarchical structure
- Update all tooling and scripts
- Preserve git history where possible

**Steps:**

1. **Backup**
   ```bash
   git checkout -b pre-migration-backup
   git tag pre-migration-backup-2025-11-09
   git checkout main
   git checkout -b migration-hierarchical-roadmap
   ```

2. **Run Migration Script**
   ```bash
   python3 framework/scripts/migrate-roadmap-hierarchy.py --dry-run
   # Review output
   python3 framework/scripts/migrate-roadmap-hierarchy.py --execute
   ```

3. **Update Scripts**
   - `framework/roadmap/*.py` - Update paths
   - `framework/scripts/deploy.py` - Generate hierarchical structure
   - `vibey` CLI - Support new paths

4. **Generate Artifacts**
   ```bash
   vibey roadmap generate-docs --all
   ```

5. **Testing**
   ```bash
   # Test all roadmap commands
   vibey roadmap summarize roadmap
   vibey roadmap summarize track mcp-server
   vibey roadmap context mcp-server-1-task-001

   # Test deployment
   vibey deploy --platform claude-code
   ```

6. **Documentation**
   - Update ARCHITECTURE.md with new structure
   - Update README.md references
   - Create ROADMAP_HIERARCHY.md guide

7. **Commit**
   ```bash
   git add -A
   git commit -m "refactor: Migrate roadmap to hierarchical structure"
   git push origin migration-hierarchical-roadmap
   ```

8. **Review & Merge**
   - Create PR
   - Review changes
   - Merge to main

**Duration:** 2-3 days

### Post-Migration

**Goals:**
- Deprecate old structure support
- Monitor for issues
- Iterate on improvements

**Tasks:**
1. Monitor for path-related issues
2. Gather feedback on usability
3. Iterate on TOC generation
4. Remove backward compatibility after 2 weeks

**Duration:** 2 weeks monitoring

---

## Impact Assessment

### Impact on Existing Workflows

#### Roadmap State Management

**Current:**
```python
# Load track
track_path = '.vibey/tracks/mcp-server.yaml'
track = yaml.load(track_path)

# Load sprint
sprint_path = '.vibey/sprints/mcp-server-1.yaml'
sprint = yaml.load(sprint_path)
```

**After Migration:**
```python
# Load track
track_path = 'docs/roadmap/mcp-server/mcp-server.yaml'
track = yaml.load(track_path)

# Load sprint
sprint_path = 'docs/roadmap/mcp-server/mcp-server-1/mcp-server-1.yaml'
sprint = yaml.load(sprint_path)
```

**Impact:** Path changes only, logic unchanged

#### Context Loading (NEW CAPABILITY)

**After Migration:**
```python
# Load all context for a task
task_context_dir = 'docs/roadmap/mcp-server/mcp-server-1/task-001/context/'
context_files = glob.glob(f'{task_context_dir}/*.md')

# Load hierarchical context (task + sprint + track)
contexts = [
    'docs/roadmap/mcp-server/mcp-server-1/task-001/context/',  # Task level
    'docs/roadmap/mcp-server/mcp-server-1/context/',            # Sprint level (if exists)
    'docs/roadmap/mcp-server/context/',                         # Track level
]
```

**Impact:** New capability for systematic context loading

#### Documentation Generation

**Current:**
```python
# Generate sprint summary manually
summary = generate_summary(sprint_data)
save_to_file('.vibey/sprint_summaries/mcp-server-1-COMPLETED.md', summary)
```

**After Migration:**
```python
# Generate sprint markdown view
sprint_md = generate_sprint_markdown(sprint_yaml)
save_to_file('docs/roadmap/mcp-server/mcp-server-1/mcp-server-1.md', sprint_md)

# Generate TOC
toc = generate_toc(sprint_yaml, parent_path='../mcp-server')
save_to_file('docs/roadmap/mcp-server/mcp-server-1/table_of_contents.json', toc)

# Generate summary on completion
summary = generate_summary(sprint_data)
save_to_file('docs/roadmap/mcp-server/mcp-server-1/mcp-server-1-COMPLETED.md', summary)
```

**Impact:** More files generated, but automated via CLI

---

### Impact on AI Agent Workflows

#### Before Migration

**Problem:** AI must search multiple locations for context.

```
Agent working on mcp-server-1-task-001:
1. Read .vibey/tasks/mcp-server-1-tasks.yaml  # Find task definition
2. Read .vibey/sprints/mcp-server-1.yaml      # Find sprint context
3. Read .vibey/tracks/mcp-server.yaml         # Find track context
4. Search docs/development/ for related docs   # Hope to find relevant files
5. No standard place for task execution context
```

#### After Migration

**Solution:** AI can systematically load context from hierarchy.

```
Agent working on mcp-server-1-task-001:
1. Load docs/roadmap/mcp-server/mcp-server-1/task-001/table_of_contents.json
   → Get task metadata, parent links, files list
2. Load docs/roadmap/mcp-server/mcp-server-1/task-001/task-001.yaml
   → Get task state
3. Load docs/roadmap/mcp-server/mcp-server-1/task-001/context/*
   → Get all task execution context
4. Walk up hierarchy via TOC parent links to get sprint/track context
5. Save new research to docs/roadmap/mcp-server/mcp-server-1/task-001/context/
```

**Benefits:**
- Systematic context discovery
- Standard location for execution artifacts
- Hierarchical context loading (task → sprint → track)
- Can resume work with full context

---

### Impact on CLI Commands

#### New Commands

```bash
# Generate all markdown views and TOCs
vibey roadmap generate-docs --all
vibey roadmap generate-docs --track mcp-server
vibey roadmap generate-docs --sprint mcp-server-1

# Add context to current task
vibey roadmap add-context research.md --task mcp-server-1-task-001
vibey roadmap add-context analysis.md --sprint mcp-server-1
vibey roadmap add-context architecture.md --track mcp-server

# Link project documentation
vibey roadmap link-doc README.md --change-type "added_section"
vibey roadmap list-docs --sprint mcp-server-1
vibey roadmap doc-changelog

# Navigate hierarchy
vibey roadmap show-toc                           # Root TOC
vibey roadmap show-toc --track mcp-server        # Track TOC
vibey roadmap show-toc --sprint mcp-server-1     # Sprint TOC
```

#### Modified Commands

```bash
# Context loading (ENHANCED)
vibey roadmap context <task-id>
# Now also loads sprint and track context, not just task

# Summarize (UNCHANGED, but reads from new locations)
vibey roadmap summarize track <track-id>
vibey roadmap summarize sprint <sprint-id>
```

---

### Impact on Git Repository

#### Repository Size

**Before Migration:**
- YAML files: ~50 files
- Documentation: ~30 files
- Total: ~80 files

**After Migration:**
- YAML files: ~50 files (same)
- Markdown views: ~50 files (generated)
- TOC JSON: ~50 files (generated)
- Documentation: ~30 files
- Total: ~180 files (2.25x increase)

**Mitigation:**
- Generated files are small (1-5 KB)
- Total size increase: ~500 KB (negligible)
- Can `.gitignore` generated files if desired (not recommended)

#### Git History

**Impact:**
- One large migration commit with file moves
- Preserved via `git mv` where possible
- Use `git log --follow` to track moved files

---

## Conclusion

### Summary of Approved Decisions

**✅ APPROVED ARCHITECTURAL DECISIONS:**

1. **ADOPT hierarchical structure** - Benefits outweigh costs for long-term scalability
   - Co-location of related information
   - Natural scalability as roadmap grows
   - Systematic context discovery for AI agents

2. **Use `.vibey/roadmap/` as source of truth** - Keep internal workspace separate from user docs
   - `.vibey/roadmap/` = Internal workspace (all files, YAML state, execution context)
   - `docs/roadmap/` = User-facing view (synchronized markdown files only)
   - Users never navigate `.vibey/` directly

3. **Generate MD + JSON files, commit to git** - Multi-format artifacts for different use cases
   - YAML = Source of truth (machine-readable, state tracking)
   - MD = Human-readable view (GitHub browsing, review)
   - JSON = Navigation aid (programmatic traversal)
   - Commit all generated files for immediate access

4. **Implement table_of_contents.json** - Critical for programmatic navigation
   - JSON format (fast parsing, standard for manifests)
   - Generated automatically on state changes
   - Provides breadcrumbs and hierarchy navigation

5. **Add `/context/` directories at ALL levels** - Standardized context storage
   - Track-level: Strategic analyses, architectural decisions, implementation plans
   - Sprint-level: Sprint-wide research, design docs, planning artifacts
   - Task-level: Execution artifacts, research findings, decision logs
   - Flat structure within each `/context/` (no sub-directories)

6. **Implement documentation synchronization** - Copy from `.vibey/` to `docs/`
   - Automatic sync on state changes (task/sprint/track completion, context add)
   - Manual sync via `vibey roadmap sync-docs`
   - Selective sync based on configuration (include/exclude patterns)
   - Sync manifest tracks what's been synchronized

7. **Track project documentation** - Use `.meta.json` sidecar files
   - Non-intrusive metadata tracking
   - Links project docs to roadmap objects that impact them
   - Enables documentation changelog generation
   - CLI support for linking and querying

8. **Phased migration** - Test with new tracks, migrate existing after validation
   - Phase 1: New tracks use hierarchical structure
   - Phase 2: Build migration script, test on copy
   - Phase 3: Full migration of existing tracks

### Next Steps

**Immediate (Next Session):**
1. ✅ Document approved strategy (COMPLETE)
2. Create implementation plan for Phase 1
3. Design synchronization mechanism in detail
4. Define YAML schema updates for context tracking

**Short Term (1-2 weeks):**
1. Implement hierarchical structure for new tracks
2. Build documentation synchronization system
3. Update roadmap CLI commands (add-context, sync-docs, link-doc)
4. Generate table_of_contents.json on state changes
5. Test with mcp-server track (first new track to use structure)

**Medium Term (1-2 months):**
1. Build migration script for existing tracks
2. Test migration on copy of repository
3. Run migration on main repository
4. Update all Python scripts to use new paths
5. Deprecate old structure support

**Long Term (3+ months):**
1. Monitor usage and gather feedback
2. Iterate on synchronization rules
3. Enhance project documentation tracking
4. Build analytics on documentation impact

### Resolved Questions

1. **Should generated files (MD, JSON) be committed to git?**
   - ✅ **YES** - Commit them for easier GitHub browsing and immediate model context access

2. **Should we support sprint-level `/context/` directories?**
   - ✅ **YES** - Support context at track, sprint, AND task levels for maximum flexibility

3. **Where should roadmap hierarchy live?**
   - ✅ **`.vibey/roadmap/`** - Internal workspace, synchronized to `docs/roadmap/` for users

4. **How deep should task nesting go? (sub-tasks?)**
   - ✅ **Keep flat** - Task level is sufficient, no sub-task nesting

5. **Should TOC JSON include full metadata or just references?**
   - ✅ **Just references + status** - Lightweight, fast to parse, full data in YAML

---

**Document Status:** ✅ APPROVED - Ready for Implementation
**Decision:** ADOPT hierarchical structure with synchronization
**Timeline:** Begin Phase 1 implementation within 1-2 weeks
