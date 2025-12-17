"""
Command specification and decorator for unified CLI/MCP commands.

The @unified_command decorator creates a single source of truth for
commands, automatically registering them to both CLI and MCP interfaces.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, List, Optional, TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from .param import ParamSpec
    from .formatters.base import OutputFormatter


class Interface(Enum):
    """Available interfaces for command registration."""

    CLI = "cli"
    MCP = "mcp"


@dataclass
class CommandSpec:
    """
    Specification for a unified command.

    Contains all information needed to generate both CLI commands
    and MCP tools from a single definition.

    Attributes:
        name: Internal command name (e.g., "start_task")
        description: Help text (shared by both interfaces)
        operation: The underlying function to call
        params: List of parameter specifications
        interfaces: Which interfaces to register to
        cli_group: CLI group name (e.g., "roadmap" for `vibey roadmap start`)
        cli_name: Override command name in CLI
        mcp_name: Override tool name in MCP (default: vibey_{name})
        mcp_category: Category for organizing MCP tools
        formatter: Custom output formatter
        exclusion_reason: Why command is excluded from an interface
    """

    name: str
    description: str
    operation: Callable[..., Any]
    params: List["ParamSpec"] = field(default_factory=list)
    interfaces: List[Interface] = field(
        default_factory=lambda: [Interface.CLI, Interface.MCP]
    )

    # CLI-specific options
    cli_group: Optional[str] = None
    cli_name: Optional[str] = None

    # MCP-specific options
    mcp_name: Optional[str] = None
    mcp_category: Optional[str] = None

    # Output handling
    formatter: Optional["OutputFormatter"] = None

    # Documentation for parity checker
    exclusion_reason: Optional[str] = None

    @property
    def cli_command_name(self) -> str:
        """Get the CLI command name (with dashes)."""
        return self.cli_name or self.name.replace("_", "-")

    @property
    def mcp_tool_name(self) -> str:
        """Get the MCP tool name."""
        return self.mcp_name or f"vibey_{self.name}"

    def is_available_in(self, interface: Interface) -> bool:
        """Check if command is available in the given interface."""
        return interface in self.interfaces


F = TypeVar("F", bound=Callable[..., Any])


def unified_command(
    name: str,
    description: str,
    *,
    interfaces: Optional[List[str]] = None,
    cli_group: Optional[str] = None,
    cli_name: Optional[str] = None,
    mcp_name: Optional[str] = None,
    mcp_category: Optional[str] = None,
    exclusion_reason: Optional[str] = None,
) -> Callable[[F], F]:
    """
    Decorator to define a unified command for both CLI and MCP.

    By default, commands are registered to both interfaces. Use the
    `interfaces` parameter to restrict to specific interfaces.

    Example:
        # Available in both CLI and MCP (default)
        @unified_command(
            name="start_task",
            description="Mark a task as in progress",
            cli_group="roadmap",
        )
        @param("task_id", type=ParamType.STRING, required=True)
        def start_task(task_id: str, root_dir=None):
            return start_task_operation(root_dir, task_id)

        # CLI only (interactive feature)
        @unified_command(
            name="wizard",
            description="Interactive setup wizard",
            interfaces=["cli"],
            exclusion_reason="Interactive prompts not supported in MCP",
        )
        def wizard():
            ...

        # MCP only (agent-specific)
        @unified_command(
            name="agent_handoff",
            description="Hand off context to another agent",
            interfaces=["mcp"],
            exclusion_reason="Agent-specific context operation",
        )
        def agent_handoff():
            ...

    Args:
        name: Internal command name (e.g., "start_task")
        description: Help text for both interfaces
        interfaces: List of interfaces ["cli", "mcp"] (default: both)
        cli_group: CLI group (e.g., "roadmap" for `vibey roadmap ...`)
        cli_name: Override CLI command name
        mcp_name: Override MCP tool name
        mcp_category: Category for MCP tool organization
        exclusion_reason: Reason for interface exclusion (for parity reports)

    Returns:
        Decorator function
    """
    # Parse interfaces
    if interfaces is None:
        parsed_interfaces = [Interface.CLI, Interface.MCP]
    else:
        parsed_interfaces = [Interface(i) for i in interfaces]

    def decorator(func: F) -> F:
        # Import here to avoid circular dependency
        from .registry import COMMAND_REGISTRY

        # Collect params from @param decorators
        params = getattr(func, "_unified_params", [])

        # Create command specification
        spec = CommandSpec(
            name=name,
            description=description,
            operation=func,
            params=params,
            interfaces=parsed_interfaces,
            cli_group=cli_group,
            cli_name=cli_name,
            mcp_name=mcp_name,
            mcp_category=mcp_category,
            exclusion_reason=exclusion_reason,
        )

        # Register in global registry
        COMMAND_REGISTRY.register(spec)

        # Store spec on function for introspection
        func._unified_spec = spec  # type: ignore

        return func

    return decorator
