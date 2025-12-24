"""
TaskSelector - Find executable tasks for Implementation Mode.

This module provides the TaskSelector class for finding the next task
to execute in autonomous implementation mode.

Selection Criteria (in order):
1. status == 'not_started' (planned tasks ready for work)
2. blocked == False (no unresolved dependencies)
3. All depends_on tasks are completed
4. is_planned == True (planning criteria met)
5. Ordered by priority (critical > high > medium > low)
6. Ordered by creation date (oldest first)

Usage:
    from vibey.services.implementation import TaskSelector
    from pathlib import Path

    # Initialize with roadmap root
    selector = TaskSelector(roadmap_root=Path(".vibey/roadmap"))

    # Get next executable task
    next_task = selector.get_next_task()

    # Get next task in specific track
    next_task = selector.get_next_task(track_id="01KC...")

    # Get all currently executable tasks
    all_executable = selector.get_all_executable()

    # Count remaining tasks
    remaining = selector.count_remaining()

Design Reference:
- Implementation Mode Track Sprint 1
- ADR-0002: Flat Directory Structure
"""

import logging
import sqlite3
from pathlib import Path
from typing import List, Optional

from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket
from vibey.roadmap.models.ticket.enums import Priority
from vibey.roadmap.criteria.planned import check_planned_status
from vibey.roadmap.database.connection import get_connection

logger = logging.getLogger(__name__)


# Priority ordering for sorting (lower index = higher priority)
PRIORITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    None: 4,  # No priority set defaults to lowest
}


