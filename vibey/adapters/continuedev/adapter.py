"""
Continue.dev Platform Adapter.

Main adapter class that coordinates all Continue.dev export generators
to produce a complete deployment package.

Zero-Drift Architecture:
- All artifacts generated from frontmatter (single source of truth)
- Checksums embedded for drift detection
- CI validation ensures no manual edits

Continue.dev Integration:
- Native MCP support (first client with full MCP support, Dec 2024)
- .continuerc.yaml for workspace configuration
- Custom prompts from agent frontmatter
- Works in VS Code and JetBrains IDEs
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Any, Dict

from vibey.adapters.base import PlatformAdapter, DeploymentResult
from .context_generator import ContinueContextGenerator, GeneratedContext
from .settings_generator import ContinueSettingsGenerator, GeneratedSettings

logger = logging.getLogger(__name__)


@dataclass
class ContinueExportResult:
    """Complete result of Continue.dev export."""
    success: bool
    output_dir: Path
    context: Optional[GeneratedContext] = None
    settings: Optional[GeneratedSettings] = None
    files_created: List[Path] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    checksums: Dict[str, str] = field(default_factory=dict)
    duration_seconds: float = 0.0


class ContinueAdapter(PlatformAdapter):
    """
    Adapter for Continue.dev platform.

    Exports Vibey framework to Continue.dev's configuration format:
    - CONTINUE.md context file (from agent frontmatter)
    - .continuerc.yaml (MCP server + prompts configuration)
    - Checksums manifest for drift detection

    Zero-Drift Guarantee:
    All outputs are generated from frontmatter. The adapter tracks
    checksums for each generated artifact, enabling CI to detect
    and reject manual edits.

    Example:
        >>> adapter = ContinueAdapter(Path("/path/to/vibey"))
        >>> result = adapter.export(Path("./dist"))
        >>> print(f"Created {len(result.files_created)} files")
    """

    def __init__(
        self,
        vibey_root: Optional[Path] = None,
    ):
        """
        Initialize Continue adapter.

        Args:
            vibey_root: Root directory of Vibey repository (default: cwd)
        """
        self._vibey_root = Path(vibey_root) if vibey_root else None
        self._context_generator: Optional[ContinueContextGenerator] = None
        self._settings_generator: Optional[ContinueSettingsGenerator] = None

        # Initialize generators if root is provided
        if self._vibey_root:
            self._init_generators()

    def _init_generators(self, root: Optional[Path] = None) -> None:
        """Initialize generators with the given root directory."""
        if root:
            self._vibey_root = Path(root)
        if self._vibey_root:
            self._context_generator = ContinueContextGenerator(self._vibey_root)
            self._settings_generator = ContinueSettingsGenerator(self._vibey_root)

    @property
    def vibey_root(self) -> Path:
        """Get vibey root, defaulting to cwd if not set."""
        if self._vibey_root is None:
            self._vibey_root = Path.cwd()
        return self._vibey_root

    @property
    def context_generator(self) -> ContinueContextGenerator:
        """Get context generator, initializing if needed."""
        if self._context_generator is None:
            self._init_generators()
        return self._context_generator

    @property
    def settings_generator(self) -> ContinueSettingsGenerator:
        """Get settings generator, initializing if needed."""
        if self._settings_generator is None:
            self._init_generators()
        return self._settings_generator

    def get_platform_name(self) -> str:
        """Get platform name."""
        return "continue"

    def get_deployment_dir(self, project_root: Optional[Path] = None) -> Path:
        """Get default deployment directory."""
        if project_root is None:
            project_root = Path.cwd()
        return project_root / ".continue"

    def export(
        self,
        output_dir: Path,
        include_readme: bool = True,
        mcp_server_command: str = "python",
        mcp_server_args: Optional[List[str]] = None,
    ) -> ContinueExportResult:
        """
        Export complete Continue.dev configuration package.

        This is the main export method that generates all artifacts:
        1. CONTINUE.md (context file)
        2. .continuerc.yaml (MCP + prompts config)
        3. README.md (optional)
        4. .checksums.json (drift detection)

        Args:
            output_dir: Directory to write configuration
            include_readme: Generate README.md
            mcp_server_command: Python command for MCP server
            mcp_server_args: Args for MCP server

        Returns:
            ContinueExportResult with all metadata
        """
        if mcp_server_args is None:
            mcp_server_args = ["-m", "framework.mcp.server"]

        start_time = datetime.now(timezone.utc)
        result = ContinueExportResult(
            success=False,
            output_dir=output_dir,
        )

        try:
            output_dir.mkdir(parents=True, exist_ok=True)

            # 1. Generate CONTINUE.md
            logger.info("Generating CONTINUE.md...")
            context_result = self.context_generator.write_to_file(
                output_dir / "CONTINUE.md"
            )
            result.context = context_result
            result.files_created.append(output_dir / "CONTINUE.md")
            result.checksums["CONTINUE.md"] = context_result.checksum

            # 2. Generate .continuerc.yaml
            logger.info("Generating .continuerc.yaml...")
            settings_result = self.settings_generator.generate(
                mcp_command=mcp_server_command,
                mcp_args=mcp_server_args,
            )
            continuerc_path = output_dir / ".continuerc.yaml"
            continuerc_path.write_text(settings_result.content, encoding='utf-8')
            result.settings = settings_result
            result.files_created.append(continuerc_path)
            result.checksums[".continuerc.yaml"] = settings_result.checksum

            # 3. Generate README (optional)
            if include_readme:
                readme_path = self._generate_readme(output_dir, context_result)
                result.files_created.append(readme_path)

            # 4. Write checksums manifest for drift detection
            self._write_checksums_manifest(output_dir, result.checksums)
            result.files_created.append(output_dir / ".checksums.json")

            result.success = True
            logger.info(
                f"Continue export complete: {len(result.files_created)} files, "
                f"{context_result.agents_count} agents, "
                f"{context_result.workflows_count} workflows"
            )

        except Exception as e:
            logger.error(f"Export failed: {e}")
            result.errors.append(str(e))
            result.success = False

        result.duration_seconds = (
            datetime.now(timezone.utc) - start_time
        ).total_seconds()

        return result

    def _generate_readme(
        self,
        output_dir: Path,
        context: GeneratedContext,
    ) -> Path:
        """Generate README.md for the export."""
        readme_content = f"""# Vibey Framework for Continue.dev

