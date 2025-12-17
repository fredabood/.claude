"""
Terminal formatting utilities for roadmap CLI.

Provides colored output, progress bars, tables, and tree views
without external dependencies (uses ANSI escape codes).
"""

import sys
import os
from typing import List, Dict, Optional
from enum import Enum


class Color(Enum):
    """ANSI color codes."""
    # Basic colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'

    # Reset
    RESET = '\033[0m'


class StatusIcon(Enum):
    """Status icons with colors."""
    COMPLETED = ('✅', Color.GREEN)
    IN_PROGRESS = ('🔵', Color.BLUE)
    PENDING = ('⚪', Color.WHITE)
    BLOCKED = ('❌', Color.RED)
    PLANNING = ('📋', Color.CYAN)


# Global flag for plain output
_PLAIN_MODE = False


def set_plain_mode(enabled: bool):
    """Enable or disable plain mode (no colors/formatting)."""
    global _PLAIN_MODE
    _PLAIN_MODE = enabled


def is_plain_mode() -> bool:
    """Check if plain mode is enabled."""
    return _PLAIN_MODE or not _supports_color()


def _supports_color() -> bool:
    """Check if terminal supports color output."""
    # Check if output is a TTY
    if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
        return False

    # Check for NO_COLOR environment variable
    if os.environ.get('NO_COLOR'):
        return False

    # Check TERM environment variable
    term = os.environ.get('TERM', '')
    if term == 'dumb':
        return False

    return True


def colorize(text: str, color: Color) -> str:
    """Apply color to text."""
    if is_plain_mode():
        return text
    return f"{color.value}{text}{Color.RESET.value}"


def bold(text: str) -> str:
    """Make text bold."""
    if is_plain_mode():
        return text
    return f"{Color.BOLD.value}{text}{Color.RESET.value}"


def dim(text: str) -> str:
    """Make text dimmed."""
    if is_plain_mode():
        return text
    return f"{Color.DIM.value}{text}{Color.RESET.value}"


def status_indicator(status: str) -> str:
    """
    Get colored status indicator.

    Args:
        status: Status string (completed, in_progress, pending, blocked, etc.)

    Returns:
        Formatted status with icon and color
    """
    status_lower = status.lower().replace(' ', '_')

    # Map status to icon
    status_map = {
        'completed': StatusIcon.COMPLETED,
        'in_progress': StatusIcon.IN_PROGRESS,
        'pending': StatusIcon.PENDING,
        'not_started': StatusIcon.PENDING,
        'blocked': StatusIcon.BLOCKED,
        'planning': StatusIcon.PLANNING,
    }

    icon_enum = status_map.get(status_lower, StatusIcon.PENDING)
    icon, color = icon_enum.value

    if is_plain_mode():
        return status

    return f"{icon} {colorize(status, color)}"


def progress_bar(current: int, total: int, width: int = 30, show_percentage: bool = True) -> str:
    """
    Create a progress bar.

    Args:
        current: Current value
        total: Total value
        width: Width of progress bar in characters
        show_percentage: Show percentage after bar

    Returns:
        Formatted progress bar
    """
    if total == 0:
        percentage = 0
    else:
        percentage = (current / total) * 100

    if is_plain_mode():
        if show_percentage:
            return f"{current}/{total} ({percentage:.0f}%)"
        return f"{current}/{total}"

    filled = int((current / total) * width) if total > 0 else 0
    bar = '█' * filled + '░' * (width - filled)

    # Color based on percentage
    if percentage >= 100:
        color = Color.GREEN
    elif percentage >= 75:
        color = Color.BRIGHT_GREEN
    elif percentage >= 50:
        color = Color.YELLOW
    elif percentage >= 25:
        color = Color.BRIGHT_YELLOW
    else:
        color = Color.RED

    colored_bar = colorize(bar, color)

    if show_percentage:
        return f"{colored_bar} {percentage:.0f}% ({current}/{total})"
    return f"{colored_bar} ({current}/{total})"


