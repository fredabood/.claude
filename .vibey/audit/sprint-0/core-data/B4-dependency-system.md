# B4: Dependency System Audit

**Task ID:** 01KFXF8Z78A5B8QCFB5C04PKDG
**Phase:** B4: Core Data Model
**Date:** 2026-01-29

## Executive Summary

Complete documentation of the Vibey dependency system, covering dependency fields, blocking semantics, circular dependency detection, and critical path analysis. The system uses a dual approach: the legacy model has `dependencies`, `blocks`, `blocked_by`, and `depends_on` fields, while the unified ticket architecture uses `Criterion` objects with `blocks_transition_to` for dependency blocking. Key finding: `depends_on` is the cached source of truth for blocked status computation, while `blocked_by` is deprecated. The dependency resolution algorithm uses DFS for both circular detection and transitive dependency computation.

## Methodology

**Files Analyzed:**
- `vibey/roadmap/models/task.py:218-370` - Task dependency fields and validation
- `vibey/cli/roadmap_lib/dependencies.py:1-267` - DependencyResolver class
- `vibey/cli/roadmap_lib/blockers.py:1-320` - BlockerComputer class
- `vibey/roadmap/models/ticket/completable.py:32-168` - Criterion-based blocking

## Findings

### 2. Dependency Fields Table

| Field | Type | Direction | Semantics | Example |
|-------|------|-----------|-----------|---------|
| `dependencies` | List[TaskDependency] | Forward | What I depend on (authored data) | `[{target_id: "task-001", type: "task", target_status: "completed"}]` |
| `blocks` | List[TaskDependency] | Forward | What I block from starting (forward index) | `[{target_id: "task-003", type: "task"}]` |
| `blocked_by` | List[TaskBlocker] | Backward | What's blocking me (DEPRECATED) | `[{dependency_id: "task-001", required_status: "completed"}]` |
| `depends_on` | List[DependencyStatus] | Cached | Cached blocker status with satisfaction check | `[{blocker_id: "task-001", current_status: "in_progress", is_satisfied: false}]` |
| `depended_on_by` | List[str] | Reverse | IDs depending on me (reverse index) | `["task-003", "task-004"]` |
| `development_gates` | List[DevelopmentGate] | Forward | Sprint external dependencies | `[{target_id: "api-ready", type: "external"}]` |

### 3. Dependency Semantics Table

| Relationship | Meaning | Blocked Computation | Use Case |
|--------------|---------|---------------------|----------|
| `dependencies` | "I need X to reach status Y before I can start" | Source of truth for what's needed | Task ordering, critical path |
| `blocks` | "I am blocking X from starting" | Forward index for quick lookup | Cascade unblock notification |
| `blocked_by` | "X is currently blocking me" (deprecated) | Legacy, replaced by depends_on | Backward compatibility |
| `depends_on` | "Cached status of my dependencies" | `blocked = any(not dep.is_satisfied())` | Fast blocked check without file I/O |
| `depended_on_by` | "These entities depend on me" | Not used for blocking | Cascade update when I complete |

### 4. Validation Rules Table

| Rule | Check | Error | Recovery |
|------|-------|-------|----------|
| Circular dependency | DFS cycle detection | "Circular dependency detected: A → B → C → A" | Remove one edge in cycle |
| Missing dependency | `_get_object_status()` returns None | "Dependency 'X' not found" | Create referenced entity or remove dependency |
| Self-dependency | target_id == self.id | "Entity cannot depend on itself" | Remove self-reference |
| Cross-type validity | Task→Task, Sprint→Sprint, Track→Track | "Invalid dependency type" | Change to valid type |
| Status progression | `_status_satisfied()` check | "Required status 'completed' not met (current: 'in_progress')" | Complete dependency first |
| Gate type mismatch | completion_gate → blocks_status = "completed" | "Gate type mismatch" | Align gate type with blocks_status |

### 5. Blocked Status Propagation Table

| Event | Effect | Cascade | Timing |
|-------|--------|---------|--------|
| Dependency completes | depends_on[i].current_status updated | Recompute blocked for dependent | Immediate |
| Dependency regresses | depends_on[i].is_satisfied → false | blocked = true for dependent | Immediate |
| All dependencies satisfied | blocked = false | Unblock dependent | Immediate |
| New dependency added | depends_on[] grows | Recompute blocked | On save |
| Dependency removed | depends_on[] shrinks | Recompute blocked | On save |
| Entity status changes | depended_on_by notified | Update their depends_on cache | On save |

**Blocked Computation Code:**
```python
# From task.py:326-330
def is_blocked_by_deps(self) -> bool:
    """Compute blocked status from depends_on array."""
    return any(not dep.is_satisfied() for dep in self.depends_on)
```

### 6. Dependency Resolution Algorithm

