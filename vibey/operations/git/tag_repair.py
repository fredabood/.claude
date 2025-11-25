"""
Tag repair automation for git integration.

This module provides:
- Detection of dangling tags (pointing to non-existent commits)
- Automatic repair of tags after rebase/squash
- Manual tag movement
- Post-rebase/post-merge hooks
"""

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set


@dataclass
class DanglingTag:
    """Information about a dangling tag."""
    tag_name: str
    commit_sha: str  # The SHA that no longer exists
    tag_type: str  # 'sprint' or 'task'
    entity_id: Optional[str] = None  # sprint-id or task-id parsed from tag
    message: Optional[str] = None  # Tag annotation message


@dataclass
class TagRepairResult:
    """Result of a single tag repair."""
    tag_name: str
    old_sha: str
    new_sha: Optional[str]
    success: bool
    reason: str


@dataclass
class RepairSummary:
    """Summary of tag repair operation."""
    dangling_found: int
    repaired: int
    unfixable: int
    repairs: List[TagRepairResult]
    errors: List[str]


class TagRepairer:
    """
    Repair dangling tags after rebase/squash operations.

    Detects tags pointing to non-existent commits and attempts to
    repair them by finding matching commits in the new history.
    """

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)

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

    def _commit_exists(self, sha: str) -> bool:
        """Check if a commit SHA exists in the repository."""
        success, _, _ = self._run_git(['cat-file', '-e', sha], check=False)
        return success

    def _parse_tag_name(self, tag_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse tag name to extract type and entity ID.

        Patterns:
        - sprint/<sprint-id>/start -> ('sprint', '<sprint-id>')
        - sprint/<sprint-id>/end -> ('sprint', '<sprint-id>')
        - task/<task-id> -> ('task', '<task-id>')

        Returns:
            (tag_type, entity_id) or (None, None) if not a roadmap tag
        """
        # Sprint tags: sprint/<sprint-id>/start or sprint/<sprint-id>/end
        sprint_match = re.match(r'sprint/([^/]+)/(start|end)', tag_name)
        if sprint_match:
            return 'sprint', sprint_match.group(1)

        # Task tags: task/<task-id>
        task_match = re.match(r'task/(.+)', tag_name)
        if task_match:
            return 'task', task_match.group(1)

        return None, None

    def find_dangling_tags(self) -> Tuple[List[DanglingTag], Optional[str]]:
        """
        Find all tags pointing to non-existent commits.

        Returns:
            (dangling_tags, error) tuple
        """
        dangling = []

        # Get all tags with their commit SHAs
        success, stdout, stderr = self._run_git(
            ['tag', '-l', '--format=%(refname:short) %(objectname)'],
            check=False
        )

        if not success:
            return [], f"Failed to list tags: {stderr}"

        for line in stdout.strip().split('\n'):
            if not line:
                continue

            parts = line.split()
            if len(parts) < 2:
                continue

            tag_name, commit_sha = parts[0], parts[1]

            # Check if commit exists
            if not self._commit_exists(commit_sha):
                # Parse tag to see if it's a roadmap tag
                tag_type, entity_id = self._parse_tag_name(tag_name)

                # Get tag message if it's an annotated tag
                message = None
                if tag_type:  # Only get message for roadmap tags
                    success, msg_out, _ = self._run_git(
                        ['tag', '-l', '--format=%(contents)', tag_name],
                        check=False
                    )
                    if success:
                        message = msg_out.strip()

                dangling.append(DanglingTag(
                    tag_name=tag_name,
                    commit_sha=commit_sha,
                    tag_type=tag_type or 'unknown',
                    entity_id=entity_id,
                    message=message
                ))

        return dangling, None

    def _find_matching_commit(self, dangling: DanglingTag, strategy: str = 'message_match') -> Optional[str]:
        """
        Find a new commit that matches the dangling tag.

        Strategies:
        - message_match: Search for commits with matching message and entity references
        - first_match: Use the first commit mentioning the entity ID

        Returns:
            New commit SHA or None if no match found
        """
        if not dangling.entity_id:
            return None

        if strategy == 'message_match':
            # Try to find commit with similar message and entity reference
            # Search in last 1000 commits
            success, stdout, _ = self._run_git(
                ['log', '-1000', '--format=%H %s', '--all'],
                check=False
            )

            if not success:
                return None

            entity_id = dangling.entity_id

            # Look for commits mentioning this entity
            for line in stdout.strip().split('\n'):
                if not line:
                    continue

                parts = line.split(' ', 1)
                if len(parts) < 2:
                    continue

                commit_sha, message = parts[0], parts[1]

                # Check if commit message mentions the entity ID
                if entity_id in message:
                    # Additional validation: check if this is the right type
                    if dangling.tag_type == 'sprint' and 'sprint' in message.lower():
                        return commit_sha
                    elif dangling.tag_type == 'task' and 'task' in message.lower():
                        return commit_sha
                    elif dangling.tag_type == 'unknown':
                        # For unknown tags, accept any mention
                        return commit_sha

        return None

    def repair_tag(self, dangling: DanglingTag, strategy: str = 'message_match',
                   force: bool = True, dry_run: bool = False) -> TagRepairResult:
        """
        Repair a single dangling tag.

        Args:
            dangling: The dangling tag to repair
            strategy: Repair strategy ('message_match', 'manual')
            force: If True, force delete old tag
            dry_run: If True, only simulate repair

        Returns:
            TagRepairResult with outcome
        """
        # Find matching commit
        new_sha = self._find_matching_commit(dangling, strategy)

        if not new_sha:
            return TagRepairResult(
                tag_name=dangling.tag_name,
                old_sha=dangling.commit_sha,
                new_sha=None,
                success=False,
                reason="No matching commit found"
            )

        if dry_run:
            return TagRepairResult(
                tag_name=dangling.tag_name,
                old_sha=dangling.commit_sha,
                new_sha=new_sha,
                success=True,
                reason="Would repair (dry run)"
            )

        # Delete old tag
        success, _, stderr = self._run_git(['tag', '-d', dangling.tag_name], check=False)
        if not success:
            return TagRepairResult(
                tag_name=dangling.tag_name,
                old_sha=dangling.commit_sha,
                new_sha=new_sha,
                success=False,
                reason=f"Failed to delete old tag: {stderr}"
            )

        # Recreate tag on new commit
        # If we have the original message, use it for annotation
        if dangling.message:
            success, _, stderr = self._run_git(
                ['tag', '-a', dangling.tag_name, new_sha, '-m', dangling.message],
                check=False
            )
        else:
            # Create lightweight tag
            success, _, stderr = self._run_git(
                ['tag', dangling.tag_name, new_sha],
                check=False
            )

        if not success:
            return TagRepairResult(
                tag_name=dangling.tag_name,
                old_sha=dangling.commit_sha,
                new_sha=new_sha,
                success=False,
                reason=f"Failed to recreate tag: {stderr}"
            )

        return TagRepairResult(
            tag_name=dangling.tag_name,
            old_sha=dangling.commit_sha,
            new_sha=new_sha,
            success=True,
            reason="Repaired successfully"
        )

    def repair_all_tags(self, strategy: str = 'message_match',
                       dry_run: bool = False,
                       only_roadmap: bool = True) -> Tuple[RepairSummary, Optional[str]]:
        """
        Repair all dangling tags.

        Args:
            strategy: Repair strategy to use
            dry_run: If True, only simulate repairs
            only_roadmap: If True, only repair roadmap tags (sprint/task tags)

        Returns:
            (RepairSummary, error) tuple
        """
        # Find all dangling tags
        dangling_tags, error = self.find_dangling_tags()
        if error:
            return RepairSummary(
                dangling_found=0,
                repaired=0,
                unfixable=0,
                repairs=[],
                errors=[error]
            ), error

        # Filter to only roadmap tags if requested
        if only_roadmap:
            dangling_tags = [t for t in dangling_tags if t.tag_type in ('sprint', 'task')]

        repairs = []
        errors = []

        for dangling in dangling_tags:
            try:
                result = self.repair_tag(dangling, strategy=strategy, dry_run=dry_run)
                repairs.append(result)
            except Exception as e:
                errors.append(f"Error repairing {dangling.tag_name}: {e}")
                repairs.append(TagRepairResult(
                    tag_name=dangling.tag_name,
                    old_sha=dangling.commit_sha,
                    new_sha=None,
                    success=False,
                    reason=str(e)
                ))

        repaired = len([r for r in repairs if r.success])
        unfixable = len([r for r in repairs if not r.success])

        return RepairSummary(
            dangling_found=len(dangling_tags),
            repaired=repaired,
            unfixable=unfixable,
            repairs=repairs,
            errors=errors
        ), None

    def move_tag(self, tag_name: str, new_sha: str, force: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Manually move a tag to a different commit.

        Args:
            tag_name: Name of the tag to move
            new_sha: Target commit SHA
            force: If True, delete existing tag first

        Returns:
            (success, error) tuple
        """
        # Check if target commit exists
        if not self._commit_exists(new_sha):
            return False, f"Commit does not exist: {new_sha}"

        # Check if tag exists
        success, _, _ = self._run_git(['tag', '-l', tag_name], check=False)
        tag_exists = success

        if tag_exists:
            if not force:
                return False, f"Tag already exists: {tag_name}. Use --force to move it."

            # Get original tag message if it's annotated
            message = None
            success, msg_out, _ = self._run_git(
                ['tag', '-l', '--format=%(contents)', tag_name],
                check=False
            )
            if success and msg_out.strip():
                message = msg_out.strip()

            # Delete existing tag
            success, _, stderr = self._run_git(['tag', '-d', tag_name], check=False)
            if not success:
                return False, f"Failed to delete existing tag: {stderr}"

            # Recreate with message if we had one
            if message:
                success, _, stderr = self._run_git(
                    ['tag', '-a', tag_name, new_sha, '-m', message],
                    check=False
                )
            else:
                success, _, stderr = self._run_git(['tag', tag_name, new_sha], check=False)

            if not success:
                return False, f"Failed to recreate tag: {stderr}"

            return True, None
        else:
            # Create new tag
            success, _, stderr = self._run_git(['tag', tag_name, new_sha], check=False)
            if not success:
                return False, f"Failed to create tag: {stderr}"
            return True, None


def find_dangling_tags(repo_path: str = ".") -> Tuple[List[DanglingTag], Optional[str]]:
    """
    Convenience function to find dangling tags.

    Args:
        repo_path: Path to git repository

    Returns:
        (dangling_tags, error) tuple
    """
    repairer = TagRepairer(repo_path)
    return repairer.find_dangling_tags()


def repair_all_tags(repo_path: str = ".", strategy: str = 'message_match',
                   dry_run: bool = False, only_roadmap: bool = True) -> Tuple[RepairSummary, Optional[str]]:
    """
    Convenience function to repair all dangling tags.

    Args:
        repo_path: Path to git repository
        strategy: Repair strategy to use
        dry_run: If True, only simulate repairs
        only_roadmap: If True, only repair roadmap tags

    Returns:
        (RepairSummary, error) tuple
    """
    repairer = TagRepairer(repo_path)
    return repairer.repair_all_tags(strategy=strategy, dry_run=dry_run, only_roadmap=only_roadmap)


def move_tag(tag_name: str, new_sha: str, repo_path: str = ".", force: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to move a tag.

    Args:
        tag_name: Name of the tag to move
        new_sha: Target commit SHA
        repo_path: Path to git repository
        force: If True, move even if tag exists

    Returns:
        (success, error) tuple
    """
    repairer = TagRepairer(repo_path)
    return repairer.move_tag(tag_name, new_sha, force=force)
