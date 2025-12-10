# Commit Parser Implementation Guide

**Task:** git-integration-1-task-002
**Sprint:** git-integration-1 (Git History & Commit Analysis)
**Status:** Completed
**Date:** 2025-11-24

---

## Overview

This document describes the `CommitParser` implementation, which parses Git commit messages to extract Vibey roadmap references (tasks, sprints, tracks).

**Implementation File:** `vibey/operations/git/commit_parser.py`
**Schema Definition:** `vibey/operations/git/commit_parser_schema.py`

---

## Quick Start

### Basic Usage

```python
from vibey.operations.git import CommitParser

# Create parser with default config
parser = CommitParser()

# Parse a single commit
message = """feat(git-integration-1-task-002): implement commit parser

Added CommitParser class with full format support.

Task: git-integration-1-task-002
Status: completed
"""

parsed = parser.parse(message, sha="abc123")

# Access results
print(f"Type: {parsed.type}")           # "feat"
print(f"Tasks: {len(parsed.tasks)}")    # 1
print(f"Task ID: {parsed.tasks[0].task_id}")  # "git-integration-1-task-002"
print(f"Status: {parsed.tasks[0].status}")    # TaskStatus.COMPLETED
```

### Batch Processing

```python
from vibey.operations.git import analyze_batch

# Parse multiple commits
commits = [
    {"message": "feat(task-001): add feature", "sha": "abc123"},
    {"message": "fix(task-002): resolve bug", "sha": "def456"},
    {"message": "docs: update README", "sha": "ghi789"},
]

result = analyze_batch(commits)

print(f"Total commits: {result.total_commits}")
print(f"With tasks: {result.commits_with_tasks}")
print(f"Without tasks: {result.commits_without_tasks}")
print(f"Unique tasks: {result.unique_tasks}")
print(f"Format usage: {result.format_usage}")
```

---

## Features

### 1. Multi-Format Support

The parser supports four commit message formats:

#### Format 1: Conventional Commits (Priority 2)

```python
message = "feat(git-integration-1-task-001): implement feature"
parsed = parser.parse(message)

# Extracts:
# - type: "feat"
# - scope: "git-integration-1-task-001"
# - task: "git-integration-1-task-001"
# - format: CommitFormat.CONVENTIONAL
```

#### Format 2: Footer References (Priority 1 - Highest)

```python
message = """feat: implement feature

Detailed description of changes.

Task: git-integration-1-task-001
Status: completed
"""
parsed = parser.parse(message)

# Extracts:
# - task: "git-integration-1-task-001"
# - status: TaskStatus.COMPLETED
# - format: CommitFormat.FOOTER
```

#### Format 3: Bracket Notation (Priority 3)

```python
message = "[git-integration-1-task-001] implement feature"
parsed = parser.parse(message)

# Extracts:
# - task: "git-integration-1-task-001"
# - format: CommitFormat.BRACKET
```

#### Format 4: Inline References (Priority 4 - Lowest, Optional)

```python
from vibey.operations.git import ParserConfig, CommitFormat

config = ParserConfig(parse_inline=True)
parser = CommitParser(config)

message = "Implement feature for git-integration-1-task-001"
parsed = parser.parse(message)

# Extracts:
# - task: "git-integration-1-task-001"
# - format: CommitFormat.INLINE
# - confidence: 0.7 (lower confidence)
```

### 2. Status Detection

Automatically detects task status changes from footer keywords:

```python
# Completion keywords
message = """fix: resolve bug

Closes: git-integration-1-task-003
"""
parsed = parser.parse(message)
# task.status = TaskStatus.COMPLETED

# Progress keywords
message = """feat: start implementation

Starts: git-integration-1-task-004
"""
parsed = parser.parse(message)
# task.status = TaskStatus.IN_PROGRESS

# Blocker keywords
message = """chore: mark as blocked

Blocked: git-integration-1-task-005
"""
parsed = parser.parse(message)
# task.status = TaskStatus.BLOCKED
```

**Supported Keywords:**
- **Completion:** closes, completes, finishes, fixes, resolves
- **Progress:** addresses, starts, wip
- **Blocker:** blocks, blocked
- **Revert:** reverts

### 3. Multi-Task Commits

