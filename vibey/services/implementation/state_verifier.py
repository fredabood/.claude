"""
RoadmapStateVerifier - Verify YAML/SQLite synchronization state.

This module provides verification of synchronization between YAML files
(source of truth) and the SQLite database cache. It can detect discrepancies,
assess their severity, and optionally auto-fix them by rebuilding from YAML.

Key Features:
- Verify all YAML files have corresponding DB records
- Verify all DB records have corresponding YAML files
- Compare field values between YAML and DB
- Classify discrepancy severity (none, minor, major, critical)
- Auto-fix by rebuilding database from YAML

Usage:
    from vibey.services.implementation import RoadmapStateVerifier

    verifier = RoadmapStateVerifier(roadmap_root=Path(".vibey/roadmap"))

    # Check sync status
    status = verifier.verify_sync()
    if not status.is_synced:
        print(f"Found {len(status.discrepancies)} discrepancies")
        print(f"Severity: {status.severity}")

    # Get discrepancy details
    discrepancies = verifier.get_discrepancies()
    for d in discrepancies:
        print(f"{d.entity_type}/{d.entity_id}: {d.issue_type} - {d.details}")

    # Auto-fix by rebuilding from YAML
    if verifier.should_abort(status):
        print("Critical discrepancies detected - aborting")
    else:
        result = verifier.auto_fix(discrepancies)
        print(f"Fixed {result.fixed_count} issues")

Design Reference:
- Dual Storage System (YAML + SQLite)
- ADR-0003: Dual storage SQLite-YAML strategy
- Implementation Mode Track Sprint 2
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

DEFAULT_ROADMAP_ROOT = Path(".vibey/roadmap")
"""Default path to the roadmap directory containing YAML files."""

DEFAULT_DB_PATH = Path(".vibey/roadmap.db")
"""Default path to the SQLite database file."""

# Key fields to compare for each entity type
TRACK_KEY_FIELDS = frozenset({
    "name", "status", "priority", "blocked", "roadmap_id",
    "started", "completed", "estimated_duration",
})

SPRINT_KEY_FIELDS = frozenset({
    "name", "status", "blocked", "track_id", "roadmap_id",
    "started", "completed", "goal", "description",
})

TASK_KEY_FIELDS = frozenset({
    "title", "status", "blocked", "sprint_id", "track_id", "roadmap_id",
    "task_type", "priority", "started", "completed", "deferred",
    "estimated_tokens", "actual_tokens", "complexity",
})


# =============================================================================
# ENUMS
# =============================================================================


class IssueType(str, Enum):
    """
    Type of discrepancy between YAML and database.

    Values:
        MISSING_IN_DB: YAML file exists but no corresponding DB record
        MISSING_IN_YAML: DB record exists but no corresponding YAML file
        FIELD_MISMATCH: Field values differ between YAML and DB
    """
    MISSING_IN_DB = "missing_in_db"
    MISSING_IN_YAML = "missing_in_yaml"
    FIELD_MISMATCH = "field_mismatch"


class Severity(str, Enum):
    """
    Severity level of sync discrepancies.

    Values:
        NONE: No discrepancies found - fully synced
        MINOR: Only metadata or computed fields differ
        MAJOR: Status or key fields differ (requires attention)
        CRITICAL: Missing entities or corruption detected (may require abort)
    """
    NONE = "none"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"


# =============================================================================
# DATA MODELS
# =============================================================================


@dataclass
class Discrepancy:
    """
    Record of a single discrepancy between YAML and database.

    Attributes:
        entity_type: Type of entity ('track', 'sprint', 'task')
        entity_id: ULID of the entity
        issue_type: Type of issue detected
        details: Human-readable description of the discrepancy
        field_name: Name of mismatched field (for FIELD_MISMATCH)
        yaml_value: Value from YAML file
        db_value: Value from database
    """
    entity_type: str
    entity_id: str
    issue_type: IssueType
    details: str
    field_name: Optional[str] = None
    yaml_value: Optional[Any] = None
    db_value: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for logging/storage."""
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "issue_type": self.issue_type.value,
            "details": self.details,
            "field_name": self.field_name,
            "yaml_value": str(self.yaml_value) if self.yaml_value is not None else None,
            "db_value": str(self.db_value) if self.db_value is not None else None,
        }


