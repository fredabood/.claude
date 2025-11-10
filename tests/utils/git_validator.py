"""
Git validator utility for validating git history and commits.

This module provides tools for validating git commits, history,
and repository state.
"""

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class Commit:
    """Represents a git commit."""

    hash: str
    message: str
    author: str
    date: str
    files_changed: List[str]


class GitValidator:
    """
    Validate git history and commits.

    This class provides methods to validate commit messages,
    commit order, file changes, and overall git state.
    """

    # Conventional commit pattern
    CONVENTIONAL_COMMIT_PATTERN = re.compile(
        r"^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\(.+\))?: .+"
    )

    @staticmethod
    def validate_commit_message(commit: Commit, pattern: Optional[str] = None) -> bool:
        """
        Validate commit message format.

        Args:
            commit: Commit to validate
            pattern: Regex pattern (defaults to conventional commit format)

        Returns:
            True if valid, False otherwise
        """
        if pattern:
            return bool(re.match(pattern, commit.message))
        return bool(GitValidator.CONVENTIONAL_COMMIT_PATTERN.match(commit.message))

    @staticmethod
    def validate_commit_order(
        commits: List[Commit], expected_order: List[str]
    ) -> bool:
        """
        Validate commits are in expected order.

        Args:
            commits: List of commits (newest first)
            expected_order: List of expected commit message patterns

        Returns:
            True if order matches, False otherwise
        """
        if len(commits) < len(expected_order):
            return False

        for i, expected_pattern in enumerate(expected_order):
            if not re.search(expected_pattern, commits[i].message):
                return False

        return True

    @staticmethod
    def validate_file_changes(
        commit: Commit, expected_files: List[str]
    ) -> bool:
        """
        Validate files changed in commit.

        Args:
            commit: Commit to validate
            expected_files: List of expected file paths (can use glob patterns)

        Returns:
            True if all expected files present, False otherwise
        """
        from fnmatch import fnmatch

        for expected in expected_files:
            found = False
            for changed_file in commit.files_changed:
                if fnmatch(changed_file, expected):
                    found = True
                    break
            if not found:
                return False

        return True

    @staticmethod
    def get_commit_history(
        repo_path: Path, count: int = 10
    ) -> List[Commit]:
        """
        Get commit history from repository.

        Args:
            repo_path: Path to repository
            count: Number of commits to retrieve

        Returns:
            List of Commit objects
        """
        commits = []

        # Get commit hashes
        result = subprocess.run(
            ["git", "log", f"-{count}", "--format=%H"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )

        commit_hashes = result.stdout.strip().split("\n")

        for commit_hash in commit_hashes:
            if not commit_hash:
                continue

            # Get commit details
            result = subprocess.run(
                [
                    "git", "show", "--no-patch",
                    "--format=%s%n%an%n%ad",
                    commit_hash
                ],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )

            lines = result.stdout.strip().split("\n")
            message = lines[0] if len(lines) > 0 else ""
            author = lines[1] if len(lines) > 1 else ""
            date = lines[2] if len(lines) > 2 else ""

            # Get files changed
            result = subprocess.run(
                ["git", "show", "--name-only", "--format=", commit_hash],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )

            files_changed = [
                f for f in result.stdout.strip().split("\n") if f
            ]

            commits.append(
                Commit(
                    hash=commit_hash,
                    message=message,
                    author=author,
                    date=date,
                    files_changed=files_changed
                )
            )

        return commits

    @staticmethod
    def validate_branch_state(
        repo_path: Path, expected_branch: str
    ) -> bool:
        """
        Validate repository is on expected branch.

        Args:
            repo_path: Path to repository
            expected_branch: Expected branch name

        Returns:
            True if on expected branch, False otherwise
        """
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )

        actual_branch = result.stdout.strip()
        return actual_branch == expected_branch
