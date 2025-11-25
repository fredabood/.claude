"""
YAML Change Analyzer for CLI Usage Validation

Detects manual YAML edits and suggests appropriate CLI commands instead.

Task: git-integration-4-task-003
"""

import subprocess
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class YAMLChange:
    """Represents a detected change in a YAML file."""
    file_path: str
    file_type: str  # "task", "sprint", "track"
    item_id: str
    field_name: str
    old_value: Optional[str]
    new_value: Optional[str]
    line_number: Optional[int] = None

    @property
    def is_status_change(self) -> bool:
        """Check if this is a status-related change."""
        return self.field_name in ("status", "completed", "started")

    @property
    def is_progress_change(self) -> bool:
        """Check if this is a progress-related change."""
        return self.field_name in (
            "completion_percent", "tasks_completed", "tasks_total",
            "sprints_completed", "sprints_total"
        )


@dataclass
class CLISuggestion:
    """A suggested CLI command to use instead of manual editing."""
    command: str
    description: str
    priority: str = "medium"  # "high", "medium", "low"

    def format(self, show_description: bool = True) -> str:
        """Format the suggestion for display."""
        if show_description:
            return f"  {self.command}\n    ({self.description})"
        return f"  {self.command}"


@dataclass
class AnalysisResult:
    """Result of analyzing YAML changes."""
    file_path: str
    file_type: str
    item_id: str
    changes: List[YAMLChange] = field(default_factory=list)
    suggestions: List[CLISuggestion] = field(default_factory=list)
    should_block: bool = False

    def format_summary(self) -> str:
        """Format a summary of changes for display."""
        if not self.changes:
            return ""

        lines = [f"Manual YAML edit detected: {self.file_path}"]

        # Group changes by type
        field_names = [c.field_name for c in self.changes]
        lines.append(f"  Modified: {', '.join(set(field_names))}")

        return "\n".join(lines)


