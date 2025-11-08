# Sprint Plan: Config-to-Docs Architecture

**Sprint ID:** core-framework-2
**Sprint Name:** Config-to-Docs Architecture
**Track:** core-framework
**Duration:** 4 weeks (estimated)
**Priority:** Critical
**Status:** Not Started

---

## Sprint Goal

Establish the permanent `.vibey/` directory as the platform-agnostic core of Vibey, implement a comprehensive config-driven documentation generation system, and build the context loading strategy that enables multi-platform architecture.

**Success Criteria:**
- `.vibey/` directory becomes the permanent, platform-agnostic source of truth
- Platform deployments (`.claude/`, `.goose/`, `.cursor/`) generated from `.vibey/config/`
- Context loading strategy reduces context size by 80-90% for complex dependencies
- Modular config system supports project, framework, agents, and quality gates
- `vibey deploy --platform <name>` command works for all target platforms
- `vibey docs generate` creates platform-specific documentation from configs
- Foundation ready for adapter pattern (enables goose-port and multi-platform tracks)

---

## Background

### Current State (Problems)

**1. Platform Lock-in:**
- Framework currently tightly coupled to Claude Code
- All files in `.claude/` directory (Claude-specific)
- No clear separation between platform-agnostic core and platform-specific deployment
- Porting to Goose/Cursor requires duplicating entire framework

**2. Documentation Duplication:**
- CLAUDE.md manually maintained
- Agent instructions duplicated across platforms
- No single source of truth for configuration
- Changes require updating multiple files

**3. Context Explosion:**
- Loading all sprint plans and dependencies overwhelms context window
- No intelligent context summarization
- Can't handle projects with >10 sprints efficiently
- Distance-based loading not implemented

**4. No Multi-Platform Support:**
- Can't deploy framework to multiple platforms simultaneously
- No adapter pattern for platform-specific differences
- Manual porting required for each new platform

### Desired State (Solution)

**1. Platform-Agnostic Core (`.vibey/`):**
```
.vibey/
├── config/
│   ├── project.yaml        # Project-level config
│   ├── framework.yaml      # Framework settings
│   ├── agents/             # Agent definitions (YAML)
│   ├── workflows/          # Workflow definitions (YAML)
│   └── quality-gates.yaml  # Quality gate configs
├── roadmap/                # Roadmap system (YAML state)
│   ├── roadmap.yaml
│   ├── tracks/
│   ├── sprints/
│   └── tasks/
├── sprint_docs/            # Sprint documentation (Markdown context)
│   ├── <track-id>/
│   │   ├── <sprint-id>/
│   │   │   ├── plan.md           # Sprint plan (never regenerated)
│   │   │   ├── architecture.md   # Architecture decisions
│   │   │   ├── learnings.md      # Lessons learned
│   │   │   └── retrospective.md  # Sprint retrospective
├── summaries/              # Auto-generated summaries
│   ├── dependency_summaries/
│   └── task_summaries/
└── templates/              # User-customizable templates
    ├── claude.md.j2        # CLAUDE.md template
    ├── goose.md.j2         # Goose instructions template
    └── cursor.md.j2        # Cursor instructions template
```

**2. Platform Deployments (Generated):**
```
.claude/                    # Generated for Claude Code
├── CLAUDE.md              # Generated from .vibey/templates/claude.md.j2
├── agents/                # Generated from .vibey/config/agents/
├── workflows/             # Generated from .vibey/config/workflows/
└── project-config.yaml    # Generated from .vibey/config/project.yaml

.goose/                     # Generated for Goose
├── README.md              # Generated from .vibey/templates/goose.md.j2
├── extensions/            # Generated from .vibey/config/agents/
└── recipes/               # Generated from .vibey/config/workflows/

.cursor/                    # Generated for Cursor (future)
├── .cursorrules           # Generated from .vibey/templates/cursor.md.j2
└── agents/                # Generated from .vibey/config/agents/
```

**3. Dual System Design:**

**YAML (Roadmap System) - State Tracking:**
- Sprint status, progress, dependencies
- Updated by roadmap CLI
- Machine-readable
- Location: `.vibey/roadmap/*.yaml`
- Purpose: Deterministic state tracking

**Markdown (Sprint Docs) - Rich Context:**
- What to build, architecture decisions, learnings
- Iterated during development (NEVER regenerated)
- Human and AI readable
- Location: `.vibey/sprint_docs/*/`
- Purpose: Accumulated knowledge and context

**Critical Distinction:**
- YAML tracks deterministic state (status, completion %, dependencies)
- Markdown provides accumulated context (never lost, always growing)
- YAML links to Markdown via `documentation.files` field
- Both committed to git, non-overlapping purposes

**4. Context Loading Strategy:**

**Problem:** Loading all sprint plans for dependency context explodes context window.

**Solution:** Hierarchical, distance-based context loading with auto-generated summaries.

```
Context Loading Modes:

1. Minimal (< 5KB per dependency)
   - Task ID, title, status, blocking reason
   - Used for: distant dependencies (>2 hops away)

2. Summary (< 20KB per dependency)
   - Task summary (auto-generated, 200 words)
   - Key decisions, API contracts, interfaces
   - Used for: medium dependencies (1-2 hops away)

3. Full (original size)
   - Complete sprint plan, architecture docs
   - All context preserved
   - Used for: direct dependencies (0 hops - current sprint)

Distance Calculation:
- Current task: distance = 0 (full context)
- Direct dependency: distance = 1 (summary context)
- Dependency of dependency: distance = 2 (minimal context)
- 3+ hops: minimal context or omit

Result: 80-90% reduction in context size
```

---

## Architecture Overview

### Key Design Principles

**1. Separation of Concerns:**
- **Source:** `.vibey/` (platform-agnostic, version controlled)
- **Deployment:** `.claude/`, `.goose/`, `.cursor/` (generated, gitignored)
- **State:** `.vibey/roadmap/` (YAML, machine-readable)
- **Context:** `.vibey/sprint_docs/` (Markdown, human-readable)

**2. Single Source of Truth:**
- All configuration in `.vibey/config/`
- Templates in `.vibey/templates/`
- Platform deployments generated on-demand

**3. Never Lose Context:**
- Sprint documentation (Markdown) never regenerated
- YAML state and Markdown context coexist
- YAML points to Markdown via references
- Both committed to git

**4. Intelligent Context Loading:**
- Distance-based context selection
- Auto-generated summaries for distant dependencies
- Hierarchical loading strategy
- Massive reduction in context size

**5. Adapter Pattern Ready:**
- Platform-specific adapters in `framework/platform_adapters/`
- Each adapter knows how to generate deployment for its platform
- Core framework unchanged

---

## Tasks

### Phase 1: Foundation (Week 1)

#### Task 1: Design and document permanent .vibey/ directory structure
**ID:** core-framework-2-task-001
**Priority:** Critical
**Estimated:** 8 hours
**Agents:** coordinator, docs-writer

**Description:**
Design the complete `.vibey/` directory structure that will serve as the platform-agnostic core.

**Deliverables:**

**1.1 Architecture Document:** `docs/development/PLATFORM_AGNOSTIC_ARCHITECTURE.md`
- Complete directory structure with explanations
- File naming conventions
- What goes in `.vibey/` vs platform deployments
- Migration path from current structure
- Gitignore strategy

**1.2 YAML/Markdown Separation Document:** `docs/development/YAML_MARKDOWN_SEPARATION.md`
- Design principle explanation
- When to use YAML vs Markdown
- How they reference each other
- Examples of both systems working together
- Best practices

