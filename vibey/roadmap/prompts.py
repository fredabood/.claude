"""
Smart prompting system for platform context management.

Provides user prompts when compatibility issues are detected,
allowing users to choose how to proceed without auto-recalculating.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

from vibey.roadmap.compatibility import (
    SprintCompatibility,
    CompatibilityStatus,
    check_sprint_compatibility,
    format_compatibility_result,
)
from vibey.platform import format_token_count


console = Console()


class PromptAction(str, Enum):
    """User action choices for compatibility prompts."""
    RECALCULATE = "recalculate"
    CONTINUE = "continue"
    INFO = "info"
    CANCEL = "cancel"


@dataclass
class PromptResult:
    """Result of a user prompt."""
    action: PromptAction
    should_proceed: bool
    message: str = ""


def show_compatibility_warning(result: SprintCompatibility) -> None:
    """
    Display a compatibility warning panel.

    Args:
        result: SprintCompatibility result to display.
    """
    # Build warning message
    lines = []
    lines.append(f"[bold yellow]⚠️  Sprint Compatibility Warning[/bold yellow]")
    lines.append("")
    lines.append(f"This sprint has tasks that may not fit in your platform's context window.")
    lines.append("")
    lines.append(f"[bold]Your platform:[/bold] {result.platform.display_name} ({format_token_count(result.platform.context_window)} context)")
    lines.append("")
    lines.append(f"[bold]Oversized incomplete tasks:[/bold] {result.oversized_tasks}/{result.incomplete_tasks} tasks")

    # Show problem tasks
    problem_tasks = [t for t in result.task_results
                     if t.compatibility == CompatibilityStatus.OVERSIZED]
    for task in problem_tasks[:3]:  # Show up to 3
        overflow = format_token_count(task.overflow_tokens)
        lines.append(f"  [red]• {task.task_id}:[/red] {format_token_count(task.estimated_tokens)} tokens (exceeds by {overflow})")

    if len(problem_tasks) > 3:
        lines.append(f"  ... and {len(problem_tasks) - 3} more")

    panel = Panel(
        "\n".join(lines),
        title="Compatibility Check",
        border_style="yellow",
    )
    console.print(panel)


def prompt_compatibility_action(result: SprintCompatibility) -> PromptResult:
    """
    Prompt user for action when compatibility issues detected.

    Always asks the user - never auto-recalculates.

    Args:
        result: SprintCompatibility with issues.

    Returns:
        PromptResult with user's choice.
    """
    show_compatibility_warning(result)

    console.print("")
    console.print("Would you like to recalculate this sprint for your platform?")
    console.print("This will split oversized tasks while preserving dependencies and success criteria.")
    console.print("")
    console.print("[bold]Options:[/bold]")
    console.print("  [green][Y][/green] Recalculate now - Split tasks to fit your context window")
    console.print("  [yellow][N][/yellow] Continue anyway - Proceed without changes (may cause issues)")
    console.print("  [blue][I][/blue] More info - Show detailed compatibility analysis")
    console.print("  [red][C][/red] Cancel - Abort this operation")
    console.print("")

    while True:
        choice = Prompt.ask(
            "Your choice",
            choices=["y", "n", "i", "c", "Y", "N", "I", "C"],
            default="y",
        ).lower()

        if choice == "y":
            return PromptResult(
                action=PromptAction.RECALCULATE,
                should_proceed=True,
                message="User chose to recalculate sprint",
            )
        elif choice == "n":
            console.print("")
            if Confirm.ask("[yellow]Are you sure you want to continue without recalculating?[/yellow]"):
                return PromptResult(
                    action=PromptAction.CONTINUE,
                    should_proceed=True,
                    message="User chose to continue without recalculation",
                )
            # If they say no to confirmation, show options again
            continue
        elif choice == "i":
            # Show detailed info
            console.print("")
            console.print(format_compatibility_result(result, verbose=True))
            console.print("")
            # Loop back to ask again
            continue
        elif choice == "c":
            return PromptResult(
                action=PromptAction.CANCEL,
                should_proceed=False,
                message="User cancelled operation",
            )


def check_and_prompt_compatibility(
    sprint_id: str,
    project_root: Optional[Path] = None,
    skip_prompt: bool = False,
    on_recalculate: Optional[Callable[[str], None]] = None,
) -> PromptResult:
    """
    Check sprint compatibility and prompt user if issues found.

    This is the main integration point for commands like `roadmap start`.

    Args:
        sprint_id: Sprint to check.
        project_root: Project root directory.
        skip_prompt: Skip prompting (for CI/non-interactive).
        on_recalculate: Callback if user chooses to recalculate.

    Returns:
        PromptResult indicating whether to proceed.
    """
    if project_root is None:
        project_root = Path.cwd()

    # Run compatibility check
    try:
        result = check_sprint_compatibility(sprint_id, project_root)
    except FileNotFoundError:
        # Sprint not found - let the caller handle it
        return PromptResult(
            action=PromptAction.CONTINUE,
            should_proceed=True,
            message="Sprint not found, skipping compatibility check",
        )

    # If compatible, proceed without prompting
    if result.can_proceed:
        return PromptResult(
            action=PromptAction.CONTINUE,
            should_proceed=True,
            message="Sprint is compatible with current platform",
        )

    # If skip_prompt, warn but continue
    if skip_prompt:
        console.print(f"[yellow]⚠️  Sprint has compatibility issues ({result.oversized_tasks} oversized tasks)[/yellow]")
        console.print("[dim]Skipping prompt (non-interactive mode)[/dim]")
        return PromptResult(
            action=PromptAction.CONTINUE,
            should_proceed=True,
            message="Compatibility issues detected but prompting skipped",
        )

    # Prompt user
    prompt_result = prompt_compatibility_action(result)

    # Handle recalculate action
    if prompt_result.action == PromptAction.RECALCULATE:
        if on_recalculate:
            on_recalculate(sprint_id)
        else:
            console.print("")
            console.print(f"[blue]Run:[/blue] vibey roadmap recalculate {sprint_id}")
            console.print("")

    return prompt_result


def show_compatibility_status_brief(
    sprint_id: str,
    project_root: Optional[Path] = None,
) -> None:
    """
    Show brief compatibility status (for `roadmap show` command).

    Args:
        sprint_id: Sprint to check.
        project_root: Project root directory.
    """
    if project_root is None:
        project_root = Path.cwd()

    try:
        result = check_sprint_compatibility(sprint_id, project_root)
    except FileNotFoundError:
        return  # Silent fail for show command

    if result.can_proceed:
        console.print(f"\n[green]✅ Compatible with {result.platform.display_name}[/green]")
    else:
        console.print(f"\n[yellow]⚠️  {result.oversized_tasks} task(s) may not fit in {result.platform.display_name} context[/yellow]")
        console.print(f"   Run: [blue]vibey roadmap check-compatibility {sprint_id}[/blue]")
