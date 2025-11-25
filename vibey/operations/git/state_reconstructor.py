"""
State Reconstruction from Git History

Reconstruct roadmap state at any point in time from Git history.

Task: git-integration-1-task-008
Status: In Progress
"""

import subprocess
import yaml
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from vibey.operations.git.log_analyzer import GitLogAnalyzer, CommitInfo


@dataclass
class StateSnapshot:
    """A snapshot of roadmap state at a specific commit."""
    ref: str
    sha: str
    date: datetime
    author: str
    message: str

    # Roadmap state (parsed YAML)
    tracks: Dict[str, Any]
    sprints: Dict[str, Any]
    tasks: Dict[str, Any]

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "ref": self.ref,
            "sha": self.sha,
            "date": self.date.isoformat(),
            "author": self.author,
            "message": self.message,
            "tracks": self.tracks,
            "sprints": self.sprints,
            "tasks": self.tasks,
        }


@dataclass
class StateChange:
    """A change in state between two commits."""
    field: str
    old_value: Any
    new_value: Any
    commit_sha: str
    commit_date: datetime

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "field": self.field,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "commit_sha": self.commit_sha,
            "commit_date": self.commit_date.isoformat(),
        }


@dataclass
class ProgressPoint:
    """A point in progress timeline."""
    date: datetime
    sha: str
    tasks_total: int
    tasks_completed: int
    completion_percent: float

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "date": self.date.isoformat(),
            "sha": self.sha,
            "tasks_total": self.tasks_total,
            "tasks_completed": self.tasks_completed,
            "completion_percent": self.completion_percent,
        }


