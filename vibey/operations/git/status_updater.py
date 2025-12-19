"""
Automatic Task Status Updater

Updates task status in roadmap YAML files based on commit messages.

Task: git-integration-2-task-004
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone

from vibey.operations.git.commit_parser import CommitParser, TaskStatus


@dataclass
class StatusUpdate:
    """Represents a status update to be applied."""
    task_id: str
    old_status: str
    new_status: str
    commit_sha: str
    commit_message: str
    file_path: Path
    sprint_id: str
    applied: bool = False
    error: Optional[str] = None


@dataclass
class UpdateResult:
    """Result of applying status updates."""
    total_updates: int
    successful_updates: int
    failed_updates: int
    skipped_updates: int
    updates: List[StatusUpdate]
    errors: List[str]


class TaskStatusUpdater:
    """
    Automatically update task status based on commit messages.

    Parses commit messages for status indicators (completes, starts, blocks)
    and updates the corresponding task YAML files.
    """

    def __init__(self, repo_path: str = "."):
        """
        Initialize status updater.

        Args:
            repo_path: Path to repository root
        """
        self.repo_path = Path(repo_path).resolve()
        self.roadmap_dir = self.repo_path / ".vibey" / "roadmap"
        self.parser = CommitParser()

    def find_task_file(self, task_id: str) -> Optional[Path]:
        """
        Find the YAML file for a specific task.

        Uses direct ULID-based lookup in the flat tasks directory structure.

        Args:
            task_id: Task ULID to search for

        Returns:
            Path to task.yaml file, or None if not found
        """
        if not self.roadmap_dir.exists():
            return None

        # Direct ULID lookup in flat tasks directory (per ADR-0001, ADR-0002)
        tasks_dir = self.roadmap_dir / "tasks"
        if tasks_dir.exists():
            task_file = tasks_dir / f"{task_id}.yaml"
            if task_file.exists():
                return task_file

        return None

    def get_task_from_file(self, file_path: Path, task_id: str) -> Optional[Dict]:
        """
        Load a specific task from a YAML file.

        Args:
            file_path: Path to task.yaml file
            task_id: Task ULID to load

        Returns:
            Task dictionary, or None if not found
        """
        try:
            with open(file_path) as f:
                data = yaml.safe_load(f)

            # Standalone task file format (per ADR-0002)
            if "task" in data:
                task = data["task"]
                if task.get("id") == task_id:
                    return task

        except Exception:
            pass

        return None

    def update_task_in_file(
        self,
        file_path: Path,
        task_id: str,
        new_status: str,
        commit_sha: str,
        dry_run: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Update task status in a YAML file.

        Args:
            file_path: Path to task.yaml file
            task_id: Task ULID to update
            new_status: New status to set
            commit_sha: Commit SHA to record
            dry_run: If True, don't actually write changes

        Returns:
            Tuple of (success, error_message)
        """
        try:
            with open(file_path) as f:
                data = yaml.safe_load(f)

            # Standalone task file format (per ADR-0002)
            if "task" not in data:
                return False, f"Invalid task file format: {file_path}"

            task = data["task"]
            if task.get("id") != task_id:
                return False, f"Task {task_id} not found in file"

            # Update task
            task["status"] = new_status

            # Add commit to commits list
            if "commits" not in task:
                task["commits"] = []
            if commit_sha not in task["commits"]:
                task["commits"].append(commit_sha)

            # Update timestamps
            if new_status == "completed" and task.get("completed") is None:
                task["completed"] = datetime.now(timezone.utc).isoformat()
            if new_status == "in_progress" and task.get("started") is None:
                task["started"] = datetime.now(timezone.utc).isoformat()

            # Write changes
            if not dry_run:
                with open(file_path, 'w') as f:
                    yaml.dump(data, f, default_flow_style=False, sort_keys=False)

            return True, None

        except Exception as e:
            return False, str(e)

    def process_commit(
        self,
        commit_sha: str,
        commit_message: str,
        dry_run: bool = False,
        force: bool = False
    ) -> UpdateResult:
        """
        Process a commit message and apply status updates.

        Args:
            commit_sha: Commit SHA
            commit_message: Commit message text
            dry_run: If True, don't actually apply changes
            force: If True, allow updates even if task is already in target status

        Returns:
            UpdateResult with details of updates applied
        """
        updates = []
        errors = []
        successful = 0
        failed = 0
        skipped = 0

        # Parse commit message
        parsed = self.parser.parse(commit_message, commit_sha)

        if not parsed.has_task_reference:
            return UpdateResult(
                total_updates=0,
                successful_updates=0,
                failed_updates=0,
                skipped_updates=0,
                updates=[],
                errors=["No task references found in commit message"]
            )

        # Process each task reference
        for task_ref in parsed.tasks:
            task_id = task_ref.task_id

            # Determine target status from commit message
            target_status = None
            if task_ref.status:
                if task_ref.status == TaskStatus.COMPLETED:
                    target_status = "completed"
                elif task_ref.status == TaskStatus.IN_PROGRESS:
                    target_status = "in_progress"
                elif task_ref.status == TaskStatus.BLOCKED:
                    target_status = "blocked"

            if not target_status:
                skipped += 1
                updates.append(StatusUpdate(
                    task_id=task_id,
                    old_status="unknown",
                    new_status="none",
                    commit_sha=commit_sha,
                    commit_message=commit_message.split('\n')[0],
                    file_path=Path("unknown"),
                    sprint_id="unknown",
                    applied=False,
                    error="No status indicator in commit message"
                ))
                continue

            # Find task file
            task_file = self.find_task_file(task_id)

            if not task_file:
                failed += 1
                error = f"Task {task_id} not found in roadmap"
                errors.append(error)
                updates.append(StatusUpdate(
                    task_id=task_id,
                    old_status="unknown",
                    new_status=target_status,
                    commit_sha=commit_sha,
                    commit_message=commit_message.split('\n')[0],
                    file_path=Path("unknown"),
                    sprint_id="unknown",
                    applied=False,
                    error=error
                ))
                continue

            # Load current task
            task = self.get_task_from_file(task_file, task_id)

            if not task:
                failed += 1
                error = f"Could not load task {task_id}"
                errors.append(error)
                updates.append(StatusUpdate(
                    task_id=task_id,
                    old_status="unknown",
                    new_status=target_status,
                    commit_sha=commit_sha,
                    commit_message=commit_message.split('\n')[0],
                    file_path=task_file,
                    sprint_id="unknown",
                    applied=False,
                    error=error
                ))
                continue

            old_status = task.get("status", "not_started")

            # Check if already in target status
            if old_status == target_status and not force:
                skipped += 1
                updates.append(StatusUpdate(
                    task_id=task_id,
                    old_status=old_status,
                    new_status=target_status,
                    commit_sha=commit_sha,
                    commit_message=commit_message.split('\n')[0],
                    file_path=task_file,
                    sprint_id=task_file.parent.name,
                    applied=False,
                    error=f"Task already {target_status}"
                ))
                continue

            # Validate transition
            if old_status == "completed" and target_status != "completed" and not force:
                skipped += 1
                updates.append(StatusUpdate(
                    task_id=task_id,
                    old_status=old_status,
                    new_status=target_status,
                    commit_sha=commit_sha,
                    commit_message=commit_message.split('\n')[0],
                    file_path=task_file,
                    sprint_id=task_file.parent.name,
                    applied=False,
                    error="Cannot change status of completed task (use --force to override)"
                ))
                continue

            # Apply update
            success, error = self.update_task_in_file(
                task_file,
                task_id,
                target_status,
                commit_sha,
                dry_run=dry_run
            )

            if success:
                successful += 1
                updates.append(StatusUpdate(
                    task_id=task_id,
                    old_status=old_status,
                    new_status=target_status,
                    commit_sha=commit_sha,
                    commit_message=commit_message.split('\n')[0],
                    file_path=task_file,
                    sprint_id=task_file.parent.name,
                    applied=not dry_run,
                    error=None
                ))
            else:
                failed += 1
                errors.append(f"{task_id}: {error}")
                updates.append(StatusUpdate(
                    task_id=task_id,
                    old_status=old_status,
                    new_status=target_status,
                    commit_sha=commit_sha,
                    commit_message=commit_message.split('\n')[0],
                    file_path=task_file,
                    sprint_id=task_file.parent.name,
                    applied=False,
                    error=error
                ))

        return UpdateResult(
            total_updates=len(updates),
            successful_updates=successful,
            failed_updates=failed,
            skipped_updates=skipped,
            updates=updates,
            errors=errors
        )

    def process_recent_commits(
        self,
        max_count: int = 10,
        dry_run: bool = False,
        force: bool = False
    ) -> UpdateResult:
        """
        Process recent commits for status updates.

        Args:
            max_count: Maximum number of commits to process
            dry_run: If True, don't actually apply changes
            force: If True, allow updates even if task already in target status

        Returns:
            UpdateResult with aggregated results
        """
        from vibey.operations.git import GitLogAnalyzer

        analyzer = GitLogAnalyzer(repo_path=str(self.repo_path))

        if not analyzer.is_git_repo():
            return UpdateResult(
                total_updates=0,
                successful_updates=0,
                failed_updates=0,
                skipped_updates=0,
                updates=[],
                errors=["Not a git repository"]
            )

        # Get recent commits
        commits = analyzer.get_commits(max_count=max_count)

        # Aggregate results
        all_updates = []
        all_errors = []
        total_successful = 0
        total_failed = 0
        total_skipped = 0

        for commit in commits:
            result = self.process_commit(
                commit.sha,
                commit.message,
                dry_run=dry_run,
                force=force
            )

            all_updates.extend(result.updates)
            all_errors.extend(result.errors)
            total_successful += result.successful_updates
            total_failed += result.failed_updates
            total_skipped += result.skipped_updates

        return UpdateResult(
            total_updates=len(all_updates),
            successful_updates=total_successful,
            failed_updates=total_failed,
            skipped_updates=total_skipped,
            updates=all_updates,
            errors=all_errors
        )


def update_from_commit(
    commit_sha: str,
    commit_message: str,
    repo_path: str = ".",
    dry_run: bool = False,
    force: bool = False
) -> UpdateResult:
    """
    Convenience function to update task status from a single commit.

    Args:
        commit_sha: Commit SHA
        commit_message: Commit message
        repo_path: Repository path
        dry_run: If True, don't apply changes
        force: If True, allow updates even if already in target status

    Returns:
        UpdateResult
    """
    updater = TaskStatusUpdater(repo_path)
    return updater.process_commit(commit_sha, commit_message, dry_run, force)


def update_from_recent_commits(
    repo_path: str = ".",
    max_count: int = 10,
    dry_run: bool = False,
    force: bool = False
) -> UpdateResult:
    """
    Convenience function to process recent commits.

    Args:
        repo_path: Repository path
        max_count: Maximum commits to process
        dry_run: If True, don't apply changes
        force: If True, allow updates even if already in target status

    Returns:
        UpdateResult
    """
    updater = TaskStatusUpdater(repo_path)
    return updater.process_recent_commits(max_count, dry_run, force)
