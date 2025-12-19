# Cross-Repo Dependency Tracking Design

**Task:** 01KCMP38FG3MBX9VKMW2QWYJEM
**Date:** 2025-12-19
**Status:** Complete

---

## Overview

This document defines how dependencies work across repository boundaries. The design extends the existing criterion system to span multiple repos while integrating with the Unified Ticket Architecture.

---

## 1. Core Concept

**Cross-repo dependency** = A ticket in one repo depends on a ticket in another repo.

```
PARENT REPO                              SUBMODULE REPO
┌──────────────────────┐                ┌──────────────────────┐
│ Ticket: MAIN-001     │                │ Ticket: AUTH-042     │
│ "Deploy OAuth"       │                │ "Implement OAuth"    │
│                      │────────────────│                      │
│ depends_on:          │  CrossRepoDep  │ depended_on_by:      │
│   - AUTH-042@libs/auth               │   - MAIN-001@parent  │
└──────────────────────┘                └──────────────────────┘
```

---

## 2. CrossRepoDependency Entity

```python
@dataclass
class CrossRepoDependency:
    """Represents a dependency between tickets in different repos."""
    id: str                              # ULID

    # Dependent (the ticket that is waiting)
    dependent_roadmap_id: str
    dependent_ticket_id: str
    dependent_repo_path: str             # For routing

    # Dependency (the ticket being waited on)
    dependency_roadmap_id: str
    dependency_ticket_id: str
    dependency_repo_path: str            # Submodule path or "." for parent

    # Dependency characteristics
    dependency_type: DependencyType
    blocking: bool                       # Does this block progress?
    soft_dependency: bool                # Advisory vs hard requirement

    # Resolution criteria
    resolution_criteria: ResolutionCriteria

    # Status
    status: DependencyStatus
    created_at: datetime
    resolved_at: Optional[datetime]

    # Metadata
    created_by: str                      # User/agent that created
    reason: Optional[str]                # Why this dependency exists


class DependencyType(Enum):
    COMPLETION = "completion"            # Wait for ticket completion
    ARTIFACT = "artifact"                # Wait for specific artifact
    INTERFACE = "interface"              # Wait for API/interface
    MILESTONE = "milestone"              # Wait for milestone/gate
    APPROVAL = "approval"                # Wait for sign-off


class DependencyStatus(Enum):
    ACTIVE = "active"                    # Dependency not yet satisfied
    SATISFIED = "satisfied"              # Dependency met
    CANCELLED = "cancelled"              # Dependency removed
    FAILED = "failed"                    # Cannot be satisfied


@dataclass
class ResolutionCriteria:
    """What needs to happen for dependency to be satisfied."""
    criteria_type: str                   # "ticket_complete" | "artifact_exists" | "custom"

    # For ticket_complete
    required_status: Optional[str] = "completed"

    # For artifact_exists
    artifact_patterns: List[str] = field(default_factory=list)

    # For custom
    custom_criterion_id: Optional[str] = None
```

---

## 3. Dependency Reference Syntax

### 3.1 Cross-Repo Ticket References

```
<ticket_id>@<repo_path>

Examples:
  AUTH-042@libs/auth          # Ticket in libs/auth submodule
  MAIN-001@.                  # Ticket in parent repo (from submodule perspective)
  UI-015@libs/ui              # Ticket in sibling submodule
  01KCXYZ123@libs/auth        # ULID-based reference
```

### 3.2 In YAML

```yaml
# Parent ticket depending on submodule ticket
task:
  id: 01TASK_DEPLOY_OAUTH
  title: Deploy OAuth to production
  cross_repo_depends_on:
    - ticket_ref: 01TASK_IMPL_OAUTH@libs/auth
      type: completion
      blocking: true
      reason: Cannot deploy until OAuth is implemented
```

```yaml
# Submodule ticket depended on by parent
task:
  id: 01TASK_IMPL_OAUTH
  title: Implement OAuth
  cross_repo_depended_on_by:
    - ticket_ref: 01TASK_DEPLOY_OAUTH@..
      type: completion
```

---

## 4. Extended Criterion System

### 4.1 CrossRepoCriterionTarget

