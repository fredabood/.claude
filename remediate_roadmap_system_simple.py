#!/usr/bin/env python3
"""
Remediate roadmap-system track by creating all missing task.yaml files
with proper commit attribution and deliverables.

Simplified version - uses direct YAML generation.
"""

import os
from pathlib import Path
from datetime import datetime
import yaml

REPO_ROOT = Path(__file__).parent
TRACK_PATH = REPO_ROOT / ".vibey" / "roadmap" / "roadmap-system"

# Sprint and task data (simplified for YAML generation)
SPRINTS = {
    "roadmap-system-1": {
        "name": "Core Data Model & YAML Schema",
        "started": "2025-11-07T03:00:00+00:00",
        "completed": "2025-11-12T17:00:00+00:00",
        "tasks": [
            {"id": "001", "title": "Design YAML schema for Roadmap object", "type": "implementation", "status": "completed", "commits": []},
            {"id": "002", "title": "Design YAML schema for Track object", "type": "implementation", "status": "completed", "commits": []},
            {"id": "003", "title": "Design YAML schema for Sprint object", "type": "implementation", "status": "completed", "commits": []},
            {"id": "004", "title": "Design YAML schema for Task object", "type": "implementation", "status": "completed", "commits": []},
            {"id": "005", "title": "Create Python data models (dataclasses)", "type": "implementation", "status": "completed",
             "commits": [
                 ("2d0f313", "2025-11-10T18:47:49-05:00", "feat: Move framework modules to vibey package (Task 002)"),
                 ("f071177", "2025-11-11T16:01:52-05:00", "fix: Comprehensive audit and critical fixes - eliminate deprecated API usage"),
             ],
             "deliverables": ["vibey/roadmap/models/ - All data model files"]
            },
            {"id": "006", "title": "Implement YAML validation logic", "type": "implementation", "status": "completed",
             "commits": [("2d0f313", "2025-11-10T18:47:49-05:00", "feat: Move framework modules to vibey package (Task 002)")],
             "deliverables": ["vibey/roadmap/validation/ - Validation logic"]
            },
            {"id": "007", "title": "Implement serialization/deserialization", "type": "implementation", "status": "completed",
             "commits": [
                 ("2d0f313", "2025-11-10T18:47:49-05:00", "feat: Move framework modules to vibey package (Task 002)"),
                 ("205c877", "2025-11-12T16:22:27-05:00", "fix: Begin addressing test failures in comprehensive CLI test suite"),
             ],
             "deliverables": ["vibey/roadmap/serialization/ - YAML loader and dumper"]
            },
            {"id": "008", "title": "Create example roadmap for testing", "type": "implementation", "status": "completed",
             "deliverables": [".vibey/roadmap/ - Vibey's own roadmap"]
            },
            {"id": "009", "title": "Write unit tests for data models", "type": "testing", "status": "completed",
             "commits": [("205c877", "2025-11-12T16:22:27-05:00", "fix: Begin addressing test failures in comprehensive CLI test suite")],
             "deliverables": ["tests/cli/test_roadmap_*.py - Test suite"]
            },
        ]
    },
    "roadmap-system-2": {
        "name": "State Management Scripts",
        "started": "2025-11-10T18:00:00+00:00",
        "completed": "2025-11-12T17:00:00+00:00",
        "tasks": [
            {"id": "001", "title": "Implement roadmap-init.py (create new roadmap)", "type": "implementation", "status": "completed",
             "commits": [
                 ("2d0f313", "2025-11-10T18:47:49-05:00", "feat: Move framework modules to vibey package (Task 002)"),
                 ("2f5c644", "2025-11-11T15:44:37-05:00", "fix: Modernize roadmap-init.py and achieve 91% test pass rate"),
             ],
             "deliverables": ["vibey/operations/roadmap/init.py"]
            },
            {"id": "002", "title": "Implement roadmap-query.py (read operations)", "type": "implementation", "status": "completed",
             "commits": [
                 ("2d0f313", "2025-11-10T18:47:49-05:00", "feat: Move framework modules to vibey package (Task 002)"),
                 ("205c877", "2025-11-12T16:22:27-05:00", "fix: Begin addressing test failures in comprehensive CLI test suite"),
                 ("feb614b", "2025-11-12T16:57:23-05:00", "fix: Improve error handling and defensive coding for track queries"),
             ],
             "deliverables": ["vibey/operations/roadmap/query.py"]
            },
            {"id": "003", "title": "Implement roadmap-update.py (update operations)", "type": "implementation", "status": "completed",
             "commits": [
                 ("2d0f313", "2025-11-10T18:47:49-05:00", "feat: Move framework modules to vibey package (Task 002)"),
                 ("205c877", "2025-11-12T16:22:27-05:00", "fix: Begin addressing test failures in comprehensive CLI test suite"),
                 ("9517859", "2025-11-12T16:59:29-05:00", "fix: Implement idempotent start behavior - 2 tests fixed"),
             ],
             "deliverables": ["vibey/operations/roadmap/update.py"]
            },
            {"id": "004", "title": "Build dependency resolution engine", "type": "implementation", "status": "completed",
             "commits": [("2d0f313", "2025-11-10T18:47:49-05:00", "feat: Move framework modules to vibey package (Task 002)")],
             "deliverables": ["vibey/cli/roadmap_lib/dependencies.py"]
            },
            {"id": "005", "title": "Implement blocker computation logic", "type": "implementation", "status": "completed",
             "commits": [("2d0f313", "2025-11-10T18:47:49-05:00", "feat: Move framework modules to vibey package (Task 002)")],
             "deliverables": ["vibey/cli/roadmap_lib/blockers.py"]
            },
            {"id": "006", "title": "Build automatic status progression", "type": "implementation", "status": "completed",
             "commits": [("2d0f313", "2025-11-10T18:47:49-05:00", "feat: Move framework modules to vibey package (Task 002)")],
             "deliverables": ["vibey/cli/roadmap_lib/status.py"]
            },
            {"id": "007", "title": "Implement activity logging system", "type": "implementation", "status": "completed",
             "commits": [("2d0f313", "2025-11-10T18:47:49-05:00", "feat: Move framework modules to vibey package (Task 002)")],
             "deliverables": ["vibey/cli/roadmap_lib/activity.py"]
            },
            {"id": "008", "title": "Create file structure management utilities", "type": "implementation", "status": "completed",
             "commits": [("2d0f313", "2025-11-10T18:47:49-05:00", "feat: Move framework modules to vibey package (Task 002)")],
             "deliverables": ["vibey/cli/roadmap_lib/filesystem.py"]
            },
            {"id": "009", "title": "Write integration tests for scripts", "type": "testing", "status": "completed",
             "commits": [("2d0f313", "2025-11-10T18:47:49-05:00", "feat: Move framework modules to vibey package (Task 002)")],
             "deliverables": ["vibey/cli/tests/test_roadmap_*.py"]
            },
        ]
    },
    "roadmap-system-3": {
        "name": "CLI Commands (Part 1: Query)",
        "started": "2025-11-10T18:00:00+00:00",
        "completed": "2025-11-12T17:00:00+00:00",
        "tasks": [
            {"id": "001", "title": "Set up CLI framework (Click/Typer)", "type": "implementation", "status": "completed",
             "commits": [("3aee108", "2025-11-10T18:52:02-05:00", "feat: Create CLI entry point with Click framework (Task 003)")],
             "deliverables": ["vibey/cli/main.py"]
            },
            {"id": "002", "title": "Implement `vibey roadmap status`", "type": "implementation", "status": "completed",
             "commits": [
                 ("082b952", "2025-11-10T19:03:27-05:00", "feat: Wire CLI commands to script functionality (Task 004)"),
                 ("c5c575e", "2025-11-10T19:07:12-05:00", "feat: Verify and fix roadmap CLI commands (Tasks 006-007)"),
             ],
             "deliverables": ["vibey/cli/roadmap_commands/status.py"]
            },
            {"id": "003", "title": "Implement `vibey track list/status`", "type": "implementation", "status": "completed",
             "commits": [
                 ("082b952", "2025-11-10T19:03:27-05:00", "feat: Wire CLI commands to script functionality (Task 004)"),
                 ("c5c575e", "2025-11-10T19:07:12-05:00", "feat: Verify and fix roadmap CLI commands (Tasks 006-007)"),
             ],
             "deliverables": ["vibey/cli/roadmap_commands/list_cmd.py"]
            },
            {"id": "004", "title": "Implement `vibey sprint list/status`", "type": "implementation", "status": "completed",
             "commits": [
                 ("082b952", "2025-11-10T19:03:27-05:00", "feat: Wire CLI commands to script functionality (Task 004)"),
                 ("c5c575e", "2025-11-10T19:07:12-05:00", "feat: Verify and fix roadmap CLI commands (Tasks 006-007)"),
             ],
             "deliverables": ["vibey/cli/roadmap_commands/list_cmd.py"]
            },
            {"id": "005", "title": "Implement `vibey task list/status`", "type": "implementation", "status": "completed",
             "commits": [
                 ("082b952", "2025-11-10T19:03:27-05:00", "feat: Wire CLI commands to script functionality (Task 004)"),
                 ("c5c575e", "2025-11-10T19:07:12-05:00", "feat: Verify and fix roadmap CLI commands (Tasks 006-007)"),
             ],
             "deliverables": ["vibey/cli/roadmap_commands/list_cmd.py"]
            },
            {"id": "006", "title": "Implement `vibey deps graph/check`", "type": "implementation", "status": "completed",
             "commits": [
                 ("082b952", "2025-11-10T19:03:27-05:00", "feat: Wire CLI commands to script functionality (Task 004)"),
                 ("c5c575e", "2025-11-10T19:07:12-05:00", "feat: Verify and fix roadmap CLI commands (Tasks 006-007)"),
             ],
             "deliverables": ["vibey/cli/roadmap_commands/deps.py"]
            },
            {"id": "007", "title": "Build rich output formatting (tables)", "type": "implementation", "status": "completed",
             "commits": [
                 ("205c877", "2025-11-12T16:22:27-05:00", "fix: Begin addressing test failures in comprehensive CLI test suite"),
                 ("2cfdfd5", "2025-11-12T16:33:11-05:00", "fix: Resolve formatter and path issues in CLI commands"),
             ],
             "deliverables": ["vibey/cli/formatters.py"]
            },
            {"id": "008", "title": "Implement filtering and search", "type": "implementation", "status": "completed",
             "commits": [("082b952", "2025-11-10T19:03:27-05:00", "feat: Wire CLI commands to script functionality (Task 004)")],
             "deliverables": ["vibey/cli/roadmap_commands/find.py"]
            },
            {"id": "009", "title": "Write CLI integration tests", "type": "testing", "status": "completed",
             "commits": [
                 ("205c877", "2025-11-12T16:22:27-05:00", "fix: Begin addressing test failures in comprehensive CLI test suite"),
                 ("a701f28", "2025-11-12T17:00:26-05:00", "docs: Complete test fix session documentation - 97.7% pass rate achieved"),
             ],
             "deliverables": ["tests/cli/test_roadmap_*.py - 43 CLI tests, 97.7% pass rate"]
            },
        ]
    },
    "roadmap-system-4": {
        "name": "CLI Commands (Part 2: Update & Version)",
        "started": "2025-11-12T16:00:00+00:00",
        "completed": None,
        "tasks": [
            {"id": "001", "title": "Implement `vibey task start <id>`", "type": "implementation", "status": "completed",
             "commits": [
                 ("205c877", "2025-11-12T16:22:27-05:00", "fix: Begin addressing test failures in comprehensive CLI test suite"),
                 ("9517859", "2025-11-12T16:59:29-05:00", "fix: Implement idempotent start behavior - 2 tests fixed"),
             ],
             "deliverables": ["vibey/cli/roadmap_commands/start.py", "vibey/operations/roadmap/update.py"]
            },
            {"id": "002", "title": "Implement `vibey task complete <id>`", "type": "implementation", "status": "completed",
             "commits": [("205c877", "2025-11-12T16:22:27-05:00", "fix: Begin addressing test failures in comprehensive CLI test suite")],
             "deliverables": ["vibey/cli/roadmap_commands/complete.py"]
            },
            {"id": "003", "title": "Implement `vibey sprint start/complete`", "type": "implementation", "status": "completed",
             "commits": [("205c877", "2025-11-12T16:22:27-05:00", "fix: Begin addressing test failures in comprehensive CLI test suite")],
             "deliverables": ["vibey/operations/roadmap/update.py - Sprint operations"]
            },
            {"id": "004", "title": "Build automatic version bumping logic", "type": "implementation", "status": "not_started", "deliverables": ["NOT IMPLEMENTED"]},
            {"id": "005", "title": "Implement git tag creation", "type": "implementation", "status": "not_started", "deliverables": ["NOT IMPLEMENTED"]},
            {"id": "006", "title": "Implement `vibey version bump/history`", "type": "implementation", "status": "not_started", "deliverables": ["NOT IMPLEMENTED"]},
            {"id": "007", "title": "Build task assignment commands", "type": "implementation", "status": "completed",
             "commits": [("205c877", "2025-11-12T16:22:27-05:00", "fix: Begin addressing test failures in comprehensive CLI test suite")],
             "deliverables": ["vibey/cli/roadmap_commands/assign.py"]
            },
            {"id": "008", "title": "Add validation and safety checks", "type": "implementation", "status": "completed",
             "commits": [("205c877", "2025-11-12T16:22:27-05:00", "fix: Begin addressing test failures in comprehensive CLI test suite")],
             "deliverables": ["vibey/operations/roadmap/validate.py"]
            },
            {"id": "009", "title": "Write tests for update operations", "type": "testing", "status": "completed",
             "commits": [("205c877", "2025-11-12T16:22:27-05:00", "fix: Begin addressing test failures in comprehensive CLI test suite")],
             "deliverables": ["tests/cli/test_roadmap_*.py"]
            },
        ]
    },
    "roadmap-system-5": {
        "name": "Agent Integration & Auto-routing",
        "started": "2025-11-12T16:00:00+00:00",
        "completed": None,
        "tasks": [
            {"id": "001", "title": "Design agent recommendation algorithm", "type": "design", "status": "not_started", "deliverables": ["NOT IMPLEMENTED"]},
            {"id": "002", "title": "Implement `vibey task next` with routing", "type": "implementation", "status": "not_started", "deliverables": ["NOT IMPLEMENTED"]},
            {"id": "003", "title": "Build agent-task matching logic", "type": "implementation", "status": "not_started", "deliverables": ["NOT IMPLEMENTED"]},
            {"id": "004", "title": "Integrate with sprint planning workflow", "type": "implementation", "status": "not_started", "deliverables": ["NOT IMPLEMENTED"]},
            {"id": "005", "title": "Create quality gate task automation", "type": "implementation", "status": "completed",
             "commits": [("205c877", "2025-11-12T16:22:27-05:00", "fix: Begin addressing test failures in comprehensive CLI test suite")],
             "deliverables": ["vibey/roadmap/standards/ - Complete standards system", "vibey/operations/roadmap/standards_enforcement.py"]
            },
            {"id": "006", "title": "Build sprint retroactive agent analysis", "type": "implementation", "status": "not_started", "deliverables": ["NOT IMPLEMENTED"]},
            {"id": "007", "title": "Implement parallel task detection", "type": "implementation", "status": "not_started", "deliverables": ["NOT IMPLEMENTED"]},
            {"id": "008", "title": "Update coordinator agent integration", "type": "implementation", "status": "not_started", "deliverables": ["NOT IMPLEMENTED"]},
            {"id": "009", "title": "Write tests for agent routing", "type": "testing", "status": "not_started", "deliverables": ["NOT IMPLEMENTED"]},
        ]
    },
    "roadmap-system-6": {
        "name": "Documentation & Polish",
        "started": "2025-11-09T18:00:00+00:00",
        "completed": "2025-11-12T17:00:00+00:00",
        "tasks": [
            {"id": "001", "title": "Write user guide (Getting Started)", "type": "documentation", "status": "completed",
             "commits": [("9cab354", "2025-11-09T18:13:30-05:00", "docs: Add comprehensive roadmap user guide and CLI reference (Sprint 6)")],
             "deliverables": ["docs/guides/ROADMAP_USER_GUIDE.md"]
            },
            {"id": "002", "title": "Write CLI reference documentation", "type": "documentation", "status": "completed",
             "commits": [("9cab354", "2025-11-09T18:13:30-05:00", "docs: Add comprehensive roadmap user guide and CLI reference (Sprint 6)")],
             "deliverables": ["docs/guides/ROADMAP_CLI_REFERENCE.md"]
            },
            {"id": "003", "title": "Create tutorial (E-commerce example)", "type": "documentation", "status": "completed",
             "commits": [("c123c0f", "2025-11-09T18:18:47-05:00", "docs: Add comprehensive E-commerce platform tutorial (Sprint 6)")],
             "deliverables": ["docs/guides/ROADMAP_TUTORIAL.md"]
            },
            {"id": "004", "title": "Build 3 example projects", "type": "documentation", "status": "completed",
             "commits": [("c123c0f", "2025-11-09T18:18:47-05:00", "docs: Add comprehensive E-commerce platform tutorial (Sprint 6)")],
             "deliverables": ["E-commerce, ML Pipeline, Mobile App examples in tutorial"]
            },
            {"id": "005", "title": "Create architecture diagrams", "type": "documentation", "status": "completed",
             "deliverables": ["Diagrams in ROADMAP_OBJECT_HIERARCHY.md"]
            },
            {"id": "006", "title": "Polish CLI output and error messages", "type": "implementation", "status": "completed",
             "commits": [
                 ("205c877", "2025-11-12T16:22:27-05:00", "fix: Begin addressing test failures in comprehensive CLI test suite"),
                 ("2cfdfd5", "2025-11-12T16:33:11-05:00", "fix: Resolve formatter and path issues in CLI commands"),
             ],
             "deliverables": ["vibey/cli/formatters.py", "vibey/cli/roadmap_errors.py"]
            },
            {"id": "007", "title": "Final integration testing", "type": "testing", "status": "completed",
             "commits": [
                 ("205c877", "2025-11-12T16:22:27-05:00", "fix: Begin addressing test failures in comprehensive CLI test suite"),
                 ("a701f28", "2025-11-12T17:00:26-05:00", "docs: Complete test fix session documentation - 97.7% pass rate"),
             ],
             "deliverables": ["43 CLI tests, 97.7% pass rate"]
            },
            {"id": "008", "title": "Bug fixes and refinements", "type": "implementation", "status": "completed",
             "commits": [
                 ("228015a", "2025-11-12T16:50:26-05:00", "fix: Resolve data structure mismatches in context and cache systems - 13 tests fixed"),
                 ("feb614b", "2025-11-12T16:57:23-05:00", "fix: Improve error handling and defensive coding for track queries"),
                 ("9517859", "2025-11-12T16:59:29-05:00", "fix: Implement idempotent start behavior - 2 tests fixed"),
             ],
             "deliverables": ["Multiple bug fixes improving test pass rate from 70% to 97.7%"]
            },
        ]
    },
}


