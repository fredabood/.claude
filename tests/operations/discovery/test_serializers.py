"""
Tests for vibey.operations.discovery.serializers module.

Tests serialization and deserialization of DiscoveryOutput objects.
"""

import pytest
import json
import yaml
from pathlib import Path
from datetime import datetime, timezone

from vibey.operations.discovery.schema import (
    DiscoveryOutput,
    DiscoveryMetadata,
    ProjectInfo,
    ProjectType,
    LanguageInfo,
    FrameworkInfo,
    FrameworkCategory,
    StructureInfo,
    DirectoryInfo,
    DirectoryPurpose,
    DependenciesInfo,
    Dependency,
)
from vibey.operations.discovery.serializers import (
    DiscoverySerializer,
    to_yaml,
    to_json,
    from_yaml,
    from_json,
    save_yaml,
    save_json,
    load_yaml,
    load_json,
)


@pytest.fixture
def sample_discovery():
    """Create a sample DiscoveryOutput for testing."""
    return DiscoveryOutput(
        metadata=DiscoveryMetadata(
            schema_version="1.0.0",
            discovered_at=datetime(2025, 12, 15, 10, 0, 0, tzinfo=timezone.utc),
            project_root="/path/to/project",
            git_commit="abc123",
            git_branch="main",
        ),
        project=ProjectInfo(
            name="test-project",
            type=ProjectType.WEB_APP,
            languages=[
                LanguageInfo(name="Python", version="3.11", percentage=80.0),
                LanguageInfo(name="JavaScript", percentage=20.0),
            ],
            frameworks=[
                FrameworkInfo(
                    name="FastAPI",
                    version="0.100.0",
                    category=FrameworkCategory.BACKEND,
                ),
            ],
        ),
        structure=StructureInfo(
            total_files=100,
            total_lines=5000,
            directories=[
                DirectoryInfo(
                    path="src",
                    purpose=DirectoryPurpose.SOURCE,
                    file_count=50,
                    line_count=3000,
                ),
            ],
            entry_points=["main.py"],
        ),
        dependencies=DependenciesInfo(
            runtime=[
                Dependency(name="fastapi", version="0.100.0"),
                Dependency(name="pydantic", version="2.0.0"),
            ],
            development=[
                Dependency(name="pytest", version="7.0.0"),
            ],
            vulnerable_count=0,
        ),
    )


class TestDiscoverySerializerToDict:
    """Test DiscoverySerializer.to_dict method."""

    def test_basic_conversion(self, sample_discovery):
        """Test basic dict conversion."""
        result = DiscoverySerializer.to_dict(sample_discovery)
        assert isinstance(result, dict)
        assert "metadata" in result
        assert "project" in result
        assert "structure" in result
        assert "dependencies" in result

    def test_project_info(self, sample_discovery):
        """Test project info is correctly converted."""
        result = DiscoverySerializer.to_dict(sample_discovery)
        assert result["project"]["name"] == "test-project"
        assert result["project"]["type"] == "web-app"
        assert len(result["project"]["languages"]) == 2

    def test_exclude_none(self, sample_discovery):
        """Test exclude_none parameter."""
        result = DiscoverySerializer.to_dict(sample_discovery, exclude_none=True)
        # Metadata should not have discovery_duration_ms since it's None
        assert "discovery_duration_ms" not in result["metadata"]

    def test_include_none(self, sample_discovery):
        """Test including None values."""
        result = DiscoverySerializer.to_dict(sample_discovery, exclude_none=False)
        # Metadata should have None fields
        assert "discovery_duration_ms" in result["metadata"]


class TestDiscoverySerializerToYaml:
    """Test DiscoverySerializer.to_yaml method."""

    def test_valid_yaml(self, sample_discovery):
        """Test YAML output is valid."""
        yaml_str = DiscoverySerializer.to_yaml(sample_discovery)
        assert isinstance(yaml_str, str)
        # Should be parseable
        data = yaml.safe_load(yaml_str)
        assert isinstance(data, dict)

    def test_yaml_content(self, sample_discovery):
        """Test YAML contains expected content."""
        yaml_str = DiscoverySerializer.to_yaml(sample_discovery)
        assert "test-project" in yaml_str
        assert "web-app" in yaml_str
        assert "Python" in yaml_str


class TestDiscoverySerializerToJson:
    """Test DiscoverySerializer.to_json method."""

    def test_valid_json(self, sample_discovery):
        """Test JSON output is valid."""
        json_str = DiscoverySerializer.to_json(sample_discovery)
        assert isinstance(json_str, str)
        # Should be parseable
        data = json.loads(json_str)
        assert isinstance(data, dict)

    def test_json_content(self, sample_discovery):
        """Test JSON contains expected content."""
        json_str = DiscoverySerializer.to_json(sample_discovery)
        assert "test-project" in json_str
        assert "web-app" in json_str

    def test_json_indentation(self, sample_discovery):
        """Test JSON indentation."""
        json_str = DiscoverySerializer.to_json(sample_discovery, indent=4)
        # With indentation, should have newlines
        assert "\n" in json_str

    def test_json_compact(self, sample_discovery):
        """Test compact JSON (no indentation)."""
        json_str = DiscoverySerializer.to_json(sample_discovery, indent=None)
        # Compact JSON has fewer newlines
        assert json_str.count("\n") < 5


