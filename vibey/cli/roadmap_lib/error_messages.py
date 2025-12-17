"""
Centralized error messages for roadmap CLI.

Provides consistent, helpful error messages across all commands.
"""

from typing import List, Optional, Dict
from help_formatter import CLIHelpFormatter


class ErrorMessages:
    """Centralized error message templates."""

    @staticmethod
    def roadmap_not_found(searched_dir: str) -> str:
        """Error when roadmap.yaml not found."""
        return CLIHelpFormatter.format_error_with_suggestion(
            error=f"Roadmap not found in {searched_dir}",
            suggestions=[
                "Initialize a roadmap: python3 roadmap-init.py --id my-project --name 'My Project'",
                "Check you're in the correct directory",
                "Specify directory manually: --dir /path/to/.vibey"
            ],
            hint="Roadmap systems require initialization before use"
        )

    @staticmethod
    def track_not_found(track_id: str, available: Optional[List[str]] = None) -> str:
        """Error when track not found."""
        error = f"Track '{track_id}' not found"

        suggestions = [
            f"List all tracks: python3 roadmap-query.py --list-tracks",
            "Check the track ID is spelled correctly",
        ]

        if available:
            suggestions.append(f"Available tracks: {', '.join(available)}")

        return CLIHelpFormatter.format_error_with_suggestion(
            error=error,
            suggestions=suggestions,
            hint="Track IDs are case-sensitive and use kebab-case (lowercase-with-hyphens)"
        )

    @staticmethod
    def sprint_not_found(sprint_id: str, track_id: Optional[str] = None) -> str:
        """Error when sprint not found."""
        error = f"Sprint '{sprint_id}' not found"

        suggestions = [
            "List all sprints: python3 roadmap-query.py --list-sprints",
            "Check the sprint ID is spelled correctly",
        ]

        if track_id:
            suggestions.append(f"List sprints in track: python3 roadmap-query.py --track {track_id}")

        return CLIHelpFormatter.format_error_with_suggestion(
            error=error,
            suggestions=suggestions,
            hint="Sprint IDs should follow the pattern: <track-id>-<sprint-number> (e.g., backend-1)"
        )

    @staticmethod
    def task_not_found(task_id: str, sprint_id: Optional[str] = None) -> str:
        """Error when task not found."""
        error = f"Task '{task_id}' not found"

        suggestions = []

        if sprint_id:
            suggestions.append(f"List tasks in sprint: python3 roadmap-query.py --sprint {sprint_id}")
        else:
            # Try to extract sprint ID
            if '-task-' in task_id:
                extracted_sprint = task_id.split('-task-')[0]
                suggestions.append(f"List tasks in sprint '{extracted_sprint}': python3 roadmap-query.py --sprint {extracted_sprint}")

        suggestions.extend([
            "Check the task ID is spelled correctly",
            "Verify the sprint exists first",
        ])

        return CLIHelpFormatter.format_error_with_suggestion(
            error=error,
            suggestions=suggestions,
            hint="Task IDs should follow the pattern: <sprint-id>-task-<number> (e.g., backend-1-task-001)"
        )

    @staticmethod
    def dependency_blocked(
        object_id: str,
        object_type: str,
        blocker_id: str,
        blocker_type: str,
        required_status: str,
        current_status: str,
    ) -> str:
        """Error when operation blocked by dependency."""
        return CLIHelpFormatter.format_dependency_error(
            object_id=object_id,
            object_type=object_type,
            blocker_id=blocker_id,
            blocker_type=blocker_type,
            required_status=required_status,
            current_status=current_status
        )

    @staticmethod
    def invalid_status_transition(
        object_id: str,
        current_status: str,
        attempted_status: str,
        valid_transitions: List[str]
    ) -> str:
        """Error when status transition is invalid."""
        error = f"Cannot transition {object_id} from '{current_status}' to '{attempted_status}'"

        suggestions = [
            f"Valid transitions from '{current_status}': {', '.join(valid_transitions)}",
            f"Check current status: python3 roadmap-query.py --id {object_id}",
            "Ensure all dependencies are satisfied"
        ]

        return CLIHelpFormatter.format_error_with_suggestion(
            error=error,
            suggestions=suggestions,
            hint="Status transitions follow a strict progression to maintain data integrity"
        )

    @staticmethod
    def completion_gate_not_passed(
        sprint_id: str,
        incomplete_gates: List[str]
    ) -> str:
        """Error when trying to complete sprint without passing completion gates."""
        gates_list = "\n  ".join(f"• {gate}" for gate in incomplete_gates)

        error = f"Cannot complete sprint '{sprint_id}' - completion gates not passed"

        suggestions = [
            "Complete all completion gates before completing the sprint",
            f"Incomplete gates:\n  {gates_list}",
            f"Check gate status: python3 roadmap-query.py --sprint {sprint_id}",
            "Start gates: python3 roadmap-update.py --start-task <gate-id>",
            "Complete gates: python3 roadmap-update.py --complete-task <gate-id> --gate-passed"
        ]

        return CLIHelpFormatter.format_error_with_suggestion(
            error=error,
            suggestions=suggestions,
            hint="Completion gates enforce quality standards before marking work complete"
        )

    @staticmethod
    def production_gate_not_passed(
        sprint_id: str,
        incomplete_gates: List[str]
    ) -> str:
        """Error when trying to mark production-ready without passing production gates."""
        gates_list = "\n  ".join(f"• {gate}" for gate in incomplete_gates)

        error = f"Cannot mark sprint '{sprint_id}' production-ready - production gates not passed"

        suggestions = [
            "Complete all production gates before deploying to production",
            f"Incomplete gates:\n  {gates_list}",
            f"Check gate status: python3 roadmap-query.py --sprint {sprint_id}",
            "Run gate validation: python3 roadmap-update.py --run-gate <gate-id>",
        ]

        return CLIHelpFormatter.format_error_with_suggestion(
            error=error,
            suggestions=suggestions,
            hint="Production gates protect against deploying untested or insecure code"
        )

    @staticmethod
    def invalid_id_format(
        provided_id: str,
        object_type: str,
        expected_format: str,
        example: str
    ) -> str:
        """Error when ID format is invalid."""
        return CLIHelpFormatter.format_validation_error(
            field=f"{object_type}_id",
            value=provided_id,
            expected=expected_format,
            context=f"Example: {example}"
        )

    @staticmethod
    def missing_required_field(
        field_name: str,
        object_type: str,
        context: Optional[str] = None
    ) -> str:
        """Error when required field is missing."""
        error = f"Missing required field: {field_name}"

        suggestions = [
            f"Provide --{field_name.replace('_', '-')} when creating {object_type}",
            f"Check command help: python3 roadmap-<command>.py --help",
        ]

        if context:
            suggestions.append(f"Context: {context}")

        return CLIHelpFormatter.format_error_with_suggestion(
            error=error,
            suggestions=suggestions,
            hint=f"All {object_type}s require {field_name} to be specified"
        )

    @staticmethod
    def file_not_found(file_path: str, file_type: str) -> str:
        """Error when expected file not found."""
        error = f"{file_type} file not found: {file_path}"

        suggestions = [
            "Check the file path is correct",
            "Ensure the roadmap was initialized properly",
            "Try refreshing: python3 roadmap-update.py --refresh-progress"
        ]

        return CLIHelpFormatter.format_error_with_suggestion(
            error=error,
            suggestions=suggestions,
            hint="Files may be missing if initialization was incomplete"
        )

    @staticmethod
    def circular_dependency(
        object_id: str,
        dependency_chain: List[str]
    ) -> str:
        """Error when circular dependency detected."""
        chain = " → ".join(dependency_chain)

        error = f"Circular dependency detected involving {object_id}"

        suggestions = [
            f"Dependency chain: {chain}",
            "Remove one of the dependencies to break the cycle",
            "Review your dependency graph: python3 roadmap-query.py --dependencies",
        ]

        return CLIHelpFormatter.format_error_with_suggestion(
            error=error,
            suggestions=suggestions,
            hint="Circular dependencies prevent progress and must be resolved"
        )

    @staticmethod
    def no_tasks_ready(sprint_id: str, blocked_count: int) -> str:
        """Warning when no tasks are ready to work on."""
        error = f"No tasks ready to start in sprint '{sprint_id}'"

        suggestions = [
            f"{blocked_count} task(s) are blocked by dependencies",
            f"Check blockers: python3 roadmap-query.py --blockers --id {sprint_id}",
            "Complete prerequisite tasks to unblock",
            "View dependency graph: python3 roadmap-query.py --dependencies --sprint {sprint_id}"
        ]

        return CLIHelpFormatter.format_error_with_suggestion(
            error=error,
            suggestions=suggestions,
            hint="Tasks become ready when their dependencies are satisfied"
        )

    @staticmethod
    def validation_failed(
        object_type: str,
        object_id: str,
        errors: List[str]
    ) -> str:
        """Error when object validation fails."""
        errors_list = "\n  ".join(f"• {err}" for err in errors)

        error = f"Validation failed for {object_type} '{object_id}'"

        suggestions = [
            f"Errors found:\n  {errors_list}",
            f"Check schema: framework/roadmap/schema/{object_type}.schema.yaml",
            "Fix validation errors and try again"
        ]

        return CLIHelpFormatter.format_error_with_suggestion(
            error=error,
            suggestions=suggestions,
            hint="All roadmap objects must pass validation to maintain data integrity"
        )

    @staticmethod
    def concurrent_modification(
        object_id: str,
        expected_version: str,
        actual_version: str
    ) -> str:
        """Error when concurrent modification detected."""
        error = f"Concurrent modification detected for {object_id}"

        suggestions = [
            f"Expected version: {expected_version}",
            f"Actual version: {actual_version}",
            "Reload the object and retry your operation",
            f"Query current state: python3 roadmap-query.py --id {object_id}"
        ]

        return CLIHelpFormatter.format_error_with_suggestion(
            error=error,
            suggestions=suggestions,
            hint="Another process modified this object - reload and retry"
        )