class TaskSelector:
    """
    Find the next executable task based on status, dependencies, and priority.

    TaskSelector queries the SQLite database for tasks that are ready for
    execution, applying filters for blocked status, dependency satisfaction,
    and planning completion.

    Attributes:
        root: Path to the roadmap directory (.vibey/roadmap)
        db_path: Path to the SQLite database

    Example:
        >>> selector = TaskSelector(Path(".vibey/roadmap"))
        >>> next_task = selector.get_next_task()
        >>> if next_task:
        ...     print(f"Next task: {next_task.name}")
        ...     # Start the task
        ...     next_task.start()
    """

    def __init__(self, roadmap_root: Path):
        """
        Initialize TaskSelector with roadmap root directory.

        Args:
            roadmap_root: Path to .vibey/roadmap directory containing
                         the SQLite database and YAML files.

        Raises:
            FileNotFoundError: If roadmap.db doesn't exist
        """
        self.root = roadmap_root
        self.db_path = roadmap_root / "roadmap.db"

        if not self.db_path.exists():
            # Try parent directory (if roadmap_root is .vibey, db is in .vibey)
            alt_path = roadmap_root.parent / "roadmap.db"
            if alt_path.exists():
                self.db_path = alt_path
            else:
                raise FileNotFoundError(
                    f"Database not found at {self.db_path} or {alt_path}"
                )

        logger.debug(f"TaskSelector initialized with db: {self.db_path}")

    def get_next_task(
        self,
        track_id: Optional[str] = None,
        sprint_id: Optional[str] = None,
    ) -> Optional[HierarchicalTicket]:
        """
        Find the next planned and unblocked task.

        Selection criteria applied in order:
        1. status == 'not_started'
        2. blocked == False
        3. All dependencies are completed (no blocking entries)
        4. is_planned == True (planning criteria met)
        5. Ordered by priority (critical > high > medium > low)
        6. Ordered by creation date (oldest first within same priority)

        Args:
            track_id: Optional track ULID to filter by
            sprint_id: Optional sprint ULID to filter by

        Returns:
            HierarchicalTicket for the next executable task, or None
            if no tasks are ready for execution.

        Example:
            >>> selector = TaskSelector(Path(".vibey/roadmap"))
            >>> task = selector.get_next_task()
            >>> task = selector.get_next_task(track_id="01KC...")
        """
        candidates = self._query_candidate_tasks(
            track_id=track_id,
            sprint_id=sprint_id,
            limit=100,  # Get more to filter for planned status
        )

        for task_data in candidates:
            # Check if task is planned (planning criteria met)
            if self._is_task_planned(task_data["id"]):
                # Convert to HierarchicalTicket
                return self._load_task_as_ticket(task_data)

        return None

    def get_all_executable(
        self,
        track_id: Optional[str] = None,
        sprint_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[HierarchicalTicket]:
        """
        Get all currently executable tasks.

        Returns all tasks that meet the execution criteria:
        - status == 'not_started'
        - blocked == False
        - No incomplete dependencies
        - is_planned == True

        Tasks are returned ordered by priority then creation date.

        Args:
            track_id: Optional track ULID to filter by
            sprint_id: Optional sprint ULID to filter by
            limit: Maximum number of tasks to return (default 100)

        Returns:
            List of HierarchicalTicket objects for executable tasks.

        Example:
            >>> selector = TaskSelector(Path(".vibey/roadmap"))
            >>> tasks = selector.get_all_executable()
            >>> for task in tasks:
            ...     print(f"{task.id}: {task.name}")
        """
        candidates = self._query_candidate_tasks(
            track_id=track_id,
            sprint_id=sprint_id,
            limit=limit * 2,  # Get more to account for filtering
        )

        executable = []
        for task_data in candidates:
            if len(executable) >= limit:
                break
            if self._is_task_planned(task_data["id"]):
                ticket = self._load_task_as_ticket(task_data)
                executable.append(ticket)

        return executable

    def count_remaining(
        self,
        track_id: Optional[str] = None,
        sprint_id: Optional[str] = None,
    ) -> int:
        """
        Count tasks that could be executed.

        Counts tasks meeting basic execution criteria (not_started,
        not blocked, no incomplete dependencies). Does not check
        is_planned status for performance reasons.

        For accurate count including planned status, use:
            len(selector.get_all_executable())

        Args:
            track_id: Optional track ULID to filter by
            sprint_id: Optional sprint ULID to filter by

        Returns:
            Count of potentially executable tasks.

        Example:
            >>> selector = TaskSelector(Path(".vibey/roadmap"))
            >>> remaining = selector.count_remaining()
            >>> print(f"{remaining} tasks remaining")
        """
        candidates = self._query_candidate_tasks(
            track_id=track_id,
            sprint_id=sprint_id,
            limit=10000,  # High limit for counting
            count_only=True,
        )
        return len(candidates)

    def _query_candidate_tasks(
        self,
        track_id: Optional[str] = None,
        sprint_id: Optional[str] = None,
        limit: int = 100,
        count_only: bool = False,
    ) -> List[dict]:
        """
        Query database for candidate tasks.

        Finds tasks that are:
        - status = 'not_started'
        - blocked = 0 (False)
        - Have no incomplete dependencies (no blocking entries in entity_blocked_by)

        Args:
            track_id: Filter by track
            sprint_id: Filter by sprint
            limit: Max results
            count_only: If True, don't order (faster for counting)

        Returns:
            List of task dictionaries from database.
        """
        conn = get_connection(db_path=self.db_path)

        # Build query
        # Select tasks that are not_started, not blocked, and have no
        # incomplete dependencies blocking them
        query = """
            SELECT
                t.id,
                t.title,
                t.description,
                t.sprint_id,
                t.track_id,
                t.roadmap_id,
                t.task_type,
                t.status,
                t.blocked,
                t.created,
                t.started,
                t.completed,
                t.priority,
                t.estimated_tokens,
                t.complexity
            FROM tasks t
            WHERE t.status = 'not_started'
              AND t.blocked = 0
              AND NOT EXISTS (
                  SELECT 1 FROM entity_blocked_by eb
                  JOIN tasks blocker ON blocker.id = eb.blocker_id
                    AND eb.blocker_type = 'task'
                  WHERE eb.blocked_type = 'task'
                    AND eb.blocked_id = t.id
                    AND blocker.status != 'completed'
              )
        """

        params = []

        if track_id:
            query += " AND t.track_id = ?"
            params.append(track_id)

        if sprint_id:
            query += " AND t.sprint_id = ?"
            params.append(sprint_id)

        if not count_only:
            # Order by priority (using CASE for custom ordering)
            # then by creation date (oldest first)
            query += """
                ORDER BY
                    CASE t.priority
                        WHEN 'critical' THEN 0
                        WHEN 'high' THEN 1
                        WHEN 'medium' THEN 2
                        WHEN 'low' THEN 3
                        ELSE 4
                    END ASC,
                    t.created ASC
            """

        query += " LIMIT ?"
        params.append(limit)

        try:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            # Convert Row objects to dicts
            return [dict(row) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Database query error: {e}")
            return []

    def _is_task_planned(self, task_id: str) -> bool:
        """
        Check if a task is planned (planning criteria met).

        Uses the planned criterion system to verify:
        - YAML file exists
        - Context files exist (if required)
        - Other planning criteria

        Args:
            task_id: Task ULID to check

        Returns:
            True if task meets all required planning criteria.
        """
        try:
            is_planned, _ = check_planned_status(
                ticket_id=task_id,
                ticket_type="task",
                roadmap_root=self.root,
            )
            return is_planned
        except Exception as e:
            logger.warning(f"Failed to check planned status for {task_id}: {e}")
            # Default to True if check fails (assume planned)
            return True

    def _load_task_as_ticket(self, task_data: dict) -> HierarchicalTicket:
        """
        Load a task from database row as HierarchicalTicket.

        Converts raw database row to a full HierarchicalTicket object
        that can be used for operations.

        Args:
            task_data: Dictionary from database query

        Returns:
            HierarchicalTicket instance
        """
        from vibey.roadmap.serialization.yaml_loader import load_task_ticket

        # Load from YAML file for complete data
        task_path = self.root / "tasks" / f"{task_data['id']}.yaml"

        if task_path.exists():
            try:
                return load_task_ticket(task_path)
            except Exception as e:
                logger.warning(f"Failed to load task from YAML: {e}")

        # Fallback: construct from database data
        from datetime import datetime, timezone
        from vibey.roadmap.models.ticket.enums import TicketStatus

        # Parse timestamps
        created_at = None
        if task_data.get("created"):
            try:
                created_at = datetime.fromisoformat(
                    task_data["created"].replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                created_at = datetime.now(timezone.utc)

        return HierarchicalTicket(
            id=task_data["id"],
            name=task_data.get("title", ""),
            status=TicketStatus.NOT_STARTED,
            parent_ref=task_data.get("sprint_id"),
            children=[],
            blocked=bool(task_data.get("blocked", False)),
            created_at=created_at,
        )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "TaskSelector",
]
