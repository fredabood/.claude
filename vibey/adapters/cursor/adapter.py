"""
Cursor Platform Adapter.

Exports Vibey framework to Cursor's configuration format.
Cursor uses the same MCP config schema as Claude Desktop.

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
class CursorExportResult:
    """Result of Cursor export."""
    success: bool
    output_dir: Path
    files_created: List[Path] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    checksums: Dict[str, str] = field(default_factory=dict)
    agents_count: int = 0
    workflows_count: int = 0
    duration_seconds: float = 0.0


class CursorAdapter(PlatformAdapter):
    """
    Adapter for Cursor IDE platform.

    Exports Vibey framework to Cursor's configuration format:
    - .cursor/mcp.json (MCP server configuration)
    - .cursorrules (project-specific AI rules)
    - CURSOR.md context file

    Cursor has native MCP support (since Nov 2024) with the same config
    schema as Claude Desktop.

    Example:
        >>> adapter = CursorAdapter(Path("/path/to/vibey"))
        >>> result = adapter.export(Path("./.cursor"))
    """

    def __init__(self, vibey_root: Optional[Path] = None):
        """Initialize Cursor adapter."""
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
        return "cursor"

    def get_deployment_dir(self, project_root: Optional[Path] = None) -> Path:
        if project_root is None:
            project_root = Path.cwd()
        return project_root / ".cursor"

    def export(
        self,
        output_dir: Path,
        mcp_server_command: str = "python",
        mcp_server_args: Optional[List[str]] = None,
    ) -> CursorExportResult:
        """
        Export Cursor configuration package.

        Args:
            output_dir: Directory to write configuration (.cursor/)
            mcp_server_command: Python command for MCP server
            mcp_server_args: Args for MCP server

        Returns:
            CursorExportResult with metadata
        """
        if mcp_server_args is None:
            mcp_server_args = ["-m", "vibey.mcp.server"]

        start_time = datetime.now(timezone.utc)
        result = CursorExportResult(success=False, output_dir=output_dir)

        try:
            output_dir.mkdir(parents=True, exist_ok=True)

            # Discover agents/workflows
            if self._agent_discovery is None:
                self._init_generators()
            agents = self._agent_discovery.discover()
            workflows = self._workflow_discovery.discover()
            result.agents_count = len(agents)
            result.workflows_count = len(workflows)

            # 1. Generate mcp.json (Claude Desktop format)
            logger.info("Generating mcp.json...")
            config = self._build_mcp_config(mcp_server_command, mcp_server_args)
            config_path = output_dir / "mcp.json"
            config_content = json.dumps(config, indent=2)
            config_path.write_text(config_content, encoding='utf-8')
            result.files_created.append(config_path)
            result.checksums["mcp.json"] = hashlib.sha256(
                config_content.encode()
            ).hexdigest()[:16]

            # 2. Generate .cursorrules (project rules from frontmatter)
            logger.info("Generating .cursorrules...")
            rules_content = self._build_cursorrules(agents, workflows)
            # .cursorrules goes in project root, not .cursor/
            rules_path = output_dir.parent / ".cursorrules"
            rules_path.write_text(rules_content, encoding='utf-8')
            result.files_created.append(rules_path)
            result.checksums[".cursorrules"] = hashlib.sha256(
                rules_content.encode()
            ).hexdigest()[:16]

            # 3. Generate CURSOR.md context file
            logger.info("Generating CURSOR.md...")
            context_content = self._build_context(agents, workflows)
            context_path = output_dir / "CURSOR.md"
            context_path.write_text(context_content, encoding='utf-8')
            result.files_created.append(context_path)

            # 4. Generate README
            readme_path = self._generate_readme(output_dir, result)
            result.files_created.append(readme_path)

            # 5. Write checksums manifest
            self._write_checksums_manifest(output_dir, result.checksums)
            result.files_created.append(output_dir / ".checksums.json")

            result.success = True
            logger.info(f"Cursor export complete: {len(result.files_created)} files")

        except Exception as e:
            logger.error(f"Export failed: {e}")
            result.errors.append(str(e))

        result.duration_seconds = (
            datetime.now(timezone.utc) - start_time
        ).total_seconds()

        return result

    def _build_mcp_config(
        self,
        command: str,
        args: List[str],
    ) -> Dict[str, Any]:
        """Build MCP config in Claude Desktop format."""
        return {
            "mcpServers": {
                "vibey": {
                    "command": command,
                    "args": args,
                }
            }
        }

    def _build_cursorrules(self, agents: list, workflows: list) -> str:
        """Build .cursorrules content from frontmatter."""
        lines = [
            "# Vibey Agent Framework Rules",
            "",
            "This project uses the Vibey Agent Framework for intelligent workflow management.",
            "",
            "## MCP Tools",
            "",
            "Use Vibey MCP tools (prefixed with `vibey_`) for framework operations:",
            "- `vibey_roadmap_status` - Check roadmap progress",
            "- `vibey_start_task` / `vibey_complete_task` - Manage tasks",
            "- `vibey_start_sprint` / `vibey_complete_sprint` - Manage sprints",
            "",
            "## Available Agents",
            "",
        ]

        for agent in agents:
            tool_name = agent.id.replace('-', '_')
            lines.append(f"- `vibey_{tool_name}` - {agent.name}")

        lines.extend([
            "",
            "## Workflows",
            "",
        ])

        for workflow in workflows:
            tool_name = workflow.id.replace('-', '_')
            lines.append(f"- `vibey_workflow_{tool_name}` - {workflow.name}")

        lines.extend([
            "",
            "## Best Practices",
            "",
            "1. Use agent specialization - each agent has domain expertise",
            "2. Follow structured workflows for multi-step tasks",
            "3. Validate quality gates before marking tasks complete",
            "4. Reference roadmap status before starting new work",
            "",
            "<!-- Generated by Vibey Framework -->",
        ])

        return "\n".join(lines)

    def _build_context(self, agents: list, workflows: list) -> str:
        """Build CURSOR.md context content."""
        timestamp = datetime.now(timezone.utc).isoformat()
        lines = [
            "# Vibey Agent Framework",
            "",
            "This project uses the **Vibey Agent Framework** for intelligent workflow management.",
            "",
            "## MCP Integration",
            "",
            "The Vibey MCP server is configured in `.cursor/mcp.json`.",
            "Cursor will automatically discover and connect to it.",
            "",
            "## Available Tools",
            "",
            "### Roadmap Tools",
            "- `vibey_roadmap_status` - Get overall roadmap status",
            "- `vibey_start_task` / `vibey_complete_task` - Manage tasks",
            "- `vibey_start_sprint` / `vibey_complete_sprint` - Manage sprints",
            "- `vibey_query_task` / `vibey_query_sprint` / `vibey_query_track` - Query details",
            "",
            "### Agent Tools",
            "",
        ]

        for agent in agents:
            tool_name = agent.id.replace('-', '_')
            lines.append(f"- **{agent.name}**: `vibey_{tool_name}`")

        lines.extend(["", "### Workflow Tools", ""])

        for workflow in workflows:
            tool_name = workflow.id.replace('-', '_')
            lines.append(f"- **{workflow.name}**: `vibey_workflow_{tool_name}`")

        lines.extend([
            "",
            "---",
            f"<!-- Generated: {timestamp} -->",
            "<!-- Generator: vibey-cursor-adapter -->",
        ])

        return "\n".join(lines)

    def _generate_readme(self, output_dir: Path, result: CursorExportResult) -> Path:
        """Generate README.md."""
        content = f"""# Vibey Framework for Cursor

