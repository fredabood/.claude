# Git Submodule Integration - Comprehensive Design Document

**Task:** 01KCMP3EX1K7BVMF69WH8DC2DF
**Date:** 2025-12-19
**Version:** 1.0
**Status:** Complete

---

## Executive Summary

This document provides the complete design for Git Submodule Integration in Vibey, enabling roadmap management across parent projects and their submodules. The design extends the Unified Ticket Architecture's Triangle Model to support cross-repository relationships.

### Key Capabilities

1. **Detection & Discovery** - Automatically find submodules with Vibey roadmaps
2. **Push-Down** - Parent pushes requirements to submodule roadmaps
3. **Pull-Up** - Parent aggregates progress from submodule roadmaps
4. **Cross-Repo Dependencies** - Track dependencies between tickets in different repos

### Design Principles

- **Extend, don't duplicate** - Build on existing Triangle Model entities
- **Explicit ownership** - Clear who owns what (parent vs submodule)
- **Configurable coupling** - Support tight, loose, and manual sync modes
- **Git-native** - Leverage `.gitmodules` for discovery

---

## Part 1: Architecture Overview

### 1.1 Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PARENT REPOSITORY                                     │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                     Unified Ticket Architecture                       │   │
│  │  ┌─────────┐     ┌─────────────────┐     ┌─────────────────────┐    │   │
│  │  │ Ticket  │────▶│ TicketCommitLink │◀───│ TicketArtifactAssoc │    │   │
│  │  └─────────┘     └─────────────────┘     └─────────────────────┘    │   │
│  │       │                   │                        │                 │   │
│  │       │                   ▼                        ▼                 │   │
│  │       │          ┌─────────────┐          ┌─────────────┐           │   │
│  │       │          │  GitCommit  │─────────▶│  Artifact   │           │   │
│  │       │          └─────────────┘          └─────────────┘           │   │
│  └───────┼──────────────────────────────────────────────────────────────┘   │
│          │                                                                   │
│          │ NEW: Cross-Repo Extensions                                        │
│          ▼                                                                   │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ ┌─────────────────┐  ┌────────────────────┐  ┌────────────────────┐ │   │
│  │ │SubmoduleReference│  │CrossRepoRequirement│  │CrossRepoDependency │ │   │
│  │ └────────┬────────┘  └─────────┬──────────┘  └─────────┬──────────┘ │   │
│  └──────────┼───────────────────────────────────────────────────────────┘   │
│             │                     │                       │                  │
└─────────────┼─────────────────────┼───────────────────────┼──────────────────┘
              │                     │                       │
              ▼                     ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SUBMODULE REPOSITORY                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                     Unified Ticket Architecture                       │   │
│  │  (Same structure - Ticket, GitCommit, Artifact, relationships)       │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 New Entities Summary

| Entity | Purpose | Location |
|--------|---------|----------|
| `SubmoduleReference` | Links parent to submodule roadmap | `vibey/roadmap/models/submodule.py` |
| `CrossRepoRequirement` | Push-down requirements | `vibey/roadmap/models/cross_repo.py` |
| `CrossRepoDependency` | Cross-repo task dependencies | `vibey/roadmap/models/cross_repo.py` |
| `AggregatedProgress` | Pull-up progress summary | `vibey/roadmap/models/submodule.py` |
| `SubmoduleBlocker` | Blockers from submodules | `vibey/roadmap/models/submodule.py` |

---

## Part 2: Implementation Specifications

### 2.1 Directory Structure

```
vibey/
├── roadmap/
│   └── models/
│       ├── submodule.py          # NEW: SubmoduleReference, AggregatedProgress
│       └── cross_repo.py         # NEW: CrossRepoRequirement, CrossRepoDependency
├── operations/
│   └── submodule/                # NEW: All submodule operations
│       ├── __init__.py
│       ├── discovery.py          # SubmoduleDiscovery class
│       ├── push.py               # RequirementPusher class
│       ├── pull.py               # ProgressAggregator class
│       └── deps.py               # CrossRepoDependencyResolver class
├── cli/
│   └── submodule.py              # NEW: CLI commands
└── mcp/
    └── tools/
        └── submodule.py          # NEW: MCP tools

.vibey/roadmap/
├── submodules/                   # NEW: Submodule registry
│   ├── .registry.yaml
│   └── {submodule-name}.yaml
├── cross_repo_requirements/      # NEW: Push-down requirements
│   └── {requirement-id}.yaml
├── cross_repo_deps/              # NEW: Cross-repo dependencies
│   ├── outgoing/
│   └── incoming/
└── submodule_progress/           # NEW: Pull-up data
    ├── .aggregated.yaml
    └── {submodule-name}.yaml
```

