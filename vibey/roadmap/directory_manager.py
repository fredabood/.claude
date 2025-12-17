"""
Directory Manager - Hierarchical roadmap directory structure

This module manages the hierarchical directory structure for roadmap objects:
.vibey/roadmap/
├── {track-slug}/
│   ├── .id (contains track_{ulid})
│   ├── track.yaml
│   ├── track.md
│   ├── table_of_contents.json
│   └── context/
│   └── {sprint-slug}/
│       ├── .id (contains sprint_{ulid})
│       ├── sprint.yaml
│       ├── sprint.md
│       ├── table_of_contents.json
│       └── context/
│       └── {task-slug}/
│           ├── .id (contains task_{ulid})
│           ├── task.yaml
│           ├── task.md
│           └── context/

Key Features:
- Human-readable directory slugs for browsing
- ULID-based IDs in YAML files for stability
- .id files for validation (ensure slug matches ID)
- Automatic context directory creation
- Path helper functions for consistent access
"""

import re
from pathlib import Path
from typing import Optional, Tuple, List
from dataclasses import dataclass


@dataclass
class RoadmapPaths:
    """Container for roadmap directory paths."""
    root: Path
    track_dir: Optional[Path] = None
    sprint_dir: Optional[Path] = None
    task_dir: Optional[Path] = None

    def track_path(self, filename: str) -> Path:
        """Get path to file in track directory."""
        if not self.track_dir:
            raise ValueError("Track directory not set")
        return self.track_dir / filename

    def sprint_path(self, filename: str) -> Path:
        """Get path to file in sprint directory."""
        if not self.sprint_dir:
            raise ValueError("Sprint directory not set")
        return self.sprint_dir / filename

    def task_path(self, filename: str) -> Path:
        """Get path to file in task directory."""
        if not self.task_dir:
            raise ValueError("Task directory not set")
        return self.task_dir / filename


