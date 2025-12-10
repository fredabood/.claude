# Task 002: Add Create Sprint CLI Command

**Task ID:** dogfooding-bugs-05-task-002
**Bug Addressed:** #15 (No CLI Commands to Create Tracks, Sprints, or Tasks in ULID Structure)
**Complexity:** Medium
**Type:** Development

---

## Problem Statement

The CLI lacks a command to create new sprints in the ULID-based flat directory structure. Users must manually create sprint YAML files, generate ULIDs, and manually link sprints to tracks.

---

## Current State

```bash
# No create sprint command exists
vibey roadmap create sprint  # Would error: no such command

# Current workaround: manual file creation
cat > .vibey/roadmap/sprints/sprint_01JB3QVE2CSPRT7KDHM4JQWXYZ.yaml << 'EOF'
sprint:
  id: sprint_01JB3QVE2CSPRT7KDHM4JQWXYZ
  track_id: track_01JB3QVDZ8TRK9XN1FJFHGWPRM
  name: Sprint 1
  # ... 60+ lines of boilerplate
EOF

# Then manually update track to reference sprint...
```

---

## Implementation

### CLI Command Definition

```python
# vibey/cli/main.py - Add to roadmap command group

@roadmap.command('create-sprint')
@click.option('--track', '-t', required=True, help='Track ID or slug to add sprint to')
@click.option('--name', '-n', required=True, help='Sprint name')
@click.option('--description', '-d', default='', help='Sprint description')
@click.option('--priority', '-p',
              type=click.Choice(['critical', 'high', 'medium', 'low']),
              default='medium', help='Sprint priority')
@click.option('--duration', default='2 weeks', help='Estimated duration')
@click.option('--start', is_flag=True, help='Mark sprint as started immediately')
@click.option('--depends-on', multiple=True, help='Sprint IDs this sprint depends on')
@click.pass_context
def roadmap_create_sprint(ctx, track: str, name: str, description: str,
                          priority: str, duration: str, start: bool,
                          depends_on: tuple):
    """Create a new sprint in a track.

    Creates a new sprint YAML file using ULID-based naming in the flat structure.
    The sprint is automatically linked to the specified track.

    Examples:
      vibey roadmap create-sprint --track my-track --name "Sprint 1"
      vibey roadmap create-sprint -t auth-system -n "MVP Implementation" -p high
      vibey roadmap create-sprint --track track_01JB3... --name "Sprint 2" --depends-on sprint_01JB3...
    """
    from vibey.cli.commands import create_sprint_cmd

    exit_code = create_sprint_cmd(
        track_id_or_slug=track,
        name=name,
        description=description,
        priority=priority,
        duration=duration,
        start=start,
        depends_on=list(depends_on)
    )
    sys.exit(exit_code)
```

### Command Implementation