```python
class CrossRepoCriterionTarget(CriterionTarget):
    """Criterion that evaluates state in another repo."""
    target_type: str = "cross_repo"

    # Target location
    repo_path: str                       # Submodule path or ".." for parent
    ticket_id: str                       # Ticket to evaluate

    # What to check
    check_type: CrossRepoCheckType
    required_value: Any                  # Depends on check_type

    def evaluate(self, context: EvaluationContext) -> CriterionResult:
        # Resolve cross-repo reference
        target_roadmap = context.resolve_repo(self.repo_path)
        target_ticket = target_roadmap.get_ticket(self.ticket_id)

        if self.check_type == CrossRepoCheckType.STATUS:
            return self._check_status(target_ticket)
        elif self.check_type == CrossRepoCheckType.ARTIFACT:
            return self._check_artifact(target_ticket)
        # ...


class CrossRepoCheckType(Enum):
    STATUS = "status"                    # Check ticket status
    ARTIFACT = "artifact"                # Check artifact exists
    PROGRESS = "progress"                # Check progress >= threshold
    CRITERION = "criterion"              # Evaluate specific criterion
```

### 4.2 Usage Examples

```yaml
# Wait for submodule ticket to be completed
criteria:
  - id: crit-oauth-complete
    name: OAuth implementation complete
    target:
      target_type: cross_repo
      repo_path: libs/auth
      ticket_id: 01TASK_IMPL_OAUTH
      check_type: status
      required_value: completed

# Wait for submodule artifact to exist
criteria:
  - id: crit-oauth-module
    name: OAuth module exists
    target:
      target_type: cross_repo
      repo_path: libs/auth
      ticket_id: 01TASK_IMPL_OAUTH
      check_type: artifact
      required_value:
        pattern: "src/oauth/**/*.py"
        min_count: 1
```

---

## 5. Dependency Resolution Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                  CROSS-REPO DEPENDENCY RESOLUTION                    │
├─────────────────────────────────────────────────────────────────────┤
│  TRIGGER: Ticket status check or criterion evaluation                │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 1: Identify Cross-Repo Dependencies                            │
│    • Read ticket's cross_repo_depends_on list                        │
│    • Parse repo_path@ticket_id references                            │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 2: Resolve Target Repos                                        │
│    For each dependency:                                              │
│      • Locate submodule via SubmoduleRegistry                        │
│      • Verify submodule has Vibey roadmap                            │
│      • Get path to submodule's .vibey/roadmap                        │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 3: Evaluate Each Dependency                                    │
│    For each dependency:                                              │
│      • Load target ticket from submodule                             │
│      • Check resolution_criteria                                     │
│      • Return DependencyStatus                                       │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 4: Aggregate Results                                           │
│    • All blocking deps satisfied → ticket can proceed                │
│    • Any blocking dep unsatisfied → ticket blocked                   │
│    • Update ticket.blocked and ticket.blocked_reason                 │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 5: Update Cross-Repo Status                                    │
│    • Mark satisfied dependencies                                     │
│    • Update timestamps                                               │
│    • Notify dependent tickets (pull-up mechanism)                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. Circular Dependency Detection

### 6.1 Cross-Repo Cycle Detection

```python
class CrossRepoDependencyResolver:
    """Resolves and validates cross-repo dependencies."""

    def detect_cycles(self, start_ticket: str, start_repo: str) -> List[DependencyCycle]:
        """Detect circular dependencies spanning repos."""
        visited = set()
        path = []

        def dfs(ticket_id: str, repo_path: str) -> Optional[DependencyCycle]:
            key = f"{ticket_id}@{repo_path}"
            if key in path:
                cycle_start = path.index(key)
                return DependencyCycle(path[cycle_start:] + [key])

            if key in visited:
                return None

            visited.add(key)
            path.append(key)

            deps = self._get_dependencies(ticket_id, repo_path)
            for dep in deps:
                cycle = dfs(dep.ticket_id, dep.repo_path)
                if cycle:
                    return cycle

            path.pop()
            return None

        return dfs(start_ticket, start_repo)


@dataclass
class DependencyCycle:
    """Represents a circular dependency."""
    cycle_path: List[str]  # List of ticket@repo references

    @property
    def description(self) -> str:
        return " → ".join(self.cycle_path)
```

### 6.2 CLI Validation

```bash
# Check for circular dependencies
vibey submodule validate-deps

# Output:
# Checking cross-repo dependencies...
# ⚠ CYCLE DETECTED:
#   MAIN-001@. → AUTH-042@libs/auth → API-015@libs/api → MAIN-001@.
#
# Resolution suggestions:
#   1. Remove dependency MAIN-001 → AUTH-042
#   2. Make AUTH-042 → API-015 non-blocking
```

---

## 7. Storage Structure

### 7.1 Parent Side

```
.vibey/roadmap/
├── cross_repo_deps/
│   ├── outgoing/                # Dependencies on submodule tickets
│   │   └── 01DEP_001.yaml
│   └── incoming/                # Dependencies from submodule tickets
│       └── 01DEP_002.yaml
```

### 7.2 SQLite Schema

