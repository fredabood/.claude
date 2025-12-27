"""
CLI Commands for Implementation Mode.

This module provides CLI commands for running and controlling autonomous task
execution through the Implementation Mode loop.

Commands:
- vibey implement: Run the implementation loop (main command)
- vibey implement status: Show current implementation mode status
- vibey implement pause: Pause execution after current task completes
- vibey implement resume: Resume paused execution
- vibey implement stop: Stop execution immediately

State File: .vibey/implementation/state.yaml
PID File: .vibey/implementation/pid
Control File: .vibey/implementation/control

Design Reference:
- Implementation Mode Track
- Task NA: Implement vibey implement CLI command
- Task NB: Implement control commands
"""

import asyncio
import os
import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from vibey.services.implementation.display import ProgressDisplay
from vibey.services.implementation.state import LoopState, LoopStatus

# =============================================================================
# CONSTANTS
# =============================================================================

# Default paths for implementation mode files
IMPLEMENTATION_DIR = Path(".vibey/implementation")
STATE_FILE = IMPLEMENTATION_DIR / "state.yaml"
PID_FILE = IMPLEMENTATION_DIR / "pid"
CONTROL_FILE = IMPLEMENTATION_DIR / "control"

# Control signals
CONTROL_PAUSE = "PAUSE"
CONTROL_RESUME = "RESUME"
CONTROL_STOP = "STOP"

# Console for rich output
console = Console()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_implementation_dir() -> Path:
    """Get the implementation directory path (creates if needed)."""
    impl_dir = Path.cwd() / IMPLEMENTATION_DIR
    impl_dir.mkdir(parents=True, exist_ok=True)
    return impl_dir


def get_state_path() -> Path:
    """Get the state file path."""
    return Path.cwd() / STATE_FILE


def get_pid_path() -> Path:
    """Get the PID file path."""
    return Path.cwd() / PID_FILE


def get_control_path() -> Path:
    """Get the control file path."""
    return Path.cwd() / CONTROL_FILE


def read_pid() -> Optional[int]:
    """
    Read the PID of the running implementation loop.

    Returns:
        The PID if a valid PID file exists, None otherwise.
    """
    pid_path = get_pid_path()
    if not pid_path.exists():
        return None

    try:
        with open(pid_path, "r") as f:
            pid_str = f.read().strip()
            return int(pid_str) if pid_str else None
    except (ValueError, IOError):
        return None


def write_pid(pid: int) -> None:
    """
    Write the PID to the PID file.

    Args:
        pid: The process ID to write.
    """
    pid_path = get_pid_path()
    get_implementation_dir()  # Ensure directory exists
    with open(pid_path, "w") as f:
        f.write(str(pid))


def remove_pid() -> None:
    """Remove the PID file."""
    pid_path = get_pid_path()
    if pid_path.exists():
        pid_path.unlink()


def is_process_running(pid: int) -> bool:
    """
    Check if a process with the given PID is running.

    Args:
        pid: The process ID to check.

    Returns:
        True if the process is running, False otherwise.
    """
    try:
        # Sending signal 0 checks if process exists without affecting it
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def write_control(signal_type: str) -> None:
    """
    Write a control signal to the control file.

    Args:
        signal_type: One of CONTROL_PAUSE, CONTROL_RESUME, CONTROL_STOP
    """
    control_path = get_control_path()
    get_implementation_dir()  # Ensure directory exists
    with open(control_path, "w") as f:
        f.write(signal_type)


def read_control() -> Optional[str]:
    """
    Read the current control signal.

    Returns:
        The control signal if file exists, None otherwise.
    """
    control_path = get_control_path()
    if not control_path.exists():
        return None

    try:
        with open(control_path, "r") as f:
            return f.read().strip()
    except IOError:
        return None


def clear_control() -> None:
    """Remove the control file."""
    control_path = get_control_path()
    if control_path.exists():
        control_path.unlink()


