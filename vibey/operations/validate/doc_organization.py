"""
Documentation Organization Validator

Ensures all documentation in the roadmap follows organization standards:
- Analysis files are in context/ directories
- Only core files at their respective levels
- No loose analysis/report files at track or sprint levels
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple


# Core files allowed at each level
ALLOWED_TRACK_FILES = {'track.yaml', 'track.md', '.id'}
ALLOWED_SPRINT_FILES = {'sprint.yaml', 'sprint.md', '.id'}
ALLOWED_TASK_FILES = {'task.yaml', 'task.md', '.id'}
ALLOWED_ROOT_FILES = {'roadmap.yaml', 'roadmap.md'}

# System/metadata files to ignore
SYSTEM_FILES = {
    '.id',
    '.sync-manifest.json',
    'audit-trail.yaml',
    'table_of_contents.json',
    'COMMIT_CLUSTERS.json',
}

# Directories to ignore
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

    @property
    def is_valid(self) -> bool:
        """Return True if no issues found."""
        return len(self.issues) == 0


class DocOrganizationValidator:
    """Validates documentation organization in roadmap."""

    def __init__(self, roadmap_dir: Path, verbose: bool = False):
        self.roadmap_dir = roadmap_dir
        self.verbose = verbose
        self.report = ValidationReport()

    def validate(self) -> ValidationReport:
        """Run validation and return report."""
        if not self.roadmap_dir.exists():
            self.report.add_issue(str(self.roadmap_dir), "Roadmap directory not found")
            return self.report

        # Check root level
        self._validate_root()

        # Check each track
        for track_dir in self.roadmap_dir.iterdir():
            if track_dir.is_dir() and track_dir.name not in IGNORED_DIRS:
                self._validate_track(track_dir)

        return self.report

    def _validate_root(self):
        """Validate root roadmap directory."""
        for item in self.roadmap_dir.iterdir():
            if item.is_file():
                if item.name not in ALLOWED_ROOT_FILES and item.name not in SYSTEM_FILES:
                    self.report.add_issue(
                        str(item.relative_to(self.roadmap_dir)),
                        "Unexpected file at root level. Move to appropriate context/ or archived/"
                    )

    def _validate_track(self, track_dir: Path):
        """Validate a track directory."""
        self.report.tracks_checked += 1

        for item in track_dir.iterdir():
            if item.is_file():
                if item.name not in ALLOWED_TRACK_FILES and item.name not in SYSTEM_FILES:
                    self.report.add_issue(
                        str(item.relative_to(self.roadmap_dir)),
                        f"File should be in {track_dir.name}/context/"
                    )
            elif item.is_dir() and item.name not in IGNORED_DIRS:
                self._validate_sprint(item)

        # Check context/ exists
        context_dir = track_dir / 'context'
        if not context_dir.exists():
            self.report.add_warning(
                str(track_dir.relative_to(self.roadmap_dir)),
                "Missing context/ directory (may be empty track)"
            )

    def _validate_sprint(self, sprint_dir: Path):
        """Validate a sprint directory."""
        self.report.sprints_checked += 1

        for item in sprint_dir.iterdir():
            if item.is_file():
                if item.name not in ALLOWED_SPRINT_FILES and item.name not in SYSTEM_FILES:
                    self.report.add_issue(
                        str(item.relative_to(self.roadmap_dir)),
                        f"File should be in {sprint_dir.name}/context/"
                    )
            elif item.is_dir() and item.name not in IGNORED_DIRS:
                self._validate_task(item)

    def _validate_task(self, task_dir: Path):
        """Validate a task directory."""
        for item in task_dir.iterdir():
            if item.is_file():
                if item.name not in ALLOWED_TASK_FILES and item.name not in SYSTEM_FILES:
                    self.report.add_issue(
                        str(item.relative_to(self.roadmap_dir)),
                        "Unexpected file in task directory"
                    )