```
ALGORITHM: Build Dependency Graph
INPUT: roadmap_path
OUTPUT: dependency_graph (Dict[str, DependencyNode])

1. LOAD roadmap from roadmap_path
2. ADD roadmap node to graph (no dependencies)
3. FOR each track in roadmap.tracks:
   a. LOAD track from track_path
   b. EXTRACT depends_on IDs from track.dependencies
   c. ADD track node to graph
   d. FOR each sprint in track.sprints:
      i.   LOAD sprint from sprint_path
      ii.  EXTRACT depends_on IDs from sprint.development_gates
      iii. ADD sprint node to graph
      iv.  FOR each task in sprint.tasks:
           - IF task.is_quality_gate(): SKIP
           - EXTRACT depends_on IDs from task.dependencies
           - ADD task node to graph
4. RETURN graph


ALGORITHM: Detect Circular Dependencies (DFS)
INPUT: dependency_graph
OUTPUT: cycles (List[List[str]])

1. INITIALIZE visited = {}, rec_stack = {}, cycles = []
2. FUNCTION dfs(node_id, path):
   a. IF node_id IN rec_stack: FOUND CYCLE
      - cycle = path[cycle_start:] + [node_id]
      - ADD cycle to cycles
      - RETURN
   b. IF node_id IN visited: RETURN
   c. ADD node_id to visited and rec_stack
   d. FOR each dep in graph[node_id].depends_on:
      - dfs(dep, path + [node_id])
   e. REMOVE node_id from rec_stack
3. FOR each node in graph: dfs(node, [])
4. RETURN cycles


ALGORITHM: Get Transitive Dependencies (DFS)
INPUT: object_id, dependency_graph
OUTPUT: all_deps (Set[str])

1. INITIALIZE visited = set()
2. FUNCTION visit(node_id):
   a. IF node_id IN visited OR node_id NOT IN graph: RETURN
   b. ADD node_id to visited
   c. FOR each dep in graph[node_id].depends_on:
      - visit(dep)
3. FOR each dep in graph[object_id].depends_on:
   - visit(dep)
4. RETURN visited
```

### 7. Critical Path Analysis Table

| Algorithm Step | Input | Output | Complexity |
|----------------|-------|--------|------------|
| Build dependency graph | All entity files | Dict[id, DependencyNode] | O(E) where E = entities |
| Topological sort | Dependency graph | Ordered list of tasks | O(V + E) |
| Find longest path | Topological order + durations | Critical path tasks | O(V + E) |
| Identify parallel tasks | Topological order | Groups of independent tasks | O(V) |
| Compute slack time | Critical path + all paths | Slack per task | O(V * E) |

**Critical Path Identification (not yet implemented):**
```
1. TOPOLOGICAL_SORT the dependency graph
2. COMPUTE earliest_start[task] = max(earliest_finish[dep] for dep in depends_on)
3. COMPUTE earliest_finish[task] = earliest_start[task] + duration[task]
4. COMPUTE latest_finish[task] = min(latest_start[dependent] for dependent in depended_on_by)
5. COMPUTE latest_start[task] = latest_finish[task] - duration[task]
6. CRITICAL PATH = tasks where slack = latest_start - earliest_start = 0
```

### 8. Remote Sync Strategy Table

| Scenario | Challenge | Strategy | Trade-offs |
|----------|-----------|----------|------------|
| Stale depends_on cache | Local cache out of sync with remote | Pull remote status before transition check | Latency vs accuracy |
| Concurrent dependency completion | Two users complete blocking task | Last-write-wins for depends_on cache | Eventual consistency |
| New dependency added remotely | Local doesn't know about new blocker | Pull dependencies before start | May block unexpectedly |
| Dependency removed remotely | Local thinks it's still blocked | Pull dependencies before blocked check | May unblock unexpectedly |
| Circular dependency created | Two remotes add conflicting deps | Reject on merge, require manual fix | Preserves integrity |
| Cross-workspace dependencies | Dependency in different workspace | External dependency type with webhook | Polling overhead |
| Offline dependency changes | Local changes while offline | Merge with conflict detection | May need manual resolution |

**Sync Protocol:**
1. **Before start()**: Pull latest `depends_on` for target entity
2. **After complete()**: Push updated status, trigger webhook for `depended_on_by` entities
3. **On merge conflict**: Compare timestamps, keep latest, recompute `blocked`
4. **For external deps**: Poll status periodically or use webhooks

## Remote Mode Implications

| Finding | Recommendation | Effort | Priority |
|---------|----------------|--------|----------|
| depends_on is cached status | Implement cache invalidation on remote status change | M | Critical |
| blocked_by is deprecated | Do not replicate to Delta Lake | S | Low |
| Circular detection uses DFS | Run validation on remote before accepting new deps | M | High |
| depended_on_by is reverse index | Maintain as materialized view in Delta Lake | M | Medium |
| BlockerComputer loads files | Replace with Delta Lake queries | L | High |
| Status ordering is hardcoded | Store order in config table for remote | S | Medium |

## Verification Checklist

- [x] Deliverable file exists at specified path: PASS
- [x] All 4 dependency fields documented: PASS (5 fields: dependencies, blocks, blocked_by, depends_on, depended_on_by)
- [x] Blocked status propagation rules documented: PASS (6 events with effects)
- [x] Critical path algorithm documented: PASS (5-step algorithm with complexity)
- [x] Remote sync strategy addresses stale dependencies: PASS (7 scenarios with strategies)

## References

- `vibey/roadmap/models/task.py:222-227` - Task dependency field definitions
- `vibey/roadmap/models/task.py:320-338` - is_blocked_by_deps() and related methods
- `vibey/cli/roadmap_lib/dependencies.py:30-131` - DependencyResolver class
- `vibey/cli/roadmap_lib/dependencies.py:132-173` - detect_circular_dependencies()
- `vibey/cli/roadmap_lib/blockers.py:24-274` - BlockerComputer class
- `vibey/cli/roadmap_lib/blockers.py:241-273` - _status_satisfied() implementation
