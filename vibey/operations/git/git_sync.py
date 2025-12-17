"""
Git-primary sync command - derive YAML from Git state.

This module implements synchronization from Git (as source of truth) to YAML files.
In Git-primary mode, the Git repository state (branches, tags, commits) determines
the roadmap state in YAML files.

DERIVATION RULES:

Task Status:
- not_started: no branch AND no commits referencing task
- in_progress: branch exists OR commits exist BUT branch not merged
- completed: branch merged AND task commits exist

Sprint Status:
- not_started: no sprint/<id>/start tag exists
- in_progress: start tag exists, no sprint/<id>/end tag
- completed: both start and end tags exist

Progress Metrics:
- Calculated from task counts and completion states
- Derived from git history, not manually tracked
"""

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
import yaml

from vibey.operations.git.sprint_tagger import SprintTagger
from vibey.operations.git.branch_linker import BranchLinker
from vibey.operations.git.commit_parser import CommitParser


@dataclass
class TaskStateChange:
    """Represents a change to task state from git sync."""
    task_id: str
    field: str
    old_value: Any
    new_value: Any
    reason: str


@dataclass
class SprintStateChange:
    """Represents a change to sprint state from git sync."""
    sprint_id: str
    field: str
    old_value: Any
    new_value: Any
    reason: str


@dataclass
class SyncResult:
    """Result of git sync operation."""
    task_changes: List[TaskStateChange]
    sprint_changes: List[SprintStateChange]
    conflicts: List[str]
    warnings: List[str]
    dry_run: bool


