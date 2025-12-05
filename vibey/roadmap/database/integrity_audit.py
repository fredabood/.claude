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
    Walk the roadmap directory and count actual files.

    Returns:
        Tuple of (file_counts, task_statuses)
        - file_counts: Dict mapping entity_id to FileCount
        - task_statuses: Dict mapping task_id to status (for computing completed counts)
    """
    file_counts: Dict[str, FileCount] = {}
    task_statuses: Dict[str, str] = {}

    if not roadmap_root.exists():
        return file_counts, task_statuses

    # Walk track directories
    for track_dir in roadmap_root.iterdir():
        if not track_dir.is_dir() or track_dir.name.startswith('.'):
            continue

        track_yaml = track_dir / "track.yaml"
        if not track_yaml.exists():
            continue

        track_data = _parse_yaml_safe(track_yaml)
        if not track_data or 'track' not in track_data:
            continue

        track_info = track_data['track']
        track_id = track_info.get('id', track_dir.name)

        # Count sprints and tasks for this track
        sprint_count = 0
        sprints_completed = 0
        track_tasks_total = 0
        track_tasks_completed = 0

        for sprint_dir in track_dir.iterdir():
            if not sprint_dir.is_dir() or sprint_dir.name.startswith('.') or sprint_dir.name == 'context':
                continue

            sprint_yaml = sprint_dir / "sprint.yaml"
            if not sprint_yaml.exists():
                continue

            sprint_data = _parse_yaml_safe(sprint_yaml)
            if not sprint_data or 'sprint' not in sprint_data:
                continue

            sprint_info = sprint_data['sprint']
            sprint_id = sprint_info.get('id', sprint_dir.name)
            sprint_status = sprint_info.get('status', 'not_started')

            sprint_count += 1
            if sprint_status == 'completed':
                sprints_completed += 1

            # Count tasks for this sprint
            task_count = 0
            tasks_completed = 0
            dev_tasks = 0
            dev_completed = 0
            completion_gate_tasks = 0
            completion_gate_completed = 0
            production_gate_tasks = 0
            production_gate_completed = 0

            for task_dir in sprint_dir.iterdir():
                if not task_dir.is_dir() or task_dir.name.startswith('.') or task_dir.name == 'context':
                    continue

                task_yaml = task_dir / "task.yaml"
                if not task_yaml.exists():
                    continue

                task_data = _parse_yaml_safe(task_yaml)
                if not task_data or 'task' not in task_data:
                    continue

                task_info = task_data['task']
                task_id = task_info.get('id', task_dir.name)
                task_status = task_info.get('status', 'not_started')
                task_type = task_info.get('task_type', 'development')

                task_count += 1
                track_tasks_total += 1
                task_statuses[task_id] = task_status

                if task_status == 'completed':
                    tasks_completed += 1
                    track_tasks_completed += 1

                # Count by type
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

                # Record task
                file_counts[task_id] = FileCount(
                    entity_type='task',
                    entity_id=task_id,
                    parent_id=sprint_id,
                    file_path=task_yaml,
                    child_count=0,
                    status=task_status,
                    name=task_info.get('title', task_id),
                )

            # Record sprint with computed task counts
            file_counts[sprint_id] = FileCount(
                entity_type='sprint',
                entity_id=sprint_id,
                parent_id=track_id,
                file_path=sprint_yaml,
                child_count=task_count,
                status=sprint_status,
                name=sprint_info.get('name', sprint_id),
            )
            # Store additional computed values as attributes
            file_counts[sprint_id]._dev_tasks = dev_tasks
            file_counts[sprint_id]._dev_completed = dev_completed
            file_counts[sprint_id]._cg_tasks = completion_gate_tasks
            file_counts[sprint_id]._cg_completed = completion_gate_completed
            file_counts[sprint_id]._pg_tasks = production_gate_tasks
            file_counts[sprint_id]._pg_completed = production_gate_completed
            file_counts[sprint_id]._tasks_completed = tasks_completed

        # Record track
        file_counts[track_id] = FileCount(
            entity_type='track',
            entity_id=track_id,
            parent_id=None,
            file_path=track_yaml,
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
    Extract declared progress counters from YAML files.

    Returns:
        Dict mapping entity_id to DeclaredProgress
    """
    declared: Dict[str, DeclaredProgress] = {}

    if not roadmap_root.exists():
        return declared

    # Walk track directories
    for track_dir in roadmap_root.iterdir():
        if not track_dir.is_dir() or track_dir.name.startswith('.'):
            continue

        track_yaml = track_dir / "track.yaml"
        if not track_yaml.exists():
            continue

        track_data = _parse_yaml_safe(track_yaml)
        if not track_data or 'track' not in track_data:
            continue

        track_info = track_data['track']
        track_id = track_info.get('id', track_dir.name)

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

        # Walk sprint directories
        for sprint_dir in track_dir.iterdir():
            if not sprint_dir.is_dir() or sprint_dir.name.startswith('.') or sprint_dir.name == 'context':
                continue

            sprint_yaml = sprint_dir / "sprint.yaml"
            if not sprint_yaml.exists():
                continue

            sprint_data = _parse_yaml_safe(sprint_yaml)
            if not sprint_data or 'sprint' not in sprint_data:
                continue

            sprint_info = sprint_data['sprint']
            sprint_id = sprint_info.get('id', sprint_dir.name)

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
