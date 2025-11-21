"""
Commit-to-Task Mapping Algorithm

This module provides automated mapping of git commits to roadmap tasks based on
commit messages, file changes, timestamps, and author information.

Confidence scoring formula:
    confidence = (
        keyword_match * 0.40 +
        file_path_match * 0.35 +
        temporal_match * 0.15 +
        author_match * 0.10
    )

Confidence levels:
    - High (90-100): Exact task ID in message, files in task directory
    - Medium (60-89): Track ID + keywords, relevant files, aligned timestamp
    - Low (30-59): Keywords only, loosely related files, within track period
    - No match (0-29): No keyword overlap, unrelated files

Author: Vibey Framework
Created: 2025-11-20
Sprint: roadmap-integrity-fixes-1
Task: roadmap-integrity-fixes-1-task-001
"""

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
import yaml


@dataclass
class Task:
    """Represents a roadmap task with metadata for matching."""
    id: str
    title: str
    description: str
    track_id: str
    sprint_id: str
    created: Optional[datetime]
    started: Optional[datetime]
    completed: Optional[datetime]
    assigned_agent: Optional[str]

    def get_keywords(self) -> Set[str]:
        """Extract keywords from task data."""
        keywords = set()

        # Task ID components (highest weight)
        keywords.update(self.id.split('-'))

        # Title words (high weight)
        title_words = re.findall(r'\b\w+\b', self.title.lower())
        keywords.update(w for w in title_words if len(w) > 3)

        # Track and sprint components (medium weight)
        keywords.update(self.track_id.split('-'))
        keywords.update(self.sprint_id.split('-'))

        # Description keywords (medium weight, selective)
        if self.description:
            desc_words = re.findall(r'\b\w+\b', self.description.lower())
            # Filter to meaningful words (length > 4, not common words)
            common_words = {'this', 'that', 'with', 'from', 'have', 'will',
                          'been', 'were', 'their', 'there', 'these', 'those',
                          'when', 'where', 'which', 'while', 'about', 'would',
                          'should', 'could', 'being', 'make', 'made'}
            keywords.update(w for w in desc_words if len(w) > 4 and w not in common_words)

        return keywords


@dataclass
class Commit:
    """Represents a git commit with metadata for matching."""
    sha: str
    message: str
    timestamp: datetime
    author_name: str
    author_email: str
    files_changed: List[str]
    lines_added: int = 0
    lines_deleted: int = 0

    def get_keywords(self) -> Set[str]:
        """Extract keywords from commit data."""
        keywords = set()

        # Extract from commit message (high weight)
        message_words = re.findall(r'\b\w+\b', self.message.lower())
        keywords.update(w for w in message_words if len(w) > 3)

        # Extract from file paths (high weight)
        for file_path in self.files_changed:
            path_parts = re.split(r'[/._-]', file_path.lower())
            keywords.update(p for p in path_parts if len(p) > 2)

        return keywords

    def get_primary_directories(self) -> Set[str]:
        """Get primary directories affected by this commit."""
        directories = set()
        for file_path in self.files_changed:
            parts = Path(file_path).parts
            if len(parts) > 0:
                directories.add(parts[0])
            if len(parts) > 1:
                directories.add(f"{parts[0]}/{parts[1]}")
        return directories


@dataclass
class TaskMatch:
    """Represents a commit-to-task match with confidence scoring."""
    task_id: str
    confidence: float
    keyword_score: float
    file_path_score: float
    temporal_score: float
    author_score: float
    match_details: Dict[str, any]


