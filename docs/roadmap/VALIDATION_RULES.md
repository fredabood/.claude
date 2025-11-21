# Roadmap Validation Rules Reference

**Created:** 2025-11-21
**Sprint:** roadmap-integrity-fixes-6
**Status:** ✅ Production Ready

---

## Overview

This document provides a complete reference of all validation rules enforced by the Vibey roadmap validation system. Rules are organized by category and include examples, rationale, and auto-repair capabilities.

---

## Rule Categories

1. **Syntax Rules** - YAML syntax and file structure
2. **Schema Rules** - Required fields and data types
3. **Consistency Rules** - Status/progress alignment
4. **Integrity Rules** - References and dependencies
5. **Dependency Rules** - Blocking relationships
6. **Progress Rules** - Counter accuracy

---

## 1. Syntax Rules

### Rule 1.1: Valid YAML Syntax

**Level:** CRITICAL (blocks commit)

**Check:** All YAML files must have valid syntax

**Validator:** Fast validation (all profiles)

**Example Failure:**
```yaml
track:
  id: example-track
  name: Invalid YAML: missing closing quote
  status: in_progress
```

**Error Message:**
```
❌ Validation errors found in track.yaml:
  Line 3: mapping values are not allowed here
```

**Fix:**
- Correct YAML syntax
- Ensure proper indentation (2 spaces)
- Quote strings with special characters
- Balance all brackets and quotes

**Auto-Repair:** ❌ No (manual fix required)

---

### Rule 1.2: File Loading

**Level:** HIGH (blocks commit in standard+ profiles)

**Check:** All YAML files must load successfully

**Validator:** Fast validation (standard, thorough profiles)

**Example Failure:**
- File exists but contains Python object serialization (`!!python/object`)
- File contains invalid unicode characters
- File size exceeds limits

**Error Message:**
```
❌ Failed to load: .vibey/roadmap/track-1/track.yaml
  Reason: could not determine a constructor for the tag '!!python/object'
```

**Fix:**
- Remove Python serialization tags
- Validate file encoding (UTF-8)
- Check for binary data in YAML

**Auto-Repair:** ❌ No (manual fix required)

---

## 2. Schema Rules

### Rule 2.1: Required Track Fields

**Level:** HIGH (blocks commit)

**Check:** Track YAML must contain all required fields

**Required Fields:**
```yaml
track:
  id: string (required)
  name: string (required)
  roadmap_id: string (required)
  status: enum (required)
  blocked: boolean (required)
  priority: enum (required)
  created: datetime (required)
  progress: object (required)
  sprints: list (required)
```

**Example Failure:**
```yaml
track:
  id: example-track
  name: Example Track
  # Missing: status, blocked, priority, etc.
```

**Error Message:**
```
❌ Missing required field 'status' in track example-track
```

**Fix:** Add all required fields according to schema

**Auto-Repair:** ❌ No (manual fix required)

---

### Rule 2.2: Required Sprint Fields

**Level:** HIGH (blocks commit)

**Check:** Sprint YAML must contain all required fields

**Required Fields:**
```yaml
sprint:
  id: string (required)
  name: string (required)
  track_id: string (required)
  roadmap_id: string (required)
  status: enum (required)
  blocked: boolean (required)
  created: datetime (required)
  progress: object (required)
  tasks: list (required)
```

**Example Failure:**
```yaml
sprint:
  id: track-1
  name: Sprint 1
  # Missing: track_id, status, etc.
```

**Error Message:**
```
❌ Missing required field 'track_id' in sprint track-1
```

**Fix:** Add all required fields according to schema

**Auto-Repair:** ❌ No (manual fix required)

---

### Rule 2.3: Required Task Fields

**Level:** HIGH (blocks commit)

**Check:** Task YAML must contain all required fields

**Required Fields:**
```yaml
task:
  id: string (required)
  sprint_id: string (required)
  track_id: string (required)
  roadmap_id: string (required)
  task_type: enum (required)
  title: string (required)
  description: string (required)
  status: enum (required)
  blocked: boolean (required)
  created: datetime (required)
```

**Example Failure:**
```yaml
task:
  id: track-1-task-001
  title: Example Task
  # Missing: sprint_id, status, etc.
```

**Error Message:**
```
❌ Missing required field 'sprint_id' in task track-1-task-001
```

**Fix:** Add all required fields according to schema

**Auto-Repair:** ❌ No (manual fix required)

---

### Rule 2.4: Valid Status Values

**Level:** HIGH (blocks commit)

**Check:** Status field must be a valid enum value

**Valid Values:**
- `not_started`
- `in_progress`
- `completed`
- `blocked`
- `on_hold`
- `cancelled`
- `production_ready` (tracks/sprints only)
- `deployed` (tracks/sprints only)

