"""
Standards Resolution Engine.

Resolves effective standards for roadmap items through hierarchical inheritance:
roadmap → track → sprint → task

The resolution follows these rules:
1. Standards cascade down the hierarchy (children inherit from parents)
2. More specific standards override less specific ones (by ID)
3. Per-item overrides can bypass standards
4. Disabled standards are excluded from resolution
"""

from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime, timezone
import yaml

from ..models import Standard, Roadmap, Track, Sprint, Task
from ..serialization import load_roadmap, load_track, load_sprint, load_tasks
from ...cli.roadmap_lib.filesystem import FileSystemManager


def _is_ulid(item_id: str) -> bool:
    """Check if item_id is a ULID (26 alphanumeric chars starting with 01)."""
    return len(item_id) == 26 and item_id.isalnum() and item_id.startswith('01')


class ResolvedStandard:
    """
    A standard with resolution metadata.

    Tracks where the standard came from and whether it's been overridden.
    """

    def __init__(
        self,
        standard: Standard,
        source_level: str,  # "roadmap", "track", "sprint"
        source_id: str,  # ID of the object that defined it
        is_overridden: bool = False,
        override_reason: Optional[str] = None,
    ):
        self.standard = standard
        self.source_level = source_level
        self.source_id = source_id
        self.is_overridden = is_overridden
        self.override_reason = override_reason

    def __repr__(self):
        override_str = f" (overridden: {self.override_reason})" if self.is_overridden else ""
        return f"<ResolvedStandard {self.standard.id} from {self.source_level}{override_str}>"


