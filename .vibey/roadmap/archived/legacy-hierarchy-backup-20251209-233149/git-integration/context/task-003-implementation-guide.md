# Git Log Analysis Utilities Implementation Guide

**Task:** git-integration-1-task-003
**Sprint:** git-integration-1 (Git History & Commit Analysis)
**Status:** Completed
**Date:** 2025-11-24

---

## Overview

This document describes the `GitLogAnalyzer` implementation, which provides utilities for retrieving and analyzing Git commit history with integrated roadmap reference extraction.

**Implementation File:** `vibey/operations/git/log_analyzer.py`

**Key Features:**
- Git command wrappers for commit retrieval
- Branch and tag analysis
- Task/sprint/track correlation from commits
- Contributor analysis
- File change tracking
- Time-based queries

---

## Quick Start

### Basic Repository Analysis

```python
from vibey.operations.git import analyze_repository

# Analyze last 100 commits
result = analyze_repository(repo_path=".", max_count=100)

print(f"Analyzed {result.parse_result.total_commits} commits")
print(f"Found {len(result.parse_result.unique_tasks)} unique tasks")
print(f"Contributors: {result.total_contributors}")
print(f"Date range: {result.start_date} to {result.end_date}")
```

### Initialize Analyzer

```python
from vibey.operations.git import GitLogAnalyzer

# Create analyzer for current repo
analyzer = GitLogAnalyzer(repo_path=".")

# Check if valid git repo
if analyzer.is_git_repo():
    print(f"Current branch: {analyzer.get_current_branch()}")
    print(f"Current SHA: {analyzer.get_current_sha()}")
```

---

## Core Functionality

### 1. Commit Retrieval

#### Get Recent Commits

```python
# Get last 10 commits
commits = analyzer.get_commits(max_count=10)

for commit in commits:
    print(f"{commit.sha[:7]} - {commit.author_name}: {commit.message[:50]}")
```

#### Get Commits in Date Range

```python
# Get commits from last 2 weeks
commits = analyzer.get_commits(since="2 weeks ago")

# Get commits from specific date range
commits = analyzer.get_commits(
    since="2024-01-01",
    until="2024-01-31"
)
```

#### Get Commits for Specific Ref Range

```python
# Commits between two refs
commits = analyzer.get_commits(ref_range="v1.0.0..v2.0.0")

# Commits on feature branch not in main
commits = analyzer.get_commits(ref_range="main..feature/new-feature")

# Last 10 commits
commits = analyzer.get_commits(ref_range="HEAD~10..HEAD")
```

#### Filter by Author

```python
# Get commits by specific author
commits = analyzer.get_commits(author="John Doe")

# Can use email
commits = analyzer.get_commits(author="john@example.com")
```

#### Filter by Message Content

```python
# Get commits mentioning "bug fix"
commits = analyzer.get_commits(grep="bug fix")

# Case-insensitive search
commits = analyzer.get_commits(grep="(?i)security")
```

#### Filter by File Paths

```python
# Get commits affecting specific files
commits = analyzer.get_commits(paths=["src/main.py", "README.md"])

# Get commits in directory
commits = analyzer.get_commits(paths=["src/"])
```

#### Single Commit Retrieval

```python
# Get specific commit by SHA
commit = analyzer.get_commit_by_sha("abc1234")

print(f"Author: {commit.author_name}")
print(f"Date: {commit.date}")
print(f"Message: {commit.message}")
print(f"Files changed: {commit.files_changed}")
print(f"Insertions: {commit.insertions}")
print(f"Deletions: {commit.deletions}")
```

### 2. Branch Operations

#### List Branches

```python
# Get local branches
branches = analyzer.get_branches()

for branch in branches:
    marker = "*" if branch.is_current else " "
    print(f"{marker} {branch.name} ({branch.sha[:7]})")

# Get remote branches
remote_branches = analyzer.get_branches(remote=True)

# Get all branches (local + remote)
all_branches = analyzer.get_branches(all_branches=True)
```

#### Get Branch Commits