**Example Failure:**
```yaml
task:
  status: done  # Invalid - should be 'completed'
```

**Error Message:**
```
❌ Invalid status value 'done' in task track-1-task-001
  Valid values: not_started, in_progress, completed, blocked, on_hold, cancelled
```

**Fix:** Use valid status enum value

**Auto-Repair:** ❌ No (manual fix required)

---

### Rule 2.5: Valid Priority Values

**Level:** MEDIUM (warning)

**Check:** Priority field must be a valid enum value

**Valid Values:**
- `critical`
- `high`
- `medium`
- `low`

**Example Failure:**
```yaml
track:
  priority: urgent  # Invalid - should be 'critical'
```

**Error Message:**
```
⚠️  Invalid priority value 'urgent' in track example-track
  Valid values: critical, high, medium, low
```

**Fix:** Use valid priority enum value

**Auto-Repair:** ❌ No (manual fix required)

---

## 3. Consistency Rules

### Rule 3.1: Status/Progress Consistency

**Level:** HIGH (blocks commit)

**Check:** Progress counters must be consistent with status

**Rules:**
- If status = `not_started`, progress should be 0%
- If status = `completed`, progress should be 100%
- If status = `in_progress`, progress should be 0-99%

**Example Failure:**
```yaml
sprint:
  status: completed
  progress:
    tasks_completed: 3
    tasks_total: 10
    completion_percent: 30  # Inconsistent!
```

**Error Message:**
```
❌ Status 'completed' but progress is 30% (should be 100%) in sprint track-1
```

**Fix:** Align status and progress

**Auto-Repair:** ✅ Yes (can auto-correct progress counters)

---

### Rule 3.2: Sprint Count Consistency

**Level:** HIGH (blocks commit)

**Check:** Number of sprint objects must match sprints_total

**Example Failure:**
```yaml
track:
  progress:
    sprints_total: 5
  sprints:
    - id: track-1  # Only 1 sprint listed
```

**Error Message:**
```
❌ Sprint count (1) must match sprints_total (5) in track example-track
```

**Fix:** Ensure sprint list matches count

**Auto-Repair:** ✅ Yes (can auto-correct sprints_total)

---

### Rule 3.3: Task Count Consistency

**Level:** HIGH (blocks commit)

**Check:** Number of task objects must match tasks_total

**Example Failure:**
```yaml
sprint:
  progress:
    tasks_total: 10
  tasks:
    - id: task-001
    - id: task-002  # Only 2 tasks listed
```

**Error Message:**
```
❌ Task count (2) must match tasks_total (10) in sprint track-1
```

**Fix:** Ensure task list matches count

**Auto-Repair:** ✅ Yes (can auto-correct tasks_total)

---

### Rule 3.4: Completed Count Accuracy

**Level:** HIGH (blocks commit)

**Check:** Completed counts must match actual completed objects

**Example Failure:**
```yaml
sprint:
  progress:
    tasks_completed: 5  # Claimed
  tasks:
    - status: completed
    - status: completed
    - status: in_progress  # Only 2 actually completed
```

**Error Message:**
```
❌ Progress mismatch in sprint track-1:
  Claimed: 5 completed
  Actual:  2 completed
```

**Fix:** Update completed count to match reality

**Auto-Repair:** ✅ Yes (auto-fixes progress counters)

---

### Rule 3.5: Completion Percentage Accuracy

**Level:** MEDIUM (warning)

**Check:** Completion percentage must match ratio of completed/total

**Calculation:** `completion_percent = (completed / total) * 100`

**Example Failure:**
```yaml
sprint:
  progress:
    tasks_completed: 3
    tasks_total: 10
    completion_percent: 50  # Should be 30
```

**Error Message:**
```
⚠️  Completion percentage mismatch in sprint track-1:
  Claimed: 50%
  Actual:  30%
```

**Fix:** Recalculate percentage

**Auto-Repair:** ✅ Yes (auto-fixes percentages)

---

## 4. Integrity Rules

### Rule 4.1: No Broken References

**Level:** HIGH (blocks commit in advanced validation)

**Check:** All referenced IDs must exist

**Referenced IDs:**
- Task → Sprint (via `sprint_id`)
- Sprint → Track (via `track_id`)
- Task/Sprint/Track → Roadmap (via `roadmap_id`)
- Dependencies (via `depends_on`, `blocks`)
- Depended-on-by references

**Example Failure:**
```yaml
task:
  id: task-001
  sprint_id: non-existent-sprint  # Broken reference!
```

**Error Message:**
```
❌ Broken reference: Task task-001 references non-existent sprint 'non-existent-sprint'
```

**Fix:** Update reference to valid ID or create missing object

**Auto-Repair:** ⚠️ Partial (can detect, manual fix required)

---

