# Task 001: Add Create Track CLI Command

**Task ID:** dogfooding-bugs-05-task-001
**Bug Addressed:** #15 (No CLI Commands to Create Tracks, Sprints, or Tasks in ULID Structure)
**Complexity:** Medium
**Type:** Development

---

## Problem Statement

The CLI currently has no command to create new tracks in the ULID-based flat directory structure. Users must manually create YAML files and generate ULIDs, which is error-prone and time-consuming.

---

## Current State

```bash
# No create track command exists
vibey roadmap create track  # Would error: no such command

# Current workaround: manual file creation
cat > .vibey/roadmap/tracks/track_01JB3QVDZ8TRK9XN1FJFHGWPRM.yaml << 'EOF'
track:
  id: track_01JB3QVDZ8TRK9XN1FJFHGWPRM
  name: My New Track
  # ... 50+ lines of boilerplate
EOF
```

---

## Implementation

### CLI Command Definition

```python
# vibey/cli/main.py - Add to roadmap command group

@roadmap.command('create-track')
@click.option('--name', '-n', required=True, help='Track name')
@click.option('--slug', '-s', help='URL-friendly slug (generated from name if not provided)')
@click.option('--description', '-d', default='', help='Track description')
@click.option('--priority', '-p',
              type=click.Choice(['critical', 'high', 'medium', 'low']),
              default='medium', help='Track priority')
@click.option('--start', is_flag=True, help='Mark track as started immediately')
@click.pass_context
def roadmap_create_track(ctx, name: str, slug: str, description: str,
                         priority: str, start: bool):
    """Create a new track in the roadmap.

    Creates a new track YAML file using ULID-based naming in the flat structure.
    The track is automatically added to roadmap.yaml's track list.

    Examples:
      vibey roadmap create-track --name "Authentication System"
      vibey roadmap create-track -n "Performance Optimization" -p high
      vibey roadmap create-track --name "Bug Fixes" --slug bug-fixes --start
    """
    from vibey.cli.commands import create_track_cmd

    exit_code = create_track_cmd(
        name=name,
        slug=slug,
        description=description,
        priority=priority,
        start=start
    )
    sys.exit(exit_code)
```

### Command Implementation

```python
# vibey/cli/commands.py - Add create_track_cmd function

def create_track_cmd(
    name: str,
    slug: str = None,
    description: str = '',
    priority: str = 'medium',
    start: bool = False
) -> int:
    """Create a new track in the roadmap."""
    from pathlib import Path
    from datetime import datetime, timezone
    from vibey.roadmap.id_generator import generate_track_id
    from vibey.roadmap.models import Track, TrackProgress, TrackMetadata, Status, Priority
    from vibey.roadmap.serialization import save_track, load_roadmap, save_roadmap
    from vibey.cli.roadmap_lib.filesystem import FileSystemManager

    # Find repository root
    root = _find_repo_root()
    if not root:
        click.echo("❌ No .vibey/ directory found", err=True)
        return 1

    fs = FileSystemManager(root)

    # Generate track ID (ULID format)
    track_id = generate_track_id()

    # Generate slug from name if not provided
    if not slug:
        slug = _slugify(name)

    # Create track object
    now = datetime.now(timezone.utc)
    track = Track(
        id=track_id,
        name=name,
        slug=slug,
        description=description,
        roadmap_id=_get_roadmap_id(fs),
        status=Status.IN_PROGRESS if start else Status.NOT_STARTED,
        priority=Priority(priority),
        blocked=False,
        created=now,
        started=now if start else None,
        progress=TrackProgress(
            sprints_total=0,
            sprints_completed=0,
            tasks_total=0,
            tasks_completed=0,
            completion_percent=0,
        ),
        sprints=[],  # No sprints yet
        blocks=[],
        blocked_by=[],
        depends_on=[],
        depended_on_by=[],
        metadata=TrackMetadata(
            last_updated=now,
            created_by='cli',
        ),
    )

    # Save track YAML file
    track_path = fs.roadmap_root / "tracks" / f"{track_id}.yaml"
    save_track(track, track_path)

    # Update roadmap.yaml with new track summary
    _add_track_to_roadmap(fs, track)

    # Sync to database if enabled
    _sync_track_to_db(track, root)

    click.echo(f"✅ Created track: {name}")
    click.echo(f"   ID: {track_id}")
    click.echo(f"   File: {track_path.relative_to(root)}")
    click.echo(f"   Status: {'in_progress' if start else 'not_started'}")

    return 0


def _slugify(name: str) -> str:
    """Convert name to URL-friendly slug."""
    import re
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug


def _add_track_to_roadmap(fs, track):
    """Add track summary to roadmap.yaml."""
    from vibey.roadmap.serialization import load_roadmap, save_roadmap
    from vibey.roadmap.models import TrackSummary

    roadmap_path = fs.get_roadmap_path()
    if roadmap_path.exists():
        roadmap = load_roadmap(roadmap_path)

        # Add track summary
        summary = TrackSummary(
            id=track.id,
            name=track.name,
            status=track.status,
            priority=track.priority,
        )
        roadmap.tracks.append(summary)

        # Update roadmap progress
        roadmap.progress.tracks_total += 1

        save_roadmap(roadmap, roadmap_path)
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/cli/main.py` | Add `create-track` command definition |
| `vibey/cli/commands.py` | Add `create_track_cmd` implementation |

