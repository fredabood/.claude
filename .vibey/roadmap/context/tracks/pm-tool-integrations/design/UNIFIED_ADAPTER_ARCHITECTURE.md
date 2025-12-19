# Unified Adapter Architecture Design

**Track:** PM Tool Integrations
**Date:** 2025-12-19
**Version:** 1.0
**Status:** Draft

---

## Executive Summary

This document proposes a unified adapter architecture that:

1. **Makes Vibey just another adapter** - on equal footing with Jira, GitHub, Trello, Asana
2. **Decouples CLI/MCP from Vibey-specific semantics** - they talk to a generic ticket interface
3. **Enables plug-and-play PM tools** - without changing how Vibey works
4. **Moves Vibey-specific logic into VibeyAdapter** - freeing the core to be tool-agnostic

---

## Part 1: Current State Assessment

### 1.1 Existing Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          CLI / MCP Server                                │
│  (Tightly coupled to Vibey models: Track, Sprint, Task)                 │
├─────────────────────────────────────────────────────────────────────────┤
│                     vibey/roadmap/models/                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │   Roadmap   │  │    Track    │  │   Sprint    │  │    Task     │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
│                     (Legacy dataclass models)                           │
├─────────────────────────────────────────────────────────────────────────┤
│                   vibey/roadmap/models/ticket/                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Unified Ticket Architecture                   │   │
│  │  Layer 0: Completable (criteria system)                         │   │
│  │  Layer 1: Ticket (lifecycle semantics)                          │   │
│  │  Layer 2: HierarchicalTicket (parent-child navigation)          │   │
│  │  Layer 3: RoadmapTicket, TrackTicket, SprintTicket, TaskTicket  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────────┤
│                    ModelAdapter (bidirectional conversion)              │
│  Legacy ↔ Unified Ticket (currently internal adapter)                   │
├─────────────────────────────────────────────────────────────────────────┤
│                    Storage: YAML files + SQLite                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Current Pain Points

1. **Tight Coupling**: CLI imports directly from `vibey.roadmap.models`
   - 30+ files with direct model imports
   - Cannot swap underlying PM tool without rewriting CLI

2. **Vibey-Specific Semantics Everywhere**:
   - `Track`, `Sprint`, `Task` are Vibey concepts
   - Jira uses: Project, Sprint, Issue
   - GitHub uses: Repository, Milestone, Issue
   - Trello uses: Board, List, Card

3. **Duplicate Abstraction Layers**:
   - Legacy dataclass models (`roadmap.py`, `track.py`, `sprint.py`, `task.py`)
   - Unified Ticket models (`RoadmapTicket`, `TrackTicket`, `SprintTicket`, `TaskTicket`)
   - ModelAdapter converts between them

4. **No Unified Interface for CLI/MCP**:
   - No `TicketService` or `ProjectService` abstraction
   - Direct storage access mixed with business logic

---

## Part 2: Proposed Architecture

### 2.1 Target Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          CLI / MCP Server                                │
│              (Talks to TicketService - tool-agnostic)                   │
├─────────────────────────────────────────────────────────────────────────┤
│                         TicketService                                    │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Generic operations: list_projects, get_task, update_status    │    │
│  │  Delegates to active adapter                                    │    │
│  └────────────────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────────────────┤
│                      TicketAdapter (ABC)                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Abstract interface for all PM tool adapters                    │   │
│  │  - get_projects() → List[Project]                               │   │
│  │  - get_sprints(project_id) → List[Sprint]                       │   │
│  │  - get_tasks(sprint_id) → List[Task]                            │   │
│  │  - update_task_status(task_id, status) → Task                   │   │
│  │  - sync(direction) → SyncResult                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
├────────────┬────────────┬────────────┬────────────┬────────────────────┤
│ VibeyAdapter│ JiraAdapter│GitHubAdapter│TrelloAdapter│  AsanaAdapter    │
│ (YAML+SQLite)│(REST API)  │(GraphQL)   │(REST API)  │ (REST API)       │
├────────────┴────────────┴────────────┴────────────┴────────────────────┤
│                    Unified Ticket Architecture                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Layer 0: Completable (criteria system)                         │   │
│  │  Layer 1: Ticket (lifecycle, status, timestamps)                │   │
│  │  Layer 2: HierarchicalTicket (parent-child, navigation)         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│  (Generic ticket models - no Vibey-specific semantics)                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Key Design Decisions

