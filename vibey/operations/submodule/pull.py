"""
Progress pull-up mechanism for submodule integration.

Implements PARENT-INITIATED aggregation from submodule roadmaps.

Design reference: SUBMODULE_ISOLATION_AND_PUSHDOWN.md

Key principle: Parent C reads submodule A's roadmap directly.
Submodule A is a passive data source (no outgoing/ directory).
"""

import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

import yaml

from vibey.roadmap.models.submodule import (
    AggregatedProgress,
    BlockerSeverity,
    CollectionMethod,
    SubmoduleBlocker,
    SubmoduleProgress,
    SubmoduleReference,
    SyncStatus,
)
from vibey.roadmap.models.cross_repo import SyncResult
from vibey.operations.submodule.discovery import SubmoduleDiscovery


class ProgressAggregator:
    """
    Aggregates progress from submodule roadmaps.

    Implements parent-initiated pull model:
    - Parent reads submodule data directly
    - Submodule remains passive (isolation preserved)
    - All aggregation state stored in parent
    """

    def __init__(self, parent_repo_path: Optional[Path] = None):
        """
        Initialize ProgressAggregator.

        Args:
            parent_repo_path: Path to parent repository. Defaults to cwd.
        """
        self.parent_repo_path = Path(parent_repo_path) if parent_repo_path else Path.cwd()
        self.parent_vibey = self.parent_repo_path / ".vibey"
        self.parent_roadmap = self.parent_vibey / "roadmap"
        self.parent_tasks = self.parent_roadmap / "tasks"
        self.config_dir = self.parent_vibey / "config"
        self.discovery = SubmoduleDiscovery(self.parent_repo_path)

    def aggregate_all(self) -> AggregatedProgress:
        """
        Aggregate progress from all registered submodules.

        Reads submodule registry and collects progress from each
        submodule with aggregate=True.

        Returns:
            AggregatedProgress with combined metrics from all submodules.
        """
        result = AggregatedProgress()

        # Get registered submodules
        submodules = self.discovery.get_vibey_submodules()

        for submodule in submodules:
            if not submodule.aggregate:
                continue

            try:
                progress = self.aggregate_submodule(submodule.path)
                if progress:
                    result.submodule_progress.append(progress)

                    # Update sync status
                    submodule.last_synced = datetime.now(timezone.utc)
                    submodule.sync_status = SyncStatus.SYNCED
                    result.submodules_synced += 1
            except Exception as e:
                # Mark as error but continue
                submodule.sync_status = SyncStatus.ERROR
                result.submodules_error += 1

        # Compute aggregated totals
        result.aggregate()

        return result

    def aggregate_submodule(
        self,
        path: str,
        track_filter: Optional[list[str]] = None,
    ) -> Optional[SubmoduleProgress]:
        """
        Aggregate progress from a single submodule.

        Reads submodule's roadmap database or YAML files and computes
        progress metrics.

        Args:
            path: Relative path to submodule.
            track_filter: Optional list of track IDs to include. Empty = all.

        Returns:
            SubmoduleProgress with computed metrics, or None if failed.
        """
        path = path.replace("\\", "/").strip("/")
        submodule_abs = self.parent_repo_path / path

        if not submodule_abs.exists():
            return None

        submodule_roadmap = submodule_abs / ".vibey" / "roadmap"
        if not submodule_roadmap.exists():
            return None

        # Get submodule's roadmap ID
        roadmap_id = self._get_roadmap_id(submodule_abs)

        # Try to read from SQLite database first (faster)
        db_path = submodule_roadmap / "roadmap.db"
        if db_path.exists():
            return self._aggregate_from_db(path, db_path, roadmap_id, track_filter)

        # Fall back to YAML files
        return self._aggregate_from_yaml(path, submodule_roadmap, roadmap_id, track_filter)

    def _aggregate_from_db(
        self,
        path: str,
        db_path: Path,
        roadmap_id: Optional[str],
        track_filter: Optional[list[str]],
    ) -> Optional[SubmoduleProgress]:
        """Aggregate progress from submodule's SQLite database."""
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row

            # Build track filter clause
            track_clause = ""
            if track_filter:
                placeholders = ",".join("?" * len(track_filter))
                track_clause = f" AND track_id IN ({placeholders})"

            # Count tracks
            cursor = conn.execute(f"""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status IN ('completed', 'production_ready') THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress
                FROM tracks
                WHERE 1=1 {track_clause.replace('track_id', 'id') if track_clause else ''}
            """, track_filter or [])
            track_row = cursor.fetchone()

            # Count sprints
            cursor = conn.execute(f"""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status IN ('completed', 'production_ready') THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress
                FROM sprints
                WHERE 1=1 {track_clause}
            """, track_filter or [])
            sprint_row = cursor.fetchone()

            # Count tasks
            cursor = conn.execute(f"""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress
                FROM tasks
                WHERE 1=1 {track_clause}
            """, track_filter or [])
            task_row = cursor.fetchone()

            conn.close()

            progress = SubmoduleProgress(
                submodule_path=path,
                roadmap_id=roadmap_id or "unknown",
                tracks_total=track_row["total"] or 0,
                tracks_completed=track_row["completed"] or 0,
                tracks_in_progress=track_row["in_progress"] or 0,
                sprints_total=sprint_row["total"] or 0,
                sprints_completed=sprint_row["completed"] or 0,
                sprints_in_progress=sprint_row["in_progress"] or 0,
                tasks_total=task_row["total"] or 0,
                tasks_completed=task_row["completed"] or 0,
                tasks_in_progress=task_row["in_progress"] or 0,
                collected_at=datetime.now(timezone.utc),
                collection_method=CollectionMethod.ON_DEMAND,
            )
            progress.calculate_completion()
            return progress

        except Exception as e:
            return None

    def _aggregate_from_yaml(
        self,
        path: str,
        roadmap_dir: Path,
        roadmap_id: Optional[str],
        track_filter: Optional[list[str]],
    ) -> Optional[SubmoduleProgress]:
        """Aggregate progress from submodule's YAML files."""
        try:
            tracks_dir = roadmap_dir / "tracks"
            sprints_dir = roadmap_dir / "sprints"
            tasks_dir = roadmap_dir / "tasks"

            # Count tracks
            tracks_total = 0
            tracks_completed = 0
            tracks_in_progress = 0

            if tracks_dir.exists():
                for track_file in tracks_dir.glob("*.yaml"):
                    with open(track_file) as f:
                        data = yaml.safe_load(f) or {}
                    track = data.get("track", data)
                    track_id = track.get("id")

                    if track_filter and track_id not in track_filter:
                        continue

                    tracks_total += 1
                    status = track.get("status", "not_started")
                    if status in ("completed", "production_ready"):
                        tracks_completed += 1
                    elif status == "in_progress":
                        tracks_in_progress += 1

            # Count sprints
            sprints_total = 0
            sprints_completed = 0
            sprints_in_progress = 0

            if sprints_dir.exists():
                for sprint_file in sprints_dir.glob("*.yaml"):
                    with open(sprint_file) as f:
                        data = yaml.safe_load(f) or {}
                    sprint = data.get("sprint", data)

                    if track_filter:
                        sprint_track = sprint.get("track_id")
                        if sprint_track not in track_filter:
                            continue

                    sprints_total += 1
                    status = sprint.get("status", "not_started")
                    if status in ("completed", "production_ready"):
                        sprints_completed += 1
                    elif status == "in_progress":
                        sprints_in_progress += 1

            # Count tasks
            tasks_total = 0
            tasks_completed = 0
            tasks_in_progress = 0

            if tasks_dir.exists():
                for task_file in tasks_dir.glob("*.yaml"):
                    with open(task_file) as f:
                        data = yaml.safe_load(f) or {}
                    task = data.get("task", data)

                    if track_filter:
                        task_track = task.get("track_id")
                        if task_track not in track_filter:
                            continue

                    tasks_total += 1
                    status = task.get("status", "not_started")
                    if status == "completed":
                        tasks_completed += 1
                    elif status == "in_progress":
                        tasks_in_progress += 1

            progress = SubmoduleProgress(
                submodule_path=path,
                roadmap_id=roadmap_id or "unknown",
                tracks_total=tracks_total,
                tracks_completed=tracks_completed,
                tracks_in_progress=tracks_in_progress,
                sprints_total=sprints_total,
                sprints_completed=sprints_completed,
                sprints_in_progress=sprints_in_progress,
                tasks_total=tasks_total,
                tasks_completed=tasks_completed,
                tasks_in_progress=tasks_in_progress,
                collected_at=datetime.now(timezone.utc),
                collection_method=CollectionMethod.ON_DEMAND,
            )
            progress.calculate_completion()
            return progress

        except Exception:
            return None

    def sync_blocked_by_status(self) -> SyncResult:
        """
        Sync status of external blockers from submodules.

        Finds parent tasks with ExternalBlockerInfo and updates their
        current_status from the linked submodule tasks.

        Returns:
            SyncResult with counts of synced and resolved blockers.
        """
        start_time = datetime.now(timezone.utc)
        tasks_synced = 0
        blockers_updated = 0
        blockers_resolved = 0

        if not self.parent_tasks.exists():
            return SyncResult(
                success=True,
                submodule_path="*",
                tasks_synced=0,
                synced_at=start_time,
            )

        try:
            for task_file in self.parent_tasks.glob("*.yaml"):
                with open(task_file) as f:
                    data = yaml.safe_load(f) or {}

                task = data.get("task", data)
                blocked_by = task.get("blocked_by", [])

                if not blocked_by:
                    continue

                modified = False
                for blocker in blocked_by:
                    if blocker.get("blocker_type") != "submodule_task":
                        continue

                    resolved_to = blocker.get("resolved_to")
                    submodule_path = blocker.get("submodule_path")

                    if not resolved_to or not submodule_path:
                        continue

                    # Read submodule task status
                    submodule_status = self._get_submodule_task_status(
                        submodule_path, resolved_to
                    )

                    if submodule_status:
                        old_status = blocker.get("current_status")
                        blocker["current_status"] = submodule_status
                        blocker["last_synced"] = datetime.now(timezone.utc).isoformat()

                        # Check if satisfied
                        required = blocker.get("required_status", "completed")
                        was_satisfied = blocker.get("is_satisfied", False)
                        blocker["is_satisfied"] = self._status_satisfies(
                            submodule_status, required
                        )

                        if old_status != submodule_status:
                            blockers_updated += 1
                            modified = True

                        if blocker["is_satisfied"] and not was_satisfied:
                            blockers_resolved += 1

                if modified:
                    # Update blocked flag
                    any_unsatisfied = any(
                        not b.get("is_satisfied", False)
                        for b in blocked_by
                        if b.get("blocker_type") == "submodule_task"
                    )
                    task["blocked"] = any_unsatisfied
                    task["blocked_by"] = blocked_by

                    with open(task_file, "w") as f:
                        yaml.dump({"task": task}, f, default_flow_style=False, sort_keys=False)

                    tasks_synced += 1

            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            return SyncResult(
                success=True,
                submodule_path="*",
                tasks_synced=tasks_synced,
                blockers_updated=blockers_updated,
                blockers_resolved=blockers_resolved,
                synced_at=end_time,
                duration_ms=duration_ms,
            )

        except Exception as e:
            return SyncResult(
                success=False,
                submodule_path="*",
                error=str(e),
            )

    def _get_submodule_task_status(
        self,
        submodule_path: str,
        task_id: str,
    ) -> Optional[str]:
        """Get status of a task in a submodule."""
        submodule_abs = self.parent_repo_path / submodule_path
        task_file = submodule_abs / ".vibey" / "roadmap" / "tasks" / f"{task_id}.yaml"

        if not task_file.exists():
            return None

        try:
            with open(task_file) as f:
                data = yaml.safe_load(f) or {}
            task = data.get("task", data)
            return task.get("status")
        except Exception:
            return None

    def _status_satisfies(self, current: str, required: str) -> bool:
        """Check if current status satisfies required status."""
        status_order = [
            "not_started", "in_progress", "paused",
            "completion_gate_check", "completed",
            "production_gate_check", "production_ready", "deployed"
        ]

        try:
            current_idx = status_order.index(current)
            required_idx = status_order.index(required)
            return current_idx >= required_idx
        except ValueError:
            return current == required

    def get_blockers(
        self,
        severity_filter: Optional[BlockerSeverity] = None,
    ) -> list[SubmoduleBlocker]:
        """
        Aggregate blockers from all submodules.

        Finds tasks with blocked=True in submodules and converts them
        to SubmoduleBlocker objects for parent visibility.

        Args:
            severity_filter: Optional severity to filter by.

        Returns:
            List of SubmoduleBlocker sorted by severity (critical first).
        """
        blockers = []
        submodules = self.discovery.get_vibey_submodules()

        for submodule in submodules:
            if not submodule.aggregate:
                continue

            submodule_blockers = self._get_submodule_blockers(submodule.path)
            blockers.extend(submodule_blockers)

        # Filter by severity if specified
        if severity_filter:
            blockers = [b for b in blockers if b.severity == severity_filter]

        # Sort by severity (critical first)
        severity_order = {
            BlockerSeverity.CRITICAL: 0,
            BlockerSeverity.HIGH: 1,
            BlockerSeverity.MEDIUM: 2,
            BlockerSeverity.LOW: 3,
        }
        blockers.sort(key=lambda b: severity_order.get(b.severity, 99))

        return blockers

    def _get_submodule_blockers(self, path: str) -> list[SubmoduleBlocker]:
        """Get blocked tasks from a submodule as blockers."""
        blockers = []
        submodule_abs = self.parent_repo_path / path
        tasks_dir = submodule_abs / ".vibey" / "roadmap" / "tasks"

        if not tasks_dir.exists():
            return blockers

        try:
            for task_file in tasks_dir.glob("*.yaml"):
                with open(task_file) as f:
                    data = yaml.safe_load(f) or {}
                task = data.get("task", data)

                if not task.get("blocked", False):
                    continue

                blocker = SubmoduleBlocker(
                    submodule_path=path,
                    blocker_id=task.get("id", task_file.stem),
                    title=task.get("title", "Unknown"),
                    severity=self._infer_severity(task),
                    description=task.get("description"),
                    detected_at=datetime.now(timezone.utc),
                )
                blockers.append(blocker)
        except Exception:
            pass

        return blockers

    def _infer_severity(self, task: dict) -> BlockerSeverity:
        """Infer blocker severity from task priority."""
        priority = task.get("priority", "medium")
        if priority == "critical":
            return BlockerSeverity.CRITICAL
        elif priority == "high":
            return BlockerSeverity.HIGH
        elif priority == "low":
            return BlockerSeverity.LOW
        return BlockerSeverity.MEDIUM

    def get_stale_submodules(
        self,
        threshold_minutes: int = 60,
    ) -> list[SubmoduleReference]:
        """
        Find submodules not synced within threshold.

        Args:
            threshold_minutes: Minutes since last sync to consider stale.

        Returns:
            List of stale SubmoduleReference objects.
        """
        stale = []
        threshold = datetime.now(timezone.utc) - timedelta(minutes=threshold_minutes)
        submodules = self.discovery.get_vibey_submodules()

        for submodule in submodules:
            if submodule.last_synced is None:
                stale.append(submodule)
            elif submodule.last_synced < threshold:
                stale.append(submodule)

        return stale

    def _get_roadmap_id(self, submodule_abs: Path) -> Optional[str]:
        """Get roadmap ID from submodule's roadmap.yaml."""
        roadmap_yaml = submodule_abs / ".vibey" / "roadmap" / "roadmap.yaml"
        if not roadmap_yaml.exists():
            roadmap_yaml = submodule_abs / ".vibey" / "roadmap.yaml"

        if not roadmap_yaml.exists():
            return None

        try:
            with open(roadmap_yaml) as f:
                data = yaml.safe_load(f)
            if isinstance(data, dict):
                if "roadmap" in data:
                    return data["roadmap"].get("id")
                return data.get("id")
        except Exception:
            pass

        return None
