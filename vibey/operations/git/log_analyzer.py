"""
Git Log Analysis Utilities

Provides utilities for retrieving and analyzing Git commit history,
integrating with the CommitParser to extract Vibey roadmap references.

Task: git-integration-1-task-003
Status: In Progress
"""

import subprocess
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from vibey.operations.git.commit_parser import CommitParser, analyze_batch
from vibey.operations.git.commit_parser_schema import (
    ParserConfig,
    ParsedCommit,
    ParseResult,
)


@dataclass
class CommitInfo:
    """Full commit information from git log."""
    sha: str
    author_name: str
    author_email: str
    date: datetime
    message: str

    # Parsed roadmap references (added by analyzer)
    parsed: Optional[ParsedCommit] = None

    # Parent commits
    parents: List[str] = field(default_factory=list)

    # Files changed
    files_changed: int = 0
    insertions: int = 0
    deletions: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "sha": self.sha,
            "author_name": self.author_name,
            "author_email": self.author_email,
            "date": self.date.isoformat(),
            "message": self.message,
            "parents": self.parents,
            "files_changed": self.files_changed,
            "insertions": self.insertions,
            "deletions": self.deletions,
            "parsed": self.parsed.to_dict() if self.parsed else None,
        }


@dataclass
class BranchInfo:
    """Information about a git branch."""
    name: str
    sha: str
    is_current: bool = False
    is_remote: bool = False
    upstream: Optional[str] = None


@dataclass
class TagInfo:
    """Information about a git tag."""
    name: str
    sha: str
    message: Optional[str] = None
    tagger: Optional[str] = None
    date: Optional[datetime] = None
    is_annotated: bool = False


@dataclass
class AnalysisResult:
    """Result of analyzing git history."""
    commits: List[CommitInfo]
    parse_result: ParseResult

    # Time range
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    # Branches and tags involved
    branches: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    # Statistics
    total_contributors: int = 0
    contributors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "commits": [c.to_dict() for c in self.commits],
            "parse_result": self.parse_result.to_dict(),
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "branches": self.branches,
            "tags": self.tags,
            "total_contributors": self.total_contributors,
            "contributors": self.contributors,
        }


