"""
Human Approval Gates for Implementation Mode.

This module provides approval gates that require human confirmation before
executing certain high-risk or complex tasks. It supports:
- Automatic detection of tasks requiring approval
- Rich terminal display for approval prompts
- Async timeout handling for unattended approval requests
- Notification stubs for future webhook/email integration

Usage:
    from vibey.services.implementation.approval import ApprovalGate, ApprovalResult
    from vibey.services.implementation.config import ImplementConfig

    config = ImplementConfig()
    gate = ApprovalGate(config)

    if gate.requires_approval(task):
        result = await gate.request_approval(task)
        if result == ApprovalResult.APPROVED:
            # Proceed with task execution
            pass
        elif result == ApprovalResult.SKIPPED:
            # Skip this task
            pass
        elif result == ApprovalResult.QUIT:
            # Stop the implementation loop
            pass

Design Reference:
- Implementation Mode Track Sprint 1
- Task NF: Implement human approval gates
"""

import asyncio
import logging
import sys
from enum import Enum
from typing import List, Optional, Set

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from vibey.roadmap.models.ticket.enums import Complexity, Priority, TaskType
from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket
from vibey.services.implementation.config import ImplementConfig

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================


class ApprovalResult(Enum):
    """Result of an approval request."""

    APPROVED = "approved"
    SKIPPED = "skipped"
    QUIT = "quit"
    TIMEOUT = "timeout"


# =============================================================================
# CONSTANTS
# =============================================================================

# Complexity levels that require approval
APPROVAL_COMPLEXITIES: Set[Complexity] = {
    Complexity.HIGH,
    Complexity.CRITICAL,
}

# Priority levels that require approval
APPROVAL_PRIORITIES: Set[Priority] = {
    Priority.CRITICAL,
}

# Task types that require approval
APPROVAL_TASK_TYPES: Set[TaskType] = {
    TaskType.INFRASTRUCTURE,
}

# File patterns that require approval (case-insensitive)
APPROVAL_FILE_PATTERNS: Set[str] = {
    "migration",
    "migrations",
    "config",
    "configs",
    "configuration",
    ".env",
    "credentials",
    "secrets",
    "security",
}

# Default timeout for approval requests (in seconds)
DEFAULT_APPROVAL_TIMEOUT: int = 300  # 5 minutes

# Color scheme for approval prompts
COLOR_WARNING = "yellow"
COLOR_INFO = "cyan"
COLOR_MUTED = "dim"
COLOR_PROMPT = "bold white"


# =============================================================================
# APPROVAL GATE CLASS
# =============================================================================