```python
# Get all commits on feature branch
commits = analyzer.get_branch_commits("feature/new-feature")

# Get commits unique to feature branch (not in main)
commits = analyzer.get_branch_commits(
    branch="feature/new-feature",
    base="main"
)

# Analyze what's new on feature branch
for commit in commits:
    print(f"- {commit.message.splitlines()[0]}")
```

### 3. Tag Operations

#### List Tags

```python
# Get all tags
tags = analyzer.get_tags()

for tag in tags:
    tag_type = "annotated" if tag.is_annotated else "lightweight"
    print(f"{tag.name:20s} {tag.sha[:7]} ({tag_type})")
    if tag.message:
        print(f"  Message: {tag.message}")
```

#### Get Commits Between Tags

```python
# Get all commits between releases
commits = analyzer.get_commits_between_tags("v1.0.0", "v2.0.0")

print(f"Changes in v2.0.0:")
for commit in commits:
    print(f"- {commit.message.splitlines()[0]}")
```

#### Find Tags for Commit

```python
# Which tags contain this commit?
tags = analyzer.find_tags_containing_commit("abc1234")

print(f"Commit is in releases: {', '.join(tags)}")
```

### 4. Task Correlation

#### Find Commits for Task

```python
# Find all commits that worked on a task
commits = analyzer.find_commits_for_task("git-integration-1-task-003")

print(f"Found {len(commits)} commits for task:")
for commit in commits:
    print(f"{commit.date.strftime('%Y-%m-%d')} {commit.sha[:7]} - {commit.author_name}")
    print(f"  {commit.message.splitlines()[0]}")

    # Access parsed references
    if commit.parsed:
        for task_ref in commit.parsed.tasks:
            status = f"[{task_ref.status.value}]" if task_ref.status else ""
            print(f"    Task: {task_ref.task_id} {status}")
```

#### Find Commits for Sprint

```python
# Find all commits that reference a sprint
commits = analyzer.find_commits_for_sprint("git-integration-1")

print(f"Sprint activity: {len(commits)} commits")
```

#### Get Task Contributors

```python
# Who worked on this task?
contributors = analyzer.get_contributors_for_task("git-integration-1-task-003")

print("Contributors:")
for contributor, commit_count in contributors:
    print(f"  {contributor}: {commit_count} commits")
```

#### Get File Changes for Task

```python
# What files were changed for this task?
files = analyzer.get_file_changes_for_task("git-integration-1-task-003")

print("Files modified:")
for file_path, change_count in sorted(files.items(), key=lambda x: x[1], reverse=True):
    print(f"  {file_path}: {change_count} changes")
```

### 5. Analysis Operations

#### Full Repository Analysis

```python
# Comprehensive analysis
result = analyzer.analyze(
    ref_range="v1.0.0..HEAD",
    max_count=500
)

# Access results
print(f"Commits analyzed: {len(result.commits)}")
print(f"Date range: {result.start_date} to {result.end_date}")
print(f"Unique tasks: {len(result.parse_result.unique_tasks)}")
print(f"Unique sprints: {len(result.parse_result.unique_sprints)}")
print(f"Contributors: {result.total_contributors}")

# Task breakdown
print("\nTasks worked on:")
for task_id in result.parse_result.unique_tasks:
    print(f"  - {task_id}")

# Format usage
print("\nCommit message formats:")
for format_name, count in result.parse_result.format_usage.items():
    pct = (count / result.parse_result.total_commits) * 100
    print(f"  {format_name}: {count} ({pct:.1f}%)")

# Contributors list
print("\nContributors:")
for contributor in result.contributors:
    print(f"  - {contributor}")
```

#### Recent Activity Analysis

```python
# Analyze last 2 weeks
result = analyzer.analyze(since="2 weeks ago")

print(f"Last 2 weeks activity:")
print(f"  Commits: {result.parse_result.total_commits}")
print(f"  Tasks: {len(result.parse_result.unique_tasks)}")
print(f"  With task refs: {result.parse_result.commits_with_tasks}")
print(f"  Without task refs: {result.parse_result.commits_without_tasks}")

# Calculate percentage with task references
pct_with_refs = (result.parse_result.commits_with_tasks /
                 result.parse_result.total_commits * 100)
print(f"  Task reference rate: {pct_with_refs:.1f}%")
```

