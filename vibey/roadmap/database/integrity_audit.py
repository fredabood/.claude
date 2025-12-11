"""
File-Based Integrity Audit Module

This module builds computed databases by walking the filesystem and counting
actual YAML files, rather than relying on declared counters in the YAML files.

Used for Sprint 11 "Data Validation & Integrity Audit" to:
1. Build a "computed" database from actual file counts
2. Build a "declared" database from YAML counter fields
3. Compare the two to find discrepancies
4. Generate audit reports

The key insight is that declared counters (like progress.tasks_total in sprint.yaml)
should match actual task.yaml file counts. When they don't, there's data drift.

Usage:
    from vibey.roadmap.database.integrity_audit import (
        build_computed_database,
        build_declared_database,
        audit_discrepancies
    )

    # Build databases
    computed_db = build_computed_database(Path(".vibey/roadmap"))
    declared_db = build_declared_database(Path(".vibey/roadmap"))

    # Compare
    report = audit_discrepancies(computed_db, declared_db)
    print(report.summary())
"""

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import yaml


@dataclass
class FileCount:
    """Computed file count for a roadmap entity."""
    entity_type: str  # 'track', 'sprint', 'task'
    entity_id: str
    parent_id: Optional[str]
    file_path: Path
    child_count: int = 0  # sprints for track, tasks for sprint
    status: Optional[str] = None
    name: Optional[str] = None


@dataclass
class DeclaredProgress:
    """Declared progress counters from YAML."""
    entity_type: str
    entity_id: str
    parent_id: Optional[str]
    # Track-level counters
    declared_sprints_total: Optional[int] = None
    declared_sprints_completed: Optional[int] = None
    declared_tasks_total: Optional[int] = None
    declared_tasks_completed: Optional[int] = None
    declared_completion_percent: Optional[float] = None
    # Sprint-level counters
    development_tasks_total: Optional[int] = None
    development_tasks_completed: Optional[int] = None
    completion_gate_tasks_total: Optional[int] = None
    completion_gate_tasks_completed: Optional[int] = None
    production_gate_tasks_total: Optional[int] = None
    production_gate_tasks_completed: Optional[int] = None
    tasks_total: Optional[int] = None
    tasks_completed: Optional[int] = None
    completion_percent: Optional[float] = None


@dataclass
class Discrepancy:
    """A single discrepancy between computed and declared values."""
    entity_type: str
    entity_id: str
    field_name: str
    computed_value: Any
    declared_value: Any
    difference: Any
    severity: str  # 'critical', 'warning', 'info'


@dataclass
class EmbeddedSummaryDiscrepancy:
    """A discrepancy between embedded sprint summary and actual sprint data."""
    track_id: str
    sprint_id: str
    field_name: str
    embedded_value: Any
    actual_value: Any
    severity: str  # 'critical', 'warning', 'info'
    message: str


@dataclass
class EmbeddedSummaryReport:
    """Report for embedded sprint summary validation."""
    track_id: str
    discrepancies: List[EmbeddedSummaryDiscrepancy] = field(default_factory=list)
    orphaned_summaries: List[str] = field(default_factory=list)  # Sprint IDs with no matching sprint.yaml
    missing_summaries: List[str] = field(default_factory=list)   # Sprint directories with no embedded summary

    @property
    def has_issues(self) -> bool:
        return bool(self.discrepancies or self.orphaned_summaries or self.missing_summaries)

    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [f"Track: {self.track_id}"]
        if not self.has_issues:
            lines.append("  ✓ All embedded summaries match actual sprint data")
            return "\n".join(lines)

        if self.orphaned_summaries:
            lines.append(f"  Orphaned summaries (no sprint.yaml): {', '.join(self.orphaned_summaries)}")
        if self.missing_summaries:
            lines.append(f"  Missing summaries (sprint exists but not in track.yaml): {', '.join(self.missing_summaries)}")
        for d in self.discrepancies:
            lines.append(f"  {d.sprint_id}.{d.field_name}: embedded={d.embedded_value}, actual={d.actual_value}")
        return "\n".join(lines)