### Rule 4.2: No Circular Dependencies

**Level:** HIGH (blocks commit in advanced validation)

**Check:** Dependency graph must be acyclic

**Example Failure:**
```yaml
# Task A depends on Task B
task-a:
  depends_on:
    - blocker_id: task-b

# Task B depends on Task A (circular!)
task-b:
  depends_on:
    - blocker_id: task-a
```

**Error Message:**
```
❌ Circular dependency detected:
  task-a → task-b → task-a
```

**Fix:** Break circular dependency chain

**Auto-Repair:** ❌ No (requires human decision)

---

### Rule 4.3: No Orphaned Tasks

**Level:** MEDIUM (warning in advanced validation)

**Check:** All tasks must belong to a sprint

**Example Failure:**
```yaml
# Task exists but no sprint references it
task:
  id: orphaned-task
  sprint_id: sprint-1  # Sprint exists but doesn't list this task
```

**Error Message:**
```
⚠️  Orphaned task detected: orphaned-task
  Task claims sprint sprint-1 but sprint doesn't list it
```

**Fix:** Add task to sprint's task list

**Auto-Repair:** ✅ Yes (can add task to sprint)

---

### Rule 4.4: Bidirectional Dependency Consistency

**Level:** MEDIUM (warning)

**Check:** If A depends on B, then B should have A in depended_on_by

**Example Failure:**
```yaml
task-a:
  depends_on:
    - blocker_id: task-b

task-b:
  depended_on_by: []  # Missing task-a!
```

**Error Message:**
```
⚠️  Dependency mismatch:
  task-a depends on task-b
  But task-b doesn't list task-a in depended_on_by
```

**Fix:** Update both sides of dependency

**Auto-Repair:** ✅ Yes (can sync dependencies)

---

## 5. Dependency Rules

### Rule 5.1: Valid Blocker IDs

**Level:** HIGH (blocks commit)

**Check:** All blocker IDs in dependencies must exist

**Example Failure:**
```yaml
task:
  depends_on:
    - blocker_id: non-existent-task
      blocker_type: task
```

**Error Message:**
```
❌ Invalid blocker_id 'non-existent-task' in task example-task
```

**Fix:** Use valid blocker ID

**Auto-Repair:** ❌ No (manual fix required)

---

### Rule 5.2: Valid Blocker Types

**Level:** HIGH (blocks commit)

**Check:** Blocker type must match blocker ID format

**Valid Types:**
- `task` - Blocker is a task
- `sprint` - Blocker is a sprint
- `track` - Blocker is a track

**Example Failure:**
```yaml
task:
  depends_on:
    - blocker_id: track-1-task-001
      blocker_type: sprint  # Wrong type!
```

**Error Message:**
```
❌ Blocker type mismatch:
  blocker_id 'track-1-task-001' is a task but type is 'sprint'
```

**Fix:** Correct blocker type

**Auto-Repair:** ✅ Yes (can infer correct type)

---

### Rule 5.3: No Self-Dependencies

**Level:** HIGH (blocks commit)

**Check:** Objects cannot depend on themselves

**Example Failure:**
```yaml
task:
  id: task-001
  depends_on:
    - blocker_id: task-001  # Self-dependency!
```

**Error Message:**
```
❌ Self-dependency detected: task-001 depends on itself
```

**Fix:** Remove self-dependency

**Auto-Repair:** ✅ Yes (can remove)

---

### Rule 5.4: Blocked Status Consistency

**Level:** MEDIUM (warning)

**Check:** If object has blockers, blocked field should be true

**Example Failure:**
```yaml
task:
  blocked: false
  depends_on:
    - blocker_id: task-002
      required_status: completed
      current_status: in_progress  # Blocker not satisfied!
```

**Error Message:**
```
⚠️  Blocked status inconsistency in task task-001:
  Has unsatisfied blockers but blocked=false
```

**Fix:** Update blocked field

**Auto-Repair:** ✅ Yes (can auto-update)

---

## 6. Progress Rules

### Rule 6.1: Development Tasks Accuracy

**Level:** HIGH (blocks commit in advanced validation)

**Check:** development_tasks_total/completed must match actual development tasks

**Example Failure:**
```yaml
sprint:
  progress:
    development_tasks_total: 10
    development_tasks_completed: 5
  tasks:
    - task_type: development
      status: completed
    - task_type: development
      status: completed
    # Only 2 development tasks exist!
```

**Error Message:**
```
❌ Development task count mismatch in sprint example-sprint:
  Claimed: 10 total, 5 completed
  Actual:  2 total, 2 completed
```

**Fix:** Recalculate from actual tasks

**Auto-Repair:** ✅ Yes (auto-fixes progress)

---

### Rule 6.2: Gate Tasks Accuracy

**Level:** HIGH (blocks commit in advanced validation)

