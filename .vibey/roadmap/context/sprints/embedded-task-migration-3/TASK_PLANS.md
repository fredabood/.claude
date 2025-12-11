# Sprint 3: Git Operations Migration - Task Plans

**Sprint ID**: `01KC7H29E0Z5BC7HK1CK222155`
**Track**: Embedded Task Migration
**Priority**: HIGH
**Blocked By**: Sprint 2

---

## Task 001: Update git_sync.py

**Task ID**: `01KC7H29E0Z5BC7HK1CK22215H`
**Estimated Tokens**: 20,000
**Complexity**: Medium

### Objective
Update git_sync.py to query standalone task files instead of reading sprint['tasks'].

### Files to Modify
- `vibey/operations/git/git_sync.py`

### Implementation Plan

#### Step 1: Locate Current Code
Lines ~309, ~389, ~428:
```python
tasks = sprint.get('tasks', [])
```

#### Step 2: Create Helper Function
```python
def _load_tasks_for_sprint(self, sprint_id: str) -> List[Dict]:
    """Load tasks for a sprint from standalone files."""
    from vibey.roadmap.serialization import load_tasks_by_sprint_flat
    tasks_dir = self.roadmap_dir / "tasks"
    return load_tasks_by_sprint_flat(tasks_dir, sprint_id)
```

#### Step 3: Replace All Occurrences
```python
# Line ~309
sprint_id = sprint.get('id')
tasks = self._load_tasks_for_sprint(sprint_id)

# Line ~389
tasks = self._load_tasks_for_sprint(sprint['id'])

# Line ~428
tasks = self._load_tasks_for_sprint(sprint['id'])
```

### Acceptance Criteria
- [ ] All 3 occurrences updated
- [ ] Git sync works correctly
- [ ] Task status synced from standalone files

---

## Task 002: Update merge_checker.py

**Task ID**: `01KC7H29E0Z5BC7HK1CK22215J`
**Estimated Tokens**: 15,000
**Complexity**: Simple

### Objective
Update merge_checker.py to query standalone task files.

### Files to Modify
- `vibey/operations/git/merge_checker.py`

### Implementation Plan

#### Step 1: Locate Current Code
Line ~136:
```python
tasks = data['sprint'].get('tasks', [])
```

#### Step 2: Replace
```python
from vibey.roadmap.serialization import load_tasks_by_sprint_flat

def check_merge_readiness(self, sprint_file: Path) -> MergeCheckResult:
    data = yaml.safe_load(sprint_file.read_text())
    sprint_id = data['sprint']['id']

    # Load tasks from standalone files
    tasks_dir = sprint_file.parent.parent / "tasks"
    tasks = load_tasks_by_sprint_flat(tasks_dir, sprint_id)

    # ... rest of merge checking ...
```

### Acceptance Criteria
- [ ] Merge checking uses standalone files
- [ ] All task statuses correctly evaluated

---

## Task 003: Update branch_linker.py

**Task ID**: `01KC7H29E0Z5BC7HK1CK22215K`
**Estimated Tokens**: 20,000
**Complexity**: Medium

### Objective
Update branch_linker.py to query standalone task files.

### Files to Modify
- `vibey/operations/git/branch_linker.py`

### Implementation Plan

#### Step 1: Locate Current Code
Lines ~264, ~303, ~382, ~429, ~482:
```python
tasks = sprint.get("tasks", [])
```

#### Step 2: Add Helper
```python
def _get_sprint_tasks(self, sprint: Dict) -> List[Dict]:
    """Get tasks for sprint from standalone files."""
    from vibey.roadmap.serialization import load_tasks_by_sprint_flat
    sprint_id = sprint.get('id') or sprint.get('sprint', {}).get('id')
    return load_tasks_by_sprint_flat(self.tasks_dir, sprint_id)
```

#### Step 3: Replace All 5 Occurrences
```python
# Each occurrence:
tasks = self._get_sprint_tasks(sprint)
```

### Acceptance Criteria
- [ ] All 5 occurrences updated
- [ ] Branch linking works correctly
- [ ] Task-branch associations preserved

---

## Task 004: Update status_updater.py

**Task ID**: `01KC7H29E0Z5BC7HK1CK22215M`
**Estimated Tokens**: 20,000
**Complexity**: Medium

### Objective
Update status_updater.py to query standalone task files.

### Files to Modify
- `vibey/operations/git/status_updater.py`

### Implementation Plan

#### Step 1: Locate Current Code
Lines ~82, ~109, ~146, ~182-183:
```python
tasks = sprint.get("tasks", [])
```

And:
```python
sprint["progress"]["tasks_completed"] = completed_count
sprint["progress"]["tasks_total"] = total_count
```

#### Step 2: Replace Task Loading
```python
from vibey.roadmap.serialization import load_tasks_by_sprint_flat

def update_sprint_status(self, sprint_id: str) -> None:
    # Load tasks from standalone files
    tasks = load_tasks_by_sprint_flat(self.tasks_dir, sprint_id)

    completed_count = sum(1 for t in tasks if t.status == 'completed')
    total_count = len(tasks)

    # Update sprint progress
    # ...
```

### Acceptance Criteria
- [ ] All 4 occurrences updated
- [ ] Status updates use standalone files
- [ ] Progress calculations correct

---

## Task 005: Update commit_msg.py hook

**Task ID**: `01KC7H29E0Z5BC7HK1CK22215N`
**Estimated Tokens**: 15,000
**Complexity**: Simple

### Objective
Update commit_msg.py hook to query standalone task files.

### Files to Modify
- `vibey/operations/git/hooks/commit_msg.py`

### Implementation Plan

#### Step 1: Locate Current Code
Line ~124:
```python
tasks = sprint.get("tasks", [])
```

#### Step 2: Replace
```python
from vibey.roadmap.serialization import load_tasks_by_sprint_flat

def process_commit_message(self, message: str) -> str:
    # ... get sprint_id ...

    # Load tasks from standalone files
    tasks = load_tasks_by_sprint_flat(self.tasks_dir, sprint_id)

    # ... rest of processing ...
```

### Acceptance Criteria
- [ ] Commit hook uses standalone files
- [ ] Task references in commits work

---

## Sprint 3 Summary

| Task | Title | Tokens | Complexity | Lines to Change |
|------|-------|--------|------------|-----------------|
| 001 | Update git_sync.py | 20,000 | Medium | 3 occurrences |
| 002 | Update merge_checker.py | 15,000 | Simple | 1 occurrence |
| 003 | Update branch_linker.py | 20,000 | Medium | 5 occurrences |
| 004 | Update status_updater.py | 20,000 | Medium | 4 occurrences |
| 005 | Update commit_msg.py | 15,000 | Simple | 1 occurrence |

**Total Estimated Tokens**: 90,000
**Estimated Duration**: 2 days
**All tasks can run in parallel** (no inter-task dependencies)