---

## Data Structures

### CommitInfo

Full commit information with parsed roadmap references:

```python
commit = analyzer.get_commit_by_sha("abc1234")

# Basic info
print(f"SHA: {commit.sha}")
print(f"Author: {commit.author_name} <{commit.author_email}>")
print(f"Date: {commit.date}")
print(f"Message: {commit.message}")

# Parents (for merge commits)
print(f"Parents: {commit.parents}")

# File statistics
print(f"Files changed: {commit.files_changed}")
print(f"Insertions: +{commit.insertions}")
print(f"Deletions: -{commit.deletions}")

# Parsed roadmap references (if analyzed)
if commit.parsed:
    print(f"Type: {commit.parsed.type}")
    print(f"Tasks: {[t.task_id for t in commit.parsed.tasks]}")
    if commit.parsed.sprint:
        print(f"Sprint: {commit.parsed.sprint.sprint_id}")
```

### BranchInfo

Branch metadata:

```python
branches = analyzer.get_branches()

for branch in branches:
    print(f"Name: {branch.name}")
    print(f"SHA: {branch.sha}")
    print(f"Current: {branch.is_current}")
    print(f"Remote: {branch.is_remote}")
    print(f"Upstream: {branch.upstream}")
```

### TagInfo

Tag metadata:

```python
tags = analyzer.get_tags()

for tag in tags:
    print(f"Name: {tag.name}")
    print(f"SHA: {tag.sha}")
    print(f"Annotated: {tag.is_annotated}")
    if tag.message:
        print(f"Message: {tag.message}")
    if tag.tagger:
        print(f"Tagger: {tag.tagger}")
    if tag.date:
        print(f"Date: {tag.date}")
```

### AnalysisResult

Complete analysis results:

```python
result = analyzer.analyze(max_count=100)

# Commits with full details
for commit in result.commits:
    # Each CommitInfo has .parsed attribute
    pass

# Parse statistics
print(f"Total: {result.parse_result.total_commits}")
print(f"With tasks: {result.parse_result.commits_with_tasks}")
print(f"Without tasks: {result.parse_result.commits_without_tasks}")
print(f"Parse errors: {result.parse_result.parse_errors}")

# Unique references
print(f"Tasks: {result.parse_result.unique_tasks}")
print(f"Sprints: {result.parse_result.unique_sprints}")
print(f"Tracks: {result.parse_result.unique_tracks}")

# Format usage
print(f"Format usage: {result.parse_result.format_usage}")

# Time range
print(f"Start: {result.start_date}")
print(f"End: {result.end_date}")

# Branches and tags
print(f"Branches: {result.branches}")
print(f"Tags: {result.tags}")

# Contributors
print(f"Total contributors: {result.total_contributors}")
print(f"Contributors: {result.contributors}")
```

---

## Integration Examples

### Task Progress Report

```python
def generate_task_progress_report(task_id: str):
    """Generate progress report for a task from git history."""
    analyzer = GitLogAnalyzer()

    # Find all commits for task
    commits = analyzer.find_commits_for_task(task_id)

    if not commits:
        print(f"No commits found for task {task_id}")
        return

    # Sort by date
    commits.sort(key=lambda c: c.date)

    print(f"Task Progress Report: {task_id}")
    print("=" * 60)
    print(f"Total commits: {len(commits)}")
    print(f"First commit: {commits[0].date.strftime('%Y-%m-%d')}")
    print(f"Last commit: {commits[-1].date.strftime('%Y-%m-%d')}")
    print()

    # Contributors
    contributors = analyzer.get_contributors_for_task(task_id)
    print("Contributors:")
    for contributor, count in contributors:
        print(f"  {contributor}: {count} commits")
    print()

    # Files changed
    files = analyzer.get_file_changes_for_task(task_id)
    print(f"Files modified: {len(files)}")
    for file_path in sorted(files.keys())[:10]:  # Top 10
        print(f"  {file_path}")
    print()

    # Commit timeline
    print("Timeline:")
    for commit in commits:
        status_indicator = ""
        if commit.parsed:
            for task_ref in commit.parsed.tasks:
                if task_ref.task_id == task_id and task_ref.status:
                    status_indicator = f" [{task_ref.status.value}]"
                    break

        print(f"  {commit.date.strftime('%Y-%m-%d')} {commit.sha[:7]}{status_indicator}")
        print(f"    {commit.message.splitlines()[0]}")
```

