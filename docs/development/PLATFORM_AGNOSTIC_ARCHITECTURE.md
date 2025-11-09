# Platform-Agnostic Architecture

**Document Version:** 1.0
**Created:** 2025-11-09
**Sprint:** core-framework-2
**Status:** Active Design Document

---

## Executive Summary

This document defines the platform-agnostic architecture for the Vibey Agent Framework, establishing `.vibey/` as the permanent, version-controlled source of truth that enables deployment to multiple AI coding platforms (Claude Code, Goose, Cursor, and future platforms).

**Key Decisions:**
1. **Source vs Deployment Separation:** `.vibey/` (source) generates `.claude/`, `.goose/`, `.cursor/` (deployments)
2. **Dual System Design:** YAML for state tracking, Markdown for rich context
3. **Platform Adapter Pattern:** Each platform gets a dedicated adapter for deployment generation
4. **Permanent Home:** `.vibey/` is never deleted, always committed to git

---

## Problem Statement

### Current Issues

**1. Platform Lock-in:**
- Framework tightly coupled to Claude Code
- All files in `.claude/` directory (Claude-specific)
- No separation between core logic and platform-specific deployment
- Porting to Goose/Cursor requires duplicating entire framework

**2. Documentation Duplication:**
- CLAUDE.md manually maintained
- Agent instructions duplicated across files
- No single source of truth
- Changes require updating multiple locations

**3. Context Management:**
- Loading all sprint dependencies overwhelms context window
- No intelligent summarization
- Projects with >10 sprints become unusable
- Distance-based loading not implemented

**4. Multi-Platform Impossibility:**
- Can't deploy to multiple platforms simultaneously
- No adapter pattern for platform differences
- Manual porting required for each platform

### Impact

- ❌ **Locked to Claude Code** - Can't expand to other platforms
- ❌ **Manual maintenance** - High effort, error-prone
- ❌ **Context explosion** - Large projects hit limits
- ❌ **User friction** - Framework-specific files pollute user repos

---

## Solution Overview

### Core Concept

**`.vibey/` becomes the platform-agnostic source of truth**

```
┌─────────────────────────────────────────────────────┐
│                    .vibey/                          │
│         Platform-Agnostic Source                    │
│                                                     │
│  ├── config/         (What to deploy)              │
│  ├── roadmap/        (Project state - YAML)        │
│  ├── sprint_docs/    (Rich context - Markdown)     │
│  ├── summaries/      (Auto-generated)              │
│  └── templates/      (User-customizable)           │
└─────────────────────────────────────────────────────┘
                          │
                          │ Generate
                          ▼
        ┌─────────────────┬─────────────────┬─────────────────┐
        │   .claude/      │   .goose/       │   .cursor/      │
        │  (Generated)    │  (Generated)    │  (Generated)    │
        │  CLAUDE.md      │  README.md      │  .cursorrules   │
        │  agents/        │  extensions/    │  agents/        │
        │  workflows/     │  recipes/       │  workflows/     │
        └─────────────────┴─────────────────┴─────────────────┘
```

### Design Principles

**1. Separation of Concerns**
- **Source:** `.vibey/` (platform-agnostic, version-controlled)
- **Deployment:** `.claude/`, `.goose/`, `.cursor/` (generated, gitignored)
- **State:** `.vibey/roadmap/` (YAML, machine-readable)
- **Context:** `.vibey/sprint_docs/` (Markdown, human-readable)

**2. Single Source of Truth**
- All configuration in `.vibey/config/`
- Templates in `.vibey/templates/`
- Platform deployments generated on-demand
- No manual editing of generated files

**3. Never Lose Context**
- Sprint documentation (Markdown) never regenerated
- YAML state and Markdown context coexist
- YAML references Markdown via `documentation.files` field
- Both committed to git, non-overlapping purposes

**4. Intelligent Context Loading**
- Distance-based context selection
- Auto-generated summaries for distant dependencies
- Hierarchical loading strategy
- 80-90% reduction in context size

**5. Adapter Pattern**
- Platform-specific adapters in `framework/platform_adapters/`
- Each adapter knows how to generate deployment for its platform
- Core framework unchanged when adding platforms

---

## Directory Structure

### Complete `.vibey/` Layout