A single commit can reference multiple tasks:

```python
message = """refactor: consolidate utilities

Tasks: task-001, task-002, task-003
Status: completed
"""
parsed = parser.parse(message)

print(len(parsed.tasks))  # 3
for task in parsed.tasks:
    print(f"{task.task_id}: {task.status}")
# task-001: completed
# task-002: completed
# task-003: completed
```

### 4. Sprint and Track References

```python
message = """chore: complete sprint

Sprint: git-integration-1
Status: completed

Quality Gates:
- Unit Test Coverage: 95% ✓
- Documentation: 100% ✓
"""
parsed = parser.parse(message)

print(parsed.sprint.sprint_id)  # "git-integration-1"
```

### 5. Deduplication

When a task is referenced in multiple formats, the parser keeps the highest priority reference:

```python
message = """feat(task-001): implement feature

Added new feature with comprehensive tests.

Task: task-001
Status: completed
"""
parsed = parser.parse(message)

# Task referenced in both conventional (priority 2) and footer (priority 1)
# Parser keeps footer reference (highest priority)
print(len(parsed.tasks))  # 1 (deduplicated)
print(parsed.tasks[0].format)  # CommitFormat.FOOTER
print(parsed.tasks[0].status)  # TaskStatus.COMPLETED (from footer)
```

---

## Configuration

### Default Configuration

```python
from vibey.operations.git import ParserConfig, CommitFormat

config = ParserConfig(
    # Format priority (highest to lowest)
    preferred_formats=[
        CommitFormat.FOOTER,
        CommitFormat.CONVENTIONAL,
        CommitFormat.BRACKET,
    ],

    # Parsing options
    parse_inline=False,         # Don't parse inline (false positives)
    case_sensitive=False,       # Task IDs are case-insensitive

    # Validation options
    require_task_reference=False,   # Tasks optional by default
    validate_task_exists=True,      # Check if tasks exist in roadmap
    validate_type=True,             # Validate commit type

    # Valid types
    valid_types=[
        "feat", "fix", "docs", "style", "refactor",
        "test", "chore", "perf", "ci", "build", "revert"
    ],

    # Task ID pattern
    task_id_pattern=r"^[\w-]+-\d+-task-\d+$",

    # Length limits
    subject_max_length=72,
    body_max_length=None,  # No limit
)
```

### Strict Mode

```python
config = ParserConfig(
    require_task_reference=True,    # Enforce task refs
    validate_task_exists=True,      # Check roadmap
    validate_type=True,             # Check type
    subject_max_length=72,          # Enforce limit
)

parser = CommitParser(config)

# This will fail validation
message = "add feature"  # No task reference
parsed = parser.parse(message)
errors = parser.validate(parsed)
# ["Commit message must reference a task"]
```

### Lenient Mode

```python
config = ParserConfig(
    parse_inline=True,              # Allow inline refs
    require_task_reference=False,   # Tasks optional
    validate_task_exists=False,     # Don't check roadmap
    validate_type=False,            # Don't check type
    subject_max_length=100,         # Relaxed limit
)

parser = CommitParser(config)
```

---

## Validation

### Validation Rules

```python
parsed = parser.parse(message)
errors = parser.validate(parsed)

if errors:
    print("Validation errors:")
    for error in errors:
        print(f"  - {error}")

    suggestions = parser.suggest_fixes(parsed)
    print("\nSuggestions:")
    for suggestion in suggestions:
        print(f"  - {suggestion}")
```

**Built-in Validations:**
1. Task reference requirement
2. Task existence in roadmap
3. Commit type validity
4. Subject length limit
5. Body length limit
6. Task ID format

### Example Validation Output

```python
message = "feature: add something really long that exceeds the limit..."
parsed = parser.parse(message)
errors = parser.validate(parsed)

# Output:
# [
#   "Unknown commit type 'feature'. Valid types: feat, fix, docs, ...",
#   "Subject exceeds 72 characters (85 chars)",
#   "Commit message must reference a task"
# ]

suggestions = parser.suggest_fixes(parsed)

# Output:
# [
#   "Change 'feature' to 'feat'",
#   "Shorten subject by 13 characters or move details to body",
#   "Add task reference to commit message:\n  Option 1: Use footer format: ..."
# ]
```

