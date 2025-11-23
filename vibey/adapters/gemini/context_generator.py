"""
Gemini Context Generator.

Generates GEMINI.md context files from Vibey agent frontmatter.
This ensures zero-drift: the generated GEMINI.md always matches
the source agent definitions.

Gemini Context File Structure:
- GEMINI.md in project root or ~/.gemini/GEMINI.md for global
- Supports @file.md imports for modular context
- Hierarchical loading (subdirectory GEMINI.md files)
"""

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from framework.mcp.discovery.agents import AgentDefinition, AgentDiscovery
from framework.mcp.discovery.workflows import WorkflowDefinition, WorkflowDiscovery
from .orchestration import SequentialOrchestrator

logger = logging.getLogger(__name__)


@dataclass
class GeneratedContext:
    """Result of context generation."""
    content: str
    checksum: str
    agents_count: int
    workflows_count: int
    generated_at: datetime


class GeminiContextGenerator:
    """
    Generate GEMINI.md context files from Vibey agent frontmatter.

    Zero-Drift Guarantee:
    - Reads directly from agent/workflow frontmatter (single source of truth)
    - Generates checksum for drift detection
    - CI can validate no manual edits occurred

    Example:
        >>> generator = GeminiContextGenerator(Path("/path/to/vibey"))
        >>> result = generator.generate()
        >>> Path("GEMINI.md").write_text(result.content)
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
        self.orchestrator = SequentialOrchestrator(root_dir)

    def generate(
        self,
        include_workflows: bool = True,
        include_mcp_instructions: bool = True,
        include_orchestration: bool = True,
    ) -> GeneratedContext:
        """
        Generate GEMINI.md content from frontmatter.

        Args:
            include_workflows: Include workflow documentation
            include_mcp_instructions: Include MCP tool usage instructions
            include_orchestration: Include sequential orchestration hints

        Returns:
            GeneratedContext with content and metadata
        """
        agents = self.agent_discovery.discover()
        workflows = self.workflow_discovery.discover() if include_workflows else []

        content = self._build_content(
            agents, workflows, include_mcp_instructions, include_orchestration
        )
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
        include_orchestration: bool = True,
    ) -> str:
        """Build the GEMINI.md content."""
        sections = [
            self._build_header(),
            self._build_agent_section(agents),
        ]

        if workflows:
            sections.append(self._build_workflow_section(workflows))

        # Add orchestration hints for sequential execution guidance
        if include_orchestration and workflows:
            orchestration_section = self._build_orchestration_section()
            if orchestration_section:
                sections.append(orchestration_section)

        if include_mcp:
            sections.append(self._build_mcp_section(agents, workflows))

        sections.append(self._build_footer())

        return "\n\n".join(sections)

    def _build_orchestration_section(self) -> Optional[str]:
        """Build sequential orchestration hints section."""
        try:
            result = self.orchestrator.analyze()
            if result.orchestration_hints:
                return result.orchestration_hints
        except Exception as e:
            logger.warning(f"Failed to generate orchestration hints: {e}")
        return None

    def _build_header(self) -> str:
        """Build the header section."""
        return """# Vibey Agent Framework

This project uses the **Vibey Agent Framework** for intelligent workflow management.
Vibey provides specialized AI agents for different development tasks.

## Quick Start

Use the available MCP tools (prefixed with `vibey_`) or custom commands
(prefixed with `/vibey:`) to interact with the framework.