```
.vibey/
├── config/                          # Single source of truth (YAML)
│   ├── project.yaml                 # Project metadata, tech stack, team
│   ├── framework.yaml               # Framework settings, orchestration mode
│   ├── agents/                      # Agent definitions (one YAML per agent)
│   │   ├── coordinator.yaml
│   │   ├── web-developer.yaml
│   │   ├── ml-engineer.yaml
│   │   ├── security-engineer.yaml
│   │   ├── performance-engineer.yaml
│   │   ├── observability-engineer.yaml
│   │   ├── docs-writer.yaml
│   │   ├── diagram-generator.yaml
│   │   ├── git-committer.yaml
│   │   ├── sprint-planner.yaml
│   │   ├── researcher.yaml
│   │   └── vibey-manager.yaml       # (12 agents total)
│   ├── workflows/                   # Workflow definitions (one YAML per workflow)
│   │   ├── sprint-planning.yaml
│   │   ├── feature-development.yaml
│   │   ├── security-audit.yaml
│   │   ├── performance-optimization.yaml
│   │   ├── logging-instrumentation.yaml
│   │   ├── ml-model-development.yaml
│   │   ├── frontend-development.yaml
│   │   ├── infrastructure-setup.yaml
│   │   └── ...                      # (16 workflows total)
│   └── quality-gates.yaml           # Quality gate definitions
│
├── roadmap/                         # Roadmap system (YAML state - existing)
│   ├── roadmap.yaml                 # Main roadmap file
│   ├── tracks/                      # Track definitions
│   │   ├── core-framework.yaml
│   │   ├── roadmap-system.yaml
│   │   ├── roadmap-integration.yaml
│   │   ├── goose-port.yaml
│   │   └── multi-platform.yaml
│   ├── sprints/                     # Sprint state files
│   │   ├── core-framework-2.yaml
│   │   ├── core-framework-3.yaml
│   │   └── ...
│   └── tasks/                       # Task state files (optional, for large sprints)
│       └── ...
│
├── sprint_docs/                     # Sprint documentation (Markdown context)
│   └── <track-id>/                  # e.g., core-framework/
│       └── <sprint-id>/             # e.g., core-framework-2/
│           ├── plan.md              # Original sprint plan (NEVER regenerated)
│           ├── architecture.md      # Architecture decisions (iterated during dev)
│           ├── learnings.md         # Lessons learned (accumulated)
│           ├── retrospective.md     # Sprint retrospective (end of sprint)
│           └── notes/               # Additional context (optional)
│               └── *.md
│
├── summaries/                       # Auto-generated summaries (gitignored)
│   ├── dependency_summaries/        # Task-level summaries
│   │   └── <task-id>.md             # e.g., core-framework-2-task-003.md
│   └── task_summaries/              # Sprint-level summaries
│       └── <sprint-id>.md           # e.g., core-framework-2.md
│
├── templates/                       # User-customizable templates (Jinja2)
│   ├── claude.md.j2                 # CLAUDE.md template
│   ├── goose.md.j2                  # Goose README.md template
│   ├── cursor.md.j2                 # Cursor .cursorrules template
│   ├── agent.md.j2                  # Agent instruction template
│   └── workflow.md.j2               # Workflow instruction template
│
├── .cache/                          # Performance cache (gitignored - existing)
│   └── ...
│
└── .gitignore                       # Ignore generated files
```

### Platform Deployments (Generated, Gitignored)

```
.claude/                             # Generated for Claude Code
├── CLAUDE.md                        # Generated from .vibey/templates/claude.md.j2
├── agents/                          # Generated from .vibey/config/agents/*.yaml
│   ├── coordinator.md
│   ├── web-developer.md
│   └── ...
├── workflows/                       # Generated from .vibey/config/workflows/*.yaml
│   ├── sprint-planning.md
│   ├── feature-development.md
│   └── ...
└── project-config.yaml              # Generated from .vibey/config/project.yaml

.goose/                              # Generated for Goose
├── README.md                        # Generated from .vibey/templates/goose.md.j2
├── extensions/                      # Generated from .vibey/config/agents/*.yaml
│   ├── coordinator.toml
│   ├── web-developer.toml
│   └── ...
└── recipes/                         # Generated from .vibey/config/workflows/*.yaml
    ├── sprint-planning.yaml
    ├── feature-development.yaml
    └── ...

.cursor/                             # Generated for Cursor (future)
├── .cursorrules                     # Generated from .vibey/templates/cursor.md.j2
└── agents/                          # Generated from .vibey/config/agents/*.yaml
    ├── coordinator.md
    └── ...
```