@dataclass
class AuditReport:
    """Full audit report with all discrepancies."""
    computed_counts: Dict[str, FileCount]
    declared_progress: Dict[str, DeclaredProgress]
    discrepancies: List[Discrepancy] = field(default_factory=list)

    @property
    def critical_count(self) -> int:
        return sum(1 for d in self.discrepancies if d.severity == 'critical')

    @property
    def warning_count(self) -> int:
        return sum(1 for d in self.discrepancies if d.severity == 'warning')

    @property
    def info_count(self) -> int:
        return sum(1 for d in self.discrepancies if d.severity == 'info')

    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            "=" * 70,
            "INTEGRITY AUDIT REPORT",
            "=" * 70,
            "",
            f"Total entities scanned: {len(self.computed_counts)}",
            f"Discrepancies found: {len(self.discrepancies)}",
            f"  Critical: {self.critical_count}",
            f"  Warnings: {self.warning_count}",
            f"  Info: {self.info_count}",
            "",
        ]

        if self.discrepancies:
            lines.append("DISCREPANCIES:")
            lines.append("-" * 50)

            for d in sorted(self.discrepancies, key=lambda x: (x.severity, x.entity_id)):
                severity_icon = {"critical": "!!!", "warning": "!!", "info": "!"}[d.severity]
                lines.append(
                    f"  {severity_icon} {d.entity_type}/{d.entity_id}: "
                    f"{d.field_name} = {d.declared_value} (declared) vs "
                    f"{d.computed_value} (computed)"
                )
        else:
            lines.append("No discrepancies found. All counters match file counts.")

        lines.append("")
        lines.append("=" * 70)
        return "\n".join(lines)


def _parse_yaml_safe(file_path: Path) -> Optional[Dict]:
    """Safely parse a YAML file."""
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception:
        return None