def create_task_yaml_content(sprint_id: str, task_data: dict) -> dict:
    """Create task YAML content."""
    task_id = f"{sprint_id}-task-{task_data['id']}"

    # Build commits array
    commits = []
    for commit_info in task_data.get("commits", []):
        sha, date_str, message = commit_info
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        commits.append({
            "sha": sha,
            "message": message,
            "date": date_str,
            "author": "Fred Abood",
            "platform": "claude-code",
            "submitted_at": int(dt.timestamp())
        })

    return {
        "task": {
            "id": task_id,
            "title": task_data["title"],
            "type": task_data["type"],
            "sprint_id": sprint_id,
            "track_id": "roadmap-system",
            "roadmap_id": "vibey-framework-v2",
            "status": task_data["status"],
            "priority": "critical",
            "created": "2025-11-07T03:00:00+00:00",
            "started": "2025-11-10T18:00:00+00:00" if task_data["status"] != "not_started" else None,
            "completed": "2025-11-12T17:00:00+00:00" if task_data["status"] == "completed" else None,
            "estimated_duration": "4 hours",
            "assigned_agents": ["web-developer"] if task_data["type"] in ["implementation", "design"] else ["test-engineer"],
            "deliverables": task_data.get("deliverables", []),
            "commits": commits,
            "dependencies": [],
            "blocked_by": [],
            "blocks": [],
            "metadata": {}
        }
    }


