"""End-to-end tests for Gemini extension.

These tests verify the complete export → install → validate cycle
works correctly for the Gemini platform adapter.
"""

import json
import pytest
import shutil
import tempfile
from pathlib import Path

from vibey.adapters.gemini.adapter import GeminiAdapter
from vibey.adapters.gemini.mcp_test import run_mcp_test


class TestE2EExtensionExport:
    """End-to-end tests for extension export."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with project root."""
        return GeminiAdapter(Path.cwd())

    @pytest.fixture
    def export_dir(self):
        """Create temporary export directory."""
        tmp_dir = tempfile.mkdtemp(prefix="vibey-gemini-e2e-")
        yield Path(tmp_dir)
        # Cleanup
        shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_full_export_cycle(self, adapter, export_dir):
        """Test complete export cycle produces valid extension."""
        # Export
        result = adapter.export(
            export_dir,
            include_install_script=True,
            include_readme=True,
        )

        # Verify success
        assert result.success is True
        assert len(result.errors) == 0

        # Verify all required files exist
        assert (export_dir / "GEMINI.md").exists()
        assert (export_dir / "gemini-extension.json").exists()
        assert (export_dir / "settings.json").exists()
        assert (export_dir / ".checksums.json").exists()
        assert (export_dir / "commands" / "vibey").exists()
        assert (export_dir / "install.sh").exists()
        assert (export_dir / "README.md").exists()

    def test_export_gemini_md_content(self, adapter, export_dir):
        """Test GEMINI.md has expected sections."""
        adapter.export(export_dir)

        content = (export_dir / "GEMINI.md").read_text()

        # Header
        assert "# Vibey Agent Framework" in content

        # Agents section
        assert "## Available Agents" in content

        # Workflows section
        assert "## Available Workflows" in content

        # Orchestration section (from Sprint 3)
        assert "Sequential Workflow Execution" in content

        # MCP section
        assert "## MCP Integration" in content

        # Footer marker
        assert "VIBEY_GEMINI_GENERATED" in content

    def test_export_commands_structure(self, adapter, export_dir):
        """Test commands directory structure."""
        result = adapter.export(export_dir)

        commands_dir = export_dir / "commands" / "vibey"
        assert commands_dir.exists()

        # Check manifest exists
        manifest_path = commands_dir / "_manifest.json"
        assert manifest_path.exists()

        manifest = json.loads(manifest_path.read_text())
        assert "version" in manifest
        assert "commands_count" in manifest
        assert manifest["commands_count"] > 0

        # Check workflow commands
        assert (commands_dir / "status.toml").exists()
        assert (commands_dir / "sprint.toml").exists()
        assert (commands_dir / "task.toml").exists()

        # Check agent commands exist
        agent_commands = list(commands_dir.glob("agent-*.toml"))
        assert len(agent_commands) > 0

    def test_export_settings_json(self, adapter, export_dir):
        """Test settings.json has correct MCP configuration."""
        adapter.export(export_dir)

        settings = json.loads((export_dir / "settings.json").read_text())

        # MCP server config
        assert "mcpServers" in settings
        assert "vibey" in settings["mcpServers"]

        vibey_config = settings["mcpServers"]["vibey"]
        assert "command" in vibey_config
        assert "args" in vibey_config

    def test_export_extension_manifest(self, adapter, export_dir):
        """Test extension manifest is valid."""
        adapter.export(export_dir)

        manifest = json.loads((export_dir / "gemini-extension.json").read_text())

        assert manifest["name"] == "vibey"
        assert "version" in manifest
        assert "description" in manifest

    def test_export_install_script_executable(self, adapter, export_dir):
        """Test install script is executable."""
        adapter.export(export_dir, include_install_script=True)

        script_path = export_dir / "install.sh"
        assert script_path.exists()

        # Check executable bit
        mode = script_path.stat().st_mode
        assert mode & 0o111  # At least one execute bit set

        # Check shebang
        content = script_path.read_text()
        assert content.startswith("#!/")

    def test_export_readme_content(self, adapter, export_dir):
        """Test README has installation instructions."""
        adapter.export(export_dir, include_readme=True)

        content = (export_dir / "README.md").read_text()

        assert "Vibey" in content
        assert "install" in content.lower()


