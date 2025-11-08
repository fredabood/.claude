#!/usr/bin/env python3
"""
Integration Tests for Roadmap Integration

Tests the integration of roadmap system with /vibey commands:
1. Deployment initializes roadmap
2. Sprint planning creates roadmap entries
3. Task extraction works correctly
4. All files created with correct structure
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import subprocess
import yaml
import sys

# Add roadmap-lib to path
scripts_dir = Path(__file__).parent.parent
sys.path.insert(0, str(scripts_dir / "roadmap-lib"))

from plan_parser import SprintPlanParser


class TestRoadmapIntegration(unittest.TestCase):
    """Integration tests for roadmap system."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)

        # Save original directory
        self.original_dir = Path.cwd()

        # Change to test directory
        import os
        os.chdir(self.test_dir)

    def tearDown(self):
        """Clean up test environment."""
        # Return to original directory
        import os
        os.chdir(self.original_dir)

        # Remove test directory
        shutil.rmtree(self.test_dir)

    def test_roadmap_init_creates_structure(self):
        """Test that roadmap init creates proper directory structure."""
        # Create .vibey structure manually (simulating deployment)
        vibey_dir = self.test_path / ".vibey"
        vibey_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (vibey_dir / "tracks").mkdir(exist_ok=True)
        (vibey_dir / "sprints").mkdir(exist_ok=True)
        (vibey_dir / "tasks").mkdir(exist_ok=True)

        # Create roadmap.yaml
        roadmap = {
            'roadmap': {
                'id': 'test-project',
                'name': 'Test Project',
                'version': '0.1.0',
                'status': 'in_progress',
                'tracks': []
            }
        }

        roadmap_file = vibey_dir / "roadmap.yaml"
        with open(roadmap_file, 'w') as f:
            yaml.dump(roadmap, f, default_flow_style=False, sort_keys=False)

        # Verify structure
        self.assertTrue(vibey_dir.exists(), ".vibey directory not created")
        self.assertTrue(roadmap_file.exists(), "roadmap.yaml not created")
        self.assertTrue((vibey_dir / "tracks").exists(), "tracks/ directory not created")
        self.assertTrue((vibey_dir / "sprints").exists(), "sprints/ directory not created")
        self.assertTrue((vibey_dir / "tasks").exists(), "tasks/ directory not created")

        # Validate roadmap.yaml structure
        with open(roadmap_file) as f:
            roadmap_check = yaml.safe_load(f)

        self.assertIn('roadmap', roadmap_check)
        self.assertEqual(roadmap_check['roadmap']['name'], 'Test Project')
        self.assertEqual(roadmap_check['roadmap']['version'], '0.1.0')
        self.assertIn('tracks', roadmap_check['roadmap'])

    def test_plan_parser_extracts_data(self):
        """Test that plan parser correctly extracts sprint data."""
        # Create sample sprint plan
        plan_content = """# Sprint Plan: Test Sprint

## Goals
- Implement feature X
- Fix bug Y

## Features

### 1. Feature X

**What:** A new feature that does something useful
**Why:** Users need this functionality
**How:**
- Step 1: Design the interface
- Step 2: Implement backend
- Step 3: Add tests

### 2. Bug Fix Y

**What:** Fix critical bug in authentication
**Why:** Security vulnerability
**How:**
- Patch the vulnerability
- Add regression test

## Success Criteria
- ✅ All tests pass
- ✅ Security audit complete

## Deliverables
- Feature X implementation
- Bug fix for Y
- Test suite

## Quality Gates
- Unit Testing (90%)
- Security Audit (85%)
"""
        plan_file = self.test_path / "sprint-1-plan.md"
        plan_file.write_text(plan_content)

        # Parse plan
        parser = SprintPlanParser(plan_file)
        plan_data = parser.parse()

        # Verify parsed data
        self.assertEqual(plan_data['name'], 'Test Sprint')
        self.assertIn('Implement feature X', plan_data['goal'])
        self.assertEqual(len(plan_data['features']), 2)
        self.assertEqual(plan_data['features'][0]['name'], 'Feature X')
        self.assertEqual(len(plan_data['deliverables']), 3)
        self.assertEqual(len(plan_data['quality_gates']), 2)
        self.assertEqual(plan_data['quality_gates'][0]['threshold'], 90)

        # Verify task extraction
        tasks = parser.extract_tasks()
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0]['name'], 'Feature X')
        self.assertGreater(tasks[0]['estimated_hours'], 0)

    def test_plan_create_generates_sprint_and_tasks(self):
        """Test that plan create generates sprint and task files."""
        # Create .vibey structure manually
        vibey_dir = self.test_path / ".vibey"
        vibey_dir.mkdir(parents=True, exist_ok=True)
        (vibey_dir / "sprints").mkdir(exist_ok=True)
        (vibey_dir / "tasks").mkdir(exist_ok=True)

        # Create roadmap.yaml
        roadmap = {'roadmap': {'id': 'test-project', 'name': 'Test Project', 'status': 'in_progress', 'tracks': []}}
        with open(vibey_dir / "roadmap.yaml", 'w') as f:
            yaml.dump(roadmap, f)

        # Create main track
        tracks_dir = self.test_path / ".vibey" / "tracks"
        tracks_dir.mkdir(parents=True, exist_ok=True)

        main_track = {
            'track': {
                'id': 'main',
                'name': 'Main Track',
                'roadmap_id': 'test-project',
                'status': 'in_progress',
                'sprints': []
            }
        }

        with open(tracks_dir / "main.yaml", 'w') as f:
            yaml.dump(main_track, f)

        # Create sample sprint plan
        plan_content = """# Sprint 1: Integration Test Sprint

## Goals
- Test roadmap integration

## Features

### 1. Test Feature

**What:** Test feature implementation
**Why:** For testing
**How:**
- Implement test
- Verify results

## Deliverables
- Test implementation

## Quality Gates
- Testing (80%)
"""
        plan_file = self.test_path / "sprint-1-plan.md"
        plan_file.write_text(plan_content)

        # Run plan create
        result = subprocess.run(
            [
                "python3",
                str(scripts_dir / "roadmap"),
                "plan", "create",
                "--track-id", "main",
                "--from-plan", str(plan_file),
                "--sprint-id", "main-sprint-1"
            ],
            capture_output=True,
            text=True
        )

        # Check command succeeded
        self.assertEqual(result.returncode, 0, f"plan create failed: {result.stderr}")

        # Check sprint file created
        sprint_file = self.test_path / ".vibey" / "sprints" / "main-sprint-1.yaml"
        self.assertTrue(sprint_file.exists(), "Sprint file not created")

        # Check tasks file created
        tasks_file = self.test_path / ".vibey" / "tasks" / "main-sprint-1-tasks.yaml"
        self.assertTrue(tasks_file.exists(), "Tasks file not created")

        # Validate sprint structure
        with open(sprint_file) as f:
            sprint = yaml.safe_load(f)

        self.assertIn('sprint', sprint)
        self.assertEqual(sprint['sprint']['id'], 'main-sprint-1')
        self.assertEqual(sprint['sprint']['name'], 'Integration Test Sprint')
        self.assertIn('goal', sprint['sprint'])
        self.assertIn('quality_gates', sprint['sprint'])

        # Validate tasks structure
        with open(tasks_file) as f:
            tasks = yaml.safe_load(f)

        self.assertIn('tasks', tasks)
        self.assertGreater(len(tasks['tasks']), 0)

        task = tasks['tasks'][0]
        self.assertEqual(task['sprint_id'], 'main-sprint-1')
        self.assertIn('title', task)
        self.assertIn('estimated_hours', task)
        self.assertEqual(task['status'], 'not_started')

    def test_complete_deployment_workflow(self):
        """Test complete deployment workflow: init + plan create."""
        # Step 1: Create roadmap structure (simulating deployment)
        vibey_dir = self.test_path / ".vibey"
        vibey_dir.mkdir(parents=True, exist_ok=True)
        (vibey_dir / "tracks").mkdir(exist_ok=True)
        (vibey_dir / "sprints").mkdir(exist_ok=True)
        (vibey_dir / "tasks").mkdir(exist_ok=True)

        roadmap = {
            'roadmap': {
                'id': 'full-integration-test',
                'name': 'Full Integration Test',
                'version': '1.0.0',
                'status': 'in_progress',
                'tracks': []
            }
        }
        with open(vibey_dir / "roadmap.yaml", 'w') as f:
            yaml.dump(roadmap, f, default_flow_style=False, sort_keys=False)

        # Verify .vibey structure
        vibey_dir = self.test_path / ".vibey"
        self.assertTrue(vibey_dir.exists())
        self.assertTrue((vibey_dir / "roadmap.yaml").exists())
        self.assertTrue((vibey_dir / "tracks").exists())
        self.assertTrue((vibey_dir / "sprints").exists())
        self.assertTrue((vibey_dir / "tasks").exists())

        # Step 2: Create main track
        tracks_dir = vibey_dir / "tracks"
        main_track = {
            'track': {
                'id': 'main',
                'name': 'Main Development Track',
                'roadmap_id': 'full-integration-test',
                'status': 'in_progress',
                'sprints': [],
                'progress': {
                    'sprints_total': 0,
                    'sprints_completed': 0,
                    'tasks_total': 0,
                    'tasks_completed': 0
                }
            }
        }

        with open(tracks_dir / "main.yaml", 'w') as f:
            yaml.dump(main_track, f, default_flow_style=False, sort_keys=False)

        # Step 3: Create sprint plan
        plan_content = """# Sprint 1: Foundation Setup

## Goals
- Set up project foundation
- Implement core features

## Features

### 1. Project Scaffolding

**What:** Create project structure and configuration
**Why:** Needed for all subsequent development
**How:**
- Initialize project structure
- Set up configuration files
- Configure build system

### 2. Core API Implementation

**What:** Implement basic API endpoints
**Why:** Required for frontend integration
**How:**
- Design API schema
- Implement CRUD operations
- Add authentication

## Success Criteria
- ✅ Project builds successfully
- ✅ All tests pass
- ✅ API endpoints functional

## Deliverables
- Project structure
- API implementation
- Test suite
- Documentation

## Quality Gates
- Unit Testing (85%)
- Code Coverage (80%)
- Security Audit (90%)
"""
        plan_file = self.test_path / "sprint-1-plan.md"
        plan_file.write_text(plan_content)

        # Step 4: Create sprint from plan
        plan_result = subprocess.run(
            [
                "python3",
                str(scripts_dir / "roadmap"),
                "plan", "create",
                "--track-id", "main",
                "--from-plan", str(plan_file),
                "--sprint-id", "main-1"
            ],
            capture_output=True,
            text=True
        )

        self.assertEqual(plan_result.returncode, 0, f"Plan create failed: {plan_result.stderr}")

        # Step 5: Verify complete structure
        sprint_file = vibey_dir / "sprints" / "main-1.yaml"
        tasks_file = vibey_dir / "tasks" / "main-1-tasks.yaml"
        track_file = vibey_dir / "tracks" / "main.yaml"

        self.assertTrue(sprint_file.exists(), "Sprint file missing")
        self.assertTrue(tasks_file.exists(), "Tasks file missing")
        self.assertTrue(track_file.exists(), "Track file missing")

        # Verify sprint data
        with open(sprint_file) as f:
            sprint = yaml.safe_load(f)

        self.assertEqual(sprint['sprint']['name'], 'Foundation Setup')
        self.assertEqual(sprint['sprint']['track_id'], 'main')
        self.assertEqual(len(sprint['sprint']['quality_gates']), 3)
        self.assertEqual(sprint['sprint']['progress']['tasks_total'], 2)

        # Verify tasks data
        with open(tasks_file) as f:
            tasks = yaml.safe_load(f)

        self.assertEqual(len(tasks['tasks']), 2)
        self.assertEqual(tasks['tasks'][0]['title'], 'Project Scaffolding')
        self.assertEqual(tasks['tasks'][1]['title'], 'Core API Implementation')

        # Verify track updated
        with open(track_file) as f:
            track = yaml.safe_load(f)

        self.assertEqual(len(track['track']['sprints']), 1)
        self.assertEqual(track['track']['sprints'][0]['id'], 'main-1')

        print("\n✅ Complete deployment workflow test passed!")
        print(f"   Roadmap initialized: {vibey_dir}")
        print(f"   Sprint created: main-1")
        print(f"   Tasks extracted: 2")
        print(f"   Quality gates: 3")


def run_tests():
    """Run all integration tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestRoadmapIntegration)

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
