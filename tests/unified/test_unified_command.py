"""
Tests for the unified command system.

Tests cover:
- @unified_command and @param decorators
- CommandSpec and ParamSpec dataclasses
- CommandRegistry singleton
- Type mapping (Click and JSON Schema)
- Click adapter (command generation)
- MCP adapter (tool generation)
- Parity checker
"""

import pytest
from pathlib import Path
from typing import Any

from vibey.unified import (
    unified_command,
    param,
    ParamType,
    Interface,
    CommandSpec,
    ParamSpec,
    CommandRegistry,
    COMMAND_REGISTRY,
    CommandResult,
    param_to_click_type,
    param_to_json_schema,
    check_parity,
    ParityReport,
)
from vibey.unified.adapters import (
    generate_click_command,
    generate_mcp_tool_definition,
    get_unified_mcp_tools,
)


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear the command registry before and after each test."""
    COMMAND_REGISTRY.clear()
    yield
    COMMAND_REGISTRY.clear()


class TestParamType:
    """Tests for ParamType enum."""

    def test_all_types_defined(self):
        """Verify all expected types exist."""
        assert ParamType.STRING.value == "string"
        assert ParamType.INTEGER.value == "integer"
        assert ParamType.FLOAT.value == "float"
        assert ParamType.BOOLEAN.value == "boolean"
        assert ParamType.PATH.value == "path"
        assert ParamType.CHOICE.value == "choice"
        assert ParamType.LIST.value == "list"


class TestParamSpec:
    """Tests for ParamSpec dataclass."""

    def test_basic_construction(self):
        """Test basic ParamSpec construction."""
        spec = ParamSpec(name="test_param")
        assert spec.name == "test_param"
        assert spec.type == ParamType.STRING
        assert spec.required is True
        assert spec.default is None

    def test_full_construction(self):
        """Test ParamSpec with all options."""
        spec = ParamSpec(
            name="task_id",
            type=ParamType.STRING,
            required=True,
            default=None,
            help="Task ID to start",
            choices=None,
            item_type=None,
            cli_option=False,
            cli_short=None,
            cli_is_flag=False,
            cli_prompt=None,
            mcp_description="Override description",
        )
        assert spec.name == "task_id"
        assert spec.cli_option is False
        assert spec.mcp_description == "Override description"

    def test_choice_type(self):
        """Test ParamSpec with CHOICE type."""
        spec = ParamSpec(
            name="status",
            type=ParamType.CHOICE,
            choices=["pending", "in_progress", "completed"],
        )
        assert spec.choices == ["pending", "in_progress", "completed"]


class TestParamDecorator:
    """Tests for @param decorator."""

    def test_single_param(self):
        """Test single @param decorator."""
        @param("name", type=ParamType.STRING, help="User name")
        def greet(name: str):
            pass

        assert hasattr(greet, "_unified_params")
        assert len(greet._unified_params) == 1
        assert greet._unified_params[0].name == "name"

    def test_multiple_params(self):
        """Test multiple stacked @param decorators."""
        @param("name", type=ParamType.STRING)
        @param("age", type=ParamType.INTEGER)
        @param("active", type=ParamType.BOOLEAN, default=True)
        def profile(name: str, age: int, active: bool):
            pass

        assert len(profile._unified_params) == 3
        # Params should be in order (first decorator = first param)
        assert profile._unified_params[0].name == "name"
        assert profile._unified_params[1].name == "age"
        assert profile._unified_params[2].name == "active"


class TestCommandSpec:
    """Tests for CommandSpec dataclass."""

    def test_basic_construction(self):
        """Test basic CommandSpec construction."""
        def dummy_op():
            pass

        spec = CommandSpec(
            name="test_cmd",
            description="Test command",
            operation=dummy_op,
        )
        assert spec.name == "test_cmd"
        assert spec.description == "Test command"
        assert spec.cli_command_name == "test-cmd"
        assert spec.mcp_tool_name == "vibey_test_cmd"

    def test_interface_defaults(self):
        """Test default interfaces (both CLI and MCP)."""
        def dummy_op():
            pass

        spec = CommandSpec(
            name="test",
            description="Test",
            operation=dummy_op,
        )
        assert Interface.CLI in spec.interfaces
        assert Interface.MCP in spec.interfaces
        assert spec.is_available_in(Interface.CLI)
        assert spec.is_available_in(Interface.MCP)

    def test_cli_only(self):
        """Test CLI-only command."""
        def dummy_op():
            pass

        spec = CommandSpec(
            name="wizard",
            description="Interactive wizard",
            operation=dummy_op,
            interfaces=[Interface.CLI],
        )
        assert spec.is_available_in(Interface.CLI)
        assert not spec.is_available_in(Interface.MCP)

    def test_mcp_only(self):
        """Test MCP-only command."""
        def dummy_op():
            pass

        spec = CommandSpec(
            name="agent_ctx",
            description="Agent context",
            operation=dummy_op,
            interfaces=[Interface.MCP],
        )
        assert not spec.is_available_in(Interface.CLI)
        assert spec.is_available_in(Interface.MCP)

    def test_custom_names(self):
        """Test custom CLI and MCP names."""
        def dummy_op():
            pass

        spec = CommandSpec(
            name="start_task",
            description="Start a task",
            operation=dummy_op,
            cli_name="begin",
            mcp_name="custom_tool_name",
        )
        assert spec.cli_command_name == "begin"
        assert spec.mcp_tool_name == "custom_tool_name"


class TestUnifiedCommandDecorator:
    """Tests for @unified_command decorator."""

    def test_basic_registration(self):
        """Test basic command registration."""
        @unified_command(
            name="test_cmd",
            description="A test command",
        )
        def test_cmd(root_dir=None):
            return CommandResult.ok(message="Test OK")

        assert COMMAND_REGISTRY.count() == 1
        spec = COMMAND_REGISTRY.get("test_cmd")
        assert spec is not None
        assert spec.description == "A test command"

    def test_with_params(self):
        """Test command with parameters."""
        @unified_command(
            name="greet",
            description="Greet someone",
        )
        @param("name", type=ParamType.STRING, required=True, help="Name to greet")
        @param("loud", type=ParamType.BOOLEAN, default=False, cli_is_flag=True)
        def greet(name: str, loud: bool = False, root_dir=None):
            msg = f"Hello, {name}!"
            return CommandResult.ok(message=msg.upper() if loud else msg)

        spec = COMMAND_REGISTRY.get("greet")
        assert len(spec.params) == 2
        assert spec.params[0].name == "name"
        assert spec.params[1].name == "loud"

    def test_interface_selection(self):
        """Test interface selection parameter."""
        @unified_command(
            name="cli_only",
            description="CLI only command",
            interfaces=["cli"],
            exclusion_reason="Interactive feature",
        )
        def cli_only(root_dir=None):
            return CommandResult.ok()

        @unified_command(
            name="mcp_only",
            description="MCP only command",
            interfaces=["mcp"],
            exclusion_reason="Agent-specific",
        )
        def mcp_only(root_dir=None):
            return CommandResult.ok()

        assert COMMAND_REGISTRY.count() == 2
        assert COMMAND_REGISTRY.count_for_interface(Interface.CLI) == 1
        assert COMMAND_REGISTRY.count_for_interface(Interface.MCP) == 1

    def test_cli_group(self):
        """Test CLI group parameter."""
        @unified_command(
            name="status",
            description="Show status",
            cli_group="roadmap",
        )
        def status(root_dir=None):
            return CommandResult.ok()

        spec = COMMAND_REGISTRY.get("status")
        assert spec.cli_group == "roadmap"
        groups = COMMAND_REGISTRY.list_by_group("roadmap")
        assert len(groups) == 1

    def test_duplicate_registration_fails(self):
        """Test that duplicate command names raise error."""
        @unified_command(name="duplicate", description="First")
        def first(root_dir=None):
            return CommandResult.ok()

        with pytest.raises(ValueError, match="already registered"):
            @unified_command(name="duplicate", description="Second")
            def second(root_dir=None):
                return CommandResult.ok()


class TestCommandRegistry:
    """Tests for CommandRegistry."""

    def test_list_all(self):
        """Test listing all commands."""
        @unified_command(name="cmd1", description="First")
        def cmd1(root_dir=None):
            pass

        @unified_command(name="cmd2", description="Second")
        def cmd2(root_dir=None):
            pass

        all_cmds = COMMAND_REGISTRY.list_all()
        assert len(all_cmds) == 2

    def test_list_for_interface(self):
        """Test filtering by interface."""
        @unified_command(name="both", description="Both interfaces")
        def both(root_dir=None):
            pass

        @unified_command(name="cli", description="CLI only", interfaces=["cli"])
        def cli(root_dir=None):
            pass

        cli_cmds = COMMAND_REGISTRY.list_for_interface(Interface.CLI)
        mcp_cmds = COMMAND_REGISTRY.list_for_interface(Interface.MCP)

        assert len(cli_cmds) == 2  # both + cli
        assert len(mcp_cmds) == 1  # both only

    def test_list_groups(self):
        """Test listing unique groups."""
        @unified_command(name="c1", description="G1", cli_group="group1")
        def c1(root_dir=None):
            pass

        @unified_command(name="c2", description="G1", cli_group="group1")
        def c2(root_dir=None):
            pass

        @unified_command(name="c3", description="G2", cli_group="group2")
        def c3(root_dir=None):
            pass

        groups = COMMAND_REGISTRY.list_groups()
        assert sorted(groups) == ["group1", "group2"]

    def test_clear(self):
        """Test clearing registry."""
        @unified_command(name="test", description="Test")
        def test(root_dir=None):
            pass

        assert COMMAND_REGISTRY.count() == 1
        COMMAND_REGISTRY.clear()
        assert COMMAND_REGISTRY.count() == 0


class TestTypeMapping:
    """Tests for type mapping functions."""

    def test_param_to_click_type_string(self):
        """Test string type mapping to Click."""
        import click
        spec = ParamSpec(name="test", type=ParamType.STRING)
        click_type = param_to_click_type(spec)
        assert click_type == click.STRING

    def test_param_to_click_type_integer(self):
        """Test integer type mapping to Click."""
        import click
        spec = ParamSpec(name="test", type=ParamType.INTEGER)
        click_type = param_to_click_type(spec)
        assert click_type == click.INT

    def test_param_to_click_type_choice(self):
        """Test choice type mapping to Click."""
        import click
        spec = ParamSpec(
            name="status",
            type=ParamType.CHOICE,
            choices=["a", "b", "c"],
        )
        click_type = param_to_click_type(spec)
        assert isinstance(click_type, click.Choice)

    def test_param_to_json_schema_string(self):
        """Test string type mapping to JSON Schema."""
        spec = ParamSpec(name="test", type=ParamType.STRING, help="Test param")
        schema = param_to_json_schema(spec)
        assert schema["type"] == "string"
        assert schema["description"] == "Test param"

    def test_param_to_json_schema_choice(self):
        """Test choice type mapping to JSON Schema."""
        spec = ParamSpec(
            name="status",
            type=ParamType.CHOICE,
            choices=["a", "b", "c"],
        )
        schema = param_to_json_schema(spec)
        assert schema["type"] == "string"
        assert schema["enum"] == ["a", "b", "c"]

    def test_param_to_json_schema_with_default(self):
        """Test default value in JSON Schema."""
        spec = ParamSpec(name="test", type=ParamType.INTEGER, default=42)
        schema = param_to_json_schema(spec)
        assert schema["default"] == 42


class TestClickAdapter:
    """Tests for Click adapter."""

    def test_generate_click_command(self):
        """Test generating Click command from spec."""
        @unified_command(
            name="test_click",
            description="Test Click generation",
        )
        @param("name", type=ParamType.STRING, required=True, help="Name")
        def test_click(name: str, root_dir=None):
            return CommandResult.ok(message=f"Hello {name}")

        spec = COMMAND_REGISTRY.get("test_click")
        click_cmd = generate_click_command(spec)

        assert click_cmd.name == "test-click"
        assert "Test Click generation" in click_cmd.help

    def test_click_command_with_flag(self):
        """Test Click command with boolean flag."""
        @unified_command(name="test_flag", description="Test flags")
        @param("verbose", type=ParamType.BOOLEAN, default=False, cli_is_flag=True)
        def test_flag(verbose: bool = False, root_dir=None):
            return CommandResult.ok()

        spec = COMMAND_REGISTRY.get("test_flag")
        click_cmd = generate_click_command(spec)

        # Verify option was added
        assert len(click_cmd.params) > 0


class TestMCPAdapter:
    """Tests for MCP adapter."""

    def test_generate_mcp_tool_definition(self):
        """Test generating MCP tool definition from spec."""
        @unified_command(
            name="test_mcp",
            description="Test MCP generation",
            mcp_category="testing",
        )
        @param("task_id", type=ParamType.STRING, required=True, help="Task ID")
        def test_mcp(task_id: str, root_dir=None):
            return CommandResult.ok()

        spec = COMMAND_REGISTRY.get("test_mcp")
        tool_def = generate_mcp_tool_definition(spec)

        assert tool_def["name"] == "vibey_test_mcp"
        assert tool_def["description"] == "Test MCP generation"
        assert "task_id" in tool_def["inputSchema"]["properties"]
        assert "task_id" in tool_def["inputSchema"]["required"]

    def test_get_unified_mcp_tools(self):
        """Test getting all MCP tools."""
        @unified_command(name="tool1", description="Tool 1")
        def tool1(root_dir=None):
            pass

        @unified_command(name="tool2", description="Tool 2")
        def tool2(root_dir=None):
            pass

        @unified_command(name="cli_only", description="CLI", interfaces=["cli"])
        def cli_only(root_dir=None):
            pass

        tools = get_unified_mcp_tools()
        assert len(tools) == 2  # tool1 and tool2, not cli_only


class TestParityChecker:
    """Tests for parity checker."""

    def test_empty_registry_passes(self):
        """Test parity check on empty registry."""
        report = check_parity()
        assert report.is_passing
        assert report.total_commands == 0

    def test_all_both_interfaces(self):
        """Test parity when all commands have both interfaces."""
        @unified_command(name="cmd1", description="Command 1")
        def cmd1(root_dir=None):
            pass

        @unified_command(name="cmd2", description="Command 2")
        def cmd2(root_dir=None):
            pass

        report = check_parity()
        assert report.is_passing
        assert len(report.both_interfaces_commands) == 2
        assert len(report.cli_only_commands) == 0
        assert len(report.mcp_only_commands) == 0

    def test_documented_exclusions(self):
        """Test that documented exclusions don't create violations."""
        @unified_command(
            name="cli_only",
            description="CLI only",
            interfaces=["cli"],
            exclusion_reason="Interactive prompts",
        )
        def cli_only(root_dir=None):
            pass

        report = check_parity()
        assert report.is_passing  # No errors
        assert len(report.cli_only_commands) == 1
        assert "cli_only" in report.excluded_commands

    def test_undocumented_exclusion_warning(self):
        """Test that undocumented exclusions create warnings."""
        @unified_command(
            name="hidden",
            description="Hidden",
            interfaces=["cli"],
            # No exclusion_reason!
        )
        def hidden(root_dir=None):
            pass

        report = check_parity()
        # Warnings don't cause failure
        assert report.is_passing
        # But there should be a warning
        assert report.warning_count == 1
        assert report.violations[0].severity == "warning"

    def test_report_format(self):
        """Test report formatting."""
        @unified_command(name="both", description="Both")
        def both(root_dir=None):
            pass

        @unified_command(
            name="cli_only",
            description="CLI",
            interfaces=["cli"],
            exclusion_reason="Test reason",
        )
        def cli_only(root_dir=None):
            pass

        report = check_parity()
        text = report.format_report(verbose=True)

        assert "CLI/MCP Parity Report" in text
        assert "Total unified commands: 2" in text
        assert "Both interfaces: 1" in text
        assert "CLI only: 1" in text


class TestCommandResult:
    """Tests for CommandResult."""

    def test_ok_result(self):
        """Test creating successful result."""
        result = CommandResult.ok(data={"key": "value"}, message="Success")
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.message == "Success"

    def test_fail_result(self):
        """Test creating failed result."""
        result = CommandResult.fail(error="Something went wrong")
        assert result.success is False
        assert result.error == "Something went wrong"

    def test_default_formatter_success(self):
        """Test default formatter for success."""
        from vibey.unified.formatters import DEFAULT_FORMATTER

        result = CommandResult.ok(message="All good")
        output = DEFAULT_FORMATTER.format_cli(result)
        assert output == "All good"

    def test_default_formatter_error(self):
        """Test default formatter for error."""
        from vibey.unified.formatters import DEFAULT_FORMATTER

        result = CommandResult.fail(error="Failed")
        output = DEFAULT_FORMATTER.format_cli(result)
        assert "Error: Failed" in output
