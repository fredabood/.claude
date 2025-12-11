"""
YAML Remediation Module

This module provides tools to fix discrepancies between computed file counts
and declared YAML progress counters. It updates YAML files in-place with
correct values computed from actual file counts.

Part of Sprint 11 "Data Validation & Integrity Audit".

Usage:
    from vibey.roadmap.database.yaml_remediation import (
        remediate_track_counters,
        remediate_sprint_counters,
        remediate_all_discrepancies,
    )

    # Fix a specific track
    remediate_track_counters(Path(".vibey/roadmap"), "sqlite-backend")

    # Fix all discrepancies
    report = remediate_all_discrepancies(Path(".vibey/roadmap"))
    print(report)
"""

import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone

from .integrity_audit import (
    count_files_in_directory,
    extract_declared_progress,
    audit_discrepancies,
    run_full_audit,
    FileCount,
    Discrepancy,
    AuditReport,
)


@dataclass
class RemediationAction:
    """A single remediation action taken."""
    entity_type: str
    entity_id: str
    field_name: str
    old_value: Any
    new_value: Any
    file_path: Path


@dataclass
class RemediationReport:
    """Report of all remediation actions taken."""
    actions: List[RemediationAction]
    timestamp: datetime

    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            "=" * 70,
            "REMEDIATION REPORT",
            f"Timestamp: {self.timestamp.isoformat()}",
            "=" * 70,
            "",
            f"Total actions taken: {len(self.actions)}",
            "",
        ]

        if self.actions:
            lines.append("CHANGES MADE:")
            lines.append("-" * 50)

            for action in self.actions:
                lines.append(
                    f"  [{action.entity_type}] {action.entity_id}:"
                )
                lines.append(
                    f"    {action.field_name}: {action.old_value} -> {action.new_value}"
                )
                lines.append(f"    File: {action.file_path}")
                lines.append("")
        else:
            lines.append("No remediation actions needed - all counters are correct.")

        lines.append("=" * 70)
        return "\n".join(lines)


class YAMLPreservingDumper(yaml.SafeDumper):
    """YAML dumper that preserves key order."""
    pass


def _represent_str(dumper, data):
    """Represent multiline strings with literal block style."""
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


YAMLPreservingDumper.add_representer(str, _represent_str)


def _load_yaml(file_path: Path) -> Optional[Dict]:
    """Load YAML file safely."""
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception:
        return None


def _save_yaml(file_path: Path, data: Dict) -> None:
    """Save YAML file preserving structure."""
    with open(file_path, 'w') as f:
        yaml.dump(data, f, Dumper=YAMLPreservingDumper,
                  default_flow_style=False, allow_unicode=True, sort_keys=False)


def remediate_track_counters(
    roadmap_root: Path,
    track_id: str,
    dry_run: bool = False,
) -> List[RemediationAction]:
    """
    Fix track-level progress counters based on actual file counts.

    Args:
        roadmap_root: Path to .vibey/roadmap directory
        track_id: Track ID to remediate
        dry_run: If True, don't actually modify files

    Returns:
        List of remediation actions taken
    """
    actions = []

    # Find track file in flat tracks/ directory
    tracks_dir = roadmap_root / "tracks"
    if not tracks_dir.exists():
        return actions

    # Direct lookup by ID
    track_yaml = tracks_dir / f"{track_id}.yaml"
    if not track_yaml.exists():
        # Fallback: scan for matching ID
        track_yaml = None
        for f in tracks_dir.glob("*.yaml"):
            if f.name.startswith('.'):
                continue
            data = _load_yaml(f)
            if data and data.get('track', {}).get('id') == track_id:
                track_yaml = f
                break

    if not track_yaml:
        return actions
    track_data = _load_yaml(track_yaml)
    if not track_data:
        return actions

    # Compute actual counts
    file_counts, _ = count_files_in_directory(roadmap_root)
    track_count = file_counts.get(track_id)
    if not track_count:
        return actions

    # Get current progress
    progress = track_data['track'].get('progress', {})

    # Build updates
    updates = {}

    sprints_total = track_count.child_count
    if progress.get('sprints_total') != sprints_total:
        updates['sprints_total'] = (progress.get('sprints_total'), sprints_total)

    sprints_completed = getattr(track_count, '_sprints_completed', 0)
    if progress.get('sprints_completed') != sprints_completed:
        updates['sprints_completed'] = (progress.get('sprints_completed'), sprints_completed)

    tasks_total = getattr(track_count, '_tasks_total', 0)
    if progress.get('tasks_total') != tasks_total:
        updates['tasks_total'] = (progress.get('tasks_total'), tasks_total)

    tasks_completed = getattr(track_count, '_tasks_completed', 0)
    if progress.get('tasks_completed') != tasks_completed:
        updates['tasks_completed'] = (progress.get('tasks_completed'), tasks_completed)

    completion_percent = (tasks_completed / tasks_total * 100) if tasks_total > 0 else 0.0
    completion_percent = round(completion_percent, 1)
    if progress.get('completion_percent') != completion_percent:
        updates['completion_percent'] = (progress.get('completion_percent'), completion_percent)

    # Apply updates
    if updates:
        if 'progress' not in track_data['track']:
            track_data['track']['progress'] = {}

        for field, (old_val, new_val) in updates.items():
            track_data['track']['progress'][field] = new_val
            actions.append(RemediationAction(
                entity_type='track',
                entity_id=track_id,
                field_name=field,
                old_value=old_val,
                new_value=new_val,
                file_path=track_yaml,
            ))

        if not dry_run:
            _save_yaml(track_yaml, track_data)

    return actions