```python
# vibey/cli/commands.py - Add create_sprint_cmd function

def create_sprint_cmd(
    track_id_or_slug: str,
    name: str,
    description: str = '',
    priority: str = 'medium',
    duration: str = '2 weeks',
    start: bool = False,
    depends_on: list = None
) -> int:
    """Create a new sprint in a track."""
    from pathlib import Path
    from datetime import datetime, timezone
    from vibey.roadmap.id_generator import generate_sprint_id
    from vibey.roadmap.models import (
        Sprint, SprintProgress, SprintMetadata, SprintSummary,
        Status, Priority
    )
    from vibey.roadmap.serialization import save_sprint, load_track, save_track
    from vibey.cli.roadmap_lib.filesystem import FileSystemManager

    depends_on = depends_on or []

    # Find repository root
    root = _find_repo_root()
    if not root:
        click.echo("❌ No .vibey/ directory found", err=True)
        return 1

    fs = FileSystemManager(root)

    # Resolve track (by ID or slug)
    track_id, track = _resolve_track(fs, track_id_or_slug)
    if not track:
        click.echo(f"❌ Track not found: {track_id_or_slug}", err=True)
        return 1

    # Generate sprint ID (ULID format)
    sprint_id = generate_sprint_id()

    # Check dependencies exist
    for dep_id in depends_on:
        if not _sprint_exists(fs, dep_id):
            click.echo(f"❌ Dependency sprint not found: {dep_id}", err=True)
            return 1

    # Create sprint object
    now = datetime.now(timezone.utc)
    sprint = Sprint(
        id=sprint_id,
        name=name,
        description=description,
        track_id=track_id,
        roadmap_id=track.roadmap_id,
        status=Status.IN_PROGRESS if start else Status.NOT_STARTED,
        priority=Priority(priority),
        blocked=len(depends_on) > 0,  # Blocked if has unmet dependencies
        created=now,
        started=now if start else None,
        progress=SprintProgress(
            development_tasks_total=0,
            development_tasks_completed=0,
            completion_gate_tasks_total=0,
            completion_gate_tasks_completed=0,
            production_gate_tasks_total=0,
            production_gate_tasks_completed=0,
            tasks_total=0,
            tasks_completed=0,
            completion_percent=0,
        ),
        tasks=[],  # No tasks yet
        development_gates=[],
        blocks=[],
        blocked_by=[],
        depends_on=depends_on,
        depended_on_by=[],
        metadata=SprintMetadata(
            last_updated=now,
            estimated_duration=duration,
            created_by='cli',
        ),
    )

    # Save sprint YAML file
    sprint_path = fs.roadmap_root / "sprints" / f"{sprint_id}.yaml"
    save_sprint(sprint, sprint_path)

    # Update track with sprint reference
    _add_sprint_to_track(fs, track, sprint)

    # Update dependent sprints (add this sprint to their depended_on_by)
    for dep_id in depends_on:
        _add_dependent_reference(fs, dep_id, sprint_id)

    # Sync to database if enabled
    _sync_sprint_to_db(sprint, root)

    click.echo(f"✅ Created sprint: {name}")
    click.echo(f"   ID: {sprint_id}")
    click.echo(f"   Track: {track.name} ({track_id})")
    click.echo(f"   File: {sprint_path.relative_to(root)}")
    click.echo(f"   Status: {'in_progress' if start else 'not_started'}")
    if depends_on:
        click.echo(f"   Depends on: {', '.join(depends_on)}")

    return 0


def _resolve_track(fs, track_id_or_slug):
    """Resolve track by ID or slug."""
    from vibey.roadmap.serialization import load_track

    # First, try as direct ID
    if track_id_or_slug.startswith('track_'):
        track_path = fs.roadmap_root / "tracks" / f"{track_id_or_slug}.yaml"
        if track_path.exists():
            return track_id_or_slug, load_track(track_path)

    # Search by slug or name
    tracks_dir = fs.roadmap_root / "tracks"
    for track_file in tracks_dir.glob("*.yaml"):
        track = load_track(track_file)
        if track.slug == track_id_or_slug or track.name.lower() == track_id_or_slug.lower():
            return track.id, track

    return None, None


def _sprint_exists(fs, sprint_id: str) -> bool:
    """Check if sprint exists."""
    sprint_path = fs.roadmap_root / "sprints" / f"{sprint_id}.yaml"
    return sprint_path.exists()


def _add_sprint_to_track(fs, track, sprint):
    """Add sprint summary to track."""
    from vibey.roadmap.models import SprintSummary
    from vibey.roadmap.serialization import save_track

    # Add sprint summary
    summary = SprintSummary(
        id=sprint.id,
        name=sprint.name,
        status=sprint.status,
        priority=sprint.priority,
    )
    track.sprints.append(summary)

    # Update track progress
    track.progress.sprints_total += 1

    # Save track
    track_path = fs.roadmap_root / "tracks" / f"{track.id}.yaml"
    save_track(track, track_path)


def _add_dependent_reference(fs, sprint_id: str, dependent_id: str):
    """Add dependent reference to a sprint's depended_on_by list."""
    from vibey.roadmap.serialization import load_sprint, save_sprint

    sprint_path = fs.roadmap_root / "sprints" / f"{sprint_id}.yaml"
    if sprint_path.exists():
        sprint = load_sprint(sprint_path)
        if dependent_id not in sprint.depended_on_by:
            sprint.depended_on_by.append(dependent_id)
        save_sprint(sprint, sprint_path)
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/cli/main.py` | Add `create-sprint` command definition |
| `vibey/cli/commands.py` | Add `create_sprint_cmd` implementation |

