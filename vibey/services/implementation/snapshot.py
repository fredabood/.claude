"""
CriterionSnapshot - Pre-task state capture for implementation tracking.

This module provides data structures and management for capturing
the state of criteria BEFORE task execution begins. This enables:

1. Accurate before/after comparisons
2. Progress measurement from specific starting points
3. Debugging and rollback support
4. Verification that task actually changed what was expected

Key Components:
- CriterionState: Snapshot of a single criterion's state
- CriterionSnapshot: Collection of criterion states for a task
- SnapshotManager: Capture, evaluate, save, and load snapshots

Snapshot Storage: .vibey/implementation/snapshots/{task_id}.yaml

Usage:
    from vibey.services.implementation.snapshot import (
        SnapshotManager,
        CriterionSnapshot,
        CriterionState,
    )
    from pathlib import Path

    # Create manager
    manager = SnapshotManager(roadmap_root=Path(".vibey/roadmap"))

    # Capture snapshot before task execution
    snapshot = manager.capture_snapshot(task)

    # Save for later reference
    snapshot_path = Path(".vibey/implementation/snapshots")
    manager.save_snapshot(snapshot, snapshot_path / f"{task.id}.yaml")

    # Load existing snapshot
    loaded = manager.load_snapshot(snapshot_path / f"{task.id}.yaml")

Design Reference:
- Context System V2: Pre-task state capture
- Implementation Mode Track Sprint 3
- ADR-0002: Flat Directory Structure
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket
    from vibey.roadmap.models.ticket.completable import Criterion


# =============================================================================
# ENUMS
# =============================================================================


class CriterionType(str, Enum):
    """
    Classification of criterion target types for snapshot tracking.

    Maps to CriterionTargetType but focused on snapshot-relevant categories.
    """

    COMPLETABLE = "completable"
    FILE_EXISTS = "file_exists"
    TEST_PASSES = "test_passes"
    TEST_COVERAGE = "test_coverage"
    THRESHOLD = "threshold"
    MANUAL = "manual"
    EXTERNAL = "external"
    ARTIFACT = "artifact"
    TOKEN_ESTIMATE = "token_estimate"
    UNKNOWN = "unknown"


class CriterionStatus(str, Enum):
    """
    Evaluation status of a criterion at snapshot time.
    """

    MET = "met"
    NOT_MET = "not_met"
    SKIPPED = "skipped"  # Non-required criteria
    ERROR = "error"  # Evaluation failed


# =============================================================================
# DATA MODELS
# =============================================================================


@dataclass
class CriterionState:
    """
    Snapshot of a single criterion's state at a point in time.

    Captures everything needed to understand and compare criterion state:
    - Identity: which ticket and criterion
    - Type: what kind of criterion (for evaluation logic)
    - Status: whether it was met at snapshot time
    - Evidence: any supporting data from evaluation

    Attributes:
        ticket_id: ULID of the ticket containing this criterion
        criterion_index: Index of criterion within ticket's criteria list
        criterion_type: Type classification for evaluation
        description: Human-readable description of the criterion
        status: Evaluation status at snapshot time
        last_evaluated: When this state was captured
        evidence: Optional supporting data from evaluation
    """

    ticket_id: str
    criterion_index: int
    criterion_type: CriterionType
    description: str
    status: CriterionStatus
    last_evaluated: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    evidence: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return {
            "ticket_id": self.ticket_id,
            "criterion_index": self.criterion_index,
            "criterion_type": self.criterion_type.value,
            "description": self.description,
            "status": self.status.value,
            "last_evaluated": self.last_evaluated.isoformat(),
            "evidence": self.evidence,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CriterionState":
        """Create from dictionary (YAML deserialization)."""
        # Parse timestamp
        last_evaluated = data.get("last_evaluated")
        if isinstance(last_evaluated, str):
            last_evaluated = datetime.fromisoformat(
                last_evaluated.replace("Z", "+00:00")
            )
        elif last_evaluated is None:
            last_evaluated = datetime.now(timezone.utc)

        # Parse criterion type
        type_str = data.get("criterion_type", "unknown")
        try:
            criterion_type = CriterionType(type_str)
        except ValueError:
            criterion_type = CriterionType.UNKNOWN

        # Parse status
        status_str = data.get("status", "not_met")
        try:
            status = CriterionStatus(status_str)
        except ValueError:
            status = CriterionStatus.NOT_MET

        return cls(
            ticket_id=data.get("ticket_id", ""),
            criterion_index=data.get("criterion_index", 0),
            criterion_type=criterion_type,
            description=data.get("description", ""),
            status=status,
            last_evaluated=last_evaluated,
            evidence=data.get("evidence"),
        )

    @property
    def is_met(self) -> bool:
        """Check if criterion was met at snapshot time."""
        return self.status == CriterionStatus.MET


@dataclass
class CriterionSnapshot:
    """
    Collection of criterion states captured before task execution.

    Represents the complete state of all relevant criteria at the moment
    before a task begins execution. This provides the baseline for
    measuring progress and verifying changes.

    Attributes:
        task_id: ULID of the task this snapshot is for
        captured_at: When the snapshot was taken
        criteria_states: Map of criterion reference -> state
            Key format: "{ticket_id}:{criterion_index}"

    Example:
        >>> snapshot = CriterionSnapshot(task_id="01KCZF73PX...")
        >>> snapshot.criteria_states["01KCZF73PX...:0"] = CriterionState(...)
        >>> snapshot.save(Path(".vibey/implementation/snapshots/01KCZF73PX....yaml"))
    """

    task_id: str
    captured_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    criteria_states: Dict[str, CriterionState] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return {
            "task_id": self.task_id,
            "captured_at": self.captured_at.isoformat(),
            "criteria_states": {
                ref: state.to_dict()
                for ref, state in self.criteria_states.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CriterionSnapshot":
        """Create from dictionary (YAML deserialization)."""
        # Parse timestamp
        captured_at = data.get("captured_at")
        if isinstance(captured_at, str):
            captured_at = datetime.fromisoformat(
                captured_at.replace("Z", "+00:00")
            )
        elif captured_at is None:
            captured_at = datetime.now(timezone.utc)

        # Parse criteria states
        states_data = data.get("criteria_states", {})
        criteria_states = {
            ref: CriterionState.from_dict(state_data)
            for ref, state_data in states_data.items()
        }

        return cls(
            task_id=data.get("task_id", ""),
            captured_at=captured_at,
            criteria_states=criteria_states,
        )

    @property
    def total_criteria(self) -> int:
        """Total number of criteria in snapshot."""
        return len(self.criteria_states)

    @property
    def met_count(self) -> int:
        """Count of criteria that were met at snapshot time."""
        return sum(1 for s in self.criteria_states.values() if s.is_met)

    @property
    def not_met_count(self) -> int:
        """Count of criteria not met at snapshot time."""
        return sum(1 for s in self.criteria_states.values() if not s.is_met)

    def get_state(self, ticket_id: str, criterion_index: int) -> Optional[CriterionState]:
        """Get state for a specific criterion by ticket ID and index."""
        ref = f"{ticket_id}:{criterion_index}"
        return self.criteria_states.get(ref)

    def add_state(self, state: CriterionState) -> None:
        """Add a criterion state to the snapshot."""
        ref = f"{state.ticket_id}:{state.criterion_index}"
        self.criteria_states[ref] = state


# =============================================================================
# SNAPSHOT MANAGER
# =============================================================================


class SnapshotManager:
    """
    Manager for capturing, evaluating, saving, and loading criterion snapshots.

    SnapshotManager provides the primary interface for working with
    criterion snapshots. It handles:

    1. Capture: Creating snapshots from task criteria
    2. Evaluate: Checking current state of individual criteria
    3. Save: Persisting snapshots to YAML files
    4. Load: Restoring snapshots from YAML files

    Attributes:
        roadmap_root: Path to .vibey/roadmap directory

    Example:
        >>> manager = SnapshotManager(Path(".vibey/roadmap"))
        >>> snapshot = manager.capture_snapshot(task)
        >>> manager.save_snapshot(snapshot, Path(".vibey/implementation/snapshots/task.yaml"))
    """

    def __init__(self, roadmap_root: Path):
        """
        Initialize SnapshotManager with roadmap root directory.

        Args:
            roadmap_root: Path to .vibey/roadmap directory
        """
        self.roadmap_root = roadmap_root

    def capture_snapshot(self, task: "HierarchicalTicket") -> CriterionSnapshot:
        """
        Capture snapshot of all relevant criteria before task execution.

        Evaluates all criteria from the task's all_criteria property
        and records their current state. This provides the baseline
        for measuring task progress.

        Args:
            task: The HierarchicalTicket to capture snapshot for

        Returns:
            CriterionSnapshot with states for all criteria
        """
        snapshot = CriterionSnapshot(
            task_id=task.id,
            captured_at=datetime.now(timezone.utc),
        )

        # Get all criteria from the task (includes instantiated from requirements)
        all_criteria = getattr(task, 'all_criteria', task.criteria)

        for index, criterion in enumerate(all_criteria):
            state = self._evaluate_criterion(task.id, index, criterion)
            snapshot.add_state(state)

        return snapshot

    def evaluate_criterion(self, ref: str) -> Optional[CriterionState]:
        """
        Evaluate current state of a criterion by reference.

        The reference format is "{ticket_id}:{criterion_index}".
        This method loads the ticket and evaluates the specific criterion.

        Args:
            ref: Criterion reference in format "ticket_id:criterion_index"

        Returns:
            CriterionState if found and evaluated, None if not found
        """
        try:
            ticket_id, index_str = ref.split(":", 1)
            criterion_index = int(index_str)
        except (ValueError, AttributeError):
            return None

        # Load the ticket to evaluate the criterion
        from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket

        try:
            # Try to load via the configured loader
            if HierarchicalTicket._loader is not None:
                ticket = HierarchicalTicket._loader.load(ticket_id)
            else:
                # Fallback: load from YAML file directly
                ticket = self._load_ticket_from_yaml(ticket_id)

            if ticket is None:
                return None

            # Get all criteria
            all_criteria = getattr(ticket, 'all_criteria', ticket.criteria)

            if criterion_index >= len(all_criteria):
                return None

            criterion = all_criteria[criterion_index]
            return self._evaluate_criterion(ticket_id, criterion_index, criterion)

        except Exception:
            return None

    def save_snapshot(self, snapshot: CriterionSnapshot, path: Path) -> None:
        """
        Persist snapshot to YAML file.

        Creates parent directories if they don't exist.

        Args:
            snapshot: The CriterionSnapshot to save
            path: Path to save snapshot file

        Example:
            >>> manager.save_snapshot(
            ...     snapshot,
            ...     Path(".vibey/implementation/snapshots/01KCZF73PX....yaml")
            ... )
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(
                snapshot.to_dict(),
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

    def load_snapshot(self, path: Path) -> CriterionSnapshot:
        """
        Load snapshot from YAML file.

        Args:
            path: Path to snapshot file

        Returns:
            CriterionSnapshot loaded from file

        Raises:
            FileNotFoundError: If snapshot file doesn't exist
            yaml.YAMLError: If file contains invalid YAML
        """
        if not path.exists():
            raise FileNotFoundError(f"Snapshot file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if data is None:
            data = {}

        return CriterionSnapshot.from_dict(data)

    def get_snapshot_path(self, task_id: str) -> Path:
        """
        Get the standard path for a task's snapshot file.

        Snapshot storage: .vibey/implementation/snapshots/{task_id}.yaml

        Args:
            task_id: ULID of the task

        Returns:
            Path to the snapshot file
        """
        return (
            self.roadmap_root.parent / "implementation" / "snapshots" / f"{task_id}.yaml"
        )

    def snapshot_exists(self, task_id: str) -> bool:
        """Check if a snapshot exists for a task."""
        return self.get_snapshot_path(task_id).exists()

    def load_task_snapshot(self, task_id: str) -> Optional[CriterionSnapshot]:
        """
        Load snapshot for a task by ID.

        Convenience method that uses the standard snapshot path.

        Args:
            task_id: ULID of the task

        Returns:
            CriterionSnapshot if found, None if not exists
        """
        path = self.get_snapshot_path(task_id)
        if not path.exists():
            return None
        return self.load_snapshot(path)

    def save_task_snapshot(self, snapshot: CriterionSnapshot) -> Path:
        """
        Save snapshot using the standard path.

        Convenience method that derives path from task_id.

        Args:
            snapshot: The CriterionSnapshot to save

        Returns:
            Path where snapshot was saved
        """
        path = self.get_snapshot_path(snapshot.task_id)
        self.save_snapshot(snapshot, path)
        return path

    # =========================================================================
    # PRIVATE HELPER METHODS
    # =========================================================================

    def _evaluate_criterion(
        self,
        ticket_id: str,
        criterion_index: int,
        criterion: "Criterion",
    ) -> CriterionState:
        """
        Evaluate a single criterion and create state snapshot.

        Args:
            ticket_id: ULID of containing ticket
            criterion_index: Index within criteria list
            criterion: The Criterion to evaluate

        Returns:
            CriterionState capturing current evaluation
        """
        # Determine criterion type from target
        criterion_type = self._get_criterion_type(criterion)

        # Determine status
        try:
            if not criterion.required:
                status = CriterionStatus.SKIPPED
            elif criterion.is_met:
                status = CriterionStatus.MET
            else:
                status = CriterionStatus.NOT_MET
        except Exception:
            status = CriterionStatus.ERROR

        # Gather evidence from target
        evidence = self._gather_evidence(criterion)

        return CriterionState(
            ticket_id=ticket_id,
            criterion_index=criterion_index,
            criterion_type=criterion_type,
            description=criterion.description,
            status=status,
            last_evaluated=datetime.now(timezone.utc),
            evidence=evidence,
        )

    def _get_criterion_type(self, criterion: "Criterion") -> CriterionType:
        """Determine criterion type from its target."""
        target = criterion.target
        target_class = type(target).__name__

        type_mapping = {
            "CompletableTarget": CriterionType.COMPLETABLE,
            "FileExistsTarget": CriterionType.FILE_EXISTS,
            "TestPassesTarget": CriterionType.TEST_PASSES,
            "TestCoverageTarget": CriterionType.TEST_COVERAGE,
            "ThresholdTarget": CriterionType.THRESHOLD,
            "ManualTarget": CriterionType.MANUAL,
            "ExternalTarget": CriterionType.EXTERNAL,
            "ArtifactTarget": CriterionType.ARTIFACT,
            "TokenEstimateTarget": CriterionType.TOKEN_ESTIMATE,
        }

        return type_mapping.get(target_class, CriterionType.UNKNOWN)

    def _gather_evidence(self, criterion: "Criterion") -> Optional[Dict[str, Any]]:
        """
        Gather evidence from criterion target for debugging.

        Returns target-specific information that helps understand
        why a criterion is or isn't met.
        """
        target = criterion.target
        evidence: Dict[str, Any] = {}

        # Add target type
        evidence["target_type"] = type(target).__name__

        # Add target-specific evidence
        if hasattr(target, "completable_id"):
            evidence["completable_id"] = target.completable_id
        if hasattr(target, "required_status"):
            evidence["required_status"] = str(target.required_status)
        if hasattr(target, "path"):
            evidence["path"] = str(target.path)
        if hasattr(target, "paths"):
            evidence["paths"] = [str(p) for p in target.paths]
        if hasattr(target, "test_command"):
            evidence["test_command"] = target.test_command
        if hasattr(target, "threshold"):
            evidence["threshold"] = target.threshold
        if hasattr(target, "current_value"):
            evidence["current_value"] = target.current_value
        if hasattr(target, "artifact_id"):
            evidence["artifact_id"] = target.artifact_id

        return evidence if evidence else None

    def _load_ticket_from_yaml(self, ticket_id: str) -> Optional["HierarchicalTicket"]:
        """
        Load ticket directly from YAML file as fallback.

        Checks tasks, sprints, and tracks directories.
        """
        from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket

        # Check each directory type
        for subdir in ["tasks", "sprints", "tracks"]:
            yaml_path = self.roadmap_root / subdir / f"{ticket_id}.yaml"
            if yaml_path.exists():
                try:
                    with open(yaml_path, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                    if data:
                        return HierarchicalTicket.model_validate(data)
                except Exception:
                    pass

        return None


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Data classes
    "CriterionState",
    "CriterionSnapshot",
    # Manager
    "SnapshotManager",
    # Enums
    "CriterionType",
    "CriterionStatus",
]
