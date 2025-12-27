"""
Task push-down mechanism for submodule integration.

Implements DIRECT WRITE push-down from parent to submodule roadmaps.

Design reference: SUBMODULE_ISOLATION_AND_PUSHDOWN.md

Key principle: Parent C creates actual tasks in submodule A's roadmap.
Submodule A has no knowledge of parent C (isolation principle).
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import ulid
import yaml

from vibey.roadmap.models.cross_repo import (
    ExternalBlockerInfo,
    ExternalBlockerType,
    LinkedTaskPair,
    PushMode,
    PushResult,
)


@dataclass
class TaskDefinition:
    """Definition for a task to be pushed to a submodule."""

    title: str
    description: str
    task_type: str = "development"
    priority: str = "medium"
    complexity: str = "medium"
    estimated_tokens: int = 2000


class TaskPusher:
    """
    Pushes tasks from parent repo to submodule roadmaps.

    Supports three push modes:
    - LINKED: Create in both repos with link tracking
    - PARENT_ONLY: Keep task in parent only
    - SUBMODULE_ONLY: Create only in submodule

    Per design: All cross-repo data lives in PARENT only.
    """

    def __init__(self, parent_repo_path: Optional[Path] = None):
        """
        Initialize TaskPusher.

        Args:
            parent_repo_path: Path to parent repository. Defaults to cwd.
        """
        self.parent_repo_path = Path(parent_repo_path) if parent_repo_path else Path.cwd()
        self.parent_vibey = self.parent_repo_path / ".vibey"
        self.parent_roadmap = self.parent_vibey / "roadmap"
        self.parent_tasks = self.parent_roadmap / "tasks"
        self.config_dir = self.parent_vibey / "config"
        self.linked_tasks_path = self.config_dir / "linked_tasks.yaml"

    def push_task(
        self,
        submodule_path: str,
        task_def: TaskDefinition,
        mode: PushMode = PushMode.LINKED,
        parent_sprint_id: Optional[str] = None,
        parent_track_id: Optional[str] = None,
    ) -> PushResult:
        """
        Push a task to a submodule.

        Args:
            submodule_path: Relative path to submodule directory.
            task_def: Task definition with title, description, etc.
            mode: Push mode (LINKED, PARENT_ONLY, SUBMODULE_ONLY).
            parent_sprint_id: Sprint ID for parent task (required for LINKED/PARENT_ONLY).
            parent_track_id: Track ID for parent task.

        Returns:
            PushResult with created task IDs and status.
        """
        submodule_path = submodule_path.replace("\\", "/").strip("/")
        submodule_abs_path = self.parent_repo_path / submodule_path

        # Validate submodule exists
        if not submodule_abs_path.exists():
            return PushResult(
                success=False,
                push_mode=mode,
                submodule_path=submodule_path,
                error=f"Submodule directory not found: {submodule_path}",
                error_type="not_found",
            )

        # Validate submodule has roadmap
        submodule_roadmap = submodule_abs_path / ".vibey" / "roadmap"
        if not submodule_roadmap.exists():
            return PushResult(
                success=False,
                push_mode=mode,
                submodule_path=submodule_path,
                error=f"Submodule has no roadmap: {submodule_path}",
                error_type="no_roadmap",
            )

        try:
            if mode == PushMode.LINKED:
                return self._push_linked(
                    submodule_path, submodule_abs_path, task_def,
                    parent_sprint_id, parent_track_id
                )
            elif mode == PushMode.PARENT_ONLY:
                return self._push_parent_only(
                    submodule_path, task_def,
                    parent_sprint_id, parent_track_id
                )
            elif mode == PushMode.SUBMODULE_ONLY:
                return self._push_submodule_only(
                    submodule_path, submodule_abs_path, task_def
                )
            else:
                return PushResult(
                    success=False,
                    push_mode=mode,
                    submodule_path=submodule_path,
                    error=f"Unknown push mode: {mode}",
                    error_type="invalid_mode",
                )
        except Exception as e:
            return PushResult(
                success=False,
                push_mode=mode,
                submodule_path=submodule_path,
                error=str(e),
                error_type="exception",
            )

    def _push_linked(
        self,
        submodule_path: str,
        submodule_abs_path: Path,
        task_def: TaskDefinition,
        parent_sprint_id: Optional[str],
        parent_track_id: Optional[str],
    ) -> PushResult:
        """
        LINKED mode: Create tasks in BOTH repos with link tracking.

        - Creates standalone task in submodule (no parent reference)
        - Creates task in parent with ExternalBlockerInfo
        - Records link in linked_tasks.yaml
        """
        now = datetime.now(timezone.utc)

        # Generate ULIDs for both tasks
        submodule_task_id = str(ulid.ULID())
        parent_task_id = str(ulid.ULID())

        # 1. Create task in SUBMODULE (standalone, no parent reference)
        submodule_task = self._create_submodule_task_yaml(
            task_id=submodule_task_id,
            task_def=task_def,
            submodule_abs_path=submodule_abs_path,
        )

        submodule_tasks_dir = submodule_abs_path / ".vibey" / "roadmap" / "tasks"
        submodule_tasks_dir.mkdir(parents=True, exist_ok=True)
        submodule_task_path = submodule_tasks_dir / f"{submodule_task_id}.yaml"

        with open(submodule_task_path, "w") as f:
            yaml.dump({"task": submodule_task}, f, default_flow_style=False, sort_keys=False)

        # 2. Create task in PARENT with ExternalBlockerInfo
        if parent_sprint_id:
            parent_task = self._create_parent_task_yaml(
                task_id=parent_task_id,
                task_def=task_def,
                sprint_id=parent_sprint_id,
                track_id=parent_track_id,
                submodule_path=submodule_path,
                submodule_task_id=submodule_task_id,
            )

            self.parent_tasks.mkdir(parents=True, exist_ok=True)
            parent_task_path = self.parent_tasks / f"{parent_task_id}.yaml"

            with open(parent_task_path, "w") as f:
                yaml.dump({"task": parent_task}, f, default_flow_style=False, sort_keys=False)

        # 3. Record link in linked_tasks.yaml
        link_id = str(ulid.ULID())
        self._record_linked_task_pair(
            link_id=link_id,
            parent_task_id=parent_task_id if parent_sprint_id else None,
            submodule_path=submodule_path,
            submodule_task_id=submodule_task_id,
            push_mode=PushMode.LINKED,
            created=now,
        )

        return PushResult(
            success=True,
            push_mode=PushMode.LINKED,
            parent_task_id=parent_task_id if parent_sprint_id else None,
            submodule_task_id=submodule_task_id,
            link_id=link_id,
            submodule_path=submodule_path,
            pushed_at=now,
        )

    def _push_parent_only(
        self,
        submodule_path: str,
        task_def: TaskDefinition,
        parent_sprint_id: Optional[str],
        parent_track_id: Optional[str],
    ) -> PushResult:
        """
        PARENT_ONLY mode: Create task in parent only.

        - Creates task in parent with ExternalBlockerInfo (resolved_to=None)
        - No task created in submodule
        """
        now = datetime.now(timezone.utc)

        if not parent_sprint_id:
            return PushResult(
                success=False,
                push_mode=PushMode.PARENT_ONLY,
                submodule_path=submodule_path,
                error="parent_sprint_id is required for PARENT_ONLY mode",
                error_type="missing_sprint",
            )

        parent_task_id = str(ulid.ULID())

        # Create parent task with unresolved external blocker
        parent_task = self._create_parent_task_yaml(
            task_id=parent_task_id,
            task_def=task_def,
            sprint_id=parent_sprint_id,
            track_id=parent_track_id,
            submodule_path=submodule_path,
            submodule_task_id=None,  # Unresolved
        )

        self.parent_tasks.mkdir(parents=True, exist_ok=True)
        parent_task_path = self.parent_tasks / f"{parent_task_id}.yaml"

        with open(parent_task_path, "w") as f:
            yaml.dump({"task": parent_task}, f, default_flow_style=False, sort_keys=False)

        return PushResult(
            success=True,
            push_mode=PushMode.PARENT_ONLY,
            parent_task_id=parent_task_id,
            submodule_task_id=None,
            submodule_path=submodule_path,
            pushed_at=now,
        )

    def _push_submodule_only(
        self,
        submodule_path: str,
        submodule_abs_path: Path,
        task_def: TaskDefinition,
    ) -> PushResult:
        """
        SUBMODULE_ONLY mode: Create task in submodule only.

        - Creates standalone task in submodule
        - No parent task created
        """
        now = datetime.now(timezone.utc)

        submodule_task_id = str(ulid.ULID())

        # Create task in submodule (standalone)
        submodule_task = self._create_submodule_task_yaml(
            task_id=submodule_task_id,
            task_def=task_def,
            submodule_abs_path=submodule_abs_path,
        )

        submodule_tasks_dir = submodule_abs_path / ".vibey" / "roadmap" / "tasks"
        submodule_tasks_dir.mkdir(parents=True, exist_ok=True)
        submodule_task_path = submodule_tasks_dir / f"{submodule_task_id}.yaml"

        with open(submodule_task_path, "w") as f:
            yaml.dump({"task": submodule_task}, f, default_flow_style=False, sort_keys=False)

        return PushResult(
            success=True,
            push_mode=PushMode.SUBMODULE_ONLY,
            parent_task_id=None,
            submodule_task_id=submodule_task_id,
            submodule_path=submodule_path,
            pushed_at=now,
        )

    def _create_submodule_task_yaml(
        self,
        task_id: str,
        task_def: TaskDefinition,
        submodule_abs_path: Path,
    ) -> dict:
        """
        Create task YAML data for submodule.

        CRITICAL: No parent references. Task is completely standalone.
        """
        now = datetime.now(timezone.utc).isoformat()

        # Try to read submodule's roadmap ID
        roadmap_id = self._get_submodule_roadmap_id(submodule_abs_path)

        return {
            "id": task_id,
            "sprint_id": None,  # Submodule assigns to its own sprint
            "track_id": None,  # Submodule assigns to its own track
            "roadmap_id": roadmap_id,
            "task_type": task_def.task_type,
            "title": task_def.title,
            "description": task_def.description,
            "status": "not_started",
            "blocked": False,
            "created": now,
            "started": None,
            "completed": None,
            "assigned_agent": None,
            "priority": task_def.priority,
            "phase_label": None,
            "estimated_tokens": task_def.estimated_tokens,
            "actual_tokens": None,
            "complexity": task_def.complexity,
            "gate_info": None,
            "audit_results": None,
            "dependencies": [],
            "blocks": [],
            "blocked_by": [],
            "depends_on": [],
            "depended_on_by": [],
            "deliverables": [],
            "commits": [],
            "metadata": {
                "last_updated": None,
                "token_efficiency": None,
                "duration_hours": None,
            },
        }

    def _create_parent_task_yaml(
        self,
        task_id: str,
        task_def: TaskDefinition,
        sprint_id: str,
        track_id: Optional[str],
        submodule_path: str,
        submodule_task_id: Optional[str],
    ) -> dict:
        """
        Create task YAML data for parent repo.

        Includes ExternalBlockerInfo in blocked_by for cross-repo tracking.
        """
        now = datetime.now(timezone.utc).isoformat()

        # Build blocked_by with external blocker info
        blocked_by = []
        if submodule_path:
            blocker = {
                "blocker_id": f"{submodule_path}:{submodule_task_id or 'unresolved'}",
                "blocker_type": "submodule_task",
                "resolved_to": submodule_task_id,
                "required_status": "completed",
                "submodule_path": submodule_path,
                "current_status": None,
                "is_satisfied": False,
                "last_synced": None,
                "description": f"Depends on task in submodule {submodule_path}",
            }
            blocked_by.append(blocker)

        return {
            "id": task_id,
            "sprint_id": sprint_id,
            "track_id": track_id,
            "roadmap_id": "vibey-framework-v2",  # Parent's roadmap
            "task_type": task_def.task_type,
            "title": f"[Submodule] {task_def.title}",
            "description": task_def.description,
            "status": "not_started",
            "blocked": bool(blocked_by),
            "created": now,
            "started": None,
            "completed": None,
            "assigned_agent": None,
            "priority": task_def.priority,
            "phase_label": None,
            "estimated_tokens": task_def.estimated_tokens,
            "actual_tokens": None,
            "complexity": task_def.complexity,
            "gate_info": None,
            "audit_results": None,
            "dependencies": [],
            "blocks": [],
            "blocked_by": blocked_by,
            "depends_on": [],
            "depended_on_by": [],
            "deliverables": [],
            "commits": [],
            "metadata": {
                "last_updated": None,
                "token_efficiency": None,
                "duration_hours": None,
                "submodule_push_mode": "linked",
                "submodule_path": submodule_path,
            },
        }

    def _get_submodule_roadmap_id(self, submodule_abs_path: Path) -> Optional[str]:
        """Get roadmap ID from submodule's roadmap.yaml."""
        roadmap_yaml = submodule_abs_path / ".vibey" / "roadmap" / "roadmap.yaml"
        if not roadmap_yaml.exists():
            # Try legacy location
            roadmap_yaml = submodule_abs_path / ".vibey" / "roadmap.yaml"

        if not roadmap_yaml.exists():
            return None

        try:
            with open(roadmap_yaml) as f:
                data = yaml.safe_load(f)

            if isinstance(data, dict):
                if "roadmap" in data and isinstance(data["roadmap"], dict):
                    return data["roadmap"].get("id")
                return data.get("id")
        except Exception:
            pass

        return None

    def _record_linked_task_pair(
        self,
        link_id: str,
        parent_task_id: Optional[str],
        submodule_path: str,
        submodule_task_id: str,
        push_mode: PushMode,
        created: datetime,
    ) -> None:
        """Record linked task pair in config file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Load existing links
        links = []
        if self.linked_tasks_path.exists():
            try:
                with open(self.linked_tasks_path) as f:
                    data = yaml.safe_load(f) or {}
                links = data.get("links", [])
            except Exception:
                pass

        # Add new link
        link = {
            "id": link_id,
            "parent_task_id": parent_task_id,
            "submodule_path": submodule_path,
            "submodule_task_id": submodule_task_id,
            "push_mode": push_mode.value,
            "created": created.isoformat(),
        }
        links.append(link)

        # Write back
        with open(self.linked_tasks_path, "w") as f:
            yaml.dump({"links": links}, f, default_flow_style=False, sort_keys=False)

    def link_existing(
        self,
        parent_task_id: str,
        submodule_path: str,
        submodule_task_id: str,
    ) -> LinkedTaskPair:
        """
        Link an existing parent task to an existing submodule task.

        Updates the parent task's blocked_by with ExternalBlockerInfo
        pointing to the submodule task.

        Args:
            parent_task_id: ULID of parent task.
            submodule_path: Path to submodule.
            submodule_task_id: ULID of submodule task.

        Returns:
            LinkedTaskPair representing the link.
        """
        submodule_path = submodule_path.replace("\\", "/").strip("/")
        now = datetime.now(timezone.utc)

        # Load parent task
        parent_task_path = self.parent_tasks / f"{parent_task_id}.yaml"
        if not parent_task_path.exists():
            raise FileNotFoundError(f"Parent task not found: {parent_task_id}")

        with open(parent_task_path) as f:
            data = yaml.safe_load(f)

        task = data.get("task", data)

        # Add external blocker info
        blocked_by = task.get("blocked_by", [])
        blocker = {
            "blocker_id": f"{submodule_path}:{submodule_task_id}",
            "blocker_type": "submodule_task",
            "resolved_to": submodule_task_id,
            "required_status": "completed",
            "submodule_path": submodule_path,
            "current_status": None,
            "is_satisfied": False,
            "last_synced": None,
            "description": f"Linked to task in submodule {submodule_path}",
        }
        blocked_by.append(blocker)
        task["blocked_by"] = blocked_by
        task["blocked"] = True

        # Save parent task
        with open(parent_task_path, "w") as f:
            yaml.dump({"task": task}, f, default_flow_style=False, sort_keys=False)

        # Record link
        link_id = str(ulid.ULID())
        self._record_linked_task_pair(
            link_id=link_id,
            parent_task_id=parent_task_id,
            submodule_path=submodule_path,
            submodule_task_id=submodule_task_id,
            push_mode=PushMode.LINKED,
            created=now,
        )

        return LinkedTaskPair(
            parent_task_id=parent_task_id,
            submodule_path=submodule_path,
            submodule_task_id=submodule_task_id,
            push_mode=PushMode.LINKED,
            created=now,
            id=link_id,
        )

    def unlink(self, parent_task_id: str) -> bool:
        """
        Remove all submodule links from a parent task.

        Does NOT delete submodule tasks (isolation preserved).

        Args:
            parent_task_id: ULID of parent task.

        Returns:
            True if links were removed, False otherwise.
        """
        parent_task_path = self.parent_tasks / f"{parent_task_id}.yaml"
        if not parent_task_path.exists():
            return False

        with open(parent_task_path) as f:
            data = yaml.safe_load(f)

        task = data.get("task", data)

        # Remove submodule blockers
        blocked_by = task.get("blocked_by", [])
        original_count = len(blocked_by)

        blocked_by = [
            b for b in blocked_by
            if b.get("blocker_type") != "submodule_task"
        ]
        task["blocked_by"] = blocked_by
        task["blocked"] = bool(blocked_by)

        # Save parent task
        with open(parent_task_path, "w") as f:
            yaml.dump({"task": task}, f, default_flow_style=False, sort_keys=False)

        # Remove from linked_tasks.yaml
        if self.linked_tasks_path.exists():
            try:
                with open(self.linked_tasks_path) as f:
                    data = yaml.safe_load(f) or {}
                links = data.get("links", [])
                links = [l for l in links if l.get("parent_task_id") != parent_task_id]
                with open(self.linked_tasks_path, "w") as f:
                    yaml.dump({"links": links}, f, default_flow_style=False, sort_keys=False)
            except Exception:
                pass

        return len(blocked_by) < original_count

    def get_linked_tasks(self, parent_task_id: str) -> list[LinkedTaskPair]:
        """
        Get all submodule tasks linked from a parent task.

        Args:
            parent_task_id: ULID of parent task.

        Returns:
            List of LinkedTaskPair objects.
        """
        if not self.linked_tasks_path.exists():
            return []

        try:
            with open(self.linked_tasks_path) as f:
                data = yaml.safe_load(f) or {}
            links = data.get("links", [])

            result = []
            for link in links:
                if link.get("parent_task_id") == parent_task_id:
                    result.append(LinkedTaskPair(
                        parent_task_id=link["parent_task_id"],
                        submodule_path=link["submodule_path"],
                        submodule_task_id=link["submodule_task_id"],
                        push_mode=PushMode(link.get("push_mode", "linked")),
                        created=self._parse_datetime(link.get("created")),
                        id=link.get("id"),
                    ))
            return result
        except Exception:
            return []

    def _parse_datetime(self, value: Optional[str]) -> Optional[datetime]:
        """Parse ISO format datetime string."""
        if not value:
            return None
        try:
            if value.endswith("Z"):
                value = value[:-1] + "+00:00"
            return datetime.fromisoformat(value)
        except Exception:
            return None
