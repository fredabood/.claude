"""
Content versioning infrastructure for Implementation Mode.

This submodule provides versioning capabilities for tracking content changes
across the implementation lifecycle (plan, execution, post-mortem).

Core Components:
- ContentVersion: Immutable version of content at a point in time
- ContentVersioner: Service for creating and managing versions
- VersionStage: Enum for implementation lifecycle stages

Stage-Specific Versioners:
- PlanVersioner: Specialized versioning for the PLAN stage
- PlanVersionMetadata: Plan-specific metadata (status, criteria, files)
- PlanDiff: Diff between plan versions

Storage Structure:
    .vibey/roadmap/versions/
    └── {ticket_id}/
        ├── plan/
        │   ├── {version_id}.yaml
        │   └── current.yaml  # Points to latest version
        ├── execution/
        │   └── ...
        └── post_mortem/
            └── ...

Usage:
    from vibey.services.implementation.versioning import (
        ContentVersion,
        ContentVersioner,
        VersionStage,
        PlanVersioner,
        PlanVersionMetadata,
        PlanDiff,
    )
    from pathlib import Path

    # Initialize core versioner
    versioner = ContentVersioner(Path(".vibey/roadmap/versions"))

    # Use plan versioner for PLAN stage operations
    plan_versioner = PlanVersioner(versioner)
    version = plan_versioner.version_plan_creation(
        ticket=task,
        plan="# Implementation Plan\n\n...",
        author="claude-code",
    )

    # Get plan diff
    diff = plan_versioner.get_plan_diff(
        ticket_id=task.id,
        from_version=old_version_id,
        to_version=new_version_id,
    )

    # Check if content has changed
    if versioner.has_changed(ticket_id, VersionStage.PLAN, new_content):
        new_version = versioner.create_version(...)

    # Get version history
    history = versioner.get_history(ticket_id, stage=VersionStage.PLAN)

Design Reference:
- Context System V2: Content versioning for ticket lifecycle
- ADR-0001: ULID identifiers
- ADR-0002: Flat directory structure
"""

from vibey.services.implementation.versioning.core import (
    ContentVersion,
    ContentVersioner,
    VersionStage,
)
from vibey.services.implementation.versioning.plan import (
    PlanDiff,
    PlanVersioner,
    PlanVersionMetadata,
)
from vibey.services.implementation.versioning.post_mortem import (
    PostMortemDelta,
    PostMortemVersioner,
    PostMortemVersionMetadata,
)

__all__ = [
    # Core data classes
    "ContentVersion",
    # Core service
    "ContentVersioner",
    # Enums
    "VersionStage",
    # Plan-specific versioning
    "PlanDiff",
    "PlanVersioner",
    "PlanVersionMetadata",
    # Post-mortem versioning
    "PostMortemDelta",
    "PostMortemVersioner",
    "PostMortemVersionMetadata",
]
