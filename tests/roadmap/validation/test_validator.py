"""
Tests for vibey.roadmap.validation.validator module.

Tests YAML validation for roadmap objects.
"""

import pytest
import yaml
from pathlib import Path

from vibey.roadmap.validation.validator import (
    ValidationError,
    ValidationResult,
    Validator,
    validate_roadmap,
    validate_track,
    validate_sprint,
    validate_task,
)


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_valid_result(self):
        """Test valid result."""
        result = ValidationResult(valid=True, errors=[], warnings=[])
        assert result.valid
        assert bool(result)

    def test_invalid_result(self):
        """Test invalid result."""
        result = ValidationResult(valid=False, errors=["Error 1"], warnings=[])
        assert not result.valid
        assert not bool(result)

    def test_str_valid(self):
        """Test string representation when valid."""
        result = ValidationResult(valid=True, errors=[], warnings=[])
        assert "passed" in str(result)

    def test_str_valid_with_warnings(self):
        """Test string representation with warnings."""
        result = ValidationResult(valid=True, errors=[], warnings=["Warning"])
        assert "passed" in str(result)
        assert "warning" in str(result).lower()

    def test_str_invalid(self):
        """Test string representation when invalid."""
        result = ValidationResult(valid=False, errors=["Error"], warnings=[])
        assert "failed" in str(result)


class TestValidatorRoadmap:
    """Test Validator roadmap validation."""

    @pytest.fixture
    def valid_roadmap(self):
        """Create a valid roadmap dict."""
        return {
            "roadmap": {
                "id": "test-roadmap",
                "name": "Test Roadmap",
                "version": "1.0.0",
                "version_strategy": "semver",
                "status": "in_progress",
                "blocked": False,
                "created": "2025-12-15T10:00:00Z",
                "progress": {
                    "tracks_total": 1,
                    "tracks_completed": 0,
                    "sprints_total": 1,
                    "sprints_completed": 0,
                    "tasks_total": 1,
                    "tasks_completed": 0,
                    "completion_percent": 0,
                },
                "tracks": [{"id": "test-track"}],
                "activity_log": [],
                "metadata": {},
            }
        }

    def test_valid_roadmap(self, valid_roadmap):
        """Test validating valid roadmap."""
        validator = Validator()
        result = validator.validate_dict(valid_roadmap, "roadmap")
        assert result.valid

    def test_missing_root_key(self):
        """Test missing roadmap root key."""
        validator = Validator()
        result = validator.validate_dict({"wrong_key": {}}, "roadmap")
        assert not result.valid
        assert any("root key" in e for e in result.errors)

    def test_missing_required_fields(self):
        """Test missing required fields."""
        validator = Validator()
        result = validator.validate_dict({"roadmap": {"id": "test"}}, "roadmap")
        assert not result.valid
        assert len(result.errors) > 0

    def test_invalid_id_format(self, valid_roadmap):
        """Test invalid ID format."""
        valid_roadmap["roadmap"]["id"] = "Invalid ID!"
        validator = Validator()
        result = validator.validate_dict(valid_roadmap, "roadmap")
        assert not result.valid
        assert any("Invalid ID format" in e for e in result.errors)

    def test_invalid_version_format(self, valid_roadmap):
        """Test invalid version format."""
        valid_roadmap["roadmap"]["version"] = "invalid"
        validator = Validator()
        result = validator.validate_dict(valid_roadmap, "roadmap")
        assert not result.valid
        assert any("Invalid version format" in e for e in result.errors)

    def test_valid_prerelease_version(self, valid_roadmap):
        """Test valid prerelease version."""
        valid_roadmap["roadmap"]["version"] = "1.0.0-alpha.1"
        validator = Validator()
        result = validator.validate_dict(valid_roadmap, "roadmap")
        # Should be valid or only have unrelated errors
        version_errors = [e for e in result.errors if "version" in e.lower()]
        assert len(version_errors) == 0

    def test_empty_tracks(self, valid_roadmap):
        """Test empty tracks list."""
        valid_roadmap["roadmap"]["tracks"] = []
        validator = Validator()
        result = validator.validate_dict(valid_roadmap, "roadmap")
        assert not result.valid
        assert any("at least one track" in e for e in result.errors)

    def test_duplicate_track_ids(self, valid_roadmap):
        """Test duplicate track IDs."""
        valid_roadmap["roadmap"]["tracks"] = [
            {"id": "track-1"},
            {"id": "track-1"},
        ]
        validator = Validator()
        result = validator.validate_dict(valid_roadmap, "roadmap")
        assert not result.valid
        assert any("Duplicate" in e for e in result.errors)


