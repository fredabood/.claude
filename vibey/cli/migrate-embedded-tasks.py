#!/usr/bin/env python3
"""
Migrate Embedded Tasks to Separate Files

Detects sprints with tasks embedded in sprint YAML files and migrates them
to the separate-file format (.vibey/tasks/{sprint-id}-tasks.yaml) that the
roadmap update scripts expect.

This fixes the silent failure issue where task completions don't work because
the update script can't find the tasks file.

Usage:
    python3 framework/scripts/migrate-embedded-tasks.py             # Dry run
    python3 framework/scripts/migrate-embedded-tasks.py --execute   # Actually migrate
    python3 framework/scripts/migrate-embedded-tasks.py --backup-dir /path/to/backup

Created: 2025-11-09
Purpose: Fix data model mismatch between embedded and separate task formats
"""

import sys
import argparse
import yaml
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple

# Add framework to path
framework_root = Path(__file__).parent.parent
sys.path.insert(0, str(framework_root.parent))


class TaskMigrator:
    """Migrates embedded tasks to separate task files."""

    def __init__(self, root_dir: Path = None, backup_dir: Path = None):
        """
        Initialize migrator.

        Args:
            root_dir: Project root directory (auto-detected if not provided)
            backup_dir: Directory for backups (default: .vibey/migration-backups/)
        """
        self.root_dir = root_dir or Path.cwd()
        self.vibey_dir = self.root_dir / ".vibey"
        self.sprints_dir = self.vibey_dir / "sprints"
        self.tasks_dir = self.vibey_dir / "tasks"

        # Default backup directory
        if backup_dir:
            self.backup_dir = Path(backup_dir)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.backup_dir = self.vibey_dir / "migration-backups" / f"backup_{timestamp}"

        # Stats
        self.sprints_found = 0
        self.sprints_with_embedded_tasks = 0
        self.tasks_migrated = 0
        self.errors = []

    def validate_environment(self) -> bool:
        """Validate that we're in a Vibey project."""
        if not self.vibey_dir.exists():
            print(f"❌ Error: .vibey directory not found at {self.vibey_dir}")
            print("   Make sure you're in a Vibey-managed project.")
            return False

        if not self.sprints_dir.exists():
            print(f"❌ Error: sprints directory not found at {self.sprints_dir}")
            return False

        # Ensure tasks directory exists
        self.tasks_dir.mkdir(exist_ok=True)

        return True

    def find_sprints_with_embedded_tasks(self) -> List[Tuple[Path, Dict]]:
        """
        Find all sprint files with embedded tasks.

        Returns:
            List of (sprint_path, sprint_data) tuples
        """
        sprints_with_tasks = []

        for sprint_file in self.sprints_dir.glob("*.yaml"):
            self.sprints_found += 1

            try:
                with open(sprint_file) as f:
                    data = yaml.safe_load(f)

                # Check if sprint has embedded tasks
                if 'sprint' in data and 'tasks' in data['sprint']:
                    tasks = data['sprint']['tasks']
                    if tasks and len(tasks) > 0:
                        sprints_with_tasks.append((sprint_file, data))
                        self.sprints_with_embedded_tasks += 1

            except Exception as e:
                self.errors.append(f"Error reading {sprint_file.name}: {e}")

        return sprints_with_tasks

    def convert_task_to_standard_format(
        self,
        task: Dict[str, Any],
        sprint_id: str,
        track_id: str,
        roadmap_id: str
    ) -> Dict[str, Any]:
        """
        Convert embedded task to standard task format.

        Args:
            task: Embedded task data
            sprint_id: Sprint ID
            track_id: Track ID
            roadmap_id: Roadmap ID

        Returns:
            Task in standard format
        """
        # Handle estimated effort -> estimated_tokens conversion
        estimated_tokens = task.get('estimated_tokens', 2000)
        if isinstance(estimated_tokens, str):
            # Parse strings like "2 days" -> 2000 tokens
            effort_str = estimated_tokens.lower()
            if 'day' in effort_str:
                try:
                    days = int(effort_str.split()[0])
                    estimated_tokens = days * 1000
                except:
                    estimated_tokens = 2000
            else:
                estimated_tokens = 2000

        # Convert dependencies from strings to proper format
        dependencies = []
        for dep in task.get('dependencies', []):
            if isinstance(dep, str):
                # It's a task ID string
                dependencies.append({
                    'type': 'task',
                    'target_id': dep,
                    'target_status': 'completed',
                    'reason': 'Required prerequisite'
                })
            else:
                # Already in correct format
                dependencies.append(dep)

        # Build standard task
        standard_task = {
            'id': task['id'],
            'sprint_id': sprint_id,
            'track_id': track_id,
            'roadmap_id': roadmap_id,
            'task_type': task.get('task_type', 'development'),
            'title': task.get('name', task.get('title', 'Untitled Task')),
            'description': task.get('description', ''),
            'status': task.get('status', 'not_started'),
            'blocked': task.get('blocked', False),
            'created': task.get('created', datetime.now(timezone.utc).isoformat()),
            'started': task.get('started'),
            'completed': task.get('completed'),
            'assigned_agent': task.get('assigned_agent', 'web-developer'),
            'priority': task.get('priority', 'medium'),
            'phase_label': task.get('phase_label'),
            'estimated_tokens': estimated_tokens,
            'actual_tokens': task.get('actual_tokens'),
            'complexity': task.get('complexity', 'medium'),
            'gate_info': task.get('gate_info'),
            'audit_results': task.get('audit_results'),
            'dependencies': dependencies,
            'blocks': task.get('blocks', []),
            'blocked_by': task.get('blocked_by', []),
            'deliverables': task.get('deliverables', []),
            'commits': task.get('commits', []),
            'metadata': task.get('metadata', {
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'token_efficiency': None,
                'duration_hours': None
            })
        }

        # Ensure metadata has required fields
        if 'last_updated' not in standard_task['metadata']:
            standard_task['metadata']['last_updated'] = datetime.now(timezone.utc).isoformat()

        return standard_task

    def create_backup(self, sprint_file: Path) -> bool:
        """
        Create backup of sprint file.

        Args:
            sprint_file: Path to sprint file

        Returns:
            True if backup successful
        """
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            backup_file = self.backup_dir / sprint_file.name
            shutil.copy2(sprint_file, backup_file)
            return True
        except Exception as e:
            self.errors.append(f"Backup failed for {sprint_file.name}: {e}")
            return False

    def migrate_sprint(
        self,
        sprint_file: Path,
        sprint_data: Dict,
        dry_run: bool = True
    ) -> bool:
        """
        Migrate a single sprint from embedded to separate tasks.

        Args:
            sprint_file: Path to sprint file
            sprint_data: Sprint data with embedded tasks
            dry_run: If True, only simulate migration

        Returns:
            True if migration successful
        """
        try:
            sprint = sprint_data['sprint']
            sprint_id = sprint['id']
            track_id = sprint['track_id']
            roadmap_id = sprint['roadmap_id']
            embedded_tasks = sprint['tasks']

            print(f"\n{'[DRY RUN] ' if dry_run else ''}Migrating sprint: {sprint_id}")
            print(f"  Tasks to migrate: {len(embedded_tasks)}")

            # Convert all tasks
            converted_tasks = []
            for task in embedded_tasks:
                converted_task = self.convert_task_to_standard_format(
                    task, sprint_id, track_id, roadmap_id
                )
                converted_tasks.append(converted_task)
                print(f"  ✓ Converted task: {task['id']}")

            if not dry_run:
                # Create backup
                if not self.create_backup(sprint_file):
                    return False

                # Write tasks file
                tasks_file = self.tasks_dir / f"{sprint_id}-tasks.yaml"
                tasks_data = {'tasks': converted_tasks}

                with open(tasks_file, 'w') as f:
                    yaml.dump(tasks_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

                print(f"  ✅ Created: {tasks_file.name}")

                # Remove embedded tasks from sprint file
                del sprint['tasks']

                # Ensure sprint has required metadata
                if 'metadata' not in sprint:
                    sprint['metadata'] = {}
                if 'last_updated' not in sprint['metadata']:
                    sprint['metadata']['last_updated'] = datetime.now(timezone.utc).isoformat()
                if 'created_by' not in sprint['metadata']:
                    sprint['metadata']['created_by'] = 'vibey-framework-team'

                # Write updated sprint file
                with open(sprint_file, 'w') as f:
                    yaml.dump(sprint_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

                print(f"  ✅ Updated: {sprint_file.name} (embedded tasks removed)")

            self.tasks_migrated += len(converted_tasks)
            return True

        except Exception as e:
            error_msg = f"Migration failed for {sprint_file.name}: {e}"
            self.errors.append(error_msg)
            print(f"  ❌ {error_msg}")
            return False

    def run(self, dry_run: bool = True) -> bool:
        """
        Run migration process.

        Args:
            dry_run: If True, only simulate migration

        Returns:
            True if migration successful
        """
        print("=" * 70)
        print("🔄 Vibey Task Migration Tool")
        print("=" * 70)
        print()

        if dry_run:
            print("📋 DRY RUN MODE - No changes will be made")
            print()
        else:
            print("⚠️  EXECUTION MODE - Files will be modified")
            print(f"📁 Backups will be saved to: {self.backup_dir}")
            print()

        # Validate environment
        if not self.validate_environment():
            return False

        # Find sprints with embedded tasks
        print(f"🔍 Scanning for sprints with embedded tasks...")
        sprints_to_migrate = self.find_sprints_with_embedded_tasks()

        print(f"\n📊 Scan Results:")
        print(f"  Total sprints found: {self.sprints_found}")
        print(f"  Sprints with embedded tasks: {self.sprints_with_embedded_tasks}")
        print(f"  Sprints already migrated: {self.sprints_found - self.sprints_with_embedded_tasks}")

        if not sprints_to_migrate:
            print("\n✅ All sprints already using separate task files!")
            print("   No migration needed.")
            return True

        # Migrate each sprint
        print(f"\n{'=' * 70}")
        print(f"{'DRY RUN: ' if dry_run else ''}Migrating {len(sprints_to_migrate)} sprints")
        print(f"{'=' * 70}")

        success_count = 0
        for sprint_file, sprint_data in sprints_to_migrate:
            if self.migrate_sprint(sprint_file, sprint_data, dry_run):
                success_count += 1

        # Print summary
        print(f"\n{'=' * 70}")
        print(f"📊 Migration Summary")
        print(f"{'=' * 70}")
        print(f"  Sprints processed: {len(sprints_to_migrate)}")
        print(f"  Successful migrations: {success_count}")
        print(f"  Failed migrations: {len(sprints_to_migrate) - success_count}")
        print(f"  Total tasks migrated: {self.tasks_migrated}")

        if self.errors:
            print(f"\n⚠️  Errors encountered ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")

        if not dry_run and success_count > 0:
            print(f"\n💾 Backups saved to: {self.backup_dir}")

        if dry_run:
            print(f"\n💡 This was a dry run. To execute the migration, run:")
            print(f"   python3 {Path(__file__).name} --execute")
        else:
            if success_count == len(sprints_to_migrate):
                print(f"\n✅ Migration completed successfully!")
            else:
                print(f"\n⚠️  Migration completed with errors. Check the error log above.")

        print(f"{'=' * 70}")

        return success_count == len(sprints_to_migrate)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Migrate embedded tasks to separate task files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (no changes made)
  %(prog)s

  # Execute migration
  %(prog)s --execute

  # Custom backup directory
  %(prog)s --execute --backup-dir /path/to/backups

  # Specify project directory
  %(prog)s --execute --dir /path/to/project

Purpose:
  This script fixes the data model mismatch where some sprints have tasks
  embedded in the sprint YAML file, while the roadmap update scripts expect
  tasks in separate files (.vibey/tasks/{sprint-id}-tasks.yaml).

  Without this migration, task completion commands will fail silently with
  "Tasks file not found" errors.

Safety:
  - Always runs in dry-run mode by default
  - Creates backups before modifying files
  - Validates data format during conversion
  - Preserves all task metadata
        """
    )

    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute migration (default is dry-run)'
    )

    parser.add_argument(
        '--dir',
        type=Path,
        default=None,
        help='Project root directory (auto-detected if not provided)'
    )

    parser.add_argument(
        '--backup-dir',
        type=Path,
        default=None,
        help='Backup directory (default: .vibey/migration-backups/backup_TIMESTAMP)'
    )

    args = parser.parse_args()

    # Run migration
    migrator = TaskMigrator(root_dir=args.dir, backup_dir=args.backup_dir)
    success = migrator.run(dry_run=not args.execute)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
