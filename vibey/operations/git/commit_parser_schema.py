"""
Commit Message Parser Schema

Defines data structures and interfaces for parsing Git commit messages
to extract Vibey roadmap references (tasks, sprints, tracks).

Task: git-integration-1-task-001
Status: In Progress
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
import re


class CommitFormat(Enum):
    """Supported commit message formats."""
    CONVENTIONAL = "conventional"  # feat(task-id): description
    FOOTER = "footer"              # Task: task-id in footer
    BRACKET = "bracket"            # [task-id] description
    INLINE = "inline"              # task-id anywhere in message


class TaskStatus(Enum):
    """Task status that can be indicated in commits."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    REVERTED = "reverted"


@dataclass
class TaskReference:
    """A reference to a task from a commit message."""
    task_id: str
    format: CommitFormat
    status: Optional[TaskStatus] = None
    confidence: float = 1.0  # 0.0 to 1.0, lower for inline matches

    # Location information
    line_number: Optional[int] = None
    match_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "task_id": self.task_id,
            "format": self.format.value,
            "status": self.status.value if self.status else None,
            "confidence": self.confidence,
            "line_number": self.line_number,
            "match_text": self.match_text,
        }


@dataclass
class SprintReference:
    """A reference to a sprint from a commit message."""
    sprint_id: str
    status: Optional[TaskStatus] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "sprint_id": self.sprint_id,
            "status": self.status.value if self.status else None,
        }


@dataclass
class TrackReference:
    """A reference to a track from a commit message."""
    track_id: str
    status: Optional[TaskStatus] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "track_id": self.track_id,
            "status": self.status.value if self.status else None,
        }


@dataclass
class CommitMessageParts:
    """Structured parts of a commit message."""
    subject: str
    body: Optional[str] = None
    footers: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "subject": self.subject,
            "body": self.body,
            "footers": self.footers,
        }


@dataclass
class ParsedCommit:
    """Result of parsing a commit message."""
    # Original message
    message: str
    sha: Optional[str] = None

    # Structured parts
    parts: Optional[CommitMessageParts] = None

    # Conventional commit fields
    type: Optional[str] = None
    scope: Optional[str] = None
    breaking: bool = False
    description: Optional[str] = None

    # Vibey references
    tasks: List[TaskReference] = field(default_factory=list)
    sprint: Optional[SprintReference] = None
    track: Optional[TrackReference] = None

    # Metadata
    format_detected: List[CommitFormat] = field(default_factory=list)
    parse_errors: List[str] = field(default_factory=list)
    parse_warnings: List[str] = field(default_factory=list)

    @property
    def has_task_reference(self) -> bool:
        """Check if commit references any tasks."""
        return len(self.tasks) > 0

    @property
    def primary_task(self) -> Optional[TaskReference]:
        """Get the primary task reference (highest confidence)."""
        if not self.tasks:
            return None
        return max(self.tasks, key=lambda t: t.confidence)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "message": self.message,
            "sha": self.sha,
            "parts": self.parts.to_dict() if self.parts else None,
            "type": self.type,
            "scope": self.scope,
            "breaking": self.breaking,
            "description": self.description,
            "tasks": [t.to_dict() for t in self.tasks],
            "sprint": self.sprint.to_dict() if self.sprint else None,
            "track": self.track.to_dict() if self.track else None,
            "format_detected": [f.value for f in self.format_detected],
            "parse_errors": self.parse_errors,
            "parse_warnings": self.parse_warnings,
        }


@dataclass
class ParserConfig:
    """Configuration for commit message parser."""
    # Format preferences (in priority order)
    preferred_formats: List[CommitFormat] = field(default_factory=lambda: [
        CommitFormat.FOOTER,
        CommitFormat.CONVENTIONAL,
        CommitFormat.BRACKET,
    ])

    # Parsing options
    parse_inline: bool = False
    case_sensitive: bool = False

    # Validation options
    require_task_reference: bool = False
    validate_task_exists: bool = True
    validate_type: bool = True

    # Valid conventional commit types
    valid_types: List[str] = field(default_factory=lambda: [
        "feat", "fix", "docs", "style", "refactor",
        "test", "chore", "perf", "ci", "build", "revert"
    ])

    # Task ID pattern (matches legacy slug format OR ULID format)
    # ULID: 26 alphanumeric chars starting with 01
    task_id_pattern: str = r"^(?:[\w-]+-\d+-task-\d+|01[0-9A-HJKMNP-TV-Z]{24})$"

    # Length limits
    subject_max_length: int = 72
    body_max_length: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "preferred_formats": [f.value for f in self.preferred_formats],
            "parse_inline": self.parse_inline,
            "case_sensitive": self.case_sensitive,
            "require_task_reference": self.require_task_reference,
            "validate_task_exists": self.validate_task_exists,
            "validate_type": self.validate_type,
            "valid_types": self.valid_types,
            "task_id_pattern": self.task_id_pattern,
            "subject_max_length": self.subject_max_length,
            "body_max_length": self.body_max_length,
        }


