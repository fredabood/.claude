# MCP Workflow Examples

This guide provides step-by-step workflows for common tasks using Vibey MCP tools.

## Overview

Each workflow shows:
- **Goal**: What the workflow accomplishes
- **Tools Used**: MCP tools in the sequence
- **Step-by-Step**: Tool calls with inputs/outputs
- **Error Handling**: Common errors and recovery

---

## Workflow 1: Daily Development Workflow

### Goal
Start work on a task, make progress, and complete it.

### Tools Used
1. `vibey_roadmap_status` - Check overall progress
2. `vibey_roadmap_list_tasks` - Find available tasks
3. `vibey_roadmap_start` - Start working on task
4. `vibey_roadmap_show` - Get task details
5. `vibey_roadmap_complete` - Mark task done

### Step-by-Step

#### Step 1: Check Current Status
```json
// Request
{
  "tool": "vibey_roadmap_status",
  "arguments": {}
}

// Response
{
  "tracks": 47,
  "active_track": {
    "name": "Test Suite Rehabilitation",
    "progress": "62%"
  },
  "active_sprint": {
    "name": "Sprint 3: MCP/CLI Parity",
    "tasks_remaining": 7
  }
}
```

#### Step 2: List Available Tasks
```json
// Request
{
  "tool": "vibey_roadmap_list_tasks",
  "arguments": {
    "sprint_id": "01KCMTMZQF4CD2GCV1GCJB8KKE",
    "status": "not_started"
  }
}

// Response
{
  "tasks": [
    {"id": "01KCMGW1PRG8ADMD0M4Q83PYQC", "title": "Add MCP tool unit tests"},
    {"id": "01KCMGW5F2CF5XNFPWBGF9YZH0", "title": "Add MCP server integration tests"}
  ]
}
```

#### Step 3: Start a Task
```json
// Request
{
  "tool": "vibey_roadmap_start",
  "arguments": {
    "item_id": "01KCMGW1PRG8ADMD0M4Q83PYQC"
  }
}

// Response
{
  "success": true,
  "message": "Task 'Add MCP tool unit tests' marked as in progress"
}
```

#### Step 4: Get Task Details
```json
// Request
{
  "tool": "vibey_roadmap_show",
  "arguments": {
    "item_id": "01KCMGW1PRG8ADMD0M4Q83PYQC"
  }
}

// Response
{
  "type": "task",
  "id": "01KCMGW1PRG8ADMD0M4Q83PYQC",
  "title": "Add MCP tool unit tests",
  "description": "Create comprehensive tests...",
  "status": "in_progress",
  "context_files": [
    ".vibey/roadmap/context/tracks/.../TASK_5_MCP_TOOL_UNIT_TESTS.md"
  ]
}
```

#### Step 5: Complete the Task
```json
// Request
{
  "tool": "vibey_roadmap_complete",
  "arguments": {
    "item_id": "01KCMGW1PRG8ADMD0M4Q83PYQC"
  }
}

// Response
{
  "success": true,
  "message": "Task 'Add MCP tool unit tests' marked as completed"
}
```

### Error Handling
- **TASK_NOT_FOUND**: Use `vibey_roadmap_list_tasks` to find valid IDs
- **MISSING_COMMITS**: Add commits before completing
- **INVALID_STATUS_TRANSITION**: Check current status first

---

## Workflow 2: Sprint Planning

### Goal
Create a new sprint with tasks for upcoming work.

### Tools Used
1. `vibey_roadmap_list_tracks` - Find target track
2. `vibey_roadmap_create_sprint` - Create sprint
3. `vibey_roadmap_create_task` - Add tasks
4. `vibey_roadmap_show` - Verify sprint

### Step-by-Step

#### Step 1: Find Target Track
```json
// Request
{
  "tool": "vibey_roadmap_list_tracks",
  "arguments": {
    "status": "in_progress"
  }
}

// Response
{
  "tracks": [
    {"id": "01KCMTJKFKDJX7BWERZJ7SFJ96", "name": "Test Suite Rehabilitation"},
    {"id": "01KC39XSXJ39N12HWJ93F77KQ9", "name": "Dogfooding Bugs"}
  ]
}
```