class ApprovalGate:
    """
    Human approval gate for high-risk task execution.

    The approval gate checks whether a task requires human confirmation
    before execution. Tasks requiring approval include:
    - Complex or very complex tasks
    - Critical priority tasks
    - Infrastructure or security tasks
    - Tasks affecting migrations or configuration files

    Attributes:
        config: ImplementConfig for timeout and other settings
        console: Rich Console for terminal output
        timeout: Approval timeout in seconds

    Example:
        >>> config = ImplementConfig()
        >>> gate = ApprovalGate(config)
        >>> if gate.requires_approval(task):
        ...     result = await gate.request_approval(task)
        ...     if result != ApprovalResult.APPROVED:
        ...         # Handle non-approval
        ...         pass
    """

    def __init__(
        self,
        config: ImplementConfig,
        console: Optional[Console] = None,
        timeout: Optional[int] = None,
    ):
        """
        Initialize the approval gate.

        Args:
            config: Implementation configuration
            console: Optional Rich Console (created if not provided)
            timeout: Approval timeout in seconds (default: 300)
        """
        self.config = config
        self.console = console or Console()
        self.timeout = timeout or DEFAULT_APPROVAL_TIMEOUT

    # =========================================================================
    # APPROVAL DETECTION
    # =========================================================================

    def requires_approval(self, task: HierarchicalTicket) -> bool:
        """
        Check if task requires human approval.

        Approval is required for tasks matching any of:
        - complexity: high, critical
        - priority: critical
        - task_type: infrastructure
        - Files: migrations, configs, security-related

        Args:
            task: The HierarchicalTicket to check

        Returns:
            True if approval is required, False otherwise
        """
        reasons = self._get_approval_reasons(task)
        return len(reasons) > 0

    def _get_approval_reasons(self, task: HierarchicalTicket) -> List[str]:
        """
        Get the reasons why a task requires approval.

        Args:
            task: The HierarchicalTicket to check

        Returns:
            List of approval reason strings (empty if no approval needed)
        """
        reasons: List[str] = []

        # Check complexity
        complexity = self._get_task_complexity(task)
        if complexity and complexity in APPROVAL_COMPLEXITIES:
            reasons.append(f"Complexity: {complexity.value}")

        # Check priority
        priority = task.priority
        if priority in APPROVAL_PRIORITIES:
            reasons.append(f"Priority: {priority.value}")

        # Check task type
        task_type = self._get_task_type(task)
        if task_type and task_type in APPROVAL_TASK_TYPES:
            reasons.append(f"Task type: {task_type.value}")

        # Check file patterns
        sensitive_files = self._get_sensitive_files(task)
        if sensitive_files:
            file_list = ", ".join(sensitive_files[:3])
            if len(sensitive_files) > 3:
                file_list += f" (+{len(sensitive_files) - 3} more)"
            reasons.append(f"Sensitive files: {file_list}")

        return reasons

    def _get_task_complexity(self, task: HierarchicalTicket) -> Optional[Complexity]:
        """Get the complexity of a task if available."""
        # TaskTicket has complexity field directly
        if hasattr(task, "complexity"):
            return task.complexity
        return None

    def _get_task_type(self, task: HierarchicalTicket) -> Optional[TaskType]:
        """Get the task type if available."""
        # TaskTicket has task_type_detail field
        if hasattr(task, "task_type_detail"):
            return task.task_type_detail
        return None

    def _get_sensitive_files(self, task: HierarchicalTicket) -> List[str]:
        """
        Get list of sensitive files from task deliverables.

        Checks file paths against APPROVAL_FILE_PATTERNS.

        Args:
            task: The HierarchicalTicket to check

        Returns:
            List of sensitive file paths
        """
        sensitive: List[str] = []

        # Get file paths from deliverables
        for criterion in task.deliverables:
            target = criterion.target
            if hasattr(target, "file_path"):
                file_path = target.file_path.lower()
                for pattern in APPROVAL_FILE_PATTERNS:
                    if pattern in file_path:
                        sensitive.append(target.file_path)
                        break
            elif hasattr(target, "paths"):
                for path in target.paths:
                    path_lower = path.lower()
                    for pattern in APPROVAL_FILE_PATTERNS:
                        if pattern in path_lower:
                            sensitive.append(path)
                            break

        return sensitive

    # =========================================================================
    # APPROVAL REQUEST
    # =========================================================================

    async def request_approval(self, task: HierarchicalTicket) -> ApprovalResult:
        """
        Request human approval for task execution.

        Displays task details and waits for user input:
        - [A]pprove: Proceed with task execution
        - [S]kip: Skip this task and continue
        - [Q]uit: Stop the implementation loop

        Args:
            task: The HierarchicalTicket requiring approval

        Returns:
            ApprovalResult indicating the user's decision
        """
        # Display task details
        self._display_approval_prompt(task)

        # Wait for user input with timeout
        try:
            result = await asyncio.wait_for(
                self._get_user_input(),
                timeout=self.timeout,
            )
            return result
        except asyncio.TimeoutError:
            self.console.print(
                f"\n[{COLOR_WARNING}]Approval timed out after {self.timeout} seconds[/{COLOR_WARNING}]"
            )
            logger.warning(f"Approval timeout for task {task.id}")
            return ApprovalResult.TIMEOUT

    def _display_approval_prompt(self, task: HierarchicalTicket) -> None:
        """
        Display the approval prompt with task details.

        Args:
            task: The HierarchicalTicket requiring approval
        """
        # Build task details
        task_name = task.name or task.id
        reasons = self._get_approval_reasons(task)

        # Build content lines
        lines = []
        lines.append(f"[bold]{task_name}[/bold]")
        lines.append("")

        # Task ID
        lines.append(f"Task ID: [{COLOR_MUTED}]{task.id}[/{COLOR_MUTED}]")

        # Approval reasons
        lines.append("")
        lines.append(f"[{COLOR_WARNING}]Approval required for:[/{COLOR_WARNING}]")
        for reason in reasons:
            lines.append(f"  - {reason}")

        # Description if available
        if task.description:
            lines.append("")
            description = task.description
            if len(description) > 200:
                description = description[:197] + "..."
            lines.append(f"Description: {description}")

        # Build content
        content = "\n".join(lines)

        # Create panel
        panel = Panel(
            content,
            title="[bold yellow]Task Requires Approval[/bold yellow]",
            border_style=COLOR_WARNING,
            padding=(1, 2),
        )

        # Display
        self.console.print()
        self.console.print(panel)
        self.console.print()

    async def _get_user_input(self) -> ApprovalResult:
        """
        Get user input for approval decision.

        Reads from stdin asynchronously to support timeout.

        Returns:
            ApprovalResult based on user input
        """
        # Display prompt
        prompt = Text()
        prompt.append("[", style=COLOR_MUTED)
        prompt.append("A", style="bold green")
        prompt.append("]pprove / [", style=COLOR_MUTED)
        prompt.append("S", style="bold yellow")
        prompt.append("]kip / [", style=COLOR_MUTED)
        prompt.append("Q", style="bold red")
        prompt.append("]uit? ", style=COLOR_MUTED)

        self.console.print(prompt, end="")

        # Read input asynchronously
        loop = asyncio.get_event_loop()
        user_input = await loop.run_in_executor(None, self._read_input)

        # Parse response
        response = user_input.strip().lower()

        if response in ("a", "approve", "y", "yes"):
            self.console.print(f"[green]Approved[/green]")
            logger.info("Task approved by user")
            return ApprovalResult.APPROVED

        elif response in ("s", "skip", "n", "no"):
            self.console.print(f"[yellow]Skipped[/yellow]")
            logger.info("Task skipped by user")
            return ApprovalResult.SKIPPED

        elif response in ("q", "quit", "exit", "stop"):
            self.console.print(f"[red]Quitting[/red]")
            logger.info("Implementation loop quit by user")
            return ApprovalResult.QUIT

        else:
            # Default to skip for unrecognized input
            self.console.print(
                f"[{COLOR_WARNING}]Unrecognized input '{response}', treating as skip[/{COLOR_WARNING}]"
            )
            return ApprovalResult.SKIPPED

    def _read_input(self) -> str:
        """
        Read a line of input from stdin.

        This is called in an executor to allow async timeout.

        Returns:
            The input string from the user
        """
        try:
            return sys.stdin.readline()
        except EOFError:
            return ""
        except KeyboardInterrupt:
            return "q"

    # =========================================================================
    # NOTIFICATIONS
    # =========================================================================

    def notify(self, task: HierarchicalTicket, channel: str) -> None:
        """
        Send notification for approval request.

        This is a stub for future notification implementations.
        Supported channels could include:
        - "console": Print to terminal (default behavior)
        - "webhook": Send to webhook URL
        - "email": Send email notification
        - "slack": Send Slack message

        Args:
            task: The HierarchicalTicket requiring approval
            channel: Notification channel identifier
        """
        # Stub implementation - just log the notification request
        task_name = task.name or task.id
        logger.info(f"Notification requested for task '{task_name}' on channel '{channel}'")

        if channel == "console":
            # Console notification is handled by display methods
            pass
        elif channel in ("webhook", "email", "slack"):
            # Future: implement actual notification
            logger.warning(
                f"Notification channel '{channel}' is not yet implemented"
            )
        else:
            logger.warning(f"Unknown notification channel: {channel}")


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "ApprovalGate",
    "ApprovalResult",
    "APPROVAL_COMPLEXITIES",
    "APPROVAL_PRIORITIES",
    "APPROVAL_TASK_TYPES",
    "APPROVAL_FILE_PATTERNS",
    "DEFAULT_APPROVAL_TIMEOUT",
]
