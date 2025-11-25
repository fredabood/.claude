"""
Aider platform adapter.

This adapter deploys Vibey to Aider's .aider/ directory format.

Aider is a CLI-based AI coding assistant with:
- aider.conf.yml - Configuration file
- System prompts for agent-like behavior
- Python API for workflow scripting
- Git integration for commits

Source of Truth Architecture:
All .aider/ files are GENERATED from vibey/content/ sources.
Never edit generated files - modify source and regenerate.
"""

from pathlib import Path
from typing import Optional, List, Any
import shutil
from datetime import datetime, timezone
import re

from vibey.adapters.base import PlatformAdapter, DeploymentResult
from vibey.content import get_agents_dir, get_workflows_dir


class AiderAdapter(PlatformAdapter):
    """
    Adapter for Aider platform.

    Deploys Vibey framework to .aider/ directory with:
    - aider.conf.yml (main configuration)
    - agents/ (system prompts converted from vibey/content/agents/)
    - workflows/ (Python scripts converted from vibey/content/workflows/)
    - hooks/ (git hooks for quality gates)
    - .generated (marker file with timestamp)

    Source of Truth:
    - vibey/content/agents/*.md → .aider/agents/*.md
    - vibey/content/workflows/*.md → .aider/workflows/*.py
    - .vibey/config/*.yaml → .aider/aider.conf.yml

    All output files are regenerated on each deploy() call.
    """

    def get_platform_name(self) -> str:
        """Get platform name."""
        return "aider"

    def get_deployment_dir(self, project_root: Optional[Path] = None) -> Path:
        """Get deployment directory (.aider/)."""
        if project_root is None:
            project_root = Path.cwd()
        return project_root / ".aider"

    def deploy(
        self,
        source_dir: Path,
        config: Any,
        target_dir: Optional[Path] = None,
        clean: bool = False
    ) -> DeploymentResult:
        """
        Deploy to Aider.

        Deployment steps:
        1. Clean target directory if requested
        2. Create directory structure
        3. Generate .generated marker file
        4. Generate aider.conf.yml configuration
        5. Convert agents → system prompts
        6. Convert workflows → Python scripts
        7. Generate git hooks
        8. Validate deployment

        Args:
            source_dir: .vibey/ directory
            config: Vibey configuration
            target_dir: .aider/ directory (or custom)
            clean: Remove existing deployment first

        Returns:
            DeploymentResult with status and details
        """
        start_time = datetime.now(timezone.utc)

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
            (target_dir / "agents").mkdir(exist_ok=True)
            (target_dir / "workflows").mkdir(exist_ok=True)
            (target_dir / "hooks").mkdir(exist_ok=True)

            # Step 3: Generate .generated marker file
            marker_path = target_dir / ".generated"
            self._write_generation_marker(marker_path)
            result.files_created.append(marker_path)

            # Step 4: Generate aider.conf.yml
            config_path = target_dir / "aider.conf.yml"
            self._generate_aider_config(config, config_path)
            result.files_created.append(config_path)

            # Step 5: Convert agents to system prompts
            content_agents = get_agents_dir()
            if content_agents.exists():
                agents_created = self._convert_agents(
                    content_agents,
                    target_dir / "agents"
                )
                result.files_created.extend(agents_created)

            # Step 6: Convert workflows to Python scripts
            content_workflows = get_workflows_dir()
            if content_workflows.exists():
                workflows_created = self._convert_workflows(
                    content_workflows,
                    target_dir / "workflows"
                )
                result.files_created.extend(workflows_created)

            # Step 7: Generate git hooks
            hooks_created = self._generate_hooks(target_dir / "hooks")
            result.files_created.extend(hooks_created)

            # Step 8: Validate deployment
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
        result.duration_seconds = (datetime.now(timezone.utc) - start_time).total_seconds()

        return result

    def _write_generation_marker(self, marker_path: Path) -> None:
        """Write the .generated marker file."""
        content = f"""# GENERATED FILE - DO NOT EDIT
#
# This directory was generated by Vibey Agent Framework.
# All files are regenerated on each deployment.
#
# To update these files:
#   1. Edit the source files in vibey/content/agents/ or vibey/content/workflows/
#   2. Run: vibey deploy --platform aider
#
# Generation timestamp: {datetime.now(timezone.utc).isoformat()}
# Generator: vibey deploy --platform aider
#
# Source of truth:
#   vibey/content/agents/*.md → .aider/agents/*.md
#   vibey/content/workflows/*.md → .aider/workflows/*.py
#   .vibey/config/*.yaml → .aider/aider.conf.yml
"""
        marker_path.write_text(content)

    def _generate_aider_config(self, config: Any, output_path: Path) -> None:
        """
        Generate aider.conf.yml from Vibey config.

        Args:
            config: Vibey configuration
            output_path: Path to write aider.conf.yml
        """
        # Build aider.conf.yml content
        content = f"""# Aider Configuration - Generated by Vibey
# DO NOT EDIT - Regenerate with: vibey deploy --platform aider
#
# Project: {config.project.project.name}
# Generated: {datetime.now(timezone.utc).isoformat()}

# Model Configuration
# Uncomment and set your preferred model
# model: claude-3-5-sonnet
# model: gpt-4o
# model: deepseek-chat

# API Keys (use environment variables)
# api-key: $ANTHROPIC_API_KEY
# api-key: $OPENAI_API_KEY

# Git Integration
auto-commits: true
attribute-author: true
attribute-committer: true

# Commit Message Template (with Vibey metadata)
commit-prompt: |
  Create a concise commit message for these changes.

  Format: <type>(<scope>): <description>

  Types: feat, fix, docs, style, refactor, test, chore

  Include [Vibey] tag if this was part of a workflow.

  Keep the first line under 72 characters.

# Repository Map
map-tokens: 1024
map-refresh: auto

# Editor Settings
edit-format: diff
auto-lint: true

# Chat Settings
chat-history-file: .aider/chat-history.md

# Vibey Framework Integration
# Use system prompts from .aider/agents/ for specialized behavior
# Run workflow scripts from .aider/workflows/ for multi-step tasks

# --- VIBEY_FRAMEWORK_MANAGED ---
"""
        output_path.write_text(content)

    def _convert_agents(self, agents_dir: Path, output_dir: Path) -> List[Path]:
        """
        Convert framework agents to Aider system prompts.

        Args:
            agents_dir: Source vibey/content/agents/ directory
            output_dir: Target .aider/agents/ directory

        Returns:
            List of created file paths
        """
        created_files = []
        output_dir.mkdir(parents=True, exist_ok=True)

        for agent_file in agents_dir.rglob("*.md"):
            # Skip README files
            if agent_file.name.lower() == "readme.md":
                continue

            # Read agent content
            agent_content = agent_file.read_text()

            # Extract agent name from file
            agent_id = agent_file.stem

            # Convert to Aider system prompt format
            prompt_content = self._convert_agent_to_prompt(agent_id, agent_content)

            # Write to output
            output_file = output_dir / f"{agent_id}.md"
            output_file.write_text(prompt_content)
            created_files.append(output_file)

        return created_files

    def _convert_agent_to_prompt(self, agent_id: str, content: str) -> str:
        """
        Convert a Vibey agent markdown to Aider system prompt.

        Args:
            agent_id: Agent identifier (e.g., "web-developer")
            content: Original agent markdown content

        Returns:
            Aider-formatted system prompt
        """
        # Extract title (first # heading)
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else agent_id.replace('-', ' ').title()

        # Extract description (first paragraph after title)
        desc_match = re.search(r'^#\s+.+\n\n(.+?)(?:\n\n|$)', content, re.MULTILINE | re.DOTALL)
        description = desc_match.group(1).strip() if desc_match else ""

        # Build Aider system prompt
        prompt = f"""# {title} - Aider System Prompt
# GENERATED - DO NOT EDIT
# Source: vibey/content/agents/*/{agent_id}.md
# Regenerate with: vibey deploy --platform aider

You are acting as a **{title}** in this coding session.

{description}

## Your Role

{content}

---
*System prompt generated by Vibey Agent Framework for Aider*
"""
        return prompt

    def _convert_workflows(self, workflows_dir: Path, output_dir: Path) -> List[Path]:
        """
        Convert framework workflows to Aider Python scripts.

        Args:
            workflows_dir: Source vibey/content/workflows/ directory
            output_dir: Target .aider/workflows/ directory

        Returns:
            List of created file paths
        """
        created_files = []
        output_dir.mkdir(parents=True, exist_ok=True)

        for workflow_file in workflows_dir.rglob("*.md"):
            # Skip README files
            if workflow_file.name.lower() == "readme.md":
                continue

            # Read workflow content
            workflow_content = workflow_file.read_text()

            # Convert to Python script
            workflow_id = workflow_file.stem.replace("-", "_")
            script_content = self._convert_workflow_to_script(workflow_id, workflow_content)

            # Write to output
            output_file = output_dir / f"{workflow_id}.py"
            output_file.write_text(script_content)
            created_files.append(output_file)

        return created_files

    def _convert_workflow_to_script(self, workflow_id: str, content: str) -> str:
        """
        Convert a Vibey workflow markdown to Aider Python script.

        Args:
            workflow_id: Workflow identifier (e.g., "weekly_sprint")
            content: Original workflow markdown content

        Returns:
            Python script for Aider API
        """
        # Extract title
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else workflow_id.replace('_', ' ').title()

        # Extract steps (numbered list items)
        steps = re.findall(r'^\d+\.\s+\*\*([^*]+)\*\*:?\s*(.*)$', content, re.MULTILINE)

        # Build Python script
        script = f'''#!/usr/bin/env python3
"""
{title} - Aider Workflow Script

GENERATED - DO NOT EDIT
Source: vibey/content/workflows/*/{workflow_id.replace('_', '-')}.md
Regenerate with: vibey deploy --platform aider

Usage:
    python .aider/workflows/{workflow_id}.py

This script uses the Aider Python API to execute a multi-step workflow.
"""

import sys
from pathlib import Path

# Check if aider is available
try:
    from aider.coders import Coder
    from aider.models import Model
    from aider.io import InputOutput
except ImportError:
    print("Error: aider package not installed")
    print("Install with: pip install aider-chat")
    sys.exit(1)


def run_workflow():
    """Execute the {title} workflow."""

    # Initialize Aider
    model = Model("claude-3-5-sonnet")  # Configure as needed
    io = InputOutput(yes=True)  # Auto-accept changes

    # Create coder instance
    # Add relevant files to the chat
    coder = Coder.create(
        main_model=model,
        io=io,
        # fnames=["src/main.py"],  # Add files as needed
    )

    print(f"Starting workflow: {title}")
    print("=" * 50)

'''

        # Add workflow steps
        if steps:
            for i, (step_name, step_desc) in enumerate(steps, 1):
                script += f'''
    # Step {i}: {step_name.strip()}
    print(f"\\nStep {i}: {step_name.strip()}")
    # {step_desc.strip() if step_desc else 'Execute step'}
    # coder.run("Your task description here")

'''
        else:
            script += '''
    # Execute workflow steps
    # Add your Aider commands here
    # coder.run("Describe the task")

'''

        script += '''
    print("\\n" + "=" * 50)
    print("Workflow complete!")


if __name__ == "__main__":
    run_workflow()
'''
        return script

    def _generate_hooks(self, hooks_dir: Path) -> List[Path]:
        """
        Generate git hooks for quality gates.

        Args:
            hooks_dir: Target .aider/hooks/ directory

        Returns:
            List of created file paths
        """
        created_files = []
        hooks_dir.mkdir(parents=True, exist_ok=True)

        # Pre-commit hook
        pre_commit = hooks_dir / "pre-commit"
        pre_commit.write_text('''#!/bin/bash
# Vibey Pre-Commit Hook for Aider
# GENERATED - DO NOT EDIT
# Regenerate with: vibey deploy --platform aider

# Run linting
echo "Running pre-commit checks..."

# Check for syntax errors in Python files
if command -v python3 &> /dev/null; then
    for file in $(git diff --cached --name-only --diff-filter=ACM | grep -E '\\.py$'); do
        python3 -m py_compile "$file" || exit 1
    done
fi

# Check for common issues
# Add your custom checks here

echo "Pre-commit checks passed!"
exit 0
''')
        pre_commit.chmod(0o755)
        created_files.append(pre_commit)

        # Post-commit hook
        post_commit = hooks_dir / "post-commit"
        post_commit.write_text('''#!/bin/bash
# Vibey Post-Commit Hook for Aider
# GENERATED - DO NOT EDIT
# Regenerate with: vibey deploy --platform aider

# Track commit metadata for Vibey workflows
# This hook can be used to update workflow state

echo "Commit recorded by Vibey workflow tracking."
exit 0
''')
        post_commit.chmod(0o755)
        created_files.append(post_commit)

        # README for hooks
        hooks_readme = hooks_dir / "README.md"
        hooks_readme.write_text('''# Aider Git Hooks

These hooks are generated by Vibey Agent Framework.

## Installation

To activate these hooks, symlink them to your .git/hooks directory:

```bash
ln -sf ../../.aider/hooks/pre-commit .git/hooks/pre-commit
ln -sf ../../.aider/hooks/post-commit .git/hooks/post-commit
```

Or copy them:

```bash
cp .aider/hooks/* .git/hooks/
```

## Hooks

- **pre-commit**: Runs quality checks before commits
- **post-commit**: Tracks commits for Vibey workflow state

---
*Generated by Vibey Agent Framework*
''')
        created_files.append(hooks_readme)

        return created_files

    def generate_context_file(self, config: Any, output_path: Path) -> None:
        """
        Generate context file for Aider.

        Aider doesn't have a dedicated context file like CLAUDE.md,
        but we generate aider.conf.yml which serves a similar purpose.

        Args:
            config: Vibey configuration
            output_path: Path to write context file
        """
        # For Aider, the config file IS the context file
        self._generate_aider_config(config, output_path)

    def validate_deployment(self, deployment_dir: Path) -> tuple[bool, List[str]]:
        """
        Validate Aider deployment.

        Checks:
        - Deployment directory exists
        - .generated marker exists
        - aider.conf.yml exists and contains marker
        - Required subdirectories exist

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

        # Check .generated marker
        marker = deployment_dir / ".generated"
        if not marker.exists():
            errors.append("Missing .generated marker file")

        # Check aider.conf.yml exists
        config_file = deployment_dir / "aider.conf.yml"
        if not config_file.exists():
            errors.append("Missing aider.conf.yml")
        else:
            content = config_file.read_text()
            if not content.strip():
                errors.append("aider.conf.yml is empty")
            if "VIBEY_FRAMEWORK_MANAGED" not in content:
                errors.append("aider.conf.yml missing Vibey framework marker")

        # Check required subdirectories
        required_dirs = ["agents", "workflows", "hooks"]
        for dir_name in required_dirs:
            dir_path = deployment_dir / dir_name
            if not dir_path.exists():
                errors.append(f"Missing required directory: {dir_name}/")
            elif not dir_path.is_dir():
                errors.append(f"{dir_name} exists but is not a directory")

        return (len(errors) == 0, errors)

    def get_required_files(self) -> List[str]:
        """Required files for Aider."""
        return [
            ".generated",
            "aider.conf.yml",
        ]

    def get_optional_files(self) -> List[str]:
        """Optional files for Aider."""
        return [
            "agents/",
            "workflows/",
            "hooks/",
        ]

    def supports_feature(self, feature: str) -> bool:
        """
        Check feature support.

        Aider has excellent feature support:
        - agents → system prompts (full support)
        - workflows → Python scripts (full support)
        - quality-gates → git hooks (full support)
        - templates → via prompts (full support)
        """
        supported = {
            "agents",
            "workflows",
            "quality-gates",
            "templates",
        }

        partially_supported = {
            "roadmap": "Aider doesn't have native roadmap support, "
                      "but workflows can track state in git commits",
        }

        return feature in supported or feature in partially_supported
