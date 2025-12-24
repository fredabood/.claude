"""
BugLogger - Automatic bug ticket creation for the implementation loop.

This module provides automatic bug detection and ticket creation during
autonomous task execution. When errors are detected in CLI output, a bug
ticket is created as a child of a designated parent bug ticket.

Key Features:
- BugSeverity enum for classifying bug severity
- BugReport dataclass for capturing bug details
- BugLogger class for automatic bug ticket creation
- CLI error detection and analysis
- Session bug tracking and summary generation

Usage:
    from vibey.services.implementation import (
        BugLogger,
        BugSeverity,
        BugReport,
    )
    from pathlib import Path

    # Initialize with parent bug ticket ID
    logger = BugLogger(
        bug_ticket_id="01KCZF73PX9YNKWXKYVARY89NV",
        roadmap_root=Path(".vibey/roadmap"),
    )

    # Log a bug manually
    bug_id = logger.log_bug(
        title="Import error in main module",
        description="ModuleNotFoundError when importing vibey.cli",
        context={"task_id": "01KCZF...", "command": "python -m vibey"},
        severity=BugSeverity.HIGH,
    )

    # Detect bugs from CLI output
    if logger.detect_cli_error(output, command):
        # Error was detected and logged
        pass

    # Get summary of bugs found in this session
    summary = logger.generate_bug_summary()

Design Reference:
- Implementation Mode Track Sprint 2
- ADR-0001: ULID Identifiers
"""

import logging
import re
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from ulid import ULID

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

DEFAULT_BUG_TITLE_PREFIX = "Bug: "
"""Prefix for all bug ticket titles."""


# =============================================================================
# ENUMS
# =============================================================================


class BugSeverity(str, Enum):
    """
    Severity classification for bugs.

    Values:
        LOW: Minor issue, cosmetic or edge case
        MEDIUM: Functional issue, workaround available
        HIGH: Significant issue, blocking workflow
        CRITICAL: System failure, data loss risk
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def priority_value(self) -> int:
        """Get numeric priority for sorting (higher = more severe)."""
        priority_map = {
            BugSeverity.LOW: 1,
            BugSeverity.MEDIUM: 2,
            BugSeverity.HIGH: 3,
            BugSeverity.CRITICAL: 4,
        }
        return priority_map[self]


# =============================================================================
# BUG REPORT DATACLASS
# =============================================================================


@dataclass
class BugReport:
    """
    Complete bug report with all relevant context.

    Attributes:
        title: Short description of the bug
        description: Detailed description of the issue
        command: CLI command that triggered the bug (if applicable)
        output: CLI output containing the error
        stack_trace: Python stack trace (if available)
        severity: Bug severity classification
        context: Additional context (task_id, sprint_id, etc.)
        discovered_at: When the bug was discovered
        discovered_during: What operation was running when bug was found
    """

    title: str
    description: str
    command: Optional[str] = None
    output: Optional[str] = None
    stack_trace: Optional[str] = None
    severity: BugSeverity = BugSeverity.MEDIUM
    context: Dict[str, Any] = field(default_factory=dict)
    discovered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    discovered_during: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for logging/storage."""
        return {
            "title": self.title,
            "description": self.description,
            "command": self.command,
            "output": self.output,
            "stack_trace": self.stack_trace,
            "severity": self.severity.value,
            "context": self.context,
            "discovered_at": self.discovered_at.isoformat(),
            "discovered_during": self.discovered_during,
        }

    def format_description(self) -> str:
        """
        Format a complete description for the bug ticket.

        Returns:
            Formatted markdown description with all bug details.
        """
        parts = []

        # Main description
        parts.append(self.description)
        parts.append("")

        # Discovery context
        if self.discovered_during:
            parts.append(f"**Discovered during:** {self.discovered_during}")
            parts.append("")

        # Command that triggered the bug
        if self.command:
            parts.append("**Command:**")
            parts.append(f"```bash")
            parts.append(self.command)
            parts.append("```")
            parts.append("")

        # Severity
        parts.append(f"**Severity:** {self.severity.value.upper()}")
        parts.append("")

        # Steps to reproduce
        parts.append("## Steps to Reproduce")
        if self.command:
            parts.append(f"1. Run: `{self.command}`")
            parts.append("2. Observe the error output below")
        else:
            parts.append("1. [Add steps to reproduce]")
        parts.append("")

        # Expected behavior
        parts.append("## Expected Behavior")
        parts.append("[Command should complete successfully]")
        parts.append("")

        # Actual behavior
        parts.append("## Actual Behavior")
        if self.output:
            parts.append("```")
            # Truncate long output
            if len(self.output) > 2000:
                parts.append(self.output[:2000])
                parts.append("... [output truncated]")
            else:
                parts.append(self.output)
            parts.append("```")
        else:
            parts.append("[Error occurred - see description]")
        parts.append("")

        # Stack trace
        if self.stack_trace:
            parts.append("## Stack Trace")
            parts.append("```python")
            # Truncate long stack traces
            if len(self.stack_trace) > 3000:
                parts.append(self.stack_trace[:3000])
                parts.append("... [trace truncated]")
            else:
                parts.append(self.stack_trace)
            parts.append("```")
            parts.append("")

        # Additional context
        if self.context:
            parts.append("## Context")
            for key, value in self.context.items():
                parts.append(f"- **{key}:** {value}")
            parts.append("")

        return "\n".join(parts)


