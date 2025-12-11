# Platform Compatibility Track Refactor Plan

## Overview

Refactor 13 separate platform port tracks into a single **Platform Compatibility** track with one sprint per platform.

## Current State Analysis

### 13 Platform Port Tracks

| # | Platform | Track ID | Priority | Sprints | Tasks | Done | Progress |
|---|----------|----------|----------|---------|-------|------|----------|
| 1 | Aider | 01KC2D0JK06MN77ZHAGAHF5VKB | high | 1 | 10 | 8 | 80% |
| 2 | Amazon Q | 01KC2D0JK06MN77ZHAGAHF5VKN | medium | 2 | 14 | 5 | 36% |
| 3 | Claude Code | 01KC2D0JK1877YN6T0673VB24T | critical | 1 | 10 | 8 | 80% |
| 4 | Continue.dev | 01KC2D0JK1877YN6T0673VB25H | high | 2 | 14 | 7 | 50% |
| 5 | Cursor | 01KC2D0JK2A3KNMQVJDACN1X9M | high | 2 | 14 | 5 | 36% |
| 6 | Gemini | 01KC2D0JK5Y3BX5008PVANFCHN | high | 6 | 34 | 22 | 65% |
| 7 | GitHub Copilot | 01KC2D0JK1877YN6T0673VB260 | high | 2 | 16 | 5 | 31% |
| 8 | Goose | 01KC2D0JK7READW9KAK1HBX4BS | critical | 5 | 36 | 34 | 94% |
| 9 | JetBrains | 01KC2D0JK9JKQXGQW6MQEB0JZP | medium | 2 | 14 | 12 | 86% |
| 10 | Replit | 01KC2D0JKCJCWQ76VRQJWBGQY9 | medium | 6 | 38 | 4 | 11% |
| 11 | Cody | 01KC2D0JK1877YN6T0673VB254 | low | 2 | 12 | 6 | 50% |
| 12 | VS Code MCP | 01KC2D0JKWWW8WMS7PPGDQ42GY | high | 2 | 12 | 4 | 33% |
| 13 | Windsurf | 01KC2D0JKY8WC5NT15KN5SW9YE | high | 2 | 15 | 7 | 47% |

**Totals:**
- 13 tracks
- 35 sprints
- 239 tasks
- 127 completed (53%)

### Common Task Patterns Identified

1. **Adapter Implementation** - Create `{Platform}Adapter` class
2. **MCP Configuration** - Platform-specific MCP setup
3. **Unit Tests** - Write unit tests for adapter
4. **Integration Tests** - E2E testing with platform
5. **Documentation** - Integration guide, migration guide
6. **CLI Command** - `vibey deploy --platform {name}`
7. **Quality Gates** - Validation and sign-off

---

## Proposed Structure

### New Track: Platform Compatibility

```
Track: Platform Compatibility
ID: (new ULID)
Priority: critical
Status: in_progress

Sprints (13 total - one per platform):
├── Sprint 01: Claude Code Validation (reference implementation)
├── Sprint 02: Goose Integration
├── Sprint 03: Cursor Integration
├── Sprint 04: VS Code MCP Integration
├── Sprint 05: GitHub Copilot Integration
├── Sprint 06: Continue.dev Integration
├── Sprint 07: Aider Integration
├── Sprint 08: JetBrains Integration
├── Sprint 09: Windsurf/Codeium Integration
├── Sprint 10: Gemini Integration
├── Sprint 11: Amazon Q Integration
├── Sprint 12: Sourcegraph Cody Integration
└── Sprint 13: Replit Integration
```

### Sprint Order Rationale

1. **Claude Code** - Reference implementation, 80% done
2. **Goose** - Critical priority, 94% done
3. **Cursor** - High priority, popular IDE
4. **VS Code MCP** - High priority, widespread use
5. **GitHub Copilot** - High priority, enterprise adoption
6. **Continue.dev** - High priority, 50% done
7. **Aider** - High priority, 80% done
8. **JetBrains** - Medium priority, 86% done
9. **Windsurf** - High priority, emerging platform
10. **Gemini** - High priority, 65% done (most tasks)
11. **Amazon Q** - Medium priority, enterprise focus
12. **Cody** - Low priority, 50% done
13. **Replit** - Medium priority, 11% done (most remaining work)

### Standard Sprint Template

Each platform sprint follows this structure:

```yaml
sprint:
  name: "{Platform} Integration"
  tasks:
    # Phase 1: Foundation (3-4 tasks)
    - Create {Platform}Adapter class
    - Configure MCP/platform settings
    - Create configuration generator

    # Phase 2: Testing (2-3 tasks)
    - Write unit tests for adapter
    - Write integration tests
    - Platform-specific validation

    # Phase 3: Documentation (2-3 tasks)
    - Write integration guide
    - Write migration guide (if applicable)
    - Add vibey deploy --platform {name} CLI

    # Phase 4: Quality Gate (1-2 tasks)
    - Quality gate validation
    - Sprint completion summary
```