class TestDiscoverySerializerFromDict:
    """Test DiscoverySerializer.from_dict method."""

    def test_roundtrip(self, sample_discovery):
        """Test dict roundtrip."""
        data = DiscoverySerializer.to_dict(sample_discovery)
        result = DiscoverySerializer.from_dict(data)
        assert isinstance(result, DiscoveryOutput)
        assert result.project.name == sample_discovery.project.name

    def test_invalid_data(self):
        """Test invalid data raises error."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            DiscoverySerializer.from_dict({"invalid": "data"})


class TestDiscoverySerializerFromYaml:
    """Test DiscoverySerializer.from_yaml method."""

    def test_roundtrip(self, sample_discovery):
        """Test YAML roundtrip."""
        yaml_str = DiscoverySerializer.to_yaml(sample_discovery)
        result = DiscoverySerializer.from_yaml(yaml_str)
        assert isinstance(result, DiscoveryOutput)
        assert result.project.name == sample_discovery.project.name

    def test_invalid_yaml(self):
        """Test invalid YAML raises error."""
        with pytest.raises(yaml.YAMLError):
            DiscoverySerializer.from_yaml("invalid: yaml: [")


class TestDiscoverySerializerFromJson:
    """Test DiscoverySerializer.from_json method."""

    def test_roundtrip(self, sample_discovery):
        """Test JSON roundtrip."""
        json_str = DiscoverySerializer.to_json(sample_discovery)
        result = DiscoverySerializer.from_json(json_str)
        assert isinstance(result, DiscoveryOutput)
        assert result.project.name == sample_discovery.project.name

    def test_invalid_json(self):
        """Test invalid JSON raises error."""
        with pytest.raises(json.JSONDecodeError):
            DiscoverySerializer.from_json("{invalid json}")


class TestDiscoverySerializerFileOperations:
    """Test DiscoverySerializer file operations."""

    def test_save_load_yaml(self, sample_discovery, tmp_path):
        """Test save and load YAML."""
        filepath = tmp_path / "discovery.yaml"
        DiscoverySerializer.save_yaml(sample_discovery, filepath)
        assert filepath.exists()

        result = DiscoverySerializer.load_yaml(filepath)
        assert isinstance(result, DiscoveryOutput)
        assert result.project.name == sample_discovery.project.name

    def test_save_yaml_creates_dirs(self, sample_discovery, tmp_path):
        """Test save_yaml creates parent directories."""
        filepath = tmp_path / "nested" / "dir" / "discovery.yaml"
        DiscoverySerializer.save_yaml(sample_discovery, filepath)
        assert filepath.exists()

    def test_save_load_json(self, sample_discovery, tmp_path):
        """Test save and load JSON."""
        filepath = tmp_path / "discovery.json"
        DiscoverySerializer.save_json(sample_discovery, filepath)
        assert filepath.exists()

        result = DiscoverySerializer.load_json(filepath)
        assert isinstance(result, DiscoveryOutput)
        assert result.project.name == sample_discovery.project.name

    def test_save_json_creates_dirs(self, sample_discovery, tmp_path):
        """Test save_json creates parent directories."""
        filepath = tmp_path / "nested" / "dir" / "discovery.json"
        DiscoverySerializer.save_json(sample_discovery, filepath)
        assert filepath.exists()

    def test_load_yaml_file_not_found(self, tmp_path):
        """Test load_yaml raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            DiscoverySerializer.load_yaml(tmp_path / "nonexistent.yaml")

    def test_load_json_file_not_found(self, tmp_path):
        """Test load_json raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            DiscoverySerializer.load_json(tmp_path / "nonexistent.json")


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    def test_to_yaml_function(self, sample_discovery):
        """Test to_yaml convenience function."""
        result = to_yaml(sample_discovery)
        assert isinstance(result, str)
        assert "test-project" in result

    def test_to_json_function(self, sample_discovery):
        """Test to_json convenience function."""
        result = to_json(sample_discovery)
        assert isinstance(result, str)
        assert "test-project" in result

    def test_from_yaml_function(self, sample_discovery):
        """Test from_yaml convenience function."""
        yaml_str = to_yaml(sample_discovery)
        result = from_yaml(yaml_str)
        assert isinstance(result, DiscoveryOutput)

    def test_from_json_function(self, sample_discovery):
        """Test from_json convenience function."""
        json_str = to_json(sample_discovery)
        result = from_json(json_str)
        assert isinstance(result, DiscoveryOutput)

    def test_save_yaml_function(self, sample_discovery, tmp_path):
        """Test save_yaml convenience function."""
        filepath = tmp_path / "test.yaml"
        save_yaml(sample_discovery, filepath)
        assert filepath.exists()

    def test_save_json_function(self, sample_discovery, tmp_path):
        """Test save_json convenience function."""
        filepath = tmp_path / "test.json"
        save_json(sample_discovery, filepath)
        assert filepath.exists()

    def test_load_yaml_function(self, sample_discovery, tmp_path):
        """Test load_yaml convenience function."""
        filepath = tmp_path / "test.yaml"
        save_yaml(sample_discovery, filepath)
        result = load_yaml(filepath)
        assert isinstance(result, DiscoveryOutput)

    def test_load_json_function(self, sample_discovery, tmp_path):
        """Test load_json convenience function."""
        filepath = tmp_path / "test.json"
        save_json(sample_discovery, filepath)
        result = load_json(filepath)
        assert isinstance(result, DiscoveryOutput)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