**1.3 Directory Structure Specification:**
```yaml
.vibey/:
  config/:
    - project.yaml          # Project metadata, tech stack, team
    - framework.yaml        # Framework settings, orchestration mode
    - agents/               # Agent definitions (one YAML per agent)
      - coordinator.yaml
      - web-developer.yaml
      - security-engineer.yaml
      # ... all 12 agents
    - workflows/            # Workflow definitions (one YAML per workflow)
      - sprint-planning.yaml
      - feature-development.yaml
      - security-audit.yaml
      # ... all workflows
    - quality-gates.yaml    # Quality gate definitions

  roadmap/:                 # Roadmap system (YAML state - existing)
    - roadmap.yaml
    - tracks/
    - sprints/
    - tasks/

  sprint_docs/              # Sprint documentation (Markdown context)
    - <track-id>/
      - <sprint-id>/
        - plan.md           # Original plan (never regenerated)
        - architecture.md   # Architecture decisions (iterated)
        - learnings.md      # Lessons learned (accumulated)
        - retrospective.md  # Final retrospective

  summaries/                # Auto-generated summaries (gitignored)
    - dependency_summaries/
      - <task-id>.md        # Auto-generated task summary
    - task_summaries/
      - <sprint-id>.md      # Auto-generated sprint summary

  templates/                # User-customizable templates (Jinja2)
    - claude.md.j2          # CLAUDE.md template
    - goose.md.j2           # Goose README template
    - cursor.md.j2          # Cursor .cursorrules template
    - agent.md.j2           # Agent instruction template
    - workflow.md.j2        # Workflow instruction template

  .cache/                   # Performance cache (gitignored - exists)
  .gitignore                # Ignore generated files, cache, summaries
```

**1.4 .gitignore Strategy:**
```gitignore
# .vibey/.gitignore
.cache/
summaries/
*.pyc
__pycache__/
```

**Validation:**
- Architecture document reviewed and approved
- Directory structure clear and justified
- Migration path documented

---

#### Task 2: Implement modular config system (project, framework, agents, quality-gates)
**ID:** core-framework-2-task-002
**Priority:** Critical
**Estimated:** 12 hours
**Agents:** web-developer
**Dependencies:** task-001

**Description:**
Create the modular YAML configuration system that replaces monolithic config files.

**Deliverables:**

**2.1 Config Schema Definitions:**

`framework/schemas/config/`:
- `project_config.schema.yaml` - Project-level configuration
- `framework_config.schema.yaml` - Framework settings
- `agent_config.schema.yaml` - Individual agent definition
- `workflow_config.schema.yaml` - Workflow definition
- `quality_gates.schema.yaml` - Quality gates configuration

**2.2 Project Config (`/vibey/config/project.yaml`):**
```yaml
project:
  name: "My Application"
  type: web-app  # web-app, api, ml-model, data-platform, infrastructure
  description: "Full-stack web application"
  repository: "https://github.com/user/repo"

tech_stack:
  languages:
    - python
    - typescript
    - javascript
  frameworks:
    - react
    - fastapi
    - postgresql
  tools:
    - docker
    - kubernetes
    - terraform

team:
  size: small  # solo, small (2-5), medium (6-15), large (16+)
  experience: intermediate  # beginner, intermediate, advanced

preferences:
  orchestration_mode: balanced  # simple, balanced, tiered
  context_mode: summary  # minimal, summary, full
  quality_gates_enabled: true
  auto_deploy: false
```

**2.3 Framework Config (`.vibey/config/framework.yaml`):**
```yaml
framework:
  version: "1.3.0"
  platform: claude-code  # claude-code, goose, cursor

orchestration:
  mode: balanced  # simple, balanced, tiered
  agent_selection:
    method: pattern-based  # keyword, pattern-based, coordinator
    fallback: coordinator

context_loading:
  strategy: hierarchical  # full, hierarchical, minimal
  max_context_size: 150000  # tokens
  dependency_mode: summary  # minimal, summary, full
  distance_threshold: 2  # hops before minimal context

quality:
  enforce_gates: true
  blocking_threshold: 90  # percent
  auto_audit: true

performance:
  cache_enabled: true
  cache_persistence: true
  parallel_operations: true
```

**2.4 Agent Config (`.vibey/config/agents/web-developer.yaml`):**
```yaml
agent:
  id: web-developer
  name: "Web Developer"
  role: development

capabilities:
  - frontend_development
  - backend_apis
  - database_design
  - testing

technologies:
  languages:
    - javascript
    - typescript
    - python
  frameworks:
    - react
    - vue
    - fastapi
    - express
  tools:
    - git
    - docker
    - webpack

trigger_patterns:
  keywords:
    - "build a"
    - "create a component"
    - "add a feature"
    - "implement"
  regex_patterns:
    - "build.*(?:frontend|backend|api)"
    - "create.*(?:component|page|route)"

quality_standards:
  - security: true
  - testing: true
  - documentation: true
  - performance: true

handoff_templates:
  - from: sprint-planner
    to: web-developer
    template: handoffs/sprint-to-development.md
  - from: web-developer
    to: test-engineer
    template: handoffs/development-to-testing.md
```

**2.5 Workflow Config (`.vibey/config/workflows/sprint-planning.yaml`):**
```yaml
workflow:
  id: sprint-planning
  name: "Sprint Planning"
  description: "Plan a development sprint with tasks, estimates, and dependencies"

  trigger_patterns:
    - "plan a sprint"
    - "create sprint plan"
    - "new sprint"

  phases:
    - id: discovery
      name: "Requirements Discovery"
      agent: sprint-planner
      estimated_duration: 2 hours
      inputs:
        - project goals
        - feature requirements
        - constraints
      outputs:
        - sprint_goals
        - feature_list

    - id: breakdown
      name: "Task Breakdown"
      agent: sprint-planner
      estimated_duration: 3 hours
      dependencies:
        - discovery
      inputs:
        - sprint_goals
        - feature_list
      outputs:
        - task_list
        - estimates

    - id: assignment
      name: "Agent Assignment"
      agent: coordinator
      estimated_duration: 1 hour
      dependencies:
        - breakdown
      inputs:
        - task_list
        - agent_workloads
      outputs:
        - assigned_tasks

    - id: review
      name: "Plan Review"
      agent: sprint-planner
      estimated_duration: 1 hour
      dependencies:
        - assignment
      inputs:
        - assigned_tasks
        - quality_gates
      outputs:
        - sprint_plan
```

**2.6 Quality Gates Config (`.vibey/config/quality-gates.yaml`):**
```yaml
quality_gates:
  track_level:
    - name: "Integration Testing"
      threshold: 95
      blocking: true
      audit_script: "scripts/audits/integration-test.sh"

    - name: "Documentation Review"
      threshold: 90
      blocking: true
      audit_script: "scripts/audits/docs-review.sh"

  sprint_level:
    - name: "Code Coverage"
      threshold: 80
      blocking: true
      audit_script: "pytest --cov"

    - name: "Security Scan"
      threshold: 100
      blocking: true
      audit_script: "bandit -r ."

  task_level:
    - name: "Linting"
      threshold: 100
      blocking: false
      audit_script: "eslint ."

    - name: "Type Checking"
      threshold: 100
      blocking: false
      audit_script: "mypy ."
```

**2.7 Python Config Loader:**