# Regex patterns for parsing
class RegexPatterns:
    """Compiled regex patterns for commit parsing."""

    # Conventional Commits with task scope
    CONVENTIONAL = re.compile(
        r'^(?P<type>\w+)'
        r'(?:\((?P<scope>[\w-]+)\))?'
        r'(?P<breaking>!)?'
        r':\s*'
        r'(?P<description>.+)$'
    )

    # Footer pattern (Git trailer format)
    FOOTER = re.compile(
        r'^(?P<key>[\w-]+):\s*(?P<value>.+)$',
        re.MULTILINE
    )

    # Bracket notation (legacy slug OR ULID)
    BRACKET = re.compile(
        r'^\[(?P<task_id>(?:[\w-]+-\d+-task-\d+|01[0-9A-HJKMNP-TV-Z]{24}))\]\s*(?P<description>.+)$'
    )

    # Task ID (full format - legacy slug OR ULID)
    TASK_ID_FULL = re.compile(
        r'(?:(?P<track>[\w-]+)-(?P<sprint>\d+)-task-(?P<number>\d+)|(?P<ulid>01[0-9A-HJKMNP-TV-Z]{24}))'
    )

    # Task ID (short format)
    TASK_ID_SHORT = re.compile(
        r'task-(?P<number>\d+)'
    )

    # Inline task reference (legacy slug OR ULID)
    INLINE = re.compile(
        r'\b(?:task:\s*)?(?P<task_id>(?:[\w]+-\d+-task-\d+|01[0-9A-HJKMNP-TV-Z]{24}))\b',
        re.IGNORECASE
    )

    # Sprint reference (legacy slug OR ULID)
    SPRINT = re.compile(
        r'sprint:\s*(?P<sprint_id>(?:[\w-]+-\d+|01[0-9A-HJKMNP-TV-Z]{24}))',
        re.IGNORECASE
    )

    # Track reference (legacy slug OR ULID)
    TRACK = re.compile(
        r'track:\s*(?P<track_id>(?:[\w-]+|01[0-9A-HJKMNP-TV-Z]{24}))',
        re.IGNORECASE
    )


# Status keywords mapping
STATUS_KEYWORDS = {
    'closes': TaskStatus.COMPLETED,
    'completes': TaskStatus.COMPLETED,
    'finishes': TaskStatus.COMPLETED,
    'fixes': TaskStatus.COMPLETED,
    'resolves': TaskStatus.COMPLETED,
    'addresses': TaskStatus.IN_PROGRESS,
    'starts': TaskStatus.IN_PROGRESS,
    'wip': TaskStatus.IN_PROGRESS,
    'blocks': TaskStatus.BLOCKED,
    'blocked': TaskStatus.BLOCKED,
    'reverts': TaskStatus.REVERTED,
}


class CommitParserInterface:
    """
    Interface for commit message parser implementations.

    This defines the contract that all parser implementations must follow.
    """

    def parse(self, message: str, sha: Optional[str] = None) -> ParsedCommit:
        """
        Parse a commit message and extract Vibey references.

        Args:
            message: The commit message to parse
            sha: Optional commit SHA for reference

        Returns:
            ParsedCommit object with extracted information
        """
        raise NotImplementedError

    def parse_batch(self, commits: List[Dict[str, str]]) -> List[ParsedCommit]:
        """
        Parse multiple commits in batch.

        Args:
            commits: List of dicts with 'message' and optional 'sha' keys

        Returns:
            List of ParsedCommit objects
        """
        raise NotImplementedError

    def validate(self, parsed: ParsedCommit) -> List[str]:
        """
        Validate a parsed commit against configuration rules.

        Args:
            parsed: The ParsedCommit to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        raise NotImplementedError

    def suggest_fixes(self, parsed: ParsedCommit) -> List[str]:
        """
        Suggest fixes for validation errors.

        Args:
            parsed: The ParsedCommit with potential issues

        Returns:
            List of human-readable fix suggestions
        """
        raise NotImplementedError


@dataclass
class ParseResult:
    """
    High-level result of parsing operation.

    Used for batch operations and reporting.
    """
    total_commits: int
    parsed_successfully: int
    parse_errors: int

    commits_with_tasks: int
    commits_without_tasks: int

    unique_tasks: List[str] = field(default_factory=list)
    unique_sprints: List[str] = field(default_factory=list)
    unique_tracks: List[str] = field(default_factory=list)

    format_usage: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "total_commits": self.total_commits,
            "parsed_successfully": self.parsed_successfully,
            "parse_errors": self.parse_errors,
            "commits_with_tasks": self.commits_with_tasks,
            "commits_without_tasks": self.commits_without_tasks,
            "unique_tasks": self.unique_tasks,
            "unique_sprints": self.unique_sprints,
            "unique_tracks": self.unique_tracks,
            "format_usage": self.format_usage,
        }
