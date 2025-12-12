# Sprint 2.1: CLI Reference Guide (Auto-Generated)

**Sprint ID:** `01KC81GRE23T0KSHR4ZCES476M`
**Track:** User Journey Audit & Documentation Coverage
**Status:** Not Started
**Tasks:** 7

## Overview

This sprint implements an auto-generated CLI reference documentation system. The goal is to eliminate documentation drift by introspecting the Click command tree and generating comprehensive reference documentation automatically.

## Success Criteria

1. 100% CLI command coverage in generated documentation
2. Automated drift detection in CI pipeline
3. Single command to regenerate all CLI docs
4. All commands have usage examples extractable from code

---

## Task Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  [Task 1] Design CLI Introspection Architecture                 │
│      │                                                          │
│      ▼                                                          │
│  [Task 2] Build CLI Introspection Module ◄─────────────────┐    │
│      │                                                     │    │
│      │                            [Task 4] Add Usage       │    │
│      ▼                            Examples to CLI ─────────┘    │
│  [Task 3] Build CLI Reference Markdown Generator                │
│      │                                                          │
│      ▼                                                          │
│  [Task 5] Generate Initial CLI Reference Guide                  │
│      │                                                          │
│      ├──────────────────────────┐                               │
│      ▼                          ▼                               │
│  [Task 6] Implement           [Task 7] Implement                │
│  'vibey docs generate cli'    Drift Detection                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Task 1: Design CLI Introspection Architecture

**ID:** `01KC81GRE23T0KSHR4ZCES476N`
**Type:** Design
**Priority:** Medium
**Estimated Tokens:** 15,000

### Objective

Design a system that introspects Click commands to extract structured data for documentation generation.

### Inputs

- Click library documentation
- Existing CLI structure in `vibey/cli/main.py` and `vibey/cli/commands.py`
- Current command inventory (11 top-level groups, 50+ roadmap subcommands)

### Analysis Required

#### 1. Click Command Tree Structure

```python
# Current CLI hierarchy
vibey (root)
├── artifact    # Manage artifacts
├── audit       # Codebase analysis
├── auth        # Authentication keys
├── config      # Framework configuration
├── content     # Agents, workflows, templates
├── deploy      # Platform deployment
├── docs        # Documentation generation
├── export      # Platform-specific exports
├── git         # Git history analysis
├── roadmap     # Roadmap system (50+ subcommands)
│   ├── activity
│   ├── add-commit
│   ├── add-context
│   ├── ... (47 more)
└── validate    # Asset validation
```

#### 2. Data to Extract Per Command

| Field | Source | Example |
|-------|--------|---------|
| `name` | `command.name` | `"status"` |
| `path` | Computed from tree | `"roadmap status"` |
| `help` | `command.help` | `"Show roadmap status..."` |
| `short_help` | `command.short_help` | `"Show status"` |
| `params` | `command.params` | List of options/arguments |
| `deprecated` | `command.deprecated` | `False` |
| `hidden` | `command.hidden` | `False` |
| `examples` | From docstring or custom attr | `["vibey roadmap status"]` |

#### 3. Parameter Extraction

For each `click.Option` or `click.Argument`:

```python
{
    "name": "--backend",
    "type": "Choice(['auto', 'sqlite', 'yaml'])",
    "required": False,
    "default": "auto",
    "help": "Storage backend selection",
    "multiple": False,
    "is_flag": False,
    "envvar": "VIBEY_BACKEND"  # if set
}
```

#### 4. Example Extraction Strategy

Options (in order of preference):
1. **Custom attribute:** `@command.example("vibey roadmap status --all")`
2. **Docstring parsing:** Extract from `Examples:` section in docstring
3. **Help text parsing:** Extract code blocks from help text

### Output

**File:** `.vibey/roadmap/context/sprints/user-journey-phase-2-1/CLI_INTROSPECTION_DESIGN.md`

Document should include:
- Data model for introspected commands
- Tree traversal algorithm
- Example extraction strategy
- Output format specification (JSON schema)
- Error handling for malformed commands

### Acceptance Criteria