#### Step 2: Create Sprint
```json
// Request
{
  "tool": "vibey_roadmap_create_sprint",
  "arguments": {
    "track_id": "01KCMTJKFKDJX7BWERZJ7SFJ96",
    "name": "Sprint 4: Performance Optimization",
    "goal": "Improve response times by 50%"
  }
}

// Response
{
  "success": true,
  "sprint_id": "01KCNEW...",
  "message": "Sprint created successfully"
}
```

#### Step 3: Add Tasks
```json
// Request (repeat for each task)
{
  "tool": "vibey_roadmap_create_task",
  "arguments": {
    "sprint_id": "01KCNEW...",
    "title": "Profile slow database queries",
    "description": "Use SQLite EXPLAIN to identify slow queries",
    "priority": "high"
  }
}

// Response
{
  "success": true,
  "task_id": "01KCNEW...",
  "message": "Task created successfully"
}
```

#### Step 4: Verify Sprint
```json
// Request
{
  "tool": "vibey_roadmap_show",
  "arguments": {
    "item_id": "01KCNEW..."
  }
}

// Response
{
  "type": "sprint",
  "id": "01KCNEW...",
  "name": "Sprint 4: Performance Optimization",
  "tasks": 3,
  "status": "not_started"
}
```

---

## Workflow 3: Status Reporting

### Goal
Generate a comprehensive status report for stakeholders.

### Tools Used
1. `vibey_roadmap_status` - Overall status
2. `vibey_roadmap_list_tracks` - All tracks
3. `vibey_roadmap_list_sprints` - Sprint details
4. `vibey_roadmap_list_tasks` - Task breakdown

### Step-by-Step

#### Step 1: Get High-Level Status
```json
{
  "tool": "vibey_roadmap_status",
  "arguments": {}
}

// Response
{
  "roadmap": "vibey-framework-v2",
  "tracks": {
    "total": 47,
    "completed": 22,
    "in_progress": 2
  },
  "active_sprint": {
    "name": "Sprint 3: MCP/CLI Parity",
    "progress": "64%"
  }
}
```

#### Step 2: Get Active Sprints
```json
{
  "tool": "vibey_roadmap_list_sprints",
  "arguments": {
    "status": "in_progress"
  }
}

// Response
{
  "sprints": [
    {
      "id": "01KCMTMZQF4CD2GCV1GCJB8KKE",
      "name": "Sprint 3: MCP/CLI Parity",
      "track": "Test Suite Rehabilitation",
      "tasks_completed": 7,
      "tasks_total": 11
    }
  ]
}
```

#### Step 3: Get Task Breakdown
```json
{
  "tool": "vibey_roadmap_list_tasks",
  "arguments": {
    "sprint_id": "01KCMTMZQF4CD2GCV1GCJB8KKE",
    "include_completed": true
  }
}

// Response
{
  "tasks": [
    {"id": "...", "title": "Task 1", "status": "completed"},
    {"id": "...", "title": "Task 2", "status": "completed"},
    {"id": "...", "title": "Task 3", "status": "in_progress"}
  ]
}
```

### Sample Report Output
```markdown
# Roadmap Status Report

## Summary
- **Total Tracks:** 47
- **Completed:** 22 (47%)
- **In Progress:** 2

## Active Work

### Test Suite Rehabilitation (62%)
- Sprint 3: MCP/CLI Parity & Integration Tests
- Tasks: 7/11 completed
- Focus: Test coverage and CI enforcement
```

---

## Workflow 4: Deployment

### Goal
Deploy configuration to a target platform.

### Tools Used
1. `vibey_deploy_list` - Available platforms
2. `vibey_deploy_status` - Check current state
3. `vibey_deploy` - Execute deployment

### Step-by-Step