This directory contains the Vibey Agent Framework configuration for Continue.dev.

## Contents

- `CONTINUE.md` - Context file with agent and workflow documentation
- `.continuerc.yaml` - Continue configuration with MCP server and prompts

## Installation

### Option 1: Copy to Project Root

Copy `.continuerc.yaml` to your project root:

```bash
cp .continuerc.yaml /path/to/your/project/
```

### Option 2: Merge with Existing Config

If you have an existing `~/.continue/config.yaml`, merge the MCP server section:

```yaml
mcpServers:
  - name: Vibey Framework
    command: python
    args:
      - "-m"
      - "framework.mcp.server"
```

## Usage

Once configured, the Vibey MCP tools will be available in Continue:

- **Roadmap tools**: `vibey_roadmap_status`, `vibey_start_task`, etc.
- **Agent tools**: `vibey_web_developer`, `vibey_test_engineer`, etc.
- **Workflow tools**: `vibey_workflow_sprint_planning`, etc.

## Statistics

- **Agents**: {context.agents_count}
- **Workflows**: {context.workflows_count}
- **Generated**: {context.generated_at.isoformat()}

## Zero-Drift Validation

This configuration is generated from Vibey frontmatter. Do not edit manually.
Regenerate with:

```bash
vibey deploy --platform continue
```

Validate with:

```bash
vibey deploy --platform continue --validate
```
"""
        readme_path = output_dir / "README.md"
        readme_path.write_text(readme_content, encoding='utf-8')
        return readme_path

    def _write_checksums_manifest(
        self,
        output_dir: Path,
        checksums: Dict[str, str],
    ) -> None:
        """Write checksums manifest for drift detection."""
        manifest = {
            "version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generator": "vibey-continue-adapter",
            "platform": "continue",
            "checksums": checksums,
            "validation_command": "vibey deploy --platform continue --validate",
        }
        manifest_path = output_dir / ".checksums.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2),
            encoding='utf-8'
        )

    def validate_export(self, export_dir: Path) -> tuple[bool, List[str]]:
        """
        Validate an existing export hasn't drifted.

        Args:
            export_dir: Directory containing exported configuration

        Returns:
            Tuple of (is_valid, error_messages)
        """
        import hashlib

        errors = []

        checksums_path = export_dir / ".checksums.json"
        if not checksums_path.exists():
            errors.append("Missing .checksums.json - cannot validate")
            return False, errors

        try:
            stored = json.loads(checksums_path.read_text())
            stored_checksums = stored.get("checksums", {})
        except Exception as e:
            errors.append(f"Failed to read checksums: {e}")
            return False, errors

        # Check CONTINUE.md
        continue_md_path = export_dir / "CONTINUE.md"
        if continue_md_path.exists():
            content = continue_md_path.read_text()
            lines = content.split("\n")
            stable_lines = [l for l in lines if not l.startswith("<!-- Generated:")]
            stable_content = "\n".join(stable_lines)
            current_checksum = hashlib.sha256(stable_content.encode()).hexdigest()[:16]

            if stored_checksums.get("CONTINUE.md") != current_checksum:
                errors.append(
                    f"CONTINUE.md has drifted! "
                    f"Stored: {stored_checksums.get('CONTINUE.md')}, "
                    f"Current: {current_checksum}"
                )

        # Check .continuerc.yaml
        continuerc_path = export_dir / ".continuerc.yaml"
        if continuerc_path.exists():
            content = continuerc_path.read_text()
            lines = content.split("\n")
            stable_lines = [l for l in lines if "Generated:" not in l]
            stable_content = "\n".join(stable_lines)
            current_checksum = hashlib.sha256(stable_content.encode()).hexdigest()[:16]

            if stored_checksums.get(".continuerc.yaml") != current_checksum:
                errors.append(
                    f".continuerc.yaml has drifted! "
                    f"Stored: {stored_checksums.get('.continuerc.yaml')}, "
                    f"Current: {current_checksum}"
                )

        return len(errors) == 0, errors

    # PlatformAdapter interface implementation

    def deploy(
        self,
        source_dir: Path,
        config: Any,
        target_dir: Optional[Path] = None,
        clean: bool = False,
    ) -> DeploymentResult:
        """
        Deploy to Continue.dev (implements PlatformAdapter interface).

        For Continue, "deployment" means exporting the configuration.
        The source_dir is expected to be .vibey/, so vibey_root is its parent.
        """
        # Ensure generators are initialized with correct root
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
        """Generate CONTINUE.md context file."""
        self.context_generator.write_to_file(output_path)

    def validate_deployment(self, deployment_dir: Path) -> tuple[bool, List[str]]:
        """Validate Continue deployment."""
        errors = []

        # Check required files
        required = [
            "CONTINUE.md",
            ".continuerc.yaml",
        ]

        for req_file in required:
            path = deployment_dir / req_file
            if not path.exists():
                errors.append(f"Missing required file: {req_file}")

        # Validate no drift
        if (deployment_dir / ".checksums.json").exists():
            is_valid, drift_errors = self.validate_export(deployment_dir)
            if not is_valid:
                errors.extend(drift_errors)

        return len(errors) == 0, errors

    def get_required_files(self) -> List[str]:
        """Required files for Continue."""
        return [
            "CONTINUE.md",
            ".continuerc.yaml",
        ]

    def get_optional_files(self) -> List[str]:
        """Optional files for Continue."""
        return [
            "README.md",
            ".checksums.json",
        ]

    def supports_feature(self, feature: str) -> bool:
        """Check feature support."""
        supported = {
            "agents",      # Via prompts
            "workflows",   # Via MCP tools
            "mcp",         # Native support
            "templates",   # Via prompts
            "roadmap",     # Via MCP tools
        }

        return feature in supported