#### Decision 1: Vibey Becomes an Adapter

**Current**: Vibey models are the core, everything else adapts to them.
**Proposed**: Generic tickets are the core, Vibey is one adapter among many.

```python
# Current (wrong direction)
class JiraAdapter:
    def import_issue(self, jira_issue) -> Task:  # Returns Vibey Task
        pass

# Proposed (correct direction)
class VibeyAdapter(TicketAdapter):
    def get_task(self, task_id) -> Ticket:  # Returns generic Ticket
        pass

class JiraAdapter(TicketAdapter):
    def get_task(self, task_id) -> Ticket:  # Returns generic Ticket
        pass
```

#### Decision 2: Generic Ticket Hierarchy

Replace Vibey-specific hierarchy names with generic equivalents:

| Vibey Term | Generic Term | Jira Equivalent | GitHub Equivalent | Trello Equivalent |
|------------|--------------|-----------------|-------------------|-------------------|
| Roadmap | Project | Project | Repository | Board |
| Track | Workstream | Epic/Component | Milestone | List |
| Sprint | Iteration | Sprint | - | - |
| Task | WorkItem | Issue | Issue | Card |

#### Decision 3: Semantic Layer Stays in Adapters

The "semantic layer" (how each tool interprets work items) stays in adapters:

```python
class VibeyAdapter(TicketAdapter):
    """
    Vibey semantics:
    - Track = theme/workstream that groups related work
    - Sprint = time-boxed iteration
    - Task = atomic unit of work
    """

    def map_to_generic(self, vibey_task: VibeyTask) -> Ticket:
        return Ticket(
            id=vibey_task.id,
            name=vibey_task.title,
            hierarchy_type=HierarchyType.WORK_ITEM,
            # ... generic fields
        )

class JiraAdapter(TicketAdapter):
    """
    Jira semantics:
    - Epic = large body of work (→ Workstream)
    - Sprint = scrum iteration (→ Iteration)
    - Issue = work item (→ WorkItem)
    """

    def map_to_generic(self, jira_issue: JiraIssue) -> Ticket:
        return Ticket(
            id=jira_issue.key,
            name=jira_issue.summary,
            hierarchy_type=self._map_issue_type(jira_issue.issuetype),
            # ... generic fields
        )
```

---

## Part 3: Core Abstractions

### 3.1 Generic Ticket Model (Lower Level)

```python
# vibey/core/ticket.py (new location - not under roadmap/)

from enum import Enum
from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field


class HierarchyType(str, Enum):
    """Generic hierarchy levels."""
    PROJECT = "project"      # Top-level container (Roadmap, Jira Project, Board)
    WORKSTREAM = "workstream"  # Grouping (Track, Epic, List)
    ITERATION = "iteration"   # Time-boxed (Sprint)
    WORK_ITEM = "work_item"   # Atomic work (Task, Issue, Card)


class TicketStatus(str, Enum):
    """Universal status values."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Ticket(BaseModel):
    """
    Generic ticket - the universal work item abstraction.

    All PM tools map their entities to this model.
    CLI/MCP work exclusively with this model.
    """
    # Identity
    id: str
    external_id: Optional[str] = None  # Original ID in source system
    source_adapter: str  # "vibey", "jira", "github", etc.

    # Classification
    hierarchy_type: HierarchyType
    item_type: Optional[str] = None  # Adapter-specific subtype

    # Content
    name: str
    description: Optional[str] = None

    # Hierarchy
    parent_id: Optional[str] = None
    children_ids: List[str] = Field(default_factory=list)

    # Status
    status: TicketStatus = TicketStatus.NOT_STARTED
    blocked: bool = False
    blocked_reason: Optional[str] = None

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Assignment
    assignee: Optional[str] = None
    labels: List[str] = Field(default_factory=list)
    priority: Optional[str] = None

    # Progress (for containers)
    children_total: int = 0
    children_completed: int = 0
    completion_percent: float = 0.0

    # Criteria (from Unified Ticket Architecture)
    criteria: List[Any] = Field(default_factory=list)  # Criterion objects

    # Adapter-specific metadata
    metadata: dict = Field(default_factory=dict)
```

### 3.2 TicketAdapter Base Class

