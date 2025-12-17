"""
Parameter specification and decorator for unified commands.

The @param decorator defines parameters that work across both CLI and MCP
interfaces, with interface-specific options for customization.
"""

from dataclasses import dataclass
from typing import Any, Callable, List, Optional, TypeVar

from .types import ParamType


@dataclass
class ParamSpec:
    """
    Specification for a command parameter.

    Defines a parameter once with all information needed to generate
    both Click options/arguments and MCP tool input schemas.

    Attributes:
        name: Parameter name (used in function signature)
        type: Unified parameter type
        required: Whether the parameter is required
        default: Default value if not provided
        help: Help text (used in both CLI and MCP)
        choices: Valid choices for CHOICE type
        item_type: Item type for LIST type
        cli_option: True for --option style, False for positional argument
        cli_short: Short option name (e.g., "-f")
        cli_is_flag: True for boolean flags (--flag vs --flag=value)
        cli_prompt: Interactive prompt text (CLI only)
        mcp_description: Override description for MCP (if different from help)
    """

    name: str
    type: ParamType = ParamType.STRING
    required: bool = True
    default: Any = None
    help: str = ""

    # For CHOICE type
    choices: Optional[List[str]] = None

    # For LIST type
    item_type: Optional[ParamType] = None

    # CLI-specific options
    cli_option: bool = True
    cli_short: Optional[str] = None
    cli_is_flag: bool = False
    cli_prompt: Optional[str] = None

    # MCP-specific options
    mcp_description: Optional[str] = None


F = TypeVar("F", bound=Callable[..., Any])


def param(
    name: str,
    *,
    type: ParamType = ParamType.STRING,
    required: bool = True,
    default: Any = None,
    help: str = "",
    choices: Optional[List[str]] = None,
    item_type: Optional[ParamType] = None,
    cli_option: bool = True,
    cli_short: Optional[str] = None,
    cli_is_flag: bool = False,
    cli_prompt: Optional[str] = None,
    mcp_description: Optional[str] = None,
) -> Callable[[F], F]:
    """
    Decorator to define a parameter for a unified command.

    Must be applied BEFORE @unified_command (i.e., closer to the function).
    Multiple @param decorators can be stacked to define multiple parameters.

    Example:
        @unified_command(name="start_task", ...)
        @param("task_id", type=ParamType.STRING, required=True,
               help="Task ID to start", cli_option=False)
        @param("force", type=ParamType.BOOLEAN, default=False,
               help="Force start", cli_short="-f", cli_is_flag=True)
        def start_task(task_id: str, force: bool = False):
            ...

    Args:
        name: Parameter name (must match function argument name)
        type: Unified parameter type
        required: Whether parameter is required
        default: Default value
        help: Help text for both interfaces
        choices: Valid choices for CHOICE type
        item_type: Item type for LIST type
        cli_option: True for --option, False for positional argument
        cli_short: Short option (e.g., "-f")
        cli_is_flag: True for boolean flags
        cli_prompt: Interactive prompt (CLI only)
        mcp_description: Override description for MCP

    Returns:
        Decorator function
    """
    def decorator(func: F) -> F:
        # Initialize params list if not present
        if not hasattr(func, "_unified_params"):
            func._unified_params = []  # type: ignore

        spec = ParamSpec(
            name=name,
            type=type,
            required=required,
            default=default,
            help=help,
            choices=choices,
            item_type=item_type,
            cli_option=cli_option,
            cli_short=cli_short,
            cli_is_flag=cli_is_flag,
            cli_prompt=cli_prompt,
            mcp_description=mcp_description,
        )

        # Insert at beginning because decorators are applied bottom-up
        func._unified_params.insert(0, spec)  # type: ignore

        return func

    return decorator
