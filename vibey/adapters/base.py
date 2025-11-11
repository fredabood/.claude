"""
Base adapter class for platform deployments.

This module defines the PlatformAdapter abstract base class that all
platform-specific adapters must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class DeploymentResult:
    """
    Result of a platform deployment.

    Attributes:
        success: Whether deployment succeeded
        platform: Platform name (e.g., "claude-code", "goose")
        target_dir: Deployment directory path
        files_created: List of files created
        files_updated: List of files updated
        files_deleted: List of files deleted
        validation_passed: Whether post-deployment validation passed
        errors: List of error messages
        warnings: List of warning messages
        timestamp: When deployment completed
        duration_seconds: How long deployment took
    """
    success: bool
    platform: str
    target_dir: Path
    files_created: List[Path] = field(default_factory=list)
    files_updated: List[Path] = field(default_factory=list)
    files_deleted: List[Path] = field(default_factory=list)
    validation_passed: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    duration_seconds: float = 0.0

    def __str__(self) -> str:
        """Human-readable summary."""
        status = "✓ Success" if self.success else "✗ Failed"
        return (
            f"{status} - {self.platform} deployed to {self.target_dir}\n"
            f"  Files: {len(self.files_created)} created, "
            f"{len(self.files_updated)} updated, "
            f"{len(self.files_deleted)} deleted\n"
            f"  Validation: {'✓ Passed' if self.validation_passed else '✗ Failed'}\n"
            f"  Duration: {self.duration_seconds:.2f}s"
        )


class PlatformAdapter(ABC):
    """
    Abstract base class for platform adapters.

    Platform adapters transform the .vibey/ source of truth into
    platform-specific deployments (.claude/, .goose/, etc.).

    Each adapter must implement:
    - get_platform_name(): Platform identifier
    - get_deployment_dir(): Default deployment directory name
    - deploy(): Perform the deployment
    - generate_context_file(): Create platform context file
    - validate_deployment(): Verify deployment is correct

    Example:
        class MyAdapter(PlatformAdapter):
            def get_platform_name(self) -> str:
                return "my-platform"

            def deploy(self, source_dir: Path, config: VibeyConfig) -> DeploymentResult:
                # Implementation here
                pass
    """

    @abstractmethod
    def get_platform_name(self) -> str:
        """
        Get the platform name (identifier).

        Returns:
            Platform name (e.g., "claude-code", "goose", "cursor")

        Example:
            >>> adapter.get_platform_name()
            'claude-code'
        """
        pass

    @abstractmethod
    def get_deployment_dir(self, project_root: Optional[Path] = None) -> Path:
        """
        Get the deployment directory for this platform.

        Args:
            project_root: Project root directory (default: current directory)

        Returns:
            Deployment directory path (e.g., .claude/, .goose/)

        Example:
            >>> adapter.get_deployment_dir()
            PosixPath('/path/to/project/.claude')
        """
        pass

    @abstractmethod
    def deploy(
        self,
        source_dir: Path,
        config: Any,  # VibeyConfig
        target_dir: Optional[Path] = None,
        clean: bool = False
    ) -> DeploymentResult:
        """
        Deploy Vibey framework to this platform.

        This is the main deployment method. It should:
        1. Read from source_dir (.vibey/)
        2. Transform for platform
        3. Write to target_dir (.claude/, .goose/, etc.)
        4. Validate deployment

        Args:
            source_dir: Source directory (.vibey/)
            config: Vibey configuration
            target_dir: Target deployment directory (default: auto-detect)
            clean: If True, remove existing deployment first

        Returns:
            DeploymentResult with success status and details

        Example:
            >>> result = adapter.deploy(
            ...     source_dir=Path(".vibey"),
            ...     config=config,
            ...     clean=True
            ... )
            >>> print(result.success)
            True
        """
        pass

    @abstractmethod
    def generate_context_file(self, config: Any, output_path: Path) -> None:
        """
        Generate platform-specific context file.

        Different platforms use different context files:
        - Claude Code: CLAUDE.md
        - Goose: .goosehints
        - Cursor: .cursorrules
        - etc.

        Args:
            config: Vibey configuration
            output_path: Where to write context file

        Example:
            >>> adapter.generate_context_file(
            ...     config=config,
            ...     output_path=Path(".claude/CLAUDE.md")
            ... )
        """
        pass

    @abstractmethod
    def validate_deployment(self, deployment_dir: Path) -> tuple[bool, List[str]]:
        """
        Validate that deployment is correct.

        Checks:
        - Required files exist
        - File contents are valid
        - Directory structure is correct
        - Platform-specific requirements met

        Args:
            deployment_dir: Deployment directory to validate

        Returns:
            Tuple of (is_valid, error_messages)

        Example:
            >>> is_valid, errors = adapter.validate_deployment(Path(".claude"))
            >>> if not is_valid:
            ...     print("Errors:", errors)
        """
        pass

    def get_required_files(self) -> List[str]:
        """
        Get list of required files for this platform.

        Override this to specify platform-specific required files.

        Returns:
            List of required file paths (relative to deployment dir)

        Example:
            >>> adapter.get_required_files()
            ['CLAUDE.md', 'project-config.yaml']
        """
        return []

    def get_optional_files(self) -> List[str]:
        """
        Get list of optional files for this platform.

        Override this to specify platform-specific optional files.

        Returns:
            List of optional file paths (relative to deployment dir)

        Example:
            >>> adapter.get_optional_files()
            ['custom-agents/', 'templates/']
        """
        return []

    def supports_feature(self, feature: str) -> bool:
        """
        Check if platform supports a specific feature.

        Common features:
        - "agents": Custom agents
        - "workflows": Custom workflows
        - "quality-gates": Quality gate system
        - "roadmap": Roadmap system
        - "templates": Custom templates

        Args:
            feature: Feature name to check

        Returns:
            True if feature is supported

        Example:
            >>> if adapter.supports_feature("agents"):
            ...     deploy_agents()
        """
        # Default: assume all features supported
        return True

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get adapter metadata.

        Returns:
            Dictionary with adapter information

        Example:
            >>> metadata = adapter.get_metadata()
            >>> print(metadata['version'])
            '1.0.0'
        """
        return {
            "platform": self.get_platform_name(),
            "adapter_version": "1.0.0",
            "vibey_version": "2.5.0",
        }

    def pre_deploy_hook(self, source_dir: Path, target_dir: Path) -> None:
        """
        Hook called before deployment starts.

        Override to add custom pre-deployment logic.

        Args:
            source_dir: Source directory (.vibey/)
            target_dir: Target deployment directory
        """
        pass

    def post_deploy_hook(self, result: DeploymentResult) -> None:
        """
        Hook called after deployment completes.

        Override to add custom post-deployment logic.

        Args:
            result: Deployment result
        """
        pass
