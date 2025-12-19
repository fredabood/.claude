"""Post-mortem generation for completed tasks.

This module provides functions to generate post-mortems from relationship data
when tasks are completed. Post-mortems summarize:
- All commits linked to the ticket
- All artifacts changed by those commits
- Duration from task start to completion

Reference: Sprint 2 Task 9 (01KCMNEG4CXW4NK7W55VDMBXXM)
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import yaml


@dataclass
class PostMortemContext:
    """Post-mortem context for a completed task.

    Captures the summary of work done on a task including:
    - Timing information (when completed, duration)
    - Commits associated with the task
    - Artifacts that were changed
    - Key decisions made during implementation
    - Lessons learned and follow-up items
    """

    ticket_id: str
    completed_at: datetime
    duration_hours: Optional[float] = None
    summary: str = ""
    artifacts_changed: List[str] = field(default_factory=list)
    commits: List[str] = field(default_factory=list)
    key_decisions: List[str] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)
    follow_up_items: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert datetime to ISO format string
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data


def _get_ticket_commit_links(ticket_id: str) -> List[dict]:
    """Get all commit links for a ticket.

    This is a stub that will be replaced when the relationship
    entity models (TicketCommitLink) are fully implemented.

    For now, falls back to loading commits directly from the task.

    Args:
        ticket_id: The ticket/task ID

    Returns:
        List of commit link dictionaries with 'commit_sha' key
    """
    try:
        # Try to load from unified schema if available
        from vibey.roadmap.serialization.sql_loader import load_task_ticket
        task_ticket = load_task_ticket(ticket_id)
        if task_ticket and hasattr(task_ticket, 'commits'):
            return [{'commit_sha': c.sha} for c in (task_ticket.commits or [])]
    except Exception:
        pass

    try:
        # Fall back to loading from YAML
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager
        fs = FileSystemManager()
        roadmap_root = fs.roadmap_root

        task_path = roadmap_root / "tasks" / f"{ticket_id}.yaml"
        if task_path.exists():
            with open(task_path) as f:
                data = yaml.safe_load(f)
            task_data = data.get('task', data)
            commits = task_data.get('commits', [])
            return [{'commit_sha': c.get('sha', '')} for c in commits if c.get('sha')]
    except Exception:
        pass

    return []


def _get_commit_artifact_changes(commit_sha: str) -> List[dict]:
    """Get all artifact changes for a commit.

    This is a stub that will be replaced when the relationship
    entity models (CommitArtifactChange) are fully implemented.

    For now, returns an empty list as artifact tracking is not yet implemented.

    Args:
        commit_sha: The git commit SHA

    Returns:
        List of artifact change dictionaries with 'artifact_id' key
    """
    # TODO: Implement when CommitArtifactChange relationship entity is available
    # This would query the commit_artifact_changes table
    return []


def _get_task_data(ticket_id: str) -> Optional[dict]:
    """Load task data for timing information.

    Args:
        ticket_id: The ticket/task ID

    Returns:
        Dictionary with task data or None if not found
    """
    try:
        # Try SQL loader first
        from vibey.roadmap.serialization.sql_loader import load_task
        task = load_task(ticket_id)
        return {
            'started': task.started,
            'completed': task.completed,
            'title': task.title,
            'commits': task.commits,
        }
    except Exception:
        pass

    try:
        # Fall back to YAML
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager
        fs = FileSystemManager()
        roadmap_root = fs.roadmap_root

        task_path = roadmap_root / "tasks" / f"{ticket_id}.yaml"
        if task_path.exists():
            with open(task_path) as f:
                data = yaml.safe_load(f)
            task_data = data.get('task', data)

            # Parse datetime strings
            started = task_data.get('started')
            completed = task_data.get('completed')

            if isinstance(started, str):
                started = datetime.fromisoformat(started.replace('Z', '+00:00'))
            if isinstance(completed, str):
                completed = datetime.fromisoformat(completed.replace('Z', '+00:00'))

            return {
                'started': started,
                'completed': completed,
                'title': task_data.get('title', ''),
                'commits': task_data.get('commits', []),
            }
    except Exception:
        pass

    return None


def generate_post_mortem(ticket_id: str) -> PostMortemContext:
    """Generate post-mortem from relationship data.

    Collects:
    - All commits linked to ticket (via TicketCommitLink or task.commits)
    - All artifacts changed by those commits (via CommitArtifactChange)
    - Duration from task start to completion

    Args:
        ticket_id: The ID of the completed task

    Returns:
        PostMortemContext with collected data
    """
    # Get task data for timing info
    task_data = _get_task_data(ticket_id)

    # Get all commits linked to ticket
    commit_links = _get_ticket_commit_links(ticket_id)

    # Get all artifacts changed by those commits
    artifacts_changed = set()
    for link in commit_links:
        commit_sha = link.get('commit_sha', '')
        if commit_sha:
            changes = _get_commit_artifact_changes(commit_sha)
            artifacts_changed.update(c.get('artifact_id', '') for c in changes if c.get('artifact_id'))

    # Calculate duration
    duration_hours = None
    started = task_data.get('started') if task_data else None
    completed = task_data.get('completed') if task_data else None

    if started and completed:
        if isinstance(started, datetime) and isinstance(completed, datetime):
            delta = completed - started
            duration_hours = delta.total_seconds() / 3600

    # Use current time if completed is not set
    completed_at = completed if isinstance(completed, datetime) else datetime.now(timezone.utc)

    # Extract commit SHAs for the summary
    commit_shas = [link.get('commit_sha', '')[:7] for link in commit_links if link.get('commit_sha')]

    # Generate summary
    summary = f"Completed with {len(commit_links)} commits"
    if artifacts_changed:
        summary += f", {len(artifacts_changed)} artifacts changed"

    return PostMortemContext(
        ticket_id=ticket_id,
        completed_at=completed_at,
        duration_hours=duration_hours,
        summary=summary,
        artifacts_changed=list(artifacts_changed),
        commits=commit_shas,
        key_decisions=[],  # Can be populated from runtime context
        lessons_learned=[],
        follow_up_items=[]
    )


def save_post_mortem(ticket_id: str, post_mortem: PostMortemContext) -> Path:
    """Save post-mortem to YAML file.

    Post-mortems are saved to .vibey/context/post-mortems/{ticket_id}.yaml

    Args:
        ticket_id: The ticket/task ID
        post_mortem: The PostMortemContext to save

    Returns:
        Path to the saved post-mortem file
    """
    from vibey.cli.roadmap_lib.filesystem import FileSystemManager

    fs = FileSystemManager()

    # Create post-mortems directory under context
    context_dir = fs.vibey_dir / "context"
    post_mortem_dir = context_dir / "post-mortems"
    post_mortem_dir.mkdir(parents=True, exist_ok=True)

    file_path = post_mortem_dir / f"{ticket_id}.yaml"

    data = {"post_mortem": post_mortem.to_dict()}
    file_path.write_text(yaml.safe_dump(data, default_flow_style=False, sort_keys=False))

    return file_path


def auto_generate_on_complete(ticket_id: str) -> Optional[Path]:
    """Hook to auto-generate post-mortem when task is completed.

    This function is designed to be called from the task completion flow.
    It generates and saves a post-mortem, but catches all exceptions to
    avoid failing the task completion if post-mortem generation fails.

    Args:
        ticket_id: The ID of the completed task

    Returns:
        Path to the saved post-mortem file, or None if generation failed
    """
    try:
        post_mortem = generate_post_mortem(ticket_id)
        return save_post_mortem(ticket_id, post_mortem)
    except Exception as e:
        # Log but don't fail task completion
        print(f"Warning: Failed to generate post-mortem for {ticket_id}: {e}")
        return None


def load_post_mortem(ticket_id: str) -> Optional[PostMortemContext]:
    """Load a post-mortem from file.

    Args:
        ticket_id: The ticket/task ID

    Returns:
        PostMortemContext or None if not found
    """
    try:
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager

        fs = FileSystemManager()
        post_mortem_dir = fs.vibey_dir / "context" / "post-mortems"
        file_path = post_mortem_dir / f"{ticket_id}.yaml"

        if not file_path.exists():
            return None

        with open(file_path) as f:
            data = yaml.safe_load(f)

        pm_data = data.get('post_mortem', data)

        # Parse datetime
        completed_at = pm_data.get('completed_at')
        if isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
        elif not isinstance(completed_at, datetime):
            completed_at = datetime.now(timezone.utc)

        return PostMortemContext(
            ticket_id=pm_data.get('ticket_id', ticket_id),
            completed_at=completed_at,
            duration_hours=pm_data.get('duration_hours'),
            summary=pm_data.get('summary', ''),
            artifacts_changed=pm_data.get('artifacts_changed', []),
            commits=pm_data.get('commits', []),
            key_decisions=pm_data.get('key_decisions', []),
            lessons_learned=pm_data.get('lessons_learned', []),
            follow_up_items=pm_data.get('follow_up_items', []),
        )
    except Exception:
        return None
