# CLI Introspection Architecture Design

**Task ID:** `01KC81GRE23T0KSHR4ZCES476N`
**Sprint:** Phase 2.1 - CLI Reference Guide (Auto-Generated)
**Status:** In Progress
**Created:** 2025-12-12

---

## 1. Overview

This document specifies the architecture for a CLI introspection system that extracts structured documentation data from Click command trees. The goal is to enable automatic generation of CLI reference documentation that cannot drift from the implementation.

### 1.1 Requirements

| Requirement | Description |
|-------------|-------------|
| **Complete Coverage** | Extract data from all 162 CLI commands |
| **Structured Output** | JSON-serializable data model |
| **Example Extraction** | Parse examples from docstrings and help text |
| **Nested Support** | Handle deeply nested command groups (up to 4 levels) |
| **Metadata Capture** | Include hidden, deprecated, and flag information |
| **Deterministic** | Same input always produces same output |

### 1.2 Current CLI Structure

```
vibey (root)
├── roadmap/         # 57 commands (including nested)
│   ├── audit/       # 4 subcommands
│   ├── checkpoint/  # 5 subcommands
│   ├── edit/        # 4 subcommands
│   └── db/          # 9 subcommands (including nested)
├── deploy/          # 2 commands
├── docs/            # 1 command
├── config/          # 5 commands (including platform/)
├── validate/        # 2 commands
├── export/          # 5 commands
├── git/             # 32 commands (including nested)
│   ├── branch/      # 5 subcommands
│   ├── hooks/       # 4 subcommands
│   └── sprint/      # 5 subcommands
├── content/         # 7 commands
├── artifact/        # 7 commands
├── auth/            # 7 commands
└── audit/           # 2 commands

Total: 162 commands
Max depth: 4 levels (vibey → roadmap → db → query → blocked)
```

---

## 2. Data Model

### 2.1 Core Types

```python
from dataclasses import dataclass, field
from typing import List, Optional, Any, Literal
from enum import Enum


class ParamKind(Enum):
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
```

### 2.2 JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CLIStructure",
  "type": "object",
  "required": ["root", "version", "total_commands", "max_depth", "generated_at"],
  "properties": {
    "root": { "$ref": "#/definitions/CommandInfo" },
    "version": { "type": "string" },
    "total_commands": { "type": "integer" },
    "max_depth": { "type": "integer" },
    "generated_at": { "type": "string", "format": "date-time" }
  },
  "definitions": {
    "CommandInfo": {
      "type": "object",
      "required": ["name", "path"],
      "properties": {
        "name": { "type": "string" },
        "path": { "type": "string" },
        "help": { "type": ["string", "null"] },
        "short_help": { "type": ["string", "null"] },
        "params": {
          "type": "array",
          "items": { "$ref": "#/definitions/ParamInfo" }
        },
        "subcommands": {
          "type": "array",
          "items": { "$ref": "#/definitions/CommandInfo" }
        },
        "examples": {
          "type": "array",
          "items": { "$ref": "#/definitions/ExampleInfo" }
        },
        "deprecated": { "type": "boolean" },
        "hidden": { "type": "boolean" },
        "is_group": { "type": "boolean" }
      }
    },
    "ParamInfo": {
      "type": "object",
      "required": ["name", "kind", "type_str", "required"],
      "properties": {
        "name": { "type": "string" },
        "kind": { "type": "string", "enum": ["option", "argument"] },
        "type_str": { "type": "string" },
        "required": { "type": "boolean" },
        "default": {},
        "help": { "type": ["string", "null"] },
        "multiple": { "type": "boolean" },
        "is_flag": { "type": "boolean" },
        "envvar": { "type": ["string", "null"] },
        "opts": { "type": "array", "items": { "type": "string" } }
      }
    },
    "ExampleInfo": {
      "type": "object",
      "required": ["command"],
      "properties": {
        "command": { "type": "string" },
        "description": { "type": ["string", "null"] }
      }
    }
  }
}
```

---

## 3. Tree Traversal Algorithm

### 3.1 Recursive Traversal

```python
def introspect_command(
    cmd: click.Command,
    parent_path: str = "",
    depth: int = 0
) -> CommandInfo:
    """
    Recursively introspect a Click command and its subcommands.

    Algorithm:
    1. Build full path from parent path and command name
    2. Extract command metadata (help, deprecated, hidden)
    3. Extract all parameters
    4. Parse examples from help text
    5. If Group, recursively process all subcommands
    6. Return CommandInfo structure

    Args:
        cmd: Click command to introspect
        parent_path: Path of parent command (e.g., "roadmap")
        depth: Current nesting depth for metrics

    Returns:
        CommandInfo with all extracted data
    """
    # Build path
    if parent_path:
        path = f"{parent_path} {cmd.name}"
    else:
        path = cmd.name or "vibey"

    # Create CommandInfo
    info = CommandInfo(
        name=cmd.name or "vibey",
        path=path,
        help=cmd.help,
        short_help=getattr(cmd, 'short_help', None),
        params=extract_params(cmd),
        examples=extract_examples(cmd),
        deprecated=getattr(cmd, 'deprecated', False),
        hidden=getattr(cmd, 'hidden', False),
        is_group=isinstance(cmd, click.Group)
    )

    # Recurse into subcommands
    if isinstance(cmd, click.Group):
        for name in sorted(cmd.commands.keys()):
            subcmd = cmd.commands[name]
            info.subcommands.append(
                introspect_command(subcmd, path, depth + 1)
            )

    return info
