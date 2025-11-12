"""
CLI output formatters for human-readable display.

This module converts JSON responses from operations modules into
formatted text output for CLI users.
"""

from typing import Dict, Any, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console()


def format_roadmap_summary(data: Dict[str, Any]) -> str:
    """
    Format roadmap summary for CLI display.

    Args:
        data: Roadmap summary dict from query_roadmap_summary()

    Returns:
        Formatted string for display
    """
    if "error" in data:
        return f"❌ Error: {data['error']}"

    output = []
    output.append("=" * 70)
    output.append(f"📋 Roadmap: {data.get('name', 'Unknown')}")
    output.append(f"Version: {data.get('version', 'Unknown')}")
    output.append("=" * 70)
    output.append("")

    tracks = data.get('tracks', [])
    if not tracks:
        output.append("No tracks found. The roadmap is empty.")
        return "\n".join(output)

    output.append(f"📊 Tracks: {len(tracks)}")
    output.append("")

    for track in tracks:
        status_icon = _get_status_icon(track.get('status'))
        progress = track.get('progress', {})
        tasks_done = progress.get('tasks_completed', 0)
        tasks_total = progress.get('tasks_total', 0)
        pct = (tasks_done / tasks_total * 100) if tasks_total > 0 else 0

        output.append(f"{status_icon} {track.get('id', 'unknown')}")
        output.append(f"   {track.get('name', 'Unknown Track')}")
        output.append(f"   Progress: {tasks_done}/{tasks_total} tasks ({pct:.0f}%)")
        output.append(f"   {_render_progress_bar(pct)}")
        output.append("")

    return "\n".join(output)


def format_track_details(data: Dict[str, Any]) -> str:
    """Format track details for CLI display."""
    if "error" in data:
        return f"❌ Error: {data['error']}"

    output = []
    output.append("=" * 70)
    output.append(f"📦 Track: {data.get('name', 'Unknown')}")
    output.append(f"ID: {data.get('id', 'Unknown')}")
    output.append(f"Status: {data.get('status', 'unknown')}")
    output.append("=" * 70)
    output.append("")

    if data.get('description'):
        output.append(f"Description: {data['description']}")
        output.append("")

    sprints = data.get('sprints', [])
    if sprints:
        output.append(f"📅 Sprints: {len(sprints)}")
        output.append("")
        for sprint in sprints:
            status_icon = _get_status_icon(sprint.get('status'))
            output.append(f"  {status_icon} {sprint.get('id')} - {sprint.get('name', 'Unknown')}")
            output.append(f"     Status: {sprint.get('status', 'unknown')}")
            tasks = sprint.get('tasks', [])
            if tasks:
                output.append(f"     Tasks: {len(tasks)}")
            output.append("")
    else:
        output.append("No sprints found.")

    return "\n".join(output)


def format_sprint_details(data: Dict[str, Any]) -> str:
    """Format sprint details for CLI display."""
    if "error" in data:
        return f"❌ Error: {data['error']}"

    output = []
    output.append("=" * 70)
    output.append(f"🎯 Sprint: {data.get('name', 'Unknown')}")
    output.append(f"ID: {data.get('id', 'Unknown')}")
    output.append(f"Status: {data.get('status', 'unknown')}")
    output.append("=" * 70)
    output.append("")

    if data.get('description'):
        output.append(f"Description: {data['description']}")
        output.append("")

    # Handle tasks dict with categorized task types (new format)
    tasks_data = data.get('tasks', {})

    # Development tasks
    dev_tasks = tasks_data.get('development', []) if isinstance(tasks_data, dict) else tasks_data
    if dev_tasks:
        output.append(f"📝 Development Tasks: {len(dev_tasks)}")
        output.append("")
        for task in dev_tasks:
            status_icon = _get_status_icon(task.get('status'))
            output.append(f"  {status_icon} {task.get('id')} - {task.get('title', 'Unknown')}")
            output.append(f"     Status: {task.get('status', 'unknown')}")
            if task.get('assigned_to'):
                output.append(f"     Assigned: {task['assigned_to']}")
            output.append("")

    # Completion gates (always show section header for consistency)
    completion_gates = tasks_data.get('completion_gates', []) if isinstance(tasks_data, dict) else []
    output.append(f"🚧 Completion Gates: {len(completion_gates)}")
    output.append("")
    if completion_gates:
        for task in completion_gates:
            status_icon = _get_status_icon(task.get('status'))
            output.append(f"  {status_icon} {task.get('id')} - {task.get('title', 'Unknown')}")
            output.append(f"     Status: {task.get('status', 'unknown')}")
            output.append("")
    else:
        output.append("  (none)")
        output.append("")

    # Production gates (always show section header for consistency)
    production_gates = tasks_data.get('production_gates', []) if isinstance(tasks_data, dict) else []
    output.append(f"🔍 Production Gates: {len(production_gates)}")
    output.append("")
    if production_gates:
        for task in production_gates:
            status_icon = _get_status_icon(task.get('status'))
            output.append(f"  {status_icon} {task.get('id')} - {task.get('title', 'Unknown')}")
            output.append(f"     Status: {task.get('status', 'unknown')}")
            output.append("")
    else:
        output.append("  (none)")
        output.append("")

    if not dev_tasks and not completion_gates and not production_gates:
        output.append("No tasks found.")

    return "\n".join(output)


def format_task_details(data: Dict[str, Any]) -> str:
    """Format task details for CLI display."""
    if "error" in data:
        return f"❌ Error: {data['error']}"

    output = []
    output.append("=" * 70)
    output.append(f"✓ Task: {data.get('title', 'Unknown')}")
    output.append(f"ID: {data.get('id', 'Unknown')}")
    output.append(f"Status: {data.get('status', 'unknown')}")
    output.append("=" * 70)
    output.append("")

    if data.get('description'):
        output.append(f"Description: {data['description']}")
        output.append("")

    if data.get('assigned_to'):
        output.append(f"Assigned to: {data['assigned_to']}")

    if data.get('files_to_modify'):
        output.append(f"\n📁 Files to modify:")
        for file in data['files_to_modify']:
            output.append(f"  - {file}")

    if data.get('dependencies'):
        output.append(f"\n🔗 Dependencies:")
        for dep in data['dependencies']:
            output.append(f"  - {dep}")

    return "\n".join(output)


def format_error(error_msg: str) -> str:
    """Format error message for CLI display."""
    return f"❌ Error: {error_msg}"


def format_success(message: str) -> str:
    """Format success message for CLI display."""
    return f"✅ {message}"


def _get_status_icon(status: str) -> str:
    """Get emoji icon for status."""
    status_icons = {
        'not_started': '⚪',
        'in_progress': '🔵',
        'completed': '✅',
        'blocked': '🔴',
        'paused': '⏸️',
    }
    return status_icons.get(status, '❓')


def _render_progress_bar(percentage: float, width: int = 30) -> str:
    """Render a text progress bar."""
    filled = int(width * percentage / 100)
    empty = width - filled
    bar = '█' * filled + '░' * empty
    return f"[{bar}] {percentage:.0f}%"
