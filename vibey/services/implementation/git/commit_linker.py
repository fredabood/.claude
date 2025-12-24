"""
Links commits to tickets with metadata tracking.

This module provides functionality to create commits that are linked to
tickets with proper metadata in commit footers, and to track/query the
relationship between commits and tickets.

Design Reference:
- Context System v2 Architecture
- Implementation Mode Track Sprint 3
- Conventional Commits specification

The commit message format follows:
    <type>(<scope>): <subject>

    <body>

    Task: <ticket-id>
    Completes: <ticket-id>  (optional)
    Session: <session-id>

Usage:
    from vibey.services.implementation.git import TicketCommitLinker, CommitType
    from pathlib import Path

    linker = TicketCommitLinker(repo_root=Path("/path/to/repo"))

    # Create a linked commit
    commit_hash = linker.create_linked_commit(
        ticket=task,
        message="Add user authentication",
        commit_type=CommitType.FEAT,
    )

    # Get all commits for a ticket
    commits = linker.get_ticket_commits(task)
"""

import logging
import re
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

import yaml

if TYPE_CHECKING:
    from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================


class CommitType(Enum):
    """
    Conventional commit types.

    Based on the Conventional Commits specification:
    https://www.conventionalcommits.org/
    """

    FEAT = "feat"
    FIX = "fix"
    WIP = "wip"
    REFACTOR = "refactor"
    DOCS = "docs"
    TEST = "test"
    CHORE = "chore"
    STYLE = "style"
    PERF = "perf"
    CI = "ci"
    BUILD = "build"
    REVERT = "revert"


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class CommitRef:
    """
    Reference to a commit linked to a ticket.

    Captures commit metadata along with ticket association information.

    Attributes:
        hash: Full 40-character SHA hash
        short_hash: Abbreviated 7-character hash
        message: Full commit message
        timestamp: When the commit was created
        author: Commit author (Name <email> format)
        ticket_id: The ticket ID this commit is associated with
        files_changed: List of files modified in this commit
        session_id: Optional session ID for tracking
        commit_type: The type of commit (feat, fix, etc.)
    """

    hash: str
    short_hash: str
    message: str
    timestamp: datetime
    author: str
    ticket_id: str
    files_changed: List[str] = field(default_factory=list)
    session_id: Optional[str] = None
    commit_type: Optional[CommitType] = None

    @property
    def subject(self) -> str:
        """Get the first line (subject) of the commit message."""
        return self.message.split("\n")[0]

    @property
    def body(self) -> str:
        """Get the body of the commit message (after first line)."""
        lines = self.message.split("\n")
        if len(lines) > 1:
            return "\n".join(lines[1:]).strip()
        return ""

    @property
    def completes_ticket(self) -> bool:
        """Check if this commit marks the ticket as complete."""
        return f"Completes: {self.ticket_id}" in self.message


# =============================================================================
# TICKET COMMIT LINKER
# =============================================================================