def count_files_in_directory(
    roadmap_root: Path,
) -> Tuple[Dict[str, FileCount], Dict[str, int]]:
    """
    Walk the roadmap directory and count actual files (flat structure).

    Uses flat structure:
    - tracks/{track_id}.yaml
    - sprints/{sprint_id}.yaml
    - tasks/{task_id}.yaml

    Returns:
        Tuple of (file_counts, task_statuses)
        - file_counts: Dict mapping entity_id to FileCount
        - task_statuses: Dict mapping task_id to status (for computing completed counts)
    """
    file_counts: Dict[str, FileCount] = {}
    task_statuses: Dict[str, str] = {}

    if not roadmap_root.exists():
        return file_counts, task_statuses

    tracks_dir = roadmap_root / "tracks"
    sprints_dir = roadmap_root / "sprints"
    tasks_dir = roadmap_root / "tasks"

    # Build lookup tables for relationships
    # task_id -> task_info (including sprint_id, track_id)
    task_by_id: Dict[str, Dict] = {}
    # sprint_id -> sprint_info (including track_id)
    sprint_by_id: Dict[str, Dict] = {}
    # track_id -> track_info
    track_by_id: Dict[str, Dict] = {}

    # Load all tasks
    if tasks_dir.exists():
        for task_yaml in tasks_dir.glob("*.yaml"):
            if task_yaml.name.startswith('.'):
                continue
            task_data = _parse_yaml_safe(task_yaml)
            if not task_data or 'task' not in task_data:
                continue
            task_info = task_data['task']
            task_id = task_info.get('id', task_yaml.stem)
            task_info['_file_path'] = task_yaml
            task_by_id[task_id] = task_info

    # Load all sprints
    if sprints_dir.exists():
        for sprint_yaml in sprints_dir.glob("*.yaml"):
            if sprint_yaml.name.startswith('.'):
                continue
            sprint_data = _parse_yaml_safe(sprint_yaml)
            if not sprint_data or 'sprint' not in sprint_data:
                continue
            sprint_info = sprint_data['sprint']
            sprint_id = sprint_info.get('id', sprint_yaml.stem)
            sprint_info['_file_path'] = sprint_yaml
            sprint_by_id[sprint_id] = sprint_info

    # Load all tracks
    if tracks_dir.exists():
        for track_yaml in tracks_dir.glob("*.yaml"):
            if track_yaml.name.startswith('.'):
                continue
            track_data = _parse_yaml_safe(track_yaml)
            if not track_data or 'track' not in track_data:
                continue
            track_info = track_data['track']
            track_id = track_info.get('id', track_yaml.stem)
            track_info['_file_path'] = track_yaml
            track_by_id[track_id] = track_info

    # Process tasks - group by sprint
    tasks_by_sprint: Dict[str, List[str]] = {}
    for task_id, task_info in task_by_id.items():
        sprint_id = task_info.get('sprint_id')
        if sprint_id:
            tasks_by_sprint.setdefault(sprint_id, []).append(task_id)

        task_status = task_info.get('status', 'not_started')
        task_statuses[task_id] = task_status

        file_counts[task_id] = FileCount(
            entity_type='task',
            entity_id=task_id,
            parent_id=sprint_id,
            file_path=task_info['_file_path'],
            child_count=0,
            status=task_status,
            name=task_info.get('title', task_id),
        )

    # Process sprints - group by track
    sprints_by_track: Dict[str, List[str]] = {}
    for sprint_id, sprint_info in sprint_by_id.items():
        track_id = sprint_info.get('track_id')
        if track_id:
            sprints_by_track.setdefault(track_id, []).append(sprint_id)

        sprint_status = sprint_info.get('status', 'not_started')

        # Count tasks for this sprint
        sprint_task_ids = tasks_by_sprint.get(sprint_id, [])
        task_count = len(sprint_task_ids)
        tasks_completed = 0
        dev_tasks = 0
        dev_completed = 0
        completion_gate_tasks = 0
        completion_gate_completed = 0
        production_gate_tasks = 0
        production_gate_completed = 0

        for task_id in sprint_task_ids:
            task_info = task_by_id.get(task_id, {})
            task_status = task_info.get('status', 'not_started')
            task_type = task_info.get('task_type', 'development')

            if task_status == 'completed':
                tasks_completed += 1

            if task_type == 'development':
                dev_tasks += 1
                if task_status == 'completed':
                    dev_completed += 1
            elif task_type == 'completion_gate':
                completion_gate_tasks += 1
                if task_status == 'completed':
                    completion_gate_completed += 1
            elif task_type == 'production_gate':
                production_gate_tasks += 1
                if task_status == 'completed':
                    production_gate_completed += 1

        file_counts[sprint_id] = FileCount(
            entity_type='sprint',
            entity_id=sprint_id,
            parent_id=track_id,
            file_path=sprint_info['_file_path'],
            child_count=task_count,
            status=sprint_status,
            name=sprint_info.get('name', sprint_id),
        )
        file_counts[sprint_id]._dev_tasks = dev_tasks
        file_counts[sprint_id]._dev_completed = dev_completed
        file_counts[sprint_id]._cg_tasks = completion_gate_tasks
        file_counts[sprint_id]._cg_completed = completion_gate_completed
        file_counts[sprint_id]._pg_tasks = production_gate_tasks
        file_counts[sprint_id]._pg_completed = production_gate_completed
        file_counts[sprint_id]._tasks_completed = tasks_completed

    # Process tracks
    for track_id, track_info in track_by_id.items():
        track_sprint_ids = sprints_by_track.get(track_id, [])
        sprint_count = len(track_sprint_ids)
        sprints_completed = 0
        track_tasks_total = 0
        track_tasks_completed = 0

        for sprint_id in track_sprint_ids:
            sprint_info = sprint_by_id.get(sprint_id, {})
            if sprint_info.get('status') == 'completed':
                sprints_completed += 1

            # Count tasks for this sprint
            sprint_task_ids = tasks_by_sprint.get(sprint_id, [])
            track_tasks_total += len(sprint_task_ids)
            for task_id in sprint_task_ids:
                task_info = task_by_id.get(task_id, {})
                if task_info.get('status') == 'completed':
                    track_tasks_completed += 1

        file_counts[track_id] = FileCount(
            entity_type='track',
            entity_id=track_id,
            parent_id=None,
            file_path=track_info['_file_path'],
            child_count=sprint_count,
            status=track_info.get('status', 'not_started'),
            name=track_info.get('name', track_id),
        )
        file_counts[track_id]._sprints_completed = sprints_completed
        file_counts[track_id]._tasks_total = track_tasks_total
        file_counts[track_id]._tasks_completed = track_tasks_completed

    return file_counts, task_statuses


