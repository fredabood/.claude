"""
Auto-Estimation Trigger Service for the Vibey Agent Framework.

This service provides configurable automatic token estimation triggers with
multiple modes that users can select based on their workflow preferences.

Trigger Modes:
- DISABLED: No automatic estimation (manual estimation required)
- ON_CREATION: Auto-estimate when task is created via CLI or MCP
- ON_START_WARN: Warn on start if no estimate exists
- ON_CALIBRATION_UPDATE: Re-estimate when calibration changes significantly

Configuration is stored in .vibey/config/token_estimation.yaml under the
auto_estimation section.

Usage:
    from vibey.services.auto_estimation import (
        AutoEstimationConfig,
        AutoEstimationTrigger,
        on_task_created,
        on_task_status_change,
        on_calibration_updated,
        load_auto_estimation_config,
    )

    # Load project configuration
    config = load_auto_estimation_config()

    # In task creation flow
    on_task_created(task, config)

    # In task status change flow
    on_task_status_change(task, old_status, new_status, config)

    # After calibration update
    on_calibration_updated(old_calibration, new_calibration, config)

Design Reference: Sprint 4 - CLI & Reporting
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

import yaml
from pydantic import BaseModel, Field

from vibey.services.token_estimator import (
    TokenEstimator,
    CalibrationManager,
    CalibrationData,
    EstimationResult,
)

if TYPE_CHECKING:
    from vibey.roadmap.models.ticket import TaskTicket

# Configure module logger
logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION MODELS
# =============================================================================


class AutoEstimationTrigger(str, Enum):
    """Auto-estimation trigger modes.

    Defines when token estimation should be automatically triggered:
    - disabled: No auto-estimation (user must run estimate manually)
    - on_creation: Auto-estimate when task is created
    - on_start_warn: Warn on start if no estimate exists
    - on_calibration_update: Re-estimate when calibration changes significantly
    """

    DISABLED = "disabled"
    ON_CREATION = "on_creation"
    ON_START_WARN = "on_start_warn"
    ON_CALIBRATION_UPDATE = "on_calibration_update"


class AutoEstimationConfig(BaseModel):
    """Project-level auto-estimation settings.

    This configuration controls automatic token estimation behavior across
    the project. Settings are stored in .vibey/config/token_estimation.yaml.
    """

    trigger: AutoEstimationTrigger = Field(
        default=AutoEstimationTrigger.DISABLED,
        description="When to trigger automatic token estimation"
    )
    require_task_type: bool = Field(
        default=True,
        description="Require task_type to be set before auto-estimation"
    )
    require_complexity: bool = Field(
        default=True,
        description="Require complexity to be set before auto-estimation"
    )
    warn_on_start_missing: bool = Field(
        default=True,
        description="Warn when starting a task without an estimate"
    )
    re_estimate_threshold: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Re-estimate if calibration changes by this ratio (0.2 = 20%)"
    )
    exclude_task_types: List[str] = Field(
        default_factory=list,
        description="Task types to exclude from auto-estimation"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return {
            "trigger": self.trigger.value,
            "require_task_type": self.require_task_type,
            "require_complexity": self.require_complexity,
            "warn_on_start_missing": self.warn_on_start_missing,
            "re_estimate_threshold": self.re_estimate_threshold,
            "exclude_task_types": self.exclude_task_types,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AutoEstimationConfig":
        """Create from dictionary (YAML deserialization)."""
        trigger_value = data.get("trigger", "disabled")
        try:
            trigger = AutoEstimationTrigger(trigger_value)
        except ValueError:
            logger.warning(
                f"Unknown trigger value '{trigger_value}', defaulting to disabled"
            )
            trigger = AutoEstimationTrigger.DISABLED

        return cls(
            trigger=trigger,
            require_task_type=data.get("require_task_type", True),
            require_complexity=data.get("require_complexity", True),
            warn_on_start_missing=data.get("warn_on_start_missing", True),
            re_estimate_threshold=data.get("re_estimate_threshold", 0.2),
            exclude_task_types=data.get("exclude_task_types", []),
        )


# =============================================================================
# CONFIGURATION LOADING
# =============================================================================


DEFAULT_CONFIG_PATH = Path(".vibey/config/token_estimation.yaml")


def load_auto_estimation_config(
    root_dir: Optional[Path] = None,
    config_path: Optional[Path] = None,
) -> AutoEstimationConfig:
    """
    Load auto-estimation configuration from project config file.

    Args:
        root_dir: Root directory containing .vibey/ (defaults to cwd)
        config_path: Path to config file (defaults to .vibey/config/token_estimation.yaml)

    Returns:
        AutoEstimationConfig with loaded or default settings
    """
    root_dir = root_dir or Path.cwd()
    config_path = config_path or (root_dir / DEFAULT_CONFIG_PATH)

    if not config_path.exists():
        logger.debug(f"Config file not found at {config_path}, using defaults")
        return AutoEstimationConfig()

    try:
        with open(config_path, "r") as f:
            data = yaml.safe_load(f) or {}

        auto_estimation_data = data.get("auto_estimation", {})
        return AutoEstimationConfig.from_dict(auto_estimation_data)

    except Exception as e:
        logger.warning(f"Failed to load config from {config_path}: {e}")
        return AutoEstimationConfig()


def save_auto_estimation_config(
    config: AutoEstimationConfig,
    root_dir: Optional[Path] = None,
    config_path: Optional[Path] = None,
) -> None:
    """
    Save auto-estimation configuration to project config file.

    Args:
        config: AutoEstimationConfig to save
        root_dir: Root directory containing .vibey/ (defaults to cwd)
        config_path: Path to config file (defaults to .vibey/config/token_estimation.yaml)
    """
    root_dir = root_dir or Path.cwd()
    config_path = config_path or (root_dir / DEFAULT_CONFIG_PATH)

    # Load existing config to preserve other settings
    existing_data = {}
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                existing_data = yaml.safe_load(f) or {}
        except Exception:
            pass

    # Update auto_estimation section
    existing_data["auto_estimation"] = config.to_dict()

    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Write config
    with open(config_path, "w") as f:
        yaml.dump(
            existing_data,
            f,
            default_flow_style=False,
            sort_keys=False,
        )


# =============================================================================
# HOOK IMPLEMENTATIONS
# =============================================================================


def on_task_created(
    task: Any,
    config: Optional[AutoEstimationConfig] = None,
    root_dir: Optional[Path] = None,
    estimator: Optional[TokenEstimator] = None,
) -> Optional[EstimationResult]:
    """
    Hook called when a task is created.

    Auto-estimates token usage if:
    - trigger is ON_CREATION or ON_CALIBRATION_UPDATE
    - task_type is set (when require_task_type is True)
    - complexity is set (when require_complexity is True)
    - task_type is not in exclude_task_types

    Args:
        task: Task object (TaskTicket or legacy Task) that was created
        config: Auto-estimation configuration (loads from file if None)
        root_dir: Root directory for loading config
        estimator: Optional TokenEstimator instance (creates new if None)

    Returns:
        EstimationResult if estimation was performed, None otherwise
    """
    root_dir = root_dir or Path.cwd()
    config = config or load_auto_estimation_config(root_dir)

    # Check if trigger is enabled for creation
    if config.trigger not in [
        AutoEstimationTrigger.ON_CREATION,
        AutoEstimationTrigger.ON_CALIBRATION_UPDATE,
    ]:
        logger.debug("Auto-estimation not triggered on creation (trigger=%s)", config.trigger)
        return None

    # Get task properties
    task_type = _get_task_type(task)
    complexity = _get_complexity(task)

    # Check prerequisites
    if config.require_task_type and not task_type:
        logger.debug("Skipping auto-estimation: task_type not set")
        return None

    if config.require_complexity and not complexity:
        logger.debug("Skipping auto-estimation: complexity not set")
        return None

    # Check exclusions
    if task_type and task_type.lower() in [t.lower() for t in config.exclude_task_types]:
        logger.debug(f"Skipping auto-estimation: task_type '{task_type}' is excluded")
        return None

    # Perform estimation using estimate_from_description to handle task_type_detail
    estimator = estimator or TokenEstimator()
    description = getattr(task, 'description', '') or ''
    result = estimator.estimate_from_description(
        description=description,
        task_type=task_type,
        complexity=complexity or "medium",
    )

    # Apply estimates to task
    estimator.apply_estimates(task, result)

    logger.info(
        f"Auto-estimated tokens for task {_get_task_id(task)}: "
        f"input={result.input_estimate.target}, output={result.output_estimate.target}"
    )

    return result


def on_task_status_change(
    task: Any,
    old_status: str,
    new_status: str,
    config: Optional[AutoEstimationConfig] = None,
    root_dir: Optional[Path] = None,
) -> bool:
    """
    Hook called when a task status changes.

    Warns if:
    - trigger is ON_START_WARN or ON_CALIBRATION_UPDATE
    - new_status is 'in_progress'
    - warn_on_start_missing is True
    - task has no token estimate

    Args:
        task: Task object that changed status
        old_status: Previous status value
        new_status: New status value
        config: Auto-estimation configuration (loads from file if None)
        root_dir: Root directory for loading config

    Returns:
        True if a warning was issued, False otherwise
    """
    root_dir = root_dir or Path.cwd()
    config = config or load_auto_estimation_config(root_dir)

    # Only warn on start (in_progress transition)
    if new_status != "in_progress":
        return False

    # Check if trigger supports warning on start
    if config.trigger not in [
        AutoEstimationTrigger.ON_START_WARN,
        AutoEstimationTrigger.ON_CALIBRATION_UPDATE,
    ]:
        return False

    if not config.warn_on_start_missing:
        return False

    # Check if task has estimate
    has_estimate = _has_token_estimate(task)

    if not has_estimate:
        task_id = _get_task_id(task)
        logger.warning(
            f"Task {task_id} started without token estimate. "
            f"Run 'vibey roadmap estimate {task_id}' to set estimates."
        )
        return True

    return False


def on_calibration_updated(
    old_calibration: Optional[CalibrationData],
    new_calibration: CalibrationData,
    config: Optional[AutoEstimationConfig] = None,
    root_dir: Optional[Path] = None,
    get_unstarted_tasks: Optional[Callable[..., List[Any]]] = None,
) -> int:
    """
    Hook called when calibration data is updated.

    Re-estimates unstarted tasks if:
    - trigger is ON_CALIBRATION_UPDATE
    - calibration changed significantly (> re_estimate_threshold)

    Args:
        old_calibration: Previous calibration data (None if first calibration)
        new_calibration: New calibration data
        config: Auto-estimation configuration (loads from file if None)
        root_dir: Root directory for loading config
        get_unstarted_tasks: Callable to get unstarted tasks of a given type

    Returns:
        Number of tasks re-estimated
    """
    root_dir = root_dir or Path.cwd()
    config = config or load_auto_estimation_config(root_dir)

    # Only re-estimate on calibration update mode
    if config.trigger != AutoEstimationTrigger.ON_CALIBRATION_UPDATE:
        return 0

    if old_calibration is None:
        # First calibration, no comparison possible
        return 0

    if get_unstarted_tasks is None:
        logger.debug("No get_unstarted_tasks callback provided, skipping re-estimation")
        return 0

    # Check which task types have significant calibration changes
    changed_types = []
    for key, new_factor in new_calibration.factors.items():
        old_factor = old_calibration.factors.get(key)

        if old_factor is None:
            # New type, not a change
            continue

        # Check if change exceeds threshold
        input_change = abs(new_factor.input_factor - old_factor.input_factor)
        output_change = abs(new_factor.output_factor - old_factor.output_factor)

        avg_old = (old_factor.input_factor + old_factor.output_factor) / 2
        if avg_old > 0:
            relative_change = max(input_change, output_change) / avg_old
            if relative_change > config.re_estimate_threshold:
                task_type = new_factor.task_type
                if task_type not in [t.lower() for t in config.exclude_task_types]:
                    changed_types.append(task_type)
                    logger.info(
                        f"Calibration change detected for {key}: "
                        f"input {old_factor.input_factor:.2f} -> {new_factor.input_factor:.2f}, "
                        f"output {old_factor.output_factor:.2f} -> {new_factor.output_factor:.2f}"
                    )

    if not changed_types:
        return 0

    # Re-estimate affected tasks
    estimator = TokenEstimator(
        calibration_manager=CalibrationManager(root_dir=root_dir)
    )

    re_estimated_count = 0
    for task_type in changed_types:
        try:
            unstarted_tasks = get_unstarted_tasks(task_type=task_type, status="not_started")

            for task in unstarted_tasks:
                # Check prerequisites
                if config.require_task_type and not _get_task_type(task):
                    continue
                if config.require_complexity and not _get_complexity(task):
                    continue

                result = estimator.estimate_task(task)
                estimator.apply_estimates(task, result)

                task_id = _get_task_id(task)
                logger.info(f"Re-estimated {task_id} due to calibration update")
                re_estimated_count += 1

        except Exception as e:
            logger.error(f"Failed to re-estimate tasks of type {task_type}: {e}")

    return re_estimated_count


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def _get_task_type(task: Any) -> Optional[str]:
    """Extract task type from task object."""
    # Try task_type_detail first (v2 format)
    task_type = getattr(task, "task_type_detail", None)
    if task_type:
        if hasattr(task_type, "value"):
            return task_type.value
        return str(task_type)

    # Fall back to task_type (v1 format)
    task_type = getattr(task, "task_type", None)
    if task_type:
        if hasattr(task_type, "value"):
            return task_type.value
        return str(task_type)

    return None


def _get_complexity(task: Any) -> Optional[str]:
    """Extract complexity from task object."""
    complexity = getattr(task, "complexity", None)
    if complexity:
        if hasattr(complexity, "value"):
            return complexity.value
        return str(complexity)
    return None


def _get_task_id(task: Any) -> str:
    """Extract task ID from task object."""
    return getattr(task, "id", "unknown")


def _has_token_estimate(task: Any) -> bool:
    """Check if task has token estimates set."""
    input_tokens = getattr(task, "input_tokens", None)
    output_tokens = getattr(task, "output_tokens", None)

    # Check for estimate in input_tokens
    if input_tokens:
        estimate = getattr(input_tokens, "estimate", None)
        if estimate and getattr(estimate, "target", None):
            return True

    # Check for estimate in output_tokens
    if output_tokens:
        estimate = getattr(output_tokens, "estimate", None)
        if estimate and getattr(estimate, "target", None):
            return True

    return False


def estimate_task_tokens(
    task_id: str,
    root_dir: Optional[Path] = None,
    force: bool = False,
) -> Optional[EstimationResult]:
    """
    Estimate tokens for a specific task by ID.

    This is a convenience function that:
    1. Loads the task from YAML
    2. Runs token estimation
    3. Saves the updated task

    Args:
        task_id: Task ID (ULID or legacy format)
        root_dir: Root directory containing .vibey/
        force: If True, overwrite existing estimates

    Returns:
        EstimationResult if successful, None otherwise
    """
    root_dir = root_dir or Path.cwd()

    try:
        # Import here to avoid circular imports
        from vibey.operations.roadmap.query import load_task_ticket
        from vibey.roadmap.serialization.yaml_dumper import save_task_ticket

        # Load task
        task = load_task_ticket(root_dir, task_id)

        # Check for existing estimate
        if not force and _has_token_estimate(task):
            logger.info(f"Task {task_id} already has estimates, use force=True to overwrite")
            return None

        # Create estimator with calibration
        calibration_manager = CalibrationManager(root_dir=root_dir)
        estimator = TokenEstimator(calibration_manager=calibration_manager)

        # Estimate
        result = estimator.estimate_task(task)
        estimator.apply_estimates(task, result)

        # Save task
        task_path = root_dir / ".vibey" / "roadmap" / "tasks" / f"{task_id}.yaml"
        save_task_ticket(task, task_path)

        logger.info(
            f"Estimated tokens for {task_id}: "
            f"input={result.input_estimate.target}, output={result.output_estimate.target}"
        )

        return result

    except FileNotFoundError:
        logger.error(f"Task {task_id} not found")
        return None
    except Exception as e:
        logger.error(f"Failed to estimate tokens for {task_id}: {e}")
        return None


# =============================================================================
# EXPORTS
# =============================================================================


__all__ = [
    # Configuration models
    "AutoEstimationTrigger",
    "AutoEstimationConfig",
    # Configuration loading
    "load_auto_estimation_config",
    "save_auto_estimation_config",
    # Hooks
    "on_task_created",
    "on_task_status_change",
    "on_calibration_updated",
    # Convenience functions
    "estimate_task_tokens",
    # Constants
    "DEFAULT_CONFIG_PATH",
]
