# Task 014: Add Validation to Detect Sync Discrepancies

**Task ID:** dogfooding-bugs-02-task-014
**Bug Addressed:** #12 (New tracks not syncing to roadmap.yaml)
**Complexity:** Medium
**Type:** Development

---

## Problem Statement

The system should proactively detect when roadmap.yaml is out of sync with ULID files, warning users and suggesting remediation.

---

## Implementation

### Validation Function

```python
# vibey/operations/roadmap/validation.py

from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml
import logging

logger = logging.getLogger(__name__)


class SyncDiscrepancy:
    """Represents a sync discrepancy between ULID files and roadmap.yaml."""

    def __init__(
        self,
        discrepancy_type: str,
        entity_type: str,
        entity_id: str,
        details: str,
    ):
        self.type = discrepancy_type  # 'missing', 'extra', 'mismatch'
        self.entity_type = entity_type  # 'track', 'sprint', 'task'
        self.entity_id = entity_id
        self.details = details

    def __str__(self):
        return f"{self.type.upper()}: {self.entity_type} '{self.entity_id}' - {self.details}"


def validate_sync_status(roadmap_dir: Path) -> Dict[str, Any]:
    """
    Validate sync status between ULID files and roadmap.yaml.

    Args:
        roadmap_dir: Path to .vibey/roadmap directory

    Returns:
        Validation report with discrepancies and recommendations
    """
    roadmap_path = roadmap_dir / "roadmap.yaml"
    tracks_dir = roadmap_dir / "tracks"

    discrepancies: List[SyncDiscrepancy] = []

    # Load roadmap.yaml
    with open(roadmap_path, 'r') as f:
        data = yaml.safe_load(f)

    roadmap_data = data.get('roadmap', {})
    yaml_tracks = {t['id']: t for t in roadmap_data.get('tracks', [])}

    # Discover ULID tracks
    ulid_tracks = {}
    if tracks_dir.exists():
        for track_file in tracks_dir.glob("*.yaml"):
            try:
                track_data = yaml.safe_load(track_file.read_text())
                track_info = track_data.get('track', {})
                track_id = track_info.get('id', track_file.stem)
                ulid_tracks[track_id] = track_info
            except Exception as e:
                logger.warning(f"Failed to parse {track_file}: {e}")

    # Check for missing tracks (in ULID but not in YAML)
    for track_id in ulid_tracks:
        if track_id not in yaml_tracks:
            discrepancies.append(SyncDiscrepancy(
                discrepancy_type='missing',
                entity_type='track',
                entity_id=track_id,
                details=f"Track exists in tracks/{track_id}.yaml but not in roadmap.yaml",
            ))

    # Check for extra tracks (in YAML but not in ULID)
    for track_id in yaml_tracks:
        if track_id not in ulid_tracks:
            discrepancies.append(SyncDiscrepancy(
                discrepancy_type='extra',
                entity_type='track',
                entity_id=track_id,
                details=f"Track in roadmap.yaml but no tracks/{track_id}.yaml file",
            ))

    # Check for mismatches (both exist but data differs)
    for track_id in set(yaml_tracks.keys()) & set(ulid_tracks.keys()):
        yaml_track = yaml_tracks[track_id]
        ulid_track = ulid_tracks[track_id]

        for field in ['name', 'status', 'priority']:
            yaml_value = yaml_track.get(field)
            ulid_value = ulid_track.get(field)
            if yaml_value != ulid_value:
                discrepancies.append(SyncDiscrepancy(
                    discrepancy_type='mismatch',
                    entity_type='track',
                    entity_id=track_id,
                    details=f"Field '{field}': yaml='{yaml_value}' vs ulid='{ulid_value}'",
                ))

    # Validate progress counters
    progress = roadmap_data.get('progress', {})
    actual_track_count = len(ulid_tracks)
    reported_track_count = progress.get('tracks_total', 0)

    if actual_track_count != reported_track_count:
        discrepancies.append(SyncDiscrepancy(
            discrepancy_type='mismatch',
            entity_type='progress',
            entity_id='tracks_total',
            details=f"Progress shows {reported_track_count} tracks, but {actual_track_count} exist",
        ))

    # Build report
    is_synced = len(discrepancies) == 0

    return {
        'is_synced': is_synced,
        'discrepancies': discrepancies,
        'ulid_track_count': len(ulid_tracks),
        'yaml_track_count': len(yaml_tracks),
        'recommendation': None if is_synced else 'Run `vibey roadmap sync` to fix discrepancies',
    }


def print_sync_validation_report(report: Dict[str, Any]) -> None:
    """Print a formatted sync validation report."""
    if report['is_synced']:
        print("✓ roadmap.yaml is in sync with ULID files")
        print(f"  Tracks: {report['ulid_track_count']}")
        return

    print("✗ Sync discrepancies detected:")
    print(f"  ULID files: {report['ulid_track_count']} tracks")
    print(f"  roadmap.yaml: {report['yaml_track_count']} tracks")
    print()

    for d in report['discrepancies']:
        print(f"  • {d}")

    print()
    print(f"  Recommendation: {report['recommendation']}")
```

