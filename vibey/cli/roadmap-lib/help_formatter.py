"""
Enhanced help formatting for roadmap CLI.

Provides rich, contextual help messages with examples and tips.
"""

from typing import List, Dict, Optional
from .formatting import header, bold, dim, colorize, Color, info, success


class CLIHelpFormatter:
    """Format enhanced help messages for CLI commands."""

    @staticmethod
    def format_command_help(
        command: str,
        description: str,
        usage: str,
        options: List[Dict[str, str]],
        examples: Optional[List[Dict[str, str]]] = None,
        see_also: Optional[List[str]] = None,
        tips: Optional[List[str]] = None,
    ) -> str:
        """
        Format comprehensive help for a command.

        Args:
            command: Command name
            description: Command description
            usage: Usage syntax
            options: List of {flag, description, default (optional)}
            examples: List of {description, command}
            see_also: List of related commands
            tips: List of helpful tips

        Returns:
            Formatted help text
        """
        lines = []

        # Header
        lines.append(header(f"{command} - {description}", level=1))

        # Usage
        lines.append(bold("USAGE:"))
        lines.append(f"  {usage}")
        lines.append("")

        # Options
        if options:
            lines.append(bold("OPTIONS:"))
            for opt in options:
                flag = opt['flag']
                desc = opt['description']
                default = opt.get('default')

                if default:
                    lines.append(f"  {colorize(flag, Color.CYAN):<25} {desc}")
                    lines.append(f"  {' ' * 25} {dim(f'(default: {default})')}")
                else:
                    lines.append(f"  {colorize(flag, Color.CYAN):<25} {desc}")
            lines.append("")

        # Examples
        if examples:
            lines.append(bold("EXAMPLES:"))
            for i, ex in enumerate(examples, 1):
                desc = ex['description']
                cmd = ex['command']
                lines.append(f"  {i}. {desc}")
                lines.append(f"     $ {colorize(cmd, Color.GREEN)}")
                lines.append("")

        # Tips
        if tips:
            lines.append(bold("TIPS:"))
            for tip in tips:
                lines.append(f"  💡 {tip}")
            lines.append("")

        # See Also
        if see_also:
            lines.append(bold("SEE ALSO:"))
            for related in see_also:
                lines.append(f"  • {related}")
            lines.append("")

        return '\n'.join(lines)

    @staticmethod
    def format_error_with_suggestion(
        error: str,
        suggestions: List[str],
        hint: Optional[str] = None
    ) -> str:
        """
        Format error message with helpful suggestions.

        Args:
            error: Error message
            suggestions: List of suggested actions
            hint: Optional hint for resolving the error

        Returns:
            Formatted error with suggestions
        """
        lines = []

        # Error
        lines.append(colorize(f"✗ Error: {error}", Color.RED))
        lines.append("")

        # Hint
        if hint:
            lines.append(colorize(f"💡 Hint: {hint}", Color.YELLOW))
            lines.append("")

        # Suggestions
        if suggestions:
            lines.append(bold("Try:"))
            for suggestion in suggestions:
                lines.append(f"  • {suggestion}")
            lines.append("")

        return '\n'.join(lines)

    @staticmethod
    def format_validation_error(
        field: str,
        value: any,
        expected: str,
        context: Optional[str] = None
    ) -> str:
        """
        Format validation error with context.

        Args:
            field: Field name that failed validation
            value: Invalid value provided
            expected: Description of expected value
            context: Optional context (e.g., file path, object ID)

        Returns:
            Formatted validation error
        """
        lines = []

        # Error header
        lines.append(colorize(f"✗ Validation Error", Color.RED))
        lines.append("")

        # Context
        if context:
            lines.append(f"Context: {dim(context)}")
            lines.append("")

        # Details
        lines.append(f"Field:    {colorize(field, Color.CYAN)}")
        lines.append(f"Got:      {colorize(str(value), Color.RED)}")
        lines.append(f"Expected: {colorize(expected, Color.GREEN)}")
        lines.append("")

        return '\n'.join(lines)

    @staticmethod
    def format_dependency_error(
        object_id: str,
        object_type: str,
        blocker_id: str,
        blocker_type: str,
        required_status: str,
        current_status: str,
    ) -> str:
        """
        Format dependency blocking error.

        Args:
            object_id: ID of blocked object
            object_type: Type of blocked object
            blocker_id: ID of blocker
            blocker_type: Type of blocker
            required_status: Required status to unblock
            current_status: Current status of blocker

        Returns:
            Formatted dependency error
        """
        lines = []

        # Error header
        lines.append(colorize(f"✗ Dependency Blocked", Color.RED))
        lines.append("")

        # Object info
        lines.append(f"{object_type.capitalize()}: {colorize(object_id, Color.CYAN)}")
        lines.append("")

        # Blocker info
        lines.append(bold("Blocked by:"))
        lines.append(f"  {blocker_type.capitalize()}: {colorize(blocker_id, Color.YELLOW)}")
        lines.append(f"  Current status:  {colorize(current_status, Color.RED)}")
        lines.append(f"  Required status: {colorize(required_status, Color.GREEN)}")
        lines.append("")

        # Next steps
        lines.append(bold("To unblock:"))
        lines.append(f"  1. Complete {blocker_type} '{blocker_id}'")
        lines.append(f"  2. Ensure it reaches status '{required_status}'")
        lines.append(f"  3. Retry this operation")
        lines.append("")

        # Helpful command
        lines.append(bold("Check blocker status:"))
        if blocker_type == 'task':
            lines.append(f"  $ roadmap-query.py --task {blocker_id}")
        elif blocker_type == 'sprint':
            lines.append(f"  $ roadmap-query.py --sprint {blocker_id}")
        elif blocker_type == 'track':
            lines.append(f"  $ roadmap-query.py --track {blocker_id}")
        lines.append("")

        return '\n'.join(lines)

    @staticmethod
    def format_not_found_error(
        object_id: str,
        object_type: str,
        searched_paths: Optional[List[str]] = None
    ) -> str:
        """
        Format "not found" error with search paths.

        Args:
            object_id: ID of object not found
            object_type: Type of object
            searched_paths: Paths that were searched

        Returns:
            Formatted not found error
        """
        lines = []

        # Error header
        lines.append(colorize(f"✗ {object_type.capitalize()} Not Found", Color.RED))
        lines.append("")

        # Object info
        lines.append(f"ID: {colorize(object_id, Color.CYAN)}")
        lines.append("")

        # Searched paths
        if searched_paths:
            lines.append(bold("Searched in:"))
            for path in searched_paths:
                lines.append(f"  • {dim(path)}")
            lines.append("")

        # Suggestions
        lines.append(bold("Suggestions:"))
        lines.append(f"  • Check the {object_type} ID is correct")
        lines.append(f"  • List all {object_type}s: roadmap-query.py --list-{object_type}s")
        if object_type == 'task':
            lines.append(f"  • Verify sprint ID (tasks are sprint-scoped)")
        lines.append("")

        return '\n'.join(lines)

    @staticmethod
    def format_progress_summary(
        object_name: str,
        completed: int,
        total: int,
        status: str,
        details: Optional[Dict[str, any]] = None
    ) -> str:
        """
        Format progress summary for an object.

        Args:
            object_name: Name of object
            completed: Number completed
            total: Total number
            status: Current status
            details: Optional additional details

        Returns:
            Formatted progress summary
        """
        from .formatting import progress_bar, status_indicator

        lines = []

        # Header
        lines.append(bold(object_name))
        lines.append("")

        # Status
        lines.append(f"Status: {status_indicator(status)}")
        lines.append("")

        # Progress bar
        if total > 0:
            lines.append("Progress:")
            lines.append(f"  {progress_bar(completed, total, width=40)}")
            lines.append("")

        # Details
        if details:
            for key, value in details.items():
                lines.append(f"{key}: {value}")
            lines.append("")

        return '\n'.join(lines)