class CommitMapper:
    """Main class for mapping commits to tasks."""

    def __init__(self, tasks: List[Task]):
        """
        Initialize mapper with task list.

        Args:
            tasks: List of Task objects to match against
        """
        self.tasks = tasks
        self.task_by_id = {task.id: task for task in tasks}

        # Build track-to-files mapping for path scoring
        self.track_file_patterns = self._build_file_patterns()

    def _build_file_patterns(self) -> Dict[str, List[str]]:
        """Build mapping of track IDs to common file path patterns."""
        patterns = {
            'roadmap-system': [
                'vibey/roadmap/',
                '.vibey/roadmap/',
                'vibey/operations/roadmap/'
            ],
            'testing-system': [
                'tests/',
                'vibey/tests/',
                'pytest.ini',
                'conftest.py'
            ],
            'documentation-system': [
                'docs/',
                'README.md',
                '*.md',
                'CLAUDE.md'
            ],
            'interface-unification': [
                'vibey/cli/',
                'framework/mcp/',
                'vibey/commands/'
            ],
            'standards-system': [
                'vibey/standards/',
                '.vibey/standards/',
                'standards/'
            ],
            'roadmap-integrity-fixes': [
                '.vibey/roadmap/roadmap-integrity-fixes/',
                'scripts/validate-roadmap',
                'scripts/roadmap-health'
            ]
        }

        # For each task, inherit patterns from its track
        task_patterns = {}
        for task in self.tasks:
            base_track = task.track_id.split('-')[0] if '-' in task.track_id else task.track_id

            # Check if track has defined patterns
            matching_patterns = []
            for track_key, pattern_list in patterns.items():
                if base_track in track_key or track_key in task.track_id:
                    matching_patterns.extend(pattern_list)

            # Add task-specific directory patterns
            matching_patterns.append(f".vibey/roadmap/{task.track_id}/")
            matching_patterns.append(f".vibey/roadmap/{task.track_id}/{task.sprint_id}/")

            task_patterns[task.id] = matching_patterns

        return task_patterns

    def extract_task_keywords(self, task: Task) -> Dict[str, float]:
        """
        Extract keywords from task with weights.

        Args:
            task: Task object

        Returns:
            Dict mapping keywords to weights (0.0-1.0)
        """
        keywords_weighted = {}

        # Task ID (weight 1.0 - highest)
        task_id_parts = task.id.split('-')
        for part in task_id_parts:
            if len(part) > 2:
                keywords_weighted[part.lower()] = 1.0

        # Title words (weight 0.9)
        title_words = re.findall(r'\b\w+\b', task.title.lower())
        for word in title_words:
            if len(word) > 3:
                keywords_weighted[word] = max(keywords_weighted.get(word, 0), 0.9)

        # Track/Sprint ID (weight 0.7)
        for track_part in task.track_id.split('-'):
            if len(track_part) > 2:
                keywords_weighted[track_part.lower()] = max(keywords_weighted.get(track_part, 0), 0.7)

        # Description keywords (weight 0.5 - selective)
        if task.description:
            desc_words = re.findall(r'\b\w{5,}\b', task.description.lower())
            common_words = {'this', 'that', 'with', 'from', 'have', 'will', 'implementation',
                          'system', 'complete', 'update', 'create', 'should', 'would'}
            for word in desc_words:
                if word not in common_words:
                    keywords_weighted[word] = max(keywords_weighted.get(word, 0), 0.5)

        return keywords_weighted

    def extract_commit_keywords(self, commit: Commit) -> Dict[str, float]:
        """
        Extract keywords from commit with weights.

        Args:
            commit: Commit object

        Returns:
            Dict mapping keywords to weights (0.0-1.0)
        """
        keywords_weighted = {}

        # Commit message subject (first line) - weight 1.0
        message_lines = commit.message.split('\n')
        if message_lines:
            subject_words = re.findall(r'\b\w+\b', message_lines[0].lower())
            for word in subject_words:
                if len(word) > 3:
                    keywords_weighted[word] = 1.0

        # Commit message body - weight 0.7
        if len(message_lines) > 1:
            body = ' '.join(message_lines[1:])
            body_words = re.findall(r'\b\w+\b', body.lower())
            for word in body_words:
                if len(word) > 3:
                    keywords_weighted[word] = max(keywords_weighted.get(word, 0), 0.7)

        # File paths - weight 0.9
        for file_path in commit.files_changed:
            path_parts = re.split(r'[/._-]', file_path.lower())
            for part in path_parts:
                if len(part) > 2:
                    keywords_weighted[part] = max(keywords_weighted.get(part, 0), 0.9)

        return keywords_weighted

    def calculate_keyword_match(self, task_keywords: Dict[str, float],
                                commit_keywords: Dict[str, float]) -> Tuple[float, Dict]:
        """
        Calculate keyword match score between task and commit.

        Args:
            task_keywords: Task keywords with weights
            commit_keywords: Commit keywords with weights

        Returns:
            Tuple of (score 0-100, match details dict)
        """
        if not task_keywords or not commit_keywords:
            return 0.0, {'matched_keywords': [], 'total_task_keywords': len(task_keywords)}

        # Check for exact task ID match (instant high score)
        task_id_in_message = any(k in commit_keywords for k in task_keywords.keys()
                                if len(k) > 10)  # Task IDs are long
        if task_id_in_message:
            return 100.0, {
                'exact_task_id_match': True,
                'matched_keywords': list(set(task_keywords.keys()) & set(commit_keywords.keys()))
            }

        # Calculate weighted overlap
        matched_keywords = []
        total_weight = 0.0
        matched_weight = 0.0

        for task_kw, task_weight in task_keywords.items():
            total_weight += task_weight
            if task_kw in commit_keywords:
                commit_weight = commit_keywords[task_kw]
                matched_weight += min(task_weight, commit_weight)
                matched_keywords.append(task_kw)

        # Score as percentage of total possible weight
        score = (matched_weight / total_weight * 100) if total_weight > 0 else 0.0

        details = {
            'matched_keywords': matched_keywords,
            'match_count': len(matched_keywords),
            'total_task_keywords': len(task_keywords),
            'matched_weight': matched_weight,
            'total_weight': total_weight
        }

        return min(score, 100.0), details

    def calculate_file_path_score(self, commit: Commit, task: Task) -> Tuple[float, Dict]:
        """
        Calculate file path relevance score.

        Args:
            commit: Commit object
            task: Task object

        Returns:
            Tuple of (score 0-100, match details dict)
        """
        if not commit.files_changed:
            return 0.0, {'reason': 'no_files_changed'}

        task_patterns = self.track_file_patterns.get(task.id, [])
        if not task_patterns:
            # Fallback to track-level patterns
            task_patterns = [f".vibey/roadmap/{task.track_id}/"]

        matched_files = []
        total_files = len(commit.files_changed)

        for file_path in commit.files_changed:
            file_lower = file_path.lower()
            for pattern in task_patterns:
                pattern_lower = pattern.lower()

                # Handle wildcard patterns
                if '*' in pattern_lower:
                    pattern_regex = pattern_lower.replace('*', '.*')
                    if re.search(pattern_regex, file_lower):
                        matched_files.append(file_path)
                        break
                # Exact directory match
                elif file_lower.startswith(pattern_lower):
                    matched_files.append(file_path)
                    break

        match_ratio = len(matched_files) / total_files if total_files > 0 else 0.0
        score = match_ratio * 100

        details = {
            'matched_files': matched_files,
            'total_files': total_files,
            'match_ratio': match_ratio,
            'patterns_used': task_patterns
        }

        return score, details

    def calculate_temporal_score(self, commit: Commit, task: Task) -> Tuple[float, Dict]:
        """
        Calculate temporal alignment score.

        Args:
            commit: Commit object
            task: Task object

        Returns:
            Tuple of (score 0-100, match details dict)
        """
        commit_time = commit.timestamp

        # If task has no dates, can't score temporally
        if not task.created:
            return 50.0, {'reason': 'no_task_dates', 'neutral_score': True}

        # Commit before task created: very unlikely to be related
        if commit_time < task.created:
            days_before = (task.created - commit_time).days
            if days_before > 30:
                return 0.0, {'reason': 'commit_too_early', 'days_before_creation': days_before}
            else:
                # Might be backfilling old work
                return 30.0, {'reason': 'slightly_before_creation', 'days_before': days_before}

        # Commit after task completed: unlikely unless fixing bugs
        if task.completed and commit_time > task.completed:
            days_after = (commit_time - task.completed).days
            if days_after > 7:
                return 20.0, {'reason': 'commit_after_completion', 'days_after': days_after}
            else:
                # Might be quick fix
                return 60.0, {'reason': 'shortly_after_completion', 'days_after': days_after}

        # Commit during task active period: high confidence
        if task.started and task.completed:
            if task.started <= commit_time <= task.completed:
                return 100.0, {'reason': 'during_active_period',
                              'task_duration_days': (task.completed - task.started).days}

        # Commit after task started but before completion
        if task.started and commit_time >= task.started:
            if not task.completed:
                # Task still in progress
                return 90.0, {'reason': 'during_in_progress_task'}
            else:
                # Between started and completed
                return 100.0, {'reason': 'during_task_window'}

        # Commit between creation and start
        if task.created and commit_time >= task.created:
            if task.started:
                if commit_time < task.started:
                    return 70.0, {'reason': 'between_creation_and_start'}
            else:
                # Task created but not started - might be planning
                return 80.0, {'reason': 'after_creation_not_started'}

        # Default: within reasonable timeframe
        return 50.0, {'reason': 'unknown_temporal_relationship'}

    def calculate_author_score(self, commit: Commit, task: Task) -> Tuple[float, Dict]:
        """
        Calculate author match score.

        Args:
            commit: Commit object
            task: Task object

        Returns:
            Tuple of (score 0-100, match details dict)
        """
        if not task.assigned_agent:
            return 50.0, {'reason': 'no_assigned_agent', 'neutral_score': True}

        # Simple heuristic: if commit author contains agent name, likely match
        author_lower = commit.author_name.lower()
        agent_lower = task.assigned_agent.lower()

        # Direct match
        if agent_lower in author_lower or author_lower in agent_lower:
            return 100.0, {'reason': 'author_matches_agent',
                          'author': commit.author_name,
                          'agent': task.assigned_agent}

        # Check email domain match (e.g., @anthropic.com for Claude)
        if 'claude' in agent_lower or 'ai' in agent_lower:
            if 'anthropic' in commit.author_email.lower() or 'noreply' in commit.author_email.lower():
                return 80.0, {'reason': 'ai_agent_email_match'}

        # No match
        return 0.0, {'reason': 'author_mismatch',
                    'author': commit.author_name,
                    'expected_agent': task.assigned_agent}

    def map_commit_to_tasks(self, commit: Commit, top_n: int = 3) -> List[TaskMatch]:
        """
        Map a commit to top N matching tasks with confidence scores.

        Args:
            commit: Commit object to map
            top_n: Number of top matches to return

        Returns:
            List of TaskMatch objects, sorted by confidence (highest first)
        """
        matches = []

        # Extract commit keywords once
        commit_keywords = self.extract_commit_keywords(commit)

        for task in self.tasks:
            # Extract task keywords
            task_keywords = self.extract_task_keywords(task)

            # Calculate component scores
            keyword_score, keyword_details = self.calculate_keyword_match(task_keywords, commit_keywords)
            file_score, file_details = self.calculate_file_path_score(commit, task)
            temporal_score, temporal_details = self.calculate_temporal_score(commit, task)
            author_score, author_details = self.calculate_author_score(commit, task)

            # Calculate weighted confidence score
            confidence = (
                keyword_score * 0.40 +
                file_score * 0.35 +
                temporal_score * 0.15 +
                author_score * 0.10
            )

            # Compile match details
            match_details = {
                'keyword_details': keyword_details,
                'file_details': file_details,
                'temporal_details': temporal_details,
                'author_details': author_details,
                'task_title': task.title,
                'task_track': task.track_id
            }

            match = TaskMatch(
                task_id=task.id,
                confidence=confidence,
                keyword_score=keyword_score,
                file_path_score=file_score,
                temporal_score=temporal_score,
                author_score=author_score,
                match_details=match_details
            )

            matches.append(match)

        # Sort by confidence (descending)
        matches.sort(key=lambda m: m.confidence, reverse=True)

        return matches[:top_n]

    def get_confidence_level(self, confidence: float) -> str:
        """
        Get confidence level label for a score.

        Args:
            confidence: Confidence score 0-100

        Returns:
            String label: 'high', 'medium', 'low', or 'no_match'
        """
        if confidence >= 90:
            return 'high'
        elif confidence >= 60:
            return 'medium'
        elif confidence >= 30:
            return 'low'
        else:
            return 'no_match'