---

## Testing Strategy

```python
def test_create_sprint_basic(flat_roadmap_env):
    """Test basic sprint creation."""
    # First create a track
    runner = CliRunner()
    runner.invoke(cli, ['roadmap', 'create-track', '-n', 'Test Track'])

    # Then create sprint in track
    result = runner.invoke(cli, [
        'roadmap', 'create-sprint',
        '--track', 'test-track',
        '--name', 'Sprint 1',
    ])

    assert result.exit_code == 0
    assert 'Created sprint' in result.output
    assert 'Sprint 1' in result.output

    # Verify file created
    sprints_dir = flat_roadmap_env / ".vibey" / "roadmap" / "sprints"
    sprint_files = list(sprints_dir.glob("sprint_*.yaml"))
    assert len(sprint_files) == 1


def test_create_sprint_with_dependency(flat_roadmap_env):
    """Test sprint creation with dependency."""
    runner = CliRunner()

    # Create track and first sprint
    runner.invoke(cli, ['roadmap', 'create-track', '-n', 'Test Track'])
    runner.invoke(cli, ['roadmap', 'create-sprint', '-t', 'test-track', '-n', 'Sprint 1'])

    # Get sprint 1 ID from output
    sprints_dir = flat_roadmap_env / ".vibey" / "roadmap" / "sprints"
    sprint1_file = list(sprints_dir.glob("sprint_*.yaml"))[0]
    sprint1_id = sprint1_file.stem

    # Create sprint 2 depending on sprint 1
    result = runner.invoke(cli, [
        'roadmap', 'create-sprint',
        '-t', 'test-track',
        '-n', 'Sprint 2',
        '--depends-on', sprint1_id,
    ])

    assert result.exit_code == 0
    assert sprint1_id in result.output


def test_create_sprint_updates_track(flat_roadmap_env):
    """Sprint added to track's sprints list."""
    runner = CliRunner()
    runner.invoke(cli, ['roadmap', 'create-track', '-n', 'Test Track'])
    runner.invoke(cli, ['roadmap', 'create-sprint', '-t', 'test-track', '-n', 'Sprint 1'])

    # Load track and verify sprint reference
    tracks_dir = flat_roadmap_env / ".vibey" / "roadmap" / "tracks"
    track_file = list(tracks_dir.glob("track_*.yaml"))[0]
    track = load_track(track_file)

    assert len(track.sprints) == 1
    assert track.sprints[0].name == 'Sprint 1'
    assert track.progress.sprints_total == 1
```

---

## Success Criteria

- [ ] `vibey roadmap create-sprint --track X --name "Sprint 1"` works
- [ ] Sprint YAML created with ULID-based filename
- [ ] Sprint added to track's sprints list
- [ ] Track progress updated (sprints_total incremented)
- [ ] ULID generated using id_generator.py
- [ ] Track resolution by ID or slug
- [ ] Optional --depends-on for sprint dependencies
- [ ] Dependency validation (sprint must exist)
- [ ] Database sync if SQLite enabled

---

## Dependencies

- Task 001 (create track command) - for testing track resolution
- Task 005 (ULIDManager) - Already exists in id_generator.py

---

## Notes

Key considerations:
1. Track must exist before creating sprint
2. Track can be specified by ULID or slug
3. Dependencies are optional but validated
4. Sprint auto-blocked if it has unmet dependencies
5. Parent track's sprints list is updated automatically
