# Embedded Task Migration Plan

## Executive Summary

**Problem**: 1,330 tasks are embedded in sprint YAML files' `tasks[]` arrays instead of being stored as standalone task files. The YAML loader only reads from `tasks/*.yaml` files, causing these embedded tasks to be invisible to the database and all operations that rely on it.

**Impact**:
- Goose Port, JetBrains Port, and other tracks show 0 or few tasks despite having complete sprint histories
- Database is out of sync with actual roadmap state
- Progress calculations are incorrect
- Task updates don't work for embedded tasks

**Solution**: Extract all 1,330 embedded tasks to standalone YAML files, update codebase to use only standalone files, and remove embedded task support.

---

## Phase 1: Task Extraction

### 1.1 Statistics

| Metric | Count |
|--------|-------|
| Sprints with embedded tasks | 202 |
| Total embedded tasks | 1,330 |
| Existing standalone task files | 1,129 |
| After migration | ~2,459 task files |

### 1.2 Extraction Script Requirements

The extraction script must:

1. **Read each sprint file** in `.vibey/roadmap/sprints/*.yaml`
2. **For each embedded task** in `sprint.tasks[]`:
   - Check if standalone file already exists (by matching `id` or `slug`)
   - If no match: generate new ULID and create standalone file
   - If match exists: verify data consistency, prefer standalone file
3. **Generate proper standalone task format**:
   ```yaml
   task:
     id: 01KC...  # ULID
     sprint_id: 01KC...  # Parent sprint ULID
     track_id: 01KC...  # Parent track ULID
     roadmap_id: vibey-framework-v2
     task_type: development
     title: "Task title from embedded task"
     description: "..."
     status: completed
     # ... all other task fields
   ```
4. **Handle legacy slug IDs**: Convert `goose-port-1-task-001` to ULIDs using existing mapping or generating new ones
5. **Preserve all data**: status, dates, gate_info, etc.

### 1.3 Extraction Script Pseudocode

```python
def extract_embedded_tasks():
    # Build slug -> ULID mappings from existing files
    existing_tasks = {}
    for task_file in tasks_dir.glob("*.yaml"):
        task = load_yaml(task_file)
        if 'slug' in task['task']:
            existing_tasks[task['task']['slug']] = task['task']['id']
        existing_tasks[task['task']['id']] = task_file

    tasks_created = 0
    for sprint_file in sprints_dir.glob("*.yaml"):
        sprint_data = load_yaml(sprint_file)
        embedded_tasks = sprint_data.get('sprint', {}).get('tasks', [])

        if not embedded_tasks:
            continue

        sprint_id = sprint_data['sprint']['id']
        track_id = sprint_data['sprint']['track_id']

        for embedded_task in embedded_tasks:
            task_id = embedded_task['id']

            # Check if already extracted
            if task_id in existing_tasks or is_ulid(task_id) and (tasks_dir / f"{task_id}.yaml").exists():
                continue

            # Generate new ULID for legacy slug IDs
            if not is_ulid(task_id):
                new_ulid = generate_ulid()
                slug = task_id
            else:
                new_ulid = task_id
                slug = embedded_task.get('slug')

            # Create standalone task file
            standalone_task = convert_to_standalone_format(
                embedded_task,
                ulid=new_ulid,
                slug=slug,
                sprint_id=sprint_id,
                track_id=track_id
            )

            task_file = tasks_dir / f"{new_ulid}.yaml"
            save_yaml(task_file, {'task': standalone_task})
            tasks_created += 1

    return tasks_created
```

---

## Phase 2: Codebase Review

### 2.1 Files That READ Embedded Tasks

These files access `sprint['tasks']` or `sprint_data.get('tasks', [])`:

