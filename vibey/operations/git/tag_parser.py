"""
Git Tag Parser

Parses Vibey roadmap tags from Git repository.

Task: git-integration-1-task-009
Status: In Progress
"""

import re
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
from enum import Enum

from vibey.operations.git.log_analyzer import GitLogAnalyzer, TagInfo


class TagType(Enum):
    """Type of Vibey tag."""
    SPRINT_START = "sprint_start"
    SPRINT_END = "sprint_end"
    TASK_START = "task_start"
    TASK_END = "task_end"
    TRACK_MILESTONE = "track_milestone"
    UNKNOWN = "unknown"


@dataclass
class ParsedTag:
    """A parsed Vibey roadmap tag."""
    # Original tag info
    tag_info: TagInfo

    # Parsed components
    tag_type: TagType
    track_id: Optional[str] = None
    sprint_id: Optional[str] = None
    task_id: Optional[str] = None
    marker: Optional[str] = None

    # Hierarchical path
    path: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "name": self.tag_info.name,
            "sha": self.tag_info.sha,
            "type": self.tag_type.value,
            "track_id": self.track_id,
            "sprint_id": self.sprint_id,
            "task_id": self.task_id,
            "marker": self.marker,
            "path": self.path,
            "is_annotated": self.tag_info.is_annotated,
            "message": self.tag_info.message,
        }


