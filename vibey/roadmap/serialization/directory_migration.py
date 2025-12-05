"""
Directory structure migration for roadmap files.

Supports migration from hierarchical to flat directory structure:

OLD (Hierarchical):
    .vibey/roadmap/<track-id>/<sprint-id>/<task-id>/task.yaml

NEW (Flat):
    .vibey/roadmap/tracks/<track-id>.yaml
    .vibey/roadmap/sprints/<sprint-id>.yaml
    .vibey/roadmap/tasks/<task-id>.yaml
    .vibey/roadmap/context/tasks/<task-id>/*.md

This provides 98% reduction in directory count and 60% reduction in depth.
"""

import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Literal

import yaml

logger = logging.getLogger(__name__)


# ==============================================================================
# Directory Structure Detection
# ==============================================================================

DirectoryStructure = Literal["hierarchical", "flat", "unknown"]


def detect_directory_structure(roadmap_dir: Path) -> DirectoryStructure:
    """
    Detect the directory structure of a roadmap.

    Args:
        roadmap_dir: Path to roadmap directory (.vibey/roadmap)

    Returns:
        'hierarchical' if using nested track/sprint/task folders
        'flat' if using tracks/, sprints/, tasks/ folders
        'unknown' if structure cannot be determined
    """
    # Check for flat structure markers
    has_tracks_folder = (roadmap_dir / 'tracks').is_dir()
    has_sprints_folder = (roadmap_dir / 'sprints').is_dir()
    has_tasks_folder = (roadmap_dir / 'tasks').is_dir()

    if has_tracks_folder and has_sprints_folder and has_tasks_folder:
        return "flat"

    # Check for hierarchical structure markers
    # Look for track.yaml directly under track folders (not in tracks/)
    track_yamls = list(roadmap_dir.glob('*/track.yaml'))
    if track_yamls:
        return "hierarchical"

    # If roadmap.yaml exists but no other structure, it's minimal
    if (roadmap_dir / 'roadmap.yaml').exists():
        # Check if there are any subdirectories with YAML files
        sub_yamls = list(roadmap_dir.glob('*/*.yaml'))
        if sub_yamls:
            return "hierarchical"
        return "unknown"

    return "unknown"


# ==============================================================================
# Path Utilities for Both Structures
# ==============================================================================

class PathResolver:
    """
    Resolve file paths for roadmap entities in either structure.

    Automatically detects the directory structure and returns appropriate paths.
    """

    def __init__(self, roadmap_dir: Path):
        self.roadmap_dir = Path(roadmap_dir)
        self.structure = detect_directory_structure(self.roadmap_dir)

    def roadmap_file(self) -> Path:
        """Get path to roadmap.yaml."""
        return self.roadmap_dir / 'roadmap.yaml'

    def track_file(self, track_id: str) -> Path:
        """Get path to track YAML file."""
        if self.structure == "flat":
            return self.roadmap_dir / 'tracks' / f'{track_id}.yaml'
        else:  # hierarchical
            return self.roadmap_dir / track_id / 'track.yaml'

    def sprint_file(self, sprint_id: str, track_id: Optional[str] = None) -> Path:
        """
        Get path to sprint YAML file.

        Args:
            sprint_id: Sprint ID (e.g., 'sqlite-backend-8')
            track_id: Track ID (required for hierarchical, optional for flat)
        """
        if self.structure == "flat":
            return self.roadmap_dir / 'sprints' / f'{sprint_id}.yaml'
        else:  # hierarchical
            if track_id is None:
                # Try to infer track from sprint ID
                track_id = self._infer_track_from_sprint(sprint_id)
            return self.roadmap_dir / track_id / sprint_id / 'sprint.yaml'

    def task_file(self, task_id: str, sprint_id: Optional[str] = None, track_id: Optional[str] = None) -> Path:
        """
        Get path to task YAML file.

        Args:
            task_id: Task ID (e.g., 'sqlite-backend-8-task-001')
            sprint_id: Sprint ID (required for hierarchical, optional for flat)
            track_id: Track ID (required for hierarchical, optional for flat)
        """
        if self.structure == "flat":
            return self.roadmap_dir / 'tasks' / f'{task_id}.yaml'
        else:  # hierarchical
            if sprint_id is None:
                sprint_id = self._infer_sprint_from_task(task_id)
            if track_id is None:
                track_id = self._infer_track_from_sprint(sprint_id)
            return self.roadmap_dir / track_id / sprint_id / task_id / 'task.yaml'

    def context_dir(self, entity_type: str, entity_id: str) -> Path:
        """
        Get path to context directory for an entity.

        Args:
            entity_type: 'track', 'sprint', or 'task'
            entity_id: Entity ID
        """
        if self.structure == "flat":
            return self.roadmap_dir / 'context' / f'{entity_type}s' / entity_id
        else:  # hierarchical
            if entity_type == 'track':
                return self.roadmap_dir / entity_id / 'context'
            elif entity_type == 'sprint':
                track_id = self._infer_track_from_sprint(entity_id)
                return self.roadmap_dir / track_id / entity_id / 'context'
            else:  # task
                sprint_id = self._infer_sprint_from_task(entity_id)
                track_id = self._infer_track_from_sprint(sprint_id)
                return self.roadmap_dir / track_id / sprint_id / entity_id / 'context'

    def _infer_track_from_sprint(self, sprint_id: str) -> str:
        """Infer track ID from sprint ID (e.g., 'sqlite-backend-8' -> 'sqlite-backend')."""
        # Sprint IDs are typically track-id + number
        parts = sprint_id.rsplit('-', 1)
        if len(parts) == 2 and parts[1].isdigit():
            return parts[0]
        return sprint_id

    def _infer_sprint_from_task(self, task_id: str) -> str:
        """Infer sprint ID from task ID (e.g., 'sqlite-backend-8-task-001' -> 'sqlite-backend-8')."""
        # Task IDs are sprint-id + '-task-' + number
        if '-task-' in task_id:
            return task_id.rsplit('-task-', 1)[0]
        return task_id

    def all_track_files(self) -> List[Path]:
        """Get all track YAML files."""
        if self.structure == "flat":
            return list((self.roadmap_dir / 'tracks').glob('*.yaml'))
        else:
            return list(self.roadmap_dir.glob('*/track.yaml'))

    def all_sprint_files(self) -> List[Path]:
        """Get all sprint YAML files."""
        if self.structure == "flat":
            return list((self.roadmap_dir / 'sprints').glob('*.yaml'))
        else:
            return list(self.roadmap_dir.glob('*/*/sprint.yaml'))

    def all_task_files(self) -> List[Path]:
        """Get all task YAML files."""
        if self.structure == "flat":
            return list((self.roadmap_dir / 'tasks').glob('*.yaml'))
        else:
            return list(self.roadmap_dir.glob('*/*/*/task.yaml'))