```python
# vibey/adapters/pm/base.py

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from enum import Enum

from vibey.core.ticket import Ticket, HierarchyType, TicketStatus


class SyncDirection(str, Enum):
    IMPORT = "import"   # External → Vibey
    EXPORT = "export"   # Vibey → External
    BIDIRECTIONAL = "bidirectional"


class SyncResult(BaseModel):
    """Result of a sync operation."""
    success: bool
    direction: SyncDirection
    items_imported: int = 0
    items_exported: int = 0
    items_updated: int = 0
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class TicketAdapter(ABC):
    """
    Abstract base class for all PM tool adapters.

    Each adapter translates between their tool's data model
    and the generic Ticket model.
    """

    # =========================================================================
    # IDENTITY
    # =========================================================================

    @property
    @abstractmethod
    def adapter_name(self) -> str:
        """Unique adapter identifier (e.g., 'vibey', 'jira', 'github')."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name (e.g., 'Vibey Roadmap', 'Jira')."""
        pass

    # =========================================================================
    # CAPABILITIES
    # =========================================================================

    @property
    def supported_hierarchy_types(self) -> List[HierarchyType]:
        """Which hierarchy types this adapter supports."""
        return list(HierarchyType)

    @property
    def supports_sprints(self) -> bool:
        """Whether adapter supports sprint/iteration concept."""
        return True

    @property
    def supports_bidirectional_sync(self) -> bool:
        """Whether adapter supports two-way sync."""
        return False

    @property
    def supports_webhooks(self) -> bool:
        """Whether adapter supports real-time webhooks."""
        return False

    # =========================================================================
    # READ OPERATIONS (Generic Interface)
    # =========================================================================

    @abstractmethod
    def list_projects(self) -> List[Ticket]:
        """List all top-level projects/roadmaps."""
        pass

    @abstractmethod
    def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Get a single ticket by ID."""
        pass

    @abstractmethod
    def list_children(self, parent_id: str) -> List[Ticket]:
        """List direct children of a ticket."""
        pass

    @abstractmethod
    def search_tickets(
        self,
        query: Optional[str] = None,
        hierarchy_type: Optional[HierarchyType] = None,
        status: Optional[TicketStatus] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
    ) -> List[Ticket]:
        """Search tickets with filters."""
        pass

    # =========================================================================
    # WRITE OPERATIONS (Generic Interface)
    # =========================================================================

    @abstractmethod
    def create_ticket(self, ticket: Ticket) -> Ticket:
        """Create a new ticket."""
        pass

    @abstractmethod
    def update_ticket(self, ticket: Ticket) -> Ticket:
        """Update an existing ticket."""
        pass

    @abstractmethod
    def update_status(self, ticket_id: str, status: TicketStatus) -> Ticket:
        """Update ticket status (common operation)."""
        pass

    @abstractmethod
    def delete_ticket(self, ticket_id: str) -> bool:
        """Delete a ticket."""
        pass

    # =========================================================================
    # SYNC OPERATIONS
    # =========================================================================

    def sync(self, direction: SyncDirection = SyncDirection.IMPORT) -> SyncResult:
        """
        Synchronize with external system.

        Override in adapters that support sync.
        """
        raise NotImplementedError(f"{self.adapter_name} does not support sync")

    def detect_conflicts(self) -> List[Dict[str, Any]]:
        """
        Detect conflicts between local and remote state.

        Override in adapters that support bidirectional sync.
        """
        return []

    # =========================================================================
    # MAPPING (Adapter-Specific)
    # =========================================================================

    @abstractmethod
    def map_to_generic(self, native_item: Any) -> Ticket:
        """Convert adapter's native model to generic Ticket."""
        pass

    @abstractmethod
    def map_from_generic(self, ticket: Ticket) -> Any:
        """Convert generic Ticket to adapter's native model."""
        pass
```

### 3.3 TicketService (CLI/MCP Interface)