### 2.2 SQLite Schema Extensions

```sql
-- Add to vibey/roadmap/serialization/sql_schema.py

-- Submodule references (detection/discovery)
CREATE TABLE IF NOT EXISTS submodule_references (
    id TEXT PRIMARY KEY,
    parent_roadmap_id TEXT NOT NULL,
    submodule_path TEXT NOT NULL,
    submodule_url TEXT,
    submodule_commit TEXT,
    submodule_roadmap_id TEXT,
    detected_at TEXT NOT NULL,
    detection_source TEXT NOT NULL,
    has_vibey_roadmap INTEGER NOT NULL DEFAULT 0,
    last_synced_at TEXT,
    sync_status TEXT NOT NULL DEFAULT 'never_synced',
    UNIQUE(parent_roadmap_id, submodule_path)
);

-- Cross-repo requirements (push-down)
CREATE TABLE IF NOT EXISTS cross_repo_requirements (
    id TEXT PRIMARY KEY,
    source_roadmap_id TEXT NOT NULL,
    source_ticket_id TEXT NOT NULL,
    target_roadmap_id TEXT,
    target_ticket_id TEXT,
    target_submodule_path TEXT NOT NULL,
    requirement_type TEXT NOT NULL,
    requirement_spec_json TEXT NOT NULL,
    ownership_model TEXT NOT NULL,
    push_mode TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    pushed_at TEXT,
    acknowledged_at TEXT,
    fulfilled_at TEXT
);

-- Cross-repo dependencies
CREATE TABLE IF NOT EXISTS cross_repo_dependencies (
    id TEXT PRIMARY KEY,
    dependent_roadmap_id TEXT NOT NULL,
    dependent_ticket_id TEXT NOT NULL,
    dependent_repo_path TEXT NOT NULL,
    dependency_roadmap_id TEXT NOT NULL,
    dependency_ticket_id TEXT NOT NULL,
    dependency_repo_path TEXT NOT NULL,
    dependency_type TEXT NOT NULL,
    blocking INTEGER NOT NULL DEFAULT 1,
    soft_dependency INTEGER NOT NULL DEFAULT 0,
    resolution_criteria_json TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    resolved_at TEXT,
    created_by TEXT,
    reason TEXT,
    UNIQUE(dependent_ticket_id, dependency_ticket_id, dependency_repo_path)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_submod_refs_parent ON submodule_references(parent_roadmap_id);
CREATE INDEX IF NOT EXISTS idx_cross_req_source ON cross_repo_requirements(source_ticket_id);
CREATE INDEX IF NOT EXISTS idx_cross_req_target ON cross_repo_requirements(target_submodule_path);
CREATE INDEX IF NOT EXISTS idx_cross_deps_dependent ON cross_repo_dependencies(dependent_ticket_id);
CREATE INDEX IF NOT EXISTS idx_cross_deps_dependency ON cross_repo_dependencies(dependency_ticket_id);
```

---

## Part 3: Model Implementations

### 3.1 submodule.py

