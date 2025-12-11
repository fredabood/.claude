# Sprint 4: CLI and Validation Migration - Task Plans

**Sprint ID**: `01KC7H29E0Z5BC7HK1CK222156`
**Track**: Embedded Task Migration
**Priority**: MEDIUM
**Blocked By**: Sprint 3

---

## Task 001: Update formatters.py

**Task ID**: `01KC7H29E0Z5BC7HK1CK22215P`
**Estimated Tokens**: 15,000
**Complexity**: Simple

### Objective
Update formatters.py to query standalone task files.

### Files to Modify
- `vibey/cli/formatters.py`

### Implementation Plan

#### Step 1: Locate Current Code
Line ~86:
```python
tasks = sprint.get('tasks', [])
```

#### Step 2: Replace
```python
from vibey.roadmap.serialization import load_tasks_by_sprint_flat

def format_sprint_details(sprint: Dict, tasks_dir: Path) -> str:
    sprint_id = sprint.get('id') or sprint.get('sprint', {}).get('id')

    # Load tasks from standalone files
    tasks = load_tasks_by_sprint_flat(tasks_dir, sprint_id)

    # Format output...
    lines = []
    lines.append(f"Tasks ({len(tasks)}):")
    for task in tasks:
        status_icon = "✓" if task.status == 'completed' else "○"
        lines.append(f"  {status_icon} {task.title}")

    return "\n".join(lines)
```

### Acceptance Criteria
- [ ] CLI formatting uses standalone files
- [ ] Task lists display correctly
- [ ] Status icons accurate

---

## Task 002: Update commands.py task creation

**Task ID**: `01KC7H29E0Z5BC7HK1CK22215Q`
**Estimated Tokens**: 25,000
**Complexity**: Medium

### Objective
Update commands.py to write tasks to standalone files only.

### Files to Modify
- `vibey/cli/commands.py`

### Implementation Plan

#### Step 1: Locate Current Code
Lines ~638, ~647, ~652:
```python
# Line ~638
data['sprint']['tasks'] = []

# Line ~647
data['sprint']['tasks'].append(task_entry)

# Line ~652
data['sprint']['progress']['tasks_total'] = len(data['sprint']['tasks'])
```

#### Step 2: Remove Embedded Task Writing
```python
def create_task(sprint_id: str, title: str, ...) -> str:
    # Generate ULID for new task
    from ulid import ULID
    task_ulid = str(ULID())

    # Create task data
    task_data = {
        'task': {
            'id': task_ulid,
            'sprint_id': sprint_id,
            'track_id': track_id,  # Get from sprint
            'roadmap_id': 'vibey-framework-v2',
            'title': title,
            'status': 'not_started',
            # ... other fields ...
        }
    }

    # Write standalone task file
    task_file = tasks_dir / f"{task_ulid}.yaml"
    with open(task_file, 'w') as f:
        yaml.dump(task_data, f, ...)

    # Update sprint progress (count from files)
    _update_sprint_task_count(sprint_id)

    return task_ulid
```

#### Step 3: Remove Sprint Tasks Array Updates
```python
# REMOVE these lines:
# data['sprint']['tasks'] = []
# data['sprint']['tasks'].append(task_entry)

# KEEP progress update, but compute from files:
def _update_sprint_task_count(sprint_id: str):
    tasks = load_tasks_by_sprint_flat(tasks_dir, sprint_id)
    sprint_data['sprint']['progress']['tasks_total'] = len(tasks)
    sprint_data['sprint']['progress']['tasks_completed'] = sum(
        1 for t in tasks if t.status == 'completed'
    )
```

### Acceptance Criteria
- [ ] New tasks created as standalone files
- [ ] No embedded tasks added to sprint files
- [ ] Sprint progress computed from files
- [ ] `vibey roadmap task create` works correctly

---

## Task 003: Update roadmap_create_from_plan.py

**Task ID**: `01KC7H29E0Z5BC7HK1CK22215R`
**Estimated Tokens**: 20,000
**Complexity**: Medium

