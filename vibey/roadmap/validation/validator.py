"""
Validator for roadmap YAML files.

Validates YAML structure and data against schemas and business rules.
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Union
from pathlib import Path

import yaml


class ValidationError(Exception):
    """Validation error exception."""

    pass


@dataclass
class ValidationResult:
    """Result of validation."""

    valid: bool
    errors: List[str]
    warnings: List[str]

    def __bool__(self):
        """Allow boolean evaluation."""
        return self.valid

    def __str__(self):
        """String representation."""
        if self.valid:
            msg = "✅ Validation passed"
            if self.warnings:
                msg += f" ({len(self.warnings)} warnings)"
        else:
            msg = f"❌ Validation failed with {len(self.errors)} errors"
        return msg


class Validator:
    """
    YAML validator for roadmap objects.

    Validates structure, types, and business rules.
    """

    def __init__(self):
        """Initialize validator."""
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_file(self, file_path: Union[str, Path], object_type: str) -> ValidationResult:
        """
        Validate a YAML file.

        Args:
            file_path: Path to YAML file
            object_type: Type of object (roadmap, track, sprint, task)

        Returns:
            ValidationResult
        """
        self.errors = []
        self.warnings = []

        file_path = Path(file_path)

        # Check file exists
        if not file_path.exists():
            self.errors.append(f"File not found: {file_path}")
            return ValidationResult(valid=False, errors=self.errors, warnings=self.warnings)

        # Load YAML
        try:
            with open(file_path, "r") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.errors.append(f"YAML parse error: {e}")
            return ValidationResult(valid=False, errors=self.errors, warnings=self.warnings)

        # Validate based on type
        if object_type == "roadmap":
            self._validate_roadmap(data)
        elif object_type == "track":
            self._validate_track(data)
        elif object_type == "sprint":
            self._validate_sprint(data)
        elif object_type == "task":
            self._validate_task(data)
        else:
            self.errors.append(f"Unknown object type: {object_type}")

        return ValidationResult(
            valid=len(self.errors) == 0,
            errors=self.errors,
            warnings=self.warnings,
        )

    def validate_dict(self, data: Dict[str, Any], object_type: str) -> ValidationResult:
        """
        Validate a dictionary.

        Args:
            data: Dictionary to validate
            object_type: Type of object

        Returns:
            ValidationResult
        """
        self.errors = []
        self.warnings = []

        if object_type == "roadmap":
            self._validate_roadmap(data)
        elif object_type == "track":
            self._validate_track(data)
        elif object_type == "sprint":
            self._validate_sprint(data)
        elif object_type == "task":
            self._validate_task(data)
        else:
            self.errors.append(f"Unknown object type: {object_type}")

        return ValidationResult(
            valid=len(self.errors) == 0,
            errors=self.errors,
            warnings=self.warnings,
        )

    def _validate_roadmap(self, data: Dict[str, Any]):
        """Validate roadmap structure and rules."""
        if "roadmap" not in data:
            self.errors.append("Missing 'roadmap' root key")
            return

        roadmap = data["roadmap"]

        # Required fields
        required = [
            "id",
            "name",
            "version",
            "version_strategy",
            "status",
            "blocked",
            "created",
            "progress",
            "tracks",
            "activity_log",
            "metadata",
        ]
        for field in required:
            if field not in roadmap:
                self.errors.append(f"Missing required field: {field}")

        # Validate ID format
        if "id" in roadmap:
            if not re.match(r"^[a-z0-9-]+$", roadmap["id"]):
                self.errors.append(f"Invalid ID format: {roadmap['id']}")

        # Validate version format
        if "version" in roadmap:
            if not re.match(r"^\d+\.\d+\.\d+(-[a-z]+(\.\d+)?)?$", roadmap["version"]):
                self.errors.append(f"Invalid version format: {roadmap['version']}")

        # Validate progress
        if "progress" in roadmap:
            progress = roadmap["progress"]
            self._validate_progress(progress)

        # Validate tracks
        if "tracks" in roadmap:
            tracks = roadmap["tracks"]
            if not isinstance(tracks, list):
                self.errors.append("'tracks' must be a list")
            elif len(tracks) == 0:
                self.errors.append("Roadmap must have at least one track")
            else:
                # Check for duplicate track IDs
                track_ids = [t.get("id") for t in tracks if "id" in t]
                if len(track_ids) != len(set(track_ids)):
                    self.errors.append("Duplicate track IDs found")

        # Validate blocked flag matches blockers
        if "blocked" in roadmap and "blocked_by" in roadmap:
            has_blockers = len(roadmap["blocked_by"]) > 0
            if roadmap["blocked"] != has_blockers:
                self.errors.append(f"Blocked flag ({roadmap['blocked']}) doesn't match blocker list (has_blockers={has_blockers})")

    def _validate_track(self, data: Dict[str, Any]):
        """Validate track structure and rules."""
        if "track" not in data:
            self.errors.append("Missing 'track' root key")
            return

        track = data["track"]

        # Required fields
        required = [
            "id",
            "name",
            "roadmap_id",
            "status",
            "blocked",
            "priority",
            "created",
            "progress",
            "sprints",
            "dependencies",
            "blocks",
            "blocked_by",
            "quality_gates",
            "assigned_agents",
            "metadata",
        ]
        for field in required:
            if field not in track:
                self.errors.append(f"Missing required field: {field}")

        # Validate ID format
        if "id" in track:
            if not re.match(r"^[a-z0-9-]+$", track["id"]):
                self.errors.append(f"Invalid track ID format: {track['id']}")

        # Validate sprint IDs are track-scoped
        if "id" in track and "sprints" in track:
            track_id = track["id"]
            for sprint in track["sprints"]:
                if "id" in sprint:
                    if not sprint["id"].startswith(f"{track_id}-"):
                        self.errors.append(f"Sprint ID {sprint['id']} must start with track ID {track_id}")

        # Validate progress matches sprint count
        if "progress" in track and "sprints" in track:
            progress = track["progress"]
            sprint_count = len(track["sprints"])
            if progress.get("sprints_total") != sprint_count:
                self.errors.append(f"sprints_total ({progress.get('sprints_total')}) doesn't match sprint count ({sprint_count})")

        # Validate blocked flag
        if "blocked" in track and "blocked_by" in track:
            has_blockers = len(track["blocked_by"]) > 0
            if track["blocked"] != has_blockers:
                self.errors.append("Blocked flag doesn't match blocker list")

    def _validate_sprint(self, data: Dict[str, Any]):
        """Validate sprint structure and rules."""
        if "sprint" not in data:
            self.errors.append("Missing 'sprint' root key")
            return

        sprint = data["sprint"]

        # Required fields
        required = [
            "id",
            "name",
            "track_id",
            "roadmap_id",
            "status",
            "blocked",
            "created",
            "progress",
            # NOTE: "tasks" removed - tasks are now standalone files in tasks/*.yaml
            "development_gates",
            "blocks",
            "blocked_by",
            "metadata",
        ]
        for field in required:
            if field not in sprint:
                self.errors.append(f"Missing required field: {field}")

        # Validate sprint ID is track-scoped (only for slug-based IDs, not ULIDs)
        if "id" in sprint and "track_id" in sprint:
            sprint_id = sprint["id"]
            track_id = sprint["track_id"]
            # Only validate slug-based IDs, not ULIDs (26 alphanumeric chars)
            if not (len(sprint_id) == 26 and sprint_id.isalnum()):
                if not sprint_id.startswith(f"{track_id}-"):
                    self.errors.append(f"Sprint ID {sprint_id} must start with track ID {track_id}")

        # NOTE: Embedded tasks validation removed.
        # Tasks are now stored as standalone files in tasks/*.yaml.
        # Task validation is done separately via validate_task() for individual task files.
        # Legacy embedded sprint.tasks[] arrays are DEPRECATED.

        # Validate progress totals
        if "progress" in sprint:
            progress = sprint["progress"]
            expected_total = (
                progress.get("development_tasks_total", 0)
                + progress.get("completion_gate_tasks_total", 0)
                + progress.get("production_gate_tasks_total", 0)
            )
            if progress.get("tasks_total") != expected_total:
                self.errors.append(f"tasks_total doesn't match sum of task types ({expected_total})")

    def _validate_task(self, data: Dict[str, Any]):
        """Validate task structure and rules."""
        # Tasks can be in a dict or a list
        tasks = data if isinstance(data, list) else [data.get("task")]

        for task in tasks:
            if not task:
                continue

            # Required fields
            required = [
                "id",
                "sprint_id",
                "track_id",
                "roadmap_id",
                "task_type",
                "title",
                "description",
                "status",
                "blocked",
                "created",
                "assigned_agent",
                "priority",
                "estimated_tokens",
                "complexity",
                "dependencies",
                "blocks",
                "blocked_by",
                "metadata",
            ]
            for field in required:
                if field not in task:
                    self.errors.append(f"Task {task.get('id', '?')}: Missing required field: {field}")

            # Validate task ID is sprint-scoped
            if "id" in task and "sprint_id" in task:
                if not task["id"].startswith(f"{task['sprint_id']}-"):
                    self.errors.append(f"Task ID {task['id']} must start with sprint ID {task['sprint_id']}")

            # Validate task type and gate_info
            task_type = task.get("task_type")
            gate_info = task.get("gate_info")

            if task_type == "development":
                if gate_info is not None:
                    self.errors.append(f"Task {task.get('id')}: Development tasks cannot have gate_info")
            elif task_type in ["completion_gate", "production_gate"]:
                if gate_info is None:
                    self.errors.append(f"Task {task.get('id')}: Quality gate tasks must have gate_info")

            # Validate estimated tokens
            if "estimated_tokens" in task:
                if task["estimated_tokens"] <= 0:
                    self.errors.append(f"Task {task.get('id')}: estimated_tokens must be positive")

    def _validate_progress(self, progress: Dict[str, int]):
        """Validate progress object."""
        required = [
            "tracks_total",
            "tracks_completed",
            "sprints_total",
            "sprints_completed",
            "tasks_total",
            "tasks_completed",
            "completion_percent",
        ]

        for field in required:
            if field not in progress:
                self.errors.append(f"Progress missing field: {field}")

        # Validate counts
        if progress.get("tracks_completed", 0) > progress.get("tracks_total", 0):
            self.errors.append("tracks_completed cannot exceed tracks_total")

        if progress.get("sprints_completed", 0) > progress.get("sprints_total", 0):
            self.errors.append("sprints_completed cannot exceed sprints_total")

        if progress.get("tasks_completed", 0) > progress.get("tasks_total", 0):
            self.errors.append("tasks_completed cannot exceed tasks_total")

        # Validate percentage
        completion_percent = progress.get("completion_percent", 0)
        if not 0 <= completion_percent <= 100:
            self.errors.append(f"completion_percent must be 0-100, got {completion_percent}")


# Convenience functions
def validate_roadmap(data: Union[Dict, Path]) -> ValidationResult:
    """Validate a roadmap."""
    validator = Validator()
    if isinstance(data, (str, Path)):
        return validator.validate_file(data, "roadmap")
    return validator.validate_dict(data, "roadmap")


def validate_track(data: Union[Dict, Path]) -> ValidationResult:
    """Validate a track."""
    validator = Validator()
    if isinstance(data, (str, Path)):
        return validator.validate_file(data, "track")
    return validator.validate_dict(data, "track")


def validate_sprint(data: Union[Dict, Path]) -> ValidationResult:
    """Validate a sprint."""
    validator = Validator()
    if isinstance(data, (str, Path)):
        return validator.validate_file(data, "sprint")
    return validator.validate_dict(data, "sprint")


def validate_task(data: Union[Dict, Path]) -> ValidationResult:
    """Validate a task or tasks."""
    validator = Validator()
    if isinstance(data, (str, Path)):
        return validator.validate_file(data, "task")
    return validator.validate_dict(data, "task")
