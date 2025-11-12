# Platform Tracking Design - Passive & On-Demand Approach

**Date:** 2025-11-11
**Status:** Partial Implementation (Phase 2 Data Model Complete)
**Approach:** Passive tracking, on-demand recalculation

---

## Implementation Status

**Completed (2025-11-11):**
- ✅ GitCommit model updated with REQUIRED `platform` field (string)
- ✅ GitCommit uses Unix timestamps (`submitted_at` as integer) to avoid timezone issues
- ✅ YAML serialization/deserialization for platform fields
- ✅ Task.add_commit() requires platform parameter
- ✅ Unit tests for platform tracking (6/6 tests passing)
- ✅ Platform validation enforced (empty platforms rejected)
- ⚠️ Legacy commits without platform are skipped during load (not migrated)

**Pending:**
- ⏳ CLI integration for platform detection (`vibey roadmap add-commit`)
- ⏳ Platform configuration system (PlatformConfig, PlatformDeployment)
- ⏳ Platform validation standard
- ⏳ Sprint recalculation engine
- ⏳ Platform detection utilities

---

## Design Philosophy

### Passive Platform Awareness

**Key Principles:**
1. **Deploy-time configuration** - Track which platforms Vibey is deployed for
2. **On-demand recalculation** - Only recalculate sizing when requested
3. **Completion-time tracking** - Record platform when tasks complete
4. **Validation enforcement** - Ensure completed tasks use approved platforms

**What We DON'T Do:**
- ❌ Pre-calculate sizing for all platforms
- ❌ Store multiple sizing variants per task
- ❌ Proactively check platform compatibility
- ❌ Maintain platform-specific sprint copies

---

## Core Requirements

### Requirement 1: Track Deployed Platforms

**Project-level configuration:**

```yaml
# .vibey/config/project.yaml (or new platforms.yaml)
platforms:
  deployed:
    - platform: claude-code
      context_window: 200000
      deployed_at: '2025-11-01T00:00:00Z'
      deployed_by: 'alice@example.com'
      primary: true
    - platform: goose
      context_window: 128000
      deployed_at: '2025-11-05T00:00:00Z'
      deployed_by: 'bob@example.com'
      primary: false

  active_platform: claude-code  # Current session platform (auto-detected)
```

**Why This Matters:**
- Know which platforms are valid for this project
- Validate task completions against approved platforms
- Provide context for sprint planning
- Enable platform-specific standards

---

### Requirement 2: Track Commit Platform Attribution

**GitCommit model changes:**

```python
@dataclass
class GitCommit:
    """Git commit associated with task.

    Platform tracking is REQUIRED for all new commits.
    Timestamps use Unix time to avoid timezone issues.
    """
    sha: str
    message: str
    date: datetime  # Git commit date (from git log)
    author: str

    # REQUIRED: Platform tracking
    platform: str  # e.g., "claude-code", "goose", "cursor"
    submitted_at: int  # Unix timestamp (seconds since epoch)
```

**YAML output with platform tracking:**

```yaml
task:
  id: auth-task-001
  status: in_progress
  commits:
    - sha: a1b2c3d4
      message: "feat: Start user registration"
      date: '2025-11-11T10:00:00Z'
      author: 'Alice <alice@example.com>'
      platform: claude-code           # ← REQUIRED
      submitted_at: 1731330000        # ← Unix timestamp (integer)
    - sha: b2c3d4e5
      message: "fix: Handle edge cases"
      date: '2025-11-11T14:00:00Z'
      author: 'Bob <bob@example.com>'
      platform: goose                 # ← REQUIRED
      submitted_at: 1731344400        # ← Unix timestamp (integer)
```

**Why Commit-Level Tracking:**
- Multiple developers can contribute to same task using different platforms
- Provides granular platform usage metrics
- Tracks which platform submitted which code changes
- Enables platform-specific performance analysis per commit

**Why Unix Timestamps:**
- Avoids timezone conversion errors
- Simple integer comparison
- Standard format across all platforms
- No ambiguity in storage/retrieval

---

### Requirement 3: Validate Platform on Completion

**Standard enforcement:**

```yaml
# Built-in standard (always enforced)
standard:
  id: platform-validation
  name: "Platform Validation"
  type: task_completion
  enforcement: blocking
  validation:
    type: platform_check
    config:
      must_be_deployed_platform: true
      error_message: "Task completed on {platform} but Vibey is only deployed for: {deployed_platforms}"
```

**Completion workflow:**

```bash
# User completes task
vibey roadmap complete auth-task-001

# System behavior:
# 1. Detect current platform (e.g., claude-code)
# 2. Check platforms.deployed list
# 3. If platform not in list → ERROR
# 4. If platform in list → Set completed_on_platform
```

**Error example:**