### Sprint Activity Report

```python
def generate_sprint_report(sprint_id: str):
    """Generate activity report for a sprint."""
    analyzer = GitLogAnalyzer()

    # Find sprint tags (if they exist)
    all_tags = analyzer.get_tags()
    start_tag = f"sprint/{sprint_id}/start"
    end_tag = f"sprint/{sprint_id}/end"

    start_tag_exists = any(t.name == start_tag for t in all_tags)
    end_tag_exists = any(t.name == end_tag for t in all_tags)

    # Get commits
    if start_tag_exists and end_tag_exists:
        # Use tags for exact range
        commits = analyzer.get_commits_between_tags(start_tag, end_tag)
    else:
        # Search by message reference
        commits = analyzer.find_commits_for_sprint(sprint_id)

    print(f"Sprint Activity Report: {sprint_id}")
    print("=" * 60)
    print(f"Total commits: {len(commits)}")

    # Analyze commits
    all_tasks = set()
    for commit in commits:
        commit.parsed = analyzer.parser.parse(commit.message, commit.sha)
        for task in commit.parsed.tasks:
            all_tasks.add(task.task_id)

    print(f"Unique tasks: {len(all_tasks)}")
    for task_id in sorted(all_tasks):
        task_commits = [c for c in commits
                       if any(t.task_id == task_id for t in c.parsed.tasks)]
        print(f"  {task_id}: {len(task_commits)} commits")
```

### Branch Comparison

```python
def compare_branches(base: str, feature: str):
    """Compare two branches to see what's new."""
    analyzer = GitLogAnalyzer()

    # Get commits unique to feature branch
    commits = analyzer.get_branch_commits(branch=feature, base=base)

    print(f"Changes in {feature} not in {base}:")
    print("=" * 60)
    print(f"Total commits: {len(commits)}")
    print()

    # Parse commits for task references
    tasks = set()
    for commit in commits:
        commit.parsed = analyzer.parser.parse(commit.message, commit.sha)
        for task in commit.parsed.tasks:
            tasks.add(task.task_id)

    if tasks:
        print(f"Tasks addressed ({len(tasks)}):")
        for task_id in sorted(tasks):
            print(f"  - {task_id}")
        print()

    print("Commits:")
    for commit in commits:
        print(f"  {commit.sha[:7]} - {commit.author_name}")
        print(f"    {commit.message.splitlines()[0]}")
```

### Release Notes Generator

```python
def generate_release_notes(from_tag: str, to_tag: str):
    """Generate release notes from git history."""
    analyzer = GitLogAnalyzer()

    # Get commits between tags
    commits = analyzer.get_commits_between_tags(from_tag, to_tag)

    print(f"Release Notes: {from_tag} → {to_tag}")
    print("=" * 60)
    print()

    # Group by commit type
    features = []
    fixes = []
    other = []

    for commit in commits:
        commit.parsed = analyzer.parser.parse(commit.message, commit.sha)

        subject = commit.message.splitlines()[0]

        if commit.parsed.type == "feat":
            features.append(subject)
        elif commit.parsed.type == "fix":
            fixes.append(subject)
        else:
            other.append(subject)

    if features:
        print("### Features")
        for feature in features:
            print(f"- {feature}")
        print()

    if fixes:
        print("### Bug Fixes")
        for fix in fixes:
            print(f"- {fix}")
        print()

    if other:
        print("### Other Changes")
        for change in other[:5]:  # Limit to 5
            print(f"- {change}")
        print()

    # Contributors
    contributors = set()
    for commit in commits:
        contributors.add(commit.author_name)

    print(f"### Contributors ({len(contributors)})")
    for contributor in sorted(contributors):
        print(f"- {contributor}")
```

### Time-Based Analysis