class YAMLChangeAnalyzer:
    """
    Analyzes YAML file changes from git diff and generates CLI suggestions.

    This class parses git diffs of roadmap YAML files, identifies what
    fields were changed, and suggests appropriate CLI commands to achieve
    the same result in a more traceable way.
    """

    # Patterns for extracting field changes from diff
    FIELD_CHANGE_PATTERN = re.compile(r'^[-+]\s*(\w+):\s*(.*)$')

    # Mapping of file types to their identifying suffix
    FILE_TYPE_MAP = {
        "task.yaml": "task",
        "sprint.yaml": "sprint",
        "track.yaml": "track",
    }

    def __init__(self, repo_path: str = "."):
        """
        Initialize the analyzer.

        Args:
            repo_path: Path to git repository root
        """
        self.repo_path = Path(repo_path).resolve()

    def _run_git(self, *args: str) -> subprocess.CompletedProcess:
        """Run a git command."""
        cmd = ["git", "-C", str(self.repo_path)] + list(args)
        return subprocess.run(cmd, capture_output=True, text=True)

    def _get_staged_roadmap_files(self) -> List[str]:
        """Get list of staged roadmap YAML files."""
        result = self._run_git("diff", "--cached", "--name-only", "--diff-filter=ACM")
        if result.returncode != 0:
            return []

        files = [f for f in result.stdout.strip().split("\n") if f]

        # Filter for roadmap YAML files
        return [
            f for f in files
            if f.startswith(".vibey/roadmap/") and f.endswith(".yaml")
        ]

    def _get_file_type(self, file_path: str) -> Optional[str]:
        """Determine the type of roadmap file."""
        for suffix, file_type in self.FILE_TYPE_MAP.items():
            if file_path.endswith(suffix):
                return file_type
        return None

    def _extract_item_id(self, file_path: str, file_type: str) -> str:
        """Extract the item ID from file path."""
        parts = file_path.split("/")

        if file_type == "task":
            # .vibey/roadmap/track/sprint/task/task.yaml
            return parts[-2] if len(parts) >= 2 else "unknown"
        elif file_type == "sprint":
            # .vibey/roadmap/track/sprint/sprint.yaml
            return parts[-2] if len(parts) >= 2 else "unknown"
        elif file_type == "track":
            # .vibey/roadmap/track/track.yaml
            return parts[-2] if len(parts) >= 2 else "unknown"

        return "unknown"

    def _parse_diff(self, file_path: str) -> List[YAMLChange]:
        """
        Parse git diff for a file and extract field changes.

        Args:
            file_path: Path to the YAML file

        Returns:
            List of detected changes
        """
        result = self._run_git("diff", "--cached", "-U0", file_path)
        if result.returncode != 0:
            return []

        diff_lines = result.stdout.split("\n")
        file_type = self._get_file_type(file_path)
        if not file_type:
            return []

        item_id = self._extract_item_id(file_path, file_type)
        changes = []

        # Track old and new values for each field
        field_changes: Dict[str, Dict[str, str]] = {}
        current_line = 0

        for line in diff_lines:
            # Track line numbers from hunk headers
            if line.startswith("@@"):
                match = re.search(r'\+(\d+)', line)
                if match:
                    current_line = int(match.group(1))
                continue

            # Parse field changes
            if line.startswith("-") and not line.startswith("---"):
                match = self.FIELD_CHANGE_PATTERN.match(line)
                if match:
                    field_name, value = match.groups()
                    if field_name not in field_changes:
                        field_changes[field_name] = {}
                    field_changes[field_name]["old"] = value.strip()

            elif line.startswith("+") and not line.startswith("+++"):
                match = self.FIELD_CHANGE_PATTERN.match(line)
                if match:
                    field_name, value = match.groups()
                    if field_name not in field_changes:
                        field_changes[field_name] = {}
                    field_changes[field_name]["new"] = value.strip()
                    field_changes[field_name]["line"] = current_line
                current_line += 1

            elif not line.startswith("-"):
                current_line += 1

        # Convert to YAMLChange objects
        for field_name, values in field_changes.items():
            if "old" in values or "new" in values:
                changes.append(YAMLChange(
                    file_path=file_path,
                    file_type=file_type,
                    item_id=item_id,
                    field_name=field_name,
                    old_value=values.get("old"),
                    new_value=values.get("new"),
                    line_number=values.get("line"),
                ))

        return changes

    def _generate_suggestions(self, changes: List[YAMLChange]) -> List[CLISuggestion]:
        """
        Generate CLI command suggestions based on detected changes.

        Args:
            changes: List of detected YAML changes

        Returns:
            List of suggested CLI commands
        """
        if not changes:
            return []

        suggestions = []

        # Group changes by item
        item_changes: Dict[Tuple[str, str], List[YAMLChange]] = {}
        for change in changes:
            key = (change.file_type, change.item_id)
            if key not in item_changes:
                item_changes[key] = []
            item_changes[key].append(change)

        for (file_type, item_id), item_change_list in item_changes.items():
            suggestions.extend(
                self._suggest_for_item(file_type, item_id, item_change_list)
            )

        return suggestions

    def _suggest_for_item(
        self,
        file_type: str,
        item_id: str,
        changes: List[YAMLChange]
    ) -> List[CLISuggestion]:
        """Generate suggestions for a specific item's changes."""
        suggestions = []

        # Check for status changes
        status_changes = [c for c in changes if c.field_name == "status"]
        for change in status_changes:
            if change.new_value == "in_progress":
                suggestions.append(CLISuggestion(
                    command=f"vibey roadmap start {item_id}",
                    description=f"Start the {file_type} using CLI",
                    priority="high",
                ))
            elif change.new_value == "completed":
                suggestions.append(CLISuggestion(
                    command=f"vibey roadmap complete {item_id}",
                    description=f"Complete the {file_type} using CLI (includes validation)",
                    priority="high",
                ))
            elif change.new_value == "blocked":
                suggestions.append(CLISuggestion(
                    command=f"vibey roadmap update {file_type} {item_id} --blocked",
                    description=f"Mark {file_type} as blocked",
                    priority="medium",
                ))

        # Check for started/completed timestamp changes (on tasks)
        if file_type == "task":
            started_changes = [c for c in changes if c.field_name == "started"]
            if started_changes and started_changes[0].new_value:
                # Only suggest if status wasn't already changed
                if not status_changes:
                    suggestions.append(CLISuggestion(
                        command=f"vibey roadmap start {item_id}",
                        description="Start the task using CLI (auto-sets timestamp)",
                        priority="high",
                    ))

            completed_changes = [c for c in changes if c.field_name == "completed"]
            if completed_changes and completed_changes[0].new_value:
                if not status_changes:
                    suggestions.append(CLISuggestion(
                        command=f"vibey roadmap complete {item_id}",
                        description="Complete the task using CLI (includes validation)",
                        priority="high",
                    ))

        # Check for progress changes (sprints/tracks)
        progress_fields = ["completion_percent", "tasks_completed", "sprints_completed"]
        progress_changes = [c for c in changes if c.field_name in progress_fields]
        if progress_changes:
            suggestions.append(CLISuggestion(
                command=f"vibey roadmap sync {item_id}",
                description="Sync progress from child items (auto-calculates)",
                priority="medium",
            ))

        # Check for commit additions (tasks)
        if file_type == "task":
            commit_pattern = any(
                "commits" in c.field_name or c.field_name == "sha"
                for c in changes
            )
            if commit_pattern:
                suggestions.append(CLISuggestion(
                    command=f"vibey roadmap add-commit {item_id} <sha>",
                    description="Link a commit to this task using CLI",
                    priority="medium",
                ))

        # Generic fallback for other changes
        other_changes = [
            c for c in changes
            if c.field_name not in (
                "status", "started", "completed",
                "completion_percent", "tasks_completed", "sprints_completed",
                "commits", "sha"
            )
        ]
        if other_changes and not suggestions:
            # Only show generic suggestion if no specific ones
            field_list = ", ".join(set(c.field_name for c in other_changes))
            suggestions.append(CLISuggestion(
                command=f"vibey roadmap update {file_type} {item_id} ...",
                description=f"Update {file_type} fields ({field_list}) using CLI",
                priority="low",
            ))

        return suggestions

    def analyze_staged_changes(self, blocking_mode: bool = False) -> List[AnalysisResult]:
        """
        Analyze all staged roadmap YAML changes.

        Args:
            blocking_mode: If True, mark results that should block commit

        Returns:
            List of analysis results for each changed file
        """
        results = []
        staged_files = self._get_staged_roadmap_files()

        for file_path in staged_files:
            file_type = self._get_file_type(file_path)
            if not file_type:
                continue

            item_id = self._extract_item_id(file_path, file_type)
            changes = self._parse_diff(file_path)

            if not changes:
                continue

            suggestions = self._generate_suggestions(changes)

            # Determine if this should block (in blocking mode with CLI-enforced changes)
            should_block = False
            if blocking_mode:
                # Block on status changes that should use CLI
                status_changes = [c for c in changes if c.field_name == "status"]
                if status_changes:
                    should_block = True

            results.append(AnalysisResult(
                file_path=file_path,
                file_type=file_type,
                item_id=item_id,
                changes=changes,
                suggestions=suggestions,
                should_block=should_block,
            ))

        return results

    def format_analysis(self, results: List[AnalysisResult]) -> str:
        """
        Format analysis results for display.

        Args:
            results: List of analysis results

        Returns:
            Formatted string for terminal output
        """
        if not results:
            return ""

        # Terminal colors
        YELLOW = "\033[93m"
        GREEN = "\033[92m"
        BLUE = "\033[94m"
        RESET = "\033[0m"
        BOLD = "\033[1m"

        lines = []

        for result in results:
            lines.append(f"  {YELLOW}⚠{RESET} {result.format_summary()}")

            if result.suggestions:
                lines.append(f"\n  {BOLD}Suggested CLI commands:{RESET}")
                for suggestion in result.suggestions:
                    lines.append(f"    {GREEN}{suggestion.command}{RESET}")
                    lines.append(f"      {BLUE}({suggestion.description}){RESET}")

            lines.append("")

        return "\n".join(lines)


def analyze_yaml_changes(repo_path: str = ".", blocking_mode: bool = False) -> Tuple[str, bool]:
    """
    Convenience function to analyze YAML changes and format output.

    Args:
        repo_path: Path to git repository
        blocking_mode: Whether to block on CLI-required changes

    Returns:
        Tuple of (formatted output, should_block)
    """
    analyzer = YAMLChangeAnalyzer(repo_path)
    results = analyzer.analyze_staged_changes(blocking_mode=blocking_mode)

    if not results:
        return "", False

    output = analyzer.format_analysis(results)
    should_block = any(r.should_block for r in results)

    return output, should_block


if __name__ == "__main__":
    # Command-line testing
    import sys

    output, should_block = analyze_yaml_changes(blocking_mode="--blocking" in sys.argv)

    if output:
        print(output)

    sys.exit(1 if should_block else 0)