**Check:** Gate task counts must match actual gate tasks

**Types:**
- `completion_gate_tasks` - Pre-completion validation
- `production_gate_tasks` - Pre-production validation

**Example Failure:**
```yaml
sprint:
  progress:
    completion_gate_tasks_total: 3
    completion_gate_tasks_completed: 3
  tasks:
    # No completion gate tasks exist!
```

**Error Message:**
```
❌ Completion gate task count mismatch in sprint example-sprint:
  Claimed: 3 total, 3 completed
  Actual:  0 total, 0 completed
```

**Fix:** Recalculate from actual gate tasks

**Auto-Repair:** ✅ Yes (auto-fixes progress)

---

### Rule 6.3: Aggregate Progress Accuracy

**Level:** HIGH (blocks commit in advanced validation)

**Check:** tasks_total must equal sum of all task type counts

**Calculation:**
```
tasks_total = development_tasks_total +
              completion_gate_tasks_total +
              production_gate_tasks_total
```

**Example Failure:**
```yaml
sprint:
  progress:
    tasks_total: 20
    development_tasks_total: 10
    completion_gate_tasks_total: 3
    production_gate_tasks_total: 2
    # Sum = 15, not 20!
```

**Error Message:**
```
❌ Aggregate progress mismatch in sprint example-sprint:
  tasks_total (20) ≠ sum of task types (15)
```

**Fix:** Recalculate totals

**Auto-Repair:** ✅ Yes (auto-fixes aggregates)

---

## Validation Severity Levels

### CRITICAL

- **Impact:** Blocks commit in all profiles
- **Examples:** YAML syntax errors
- **Fix Required:** Immediate
- **Auto-Repair:** Usually no

### HIGH

- **Impact:** Blocks commit in standard/thorough profiles or advanced validation
- **Examples:** Missing required fields, broken references
- **Fix Required:** Before merge
- **Auto-Repair:** Sometimes

### MEDIUM

- **Impact:** Warning, doesn't block
- **Examples:** Progress mismatches, minor inconsistencies
- **Fix Required:** Soon
- **Auto-Repair:** Usually yes

### LOW

- **Impact:** Informational
- **Examples:** Style violations, suggestions
- **Fix Required:** Optional
- **Auto-Repair:** Always yes

---

## Auto-Repair Capabilities

### ✅ Auto-Repairable

- Progress counter mismatches
- Completion percentages
- Sprint/task count totals
- Bidirectional dependencies
- Blocked status updates
- Orphaned task assignment

### ⚠️ Partially Auto-Repairable

- Broken references (detection only)
- Dependency type inference

### ❌ Not Auto-Repairable

- YAML syntax errors
- Missing required fields
- Circular dependencies (requires human decision)
- Invalid enum values

---

## Testing Validation Rules

### Manual Testing

```bash
# Create test file with known violation
echo "invalid: yaml: syntax:" > test.yaml

# Run validation
vibey roadmap validate-fast

# Check error message
```

### Automated Testing

```python
# In tests/test_validation_rules.py
def test_rule_1_1_yaml_syntax():
    """Test Rule 1.1: Valid YAML Syntax"""
    invalid_yaml = "invalid: yaml: syntax:"
    result = validate_yaml(invalid_yaml)
    assert result.errors[0].code == "INVALID_YAML_SYNTAX"
```

---

## Rule Enforcement Matrix

| Rule | Fast-Quick | Fast-Standard | Fast-Thorough | Advanced | Auto-Repair |
|------|------------|---------------|---------------|----------|-------------|
| 1.1 YAML Syntax | ✅ | ✅ | ✅ | ✅ | ❌ |
| 1.2 File Loading | ❌ | ✅ | ✅ | ✅ | ❌ |
| 2.1-2.5 Schema | ❌ | ✅ | ✅ | ✅ | ❌ |
| 3.1-3.5 Consistency | ❌ | ❌ | ⚠️ | ✅ | ✅ |
| 4.1-4.4 Integrity | ❌ | ❌ | ❌ | ✅ | ⚠️ |
| 5.1-5.4 Dependencies | ❌ | ❌ | ❌ | ✅ | ✅ |
| 6.1-6.3 Progress | ❌ | ❌ | ❌ | ✅ | ✅ |

**Legend:**
- ✅ = Always enforced
- ⚠️ = Warning only
- ❌ = Not checked

---

## Related Documentation

- [Validation System Overview](./VALIDATION_SYSTEM.md) - Architecture and components
- [Best Practices](./BEST_PRACTICES.md) - Recommended workflows
- [Troubleshooting](./TROUBLESHOOTING.md) - Common issues and solutions

---

**Version:** 1.0.0
**Last Updated:** 2025-11-21
**Maintainer:** Vibey Framework Team
