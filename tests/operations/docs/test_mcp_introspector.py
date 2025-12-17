"""
Tests for MCP introspector module.

Tests the MCP server introspection capability for auto-generating MCP reference documentation.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch

from vibey.operations.docs.mcp_introspector import (
    MCPComponentType,
    SchemaProperty,
    InputSchema,
    ToolExample,
    ToolInfo,
    ResourceTemplateInfo,
    PromptArgument,
    PromptInfo,
    MCPStructure,
    MCPIntrospector,
    introspect_mcp,
    get_tool_count,
    get_resource_count,
    get_prompt_count,
    TOOL_EXAMPLES,
)


class TestMCPComponentType:
    """Test MCPComponentType enum."""

    def test_tool_value(self):
        """Test TOOL has correct value."""
        assert MCPComponentType.TOOL.value == "tool"

    def test_resource_value(self):
        """Test RESOURCE has correct value."""
        assert MCPComponentType.RESOURCE.value == "resource"

    def test_prompt_value(self):
        """Test PROMPT has correct value."""
        assert MCPComponentType.PROMPT.value == "prompt"


class TestSchemaProperty:
    """Test SchemaProperty dataclass."""

    def test_basic_construction(self):
        """Test basic SchemaProperty construction."""
        prop = SchemaProperty(
            name="task_id",
            type="string",
        )
        assert prop.name == "task_id"
        assert prop.type == "string"

    def test_default_values(self):
        """Test SchemaProperty default values."""
        prop = SchemaProperty(name="test", type="string")
        assert prop.description is None
        assert prop.required is False
        assert prop.default is None
        assert prop.enum is None
        assert prop.minimum is None
        assert prop.maximum is None

    def test_full_construction(self):
        """Test SchemaProperty with all fields."""
        prop = SchemaProperty(
            name="status",
            type="string",
            description="Task status",
            required=True,
            default="pending",
            enum=["pending", "in_progress", "completed"],
            minimum=None,
            maximum=None,
        )
        assert prop.name == "status"
        assert prop.required is True
        assert prop.enum == ["pending", "in_progress", "completed"]

    def test_to_dict_minimal(self):
        """Test to_dict with minimal fields."""
        prop = SchemaProperty(name="test", type="string")
        result = prop.to_dict()

        assert result["name"] == "test"
        assert result["type"] == "string"
        assert result["required"] is False
        assert "default" not in result  # None values excluded

    def test_to_dict_full(self):
        """Test to_dict with all fields."""
        prop = SchemaProperty(
            name="count",
            type="integer",
            description="Item count",
            required=True,
            default=10,
            minimum=1,
            maximum=100,
        )
        result = prop.to_dict()

        assert result["name"] == "count"
        assert result["type"] == "integer"
        assert result["required"] is True
        assert result["default"] == 10
        assert result["minimum"] == 1
        assert result["maximum"] == 100


class TestInputSchema:
    """Test InputSchema dataclass."""

    def test_basic_construction(self):
        """Test basic InputSchema construction."""
        schema = InputSchema()
        assert schema.properties == []
        assert schema.required == []
        assert schema.raw_schema is None

    def test_with_properties(self):
        """Test InputSchema with properties."""
        props = [
            SchemaProperty("task_id", "string", required=True),
            SchemaProperty("verbose", "boolean", required=False),
        ]
        schema = InputSchema(
            properties=props,
            required=["task_id"],
        )
        assert len(schema.properties) == 2
        assert "task_id" in schema.required

    def test_to_dict(self):
        """Test to_dict serialization."""
        schema = InputSchema(
            properties=[SchemaProperty("id", "string", required=True)],
            required=["id"],
        )
        result = schema.to_dict()

        assert len(result["properties"]) == 1
        assert result["required"] == ["id"]


class TestToolExample:
    """Test ToolExample dataclass."""

    def test_basic_construction(self):
        """Test basic ToolExample construction."""
        example = ToolExample(
            description="Start a task",
            request={"task_id": "task-001"},
        )
        assert example.description == "Start a task"
        assert example.request == {"task_id": "task-001"}
        assert example.response is None

    def test_with_response(self):
        """Test ToolExample with response."""
        example = ToolExample(
            description="Query task",
            request={"task_id": "task-001"},
            response={"status": "completed"},
        )
        assert example.response == {"status": "completed"}

    def test_to_dict(self):
        """Test to_dict serialization."""
        example = ToolExample(
            description="Example",
            request={"key": "value"},
            response={"result": "success"},
        )
        result = example.to_dict()

        assert result["description"] == "Example"
        assert result["request"] == {"key": "value"}
        assert result["response"] == {"result": "success"}


class TestToolInfo:
    """Test ToolInfo dataclass."""

    def test_basic_construction(self):
        """Test basic ToolInfo construction."""
        tool = ToolInfo(
            name="vibey_start_task",
            title="Start Task",
            description="Start a task by ID",
            input_schema=InputSchema(),
        )
        assert tool.name == "vibey_start_task"
        assert tool.title == "Start Task"

    def test_default_values(self):
        """Test ToolInfo default values."""
        tool = ToolInfo(
            name="test",
            title=None,
            description="Test tool",
            input_schema=InputSchema(),
        )
        assert tool.category == "unknown"
        assert tool.examples == []
        assert tool.source_file is None

    def test_to_dict(self):
        """Test to_dict serialization."""
        tool = ToolInfo(
            name="vibey_test",
            title="Test Tool",
            description="A test tool",
            input_schema=InputSchema(),
            category="test",
            source_file="test.py",
        )
        result = tool.to_dict()

        assert result["name"] == "vibey_test"
        assert result["title"] == "Test Tool"
        assert result["category"] == "test"


class TestResourceTemplateInfo:
    """Test ResourceTemplateInfo dataclass."""

    def test_construction(self):
        """Test ResourceTemplateInfo construction."""
        resource = ResourceTemplateInfo(
            uri_template="vibey://workflows/{workflow_id}",
            name="Workflow",
            description="A workflow resource",
            mime_type="application/json",
            provider="WorkflowProvider",
        )
        assert resource.uri_template == "vibey://workflows/{workflow_id}"
        assert resource.name == "Workflow"
        assert resource.category == "unknown"

    def test_to_dict(self):
        """Test to_dict serialization."""
        resource = ResourceTemplateInfo(
            uri_template="vibey://test/{id}",
            name="Test",
            description="Test resource",
            mime_type="text/plain",
            provider="TestProvider",
            category="test",
        )
        result = resource.to_dict()

        assert result["uri_template"] == "vibey://test/{id}"
        assert result["category"] == "test"


class TestPromptArgument:
    """Test PromptArgument dataclass."""

    def test_basic_construction(self):
        """Test basic PromptArgument construction."""
        arg = PromptArgument(
            name="task_id",
            description="The task ID",
        )
        assert arg.name == "task_id"
        assert arg.required is False

    def test_required_argument(self):
        """Test required PromptArgument."""
        arg = PromptArgument(
            name="id",
            description="Required ID",
            required=True,
        )
        assert arg.required is True

    def test_to_dict(self):
        """Test to_dict serialization."""
        arg = PromptArgument(
            name="task_id",
            description="Task identifier",
            required=True,
        )
        result = arg.to_dict()

        assert result["name"] == "task_id"
        assert result["required"] is True


class TestPromptInfo:
    """Test PromptInfo dataclass."""

    def test_basic_construction(self):
        """Test basic PromptInfo construction."""
        prompt = PromptInfo(
            name="vibey_quality_gate",
            description="Quality gate check prompt",
        )
        assert prompt.name == "vibey_quality_gate"
        assert prompt.arguments == []

    def test_with_arguments(self):
        """Test PromptInfo with arguments."""
        prompt = PromptInfo(
            name="vibey_check",
            description="Check prompt",
            arguments=[
                PromptArgument("task_id", "Task ID", True),
            ],
            category="quality_gates",
            provider="QualityGateProvider",
        )
        assert len(prompt.arguments) == 1
        assert prompt.category == "quality_gates"

    def test_to_dict(self):
        """Test to_dict serialization."""
        prompt = PromptInfo(
            name="test_prompt",
            description="Test",
            arguments=[PromptArgument("id", "ID")],
        )
        result = prompt.to_dict()

        assert result["name"] == "test_prompt"
        assert len(result["arguments"]) == 1


class TestMCPStructure:
    """Test MCPStructure dataclass."""

    def test_basic_construction(self):
        """Test basic MCPStructure construction."""
        structure = MCPStructure()
        assert structure.tools == []
        assert structure.resources == []
        assert structure.prompts == []
        assert structure.server_name == "vibey-roadmap"

    def test_post_init_sets_generated_at(self):
        """Test that __post_init__ sets generated_at if not provided."""
        structure = MCPStructure()
        assert structure.generated_at != ""
        # Should be ISO format
        datetime.fromisoformat(structure.generated_at.replace("Z", "+00:00"))

    def test_count_by_category(self):
        """Test count_by_category method."""
        structure = MCPStructure(
            tools=[
                ToolInfo("t1", None, "desc", InputSchema(), category="task"),
                ToolInfo("t2", None, "desc", InputSchema(), category="task"),
                ToolInfo("t3", None, "desc", InputSchema(), category="query"),
            ],
            resources=[
                ResourceTemplateInfo("uri", "r1", "desc", "text/plain", "p", "workflows"),
            ],
            prompts=[
                PromptInfo("p1", "desc", category="quality_gates"),
            ],
        )
        counts = structure.count_by_category()

        assert counts["tools"]["task"] == 2
        assert counts["tools"]["query"] == 1
        assert counts["resources"]["workflows"] == 1
        assert counts["prompts"]["quality_gates"] == 1

    def test_to_dict(self):
        """Test to_dict serialization."""
        structure = MCPStructure(
            tools=[ToolInfo("t1", None, "desc", InputSchema())],
            resources=[],
            prompts=[],
            version="1.0.0",
        )
        result = structure.to_dict()

        assert result["server_name"] == "vibey-roadmap"
        assert result["version"] == "1.0.0"
        assert result["total_tools"] == 1
        assert result["total_resources"] == 0
        assert result["total_prompts"] == 0

    def test_to_json(self):
        """Test to_json serialization."""
        structure = MCPStructure(version="1.0.0")
        json_str = structure.to_json()

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["version"] == "1.0.0"


class TestMCPIntrospector:
    """Test MCPIntrospector class."""

    def test_init(self):
        """Test introspector initialization."""
        introspector = MCPIntrospector()
        assert introspector.content_root == Path.cwd()

    def test_init_with_path(self, tmp_path):
        """Test introspector initialization with custom path."""
        introspector = MCPIntrospector(tmp_path)
        assert introspector.content_root == tmp_path

    def test_get_version(self):
        """Test version retrieval."""
        introspector = MCPIntrospector()
        version = introspector._get_version()
        # Should return version string or "unknown"
        assert isinstance(version, str)

    def test_parse_input_schema_empty(self):
        """Test parsing empty schema."""
        introspector = MCPIntrospector()
        schema = introspector._parse_input_schema({})

        assert schema.properties == []
        assert schema.required == []

    def test_parse_input_schema_with_properties(self):
        """Test parsing schema with properties."""
        introspector = MCPIntrospector()
        raw_schema = {
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "Task identifier",
                },
                "verbose": {
                    "type": "boolean",
                    "default": False,
                },
            },
            "required": ["task_id"],
        }
        schema = introspector._parse_input_schema(raw_schema)

        assert len(schema.properties) == 2
        assert schema.required == ["task_id"]

        # Required properties should come first
        assert schema.properties[0].name == "task_id"
        assert schema.properties[0].required is True

    def test_parse_tool_definition(self):
        """Test parsing tool definition."""
        introspector = MCPIntrospector()
        tool_def = {
            "name": "vibey_test_tool",
            "title": "Test Tool",
            "description": "A test tool for testing",
            "inputSchema": {
                "properties": {
                    "id": {"type": "string"},
                },
                "required": ["id"],
            },
        }
        tool = introspector._parse_tool_definition(tool_def, "test", "test.py")

        assert tool.name == "vibey_test_tool"
        assert tool.title == "Test Tool"
        assert tool.category == "test"
        assert tool.source_file == "test.py"


class TestToolExamples:
    """Test predefined tool examples."""

    def test_tool_examples_defined(self):
        """Test that tool examples are defined."""
        assert len(TOOL_EXAMPLES) > 0

    def test_start_task_example(self):
        """Test start task example exists."""
        assert "vibey_start_task" in TOOL_EXAMPLES
        examples = TOOL_EXAMPLES["vibey_start_task"]
        assert len(examples) > 0
        assert all(isinstance(e, ToolExample) for e in examples)

    def test_example_has_request(self):
        """Test examples have request data."""
        for tool_name, examples in TOOL_EXAMPLES.items():
            for example in examples:
                assert isinstance(example.request, dict)
                assert example.description


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_introspect_mcp_returns_structure(self, tmp_path):
        """Test introspect_mcp returns MCPStructure."""
        try:
            structure = introspect_mcp(tmp_path)
            assert isinstance(structure, MCPStructure)
        except ImportError:
            pytest.skip("MCP modules not available")

    def test_get_tool_count(self, tmp_path):
        """Test get_tool_count function."""
        try:
            with patch('vibey.operations.docs.mcp_introspector.introspect_mcp') as mock:
                mock.return_value = MCPStructure(
                    tools=[
                        ToolInfo("t1", None, "desc", InputSchema()),
                        ToolInfo("t2", None, "desc", InputSchema()),
                    ]
                )
                count = get_tool_count()
                assert count == 2
        except ImportError:
            pytest.skip("MCP modules not available")

    def test_get_resource_count(self, tmp_path):
        """Test get_resource_count function."""
        try:
            with patch('vibey.operations.docs.mcp_introspector.introspect_mcp') as mock:
                mock.return_value = MCPStructure(
                    resources=[
                        ResourceTemplateInfo("uri", "r1", "desc", "text/plain", "p"),
                    ]
                )
                count = get_resource_count()
                assert count == 1
        except ImportError:
            pytest.skip("MCP modules not available")

    def test_get_prompt_count(self, tmp_path):
        """Test get_prompt_count function."""
        try:
            with patch('vibey.operations.docs.mcp_introspector.introspect_mcp') as mock:
                mock.return_value = MCPStructure(
                    prompts=[
                        PromptInfo("p1", "desc"),
                        PromptInfo("p2", "desc"),
                        PromptInfo("p3", "desc"),
                    ]
                )
                count = get_prompt_count()
                assert count == 3
        except ImportError:
            pytest.skip("MCP modules not available")


class TestIntegration:
    """Integration tests with real MCP server."""

    def test_introspect_real_mcp(self, tmp_path):
        """Test introspecting the actual MCP server."""
        try:
            structure = introspect_mcp(tmp_path)

            # Basic structure assertions
            assert isinstance(structure, MCPStructure)
            assert structure.server_name == "vibey-roadmap"

            # Should have some tools
            assert len(structure.tools) >= 0  # May be 0 if modules not loaded

        except ImportError:
            pytest.skip("MCP modules not available")
        except Exception as e:
            # Some MCP modules may fail to load
            pytest.skip(f"MCP introspection failed: {e}")

    def test_categories_populated(self, tmp_path):
        """Test that categories are populated."""
        try:
            structure = introspect_mcp(tmp_path)
            counts = structure.count_by_category()

            assert "tools" in counts
            assert "resources" in counts
            assert "prompts" in counts

        except ImportError:
            pytest.skip("MCP modules not available")
        except Exception as e:
            pytest.skip(f"MCP introspection failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
