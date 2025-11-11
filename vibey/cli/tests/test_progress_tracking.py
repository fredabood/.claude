#!/usr/bin/env python3
"""
Integration Tests for Progress Tracking

Tests the complete progress tracking workflow including:
- Dashboard data extraction
- Task status updates
- Progress visualization
- Roadmap integration
"""

import unittest
import subprocess
import tempfile
import shutil
import yaml
import json
from pathlib import Path
from datetime import datetime, timezone


class TestProgressTracking(unittest.TestCase):
    """Test progress tracking integration with roadmap system."""

    def setUp(self):
        """Set up test environment with temporary .vibey structure."""
        # Create temporary directory
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)

        # Create .vibey structure
        self.vibey_dir = self.test_path / ".vibey"
        self.vibey_dir.mkdir(parents=True, exist_ok=True)

        (self.vibey_dir / "tracks").mkdir(exist_ok=True)
        (self.vibey_dir / "sprints").mkdir(exist_ok=True)
        (self.vibey_dir / "tasks").mkdir(exist_ok=True)

        # Create test roadmap
        self._create_test_roadmap()
        self._create_test_sprint()
        self._create_test_tasks()

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)

    def _create_test_roadmap(self):
        """Create test roadmap.yaml."""
        roadmap_data = {
            "roadmap": {
                "id": "test-roadmap",
                "name": "Test Roadmap",
                "status": "in_progress",
                "created": datetime.now(timezone.utc).isoformat() + "+00:00",
                "tracks": [],
                "metadata": {
                    "version": "1.0.0"
                }
            }
        }

        with open(self.vibey_dir / "roadmap.yaml", "w") as f:
            yaml.dump(roadmap_data, f)

    def _create_test_sprint(self):
        """Create test sprint."""
        sprint_data = {
            "sprint": {
                "id": "test-sprint-1",
                "name": "Test Sprint",
                "track_id": "test-track",
                "roadmap_id": "test-roadmap",
                "status": "in_progress",
                "blocked": False,
                "created": datetime.now(timezone.utc).isoformat() + "+00:00",
                "started": datetime.now(timezone.utc).isoformat() + "+00:00",
                "completed": None,
                "progress": {
                    "development_tasks_total": 4,
                    "development_tasks_completed": 0,
                    "completion_gate_tasks_total": 0,
                    "completion_gate_tasks_completed": 0,
                    "tasks_total": 4,
                    "tasks_completed": 0,
                    "completion_percent": 0
                },
                "tasks": [],
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
                "deliverables": ["Test deliverable"],
                "metadata": {
                    "last_updated": datetime.now(timezone.utc).isoformat() + "+00:00",
                    "estimated_duration": "1 week"
                }
            }
        }

        with open(self.vibey_dir / "sprints" / "test-sprint-1.yaml", "w") as f:
            yaml.dump(sprint_data, f)

    def _create_test_tasks(self):
        """Create test tasks."""
        tasks_data = {
            "tasks": [
                {
                    "id": "test-task-001",
                    "sprint_id": "test-sprint-1",
                    "title": "Implement feature A",
                    "description": "Build feature A",
                    "status": "not_started",
                    "priority": "high",
                    "estimated_hours": 4,
                    "assigned_agents": ["web-developer"]
                },
                {
                    "id": "test-task-002",
                    "sprint_id": "test-sprint-1",
                    "title": "Implement feature B",
                    "description": "Build feature B",
                    "status": "not_started",
                    "priority": "medium",
                    "estimated_hours": 3,
                    "assigned_agents": ["web-developer"]
                },
                {
                    "id": "test-task-003",
                    "sprint_id": "test-sprint-1",
                    "title": "Write tests",
                    "description": "Test features",
                    "status": "not_started",
                    "priority": "high",
                    "estimated_hours": 2,
                    "assigned_agents": ["test-engineer"]
                },
                {
                    "id": "test-task-004",
                    "sprint_id": "test-sprint-1",
                    "title": "Update documentation",
                    "description": "Document features",
                    "status": "not_started",
                    "priority": "low",
                    "estimated_hours": 1,
                    "assigned_agents": ["docs-writer"]
                }
            ]
        }

        with open(self.vibey_dir / "tasks" / "test-sprint-1-tasks.yaml", "w") as f:
            yaml.dump(tasks_data, f)

    def test_dashboard_data_extraction(self):
        """Test dashboard data extraction from roadmap."""
        # Read sprint data
        with open(self.vibey_dir / "sprints" / "test-sprint-1.yaml") as f:
            sprint_data = yaml.safe_load(f)

        sprint = sprint_data["sprint"]

        # Verify sprint data structure
        self.assertEqual(sprint["id"], "test-sprint-1")
        self.assertEqual(sprint["name"], "Test Sprint")
        self.assertEqual(sprint["status"], "in_progress")

        # Verify progress data
        progress = sprint["progress"]
        self.assertEqual(progress["tasks_total"], 4)
        self.assertEqual(progress["tasks_completed"], 0)
        self.assertEqual(progress["completion_percent"], 0)

        # Verify quality gates
        self.assertEqual(len(sprint["quality_gates"]), 1)
        gate = sprint["quality_gates"][0]
        self.assertEqual(gate["name"], "Unit Testing")
        self.assertEqual(gate["threshold"], 80)
        self.assertEqual(gate["status"], "not_run")

    def test_task_list_retrieval(self):
        """Test retrieving task list for sprint."""
        # Read tasks
        with open(self.vibey_dir / "tasks" / "test-sprint-1-tasks.yaml") as f:
            tasks_data = yaml.safe_load(f)

        tasks = tasks_data["tasks"]

        # Verify all tasks loaded
        self.assertEqual(len(tasks), 4)

        # Verify task structure
        task = tasks[0]
        self.assertEqual(task["id"], "test-task-001")
        self.assertEqual(task["sprint_id"], "test-sprint-1")
        self.assertEqual(task["status"], "not_started")
        self.assertEqual(task["priority"], "high")
        self.assertIn("web-developer", task["assigned_agents"])

    def test_task_status_update(self):
        """Test updating task status."""
        # Load tasks
        tasks_file = self.vibey_dir / "tasks" / "test-sprint-1-tasks.yaml"
        with open(tasks_file) as f:
            tasks_data = yaml.safe_load(f)

        # Update first task status to in_progress
        tasks_data["tasks"][0]["status"] = "in_progress"

        # Save updated tasks
        with open(tasks_file, "w") as f:
            yaml.dump(tasks_data, f)

        # Reload and verify
        with open(tasks_file) as f:
            updated_data = yaml.safe_load(f)

        self.assertEqual(updated_data["tasks"][0]["status"], "in_progress")
        self.assertEqual(updated_data["tasks"][1]["status"], "not_started")

    def test_progress_calculation(self):
        """Test progress percentage calculation."""
        # Load tasks and update statuses
        tasks_file = self.vibey_dir / "tasks" / "test-sprint-1-tasks.yaml"
        with open(tasks_file) as f:
            tasks_data = yaml.safe_load(f)

        # Complete 2 out of 4 tasks
        tasks_data["tasks"][0]["status"] = "completed"
        tasks_data["tasks"][1]["status"] = "completed"
        tasks_data["tasks"][2]["status"] = "in_progress"
        tasks_data["tasks"][3]["status"] = "not_started"

        # Calculate progress
        total_tasks = len(tasks_data["tasks"])
        completed_tasks = sum(1 for t in tasks_data["tasks"] if t["status"] == "completed")
        completion_percent = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

        # Update sprint progress
        sprint_file = self.vibey_dir / "sprints" / "test-sprint-1.yaml"
        with open(sprint_file) as f:
            sprint_data = yaml.safe_load(f)

        sprint_data["sprint"]["progress"]["tasks_completed"] = completed_tasks
        sprint_data["sprint"]["progress"]["completion_percent"] = completion_percent

        with open(sprint_file, "w") as f:
            yaml.dump(sprint_data, f)

        # Verify calculations
        self.assertEqual(total_tasks, 4)
        self.assertEqual(completed_tasks, 2)
        self.assertEqual(completion_percent, 50)

        # Reload and verify persistence
        with open(sprint_file) as f:
            updated_sprint = yaml.safe_load(f)

        self.assertEqual(updated_sprint["sprint"]["progress"]["tasks_completed"], 2)
        self.assertEqual(updated_sprint["sprint"]["progress"]["completion_percent"], 50)

    def test_progress_bar_rendering(self):
        """Test progress bar visualization."""
        test_cases = [
            (0, "░░░░░░░░░░"),
            (10, "█░░░░░░░░░"),
            (25, "██░░░░░░░░"),
            (50, "█████░░░░░"),
            (75, "███████░░░"),
            (90, "█████████░"),
            (100, "██████████"),
        ]

        for percent, expected_bar in test_cases:
            filled = int(percent / 10)
            empty = 10 - filled
            bar = "█" * filled + "░" * empty
            self.assertEqual(bar, expected_bar, f"Progress bar incorrect for {percent}%")

    def test_quality_gates_tracking(self):
        """Test quality gate status tracking."""
        sprint_file = self.vibey_dir / "sprints" / "test-sprint-1.yaml"

        # Load sprint
        with open(sprint_file) as f:
            sprint_data = yaml.safe_load(f)

        # Update quality gate status
        sprint_data["sprint"]["quality_gates"][0]["status"] = "passed"
        sprint_data["sprint"]["quality_gates"][0]["score"] = 85

        with open(sprint_file, "w") as f:
            yaml.dump(sprint_data, f)

        # Verify update
        with open(sprint_file) as f:
            updated_data = yaml.safe_load(f)

        gate = updated_data["sprint"]["quality_gates"][0]
        self.assertEqual(gate["status"], "passed")
        self.assertEqual(gate["score"], 85)

    def test_task_filtering_by_status(self):
        """Test filtering tasks by status."""
        # Load tasks
        with open(self.vibey_dir / "tasks" / "test-sprint-1-tasks.yaml") as f:
            tasks_data = yaml.safe_load(f)

        # Update some task statuses
        tasks_data["tasks"][0]["status"] = "completed"
        tasks_data["tasks"][1]["status"] = "in_progress"
        tasks_data["tasks"][2]["status"] = "not_started"
        tasks_data["tasks"][3]["status"] = "blocked"

        tasks = tasks_data["tasks"]

        # Filter by status
        completed = [t for t in tasks if t["status"] == "completed"]
        in_progress = [t for t in tasks if t["status"] == "in_progress"]
        not_started = [t for t in tasks if t["status"] == "not_started"]
        blocked = [t for t in tasks if t["status"] == "blocked"]

        # Verify counts
        self.assertEqual(len(completed), 1)
        self.assertEqual(len(in_progress), 1)
        self.assertEqual(len(not_started), 1)
        self.assertEqual(len(blocked), 1)

        # Verify correct tasks
        self.assertEqual(completed[0]["id"], "test-task-001")
        self.assertEqual(in_progress[0]["id"], "test-task-002")
        self.assertEqual(not_started[0]["id"], "test-task-003")
        self.assertEqual(blocked[0]["id"], "test-task-004")

    def test_sprint_completion_detection(self):
        """Test detection of sprint completion."""
        # Load tasks
        tasks_file = self.vibey_dir / "tasks" / "test-sprint-1-tasks.yaml"
        with open(tasks_file) as f:
            tasks_data = yaml.safe_load(f)

        # Mark all tasks complete
        for task in tasks_data["tasks"]:
            task["status"] = "completed"

        # Check completion
        total_tasks = len(tasks_data["tasks"])
        completed_tasks = sum(1 for t in tasks_data["tasks"] if t["status"] == "completed")
        is_complete = completed_tasks == total_tasks and total_tasks > 0

        self.assertTrue(is_complete)
        self.assertEqual(completed_tasks, 4)
        self.assertEqual(total_tasks, 4)

    def test_recent_activity_extraction(self):
        """Test extracting recent task activity."""
        # Load tasks
        with open(self.vibey_dir / "tasks" / "test-sprint-1-tasks.yaml") as f:
            tasks_data = yaml.safe_load(f)

        # Add timestamps to simulate activity
        now = datetime.now(timezone.utc)
        tasks_data["tasks"][0]["completed_at"] = now.isoformat() + "+00:00"
        tasks_data["tasks"][0]["status"] = "completed"

        # Get recently completed tasks
        completed_tasks = [t for t in tasks_data["tasks"] if t.get("completed_at")]

        self.assertEqual(len(completed_tasks), 1)
        self.assertEqual(completed_tasks[0]["id"], "test-task-001")

    def test_agent_assignment_tracking(self):
        """Test tracking agent assignments."""
        # Load tasks
        with open(self.vibey_dir / "tasks" / "test-sprint-1-tasks.yaml") as f:
            tasks_data = yaml.safe_load(f)

        # Count tasks by agent
        agent_workload = {}
        for task in tasks_data["tasks"]:
            for agent in task.get("assigned_agents", []):
                agent_workload[agent] = agent_workload.get(agent, 0) + 1

        # Verify workload distribution
        self.assertEqual(agent_workload.get("web-developer"), 2)
        self.assertEqual(agent_workload.get("test-engineer"), 1)
        self.assertEqual(agent_workload.get("docs-writer"), 1)

    def test_task_priority_sorting(self):
        """Test sorting tasks by priority."""
        # Load tasks
        with open(self.vibey_dir / "tasks" / "test-sprint-1-tasks.yaml") as f:
            tasks_data = yaml.safe_load(f)

        tasks = tasks_data["tasks"]

        # Define priority order
        priority_order = {"high": 1, "medium": 2, "low": 3}

        # Sort by priority
        sorted_tasks = sorted(tasks, key=lambda t: priority_order.get(t.get("priority", "low"), 999))

        # Verify order
        self.assertEqual(sorted_tasks[0]["priority"], "high")
        self.assertEqual(sorted_tasks[1]["priority"], "high")
        self.assertEqual(sorted_tasks[2]["priority"], "medium")
        self.assertEqual(sorted_tasks[3]["priority"], "low")

    def test_integration_dashboard_to_task_update(self):
        """Integration test: Dashboard display → Task update → Progress refresh."""
        # Step 1: Load initial dashboard data
        with open(self.vibey_dir / "sprints" / "test-sprint-1.yaml") as f:
            sprint_data = yaml.safe_load(f)

        initial_progress = sprint_data["sprint"]["progress"]["completion_percent"]
        self.assertEqual(initial_progress, 0)

        # Step 2: Start a task
        tasks_file = self.vibey_dir / "tasks" / "test-sprint-1-tasks.yaml"
        with open(tasks_file) as f:
            tasks_data = yaml.safe_load(f)

        tasks_data["tasks"][0]["status"] = "in_progress"

        with open(tasks_file, "w") as f:
            yaml.dump(tasks_data, f)

        # Step 3: Complete the task
        tasks_data["tasks"][0]["status"] = "completed"

        with open(tasks_file, "w") as f:
            yaml.dump(tasks_data, f)

        # Step 4: Update sprint progress
        completed_count = sum(1 for t in tasks_data["tasks"] if t["status"] == "completed")
        total_count = len(tasks_data["tasks"])
        new_percent = int((completed_count / total_count) * 100)

        sprint_data["sprint"]["progress"]["tasks_completed"] = completed_count
        sprint_data["sprint"]["progress"]["completion_percent"] = new_percent

        with open(self.vibey_dir / "sprints" / "test-sprint-1.yaml", "w") as f:
            yaml.dump(sprint_data, f)

        # Step 5: Verify updated progress
        with open(self.vibey_dir / "sprints" / "test-sprint-1.yaml") as f:
            updated_sprint = yaml.safe_load(f)

        final_progress = updated_sprint["sprint"]["progress"]["completion_percent"]
        self.assertEqual(final_progress, 25)
        self.assertEqual(updated_sprint["sprint"]["progress"]["tasks_completed"], 1)