`framework/config/loader.py`:
```python
from pathlib import Path
from typing import Dict, Any
import yaml

class VibeyConfig:
    """Load and manage Vibey configuration from .vibey/config/"""

    def __init__(self, vibey_dir: Path = Path(".vibey")):
        self.vibey_dir = vibey_dir
        self.config_dir = vibey_dir / "config"
        self._cache = {}

    def load_project_config(self) -> Dict[str, Any]:
        """Load project configuration"""
        return self._load_yaml(self.config_dir / "project.yaml")

    def load_framework_config(self) -> Dict[str, Any]:
        """Load framework configuration"""
        return self._load_yaml(self.config_dir / "framework.yaml")

    def load_agent_config(self, agent_id: str) -> Dict[str, Any]:
        """Load specific agent configuration"""
        return self._load_yaml(self.config_dir / "agents" / f"{agent_id}.yaml")

    def load_all_agents(self) -> Dict[str, Dict[str, Any]]:
        """Load all agent configurations"""
        agents = {}
        agents_dir = self.config_dir / "agents"
        for file in agents_dir.glob("*.yaml"):
            agent_id = file.stem
            agents[agent_id] = self.load_agent_config(agent_id)
        return agents

    def load_workflow_config(self, workflow_id: str) -> Dict[str, Any]:
        """Load specific workflow configuration"""
        return self._load_yaml(self.config_dir / "workflows" / f"{workflow_id}.yaml")

    def load_all_workflows(self) -> Dict[str, Dict[str, Any]]:
        """Load all workflow configurations"""
        workflows = {}
        workflows_dir = self.config_dir / "workflows"
        for file in workflows_dir.glob("*.yaml"):
            workflow_id = file.stem
            workflows[workflow_id] = self.load_workflow_config(workflow_id)
        return workflows

    def load_quality_gates(self) -> Dict[str, Any]:
        """Load quality gates configuration"""
        return self._load_yaml(self.config_dir / "quality-gates.yaml")

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load YAML file with caching"""
        if path in self._cache:
            return self._cache[path]

        with open(path) as f:
            data = yaml.safe_load(f)

        self._cache[path] = data
        return data
```

**2.8 Config Validation Script:**

`framework/scripts/validate-vibey-config.py`:
- Validate all config files against schemas
- Check for missing required fields
- Validate cross-references (agent IDs, workflow IDs)
- Report errors and warnings

**Validation:**
- All config schemas defined
- Config loader works
- Validation script catches errors
- Examples provided for each config type

---

### Phase 2: Context Loading Strategy (Week 2)

#### Task 3: Implement context loading strategy with dependency summaries
**ID:** core-framework-2-task-003
**Priority:** Critical
**Estimated:** 16 hours
**Agents:** web-developer, ml-engineer
**Dependencies:** task-002

**Description:**
Build the intelligent context loading system that reduces context size by 80-90% for projects with complex dependencies.

**Deliverables:**

**3.1 Context Loading Strategy Document:** `docs/development/CONTEXT_LOADING_STRATEGY.md`

```markdown
# Context Loading Strategy

## Problem

Loading all sprint plans and dependency context for large projects overwhelms the context window:

- 10 sprints × 20KB each = 200KB just for plans
- Add architecture docs, learnings = 400KB+
- Context window limit: 200KB
- Result: Can't load full context for sprint with dependencies

## Solution

Hierarchical, distance-based context loading with auto-generated summaries.

### Distance Calculation

Calculate dependency distance from current task:

```
Current Task A (distance = 0)
  ├── Depends on Task B (distance = 1)
  │     ├── Depends on Task C (distance = 2)
  │     └── Depends on Task D (distance = 2)
  └── Depends on Task E (distance = 1)
        └── Depends on Task F (distance = 2)
```

### Context Modes by Distance

**Distance 0 (Current Task):**
- Load: Full context
- Size: Unlimited
- Includes: Sprint plan, architecture docs, all related files

**Distance 1 (Direct Dependencies):**
- Load: Summary context
- Size: ~20KB per task
- Includes: Auto-generated summary (200 words), key decisions, API contracts

**Distance 2+ (Indirect Dependencies):**
- Load: Minimal context
- Size: ~5KB per task
- Includes: Task ID, title, status, blocking reason (if any)

### Summary Generation

Auto-generate task summaries using LLM:

```python
def generate_task_summary(task_id: str, sprint_plan: str) -> str:
    """Generate 200-word summary of task from sprint plan"""

    prompt = f'''
    Summarize this task in 200 words focusing on:
    - What is being built
    - Key technical decisions
    - API contracts and interfaces
    - Dependencies this task provides

    Task ID: {task_id}
    Sprint Plan:
    {sprint_plan}

    Summary:
    '''

    return call_llm(prompt, max_tokens=300)
```

Summaries cached in `.vibey/summaries/task_summaries/`

### Context Size Reduction

**Before (Full Context):**
- 10 dependencies × 20KB = 200KB
- Current task: 30KB
- **Total: 230KB** (exceeds limit!)

**After (Hierarchical):**
- 2 direct deps × 20KB (summary) = 40KB
- 8 indirect deps × 5KB (minimal) = 40KB
- Current task: 30KB (full)
- **Total: 110KB** (52% reduction)

With 20 dependencies:
- 3 direct × 20KB = 60KB
- 17 indirect × 5KB = 85KB
- Current: 30KB
- **Total: 175KB** (vs 430KB full = 59% reduction)

### Implementation

See: `framework/roadmap/context_loader.py`
```
</markdown>

**3.2 Context Loader Implementation:** `framework/roadmap/context_loader.py`

