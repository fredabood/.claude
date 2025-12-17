"""
Click adapter for unified commands.

Generates Click commands from the unified registry, enabling automatic
CLI registration from @unified_command definitions.
"""

from pathlib import Path
from typing import Any, Callable, Dict, Optional

import click

from ..command import CommandSpec, Interface
from ..param import ParamSpec
from ..registry import COMMAND_REGISTRY
from ..types import param_to_click_type
from ..formatters import DEFAULT_FORMATTER, CommandResult


def generate_click_command(spec: CommandSpec) -> click.Command:
    """
    Generate a Click command from a CommandSpec.

    Creates a fully configured Click command with all options/arguments
    derived from the command's parameter specifications.

    Args:
        spec: The command specification

    Returns:
        Click Command object ready for registration
    """

    def command_wrapper(**kwargs: Any) -> int:
        """Wrapper that handles Click context and calls the operation."""
        try:
            # Add root_dir from context or default to cwd
            if "root_dir" not in kwargs:
                kwargs["root_dir"] = Path.cwd()

            # Call the underlying operation
            result = spec.operation(**kwargs)

            # Handle result formatting
            formatter = spec.formatter or DEFAULT_FORMATTER

            if isinstance(result, CommandResult):
                output = formatter.format_cli(result)
                if output:
                    click.echo(output)
                return 0 if result.success else 1
            else:
                # Legacy operations may return other types
                if result is not None:
                    click.echo(str(result))
                return 0

        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            return 1

    # Apply parameter decorators in reverse order (Click processes them bottom-up)
    wrapped_func: Callable[..., Any] = command_wrapper

    for param in reversed(spec.params):
        wrapped_func = _apply_param_decorator(wrapped_func, param)

    # Create the Click command
    command = click.command(
        name=spec.cli_command_name,
        help=spec.description,
    )(wrapped_func)

    return command


def _apply_param_decorator(
    func: Callable[..., Any],
    param: ParamSpec,
) -> Callable[..., Any]:
    """
    Apply a parameter decorator to a function.

    Converts ParamSpec to either a Click option or argument.

    Args:
        func: Function to decorate
        param: Parameter specification

    Returns:
        Decorated function
    """
    click_type = param_to_click_type(param)

    if param.cli_option:
        # Create option
        option_names = [f"--{param.name.replace('_', '-')}"]
        if param.cli_short:
            option_names.insert(0, param.cli_short)

        # Determine if required (required options with no default must be provided)
        is_required = param.required and param.default is None and not param.cli_is_flag

        return click.option(
            *option_names,
            type=click_type,
            required=is_required,
            default=param.default,
            help=param.help,
            is_flag=param.cli_is_flag,
            prompt=param.cli_prompt,
        )(func)
    else:
        # Create argument (positional)
        return click.argument(
            param.name,
            type=click_type,
            required=param.required,
            default=param.default if not param.required else None,
        )(func)


def register_unified_commands_to_click(
    cli_group: click.Group,
    *,
    target_group: Optional[str] = None,
) -> int:
    """
    Register all unified commands to a Click group.

    This function queries the command registry and adds all CLI-enabled
    commands to the specified Click group.

    Args:
        cli_group: The Click group to register commands to
        target_group: If specified, only register commands in this group

    Returns:
        Number of commands registered
    """
    count = 0

    for spec in COMMAND_REGISTRY.list_for_interface(Interface.CLI):
        # Skip if filtering by group and this command doesn't match
        if target_group is not None and spec.cli_group != target_group:
            continue

        command = generate_click_command(spec)

        if spec.cli_group:
            # Find or get the subgroup
            subgroup = cli_group.commands.get(spec.cli_group)
            if subgroup and isinstance(subgroup, click.Group):
                subgroup.add_command(command)
                count += 1
        else:
            # Add to root group
            cli_group.add_command(command)
            count += 1

    return count


def get_unified_click_groups() -> Dict[str, click.Group]:
    """
    Create Click groups for all registered CLI groups.

    Returns:
        Dictionary mapping group names to Click Group objects
    """
    groups: Dict[str, click.Group] = {}

    for group_name in COMMAND_REGISTRY.list_groups():
        @click.group(name=group_name)
        def group_func() -> None:
            pass

        groups[group_name] = group_func

    return groups