---

## File Purposes and Ownership

### `.vibey/config/` - Configuration Source

**Purpose:** Platform-agnostic definitions of agents, workflows, and settings

**Ownership:** User maintains, committed to git

**File Types:**
- `project.yaml` - Project metadata, tech stack, team info
- `framework.yaml` - Framework settings, orchestration mode, context loading
- `agents/*.yaml` - Agent metadata (capabilities, triggers, tech stack)
- `workflows/*.yaml` - Workflow metadata (steps, agents, duration)
- `quality-gates.yaml` - Quality gate definitions

**Key Insight:** YAML is **metadata-focused**, not full instructions. Templates generate rich instructions from this metadata.

### `.vibey/roadmap/` - State Tracking (YAML)

**Purpose:** Machine-readable state for roadmap, tracks, sprints, tasks

**Ownership:** Updated by roadmap CLI, committed to git

**File Types:**
- `roadmap.yaml` - Main roadmap state
- `tracks/*.yaml` - Track state (status, progress, dependencies)
- `sprints/*.yaml` - Sprint state (status, tasks, gates)
- `tasks/*.yaml` - Task state (optional, for large sprints)

**Characteristics:**
- ✅ Deterministic state (status, completion %, dependencies)
- ✅ Machine-readable and queryable
- ✅ Updated by CLI commands (`roadmap update`, `roadmap query`)
- ✅ Never regenerated from scratch (incremental updates only)

### `.vibey/sprint_docs/` - Rich Context (Markdown)

**Purpose:** Human and AI-readable context for sprints

**Ownership:** Iterated during development, committed to git

**File Types:**
- `plan.md` - Original sprint plan
- `architecture.md` - Architecture decisions
- `learnings.md` - Lessons learned
- `retrospective.md` - Final retrospective

**Characteristics:**
- ✅ Rich, narrative context
- ✅ **NEVER regenerated** (accumulated knowledge)
- ✅ Iterated during sprint (living documents)
- ✅ Human and AI readable
- ✅ Referenced by YAML via `documentation.files` field

**Critical:** Markdown preserves context that would be lost if only YAML existed.

### `.vibey/summaries/` - Auto-Generated (Gitignored)

**Purpose:** LLM-generated summaries for context loading

**Ownership:** Auto-generated by framework, gitignored

**File Types:**
- `dependency_summaries/<task-id>.md` - Task summaries (~200 words)
- `task_summaries/<sprint-id>.md` - Sprint summaries

**Characteristics:**
- ✅ Generated on-demand
- ✅ Cached for performance
- ✅ Can be regenerated anytime
- ✅ Used for distance-based context loading

### `.vibey/templates/` - User-Customizable (Jinja2)

**Purpose:** Templates for generating platform-specific files

**Ownership:** Framework provides defaults, users can customize

**File Types:**
- `claude.md.j2` - CLAUDE.md template
- `goose.md.j2` - Goose README template
- `cursor.md.j2` - Cursor .cursorrules template
- `agent.md.j2` - Agent instruction template
- `workflow.md.j2` - Workflow instruction template

**Variables Available:**
```jinja2
{{ project.name }}
{{ project.type }}
{{ framework.orchestration.mode }}
{{ agents }}  # List of agent configs
{{ workflows }}  # List of workflow configs
{{ quality_gates }}
{{ current_sprint }}  # Dynamic sprint context
{{ active_tasks }}  # Dynamic task list
```

---

## YAML vs Markdown: Design Rationale

### Why Two Systems?

**Problem:** You need both deterministic state AND rich context.

**YAML (State):**
- Sprint status, completion %, dependencies
- Machine-queryable: "What sprints block this one?"
- CLI updates: `roadmap update --complete-task X`
- Deterministic: status = "completed"

**Markdown (Context):**
- Architecture decisions: "Why did we choose X over Y?"
- Learnings: "Performance issue with Z, solved by W"
- Examples, code snippets, diagrams
- Narrative explanations

**Both Required:**
- YAML: "Sprint 2 blocks Sprint 1" ← State
- Markdown: "Sprint 1 needs config system from Sprint 2 because..." ← Context

### How They Connect

