#!/usr/bin/env python3
"""
Schema migration tool for roadmap YAML files.

Automates schema transformations for version upgrades, format standardization,
and backward compatibility improvements.

Usage:
    # Dry run to see what would change
    python scripts/migrate-roadmap-schema.py --dry-run --verbose

    # Apply migrations to specific version
    python scripts/migrate-roadmap-schema.py --to-version 2.1

    # Migrate specific files
    python scripts/migrate-roadmap-schema.py --files track.yaml sprint.yaml

    # Interactive mode with confirmation
    python scripts/migrate-roadmap-schema.py --interactive
"""

import argparse
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone


# Add vibey package to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class MigrationResult:
    """Result of a migration operation."""
    file_path: Path
    success: bool
    changes_made: List[str] = field(default_factory=list)
    error: Optional[str] = None
    backed_up: bool = False
    backup_path: Optional[Path] = None


@dataclass
class MigrationReport:
    """Report of all migration operations."""
    files_processed: int = 0
    files_migrated: int = 0
    files_unchanged: int = 0
    files_failed: int = 0
    results: List[MigrationResult] = field(default_factory=list)

    def add_result(self, result: MigrationResult):
        """Add a migration result."""
        self.results.append(result)
        self.files_processed += 1

        if result.success:
            if result.changes_made:
                self.files_migrated += 1
            else:
                self.files_unchanged += 1
        else:
            self.files_failed += 1

    def print_summary(self):
        """Print migration summary."""
        print("\n" + "=" * 80)
        print("MIGRATION SUMMARY")
        print("=" * 80)
        print(f"Files processed: {self.files_processed}")
        print(f"✓ Migrated: {self.files_migrated}")
        print(f"- Unchanged: {self.files_unchanged}")
        print(f"✗ Failed: {self.files_failed}")

        if self.results:
            print("\nDetails:")
            for result in self.results[:20]:  # Show first 20
                status = "✓" if result.success else "✗"
                print(f"{status} {result.file_path}")
                if result.changes_made:
                    for change in result.changes_made[:3]:  # Show first 3 changes
                        print(f"    - {change}")
                if result.error:
                    print(f"    Error: {result.error}")

            if len(self.results) > 20:
                print(f"... and {len(self.results) - 20} more files")

        print("=" * 80)


# Migration transformations
# Each function takes a dict (parsed YAML) and returns (modified_dict, changes_list)

def migrate_dependencies_to_structured(data: Dict[str, Any], file_type: str) -> tuple[Dict[str, Any], List[str]]:
    """Convert simple string dependencies to structured format."""
    changes = []

    if file_type == 'track' and 'track' in data:
        track = data['track']

        # Migrate dependencies
        if 'dependencies' in track and isinstance(track['dependencies'], list):
            new_deps = []
            for dep in track['dependencies']:
                if isinstance(dep, str):
                    new_deps.append({
                        'type': 'track',
                        'target_id': dep,
                        'target_status': 'completed',
                        'reason': 'Dependency on track completion',
                        'optional': False
                    })
                    changes.append(f"Converted dependency '{dep}' to structured format")
                else:
                    new_deps.append(dep)
            track['dependencies'] = new_deps

        # Migrate blocks
        if 'blocks' in track and isinstance(track['blocks'], list):
            new_blocks = []
            for block in track['blocks']:
                if isinstance(block, str):
                    new_blocks.append({
                        'type': 'track',
                        'target_id': block,
                        'at_status': 'not_started',
                        'reason': 'Blocks track from starting'
                    })
                    changes.append(f"Converted block '{block}' to structured format")
                else:
                    new_blocks.append(block)
            track['blocks'] = new_blocks

    return data, changes


def migrate_add_missing_roadmap_id(data: Dict[str, Any], file_type: str) -> tuple[Dict[str, Any], List[str]]:
    """Add roadmap_id if missing."""
    changes = []
    default_roadmap = 'vibey-framework-v2'

    if file_type == 'sprint' and 'sprint' in data:
        sprint = data['sprint']
        if 'roadmap_id' not in sprint:
            sprint['roadmap_id'] = default_roadmap
            changes.append(f"Added roadmap_id: {default_roadmap}")

    elif file_type == 'task' and 'task' in data:
        task = data['task']
        if 'roadmap_id' not in task:
            task['roadmap_id'] = default_roadmap
            changes.append(f"Added roadmap_id: {default_roadmap}")

    return data, changes


def migrate_fix_null_estimated_tokens(data: Dict[str, Any], file_type: str) -> tuple[Dict[str, Any], List[str]]:
    """Fix null estimated_tokens values."""
    changes = []

    if file_type == 'task' and 'task' in data:
        task = data['task']
        if 'estimated_tokens' in task and task['estimated_tokens'] is None:
            task['estimated_tokens'] = 1
            changes.append("Fixed null estimated_tokens → 1")

    return data, changes


