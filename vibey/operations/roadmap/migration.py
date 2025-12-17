"""
Roadmap Migration Module

Provides utilities to migrate existing vibey roadmaps from legacy formats
to the new directory structure with SQLite backend.

Sprint 13 Task 008: Create migration script for existing roadmaps

Usage:
    from vibey.operations.roadmap.migration import (
        detect_format_version,
        migrate_roadmap,
        rollback_migration,
    )

    # Detect current format
    version = detect_format_version(Path('.'))

    # Dry run to preview changes
    result = migrate_roadmap(Path('.'), dry_run=True)

    # Execute migration
    result = migrate_roadmap(Path('.'), dry_run=False)

    # Rollback if needed
    rollback_migration(Path('.'), result.backup_path)
"""

import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import yaml


@dataclass
class MigrationResult:
    """Result of a migration operation."""
    success: bool
    format_from: str
    format_to: str
    backup_path: Optional[Path] = None
    tracks_migrated: int = 0
    sprints_migrated: int = 0
    tasks_migrated: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def summary(self) -> str:
        """Generate human-readable summary."""
        status = "SUCCESS" if self.success else "FAILED"
        lines = [
            f"Migration {status}",
            f"  Format: {self.format_from} -> {self.format_to}",
            f"  Tracks: {self.tracks_migrated}",
            f"  Sprints: {self.sprints_migrated}",
            f"  Tasks: {self.tasks_migrated}",
        ]
        if self.backup_path:
            lines.append(f"  Backup: {self.backup_path}")
        if self.errors:
            lines.append(f"  Errors: {len(self.errors)}")
            for e in self.errors[:3]:
                lines.append(f"    - {e}")
        if self.warnings:
            lines.append(f"  Warnings: {len(self.warnings)}")
        return "\n".join(lines)


class FormatVersion:
    """Known roadmap format versions."""
    UNKNOWN = "unknown"
    V1_FLAT = "v1_flat"           # Single roadmap.yaml with embedded data
    V2_HIERARCHY = "v2_hierarchy"  # track/sprint/task directory structure
    V3_SQLITE = "v3_sqlite"        # Hierarchy + SQLite database


def detect_format_version(root_dir: Path) -> str:
    """
    Detect the current roadmap format version.

    Args:
        root_dir: Repository root directory

    Returns:
        Format version string (FormatVersion constant)
    """
    vibey_dir = root_dir / ".vibey"

    if not vibey_dir.exists():
        return FormatVersion.UNKNOWN

    roadmap_dir = vibey_dir / "roadmap"
    roadmap_yaml = vibey_dir / "roadmap.yaml"
    roadmap_db = vibey_dir / "roadmap.db"

    # Check for V3: has database AND flat structure (tracks/, sprints/, tasks/ directories)
    if roadmap_db.exists() and roadmap_dir.exists():
        tracks_dir = roadmap_dir / "tracks"
        sprints_dir = roadmap_dir / "sprints"
        tasks_dir = roadmap_dir / "tasks"

        # V3 flat structure: has tracks/, sprints/, tasks/ directories
        if tracks_dir.exists() and any(tracks_dir.glob("*.yaml")):
            return FormatVersion.V3_SQLITE

        # Legacy V3: hierarchical structure with database (shouldn't exist anymore)
        track_dirs = [d for d in roadmap_dir.iterdir()
                      if d.is_dir() and not d.name.startswith('.') and d.name not in ('tracks', 'sprints', 'tasks', 'context')]
        if track_dirs and any((d / "track.yaml").exists() for d in track_dirs):
            return FormatVersion.V3_SQLITE

    # Check for V2: hierarchical without database
    if roadmap_dir.exists():
        track_dirs = [d for d in roadmap_dir.iterdir()
                      if d.is_dir() and not d.name.startswith('.') and d.name not in ('tracks', 'sprints', 'tasks', 'context')]
        if track_dirs and any((d / "track.yaml").exists() for d in track_dirs):
            return FormatVersion.V2_HIERARCHY

    # Check for V1: flat structure (single roadmap.yaml with embedded data)
    if roadmap_yaml.exists():
        data = _parse_yaml_safe(roadmap_yaml)
        if data and 'roadmap' in data:
            roadmap_data = data['roadmap']
            # V1 has tracks embedded directly
            if 'tracks' in roadmap_data and isinstance(roadmap_data['tracks'], list):
                # Check if tracks contain full task data (V1) or just summaries (V2+)
                tracks = roadmap_data['tracks']
                if tracks and isinstance(tracks[0], dict):
                    if 'sprints' in tracks[0] and isinstance(tracks[0]['sprints'], list):
                        sprints = tracks[0]['sprints']
                        if sprints and 'tasks' in sprints[0]:
                            # Has full embedded tasks - this is V1
                            return FormatVersion.V1_FLAT

    return FormatVersion.UNKNOWN