```python
# vibey/roadmap/models/submodule.py
"""Models for git submodule integration."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class DetectionSource(str, Enum):
    GITMODULES = "gitmodules"
    GIT_COMMAND = "git_command"
    DIRECTORY_SCAN = "directory_scan"
    MANUAL = "manual"


class SyncStatus(str, Enum):
    SYNCED = "synced"
    STALE = "stale"
    NEVER_SYNCED = "never_synced"
    ERROR = "error"


class SubmoduleReference(BaseModel):
    """Links parent roadmap to submodule roadmap."""
    id: str
    parent_roadmap_id: str
    submodule_path: str
    submodule_url: Optional[str] = None
    submodule_commit: Optional[str] = None
    submodule_roadmap_id: Optional[str] = None

    detected_at: datetime
    detection_source: DetectionSource
    has_vibey_roadmap: bool = False

    last_synced_at: Optional[datetime] = None
    sync_status: SyncStatus = SyncStatus.NEVER_SYNCED

    class Config:
        use_enum_values = True


class SubmoduleProgress(BaseModel):
    """Progress summary from a single submodule."""
    submodule_path: str
    roadmap_id: str

    tracks_total: int = 0
    tracks_completed: int = 0
    tracks_in_progress: int = 0

    sprints_total: int = 0
    sprints_completed: int = 0

    tasks_total: int = 0
    tasks_completed: int = 0
    tasks_in_progress: int = 0
    tasks_blocked: int = 0

    completion_percent: float = 0.0

    last_activity_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    collected_at: datetime = Field(default_factory=datetime.utcnow)


class BlockerSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SubmoduleBlocker(BaseModel):
    """A blocker in a submodule that may affect parent."""
    submodule_path: str
    roadmap_id: str

    blocked_ticket_id: str
    blocked_ticket_title: str
    blocked_ticket_type: str

    blocked_reason: str
    blocked_by: List[str] = Field(default_factory=list)

    affects_parent_tickets: List[str] = Field(default_factory=list)

    severity: BlockerSeverity
    since: datetime


class CollectionMethod(str, Enum):
    POLLING = "polling"
    ON_DEMAND = "on_demand"
    WEBHOOK = "webhook"
    GIT_HOOK = "git_hook"


class AggregatedProgress(BaseModel):
    """Rolled-up progress from all submodules."""
    id: str
    parent_roadmap_id: str

    submodule_progress: Dict[str, SubmoduleProgress] = Field(default_factory=dict)

    total_submodules: int = 0
    submodules_with_roadmaps: int = 0

    combined_completion_percent: float = 0.0
    combined_tasks_total: int = 0
    combined_tasks_completed: int = 0
    combined_tasks_blocked: int = 0

    blockers: List[SubmoduleBlocker] = Field(default_factory=list)
    critical_blocker_count: int = 0

    requirements_pushed: int = 0
    requirements_fulfilled: int = 0
    requirements_pending: int = 0

    collected_at: datetime = Field(default_factory=datetime.utcnow)
    collection_method: CollectionMethod = CollectionMethod.ON_DEMAND
    stale_threshold_minutes: int = 60
```

### 3.2 cross_repo.py

```python
# vibey/roadmap/models/cross_repo.py
"""Models for cross-repo relationships."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# === Push-Down Models ===

class RequirementType(str, Enum):
    FEATURE = "feature"
    BUGFIX = "bugfix"
    UPGRADE = "upgrade"
    COMPLIANCE = "compliance"
    INTERFACE = "interface"


class OwnershipModel(str, Enum):
    PARENT_OWNED = "parent_owned"
    SUBMODULE_OWNED = "submodule_owned"
    SHARED = "shared"


class PushMode(str, Enum):
    AUTOMATIC = "automatic"
    NOTIFICATION = "notification"
    MANUAL = "manual"


class RequirementStatus(str, Enum):
    DRAFT = "draft"
    PUSHED = "pushed"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    FULFILLED = "fulfilled"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ArtifactRequirement(BaseModel):
    """Specifies an artifact that must be created/modified."""
    artifact_type: str
    path_pattern: Optional[str] = None
    description: str


class InterfaceContract(BaseModel):
    """Specifies an interface/API that must be implemented."""
    interface_type: str
    signature: str
    description: str


class RequirementSpec(BaseModel):
    """Specification of what the requirement entails."""
    title: str
    description: str
    required_artifacts: List[ArtifactRequirement] = Field(default_factory=list)
    interface_contracts: List[InterfaceContract] = Field(default_factory=list)
    suggested_priority: Optional[str] = None
    suggested_deadline: Optional[datetime] = None
    parent_context: str = ""
    related_parent_tickets: List[str] = Field(default_factory=list)


class CrossRepoRequirement(BaseModel):
    """Links a parent ticket to a derived submodule ticket."""
    id: str

    source_roadmap_id: str
    source_ticket_id: str

    target_roadmap_id: Optional[str] = None
    target_ticket_id: Optional[str] = None
    target_submodule_path: str

    requirement_type: RequirementType
    requirement_spec: RequirementSpec
    acceptance_criteria: List[str] = Field(default_factory=list)

    ownership_model: OwnershipModel
    push_mode: PushMode

    created_at: datetime
    pushed_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    fulfilled_at: Optional[datetime] = None

    status: RequirementStatus = RequirementStatus.DRAFT

    class Config:
        use_enum_values = True


# === Cross-Repo Dependencies ===

class DependencyType(str, Enum):
    COMPLETION = "completion"
    ARTIFACT = "artifact"
    INTERFACE = "interface"
    MILESTONE = "milestone"
    APPROVAL = "approval"


class DependencyStatus(str, Enum):
    ACTIVE = "active"
    SATISFIED = "satisfied"
    CANCELLED = "cancelled"
    FAILED = "failed"


class ResolutionCriteria(BaseModel):
    """What needs to happen for dependency to be satisfied."""
    criteria_type: str  # "ticket_complete" | "artifact_exists" | "custom"
    required_status: Optional[str] = "completed"
    artifact_patterns: List[str] = Field(default_factory=list)
    custom_criterion_id: Optional[str] = None


class CrossRepoDependency(BaseModel):
    """Represents a dependency between tickets in different repos."""
    id: str

    dependent_roadmap_id: str
    dependent_ticket_id: str
    dependent_repo_path: str

    dependency_roadmap_id: str
    dependency_ticket_id: str
    dependency_repo_path: str

    dependency_type: DependencyType
    blocking: bool = True
    soft_dependency: bool = False

    resolution_criteria: Optional[ResolutionCriteria] = None

    status: DependencyStatus = DependencyStatus.ACTIVE
    created_at: datetime
    resolved_at: Optional[datetime] = None

    created_by: Optional[str] = None
    reason: Optional[str] = None

    @property
    def reference(self) -> str:
        """Get dependency reference string."""
        return f"{self.dependency_ticket_id}@{self.dependency_repo_path}"

    class Config:
        use_enum_values = True
```

