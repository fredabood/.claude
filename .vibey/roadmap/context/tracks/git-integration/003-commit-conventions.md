# Commit Message Conventions Specification

**Task:** git-integration-0-task-003
**Status:** Draft
**Author:** Architecture Agent
**Date:** 2025-11-24

## Executive Summary

This document defines how commit messages reference Vibey roadmap items (tasks, sprints, tracks). The conventions are designed to be compatible with existing standards while enabling automatic task correlation.

## Design Goals

1. **Compatibility** - Work with Conventional Commits, GitHub, GitLab conventions
2. **Parseable** - Machine-readable task references with clear regex patterns
3. **Flexible** - Support multiple formats for team preference
4. **Optional** - Task references are encouraged but not required by default
5. **Informative** - Commit messages remain human-readable

## Supported Formats

### Format 1: Conventional Commits (Recommended)

Task ID in the scope position:

```bash
# Basic format
<type>(<task-id>): <description>

# Examples
feat(task-001): implement content loader
fix(task-002): resolve null pointer in parser
test(task-003): add unit tests for validation
docs(task-004): update API documentation
refactor(task-005): extract common utilities
```

**Regex Pattern:**
```regex
^(?<type>\w+)\((?<task_id>[\w-]+)\):\s*(?<description>.+)$
```

**Advantages:**
- Follows widely-adopted standard
- Type classification preserved
- Single-line format
- Editor/tool support exists

### Format 2: Footer Reference

Task reference in commit message footer:

```bash
# Format
<type>: <description>

<optional body>

Task: <task-id>

# Example
feat: implement content loader functionality

Added ContentLoader class with support for:
- YAML frontmatter parsing
- Markdown body extraction
- Metadata validation

Task: python-package-3-task-001
```

**Regex Pattern:**
```regex
^Task:\s*(?<task_id>[\w-]+)\s*$
```

**Advantages:**
- Clean subject line (no scope clutter)
- Detailed body supported
- Multiple footers possible
- GitHub/GitLab issue linking style

### Format 3: Bracket Notation

Task ID in brackets:

```bash
# Format
[<task-id>] <description>

# Examples
[task-001] implement content loader
[TASK-001] implement content loader  # Case insensitive
[python-package-3-task-001] implement content loader  # Full ID
```

**Regex Pattern:**
```regex
^\[(?<task_id>[\w-]+)\]\s*(?<description>.+)$
```

**Advantages:**
- Simple, recognizable
- Common in many projects
- Easy to type
- Works with any commit style

### Format 4: Inline Reference

Task reference anywhere in message:

```bash
# Format
<message containing "Task: <task-id>" or "task-id">

# Examples
Implement content loader for task-001
Fix bug reported in task-002
Addresses task-003 and task-004
```

**Regex Pattern:**
```regex
\b(?:Task:\s*)?(?<task_id>(?:[a-z]+-)+\d+-task-\d+)\b
```

**Advantages:**
- Most flexible
- Natural language friendly
- Can reference multiple tasks easily

**Disadvantages:**
- Less structured
- May have false positives
- Harder to parse reliably

## Multi-Task Commits

A single commit can reference multiple tasks:

### Conventional Commits (Multiple Scopes)

```bash
# Primary task in scope, additional in footer
feat(task-001): implement shared utilities

Also addresses task-002 and task-003

Tasks: task-001, task-002, task-003
```

### Footer Multi-Reference

```bash
feat: refactor authentication module

Tasks: auth-task-001, auth-task-002
Closes: auth-task-003
```

### Bracket Multi-Reference

```bash
[task-001] [task-002] implement shared component
```

## Status Indication in Commits

Commits can indicate task status changes:

### Completion Indicators

```bash
# Footer indicators
Task: task-001
Status: completed

# Or using conventional keywords
Closes: task-001
Completes: task-001
Finishes: task-001

# Conventional commit with status
feat(task-001): implement feature [completed]
```

### Progress Indicators

```bash
# Partial progress
Task: task-001
Status: in_progress
Progress: 50%

# Or inline
feat(task-001): implement feature (WIP)
```

## Sprint and Track References

### Sprint Completion Commits

```bash
# Sprint completion
chore: complete sprint python-package-3

Sprint: python-package-3
Status: completed

Quality Gates:
- Test Coverage: 95% (passed)
- Documentation: 100% (passed)
```

### Track Milestone Commits

```bash
# Track milestone
chore: complete python-package track

Track: python-package
Status: completed
Sprints: 3/3 completed
Tasks: 24/24 completed
```

## Merge and Special Commits

### Merge Commits