```sql
CREATE TABLE cross_repo_dependencies (
    id TEXT PRIMARY KEY,

    -- Dependent (waiting)
    dependent_roadmap_id TEXT NOT NULL,
    dependent_ticket_id TEXT NOT NULL,
    dependent_repo_path TEXT NOT NULL,

    -- Dependency (waited on)
    dependency_roadmap_id TEXT NOT NULL,
    dependency_ticket_id TEXT NOT NULL,
    dependency_repo_path TEXT NOT NULL,

    -- Characteristics
    dependency_type TEXT NOT NULL,
    blocking INTEGER NOT NULL DEFAULT 1,
    soft_dependency INTEGER NOT NULL DEFAULT 0,
    resolution_criteria_json TEXT,

    -- Status
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    resolved_at TEXT,

    -- Metadata
    created_by TEXT,
    reason TEXT,

    UNIQUE(dependent_ticket_id, dependency_ticket_id, dependency_repo_path)
);

CREATE INDEX idx_cross_deps_dependent ON cross_repo_dependencies(dependent_ticket_id);
CREATE INDEX idx_cross_deps_dependency ON cross_repo_dependencies(dependency_ticket_id, dependency_repo_path);
```

---

## 8. API Design

### 8.1 CLI Commands

```bash
# Add cross-repo dependency
vibey task add-cross-dep <ticket> <dependency-ref>
# Example: vibey task add-cross-dep MAIN-001 AUTH-042@libs/auth

# List cross-repo dependencies
vibey task cross-deps <ticket>
# vibey task cross-deps --direction outgoing  # What I depend on
# vibey task cross-deps --direction incoming  # What depends on me

# Check dependency status
vibey submodule dep-status <dependency-id>

# Validate all cross-repo dependencies
vibey submodule validate-deps

# Visualize cross-repo dependency graph
vibey submodule dep-graph
```

### 8.2 MCP Tools

```python
@mcp_tool
def task_add_cross_dep(
    ticket_id: str,
    dependency_ref: str,  # ticket@repo format
    dependency_type: str = "completion",
    blocking: bool = True,
    reason: Optional[str] = None
) -> CrossRepoDependency:
    """Add a cross-repo dependency to a ticket."""

@mcp_tool
def task_cross_deps(
    ticket_id: str,
    direction: str = "outgoing"  # "outgoing" | "incoming" | "both"
) -> List[CrossRepoDependency]:
    """List cross-repo dependencies for a ticket."""

@mcp_tool
def submodule_dep_graph() -> DependencyGraph:
    """Get the full cross-repo dependency graph."""

@mcp_tool
def submodule_validate_deps() -> ValidationResult:
    """Validate cross-repo dependencies (cycles, missing targets)."""
```

---

## 9. Integration with Existing Systems

### 9.1 With Blocked Status

When a cross-repo dependency is unsatisfied:

```python
def update_blocked_status(ticket: Ticket) -> None:
    """Update ticket blocked status based on cross-repo deps."""
    cross_deps = get_cross_repo_dependencies(ticket.id, direction="outgoing")
    blocking_deps = [d for d in cross_deps if d.blocking and d.status == "active"]

    if blocking_deps:
        ticket.blocked = True
        ticket.blocked_reason = f"Waiting on: {', '.join(d.reference for d in blocking_deps)}"
    else:
        # Check local dependencies too
        ticket.blocked = check_local_dependencies(ticket)
```

### 9.2 With Pre-Commit Hook

Triangle validation extended for cross-repo:

```python
def validate_cross_repo_completion(ticket_id: str) -> ValidationResult:
    """Check if all cross-repo deps are satisfied before completion."""
    deps = get_cross_repo_dependencies(ticket_id, direction="outgoing")
    unsatisfied = [d for d in deps if d.blocking and d.status != "satisfied"]

    if unsatisfied:
        return ValidationResult(
            valid=False,
            message=f"Cannot complete: {len(unsatisfied)} cross-repo deps unsatisfied",
            details=[d.reference for d in unsatisfied]
        )
    return ValidationResult(valid=True)
```

---

## 10. Configuration

```yaml
# .vibey/config/submodules.yaml
cross_repo_deps:
  enabled: true

  # Validation
  validation:
    check_cycles: true
    check_missing_targets: true
    block_on_cycle: true

  # Resolution
  resolution:
    auto_satisfy_on_completion: true  # Auto-satisfy when target completes
    poll_interval_minutes: 0          # 0 = only on-demand

  # Notifications
  notifications:
    on_dependency_satisfied: true
    on_dependency_blocked: true
```

---

## Next Steps

1. → Task 6: Produce comprehensive design document consolidating all findings