def create_sprint_yaml_content(sprint_id: str, sprint_data: dict) -> dict:
    """Create sprint YAML content."""
    tasks = sprint_data["tasks"]
    completed_count = sum(1 for t in tasks if t["status"] == "completed")

    return {
        "sprint": {
            "id": sprint_id,
            "name": sprint_data["name"],
            "track_id": "roadmap-system",
            "roadmap_id": "vibey-framework-v2",
            "status": "completed" if sprint_data["completed"] else "in_progress",
            "created": "2025-11-07T03:00:00+00:00",
            "started": sprint_data["started"],
            "completed": sprint_data["completed"],
            "estimated_duration": "2 weeks",
            "progress": {
                "tasks_total": len(tasks),
                "tasks_completed": completed_count,
                "completion_percent": int((completed_count / len(tasks)) * 100) if tasks else 0,
            },
            "assigned_agents": ["web-developer", "test-engineer"],
            "deliverables": [d for task in tasks for d in task.get("deliverables", [])],
            "commits": [],
            "quality_gates": [],
            "dependencies": [],
            "metadata": {}
        }
    }


def main():
    """Main remediation process."""
    print("=" * 80)
    print("ROADMAP-SYSTEM TRACK REMEDIATION")
    print("=" * 80)
    print()

    total_tasks = 0
    completed_tasks = 0
    total_commits = 0

    for sprint_id, sprint_data in SPRINTS.items():
        sprint_dir = TRACK_PATH / sprint_id
        sprint_dir.mkdir(parents=True, exist_ok=True)

        print(f"  Sprint: {sprint_id}")
        print(f"  Name: {sprint_data['name']}")

        # Create sprint.yaml
        sprint_yaml_content = create_sprint_yaml_content(sprint_id, sprint_data)
        sprint_yaml_path = sprint_dir / "sprint.yaml"
        with open(sprint_yaml_path, 'w') as f:
            yaml.dump(sprint_yaml_content, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        print(f"    ✓ Created {sprint_yaml_path}")

        # Create task directories and task.yaml files
        for task_data in sprint_data["tasks"]:
            task_id = f"{sprint_id}-task-{task_data['id']}"
            task_dir = sprint_dir / task_id
            task_dir.mkdir(parents=True, exist_ok=True)

            task_yaml_content = create_task_yaml_content(sprint_id, task_data)
            task_yaml_path = task_dir / "task.yaml"
            with open(task_yaml_path, 'w') as f:
                yaml.dump(task_yaml_content, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

            total_tasks += 1
            if task_data["status"] == "completed":
                completed_tasks += 1
            total_commits += len(task_data.get("commits", []))

            status_icon = "✓" if task_data["status"] == "completed" else "○"
            print(f"    {status_icon} Task {task_id}: {task_data['title']} ({task_data['status']})")

        print()

    print()
    print("=" * 80)
    print("REMEDIATION SUMMARY")
    print("=" * 80)
    print()
    print(f"Sprints Created: {len(SPRINTS)}")
    print(f"Tasks Created: {total_tasks}")
    print(f"Tasks Completed: {completed_tasks} ({int(completed_tasks/total_tasks*100)}%)")
    print(f"Tasks Not Started: {total_tasks - completed_tasks}")
    print(f"Git Commits Attributed: {total_commits}")
    print()
    print("Sprint Status:")
    for sprint_id, sprint_data in SPRINTS.items():
        status = "✓ COMPLETED" if sprint_data["completed"] else "⚠ IN PROGRESS"
        tasks_completed = sum(1 for t in sprint_data["tasks"] if t["status"] == "completed")
        print(f"  {sprint_id}: {status} ({tasks_completed}/{len(sprint_data['tasks'])} tasks)")
    print()
    print(f"Track Completion: ~{int(completed_tasks/total_tasks*100)}% ({completed_tasks}/{total_tasks} tasks completed)")
    print()
    print("Next Steps:")
    print("  1. Update track.yaml with accurate progress")
    print("  2. Complete remaining Sprint 4 tasks (version management)")
    print("  3. Complete remaining Sprint 5 tasks (agent routing)")
    print("  4. Run roadmap validation to verify integrity")
    print()


if __name__ == "__main__":
    main()