```

### 3.2 Parameter Extraction

```python
def extract_params(cmd: click.Command) -> List[ParamInfo]:
    """
    Extract parameter information from a Click command.

    Handles:
    - click.Option: Named options with -- prefix
    - click.Argument: Positional arguments
    - click.Choice: Enumerated values
    - Flags: Boolean options
    - Multiple: Repeated options
    - Environment variables: ENVVAR binding
    """
    params = []

    for param in cmd.params:
        # Determine kind
        if isinstance(param, click.Option):
            kind = ParamKind.OPTION
        else:
            kind = ParamKind.ARGUMENT

        # Extract type string
        type_str = get_type_string(param.type)

        # Build ParamInfo
        params.append(ParamInfo(
            name=param.name,
            kind=kind,
            type_str=type_str,
            required=param.required,
            default=normalize_default(param.default),
            help=getattr(param, 'help', None),
            multiple=getattr(param, 'multiple', False),
            is_flag=getattr(param, 'is_flag', False),
            envvar=getattr(param, 'envvar', None),
            opts=list(getattr(param, 'opts', []))
        ))

    return params


def get_type_string(param_type: click.ParamType) -> str:
    """Convert Click parameter type to human-readable string."""
    if isinstance(param_type, click.Choice):
        return f"Choice({sorted(param_type.choices)})"
    elif isinstance(param_type, click.IntRange):
        return f"IntRange({param_type.min}, {param_type.max})"
    elif isinstance(param_type, click.FloatRange):
        return f"FloatRange({param_type.min}, {param_type.max})"
    elif isinstance(param_type, click.Path):
        parts = []
        if param_type.exists:
            parts.append("exists")
        if param_type.file_okay:
            parts.append("file")
        if param_type.dir_okay:
            parts.append("dir")
        return f"Path({', '.join(parts)})" if parts else "PATH"
    elif isinstance(param_type, click.File):
        return f"File({param_type.mode})"
    else:
        return param_type.name.upper()


def normalize_default(default: Any) -> Any:
    """Normalize default values for JSON serialization."""
    if default is None or default == ():
        return None
    if callable(default):
        return "<dynamic>"
    return default
```

### 3.3 Example Extraction Strategy

Examples are extracted in the following order of precedence:

#### Strategy 1: Custom `examples` Attribute
```python
@cli.command()
@click.pass_context
def status(ctx):
    """Show roadmap status."""
    pass

