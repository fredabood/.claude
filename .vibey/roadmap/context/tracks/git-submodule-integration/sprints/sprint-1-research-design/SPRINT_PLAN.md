# Sprint 1: Research & Design

## Overview
- **Track:** Git Submodule Integration
- **Sprint ID:** 01KCMTYK3KX9Q8B1ZS5Z4MRV7Q
- **Tasks:** 6
- **Focus:** Research patterns and design multi-repo roadmap integration

## Success Criteria
- [ ] Research complete on multi-repo patterns
- [ ] Detection/discovery mechanism designed
- [ ] Push-down requirements design complete
- [ ] Pull-up status aggregation designed
- [ ] Cross-repo dependencies specified
- [ ] Comprehensive design document produced

---

## Task 1: Research Git Submodule Integration Patterns
**ID:** `01KCMP1YQD3J2M0STQ9FNRKTPT`
**Priority:** High | **Complexity:** Medium | **Type:** Development

### Problem
Need to understand how other tools handle multi-repo/submodule scenarios before designing Vibey's approach.

### Research Areas
1. **Existing Tools:**
   - How does Nx handle monorepos?
   - How does Lerna manage cross-package dependencies?
   - How do issue trackers handle multi-repo projects?
   - How does git submodule work at the protocol level?

2. **Common Patterns:**
   - Monorepo vs polyrepo tradeoffs
   - Parent-child repo relationships
   - Dependency graph approaches
   - Status aggregation methods

3. **Sync Strategies:**
   - Push-down: Parent → Child
   - Pull-up: Child → Parent
   - Bidirectional sync
   - Event-based vs polling

### Implementation Steps
1. Research existing tools:
   ```markdown
   ## Tool Analysis

   ### Nx (Nrwl)
   - Uses project.json in each package
   - Dependency graph via implicit dependencies
   - Affected command for change detection

   ### Lerna
   - lerna.json at root
   - packages/* structure
   - Hoisting and symlinking

   ### Jira/GitHub Projects
   - Epic → Story → Subtask hierarchy
   - Cross-project linking via references
   - Status rollup via queries
   ```

2. Document patterns:
   ```markdown
   ## Patterns Identified

   ### Pattern A: Centralized Control
   Parent repo owns all roadmap data.
   Pros: Single source of truth
   Cons: Submodules lose autonomy

   ### Pattern B: Federated
   Each repo owns its roadmap, parent aggregates.
   Pros: Autonomy, parallel development
   Cons: Sync complexity

   ### Pattern C: Hybrid
   Parent defines requirements, submodules track execution.
   Pros: Balanced control/autonomy
   Cons: More complex to implement
   ```

3. Analyze sync strategies:
   ```markdown
   ## Sync Strategies

   ### Push-Down
   Parent creates requirement → Submodule creates implementing task
   - Good for: Top-down planning
   - Challenge: Submodule may not be ready

   ### Pull-Up
   Submodule completes task → Parent sees aggregated status
   - Good for: Status reporting
   - Challenge: Defining what "complete" means at parent level

   ### Bidirectional
   Changes flow both ways with conflict resolution
   - Good for: Full flexibility
   - Challenge: Conflict handling complexity
   ```

### Deliverables
- `MULTI_REPO_PATTERNS_RESEARCH.md`
- Tool comparison matrix
- Pattern analysis
- Sync strategy evaluation

### Acceptance Criteria
- [ ] 3+ existing tools researched
- [ ] Patterns documented
- [ ] Sync strategies evaluated
- [ ] Recommendations for Vibey

---

## Task 2: Define Submodule Detection and Discovery
**ID:** `01KCMP26A493MCX37CVRG8YSM0`
**Priority:** High | **Complexity:** Medium | **Type:** Development

### Problem
Need to define how Vibey detects and discovers submodules with their own roadmaps.

### Design Questions
1. Should Vibey auto-detect .gitmodules?
2. Should discovery require manual configuration?
3. How to identify submodules with .vibey/roadmap?
4. How to handle nested submodules?

