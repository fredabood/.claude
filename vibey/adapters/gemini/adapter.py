"""
Gemini Platform Adapter.

Main adapter class that coordinates all Gemini export generators
to produce a complete, installable extension package.

Zero-Drift Architecture:
- All artifacts generated from frontmatter (single source of truth)
- Checksums embedded for drift detection
- CI validation ensures no manual edits
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Any, Dict

from vibey.adapters.base import PlatformAdapter, DeploymentResult
from .context_generator import GeminiContextGenerator, GeneratedContext
from .command_generator import GeminiCommandGenerator, CommandGenerationResult
from .extension_generator import GeminiExtensionGenerator, ExtensionManifest

logger = logging.getLogger(__name__)


@dataclass
class GeminiExportResult:
    """Complete result of Gemini export."""
    success: bool
    output_dir: Path
    context: Optional[GeneratedContext] = None
    commands: Optional[CommandGenerationResult] = None
    files_created: List[Path] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    checksums: Dict[str, str] = field(default_factory=dict)
    duration_seconds: float = 0.0


class GeminiAdapter(PlatformAdapter):
    """
    Adapter for Gemini Code Assist platform.

    Exports Vibey framework to Gemini's extension format:
    - GEMINI.md context file (from agent frontmatter)
    - TOML custom commands (from workflow frontmatter)
    - MCP server configuration
    - Extension manifest

    Zero-Drift Guarantee:
    All outputs are generated from frontmatter. The adapter tracks
    checksums for each generated artifact, enabling CI to detect
    and reject manual edits.

    Example:
        >>> adapter = GeminiAdapter(Path("/path/to/vibey"))
        >>> result = adapter.export(Path("./dist/vibey-gemini-extension"))
        >>> print(f"Created {len(result.files_created)} files")
    """

    def __init__(
        self,
        vibey_root: Optional[Path] = None,
        manifest: Optional[ExtensionManifest] = None,
    ):
        """
        Initialize Gemini adapter.

        Args:
            vibey_root: Root directory of Vibey repository (default: cwd)
            manifest: Custom extension manifest (optional)
        """
        self._vibey_root = Path(vibey_root) if vibey_root else None
        self._manifest = manifest
        self._context_generator: Optional[GeminiContextGenerator] = None
        self._command_generator: Optional[GeminiCommandGenerator] = None
        self._extension_generator: Optional[GeminiExtensionGenerator] = None

        # Initialize generators if root is provided
        if self._vibey_root:
            self._init_generators()

    def _init_generators(self, root: Optional[Path] = None) -> None:
        """Initialize generators with the given root directory."""
        if root:
            self._vibey_root = Path(root)
        if self._vibey_root:
            self._context_generator = GeminiContextGenerator(self._vibey_root)
            self._command_generator = GeminiCommandGenerator(self._vibey_root)
            self._extension_generator = GeminiExtensionGenerator(self._manifest)

    @property
    def vibey_root(self) -> Path:
        """Get vibey root, defaulting to cwd if not set."""
        if self._vibey_root is None:
            self._vibey_root = Path.cwd()
        return self._vibey_root

    @property
    def context_generator(self) -> GeminiContextGenerator:
        """Get context generator, initializing if needed."""
        if self._context_generator is None:
            self._init_generators()
        return self._context_generator

    @property
    def command_generator(self) -> GeminiCommandGenerator:
        """Get command generator, initializing if needed."""
        if self._command_generator is None:
            self._init_generators()
        return self._command_generator

    @property
    def extension_generator(self) -> GeminiExtensionGenerator:
        """Get extension generator, initializing if needed."""
        if self._extension_generator is None:
            self._init_generators()
        return self._extension_generator

    def get_platform_name(self) -> str:
        """Get platform name."""
        return "gemini"

    def get_deployment_dir(self, project_root: Optional[Path] = None) -> Path:
        """Get default deployment directory."""
        if project_root is None:
            project_root = Path.cwd()
        return project_root / ".gemini"

    def export(
        self,
        output_dir: Path,
        include_install_script: bool = True,
        include_readme: bool = True,
        mcp_server_command: str = "python",
        mcp_server_args: Optional[List[str]] = None,
    ) -> GeminiExportResult:
        """
        Export complete Gemini extension package.

        This is the main export method that generates all artifacts:
        1. GEMINI.md (context file)
        2. TOML commands
        3. Extension manifest
        4. Settings.json (MCP config)
        5. Install script and README (optional)

        Args:
            output_dir: Directory to write extension package
            include_install_script: Generate install.sh
            include_readme: Generate README.md
            mcp_server_command: Python command for MCP server
            mcp_server_args: Args for MCP server

        Returns:
            GeminiExportResult with all metadata
        """
        start_time = datetime.now(timezone.utc)
        result = GeminiExportResult(
            success=False,
            output_dir=output_dir,
        )

        try:
            output_dir.mkdir(parents=True, exist_ok=True)

            # 1. Generate GEMINI.md
            logger.info("Generating GEMINI.md...")
            context_result = self.context_generator.write_to_file(
                output_dir / "GEMINI.md"
            )
            result.context = context_result
            result.files_created.append(output_dir / "GEMINI.md")
            result.checksums["GEMINI.md"] = context_result.checksum

            # 2. Generate TOML commands
            logger.info("Generating TOML commands...")
            commands_result = self.command_generator.write_to_directory(
                output_dir / "commands"
            )
            result.commands = commands_result
            result.checksums["commands"] = commands_result.checksum
            for cmd in commands_result.commands:
                result.files_created.append(
                    output_dir / "commands" / "vibey" / cmd.filename
                )

            # 3. Generate extension manifest
            logger.info("Generating extension manifest...")
            manifest_path = self.extension_generator.generate_manifest(output_dir)
            result.files_created.append(manifest_path)

            # 4. Generate settings.json
            logger.info("Generating MCP settings...")
            settings_path = self.extension_generator.generate_settings(
                output_dir,
                mcp_server_command=mcp_server_command,
                mcp_server_args=mcp_server_args,
            )
            result.files_created.append(settings_path)

            # 5. Generate install script (optional)
            if include_install_script:
                script_path = self.extension_generator.generate_install_script(output_dir)
                result.files_created.append(script_path)

            # 6. Generate README (optional)
            if include_readme:
                readme_path = self.extension_generator.generate_readme(output_dir)
                result.files_created.append(readme_path)

            # 7. Write checksums manifest for drift detection
            self._write_checksums_manifest(output_dir, result.checksums)
            result.files_created.append(output_dir / ".checksums.json")

            result.success = True
            logger.info(
                f"Gemini export complete: {len(result.files_created)} files, "
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

    def _write_checksums_manifest(
        self,
        output_dir: Path,
        checksums: Dict[str, str],
    ) -> None:
        """Write checksums manifest for drift detection."""
        manifest = {
            "version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generator": "vibey-gemini-adapter",
            "checksums": checksums,
            "validation_command": "vibey export gemini --validate",
        }
        manifest_path = output_dir / ".checksums.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2),
            encoding='utf-8'
        )

    def validate_export(self, export_dir: Path) -> tuple[bool, List[str]]:
        """
        Validate an existing export hasn't drifted.

        Compares the actual file content on disk with stored checksums
        to detect manual edits. Also checks if source has changed.

        Args:
            export_dir: Directory containing exported extension

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

        # Check GEMINI.md on disk matches stored checksum
        gemini_md_path = export_dir / "GEMINI.md"
        if gemini_md_path.exists():
            content = gemini_md_path.read_text()
            # Remove timestamp line for stable comparison
            lines = content.split("\n")
            stable_lines = [l for l in lines if not l.startswith("<!-- Generated:")]
            stable_content = "\n".join(stable_lines)
            current_checksum = hashlib.sha256(stable_content.encode()).hexdigest()[:16]

            if stored_checksums.get("GEMINI.md") != current_checksum:
                errors.append(
                    f"GEMINI.md has drifted (file modified)! "
                    f"Stored: {stored_checksums.get('GEMINI.md')}, "
                    f"Current: {current_checksum}"
                )

        # Check commands checksum - regenerate from source and compare
        # This detects if source changed OR if files were manually edited
        try:
            commands_result = self.command_generator.generate()
            regenerated_checksum = commands_result.checksum

            # Compare regenerated with stored (detects source drift)
            if stored_checksums.get("commands") != regenerated_checksum:
                # Source has changed - now check if files match source
                errors.append(
                    f"Commands have drifted (source changed)! "
                    f"Stored: {stored_checksums.get('commands')}, "
                    f"Regenerated: {regenerated_checksum}"
                )
            else:
                # Source matches stored - check if files were manually edited
                commands_dir = export_dir / "commands" / "vibey"
                if commands_dir.exists():
                    for cmd in commands_result.commands:
                        cmd_file = commands_dir / cmd.filename
                        if cmd_file.exists():
                            disk_content = cmd_file.read_text()
                            if disk_content != cmd.content:
                                errors.append(
                                    f"Command file manually edited: {cmd.filename}"
                                )
                                break  # Report first drift only
        except Exception as e:
            errors.append(f"Failed to validate commands: {e}")

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
        Deploy to Gemini (implements PlatformAdapter interface).

        For Gemini, "deployment" means exporting the extension package.
        The source_dir is expected to be .vibey/, so vibey_root is its parent.
        """
        # Ensure generators are initialized with correct root
        # source_dir is .vibey/, so parent is the project root (vibey_root)
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
        """Generate GEMINI.md context file."""
        self.context_generator.write_to_file(output_path)

    def validate_deployment(self, deployment_dir: Path) -> tuple[bool, List[str]]:
        """Validate Gemini deployment."""
        errors = []

        # Check required files
        required = [
            "GEMINI.md",
            "gemini-extension.json",
            "settings.json",
            "commands/vibey/_manifest.json",
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
        """Required files for Gemini."""
        return [
            "GEMINI.md",
            "gemini-extension.json",
            "settings.json",
        ]

    def get_optional_files(self) -> List[str]:
        """Optional files for Gemini."""
        return [
            "commands/",
            "install.sh",
            "README.md",
        ]

    def supports_feature(self, feature: str) -> bool:
        """Check feature support."""
        supported = {
            "agents",      # Via GEMINI.md
            "workflows",   # Via TOML commands
            "mcp",         # Native support
            "templates",   # Limited
        }

        not_supported = {
            "subagents",       # Gemini is sequential only
            "parallel-tasks",  # No parallel execution
            "quality-gates",   # Limited support
        }

        if feature in not_supported:
            return False
        return feature in supported