```
❌ Cannot complete task auth-task-001

Task completed on platform: cursor
Deployed platforms: claude-code, goose

Error: Vibey is not deployed for cursor in this project.

To fix:
  1. Deploy Vibey for cursor: vibey deploy run --platform cursor
  2. Or complete task using an approved platform
```

---

### Requirement 4: On-Demand Sprint Recalculation

**User-initiated recalculation:**

```bash
# User on Goose (128K) picks up sprint planned for Claude (200K)
vibey roadmap recalculate-sizing auth-sprint-1

# System behavior:
# 1. Detect current platform: goose (128K)
# 2. Check original sizing platform: claude-code (200K)
# 3. Recalculate all non-completed tasks for 128K context
# 4. Split tasks that don't fit
# 5. Update estimated_tokens in-place
```

**Example recalculation:**

```
🔄 Recalculating sprint sizing for current platform...

Current platform: goose (128K context window)
Original platform: claude-code (200K context window)

Task Sizing Updates:
  ✓ auth-task-001: Already completed (no change)
  ⚠ auth-task-002: 180K → TOO LARGE
    → Splitting into: auth-task-002-part-1 (90K)
                      auth-task-002-part-2 (90K)
  ✓ auth-task-003: 100K → OK (fits in 128K)
  ✓ auth-task-004: 80K → OK (fits in 128K)

Summary:
  Tasks before: 4
  Tasks after: 5
  Tasks split: 1
  Tasks merged: 0

✓ Sprint recalculated for goose (128K context)
```

---

## Data Model Changes

### GitCommit Model with Required Platform Tracking

```python
@dataclass
class GitCommit:
    """Git commit associated with task.

    Platform tracking is REQUIRED for all new commits.
    Timestamps use Unix time to avoid timezone issues.
    """
    sha: str
    message: str
    date: datetime  # Git commit date (from git log)
    author: str

    # REQUIRED: Platform tracking
    platform: str  # e.g., "claude-code", "goose", "cursor"
    submitted_at: int  # Unix timestamp (seconds since epoch)
```

### Task Model Changes for Splitting

```python
@dataclass
class Task:
    # ... all existing fields stay the same ...

    # NEW: Track if task was split from another
    split_from_task_id: Optional[str] = None
    split_part: Optional[int] = None  # Part 1, 2, 3, etc.
```

**Key Design Decisions:**
- Keep single `estimated_tokens` (not per-platform)
- Platform tracking at commit level, not task level
- **Platform is REQUIRED** for all new commits
- **Unix timestamps** to avoid timezone errors
- Split tasks get new IDs with parent tracking
- ⚠️ Legacy commits without platform are skipped during load

---

### New: Platform Configuration

```python
@dataclass
class PlatformDeployment:
    """Record of a platform deployment."""
    platform: str  # "claude-code", "goose", etc.
    context_window: int
    deployed_at: datetime
    deployed_by: str
    primary: bool = False  # Is this the primary platform?

@dataclass
class PlatformConfig:
    """Project platform configuration."""
    deployed: List[PlatformDeployment]
    active_platform: Optional[str] = None  # Auto-detected

    def is_deployed(self, platform: str) -> bool:
        """Check if platform is deployed for this project."""
        return any(d.platform == platform for d in self.deployed)

    def get_context_window(self, platform: str) -> Optional[int]:
        """Get context window for a platform."""
        for d in self.deployed:
            if d.platform == platform:
                return d.context_window
        return None
```

---

## CLI Commands

### 1. Deploy Platform

```bash
# Deploy Vibey for a new platform
vibey deploy run --platform goose

# Internally updates platforms.deployed:
# - Adds goose to deployed list
# - Records context window (from platform metadata)
# - Records deployer and timestamp
```

### 2. List Deployed Platforms

```bash
# Show deployed platforms
vibey platforms list

# Output:
# Deployed Platforms
# ══════════════════════════════════════════════════
#
# ✓ claude-code (200K context) [PRIMARY]
#   Deployed: 2025-11-01
#   Deployed by: alice@example.com
#
# ✓ goose (128K context)
#   Deployed: 2025-11-05
#   Deployed by: bob@example.com
#
# Current session: goose (auto-detected)
```

### 3. Recalculate Sprint Sizing

```bash
# Recalculate sizing for current platform
vibey roadmap recalculate-sizing <sprint-id>

# System:
# 1. Auto-detect current platform
# 2. Compare to original sizing
# 3. Split/merge tasks as needed
# 4. Update estimated_tokens in place
```

### 4. Check Sprint Compatibility

```bash
# Check if current platform can handle sprint
vibey roadmap check-compatibility <sprint-id>

# Output:
# Sprint Compatibility Check
# ══════════════════════════════════════════════════
#
# Current platform: goose (128K context)
# Sprint originally sized for: claude-code (200K)
#
# Task Compatibility:
#   ✓ auth-task-001: 100K (fits)
#   ✓ auth-task-003: 80K (fits)
#   ⚠ auth-task-002: 180K (TOO LARGE - exceeds context by 52K)
#
# Summary: 2/3 tasks compatible
#
# Recommendation:
#   Run: vibey roadmap recalculate-sizing auth-sprint-1
```