class GitPrimarySync:
    """
    Synchronize roadmap YAML from Git state (Git-primary mode).

    In Git-primary mode, Git is the source of truth and YAML files are
    derived from Git branches, tags, and commits.
    """

    def __init__(self, repo_path: Optional[str] = None):
        """
        Initialize Git-primary sync.

        Args:
            repo_path: Path to git repository (default: current directory)
        """
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self.roadmap_dir = self.repo_path / ".vibey" / "roadmap"
        self.git_dir = self.repo_path / ".git"

        if not self.git_dir.exists():
            raise ValueError(f"Not a git repository: {self.repo_path}")

        if not self.roadmap_dir.exists():
            raise ValueError(f"Roadmap directory not found: {self.roadmap_dir}")

        # Initialize git operation helpers
        self.tagger = SprintTagger(repo_path)
        self.linker = BranchLinker(repo_path)
        self.parser = CommitParser()

    def _run_git(self, *args, check: bool = True) -> subprocess.CompletedProcess:
        """Run a git command."""
        cmd = ["git"] + list(args)
        return subprocess.run(
            cmd,
            cwd=self.repo_path,
            check=check,
            capture_output=True,
            text=True
        )

    def _is_branch_merged(self, branch_name: str, target_branch: str = "main") -> bool:
        """
        Check if a branch is merged into target.

        Args:
            branch_name: Branch to check
            target_branch: Target branch (default: main)

        Returns:
            True if branch is merged
        """
        try:
            # Check if branch exists
            result = self._run_git("rev-parse", "--verify", branch_name, check=False)
            if result.returncode != 0:
                return False

            # Check if merged
            result = self._run_git("branch", "--merged", target_branch, check=False)
            merged_branches = result.stdout.splitlines()
            return any(branch_name in branch.strip() for branch in merged_branches)
        except Exception:
            return False

    def _get_task_commits(self, task_id: str) -> List[str]:
        """
        Get list of commits that reference a task.

        Args:
            task_id: Task identifier

        Returns:
            List of commit SHAs
        """
        try:
            # Search commit messages for task ID
            result = self._run_git("log", "--all", "--format=%H", f"--grep={task_id}", check=False)
            commits = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            return commits
        except Exception:
            return []

    def _derive_task_status(
        self,
        task_id: str,
        task_data: Dict[str, Any]
    ) -> Tuple[str, str]:
        """
        Derive task status from git state.

        Args:
            task_id: Task identifier
            task_data: Current task data from YAML

        Returns:
            (derived_status, reason)
        """
        # Check for branch
        branch_name = task_data.get('branch', {}).get('name') if isinstance(task_data.get('branch'), dict) else None

        if not branch_name:
            # Try to find branch by naming convention
            branch_name = f"task/{task_id}"

        # Check if branch exists
        branch_exists = False
        if branch_name:
            result = self._run_git("rev-parse", "--verify", branch_name, check=False)
            branch_exists = result.returncode == 0

        # Check for commits
        commits = self._get_task_commits(task_id)
        has_commits = len(commits) > 0

        # Apply derivation rules
        if not branch_exists and not has_commits:
            return "not_started", "No branch and no commits found"

        if branch_exists and self._is_branch_merged(branch_name):
            if has_commits:
                return "completed", f"Branch {branch_name} merged with commits"
            else:
                return "completed", f"Branch {branch_name} merged (no task commits found)"

        if branch_exists or has_commits:
            return "in_progress", f"Branch exists: {branch_exists}, Commits: {len(commits)}"

        return "not_started", "Default state"

    def _derive_sprint_status(
        self,
        sprint_id: str,
        sprint_data: Dict[str, Any]
    ) -> Tuple[str, str]:
        """
        Derive sprint status from git tags.

        Args:
            sprint_id: Sprint identifier
            sprint_data: Current sprint data from YAML

        Returns:
            (derived_status, reason)
        """
        # Check for start/end tags
        start_tag = f"sprint/{sprint_id}/start"
        end_tag = f"sprint/{sprint_id}/end"

        has_start = self.tagger._tag_exists(start_tag)
        has_end = self.tagger._tag_exists(end_tag)

        # Apply derivation rules
        if has_end:
            return "completed", f"End tag {end_tag} exists"
        elif has_start:
            return "in_progress", f"Start tag {start_tag} exists, no end tag"
        else:
            return "not_started", "No start tag found"

    def _calculate_progress(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate progress metrics from task list.

        Args:
            tasks: List of task dictionaries

        Returns:
            Progress dictionary with counts and percentage
        """
        total = len(tasks)
        completed = sum(1 for task in tasks if task.get('status') == 'completed')

        return {
            'tasks_total': total,
            'tasks_completed': completed,
            'completion_percent': int((completed / total * 100) if total > 0 else 0)
        }

    def _find_task_file(self, task_id: str) -> Optional[Path]:
        """
        Find YAML file for a task.

        Uses flat structure: tasks/{task_id}.yaml

        Args:
            task_id: Task identifier (ULID)

        Returns:
            Path to task.yaml file, or None
        """
        task_file = self.roadmap_dir / "tasks" / f"{task_id}.yaml"
        if task_file.exists():
            return task_file
        return None

    def _find_sprint_file(self, sprint_id: str) -> Optional[Path]:
        """
        Find YAML file for a sprint.

        Uses flat structure: sprints/{sprint_id}.yaml

        Args:
            sprint_id: Sprint identifier (ULID)

        Returns:
            Path to sprint.yaml file, or None
        """
        sprint_file = self.roadmap_dir / "sprints" / f"{sprint_id}.yaml"
        if sprint_file.exists():
            return sprint_file
        return None

    def _load_tasks_for_sprint(self, sprint_id: str) -> List[Dict[str, Any]]:
        """
        Load tasks for a sprint from standalone task files.

        Args:
            sprint_id: Sprint identifier (ULID)

        Returns:
            List of task dictionaries
        """
        tasks = []
        tasks_dir = self.roadmap_dir / "tasks"

        if not tasks_dir.exists():
            return tasks

        for task_file in tasks_dir.glob("*.yaml"):
            try:
                with open(task_file, 'r') as f:
                    data = yaml.safe_load(f)
                task_data = data.get('task', {})
                if task_data.get('sprint_id') == sprint_id:
                    tasks.append(task_data)
            except Exception:
                continue

        return tasks

    def sync_task(
        self,
        task_id: str,
        dry_run: bool = False
    ) -> Tuple[List[TaskStateChange], List[str]]:
        """
        Sync a single task from git state.

        Args:
            task_id: Task identifier
            dry_run: If True, don't modify files

        Returns:
            (changes, warnings)
        """
        changes = []
        warnings = []

        # Find task file
        task_file = self._find_task_file(task_id)
        if not task_file:
            warnings.append(f"Task {task_id} not found in roadmap")
            return changes, warnings

        # Load current state from standalone task file (tasks/{id}.yaml)
        with open(task_file, 'r') as f:
            data = yaml.safe_load(f)

        # Standalone task files have 'task:' root key (not 'sprint.tasks[]')
        task_data = data.get('task', {})
        if not task_data:
            warnings.append(f"Task {task_id} has invalid format in {task_file}")
            return changes, warnings

        # Derive status from git
        derived_status, reason = self._derive_task_status(task_id, task_data)
        current_status = task_data.get('status', 'not_started')

        # Check for changes
        if derived_status != current_status:
            change = TaskStateChange(
                task_id=task_id,
                field='status',
                old_value=current_status,
                new_value=derived_status,
                reason=reason
            )
            changes.append(change)

            # Apply change if not dry-run
            if not dry_run:
                data['task']['status'] = derived_status

                # Add git sync metadata
                if 'metadata' not in data['task']:
                    data['task']['metadata'] = {}
                data['task']['metadata']['_git_sync'] = {
                    'last_synced': datetime.now(timezone.utc).isoformat(),
                    'derived_from': 'git',
                    'reason': reason
                }

                # Update completed timestamp if newly completed
                if derived_status == 'completed' and not data['task'].get('completed'):
                    data['task']['completed'] = datetime.now(timezone.utc).isoformat()

                # Write back
                with open(task_file, 'w') as f:
                    yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        return changes, warnings

    def sync_sprint(
        self,
        sprint_id: str,
        dry_run: bool = False
    ) -> Tuple[List[SprintStateChange], List[TaskStateChange], List[str]]:
        """
        Sync a sprint and its tasks from git state.

        Args:
            sprint_id: Sprint identifier
            dry_run: If True, don't modify files

        Returns:
            (sprint_changes, task_changes, warnings)
        """
        sprint_changes = []
        task_changes = []
        warnings = []

        # Find sprint file
        sprint_file = self._find_sprint_file(sprint_id)
        if not sprint_file:
            warnings.append(f"Sprint {sprint_id} not found in roadmap")
            return sprint_changes, task_changes, warnings

        # Load current state
        with open(sprint_file, 'r') as f:
            data = yaml.safe_load(f)

        sprint = data.get('sprint', {})

        # Load tasks from standalone files (not embedded sprint.tasks[])
        tasks = self._load_tasks_for_sprint(sprint_id)

        # Derive sprint status
        derived_status, reason = self._derive_sprint_status(sprint_id, sprint)
        current_status = sprint.get('status', 'not_started')

        if derived_status != current_status:
            change = SprintStateChange(
                sprint_id=sprint_id,
                field='status',
                old_value=current_status,
                new_value=derived_status,
                reason=reason
            )
            sprint_changes.append(change)

            if not dry_run:
                sprint['status'] = derived_status

                # Update timestamps
                if derived_status == 'in_progress' and not sprint.get('started'):
                    sprint['started'] = datetime.now(timezone.utc).isoformat()
                elif derived_status == 'completed' and not sprint.get('completed'):
                    sprint['completed'] = datetime.now(timezone.utc).isoformat()

        # Sync all tasks in sprint
        for task in tasks:
            task_id = task.get('id')
            if task_id:
                changes, warns = self.sync_task(task_id, dry_run=True)  # Dry run to collect changes
                task_changes.extend(changes)
                warnings.extend(warns)

        # Recalculate progress if tasks changed
        if task_changes and not dry_run:
            # Reload to get updated task statuses from standalone files
            tasks = self._load_tasks_for_sprint(sprint_id)

            # Reload sprint data for metadata update
            with open(sprint_file, 'r') as f:
                data = yaml.safe_load(f)
            sprint = data.get('sprint', {})

            new_progress = self._calculate_progress(tasks)
            sprint['progress'] = new_progress

            # Add git sync metadata
            sprint['_git_sync'] = {
                'last_synced': datetime.now(timezone.utc).isoformat(),
                'derived_from': 'git',
                'task_changes': len(task_changes),
                'sprint_changes': len(sprint_changes)
            }

            # Write back
            data['sprint'] = sprint
            with open(sprint_file, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        return sprint_changes, task_changes, warnings

    def sync_all(
        self,
        track_id: Optional[str] = None,
        dry_run: bool = False
    ) -> SyncResult:
        """
        Sync all sprints/tasks from git state.

        Uses flat structure: sprints/{sprint_id}.yaml

        Args:
            track_id: Only sync specific track (optional)
            dry_run: If True, don't modify files

        Returns:
            SyncResult with all changes and warnings
        """
        all_task_changes = []
        all_sprint_changes = []
        all_warnings = []
        conflicts = []

        # Find all sprint files from flat structure
        sprints_dir = self.roadmap_dir / "sprints"
        if not sprints_dir.is_dir():
            all_warnings.append(f"Sprints directory not found: {sprints_dir}")
            return SyncResult(
                task_changes=all_task_changes,
                sprint_changes=all_sprint_changes,
                conflicts=conflicts,
                warnings=all_warnings,
                dry_run=dry_run
            )

        for sprint_file in sprints_dir.glob("*.yaml"):
            try:
                with open(sprint_file, 'r') as f:
                    data = yaml.safe_load(f)
                    sprint = data.get('sprint', {})
                    sprint_id = sprint.get('id')
                    sprint_track_id = sprint.get('track_id')

                    # Filter by track_id if specified
                    if track_id and sprint_track_id != track_id:
                        continue

                    if sprint_id:
                        sprint_changes, task_changes, warnings = self.sync_sprint(sprint_id, dry_run)
                        all_sprint_changes.extend(sprint_changes)
                        all_task_changes.extend(task_changes)
                        all_warnings.extend(warnings)

            except Exception as e:
                all_warnings.append(f"Error syncing {sprint_file}: {e}")

        return SyncResult(
            task_changes=all_task_changes,
            sprint_changes=all_sprint_changes,
            conflicts=conflicts,
            warnings=all_warnings,
            dry_run=dry_run
        )


def sync_from_git(
    repo_path: Optional[str] = None,
    sprint_id: Optional[str] = None,
    task_id: Optional[str] = None,
    track_id: Optional[str] = None,
    dry_run: bool = False
) -> SyncResult:
    """
    Convenience function to sync roadmap from git state.

    Args:
        repo_path: Path to git repository
        sprint_id: Sync specific sprint
        task_id: Sync specific task
        track_id: Sync specific track
        dry_run: Don't modify files

    Returns:
        SyncResult with changes
    """
    syncer = GitPrimarySync(repo_path)

    if task_id:
        changes, warnings = syncer.sync_task(task_id, dry_run)
        return SyncResult(
            task_changes=changes,
            sprint_changes=[],
            conflicts=[],
            warnings=warnings,
            dry_run=dry_run
        )
    elif sprint_id:
        sprint_changes, task_changes, warnings = syncer.sync_sprint(sprint_id, dry_run)
        return SyncResult(
            task_changes=task_changes,
            sprint_changes=sprint_changes,
            conflicts=[],
            warnings=warnings,
            dry_run=dry_run
        )
    else:
        return syncer.sync_all(track_id, dry_run)
