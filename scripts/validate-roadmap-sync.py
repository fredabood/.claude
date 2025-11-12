#!/usr/bin/env python3
"""
Roadmap Synchronization Validator

Checks for discrepancies between track.yaml files and the main roadmap.yaml.
Identifies:
- Status mismatches (track completed but roadmap shows not_started)
- Missing tracks (track directory exists but not in roadmap.yaml)
- Orphaned tracks (in roadmap.yaml but no track directory)
- Progress metric drift (calculated vs stored)

Usage:
    python3 scripts/validate-roadmap-sync.py
    python3 scripts/validate-roadmap-sync.py --fix  # Auto-fix issues
    python3 scripts/validate-roadmap-sync.py --verbose  # Show all details
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, List, Set, Tuple
from datetime import datetime, timezone

# Add vibey to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


class ValidationIssue:
    """Represents a validation issue found during sync check."""

    def __init__(self, severity: str, category: str, message: str, details: Dict = None):
        self.severity = severity  # CRITICAL, HIGH, MEDIUM, LOW
        self.category = category  # STATUS_MISMATCH, MISSING_TRACK, etc.
        self.message = message
        self.details = details or {}
        self.fixable = False

    def __str__(self):
        icon = {
            'CRITICAL': '🔴',
            'HIGH': '🟠',
            'MEDIUM': '🟡',
            'LOW': '🟢'
        }
        return f"{icon.get(self.severity, '⚪')} [{self.severity}] {self.message}"


class RoadmapSyncValidator:
    """Validates synchronization between roadmap.yaml and track files."""

    def __init__(self, root_dir: Path = None):
        self.root_dir = root_dir or Path.cwd()
        self.vibey_dir = self.root_dir / '.vibey'
        self.roadmap_file = self.vibey_dir / 'roadmap.yaml'
        self.roadmap_dir = self.vibey_dir / 'roadmap'

        self.issues: List[ValidationIssue] = []
        self.roadmap_data = None
        self.track_files = {}

    def load_roadmap(self) -> Dict:
        """Load main roadmap.yaml file."""
        if not self.roadmap_file.exists():
            raise FileNotFoundError(f"Roadmap not found: {self.roadmap_file}")

        with open(self.roadmap_file, 'r') as f:
            return yaml.safe_load(f)

    def load_track_files(self) -> Dict[str, Dict]:
        """Load all track.yaml files from .vibey/roadmap/*/track.yaml."""
        tracks = {}

        if not self.roadmap_dir.exists():
            return tracks

        for track_dir in self.roadmap_dir.iterdir():
            if not track_dir.is_dir():
                continue

            track_file = track_dir / 'track.yaml'
            if track_file.exists():
                with open(track_file, 'r') as f:
                    track_data = yaml.safe_load(f)
                    track_id = track_data['track']['id']
                    tracks[track_id] = {
                        'data': track_data['track'],
                        'file': track_file
                    }

        return tracks

    def validate_status_sync(self):
        """Check if track statuses match between files."""
        roadmap = self.roadmap_data['roadmap']
        tracks_in_roadmap = {t['id']: t for t in roadmap['tracks']}

        for track_id, track_info in self.track_files.items():
            if track_id not in tracks_in_roadmap:
                continue  # Handled by validate_track_coverage

            roadmap_status = tracks_in_roadmap[track_id]['status']
            actual_status = track_info['data']['status']

            if roadmap_status != actual_status:
                # Allow production_ready > completed
                if actual_status == 'production_ready' and roadmap_status == 'completed':
                    continue

                issue = ValidationIssue(
                    severity='CRITICAL' if actual_status == 'completed' else 'HIGH',
                    category='STATUS_MISMATCH',
                    message=f"Track '{track_id}' status mismatch",
                    details={
                        'track_id': track_id,
                        'roadmap_status': roadmap_status,
                        'actual_status': actual_status,
                        'track_file': str(track_info['file'])
                    }
                )
                issue.fixable = True
                self.issues.append(issue)

    def validate_track_coverage(self):
        """Check if all tracks are registered in both places."""
        roadmap = self.roadmap_data['roadmap']
        tracks_in_roadmap = {t['id'] for t in roadmap['tracks']}
        actual_tracks = set(self.track_files.keys())

        # Tracks with files but not in roadmap.yaml
        missing_from_roadmap = actual_tracks - tracks_in_roadmap
        for track_id in missing_from_roadmap:
            track_info = self.track_files[track_id]
            issue = ValidationIssue(
                severity='HIGH',
                category='MISSING_TRACK',
                message=f"Track '{track_id}' exists but not in roadmap.yaml",
                details={
                    'track_id': track_id,
                    'track_name': track_info['data']['name'],
                    'status': track_info['data']['status'],
                    'priority': track_info['data'].get('priority', 'unknown')
                }
            )
            issue.fixable = True
            self.issues.append(issue)

        # Tracks in roadmap.yaml but no files
        orphaned_tracks = tracks_in_roadmap - actual_tracks
        for track_id in orphaned_tracks:
            issue = ValidationIssue(
                severity='MEDIUM',
                category='ORPHANED_TRACK',
                message=f"Track '{track_id}' in roadmap.yaml but no track file",
                details={'track_id': track_id}
            )
            self.issues.append(issue)

    def validate_progress_metrics(self):
        """Check if progress metrics match calculated values."""
        roadmap = self.roadmap_data['roadmap']
        stored_progress = roadmap['progress']

        # Calculate actual metrics
        tracks_in_roadmap = roadmap['tracks']
        actual_tracks_total = len(tracks_in_roadmap)
        actual_tracks_completed = sum(
            1 for t in tracks_in_roadmap
            if t['status'] in ['completed', 'production_ready', 'deployed']
        )

        # Calculate sprints and tasks from track files
        actual_sprints_total = 0
        actual_sprints_completed = 0
        actual_tasks_total = 0
        actual_tasks_completed = 0

        for track_id in [t['id'] for t in tracks_in_roadmap]:
            if track_id in self.track_files:
                track = self.track_files[track_id]['data']
                progress = track.get('progress', {})

                actual_sprints_total += progress.get('sprints_total', 0)
                actual_sprints_completed += progress.get('sprints_completed', 0)
                actual_tasks_total += progress.get('tasks_total', 0)
                actual_tasks_completed += progress.get('tasks_completed', 0)

        # Calculate completion percentage
        if actual_tasks_total > 0:
            actual_completion = int((actual_tasks_completed / actual_tasks_total) * 100)
        else:
            actual_completion = 0

        # Check for drift
        discrepancies = []

        if stored_progress['tracks_total'] != actual_tracks_total:
            discrepancies.append(f"tracks_total: {stored_progress['tracks_total']} → {actual_tracks_total}")

        if stored_progress['tracks_completed'] != actual_tracks_completed:
            discrepancies.append(f"tracks_completed: {stored_progress['tracks_completed']} → {actual_tracks_completed}")

        if stored_progress['sprints_total'] != actual_sprints_total:
            discrepancies.append(f"sprints_total: {stored_progress['sprints_total']} → {actual_sprints_total}")

        if stored_progress['sprints_completed'] != actual_sprints_completed:
            discrepancies.append(f"sprints_completed: {stored_progress['sprints_completed']} → {actual_sprints_completed}")

        if stored_progress['tasks_total'] != actual_tasks_total:
            discrepancies.append(f"tasks_total: {stored_progress['tasks_total']} → {actual_tasks_total}")

        if stored_progress['tasks_completed'] != actual_tasks_completed:
            discrepancies.append(f"tasks_completed: {stored_progress['tasks_completed']} → {actual_tasks_completed}")

        if stored_progress['completion_percent'] != actual_completion:
            discrepancies.append(f"completion_percent: {stored_progress['completion_percent']}% → {actual_completion}%")

        if discrepancies:
            issue = ValidationIssue(
                severity='MEDIUM',
                category='PROGRESS_DRIFT',
                message=f"Progress metrics drift detected ({len(discrepancies)} metrics)",
                details={
                    'discrepancies': discrepancies,
                    'stored': stored_progress,
                    'calculated': {
                        'tracks_total': actual_tracks_total,
                        'tracks_completed': actual_tracks_completed,
                        'sprints_total': actual_sprints_total,
                        'sprints_completed': actual_sprints_completed,
                        'tasks_total': actual_tasks_total,
                        'tasks_completed': actual_tasks_completed,
                        'completion_percent': actual_completion
                    }
                }
            )
            issue.fixable = True
            self.issues.append(issue)

    def validate_all(self) -> List[ValidationIssue]:
        """Run all validation checks."""
        print(f"{Colors.BOLD}Validating Roadmap Synchronization...{Colors.END}\n")

        # Load data
        print("📂 Loading roadmap data...")
        self.roadmap_data = self.load_roadmap()
        self.track_files = self.load_track_files()

        print(f"   Found {len(self.roadmap_data['roadmap']['tracks'])} tracks in roadmap.yaml")
        print(f"   Found {len(self.track_files)} track files in .vibey/roadmap/")
        print()

        # Run validations
        print("🔍 Running validation checks...")
        self.validate_status_sync()
        self.validate_track_coverage()
        self.validate_progress_metrics()
        print()

        return self.issues

    def print_report(self, verbose: bool = False):
        """Print validation report."""
        if not self.issues:
            print(f"{Colors.GREEN}{Colors.BOLD}✅ All validation checks passed!{Colors.END}")
            print(f"{Colors.GREEN}Roadmap is synchronized correctly.{Colors.END}\n")
            return

        # Group by severity
        by_severity = {
            'CRITICAL': [],
            'HIGH': [],
            'MEDIUM': [],
            'LOW': []
        }

        for issue in self.issues:
            by_severity[issue.severity].append(issue)

        # Print summary
        print(f"{Colors.BOLD}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}VALIDATION ISSUES FOUND{Colors.END}")
        print(f"{Colors.BOLD}{'='*80}{Colors.END}\n")

        total = len(self.issues)
        fixable = sum(1 for i in self.issues if i.fixable)

        print(f"Total Issues: {Colors.RED}{total}{Colors.END}")
        print(f"Auto-Fixable: {Colors.GREEN}{fixable}{Colors.END}")
        print()

        for severity_level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            issues = by_severity[severity_level]
            if not issues:
                continue

            color = {
                'CRITICAL': Colors.RED,
                'HIGH': Colors.YELLOW,
                'MEDIUM': Colors.BLUE,
                'LOW': Colors.GREEN
            }[severity_level]

            print(f"{color}{Colors.BOLD}{severity_level} Issues ({len(issues)}):{Colors.END}")
            print(f"{color}{'─'*80}{Colors.END}\n")

            for issue in issues:
                print(f"  {issue}")

                if verbose and issue.details:
                    for key, value in issue.details.items():
                        if isinstance(value, list):
                            print(f"    {key}:")
                            for item in value:
                                print(f"      - {item}")
                        elif isinstance(value, dict):
                            print(f"    {key}:")
                            for k, v in value.items():
                                print(f"      {k}: {v}")
                        else:
                            print(f"    {key}: {value}")

                print()

        print(f"{Colors.BOLD}{'='*80}{Colors.END}\n")

        if fixable > 0:
            print(f"{Colors.CYAN}💡 Tip: Run with --fix to automatically resolve {fixable} issue(s){Colors.END}\n")

    def fix_issues(self):
        """Automatically fix issues where possible."""
        print(f"{Colors.BOLD}Attempting to fix issues...{Colors.END}\n")

        fixable_issues = [i for i in self.issues if i.fixable]

        if not fixable_issues:
            print(f"{Colors.YELLOW}No auto-fixable issues found.{Colors.END}\n")
            return

        fixed_count = 0

        for issue in fixable_issues:
            print(f"Fixing: {issue.message}...", end=" ")

            try:
                if issue.category == 'STATUS_MISMATCH':
                    self._fix_status_mismatch(issue)
                    fixed_count += 1
                    print(f"{Colors.GREEN}✓{Colors.END}")

                elif issue.category == 'MISSING_TRACK':
                    self._fix_missing_track(issue)
                    fixed_count += 1
                    print(f"{Colors.GREEN}✓{Colors.END}")

                elif issue.category == 'PROGRESS_DRIFT':
                    self._fix_progress_drift(issue)
                    fixed_count += 1
                    print(f"{Colors.GREEN}✓{Colors.END}")

                else:
                    print(f"{Colors.YELLOW}⊘ (not implemented){Colors.END}")

            except Exception as e:
                print(f"{Colors.RED}✗ Error: {e}{Colors.END}")

        print()
        print(f"{Colors.GREEN}{Colors.BOLD}Fixed {fixed_count}/{len(fixable_issues)} issues{Colors.END}\n")

        # Save updated roadmap
        if fixed_count > 0:
            self._save_roadmap()
            print(f"{Colors.GREEN}Roadmap saved: {self.roadmap_file}{Colors.END}\n")

    def _fix_status_mismatch(self, issue: ValidationIssue):
        """Fix status mismatch by updating roadmap.yaml."""
        track_id = issue.details['track_id']
        new_status = issue.details['actual_status']

        # Update in roadmap data
        for track in self.roadmap_data['roadmap']['tracks']:
            if track['id'] == track_id:
                track['status'] = new_status
                break

    def _fix_missing_track(self, issue: ValidationIssue):
        """Fix missing track by adding to roadmap.yaml."""
        track_id = issue.details['track_id']

        # Create track entry
        new_track = {
            'id': track_id,
            'name': issue.details['track_name'],
            'status': issue.details['status'],
            'priority': issue.details['priority']
        }

        # Add to roadmap
        self.roadmap_data['roadmap']['tracks'].append(new_track)

    def _fix_progress_drift(self, issue: ValidationIssue):
        """Fix progress metrics drift."""
        calculated = issue.details['calculated']

        # Update progress metrics
        self.roadmap_data['roadmap']['progress'] = calculated

    def _save_roadmap(self):
        """Save updated roadmap.yaml."""
        # Create backup first
        backup_file = self.roadmap_file.with_suffix('.yaml.bak')
        if self.roadmap_file.exists():
            import shutil
            shutil.copy(self.roadmap_file, backup_file)
            print(f"   Backup created: {backup_file}")

        # Save updated roadmap
        with open(self.roadmap_file, 'w') as f:
            yaml.dump(self.roadmap_data, f, default_flow_style=False, sort_keys=False)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Validate roadmap synchronization',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--fix',
        action='store_true',
        help='Automatically fix issues where possible'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed information about issues'
    )
    parser.add_argument(
        '--dir',
        type=Path,
        help='Root directory (defaults to current directory)'
    )

    args = parser.parse_args()

    # Run validation
    validator = RoadmapSyncValidator(root_dir=args.dir)

    try:
        issues = validator.validate_all()
        validator.print_report(verbose=args.verbose)

        if args.fix and issues:
            validator.fix_issues()

            # Re-validate after fixes
            print(f"\n{Colors.BOLD}Re-validating after fixes...{Colors.END}\n")
            validator = RoadmapSyncValidator(root_dir=args.dir)
            remaining_issues = validator.validate_all()
            validator.print_report(verbose=args.verbose)

            if remaining_issues:
                sys.exit(1)
        elif issues:
            sys.exit(1)

        sys.exit(0)

    except FileNotFoundError as e:
        print(f"{Colors.RED}Error: {e}{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}Unexpected error: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