### Implementation Steps
1. Design auto-detection:
   ```python
   # vibey/operations/git/submodule_discovery.py

   import subprocess
   from pathlib import Path
   from typing import List, Optional

   @dataclass
   class SubmoduleInfo:
       name: str
       path: Path
       url: str
       has_roadmap: bool
       roadmap_path: Optional[Path]

   def discover_submodules(repo_path: Path) -> List[SubmoduleInfo]:
       """Discover git submodules in repository."""
       gitmodules = repo_path / ".gitmodules"

       if not gitmodules.exists():
           return []

       # Parse .gitmodules
       result = subprocess.run(
           ['git', 'config', '--file', str(gitmodules), '-l'],
           capture_output=True, text=True, cwd=repo_path
       )

       submodules = parse_gitmodules_output(result.stdout)

       # Check for .vibey/roadmap in each
       for sm in submodules:
           sm_roadmap = repo_path / sm.path / ".vibey" / "roadmap"
           sm.has_roadmap = sm_roadmap.exists()
           if sm.has_roadmap:
               sm.roadmap_path = sm_roadmap

       return submodules
   ```

2. Design configuration option:
   ```yaml
   # .vibey/config/submodules.yaml

   submodules:
     discovery: auto  # auto | manual | disabled

     # Manual configuration (if discovery: manual)
     registered:
       - name: frontend
         path: packages/frontend
         track_as: frontend-module

       - name: backend
         path: packages/backend
         track_as: backend-module

     # Exclusions (applies to auto discovery)
     exclude:
       - vendor/*
       - third_party/*
   ```

3. Design roadmap identification:
   ```python
   def has_vibey_roadmap(submodule_path: Path) -> bool:
       """Check if submodule has its own Vibey roadmap."""
       roadmap_markers = [
           submodule_path / ".vibey" / "roadmap",
           submodule_path / ".vibey" / "roadmap.yaml",
           submodule_path / ".vibey" / "roadmap.db",
       ]
       return any(m.exists() for m in roadmap_markers)

   def get_roadmap_info(submodule_path: Path) -> Optional[dict]:
       """Get roadmap metadata from submodule."""
       roadmap_yaml = submodule_path / ".vibey" / "roadmap" / "roadmap.yaml"
       if roadmap_yaml.exists():
           with open(roadmap_yaml) as f:
               return yaml.safe_load(f)
       return None
   ```

4. Handle nested submodules:
   ```python
   def discover_recursive(
       repo_path: Path,
       max_depth: int = 3
   ) -> List[SubmoduleInfo]:
       """Recursively discover submodules."""
       all_submodules = []

       def _discover(path: Path, depth: int):
           if depth > max_depth:
               return

           submodules = discover_submodules(path)
           all_submodules.extend(submodules)

           # Recurse into submodules
           for sm in submodules:
               _discover(path / sm.path, depth + 1)

       _discover(repo_path, 0)
       return all_submodules
   ```

### Deliverables
- `SUBMODULE_DISCOVERY_DESIGN.md`
- Auto-detection algorithm
- Configuration schema
- Nested submodule handling

### Acceptance Criteria
- [ ] Auto-detection algorithm defined
- [ ] Configuration schema designed
- [ ] Nested submodule strategy
- [ ] CLI command design

---

## Task 3: Design Requirements Push-Down from Parent to Submodules
**ID:** `01KCMP2MN4SVE70FB55TXAV2EH`
**Priority:** Critical | **Complexity:** Complex | **Type:** Development

### Problem
Design how requirements flow from main project roadmap to submodule roadmaps.

### Design Questions
1. How are parent requirements expressed?
2. How do they translate to submodule tasks?
3. How is completion rolled up?
4. Who owns the requirement - parent or child?

### Implementation Steps
1. Design requirement expression:
   ```yaml
   # Parent task that pushes to submodules
   task:
     id: 01KC2D0JK9JKQX...
     title: Implement authentication
     description: Add authentication across all modules

     # NEW: Submodule requirements
     submodule_requirements:
       - submodule: frontend
         requirement: Add login UI components
         expected_tasks: 3
         owner: submodule  # submodule owns implementation

       - submodule: backend
         requirement: Add auth API endpoints
         expected_tasks: 5
         owner: submodule
   ```