### 5. Add Commit with Platform Detection

```bash
# Add commit to task (auto-detects platform)
vibey roadmap add-commit auth-task-001 --auto

# System:
# 1. Detect current platform: goose
# 2. Check platforms.deployed
# 3. If goose in list → Allow, add commit with platform field
# 4. If not in list → Block with error
# 5. Record submitted_at timestamp
```

**Benefits of Commit-Level Tracking:**
- Multiple platforms can contribute to same task
- Granular attribution per code change
- Platform performance metrics per commit
- Historical analysis of platform usage

---

## Sprint Metadata Enhancement

```yaml
sprint:
  id: auth-sprint-1
  # ... existing fields ...

  # NEW: Platform metadata
  platform_metadata:
    sized_for_platform: claude-code      # Original platform
    sized_context_window: 200000         # Original context window
    sized_at: '2025-11-01T10:00:00Z'     # When sized
    last_recalculated_for: goose         # Last recalculation platform
    last_recalculated_at: '2025-11-05T14:00:00Z'
    recalculation_count: 2               # Times recalculated
```

---

## Task Splitting Logic

### When to Split

```python
def should_split_task(task: Task, target_context: int) -> bool:
    """Determine if task needs splitting."""
    # Rule: Task uses >85% of context window
    return task.estimated_tokens > (target_context * 0.85)

def split_task(task: Task, target_context: int) -> List[Task]:
    """Split task into multiple smaller tasks."""
    # Calculate safe task size (75% of context to leave room)
    safe_size = int(target_context * 0.75)

    # Calculate number of parts needed
    num_parts = math.ceil(task.estimated_tokens / safe_size)

    # Create split tasks
    split_tasks = []
    for i in range(num_parts):
        split_task = Task(
            id=f"{task.id}-part-{i+1}",
            title=f"{task.title} (Part {i+1}/{num_parts})",
            estimated_tokens=safe_size,
            split_from_task_id=task.id,
            split_part=i+1,
            # ... copy other fields ...
        )
        split_tasks.append(split_task)

    return split_tasks
```

### Example Split

**Original task (Claude Code, 200K context):**
```yaml
task:
  id: auth-task-002
  title: "Implement OAuth integration"
  estimated_tokens: 180000
  complexity: high
```

**After recalculation (Goose, 128K context):**
```yaml
# Original task marked as split
task:
  id: auth-task-002
  title: "Implement OAuth integration"
  status: split  # NEW status
  split_into: [auth-task-002-part-1, auth-task-002-part-2]

# Part 1
task:
  id: auth-task-002-part-1
  title: "Implement OAuth integration (Part 1/2)"
  estimated_tokens: 90000
  split_from_task_id: auth-task-002
  split_part: 1

# Part 2
task:
  id: auth-task-002-part-2
  title: "Implement OAuth integration (Part 2/2)"
  estimated_tokens: 90000
  split_from_task_id: auth-task-002
  split_part: 2
  dependencies:
    - type: task
      target_id: auth-task-002-part-1
      reason: "Must complete part 1 first"
```

---

## Platform Detection

### Auto-Detection Logic

```python
def detect_current_platform() -> Optional[str]:
    """Auto-detect current platform."""

    # Method 1: Check environment variable
    if platform := os.getenv("VIBEY_PLATFORM"):
        return platform

    # Method 2: Check for platform-specific indicators
    if os.getenv("CLAUDE_CODE_SESSION"):
        return "claude-code"

    if os.path.exists(".goose/config.yaml"):
        return "goose"

    if os.getenv("CURSOR_SESSION_ID"):
        return "cursor"

    # Method 3: Check running process
    # (inspect parent process, check for claude/goose/cursor)

    # Method 4: Ask user (fallback)
    return None  # Will prompt user to specify
```

### Context Window Detection

```python
# Platform context window registry
PLATFORM_CONTEXT_WINDOWS = {
    "claude-code": 200000,
    "goose": 128000,
    "cursor": 128000,  # Default, can vary
    "aider": 100000,
    "continue": 100000,
}

def get_context_window(platform: str) -> int:
    """Get context window for platform."""
    return PLATFORM_CONTEXT_WINDOWS.get(platform, 100000)
```

---

## Standards Integration

### Built-in Platform Standard

```yaml
# Automatically enforced standard
standard:
  id: platform-validation
  name: "Platform Validation"
  type: task_completion
  enforcement: blocking
  validation:
    type: platform_check
    config:
      require_deployed_platform: true
```

**Validation Logic:**