- [ ] Complete data model documented
- [ ] Tree traversal algorithm specified
- [ ] JSON output schema defined
- [ ] Example extraction strategy chosen
- [ ] Edge cases documented (hidden commands, deprecated, etc.)

---

## Task 2: Build CLI Introspection Module

**ID:** `01KC81GRE23T0KSHR4ZCES476P`
**Type:** Development
**Priority:** Medium
**Estimated Tokens:** 25,000

### Objective

Implement the introspection module that walks the Click command tree and extracts structured data.

### Implementation

**File:** `vibey/operations/docs/cli_introspector.py`

```python
"""
CLI Introspection Module

Extracts structured documentation data from Click command trees.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import click
import json
import re


@dataclass
class ParamInfo:
    """Information about a Click parameter (option or argument)."""
    name: str
    param_type: str  # "option" or "argument"
    type_str: str    # e.g., "STRING", "Choice(['a', 'b'])"
    required: bool
    default: Any
    help: Optional[str]
    multiple: bool = False
    is_flag: bool = False
    envvar: Optional[str] = None


@dataclass
class CommandInfo:
    """Introspected information about a Click command."""
    name: str
    path: str           # Full command path, e.g., "roadmap status"
    help: Optional[str]
    short_help: Optional[str]
    params: List[ParamInfo] = field(default_factory=list)
    subcommands: List['CommandInfo'] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    deprecated: bool = False
    hidden: bool = False


class CLIIntrospector:
    """
    Walks Click command tree and extracts documentation data.

    Usage:
        from vibey.cli.main import cli
        introspector = CLIIntrospector(cli)
        data = introspector.introspect()
        introspector.to_json("cli_structure.json")
    """

    def __init__(self, root_command: click.Group):
        self.root = root_command
        self._data: Optional[CommandInfo] = None

    def introspect(self) -> CommandInfo:
        """Walk the command tree and extract all information."""
        self._data = self._introspect_command(self.root, "")
        return self._data

    def _introspect_command(
        self,
        cmd: click.Command,
        parent_path: str
    ) -> CommandInfo:
        """Recursively introspect a command and its subcommands."""
        path = f"{parent_path} {cmd.name}".strip() if parent_path else cmd.name

        info = CommandInfo(
            name=cmd.name,
            path=path,
            help=cmd.help,
            short_help=cmd.short_help,
            params=self._extract_params(cmd),
            examples=self._extract_examples(cmd),
            deprecated=getattr(cmd, 'deprecated', False),
            hidden=getattr(cmd, 'hidden', False)
        )

        # Recursively process subcommands for Groups
        if isinstance(cmd, click.Group):
            for name, subcmd in sorted(cmd.commands.items()):
                info.subcommands.append(
                    self._introspect_command(subcmd, path)
                )

        return info

    def _extract_params(self, cmd: click.Command) -> List[ParamInfo]:
        """Extract parameter information from a command."""
        params = []
        for param in cmd.params:
            params.append(ParamInfo(
                name=param.name,
                param_type="option" if isinstance(param, click.Option) else "argument",
                type_str=self._get_type_str(param.type),
                required=param.required,
                default=param.default if param.default != () else None,
                help=getattr(param, 'help', None),
                multiple=getattr(param, 'multiple', False),
                is_flag=getattr(param, 'is_flag', False),
                envvar=getattr(param, 'envvar', None)
            ))
        return params

    def _get_type_str(self, param_type: click.ParamType) -> str:
        """Convert Click type to human-readable string."""
        if isinstance(param_type, click.Choice):
            return f"Choice({list(param_type.choices)})"
        return param_type.name.upper()

    def _extract_examples(self, cmd: click.Command) -> List[str]:
        """Extract usage examples from docstring or help text."""
        examples = []

        # Check for custom examples attribute
        if hasattr(cmd, 'examples'):
            return cmd.examples

        # Parse from docstring
        if cmd.help:
            examples.extend(self._parse_examples_from_text(cmd.help))

        return examples

    def _parse_examples_from_text(self, text: str) -> List[str]:
        """Parse examples from docstring text."""
        examples = []
        in_examples = False

        for line in text.split('\n'):
            stripped = line.strip()

            if stripped.lower().startswith('example'):
                in_examples = True
                continue

            if in_examples:
                # End of examples section
                if stripped and not stripped.startswith(('vibey', '#', '$')):
                    if not stripped.startswith(' '):
                        break

                # Extract command lines
                if stripped.startswith('vibey') or stripped.startswith('$'):
                    cmd_line = stripped.lstrip('$ ')
                    examples.append(cmd_line)

        return examples

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        if not self._data:
            self.introspect()
        return self._to_dict_recursive(self._data)

    def _to_dict_recursive(self, info: CommandInfo) -> Dict[str, Any]:
        """Recursively convert CommandInfo to dict."""
        return {
            "name": info.name,
            "path": info.path,
            "help": info.help,
            "short_help": info.short_help,
            "params": [vars(p) for p in info.params],
            "subcommands": [self._to_dict_recursive(s) for s in info.subcommands],
            "examples": info.examples,
            "deprecated": info.deprecated,
            "hidden": info.hidden
        }

    def to_json(self, path: str, indent: int = 2) -> None:
        """Write introspection data to JSON file."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=indent, default=str)


def introspect_cli() -> CommandInfo:
    """
    Convenience function to introspect the Vibey CLI.

    Returns:
        CommandInfo: Root command info with full tree
    """
    from vibey.cli.main import cli
    introspector = CLIIntrospector(cli)
    return introspector.introspect()
```

