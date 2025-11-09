"""
File system management utilities for roadmap state.

Handles hierarchical directory structure, file paths, and roadmap discovery.

This module has been updated to use the hierarchical directory structure:
.vibey/roadmap/{track-slug}/{sprint-slug}/{task-slug}/

Legacy flat structure (.vibey/tracks/, .vibey/sprints/, .vibey/tasks/) is deprecated.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict

# Add framework to path for DirectoryManager import
# Handle both running from repo root and from framework/scripts/
script_dir = Path(__file__).resolve().parent
repo_root = script_dir.parent.parent.parent  # Go up from roadmap-lib → scripts → framework → repo

if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

try:
    from framework.roadmap.directory_manager import DirectoryManager
except ModuleNotFoundError:
    # Fallback: try relative import for running from framework/scripts/
    roadmap_dir = repo_root / "framework" / "roadmap"
    if str(roadmap_dir.parent) not in sys.path:
        sys.path.insert(0, str(roadmap_dir.parent))
    from roadmap.directory_manager import DirectoryManager


class FileSystemManager:
    """Manages hierarchical roadmap file system structure."""

    VIBEY_DIR = ".vibey"
    ROADMAP_DIR = "roadmap"
    ROADMAP_FILE = "roadmap.yaml"

    def __init__(self, root_dir: Optional[Path] = None):
        """
        Initialize file system manager.

        Args:
            root_dir: Root directory (defaults to current working directory)
        """
        self.root_dir = Path(root_dir) if root_dir else Path.cwd()
        self.vibey_dir = self.root_dir / self.VIBEY_DIR
        self.roadmap_root = self.vibey_dir / self.ROADMAP_DIR

        # Initialize DirectoryManager for hierarchical structure
        self.dir_manager = DirectoryManager(str(self.roadmap_root))

        # Cache for ID-to-slug mappings (populated on demand)
        self._id_to_slug_cache: Dict[str, str] = {}

    def ensure_structure(self):
        """Ensure .vibey/roadmap directory structure exists."""
        self.vibey_dir.mkdir(parents=True, exist_ok=True)
        self.dir_manager.create_roadmap_root()

    def get_roadmap_path(self) -> Path:
        """Get path to roadmap.yaml."""
        return self.vibey_dir / self.ROADMAP_FILE

    def get_track_path(self, track_id: str) -> Path:
        """
        Get path to track.yaml file in hierarchical structure.

        Args:
            track_id: Track ID (e.g., 'core-framework' or 'track_01JB...')

        Returns:
            Path to track.yaml
        """
        track_slug = self._resolve_slug(track_id, 'track')
        return self.roadmap_root / track_slug / "track.yaml"

    def get_sprint_path(self, sprint_id: str) -> Path:
        """
        Get path to sprint.yaml file in hierarchical structure.

        Args:
            sprint_id: Sprint ID

        Returns:
            Path to sprint.yaml
        """
        track_slug, sprint_slug = self._resolve_sprint_path(sprint_id)
        return self.roadmap_root / track_slug / sprint_slug / "sprint.yaml"

    def get_tasks_path(self, sprint_id: str) -> Path:
        """
        Get path to tasks in hierarchical structure.

        Note: In hierarchical structure, tasks are individual files in
        {track}/{sprint}/{task}/task.yaml, not a single tasks file.
        This method returns the sprint directory for compatibility.

        Args:
            sprint_id: Sprint ID

        Returns:
            Path to sprint directory containing task subdirectories
        """
        track_slug, sprint_slug = self._resolve_sprint_path(sprint_id)
        return self.roadmap_root / track_slug / sprint_slug

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
        """List all track IDs from hierarchical structure."""
        tracks = self.dir_manager.list_tracks()
        # Return IDs (second element of tuples)
        return [track_id for slug, track_id in tracks]

    def list_sprints(self) -> list[str]:
        """
        List all sprint IDs from hierarchical structure.

        Returns:
            List of sprint IDs across all tracks
        """
        sprint_ids = []
        for track_slug, _ in self.dir_manager.list_tracks():
            sprints = self.dir_manager.list_sprints(track_slug)
            sprint_ids.extend([sprint_id for _, sprint_id in sprints])
        return sprint_ids

    def list_sprint_tasks(self) -> list[str]:
        """
        List all sprint IDs that have tasks.

        Returns:
            List of sprint IDs that contain task subdirectories
        """
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
    Find the root directory containing .vibey/roadmap.yaml.

    Searches upward from start_path until .vibey/roadmap.yaml is found.

    Args:
        start_path: Starting directory (defaults to current working directory)

    Returns:
        Path to root directory, or None if not found
    """
    current = Path(start_path) if start_path else Path.cwd()

    # Search upward
    while True:
        vibey_dir = current / ".vibey"
        roadmap_file = vibey_dir / "roadmap.yaml"

        if roadmap_file.exists():
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