**YAML references Markdown:**
```yaml
sprint:
  id: core-framework-2
  documentation:
    files:
      plan: .vibey/sprint_docs/core-framework/core-framework-2/plan.md
      architecture: .vibey/sprint_docs/core-framework/core-framework-2/architecture.md
      learnings: .vibey/sprint_docs/core-framework/core-framework-2/learnings.md
```

**Agents load both:**
1. Query YAML for dependencies: "What do I need?"
2. Load Markdown for context: "How do I build it?"

### Migration Path

**Existing:** `docs/sprints/*.md` (Markdown-only, no YAML state)

**New:**
- `.vibey/roadmap/sprints/*.yaml` (State)
- `.vibey/sprint_docs/*/*.md` (Context)

**Migration:**
1. Parse existing sprint Markdown
2. Extract state → YAML
3. Preserve context → Markdown
4. Link them via `documentation.files`

---

## Platform Adapter Pattern

### Concept

Each platform has unique requirements:
- **Claude Code:** CLAUDE.md, agents/*.md, workflows/*.md
- **Goose:** README.md, extensions/*.toml, recipes/*.yaml
- **Cursor:** .cursorrules, agents/*.md

**Solution:** Platform-specific adapters generate deployments from `.vibey/config/`.

### Adapter Interface

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any

class PlatformAdapter(ABC):
    """Base class for platform-specific deployment adapters"""

    def __init__(self, vibey_dir: Path = Path(".vibey")):
        self.vibey_dir = vibey_dir
        self.config_dir = vibey_dir / "config"
        self.templates_dir = vibey_dir / "templates"

    @abstractmethod
    def get_deployment_dir(self) -> Path:
        """Return the platform's deployment directory (e.g., .claude/, .goose/)"""
        pass

    @abstractmethod
    def generate_instructions_file(self) -> str:
        """Generate main instructions file (CLAUDE.md, README.md, .cursorrules)"""
        pass

    @abstractmethod
    def generate_agents(self) -> Dict[str, str]:
        """Generate agent files for this platform"""
        pass

    @abstractmethod
    def generate_workflows(self) -> Dict[str, str]:
        """Generate workflow files for this platform"""
        pass

    def deploy(self, clean: bool = False) -> None:
        """
        Generate complete deployment for this platform.

        Args:
            clean: If True, delete existing deployment before generating
        """
        deployment_dir = self.get_deployment_dir()

        if clean and deployment_dir.exists():
            shutil.rmtree(deployment_dir)

        deployment_dir.mkdir(exist_ok=True)

        # Generate instructions file
        instructions = self.generate_instructions_file()
        instructions_path = deployment_dir / self.get_instructions_filename()
        instructions_path.write_text(instructions)

        # Generate agents
        agents_dir = deployment_dir / "agents"
        agents_dir.mkdir(exist_ok=True)
        for agent_id, content in self.generate_agents().items():
            agent_path = agents_dir / self.get_agent_filename(agent_id)
            agent_path.write_text(content)

        # Generate workflows
        workflows_dir = deployment_dir / self.get_workflows_dirname()
        workflows_dir.mkdir(exist_ok=True)
        for workflow_id, content in self.generate_workflows().items():
            workflow_path = workflows_dir / self.get_workflow_filename(workflow_id)
            workflow_path.write_text(content)
```

### Claude Code Adapter (Example)

```python
class ClaudeAdapter(PlatformAdapter):
    """Adapter for Claude Code platform"""

    def get_deployment_dir(self) -> Path:
        return Path(".claude")

    def get_instructions_filename(self) -> str:
        return "CLAUDE.md"

    def generate_instructions_file(self) -> str:
        """Generate CLAUDE.md from template"""
        template = self.load_template("claude.md.j2")
        context = {
            "project": self.load_project_config(),
            "framework": self.load_framework_config(),
            "agents": self.load_all_agents(),
            "workflows": self.load_all_workflows(),
            "quality_gates": self.load_quality_gates(),
        }
        return template.render(context)

    def generate_agents(self) -> Dict[str, str]:
        """Generate agent/*.md files"""
        agents = {}
        agent_template = self.load_template("agent.md.j2")

        for agent_file in (self.config_dir / "agents").glob("*.yaml"):
            agent_config = self.load_yaml(agent_file)
            agent_id = agent_config["agent"]["id"]
            agents[agent_id] = agent_template.render(agent=agent_config)

        return agents

    def get_agent_filename(self, agent_id: str) -> str:
        return f"{agent_id}.md"

    # ... similar for workflows
```

### Adding New Platforms

**To add Goose support:**
1. Create `framework/platform_adapters/goose_adapter.py`
2. Implement `GooseAdapter(PlatformAdapter)`
3. Create `.vibey/templates/goose.md.j2`
4. Run: `vibey deploy --platform goose`

**No changes to:**
- Core framework
- Existing adapters
- `.vibey/config/` structure

---

## Context Loading Strategy

### The Problem

**Context Explosion:** Loading all sprint plans for dependencies overwhelms context window.

**Example:**
- Current task depends on 3 tasks
- Each dependency depends on 3 more (9 total)
- Each plan is 30KB
- Total: 12 × 30KB = 360KB ❌

### The Solution

**Hierarchical, Distance-Based Loading**

```
Distance 0 (current):     FULL context (~30KB)
Distance 1 (direct deps): SUMMARY context (~20KB)
Distance 2+ (indirect):   MINIMAL context (~5KB)

Result: 1×30KB + 3×20KB + 9×5KB = 135KB ✅ (62% reduction)
```

### Distance Calculation

```python
def calculate_distances(task_id: str) -> Dict[str, int]:
    """
    Calculate dependency distances using BFS.

    Returns:
        Dict[task_id -> distance]
    """
    distances = {task_id: 0}
    queue = [(task_id, 0)]
    visited = set()

    while queue:
        current_id, current_dist = queue.pop(0)

        if current_id in visited:
            continue

        visited.add(current_id)

        # Get dependencies for current task
        deps = get_task_dependencies(current_id)

        for dep_id in deps:
            new_dist = current_dist + 1

            if dep_id not in distances or new_dist < distances[dep_id]:
                distances[dep_id] = new_dist
                queue.append((dep_id, new_dist))

    return distances
```

### Context Modes

**MINIMAL (Distance 2+):**
```markdown
**Task:** core-framework-1-task-003
**Title:** Implement config validation
**Status:** completed
**Blocking:** Provides config schema required by task core-framework-2-task-002
```

**SUMMARY (Distance 1):**
```markdown
# Task: Implement config validation

**ID:** core-framework-1-task-003
**Status:** completed

## Summary
Implemented comprehensive YAML schema validation for project.yaml and framework.yaml.
Provides validation functions used by deployment system. Catches configuration errors
early before deployment.

## Key Decisions
- Used JSON Schema for validation (industry standard)
- Strict mode by default, lenient mode optional
- Detailed error messages with line numbers

## Dependencies Provided
- `validate_project_config(yaml_path)` - Used by task 002
- `validate_framework_config(yaml_path)` - Used by task 002
```

**FULL (Distance 0):**
```markdown
# [Complete sprint plan with architecture, code examples, etc.]
```

### Implementation

See: `framework/roadmap/context_loader.py` (Task 3)

---

## Migration Strategy

### Current State

```
framework/
├── agents/
│   └── *.md              # Agent instructions (Markdown)
├── workflows/
│   └── *.md              # Workflow instructions (Markdown)
├── commands/
│   └── vibey.md          # Main command
└── config/
    └── schema.yaml       # Config schema

docs/sprints/
└── *.md                  # Sprint plans (Markdown-only)

.claude/
├── CLAUDE.md             # Manually maintained
└── project-config.yaml   # User's config
```

### Target State

```
.vibey/
├── config/               # ← Generated from framework/
│   ├── project.yaml      # ← Converted from .claude/project-config.yaml
│   ├── framework.yaml    # ← New (default settings)
│   ├── agents/           # ← Converted from framework/agents/*.md
│   └── workflows/        # ← Converted from framework/workflows/*.md
├── roadmap/              # ← Existing (already correct)
├── sprint_docs/          # ← Migrated from docs/sprints/
├── summaries/            # ← Generated (gitignored)
└── templates/            # ← Defaults from framework/templates/

.claude/                  # ← Generated (gitignored)
├── CLAUDE.md             # ← Generated from .vibey/templates/claude.md.j2
├── agents/               # ← Generated from .vibey/config/agents/
└── workflows/            # ← Generated from .vibey/config/workflows/
```

### Migration Steps

**Phase 1: Create `.vibey/` Alongside Existing** (Task 10)

```bash
python3 framework/scripts/migrate-to-vibey.py

# Creates:
# - .vibey/config/ from framework/
# - .vibey/sprint_docs/ from docs/sprints/
# - .vibey/templates/ (defaults)
# Does NOT delete anything yet
```

**Phase 2: Test Deployment Generation**

```bash
vibey deploy --platform claude-code

# Generates .claude/ from .vibey/
# Compare to existing .claude/
# Verify equivalence
```

**Phase 3: Dual Operation** (for user projects)

- Both `.claude/` and `.vibey/` exist
- Commands work with both
- Deprecation warnings for old structure
- Users migrate when ready

**Phase 4: Cutover** (framework repository)

- Remove `framework/agents/`, `framework/workflows/`
- Update build process
- `.vibey/` becomes source
- Generate platform deployments on release

### Backward Compatibility

**For Vibey Framework:**
- Migration is immediate (we control it)
- Framework generates its own deployments

**For User Projects:**
- Detection: Check for `.vibey/roadmap.yaml`
- If missing: Offer to migrate
- If present: Use `.vibey/` exclusively
- Old structure: Still supported for 1-2 releases

---

## File Naming Conventions

### `.vibey/config/`

**Project and Framework:**
- `project.yaml` (singular)
- `framework.yaml` (singular)
- `quality-gates.yaml` (plural, hyphenated)

**Agents:**
- `<agent-id>.yaml` (kebab-case)
- Examples: `web-developer.yaml`, `ml-engineer.yaml`, `vibey-manager.yaml`

**Workflows:**
- `<workflow-id>.yaml` (kebab-case)
- Examples: `sprint-planning.yaml`, `feature-development.yaml`

### `.vibey/roadmap/`

**Main Files:**
- `roadmap.yaml` (singular)

**Subdirectories:**
- `tracks/<track-id>.yaml` - Examples: `core-framework.yaml`, `goose-port.yaml`
- `sprints/<sprint-id>.yaml` - Examples: `core-framework-2.yaml`
- `tasks/<task-id>.yaml` - Examples: `core-framework-2-task-001.yaml`

### `.vibey/sprint_docs/`

**Structure:**
- `<track-id>/<sprint-id>/<file>.md`
- Examples:
  - `core-framework/core-framework-2/plan.md`
  - `core-framework/core-framework-2/architecture.md`
  - `goose-port/goose-port-1/learnings.md`

### `.vibey/summaries/`

**Auto-Generated:**
- `dependency_summaries/<task-id>.md`
- `task_summaries/<sprint-id>.md`

### `.vibey/templates/`

**Templates:**
- `<platform>.md.j2` - Instructions file template
- `agent.md.j2` - Agent instruction template
- `workflow.md.j2` - Workflow instruction template

---

## Gitignore Strategy

### `.vibey/.gitignore`

```gitignore
# Performance cache (implementation-specific)
.cache/
__pycache__/
*.pyc
*.pyo

# Auto-generated summaries (can be regenerated)
summaries/

# Temporary files
*.tmp
*.swp
.DS_Store
```

### Root `.gitignore`

```gitignore
# Platform deployments (generated from .vibey/)
.claude/
.goose/
.cursor/

# Vibey framework internals (if framework embedded)
# (Only if distributing framework with project)
framework/.cache/
framework/**/__pycache__/
framework/**/*.pyc
```

### What Gets Committed

**✅ Committed to Git:**
- `.vibey/config/` - Source of truth
- `.vibey/roadmap/` - Project state
- `.vibey/sprint_docs/` - Accumulated context
- `.vibey/templates/` - Customizations
- `.vibey/.gitignore` - Ignore rules

**❌ Gitignored:**
- `.vibey/.cache/` - Performance cache
- `.vibey/summaries/` - Auto-generated
- `.claude/`, `.goose/`, `.cursor/` - Generated deployments

---

## Security and Secrets

### Principles

1. **No secrets in `.vibey/config/`** - Configs are committed to git
2. **Use environment variables** - For API keys, credentials
3. **Reference, don't embed** - Config points to secrets, doesn't contain them

### Example

**❌ Bad:**
```yaml
# .vibey/config/project.yaml
project:
  api_key: "sk-1234567890abcdef"  # ← NEVER DO THIS