```python
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
from enum import Enum

class ContextMode(Enum):
    MINIMAL = "minimal"   # ~5KB per dependency
    SUMMARY = "summary"   # ~20KB per dependency
    FULL = "full"         # Original size

@dataclass
class ContextLoad:
    task_id: str
    distance: int
    mode: ContextMode
    content: str
    size_kb: float

class ContextLoader:
    """Load context for sprint/task with intelligent distance-based loading"""

    def __init__(self, vibey_dir: Path = Path(".vibey")):
        self.vibey_dir = vibey_dir
        self.roadmap_dir = vibey_dir / "roadmap"
        self.summaries_dir = vibey_dir / "summaries"
        self.sprint_docs_dir = vibey_dir / "sprint_docs"

        self.max_context_tokens = 150000  # Default limit
        self.distance_threshold = 2  # Distance for minimal context

    def load_task_context(self, task_id: str, max_distance: int = 3) -> List[ContextLoad]:
        """
        Load context for a task with distance-based mode selection.

        Args:
            task_id: Task to load context for
            max_distance: Maximum dependency distance to include

        Returns:
            List of ContextLoad objects with content and metadata
        """
        # Calculate dependency distances
        distances = self._calculate_distances(task_id, max_distance)

        # Load context for each dependency
        loads = []
        for dep_task_id, distance in distances.items():
            mode = self._select_context_mode(distance)
            content = self._load_content(dep_task_id, mode)

            loads.append(ContextLoad(
                task_id=dep_task_id,
                distance=distance,
                mode=mode,
                content=content,
                size_kb=len(content) / 1024
            ))

        # Sort by distance (closest first)
        loads.sort(key=lambda x: x.distance)

        return loads

    def _calculate_distances(self, task_id: str, max_distance: int) -> Dict[str, int]:
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

            if current_id in visited or current_dist > max_distance:
                continue

            visited.add(current_id)

            # Get dependencies for current task
            deps = self._get_task_dependencies(current_id)

            for dep_id in deps:
                new_dist = current_dist + 1

                if dep_id not in distances or new_dist < distances[dep_id]:
                    distances[dep_id] = new_dist
                    queue.append((dep_id, new_dist))

        return distances

    def _select_context_mode(self, distance: int) -> ContextMode:
        """Select context mode based on distance"""
        if distance == 0:
            return ContextMode.FULL
        elif distance == 1:
            return ContextMode.SUMMARY
        else:  # distance >= 2
            return ContextMode.MINIMAL

    def _load_content(self, task_id: str, mode: ContextMode) -> str:
        """Load content for task in specified mode"""
        if mode == ContextMode.FULL:
            return self._load_full_context(task_id)
        elif mode == ContextMode.SUMMARY:
            return self._load_summary_context(task_id)
        else:  # MINIMAL
            return self._load_minimal_context(task_id)

    def _load_full_context(self, task_id: str) -> str:
        """Load complete context for task"""
        task = self._load_task(task_id)
        sprint_id = task.get("sprint_id")
        track_id = task.get("track_id")

        # Load sprint plan
        sprint_plan_path = self.sprint_docs_dir / track_id / sprint_id / "plan.md"

        context = f"# Task: {task['title']}\n\n"
        context += f"**ID:** {task_id}\n"
        context += f"**Status:** {task['status']}\n"
        context += f"**Description:** {task['description']}\n\n"

        if sprint_plan_path.exists():
            context += "## Sprint Plan\n\n"
            context += sprint_plan_path.read_text()

        # Load architecture docs if exists
        arch_path = self.sprint_docs_dir / track_id / sprint_id / "architecture.md"
        if arch_path.exists():
            context += "\n\n## Architecture\n\n"
            context += arch_path.read_text()

        return context

    def _load_summary_context(self, task_id: str) -> str:
        """Load summary context (auto-generated or create)"""
        summary_path = self.summaries_dir / "task_summaries" / f"{task_id}.md"

        # Check if summary exists
        if summary_path.exists():
            return summary_path.read_text()

        # Generate summary
        summary = self._generate_task_summary(task_id)

        # Cache summary
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(summary)

        return summary

    def _load_minimal_context(self, task_id: str) -> str:
        """Load minimal context (task metadata only)"""
        task = self._load_task(task_id)

        context = f"# Task: {task['title']}\n\n"
        context += f"**ID:** {task_id}\n"
        context += f"**Status:** {task['status']}\n"
        context += f"**Sprint:** {task.get('sprint_id', 'unknown')}\n"

        if task.get('blocked'):
            context += f"**Blocked:** {task.get('blocked_reason', 'yes')}\n"

        return context

    def _generate_task_summary(self, task_id: str) -> str:
        """
        Generate auto-summary of task.

        In production, this would call an LLM to summarize.
        For now, extract key information from task and sprint plan.
        """
        task = self._load_task(task_id)
        sprint_id = task.get("sprint_id")
        track_id = task.get("track_id")

        # Load sprint plan
        sprint_plan_path = self.sprint_docs_dir / track_id / sprint_id / "plan.md"
        sprint_plan = sprint_plan_path.read_text() if sprint_plan_path.exists() else ""

        # Extract task section from sprint plan (simple approach)
        # In production, use LLM to generate 200-word summary

        summary = f"# Task Summary: {task['title']}\n\n"
        summary += f"**Task ID:** {task_id}\n"
        summary += f"**Status:** {task['status']}\n\n"
        summary += f"**Description:**\n{task['description']}\n\n"

        # TODO: Add LLM-based summarization here
        # For now, just use description

        return summary

    def _get_task_dependencies(self, task_id: str) -> List[str]:
        """Get list of task IDs this task depends on"""
        task = self._load_task(task_id)

        deps = []
        for dep in task.get("dependencies", []):
            if isinstance(dep, dict):
                deps.append(dep.get("target_id"))
            else:
                deps.append(str(dep))

        return [d for d in deps if d]

    def _load_task(self, task_id: str) -> Dict:
        """Load task data from YAML"""
        # Parse sprint_id from task_id (e.g., "sprint-1-task-001" -> "sprint-1")
        # This is simplified - production would use proper task index

        sprint_id = "-".join(task_id.split("-")[:-2])  # Extract sprint ID

        tasks_path = self.roadmap_dir / "tasks" / f"{sprint_id}-tasks.yaml"

        import yaml
        with open(tasks_path) as f:
            tasks_data = yaml.safe_load(f)

        for task in tasks_data.get("tasks", []):
            if task["id"] == task_id:
                return task

        raise ValueError(f"Task {task_id} not found")
```

**3.3 Roadmap CLI Context Command:**

`framework/scripts/roadmap-lib/context.py`:
```python
def handle_context(args):
    """Handle 'roadmap context <task-id>' command"""

    from framework.roadmap.context_loader import ContextLoader, ContextMode

    loader = ContextLoader()

    # Load context for task
    context_loads = loader.load_task_context(
        task_id=args.task_id,
        max_distance=args.max_distance or 3
    )

    # Print context summary
    print(f"\n📚 Context for Task: {args.task_id}\n")
    print("=" * 80)

    total_size = 0
    for load in context_loads:
        mode_emoji = {
            ContextMode.FULL: "📖",
            ContextMode.SUMMARY: "📝",
            ContextMode.MINIMAL: "📌"
        }[load.mode]

        print(f"\n{mode_emoji} {load.task_id} (distance: {load.distance}, mode: {load.mode.value}, size: {load.size_kb:.1f}KB)")

        if args.verbose:
            print(f"\n{load.content}\n")
            print("-" * 80)

        total_size += load.size_kb

    print(f"\n📊 Total Context Size: {total_size:.1f}KB")

    # Estimate token count (rough: 1KB ≈ 250 tokens)
    estimated_tokens = int(total_size * 250)
    print(f"📊 Estimated Tokens: ~{estimated_tokens:,}")
```

**3.4 Performance Benchmarks:**

Create `docs/development/CONTEXT_LOADING_BENCHMARKS.md`:
- Benchmark context loading for projects of various sizes
- Compare full vs hierarchical loading
- Measure token reduction percentages
- Performance metrics (<100ms for context calculation)

**Validation:**
- Context loader works for all distances
- Summary generation functional
- 80-90% reduction achieved for 10+ dependencies
- Roadmap context command works
- Benchmarks documented

---

#### Task 4: Implement auto-generated task and dependency summaries
**ID:** core-framework-2-task-004
**Priority:** High
**Estimated:** 10 hours
**Agents:** ml-engineer, web-developer
**Dependencies:** task-003

**Description:**
Build the summary generation system that creates concise, LLM-generated summaries of tasks and dependencies.

**Deliverables:**

**4.1 Summary Generator:** `framework/roadmap/summary_generator.py`