```python
# vibey/services/ticket_service.py

from typing import List, Optional
from vibey.core.ticket import Ticket, HierarchyType, TicketStatus
from vibey.adapters.pm.base import TicketAdapter, SyncDirection, SyncResult
from vibey.adapters.pm.registry import PMAdapterRegistry


class TicketService:
    """
    Service layer for ticket operations.

    CLI and MCP server use this - they never touch adapters directly.
    This enables swapping PM tools without changing CLI/MCP code.
    """

    def __init__(self, adapter: Optional[TicketAdapter] = None):
        """
        Initialize with optional adapter.

        If no adapter provided, uses default from registry.
        """
        self._adapter = adapter or PMAdapterRegistry.get_default()

    @property
    def adapter_name(self) -> str:
        return self._adapter.adapter_name

    def set_adapter(self, adapter: TicketAdapter) -> None:
        """Switch to a different adapter."""
        self._adapter = adapter

    # =========================================================================
    # READ OPERATIONS
    # =========================================================================

    def list_projects(self) -> List[Ticket]:
        return self._adapter.list_projects()

    def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        return self._adapter.get_ticket(ticket_id)

    def list_children(self, parent_id: str) -> List[Ticket]:
        return self._adapter.list_children(parent_id)

    def get_workstreams(self, project_id: str) -> List[Ticket]:
        """Get tracks/epics for a project."""
        children = self._adapter.list_children(project_id)
        return [c for c in children if c.hierarchy_type == HierarchyType.WORKSTREAM]

    def get_iterations(self, workstream_id: str) -> List[Ticket]:
        """Get sprints/iterations for a workstream."""
        children = self._adapter.list_children(workstream_id)
        return [c for c in children if c.hierarchy_type == HierarchyType.ITERATION]

    def get_work_items(self, parent_id: str) -> List[Ticket]:
        """Get tasks/issues for an iteration or workstream."""
        children = self._adapter.list_children(parent_id)
        return [c for c in children if c.hierarchy_type == HierarchyType.WORK_ITEM]

    def search(self, **kwargs) -> List[Ticket]:
        return self._adapter.search_tickets(**kwargs)

    # =========================================================================
    # WRITE OPERATIONS
    # =========================================================================

    def create(self, ticket: Ticket) -> Ticket:
        return self._adapter.create_ticket(ticket)

    def update(self, ticket: Ticket) -> Ticket:
        return self._adapter.update_ticket(ticket)

    def start(self, ticket_id: str) -> Ticket:
        """Start working on a ticket."""
        return self._adapter.update_status(ticket_id, TicketStatus.IN_PROGRESS)

    def complete(self, ticket_id: str) -> Ticket:
        """Mark a ticket as complete."""
        return self._adapter.update_status(ticket_id, TicketStatus.COMPLETED)

    def block(self, ticket_id: str, reason: str) -> Ticket:
        """Mark a ticket as blocked."""
        ticket = self._adapter.get_ticket(ticket_id)
        if ticket:
            ticket.blocked = True
            ticket.blocked_reason = reason
            return self._adapter.update_ticket(ticket)
        raise ValueError(f"Ticket not found: {ticket_id}")

    def delete(self, ticket_id: str) -> bool:
        return self._adapter.delete_ticket(ticket_id)

    # =========================================================================
    # SYNC OPERATIONS
    # =========================================================================

    def sync(self, direction: SyncDirection = SyncDirection.IMPORT) -> SyncResult:
        return self._adapter.sync(direction)

    def detect_conflicts(self) -> List[dict]:
        return self._adapter.detect_conflicts()
```

---

## Part 4: VibeyAdapter Implementation

### 4.1 VibeyAdapter Class