```bash
# Standard merge
Merge branch 'feature/task-001' into main

Task: task-001
Status: completed

# Squash merge
feat: implement content management (#123)

Tasks: task-001, task-002, task-003
Status: completed
```

### Revert Commits

```bash
Revert "feat(task-001): implement content loader"

This reverts commit abc123.
Task: task-001
Status: reverted  # Or: in_progress
```

### Amend Note

```bash
# When amending, preserve task references
feat(task-001): implement content loader (amended)

Original: def456
Amended from: abc123
```

## Parsing Rules

### Parser Priority

When multiple formats are detected, use this priority:

1. Footer references (most explicit)
2. Conventional commit scope
3. Bracket notation
4. Inline references (least reliable)

### Task ID Formats

Supported task ID patterns:

```regex
# Full format: track-sprint-task-number
(?<track>[\w-]+)-(?<sprint>\d+)-task-(?<number>\d+)

# Short format: task-number (requires context)
task-(?<number>\d+)

# Custom format (configurable)
(?<custom_pattern>.+)
```

### Parsing Algorithm

```python
def parse_commit_message(message: str) -> ParsedCommit:
    """Parse commit message for Vibey references."""
    result = ParsedCommit()

    # Split into subject, body, footers
    parts = split_commit_message(message)

    # 1. Check footers first (most reliable)
    for footer in parts.footers:
        if footer.key in ['Task', 'Tasks']:
            result.tasks.extend(parse_task_list(footer.value))
        elif footer.key == 'Status':
            result.status = footer.value
        elif footer.key in ['Closes', 'Completes', 'Finishes']:
            result.tasks.extend(parse_task_list(footer.value))
            result.status = 'completed'
        elif footer.key == 'Sprint':
            result.sprint = footer.value

    # 2. Check conventional commit scope
    if match := CONVENTIONAL_PATTERN.match(parts.subject):
        result.type = match.group('type')
        scope = match.group('scope')
        if is_task_id(scope):
            result.tasks.append(scope)

    # 3. Check bracket notation
    if match := BRACKET_PATTERN.match(parts.subject):
        result.tasks.append(match.group('task_id'))

    # 4. Check inline references (if enabled)
    if config.parse_inline:
        for match in INLINE_PATTERN.finditer(message):
            task_id = match.group('task_id')
            if task_id not in result.tasks:
                result.tasks.append(task_id)

    return result
```

## Validation Rules

### Linting Checks

```yaml
# .vibey/config/commit-lint.yaml
commit_lint:
  enabled: true

  rules:
    # Task reference requirements
    require_task_reference: false  # Set true for strict mode
    allow_empty_scope: true

    # Format validation
    valid_types:
      - feat
      - fix
      - docs
      - style
      - refactor
      - test
      - chore
      - perf
      - ci
      - build
      - revert

    # Task ID validation
    task_id_pattern: "^[a-z]+-\\d+-task-\\d+$"
    validate_task_exists: true  # Check task exists in roadmap

    # Length limits
    subject_max_length: 72
    body_max_length: null  # No limit
```

### Validation Messages

```bash
# Missing task reference (when required)
ERROR: Commit message must reference a task
  Subject: "fix: resolve null pointer"
  Suggestion: Use "fix(task-id): resolve null pointer"
             or add "Task: task-id" footer

# Invalid task ID
WARNING: Task ID 'task-999' not found in roadmap
  Did you mean: task-001, task-002?

# Invalid type
ERROR: Unknown commit type 'feature'
  Valid types: feat, fix, docs, style, refactor, test, chore

# Subject too long
WARNING: Subject exceeds 72 characters (85 chars)
  Consider shortening or moving details to body
```

## Configuration

```yaml
# .vibey/config/git.yaml
git:
  commit:
    # Format preferences (in priority order)
    preferred_formats:
      - conventional  # feat(task-id): description
      - footer        # Task: task-id in footer
      - bracket       # [task-id] description

    # Parsing options
    parse_inline: false     # Parse inline task references
    case_sensitive: false   # Task ID case sensitivity

    # Validation options
    require_task_reference: false
    validate_task_exists: true
    validate_type: true

    # Auto-generation
    auto_add_footer: false  # Add Task footer automatically
    auto_scope: false       # Add task ID to scope automatically

  # Commit message template
  template: |
    <type>(<scope>): <description>

    <body>

    Task: <task-id>
```

## Editor Integration

### Git Commit Template

```bash
# .gitmessage template
# <type>(<task-id>): <description>
#
# Types: feat, fix, docs, style, refactor, test, chore
# Task ID: track-sprint-task-number (e.g., python-package-3-task-001)
#
# Body: Explain what and why (not how)
#
# Footers:
#   Task: <task-id>
#   Status: not_started | in_progress | completed
#   Closes: <task-id>  (marks task completed)
```