class StandardsResolver:
    """
    Resolves effective standards for roadmap items.

    Implements hierarchical inheritance with deduplication and override handling.

    Examples:
        # Resolve standards for a task
        resolver = StandardsResolver(root_dir)
        standards = resolver.resolve_for_task("backend-1-task-001")

        # Resolve standards for a sprint
        standards = resolver.resolve_for_sprint("backend-1")

        # Check if a standard applies
        if resolver.has_standard("commit-required", "backend-1-task-001"):
            # Standard applies to this task
            pass
    """

    def __init__(self, root_dir: Path):
        """
        Initialize resolver.

        Args:
            root_dir: Root directory containing .vibey/
        """
        self.root_dir = Path(root_dir)
        self.fs = FileSystemManager(root_dir)

        # Cache loaded objects to avoid repeated file I/O
        self._roadmap_cache: Optional[Roadmap] = None
        self._track_cache: Dict[str, Track] = {}
        self._sprint_cache: Dict[str, Sprint] = {}

    def _get_roadmap(self) -> Roadmap:
        """Get cached roadmap or load it."""
        if self._roadmap_cache is None:
            roadmap_path = self.fs.get_roadmap_path()
            self._roadmap_cache = load_roadmap(roadmap_path)
        return self._roadmap_cache

    def _get_track(self, track_id: str) -> Track:
        """Get cached track or load it."""
        if track_id not in self._track_cache:
            track_path = self.fs.get_track_path(track_id)
            self._track_cache[track_id] = load_track(track_path)
        return self._track_cache[track_id]

    def _get_sprint(self, sprint_id: str) -> Sprint:
        """Get cached sprint or load it."""
        if sprint_id not in self._sprint_cache:
            sprint_path = self.fs.get_sprint_path(sprint_id)
            self._sprint_cache[sprint_id] = load_sprint(sprint_path)
        return self._sprint_cache[sprint_id]

    def _deduplicate_standards(
        self,
        standards_by_level: List[tuple[str, str, List[Standard]]]
    ) -> List[ResolvedStandard]:
        """
        Deduplicate standards by ID, keeping most specific (last in list).

        Args:
            standards_by_level: List of (level, id, standards) tuples
                in order from least specific to most specific

        Returns:
            List of ResolvedStandard objects (deduplicated)
        """
        # Build dict: standard_id -> (level, source_id, standard)
        # Later entries override earlier ones (most specific wins)
        standards_dict: Dict[str, tuple[str, str, Standard]] = {}

        for level, source_id, standards in standards_by_level:
            for standard in standards:
                if standard.is_active():
                    standards_dict[standard.id] = (level, source_id, standard)

        # Convert to ResolvedStandard objects
        resolved = []
        for standard_id, (level, source_id, standard) in standards_dict.items():
            resolved.append(ResolvedStandard(
                standard=standard,
                source_level=level,
                source_id=source_id,
            ))

        return resolved

    def _apply_overrides(
        self,
        resolved_standards: List[ResolvedStandard],
        target_id: str
    ) -> List[ResolvedStandard]:
        """
        Apply overrides for a specific target.

        Marks standards as overridden if they have an active override
        for the given target_id.

        Args:
            resolved_standards: Standards to check for overrides
            target_id: ID of the item to check overrides for

        Returns:
            List of ResolvedStandard objects with override status updated
        """
        for resolved in resolved_standards:
            override = resolved.standard.get_override_for(target_id)
            if override:
                resolved.is_overridden = True
                resolved.override_reason = override.reason

        return resolved_standards

    def resolve_for_task(self, task_id: str) -> List[ResolvedStandard]:
        """
        Resolve effective standards for a task.

        Inherits from: roadmap → track → sprint

        Args:
            task_id: Task ID (e.g., "backend-1-task-001" or ULID like "01KC...")

        Returns:
            List of ResolvedStandard objects that apply to this task

        Raises:
            ValueError: If task ID is invalid or task not found
        """
        # Check if ULID format
        if _is_ulid(task_id):
            # Load task directly from tasks/ directory
            task_path = self.root_dir / ".vibey" / "roadmap" / "tasks" / f"{task_id}.yaml"
            if not task_path.exists():
                raise ValueError(f"Task file not found: {task_path}")
            with open(task_path) as f:
                task_data = yaml.safe_load(f)
            sprint_id = task_data.get('task', {}).get('sprint_id')
            if not sprint_id:
                raise ValueError(f"Task {task_id} has no sprint_id")
        else:
            # Parse legacy task ID to get sprint
            parts = task_id.split('-')
            if len(parts) < 4 or parts[-2] != 'task':
                raise ValueError(f"Invalid task ID format: {task_id}")
            # Extract sprint_id (e.g., "backend-1" from "backend-1-task-001")
            sprint_id = '-'.join(parts[:-2])

        # Load sprint to get track_id
        sprint = self._get_sprint(sprint_id)
        track_id = sprint.track_id

        # Load track
        track = self._get_track(track_id)

        # Load roadmap
        roadmap = self._get_roadmap()

        # Collect standards from all levels (least specific to most specific)
        standards_by_level = [
            ("roadmap", roadmap.id, roadmap.standards),
            ("track", track_id, track.standards),
            ("sprint", sprint_id, sprint.standards),
        ]

        # Deduplicate (most specific wins)
        resolved = self._deduplicate_standards(standards_by_level)

        # Apply overrides for this task
        resolved = self._apply_overrides(resolved, task_id)

        return resolved

    def resolve_for_sprint(self, sprint_id: str) -> List[ResolvedStandard]:
        """
        Resolve effective standards for a sprint.

        Inherits from: roadmap → track

        Args:
            sprint_id: Sprint ID (e.g., "backend-1")

        Returns:
            List of ResolvedStandard objects that apply to this sprint
        """
        # Load sprint
        sprint = self._get_sprint(sprint_id)
        track_id = sprint.track_id

        # Load track
        track = self._get_track(track_id)

        # Load roadmap
        roadmap = self._get_roadmap()

        # Collect standards from all levels (least specific to most specific)
        standards_by_level = [
            ("roadmap", roadmap.id, roadmap.standards),
            ("track", track_id, track.standards),
            ("sprint", sprint_id, sprint.standards),
        ]

        # Deduplicate (most specific wins)
        resolved = self._deduplicate_standards(standards_by_level)

        # Apply overrides for this sprint
        resolved = self._apply_overrides(resolved, sprint_id)

        return resolved

    def resolve_for_track(self, track_id: str) -> List[ResolvedStandard]:
        """
        Resolve effective standards for a track.

        Inherits from: roadmap

        Args:
            track_id: Track ID (e.g., "backend")

        Returns:
            List of ResolvedStandard objects that apply to this track
        """
        # Load track
        track = self._get_track(track_id)

        # Load roadmap
        roadmap = self._get_roadmap()

        # Collect standards from all levels (least specific to most specific)
        standards_by_level = [
            ("roadmap", roadmap.id, roadmap.standards),
            ("track", track_id, track.standards),
        ]

        # Deduplicate (most specific wins)
        resolved = self._deduplicate_standards(standards_by_level)

        # Apply overrides for this track
        resolved = self._apply_overrides(resolved, track_id)

        return resolved

    def has_standard(self, standard_id: str, item_id: str) -> bool:
        """
        Check if a specific standard applies to an item.

        Args:
            standard_id: Standard ID to check
            item_id: ID of task/sprint/track

        Returns:
            True if the standard applies (and is not overridden)
        """
        # Determine item type from ID format
        if '-task-' in item_id:
            resolved = self.resolve_for_task(item_id)
        elif item_id.count('-') >= 1 and not item_id.startswith('task-'):
            # Sprint format: "track-X"
            resolved = self.resolve_for_sprint(item_id)
        else:
            # Track format: "track-name"
            resolved = self.resolve_for_track(item_id)

        # Check if standard exists and is not overridden
        for r in resolved:
            if r.standard.id == standard_id and not r.is_overridden:
                return True

        return False

    def get_standard(self, standard_id: str, item_id: str) -> Optional[ResolvedStandard]:
        """
        Get a specific standard for an item.

        Args:
            standard_id: Standard ID
            item_id: ID of task/sprint/track

        Returns:
            ResolvedStandard if found, None otherwise
        """
        # Determine item type from ID format
        if '-task-' in item_id:
            resolved = self.resolve_for_task(item_id)
        elif item_id.count('-') >= 1:
            resolved = self.resolve_for_sprint(item_id)
        else:
            resolved = self.resolve_for_track(item_id)

        # Find standard
        for r in resolved:
            if r.standard.id == standard_id:
                return r

        return None

    def get_blocking_standards(self, item_id: str) -> List[ResolvedStandard]:
        """
        Get all blocking standards for an item.

        Args:
            item_id: ID of task/sprint/track

        Returns:
            List of blocking ResolvedStandard objects
        """
        # Determine item type from ID format
        if '-task-' in item_id:
            resolved = self.resolve_for_task(item_id)
        elif item_id.count('-') >= 1:
            resolved = self.resolve_for_sprint(item_id)
        else:
            resolved = self.resolve_for_track(item_id)

        # Filter to blocking standards that are not overridden
        return [
            r for r in resolved
            if r.standard.is_blocking() and not r.is_overridden
        ]

    def clear_cache(self):
        """Clear cached roadmap objects."""
        self._roadmap_cache = None
        self._track_cache.clear()
        self._sprint_cache.clear()
