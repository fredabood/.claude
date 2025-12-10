"""
File system management utilities for roadmap state.

Handles both hierarchical and flat directory structures with automatic detection.

DIRECTORY STRUCTURE FORMATS:

1. Nested (v1 - legacy):
   .vibey/roadmap/{track-slug}/{sprint-slug}/{task-slug}/

2. Flat (v2 - unified architecture):
   .vibey/roadmap/tracks/{ulid}.yaml
   .vibey/roadmap/sprints/{ulid}.yaml
   .vibey/roadmap/tasks/{ulid}.yaml
   .vibey/roadmap/artifacts/{ulid}.yaml
   .vibey/roadmap/context/{scope}/{slug}/

The FileSystemManager automatically detects which format is in use and provides
a unified interface for both.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Literal

# Add framework to path for DirectoryManager import
# Handle both running from repo root and from framework/scripts/
script_dir = Path(__file__).resolve().parent
repo_root = script_dir.parent.parent.parent  # Go up from roadmap-lib → scripts → framework → repo

if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

try:
    from vibey.roadmap.directory_manager import DirectoryManager
except ModuleNotFoundError:
    # Fallback: try relative import for running from framework/scripts/
    roadmap_dir = repo_root / "framework" / "roadmap"
    if str(roadmap_dir.parent) not in sys.path:
        sys.path.insert(0, str(roadmap_dir.parent))
    from roadmap.directory_manager import DirectoryManager


class FileSystemManager:
    """Manages roadmap file system structure (nested or flat)."""

    VIBEY_DIR = ".vibey"
    ROADMAP_DIR = "roadmap"
    ROADMAP_FILE = "roadmap.yaml"

    def __init__(self, root_dir: Optional[Path] = None):
        """
        Initialize file system manager with automatic structure detection.

        Args:
            root_dir: Root directory (defaults to current working directory)
        """
        self.root_dir = Path(root_dir) if root_dir else Path.cwd()
        self.vibey_dir = self.root_dir / self.VIBEY_DIR
        self.roadmap_root = self.vibey_dir / self.ROADMAP_DIR

        # Detect directory structure format
        self.structure_format = self._detect_structure_format()

        # Initialize DirectoryManager for hierarchical structure (legacy)
        # Only used when structure_format == 'nested'
        self.dir_manager = DirectoryManager(str(self.roadmap_root))

        # Cache for ID-to-slug mappings (populated on demand)
        self._id_to_slug_cache: Dict[str, str] = {}

        # Cache for slug-to-ULID mappings from .id files (flat structure)
        self._id_mappings: Optional[Dict[str, Dict[str, str]]] = None

    def ensure_structure(self):
        """Ensure .vibey/roadmap directory structure exists."""
        self.vibey_dir.mkdir(parents=True, exist_ok=True)
        self.dir_manager.create_roadmap_root()

    def _detect_structure_format(self) -> Literal["flat", "nested"]:
        """
        Detect whether roadmap uses flat or nested directory structure.

        Detection logic:
        - If tracks/, sprints/, tasks/ directories exist → flat structure
        - Otherwise → nested structure (default/legacy)

        Returns:
            "flat" or "nested"
        """
        if not self.roadmap_root.exists():
            # No structure yet - default to nested for backward compatibility
            return "nested"

        # Check for flat structure markers
        tracks_dir = self.roadmap_root / "tracks"
        sprints_dir = self.roadmap_root / "sprints"
        tasks_dir = self.roadmap_root / "tasks"

        if tracks_dir.exists() and sprints_dir.exists() and tasks_dir.exists():
            return "flat"

        return "nested"

    def _load_id_mappings(self):
        """
        Load .id mapping files for flat structure.

        Creates in-memory bidirectional mappings:
        - slug → ULID
        - ULID → slug

        For each entity type (tracks, sprints, tasks, artifacts).
        """
        if self._id_mappings is not None:
            return  # Already loaded

        self._id_mappings = {
            "tracks": {},
            "sprints": {},
            "tasks": {},
            "artifacts": {},
        }

        for entity_type in ["tracks", "sprints", "tasks", "artifacts"]:
            id_file = self.roadmap_root / entity_type / ".id"
            if not id_file.exists():
                continue

            # Parse .id file
            with open(id_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue

                    # Parse slug=ulid
                    if '=' in line:
                        slug, ulid = line.split('=', 1)
                        slug = slug.strip()
                        ulid = ulid.strip()

                        # Store bidirectional mapping
                        self._id_mappings[entity_type][slug] = ulid
                        self._id_mappings[entity_type][ulid] = slug

    def _resolve_id_in_flat_structure(self, entity_id: str, entity_type: str) -> str:
        """
        Resolve slug or ULID to ULID in flat structure.

        Args:
            entity_id: Slug or ULID
            entity_type: 'tracks', 'sprints', 'tasks', or 'artifacts'

        Returns:
            ULID

        Raises:
            ValueError: If entity not found
        """
        self._load_id_mappings()

        # If it's already a ULID (26 chars, uppercase alphanumeric)
        if len(entity_id) == 26 and entity_id.replace('_', '').replace('-', '').isalnum():
            return entity_id

        # Look up slug in mapping
        mappings = self._id_mappings.get(entity_type, {})
        ulid = mappings.get(entity_id)

        if ulid:
            # If mapping returns another slug, return the slug as ULID
            # (handles pre-migration state where IDs are slugs)
            return ulid

        # Fallback: assume ID is ULID
        return entity_id

    def _resolve_slug_from_ulid(self, ulid: str, entity_type: str) -> Optional[str]:
        """
        Resolve ULID to slug in flat structure.

        Args:
            ulid: ULID
            entity_type: 'tracks', 'sprints', 'tasks', or 'artifacts'

        Returns:
            Slug if found, None otherwise
        """
        self._load_id_mappings()

        mappings = self._id_mappings.get(entity_type, {})
        return mappings.get(ulid)

    def get_roadmap_path(self) -> Path:
        """Get path to roadmap.yaml (in roadmap root directory)."""
        return self.roadmap_root / self.ROADMAP_FILE

    def get_track_path(self, track_id: str) -> Path:
        """
        Get path to track YAML file (supports both flat and nested structures).

        Args:
            track_id: Track ID (slug or ULID)

        Returns:
            Path to track YAML file
            - Flat: .vibey/roadmap/tracks/{ulid}.yaml
            - Nested: .vibey/roadmap/{track-slug}/track.yaml
        """
        if self.structure_format == "flat":
            ulid = self._resolve_id_in_flat_structure(track_id, "tracks")
            return self.roadmap_root / "tracks" / f"{ulid}.yaml"
        else:
            # Nested structure (legacy)
            track_slug = self._resolve_slug(track_id, 'track')
            return self.roadmap_root / track_slug / "track.yaml"

    def get_sprint_path(self, sprint_id: str) -> Path:
        """
        Get path to sprint YAML file (supports both flat and nested structures).

        Args:
            sprint_id: Sprint ID (slug or ULID)

        Returns:
            Path to sprint YAML file
            - Flat: .vibey/roadmap/sprints/{ulid}.yaml
            - Nested: .vibey/roadmap/{track-slug}/{sprint-slug}/sprint.yaml
        """
        if self.structure_format == "flat":
            ulid = self._resolve_id_in_flat_structure(sprint_id, "sprints")
            return self.roadmap_root / "sprints" / f"{ulid}.yaml"
        else:
            # Nested structure (legacy)
            track_slug, sprint_slug = self._resolve_sprint_path(sprint_id)
            return self.roadmap_root / track_slug / sprint_slug / "sprint.yaml"

    def get_tasks_path(self, sprint_id: str) -> Path:
        """
        Get path to tasks directory (behavior differs by structure).

        Flat structure: Returns tasks/ directory (all tasks in one place)
        Nested structure: Returns sprint directory (tasks in subdirectories)

        Args:
            sprint_id: Sprint ID

        Returns:
            Path to directory containing task files
            - Flat: .vibey/roadmap/tasks/ (all tasks)
            - Nested: .vibey/roadmap/{track-slug}/{sprint-slug}/ (task subdirs)
        """
        if self.structure_format == "flat":
            # In flat structure, all tasks are in tasks/ directory
            # Caller will need to filter by sprint_id
            return self.roadmap_root / "tasks"
        else:
            # Nested structure: return sprint directory containing task subdirectories
            track_slug, sprint_slug = self._resolve_sprint_path(sprint_id)
            return self.roadmap_root / track_slug / sprint_slug

    def get_task_path(self, task_id: str) -> Path:
        """
        Get path to task YAML file (supports both flat and nested structures).

        Args:
            task_id: Task ID (slug or ULID)

        Returns:
            Path to task YAML file
            - Flat: .vibey/roadmap/tasks/{ulid}.yaml
            - Nested: .vibey/roadmap/{track-slug}/{sprint-slug}/{task-slug}/task.yaml
        """
        if self.structure_format == "flat":
            ulid = self._resolve_id_in_flat_structure(task_id, "tasks")
            return self.roadmap_root / "tasks" / f"{ulid}.yaml"
        else:
            # Nested structure - need to search for task
            # This is inefficient but necessary for nested structure
            for track_slug, _ in self.dir_manager.list_tracks():
                for sprint_slug, _ in self.dir_manager.list_sprints(track_slug):
                    task_dir = self.roadmap_root / track_slug / sprint_slug / task_id
                    task_file = task_dir / "task.yaml"
                    if task_file.exists():
                        return task_file

            # Fallback: construct path assuming task_id is directory name
            raise ValueError(f"Task not found: {task_id}")

    def roadmap_exists(self) -> bool:
        """Check if roadmap.yaml exists."""
        return self.get_roadmap_path().exists()

    def track_exists(self, track_id: str) -> bool:
        """Check if track exists in hierarchical structure."""
        try:
            track_path = self.get_track_path(track_id)
            return track_path.exists()
        except (ValueError, FileNotFoundError):
            return False

    def sprint_exists(self, sprint_id: str) -> bool:
        """Check if sprint exists in hierarchical structure."""
        try:
            sprint_path = self.get_sprint_path(sprint_id)
            return sprint_path.exists()
        except (ValueError, FileNotFoundError):
            return False

    def tasks_exist(self, sprint_id: str) -> bool:
        """Check if tasks exist for a sprint."""
        try:
            sprint_dir = self.get_tasks_path(sprint_id)
            # Check if sprint directory exists and has task subdirectories
            if not sprint_dir.exists():
                return False

            # Check for task subdirectories (not 'context' and not starting with '.')
            has_tasks = any(
                item.is_dir() and not item.name.startswith('.') and item.name != 'context'
                for item in sprint_dir.iterdir()
            )
            return has_tasks
        except (ValueError, FileNotFoundError):
            return False

    def list_tracks(self) -> list[str]:
        """
        List all track IDs (supports both flat and nested structures).

        Returns:
            List of track IDs (ULIDs in flat structure, slugs in nested)
        """
        if self.structure_format == "flat":
            tracks_dir = self.roadmap_root / "tracks"
            if not tracks_dir.exists():
                return []

            # Return all .yaml files (excluding .id file)
            track_files = tracks_dir.glob("*.yaml")
            return [f.stem for f in track_files]  # stem removes .yaml extension
        else:
            # Nested structure
            tracks = self.dir_manager.list_tracks()
            # Return IDs (second element of tuples)
            return [track_id for slug, track_id in tracks]

    def list_sprints(self) -> list[str]:
        """
        List all sprint IDs (supports both flat and nested structures).

        Returns:
            List of sprint IDs (ULIDs in flat structure, slugs in nested)
        """
        if self.structure_format == "flat":
            sprints_dir = self.roadmap_root / "sprints"
            if not sprints_dir.exists():
                return []

            # Return all .yaml files (excluding .id file)
            sprint_files = sprints_dir.glob("*.yaml")
            return [f.stem for f in sprint_files]  # stem removes .yaml extension
        else:
            # Nested structure
            sprint_ids = []
            for track_slug, _ in self.dir_manager.list_tracks():
                sprints = self.dir_manager.list_sprints(track_slug)
                sprint_ids.extend([sprint_id for _, sprint_id in sprints])
            return sprint_ids

    def list_sprint_tasks(self) -> list[str]:
        """
        List all sprint IDs that have tasks (supports both flat and nested structures).

        Returns:
            List of sprint IDs that contain tasks
        """
        if self.structure_format == "flat":
            # In flat structure, need to check tasks/ directory
            tasks_dir = self.roadmap_root / "tasks"
            if not tasks_dir.exists():
                return []

            # Get unique sprint IDs from task files
            # Note: This requires loading task files to get sprint_id field
            # For now, return all sprints (optimization can be done later)
            return self.list_sprints()
        else:
            # Nested structure
            sprint_ids_with_tasks = []

            for track_slug, _ in self.dir_manager.list_tracks():
                for sprint_slug, sprint_id in self.dir_manager.list_sprints(track_slug):
                    tasks = self.dir_manager.list_tasks(track_slug, sprint_slug)
                    if tasks:
                        sprint_ids_with_tasks.append(sprint_id)

            return sprint_ids_with_tasks

    # Private helper methods for slug resolution

    def _resolve_slug(self, object_id: str, object_type: str) -> str:
        """
        Resolve object ID to directory slug.

        Args:
            object_id: Object ID (may be slug or ULID)
            object_type: 'track', 'sprint', or 'task'

        Returns:
            Directory slug
        """
        # Check cache
        cache_key = f"{object_type}:{object_id}"
        if cache_key in self._id_to_slug_cache:
            return self._id_to_slug_cache[cache_key]

        # If ID looks like a slug (no underscores, lowercase), try it directly
        if '_' not in object_id and object_id.islower():
            # Verify it exists
            if object_type == 'track':
                test_path = self.roadmap_root / object_id
                if test_path.exists():
                    self._id_to_slug_cache[cache_key] = object_id
                    return object_id

        # Search for directory by ID
        found_dir = self.dir_manager.find_directory_by_id(object_id)
        if found_dir:
            slug = found_dir.name
            self._id_to_slug_cache[cache_key] = slug
            return slug

        # Fallback: assume ID is the slug
        # This handles legacy IDs that are already slug-like (e.g., 'core-framework')
        return object_id

    def _resolve_sprint_path(self, sprint_id: str) -> tuple[str, str]:
        """
        Resolve sprint ID to (track_slug, sprint_slug) tuple.

        Args:
            sprint_id: Sprint ID

        Returns:
            Tuple of (track_slug, sprint_slug)
        """
        # Search all tracks for the sprint
        for track_slug, _ in self.dir_manager.list_tracks():
            for sprint_slug, sid in self.dir_manager.list_sprints(track_slug):
                if sid == sprint_id:
                    return track_slug, sprint_slug

        # Fallback: try to extract from sprint_id pattern (track-id-N)
        # e.g., 'core-framework-2' → track='core-framework', sprint='sprint-2'
        parts = sprint_id.rsplit('-', 1)
        if len(parts) == 2:
            track_slug = parts[0]
            sprint_slug = sprint_id  # Use full ID as slug
            return track_slug, sprint_slug

        raise ValueError(f"Cannot resolve sprint path for: {sprint_id}")


def find_roadmap_root(start_path: Optional[Path] = None) -> Optional[Path]:
    """
    Find the root directory containing a roadmap.

    Searches upward from start_path until a roadmap structure is found.
    Checks for both new (.vibey/roadmap/roadmap.yaml) and legacy (.vibey/roadmap.yaml) paths.

    Args:
        start_path: Starting directory (defaults to current working directory)

    Returns:
        Path to root directory, or None if not found
    """
    current = Path(start_path) if start_path else Path.cwd()

    # Search upward
    while True:
        vibey_dir = current / ".vibey"

        # Check new canonical location first: .vibey/roadmap/roadmap.yaml
        new_roadmap_file = vibey_dir / "roadmap" / "roadmap.yaml"
        if new_roadmap_file.exists():
            return current

        # Fall back to legacy location: .vibey/roadmap.yaml
        legacy_roadmap_file = vibey_dir / "roadmap.yaml"
        if legacy_roadmap_file.exists():
            return current

        # Move up one directory
        parent = current.parent
        if parent == current:
            # Reached filesystem root
            return None

        current = parent


def ensure_roadmap_structure(root_dir: Optional[Path] = None):
    """
    Ensure .vibey directory structure exists.

    Args:
        root_dir: Root directory (defaults to current working directory)
    """
    fs = FileSystemManager(root_dir)
    fs.ensure_structure()


def get_file_system_manager(root_dir: Optional[Path] = None) -> FileSystemManager:
    """
    Get a FileSystemManager instance.

    Args:
        root_dir: Root directory (defaults to current working directory)

    Returns:
        FileSystemManager instance
    """
    return FileSystemManager(root_dir)


def load_yaml(file_path: Path) -> dict:
    """
    Load YAML file.

    Args:
        file_path: Path to YAML file

    Returns:
        Parsed YAML data as dict
    """
    import yaml

    if not file_path.exists():
        return {}

    with open(file_path, 'r') as f:
        return yaml.safe_load(f) or {}


def save_yaml(file_path: Path, data: dict) -> None:
    """
    Save data to YAML file.

    Args:
        file_path: Path to YAML file
        data: Data to save
    """
    import yaml

    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