def migrate_rename_fields(data: Dict[str, Any], file_type: str) -> tuple[Dict[str, Any], List[str]]:
    """Rename fields for consistency."""
    changes = []

    if file_type == 'sprint' and 'sprint' in data:
        sprint = data['sprint']

        # Rename task 'name' to 'title' in task summaries
        if 'tasks' in sprint and isinstance(sprint['tasks'], list):
            for task in sprint['tasks']:
                if 'name' in task and 'title' not in task:
                    task['title'] = task.pop('name')
                    changes.append(f"Renamed task 'name' → 'title' (task: {task.get('id', 'unknown')})")

    if file_type == 'task' and 'task' in data:
        task = data['task']

        # Rename gate_info 'blocking' to 'is_blocking'
        if 'gate_info' in task and task['gate_info']:
            gi = task['gate_info']
            if 'blocking' in gi and 'is_blocking' not in gi:
                gi['is_blocking'] = gi.pop('blocking')
                changes.append("Renamed gate_info 'blocking' → 'is_blocking'")

    return data, changes


def migrate_fix_task_types(data: Dict[str, Any], file_type: str) -> tuple[Dict[str, Any], List[str]]:
    """Fix legacy task type values."""
    changes = []

    if file_type == 'task' and 'task' in data:
        task = data['task']

        # Map quality_gate → completion_gate
        if task.get('task_type') == 'quality_gate':
            task['task_type'] = 'completion_gate'
            changes.append("Migrated task_type: 'quality_gate' → 'completion_gate'")

    return data, changes


def migrate_add_missing_gate_fields(data: Dict[str, Any], file_type: str) -> tuple[Dict[str, Any], List[str]]:
    """Add missing gate_info fields."""
    changes = []

    if file_type == 'task' and 'task' in data:
        task = data['task']

        if 'gate_info' in task and task['gate_info']:
            gi = task['gate_info']

            # Add blocks_status if missing (infer from task_type)
            if 'blocks_status' not in gi:
                task_type = task.get('task_type', 'development')
                if task_type == 'completion_gate':
                    gi['blocks_status'] = 'completed'
                elif task_type == 'production_gate':
                    gi['blocks_status'] = 'production_ready'
                else:
                    gi['blocks_status'] = 'completed'
                changes.append(f"Added gate_info.blocks_status: '{gi['blocks_status']}'")

    return data, changes


def migrate_add_missing_progress(data: Dict[str, Any], file_type: str) -> tuple[Dict[str, Any], List[str]]:
    """Add minimal progress section if missing."""
    changes = []

    if file_type == 'sprint' and 'sprint' in data:
        sprint = data['sprint']

        if 'progress' not in sprint:
            # Create minimal progress
            sprint['progress'] = {
                'development_tasks_total': 0,
                'development_tasks_completed': 0,
                'completion_gate_tasks_total': 0,
                'completion_gate_tasks_completed': 0,
                'production_gate_tasks_total': 0,
                'production_gate_tasks_completed': 0,
                'tasks_total': 0,
                'tasks_completed': 0,
                'completion_percent': 0
            }
            changes.append("Added missing progress section")
        elif 'completion_percent' not in sprint['progress']:
            # Calculate completion_percent if missing
            prog = sprint['progress']
            total = prog.get('tasks_total', 0)
            completed = prog.get('tasks_completed', 0)
            prog['completion_percent'] = int((completed / total) * 100) if total > 0 else 0
            changes.append(f"Calculated completion_percent: {prog['completion_percent']}%")

    return data, changes


# Migration registry: version → list of transformations
MIGRATIONS: Dict[str, List[Callable]] = {
    '2.1': [
        migrate_dependencies_to_structured,
        migrate_add_missing_roadmap_id,
        migrate_fix_null_estimated_tokens,
        migrate_rename_fields,
        migrate_fix_task_types,
        migrate_add_missing_gate_fields,
        migrate_add_missing_progress,
    ],
}


