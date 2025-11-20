#!/usr/bin/env python3
"""
Pydantic schema validator for roadmap data.

Validates all roadmap YAML files against their Pydantic models to ensure
complete schema compliance and data integrity.

Usage:
    python3 scripts/validate-roadmap-schema.py [--strict] [--verbose]
"""

import argparse
import sys
import yaml
from pathlib import Path
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass, field
from pydantic import ValidationError

# Add vibey package to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from vibey.roadmap.models import Track, Sprint, Task
from vibey.roadmap.serialization.yaml_loader import load_track, load_sprint, load_task
from vibey.cli.roadmap_lib.filesystem import FileSystemManager


@dataclass
class ValidationReport:
    """Report of validation operations."""
    files_validated: int = 0
    files_passed: int = 0
    files_failed: int = 0
    validation_errors: List[Tuple[str, str]] = field(default_factory=list)
    warnings: List[Tuple[str, str]] = field(default_factory=list)

    def add_error(self, file_path: str, error: str):
        """Record a validation error."""
        self.validation_errors.append((file_path, error))

    def add_warning(self, file_path: str, warning: str):
        """Record a validation warning."""
        self.warnings.append((file_path, warning))

    def print_summary(self):
        """Print validation summary."""
        print("\n" + "=" * 80)
        print("SCHEMA VALIDATION SUMMARY")
        print("=" * 80)
        print(f"Files validated: {self.files_validated}")
        print(f"✓ Passed: {self.files_passed} ({self._percentage(self.files_passed, self.files_validated):.1f}%)")
        print(f"✗ Failed: {self.files_failed} ({self._percentage(self.files_failed, self.files_validated):.1f}%)")

        if self.warnings:
            print(f"\n⚠ Warnings: {len(self.warnings)}")
            for file_path, warning in self.warnings[:5]:
                print(f"  {file_path}")
                print(f"    {warning}")
            if len(self.warnings) > 5:
                print(f"  ... and {len(self.warnings) - 5} more warnings")

        if self.validation_errors:
            print(f"\n✗ Validation Errors: {len(self.validation_errors)}")
            for file_path, error in self.validation_errors[:10]:
                print(f"  {file_path}")
                # Truncate long error messages
                error_lines = error.split('\n')
                for line in error_lines[:3]:
                    print(f"    {line}")
                if len(error_lines) > 3:
                    print(f"    ... ({len(error_lines) - 3} more lines)")
            if len(self.validation_errors) > 10:
                print(f"  ... and {len(self.validation_errors) - 10} more errors")

        print("\n" + "=" * 80)
        if self.files_failed == 0:
            print("✅ All files passed schema validation!")
        else:
            print(f"❌ {self.files_failed} files failed schema validation")
        print("=" * 80)

    @staticmethod
    def _percentage(part: int, whole: int) -> float:
        """Calculate percentage."""
        if whole == 0:
            return 0.0
        return (part / whole) * 100