class StateReconstructor:
    """
    Reconstruct roadmap state from Git history.

    Provides time-travel queries, change history, progress tracking,
    and rollback capabilities by reading YAML files at different commits.
    """

    def __init__(self, repo_path: str = ".", roadmap_root: str = ".vibey/roadmap"):
        """
        Initialize state reconstructor.

        Args:
            repo_path: Path to git repository
            roadmap_root: Path to roadmap directory relative to repo root
        """
        self.analyzer = GitLogAnalyzer(repo_path=repo_path)
        self.repo_path = Path(repo_path).resolve()
        self.roadmap_root = roadmap_root

    def _run_git(self, *args: str) -> subprocess.CompletedProcess:
        """Run a git command."""
        cmd = ["git", "-C", str(self.repo_path)] + list(args)
        return subprocess.run(cmd, capture_output=True, text=True, check=True)

    def _get_file_at_ref(self, ref: str, file_path: str) -> Optional[str]:
        """
        Get file contents at a specific ref.

        Args:
            ref: Git ref (commit SHA, tag, branch, etc.)
            file_path: Path to file relative to repo root

        Returns:
            File contents as string, or None if file doesn't exist at that ref
        """
        try:
            result = self._run_git("show", f"{ref}:{file_path}")
            return result.stdout
        except subprocess.CalledProcessError:
            return None

    def _parse_yaml_content(self, content: str) -> Optional[Dict]:
        """Parse YAML content safely."""
        if not content:
            return None
        try:
            return yaml.safe_load(content)
        except yaml.YAMLError:
            return None

    def _resolve_ref_to_commit(self, ref: str) -> Tuple[str, CommitInfo]:
        """
        Resolve a ref to a commit SHA and info.

        Args:
            ref: Git ref (commit, tag, branch, date like "2024-01-01")

        Returns:
            Tuple of (SHA, CommitInfo)
        """
        # Try as date
        if ref and not ref.startswith(("HEAD", "main", "master")) and "-" in ref:
            try:
                # Parse as date
                commits = self.analyzer.get_commits(until=ref, max_count=1)
                if commits:
                    return commits[0].sha, commits[0]
            except:
                pass

        # Resolve ref to SHA
        result = self._run_git("rev-parse", ref)
        sha = result.stdout.strip()

        # Get commit info
        commit = self.analyzer.get_commit_by_sha(sha)
        return sha, commit

    def get_state_at(self, ref: str) -> StateSnapshot:
        """
        Get roadmap state at a specific ref.

        Args:
            ref: Git ref (commit SHA, tag, branch, or date)

        Returns:
            StateSnapshot with roadmap state at that point
        """
        sha, commit = self._resolve_ref_to_commit(ref)

        # Read roadmap files at this commit
        tracks = {}
        sprints = {}
        tasks = {}

        # Get all track directories
        try:
            result = self._run_git("ls-tree", "--name-only", sha, self.roadmap_root)
            track_dirs = [line.strip() for line in result.stdout.strip().split('\n') if line]
        except subprocess.CalledProcessError:
            track_dirs = []

        # Read each track
        for track_dir in track_dirs:
            # Read track.yaml
            track_file = f"{self.roadmap_root}/{track_dir}/track.yaml"
            content = self._get_file_at_ref(sha, track_file)
            if content:
                track_data = self._parse_yaml_content(content)
                if track_data and 'track' in track_data:
                    track_id = track_data['track']['id']
                    tracks[track_id] = track_data['track']

                    # Get sprints for this track
                    try:
                        result = self._run_git("ls-tree", "--name-only", sha,
                                              f"{self.roadmap_root}/{track_dir}")
                        sprint_dirs = [d.strip() for d in result.stdout.strip().split('\n')
                                     if d and d != 'track.yaml' and d != 'context']
                    except subprocess.CalledProcessError:
                        sprint_dirs = []

                    # Read each sprint
                    for sprint_dir in sprint_dirs:
                        sprint_file = f"{self.roadmap_root}/{track_dir}/{sprint_dir}/sprint.yaml"
                        content = self._get_file_at_ref(sha, sprint_file)
                        if content:
                            sprint_data = self._parse_yaml_content(content)
                            if sprint_data and 'sprint' in sprint_data:
                                sprint_id = sprint_data['sprint']['id']
                                sprints[sprint_id] = sprint_data['sprint']

                                # Extract tasks
                                if 'tasks' in sprint_data['sprint']:
                                    for task in sprint_data['sprint']['tasks']:
                                        task_id = task['id']
                                        tasks[task_id] = task

        return StateSnapshot(
            ref=ref,
            sha=sha,
            date=commit.date,
            author=commit.author_name,
            message=commit.message,
            tracks=tracks,
            sprints=sprints,
            tasks=tasks,
        )

    def diff_states(self, ref1: str, ref2: str) -> Dict[str, List[StateChange]]:
        """
        Compare roadmap states between two refs.

        Args:
            ref1: First ref (older)
            ref2: Second ref (newer)

        Returns:
            Dict mapping item_id to list of changes
        """
        state1 = self.get_state_at(ref1)
        state2 = self.get_state_at(ref2)

        changes_by_item = {}

        # Compare tasks
        all_task_ids = set(state1.tasks.keys()) | set(state2.tasks.keys())
        for task_id in all_task_ids:
            task1 = state1.tasks.get(task_id, {})
            task2 = state2.tasks.get(task_id, {})

            item_changes = []

            # Check if added/removed
            if not task1 and task2:
                item_changes.append(StateChange(
                    field="existence",
                    old_value=None,
                    new_value="created",
                    commit_sha=state2.sha,
                    commit_date=state2.date,
                ))
            elif task1 and not task2:
                item_changes.append(StateChange(
                    field="existence",
                    old_value="exists",
                    new_value="deleted",
                    commit_sha=state2.sha,
                    commit_date=state2.date,
                ))

            # Compare fields
            if task1 and task2:
                fields_to_compare = ['status', 'name', 'priority', 'assigned_agent']
                for field in fields_to_compare:
                    val1 = task1.get(field)
                    val2 = task2.get(field)
                    if val1 != val2:
                        item_changes.append(StateChange(
                            field=field,
                            old_value=val1,
                            new_value=val2,
                            commit_sha=state2.sha,
                            commit_date=state2.date,
                        ))

            if item_changes:
                changes_by_item[task_id] = item_changes

        # Compare sprints
        all_sprint_ids = set(state1.sprints.keys()) | set(state2.sprints.keys())
        for sprint_id in all_sprint_ids:
            sprint1 = state1.sprints.get(sprint_id, {})
            sprint2 = state2.sprints.get(sprint_id, {})

            item_changes = []

            if sprint1 and sprint2:
                fields_to_compare = ['status', 'started', 'completed']
                for field in fields_to_compare:
                    val1 = sprint1.get(field)
                    val2 = sprint2.get(field)
                    if val1 != val2:
                        item_changes.append(StateChange(
                            field=field,
                            old_value=val1,
                            new_value=val2,
                            commit_sha=state2.sha,
                            commit_date=state2.date,
                        ))

                # Compare progress
                if 'progress' in sprint1 and 'progress' in sprint2:
                    prog1 = sprint1['progress']
                    prog2 = sprint2['progress']
                    if prog1.get('tasks_completed') != prog2.get('tasks_completed'):
                        item_changes.append(StateChange(
                            field="tasks_completed",
                            old_value=prog1.get('tasks_completed'),
                            new_value=prog2.get('tasks_completed'),
                            commit_sha=state2.sha,
                            commit_date=state2.date,
                        ))

            if item_changes:
                changes_by_item[sprint_id] = item_changes

        return changes_by_item

    def get_history(self, item_id: str, item_type: str = "task") -> List[StateChange]:
        """
        Get complete change history for an item.

        Args:
            item_id: Task, sprint, or track ID
            item_type: Type of item ("task", "sprint", "track")

        Returns:
            List of StateChange objects chronologically
        """
        # Get all commits
        commits = self.analyzer.get_commits(max_count=1000)

        # Track changes over time
        all_changes = []
        prev_state = None

        for commit in reversed(commits):  # Oldest to newest
            try:
                state = self.get_state_at(commit.sha)

                if item_type == "task":
                    current_item = state.tasks.get(item_id)
                    prev_item = prev_state.tasks.get(item_id) if prev_state else None
                elif item_type == "sprint":
                    current_item = state.sprints.get(item_id)
                    prev_item = prev_state.sprints.get(item_id) if prev_state else None
                else:  # track
                    current_item = state.tracks.get(item_id)
                    prev_item = prev_state.tracks.get(item_id) if prev_state else None

                # Check for changes
                if prev_item is None and current_item:
                    # Item created
                    all_changes.append(StateChange(
                        field="existence",
                        old_value=None,
                        new_value="created",
                        commit_sha=commit.sha,
                        commit_date=commit.date,
                    ))
                elif prev_item and current_item:
                    # Check field changes
                    for field in ['status', 'name', 'priority', 'assigned_agent']:
                        if field in current_item and field in prev_item:
                            if current_item[field] != prev_item[field]:
                                all_changes.append(StateChange(
                                    field=field,
                                    old_value=prev_item[field],
                                    new_value=current_item[field],
                                    commit_sha=commit.sha,
                                    commit_date=commit.date,
                                ))

                prev_state = state
            except:
                continue

        return all_changes

    def get_progress_timeline(self, sprint_id: str, sample_interval: int = 10) -> List[ProgressPoint]:
        """
        Get progress timeline for a sprint (for burndown charts).

        Args:
            sprint_id: Sprint identifier
            sample_interval: Sample every N commits (default: 10)

        Returns:
            List of ProgressPoint objects
        """
        # Get all commits
        commits = self.analyzer.get_commits(max_count=1000)

        timeline = []
        for i, commit in enumerate(reversed(commits)):
            # Sample at intervals
            if i % sample_interval != 0:
                continue

            try:
                state = self.get_state_at(commit.sha)
                sprint = state.sprints.get(sprint_id)

                if sprint and 'progress' in sprint:
                    progress = sprint['progress']
                    timeline.append(ProgressPoint(
                        date=commit.date,
                        sha=commit.sha,
                        tasks_total=progress.get('tasks_total', 0),
                        tasks_completed=progress.get('tasks_completed', 0),
                        completion_percent=progress.get('completion_percent', 0.0),
                    ))
            except:
                continue

        return timeline

    def rollback(self, ref: str, dry_run: bool = True) -> Dict[str, str]:
        """
        Rollback roadmap to state at ref.

        Args:
            ref: Git ref to rollback to
            dry_run: If True, just show what would change

        Returns:
            Dict mapping file paths to "would restore" or "restored"
        """
        sha, commit = self._resolve_ref_to_commit(ref)

        # Get state at target ref
        target_state = self.get_state_at(ref)

        # Get list of files to restore
        result = self._run_git("ls-tree", "-r", "--name-only", sha, self.roadmap_root)
        files = [line.strip() for line in result.stdout.strip().split('\n') if line and line.endswith('.yaml')]

        restore_status = {}

        for file_path in files:
            if dry_run:
                restore_status[file_path] = f"would restore from {ref}"
            else:
                # Actually restore the file
                try:
                    content = self._get_file_at_ref(sha, file_path)
                    if content:
                        full_path = self.repo_path / file_path
                        full_path.parent.mkdir(parents=True, exist_ok=True)
                        full_path.write_text(content)
                        restore_status[file_path] = f"restored from {ref}"
                except Exception as e:
                    restore_status[file_path] = f"error: {e}"

        return restore_status


def get_state_at_ref(ref: str, repo_path: str = ".") -> StateSnapshot:
    """
    Quick helper to get state at a ref.

    Args:
        ref: Git ref
        repo_path: Path to repository

    Returns:
        StateSnapshot
    """
    reconstructor = StateReconstructor(repo_path=repo_path)
    return reconstructor.get_state_at(ref)
