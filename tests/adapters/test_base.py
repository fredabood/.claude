"""
Tests for vibey.adapters.base module.

Tests DeploymentResult dataclass and PlatformAdapter abstract class.
"""

import pytest
from pathlib import Path
from datetime import datetime
from typing import List, Any, Optional

from vibey.adapters.base import DeploymentResult, PlatformAdapter


class TestDeploymentResult:
    """Test DeploymentResult dataclass."""

    def test_successful_deployment(self):
        """Test creating a successful deployment result."""
        result = DeploymentResult(
            success=True,
            platform="claude-code",
            target_dir=Path("/project/.claude"),
            files_created=[Path("CLAUDE.md")],
            files_updated=[],
            files_deleted=[],
            validation_passed=True,
        )
        assert result.success is True
        assert result.platform == "claude-code"
        assert result.validation_passed is True

    def test_failed_deployment(self):
        """Test creating a failed deployment result."""
        result = DeploymentResult(
            success=False,
            platform="goose",
            target_dir=Path("/project/.goose"),
            errors=["Missing required file", "Invalid config"],
            validation_passed=False,
        )
        assert result.success is False
        assert len(result.errors) == 2
        assert result.validation_passed is False

    def test_str_successful(self):
        """Test string representation for success."""
        result = DeploymentResult(
            success=True,
            platform="claude-code",
            target_dir=Path("/project/.claude"),
            files_created=[Path("f1.md"), Path("f2.md")],
            files_updated=[Path("f3.md")],
            duration_seconds=1.5,
        )
        s = str(result)
        assert "Success" in s
        assert "claude-code" in s
        assert "2 created" in s
        assert "1 updated" in s
        assert "1.50s" in s

    def test_str_failed(self):
        """Test string representation for failure."""
        result = DeploymentResult(
            success=False,
            platform="test",
            target_dir=Path("/tmp"),
            validation_passed=False,
        )
        s = str(result)
        assert "Failed" in s
        assert "Validation" in s

    def test_default_lists(self):
        """Test default list values."""
        result = DeploymentResult(
            success=True,
            platform="test",
            target_dir=Path("/tmp"),
        )
        assert result.files_created == []
        assert result.files_updated == []
        assert result.files_deleted == []
        assert result.errors == []
        assert result.warnings == []

    def test_default_timestamp(self):
        """Test default timestamp is set."""
        result = DeploymentResult(
            success=True,
            platform="test",
            target_dir=Path("/tmp"),
        )
        assert result.timestamp is not None
        assert isinstance(result.timestamp, datetime)


class MockAdapter(PlatformAdapter):
    """Mock adapter for testing."""

    def __init__(self, name: str = "mock-platform"):
        self._name = name
        self._required_files = ["context.md"]
        self._optional_files = ["custom/"]
        self._supported_features = {"agents", "workflows"}

    def get_platform_name(self) -> str:
        return self._name

    def get_deployment_dir(self, project_root: Optional[Path] = None) -> Path:
        root = project_root or Path.cwd()
        return root / f".{self._name}"

    def deploy(
        self,
        source_dir: Path,
        config: Any,
        target_dir: Optional[Path] = None,
        clean: bool = False,
    ) -> DeploymentResult:
        target = target_dir or self.get_deployment_dir()
        return DeploymentResult(
            success=True,
            platform=self._name,
            target_dir=target,
            files_created=[target / "context.md"],
        )

    def generate_context_file(self, config: Any, output_path: Path) -> None:
        output_path.write_text("# Mock Context")

    def validate_deployment(self, deployment_dir: Path) -> tuple[bool, List[str]]:
        if not deployment_dir.exists():
            return False, ["Deployment directory does not exist"]
        return True, []

    def get_required_files(self) -> List[str]:
        return self._required_files

    def get_optional_files(self) -> List[str]:
        return self._optional_files

    def supports_feature(self, feature: str) -> bool:
        return feature in self._supported_features


class TestPlatformAdapter:
    """Test PlatformAdapter abstract class through MockAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create a mock adapter instance."""
        return MockAdapter()

    def test_get_platform_name(self, adapter):
        """Test getting platform name."""
        assert adapter.get_platform_name() == "mock-platform"

    def test_get_deployment_dir(self, adapter, tmp_path):
        """Test getting deployment directory."""
        deploy_dir = adapter.get_deployment_dir(tmp_path)
        assert deploy_dir == tmp_path / ".mock-platform"

    def test_get_deployment_dir_default(self, adapter):
        """Test deployment dir defaults to cwd."""
        deploy_dir = adapter.get_deployment_dir()
        assert ".mock-platform" in str(deploy_dir)

    def test_deploy(self, adapter, tmp_path):
        """Test deploy method."""
        result = adapter.deploy(
            source_dir=tmp_path / ".vibey",
            config={},
            target_dir=tmp_path / ".mock-platform",
        )
        assert result.success is True
        assert result.platform == "mock-platform"
        assert len(result.files_created) == 1

    def test_generate_context_file(self, adapter, tmp_path):
        """Test generating context file."""
        output = tmp_path / "context.md"
        adapter.generate_context_file({}, output)
        assert output.exists()
        assert "Mock Context" in output.read_text()

    def test_validate_deployment_exists(self, adapter, tmp_path):
        """Test validation when deployment exists."""
        tmp_path.mkdir(exist_ok=True)
        is_valid, errors = adapter.validate_deployment(tmp_path)
        assert is_valid is True
        assert errors == []

    def test_validate_deployment_missing(self, adapter, tmp_path):
        """Test validation when deployment missing."""
        missing = tmp_path / "nonexistent"
        is_valid, errors = adapter.validate_deployment(missing)
        assert is_valid is False
        assert len(errors) > 0

    def test_get_required_files(self, adapter):
        """Test getting required files."""
        files = adapter.get_required_files()
        assert "context.md" in files

    def test_get_optional_files(self, adapter):
        """Test getting optional files."""
        files = adapter.get_optional_files()
        assert "custom/" in files

    def test_supports_feature_true(self, adapter):
        """Test supported feature returns True."""
        assert adapter.supports_feature("agents") is True
        assert adapter.supports_feature("workflows") is True

    def test_supports_feature_false(self, adapter):
        """Test unsupported feature returns False."""
        assert adapter.supports_feature("recipes") is False

    def test_get_metadata(self, adapter):
        """Test getting adapter metadata."""
        metadata = adapter.get_metadata()
        assert metadata["platform"] == "mock-platform"
        assert "adapter_version" in metadata
        assert "vibey_version" in metadata

    def test_pre_deploy_hook(self, adapter, tmp_path):
        """Test pre-deploy hook can be called."""
        # Should not raise
        adapter.pre_deploy_hook(tmp_path / ".vibey", tmp_path / ".mock")

    def test_post_deploy_hook(self, adapter, tmp_path):
        """Test post-deploy hook can be called."""
        result = DeploymentResult(
            success=True,
            platform="mock",
            target_dir=tmp_path,
        )
        # Should not raise
        adapter.post_deploy_hook(result)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