def table(headers: List[str], rows: List[List[str]], title: Optional[str] = None) -> str:
    """
    Create a formatted table.

    Args:
        headers: Column headers
        rows: List of rows (each row is a list of strings)
        title: Optional table title

    Returns:
        Formatted table as string
    """
    if not rows:
        return ""

    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            # Strip ANSI codes for width calculation
            clean_cell = _strip_ansi(str(cell))
            col_widths[i] = max(col_widths[i], len(clean_cell))

    # Build table
    lines = []

    # Title
    if title:
        total_width = sum(col_widths) + len(col_widths) * 3 + 1
        if is_plain_mode():
            lines.append(title)
            lines.append("=" * total_width)
        else:
            lines.append(bold(title))
            lines.append("─" * total_width)

    # Headers
    header_row = " │ ".join(
        headers[i].ljust(col_widths[i]) for i in range(len(headers))
    )
    if not is_plain_mode():
        header_row = bold(header_row)
    lines.append(header_row)

    # Separator
    separator = "─┼─".join("─" * w for w in col_widths)
    lines.append(separator)

    # Rows
    for row in rows:
        # Pad row to match header length
        padded_row = list(row) + [''] * (len(headers) - len(row))
        formatted_row = []
        for i, cell in enumerate(padded_row):
            cell_str = str(cell)
            clean_cell = _strip_ansi(cell_str)
            padding = col_widths[i] - len(clean_cell)
            formatted_row.append(cell_str + ' ' * padding)
        lines.append(" │ ".join(formatted_row))

    return '\n'.join(lines)


def tree(items: List[Dict], indent_str: str = "  ", show_status: bool = True) -> str:
    """
    Create a tree view for hierarchical data.

    Args:
        items: List of items with 'id', 'name', 'status', 'children' (optional)
        indent_str: String to use for indentation
        show_status: Show status indicators

    Returns:
        Formatted tree as string
    """
    lines = []

    def render_item(item: Dict, level: int = 0, is_last: bool = True, prefix: str = ""):
        # Tree characters
        if level == 0:
            connector = ""
        elif is_last:
            connector = "└─ "
        else:
            connector = "├─ "

        # Status indicator
        status = item.get('status', 'pending')
        if show_status:
            status_str = status_indicator(status) + " "
        else:
            status_str = ""

        # Item name
        name = item.get('name', item.get('id', 'Unknown'))

        # Build line
        line = f"{prefix}{connector}{status_str}{name}"
        lines.append(line)

        # Render children
        children = item.get('children', [])
        for i, child in enumerate(children):
            is_child_last = (i == len(children) - 1)
            if level == 0:
                child_prefix = prefix
            elif is_last:
                child_prefix = prefix + "   "
            else:
                child_prefix = prefix + "│  "
            render_item(child, level + 1, is_child_last, child_prefix)

    for i, item in enumerate(items):
        is_last = (i == len(items) - 1)
        render_item(item, 0, is_last)

    return '\n'.join(lines)


def header(text: str, level: int = 1) -> str:
    """
    Create a formatted header.

    Args:
        text: Header text
        level: Header level (1-3)

    Returns:
        Formatted header
    """
    if is_plain_mode():
        if level == 1:
            return f"\n{text}\n{'=' * len(text)}\n"
        elif level == 2:
            return f"\n{text}\n{'-' * len(text)}\n"
        else:
            return f"\n{text}\n"

    if level == 1:
        return f"\n{bold(colorize(text, Color.BRIGHT_CYAN))}\n{'═' * len(text)}\n"
    elif level == 2:
        return f"\n{bold(text)}\n{'─' * len(text)}\n"
    else:
        return f"\n{bold(text)}\n"


def success(text: str) -> str:
    """Format success message."""
    if is_plain_mode():
        return f"SUCCESS: {text}"
    return f"{colorize('✓', Color.GREEN)} {text}"


def error(text: str) -> str:
    """Format error message."""
    if is_plain_mode():
        return f"ERROR: {text}"
    return f"{colorize('✗', Color.RED)} {colorize(text, Color.RED)}"


def warning(text: str) -> str:
    """Format warning message."""
    if is_plain_mode():
        return f"WARNING: {text}"
    return f"{colorize('⚠', Color.YELLOW)} {colorize(text, Color.YELLOW)}"


def info(text: str) -> str:
    """Format info message."""
    if is_plain_mode():
        return f"INFO: {text}"
    return f"{colorize('ℹ', Color.BLUE)} {text}"


def _strip_ansi(text: str) -> str:
    """Strip ANSI escape codes from text."""
    import re
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)