def load_state() -> Optional[LoopState]:
    """
    Load the implementation loop state from the state file.

    Returns:
        LoopState if file exists and is valid, None otherwise.
    """
    state_path = get_state_path()
    if not state_path.exists():
        return None

    try:
        return LoopState.load(state_path)
    except Exception:
        return None


def save_state(state: LoopState) -> None:
    """
    Save the implementation loop state to the state file.

    Args:
        state: The LoopState to save.
    """
    state_path = get_state_path()
    get_implementation_dir()  # Ensure directory exists
    state.save(state_path)


# =============================================================================
# CLICK COMMAND GROUP
# =============================================================================


def _show_scope_required_help() -> None:
    """Display help message when no scope is specified."""
    console.print(
        Panel(
            "[bold cyan]Implementation Mode[/bold cyan]\n\n"
            "[yellow]Explicit scope required.[/yellow]\n\n"
            "To prevent accidental execution, you must specify what to run:\n\n"
            "  [bold]vibey implement --ticket <ULID>[/bold]\n"
            "    Execute a specific ticket and its descendants\n\n"
            "  [bold]vibey implement --all-tickets[/bold]\n"
            "    Execute all planned tickets (will prompt for confirmation)\n\n"
            "  [bold]vibey implement --dry-run --ticket <ULID>[/bold]\n"
            "    Preview what would be executed\n\n"
            "[dim]Use 'vibey implement --help' for all options[/dim]",
            title="Scope Required",
            border_style="yellow",
        )
    )


@click.group(invoke_without_command=True)
@click.option('--all-tickets', is_flag=True, help='Execute all planned tickets (requires confirmation)')
@click.option('--ticket', help='Execute specific ticket by ULID')
@click.option('--track', help='[DEPRECATED] Use --ticket instead')
@click.option('--sprint', help='[DEPRECATED] Use --ticket instead')
@click.option('--max-tasks', type=int, help='Stop after N tasks')
@click.option('--max-tokens', type=int, help='Stop after N tokens')
@click.option('--dry-run', is_flag=True, help='Show what would run without executing')
@click.option('--background', is_flag=True, help='Run as background process')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompts')
@click.pass_context
def implement(ctx, all_tickets, ticket, track, sprint, max_tasks, max_tokens, dry_run, background, yes):
    """
    Run implementation mode to execute planned tickets.

    REQUIRES explicit scope specification to prevent accidental execution.

    \b
    SCOPE OPTIONS (one required):
      --all-tickets         Execute entire roadmap (with confirmation)
      --ticket ULID         Execute specific ticket and its descendants

    \b
    EXAMPLES:
      vibey implement --ticket 01KC...     # Execute specific ticket
      vibey implement --all-tickets        # Execute all (with confirmation)
      vibey implement --dry-run            # Preview what would run

    \b
    DEPRECATED OPTIONS (still work, will be removed):
      --track <ULID>   → Use --ticket <ULID> instead
      --sprint <ULID>  → Use --ticket <ULID> instead

    \b
    CONTROL COMMANDS:
      vibey implement status             # Show current status
      vibey implement pause              # Pause after current task
      vibey implement resume             # Resume paused execution
      vibey implement stop               # Stop immediately
    """
    ctx.ensure_object(dict)

    # If a subcommand is being invoked, let it handle things
    if ctx.invoked_subcommand is not None:
        return

    # Deprecation warnings for --track and --sprint
    if track:
        console.print(
            f"[yellow]Warning:[/yellow] --track is deprecated. "
            f"Use [bold]--ticket {track}[/bold] instead.\n"
        )

    if sprint:
        console.print(
            f"[yellow]Warning:[/yellow] --sprint is deprecated. "
            f"Use [bold]--ticket {sprint}[/bold] instead.\n"
        )

    # Check for explicit scope
    has_scope = all_tickets or ticket or track or sprint

    if not has_scope:
        _show_scope_required_help()
        sys.exit(0)

    # Resolve scope - --ticket takes precedence over deprecated options
    scope_ulid = ticket or track or sprint

    # Run the main implementation loop
    exit_code = run_implementation_cmd(
        scope_ulid=scope_ulid,
        all_tickets=all_tickets,
        max_tasks=max_tasks,
        max_tokens=max_tokens,
        dry_run=dry_run,
        background=background,
        yes=yes,
    )
    sys.exit(exit_code)