---

## Part 4: Operations Implementations

### 4.1 discovery.py

```python
# vibey/operations/submodule/discovery.py
"""Submodule discovery operations."""

import configparser
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from ulid import ULID

from vibey.roadmap.models.submodule import (
    SubmoduleReference,
    DetectionSource,
    SyncStatus,
)


class SubmoduleEntry:
    """Raw submodule entry from .gitmodules."""
    def __init__(self, name: str, path: str, url: str):
        self.name = name
        self.path = path
        self.url = url
        self.commit: Optional[str] = None
        self.status: Optional[str] = None


class SubmoduleDiscovery:
    """Discovers and tracks git submodules with Vibey roadmaps."""

    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root)
        self.registry: dict[str, SubmoduleReference] = {}

    def discover(self) -> List[SubmoduleReference]:
        """Run full discovery process."""
        # Step 1: Parse .gitmodules
        entries = self._parse_gitmodules()

        # Step 2: Validate with git submodule status
        entries = self._validate_with_git(entries)

        # Step 3: Check for Vibey roadmaps and build references
        references = []
        for entry in entries:
            ref = self._create_reference(entry)
            ref.has_vibey_roadmap = self._has_vibey_roadmap(entry.path)
            if ref.has_vibey_roadmap:
                ref.submodule_roadmap_id = self._read_roadmap_id(entry.path)
            references.append(ref)
            self.registry[entry.path] = ref

        return references

    def _parse_gitmodules(self) -> List[SubmoduleEntry]:
        """Parse .gitmodules file."""
        gitmodules_path = self.repo_root / ".gitmodules"
        if not gitmodules_path.exists():
            return []

        config = configparser.ConfigParser()
        config.read(gitmodules_path)

        entries = []
        for section in config.sections():
            if section.startswith('submodule "'):
                name = section[11:-1]  # Remove 'submodule "' and '"'
                entries.append(SubmoduleEntry(
                    name=name,
                    path=config.get(section, "path"),
                    url=config.get(section, "url"),
                ))
        return entries

    def _validate_with_git(self, entries: List[SubmoduleEntry]) -> List[SubmoduleEntry]:
        """Validate entries with git submodule status."""
        try:
            result = subprocess.run(
                ["git", "submodule", "status"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if not line:
                        continue
                    # Format: " abc1234 path (tag)" or "-abc1234 path"
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        commit = parts[0].lstrip("+-U ")
                        path = parts[1]
                        for entry in entries:
                            if entry.path == path:
                                entry.commit = commit
                                entry.status = line[0] if line[0] in " -+U" else " "
        except Exception:
            pass  # Fallback to entries without git validation
        return entries

    def _create_reference(self, entry: SubmoduleEntry) -> SubmoduleReference:
        """Create SubmoduleReference from entry."""
        return SubmoduleReference(
            id=str(ULID()),
            parent_roadmap_id=self._get_parent_roadmap_id(),
            submodule_path=entry.path,
            submodule_url=entry.url,
            submodule_commit=entry.commit,
            detected_at=datetime.utcnow(),
            detection_source=DetectionSource.GITMODULES,
            sync_status=SyncStatus.NEVER_SYNCED,
        )

    def _has_vibey_roadmap(self, submodule_path: str) -> bool:
        """Check if submodule has a Vibey roadmap."""
        submod_full_path = self.repo_root / submodule_path
        indicators = [
            submod_full_path / ".vibey" / "roadmap",
            submod_full_path / ".vibey" / "roadmap.yaml",
            submod_full_path / ".vibey" / "roadmap" / "roadmap.yaml",
        ]
        return any(p.exists() for p in indicators)

    def _read_roadmap_id(self, submodule_path: str) -> Optional[str]:
        """Read roadmap ID from submodule."""
        roadmap_yaml = self.repo_root / submodule_path / ".vibey" / "roadmap" / "roadmap.yaml"
        if roadmap_yaml.exists():
            import yaml
            with open(roadmap_yaml) as f:
                data = yaml.safe_load(f)
                return data.get("roadmap", {}).get("id")
        return None

    def _get_parent_roadmap_id(self) -> str:
        """Get parent roadmap ID."""
        roadmap_yaml = self.repo_root / ".vibey" / "roadmap" / "roadmap.yaml"
        if roadmap_yaml.exists():
            import yaml
            with open(roadmap_yaml) as f:
                data = yaml.safe_load(f)
                return data.get("roadmap", {}).get("id", "unknown")
        return "unknown"

    def get_vibey_submodules(self) -> List[SubmoduleReference]:
        """Return only submodules with Vibey roadmaps."""
        if not self.registry:
            self.discover()
        return [ref for ref in self.registry.values() if ref.has_vibey_roadmap]

    def refresh(self, path: str) -> Optional[SubmoduleReference]:
        """Refresh discovery for a specific submodule."""
        entries = self._parse_gitmodules()
        entry = next((e for e in entries if e.path == path), None)
        if entry:
            entries = self._validate_with_git([entry])
            ref = self._create_reference(entries[0])
            ref.has_vibey_roadmap = self._has_vibey_roadmap(path)
            if ref.has_vibey_roadmap:
                ref.submodule_roadmap_id = self._read_roadmap_id(path)
            self.registry[path] = ref
            return ref
        return None
```

