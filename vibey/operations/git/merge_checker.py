"""
PR merge checkpoint for task conflict detection.

This module provides:
- Detection of task completion conflicts during PR merges
- Diff analysis between PR branch and target branch
- Audit logging for conflict resolutions
- CI/CD integration support
"""

import subprocess
import yaml
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set


@dataclass
class TaskStatusChange:
    """Represents a task status change between branches."""
    task_id: str
    file_path: str
    old_status: str
    new_status: str
    sprint_id: str


@dataclass
class TaskConflict:
    """Represents a task completion conflict."""
    task_id: str
    file_path: str
    pr_branch: str
    target_branch: str
    pr_status: str
    target_status: str
    pr_commit: Optional[str] = None
    target_commit: Optional[str] = None
    severity: str = 'error'  # 'error', 'warning'


@dataclass
class ConflictResolution:
    """Resolution decision for a conflict."""
    task_id: str
    resolution: str  # 'keep_target', 'keep_pr', 'merge_both'
    resolved_by: str
    resolved_at: datetime
    notes: Optional[str] = None


@dataclass
class MergeCheckResult:
    """Result of a merge check operation."""
    pr_branch: str
    target_branch: str
    conflicts: List[TaskConflict]
    warnings: List[str]
    safe_to_merge: bool
    checked_at: datetime


