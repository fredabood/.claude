#!/usr/bin/env python3
"""
Automated YAML cleanup script for roadmap data integrity.

Detects and fixes common YAML corruption issues:
- Python object serialization (!!python patterns)
- Incorrect enum values
- Type mismatches (strings vs integers/booleans)
- Formatting issues

Usage:
    python3 scripts/cleanup-roadmap-yaml.py [--dry-run] [--verbose]
"""

import argparse
import re
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field

# Add vibey package to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from vibey.roadmap.models.common import Status, TaskStatus, Priority, DependencyType


@dataclass
class CleanupReport:
    """Report of cleanup operations."""
    files_scanned: int = 0
    files_modified: int = 0
    issues_fixed: int = 0
    python_serialization_fixes: int = 0
    enum_fixes: int = 0
    type_fixes: int = 0
    formatting_fixes: int = 0
    errors: List[Tuple[str, str]] = field(default_factory=list)
    changes: Dict[str, List[str]] = field(default_factory=dict)

    def add_change(self, file_path: str, description: str):
        """Record a change made to a file."""
        if file_path not in self.changes:
            self.changes[file_path] = []
        self.changes[file_path].append(description)
        self.issues_fixed += 1

    def print_summary(self):
        """Print cleanup summary."""
        print("\n" + "=" * 80)
        print("CLEANUP SUMMARY")
        print("=" * 80)
        print(f"Files scanned: {self.files_scanned}")
        print(f"Files modified: {self.files_modified}")
        print(f"Total issues fixed: {self.issues_fixed}")
        print(f"  - Python serialization: {self.python_serialization_fixes}")
        print(f"  - Invalid enum values: {self.enum_fixes}")
        print(f"  - Type mismatches: {self.type_fixes}")
        print(f"  - Formatting issues: {self.formatting_fixes}")

        if self.errors:
            print(f"\nErrors encountered: {len(self.errors)}")
            for file_path, error in self.errors[:10]:
                print(f"  - {file_path}: {error}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more")

        if self.changes:
            print(f"\nModified files: {len(self.changes)}")
            for file_path, changes in list(self.changes.items())[:5]:
                print(f"\n{file_path}:")
                for change in changes:
                    print(f"  ✓ {change}")
            if len(self.changes) > 5:
                print(f"\n... and {len(self.changes) - 5} more files")


