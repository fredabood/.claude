"""
Vibey CLI - Main entry point for the Vibey Agent Framework.

This module provides the main CLI interface using Click, organizing all
framework commands into logical groups.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Version
__version__ = "2.5.0"

# Console for rich output
console = Console()


def print_banner():
    """Print the Vibey CLI banner."""
    title = Text("Vibey Agent Framework", style="bold green")
    subtitle = Text(f"Version {__version__} - Platform-Agnostic CLI", style="dim")

    panel = Panel(
        Text.assemble(title, "\n", subtitle),
        border_style="blue",
        padding=(1, 2)
    )
    console.print(panel)


@click.group()
@click.version_option(version=__version__, prog_name="vibey")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--quiet', '-q', is_flag=True, help='Suppress non-essential output')
@click.pass_context
def cli(ctx, verbose: bool, quiet: bool):
    """
    Vibey Agent Framework - Platform-agnostic agentic orchestration.

    The Vibey CLI provides unified access to all framework functionality:
    roadmap management, deployment, configuration, and documentation.

    Examples:

      # Initialize a new roadmap
      vibey roadmap init

      # Deploy to Claude Code
      vibey deploy --platform claude-code

      # Generate documentation
      vibey docs generate

      # Show roadmap status
      vibey roadmap status

    For command-specific help:

      vibey roadmap --help
      vibey deploy --help
    """
    ctx.ensure_object(dict)
    ctx.obj['VERBOSE'] = verbose
    ctx.obj['QUIET'] = quiet

    if not quiet and ctx.invoked_subcommand is None:
        print_banner()


# ============================================================================
# Roadmap Command Group
# ============================================================================

@cli.group()
@click.pass_context
def roadmap(ctx):
    """
    Manage roadmap system - tracks, sprints, tasks, and dependencies.

    The roadmap system provides hierarchical project planning with:
    - Tracks: Major feature areas or work streams
    - Sprints: Time-boxed iterations within tracks
    - Tasks: Specific work items within sprints
    - Dependencies: Blocker relationships between items

    Examples:

      vibey roadmap init           # Initialize new roadmap
      vibey roadmap status         # Show current status
      vibey roadmap show sprint-1  # Show sprint details
      vibey roadmap start task-001 # Start a task
    """
    pass


@roadmap.command('init')
@click.option('--name', prompt='Roadmap name', help='Name of the roadmap')
@click.option('--version', default='1.0.0', help='Initial version')
@click.pass_context
def roadmap_init(ctx, name: str, version: str):
    """Initialize a new roadmap in .vibey/roadmap.yaml"""
    from vibey.cli.commands import roadmap_init_cmd

    exit_code = roadmap_init_cmd(name, version)
    sys.exit(exit_code)


@roadmap.command('status')
@click.option('--track', help='Show status for specific track')
@click.option('--sprint', help='Show status for specific sprint')
@click.pass_context
def roadmap_status(ctx, track: Optional[str], sprint: Optional[str]):
    """Show roadmap status - tracks, sprints, and tasks"""
    from vibey.cli.commands import roadmap_status_cmd

    exit_code = roadmap_status_cmd(track, sprint)
    sys.exit(exit_code)


@roadmap.command('show')
@click.argument('item_id')
@click.pass_context
def roadmap_show(ctx, item_id: str):
    """Show details for a track, sprint, or task"""
    from vibey.cli.commands import roadmap_show_cmd

    exit_code = roadmap_show_cmd(item_id)
    sys.exit(exit_code)


@roadmap.command('start')
@click.argument('item_id')
@click.pass_context
def roadmap_start(ctx, item_id: str):
    """Start a sprint or task"""
    from vibey.cli.commands import roadmap_start_cmd

    exit_code = roadmap_start_cmd(item_id)
    sys.exit(exit_code)


@roadmap.command('complete')
@click.argument('item_id')
@click.pass_context
def roadmap_complete(ctx, item_id: str):
    """Complete a sprint or task"""
    from vibey.cli.commands import roadmap_complete_cmd

    exit_code = roadmap_complete_cmd(item_id)
    sys.exit(exit_code)


@roadmap.command('context')
@click.argument('task_id')
@click.pass_context
def roadmap_context(ctx, task_id: str):
    """Get AI-optimized context for a task"""
    from vibey.cli.commands import roadmap_context_cmd

    exit_code = roadmap_context_cmd(task_id)
    sys.exit(exit_code)


@roadmap.command('summarize')
@click.argument('item_type', type=click.Choice(['sprint', 'task', 'track']))
@click.argument('item_id')
@click.pass_context
def roadmap_summarize(ctx, item_type: str, item_id: str):
    """Summarize a sprint, task, or track"""
    from vibey.cli.commands import roadmap_summarize_cmd

    exit_code = roadmap_summarize_cmd(item_type, item_id)
    sys.exit(exit_code)


# ============================================================================
# Deploy Command Group
# ============================================================================

@cli.group()
@click.pass_context
def deploy(ctx):
    """
    Deploy framework to target platforms.

    Supports multiple AI coding assistant platforms:
    - claude-code (Claude Code)
    - goose (Goose by Block)
    - cursor (Cursor IDE)
    - aider (Aider CLI)
    - continue (Continue.dev)

    Examples:

      vibey deploy --platform claude-code
      vibey deploy --platform goose --clean
      vibey deploy --list-platforms
    """
    pass


@deploy.command('run')
@click.option('--platform', type=click.Choice(['claude-code', 'goose', 'cursor', 'aider', 'continue']),
              required=True, help='Target platform')
@click.option('--clean', is_flag=True, help='Remove existing deployment first')
@click.pass_context
def deploy_run(ctx, platform: str, clean: bool):
    """Deploy framework to specified platform"""
    from vibey.cli.commands import deploy_cmd

    exit_code = deploy_cmd(platform, clean)
    sys.exit(exit_code)


@deploy.command('list-platforms')
@click.pass_context
def deploy_list_platforms(ctx):
    """List available deployment platforms"""
    console.print("[bold]Available Platforms:[/bold]")
    platforms = [
        ("claude-code", "Claude Code (current)", "✅"),
        ("goose", "Goose by Block", "🚧 In development"),
        ("cursor", "Cursor IDE", "📋 Planned"),
        ("aider", "Aider CLI", "📋 Planned"),
        ("continue", "Continue.dev", "📋 Planned"),
    ]

    for name, description, status in platforms:
        console.print(f"  {status} [cyan]{name:15}[/cyan] - {description}")


# ============================================================================
# Docs Command Group
# ============================================================================

@cli.group()
@click.pass_context
def docs(ctx):
    """
    Generate and manage documentation.

    Examples:

      vibey docs generate           # Generate all docs
      vibey docs generate --overwrite
      vibey docs context            # Generate context docs
    """
    pass


@docs.command('generate')
@click.option('--overwrite', is_flag=True, help='Overwrite existing docs')
@click.pass_context
def docs_generate(ctx, overwrite: bool):
    """Generate documentation from configuration"""
    from vibey.cli.commands import docs_generate_cmd

    exit_code = docs_generate_cmd(overwrite)
    sys.exit(exit_code)


# ============================================================================
# Config Command Group
# ============================================================================

@cli.group()
@click.pass_context
def config(ctx):
    """
    Manage framework configuration.

    Examples:

      vibey config show             # Show current config
      vibey config validate         # Validate config files
      vibey config migrate          # Migrate old config format
    """
    pass


@config.command('show')
@click.pass_context
def config_show(ctx):
    """Show current configuration"""
    from vibey.cli.commands import config_show_cmd

    exit_code = config_show_cmd()
    sys.exit(exit_code)


@config.command('validate')
@click.pass_context
def config_validate(ctx):
    """Validate configuration files"""
    from vibey.cli.commands import config_validate_cmd

    exit_code = config_validate_cmd()
    sys.exit(exit_code)


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point for the vibey CLI."""
    try:
        cli(obj={})
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