# =============================================================================
# MAIN IMPLEMENTATION COMMAND
# =============================================================================


def run_implementation_cmd(
    scope_ulid: Optional[str] = None,
    all_tickets: bool = False,
    max_tasks: Optional[int] = None,
    max_tokens: Optional[int] = None,
    dry_run: bool = False,
    background: bool = False,
    yes: bool = False,
) -> int:
    """
    Run implementation mode to execute planned tickets.

    Args:
        scope_ulid: Specific ticket ULID to execute (and its descendants)
        all_tickets: Execute all planned tickets (requires confirmation)
        max_tasks: Stop after N tasks
        max_tokens: Stop after N tokens
        dry_run: Show what would run without executing
        background: Run as background process
        yes: Skip confirmation prompts

    Returns:
        Exit code (0 = success, 1 = error)
    """
    from vibey.services.implementation import (
        ClaudeTaskExecutor,
        ImplementConfig,
        ImplementationLoop,
        ProgressDisplay,
        TaskSelector,
    )

    # Determine roadmap root
    project_root = Path.cwd()
    roadmap_root = project_root / ".vibey" / "roadmap"

    if not roadmap_root.exists():
        console.print(
            "[red]Error:[/red] Roadmap not found at .vibey/roadmap/\n"
            "Run 'vibey roadmap init' to initialize a roadmap."
        )
        return 1

    # Check database exists (in roadmap dir or parent .vibey dir)
    db_path = roadmap_root / "roadmap.db"
    alt_db_path = project_root / ".vibey" / "roadmap.db"
    if not db_path.exists() and not alt_db_path.exists():
        console.print(
            "[red]Error:[/red] Roadmap database not found.\n"
            "Run 'vibey roadmap db rebuild' to create the database."
        )
        return 1

    # Handle --all-tickets confirmation (skip for dry_run - it's a safe operation)
    if all_tickets and not yes and not dry_run:
        # Count executable tasks for confirmation
        from vibey.services.implementation import TaskSelector
        selector = TaskSelector(roadmap_root)
        count = selector.count_remaining()

        if count == 0:
            console.print("[yellow]No executable tasks found.[/yellow]")
            return 0

        console.print(
            f"\n[bold yellow]Warning:[/bold yellow] About to execute [bold]{count}[/bold] planned tickets.\n"
        )
        if not click.confirm("Do you want to continue?"):
            console.print("[dim]Cancelled.[/dim]")
            return 0

    # Handle background mode
    if background:
        return _run_background(scope_ulid, all_tickets, max_tasks, max_tokens)

    # Handle dry-run mode
    if dry_run:
        return _run_dry_run(roadmap_root, scope_ulid, max_tasks)

    # Create configuration
    state_path = get_state_path()
    config = ImplementConfig(
        max_tasks=max_tasks,
        max_tokens=max_tokens,
        state_path=state_path,
        scope_ulid=scope_ulid,
        auto_save=True,
    )

    # Create state (or load existing)
    state = LoopState.load_or_create(state_path)

    # Create progress display
    display = ProgressDisplay(state, console=console)

    # Show startup banner
    _show_startup_banner(scope_ulid, all_tickets, max_tasks, max_tokens)

    # Write PID for status tracking
    write_pid(os.getpid())

    try:
        # Create components
        selector = TaskSelector(roadmap_root)
        executor = ClaudeTaskExecutor(
            config=config,
            roadmap_root=roadmap_root,
            working_directory=project_root,
        )

        # Create and run loop
        loop = ImplementationLoop(
            selector=selector,
            executor=executor,
            config=config,
            state=state,
        )

        # Run the async loop
        result = asyncio.run(loop.run())

        # Show final summary
        display.show_summary(state)
        display.show_task_results_table(limit=10)

        # Return exit code based on result
        if result.tasks_failed > 0:
            console.print(
                f"\n[yellow]Warning:[/yellow] {result.tasks_failed} task(s) failed"
            )
            return 1

        if result.stop_reason == "error":
            console.print(f"\n[red]Error:[/red] Loop stopped due to error")
            return 1

        console.print(
            f"\n[green]Success:[/green] Completed {result.tasks_completed} task(s)"
        )
        return 0

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print(
            "\n[dim]Hint: Make sure the Claude Code CLI is installed and in your PATH[/dim]"
        )
        return 1

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        return 130

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        return 1

    finally:
        # Clean up PID file
        remove_pid()