class TestValidatorTrack:
    """Test Validator track validation."""

    @pytest.fixture
    def valid_track(self):
        """Create a valid track dict."""
        return {
            "track": {
                "id": "test-track",
                "name": "Test Track",
                "roadmap_id": "test-roadmap",
                "status": "in_progress",
                "blocked": False,
                "priority": "medium",
                "created": "2025-12-15T10:00:00Z",
                "progress": {
                    "sprints_total": 0,
                    "sprints_completed": 0,
                },
                "sprints": [],
                "dependencies": [],
                "blocks": [],
                "blocked_by": [],
                "quality_gates": [],
                "assigned_agents": [],
                "metadata": {},
            }
        }

    def test_valid_track(self, valid_track):
        """Test validating valid track."""
        validator = Validator()
        result = validator.validate_dict(valid_track, "track")
        assert result.valid

    def test_missing_root_key(self):
        """Test missing track root key."""
        validator = Validator()
        result = validator.validate_dict({"wrong_key": {}}, "track")
        assert not result.valid

    def test_invalid_track_id_format(self, valid_track):
        """Test invalid track ID format."""
        valid_track["track"]["id"] = "Invalid Track!"
        validator = Validator()
        result = validator.validate_dict(valid_track, "track")
        assert not result.valid


class TestValidatorSprint:
    """Test Validator sprint validation."""

    @pytest.fixture
    def valid_sprint(self):
        """Create a valid sprint dict."""
        return {
            "sprint": {
                "id": "01ABCDEFGHIJKLMNOPQRSTUVWX",
                "name": "Sprint 1",
                "track_id": "test-track",
                "roadmap_id": "test-roadmap",
                "status": "not_started",
                "blocked": False,
                "created": "2025-12-15T10:00:00Z",
                "progress": {
                    "development_tasks_total": 3,
                    "development_tasks_completed": 0,
                    "completion_gate_tasks_total": 1,
                    "completion_gate_tasks_completed": 0,
                    "production_gate_tasks_total": 1,
                    "production_gate_tasks_completed": 0,
                    "tasks_total": 5,
                    "tasks_completed": 0,
                },
                "development_gates": [],
                "blocks": [],
                "blocked_by": [],
                "metadata": {},
            }
        }

    def test_valid_sprint(self, valid_sprint):
        """Test validating valid sprint."""
        validator = Validator()
        result = validator.validate_dict(valid_sprint, "sprint")
        assert result.valid

    def test_missing_root_key(self):
        """Test missing sprint root key."""
        validator = Validator()
        result = validator.validate_dict({"wrong_key": {}}, "sprint")
        assert not result.valid

    def test_invalid_task_totals(self, valid_sprint):
        """Test invalid task totals."""
        valid_sprint["sprint"]["progress"]["tasks_total"] = 10  # Doesn't match sum
        validator = Validator()
        result = validator.validate_dict(valid_sprint, "sprint")
        assert not result.valid
        assert any("tasks_total doesn't match" in e for e in result.errors)


class TestValidatorTask:
    """Test Validator task validation."""

    @pytest.fixture
    def valid_task(self):
        """Create a valid task dict."""
        return {
            "task": {
                "id": "test-track-1-task-001",
                "sprint_id": "test-track-1",
                "track_id": "test-track",
                "roadmap_id": "test-roadmap",
                "task_type": "development",
                "title": "Test Task",
                "description": "A test task",
                "status": "not_started",
                "blocked": False,
                "created": "2025-12-15T10:00:00Z",
                "assigned_agent": None,
                "priority": "medium",
                "estimated_tokens": 10000,
                "complexity": "medium",
                "dependencies": [],
                "blocks": [],
                "blocked_by": [],
                "metadata": {},
            }
        }

    def test_valid_task(self, valid_task):
        """Test validating valid task."""
        validator = Validator()
        result = validator.validate_dict(valid_task, "task")
        assert result.valid

    def test_missing_task_root(self):
        """Test missing task root key."""
        validator = Validator()
        result = validator.validate_dict({"wrong_key": {}}, "task")
        # With no task, should just skip validation
        # Check it doesn't crash

    def test_gate_task_requires_gate_info(self, valid_task):
        """Test gate task requires gate_info."""
        valid_task["task"]["task_type"] = "completion_gate"
        valid_task["task"]["gate_info"] = None
        validator = Validator()
        result = validator.validate_dict(valid_task, "task")
        assert not result.valid
        assert any("gate_info" in e for e in result.errors)

    def test_development_task_no_gate_info(self, valid_task):
        """Test development task cannot have gate_info."""
        valid_task["task"]["task_type"] = "development"
        valid_task["task"]["gate_info"] = {"some": "info"}
        validator = Validator()
        result = validator.validate_dict(valid_task, "task")
        assert not result.valid
        assert any("cannot have gate_info" in e for e in result.errors)

    def test_invalid_estimated_tokens(self, valid_task):
        """Test invalid estimated_tokens."""
        valid_task["task"]["estimated_tokens"] = -100
        validator = Validator()
        result = validator.validate_dict(valid_task, "task")
        assert not result.valid
        assert any("positive" in e for e in result.errors)


