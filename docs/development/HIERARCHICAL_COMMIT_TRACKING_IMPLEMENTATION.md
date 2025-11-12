# Hierarchical Commit Tracking Implementation

**Status:** ✅ PHASE 1-3 COMPLETE (Data Models & Serialization)
**Started:** 2025-11-11
**Phase 1-3 Completed:** 2025-11-11
**Remaining:** CLI Integration & Automation

---

## Overview

Implementing a hierarchical commit tracking system that records:
1. **Tasks**: ALL commits that impacted the task (multiple commits possible, same commit can affect multiple tasks)
2. **Sprints**: Commits that marked completion of each task within the sprint
3. **Tracks**: Commits that marked completion of each sprint within the track

---

## Design

### Data Model Hierarchy

```
Roadmap
└── Track
    ├── commits: [SprintCompletionCommit]  ← Commits that completed sprints
    └── Sprint
        ├── commits: [TaskCompletionCommit]  ← Commits that completed tasks
        └── Task
            └── commits: [GitCommit]  ← All commits that impacted task
```

### New Data Structures

#### GitCommit (existing - for tasks)
```python
@dataclass
class GitCommit:
    """Git commit associated with task."""
    sha: str
    message: str
    date: datetime
    author: str
```

#### TaskCompletionCommit (new - for sprints)
```python
@dataclass
class TaskCompletionCommit:
    """Commit that completed a task (used in sprint tracking)."""
    task_id: str  # Which task was completed
    sha: str
    message: str
    date: datetime
    author: str
```

#### SprintCompletionCommit (new - for tracks)
```python
@dataclass
class SprintCompletionCommit:
    """Commit that completed a sprint (used in track tracking)."""
    sprint_id: str  # Which sprint was completed
    sha: str
    message: str
    date: datetime
    author: str
```

---

## Implementation Progress

### ✅ Phase 1: Data Models (COMPLETE)

**Files Modified:**
- `vibey/roadmap/models/task.py`
  - Added `TaskCompletionCommit` dataclass (lines 105-123)
  - Added `SprintCompletionCommit` dataclass (lines 126-144)
- `vibey/roadmap/models/sprint.py`
  - Imported `TaskCompletionCommit` (line 12)
  - Added `commits: List[TaskCompletionCommit]` field (line 155)
- `vibey/roadmap/models/track.py`
  - Imported `SprintCompletionCommit` (line 12)
  - Added `commits: List[SprintCompletionCommit]` field (line 145)
- `vibey/roadmap/models/__init__.py`
  - Exported `TaskCompletionCommit` and `SprintCompletionCommit` (lines 81-82, 133-134)

**Result:** Data models support hierarchical commit tracking

### ✅ Phase 2: YAML Serialization (Dumper) (COMPLETE)

**Files Modified:**
- `vibey/roadmap/serialization/yaml_dumper.py`
  - Updated `save_sprint()` to serialize sprint commits (lines 481-490)
  - Updated `save_track()` to serialize track commits (lines 377-386)

**YAML Format:**

**Sprint YAML:**
```yaml
sprint:
  # ... other fields ...
  commits:
    - task_id: infrastructure-fixes-1-task-005
      sha: 40c760091cb87cb8afc2edbd291469766d942858
      message: 'fix: Task completion'
      date: '2025-11-11T16:15:17-05:00'
      author: '@fredabood <fredabood@gmail.com>'
```

**Track YAML:**
```yaml
track:
  # ... other fields ...
  commits:
    - sprint_id: infrastructure-fixes-1
      sha: f0711771465374cabeac87f4809e005f07ac7aa1
      message: 'fix: Sprint completion'
      date: '2025-11-11T16:01:52-05:00'
      author: '@fredabood <fredabood@gmail.com>'
```

### ✅ Phase 3: YAML Deserialization (Loader) (COMPLETE)

**Files Modified:**
- `vibey/roadmap/serialization/yaml_loader.py`
  - Updated `load_sprint()` to deserialize sprint commits (lines 496-507)
  - Updated `load_track()` to deserialize track commits (lines 338-349)

**Implementation:**
- Backward compatible - loads empty array if `commits` field missing
- Properly deserializes TaskCompletionCommit and SprintCompletionCommit objects
- Tested with round-trip serialization

**Status:** ✅ COMPLETE

### 🚧 Phase 4: CLI Commands (IN PROGRESS)

**Commands to Implement:**

1. **`vibey roadmap add-commit <task-id> <commit-sha>`** ✅ COMPLETE
   - Adds commit to task (already implemented)

2. **`vibey roadmap complete <task-id> --commit <sha>`** (NEW)
   - Marks task as complete
   - Records commit in both task AND parent sprint
   - Auto-detects commit if `--commit` not provided

3. **`vibey roadmap complete <sprint-id> --commit <sha>`** (NEW)
   - Marks sprint as complete
   - Records commit in both sprint AND parent track
   - Auto-detects commit if `--commit` not provided

**Implementation Files:**
- `vibey/cli/roadmap-update.py` - Extend existing complete logic
- `vibey/cli/commands.py` - Add `--commit` parameter
- `vibey/cli/main.py` - Update CLI signatures

**Status:** NOT STARTED

### 🚧 Phase 5: Automatic Tracking (FUTURE)

