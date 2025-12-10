# Commit Message Parsing Schema Design

**Task:** git-integration-1-task-001
**Sprint:** git-integration-1 (Git History & Commit Analysis)
**Status:** Completed
**Date:** 2025-11-24

---

## Executive Summary

This document defines the data structures, interfaces, and algorithms for parsing Git commit messages to extract Vibey roadmap references. The schema is implemented in `vibey/operations/git/commit_parser_schema.py`.

**Key Design Goals:**
- **Type-Safe**: Python dataclasses with full type hints
- **Extensible**: Support multiple commit formats simultaneously
- **Configurable**: All parsing behavior controlled by ParserConfig
- **Validated**: Built-in validation and error reporting
- **Performant**: Batch processing support, compiled regex patterns

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                    Commit Parser Architecture                 │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Input: Raw commit message(s)                                │
│         ↓                                                     │
│  ┌─────────────────┐                                         │
│  │ Parser          │                                         │
│  │ (implements     │→ Uses → ParserConfig                   │
│  │  Interface)     │                                         │
│  └────────┬────────┘                                         │
│           ↓                                                   │
│  ┌─────────────────┐                                         │
│  │ Split message   │                                         │
│  │ into parts      │→ Output → CommitMessageParts           │
│  └────────┬────────┘                                         │
│           ↓                                                   │
│  ┌─────────────────┐                                         │
│  │ Apply regex     │                                         │
│  │ patterns        │→ Uses → RegexPatterns                  │
│  └────────┬────────┘                                         │
│           ↓                                                   │
│  ┌─────────────────┐                                         │
│  │ Extract refs    │→ Creates → TaskReference               │
│  │                 │           SprintReference              │
│  │                 │           TrackReference               │
│  └────────┬────────┘                                         │
│           ↓                                                   │
│  ┌─────────────────┐                                         │
│  │ Validate &      │                                         │
│  │ prioritize      │→ Output → ParsedCommit                 │
│  └─────────────────┘                                         │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## Data Structures

### 1. Core Enums

#### CommitFormat
Identifies which commit message format was detected:

```python
class CommitFormat(Enum):
    CONVENTIONAL = "conventional"  # feat(task-id): description
    FOOTER = "footer"              # Task: task-id in footer
    BRACKET = "bracket"            # [task-id] description
    INLINE = "inline"              # task-id anywhere in message
```

#### TaskStatus
Status that can be indicated in commit messages:

```python
class TaskStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    REVERTED = "reverted"
```

### 2. Reference Objects

#### TaskReference
Represents a single task reference found in a commit:

```python
@dataclass
class TaskReference:
    task_id: str                    # e.g., "git-integration-1-task-001"
    format: CommitFormat            # How it was detected
    status: Optional[TaskStatus]    # Indicated status change
    confidence: float = 1.0         # 0.0-1.0 (lower for inline matches)
    line_number: Optional[int]      # Location in message
    match_text: str                 # The actual matched text
```

**Key Features:**
- **Confidence scoring**: Inline matches get lower confidence (0.6-0.8)
- **Location tracking**: Know where in the message the reference was found
- **Status indication**: Detect "Closes: task-id" → status = completed

**Usage Example:**
```python
ref = TaskReference(
    task_id="git-integration-1-task-001",
    format=CommitFormat.FOOTER,
    status=TaskStatus.COMPLETED,
    confidence=1.0,
    line_number=5,
    match_text="Task: git-integration-1-task-001"
)
```

#### SprintReference & TrackReference
Similar structure for sprint and track references:

```python
@dataclass
class SprintReference:
    sprint_id: str
    status: Optional[TaskStatus]

@dataclass
class TrackReference:
    track_id: str
    status: Optional[TaskStatus]
```

### 3. Message Structure

#### CommitMessageParts
Structured breakdown of commit message:

```python
@dataclass
class CommitMessageParts:
    subject: str                     # First line
    body: Optional[str]              # Middle paragraphs
    footers: Dict[str, str]          # Key: value pairs at end
```

**Parsing Rules:**
- **Subject**: First line up to first blank line
- **Body**: Content between subject and footers
- **Footers**: Lines matching `Key: value` pattern at end

**Example:**
```python
parts = CommitMessageParts(
    subject="feat(task-001): implement content loader",
    body="Added ContentLoader class with YAML support",
    footers={
        "Task": "python-package-3-task-001",
        "Status": "completed"
    }
)
```

### 4. Parsed Result

#### ParsedCommit
Complete result of parsing a commit message:

```python
@dataclass
class ParsedCommit:
    # Original
    message: str
    sha: Optional[str]

    # Structured parts
    parts: Optional[CommitMessageParts]

    # Conventional commit fields
    type: Optional[str]           # feat, fix, docs, etc.
    scope: Optional[str]          # From (scope)
    breaking: bool                # ! indicator
    description: Optional[str]    # After :

    # Vibey references
    tasks: List[TaskReference]
    sprint: Optional[SprintReference]
    track: Optional[TrackReference]

    # Metadata
    format_detected: List[CommitFormat]
    parse_errors: List[str]
    parse_warnings: List[str]
```

**Properties:**
- `has_task_reference` → bool: Quick check if any tasks referenced
- `primary_task` → TaskReference: Get highest-confidence task

**Usage Example:**
```python
parsed = ParsedCommit(
    message="feat(task-001): implement feature",
    sha="abc123",
    type="feat",
    scope="task-001",
    description="implement feature",
    tasks=[TaskReference(task_id="task-001", ...)],
    format_detected=[CommitFormat.CONVENTIONAL]
)

if parsed.has_task_reference:
    primary = parsed.primary_task
    print(f"Primary task: {primary.task_id}")
```

### 5. Configuration

#### ParserConfig
Controls all parsing behavior:

```python
@dataclass
class ParserConfig:
    # Format preferences (priority order)
    preferred_formats: List[CommitFormat]

    # Parsing options
    parse_inline: bool = False          # Parse inline refs?
    case_sensitive: bool = False        # Task ID case?

    # Validation
    require_task_reference: bool = False
    validate_task_exists: bool = True   # Check roadmap?
    validate_type: bool = True          # Valid commit type?

    # Valid types
    valid_types: List[str] = [
        "feat", "fix", "docs", "style", "refactor",
        "test", "chore", "perf", "ci", "build", "revert"
    ]

    # Patterns
    task_id_pattern: str = r"^[\w-]+-\d+-task-\d+$"

    # Limits
    subject_max_length: int = 72
    body_max_length: Optional[int] = None
```

**Default Configuration:**
```python
config = ParserConfig(
    preferred_formats=[
        CommitFormat.FOOTER,         # Priority 1: Most explicit
        CommitFormat.CONVENTIONAL,   # Priority 2: Standard
        CommitFormat.BRACKET,        # Priority 3: Common
    ],
    parse_inline=False,              # Disabled by default (false positives)
    require_task_reference=False,    # Optional by default
)
```

---

## Regex Patterns

### Pattern Definitions

All regex patterns are pre-compiled in `RegexPatterns` class:

```python
class RegexPatterns:
    # Conventional: feat(task-id): description
    CONVENTIONAL = re.compile(
        r'^(?P<type>\w+)'
        r'(?:\((?P<scope>[\w-]+)\))?'
        r'(?P<breaking>!)?'
        r':\s*'
        r'(?P<description>.+)$'
    )

    # Footer: Task: task-id
    FOOTER = re.compile(
        r'^(?P<key>[\w-]+):\s*(?P<value>.+)$',
        re.MULTILINE
    )

    # Bracket: [task-id] description
    BRACKET = re.compile(
        r'^\[(?P<task_id>[\w-]+)\]\s*(?P<description>.+)$'
    )

    # Full task ID: track-sprint-task-number
    TASK_ID_FULL = re.compile(
        r'(?P<track>[\w-]+)-(?P<sprint>\d+)-task-(?P<number>\d+)'
    )

    # Short task ID: task-number
    TASK_ID_SHORT = re.compile(
        r'task-(?P<number>\d+)'
    )

    # Inline reference: task: task-id or just task-id
    INLINE = re.compile(
        r'\b(?:task:\s*)?(?P<task_id>[\w]+-\d+-task-\d+)\b',
        re.IGNORECASE
    )

    # Sprint: Sprint: sprint-id
    SPRINT = re.compile(
        r'sprint:\s*(?P<sprint_id>[\w-]+-\d+)',
        re.IGNORECASE
    )

    # Track: Track: track-id
    TRACK = re.compile(
        r'track:\s*(?P<track_id>[\w-]+)',
        re.IGNORECASE
    )
```

### Pattern Priority

When multiple formats detected, priority order:
1. **Footer references** (most explicit, highest confidence)
2. **Conventional commit scope** (standard, high confidence)
3. **Bracket notation** (clear, medium-high confidence)
4. **Inline references** (lowest confidence, only if enabled)

---

## Parsing Algorithm

### High-Level Flow

```python
def parse(message: str, sha: Optional[str] = None) -> ParsedCommit:
    """
    Parse commit message following this algorithm:

    1. Split message into parts (subject, body, footers)
    2. Check footers first (most reliable)
       - Extract task references
       - Extract status indicators
       - Extract sprint/track references
    3. Check conventional commit scope
       - Extract type, scope, breaking, description
       - Check if scope is a task ID
    4. Check bracket notation in subject
       - Extract task ID from [task-id]
    5. If enabled, check inline references
       - Scan entire message for task IDs
       - Assign lower confidence
    6. Validate and deduplicate results
    7. Return ParsedCommit object
    """
```

### Step-by-Step Example

**Input:**
```
feat(git-integration-1-task-001): implement commit parser

Added CommitParser class with support for:
- Conventional commits
- Footer references
- Bracket notation

Task: git-integration-1-task-001
Status: completed
Sprint: git-integration-1
```

**Step 1: Split message**
```python
parts = CommitMessageParts(
    subject="feat(git-integration-1-task-001): implement commit parser",
    body="Added CommitParser class with support for:\n...",
    footers={
        "Task": "git-integration-1-task-001",
        "Status": "completed",
        "Sprint": "git-integration-1"
    }
)
```

**Step 2: Parse footers**
```python
tasks.append(TaskReference(
    task_id="git-integration-1-task-001",
    format=CommitFormat.FOOTER,
    status=TaskStatus.COMPLETED,
    confidence=1.0
))

sprint = SprintReference(
    sprint_id="git-integration-1"
)
```

**Step 3: Parse conventional format**
```python
type = "feat"
scope = "git-integration-1-task-001"
description = "implement commit parser"

# Check if scope is task ID
if is_task_id(scope):
    tasks.append(TaskReference(
        task_id=scope,
        format=CommitFormat.CONVENTIONAL,
        confidence=1.0
    ))
```

**Step 4: Deduplicate**
```python
# Same task ID from footer and conventional format
# Keep footer (higher priority), discard conventional
```

**Step 5: Build result**
```python
result = ParsedCommit(
    message=original_message,
    sha=sha,
    parts=parts,
    type="feat",
    scope="git-integration-1-task-001",
    description="implement commit parser",
    tasks=[
        TaskReference(
            task_id="git-integration-1-task-001",
            format=CommitFormat.FOOTER,
            status=TaskStatus.COMPLETED,
            confidence=1.0
        )
    ],
    sprint=SprintReference(sprint_id="git-integration-1"),
    format_detected=[CommitFormat.FOOTER, CommitFormat.CONVENTIONAL]
)
```

