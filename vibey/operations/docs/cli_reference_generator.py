"""
CLI Reference Markdown Generator

Generates comprehensive CLI reference documentation from introspected
command structure. Produces Markdown files suitable for documentation sites.

Usage:
    from vibey.operations.docs.cli_reference_generator import generate_cli_reference

    markdown = generate_cli_reference()
    Path("docs/reference/CLI_REFERENCE.md").write_text(markdown)
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from vibey.operations.docs.cli_introspector import (
    CLIStructure,
    CommandInfo,
    ParamInfo,
    ExampleInfo,
    ParamKind,
    introspect_cli,
)


@dataclass
class GeneratorConfig:
    """Configuration for the Markdown generator."""
    # Include table of contents
    include_toc: bool = True
    # Include command index
    include_index: bool = True
    # Include hidden commands
    include_hidden: bool = False
    # Include deprecated commands
    include_deprecated: bool = True
    # Max heading depth (h1 to hN)
    max_heading_depth: int = 4
    # Include generation timestamp
    include_timestamp: bool = True
    # Base command for examples (e.g., "vibey" or "./vibey")
    base_command: str = "vibey"


class CLIReferenceGenerator:
    """
    Generates Markdown documentation from CLI structure.

    Usage:
        from vibey.operations.docs.cli_introspector import introspect_cli

        structure = introspect_cli()
        generator = CLIReferenceGenerator(structure)
        markdown = generator.generate()
    """

    def __init__(
        self,
        structure: CLIStructure,
        config: Optional[GeneratorConfig] = None,
    ):
        """
        Initialize the generator.

        Args:
            structure: Introspected CLI structure
            config: Generator configuration
        """
        self.structure = structure
        self.config = config or GeneratorConfig()
        self._lines: List[str] = []

    def generate(self) -> str:
        """
        Generate complete CLI reference documentation.

        Returns:
            Markdown string
        """
        self._lines = []

        # Header
        self._add_header()

        # Quick start
        self._add_quick_start()

        # Table of contents
        if self.config.include_toc:
            self._add_toc()

        # Command index
        if self.config.include_index:
            self._add_command_index()

        # Command reference
        self._add_command_reference()

        # Common errors
        self._add_common_errors()

        # Footer
        self._add_footer()

        return "\n".join(self._lines)

    def _line(self, text: str = ""):
        """Add a line to the output."""
        self._lines.append(text)

    def _heading(self, text: str, level: int):
        """Add a heading, respecting max depth."""
        level = min(level, self.config.max_heading_depth)
        self._line(f"{'#' * level} {text}")
        self._line()

    def _add_header(self):
        """Add document header."""
        self._heading("CLI Reference", 1)

        self._line(f"**Version:** {self.structure.version}")
        self._line(f"**Total Commands:** {self.structure.total_commands}")

        if self.config.include_timestamp:
            self._line(f"**Generated:** {self.structure.generated_at}")

        self._line()
        self._line("This document provides comprehensive reference documentation for all "
                  f"`{self.config.base_command}` CLI commands.")
        self._line()
        self._line("---")
        self._line()

    def _add_quick_start(self):
        """Add quick start section with essential commands."""
        self._heading("Quick Start", 2)

        self._line("Get started with these essential commands:")
        self._line()
        self._line("```bash")
        self._line("# Initialize Vibey in your project")
        self._line("vibey init")
        self._line()
        self._line("# View roadmap status")
        self._line("vibey roadmap status")
        self._line()
        self._line("# Start working on a task")
        self._line("vibey roadmap start <task-id>")
        self._line()
        self._line("# Complete a task")
        self._line("vibey roadmap complete <task-id>")
        self._line()
        self._line("# Deploy to a platform (e.g., cursor, vscode, copilot)")
        self._line("vibey deploy run --platform cursor")
        self._line()
        self._line("# Get help for any command")
        self._line("vibey <command> --help")
        self._line("```")
        self._line()
        self._line("---")
        self._line()

    def _add_toc(self):
        """Add table of contents."""
        self._heading("Table of Contents", 2)

        # Top-level groups
        for cmd in self.structure.root.subcommands:
            if cmd.hidden and not self.config.include_hidden:
                continue
            anchor = self._make_anchor(cmd.name)
            self._line(f"- [{cmd.name}](#{anchor})")

            # Subcommands (one level)
            for subcmd in cmd.subcommands[:5]:  # Limit to avoid huge TOC
                if subcmd.hidden and not self.config.include_hidden:
                    continue
                sub_anchor = self._make_anchor(f"{cmd.name}-{subcmd.name}")
                self._line(f"  - [{subcmd.name}](#{sub_anchor})")

            if len(cmd.subcommands) > 5:
                self._line(f"  - *... and {len(cmd.subcommands) - 5} more*")

        self._line()
        self._line("---")
        self._line()

    def _add_command_index(self):
        """Add alphabetical command index."""
        self._heading("Command Index", 2)

        # Collect all commands
        all_commands = []
        self._collect_commands(self.structure.root, all_commands)

        # Sort alphabetically by path
        all_commands.sort(key=lambda c: c.path)

        # Group by command group (first-level subcommand)
        current_group = ""
        command_index = 0
        for cmd in all_commands:
            if cmd.hidden and not self.config.include_hidden:
                continue

            # Get the command group (first subcommand after 'vibey')
            parts = cmd.path.split()
            cmd_group = parts[1] if len(parts) > 1 else parts[0]
            first_letter = cmd_group[0].upper() if cmd_group else "?"

            if cmd_group != current_group:
                current_group = cmd_group
                self._line()
                self._line(f"**{cmd_group.title()}**")

            command_index += 1
            anchor = self._make_anchor(cmd.path.replace(" ", "-"))
            short = cmd.short_help or (cmd.help[:150] + "..." if cmd.help and len(cmd.help) > 150 else cmd.help) or ""
            self._line(f"{command_index}. [`{cmd.path}`](#{anchor}) - {short}")

        self._line()
        self._line("---")
        self._line()

    def _collect_commands(self, cmd: CommandInfo, result: List[CommandInfo]):
        """Recursively collect all commands."""
        # Don't include root in index
        if cmd.path != "vibey":
            result.append(cmd)
        for subcmd in cmd.subcommands:
            self._collect_commands(subcmd, result)

    def _add_command_reference(self):
        """Add detailed command reference."""
        self._heading("Command Reference", 2)

        # Process each top-level group
        for cmd in self.structure.root.subcommands:
            if cmd.hidden and not self.config.include_hidden:
                continue
            self._document_command(cmd, 3)

    def _document_command(self, cmd: CommandInfo, level: int):
        """Document a single command and its subcommands."""
        if cmd.hidden and not self.config.include_hidden:
            return

        # Command heading
        anchor_name = cmd.path.replace(" ", "-")
        self._line(f"<a id=\"{self._make_anchor(anchor_name)}\"></a>")
        self._line()

        # Add deprecated badge if applicable
        title = f"`{cmd.path}`"
        if cmd.deprecated:
            title += " *(deprecated)*"

        self._heading(title, level)

        # Description
        if cmd.help:
            # Clean up help text (remove Examples section for cleaner display)
            help_text = cmd.help
            if "Example" in help_text:
                help_text = help_text.split("Example")[0].strip()
            self._line(help_text)
            self._line()

        # Usage
        self._line("**Usage:**")
        self._line("```bash")
        usage = self._build_usage(cmd)
        self._line(usage)
        self._line("```")
        self._line()

        # Options and arguments
        if cmd.params:
            self._document_params(cmd)

        # Examples
        if cmd.examples:
            self._document_examples(cmd)

        # Subcommands summary (if group)
        if cmd.is_group and cmd.subcommands:
            self._line("**Subcommands:**")
            self._line()
            self._line("| Command | Description |")
            self._line("|---------|-------------|")
            for subcmd in cmd.subcommands:
                if subcmd.hidden and not self.config.include_hidden:
                    continue
                desc = subcmd.short_help or (subcmd.help[:150] + "..." if subcmd.help and len(subcmd.help) > 150 else subcmd.help) or ""
                # Escape pipe characters in description
                desc = desc.replace("|", "\\|")
                self._line(f"| `{subcmd.name}` | {desc} |")
            self._line()

        # Add "See Also" section for related commands
        self._add_see_also(cmd)

        self._line("---")
        self._line()

        # Document subcommands
        if cmd.is_group:
            for subcmd in cmd.subcommands:
                self._document_command(subcmd, min(level + 1, self.config.max_heading_depth))

    def _add_see_also(self, cmd: CommandInfo):
        """Add 'See Also' section with related commands."""
        # Define command relationships
        relationships = {
            "vibey roadmap status": ["vibey roadmap show", "vibey roadmap list"],
            "vibey roadmap start": ["vibey roadmap complete", "vibey roadmap show"],
            "vibey roadmap complete": ["vibey roadmap start", "vibey roadmap show"],
            "vibey roadmap show": ["vibey roadmap status", "vibey roadmap list"],
            "vibey roadmap list": ["vibey roadmap show", "vibey roadmap status"],
            "vibey roadmap db rebuild": ["vibey roadmap db status", "vibey roadmap db validate"],
            "vibey roadmap db status": ["vibey roadmap db rebuild", "vibey roadmap db validate"],
            "vibey roadmap db validate": ["vibey roadmap db rebuild", "vibey roadmap db status"],
            "vibey deploy run": ["vibey deploy list", "vibey deploy validate"],
            "vibey deploy list": ["vibey deploy run", "vibey deploy validate"],
            "vibey init": ["vibey roadmap status", "vibey deploy run"],
            "vibey docs generate-cli": ["vibey docs generate-mcp", "vibey docs check-drift"],
            "vibey docs generate-mcp": ["vibey docs generate-cli", "vibey docs check-drift"],
        }

        related = relationships.get(cmd.path)
        if related:
            self._line("**See Also:**")
            for rel_cmd in related:
                anchor = self._make_anchor(rel_cmd.replace(" ", "-"))
                self._line(f"- [`{rel_cmd}`](#{anchor})")
            self._line()

    def _build_usage(self, cmd: CommandInfo) -> str:
        """Build usage string for a command."""
        parts = [cmd.path]

        # Add options placeholder if there are options
        has_options = any(p.kind == ParamKind.OPTION for p in cmd.params)
        if has_options:
            parts.append("[OPTIONS]")

        # Add arguments
        for param in cmd.params:
            if param.kind == ParamKind.ARGUMENT:
                if param.required:
                    parts.append(f"<{param.name.upper()}>")
                else:
                    parts.append(f"[{param.name.upper()}]")

        # Add subcommand placeholder if group
        if cmd.is_group:
            parts.append("COMMAND")

        return " ".join(parts)

    def _document_params(self, cmd: CommandInfo):
        """Document command parameters."""
        options = [p for p in cmd.params if p.kind == ParamKind.OPTION]
        arguments = [p for p in cmd.params if p.kind == ParamKind.ARGUMENT]

        if arguments:
            self._line("**Arguments:**")
            self._line()
            self._line("| Argument | Type | Required | Description |")
            self._line("|----------|------|----------|-------------|")
            for arg in arguments:
                desc = (arg.help or "").replace("|", "\\|")
                req = "Yes" if arg.required else "No"
                self._line(f"| `{arg.name.upper()}` | {arg.type_str} | {req} | {desc} |")
            self._line()

        if options:
            self._line("**Options:**")
            self._line()
            self._line("| Option | Type | Default | Description |")
            self._line("|--------|------|---------|-------------|")
            for opt in options:
                # Build option string
                opt_str = ", ".join(opt.opts) if opt.opts else f"--{opt.name}"

                # Handle flags
                if opt.is_flag:
                    type_str = "flag"
                else:
                    type_str = opt.type_str

                # Default value
                if opt.default is None:
                    default = "-"
                elif opt.default == "<dynamic>":
                    default = "*dynamic*"
                else:
                    default = f"`{opt.default}`"

                desc = (opt.help or "").replace("|", "\\|")

                self._line(f"| `{opt_str}` | {type_str} | {default} | {desc} |")
            self._line()

    def _document_examples(self, cmd: CommandInfo):
        """Document command examples."""
        self._line("**Examples:**")
        self._line()
        for ex in cmd.examples:
            if ex.description:
                self._line(f"*{ex.description}:*")
            self._line("```bash")
            self._line(ex.command)
            self._line("```")
            self._line()

    def _add_common_errors(self):
        """Add common errors section."""
        self._heading("Common Errors", 2)

        self._line("### Database Errors")
        self._line()
        self._line("**Error:** `Database out of sync with YAML`")
        self._line()
        self._line("**Solution:** Rebuild the database from YAML sources:")
        self._line("```bash")
        self._line("vibey roadmap db rebuild")
        self._line("```")
        self._line()

        self._line("**Error:** `Task not found: <id>`")
        self._line()
        self._line("**Solution:** Verify the task ID and check database status:")
        self._line("```bash")
        self._line("vibey roadmap db status")
        self._line("vibey roadmap list tasks")
        self._line("```")
        self._line()

        self._line("### Task Lifecycle Errors")
        self._line()
        self._line("**Error:** `Cannot complete task: Task has no commits`")
        self._line()
        self._line("**Solution:** Either add commits or mark as non-code task:")
        self._line("```bash")
        self._line("# Add commits")
        self._line("vibey roadmap add-commit <task-id> <sha>")
        self._line("")
        self._line("# Or mark as non-code task")
        self._line("vibey roadmap complete <task-id> --no-commits")
        self._line("```")
        self._line()

        self._line("**Error:** `Cannot start task: Sprint not active`")
        self._line()
        self._line("**Solution:** Start the sprint first:")
        self._line("```bash")
        self._line("vibey roadmap start <sprint-id>")
        self._line("```")
        self._line()

        self._line("### Activity Log Errors")
        self._line()
        self._line("**Error:** `No activity log entry for: <file>`")
        self._line()
        self._line("**Solution:** Use CLI commands instead of direct file edits:")
        self._line("```bash")
        self._line("# Use CLI to update tasks")
        self._line("vibey roadmap update task <id> --status <status>")
        self._line("")
        self._line("# Or bypass with --no-verify (not recommended)")
        self._line("git commit --no-verify -m 'message'")
        self._line("```")
        self._line()

        self._line("---")
        self._line()

    def _add_footer(self):
        """Add document footer."""
        self._line("---")
        self._line()
        self._line("*This documentation was auto-generated from the CLI source code.*")
        self._line()
        self._line(f"*Generated at: {self.structure.generated_at}*")

    def _make_anchor(self, text: str) -> str:
        """Create a valid Markdown anchor from text."""
        # Convert to lowercase, replace spaces with hyphens, remove special chars
        anchor = text.lower()
        anchor = anchor.replace(" ", "-")
        anchor = "".join(c for c in anchor if c.isalnum() or c == "-")
        return anchor


def generate_cli_reference(
    config: Optional[GeneratorConfig] = None,
    structure: Optional[CLIStructure] = None,
) -> str:
    """
    Generate CLI reference documentation.

    This is the main entry point for CLI reference generation.

    Args:
        config: Optional generator configuration
        structure: Optional pre-introspected CLI structure

    Returns:
        Markdown string

    Usage:
        from vibey.operations.docs.cli_reference_generator import generate_cli_reference

        # Generate with defaults
        markdown = generate_cli_reference()

        # Generate with custom config
        from vibey.operations.docs.cli_reference_generator import GeneratorConfig
        config = GeneratorConfig(include_hidden=True)
        markdown = generate_cli_reference(config=config)

        # Save to file
        Path("docs/reference/CLI_REFERENCE.md").write_text(markdown)
    """
    if structure is None:
        structure = introspect_cli()

    generator = CLIReferenceGenerator(structure, config)
    return generator.generate()


def write_cli_reference(
    output_path: str,
    config: Optional[GeneratorConfig] = None,
) -> Path:
    """
    Generate and write CLI reference to a file.

    Args:
        output_path: Path to write the Markdown file
        config: Optional generator configuration

    Returns:
        Path to the written file
    """
    markdown = generate_cli_reference(config)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown)
    return path


if __name__ == "__main__":
    # Quick test when run directly
    import sys

    output = sys.argv[1] if len(sys.argv) > 1 else None

    if output:
        path = write_cli_reference(output)
        print(f"Written to: {path}")
        print(f"Size: {path.stat().st_size} bytes")
    else:
        markdown = generate_cli_reference()
        print(f"Generated {len(markdown)} characters")
        print(f"Lines: {markdown.count(chr(10))}")
        print()
        # Print first 100 lines
        lines = markdown.split("\n")
        for line in lines[:100]:
            print(line)
        if len(lines) > 100:
            print(f"... and {len(lines) - 100} more lines")
