# Reporting and Status

> **Time Required:** 10 minutes
> **Difficulty:** Beginner
> **Prerequisites:** Vibey installed, active roadmap

---

## Overview

This walkthrough covers generating reports, viewing status, and exporting roadmap data.

---

## Status Commands

### Overall Status

```bash
vibey roadmap status
```

Shows:
- Total tracks, sprints, tasks
- Items by status (not_started, in_progress, completed)
- Progress percentages

### Filtered Status

```bash
# Only in-progress items
vibey roadmap status --filter in_progress

# Only completed items
vibey roadmap status --filter completed
```

### Item Details

```bash
# Show any item details by ID
vibey roadmap show <id>
```

Works for tracks, sprints, and tasks - pass the ULID.

---

## Activity and History

### View Activity Log

```bash
# Recent activity
vibey roadmap activity --limit 10

# Today's activity
vibey roadmap activity --since today

# Activity for specific track
vibey roadmap activity --track <track-id>
```

### View History

```bash
# History of changes
vibey roadmap history

# History for specific item
vibey roadmap history --id <item-id>
```

---

## Generating Reports

### Summary Report

```bash
vibey roadmap summarize
```

Generates a human-readable summary of the roadmap.

### Export to File

```bash
vibey roadmap summarize --output summary.md
```

Saves the summary to a markdown file.

---

## Data Export

### Export Formats

```bash
# List available export formats
vibey export list
```

### Export to JSON

```bash
vibey roadmap export --format json > roadmap.json
```

### Export Statistics

```bash
vibey export stats
```

Shows export-related statistics.

### Export to Gemini Format

For Google Gemini integration:

```bash
vibey export gemini
```

### Run Custom Export

```bash
vibey export run --format <format>
```

---

## Field Queries

### Get Specific Field

```bash
# Get a specific field value
vibey roadmap get-field <item-id> --field status
vibey roadmap get-field <item-id> --field progress
```

Useful for scripting and automation.

---

## Progress Tracking

### View Track Progress

```bash
vibey roadmap show <track-id>
```

Shows:
- Sprints in the track
- Completion percentage
- Tasks remaining

### View Sprint Progress

```bash
vibey roadmap show <sprint-id>
```

Shows:
- Tasks in the sprint
- Task status breakdown
- Completion percentage

---

## Viewing Items

### View All Items

```bash
# Show all tracks with status
vibey roadmap status
```

### View Specific Items

```bash
# Show track with its sprints
vibey roadmap show <track-id>

# Show sprint with its tasks
vibey roadmap show <sprint-id>

# Show task details
vibey roadmap show <task-id>
```

Use `vibey roadmap status` to find item IDs, then `show` for details.

---

## Command Reference

### Status Commands
```bash
vibey roadmap status                    # Overall status
vibey roadmap status --filter <status>  # Filtered status
vibey roadmap show <id>                 # Item details
vibey roadmap get-field <id> --field x  # Get specific field
```

### Activity and History
```bash
vibey roadmap activity --limit <n>      # Recent activity
vibey roadmap activity --since <date>   # Activity since date
vibey roadmap history                   # Change history
vibey roadmap history --id <id>         # Item history
```

### Reports and Export
```bash
vibey roadmap summarize                 # Generate summary
vibey roadmap summarize --output <file> # Save summary
vibey roadmap export --format json      # Export to JSON
vibey export list                       # List export formats
vibey export run --format <format>      # Run export
vibey export stats                      # Export statistics
vibey export gemini                     # Export for Gemini
```

### Viewing Items
```bash
vibey roadmap status                    # All items overview
vibey roadmap show <id>                 # Details for specific item
```

---

## MCP Integration

AI assistants can query roadmap status via MCP:

### Status Tools

| MCP Tool | Purpose |
|----------|---------|
| `roadmap_status` | Get overall roadmap status |
| `task_query` | Query specific task details |
| `vibey_query_track` | Query track details |

### Example: Get Status via MCP

```json
{
  "tool": "roadmap_status",
  "arguments": {}
}
```

Returns tracks, sprints, tasks counts and progress.

---

## See Also

- [Daily Workflow](./DAILY_WORKFLOW.md) - Task management cycle
- [Roadmap Management](./ROADMAP_MANAGEMENT.md) - Creating items
- [CLI Reference](../reference/CLI_REFERENCE.md) - All commands
