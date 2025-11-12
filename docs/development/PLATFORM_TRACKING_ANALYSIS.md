# Platform Tracking Analysis - Multi-Platform Roadmap Management

**Date:** 2025-11-11
**Status:** Analysis Complete
**Related:** standards-system track, multi-platform track

---

## Questions Addressed

1. **How are we tracking the different platforms that Vibey gets deployed for in a given project?**
2. **If a person's session is in Claude, is their platform tied to the tasks they complete?**
3. **If one person builds a sprint plan using a 200K token context window, can their coworker pick up the sprint and recalculate the sizing of open tasks for a different context window?**

---

## Current State: Platform Tracking

### ❌ Platform Tracking Does NOT Currently Exist

**What We Found:**

```python
# Task model (vibey/roadmap/models/task.py)
@dataclass
class Task:
    id: str
    sprint_id: str
    track_id: str
    roadmap_id: str
    # ... fields ...
    estimated_tokens: int  # ← No platform context!
    # ... more fields ...
```

**Key Issues:**

1. **No platform field** in Task/Sprint/Track/Roadmap models
2. **No created_by_platform** tracking for tasks/commits
3. **No context window metadata** for tasks
4. **No platform-specific sizing** support
5. **Task sizing is absolute** (estimated_tokens), not platform-relative

---

## Problem Statement

### Scenario 1: Mixed Platform Development Team

**Team Setup:**
- Alice uses **Claude Code** (200K token context window)
- Bob uses **Goose** (128K token context window)
- Carol uses **Cursor** (variable context window)

**Current Behavior:**

```yaml
# Sprint planned by Alice (Claude Code, 200K tokens)
task:
  id: auth-task-001
  title: "Implement OAuth integration"
  estimated_tokens: 180000  # ← Sized for 200K window!
  complexity: high
```

**Problem:** Bob picks up this task using Goose (128K window):
- Task won't fit in Bob's context window
- No indication task was sized for different platform
- No way to recalculate sizing for Bob's platform
- Task completion not tied to platform used

---

### Scenario 2: Task Completion Platform Attribution

**Current Behavior:**

```yaml
task:
  id: auth-task-001
  status: completed
  completed: '2025-11-11T18:00:00Z'
  assigned_agent: web-developer
  commits:
    - sha: a1b2c3d
      author: '@alice <alice@example.com>'
      # ← No platform attribution!
```

**Questions:**
- Was this task completed using Claude? Goose? Cursor?
- Should platform-specific success metrics be tracked?
- Do certain platforms complete certain task types faster?
- Should platform capabilities affect task assignment?

---

### Scenario 3: Sprint Recalculation for Different Platforms

**Desired Workflow:**

```bash
# Alice creates sprint using Claude Code (200K tokens)
vibey roadmap create-sprint auth-sprint-1 --platform claude-code

# Bob wants to work on same sprint using Goose (128K tokens)
vibey roadmap recalculate-sprint auth-sprint-1 --platform goose
# Should resize all tasks for 128K context window
```

**Current State:** ❌ This functionality doesn't exist

---

## Proposed Solution: Platform-Aware Roadmap System

### Phase 1: Platform Tracking Infrastructure

#### 1.1: Add Platform Metadata to Models

```python
# vibey/roadmap/models/common.py
from enum import Enum

class Platform(str, Enum):
    """Supported platforms."""
    CLAUDE_CODE = "claude-code"
    GOOSE = "goose"
    CURSOR = "cursor"
    AIDER = "aider"
    CONTINUE = "continue"
    WINDSURF = "windsurf"
    JETBRAINS = "jetbrains"
    UNKNOWN = "unknown"

@dataclass
class PlatformCapabilities:
    """Platform capabilities and constraints."""
    platform: Platform
    context_window_tokens: int
    supports_multi_file: bool
    supports_streaming: bool
    max_output_tokens: Optional[int] = None

    # Platform-specific features
    supports_image_input: bool = False
    supports_tool_use: bool = True
    supports_artifacts: bool = False
```

#### 1.2: Update Task Model

```python
@dataclass
class TaskSizing:
    """Task sizing for different platforms."""
    platform: Platform
    estimated_tokens: int
    complexity: Complexity
    fits_in_context: bool

    def __post_init__(self):
        """Validate sizing."""
        if self.estimated_tokens < 0:
            raise ValueError("Estimated tokens cannot be negative")

@dataclass
class Task:
    # ... existing fields ...

    # NEW: Platform-aware sizing
    sizing: Dict[Platform, TaskSizing] = field(default_factory=dict)
    primary_platform: Optional[Platform] = None  # Platform task was sized for

    # NEW: Platform completion tracking
    completed_on_platform: Optional[Platform] = None

    # MODIFIED: Make estimated_tokens computed property
    @property
    def estimated_tokens(self) -> int:
        """Get estimated tokens for primary platform."""
        if self.primary_platform and self.primary_platform in self.sizing:
            return self.sizing[self.primary_platform].estimated_tokens
        # Fallback for backward compatibility
        return self._legacy_estimated_tokens
```

#### 1.3: Update GitCommit Tracking

