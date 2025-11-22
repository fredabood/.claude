# Recalculation Algorithm

Technical documentation for Vibey's intelligent sprint recalculation system.

## Overview

The recalculation algorithm splits oversized tasks into smaller subtasks while preserving:
- Dependency relationships
- Success criteria coverage
- Agent assignments
- Sprint coherence

## Algorithm Components

### 1. Task Compatibility Analysis

Located in `vibey/roadmap/compatibility.py`

```python
def check_task_compatibility(
    task_data: Dict[str, Any],
    context_window: int,
    buffer_percent: float = 0.1
) -> TaskCompatibility:
```

**Process:**
1. Extract `estimated_tokens` from task
2. Calculate effective context (window - buffer)
3. Determine compatibility status:
   - `COMPATIBLE`: < 80% of effective context
   - `WARNING`: 80-100% of effective context
   - `OVERSIZED`: > effective context
   - `UNKNOWN`: Missing token estimate

### 2. Split Count Calculation

Located in `vibey/roadmap/recalculator.py`

```python
def calculate_split_count(
    estimated_tokens: int,
    target_context: int,
    buffer_percent: float = 0.1
) -> int:
```

**Formula:**
```
effective_context = target_context * (1 - buffer_percent)
split_count = ceil(estimated_tokens / effective_context)
```

**Example:**
- Task: 250,000 tokens
- Target: 128,000 tokens (Goose)
- Effective: 115,200 tokens
- Split count: ceil(250,000 / 115,200) = 3 subtasks

### 3. Success Criteria Distribution

```python
def split_success_criteria(
    criteria: List[str],
    split_count: int
) -> List[List[str]]:
```

**Algorithm:**
1. Analyze criteria for natural groupings
2. Distribute criteria across subtasks
3. Ensure each subtask has meaningful criteria
4. Preserve order where logical

**Example:**
```python
# Original: 6 criteria, 3 splits
criteria = [
    "API endpoints implemented",
    "API endpoints tested",
    "Business logic complete",
    "Business logic tested",
    "Data layer complete",
    "Data layer tested"
]

# Result:
[
    ["API endpoints implemented", "API endpoints tested"],
    ["Business logic complete", "Business logic tested"],
    ["Data layer complete", "Data layer tested"]
]
```

### 4. Dependency Preservation

```python
def split_task(
    task_data: Dict[str, Any],
    target_context: int,
    sprint_id: str,
    existing_task_ids: Set[str]
) -> List[SubTask]:
```

**Rules:**
1. First subtask inherits parent's dependencies
2. Subsequent subtasks depend on previous subtask
3. External references to parent redirect to last subtask
4. Circular dependencies are detected and prevented

**Example:**
```
Before:
  task-002 depends on task-001
  task-003 depends on task-002 (to be split)
  task-004 depends on task-003

After splitting task-003 into 3 subtasks:
  task-003a depends on task-002
  task-003b depends on task-003a
  task-003c depends on task-003b
  task-004 depends on task-003c (remapped)
```

### 5. ID Generation

Subtask IDs follow the pattern:
```
{parent_task_id}-{letter}
```

**Example:**
```
platform-context-management-3-task-005
  → platform-context-management-3-task-005-a
  → platform-context-management-3-task-005-b
```

If lettered IDs exist, numeric suffixes are used:
```
  → platform-context-management-3-task-005-001
  → platform-context-management-3-task-005-002
```

## Data Structures

### SubTask

```python
@dataclass
class SubTask:
    id: str
    name: str
    estimated_tokens: int
    dependencies: List[str]
    success_criteria: List[str]
    parent_task_id: str
    assigned_agent: Optional[str] = None
```

### RecalculationPlan

```python
@dataclass
class RecalculationPlan:
    sprint_id: str
    target_platform: str
    target_context: int
    tasks_to_split: List[TaskSplit]
    tasks_to_keep: List[str]
    dependency_remappings: Dict[str, str]
    estimated_new_task_count: int
    warnings: List[str]
```

### TaskSplit

```python
@dataclass
class TaskSplit:
    original_task_id: str
    original_tokens: int
    subtasks: List[SubTask]
    reason: str
```

### RecalculationResult

```python
@dataclass
class RecalculationResult:
    success: bool
    plan: RecalculationPlan
    tasks_created: List[str]
    tasks_archived: List[str]
    files_modified: List[Path]
    errors: List[str]
```

## File Operations

### Creating Subtask Files

When applying recalculation:

1. Create subtask directories:
   ```
   .vibey/roadmap/{track}/{sprint}/{subtask_id}/
   ```

2. Write task.yaml for each subtask:
   ```yaml
   task:
     id: {subtask_id}
     name: {original_name} (Part {n}/{total})
     sprint_id: {sprint_id}
     track_id: {track_id}
     status: not_started
     estimated_tokens: {calculated_tokens}
     dependencies: {remapped_dependencies}
     parent_task_id: {original_task_id}
     success_criteria: {distributed_criteria}
   ```

3. Archive original task:
   ```yaml
   task:
     status: superseded
     superseded_by: [{subtask_ids}]
     superseded_at: {timestamp}
   ```

### Updating Sprint Metadata

After splitting:

1. Update sprint.yaml task list
2. Recalculate progress totals
3. Update completion percentages

## CLI Integration

### Command: `vibey roadmap recalculate`

```bash
vibey roadmap recalculate <sprint-id> [OPTIONS]

Options:
  --platform TEXT       Target platform (default: current)
  --context-window INT  Override context window
  --dry-run            Preview without applying
  --force              Skip confirmation prompt
```

### Flow:

1. Load sprint data
2. Check task compatibility
3. Generate recalculation plan
4. Display plan summary
5. Prompt for confirmation (unless --dry-run or --force)
6. Apply changes
7. Report results

## Error Handling

### Validation Errors

| Error | Cause | Resolution |
|-------|-------|------------|
| `SprintNotFound` | Invalid sprint ID | Check sprint exists |
| `NoOversizedTasks` | All tasks fit | No recalculation needed |
| `CircularDependency` | Dependency loop | Manual intervention |
| `InvalidTokenEstimate` | Missing/invalid estimate | Update task data |

### Recovery

If recalculation fails mid-operation:

1. Check `.vibey/roadmap-backup/` for automatic backups
2. Review error messages for specific failures
3. Manually fix or restore from backup

## Testing

### Test Scenarios

1. **Basic Split**: Single oversized task
2. **Multiple Splits**: Several oversized tasks
3. **Dependency Chain**: Tasks with complex dependencies
4. **Edge Cases**: Tasks at exactly the limit

### Test Command

```bash
pytest tests/roadmap/test_recalculator.py -v
```

## Performance Considerations

- Plan generation is O(n) where n = task count
- File operations are batched for efficiency
- Large sprints (>50 tasks) may take several seconds

## Future Enhancements

1. **Smart Grouping**: AI-assisted criteria grouping
2. **Incremental Recalculation**: Only recalculate changed tasks
3. **Undo Support**: Reverse recalculation operations
4. **Cross-Sprint Optimization**: Balance across sprints

## See Also

- [Platform Context Management Guide](../guides/PLATFORM_CONTEXT_MANAGEMENT.md)
- [Token Effort Estimation](../guides/TOKEN_EFFORT_ESTIMATION.md)
- [Roadmap CLI Reference](../guides/ROADMAP_CLI_REFERENCE.md)