def _show_startup_banner(
    scope_ulid: Optional[str],
    all_tickets: bool,
    max_tasks: Optional[int],
    max_tokens: Optional[int],
) -> None:
    """Display startup banner with configuration."""
    lines = ["[bold cyan]Implementation Mode[/bold cyan]"]

    # Add scope info
    if all_tickets:
        lines.append("Scope: [bold]All planned tickets[/bold]")
    elif scope_ulid:
        scope_display = scope_ulid[:12] + "..." if len(scope_ulid) > 12 else scope_ulid
        lines.append(f"Scope: Ticket {scope_display}")

    # Add limits
    limits = []
    if max_tasks:
        limits.append(f"Max Tasks: {max_tasks}")
    if max_tokens:
        limits.append(f"Max Tokens: {max_tokens:,}")
    if limits:
        lines.append(f"Limits: {', '.join(limits)}")

    content = "\n".join(lines)
    panel = Panel(content, border_style="blue", padding=(0, 1))
    console.print(panel)
    console.print()


def _run_dry_run(
    roadmap_root: Path,
    scope_ulid: Optional[str],
    max_tasks: Optional[int],
) -> int:
    """
    Run in dry-run mode - show what would be executed.

    Args:
        roadmap_root: Path to roadmap directory
        scope_ulid: Scope ticket ULID (or None for all)
        max_tasks: Maximum tasks to show

    Returns:
        Exit code
    """
    from vibey.services.implementation import TaskSelector

    console.print(
        Panel(
            "[bold cyan]Implementation Mode - Dry Run[/bold cyan]\n"
            "[dim]Showing tasks that would be executed[/dim]",
            border_style="yellow",
        )
    )
    console.print()

    try:
        selector = TaskSelector(roadmap_root)

        # Get executable tasks
        # TODO: Task 04 will refactor TaskSelector to use scope_ulid directly
        # For now, pass scope_ulid as track_id (works for any ULID type)
        limit = max_tasks or 20
        tasks = selector.get_all_executable(
            track_id=scope_ulid,
            limit=limit,
        )

        if not tasks:
            console.print("[yellow]No executable tasks found.[/yellow]")
            console.print()
            console.print("[dim]Possible reasons:[/dim]")
            console.print("  - All tasks are completed")
            console.print("  - Tasks have incomplete dependencies")
            console.print("  - Tasks are not yet planned (missing context files)")
            console.print("  - Scope doesn't match any tasks")
            return 0

        # Display tasks table
        table = Table(
            title=f"Executable Tasks ({len(tasks)} found)",
            show_header=True,
            header_style="bold",
        )
        table.add_column("#", style="dim", width=3)
        table.add_column("Task ID", style="cyan", max_width=28)
        table.add_column("Name", style="green")
        table.add_column("Status", style="dim")

        for i, task in enumerate(tasks, 1):
            task_id = task.id
            if len(task_id) > 26:
                task_id = task_id[:23] + "..."

            table.add_row(
                str(i),
                task_id,
                task.name or "[unnamed]",
                task.status.value if hasattr(task, "status") else "not_started",
            )

        console.print(table)

        # Summary
        console.print()
        # TODO: Task 04 will refactor to use scope_ulid directly
        remaining = selector.count_remaining(track_id=scope_ulid)
        console.print(f"[dim]Total executable tasks: {remaining}[/dim]")

        if max_tasks and len(tasks) >= max_tasks:
            console.print(f"[dim](showing first {max_tasks} due to --max-tasks)[/dim]")

        console.print()
        console.print("[dim]Run without --dry-run to execute these tasks[/dim]")

        return 0

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        return 1

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        return 1


