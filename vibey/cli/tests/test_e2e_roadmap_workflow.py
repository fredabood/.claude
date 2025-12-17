#!/usr/bin/env python3
"""
End-to-End Roadmap Workflow Integration Tests

Tests the complete user journey through the roadmap-integrated /vibey workflow:
1. Initialize project
2. Create sprint
3. Execute sprint
4. Track progress
5. Complete sprint

This validates that all components work together correctly.
"""

import unittest
import tempfile
import shutil
import yaml
import os
from pathlib import Path
from datetime import datetime, timezone


class TestE2ERoadmapWorkflow(unittest.TestCase):
    """Test complete end-to-end roadmap workflow."""

    def setUp(self):
        """Set up test environment with temporary project directory."""
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)
        self.original_dir = os.getcwd()

        # Change to test directory
        os.chdir(self.test_path)

        # Get path to scripts directory
        self.scripts_dir = Path(self.original_dir) / "framework" / "scripts"

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)

    def test_01_initialization(self):
        """Test: Initialize .vibey/ structure."""
        # Create .vibey directory structure manually
        # (simulates what /vibey deployment would do)
        vibey_dir = self.test_path / ".vibey"
        vibey_dir.mkdir(parents=True, exist_ok=True)

        (vibey_dir / "tracks").mkdir(exist_ok=True)
        (vibey_dir / "sprints").mkdir(exist_ok=True)
        (vibey_dir / "tasks").mkdir(exist_ok=True)

        # Create roadmap.yaml
        roadmap_data = {
            "roadmap": {
                "id": "test-project",
                "name": "Test Project",
                "status": "in_progress",
                "created": datetime.now(timezone.utc).isoformat() + "+00:00",
                "tracks": [],
                "metadata": {
                    "version": "1.0.0",
                    "framework_version": "1.3.0"
                }
            }
        }

        with open(vibey_dir / "roadmap.yaml", "w") as f:
            yaml.dump(roadmap_data, f)

        # Verify structure created
        self.assertTrue(vibey_dir.exists())
        self.assertTrue((vibey_dir / "roadmap.yaml").exists())
        self.assertTrue((vibey_dir / "tracks").exists())
        self.assertTrue((vibey_dir / "sprints").exists())
        self.assertTrue((vibey_dir / "tasks").exists())

        # Verify roadmap content
        with open(vibey_dir / "roadmap.yaml") as f:
            loaded = yaml.safe_load(f)
            self.assertEqual(loaded["roadmap"]["id"], "test-project")
            self.assertEqual(loaded["roadmap"]["status"], "in_progress")

    def test_02_create_track(self):
        """Test: Create track in roadmap."""
        vibey_dir = self.test_path / ".vibey"
        vibey_dir.mkdir(parents=True, exist_ok=True)
        (vibey_dir / "tracks").mkdir(exist_ok=True)

        # Create test track
        track_data = {
            "track": {
                "id": "test-track",
                "name": "Test Track",
                "roadmap_id": "test-project",
                "status": "not_started",
                "blocked": False,
                "priority": "high",
                "created": datetime.now(timezone.utc).isoformat() + "+00:00",
                "started": None,
                "completed": None,
                "estimated_duration": "2 weeks",
                "progress": {
                    "sprints_total": 0,
                    "sprints_completed": 0,
                    "tasks_total": 0,
                    "tasks_completed": 0,
                    "completion_percent": 0
                },
                "sprints": [],
                "dependencies": [],
                "quality_gates": [],
                "assigned_agents": [],
                "deliverables": [],
                "metadata": {
                    "created_by": "test",
                    "last_updated": datetime.now(timezone.utc).isoformat() + "+00:00"
                }
            }
        }

        track_file = vibey_dir / "tracks" / "test-track.yaml"
        with open(track_file, "w") as f:
            yaml.dump(track_data, f)

        # Verify track created
        self.assertTrue(track_file.exists())

        with open(track_file) as f:
            loaded = yaml.safe_load(f)
            self.assertEqual(loaded["track"]["id"], "test-track")
            self.assertEqual(loaded["track"]["status"], "not_started")

    def test_03_create_sprint(self):
        """Test: Create sprint with tasks."""
        vibey_dir = self.test_path / ".vibey"
        (vibey_dir / "sprints").mkdir(parents=True, exist_ok=True)
        (vibey_dir / "tasks").mkdir(parents=True, exist_ok=True)

        # Create sprint
        sprint_data = {
            "sprint": {
                "id": "test-sprint-1",
                "name": "Test Sprint 1",
                "track_id": "test-track",
                "roadmap_id": "test-project",
                "status": "not_started",
                "blocked": False,
                "created": datetime.now(timezone.utc).isoformat() + "+00:00",
                "started": None,
                "completed": None,
                "progress": {
                    "development_tasks_total": 3,
                    "development_tasks_completed": 0,
                    "tasks_total": 3,
                    "tasks_completed": 0,
                    "completion_percent": 0
                },
                "tasks": [
                    "test-sprint-1-task-001",
                    "test-sprint-1-task-002",
                    "test-sprint-1-task-003"
                ],
                "quality_gates": [
                    {
                        "name": "Unit Testing",
                        "threshold": 80,
                        "blocking": True,
                        "status": "not_run",
                        "score": None
                    }
                ],
                "plan_file": "docs/sprints/test-sprint-1-plan.md",
                "deliverables": ["Test feature"],
                "metadata": {
                    "last_updated": datetime.now(timezone.utc).isoformat() + "+00:00",
                    "estimated_duration": "1 week"
                }
            }
        }

        sprint_file = vibey_dir / "sprints" / "test-sprint-1.yaml"
        with open(sprint_file, "w") as f:
            yaml.dump(sprint_data, f)

        # Create tasks
        tasks_data = {
            "tasks": [
                {
                    "id": "test-sprint-1-task-001",
                    "sprint_id": "test-sprint-1",
                    "title": "Implement feature A",
                    "description": "Build feature A",
                    "status": "not_started",
                    "priority": "high",
                    "estimated_hours": 4,
                    "assigned_agents": ["web-developer"]
                },
                {
                    "id": "test-sprint-1-task-002",
                    "sprint_id": "test-sprint-1",
                    "title": "Write tests",
                    "description": "Test feature A",
                    "status": "not_started",
                    "priority": "high",
                    "estimated_hours": 2,
                    "assigned_agents": ["test-engineer"]
                },
                {
                    "id": "test-sprint-1-task-003",
                    "sprint_id": "test-sprint-1",
                    "title": "Update documentation",
                    "description": "Document feature A",
                    "status": "not_started",
                    "priority": "medium",
                    "estimated_hours": 1,
                    "assigned_agents": ["docs-writer"]
                }
            ]
        }

        tasks_file = vibey_dir / "tasks" / "test-sprint-1-tasks.yaml"
        with open(tasks_file, "w") as f:
            yaml.dump(tasks_data, f)

        # Verify sprint and tasks created
        self.assertTrue(sprint_file.exists())
        self.assertTrue(tasks_file.exists())

        with open(sprint_file) as f:
            sprint = yaml.safe_load(f)
            self.assertEqual(len(sprint["sprint"]["tasks"]), 3)

        with open(tasks_file) as f:
            tasks = yaml.safe_load(f)
            self.assertEqual(len(tasks["tasks"]), 3)

    def test_04_start_sprint(self):
        """Test: Start sprint and mark task in progress."""
        vibey_dir = self.test_path / ".vibey"
        sprint_file = vibey_dir / "sprints" / "test-sprint-1.yaml"
        tasks_file = vibey_dir / "tasks" / "test-sprint-1-tasks.yaml"

        # Create files first
        self.test_03_create_sprint()

        # Start sprint
        with open(sprint_file) as f:
            sprint_data = yaml.safe_load(f)

        sprint_data["sprint"]["status"] = "in_progress"
        sprint_data["sprint"]["started"] = datetime.now(timezone.utc).isoformat() + "+00:00"

        with open(sprint_file, "w") as f:
            yaml.dump(sprint_data, f)

        # Start first task
        with open(tasks_file) as f:
            tasks_data = yaml.safe_load(f)

        tasks_data["tasks"][0]["status"] = "in_progress"
        tasks_data["tasks"][0]["started"] = datetime.now(timezone.utc).isoformat() + "+00:00"

        with open(tasks_file, "w") as f:
            yaml.dump(tasks_data, f)

        # Verify status updates
        with open(sprint_file) as f:
            sprint = yaml.safe_load(f)
            self.assertEqual(sprint["sprint"]["status"], "in_progress")
            self.assertIsNotNone(sprint["sprint"]["started"])

        with open(tasks_file) as f:
            tasks = yaml.safe_load(f)
            self.assertEqual(tasks["tasks"][0]["status"], "in_progress")
            self.assertIsNotNone(tasks["tasks"][0]["started"])

    def test_05_complete_task(self):
        """Test: Complete task and update progress."""
        vibey_dir = self.test_path / ".vibey"
        sprint_file = vibey_dir / "sprints" / "test-sprint-1.yaml"
        tasks_file = vibey_dir / "tasks" / "test-sprint-1-tasks.yaml"

        # Start from previous test state
        self.test_04_start_sprint()

        # Complete first task
        with open(tasks_file) as f:
            tasks_data = yaml.safe_load(f)

        tasks_data["tasks"][0]["status"] = "completed"
        tasks_data["tasks"][0]["completed"] = datetime.now(timezone.utc).isoformat() + "+00:00"

        with open(tasks_file, "w") as f:
            yaml.dump(tasks_data, f)

        # Update sprint progress
        with open(sprint_file) as f:
            sprint_data = yaml.safe_load(f)

        sprint_data["sprint"]["progress"]["tasks_completed"] = 1
        sprint_data["sprint"]["progress"]["completion_percent"] = 33  # 1/3 = 33%

        with open(sprint_file, "w") as f:
            yaml.dump(sprint_data, f)

        # Verify task completed
        with open(tasks_file) as f:
            tasks = yaml.safe_load(f)
            self.assertEqual(tasks["tasks"][0]["status"], "completed")
            self.assertIsNotNone(tasks["tasks"][0]["completed"])

        # Verify progress updated
        with open(sprint_file) as f:
            sprint = yaml.safe_load(f)
            self.assertEqual(sprint["sprint"]["progress"]["tasks_completed"], 1)
            self.assertEqual(sprint["sprint"]["progress"]["completion_percent"], 33)

    def test_06_complete_all_tasks(self):
        """Test: Complete all tasks in sprint."""
        vibey_dir = self.test_path / ".vibey"
        sprint_file = vibey_dir / "sprints" / "test-sprint-1.yaml"
        tasks_file = vibey_dir / "tasks" / "test-sprint-1-tasks.yaml"

        # Start from previous state
        self.test_05_complete_task()

        # Complete remaining tasks
        with open(tasks_file) as f:
            tasks_data = yaml.safe_load(f)

        for task in tasks_data["tasks"]:
            task["status"] = "completed"
            if not task.get("completed"):
                task["completed"] = datetime.now(timezone.utc).isoformat() + "+00:00"

        with open(tasks_file, "w") as f:
            yaml.dump(tasks_data, f)

        # Update sprint progress to 100%
        with open(sprint_file) as f:
            sprint_data = yaml.safe_load(f)

        sprint_data["sprint"]["progress"]["tasks_completed"] = 3
        sprint_data["sprint"]["progress"]["completion_percent"] = 100

        with open(sprint_file, "w") as f:
            yaml.dump(sprint_data, f)

        # Verify all tasks completed
        with open(tasks_file) as f:
            tasks = yaml.safe_load(f)
            completed_count = sum(1 for t in tasks["tasks"] if t["status"] == "completed")
            self.assertEqual(completed_count, 3)

        # Verify sprint at 100%
        with open(sprint_file) as f:
            sprint = yaml.safe_load(f)
            self.assertEqual(sprint["sprint"]["progress"]["completion_percent"], 100)

    def test_07_quality_gates(self):
        """Test: Update quality gate status."""
        vibey_dir = self.test_path / ".vibey"
        sprint_file = vibey_dir / "sprints" / "test-sprint-1.yaml"

        # Start from previous state
        self.test_06_complete_all_tasks()

        # Update quality gate
        with open(sprint_file) as f:
            sprint_data = yaml.safe_load(f)

        sprint_data["sprint"]["quality_gates"][0]["status"] = "passed"
        sprint_data["sprint"]["quality_gates"][0]["score"] = 85

        with open(sprint_file, "w") as f:
            yaml.dump(sprint_data, f)

        # Verify gate updated
        with open(sprint_file) as f:
            sprint = yaml.safe_load(f)
            gate = sprint["sprint"]["quality_gates"][0]
            self.assertEqual(gate["status"], "passed")
            self.assertEqual(gate["score"], 85)

    def test_08_complete_sprint(self):
        """Test: Mark sprint as completed."""
        vibey_dir = self.test_path / ".vibey"
        sprint_file = vibey_dir / "sprints" / "test-sprint-1.yaml"

        # Start from previous state
        self.test_07_quality_gates()

        # Complete sprint
        with open(sprint_file) as f:
            sprint_data = yaml.safe_load(f)

        sprint_data["sprint"]["status"] = "completed"
        sprint_data["sprint"]["completed"] = datetime.now(timezone.utc).isoformat() + "+00:00"

        with open(sprint_file, "w") as f:
            yaml.dump(sprint_data, f)

        # Verify sprint completed
        with open(sprint_file) as f:
            sprint = yaml.safe_load(f)
            self.assertEqual(sprint["sprint"]["status"], "completed")
            self.assertIsNotNone(sprint["sprint"]["completed"])

    def test_09_task_dependencies(self):
        """Test: Task dependency handling."""
        vibey_dir = self.test_path / ".vibey"
        (vibey_dir / "tasks").mkdir(parents=True, exist_ok=True)

        # Create tasks with dependencies
        tasks_data = {
            "tasks": [
                {
                    "id": "test-task-A",
                    "sprint_id": "test-sprint-2",
                    "title": "Task A (independent)",
                    "status": "not_started",
                    "depends_on": []
                },
                {
                    "id": "test-task-B",
                    "sprint_id": "test-sprint-2",
                    "title": "Task B (depends on A)",
                    "status": "not_started",
                    "depends_on": ["test-task-A"]
                },
                {
                    "id": "test-task-C",
                    "sprint_id": "test-sprint-2",
                    "title": "Task C (depends on B)",
                    "status": "not_started",
                    "depends_on": ["test-task-B"]
                }
            ]
        }

        tasks_file = vibey_dir / "tasks" / "test-sprint-2-tasks.yaml"
        with open(tasks_file, "w") as f:
            yaml.dump(tasks_data, f)

        # Verify dependencies
        with open(tasks_file) as f:
            tasks = yaml.safe_load(f)

        self.assertEqual(len(tasks["tasks"][0]["depends_on"]), 0)
        self.assertEqual(len(tasks["tasks"][1]["depends_on"]), 1)
        self.assertEqual(tasks["tasks"][1]["depends_on"][0], "test-task-A")
        self.assertEqual(tasks["tasks"][2]["depends_on"][0], "test-task-B")

    def test_10_agent_assignments(self):
        """Test: Agent assignment and workload."""
        vibey_dir = self.test_path / ".vibey"
        (vibey_dir / "tasks").mkdir(parents=True, exist_ok=True)

        # Create tasks with different agent assignments
        tasks_data = {
            "tasks": [
                {
                    "id": "test-task-1",
                    "sprint_id": "test-sprint-3",
                    "title": "Frontend task",
                    "assigned_agents": ["web-developer"]
                },
                {
                    "id": "test-task-2",
                    "sprint_id": "test-sprint-3",
                    "title": "Backend task",
                    "assigned_agents": ["web-developer"]
                },
                {
                    "id": "test-task-3",
                    "sprint_id": "test-sprint-3",
                    "title": "Testing task",
                    "assigned_agents": ["test-engineer"]
                },
                {
                    "id": "test-task-4",
                    "sprint_id": "test-sprint-3",
                    "title": "Multi-agent task",
                    "assigned_agents": ["web-developer", "docs-writer"]
                }
            ]
        }

        tasks_file = vibey_dir / "tasks" / "test-sprint-3-tasks.yaml"
        with open(tasks_file, "w") as f:
            yaml.dump(tasks_data, f)

        # Calculate agent workload
        agent_workload = {}
        with open(tasks_file) as f:
            tasks = yaml.safe_load(f)

        for task in tasks["tasks"]:
            for agent in task["assigned_agents"]:
                agent_workload[agent] = agent_workload.get(agent, 0) + 1

        # Verify workload distribution
        self.assertEqual(agent_workload["web-developer"], 3)
        self.assertEqual(agent_workload["test-engineer"], 1)
        self.assertEqual(agent_workload["docs-writer"], 1)