### 4.2 CLI Commands (Specification)

```python
# vibey/cli/submodule.py
"""CLI commands for git submodule integration."""

import click
from vibey.cli.main import cli


@cli.group()
def submodule():
    """Git submodule integration commands."""
    pass


# === Discovery ===

@submodule.command("list")
def submodule_list():
    """List all detected submodules."""
    # Implementation: SubmoduleDiscovery.discover()
    pass


@submodule.command("discover")
def submodule_discover():
    """Refresh submodule discovery."""
    pass


@submodule.command("show")
@click.argument("path")
def submodule_show(path: str):
    """Show details for a specific submodule."""
    pass


# === Push-Down ===

@submodule.command("push-requirement")
@click.argument("ticket_id")
@click.argument("submodule_path")
@click.option("--title", required=True)
@click.option("--description", default="")
@click.option("--mode", type=click.Choice(["automatic", "notification", "manual"]), default="automatic")
def push_requirement(ticket_id: str, submodule_path: str, title: str, description: str, mode: str):
    """Push a requirement to a submodule."""
    pass


@submodule.command("requirements")
@click.option("--direction", type=click.Choice(["incoming", "outgoing"]), default="outgoing")
@click.option("--status", default=None)
def requirements(direction: str, status: str):
    """List cross-repo requirements."""
    pass


@submodule.command("accept-requirement")
@click.argument("requirement_id")
def accept_requirement(requirement_id: str):
    """Accept an incoming requirement (run in submodule)."""
    pass


@submodule.command("reject-requirement")
@click.argument("requirement_id")
@click.option("--reason", required=True)
def reject_requirement(requirement_id: str, reason: str):
    """Reject an incoming requirement (run in submodule)."""
    pass


# === Pull-Up ===

@submodule.command("status")
def submodule_status():
    """Show aggregated submodule progress."""
    pass


@submodule.command("blockers")
@click.option("--severity", type=click.Choice(["critical", "high", "medium", "low"]), default=None)
def blockers(severity: str):
    """List blockers from submodules."""
    pass


@submodule.command("refresh")
def refresh():
    """Force refresh submodule progress data."""
    pass


# === Cross-Repo Dependencies ===

@submodule.command("add-dep")
@click.argument("ticket_id")
@click.argument("dependency_ref")  # ticket@repo format
@click.option("--type", "dep_type", type=click.Choice(["completion", "artifact", "interface"]), default="completion")
@click.option("--blocking/--non-blocking", default=True)
@click.option("--reason", default=None)
def add_dep(ticket_id: str, dependency_ref: str, dep_type: str, blocking: bool, reason: str):
    """Add a cross-repo dependency."""
    pass


@submodule.command("deps")
@click.argument("ticket_id")
@click.option("--direction", type=click.Choice(["outgoing", "incoming", "both"]), default="both")
def deps(ticket_id: str, direction: str):
    """List cross-repo dependencies for a ticket."""
    pass


@submodule.command("validate-deps")
def validate_deps():
    """Validate cross-repo dependencies (check cycles, missing targets)."""
    pass


@submodule.command("dep-graph")
def dep_graph():
    """Visualize cross-repo dependency graph."""
    pass
```

