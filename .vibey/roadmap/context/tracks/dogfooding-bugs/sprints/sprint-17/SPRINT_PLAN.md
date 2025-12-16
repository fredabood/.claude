# Sprint 17: Task Start/Edit Command Bugs

**Sprint ID:** 01KCJ5KBC53DKH35F09SZS3W9S
**Track:** CLI Dogfooding Bug Fixes (01KC39XSXJ39N12HWJ93F77KQ9)
**Status:** in_progress
**Tasks:** 3 total, 0 completed

---

## Sprint Overview

This sprint addresses CLI bugs related to ULID handling and activity logging that prevent smooth development workflows.

## Root Cause Analysis

### Activity Logging System Architecture

The roadmap system has **two separate logging mechanisms**:

1. **JSONL Activity Log** (`activity_log/*.jsonl`)
   - Uses `AuditTrailManager.log_change()` under the hood
   - Records field-level changes with old/new values
   - **Does NOT include file hashes**

2. **Pre-commit Verification** (`ChangeVerifier`)
   - Expects `file_hash_before` and `file_hash_after` fields
   - Used by pre-commit hook to verify CLI usage
   - **Cannot find entries because file hashes are missing**

### Data Model Mismatch

Current JSONL entry format:
```json
{
  "timestamp": "2025-12-16T...",
  "object_type": "task",
  "object_id": "01KCMP...",
  "field": "created",
  "old_value": null,
  "new_value": "Sprint: ..., Title: ...",
  "changed_by": "fredabood",
  "reason": "Task created via CLI",
  "commit": "de13816",
  "source": "cli"
}
```

Expected format for verification:
```json
{
  ...
  "file_path": ".vibey/roadmap/tasks/01KCMP....yaml",
  "file_hash_before": null,
  "file_hash_after": "sha256:abc123..."
}
```

---

## Tasks

### Task 1: Fix create-sprint and create-task to log to activity log

**ID:** 01KCJ5N4VCH2F5T9BYW1GXCV2F
**Type:** development
**Complexity:** simple
**Priority:** high

#### Problem Statement
The `create-sprint` and `create-task` CLI commands call `log_task_added()` and `log_sprint_added()`, but these functions log entries without file hashes. The pre-commit hook's `ChangeVerifier` expects file hashes to verify changes.

#### Current Code Analysis
- `vibey/cli/commands.py:455-466` - `create_sprint_cmd` calls `log_sprint_added()`
- `vibey/cli/commands.py:638-649` - `create_task_cmd` calls `log_task_added()`
- `vibey/operations/roadmap/activity_log.py:156-183` - `log_task_added()` implementation
- `vibey/operations/roadmap/activity_log.py:189-216` - `log_sprint_added()` implementation
- `vibey/operations/roadmap/verification.py:65-91` - `ChangeVerifier` expects file hashes

#### Implementation Plan

1. **Extend `AuditTrailManager.log_change()`** to optionally include:
   - `file_path` - path to the YAML file
   - `file_hash_before` - hash before change (null for creates)
   - `file_hash_after` - hash after change

2. **Update `log_task_added()` and `log_sprint_added()`** to:
   - Accept file path parameter
   - Compute file hash after write
   - Include hash in the log entry

3. **Update `create_sprint_cmd` and `create_task_cmd`** to:
   - Pass file path to logging function after saving YAML
   - Ensure logging happens AFTER file save completes

#### Files to Modify
- `vibey/operations/roadmap/audit_trail.py` - Add file hash support
- `vibey/operations/roadmap/activity_log.py` - Update convenience functions
- `vibey/cli/commands.py` - Update CLI commands (lines ~455-466, ~638-649)

#### Acceptance Criteria
- [ ] After `create-sprint`, new sprint YAML file hash is in activity log
- [ ] After `create-task`, new task YAML file hash is in activity log
- [ ] `ChangeVerifier.verify_file()` returns verified=True for newly created files
- [ ] Pre-commit hook passes for commits containing only CLI-created files

---

