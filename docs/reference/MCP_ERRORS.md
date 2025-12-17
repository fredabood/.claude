# MCP Error Reference

This document describes all error responses that MCP tools may return.

---

## Error Response Format

All errors follow this structure:

```json
{
  "isError": true,
  "content": [
    {
      "type": "text",
      "text": "Error message here"
    }
  ]
}
```

For structured errors, the text content may include JSON:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      // Additional context (optional)
    }
  }
}
```

---

## Error Categories

### Validation Errors (4xx)

#### INVALID_PARAMETER
Returned when a parameter value is invalid.

| Field | Value |
|-------|-------|
| Code | `INVALID_PARAMETER` |
| HTTP Equivalent | 400 Bad Request |

**Example:**
```json
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
```

**Resolution:** Ensure parameter values match expected format.

---

#### MISSING_PARAMETER
Returned when a required parameter is not provided.

| Field | Value |
|-------|-------|
| Code | `MISSING_PARAMETER` |
| HTTP Equivalent | 400 Bad Request |

**Example:**
```json
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
```

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
```json
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
```

**Resolution:** Verify task ID exists using `vibey_roadmap_list_tasks`.

---

#### SPRINT_NOT_FOUND
Returned when referenced sprint doesn't exist.

| Field | Value |
|-------|-------|
| Code | `SPRINT_NOT_FOUND` |
| HTTP Equivalent | 404 Not Found |

**Example:**
```json
{
  "error": {
    "code": "SPRINT_NOT_FOUND",
    "message": "Sprint '01KCXYZ...' not found",
    "details": {
      "sprint_id": "01KCXYZ..."
    }
  }
}
```

**Resolution:** Verify sprint ID exists using `vibey_roadmap_list_sprints`.

---

#### TRACK_NOT_FOUND
Returned when referenced track doesn't exist.

| Field | Value |
|-------|-------|
| Code | `TRACK_NOT_FOUND` |
| HTTP Equivalent | 404 Not Found |

**Resolution:** Verify track ID exists using `vibey_roadmap_list_tracks`.

---

### State Errors (409)

#### INVALID_STATUS_TRANSITION
Returned when status transition is not allowed.

| Field | Value |
|-------|-------|
| Code | `INVALID_STATUS_TRANSITION` |
| HTTP Equivalent | 409 Conflict |

**Example:**
```json
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
```

**Resolution:** Follow valid status progression: not_started -> in_progress -> completed

---

#### TASK_BLOCKED
Returned when task is blocked by dependencies.

| Field | Value |
|-------|-------|
| Code | `TASK_BLOCKED` |
| HTTP Equivalent | 409 Conflict |

**Example:**
```json
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
```

**Resolution:** Complete blocking tasks first.

---

#### MISSING_COMMITS
Returned when trying to complete task without commits.

| Field | Value |
|-------|-------|
| Code | `MISSING_COMMITS` |
| HTTP Equivalent | 409 Conflict |

**Example:**
```json
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
```

**Resolution:** Add commits with `vibey_roadmap_add_commit` or mark as non-code task.

---

### Internal Errors (500)

#### INTERNAL_ERROR
Returned for unexpected server errors.

| Field | Value |
|-------|-------|
| Code | `INTERNAL_ERROR` |
| HTTP Equivalent | 500 Internal Server Error |

**Example:**
```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An unexpected error occurred",
    "details": {
      "request_id": "abc123"
    }
  }
}
```

**Resolution:** Report issue with request_id if persistent.

---

#### DATABASE_ERROR
Returned for database-related failures.

| Field | Value |
|-------|-------|
| Code | `DATABASE_ERROR` |
| HTTP Equivalent | 500 Internal Server Error |

**Example:**
```json
{
  "error": {
    "code": "DATABASE_ERROR",
    "message": "Database operation failed",
    "details": {
      "suggestion": "Try vibey_roadmap_db_rebuild to repair database"
    }
  }
}
```

**Resolution:** Run `vibey roadmap db rebuild` to repair the database.

---

#### UNKNOWN_TOOL
Returned when the requested tool name doesn't exist.

| Field | Value |
|-------|-------|
| Code | `UNKNOWN_TOOL` |
| HTTP Equivalent | 404 Not Found |

**Example:**
```json
{
  "isError": true,
  "content": [
    {
      "type": "text",
      "text": "Unknown tool: nonexistent_tool"
    }
  ]
}
```

**Resolution:** Use a valid tool name from the MCP tools list.

---

## Error Handling Best Practices

### For AI Agents

1. **Check isError first** - Determine if response is an error
2. **Parse error content** - Extract error message from content
3. **Use suggestions** - Error details often include recovery suggestions
4. **Implement retry logic** - For transient errors
5. **Fall back gracefully** - Show user-friendly message

### Example Error Handler

```python
async def handle_mcp_response(response):
    if response.get("isError"):
        content = response.get("content", [])
        error_text = content[0].get("text", "") if content else "Unknown error"

        # Check for specific error patterns
        if "not found" in error_text.lower():
            # Suggest listing items
            return await call_tool("vibey_roadmap_status", {})

        elif "INVALID_STATUS_TRANSITION" in error_text:
            # Check current status and adjust
            pass

        elif "MISSING_COMMITS" in error_text:
            # Prompt user to add commits
            pass

        else:
            # Generic error handling
            raise MCPError(error_text)

    return response
```

---

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
| `UNKNOWN_TOOL` | Internal | Tool name not recognized |

---

## Recovery Strategies by Error Type

### Validation Errors
- Re-read tool schema for parameter requirements
- Verify ID formats (ULIDs are 26 characters)
- Check parameter types match expected types

### Not Found Errors
- Use list tools to find valid IDs:
  - `vibey_roadmap_list_tracks`
  - `vibey_roadmap_list_sprints`
  - `vibey_roadmap_list_tasks`

### State Errors
- Check current item status with `vibey_roadmap_show`
- Follow status progression rules
- Complete blocking items first

### Internal Errors
- Retry operation after brief delay
- Run `vibey roadmap db rebuild` for database issues
- Check system logs for persistent failures

---

*This documentation is maintained alongside MCP tool implementations.*
