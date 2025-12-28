# Task 2.8: Update FILE_TO_ARTIFACT_MAPPING.yaml - Detailed Plan

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | TBD (assign during execution) |
| Sprint | Sprint 2: Data Integrity Validation |
| Type | documentation |
| Complexity | **medium** |
| Priority | medium |
| Estimated Tokens | 3,000 |
| Dependencies | Task 2.7 (Schema Documentation) recommended first |

## Objective

Update FILE_TO_ARTIFACT_MAPPING.yaml to map new Python files to their corresponding database artifacts, update ARTIFACT_RELATIONSHIP_MODEL.md, and document entity relationships between code and data.

## Background

### Problem Statement
As the codebase grows, the mapping between Python source files and the database artifacts they manage can become unclear:
- New operations modules may create/modify database entities
- New models may not be mapped to their storage
- CLI commands may interact with multiple tables
- Relationships between code and data drift from documentation

### Why This Matters
- **Impact Analysis:** Understanding what code affects which data
- **Debugging:** Tracing issues from database to code
- **Refactoring:** Knowing dependencies before making changes
- **Onboarding:** Helping developers understand architecture

## Investigation Steps

### Step 1: Inventory Python Source Files

```bash
# Find all Python files in vibey package
find vibey -name "*.py" -type f | sort

# Categorize by directory
find vibey/cli -name "*.py" | wc -l        # CLI commands
find vibey/operations -name "*.py" | wc -l  # Business logic
find vibey/mcp -name "*.py" | wc -l         # MCP server
find vibey/roadmap -name "*.py" | wc -l     # Models
find vibey/adapters -name "*.py" | wc -l    # Platform adapters
```

### Step 2: Identify Database Interactions

```bash
# Find files importing sqlite
grep -r "sqlite3" vibey/ --include="*.py" -l

# Find files with SQL queries
grep -r "SELECT\|INSERT\|UPDATE\|DELETE" vibey/ --include="*.py" -l

# Find files referencing specific tables
grep -r "FROM tasks\|INTO tasks" vibey/ --include="*.py" -l
grep -r "FROM sprints\|INTO sprints" vibey/ --include="*.py" -l
grep -r "FROM tracks\|INTO tracks" vibey/ --include="*.py" -l
```

### Step 3: Map Operations to Entities

For each operations module, identify:
- Which database tables it reads from
- Which tables it writes to
- Which views it uses
- Which triggers it depends on

```bash
# Example: Check roadmap operations
grep -r "sqlite\|\.db" vibey/operations/roadmap/ --include="*.py"
```

### Step 4: Document Model-Table Relationships

```bash
# Find model definitions
grep -r "class.*Model\|dataclass\|@dataclass" vibey/roadmap/models/ --include="*.py" -A 5
```

### Step 5: Map CLI Commands to Database

```bash
# For each CLI command group, identify database interactions
grep -r "def.*command\|@click" vibey/cli/ --include="*.py" -A 10 | grep -E "db\.|sqlite|query"
```

### Step 6: Review Existing Mapping

```bash
# Find existing artifact mapping
find . -name "*ARTIFACT*" -o -name "*artifact*" | grep -i map
find . -name "*FILE_TO*" -o -name "*file_to*"

# Review current state
cat docs/architecture/FILE_TO_ARTIFACT_MAPPING.yaml
# or wherever it exists
```

## Mapping Structure

### FILE_TO_ARTIFACT_MAPPING.yaml Template

```yaml
# File to Database Artifact Mapping
# Maps Python source files to database tables, views, and triggers they interact with
# Last Updated: [date]

version: "2.5.0"

# Mapping Categories
categories:
  - operations     # Core business logic
  - cli           # Command-line interface
  - models        # Data models
  - mcp           # MCP server tools

# Operations Mappings
operations:
  vibey/operations/roadmap/tracks.py:
    reads:
      - tracks
      - sprints  # for cascading operations
    writes:
      - tracks
    views_used:
      - track_summary
    triggers_affected:
      - trg_track_updated
    description: "Track CRUD operations"

  vibey/operations/roadmap/sprints.py:
    reads:
      - sprints
      - tasks  # for progress calculation
    writes:
      - sprints
    views_used:
      - sprint_progress
    description: "Sprint CRUD operations"

  vibey/operations/roadmap/tasks.py:
    reads:
      - tasks
      - sprints  # for validation
    writes:
      - tasks
    views_used:
      - active_tasks
      - blocked_tasks
    description: "Task CRUD operations"

# CLI Mappings
cli:
  vibey/cli/commands/roadmap.py:
    operations_used:
      - vibey/operations/roadmap/tracks.py
      - vibey/operations/roadmap/sprints.py
      - vibey/operations/roadmap/tasks.py
    direct_db_access: false
    description: "Roadmap CLI commands"

# Model Mappings
models:
  vibey/roadmap/models/track.py:
    table: tracks
    columns_mapped:
      - id -> id
      - name -> name
      - status -> status
    description: "Track data model"

  vibey/roadmap/models/sprint.py:
    table: sprints
    columns_mapped:
      - id -> id
      - name -> name
      - track_id -> track_id
    description: "Sprint data model"

# MCP Tool Mappings
mcp:
  vibey/mcp/tools/roadmap.py:
    tables_accessed:
      - tracks
      - sprints
      - tasks
    operations_used:
      - vibey/operations/roadmap/*.py
    description: "MCP roadmap tools"

# Reverse Mapping (Table to Files)
reverse_mapping:
  tracks:
    primary_operations:
      - vibey/operations/roadmap/tracks.py
    cli_commands:
      - vibey/cli/commands/roadmap.py
    models:
      - vibey/roadmap/models/track.py
    mcp_tools:
      - vibey/mcp/tools/roadmap.py

  sprints:
    primary_operations:
      - vibey/operations/roadmap/sprints.py
    # ... etc
```

