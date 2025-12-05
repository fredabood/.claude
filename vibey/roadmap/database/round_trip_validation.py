"""
Round-Trip Validation Module

Implements Steps 2-3 of the sqlite_validation.md process:
- Step 2: Dump computed database to YAML and compare to original
- Step 3: Load generated YAML into new computed database and verify identical

This ensures the full YAML -> SQLite -> YAML round-trip preserves all data.

Usage:
    from vibey.roadmap.database.round_trip_validation import (
        dump_database_to_yaml,
        compare_yaml_directories,
        run_round_trip_validation,
    )

    # Full validation
    report = run_round_trip_validation(
        roadmap_root=Path(".vibey/roadmap"),
        db_path=Path(".vibey/roadmap.db"),
    )
    print(report.summary())
"""

import difflib
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone
import yaml

from .integrity_audit import build_computed_database, run_full_audit


@dataclass
class FileDifference:
    """Represents a difference between two YAML files."""
    file_path: str
    diff_type: str  # 'missing_in_generated', 'missing_in_original', 'content_differs'
    original_lines: Optional[int] = None
    generated_lines: Optional[int] = None
    diff_preview: Optional[str] = None


@dataclass
class RoundTripReport:
    """Report from round-trip validation."""
    step2_differences: List[FileDifference] = field(default_factory=list)
    step3_success: bool = False
    step3_discrepancies: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def step2_success(self) -> bool:
        return len(self.step2_differences) == 0

    @property
    def success(self) -> bool:
        return self.step2_success and self.step3_success

    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            "=" * 70,
            "ROUND-TRIP VALIDATION REPORT",
            f"Timestamp: {self.timestamp.isoformat()}",
            "=" * 70,
            "",
            "STEP 2: Compare generated YAML to original",
            "-" * 50,
        ]

        if self.step2_success:
            lines.append("All YAML files match! No content differences found.")
        else:
            lines.append(f"Found {len(self.step2_differences)} differences:")
            for diff in self.step2_differences[:10]:  # Show first 10
                lines.append(f"  - {diff.file_path}: {diff.diff_type}")
                if diff.diff_preview:
                    for line in diff.diff_preview.split('\n')[:5]:
                        lines.append(f"      {line}")
            if len(self.step2_differences) > 10:
                lines.append(f"  ... and {len(self.step2_differences) - 10} more")

        lines.append("")
        lines.append("STEP 3: Verify round-trip database integrity")
        lines.append("-" * 50)

        if self.step3_success:
            lines.append("Round-trip database matches original! Zero discrepancies.")
        else:
            lines.append(f"FAILED: {self.step3_discrepancies} discrepancies found after round-trip")

        lines.append("")
        lines.append("=" * 70)
        lines.append(f"OVERALL: {'PASS' if self.success else 'FAIL'}")
        lines.append("=" * 70)

        return "\n".join(lines)


def dump_database_to_yaml(
    db_path: Path,
    output_dir: Path,
) -> None:
    """
    Dump SQLite database contents to YAML files.

    This creates a full YAML roadmap structure from the database.
    Uses hierarchical format (task: singular) to match original files.

    Args:
        db_path: Path to SQLite database
        output_dir: Directory to write YAML files
    """
    from ..serialization.sql_loader import (
        load_roadmap,
        load_track,
        load_sprint,
        load_tasks_by_sprint,
    )
    from ..serialization.yaml_dumper import (
        save_roadmap,
        save_track,
        save_sprint,
        save_tasks,
    )

    # Load roadmap
    roadmap = load_roadmap()

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save roadmap.yaml
    save_roadmap(roadmap, output_dir / "roadmap.yaml")

    # Process each track
    for track_id in _get_track_ids(db_path):
        track = load_track(track_id)

        # Create track directory
        track_dir = output_dir / track_id
        track_dir.mkdir(parents=True, exist_ok=True)

        # Save track.yaml
        save_track(track, track_dir / "track.yaml")

        # Process each sprint
        for sprint_id in _get_sprint_ids(db_path, track_id):
            sprint = load_sprint(sprint_id)

            # Create sprint directory
            sprint_dir = track_dir / sprint_id
            sprint_dir.mkdir(parents=True, exist_ok=True)

            # Save sprint.yaml
            save_sprint(sprint, sprint_dir / "sprint.yaml")

            # Get tasks for sprint and save using hierarchical format
            # Pass sprint_dir as directory so save_tasks uses _save_task_hierarchical
            tasks = load_tasks_by_sprint(sprint_id)
            if tasks:
                save_tasks(tasks, sprint_dir)


def _get_track_ids(db_path: Path) -> List[str]:
    """Get all track IDs from database."""
    import sqlite3
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute("SELECT id FROM tracks ORDER BY id").fetchall()
        return [row[0] for row in rows]
    finally:
        conn.close()


def _get_sprint_ids(db_path: Path, track_id: str) -> List[str]:
    """Get all sprint IDs for a track from database."""
    import sqlite3
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT id FROM sprints WHERE track_id = ? ORDER BY id",
            (track_id,)
        ).fetchall()
        return [row[0] for row in rows]
    finally:
        conn.close()