### VS Code Settings

```json
{
  "editor.rulers": [72, 100],
  "git.inputValidationSubjectLength": 72,
  "vibey.commit.autoSuggestTask": true,
  "vibey.commit.preferredFormat": "conventional"
}
```

## Examples

### Feature Implementation

```bash
feat(python-package-3-task-001): implement content loader

Add ContentLoader class with capabilities:
- Load content from filesystem
- Parse YAML frontmatter
- Validate content metadata
- Return ContentItem objects

The loader supports all content types: agents, workflows,
templates, handoffs, schemas, and examples.

Task: python-package-3-task-001
Status: completed
```

### Bug Fix

```bash
fix(git-integration-2-task-003): resolve commit parsing edge case

The commit parser failed when scope contained hyphens.
Updated regex to handle hyphenated task IDs correctly.

Closes: git-integration-2-task-003
```

### Documentation Update

```bash
docs(user-journey-audit-1-task-005): update API reference

- Add missing endpoints documentation
- Include request/response examples
- Update authentication section

Task: user-journey-audit-1-task-005
```

### Multi-Task Refactor

```bash
refactor: consolidate utility functions

Extract common utilities from multiple modules into shared
utils package. This addresses technical debt across several
tasks.

Tasks: task-001, task-002, task-003
Status: completed (all)
```

### Sprint Completion

```bash
chore: complete Sprint 3 - Content Management Interface

All 10 tasks completed:
- Content models defined
- CRUD operations implemented
- CLI commands added
- MCP tools registered
- Tests passing (29/29)

Sprint: python-package-3
Status: completed

Quality Gates:
- Unit Test Coverage: 95% (threshold: 90%) ✓
- Integration Tests: 100% (threshold: 95%) ✓
- Documentation: 100% (threshold: 100%) ✓
```

## Compatibility Matrix

| Standard/Tool | Conventional | Footer | Bracket | Inline |
|---------------|--------------|--------|---------|--------|
| Conventional Commits | ✓ Native | ✓ Compatible | ✓ Compatible | ⚠ Non-standard |
| GitHub Issues | ✓ Compatible | ✓ Compatible | ✓ Compatible | ✓ Compatible |
| GitLab Issues | ✓ Compatible | ✓ Compatible | ✓ Compatible | ✓ Compatible |
| Commitlint | ✓ Native | ✓ Compatible | ⚠ Needs config | ⚠ Needs config |
| Semantic Release | ✓ Native | ✓ Compatible | ⚠ Needs config | ✗ Not supported |
| JIRA | ⚠ Needs adapter | ✓ Compatible | ✓ Common format | ✓ Compatible |

## Appendix: Regex Patterns

```python
# Conventional Commits with task scope
CONVENTIONAL_PATTERN = re.compile(
    r'^(?P<type>\w+)'
    r'(?:\((?P<scope>[\w-]+)\))?'
    r'(?P<breaking>!)?'
    r':\s*'
    r'(?P<description>.+)$'
)

# Footer pattern (Git trailer format)
FOOTER_PATTERN = re.compile(
    r'^(?P<key>[\w-]+):\s*(?P<value>.+)$',
    re.MULTILINE
)

# Bracket notation
BRACKET_PATTERN = re.compile(
    r'^\[(?P<task_id>[\w-]+)\]\s*(?P<description>.+)$'
)

# Task ID (full format)
TASK_ID_PATTERN = re.compile(
    r'(?P<track>[\w-]+)-(?P<sprint>\d+)-task-(?P<number>\d+)'
)

# Inline task reference
INLINE_PATTERN = re.compile(
    r'\b(?:task:\s*)?(?P<task_id>[\w]+-\d+-task-\d+)\b',
    re.IGNORECASE
)

# Status keywords
STATUS_KEYWORDS = {
    'closes': 'completed',
    'completes': 'completed',
    'finishes': 'completed',
    'fixes': 'completed',
    'resolves': 'completed',
    'addresses': 'in_progress',
    'starts': 'in_progress',
    'wip': 'in_progress',
}
```

## Decision Log

| Decision | Options Considered | Choice | Rationale |
|----------|-------------------|--------|-----------|
| Primary format | Conventional, Custom | Conventional Commits | Industry standard, tooling support |
| Multi-format support | Single, Multiple | Multiple formats | Team flexibility |
| Task requirement | Required, Optional | Optional default | Gradual adoption |
| Inline parsing | Enabled, Disabled | Disabled default | Avoid false positives |
| Status keywords | Custom, GitHub-style | GitHub-style | Familiar to developers |
