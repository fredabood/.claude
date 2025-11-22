# Documentation Management System

The Vibey Framework includes a comprehensive documentation management system that synchronizes documentation between the roadmap source of truth (`.vibey/roadmap/`) and user-facing documentation (`docs/roadmap/`).

## Overview

The system provides:

1. **Hierarchical Documentation Storage** - Context files stored alongside roadmap objects
2. **Automatic Synchronization** - Sync docs on task/sprint completion
3. **Documentation Tracking** - Track which roadmap objects impact which docs
4. **Changelog Generation** - Generate doc changelogs from impacts

## CLI Commands

### Sync Documentation

Synchronize documentation from `.vibey/roadmap/` to `docs/roadmap/`:

```bash
# Sync all documentation
vibey roadmap sync-docs --all

# Sync specific track
vibey roadmap sync-docs --track my-track

# Preview changes without syncing
vibey roadmap sync-docs --dry-run

# Delete orphaned files
vibey roadmap sync-docs --delete-orphaned

# Sync only completion summaries
vibey roadmap sync-docs --summaries-only
```

### Add Context Files

Add context files (research, analysis, notes) to roadmap objects:

```bash
# Add context to a track
vibey roadmap add-context design.md --track my-track

# Add context to a sprint
vibey roadmap add-context analysis.md --sprint my-track-1

# Add context to a task
vibey roadmap add-context notes.md --task my-track-1-task-003
```

Context files are stored in `/context/` subdirectories alongside roadmap objects.

### Link Documentation

Track which roadmap objects impact which documentation files:

```bash
# Link a doc to a roadmap object
vibey roadmap link-doc docs/API.md feature-1-task-003 -t added_section -s "Authentication"

# Link with description
vibey roadmap link-doc README.md infrastructure-fixes -t updated -d "Updated install steps"
```

Change types:
- `created` - New documentation file
- `added_section` - Added new section to existing doc
- `updated` - Updated existing content
- `refactored` - Restructured documentation
- `removed` - Removed content
- `fixed` - Fixed errors in documentation

### List Tracked Documents

List all tracked documentation files:

```bash
# List all tracked docs
vibey roadmap list-docs

# Filter to docs linked to a specific object
vibey roadmap list-docs --object my-track-1-task-003
```

### Generate Changelog

Generate a documentation changelog:

```bash
# Full changelog (grouped by object)
vibey roadmap doc-changelog

# Filter to specific roadmap object
vibey roadmap doc-changelog --object feature-1

# Group by date instead of object
vibey roadmap doc-changelog --group-by time

# Write to file
vibey roadmap doc-changelog -o CHANGELOG.md

# Filter by date range
vibey roadmap doc-changelog --start-date 2025-01-01 --end-date 2025-01-31
```

## Automatic Synchronization

Documentation can be automatically synchronized on roadmap events:

- `task_complete` - When a task is marked complete
- `sprint_complete` - When a sprint is marked complete
- `track_complete` - When a track is marked complete
- `context_add` - When a context file is added

Configure in `.vibey/config/project.yaml`:

```yaml
documentation:
  sync:
    enabled: true
    source_dir: ".vibey/roadmap"
    target_dir: "docs/roadmap"
    delete_orphaned: false
    auto_sync_on:
      - sprint_complete
      - track_complete
```

## Directory Structure

```
.vibey/roadmap/
  my-track/
    track.yaml           # Track definition
    context/             # Track-level context files
      design.md
    my-track-1/
      sprint.yaml        # Sprint definition
      context/           # Sprint-level context files
        research.md
      my-track-1-task-001/
        task.yaml        # Task definition
        context/         # Task-level context files
          notes.md

docs/roadmap/            # Synchronized documentation
  my-track/
    track.md             # Synced track docs
    my-track-1/
      sprint.md          # Synced sprint docs
```

## Metadata Files

Documentation impacts are tracked in `.meta.json` sidecar files:

```json
{
  "doc_path": "docs/API.md",
  "title": "API Documentation",
  "created": "2025-01-01T00:00:00Z",
  "last_modified": "2025-01-15T12:00:00Z",
  "impacts": [
    {
      "roadmap_object_id": "feature-1-task-003",
      "roadmap_object_type": "task",
      "change_type": "added_section",
      "section": "Authentication",
      "description": "Added OAuth2 authentication docs",
      "timestamp": "2025-01-15T12:00:00Z"
    }
  ]
}
```

## Best Practices

1. **Add Context Early** - Add research and design docs as context files during planning
2. **Link Docs Consistently** - Link documentation changes to the task that made them
3. **Use Descriptive Change Types** - Be specific about what kind of change was made
4. **Sync on Sprint Complete** - Run sync at sprint boundaries to keep docs current
5. **Review Changelogs** - Use changelogs in sprint retrospectives

## Integration with Roadmap Workflow

1. **During Task Work**
   - Add research/analysis to task context
   - Link any docs you update to the task

2. **On Task Complete**
   - Documentation automatically syncs (if configured)
   - Impact is recorded in .meta.json

3. **On Sprint Complete**
   - Run `vibey roadmap sync-docs` to ensure all docs synced
   - Generate changelog for sprint review

4. **For Documentation Audits**
   - Use `list-docs` to see all tracked documentation
   - Use `doc-changelog` to review recent changes