class TicketCommitLinker:
    """
    Links all commits to tickets with metadata.

    Provides functionality to:
    - Create commits with proper ticket linking in footers
    - Query commits associated with tickets
    - Update ticket YAML with commit references
    - Generate commit summaries for tickets

    Commit messages follow the format:
        <type>(<scope>): <subject>

        <body>

        Task: <ticket-id>
        Completes: <ticket-id>  (optional)
        Session: <session-id>

    Attributes:
        repo_root: Root directory of the git repository
        session_id: Current session identifier for tracking
        context_dumper: CommitContextDumper for audit trail

    Example:
        >>> linker = TicketCommitLinker(Path("/repo"))
        >>> hash = linker.create_linked_commit(
        ...     ticket=task,
        ...     message="Add feature",
        ...     commit_type=CommitType.FEAT,
        ... )
        >>> commits = linker.get_ticket_commits(task)
        >>> print(f"Found {len(commits)} commits")
    """

    # Regex for parsing ticket references from commit messages
    TASK_PATTERN = re.compile(r"^Task:\s*(.+)$", re.MULTILINE)
    COMPLETES_PATTERN = re.compile(r"^Completes:\s*(.+)$", re.MULTILINE)
    SESSION_PATTERN = re.compile(r"^Session:\s*(.+)$", re.MULTILINE)

    def __init__(
        self,
        repo_root: Path,
        session_id: Optional[str] = None,
    ):
        """
        Initialize the commit linker.

        Args:
            repo_root: Root directory of the git repository
            session_id: Optional session ID (auto-generated if not provided)
        """
        self.repo_root = repo_root
        self.session_id = session_id or self._generate_session_id()

        # Import here to avoid circular imports
        from vibey.services.implementation.git.context_dumper import (
            CommitContextDumper,
        )

        self.context_dumper = CommitContextDumper(repo_root)

    def _generate_session_id(self) -> str:
        """Generate a unique session identifier."""
        return f"session-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"

    def create_linked_commit(
        self,
        ticket: "HierarchicalTicket",
        message: str,
        files: Optional[List[Path]] = None,
        commit_type: CommitType = CommitType.FEAT,
        detailed_description: Optional[str] = None,
        completes: bool = False,
        scope: Optional[str] = None,
    ) -> str:
        """
        Create commit with ticket metadata in footer.

        Creates a git commit with the message formatted according to
        conventional commits, with ticket linking in the footer.

        Args:
            ticket: The HierarchicalTicket to link to
            message: The commit subject/summary
            files: Optional list of specific files to stage
            commit_type: Type of commit (feat, fix, etc.)
            detailed_description: Optional detailed body text
            completes: Whether this commit completes the ticket
            scope: Optional scope for conventional commit format

        Returns:
            The commit SHA hash

        Raises:
            subprocess.CalledProcessError: If git commands fail
            ValueError: If commit message validation fails
        """
        # Format the full commit message
        full_message = self._format_commit_message(
            subject=message,
            commit_type=commit_type,
            scope=scope,
            body=detailed_description,
            ticket_id=ticket.id,
            completes=completes,
        )

        # Validate the message
        if not self.validate_commit_message(full_message, ticket):
            raise ValueError(f"Invalid commit message format for ticket {ticket.id}")

        # Stage files if specified, otherwise stage all changes
        if files:
            for f in files:
                self._run_git(["add", str(f)])
        else:
            self._run_git(["add", "-A"])

        # Create the commit
        result = self._run_git(["commit", "-m", full_message])

        # Get the commit hash
        commit_hash = self._run_git(["rev-parse", "HEAD"]).strip()

        logger.info(f"Created linked commit {commit_hash[:7]} for ticket {ticket.id}")

        # Update ticket with commit reference
        self.update_ticket_commits(ticket, commit_hash)

        # Post-commit hook
        self.on_post_commit(commit_hash, ticket)

        return commit_hash

    def _format_commit_message(
        self,
        subject: str,
        commit_type: CommitType,
        scope: Optional[str] = None,
        body: Optional[str] = None,
        ticket_id: str = "",
        completes: bool = False,
    ) -> str:
        """
        Format a commit message with conventional commit format and footer.

        Args:
            subject: The commit subject line
            commit_type: Type of commit
            scope: Optional scope
            body: Optional body text
            ticket_id: The ticket ID to reference
            completes: Whether this completes the ticket

        Returns:
            Formatted commit message
        """
        # Build the subject line
        if scope:
            subject_line = f"{commit_type.value}({scope}): {subject}"
        else:
            subject_line = f"{commit_type.value}: {subject}"

        # Build the full message
        lines = [subject_line]

        if body:
            lines.append("")
            lines.append(body)

        # Add footer
        lines.append("")
        lines.append(f"Task: {ticket_id}")
        if completes:
            lines.append(f"Completes: {ticket_id}")
        lines.append(f"Session: {self.session_id}")

        return "\n".join(lines)

    def validate_commit_message(
        self, message: str, ticket: "HierarchicalTicket"
    ) -> bool:
        """
        Validate commit message follows required format.

        Checks:
        - Has a subject line
        - Contains Task: footer with matching ticket ID
        - Follows conventional commit format

        Args:
            message: The commit message to validate
            ticket: The ticket that should be referenced

        Returns:
            True if valid, False otherwise
        """
        lines = message.strip().split("\n")

        # Must have at least a subject
        if not lines or not lines[0].strip():
            logger.warning("Commit message missing subject line")
            return False

        # Check for Task: footer
        task_match = self.TASK_PATTERN.search(message)
        if not task_match:
            logger.warning("Commit message missing Task: footer")
            return False

        # Verify ticket ID matches
        referenced_id = task_match.group(1).strip()
        if referenced_id != ticket.id:
            logger.warning(
                f"Task ID mismatch: expected {ticket.id}, got {referenced_id}"
            )
            return False

        # Check conventional commit format (type: or type(scope):)
        subject = lines[0]
        conventional_pattern = re.compile(
            r"^(feat|fix|wip|refactor|docs|test|chore|style|perf|ci|build|revert)"
            r"(\([^)]+\))?:\s*.+"
        )
        if not conventional_pattern.match(subject):
            logger.warning("Subject line doesn't follow conventional commit format")
            return False

        return True

    def update_ticket_commits(
        self, ticket: "HierarchicalTicket", commit_hash: str
    ):
        """
        Update ticket YAML with commit reference.

        Adds the commit to the ticket's commits field in the YAML file.

        Args:
            ticket: The ticket to update
            commit_hash: The commit SHA to add
        """
        # Find the ticket YAML file
        roadmap_root = self.repo_root / ".vibey" / "roadmap"
        ticket_file = None

        # Check each entity type directory
        for entity_type in ["tasks", "sprints", "tracks"]:
            potential_file = roadmap_root / entity_type / f"{ticket.id}.yaml"
            if potential_file.exists():
                ticket_file = potential_file
                break

        if ticket_file is None:
            logger.warning(f"Could not find YAML file for ticket {ticket.id}")
            return

        try:
            # Load existing YAML
            with open(ticket_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            # Get commit details
            commit_info = self._get_commit_info(commit_hash)

            # Initialize commits list if not present
            if "commits" not in data:
                data["commits"] = []

            # Add new commit reference
            data["commits"].append(
                {
                    "sha": commit_hash,
                    "message": commit_info.get("message", ""),
                    "date": commit_info.get("date", datetime.now(timezone.utc).isoformat()),
                    "author": commit_info.get("author", "unknown"),
                }
            )

            # Write back
            with open(ticket_file, "w", encoding="utf-8") as f:
                yaml.dump(
                    data,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )

            logger.debug(f"Updated ticket {ticket.id} with commit {commit_hash[:7]}")

        except Exception as e:
            logger.warning(f"Failed to update ticket YAML: {e}")

    def get_ticket_commits(self, ticket: "HierarchicalTicket") -> List[CommitRef]:
        """
        Get all commits associated with ticket.

        Searches git log for commits that reference this ticket ID
        in their Task: or Completes: footer.

        Args:
            ticket: The ticket to get commits for

        Returns:
            List of CommitRef objects for matching commits
        """
        commits: List[CommitRef] = []

        try:
            # Search git log for commits mentioning this ticket
            result = self._run_git(
                [
                    "log",
                    "--all",
                    "--format=%H%n%h%n%s%n%aI%n%an <%ae>%n%B%n---COMMIT-END---",
                    f"--grep=Task: {ticket.id}",
                ]
            )

            # Parse the output
            commit_blocks = result.split("---COMMIT-END---")

            for block in commit_blocks:
                block = block.strip()
                if not block:
                    continue

                lines = block.split("\n")
                if len(lines) < 5:
                    continue

                full_hash = lines[0]
                short_hash = lines[1]
                timestamp_str = lines[3]
                author = lines[4]
                message = "\n".join(lines[5:]).strip() if len(lines) > 5 else lines[2]

                # Get subject line (lines[2] is from %s format)
                full_message = lines[2] + ("\n" + message if message else "")

                # Parse timestamp
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                except ValueError:
                    timestamp = datetime.now(timezone.utc)

                # Get files changed
                files_changed = self._get_commit_files(full_hash)

                # Extract session ID if present
                session_match = self.SESSION_PATTERN.search(full_message)
                session_id = session_match.group(1).strip() if session_match else None

                # Determine commit type from subject
                commit_type = self._extract_commit_type(lines[2])

                commits.append(
                    CommitRef(
                        hash=full_hash,
                        short_hash=short_hash,
                        message=full_message,
                        timestamp=timestamp,
                        author=author,
                        ticket_id=ticket.id,
                        files_changed=files_changed,
                        session_id=session_id,
                        commit_type=commit_type,
                    )
                )

        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to get ticket commits: {e}")
        except FileNotFoundError:
            logger.warning("git not found in PATH")

        # Sort by timestamp
        commits.sort(key=lambda c: c.timestamp)

        return commits

    def _extract_commit_type(self, subject: str) -> Optional[CommitType]:
        """Extract commit type from subject line."""
        match = re.match(r"^(\w+)(\([^)]+\))?:", subject)
        if match:
            type_str = match.group(1).lower()
            try:
                return CommitType(type_str)
            except ValueError:
                pass
        return None

    def generate_commit_summary(self, ticket: "HierarchicalTicket") -> str:
        """
        Generate summary of all commits for ticket.

        Creates a human-readable summary of all commits associated with
        the ticket, including statistics and timeline.

        Args:
            ticket: The ticket to summarize

        Returns:
            Formatted summary string
        """
        commits = self.get_ticket_commits(ticket)

        if not commits:
            return f"No commits found for ticket {ticket.id}"

        lines = [
            f"Commit Summary for Ticket {ticket.id}",
            f"Total Commits: {len(commits)}",
            "",
        ]

        # Group by type
        by_type: dict = {}
        for commit in commits:
            type_name = commit.commit_type.value if commit.commit_type else "other"
            if type_name not in by_type:
                by_type[type_name] = []
            by_type[type_name].append(commit)

        lines.append("By Type:")
        for type_name, type_commits in sorted(by_type.items()):
            lines.append(f"  {type_name}: {len(type_commits)}")

        lines.append("")
        lines.append("Timeline:")
        for commit in commits:
            date_str = commit.timestamp.strftime("%Y-%m-%d %H:%M")
            lines.append(f"  [{date_str}] {commit.short_hash} - {commit.subject}")

        # Files touched
        all_files = set()
        for commit in commits:
            all_files.update(commit.files_changed)

        lines.append("")
        lines.append(f"Files Modified: {len(all_files)}")

        return "\n".join(lines)

    def get_commits_since(self, since: datetime) -> List[CommitRef]:
        """
        Get all implementation mode commits since datetime.

        Finds all commits that have Session: footer (indicating they
        were created in implementation mode) since the given datetime.

        Args:
            since: Start datetime for the search

        Returns:
            List of CommitRef objects
        """
        commits: List[CommitRef] = []

        try:
            since_str = since.strftime("%Y-%m-%d %H:%M:%S")
            result = self._run_git(
                [
                    "log",
                    "--all",
                    f"--since={since_str}",
                    "--format=%H%n%h%n%s%n%aI%n%an <%ae>%n%B%n---COMMIT-END---",
                    "--grep=Session:",
                ]
            )

            # Parse similar to get_ticket_commits
            commit_blocks = result.split("---COMMIT-END---")

            for block in commit_blocks:
                block = block.strip()
                if not block:
                    continue

                lines = block.split("\n")
                if len(lines) < 5:
                    continue

                full_hash = lines[0]
                short_hash = lines[1]
                timestamp_str = lines[3]
                author = lines[4]
                message = "\n".join(lines[5:]).strip() if len(lines) > 5 else ""
                full_message = lines[2] + ("\n" + message if message else "")

                # Parse timestamp
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                except ValueError:
                    timestamp = datetime.now(timezone.utc)

                # Extract ticket ID from Task: footer
                task_match = self.TASK_PATTERN.search(full_message)
                ticket_id = task_match.group(1).strip() if task_match else "unknown"

                # Get files changed
                files_changed = self._get_commit_files(full_hash)

                # Extract session ID
                session_match = self.SESSION_PATTERN.search(full_message)
                session_id = session_match.group(1).strip() if session_match else None

                # Determine commit type
                commit_type = self._extract_commit_type(lines[2])

                commits.append(
                    CommitRef(
                        hash=full_hash,
                        short_hash=short_hash,
                        message=full_message,
                        timestamp=timestamp,
                        author=author,
                        ticket_id=ticket_id,
                        files_changed=files_changed,
                        session_id=session_id,
                        commit_type=commit_type,
                    )
                )

        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to get commits since {since}: {e}")
        except FileNotFoundError:
            logger.warning("git not found in PATH")

        # Sort by timestamp
        commits.sort(key=lambda c: c.timestamp)

        return commits

    def on_post_commit(self, commit_hash: str, ticket: "HierarchicalTicket"):
        """
        Post-commit hook handler.

        Called after a linked commit is created. Handles:
        - Context dumping for audit trail
        - Ticket update verification
        - Any additional post-commit tasks

        Args:
            commit_hash: The SHA of the created commit
            ticket: The linked ticket
        """
        logger.debug(f"Post-commit hook for {commit_hash[:7]} / {ticket.id}")

        # Dump context for audit trail
        try:
            # Get current task state for context
            task_state = {
                "status": ticket.status.value if hasattr(ticket, "status") else None,
                "name": ticket.name,
                "description": ticket.description,
            }

            self.context_dumper.dump_commit_context(
                ticket_id=ticket.id,
                commit_sha=commit_hash,
                task_state=task_state,
            )
        except Exception as e:
            logger.warning(f"Failed to dump commit context: {e}")

    def _run_git(self, args: List[str]) -> str:
        """
        Run a git command and return stdout.

        Args:
            args: Git command arguments (without 'git')

        Returns:
            Command stdout

        Raises:
            subprocess.CalledProcessError: If command fails
        """
        result = subprocess.run(
            ["git"] + args,
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout

    def _get_commit_info(self, commit_hash: str) -> dict:
        """Get basic info about a commit."""
        try:
            result = self._run_git(
                ["log", "-1", "--format=%s%n%aI%n%an <%ae>", commit_hash]
            )
            lines = result.strip().split("\n")
            return {
                "message": lines[0] if lines else "",
                "date": lines[1] if len(lines) > 1 else "",
                "author": lines[2] if len(lines) > 2 else "",
            }
        except subprocess.CalledProcessError:
            return {}

    def _get_commit_files(self, commit_hash: str) -> List[str]:
        """Get list of files changed in a commit."""
        try:
            result = self._run_git(
                ["diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash]
            )
            return [f.strip() for f in result.strip().split("\n") if f.strip()]
        except subprocess.CalledProcessError:
            return []


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "CommitRef",
    "CommitType",
    "TicketCommitLinker",
]