class DirectoryManager:
    """Manages hierarchical directory structure for roadmap objects."""

    def __init__(self, roadmap_root: str = ".vibey/roadmap"):
        """
        Initialize directory manager.

        Args:
            roadmap_root: Root directory for roadmap hierarchy
        """
        self.roadmap_root = Path(roadmap_root)

    def create_roadmap_root(self) -> Path:
        """
        Create the root roadmap directory if it doesn't exist.

        Returns:
            Path: Path to roadmap root
        """
        self.roadmap_root.mkdir(parents=True, exist_ok=True)
        return self.roadmap_root

    def create_track_directory(
        self,
        track_id: str,
        slug: str,
        create_context: bool = True
    ) -> Path:
        """
        Create directory structure for a track.

        Args:
            track_id: ULID-based track ID (e.g., track_01K9N2Z50R...)
            slug: Human-readable slug (e.g., documentation-system)
            create_context: Whether to create context/ subdirectory

        Returns:
            Path: Path to track directory

        Example:
            >>> dm = DirectoryManager()
            >>> track_dir = dm.create_track_directory(
            ...     "track_01K9N2Z50RD3VE1G75ZFZ8936V",
            ...     "documentation-system"
            ... )
            >>> print(track_dir)
            .vibey/roadmap/documentation-system
        """
        # Validate slug
        self._validate_slug(slug)

        # Create track directory
        track_dir = self.roadmap_root / slug
        track_dir.mkdir(parents=True, exist_ok=True)

        # Write .id file for validation
        self._write_id_file(track_dir, track_id)

        # Create context directory if requested
        if create_context:
            (track_dir / "context").mkdir(exist_ok=True)

        return track_dir

    def create_sprint_directory(
        self,
        track_slug: str,
        sprint_id: str,
        sprint_slug: str,
        create_context: bool = True
    ) -> Path:
        """
        Create directory structure for a sprint.

        Args:
            track_slug: Track directory slug
            sprint_id: ULID-based sprint ID
            sprint_slug: Human-readable sprint slug
            create_context: Whether to create context/ subdirectory

        Returns:
            Path: Path to sprint directory
        """
        self._validate_slug(sprint_slug)

        track_dir = self.roadmap_root / track_slug
        if not track_dir.exists():
            raise ValueError(f"Track directory does not exist: {track_dir}")

        sprint_dir = track_dir / sprint_slug
        sprint_dir.mkdir(parents=True, exist_ok=True)

        self._write_id_file(sprint_dir, sprint_id)

        if create_context:
            (sprint_dir / "context").mkdir(exist_ok=True)

        return sprint_dir

    def create_task_directory(
        self,
        track_slug: str,
        sprint_slug: str,
        task_id: str,
        task_slug: str,
        create_context: bool = True
    ) -> Path:
        """
        Create directory structure for a task.

        Args:
            track_slug: Track directory slug
            sprint_slug: Sprint directory slug
            task_id: ULID-based task ID
            task_slug: Human-readable task slug
            create_context: Whether to create context/ subdirectory

        Returns:
            Path: Path to task directory
        """
        self._validate_slug(task_slug)

        sprint_dir = self.roadmap_root / track_slug / sprint_slug
        if not sprint_dir.exists():
            raise ValueError(f"Sprint directory does not exist: {sprint_dir}")

        task_dir = sprint_dir / task_slug
        task_dir.mkdir(parents=True, exist_ok=True)

        self._write_id_file(task_dir, task_id)

        if create_context:
            (task_dir / "context").mkdir(exist_ok=True)

        return task_dir

    def get_track_id(self, track_slug: str) -> str:
        """
        Get track ID from its directory slug.

        Args:
            track_slug: Track directory slug

        Returns:
            str: Track ULID ID

        Raises:
            ValueError: If .id file missing or directory doesn't exist
        """
        track_dir = self.roadmap_root / track_slug
        return self._read_id_file(track_dir)

    def get_sprint_id(self, track_slug: str, sprint_slug: str) -> str:
        """Get sprint ID from its directory slug."""
        sprint_dir = self.roadmap_root / track_slug / sprint_slug
        return self._read_id_file(sprint_dir)

    def get_task_id(
        self,
        track_slug: str,
        sprint_slug: str,
        task_slug: str
    ) -> str:
        """Get task ID from its directory slug."""
        task_dir = self.roadmap_root / track_slug / sprint_slug / task_slug
        return self._read_id_file(task_dir)

    def validate_directory(self, directory: Path, expected_id: str) -> bool:
        """
        Validate that directory's .id file matches expected ID.

        Args:
            directory: Directory to validate
            expected_id: Expected ULID ID

        Returns:
            bool: True if valid, False otherwise
        """
        try:
            actual_id = self._read_id_file(directory)
            return actual_id == expected_id
        except (ValueError, FileNotFoundError):
            return False

    def find_directory_by_id(
        self,
        object_id: str,
        search_root: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Find directory by its ULID ID (searches .id files).

        Args:
            object_id: ULID ID to search for
            search_root: Root directory to search (defaults to roadmap_root)

        Returns:
            Path: Directory path if found, None otherwise
        """
        if search_root is None:
            search_root = self.roadmap_root

        for id_file in search_root.rglob(".id"):
            try:
                file_id = id_file.read_text().strip()
                if file_id == object_id:
                    return id_file.parent
            except Exception:
                continue

        return None

    def list_tracks(self) -> List[Tuple[str, str]]:
        """
        List all tracks (slug, ID pairs).

        Returns:
            List of (slug, id) tuples
        """
        tracks = []
        if not self.roadmap_root.exists():
            return tracks

        for item in self.roadmap_root.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                try:
                    track_id = self._read_id_file(item)
                    tracks.append((item.name, track_id))
                except (ValueError, FileNotFoundError):
                    continue

        return tracks

    def list_sprints(self, track_slug: str) -> List[Tuple[str, str]]:
        """
        List all sprints in a track.

        Returns:
            List of (slug, id) tuples
        """
        sprints = []
        track_dir = self.roadmap_root / track_slug

        if not track_dir.exists():
            return sprints

        for item in track_dir.iterdir():
            if item.is_dir() and not item.name.startswith(".") and item.name != "context":
                try:
                    sprint_id = self._read_id_file(item)
                    sprints.append((item.name, sprint_id))
                except (ValueError, FileNotFoundError):
                    continue

        return sprints

    def list_tasks(
        self,
        track_slug: str,
        sprint_slug: str
    ) -> List[Tuple[str, str]]:
        """
        List all tasks in a sprint.

        Returns:
            List of (slug, id) tuples
        """
        tasks = []
        sprint_dir = self.roadmap_root / track_slug / sprint_slug

        if not sprint_dir.exists():
            return tasks

        for item in sprint_dir.iterdir():
            if item.is_dir() and not item.name.startswith(".") and item.name != "context":
                try:
                    task_id = self._read_id_file(item)
                    tasks.append((item.name, task_id))
                except (ValueError, FileNotFoundError):
                    continue

        return tasks

    def get_paths(
        self,
        track_slug: Optional[str] = None,
        sprint_slug: Optional[str] = None,
        task_slug: Optional[str] = None
    ) -> RoadmapPaths:
        """
        Get path container for roadmap objects.

        Args:
            track_slug: Optional track slug
            sprint_slug: Optional sprint slug (requires track_slug)
            task_slug: Optional task slug (requires sprint_slug)

        Returns:
            RoadmapPaths: Container with paths
        """
        paths = RoadmapPaths(root=self.roadmap_root)

        if track_slug:
            paths.track_dir = self.roadmap_root / track_slug

        if sprint_slug:
            if not track_slug:
                raise ValueError("track_slug required when sprint_slug provided")
            paths.sprint_dir = paths.track_dir / sprint_slug

        if task_slug:
            if not sprint_slug:
                raise ValueError("sprint_slug required when task_slug provided")
            paths.task_dir = paths.sprint_dir / task_slug

        return paths

    # Private helper methods

    def _write_id_file(self, directory: Path, object_id: str) -> None:
        """Write .id file to directory."""
        id_file = directory / ".id"
        id_file.write_text(object_id)

    def _read_id_file(self, directory: Path) -> str:
        """Read .id file from directory."""
        id_file = directory / ".id"

        if not directory.exists():
            raise ValueError(f"Directory does not exist: {directory}")

        if not id_file.exists():
            raise ValueError(f"Missing .id file in directory: {directory}")

        return id_file.read_text().strip()

    def _validate_slug(self, slug: str) -> None:
        """
        Validate directory slug format.

        Slugs must be:
        - Lowercase alphanumeric + hyphens
        - Start with letter or number
        - Not empty
        - Max 100 characters
        """
        if not slug:
            raise ValueError("Slug cannot be empty")

        if len(slug) > 100:
            raise ValueError(f"Slug too long (max 100 chars): {slug}")

        if not re.match(r'^[a-z0-9][a-z0-9-]*$', slug):
            raise ValueError(
                f"Invalid slug format: {slug}. "
                "Must be lowercase alphanumeric + hyphens, starting with letter/number"
            )

        if slug.endswith('-'):
            raise ValueError(f"Slug cannot end with hyphen: {slug}")

        if '--' in slug:
            raise ValueError(f"Slug cannot contain consecutive hyphens: {slug}")


# Convenience functions

def create_track(track_id: str, slug: str) -> Path:
    """Create track directory (convenience function)."""
    dm = DirectoryManager()
    dm.create_roadmap_root()
    return dm.create_track_directory(track_id, slug)


def create_sprint(
    track_slug: str,
    sprint_id: str,
    sprint_slug: str
) -> Path:
    """Create sprint directory (convenience function)."""
    dm = DirectoryManager()
    return dm.create_sprint_directory(track_slug, sprint_id, sprint_slug)


def create_task(
    track_slug: str,
    sprint_slug: str,
    task_id: str,
    task_slug: str
) -> Path:
    """Create task directory (convenience function)."""
    dm = DirectoryManager()
    return dm.create_task_directory(track_slug, sprint_slug, task_id, task_slug)


def get_track_paths(track_slug: str) -> RoadmapPaths:
    """Get paths for a track (convenience function)."""
    dm = DirectoryManager()
    return dm.get_paths(track_slug=track_slug)


def get_sprint_paths(track_slug: str, sprint_slug: str) -> RoadmapPaths:
    """Get paths for a sprint (convenience function)."""
    dm = DirectoryManager()
    return dm.get_paths(track_slug=track_slug, sprint_slug=sprint_slug)


def get_task_paths(
    track_slug: str,
    sprint_slug: str,
    task_slug: str
) -> RoadmapPaths:
    """Get paths for a task (convenience function)."""
    dm = DirectoryManager()
    return dm.get_paths(
        track_slug=track_slug,
        sprint_slug=sprint_slug,
        task_slug=task_slug
    )


if __name__ == "__main__":
    # Demo usage
    print("=== Directory Manager Demo ===\n")

    from vibey.roadmap.id_generator import (
        generate_track_id,
        generate_sprint_id,
        generate_task_id
    )

    # Create test structure
    dm = DirectoryManager("/tmp/vibey-demo")
    dm.create_roadmap_root()

    # Create track
    track_id = generate_track_id()
    track_dir = dm.create_track_directory(track_id, "test-track")
    print(f"Created track: {track_dir}")
    print(f"Track ID: {track_id}\n")

    # Create sprint
    sprint_id = generate_sprint_id()
    sprint_dir = dm.create_sprint_directory("test-track", sprint_id, "sprint-1")
    print(f"Created sprint: {sprint_dir}")
    print(f"Sprint ID: {sprint_id}\n")

    # Create task
    task_id = generate_task_id()
    task_dir = dm.create_task_directory("test-track", "sprint-1", task_id, "task-001")
    print(f"Created task: {task_dir}")
    print(f"Task ID: {task_id}\n")

    # Validate
    print("Validation:")
    print(f"Track valid: {dm.validate_directory(track_dir, track_id)}")
    print(f"Sprint valid: {dm.validate_directory(sprint_dir, sprint_id)}")
    print(f"Task valid: {dm.validate_directory(task_dir, task_id)}\n")

    # List objects
    print("Listing:")
    print(f"Tracks: {dm.list_tracks()}")
    print(f"Sprints: {dm.list_sprints('test-track')}")
    print(f"Tasks: {dm.list_tasks('test-track', 'sprint-1')}")