---"""

    def _build_agent_section(self, agents: List[AgentDefinition]) -> str:
        """Build the agents documentation section."""
        if not agents:
            return "## Agents\n\nNo agents discovered."

        lines = ["## Available Agents\n"]

        # Group agents by type
        agents_by_type: dict[str, List[AgentDefinition]] = {}
        for agent in agents:
            agent_type = agent.type or "other"
            if agent_type not in agents_by_type:
                agents_by_type[agent_type] = []
            agents_by_type[agent_type].append(agent)

        # Build section for each type
        for agent_type in sorted(agents_by_type.keys()):
            type_agents = agents_by_type[agent_type]
            lines.append(f"### {agent_type.title()} Agents\n")

            for agent in sorted(type_agents, key=lambda a: a.name):
                lines.append(f"**{agent.name}** (`{agent.id}`)")
                if agent.description:
                    lines.append(f": {agent.description}")
                else:
                    lines.append("")

                # Add trigger keywords if present
                if agent.triggers:
                    keywords = agent.triggers.get('keywords', [])
                    if keywords:
                        lines.append(f"- Triggers: {', '.join(keywords[:5])}")

                # Add MCP tool reference
                lines.append(f"- MCP Tool: `vibey_{agent.id.replace('-', '_')}`")
                lines.append("")

        return "\n".join(lines)

    def _build_workflow_section(self, workflows: List[WorkflowDefinition]) -> str:
        """Build the workflows documentation section."""
        if not workflows:
            return "## Workflows\n\nNo workflows discovered."

        lines = ["## Available Workflows\n"]
        lines.append("Use `/vibey:<workflow-id>` commands or MCP tools.\n")

        # Group by type
        workflows_by_type: dict[str, List[WorkflowDefinition]] = {}
        for wf in workflows:
            wf_type = wf.type or "other"
            if wf_type not in workflows_by_type:
                workflows_by_type[wf_type] = []
            workflows_by_type[wf_type].append(wf)

        for wf_type in sorted(workflows_by_type.keys()):
            type_workflows = workflows_by_type[wf_type]
            lines.append(f"### {wf_type.title()} Workflows\n")

            for wf in sorted(type_workflows, key=lambda w: w.name):
                lines.append(f"**{wf.name}** (`{wf.id}`)")
                if wf.description:
                    lines.append(f": {wf.description}")
                if wf.duration:
                    lines.append(f"- Duration: {wf.duration}")
                if wf.steps:
                    lines.append(f"- Steps: {len(wf.steps)}")
                lines.append(f"- Command: `/vibey:{wf.id}`")
                lines.append("")

        return "\n".join(lines)

    def _build_mcp_section(
        self,
        agents: List[AgentDefinition],
        workflows: List[WorkflowDefinition],
    ) -> str:
        """Build MCP usage instructions."""
        lines = [
            "## MCP Integration\n",
            "Vibey exposes tools via Model Context Protocol (MCP).",
            "Use `/mcp` to see available servers and tools.\n",
            "### Tool Naming Convention\n",
            "- Agent tools: `vibey_<agent_id>` (e.g., `vibey_test_engineer`)",
            "- Workflow tools: `vibey_workflow_<workflow_id>`",
            "- Roadmap tools: `vibey_roadmap_status`, `vibey_query_task`, etc.\n",
            "### Example Usage\n",
            "```",
            "# Invoke the test engineer agent",
            "Use the vibey_test_engineer tool to write tests for src/utils.py",
            "",
            "# Start a workflow",
            "Use vibey_workflow_single_feature_development for the new auth feature",
            "",
            "# Check roadmap status",
            "Use vibey_roadmap_status to see current sprint progress",
            "```",
        ]

        return "\n".join(lines)

    def _build_footer(self) -> str:
        """Build the footer with metadata."""
        timestamp = datetime.now(timezone.utc).isoformat()
        return f"""---

<!-- VIBEY_GEMINI_GENERATED -->
<!-- Generated: {timestamp} -->
<!-- Do not edit manually - regenerate with: vibey export gemini -->
*Generated by Vibey Agent Framework for Gemini Code Assist*"""

    def _calculate_checksum(self, content: str) -> str:
        """Calculate SHA256 checksum for drift detection."""
        # Remove timestamp line for stable checksum
        lines = content.split("\n")
        stable_lines = [
            line for line in lines
            if not line.startswith("<!-- Generated:")
        ]
        stable_content = "\n".join(stable_lines)
        return hashlib.sha256(stable_content.encode()).hexdigest()[:16]

    def write_to_file(
        self,
        output_path: Path,
        include_workflows: bool = True,
        include_mcp_instructions: bool = True,
    ) -> GeneratedContext:
        """
        Generate and write GEMINI.md to file.

        Args:
            output_path: Where to write the file
            include_workflows: Include workflow documentation
            include_mcp_instructions: Include MCP instructions

        Returns:
            GeneratedContext with metadata
        """
        result = self.generate(include_workflows, include_mcp_instructions)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result.content, encoding='utf-8')
        logger.info(
            f"Generated GEMINI.md: {result.agents_count} agents, "
            f"{result.workflows_count} workflows (checksum: {result.checksum})"
        )
        return result