def compare_yaml_directories(
    original_dir: Path,
    generated_dir: Path,
) -> List[FileDifference]:
    """
    Compare two YAML directory trees and report differences.

    Args:
        original_dir: Original YAML directory
        generated_dir: Generated YAML directory

    Returns:
        List of file differences
    """
    differences = []

    # Get all YAML files from both directories
    original_files = set()
    for f in original_dir.rglob("*.yaml"):
        rel = f.relative_to(original_dir)
        # Skip non-roadmap files
        if rel.name in ['roadmap.yaml', 'track.yaml', 'sprint.yaml', 'task.yaml']:
            original_files.add(str(rel))

    generated_files = set()
    for f in generated_dir.rglob("*.yaml"):
        rel = f.relative_to(generated_dir)
        if rel.name in ['roadmap.yaml', 'track.yaml', 'sprint.yaml', 'task.yaml']:
            generated_files.add(str(rel))

    # Check for missing files
    for f in original_files - generated_files:
        differences.append(FileDifference(
            file_path=f,
            diff_type='missing_in_generated',
        ))

    for f in generated_files - original_files:
        differences.append(FileDifference(
            file_path=f,
            diff_type='missing_in_original',
        ))

    # Compare common files
    for f in original_files & generated_files:
        orig_path = original_dir / f
        gen_path = generated_dir / f

        try:
            with open(orig_path) as of:
                orig_content = of.read()
            with open(gen_path) as gf:
                gen_content = gf.read()

            # Normalize YAML for comparison (parse and re-serialize)
            try:
                orig_data = yaml.safe_load(orig_content)
                gen_data = yaml.safe_load(gen_content)

                # Compare data structures (ignore formatting)
                if _normalize_yaml_data(orig_data) != _normalize_yaml_data(gen_data):
                    # Generate diff preview
                    diff_lines = list(difflib.unified_diff(
                        orig_content.splitlines(keepends=True),
                        gen_content.splitlines(keepends=True),
                        fromfile=f'original/{f}',
                        tofile=f'generated/{f}',
                        n=2
                    ))
                    diff_preview = ''.join(diff_lines[:20])  # First 20 lines

                    differences.append(FileDifference(
                        file_path=f,
                        diff_type='content_differs',
                        original_lines=len(orig_content.splitlines()),
                        generated_lines=len(gen_content.splitlines()),
                        diff_preview=diff_preview,
                    ))
            except yaml.YAMLError:
                # If YAML parsing fails, do string comparison
                if orig_content.strip() != gen_content.strip():
                    differences.append(FileDifference(
                        file_path=f,
                        diff_type='content_differs',
                    ))

        except Exception as e:
            differences.append(FileDifference(
                file_path=f,
                diff_type=f'error: {e}',
            ))

    return differences


def _normalize_yaml_data(data: Any) -> Any:
    """Normalize YAML data for comparison (ignore None vs missing, etc.)."""
    if isinstance(data, dict):
        return {k: _normalize_yaml_data(v) for k, v in data.items() if v is not None}
    elif isinstance(data, list):
        return [_normalize_yaml_data(item) for item in data]
    elif isinstance(data, str):
        return data.strip()
    return data


def run_round_trip_validation(
    roadmap_root: Path,
    db_path: Optional[Path] = None,
) -> RoundTripReport:
    """
    Run full round-trip validation (Steps 2-3 of sqlite_validation.md).

    Args:
        roadmap_root: Path to .vibey/roadmap directory
        db_path: Path to SQLite database (default: .vibey/roadmap.db)

    Returns:
        RoundTripReport with validation results
    """
    if db_path is None:
        db_path = roadmap_root.parent / "roadmap.db"

    report = RoundTripReport()

    # Create temp directory for generated YAML
    with tempfile.TemporaryDirectory() as temp_dir:
        generated_dir = Path(temp_dir) / "generated"

        # Step 2: Dump database to YAML
        try:
            dump_database_to_yaml(db_path, generated_dir)
        except Exception as e:
            report.step2_differences.append(FileDifference(
                file_path="(database dump failed)",
                diff_type=f'error: {e}',
            ))
            return report

        # Step 2: Compare generated to original
        report.step2_differences = compare_yaml_directories(
            roadmap_root, generated_dir
        )

        # Step 3: Build computed database from generated YAML
        if report.step2_success:
            try:
                generated_db = Path(temp_dir) / "generated.db"
                build_computed_database(generated_dir, generated_db)

                # Compare to original computed database
                original_db = Path(temp_dir) / "original.db"
                build_computed_database(roadmap_root, original_db)

                # Run audit comparison
                audit = run_full_audit(generated_dir)
                report.step3_discrepancies = len(audit.discrepancies)
                report.step3_success = report.step3_discrepancies == 0

            except Exception as e:
                report.step3_discrepancies = -1  # Error indicator
                report.step3_success = False
        else:
            # Skip step 3 if step 2 failed
            report.step3_success = False
            report.step3_discrepancies = -1

    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run round-trip validation")
    parser.add_argument(
        "roadmap_root",
        type=Path,
        nargs='?',
        default=Path(".vibey/roadmap"),
        help="Path to roadmap root directory"
    )
    parser.add_argument(
        "--db",
        type=Path,
        help="Path to SQLite database (default: .vibey/roadmap.db)"
    )

    args = parser.parse_args()

    report = run_round_trip_validation(args.roadmap_root, args.db)
    print(report.summary())