def extract_declared_progress(
    roadmap_root: Path,
) -> Dict[str, DeclaredProgress]:
    """
    Extract declared progress counters from YAML files (flat structure).

    Uses flat structure:
    - tracks/{track_id}.yaml
    - sprints/{sprint_id}.yaml

    Returns:
        Dict mapping entity_id to DeclaredProgress
    """
    declared: Dict[str, DeclaredProgress] = {}

    if not roadmap_root.exists():
        return declared

    tracks_dir = roadmap_root / "tracks"
    sprints_dir = roadmap_root / "sprints"

    # Load all tracks
    if tracks_dir.exists():
        for track_yaml in tracks_dir.glob("*.yaml"):
            if track_yaml.name.startswith('.'):
                continue

            track_data = _parse_yaml_safe(track_yaml)
            if not track_data or 'track' not in track_data:
                continue

            track_info = track_data['track']
            track_id = track_info.get('id', track_yaml.stem)

            # Extract track-level progress
            progress = track_info.get('progress', {})
            declared[track_id] = DeclaredProgress(
                entity_type='track',
                entity_id=track_id,
                parent_id=None,
                declared_sprints_total=progress.get('sprints_total'),
                declared_sprints_completed=progress.get('sprints_completed'),
                declared_tasks_total=progress.get('tasks_total'),
                declared_tasks_completed=progress.get('tasks_completed'),
                declared_completion_percent=progress.get('completion_percent'),
            )

    # Load all sprints
    if sprints_dir.exists():
        for sprint_yaml in sprints_dir.glob("*.yaml"):
            if sprint_yaml.name.startswith('.'):
                continue

            sprint_data = _parse_yaml_safe(sprint_yaml)
            if not sprint_data or 'sprint' not in sprint_data:
                continue

            sprint_info = sprint_data['sprint']
            sprint_id = sprint_info.get('id', sprint_yaml.stem)
            track_id = sprint_info.get('track_id')

            # Extract sprint-level progress
            progress = sprint_info.get('progress', {})
            declared[sprint_id] = DeclaredProgress(
                entity_type='sprint',
                entity_id=sprint_id,
                parent_id=track_id,
                development_tasks_total=progress.get('development_tasks_total'),
                development_tasks_completed=progress.get('development_tasks_completed'),
                completion_gate_tasks_total=progress.get('completion_gate_tasks_total'),
                completion_gate_tasks_completed=progress.get('completion_gate_tasks_completed'),
                production_gate_tasks_total=progress.get('production_gate_tasks_total'),
                production_gate_tasks_completed=progress.get('production_gate_tasks_completed'),
                tasks_total=progress.get('tasks_total'),
                tasks_completed=progress.get('tasks_completed'),
                completion_percent=progress.get('completion_percent'),
            )

    return declared