## ARTIFACT_RELATIONSHIP_MODEL.md Structure

```markdown
# Artifact Relationship Model

## Overview
This document describes the relationships between code artifacts and data artifacts
in the Vibey framework.

## Architecture Layers

### Layer 1: CLI (User Interface)
```
vibey/cli/
├── commands/           # Command implementations
│   ├── roadmap.py     → Operations layer
│   ├── deploy.py      → Adapters
│   └── docs.py        → Docs operations
└── main.py            # Entry point
```

### Layer 2: Operations (Business Logic)
```
vibey/operations/
├── roadmap/           # Roadmap domain
│   ├── tracks.py     → Track model, tracks table
│   ├── sprints.py    → Sprint model, sprints table
│   └── tasks.py      → Task model, tasks table
└── docs/              # Documentation domain
```

### Layer 3: Models (Data Structures)
```
vibey/roadmap/models/
├── track.py          ↔ tracks table
├── sprint.py         ↔ sprints table
└── task.py           ↔ tasks table
```

### Layer 4: Storage (Database)
```
.vibey/roadmap/roadmap.db
├── Tables (39)        ← Models layer
├── Views (25)         ← Operations layer (queries)
└── Triggers (X)       ← Database integrity
```

## Relationship Diagram

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│    CLI      │────▶│  Operations  │────▶│   Models    │
└─────────────┘     └──────────────┘     └─────────────┘
                           │                    │
                           ▼                    ▼
                    ┌──────────────┐     ┌─────────────┐
                    │    Views     │     │   Tables    │
                    └──────────────┘     └─────────────┘
```

## Entity Relationships

### Track Entity
- **Model:** `vibey/roadmap/models/track.py`
- **Table:** `tracks`
- **Operations:** `vibey/operations/roadmap/tracks.py`
- **CLI:** `vibey roadmap track *`
- **MCP:** `mcp_track_*` tools

### Sprint Entity
[Similar structure]

### Task Entity
[Similar structure]
```

## Verification Steps

1. **File Inventory:** List all Python files in vibey package
2. **Database Scan:** Identify files with database interactions
3. **Pattern Analysis:** Categorize by interaction type (read/write)
4. **Existing Review:** Check current mapping documentation
5. **Gap Identification:** Find unmapped files and tables
6. **Documentation:** Update YAML mapping and relationship model

## Deliverables

### 1. FILE_TO_ARTIFACT_MAPPING.yaml (Updated)

Complete mapping covering:
- All operations modules and their table interactions
- All CLI commands and their operation dependencies
- All models and their table mappings
- All MCP tools and their data access
- Reverse mapping (table to files)

### 2. ARTIFACT_RELATIONSHIP_MODEL.md (Updated)

- Architecture layer diagram
- Entity relationship descriptions
- Dependency flow documentation
- Visual diagrams (ASCII/Mermaid)

### 3. MAPPING_CHANGES.md

```markdown
# Artifact Mapping Changes

## New Mappings Added
| File | Artifacts | Interaction Type |
|------|-----------|------------------|
| ... | ... | read/write |

## Modified Mappings
| File | Previous | Current | Reason |
|------|----------|---------|--------|
| ... | ... | ... | ... |

## Unmapped Files (Require Investigation)
| File | Notes |
|------|-------|
| ... | ... |

## Unmapped Tables (No Code Reference)
| Table | Notes |
|-------|-------|
| ... | ... |
```

## Acceptance Criteria

- [ ] All Python files in vibey/ are mapped or explicitly marked as no-db-interaction
- [ ] All database tables have at least one file mapping
- [ ] Read vs write interactions are distinguished
- [ ] CLI → Operations → Models → Tables chain is documented
- [ ] MCP tools are mapped to their data access
- [ ] Reverse mapping allows tracing from table to code
- [ ] ARTIFACT_RELATIONSHIP_MODEL.md reflects current architecture

## Estimated Time

- File inventory: 20 minutes
- Database interaction scanning: 40 minutes
- Mapping creation: 60 minutes
- Relationship model update: 40 minutes
- Validation: 20 minutes
- **Total: ~3 hours**

## Notes

- Focus on files that interact with `.vibey/roadmap/roadmap.db`
- Include indirect interactions (via imported modules)
- Note any files that bypass operations layer to access DB directly
- Flag architectural concerns (e.g., CLI directly querying DB)
- Consider generating mapping automatically from code analysis
- Coordinate with Task 2.7 (Schema Documentation) for table information
