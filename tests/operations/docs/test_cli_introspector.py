"""
Tests for CLI introspector module.

Tests the CLI introspection capability for auto-generating CLI reference documentation.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import click

from vibey.operations.docs.cli_introspector import (
    ParamKind,
    ParamInfo,
    ExampleInfo,
    CommandInfo,
    CLIStructure,
    CLIIntrospector,
    introspect_cli,
    get_command_by_path,
    list_all_commands,
)


class TestParamKind:
    """Test ParamKind enum."""

    def test_option_value(self):
        """Test OPTION has correct value."""
        assert ParamKind.OPTION.value == "option"

    def test_argument_value(self):
        """Test ARGUMENT has correct value."""
        assert ParamKind.ARGUMENT.value == "argument"


class TestParamInfo:
    """Test ParamInfo dataclass."""

    def test_basic_construction(self):
        """Test basic ParamInfo construction."""
        param = ParamInfo(
            name="verbose",
            kind=ParamKind.OPTION,
            type_str="BOOL",
            required=False,
        )
        assert param.name == "verbose"
        assert param.kind == ParamKind.OPTION
        assert param.type_str == "BOOL"
        assert param.required is False

    def test_default_values(self):
        """Test ParamInfo default values."""
        param = ParamInfo(
            name="test",
            kind=ParamKind.ARGUMENT,
            type_str="STRING",
            required=True,
        )
        assert param.default is None
        assert param.help is None
        assert param.multiple is False
        assert param.is_flag is False
        assert param.envvar is None
        assert param.opts == []

    def test_full_construction(self):
        """Test ParamInfo with all fields."""
        param = ParamInfo(
            name="output",
            kind=ParamKind.OPTION,
            type_str="PATH",
            required=False,
            default="/tmp/out",
            help="Output file path",
            multiple=True,
            is_flag=False,
            envvar="OUTPUT_PATH",
            opts=["-o", "--output"],
        )
        assert param.name == "output"
        assert param.default == "/tmp/out"
        assert param.help == "Output file path"
        assert param.multiple is True
        assert param.envvar == "OUTPUT_PATH"
        assert param.opts == ["-o", "--output"]

    def test_to_dict(self):
        """Test to_dict serialization."""
        param = ParamInfo(
            name="format",
            kind=ParamKind.OPTION,
            type_str="Choice(['json', 'yaml'])",
            required=False,
            default="json",
            help="Output format",
            opts=["--format", "-f"],
        )
        result = param.to_dict()

        assert result["name"] == "format"
        assert result["kind"] == "option"
        assert result["type_str"] == "Choice(['json', 'yaml'])"
        assert result["required"] is False
        assert result["default"] == "json"
        assert result["help"] == "Output format"
        assert result["opts"] == ["--format", "-f"]


class TestExampleInfo:
    """Test ExampleInfo dataclass."""

    def test_basic_construction(self):
        """Test basic ExampleInfo construction."""
        example = ExampleInfo(command="vibey status")
        assert example.command == "vibey status"
        assert example.description is None

    def test_full_construction(self):
        """Test ExampleInfo with description."""
        example = ExampleInfo(
            command="vibey roadmap list tasks",
            description="List all tasks in the roadmap",
        )
        assert example.command == "vibey roadmap list tasks"
        assert example.description == "List all tasks in the roadmap"

    def test_to_dict(self):
        """Test to_dict serialization."""
        example = ExampleInfo(
            command="vibey roadmap start task-001",
            description="Start a specific task",
        )
        result = example.to_dict()

        assert result["command"] == "vibey roadmap start task-001"
        assert result["description"] == "Start a specific task"


class TestCommandInfo:
    """Test CommandInfo dataclass."""

    def test_basic_construction(self):
        """Test basic CommandInfo construction."""
        cmd = CommandInfo(name="status", path="vibey status")
        assert cmd.name == "status"
        assert cmd.path == "vibey status"

    def test_default_values(self):
        """Test CommandInfo default values."""
        cmd = CommandInfo(name="test", path="test")
        assert cmd.help is None
        assert cmd.short_help is None
        assert cmd.params == []
        assert cmd.subcommands == []
        assert cmd.examples == []
        assert cmd.deprecated is False
        assert cmd.hidden is False
        assert cmd.is_group is False

    def test_full_construction(self):
        """Test CommandInfo with all fields."""
        cmd = CommandInfo(
            name="roadmap",
            path="vibey roadmap",
            help="Roadmap management commands",
            short_help="Roadmap commands",
            params=[ParamInfo("verbose", ParamKind.OPTION, "BOOL", False)],
            subcommands=[CommandInfo("status", "vibey roadmap status")],
            examples=[ExampleInfo("vibey roadmap status")],
            deprecated=False,
            hidden=False,
            is_group=True,
        )
        assert cmd.name == "roadmap"
        assert cmd.is_group is True
        assert len(cmd.subcommands) == 1
        assert len(cmd.params) == 1

    def test_count_commands_single(self):
        """Test count_commands for single command."""
        cmd = CommandInfo(name="status", path="vibey status")
        total, depth = cmd.count_commands()
        assert total == 1
        assert depth == 0

    def test_count_commands_with_subcommands(self):
        """Test count_commands with nested commands."""
        root = CommandInfo(
            name="vibey",
            path="vibey",
            is_group=True,
            subcommands=[
                CommandInfo(name="status", path="vibey status"),
                CommandInfo(
                    name="roadmap",
                    path="vibey roadmap",
                    is_group=True,
                    subcommands=[
                        CommandInfo(name="list", path="vibey roadmap list"),
                        CommandInfo(name="show", path="vibey roadmap show"),
                    ],
                ),
            ],
        )
        total, depth = root.count_commands()
        assert total == 5  # vibey + status + roadmap + list + show
        assert depth == 2  # vibey -> roadmap -> list/show

    def test_to_dict(self):
        """Test to_dict serialization."""
        cmd = CommandInfo(
            name="status",
            path="vibey status",
            help="Show status",
            short_help="Status",
        )
        result = cmd.to_dict()

        assert result["name"] == "status"
        assert result["path"] == "vibey status"
        assert result["help"] == "Show status"
        assert result["subcommands"] == []


class TestCLIStructure:
    """Test CLIStructure dataclass."""

    def test_construction(self):
        """Test CLIStructure construction."""
        root = CommandInfo(name="vibey", path="vibey")
        structure = CLIStructure(
            root=root,
            version="1.0.0",
            total_commands=10,
            max_depth=3,
            generated_at="2024-01-01T00:00:00+00:00",
        )
        assert structure.version == "1.0.0"
        assert structure.total_commands == 10
        assert structure.max_depth == 3

    def test_to_dict(self):
        """Test to_dict serialization."""
        root = CommandInfo(name="vibey", path="vibey")
        structure = CLIStructure(
            root=root,
            version="2.0.0",
            total_commands=5,
            max_depth=2,
            generated_at="2024-06-15T12:00:00+00:00",
        )
        result = structure.to_dict()

        assert result["version"] == "2.0.0"
        assert result["total_commands"] == 5
        assert result["max_depth"] == 2
        assert "root" in result

    def test_to_json(self):
        """Test to_json serialization."""
        root = CommandInfo(name="vibey", path="vibey")
        structure = CLIStructure(
            root=root,
            version="1.0.0",
            total_commands=1,
            max_depth=0,
            generated_at="2024-01-01T00:00:00Z",
        )
        json_str = structure.to_json()

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["version"] == "1.0.0"

    def test_to_yaml(self):
        """Test to_yaml serialization."""
        root = CommandInfo(name="vibey", path="vibey")
        structure = CLIStructure(
            root=root,
            version="1.0.0",
            total_commands=1,
            max_depth=0,
            generated_at="2024-01-01T00:00:00Z",
        )
        try:
            yaml_str = structure.to_yaml()
            assert "version: 1.0.0" in yaml_str
        except ImportError:
            pytest.skip("PyYAML not installed")


class TestCLIIntrospector:
    """Test CLIIntrospector class."""

    def test_init(self):
        """Test introspector initialization."""
        mock_cmd = MagicMock(spec=click.Command)
        introspector = CLIIntrospector(mock_cmd, version="1.0.0")
        assert introspector.root == mock_cmd
        assert introspector.version == "1.0.0"

    def test_introspect_simple_command(self):
        """Test introspection of a simple command."""
        @click.command()
        @click.option("--verbose", is_flag=True, help="Verbose output")
        def test_cmd(verbose):
            """A test command."""
            pass

        introspector = CLIIntrospector(test_cmd, version="1.0.0")
        structure = introspector.introspect()

        assert structure.total_commands == 1
        assert structure.root.name == "vibey"
        assert "verbose" in [p.name for p in structure.root.params]

    def test_introspect_group_with_subcommands(self):
        """Test introspection of command group."""
        @click.group()
        def cli():
            """Root CLI."""
            pass

        @cli.command()
        def status():
            """Show status."""
            pass

        @cli.command()
        def version():
            """Show version."""
            pass

        introspector = CLIIntrospector(cli, version="2.0.0")
        structure = introspector.introspect()

        assert structure.total_commands == 3  # cli + status + version
        assert structure.root.is_group is True
        assert len(structure.root.subcommands) == 2

    def test_extract_params_option(self):
        """Test parameter extraction for options."""
        @click.command()
        @click.option("--format", "-f", type=click.Choice(["json", "yaml"]),
                      default="json", help="Output format")
        def cmd(format):
            pass

        introspector = CLIIntrospector(cmd)
        params = introspector._extract_params(cmd)

        assert len(params) == 1
        assert params[0].name == "format"
        assert params[0].kind == ParamKind.OPTION
        assert "Choice" in params[0].type_str

    def test_extract_params_argument(self):
        """Test parameter extraction for arguments."""
        @click.command()
        @click.argument("task_id")
        def cmd(task_id):
            pass

        introspector = CLIIntrospector(cmd)
        params = introspector._extract_params(cmd)

        assert len(params) == 1
        assert params[0].name == "task_id"
        assert params[0].kind == ParamKind.ARGUMENT

    def test_get_type_string_choice(self):
        """Test type string extraction for Choice type."""
        introspector = CLIIntrospector(MagicMock())
        choice_type = click.Choice(["a", "b", "c"])
        result = introspector._get_type_string(choice_type)
        assert "Choice" in result
        assert "a" in result

    def test_get_type_string_path(self):
        """Test type string extraction for Path type."""
        introspector = CLIIntrospector(MagicMock())
        path_type = click.Path(exists=True)
        result = introspector._get_type_string(path_type)
        assert "Path" in result

    def test_normalize_default_none(self):
        """Test normalize_default with None."""
        introspector = CLIIntrospector(MagicMock())
        assert introspector._normalize_default(None) is None

    def test_normalize_default_empty_tuple(self):
        """Test normalize_default with empty tuple."""
        introspector = CLIIntrospector(MagicMock())
        assert introspector._normalize_default(()) is None

    def test_normalize_default_callable(self):
        """Test normalize_default with callable."""
        introspector = CLIIntrospector(MagicMock())
        result = introspector._normalize_default(lambda: "dynamic")
        assert result == "<dynamic>"

    def test_normalize_default_value(self):
        """Test normalize_default with regular value."""
        introspector = CLIIntrospector(MagicMock())
        assert introspector._normalize_default("test") == "test"
        assert introspector._normalize_default(123) == 123
        assert introspector._normalize_default(True) is True

    def test_parse_examples_from_text_basic(self):
        """Test parsing examples from help text."""
        introspector = CLIIntrospector(MagicMock())
        text = """
        Some description.

        Examples:
            # Show status
            vibey roadmap status

            vibey roadmap list tasks
        """
        examples = introspector._parse_examples_from_text(text)

        assert len(examples) >= 1
        assert any("vibey roadmap status" in e.command for e in examples)

    def test_parse_examples_from_text_empty(self):
        """Test parsing examples from empty text."""
        introspector = CLIIntrospector(MagicMock())
        assert introspector._parse_examples_from_text("") == []
        assert introspector._parse_examples_from_text(None) == []


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_introspect_cli_returns_structure(self):
        """Test introspect_cli returns CLIStructure."""
        try:
            structure = introspect_cli()
            assert isinstance(structure, CLIStructure)
            assert structure.total_commands > 0
            assert structure.root.name == "vibey"
        except ImportError:
            pytest.skip("vibey.cli.main not available")

    def test_get_command_by_path_root(self):
        """Test get_command_by_path for root."""
        root = CommandInfo(name="vibey", path="vibey")
        structure = CLIStructure(
            root=root,
            version="1.0.0",
            total_commands=1,
            max_depth=0,
            generated_at="2024-01-01",
        )
        result = get_command_by_path(structure, "vibey")
        assert result == root

    def test_get_command_by_path_subcommand(self):
        """Test get_command_by_path for subcommand."""
        status = CommandInfo(name="status", path="vibey status")
        root = CommandInfo(
            name="vibey",
            path="vibey",
            subcommands=[status],
        )
        structure = CLIStructure(
            root=root,
            version="1.0.0",
            total_commands=2,
            max_depth=1,
            generated_at="2024-01-01",
        )
        result = get_command_by_path(structure, "vibey status")
        assert result == status

    def test_get_command_by_path_nested(self):
        """Test get_command_by_path for nested command."""
        list_cmd = CommandInfo(name="list", path="vibey roadmap list")
        roadmap = CommandInfo(
            name="roadmap",
            path="vibey roadmap",
            subcommands=[list_cmd],
        )
        root = CommandInfo(
            name="vibey",
            path="vibey",
            subcommands=[roadmap],
        )
        structure = CLIStructure(
            root=root,
            version="1.0.0",
            total_commands=3,
            max_depth=2,
            generated_at="2024-01-01",
        )
        result = get_command_by_path(structure, "vibey roadmap list")
        assert result == list_cmd

    def test_get_command_by_path_not_found(self):
        """Test get_command_by_path for nonexistent command."""
        root = CommandInfo(name="vibey", path="vibey")
        structure = CLIStructure(
            root=root,
            version="1.0.0",
            total_commands=1,
            max_depth=0,
            generated_at="2024-01-01",
        )
        result = get_command_by_path(structure, "vibey nonexistent")
        assert result is None

    def test_list_all_commands(self):
        """Test list_all_commands function."""
        roadmap = CommandInfo(
            name="roadmap",
            path="vibey roadmap",
            subcommands=[
                CommandInfo(name="status", path="vibey roadmap status"),
                CommandInfo(name="list", path="vibey roadmap list"),
            ],
        )
        root = CommandInfo(
            name="vibey",
            path="vibey",
            subcommands=[
                roadmap,
                CommandInfo(name="version", path="vibey version"),
            ],
        )
        structure = CLIStructure(
            root=root,
            version="1.0.0",
            total_commands=5,
            max_depth=2,
            generated_at="2024-01-01",
        )
        commands = list_all_commands(structure)

        assert "vibey" in commands
        assert "vibey roadmap" in commands
        assert "vibey roadmap status" in commands
        assert "vibey roadmap list" in commands
        assert "vibey version" in commands
        assert commands == sorted(commands)  # Should be sorted


class TestIntegration:
    """Integration tests with real CLI."""

    def test_introspect_real_cli(self):
        """Test introspecting the actual Vibey CLI."""
        try:
            structure = introspect_cli()

            # Basic structure assertions
            assert structure.total_commands > 50  # Vibey has many commands
            assert structure.max_depth >= 2  # At least vibey -> roadmap -> status

            # Root command
            assert structure.root.name == "vibey"
            assert structure.root.is_group is True

            # Check some expected subcommands exist
            subcommand_names = [s.name for s in structure.root.subcommands]
            assert "roadmap" in subcommand_names or len(subcommand_names) > 0

        except ImportError:
            pytest.skip("vibey.cli.main not available")

    def test_list_real_commands(self):
        """Test listing real CLI commands."""
        try:
            structure = introspect_cli()
            commands = list_all_commands(structure)

            assert len(commands) > 50
            assert all(cmd.startswith("vibey") for cmd in commands)

        except ImportError:
            pytest.skip("vibey.cli.main not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
