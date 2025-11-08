"""
File system management utilities for roadmap state.

Handles directory structure, file paths, and roadmap discovery.
"""

import os
from pathlib import Path
from typing import Optional


class FileSystemManager:
    """Manages roadmap file system structure."""

    VIBEY_DIR = ".vibey"
    TRACKS_DIR = "tracks"
    SPRINTS_DIR = "sprints"
    TASKS_DIR = "tasks"

    ROADMAP_FILE = "roadmap.yaml"

    def __init__(self, root_dir: Optional[Path] = None):
        """
        Initialize file system manager.

        Args:
            root_dir: Root directory (defaults to current working directory)
        """
        self.root_dir = Path(root_dir) if root_dir else Path.cwd()
        self.vibey_dir = self.root_dir / self.VIBEY_DIR

    def ensure_structure(self):
        """Ensure .vibey directory structure exists."""
        dirs = [
            self.vibey_dir,
            self.vibey_dir / self.TRACKS_DIR,
            self.vibey_dir / self.SPRINTS_DIR,
            self.vibey_dir / self.TASKS_DIR,
        ]

        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)

    def get_roadmap_path(self) -> Path:
        """Get path to roadmap.yaml."""
        return self.vibey_dir / self.ROADMAP_FILE

    def get_track_path(self, track_id: str) -> Path:
        """Get path to track YAML file."""
        return self.vibey_dir / self.TRACKS_DIR / f"{track_id}.yaml"

    def get_sprint_path(self, sprint_id: str) -> Path:
        """Get path to sprint YAML file."""
        return self.vibey_dir / self.SPRINTS_DIR / f"{sprint_id}.yaml"

    def get_tasks_path(self, sprint_id: str) -> Path:
        """Get path to tasks YAML file."""
        return self.vibey_dir / self.TASKS_DIR / f"{sprint_id}-tasks.yaml"

    def roadmap_exists(self) -> bool:
        """Check if roadmap.yaml exists."""
        return self.get_roadmap_path().exists()

    def track_exists(self, track_id: str) -> bool:
        """Check if track file exists."""
        return self.get_track_path(track_id).exists()

    def sprint_exists(self, sprint_id: str) -> bool:
        """Check if sprint file exists."""
        return self.get_sprint_path(sprint_id).exists()

    def tasks_exist(self, sprint_id: str) -> bool:
        """Check if tasks file exists."""
        return self.get_tasks_path(sprint_id).exists()

    def list_tracks(self) -> list[str]:
        """List all track IDs."""
        tracks_dir = self.vibey_dir / self.TRACKS_DIR
        if not tracks_dir.exists():
            return []

        return [
            f.stem
            for f in tracks_dir.glob("*.yaml")
            if f.is_file()
        ]

    def list_sprints(self) -> list[str]:
        """List all sprint IDs."""
        sprints_dir = self.vibey_dir / self.SPRINTS_DIR
        if not sprints_dir.exists():
            return []

        return [
            f.stem
            for f in sprints_dir.glob("*.yaml")
            if f.is_file()
        ]

    def list_sprint_tasks(self) -> list[str]:
        """List all sprint IDs that have tasks."""
        tasks_dir = self.vibey_dir / self.TASKS_DIR
        if not tasks_dir.exists():
            return []

        return [
            f.stem.replace("-tasks", "")
            for f in tasks_dir.glob("*-tasks.yaml")
            if f.is_file()
        ]


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