def audit_discrepancies(
    computed: Dict[str, FileCount],
    declared: Dict[str, DeclaredProgress],
) -> AuditReport:
    """
    Compare computed file counts to declared progress counters.

    Returns:
        AuditReport with all discrepancies
    """
    discrepancies: List[Discrepancy] = []

    # Check track discrepancies
    for entity_id, count in computed.items():
        if count.entity_type == 'track':
            decl = declared.get(entity_id)
            if not decl:
                continue

            # Check sprints_total
            if decl.declared_sprints_total is not None:
                if count.child_count != decl.declared_sprints_total:
                    discrepancies.append(Discrepancy(
                        entity_type='track',
                        entity_id=entity_id,
                        field_name='sprints_total',
                        computed_value=count.child_count,
                        declared_value=decl.declared_sprints_total,
                        difference=count.child_count - decl.declared_sprints_total,
                        severity='critical' if abs(count.child_count - decl.declared_sprints_total) > 0 else 'info',
                    ))

            # Check sprints_completed
            if decl.declared_sprints_completed is not None:
                sprints_completed = getattr(count, '_sprints_completed', 0)
                if sprints_completed != decl.declared_sprints_completed:
                    discrepancies.append(Discrepancy(
                        entity_type='track',
                        entity_id=entity_id,
                        field_name='sprints_completed',
                        computed_value=sprints_completed,
                        declared_value=decl.declared_sprints_completed,
                        difference=sprints_completed - decl.declared_sprints_completed,
                        severity='warning',
                    ))

            # Check tasks_total
            if decl.declared_tasks_total is not None:
                tasks_total = getattr(count, '_tasks_total', 0)
                if tasks_total != decl.declared_tasks_total:
                    discrepancies.append(Discrepancy(
                        entity_type='track',
                        entity_id=entity_id,
                        field_name='tasks_total',
                        computed_value=tasks_total,
                        declared_value=decl.declared_tasks_total,
                        difference=tasks_total - decl.declared_tasks_total,
                        severity='critical',
                    ))

            # Check tasks_completed
            if decl.declared_tasks_completed is not None:
                tasks_completed = getattr(count, '_tasks_completed', 0)
                if tasks_completed != decl.declared_tasks_completed:
                    discrepancies.append(Discrepancy(
                        entity_type='track',
                        entity_id=entity_id,
                        field_name='tasks_completed',
                        computed_value=tasks_completed,
                        declared_value=decl.declared_tasks_completed,
                        difference=tasks_completed - decl.declared_tasks_completed,
                        severity='warning',
                    ))

        elif count.entity_type == 'sprint':
            decl = declared.get(entity_id)
            if not decl:
                continue

            # Check tasks_total
            if decl.tasks_total is not None:
                if count.child_count != decl.tasks_total:
                    discrepancies.append(Discrepancy(
                        entity_type='sprint',
                        entity_id=entity_id,
                        field_name='tasks_total',
                        computed_value=count.child_count,
                        declared_value=decl.tasks_total,
                        difference=count.child_count - decl.tasks_total,
                        severity='critical',
                    ))

            # Check tasks_completed
            if decl.tasks_completed is not None:
                tasks_completed = getattr(count, '_tasks_completed', 0)
                if tasks_completed != decl.tasks_completed:
                    discrepancies.append(Discrepancy(
                        entity_type='sprint',
                        entity_id=entity_id,
                        field_name='tasks_completed',
                        computed_value=tasks_completed,
                        declared_value=decl.tasks_completed,
                        difference=tasks_completed - decl.tasks_completed,
                        severity='warning',
                    ))

            # Check development_tasks_total
            if decl.development_tasks_total is not None:
                dev_tasks = getattr(count, '_dev_tasks', 0)
                if dev_tasks != decl.development_tasks_total:
                    discrepancies.append(Discrepancy(
                        entity_type='sprint',
                        entity_id=entity_id,
                        field_name='development_tasks_total',
                        computed_value=dev_tasks,
                        declared_value=decl.development_tasks_total,
                        difference=dev_tasks - decl.development_tasks_total,
                        severity='warning',
                    ))

    return AuditReport(
        computed_counts=computed,
        declared_progress=declared,
        discrepancies=discrepancies,
    )