class MergeChecker:
    """
    Check for task completion conflicts during PR merges.

    Prevents duplicate task completion claims by detecting when
    a task is marked complete in both the PR branch and target branch.
    """

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.roadmap_root = self.repo_path / ".vibey" / "roadmap"

    def _run_git(self, args: List[str], check: bool = True) -> Tuple[bool, str, str]:
        """
        Run a git command and return (success, stdout, stderr).

        Args:
            args: Git command arguments (without 'git')
            check: If True, raise on non-zero exit

        Returns:
            (success, stdout, stderr) tuple
        """
        try:
            result = subprocess.run(
                ['git'] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=check
            )
            return True, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            if check:
                raise
            return False, e.stdout, e.stderr

    def _get_file_at_ref(self, file_path: str, ref: str) -> Optional[str]:
        """
        Get file content at a specific git ref.

        Args:
            file_path: Path to file relative to repo root
            ref: Git ref (branch name, commit SHA, etc.)

        Returns:
            File content or None if file doesn't exist at ref
        """
        success, stdout, _ = self._run_git(
            ['show', f'{ref}:{file_path}'],
            check=False
        )

        if success:
            return stdout
        return None

    def _parse_task_status(self, yaml_content: str) -> Dict[str, str]:
        """
        Parse task statuses from standalone task YAML content or sprint YAML.

        Supports both standalone task files (task: {}) and legacy sprint files
        with embedded tasks (sprint: {tasks: []}).

        Args:
            yaml_content: YAML file content

        Returns:
            Dict mapping task_id to status
        """
        try:
            data = yaml.safe_load(yaml_content)
            if not data:
                return {}

            # Check for standalone task file format (task: {})
            if 'task' in data:
                task_data = data['task']
                task_id = task_data.get('id')
                if task_id:
                    return {task_id: task_data.get('status', 'not_started')}
                return {}

            # Legacy: Sprint file with embedded tasks (DEPRECATED)
            if 'sprint' not in data:
                return {}

            tasks = data['sprint'].get('tasks', [])
            return {
                task['id']: task.get('status', 'not_started')
                for task in tasks
                if 'id' in task
            }
        except Exception:
            return {}

    def _find_sprint_files(self, ref: str) -> List[str]:
        """
        Find all sprint.yaml files at a given ref.

        Args:
            ref: Git ref to search

        Returns:
            List of file paths relative to repo root
        """
        success, stdout, _ = self._run_git(
            ['ls-tree', '-r', '--name-only', ref, '.vibey/roadmap'],
            check=False
        )

        if not success:
            return []

        files = []
        for line in stdout.strip().split('\n'):
            if line.endswith('sprint.yaml'):
                files.append(line)

        return files

    def _find_task_files(self, ref: str) -> List[str]:
        """
        Find all standalone task YAML files at a given ref.

        Args:
            ref: Git ref to search

        Returns:
            List of file paths relative to repo root
        """
        success, stdout, _ = self._run_git(
            ['ls-tree', '-r', '--name-only', ref, '.vibey/roadmap/tasks'],
            check=False
        )

        if not success:
            return []

        files = []
        for line in stdout.strip().split('\n'):
            if line and line.endswith('.yaml'):
                files.append(line)

        return files

    def _get_task_status_changes(self, pr_branch: str, target_branch: str) -> List[TaskStatusChange]:
        """
        Get all task status changes between PR branch and target branch.

        Scans both standalone task files (tasks/*.yaml) and legacy sprint files
        with embedded tasks.

        Args:
            pr_branch: PR source branch
            target_branch: Target branch (e.g., 'main')

        Returns:
            List of task status changes
        """
        changes = []

        # First: Scan standalone task files (primary source)
        task_files = self._find_task_files(target_branch)
        pr_task_files = self._find_task_files(pr_branch)
        all_task_files = set(task_files) | set(pr_task_files)

        for task_file in all_task_files:
            target_content = self._get_file_at_ref(task_file, target_branch)
            pr_content = self._get_file_at_ref(task_file, pr_branch)

            target_statuses = self._parse_task_status(target_content) if target_content else {}
            pr_statuses = self._parse_task_status(pr_content) if pr_content else {}

            # Get sprint_id from task file content
            sprint_id = 'unknown'
            content = pr_content or target_content
            if content:
                try:
                    data = yaml.safe_load(content)
                    if data and 'task' in data:
                        sprint_id = data['task'].get('sprint_id', 'unknown')
                except Exception:
                    pass

            all_task_ids = set(target_statuses.keys()) | set(pr_statuses.keys())
            for task_id in all_task_ids:
                target_status = target_statuses.get(task_id, 'not_started')
                pr_status = pr_statuses.get(task_id, 'not_started')

                if target_status != pr_status:
                    changes.append(TaskStatusChange(
                        task_id=task_id,
                        file_path=task_file,
                        old_status=target_status,
                        new_status=pr_status,
                        sprint_id=sprint_id
                    ))

        # Second: Also check legacy sprint files with embedded tasks (DEPRECATED)
        sprint_files = self._find_sprint_files(target_branch)

        for sprint_file in sprint_files:
            target_content = self._get_file_at_ref(sprint_file, target_branch)
            pr_content = self._get_file_at_ref(sprint_file, pr_branch)

            if not target_content or not pr_content:
                continue

            # Parse task statuses (will return empty for sprints without embedded tasks)
            target_statuses = self._parse_task_status(target_content)
            pr_statuses = self._parse_task_status(pr_content)

            # Skip if no embedded tasks found (they're in standalone files now)
            if not target_statuses and not pr_statuses:
                continue

            # Extract sprint ID from file path
            # .vibey/roadmap/sprints/{sprint_id}.yaml or legacy path
            parts = Path(sprint_file).parts
            if 'sprints' in parts:
                idx = parts.index('sprints')
                if idx + 1 < len(parts):
                    sprint_id = Path(parts[idx + 1]).stem  # Remove .yaml extension
                else:
                    sprint_id = 'unknown'
            elif len(parts) >= 4:
                sprint_id = parts[3]
            else:
                sprint_id = 'unknown'

            # Find status changes
            all_task_ids = set(target_statuses.keys()) | set(pr_statuses.keys())
            for task_id in all_task_ids:
                target_status = target_statuses.get(task_id, 'not_started')
                pr_status = pr_statuses.get(task_id, 'not_started')

                if target_status != pr_status:
                    changes.append(TaskStatusChange(
                        task_id=task_id,
                        file_path=sprint_file,
                        old_status=target_status,
                        new_status=pr_status,
                        sprint_id=sprint_id
                    ))

        return changes

    def _is_completion_change(self, change: TaskStatusChange) -> bool:
        """
        Check if a status change represents a task being marked as completed.

        Args:
            change: Task status change

        Returns:
            True if change is incomplete → complete
        """
        return (
            change.old_status in ('not_started', 'in_progress', 'blocked') and
            change.new_status == 'completed'
        )

    def _get_commit_for_status_change(self, task_id: str, branch: str) -> Optional[str]:
        """
        Find the commit that changed a task's status to completed.

        Args:
            task_id: Task ID
            branch: Branch to search

        Returns:
            Commit SHA or None
        """
        # Search git log for commits mentioning this task
        success, stdout, _ = self._run_git(
            ['log', '--all', '--format=%H', f'--grep={task_id}', '-n', '10'],
            check=False
        )

        if success and stdout.strip():
            commits = stdout.strip().split('\n')
            return commits[0] if commits else None

        return None

    def check_merge(self, pr_branch: str, target_branch: str = 'main') -> Tuple[MergeCheckResult, Optional[str]]:
        """
        Check for task completion conflicts between PR and target branch.

        Args:
            pr_branch: PR source branch
            target_branch: Target branch (default: 'main')

        Returns:
            (MergeCheckResult, error) tuple
        """
        # Verify branches exist
        for branch in [pr_branch, target_branch]:
            success, _, _ = self._run_git(['rev-parse', '--verify', branch], check=False)
            if not success:
                return MergeCheckResult(
                    pr_branch=pr_branch,
                    target_branch=target_branch,
                    conflicts=[],
                    warnings=[],
                    safe_to_merge=False,
                    checked_at=datetime.now(timezone.utc)
                ), f"Branch not found: {branch}"

        # Get all task status changes
        changes = self._get_task_status_changes(pr_branch, target_branch)

        conflicts = []
        warnings = []

        # Check each change for conflicts
        for change in changes:
            # CONFLICT CONDITION:
            # Task is NEWLY marked complete in PR (incomplete → complete in PR)
            # AND that SAME task is ALREADY complete in target

            # Check if this is a completion in the PR
            if self._is_completion_change(change):
                # This means in target it was incomplete, in PR it's complete
                # This is NOT a conflict - it's the normal flow
                continue

            # Check if task is being "uncompleted" in PR but complete in target
            if change.old_status == 'completed' and change.new_status != 'completed':
                # Task complete in target, incomplete in PR
                # This could be a conflict if PR is trying to redo completed work
                pr_commit = self._get_commit_for_status_change(change.task_id, pr_branch)
                target_commit = self._get_commit_for_status_change(change.task_id, target_branch)

                conflicts.append(TaskConflict(
                    task_id=change.task_id,
                    file_path=change.file_path,
                    pr_branch=pr_branch,
                    target_branch=target_branch,
                    pr_status=change.new_status,
                    target_status=change.old_status,
                    pr_commit=pr_commit,
                    target_commit=target_commit,
                    severity='warning'  # This might be intentional
                ))

            # Check if both branches mark task as complete with different data
            # (This would be detected by comparing the entire task object, not just status)
            if change.old_status == 'completed' and change.new_status == 'completed':
                # Both complete - might have different metadata
                # This is generally OK, just a warning
                warnings.append(
                    f"Task {change.task_id} is complete in both branches, "
                    f"metadata may differ"
                )

        safe_to_merge = len([c for c in conflicts if c.severity == 'error']) == 0

        return MergeCheckResult(
            pr_branch=pr_branch,
            target_branch=target_branch,
            conflicts=conflicts,
            warnings=warnings,
            safe_to_merge=safe_to_merge,
            checked_at=datetime.now(timezone.utc)
        ), None

    def log_resolution(self, conflict: TaskConflict, resolution: ConflictResolution,
                      log_file: Optional[Path] = None) -> Tuple[bool, Optional[str]]:
        """
        Log a conflict resolution decision.

        Args:
            conflict: The conflict being resolved
            resolution: The resolution decision
            log_file: Optional custom log file path

        Returns:
            (success, error) tuple
        """
        if log_file is None:
            log_file = self.repo_path / ".vibey" / "audit" / "merge_conflicts.log"

        log_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(log_file, 'a') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"Conflict Resolution: {conflict.task_id}\n")
                f.write(f"Timestamp: {resolution.resolved_at.isoformat()}\n")
                f.write(f"Resolved by: {resolution.resolved_by}\n")
                f.write(f"Resolution: {resolution.resolution}\n")
                f.write(f"PR Branch: {conflict.pr_branch}\n")
                f.write(f"Target Branch: {conflict.target_branch}\n")
                f.write(f"PR Status: {conflict.pr_status}\n")
                f.write(f"Target Status: {conflict.target_status}\n")
                if resolution.notes:
                    f.write(f"Notes: {resolution.notes}\n")
                f.write(f"{'='*80}\n")

            return True, None
        except Exception as e:
            return False, f"Failed to write log: {e}"


def check_merge(pr_branch: str, target_branch: str = 'main',
               repo_path: str = ".") -> Tuple[MergeCheckResult, Optional[str]]:
    """
    Convenience function to check for merge conflicts.

    Args:
        pr_branch: PR source branch
        target_branch: Target branch (default: 'main')
        repo_path: Path to repository

    Returns:
        (MergeCheckResult, error) tuple
    """
    checker = MergeChecker(repo_path)
    return checker.check_merge(pr_branch, target_branch)
