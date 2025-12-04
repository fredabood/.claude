"""
YAML migration utilities for converting between legacy and unified ticket formats.

This module provides functions for migrating YAML files from the legacy format
(explicit tracks/sprints/tasks lists) to the unified format (criteria-based).

Key Changes:
- Children lists → CompletableTarget criteria with blocks_transition_to=COMPLETED
- Dependencies → CompletableTarget criteria with blocks_transition_to=IN_PROGRESS
- Deliverables → FileExistsTarget criteria with blocks_transition_to=COMPLETED
- Timestamp fields: created → created_at, started → started_at, etc.

Design Reference: sqlite-backend-6-task-013 (Migration Task)
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid
import yaml


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def generate_criterion_id() -> str:
    """Generate a unique criterion ID."""
    return f"crit-{uuid.uuid4().hex[:8]}"


def migrate_timestamps(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate timestamp field names from legacy to unified format.

    Changes:
    - created → created_at
    - started → started_at
    - completed → completed_at

    Args:
        data: Dictionary with legacy field names

    Returns:
        Dictionary with unified field names
    """
    result = dict(data)

    # Migrate timestamp fields
    if 'created' in result:
        result['created_at'] = result.pop('created')
    if 'started' in result:
        result['started_at'] = result.pop('started')
    if 'completed' in result:
        result['completed_at'] = result.pop('completed')

    # Ensure updated_at exists
    if 'updated_at' not in result:
        result['updated_at'] = datetime.now(timezone.utc).isoformat()

    return result


def children_to_criteria_yaml(
    child_ids: List[str],
    description_template: str = "Child {} complete",
) -> List[Dict[str, Any]]:
    """
    Convert a list of child IDs to criteria YAML format.

    Args:
        child_ids: List of child IDs
        description_template: Template for descriptions

    Returns:
        List of criterion dicts in YAML format
    """
    return [
        {
            "id": generate_criterion_id(),
            "description": description_template.format(child_id),
            "target": {
                "type": "completable",
                "completable_id": child_id,
                "required_status": "completed",
            },
            "blocks_transition_to": "completed",
        }
        for child_id in child_ids
    ]


def dependencies_to_criteria_yaml(
    dependency_ids: List[str],
    description_template: str = "Dependency {} must complete",
) -> List[Dict[str, Any]]:
    """
    Convert dependency IDs to criteria YAML format.

    Args:
        dependency_ids: List of dependency IDs
        description_template: Template for descriptions

    Returns:
        List of criterion dicts blocking IN_PROGRESS
    """
    return [
        {
            "id": generate_criterion_id(),
            "description": description_template.format(dep_id),
            "target": {
                "type": "completable",
                "completable_id": dep_id,
                "required_status": "completed",
            },
            "blocks_transition_to": "in_progress",
        }
        for dep_id in dependency_ids
    ]


