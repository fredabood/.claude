#!/usr/bin/env python3
"""
Migrate Legacy Sprint State to Roadmap System

Migrates sprint data from legacy structure:
  docs/sprints/sprint-{N}-state.yaml
  docs/sprints/sprint-{N}-plan.md

To hierarchical roadmap structure:
  .vibey/roadmap.yaml (if not exists)
  .vibey/roadmap/{track}/{sprint}/sprint.yaml
  .vibey/roadmap/{track}/{sprint}/{task}/task.yaml

This migration tool is for projects that were using the old sprint state
system (docs/sprints/*.yaml) and need to upgrade to the new roadmap system.

Usage:
    python3 framework/scripts/migrate-to-roadmap.py                # Dry run
    python3 framework/scripts/migrate-to-roadmap.py --execute      # Migrate
    python3 framework/scripts/migrate-to-roadmap.py --track main   # Specify track
"""

import sys
import argparse
import yaml
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

# Add repository root to path
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))

try:
    from framework.roadmap.models import (
        Sprint, Task, TaskStatus, Priority, Complexity
    )
    from framework.roadmap.serialization import (
        save_sprint, save_tasks, load_roadmap, save_roadmap
    )
    from framework.roadmap.directory_manager import DirectoryManager
    HAS_ROADMAP = True
except ImportError as e:
    HAS_ROADMAP = False
    print(f"⚠️  Warning: Roadmap modules not found. Limited functionality.")


class LegacySprintParser:
    """Parse legacy sprint state files."""

    def __init__(self, state_file: Path, plan_file: Optional[Path] = None):
        """
        Initialize parser.

        Args:
            state_file: Path to sprint-N-state.yaml
            plan_file: Optional path to sprint-N-plan.md
        """
        self.state_file = state_file
        self.plan_file = plan_file

        # Load state
        with open(state_file) as f:
            self.state = yaml.safe_load(f)

    def get_sprint_metadata(self) -> Dict:
        """Extract sprint metadata from state file."""
        sprint_data = self.state.get('sprint', {})

        # Extract sprint number from filename
        match = re.search(r'sprint-(\d+)-state', self.state_file.name)
        sprint_num = match.group(1) if match else '1'

        metadata = {
            'sprint_id': sprint_data.get('id', f'sprint-{sprint_num}'),
            'name': sprint_data.get('name', f'Sprint {sprint_num}'),
            'goal': sprint_data.get('goal', ''),
            'status': sprint_data.get('status', 'not_started'),
            'started': sprint_data.get('started'),
            'completed': sprint_data.get('completed'),
            'duration': sprint_data.get('duration', '2 weeks'),
        }

        return metadata

    def get_phases(self) -> List[Dict]:
        """Extract phases from state file."""
        return self.state.get('phases', [])

    def get_tasks_from_phases(self) -> List[Dict]:
        """Extract tasks from phases."""
        tasks = []
        phases = self.get_phases()

        for phase_num, phase in enumerate(phases, 1):
            phase_label = f"Phase {phase_num}"
            phase_tasks = phase.get('tasks', [])

            for task_num, task in enumerate(phase_tasks, 1):
                task_id = task.get('id', f'task-{phase_num}-{task_num}')

                task_data = {
                    'id': task_id,
                    'title': task.get('title', 'Untitled Task'),
                    'description': task.get('description', ''),
                    'status': task.get('status', 'not_started'),
                    'started': task.get('started'),
                    'completed': task.get('completed'),
                    'assigned_agent': task.get('assigned_agent', 'web-developer'),
                    'phase_label': phase_label,
                    'complexity': task.get('complexity', 'medium'),
                    'estimated_tokens': task.get('estimated_tokens', 5000),
                }

                tasks.append(task_data)

        return tasks

    def get_quality_gates(self) -> List[Dict]:
        """Extract quality gates from state file."""
        return self.state.get('quality_gates', [])