---

## Advanced Usage

### Custom Task ID Pattern

Support custom task ID formats (e.g., JIRA-style):

```python
config = ParserConfig(
    task_id_pattern=r"^[A-Z]+-\d+$",  # Match JIRA-123
    parse_inline=True,
)

parser = CommitParser(config)

message = "feat: implement JIRA-123 feature"
parsed = parser.parse(message)

print(parsed.tasks[0].task_id)  # "JIRA-123"
```

### Confidence Scoring

Inline references get lower confidence scores:

```python
config = ParserConfig(parse_inline=True)
parser = CommitParser(config)

message = """feat(task-001): implement feature

This also addresses task-002 inline.

Task: task-003
"""
parsed = parser.parse(message)

for task in parsed.tasks:
    print(f"{task.task_id}: confidence={task.confidence}, format={task.format}")

# Output:
# task-001: confidence=1.0, format=CommitFormat.CONVENTIONAL
# task-002: confidence=0.7, format=CommitFormat.INLINE
# task-003: confidence=1.0, format=CommitFormat.FOOTER
```

### Primary Task Detection

Get the most important task reference:

```python
parsed = parser.parse(message)

if parsed.has_task_reference:
    primary = parsed.primary_task  # Highest confidence task
    print(f"Primary task: {primary.task_id}")
```

---

## Integration Examples

### Git Log Analysis

```python
import subprocess
from vibey.operations.git import CommitParser

def analyze_git_log(repo_path: str, ref_range: str = "HEAD~10..HEAD"):
    """Analyze recent commits in a git repository."""
    parser = CommitParser()

    # Get git log
    result = subprocess.run(
        ["git", "log", "--format=%H|%s%n%b", ref_range],
        cwd=repo_path,
        capture_output=True,
        text=True
    )

    # Parse commits
    commits = []
    current = {}
    for line in result.stdout.split('\n'):
        if '|' in line:
            # New commit
            if current:
                commits.append(current)
            sha, message = line.split('|', 1)
            current = {"sha": sha, "message": message + '\n'}
        else:
            # Continue message
            if current:
                current["message"] += line + '\n'

    if current:
        commits.append(current)

    # Parse all commits
    parsed_commits = parser.parse_batch(commits)

    # Report
    tasks_by_id = {}
    for parsed in parsed_commits:
        for task in parsed.tasks:
            if task.task_id not in tasks_by_id:
                tasks_by_id[task.task_id] = []
            tasks_by_id[task.task_id].append(parsed.sha)

    print(f"Analyzed {len(parsed_commits)} commits")
    print(f"Found {len(tasks_by_id)} unique tasks:")
    for task_id, shas in tasks_by_id.items():
        print(f"  {task_id}: {len(shas)} commits")

    return parsed_commits, tasks_by_id
```

### Pre-Commit Hook

```python
#!/usr/bin/env python3
"""Pre-commit hook to validate commit messages."""

import sys
from vibey.operations.git import CommitParser, ParserConfig

def main():
    # Read commit message
    with open(sys.argv[1], 'r') as f:
        message = f.read()

    # Configure parser (strict mode)
    config = ParserConfig(
        require_task_reference=True,
        validate_type=True,
        subject_max_length=72,
    )
    parser = CommitParser(config)

    # Parse and validate
    parsed = parser.parse(message)
    errors = parser.validate(parsed)

    if errors:
        print("ERROR: Commit message validation failed:")
        for error in errors:
            print(f"  - {error}")
        print()

        suggestions = parser.suggest_fixes(parsed)
        if suggestions:
            print("Suggestions:")
            for suggestion in suggestions:
                print(f"  {suggestion}")

        return 1

    print("✓ Commit message valid")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### Task Correlation Report

```python
from collections import defaultdict
from vibey.operations.git import analyze_batch

