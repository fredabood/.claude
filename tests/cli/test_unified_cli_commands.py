"""
Tests for unified CLI commands.

Tests that unified commands work correctly via CLI invocation
and verifies CLI/MCP parity for commands defined with @unified_command.
"""

import pytest
from click.testing import CliRunner
from pathlib import Path


class TestUnifiedCommandsViaCLI:
    """Test unified commands invoked via CLI."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def cli(self):
        """Import CLI for testing."""
        from vibey.cli.main import cli
        return cli

    def test_roadmap_status_command_runs(self, cli_runner, cli):
        """Test roadmap status command can be invoked."""
        result = cli_runner.invoke(cli, ["roadmap", "status"])
        # May fail due to no roadmap, but should not crash
        assert result.exception is None or "not found" in str(result.output).lower()

    def test_roadmap_show_command_missing_arg(self, cli_runner, cli):
        """Test roadmap show requires item_id argument."""
        result = cli_runner.invoke(cli, ["roadmap", "show"])
        assert result.exit_code != 0
        # Should indicate missing argument
        assert "missing" in result.output.lower() or "required" in result.output.lower() or "usage" in result.output.lower()

    def test_roadmap_show_command_invalid_id(self, cli_runner, cli):
        """Test roadmap show with invalid ID returns error."""
        result = cli_runner.invoke(cli, ["roadmap", "show", "invalid-id-12345"])
        # Should fail with helpful message
        assert result.exit_code != 0 or "not found" in result.output.lower()

    def test_deploy_list_command_runs(self, cli_runner, cli):
        """Test deploy list command runs successfully."""
        result = cli_runner.invoke(cli, ["deploy", "list"])
        assert result.exit_code == 0
        # Should list some platforms
        assert "claude" in result.output.lower() or "cursor" in result.output.lower() or "copilot" in result.output.lower()

    def test_docs_generate_cli_help(self, cli_runner, cli):
        """Test docs generate-cli shows help."""
        result = cli_runner.invoke(cli, ["docs", "generate-cli", "--help"])
        assert result.exit_code == 0
        assert "cli" in result.output.lower()

    def test_docs_generate_mcp_help(self, cli_runner, cli):
        """Test docs generate-mcp shows help."""
        result = cli_runner.invoke(cli, ["docs", "generate-mcp", "--help"])
        assert result.exit_code == 0
        assert "mcp" in result.output.lower()


class TestParityCommands:
    """Test parity checking commands."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def cli(self):
        """Import CLI for testing."""
        from vibey.cli.main import cli
        return cli

    def test_parity_check_runs(self, cli_runner, cli):
        """Test parity check command runs."""
        result = cli_runner.invoke(cli, ["parity", "check"])
        # Exit code 0 = pass, 1 = violations - both are valid outcomes
        assert result.exit_code in [0, 1]
        assert "parity" in result.output.lower() or "cli" in result.output.lower() or "mcp" in result.output.lower()

    def test_parity_check_verbose(self, cli_runner, cli):
        """Test parity check with verbose flag."""
        result = cli_runner.invoke(cli, ["parity", "check", "-v"])
        assert result.exit_code in [0, 1]
        # Verbose should show more detail
        assert len(result.output) > 0

    def test_parity_report_runs(self, cli_runner, cli):
        """Test parity report command runs."""
        result = cli_runner.invoke(cli, ["parity", "report"])
        assert result.exit_code == 0
        # Should contain report content
        assert "parity" in result.output.lower() or "report" in result.output.lower() or "commands" in result.output.lower()


