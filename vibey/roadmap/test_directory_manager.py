"""
Unit tests for hierarchical directory manager.

Tests verify:
- Directory creation at all levels (track/sprint/task)
- .id file creation and validation
- Slug validation
- Path helper functions
- Directory listing
- ID lookup by directory
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from framework.roadmap.directory_manager import (
    DirectoryManager,
    RoadmapPaths,
    create_track,
    create_sprint,
    create_task,
    get_track_paths,
    get_sprint_paths,
    get_task_paths,
)
from framework.roadmap.id_generator import (
    generate_track_id,
    generate_sprint_id,
    generate_task_id,
)


class TestDirectoryCreation(unittest.TestCase):
    """Test directory creation at all levels."""

    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.dm = DirectoryManager(self.temp_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_create_roadmap_root(self):
        """Root directory is created."""
        root = self.dm.create_roadmap_root()
        self.assertTrue(root.exists())
        self.assertTrue(root.is_dir())

    def test_create_track_directory(self):
        """Track directory is created with correct structure."""
        self.dm.create_roadmap_root()
        track_id = generate_track_id()

        track_dir = self.dm.create_track_directory(track_id, "test-track")

        self.assertTrue(track_dir.exists())
        self.assertTrue((track_dir / ".id").exists())
        self.assertTrue((track_dir / "context").exists())
        self.assertEqual(track_dir.name, "test-track")

    def test_create_sprint_directory(self):
        """Sprint directory is created with correct structure."""
        self.dm.create_roadmap_root()
        track_id = generate_track_id()
        sprint_id = generate_sprint_id()

        self.dm.create_track_directory(track_id, "test-track")
        sprint_dir = self.dm.create_sprint_directory(
            "test-track", sprint_id, "sprint-1"
        )

        self.assertTrue(sprint_dir.exists())
        self.assertTrue((sprint_dir / ".id").exists())
        self.assertTrue((sprint_dir / "context").exists())

    def test_create_task_directory(self):
        """Task directory is created with correct structure."""
        self.dm.create_roadmap_root()
        track_id = generate_track_id()
        sprint_id = generate_sprint_id()
        task_id = generate_task_id()

        self.dm.create_track_directory(track_id, "test-track")
        self.dm.create_sprint_directory("test-track", sprint_id, "sprint-1")
        task_dir = self.dm.create_task_directory(
            "test-track", "sprint-1", task_id, "task-001"
        )

        self.assertTrue(task_dir.exists())
        self.assertTrue((task_dir / ".id").exists())
        self.assertTrue((task_dir / "context").exists())

    def test_create_without_context(self):
        """Can create directories without context subdirectory."""
        self.dm.create_roadmap_root()
        track_id = generate_track_id()

        track_dir = self.dm.create_track_directory(
            track_id, "test-track", create_context=False
        )

        self.assertTrue(track_dir.exists())
        self.assertFalse((track_dir / "context").exists())


class TestIDFiles(unittest.TestCase):
    """Test .id file creation and validation."""

    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.dm = DirectoryManager(self.temp_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_id_file_contains_correct_id(self):
        """".id file contains the correct ULID."""
        self.dm.create_roadmap_root()
        track_id = generate_track_id()

        track_dir = self.dm.create_track_directory(track_id, "test-track")
        id_file_content = (track_dir / ".id").read_text().strip()

        self.assertEqual(id_file_content, track_id)

    def test_get_track_id(self):
        """Can retrieve track ID from directory slug."""
        self.dm.create_roadmap_root()
        track_id = generate_track_id()

        self.dm.create_track_directory(track_id, "test-track")
        retrieved_id = self.dm.get_track_id("test-track")

        self.assertEqual(retrieved_id, track_id)

    def test_get_sprint_id(self):
        """Can retrieve sprint ID from directory slug."""
        self.dm.create_roadmap_root()
        track_id = generate_track_id()
        sprint_id = generate_sprint_id()

        self.dm.create_track_directory(track_id, "test-track")
        self.dm.create_sprint_directory("test-track", sprint_id, "sprint-1")

        retrieved_id = self.dm.get_sprint_id("test-track", "sprint-1")
        self.assertEqual(retrieved_id, sprint_id)

    def test_get_task_id(self):
        """Can retrieve task ID from directory slug."""
        self.dm.create_roadmap_root()
        track_id = generate_track_id()
        sprint_id = generate_sprint_id()
        task_id = generate_task_id()

        self.dm.create_track_directory(track_id, "test-track")
        self.dm.create_sprint_directory("test-track", sprint_id, "sprint-1")
        self.dm.create_task_directory("test-track", "sprint-1", task_id, "task-001")

        retrieved_id = self.dm.get_task_id("test-track", "sprint-1", "task-001")
        self.assertEqual(retrieved_id, task_id)


