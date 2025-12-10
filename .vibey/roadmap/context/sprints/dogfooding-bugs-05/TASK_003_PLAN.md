# Task 003: Add Create Task CLI Command

**Task ID:** dogfooding-bugs-05-task-003
**Bug Addressed:** #15 (No CLI Commands to Create Tracks, Sprints, or Tasks in ULID Structure)
**Complexity:** Medium
**Type:** Development

---

## Problem Statement

The CLI lacks a command to create new tasks in the ULID-based flat directory structure. Users must manually create task YAML files, generate ULIDs, and manually update sprint progress counters.

---

## Current State

```bash
# No create task command exists
vibey roadmap create task  # Would error: no such command

# Current workaround: manual file creation
cat > .vibey/roadmap/tasks/task_01JB3QVE5NTSK2BPFQR8LVXABC.yaml << 'EOF'
task:
  id: task_01JB3QVE5NTSK2BPFQR8LVXABC
  sprint_id: sprint_01JB3QVE2CSPRT7KDHM4JQWXYZ
  track_id: track_01JB3QVDZ8TRK9XN1FJFHGWPRM
  title: "My Task"
  # ... 40+ lines of boilerplate
EOF

# Then manually update sprint progress...
```

---

## Implementation

### CLI Command Definition

```python
# vibey/cli/main.py - Add to roadmap command group

@roadmap.command('create-task')
@click.option('--sprint', '-s', required=True, help='Sprint ID to add task to')
@click.option('--title', '-t', required=True, help='Task title')
@click.option('--description', '-d', default='', help='Task description')
@click.option('--priority', '-p',
              type=click.Choice(['critical', 'high', 'medium', 'low']),
              default='medium', help='Task priority')
@click.option('--complexity',
              type=click.Choice(['simple', 'medium', 'complex']),
              default='medium', help='Task complexity')
@click.option('--type', 'task_type',
              type=click.Choice(['development', 'completion_gate', 'production_gate']),
              default='development', help='Task type')
@click.option('--agent', default='backend-engineer', help='Assigned agent')
@click.option('--estimated-tokens', type=int, default=5000, help='Estimated tokens')
@click.option('--depends-on', multiple=True, help='Task IDs this task depends on')
@click.option('--start', is_flag=True, help='Mark task as started immediately')
@click.pass_context
def roadmap_create_task(ctx, sprint: str, title: str, description: str,
                        priority: str, complexity: str, task_type: str,
                        agent: str, estimated_tokens: int, depends_on: tuple,
                        start: bool):
    """Create a new task in a sprint.

    Creates a new task YAML file using ULID-based naming in the flat structure.
    The task is automatically linked to the specified sprint and track.
    Sprint progress counters are updated automatically.

    Examples:
      vibey roadmap create-task --sprint sprint_01JB3... --title "Implement login"
      vibey roadmap create-task -s sprint_01JB3... -t "Add unit tests" --type completion_gate
      vibey roadmap create-task -s sprint_01JB3... -t "Fix bug" -p high --start
    """
    from vibey.cli.commands import create_task_cmd

    exit_code = create_task_cmd(
        sprint_id=sprint,
        title=title,
        description=description,
        priority=priority,
        complexity=complexity,
        task_type=task_type,
        agent=agent,
        estimated_tokens=estimated_tokens,
        depends_on=list(depends_on),
        start=start
    )
    sys.exit(exit_code)
```

### Command Implementation