### Objective
Update roadmap_create_from_plan.py to create standalone task files.

### Files to Modify
- `vibey/cli/roadmap_create_from_plan.py`

### Implementation Plan

#### Step 1: Locate Current Code
Lines ~245-252:
```python
def _update_sprint_tasks(sprint_yaml: Path, task_summaries: List[Dict]):
    # ... loads sprint, adds embedded tasks ...
    data['sprint']['tasks'] = task_summaries
```

#### Step 2: Replace with Standalone Creation
```python
def _create_standalone_tasks(
    tasks_dir: Path,
    sprint_id: str,
    track_id: str,
    task_definitions: List[Dict]
) -> List[str]:
    """Create standalone task files from plan definitions."""
    from ulid import ULID

    created_ids = []
    for i, task_def in enumerate(task_definitions, 1):
        task_ulid = str(ULID())

        task_data = {
            'task': {
                'id': task_ulid,
                'sprint_id': sprint_id,
                'track_id': track_id,
                'roadmap_id': 'vibey-framework-v2',
                'title': task_def.get('title', f'Task {i}'),
                'description': task_def.get('description', ''),
                'status': 'not_started',
                'sequence': i,
                # ... other fields ...
            }
        }

        task_file = tasks_dir / f"{task_ulid}.yaml"
        with open(task_file, 'w') as f:
            yaml.dump(task_data, f, ...)

        created_ids.append(task_ulid)

    return created_ids
```

#### Step 3: Remove _update_sprint_tasks
Delete the function and all calls to it.

### Acceptance Criteria
- [ ] Plan creation produces standalone files
- [ ] No embedded tasks in new sprints
- [ ] Task sequence preserved

---

## Task 004: Update validator.py

**Task ID**: `01KC7H29E0Z5BC7HK1CK22215S`
**Estimated Tokens**: 15,000
**Complexity**: Simple

### Objective
Update validator.py to check standalone task files.

### Files to Modify
- `vibey/roadmap/validation/validator.py`

### Implementation Plan

#### Step 1: Locate Current Code
Lines ~285, ~287, ~294:
```python
if "id" in sprint and "tasks" in sprint:
    for task in sprint["tasks"]:
        # validate task...
```

#### Step 2: Replace with Standalone Validation
```python
def validate_sprint_tasks(sprint_id: str, tasks_dir: Path) -> List[ValidationError]:
    """Validate tasks for a sprint from standalone files."""
    from vibey.roadmap.serialization import load_tasks_by_sprint_flat

    errors = []
    tasks = load_tasks_by_sprint_flat(tasks_dir, sprint_id)

    for task in tasks:
        # Validate task fields
        if not task.id:
            errors.append(ValidationError(f"Task missing id"))
        if not task.title:
            errors.append(ValidationError(f"Task {task.id} missing title"))
        # ... other validations ...

    return errors
```

#### Step 3: Add Warning for Embedded Tasks
```python
def validate_sprint(sprint_data: Dict) -> List[ValidationError]:
    errors = []

    # Warn if embedded tasks found
    if sprint_data.get('tasks'):
        errors.append(ValidationWarning(
            f"Sprint has embedded tasks. "
            "Run 'vibey roadmap extract-embedded' to migrate."
        ))

    # ... other validation ...
    return errors
```

### Acceptance Criteria
- [ ] Validation checks standalone files
- [ ] Warning for embedded tasks
- [ ] All task validations work

---

## Sprint 4 Summary

| Task | Title | Tokens | Complexity | Impact |
|------|-------|--------|------------|--------|
| 001 | Update formatters.py | 15,000 | Simple | CLI display |
| 002 | Update commands.py | 25,000 | Medium | Task creation |
| 003 | Update roadmap_create_from_plan.py | 20,000 | Medium | Plan import |
| 004 | Update validator.py | 15,000 | Simple | Validation |

**Total Estimated Tokens**: 75,000
**Estimated Duration**: 2 days
**Critical**: Task 002 (commands.py) - affects all new task creation