```python
# vibey/adapters/pm/vibey/adapter.py

from pathlib import Path
from typing import List, Optional, Any
from datetime import datetime, timezone

from vibey.core.ticket import Ticket, HierarchyType, TicketStatus
from vibey.adapters.pm.base import TicketAdapter, SyncDirection, SyncResult
from vibey.roadmap.serialization.yaml_loader import load_roadmap_from_yaml
from vibey.roadmap.serialization.yaml_dumper import dump_roadmap_to_yaml


class VibeyAdapter(TicketAdapter):
    """
    Adapter for Vibey's native YAML + SQLite roadmap system.

    Maps Vibey hierarchy to generic tickets:
    - Roadmap → Project
    - Track → Workstream
    - Sprint → Iteration
    - Task → WorkItem
    """

    def __init__(self, vibey_dir: Optional[Path] = None):
        self._vibey_dir = vibey_dir or Path.cwd() / ".vibey"
        self._roadmap_dir = self._vibey_dir / "roadmap"

    # =========================================================================
    # IDENTITY
    # =========================================================================

    @property
    def adapter_name(self) -> str:
        return "vibey"

    @property
    def display_name(self) -> str:
        return "Vibey Roadmap"

    # =========================================================================
    # CAPABILITIES
    # =========================================================================

    @property
    def supports_sprints(self) -> bool:
        return True

    @property
    def supports_bidirectional_sync(self) -> bool:
        return True  # Can sync with other adapters

    # =========================================================================
    # MAPPING: Vibey → Generic
    # =========================================================================

    def map_to_generic(self, native_item: Any) -> Ticket:
        """Convert Vibey model to generic Ticket."""
        from vibey.roadmap.models import Roadmap, Track, Sprint, Task

        if isinstance(native_item, Roadmap):
            return self._roadmap_to_ticket(native_item)
        elif isinstance(native_item, Track):
            return self._track_to_ticket(native_item)
        elif isinstance(native_item, Sprint):
            return self._sprint_to_ticket(native_item)
        elif isinstance(native_item, Task):
            return self._task_to_ticket(native_item)
        else:
            raise TypeError(f"Unknown Vibey type: {type(native_item)}")

    def _roadmap_to_ticket(self, roadmap) -> Ticket:
        return Ticket(
            id=roadmap.id,
            external_id=roadmap.id,
            source_adapter="vibey",
            hierarchy_type=HierarchyType.PROJECT,
            item_type="roadmap",
            name=roadmap.name,
            description=getattr(roadmap, 'description', ''),
            status=self._map_status(roadmap.status),
            created_at=getattr(roadmap, 'created', datetime.now(timezone.utc)),
            children_total=getattr(roadmap, 'tracks_total', 0),
            children_completed=getattr(roadmap, 'tracks_completed', 0),
            metadata={"version": getattr(roadmap, 'version', '0.0.0')},
        )

    def _track_to_ticket(self, track) -> Ticket:
        return Ticket(
            id=track.id,
            external_id=track.id,
            source_adapter="vibey",
            hierarchy_type=HierarchyType.WORKSTREAM,
            item_type="track",
            name=track.name,
            description=getattr(track, 'description', ''),
            parent_id=getattr(track, 'roadmap_id', None),
            status=self._map_status(track.status),
            priority=getattr(track, 'priority', 'medium'),
            created_at=getattr(track, 'created', datetime.now(timezone.utc)),
            children_total=getattr(track, 'sprints_total', 0),
            children_completed=getattr(track, 'sprints_completed', 0),
        )

    def _sprint_to_ticket(self, sprint) -> Ticket:
        return Ticket(
            id=sprint.id,
            external_id=sprint.id,
            source_adapter="vibey",
            hierarchy_type=HierarchyType.ITERATION,
            item_type="sprint",
            name=sprint.name,
            description=getattr(sprint, 'description', ''),
            parent_id=getattr(sprint, 'track_id', None),
            status=self._map_status(sprint.status),
            blocked=getattr(sprint, 'blocked', False),
            blocked_reason=getattr(sprint, 'blocked_reason', None),
            created_at=getattr(sprint, 'created', datetime.now(timezone.utc)),
            started_at=getattr(sprint, 'started', None),
            completed_at=getattr(sprint, 'completed', None),
            children_total=getattr(sprint, 'tasks_total', 0),
            children_completed=getattr(sprint, 'tasks_completed', 0),
        )

    def _task_to_ticket(self, task) -> Ticket:
        return Ticket(
            id=task.id,
            external_id=task.id,
            source_adapter="vibey",
            hierarchy_type=HierarchyType.WORK_ITEM,
            item_type=getattr(task, 'task_type', 'development'),
            name=getattr(task, 'title', task.id),
            description=getattr(task, 'description', ''),
            parent_id=getattr(task, 'sprint_id', None),
            status=self._map_status(task.status),
            blocked=getattr(task, 'blocked', False),
            priority=getattr(task, 'priority', 'medium'),
            assignee=getattr(task, 'assigned_agent', None),
            created_at=getattr(task, 'created', datetime.now(timezone.utc)),
            started_at=getattr(task, 'started', None),
            completed_at=getattr(task, 'completed', None),
            metadata={
                "complexity": getattr(task, 'complexity', 'medium'),
                "estimated_tokens": getattr(task, 'estimated_tokens', 0),
            },
        )

    def _map_status(self, status) -> TicketStatus:
        """Map Vibey status to generic TicketStatus."""
        status_str = status.value if hasattr(status, 'value') else str(status)
        mapping = {
            "not_started": TicketStatus.NOT_STARTED,
            "in_progress": TicketStatus.IN_PROGRESS,
            "paused": TicketStatus.BLOCKED,
            "completed": TicketStatus.COMPLETED,
            "production_ready": TicketStatus.COMPLETED,
            "deployed": TicketStatus.COMPLETED,
            "wont_do": TicketStatus.CANCELLED,
            "superseded": TicketStatus.CANCELLED,
        }
        return mapping.get(status_str.lower(), TicketStatus.NOT_STARTED)

    # ... (read/write operations using existing YAML loader/dumper)
```

