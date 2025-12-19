# Requirements Pull-Up Mechanism Design

**Task:** 01KCMP2V4FF9QP8ZDFZT5YZAV3
**Date:** 2025-12-19
**Status:** Complete

---

## Overview

This document defines how status and progress pull up from submodule roadmaps to the parent project. The design integrates with the Unified Ticket Architecture's Triangle Model.

---

## 1. Core Concept

**Pull-up** = Parent roadmap aggregates information from submodule roadmaps.

```
SUBMODULE ROADMAPS                      PARENT ROADMAP
┌──────────────────┐                   ┌──────────────────────┐
│ libs/auth: 80%   │──────────────────▶│ Aggregated Progress  │
└──────────────────┘                   │                      │
┌──────────────────┐   ProgressPullUp  │ Submodules: 75%      │
│ libs/ui: 100%    │──────────────────▶│ - libs/auth: 80%     │
└──────────────────┘                   │ - libs/ui: 100%      │
┌──────────────────┐                   │ - libs/api: 45%      │
│ libs/api: 45%    │──────────────────▶│                      │
└──────────────────┘                   │ Blockers: 2          │
                                       └──────────────────────┘
```

---

## 2. What Gets Pulled Up

### 2.1 Progress Metrics

```python
@dataclass
class SubmoduleProgress:
    """Progress summary from a single submodule."""
    submodule_path: str
    roadmap_id: str

    # Track-level progress
    tracks_total: int
    tracks_completed: int
    tracks_in_progress: int

    # Sprint-level progress
    sprints_total: int
    sprints_completed: int

    # Task-level progress
    tasks_total: int
    tasks_completed: int
    tasks_in_progress: int
    tasks_blocked: int

    # Computed
    completion_percent: float

    # Timing
    last_activity_at: Optional[datetime]
    estimated_completion: Optional[datetime]

    # Collected at
    collected_at: datetime
```

### 2.2 Blocker Information

```python
@dataclass
class SubmoduleBlocker:
    """A blocker in a submodule that may affect parent."""
    submodule_path: str
    roadmap_id: str

    # The blocked item
    blocked_ticket_id: str
    blocked_ticket_title: str
    blocked_ticket_type: str  # track, sprint, task

    # Blocking reason
    blocked_reason: str
    blocked_by: List[str]  # Ticket IDs causing block

    # Cross-repo impact
    affects_parent_tickets: List[str]  # Parent tickets waiting on this

    # Severity
    severity: BlockerSeverity
    since: datetime


class BlockerSeverity(Enum):
    CRITICAL = "critical"    # Blocks parent completion
    HIGH = "high"            # Affects parent timeline
    MEDIUM = "medium"        # May delay parent
    LOW = "low"              # Informational
```

### 2.3 Requirement Fulfillment Status

```python
@dataclass
class RequirementFulfillment:
    """Status of a pushed requirement."""
    requirement_id: str
    source_ticket_id: str  # Parent ticket that pushed

    # Current state
    status: RequirementStatus
    target_ticket_id: Optional[str]
    target_ticket_status: Optional[str]

    # Progress on fulfillment
    artifacts_required: int
    artifacts_completed: int
    criteria_required: int
    criteria_met: int

    # Timeline
    acknowledged_at: Optional[datetime]
    estimated_completion: Optional[datetime]
    actual_completion: Optional[datetime]
```

---

## 3. AggregatedProgress Entity

```python
@dataclass
class AggregatedProgress:
    """Rolled-up progress from all submodules."""
    id: str                              # ULID
    parent_roadmap_id: str

    # Per-submodule breakdown
    submodule_progress: Dict[str, SubmoduleProgress]

    # Aggregated totals
    total_submodules: int
    submodules_with_roadmaps: int

    # Combined metrics (weighted by task count)
    combined_completion_percent: float
    combined_tasks_total: int
    combined_tasks_completed: int
    combined_tasks_blocked: int

    # Blockers affecting parent
    blockers: List[SubmoduleBlocker]
    critical_blocker_count: int

    # Requirements status
    requirements_pushed: int
    requirements_fulfilled: int
    requirements_pending: int

    # Collection metadata
    collected_at: datetime
    collection_method: CollectionMethod
    stale_threshold_minutes: int = 60


class CollectionMethod(Enum):
    POLLING = "polling"           # Scheduled pull
    ON_DEMAND = "on_demand"       # User-triggered
    WEBHOOK = "webhook"           # Push notification from submodule
    GIT_HOOK = "git_hook"         # Triggered by git operation
```