```python
# vibey/cli/commands.py - Add create_task_cmd function

def create_task_cmd(
    sprint_id: str,
    title: str,
    description: str = '',
    priority: str = 'medium',
    complexity: str = 'medium',
    task_type: str = 'development',
    agent: str = 'backend-engineer',
    estimated_tokens: int = 5000,
    depends_on: list = None,
    start: bool = False
) -> int:
    """Create a new task in a sprint."""
    from pathlib import Path
    from datetime import datetime, timezone
    from vibey.roadmap.id_generator import generate_task_id
    from vibey.roadmap.models import (
        Task, TaskMetadata, TaskSummary, TaskStatus, TaskType,
        Priority, Complexity
    )
    from vibey.roadmap.serialization import (
        save_task, load_sprint, save_sprint
    )
    from vibey.cli.roadmap_lib.filesystem import FileSystemManager

    depends_on = depends_on or []

    # Find repository root
    root = _find_repo_root()
    if not root:
        click.echo("❌ No .vibey/ directory found", err=True)
        return 1

    fs = FileSystemManager(root)

    # Load sprint
    sprint_path = fs.roadmap_root / "sprints" / f"{sprint_id}.yaml"
    if not sprint_path.exists():
        click.echo(f"❌ Sprint not found: {sprint_id}", err=True)
        return 1

    sprint = load_sprint(sprint_path)

    # Generate task ID (ULID format)
    task_id = generate_task_id()

    # Check dependencies exist
    for dep_id in depends_on:
        if not _task_exists(fs, dep_id):
            click.echo(f"❌ Dependency task not found: {dep_id}", err=True)
            return 1

    # Map task type string to enum
    task_type_map = {
        'development': TaskType.DEVELOPMENT,
        'completion_gate': TaskType.COMPLETION_GATE,
        'production_gate': TaskType.PRODUCTION_GATE,
    }

    # Create task object
    now = datetime.now(timezone.utc)
    task = Task(
        id=task_id,
        sprint_id=sprint_id,
        track_id=sprint.track_id,
        roadmap_id=sprint.roadmap_id,
        task_type=task_type_map[task_type],
        title=title,
        description=description,
        status=TaskStatus.IN_PROGRESS if start else TaskStatus.NOT_STARTED,
        blocked=len(depends_on) > 0,  # Blocked if has unmet dependencies
        created=now,
        started=now if start else None,
        assigned_agent=agent,
        priority=Priority(priority),
        complexity=Complexity(complexity),
        estimated_tokens=estimated_tokens,
        dependencies=[],
        blocks=[],
        blocked_by=[],
        depends_on=depends_on,
        depended_on_by=[],
        metadata=TaskMetadata(
            last_updated=now,
            created_by='cli',
        ),
    )

    # Save task YAML file
    task_path = fs.roadmap_root / "tasks" / f"{task_id}.yaml"
    save_task(task, task_path)

    # Update sprint with task reference and progress
    _add_task_to_sprint(fs, sprint, task, sprint_path)

    # Update track progress
    _update_track_task_count(fs, sprint.track_id)

    # Update dependent tasks (add this task to their depended_on_by)
    for dep_id in depends_on:
        _add_task_dependent_reference(fs, dep_id, task_id)

    # Sync to database if enabled
    _sync_task_to_db(task, root)

    click.echo(f"✅ Created task: {title}")
    click.echo(f"   ID: {task_id}")
    click.echo(f"   Sprint: {sprint.name} ({sprint_id})")
    click.echo(f"   Type: {task_type}")
    click.echo(f"   File: {task_path.relative_to(root)}")
    click.echo(f"   Status: {'in_progress' if start else 'not_started'}")
    if depends_on:
        click.echo(f"   Depends on: {', '.join(depends_on)}")

    return 0


def _task_exists(fs, task_id: str) -> bool:
    """Check if task exists."""
    task_path = fs.roadmap_root / "tasks" / f"{task_id}.yaml"
    return task_path.exists()


def _add_task_to_sprint(fs, sprint, task, sprint_path):
    """Add task summary to sprint and update progress."""
    from vibey.roadmap.models import TaskSummary
    from vibey.roadmap.serialization import save_sprint

    # Add task summary
    summary = TaskSummary(
        id=task.id,
        title=task.title,
        status=task.status,
        task_type=task.task_type,
        priority=task.priority,
    )
    sprint.tasks.append(summary)

    # Update sprint progress based on task type
    sprint.progress.tasks_total += 1

    if task.task_type == TaskType.DEVELOPMENT:
        sprint.progress.development_tasks_total += 1
    elif task.task_type == TaskType.COMPLETION_GATE:
        sprint.progress.completion_gate_tasks_total += 1
    elif task.task_type == TaskType.PRODUCTION_GATE:
        sprint.progress.production_gate_tasks_total += 1

    # Recalculate completion percent
    if sprint.progress.tasks_total > 0:
        sprint.progress.completion_percent = int(
            (sprint.progress.tasks_completed / sprint.progress.tasks_total) * 100
        )

    save_sprint(sprint, sprint_path)


def _update_track_task_count(fs, track_id: str):
    """Update track's tasks_total counter."""
    from vibey.roadmap.serialization import load_track, save_track

    track_path = fs.roadmap_root / "tracks" / f"{track_id}.yaml"
    if track_path.exists():
        track = load_track(track_path)
        track.progress.tasks_total += 1
        save_track(track, track_path)


def _add_task_dependent_reference(fs, task_id: str, dependent_id: str):
    """Add dependent reference to a task's depended_on_by list."""
    from vibey.roadmap.serialization import load_task, save_task

    task_path = fs.roadmap_root / "tasks" / f"{task_id}.yaml"
    if task_path.exists():
        task = load_task(task_path)
        if dependent_id not in task.depended_on_by:
            task.depended_on_by.append(dependent_id)
        save_task(task, task_path)
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/cli/main.py` | Add `create-task` command definition |
| `vibey/cli/commands.py` | Add `create_task_cmd` implementation |

