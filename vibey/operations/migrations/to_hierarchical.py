"""
Migrate Flat Structure to Hierarchical Structure

Migrates roadmap data from flat structure:
  .vibey/tracks/*.yaml
  .vibey/sprints/*.yaml
  .vibey/tasks/*.yaml

To hierarchical structure:
  .vibey/roadmap/{track-slug}/track.yaml
  .vibey/roadmap/{track-slug}/{sprint-slug}/sprint.yaml
  .vibey/roadmap/{track-slug}/{sprint-slug}/{task-slug}/task.yaml
"""

import yaml
import shutil
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

from vibey.roadmap.directory_manager import DirectoryManager


class HierarchicalMigrator:
    """Migrates from flat to hierarchical structure."""

    def __init__(self, root_dir: Optional[Path] = None, backup: bool = True):
        """
        Initialize migrator.

        Args:
            root_dir: Project root directory
            backup: Whether to create backups
        """
        self.root_dir = root_dir or Path.cwd()
        self.vibey_dir = self.root_dir / ".vibey"

        # Old structure
        self.tracks_dir = self.vibey_dir / "tracks"
        self.sprints_dir = self.vibey_dir / "sprints"
        self.tasks_dir = self.vibey_dir / "tasks"

        # New structure
        self.dir_manager = DirectoryManager(str(self.vibey_dir / "roadmap"))

        # Backup
        self.backup = backup
        if backup:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.backup_dir = self.vibey_dir / "hierarchical-migration-backups" / f"backup_{timestamp}"

        # Stats
        self.tracks_migrated = 0
        self.sprints_migrated = 0
        self.tasks_migrated = 0
        self.errors: List[str] = []

    def create_slug(self, name: str) -> str:
        """
        Create a slug from a name.

        Args:
            name: Object name

        Returns:
            URL-friendly slug
        """
        slug = name.lower()
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        slug = slug.strip('-')
        return slug[:100]  # Max length

    def load_yaml(self, file_path: Path) -> Dict:
        """Load YAML file."""
        with open(file_path) as f:
            return yaml.safe_load(f)

    def save_yaml(self, data: Dict, file_path: Path) -> None:
        """Save YAML file."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    def migrate_track(self, track_file: Path, dry_run: bool = True) -> Tuple[bool, str]:
        """
        Migrate a single track.

        Args:
            track_file: Path to track YAML file
            dry_run: Whether to simulate only

        Returns:
            (success, track_slug)
        """
        try:
            # Load track
            data = self.load_yaml(track_file)
            track = data['track']
            track_id = track['id']

            # Create slug from track ID (already has good format)
            track_slug = track_id

            print(f"  Migrating track: {track_id} → {track_slug}/")

            if not dry_run:
                # Create track directory
                track_dir = self.dir_manager.create_track_directory(
                    track_id=track_id,
                    slug=track_slug,
                    create_context=True
                )

                # Save track.yaml
                track_yaml = track_dir / "track.yaml"
                self.save_yaml(data, track_yaml)

                print(f"    ✓ Created {track_yaml}")

            self.tracks_migrated += 1
            return True, track_slug

        except Exception as e:
            error = f"Failed to migrate track {track_file.name}: {e}"
            self.errors.append(error)
            print(f"    ✗ {error}")
            return False, ""

    def migrate_sprint(self, sprint_file: Path, track_slug: str, dry_run: bool = True) -> Tuple[bool, str]:
        """
        Migrate a single sprint.

        Args:
            sprint_file: Path to sprint YAML file
            track_slug: Parent track slug
            dry_run: Whether to simulate only

        Returns:
            (success, sprint_slug)
        """
        try:
            # Load sprint
            data = self.load_yaml(sprint_file)
            sprint = data['sprint']
            sprint_id = sprint['id']

            # Create slug from sprint ID
            sprint_slug = sprint_id

            print(f"    Migrating sprint: {sprint_id} → {track_slug}/{sprint_slug}/")

            if not dry_run:
                # Create sprint directory
                sprint_dir = self.dir_manager.create_sprint_directory(
                    track_slug=track_slug,
                    sprint_id=sprint_id,
                    sprint_slug=sprint_slug,
                    create_context=True
                )

                # Save sprint.yaml
                sprint_yaml = sprint_dir / "sprint.yaml"
                self.save_yaml(data, sprint_yaml)

                print(f"      ✓ Created {sprint_yaml}")

            self.sprints_migrated += 1
            return True, sprint_slug

        except Exception as e:
            error = f"Failed to migrate sprint {sprint_file.name}: {e}"
            self.errors.append(error)
            print(f"      ✗ {error}")
            return False, ""

    def migrate_tasks(self, tasks_file: Path, track_slug: str, sprint_slug: str, dry_run: bool = True) -> bool:
        """
        Migrate tasks for a sprint.

        Args:
            tasks_file: Path to tasks YAML file
            track_slug: Parent track slug
            sprint_slug: Parent sprint slug
            dry_run: Whether to simulate only

        Returns:
            Success status
        """
        try:
            # Load tasks
            data = self.load_yaml(tasks_file)
            tasks = data['tasks']

            print(f"      Migrating {len(tasks)} tasks...")

            for task in tasks:
                task_id = task['id']

                # Create slug from task ID
                task_slug = task_id

                if not dry_run:
                    # Create task directory
                    task_dir = self.dir_manager.create_task_directory(
                        track_slug=track_slug,
                        sprint_slug=sprint_slug,
                        task_id=task_id,
                        task_slug=task_slug,
                        create_context=True
                    )

                    # Save task.yaml (single task per file)
                    task_yaml = task_dir / "task.yaml"
                    task_data = {'task': task}
                    self.save_yaml(task_data, task_yaml)

                self.tasks_migrated += 1

            print(f"        ✓ Migrated {len(tasks)} tasks")
            return True

        except Exception as e:
            error = f"Failed to migrate tasks {tasks_file.name}: {e}"
            self.errors.append(error)
            print(f"        ✗ {error}")
            return False

    def create_backups(self, dry_run: bool = True) -> bool:
        """Create backups of flat structure."""
        if not self.backup or dry_run:
            return True

        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)

            # Backup tracks
            if self.tracks_dir.exists():
                shutil.copytree(self.tracks_dir, self.backup_dir / "tracks")

            # Backup sprints
            if self.sprints_dir.exists():
                shutil.copytree(self.sprints_dir, self.backup_dir / "sprints")

            # Backup tasks
            if self.tasks_dir.exists():
                shutil.copytree(self.tasks_dir, self.backup_dir / "tasks")

            print(f"✓ Backups created at: {self.backup_dir}")
            return True

        except Exception as e:
            print(f"✗ Backup failed: {e}")
            return False

    def run(self, dry_run: bool = True) -> bool:
        """
        Run migration.

        Args:
            dry_run: Whether to simulate only

        Returns:
            Success status
        """
        print("=" * 70)
        print("🔄 Hierarchical Structure Migration")
        print("=" * 70)
        print()

        if dry_run:
            print("📋 DRY RUN MODE - No changes will be made")
        else:
            print("⚠️  EXECUTION MODE - Migrating to hierarchical structure")
        print()

        # Create backups
        if not dry_run:
            print("💾 Creating backups...")
            if not self.create_backups(dry_run):
                return False
            print()

        # Create roadmap root
        if not dry_run:
            self.dir_manager.create_roadmap_root()

        # Load all tracks and build migration map
        track_map: Dict[str, str] = {}  # track_id -> track_slug
        sprint_map: Dict[str, Tuple[str, str]] = {}  # sprint_id -> (track_slug, sprint_slug)

        print("📊 Scanning existing structure...")
        tracks = sorted(self.tracks_dir.glob("*.yaml")) if self.tracks_dir.exists() else []
        sprints = sorted(self.sprints_dir.glob("*.yaml")) if self.sprints_dir.exists() else []
        tasks = sorted(self.tasks_dir.glob("*-tasks.yaml")) if self.tasks_dir.exists() else []

        print(f"  Tracks: {len(tracks)}")
        print(f"  Sprints: {len(sprints)}")
        print(f"  Task files: {len(tasks)}")
        print()

        # Migrate tracks
        print("🔄 Migrating tracks...")
        for track_file in tracks:
            success, track_slug = self.migrate_track(track_file, dry_run)
            if success:
                track_id = track_file.stem
                track_map[track_id] = track_slug
        print()

        # Migrate sprints
        print("🔄 Migrating sprints...")
        for sprint_file in sprints:
            # Load to get track_id
            data = self.load_yaml(sprint_file)
            sprint = data['sprint']
            track_id = sprint['track_id']

            if track_id in track_map:
                track_slug = track_map[track_id]
                success, sprint_slug = self.migrate_sprint(sprint_file, track_slug, dry_run)
                if success:
                    sprint_map[sprint['id']] = (track_slug, sprint_slug)
            else:
                print(f"    ✗ Track not found for sprint: {sprint_file.name}")
        print()

        # Migrate tasks
        print("🔄 Migrating tasks...")
        for tasks_file in tasks:
            # Extract sprint_id from filename (sprint-id-tasks.yaml)
            sprint_id = tasks_file.stem.replace('-tasks', '')

            if sprint_id in sprint_map:
                track_slug, sprint_slug = sprint_map[sprint_id]
                self.migrate_tasks(tasks_file, track_slug, sprint_slug, dry_run)
            else:
                print(f"      ✗ Sprint not found for tasks: {tasks_file.name}")
        print()

        # Summary
        print("=" * 70)
        print("📊 Migration Summary")
        print("=" * 70)
        print(f"  Tracks migrated: {self.tracks_migrated}/{len(tracks)}")
        print(f"  Sprints migrated: {self.sprints_migrated}/{len(sprints)}")
        print(f"  Tasks migrated: {self.tasks_migrated}")

        if self.errors:
            print(f"\n⚠️  Errors: {len(self.errors)}")
            for error in self.errors[:10]:  # Show first 10
                print(f"  - {error}")

        if not dry_run and self.backup:
            print(f"\n💾 Backups: {self.backup_dir}")

        if dry_run:
            print(f"\n💡 To execute migration, run with --execute flag")
        else:
            if len(self.errors) == 0:
                print(f"\n✅ Migration completed successfully!")
            else:
                print(f"\n⚠️  Migration completed with errors")

        print("=" * 70)

        return len(self.errors) == 0


def migrate_to_hierarchical(
    root_dir: Optional[Path] = None,
    dry_run: bool = True,
    backup: bool = True
) -> int:
    """
    Migrate from flat to hierarchical structure.

    Args:
        root_dir: Project root directory (defaults to current directory)
        dry_run: If True, only show what would be done (defaults to True)
        backup: Whether to create backups (defaults to True)

    Returns:
        Exit code (0 = success, non-zero = error)
    """
    migrator = HierarchicalMigrator(root_dir=root_dir, backup=backup)
    success = migrator.run(dry_run=dry_run)
    return 0 if success else 1