| File | Line(s) | Usage | Action Required |
|------|---------|-------|-----------------|
| `vibey/roadmap/serialization/yaml_loader.py` | 1108, 2113 | Loads embedded tasks into Sprint object | Update to ignore or warn |
| `vibey/roadmap/serialization/yaml_dumper.py` | 505-518 | Writes embedded tasks | Remove embedded task writing |
| `vibey/roadmap/summary_generator.py` | 137, 328 | Reads tasks for summaries | Query from standalone files |
| `vibey/roadmap/context_loader.py` | 216, 395 | Loads task context | Query from standalone files |
| `vibey/roadmap/markdown_generator.py` | 289 | Generates markdown | Query from standalone files |
| `vibey/operations/git/git_sync.py` | 309, 389, 428 | Syncs git state | Query from standalone files |
| `vibey/operations/git/merge_checker.py` | 136 | Checks merge state | Query from standalone files |
| `vibey/operations/git/branch_linker.py` | 264, 303, 382, 429, 482 | Links branches to tasks | Query from standalone files |
| `vibey/operations/git/status_updater.py` | 82, 109, 146, 182-183 | Updates task status | Query from standalone files |
| `vibey/operations/git/hooks/commit_msg.py` | 124 | Commit message hook | Query from standalone files |
| `vibey/cli/formatters.py` | 86 | CLI formatting | Query from standalone files |
| `vibey/roadmap/migration/yaml_migrator.py` | 243 | Migration | Update or remove |
| `vibey/operations/git/state_reconstructor.py` | 223 | State reconstruction | Query from standalone files |
| `vibey/cli/remediate_roadmap_system.py` | 731, 789, 823 | Remediation | Query from standalone files |
| `vibey/roadmap/validation/validator.py` | 285, 287, 294 | Validation | Query from standalone files |

### 2.2 Files That WRITE Embedded Tasks

| File | Line(s) | Usage | Action Required |
|------|---------|-------|-----------------|
| `vibey/roadmap/serialization/yaml_dumper.py` | 505-518 | `'tasks': [...]` in sprint | Remove embedded task section |
| `vibey/cli/commands.py` | 638, 647, 652 | Creates new tasks | Write to standalone files only |
| `vibey/cli/roadmap_create_from_plan.py` | 245-252 | Creates tasks from plan | Update to standalone format |
| `vibey/operations/roadmap/migration.py` | 285, 299 | Migration | Update to standalone format |

### 2.3 Migration Pattern

For each file that reads embedded tasks, the pattern is:

**Before (reading embedded tasks):**
```python
tasks = sprint_data.get('sprint', {}).get('tasks', [])
for task in tasks:
    # process task
```

**After (query standalone files):**
```python
from vibey.roadmap.serialization import load_tasks_by_sprint_flat

tasks = load_tasks_by_sprint_flat(tasks_dir, sprint_id)
for task in tasks:
    # process task
```

---

## Phase 3: Code Migration

### 3.1 Update yaml_loader.py

**Changes:**
1. Remove code that reads `sprint_data['tasks']` into Sprint.tasks
2. Add deprecation warning if embedded tasks are detected
3. Update `load_sprint()` to query standalone task files

```python
def load_sprint(file_path: Union[str, Path]) -> Sprint:
    # ... existing code ...

    # DEPRECATED: Warn about embedded tasks
    if 'tasks' in sprint_data and sprint_data['tasks']:
        import warnings
        warnings.warn(
            f"Sprint {sprint_data['id']} has embedded tasks. "
            "Run 'vibey roadmap migrate-embedded-tasks' to extract them.",
            DeprecationWarning
        )

    # Tasks should be loaded from standalone files, not embedded
    sprint.tasks = []  # Will be populated by querying tasks/*.yaml

    return sprint
```

### 3.2 Update yaml_dumper.py

**Changes:**
1. Remove the `'tasks': [...]` section from sprint output
2. Update `save_sprint()` to not write embedded tasks

```python
def save_sprint(sprint: Sprint, file_path: Union[str, Path]):
    # ... existing code ...

    data = {
        'sprint': {
            # ... all other fields ...
            # REMOVED: 'tasks': [...] - tasks are in standalone files
        }
    }
```

