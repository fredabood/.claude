# Discovery Mode Audit

**Sprint:** Phase 4.2 - Discovery Output Architecture
**Task:** Task 1 - Audit current discovery mode
**Date:** 2025-12-14
**Status:** Complete

---

## Executive Summary

The Vibey framework currently has **no unified project discovery system**. Discovery functionality exists in fragmented forms:

1. **MCP Tool Discovery** - Discovers agents/workflows/handoffs from markdown files
2. **Audit Operations** - Partial implementation for file analysis
3. **Workflow Documentation** - Detailed codebase audit workflow (unimplemented)

**Key Finding:** There is no `vibey discover` CLI command. The codebase audit workflow exists only as a specification document.

---

## 1. Discovery Commands Audit

### 1.1 CLI Commands

| Command | Exists | Description |
|---------|--------|-------------|
| `vibey discover` | **NO** | No discovery command in CLI |
| `vibey discover show` | **NO** | - |
| `vibey discover diff` | **NO** | - |
| `vibey discover history` | **NO** | - |
| `vibey discover status` | **NO** | - |
| `vibey discover refresh` | **NO** | - |

**Source:** `vibey --help` and `vibey/cli/main.py`

### 1.2 MCP Tools (Discovery-Related)

| Tool | Exists | Description |
|------|--------|-------------|
| `vibey_list_agents` | YES | Lists discovered agents from markdown files |
| `vibey_list_workflows` | YES | Lists discovered workflows from markdown files |
| `vibey_discover_*` (project) | **NO** | No project discovery MCP tools |

**Source:** `vibey/mcp/discovery/` module

---

## 2. What Currently Exists

### 2.1 MCP Tool Discovery (`vibey/mcp/discovery/`)

**Purpose:** Discovers framework assets (agents, workflows, handoffs) from markdown files to generate MCP tools.

**Files:**
- `discovery.py` (243 lines) - Main ToolDiscovery orchestrator with caching
- `agents.py` - AgentDiscovery class
- `workflows.py` - WorkflowDiscovery class
- `handoffs.py` - HandoffDiscovery class
- `generator.py` - ToolGenerator for MCP tool schemas
- `parser.py` - Markdown parsing utilities

**Key Features:**
- Scans `framework/agents/`, `framework/workflows/`, `framework/templates/handoffs/`
- Parses YAML frontmatter and markdown content
- Generates MCP tool definitions
- Caches results with TTL and file-change invalidation

**Limitations:**
- Only discovers framework assets, NOT project codebase
- No CLI interface
- No versioning or history
- No structured output schema

### 2.2 Audit Operations (`vibey/operations/audit/`)

**Purpose:** Partial implementation for codebase file analysis.

**Files:**
- `file_inventory.py` (166 lines) - Generates YAML inventory of files with metadata
- `file_classifier.py` (1,045 lines) - Classifies files by type, purpose, complexity
- `code_auditor.py` (627 lines) - Audits individual files for quality metrics

**Key Features:**
- `FileInventoryConfig` - Configurable directory scanning
- `FileInfo` - Dataclass for file metadata (path, size, mtime, lines)
- `FileClassifier` - Categorizes files (core library, tests, docs, config)
- `CodeAuditor` - Calculates quality scores (documentation, complexity, etc.)

**Limitations:**
- No CLI commands to invoke these modules
- Not integrated into a unified discovery workflow
- No project-level output (only per-file analysis)
- No structured discovery schema

### 2.3 Codebase Audit Workflow (`vibey/content/workflows/planning/codebase-audit-discovery.md`)

**Purpose:** Comprehensive specification for codebase analysis workflow.

**Status:** DOCUMENTATION ONLY - Not implemented as code

