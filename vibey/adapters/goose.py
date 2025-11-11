"""
Goose platform adapter.

This adapter deploys Vibey to Goose's .goose/ directory format.

Goose (by Block) uses:
- .goosehints - Context file (markdown format)
- Toolkit extensions (.goose/extensions/)
- Recipe files (.goose/recipes/)
"""

from pathlib import Path
from typing import Optional, List, Any
import shutil
from datetime import datetime

from vibey.adapters.base import PlatformAdapter, DeploymentResult


class GooseAdapter(PlatformAdapter):
    """
    Adapter for Goose platform (by Block).

    Deploys Vibey framework to .goose/ directory with:
    - .goosehints (context file, similar to CLAUDE.md)
    - extensions/ (custom toolkit extensions)
    - recipes/ (workflow recipes)

    Note: This is a basic implementation. Goose's extension system
    is more limited than Claude Code's agent system, so we map:
    - Vibey workflows → Goose recipes
    - Vibey agents → Goose extensions (where possible)
    """

    def get_platform_name(self) -> str:
        """Get platform name."""
        return "goose"

    def get_deployment_dir(self, project_root: Optional[Path] = None) -> Path:
        """Get deployment directory (.goose/)."""
        if project_root is None:
            project_root = Path.cwd()
        return project_root / ".goose"

    def deploy(
        self,
        source_dir: Path,
        config: Any,
        target_dir: Optional[Path] = None,
        clean: bool = False
    ) -> DeploymentResult:
        """
        Deploy to Goose.

        Deployment steps:
        1. Clean target directory if requested
        2. Create directory structure
        3. Generate .goosehints context file
        4. Convert workflows → recipes
        5. Generate extensions from agents (basic mapping)
        6. Validate deployment

        Args:
            source_dir: .vibey/ directory
            config: Vibey configuration
            target_dir: .goose/ directory (or custom)
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

            # Create subdirectories
            (target_dir / "extensions").mkdir(exist_ok=True)
            (target_dir / "recipes").mkdir(exist_ok=True)

            # Step 3: Generate .goosehints
            # Goose expects .goosehints in project root (parent of .goose/)
            goosehints_path = target_dir.parent / ".goosehints"
            self.generate_context_file(config, goosehints_path)
            if goosehints_path.exists():
                result.files_created.append(goosehints_path)

            # Step 4: Convert workflows to recipes (if they exist)
            workflows_dir = source_dir.parent / "workflows"
            if workflows_dir.exists() and workflows_dir.is_dir():
                recipes_dir = target_dir / "recipes"
                # Copy workflow markdown files as recipes
                # (Goose recipes are similar to workflows)
                for workflow_file in workflows_dir.rglob("*.md"):
                    recipe_file = recipes_dir / workflow_file.relative_to(workflows_dir)
                    recipe_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(workflow_file, recipe_file)
                    result.files_created.append(recipe_file)

                result.warnings.append(
                    f"Workflows converted to recipes. "
                    f"Note: Goose recipes may have different syntax than Vibey workflows."
                )

            # Step 5: Generate basic extensions info
            # (Goose extensions are Python-based toolkits, different from Vibey agents)
            extensions_readme = target_dir / "extensions" / "README.md"
            extensions_readme.write_text(
                "# Vibey Agent Mappings\n\n"
                "Goose uses Python-based toolkit extensions rather than markdown agents.\n"
                "Vibey agents cannot be directly converted to Goose extensions.\n\n"
                "Consider creating custom Goose toolkits for your agent functionality.\n"
            )
            result.files_created.append(extensions_readme)
            result.warnings.append(
                "Vibey agents not converted to Goose extensions. "
                "Goose uses Python toolkits instead of markdown agents."
            )

            # Step 6: Validate deployment
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
        Generate .goosehints context file.

        Goose's context file (.goosehints) is similar to CLAUDE.md but
        with Goose-specific formatting preferences.

        Args:
            config: Vibey configuration
            output_path: Path to write .goosehints
        """
        # Build .goosehints content
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

## Vibey Framework

This project uses the Vibey Agent Framework for intelligent workflow management.

**Orchestration Mode:** {mode}

Available workflows are in `.goose/recipes/`.

---

## Project Structure

""".format(mode=config.framework.framework.orchestration_mode.value)

        # Add paths if configured
        if hasattr(config.project, 'paths'):
            content += f"- Source: `{config.project.paths.source}`\n"
            content += f"- Tests: `{config.project.paths.tests}`\n"
            content += f"- Docs: `{config.project.paths.docs}`\n"

        content += """
---

<!-- VIBEY_FRAMEWORK_MANAGED -->
*Generated by Vibey Agent Framework for Goose*
"""

        # Write to file
        output_path.write_text(content)

    def validate_deployment(self, deployment_dir: Path) -> tuple[bool, List[str]]:
        """
        Validate Goose deployment.

        Checks:
        - Deployment directory exists
        - .goosehints exists and has content
        - .goosehints contains Vibey marker
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

        # Check .goosehints exists (in parent directory)
        goosehints = deployment_dir.parent / ".goosehints"
        if not goosehints.exists():
            errors.append(f"Missing required file: .goosehints")
        else:
            # Check .goosehints has content
            content = goosehints.read_text()
            if not content.strip():
                errors.append(".goosehints is empty")

            # Check for Vibey marker
            if "VIBEY_FRAMEWORK_MANAGED" not in content:
                errors.append(".goosehints missing Vibey framework marker")

        # Check required subdirectories
        required_dirs = ["extensions", "recipes"]
        for dir_name in required_dirs:
            dir_path = deployment_dir / dir_name
            if not dir_path.exists():
                errors.append(f"Missing required directory: {dir_name}/")
            elif not dir_path.is_dir():
                errors.append(f"{dir_name} exists but is not a directory")

        return (len(errors) == 0, errors)

    def get_required_files(self) -> List[str]:
        """Required files for Goose."""
        return [
            "../.goosehints",  # In parent directory
        ]

    def get_optional_files(self) -> List[str]:
        """Optional files for Goose."""
        return [
            "extensions/",
            "recipes/",
        ]

    def supports_feature(self, feature: str) -> bool:
        """
        Check feature support.

        Goose has more limited features than Claude Code:
        - workflows → recipes (supported, with caveats)
        - agents → NOT directly supported (different paradigm)
        - quality-gates → NOT supported
        - templates → LIMITED support
        """
        supported = {
            "workflows",  # Via recipes
            "templates",  # Limited
        }

        partially_supported = {
            "roadmap": "Goose doesn't have native roadmap support, but recipes can reference roadmap",
        }

        return feature in supported or feature in partially_supported