### 3.3 Update Other Files

Each file in section 2.1 needs to be updated to:
1. Query standalone task files using `load_tasks_by_sprint_flat()`
2. Remove direct access to `sprint['tasks']`
3. Handle case where tasks are in both places during migration

---

## Phase 4: Cleanup

### 4.1 Remove Embedded Tasks from Sprint Files

After all code is migrated, run cleanup script:

```python
def remove_embedded_tasks_from_sprints():
    for sprint_file in sprints_dir.glob("*.yaml"):
        data = load_yaml(sprint_file)
        if 'tasks' in data.get('sprint', {}):
            del data['sprint']['tasks']
            save_yaml(sprint_file, data)
```

### 4.2 Verify Migration

```python
def verify_migration():
    # 1. Count standalone task files
    task_files = list(tasks_dir.glob("*.yaml"))
    print(f"Standalone task files: {len(task_files)}")

    # 2. Check no sprint has embedded tasks
    for sprint_file in sprints_dir.glob("*.yaml"):
        data = load_yaml(sprint_file)
        if 'tasks' in data.get('sprint', {}):
            print(f"ERROR: {sprint_file.name} still has embedded tasks")

    # 3. Rebuild database and verify counts
    os.system("vibey roadmap db rebuild")

    # 4. Check all sprints have expected task counts
```

---

## Implementation Order

### Sprint 1: Extraction (Priority: CRITICAL)
1. [ ] Create `extract_embedded_tasks.py` script
2. [ ] Build comprehensive slug → ULID mapping for embedded task IDs
3. [ ] Extract all 1,330 embedded tasks to standalone files
4. [ ] Verify extraction by rebuilding database

### Sprint 2: Codebase Migration (Priority: HIGH)
1. [ ] Update `yaml_loader.py` - add deprecation warning, stop loading embedded tasks
2. [ ] Update `yaml_dumper.py` - stop writing embedded tasks
3. [ ] Update `summary_generator.py`
4. [ ] Update `context_loader.py`
5. [ ] Update `markdown_generator.py`

### Sprint 3: Git Operations Migration (Priority: HIGH)
1. [ ] Update `git_sync.py`
2. [ ] Update `merge_checker.py`
3. [ ] Update `branch_linker.py`
4. [ ] Update `status_updater.py`
5. [ ] Update `commit_msg.py` hook

### Sprint 4: CLI and Validation Migration (Priority: MEDIUM)
1. [ ] Update `formatters.py`
2. [ ] Update `commands.py` task creation
3. [ ] Update `roadmap_create_from_plan.py`
4. [ ] Update `validator.py`

### Sprint 5: Cleanup (Priority: LOW)
1. [ ] Run cleanup to remove embedded tasks from sprint files
2. [ ] Remove legacy migration code that handles embedded format
3. [ ] Update documentation
4. [ ] Final verification

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Data loss during extraction | Create full backup before running |
| Duplicate tasks created | Check for existing files by ID and slug before creating |
| Breaking existing workflows | Phase migration with deprecation warnings first |
| Performance impact of many files | Already tested with 1,129 files - negligible impact |

---

## Success Criteria

1. **All 1,330 embedded tasks extracted** to standalone files
2. **Database shows correct task counts** for all tracks
3. **No code references** `sprint['tasks']` or `sprint_data.get('tasks', [])`
4. **Sprint YAML files** have no `tasks:` section
5. **All tests pass** after migration
6. **Roadmap status command** shows accurate progress

---

## Appendix: Affected Tracks

Tracks with embedded tasks that need extraction:

| Track | Sprints | Embedded Tasks |
|-------|---------|----------------|
| goose-port | 5 | 34 |
| jetbrains-port | ? | ? |
| mcp-server | ? | ? |
| (others) | ... | ... |

Total: 202 sprints, 1,330 embedded tasks

---

*Created: 2025-12-11*
*Status: READY FOR IMPLEMENTATION*
