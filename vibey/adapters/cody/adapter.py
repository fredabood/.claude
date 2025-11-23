"""
Sourcegraph Cody Platform Adapter.

Exports Vibey framework to Cody configuration format.
Works with Cody's MCP support via OpenCtx.

Zero-Drift Architecture:
- All artifacts generated from frontmatter (single source of truth)
- Checksums embedded for drift detection

Note: Cody Free/Pro tiers sunset July 2025.
This adapter targets Cody Enterprise.
"""

import json
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Any, Dict

from vibey.adapters.base import PlatformAdapter, DeploymentResult
from framework.mcp.discovery.agents import AgentDiscovery
from framework.mcp.discovery.workflows import WorkflowDiscovery

logger = logging.getLogger(__name__)


@dataclass
class CodyExportResult:
    """Result of Cody export."""
    success: bool
    output_dir: Path
    files_created: List[Path] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    checksums: Dict[str, str] = field(default_factory=dict)
    agents_count: int = 0
    workflows_count: int = 0
    duration_seconds: float = 0.0


class CodyAdapter(PlatformAdapter):
    """
    Adapter for Sourcegraph Cody platform.

    Exports Vibey framework to Cody configuration format:
    - .cody/mcp.json (MCP server configuration via OpenCtx)
    - CODY.md context file

    Cody has native MCP support via OpenCtx:
    - VS Code extension
    - JetBrains plugin
    - Sourcegraph Enterprise integration

    Example:
        >>> adapter = CodyAdapter(Path("/path/to/vibey"))
        >>> result = adapter.export(Path("./.cody"))
    """

    def __init__(self, vibey_root: Optional[Path] = None):
        """Initialize Cody adapter."""
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
        return "cody"

    def get_deployment_dir(self, project_root: Optional[Path] = None) -> Path:
        if project_root is None:
            project_root = Path.cwd()
        return project_root / ".cody"

    def export(
        self,
        output_dir: Path,
        mcp_server_command: str = "python",
        mcp_server_args: Optional[List[str]] = None,
    ) -> CodyExportResult:
        """
        Export Cody configuration package.

        Args:
            output_dir: Directory to write configuration (.cody/)
            mcp_server_command: Python command for MCP server
            mcp_server_args: Args for MCP server

        Returns:
            CodyExportResult with metadata
        """
        if mcp_server_args is None:
            mcp_server_args = ["-m", "framework.mcp.server"]

        start_time = datetime.now(timezone.utc)
        result = CodyExportResult(success=False, output_dir=output_dir)

        try:
            output_dir.mkdir(parents=True, exist_ok=True)

            # Discover agents/workflows
            if self._agent_discovery is None:
                self._init_generators()
            agents = self._agent_discovery.discover()
            workflows = self._workflow_discovery.discover()
            result.agents_count = len(agents)
            result.workflows_count = len(workflows)

            # 1. Generate MCP config (Cody/OpenCtx format)
            logger.info("Generating mcp.json...")
            config = self._build_mcp_config(mcp_server_command, mcp_server_args)
            config_path = output_dir / "mcp.json"
            config_content = json.dumps(config, indent=2)
            config_path.write_text(config_content, encoding='utf-8')
            result.files_created.append(config_path)
            result.checksums["mcp.json"] = hashlib.sha256(
                config_content.encode()
            ).hexdigest()[:16]

            # 2. Generate CODY.md context file
            logger.info("Generating CODY.md...")
            context_content = self._build_context(agents, workflows)
            context_path = output_dir / "CODY.md"
            context_path.write_text(context_content, encoding='utf-8')
            result.files_created.append(context_path)

            # 3. Generate README
            readme_path = self._generate_readme(output_dir, result)
            result.files_created.append(readme_path)

            # 4. Write checksums manifest
            self._write_checksums_manifest(output_dir, result.checksums)
            result.files_created.append(output_dir / ".checksums.json")

            result.success = True
            logger.info(f"Cody export complete: {len(result.files_created)} files")

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
        """Build MCP config in Cody/OpenCtx format."""
        # Cody uses mcpServers format via OpenCtx
        return {
            "mcpServers": {
                "vibey": {
                    "command": command,
                    "args": args,
                    "env": {},
                }
            }
        }

    def _build_context(self, agents: list, workflows: list) -> str:
        """Build CODY.md context content."""
        timestamp = datetime.now(timezone.utc).isoformat()
        lines = [
            "# Vibey Agent Framework",
            "",
            "This project uses the **Vibey Agent Framework** for intelligent workflow management.",
            "",
            "## Sourcegraph Cody Integration",
            "",
            "The Vibey MCP server is configured in `.cody/mcp.json`.",
            "Cody connects via OpenCtx for MCP support.",
            "",
            "## Supported Interfaces",
            "",
            "- **VS Code Extension** - Cody for VS Code",
            "- **JetBrains Plugin** - Cody for JetBrains IDEs",
            "- **Sourcegraph Web** - Enterprise web interface",
            "",
            "## Enterprise Features",
            "",
            "Cody Enterprise provides:",
            "- **Code Graph** - Cross-repository understanding",
            "- **Context Search** - Semantic code search",
            "- **Prompt Library** - Shared prompt templates",
            "- **Admin Controls** - Organization governance",
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
            "## Usage",
            "",
            "### VS Code / JetBrains",
            "1. Open Cody panel",
            "2. Ask about Vibey tools",
            "3. Use tools in conversation",
            "",
            "### Context Mentions",
            "Use @-mentions to add context:",
            "- `@file:path/to/file` - Include file",
            "- `@symbol:functionName` - Include symbol",
            "",
            "## OpenCtx Integration",
            "",
            "Cody uses OpenCtx for MCP server connections.",
            "The configuration in `.cody/mcp.json` is automatically detected.",
            "",
            "---",
            f"<!-- Generated: {timestamp} -->",
            "<!-- Generator: vibey-cody-adapter -->",
        ])

        return "\n".join(lines)

    def _generate_readme(self, output_dir: Path, result: CodyExportResult) -> Path:
        """Generate README.md."""
        content = f"""# Vibey Framework for Sourcegraph Cody

## Installation

The `.cody/mcp.json` file configures the Vibey MCP server.
Cody will automatically detect and connect via OpenCtx.

## Requirements

- Cody Enterprise subscription
- VS Code or JetBrains IDE with Cody extension
- Python 3.9+
- Vibey framework installed

## Configuration

MCP config is in `.cody/mcp.json`:

```json
{{
  "mcpServers": {{
    "vibey": {{
      "command": "python",
      "args": ["-m", "framework.mcp.server"]
    }}
  }}
}}
```

## Usage

### VS Code
1. Install Cody extension
2. Sign in with Sourcegraph account
3. Open Cody panel
4. Use Vibey tools in conversation

### JetBrains
1. Install Cody plugin
2. Sign in with Sourcegraph account
3. Open Cody tool window
4. Use Vibey tools in conversation

## Statistics

- **Agents**: {result.agents_count}
- **Workflows**: {result.workflows_count}

## Enterprise Features

Cody Enterprise provides additional capabilities:
- **Code Graph**: Cross-repository context
- **Semantic Search**: Find code by meaning
- **Prompt Library**: Shared templates
- **Audit Logging**: Enterprise compliance

## Important Note

Cody Free and Pro tiers sunset July 23, 2025.
This integration targets Cody Enterprise.

## Regenerate

```bash
vibey deploy --platform cody
```

## Learn More

- [Cody Documentation](https://sourcegraph.com/docs/cody)
- [OpenCtx MCP Support](https://sourcegraph.com/docs/cody/capabilities/openctx)
"""
        readme_path = output_dir / "README.md"
        readme_path.write_text(content, encoding='utf-8')
        return readme_path

    def _write_checksums_manifest(self, output_dir: Path, checksums: Dict[str, str]) -> None:
        """Write checksums manifest."""
        manifest = {
            "version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generator": "vibey-cody-adapter",
            "platform": "cody",
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
        required = ["mcp.json", "CODY.md"]
        for f in required:
            if not (deployment_dir / f).exists():
                errors.append(f"Missing: {f}")
        return len(errors) == 0, errors

    def get_required_files(self) -> List[str]:
        return ["mcp.json", "CODY.md"]

    def supports_feature(self, feature: str) -> bool:
        return feature in {"agents", "workflows", "mcp", "roadmap", "enterprise", "openctx"}