def load_tasks_from_roadmap(roadmap_path: Path) -> List[Task]:
    """
    Load all tasks from roadmap directory structure.

    Args:
        roadmap_path: Path to .vibey/roadmap directory

    Returns:
        List of Task objects
    """
    tasks = []

    # Find all task.yaml files
    for task_file in roadmap_path.rglob('task.yaml'):
        try:
            with open(task_file) as f:
                data = yaml.safe_load(f)
                task_data = data.get('task', {})

                # Parse dates
                created = None
                if task_data.get('created'):
                    try:
                        created = datetime.fromisoformat(task_data['created'].replace('Z', '+00:00'))
                    except:
                        pass

                started = None
                if task_data.get('started'):
                    try:
                        started = datetime.fromisoformat(task_data['started'].replace('Z', '+00:00'))
                    except:
                        pass

                completed = None
                if task_data.get('completed'):
                    try:
                        completed = datetime.fromisoformat(task_data['completed'].replace('Z', '+00:00'))
                    except:
                        pass

                task = Task(
                    id=task_data.get('id', ''),
                    title=task_data.get('title', ''),
                    description=task_data.get('description', ''),
                    track_id=task_data.get('track_id', ''),
                    sprint_id=task_data.get('sprint_id', ''),
                    created=created,
                    started=started,
                    completed=completed,
                    assigned_agent=task_data.get('assigned_agent')
                )

                tasks.append(task)
        except Exception as e:
            print(f"Warning: Could not load task from {task_file}: {e}")
            continue

    return tasks