### Test Cases

```python
# tests/operations/docs/test_cli_introspector.py

def test_introspect_root_command():
    """Test introspecting the root CLI command."""
    from vibey.cli.main import cli
    introspector = CLIIntrospector(cli)
    data = introspector.introspect()

    assert data.name == "cli"
    assert len(data.subcommands) >= 10  # artifact, audit, auth, etc.

def test_introspect_nested_commands():
    """Test that nested commands are captured."""
    data = introspect_cli()

    # Find roadmap command
    roadmap = next(c for c in data.subcommands if c.name == "roadmap")
    assert len(roadmap.subcommands) >= 40  # Many subcommands

    # Find roadmap status
    status = next(c for c in roadmap.subcommands if c.name == "status")
    assert "status" in status.path

def test_extract_params():
    """Test parameter extraction."""
    data = introspect_cli()
    roadmap = next(c for c in data.subcommands if c.name == "roadmap")

    # Check backend option
    backend_param = next(
        (p for p in roadmap.params if p.name == "backend"),
        None
    )
    assert backend_param is not None
    assert "Choice" in backend_param.type_str

def test_extract_examples():
    """Test example extraction from docstrings."""
    data = introspect_cli()

    # Root command should have examples
    assert len(data.examples) > 0
    assert any("vibey roadmap" in ex for ex in data.examples)

def test_to_json():
    """Test JSON serialization."""
    introspector = CLIIntrospector(cli)
    introspector.introspect()

    # Should not raise
    json_str = json.dumps(introspector.to_dict())
    assert "roadmap" in json_str
```

### Acceptance Criteria

- [ ] Module implemented at `vibey/operations/docs/cli_introspector.py`
- [ ] All Click command types handled (Command, Group, MultiCommand)
- [ ] Parameters extracted with full metadata
- [ ] Examples extracted from docstrings
- [ ] Hidden/deprecated commands flagged
- [ ] JSON export working
- [ ] Unit tests passing

---

## Task 3: Build CLI Reference Markdown Generator

**ID:** `01KC81GRE23T0KSHR4ZCES476Q`
**Type:** Development
**Priority:** Medium
**Estimated Tokens:** 20,000

### Objective

Implement a generator that takes introspection output and produces comprehensive Markdown documentation.

### Implementation

**File:** `vibey/operations/docs/cli_reference_generator.py`