# Attach examples as attribute
status.examples = [
    ExampleInfo("vibey roadmap status", "Show all tracks"),
    ExampleInfo("vibey roadmap status --track my-track", "Show specific track"),
]
```

#### Strategy 2: Parse from Docstring
```python
def extract_examples_from_docstring(help_text: str) -> List[ExampleInfo]:
    """
    Parse examples from docstring.

    Recognized formats:

    1. Examples section with indented commands:
       '''
       Examples:
         vibey roadmap status
         vibey roadmap status --all
       '''

    2. Examples section with descriptions:
       '''
       Examples:
         # Show all tracks
         vibey roadmap status

         # Show specific track
         vibey roadmap status --track my-track
       '''

    3. Code blocks:
       '''
       Example:
       ```
       vibey roadmap status
       ```
       '''
    """
    examples = []

    if not help_text:
        return examples

    # Find Examples section
    lines = help_text.split('\n')
    in_examples = False
    current_description = None

    for line in lines:
        stripped = line.strip()

        # Detect start of examples section
        if stripped.lower().startswith('example'):
            in_examples = True
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

        # Code block markers
        if stripped.startswith('```'):
            continue

        # Command line (starts with vibey or $ vibey)
        if stripped.startswith('vibey') or stripped.startswith('$ vibey'):
            cmd = stripped.lstrip('$ ')
            examples.append(ExampleInfo(
                command=cmd,
                description=current_description
            ))
            current_description = None

    return examples
```

#### Strategy 3: Infer from Command Path
```python
def generate_basic_example(cmd_info: CommandInfo) -> ExampleInfo:
    """Generate a basic example from command path and params."""
    parts = [cmd_info.path]

    # Add required arguments
    for param in cmd_info.params:
        if param.kind == ParamKind.ARGUMENT and param.required:
            parts.append(f"<{param.name}>")

    return ExampleInfo(
        command=' '.join(parts),
        description=f"Basic usage of {cmd_info.name}"
    )
```

---

## 4. Error Handling

### 4.1 Malformed Commands

| Scenario | Handling |
|----------|----------|
| Missing help text | Use `short_help` or `None` |
| Circular references | Track visited commands, skip duplicates |
| Invalid parameter types | Fall back to `"UNKNOWN"` type string |
| Non-serializable defaults | Convert to `"<non-serializable>"` |
| Unicode issues | Encode/decode with error handling |

### 4.2 Error Recovery

```python
class IntrospectionError(Exception):
    """Error during CLI introspection."""
    def __init__(self, message: str, command_path: str, cause: Exception = None):
        self.message = message
        self.command_path = command_path
        self.cause = cause
        super().__init__(f"{command_path}: {message}")


def safe_introspect(cmd: click.Command, parent_path: str = "") -> CommandInfo:
    """
    Introspect with error recovery.

    On error:
    1. Log warning with command path
    2. Return partial CommandInfo with error note
    3. Continue processing other commands
    """
    try:
        return introspect_command(cmd, parent_path)
    except Exception as e:
        path = f"{parent_path} {cmd.name}".strip()
        logging.warning(f"Error introspecting {path}: {e}")

        # Return partial info
        return CommandInfo(
            name=cmd.name or "unknown",
            path=path,
            help=f"[Error: {e}]",
            is_group=isinstance(cmd, click.Group)
        )
```

---

## 5. Output Formats

### 5.1 JSON Output

```python
def to_json(structure: CLIStructure, indent: int = 2) -> str:
    """Serialize CLI structure to JSON."""
    return json.dumps(
        asdict(structure),
        indent=indent,
        default=str,  # Handle non-serializable types
        ensure_ascii=False
    )
```

### 5.2 YAML Output (Optional)

```python
def to_yaml(structure: CLIStructure) -> str:
    """Serialize CLI structure to YAML."""
    import yaml
    return yaml.dump(
        asdict(structure),
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False
    )
```

---

## 6. Integration Points

### 6.1 Entry Point

```python
# vibey/operations/docs/cli_introspector.py

