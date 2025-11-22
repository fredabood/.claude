#!/usr/bin/env python3
"""
Validate Documentation Organization

Ensures all documentation in the roadmap follows the organization standards:
- Analysis files are in context/ directories
- Only core files (track.yaml, track.md, sprint.yaml, sprint.md, task.yaml, task.md)
  are at their respective levels
- No loose analysis/report files at track or sprint levels

Usage:
    python3 scripts/validate-doc-organization.py [--fix] [--verbose]
"""

import argparse
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Tuple

# Core files that are allowed at each level
ALLOWED_TRACK_FILES = {'track.yaml', 'track.md', '.id'}
ALLOWED_SPRINT_FILES = {'sprint.yaml', 'sprint.md', '.id'}
ALLOWED_TASK_FILES = {'task.yaml', 'task.md', '.id'}
ALLOWED_ROOT_FILES = {'roadmap.yaml', 'roadmap.md'}

# System/metadata files to ignore at any level
SYSTEM_FILES = {
    '.id',
    '.sync-manifest.json',
    'audit-trail.yaml',
    'table_of_contents.json',
    'COMMIT_CLUSTERS.json',
}

# Directories that should be ignored
IGNORED_DIRS = {'archived', 'context', '__pycache__'}


@dataclass
class ValidationReport:
    """Report of validation operations."""
    tracks_checked: int = 0
    sprints_checked: int = 0
    issues: List[Tuple[str, str]] = field(default_factory=list)
    warnings: List[Tuple[str, str]] = field(default_factory=list)

    def add_issue(self, path: str, message: str):
        """Record a validation issue."""
        self.issues.append((path, message))

    def add_warning(self, path: str, message: str):
        """Record a warning."""
        self.warnings.append((path, message))

    def print_summary(self):
        """Print validation summary."""
        print("\n" + "=" * 80)
        print("DOCUMENTATION ORGANIZATION VALIDATION")
        print("=" * 80)
        print(f"Tracks checked: {self.tracks_checked}")
        print(f"Sprints checked: {self.sprints_checked}")

        if self.warnings:
            print(f"\n⚠ Warnings: {len(self.warnings)}")
            for path, warning in self.warnings[:10]:
                print(f"  {path}")
                print(f"    {warning}")
            if len(self.warnings) > 10:
                print(f"  ... and {len(self.warnings) - 10} more warnings")

        if self.issues:
            print(f"\n✗ Issues: {len(self.issues)}")
            for path, issue in self.issues[:20]:
                print(f"  {path}")
                print(f"    {issue}")
            if len(self.issues) > 20:
                print(f"  ... and {len(self.issues) - 20} more issues")

        print("\n" + "=" * 80)
        if not self.issues:
            print("✅ All documentation properly organized!")
        else:
            print(f"❌ {len(self.issues)} organization issues found")
        print("=" * 80)

        return len(self.issues) == 0


class DocOrganizationValidator:
    """Validates documentation organization in roadmap."""

    def __init__(self, roadmap_dir: Path, verbose: bool = False):
        self.roadmap_dir = roadmap_dir
        self.verbose = verbose
        self.report = ValidationReport()

    def validate(self) -> bool:
        """Run validation and return success status."""
        if not self.roadmap_dir.exists():
            print(f"❌ Roadmap directory not found: {self.roadmap_dir}")
            return False

        # Check root level
        self._validate_root()

        # Check each track
        for track_dir in self.roadmap_dir.iterdir():
            if track_dir.is_dir() and track_dir.name not in IGNORED_DIRS:
                self._validate_track(track_dir)

        return self.report.print_summary()

    def _validate_root(self):
        """Validate root roadmap directory."""
        for item in self.roadmap_dir.iterdir():
            if item.is_file():
                if item.name not in ALLOWED_ROOT_FILES and item.name not in SYSTEM_FILES:
                    self.report.add_issue(
                        str(item.relative_to(self.roadmap_dir)),
                        f"Unexpected file at root level. Move to appropriate context/ or archived/"
                    )

    def _validate_track(self, track_dir: Path):
        """Validate a track directory."""
        self.report.tracks_checked += 1

        # Check track-level files
        for item in track_dir.iterdir():
            if item.is_file():
                if item.name not in ALLOWED_TRACK_FILES and item.name not in SYSTEM_FILES:
                    self.report.add_issue(
                        str(item.relative_to(self.roadmap_dir)),
                        f"File should be in {track_dir.name}/context/"
                    )
            elif item.is_dir() and item.name not in IGNORED_DIRS:
                # This should be a sprint directory
                self._validate_sprint(item)

        # Check context/ exists if there are analysis files
        context_dir = track_dir / 'context'
        if not context_dir.exists():
            self.report.add_warning(
                str(track_dir.relative_to(self.roadmap_dir)),
                "Missing context/ directory (may be empty track)"
            )

    def _validate_sprint(self, sprint_dir: Path):
        """Validate a sprint directory."""
        self.report.sprints_checked += 1

        # Check sprint-level files
        for item in sprint_dir.iterdir():
            if item.is_file():
                if item.name not in ALLOWED_SPRINT_FILES and item.name not in SYSTEM_FILES:
                    self.report.add_issue(
                        str(item.relative_to(self.roadmap_dir)),
                        f"File should be in {sprint_dir.name}/context/"
                    )
            elif item.is_dir() and item.name not in IGNORED_DIRS:
                # This should be a task directory
                self._validate_task(item)

    def _validate_task(self, task_dir: Path):
        """Validate a task directory."""
        for item in task_dir.iterdir():
            if item.is_file():
                if item.name not in ALLOWED_TASK_FILES and item.name not in SYSTEM_FILES:
                    self.report.add_issue(
                        str(item.relative_to(self.roadmap_dir)),
                        f"Unexpected file in task directory"
                    )


def main():
    parser = argparse.ArgumentParser(
        description='Validate documentation organization in roadmap'
    )
    parser.add_argument(
        '--roadmap-dir',
        type=Path,
        default=Path.cwd() / '.vibey' / 'roadmap',
        help='Path to roadmap directory'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed output'
    )

    args = parser.parse_args()

    validator = DocOrganizationValidator(args.roadmap_dir, args.verbose)
    success = validator.validate()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