```python
def validate_platform_on_completion(task: Task, platform: str) -> ValidationResult:
    """Validate platform when completing task."""

    # Load platform config
    config = load_platform_config()

    # Check if platform is deployed
    if not config.is_deployed(platform):
        return ValidationResult(
            passed=False,
            message=f"Platform {platform} is not deployed for this project. "
                   f"Deployed platforms: {', '.join([d.platform for d in config.deployed])}. "
                   f"Run: vibey deploy run --platform {platform}"
        )

    return ValidationResult(passed=True)
```

---

## Implementation Plan

### Phase 1: Platform Configuration (Week 1)

**Tasks:**
1. Create `PlatformDeployment` and `PlatformConfig` dataclasses
2. Add platform detection utility
3. Update `vibey deploy` to record platform deployment
4. Create `vibey platforms list` command
5. Write unit tests

**Deliverables:**
- Platform configuration system
- Platform detection working
- Deploy command records platform

---

### Phase 2: Platform Tracking on Commits (Week 2)

**Tasks:**
1. ✅ Add REQUIRED `platform` field to GitCommit model
2. ✅ Change `submitted_at` to Unix timestamp (integer)
3. ✅ Update YAML serialization (dumper and loader)
4. ✅ Update `add_commit()` method to require platform parameter
5. ✅ Add validation for empty platform and negative timestamps
6. ✅ Write unit tests for platform tracking
7. Modify `vibey roadmap add-commit` CLI to detect and store platform
8. Create platform validation standard

**Deliverables:**
- ✅ GitCommit requires platform (string) and submitted_at (Unix timestamp)
- ✅ Platform validation enforced (empty platforms rejected)
- ✅ Unix timestamps avoid timezone errors
- ✅ All tests passing (6/6 tests pass)
- ⚠️ Legacy commits without platform skipped during load
- ⏳ CLI integration pending

---

### Phase 3: Sprint Recalculation (Week 2-3)

**Tasks:**
1. Add sprint platform metadata
2. Implement task splitting algorithm
3. Create `vibey roadmap recalculate-sizing` command
4. Create `vibey roadmap check-compatibility` command
5. Handle dependencies during splitting
6. Write recalculation tests

**Deliverables:**
- Sprint recalculation working
- Task splitting logic tested
- Dependency preservation

---

### Phase 4: Documentation & Testing (Week 3)

**Tasks:**
1. Write user documentation
2. Write platform selection guide
3. Update user journeys
4. Final integration testing
5. Backward compatibility testing

**Deliverables:**
- Complete documentation
- Platform guide
- All tests passing

---

## Backward Compatibility

### Migration Strategy

**For Existing Roadmaps:**

1. **No platform info** - Existing tasks without platform info:
   ```yaml
   task:
     id: task-001
     status: completed
     completed_on_platform: null  # ← Optional field, null is fine
   ```

2. **Assume primary platform** - If no platform metadata on sprint:
   ```python
   # Assume primary platform from config
   sprint.platform_metadata.sized_for_platform = config.deployed[0].platform
   ```

3. **No recalculation needed** - Only recalculate when user requests it

**Breaking Changes:** ❌ None - all new fields are optional

---

## Success Metrics

### Implementation Metrics
- ✅ Platform tracking in Task model
- ✅ Platform validation on completion
- ✅ Sprint recalculation working
- ✅ 100% backward compatibility

### Usage Metrics (Post-Implementation)
- 🎯 100% of completed tasks have platform attribution
- 🎯 95%+ platform detection accuracy
- 🎯 Zero unauthorized platform completions
- 🎯 Sprint recalculation reduces context overflow errors

---

## Timeline

| Phase | Duration | Focus |
|-------|----------|-------|
| Phase 1 | 1 week | Platform configuration |
| Phase 2 | 1 week | Completion tracking & validation |
| Phase 3 | 1 week | Sprint recalculation |
| Phase 4 | 1 week | Documentation & testing |

**Total:** 3-4 weeks (can be compressed to 3 weeks if needed)

---

## Key Simplifications from Original Design

### What We Removed ✂️

1. ❌ Pre-calculated sizing for all platforms
2. ❌ Multiple sizing variants per task
3. ❌ Platform-specific sprint copies
4. ❌ Proactive platform compatibility checking
5. ❌ Complex multi-platform analytics
6. ❌ Platform comparison reports

### What We Kept ✅

1. ✅ Track deployed platforms (essential)
2. ✅ Validate completion platform (security)
3. ✅ On-demand recalculation (when needed)
4. ✅ Task splitting logic (necessary)
5. ✅ Platform detection (convenience)

**Result:** Much simpler, more maintainable, achieves all goals

---

**Document Version:** 2.0 (Passive Approach)
**Created:** 2025-11-11
**Status:** Design Complete
**Approach:** Passive tracking, on-demand recalculation
