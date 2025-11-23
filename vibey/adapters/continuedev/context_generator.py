"""
Continue.dev Context Generator.

Generates CONTINUE.md context files from Vibey agent frontmatter.
This ensures zero-drift: the generated context always matches
the source agent definitions.

Continue Context:
- Continue supports custom system prompts and context providers
- .continuerc.yaml or ~/.continue/config.yaml for configuration
- rules field for project-specific instructions
"""

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from framework.mcp.discovery.agents import AgentDefinition, AgentDiscovery
from framework.mcp.discovery.workflows import WorkflowDefinition, WorkflowDiscovery

logger = logging.getLogger(__name__)


@dataclass
class GeneratedContext:
    """Result of context generation."""
    content: str
    checksum: str
    agents_count: int
    workflows_count: int
    generated_at: datetime


class ContinueContextGenerator:
    """
    Generate context content from Vibey agent frontmatter for Continue.dev.

    Zero-Drift Guarantee:
    - Reads directly from agent/workflow frontmatter (single source of truth)
    - Generates checksum for drift detection
    - CI can validate no manual edits occurred

    Example:
        >>> generator = ContinueContextGenerator(Path("/path/to/vibey"))
        >>> result = generator.generate()
        >>> Path("CONTINUE.md").write_text(result.content)
    """

    def __init__(self, root_dir: Path):
        """
        Initialize context generator.

        Args:
            root_dir: Root directory of Vibey repository
        """
        self.root_dir = Path(root_dir)
        self.agent_discovery = AgentDiscovery(root_dir)
        self.workflow_discovery = WorkflowDiscovery(root_dir)

    def generate(
        self,
        include_workflows: bool = True,
        include_mcp_instructions: bool = True,
    ) -> GeneratedContext:
        """
        Generate context content from frontmatter.

        Args:
            include_workflows: Include workflow documentation
            include_mcp_instructions: Include MCP tool usage instructions

        Returns:
            GeneratedContext with content and metadata
        """
        agents = self.agent_discovery.discover()
        workflows = self.workflow_discovery.discover() if include_workflows else []

        content = self._build_content(agents, workflows, include_mcp_instructions)
        checksum = self._calculate_checksum(content)

        return GeneratedContext(
            content=content,
            checksum=checksum,
            agents_count=len(agents),
            workflows_count=len(workflows),
            generated_at=datetime.now(timezone.utc),
        )

    def _build_content(
        self,
        agents: List[AgentDefinition],
        workflows: List[WorkflowDefinition],
        include_mcp: bool,
    ) -> str:
        """Build the context content."""
        sections = [
            self._build_header(),
            self._build_agent_section(agents),
        ]

        if workflows:
            sections.append(self._build_workflow_section(workflows))

        if include_mcp:
            sections.append(self._build_mcp_section(agents, workflows))

        sections.append(self._build_footer())

        return "\n\n".join(sections)

    def _build_header(self) -> str:
        """Build the header section."""
        return """# Vibey Agent Framework

This project uses the **Vibey Agent Framework** for intelligent workflow management.
Vibey provides specialized AI agents and MCP tools for different development tasks.

## Quick Start

Use the available MCP tools (prefixed with `vibey_`) to interact with the framework.
The Vibey MCP server provides 46 tools for roadmap management, agents, and workflows.

---"""

    def _build_agent_section(self, agents: List[AgentDefinition]) -> str:
        """Build the agents section."""
        if not agents:
            return "## Available Agents\n\nNo agents discovered."

        lines = ["## Available Agents", ""]

        for agent in agents:
            tool_name = agent.id.replace('-', '_')
            lines.append(f"### {agent.name}")
            lines.append(f"**Tool:** `vibey_{tool_name}`")
            if agent.description:
                lines.append(f"**Description:** {agent.description}")

            if agent.triggers and isinstance(agent.triggers, dict):
                keywords = agent.triggers.get('keywords', [])
                if keywords:
                    triggers_str = ", ".join(keywords[:5])
                    lines.append(f"**Triggers:** {triggers_str}")

            lines.append("")

        return "\n".join(lines)

    def _build_workflow_section(self, workflows: List[WorkflowDefinition]) -> str:
        """Build the workflows section."""
        if not workflows:
            return "## Available Workflows\n\nNo workflows discovered."

        lines = ["## Available Workflows", ""]

        for workflow in workflows:
            tool_name = workflow.id.replace('-', '_')
            lines.append(f"### {workflow.name}")
            lines.append(f"**Tool:** `vibey_workflow_{tool_name}`")
            if workflow.description:
                lines.append(f"**Description:** {workflow.description}")

            if workflow.steps:
                lines.append(f"**Steps:** {len(workflow.steps)}")

            if workflow.duration:
                lines.append(f"**Duration:** {workflow.duration}")

            lines.append("")

        return "\n".join(lines)

    def _build_mcp_section(
        self,
        agents: List[AgentDefinition],
        workflows: List[WorkflowDefinition],
    ) -> str:
        """Build MCP usage instructions section."""
        return """## MCP Integration

The Vibey MCP server is configured in your Continue settings. Available tool categories:

### Roadmap Tools
- `vibey_roadmap_status` - Get overall roadmap status
- `vibey_start_task` / `vibey_complete_task` - Manage tasks
- `vibey_start_sprint` / `vibey_complete_sprint` - Manage sprints
- `vibey_query_task` / `vibey_query_sprint` / `vibey_query_track` - Query details
- `vibey_list_blockers` / `vibey_list_dependencies` - Check blockers
- `vibey_refresh_progress` - Recalculate progress metrics

### Agent Tools
Use agent tools for specialized development tasks. Each agent has deep expertise
in its domain and follows structured workflows.

### Workflow Tools
Use workflow tools for multi-step development processes. Workflows coordinate
multiple agents and ensure quality gates are passed.

---"""

    def _build_footer(self) -> str:
        """Build the footer section."""
        timestamp = datetime.now(timezone.utc).isoformat()
        return f"""---

<!-- Generated: {timestamp} -->
<!-- Generator: vibey-continue-adapter -->
<!-- DO NOT EDIT: This file is generated from Vibey frontmatter -->
"""

    def _calculate_checksum(self, content: str) -> str:
        """Calculate checksum for drift detection."""
        # Remove timestamp line for stable checksum
        lines = content.split("\n")
        stable_lines = [l for l in lines if not l.startswith("<!-- Generated:")]
        stable_content = "\n".join(stable_lines)
        return hashlib.sha256(stable_content.encode()).hexdigest()[:16]

    def write_to_file(self, output_path: Path) -> GeneratedContext:
        """
        Generate and write context to file.

        Args:
            output_path: Path to write CONTINUE.md

        Returns:
            GeneratedContext with metadata
        """
        result = self.generate()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result.content, encoding='utf-8')
        logger.info(
            f"Wrote {output_path}: {result.agents_count} agents, "
            f"{result.workflows_count} workflows"
        )
        return result