---

## Status Keyword Mapping

Keywords that indicate status changes:

```python
STATUS_KEYWORDS = {
    # Completion indicators
    'closes': TaskStatus.COMPLETED,
    'completes': TaskStatus.COMPLETED,
    'finishes': TaskStatus.COMPLETED,
    'fixes': TaskStatus.COMPLETED,
    'resolves': TaskStatus.COMPLETED,

    # Progress indicators
    'addresses': TaskStatus.IN_PROGRESS,
    'starts': TaskStatus.IN_PROGRESS,
    'wip': TaskStatus.IN_PROGRESS,

    # Blocker indicators
    'blocks': TaskStatus.BLOCKED,
    'blocked': TaskStatus.BLOCKED,

    # Revert indicators
    'reverts': TaskStatus.REVERTED,
}
```

**Usage in Footers:**
```
Closes: task-001          → status = completed
Starts: task-002          → status = in_progress
Blocked: task-003         → status = blocked
Status: completed         → status = completed (explicit)
```

---

## Interface Definition

### CommitParserInterface

Abstract interface that all parser implementations must follow:

```python
class CommitParserInterface:
    def parse(self, message: str, sha: Optional[str] = None) -> ParsedCommit:
        """Parse single commit message."""
        raise NotImplementedError

    def parse_batch(self, commits: List[Dict[str, str]]) -> List[ParsedCommit]:
        """Parse multiple commits efficiently."""
        raise NotImplementedError

    def validate(self, parsed: ParsedCommit) -> List[str]:
        """Validate parsed commit against rules."""
        raise NotImplementedError

    def suggest_fixes(self, parsed: ParsedCommit) -> List[str]:
        """Suggest fixes for validation errors."""
        raise NotImplementedError
```

**Batch Processing:**
```python
commits = [
    {"message": "feat: add feature", "sha": "abc123"},
    {"message": "fix: resolve bug", "sha": "def456"},
]

results = parser.parse_batch(commits)
for result in results:
    if result.has_task_reference:
        print(f"Commit {result.sha} references {len(result.tasks)} tasks")
```

**Validation:**
```python
parsed = parser.parse("feat: add feature")
errors = parser.validate(parsed)

if errors:
    print("Validation failed:")
    for error in errors:
        print(f"  - {error}")

    suggestions = parser.suggest_fixes(parsed)
    print("Suggestions:")
    for suggestion in suggestions:
        print(f"  - {suggestion}")
```

---

## Validation Rules

### Built-in Validations

1. **Task Reference Requirement**
   - If `require_task_reference=True`, commits MUST reference at least one task
   - Error: "Commit message must reference a task"

2. **Task Existence Check**
   - If `validate_task_exists=True`, verify task IDs exist in roadmap
   - Error: "Task 'task-999' not found in roadmap"

3. **Commit Type Validation**
   - If `validate_type=True`, type must be in `valid_types` list
   - Error: "Unknown commit type 'feature'. Valid types: feat, fix, ..."

4. **Subject Length**
   - Subject must not exceed `subject_max_length`
   - Warning: "Subject exceeds 72 characters (85 chars)"

5. **Body Length**
   - If `body_max_length` set, body must not exceed limit
   - Warning: "Body exceeds maximum length"

6. **Task ID Format**
   - Task IDs must match `task_id_pattern`
   - Error: "Invalid task ID format: 'bad-id'"

### Example Validation Output

```python
parsed = parser.parse("feature(bad-id): add stuff that is way too long...")

errors = [
    "Unknown commit type 'feature'. Valid types: feat, fix, docs, ...",
    "Invalid task ID format: 'bad-id'",
    "Subject exceeds 72 characters (85 chars)"
]

suggestions = [
    "Change 'feature' to 'feat'",
    "Use valid task ID format: track-sprint-task-number",
    "Shorten subject to 72 characters or move details to body"
]
```

---

