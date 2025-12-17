# Task 10: Add MCP Error Documentation

## Task Metadata
- **ID:** `01KCMGW9859M6C6VPKKHB5BQMR`
- **Sprint:** Sprint 3: MCP/CLI Parity & Integration Tests
- **Priority:** Low
- **Complexity:** Simple
- **Type:** Documentation
- **Estimated Effort:** 2-3 hours

## Objective
Create comprehensive documentation for all MCP error responses, enabling AI agents and developers to handle errors gracefully.

## Current State Analysis

### MCP Error Categories
1. **Validation Errors** - Invalid parameters, missing required fields
2. **Not Found Errors** - Task/sprint/track doesn't exist
3. **State Errors** - Invalid status transitions, blocked items
4. **Permission Errors** - Unauthorized operations
5. **Internal Errors** - Unexpected failures

### Existing Error Handling
- Errors returned in MCP response format
- May lack consistent structure
- Documentation scattered or missing

## Implementation Steps

### Step 1: Audit Current Error Responses
```bash
# Search for error handling in MCP code
grep -r "error" vibey/mcp/ --include="*.py"
grep -r "raise" vibey/mcp/ --include="*.py"
grep -r "Exception" vibey/mcp/ --include="*.py"
```

### Step 2: Create Error Reference Document
**File:** `docs/reference/MCP_ERRORS.md`
```markdown
# MCP Error Reference

This document describes all error responses that MCP tools may return.

## Error Response Format

All errors follow this structure:

\`\`\`json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      // Additional context (optional)
    }
  }
}
\`\`\`

## Error Categories

### Validation Errors (4xx)

#### INVALID_PARAMETER
Returned when a parameter value is invalid.

| Field | Value |
|-------|-------|
| Code | `INVALID_PARAMETER` |
| HTTP Equivalent | 400 Bad Request |

**Example:**
\`\`\`json
{
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "Invalid task ID format: 'abc'. Expected ULID format.",
    "details": {
      "parameter": "task_id",
      "value": "abc",
      "expected": "26-character ULID"
    }
  }
}
\`\`\`

**Resolution:** Ensure parameter values match expected format.

---

#### MISSING_PARAMETER
Returned when a required parameter is not provided.

| Field | Value |
|-------|-------|
| Code | `MISSING_PARAMETER` |
| HTTP Equivalent | 400 Bad Request |

**Example:**
\`\`\`json
{
  "error": {
    "code": "MISSING_PARAMETER",
    "message": "Missing required parameter: item_id",
    "details": {
      "parameter": "item_id",
      "required": true
    }
  }
}
\`\`\`

**Resolution:** Provide all required parameters.

---

### Not Found Errors (404)

#### TASK_NOT_FOUND
Returned when referenced task doesn't exist.

| Field | Value |
|-------|-------|
| Code | `TASK_NOT_FOUND` |
| HTTP Equivalent | 404 Not Found |

**Example:**
\`\`\`json
{
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "Task '01KCXYZ...' not found",
    "details": {
      "task_id": "01KCXYZ...",
      "suggestion": "Use vibey_roadmap_list_tasks to find valid task IDs"
    }
  }
}
\`\`\`

**Resolution:** Verify task ID exists using `vibey_roadmap_list_tasks`.

---

#### SPRINT_NOT_FOUND
Returned when referenced sprint doesn't exist.

| Field | Value |
|-------|-------|
| Code | `SPRINT_NOT_FOUND` |
| HTTP Equivalent | 404 Not Found |

**Example:**
\`\`\`json
{
  "error": {
    "code": "SPRINT_NOT_FOUND",
    "message": "Sprint '01KCXYZ...' not found",
    "details": {
      "sprint_id": "01KCXYZ..."
    }
  }
}
\`\`\`

---

#### TRACK_NOT_FOUND
Returned when referenced track doesn't exist.

| Field | Value |
|-------|-------|
| Code | `TRACK_NOT_FOUND` |
| HTTP Equivalent | 404 Not Found |

---

### State Errors (409)

#### INVALID_STATUS_TRANSITION
Returned when status transition is not allowed.

| Field | Value |
|-------|-------|
| Code | `INVALID_STATUS_TRANSITION` |
| HTTP Equivalent | 409 Conflict |

**Example:**
\`\`\`json
{
  "error": {
    "code": "INVALID_STATUS_TRANSITION",
    "message": "Cannot transition from 'not_started' to 'completed'. Must be 'in_progress' first.",
    "details": {
      "current_status": "not_started",
      "requested_status": "completed",
      "valid_transitions": ["in_progress"]
    }
  }
}
\`\`\`

**Resolution:** Follow valid status progression: not_started → in_progress → completed

---

#### TASK_BLOCKED
Returned when task is blocked by dependencies.

| Field | Value |
|-------|-------|
| Code | `TASK_BLOCKED` |
| HTTP Equivalent | 409 Conflict |

**Example:**
\`\`\`json
{
  "error": {
    "code": "TASK_BLOCKED",
    "message": "Task '01KC...' is blocked",
    "details": {
      "blocked_by": ["01KCABC...", "01KCDEF..."],
      "reason": "Dependent tasks not completed"
    }
  }
}
\`\`\`

**Resolution:** Complete blocking tasks first.

---

#### MISSING_COMMITS
Returned when trying to complete task without commits.

| Field | Value |
|-------|-------|
| Code | `MISSING_COMMITS` |
| HTTP Equivalent | 409 Conflict |

**Example:**
\`\`\`json
{
  "error": {
    "code": "MISSING_COMMITS",
    "message": "Cannot complete task: no commits linked",
    "details": {
      "task_id": "01KC...",
      "suggestion": "Add commits with vibey_roadmap_add_commit or use --no-commits flag"
    }
  }
}
\`\`\`

---

### Internal Errors (500)

#### INTERNAL_ERROR
Returned for unexpected server errors.

| Field | Value |
|-------|-------|
| Code | `INTERNAL_ERROR` |
| HTTP Equivalent | 500 Internal Server Error |

**Example:**
\`\`\`json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An unexpected error occurred",
    "details": {
      "request_id": "abc123"
    }
  }
}
\`\`\`

**Resolution:** Report issue with request_id if persistent.

---

#### DATABASE_ERROR
Returned for database-related failures.

| Field | Value |
|-------|-------|
| Code | `DATABASE_ERROR` |
| HTTP Equivalent | 500 Internal Server Error |

**Example:**
\`\`\`json
{
  "error": {
    "code": "DATABASE_ERROR",
    "message": "Database operation failed",
    "details": {
      "suggestion": "Try vibey_roadmap_db_rebuild to repair database"
    }
  }
}
\`\`\`

---

## Error Handling Best Practices

### For AI Agents

1. **Check error code first** - Use code for programmatic handling
2. **Read message for context** - Human-readable explanation
3. **Use details for recovery** - Contains actionable information
4. **Implement retry logic** - For transient errors
5. **Fall back gracefully** - Show user-friendly message

### Example Error Handler
\`\`\`python
async def handle_mcp_response(response):
    if "error" in response:
        error = response["error"]
        code = error.get("code")

        if code == "TASK_NOT_FOUND":
            # Suggest listing tasks
            return await call_tool("vibey_roadmap_list_tasks", {})

        elif code == "INVALID_STATUS_TRANSITION":
            # Check current status and adjust
            details = error.get("details", {})
            valid = details.get("valid_transitions", [])
            # ...

        elif code == "MISSING_COMMITS":
            # Prompt user to add commits or use flag
            pass

        else:
            # Generic error handling
            raise MCPError(error["message"])

    return response
\`\`\`

## Complete Error Code Reference

| Code | Category | Description |
|------|----------|-------------|
| `INVALID_PARAMETER` | Validation | Parameter value invalid |
| `MISSING_PARAMETER` | Validation | Required parameter missing |
| `TASK_NOT_FOUND` | Not Found | Task doesn't exist |
| `SPRINT_NOT_FOUND` | Not Found | Sprint doesn't exist |
| `TRACK_NOT_FOUND` | Not Found | Track doesn't exist |
| `INVALID_STATUS_TRANSITION` | State | Status change not allowed |
| `TASK_BLOCKED` | State | Task blocked by dependencies |
| `MISSING_COMMITS` | State | Task has no commits |
| `INTERNAL_ERROR` | Internal | Unexpected error |
| `DATABASE_ERROR` | Internal | Database failure |
```