```python
from pathlib import Path
from typing import Dict, Optional
import yaml

class SummaryGenerator:
    """Generate task and dependency summaries using LLM"""

    def __init__(self, vibey_dir: Path = Path(".vibey")):
        self.vibey_dir = vibey_dir
        self.summaries_dir = vibey_dir / "summaries"
        self.sprint_docs_dir = vibey_dir / "sprint_docs"

        # Create summaries directories
        (self.summaries_dir / "task_summaries").mkdir(parents=True, exist_ok=True)
        (self.summaries_dir / "dependency_summaries").mkdir(parents=True, exist_ok=True)

    def generate_task_summary(
        self,
        task_id: str,
        max_words: int = 200,
        force_regenerate: bool = False
    ) -> str:
        """
        Generate or retrieve summary for a task.

        Args:
            task_id: Task to summarize
            max_words: Maximum words in summary
            force_regenerate: Regenerate even if cached

        Returns:
            Summary text (Markdown)
        """
        summary_path = self.summaries_dir / "task_summaries" / f"{task_id}.md"

        # Check cache
        if summary_path.exists() and not force_regenerate:
            return summary_path.read_text()

        # Load task context
        task = self._load_task(task_id)
        sprint_id = task.get("sprint_id")
        track_id = task.get("track_id")

        # Load sprint plan
        sprint_plan_path = self.sprint_docs_dir / track_id / sprint_id / "plan.md"
        sprint_plan = ""
        if sprint_plan_path.exists():
            sprint_plan = sprint_plan_path.read_text()

        # Generate summary using LLM
        summary = self._call_llm_for_summary(
            task=task,
            sprint_plan=sprint_plan,
            max_words=max_words
        )

        # Cache summary
        summary_path.write_text(summary)

        return summary

    def generate_dependency_summary(
        self,
        task_id: str,
        dependency_id: str,
        max_words: int = 100
    ) -> str:
        """
        Generate summary of how dependency relates to task.

        Args:
            task_id: Task that depends on dependency
            dependency_id: Task being depended upon
            max_words: Maximum words in summary

        Returns:
            Dependency relationship summary
        """
        summary_path = self.summaries_dir / "dependency_summaries" / f"{task_id}_depends_{dependency_id}.md"

        # Check cache
        if summary_path.exists():
            return summary_path.read_text()

        # Load both tasks
        task = self._load_task(task_id)
        dependency = self._load_task(dependency_id)

        # Generate relationship summary
        summary = self._call_llm_for_dependency_summary(
            task=task,
            dependency=dependency,
            max_words=max_words
        )

        # Cache
        summary_path.write_text(summary)

        return summary

    def _call_llm_for_summary(
        self,
        task: Dict,
        sprint_plan: str,
        max_words: int
    ) -> str:
        """
        Call LLM to generate task summary.

        In production, this would call Claude/GPT API.
        For now, returns structured format.
        """
        # TODO: Implement actual LLM call
        # For now, create structured summary from task data

        summary = f"# Task Summary: {task['title']}\n\n"
        summary += f"**Task ID:** {task['id']}\n"
        summary += f"**Status:** {task['status']}\n"
        summary += f"**Priority:** {task.get('priority', 'medium')}\n\n"

        summary += "## What is Being Built\n\n"
        summary += f"{task['description']}\n\n"

        if task.get('deliverables'):
            summary += "## Deliverables\n\n"
            for deliverable in task['deliverables']:
                summary += f"- {deliverable}\n"
            summary += "\n"

        # In production, LLM would extract key technical decisions from sprint plan
        summary += "## Key Technical Decisions\n\n"
        summary += "(To be extracted from sprint plan by LLM)\n\n"

        summary += "## Dependencies Provided\n\n"
        summary += "(APIs, interfaces, data this task provides to other tasks)\n\n"

        return summary

    def _call_llm_for_dependency_summary(
        self,
        task: Dict,
        dependency: Dict,
        max_words: int
    ) -> str:
        """Generate dependency relationship summary"""

        summary = f"# Dependency: {task['title']} → {dependency['title']}\n\n"
        summary += f"**Task:** {task['id']}\n"
        summary += f"**Depends On:** {dependency['id']}\n\n"

        summary += "## Why This Dependency Exists\n\n"

        # Find dependency reason from task dependencies
        for dep in task.get("dependencies", []):
            if dep.get("target_id") == dependency["id"]:
                reason = dep.get("reason", "No reason specified")
                summary += f"{reason}\n\n"
                break

        summary += "## What This Dependency Provides\n\n"
        summary += f"The task '{dependency['title']}' provides:\n"
        summary += "(To be extracted from dependency deliverables)\n"

        return summary

    def _load_task(self, task_id: str) -> Dict:
        """Load task from roadmap"""
        # Simplified - production uses task index
        sprint_id = "-".join(task_id.split("-")[:-2])
        tasks_path = self.vibey_dir / "roadmap" / "tasks" / f"{sprint_id}-tasks.yaml"

        with open(tasks_path) as f:
            tasks_data = yaml.safe_load(f)

        for task in tasks_data.get("tasks", []):
            if task["id"] == task_id:
                return task

        raise ValueError(f"Task {task_id} not found")
```

**4.2 Roadmap CLI Summarize Command:**

Add to `framework/scripts/roadmap`:
```bash
roadmap summarize <task-id>     # Summarize task
roadmap summarize --sprint <id>  # Summarize all tasks in sprint
roadmap summarize --regenerate   # Force regenerate summaries
```

**4.3 Batch Summary Generation:**

`framework/scripts/generate-summaries.py`:
- Generate summaries for all tasks in roadmap
- Show progress
- Cache results
- Report statistics (total size reduction)

**Validation:**
- Summary generator works
- Summaries cached correctly
- CLI command functional
- Batch generation works

---

### Phase 3: Platform Deployment System (Week 3)

#### Task 5: Design platform adapter pattern and interfaces
**ID:** core-framework-2-task-005
**Priority:** Critical
**Estimated:** 8 hours
**Agents:** coordinator, web-developer
**Dependencies:** task-002

**Description:**
Design the adapter pattern that allows platform-specific deployment generation while keeping the core platform-agnostic.

**Deliverables:**

**5.1 Adapter Pattern Design:** `docs/development/ADAPTER_PATTERN.md`

```markdown
# Platform Adapter Pattern

## Overview

The adapter pattern enables platform-specific deployments while keeping `.vibey/` platform-agnostic.

## Architecture

```
.vibey/ (Platform-Agnostic Core)
    ↓
PlatformAdapter Interface
    ↓
