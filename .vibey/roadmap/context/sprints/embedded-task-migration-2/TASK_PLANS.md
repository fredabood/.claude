# Sprint 2: Serialization Migration - Task Plans

**Sprint ID**: `01KC7H29E0Z5BC7HK1CK222154`
**Track**: Embedded Task Migration
**Priority**: HIGH
**Blocked By**: Sprint 1

---

## Task 001: Update yaml_loader.py - add deprecation warning

**Task ID**: `01KC7H29E0Z5BC7HK1CK22215C`
**Estimated Tokens**: 25,000
**Complexity**: Medium

### Objective
Update yaml_loader.py to warn when embedded tasks are detected and stop loading them into Sprint.tasks.

### Files to Modify
- `vibey/roadmap/serialization/yaml_loader.py`

### Implementation Plan

#### Step 1: Locate Current Code
Lines ~1108 and ~2113 read embedded tasks:
```python
for t in sprint_data['tasks']:
    # ...
```

#### Step 2: Add Deprecation Warning
```python
import warnings

def load_sprint(file_path: Union[str, Path]) -> Sprint:
    # ... existing code ...

    # Check for embedded tasks (DEPRECATED)
    embedded_tasks = sprint_data.get('tasks', [])
    if embedded_tasks:
        warnings.warn(
            f"Sprint '{sprint_data.get('id', 'unknown')}' has {len(embedded_tasks)} "
            "embedded tasks. Embedded tasks are deprecated. "
            "Run 'vibey roadmap extract-embedded' to migrate them.",
            DeprecationWarning,
            stacklevel=2
        )

    # Don't load embedded tasks - they should be in standalone files
    # sprint.tasks will be populated by querying tasks/*.yaml
    sprint = Sprint(
        # ... existing fields ...
        tasks=[],  # Empty - load from standalone files
    )

    return sprint
```

#### Step 3: Update load_sprint_ticket() Similarly
Same pattern for the v2 loader at ~line 2113.

### Acceptance Criteria
- [ ] Warning shown when embedded tasks detected
- [ ] Embedded tasks NOT loaded into Sprint.tasks
- [ ] Tests updated to expect empty tasks list
- [ ] Warning includes sprint ID and task count

### Testing
```python
def test_embedded_task_warning():
    with pytest.warns(DeprecationWarning, match="embedded tasks"):
        sprint = load_sprint("sprint_with_embedded.yaml")
    assert sprint.tasks == []
```

---

## Task 002: Update yaml_dumper.py - stop writing embedded tasks

**Task ID**: `01KC7H29E0Z5BC7HK1CK22215D`
**Estimated Tokens**: 20,000
**Complexity**: Medium

### Objective
Update yaml_dumper.py to not write embedded tasks to sprint files.

### Files to Modify
- `vibey/roadmap/serialization/yaml_dumper.py`

### Implementation Plan

#### Step 1: Locate Current Code
Lines ~505-518 write embedded tasks:
```python
'tasks': [
    {
        'id': t.id,
        'title': t.title,
        'status': t.status.value,
        'task_type': t.task_type.value,
        'gate_info': ...,
    }
    for t in sprint.tasks
],
```

#### Step 2: Remove Embedded Task Writing
```python
def save_sprint(sprint: Sprint, file_path: Union[str, Path]):
    # ... existing code ...

    data = {
        'sprint': {
            'id': sprint.id,
            'name': sprint.name,
            # ... all other fields ...

            # REMOVED: 'tasks': [...]
            # Tasks are stored in standalone files at tasks/{ulid}.yaml
            # See: load_tasks_by_sprint_flat() to query tasks

            'development_gates': [...],
            # ... rest of fields ...
        }
    }
```

#### Step 3: Add Comment in Output
Add a comment field explaining where tasks are:
```python
# Optionally add a reference field
'_tasks_note': 'Tasks stored in tasks/*.yaml files, query by sprint_id',
```

### Acceptance Criteria
- [ ] save_sprint() does not write 'tasks' key
- [ ] Existing sprint files can still be read (backward compat)
- [ ] New sprint files have no embedded tasks