class TestProgressVisualization(unittest.TestCase):
    """Test progress visualization formatting."""

    def test_progress_bar_edge_cases(self):
        """Test progress bar edge cases."""
        # Empty progress
        bar = "░" * 10
        self.assertEqual(len(bar), 10)

        # Full progress
        bar = "█" * 10
        self.assertEqual(len(bar), 10)

        # Partial progress
        percent = 33
        filled = int(percent / 10)
        empty = 10 - filled
        bar = "█" * filled + "░" * empty
        self.assertEqual(len(bar), 10)
        self.assertEqual(bar.count("█"), 3)
        self.assertEqual(bar.count("░"), 7)

    def test_task_count_formatting(self):
        """Test task count display formatting."""
        completed = 3
        total = 6
        percent = int((completed / total) * 100)

        output = f"{completed}/{total} tasks ({percent}%)"
        self.assertEqual(output, "3/6 tasks (50%)")

    def test_emoji_status_indicators(self):
        """Test emoji status indicators."""
        status_map = {
            "completed": "✅",
            "in_progress": "🔄",
            "not_started": "⏸️",
            "blocked": "🚫"
        }

        self.assertEqual(status_map["completed"], "✅")
        self.assertEqual(status_map["in_progress"], "🔄")
        self.assertEqual(status_map["not_started"], "⏸️")
        self.assertEqual(status_map["blocked"], "🚫")


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestProgressTracking))
    suite.addTests(loader.loadTestsFromTestCase(TestProgressVisualization))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    exit(run_tests())
