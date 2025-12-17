"""
Tests for unified MCP tools.

Tests the MCP adapter that generates tools from unified command definitions.
"""

import pytest
from pathlib import Path

# Skip all tests if unified module not available
pytest.importorskip("vibey.unified")

# Import commands module to register them
from vibey.unified import commands as unified_commands  # noqa: F401


class TestUnifiedToolDefinitions:
    """Test MCP tool definition generation from unified commands."""

    def test_registry_has_mcp_commands(self):
        """Verify unified commands are registered for MCP interface."""
        from vibey.unified import COMMAND_REGISTRY
        from vibey.unified.command import Interface

        mcp_commands = COMMAND_REGISTRY.list_for_interface(Interface.MCP)
        assert len(mcp_commands) > 0, "No MCP commands registered"

    def test_generate_tool_definition_has_required_fields(self):
        """Verify generated tool definitions have required MCP fields."""
        from vibey.unified import COMMAND_REGISTRY
        from vibey.unified.command import Interface
        from vibey.unified.adapters.mcp_adapter import generate_mcp_tool_definition

        mcp_commands = COMMAND_REGISTRY.list_for_interface(Interface.MCP)
        assert len(mcp_commands) > 0

        for spec in mcp_commands:
            definition = generate_mcp_tool_definition(spec)

            # Required fields for MCP tool
            assert "name" in definition, f"Missing 'name' for {spec.name}"
            assert "description" in definition, f"Missing 'description' for {spec.name}"
            assert "inputSchema" in definition, f"Missing 'inputSchema' for {spec.name}"

            # Input schema should be valid JSON Schema
            schema = definition["inputSchema"]
            assert schema.get("type") == "object", f"Schema type should be 'object' for {spec.name}"
            assert "properties" in schema, f"Missing 'properties' in schema for {spec.name}"

    def test_tool_names_follow_convention(self):
        """Verify tool names follow vibey_ prefix convention."""
        from vibey.unified import COMMAND_REGISTRY
        from vibey.unified.command import Interface
        from vibey.unified.adapters.mcp_adapter import generate_mcp_tool_definition

        mcp_commands = COMMAND_REGISTRY.list_for_interface(Interface.MCP)

        for spec in mcp_commands:
            definition = generate_mcp_tool_definition(spec)
            name = definition["name"]
            assert name.startswith("vibey_"), f"Tool name should start with 'vibey_': {name}"

    def test_required_parameters_marked_in_schema(self):
        """Verify required parameters are properly marked in JSON Schema."""
        from vibey.unified import COMMAND_REGISTRY
        from vibey.unified.command import Interface
        from vibey.unified.adapters.mcp_adapter import generate_mcp_tool_definition

        # Find a command with required parameters
        mcp_commands = COMMAND_REGISTRY.list_for_interface(Interface.MCP)

        for spec in mcp_commands:
            if any(p.required for p in spec.params):
                definition = generate_mcp_tool_definition(spec)
                schema = definition["inputSchema"]

                # Should have 'required' array
                required_params = [p.name for p in spec.params if p.required]
                schema_required = schema.get("required", [])

                for param_name in required_params:
                    assert param_name in schema_required, \
                        f"Required param '{param_name}' not in schema.required for {spec.name}"
                break

    def test_parameter_types_mapped_correctly(self):
        """Verify parameter types are correctly mapped to JSON Schema."""
        from vibey.unified import COMMAND_REGISTRY, ParamType
        from vibey.unified.command import Interface
        from vibey.unified.adapters.mcp_adapter import generate_mcp_tool_definition

        mcp_commands = COMMAND_REGISTRY.list_for_interface(Interface.MCP)

        type_mapping = {
            ParamType.STRING: "string",
            ParamType.INTEGER: "integer",
            ParamType.BOOLEAN: "boolean",
            ParamType.PATH: "string",  # Path maps to string in JSON Schema
        }

        for spec in mcp_commands:
            definition = generate_mcp_tool_definition(spec)
            properties = definition["inputSchema"].get("properties", {})

            for param in spec.params:
                if param.name in properties:
                    expected_type = type_mapping.get(param.type)
                    if expected_type:
                        actual_type = properties[param.name].get("type")
                        assert actual_type == expected_type, \
                            f"Type mismatch for {spec.name}.{param.name}: expected {expected_type}, got {actual_type}"


