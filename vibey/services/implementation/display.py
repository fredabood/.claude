"""
Real-time Progress Display for Implementation Mode.

This module provides rich terminal output for tracking autonomous task execution,
including status displays, task notifications, and execution summaries.

Usage:
    from vibey.services.implementation.display import ProgressDisplay
    from vibey.services.implementation.state import LoopState
    from rich.console import Console

    # Create display with state
    state = LoopState()
    display = ProgressDisplay(state)

    # Show current status
    display.show_status()

    # Notify task events
    display.show_task_start(task)
    display.show_task_complete(task, result)

    # Show final summary
    display.show_summary(state)

Design Reference:
- Implementation Mode Track Sprint 1
- Task N7: Implement real-time progress display
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket
from vibey.services.implementation.result import ExecutionResult, ExecutionStatus
from vibey.services.implementation.state import LoopState, LoopStatus


# =============================================================================
# COLOR SCHEME
# =============================================================================

# Status colors
COLOR_SUCCESS = "green"
COLOR_FAILURE = "red"
COLOR_WARNING = "yellow"
COLOR_INFO = "cyan"
COLOR_MUTED = "dim"

# Status-specific colors
STATUS_COLORS = {
    LoopStatus.RUNNING: "green",
    LoopStatus.PAUSED: "yellow",
    LoopStatus.STOPPED: "red",
    LoopStatus.COMPLETED: "cyan",
}

EXECUTION_STATUS_COLORS = {
    ExecutionStatus.SUCCESS: "green",
    ExecutionStatus.FAILURE: "red",
    ExecutionStatus.BLOCKED: "yellow",
    ExecutionStatus.TIMEOUT: "red",
    ExecutionStatus.CANCELLED: "dim",
}


# =============================================================================
# PROGRESS DISPLAY CLASS
# =============================================================================


class ProgressDisplay:
    """
    Real-time progress display for Implementation Mode.

    Provides rich terminal output for tracking autonomous task execution,
    including status panels, task notifications, and execution summaries.

    Attributes:
        state: The LoopState instance to display
        console: Rich Console for output (created if not provided)
        total_tasks: Optional total task count for progress calculation

    Example:
        >>> state = LoopState()
        >>> display = ProgressDisplay(state)
        >>> display.show_status()
        Implementation Mode: Running
        ...
    """

    def __init__(
        self,
        state: LoopState,
        console: Optional[Console] = None,
        total_tasks: Optional[int] = None,
    ):
        """
        Initialize the progress display.

        Args:
            state: The LoopState instance to track and display
            console: Optional Rich Console (created if not provided)
            total_tasks: Optional total number of tasks for progress calculation
        """
        self.state = state
        self.console = console or Console()
        self.total_tasks = total_tasks

    # =========================================================================
    # STATUS DISPLAY
    # =========================================================================

    def show_status(self, current_task_name: Optional[str] = None) -> None:
        """
        Display current execution status.

        Shows a formatted panel with:
        - Current status (Running, Paused, etc.)
        - Current task being executed
        - Progress (completed/total tasks)
        - Token usage
        - Duration and time estimates

        Args:
            current_task_name: Optional human-readable name of current task

        Example output:
            Implementation Mode: Running
            ----------------------------------------
            Current Task: Implement user authentication
            Progress: 5/12 tasks (41.7%)

            Tokens: 15,234 input / 8,456 output
            Duration: 00:23:45
            Remaining: ~00:32:00 (estimated)
            ----------------------------------------
        """
        # Build status line
        status_color = STATUS_COLORS.get(self.state.status, "white")
        status_text = Text()
        status_text.append("Implementation Mode: ", style="bold")
        status_text.append(
            self.state.status.value.capitalize(),
            style=f"bold {status_color}"
        )

        # Build content lines
        lines = []

        # Current task
        if current_task_name:
            lines.append(f"Current Task: {current_task_name}")
        elif self.state.current_task:
            lines.append(f"Current Task: {self.state.current_task}")
        else:
            lines.append("Current Task: [dim]None[/dim]")

        # Progress
        progress_line = self._format_progress()
        lines.append(progress_line)

        # Blank line separator
        lines.append("")

        # Token usage
        token_line = self._format_tokens()
        lines.append(token_line)

        # Duration
        duration_line = self._format_duration()
        lines.append(duration_line)

        # Remaining time estimate
        remaining = self.estimate_remaining()
        if remaining is not None:
            remaining_str = self._format_timedelta(remaining)
            lines.append(f"Remaining: ~{remaining_str} [dim](estimated)[/dim]")

        # Build panel content
        content = "\n".join(lines)

        # Create and display panel
        panel = Panel(
            content,
            title=status_text,
            border_style=status_color,
            padding=(0, 1),
        )
        self.console.print(panel)

    def _format_progress(self) -> str:
        """Format progress line with percentage."""
        completed = self.state.tasks_completed
        attempted = self.state.tasks_attempted
        total = self.total_tasks

        if total is not None and total > 0:
            percentage = (completed / total) * 100
            return f"Progress: {completed}/{total} tasks ({percentage:.1f}%)"
        elif attempted > 0:
            return f"Progress: {completed} completed / {attempted} attempted"
        else:
            return "Progress: No tasks started"

    def _format_tokens(self) -> str:
        """Format token usage line."""
        input_tokens = self.state.tokens_input
        output_tokens = self.state.tokens_output

        # Format with thousands separators
        input_formatted = f"{input_tokens:,}"
        output_formatted = f"{output_tokens:,}"

        return f"Tokens: {input_formatted} input / {output_formatted} output"

    def _format_duration(self) -> str:
        """Format duration line."""
        elapsed = self.state.elapsed_seconds
        elapsed_td = timedelta(seconds=elapsed)
        elapsed_str = self._format_timedelta(elapsed_td)
        return f"Duration: {elapsed_str}"

    def _format_timedelta(self, td: timedelta) -> str:
        """Format timedelta as HH:MM:SS."""
        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    # =========================================================================
    # TASK NOTIFICATIONS
    # =========================================================================

    def show_task_start(self, task: HierarchicalTicket) -> None:
        """
        Display task starting notification.

        Shows a brief notification when a task begins execution.

        Args:
            task: The HierarchicalTicket that is starting

        Example output:
            [>] Starting: Implement user authentication
                Task ID: 01KCZF73PX9YNKWXKYVARY89N3
        """
        # Task name
        task_name = task.name or task.id

        # Build output
        prefix = Text("[>]", style=f"bold {COLOR_INFO}")
        self.console.print()  # Blank line before
        self.console.print(prefix, f"Starting: [bold]{task_name}[/bold]")
        self.console.print(f"    Task ID: [dim]{task.id}[/dim]")

    def show_task_complete(
        self,
        task: HierarchicalTicket,
        result: ExecutionResult,
    ) -> None:
        """
        Display task completion with result.

        Shows task completion status with details on success or failure.

        Args:
            task: The HierarchicalTicket that completed
            result: The ExecutionResult with outcome details

        Example output (success):
            [+] Completed: Implement user authentication
                Duration: 00:05:23 | Tokens: 1,500 in / 500 out
                Files: 2 modified, 1 created | Commits: 1

        Example output (failure):
            [!] Failed: Implement user authentication
                Duration: 00:02:15 | Tokens: 800 in / 200 out
                Error: Test assertions failed
        """
        # Determine status and styling
        if result.succeeded:
            prefix = Text("[+]", style=f"bold {COLOR_SUCCESS}")
            status_word = "Completed"
            status_style = COLOR_SUCCESS
        else:
            prefix = Text("[!]", style=f"bold {COLOR_FAILURE}")
            status_word = "Failed"
            status_style = COLOR_FAILURE

        # Task name
        task_name = task.name or task.id

        # Build output
        self.console.print()  # Blank line before
        self.console.print(
            prefix,
            f"{status_word}: [bold {status_style}]{task_name}[/bold {status_style}]"
        )

        # Duration and tokens
        duration_str = self._format_timedelta(result.duration)
        tokens_in = f"{result.tokens_input:,}"
        tokens_out = f"{result.tokens_output:,}"
        self.console.print(
            f"    Duration: {duration_str} | Tokens: {tokens_in} in / {tokens_out} out"
        )

        # Files and commits (for success)
        if result.succeeded:
            files_modified = len(result.files_modified)
            files_created = len(result.files_created)
            commits = len(result.commits)

            if files_modified or files_created or commits:
                parts = []
                if files_modified:
                    parts.append(f"{files_modified} modified")
                if files_created:
                    parts.append(f"{files_created} created")
                files_str = ", ".join(parts) if parts else "0 files"

                self.console.print(
                    f"    Files: {files_str} | Commits: {commits}"
                )

        # Error message (for failure)
        if not result.succeeded and result.error_message:
            error_msg = result.error_message
            # Truncate long error messages
            if len(error_msg) > 80:
                error_msg = error_msg[:77] + "..."
            self.console.print(
                f"    Error: [{COLOR_FAILURE}]{error_msg}[/{COLOR_FAILURE}]"
            )

    # =========================================================================
    # SUMMARY DISPLAY
    # =========================================================================

    def show_summary(self, state: Optional[LoopState] = None) -> None:
        """
        Display final execution summary.

        Shows a comprehensive summary of the execution session including:
        - Session ID and status
        - Task statistics (completed, failed, blocked)
        - Token usage totals
        - Total duration
        - Success rate

        Args:
            state: Optional LoopState to summarize (uses self.state if not provided)

        Example output:
            Execution Summary
            ----------------------------------------
            Session: 01KCZF73PX9YNKWXKYVARY89N3
            Status: Completed

            Tasks:
              Completed:  8  [green bar]
              Failed:     2  [red bar]
              Blocked:    1  [yellow bar]
              ----------------------
              Total:     11

            Success Rate: 72.7%

            Tokens:
              Input:    45,234
              Output:   23,456
              Total:    68,690

            Duration: 01:23:45
            ----------------------------------------
        """
        if state is None:
            state = self.state

        # Determine summary color based on outcome
        if state.status == LoopStatus.COMPLETED and state.tasks_failed == 0:
            border_color = COLOR_SUCCESS
        elif state.tasks_failed > 0:
            border_color = COLOR_WARNING
        else:
            border_color = COLOR_INFO

        # Build content
        lines = []

        # Session info
        lines.append(f"Session: [dim]{state.session_id}[/dim]")
        status_color = STATUS_COLORS.get(state.status, "white")
        lines.append(f"Status: [{status_color}]{state.status.value.capitalize()}[/{status_color}]")
        lines.append("")

        # Task statistics
        lines.append("[bold]Tasks:[/bold]")
        lines.append(f"  Completed:  [{COLOR_SUCCESS}]{state.tasks_completed:>3}[/{COLOR_SUCCESS}]")
        lines.append(f"  Failed:     [{COLOR_FAILURE}]{state.tasks_failed:>3}[/{COLOR_FAILURE}]")
        lines.append(f"  Blocked:    [{COLOR_WARNING}]{state.tasks_blocked:>3}[/{COLOR_WARNING}]")
        lines.append("  " + "-" * 18)
        lines.append(f"  Total:      {state.tasks_attempted:>3}")
        lines.append("")

        # Success rate
        if state.success_rate is not None:
            rate_pct = state.success_rate * 100
            rate_color = COLOR_SUCCESS if rate_pct >= 80 else (
                COLOR_WARNING if rate_pct >= 50 else COLOR_FAILURE
            )
            lines.append(f"Success Rate: [{rate_color}]{rate_pct:.1f}%[/{rate_color}]")
            lines.append("")

        # Token usage
        lines.append("[bold]Tokens:[/bold]")
        lines.append(f"  Input:   {state.tokens_input:>10,}")
        lines.append(f"  Output:  {state.tokens_output:>10,}")
        lines.append("  " + "-" * 18)
        lines.append(f"  Total:   {state.total_tokens:>10,}")
        lines.append("")

        # Duration
        elapsed_td = timedelta(seconds=state.elapsed_seconds)
        elapsed_str = self._format_timedelta(elapsed_td)
        lines.append(f"Duration: {elapsed_str}")

        # Build panel content
        content = "\n".join(lines)

        # Create and display panel
        panel = Panel(
            content,
            title="[bold]Execution Summary[/bold]",
            border_style=border_color,
            padding=(0, 1),
        )
        self.console.print()  # Blank line before
        self.console.print(panel)

    # =========================================================================
    # TASK RESULT TABLE
    # =========================================================================

    def show_task_results_table(self, limit: Optional[int] = None) -> None:
        """
        Display a table of task execution results.

        Shows a formatted table with task IDs, status, duration, and tokens.

        Args:
            limit: Optional maximum number of results to show

        Example output:
            Task Results
            +--------------------------+---------+----------+--------+
            | Task ID                  | Status  | Duration | Tokens |
            +--------------------------+---------+----------+--------+
            | 01KCZF73PX9YNKWXKYVARY...| Success | 00:05:23 |  2,000 |
            | 01KCZF73PXYNKWXKYVARY8...| Failed  | 00:02:15 |  1,000 |
            +--------------------------+---------+----------+--------+
        """
        results = self.state.task_results
        if limit is not None:
            results = results[-limit:]  # Show most recent

        if not results:
            self.console.print("[dim]No task results to display.[/dim]")
            return

        # Build table
        table = Table(title="Task Results", show_header=True, header_style="bold")
        table.add_column("Task ID", style="dim", no_wrap=True, max_width=26)
        table.add_column("Status", justify="center")
        table.add_column("Duration", justify="right")
        table.add_column("Tokens", justify="right")

        for result in results:
            # Truncate task ID
            task_id = result.task_id
            if len(task_id) > 26:
                task_id = task_id[:23] + "..."

            # Status with color
            if result.success:
                status = Text("Success", style=COLOR_SUCCESS)
            else:
                status = Text("Failed", style=COLOR_FAILURE)

            # Duration
            if result.duration_seconds is not None:
                duration_td = timedelta(seconds=result.duration_seconds)
                duration = self._format_timedelta(duration_td)
            else:
                duration = "-"

            # Tokens
            tokens = f"{result.total_tokens:,}"

            table.add_row(task_id, status, duration, tokens)

        self.console.print()
        self.console.print(table)

    # =========================================================================
    # TIME ESTIMATION
    # =========================================================================

    def estimate_remaining(self) -> Optional[timedelta]:
        """
        Estimate time remaining based on average task duration.

        Calculates the average duration of completed tasks and multiplies
        by the number of remaining tasks.

        Returns:
            Estimated time remaining as timedelta, or None if cannot estimate.

        Notes:
            - Returns None if no tasks completed or total_tasks not set
            - Uses average of all completed task durations
            - Estimate becomes more accurate as more tasks complete
        """
        # Need completed tasks to estimate
        if self.state.tasks_completed == 0:
            return None

        # Need total tasks to calculate remaining
        if self.total_tasks is None or self.total_tasks <= 0:
            return None

        # Calculate remaining tasks
        remaining_count = self.total_tasks - self.state.tasks_completed
        if remaining_count <= 0:
            return timedelta(seconds=0)

        # Calculate average duration from completed tasks
        completed_results = [
            r for r in self.state.task_results
            if r.success and r.duration_seconds is not None
        ]

        if not completed_results:
            # Fallback: use total elapsed time / completed count
            avg_seconds = self.state.elapsed_seconds / self.state.tasks_completed
        else:
            total_duration = sum(r.duration_seconds for r in completed_results)
            avg_seconds = total_duration / len(completed_results)

        # Estimate remaining time
        estimated_seconds = avg_seconds * remaining_count

        return timedelta(seconds=estimated_seconds)

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def print_separator(self) -> None:
        """Print a horizontal separator line."""
        self.console.print("-" * 40, style=COLOR_MUTED)

    def print_blank(self) -> None:
        """Print a blank line."""
        self.console.print()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "ProgressDisplay",
]
