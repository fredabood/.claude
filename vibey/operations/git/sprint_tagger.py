"""
Sprint tagging system for marking sprint boundaries in git history.

This module implements git tag management for sprint start/end markers,
which are used by velocity calculators and state reconstruction queries
to determine sprint commit ranges.

TAG FORMAT:
- sprint/<sprint-id>/start - Marks sprint beginning
- sprint/<sprint-id>/end - Marks sprint completion

Example: sprint/git-integration-2/start
"""

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
import yaml


@dataclass
class SprintTag:
    """Information about a sprint tag."""
    tag_name: str
    sprint_id: str
    tag_type: str  # 'start' or 'end'
    commit_sha: str
    tagger_name: str
    tagger_email: str
    tag_date: datetime
    message: str


class SprintTagger:
    """
    Manage sprint boundary tags in git repository.

    Sprint tags mark the beginning and end of sprints in git history,
    enabling accurate velocity calculations and state reconstruction.
    """

    def __init__(self, repo_path: Optional[str] = None):
        """
        Initialize sprint tagger.

        Args:
            repo_path: Path to git repository (default: current directory)
        """
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self.git_dir = self.repo_path / ".git"

        if not self.git_dir.exists():
            raise ValueError(f"Not a git repository: {self.repo_path}")

    def _run_git(self, *args, check: bool = True, capture_output: bool = True) -> subprocess.CompletedProcess:
        """
        Run a git command.

        Args:
            *args: Git command arguments
            check: Raise exception on non-zero exit code
            capture_output: Capture stdout/stderr

        Returns:
            CompletedProcess result
        """
        cmd = ["git"] + list(args)
        return subprocess.run(
            cmd,
            cwd=self.repo_path,
            check=check,
            capture_output=capture_output,
            text=True
        )

    def _get_current_commit(self) -> str:
        """
        Get SHA of current HEAD commit.

        Returns:
            Commit SHA

        Raises:
            RuntimeError: If HEAD cannot be resolved
        """
        result = self._run_git("rev-parse", "HEAD")
        return result.stdout.strip()

    def _tag_exists(self, tag_name: str) -> bool:
        """
        Check if a tag exists.

        Args:
            tag_name: Tag name to check

        Returns:
            True if tag exists, False otherwise
        """
        result = self._run_git("tag", "-l", tag_name, check=False)
        return bool(result.stdout.strip())

    def _format_tag_name(self, sprint_id: str, tag_type: str) -> str:
        """
        Format sprint tag name.

        Args:
            sprint_id: Sprint identifier
            tag_type: 'start' or 'end'

        Returns:
            Formatted tag name: sprint/<sprint-id>/start
        """
        if tag_type not in ('start', 'end'):
            raise ValueError(f"Invalid tag type: {tag_type}. Must be 'start' or 'end'")

        return f"sprint/{sprint_id}/{tag_type}"

    def _load_sprint_metadata(self, sprint_id: str) -> Optional[Dict[str, Any]]:
        """
        Load sprint metadata from roadmap YAML using flat structure.

        Args:
            sprint_id: Sprint identifier

        Returns:
            Sprint metadata dict, or None if not found
        """
        roadmap_dir = self.repo_path / ".vibey" / "roadmap"
        if not roadmap_dir.exists():
            return None

        # Direct lookup in flat sprints/ directory
        sprint_file = roadmap_dir / "sprints" / f"{sprint_id}.yaml"
        if sprint_file.exists():
            try:
                with open(sprint_file, 'r') as f:
                    data = yaml.safe_load(f)
                    sprint = data.get('sprint', {})
                    if sprint.get('id') == sprint_id:
                        return sprint
            except Exception:
                pass

        # Fallback: scan sprints directory for matching ID
        sprints_dir = roadmap_dir / "sprints"
        if sprints_dir.exists():
            for sprint_file in sprints_dir.glob("*.yaml"):
                if sprint_file.name.startswith('.'):
                    continue
                try:
                    with open(sprint_file, 'r') as f:
                        data = yaml.safe_load(f)
                        sprint = data.get('sprint', {})
                        if sprint.get('id') == sprint_id:
                            return sprint
                except Exception:
                    continue

        return None

    def _format_tag_message(self, sprint_id: str, tag_type: str) -> str:
        """
        Format annotated tag message with sprint metadata.

        Args:
            sprint_id: Sprint identifier
            tag_type: 'start' or 'end'

        Returns:
            Tag message with sprint metadata
        """
        sprint = self._load_sprint_metadata(sprint_id)

        if sprint:
            sprint_name = sprint.get('name', 'Unknown Sprint')
            track_id = sprint.get('track_id', 'unknown')

            if tag_type == 'start':
                message = f"Sprint Start: {sprint_name}\n\n"
                message += f"Sprint ID: {sprint_id}\n"
                message += f"Track: {track_id}\n"
                message += f"Status: {sprint.get('status', 'not_started')}\n"
                message += f"Estimated Duration: {sprint.get('estimated_duration', 'N/A')}\n"
                message += f"Tasks: {sprint.get('progress', {}).get('tasks_total', 0)}\n"
            else:
                message = f"Sprint Complete: {sprint_name}\n\n"
                message += f"Sprint ID: {sprint_id}\n"
                message += f"Track: {track_id}\n"
                progress = sprint.get('progress', {})
                message += f"Tasks Completed: {progress.get('tasks_completed', 0)}/{progress.get('tasks_total', 0)}\n"
                message += f"Completion: {progress.get('completion_percent', 0)}%\n"
        else:
            message = f"Sprint {tag_type.capitalize()}: {sprint_id}\n\n"
            message += f"Sprint ID: {sprint_id}\n"
            message += "Note: Sprint metadata not found in roadmap\n"

        message += f"\nTagged: {datetime.now(timezone.utc).isoformat()}\n"
        return message

    def create_sprint_tag(
        self,
        sprint_id: str,
        tag_type: str,
        commit: Optional[str] = None,
        force: bool = False,
        push: bool = False,
        remote: str = "origin"
    ) -> Tuple[bool, Optional[str]]:
        """
        Create a sprint boundary tag.

        Args:
            sprint_id: Sprint identifier
            tag_type: 'start' or 'end'
            commit: Commit SHA to tag (default: HEAD)
            force: Overwrite existing tag
            push: Push tag to remote
            remote: Remote name (default: 'origin')

        Returns:
            (success, error_message)
        """
        # Format tag name
        tag_name = self._format_tag_name(sprint_id, tag_type)

        # Check if tag exists
        if self._tag_exists(tag_name) and not force:
            return False, f"Tag '{tag_name}' already exists. Use --force to overwrite."

        # Get commit to tag
        if not commit:
            try:
                commit = self._get_current_commit()
            except Exception as e:
                return False, f"Failed to get current commit: {e}"

        # Format tag message
        message = self._format_tag_message(sprint_id, tag_type)

        # Create annotated tag
        try:
            args = ["tag", "-a", tag_name, commit, "-m", message]
            if force:
                args.insert(1, "-f")

            self._run_git(*args)
        except subprocess.CalledProcessError as e:
            return False, f"Failed to create tag: {e.stderr}"

        # Push tag if requested
        if push:
            try:
                self._run_git("push", remote, tag_name, "--force" if force else "--no-force")
            except subprocess.CalledProcessError as e:
                return False, f"Tag created but push failed: {e.stderr}"

        return True, None

    def delete_sprint_tag(
        self,
        sprint_id: str,
        tag_type: str,
        push: bool = False,
        remote: str = "origin"
    ) -> Tuple[bool, Optional[str]]:
        """
        Delete a sprint boundary tag.

        Args:
            sprint_id: Sprint identifier
            tag_type: 'start' or 'end'
            push: Delete tag from remote
            remote: Remote name (default: 'origin')

        Returns:
            (success, error_message)
        """
        tag_name = self._format_tag_name(sprint_id, tag_type)

        # Check if tag exists
        if not self._tag_exists(tag_name):
            return False, f"Tag '{tag_name}' does not exist"

        # Delete local tag
        try:
            self._run_git("tag", "-d", tag_name)
        except subprocess.CalledProcessError as e:
            return False, f"Failed to delete tag: {e.stderr}"

        # Delete remote tag if requested
        if push:
            try:
                self._run_git("push", remote, "--delete", tag_name)
            except subprocess.CalledProcessError as e:
                return False, f"Local tag deleted but remote delete failed: {e.stderr}"

        return True, None

    def list_sprint_tags(self, sprint_id: Optional[str] = None) -> List[SprintTag]:
        """
        List all sprint tags or tags for specific sprint.

        Args:
            sprint_id: Filter by sprint ID (optional)

        Returns:
            List of SprintTag objects
        """
        # Get all tags matching sprint/* pattern
        pattern = f"sprint/{sprint_id}/*" if sprint_id else "sprint/*"

        try:
            result = self._run_git("tag", "-l", pattern)
            tag_names = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        except subprocess.CalledProcessError:
            return []

        sprint_tags = []

        for tag_name in tag_names:
            # Parse tag name
            parts = tag_name.split('/')
            if len(parts) != 3:
                continue

            _, tag_sprint_id, tag_type = parts

            # Get tag info
            try:
                # Get commit SHA
                sha_result = self._run_git("rev-list", "-n", "1", tag_name)
                commit_sha = sha_result.stdout.strip()

                # Get tag message and metadata
                show_result = self._run_git("show", tag_name, "--format=%an%n%ae%n%aI%n%B", "--no-patch")
                lines = show_result.stdout.splitlines()

                if len(lines) >= 4:
                    tagger_name = lines[0]
                    tagger_email = lines[1]
                    tag_date_str = lines[2]
                    message = '\n'.join(lines[3:])

                    try:
                        tag_date = datetime.fromisoformat(tag_date_str.replace('Z', '+00:00'))
                    except ValueError:
                        tag_date = datetime.now(timezone.utc)

                    sprint_tags.append(SprintTag(
                        tag_name=tag_name,
                        sprint_id=tag_sprint_id,
                        tag_type=tag_type,
                        commit_sha=commit_sha,
                        tagger_name=tagger_name,
                        tagger_email=tagger_email,
                        tag_date=tag_date,
                        message=message
                    ))
            except Exception:
                # Skip tags we can't parse
                continue

        # Sort by date
        sprint_tags.sort(key=lambda t: t.tag_date)

        return sprint_tags

    def get_sprint_commit_range(self, sprint_id: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Get commit range for a sprint (start tag to end tag).

        Args:
            sprint_id: Sprint identifier

        Returns:
            (start_commit, end_commit, error_message)
        """
        start_tag = self._format_tag_name(sprint_id, 'start')
        end_tag = self._format_tag_name(sprint_id, 'end')

        start_commit = None
        end_commit = None

        # Get start commit
        if self._tag_exists(start_tag):
            try:
                result = self._run_git("rev-list", "-n", "1", start_tag)
                start_commit = result.stdout.strip()
            except subprocess.CalledProcessError as e:
                return None, None, f"Failed to resolve start tag: {e.stderr}"
        else:
            return None, None, f"Start tag '{start_tag}' does not exist"

        # Get end commit
        if self._tag_exists(end_tag):
            try:
                result = self._run_git("rev-list", "-n", "1", end_tag)
                end_commit = result.stdout.strip()
            except subprocess.CalledProcessError as e:
                return None, None, f"Failed to resolve end tag: {e.stderr}"
        else:
            # Sprint not yet completed, use HEAD
            try:
                end_commit = self._get_current_commit()
            except Exception as e:
                return None, None, f"Failed to get current commit: {e}"

        return start_commit, end_commit, None

    def get_sprint_commits(self, sprint_id: str) -> Tuple[List[str], Optional[str]]:
        """
        Get list of commit SHAs in a sprint's range.

        Args:
            sprint_id: Sprint identifier

        Returns:
            (commit_sha_list, error_message)
        """
        start_commit, end_commit, error = self.get_sprint_commit_range(sprint_id)

        if error:
            return [], error

        # Get commits in range
        try:
            result = self._run_git("rev-list", f"{start_commit}..{end_commit}")
            commits = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            return commits, None
        except subprocess.CalledProcessError as e:
            return [], f"Failed to get commit range: {e.stderr}"


def create_sprint_start_tag(
    sprint_id: str,
    repo_path: Optional[str] = None,
    commit: Optional[str] = None,
    force: bool = False,
    push: bool = False
) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to create sprint start tag.

    Args:
        sprint_id: Sprint identifier
        repo_path: Path to git repository
        commit: Commit SHA to tag (default: HEAD)
        force: Overwrite existing tag
        push: Push tag to remote

    Returns:
        (success, error_message)
    """
    tagger = SprintTagger(repo_path)
    return tagger.create_sprint_tag(sprint_id, 'start', commit, force, push)


def create_sprint_end_tag(
    sprint_id: str,
    repo_path: Optional[str] = None,
    commit: Optional[str] = None,
    force: bool = False,
    push: bool = False
) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to create sprint end tag.

    Args:
        sprint_id: Sprint identifier
        repo_path: Path to git repository
        commit: Commit SHA to tag (default: HEAD)
        force: Overwrite existing tag
        push: Push tag to remote

    Returns:
        (success, error_message)
    """
    tagger = SprintTagger(repo_path)
    return tagger.create_sprint_tag(sprint_id, 'end', commit, force, push)


def list_all_sprint_tags(repo_path: Optional[str] = None) -> List[SprintTag]:
    """
    Convenience function to list all sprint tags.

    Args:
        repo_path: Path to git repository

    Returns:
        List of SprintTag objects
    """
    tagger = SprintTagger(repo_path)
    return tagger.list_sprint_tags()
