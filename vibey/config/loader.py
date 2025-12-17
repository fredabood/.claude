"""
Config loader with fallback support.

This module provides intelligent config loading that supports:
1. New modular format (.vibey/config/)
2. Legacy monolithic format (.claude/project-config.yaml)
3. Automatic fallback and detection
4. Clear error messages for missing or invalid configs
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Optional
import warnings

from pydantic import ValidationError as PydanticValidationError
import yaml

from vibey.config.models import (
    VibeyConfig,
    ProjectConfig,
    FrameworkConfig,
    AgentsConfig,
    QualityGatesConfig,
    Project,
    TechStack,
    Paths,
    Framework,
    Deployment,
    Features,
    Agents,
    QualityGates,
    Gates,
    OrchestrationMode,
    ProjectType,
    QualityGateMode,
)

# Import unified error handling
from vibey.common import (
    ConfigurationError as ConfigLoadError,
    ConfigNotFoundError,
    ConfigValidationError,
)


class ConfigLocation(str, Enum):
    """Config location detection result."""
    MODULAR = "modular"           # .vibey/config/ (new format)
    LEGACY = "legacy"             # .claude/project-config.yaml (old format)
    BOTH = "both"                 # Both exist (use modular, warn about legacy)
    NONE = "none"                 # Neither exists (error)


class ConfigLoader:
    """
    Intelligent config loader with fallback support.

    Load priority:
    1. .vibey/config/ (new modular format) - preferred
    2. .claude/project-config.yaml (legacy) - fallback with warning
    3. Error if neither exists

    Usage:
        loader = ConfigLoader()
        config = loader.load_config(Path.cwd())
    """

    def __init__(self, warn_on_legacy: bool = True):
        """
        Initialize config loader.

        Args:
            warn_on_legacy: Show warning when loading legacy config (default: True)
        """
        self.warn_on_legacy = warn_on_legacy

    def load_config(self, project_root: Optional[Path] = None) -> VibeyConfig:
        """
        Load Vibey configuration with automatic fallback.

        Args:
            project_root: Project root directory (default: current directory)

        Returns:
            VibeyConfig: Loaded and validated configuration

        Raises:
            ConfigNotFoundError: No config files found
            ConfigValidationError: Config validation failed
        """
        if project_root is None:
            project_root = Path.cwd()

        project_root = Path(project_root).resolve()

        # Detect which config format exists
        location = self.detect_config_location(project_root)

        if location == ConfigLocation.NONE:
            raise ConfigNotFoundError(
                searched_paths=[
                    str(project_root / ".vibey" / "config"),
                    str(project_root / ".claude" / "project-config.yaml"),
                ]
            )

        # Load from appropriate location
        if location == ConfigLocation.MODULAR:
            return self._load_modular_config(project_root / ".vibey" / "config")

        elif location == ConfigLocation.LEGACY:
            if self.warn_on_legacy:
                warnings.warn(
                    "Loading legacy config from .claude/project-config.yaml. "
                    "Consider migrating to modular format with 'vibey migrate config'.",
                    DeprecationWarning,
                    stacklevel=2
                )
            return self._load_legacy_config(project_root / ".claude" / "project-config.yaml")

        elif location == ConfigLocation.BOTH:
            # Both exist - prefer modular, warn about legacy
            warnings.warn(
                "Found both .vibey/config/ and .claude/project-config.yaml. "
                "Using modular config from .vibey/config/. "
                "Legacy config will be ignored.",
                UserWarning,
                stacklevel=2
            )
            return self._load_modular_config(project_root / ".vibey" / "config")

    def detect_config_location(self, project_root: Path) -> ConfigLocation:
        """
        Detect which config format is present.

        Args:
            project_root: Project root directory

        Returns:
            ConfigLocation: Detection result
        """
        modular_dir = project_root / ".vibey" / "config"
        legacy_file = project_root / ".claude" / "project-config.yaml"

        modular_exists = self._check_modular_config_exists(modular_dir)
        legacy_exists = legacy_file.exists()

        if modular_exists and legacy_exists:
            return ConfigLocation.BOTH
        elif modular_exists:
            return ConfigLocation.MODULAR
        elif legacy_exists:
            return ConfigLocation.LEGACY
        else:
            return ConfigLocation.NONE

    def _check_modular_config_exists(self, config_dir: Path) -> bool:
        """
        Check if modular config exists (all 4 required files).

        Args:
            config_dir: .vibey/config directory

        Returns:
            bool: True if all required files exist
        """
        if not config_dir.exists():
            return False

        required_files = [
            "project.yaml",
            "framework.yaml",
            "agents.yaml",
            "quality-gates.yaml"
        ]

        return all((config_dir / filename).exists() for filename in required_files)

    def _load_modular_config(self, config_dir: Path) -> VibeyConfig:
        """
        Load config from modular format (.vibey/config/).

        Args:
            config_dir: .vibey/config directory

        Returns:
            VibeyConfig: Loaded configuration

        Raises:
            ConfigNotFoundError: Missing config files
            ConfigValidationError: Validation failed
        """
        try:
            return VibeyConfig.from_directory(config_dir)

        except FileNotFoundError as e:
            raise ConfigNotFoundError(
                searched_paths=[str(config_dir)]
            )

        except PydanticValidationError as e:
            # Extract validation errors from Pydantic
            errors = [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
            raise ConfigValidationError(
                validation_errors=errors,
                config_file=str(config_dir)
            )

        except Exception as e:
            from vibey.common.errors import VibeyError, ErrorCategory
            raise VibeyError(
                message=f"Failed to load config from {config_dir}: {e}",
                code="CONFIG_LOAD_FAILED",
                category=ErrorCategory.CONFIGURATION,
            )

    def _load_legacy_config(self, legacy_file: Path) -> VibeyConfig:
        """
        Load and convert legacy config (.claude/project-config.yaml).

        This method reads the monolithic legacy config and converts it
        to the new modular format in memory.

        Args:
            legacy_file: Path to .claude/project-config.yaml

        Returns:
            VibeyConfig: Converted configuration

        Raises:
            ConfigNotFoundError: Legacy file not found
            ConfigValidationError: Validation failed
        """
        if not legacy_file.exists():
            raise ConfigNotFoundError(
                searched_paths=[str(legacy_file)]
            )

        try:
            with open(legacy_file, 'r') as f:
                legacy_data = yaml.safe_load(f)

            if not legacy_data:
                raise ConfigValidationError(
                    validation_errors=["Config file is empty"],
                    config_file=str(legacy_file)
                )

            # Convert legacy format to modular configs
            project_config = self._extract_project_config(legacy_data)
            framework_config = self._extract_framework_config(legacy_data)
            agents_config = self._extract_agents_config(legacy_data)
            quality_gates_config = self._extract_quality_gates_config(legacy_data)

            return VibeyConfig(
                project=project_config,
                framework=framework_config,
                agents=agents_config,
                quality_gates=quality_gates_config
            )

        except PydanticValidationError as e:
            # Extract validation errors from Pydantic
            errors = [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
            raise ConfigValidationError(
                validation_errors=errors,
                config_file=str(legacy_file)
            )

        except Exception as e:
            from vibey.common.errors import VibeyError, ErrorCategory
            raise VibeyError(
                message=f"Failed to load legacy config from {legacy_file}: {e}",
                code="CONFIG_LOAD_FAILED",
                category=ErrorCategory.CONFIGURATION,
            )

    def _extract_project_config(self, legacy_data: dict) -> ProjectConfig:
        """Extract project config from legacy format."""
        project_data = legacy_data.get('project', {})
        tech_stack_data = legacy_data.get('tech_stack', {})
        paths_data = legacy_data.get('paths', {})

        return ProjectConfig(
            project=Project(
                name=project_data.get('name', 'unknown'),
                version=project_data.get('version', '0.0.0'),
                type=ProjectType(project_data.get('type', 'library')),
                description=project_data.get('description'),
                repository=project_data.get('repository')
            ),
            tech_stack=TechStack(
                languages=tech_stack_data.get('languages', []),
                frameworks=tech_stack_data.get('frameworks', []),
                databases=tech_stack_data.get('databases', []),
                infrastructure=tech_stack_data.get('infrastructure', [])
            ),
            paths=Paths(
                source=paths_data.get('source', 'src'),
                tests=paths_data.get('tests', 'tests'),
                docs=paths_data.get('docs', 'docs'),
                config=paths_data.get('config', '.vibey/config')
            )
        )

    def _extract_framework_config(self, legacy_data: dict) -> FrameworkConfig:
        """Extract framework config from legacy format."""
        # Legacy used 'vibey' key for framework config
        vibey_data = legacy_data.get('vibey', {})
        deployment_data = legacy_data.get('deployment', {})
        features_data = vibey_data.get('features', {})

        return FrameworkConfig(
            framework=Framework(
                version=vibey_data.get('version', '2.5.0'),
                orchestration_mode=OrchestrationMode(
                    vibey_data.get('orchestration_mode', 'balanced')
                ),
                sprint_state_enabled=vibey_data.get('sprint_state_enabled', True),
                project_context_enabled=vibey_data.get('project_context_enabled', True)
            ),
            deployment=Deployment(
                platforms=deployment_data.get('platforms', ['claude-code']),
                auto_deploy=deployment_data.get('auto_deploy', False),
                deployment_dir=deployment_data.get('deployment_dir', '.claude')
            ),
            features=Features(
                roadmap_system=features_data.get('roadmap_system', True),
                documentation_generation=features_data.get('documentation_generation', True),
                codebase_audit=features_data.get('codebase_audit', True),
                git_history_analysis=features_data.get('git_history_analysis', True)
            )
        )

    def _extract_agents_config(self, legacy_data: dict) -> AgentsConfig:
        """Extract agents config from legacy format."""
        agents_data = legacy_data.get('agents', {})

        # Legacy used 'available' instead of 'enabled'
        enabled = agents_data.get('enabled', agents_data.get('available', []))

        return AgentsConfig(
            agents=Agents(
                enabled=enabled if enabled else ['coordinator'],
                disabled=agents_data.get('disabled', [])
            ),
            agent_preferences=agents_data.get('preferences', {})
        )

    def _extract_quality_gates_config(self, legacy_data: dict) -> QualityGatesConfig:
        """Extract quality gates config from legacy format."""
        qg_data = legacy_data.get('quality_gates', {})
        gates_data = qg_data.get('gates', {})

        return QualityGatesConfig(
            quality_gates=QualityGates(
                enabled=qg_data.get('enabled', True),
                mode=QualityGateMode(qg_data.get('mode', 'balanced'))
            ),
            gates=Gates(
                security=self._extract_gate_config(gates_data.get('security', {})),
                testing=self._extract_gate_config(gates_data.get('testing', {})),
                logging=self._extract_gate_config(gates_data.get('logging', {})),
                documentation=self._extract_gate_config(gates_data.get('documentation', {})),
                performance=self._extract_gate_config(gates_data.get('performance', {}))
            )
        )

    def _extract_gate_config(self, gate_data: dict) -> dict:
        """Extract individual gate config."""
        if not gate_data:
            return {}

        result = {
            'enabled': gate_data.get('enabled', True),
            'threshold': gate_data.get('threshold', 90),
            'blocking': gate_data.get('blocking', True)
        }

        # Special handling for specific gate types
        if 'checks' in gate_data:
            result['checks'] = gate_data['checks']
        if 'coverage_threshold' in gate_data:
            result['coverage_threshold'] = gate_data['coverage_threshold']

        return result


# Convenience function for simple usage
def load_config(project_root: Optional[Path] = None) -> VibeyConfig:
    """
    Load Vibey configuration with automatic fallback.

    Convenience function that creates a ConfigLoader and loads config.

    Args:
        project_root: Project root directory (default: current directory)

    Returns:
        VibeyConfig: Loaded configuration

    Raises:
        ConfigNotFoundError: No config files found
        ConfigValidationError: Config validation failed

    Example:
        from vibey.config import load_config

        config = load_config()
        print(f"Project: {config.project.project.name}")
    """
    loader = ConfigLoader()
    return loader.load_config(project_root)


__all__ = [
    'ConfigLoader',
    'ConfigLocation',
    'ConfigLoadError',
    'ConfigNotFoundError',
    'ConfigValidationError',
    'load_config',
]
