"""
PostMortemGenerator - Task retrospective generation for the implementation loop.

This module provides automatic post-mortem generation for completed tasks,
capturing accomplishments, lessons learned, and metrics for continuous
improvement.

Key Features:
- PostMortem dataclass for capturing task retrospective data
- PostMortemGenerator class for generating and saving post-mortems
- Markdown generation for human-readable output
- Sprint-level learning aggregation

Usage:
    from vibey.services.implementation import (
        PostMortem,
        PostMortemGenerator,
    )
    from pathlib import Path
    from datetime import datetime, timedelta, timezone

    # Initialize generator
    generator = PostMortemGenerator(roadmap_root=Path(".vibey/roadmap"))

    # Generate a post-mortem
    post_mortem = generator.generate(task, result, context)

    # Save to context directory
    generator.save(task, post_mortem)

    # Aggregate learnings from a sprint
    learnings = generator.aggregate_sprint_learnings("sprint-1")

Design Reference:
- Implementation Mode Track Sprint 3
- Context System v2 Integration
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# POST-MORTEM DATACLASS
# =============================================================================


@dataclass
class PostMortem:
    """
    Complete post-mortem data for a task retrospective.

    Captures all relevant information about task completion including
    timing, resource usage, accomplishments, and lessons learned.

    Attributes:
        task_id: ULID of the completed task
        completed_at: When the task was completed
        duration: How long the task took to complete
        tokens_used: Total tokens consumed (input + output)

        accomplishments: What was achieved during the task
        what_worked: Approaches or techniques that worked well
        what_didnt_work: Approaches that failed or caused issues
        discoveries: Unexpected findings during implementation
        lessons_learned: Key takeaways for future work

        estimated_tokens: Original token estimate (if available)
        actual_tokens: Actual tokens consumed
        token_efficiency: Ratio of estimated to actual tokens

        files_modified: Files that were changed during implementation
        commits: Git commit SHAs created during the task
        bugs_logged: Bug ticket IDs created during the task

    Example:
        >>> post_mortem = PostMortem(
        ...     task_id="01KCZF73PX9YNKWXKYVARY89N3",
        ...     completed_at=datetime.now(timezone.utc),
        ...     duration=timedelta(minutes=15),
        ...     tokens_used=2500,
        ...     accomplishments=["Implemented new feature", "Added tests"],
        ...     what_worked=["Incremental approach worked well"],
        ...     what_didnt_work=["Initial design was too complex"],
        ...     discoveries=["Found related bug in module X"],
        ...     lessons_learned=["Start simple, iterate"],
        ... )
        >>> print(post_mortem.to_markdown())
    """

    # Required fields
    task_id: str
    completed_at: datetime
    duration: timedelta
    tokens_used: int

    # Retrospective sections
    accomplishments: List[str] = field(default_factory=list)
    what_worked: List[str] = field(default_factory=list)
    what_didnt_work: List[str] = field(default_factory=list)
    discoveries: List[str] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)

    # Token metrics
    estimated_tokens: Optional[int] = None
    actual_tokens: Optional[int] = None
    token_efficiency: Optional[float] = None

    # Artifacts
    files_modified: List[Path] = field(default_factory=list)
    commits: List[str] = field(default_factory=list)
    bugs_logged: List[str] = field(default_factory=list)

    # =========================================================================
    # COMPUTED PROPERTIES
    # =========================================================================

    @property
    def duration_formatted(self) -> str:
        """
        Format duration as human-readable string.

        Returns:
            Duration string like "2h 15m" or "45m 30s"
        """
        total_seconds = int(self.duration.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 and hours == 0:  # Only show seconds if under an hour
            parts.append(f"{seconds}s")

        return " ".join(parts) if parts else "0s"

    @property
    def efficiency_rating(self) -> str:
        """
        Get efficiency rating based on token usage.

        Returns:
            Rating string: "excellent", "good", "fair", or "poor"
        """
        if self.token_efficiency is None:
            return "unknown"

        if self.token_efficiency >= 1.0:
            return "excellent"  # Under or at budget
        elif self.token_efficiency >= 0.8:
            return "good"  # Within 20% over budget
        elif self.token_efficiency >= 0.5:
            return "fair"  # Within 50% over budget
        else:
            return "poor"  # Significantly over budget

    # =========================================================================
    # SERIALIZATION
    # =========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize for logging/storage.

        Returns:
            Dictionary representation of the post-mortem.
        """
        return {
            "task_id": self.task_id,
            "completed_at": self.completed_at.isoformat(),
            "duration_seconds": self.duration.total_seconds(),
            "duration_formatted": self.duration_formatted,
            "tokens_used": self.tokens_used,
            "retrospective": {
                "accomplishments": self.accomplishments,
                "what_worked": self.what_worked,
                "what_didnt_work": self.what_didnt_work,
                "discoveries": self.discoveries,
                "lessons_learned": self.lessons_learned,
            },
            "token_metrics": {
                "estimated_tokens": self.estimated_tokens,
                "actual_tokens": self.actual_tokens,
                "token_efficiency": self.token_efficiency,
                "efficiency_rating": self.efficiency_rating,
            },
            "artifacts": {
                "files_modified": [str(p) for p in self.files_modified],
                "commits": self.commits,
                "bugs_logged": self.bugs_logged,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PostMortem":
        """
        Deserialize from dictionary.

        Args:
            data: Dictionary representation of a PostMortem.

        Returns:
            PostMortem instance.
        """
        # Parse timestamps
        completed_at = data.get("completed_at")
        if isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
        elif completed_at is None:
            completed_at = datetime.now(timezone.utc)

        # Parse duration
        duration_seconds = data.get("duration_seconds", 0)
        duration = timedelta(seconds=duration_seconds)

        # Parse retrospective sections
        retrospective = data.get("retrospective", {})
        accomplishments = retrospective.get(
            "accomplishments", data.get("accomplishments", [])
        )
        what_worked = retrospective.get("what_worked", data.get("what_worked", []))
        what_didnt_work = retrospective.get(
            "what_didnt_work", data.get("what_didnt_work", [])
        )
        discoveries = retrospective.get("discoveries", data.get("discoveries", []))
        lessons_learned = retrospective.get(
            "lessons_learned", data.get("lessons_learned", [])
        )

        # Parse token metrics
        token_metrics = data.get("token_metrics", {})
        estimated_tokens = token_metrics.get(
            "estimated_tokens", data.get("estimated_tokens")
        )
        actual_tokens = token_metrics.get("actual_tokens", data.get("actual_tokens"))
        token_efficiency = token_metrics.get(
            "token_efficiency", data.get("token_efficiency")
        )

        # Parse artifacts
        artifacts = data.get("artifacts", {})
        files_modified_raw = artifacts.get(
            "files_modified", data.get("files_modified", [])
        )
        files_modified = [Path(p) for p in files_modified_raw]
        commits = artifacts.get("commits", data.get("commits", []))
        bugs_logged = artifacts.get("bugs_logged", data.get("bugs_logged", []))

        return cls(
            task_id=data.get("task_id", ""),
            completed_at=completed_at,
            duration=duration,
            tokens_used=data.get("tokens_used", 0),
            accomplishments=accomplishments,
            what_worked=what_worked,
            what_didnt_work=what_didnt_work,
            discoveries=discoveries,
            lessons_learned=lessons_learned,
            estimated_tokens=estimated_tokens,
            actual_tokens=actual_tokens,
            token_efficiency=token_efficiency,
            files_modified=files_modified,
            commits=commits,
            bugs_logged=bugs_logged,
        )

    def to_markdown(self) -> str:
        """
        Generate markdown representation of the post-mortem.

        Returns:
            Formatted markdown string for the post-mortem document.
        """
        parts = []

        # Header
        parts.append("# Task Post-Mortem")
        parts.append("")
        parts.append(f"**Task ID:** `{self.task_id}`")
        parts.append(f"**Completed:** {self.completed_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        parts.append(f"**Duration:** {self.duration_formatted}")
        parts.append(f"**Tokens Used:** {self.tokens_used:,}")
        parts.append("")

        # Token efficiency section
        if self.estimated_tokens is not None or self.actual_tokens is not None:
            parts.append("## Token Metrics")
            parts.append("")
            if self.estimated_tokens is not None:
                parts.append(f"- **Estimated Tokens:** {self.estimated_tokens:,}")
            if self.actual_tokens is not None:
                parts.append(f"- **Actual Tokens:** {self.actual_tokens:,}")
            if self.token_efficiency is not None:
                efficiency_pct = self.token_efficiency * 100
                parts.append(
                    f"- **Token Efficiency:** {efficiency_pct:.1f}% ({self.efficiency_rating})"
                )
            parts.append("")

        # Accomplishments
        parts.append("## Accomplishments")
        parts.append("")
        if self.accomplishments:
            for item in self.accomplishments:
                parts.append(f"- {item}")
        else:
            parts.append("_No accomplishments recorded._")
        parts.append("")

        # What Worked Well
        parts.append("## What Worked Well")
        parts.append("")
        if self.what_worked:
            for item in self.what_worked:
                parts.append(f"- {item}")
        else:
            parts.append("_No insights recorded._")
        parts.append("")

        # What Didn't Work
        parts.append("## What Didn't Work")
        parts.append("")
        if self.what_didnt_work:
            for item in self.what_didnt_work:
                parts.append(f"- {item}")
        else:
            parts.append("_No issues recorded._")
        parts.append("")

        # Discoveries
        parts.append("## Discoveries")
        parts.append("")
        if self.discoveries:
            for item in self.discoveries:
                parts.append(f"- {item}")
        else:
            parts.append("_No discoveries recorded._")
        parts.append("")

        # Lessons Learned
        parts.append("## Lessons Learned")
        parts.append("")
        if self.lessons_learned:
            for item in self.lessons_learned:
                parts.append(f"- {item}")
        else:
            parts.append("_No lessons recorded._")
        parts.append("")

        # Artifacts section
        parts.append("## Artifacts")
        parts.append("")

        # Files Modified
        parts.append("### Files Modified")
        parts.append("")
        if self.files_modified:
            for file_path in self.files_modified:
                parts.append(f"- `{file_path}`")
        else:
            parts.append("_No files modified._")
        parts.append("")

        # Commits
        parts.append("### Commits")
        parts.append("")
        if self.commits:
            for commit in self.commits:
                parts.append(f"- `{commit}`")
        else:
            parts.append("_No commits recorded._")
        parts.append("")

        # Bugs Logged
        parts.append("### Bugs Logged")
        parts.append("")
        if self.bugs_logged:
            for bug_id in self.bugs_logged:
                parts.append(f"- `{bug_id}`")
        else:
            parts.append("_No bugs logged._")
        parts.append("")

        return "\n".join(parts)


# =============================================================================
# POST-MORTEM GENERATOR
# =============================================================================


class PostMortemGenerator:
    """
    Generate and manage task post-mortems.

    Creates post-mortem analyses for completed tasks, saves them to the
    context directory, and aggregates learnings across sprints.

    Attributes:
        roadmap_root: Path to the roadmap directory

    Example:
        >>> generator = PostMortemGenerator(Path(".vibey/roadmap"))
        >>> post_mortem = generator.generate(task, result, context)
        >>> generator.save(task, post_mortem)
        >>> learnings = generator.aggregate_sprint_learnings("sprint-1")
    """

    def __init__(self, roadmap_root: Path):
        """
        Initialize PostMortemGenerator.

        Args:
            roadmap_root: Path to .vibey/roadmap directory
        """
        self.roadmap_root = Path(roadmap_root)
        logger.debug(f"PostMortemGenerator initialized with root: {roadmap_root}")

    def generate(
        self,
        task: Any,  # HierarchicalTicket
        result: Any,  # ExecutionResult
        context: Optional[Any] = None,  # TaskContext
    ) -> PostMortem:
        """
        Generate a post-mortem analysis for a completed task.

        Extracts information from the task, execution result, and context
        to create a comprehensive post-mortem.

        Args:
            task: The completed HierarchicalTicket
            result: The ExecutionResult from task execution
            context: Optional TaskContext with additional information

        Returns:
            PostMortem instance with generated analysis
        """
        # Extract task ID
        task_id = getattr(task, "id", str(task))

        # Get timing information
        completed_at = getattr(result, "completed_at", datetime.now(timezone.utc))
        started_at = getattr(result, "started_at", completed_at)
        duration = completed_at - started_at

        # Get token usage
        tokens_input = getattr(result, "tokens_input", 0)
        tokens_output = getattr(result, "tokens_output", 0)
        tokens_used = tokens_input + tokens_output

        # Get artifacts
        files_modified = list(getattr(result, "files_modified", []))
        files_created = list(getattr(result, "files_created", []))
        all_files = files_modified + files_created
        commits = list(getattr(result, "commits", []))

        # Get estimated tokens from task or context
        estimated_tokens = None
        if hasattr(task, "total_token_budget") and task.total_token_budget:
            estimated_tokens = task.total_token_budget
        elif context and hasattr(context, "max_tokens") and context.max_tokens:
            estimated_tokens = context.max_tokens

        # Calculate token efficiency
        actual_tokens = tokens_used
        token_efficiency = None
        if estimated_tokens and estimated_tokens > 0 and actual_tokens:
            token_efficiency = estimated_tokens / actual_tokens

        # Generate accomplishments based on result
        accomplishments = self._generate_accomplishments(task, result, all_files)

        # Generate what worked/didn't work based on result status
        what_worked, what_didnt_work = self._analyze_execution(task, result)

        # Generate discoveries (empty for now, can be enhanced)
        discoveries = []

        # Generate lessons learned
        lessons_learned = self._generate_lessons(task, result, token_efficiency)

        # Get bug IDs if available from context
        bugs_logged = []
        if context and hasattr(context, "bugs_logged"):
            bugs_logged = list(context.bugs_logged)

        return PostMortem(
            task_id=task_id,
            completed_at=completed_at,
            duration=duration,
            tokens_used=tokens_used,
            accomplishments=accomplishments,
            what_worked=what_worked,
            what_didnt_work=what_didnt_work,
            discoveries=discoveries,
            lessons_learned=lessons_learned,
            estimated_tokens=estimated_tokens,
            actual_tokens=actual_tokens,
            token_efficiency=token_efficiency,
            files_modified=[Path(f) for f in all_files],
            commits=commits,
            bugs_logged=bugs_logged,
        )

    def save(self, task: Any, post_mortem: PostMortem) -> Path:
        """
        Save post-mortem to the context directory.

        Saves the post-mortem as a markdown file in the task's context
        directory.

        Args:
            task: The task the post-mortem is for
            post_mortem: The PostMortem to save

        Returns:
            Path to the saved post-mortem file
        """
        post_mortem_path = self.get_post_mortem_path(task)

        # Create directory if needed
        post_mortem_path.parent.mkdir(parents=True, exist_ok=True)

        # Write markdown content
        content = post_mortem.to_markdown()
        post_mortem_path.write_text(content, encoding="utf-8")

        logger.info(f"Saved post-mortem to {post_mortem_path}")
        return post_mortem_path

    def get_post_mortem_path(self, task: Any) -> Path:
        """
        Get the path for a task's post-mortem file.

        Path format: .vibey/roadmap/context/sprints/{sprint}/tasks/{task}/POST_MORTEM.md

        Args:
            task: The task to get the path for

        Returns:
            Path to the post-mortem file
        """
        task_id = getattr(task, "id", str(task))

        # Get sprint reference from task
        sprint_id = None
        if hasattr(task, "parent_ref") and task.parent_ref:
            sprint_id = task.parent_ref
        elif hasattr(task, "sprint_id") and task.sprint_id:
            sprint_id = task.sprint_id

        # If no sprint found, use a default directory
        if sprint_id:
            return (
                self.roadmap_root
                / "context"
                / "sprints"
                / sprint_id
                / "tasks"
                / task_id
                / "POST_MORTEM.md"
            )
        else:
            # Fallback to tasks directory
            return (
                self.roadmap_root
                / "context"
                / "tasks"
                / task_id
                / "POST_MORTEM.md"
            )

    def aggregate_sprint_learnings(self, sprint_id: str) -> Dict[str, Any]:
        """
        Aggregate learnings from all tasks in a sprint.

        Reads all post-mortems from the sprint's tasks and aggregates
        the lessons learned, what worked, and what didn't.

        Args:
            sprint_id: The sprint ID or slug to aggregate

        Returns:
            Dictionary with aggregated learnings:
            - total_tasks: Number of tasks with post-mortems
            - total_duration: Combined duration of all tasks
            - total_tokens: Combined token usage
            - all_accomplishments: All accomplishments across tasks
            - all_what_worked: All things that worked well
            - all_what_didnt_work: All issues encountered
            - all_discoveries: All discoveries made
            - all_lessons_learned: All lessons learned
            - files_modified: All unique files modified
            - total_commits: Total commits made
            - bugs_logged: All bugs logged
        """
        sprint_context_path = self.roadmap_root / "context" / "sprints" / sprint_id

        # Initialize aggregation
        aggregation: Dict[str, Any] = {
            "sprint_id": sprint_id,
            "total_tasks": 0,
            "total_duration_seconds": 0,
            "total_tokens": 0,
            "all_accomplishments": [],
            "all_what_worked": [],
            "all_what_didnt_work": [],
            "all_discoveries": [],
            "all_lessons_learned": [],
            "files_modified": set(),
            "total_commits": 0,
            "bugs_logged": [],
            "token_efficiency_avg": None,
        }

        if not sprint_context_path.exists():
            logger.warning(f"Sprint context path does not exist: {sprint_context_path}")
            return aggregation

        # Find all POST_MORTEM.md files in the sprint
        tasks_path = sprint_context_path / "tasks"
        if not tasks_path.exists():
            logger.debug(f"No tasks directory for sprint: {sprint_id}")
            return aggregation

        efficiencies = []

        for task_dir in tasks_path.iterdir():
            if not task_dir.is_dir():
                continue

            post_mortem_file = task_dir / "POST_MORTEM.md"
            if not post_mortem_file.exists():
                continue

            try:
                # Parse the post-mortem markdown
                content = post_mortem_file.read_text(encoding="utf-8")
                parsed = self._parse_post_mortem_markdown(content)

                aggregation["total_tasks"] += 1
                aggregation["total_duration_seconds"] += parsed.get(
                    "duration_seconds", 0
                )
                aggregation["total_tokens"] += parsed.get("tokens_used", 0)

                aggregation["all_accomplishments"].extend(
                    parsed.get("accomplishments", [])
                )
                aggregation["all_what_worked"].extend(parsed.get("what_worked", []))
                aggregation["all_what_didnt_work"].extend(
                    parsed.get("what_didnt_work", [])
                )
                aggregation["all_discoveries"].extend(parsed.get("discoveries", []))
                aggregation["all_lessons_learned"].extend(
                    parsed.get("lessons_learned", [])
                )

                for f in parsed.get("files_modified", []):
                    aggregation["files_modified"].add(f)

                aggregation["total_commits"] += len(parsed.get("commits", []))
                aggregation["bugs_logged"].extend(parsed.get("bugs_logged", []))

                if parsed.get("token_efficiency") is not None:
                    efficiencies.append(parsed["token_efficiency"])

            except Exception as e:
                logger.warning(
                    f"Failed to parse post-mortem at {post_mortem_file}: {e}"
                )

        # Convert set to list for JSON serialization
        aggregation["files_modified"] = list(aggregation["files_modified"])

        # Calculate average efficiency
        if efficiencies:
            aggregation["token_efficiency_avg"] = sum(efficiencies) / len(efficiencies)

        return aggregation

    # =========================================================================
    # PRIVATE HELPER METHODS
    # =========================================================================

    def _generate_accomplishments(
        self,
        task: Any,
        result: Any,
        files: List[Any],
    ) -> List[str]:
        """Generate accomplishments based on task result."""
        accomplishments = []

        # Check if task was successful
        status = getattr(result, "status", None)
        if status and hasattr(status, "value"):
            status_value = status.value
        else:
            status_value = str(status) if status else "unknown"

        if status_value == "success":
            task_name = getattr(task, "name", "Task")
            accomplishments.append(f"Completed: {task_name}")

        # Add file-based accomplishments
        if files:
            accomplishments.append(f"Modified {len(files)} file(s)")

        # Add commit-based accomplishments
        commits = getattr(result, "commits", [])
        if commits:
            accomplishments.append(f"Created {len(commits)} commit(s)")

        return accomplishments

    def _analyze_execution(
        self,
        task: Any,
        result: Any,
    ) -> tuple[List[str], List[str]]:
        """Analyze execution to determine what worked and what didn't."""
        what_worked = []
        what_didnt_work = []

        # Check execution status
        status = getattr(result, "status", None)
        if status and hasattr(status, "value"):
            status_value = status.value
        else:
            status_value = str(status) if status else "unknown"

        if status_value == "success":
            what_worked.append("Task completed successfully")
        elif status_value == "failure":
            error_msg = getattr(result, "error_message", "Unknown error")
            what_didnt_work.append(f"Task failed: {error_msg}")
        elif status_value == "timeout":
            what_didnt_work.append("Task exceeded time limit")
        elif status_value == "blocked":
            what_didnt_work.append("Task was blocked by dependencies")

        return what_worked, what_didnt_work

    def _generate_lessons(
        self,
        task: Any,
        result: Any,
        token_efficiency: Optional[float],
    ) -> List[str]:
        """Generate lessons learned based on execution."""
        lessons = []

        # Token efficiency lessons
        if token_efficiency is not None:
            if token_efficiency < 0.5:
                lessons.append(
                    "Task took significantly more tokens than estimated - "
                    "consider breaking into smaller tasks"
                )
            elif token_efficiency > 1.2:
                lessons.append(
                    "Task used fewer tokens than estimated - "
                    "estimates may be too conservative"
                )

        # Status-based lessons
        status = getattr(result, "status", None)
        if status and hasattr(status, "value"):
            status_value = status.value
        else:
            status_value = str(status) if status else "unknown"

        if status_value == "timeout":
            lessons.append(
                "Task timed out - may need to increase timeout or simplify scope"
            )
        elif status_value == "blocked":
            lessons.append(
                "Task was blocked - ensure dependencies are clearly documented"
            )

        return lessons

    def _parse_post_mortem_markdown(self, content: str) -> Dict[str, Any]:
        """
        Parse post-mortem markdown to extract data.

        This is a simple parser that extracts key sections.
        """
        import re

        result: Dict[str, Any] = {
            "tokens_used": 0,
            "duration_seconds": 0,
            "accomplishments": [],
            "what_worked": [],
            "what_didnt_work": [],
            "discoveries": [],
            "lessons_learned": [],
            "files_modified": [],
            "commits": [],
            "bugs_logged": [],
            "token_efficiency": None,
        }

        # Extract tokens used
        tokens_match = re.search(r"\*\*Tokens Used:\*\*\s*([\d,]+)", content)
        if tokens_match:
            result["tokens_used"] = int(tokens_match.group(1).replace(",", ""))

        # Extract duration
        duration_match = re.search(r"\*\*Duration:\*\*\s*(.+)", content)
        if duration_match:
            duration_str = duration_match.group(1).strip()
            result["duration_seconds"] = self._parse_duration(duration_str)

        # Extract token efficiency
        efficiency_match = re.search(
            r"\*\*Token Efficiency:\*\*\s*([\d.]+)%", content
        )
        if efficiency_match:
            result["token_efficiency"] = float(efficiency_match.group(1)) / 100

        # Extract list sections
        section_patterns = {
            "accomplishments": r"## Accomplishments\n\n((?:- .+\n)*)",
            "what_worked": r"## What Worked Well\n\n((?:- .+\n)*)",
            "what_didnt_work": r"## What Didn't Work\n\n((?:- .+\n)*)",
            "discoveries": r"## Discoveries\n\n((?:- .+\n)*)",
            "lessons_learned": r"## Lessons Learned\n\n((?:- .+\n)*)",
            "files_modified": r"### Files Modified\n\n((?:- .+\n)*)",
            "commits": r"### Commits\n\n((?:- .+\n)*)",
            "bugs_logged": r"### Bugs Logged\n\n((?:- .+\n)*)",
        }

        for key, pattern in section_patterns.items():
            match = re.search(pattern, content)
            if match:
                items_text = match.group(1)
                items = [
                    line[2:].strip()
                    for line in items_text.split("\n")
                    if line.startswith("- ") and not line.startswith("- _")
                ]
                # Remove backticks from items
                items = [item.strip("`") for item in items]
                result[key] = items

        return result

    def _parse_duration(self, duration_str: str) -> int:
        """Parse duration string to seconds."""
        import re

        total_seconds = 0

        hours_match = re.search(r"(\d+)h", duration_str)
        if hours_match:
            total_seconds += int(hours_match.group(1)) * 3600

        minutes_match = re.search(r"(\d+)m", duration_str)
        if minutes_match:
            total_seconds += int(minutes_match.group(1)) * 60

        seconds_match = re.search(r"(\d+)s", duration_str)
        if seconds_match:
            total_seconds += int(seconds_match.group(1))

        return total_seconds


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "PostMortem",
    "PostMortemGenerator",
]