```python
"""
CLI Reference Markdown Generator

Generates comprehensive CLI reference documentation from introspection data.
"""

from pathlib import Path
from typing import List, Optional
from datetime import datetime

from vibey.operations.docs.cli_introspector import (
    CLIIntrospector,
    CommandInfo,
    ParamInfo,
    introspect_cli
)


class CLIReferenceGenerator:
    """
    Generates Markdown CLI reference documentation.

    Output structure:
    - Title and generation timestamp
    - Table of contents with all commands
    - Detailed documentation for each command
    - Index of all options
    """

    def __init__(self, data: Optional[CommandInfo] = None):
        self.data = data or introspect_cli()
        self._lines: List[str] = []

    def generate(self) -> str:
        """Generate complete CLI reference documentation."""
        self._lines = []

        self._add_header()
        self._add_toc()
        self._add_command_docs(self.data, level=2)
        self._add_options_index()
        self._add_footer()

        return "\n".join(self._lines)

    def _add_header(self) -> None:
        """Add document header."""
        self._lines.extend([
            "# Vibey CLI Reference",
            "",
            f"> Auto-generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "> Do not edit manually - regenerate with `vibey docs generate cli`",
            "",
            "## Overview",
            "",
            "The Vibey CLI provides unified access to the Vibey Agent Framework.",
            "All commands follow the pattern: `vibey <group> <command> [options]`",
            "",
        ])

    def _add_toc(self) -> None:
        """Add table of contents."""
        self._lines.extend([
            "## Table of Contents",
            "",
        ])

        self._add_toc_entry(self.data, depth=0)
        self._lines.append("")

    def _add_toc_entry(self, cmd: CommandInfo, depth: int) -> None:
        """Add a TOC entry for a command."""
        if cmd.hidden:
            return

        indent = "  " * depth
        anchor = cmd.path.replace(" ", "-").lower()

        # Add entry
        self._lines.append(f"{indent}- [{cmd.path}](#{anchor})")

        # Add subcommands
        for sub in cmd.subcommands:
            self._add_toc_entry(sub, depth + 1)

    def _add_command_docs(self, cmd: CommandInfo, level: int) -> None:
        """Add documentation for a command."""
        if cmd.hidden:
            return

        # Section header
        header = "#" * level
        self._lines.extend([
            f"{header} {cmd.path}",
            "",
        ])

        # Deprecation warning
        if cmd.deprecated:
            self._lines.extend([
                "> **DEPRECATED:** This command is deprecated and may be removed.",
                "",
            ])

        # Description
        if cmd.help:
            self._lines.extend([
                cmd.help.strip(),
                "",
            ])

        # Usage
        self._lines.extend([
            "**Usage:**",
            "",
            "```bash",
            f"{cmd.path} [OPTIONS]" + self._get_args_str(cmd),
            "```",
            "",
        ])

        # Options table
        options = [p for p in cmd.params if p.param_type == "option"]
        if options:
            self._lines.extend([
                "**Options:**",
                "",
                "| Option | Type | Default | Description |",
                "|--------|------|---------|-------------|",
            ])
            for opt in options:
                flag = f"`--{opt.name}`"
                if opt.is_flag:
                    flag += " (flag)"
                default = f"`{opt.default}`" if opt.default is not None else "-"
                desc = opt.help or "-"
                self._lines.append(f"| {flag} | {opt.type_str} | {default} | {desc} |")
            self._lines.append("")

        # Arguments table
        args = [p for p in cmd.params if p.param_type == "argument"]
        if args:
            self._lines.extend([
                "**Arguments:**",
                "",
                "| Argument | Type | Required | Description |",
                "|----------|------|----------|-------------|",
            ])
            for arg in args:
                req = "Yes" if arg.required else "No"
                desc = arg.help or "-"
                self._lines.append(f"| `{arg.name}` | {arg.type_str} | {req} | {desc} |")
            self._lines.append("")

        # Examples
        if cmd.examples:
            self._lines.extend([
                "**Examples:**",
                "",
                "```bash",
            ])
            for ex in cmd.examples:
                self._lines.append(ex)
            self._lines.extend([
                "```",
                "",
            ])

        # Horizontal rule between sections
        self._lines.extend(["---", ""])

        # Subcommands
        for sub in cmd.subcommands:
            self._add_command_docs(sub, min(level + 1, 4))

    def _get_args_str(self, cmd: CommandInfo) -> str:
        """Get argument string for usage line."""
        args = [p for p in cmd.params if p.param_type == "argument"]
        if not args:
            return ""

        parts = []
        for arg in args:
            if arg.required:
                parts.append(f"<{arg.name}>")
            else:
                parts.append(f"[{arg.name}]")

        return " " + " ".join(parts)

    def _add_options_index(self) -> None:
        """Add an index of all options across all commands."""
        self._lines.extend([
            "## Options Index",
            "",
            "Complete index of all CLI options:",
            "",
            "| Option | Commands | Description |",
            "|--------|----------|-------------|",
        ])

        # Collect all options
        options_map = {}
        self._collect_options(self.data, options_map)

        for opt_name in sorted(options_map.keys()):
            info = options_map[opt_name]
            commands = ", ".join(f"`{c}`" for c in info["commands"][:3])
            if len(info["commands"]) > 3:
                commands += f" (+{len(info['commands']) - 3} more)"
            self._lines.append(f"| `--{opt_name}` | {commands} | {info['help']} |")

        self._lines.append("")

    def _collect_options(
        self,
        cmd: CommandInfo,
        options_map: dict
    ) -> None:
        """Recursively collect all options."""
        for param in cmd.params:
            if param.param_type == "option":
                if param.name not in options_map:
                    options_map[param.name] = {
                        "help": param.help or "-",
                        "commands": []
                    }
                options_map[param.name]["commands"].append(cmd.path)

        for sub in cmd.subcommands:
            self._collect_options(sub, options_map)

    def _add_footer(self) -> None:
        """Add document footer."""
        self._lines.extend([
            "---",
            "",
            "*This reference was auto-generated. For the latest version, run:*",
            "",
            "```bash",
            "vibey docs generate cli",
            "```",
        ])

    def write(self, path: str) -> None:
        """Write generated documentation to file."""
        content = self.generate()
        Path(path).write_text(content)