from vibey.cli.main import cli as root_cli

def introspect_cli() -> CLIStructure:
    """
    Introspect the Vibey CLI and return structured data.

    Usage:
        from vibey.operations.docs.cli_introspector import introspect_cli

        structure = introspect_cli()
        print(f"Total commands: {structure.total_commands}")
    """
    from datetime import datetime, timezone

    root = introspect_command(root_cli)
    total, max_depth = count_commands(root)

    return CLIStructure(
        root=root,
        version=get_cli_version(),
        total_commands=total,
        max_depth=max_depth,
        generated_at=datetime.now(timezone.utc).isoformat()
    )
```

### 6.2 CLI Command Integration

```python
# In vibey/cli/main.py

@docs.command('introspect')
@click.option('--format', '-f', type=click.Choice(['json', 'yaml']), default='json')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
def docs_introspect(format: str, output: str):
    """
    Introspect CLI structure and output documentation data.

    Examples:
      # Output to stdout as JSON
      vibey docs introspect

      # Save to file
      vibey docs introspect -o cli_structure.json

      # Output as YAML
      vibey docs introspect -f yaml
    """
    from vibey.operations.docs.cli_introspector import introspect_cli

    structure = introspect_cli()

    if format == 'yaml':
        content = to_yaml(structure)
    else:
        content = to_json(structure)

    if output:
        Path(output).write_text(content)
        click.echo(f"Written to {output}")
    else:
        click.echo(content)
```

---

## 7. Testing Strategy

### 7.1 Unit Tests

```python
# tests/operations/docs/test_cli_introspector.py

def test_introspect_simple_command():
    """Test introspection of a simple command."""
    @click.command()
    @click.option('--name', '-n', help='Your name')
    def hello(name):
        """Say hello."""
        pass

    info = introspect_command(hello)

    assert info.name == 'hello'
    assert info.help == 'Say hello.'
    assert len(info.params) == 1
    assert info.params[0].name == 'name'
    assert info.params[0].opts == ['-n', '--name']


def test_introspect_group():
    """Test introspection of a command group."""
    @click.group()
    def parent():
        """Parent group."""
        pass

    @parent.command()
    def child():
        """Child command."""
        pass

    info = introspect_command(parent)

    assert info.is_group
    assert len(info.subcommands) == 1
    assert info.subcommands[0].name == 'child'
    assert info.subcommands[0].path == 'parent child'


def test_extract_examples_from_docstring():
    """Test example extraction from docstring."""
    help_text = '''
    Show roadmap status.

    Examples:
      # Show all tracks
      vibey roadmap status

      # Show specific track
      vibey roadmap status --track my-track
    '''

    examples = extract_examples_from_docstring(help_text)

    assert len(examples) == 2
    assert examples[0].command == 'vibey roadmap status'
    assert examples[0].description == 'Show all tracks'
```

### 7.2 Integration Tests

```python
def test_introspect_full_cli():
    """Test introspection of the full Vibey CLI."""
    from vibey.cli.main import cli

    structure = introspect_cli()

    # Verify counts
    assert structure.total_commands >= 150  # Known minimum
    assert structure.max_depth >= 3  # Known minimum

    # Verify root structure
    assert structure.root.name == 'vibey'
    assert structure.root.is_group

    # Verify roadmap group exists
    roadmap = next(
        (c for c in structure.root.subcommands if c.name == 'roadmap'),
        None
    )
    assert roadmap is not None
    assert roadmap.is_group

    # Verify JSON serialization
    json_output = to_json(structure)
    parsed = json.loads(json_output)
    assert parsed['total_commands'] == structure.total_commands
```

---

## 8. Performance Considerations

| Operation | Estimated Time | Notes |
|-----------|---------------|-------|
| Full CLI introspection | < 100ms | Single tree traversal |
| JSON serialization | < 10ms | Simple dict conversion |
| Example parsing | < 50ms | Regex on help strings |
| Total | < 200ms | Acceptable for CLI command |

### 8.1 Caching Strategy

```python
_cached_structure: Optional[CLIStructure] = None
_cache_time: Optional[float] = None
CACHE_TTL = 60  # seconds