```python
@dataclass
class GitCommit:
    """Git commit associated with task."""
    sha: str
    message: str
    date: datetime
    author: str

    # NEW: Platform tracking
    platform: Optional[Platform] = None  # Platform used for this commit
    context_window_used: Optional[int] = None  # Actual context window at time
```

#### 1.4: Add Sprint Platform Metadata

```python
@dataclass
class SprintMetadata:
    """Sprint metadata."""
    created_by: str
    created_on_platform: Platform  # Platform used to plan sprint
    target_platforms: List[Platform]  # Platforms this sprint should work on
    sizing_validated_for: List[Platform]  # Platforms where sizing is validated
```

---

### Phase 2: Platform-Aware CLI Commands

#### 2.1: Sprint Creation with Platform Context

```bash
# Create sprint with platform context
vibey roadmap create-sprint auth-sprint-1 \
  --platform claude-code \
  --context-window 200000

# Output:
# ✓ Sprint created: auth-sprint-1
# ✓ Platform: claude-code (200K token context)
# ✓ Tasks sized for 200K context window
#
# Note: This sprint can be recalculated for other platforms
```

#### 2.2: Sprint Recalculation for Different Platforms

```bash
# Recalculate sprint sizing for different platform
vibey roadmap recalculate-sprint auth-sprint-1 \
  --platform goose \
  --context-window 128000

# Output:
# 🔄 Recalculating sprint auth-sprint-1 for goose (128K context)...
#
# Task Sizing Changes:
#   auth-task-001: 180K → Split into 2 tasks (90K each)
#   auth-task-002: 100K → OK (fits in 128K)
#   auth-task-003: 150K → Split into 2 tasks (75K each)
#
# Summary:
#   Original: 5 tasks
#   Recalculated: 7 tasks (2 tasks split)
#   Platform: goose (128K context)
#
# ✓ Sprint recalculated successfully
```

#### 2.3: Task Completion with Platform Tracking

```bash
# Complete task (auto-detect platform)
vibey roadmap complete auth-task-001

# Output:
# ✓ Task completed: auth-task-001
# ✓ Platform: claude-code (detected)
# ✓ Context window: 200K tokens
# ✓ Task sized for: claude-code (200K)
# ✓ Platform match: Yes ✓
```

#### 2.4: Platform Compatibility Check

```bash
# Check if sprint is compatible with current platform
vibey roadmap check-platform auth-sprint-1

# Output:
# Platform Compatibility Check
# ════════════════════════════════════════════════════
#
# Current Platform: goose (128K context window)
# Sprint Platform: claude-code (200K context window)
#
# Task Compatibility:
#   ✓ auth-task-001: 90K tokens (fits)
#   ✓ auth-task-002: 100K tokens (fits)
#   ⚠ auth-task-003: 180K tokens (TOO LARGE - need 52K more)
#   ✓ auth-task-004: 80K tokens (fits)
#
# Summary:
#   Compatible: 3/4 tasks (75%)
#   Requires splitting: 1 task
#
# Recommendation:
#   Run: vibey roadmap recalculate-sprint auth-sprint-1 --platform goose
```

---

### Phase 3: Platform Analytics & Insights

#### 3.1: Platform Usage Metrics

```bash
# Show platform usage statistics
vibey roadmap stats --platform-breakdown

# Output:
# Platform Usage Statistics
# ════════════════════════════════════════════════════
#
# Tasks Completed by Platform:
#   claude-code: 45 tasks (60%)
#   goose: 25 tasks (33%)
#   cursor: 5 tasks (7%)
#
# Average Completion Time by Platform:
#   claude-code: 2.3 hours/task
#   goose: 2.8 hours/task
#   cursor: 3.1 hours/task
#
# Platform Efficiency (tokens used vs estimated):
#   claude-code: 85% efficient
#   goose: 78% efficient
#   cursor: 72% efficient
```

#### 3.2: Platform-Specific Success Metrics

```bash
# Compare platform performance
vibey roadmap compare-platforms auth-sprint-1

# Output:
# Platform Comparison: auth-sprint-1
# ════════════════════════════════════════════════════
#
# Claude Code:
#   Tasks completed: 3
#   Avg time: 2.1 hours
#   Context efficiency: 87%
#   Quality gate pass rate: 100%
#
# Goose:
#   Tasks completed: 2
#   Avg time: 2.6 hours
#   Context efficiency: 81%
#   Quality gate pass rate: 100%
#
# Insights:
#   - Claude Code 19% faster on average
#   - Both platforms achieve 100% quality
#   - Consider platform for time-critical tasks
```

---

## Implementation Plan

### Sprint 1: Platform Infrastructure (1 week)

**Tasks:**
1. Define `Platform` enum and `PlatformCapabilities`
2. Add `TaskSizing` dataclass
3. Update `Task` model with platform fields
4. Update `GitCommit` with platform tracking
5. Update `SprintMetadata` with platform context
6. Update YAML serialization/deserialization
7. Write unit tests
8. Verify backward compatibility

**Deliverables:**
- Platform-aware data models
- YAML schema updated
- All tests passing
- No breaking changes