---

## Testing Strategy

```python
def test_create_task_basic(flat_roadmap_env):
    """Test basic task creation."""
    runner = CliRunner()

    # Create track and sprint first
    runner.invoke(cli, ['roadmap', 'create-track', '-n', 'Test Track'])
    runner.invoke(cli, ['roadmap', 'create-sprint', '-t', 'test-track', '-n', 'Sprint 1'])

    # Get sprint ID
    sprints_dir = flat_roadmap_env / ".vibey" / "roadmap" / "sprints"
    sprint_file = list(sprints_dir.glob("sprint_*.yaml"))[0]
    sprint_id = sprint_file.stem

    # Create task
    result = runner.invoke(cli, [
        'roadmap', 'create-task',
        '--sprint', sprint_id,
        '--title', 'Implement login',
    ])

    assert result.exit_code == 0
    assert 'Created task' in result.output
    assert 'Implement login' in result.output

    # Verify file created
    tasks_dir = flat_roadmap_env / ".vibey" / "roadmap" / "tasks"
    task_files = list(tasks_dir.glob("task_*.yaml"))
    assert len(task_files) == 1


def test_create_task_updates_sprint_progress(flat_roadmap_env):
    """Task creation updates sprint progress."""
    runner = CliRunner()

    # Setup
    runner.invoke(cli, ['roadmap', 'create-track', '-n', 'Test Track'])
    runner.invoke(cli, ['roadmap', 'create-sprint', '-t', 'test-track', '-n', 'Sprint 1'])

    sprints_dir = flat_roadmap_env / ".vibey" / "roadmap" / "sprints"
    sprint_file = list(sprints_dir.glob("sprint_*.yaml"))[0]
    sprint_id = sprint_file.stem

    # Create 3 tasks
    for i in range(3):
        runner.invoke(cli, [
            'roadmap', 'create-task',
            '-s', sprint_id,
            '-t', f'Task {i+1}',
        ])

    # Verify sprint progress
    sprint = load_sprint(sprint_file)
    assert sprint.progress.tasks_total == 3
    assert sprint.progress.development_tasks_total == 3
    assert len(sprint.tasks) == 3


def test_create_task_different_types(flat_roadmap_env):
    """Task types correctly categorized."""
    runner = CliRunner()

    # Setup
    runner.invoke(cli, ['roadmap', 'create-track', '-n', 'Test Track'])
    runner.invoke(cli, ['roadmap', 'create-sprint', '-t', 'test-track', '-n', 'Sprint 1'])

    sprints_dir = flat_roadmap_env / ".vibey" / "roadmap" / "sprints"
    sprint_file = list(sprints_dir.glob("sprint_*.yaml"))[0]
    sprint_id = sprint_file.stem

    # Create tasks of different types
    runner.invoke(cli, ['roadmap', 'create-task', '-s', sprint_id, '-t', 'Dev Task', '--type', 'development'])
    runner.invoke(cli, ['roadmap', 'create-task', '-s', sprint_id, '-t', 'Gate Task', '--type', 'completion_gate'])
    runner.invoke(cli, ['roadmap', 'create-task', '-s', sprint_id, '-t', 'Prod Task', '--type', 'production_gate'])

    # Verify progress counters
    sprint = load_sprint(sprint_file)
    assert sprint.progress.development_tasks_total == 1
    assert sprint.progress.completion_gate_tasks_total == 1
    assert sprint.progress.production_gate_tasks_total == 1
    assert sprint.progress.tasks_total == 3
```

---

## Success Criteria

- [ ] `vibey roadmap create-task --sprint X --title "Task"` works
- [ ] Task YAML created with ULID-based filename
- [ ] Task added to sprint's tasks list
- [ ] Sprint progress counters updated (tasks_total, type-specific)
- [ ] Track progress updated (tasks_total)
- [ ] ULID generated using id_generator.py
- [ ] Task type classification (development, completion_gate, production_gate)
- [ ] Optional --depends-on for task dependencies
- [ ] Database sync if SQLite enabled

---

## Dependencies

- Task 001 (create track command)
- Task 002 (create sprint command)
- Task 005 (ULIDManager) - Already exists in id_generator.py

---

## Notes

Key considerations:
1. Sprint must exist before creating task
2. Track ID extracted from sprint (no need to specify)
3. Task type affects which progress counter is incremented
4. Dependencies are optional but validated
5. Task auto-blocked if it has unmet dependencies
6. Both sprint and track progress are updated