---

## Part 5: Configuration Schema

```yaml
# .vibey/config/submodules.yaml

# Enable submodule integration
enabled: true

# === Discovery Settings ===
discovery:
  # Auto-discover triggers
  auto_discover:
    on_init: true
    on_roadmap_status: true
    on_git_pull: false

  # Detection methods (priority order)
  detection_methods:
    - gitmodules
    - git_command

  # Filtering
  include_patterns:
    - "*"
  exclude_patterns:
    - "vendor/*"
    - "third_party/*"

# === Push-Down Settings ===
push_down:
  enabled: true

  # Default push mode
  default_mode: notification  # automatic | notification | manual

  # Default ownership
  default_ownership: parent_owned

# === Pull-Up Settings ===
pull_up:
  enabled: true

  # Collection triggers
  triggers:
    on_roadmap_status: true
    on_git_pull: false
    scheduled_interval_minutes: 0  # 0 = disabled

  # Staleness
  stale_threshold_minutes: 60

  # Blocker surfacing
  blockers:
    surface_to_parent: true
    minimum_severity: medium
    notify_on_critical: true

  # Aggregation
  aggregation:
    weight_by: task_count  # task_count | equal | custom
    include_not_started: false

# === Cross-Repo Dependencies ===
cross_repo_deps:
  enabled: true

  # Validation
  validation:
    check_cycles: true
    check_missing_targets: true
    block_on_cycle: true

  # Resolution
  resolution:
    auto_satisfy_on_completion: true
    poll_interval_minutes: 0  # 0 = on-demand only

  # Notifications
  notifications:
    on_dependency_satisfied: true
    on_dependency_blocked: true
```

---

## Part 6: MCP Tools Specification