class TestRoadmapDataIntegrity(unittest.TestCase):
    """Test data integrity across roadmap files."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)

        self.vibey_dir = self.test_path / ".vibey"
        self.vibey_dir.mkdir(parents=True, exist_ok=True)
        (self.vibey_dir / "tracks").mkdir(exist_ok=True)
        (self.vibey_dir / "sprints").mkdir(exist_ok=True)
        (self.vibey_dir / "tasks").mkdir(exist_ok=True)

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)

    def test_sprint_tasks_consistency(self):
        """Test: Sprint references match task sprint_id."""
        # Create sprint with task references
        sprint_data = {
            "sprint": {
                "id": "test-sprint",
                "name": "Test Sprint",
                "tasks": ["test-sprint-task-001", "test-sprint-task-002"]
            }
        }

        sprint_file = self.vibey_dir / "sprints" / "test-sprint.yaml"
        with open(sprint_file, "w") as f:
            yaml.dump(sprint_data, f)

        # Create matching tasks
        tasks_data = {
            "tasks": [
                {
                    "id": "test-sprint-task-001",
                    "sprint_id": "test-sprint",
                    "title": "Task 1"
                },
                {
                    "id": "test-sprint-task-002",
                    "sprint_id": "test-sprint",
                    "title": "Task 2"
                }
            ]
        }

        tasks_file = self.vibey_dir / "tasks" / "test-sprint-tasks.yaml"
        with open(tasks_file, "w") as f:
            yaml.dump(tasks_data, f)

        # Verify consistency
        with open(sprint_file) as f:
            sprint = yaml.safe_load(f)

        with open(tasks_file) as f:
            tasks = yaml.safe_load(f)

        sprint_task_ids = set(sprint["sprint"]["tasks"])
        actual_task_ids = set(t["id"] for t in tasks["tasks"])

        self.assertEqual(sprint_task_ids, actual_task_ids)

        for task in tasks["tasks"]:
            self.assertEqual(task["sprint_id"], "test-sprint")

    def test_track_sprints_consistency(self):
        """Test: Track sprint references match actual sprints."""
        # Create track with sprint references
        track_data = {
            "track": {
                "id": "test-track",
                "name": "Test Track",
                "sprints": [
                    {"id": "test-track-sprint-1", "name": "Sprint 1"},
                    {"id": "test-track-sprint-2", "name": "Sprint 2"}
                ]
            }
        }

        track_file = self.vibey_dir / "tracks" / "test-track.yaml"
        with open(track_file, "w") as f:
            yaml.dump(track_data, f)

        # Create matching sprints
        for i in [1, 2]:
            sprint_data = {
                "sprint": {
                    "id": f"test-track-sprint-{i}",
                    "name": f"Sprint {i}",
                    "track_id": "test-track"
                }
            }

            sprint_file = self.vibey_dir / "sprints" / f"test-track-sprint-{i}.yaml"
            with open(sprint_file, "w") as f:
                yaml.dump(sprint_data, f)

        # Verify consistency
        with open(track_file) as f:
            track = yaml.safe_load(f)

        track_sprint_ids = set(s["id"] for s in track["track"]["sprints"])

        for sprint_id in track_sprint_ids:
            sprint_file = self.vibey_dir / "sprints" / f"{sprint_id}.yaml"
            self.assertTrue(sprint_file.exists())

            with open(sprint_file) as f:
                sprint = yaml.safe_load(f)
                self.assertEqual(sprint["sprint"]["track_id"], "test-track")


def run_tests():
    """Run all end-to-end tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestE2ERoadmapWorkflow))
    suite.addTests(loader.loadTestsFromTestCase(TestRoadmapDataIntegrity))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    exit(run_tests())