def remediate_sprint_counters(
    roadmap_root: Path,
    sprint_id: str,
    dry_run: bool = False,
) -> List[RemediationAction]:
    """
    Fix sprint-level progress counters based on actual file counts.

    Args:
        roadmap_root: Path to .vibey/roadmap directory
        sprint_id: Sprint ID to remediate
        dry_run: If True, don't actually modify files

    Returns:
        List of remediation actions taken
    """
    actions = []

    # Find sprint file in flat sprints/ directory
    sprints_dir = roadmap_root / "sprints"
    if not sprints_dir.exists():
        return actions

    # Direct lookup by ID
    sprint_yaml = sprints_dir / f"{sprint_id}.yaml"
    if not sprint_yaml.exists():
        # Fallback: scan for matching ID
        sprint_yaml = None
        for f in sprints_dir.glob("*.yaml"):
            if f.name.startswith('.'):
                continue
            data = _load_yaml(f)
            if data and data.get('sprint', {}).get('id') == sprint_id:
                sprint_yaml = f
                break

    if not sprint_yaml:
        return actions

    sprint_data = _load_yaml(sprint_yaml)
    if not sprint_data:
        return actions

    # Compute actual counts
    file_counts, _ = count_files_in_directory(roadmap_root)
    sprint_count = file_counts.get(sprint_id)
    if not sprint_count:
        return actions

    # Get current progress
    progress = sprint_data['sprint'].get('progress', {})

    # Build updates
    updates = {}

    tasks_total = sprint_count.child_count
    if progress.get('tasks_total') != tasks_total:
        updates['tasks_total'] = (progress.get('tasks_total'), tasks_total)

    tasks_completed = getattr(sprint_count, '_tasks_completed', 0)
    if progress.get('tasks_completed') != tasks_completed:
        updates['tasks_completed'] = (progress.get('tasks_completed'), tasks_completed)

    dev_tasks = getattr(sprint_count, '_dev_tasks', 0)
    if progress.get('development_tasks_total') != dev_tasks:
        updates['development_tasks_total'] = (progress.get('development_tasks_total'), dev_tasks)

    dev_completed = getattr(sprint_count, '_dev_completed', 0)
    if progress.get('development_tasks_completed') != dev_completed:
        updates['development_tasks_completed'] = (progress.get('development_tasks_completed'), dev_completed)

    cg_tasks = getattr(sprint_count, '_cg_tasks', 0)
    if progress.get('completion_gate_tasks_total') != cg_tasks:
        updates['completion_gate_tasks_total'] = (progress.get('completion_gate_tasks_total'), cg_tasks)

    cg_completed = getattr(sprint_count, '_cg_completed', 0)
    if progress.get('completion_gate_tasks_completed') != cg_completed:
        updates['completion_gate_tasks_completed'] = (progress.get('completion_gate_tasks_completed'), cg_completed)

    pg_tasks = getattr(sprint_count, '_pg_tasks', 0)
    if progress.get('production_gate_tasks_total') != pg_tasks:
        updates['production_gate_tasks_total'] = (progress.get('production_gate_tasks_total'), pg_tasks)

    pg_completed = getattr(sprint_count, '_pg_completed', 0)
    if progress.get('production_gate_tasks_completed') != pg_completed:
        updates['production_gate_tasks_completed'] = (progress.get('production_gate_tasks_completed'), pg_completed)

    completion_percent = (tasks_completed / tasks_total * 100) if tasks_total > 0 else 0.0
    completion_percent = round(completion_percent, 1)
    if progress.get('completion_percent') != completion_percent:
        updates['completion_percent'] = (progress.get('completion_percent'), completion_percent)

    # Apply updates
    if updates:
        if 'progress' not in sprint_data['sprint']:
            sprint_data['sprint']['progress'] = {}

        for field, (old_val, new_val) in updates.items():
            sprint_data['sprint']['progress'][field] = new_val
            actions.append(RemediationAction(
                entity_type='sprint',
                entity_id=sprint_id,
                field_name=field,
                old_value=old_val,
                new_value=new_val,
                file_path=sprint_yaml,
            ))

        if not dry_run:
            _save_yaml(sprint_yaml, sprint_data)

    return actions