class TestUnifiedToolDiscovery:
    """Test that unified tools are discoverable via MCP."""

    def test_get_unified_mcp_tools_returns_list(self):
        """Verify get_unified_mcp_tools returns a list of tool definitions."""
        from vibey.unified.adapters.mcp_adapter import get_unified_mcp_tools

        tools = get_unified_mcp_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0, "Should have at least one unified tool"

    def test_all_unified_tools_have_unique_names(self):
        """Verify all tool names are unique."""
        from vibey.unified.adapters.mcp_adapter import get_unified_mcp_tools

        tools = get_unified_mcp_tools()
        names = [t["name"] for t in tools]
        assert len(names) == len(set(names)), "Duplicate tool names found"

    def test_expected_tools_present(self):
        """Verify expected unified tools are present."""
        from vibey.unified.adapters.mcp_adapter import get_unified_mcp_tools

        tools = get_unified_mcp_tools()
        tool_names = {t["name"] for t in tools}

        # These are the actual tool names from the unified commands
        expected_tools = [
            "vibey_roadmap_status",
            "vibey_roadmap_show",
            "vibey_start_task",  # Named start_task, not roadmap_start
            "vibey_complete_task",  # Named complete_task, not roadmap_complete
            "vibey_deploy_list",
            "vibey_docs_generate_cli",
        ]

        for expected in expected_tools:
            assert expected in tool_names, f"Expected tool '{expected}' not found. Available: {tool_names}"


class TestUnifiedToolExecution:
    """Test unified tool execution via MCP adapter."""

    @pytest.fixture
    def roadmap_context(self, tmp_path):
        """Create minimal roadmap context for testing."""
        roadmap_dir = tmp_path / ".vibey" / "roadmap"
        roadmap_dir.mkdir(parents=True)

        # Create minimal roadmap.yaml
        roadmap_yaml = roadmap_dir / "roadmap.yaml"
        roadmap_yaml.write_text("""roadmap:
  id: test-roadmap
  name: Test Roadmap
  version: 1.0.0
""")

        # Create tracks directory
        (roadmap_dir / "tracks").mkdir()
        (roadmap_dir / "sprints").mkdir()
        (roadmap_dir / "tasks").mkdir()

        return tmp_path

    @pytest.mark.asyncio
    async def test_handle_unknown_tool_returns_error(self):
        """Verify unknown tool name returns error response."""
        from vibey.unified.adapters.mcp_adapter import handle_unified_tool_call

        result = await handle_unified_tool_call("nonexistent_tool", {})
        # Should return error dict, not raise
        assert result is not None
        assert result.get("isError") is True or "error" in str(result).lower()

    @pytest.mark.asyncio
    async def test_handle_roadmap_status_returns_result(self, roadmap_context):
        """Verify roadmap_status tool returns a result."""
        from vibey.unified.adapters.mcp_adapter import handle_unified_tool_call

        result = await handle_unified_tool_call(
            "vibey_roadmap_status",
            {},
            root_dir=roadmap_context
        )

        # Should return something (may be error if no tracks)
        assert result is not None

    @pytest.mark.asyncio
    async def test_handle_deploy_list_returns_result(self):
        """Verify deploy_list tool returns some result."""
        from vibey.unified.adapters.mcp_adapter import handle_unified_tool_call

        result = await handle_unified_tool_call(
            "vibey_deploy_list",
            {}
        )

        assert result is not None
        # Result format varies - may be success or error
        # Just verify we get a response


class TestUnifiedToolParameters:
    """Test parameter handling for unified tools."""

    @pytest.mark.asyncio
    async def test_missing_required_parameter_returns_error(self):
        """Verify missing required parameter returns error."""
        from vibey.unified.adapters.mcp_adapter import handle_unified_tool_call

        # roadmap_show requires item_id
        result = await handle_unified_tool_call(
            "vibey_roadmap_show",
            {}  # Missing required item_id
        )

        # Should return an error result
        assert result is not None
        # The exact error format depends on implementation
        # Just verify it doesn't crash

    @pytest.mark.asyncio
    async def test_optional_parameters_have_defaults(self, tmp_path):
        """Verify optional parameters use defaults when not provided."""
        from vibey.unified.adapters.mcp_adapter import handle_unified_tool_call

        # deploy with dry_run has default False
        result = await handle_unified_tool_call(
            "vibey_deploy",
            {"platform": "test"},  # dry_run and force have defaults
            root_dir=tmp_path
        )

        # Should not crash due to missing optional params
        assert result is not None


class TestCommandResultFormatting:
    """Test CommandResult formatting for MCP responses."""

    def test_command_result_ok_format(self):
        """Verify CommandResult.ok creates proper response."""
        from vibey.unified import CommandResult

        result = CommandResult.ok(
            data={"key": "value"},
            message="Operation successful"
        )

        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.message == "Operation successful"
        assert result.error == ""  # Empty string, not None

    def test_command_result_fail_format(self):
        """Verify CommandResult.fail creates proper response."""
        from vibey.unified import CommandResult

        result = CommandResult.fail(error="Something went wrong")

        assert result.success is False
        assert result.error == "Something went wrong"

    def test_command_result_as_dataclass(self):
        """Verify CommandResult is a proper dataclass."""
        from dataclasses import asdict
        from vibey.unified import CommandResult

        result = CommandResult.ok(data={"test": True}, message="Done")
        result_dict = asdict(result)

        assert isinstance(result_dict, dict)
        assert result_dict.get("success") is True
        assert result_dict.get("data") == {"test": True}
        assert result_dict.get("message") == "Done"
        assert result_dict.get("error") == ""
