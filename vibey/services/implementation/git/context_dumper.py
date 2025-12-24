"""
Context dumping at commit time for audit trail.

This module provides functionality to capture and persist the complete
context state at each commit during autonomous implementation mode.
This creates an audit trail that enables:
- Post-mortem analysis of implementation decisions
- Token usage tracking per commit
- File change attribution
- Decision history preservation

Design Reference:
- Context System v2 Architecture
- Implementation Mode Track Sprint 3

Usage:
    from vibey.services.implementation.git import CommitContextDumper
    from pathlib import Path

    dumper = CommitContextDumper(repo_root=Path("/path/to/repo"))
    context_path = dumper.dump_commit_context(
        ticket_id="01ABC123",
        commit_sha="abc1234def5678",
    )
"""

import json
import logging
import subprocess
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class CommitContext:
    """
    Full context state at commit time.

    Captures all relevant state information when a commit is made,
    enabling comprehensive audit trail and post-mortem analysis.

    Attributes:
        commit_sha: The full SHA of the commit
        ticket_id: The ticket this commit is associated with
        timestamp: When the context was captured
        files_modified: List of files changed in this commit
        token_usage: Token consumption data (input/output counts)
        decisions: Key decisions made during implementation
        task_state: Snapshot of ticket state at commit time
    """

    commit_sha: str
    ticket_id: str
    timestamp: datetime
    files_modified: List[str] = field(default_factory=list)
    token_usage: Optional[Dict[str, Any]] = None
    decisions: List[str] = field(default_factory=list)
    task_state: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert datetime to ISO format string
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CommitContext":
        """Create from dictionary."""
        # Parse timestamp if string
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


# =============================================================================
# COMMIT CONTEXT DUMPER
# =============================================================================


