# ADR-0004: Click for CLI Implementation

## Status

Accepted

## Context

Vibey needs a robust CLI interface for roadmap management, deployment, and documentation commands. Requirements:

- 150+ commands organized in groups
- Consistent help text and documentation
- Tab completion support
- Testable command implementations
- Good error handling

Options considered:
- **argparse** (Python stdlib)
- **Click** (Pallets project)
- **Typer** (Click wrapper with type hints)
- **Rich CLI** (custom with Rich library)

## Decision

Use Click for CLI implementation.

**Structure:**
```python
@click.group()
def cli():
    """Vibey Agent Framework CLI."""
    pass

@cli.group()
def roadmap():
    """Roadmap management commands."""
    pass

@roadmap.command('status')
@click.option('--backend', type=click.Choice(['auto', 'sqlite', 'yaml']))
def roadmap_status(backend):
    """Show roadmap status."""
    ...
```

## Consequences

### Positive

- **Mature ecosystem**: Well-tested, widely used
- **Composable**: Commands, groups, options compose cleanly
- **Auto-help**: Generates help text from docstrings
- **Testing**: `CliRunner` for isolated command testing
- **Decorators**: Declarative command definition
- **Error handling**: Built-in exception handling
- **Completion**: Shell completion generation

### Negative

- **Learning curve**: Different patterns than argparse
- **Implicit magic**: Decorator behavior can be surprising
- **Dependency**: External library (not stdlib)

### Neutral

- Similar patterns to Flask (same maintainers)
- Can integrate with Rich for enhanced output

## Implementation Patterns

### Command Groups

```python
@cli.group()
def roadmap():
    """Roadmap management commands."""
    pass

@cli.group()
def deploy():
    """Deployment commands."""
    pass

@cli.group()
def docs():
    """Documentation commands."""
    pass
```

### Options and Arguments

```python
@roadmap.command('show')
@click.argument('item_id')
@click.option('--format', '-f', type=click.Choice(['text', 'json', 'yaml']))
@click.option('--verbose', '-v', is_flag=True)
@click.pass_context
def roadmap_show(ctx, item_id, format, verbose):
    """Show details for a track, sprint, or task."""
    ...
```

### Context Passing

```python
@cli.group()
@click.option('--backend', type=click.Choice(['auto', 'sqlite', 'yaml']))
@click.pass_context
def roadmap(ctx, backend):
    ctx.ensure_object(dict)
    ctx.obj['backend'] = backend

@roadmap.command('status')
@click.pass_context
def status(ctx):
    backend = ctx.obj.get('backend', 'auto')
    ...
```

### Testing

```python
from click.testing import CliRunner
from vibey.cli.main import cli

def test_roadmap_status():
    runner = CliRunner()
    result = runner.invoke(cli, ['roadmap', 'status'])
    assert result.exit_code == 0
    assert 'Tracks:' in result.output
```

## Alternatives Considered

### argparse (stdlib)

**Pros:**
- No dependencies
- Well-documented

**Cons:**
- Verbose subcommand setup
- Manual help formatting
- No built-in testing support

### Typer

**Pros:**
- Type hints for arguments
- Modern, less boilerplate

**Cons:**
- Wrapper around Click (dependency chain)
- Less mature ecosystem
- Some Click features harder to access

### Custom with Rich

**Pros:**
- Full control
- Beautiful output

**Cons:**
- Significant development effort
- Reinventing solved problems

## References

- [Click documentation](https://click.palletsprojects.com/)
- CLI implementation in `vibey/cli/main.py`
- Auto-generated CLI reference via introspection