def build_computed_database(
    roadmap_root: Path,
    output_path: Optional[Path] = None,
) -> Path:
    """
    Build a SQLite database with file-based computed progress values.

    This walks the filesystem and counts actual task.yaml files,
    rather than relying on declared counters.

    Args:
        roadmap_root: Path to .vibey/roadmap directory
        output_path: Where to write the database (default: /tmp/computed_roadmap.db)

    Returns:
        Path to created database
    """
    if output_path is None:
        output_path = Path("/tmp/computed_roadmap.db")

    # Delete existing database
    if output_path.exists():
        output_path.unlink()

    # Count files
    file_counts, task_statuses = count_files_in_directory(roadmap_root)

    # Create database
    conn = sqlite3.connect(str(output_path))

    # Create tables for computed values
    conn.execute("""
        CREATE TABLE tracks (
            id TEXT PRIMARY KEY,
            name TEXT,
            status TEXT,
            sprints_total INTEGER,
            sprints_completed INTEGER,
            tasks_total INTEGER,
            tasks_completed INTEGER,
            completion_percent REAL
        )
    """)

    conn.execute("""
        CREATE TABLE sprints (
            id TEXT PRIMARY KEY,
            track_id TEXT,
            name TEXT,
            status TEXT,
            development_tasks_total INTEGER,
            development_tasks_completed INTEGER,
            completion_gate_tasks_total INTEGER,
            completion_gate_tasks_completed INTEGER,
            production_gate_tasks_total INTEGER,
            production_gate_tasks_completed INTEGER,
            tasks_total INTEGER,
            tasks_completed INTEGER,
            completion_percent REAL,
            FOREIGN KEY (track_id) REFERENCES tracks(id)
        )
    """)

    conn.execute("""
        CREATE TABLE tasks (
            id TEXT PRIMARY KEY,
            sprint_id TEXT,
            title TEXT,
            status TEXT,
            task_type TEXT,
            FOREIGN KEY (sprint_id) REFERENCES sprints(id)
        )
    """)

    # Insert data
    for entity_id, count in file_counts.items():
        if count.entity_type == 'track':
            tasks_total = getattr(count, '_tasks_total', 0)
            tasks_completed = getattr(count, '_tasks_completed', 0)
            sprints_completed = getattr(count, '_sprints_completed', 0)
            completion_percent = (tasks_completed / tasks_total * 100) if tasks_total > 0 else 0

            conn.execute(
                """INSERT INTO tracks
                   (id, name, status, sprints_total, sprints_completed,
                    tasks_total, tasks_completed, completion_percent)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (entity_id, count.name, count.status, count.child_count,
                 sprints_completed, tasks_total, tasks_completed, completion_percent)
            )

        elif count.entity_type == 'sprint':
            tasks_completed = getattr(count, '_tasks_completed', 0)
            completion_percent = (tasks_completed / count.child_count * 100) if count.child_count > 0 else 0

            conn.execute(
                """INSERT INTO sprints
                   (id, track_id, name, status,
                    development_tasks_total, development_tasks_completed,
                    completion_gate_tasks_total, completion_gate_tasks_completed,
                    production_gate_tasks_total, production_gate_tasks_completed,
                    tasks_total, tasks_completed, completion_percent)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (entity_id, count.parent_id, count.name, count.status,
                 getattr(count, '_dev_tasks', 0), getattr(count, '_dev_completed', 0),
                 getattr(count, '_cg_tasks', 0), getattr(count, '_cg_completed', 0),
                 getattr(count, '_pg_tasks', 0), getattr(count, '_pg_completed', 0),
                 count.child_count, tasks_completed, completion_percent)
            )

        elif count.entity_type == 'task':
            # Read task_type from the YAML
            task_data = _parse_yaml_safe(count.file_path)
            task_type = 'development'
            if task_data and 'task' in task_data:
                task_type = task_data['task'].get('task_type', 'development')

            conn.execute(
                """INSERT INTO tasks (id, sprint_id, title, status, task_type)
                   VALUES (?, ?, ?, ?, ?)""",
                (entity_id, count.parent_id, count.name, count.status, task_type)
            )

    conn.commit()
    conn.close()

    return output_path