def _parse_yaml_safe(file_path: Path) -> Optional[Dict]:
    """Safely parse a YAML file."""
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception:
        return None


def _write_yaml(file_path: Path, data: Dict) -> None:
    """Write data to YAML file with proper formatting."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def create_backup(root_dir: Path) -> Path:
    """
    Create a backup of the current roadmap state.

    Args:
        root_dir: Repository root directory

    Returns:
        Path to backup directory
    """
    vibey_dir = root_dir / ".vibey"
    backup_dir = vibey_dir / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"roadmap-backup-{timestamp}"

    # Copy roadmap directory
    roadmap_dir = vibey_dir / "roadmap"
    if roadmap_dir.exists():
        shutil.copytree(roadmap_dir, backup_path / "roadmap")

    # Copy roadmap.yaml
    roadmap_yaml = vibey_dir / "roadmap.yaml"
    if roadmap_yaml.exists():
        shutil.copy2(roadmap_yaml, backup_path / "roadmap.yaml")

    # Copy roadmap.db if exists
    roadmap_db = vibey_dir / "roadmap.db"
    if roadmap_db.exists():
        shutil.copy2(roadmap_db, backup_path / "roadmap.db")

    return backup_path


def migrate_v1_to_v2(root_dir: Path, dry_run: bool = True) -> MigrationResult:
    """
    Migrate from V1 (flat) to V2 (hierarchical) format.

    Args:
        root_dir: Repository root directory
        dry_run: If True, only simulate migration

    Returns:
        MigrationResult with details
    """
    result = MigrationResult(
        success=False,
        format_from=FormatVersion.V1_FLAT,
        format_to=FormatVersion.V2_HIERARCHY,
    )

    vibey_dir = root_dir / ".vibey"
    roadmap_yaml = vibey_dir / "roadmap.yaml"

    if not roadmap_yaml.exists():
        result.errors.append("roadmap.yaml not found")
        return result

    data = _parse_yaml_safe(roadmap_yaml)
    if not data or 'roadmap' not in data:
        result.errors.append("Invalid roadmap.yaml format")
        return result

    roadmap_data = data['roadmap']
    tracks = roadmap_data.get('tracks', [])

    if not dry_run:
        result.backup_path = create_backup(root_dir)

    roadmap_dir = vibey_dir / "roadmap"

    for track in tracks:
        if not isinstance(track, dict):
            continue

        track_id = track.get('id', '')
        if not track_id:
            result.warnings.append(f"Track missing ID, skipping")
            continue

        result.tracks_migrated += 1
        track_dir = roadmap_dir / track_id

        # Create track.yaml with summary (no embedded sprints)
        track_summary = {
            'track': {
                'id': track_id,
                'name': track.get('name', track_id),
                'status': track.get('status', 'not_started'),
                'description': track.get('description', ''),
                'progress': track.get('progress', {}),
                'sprints': [],  # Will be populated with summaries
            }
        }

        sprints = track.get('sprints', [])
        for sprint in sprints:
            if not isinstance(sprint, dict):
                continue

            sprint_id = sprint.get('id', '')
            if not sprint_id:
                result.warnings.append(f"Sprint in {track_id} missing ID, skipping")
                continue

            result.sprints_migrated += 1
            sprint_dir = track_dir / sprint_id

            # Add sprint summary to track
            track_summary['track']['sprints'].append({
                'id': sprint_id,
                'name': sprint.get('name', sprint_id),
                'status': sprint.get('status', 'not_started'),
            })

            # Create sprint.yaml with summary (no embedded tasks)
            sprint_data = {
                'sprint': {
                    'id': sprint_id,
                    'name': sprint.get('name', sprint_id),
                    'track_id': track_id,
                    'status': sprint.get('status', 'not_started'),
                    'description': sprint.get('description', ''),
                    'progress': sprint.get('progress', {}),
                    'tasks': [],  # Will be populated with summaries
                }
            }

            tasks = sprint.get('tasks', [])
            for task in tasks:
                if not isinstance(task, dict):
                    continue

                task_id = task.get('id', '')
                if not task_id:
                    result.warnings.append(f"Task in {sprint_id} missing ID, skipping")
                    continue

                result.tasks_migrated += 1
                task_dir = sprint_dir / task_id

                # Add task summary to sprint
                sprint_data['sprint']['tasks'].append({
                    'id': task_id,
                    'title': task.get('title', task_id),
                    'status': task.get('status', 'not_started'),
                    'task_type': task.get('task_type', 'development'),
                })

                # Create task.yaml with full task data
                task_data = {
                    'task': {
                        'id': task_id,
                        'sprint_id': sprint_id,
                        'track_id': track_id,
                        'title': task.get('title', task_id),
                        'status': task.get('status', 'not_started'),
                        'description': task.get('description', ''),
                        'task_type': task.get('task_type', 'development'),
                        'blocked': task.get('blocked', False),
                        'created': task.get('created'),
                        'started': task.get('started'),
                        'completed': task.get('completed'),
                        'commits': task.get('commits', []),
                        'deliverables': task.get('deliverables', []),
                        'dependencies': task.get('dependencies', []),
                    }
                }

                if not dry_run:
                    _write_yaml(task_dir / "task.yaml", task_data)

            if not dry_run:
                _write_yaml(sprint_dir / "sprint.yaml", sprint_data)

        if not dry_run:
            _write_yaml(track_dir / "track.yaml", track_summary)

    # Update main roadmap.yaml to just be a summary
    if not dry_run:
        summary_data = {
            'roadmap': {
                'id': roadmap_data.get('id', 'default'),
                'name': roadmap_data.get('name', 'Roadmap'),
                'version': roadmap_data.get('version', '1.0.0'),
                'tracks': [{'id': t.get('id'), 'name': t.get('name')}
                           for t in tracks if isinstance(t, dict) and t.get('id')],
            }
        }
        _write_yaml(roadmap_yaml, summary_data)

    result.success = True
    return result


def migrate_v2_to_v3(root_dir: Path, dry_run: bool = True) -> MigrationResult:
    """
    Migrate from V2 (hierarchical) to V3 (SQLite) format.

    Args:
        root_dir: Repository root directory
        dry_run: If True, only simulate migration

    Returns:
        MigrationResult with details
    """
    result = MigrationResult(
        success=False,
        format_from=FormatVersion.V2_HIERARCHY,
        format_to=FormatVersion.V3_SQLITE,
    )

    vibey_dir = root_dir / ".vibey"
    roadmap_dir = vibey_dir / "roadmap"

    if not roadmap_dir.exists():
        result.errors.append("roadmap directory not found")
        return result

    if not dry_run:
        result.backup_path = create_backup(root_dir)

    # Count entities
    for track_dir in roadmap_dir.iterdir():
        if not track_dir.is_dir() or track_dir.name.startswith('.'):
            continue

        track_yaml = track_dir / "track.yaml"
        if not track_yaml.exists():
            continue

        result.tracks_migrated += 1

        for sprint_dir in track_dir.iterdir():
            if not sprint_dir.is_dir() or sprint_dir.name.startswith('.') or sprint_dir.name == 'context':
                continue

            sprint_yaml = sprint_dir / "sprint.yaml"
            if not sprint_yaml.exists():
                continue

            result.sprints_migrated += 1

            for task_dir in sprint_dir.iterdir():
                if not task_dir.is_dir() or task_dir.name.startswith('.') or task_dir.name == 'context':
                    continue

                task_yaml = task_dir / "task.yaml"
                if task_yaml.exists():
                    result.tasks_migrated += 1

    if not dry_run:
        try:
            # Initialize database
            from vibey.roadmap.database.schema import init_database
            from vibey.roadmap.serialization.backend import SyncManager

            db_path = vibey_dir / "roadmap.db"

            # Remove existing database if present
            if db_path.exists():
                db_path.unlink()

            # Initialize fresh database
            init_database(db_path)

            # Rebuild from YAML
            sync = SyncManager(roadmap_dir=roadmap_dir, db_path=db_path)
            sync.rebuild(force=True)

            result.success = True

        except Exception as e:
            result.errors.append(f"Database initialization failed: {e}")
            return result
    else:
        result.success = True

    return result


def migrate_roadmap(root_dir: Path, dry_run: bool = True) -> MigrationResult:
    """
    Migrate roadmap to the latest format.

    Automatically detects current format and migrates through each version
    as needed to reach the latest format (V3 with SQLite).

    Args:
        root_dir: Repository root directory
        dry_run: If True, only simulate migration

    Returns:
        MigrationResult with details
    """
    current_version = detect_format_version(root_dir)

    if current_version == FormatVersion.UNKNOWN:
        return MigrationResult(
            success=False,
            format_from=current_version,
            format_to=FormatVersion.V3_SQLITE,
            errors=["Unable to detect roadmap format. Is this a vibey project?"],
        )

    if current_version == FormatVersion.V3_SQLITE:
        return MigrationResult(
            success=True,
            format_from=current_version,
            format_to=FormatVersion.V3_SQLITE,
            warnings=["Already at latest format (V3 with SQLite)"],
        )

    # Migrate through versions
    if current_version == FormatVersion.V1_FLAT:
        result = migrate_v1_to_v2(root_dir, dry_run)
        if not result.success:
            return result

        # Continue to V3
        if not dry_run:
            current_version = FormatVersion.V2_HIERARCHY

    if current_version == FormatVersion.V2_HIERARCHY:
        result = migrate_v2_to_v3(root_dir, dry_run)
        return result

    return MigrationResult(
        success=False,
        format_from=current_version,
        format_to=FormatVersion.V3_SQLITE,
        errors=[f"Unsupported format version: {current_version}"],
    )


def rollback_migration(root_dir: Path, backup_path: Path) -> bool:
    """
    Rollback a migration using a backup.

    Args:
        root_dir: Repository root directory
        backup_path: Path to backup created during migration

    Returns:
        True if rollback succeeded
    """
    if not backup_path.exists():
        return False

    vibey_dir = root_dir / ".vibey"

    # Remove current files
    roadmap_dir = vibey_dir / "roadmap"
    if roadmap_dir.exists():
        shutil.rmtree(roadmap_dir)

    roadmap_yaml = vibey_dir / "roadmap.yaml"
    if roadmap_yaml.exists():
        roadmap_yaml.unlink()

    roadmap_db = vibey_dir / "roadmap.db"
    if roadmap_db.exists():
        roadmap_db.unlink()

    # Restore from backup
    backup_roadmap = backup_path / "roadmap"
    if backup_roadmap.exists():
        shutil.copytree(backup_roadmap, roadmap_dir)

    backup_yaml = backup_path / "roadmap.yaml"
    if backup_yaml.exists():
        shutil.copy2(backup_yaml, roadmap_yaml)

    backup_db = backup_path / "roadmap.db"
    if backup_db.exists():
        shutil.copy2(backup_db, roadmap_db)

    return True


def validate_migration(root_dir: Path) -> List[str]:
    """
    Validate that a migration was successful.

    Args:
        root_dir: Repository root directory

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    version = detect_format_version(root_dir)
    if version != FormatVersion.V3_SQLITE:
        errors.append(f"Expected V3_SQLITE format, got {version}")
        return errors

    vibey_dir = root_dir / ".vibey"

    # Check database exists and is valid
    db_path = vibey_dir / "roadmap.db"
    if not db_path.exists():
        errors.append("Database file missing")
    else:
        import sqlite3
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            if result != 'ok':
                errors.append(f"Database integrity check failed: {result}")
            conn.close()
        except Exception as e:
            errors.append(f"Database validation failed: {e}")

    # Check flat directory structure
    roadmap_dir = vibey_dir / "roadmap"

    if not roadmap_dir.exists():
        errors.append("Roadmap directory missing")
    else:
        # Check for flat structure directories
        tracks_dir = roadmap_dir / "tracks"
        sprints_dir = roadmap_dir / "sprints"
        tasks_dir = roadmap_dir / "tasks"

        if not tracks_dir.exists():
            errors.append("Flat structure: tracks/ directory missing")
        else:
            track_count = len(list(tracks_dir.glob("*.yaml")))
            if track_count == 0:
                errors.append("No track YAML files found in tracks/")

        if not sprints_dir.exists():
            errors.append("Flat structure: sprints/ directory missing")

        if not tasks_dir.exists():
            errors.append("Flat structure: tasks/ directory missing")

    return errors