### Step 3: Add Error Examples to Each Tool
Update `docs/reference/MCP_REFERENCE.md` to include error examples for each tool.

### Step 4: Create Error Code Constants
**File:** `vibey/mcp/errors.py`
```python
"""MCP error codes and utilities."""

class ErrorCode:
    # Validation errors
    INVALID_PARAMETER = "INVALID_PARAMETER"
    MISSING_PARAMETER = "MISSING_PARAMETER"

    # Not found errors
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    SPRINT_NOT_FOUND = "SPRINT_NOT_FOUND"
    TRACK_NOT_FOUND = "TRACK_NOT_FOUND"

    # State errors
    INVALID_STATUS_TRANSITION = "INVALID_STATUS_TRANSITION"
    TASK_BLOCKED = "TASK_BLOCKED"
    MISSING_COMMITS = "MISSING_COMMITS"

    # Internal errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"


def create_error_response(code: str, message: str, details: dict = None) -> dict:
    """Create standardized error response."""
    error = {
        "code": code,
        "message": message,
    }
    if details:
        error["details"] = details
    return {"error": error}
```

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `docs/reference/MCP_ERRORS.md` | Create | Main error reference |
| `docs/reference/MCP_REFERENCE.md` | Modify | Add error examples |
| `vibey/mcp/errors.py` | Create | Error code constants |

## Acceptance Criteria

- [ ] All error types documented
- [ ] Each error has code, message format, example
- [ ] Resolution steps provided for each error
- [ ] Error handling best practices documented
- [ ] Error codes defined in code constants
- [ ] MCP_REFERENCE.md updated with error examples

## Dependencies
None (documentation only)

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Error responses change | Keep docs in sync with code |
| Incomplete coverage | Audit error paths systematically |