**Workflow Steps Defined:**
1. Detect Project Type & Structure (5-10 min)
2. Detect Technology Stack (10-15 min)
3. Review Existing Documentation (5-10 min)
4. Security Scan (10-15 min)
5. Logging & Observability Audit (5-10 min)
6. Test Coverage Analysis (10-15 min)
7. Code Quality Metrics (5-10 min)
8. Identify Patterns & Conventions (5 min)
9. Git History Analysis (10-20 min) - OPTIONAL
10. Generate Audit Report (5-10 min)
11. Pre-fill Project Configuration (5 min)

**Output Artifacts Specified:**
- `docs/codebase-audit-report.md`
- `.claude/project-config.yaml` (pre-filled)

**Limitations:**
- No Python implementation
- No CLI integration
- No structured output schema
- No versioning

---

## 3. Output Format Analysis

### 3.1 Current Output Formats

| Component | Output Format | Structured | Machine-Readable |
|-----------|--------------|------------|------------------|
| MCP Tool Discovery | JSON (MCP protocol) | Yes | Yes |
| File Inventory | YAML | Yes | Yes |
| File Classifier | Dict/YAML | Yes | Yes |
| Code Auditor | Dict/YAML | Yes | Yes |
| Codebase Audit | Markdown (specified) | No | No |

### 3.2 Output Schema Status

- **Formal schema:** NO - No JSON Schema, Pydantic models, or YAML schema
- **Versioning:** NO - No version field in outputs
- **Timestamp:** PARTIAL - File metadata has mtime, no discovery timestamp
- **Git correlation:** NO - No git commit recorded with discovery

---

## 4. Storage Analysis

### 4.1 Current Storage Patterns

| Component | Storage Location | Persistent | Versioned |
|-----------|------------------|------------|-----------|
| MCP Tool Discovery | In-memory cache | No | No |
| File Inventory | `.vibey/roadmap/context/` | Yes | No |
| File Classifier | Not stored | No | No |
| Code Auditor | Not stored | No | No |

### 4.2 Proposed Storage (from Sprint Plan)

```
.vibey/discovery/
├── current.yaml           # Latest discovery
├── history/
│   ├── 2025-12-12T10-00-00.yaml
│   └── 2025-12-11T15-30-00.yaml
└── diffs/
    └── 2025-12-12T10-00-00.diff.yaml
```

**Gap:** This structure does not exist. Discovery outputs are not persisted.

---

## 5. Integration Points

### 5.1 Current Integrations

| Integration | Status | Description |
|-------------|--------|-------------|
| MCP Server → Tool Discovery | YES | MCP server uses ToolDiscovery for dynamic tools |
| CLI → Audit Operations | **NO** | No CLI commands invoke audit modules |
| Session Tracking → Discovery | **NO** | Discovery not linked to sessions |
| Context Management → Discovery | **NO** | No auto-loading of discovery context |

### 5.2 Desired Integrations (from Sprint Plan)

1. **Context Seeding** - Run discovery on project init, seed context
2. **Refresh Triggers** - File changes, dependency updates, git events
3. **Staleness Detection** - Compare current vs last discovery
4. **Session Correlation** - Link discovery version to sessions

---

## 6. Gaps Identified

### 6.1 Critical Gaps

| Gap | Priority | Impact |
|-----|----------|--------|
| No `vibey discover` CLI command | CRITICAL | Users cannot run discovery |
| No project discovery (only framework assets) | CRITICAL | Core feature missing |
| No discovery output schema | HIGH | No structured, versioned outputs |
| No discovery storage/history | HIGH | Cannot track changes over time |

### 6.2 Feature Gaps

| Gap | Priority | Description |
|-----|----------|-------------|
| No technology stack detection | HIGH | Must detect languages, frameworks, DBs |
| No security scanning | MEDIUM | No vulnerability detection |
| No git history analysis | MEDIUM | No sprint/velocity detection |
| No discovery diff | MEDIUM | Cannot compare discovery versions |
| No staleness detection | LOW | Cannot detect when discovery is stale |

### 6.3 Integration Gaps