class TestValidatorFile:
    """Test Validator file validation."""

    def test_file_not_found(self, tmp_path):
        """Test file not found."""
        validator = Validator()
        result = validator.validate_file(tmp_path / "nonexistent.yaml", "roadmap")
        assert not result.valid
        assert any("File not found" in e for e in result.errors)

    def test_invalid_yaml(self, tmp_path):
        """Test invalid YAML."""
        yaml_file = tmp_path / "invalid.yaml"
        yaml_file.write_text("invalid: yaml: [")
        validator = Validator()
        result = validator.validate_file(yaml_file, "roadmap")
        assert not result.valid
        assert any("YAML parse error" in e for e in result.errors)

    def test_unknown_object_type(self):
        """Test unknown object type."""
        validator = Validator()
        result = validator.validate_dict({}, "unknown_type")
        assert not result.valid
        assert any("Unknown object type" in e for e in result.errors)


class TestConvenienceFunctions:
    """Test convenience validation functions."""

    def test_validate_roadmap_dict(self):
        """Test validate_roadmap with dict."""
        result = validate_roadmap({"roadmap": {}})
        assert not result.valid  # Missing fields

    def test_validate_track_dict(self):
        """Test validate_track with dict."""
        result = validate_track({"track": {}})
        assert not result.valid

    def test_validate_sprint_dict(self):
        """Test validate_sprint with dict."""
        result = validate_sprint({"sprint": {}})
        assert not result.valid

    def test_validate_task_dict(self):
        """Test validate_task with dict."""
        result = validate_task({"task": {}})
        # Missing fields but shouldn't crash

    def test_validate_roadmap_file(self, tmp_path):
        """Test validate_roadmap with file path."""
        yaml_file = tmp_path / "roadmap.yaml"
        yaml_file.write_text("roadmap:\n  id: test")
        result = validate_roadmap(yaml_file)
        assert not result.valid  # Missing required fields


class TestValidatorProgress:
    """Test progress validation."""

    def test_valid_progress(self):
        """Test valid progress dict."""
        progress = {
            "tracks_total": 5,
            "tracks_completed": 2,
            "sprints_total": 10,
            "sprints_completed": 5,
            "tasks_total": 50,
            "tasks_completed": 25,
            "completion_percent": 50,
        }
        validator = Validator()
        validator._validate_progress(progress)
        assert len(validator.errors) == 0

    def test_completed_exceeds_total(self):
        """Test completed exceeds total."""
        progress = {
            "tracks_total": 5,
            "tracks_completed": 10,  # Exceeds total
            "sprints_total": 10,
            "sprints_completed": 5,
            "tasks_total": 50,
            "tasks_completed": 25,
            "completion_percent": 50,
        }
        validator = Validator()
        validator._validate_progress(progress)
        assert any("cannot exceed" in e for e in validator.errors)

    def test_invalid_completion_percent(self):
        """Test invalid completion percent."""
        progress = {
            "tracks_total": 5,
            "tracks_completed": 2,
            "sprints_total": 10,
            "sprints_completed": 5,
            "tasks_total": 50,
            "tasks_completed": 25,
            "completion_percent": 150,  # Invalid
        }
        validator = Validator()
        validator._validate_progress(progress)
        assert any("0-100" in e for e in validator.errors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