### Testing
```python
def test_sprint_no_embedded_tasks():
    sprint = create_test_sprint()
    sprint.tasks = [create_test_task()]

    save_sprint(sprint, tmp_path / "sprint.yaml")

    data = yaml.safe_load((tmp_path / "sprint.yaml").read_text())
    assert 'tasks' not in data['sprint']
```

---

## Task 003: Update summary_generator.py

**Task ID**: `01KC7H29E0Z5BC7HK1CK22215E`
**Estimated Tokens**: 15,000
**Complexity**: Simple

### Objective
Update summary_generator.py to query standalone task files.

### Files to Modify
- `vibey/roadmap/summary_generator.py`

### Implementation Plan

#### Step 1: Locate Current Code
Lines ~137 and ~328:
```python
tasks = sprint_data.get('sprint', {}).get('tasks', [])
```

#### Step 2: Replace with Standalone Query
```python
from vibey.roadmap.serialization import load_tasks_by_sprint_flat

def generate_sprint_summary(sprint_file: Path, tasks_dir: Path) -> str:
    sprint_data = yaml.safe_load(sprint_file.read_text())
    sprint_id = sprint_data.get('sprint', {}).get('id')

    # Load tasks from standalone files
    tasks = load_tasks_by_sprint_flat(tasks_dir, sprint_id)

    # ... rest of summary generation ...
```

#### Step 3: Update Function Signatures
Add `tasks_dir` parameter where needed.

### Acceptance Criteria
- [ ] No direct access to sprint['tasks']
- [ ] Tasks loaded from standalone files
- [ ] Summaries show correct task counts

---

## Task 004: Update context_loader.py

**Task ID**: `01KC7H29E0Z5BC7HK1CK22215F`
**Estimated Tokens**: 15,000
**Complexity**: Simple

### Objective
Update context_loader.py to query standalone task files.

### Files to Modify
- `vibey/roadmap/context_loader.py`

### Implementation Plan

#### Step 1: Locate Current Code
Lines ~216 and ~395:
```python
tasks = sprint_data.get('sprint', {}).get('tasks', [])
```

#### Step 2: Replace Pattern
Same pattern as summary_generator.py:
```python
from vibey.roadmap.serialization import load_tasks_by_sprint_flat

# Replace embedded task access with:
tasks = load_tasks_by_sprint_flat(self.tasks_dir, sprint_id)
```

### Acceptance Criteria
- [ ] Context loading uses standalone files
- [ ] All task data available in context

---

## Task 005: Update markdown_generator.py

**Task ID**: `01KC7H29E0Z5BC7HK1CK22215G`
**Estimated Tokens**: 15,000
**Complexity**: Simple

### Objective
Update markdown_generator.py to query standalone task files.

### Files to Modify
- `vibey/roadmap/markdown_generator.py`

### Implementation Plan

#### Step 1: Locate Current Code
Line ~289:
```python
for task in sprint['tasks']:
```

#### Step 2: Replace with Query
```python
from vibey.roadmap.serialization import load_tasks_by_sprint_flat

def generate_sprint_markdown(sprint_data: Dict, tasks_dir: Path) -> str:
    sprint_id = sprint_data['sprint']['id']
    tasks = load_tasks_by_sprint_flat(tasks_dir, sprint_id)

    for task in tasks:
        # ... generate task markdown ...
```

### Acceptance Criteria
- [ ] Markdown generation uses standalone files
- [ ] Output unchanged (same content)

---

## Sprint 2 Summary

| Task | Title | Tokens | Complexity | Files |
|------|-------|--------|------------|-------|
| 001 | Update yaml_loader.py | 25,000 | Medium | yaml_loader.py |
| 002 | Update yaml_dumper.py | 20,000 | Medium | yaml_dumper.py |
| 003 | Update summary_generator.py | 15,000 | Simple | summary_generator.py |
| 004 | Update context_loader.py | 15,000 | Simple | context_loader.py |
| 005 | Update markdown_generator.py | 15,000 | Simple | markdown_generator.py |

**Total Estimated Tokens**: 90,000
**Estimated Duration**: 2 days
**All tasks can run in parallel** (no inter-task dependencies)
