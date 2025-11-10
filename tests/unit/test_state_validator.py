"""
Unit tests for StateValidator test utility.

Tests the functionality of validating repository state.
"""

import pytest
from pathlib import Path
from tests.utils import StateValidator, ValidationResult, RepoBuilder
import yaml


@pytest.mark.unit
class TestStateValidator:
    """Test StateValidator utility."""

    def test_validate_directory_structure_success(self, temp_dir):
        """Test successful directory structure validation."""
        # Create test structure
        (temp_dir / "src").mkdir()
        (temp_dir / "tests").mkdir()
        (temp_dir / "README.md").touch()

        validator = StateValidator()
        expected = {
            "directories": ["src", "tests"],
            "files": ["README.md"]
        }

        result = validator.validate_directory_structure(temp_dir, expected)

        assert result.passed
        assert len(result.errors) == 0
        assert "valid" in result.message.lower()

    def test_validate_directory_structure_missing_dir(self, temp_dir):
        """Test validation fails for missing directory."""
        validator = StateValidator()
        expected = {
            "directories": ["src", "missing"],
            "files": []
        }

        result = validator.validate_directory_structure(temp_dir, expected)

        assert not result.passed
        assert len(result.errors) > 0
        assert any("missing" in error.lower() for error in result.errors)

    def test_validate_directory_structure_missing_file(self, temp_dir):
        """Test validation fails for missing file."""
        validator = StateValidator()
        expected = {
            "directories": [],
            "files": ["missing.txt"]
        }

        result = validator.validate_directory_structure(temp_dir, expected)

        assert not result.passed
        assert "missing.txt" in result.errors[0]

    def test_validate_yaml_structure_success(self, temp_dir):
        """Test successful YAML validation."""
        yaml_file = temp_dir / "test.yaml"
        yaml_file.write_text("""
project:
  name: test
  version: 1.0.0
framework:
  mode: balanced
""")

        validator = StateValidator()
        schema = {
            "required_keys": ["project", "framework"]
        }

        result = validator.validate_yaml_structure(yaml_file, schema)

        assert result.passed
        assert len(result.errors) == 0

    def test_validate_yaml_structure_missing_key(self, temp_dir):
        """Test YAML validation fails for missing key."""
        yaml_file = temp_dir / "test.yaml"
        yaml_file.write_text("""
project:
  name: test
""")

        validator = StateValidator()
        schema = {
            "required_keys": ["project", "framework", "agents"]
        }

        result = validator.validate_yaml_structure(yaml_file, schema)

        assert not result.passed
        assert len(result.errors) >= 2
        assert any("framework" in error.lower() for error in result.errors)
        assert any("agents" in error.lower() for error in result.errors)

    def test_validate_yaml_file_not_found(self, temp_dir):
        """Test YAML validation handles missing file."""
        yaml_file = temp_dir / "missing.yaml"

        validator = StateValidator()
        schema = {"required_keys": []}

        result = validator.validate_yaml_structure(yaml_file, schema)

        assert not result.passed
        assert "not found" in result.message.lower()

    def test_validate_yaml_invalid_syntax(self, temp_dir):
        """Test YAML validation handles parse errors."""
        yaml_file = temp_dir / "bad.yaml"
        yaml_file.write_text("""
invalid: yaml: content: [
""")

        validator = StateValidator()
        schema = {"required_keys": []}

        result = validator.validate_yaml_structure(yaml_file, schema)

        assert not result.passed
        assert "parse error" in result.message.lower()

    def test_validate_yaml_key_types(self, temp_dir):
        """Test YAML validation checks key types."""
        yaml_file = temp_dir / "test.yaml"
        yaml_file.write_text("""
project:
  name: test
count: 42
enabled: true
""")

        validator = StateValidator()
        schema = {
            "key_types": {
                "project": "dict",
                "count": "int",
                "enabled": "bool"
            }
        }

        result = validator.validate_yaml_structure(yaml_file, schema)

        assert result.passed

    @pytest.mark.requires_git
    def test_validate_git_state_success(self, temp_dir):
        """Test successful git state validation."""
        import subprocess

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=temp_dir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=temp_dir, capture_output=True)

        validator = StateValidator()
        expected = {
            "branch": "main"
        }

        result = validator.validate_git_state(temp_dir, expected)

        assert result.passed or "branch" in result.errors[0]  # May fail if not on main

    def test_validate_git_state_not_a_repo(self, temp_dir):
        """Test git validation fails for non-git directory."""
        validator = StateValidator()
        expected = {"branch": "main"}

        result = validator.validate_git_state(temp_dir, expected)

        assert not result.passed
        assert "not a git repository" in result.message.lower()

    def test_validate_file_content_exact_match(self, temp_dir):
        """Test file content validation with exact match."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello, World!")

        validator = StateValidator()
        result = validator.validate_file_content(
            test_file,
            expected_content="Hello, World!"
        )

        assert result.passed

    def test_validate_file_content_exact_mismatch(self, temp_dir):
        """Test file content validation fails on mismatch."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello, World!")

        validator = StateValidator()
        result = validator.validate_file_content(
            test_file,
            expected_content="Different content"
        )

        assert not result.passed

    def test_validate_file_content_contains(self, temp_dir):
        """Test file content validation with contains check."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello, World! This is a test.")

        validator = StateValidator()
        result = validator.validate_file_content(
            test_file,
            contains=["Hello", "test"]
        )

        assert result.passed

    def test_validate_file_content_missing_substring(self, temp_dir):
        """Test file content validation fails for missing substring."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello, World!")

        validator = StateValidator()
        result = validator.validate_file_content(
            test_file,
            contains=["Hello", "missing"]
        )

        assert not result.passed
        assert any("missing" in error for error in result.errors)

    def test_validate_file_not_found(self, temp_dir):
        """Test file content validation handles missing file."""
        test_file = temp_dir / "missing.txt"

        validator = StateValidator()
        result = validator.validate_file_content(test_file, contains=["test"])

        assert not result.passed
        assert "not found" in result.message.lower()

    def test_validation_result_str(self):
        """Test ValidationResult string representation."""
        result_pass = ValidationResult(True, "Test passed", [])
        assert "✓" in str(result_pass)
        assert "Test passed" in str(result_pass)

        result_fail = ValidationResult(False, "Test failed", ["Error 1"])
        assert "✗" in str(result_fail)
        assert "Test failed" in str(result_fail)