class TagParser:
    """
    Parse Vibey roadmap tags from Git repository.

    Supported tag formats (from Sprint 0 addendum):
    - Sprint tags: sprint/<sprint-id>/start, sprint/<sprint-id>/end
    - Task tags: <track>/<sprint>/<task>/<marker>
    - Track milestones: track/<track-id>/<milestone>

    Examples:
        sprint/git-integration-1/start
        sprint/git-integration-1/end
        git-integration/git-integration-1/git-integration-1-task-001/start
        git-integration/git-integration-1/git-integration-1-task-001/completed
    """

    # Tag patterns
    SPRINT_TAG_PATTERN = re.compile(
        r'^sprint/(?P<sprint_id>[\w-]+)/(?P<marker>start|end)$'
    )

    TASK_TAG_PATTERN = re.compile(
        r'^(?P<track>[\w-]+)/(?P<sprint>[\w-]+)/(?P<task>[\w-]+)/(?P<marker>start|end|completed|blocked|[\w-]+)$'
    )

    TRACK_TAG_PATTERN = re.compile(
        r'^track/(?P<track_id>[\w-]+)/(?P<marker>[\w-]+)$'
    )

    def __init__(self, analyzer: Optional[GitLogAnalyzer] = None, repo_path: str = "."):
        """
        Initialize tag parser.

        Args:
            analyzer: GitLogAnalyzer instance (creates new one if None)
            repo_path: Path to git repository
        """
        self.analyzer = analyzer or GitLogAnalyzer(repo_path=repo_path)

    def get_all_tags(self) -> List[TagInfo]:
        """Get all tags from repository."""
        return self.analyzer.get_tags()

    def parse_tag(self, tag: TagInfo) -> ParsedTag:
        """
        Parse a tag to determine if it's a Vibey roadmap tag.

        Args:
            tag: TagInfo object

        Returns:
            ParsedTag with parsed components
        """
        name = tag.name

        # Try sprint tag format
        if match := self.SPRINT_TAG_PATTERN.match(name):
            return ParsedTag(
                tag_info=tag,
                tag_type=TagType.SPRINT_START if match.group('marker') == 'start' else TagType.SPRINT_END,
                sprint_id=match.group('sprint_id'),
                marker=match.group('marker'),
                path=name,
            )

        # Try task tag format
        if match := self.TASK_TAG_PATTERN.match(name):
            marker = match.group('marker')
            tag_type = TagType.TASK_START if marker == 'start' else TagType.TASK_END if marker == 'end' else TagType.UNKNOWN

            return ParsedTag(
                tag_info=tag,
                tag_type=tag_type,
                track_id=match.group('track'),
                sprint_id=match.group('sprint'),
                task_id=match.group('task'),
                marker=marker,
                path=name,
            )

        # Try track tag format
        if match := self.TRACK_TAG_PATTERN.match(name):
            return ParsedTag(
                tag_info=tag,
                tag_type=TagType.TRACK_MILESTONE,
                track_id=match.group('track_id'),
                marker=match.group('marker'),
                path=name,
            )

        # Unknown tag format
        return ParsedTag(
            tag_info=tag,
            tag_type=TagType.UNKNOWN,
            path=name,
        )

    def get_vibey_tags(self) -> List[ParsedTag]:
        """
        Get all Vibey roadmap tags.

        Returns:
            List of ParsedTag objects for Vibey tags only
        """
        all_tags = self.get_all_tags()
        parsed_tags = [self.parse_tag(tag) for tag in all_tags]
        return [pt for pt in parsed_tags if pt.tag_type != TagType.UNKNOWN]

    def get_sprint_tags(self, sprint_id: Optional[str] = None) -> List[ParsedTag]:
        """
        Get sprint tags.

        Args:
            sprint_id: Optional sprint ID to filter by

        Returns:
            List of sprint tags
        """
        vibey_tags = self.get_vibey_tags()
        sprint_tags = [
            pt for pt in vibey_tags
            if pt.tag_type in [TagType.SPRINT_START, TagType.SPRINT_END]
        ]

        if sprint_id:
            sprint_tags = [pt for pt in sprint_tags if pt.sprint_id == sprint_id]

        return sprint_tags

    def get_sprint_boundary_tags(self, sprint_id: str) -> Tuple[Optional[ParsedTag], Optional[ParsedTag]]:
        """
        Get start and end tags for a sprint.

        Args:
            sprint_id: Sprint identifier

        Returns:
            Tuple of (start_tag, end_tag), either may be None
        """
        sprint_tags = self.get_sprint_tags(sprint_id)

        start_tag = next((pt for pt in sprint_tags if pt.tag_type == TagType.SPRINT_START), None)
        end_tag = next((pt for pt in sprint_tags if pt.tag_type == TagType.SPRINT_END), None)

        return start_tag, end_tag

    def get_task_tags(self, task_id: Optional[str] = None) -> List[ParsedTag]:
        """
        Get task tags.

        Args:
            task_id: Optional task ID to filter by

        Returns:
            List of task tags
        """
        vibey_tags = self.get_vibey_tags()
        task_tags = [
            pt for pt in vibey_tags
            if pt.tag_type in [TagType.TASK_START, TagType.TASK_END] or
            (pt.task_id is not None and pt.tag_type == TagType.UNKNOWN)
        ]

        if task_id:
            task_tags = [pt for pt in task_tags if pt.task_id == task_id]

        return task_tags

    def get_task_boundary_tags(self, task_id: str) -> Tuple[Optional[ParsedTag], Optional[ParsedTag]]:
        """
        Get start and end tags for a task.

        Args:
            task_id: Task identifier

        Returns:
            Tuple of (start_tag, end_tag), either may be None
        """
        task_tags = self.get_task_tags(task_id)

        start_tag = next((pt for pt in task_tags if pt.tag_type == TagType.TASK_START), None)
        end_tag = next((pt for pt in task_tags if pt.tag_type == TagType.TASK_END), None)

        return start_tag, end_tag

    def get_commits_for_sprint_by_tags(self, sprint_id: str):
        """
        Get commits for a sprint using sprint boundary tags.

        Args:
            sprint_id: Sprint identifier

        Returns:
            List of CommitInfo objects, or None if tags don't exist
        """
        start_tag, end_tag = self.get_sprint_boundary_tags(sprint_id)

        if not start_tag or not end_tag:
            return None

        # Get commits between tags
        return self.analyzer.get_commits_between_tags(
            start_tag.tag_info.name,
            end_tag.tag_info.name
        )

    def get_commits_for_task_by_tags(self, task_id: str):
        """
        Get commits for a task using task boundary tags.

        Args:
            task_id: Task identifier

        Returns:
            List of CommitInfo objects, or None if tags don't exist
        """
        start_tag, end_tag = self.get_task_boundary_tags(task_id)

        if not start_tag or not end_tag:
            return None

        # Get commits between tags
        return self.analyzer.get_commits_between_tags(
            start_tag.tag_info.name,
            end_tag.tag_info.name
        )

    def get_tags_by_track(self) -> Dict[str, List[ParsedTag]]:
        """
        Get tags grouped by track.

        Returns:
            Dict mapping track_id to list of ParsedTag objects
        """
        vibey_tags = self.get_vibey_tags()

        by_track: Dict[str, List[ParsedTag]] = {}
        for tag in vibey_tags:
            if tag.track_id:
                if tag.track_id not in by_track:
                    by_track[tag.track_id] = []
                by_track[tag.track_id].append(tag)

        return by_track

    def get_tags_by_sprint(self) -> Dict[str, List[ParsedTag]]:
        """
        Get tags grouped by sprint.

        Returns:
            Dict mapping sprint_id to list of ParsedTag objects
        """
        vibey_tags = self.get_vibey_tags()

        by_sprint: Dict[str, List[ParsedTag]] = {}
        for tag in vibey_tags:
            if tag.sprint_id:
                if tag.sprint_id not in by_sprint:
                    by_sprint[tag.sprint_id] = []
                by_sprint[tag.sprint_id].append(tag)

        return by_sprint

    def has_sprint_tags(self, sprint_id: str) -> bool:
        """Check if a sprint has boundary tags."""
        start_tag, end_tag = self.get_sprint_boundary_tags(sprint_id)
        return start_tag is not None and end_tag is not None

    def has_task_tags(self, task_id: str) -> bool:
        """Check if a task has boundary tags."""
        start_tag, end_tag = self.get_task_boundary_tags(task_id)
        return start_tag is not None and end_tag is not None

    def suggest_sprint_tags(self, sprint_id: str) -> Tuple[str, str]:
        """
        Suggest tag names for a sprint.

        Args:
            sprint_id: Sprint identifier

        Returns:
            Tuple of (start_tag_name, end_tag_name)
        """
        return (
            f"sprint/{sprint_id}/start",
            f"sprint/{sprint_id}/end"
        )

    def suggest_task_tags(self, track_id: str, sprint_id: str, task_id: str) -> Tuple[str, str]:
        """
        Suggest tag names for a task.

        Args:
            track_id: Track identifier
            sprint_id: Sprint identifier
            task_id: Task identifier

        Returns:
            Tuple of (start_tag_name, end_tag_name)
        """
        return (
            f"{track_id}/{sprint_id}/{task_id}/start",
            f"{track_id}/{sprint_id}/{task_id}/end"
        )

    def validate_tag_name(self, tag_name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a Vibey tag name.

        Args:
            tag_name: Tag name to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Try to parse as each format
        if self.SPRINT_TAG_PATTERN.match(tag_name):
            return True, None

        if self.TASK_TAG_PATTERN.match(tag_name):
            return True, None

        if self.TRACK_TAG_PATTERN.match(tag_name):
            return True, None

        # Check for common mistakes
        if tag_name.startswith('sprint/') and tag_name.count('/') != 2:
            return False, "Sprint tags must be: sprint/<sprint-id>/<start|end>"

        if '/' in tag_name and not any(tag_name.startswith(prefix) for prefix in ['sprint/', 'track/']):
            return False, "Task tags must be: <track>/<sprint>/<task>/<marker>"

        return False, f"Unknown tag format: {tag_name}"


def get_sprint_commits_with_tags(
    sprint_id: str,
    repo_path: str = "."
) -> Optional[List]:
    """
    Quick helper to get sprint commits using tags.

    Args:
        sprint_id: Sprint identifier
        repo_path: Path to git repository

    Returns:
        List of commits, or None if tags don't exist
    """
    parser = TagParser(repo_path=repo_path)
    return parser.get_commits_for_sprint_by_tags(sprint_id)


def get_task_commits_with_tags(
    task_id: str,
    repo_path: str = "."
) -> Optional[List]:
    """
    Quick helper to get task commits using tags.

    Args:
        task_id: Task identifier
        repo_path: Path to git repository

    Returns:
        List of commits, or None if tags don't exist
    """
    parser = TagParser(repo_path=repo_path)
    return parser.get_commits_for_task_by_tags(task_id)
