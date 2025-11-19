#!/usr/bin/env python3
"""
Roadmap Data Quality Dashboard

Displays comprehensive health metrics for roadmap data integrity.
Tracks YAML syntax, serialization issues, schema compliance, and data quality.

Usage:
    python3 scripts/roadmap-health-dashboard.py [--json] [--export FILE]
"""

import argparse
import json
import sys
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, asdict

# Add vibey package to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from vibey.roadmap.models.common import Status, TaskStatus, Priority, DependencyType
from vibey.cli.roadmap_lib.filesystem import FileSystemManager


@dataclass
class HealthMetrics:
    """Roadmap data health metrics."""
    timestamp: str
    total_files: int = 0
    yaml_syntax_pass: int = 0
    yaml_syntax_fail: int = 0
    python_serialization_found: int = 0
    invalid_enum_values: int = 0
    type_mismatches: int = 0
    missing_required_fields: int = 0
    date_inconsistencies: int = 0
    overall_health_score: float = 0.0

    # File type breakdowns
    tracks_total: int = 0
    sprints_total: int = 0
    tasks_total: int = 0

    # Detailed issues
    issues: List[Dict[str, str]] = None

    def __post_init__(self):
        if self.issues is None:
            self.issues = []

    def calculate_health_score(self):
        """Calculate overall health score (0-100)."""
        if self.total_files == 0:
            return 100.0

        # Weight different types of issues
        deductions = 0

        # Critical issues (major deductions)
        deductions += self.yaml_syntax_fail * 10  # Can't even parse
        deductions += self.python_serialization_found * 5  # Data corruption
        deductions += self.missing_required_fields * 3  # Broken schema

        # Medium issues
        deductions += self.invalid_enum_values * 2  # Wrong values
        deductions += self.type_mismatches * 2  # Wrong types
        deductions += self.date_inconsistencies * 1  # Logic errors

        # Cap deductions at 100
        max_deductions = min(deductions, 100)

        self.overall_health_score = max(0.0, 100.0 - max_deductions)