---

## Part 5: Migration Path

### 5.1 Phase 1: Create Core Abstractions

1. Create `vibey/core/ticket.py` with generic Ticket model
2. Create `vibey/adapters/pm/base.py` with TicketAdapter ABC
3. Create `vibey/adapters/pm/registry.py` with PMAdapterRegistry
4. Create `vibey/services/ticket_service.py` with TicketService

### 5.2 Phase 2: Implement VibeyAdapter

1. Create `vibey/adapters/pm/vibey/adapter.py`
2. Move mapping logic from `ModelAdapter` to `VibeyAdapter`
3. Implement all TicketAdapter interface methods
4. Keep existing YAML/SQLite storage unchanged

### 5.3 Phase 3: Refactor CLI to Use TicketService

1. Create CLI wrapper that uses TicketService
2. Replace direct model imports with service calls
3. Keep backward compatibility via adapter

### 5.4 Phase 4: Implement External Adapters

1. JiraAdapter (Sprint 2)
2. GitHubAdapter (Sprint 3)
3. TrelloAdapter (Sprint 4)
4. AsanaAdapter (Sprint 5)

---

## Part 6: Proposed Track Restructure

### New Sprint Structure

| Sprint | Name | Tasks | Focus |
|--------|------|-------|-------|
| **0** | Architecture Design | 4 | This design document, ADRs |
| **1** | Core Abstractions | 6 | Generic Ticket, TicketAdapter, TicketService |
| **2** | VibeyAdapter | 5 | Extract Vibey semantics into adapter |
| **3** | CLI Refactor | 5 | Update CLI to use TicketService |
| **4** | JiraAdapter | 6 | Jira OAuth, REST client, mapping |
| **5** | Jira Sync | 5 | Bidirectional sync, webhooks |
| **6** | GitHubAdapter | 5 | GitHub Issues/Projects integration |
| **7** | TrelloAdapter | 4 | Trello boards/lists/cards |
| **8** | AsanaAdapter | 4 | Asana projects/tasks |
| **9** | ConfluenceAdapter | 4 | Documentation sync |
| **10** | Integration & Polish | 4 | Cross-adapter features, CLI polish |

---

## Part 7: Benefits

### For Users
- Use Vibey with existing PM tools (Jira, GitHub, Trello, Asana)
- Migrate between tools without losing history
- Unified CLI regardless of backing tool

### For Development
- Clean separation of concerns
- Easy to add new PM tools
- Test adapters in isolation
- Vibey-specific logic contained in one place

### For Architecture
- Generic ticket abstraction as stable foundation
- Adapters can evolve independently
- CLI/MCP decoupled from storage implementation

---

## Appendix A: Field Mapping Reference

| Generic Field | Vibey | Jira | GitHub | Trello | Asana |
|---------------|-------|------|--------|--------|-------|
| id | id (ULID) | key | number | id | gid |
| name | title/name | summary | title | name | name |
| description | description | description | body | desc | notes |
| status | status | status.name | state | idList→ | completed |
| parent_id | sprint_id/track_id | parent.key | milestone.id | idList | parent.gid |
| assignee | assigned_agent | assignee.displayName | assignees[0] | idMembers[0] | assignee.gid |
| priority | priority | priority.name | labels→ | - | - |
| labels | - | labels[].name | labels[].name | idLabels | tags[].name |

---

## Appendix B: Related Documents

- [ADR-0001: ULID Identifiers](docs/architecture/adr/0001-ulid-identifiers.md)
- [ADR-0002: Flat Directory Structure](docs/architecture/adr/0002-flat-directory-structure.md)
- [Unified Ticket Architecture](sqlite-backend-6/context/architecture/02-CLASS-MODEL.md)
- [ModelAdapter Implementation](vibey/roadmap/models/ticket/adapters.py)