class GitLogAnalyzer:
    """
    Analyze Git commit history and extract Vibey roadmap references.

    Provides utilities for:
    - Retrieving commit history with various filters
    - Parsing commits for task/sprint/track references
    - Analyzing branches and tags
    - Generating statistics and reports
    """

    def __init__(
        self,
        repo_path: str = ".",
        parser_config: Optional[ParserConfig] = None
    ):
        """
        Initialize analyzer.

        Args:
            repo_path: Path to git repository (default: current directory)
            parser_config: Configuration for commit parser
        """
        self.repo_path = Path(repo_path).resolve()
        self.parser = CommitParser(parser_config)

    # Git command wrappers

    def _run_git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        """
        Run a git command.

        Args:
            *args: Git command arguments
            check: Raise exception on non-zero exit code

        Returns:
            CompletedProcess result
        """
        cmd = ["git", "-C", str(self.repo_path)] + list(args)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=check
        )
        return result

    def is_git_repo(self) -> bool:
        """Check if the path is a git repository."""
        try:
            self._run_git("rev-parse", "--git-dir")
            return True
        except subprocess.CalledProcessError:
            return False

    def get_current_branch(self) -> Optional[str]:
        """Get the name of the current branch."""
        try:
            result = self._run_git("branch", "--show-current")
            return result.stdout.strip() or None
        except subprocess.CalledProcessError:
            return None

    def get_current_sha(self) -> str:
        """Get the SHA of the current HEAD."""
        result = self._run_git("rev-parse", "HEAD")
        return result.stdout.strip()

    # Commit retrieval

    def get_commits(
        self,
        ref_range: Optional[str] = None,
        max_count: Optional[int] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        author: Optional[str] = None,
        grep: Optional[str] = None,
        paths: Optional[List[str]] = None,
    ) -> List[CommitInfo]:
        """
        Get commits from git log with various filters.

        Args:
            ref_range: Commit range (e.g., "HEAD~10..HEAD", "main..develop")
            max_count: Maximum number of commits to retrieve
            since: Show commits after date (e.g., "2 weeks ago", "2024-01-01")
            until: Show commits before date
            author: Filter by author name/email
            grep: Filter by commit message pattern
            paths: Only show commits affecting these paths

        Returns:
            List of CommitInfo objects
        """
        # Build git log command
        args = ["log", "--format=%H|%aN|%aE|%aI|%P"]

        if max_count:
            args.extend(["-n", str(max_count)])

        if since:
            args.extend(["--since", since])

        if until:
            args.extend(["--until", until])

        if author:
            args.extend(["--author", author])

        if grep:
            args.extend(["--grep", grep])

        args.append("--stat")  # Include file statistics

        if ref_range:
            args.append(ref_range)

        if paths:
            args.append("--")
            args.extend(paths)

        # Get commit log
        result = self._run_git(*args)

        # Parse output
        commits = []
        current_commit = None

        for line in result.stdout.split('\n'):
            if not line.strip():
                continue

            # New commit line: SHA|Author|Email|Date|Parents
            if '|' in line and len(line.split('|')) >= 4:
                if current_commit:
                    commits.append(current_commit)

                parts = line.split('|')
                sha = parts[0]
                author_name = parts[1]
                author_email = parts[2]
                date_str = parts[3]
                parents = parts[4].split() if len(parts) > 4 and parts[4] else []

                current_commit = CommitInfo(
                    sha=sha,
                    author_name=author_name,
                    author_email=author_email,
                    date=datetime.fromisoformat(date_str.replace('Z', '+00:00')),
                    message="",
                    parents=parents,
                )

            # File statistics line
            elif current_commit and " changed" in line:
                # Parse: " 3 files changed, 12 insertions(+), 5 deletions(-)"
                parts = line.strip().split(',')
                for part in parts:
                    if "changed" in part:
                        current_commit.files_changed = int(part.split()[0])
                    elif "insertion" in part:
                        current_commit.insertions = int(part.split()[0])
                    elif "deletion" in part:
                        current_commit.deletions = int(part.split()[0])

        if current_commit:
            commits.append(current_commit)

        # Get commit messages separately (they can contain newlines)
        for commit in commits:
            result = self._run_git("log", "-1", "--format=%B", commit.sha)
            commit.message = result.stdout.strip()

        return commits

    def get_commit_by_sha(self, sha: str) -> CommitInfo:
        """
        Get a single commit by SHA.

        Args:
            sha: Commit SHA (can be abbreviated)

        Returns:
            CommitInfo object
        """
        commits = self.get_commits(ref_range=f"{sha}^..{sha}", max_count=1)
        if not commits:
            raise ValueError(f"Commit not found: {sha}")
        return commits[0]

    # Branch operations

    def get_branches(
        self,
        remote: bool = False,
        all_branches: bool = False
    ) -> List[BranchInfo]:
        """
        Get list of branches.

        Args:
            remote: Include remote branches
            all_branches: Include both local and remote

        Returns:
            List of BranchInfo objects
        """
        args = ["branch", "-v", "--format=%(refname:short)|%(objectname)|%(HEAD)|%(upstream:short)"]

        if all_branches:
            args.append("-a")
        elif remote:
            args.append("-r")

        result = self._run_git(*args)

        branches = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue

            parts = line.split('|')
            if len(parts) >= 3:
                name = parts[0]
                sha = parts[1]
                is_current = parts[2] == '*'
                upstream = parts[3] if len(parts) > 3 and parts[3] else None

                branches.append(BranchInfo(
                    name=name,
                    sha=sha,
                    is_current=is_current,
                    is_remote=name.startswith('origin/'),
                    upstream=upstream,
                ))

        return branches

    def get_branch_commits(
        self,
        branch: str,
        base: Optional[str] = None
    ) -> List[CommitInfo]:
        """
        Get commits on a branch.

        Args:
            branch: Branch name
            base: Base branch to compare against (e.g., "main")

        Returns:
            List of CommitInfo objects
        """
        if base:
            # Get commits unique to this branch
            ref_range = f"{base}..{branch}"
        else:
            # Get all commits on this branch
            ref_range = branch

        return self.get_commits(ref_range=ref_range)

    # Tag operations

    def get_tags(self) -> List[TagInfo]:
        """
        Get list of tags.

        Returns:
            List of TagInfo objects
        """
        # Get all tags with their commit SHAs
        result = self._run_git("tag", "-l", "--format=%(refname:short)|%(objectname)")

        tags = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue

            parts = line.split('|')
            if len(parts) >= 2:
                name = parts[0]
                sha = parts[1]

                # Check if annotated tag
                tag_result = self._run_git("cat-file", "-t", sha, check=False)
                is_annotated = tag_result.stdout.strip() == "tag"

                tag_info = TagInfo(
                    name=name,
                    sha=sha,
                    is_annotated=is_annotated,
                )

                # Get tag message and tagger info if annotated
                if is_annotated:
                    msg_result = self._run_git("tag", "-l", "-n99", name)
                    # Format: "tag-name    message..."
                    if '\t' in msg_result.stdout or '    ' in msg_result.stdout:
                        tag_info.message = msg_result.stdout.split(None, 1)[1].strip()

                tags.append(tag_info)

        return tags

    def get_commits_between_tags(
        self,
        start_tag: str,
        end_tag: str
    ) -> List[CommitInfo]:
        """
        Get commits between two tags.

        Args:
            start_tag: Starting tag (exclusive)
            end_tag: Ending tag (inclusive)

        Returns:
            List of CommitInfo objects
        """
        return self.get_commits(ref_range=f"{start_tag}..{end_tag}")

    def find_tags_containing_commit(self, sha: str) -> List[str]:
        """
        Find all tags that contain a specific commit.

        Args:
            sha: Commit SHA

        Returns:
            List of tag names
        """
        result = self._run_git("tag", "--contains", sha)
        return [line.strip() for line in result.stdout.strip().split('\n') if line]

    # Analysis operations

    def analyze(
        self,
        ref_range: Optional[str] = None,
        max_count: Optional[int] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
    ) -> AnalysisResult:
        """
        Analyze commit history and extract Vibey references.

        Args:
            ref_range: Commit range to analyze
            max_count: Maximum commits to analyze
            since: Analyze commits after date
            until: Analyze commits before date

        Returns:
            AnalysisResult with commits and statistics
        """
        # Get commits
        commits = self.get_commits(
            ref_range=ref_range,
            max_count=max_count,
            since=since,
            until=until,
        )

        # Parse commits for roadmap references
        for commit in commits:
            commit.parsed = self.parser.parse(commit.message, commit.sha)

        # Analyze with batch parser
        commit_dicts = [
            {"message": c.message, "sha": c.sha}
            for c in commits
        ]
        parse_result = analyze_batch(commit_dicts, self.parser.config)

        # Collect statistics
        contributors = set()
        for commit in commits:
            contributors.add(f"{commit.author_name} <{commit.author_email}>")

        # Time range
        start_date = min(c.date for c in commits) if commits else None
        end_date = max(c.date for c in commits) if commits else None

        # Find branches containing these commits
        branches = []
        if commits:
            first_sha = commits[0].sha
            branch_result = self._run_git("branch", "--contains", first_sha, check=False)
            if branch_result.returncode == 0:
                branches = [
                    line.strip().lstrip('* ')
                    for line in branch_result.stdout.strip().split('\n')
                    if line
                ]

        # Find tags
        tags = []
        if commits:
            for commit in commits[:10]:  # Check first 10 commits
                commit_tags = self.find_tags_containing_commit(commit.sha)
                tags.extend(commit_tags)
        tags = list(set(tags))  # Deduplicate

        return AnalysisResult(
            commits=commits,
            parse_result=parse_result,
            start_date=start_date,
            end_date=end_date,
            branches=branches,
            tags=tags,
            total_contributors=len(contributors),
            contributors=sorted(contributors),
        )

    def find_commits_for_task(self, task_id: str) -> List[CommitInfo]:
        """
        Find all commits that reference a specific task.

        Args:
            task_id: Task ID to search for

        Returns:
            List of CommitInfo objects
        """
        # Get all commits
        all_commits = self.get_commits()

        # Parse and filter
        matching = []
        for commit in all_commits:
            commit.parsed = self.parser.parse(commit.message, commit.sha)

            # Check if this commit references the task
            for task_ref in commit.parsed.tasks:
                if task_ref.task_id == task_id:
                    matching.append(commit)
                    break

        return matching

    def find_commits_for_sprint(self, sprint_id: str) -> List[CommitInfo]:
        """
        Find all commits that reference a specific sprint.

        Args:
            sprint_id: Sprint ID to search for

        Returns:
            List of CommitInfo objects
        """
        all_commits = self.get_commits()

        matching = []
        for commit in all_commits:
            commit.parsed = self.parser.parse(commit.message, commit.sha)

            if commit.parsed.sprint and commit.parsed.sprint.sprint_id == sprint_id:
                matching.append(commit)

        return matching

    def get_contributors_for_task(self, task_id: str) -> List[Tuple[str, int]]:
        """
        Get contributors who worked on a specific task.

        Args:
            task_id: Task ID

        Returns:
            List of (contributor, commit_count) tuples, sorted by count
        """
        commits = self.find_commits_for_task(task_id)

        contributor_counts: Dict[str, int] = {}
        for commit in commits:
            contributor = f"{commit.author_name} <{commit.author_email}>"
            contributor_counts[contributor] = contributor_counts.get(contributor, 0) + 1

        # Sort by count descending
        return sorted(
            contributor_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

    # Utility methods

    def get_file_changes_for_task(self, task_id: str) -> Dict[str, int]:
        """
        Get files changed for a specific task.

        Args:
            task_id: Task ID

        Returns:
            Dict mapping file path to number of times changed
        """
        commits = self.find_commits_for_task(task_id)

        file_changes: Dict[str, int] = {}
        for commit in commits:
            # Get files changed in this commit
            result = self._run_git("diff-tree", "--no-commit-id", "--name-only", "-r", commit.sha)
            files = [line.strip() for line in result.stdout.strip().split('\n') if line]

            for file_path in files:
                file_changes[file_path] = file_changes.get(file_path, 0) + 1

        return file_changes

    def get_commit_at_date(self, date_str: str) -> Optional[CommitInfo]:
        """
        Get the commit closest to a specific date.

        Args:
            date_str: Date string (e.g., "2024-01-01", "2 weeks ago")

        Returns:
            CommitInfo or None if no commits before that date
        """
        commits = self.get_commits(until=date_str, max_count=1)
        return commits[0] if commits else None

    def get_commit_count_between(
        self,
        start_ref: str,
        end_ref: str
    ) -> int:
        """
        Get number of commits between two refs.

        Args:
            start_ref: Starting reference (exclusive)
            end_ref: Ending reference (inclusive)

        Returns:
            Number of commits
        """
        result = self._run_git("rev-list", "--count", f"{start_ref}..{end_ref}")
        return int(result.stdout.strip())


def analyze_repository(
    repo_path: str = ".",
    ref_range: Optional[str] = None,
    max_count: int = 100,
    parser_config: Optional[ParserConfig] = None,
) -> AnalysisResult:
    """
    Quick helper to analyze a repository.

    Args:
        repo_path: Path to git repository
        ref_range: Commit range to analyze (default: last 100 commits)
        max_count: Maximum commits to retrieve
        parser_config: Parser configuration

    Returns:
        AnalysisResult with commits and statistics
    """
    analyzer = GitLogAnalyzer(repo_path, parser_config)
    return analyzer.analyze(ref_range=ref_range, max_count=max_count)