2. Design push-down mechanism:
   ```python
   # vibey/operations/roadmap/submodule_sync.py

   @dataclass
   class SubmoduleRequirement:
       parent_task_id: str
       submodule_name: str
       requirement_text: str
       expected_tasks: int
       owner: str  # 'parent' | 'submodule'

   def push_requirement_to_submodule(
       parent_task_id: str,
       submodule_path: Path,
       requirement: SubmoduleRequirement
   ) -> str:
       """Create or link requirement in submodule roadmap."""

       # Load submodule roadmap
       sm_roadmap = load_roadmap(submodule_path / ".vibey" / "roadmap")

       # Create linked task in submodule
       linked_task = Task(
           title=requirement.requirement_text,
           description=f"Requirement from parent: {parent_task_id}",
           metadata={
               'parent_task_id': parent_task_id,
               'parent_repo': get_parent_repo_name(),
               'requirement_type': 'pushed',
           }
       )

       # Save to submodule
       save_task(linked_task, sm_roadmap)

       # Record linkage in parent
       record_submodule_link(parent_task_id, linked_task.id, submodule_path)

       return linked_task.id
   ```

3. Design ownership model:
   ```markdown
   ## Ownership Models

   ### Parent-Owned Requirement
   - Parent creates task outline
   - Submodule implements but parent tracks
   - Status flows up automatically
   - Parent can override/reassign

   ### Submodule-Owned Requirement
   - Parent expresses need
   - Submodule creates its own tasks
   - Submodule reports status
   - More autonomy, less control

   ### Shared Ownership
   - Parent and submodule both track
   - Sync mechanism keeps aligned
   - Conflict resolution needed
   ```

4. Design completion rollup:
   ```python
   def check_submodule_requirement_complete(
       parent_task_id: str
   ) -> RequirementStatus:
       """Check if submodule requirements are complete."""

       parent_task = load_task(parent_task_id)
       requirements = parent_task.submodule_requirements

       statuses = []
       for req in requirements:
           sm_path = get_submodule_path(req.submodule)
           linked_task_id = get_linked_task(parent_task_id, sm_path)

           if linked_task_id:
               sm_task = load_task_from_submodule(linked_task_id, sm_path)
               statuses.append({
                   'submodule': req.submodule,
                   'status': sm_task.status,
                   'complete': sm_task.status == Status.COMPLETED
               })
           else:
               statuses.append({
                   'submodule': req.submodule,
                   'status': 'not_linked',
                   'complete': False
               })

       return RequirementStatus(
           all_complete=all(s['complete'] for s in statuses),
           statuses=statuses
       )
   ```

### Deliverables
- `PUSH_DOWN_DESIGN.md`
- Requirement expression schema
- Push mechanism design
- Ownership model specification
- Completion rollup algorithm

### Acceptance Criteria
- [ ] Requirement schema defined
- [ ] Push mechanism designed
- [ ] Ownership models documented
- [ ] Rollup algorithm specified

---

## Task 4: Design Requirements Pull-Up from Submodules to Parent
**ID:** `01KCMP2V4FF9QP8ZDFZT5YZAV3`
**Priority:** Critical | **Complexity:** Complex | **Type:** Development

### Problem
Design how requirements/status pull up from submodule roadmaps to main project.

### Design Questions
1. How does parent see submodule progress?
2. How are submodule blockers surfaced?
3. How to aggregate completion across submodules?

### Implementation Steps
1. Design status aggregation:
   ```python
   # vibey/operations/roadmap/submodule_aggregation.py

   @dataclass
   class SubmoduleProgress:
       name: str
       tracks_total: int
       tracks_completed: int
       sprints_total: int
       sprints_completed: int
       tasks_total: int
       tasks_completed: int
       completion_percent: float
       blockers: List[str]
       last_updated: datetime

   def aggregate_submodule_progress(
       submodule_path: Path
   ) -> SubmoduleProgress:
       """Pull progress from submodule roadmap."""

       roadmap = load_roadmap(submodule_path / ".vibey" / "roadmap")

       # Count entities
       tracks = roadmap.tracks
       sprints = [s for t in tracks for s in t.sprints]
       tasks = [t for s in sprints for t in s.tasks]

       # Find blockers
       blockers = [
           t.title for t in tasks
           if t.blocked and t.status == Status.IN_PROGRESS
       ]

       return SubmoduleProgress(
           name=submodule_path.name,
           tracks_total=len(tracks),
           tracks_completed=len([t for t in tracks if t.status == Status.COMPLETED]),
           sprints_total=len(sprints),
           sprints_completed=len([s for s in sprints if s.status == Status.COMPLETED]),
           tasks_total=len(tasks),
           tasks_completed=len([t for t in tasks if t.status == Status.COMPLETED]),
           completion_percent=calculate_completion(tasks),
           blockers=blockers,
           last_updated=datetime.now()
       )
   ```