@dataclass
class SyncStatus:
    """
    Overall synchronization status between YAML and database.

    Attributes:
        is_synced: True if no discrepancies found
        yaml_count: Number of YAML files found
        db_count: Number of database records found
        discrepancies: List of discrepancies found
        last_verified: When verification was performed
    """
    is_synced: bool
    yaml_count: int
    db_count: int
    discrepancies: List[Discrepancy] = field(default_factory=list)
    last_verified: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @property
    def severity(self) -> Severity:
        """
        Compute severity based on discrepancies.

        Returns:
            Severity level based on discrepancy types and counts:
            - NONE: No discrepancies
            - MINOR: Only field mismatches on non-critical fields
            - MAJOR: Status mismatches or multiple issues
            - CRITICAL: Missing entities
        """
        if not self.discrepancies:
            return Severity.NONE

        has_missing = any(
            d.issue_type in (IssueType.MISSING_IN_DB, IssueType.MISSING_IN_YAML)
            for d in self.discrepancies
        )

        if has_missing:
            return Severity.CRITICAL

        # Check for status mismatches
        has_status_mismatch = any(
            d.issue_type == IssueType.FIELD_MISMATCH and d.field_name == "status"
            for d in self.discrepancies
        )

        if has_status_mismatch or len(self.discrepancies) > 10:
            return Severity.MAJOR

        return Severity.MINOR

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for logging/storage."""
        return {
            "is_synced": self.is_synced,
            "yaml_count": self.yaml_count,
            "db_count": self.db_count,
            "discrepancy_count": len(self.discrepancies),
            "severity": self.severity.value,
            "last_verified": self.last_verified.isoformat(),
            "discrepancies": [d.to_dict() for d in self.discrepancies[:20]],
        }


@dataclass
class FixResult:
    """
    Result of auto-fix operation.

    Attributes:
        fixed_count: Number of discrepancies fixed
        failed_count: Number of discrepancies that could not be fixed
        actions_taken: List of actions performed during fix
    """
    fixed_count: int
    failed_count: int
    actions_taken: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for logging/storage."""
        return {
            "fixed_count": self.fixed_count,
            "failed_count": self.failed_count,
            "actions_taken": self.actions_taken,
        }


# =============================================================================
# STATE VERIFIER
# =============================================================================


