"""
Amazon Q Developer Platform Adapter.

Exports Vibey framework to Amazon Q Developer configuration format.
Works with Amazon Q CLI and IDE plugins (VS Code, JetBrains).

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
from framework.mcp.discovery.agents import AgentDiscovery
from framework.mcp.discovery.workflows import WorkflowDiscovery

logger = logging.getLogger(__name__)


@dataclass
class AmazonQExportResult:
    """Result of Amazon Q export."""
    success: bool
    output_dir: Path
    files_created: List[Path] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    checksums: Dict[str, str] = field(default_factory=dict)
    agents_count: int = 0
    workflows_count: int = 0
    duration_seconds: float = 0.0


class AmazonQAdapter(PlatformAdapter):
    """
    Adapter for Amazon Q Developer platform.

    Exports Vibey framework to Amazon Q configuration format:
    - .amazonq/mcp.json (MCP server configuration)
    - AMAZONQ.md context file

    Amazon Q Developer has full MCP support (GA April 2025):
    - CLI: GA April 2025
    - IDE plugins (VS Code, JetBrains): GA June 2025
    - Admin controls: August 2025

    Example:
        >>> adapter = AmazonQAdapter(Path("/path/to/vibey"))
        >>> result = adapter.export(Path("./.amazonq"))
    """

    def __init__(self, vibey_root: Optional[Path] = None):
        """Initialize Amazon Q adapter."""
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
        return "amazonq"

    def get_deployment_dir(self, project_root: Optional[Path] = None) -> Path:
        if project_root is None:
            project_root = Path.cwd()
        return project_root / ".amazonq"

    def export(
        self,
        output_dir: Path,
        mcp_server_command: str = "python",
        mcp_server_args: Optional[List[str]] = None,
    ) -> AmazonQExportResult:
        """
        Export Amazon Q configuration package.

        Args:
            output_dir: Directory to write configuration (.amazonq/)
            mcp_server_command: Python command for MCP server
            mcp_server_args: Args for MCP server

        Returns:
            AmazonQExportResult with metadata
        """
        if mcp_server_args is None:
            mcp_server_args = ["-m", "framework.mcp.server"]

        start_time = datetime.now(timezone.utc)
        result = AmazonQExportResult(success=False, output_dir=output_dir)

        try:
            output_dir.mkdir(parents=True, exist_ok=True)

            # Discover agents/workflows
            if self._agent_discovery is None:
                self._init_generators()
            agents = self._agent_discovery.discover()
            workflows = self._workflow_discovery.discover()
            result.agents_count = len(agents)
            result.workflows_count = len(workflows)

            # 1. Generate mcp.json (Amazon Q format)
            logger.info("Generating mcp.json...")
            config = self._build_mcp_config(mcp_server_command, mcp_server_args)
            config_path = output_dir / "mcp.json"
            config_content = json.dumps(config, indent=2)
            config_path.write_text(config_content, encoding='utf-8')
            result.files_created.append(config_path)
            result.checksums["mcp.json"] = hashlib.sha256(
                config_content.encode()
            ).hexdigest()[:16]

            # 2. Generate AMAZONQ.md context file
            logger.info("Generating AMAZONQ.md...")
            context_content = self._build_context(agents, workflows)
            context_path = output_dir / "AMAZONQ.md"
            context_path.write_text(context_content, encoding='utf-8')
            result.files_created.append(context_path)

            # 3. Generate README
            readme_path = self._generate_readme(output_dir, result)
            result.files_created.append(readme_path)

            # 4. Write checksums manifest
            self._write_checksums_manifest(output_dir, result.checksums)
            result.files_created.append(output_dir / ".checksums.json")

            result.success = True
            logger.info(f"Amazon Q export complete: {len(result.files_created)} files")

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
        """Build MCP config in Amazon Q format."""
        # Amazon Q uses mcpServers format similar to Claude Desktop
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
        """Build AMAZONQ.md context content."""
        timestamp = datetime.now(timezone.utc).isoformat()
        lines = [
            "# Vibey Agent Framework",
            "",
            "This project uses the **Vibey Agent Framework** for intelligent workflow management.",
            "",
            "## Amazon Q Developer Integration",
            "",
            "The Vibey MCP server is configured in `.amazonq/mcp.json`.",
            "Amazon Q will automatically discover and connect to it.",
            "",
            "## Supported Interfaces",
            "",
            "- **Amazon Q CLI** - Command-line interface",
            "- **VS Code Extension** - Amazon Q for VS Code",
            "- **JetBrains Plugin** - Amazon Q for JetBrains IDEs",
            "- **AWS Console** - Amazon Q in AWS Console",
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
            "## AWS Integration",
            "",
            "Amazon Q integrates with AWS services:",
            "- **IAM** - Identity and access management",
            "- **AWS SSO** - Single sign-on",
            "- **CloudWatch** - Logging and monitoring",
            "- **CodeWhisperer** - Code suggestions",
            "",
            "## Usage",
            "",
            "### CLI",
            "```bash",
            "q chat \"Use vibey_roadmap_status to check project progress\"",
            "```",
            "",
            "### IDE",
            "1. Open Amazon Q panel",
            "2. Ask about Vibey tools",
            "3. Use tools directly in conversation",
            "",
            "---",
            f"<!-- Generated: {timestamp} -->",
            "<!-- Generator: vibey-amazonq-adapter -->",
        ])

        return "\n".join(lines)

    def _generate_readme(self, output_dir: Path, result: AmazonQExportResult) -> Path:
        """Generate README.md."""
        content = f"""# Vibey Framework for Amazon Q Developer

## Installation

The `mcp.json` file is in the `.amazonq/` directory.
Amazon Q will automatically detect the Vibey MCP server.

## Requirements

- Amazon Q Developer subscription
- AWS credentials configured
- Python 3.9+
- Vibey framework installed

## Supported Interfaces

- **Amazon Q CLI** (`q` command)
- **VS Code Extension** (Amazon Q for VS Code)
- **JetBrains Plugin** (Amazon Q for JetBrains)
- **AWS Console** (Amazon Q in browser)

## AWS Authentication

Amazon Q uses AWS credentials. Ensure you have:

```bash
# Configure AWS credentials
aws configure

# Or use AWS SSO
aws sso login
```

## Usage

### CLI
```bash
q chat "What Vibey tools are available?"
q chat "Use vibey_roadmap_status to check progress"
```

### IDE
1. Install Amazon Q extension/plugin
2. Sign in with AWS credentials
3. Open Amazon Q panel
4. Use Vibey tools in conversation

## Statistics

- **Agents**: {result.agents_count}
- **Workflows**: {result.workflows_count}

## Enterprise Features

Amazon Q supports enterprise controls:
- IAM policies for MCP access
- Admin controls (August 2025+)
- Audit logging via CloudWatch

## Regenerate

```bash
vibey deploy --platform amazonq
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
            "generator": "vibey-amazonq-adapter",
            "platform": "amazonq",
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
        required = ["mcp.json", "AMAZONQ.md"]
        for f in required:
            if not (deployment_dir / f).exists():
                errors.append(f"Missing: {f}")
        return len(errors) == 0, errors

    def get_required_files(self) -> List[str]:
        return ["mcp.json", "AMAZONQ.md"]

    def supports_feature(self, feature: str) -> bool:
        return feature in {"agents", "workflows", "mcp", "roadmap", "aws"}