class SchemaValidator:
    """Pydantic schema validator for roadmap data."""

    def __init__(self, strict: bool = False, verbose: bool = False):
        self.strict = strict
        self.verbose = verbose
        self.report = ValidationReport()
        self.fs = FileSystemManager()

    def validate_track(self, track_path: Path) -> bool:
        """Validate a track YAML file against Track model."""
        self.report.files_validated += 1

        try:
            # Load using the loader (which uses Pydantic validation)
            track = load_track(track_path)

            # Additional custom validations
            warnings = []

            # Check progress consistency
            if track.progress:
                # Sprints count should match sprints list length
                if track.sprints and len(track.sprints) != track.progress.sprints_total:
                    warnings.append(
                        f"Progress sprints_total ({track.progress.sprints_total}) "
                        f"doesn't match sprints list length ({len(track.sprints)})"
                    )

                # Completion percent should be in valid range
                if not (0 <= track.progress.completion_percent <= 100):
                    warnings.append(
                        f"Invalid completion_percent: {track.progress.completion_percent}"
                    )

            # Check date consistency
            if track.started and track.completed:
                if track.started > track.completed:
                    warnings.append(
                        f"Started date ({track.started}) is after completed date ({track.completed})"
                    )

            # Report warnings
            for warning in warnings:
                self.report.add_warning(str(track_path), warning)
                if self.verbose:
                    print(f"⚠ {track_path}: {warning}")

            self.report.files_passed += 1
            if self.verbose:
                print(f"✓ {track_path}")

            return True

        except ValidationError as e:
            self.report.files_failed += 1
            self.report.add_error(str(track_path), str(e))
            if self.verbose:
                print(f"✗ {track_path}")
                print(f"  {e}")
            return False

        except Exception as e:
            self.report.files_failed += 1
            error_msg = f"Unexpected error: {str(e)}"
            self.report.add_error(str(track_path), error_msg)
            if self.verbose:
                print(f"✗ {track_path}: {error_msg}")
            return False

    def validate_sprint(self, sprint_path: Path) -> bool:
        """Validate a sprint YAML file against Sprint model."""
        self.report.files_validated += 1

        try:
            sprint = load_sprint(sprint_path)

            warnings = []

            # Check date consistency
            if sprint.started and sprint.completed:
                if sprint.started > sprint.completed:
                    warnings.append(
                        f"Started date ({sprint.started}) is after completed date ({sprint.completed})"
                    )

            # Check task counts consistency
            if sprint.progress and sprint.progress.tasks_total is not None:
                task_type_sum = (
                    sprint.progress.development_tasks_total +
                    sprint.progress.completion_gate_tasks_total +
                    sprint.progress.production_gate_tasks_total
                )
                if task_type_sum > 0 and task_type_sum != sprint.progress.tasks_total:
                    warnings.append(
                        f"Tasks total ({sprint.progress.tasks_total}) doesn't match sum of task types ({task_type_sum})"
                    )

            for warning in warnings:
                self.report.add_warning(str(sprint_path), warning)
                if self.verbose:
                    print(f"⚠ {sprint_path}: {warning}")

            self.report.files_passed += 1
            if self.verbose:
                print(f"✓ {sprint_path}")

            return True

        except ValidationError as e:
            self.report.files_failed += 1
            self.report.add_error(str(sprint_path), str(e))
            if self.verbose:
                print(f"✗ {sprint_path}")
                print(f"  {e}")
            return False

        except Exception as e:
            self.report.files_failed += 1
            error_msg = f"Unexpected error: {str(e)}"
            self.report.add_error(str(sprint_path), error_msg)
            if self.verbose:
                print(f"✗ {sprint_path}: {error_msg}")
            return False

    def validate_task(self, task_path: Path) -> bool:
        """Validate a task YAML file against Task model."""
        self.report.files_validated += 1

        try:
            task = load_task(task_path)

            warnings = []

            # Check date consistency
            if task.started and task.completed:
                if task.started > task.completed:
                    warnings.append(
                        f"Started date ({task.started}) is after completed date ({task.completed})"
                    )

            # Check token consistency
            if task.estimated_tokens and task.actual_tokens:
                # Just a warning if actual exceeds estimate by more than 2x
                if task.actual_tokens > task.estimated_tokens * 2:
                    warnings.append(
                        f"Actual tokens ({task.actual_tokens}) significantly exceeds "
                        f"estimate ({task.estimated_tokens})"
                    )

            for warning in warnings:
                self.report.add_warning(str(task_path), warning)
                if self.verbose:
                    print(f"⚠ {task_path}: {warning}")

            self.report.files_passed += 1
            if self.verbose:
                print(f"✓ {task_path}")

            return True

        except ValidationError as e:
            self.report.files_failed += 1
            self.report.add_error(str(task_path), str(e))
            if self.verbose:
                print(f"✗ {task_path}")
                print(f"  {e}")
            return False

        except Exception as e:
            self.report.files_failed += 1
            error_msg = f"Unexpected error: {str(e)}"
            self.report.add_error(str(task_path), error_msg)
            if self.verbose:
                print(f"✗ {task_path}: {error_msg}")
            return False

    def run(self):
        """Run schema validation on all roadmap files."""
        print("Validating roadmap data against Pydantic schemas...\n")

        # Validate all tracks (direct file discovery)
        print("Validating tracks...")
        for track_path in self.fs.roadmap_root.glob('*/track.yaml'):
            # Skip archived files
            if 'archived' in str(track_path):
                continue
            self.validate_track(track_path)

        # Validate all sprints (direct file discovery)
        print("Validating sprints...")
        for sprint_path in self.fs.roadmap_root.glob('*/*/sprint.yaml'):
            # Skip archived files
            if 'archived' in str(sprint_path):
                continue
            self.validate_sprint(sprint_path)

        # Validate all tasks (direct file discovery)
        print("Validating tasks...")
        for task_path in self.fs.roadmap_root.glob('*/*/*/task.yaml'):
            # Skip archived files
            if 'archived' in str(task_path):
                continue
            self.validate_task(task_path)

        self.report.print_summary()


def main():
    parser = argparse.ArgumentParser(
        description='Validate roadmap data against Pydantic schemas'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Treat warnings as errors'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed output for each file'
    )

    args = parser.parse_args()

    validator = SchemaValidator(strict=args.strict, verbose=args.verbose)
    validator.run()

    # Exit with error code if validation failed
    if validator.report.files_failed > 0:
        sys.exit(1)
    elif args.strict and validator.report.warnings:
        sys.exit(1)


if __name__ == '__main__':
    main()
