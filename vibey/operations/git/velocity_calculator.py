"""
Sprint Velocity Calculator

Calculates sprint velocity and other metrics from Git commit history.

Task: git-integration-1-task-004
Status: In Progress
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict

from vibey.operations.git.log_analyzer import GitLogAnalyzer, CommitInfo, AnalysisResult
from vibey.operations.git.commit_parser_schema import ParserConfig, TaskStatus


@dataclass
class TaskMetrics:
    """Metrics for a single task."""
    task_id: str
    commits: int
    contributors: int
    files_changed: int
    insertions: int
    deletions: int
    first_commit_date: Optional[datetime] = None
    last_commit_date: Optional[datetime] = None
    duration_days: Optional[float] = None
    completed: bool = False

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "task_id": self.task_id,
            "commits": self.commits,
            "contributors": self.contributors,
            "files_changed": self.files_changed,
            "insertions": self.insertions,
            "deletions": self.deletions,
            "first_commit_date": self.first_commit_date.isoformat() if self.first_commit_date else None,
            "last_commit_date": self.last_commit_date.isoformat() if self.last_commit_date else None,
            "duration_days": self.duration_days,
            "completed": self.completed,
        }


@dataclass
class SprintVelocity:
    """Sprint velocity metrics."""
    sprint_id: str

    # Time period
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    duration_days: Optional[float] = None

    # Commit metrics
    total_commits: int = 0
    commits_per_day: float = 0.0

    # Task metrics
    tasks_worked: int = 0
    tasks_completed: int = 0
    completion_rate: float = 0.0

    # Contributor metrics
    total_contributors: int = 0
    avg_commits_per_contributor: float = 0.0

    # Code metrics
    total_files_changed: int = 0
    total_insertions: int = 0
    total_deletions: int = 0
    net_lines: int = 0

    # Per-task breakdown
    task_metrics: List[TaskMetrics] = field(default_factory=list)

    # Contributor breakdown
    contributor_commits: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "sprint_id": self.sprint_id,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "duration_days": self.duration_days,
            "total_commits": self.total_commits,
            "commits_per_day": self.commits_per_day,
            "tasks_worked": self.tasks_worked,
            "tasks_completed": self.tasks_completed,
            "completion_rate": self.completion_rate,
            "total_contributors": self.total_contributors,
            "avg_commits_per_contributor": self.avg_commits_per_contributor,
            "total_files_changed": self.total_files_changed,
            "total_insertions": self.total_insertions,
            "total_deletions": self.total_deletions,
            "net_lines": self.net_lines,
            "task_metrics": [t.to_dict() for t in self.task_metrics],
            "contributor_commits": self.contributor_commits,
        }


@dataclass
class VelocityTrend:
    """Velocity trend over multiple sprints."""
    sprints: List[SprintVelocity] = field(default_factory=list)

    # Trend statistics
    avg_commits_per_sprint: float = 0.0
    avg_tasks_per_sprint: float = 0.0
    avg_completion_rate: float = 0.0

    # Trend direction
    commits_trending_up: bool = False
    tasks_trending_up: bool = False
    completion_trending_up: bool = False

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "sprints": [s.to_dict() for s in self.sprints],
            "avg_commits_per_sprint": self.avg_commits_per_sprint,
            "avg_tasks_per_sprint": self.avg_tasks_per_sprint,
            "avg_completion_rate": self.avg_completion_rate,
            "commits_trending_up": self.commits_trending_up,
            "tasks_trending_up": self.tasks_trending_up,
            "completion_trending_up": self.completion_trending_up,
        }


class VelocityCalculator:
    """
    Calculate sprint velocity from Git commit history.

    Provides metrics on:
    - Commit frequency and trends
    - Task completion rates
    - Contributor activity
    - Code change volume
    """

    def __init__(
        self,
        repo_path: str = ".",
        parser_config: Optional[ParserConfig] = None
    ):
        """
        Initialize velocity calculator.

        Args:
            repo_path: Path to git repository
            parser_config: Configuration for commit parser
        """
        self.analyzer = GitLogAnalyzer(repo_path, parser_config)

    def calculate_sprint_velocity(
        self,
        sprint_id: str,
        start_ref: Optional[str] = None,
        end_ref: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> SprintVelocity:
        """
        Calculate velocity metrics for a sprint.

        Can use either:
        - Git refs (tags like sprint/<id>/start, sprint/<id>/end)
        - Date range
        - Commit message references

        Args:
            sprint_id: Sprint identifier
            start_ref: Starting ref (tag or commit SHA)
            end_ref: Ending ref (tag or commit SHA)
            start_date: Starting date (e.g., "2024-01-01")
            end_date: Ending date

        Returns:
            SprintVelocity with metrics
        """
        velocity = SprintVelocity(sprint_id=sprint_id)

        # Get commits for sprint
        if start_ref and end_ref:
            # Use ref range
            commits = self.analyzer.get_commits(ref_range=f"{start_ref}..{end_ref}")
        elif start_date and end_date:
            # Use date range
            commits = self.analyzer.get_commits(since=start_date, until=end_date)
        else:
            # Search by sprint reference in commits
            commits = self.analyzer.find_commits_for_sprint(sprint_id)

        if not commits:
            return velocity

        # Parse commits
        for commit in commits:
            if not commit.parsed:
                commit.parsed = self.analyzer.parser.parse(commit.message, commit.sha)

        # Time period
        velocity.start_date = min(c.date for c in commits)
        velocity.end_date = max(c.date for c in commits)
        velocity.duration_days = (velocity.end_date - velocity.start_date).days + 1

        # Commit metrics
        velocity.total_commits = len(commits)
        if velocity.duration_days > 0:
            velocity.commits_per_day = velocity.total_commits / velocity.duration_days

        # Collect task information
        task_commits: Dict[str, List[CommitInfo]] = defaultdict(list)
        for commit in commits:
            for task_ref in commit.parsed.tasks:
                task_commits[task_ref.task_id].append(commit)

        velocity.tasks_worked = len(task_commits)

        # Calculate per-task metrics
        for task_id, task_commit_list in task_commits.items():
            task_commit_list.sort(key=lambda c: c.date)

            # Check if task was marked completed
            completed = False
            for commit in task_commit_list:
                for task_ref in commit.parsed.tasks:
                    if task_ref.task_id == task_id and task_ref.status == TaskStatus.COMPLETED:
                        completed = True
                        break

            if completed:
                velocity.tasks_completed += 1

            # Calculate task metrics
            contributors = set(c.author_email for c in task_commit_list)
            files_changed = sum(c.files_changed for c in task_commit_list)
            insertions = sum(c.insertions for c in task_commit_list)
            deletions = sum(c.deletions for c in task_commit_list)

            first_commit = task_commit_list[0]
            last_commit = task_commit_list[-1]
            duration = (last_commit.date - first_commit.date).days + 1

            task_metrics = TaskMetrics(
                task_id=task_id,
                commits=len(task_commit_list),
                contributors=len(contributors),
                files_changed=files_changed,
                insertions=insertions,
                deletions=deletions,
                first_commit_date=first_commit.date,
                last_commit_date=last_commit.date,
                duration_days=duration,
                completed=completed,
            )

            velocity.task_metrics.append(task_metrics)

        # Completion rate
        if velocity.tasks_worked > 0:
            velocity.completion_rate = velocity.tasks_completed / velocity.tasks_worked

        # Contributor metrics
        contributors: Dict[str, int] = defaultdict(int)
        for commit in commits:
            contributor = f"{commit.author_name} <{commit.author_email}>"
            contributors[contributor] += 1

        velocity.total_contributors = len(contributors)
        velocity.contributor_commits = dict(contributors)

        if velocity.total_contributors > 0:
            velocity.avg_commits_per_contributor = (
                velocity.total_commits / velocity.total_contributors
            )

        # Code metrics
        velocity.total_files_changed = sum(c.files_changed for c in commits)
        velocity.total_insertions = sum(c.insertions for c in commits)
        velocity.total_deletions = sum(c.deletions for c in commits)
        velocity.net_lines = velocity.total_insertions - velocity.total_deletions

        return velocity

    def calculate_velocity_trend(
        self,
        sprint_ids: List[str],
        sprint_periods: Optional[List[Tuple[Optional[str], Optional[str]]]] = None,
    ) -> VelocityTrend:
        """
        Calculate velocity trend across multiple sprints.

        Args:
            sprint_ids: List of sprint identifiers
            sprint_periods: Optional list of (start_ref, end_ref) tuples for each sprint

        Returns:
            VelocityTrend with metrics and trend analysis
        """
        trend = VelocityTrend()

        # Calculate velocity for each sprint
        for i, sprint_id in enumerate(sprint_ids):
            if sprint_periods and i < len(sprint_periods):
                start_ref, end_ref = sprint_periods[i]
                velocity = self.calculate_sprint_velocity(
                    sprint_id,
                    start_ref=start_ref,
                    end_ref=end_ref
                )
            else:
                velocity = self.calculate_sprint_velocity(sprint_id)

            trend.sprints.append(velocity)

        if not trend.sprints:
            return trend

        # Calculate averages
        n = len(trend.sprints)
        trend.avg_commits_per_sprint = sum(s.total_commits for s in trend.sprints) / n
        trend.avg_tasks_per_sprint = sum(s.tasks_worked for s in trend.sprints) / n
        trend.avg_completion_rate = sum(s.completion_rate for s in trend.sprints) / n

        # Analyze trends (simple: compare first half to second half)
        if n >= 2:
            mid = n // 2

            first_half_commits = sum(s.total_commits for s in trend.sprints[:mid]) / mid
            second_half_commits = sum(s.total_commits for s in trend.sprints[mid:]) / (n - mid)
            trend.commits_trending_up = second_half_commits > first_half_commits

            first_half_tasks = sum(s.tasks_worked for s in trend.sprints[:mid]) / mid
            second_half_tasks = sum(s.tasks_worked for s in trend.sprints[mid:]) / (n - mid)
            trend.tasks_trending_up = second_half_tasks > first_half_tasks

            first_half_completion = sum(s.completion_rate for s in trend.sprints[:mid]) / mid
            second_half_completion = sum(s.completion_rate for s in trend.sprints[mid:]) / (n - mid)
            trend.completion_trending_up = second_half_completion > first_half_completion

        return trend

    def calculate_weekly_velocity(
        self,
        weeks: int = 4,
        end_date: Optional[datetime] = None
    ) -> List[Tuple[datetime, int, int]]:
        """
        Calculate weekly commit velocity.

        Args:
            weeks: Number of weeks to analyze
            end_date: End date (default: now)

        Returns:
            List of (week_start, commits, tasks) tuples
        """
        if end_date is None:
            end_date = datetime.now()

        weekly_data = []

        for i in range(weeks):
            week_end = end_date - timedelta(weeks=i)
            week_start = week_end - timedelta(weeks=1)

            # Get commits for this week
            commits = self.analyzer.get_commits(
                since=week_start.strftime("%Y-%m-%d"),
                until=week_end.strftime("%Y-%m-%d")
            )

            # Parse and count tasks
            tasks = set()
            for commit in commits:
                commit.parsed = self.analyzer.parser.parse(commit.message, commit.sha)
                for task_ref in commit.parsed.tasks:
                    tasks.add(task_ref.task_id)

            weekly_data.append((week_start, len(commits), len(tasks)))

        return list(reversed(weekly_data))

    def calculate_task_duration_stats(
        self,
        sprint_id: Optional[str] = None,
        task_ids: Optional[List[str]] = None,
    ) -> Dict[str, float]:
        """
        Calculate task duration statistics.

        Args:
            sprint_id: Optional sprint to analyze
            task_ids: Optional specific tasks to analyze

        Returns:
            Dict with statistics: avg, min, max, median duration in days
        """
        durations = []

        if task_ids:
            # Analyze specific tasks
            for task_id in task_ids:
                commits = self.analyzer.find_commits_for_task(task_id)
                if commits:
                    commits.sort(key=lambda c: c.date)
                    duration = (commits[-1].date - commits[0].date).days + 1
                    durations.append(duration)

        elif sprint_id:
            # Analyze all tasks in sprint
            velocity = self.calculate_sprint_velocity(sprint_id)
            durations = [t.duration_days for t in velocity.task_metrics if t.duration_days]

        if not durations:
            return {
                "avg": 0.0,
                "min": 0.0,
                "max": 0.0,
                "median": 0.0,
            }

        durations.sort()
        n = len(durations)

        return {
            "avg": sum(durations) / n,
            "min": durations[0],
            "max": durations[-1],
            "median": durations[n // 2] if n % 2 == 1 else (durations[n//2-1] + durations[n//2]) / 2,
        }

    def calculate_contributor_velocity(
        self,
        contributor: str,
        since: Optional[str] = None,
        until: Optional[str] = None,
    ) -> Dict[str, any]:
        """
        Calculate velocity metrics for a specific contributor.

        Args:
            contributor: Contributor name or email
            since: Start date
            until: End date

        Returns:
            Dict with contributor metrics
        """
        # Get commits by contributor
        commits = self.analyzer.get_commits(
            author=contributor,
            since=since,
            until=until
        )

        if not commits:
            return {
                "commits": 0,
                "tasks": 0,
                "files_changed": 0,
                "insertions": 0,
                "deletions": 0,
            }

        # Parse commits
        tasks = set()
        for commit in commits:
            commit.parsed = self.analyzer.parser.parse(commit.message, commit.sha)
            for task_ref in commit.parsed.tasks:
                tasks.add(task_ref.task_id)

        return {
            "commits": len(commits),
            "tasks": len(tasks),
            "files_changed": sum(c.files_changed for c in commits),
            "insertions": sum(c.insertions for c in commits),
            "deletions": sum(c.deletions for c in commits),
            "net_lines": sum(c.insertions - c.deletions for c in commits),
        }


def quick_sprint_velocity(
    sprint_id: str,
    repo_path: str = ".",
    start_ref: Optional[str] = None,
    end_ref: Optional[str] = None,
) -> SprintVelocity:
    """
    Quick helper to calculate sprint velocity.

    Args:
        sprint_id: Sprint identifier
        repo_path: Path to git repository
        start_ref: Optional starting ref
        end_ref: Optional ending ref

    Returns:
        SprintVelocity with metrics
    """
    calculator = VelocityCalculator(repo_path)
    return calculator.calculate_sprint_velocity(
        sprint_id,
        start_ref=start_ref,
        end_ref=end_ref
    )
