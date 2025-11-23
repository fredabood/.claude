"""
Claude Code platform adapter.

This adapter deploys Vibey to Claude Code's .claude/ directory format.
"""

import json
import sys
from pathlib import Path
from typing import Optional, List, Any
import shutil
from datetime import datetime

from vibey.adapters.base import PlatformAdapter, DeploymentResult


class ClaudeCodeAdapter(PlatformAdapter):
    """
    Adapter for Claude Code platform.

    Deploys Vibey framework to .claude/ directory with:
    - CLAUDE.md (context file)
    - project-config.yaml (legacy, for backward compat)
    - agents/ (custom agents)
    - workflows/ (custom workflows)
    - templates/ (templates)
    - commands/ (slash commands)
    """

    def get_platform_name(self) -> str:
        """Get platform name."""
        return "claude-code"

    def get_deployment_dir(self, project_root: Optional[Path] = None) -> Path:
        """Get deployment directory (.claude/)."""
        if project_root is None:
            project_root = Path.cwd()
        return project_root / ".claude"

    def deploy(
        self,
        source_dir: Path,
        config: Any,
        target_dir: Optional[Path] = None,
        clean: bool = False
    ) -> DeploymentResult:
        """
        Deploy to Claude Code.

        Deployment steps:
        1. Clean target directory if requested
        2. Create directory structure
        3. Generate CLAUDE.md context file
        4. Copy/generate platform-specific files
        5. Validate deployment

        Args:
            source_dir: .vibey/ directory
            config: Vibey configuration
            target_dir: .claude/ directory (or custom)
            clean: Remove existing deployment first

        Returns:
            DeploymentResult with status and details
        """
        start_time = datetime.now()

        if target_dir is None:
            target_dir = self.get_deployment_dir(source_dir.parent)

        result = DeploymentResult(
            success=False,
            platform=self.get_platform_name(),
            target_dir=target_dir,
        )

        try:
            # Pre-deployment hook
            self.pre_deploy_hook(source_dir, target_dir)

            # Step 1: Clean if requested
            if clean and target_dir.exists():
                shutil.rmtree(target_dir)
                result.files_deleted.append(target_dir)

            # Step 2: Create directory structure
            target_dir.mkdir(parents=True, exist_ok=True)

            # Step 3: Generate CLAUDE.md
            claude_md_path = target_dir / "CLAUDE.md"
            self.generate_context_file(config, claude_md_path)
            if claude_md_path.exists():
                result.files_created.append(claude_md_path)

            # Step 4: Copy framework components (if they exist in source)
            components = [
                ("agents", "agents"),
                ("workflows", "workflows"),
                ("templates", "templates"),
                ("commands", "commands"),
            ]

            for source_name, target_name in components:
                source_component = source_dir.parent / source_name
                if source_component.exists() and source_component.is_dir():
                    target_component = target_dir / target_name
                    if target_component.exists():
                        shutil.rmtree(target_component)
                    shutil.copytree(source_component, target_component)
                    result.files_created.append(target_component)

            # Step 5: Generate legacy project-config.yaml for backward compat
            # (Optional - only if using modular config)
            config_dir = source_dir / "config"
            if config_dir.exists():
                result.warnings.append(
                    "Modular config detected. Legacy project-config.yaml "
                    "generation not yet implemented."
                )

            # Step 6: Generate .mcp.json for MCP server integration
            project_root = source_dir.parent
            mcp_config_path = self.generate_mcp_config(project_root)
            if mcp_config_path.exists():
                result.files_created.append(mcp_config_path)

            # Step 7: Validate deployment
            is_valid, errors = self.validate_deployment(target_dir)
            result.validation_passed = is_valid
            result.errors.extend(errors)

            # Mark as success if no errors
            result.success = len(result.errors) == 0

            # Post-deployment hook
            self.post_deploy_hook(result)

        except Exception as e:
            result.success = False
            result.errors.append(f"Deployment failed: {e}")

        # Calculate duration
        result.duration_seconds = (datetime.now() - start_time).total_seconds()

        return result

    def generate_context_file(self, config: Any, output_path: Path) -> None:
        """
        Generate CLAUDE.md context file.

        Creates a comprehensive context file for Claude Code with:
        - Project information
        - Technology stack
        - Available agents
        - Orchestration mode
        - Framework version
        - Vibey framework marker

        Args:
            config: Vibey configuration
            output_path: Path to write CLAUDE.md
        """
        # Build CLAUDE.md content
        content = f"""# {config.project.project.name}

**Project Type:** {config.project.project.type.value}
**Version:** {config.project.project.version}

{config.project.project.description or 'AI-powered project using Vibey Agent Framework'}

---

## Tech Stack

**Languages:** {', '.join(config.project.tech_stack.languages)}
"""

        # Add frameworks if present
        if config.project.tech_stack.frameworks:
            content += f"**Frameworks:** {', '.join(config.project.tech_stack.frameworks)}\n"

        # Add databases if present
        if config.project.tech_stack.databases:
            content += f"**Databases:** {', '.join(config.project.tech_stack.databases)}\n"

        # Add infrastructure if present
        if config.project.tech_stack.infrastructure:
            content += f"**Infrastructure:** {', '.join(config.project.tech_stack.infrastructure)}\n"

        content += """
---

## Available Agents

This project uses the Vibey Agent Framework with the following specialized agents:

"""

        # List enabled agents
        for agent_id in config.agents.agents.enabled:
            # Convert ID to display name
            display_name = agent_id.replace('-', ' ').title()
            content += f"- **{display_name}** (`{agent_id}`)\n"

        content += f"""
---

## Orchestration Mode

**Current Mode:** {config.framework.framework.orchestration_mode.value}

"""

        # Add orchestration mode description
        mode_descriptions = {
            "simple": "Explicit agent selection via keywords",
            "balanced": "Smart pattern matching with recommendations",
            "tiered": "Intelligent coordinator-based routing"
        }

        mode = config.framework.framework.orchestration_mode.value
        if mode in mode_descriptions:
            content += f"*{mode_descriptions[mode]}*\n"

        content += """
---

<!-- VIBEY_FRAMEWORK_MANAGED -->
*Generated by Vibey Agent Framework for Claude Code*
"""

        # Write to file
        output_path.write_text(content)


    def validate_deployment(self, deployment_dir: Path) -> tuple[bool, List[str]]:
        """
        Validate Claude Code deployment.

        Checks:
        - Deployment directory exists
        - CLAUDE.md exists and has content
        - CLAUDE.md contains Vibey marker
        - Optional components are valid if present

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check deployment directory exists
        if not deployment_dir.exists():
            errors.append(f"Deployment directory does not exist: {deployment_dir}")
            return (False, errors)

        if not deployment_dir.is_dir():
            errors.append(f"Deployment path is not a directory: {deployment_dir}")
            return (False, errors)

        # Check CLAUDE.md exists
        claude_md = deployment_dir / "CLAUDE.md"
        if not claude_md.exists():
            errors.append(f"Missing required file: CLAUDE.md")
        else:
            # Check CLAUDE.md has content
            content = claude_md.read_text()
            if not content.strip():
                errors.append("CLAUDE.md is empty")

            # Check for Vibey marker
            if "VIBEY_FRAMEWORK_MANAGED" not in content:
                errors.append("CLAUDE.md missing Vibey framework marker")

        # Validate optional components if they exist
        optional_dirs = ["agents", "workflows", "templates", "commands"]
        for dir_name in optional_dirs:
            dir_path = deployment_dir / dir_name
            if dir_path.exists() and not dir_path.is_dir():
                errors.append(f"{dir_name} exists but is not a directory")

        return (len(errors) == 0, errors)

    def get_required_files(self) -> List[str]:
        """Required files for Claude Code."""
        return [
            "CLAUDE.md",
        ]

    def get_optional_files(self) -> List[str]:
        """Optional files for Claude Code."""
        return [
            "project-config.yaml",  # Legacy, optional in v2.5+
            "agents/",
            "workflows/",
            "templates/",
            "commands/",
        ]

    def supports_feature(self, feature: str) -> bool:
        """Check feature support."""
        # Claude Code supports all Vibey features
        supported = {
            "agents",
            "workflows",
            "quality-gates",
            "roadmap",
            "templates",
            "commands",
        }
        return feature in supported

    def generate_mcp_config(self, project_root: Path) -> Path:
        """
        Generate .mcp.json for Claude Code MCP server integration.

        Creates the MCP configuration file that tells Claude Code how to
        connect to the Vibey MCP server. This enables AI assistant integration
        with all Vibey tools (roadmap, agents, workflows).

        Args:
            project_root: Root directory of the project

        Returns:
            Path to the generated .mcp.json file
        """
        mcp_config = {
            "mcpServers": {
                "vibey": {
                    "command": sys.executable,
                    "args": ["-m", "vibey.mcp.server"],
                    "env": {
                        "VIBEY_PROJECT_ROOT": str(project_root)
                    }
                }
            }
        }

        config_path = project_root / ".mcp.json"
        config_path.write_text(json.dumps(mcp_config, indent=2))
        return config_path