```python
# vibey/mcp/tools/submodule.py
"""MCP tools for git submodule integration."""

from vibey.mcp.decorators import mcp_tool


# === Discovery ===

@mcp_tool(
    name="submodule_list",
    description="List all detected submodules and their Vibey status"
)
def submodule_list() -> list:
    """List detected submodules."""
    pass


@mcp_tool(
    name="submodule_discover",
    description="Run submodule discovery and return findings"
)
def submodule_discover() -> dict:
    """Refresh discovery."""
    pass


@mcp_tool(
    name="submodule_roadmap",
    description="Get roadmap summary for a Vibey-enabled submodule"
)
def submodule_roadmap(path: str) -> dict:
    """Get submodule roadmap."""
    pass


# === Push-Down ===

@mcp_tool(
    name="submodule_push_requirement",
    description="Push a requirement to a submodule"
)
def submodule_push_requirement(
    parent_ticket_id: str,
    submodule_path: str,
    title: str,
    description: str = "",
    push_mode: str = "automatic"
) -> dict:
    """Push requirement."""
    pass


@mcp_tool(
    name="submodule_requirements",
    description="List cross-repo requirements"
)
def submodule_requirements(
    direction: str = "outgoing",
    status_filter: str = None
) -> list:
    """List requirements."""
    pass


@mcp_tool(
    name="submodule_accept_requirement",
    description="Accept an incoming requirement"
)
def submodule_accept_requirement(
    requirement_id: str,
    create_ticket: bool = True
) -> dict:
    """Accept requirement."""
    pass


# === Pull-Up ===

@mcp_tool(
    name="submodule_status",
    description="Get aggregated progress from all submodules"
)
def submodule_status() -> dict:
    """Get aggregated status."""
    pass


@mcp_tool(
    name="submodule_blockers",
    description="List blockers from submodules"
)
def submodule_blockers(
    severity_filter: str = None,
    submodule_filter: str = None
) -> list:
    """Get blockers."""
    pass


@mcp_tool(
    name="submodule_refresh",
    description="Force refresh of submodule progress data"
)
def submodule_refresh() -> dict:
    """Refresh progress."""
    pass


# === Cross-Repo Dependencies ===

@mcp_tool(
    name="task_add_cross_dep",
    description="Add a cross-repo dependency to a ticket"
)
def task_add_cross_dep(
    ticket_id: str,
    dependency_ref: str,
    dependency_type: str = "completion",
    blocking: bool = True,
    reason: str = None
) -> dict:
    """Add dependency."""
    pass


@mcp_tool(
    name="task_cross_deps",
    description="List cross-repo dependencies for a ticket"
)
def task_cross_deps(
    ticket_id: str,
    direction: str = "outgoing"
) -> list:
    """List dependencies."""
    pass


@mcp_tool(
    name="submodule_dep_graph",
    description="Get the full cross-repo dependency graph"
)
def submodule_dep_graph() -> dict:
    """Get dependency graph."""
    pass


@mcp_tool(
    name="submodule_validate_deps",
    description="Validate cross-repo dependencies"
)
def submodule_validate_deps() -> dict:
    """Validate dependencies."""
    pass
```

---

## Part 7: Implementation Roadmap (Sprint 2)

### Phase 1: Foundation (Tasks 1-2)
1. Create model files (`submodule.py`, `cross_repo.py`)
2. Add SQLite schema extensions
3. Implement `SubmoduleDiscovery` class
4. Add basic CLI commands (`submodule list`, `submodule discover`)

### Phase 2: Push-Down (Tasks 3-4)
1. Implement `RequirementPusher` class
2. Add push-down CLI commands
3. Add incoming requirements storage
4. Implement accept/reject flow

### Phase 3: Pull-Up (Tasks 5-6)
1. Implement `ProgressAggregator` class
2. Add blocker detection
3. Add aggregated progress storage
4. Add status CLI command

### Phase 4: Cross-Repo Dependencies (Tasks 7-8)
1. Implement `CrossRepoDependencyResolver`
2. Add cycle detection
3. Extend criterion system with `CrossRepoCriterionTarget`
4. Add dependency CLI commands

### Phase 5: MCP & Integration (Task 9)
1. Add all MCP tools
2. Integration tests
3. Documentation updates

---

## Appendix A: Reference Documents

- [RESEARCH_FINDINGS.md](RESEARCH_FINDINGS.md) - Task 1 output
- [DETECTION_DISCOVERY_DESIGN.md](DETECTION_DISCOVERY_DESIGN.md) - Task 2 output
- [PUSH_DOWN_DESIGN.md](PUSH_DOWN_DESIGN.md) - Task 3 output
- [PULL_UP_DESIGN.md](PULL_UP_DESIGN.md) - Task 4 output
- [CROSS_REPO_DEPS_DESIGN.md](CROSS_REPO_DEPS_DESIGN.md) - Task 5 output

## Appendix B: Related Architecture Documents

- [UNIFIED_TICKET_ARCHITECTURE.md](../../../../docs/roadmap/sqlite-backend/sqlite-backend-6/UNIFIED_TICKET_ARCHITECTURE.md)
- [Context System V2 DESIGN_DECISIONS.md](../../../context/tracks/context-system-v2/sprints/sprint-0-planning-design-review/DESIGN_DECISIONS.md)