```

**✅ Good:**
```yaml
# .vibey/config/project.yaml
project:
  api_key_env: "VIBEY_API_KEY"  # ← Reference environment variable
```

**Template Usage:**
```jinja2
{# .vibey/templates/claude.md.j2 #}
{% if project.api_key_env %}
API Key: Load from environment variable `{{ project.api_key_env }}`
{% endif %}
```

### Platform-Specific Secrets

Some platforms (Goose) may support `.env` files:

```
.goose/.env  ← Gitignored
.cursor/.env ← Gitignored
```

These are generated deployments, never committed.

---

## Performance Considerations

### Caching Strategy

**What to Cache:**
- Parsed YAML configs (`.vibey/.cache/config/`)
- Rendered templates (`.vibey/.cache/templates/`)
- Generated summaries (`.vibey/summaries/`)

**Cache Invalidation:**
```python
def get_cache_key(file_path: Path) -> str:
    """Generate cache key from file path and modification time"""
    stat = file_path.stat()
    return f"{file_path}:{stat.st_mtime}"

def load_cached(file_path: Path, cache_dir: Path):
    cache_key = get_cache_key(file_path)
    cache_file = cache_dir / f"{cache_key}.cache"

    if cache_file.exists():
        return pickle.load(cache_file.open("rb"))

    # Load and cache
    data = load_and_parse(file_path)
    pickle.dump(data, cache_file.open("wb"))
    return data
```

### Deployment Generation Performance

**Target:** <5 seconds for full deployment

**Optimizations:**
1. **Parallel template rendering** - Render agents in parallel
2. **Incremental updates** - Only regenerate changed files
3. **Cached parsing** - Don't re-parse unchanged YAML

### Context Loading Performance

**Target:** <100ms for dependency context loading

**Optimizations:**
1. **Distance-based filtering** - Don't load unnecessary context
2. **Pre-generated summaries** - Don't regenerate on every load
3. **Lazy loading** - Load only when needed

---

## Testing Strategy

### Unit Tests

**Test Coverage:**
- ✅ Config validation (schema compliance)
- ✅ Template rendering (all variables resolved)
- ✅ Adapter pattern (interface compliance)
- ✅ Context loader (distance calculation, mode selection)
- ✅ Summary generation (LLM mocking)

### Integration Tests

**Test Scenarios:**
- ✅ Full deployment generation (Claude, Goose, Cursor)
- ✅ Migration script (old → new structure)
- ✅ Context loading (with real dependency graphs)
- ✅ CLI commands (deploy, docs generate, etc.)

### Validation Tests

**Verify:**
- ✅ Generated deployments are valid
- ✅ No secrets leaked to git
- ✅ All templates render without errors
- ✅ Performance targets met

---

## Future Extensions

### Multi-Platform Deployment

```bash
# Deploy to all platforms simultaneously
vibey deploy --all

# Deploy to specific platforms
vibey deploy --platforms claude-code,goose
```

### Custom Platform Adapters

Users can create their own adapters:

```python
# .vibey/custom_adapters/my_platform.py
from framework.platform_adapters import PlatformAdapter

class MyPlatformAdapter(PlatformAdapter):
    def get_deployment_dir(self) -> Path:
        return Path(".myplatform")

    # ... implement interface
```

```bash
vibey deploy --platform my-platform --adapter .vibey/custom_adapters/my_platform.py
```

### Template Marketplace

Share and discover templates:

```bash
vibey template install goose-advanced
vibey template list --remote
```

---

## Summary

**Key Achievements:**

1. ✅ **Platform-Agnostic:** `.vibey/` works with any AI coding platform
2. ✅ **Single Source of Truth:** All config in one place
3. ✅ **Never Lose Context:** Markdown preserved, YAML tracks state
4. ✅ **Intelligent Context:** 80-90% reduction via distance-based loading
5. ✅ **Extensible:** Adapter pattern for new platforms
6. ✅ **User-Friendly:** Templates customizable, deployments automatic

**Next Steps:**

- Task 2: Implement modular config system
- Task 3: Implement context loading strategy
- Task 5: Design platform adapter pattern
- Task 6: Implement Claude Code adapter
- Task 7: Implement `vibey deploy` command

---

**Document Status:** ✅ Active Design Document
**Last Updated:** 2025-11-09
**Next Review:** After Task 1 completion