---

### Sprint 2: Platform Detection & Auto-Configuration (1 week)

**Tasks:**
1. Create platform detection utility
2. Implement auto-detection for Claude Code/Goose/Cursor
3. Add platform configuration to `.vibey/config.yaml`
4. Create platform capabilities registry
5. Write detection tests

**Deliverables:**
- Auto-detect current platform
- Platform capabilities database
- Configuration support

---

### Sprint 3: Sprint Recalculation Engine (1 week)

**Tasks:**
1. Create task splitting algorithm
2. Implement `recalculate_sprint_for_platform()`
3. Add task merging logic (when moving to larger context)
4. Handle dependencies during splitting
5. Write integration tests

**Deliverables:**
- Sprint recalculation working
- Task splitting/merging logic
- Dependency preservation

---

### Sprint 4: CLI Integration (1 week)

**Tasks:**
1. Add `--platform` flag to relevant commands
2. Implement `recalculate-sprint` command
3. Implement `check-platform` command
4. Update `complete` command with platform tracking
5. Write CLI tests

**Deliverables:**
- Platform-aware CLI commands
- Recalculation command working
- Platform compatibility checking

---

### Sprint 5: Platform Analytics (1 week)

**Tasks:**
1. Create platform metrics collector
2. Implement platform usage statistics
3. Create platform comparison reports
4. Add platform efficiency tracking
5. Write analytics tests

**Deliverables:**
- Platform usage metrics
- Comparison reports
- Efficiency tracking

---

### Sprint 6: Documentation & Migration (1 week)

**Tasks:**
1. Write user documentation
2. Write migration guide
3. Create platform selection guide
4. Update user journeys
5. Final testing and validation

**Deliverables:**
- Complete documentation
- Migration guide
- Platform selection guide

---

## Answers to Original Questions

### Q1: How are we tracking platforms?

**Current Answer:** ❌ We are NOT tracking platforms

**Proposed Solution:**
- Add `Platform` enum to data models
- Track `completed_on_platform` for tasks
- Track `created_on_platform` for sprints
- Track `platform` for git commits

---

### Q2: Is a person's platform tied to their task completions?

**Current Answer:** ❌ No, platform is not tracked

**Proposed Solution:**
- Auto-detect platform on task completion
- Store `completed_on_platform` in task
- Store `platform` in git commits
- Enable platform-specific analytics

---

### Q3: Can sprints be recalculated for different context windows?

**Current Answer:** ❌ No, this functionality doesn't exist

**Proposed Solution:**
- `vibey roadmap recalculate-sprint <id> --platform <platform>`
- Automatically split tasks that are too large
- Merge tasks when moving to larger context
- Preserve dependencies during recalculation
- Validate sizing before starting work

---

## Migration Strategy

### For Existing Roadmaps

**Backward Compatibility:**
1. Make all platform fields optional
2. Default platform to "unknown"
3. Use `_legacy_estimated_tokens` for existing tasks
4. Gradual migration: add platform info as tasks are worked on

**Migration Script:**
```bash
# Add platform metadata to existing roadmap
vibey roadmap migrate-platforms \
  --default-platform claude-code \
  --context-window 200000

# Optionally recalculate for target platforms
vibey roadmap recalculate-all \
  --target-platforms claude-code,goose,cursor
```

---

## Standards Integration

### Platform-Specific Standards

Once the standards system is implemented, we can enforce platform-specific requirements:

```yaml
# Example: Ensure tasks fit in target platform context windows
standard:
  id: platform-compatibility
  name: "Platform Context Window Compatibility"
  type: task_completion
  enforcement: blocking
  validation:
    type: custom
    script: check_platform_compatibility.py
    config:
      required_platforms:
        - claude-code
        - goose
      max_context_usage_percent: 90  # Task can't use >90% of context
```

---

## Success Metrics

### Implementation Metrics
- ✅ Platform tracking in all models
- ✅ Sprint recalculation working
- ✅ Platform detection accurate
- ✅ 100% backward compatibility

### Usage Metrics (Post-Implementation)
- 🎯 80%+ of tasks have platform attribution
- 🎯 95%+ platform detection accuracy
- 🎯 Zero context overflow errors
- 🎯 Platform-aware sizing reduces task failures

---

## Timeline

| Sprint | Duration | Focus |
|--------|----------|-------|
| Sprint 1 | 1 week | Platform infrastructure |
| Sprint 2 | 1 week | Platform detection |
| Sprint 3 | 1 week | Recalculation engine |
| Sprint 4 | 1 week | CLI integration |
| Sprint 5 | 1 week | Platform analytics |
| Sprint 6 | 1 week | Documentation & migration |

**Total:** 6 weeks

---

## Relationship to Other Tracks

**Dependencies:**
- None (can start immediately)

**Enhances:**
- `standards-system` - Can enforce platform compatibility standards
- `multi-platform` - Provides infrastructure for multi-platform support
- `testing-system` - Platform-specific test validation

**Recommended Start:** After standards-system Sprint 3 (validators available)

---

**Document Version:** 1.0
**Created:** 2025-11-11
**Status:** Proposed
