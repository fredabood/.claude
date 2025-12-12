"""
Session-aware git hooks for Vibey.

Provides functions to integrate session tracking with git operations:
- Recording commits to active sessions
- Warning about active sessions on push
- Session context in commit messages

Sprint 3.2: Git Versioning for Vibe Coding Sessions
Task 6: Git Hook Integration
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def get_session_manager(repo_path: Path):
    """
    Get a SessionManager instance for the repository.

    Args:
        repo_path: Path to repository root

    Returns:
        SessionManager or None if not available
    """
    try:
        from vibey.operations.roadmap.session_manager import SessionManager
        roadmap_path = repo_path / ".vibey" / "roadmap"
        if roadmap_path.exists():
            return SessionManager(roadmap_path)
    except ImportError:
        logger.debug("SessionManager not available")
    except Exception as e:
        logger.debug(f"Could not create SessionManager: {e}")
    return None


def on_post_commit(repo_path: Path, commit_sha: str, message: str) -> bool:
    """
    Handle post-commit hook for session tracking.

    Associates the commit with any active session and logs the commit event.

    Args:
        repo_path: Path to repository root
        commit_sha: Full commit SHA
        message: Commit message

    Returns:
        True if commit was associated with a session, False otherwise
    """
    try:
        manager = get_session_manager(repo_path)
        if not manager:
            return False

        session = manager.get_active_session()
        if not session:
            return False

        # Associate commit with session
        manager.associate_commit(
            commit_sha=commit_sha,
            message=message,
        )

        logger.info(f"Associated commit {commit_sha[:8]} with session {session.id}")
        return True

    except Exception as e:
        logger.warning(f"Failed to associate commit with session: {e}")
        return False


def on_pre_push(repo_path: Path) -> Optional[Dict[str, Any]]:
    """
    Handle pre-push hook for session tracking.

    Checks for active sessions and returns warning info if found.

    Args:
        repo_path: Path to repository root

    Returns:
        Dictionary with session info if active session exists, None otherwise
    """
    try:
        manager = get_session_manager(repo_path)
        if not manager:
            return None

        session = manager.get_active_session()
        if not session:
            return None

        return {
            "session_id": session.id,
            "session_name": session.name,
            "started": session.started.isoformat() if session.started else None,
            "goals": session.goals,
            "events_count": len(session.events),
            "commits_count": len(session.commits),
            "branch": session.branch,
        }

    except Exception as e:
        logger.warning(f"Failed to check active session: {e}")
        return None


def enhance_commit_message(repo_path: Path, message: str) -> str:
    """
    Add session reference to commit message if session is active.

    Args:
        repo_path: Path to repository root
        message: Original commit message

    Returns:
        Enhanced commit message with session reference
    """
    try:
        manager = get_session_manager(repo_path)
        if not manager:
            return message

        session = manager.get_active_session()
        if not session:
            return message

        # Don't add if already has session reference
        if f"Session: {session.id}" in message:
            return message

        return f"{message}\n\nSession: {session.id}"

    except Exception as e:
        logger.warning(f"Failed to enhance commit message: {e}")
        return message


def print_active_session_warning(session_info: Dict[str, Any]) -> None:
    """
    Print a warning about pushing with an active session.

    Args:
        session_info: Dictionary with session information
    """
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    print()
    print(f"{BOLD}{YELLOW}[vibey] Active session detected!{RESET}")
    print()
    print(f"  Session: {session_info['session_name']} ({session_info['session_id'][:8]}...)")
    if session_info.get('started'):
        print(f"  Started: {session_info['started']}")
    if session_info.get('events_count'):
        print(f"  Events: {session_info['events_count']}")
    if session_info.get('commits_count'):
        print(f"  Commits: {session_info['commits_count']}")
    print()
    print(f"  {BOLD}Consider ending your session before pushing:{RESET}")
    print(f"    {CYAN}vibey session end --summary \"...description...\"{RESET}")
    print()
    print(f"  Or continue pushing with the session active.")
    print()


def get_commit_info_for_session(repo_path: Path, commit_sha: str) -> Optional[Dict[str, Any]]:
    """
    Get commit information suitable for session recording.

    Args:
        repo_path: Path to repository root
        commit_sha: Commit SHA to get info for

    Returns:
        Dictionary with commit info or None on error
    """
    import subprocess

    try:
        # Get commit details
        result = subprocess.run(
            ["git", "-C", str(repo_path), "show", "--no-patch",
             "--format=%H%n%h%n%aI%n%s%n%aN", commit_sha],
            capture_output=True, text=True
        )

        if result.returncode != 0:
            return None

        lines = result.stdout.strip().split("\n")
        if len(lines) < 5:
            return None

        # Get diff stats
        stats_result = subprocess.run(
            ["git", "-C", str(repo_path), "show", "--stat", "--format=",
             commit_sha],
            capture_output=True, text=True
        )

        files_changed = 0
        insertions = 0
        deletions = 0

        if stats_result.returncode == 0 and stats_result.stdout.strip():
            # Parse stat line like "3 files changed, 10 insertions(+), 5 deletions(-)"
            stat_line = stats_result.stdout.strip().split("\n")[-1]
            import re
            files_match = re.search(r'(\d+) files? changed', stat_line)
            ins_match = re.search(r'(\d+) insertions?', stat_line)
            del_match = re.search(r'(\d+) deletions?', stat_line)

            if files_match:
                files_changed = int(files_match.group(1))
            if ins_match:
                insertions = int(ins_match.group(1))
            if del_match:
                deletions = int(del_match.group(1))

        return {
            "commit_sha": lines[0],
            "short_sha": lines[1],
            "timestamp": lines[2],
            "message": lines[3],
            "author": lines[4],
            "files_changed": files_changed,
            "insertions": insertions,
            "deletions": deletions,
        }

    except Exception as e:
        logger.warning(f"Failed to get commit info: {e}")
        return None
