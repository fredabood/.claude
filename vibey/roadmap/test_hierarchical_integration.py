"""
Integration tests for hierarchical roadmap structure.

Tests the complete workflow from directory creation to TOC generation,
context management, and path resolution.

Created: 2025-11-09
Task: documentation-system-1-task-006
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone

from framework.roadmap.directory_manager import DirectoryManager
from framework.roadmap.id_generator import (
    generate_track_id,
    generate_sprint_id,
    generate_task_id,
)
from framework.roadmap.toc_generator import TOCGenerator


class TestHierarchicalIntegration(unittest.TestCase):
    """Integration tests for hierarchical structure."""

    def setUp(self):
        """Create temporary test directory."""
        self.test_dir = tempfile.mkdtemp(prefix="vibey_test_")
        self.roadmap_root = Path(self.test_dir) / ".vibey" / "roadmap"
        self.dir_manager = DirectoryManager(str(self.roadmap_root))
        self.toc_generator = TOCGenerator(str(self.roadmap_root))

    def tearDown(self):
        """Clean up temporary directory."""
        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)

    def test_create_full_hierarchy(self):
        """Create complete track > sprint > task hierarchy."""
        # Generate IDs
        track_id = generate_track_id()
        sprint_id = generate_sprint_id()
        task_id = generate_task_id()

        # Create hierarchy
        track_dir = self.dir_manager.create_track_directory(
            track_id=track_id,
            slug="test-track",
            create_context=True
        )

        sprint_dir = self.dir_manager.create_sprint_directory(
            track_slug="test-track",
            sprint_id=sprint_id,
            sprint_slug="sprint-1",
            create_context=True
        )

        task_dir = self.dir_manager.create_task_directory(
            track_slug="test-track",
            sprint_slug="sprint-1",
            task_id=task_id,
            task_slug="task-001",
            create_context=True
        )

        # Verify structure
        self.assertTrue(track_dir.exists())
        self.assertTrue(sprint_dir.exists())
        self.assertTrue(task_dir.exists())

        # Verify .id files
        self.assertTrue((track_dir / ".id").exists())
        self.assertTrue((sprint_dir / ".id").exists())
        self.assertTrue((task_dir / ".id").exists())

        # Verify context directories
        self.assertTrue((track_dir / "context").exists())
        self.assertTrue((sprint_dir / "context").exists())
        self.assertTrue((task_dir / "context").exists())

        # Verify ID resolution
        self.assertEqual(self.dir_manager.get_track_id("test-track"), track_id)
        self.assertEqual(
            self.dir_manager.get_sprint_id("test-track", "sprint-1"),
            sprint_id
        )
        self.assertEqual(
            self.dir_manager.get_task_id("test-track", "sprint-1", "task-001"),
            task_id
        )

    def test_list_hierarchy(self):
        """Test listing tracks, sprints, and tasks."""
        # Create test data
        track1_id = generate_track_id()
        track2_id = generate_track_id()

        self.dir_manager.create_track_directory(track1_id, "track-1")
        self.dir_manager.create_track_directory(track2_id, "track-2")

        sprint1_id = generate_sprint_id()
        sprint2_id = generate_sprint_id()

        self.dir_manager.create_sprint_directory("track-1", sprint1_id, "sprint-1")
        self.dir_manager.create_sprint_directory("track-1", sprint2_id, "sprint-2")

        task1_id = generate_task_id()
        task2_id = generate_task_id()

        self.dir_manager.create_task_directory(
            "track-1", "sprint-1", task1_id, "task-001"
        )
        self.dir_manager.create_task_directory(
            "track-1", "sprint-1", task2_id, "task-002"
        )

        # Test listing
        tracks = self.dir_manager.list_tracks()
        self.assertEqual(len(tracks), 2)
        track_ids = [tid for slug, tid in tracks]
        self.assertIn(track1_id, track_ids)
        self.assertIn(track2_id, track_ids)

        sprints = self.dir_manager.list_sprints("track-1")
        self.assertEqual(len(sprints), 2)
        sprint_ids = [sid for slug, sid in sprints]
        self.assertIn(sprint1_id, sprint_ids)
        self.assertIn(sprint2_id, sprint_ids)

        tasks = self.dir_manager.list_tasks("track-1", "sprint-1")
        self.assertEqual(len(tasks), 2)
        task_ids = [tid for slug, tid in tasks]
        self.assertIn(task1_id, task_ids)
        self.assertIn(task2_id, task_ids)

    def test_find_directory_by_id(self):
        """Test finding directories by ID."""
        track_id = generate_track_id()
        sprint_id = generate_sprint_id()
        task_id = generate_task_id()

        self.dir_manager.create_track_directory(track_id, "my-track")
        self.dir_manager.create_sprint_directory("my-track", sprint_id, "my-sprint")
        self.dir_manager.create_task_directory(
            "my-track", "my-sprint", task_id, "my-task"
        )

        # Find by ID
        track_dir = self.dir_manager.find_directory_by_id(track_id)
        self.assertIsNotNone(track_dir)
        self.assertEqual(track_dir.name, "my-track")

        sprint_dir = self.dir_manager.find_directory_by_id(sprint_id)
        self.assertIsNotNone(sprint_dir)
        self.assertEqual(sprint_dir.name, "my-sprint")

        task_dir = self.dir_manager.find_directory_by_id(task_id)
        self.assertIsNotNone(task_dir)
        self.assertEqual(task_dir.name, "my-task")

    def test_validate_directory(self):
        """Test directory validation."""
        track_id = generate_track_id()
        wrong_id = generate_track_id()

        track_dir = self.dir_manager.create_track_directory(track_id, "test-track")

        # Correct ID validates
        self.assertTrue(self.dir_manager.validate_directory(track_dir, track_id))

        # Wrong ID fails validation
        self.assertFalse(self.dir_manager.validate_directory(track_dir, wrong_id))

    def test_path_helpers(self):
        """Test RoadmapPaths helper methods."""
        track_id = generate_track_id()
        sprint_id = generate_sprint_id()
        task_id = generate_task_id()

        self.dir_manager.create_track_directory(track_id, "test-track")
        self.dir_manager.create_sprint_directory("test-track", sprint_id, "sprint-1")
        self.dir_manager.create_task_directory(
            "test-track", "sprint-1", task_id, "task-001"
        )

        # Get paths
        track_paths = self.dir_manager.get_paths("test-track")
        self.assertIsNotNone(track_paths.track_dir)
        self.assertEqual(track_paths.track_dir.name, "test-track")

        sprint_paths = self.dir_manager.get_paths("test-track", "sprint-1")
        self.assertIsNotNone(sprint_paths.sprint_dir)
        self.assertEqual(sprint_paths.sprint_dir.name, "sprint-1")

        task_paths = self.dir_manager.get_paths("test-track", "sprint-1", "task-001")
        self.assertIsNotNone(task_paths.task_dir)
        self.assertEqual(task_paths.task_dir.name, "task-001")

        # Test path helper methods
        track_yaml = track_paths.track_path("track.yaml")
        self.assertEqual(track_yaml.name, "track.yaml")

        sprint_yaml = sprint_paths.sprint_path("sprint.yaml")
        self.assertEqual(sprint_yaml.name, "sprint.yaml")

        task_yaml = task_paths.task_path("task.yaml")
        self.assertEqual(task_yaml.name, "task.yaml")

    def test_context_directory_creation(self):
        """Test context directory creation at all levels."""
        track_id = generate_track_id()
        sprint_id = generate_sprint_id()
        task_id = generate_task_id()

        # Create with context directories
        track_dir = self.dir_manager.create_track_directory(
            track_id, "test-track", create_context=True
        )
        sprint_dir = self.dir_manager.create_sprint_directory(
            "test-track", sprint_id, "sprint-1", create_context=True
        )
        task_dir = self.dir_manager.create_task_directory(
            "test-track", "sprint-1", task_id, "task-001", create_context=True
        )

        # Verify context dirs exist
        self.assertTrue((track_dir / "context").is_dir())
        self.assertTrue((sprint_dir / "context").is_dir())
        self.assertTrue((task_dir / "context").is_dir())

        # Test without context directories
        track2_id = generate_track_id()
        track2_dir = self.dir_manager.create_track_directory(
            track2_id, "test-track-2", create_context=False
        )

        # Context should not be created
        self.assertFalse((track2_dir / "context").exists())

    def test_slug_validation(self):
        """Test slug validation rules."""
        track_id = generate_track_id()

        # Valid slugs
        valid_slugs = [
            "test-track",
            "my-awesome-track",
            "track123",
            "123track",
            "a" * 100,  # Max length
        ]

        for slug in valid_slugs:
            try:
                self.dir_manager.create_track_directory(track_id, slug)
            except ValueError as e:
                self.fail(f"Valid slug '{slug}' was rejected: {e}")

        # Invalid slugs
        invalid_slugs = [
            "",  # Empty
            "Test-Track",  # Uppercase
            "test--track",  # Consecutive hyphens
            "-test",  # Starts with hyphen
            "test-",  # Ends with hyphen
            "test_track",  # Underscore
            "test track",  # Space
            "a" * 101,  # Too long
        ]

        for slug in invalid_slugs:
            with self.assertRaises(ValueError, msg=f"Invalid slug '{slug}' was accepted"):
                self.dir_manager.create_track_directory(generate_track_id(), slug)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def setUp(self):
        """Create temporary test directory."""
        self.test_dir = tempfile.mkdtemp(prefix="vibey_test_edge_")
        self.roadmap_root = Path(self.test_dir) / ".vibey" / "roadmap"
        self.dir_manager = DirectoryManager(str(self.roadmap_root))

    def tearDown(self):
        """Clean up temporary directory."""
        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)

    def test_missing_parent_directory(self):
        """Creating child without parent should raise error."""
        sprint_id = generate_sprint_id()

        with self.assertRaises(ValueError):
            self.dir_manager.create_sprint_directory(
                "nonexistent-track",
                sprint_id,
                "sprint-1"
            )

    def test_missing_id_file(self):
        """Reading ID from directory without .id file should raise error."""
        # Create directory manually without .id file
        track_dir = self.roadmap_root / "manual-track"
        track_dir.mkdir(parents=True)

        with self.assertRaises(ValueError):
            self.dir_manager.get_track_id("manual-track")

    def test_directory_not_exist(self):
        """Validating nonexistent directory should return False."""
        nonexistent = self.roadmap_root / "ghost"

        # validate_directory returns False for nonexistent directories
        result = self.dir_manager.validate_directory(nonexistent, "some-id")
        self.assertFalse(result)

    def test_find_nonexistent_id(self):
        """Finding nonexistent ID should return None."""
        result = self.dir_manager.find_directory_by_id("nonexistent-id")
        self.assertIsNone(result)


class TestPerformance(unittest.TestCase):
    """Performance tests for hierarchical operations."""

    def setUp(self):
        """Create temporary test directory."""
        self.test_dir = tempfile.mkdtemp(prefix="vibey_test_perf_")
        self.roadmap_root = Path(self.test_dir) / ".vibey" / "roadmap"
        self.dir_manager = DirectoryManager(str(self.roadmap_root))

    def tearDown(self):
        """Clean up temporary directory."""
        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)

    def test_list_large_hierarchy(self):
        """List operations should be fast even with many objects."""
        import time

        # Create 10 tracks with 5 sprints each with 10 tasks each = 500 tasks
        for t in range(10):
            track_id = generate_track_id()
            self.dir_manager.create_track_directory(track_id, f"track-{t}")

            for s in range(5):
                sprint_id = generate_sprint_id()
                self.dir_manager.create_sprint_directory(
                    f"track-{t}",
                    sprint_id,
                    f"sprint-{s}"
                )

                for tk in range(10):
                    task_id = generate_task_id()
                    self.dir_manager.create_task_directory(
                        f"track-{t}",
                        f"sprint-{s}",
                        task_id,
                        f"task-{tk}"
                    )

        # Test list performance
        start = time.time()
        tracks = self.dir_manager.list_tracks()
        track_time = (time.time() - start) * 1000

        start = time.time()
        sprints = self.dir_manager.list_sprints("track-0")
        sprint_time = (time.time() - start) * 1000

        start = time.time()
        tasks = self.dir_manager.list_tasks("track-0", "sprint-0")
        task_time = (time.time() - start) * 1000

        # Verify counts
        self.assertEqual(len(tracks), 10)
        self.assertEqual(len(sprints), 5)
        self.assertEqual(len(tasks), 10)

        # Performance should be reasonable (<100ms each)
        self.assertLess(track_time, 100, f"List tracks took {track_time:.1f}ms")
        self.assertLess(sprint_time, 100, f"List sprints took {sprint_time:.1f}ms")
        self.assertLess(task_time, 100, f"List tasks took {task_time:.1f}ms")


if __name__ == '__main__':
    unittest.main()
