#!/usr/bin/env python3
"""
Add git commit to a task in the roadmap system.

Usage:
    python3 vibey/cli/roadmap-add-commit.py <task-id> <commit-sha> [options]
    python3 vibey/cli/roadmap-add-commit.py <task-id> --auto

Created: 2025-11-11
Purpose: Track git commits associated with roadmap tasks
"""

import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Tuple

# Add vibey to path
vibey_dir = Path(__file__).parent.parent
sys.path.insert(0, str(vibey_dir.parent))

import yaml

from vibey.roadmap.serialization.yaml_loader import load_task
from vibey.cli.roadmap_lib.filesystem import FileSystemManager, find_roadmap_root


def get_commit_info(commit_sha: str, repo_path: Path = None) -> Optional[Tuple[str, str, str, datetime]]:
    """
    Get commit information from git.

    Args:
        commit_sha: Git commit SHA (can be short form)
        repo_path: Path to git repository (default: current directory)

    Returns:
        Tuple of (full_sha, message, author, date) or None if commit not found
    """
    if repo_path is None:
        repo_path = Path.cwd()

    try:
        # Get full commit SHA
        result = subprocess.run(
            ['git', 'rev-parse', commit_sha],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        full_sha = result.stdout.strip()

        # Get commit message (first line only)
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%s', full_sha],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        message = result.stdout.strip()

        # Get commit author
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%an <%ae>', full_sha],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        author = result.stdout.strip()

        # Get commit date (ISO 8601 format)
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%aI', full_sha],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        date_str = result.stdout.strip()
        commit_date = datetime.fromisoformat(date_str)

        return (full_sha, message, author, commit_date)

    except subprocess.CalledProcessError as e:
        print(f"❌ Error: Could not find commit '{commit_sha}'")
        print(f"   Git error: {e.stderr.strip() if e.stderr else 'Unknown error'}")
        return None
    except Exception as e:
        print(f"❌ Error getting commit info: {e}")
        return None


def get_current_commit() -> Optional[str]:
    """
    Get the current HEAD commit SHA.

    Returns:
        Commit SHA or None if not in a git repository
    """
    try:
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def add_commit_to_task(
    task_id: str,
    commit_sha: str,
    vibey_path: Path = None,
    auto_detect: bool = False
) -> int:
    """
    Add a git commit to a task.

    Args:
        task_id: Task ID (e.g., 'infrastructure-fixes-1-task-005')
        commit_sha: Git commit SHA (or 'auto' to use current HEAD)
        vibey_path: Path to .vibey directory (auto-detected if None)
        auto_detect: If True, use current HEAD commit

    Returns:
        Exit code (0 = success, 1 = error)
    """
    # Auto-detect current commit if requested
    if auto_detect or commit_sha.lower() == 'auto':
        current_sha = get_current_commit()
        if not current_sha:
            print("❌ Error: Could not detect current commit (not in a git repository?)")
            return 1
        commit_sha = current_sha
        print(f"🔍 Auto-detected current commit: {commit_sha[:8]}")

    # Get commit information from git
    commit_info = get_commit_info(commit_sha)
    if not commit_info:
        return 1

    full_sha, message, author, commit_date = commit_info

    # Find project root (where .vibey/ is located)
    try:
        project_root = find_roadmap_root(vibey_path)
        if not project_root:
            raise FileNotFoundError("Could not find .vibey/roadmap.yaml")
        roadmap_dir = project_root / ".vibey" / "roadmap"
        fs = FileSystemManager(project_root)
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("\nMake sure you're in a Vibey-managed project (with .vibey/ directory).")
        return 1
    except Exception as e:
        print(f"❌ Error finding roadmap: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Find the task file using the hierarchical directory structure
    # Format: .vibey/roadmap/{track_id}/{sprint_id}/{task_id}/task.yaml

    # Parse task ID to extract track and sprint
    # Task ID format: {track}-{sprint}-task-{number}
    # Example: infrastructure-fixes-1-task-005
    parts = task_id.split('-task-')
    if len(parts) != 2:
        print(f"❌ Error: Invalid task ID format: {task_id}")
        print("   Expected format: <track>-<sprint>-task-<number>")
        return 1

    prefix = parts[0]  # infrastructure-fixes-1
    task_num = parts[1]  # 005

    # Find the task in the roadmap directory structure
    # We need to search for it since we don't know the exact track/sprint split
    task_path = None
    if not roadmap_dir.exists():
        print(f"❌ Error: Roadmap directory not found: {roadmap_dir}")
        return 1

    for track_dir in roadmap_dir.iterdir():
        if not track_dir.is_dir():
            continue
        for sprint_dir in track_dir.iterdir():
            if not sprint_dir.is_dir():
                continue
            task_dir = sprint_dir / task_id
            potential_path = task_dir / "task.yaml"
            if potential_path.exists():
                task_path = potential_path
                break
        if task_path:
            break

    if not task_path:
        print(f"❌ Error: Task file not found: {task_id}")
        print(f"   Searched in: {roadmap_dir}")
        return 1

    # Load the task - directly read the task.yaml file since it has {'task': {...}} format
    try:
        with open(task_path, 'r') as f:
            task_yaml = yaml.safe_load(f)

        if not task_yaml or 'task' not in task_yaml:
            raise ValueError("Invalid task file format - missing 'task' key")

        # For now, we'll work with the raw YAML data and just modify commits
        # We don't need to fully deserialize to Task object for this operation
        task_data = task_yaml['task']

    except Exception as e:
        print(f"❌ Error loading task: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Check if commit already exists
    existing_commits = task_data.get('commits', [])
    for existing_commit in existing_commits:
        if existing_commit.get('sha') == full_sha:
            print(f"⚠️  Warning: Commit {full_sha[:8]} already associated with task {task_id}")
            print(f"   Message: {message}")
            return 0

    # Add the new commit
    new_commit = {
        'sha': full_sha,
        'message': message,
        'author': author,
        'date': commit_date.isoformat(),
    }
    existing_commits.append(new_commit)
    task_data['commits'] = existing_commits

    # Update metadata last_updated
    task_data['metadata']['last_updated'] = datetime.now(timezone.utc).isoformat()

    # Save the updated task
    try:
        with open(task_path, 'w') as f:
            yaml.dump(task_yaml, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        print(f"✅ Successfully added commit to task {task_id}")
        print(f"   Commit: {full_sha[:8]}")
        print(f"   Message: {message}")
        print(f"   Author: {author}")
        print(f"   Date: {commit_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Total commits for this task: {len(existing_commits)}")
        return 0
    except Exception as e:
        print(f"❌ Error saving task: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Add git commit to a roadmap task',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add a specific commit to a task
  %(prog)s infrastructure-fixes-1-task-005 4367bc8

  # Add the current HEAD commit to a task
  %(prog)s infrastructure-fixes-1-task-005 --auto

  # Add a commit using full SHA
  %(prog)s infrastructure-fixes-1-task-005 4367bc8f1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p
        """
    )

    parser.add_argument(
        'task_id',
        help='Task ID (e.g., infrastructure-fixes-1-task-005)'
    )

    parser.add_argument(
        'commit_sha',
        nargs='?',
        default=None,
        help='Git commit SHA (full or short form, or "auto" to use current HEAD)'
    )

    parser.add_argument(
        '--auto',
        action='store_true',
        help='Use current HEAD commit (same as passing "auto" as commit_sha)'
    )

    parser.add_argument(
        '--vibey-dir',
        type=Path,
        default=None,
        help='Path to .vibey directory (auto-detected if not provided)'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.commit_sha and not args.auto:
        parser.error("Either provide commit_sha or use --auto flag")

    commit_sha = args.commit_sha or 'auto'

    # Execute
    return add_commit_to_task(
        task_id=args.task_id,
        commit_sha=commit_sha,
        vibey_path=args.vibey_dir,
        auto_detect=args.auto or commit_sha.lower() == 'auto'
    )


if __name__ == "__main__":
    sys.exit(main())