### Integration with Existing Validation

```python
# Add to existing validation flow

def validate_roadmap(roadmap_dir: Path, include_sync: bool = True) -> Dict[str, Any]:
    """
    Comprehensive roadmap validation.

    Args:
        roadmap_dir: Path to .vibey/roadmap
        include_sync: Whether to check sync status

    Returns:
        Validation results
    """
    results = {
        'valid': True,
        'errors': [],
        'warnings': [],
    }

    # Existing validations...
    # ...

    # Add sync validation
    if include_sync:
        sync_report = validate_sync_status(roadmap_dir)
        if not sync_report['is_synced']:
            results['warnings'].append(
                f"roadmap.yaml out of sync: {len(sync_report['discrepancies'])} discrepancies. "
                f"Run `vibey roadmap sync` to fix."
            )

    return results
```

### CLI Integration

```python
# vibey/cli/commands.py

@roadmap.command()
@click.option('--include-sync/--no-sync', default=True, help='Check sync status')
@click.pass_context
def validate(ctx, include_sync):
    """Validate roadmap structure and sync status."""
    from vibey.operations.roadmap.validation import validate_roadmap, validate_sync_status

    root_dir = ctx.obj.get('root_dir', Path.cwd())
    roadmap_dir = root_dir / ".vibey" / "roadmap"

    # Run validation
    results = validate_roadmap(roadmap_dir, include_sync=include_sync)

    # Display results
    if results['valid'] and not results['warnings']:
        click.echo("✓ Roadmap validation passed")
    else:
        if results['errors']:
            click.echo("✗ Validation errors:", err=True)
            for error in results['errors']:
                click.echo(f"  • {error}", err=True)

        if results['warnings']:
            click.echo("\n⚠ Warnings:")
            for warning in results['warnings']:
                click.echo(f"  • {warning}")

    ctx.exit(0 if results['valid'] else 1)
```

---

## Files to Create/Modify

| File | Changes |
|------|---------|
| `vibey/operations/roadmap/validation.py` | Add sync validation functions |
| `vibey/cli/commands.py` | Add/update `validate` command |

---

## Testing Strategy

```python
def test_validate_sync_detects_missing_track(tmp_path):
    """Detect track in ULID but not in roadmap.yaml."""
    # Setup with extra ULID track
    ...

    report = validate_sync_status(tmp_path / ".vibey/roadmap")

    assert not report['is_synced']
    assert any(d.type == 'missing' for d in report['discrepancies'])


def test_validate_sync_detects_extra_track(tmp_path):
    """Detect track in roadmap.yaml but not in ULID."""
    # Setup with extra YAML track
    ...

    report = validate_sync_status(tmp_path / ".vibey/roadmap")

    assert not report['is_synced']
    assert any(d.type == 'extra' for d in report['discrepancies'])


def test_validate_sync_detects_mismatch(tmp_path):
    """Detect data mismatch between ULID and YAML."""
    # Setup with different status values
    ...

    report = validate_sync_status(tmp_path / ".vibey/roadmap")

    assert not report['is_synced']
    assert any(d.type == 'mismatch' for d in report['discrepancies'])


def test_validate_sync_all_synced(tmp_path):
    """Report success when in sync."""
    # Setup with matching data
    ...

    report = validate_sync_status(tmp_path / ".vibey/roadmap")

    assert report['is_synced']
    assert len(report['discrepancies']) == 0
```

---

## Success Criteria

- [ ] `validate_sync_status()` detects missing tracks
- [ ] `validate_sync_status()` detects extra tracks
- [ ] `validate_sync_status()` detects data mismatches
- [ ] Progress counter validation works
- [ ] CLI `validate` command shows sync warnings
- [ ] Recommendation to run sync is clear

---

## Dependencies

- Task 012 (sync functions for remediation)
- Task 013 (CLI sync command to recommend)

---

## Notes

This validation runs automatically during:
- `vibey roadmap status` (optional, can be disabled)
- `vibey roadmap validate` (explicit)
- Pre-commit hooks (future)

The warning should be informative but not block operations.