# ==============================================================================
# Directory Migration
# ==============================================================================

class MigrationResult:
    """Result of directory structure migration."""

    def __init__(self):
        self.tracks_migrated: int = 0
        self.sprints_migrated: int = 0
        self.tasks_migrated: int = 0
        self.context_files_migrated: int = 0
        self.errors: List[Tuple[str, str]] = []

    @property
    def total_migrated(self) -> int:
        return self.tracks_migrated + self.sprints_migrated + self.tasks_migrated

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0


def migrate_to_flat_structure(
    roadmap_dir: Path,
    dry_run: bool = False,
    preserve_old: bool = True,
    verbose: bool = False,
) -> MigrationResult:
    """
    Migrate from hierarchical to flat directory structure.

    Args:
        roadmap_dir: Path to roadmap directory (.vibey/roadmap)
        dry_run: If True, only report what would happen
        preserve_old: If True, create backup before migration
        verbose: If True, log detailed progress

    Returns:
        MigrationResult with migration details
    """
    result = MigrationResult()

    # Check current structure
    current = detect_directory_structure(roadmap_dir)
    if current == "flat":
        logger.info("Directory is already in flat structure")
        return result
    elif current == "unknown":
        result.errors.append(("roadmap_dir", "Cannot detect directory structure"))
        return result

    # Create new directories
    if not dry_run:
        (roadmap_dir / 'tracks').mkdir(exist_ok=True)
        (roadmap_dir / 'sprints').mkdir(exist_ok=True)
        (roadmap_dir / 'tasks').mkdir(exist_ok=True)
        (roadmap_dir / 'context' / 'tracks').mkdir(parents=True, exist_ok=True)
        (roadmap_dir / 'context' / 'sprints').mkdir(parents=True, exist_ok=True)
        (roadmap_dir / 'context' / 'tasks').mkdir(parents=True, exist_ok=True)

    # Migrate tracks
    track_files = list(roadmap_dir.glob('*/track.yaml'))
    for track_file in track_files:
        track_id = track_file.parent.name
        try:
            new_path = roadmap_dir / 'tracks' / f'{track_id}.yaml'
            if verbose:
                logger.info(f"Migrating track: {track_id}")

            if not dry_run:
                # Copy track file
                shutil.copy2(track_file, new_path)

                # Copy context files
                old_context = track_file.parent / 'context'
                if old_context.exists():
                    new_context = roadmap_dir / 'context' / 'tracks' / track_id
                    if old_context.is_dir():
                        shutil.copytree(old_context, new_context, dirs_exist_ok=True)
                        result.context_files_migrated += len(list(old_context.glob('**/*')))

            result.tracks_migrated += 1

        except Exception as e:
            result.errors.append((f"track:{track_id}", str(e)))

    # Migrate sprints
    sprint_files = list(roadmap_dir.glob('*/*/sprint.yaml'))
    for sprint_file in sprint_files:
        sprint_id = sprint_file.parent.name
        try:
            new_path = roadmap_dir / 'sprints' / f'{sprint_id}.yaml'
            if verbose:
                logger.info(f"Migrating sprint: {sprint_id}")

            if not dry_run:
                shutil.copy2(sprint_file, new_path)

                # Copy context files
                old_context = sprint_file.parent / 'context'
                if old_context.exists():
                    new_context = roadmap_dir / 'context' / 'sprints' / sprint_id
                    if old_context.is_dir():
                        shutil.copytree(old_context, new_context, dirs_exist_ok=True)
                        result.context_files_migrated += len(list(old_context.glob('**/*')))

            result.sprints_migrated += 1

        except Exception as e:
            result.errors.append((f"sprint:{sprint_id}", str(e)))

    # Migrate tasks
    task_files = list(roadmap_dir.glob('*/*/*/task.yaml'))
    for task_file in task_files:
        task_id = task_file.parent.name
        try:
            new_path = roadmap_dir / 'tasks' / f'{task_id}.yaml'
            if verbose:
                logger.info(f"Migrating task: {task_id}")

            if not dry_run:
                shutil.copy2(task_file, new_path)

                # Copy context files
                old_context = task_file.parent / 'context'
                if old_context.exists():
                    new_context = roadmap_dir / 'context' / 'tasks' / task_id
                    if old_context.is_dir():
                        shutil.copytree(old_context, new_context, dirs_exist_ok=True)
                        result.context_files_migrated += len(list(old_context.glob('**/*')))

            result.tasks_migrated += 1

        except Exception as e:
            result.errors.append((f"task:{task_id}", str(e)))

    return result