def run_full_audit(roadmap_root: Path) -> AuditReport:
    """
    Run a full integrity audit on the roadmap.

    Args:
        roadmap_root: Path to .vibey/roadmap directory

    Returns:
        AuditReport with all discrepancies
    """
    computed, task_statuses = count_files_in_directory(roadmap_root)
    declared = extract_declared_progress(roadmap_root)
    return audit_discrepancies(computed, declared)


def validate_embedded_summaries(track_id: str, roadmap_root: Path) -> EmbeddedSummaryReport:
    """
    Validate embedded sprint summaries in track.yaml against actual sprint data (flat structure).

    Sprint 13 Task 006: Extends integrity audit to validate that embedded
    sprint summaries in track.yaml match the actual sprint.yaml files.

    Uses flat structure:
    - tracks/{track_id}.yaml
    - sprints/{sprint_id}.yaml (filtered by track_id)

    Args:
        track_id: The track ID to validate
        roadmap_root: Path to .vibey/roadmap directory

    Returns:
        EmbeddedSummaryReport with discrepancies

    Validation checks:
    1. Sprint count matches actual sprint files for this track
    2. Sprint IDs in summary match sprint.yaml IDs
    3. Task counts match computed values
    4. Completion percentages are accurate
    5. Status values are current
    """
    tracks_dir = roadmap_root / "tracks"
    sprints_dir = roadmap_root / "sprints"

    track_yaml = tracks_dir / f"{track_id}.yaml"
    if not track_yaml.exists():
        return EmbeddedSummaryReport(track_id=track_id)

    track_data = _parse_yaml_safe(track_yaml)
    if not track_data or 'track' not in track_data:
        return EmbeddedSummaryReport(track_id=track_id)

    track_info = track_data['track']

    report = EmbeddedSummaryReport(track_id=track_id)

    # Get embedded sprint summaries from track.yaml
    embedded_summaries = track_info.get('sprints', [])
    embedded_by_id = {s.get('id', ''): s for s in embedded_summaries if isinstance(s, dict)}

    # Find actual sprints for this track (from flat sprints/ directory)
    actual_sprints: Dict[str, Dict] = {}
    if sprints_dir.exists():
        for sprint_yaml in sprints_dir.glob("*.yaml"):
            if sprint_yaml.name.startswith('.'):
                continue
            sprint_data = _parse_yaml_safe(sprint_yaml)
            if sprint_data and 'sprint' in sprint_data:
                sprint_info = sprint_data['sprint']
                # Only include sprints belonging to this track
                if sprint_info.get('track_id') == track_id:
                    sprint_id = sprint_info.get('id', sprint_yaml.stem)
                    actual_sprints[sprint_id] = sprint_info

    actual_sprint_ids = set(actual_sprints.keys())

    # Check for orphaned summaries (in track.yaml but no sprint file)
    for embedded_id in embedded_by_id:
        if embedded_id and embedded_id not in actual_sprint_ids:
            report.orphaned_summaries.append(embedded_id)

    # Check for missing summaries (sprint exists but not in track.yaml)
    for actual_id in actual_sprint_ids:
        if actual_id not in embedded_by_id:
            report.missing_summaries.append(actual_id)

    # Compare embedded summaries to actual sprint data
    for sprint_id, sprint_info in actual_sprints.items():
        # Get corresponding embedded summary
        embedded = embedded_by_id.get(sprint_id)
        if not embedded:
            continue  # Already flagged as missing

        # Compare status
        actual_status = sprint_info.get('status')
        embedded_status = embedded.get('status')
        if actual_status and embedded_status and actual_status != embedded_status:
            report.discrepancies.append(EmbeddedSummaryDiscrepancy(
                track_id=track_id,
                sprint_id=sprint_id,
                field_name='status',
                embedded_value=embedded_status,
                actual_value=actual_status,
                severity='warning',
                message=f"Status mismatch: embedded={embedded_status}, actual={actual_status}",
            ))

        # Compare task counts from progress
        actual_progress = sprint_info.get('progress', {})
        actual_tasks_total = actual_progress.get('tasks_total')
        actual_tasks_completed = actual_progress.get('tasks_completed')
        actual_completion = actual_progress.get('completion_percent')

        # Embedded summaries may have different field names
        embedded_tasks_total = embedded.get('tasks_total')
        embedded_tasks_completed = embedded.get('tasks_completed')
        embedded_completion = embedded.get('completion_percent')

        if actual_tasks_total is not None and embedded_tasks_total is not None:
            if actual_tasks_total != embedded_tasks_total:
                report.discrepancies.append(EmbeddedSummaryDiscrepancy(
                    track_id=track_id,
                    sprint_id=sprint_id,
                    field_name='tasks_total',
                    embedded_value=embedded_tasks_total,
                    actual_value=actual_tasks_total,
                    severity='critical',
                    message=f"Task count mismatch",
                ))

        if actual_tasks_completed is not None and embedded_tasks_completed is not None:
            if actual_tasks_completed != embedded_tasks_completed:
                report.discrepancies.append(EmbeddedSummaryDiscrepancy(
                    track_id=track_id,
                    sprint_id=sprint_id,
                    field_name='tasks_completed',
                    embedded_value=embedded_tasks_completed,
                    actual_value=actual_tasks_completed,
                    severity='warning',
                    message=f"Completed task count mismatch",
                ))

        if actual_completion is not None and embedded_completion is not None:
            # Allow small floating point differences
            if abs(actual_completion - embedded_completion) > 0.1:
                report.discrepancies.append(EmbeddedSummaryDiscrepancy(
                    track_id=track_id,
                    sprint_id=sprint_id,
                    field_name='completion_percent',
                    embedded_value=embedded_completion,
                    actual_value=actual_completion,
                    severity='info',
                    message=f"Completion percentage mismatch",
                ))

    return report


