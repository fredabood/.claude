"""
Central registry for unified commands.

The CommandRegistry singleton stores all registered commands and provides
methods to query commands by interface, group, or other criteria.
"""

from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .command import CommandSpec, Interface


class CommandRegistry:
    """
    Central registry for all unified commands.

    This is a singleton that stores all commands registered via
    @unified_command. Adapters query this registry to generate
    CLI commands and MCP tools.

    Example:
        # Get all CLI commands
        cli_commands = COMMAND_REGISTRY.list_for_interface(Interface.CLI)

        # Get commands in a specific CLI group
        roadmap_commands = COMMAND_REGISTRY.list_by_group("roadmap")

        # Get all MCP tools
        mcp_tools = COMMAND_REGISTRY.list_for_interface(Interface.MCP)
    """

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._commands: Dict[str, "CommandSpec"] = {}

    def register(self, spec: "CommandSpec") -> None:
        """
        Register a command specification.

        Args:
            spec: The command specification to register

        Raises:
            ValueError: If a command with this name is already registered
        """
        if spec.name in self._commands:
            raise ValueError(
                f"Command '{spec.name}' is already registered. "
                "Command names must be unique."
            )
        self._commands[spec.name] = spec

    def get(self, name: str) -> Optional["CommandSpec"]:
        """
        Get a command by name.

        Args:
            name: The command name

        Returns:
            CommandSpec if found, None otherwise
        """
        return self._commands.get(name)

    def list_all(self) -> List["CommandSpec"]:
        """
        List all registered commands.

        Returns:
            List of all CommandSpec objects
        """
        return list(self._commands.values())

    def list_for_interface(self, interface: "Interface") -> List["CommandSpec"]:
        """
        List commands available for a specific interface.

        Args:
            interface: The interface to filter by (CLI or MCP)

        Returns:
            List of CommandSpec objects available in that interface
        """
        return [
            cmd for cmd in self._commands.values()
            if cmd.is_available_in(interface)
        ]

    def list_by_group(self, group: str) -> List["CommandSpec"]:
        """
        List CLI commands in a specific group.

        Args:
            group: The CLI group name (e.g., "roadmap")

        Returns:
            List of CommandSpec objects in that group
        """
        from .command import Interface
        return [
            cmd for cmd in self._commands.values()
            if cmd.cli_group == group and cmd.is_available_in(Interface.CLI)
        ]

    def list_groups(self) -> List[str]:
        """
        List all unique CLI groups.

        Returns:
            List of group names
        """
        from .command import Interface
        groups = set()
        for cmd in self._commands.values():
            if cmd.cli_group and cmd.is_available_in(Interface.CLI):
                groups.add(cmd.cli_group)
        return sorted(groups)

    def count(self) -> int:
        """
        Get total number of registered commands.

        Returns:
            Number of registered commands
        """
        return len(self._commands)

    def count_for_interface(self, interface: "Interface") -> int:
        """
        Get number of commands for a specific interface.

        Args:
            interface: The interface to count

        Returns:
            Number of commands available in that interface
        """
        return len(self.list_for_interface(interface))

    def clear(self) -> None:
        """
        Clear all registered commands.

        Primarily used for testing.
        """
        self._commands.clear()


# Global registry singleton
COMMAND_REGISTRY = CommandRegistry()