class WarningMessages:
    """Centralized warning message templates."""

    @staticmethod
    def deprecated_command(old_command: str, new_command: str) -> str:
        """Warning for deprecated commands."""
        from formatting import warning, info

        return (
            f"{warning(f'Command {old_command} is deprecated')}\n"
            f"{info(f'Use {new_command} instead')}\n"
            f"The old command will be removed in a future version.\n"
        )

    @staticmethod
    def large_context_warning(size_kb: float, threshold_kb: float = 200) -> str:
        """Warning when context size is large."""
        from formatting import warning

        if size_kb <= threshold_kb:
            return ""

        return (
            f"{warning(f'Large context size: {size_kb:.1f} KB')}\n"
            f"This may exceed Claude's context window (200KB).\n"
            f"Consider using --max-distance to reduce context size.\n"
        )

    @staticmethod
    def stale_cache_warning(last_updated: str) -> str:
        """Warning when cache is stale."""
        from formatting import warning

        return (
            f"{warning('Cache may be stale')}\n"
            f"Last updated: {last_updated}\n"
            f"Run --refresh-progress to update all cached values.\n"
        )


class SuccessMessages:
    """Centralized success message templates."""

    @staticmethod
    def task_completed(task_id: str, task_title: str, unblocked: List[str]) -> str:
        """Success message for task completion."""
        from formatting import success, info

        lines = [
            success(f"Task completed: {task_title}"),
            ""
        ]

        if unblocked:
            lines.append(info(f"Unblocked {len(unblocked)} task(s):"))
            for task in unblocked:
                lines.append(f"  ✓ {task}")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def sprint_completed(sprint_id: str, sprint_name: str, stats: Dict[str, any]) -> str:
        """Success message for sprint completion."""
        from formatting import success, info, bold

        lines = [
            success(f"Sprint completed: {sprint_name}"),
            "",
            bold("Statistics:"),
            f"  Tasks completed: {stats.get('tasks_completed', 0)}",
            f"  Duration: {stats.get('duration', 'N/A')}",
            f"  Completion gates: {stats.get('completion_gates_passed', 0)} passed",
            ""
        ]

        if stats.get('production_gates_total', 0) > 0:
            lines.append(info("Note: Production gates not run yet"))
            lines.append("Run production gates before deploying to production:")
            lines.append(f"  python3 roadmap-update.py --run-production-gates {sprint_id}")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def initialization_success(roadmap_id: str, roadmap_dir: str) -> str:
        """Success message for roadmap initialization."""
        from formatting import success, info, bold

        lines = [
            success(f"Roadmap initialized: {roadmap_id}"),
            "",
            bold("Created:"),
            f"  ✓ Roadmap file: {roadmap_dir}/roadmap.yaml",
            f"  ✓ Tracks directory: {roadmap_dir}/tracks/",
            f"  ✓ Sprints directory: {roadmap_dir}/sprints/",
            f"  ✓ Tasks directory: {roadmap_dir}/tasks/",
            "",
            bold("Next steps:"),
            "  1. Create tracks: python3 roadmap-track.py create --id <track-id> --name '<Name>'",
            "  2. Plan sprints: python3 roadmap-sprint.py create --id <sprint-id> --track <track-id> --name '<Name>'",
            "  3. Add tasks: python3 roadmap-task.py create --sprint <sprint-id> --id <task-id> --title '<Title>'",
            "",
            info("See docs/guides/ROADMAP_TUTORIAL.md for a complete walkthrough"),
            ""
        ]

        return "\n".join(lines)