def deliverables_to_criteria_yaml(
    deliverables: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Convert deliverables to FileExistsTarget criteria YAML format.

    Args:
        deliverables: List of deliverable dicts with 'paths' field

    Returns:
        List of criterion dicts
    """
    criteria = []
    for deliverable in deliverables:
        paths = deliverable.get('paths', [])
        if paths:
            for path in paths:
                criteria.append({
                    "id": generate_criterion_id(),
                    "description": f"Deliverable exists: {path}",
                    "target": {
                        "type": "file_exists",
                        "paths": [path],
                    },
                    "blocks_transition_to": "completed",
                })
    return criteria


# =============================================================================
# TASK MIGRATION
# =============================================================================


def migrate_task_yaml(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate a task YAML from legacy to unified format.

    Args:
        task_data: Legacy task YAML dict (with 'task' key)

    Returns:
        Unified task YAML dict (with 'ticket' key)
    """
    # Extract task dict
    task = task_data.get('task', task_data)

    # Build criteria from deliverables and dependencies
    criteria = []

    # Convert deliverables
    if 'deliverables' in task:
        criteria.extend(deliverables_to_criteria_yaml(task['deliverables']))

    # Convert depends_on
    if 'depends_on' in task:
        dep_ids = []
        for dep in task['depends_on']:
            if isinstance(dep, str):
                dep_ids.append(dep)
            elif isinstance(dep, dict):
                dep_ids.append(dep.get('blocker_id', dep.get('target_id', '')))
        criteria.extend(dependencies_to_criteria_yaml(dep_ids))

    # Build unified format
    unified = {
        "id": task['id'],
        "name": task.get('title', task['id']),
        "description": task.get('description', ''),
        "status": task.get('status', 'not_started'),
        "ticket_type": "task",
        "priority": task.get('priority', 'medium'),
        "parent_ref": task.get('sprint_id'),
        "criteria": criteria,
        # Task-specific fields
        "task_type_detail": task.get('task_type', 'development'),
        "estimated_tokens": task.get('estimated_tokens', 0),
        "sprint_id": task.get('sprint_id', ''),
        "track_id": task.get('track_id', ''),
        "roadmap_id": task.get('roadmap_id', ''),
    }

    # Migrate timestamps
    unified = migrate_timestamps({**task, **unified})

    # Preserve other fields
    for key in ['blocked', 'deferred', 'commits', 'assigned_agent', 'complexity', 'phase_label']:
        if key in task:
            unified[key] = task[key]

    return {"ticket": unified}


# =============================================================================
# SPRINT MIGRATION
# =============================================================================


def migrate_sprint_yaml(
    sprint_data: Dict[str, Any],
    task_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Migrate a sprint YAML from legacy to unified format.

    Args:
        sprint_data: Legacy sprint YAML dict (with 'sprint' key)
        task_ids: Optional list of task IDs (if not in sprint data)

    Returns:
        Unified sprint YAML dict (with 'ticket' key)
    """
    sprint = sprint_data.get('sprint', sprint_data)

    # Build criteria from tasks and dependencies
    criteria = []

    # Get task IDs from tasks list or parameter
    child_task_ids = task_ids or []
    if 'tasks' in sprint:
        for task in sprint['tasks']:
            if isinstance(task, str):
                child_task_ids.append(task)
            elif isinstance(task, dict):
                child_task_ids.append(task.get('id', ''))

    criteria.extend(children_to_criteria_yaml(child_task_ids, "Task {} complete"))

    # Convert depends_on
    if 'depends_on' in sprint:
        dep_ids = []
        for dep in sprint['depends_on']:
            if isinstance(dep, str):
                dep_ids.append(dep)
            elif isinstance(dep, dict):
                dep_ids.append(dep.get('blocker_id', dep.get('target_id', '')))
        criteria.extend(dependencies_to_criteria_yaml(dep_ids))

    # Build unified format
    unified = {
        "id": sprint['id'],
        "name": sprint.get('name', sprint['id']),
        "description": sprint.get('description', ''),
        "status": sprint.get('status', 'not_started'),
        "ticket_type": "sprint",
        "parent_ref": sprint.get('track_id'),
        "criteria": criteria,
        # Sprint-specific fields
        "track_id": sprint.get('track_id', ''),
        "roadmap_id": sprint.get('roadmap_id', ''),
    }

    # Migrate timestamps
    unified = migrate_timestamps({**sprint, **unified})

    # Preserve metadata
    if 'metadata' in sprint:
        unified['metadata'] = sprint['metadata']

    return {"ticket": unified}


# =============================================================================
# TRACK MIGRATION
# =============================================================================


def migrate_track_yaml(
    track_data: Dict[str, Any],
    sprint_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Migrate a track YAML from legacy to unified format.

    Args:
        track_data: Legacy track YAML dict (with 'track' key)
        sprint_ids: Optional list of sprint IDs (if not in track data)

    Returns:
        Unified track YAML dict (with 'ticket' key)
    """
    track = track_data.get('track', track_data)

    # Build criteria from sprints and dependencies
    criteria = []

    # Get sprint IDs from sprints list or parameter
    child_sprint_ids = sprint_ids or []
    if 'sprints' in track:
        for sprint in track['sprints']:
            if isinstance(sprint, str):
                child_sprint_ids.append(sprint)
            elif isinstance(sprint, dict):
                child_sprint_ids.append(sprint.get('id', ''))

    criteria.extend(children_to_criteria_yaml(child_sprint_ids, "Sprint {} complete"))

    # Convert depends_on
    if 'depends_on' in track:
        dep_ids = []
        for dep in track['depends_on']:
            if isinstance(dep, str):
                dep_ids.append(dep)
            elif isinstance(dep, dict):
                dep_ids.append(dep.get('blocker_id', dep.get('target_id', '')))
        criteria.extend(dependencies_to_criteria_yaml(dep_ids))

    # Build unified format
    unified = {
        "id": track['id'],
        "name": track.get('name', track['id']),
        "description": track.get('description', ''),
        "status": track.get('status', 'not_started'),
        "ticket_type": "track",
        "priority": track.get('priority', 'medium'),
        "parent_ref": track.get('roadmap_id'),
        "criteria": criteria,
        # Track-specific fields
        "roadmap_id": track.get('roadmap_id', ''),
    }

    # Migrate timestamps
    unified = migrate_timestamps({**track, **unified})

    # Preserve metadata
    if 'metadata' in track:
        unified['metadata'] = track['metadata']

    return {"ticket": unified}


# =============================================================================
# ROADMAP MIGRATION
# =============================================================================


def migrate_roadmap_yaml(
    roadmap_data: Dict[str, Any],
    track_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Migrate a roadmap YAML from legacy to unified format.

    Args:
        roadmap_data: Legacy roadmap YAML dict (with 'roadmap' key)
        track_ids: Optional list of track IDs (if not in roadmap data)

    Returns:
        Unified roadmap YAML dict (with 'ticket' key)
    """
    roadmap = roadmap_data.get('roadmap', roadmap_data)

    # Build criteria from tracks
    criteria = []

    # Get track IDs from tracks list or parameter
    child_track_ids = track_ids or []
    if 'tracks' in roadmap:
        for track in roadmap['tracks']:
            if isinstance(track, str):
                child_track_ids.append(track)
            elif isinstance(track, dict):
                child_track_ids.append(track.get('id', ''))

    criteria.extend(children_to_criteria_yaml(child_track_ids, "Track {} complete"))

    # Build unified format
    unified = {
        "id": roadmap['id'],
        "name": roadmap.get('name', roadmap['id']),
        "description": roadmap.get('description', ''),
        "status": roadmap.get('status', 'not_started'),
        "ticket_type": "roadmap",
        "criteria": criteria,
        # Roadmap-specific fields
        "version": roadmap.get('version', '0.0.0'),
    }

    # Migrate timestamps
    unified = migrate_timestamps({**roadmap, **unified})

    return {"ticket": unified}


# =============================================================================
# YAML MIGRATOR CLASS
# =============================================================================


class YAMLMigrator:
    """
    Class for migrating YAML files between legacy and unified formats.

    Usage:
        migrator = YAMLMigrator()

        # Migrate a single file
        migrator.migrate_file(Path("task.yaml"), Path("task_new.yaml"))

        # Migrate entire roadmap directory
        migrator.migrate_roadmap_directory(Path(".vibey/roadmap"))
    """

    def __init__(self, backup: bool = True):
        """
        Initialize the migrator.

        Args:
            backup: Whether to create backups before modifying files
        """
        self.backup = backup

    def detect_format(self, data: Dict[str, Any]) -> str:
        """
        Detect whether YAML is in legacy or unified format.

        Args:
            data: Parsed YAML data

        Returns:
            "legacy" or "unified"
        """
        if 'ticket' in data:
            return "unified"
        if any(key in data for key in ['roadmap', 'track', 'sprint', 'task']):
            return "legacy"
        # Check for criteria field as indicator of unified
        if 'criteria' in data:
            return "unified"
        return "legacy"

    def detect_type(self, data: Dict[str, Any]) -> str:
        """
        Detect the ticket type from YAML data.

        Args:
            data: Parsed YAML data

        Returns:
            "roadmap", "track", "sprint", or "task"
        """
        if 'roadmap' in data or data.get('ticket_type') == 'roadmap':
            return "roadmap"
        if 'track' in data or data.get('ticket_type') == 'track':
            return "track"
        if 'sprint' in data or data.get('ticket_type') == 'sprint':
            return "sprint"
        if 'task' in data or data.get('ticket_type') == 'task':
            return "task"
        # Fallback based on ID patterns
        id_val = data.get('id', data.get('ticket', {}).get('id', ''))
        if 'task' in id_val:
            return "task"
        if 'sprint' in id_val:
            return "sprint"
        if 'track' in id_val:
            return "track"
        return "roadmap"

    def migrate_data(
        self,
        data: Dict[str, Any],
        ticket_type: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Migrate YAML data to unified format.

        Args:
            data: Parsed YAML data
            ticket_type: Type of ticket (auto-detected if not provided)
            **kwargs: Additional arguments passed to migration functions

        Returns:
            Migrated data in unified format
        """
        if self.detect_format(data) == "unified":
            return data  # Already migrated

        t_type = ticket_type or self.detect_type(data)

        if t_type == "task":
            return migrate_task_yaml(data)
        elif t_type == "sprint":
            return migrate_sprint_yaml(data, **kwargs)
        elif t_type == "track":
            return migrate_track_yaml(data, **kwargs)
        elif t_type == "roadmap":
            return migrate_roadmap_yaml(data, **kwargs)
        else:
            raise ValueError(f"Unknown ticket type: {t_type}")

    def migrate_file(
        self,
        source_path: Path,
        target_path: Optional[Path] = None,
        **kwargs,
    ) -> Path:
        """
        Migrate a single YAML file.

        Args:
            source_path: Path to source file
            target_path: Path for output (defaults to overwriting source)
            **kwargs: Additional arguments for migration

        Returns:
            Path to migrated file
        """
        with open(source_path, 'r') as f:
            data = yaml.safe_load(f)

        migrated = self.migrate_data(data, **kwargs)

        output_path = target_path or source_path

        if self.backup and output_path == source_path:
            backup_path = source_path.with_suffix('.yaml.bak')
            with open(backup_path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        with open(output_path, 'w') as f:
            yaml.dump(migrated, f, default_flow_style=False, sort_keys=False)

        return output_path


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "YAMLMigrator",
    "migrate_task_yaml",
    "migrate_sprint_yaml",
    "migrate_track_yaml",
    "migrate_roadmap_yaml",
    "migrate_timestamps",
    "children_to_criteria_yaml",
    "dependencies_to_criteria_yaml",
    "deliverables_to_criteria_yaml",
]