#### Step 1: List Available Platforms
```json
{
  "tool": "vibey_deploy_list",
  "arguments": {}
}

// Response
{
  "platforms": [
    {"name": "claude-code", "description": "Claude Code CLI"},
    {"name": "cursor", "description": "Cursor IDE"},
    {"name": "copilot", "description": "GitHub Copilot"},
    {"name": "vscode", "description": "VS Code"},
    {"name": "goose", "description": "Goose AI"}
  ]
}
```

#### Step 2: Check Deployment Status
```json
{
  "tool": "vibey_deploy_status",
  "arguments": {
    "platform": "cursor"
  }
}

// Response
{
  "platform": "cursor",
  "deployed": false,
  "last_deploy": null
}
```

#### Step 3: Deploy (Dry Run First)
```json
{
  "tool": "vibey_deploy",
  "arguments": {
    "platform": "cursor",
    "dry_run": true
  }
}

// Response
{
  "dry_run": true,
  "files": [
    ".cursor/rules",
    ".cursor/mcp.json"
  ]
}
```

#### Step 4: Execute Deployment
```json
{
  "tool": "vibey_deploy",
  "arguments": {
    "platform": "cursor",
    "force": false
  }
}

// Response
{
  "success": true,
  "files_written": 2,
  "message": "Deployed to cursor successfully"
}
```

---

## Workflow 5: Documentation Generation

### Goal
Generate and verify documentation is up to date.

### Tools Used
1. `vibey_docs_generate_cli` - Generate CLI reference
2. `vibey_docs_generate_mcp` - Generate MCP reference
3. `vibey_docs_check_drift` - Verify no drift

### Step-by-Step

#### Step 1: Generate CLI Reference
```json
{
  "tool": "vibey_docs_generate_cli",
  "arguments": {
    "output": "docs/reference/CLI_REFERENCE.md"
  }
}

// Response
{
  "success": true,
  "path": "docs/reference/CLI_REFERENCE.md",
  "commands_documented": 169
}
```

#### Step 2: Generate MCP Reference
```json
{
  "tool": "vibey_docs_generate_mcp",
  "arguments": {
    "output": "docs/reference/MCP_REFERENCE.md"
  }
}

// Response
{
  "success": true,
  "path": "docs/reference/MCP_REFERENCE.md",
  "tools_documented": 76
}
```

#### Step 3: Check for Drift
```json
{
  "tool": "vibey_docs_check_drift",
  "arguments": {}
}

// Response (success)
{
  "drift_detected": false,
  "message": "Documentation is up to date"
}

// Response (drift found)
{
  "drift_detected": true,
  "drift_items": [
    "CLI command 'roadmap verify' missing from docs",
    "MCP tool 'vibey_deploy_rollback' not documented"
  ]
}
```

---

## Best Practices for AI Agents

### 1. Always Check Status First
Before starting work, get current context with `vibey_roadmap_status`.

### 2. Use List Tools for Discovery
Don't assume IDs - use list tools to find valid identifiers.

### 3. Handle Errors Gracefully
Check for error responses and use recovery strategies. See [MCP_ERRORS.md](../reference/MCP_ERRORS.md).

### 4. Follow Status Transitions
Tasks: not_started -> in_progress -> completed

### 5. Read Task Context Files
Use `vibey_roadmap_show` to get context file paths for detailed plans.

### 6. Dry Run Before Deployment
Always use `dry_run: true` first for deploy operations.

### 7. Verify After Changes
After creating or modifying items, use `vibey_roadmap_show` to verify.

---

## Quick Reference

| Workflow | Key Tools |
|----------|-----------|
| Daily Development | status, list_tasks, start, complete |
| Sprint Planning | list_tracks, create_sprint, create_task |
| Status Reporting | status, list_tracks, list_sprints |
| Deployment | deploy_list, deploy_status, deploy |
| Documentation | docs_generate_cli, docs_generate_mcp, docs_check_drift |

---

## Related Documentation

- [MCP Reference](../reference/MCP_REFERENCE.md) - Complete tool documentation
- [MCP Errors](../reference/MCP_ERRORS.md) - Error handling guide
- [CLI Reference](../reference/CLI_REFERENCE.md) - CLI equivalent commands