def generate_cli_reference(output_path: str = "docs/reference/CLI_REFERENCE.md") -> str:
    """
    Generate CLI reference and write to file.

    Args:
        output_path: Where to write the generated documentation

    Returns:
        The generated Markdown content
    """
    generator = CLIReferenceGenerator()
    generator.write(output_path)
    return generator.generate()
```

### Output Format

**File:** `docs/reference/CLI_REFERENCE.md`

Structure:
1. Header with generation timestamp
2. Table of contents (nested, linked)
3. Each command section:
   - Full path as header
   - Description from help text
   - Usage line
   - Options table
   - Arguments table
   - Examples (if available)
4. Options index (all options across all commands)
5. Footer with regeneration instructions

### Acceptance Criteria

- [ ] Generator implemented at `vibey/operations/docs/cli_reference_generator.py`
- [ ] Markdown output is well-formatted
- [ ] Table of contents with working links
- [ ] Options and arguments documented in tables
- [ ] Examples included where available
- [ ] Options index generated
- [ ] Hidden commands excluded
- [ ] Deprecated commands marked

---

## Task 4: Add Usage Examples to CLI Commands

**ID:** `01KC81GRE23T0KSHR4ZCES476R`
**Type:** Documentation
**Priority:** Medium
**Estimated Tokens:** 30,000

### Objective

Ensure every CLI command has extractable usage examples in its docstring.

### Commands to Update

Based on current CLI structure, the following command groups need examples:

#### Top-Level Commands (11 groups)

| Group | Commands | Examples Needed |
|-------|----------|-----------------|
| artifact | ~5 | 5 |
| audit | ~3 | 3 |
| auth | ~4 | 4 |
| config | ~5 | 5 |
| content | ~6 | 6 |
| deploy | ~3 | 3 |
| docs | ~4 | 4 |
| export | ~3 | 3 |
| git | ~3 | 3 |
| roadmap | ~50 | 50 |
| validate | ~4 | 4 |

**Total:** ~90 commands needing examples

### Example Format

```python
@cli.command()
def status():
    """
    Show roadmap status - tracks, sprints, and tasks.

    Displays hierarchical view of all roadmap items with their
    current status, progress, and blockers.

    Examples:

      vibey roadmap status              # Show all tracks
      vibey roadmap status --all        # Include completed items
      vibey roadmap status --track auth # Filter by track
      vibey roadmap status --json       # JSON output
    """
    pass