---

## Helper Functions Required

```python
def _find_repo_root() -> Optional[Path]:
    """Find repository root with .vibey/ directory."""
    root = Path.cwd()
    while root != root.parent:
        if (root / ".vibey").exists():
            return root
        root = root.parent
    return None


def _get_roadmap_id(fs) -> str:
    """Get roadmap ID from roadmap.yaml."""
    roadmap_path = fs.get_roadmap_path()
    if roadmap_path.exists():
        roadmap = load_roadmap(roadmap_path)
        return roadmap.id
    return "default-roadmap"


def _sync_track_to_db(track, root):
    """Sync track to SQLite database if enabled."""
    try:
        db_path = root / ".vibey" / "roadmap.db"
        if db_path.exists():
            from vibey.roadmap.serialization.sql_dumper import dump_track_to_db
            dump_track_to_db(track, db_path)
    except Exception as e:
        click.echo(f"⚠️  Database sync skipped: {e}", err=True)
```

---

## Testing Strategy

```python
def test_create_track_basic(flat_roadmap_env):
    """Test basic track creation."""
    from click.testing import CliRunner
    from vibey.cli.main import cli

    runner = CliRunner()
    result = runner.invoke(cli, [
        'roadmap', 'create-track',
        '--name', 'Test Track',
    ])

    assert result.exit_code == 0
    assert 'Created track' in result.output
    assert 'Test Track' in result.output

    # Verify file created
    tracks_dir = flat_roadmap_env / ".vibey" / "roadmap" / "tracks"
    track_files = list(tracks_dir.glob("track_*.yaml"))
    assert len(track_files) == 1


def test_create_track_with_options(flat_roadmap_env):
    """Test track creation with all options."""
    runner = CliRunner()
    result = runner.invoke(cli, [
        'roadmap', 'create-track',
        '--name', 'High Priority Track',
        '--slug', 'high-priority',
        '--description', 'Critical work',
        '--priority', 'high',
        '--start',
    ])

    assert result.exit_code == 0
    assert 'in_progress' in result.output


def test_create_track_updates_roadmap(flat_roadmap_env):
    """Track summary added to roadmap.yaml."""
    runner = CliRunner()
    runner.invoke(cli, ['roadmap', 'create-track', '-n', 'New Track'])

    roadmap_path = flat_roadmap_env / ".vibey" / "roadmap" / "roadmap.yaml"
    roadmap = load_roadmap(roadmap_path)

    # Find the new track
    new_track = next((t for t in roadmap.tracks if t.name == 'New Track'), None)
    assert new_track is not None
    assert new_track.id.startswith('track_')
```

---

## Success Criteria

- [ ] `vibey roadmap create-track --name "Track Name"` works
- [ ] Track YAML created with ULID-based filename
- [ ] Track added to roadmap.yaml tracks list
- [ ] ULID generated using id_generator.py
- [ ] Optional slug generation from name
- [ ] Optional --start flag to mark as in_progress
- [ ] Database sync if SQLite enabled
- [ ] User-friendly output with track ID and file path

---

## Dependencies

- Task 005 (ULIDManager) - Already exists in id_generator.py!

---

## Notes

The `id_generator.py` module already provides `generate_track_id()` which returns properly formatted ULID strings like `track_01JB3QVDZ8TRK9XN1FJFHGWPRM`. This task primarily involves:

1. CLI command wiring (Click decorator)
2. Track model instantiation
3. YAML serialization
4. Roadmap.yaml update
5. Optional database sync

The heavy lifting of ID generation is already done.