def generate_task_report(commits: List[Dict[str, str]]):
    """Generate report of task activity from commits."""
    result = analyze_batch(commits)

    print("=" * 60)
    print("TASK CORRELATION REPORT")
    print("=" * 60)
    print()

    print(f"Total Commits: {result.total_commits}")
    print(f"  With task references: {result.commits_with_tasks} "
          f"({result.commits_with_tasks/result.total_commits*100:.1f}%)")
    print(f"  Without task references: {result.commits_without_tasks} "
          f"({result.commits_without_tasks/result.total_commits*100:.1f}%)")
    print()

    print(f"Unique Tasks: {len(result.unique_tasks)}")
    for task_id in result.unique_tasks:
        print(f"  - {task_id}")
    print()

    print("Format Usage:")
    for format_name, count in sorted(result.format_usage.items()):
        pct = (count / result.total_commits) * 100
        print(f"  {format_name:15s}: {count:3d} ({pct:5.1f}%)")
    print()

    if result.unique_sprints:
        print(f"Sprints: {', '.join(result.unique_sprints)}")

    if result.unique_tracks:
        print(f"Tracks: {', '.join(result.unique_tracks)}")
```

---

## Performance Considerations

### Batch Processing

For large repositories, use batch processing:

```python
from vibey.operations.git import analyze_batch

# Process 1000 commits efficiently
commits = get_git_log(limit=1000)
result = analyze_batch(commits)

# Much faster than:
# for commit in commits:
#     parsed = parser.parse(commit["message"])
```

### Regex Compilation

All regex patterns are pre-compiled in `RegexPatterns` class for optimal performance.

### Memory Usage

For very large repositories (10,000+ commits), consider streaming:

```python
def stream_parse(commits_iterator):
    """Stream commits through parser without loading all into memory."""
    parser = CommitParser()

    for commit in commits_iterator:
        parsed = parser.parse(commit["message"], commit["sha"])
        yield parsed
```

---

## Error Handling

### Parse Errors

```python
parsed = parser.parse(malformed_message)

if parsed.parse_errors:
    print("Parse errors occurred:")
    for error in parsed.parse_errors:
        print(f"  - {error}")

if parsed.parse_warnings:
    print("Warnings:")
    for warning in parsed.parse_warnings:
        print(f"  - {warning}")
```

### Validation Errors

```python
try:
    parsed = parser.parse(message)
    errors = parser.validate(parsed)

    if errors:
        raise ValueError(f"Invalid commit: {', '.join(errors)}")

except Exception as e:
    print(f"Error: {e}")
```

---

## Testing

### Unit Tests

```python
def test_conventional_format():
    parser = CommitParser()

    message = "feat(task-001): add feature"
    parsed = parser.parse(message)

    assert parsed.type == "feat"
    assert parsed.scope == "task-001"
    assert len(parsed.tasks) == 1
    assert parsed.tasks[0].task_id == "task-001"
    assert parsed.tasks[0].format == CommitFormat.CONVENTIONAL

def test_footer_format():
    parser = CommitParser()

    message = """feat: add feature

    Task: task-001
    Status: completed
    """
    parsed = parser.parse(message)

    assert len(parsed.tasks) == 1
    assert parsed.tasks[0].task_id == "task-001"
    assert parsed.tasks[0].status == TaskStatus.COMPLETED
    assert parsed.tasks[0].format == CommitFormat.FOOTER
```

---

## Next Steps

With the commit parser complete, the following tasks can now proceed:

- **Task 003**: Git log analysis utilities (use `CommitParser` to analyze history)
- **Task 004**: Sprint velocity calculator (use parsed commits for metrics)
- **Task 005**: CLI command `vibey git analyze` (expose parser via CLI)
- **Task 008**: State reconstruction (parse commits at different refs)

---

## Implementation Summary

**Files Created:**
- `vibey/operations/git/commit_parser_schema.py` (schema definitions)
- `vibey/operations/git/commit_parser.py` (parser implementation)
- `vibey/operations/git/__init__.py` (package exports)

**Lines of Code:**
- Schema: ~350 lines
- Parser: ~550 lines
- Total: ~900 lines

**Features Delivered:**
- ✅ Multi-format parsing (4 formats)
- ✅ Status detection (8 keywords)
- ✅ Multi-task support
- ✅ Deduplication logic
- ✅ Validation engine
- ✅ Suggestion system
- ✅ Batch processing
- ✅ Configuration system
- ✅ Type-safe dataclasses
- ✅ Comprehensive error handling

**Test Coverage:** (Task 006 will add formal tests)
- Manual testing completed
- Integration examples provided
- Ready for unit test suite