def _run_background(
    scope_ulid: Optional[str],
    all_tickets: bool,
    max_tasks: Optional[int],
    max_tokens: Optional[int],
) -> int:
    """
    Run implementation mode as a background process.

    Args:
        scope_ulid: Scope ticket ULID
        all_tickets: Execute all tickets
        max_tasks: Maximum tasks
        max_tokens: Maximum tokens

    Returns:
        Exit code (0 if process started successfully)
    """
    # Build command
    cmd = [sys.executable, "-m", "vibey", "implement"]

    if all_tickets:
        cmd.extend(["--all-tickets", "--yes"])  # Skip confirmation in background
    elif scope_ulid:
        cmd.extend(["--ticket", scope_ulid])
    if max_tasks:
        cmd.extend(["--max-tasks", str(max_tasks)])
    if max_tokens:
        cmd.extend(["--max-tokens", str(max_tokens)])

    # Log file for background output
    log_dir = Path.cwd() / ".vibey" / "implementation" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"implement_{timestamp}.log"

    console.print(
        Panel(
            "[bold cyan]Implementation Mode - Background[/bold cyan]\n"
            f"Log file: {log_file}",
            border_style="blue",
        )
    )

    try:
        # Open log file
        with open(log_file, "w") as log:
            # Start detached process
            if sys.platform == "win32":
                # Windows: use DETACHED_PROCESS flag
                process = subprocess.Popen(
                    cmd,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    creationflags=subprocess.DETACHED_PROCESS
                    | subprocess.CREATE_NEW_PROCESS_GROUP,
                )
            else:
                # Unix: use nohup-like behavior with start_new_session
                process = subprocess.Popen(
                    cmd,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                    preexec_fn=os.setpgrp if hasattr(os, "setpgrp") else None,
                )

        console.print(f"\n[green]Started background process (PID: {process.pid})[/green]")
        console.print()
        console.print("[dim]Monitor progress with:[/dim]")
        console.print(f"  tail -f {log_file}")
        console.print()
        console.print("[dim]Check status with:[/dim]")
        console.print("  vibey implement status")

        # Save PID for status tracking
        write_pid(process.pid)

        return 0

    except Exception as e:
        console.print(f"[red]Error starting background process:[/red] {e}")
        return 1


# =============================================================================
# STATUS COMMAND
# =============================================================================


@implement.command("status")
@click.pass_context
def implement_status(ctx):
    """
    Show current implementation mode status.

    Displays:
    - Session ID and start time
    - Current task being executed
    - Progress (X/Y tasks completed)
    - Token usage
    - Status (running/paused/stopped/completed)

    Examples:
      vibey implement status
    """
    state = load_state()

    if state is None:
        console.print(
            Panel(
                "[dim]No active implementation session found.[/dim]\n\n"
                "Start a new session with: [bold]vibey implement start[/bold]",
                title="Implementation Mode Status",
                border_style="dim",
            )
        )
        sys.exit(0)

    # Check if the process is actually running
    pid = read_pid()
    process_running = pid is not None and is_process_running(pid)

    # Create display and show status
    display = ProgressDisplay(state, console=console)
    display.show_status()

    # Add process status information
    console.print()
    if process_running:
        console.print(f"[green]Process running[/green] (PID: {pid})")
    else:
        if state.status == LoopStatus.RUNNING:
            console.print(
                "[yellow]Warning:[/yellow] State shows running but no process found.\n"
                "The process may have crashed. Use [bold]vibey implement resume[/bold] to continue."
            )
        elif state.status == LoopStatus.PAUSED:
            console.print("[yellow]Session is paused.[/yellow] Use [bold]vibey implement resume[/bold] to continue.")
        elif state.status == LoopStatus.STOPPED:
            console.print("[red]Session was stopped.[/red]")
        elif state.status == LoopStatus.COMPLETED:
            console.print("[green]Session completed successfully.[/green]")

    # Show task results if any
    if state.task_results:
        display.show_task_results_table(limit=5)

    sys.exit(0)


