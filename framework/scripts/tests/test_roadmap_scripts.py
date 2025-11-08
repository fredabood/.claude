#!/usr/bin/env python3
"""
Integration tests for roadmap scripts.

Tests the full workflow: init → query → update
"""

import unittest
import tempfile
import shutil
import subprocess
import os
from pathlib import Path


class TestRoadmapScripts(unittest.TestCase):
    """Integration tests for roadmap scripts."""

    def setUp(self):
        """Set up test directory."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.scripts_dir = Path(__file__).parent.parent
        self.framework_root = self.scripts_dir.parent

        # Set up environment
        self.env = os.environ.copy()
        self.env['PYTHONPATH'] = str(self.framework_root)

    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)

    def run_script(self, script_name: str, args: list[str]) -> subprocess.CompletedProcess:
        """Run a roadmap script."""
        script_path = self.scripts_dir / script_name
        cmd = ["python3", str(script_path), "--dir", str(self.test_dir)] + args
        return subprocess.run(cmd, capture_output=True, text=True, env=self.env)

    def test_01_init_interactive_help(self):
        """Test that init script shows help."""
        result = self.run_script("roadmap-init.py", ["--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("Initialize a new roadmap", result.stdout)

    def test_02_init_non_interactive(self):
        """Test roadmap initialization (non-interactive)."""
        result = self.run_script(
            "roadmap-init.py",
            [
                "--id", "test-roadmap",
                "--name", "Test Roadmap",
                "--version", "1.0.0",
                "--bump-on", "sprint_completion",
                "--bump-type", "minor",
                "--created-by", "test-suite",
            ]
        )

        self.assertEqual(result.returncode, 0, f"Init failed: {result.stderr}")
        self.assertIn("Roadmap Initialized Successfully", result.stdout)

        # Check files created
        vibey_dir = self.test_dir / ".vibey"
        self.assertTrue(vibey_dir.exists())
        self.assertTrue((vibey_dir / "roadmap.yaml").exists())
        self.assertTrue((vibey_dir / "tracks").exists())
        self.assertTrue((vibey_dir / "sprints").exists())
        self.assertTrue((vibey_dir / "tasks").exists())

    def test_03_query_roadmap_summary(self):
        """Test querying roadmap summary."""
        # Initialize first
        self.run_script(
            "roadmap-init.py",
            [
                "--id", "test-roadmap",
                "--name", "Test Roadmap",
                "--version", "1.0.0",
            ]
        )

        # Query
        result = self.run_script("roadmap-query.py", [])

        self.assertEqual(result.returncode, 0)
        self.assertIn("Test Roadmap", result.stdout)
        self.assertIn("1.0.0", result.stdout)

    def test_04_query_json_output(self):
        """Test JSON output from query."""
        # Initialize first
        self.run_script(
            "roadmap-init.py",
            [
                "--id", "test-roadmap",
                "--name", "Test Roadmap",
            ]
        )

        # Query with JSON
        result = self.run_script("roadmap-query.py", ["--json"])

        self.assertEqual(result.returncode, 0)
        self.assertIn('"id": "test-roadmap"', result.stdout)
        self.assertIn('"name": "Test Roadmap"', result.stdout)

    def test_05_query_nonexistent_track(self):
        """Test querying non-existent track."""
        # Initialize first
        self.run_script(
            "roadmap-init.py",
            ["--id", "test-roadmap", "--name", "Test"]
        )

        # Query non-existent track
        result = self.run_script("roadmap-query.py", ["--track", "nonexistent"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not found", result.stdout)

    def test_06_init_force_reinitialize(self):
        """Test force re-initialization."""
        # Initialize
        self.run_script(
            "roadmap-init.py",
            ["--id", "test-1", "--name", "First"]
        )

        # Try to init again without force (should fail)
        result = self.run_script(
            "roadmap-init.py",
            ["--id", "test-2", "--name", "Second"]
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("already exists", result.stdout)

        # Init with force (should succeed)
        result = self.run_script(
            "roadmap-init.py",
            ["--id", "test-2", "--name", "Second", "--force"]
        )
        self.assertEqual(result.returncode, 0)

    def test_07_query_help(self):
        """Test that query script shows help."""
        result = self.run_script("roadmap-query.py", ["--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("Query roadmap state", result.stdout)

    def test_08_update_help(self):
        """Test that update script shows help."""
        result = self.run_script("roadmap-update.py", ["--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("Update roadmap state", result.stdout)

    def test_09_update_without_roadmap(self):
        """Test update operations fail without roadmap."""
        result = self.run_script(
            "roadmap-update.py",
            ["--start-task", "backend-1-task-001"]
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("No roadmap found", result.stdout)

    def test_10_query_without_roadmap(self):
        """Test query fails without roadmap."""
        result = self.run_script("roadmap-query.py", [])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("No roadmap found", result.stdout)


class TestRoadmapWorkflow(unittest.TestCase):
    """Test complete roadmap workflow using example data."""

    def setUp(self):
        """Set up test directory with example roadmap."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.scripts_dir = Path(__file__).parent.parent
        self.framework_root = self.scripts_dir.parent
        self.example_dir = self.framework_root / "roadmap" / "examples" / "sample-roadmap"

        # Set up environment
        self.env = os.environ.copy()
        self.env['PYTHONPATH'] = str(self.framework_root)

        # Copy example to test directory
        vibey_dir = self.test_dir / ".vibey"
        vibey_dir.mkdir()

        # Copy example files
        shutil.copy(
            self.example_dir / "roadmap.yaml",
            vibey_dir / "roadmap.yaml"
        )

        (vibey_dir / "tracks").mkdir()
        shutil.copy(
            self.example_dir / "tracks" / "backend.yaml",
            vibey_dir / "tracks" / "backend.yaml"
        )

        (vibey_dir / "sprints").mkdir()
        shutil.copy(
            self.example_dir / "sprints" / "backend-1.yaml",
            vibey_dir / "sprints" / "backend-1.yaml"
        )

        (vibey_dir / "tasks").mkdir()
        shutil.copy(
            self.example_dir / "tasks" / "backend-1-tasks.yaml",
            vibey_dir / "tasks" / "backend-1-tasks.yaml"
        )

    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)

    def run_script(self, script_name: str, args: list[str]) -> subprocess.CompletedProcess:
        """Run a roadmap script."""
        script_path = self.scripts_dir / script_name
        cmd = ["python3", str(script_path), "--dir", str(self.test_dir)] + args
        return subprocess.run(cmd, capture_output=True, text=True, env=self.env)

    def test_01_query_roadmap(self):
        """Test querying example roadmap."""
        result = self.run_script("roadmap-query.py", [])

        self.assertEqual(result.returncode, 0)
        self.assertIn("E-Commerce Platform", result.stdout)

    def test_02_query_track(self):
        """Test querying backend track."""
        result = self.run_script("roadmap-query.py", ["--track", "backend"])

        self.assertEqual(result.returncode, 0)
        self.assertIn("Backend Development", result.stdout)

    def test_03_query_sprint(self):
        """Test querying backend-1 sprint."""
        result = self.run_script("roadmap-query.py", ["--sprint", "backend-1"])

        self.assertEqual(result.returncode, 0)
        self.assertIn("User Authentication", result.stdout)
        self.assertIn("Development Tasks", result.stdout)

    def test_04_query_task(self):
        """Test querying specific task."""
        result = self.run_script("roadmap-query.py", ["--task", "backend-1-task-001"])

        self.assertEqual(result.returncode, 0)
        self.assertIn("backend-1-task-001", result.stdout)

    def test_05_start_sprint(self):
        """Test starting a sprint."""
        result = self.run_script("roadmap-update.py", ["--start-sprint", "backend-1"])

        self.assertEqual(result.returncode, 0)
        self.assertIn("started", result.stdout)

        # Verify status changed
        result = self.run_script("roadmap-query.py", ["--sprint", "backend-1", "--json"])
        self.assertIn('"status": "in_progress"', result.stdout)

    def test_06_start_task(self):
        """Test starting a task."""
        # Start sprint first
        self.run_script("roadmap-update.py", ["--start-sprint", "backend-1"])

        # Start task
        result = self.run_script(
            "roadmap-update.py",
            ["--start-task", "backend-1-task-001"]
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("in progress", result.stdout)

    def test_07_assign_task(self):
        """Test assigning a task."""
        result = self.run_script(
            "roadmap-update.py",
            ["--assign-task", "backend-1-task-001", "--agent", "web-developer"]
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("assigned", result.stdout)

    def test_08_complete_task(self):
        """Test completing a task."""
        # Start sprint first
        self.run_script("roadmap-update.py", ["--start-sprint", "backend-1"])

        # Complete task
        result = self.run_script(
            "roadmap-update.py",
            ["--complete-task", "backend-1-task-001"]
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("completed", result.stdout)

    def test_09_complete_all_tasks_progresses_sprint(self):
        """Test that completing all dev tasks progresses sprint to completion_gate_check."""
        # Start sprint
        self.run_script("roadmap-update.py", ["--start-sprint", "backend-1"])

        # Complete all dev tasks (001-003)
        self.run_script("roadmap-update.py", ["--complete-task", "backend-1-task-001"])
        self.run_script("roadmap-update.py", ["--complete-task", "backend-1-task-002"])
        result = self.run_script("roadmap-update.py", ["--complete-task", "backend-1-task-003"])

        # Sprint should auto-progress to completion_gate_check
        self.assertIn("completion_gate_check", result.stdout)

    def test_10_refresh_progress(self):
        """Test refreshing progress calculations."""
        result = self.run_script("roadmap-update.py", ["--refresh-progress"])

        self.assertEqual(result.returncode, 0)
        self.assertIn("Progress refreshed", result.stdout)

    def test_11_query_blockers(self):
        """Test querying blockers."""
        result = self.run_script("roadmap-query.py", ["--blockers"])

        self.assertEqual(result.returncode, 0)
        # Should return JSON with blockers info

    def test_12_query_dependencies(self):
        """Test querying dependency graph."""
        result = self.run_script("roadmap-query.py", ["--dependencies"])

        self.assertEqual(result.returncode, 0)
        self.assertIn('"nodes":', result.stdout)


def run_tests():
    """Run all tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestRoadmapScripts))
    suite.addTests(loader.loadTestsFromTestCase(TestRoadmapWorkflow))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