class TestValidation(unittest.TestCase):
    """Test directory and slug validation."""

    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.dm = DirectoryManager(self.temp_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_validate_directory_correct_id(self):
        """validate_directory returns True for correct ID."""
        self.dm.create_roadmap_root()
        track_id = generate_track_id()

        track_dir = self.dm.create_track_directory(track_id, "test-track")
        is_valid = self.dm.validate_directory(track_dir, track_id)

        self.assertTrue(is_valid)

    def test_validate_directory_wrong_id(self):
        """validate_directory returns False for wrong ID."""
        self.dm.create_roadmap_root()
        track_id = generate_track_id()
        wrong_id = generate_track_id()

        track_dir = self.dm.create_track_directory(track_id, "test-track")
        is_valid = self.dm.validate_directory(track_dir, wrong_id)

        self.assertFalse(is_valid)

    def test_valid_slugs(self):
        """Valid slugs are accepted."""
        valid_slugs = [
            "test-track",
            "documentation-system",
            "mcp-server-1",
            "task-001",
            "a",
            "1-2-3",
        ]

        self.dm.create_roadmap_root()
        for slug in valid_slugs:
            try:
                track_id = generate_track_id()
                self.dm.create_track_directory(track_id, slug)
            except ValueError:
                self.fail(f"Valid slug rejected: {slug}")

    def test_invalid_slugs(self):
        """Invalid slugs are rejected."""
        invalid_slugs = [
            "",  # Empty
            "Test-Track",  # Uppercase
            "test_track",  # Underscore
            "test.track",  # Dot
            "-test",  # Starts with hyphen
            "test-",  # Ends with hyphen
            "test--track",  # Consecutive hyphens
            "x" * 101,  # Too long
        ]

        self.dm.create_roadmap_root()
        for slug in invalid_slugs:
            with self.assertRaises(ValueError, msg=f"Invalid slug accepted: {slug}"):
                track_id = generate_track_id()
                self.dm.create_track_directory(track_id, slug)


class TestListing(unittest.TestCase):
    """Test directory listing functions."""

    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.dm = DirectoryManager(self.temp_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_list_tracks(self):
        """list_tracks returns all tracks."""
        self.dm.create_roadmap_root()

        track1_id = generate_track_id()
        track2_id = generate_track_id()

        self.dm.create_track_directory(track1_id, "track-1")
        self.dm.create_track_directory(track2_id, "track-2")

        tracks = self.dm.list_tracks()

        self.assertEqual(len(tracks), 2)
        slugs = [slug for slug, _ in tracks]
        self.assertIn("track-1", slugs)
        self.assertIn("track-2", slugs)

    def test_list_sprints(self):
        """list_sprints returns all sprints in a track."""
        self.dm.create_roadmap_root()

        track_id = generate_track_id()
        sprint1_id = generate_sprint_id()
        sprint2_id = generate_sprint_id()

        self.dm.create_track_directory(track_id, "test-track")
        self.dm.create_sprint_directory("test-track", sprint1_id, "sprint-1")
        self.dm.create_sprint_directory("test-track", sprint2_id, "sprint-2")

        sprints = self.dm.list_sprints("test-track")

        self.assertEqual(len(sprints), 2)
        slugs = [slug for slug, _ in sprints]
        self.assertIn("sprint-1", slugs)
        self.assertIn("sprint-2", slugs)

    def test_list_tasks(self):
        """list_tasks returns all tasks in a sprint."""
        self.dm.create_roadmap_root()

        track_id = generate_track_id()
        sprint_id = generate_sprint_id()
        task1_id = generate_task_id()
        task2_id = generate_task_id()

        self.dm.create_track_directory(track_id, "test-track")
        self.dm.create_sprint_directory("test-track", sprint_id, "sprint-1")
        self.dm.create_task_directory("test-track", "sprint-1", task1_id, "task-001")
        self.dm.create_task_directory("test-track", "sprint-1", task2_id, "task-002")

        tasks = self.dm.list_tasks("test-track", "sprint-1")

        self.assertEqual(len(tasks), 2)
        slugs = [slug for slug, _ in tasks]
        self.assertIn("task-001", slugs)
        self.assertIn("task-002", slugs)

    def test_list_empty_returns_empty_list(self):
        """Listing empty directories returns empty list."""
        self.dm.create_roadmap_root()

        tracks = self.dm.list_tracks()
        self.assertEqual(len(tracks), 0)


class TestPathHelpers(unittest.TestCase):
    """Test path helper functions."""

    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.dm = DirectoryManager(self.temp_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_get_track_paths(self):
        """get_paths returns correct paths for track level."""
        paths = self.dm.get_paths(track_slug="test-track")

        self.assertIsNotNone(paths.track_dir)
        self.assertEqual(paths.track_dir.name, "test-track")
        self.assertIsNone(paths.sprint_dir)
        self.assertIsNone(paths.task_dir)

    def test_get_sprint_paths(self):
        """get_paths returns correct paths for sprint level."""
        paths = self.dm.get_paths(track_slug="test-track", sprint_slug="sprint-1")

        self.assertIsNotNone(paths.track_dir)
        self.assertIsNotNone(paths.sprint_dir)
        self.assertEqual(paths.sprint_dir.name, "sprint-1")
        self.assertIsNone(paths.task_dir)

    def test_get_task_paths(self):
        """get_paths returns correct paths for task level."""
        paths = self.dm.get_paths(
            track_slug="test-track", sprint_slug="sprint-1", task_slug="task-001"
        )

        self.assertIsNotNone(paths.track_dir)
        self.assertIsNotNone(paths.sprint_dir)
        self.assertIsNotNone(paths.task_dir)
        self.assertEqual(paths.task_dir.name, "task-001")

    def test_paths_helper_methods(self):
        """RoadmapPaths helper methods work correctly."""
        paths = self.dm.get_paths(
            track_slug="test-track", sprint_slug="sprint-1", task_slug="task-001"
        )

        track_file = paths.track_path("track.yaml")
        sprint_file = paths.sprint_path("sprint.yaml")
        task_file = paths.task_path("task.yaml")

        self.assertEqual(track_file.name, "track.yaml")
        self.assertEqual(sprint_file.name, "sprint.yaml")
        self.assertEqual(task_file.name, "task.yaml")


class TestFindByID(unittest.TestCase):
    """Test finding directories by ULID."""

    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.dm = DirectoryManager(self.temp_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_find_track_by_id(self):
        """Can find track directory by its ULID."""
        self.dm.create_roadmap_root()
        track_id = generate_track_id()

        self.dm.create_track_directory(track_id, "test-track")
        found_dir = self.dm.find_directory_by_id(track_id)

        self.assertIsNotNone(found_dir)
        self.assertEqual(found_dir.name, "test-track")

    def test_find_sprint_by_id(self):
        """Can find sprint directory by its ULID."""
        self.dm.create_roadmap_root()
        track_id = generate_track_id()
        sprint_id = generate_sprint_id()

        self.dm.create_track_directory(track_id, "test-track")
        self.dm.create_sprint_directory("test-track", sprint_id, "sprint-1")

        found_dir = self.dm.find_directory_by_id(sprint_id)

        self.assertIsNotNone(found_dir)
        self.assertEqual(found_dir.name, "sprint-1")

    def test_find_nonexistent_id(self):
        """find_directory_by_id returns None for nonexistent ID."""
        self.dm.create_roadmap_root()
        nonexistent_id = generate_track_id()

        found_dir = self.dm.find_directory_by_id(nonexistent_id)

        self.assertIsNone(found_dir)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""

    def setUp(self):
        """Create temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        # Override default directory for testing
        import framework.roadmap.directory_manager as dm_module
        self.original_default = dm_module.DirectoryManager.__init__.__defaults__
        dm_module.DirectoryManager.__init__.__defaults__ = (self.temp_dir,)

    def tearDown(self):
        """Clean up and restore defaults."""
        import framework.roadmap.directory_manager as dm_module
        dm_module.DirectoryManager.__init__.__defaults__ = self.original_default
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_track_convenience(self):
        """create_track convenience function works."""
        track_id = generate_track_id()
        track_dir = create_track(track_id, "test-track")

        self.assertTrue(track_dir.exists())
        self.assertTrue((track_dir / ".id").exists())


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