# Pre-defined help messages for common commands

ROADMAP_QUERY_HELP = CLIHelpFormatter.format_command_help(
    command="roadmap-query.py",
    description="Query roadmap state (read-only operations)",
    usage="python3 roadmap-query.py [OPTIONS]",
    options=[
        {"flag": "--dir DIR", "description": "Root directory (.vibey)", "default": "auto-detected"},
        {"flag": "--track TRACK", "description": "Show track details"},
        {"flag": "--sprint SPRINT", "description": "Show sprint details"},
        {"flag": "--task TASK", "description": "Show task details"},
        {"flag": "--blockers", "description": "Show all blockers"},
        {"flag": "--id ID", "description": "Show blockers for specific object"},
        {"flag": "--dependencies", "description": "Show dependency graph"},
        {"flag": "--json", "description": "Output as JSON"},
    ],
    examples=[
        {
            "description": "Show roadmap summary",
            "command": "python3 roadmap-query.py"
        },
        {
            "description": "Show sprint progress",
            "command": "python3 roadmap-query.py --sprint backend-1"
        },
        {
            "description": "Show what's blocking a task",
            "command": "python3 roadmap-query.py --blockers --id backend-1-task-002"
        },
        {
            "description": "Export as JSON for processing",
            "command": "python3 roadmap-query.py --sprint backend-1 --json | jq ."
        },
    ],
    tips=[
        "Use --json for programmatic access and piping to other tools",
        "Check blockers regularly to identify what's preventing progress",
        "Use --dependencies to visualize the entire dependency graph"
    ],
    see_also=[
        "roadmap-update.py - Update roadmap state",
        "roadmap-init.py - Initialize new roadmap",
        "ROADMAP_CLI_REFERENCE.md - Complete command reference"
    ]
)