def introspect_cli(use_cache: bool = True) -> CLIStructure:
    """
    Introspect CLI with optional caching.

    Cache is invalidated after CACHE_TTL seconds or when
    use_cache=False is passed.
    """
    global _cached_structure, _cache_time

    now = time.time()
    if use_cache and _cached_structure and _cache_time:
        if now - _cache_time < CACHE_TTL:
            return _cached_structure

    structure = _do_introspect()
    _cached_structure = structure
    _cache_time = now

    return structure
```

---

## 9. Acceptance Criteria Checklist

- [x] Complete data model documented (Section 2)
- [x] Tree traversal algorithm specified (Section 3)
- [x] JSON output schema defined (Section 2.2)
- [x] Example extraction strategy chosen (Section 3.3)
- [x] Edge cases documented (Section 4)
- [x] Integration points defined (Section 6)
- [x] Testing strategy outlined (Section 7)

---

## 10. Next Steps

1. **Task 2:** Implement `cli_introspector.py` based on this design
2. **Task 3:** Implement Markdown generator using introspection output
3. **Task 4:** Add examples to CLI commands following extraction patterns
4. **Task 5:** Generate initial reference guide
5. **Task 6:** Add `vibey docs generate cli` command
6. **Task 7:** Implement drift detection in CI

---

## Appendix A: Sample Output

```json
{
  "root": {
    "name": "vibey",
    "path": "vibey",
    "help": "Vibey Agent Framework - Platform-agnostic agentic orchestration...",
    "short_help": null,
    "params": [
      {
        "name": "verbose",
        "kind": "option",
        "type_str": "BOOL",
        "required": false,
        "default": false,
        "help": "Enable verbose output",
        "multiple": false,
        "is_flag": true,
        "envvar": null,
        "opts": ["-v", "--verbose"]
      }
    ],
    "subcommands": [
      {
        "name": "roadmap",
        "path": "roadmap",
        "help": "Manage roadmap system - tracks, sprints, tasks...",
        "is_group": true,
        "subcommands": [
          {
            "name": "status",
            "path": "roadmap status",
            "help": "Show roadmap status.",
            "examples": [
              {
                "command": "vibey roadmap status",
                "description": "Show all tracks"
              },
              {
                "command": "vibey roadmap status --track my-track",
                "description": "Show specific track"
              }
            ]
          }
        ]
      }
    ],
    "examples": [
      {
        "command": "vibey roadmap init",
        "description": "Initialize a new roadmap"
      }
    ],
    "deprecated": false,
    "hidden": false,
    "is_group": true
  },
  "version": "2.5.0",
  "total_commands": 162,
  "max_depth": 4,
  "generated_at": "2025-12-12T18:30:00+00:00"
}
```

---

## Appendix B: Command Categories

| Category | Commands | Notes |
|----------|----------|-------|
| Roadmap Core | init, status, sync, show | Basic CRUD |
| Roadmap Creation | create-track, create-sprint, create-task | Entity creation |
| Roadmap Lifecycle | start, complete | Status transitions |
| Roadmap Queries | context, summarize | Information retrieval |
| Roadmap Git | add-commit, sync-commits, verify-commits | Git integration |
| Roadmap Validation | validate-*, repair | Data integrity |
| Roadmap Edit | edit file, edit bulk, edit rollback | In-place modification |
| Roadmap DB | db init, db rebuild, db query | SQLite operations |
| Deployment | deploy run, deploy list | Platform deployment |
| Documentation | docs generate | Doc generation |
| Configuration | config show, config validate, config migrate | Config management |
| Git Operations | git analyze, git tasks, git history | Git analysis |
| Content | content list, content show, content search | Framework content |
| Artifacts | artifact list, artifact show, artifact adopt | Artifact management |
| Auth | auth setup, auth status | Authentication |
| Audit | audit inventory, audit classify | Codebase audit |