2. Design blocker surfacing:
   ```python
   @dataclass
   class SurfacedBlocker:
       source_submodule: str
       task_id: str
       task_title: str
       blocked_by: List[str]
       impact: str  # 'critical' | 'high' | 'medium'

   def surface_blockers_from_submodules(
       submodule_paths: List[Path]
   ) -> List[SurfacedBlocker]:
       """Surface critical blockers from submodules to parent."""

       blockers = []
       for sm_path in submodule_paths:
           roadmap = load_roadmap(sm_path / ".vibey" / "roadmap")

           for task in roadmap.all_tasks():
               if task.blocked:
                   blockers.append(SurfacedBlocker(
                       source_submodule=sm_path.name,
                       task_id=task.id,
                       task_title=task.title,
                       blocked_by=task.blocked_by,
                       impact=calculate_impact(task)
                   ))

       # Sort by impact
       blockers.sort(key=lambda b: ['critical', 'high', 'medium'].index(b.impact))
       return blockers
   ```

3. Design completion aggregation:
   ```python
   @dataclass
   class AggregatedCompletion:
       total_completion_percent: float
       submodule_completions: Dict[str, float]
       weighted_completion: float
       all_submodules_complete: bool

   def aggregate_completion(
       submodule_weights: Dict[str, float] = None
   ) -> AggregatedCompletion:
       """Aggregate completion across all submodules."""

       submodule_paths = discover_submodules(Path("."))
       completions = {}

       for sm in submodule_paths:
           progress = aggregate_submodule_progress(sm.path)
           completions[sm.name] = progress.completion_percent

       # Calculate weighted average
       if submodule_weights:
           weighted = sum(
               completions.get(name, 0) * weight
               for name, weight in submodule_weights.items()
           ) / sum(submodule_weights.values())
       else:
           weighted = sum(completions.values()) / len(completions)

       return AggregatedCompletion(
           total_completion_percent=weighted,
           submodule_completions=completions,
           weighted_completion=weighted,
           all_submodules_complete=all(c >= 100 for c in completions.values())
       )
   ```

4. Design parent dashboard:
   ```python
   def generate_parent_dashboard() -> dict:
       """Generate dashboard showing all submodule status."""

       submodules = discover_submodules(Path("."))

       return {
           'submodules': [
               {
                   'name': sm.name,
                   'path': str(sm.path),
                   'has_roadmap': sm.has_roadmap,
                   'progress': aggregate_submodule_progress(sm.path) if sm.has_roadmap else None
               }
               for sm in submodules
           ],
           'aggregated': aggregate_completion(),
           'blockers': surface_blockers_from_submodules([sm.path for sm in submodules]),
           'generated_at': datetime.now().isoformat()
       }
   ```

### Deliverables
- `PULL_UP_DESIGN.md`
- Status aggregation algorithm
- Blocker surfacing mechanism
- Completion aggregation design
- Dashboard specification

### Acceptance Criteria
- [ ] Status aggregation designed
- [ ] Blocker surfacing mechanism
- [ ] Weighted completion calculation
- [ ] Dashboard spec complete

---

## Task 5: Design Cross-Repo Dependency Tracking
**ID:** `01KCMP38FG3MBX9VKMW2QWYJEM`
**Priority:** High | **Complexity:** Complex | **Type:** Development

### Problem
Design how dependencies work across repository boundaries.

### Design Questions
1. Can a task in main depend on task in submodule?
2. How are cross-repo blockers tracked?
3. How does the criterion system span repos?

### Implementation Steps
1. Design cross-repo reference format:
   ```yaml
   # Reference format for cross-repo dependencies
   # Format: {repo}:{task_id}

   task:
     id: 01KC2D0JK9JKQX...
     depends_on:
       # Local dependency
       - blocker_id: 01KC2D0JK9JKQY...
         blocker_type: task

       # Cross-repo dependency (NEW)
       - blocker_id: frontend:01KCABC123...
         blocker_type: task
         blocker_repo: frontend  # Submodule name
         cross_repo: true
   ```