---

## 4. Pull-Up Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                       PULL-UP FLOW                                   │
├─────────────────────────────────────────────────────────────────────┤
│  TRIGGER: One of:                                                    │
│    • User runs: vibey submodule status                               │
│    • Scheduled poll (configurable interval)                          │
│    • Git hook (post-merge, post-checkout)                            │
│    • Parent roadmap status check                                     │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 1: Enumerate Submodules                                        │
│    • Read SubmoduleRegistry from discovery                           │
│    • Filter to has_vibey_roadmap=True                                │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 2: Collect Per-Submodule Progress                              │
│    For each submodule:                                               │
│      • Read .vibey/roadmap/roadmap.yaml for summary                  │
│      • Query SQLite for detailed metrics                             │
│      • Build SubmoduleProgress record                                │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 3: Identify Blockers                                           │
│    For each submodule:                                               │
│      • Query for blocked=true tickets                                │
│      • Check if blocker affects any CrossRepoRequirement             │
│      • Build SubmoduleBlocker records with severity                  │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 4: Check Requirement Fulfillment                               │
│    For each CrossRepoRequirement with status != FULFILLED:           │
│      • Query submodule for target_ticket_id status                   │
│      • Check artifact completion                                     │
│      • Check criteria satisfaction                                   │
│      • Update RequirementFulfillment                                 │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 5: Aggregate                                                   │
│    • Combine per-submodule progress (weighted average)               │
│    • Collect all blockers sorted by severity                         │
│    • Build AggregatedProgress record                                 │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 6: Persist & Notify                                            │
│    • Store AggregatedProgress in parent's .vibey/roadmap/            │
│    • Update parent's roadmap.yaml with submodule summary             │
│    • If critical blockers: emit warning/notification                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Storage Structure

### 5.1 Parent Side

```
.vibey/roadmap/
├── submodule_progress/
│   ├── .aggregated.yaml         # Latest AggregatedProgress
│   ├── libs-auth.yaml           # SubmoduleProgress snapshot
│   ├── libs-ui.yaml
│   └── history/                 # Historical snapshots
│       └── 2025-12-19T19-00.yaml
```

**Example .aggregated.yaml:**
```yaml
aggregated_progress:
  id: 01KCX_AGG_001
  parent_roadmap_id: parent-app-v2

  submodule_progress:
    libs/auth:
      completion_percent: 80
      tasks_total: 50
      tasks_completed: 40
      tasks_blocked: 2
    libs/ui:
      completion_percent: 100
      tasks_total: 30
      tasks_completed: 30
      tasks_blocked: 0
    libs/api:
      completion_percent: 45
      tasks_total: 60
      tasks_completed: 27
      tasks_blocked: 5

  combined_completion_percent: 69.3
  combined_tasks_total: 140
  combined_tasks_completed: 97
  combined_tasks_blocked: 7

  blockers:
    - submodule_path: libs/api
      blocked_ticket_id: 01TASK_API_AUTH
      blocked_ticket_title: API authentication
      blocked_reason: Waiting for OAuth implementation
      severity: critical
      affects_parent_tickets: [01TASK_MAIN_AUTH]

  requirements_pushed: 3
  requirements_fulfilled: 1
  requirements_pending: 2

  collected_at: '2025-12-19T19:30:00+00:00'
  collection_method: on_demand
```

---

## 6. API Design

### 6.1 ProgressAggregator Class