```python
def analyze_by_week():
    """Analyze commit activity by week."""
    from datetime import datetime, timedelta

    analyzer = GitLogAnalyzer()

    # Get last 4 weeks
    weeks = []
    for i in range(4):
        week_start = datetime.now() - timedelta(weeks=i+1)
        week_end = datetime.now() - timedelta(weeks=i)

        commits = analyzer.get_commits(
            since=week_start.strftime("%Y-%m-%d"),
            until=week_end.strftime("%Y-%m-%d")
        )

        weeks.append((week_start, len(commits)))

    print("Weekly Activity:")
    print("=" * 60)
    for week_start, commit_count in reversed(weeks):
        bar = "█" * (commit_count // 5)
        print(f"{week_start.strftime('%Y-%m-%d')}: {bar} ({commit_count})")
```

---

## Performance Considerations

### Limiting Results

Always use `max_count` for large repositories:

```python
# Good: limit results
commits = analyzer.get_commits(max_count=1000)

# Bad: retrieves entire history (could be millions)
commits = analyzer.get_commits()
```

### Efficient Filtering

Use git's built-in filtering when possible:

```python
# Good: git filters before retrieving
commits = analyzer.get_commits(
    since="1 month ago",
    author="John",
    grep="bug"
)

# Bad: retrieve all then filter in Python
commits = analyzer.get_commits()
commits = [c for c in commits if "bug" in c.message]
```

### Batch Analysis

When analyzing many commits, let the analyzer parse in batch:

```python
# Good: single analysis with batch parsing
result = analyzer.analyze(max_count=1000)

# Bad: parse each commit individually
commits = analyzer.get_commits(max_count=1000)
for commit in commits:
    commit.parsed = analyzer.parser.parse(commit.message)
```

---

## Error Handling

### Check Repository Validity

```python
analyzer = GitLogAnalyzer(repo_path="/some/path")

if not analyzer.is_git_repo():
    print("Error: Not a git repository")
    exit(1)

# Proceed with analysis
commits = analyzer.get_commits()
```

### Handle Missing Refs

```python
try:
    commits = analyzer.get_commits(ref_range="nonexistent..HEAD")
except subprocess.CalledProcessError as e:
    print(f"Invalid ref range: {e}")
```

### Handle Empty Results

```python
commits = analyzer.find_commits_for_task("unknown-task")

if not commits:
    print("No commits found for this task")
else:
    print(f"Found {len(commits)} commits")
```

---

## Testing

### Manual Testing

```python
# Test basic functionality
analyzer = GitLogAnalyzer(repo_path=".")

# Test commit retrieval
commits = analyzer.get_commits(max_count=10)
assert len(commits) <= 10
assert all(c.sha for c in commits)

# Test parsing integration
for commit in commits:
    commit.parsed = analyzer.parser.parse(commit.message, commit.sha)
    assert commit.parsed is not None

# Test task finding
commits = analyzer.find_commits_for_task("git-integration-1-task-003")
for commit in commits:
    assert any(t.task_id == "git-integration-1-task-003"
              for t in commit.parsed.tasks)
```

---

## Next Steps

With the log analyzer complete, the following tasks can now proceed:

- **Task 004**: Sprint velocity calculator (use `GitLogAnalyzer` to analyze sprint commits)
- **Task 005**: CLI command `vibey git analyze` (expose analyzer via CLI)
- **Task 008**: State reconstruction (use analyzer to query history at different refs)

---

## Implementation Summary

**Files Created:**
- `vibey/operations/git/log_analyzer.py` (~650 lines)
- Updated `vibey/operations/git/__init__.py` with exports

**Features Delivered:**
- ✅ Git command wrappers (commits, branches, tags)
- ✅ Flexible commit retrieval with filters
- ✅ Branch and tag operations
- ✅ Task/sprint correlation
- ✅ Contributor analysis
- ✅ File change tracking
- ✅ Time-based queries
- ✅ Comprehensive analysis results
- ✅ Integration with CommitParser
- ✅ Type-safe dataclasses
- ✅ Error handling

**Lines of Code:**
- Log analyzer: ~650 lines
- Total git operations: ~1,500+ lines (schema + parser + analyzer)