class SchemaMigrator:
    """Schema migration orchestrator."""

    def __init__(self, dry_run: bool = False, verbose: bool = False, interactive: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.interactive = interactive
        self.report = MigrationReport()

    def detect_file_type(self, file_path: Path) -> Optional[str]:
        """Detect file type (track, sprint, task) from path."""
        if file_path.name == 'track.yaml':
            return 'track'
        elif file_path.name == 'sprint.yaml':
            return 'sprint'
        elif file_path.name == 'task.yaml':
            return 'task'
        return None

    def backup_file(self, file_path: Path) -> Optional[Path]:
        """Create backup of file."""
        if self.dry_run:
            return None

        backup_dir = file_path.parent / '.schema-migration-backups'
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = backup_dir / f"{file_path.name}.{timestamp}.bak"

        backup_path.write_text(file_path.read_text())
        return backup_path

    def migrate_file(self, file_path: Path, to_version: str) -> MigrationResult:
        """Migrate a single file."""
        result = MigrationResult(file_path=file_path, success=False)

        try:
            # Load YAML
            with open(file_path) as f:
                data = yaml.safe_load(f)

            # Detect file type
            file_type = self.detect_file_type(file_path)
            if not file_type:
                result.error = f"Unknown file type: {file_path.name}"
                return result

            # Get migrations for target version
            migrations = MIGRATIONS.get(to_version, [])
            if not migrations:
                result.error = f"No migrations defined for version {to_version}"
                return result

            # Apply transformations
            all_changes = []
            modified_data = data

            for migration_func in migrations:
                modified_data, changes = migration_func(modified_data, file_type)
                all_changes.extend(changes)

            result.changes_made = all_changes

            # If no changes, we're done
            if not all_changes:
                result.success = True
                if self.verbose:
                    print(f"✓ {file_path} - No changes needed")
                return result

            # Interactive confirmation
            if self.interactive:
                print(f"\n{file_path}:")
                for change in all_changes:
                    print(f"  - {change}")
                response = input("Apply these changes? [y/N]: ")
                if response.lower() != 'y':
                    result.error = "Skipped by user"
                    return result

            # Write changes (if not dry-run)
            if not self.dry_run:
                # Backup original
                backup_path = self.backup_file(file_path)
                result.backed_up = True
                result.backup_path = backup_path

                # Write modified data
                with open(file_path, 'w') as f:
                    yaml.safe_dump(modified_data, f, default_flow_style=False, sort_keys=False)

                if self.verbose:
                    print(f"✓ {file_path} - {len(all_changes)} changes applied")
            else:
                if self.verbose:
                    print(f"[DRY-RUN] {file_path} - Would apply {len(all_changes)} changes")

            result.success = True

        except Exception as e:
            result.error = str(e)
            if self.verbose:
                print(f"✗ {file_path} - Error: {e}")

        return result

    def migrate_directory(self, directory: Path, to_version: str, file_pattern: str = "*.yaml") -> MigrationReport:
        """Migrate all matching files in directory recursively."""
        files = list(directory.rglob(file_pattern))

        # Filter out archived files
        files = [f for f in files if 'archived' not in str(f) and '.schema-migration-backups' not in str(f)]

        print(f"Found {len(files)} files to migrate")

        for file_path in files:
            result = self.migrate_file(file_path, to_version)
            self.report.add_result(result)

        return self.report


def main():
    parser = argparse.ArgumentParser(
        description='Migrate roadmap YAML files to new schema version',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to see what would change
  python scripts/migrate-roadmap-schema.py --dry-run --verbose

  # Migrate all files to version 2.1
  python scripts/migrate-roadmap-schema.py --to-version 2.1

  # Interactive mode with confirmation
  python scripts/migrate-roadmap-schema.py --interactive --verbose

  # Migrate specific files
  python scripts/migrate-roadmap-schema.py --files .vibey/roadmap/my-track/track.yaml
        """
    )

    parser.add_argument(
        '--to-version',
        default='2.1',
        help='Target schema version (default: 2.1)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would change without modifying files'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed output'
    )
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Ask for confirmation before applying changes'
    )
    parser.add_argument(
        '--files',
        nargs='+',
        help='Specific files to migrate (default: all in .vibey/roadmap)'
    )
    parser.add_argument(
        '--directory',
        default='.vibey/roadmap',
        help='Directory to scan (default: .vibey/roadmap)'
    )

    args = parser.parse_args()

    migrator = SchemaMigrator(
        dry_run=args.dry_run,
        verbose=args.verbose,
        interactive=args.interactive
    )

    if args.files:
        # Migrate specific files
        print(f"Migrating {len(args.files)} specified files...")
        for file_path_str in args.files:
            file_path = Path(file_path_str)
            if not file_path.exists():
                print(f"✗ File not found: {file_path}")
                continue

            result = migrator.migrate_file(file_path, args.to_version)
            migrator.report.add_result(result)
    else:
        # Migrate entire directory
        directory = Path(args.directory)
        if not directory.exists():
            print(f"✗ Directory not found: {directory}")
            sys.exit(1)

        migrator.migrate_directory(directory, args.to_version)

    # Print summary
    migrator.report.print_summary()

    # Exit with error code if any failures
    if migrator.report.files_failed > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