---

## Migration Plan

### Phase 1: Create New Track Structure

1. Create new track YAML: `platform-compatibility`
2. Create 13 sprint YAML files (one per platform)
3. Generate new ULIDs for track and sprints

### Phase 2: Migrate Tasks

For each of the 13 platforms:

1. Query existing tasks from old track
2. Update `track_id` to new track ULID
3. Update `sprint_id` to new sprint ULID
4. Preserve task status (completed/not_started)
5. Preserve task metadata

### Phase 3: Update Dependencies

1. Any tracks that depend on old platform tracks need updating
2. Update references in context documents
3. Update any hardcoded track IDs

### Phase 4: Archive Old Tracks

1. Set old tracks status to `superseded`
2. Add metadata noting superseded by `platform-compatibility`
3. Keep files for historical reference (don't delete)

### Phase 5: Verify Integrity

1. Run `vibey roadmap db rebuild`
2. Verify task counts match
3. Verify progress calculations
4. Run `vibey roadmap status` to confirm

---

## Implementation Steps

### Step 1: Generate New IDs

```bash
# Generate track ULID
python -c "import ulid; print(ulid.new())"

# Generate 13 sprint ULIDs
for i in range(13):
    print(ulid.new())
```

### Step 2: Create Track YAML

```yaml
track:
  id: {NEW_TRACK_ULID}
  name: Platform Compatibility
  roadmap_id: vibey-framework-v2
  status: in_progress
  blocked: false
  priority: critical
  created: '2025-12-11T00:00:00+00:00'
  progress:
    sprints_total: 13
    sprints_completed: 0
    tasks_total: 239
    tasks_completed: 127
    completion_percent: 53
  strategic_value:
    - Single track for all platform integrations
    - Consistent sprint structure across platforms
    - Clear progress visibility per platform
    - Simplified dependency management
```

### Step 3: Create Sprint YAMLs

One file per platform following the standard template.

### Step 4: Migrate Tasks

```python
# Pseudocode for task migration
for old_track_id, platform_name in PLATFORM_TRACKS.items():
    new_sprint_id = PLATFORM_SPRINT_MAP[platform_name]

    tasks = get_tasks_for_track(old_track_id)
    for task in tasks:
        task.track_id = NEW_TRACK_ID
        task.sprint_id = new_sprint_id
        save_task(task)
```

### Step 5: Archive Old Tracks

```python
for old_track_id in PLATFORM_TRACKS.keys():
    track = load_track(old_track_id)
    track.status = 'superseded'
    track.metadata['superseded_by'] = NEW_TRACK_ID
    track.metadata['superseded_date'] = datetime.now().isoformat()
    save_track(track)
```

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Task ID conflicts | High | Use existing task ULIDs, only update track_id/sprint_id |
| Broken dependencies | Medium | Audit all depends_on/blocked_by before migration |
| Lost context | Medium | Preserve all metadata and context files |
| Progress miscalculation | Low | Rebuild database after migration |
| Git history loss | Low | Archive old tracks instead of deleting |

---

## Rollback Plan

If migration fails:

1. Restore track YAMLs from git history
2. Restore task YAMLs from backup
3. Rebuild database
4. Delete new track/sprint files

---

## Success Criteria

- [ ] New Platform Compatibility track created
- [ ] All 239 tasks migrated to correct sprints
- [ ] Progress shows 127/239 (53%) completed
- [ ] Each platform sprint shows correct progress
- [ ] Old tracks marked as superseded
- [ ] No broken dependencies
- [ ] All tests pass
- [ ] CLI commands work correctly

---

## Estimated Effort

- **Planning**: 30 minutes (this document)
- **Script Development**: 1 hour
- **Migration Execution**: 30 minutes
- **Verification**: 30 minutes
- **Total**: ~2.5 hours

---

## Appendix: Track ID Reference

Old Track IDs to archive:
```
01KC2D0JK06MN77ZHAGAHF5VKB - Aider
01KC2D0JK06MN77ZHAGAHF5VKN - Amazon Q
01KC2D0JK1877YN6T0673VB24T - Claude Code
01KC2D0JK1877YN6T0673VB25H - Continue.dev
01KC2D0JK2A3KNMQVJDACN1X9M - Cursor
01KC2D0JK5Y3BX5008PVANFCHN - Gemini
01KC2D0JK1877YN6T0673VB260 - GitHub Copilot
01KC2D0JK7READW9KAK1HBX4BS - Goose
01KC2D0JK9JKQXGQW6MQEB0JZP - JetBrains
01KC2D0JKCJCWQ76VRQJWBGQY9 - Replit
01KC2D0JK1877YN6T0673VB254 - Cody
01KC2D0JKWWW8WMS7PPGDQ42GY - VS Code MCP
01KC2D0JKY8WC5NT15KN5SW9YE - Windsurf
```