# =============================================================================
# PAUSE COMMAND
# =============================================================================


@implement.command("pause")
@click.pass_context
def implement_pause(ctx):
    """
    Pause execution after current task completes.

    Sets the status to PAUSED. The loop will stop after the current task
    finishes and can be resumed later with 'vibey implement resume'.

    The pause signal is written to a control file that the main loop checks
    periodically.

    Examples:
      vibey implement pause
    """
    state = load_state()
    pid = read_pid()

    if state is None:
        console.print("[yellow]No active implementation session found.[/yellow]")
        sys.exit(1)

    if state.status == LoopStatus.PAUSED:
        console.print("[yellow]Session is already paused.[/yellow]")
        sys.exit(0)

    if state.status in (LoopStatus.STOPPED, LoopStatus.COMPLETED):
        console.print(f"[yellow]Session is already {state.status.value}. Cannot pause.[/yellow]")
        sys.exit(1)

    # Check if process is running
    process_running = pid is not None and is_process_running(pid)

    if process_running:
        # Write pause signal to control file
        write_control(CONTROL_PAUSE)
        console.print(
            "[cyan]Pause signal sent.[/cyan]\n"
            "Execution will pause after the current task completes."
        )
    else:
        # Process not running, update state directly
        state.pause()
        save_state(state)
        console.print(
            "[cyan]Session marked as paused.[/cyan]\n"
            "Use [bold]vibey implement resume[/bold] to continue."
        )

    sys.exit(0)


# =============================================================================
# RESUME COMMAND
# =============================================================================


@implement.command("resume")
@click.pass_context
def implement_resume(ctx):
    """
    Resume paused execution.

    Loads the state from the state file and continues execution from where
    it left off. This command will start the implementation loop.

    Note: This command does not start a new process. Use 'vibey implement start'
    to start a new implementation session.

    Examples:
      vibey implement resume
    """
    state = load_state()
    pid = read_pid()

    if state is None:
        console.print(
            "[yellow]No implementation session found to resume.[/yellow]\n"
            "Start a new session with: [bold]vibey implement start[/bold]"
        )
        sys.exit(1)

    # Check if already running
    if pid is not None and is_process_running(pid):
        console.print(
            f"[yellow]Implementation loop is already running (PID: {pid}).[/yellow]\n"
            "Use [bold]vibey implement status[/bold] to check progress."
        )
        sys.exit(1)

    if state.status == LoopStatus.COMPLETED:
        console.print(
            "[yellow]Session has completed.[/yellow]\n"
            "Start a new session with: [bold]vibey implement start[/bold]"
        )
        sys.exit(1)

    if state.status == LoopStatus.STOPPED:
        # Allow resuming stopped sessions
        console.print(
            "[cyan]Resuming stopped session...[/cyan]\n"
            f"Session ID: {state.session_id}"
        )
    elif state.status == LoopStatus.PAUSED:
        console.print(
            "[cyan]Resuming paused session...[/cyan]\n"
            f"Session ID: {state.session_id}"
        )
    elif state.status == LoopStatus.RUNNING:
        # Session shows running but no process - likely crashed
        console.print(
            "[cyan]Resuming session (process not found)...[/cyan]\n"
            f"Session ID: {state.session_id}"
        )

    # Clear any stale control signals
    clear_control()

    # Update state to running
    state.status = LoopStatus.RUNNING
    save_state(state)

    # Write resume signal (in case main loop is checking)
    write_control(CONTROL_RESUME)

    console.print(
        "\n[green]Session ready to resume.[/green]\n\n"
        "To start the implementation loop, run:\n"
        "  [bold]vibey implement start --resume[/bold]\n\n"
        "Or restart your AI assistant in implementation mode."
    )

    sys.exit(0)


