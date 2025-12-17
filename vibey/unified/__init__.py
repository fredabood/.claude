"""
Vibey Unified Command System.

Provides a single source of truth for CLI and MCP commands via the
@unified_command decorator. Commands defined once are automatically
available in both interfaces.

Example:
    from vibey.unified import unified_command, param, ParamType, CommandResult

    @unified_command(
        name="start_task",
        description="Mark a task as in progress",
        cli_group="roadmap",
    )
    @param("task_id", type=ParamType.STRING, required=True,
           help="Task ID to start", cli_option=False)
    @param("force", type=ParamType.BOOLEAN, default=False,
           help="Force start", cli_short="-f", cli_is_flag=True)
    def start_task(task_id: str, force: bool = False, root_dir=None):
        # Implementation calls operations layer
        from vibey.operations.roadmap import start_task as ops_start
        result = ops_start(root_dir, task_id)
        return CommandResult.ok(result, f"Started task {task_id}")
"""

from .command import CommandSpec, Interface, unified_command
from .param import ParamSpec, param
from .types import ParamType, param_to_click_type, param_to_json_schema
from .registry import CommandRegistry, COMMAND_REGISTRY
from .formatters import CommandResult, OutputFormatter, DefaultFormatter
from .parity import ParityChecker, ParityReport, ParityViolation, check_parity, format_parity_report

__all__ = [
    # Main decorators
    "unified_command",
    "param",
    # Types
    "ParamType",
    "Interface",
    # Specs
    "CommandSpec",
    "ParamSpec",
    # Registry
    "CommandRegistry",
    "COMMAND_REGISTRY",
    # Type conversion
    "param_to_click_type",
    "param_to_json_schema",
    # Results
    "CommandResult",
    "OutputFormatter",
    "DefaultFormatter",
    # Parity checking
    "ParityChecker",
    "ParityReport",
    "ParityViolation",
    "check_parity",
    "format_parity_report",
]