class RoadmapStateVerifier:
    """
    Verifies synchronization between YAML files and SQLite database.

    The verifier checks:
    1. All YAML files have corresponding database records
    2. All database records have corresponding YAML files
    3. Field values match between YAML and database

    YAML is always the source of truth. Auto-fix rebuilds the database
    from YAML files.

    Attributes:
        roadmap_root: Path to the roadmap directory with YAML files
        db_path: Path to the SQLite database file

    Example:
        >>> verifier = RoadmapStateVerifier()
        >>> status = verifier.verify_sync()
        >>> if not status.is_synced:
        ...     if verifier.should_abort(status):
        ...         raise RuntimeError("Critical sync issues")
        ...     result = verifier.auto_fix(status.discrepancies)
    """

    def __init__(
        self,
        roadmap_root: Optional[Path] = None,
        db_path: Optional[Path] = None,
    ):
        """
        Initialize state verifier.

        Args:
            roadmap_root: Path to roadmap directory (default: .vibey/roadmap)
            db_path: Path to SQLite database (default: .vibey/roadmap.db)
        """
        self.roadmap_root = Path(roadmap_root) if roadmap_root else DEFAULT_ROADMAP_ROOT
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self._cached_discrepancies: Optional[List[Discrepancy]] = None

    # =========================================================================
    # MAIN VERIFICATION
    # =========================================================================

    def verify_sync(self) -> SyncStatus:
        """
        Verify YAML matches SQLite.

        Compares all YAML files against database records, checking for:
        - Missing entities in either direction
        - Field value mismatches

        Returns:
            SyncStatus with is_synced flag and any discrepancies found

        Raises:
            FileNotFoundError: If roadmap_root doesn't exist
        """
        logger.info("Verifying YAML/SQLite sync status")

        if not self.roadmap_root.exists():
            raise FileNotFoundError(f"Roadmap root not found: {self.roadmap_root}")

        discrepancies: List[Discrepancy] = []

        # Count YAML files
        yaml_tracks = self._get_yaml_entity_ids("tracks")
        yaml_sprints = self._get_yaml_entity_ids("sprints")
        yaml_tasks = self._get_yaml_entity_ids("tasks")
        yaml_count = len(yaml_tracks) + len(yaml_sprints) + len(yaml_tasks)

        # Check if database exists
        if not self.db_path.exists():
            logger.warning("Database does not exist")
            # All YAML files are missing in DB
            for entity_id in yaml_tracks:
                discrepancies.append(Discrepancy(
                    entity_type="track",
                    entity_id=entity_id,
                    issue_type=IssueType.MISSING_IN_DB,
                    details=f"Track {entity_id} exists in YAML but database not found",
                ))
            for entity_id in yaml_sprints:
                discrepancies.append(Discrepancy(
                    entity_type="sprint",
                    entity_id=entity_id,
                    issue_type=IssueType.MISSING_IN_DB,
                    details=f"Sprint {entity_id} exists in YAML but database not found",
                ))
            for entity_id in yaml_tasks:
                discrepancies.append(Discrepancy(
                    entity_type="task",
                    entity_id=entity_id,
                    issue_type=IssueType.MISSING_IN_DB,
                    details=f"Task {entity_id} exists in YAML but database not found",
                ))

            self._cached_discrepancies = discrepancies
            return SyncStatus(
                is_synced=False,
                yaml_count=yaml_count,
                db_count=0,
                discrepancies=discrepancies,
            )

        # Count database records
        db_tracks = self._get_db_entity_ids("tracks")
        db_sprints = self._get_db_entity_ids("sprints")
        db_tasks = self._get_db_entity_ids("tasks")
        db_count = len(db_tracks) + len(db_sprints) + len(db_tasks)

        # Check tracks
        discrepancies.extend(self._verify_entity_sync(
            entity_type="track",
            yaml_ids=yaml_tracks,
            db_ids=db_tracks,
            key_fields=TRACK_KEY_FIELDS,
        ))

        # Check sprints
        discrepancies.extend(self._verify_entity_sync(
            entity_type="sprint",
            yaml_ids=yaml_sprints,
            db_ids=db_sprints,
            key_fields=SPRINT_KEY_FIELDS,
        ))

        # Check tasks
        discrepancies.extend(self._verify_entity_sync(
            entity_type="task",
            yaml_ids=yaml_tasks,
            db_ids=db_tasks,
            key_fields=TASK_KEY_FIELDS,
        ))

        self._cached_discrepancies = discrepancies

        status = SyncStatus(
            is_synced=len(discrepancies) == 0,
            yaml_count=yaml_count,
            db_count=db_count,
            discrepancies=discrepancies,
        )

        logger.info(
            f"Sync verification complete: synced={status.is_synced}, "
            f"discrepancies={len(discrepancies)}, severity={status.severity.value}"
        )

        return status

    def get_discrepancies(self) -> List[Discrepancy]:
        """
        Get list of all discrepancies.

        If verify_sync() hasn't been called, calls it first.

        Returns:
            List of Discrepancy objects
        """
        if self._cached_discrepancies is None:
            self.verify_sync()
        return self._cached_discrepancies or []

    # =========================================================================
    # AUTO-FIX
    # =========================================================================

    def auto_fix(
        self,
        discrepancies: Optional[List[Discrepancy]] = None
    ) -> FixResult:
        """
        Attempt to fix discrepancies by rebuilding from YAML.

        YAML is the source of truth, so fixing means rebuilding the
        database from YAML files. This handles:
        - MISSING_IN_DB: Rebuild will add missing records
        - FIELD_MISMATCH: Rebuild will update mismatched fields
        - MISSING_IN_YAML: Cannot fix (orphan DB records will be removed)

        Args:
            discrepancies: List of discrepancies to fix (if None, uses cached)

        Returns:
            FixResult with counts of fixed and failed issues

        Note:
            This operation is destructive - it replaces the entire database.
            Always backup before running if you have uncommitted DB changes.
        """
        if discrepancies is None:
            discrepancies = self.get_discrepancies()

        if not discrepancies:
            logger.info("No discrepancies to fix")
            return FixResult(fixed_count=0, failed_count=0, actions_taken=[])

        logger.info(f"Auto-fixing {len(discrepancies)} discrepancies")

        actions: List[str] = []
        fixed = 0
        failed = 0

        try:
            # Import here to avoid circular imports
            from vibey.roadmap.serialization.backend import SyncManager

            sync_manager = SyncManager(
                roadmap_dir=self.roadmap_root,
                db_path=self.db_path,
            )

            actions.append("Rebuilding database from YAML files")
            sync_manager.rebuild(force=True)
            actions.append("Database rebuild completed successfully")

            # Count fixed issues by type
            for d in discrepancies:
                if d.issue_type == IssueType.MISSING_IN_YAML:
                    # Orphan DB records are removed during rebuild
                    actions.append(
                        f"Removed orphan {d.entity_type} {d.entity_id} from database"
                    )
                    fixed += 1
                elif d.issue_type == IssueType.MISSING_IN_DB:
                    actions.append(
                        f"Added {d.entity_type} {d.entity_id} to database from YAML"
                    )
                    fixed += 1
                elif d.issue_type == IssueType.FIELD_MISMATCH:
                    actions.append(
                        f"Updated {d.entity_type} {d.entity_id}.{d.field_name} "
                        f"from YAML value"
                    )
                    fixed += 1

            # Clear cached discrepancies after fix
            self._cached_discrepancies = None

            logger.info(f"Auto-fix complete: fixed={fixed}, failed={failed}")

        except Exception as e:
            logger.error(f"Auto-fix failed: {e}")
            failed = len(discrepancies)
            actions.append(f"Fix failed: {e}")

        return FixResult(
            fixed_count=fixed,
            failed_count=failed,
            actions_taken=actions,
        )

    # =========================================================================
    # ABORT DECISION
    # =========================================================================

    def should_abort(self, status: SyncStatus) -> bool:
        """
        Determine if discrepancies require aborting the operation.

        Critical discrepancies that warrant abort:
        - Missing entities (corrupted state)
        - Large number of mismatches (something is wrong)
        - Status field mismatches on in-progress work

        Args:
            status: SyncStatus from verify_sync()

        Returns:
            True if operation should be aborted, False if safe to continue
        """
        if status.is_synced:
            return False

        severity = status.severity

        # Critical severity always requires abort
        if severity == Severity.CRITICAL:
            logger.warning(
                "Critical sync discrepancies detected - abort recommended"
            )
            return True

        # Major severity with many issues requires abort
        if severity == Severity.MAJOR and len(status.discrepancies) > 20:
            logger.warning(
                f"Major sync issues ({len(status.discrepancies)} discrepancies) "
                "- abort recommended"
            )
            return True

        # Check for status mismatches on in_progress items
        for d in status.discrepancies:
            if (
                d.issue_type == IssueType.FIELD_MISMATCH
                and d.field_name == "status"
                and d.yaml_value == "in_progress"
            ):
                logger.warning(
                    f"Status mismatch on in-progress {d.entity_type} {d.entity_id} "
                    "- abort recommended"
                )
                return True

        return False

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _get_yaml_entity_ids(self, entity_dir: str) -> Set[str]:
        """
        Get set of entity IDs from YAML files.

        Args:
            entity_dir: Subdirectory name ('tracks', 'sprints', 'tasks')

        Returns:
            Set of entity IDs (from filenames)
        """
        entity_path = self.roadmap_root / entity_dir
        if not entity_path.exists():
            return set()

        ids = set()
        for yaml_file in entity_path.glob("*.yaml"):
            if yaml_file.name.startswith("."):
                continue
            # ID is filename without .yaml extension
            entity_id = yaml_file.stem
            ids.add(entity_id)

        return ids

    def _get_db_entity_ids(self, table_name: str) -> Set[str]:
        """
        Get set of entity IDs from database table.

        Args:
            table_name: Database table name

        Returns:
            Set of entity IDs
        """
        import sqlite3

        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.execute(f"SELECT id FROM {table_name}")
            ids = {row[0] for row in cursor.fetchall()}
            conn.close()
            return ids
        except sqlite3.Error as e:
            logger.error(f"Failed to query {table_name}: {e}")
            return set()

    def _verify_entity_sync(
        self,
        entity_type: str,
        yaml_ids: Set[str],
        db_ids: Set[str],
        key_fields: frozenset,
    ) -> List[Discrepancy]:
        """
        Verify sync for a single entity type.

        Args:
            entity_type: Type name ('track', 'sprint', 'task')
            yaml_ids: Set of IDs from YAML files
            db_ids: Set of IDs from database
            key_fields: Set of field names to compare

        Returns:
            List of discrepancies found
        """
        discrepancies: List[Discrepancy] = []

        # Find missing in database
        missing_in_db = yaml_ids - db_ids
        for entity_id in missing_in_db:
            discrepancies.append(Discrepancy(
                entity_type=entity_type,
                entity_id=entity_id,
                issue_type=IssueType.MISSING_IN_DB,
                details=f"{entity_type.capitalize()} {entity_id} exists in YAML "
                        f"but not in database",
            ))

        # Find missing in YAML (orphan DB records)
        missing_in_yaml = db_ids - yaml_ids
        for entity_id in missing_in_yaml:
            discrepancies.append(Discrepancy(
                entity_type=entity_type,
                entity_id=entity_id,
                issue_type=IssueType.MISSING_IN_YAML,
                details=f"{entity_type.capitalize()} {entity_id} exists in database "
                        f"but not in YAML",
            ))

        # Compare field values for entities that exist in both
        common_ids = yaml_ids & db_ids
        for entity_id in common_ids:
            field_discrepancies = self._compare_entity_fields(
                entity_type=entity_type,
                entity_id=entity_id,
                key_fields=key_fields,
            )
            discrepancies.extend(field_discrepancies)

        return discrepancies

    def _compare_entity_fields(
        self,
        entity_type: str,
        entity_id: str,
        key_fields: frozenset,
    ) -> List[Discrepancy]:
        """
        Compare field values between YAML and database for an entity.

        Args:
            entity_type: Type name ('track', 'sprint', 'task')
            entity_id: Entity ID to compare
            key_fields: Set of field names to compare

        Returns:
            List of field mismatch discrepancies
        """
        discrepancies: List[Discrepancy] = []

        try:
            yaml_data = self._load_yaml_entity(entity_type, entity_id)
            db_data = self._load_db_entity(entity_type, entity_id)

            if yaml_data is None or db_data is None:
                return discrepancies

            for field_name in key_fields:
                yaml_value = yaml_data.get(field_name)
                db_value = db_data.get(field_name)

                # Normalize values for comparison
                yaml_value = self._normalize_value(yaml_value)
                db_value = self._normalize_value(db_value)

                if yaml_value != db_value:
                    discrepancies.append(Discrepancy(
                        entity_type=entity_type,
                        entity_id=entity_id,
                        issue_type=IssueType.FIELD_MISMATCH,
                        details=f"{field_name}: YAML={yaml_value}, DB={db_value}",
                        field_name=field_name,
                        yaml_value=yaml_value,
                        db_value=db_value,
                    ))

        except Exception as e:
            logger.warning(
                f"Failed to compare fields for {entity_type} {entity_id}: {e}"
            )

        return discrepancies

    def _load_yaml_entity(
        self,
        entity_type: str,
        entity_id: str
    ) -> Optional[Dict[str, Any]]:
        """Load entity data from YAML file."""
        import yaml

        dir_name = f"{entity_type}s"  # track -> tracks
        yaml_path = self.roadmap_root / dir_name / f"{entity_id}.yaml"

        if not yaml_path.exists():
            return None

        try:
            with open(yaml_path, 'r') as f:
                data = yaml.safe_load(f) or {}

            # YAML files have a wrapper element (track:, sprint:, task:)
            # Extract the inner data if wrapper exists
            if entity_type in data and isinstance(data[entity_type], dict):
                return data[entity_type]

            return data
        except Exception as e:
            logger.warning(f"Failed to load YAML {yaml_path}: {e}")
            return None

    def _load_db_entity(
        self,
        entity_type: str,
        entity_id: str
    ) -> Optional[Dict[str, Any]]:
        """Load entity data from database."""
        import sqlite3

        table_name = f"{entity_type}s"  # track -> tracks

        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                f"SELECT * FROM {table_name} WHERE id = ?",
                (entity_id,)
            )
            row = cursor.fetchone()
            conn.close()

            if row is None:
                return None

            return dict(row)
        except sqlite3.Error as e:
            logger.warning(f"Failed to load DB {entity_type} {entity_id}: {e}")
            return None

    def _normalize_value(self, value: Any) -> Any:
        """
        Normalize a value for comparison.

        Handles:
        - None vs empty string
        - Boolean normalization
        - Datetime string normalization
        - List/dict serialization differences
        """
        if value is None:
            return None

        # Normalize empty strings to None
        if isinstance(value, str) and value.strip() == "":
            return None

        # Normalize booleans
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            # SQLite stores booleans as 0/1
            if value in (0, 1):
                return bool(value)
            return value

        # Normalize datetime strings (remove timezone suffix variations)
        if isinstance(value, str):
            # Strip timezone info for comparison (Z vs +00:00)
            if value.endswith("Z"):
                value = value[:-1] + "+00:00"
            if "+00:00" in value:
                value = value.replace("+00:00", "")
                if value.endswith(".000000"):
                    value = value[:-7]

        return value


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Main class
    "RoadmapStateVerifier",
    # Data models
    "SyncStatus",
    "Discrepancy",
    "FixResult",
    # Enums
    "IssueType",
    "Severity",
    # Constants
    "DEFAULT_ROADMAP_ROOT",
    "DEFAULT_DB_PATH",
]