| Gap | Priority | Description |
|-----|----------|-------------|
| No session correlation | HIGH | Discovery not linked to sessions |
| No MCP tools for discovery | MEDIUM | AI agents cannot invoke discovery |
| No auto-refresh triggers | LOW | Manual refresh only |

---

## 7. Existing Assets to Leverage

### 7.1 Code to Reuse

1. **`vibey/operations/audit/file_inventory.py`**
   - FileInventoryConfig, FileInfo dataclasses
   - Directory scanning with exclusion patterns
   - YAML output generation

2. **`vibey/operations/audit/file_classifier.py`**
   - File type classification
   - Purpose detection (core, test, docs, config)
   - Complexity assessment

3. **`vibey/operations/audit/code_auditor.py`**
   - Quality scoring (documentation, tests, practices)
   - AST analysis for Python files
   - Findings and recommendations

4. **`vibey/mcp/discovery/discovery.py`**
   - Caching pattern with TTL
   - File hash computation for invalidation
   - Stats aggregation

### 7.2 Specifications to Implement

1. **Codebase Audit Workflow** (`codebase-audit-discovery.md`)
   - 11-step discovery process
   - Bash commands for detection
   - Output format specifications

---

## 8. Recommendations

### 8.1 Immediate Actions (Phase 4.2)

1. **Design discovery output schema** (Task 2)
   - Create `DiscoveryOutput` Pydantic model
   - Include metadata (version, timestamp, git commit)
   - Define project, structure, dependencies, patterns sections

2. **Design discovery-to-context integration** (Task 3)
   - Define storage structure in `.vibey/discovery/`
   - Define refresh triggers
   - Define staleness detection algorithm

3. **Implement structured outputs** (Task 4)
   - Create `vibey/operations/discovery/` module
   - Implement analyzers (project, structure, dependencies, patterns)
   - Integrate existing audit code

4. **Implement versioning** (Task 5)
   - Store discovery with timestamps
   - Implement diff capability
   - Add retention policy

5. **Add CLI commands** (Task 6)
   - `vibey discover` - Run discovery
   - `vibey discover show` - Display current
   - `vibey discover diff` - Compare versions
   - `vibey discover history` - List versions
   - `vibey discover status` - Check staleness
   - `vibey discover refresh` - Re-run if stale

### 8.2 Future Considerations (Phase 4.4+)

- MCP tools for discovery
- Auto-refresh on file system changes
- Integration with session management
- Agent context loading with discovery data

---

## Appendix: File Locations

### Discovery-Related Files

```
vibey/
├── mcp/
│   └── discovery/
│       ├── __init__.py
│       ├── discovery.py      # MCP tool discovery orchestrator
│       ├── agents.py         # Agent discovery
│       ├── workflows.py      # Workflow discovery
│       ├── handoffs.py       # Handoff discovery
│       ├── generator.py      # MCP tool generator
│       └── parser.py         # Markdown parser
│
├── operations/
│   └── audit/
│       ├── __init__.py
│       ├── file_inventory.py # File inventory generation
│       ├── file_classifier.py # File classification
│       └── code_auditor.py   # Code quality auditing
│
└── content/
    └── workflows/
        └── planning/
            └── codebase-audit-discovery.md  # Workflow spec (not implemented)
```

### Proposed New Files (Phase 4.2)

```
vibey/
├── operations/
│   └── discovery/
│       ├── __init__.py
│       ├── schema.py         # DiscoveryOutput dataclass
│       ├── serializers.py    # YAML/JSON serialization
│       └── analyzers/
│           ├── project.py    # Project info analyzer
│           ├── structure.py  # Structure analyzer
│           ├── dependencies.py # Dependency analyzer
│           ├── patterns.py   # Pattern analyzer
│           └── conventions.py # Convention analyzer
│
├── cli/
│   └── commands.py           # Add discover command group
│
└── .vibey/
    └── discovery/            # Runtime storage
        ├── current.yaml
        └── history/
```