def remediate_all_discrepancies(
    roadmap_root: Path,
    dry_run: bool = False,
) -> RemediationReport:
    """
    Find and fix all discrepancies in the roadmap.

    Args:
        roadmap_root: Path to .vibey/roadmap directory
        dry_run: If True, don't actually modify files

    Returns:
        RemediationReport with all actions taken
    """
    all_actions = []

    # Get current audit
    audit = run_full_audit(roadmap_root)

    # Get unique entities with discrepancies
    entities_to_fix = set()
    for d in audit.discrepancies:
        entities_to_fix.add((d.entity_type, d.entity_id))

    # Fix each entity
    for entity_type, entity_id in entities_to_fix:
        if entity_type == 'track':
            actions = remediate_track_counters(roadmap_root, entity_id, dry_run)
            all_actions.extend(actions)
        elif entity_type == 'sprint':
            actions = remediate_sprint_counters(roadmap_root, entity_id, dry_run)
            all_actions.extend(actions)

    return RemediationReport(
        actions=all_actions,
        timestamp=datetime.now(timezone.utc),
    )


def verify_remediation(roadmap_root: Path) -> Tuple[bool, AuditReport]:
    """
    Run audit after remediation to verify all discrepancies are fixed.

    Returns:
        Tuple of (success: bool, report: AuditReport)
    """
    report = run_full_audit(roadmap_root)
    return len(report.discrepancies) == 0, report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Remediate YAML counter discrepancies")
    parser.add_argument(
        "roadmap_root",
        type=Path,
        nargs='?',
        default=Path(".vibey/roadmap"),
        help="Path to roadmap root directory"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes"
    )
    parser.add_argument(
        "--track",
        type=str,
        help="Remediate specific track only"
    )
    parser.add_argument(
        "--sprint",
        type=str,
        help="Remediate specific sprint only"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Run verification after remediation"
    )

    args = parser.parse_args()

    if args.track:
        actions = remediate_track_counters(args.roadmap_root, args.track, args.dry_run)
        report = RemediationReport(actions=actions, timestamp=datetime.now(timezone.utc))
    elif args.sprint:
        actions = remediate_sprint_counters(args.roadmap_root, args.sprint, args.dry_run)
        report = RemediationReport(actions=actions, timestamp=datetime.now(timezone.utc))
    else:
        report = remediate_all_discrepancies(args.roadmap_root, args.dry_run)

    print(report.summary())

    if args.verify and not args.dry_run:
        print("\nRunning verification...")
        success, audit = verify_remediation(args.roadmap_root)
        if success:
            print("All discrepancies fixed!")
        else:
            print("Remaining discrepancies:")
            print(audit.summary())