class CommitContextDumper:
    """
    Dumps context state at each commit.

    Creates a persistent audit trail of context state at each commit point,
    enabling post-mortem analysis, token tracking, and decision history.

    The context is stored in:
        .vibey/context/commits/{ticket_id}/{commit_sha}/
            context.yaml  - Main context file
            files.yaml    - Detailed file changes
            decisions.yaml - Key decisions made
            state.yaml    - Task state snapshot

    Attributes:
        repo_root: Root directory of the git repository
        context_root: Root directory for context storage

    Example:
        >>> dumper = CommitContextDumper(Path("/repo"))
        >>> path = dumper.dump_commit_context("01ABC", "abc123")
        >>> print(f"Context saved to: {path}")
    """

    def __init__(self, repo_root: Path):
        """
        Initialize the context dumper.

        Args:
            repo_root: Root directory of the git repository
        """
        self.repo_root = repo_root
        self.context_root = repo_root / ".vibey" / "context" / "commits"

    def dump_commit_context(
        self,
        ticket_id: str,
        commit_sha: str,
        output_dir: Optional[Path] = None,
        token_usage: Optional[Dict[str, Any]] = None,
        decisions: Optional[List[str]] = None,
        task_state: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Dump full context state at commit time.

        Creates a directory structure containing:
        - context.yaml: Main context summary
        - files.yaml: Detailed file changes from the commit
        - decisions.yaml: Key decisions made during implementation
        - state.yaml: Task state snapshot

        Args:
            ticket_id: The ticket ID this commit is associated with
            commit_sha: The full or abbreviated git commit SHA
            output_dir: Optional override for output directory
            token_usage: Optional token usage data to include
            decisions: Optional list of decisions to include
            task_state: Optional task state snapshot to include

        Returns:
            Path to the context directory created

        Raises:
            OSError: If directory creation fails
            subprocess.CalledProcessError: If git commands fail
        """
        # Determine output directory
        if output_dir is None:
            output_dir = self.context_root / ticket_id / commit_sha[:12]

        # Create directory structure
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Dumping commit context to: {output_dir}")

        # Get files modified in commit
        files_modified = self._get_commit_files(commit_sha)

        # Create main context object
        context = CommitContext(
            commit_sha=commit_sha,
            ticket_id=ticket_id,
            timestamp=datetime.now(timezone.utc),
            files_modified=files_modified,
            token_usage=token_usage,
            decisions=decisions or [],
            task_state=task_state,
        )

        # Write main context file
        context_file = output_dir / "context.yaml"
        self._write_yaml(context_file, context.to_dict())

        # Dump detailed files info
        self._dump_files(output_dir, commit_sha)

        # Dump decisions if provided
        if decisions:
            self._dump_decisions(output_dir, ticket_id, decisions)

        # Dump state if provided
        if task_state:
            self._dump_state(output_dir, ticket_id, task_state)

        logger.debug(f"Context dump complete: {output_dir}")

        return output_dir

    def _get_commit_files(self, commit_sha: str) -> List[str]:
        """
        Get list of files modified in a commit.

        Args:
            commit_sha: The commit SHA to inspect

        Returns:
            List of file paths modified in the commit
        """
        try:
            result = subprocess.run(
                ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_sha],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True,
            )
            files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
            return files
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to get commit files: {e}")
            return []
        except FileNotFoundError:
            logger.warning("git not found in PATH")
            return []

    def _dump_files(self, output_dir: Path, commit_sha: str):
        """
        Dump detailed file changes from commit.

        Creates files.yaml with:
        - added: List of added files
        - modified: List of modified files
        - deleted: List of deleted files
        - details: Per-file change statistics

        Args:
            output_dir: Directory to write the file
            commit_sha: The commit SHA to inspect
        """
        files_data: Dict[str, Any] = {
            "commit_sha": commit_sha,
            "added": [],
            "modified": [],
            "deleted": [],
            "details": [],
        }

        try:
            # Get file status (A=added, M=modified, D=deleted)
            result = subprocess.run(
                [
                    "git",
                    "diff-tree",
                    "--no-commit-id",
                    "--name-status",
                    "-r",
                    commit_sha,
                ],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True,
            )

            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                parts = line.split("\t")
                if len(parts) >= 2:
                    status = parts[0]
                    filepath = parts[1]

                    if status.startswith("A"):
                        files_data["added"].append(filepath)
                    elif status.startswith("M"):
                        files_data["modified"].append(filepath)
                    elif status.startswith("D"):
                        files_data["deleted"].append(filepath)

            # Get line statistics per file
            stat_result = subprocess.run(
                ["git", "diff-tree", "--no-commit-id", "--numstat", "-r", commit_sha],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True,
            )

            for line in stat_result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                parts = line.split("\t")
                if len(parts) >= 3:
                    added_lines = parts[0]
                    deleted_lines = parts[1]
                    filepath = parts[2]

                    files_data["details"].append(
                        {
                            "path": filepath,
                            "lines_added": (
                                int(added_lines) if added_lines != "-" else 0
                            ),
                            "lines_deleted": (
                                int(deleted_lines) if deleted_lines != "-" else 0
                            ),
                        }
                    )

        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to get file details: {e}")
        except FileNotFoundError:
            logger.warning("git not found in PATH")

        files_file = output_dir / "files.yaml"
        self._write_yaml(files_file, files_data)

    def _dump_decisions(
        self, output_dir: Path, ticket_id: str, decisions: List[str]
    ):
        """
        Dump key decisions made during implementation.

        Creates decisions.yaml with timestamped decision records.

        Args:
            output_dir: Directory to write the file
            ticket_id: The ticket ID for context
            decisions: List of decision descriptions
        """
        decisions_data = {
            "ticket_id": ticket_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "decisions": [
                {"index": i, "description": d} for i, d in enumerate(decisions)
            ],
        }

        decisions_file = output_dir / "decisions.yaml"
        self._write_yaml(decisions_file, decisions_data)

    def _dump_state(
        self, output_dir: Path, ticket_id: str, task_state: Dict[str, Any]
    ):
        """
        Dump task state snapshot.

        Creates state.yaml with the current task state.

        Args:
            output_dir: Directory to write the file
            ticket_id: The ticket ID for context
            task_state: The task state dictionary to dump
        """
        state_data = {
            "ticket_id": ticket_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "state": task_state,
        }

        state_file = output_dir / "state.yaml"
        self._write_yaml(state_file, state_data)

    def _write_yaml(self, path: Path, data: Dict[str, Any]):
        """
        Write data to a YAML file.

        Args:
            path: Path to write the file
            data: Dictionary data to serialize
        """
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(
                data,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

    def load_commit_context(
        self, ticket_id: str, commit_sha: str
    ) -> Optional[CommitContext]:
        """
        Load a previously dumped commit context.

        Args:
            ticket_id: The ticket ID
            commit_sha: The commit SHA (full or abbreviated)

        Returns:
            CommitContext if found, None otherwise
        """
        # Try both full and abbreviated SHA
        for sha_len in [12, len(commit_sha)]:
            context_dir = self.context_root / ticket_id / commit_sha[:sha_len]
            context_file = context_dir / "context.yaml"

            if context_file.exists():
                try:
                    with open(context_file, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                    return CommitContext.from_dict(data)
                except Exception as e:
                    logger.warning(f"Failed to load context: {e}")

        return None

    def list_ticket_contexts(self, ticket_id: str) -> List[Path]:
        """
        List all context dumps for a ticket.

        Args:
            ticket_id: The ticket ID

        Returns:
            List of paths to context directories, sorted by commit SHA
        """
        ticket_dir = self.context_root / ticket_id
        if not ticket_dir.exists():
            return []

        contexts = []
        for entry in ticket_dir.iterdir():
            if entry.is_dir() and (entry / "context.yaml").exists():
                contexts.append(entry)

        return sorted(contexts)

    def get_total_token_usage(self, ticket_id: str) -> Dict[str, int]:
        """
        Get total token usage across all commits for a ticket.

        Args:
            ticket_id: The ticket ID

        Returns:
            Dictionary with total input and output token counts
        """
        total = {"input": 0, "output": 0}

        for context_path in self.list_ticket_contexts(ticket_id):
            context = self.load_commit_context(ticket_id, context_path.name)
            if context and context.token_usage:
                total["input"] += context.token_usage.get("input", 0)
                total["output"] += context.token_usage.get("output", 0)

        return total


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "CommitContext",
    "CommitContextDumper",
]