# =============================================================================
# STOP COMMAND
# =============================================================================


@implement.command("stop")
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force stop without waiting for current task",
)
@click.pass_context
def implement_stop(ctx, force: bool):
    """
    Stop execution immediately.

    Sends SIGINT to the running agent subprocess. The current task will be
    marked as blocked, and state is saved for potential resume.

    Use --force to send SIGKILL instead of SIGINT.

    Examples:
      vibey implement stop           # Graceful stop (SIGINT)
      vibey implement stop --force   # Force stop (SIGKILL)
    """
    state = load_state()
    pid = read_pid()

    if state is None and pid is None:
        console.print("[yellow]No active implementation session found.[/yellow]")
        sys.exit(1)

    # Check if process is running
    process_running = pid is not None and is_process_running(pid)

    if process_running:
        try:
            # Send appropriate signal
            if force:
                console.print(f"[red]Sending SIGKILL to process {pid}...[/red]")
                os.kill(pid, signal.SIGKILL)
            else:
                console.print(f"[yellow]Sending SIGINT to process {pid}...[/yellow]")
                os.kill(pid, signal.SIGINT)

            # Write stop signal to control file
            write_control(CONTROL_STOP)

            console.print(
                "[cyan]Stop signal sent.[/cyan]\n"
                "The process should terminate shortly."
            )

            # Clean up PID file after a forced kill
            if force:
                remove_pid()

        except OSError as e:
            console.print(f"[red]Failed to send signal: {e}[/red]")
            sys.exit(1)
    else:
        console.print("[dim]No running process found.[/dim]")

    # Update state if available
    if state is not None:
        # Mark current task as blocked if there is one
        if state.current_task:
            console.print(f"[yellow]Current task {state.current_task} marked as blocked.[/yellow]")
            state.skip_blocked_task(state.current_task)
            state.current_task = None

        state.stop()
        save_state(state)
        console.print(
            "\n[cyan]Session stopped.[/cyan]\n"
            f"Session ID: {state.session_id}\n"
            f"Tasks completed: {state.tasks_completed}\n"
            f"Tasks failed: {state.tasks_failed}\n"
            f"Tasks blocked: {state.tasks_blocked}"
        )

    # Clean up
    clear_control()
    if not process_running:
        remove_pid()

    sys.exit(0)


# =============================================================================
# REGRESSIONS COMMAND
# =============================================================================


@implement.command("regressions")
@click.option(
    "--task",
    "-t",
    "task_id",
    help="Show regressions for a specific task (ULID)",
)
@click.option(
    "--limit",
    "-n",
    type=int,
    default=10,
    help="Maximum number of reports to show",
)
@click.pass_context
def implement_regressions(ctx, task_id: Optional[str], limit: int):
    """
    View regression reports from implementation mode.

    Shows detected regressions from task execution, including:
    - Blocking regressions (unacknowledged)
    - Acknowledged regressions
    - New failures

    Examples:
      vibey implement regressions                     # Show recent reports
      vibey implement regressions --task 01KC...      # Show specific task
      vibey implement regressions --limit 5           # Limit to 5 reports
    """
    from vibey.services.implementation import RegressionDetector, RegressionConfig

    # Create detector
    project_root = Path.cwd()
    reports_dir = project_root / ".vibey" / "implementation" / "regressions"

    detector = RegressionDetector(
        config=RegressionConfig(),
        reports_dir=reports_dir,
    )

    if task_id:
        # Show specific task report
        report = detector.load_report(task_id)
        if not report:
            console.print(f"[yellow]No regression report found for task {task_id}[/yellow]")
            sys.exit(1)

        console.print(detector.generate_report(report))
    else:
        # Show recent reports
        reports = detector.list_reports(limit=limit)

        if not reports:
            console.print("[dim]No regression reports found.[/dim]")
            console.print(
                "\nRegression reports are created when implementation mode detects "
                "that a task caused previously-passing criteria to fail."
            )
            sys.exit(0)

        # Summary table
        table = Table(
            title=f"Regression Reports ({len(reports)} found)",
            show_header=True,
            header_style="bold",
        )
        table.add_column("Task ID", style="cyan", max_width=28)
        table.add_column("Date", style="dim")
        table.add_column("Regressions", style="red")
        table.add_column("Blocking", style="yellow")
        table.add_column("Status")

        for report in reports:
            task_display = report.task_id
            if len(task_display) > 26:
                task_display = task_display[:23] + "..."

            date_str = report.evaluated_at.strftime("%Y-%m-%d %H:%M")

            status = "[green]OK[/green]"
            if report.has_unacknowledged_regressions:
                status = "[red]BLOCKED[/red]"
            elif report.regression_count > 0:
                status = "[yellow]ACKNOWLEDGED[/yellow]"

            table.add_row(
                task_display,
                date_str,
                str(report.regression_count),
                str(report.blocking_count),
                status,
            )

        console.print(table)
        console.print()
        console.print(
            "[dim]Use --task <ULID> to see detailed report for a specific task[/dim]"
        )

    sys.exit(0)