├── ClaudeAdapter → .claude/
├── GooseAdapter → .goose/
└── CursorAdapter → .cursor/
```

## Interface Definition

All platform adapters implement `PlatformAdapter` interface:

```python
class PlatformAdapter(ABC):
    """Base interface for platform-specific adapters"""

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Platform identifier (e.g., 'claude-code', 'goose', 'cursor')"""
        pass

    @property
    @abstractmethod
    def deployment_dir(self) -> str:
        """Deployment directory name (e.g., '.claude', '.goose', '.cursor')"""
        pass

    @abstractmethod
    def deploy(self, config: VibeyConfig) -> DeploymentResult:
        """
        Generate platform-specific deployment from .vibey/ config.

        Args:
            config: Loaded Vibey configuration

        Returns:
            DeploymentResult with status and files created
        """
        pass

    @abstractmethod
    def generate_instructions_file(self, config: VibeyConfig) -> str:
        """
        Generate main instructions file (CLAUDE.md, README.md, .cursorrules, etc.)

        Args:
            config: Loaded Vibey configuration

        Returns:
            Generated file content
        """
        pass

    @abstractmethod
    def generate_agent_files(self, agents: Dict[str, Dict]) -> List[str]:
        """
        Generate platform-specific agent files.

        Args:
            agents: Dict of agent configs from .vibey/config/agents/

        Returns:
            List of file paths created
        """
        pass

    @abstractmethod
    def generate_workflow_files(self, workflows: Dict[str, Dict]) -> List[str]:
        """
        Generate platform-specific workflow files.

        Args:
            workflows: Dict of workflow configs from .vibey/config/workflows/

        Returns:
            List of file paths created
        """
        pass

    @abstractmethod
    def validate_deployment(self) -> ValidationResult:
        """
        Validate generated deployment is correct.

        Returns:
            ValidationResult with any errors/warnings
        """
        pass
```

## Adapter Responsibilities

Each adapter is responsible for:

1. **Template Selection:** Choose appropriate Jinja2 template for platform
2. **File Generation:** Generate all platform-specific files
3. **Structure Creation:** Create platform-specific directory structure
4. **Validation:** Ensure deployment is valid for platform
5. **Cleanup:** Handle .gitignore, cache invalidation

## Example: Claude Adapter

```python
class ClaudeAdapter(PlatformAdapter):
    """Adapter for Claude Code platform"""

    @property
    def platform_name(self) -> str:
        return "claude-code"

    @property
    def deployment_dir(self) -> str:
        return ".claude"

    def deploy(self, config: VibeyConfig) -> DeploymentResult:
        results = []

        # 1. Generate CLAUDE.md from template
        claude_md = self.generate_instructions_file(config)
        claude_path = Path(self.deployment_dir) / "CLAUDE.md"
        claude_path.write_text(claude_md)
        results.append(str(claude_path))

        # 2. Generate agent files
        agents = config.load_all_agents()
        agent_files = self.generate_agent_files(agents)
        results.extend(agent_files)

        # 3. Generate workflow files
        workflows = config.load_all_workflows()
        workflow_files = self.generate_workflow_files(workflows)
        results.extend(workflow_files)

        # 4. Copy project config
        project_config_src = config.config_dir / "project.yaml"
        project_config_dst = Path(self.deployment_dir) / "project-config.yaml"
        shutil.copy(project_config_src, project_config_dst)
        results.append(str(project_config_dst))

        return DeploymentResult(
            platform=self.platform_name,
            success=True,
            files_created=results
        )

    def generate_instructions_file(self, config: VibeyConfig) -> str:
        # Load template
        template_path = Path(".vibey/templates/claude.md.j2")
        template = jinja2.Template(template_path.read_text())

        # Render with config
        project_config = config.load_project_config()
        framework_config = config.load_framework_config()

        return template.render(
            project=project_config["project"],
            tech_stack=project_config["tech_stack"],
            framework=framework_config["framework"]
        )

    # ... implement other methods
```

## Platform-Specific Mappings

### Claude Code
- Instructions: `CLAUDE.md` (Markdown)
- Agents: `.claude/agents/*.md` (Markdown)
- Workflows: `.claude/workflows/*.md` (Markdown)

### Goose
- Instructions: `.goose/README.md` (Markdown)
- Agents: `.goose/extensions/*.yaml` (YAML)
- Workflows: `.goose/recipes/*.yaml` (YAML)

### Cursor
- Instructions: `.cursor/.cursorrules` (Text)
- Agents: `.cursor/agents/*.md` (Markdown)
- Workflows: `.cursor/workflows/*.md` (Markdown)

## Benefits

1. **Single Source of Truth:** `.vibey/config/` is the only place to edit
2. **Multi-Platform:** Can deploy to Claude, Goose, Cursor simultaneously
3. **Consistency:** Same config generates consistent deployment
4. **Maintainability:** Update adapter, not entire framework
```

**5.2 Platform Adapter Base Class:**

`framework/platform_adapters/base.py`:
```python
from abc import ABC, abstractmethod
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Any

@dataclass
class DeploymentResult:
    platform: str
    success: bool
    files_created: List[str]
    errors: List[str] = None
    warnings: List[str] = None

@dataclass
class ValidationResult:
    valid: bool
    errors: List[str] = None
    warnings: List[str] = None

class PlatformAdapter(ABC):
    """Base interface for platform-specific adapters"""

    def __init__(self, vibey_dir: Path = Path(".vibey")):
        self.vibey_dir = vibey_dir
        self.deployment_path = Path(self.deployment_dir)

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Platform identifier"""
        pass

    @property
    @abstractmethod
    def deployment_dir(self) -> str:
        """Deployment directory name"""
        pass

    @abstractmethod
    def deploy(self, config) -> DeploymentResult:
        """Generate platform-specific deployment"""
        pass

    @abstractmethod
    def generate_instructions_file(self, config) -> str:
        """Generate main instructions file"""
        pass

    @abstractmethod
    def generate_agent_files(self, agents: Dict[str, Dict]) -> List[str]:
        """Generate platform-specific agent files"""
        pass

    @abstractmethod
    def generate_workflow_files(self, workflows: Dict[str, Dict]) -> List[str]:
        """Generate platform-specific workflow files"""
        pass

    @abstractmethod
    def validate_deployment(self) -> ValidationResult:
        """Validate generated deployment"""
        pass

    def clean_deployment(self) -> None:
        """Clean existing deployment directory"""
        if self.deployment_path.exists():
            import shutil
            shutil.rmtree(self.deployment_path)
        self.deployment_path.mkdir(parents=True)
```

**Validation:**
- Adapter pattern documented
- Base class defined
- Interface clear and complete
- Examples provided

---

#### Task 6: Implement Claude Code platform adapter
**ID:** core-framework-2-task-006
**Priority:** High
**Estimated:** 12 hours
**Agents:** web-developer
**Dependencies:** task-005

**Description:**
Implement the Claude Code platform adapter that generates `.claude/` deployment from `.vibey/config/`.

**Deliverables:**

**6.1 Claude Adapter:** `framework/platform_adapters/claude_adapter.py`

(Implementation of ClaudeAdapter class - full code too long, but complete implementation following the pattern above)

**6.2 Claude.md Template:** `.vibey/templates/claude.md.j2`

```jinja2
<!-- VIBEY_FRAMEWORK_MANAGED -->
# {{ project.name }} - Project Context

**Project Type:** {{ project.type }}
**Tech Stack:** {{ tech_stack.languages | join(", ") }}
**Frameworks:** {{ tech_stack.frameworks | join(", ") }}

---

## Project Overview

{{ project.description }}

---

## Technology Stack

**Languages:**
{% for lang in tech_stack.languages %}
- {{ lang }}
{% endfor %}

**Frameworks:**
{% for framework in tech_stack.frameworks %}
- {{ framework }}
{% endfor %}