def validate_all_embedded_summaries(roadmap_root: Path) -> List[EmbeddedSummaryReport]:
    """
    Validate embedded sprint summaries across all tracks (flat structure).

    Uses flat structure:
    - tracks/{track_id}.yaml

    Args:
        roadmap_root: Path to .vibey/roadmap directory

    Returns:
        List of EmbeddedSummaryReport, one per track
    """
    reports = []

    if not roadmap_root.exists():
        return reports

    tracks_dir = roadmap_root / "tracks"
    if not tracks_dir.exists():
        return reports

    for track_yaml in tracks_dir.glob("*.yaml"):
        if track_yaml.name.startswith('.'):
            continue

        track_data = _parse_yaml_safe(track_yaml)
        if not track_data or 'track' not in track_data:
            continue

        track_id = track_data['track'].get('id', track_yaml.stem)
        report = validate_embedded_summaries(track_id, roadmap_root)
        reports.append(report)

    return reports


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Audit roadmap data integrity")
    parser.add_argument(
        "roadmap_root",
        type=Path,
        nargs='?',
        default=Path(".vibey/roadmap"),
        help="Path to roadmap root directory"
    )
    parser.add_argument(
        "--build-db",
        type=Path,
        help="Build computed database at specified path"
    )

    args = parser.parse_args()

    if args.build_db:
        db_path = build_computed_database(args.roadmap_root, args.build_db)
        print(f"Built computed database: {db_path}")
    else:
        report = run_full_audit(args.roadmap_root)
        print(report.summary())