# =============================================================================
# ERROR DETECTION PATTERNS
# =============================================================================

# Patterns for detecting errors in CLI output
ERROR_PATTERNS = [
    # Python exceptions
    (r"Traceback \(most recent call last\):", BugSeverity.HIGH),
    (r"^\s*File \".*\", line \d+", BugSeverity.MEDIUM),
    (r"(?:Error|Exception):\s+.+", BugSeverity.HIGH),
    (r"ModuleNotFoundError:\s+.+", BugSeverity.HIGH),
    (r"ImportError:\s+.+", BugSeverity.HIGH),
    (r"SyntaxError:\s+.+", BugSeverity.HIGH),
    (r"TypeError:\s+.+", BugSeverity.MEDIUM),
    (r"ValueError:\s+.+", BugSeverity.MEDIUM),
    (r"KeyError:\s+.+", BugSeverity.MEDIUM),
    (r"AttributeError:\s+.+", BugSeverity.MEDIUM),
    (r"RuntimeError:\s+.+", BugSeverity.HIGH),
    (r"PermissionError:\s+.+", BugSeverity.HIGH),
    (r"FileNotFoundError:\s+.+", BugSeverity.HIGH),
    (r"OSError:\s+.+", BugSeverity.MEDIUM),

    # CLI error indicators
    (r"(?:FATAL|CRITICAL|ERROR)[\s:]+.+", BugSeverity.HIGH),
    (r"^\s*error:\s+.+", BugSeverity.HIGH),
    (r"^\s*fatal:\s+.+", BugSeverity.CRITICAL),
    (r"failed with exit code \d+", BugSeverity.HIGH),

    # Specific framework errors
    (r"ValidationError:\s+.+", BugSeverity.MEDIUM),
    (r"DatabaseError:\s+.+", BugSeverity.HIGH),
    (r"ConnectionError:\s+.+", BugSeverity.MEDIUM),
]


# =============================================================================
# BUG LOGGER
# =============================================================================