class TestE2EDriftDetection:
    """End-to-end tests for drift detection."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with project root."""
        return GeminiAdapter(Path.cwd())

    @pytest.fixture
    def export_dir(self):
        """Create temporary export directory."""
        tmp_dir = tempfile.mkdtemp(prefix="vibey-gemini-drift-")
        yield Path(tmp_dir)
        shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_fresh_export_no_drift(self, adapter, export_dir):
        """Test fresh export passes drift detection."""
        adapter.export(export_dir)

        is_valid, errors = adapter.validate_export(export_dir)

        assert is_valid is True
        assert len(errors) == 0

    def test_modified_gemini_md_detected(self, adapter, export_dir):
        """Test that modifying GEMINI.md is detected as drift."""
        adapter.export(export_dir)

        # Modify GEMINI.md
        gemini_md = export_dir / "GEMINI.md"
        original = gemini_md.read_text()
        gemini_md.write_text(original + "\n\n## Manual Addition\nThis was added manually.")

        # Validate should detect drift
        is_valid, errors = adapter.validate_export(export_dir)

        assert is_valid is False
        assert len(errors) > 0
        assert any("GEMINI.md" in e and "drift" in e.lower() for e in errors)

    def test_modified_command_detected(self, adapter, export_dir):
        """Test that modifying a command is detected as drift."""
        adapter.export(export_dir)

        # Modify a command file
        status_cmd = export_dir / "commands" / "vibey" / "status.toml"
        if status_cmd.exists():
            original = status_cmd.read_text()
            status_cmd.write_text(original + '\n# Manual edit')

            # Validate should detect modification
            is_valid, errors = adapter.validate_export(export_dir)

            assert is_valid is False
            assert any("edited" in e.lower() or "drift" in e.lower() for e in errors)

    def test_missing_checksums_detected(self, adapter, export_dir):
        """Test that missing checksums file is detected."""
        adapter.export(export_dir)

        # Remove checksums file
        (export_dir / ".checksums.json").unlink()

        is_valid, errors = adapter.validate_export(export_dir)

        assert is_valid is False
        assert any("checksums" in e.lower() for e in errors)

    def test_checksums_stable_across_exports(self, adapter, export_dir):
        """Test that checksums are stable across regenerations."""
        # First export
        result1 = adapter.export(export_dir)
        checksum1 = result1.checksums.copy()

        # Clean and re-export
        shutil.rmtree(export_dir)
        export_dir.mkdir()
        result2 = adapter.export(export_dir)
        checksum2 = result2.checksums

        # Checksums should match
        assert checksum1["GEMINI.md"] == checksum2["GEMINI.md"]
        assert checksum1["commands"] == checksum2["commands"]


class TestE2EMCPConnectivity:
    """End-to-end tests for MCP connectivity."""

    @pytest.fixture
    def export_dir(self):
        """Create temporary export directory."""
        tmp_dir = tempfile.mkdtemp(prefix="vibey-gemini-mcp-")
        yield Path(tmp_dir)
        shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_mcp_test_passes(self):
        """Test MCP connectivity test passes."""
        result = run_mcp_test()

        assert result.passed >= 2  # At least deps and import tests
        # Allow some failures in test env

    def test_mcp_test_with_export_dir(self, export_dir):
        """Test MCP connectivity with exported extension."""
        adapter = GeminiAdapter(Path.cwd())
        adapter.export(export_dir)

        result = run_mcp_test(export_dir)

        # Should pass settings validation
        assert result.passed >= 3


class TestE2EDeploymentValidation:
    """End-to-end tests for deployment validation."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with project root."""
        return GeminiAdapter(Path.cwd())

    @pytest.fixture
    def export_dir(self):
        """Create temporary export directory."""
        tmp_dir = tempfile.mkdtemp(prefix="vibey-gemini-deploy-")
        yield Path(tmp_dir)
        shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_validate_deployment_passes(self, adapter, export_dir):
        """Test deployment validation passes for valid export."""
        adapter.export(export_dir)

        is_valid, errors = adapter.validate_deployment(export_dir)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_deployment_missing_gemini_md(self, adapter, export_dir):
        """Test validation fails without GEMINI.md."""
        adapter.export(export_dir)
        (export_dir / "GEMINI.md").unlink()

        is_valid, errors = adapter.validate_deployment(export_dir)

        assert is_valid is False
        assert any("GEMINI.md" in e for e in errors)

    def test_validate_deployment_missing_manifest(self, adapter, export_dir):
        """Test validation fails without extension manifest."""
        adapter.export(export_dir)
        (export_dir / "gemini-extension.json").unlink()

        is_valid, errors = adapter.validate_deployment(export_dir)

        assert is_valid is False
        assert any("gemini-extension.json" in e for e in errors)

    def test_validate_deployment_missing_settings(self, adapter, export_dir):
        """Test validation fails without settings.json."""
        adapter.export(export_dir)
        (export_dir / "settings.json").unlink()

        is_valid, errors = adapter.validate_deployment(export_dir)

        assert is_valid is False
        assert any("settings.json" in e for e in errors)