class YAMLCleaner:
    """Automated YAML cleanup engine."""

    # Valid enum values
    VALID_STATUSES = {s.value for s in Status}
    VALID_TASK_STATUSES = {s.value for s in TaskStatus}
    VALID_PRIORITIES = {p.value for p in Priority}
    VALID_DEPENDENCY_TYPES = {t.value for t in DependencyType}

    # Python serialization pattern
    PYTHON_PATTERN = re.compile(r'!!python/[^\n]+')

    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.report = CleanupReport()

    def get_roadmap_yaml_files(self) -> List[Path]:
        """Get all YAML files in the roadmap directory."""
        roadmap_dir = Path('.vibey/roadmap')
        if not roadmap_dir.exists():
            return []

        files = []
        for pattern in ['**/track.yaml', '**/sprint.yaml', '**/task.yaml']:
            files.extend(roadmap_dir.glob(pattern))
        return sorted(files)

    def fix_python_serialization(self, content: str, file_path: str) -> str:
        """Fix Python object serialization patterns."""
        matches = list(self.PYTHON_PATTERN.finditer(content))
        if not matches:
            return content

        # Fix each Python serialization pattern
        for match in reversed(matches):  # Reverse to preserve offsets
            full_match = match.group(0)
            start = match.start()

            # Look for the value on the next line (typical pattern)
            # !!python/object/apply:...
            # - value_here
            end_of_line = content.find('\n', start)
            next_line_start = end_of_line + 1
            next_line_end = content.find('\n', next_line_start)
            next_line = content[next_line_start:next_line_end].strip()

            # Extract the actual value (after "- ")
            if next_line.startswith('- '):
                value = next_line[2:].strip()

                # Replace the pattern with just the value
                # Find the key before the !!python pattern
                line_start = content.rfind('\n', 0, start) + 1
                key_match = re.match(r'(\s+)(\w+):\s+', content[line_start:start])

                if key_match:
                    indent = key_match.group(1)
                    key = key_match.group(2)
                    # Replace entire pattern with key: value
                    replacement = f"{indent}{key}: {value}"
                    content = content[:line_start] + replacement + content[next_line_end:]

                    self.report.python_serialization_fixes += 1
                    self.report.add_change(
                        str(file_path),
                        f"Fixed Python serialization for '{key}' field"
                    )

        return content

    def validate_and_fix_enums(self, data: Dict[str, Any], file_path: str, file_type: str) -> bool:
        """Validate and fix enum values in parsed data."""
        modified = False

        if file_type == 'track':
            track_data = data.get('track', {})

            # Fix track status
            status = track_data.get('status')
            if status and status not in self.VALID_STATUSES:
                closest = self._find_closest_enum(status, self.VALID_STATUSES)
                if closest:
                    track_data['status'] = closest
                    modified = True
                    self.report.enum_fixes += 1
                    self.report.add_change(
                        str(file_path),
                        f"Fixed invalid status: '{status}' → '{closest}'"
                    )

            # Fix priority
            priority = track_data.get('priority')
            if priority and priority not in self.VALID_PRIORITIES:
                closest = self._find_closest_enum(priority, self.VALID_PRIORITIES)
                if closest:
                    track_data['priority'] = closest
                    modified = True
                    self.report.enum_fixes += 1
                    self.report.add_change(
                        str(file_path),
                        f"Fixed invalid priority: '{priority}' → '{closest}'"
                    )

            # Fix sprint statuses
            for sprint in track_data.get('sprints', []):
                sprint_status = sprint.get('status')
                if sprint_status and sprint_status not in self.VALID_STATUSES:
                    closest = self._find_closest_enum(sprint_status, self.VALID_STATUSES)
                    if closest:
                        sprint['status'] = closest
                        modified = True
                        self.report.enum_fixes += 1
                        self.report.add_change(
                            str(file_path),
                            f"Fixed invalid sprint status: '{sprint_status}' → '{closest}'"
                        )

        elif file_type == 'task':
            task_data = data.get('task', {})

            # Fix task status
            status = task_data.get('status')
            if status and status not in self.VALID_TASK_STATUSES:
                closest = self._find_closest_enum(status, self.VALID_TASK_STATUSES)
                if closest:
                    task_data['status'] = closest
                    modified = True
                    self.report.enum_fixes += 1
                    self.report.add_change(
                        str(file_path),
                        f"Fixed invalid task status: '{status}' → '{closest}'"
                    )

        return modified

    def fix_type_mismatches(self, data: Dict[str, Any], file_path: str, file_type: str) -> bool:
        """Fix type mismatches (strings that should be ints/bools)."""
        modified = False

        if file_type == 'track':
            track_data = data.get('track', {})
            progress = track_data.get('progress', {})

            # Fix numeric fields that might be strings
            numeric_fields = ['sprints_total', 'sprints_completed', 'tasks_total', 'tasks_completed', 'completion_percent']
            for field in numeric_fields:
                value = progress.get(field)
                if value is not None and isinstance(value, str):
                    try:
                        progress[field] = int(value)
                        modified = True
                        self.report.type_fixes += 1
                        self.report.add_change(
                            str(file_path),
                            f"Fixed type: progress.{field} (str → int)"
                        )
                    except ValueError:
                        pass

            # Fix boolean fields
            blocked = track_data.get('blocked')
            if blocked is not None and not isinstance(blocked, bool):
                if str(blocked).lower() in ('true', '1', 'yes'):
                    track_data['blocked'] = True
                    modified = True
                    self.report.type_fixes += 1
                    self.report.add_change(str(file_path), "Fixed type: blocked (str → bool)")
                elif str(blocked).lower() in ('false', '0', 'no'):
                    track_data['blocked'] = False
                    modified = True
                    self.report.type_fixes += 1
                    self.report.add_change(str(file_path), "Fixed type: blocked (str → bool)")

        return modified

    def _find_closest_enum(self, value: str, valid_values: set) -> Optional[str]:
        """Find the closest valid enum value using simple string matching."""
        value_lower = str(value).lower().replace('_', '').replace('-', '')

        for valid in valid_values:
            valid_lower = valid.lower().replace('_', '').replace('-', '')
            if value_lower == valid_lower:
                return valid

        return None

    def cleanup_file(self, file_path: Path) -> bool:
        """Clean up a single YAML file."""
        self.report.files_scanned += 1

        try:
            # Read original content
            with open(file_path, 'r') as f:
                original_content = f.read()

            # Fix Python serialization in raw text
            content = self.fix_python_serialization(original_content, file_path)
            text_modified = (content != original_content)

            # Parse YAML
            data = yaml.safe_load(content)
            if not data:
                return False

            # Determine file type
            file_type = None
            if 'track' in data:
                file_type = 'track'
            elif 'sprint' in data:
                file_type = 'sprint'
            elif 'task' in data:
                file_type = 'task'

            if not file_type:
                return False

            # Fix enum values and types
            data_modified = False
            data_modified |= self.validate_and_fix_enums(data, file_path, file_type)
            data_modified |= self.fix_type_mismatches(data, file_path, file_type)

            # Write back if modified
            if text_modified or data_modified:
                if not self.dry_run:
                    if data_modified:
                        # Re-serialize with fixed data
                        with open(file_path, 'w') as f:
                            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
                    else:
                        # Just write the text-fixed content
                        with open(file_path, 'w') as f:
                            f.write(content)

                self.report.files_modified += 1

                if self.verbose:
                    print(f"✓ Modified: {file_path}")
                    if file_path in self.report.changes:
                        for change in self.report.changes[str(file_path)]:
                            print(f"  - {change}")

                return True

        except Exception as e:
            self.report.errors.append((str(file_path), str(e)))
            if self.verbose:
                print(f"✗ Error in {file_path}: {e}")
            return False

        return False

    def run(self):
        """Run cleanup on all roadmap YAML files."""
        print(f"{'[DRY RUN] ' if self.dry_run else ''}Scanning roadmap YAML files...")

        files = self.get_roadmap_yaml_files()
        print(f"Found {len(files)} YAML files to process\n")

        for file_path in files:
            self.cleanup_file(file_path)

        self.report.print_summary()

        if self.dry_run:
            print("\n" + "=" * 80)
            print("DRY RUN MODE - No files were actually modified")
            print("Run without --dry-run to apply changes")
            print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description='Automated YAML cleanup for roadmap data integrity'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without modifying files'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed output for each file'
    )

    args = parser.parse_args()

    cleaner = YAMLCleaner(dry_run=args.dry_run, verbose=args.verbose)
    cleaner.run()

    # Exit with error code if errors occurred
    if cleaner.report.errors:
        sys.exit(1)


if __name__ == '__main__':
    main()