class BugLogger:
    """
    Automatic bug ticket creation for the implementation loop.

    Creates bug tickets as children of a designated parent ticket,
    with automatic error detection from CLI output.

    Attributes:
        bug_ticket_id: ULID of the parent bug ticket for created bugs
        roadmap_root: Path to the roadmap directory
        session_bugs: List of bug ticket IDs created in this session

    Example:
        >>> logger = BugLogger("01KCZF73PX...", Path(".vibey/roadmap"))
        >>> bug_id = logger.log_bug("Error in module", "Details...", {}, BugSeverity.HIGH)
        >>> logger.detect_cli_error("Traceback...", "python script.py")
        True
        >>> logger.generate_bug_summary()
        {'total_bugs': 2, 'by_severity': {...}, ...}
    """

    def __init__(
        self,
        bug_ticket_id: str,
        roadmap_root: Path,
    ):
        """
        Initialize the bug logger.

        Args:
            bug_ticket_id: ULID of the parent bug ticket for all bugs
            roadmap_root: Path to .vibey/roadmap directory
        """
        self.bug_ticket_id = bug_ticket_id
        self.roadmap_root = Path(roadmap_root)
        self.session_bugs: List[str] = []
        self._bug_reports: List[BugReport] = []

        logger.debug(
            f"BugLogger initialized with parent ticket {bug_ticket_id}, "
            f"roadmap at {roadmap_root}"
        )

    # =========================================================================
    # MAIN METHODS
    # =========================================================================

    def log_bug(
        self,
        title: str,
        description: str,
        context: Dict[str, Any],
        severity: BugSeverity = BugSeverity.MEDIUM,
    ) -> str:
        """
        Log a bug by creating a child ticket under the parent bug ticket.

        Creates a new TaskTicket with:
        - Title prefixed with "Bug: "
        - Description formatted with context
        - parent_ref set to bug_ticket_id

        Args:
            title: Short description of the bug
            description: Detailed description
            context: Additional context (task_id, command, output, etc.)
            severity: Bug severity level

        Returns:
            ULID of the created bug ticket
        """
        # Create bug report
        report = BugReport(
            title=title,
            description=description,
            severity=severity,
            context=context,
            command=context.get("command"),
            output=context.get("output"),
            stack_trace=context.get("stack_trace"),
            discovered_during=context.get("discovered_during"),
        )

        return self.create_bug_ticket(report)

    def detect_cli_error(
        self,
        output: str,
        command: str,
    ) -> bool:
        """
        Analyze CLI output for potential bugs and create tickets if found.

        Scans the output for error patterns and automatically creates
        bug tickets for detected errors.

        Args:
            output: CLI command output (stdout + stderr)
            command: The command that was executed

        Returns:
            True if an error was detected and a bug ticket was created
        """
        if not output:
            return False

        detected_severity = None
        matched_pattern = None

        # Check each error pattern
        for pattern, severity in ERROR_PATTERNS:
            if re.search(pattern, output, re.MULTILINE | re.IGNORECASE):
                # Use highest severity found
                if detected_severity is None or severity.priority_value > detected_severity.priority_value:
                    detected_severity = severity
                    matched_pattern = pattern

        if detected_severity is None:
            return False

        # Extract error message for title
        title = self._extract_error_title(output)

        # Extract stack trace if present
        stack_trace = self._extract_stack_trace(output)

        # Create bug report
        report = BugReport(
            title=title,
            description=f"Error detected during command execution: {command}",
            command=command,
            output=output,
            stack_trace=stack_trace,
            severity=detected_severity,
            context={
                "matched_pattern": matched_pattern,
                "auto_detected": True,
            },
        )

        self.create_bug_ticket(report)
        logger.info(
            f"Auto-detected {detected_severity.value} bug in command output: {title[:50]}..."
        )
        return True

    def create_bug_ticket(self, report: BugReport) -> str:
        """
        Create a bug ticket from a BugReport.

        Creates a TaskTicket in the roadmap with:
        - Formatted description including all bug details
        - parent_ref pointing to the bug_ticket_id
        - Appropriate priority based on severity

        Args:
            report: Complete bug report

        Returns:
            ULID of the created bug ticket
        """
        # Generate new ULID for the bug ticket
        bug_id = str(ULID())

        # Format the title
        full_title = f"{DEFAULT_BUG_TITLE_PREFIX}{report.title}"

        # Map severity to priority
        priority_map = {
            BugSeverity.LOW: "low",
            BugSeverity.MEDIUM: "medium",
            BugSeverity.HIGH: "high",
            BugSeverity.CRITICAL: "critical",
        }
        priority = priority_map[report.severity]

        # Create the ticket data
        ticket_data = {
            "task": {
                "format_version": "v2",
                "id": bug_id,
                "name": full_title,
                "title": full_title,
                "description": report.format_description(),
                "status": "not_started",
                "priority": priority,
                "parent_ref": self.bug_ticket_id,
                "task_type_detail": "development",
                "created_at": report.discovered_at.isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "metadata": {
                    "bug_severity": report.severity.value,
                    "auto_created": True,
                    "discovered_at": report.discovered_at.isoformat(),
                },
            }
        }

        # Save the ticket
        task_path = self.roadmap_root / "tasks" / f"{bug_id}.yaml"
        task_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            import yaml
            with open(task_path, "w") as f:
                yaml.dump(ticket_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

            # Track the bug
            self.session_bugs.append(bug_id)
            self._bug_reports.append(report)

            logger.info(f"Created bug ticket {bug_id}: {full_title}")
            return bug_id

        except Exception as e:
            logger.error(f"Failed to create bug ticket: {e}")
            raise

    def get_session_bugs(self) -> List[str]:
        """
        Get all bug ticket IDs created in this session.

        Returns:
            List of bug ticket ULIDs
        """
        return list(self.session_bugs)

    def generate_bug_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of bugs found in this session.

        Returns:
            Dictionary with:
            - total_bugs: Total number of bugs found
            - by_severity: Count by severity level
            - bug_ids: List of bug ticket IDs
            - reports: List of bug report dicts
        """
        by_severity: Dict[str, int] = {
            "low": 0,
            "medium": 0,
            "high": 0,
            "critical": 0,
        }

        for report in self._bug_reports:
            by_severity[report.severity.value] += 1

        return {
            "total_bugs": len(self.session_bugs),
            "by_severity": by_severity,
            "bug_ids": list(self.session_bugs),
            "reports": [r.to_dict() for r in self._bug_reports],
        }

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _extract_error_title(self, output: str) -> str:
        """
        Extract a concise error title from output.

        Args:
            output: CLI output containing error

        Returns:
            Short error title (max 100 chars)
        """
        # Look for common error patterns
        patterns = [
            # Python exception with message
            r"(\w+Error|\w+Exception):\s*(.+?)(?:\n|$)",
            # Fatal/error prefix
            r"(?:fatal|error):\s*(.+?)(?:\n|$)",
            # Failed with message
            r"failed:\s*(.+?)(?:\n|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                if match.lastindex == 2:
                    # Exception type + message
                    title = f"{match.group(1)}: {match.group(2)}"
                else:
                    title = match.group(1)

                # Truncate if too long
                if len(title) > 100:
                    title = title[:97] + "..."
                return title.strip()

        # Default: first line of output (truncated)
        first_line = output.split("\n")[0].strip()
        if len(first_line) > 100:
            first_line = first_line[:97] + "..."
        return first_line or "Unknown error"

    def _extract_stack_trace(self, output: str) -> Optional[str]:
        """
        Extract Python stack trace from output if present.

        Args:
            output: CLI output that may contain a traceback

        Returns:
            Stack trace string or None
        """
        # Look for Python traceback
        traceback_pattern = r"(Traceback \(most recent call last\):[\s\S]*?)(?=\n\n|\Z)"
        match = re.search(traceback_pattern, output)

        if match:
            return match.group(1).strip()

        return None


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "BugSeverity",
    "BugReport",
    "BugLogger",
    "DEFAULT_BUG_TITLE_PREFIX",
    "ERROR_PATTERNS",
]
