"""
GitHub Copilot Platform Adapter.

Exports Vibey framework to GitHub Copilot's configuration format.
Copilot supports custom agents via .github/agents/ and MCP via CLI.

Zero-Drift Architecture:
- All artifacts generated from frontmatter (single source of truth)
- Checksums embedded for drift detection
"""

import json
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Any, Dict

from vibey.adapters.base import PlatformAdapter, DeploymentResult
from vibey.mcp.discovery.agents import AgentDiscovery
from vibey.mcp.discovery.workflows import WorkflowDiscovery

logger = logging.getLogger(__name__)


@dataclass
class CopilotExportResult:
    """Result of Copilot export."""
    success: bool
    output_dir: Path
    files_created: List[Path] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    checksums: Dict[str, str] = field(default_factory=dict)
    agents_count: int = 0
    workflows_count: int = 0
    duration_seconds: float = 0.0


class CopilotAdapter(PlatformAdapter):
    """
    Adapter for GitHub Copilot platform.

    Exports Vibey framework to Copilot's configuration format:
    - .github/copilot-instructions.md (repository instructions)
    - .github/agents/*.md (custom agent profiles)
    - COPILOT.md context file

    GitHub Copilot supports:
    - Custom instructions per repository
    - Custom agent profiles (.github/agents/)
    - MCP via Copilot CLI and VS Code integration

    Example:
        >>> adapter = CopilotAdapter(Path("/path/to/vibey"))
        >>> result = adapter.export(Path("./.github"))
    """

    def __init__(self, vibey_root: Optional[Path] = None):
        """Initialize Copilot adapter."""
        self._vibey_root = Path(vibey_root) if vibey_root else None
        self._agent_discovery: Optional[AgentDiscovery] = None
        self._workflow_discovery: Optional[WorkflowDiscovery] = None

        if self._vibey_root:
            self._init_generators()

    def _init_generators(self, root: Optional[Path] = None) -> None:
        """Initialize discovery components."""
        if root:
            self._vibey_root = Path(root)
        if self._vibey_root:
            self._agent_discovery = AgentDiscovery(self._vibey_root)
            self._workflow_discovery = WorkflowDiscovery(self._vibey_root)

    @property
    def vibey_root(self) -> Path:
        if self._vibey_root is None:
            self._vibey_root = Path.cwd()
        return self._vibey_root

    def get_platform_name(self) -> str:
        return "copilot"

    def get_deployment_dir(self, project_root: Optional[Path] = None) -> Path:
        if project_root is None:
            project_root = Path.cwd()
        return project_root / ".github"

    def export(
        self,
        output_dir: Path,
        mcp_server_command: str = "python",
        mcp_server_args: Optional[List[str]] = None,
    ) -> CopilotExportResult:
        """
        Export Copilot configuration package.

        Args:
            output_dir: Directory to write configuration (.github/)
            mcp_server_command: Python command for MCP server
            mcp_server_args: Args for MCP server

        Returns:
            CopilotExportResult with metadata
        """
        if mcp_server_args is None:
            mcp_server_args = ["-m", "vibey.mcp.server"]

        start_time = datetime.now(timezone.utc)
        result = CopilotExportResult(success=False, output_dir=output_dir)

        try:
            output_dir.mkdir(parents=True, exist_ok=True)

            # Discover agents/workflows
            if self._agent_discovery is None:
                self._init_generators()
            agents = self._agent_discovery.discover()
            workflows = self._workflow_discovery.discover()
            result.agents_count = len(agents)
            result.workflows_count = len(workflows)

            # 1. Generate copilot-instructions.md
            logger.info("Generating copilot-instructions.md...")
            instructions = self._build_instructions(agents, workflows)
            instructions_path = output_dir / "copilot-instructions.md"
            instructions_path.write_text(instructions, encoding='utf-8')
            result.files_created.append(instructions_path)
            result.checksums["copilot-instructions.md"] = hashlib.sha256(
                instructions.encode()
            ).hexdigest()[:16]

            # 2. Generate custom agents in .github/agents/
            agents_dir = output_dir / "agents"
            agents_dir.mkdir(exist_ok=True)
            logger.info("Generating custom agent profiles...")
            for agent in agents:
                agent_content = self._build_agent_profile(agent)
                agent_filename = f"{agent.id}.md"
                agent_path = agents_dir / agent_filename
                agent_path.write_text(agent_content, encoding='utf-8')
                result.files_created.append(agent_path)

            # 3. Generate COPILOT.md context file
            logger.info("Generating COPILOT.md...")
            context_content = self._build_context(agents, workflows)
            context_path = output_dir / "COPILOT.md"
            context_path.write_text(context_content, encoding='utf-8')
            result.files_created.append(context_path)

            # 4. Generate README
            readme_path = self._generate_readme(output_dir, result)
            result.files_created.append(readme_path)

            # 5. Write checksums manifest
            self._write_checksums_manifest(output_dir, result.checksums)
            result.files_created.append(output_dir / ".checksums.json")

            result.success = True
            logger.info(f"Copilot export complete: {len(result.files_created)} files")

        except Exception as e:
            logger.error(f"Export failed: {e}")
            result.errors.append(str(e))

        result.duration_seconds = (
            datetime.now(timezone.utc) - start_time
        ).total_seconds()

        return result

    def _build_instructions(self, agents: list, workflows: list) -> str:
        """Build copilot-instructions.md content."""
        lines = [
            "# Vibey Agent Framework Instructions",
            "",
            "This repository uses the **Vibey Agent Framework** for intelligent workflow management.",
            "",
            "## Framework Overview",
            "",
            "Vibey provides:",
            f"- **{len(agents)} specialized agents** for different development tasks",
            f"- **{len(workflows)} structured workflows** for multi-step processes",
            "- **46 MCP tools** for roadmap and task management",
            "- **Quality gates** for code review and security",
            "",
            "## Available Agents",
            "",
        ]

        for agent in agents:
            desc = agent.description or f"{agent.name} agent"
            lines.append(f"- **{agent.name}**: {desc}")

        lines.extend([
            "",
            "## MCP Tools",
            "",
            "When using Copilot CLI or VS Code with MCP enabled, you have access to:",
            "",
            "### Roadmap Management",
            "- `vibey_roadmap_status` - Get overall roadmap status",
            "- `vibey_start_task` / `vibey_complete_task` - Track task progress",
            "- `vibey_query_task` - Get detailed task information",
            "",
            "### Agent Invocation",
        ])

        for agent in agents[:5]:  # Top 5 agents
            tool_name = agent.id.replace('-', '_')
            lines.append(f"- `vibey_{tool_name}` - {agent.name}")

        lines.extend([
            "",
            "## Best Practices",
            "",
            "1. Check roadmap status before starting new work",
            "2. Use appropriate agent for the task domain",
            "3. Follow structured workflows for complex tasks",
            "4. Update task status as you progress",
            "",
            "---",
            "<!-- Generated by Vibey Framework -->",
        ])

        return "\n".join(lines)

    def _build_agent_profile(self, agent) -> str:
        """Build a custom agent profile for .github/agents/."""
        tool_name = agent.id.replace('-', '_')
        desc = agent.description or f"Specialized {agent.name} agent"

        lines = [
            f"# {agent.name}",
            "",
            f"{desc}",
            "",
            "## Capabilities",
            "",
        ]

        # Add triggers as capabilities if available
        if hasattr(agent, 'triggers') and agent.triggers:
            # triggers is a dict with 'keywords' list
            keywords = agent.triggers.get('keywords', []) if isinstance(agent.triggers, dict) else []
            for keyword in keywords[:5]:
                lines.append(f"- {keyword}")
            if not keywords:
                lines.append(f"- Specialized in {agent.name.lower()} tasks")
        else:
            lines.append(f"- Specialized in {agent.name.lower()} tasks")
            lines.append("- Follows Vibey framework best practices")
            lines.append("- Integrates with roadmap management")

        lines.extend([
            "",
            "## MCP Tool",
            "",
            f"Invoke via MCP: `vibey_{tool_name}`",
            "",
            "## Usage",
            "",
            f"Use this agent for {agent.name.lower()}-related tasks.",
            "The agent follows structured workflows and quality gates.",
            "",
            "---",
            "<!-- Generated by Vibey Framework -->",
        ])

        return "\n".join(lines)

    def _build_context(self, agents: list, workflows: list) -> str:
        """Build COPILOT.md context content."""
        timestamp = datetime.now(timezone.utc).isoformat()
        lines = [
            "# Vibey Agent Framework",
            "",
            "This project uses the **Vibey Agent Framework** for intelligent workflow management.",
            "",
            "## Copilot Integration",
            "",
            "- Repository instructions: `.github/copilot-instructions.md`",
            "- Custom agents: `.github/agents/*.md`",
            "- MCP integration available via Copilot CLI",
            "",
            "## Available Agents",
            "",
        ]

        for agent in agents:
            tool_name = agent.id.replace('-', '_')
            lines.append(f"- **{agent.name}**: `vibey_{tool_name}`")

        lines.extend(["", "## Available Workflows", ""])

        for workflow in workflows:
            tool_name = workflow.id.replace('-', '_')
            lines.append(f"- **{workflow.name}**: `vibey_workflow_{tool_name}`")

        lines.extend([
            "",
            "## MCP Tools (46 total)",
            "",
            "### Roadmap Tools",
            "- `vibey_roadmap_status` - Get overall roadmap status",
            "- `vibey_start_task` / `vibey_complete_task` - Manage tasks",
            "- `vibey_start_sprint` / `vibey_complete_sprint` - Manage sprints",
            "",
            "---",
            f"<!-- Generated: {timestamp} -->",
            "<!-- Generator: vibey-copilot-adapter -->",
        ])

        return "\n".join(lines)

    def _generate_readme(self, output_dir: Path, result: CopilotExportResult) -> Path:
        """Generate README.md."""
        content = f"""# Vibey Framework for GitHub Copilot

## Installation

The configuration files are in the `.github/` directory:
- `copilot-instructions.md` - Repository-level instructions
- `agents/*.md` - Custom agent profiles
- `COPILOT.md` - Context file

## Requirements

- GitHub Copilot (individual or enterprise)
- VS Code with Copilot extension
- Optional: Copilot CLI for MCP support

## Usage

1. Copilot automatically reads `.github/copilot-instructions.md`
2. Custom agents are available in Copilot Chat
3. Use MCP tools via Copilot CLI for advanced integration

## Statistics

- **Agents**: {result.agents_count}
- **Workflows**: {result.workflows_count}
- **Agent Profiles Generated**: {result.agents_count}

## Regenerate

```bash
vibey deploy --platform copilot
```
"""
        readme_path = output_dir / "COPILOT_README.md"
        readme_path.write_text(content, encoding='utf-8')
        return readme_path

    def _write_checksums_manifest(self, output_dir: Path, checksums: Dict[str, str]) -> None:
        """Write checksums manifest."""
        manifest = {
            "version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generator": "vibey-copilot-adapter",
            "platform": "copilot",
            "checksums": checksums,
        }
        (output_dir / ".checksums.json").write_text(
            json.dumps(manifest, indent=2), encoding='utf-8'
        )

    # PlatformAdapter interface

    def deploy(
        self,
        source_dir: Path,
        config: Any,
        target_dir: Optional[Path] = None,
        clean: bool = False,
    ) -> DeploymentResult:
        project_root = source_dir.parent
        if self._vibey_root is None or self._vibey_root != project_root:
            self._init_generators(project_root)

        if target_dir is None:
            target_dir = self.get_deployment_dir(project_root)

        start_time = datetime.now()

        if clean and target_dir.exists():
            import shutil
            shutil.rmtree(target_dir)

        export_result = self.export(target_dir)

        return DeploymentResult(
            success=export_result.success,
            platform=self.get_platform_name(),
            target_dir=target_dir,
            files_created=export_result.files_created,
            errors=export_result.errors,
            duration_seconds=(datetime.now() - start_time).total_seconds(),
        )

    def generate_context_file(self, config: Any, output_path: Path) -> None:
        if self._agent_discovery is None:
            self._init_generators()
        agents = self._agent_discovery.discover()
        workflows = self._workflow_discovery.discover()
        content = self._build_context(agents, workflows)
        output_path.write_text(content, encoding='utf-8')

    def validate_deployment(self, deployment_dir: Path) -> tuple[bool, List[str]]:
        errors = []
        required = ["copilot-instructions.md", "COPILOT.md"]
        for f in required:
            if not (deployment_dir / f).exists():
                errors.append(f"Missing: {f}")
        # Check agents directory
        if not (deployment_dir / "agents").exists():
            errors.append("Missing: agents/ directory")
        return len(errors) == 0, errors

    def get_required_files(self) -> List[str]:
        return ["copilot-instructions.md", "COPILOT.md", "agents/"]

    def supports_feature(self, feature: str) -> bool:
        return feature in {"agents", "workflows", "mcp", "roadmap", "instructions"}
