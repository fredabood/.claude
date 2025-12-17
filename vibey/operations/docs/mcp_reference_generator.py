"""
MCP Reference Markdown Generator

Generates comprehensive MCP server reference documentation from introspected
server structure. Produces Markdown files suitable for documentation sites.

Usage:
    from vibey.operations.docs.mcp_reference_generator import generate_mcp_reference

    markdown = generate_mcp_reference()
    Path("docs/reference/MCP_REFERENCE.md").write_text(markdown)

Task: 01KC81GRE23T0KSHR4ZCES476Z
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict

from vibey.operations.docs.mcp_introspector import (
    MCPStructure,
    ToolInfo,
    ResourceTemplateInfo,
    PromptInfo,
    SchemaProperty,
    ToolExample,
    PromptArgument,
    introspect_mcp,
)


@dataclass
class GeneratorConfig:
    """Configuration for the MCP Markdown generator."""
    # Include table of contents
    include_toc: bool = True
    # Include component index
    include_index: bool = True
    # Include examples for tools
    include_examples: bool = True
    # Max heading depth (h1 to hN)
    max_heading_depth: int = 4
    # Include generation timestamp
    include_timestamp: bool = True
    # Group tools by category
    group_by_category: bool = True


class MCPReferenceGenerator:
    """
    Generates Markdown documentation from MCP server structure.

    Usage:
        from vibey.operations.docs.mcp_introspector import introspect_mcp

        structure = introspect_mcp()
        generator = MCPReferenceGenerator(structure)
        markdown = generator.generate()
    """

    def __init__(
        self,
        structure: MCPStructure,
        config: Optional[GeneratorConfig] = None,
    ):
        """
        Initialize the generator.

        Args:
            structure: Introspected MCP structure
            config: Generator configuration
        """
        self.structure = structure
        self.config = config or GeneratorConfig()
        self._lines: List[str] = []

    def generate(self) -> str:
        """
        Generate complete MCP reference documentation.

        Returns:
            Markdown string
        """
        self._lines = []

        # Header
        self._add_header()

        # Usage guidance (when to use MCP vs CLI)
        self._add_usage_guidance()

        # Table of contents
        if self.config.include_toc:
            self._add_toc()

        # Quick reference
        self._add_quick_reference()

        # Tools section
        self._add_tools_section()

        # Resources section
        self._add_resources_section()

        # Prompts section
        self._add_prompts_section()

        # Footer
        self._add_footer()

        return "\n".join(self._lines)

    def _line(self, text: str = ""):
        """Add a line to the output."""
        self._lines.append(text)

    def _heading(self, text: str, level: int):
        """Add a heading, respecting max depth."""
        level = min(level, self.config.max_heading_depth)
        self._line(f"{'#' * level} {text}")
        self._line()

    def _make_anchor(self, text: str) -> str:
        """Create a markdown anchor from text."""
        return text.lower().replace(" ", "-").replace("_", "-")

    def _add_header(self):
        """Add document header."""
        self._heading("MCP Server Reference", 1)

        self._line(f"**Server:** {self.structure.server_name}")
        self._line(f"**Version:** {self.structure.version}")
        self._line()

        if self.config.include_timestamp:
            self._line(f"**Generated:** {self.structure.generated_at}")
            self._line()

        self._line("This document provides comprehensive reference documentation for the "
                  "Vibey MCP (Model Context Protocol) server, including all tools, resources, "
                  "and prompts available for AI assistant integration.")
        self._line()

        # Stats box
        self._line("| Component | Count |")
        self._line("|-----------|-------|")
        self._line(f"| Tools | {len(self.structure.tools)} |")
        self._line(f"| Resources | {len(self.structure.resources)} |")
        self._line(f"| Prompts | {len(self.structure.prompts)} |")
        self._line()

        self._line("---")
        self._line()

    def _add_usage_guidance(self):
        """Add guidance on when to use MCP vs CLI."""
        self._heading("When to Use MCP vs CLI", 2)

        self._line("### Use MCP Tools When:")
        self._line()
        self._line("- **AI Assistant Integration** - Working within Claude, Cursor, or other AI tools")
        self._line("- **Programmatic Access** - Building automation or integrations")
        self._line("- **Structured Data** - Need JSON responses for processing")
        self._line("- **Context Preservation** - AI needs to maintain conversation context")
        self._line()

        self._line("### Use CLI Commands When:")
        self._line()
        self._line("- **Terminal Workflows** - Direct command-line interaction")
        self._line("- **Shell Scripts** - Automation via bash/shell")
        self._line("- **Human Readable** - Want formatted, colorized output")
        self._line("- **Quick Operations** - One-off commands")
        self._line()

        self._line("### Common Operations Mapping")
        self._line()
        self._line("| Operation | CLI Command | MCP Tool |")
        self._line("|-----------|-------------|----------|")
        self._line("| Get status | `vibey roadmap status` | `roadmap_status` |")
        self._line("| Start task | `vibey roadmap start <id>` | `task_start` |")
        self._line("| Complete task | `vibey roadmap complete <id>` | `task_complete` |")
        self._line("| Query task | `vibey roadmap show <id>` | `task_query` |")
        self._line("| List sprints | `vibey roadmap list sprints` | `sprint_list` |")
        self._line("| Deploy config | `vibey deploy run --platform X` | N/A (CLI only) |")
        self._line()

        self._line("---")
        self._line()

    def _add_toc(self):
        """Add table of contents."""
        self._heading("Table of Contents", 2)

        self._line("- [Quick Reference](#quick-reference)")
        self._line("- [Tools](#tools)")

        # Tool categories
        if self.config.group_by_category:
            categories = self._get_tool_categories()
            for category in categories:
                anchor = self._make_anchor(f"{category}-tools")
                self._line(f"  - [{category.title()} Tools](#{anchor})")

        self._line("- [Resources](#resources)")

        # Resource categories
        resource_cats = self._get_resource_categories()
        for category in resource_cats:
            anchor = self._make_anchor(f"{category}-resources")
            self._line(f"  - [{category.title()} Resources](#{anchor})")

        self._line("- [Prompts](#prompts)")
        self._line()
        self._line("---")
        self._line()

    def _add_quick_reference(self):
        """Add quick reference tables."""
        self._heading("Quick Reference", 2)

        # Tool summary by category
        self._heading("Tools by Category", 3)
        categories = self.structure.count_by_category()["tools"]
        self._line("| Category | Count | Description |")
        self._line("|----------|-------|-------------|")

        category_descriptions = {
            "task": "Task lifecycle management (start, complete, query)",
            "sprint": "Sprint management and progress tracking",
            "query": "Roadmap queries and status checks",
            "content": "Content management (list, show, search)",
            "agent": "Agent invocation tools",
            "workflow": "Workflow execution tools",
            "handoff": "Handoff template tools",
        }

        for cat, count in sorted(categories.items()):
            desc = category_descriptions.get(cat, "")
            self._line(f"| {cat.title()} | {count} | {desc} |")
        self._line()

        # Resource summary
        self._heading("Resources by Provider", 3)
        self._line("| Provider | Templates | URI Pattern |")
        self._line("|----------|-----------|-------------|")

        providers: Dict[str, List[ResourceTemplateInfo]] = {}
        for resource in self.structure.resources:
            if resource.provider not in providers:
                providers[resource.provider] = []
            providers[resource.provider].append(resource)

        for provider, resources in sorted(providers.items()):
            uri_pattern = resources[0].uri_template.split("{")[0] + "..."
            self._line(f"| {provider} | {len(resources)} | `{uri_pattern}` |")
        self._line()

        self._line("---")
        self._line()

    def _get_tool_categories(self) -> List[str]:
        """Get sorted list of tool categories."""
        categories = set(t.category for t in self.structure.tools)
        # Order: core operations first, then dynamic
        order = ["task", "sprint", "query", "content", "agent", "workflow", "handoff"]
        result = [c for c in order if c in categories]
        result.extend(sorted(c for c in categories if c not in order))
        return result

    def _get_resource_categories(self) -> List[str]:
        """Get sorted list of resource categories."""
        return sorted(set(r.category for r in self.structure.resources))

    def _add_tools_section(self):
        """Add tools documentation section."""
        self._heading("Tools", 2)

        self._line("MCP tools enable AI assistants to interact with the Vibey roadmap system. "
                  "Each tool has a defined input schema and produces structured output.")
        self._line()

        if self.config.group_by_category:
            # Group by category
            categories = self._get_tool_categories()
            for category in categories:
                tools = [t for t in self.structure.tools if t.category == category]
                self._add_tool_category(category, tools)
        else:
            # Alphabetical
            for tool in sorted(self.structure.tools, key=lambda t: t.name):
                self._add_tool(tool)

    def _add_tool_category(self, category: str, tools: List[ToolInfo]):
        """Add a category of tools."""
        self._heading(f"{category.title()} Tools", 3)

        # Category description
        category_intros = {
            "task": "Task tools manage individual task lifecycle - starting, completing, and querying tasks.",
            "sprint": "Sprint tools handle sprint management including starting, completing, and progress tracking.",
            "query": "Query tools provide read-only access to roadmap data including tracks, blockers, and status.",
            "content": "Content tools manage framework content including agents, workflows, and handoffs.",
            "agent": "Agent tools invoke specialized AI agents defined in the framework.",
            "workflow": "Workflow tools execute predefined development workflows.",
            "handoff": "Handoff tools generate structured handoff documents between agents.",
        }

        intro = category_intros.get(category, "")
        if intro:
            self._line(intro)
            self._line()

        # Tool index for this category
        self._line("| Tool | Description |")
        self._line("|------|-------------|")
        for tool in tools:
            anchor = self._make_anchor(tool.name)
            desc = tool.description[:80] + "..." if len(tool.description) > 80 else tool.description
            self._line(f"| [`{tool.name}`](#{anchor}) | {desc} |")
        self._line()

        # Individual tools
        for tool in tools:
            self._add_tool(tool)

    def _add_tool(self, tool: ToolInfo):
        """Add documentation for a single tool."""
        self._heading(f"`{tool.name}`", 4)

        if tool.title:
            self._line(f"**{tool.title}**")
            self._line()

        self._line(tool.description)
        self._line()

        # Input schema
        if tool.input_schema.properties:
            self._line("**Parameters:**")
            self._line()
            self._line("| Name | Type | Required | Description |")
            self._line("|------|------|----------|-------------|")

            for prop in tool.input_schema.properties:
                required = "Yes" if prop.required else "No"
                desc = prop.description or ""
                if prop.default is not None:
                    desc += f" (default: `{prop.default}`)"
                if prop.enum:
                    desc += f" (enum: {', '.join(f'`{e}`' for e in prop.enum)})"
                self._line(f"| `{prop.name}` | `{prop.type}` | {required} | {desc} |")
            self._line()
        else:
            self._line("**Parameters:** None")
            self._line()

        # Examples
        if self.config.include_examples and tool.examples:
            self._line("**Examples:**")
            self._line()
            for example in tool.examples:
                self._line(f"*{example.description}:*")
                self._line()
                self._line("```json")
                import json
                self._line(json.dumps(example.request, indent=2))
                self._line("```")
                self._line()

        # Source file reference
        if tool.source_file:
            self._line(f"*Source: `{tool.source_file}`*")
            self._line()

        self._line("---")
        self._line()

    def _add_resources_section(self):
        """Add resources documentation section."""
        self._heading("Resources", 2)

        self._line("MCP resources provide access to Vibey framework content via URI patterns. "
                  "Resources support both direct access and template-based discovery.")
        self._line()

        # Group by category
        categories = self._get_resource_categories()
        for category in categories:
            resources = [r for r in self.structure.resources if r.category == category]
            self._add_resource_category(category, resources)

    def _add_resource_category(self, category: str, resources: List[ResourceTemplateInfo]):
        """Add a category of resources."""
        self._heading(f"{category.title()} Resources", 3)

        category_intros = {
            "workflows": "Workflow resources provide access to workflow definitions, steps, and metadata.",
            "handoffs": "Handoff resources provide access to handoff templates and variable schemas.",
        }

        intro = category_intros.get(category, "")
        if intro:
            self._line(intro)
            self._line()

        # Resource table
        self._line("| URI Template | Name | MIME Type |")
        self._line("|--------------|------|-----------|")
        for resource in resources:
            self._line(f"| `{resource.uri_template}` | {resource.name} | `{resource.mime_type}` |")
        self._line()

        # Details
        for resource in resources:
            self._add_resource(resource)

    def _add_resource(self, resource: ResourceTemplateInfo):
        """Add documentation for a single resource template."""
        self._heading(f"`{resource.uri_template}`", 4)

        self._line(f"**{resource.name}**")
        self._line()
        self._line(resource.description)
        self._line()

        self._line(f"- **MIME Type:** `{resource.mime_type}`")
        self._line(f"- **Provider:** `{resource.provider}`")
        self._line()

        # Example usage
        self._line("**Example:**")
        self._line()
        self._line("```")
        # Generate example URI
        example_uri = resource.uri_template.replace("{workflow_id}", "sprint-planning")
        example_uri = example_uri.replace("{handoff_id}", "diagram-handoff")
        self._line(f"GET {example_uri}")
        self._line("```")
        self._line()

    def _add_prompts_section(self):
        """Add prompts documentation section."""
        self._heading("Prompts", 2)

        self._line("MCP prompts provide structured prompt templates for common tasks. "
                  "Each prompt accepts arguments to customize the generated instructions.")
        self._line()

        # Prompt table
        self._line("| Prompt | Description | Required Args |")
        self._line("|--------|-------------|---------------|")
        for prompt in self.structure.prompts:
            required = ", ".join(f"`{a.name}`" for a in prompt.arguments if a.required) or "None"
            desc = prompt.description[:60] + "..." if len(prompt.description) > 60 else prompt.description
            self._line(f"| `{prompt.name}` | {desc} | {required} |")
        self._line()

        # Individual prompts
        for prompt in self.structure.prompts:
            self._add_prompt(prompt)

    def _add_prompt(self, prompt: PromptInfo):
        """Add documentation for a single prompt."""
        self._heading(f"`{prompt.name}`", 3)

        self._line(prompt.description)
        self._line()

        if prompt.arguments:
            self._line("**Arguments:**")
            self._line()
            self._line("| Name | Required | Description |")
            self._line("|------|----------|-------------|")
            for arg in prompt.arguments:
                required = "Yes" if arg.required else "No"
                self._line(f"| `{arg.name}` | {required} | {arg.description} |")
            self._line()
        else:
            self._line("**Arguments:** None")
            self._line()

        # Provider info
        if prompt.provider:
            self._line(f"*Provider: `{prompt.provider}`*")
            self._line()

        self._line("---")
        self._line()

    def _add_footer(self):
        """Add document footer."""
        self._line("## About This Document")
        self._line()
        self._line("This reference was auto-generated from the Vibey MCP server implementation. "
                  "It cannot drift from the actual implementation because it is generated directly "
                  "from the source code.")
        self._line()
        self._line("To regenerate this document:")
        self._line()
        self._line("```bash")
        self._line("vibey docs generate-mcp")
        self._line("```")
        self._line()
        self._line("To check for drift:")
        self._line()
        self._line("```bash")
        self._line("vibey docs check-mcp-drift")
        self._line("```")
        self._line()


# =============================================================================
# Convenience Functions
# =============================================================================


def generate_mcp_reference(
    structure: Optional[MCPStructure] = None,
    config: Optional[GeneratorConfig] = None,
) -> str:
    """
    Generate MCP reference documentation.

    Args:
        structure: Pre-introspected structure (introspects if not provided)
        config: Generator configuration

    Returns:
        Markdown string

    Example:
        >>> markdown = generate_mcp_reference()
        >>> Path("docs/reference/MCP_REFERENCE.md").write_text(markdown)
    """
    if structure is None:
        structure = introspect_mcp()

    generator = MCPReferenceGenerator(structure, config)
    return generator.generate()
