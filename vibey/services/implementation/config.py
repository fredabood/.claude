"""
Configuration system for Implementation Mode.

This module provides comprehensive configuration management for the autonomous
implementation loop, including:
- YAML-based configuration with sensible defaults
- CLI option merging for runtime overrides
- Validation of all configuration values
- Support for retry behavior, task selection, and agent configuration

Usage:
    from vibey.services.implementation.config import ImplementConfig
    from pathlib import Path

    # Load from default location (.vibey/config/implement.yaml)
    config = ImplementConfig.load()

    # Load from custom path
    config = ImplementConfig.load(Path("/custom/config.yaml"))

    # Override with CLI options
    config = config.merge_cli_options(
        max_tasks=5,
        timeout=300,
    )

Configuration file: .vibey/config/implement.yaml
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, replace
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================


class Priority(str, Enum):
    """Task priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Complexity(str, Enum):
    """Task complexity levels."""
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class RetryCondition(str, Enum):
    """Conditions that trigger retry behavior."""
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    NETWORK_ERROR = "network_error"
    API_ERROR = "api_error"


class SkipCondition(str, Enum):
    """Conditions that skip retry and mark task as blocked."""
    SYNTAX_ERROR = "syntax_error"
    IMPORT_ERROR = "import_error"
    VALIDATION_ERROR = "validation_error"
    PERMISSION_ERROR = "permission_error"


# =============================================================================
# CONFIGURATION ERRORS
# =============================================================================


class ImplementConfigError(Exception):
    """Base exception for configuration errors."""
    pass


class ConfigValidationError(ImplementConfigError):
    """Raised when configuration values are invalid."""

    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(f"Configuration validation failed: {'; '.join(errors)}")


class ConfigLoadError(ImplementConfigError):
    """Raised when configuration file cannot be loaded."""

    def __init__(self, path: Path, reason: str):
        self.path = path
        self.reason = reason
        super().__init__(f"Failed to load config from {path}: {reason}")


# =============================================================================
# SUB-CONFIGURATIONS
# =============================================================================


@dataclass(frozen=True)
class RetryConfig:
    """
    Configuration for retry behavior.

    Attributes:
        max_retries: Maximum number of retry attempts per task
        retry_on: Conditions that trigger a retry
        skip_on: Conditions that skip retry and block the task
    """
    max_retries: int = 2
    retry_on: tuple[str, ...] = ("timeout", "rate_limit")
    skip_on: tuple[str, ...] = ("syntax_error", "import_error")

    def should_retry(self, condition: str) -> bool:
        """Check if the given condition should trigger a retry."""
        return condition.lower() in [c.lower() for c in self.retry_on]

    def should_skip(self, condition: str) -> bool:
        """Check if the given condition should skip retry."""
        return condition.lower() in [c.lower() for c in self.skip_on]


@dataclass(frozen=True)
class SelectionConfig:
    """
    Configuration for task selection behavior.

    Attributes:
        priority_order: Order of priority levels for task selection
        prefer_smaller_tasks: Whether to prefer smaller/simpler tasks
        exclude_complexity: Complexity levels to exclude from selection
    """
    priority_order: tuple[str, ...] = ("critical", "high", "medium", "low")
    prefer_smaller_tasks: bool = True
    exclude_complexity: tuple[str, ...] = ("very_complex",)

    def is_complexity_excluded(self, complexity: str) -> bool:
        """Check if a complexity level is excluded."""
        return complexity.lower() in [c.lower() for c in self.exclude_complexity]


@dataclass(frozen=True)
class AgentConfig:
    """
    Configuration for the AI agent.

    Attributes:
        model: Model identifier to use for execution
        dangerously_skip_permissions: Skip permission checks (use with caution)
        print_output: Whether to print agent output to console
        max_turns: Maximum conversation turns per task
    """
    model: str = "claude-sonnet-4-20250514"
    dangerously_skip_permissions: bool = True
    print_output: bool = True
    max_turns: int = 50


# =============================================================================
# MAIN CONFIGURATION
# =============================================================================