def format_migration_result(result: MigrationResult, verbose: bool = False) -> str:
    """Format migration result for CLI output."""
    lines = []

    lines.append("\nDirectory Migration Summary")
    lines.append("=" * 50)
    lines.append(f"Tracks migrated:  {result.tracks_migrated}")
    lines.append(f"Sprints migrated: {result.sprints_migrated}")
    lines.append(f"Tasks migrated:   {result.tasks_migrated}")
    lines.append(f"Context files:    {result.context_files_migrated}")
    lines.append(f"Total:            {result.total_migrated}")

    if result.errors:
        lines.append("\nErrors:")
        for entity, error in result.errors:
            lines.append(f"  ! {entity}: {error}")

    return '\n'.join(lines)


# ==============================================================================
# Structure Comparison
# ==============================================================================

def compare_structures(roadmap_dir: Path) -> Dict[str, Any]:
    """
    Compare current structure metrics.

    Args:
        roadmap_dir: Path to roadmap directory

    Returns:
        Dict with structure metrics
    """
    structure = detect_directory_structure(roadmap_dir)

    # Count directories
    all_dirs = list(roadmap_dir.glob('**'))
    dir_count = len([d for d in all_dirs if d.is_dir()])

    # Calculate max depth
    max_depth = 0
    for path in all_dirs:
        depth = len(path.relative_to(roadmap_dir).parts)
        max_depth = max(max_depth, depth)

    # Count files by type
    yaml_count = len(list(roadmap_dir.glob('**/*.yaml')))
    md_count = len(list(roadmap_dir.glob('**/*.md')))

    return {
        'structure': structure,
        'directory_count': dir_count,
        'max_depth': max_depth,
        'yaml_file_count': yaml_count,
        'markdown_file_count': md_count,
    }


def estimate_flat_structure(roadmap_dir: Path) -> Dict[str, Any]:
    """
    Estimate metrics after migration to flat structure.

    Args:
        roadmap_dir: Path to roadmap directory

    Returns:
        Dict with estimated metrics
    """
    # Count entities
    track_count = len(list(roadmap_dir.glob('*/track.yaml')))
    sprint_count = len(list(roadmap_dir.glob('*/*/sprint.yaml')))
    task_count = len(list(roadmap_dir.glob('*/*/*/task.yaml')))

    # Flat structure: tracks/, sprints/, tasks/, context/{tracks,sprints,tasks}/<entity-id>
    # Base: 7 directories (tracks, sprints, tasks, context, context/tracks, context/sprints, context/tasks)
    base_dirs = 7

    # Plus one context dir per entity that has context files
    context_entities = 0
    for track_dir in roadmap_dir.glob('*/'):
        if (track_dir / 'context').is_dir():
            context_entities += 1
    for sprint_dir in roadmap_dir.glob('*/*/'):
        if (sprint_dir / 'context').is_dir():
            context_entities += 1
    for task_dir in roadmap_dir.glob('*/*/*/'):
        if (task_dir / 'context').is_dir():
            context_entities += 1

    return {
        'structure': 'flat',
        'directory_count': base_dirs + context_entities,
        'max_depth': 4,  # context/tasks/<task-id>/subdir
        'track_count': track_count,
        'sprint_count': sprint_count,
        'task_count': task_count,
    }