2. Design cross-repo dependency resolution:
   ```python
   # vibey/operations/roadmap/cross_repo_deps.py

   @dataclass
   class CrossRepoDependency:
       local_task_id: str
       remote_repo: str
       remote_task_id: str
       required_status: Status
       current_status: Optional[Status]
       is_blocking: bool

   def resolve_cross_repo_dependency(
       dep: CrossRepoDependency
   ) -> DependencyStatus:
       """Check status of cross-repo dependency."""

       # Get submodule path
       sm_path = get_submodule_path(dep.remote_repo)
       if not sm_path:
           return DependencyStatus(
               resolved=False,
               error=f"Submodule {dep.remote_repo} not found"
           )

       # Load remote task
       try:
           remote_task = load_task_from_path(
               sm_path / ".vibey" / "roadmap" / "tasks" / f"{dep.remote_task_id}.yaml"
           )
       except FileNotFoundError:
           return DependencyStatus(
               resolved=False,
               error=f"Task {dep.remote_task_id} not found in {dep.remote_repo}"
           )

       # Check status
       meets_requirement = remote_task.status == dep.required_status

       return DependencyStatus(
           resolved=True,
           met=meets_requirement,
           current_status=remote_task.status,
           required_status=dep.required_status
       )

   def check_all_cross_repo_deps(task_id: str) -> List[DependencyStatus]:
       """Check all cross-repo dependencies for a task."""
       task = load_task(task_id)
       cross_deps = [d for d in task.depends_on if d.get('cross_repo')]

       return [
           resolve_cross_repo_dependency(CrossRepoDependency(
               local_task_id=task_id,
               remote_repo=d['blocker_repo'],
               remote_task_id=d['blocker_id'].split(':')[1],
               required_status=Status(d['required_status']),
               current_status=None,
               is_blocking=True
           ))
           for d in cross_deps
       ]
   ```

3. Design criterion spanning repos:
   ```python
   class CrossRepoCriterion(CriterionTarget):
       """Criterion that spans repository boundaries."""

       def __init__(self, remote_repo: str, criterion_spec: dict):
           self.remote_repo = remote_repo
           self.criterion_spec = criterion_spec

       def evaluate(self, ticket_id: str) -> CriterionResult:
           """Evaluate criterion in remote repo context."""

           sm_path = get_submodule_path(self.remote_repo)
           if not sm_path:
               return CriterionResult(
                   passed=False,
                   message=f"Submodule {self.remote_repo} not found"
               )

           # Create criterion in remote context
           remote_criterion = create_criterion(
               self.criterion_spec,
               context_path=sm_path / ".vibey" / "roadmap"
           )

           # Evaluate in remote context
           return remote_criterion.evaluate(ticket_id)
   ```

4. Design blocker notification:
   ```python
   def notify_cross_repo_block(
       blocking_task_id: str,
       blocked_task_id: str,
       blocked_repo: str
   ) -> None:
       """Notify when cross-repo task is blocking another."""

       # Record in local roadmap
       activity_log.log_event({
           'type': 'cross_repo_block',
           'blocking_task': blocking_task_id,
           'blocked_task': blocked_task_id,
           'blocked_repo': blocked_repo,
           'timestamp': datetime.now().isoformat()
       })

       # Optionally notify in remote repo
       # (if bidirectional sync enabled)
   ```

### Deliverables
- `CROSS_REPO_DEPS_DESIGN.md`
- Reference format specification
- Resolution algorithm
- Criterion spanning design
- Notification mechanism

### Acceptance Criteria
- [ ] Reference format defined
- [ ] Resolution algorithm designed
- [ ] Criteria can span repos
- [ ] Blocking notifications specified

---

## Task 6: Produce Git Submodule Integration Design Document
**ID:** `01KCMP3EX1K7BVMF69WH8DC2DF`
**Priority:** High | **Complexity:** Medium | **Type:** Documentation

### Problem
Consolidate all research and design into comprehensive design document.

### Implementation Steps
Create `docs/architecture/GIT_SUBMODULE_INTEGRATION.md`:

```markdown
# Git Submodule Integration Design

## Executive Summary
This document describes how Vibey integrates with git submodules
to provide multi-repository roadmap management.

## Goals
1. Enable parent project to track progress across submodules
2. Allow requirements to flow from parent to submodules
3. Aggregate status from submodules to parent
4. Support cross-repo dependencies

## Non-Goals
1. Full bidirectional sync (phase 2)
2. Non-git multi-repo scenarios
3. Remote repository integration (GitHub, GitLab)

## Architecture Overview

### Component Diagram
```
┌─────────────────────────────────────────────┐
│              Parent Repository              │
│  ┌─────────────────────────────────────┐    │
│  │         Parent Roadmap              │    │
│  │  - Aggregated status                │    │
│  │  - Cross-repo dependencies          │    │
│  │  - Submodule requirements           │    │
│  └──────────────┬──────────────────────┘    │
│                 │                           │
│    ┌────────────┴────────────┐              │
│    │    Submodule Manager    │              │
│    │  - Discovery            │              │
│    │  - Push-down            │              │
│    │  - Pull-up              │              │
│    └────────────┬────────────┘              │
└─────────────────┼───────────────────────────┘
                  │
      ┌───────────┼───────────┐
      ▼           ▼           ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│Submodule │ │Submodule │ │Submodule │
│    A     │ │    B     │ │    C     │
│ roadmap  │ │ roadmap  │ │ roadmap  │
└──────────┘ └──────────┘ └──────────┘
```

## Detection & Discovery

### Auto-Detection
[Content from Task 2]

### Manual Configuration
[Content from Task 2]

## Push-Down Mechanism

### Requirement Expression
[Content from Task 3]

### Ownership Model
[Content from Task 3]

## Pull-Up Mechanism

### Status Aggregation
[Content from Task 4]

### Blocker Surfacing
[Content from Task 4]

## Cross-Repo Dependencies

### Reference Format
[Content from Task 5]

### Resolution Algorithm
[Content from Task 5]

## CLI Commands

### Discovery
```bash
vibey submodule discover       # Auto-discover submodules
vibey submodule list           # List configured submodules
vibey submodule add <path>     # Add submodule manually
```

### Status
```bash
vibey submodule status         # Show all submodule status
vibey submodule status <name>  # Show specific submodule
vibey submodule blockers       # Show cross-repo blockers
```

### Requirements
```bash
vibey submodule push <task> <submodule>   # Push requirement down
vibey submodule link <local> <remote>     # Link tasks manually
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `submodule_discover` | Discover submodules |
| `submodule_status` | Get submodule status |
| `submodule_push_requirement` | Push requirement to submodule |
| `submodule_link_task` | Link cross-repo tasks |
| `submodule_aggregate` | Get aggregated completion |

## Implementation Roadmap

### Phase 1: Read-Only Integration
- Discovery and listing
- Status aggregation
- Blocker surfacing

### Phase 2: Write Integration
- Push-down requirements
- Cross-repo dependencies
- Completion rollup

### Phase 3: Full Sync
- Bidirectional sync
- Conflict resolution
- Webhooks/events

## Open Questions
1. How to handle submodule version pinning?
2. Should we support non-submodule multi-repo?
3. How to handle stale submodule data?

## References
- [Git Submodules Documentation](https://git-scm.com/book/en/v2/Git-Tools-Submodules)
- [MULTI_REPO_PATTERNS_RESEARCH.md](context/research/MULTI_REPO_PATTERNS_RESEARCH.md)
```

### Deliverables
- `docs/architecture/GIT_SUBMODULE_INTEGRATION.md`
- Comprehensive design covering all aspects
- CLI command specifications
- MCP tool specifications
- Implementation phases

### Acceptance Criteria
- [ ] All research consolidated
- [ ] Design complete and coherent
- [ ] CLI commands specified
- [ ] MCP tools specified
- [ ] Implementation roadmap defined

---

## Sprint Completion Checklist
- [ ] Multi-repo patterns researched
- [ ] Detection/discovery mechanism designed
- [ ] Push-down requirements designed
- [ ] Pull-up aggregation designed
- [ ] Cross-repo dependencies specified
- [ ] Design document complete
- [ ] CLI commands specified
- [ ] MCP tools specified