# =============================================================================
# ACKNOWLEDGE COMMAND
# =============================================================================


@implement.command("acknowledge")
@click.argument("task_id")
@click.option(
    "--criterion",
    "-c",
    "criterion_ref",
    help="Acknowledge a specific criterion (default: all)",
)
@click.option(
    "--reason",
    "-r",
    default="Acknowledged by user",
    help="Reason for acknowledgment",
)
@click.pass_context
def implement_acknowledge(
    ctx,
    task_id: str,
    criterion_ref: Optional[str],
    reason: str,
):
    """
    Acknowledge regression(s) for a task.

    Acknowledging a regression marks it as acceptable and allows
    task execution to proceed without blocking.

    Arguments:
      TASK_ID: The task ULID with regressions to acknowledge

    Examples:
      vibey implement acknowledge 01KC...                        # Acknowledge all
      vibey implement acknowledge 01KC... --criterion test-xyz   # Acknowledge one
      vibey implement acknowledge 01KC... -r "Expected change"   # With reason
    """
    from vibey.services.implementation import RegressionDetector, RegressionConfig

    # Create detector
    project_root = Path.cwd()
    reports_dir = project_root / ".vibey" / "implementation" / "regressions"

    detector = RegressionDetector(
        config=RegressionConfig(),
        reports_dir=reports_dir,
    )

    # Load report
    report = detector.load_report(task_id)
    if not report:
        console.print(f"[red]Error:[/red] No regression report found for task {task_id}")
        sys.exit(1)

    if not report.has_unacknowledged_regressions:
        console.print(f"[yellow]No unacknowledged regressions for task {task_id}[/yellow]")
        sys.exit(0)

    # Acknowledge
    if detector.acknowledge_regression(task_id, criterion_ref, reason):
        if criterion_ref:
            console.print(
                f"[green]Acknowledged regression:[/green] {criterion_ref}\n"
                f"Reason: {reason}"
            )
        else:
            console.print(
                f"[green]Acknowledged all regressions for task {task_id}[/green]\n"
                f"Reason: {reason}"
            )

        # Show updated status
        updated_report = detector.load_report(task_id)
        if updated_report:
            if updated_report.has_unacknowledged_regressions:
                console.print(
                    f"\n[yellow]Remaining unacknowledged: {updated_report.blocking_count}[/yellow]"
                )
            else:
                console.print("\n[green]All regressions acknowledged. Task may proceed.[/green]")
    else:
        console.print("[red]Error:[/red] Failed to acknowledge regression")
        sys.exit(1)

    sys.exit(0)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "implement",
    "run_implementation_cmd",
    "implement_status",
    "implement_pause",
    "implement_resume",
    "implement_stop",
    "implement_regressions",
    "implement_acknowledge",
]