**Tools:**
{% for tool in tech_stack.tools %}
- {{ tool %}
{% endfor %}

---

## Vibey Framework Configuration

**Framework Version:** {{ framework.version }}
**Orchestration Mode:** {{ framework.orchestration.mode }}
**Quality Gates:** {{ "Enabled" if framework.quality.enforce_gates else "Disabled" }}

---

## Agent Team

Your development team consists of specialized AI agents:

{% for agent_id, agent in agents.items() %}
### {{ agent.name }} (`{{ agent_id }}`)

**Role:** {{ agent.role }}

**Capabilities:**
{% for capability in agent.capabilities %}
- {{ capability }}
{% endfor %}

**Technologies:**
- Languages: {{ agent.technologies.languages | join(", ") }}
- Frameworks: {{ agent.technologies.frameworks | join(", ") }}

**Trigger Patterns:**
{% for keyword in agent.trigger_patterns.keywords %}
- "{{ keyword }}"
{% endfor %}

---
{% endfor %}

## Workflows Available

{% for workflow_id, workflow in workflows.items() %}
### {{ workflow.name }}

{{ workflow.description }}

**Phases:**
{% for phase in workflow.phases %}
1. **{{ phase.name }}** ({{ phase.agent }}) - {{ phase.estimated_duration }}
{% endfor %}

---
{% endfor %}

## Current Sprint

{% if current_sprint %}
**Sprint:** {{ current_sprint.name }}
**Status:** {{ current_sprint.status }}
**Progress:** {{ current_sprint.progress.completion_percent }}%

### Active Tasks

{% for task in current_sprint.active_tasks %}
- {{ task.title }} ({{ task.status }})
{% endfor %}
{% else %}
No active sprint. Run `/vibey plan` to create a sprint.
{% endif %}

---

## Quality Standards

{% for gate in quality_gates.task_level %}
- **{{ gate.name }}:** {{ gate.threshold }}% threshold ({{ "Blocking" if gate.blocking else "Non-blocking" }})
{% endfor %}

---

**Generated by Vibey Framework v{{ framework.version }}**
**Last Updated:** {{ generation_timestamp }}
```

**6.3 Agent Template:** `.vibey/templates/agent.md.j2`
**6.4 Workflow Template:** `.vibey/templates/workflow.md.j2`

**Validation:**
- Claude adapter generates valid `.claude/` directory
- All files created correctly
- Templates render properly
- Validation passes

---

### Phase 4: CLI Commands & Integration (Week 4)

#### Task 7: Implement `vibey deploy --platform <name>` command
**ID:** core-framework-2-task-007
**Priority:** High
**Estimated:** 10 hours
**Agents:** web-developer
**Dependencies:** task-006

**Description:**
Create the CLI command that generates platform-specific deployments from `.vibey/config/`.

**Deliverables:**

**7.1 Deploy Command:** `framework/commands/vibey-deploy.md`

```markdown
# Vibey Deploy Command

**Usage:** `/vibey deploy --platform <name>`

Generate platform-specific deployment from `.vibey/` configuration.

## Platforms Supported

- `claude-code` - Generate `.claude/` directory
- `goose` - Generate `.goose/` directory (future)
- `cursor` - Generate `.cursor/` directory (future)
- `all` - Generate all platforms

## Examples

```bash
# Deploy to Claude Code
/vibey deploy --platform claude-code

# Deploy to all platforms
/vibey deploy --platform all

# Clean and redeploy
/vibey deploy --platform claude-code --clean
```

## Implementation

1. Load `.vibey/config/` using VibeyConfig
2. Select appropriate PlatformAdapter
3. Call adapter.deploy(config)
4. Show deployment results
5. Validate deployment
```

**7.2 Python CLI Implementation:** `framework/scripts/vibey-deploy.py`

**Validation:**
- Command works for Claude Code
- Generates valid deployment
- Clean flag works
- Error handling robust

---

#### Task 8: Implement `vibey docs generate` command
**ID:** core-framework-2-task-008
**Priority:** Medium
**Estimated:** 8 hours
**Agents:** web-developer, docs-writer
**Dependencies:** task-007

**Description:**
Create command to generate documentation from configs without full deployment.

**Deliverables:**

**8.1 Docs Generate Command**
- Generate CLAUDE.md without deploying
- Update CLAUDE.md from latest config
- Regenerate specific sections

**Validation:**
- Generates documentation correctly
- Can update existing file
- Preserves manual edits outside managed sections

---

#### Task 9: Implement `roadmap summarize` and `roadmap context` commands
**ID:** core-framework-2-task-009
**Priority:** Medium
**Estimated:** 6 hours
**Agents:** web-developer
**Dependencies:** task-003, task-004

**Description:**
Add CLI commands for context loading and summarization (already partially implemented in task 3 & 4, this finalizes integration).

**Deliverables:**

**9.1 Integration with roadmap CLI**
- `roadmap context <task-id>` - Load context with distance-based loading
- `roadmap summarize <task-id>` - Generate task summary
- `roadmap summarize --all` - Generate all summaries

**Validation:**
- Commands work
- Performance acceptable
- Output clear and useful

---

#### Task 10: Create migration script from current structure to new .vibey/ structure
**ID:** core-framework-2-task-010
**Priority:** High
**Estimated:** 10 hours
**Agents:** web-developer
**Dependencies:** task-001, task-002

**Description:**
Create script to migrate existing Vibey projects to new `.vibey/` structure.

**Deliverables:**

**10.1 Migration Script:** `framework/scripts/migrate-to-vibey-structure.py`

```python
#!/usr/bin/env python3
"""
Migrate existing Vibey project to new .vibey/ structure.

Before:
- .claude/agents/*.md
- .claude/workflows/*.md
- .claude/CLAUDE.md (manually maintained)

After:
- .vibey/config/ (YAML configs)
- .vibey/templates/ (Jinja2 templates)
- .claude/ (generated from .vibey/)
"""

from pathlib import Path
import yaml
import shutil

def migrate_project():
    """Migrate project to new .vibey/ structure"""

    print("🔄 Migrating to new .vibey/ structure...")

    # 1. Create .vibey/ structure
    create_vibey_structure()

    # 2. Extract config from existing CLAUDE.md
    extract_config_from_claude_md()

    # 3. Convert agent .md files to YAML configs
    convert_agents_to_yaml()

    # 4. Convert workflow .md files to YAML configs
    convert_workflows_to_yaml()

    # 5. Backup existing .claude/
    backup_claude_dir()

    # 6. Regenerate .claude/ from .vibey/
    regenerate_claude_deployment()

    # 7. Validate migration
    validate_migration()

    print("✅ Migration complete!")
```

**10.2 Migration Documentation:** `docs/guides/MIGRATION_TO_VIBEY_STRUCTURE.md`

**Validation:**
- Migrates existing projects successfully
- No data loss
- Rollback capability
- Clear instructions

---

#### Task 11: Update all Vibey commands to use .vibey/ structure
**ID:** core-framework-2-task-011
**Priority:** Critical
**Estimated:** 12 hours
**Agents:** web-developer
**Dependencies:** task-010

**Description:**
Update `/vibey` commands to work with new `.vibey/` structure.

**Deliverables:**

**11.1 Update `/vibey deployment`**
- Initialize `.vibey/config/` instead of `.claude/`
- Create default project.yaml and framework.yaml
- Create `.vibey/templates/` with default templates
- Deploy to `.claude/` using adapter

**11.2 Update `/vibey plan`**
- Save sprint plan to `.vibey/sprint_docs/<track>/<sprint>/plan.md`
- Update roadmap in `.vibey/roadmap/`
- Don't regenerate plan once created

**11.3 Update `/vibey code`**
- Read from `.vibey/roadmap/`
- Show progress from `.vibey/`
- Update based on `.vibey/config/framework.yaml`

**11.4 Update `/vibey manage`**
- Manage `.vibey/config/` files
- Trigger redeployment after config changes
- Show config status

**Validation:**
- All commands work with new structure
- Backward compatibility maintained (migration script available)
- No breaking changes for users

---

#### Task 12: Write comprehensive documentation for Config-to-Docs Architecture
**ID:** core-framework-2-task-012
**Priority:** High
**Estimated:** 10 hours
**Agents:** docs-writer
**Dependencies:** task-001 through task-011

**Description:**
Create complete documentation for the new architecture.

**Deliverables:**

**12.1 Architecture Documentation:**
- `docs/development/PLATFORM_AGNOSTIC_ARCHITECTURE.md` (from task 1)
- `docs/development/YAML_MARKDOWN_SEPARATION.md` (from task 1)
- `docs/development/CONTEXT_LOADING_STRATEGY.md` (from task 3)
- `docs/development/ADAPTER_PATTERN.md` (from task 5)

**12.2 User Guides:**
- `docs/guides/VIBEY_DIRECTORY_STRUCTURE.md` - Complete .vibey/ reference
- `docs/guides/CONFIG_SYSTEM.md` - How to configure Vibey
- `docs/guides/MULTI_PLATFORM_DEPLOYMENT.md` - Deploy to multiple platforms
- `docs/guides/CONTEXT_OPTIMIZATION.md` - Using context loading effectively

**12.3 Reference Documentation:**
- Config file format reference
- Template variable reference
- CLI command reference (updated)

**Validation:**
- All documentation complete
- Examples working
- Clear and comprehensive
- No broken links

---

#### Task 13: Integration testing and production readiness validation
**ID:** core-framework-2-task-013
**Priority:** Critical
**Estimated:** 12 hours
**Agents:** test-engineer
**Dependencies:** task-001 through task-012

**Description:**
Comprehensive testing of entire Config-to-Docs architecture.

**Deliverables:**

**13.1 Integration Test Suite:**

`framework/scripts/tests/test_config_to_docs.py`:
- Test config loading system
- Test context loader with various dependency graphs
- Test summary generation
- Test platform adapter deployment
- Test CLI commands
- Test migration script

**13.2 End-to-End Test:**

`framework/scripts/tests/test_e2e_vibey_structure.py`:
- Fresh project initialization
- Config modification
- Platform deployment
- Multi-sprint workflow with dependencies
- Context loading for complex dependencies
- Migration from old structure

**13.3 Performance Benchmarks:**
- Context loading performance (various project sizes)
- Summary generation time
- Deployment generation time
- Overall system performance

**13.4 Validation:**
- All tests passing (100%)
- Performance targets met:
  - Context loading: <100ms for 50 tasks
  - Summary generation: <2s per task
  - Deployment: <5s for full deployment
  - 80-90% context reduction achieved

---

## Dependencies

### Sprint Dependencies
- **Sprint 1 (Default CLAUDE.md):** Blocked by this sprint
- **Sprint 3 (Framework Polish):** ✅ Complete

### External Dependencies
- None (self-contained architecture changes)

### Blocks
- **Track 3 (goose-port):** Blocked waiting for adapter pattern
- **Track 4 (multi-platform):** Blocked waiting for `.vibey/` structure

---

## Deliverables Summary

### Code
- Modular config system (~800 lines)
- Context loader (~500 lines)
- Summary generator (~400 lines)
- Platform adapters (~1,000 lines)
- CLI commands (~600 lines)
- Migration script (~400 lines)
- **Total:** ~3,700 lines

### Tests
- Integration tests (~800 lines)
- E2E tests (~400 lines)
- **Total:** ~1,200 lines

### Documentation
- Architecture docs (~2,000 lines)
- User guides (~1,500 lines)
- Reference docs (~800 lines)
- **Total:** ~4,300 lines

### Grand Total
- **Code + Tests + Docs:** ~9,200 lines

---

## Timeline

**Week 1: Foundation**
- Task 1: .vibey/ structure design (8h)
- Task 2: Modular config system (12h)
- Task 3: Context loading strategy (16h)
- **Total:** 36 hours

**Week 2: Context & Summaries**
- Task 4: Summary generation (10h)
- **Total:** 10 hours

**Week 3: Platform Deployment**
- Task 5: Adapter pattern design (8h)
- Task 6: Claude adapter implementation (12h)
- Task 7: Deploy command (10h)
- **Total:** 30 hours

**Week 4: Integration & Documentation**
- Task 8: Docs generate command (8h)
- Task 9: Roadmap commands (6h)
- Task 10: Migration script (10h)
- Task 11: Update Vibey commands (12h)
- Task 12: Documentation (10h)
- Task 13: Testing (12h)
- **Total:** 58 hours

**Total Estimated:** 134 hours (~4 weeks with 2-3 developers)

---

## Risk Management

### Risk 1: Context loading doesn't achieve 80-90% reduction
**Likelihood:** Low
**Impact:** High
**Mitigation:**
- Early prototyping and benchmarking
- Test with various dependency graphs
- Adjust distance thresholds and summary sizes

### Risk 2: Breaking changes for existing users
**Likelihood:** Medium
**Impact:** High
**Mitigation:**
- Comprehensive migration script
- Backward compatibility testing
- Clear migration guide
- Rollback capability

### Risk 3: Platform adapter pattern too complex
**Likelihood:** Low
**Impact:** Medium
**Mitigation:**
- Clear interface definition
- Reference implementation (Claude)
- Comprehensive documentation
- Examples for Goose/Cursor

### Risk 4: Summary quality insufficient
**Likelihood:** Medium
**Impact:** Medium
**Mitigation:**
- Use LLM for summarization (Claude API)
- Human review of generated summaries
- Iterative refinement of prompts
- Fallback to structured format

---

## Success Criteria

### Functional
- ✅ `.vibey/` structure fully functional
- ✅ Config system modular and validated
- ✅ Context loading reduces size by 80-90%
- ✅ Platform deployments generated correctly
- ✅ Migration script works without data loss
- ✅ All `/vibey` commands updated

### Quality
- ✅ 100% test pass rate
- ✅ Performance targets met
- ✅ Documentation complete and accurate
- ✅ No regressions

### Strategic
- ✅ Foundation for multi-platform ready
- ✅ Adapter pattern validated
- ✅ Context explosion problem solved
- ✅ Goose port unblocked
- ✅ Sprint 1 (Default CLAUDE.md) can proceed

---

## Metrics to Track

### Code Quality
- Test coverage: Target ≥95%
- Linting errors: Target 0
- Type coverage: Target ≥90%

### Performance
- Context loading time: Target <100ms for 50 tasks
- Summary generation: Target <2s per task
- Deployment generation: Target <5s full deployment
- Context size reduction: Target 80-90%

### User Impact
- Migration success rate: Target 100%
- Breaking changes: Target 0
- User documentation: Target 100% coverage

---

## References

**Track Documentation:**
- `.vibey/tracks/core-framework.yaml`

**Related Design Docs:**
- `docs/development/ROADMAP_OBJECT_HIERARCHY.md`
- `docs/development/ROADMAP_IMPLEMENTATION_PLAN.md`
- `docs/FRAMEWORK_ROADMAP.md` (multi-platform strategy)

**Current Structure:**
- `framework/commands/vibey.md`
- `.vibey/` (current minimal structure)

---

## Appendix: File Structure Comparison

### Before (Current)
```
.claude/
├── CLAUDE.md (manually maintained)
├── agents/ (12 .md files)
├── workflows/ (16 .md files)
└── project-config.yaml

.vibey/
├── roadmap.yaml
├── tracks/
├── sprints/
└── tasks/
```

### After (New Architecture)
```
.vibey/ (Platform-Agnostic Core)
├── config/
│   ├── project.yaml
│   ├── framework.yaml
│   ├── agents/ (12 YAML files)
│   ├── workflows/ (16 YAML files)
│   └── quality-gates.yaml
├── roadmap/ (unchanged)
│   ├── roadmap.yaml
│   ├── tracks/
│   ├── sprints/
│   └── tasks/
├── sprint_docs/
│   └── <track>/<sprint>/
│       ├── plan.md
│       ├── architecture.md
│       └── learnings.md
├── summaries/ (gitignored)
│   ├── task_summaries/
│   └── dependency_summaries/
└── templates/
    ├── claude.md.j2
    ├── agent.md.j2
    └── workflow.md.j2

.claude/ (Generated - gitignored)
├── CLAUDE.md (generated from template)
├── agents/ (generated from config)
├── workflows/ (generated from config)
└── project-config.yaml (copy of .vibey/config/project.yaml)
```

**Key Difference:**
- **Before:** `.claude/` is source of truth (platform-specific)
- **After:** `.vibey/` is source of truth (platform-agnostic), `.claude/` is generated

---

**Sprint Created:** 2025-11-08
**Sprint Author:** coordinator, sprint-planner, web-developer, docs-writer
**Review Status:** Ready for execution
**Strategic Importance:** CRITICAL - Unblocks multi-platform tracks

---

## Impact on Sprint 1 (Default CLAUDE.md Auto-Generation)

**How Sprint 2 Affects Sprint 1:**

Sprint 1's goal is to auto-generate CLAUDE.md from configuration. Sprint 2 provides the foundation:

1. **Config System:** Sprint 2 creates `.vibey/config/project.yaml` and `framework.yaml` - Sprint 1 will use these as inputs
2. **Template System:** Sprint 2 creates `.vibey/templates/claude.md.j2` - Sprint 1 will use this template
3. **Platform Adapter:** Sprint 2 creates the adapter pattern - Sprint 1 will use `ClaudeAdapter.generate_instructions_file()`
4. **Generation Logic:** Sprint 2 implements template rendering - Sprint 1 extends it with dynamic sprint context

**Sprint 1 Implementation (After Sprint 2):**

```python
def generate_claude_md():
    # Uses Sprint 2 deliverables
    config = VibeyConfig()  # Sprint 2
    adapter = ClaudeAdapter()  # Sprint 2

    # Sprint 1 adds dynamic context
    context = {
        "project": config.load_project_config(),  # Sprint 2
        "framework": config.load_framework_config(),  # Sprint 2
        "agents": config.load_all_agents(),  # Sprint 2
        "workflows": config.load_all_workflows(),  # Sprint 2
        "current_sprint": load_current_sprint(),  # Sprint 1 (new)
        "active_tasks": load_active_tasks(),  # Sprint 1 (new)
        "recent_activity": load_recent_activity(),  # Sprint 1 (new)
    }

    # Uses Sprint 2 template + Sprint 1 dynamic data
    return adapter.generate_instructions_file_with_context(context)
```

**Recommendation:** Complete Sprint 2 first, then Sprint 1 becomes much simpler (uses Sprint 2 infrastructure + adds dynamic sprint context).