## Installation

The `mcp.json` file is already in the `.cursor/` directory.
Cursor will automatically detect and connect to the Vibey MCP server.

The `.cursorrules` file in your project root provides AI-specific guidelines.

## Requirements

- Cursor IDE (with MCP support, Nov 2024+)
- Python 3.9+
- Vibey framework installed

## Usage

1. Open this project in Cursor
2. The MCP server will start automatically
3. Use Composer to access Vibey tools

## Statistics

- **Agents**: {result.agents_count}
- **Workflows**: {result.workflows_count}

## Regenerate

```bash
vibey deploy --platform cursor
```
"""
        readme_path = output_dir / "README.md"
        readme_path.write_text(content, encoding='utf-8')
        return readme_path

    def _write_checksums_manifest(self, output_dir: Path, checksums: Dict[str, str]) -> None:
        """Write checksums manifest."""
        manifest = {
            "version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generator": "vibey-cursor-adapter",
            "platform": "cursor",
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
        required = ["mcp.json", "CURSOR.md"]
        for f in required:
            if not (deployment_dir / f).exists():
                errors.append(f"Missing: {f}")
        # Also check .cursorrules in parent
        if not (deployment_dir.parent / ".cursorrules").exists():
            errors.append("Missing: .cursorrules (in project root)")
        return len(errors) == 0, errors

    def get_required_files(self) -> List[str]:
        return ["mcp.json", "CURSOR.md", ".cursorrules"]

    def supports_feature(self, feature: str) -> bool:
        return feature in {"agents", "workflows", "mcp", "roadmap", "rules"}