ROADMAP_UPDATE_HELP = CLIHelpFormatter.format_command_help(
    command="roadmap-update.py",
    description="Update roadmap state (write operations)",
    usage="python3 roadmap-update.py [OPTIONS]",
    options=[
        {"flag": "--dir DIR", "description": "Root directory (.vibey)", "default": "auto-detected"},
        {"flag": "--start-task TASK_ID", "description": "Start a task"},
        {"flag": "--complete-task TASK_ID", "description": "Complete a task"},
        {"flag": "--start-sprint SPRINT_ID", "description": "Start a sprint"},
        {"flag": "--complete-sprint SPRINT_ID", "description": "Complete a sprint"},
        {"flag": "--refresh-progress", "description": "Recalculate all progress metrics"},
        {"flag": "--by USER", "description": "User making the update", "default": "system"},
    ],
    examples=[
        {
            "description": "Start working on a task",
            "command": "python3 roadmap-update.py --start-task backend-1-task-001"
        },
        {
            "description": "Complete a task",
            "command": "python3 roadmap-update.py --complete-task backend-1-task-001"
        },
        {
            "description": "Start a sprint",
            "command": "python3 roadmap-update.py --start-sprint backend-1"
        },
        {
            "description": "Complete sprint (after all completion gates pass)",
            "command": "python3 roadmap-update.py --complete-sprint backend-1"
        },
    ],
    tips=[
        "Check dependencies before starting: roadmap-query.py --blockers --id <ID>",
        "Tasks auto-unblock dependent tasks when completed",
        "Use --refresh-progress if metrics seem stale"
    ],
    see_also=[
        "roadmap-query.py - Query roadmap state",
        "ROADMAP_USER_GUIDE.md - Comprehensive user guide"
    ]
)

ROADMAP_INIT_HELP = CLIHelpFormatter.format_command_help(
    command="roadmap-init.py",
    description="Initialize a new roadmap",
    usage="python3 roadmap-init.py --id ID --name NAME [OPTIONS]",
    options=[
        {"flag": "--id ID", "description": "Roadmap ID (lowercase-with-hyphens)"},
        {"flag": "--name NAME", "description": "Human-readable name"},
        {"flag": "--dir DIR", "description": "Root directory", "default": ".vibey"},
        {"flag": "--description DESC", "description": "Project description"},
        {"flag": "--project-type TYPE", "description": "Project type", "default": "web-app"},
    ],
    examples=[
        {
            "description": "Initialize basic roadmap",
            "command": 'python3 roadmap-init.py --id my-project --name "My Project"'
        },
        {
            "description": "Initialize with description and type",
            "command": 'python3 roadmap-init.py --id ml-pipeline --name "ML Pipeline" --description "Customer churn prediction" --project-type ml-platform'
        },
    ],
    tips=[
        "Use descriptive IDs (e.g., 'ecommerce-platform' not 'proj1')",
        "Choose appropriate project-type for better templates",
        "Run this once per project - subsequent work uses roadmap-update.py"
    ],
    see_also=[
        "roadmap-query.py - Query the roadmap you just created",
        "examples/roadmaps/ - Example roadmaps to learn from"
    ]
)