## Batch Processing & Reporting

### ParseResult
High-level summary for batch operations:

```python
@dataclass
class ParseResult:
    total_commits: int
    parsed_successfully: int
    parse_errors: int

    commits_with_tasks: int
    commits_without_tasks: int

    unique_tasks: List[str]
    unique_sprints: List[str]
    unique_tracks: List[str]

    format_usage: Dict[str, int]  # Format → count
```

**Usage Example:**
```python
result = parse_git_log()

print(f"Parsed {result.total_commits} commits")
print(f"Found {len(result.unique_tasks)} unique tasks")
print(f"Format usage:")
for format_name, count in result.format_usage.items():
    pct = (count / result.total_commits) * 100
    print(f"  {format_name}: {count} ({pct:.1f}%)")
```

---

## Configuration Examples

### Strict Mode (All Validation)

```yaml
# .vibey/config/git.yaml
git:
  commit:
    preferred_formats:
      - footer
      - conventional

    parse_inline: false
    case_sensitive: false

    require_task_reference: true      # Enforce task refs
    validate_task_exists: true        # Check roadmap
    validate_type: true               # Check commit type

    valid_types:
      - feat
      - fix
      - docs

    subject_max_length: 72
```

### Lenient Mode (Warnings Only)

```yaml
git:
  commit:
    preferred_formats:
      - conventional
      - footer
      - bracket
      - inline                        # Allow inline

    parse_inline: true

    require_task_reference: false     # Optional
    validate_task_exists: false       # Don't check
    validate_type: false              # Don't check

    subject_max_length: 100           # Relaxed
```

### Custom Format (Inline Only)

```yaml
git:
  commit:
    preferred_formats:
      - inline

    parse_inline: true
    case_sensitive: true

    # Custom task ID pattern (e.g., JIRA-style)
    task_id_pattern: "^[A-Z]+-\\d+$"
```

---

## Implementation Checklist

Task 001 deliverables:

- [x] Define all data structures (dataclasses)
- [x] Define all enums (CommitFormat, TaskStatus)
- [x] Define reference objects (TaskReference, SprintReference, TrackReference)
- [x] Define message structure (CommitMessageParts)
- [x] Define parsed result (ParsedCommit)
- [x] Define configuration (ParserConfig)
- [x] Define regex patterns (RegexPatterns)
- [x] Define status keywords mapping
- [x] Define parser interface (CommitParserInterface)
- [x] Define batch result structure (ParseResult)
- [x] Add type hints throughout
- [x] Add to_dict() methods for serialization
- [x] Add helper properties (has_task_reference, primary_task)
- [x] Document all structures
- [x] Provide usage examples

**Next Tasks:**
- Task 002: Implement CommitParser class using this schema
- Task 003: Create git log analysis utilities using parsed commits
- Task 004: Build velocity calculator from parsed commits

---

## Design Decisions

| Decision | Options Considered | Choice | Rationale |
|----------|-------------------|--------|-----------|
| Data structure | dict, dataclass, pydantic | dataclass | Balance of simplicity, type safety, and performance |
| Confidence scoring | Binary, 0-100, 0.0-1.0 | 0.0-1.0 float | Standard ML practice, easy to compare |
| Multi-format support | Single best match, All matches | All matches | Enables format usage analytics |
| Batch interface | Single-only, Batch-capable | Both | Performance optimization for git log analysis |
| Validation approach | Inline, Separate method | Separate validate() | Flexible: can parse without validating |
| Configuration | Hardcoded, Config object, YAML | Config object + YAML | Type-safe config, easy to override |

---

## References

- **Sprint 0 Architecture:** 003-commit-conventions.md
- **Implementation File:** vibey/operations/git/commit_parser_schema.py
- **Related Tasks:**
  - Task 002: Commit parser implementation
  - Task 008: State reconstruction (uses parsed commits)
  - Task 009: Tag parsing (extends this schema)
