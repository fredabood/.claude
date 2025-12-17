#!/usr/bin/env python3
"""
Validate Roadmap Data Format

Checks that all roadmap objects follow the expected data model:
- Sprints should NOT have embedded tasks
- Tasks should be in separate files (.vibey/tasks/{sprint-id}-tasks.yaml)
- All required fields are present
- Data types are correct

This prevents the silent failure issue where task completions don't work
due to format mismatches.

Usage:
    python3 framework/scripts/validate-roadmap-format.py
    python3 framework/scripts/validate-roadmap-format.py --fix  # Auto-fix issues

Created: 2025-11-09
Purpose: Prevent data model mismatches and format inconsistencies
"""

import sys
import argparse
import yaml
from pathlib import Path

# Add framework to path
framework_root = Path(__file__).parent.parent
sys.path.insert(0, str(framework_root.parent))


class RoadmapValidator:
    """Validates roadmap data format and structure."""

    def __init__(self, root_dir: Path = None):
        """
        Initialize validator.

        Args:
            root_dir: Project root directory (auto-detected if not provided)
        """
        self.root_dir = root_dir or Path.cwd()
        self.vibey_dir = self.root_dir / ".vibey"
        self.sprints_dir = self.vibey_dir / "sprints"
        self.tasks_dir = self.vibey_dir / "tasks"
        self.tracks_dir = self.vibey_dir / "tracks"

        # Validation results
        self.issues = []
        self.warnings = []
        self.sprints_checked = 0
        self.tasks_checked = 0
        self.tracks_checked = 0

    def validate_environment(self) -> bool:
        """Validate that we're in a Vibey project."""
        if not self.vibey_dir.exists():
            print(f"❌ Error: .vibey directory not found at {self.vibey_dir}")
            return False

        if not self.sprints_dir.exists():
            print(f"❌ Error: sprints directory not found at {self.sprints_dir}")
            return False

        return True

    def add_issue(self, severity: str, file: str, message: str):
        """Record a validation issue."""
        issue = {
            'severity': severity,
            'file': file,
            'message': message
        }
        if severity == 'error':
            self.issues.append(issue)
        else:
            self.warnings.append(issue)

    def validate_sprint(self, sprint_file: Path) -> bool:
        """
        Validate a single sprint file.

        Args:
            sprint_file: Path to sprint YAML file

        Returns:
            True if valid
        """
        self.sprints_checked += 1
        valid = True

        try:
            with open(sprint_file) as f:
                data = yaml.safe_load(f)

            if 'sprint' not in data:
                self.add_issue('error', sprint_file.name, "Missing 'sprint' key")
                return False

            sprint = data['sprint']
            sprint_id = sprint.get('id', 'unknown')

            # Check for embedded tasks (anti-pattern)
            if 'tasks' in sprint:
                task_count = len(sprint['tasks']) if sprint['tasks'] else 0
                if task_count > 0:
                    self.add_issue(
                        'error',
                        sprint_file.name,
                        f"Sprint has {task_count} embedded tasks - should use separate tasks file"
                    )
                    valid = False

            # Check that corresponding tasks file exists
            tasks_file = self.tasks_dir / f"{sprint_id}-tasks.yaml"
            if not tasks_file.exists():
                self.add_issue(
                    'warning',
                    sprint_file.name,
                    f"No tasks file found at {tasks_file.name} (sprint might have 0 tasks)"
                )

            # Check required fields
            required_fields = ['id', 'name', 'track_id', 'roadmap_id', 'status']
            for field in required_fields:
                if field not in sprint:
                    self.add_issue('error', sprint_file.name, f"Missing required field: {field}")
                    valid = False

            # Check metadata
            if 'metadata' not in sprint:
                self.add_issue('warning', sprint_file.name, "Missing metadata object")
            elif 'last_updated' not in sprint['metadata']:
                self.add_issue('warning', sprint_file.name, "Missing metadata.last_updated")

        except Exception as e:
            self.add_issue('error', sprint_file.name, f"Failed to parse: {e}")
            return False

        return valid

    def validate_tasks_file(self, tasks_file: Path) -> bool:
        """
        Validate a tasks file.

        Args:
            tasks_file: Path to tasks YAML file

        Returns:
            True if valid
        """
        valid = True

        try:
            with open(tasks_file) as f:
                data = yaml.safe_load(f)

            if 'tasks' not in data:
                self.add_issue('error', tasks_file.name, "Missing 'tasks' key")
                return False

            tasks = data['tasks']
            for i, task in enumerate(tasks):
                self.tasks_checked += 1

                # Check required fields
                required_fields = ['id', 'sprint_id', 'track_id', 'roadmap_id', 'title', 'status']
                for field in required_fields:
                    if field not in task:
                        self.add_issue(
                            'error',
                            tasks_file.name,
                            f"Task {i} ({task.get('id', 'unknown')}): Missing required field: {field}"
                        )
                        valid = False

                # Check data types
                if 'estimated_tokens' in task:
                    if not isinstance(task['estimated_tokens'], (int, type(None))):
                        self.add_issue(
                            'error',
                            tasks_file.name,
                            f"Task {task.get('id', 'unknown')}: estimated_tokens must be integer, got {type(task['estimated_tokens']).__name__}"
                        )
                        valid = False

                # Check dependencies format
                if 'dependencies' in task and task['dependencies']:
                    for dep in task['dependencies']:
                        if isinstance(dep, str):
                            self.add_issue(
                                'error',
                                tasks_file.name,
                                f"Task {task.get('id', 'unknown')}: dependency should be object, not string: {dep}"
                            )
                            valid = False

        except Exception as e:
            self.add_issue('error', tasks_file.name, f"Failed to parse: {e}")
            return False

        return valid

    def validate_track(self, track_file: Path) -> bool:
        """
        Validate a track file.

        Args:
            track_file: Path to track YAML file

        Returns:
            True if valid
        """
        self.tracks_checked += 1
        valid = True

        try:
            with open(track_file) as f:
                data = yaml.safe_load(f)

            if 'track' not in data:
                self.add_issue('error', track_file.name, "Missing 'track' key")
                return False

            track = data['track']

            # Check required fields
            required_fields = ['id', 'name', 'roadmap_id', 'status']
            for field in required_fields:
                if field not in track:
                    self.add_issue('error', track_file.name, f"Missing required field: {field}")
                    valid = False

            # Check depends_on format
            if 'depends_on' in track and track['depends_on']:
                for dep in track['depends_on']:
                    if isinstance(dep, str):
                        self.add_issue(
                            'error',
                            track_file.name,
                            f"depends_on should be objects, not strings: {dep}"
                        )
                        valid = False

        except Exception as e:
            self.add_issue('error', track_file.name, f"Failed to parse: {e}")
            return False

        return valid

    def run(self) -> bool:
        """
        Run full validation.

        Returns:
            True if all validations pass
        """
        print("=" * 70)
        print("✓ Vibey Roadmap Format Validator")
        print("=" * 70)
        print()

        # Validate environment
        if not self.validate_environment():
            return False

        # Validate sprints
        print("🔍 Validating sprints...")
        for sprint_file in self.sprints_dir.glob("*.yaml"):
            self.validate_sprint(sprint_file)

        # Validate tasks
        print(f"🔍 Validating task files...")
        for tasks_file in self.tasks_dir.glob("*-tasks.yaml"):
            self.validate_tasks_file(tasks_file)

        # Validate tracks
        print(f"🔍 Validating tracks...")
        for track_file in self.tracks_dir.glob("*.yaml"):
            self.validate_track(track_file)

        # Print results
        print()
        print("=" * 70)
        print("📊 Validation Results")
        print("=" * 70)
        print(f"  Sprints checked: {self.sprints_checked}")
        print(f"  Tasks checked: {self.tasks_checked}")
        print(f"  Tracks checked: {self.tracks_checked}")
        print()
        print(f"  Errors: {len(self.issues)}")
        print(f"  Warnings: {len(self.warnings)}")

        # Print issues
        if self.issues:
            print()
            print("❌ ERRORS:")
            for issue in self.issues:
                print(f"  [{issue['file']}] {issue['message']}")

        if self.warnings:
            print()
            print("⚠️  WARNINGS:")
            for issue in self.warnings:
                print(f"  [{issue['file']}] {issue['message']}")

        print()
        if len(self.issues) == 0:
            print("✅ All validations passed!")
        else:
            print(f"❌ Found {len(self.issues)} error(s) - please fix before proceeding")
            print()
            print("💡 Tip: Run migrate-embedded-tasks.py to fix embedded task issues")

        print("=" * 70)

        return len(self.issues) == 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Validate roadmap data format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate roadmap format
  %(prog)s

  # Validate specific project
  %(prog)s --dir /path/to/project

Purpose:
  Checks that all roadmap objects follow the expected data model to prevent
  silent failures in task completion and status updates.

  Validates:
  - No embedded tasks in sprint files
  - Task files exist for each sprint
  - Required fields present
  - Correct data types
  - Proper dependency formats

  Use this as a pre-commit hook or CI check to catch format issues early.
        """
    )

    parser.add_argument(
        '--dir',
        type=Path,
        default=None,
        help='Project root directory (auto-detected if not provided)'
    )

    args = parser.parse_args()

    # Run validation
    validator = RoadmapValidator(root_dir=args.dir)
    success = validator.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