```

### Implementation Approach

1. Audit all commands for existing examples
2. Add examples following the pattern above
3. Ensure examples are real, working commands
4. Include common use cases and option combinations

### Files to Modify

- `vibey/cli/main.py` - Root and group commands
- `vibey/cli/commands.py` - Core command implementations
- `vibey/cli/roadmap_commands/*.py` - Roadmap subcommands (largest set)

### Acceptance Criteria

- [ ] All commands have at least 2 usage examples
- [ ] Examples follow consistent format (`Examples:` section)
- [ ] Examples are actual working commands
- [ ] Examples demonstrate key options
- [ ] Introspector can extract all examples

---

## Task 5: Generate Initial CLI Reference Guide

**ID:** `01KC81GRE23T0KSHR4ZCES476V`
**Type:** Documentation
**Priority:** Medium
**Estimated Tokens:** 10,000

### Objective

Run the generator to produce the first auto-generated CLI reference with verified 100% coverage.

### Steps

1. Run introspection:
   ```bash
   python -c "from vibey.operations.docs.cli_introspector import introspect_cli; print(len(introspect_cli().subcommands))"
   ```

2. Generate reference:
   ```bash
   python -c "from vibey.operations.docs.cli_reference_generator import generate_cli_reference; generate_cli_reference()"
   ```

3. Verify coverage:
   - Count commands in generated doc
   - Compare against `vibey --help` output
   - Ensure no commands missing

4. Review output:
   - Check formatting
   - Verify links work
   - Confirm examples render properly

### Verification Checklist

- [ ] All 11 top-level groups documented
- [ ] All ~50 roadmap subcommands documented
- [ ] All options documented with types
- [ ] All arguments documented
- [ ] Examples render in code blocks
- [ ] Table of contents links work
- [ ] No hidden commands in output
- [ ] Deprecated commands marked

### Output

**File:** `docs/reference/CLI_REFERENCE.md`

Expected size: ~3,000-5,000 lines

### Acceptance Criteria

- [ ] Reference generated successfully
- [ ] 100% command coverage verified
- [ ] Output committed to repository
- [ ] No formatting issues

---

## Task 6: Implement 'vibey docs generate cli' Command

**ID:** `01KC81GRE23T0KSHR4ZCES476S`
**Type:** Development
**Priority:** Medium
**Estimated Tokens:** 8,000

### Objective

Add a CLI command to regenerate CLI reference documentation on demand.

### Implementation

**File:** `vibey/cli/docs.py` (add to existing docs group)

```python
@docs.command("generate")
@click.argument("doc_type", type=click.Choice(["cli", "mcp", "all"]))
@click.option(
    "--output", "-o",
    type=click.Path(),
    help="Custom output path (default: docs/reference/)"
)
@click.option(
    "--check", is_flag=True,
    help="Check if docs are up-to-date without regenerating"
)
@click.option(
    "--verbose", "-v", is_flag=True,
    help="Show detailed generation progress"
)
def generate(doc_type: str, output: Optional[str], check: bool, verbose: bool):
    """
    Generate reference documentation from code.

    Introspects the codebase and generates up-to-date reference
    documentation. Use --check to verify docs match code.

    Examples:

      vibey docs generate cli          # Generate CLI reference
      vibey docs generate cli --check  # Check if up-to-date
      vibey docs generate all          # Generate all docs
      vibey docs generate cli -o ./my-docs/CLI.md
    """
    from vibey.operations.docs.cli_reference_generator import (
        CLIReferenceGenerator,
        generate_cli_reference
    )

    if doc_type in ("cli", "all"):
        output_path = output or "docs/reference/CLI_REFERENCE.md"

        if check:
            # Check mode - compare generated vs existing
            generator = CLIReferenceGenerator()
            new_content = generator.generate()

            try:
                with open(output_path) as f:
                    existing = f.read()

                if new_content == existing:
                    click.echo("✅ CLI reference is up-to-date")
                else:
                    click.echo("❌ CLI reference is out of date")
                    click.echo(f"   Run 'vibey docs generate cli' to update")
                    raise SystemExit(1)
            except FileNotFoundError:
                click.echo("❌ CLI reference not found")
                raise SystemExit(1)
        else:
            # Generate mode
            if verbose:
                click.echo("🔍 Introspecting CLI commands...")

            generate_cli_reference(output_path)

            click.echo(f"✅ Generated CLI reference: {output_path}")
```

### Usage

```bash
# Generate CLI reference
vibey docs generate cli

# Check if docs are current (for CI)
vibey docs generate cli --check

# Custom output location
vibey docs generate cli -o ./docs/CLI.md

# Generate all docs
vibey docs generate all
```

### Acceptance Criteria

- [ ] Command implemented in docs group
- [ ] Generate mode works correctly
- [ ] Check mode compares and reports drift
- [ ] Custom output path supported
- [ ] Help text and examples included
- [ ] Exit codes appropriate for CI

---

## Task 7: Implement Drift Detection

**ID:** `01KC81GRE23T0KSHR4ZCES476T`
**Type:** Development
**Priority:** Medium
**Estimated Tokens:** 12,000

### Objective

Build a CI check that fails if generated documentation drifts from committed version.

### Implementation

#### 1. GitHub Actions Workflow

**File:** `.github/workflows/docs-drift.yml`

```yaml
name: Documentation Drift Check

on:
  push:
    paths:
      - 'vibey/cli/**'
      - 'docs/reference/CLI_REFERENCE.md'
  pull_request:
    paths:
      - 'vibey/cli/**'

jobs:
  check-cli-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e .

      - name: Check CLI reference drift
        run: |
          vibey docs generate cli --check

      - name: Report drift
        if: failure()
        run: |
          echo "::error::CLI documentation is out of date!"
          echo "Run 'vibey docs generate cli' locally and commit the changes."
```

#### 2. Pre-commit Hook (Optional)

**File:** `.pre-commit-config.yaml` (add entry)

```yaml
  - repo: local
    hooks:
      - id: check-cli-docs
        name: Check CLI docs drift
        entry: vibey docs generate cli --check
        language: system
        files: ^vibey/cli/.*\.py$
        pass_filenames: false
```

#### 3. Makefile Target

**File:** `Makefile` (add target)

```makefile
.PHONY: check-docs
check-docs:
	vibey docs generate cli --check
	vibey docs generate mcp --check

.PHONY: generate-docs
generate-docs:
	vibey docs generate all
```

### CI Integration Points

| Trigger | Action |
|---------|--------|
| PR with CLI changes | Check drift, fail if outdated |
| Push to main | Generate and commit if needed |
| Manual trigger | Force regeneration |

### Acceptance Criteria

- [ ] GitHub Actions workflow implemented
- [ ] CI fails on documentation drift
- [ ] Clear error messages guide developers
- [ ] Optional pre-commit hook available
- [ ] Makefile targets for local development

---

## File Structure After Sprint

```
vibey/
├── operations/
│   └── docs/
│       ├── __init__.py
│       ├── cli_introspector.py      # Task 2
│       └── cli_reference_generator.py  # Task 3
├── cli/
│   ├── main.py                      # Task 4 (examples added)
│   ├── commands.py                  # Task 4 (examples added)
│   ├── docs.py                      # Task 6 (generate command)
│   └── roadmap_commands/*.py        # Task 4 (examples added)
│
docs/
├── reference/
│   └── CLI_REFERENCE.md             # Task 5 (generated)
│
.github/
└── workflows/
    └── docs-drift.yml               # Task 7

.vibey/roadmap/context/sprints/user-journey-phase-2-1/
├── SPRINT_PLAN.md                   # This document
└── CLI_INTROSPECTION_DESIGN.md      # Task 1 output
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Click API changes | Low | Medium | Pin Click version, test on upgrades |
| Complex command structures | Medium | Low | Handle edge cases in introspector |
| Large generated docs | Medium | Low | Add TOC, improve navigation |
| Example extraction fails | Medium | Medium | Fallback to basic format |
| CI timeouts | Low | Low | Cache introspection results |

---

## Definition of Done

- [ ] All 7 tasks completed
- [ ] 100% CLI command coverage in generated docs
- [ ] CI drift detection passing
- [ ] Documentation reviewed for accuracy
- [ ] No regressions in existing CLI functionality
- [ ] Sprint summary written
