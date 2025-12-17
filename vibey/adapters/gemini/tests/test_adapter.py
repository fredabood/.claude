"""Tests for GeminiAdapter."""

import json
import pytest
from pathlib import Path

from vibey.adapters.gemini.adapter import GeminiAdapter, GeminiExportResult
from vibey.adapters.base import DeploymentResult


class TestGeminiAdapter:
    """Test suite for GeminiAdapter."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with project root."""
        return GeminiAdapter(Path.cwd())

    @pytest.fixture
    def export_dir(self, tmp_path):
        """Create temporary export directory."""
        return tmp_path / "vibey-gemini-extension"

    def test_get_platform_name(self, adapter):
        """Test platform name is 'gemini'."""
        assert adapter.get_platform_name() == "gemini"

    def test_get_deployment_dir(self, adapter, tmp_path):
        """Test default deployment directory."""
        result = adapter.get_deployment_dir(tmp_path)
        assert result == tmp_path / ".gemini"

    def test_export_creates_result(self, adapter, export_dir):
        """Test that export() returns GeminiExportResult."""
        result = adapter.export(export_dir)

        assert isinstance(result, GeminiExportResult)
        assert result.output_dir == export_dir

    def test_export_success(self, adapter, export_dir):
        """Test successful export."""
        result = adapter.export(export_dir)

        assert result.success is True
        assert len(result.errors) == 0

    def test_export_creates_gemini_md(self, adapter, export_dir):
        """Test that export creates GEMINI.md."""
        adapter.export(export_dir)

        gemini_md = export_dir / "GEMINI.md"
        assert gemini_md.exists()
        content = gemini_md.read_text()
        assert "Vibey Agent Framework" in content

    def test_export_creates_commands(self, adapter, export_dir):
        """Test that export creates command TOML files."""
        result = adapter.export(export_dir)

        commands_dir = export_dir / "commands" / "vibey"
        assert commands_dir.exists()

        # Check some commands exist
        assert (commands_dir / "status.toml").exists()
        assert (commands_dir / "sprint.toml").exists()
        assert (commands_dir / "task.toml").exists()

    def test_export_creates_manifest(self, adapter, export_dir):
        """Test that export creates extension manifest."""
        adapter.export(export_dir)

        manifest_path = export_dir / "gemini-extension.json"
        assert manifest_path.exists()

        manifest = json.loads(manifest_path.read_text())
        assert manifest["name"] == "vibey"
        assert "version" in manifest

    def test_export_creates_settings(self, adapter, export_dir):
        """Test that export creates settings.json."""
        adapter.export(export_dir)

        settings_path = export_dir / "settings.json"
        assert settings_path.exists()

        settings = json.loads(settings_path.read_text())
        assert "mcpServers" in settings
        assert "vibey" in settings["mcpServers"]

    def test_export_creates_install_script(self, adapter, export_dir):
        """Test that export creates install.sh."""
        adapter.export(export_dir, include_install_script=True)

        script_path = export_dir / "install.sh"
        assert script_path.exists()
        assert script_path.stat().st_mode & 0o111  # Executable

    def test_export_creates_readme(self, adapter, export_dir):
        """Test that export creates README.md."""
        adapter.export(export_dir, include_readme=True)

        readme_path = export_dir / "README.md"
        assert readme_path.exists()
        assert "Vibey" in readme_path.read_text()

    def test_export_creates_checksums(self, adapter, export_dir):
        """Test that export creates checksums manifest."""
        adapter.export(export_dir)

        checksums_path = export_dir / ".checksums.json"
        assert checksums_path.exists()

        checksums = json.loads(checksums_path.read_text())
        assert "checksums" in checksums
        assert "GEMINI.md" in checksums["checksums"]
        assert "commands" in checksums["checksums"]

    def test_export_skips_install_script(self, adapter, export_dir):
        """Test that install script can be skipped."""
        adapter.export(export_dir, include_install_script=False)

        assert not (export_dir / "install.sh").exists()

    def test_export_skips_readme(self, adapter, export_dir):
        """Test that README can be skipped."""
        adapter.export(export_dir, include_readme=False)

        assert not (export_dir / "README.md").exists()

    def test_export_result_has_context(self, adapter, export_dir):
        """Test that result includes context metadata."""
        result = adapter.export(export_dir)

        assert result.context is not None
        assert result.context.agents_count > 0
        assert result.context.workflows_count > 0

    def test_export_result_has_commands(self, adapter, export_dir):
        """Test that result includes commands metadata."""
        result = adapter.export(export_dir)

        assert result.commands is not None
        assert len(result.commands.commands) > 0

    def test_export_result_has_checksums(self, adapter, export_dir):
        """Test that result includes checksums."""
        result = adapter.export(export_dir)

        assert "GEMINI.md" in result.checksums
        assert "commands" in result.checksums

    def test_export_result_has_duration(self, adapter, export_dir):
        """Test that result includes duration."""
        result = adapter.export(export_dir)

        assert result.duration_seconds > 0
        assert result.duration_seconds < 60  # Should be fast

    def test_validate_export_passes(self, adapter, export_dir):
        """Test that validation passes for fresh export."""
        adapter.export(export_dir)

        is_valid, errors = adapter.validate_export(export_dir)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_export_missing_checksums(self, adapter, export_dir):
        """Test that validation fails without checksums file."""
        adapter.export(export_dir)
        (export_dir / ".checksums.json").unlink()

        is_valid, errors = adapter.validate_export(export_dir)

        assert is_valid is False
        assert len(errors) > 0
        assert "checksums" in errors[0].lower()

    def test_validate_deployment(self, adapter, export_dir):
        """Test validate_deployment method."""
        adapter.export(export_dir)

        is_valid, errors = adapter.validate_deployment(export_dir)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_deployment_missing_files(self, adapter, export_dir):
        """Test validation fails for missing required files."""
        adapter.export(export_dir)
        (export_dir / "GEMINI.md").unlink()

        is_valid, errors = adapter.validate_deployment(export_dir)

        assert is_valid is False
        assert any("GEMINI.md" in e for e in errors)

    def test_deploy_interface(self, adapter, export_dir):
        """Test deploy() method (PlatformAdapter interface)."""
        result = adapter.deploy(
            source_dir=Path.cwd() / ".vibey",
            config=None,
            target_dir=export_dir,
        )

        assert isinstance(result, DeploymentResult)
        assert result.success is True
        assert result.platform == "gemini"

    def test_supports_feature(self, adapter):
        """Test feature support checking."""
        # Supported features
        assert adapter.supports_feature("agents") is True
        assert adapter.supports_feature("workflows") is True
        assert adapter.supports_feature("mcp") is True

        # Unsupported features
        assert adapter.supports_feature("subagents") is False
        assert adapter.supports_feature("parallel-tasks") is False

    def test_get_required_files(self, adapter):
        """Test getting required files list."""
        required = adapter.get_required_files()

        assert "GEMINI.md" in required
        assert "gemini-extension.json" in required
        assert "settings.json" in required

    def test_get_optional_files(self, adapter):
        """Test getting optional files list."""
        optional = adapter.get_optional_files()

        assert "commands/" in optional
        assert "install.sh" in optional
        assert "README.md" in optional


class TestGeminiExportResult:
    """Test GeminiExportResult dataclass."""

    def test_dataclass_fields(self):
        """Test GeminiExportResult has expected fields."""
        result = GeminiExportResult(
            success=True,
            output_dir=Path("/tmp/test"),
        )

        assert result.success is True
        assert result.output_dir == Path("/tmp/test")
        assert result.context is None
        assert result.commands is None
        assert result.files_created == []
        assert result.errors == []
        assert result.checksums == {}
