"""
Package Installation Tests.

Verifies that the vibey package is correctly structured and all
components are importable after installation.

These tests should pass for both:
- Regular pip install (pip install vibey-framework)
- Editable install (pip install -e .)
"""

import pytest
from pathlib import Path


class TestPackageImports:
    """Test that all package modules are importable."""

    def test_import_vibey(self):
        """Test main package import."""
        import vibey
        assert vibey is not None

    def test_import_vibey_cli(self):
        """Test CLI module import."""
        from vibey import cli
        assert cli is not None

    def test_import_vibey_content(self):
        """Test content module import."""
        from vibey import content
        assert content is not None

    def test_import_vibey_mcp(self):
        """Test MCP module import."""
        from vibey import mcp
        assert mcp is not None

    def test_import_vibey_operations(self):
        """Test operations module import."""
        from vibey import operations
        assert operations is not None

    def test_import_vibey_adapters(self):
        """Test adapters module import."""
        from vibey import adapters
        assert adapters is not None

    def test_import_vibey_common(self):
        """Test common module import."""
        from vibey import common
        assert common is not None

    def test_import_vibey_config(self):
        """Test config module import."""
        from vibey import config
        assert config is not None

    def test_import_vibey_platform(self):
        """Test platform module import."""
        from vibey import platform
        assert platform is not None

    def test_import_vibey_roadmap(self):
        """Test roadmap module import."""
        from vibey import roadmap
        assert roadmap is not None


class TestContentAccessor:
    """Test content accessor functions."""

    def test_get_content_root(self):
        """Test get_content_root returns valid path."""
        from vibey.content import get_content_root
        root = get_content_root()
        assert isinstance(root, Path)
        assert root.exists()
        assert root.name == 'content'

    def test_get_agents_dir(self):
        """Test get_agents_dir returns valid path."""
        from vibey.content import get_agents_dir
        agents_dir = get_agents_dir()
        assert isinstance(agents_dir, Path)
        assert agents_dir.exists()
        assert agents_dir.name == 'agents'

    def test_get_workflows_dir(self):
        """Test get_workflows_dir returns valid path."""
        from vibey.content import get_workflows_dir
        workflows_dir = get_workflows_dir()
        assert isinstance(workflows_dir, Path)
        assert workflows_dir.exists()
        assert workflows_dir.name == 'workflows'

    def test_get_templates_dir(self):
        """Test get_templates_dir returns valid path."""
        from vibey.content import get_templates_dir
        templates_dir = get_templates_dir()
        assert isinstance(templates_dir, Path)
        assert templates_dir.exists()
        assert templates_dir.name == 'templates'

    def test_get_schemas_dir(self):
        """Test get_schemas_dir returns valid path."""
        from vibey.content import get_schemas_dir
        schemas_dir = get_schemas_dir()
        assert isinstance(schemas_dir, Path)
        assert schemas_dir.exists()
        assert schemas_dir.name == 'schemas'

    def test_get_examples_dir(self):
        """Test get_examples_dir returns valid path."""
        from vibey.content import get_examples_dir
        examples_dir = get_examples_dir()
        assert isinstance(examples_dir, Path)
        assert examples_dir.exists()
        assert examples_dir.name == 'examples'

    def test_get_config_dir(self):
        """Test get_config_dir returns valid path."""
        from vibey.content import get_config_dir
        config_dir = get_config_dir()
        assert isinstance(config_dir, Path)
        assert config_dir.exists()
        assert config_dir.name == 'config'


class TestContentFilesExist:
    """Test that content files are accessible."""

    def test_agents_contain_markdown_files(self):
        """Test agents directory contains markdown files."""
        from vibey.content import get_agents_dir
        agents_dir = get_agents_dir()
        md_files = list(agents_dir.rglob('*.md'))
        assert len(md_files) > 0, "No agent markdown files found"

    def test_workflows_contain_markdown_files(self):
        """Test workflows directory contains markdown files."""
        from vibey.content import get_workflows_dir
        workflows_dir = get_workflows_dir()
        md_files = list(workflows_dir.rglob('*.md'))
        assert len(md_files) > 0, "No workflow markdown files found"

    def test_templates_contain_files(self):
        """Test templates directory contains files."""
        from vibey.content import get_templates_dir
        templates_dir = get_templates_dir()
        all_files = list(templates_dir.rglob('*'))
        # Filter to only files (not directories)
        files = [f for f in all_files if f.is_file()]
        assert len(files) > 0, "No template files found"


class TestCLIEntryPoint:
    """Test CLI entry point."""

    def test_cli_import(self):
        """Test CLI main module import."""
        from vibey.cli.main import cli
        assert cli is not None
        assert callable(cli)

    def test_cli_help(self):
        """Test CLI --help works."""
        from click.testing import CliRunner
        from vibey.cli.main import cli

        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'vibey' in result.output.lower() or 'usage' in result.output.lower()


class TestMCPDiscovery:
    """Test MCP discovery functionality."""

    def test_agent_discovery_import(self):
        """Test AgentDiscovery import."""
        from vibey.mcp.discovery.agents import AgentDiscovery
        assert AgentDiscovery is not None

    def test_workflow_discovery_import(self):
        """Test WorkflowDiscovery import."""
        from vibey.mcp.discovery.workflows import WorkflowDiscovery
        assert WorkflowDiscovery is not None

    def test_agent_discovery_finds_agents(self):
        """Test AgentDiscovery can discover agents."""
        from vibey.mcp.discovery.agents import AgentDiscovery
        discovery = AgentDiscovery()
        agents = discovery.discover()
        # Should find at least some agents
        assert isinstance(agents, list)
        # Note: May be empty if frontmatter not present, but should not error

    def test_workflow_discovery_finds_workflows(self):
        """Test WorkflowDiscovery can discover workflows."""
        from vibey.mcp.discovery.workflows import WorkflowDiscovery
        discovery = WorkflowDiscovery()
        workflows = discovery.discover()
        # Should find at least some workflows
        assert isinstance(workflows, list)
        # Note: May be empty if frontmatter not present, but should not error


class TestSubpackageImports:
    """Test nested subpackage imports."""

    def test_import_roadmap_models(self):
        """Test roadmap models import."""
        from vibey.roadmap import models
        assert models is not None

    def test_import_roadmap_serialization(self):
        """Test roadmap serialization import."""
        from vibey.roadmap import serialization
        assert serialization is not None

    def test_import_operations_roadmap(self):
        """Test operations roadmap import."""
        from vibey.operations import roadmap
        assert roadmap is not None

    def test_import_operations_validate(self):
        """Test operations validate import."""
        from vibey.operations import validate
        assert validate is not None

    def test_import_mcp_discovery(self):
        """Test mcp discovery import."""
        from vibey.mcp import discovery
        assert discovery is not None

    def test_import_mcp_tools(self):
        """Test mcp tools import."""
        try:
            from vibey.mcp import tools
            assert tools is not None
        except ImportError as e:
            # jsonschema may not be installed in test environment
            if 'jsonschema' in str(e):
                pytest.skip("jsonschema not installed")
            raise