class RoadmapMigrator:
    """Migrate legacy sprints to roadmap system."""

    def __init__(self, root_dir: Path = None, backup: bool = True):
        """
        Initialize migrator.

        Args:
            root_dir: Project root directory
            backup: Whether to create backups
        """
        if not HAS_ROADMAP:
            print("❌ Error: Roadmap system not available")
            print("   Please ensure framework/roadmap/ modules are installed")
            sys.exit(1)

        self.root_dir = root_dir or Path.cwd()
        self.vibey_dir = self.root_dir / ".vibey"
        self.docs_sprints_dir = self.root_dir / "docs" / "sprints"

        # Initialize directory manager
        roadmap_root = self.vibey_dir / "roadmap"
        self.dir_manager = DirectoryManager(str(roadmap_root))

        # Backup
        self.backup = backup
        if backup:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.backup_dir = self.vibey_dir / "roadmap-migration-backups" / f"backup_{timestamp}"

        # Stats
        self.sprints_migrated = 0
        self.tasks_migrated = 0
        self.errors = []

    def find_legacy_sprints(self) -> List[Path]:
        """Find all legacy sprint state files."""
        if not self.docs_sprints_dir.exists():
            return []

        state_files = list(self.docs_sprints_dir.glob("sprint-*-state.yaml"))
        return sorted(state_files)

    def init_roadmap_if_needed(self, project_name: str = None, dry_run: bool = True):
        """Initialize roadmap.yaml if it doesn't exist."""
        roadmap_yaml = self.vibey_dir / "roadmap.yaml"

        if roadmap_yaml.exists():
            print(f"✓ Roadmap already exists: {roadmap_yaml}")
            return

        if dry_run:
            print(f"  [DRY RUN] Would create: {roadmap_yaml}")
            return

        # Create minimal roadmap
        project_name = project_name or self.root_dir.name or "Project"

        roadmap_data = {
            'roadmap': {
                'id': 'main-roadmap',
                'name': f'{project_name} Roadmap',
                'version': '1.0.0',
                'created': datetime.now(timezone.utc).isoformat(),
                'status': 'active',
                'tracks': [],
                'activity_log': []
            }
        }

        roadmap_yaml.parent.mkdir(parents=True, exist_ok=True)
        with open(roadmap_yaml, 'w') as f:
            yaml.dump(roadmap_data, f, default_flow_style=False, sort_keys=False)

        print(f"✓ Created: {roadmap_yaml}")

    def create_backup(self, sprint_file: Path):
        """Create backup of sprint file."""
        if not self.backup:
            return

        self.backup_dir.mkdir(parents=True, exist_ok=True)
        backup_file = self.backup_dir / sprint_file.name

        import shutil
        shutil.copy2(sprint_file, backup_file)

    def migrate_sprint(
        self,
        state_file: Path,
        track_id: str = "main",
        dry_run: bool = True
    ) -> Tuple[bool, str]:
        """
        Migrate a single sprint from legacy format to roadmap.

        Args:
            state_file: Path to sprint-N-state.yaml
            track_id: Track ID to assign sprint to
            dry_run: If True, only show what would be done

        Returns:
            (success, message) tuple
        """
        try:
            # Parse legacy sprint
            plan_file = state_file.with_name(state_file.name.replace('-state.yaml', '-plan.md'))
            if not plan_file.exists():
                plan_file = None

            parser = LegacySprintParser(state_file, plan_file)
            metadata = parser.get_sprint_metadata()
            tasks = parser.get_tasks_from_phases()

            sprint_id = metadata['sprint_id']
            sprint_name = metadata['name']

            print(f"\n📋 Sprint: {sprint_name} ({sprint_id})")
            print(f"   Tasks: {len(tasks)}")
            print(f"   Status: {metadata['status']}")

            if dry_run:
                print(f"   [DRY RUN] Would migrate to: .vibey/roadmap/{track_id}/{sprint_id}/")
                for task in tasks:
                    print(f"      - {task['id']}: {task['title']}")
                return True, "Dry run successful"

            # Create backup
            self.create_backup(state_file)

            # Create sprint directory
            sprint_dir = self.dir_manager.create_sprint_directory(
                track_slug=track_id,
                sprint_id=sprint_id,
                sprint_slug=sprint_id,
                create_context=True
            )

            # Create Sprint object
            status_map = {
                'not_started': TaskStatus.NOT_STARTED,
                'in_progress': TaskStatus.IN_PROGRESS,
                'completed': TaskStatus.COMPLETED,
            }

            sprint = Sprint(
                id=sprint_id,
                sprint_id=sprint_id,
                track_id=track_id,
                roadmap_id='main-roadmap',
                name=sprint_name,
                description=metadata['goal'],
                status=status_map.get(metadata['status'], TaskStatus.NOT_STARTED),
                blocked=False,
                created=datetime.now(timezone.utc),
                started=self._parse_datetime(metadata.get('started')),
                completed=self._parse_datetime(metadata.get('completed')),
                estimated_duration=metadata['duration'],
                priority=Priority.MEDIUM,
                tasks_total=len(tasks),
                tasks_completed=sum(1 for t in tasks if t['status'] == 'completed'),
                progress_percent=int((sum(1 for t in tasks if t['status'] == 'completed') / len(tasks) * 100) if tasks else 0),
                dependencies=[],
                blocks=[],
                blocked_by=[],
                depends_on=[],
                depended_on_by=[],
                metadata={
                    'migrated_from': str(state_file),
                    'migration_date': datetime.now(timezone.utc).isoformat(),
                }
            )

            # Save sprint
            sprint_yaml = sprint_dir / "sprint.yaml"
            save_sprint(sprint, sprint_yaml)
            print(f"   ✓ Created: {sprint_yaml}")

            # Create tasks
            for task_data in tasks:
                task_id = task_data['id']

                # Map complexity
                complexity_map = {
                    'simple': Complexity.SIMPLE,
                    'medium': Complexity.MEDIUM,
                    'complex': Complexity.COMPLEX,
                }

                task = Task(
                    id=task_id,
                    task_id=task_id,
                    sprint_id=sprint_id,
                    track_id=track_id,
                    roadmap_id='main-roadmap',
                    task_type='development',
                    title=task_data['title'],
                    description=task_data['description'],
                    status=status_map.get(task_data['status'], TaskStatus.NOT_STARTED),
                    blocked=False,
                    created=datetime.now(timezone.utc),
                    started=self._parse_datetime(task_data.get('started')),
                    completed=self._parse_datetime(task_data.get('completed')),
                    assigned_agent=task_data['assigned_agent'],
                    priority=Priority.MEDIUM,
                    complexity=complexity_map.get(task_data['complexity'], Complexity.MEDIUM),
                    estimated_tokens=task_data['estimated_tokens'],
                    actual_tokens=None,
                    dependencies=[],
                    blocks=[],
                    blocked_by=[],
                    depends_on=[],
                    depended_on_by=[],
                    deliverables=[],
                    commits=[],
                    metadata={
                        'phase_label': task_data.get('phase_label'),
                        'migrated_from': str(state_file),
                    }
                )

                # Create task directory
                task_dir = self.dir_manager.create_task_directory(
                    track_slug=track_id,
                    sprint_slug=sprint_id,
                    task_id=task_id,
                    task_slug=task_id,
                    create_context=True
                )

                task_yaml = task_dir / "task.yaml"
                # Use yaml.dump directly since save_task doesn't exist
                with open(task_yaml, 'w') as f:
                    task_dict = {
                        'task': {
                            'id': task.id,
                            'sprint_id': task.sprint_id,
                            'track_id': task.track_id,
                            'roadmap_id': task.roadmap_id,
                            'task_type': task.task_type,
                            'title': task.title,
                            'description': task.description,
                            'status': task.status.value if hasattr(task.status, 'value') else task.status,
                            'blocked': task.blocked,
                            'created': task.created.isoformat() if task.created else None,
                            'started': task.started.isoformat() if task.started else None,
                            'completed': task.completed.isoformat() if task.completed else None,
                            'assigned_agent': task.assigned_agent,
                            'priority': task.priority.value if hasattr(task.priority, 'value') else task.priority,
                            'phase_label': task.metadata.get('phase_label'),
                            'estimated_tokens': task.estimated_tokens,
                            'actual_tokens': task.actual_tokens,
                            'complexity': task.complexity.value if hasattr(task.complexity, 'value') else task.complexity,
                            'gate_info': None,
                            'audit_results': None,
                            'dependencies': task.dependencies,
                            'blocks': task.blocks,
                            'blocked_by': task.blocked_by,
                            'depends_on': task.depends_on,
                            'depended_on_by': task.depended_on_by,
                            'deliverables': task.deliverables,
                            'commits': task.commits,
                            'metadata': task.metadata,
                        }
                    }
                    yaml.dump(task_dict, f, default_flow_style=False, sort_keys=False)

            print(f"   ✓ Created {len(tasks)} tasks")

            self.sprints_migrated += 1
            self.tasks_migrated += len(tasks)

            return True, f"Migrated {sprint_name} with {len(tasks)} tasks"

        except Exception as e:
            error_msg = f"Error migrating {state_file.name}: {e}"
            self.errors.append(error_msg)
            return False, error_msg

    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string to datetime object."""
        if not dt_str:
            return None

        try:
            # Try ISO format
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except:
            try:
                # Try other formats
                return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
            except:
                return None

    def run(self, track_id: str = "main", dry_run: bool = True) -> bool:
        """
        Run migration.

        Args:
            track_id: Track ID to assign sprints to
            dry_run: If True, only show what would be done

        Returns:
            Success status
        """
        print("=" * 60)
        print("Legacy Sprint → Roadmap Migration")
        print("=" * 60)

        if dry_run:
            print("\n🔍 DRY RUN MODE - No files will be modified\n")

        # Find legacy sprints
        sprint_files = self.find_legacy_sprints()

        if not sprint_files:
            print("\n✓ No legacy sprint state files found")
            print(f"  Searched: {self.docs_sprints_dir}")
            return True

        print(f"\n📁 Found {len(sprint_files)} legacy sprint(s)")

        # Initialize roadmap if needed
        project_name = self.root_dir.name
        self.init_roadmap_if_needed(project_name, dry_run)

        # Migrate each sprint
        print(f"\n🔄 Migrating to track: {track_id}")

        for sprint_file in sprint_files:
            success, msg = self.migrate_sprint(sprint_file, track_id, dry_run)
            if not success:
                print(f"   ❌ {msg}")

        # Summary
        print("\n" + "=" * 60)
        print("Migration Summary")
        print("=" * 60)
        print(f"Sprints migrated: {self.sprints_migrated}/{len(sprint_files)}")
        print(f"Tasks migrated:   {self.tasks_migrated}")

        if self.errors:
            print(f"\n⚠️  Errors: {len(self.errors)}")
            for error in self.errors:
                print(f"   - {error}")

        if self.backup and not dry_run:
            print(f"\n💾 Backup created: {self.backup_dir}")

        if dry_run:
            print("\n✅ Dry run complete. Run with --execute to perform migration.")
        else:
            print("\n✅ Migration complete!")
            print("\nNext steps:")
            print("  1. Verify migrated data: ./framework/scripts/roadmap-cli.sh query --track", track_id)
            print("  2. Update CLAUDE.md sprint marker if needed")
            print("  3. Archive legacy files: mv docs/sprints/*.yaml docs/sprints/archived/")

        return len(self.errors) == 0


def main():
    parser = argparse.ArgumentParser(
        description='Migrate legacy sprint state files to roadmap system',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (show what would be done)
  python3 framework/scripts/migrate-to-roadmap.py

  # Migrate to 'main' track
  python3 framework/scripts/migrate-to-roadmap.py --execute

  # Migrate to specific track
  python3 framework/scripts/migrate-to-roadmap.py --execute --track backend

  # No backup
  python3 framework/scripts/migrate-to-roadmap.py --execute --no-backup
        """
    )

    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute migration (default is dry run)'
    )

    parser.add_argument(
        '--track',
        default='main',
        help='Track ID to assign sprints to (default: main)'
    )

    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip creating backup of legacy files'
    )

    parser.add_argument(
        '--root',
        type=Path,
        help='Project root directory (default: current directory)'
    )

    args = parser.parse_args()

    # Create migrator
    migrator = RoadmapMigrator(
        root_dir=args.root,
        backup=not args.no_backup
    )

    # Run migration
    success = migrator.run(
        track_id=args.track,
        dry_run=not args.execute
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