@dataclass
class ImplementConfig:
    """
    Configuration for the implementation loop.

    This class provides comprehensive configuration for autonomous task execution,
    including execution limits, retry behavior, task selection, and agent settings.

    The configuration can be loaded from a YAML file (.vibey/config/implement.yaml)
    or created programmatically with defaults. CLI options can override any setting.

    Attributes:
        max_tasks_per_session: Maximum tasks to execute in one session (None = unlimited)
        max_tokens_per_session: Maximum total tokens to consume (None = unlimited)
        max_tokens_per_task: Maximum tokens for a single task
        timeout_per_task: Timeout in seconds for each task
        state_path: Path for persisting loop state
        track_id: Optional track ULID to filter tasks
        sprint_id: Optional sprint ULID to filter tasks
        auto_save: Whether to auto-save state after each task
        save_interval: How often to save state during long tasks (seconds)
        retry: Retry behavior configuration
        selection: Task selection configuration
        agent: Agent configuration

    Example:
        >>> config = ImplementConfig.load()
        >>> config = config.merge_cli_options(max_tasks_per_session=5)
        >>> print(config.max_tasks_per_session)
        5
    """

    # Execution limits
    max_tasks_per_session: Optional[int] = 10
    max_tokens_per_session: Optional[int] = 100000
    max_tokens_per_task: int = 25000
    timeout_per_task: int = 600  # seconds

    # State management
    state_path: Optional[Path] = None
    track_id: Optional[str] = None
    sprint_id: Optional[str] = None
    auto_save: bool = True
    save_interval: int = 60  # seconds

    # Sub-configurations
    retry: RetryConfig = field(default_factory=RetryConfig)
    selection: SelectionConfig = field(default_factory=SelectionConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)

    # Compatibility aliases (for existing ImplementConfig in loop.py)
    @property
    def max_tasks(self) -> Optional[int]:
        """Alias for max_tasks_per_session (backward compatibility)."""
        return self.max_tasks_per_session

    @property
    def max_tokens(self) -> Optional[int]:
        """Alias for max_tokens_per_session (backward compatibility)."""
        return self.max_tokens_per_session

    # =========================================================================
    # LOADING
    # =========================================================================

    @classmethod
    def load(
        cls,
        config_path: Optional[Path] = None,
        project_root: Optional[Path] = None,
    ) -> "ImplementConfig":
        """
        Load configuration from YAML file.

        If no config_path is provided, looks for .vibey/config/implement.yaml
        in the project root (or current directory).

        If the config file doesn't exist, returns a config with default values.

        Args:
            config_path: Direct path to config file (optional)
            project_root: Project root directory (default: current directory)

        Returns:
            ImplementConfig loaded from file or defaults

        Raises:
            ConfigLoadError: If file exists but cannot be parsed
            ConfigValidationError: If configuration values are invalid
        """
        # Determine config path
        if config_path is None:
            if project_root is None:
                project_root = Path.cwd()
            config_path = project_root / ".vibey" / "config" / "implement.yaml"

        # If file doesn't exist, return defaults
        if not config_path.exists():
            logger.debug(f"Config file not found at {config_path}, using defaults")
            return cls()

        # Load from YAML
        try:
            with open(config_path, "r") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigLoadError(config_path, f"YAML parse error: {e}")
        except IOError as e:
            raise ConfigLoadError(config_path, f"IO error: {e}")

        if not data:
            logger.debug(f"Config file {config_path} is empty, using defaults")
            return cls()

        # Parse and validate
        return cls._from_dict(data, config_path)

    @classmethod
    def _from_dict(cls, data: Dict[str, Any], source_path: Path) -> "ImplementConfig":
        """
        Create config from dictionary (parsed YAML).

        Args:
            data: Dictionary from YAML parsing
            source_path: Source file path for error messages

        Returns:
            ImplementConfig instance

        Raises:
            ConfigValidationError: If values are invalid
        """
        # Extract implement section if present (supports both flat and nested)
        if "implement" in data:
            data = data["implement"]

        errors: List[str] = []

        # Parse defaults section
        defaults = data.get("defaults", {})
        max_tasks = defaults.get("max_tasks_per_session", 10)
        max_tokens_session = defaults.get("max_tokens_per_session", 100000)
        max_tokens_task = defaults.get("max_tokens_per_task", 25000)
        timeout = defaults.get("timeout_per_task", 600)

        # Validate execution limits
        if max_tasks is not None and max_tasks < 1:
            errors.append("max_tasks_per_session must be >= 1 or None")
        if max_tokens_session is not None and max_tokens_session < 1000:
            errors.append("max_tokens_per_session must be >= 1000 or None")
        if max_tokens_task < 1000:
            errors.append("max_tokens_per_task must be >= 1000")
        if timeout < 10:
            errors.append("timeout_per_task must be >= 10 seconds")

        # Parse retry section
        retry_data = data.get("retry", {})
        max_retries = retry_data.get("max_retries", 2)
        retry_on = tuple(retry_data.get("retry_on", ["timeout", "rate_limit"]))
        skip_on = tuple(retry_data.get("skip_on", ["syntax_error", "import_error"]))

        if max_retries < 0:
            errors.append("max_retries must be >= 0")

        retry_config = RetryConfig(
            max_retries=max_retries,
            retry_on=retry_on,
            skip_on=skip_on,
        )

        # Parse selection section
        selection_data = data.get("selection", {})
        priority_order = tuple(
            selection_data.get("priority_order", ["critical", "high", "medium", "low"])
        )
        prefer_smaller = selection_data.get("prefer_smaller_tasks", True)
        exclude_complexity = tuple(
            selection_data.get("exclude_complexity", ["very_complex"])
        )

        selection_config = SelectionConfig(
            priority_order=priority_order,
            prefer_smaller_tasks=prefer_smaller,
            exclude_complexity=exclude_complexity,
        )

        # Parse agent section
        agent_data = data.get("agent", {})
        model = agent_data.get("model", "claude-sonnet-4-20250514")
        skip_permissions = agent_data.get("dangerously_skip_permissions", True)
        print_output = agent_data.get("print_output", True)
        max_turns = agent_data.get("max_turns", 50)

        if not model:
            errors.append("agent.model must not be empty")
        if max_turns < 1:
            errors.append("agent.max_turns must be >= 1")

        agent_config = AgentConfig(
            model=model,
            dangerously_skip_permissions=skip_permissions,
            print_output=print_output,
            max_turns=max_turns,
        )

        # Raise if validation errors
        if errors:
            raise ConfigValidationError(errors)

        return cls(
            max_tasks_per_session=max_tasks,
            max_tokens_per_session=max_tokens_session,
            max_tokens_per_task=max_tokens_task,
            timeout_per_task=timeout,
            retry=retry_config,
            selection=selection_config,
            agent=agent_config,
        )

    # =========================================================================
    # MERGING
    # =========================================================================

    def merge_cli_options(self, **kwargs: Any) -> "ImplementConfig":
        """
        Override configuration with CLI options.

        Only non-None values in kwargs will override the current config.
        This allows CLI options to selectively override specific settings.

        Args:
            **kwargs: CLI options to override. Supported options:
                - max_tasks: Override max_tasks_per_session
                - max_tokens: Override max_tokens_per_session
                - max_tokens_per_task: Override max_tokens_per_task
                - timeout: Override timeout_per_task
                - track_id: Override track_id filter
                - sprint_id: Override sprint_id filter
                - state_path: Override state_path
                - model: Override agent.model
                - print_output: Override agent.print_output

        Returns:
            New ImplementConfig with merged options

        Example:
            >>> config = ImplementConfig.load()
            >>> config = config.merge_cli_options(
            ...     max_tasks=5,
            ...     timeout=300,
            ...     model="claude-opus-4-20250514",
            ... )
        """
        # Map CLI option names to config field names
        field_mapping = {
            "max_tasks": "max_tasks_per_session",
            "max_tokens": "max_tokens_per_session",
            "timeout": "timeout_per_task",
        }

        # Build replacement dict for direct fields
        replacements: Dict[str, Any] = {}

        for cli_name, value in kwargs.items():
            if value is None:
                continue

            # Map to field name
            field_name = field_mapping.get(cli_name, cli_name)

            # Handle agent sub-config fields
            if field_name in ("model", "print_output", "max_turns"):
                continue  # Handle separately below

            # Handle path conversion
            if field_name == "state_path" and value is not None:
                value = Path(value) if not isinstance(value, Path) else value

            replacements[field_name] = value

        # Handle agent config updates
        agent_updates = {}
        if kwargs.get("model") is not None:
            agent_updates["model"] = kwargs["model"]
        if kwargs.get("print_output") is not None:
            agent_updates["print_output"] = kwargs["print_output"]
        if kwargs.get("max_turns") is not None:
            agent_updates["max_turns"] = kwargs["max_turns"]

        if agent_updates:
            # Create new AgentConfig with updates
            new_agent = AgentConfig(
                model=agent_updates.get("model", self.agent.model),
                dangerously_skip_permissions=self.agent.dangerously_skip_permissions,
                print_output=agent_updates.get("print_output", self.agent.print_output),
                max_turns=agent_updates.get("max_turns", self.agent.max_turns),
            )
            replacements["agent"] = new_agent

        # Create new config with replacements
        return replace(self, **replacements)

    # =========================================================================
    # VALIDATION
    # =========================================================================

    def validate(self) -> List[str]:
        """
        Validate configuration values.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors: List[str] = []

        # Validate execution limits
        if self.max_tasks_per_session is not None and self.max_tasks_per_session < 1:
            errors.append("max_tasks_per_session must be >= 1 or None")

        if (
            self.max_tokens_per_session is not None
            and self.max_tokens_per_session < 1000
        ):
            errors.append("max_tokens_per_session must be >= 1000 or None")

        if self.max_tokens_per_task < 1000:
            errors.append("max_tokens_per_task must be >= 1000")

        if self.timeout_per_task < 10:
            errors.append("timeout_per_task must be >= 10 seconds")

        # Validate retry config
        if self.retry.max_retries < 0:
            errors.append("retry.max_retries must be >= 0")

        # Validate agent config
        if not self.agent.model:
            errors.append("agent.model must not be empty")

        if self.agent.max_turns < 1:
            errors.append("agent.max_turns must be >= 1")

        return errors

    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return len(self.validate()) == 0

    # =========================================================================
    # SERIALIZATION
    # =========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Dictionary representation suitable for YAML serialization
        """
        return {
            "implement": {
                "defaults": {
                    "max_tasks_per_session": self.max_tasks_per_session,
                    "max_tokens_per_session": self.max_tokens_per_session,
                    "max_tokens_per_task": self.max_tokens_per_task,
                    "timeout_per_task": self.timeout_per_task,
                },
                "retry": {
                    "max_retries": self.retry.max_retries,
                    "retry_on": list(self.retry.retry_on),
                    "skip_on": list(self.retry.skip_on),
                },
                "selection": {
                    "priority_order": list(self.selection.priority_order),
                    "prefer_smaller_tasks": self.selection.prefer_smaller_tasks,
                    "exclude_complexity": list(self.selection.exclude_complexity),
                },
                "agent": {
                    "model": self.agent.model,
                    "dangerously_skip_permissions": self.agent.dangerously_skip_permissions,
                    "print_output": self.agent.print_output,
                    "max_turns": self.agent.max_turns,
                },
            }
        }

    def save(self, path: Path) -> None:
        """
        Save configuration to YAML file.

        Args:
            path: Path to save configuration to
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.dump(
                self.to_dict(),
                f,
                default_flow_style=False,
                sort_keys=False,
            )
        logger.info(f"Saved configuration to {path}")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def load_implement_config(
    config_path: Optional[Path] = None,
    project_root: Optional[Path] = None,
) -> ImplementConfig:
    """
    Load implementation configuration.

    Convenience function that wraps ImplementConfig.load().

    Args:
        config_path: Direct path to config file (optional)
        project_root: Project root directory (default: current directory)

    Returns:
        ImplementConfig loaded from file or defaults
    """
    return ImplementConfig.load(config_path, project_root)


def get_default_config_path(project_root: Optional[Path] = None) -> Path:
    """
    Get the default configuration file path.

    Args:
        project_root: Project root directory (default: current directory)

    Returns:
        Path to .vibey/config/implement.yaml
    """
    if project_root is None:
        project_root = Path.cwd()
    return project_root / ".vibey" / "config" / "implement.yaml"


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Main config
    "ImplementConfig",
    # Sub-configs
    "RetryConfig",
    "SelectionConfig",
    "AgentConfig",
    # Enums
    "Priority",
    "Complexity",
    "RetryCondition",
    "SkipCondition",
    # Errors
    "ImplementConfigError",
    "ConfigValidationError",
    "ConfigLoadError",
    # Functions
    "load_implement_config",
    "get_default_config_path",
]
