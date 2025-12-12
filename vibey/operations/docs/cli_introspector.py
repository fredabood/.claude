"""
CLI Introspection Module

Extracts structured documentation data from Click command trees.
Enables auto-generation of CLI reference documentation that cannot
drift from the implementation.

Usage:
    from vibey.operations.docs.cli_introspector import introspect_cli

    structure = introspect_cli()
    print(f"Total commands: {structure.total_commands}")

    # Export to JSON
    json_output = structure.to_json()
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Any, Dict
import json
import logging
import re

import click

logger = logging.getLogger(__name__)


class ParamKind(str, Enum):
    """Type of Click parameter."""
    OPTION = "option"
    ARGUMENT = "argument"


@dataclass
class ParamInfo:
    """
    Information about a Click parameter (option or argument).

    Attributes:
        name: Parameter name (e.g., "track", "verbose")
        kind: Whether this is an option or argument
        type_str: Human-readable type (e.g., "STRING", "Choice(['a', 'b'])")
        required: Whether the parameter is required
        default: Default value if any
        help: Help text for the parameter
        multiple: Whether multiple values are accepted
        is_flag: Whether this is a boolean flag
        envvar: Environment variable name if set
        opts: Option strings (e.g., ["-v", "--verbose"])
    """
    name: str
    kind: ParamKind
    type_str: str
    required: bool
    default: Optional[Any] = None
    help: Optional[str] = None
    multiple: bool = False
    is_flag: bool = False
    envvar: Optional[str] = None
    opts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "kind": self.kind.value,
            "type_str": self.type_str,
            "required": self.required,
            "default": self.default,
            "help": self.help,
            "multiple": self.multiple,
            "is_flag": self.is_flag,
            "envvar": self.envvar,
            "opts": self.opts,
        }


@dataclass
class ExampleInfo:
    """
    A usage example for a command.

    Attributes:
        command: The example command line
        description: Optional description of what the example does
    """
    command: str
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "command": self.command,
            "description": self.description,
        }


@dataclass
class CommandInfo:
    """
    Introspected information about a Click command.

    Attributes:
        name: Command name (e.g., "status")
        path: Full command path (e.g., "roadmap status")
        help: Full help text (may be multi-line)
        short_help: Short help for listings
        params: List of parameters (options and arguments)
        subcommands: Nested commands (if this is a Group)
        examples: Usage examples extracted from docstring
        deprecated: Whether command is marked deprecated
        hidden: Whether command is hidden from help
        is_group: Whether this command has subcommands
    """
    name: str
    path: str
    help: Optional[str] = None
    short_help: Optional[str] = None
    params: List[ParamInfo] = field(default_factory=list)
    subcommands: List['CommandInfo'] = field(default_factory=list)
    examples: List[ExampleInfo] = field(default_factory=list)
    deprecated: bool = False
    hidden: bool = False
    is_group: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "path": self.path,
            "help": self.help,
            "short_help": self.short_help,
            "params": [p.to_dict() for p in self.params],
            "subcommands": [s.to_dict() for s in self.subcommands],
            "examples": [e.to_dict() for e in self.examples],
            "deprecated": self.deprecated,
            "hidden": self.hidden,
            "is_group": self.is_group,
        }

    def count_commands(self) -> tuple[int, int]:
        """
        Count total commands and max depth.

        Returns:
            Tuple of (total_commands, max_depth)
        """
        total = 1
        max_depth = 0

        for subcmd in self.subcommands:
            sub_total, sub_depth = subcmd.count_commands()
            total += sub_total
            max_depth = max(max_depth, sub_depth + 1)

        return total, max_depth


@dataclass
class CLIStructure:
    """
    Complete introspected CLI structure.

    Attributes:
        root: The root command (vibey)
        version: CLI version string
        total_commands: Total number of commands
        max_depth: Maximum nesting depth
        generated_at: ISO timestamp of generation
    """
    root: CommandInfo
    version: str
    total_commands: int
    max_depth: int
    generated_at: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "root": self.root.to_dict(),
            "version": self.version,
            "total_commands": self.total_commands,
            "max_depth": self.max_depth,
            "generated_at": self.generated_at,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(
            self.to_dict(),
            indent=indent,
            ensure_ascii=False,
        )

    def to_yaml(self) -> str:
        """Serialize to YAML string."""
        try:
            import yaml
            return yaml.dump(
                self.to_dict(),
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
        except ImportError:
            raise ImportError("PyYAML required for YAML output: pip install pyyaml")


class CLIIntrospector:
    """
    Walks Click command tree and extracts documentation data.

    Usage:
        from vibey.cli.main import cli

        introspector = CLIIntrospector(cli)
        structure = introspector.introspect()

        print(f"Total commands: {structure.total_commands}")
        print(structure.to_json())
    """

    def __init__(self, root_command: click.BaseCommand, version: str = "unknown"):
        """
        Initialize the introspector.

        Args:
            root_command: The root Click command/group to introspect
            version: CLI version string
        """
        self.root = root_command
        self.version = version
        self._visited: set = set()

    def introspect(self) -> CLIStructure:
        """
        Walk the command tree and extract all information.

        Returns:
            CLIStructure containing complete CLI documentation data
        """
        self._visited.clear()
        root_info = self._introspect_command(self.root, "")
        total, max_depth = root_info.count_commands()

        return CLIStructure(
            root=root_info,
            version=self.version,
            total_commands=total,
            max_depth=max_depth,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def _introspect_command(
        self,
        cmd: click.BaseCommand,
        parent_path: str,
    ) -> CommandInfo:
        """
        Recursively introspect a command and its subcommands.

        Args:
            cmd: Click command to introspect
            parent_path: Path of parent command (e.g., "roadmap")

        Returns:
            CommandInfo with all extracted data
        """
        # Build path
        name = getattr(cmd, 'name', None)
        # Use 'vibey' for root command regardless of internal name
        if not parent_path:
            name = "vibey"
            path = "vibey"
        else:
            name = name or "unknown"
            path = f"{parent_path} {name}"

        # Prevent circular references
        cmd_id = id(cmd)
        if cmd_id in self._visited:
            logger.warning(f"Circular reference detected at {path}")
            return CommandInfo(
                name=name,
                path=path,
                help="[Circular reference]",
            )
        self._visited.add(cmd_id)

        # Extract command information
        info = CommandInfo(
            name=name,
            path=path,
            help=getattr(cmd, 'help', None),
            short_help=getattr(cmd, 'short_help', None),
            params=self._extract_params(cmd),
            examples=self._extract_examples(cmd),
            deprecated=getattr(cmd, 'deprecated', False),
            hidden=getattr(cmd, 'hidden', False),
            is_group=isinstance(cmd, click.Group),
        )

        # Recursively process subcommands for Groups
        if isinstance(cmd, click.Group):
            commands = getattr(cmd, 'commands', {})
            for subcmd_name in sorted(commands.keys()):
                subcmd = commands[subcmd_name]
                try:
                    info.subcommands.append(
                        self._introspect_command(subcmd, path)
                    )
                except Exception as e:
                    logger.warning(f"Error introspecting {path} {subcmd_name}: {e}")
                    info.subcommands.append(CommandInfo(
                        name=subcmd_name,
                        path=f"{path} {subcmd_name}",
                        help=f"[Error: {e}]",
                    ))

        return info

    def _extract_params(self, cmd: click.BaseCommand) -> List[ParamInfo]:
        """
        Extract parameter information from a command.

        Args:
            cmd: Click command

        Returns:
            List of ParamInfo objects
        """
        params = []
        cmd_params = getattr(cmd, 'params', [])

        for param in cmd_params:
            try:
                # Determine kind
                if isinstance(param, click.Option):
                    kind = ParamKind.OPTION
                else:
                    kind = ParamKind.ARGUMENT

                # Extract type string
                param_type = getattr(param, 'type', None)
                type_str = self._get_type_string(param_type) if param_type else "UNKNOWN"

                # Normalize default
                default = getattr(param, 'default', None)
                default = self._normalize_default(default)

                params.append(ParamInfo(
                    name=param.name,
                    kind=kind,
                    type_str=type_str,
                    required=getattr(param, 'required', False),
                    default=default,
                    help=getattr(param, 'help', None),
                    multiple=getattr(param, 'multiple', False),
                    is_flag=getattr(param, 'is_flag', False),
                    envvar=getattr(param, 'envvar', None),
                    opts=list(getattr(param, 'opts', [])),
                ))
            except Exception as e:
                logger.warning(f"Error extracting param {param}: {e}")

        return params

    def _normalize_default(self, default: Any) -> Any:
        """
        Normalize default values for JSON serialization.

        Args:
            default: Raw default value from Click

        Returns:
            JSON-serializable default value
        """
        if default is None:
            return None
        if default == ():
            return None
        if callable(default):
            return "<dynamic>"

        # Handle Click's Sentinel type and other non-serializable types
        type_name = type(default).__name__
        if type_name in ('Sentinel', '_UNSET'):
            return None

        # Try to serialize to catch any other issues
        try:
            json.dumps(default)
            return default
        except (TypeError, ValueError):
            return f"<{type_name}>"

    def _get_type_string(self, param_type: click.ParamType) -> str:
        """
        Convert Click parameter type to human-readable string.

        Args:
            param_type: Click parameter type

        Returns:
            Human-readable type string
        """
        if param_type is None:
            return "UNKNOWN"

        try:
            if isinstance(param_type, click.Choice):
                choices = sorted(param_type.choices) if param_type.choices else []
                return f"Choice({choices})"
            elif isinstance(param_type, click.IntRange):
                min_val = getattr(param_type, 'min', None)
                max_val = getattr(param_type, 'max', None)
                return f"IntRange({min_val}, {max_val})"
            elif isinstance(param_type, click.FloatRange):
                min_val = getattr(param_type, 'min', None)
                max_val = getattr(param_type, 'max', None)
                return f"FloatRange({min_val}, {max_val})"
            elif isinstance(param_type, click.Path):
                parts = []
                if getattr(param_type, 'exists', False):
                    parts.append("exists")
                if getattr(param_type, 'file_okay', True):
                    parts.append("file")
                if getattr(param_type, 'dir_okay', True):
                    parts.append("dir")
                return f"Path({', '.join(parts)})" if parts else "PATH"
            elif isinstance(param_type, click.File):
                mode = getattr(param_type, 'mode', 'r')
                return f"File({mode})"
            else:
                return getattr(param_type, 'name', 'UNKNOWN').upper()
        except Exception as e:
            logger.warning(f"Error getting type string: {e}")
            return "UNKNOWN"

    def _extract_examples(self, cmd: click.BaseCommand) -> List[ExampleInfo]:
        """
        Extract usage examples from command.

        Extraction order:
        1. Custom 'examples' attribute on command
        2. Parse from help text/docstring
        3. Generate basic example from command path

        Args:
            cmd: Click command

        Returns:
            List of ExampleInfo objects
        """
        examples = []

        # Strategy 1: Custom examples attribute
        if hasattr(cmd, 'examples'):
            custom_examples = getattr(cmd, 'examples', [])
            for ex in custom_examples:
                if isinstance(ex, ExampleInfo):
                    examples.append(ex)
                elif isinstance(ex, dict):
                    examples.append(ExampleInfo(
                        command=ex.get('command', ''),
                        description=ex.get('description'),
                    ))
                elif isinstance(ex, str):
                    examples.append(ExampleInfo(command=ex))

        # Strategy 2: Parse from docstring
        help_text = getattr(cmd, 'help', None)
        if help_text and not examples:
            examples.extend(self._parse_examples_from_text(help_text))

        return examples

    def _parse_examples_from_text(self, text: str) -> List[ExampleInfo]:
        """
        Parse examples from help text/docstring.

        Recognizes:
        - "Examples:" section with indented commands
        - Comments (# ...) as descriptions
        - Code blocks (```)

        Args:
            text: Help text to parse

        Returns:
            List of ExampleInfo objects
        """
        examples = []
        if not text:
            return examples

        lines = text.split('\n')
        in_examples = False
        in_code_block = False
        current_description = None

        for line in lines:
            stripped = line.strip()

            # Detect code block markers
            if stripped.startswith('```'):
                in_code_block = not in_code_block
                continue

            # Detect start of examples section
            if stripped.lower().startswith('example'):
                in_examples = True
                continue

            # Detect end of examples section (new major section)
            if in_examples and stripped and stripped[0].isupper() and stripped.endswith(':'):
                if not stripped.lower().startswith('example'):
                    in_examples = False
                    continue

            if not in_examples:
                continue

            # Empty line - reset description
            if not stripped:
                current_description = None
                continue

            # Comment line - capture as description
            if stripped.startswith('#'):
                current_description = stripped[1:].strip()
                continue

            # Command line detection
            if stripped.startswith('vibey') or stripped.startswith('$ vibey'):
                cmd_text = stripped.lstrip('$ ')
                examples.append(ExampleInfo(
                    command=cmd_text,
                    description=current_description,
                ))
                current_description = None

        return examples


def introspect_cli(use_cache: bool = False) -> CLIStructure:
    """
    Introspect the Vibey CLI and return structured data.

    This is the main entry point for CLI introspection.

    Args:
        use_cache: Whether to use cached results (not implemented yet)

    Returns:
        CLIStructure with complete CLI documentation data

    Usage:
        from vibey.operations.docs.cli_introspector import introspect_cli

        structure = introspect_cli()
        print(f"Total commands: {structure.total_commands}")
        print(f"Max depth: {structure.max_depth}")

        # Export to JSON
        with open("cli_structure.json", "w") as f:
            f.write(structure.to_json())
    """
    # Import here to avoid circular imports
    from vibey.cli.main import cli, __version__

    introspector = CLIIntrospector(cli, version=__version__)
    return introspector.introspect()


def get_command_by_path(structure: CLIStructure, path: str) -> Optional[CommandInfo]:
    """
    Find a command by its full path.

    Args:
        structure: CLIStructure to search
        path: Command path (e.g., "roadmap status")

    Returns:
        CommandInfo if found, None otherwise
    """
    parts = path.split()
    current = structure.root

    # Skip root name if it matches
    if parts and parts[0] == current.name:
        parts = parts[1:]

    for part in parts:
        found = None
        for subcmd in current.subcommands:
            if subcmd.name == part:
                found = subcmd
                break
        if found is None:
            return None
        current = found

    return current


def list_all_commands(structure: CLIStructure) -> List[str]:
    """
    Get a flat list of all command paths.

    Args:
        structure: CLIStructure to enumerate

    Returns:
        List of command paths sorted alphabetically
    """
    commands = []

    def collect(cmd: CommandInfo):
        commands.append(cmd.path)
        for subcmd in cmd.subcommands:
            collect(subcmd)

    collect(structure.root)
    return sorted(commands)


if __name__ == "__main__":
    # Quick test when run directly
    structure = introspect_cli()
    print(f"CLI Version: {structure.version}")
    print(f"Total Commands: {structure.total_commands}")
    print(f"Max Depth: {structure.max_depth}")
    print(f"Generated At: {structure.generated_at}")
    print("\nTop-level commands:")
    for subcmd in structure.root.subcommands:
        count = subcmd.count_commands()[0]
        print(f"  {subcmd.name}: {count} commands")