### Task 2: Fix roadmap edit file command for ULID task IDs

**ID:** 01KCJ5KX221E0PRZ3PD8Q0GVZZ
**Type:** development
**Complexity:** medium
**Priority:** high

#### Problem Statement
The `vibey roadmap edit file` command fails with "Task ID mismatch" error when editing tasks with ULID-based IDs. The validation logic incorrectly compares ID formats.

#### Current Code Analysis
- Need to locate the validation logic in `vibey/cli/commands.py` or `vibey/operations/roadmap/safe_yaml_editor.py`
- The error suggests comparison between task ID in file vs expected format

#### Implementation Plan

1. **Investigate error location** - Search for "Task ID mismatch" error message
2. **Understand ID resolution** - Check how `_resolve_id()` works for tasks
3. **Fix comparison logic** - Ensure ULID→ULID or slug→ULID comparisons work
4. **Add tests** - Create test cases for ULID and slug ID formats

#### Files to Investigate
- `vibey/cli/commands.py` - Edit command implementation
- `vibey/operations/roadmap/safe_yaml_editor.py` - YAML editing logic
- ID resolution functions (`_resolve_id`, `_get_slug_for_ulid`)

#### Acceptance Criteria
- [ ] `vibey roadmap edit file tasks/01KC....yaml --set task.status=completed` works
- [ ] Error message is clear if file not found
- [ ] Both ULID and slug IDs work in edit commands

---

### Task 3: Fix roadmap start command for ULID task IDs

**ID:** 01KCJ5KSDKNFXDKQG1B9RBEGKF
**Type:** development
**Complexity:** medium
**Priority:** high

#### Problem Statement
The `vibey roadmap start` command fails with "Invalid task ID format" when given ULID-based task IDs. The command expects slug format but should accept both slugs and ULIDs.

#### Current Code Analysis
- `vibey roadmap start <task-id>` should accept:
  - Slug: `dogfooding-bugs-17-task-001`
  - ULID: `01KCJ5KSDKNFXDKQG1B9RBEGKF`
- Need to find where ID format validation happens

#### Implementation Plan

1. **Locate start command** - Find `start_cmd` or similar in commands.py
2. **Check ID validation** - Find where "Invalid task ID format" is raised
3. **Update validation** - Accept 26-character ULID format in addition to slugs
4. **Test both formats** - Verify slug and ULID inputs work

#### ULID Format Reference
- 26 characters: `01KC39XSXJ39N12HWJ93F77KQ9`
- Base32 encoding: `0123456789ABCDEFGHJKMNPQRSTVWXYZ`
- Time-sortable, URL-safe

#### Files to Investigate
- `vibey/cli/commands.py` - Start command implementation
- ID resolution functions

#### Acceptance Criteria
- [ ] `vibey roadmap start 01KCJ5KSDKNFXDKQG1B9RBEGKF` works (ULID)
- [ ] `vibey roadmap start dogfooding-bugs-17-task-001` works (slug)
- [ ] Clear error message for invalid IDs
- [ ] Activity log entry created on successful start

---

## Dependencies

None - these tasks are independent and can be worked in any order.

## Testing Strategy

1. **Unit Tests**
   - Test `log_task_added()` produces entries with file hashes
   - Test `_resolve_id()` accepts both ULID and slug formats
   - Test `ChangeVerifier.verify_file()` with new entry format

2. **Integration Tests**
   - Create sprint via CLI, verify activity log entry, verify pre-commit passes
   - Create task via CLI, verify activity log entry, verify pre-commit passes
   - Edit task with ULID, verify changes saved correctly
   - Start task with ULID, verify status change

3. **Manual Testing**
   - Create new sprint, commit without `--no-verify`
   - Create new task, commit without `--no-verify`
   - Edit existing task using ULID ID
   - Start existing task using ULID ID

---

## Notes

- The activity logging system has evolved over time (V1 → V2)
- File hash verification was added for security/auditability
- ULID format is the new standard (ADR-0001), slugs are legacy