class HealthDashboard:
    """Data quality dashboard generator."""

    def __init__(self):
        self.fs = FileSystemManager()
        self.metrics = HealthMetrics(timestamp=datetime.now().isoformat())

        # Valid enum values
        self.valid_statuses = {s.value for s in Status}
        self.valid_task_statuses = {s.value for s in TaskStatus}
        self.valid_priorities = {p.value for p in Priority}
        self.valid_dependency_types = {t.value for t in DependencyType}

    def get_all_roadmap_files(self) -> List[Path]:
        """Get all roadmap YAML files."""
        roadmap_dir = Path('.vibey/roadmap')
        if not roadmap_dir.exists():
            return []

        files = []
        for pattern in ['**/track.yaml', '**/sprint.yaml', '**/task.yaml']:
            files.extend(roadmap_dir.glob(pattern))
        return sorted(files)

    def check_yaml_syntax(self, file_path: Path) -> bool:
        """Check if YAML file has valid syntax."""
        try:
            with open(file_path) as f:
                yaml.safe_load(f)
            return True
        except Exception as e:
            self.metrics.issues.append({
                'file': str(file_path),
                'severity': 'critical',
                'category': 'syntax',
                'message': f"YAML syntax error: {str(e)}"
            })
            return False

    def check_python_serialization(self, file_path: Path) -> bool:
        """Check for Python object serialization."""
        try:
            with open(file_path) as f:
                content = f.read()
            if '!!python' in content:
                self.metrics.issues.append({
                    'file': str(file_path),
                    'severity': 'critical',
                    'category': 'serialization',
                    'message': 'Contains Python object serialization'
                })
                return True
        except Exception:
            pass
        return False

    def check_enum_values(self, data: Dict[str, Any], file_path: Path, file_type: str):
        """Check for invalid enum values."""
        if file_type == 'track':
            track_data = data.get('track', {})

            # Check status
            status = track_data.get('status')
            if status and status not in self.valid_statuses:
                self.metrics.invalid_enum_values += 1
                self.metrics.issues.append({
                    'file': str(file_path),
                    'severity': 'high',
                    'category': 'enum',
                    'message': f"Invalid status: '{status}'"
                })

            # Check priority
            priority = track_data.get('priority')
            if priority and priority not in self.valid_priorities:
                self.metrics.invalid_enum_values += 1
                self.metrics.issues.append({
                    'file': str(file_path),
                    'severity': 'high',
                    'category': 'enum',
                    'message': f"Invalid priority: '{priority}'"
                })

        elif file_type == 'task':
            task_data = data.get('task', {})

            status = task_data.get('status')
            if status and status not in self.valid_task_statuses:
                self.metrics.invalid_enum_values += 1
                self.metrics.issues.append({
                    'file': str(file_path),
                    'severity': 'high',
                    'category': 'enum',
                    'message': f"Invalid task status: '{status}'"
                })

    def check_type_mismatches(self, data: Dict[str, Any], file_path: Path, file_type: str):
        """Check for type mismatches."""
        if file_type == 'track':
            track_data = data.get('track', {})
            progress = track_data.get('progress', {})

            # Check numeric fields
            numeric_fields = ['sprints_total', 'sprints_completed', 'tasks_total', 'tasks_completed']
            for field in numeric_fields:
                value = progress.get(field)
                if value is not None and not isinstance(value, int):
                    self.metrics.type_mismatches += 1
                    self.metrics.issues.append({
                        'file': str(file_path),
                        'severity': 'medium',
                        'category': 'type',
                        'message': f"Field 'progress.{field}' should be int, got {type(value).__name__}"
                    })

            # Check boolean fields
            blocked = track_data.get('blocked')
            if blocked is not None and not isinstance(blocked, bool):
                self.metrics.type_mismatches += 1
                self.metrics.issues.append({
                    'file': str(file_path),
                    'severity': 'medium',
                    'category': 'type',
                    'message': f"Field 'blocked' should be bool, got {type(blocked).__name__}"
                })

    def check_date_consistency(self, data: Dict[str, Any], file_path: Path, file_type: str):
        """Check for date logic inconsistencies."""
        obj_data = data.get(file_type, {})

        started = obj_data.get('started')
        completed = obj_data.get('completed')

        if started and completed:
            try:
                # Parse dates (they're strings in YAML)
                from dateutil import parser
                start_dt = parser.parse(str(started))
                complete_dt = parser.parse(str(completed))

                if start_dt > complete_dt:
                    self.metrics.date_inconsistencies += 1
                    self.metrics.issues.append({
                        'file': str(file_path),
                        'severity': 'low',
                        'category': 'logic',
                        'message': f"Started date ({started}) is after completed date ({completed})"
                    })
            except Exception:
                pass  # Skip if dates can't be parsed

    def analyze_file(self, file_path: Path):
        """Analyze a single file for issues."""
        self.metrics.total_files += 1

        # Determine file type
        file_type = None
        if file_path.name == 'track.yaml':
            file_type = 'track'
            self.metrics.tracks_total += 1
        elif file_path.name == 'sprint.yaml':
            file_type = 'sprint'
            self.metrics.sprints_total += 1
        elif file_path.name == 'task.yaml':
            file_type = 'task'
            self.metrics.tasks_total += 1

        # Check YAML syntax
        if not self.check_yaml_syntax(file_path):
            self.metrics.yaml_syntax_fail += 1
            return  # Can't continue if syntax is invalid
        else:
            self.metrics.yaml_syntax_pass += 1

        # Check for Python serialization
        if self.check_python_serialization(file_path):
            self.metrics.python_serialization_found += 1

        # Load and analyze data
        try:
            with open(file_path) as f:
                data = yaml.safe_load(f)

            if data and file_type:
                self.check_enum_values(data, file_path, file_type)
                self.check_type_mismatches(data, file_path, file_type)
                self.check_date_consistency(data, file_path, file_type)

        except Exception:
            pass  # Already caught by syntax check

    def run(self) -> HealthMetrics:
        """Run health check on all roadmap files."""
        files = self.get_all_roadmap_files()

        for file_path in files:
            self.analyze_file(file_path)

        # Calculate overall health score
        self.metrics.calculate_health_score()

        return self.metrics

    def print_dashboard(self, metrics: HealthMetrics):
        """Print health dashboard to console."""
        print("\n" + "=" * 80)
        print("ROADMAP DATA HEALTH DASHBOARD")
        print("=" * 80)
        print(f"Generated: {metrics.timestamp}")
        print()

        # Overall health score
        score = metrics.overall_health_score
        score_color = self._get_score_color(score)
        score_emoji = self._get_score_emoji(score)
        print(f"{score_emoji}  OVERALL HEALTH SCORE: {score:.1f}/100 {score_color}")
        print()

        # File statistics
        print("FILE STATISTICS:")
        print(f"  Total files: {metrics.total_files}")
        print(f"  └─ Tracks: {metrics.tracks_total}")
        print(f"  └─ Sprints: {metrics.sprints_total}")
        print(f"  └─ Tasks: {metrics.tasks_total}")
        print()

        # Data quality metrics
        print("DATA QUALITY METRICS:")
        self._print_metric("YAML Syntax", metrics.yaml_syntax_pass, metrics.total_files, "✓")
        self._print_metric("Python Serialization", metrics.total_files - metrics.python_serialization_found, metrics.total_files, "✓")
        self._print_metric("Valid Enum Values", metrics.total_files - metrics.invalid_enum_values, metrics.total_files, "✓")
        self._print_metric("Correct Types", metrics.total_files - metrics.type_mismatches, metrics.total_files, "✓")
        self._print_metric("Date Consistency", metrics.total_files - metrics.date_inconsistencies, metrics.total_files, "✓")
        print()

        # Issue summary
        if metrics.issues:
            print("ISSUES FOUND:")
            critical = [i for i in metrics.issues if i['severity'] == 'critical']
            high = [i for i in metrics.issues if i['severity'] == 'high']
            medium = [i for i in metrics.issues if i['severity'] == 'medium']
            low = [i for i in metrics.issues if i['severity'] == 'low']

            if critical:
                print(f"  ❌ Critical: {len(critical)}")
            if high:
                print(f"  ⚠️  High: {len(high)}")
            if medium:
                print(f"  🔶 Medium: {len(medium)}")
            if low:
                print(f"  ℹ️  Low: {len(low)}")

            # Show top 5 issues
            print("\n  Top Issues:")
            for i, issue in enumerate(sorted(metrics.issues, key=lambda x: {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}[x['severity']])[:5], 1):
                severity_icon = {'critical': '❌', 'high': '⚠️', 'medium': '🔶', 'low': 'ℹ️'}[issue['severity']]
                file_short = Path(issue['file']).name
                print(f"    {i}. {severity_icon} [{issue['category']}] {file_short}: {issue['message']}")
        else:
            print("✅ NO ISSUES FOUND - All data is healthy!")

        print("\n" + "=" * 80)

    @staticmethod
    def _get_score_color(score: float) -> str:
        """Get color indicator for score."""
        if score >= 90:
            return "🟢 EXCELLENT"
        elif score >= 75:
            return "🟡 GOOD"
        elif score >= 50:
            return "🟠 FAIR"
        else:
            return "🔴 POOR"

    @staticmethod
    def _get_score_emoji(score: float) -> str:
        """Get emoji for score."""
        if score >= 90:
            return "✨"
        elif score >= 75:
            return "👍"
        elif score >= 50:
            return "⚠️"
        else:
            return "❌"

    @staticmethod
    def _print_metric(name: str, passed: int, total: int, icon: str):
        """Print a metric line."""
        if total == 0:
            percentage = 0.0
        else:
            percentage = (passed / total) * 100
        status = "✓" if passed == total else "✗"
        print(f"  {status} {name}: {passed}/{total} ({percentage:.1f}%)")


def main():
    parser = argparse.ArgumentParser(
        description='Roadmap data quality health dashboard'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output metrics as JSON'
    )
    parser.add_argument(
        '--export',
        type=str,
        metavar='FILE',
        help='Export metrics to JSON file'
    )

    args = parser.parse_args()

    dashboard = HealthDashboard()
    metrics = dashboard.run()

    if args.json:
        # Output as JSON
        print(json.dumps(asdict(metrics), indent=2))
    else:
        # Print dashboard
        dashboard.print_dashboard(metrics)

    if args.export:
        # Export to file
        with open(args.export, 'w') as f:
            json.dump(asdict(metrics), f, indent=2)
        print(f"\nMetrics exported to: {args.export}")

    # Exit with error code if health score is below threshold
    if metrics.overall_health_score < 50:
        sys.exit(1)


if __name__ == '__main__':
    main()
