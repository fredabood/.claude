"""
Commit evidence enforcement for task completion.

Ensures tasks have commit evidence before completion.
"""

import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml


@dataclass
class CommitEvidenceConfig:
    """Configuration for commit evidence requirements."""
    enabled: bool = True
    mode: str = "blocking"  # blocking, advisory, off
    require_commits: bool = True
    exception_task_types: List[str] = field(default_factory=lambda: ["documentation", "planning", "review"])


@dataclass
class EvidenceCheckResult:
    """Result of checking commit evidence for a task."""
    task_id: str
    has_evidence: bool
    commit_count: int
    commits: List[str] = field(default_factory=list)
    is_exception: bool = False
    exception_reason: Optional[str] = None
    can_complete: bool = True
    message: str = ""


def load_git_config(repo_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load git configuration from .vibey/config/git.yaml."""
    if repo_path is None:
        repo_path = Path.cwd()

    config_file = repo_path / ".vibey" / "config" / "git.yaml"

    if not config_file.exists():
        return {}

    try:
        with open(config_file, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def get_commit_evidence_config(repo_path: Optional[Path] = None) -> CommitEvidenceConfig:
    """Get commit evidence configuration."""
    config = load_git_config(repo_path)

    git_config = config.get('git', {})
    enforcement = git_config.get('enforcement', {})
    rules = enforcement.get('rules', {})
    commit_evidence = rules.get('commit_evidence', {})

    # Also check commit_tracking section
    commit_tracking = git_config.get('commit_tracking', {})

    return CommitEvidenceConfig(
        enabled=commit_evidence.get('enabled', True),
        mode=commit_evidence.get('mode', enforcement.get('mode', 'advisory')),
        require_commits=commit_tracking.get('require_commits', commit_evidence.get('require_commits', False)),
        exception_task_types=commit_evidence.get('exceptions', {}).get('task_types',
                                                                        ["documentation", "planning", "review"])
    )


def get_task_commits(task_id: str, repo_path: Optional[Path] = None) -> List[str]:
    """
    Get commits associated with a task.

    Checks both:
    1. Commits stored in task.yaml
    2. Commits in git log that reference the task
    """
    if repo_path is None:
        repo_path = Path.cwd()

    commits = []

    # Method 1: Check task.yaml for stored commits
    task_commits = get_task_yaml_commits(task_id, repo_path)
    commits.extend(task_commits)

    # Method 2: Search git log for task references
    git_commits = find_commits_referencing_task(task_id, repo_path)
    for sha in git_commits:
        if sha not in commits:
            commits.append(sha)

    return commits


def get_task_yaml_commits(task_id: str, repo_path: Path) -> List[str]:
    """Get commits stored in task.yaml."""
    # Extract sprint ID
    if '-task-' not in task_id:
        return []

    sprint_id = task_id.split('-task-')[0]

    # Build path: .vibey/roadmap/<track>/<sprint>/<task>/task.yaml
    # We need to find the track from the sprint ID
    roadmap_root = repo_path / ".vibey" / "roadmap"
    if not roadmap_root.exists():
        return []

    # Search for the task file
    for track_dir in roadmap_root.iterdir():
        if not track_dir.is_dir() or track_dir.name.startswith('.'):
            continue

        sprint_dir = track_dir / sprint_id
        if sprint_dir.exists():
            task_dir = sprint_dir / task_id
            task_file = task_dir / "task.yaml"

            if task_file.exists():
                try:
                    with open(task_file, 'r') as f:
                        task_data = yaml.safe_load(f)
                        if task_data and 'task' in task_data:
                            commits = task_data['task'].get('commits', [])
                            # Extract SHAs from commit objects
                            return [c.get('sha', c) if isinstance(c, dict) else c
                                    for c in commits]
                except Exception:
                    pass

    return []


def find_commits_referencing_task(task_id: str, repo_path: Path) -> List[str]:
    """Find commits in git log that reference a task ID."""
    try:
        # Search git log for task ID in commit messages
        result = subprocess.run(
            ['git', 'log', '--all', '--oneline', f'--grep={task_id}', '--format=%H'],
            cwd=repo_path,
            capture_output=True,
            text=True
        )

        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split('\n')
    except Exception:
        pass

    return []


def get_task_type(task_id: str, repo_path: Path) -> Optional[str]:
    """Get the task type from task.yaml."""
    if '-task-' not in task_id:
        return None

    sprint_id = task_id.split('-task-')[0]
    roadmap_root = repo_path / ".vibey" / "roadmap"

    if not roadmap_root.exists():
        return None

    for track_dir in roadmap_root.iterdir():
        if not track_dir.is_dir() or track_dir.name.startswith('.'):
            continue

        sprint_dir = track_dir / sprint_id
        if sprint_dir.exists():
            task_dir = sprint_dir / task_id
            task_file = task_dir / "task.yaml"

            if task_file.exists():
                try:
                    with open(task_file, 'r') as f:
                        task_data = yaml.safe_load(f)
                        if task_data and 'task' in task_data:
                            return task_data['task'].get('task_type')
                except Exception:
                    pass

    return None


def check_commit_evidence(
    task_id: str,
    repo_path: Optional[Path] = None
) -> EvidenceCheckResult:
    """
    Check if a task has commit evidence for completion.

    Returns an EvidenceCheckResult indicating whether the task
    can be completed based on commit evidence requirements.
    """
    if repo_path is None:
        repo_path = Path.cwd()

    config = get_commit_evidence_config(repo_path)

    # If enforcement is off, always allow
    if not config.enabled or config.mode == "off":
        return EvidenceCheckResult(
            task_id=task_id,
            has_evidence=True,
            commit_count=0,
            can_complete=True,
            message="Commit evidence enforcement is disabled"
        )

    # Check for exception task types
    task_type = get_task_type(task_id, repo_path)
    if task_type and task_type in config.exception_task_types:
        return EvidenceCheckResult(
            task_id=task_id,
            has_evidence=True,
            commit_count=0,
            is_exception=True,
            exception_reason=f"Task type '{task_type}' is exempt from commit requirements",
            can_complete=True,
            message=f"Task type '{task_type}' does not require commits"
        )

    # Get commits for the task
    commits = get_task_commits(task_id, repo_path)
    has_evidence = len(commits) > 0

    # Determine if completion is allowed
    if config.require_commits and not has_evidence:
        if config.mode == "blocking":
            return EvidenceCheckResult(
                task_id=task_id,
                has_evidence=False,
                commit_count=0,
                commits=[],
                can_complete=False,
                message=f"Task '{task_id}' has no commits. Add commits before completing:\n"
                        f"  vibey roadmap add-commit {task_id} <sha>\n"
                        f"Or mark as non-code task with --no-commits flag."
            )
        else:  # advisory mode
            return EvidenceCheckResult(
                task_id=task_id,
                has_evidence=False,
                commit_count=0,
                commits=[],
                can_complete=True,
                message=f"⚠️  Warning: Task '{task_id}' has no commits linked."
            )

    return EvidenceCheckResult(
        task_id=task_id,
        has_evidence=has_evidence,
        commit_count=len(commits),
        commits=commits,
        can_complete=True,
        message=f"Task has {len(commits)} commit(s) linked"
    )


def sync_commits_from_git(
    repo_path: Optional[Path] = None,
    dry_run: bool = False
) -> Dict[str, List[str]]:
    """
    Scan git history and link commits to tasks based on commit messages.

    Returns a dict mapping task_id -> list of commit SHAs found.
    """
    if repo_path is None:
        repo_path = Path.cwd()

    found_commits: Dict[str, List[str]] = {}

    try:
        # Get all commit messages with task references
        result = subprocess.run(
            ['git', 'log', '--all', '--format=%H|%s'],
            cwd=repo_path,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return found_commits

        import re
        # Pattern to find task IDs in commit messages
        task_pattern = re.compile(r'([\w-]+-task-\d+)')

        for line in result.stdout.strip().split('\n'):
            if '|' not in line:
                continue

            sha, message = line.split('|', 1)
            matches = task_pattern.findall(message)

            for task_id in matches:
                if task_id not in found_commits:
                    found_commits[task_id] = []
                if sha not in found_commits[task_id]:
                    found_commits[task_id].append(sha)

    except Exception:
        pass

    return found_commits


def validate_all_tasks_have_commits(
    repo_path: Optional[Path] = None
) -> List[EvidenceCheckResult]:
    """
    Validate that all completed tasks have commit evidence.

    Returns list of tasks missing commits.
    """
    if repo_path is None:
        repo_path = Path.cwd()

    issues = []
    roadmap_root = repo_path / ".vibey" / "roadmap"

    if not roadmap_root.exists():
        return issues

    # Find all completed tasks
    for track_dir in roadmap_root.iterdir():
        if not track_dir.is_dir() or track_dir.name.startswith('.'):
            continue

        for sprint_dir in track_dir.iterdir():
            if not sprint_dir.is_dir() or sprint_dir.name.startswith('.') or sprint_dir.name == 'context':
                continue

            for task_dir in sprint_dir.iterdir():
                if not task_dir.is_dir() or task_dir.name.startswith('.') or task_dir.name == 'context':
                    continue

                task_file = task_dir / "task.yaml"
                if not task_file.exists():
                    continue

                try:
                    with open(task_file, 'r') as f:
                        task_data = yaml.safe_load(f)
                        if task_data and 'task' in task_data:
                            task = task_data['task']
                            if task.get('status') == 'completed':
                                result = check_commit_evidence(task['id'], repo_path)
                                if not result.has_evidence and not result.is_exception:
                                    issues.append(result)
                except Exception:
                    pass

    return issues