```python
class ProgressAggregator:
    """Collects and aggregates progress from submodules."""

    def __init__(self, parent_roadmap_path: Path):
        self.parent_path = parent_roadmap_path
        self.discovery = SubmoduleDiscovery(parent_roadmap_path.parent.parent)

    def collect(self) -> AggregatedProgress:
        """Collect progress from all submodules."""
        submodules = self.discovery.get_vibey_submodules()

        progress_map = {}
        blockers = []

        for submod in submodules:
            progress = self._collect_submodule_progress(submod)
            progress_map[submod.submodule_path] = progress

            submod_blockers = self._collect_blockers(submod)
            blockers.extend(submod_blockers)

        return AggregatedProgress(
            submodule_progress=progress_map,
            blockers=sorted(blockers, key=lambda b: b.severity.value),
            # ... compute aggregates
        )

    def _collect_submodule_progress(self, submod: SubmoduleReference) -> SubmoduleProgress:
        """Read progress from a single submodule."""
        submod_path = self.parent_path.parent.parent / submod.submodule_path
        roadmap_path = submod_path / ".vibey" / "roadmap"
        # Read and return progress
        pass
```

### 6.2 CLI Commands

```bash
# Show aggregated submodule progress
vibey submodule status
# Output:
# SUBMODULE STATUS
# ================
# Overall: 69% complete (97/140 tasks)
#
# libs/auth    [████████░░] 80%   40/50 tasks   2 blocked
# libs/ui      [██████████] 100%  30/30 tasks   ✓ complete
# libs/api     [████░░░░░░] 45%   27/60 tasks   5 blocked  ⚠ critical
#
# BLOCKERS (7 total, 1 critical)
# [CRITICAL] libs/api: API authentication waiting for OAuth
#            Affects: 01TASK_MAIN_AUTH

# Show blockers only
vibey submodule blockers

# Show requirement fulfillment
vibey submodule requirements --status pending

# Force refresh
vibey submodule refresh
```

### 6.3 MCP Tools

```python
@mcp_tool
def submodule_status() -> AggregatedProgress:
    """Get aggregated progress from all submodules."""

@mcp_tool
def submodule_blockers(
    severity_filter: Optional[str] = None,
    submodule_filter: Optional[str] = None
) -> List[SubmoduleBlocker]:
    """List blockers from submodules."""

@mcp_tool
def submodule_refresh() -> RefreshResult:
    """Force refresh of submodule progress data."""
```

---

## 7. Configuration

```yaml
# .vibey/config/submodules.yaml
pull_up:
  enabled: true

  # Collection triggers
  triggers:
    on_roadmap_status: true      # Collect when showing roadmap status
    on_git_pull: false           # Collect after git pull
    scheduled_interval_minutes: 0 # 0 = disabled

  # Staleness
  stale_threshold_minutes: 60    # Mark data stale after this

  # Blocker surfacing
  blockers:
    surface_to_parent: true
    minimum_severity: medium     # Only surface medium+ blockers
    notify_on_critical: true     # Alert on critical blockers

  # Progress aggregation
  aggregation:
    weight_by: task_count        # task_count | equal | custom
    include_not_started: false   # Include submodules with 0% progress
```

---

## 8. Triangle Model Integration

### 8.1 Artifact Visibility

When pulling up, parent can see artifacts in submodules:

```
Parent query: "What artifacts were created for requirement REQ-001?"

→ CrossRepoRequirement(REQ-001)
  → target_ticket_id in submodule
    → TicketArtifactAssociation in submodule
      → Artifact details

Result: List of artifacts in submodule associated with derived ticket
```

### 8.2 Commit Visibility

Parent can see commits related to requirements:

```
Parent query: "What commits addressed requirement REQ-001?"

→ CrossRepoRequirement(REQ-001)
  → target_ticket_id in submodule
    → TicketCommitLink in submodule
      → GitCommit details

Result: List of commits in submodule linked to derived ticket
```

---

## Next Steps

1. → Task 5: Design cross-repo dependency tracking
2. → Task 6: Consolidate into design document
