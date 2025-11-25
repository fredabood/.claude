"""
Commit Message Parser Implementation

Parses Git commit messages to extract Vibey roadmap references.

Task: git-integration-1-task-002
Status: In Progress
"""

from typing import List, Dict, Optional, Set
import re

from vibey.operations.git.commit_parser_schema import (
    CommitFormat,
    TaskStatus,
    TaskReference,
    SprintReference,
    TrackReference,
    CommitMessageParts,
    ParsedCommit,
    ParserConfig,
    RegexPatterns,
    CommitParserInterface,
    ParseResult,
    STATUS_KEYWORDS,
)


class CommitParser(CommitParserInterface):
    """
    Parse Git commit messages to extract Vibey roadmap references.

    Supports multiple commit message formats:
    - Conventional commits: feat(task-id): description
    - Footer references: Task: task-id
    - Bracket notation: [task-id] description
    - Inline references: task-id anywhere (optional)

    Thread-safe and suitable for batch processing.
    """

    def __init__(self, config: Optional[ParserConfig] = None):
        """
        Initialize parser with configuration.

        Args:
            config: Parser configuration, uses defaults if None
        """
        self.config = config or ParserConfig()

    def parse(self, message: str, sha: Optional[str] = None) -> ParsedCommit:
        """
        Parse a commit message and extract Vibey references.

        Args:
            message: The commit message to parse
            sha: Optional commit SHA for reference

        Returns:
            ParsedCommit object with extracted information
        """
        result = ParsedCommit(message=message, sha=sha)

        try:
            # Step 1: Split message into parts
            result.parts = self._split_message(message)

            # Step 2: Parse footers (highest priority)
            self._parse_footers(result)

            # Step 3: Parse conventional commit format
            self._parse_conventional(result)

            # Step 4: Parse bracket notation
            self._parse_bracket(result)

            # Step 5: Parse inline references (if enabled)
            if self.config.parse_inline:
                self._parse_inline(result)

            # Step 6: Deduplicate and prioritize
            self._deduplicate_tasks(result)

        except Exception as e:
            result.parse_errors.append(f"Parse error: {str(e)}")

        return result

    def parse_batch(self, commits: List[Dict[str, str]]) -> List[ParsedCommit]:
        """
        Parse multiple commits in batch.

        Args:
            commits: List of dicts with 'message' and optional 'sha' keys

        Returns:
            List of ParsedCommit objects
        """
        results = []
        for commit in commits:
            message = commit.get("message", "")
            sha = commit.get("sha")
            parsed = self.parse(message, sha)
            results.append(parsed)
        return results

    def validate(self, parsed: ParsedCommit) -> List[str]:
        """
        Validate a parsed commit against configuration rules.

        Args:
            parsed: The ParsedCommit to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check: task reference required?
        if self.config.require_task_reference and not parsed.has_task_reference:
            errors.append("Commit message must reference a task")

        # Check: valid commit type?
        if self.config.validate_type and parsed.type:
            if parsed.type not in self.config.valid_types:
                valid = ", ".join(self.config.valid_types)
                errors.append(
                    f"Unknown commit type '{parsed.type}'. Valid types: {valid}"
                )

        # Check: subject length?
        if parsed.parts:
            subject_len = len(parsed.parts.subject)
            if subject_len > self.config.subject_max_length:
                errors.append(
                    f"Subject exceeds {self.config.subject_max_length} characters "
                    f"({subject_len} chars)"
                )

        # Check: body length?
        if self.config.body_max_length and parsed.parts and parsed.parts.body:
            body_len = len(parsed.parts.body)
            if body_len > self.config.body_max_length:
                errors.append(
                    f"Body exceeds {self.config.body_max_length} characters "
                    f"({body_len} chars)"
                )

        # Check: task ID format?
        task_pattern = re.compile(self.config.task_id_pattern)
        for task in parsed.tasks:
            if not task_pattern.match(task.task_id):
                errors.append(f"Invalid task ID format: '{task.task_id}'")

        return errors

    def suggest_fixes(self, parsed: ParsedCommit) -> List[str]:
        """
        Suggest fixes for validation errors.

        Args:
            parsed: The ParsedCommit with potential issues

        Returns:
            List of human-readable fix suggestions
        """
        suggestions = []

        # Missing task reference?
        if not parsed.has_task_reference:
            if parsed.parts:
                subject = parsed.parts.subject
                suggestions.append(
                    f'Add task reference to commit message:\n'
                    f'  Option 1: Use footer format:\n'
                    f'    {subject}\n'
                    f'    \n'
                    f'    Task: <task-id>\n'
                    f'  Option 2: Use conventional format:\n'
                    f'    <type>(<task-id>): {subject}\n'
                    f'  Option 3: Use bracket format:\n'
                    f'    [<task-id>] {subject}'
                )

        # Invalid type?
        if parsed.type and parsed.type not in self.config.valid_types:
            # Try to suggest similar types
            similar = self._find_similar_type(parsed.type)
            if similar:
                suggestions.append(
                    f"Change '{parsed.type}' to '{similar}'"
                )

        # Subject too long?
        if parsed.parts:
            subject_len = len(parsed.parts.subject)
            if subject_len > self.config.subject_max_length:
                excess = subject_len - self.config.subject_max_length
                suggestions.append(
                    f"Shorten subject by {excess} characters or "
                    f"move details to body"
                )

        # Invalid task ID format?
        for task in parsed.tasks:
            task_pattern = re.compile(self.config.task_id_pattern)
            if not task_pattern.match(task.task_id):
                suggestions.append(
                    f"Use valid task ID format for '{task.task_id}': "
                    f"track-sprint-task-number (e.g., git-integration-1-task-001)"
                )

        return suggestions

    # Internal parsing methods

    def _split_message(self, message: str) -> CommitMessageParts:
        """
        Split commit message into subject, body, and footers.

        Args:
            message: Raw commit message

        Returns:
            CommitMessageParts with structured content
        """
        lines = message.split('\n')

        # Subject is first line
        subject = lines[0] if lines else ""

        # Find where footers start (Git trailer format)
        # Footers are at the end, separated by blank line, Key: value format
        footer_start = len(lines)
        for i in range(len(lines) - 1, 0, -1):
            line = lines[i].strip()
            if not line:
                # Blank line before footers
                footer_start = i + 1
                break
            if not RegexPatterns.FOOTER.match(line):
                # Not a footer, stop searching
                footer_start = i + 1
                break

        # Body is between subject and footers
        body_lines = []
        for i in range(1, footer_start):
            line = lines[i]
            # Skip blank lines at start of body
            if not body_lines and not line.strip():
                continue
            body_lines.append(line)

        body = '\n'.join(body_lines).strip() if body_lines else None

        # Parse footers
        footers = {}
        for i in range(footer_start, len(lines)):
            line = lines[i].strip()
            if match := RegexPatterns.FOOTER.match(line):
                key = match.group('key')
                value = match.group('value').strip()
                footers[key] = value

        return CommitMessageParts(
            subject=subject,
            body=body,
            footers=footers
        )

    def _parse_footers(self, result: ParsedCommit) -> None:
        """
        Parse footer references (highest priority).

        Args:
            result: ParsedCommit to update
        """
        if not result.parts or not result.parts.footers:
            return

        footers = result.parts.footers

        # Parse task references
        for key, value in footers.items():
            key_lower = key.lower()

            # Task: task-id or Tasks: task-1, task-2
            if key_lower in ['task', 'tasks']:
                task_ids = self._parse_task_list(value)
                for task_id in task_ids:
                    result.tasks.append(TaskReference(
                        task_id=task_id,
                        format=CommitFormat.FOOTER,
                        confidence=1.0,
                        match_text=f"{key}: {value}"
                    ))
                result.format_detected.append(CommitFormat.FOOTER)

            # Status keywords (Closes, Fixes, Resolves, etc.)
            elif key_lower in STATUS_KEYWORDS:
                task_ids = self._parse_task_list(value)
                status = STATUS_KEYWORDS[key_lower]
                for task_id in task_ids:
                    result.tasks.append(TaskReference(
                        task_id=task_id,
                        format=CommitFormat.FOOTER,
                        status=status,
                        confidence=1.0,
                        match_text=f"{key}: {value}"
                    ))
                result.format_detected.append(CommitFormat.FOOTER)

            # Explicit status
            elif key_lower == 'status':
                try:
                    status = TaskStatus(value.lower())
                    # Apply status to most recent task (or all tasks)
                    if result.tasks:
                        result.tasks[-1].status = status
                except ValueError:
                    result.parse_warnings.append(
                        f"Unknown status value: '{value}'"
                    )

            # Sprint reference
            elif key_lower == 'sprint':
                result.sprint = SprintReference(sprint_id=value)

            # Track reference
            elif key_lower == 'track':
                result.track = TrackReference(track_id=value)

    def _parse_conventional(self, result: ParsedCommit) -> None:
        """
        Parse conventional commit format.

        Args:
            result: ParsedCommit to update
        """
        if not result.parts:
            return

        subject = result.parts.subject
        if match := RegexPatterns.CONVENTIONAL.match(subject):
            result.type = match.group('type')
            result.scope = match.group('scope')
            result.breaking = match.group('breaking') == '!'
            result.description = match.group('description').strip()

            # Check if scope is a task ID
            if result.scope and self._is_task_id(result.scope):
                result.tasks.append(TaskReference(
                    task_id=result.scope,
                    format=CommitFormat.CONVENTIONAL,
                    confidence=1.0,
                    match_text=f"({result.scope})"
                ))
                result.format_detected.append(CommitFormat.CONVENTIONAL)

    def _parse_bracket(self, result: ParsedCommit) -> None:
        """
        Parse bracket notation format.

        Args:
            result: ParsedCommit to update
        """
        if not result.parts:
            return

        subject = result.parts.subject
        if match := RegexPatterns.BRACKET.match(subject):
            task_id = match.group('task_id')
            if self._is_task_id(task_id):
                result.tasks.append(TaskReference(
                    task_id=task_id,
                    format=CommitFormat.BRACKET,
                    confidence=1.0,
                    match_text=f"[{task_id}]"
                ))
                result.format_detected.append(CommitFormat.BRACKET)

    def _parse_inline(self, result: ParsedCommit) -> None:
        """
        Parse inline task references (lowest priority).

        Args:
            result: ParsedCommit to update
        """
        if not result.message:
            return

        # Search entire message for task IDs
        for match in RegexPatterns.INLINE.finditer(result.message):
            task_id = match.group('task_id')

            # Normalize case if not case-sensitive
            if not self.config.case_sensitive:
                task_id = task_id.lower()

            if self._is_task_id(task_id):
                result.tasks.append(TaskReference(
                    task_id=task_id,
                    format=CommitFormat.INLINE,
                    confidence=0.7,  # Lower confidence for inline matches
                    match_text=match.group(0)
                ))

        if any(t.format == CommitFormat.INLINE for t in result.tasks):
            result.format_detected.append(CommitFormat.INLINE)

    def _deduplicate_tasks(self, result: ParsedCommit) -> None:
        """
        Remove duplicate task references, keeping highest priority.

        Priority order:
        1. Footer references (explicit)
        2. Conventional format (structured)
        3. Bracket notation (clear)
        4. Inline references (lowest confidence)

        Args:
            result: ParsedCommit to deduplicate
        """
        if not result.tasks:
            return

        # Group tasks by ID
        tasks_by_id: Dict[str, List[TaskReference]] = {}
        for task in result.tasks:
            task_id = task.task_id
            if task_id not in tasks_by_id:
                tasks_by_id[task_id] = []
            tasks_by_id[task_id].append(task)

        # For each task ID, keep only the highest priority reference
        deduplicated = []
        format_priority = {
            CommitFormat.FOOTER: 1,
            CommitFormat.CONVENTIONAL: 2,
            CommitFormat.BRACKET: 3,
            CommitFormat.INLINE: 4,
        }

        for task_id, refs in tasks_by_id.items():
            # Sort by priority (lowest number = highest priority)
            refs.sort(key=lambda r: (format_priority[r.format], -r.confidence))
            best_ref = refs[0]

            # Merge status information from all refs
            for ref in refs:
                if ref.status and not best_ref.status:
                    best_ref.status = ref.status

            deduplicated.append(best_ref)

        result.tasks = deduplicated

    def _parse_task_list(self, value: str) -> List[str]:
        """
        Parse comma-separated list of task IDs.

        Args:
            value: String like "task-1, task-2, task-3"

        Returns:
            List of task IDs
        """
        # Split on commas, strip whitespace
        parts = [p.strip() for p in value.split(',')]

        # Filter to valid task IDs
        task_ids = []
        for part in parts:
            if self._is_task_id(part):
                task_ids.append(part)

        return task_ids

    def _is_task_id(self, value: str) -> bool:
        """
        Check if a string looks like a task ID.

        Args:
            value: String to check

        Returns:
            True if matches task ID pattern
        """
        # Try full format first
        if RegexPatterns.TASK_ID_FULL.match(value):
            return True

        # Try short format
        if RegexPatterns.TASK_ID_SHORT.match(value):
            return True

        # Try custom pattern from config
        try:
            pattern = re.compile(self.config.task_id_pattern)
            if pattern.match(value):
                return True
        except re.error:
            pass

        return False

    def _find_similar_type(self, invalid_type: str) -> Optional[str]:
        """
        Find similar valid commit type using simple string matching.

        Args:
            invalid_type: The invalid type string

        Returns:
            Most similar valid type, or None
        """
        invalid_lower = invalid_type.lower()

        # Exact match (case-insensitive)
        for valid in self.config.valid_types:
            if valid.lower() == invalid_lower:
                return valid

        # Prefix match
        for valid in self.config.valid_types:
            if valid.lower().startswith(invalid_lower[:3]):
                return valid

        # Common mistakes
        mappings = {
            'feature': 'feat',
            'bugfix': 'fix',
            'documentation': 'docs',
            'testing': 'test',
        }

        if invalid_lower in mappings:
            return mappings[invalid_lower]

        return None


def analyze_batch(
    commits: List[Dict[str, str]],
    config: Optional[ParserConfig] = None
) -> ParseResult:
    """
    Analyze a batch of commits and generate summary statistics.

    Args:
        commits: List of dicts with 'message' and optional 'sha'
        config: Parser configuration

    Returns:
        ParseResult with summary statistics
    """
    parser = CommitParser(config)
    parsed_commits = parser.parse_batch(commits)

    # Collect statistics
    total = len(parsed_commits)
    errors = sum(1 for p in parsed_commits if p.parse_errors)
    successful = total - errors

    with_tasks = sum(1 for p in parsed_commits if p.has_task_reference)
    without_tasks = total - with_tasks

    # Collect unique IDs
    unique_tasks: Set[str] = set()
    unique_sprints: Set[str] = set()
    unique_tracks: Set[str] = set()

    for parsed in parsed_commits:
        for task in parsed.tasks:
            unique_tasks.add(task.task_id)
        if parsed.sprint:
            unique_sprints.add(parsed.sprint.sprint_id)
        if parsed.track:
            unique_tracks.add(parsed.track.track_id)

    # Count format usage
    format_usage: Dict[str, int] = {}
    for parsed in parsed_commits:
        for fmt in parsed.format_detected:
            format_name = fmt.value
            format_usage[format_name] = format_usage.get(format_name, 0) + 1

    return ParseResult(
        total_commits=total,
        parsed_successfully=successful,
        parse_errors=errors,
        commits_with_tasks=with_tasks,
        commits_without_tasks=without_tasks,
        unique_tasks=sorted(unique_tasks),
        unique_sprints=sorted(unique_sprints),
        unique_tracks=sorted(unique_tracks),
        format_usage=format_usage,
    )