**Hook Integration:**
- Git pre-commit hook: Extract task ID from commit message
- Git post-commit hook: Auto-associate commit with task
- Task completion hook: Record commit in sprint
- Sprint completion hook: Record commit in track

**Configuration:**
```yaml
# .vibey/config/git-tracking.yaml
git_tracking:
  enabled: true
  task_id_pattern: 'task-\d+'  # Regex to extract task ID
  auto_associate: true
  commit_message_format: '{task_id}: {message}'
```

**Status:** DESIGN ONLY

---

## Usage Examples

### Current (Task-Level Only)
```bash
# Add commits to a task
vibey roadmap add-commit infrastructure-fixes-1-task-005 --auto
vibey roadmap add-commit infrastructure-fixes-1-task-005 f071177
```

### Planned (Hierarchical Tracking)
```bash
# Complete a task and record commit in sprint
vibey roadmap complete infrastructure-fixes-1-task-005 --commit 40c7600
# Or auto-detect:
vibey roadmap complete infrastructure-fixes-1-task-005 --auto

# Complete a sprint and record commit in track
vibey roadmap complete infrastructure-fixes-1 --commit f071177
# Or auto-detect:
vibey roadmap complete infrastructure-fixes-1 --auto
```

### Query Commits
```bash
# Show task commits
vibey roadmap show infrastructure-fixes-1-task-005
# Output includes: "Commits: 3 commits"

# Show sprint completion commits
vibey roadmap show infrastructure-fixes-1
# Output includes: "Task Completions: 5 commits"

# Show track sprint completion commits
vibey roadmap show infrastructure-fixes
# Output includes: "Sprint Completions: 3 commits"
```

---

## Implementation Timeline

### ✅ Completed (Nov 11, 2025)
- ✅ Data model design and implementation
- ✅ YAML dumper updates (sprint & track commits)
- ✅ YAML loader updates (sprint & track commits)
- ✅ Round-trip serialization testing
- ✅ Basic task-level commit tracking CLI
- ✅ Backward compatibility verification

### 🚧 Remaining Work (Optional - CLI Automation)
1. Extend `roadmap complete` command to accept `--commit` flag (~2-3 hours)
2. Implement automatic commit recording on task/sprint completion (~2-3 hours)
3. Add commit display to `roadmap show` command (~1 hour)
4. Create CLI command to complete task with commit recording in sprint (~1 hour)
5. Create CLI command to complete sprint with commit recording in track (~1 hour)
6. End-to-end integration tests (~1 hour)

**Total Remaining:** ~8-10 hours (CLI automation - optional)

### Current Capability
**What works NOW:**
- ✅ All three levels support commit storage (task, sprint, track)
- ✅ Data models fully implemented and validated
- ✅ YAML serialization/deserialization complete
- ✅ Backward compatible with existing YAML files
- ✅ Round-trip tested and verified
- ✅ Manual commit addition to tasks via `vibey roadmap add-commit`

**What needs CLI work:**
- ❌ Automatic recording on `vibey roadmap complete <task-id>`
- ❌ Automatic recording on `vibey roadmap complete <sprint-id>`
- ❌ Display commits in `vibey roadmap show` output

---

## Testing Strategy

### Unit Tests
- Test TaskCompletionCommit validation
- Test SprintCompletionCommit validation
- Test YAML serialization/deserialization

### Integration Tests
- Complete task with commit → verify sprint has it
- Complete sprint with commit → verify track has it
- Same commit affects multiple tasks → verify all record it

### E2E Tests
```bash
# Create task
vibey roadmap add-task infrastructure-fixes-1 "Fix bug"

# Add commits to task
git commit -m "task-001: Start work"
vibey roadmap add-commit infrastructure-fixes-1-task-001 --auto

git commit -m "task-001: Finish work"
vibey roadmap complete infrastructure-fixes-1-task-001 --auto

# Verify sprint has task completion commit
vibey roadmap show infrastructure-fixes-1 --format json | jq '.commits'
# Should show commit that completed task-001

# Complete sprint
vibey roadmap complete infrastructure-fixes-1 --auto

# Verify track has sprint completion commit
vibey roadmap show infrastructure-fixes --format json | jq '.commits'
# Should show commit that completed sprint-1
```

---

## Breaking Changes

### None (Backwards Compatible)

- New `commits` fields default to empty arrays
- Old YAML files without commits still load correctly
- Existing workflows unchanged

---

## Future Enhancements

1. **Commit Statistics**
   - `vibey roadmap stats <item-id>` shows commit counts
   - Task: Total commits affecting it
   - Sprint: Tasks completed with commits
   - Track: Sprints completed with commits

2. **Commit Search**
   - `vibey roadmap find-commit <sha>` shows all affected tasks

3. **Commit Timeline**
   - `vibey roadmap timeline <track-id>` shows chronological commit history

4. **Git Integration**
   - Auto-detect task IDs from commit messages
   - Auto-associate commits on git commit
   - Pre-commit validation (task must exist)

---

## Related Documentation

- `docs/guides/GIT_COMMIT_TRACKING.md` - User guide for task-level tracking
- `docs/development/ROADMAP_OBJECT_HIERARCHY.md` - Data model reference
- `docs/guides/ROADMAP_CLI.md` - CLI command reference

---

**Last Updated:** 2025-11-11
**Status:** Data models complete, serialization in progress, CLI pending