class TestCLIMCPParity:
    """Test CLI/MCP output parity for unified commands."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def cli(self):
        """Import CLI for testing."""
        from vibey.cli.main import cli
        return cli

    def test_deploy_list_cli_succeeds(self, cli_runner, cli):
        """Test deploy list via CLI."""
        result = cli_runner.invoke(cli, ["deploy", "list"])
        assert result.exit_code == 0

    @pytest.mark.asyncio
    async def test_deploy_list_mcp_succeeds(self):
        """Test deploy list via MCP."""
        try:
            from vibey.unified.adapters.mcp_adapter import handle_unified_tool_call
            result = await handle_unified_tool_call("vibey_deploy_list", {})
            assert result is not None
        except ImportError:
            pytest.skip("Unified adapter not available")

    @pytest.mark.asyncio
    async def test_roadmap_status_both_interfaces(self, cli_runner, cli, tmp_path):
        """Test roadmap status available in both CLI and MCP."""
        # CLI
        cli_result = cli_runner.invoke(cli, ["roadmap", "status"])
        # Should run (may fail due to no roadmap, but shouldn't crash)
        cli_ran = cli_result.exception is None or "no roadmap" in str(cli_result.output).lower()

        # MCP
        try:
            from vibey.unified.adapters.mcp_adapter import handle_unified_tool_call
            mcp_result = await handle_unified_tool_call(
                "vibey_roadmap_status",
                {},
                root_dir=tmp_path
            )
            mcp_ran = mcp_result is not None
        except ImportError:
            mcp_ran = False
            pytest.skip("Unified adapter not available")

        # Both should run without crashing
        assert cli_ran and mcp_ran


class TestCLIErrorHandling:
    """Test CLI error handling and messages."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def cli(self):
        """Import CLI for testing."""
        from vibey.cli.main import cli
        return cli

    def test_unknown_command_shows_help(self, cli_runner, cli):
        """Test unknown command shows usage help."""
        result = cli_runner.invoke(cli, ["nonexistent"])
        assert result.exit_code != 0
        # Should show available commands or usage
        assert "usage" in result.output.lower() or "error" in result.output.lower()

    def test_unknown_subcommand_shows_help(self, cli_runner, cli):
        """Test unknown subcommand shows help."""
        result = cli_runner.invoke(cli, ["roadmap", "nonexistent"])
        assert result.exit_code != 0
        # Should show available subcommands
        assert "usage" in result.output.lower() or "error" in result.output.lower() or "no such command" in result.output.lower()

    def test_help_flag_works(self, cli_runner, cli):
        """Test --help flag shows help."""
        result = cli_runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "usage" in result.output.lower() or "options" in result.output.lower()

    def test_version_flag_works(self, cli_runner, cli):
        """Test --version flag shows version."""
        result = cli_runner.invoke(cli, ["--version"])
        # Should show version or at least not crash
        assert result.exit_code == 0 or "version" in result.output.lower()


class TestDeployCommands:
    """Test deploy commands."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def cli(self):
        """Import CLI for testing."""
        from vibey.cli.main import cli
        return cli

    def test_deploy_list_shows_platforms(self, cli_runner, cli):
        """Test deploy list shows available platforms."""
        result = cli_runner.invoke(cli, ["deploy", "list"])
        assert result.exit_code == 0
        # Should show at least one platform
        platforms = ["cursor", "claude", "copilot", "vscode", "goose"]
        has_platform = any(p in result.output.lower() for p in platforms)
        assert has_platform, f"No known platform found in output: {result.output}"

    def test_deploy_run_invalid_platform(self, cli_runner, cli):
        """Test deploy run with invalid platform shows error."""
        result = cli_runner.invoke(cli, ["deploy", "run", "--platform", "invalid-platform-xyz"])
        assert result.exit_code != 0
        # Should indicate invalid platform
        assert "invalid" in result.output.lower() or "unknown" in result.output.lower() or "error" in result.output.lower()

    def test_deploy_run_dry_run(self, cli_runner, cli, tmp_path):
        """Test deploy run with dry-run flag."""
        result = cli_runner.invoke(
            cli,
            ["deploy", "run", "--platform", "cursor", "--dry-run"],
            env={"HOME": str(tmp_path)}
        )
        # Dry run should show what would be done
        assert "dry" in result.output.lower() or result.exit_code == 0


class TestDocsCommands:
    """Test docs commands."""

    @pytest.fixture
    def cli_runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def cli(self):
        """Import CLI for testing."""
        from vibey.cli.main import cli
        return cli

    def test_docs_generate_cli_runs(self, cli_runner, cli, tmp_path):
        """Test docs generate-cli creates output."""
        output_file = tmp_path / "CLI_REFERENCE.md"
        result = cli_runner.invoke(
            cli,
            ["docs", "generate-cli", "-o", str(output_file)]
        )
        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "CLI" in content

    def test_docs_generate_mcp_runs(self, cli_runner, cli, tmp_path):
        """Test docs generate-mcp creates output."""
        output_file = tmp_path / "MCP_REFERENCE.md"
        result = cli_runner.invoke(
            cli,
            ["docs", "generate-mcp", "-o", str(output_file)]
        )
        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "MCP" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
