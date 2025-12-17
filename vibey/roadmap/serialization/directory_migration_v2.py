"""
Directory structure migration for unified ticket architecture.

Migrates from hierarchical (nested) to flat (ULID-based) directory structure:

OLD (Hierarchical - v1):
    .vibey/roadmap/<track-slug>/<sprint-slug>/<task-slug>/task.yaml

NEW (Flat - v2):
    .vibey/roadmap/tracks/<track-ulid>.yaml
    .vibey/roadmap/sprints/<sprint-ulid>.yaml
    .vibey/roadmap/tasks/<task-ulid>.yaml
    .vibey/roadmap/context/tasks/<task-slug>/

This provides 98% reduction in directory count (1300+ → ~30) and 60% reduction in depth (10 → 4).

Task: unified-arch-1-task-002
"""

import logging
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

logger = logging.getLogger(__name__)


# ==============================================================================
# ULID Generation
# ==============================================================================

def generate_ulid() -> str:
    """
    Generate a ULID (Universally Unique Lexicographically Sortable Identifier).

    Returns:
        26-character ULID string
    """
    try:
        from ulid import ULID
        return str(ULID())
    except ImportError:
        # Fallback: use timestamp + random for basic sortable ID
        import secrets
        import time

        # ULID format: 10 char timestamp + 16 char random
        timestamp_ms = int(time.time() * 1000)
        timestamp_part = format(timestamp_ms, '048b')  # 48 bits
        random_part = format(int.from_bytes(secrets.token_bytes(10), 'big'), '080b')  # 80 bits

        # Convert to base32 (Crockford)
        ENCODING = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
        bits = timestamp_part + random_part
        ulid = ""
        for i in range(0, 128, 5):
            chunk = int(bits[i:i+5], 2)
            ulid += ENCODING[chunk]

        return ulid


def validate_ulid(ulid: str) -> bool:
    """
    Validate ULID format.

    Args:
        ulid: ULID string to validate

    Returns:
        True if valid ULID format
    """
    if len(ulid) != 26:
        return False

    # Check all characters are valid Crockford Base32
    VALID_CHARS = set("0123456789ABCDEFGHJKMNPQRSTVWXYZ")
    return all(c in VALID_CHARS for c in ulid.upper())


# ==============================================================================
# ID Mapping File
# ==============================================================================

class IdMappingFile:
    """Manages .id files for slug ↔ ULID bidirectional mapping."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.slug_to_ulid: Dict[str, str] = {}
        self.ulid_to_slug: Dict[str, str] = {}

        if file_path.exists():
            self.load()

    def load(self):
        """Load mappings from .id file."""
        with open(self.file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                if '=' in line:
                    slug, ulid = line.split('=', 1)
                    self.slug_to_ulid[slug] = ulid
                    self.ulid_to_slug[ulid] = slug

    def save(self):
        """Save mappings to .id file."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.file_path, 'w') as f:
            f.write("# Vibey Roadmap ID Mapping File\n")
            f.write("# Format: slug=ulid\n")
            f.write(f"# Generated: {datetime.now(timezone.utc).isoformat()}\n")
            f.write("\n")

            for slug in sorted(self.slug_to_ulid.keys()):
                f.write(f"{slug}={self.slug_to_ulid[slug]}\n")

    def register(self, slug: str, ulid: str):
        """Register a new slug ↔ ULID mapping."""
        self.slug_to_ulid[slug] = ulid
        self.ulid_to_slug[ulid] = slug

    def get_ulid(self, slug: str) -> Optional[str]:
        """Get ULID for a slug."""
        return self.slug_to_ulid.get(slug)

    def get_slug(self, ulid: str) -> Optional[str]:
        """Get slug for a ULID."""
        return self.ulid_to_slug.get(ulid)

    def rename_slug(self, old_slug: str, new_slug: str):
        """Rename a slug (ULID remains unchanged)."""
        if old_slug in self.slug_to_ulid:
            ulid = self.slug_to_ulid[old_slug]
            del self.slug_to_ulid[old_slug]
            self.slug_to_ulid[new_slug] = ulid
            self.ulid_to_slug[ulid] = new_slug


# ==============================================================================
# Entity Discovery
# ==============================================================================

@dataclass
class EntityInfo:
    """Information about a roadmap entity."""
    entity_type: str  # 'track', 'sprint', 'task'
    old_id: str  # Slug-based ID
    new_id: str  # ULID
    old_path: Path  # Old file path
    new_path: Path  # New file path
    context_path: Optional[Path] = None  # Context directory
    parent_id: Optional[str] = None  # Parent entity ID (for hierarchy)


def scan_hierarchical_structure(roadmap_dir: Path) -> Tuple[List[EntityInfo], List[EntityInfo], List[EntityInfo]]:
    """
    Scan hierarchical structure and prepare entity info for migration.

    Args:
        roadmap_dir: Path to .vibey/roadmap directory

    Returns:
        Tuple of (tracks, sprints, tasks) lists
    """
    tracks = []
    sprints = []
    tasks = []

    # Generate ULIDs for all tracks
    for track_dir in sorted(roadmap_dir.glob('*/')):
        if not track_dir.is_dir():
            continue

        track_file = track_dir / 'track.yaml'
        if not track_file.exists():
            continue

        track_slug = track_dir.name
        track_ulid = generate_ulid()

        entity = EntityInfo(
            entity_type='track',
            old_id=track_slug,
            new_id=track_ulid,
            old_path=track_file,
            new_path=roadmap_dir / 'tracks' / f'{track_ulid}.yaml',
            context_path=track_dir / 'context' if (track_dir / 'context').exists() else None,
        )
        tracks.append(entity)

        # Scan sprints within this track
        for sprint_dir in sorted(track_dir.glob('*/')):
            if not sprint_dir.is_dir():
                continue

            sprint_file = sprint_dir / 'sprint.yaml'
            if not sprint_file.exists():
                continue

            sprint_slug = sprint_dir.name
            sprint_ulid = generate_ulid()

            entity = EntityInfo(
                entity_type='sprint',
                old_id=sprint_slug,
                new_id=sprint_ulid,
                old_path=sprint_file,
                new_path=roadmap_dir / 'sprints' / f'{sprint_ulid}.yaml',
                context_path=sprint_dir / 'context' if (sprint_dir / 'context').exists() else None,
                parent_id=track_ulid,
            )
            sprints.append(entity)

            # Scan tasks within this sprint
            for task_dir in sorted(sprint_dir.glob('*/')):
                if not task_dir.is_dir():
                    continue

                task_file = task_dir / 'task.yaml'
                if not task_file.exists():
                    continue

                task_slug = task_dir.name
                task_ulid = generate_ulid()

                entity = EntityInfo(
                    entity_type='task',
                    old_id=task_slug,
                    new_id=task_ulid,
                    old_path=task_file,
                    new_path=roadmap_dir / 'tasks' / f'{task_ulid}.yaml',
                    context_path=task_dir / 'context' if (task_dir / 'context').exists() else None,
                    parent_id=sprint_ulid,
                )
                tasks.append(entity)

    return tracks, sprints, tasks


# ==============================================================================
# Migration Result
# ==============================================================================

@dataclass
class MigrationResult:
    """Result of directory structure migration."""

    tracks_migrated: int = 0
    sprints_migrated: int = 0
    tasks_migrated: int = 0
    context_dirs_migrated: int = 0
    files_moved: int = 0
    references_updated: int = 0

    errors: List[Tuple[str, str]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    backup_path: Optional[Path] = None

    @property
    def total_entities(self) -> int:
        return self.tracks_migrated + self.sprints_migrated + self.tasks_migrated

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    @property
    def success(self) -> bool:
        return not self.has_errors


# ==============================================================================
# Backup & Restore
# ==============================================================================

def create_backup(roadmap_dir: Path, backup_dir: Optional[Path] = None) -> Path:
    """
    Create a timestamped backup of the roadmap directory.

    Args:
        roadmap_dir: Path to .vibey/roadmap directory
        backup_dir: Optional backup directory (defaults to .vibey/backups)

    Returns:
        Path to created backup directory
    """
    if backup_dir is None:
        backup_dir = roadmap_dir.parent / 'backups'

    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    backup_name = f'roadmap-pre-migration-{timestamp}'
    backup_path = backup_dir / backup_name

    logger.info(f"Creating backup: {backup_path}")
    shutil.copytree(roadmap_dir, backup_path, ignore=shutil.ignore_patterns('*.db-shm', '*.db-wal'))

    # Also backup database if exists
    db_file = roadmap_dir.parent / 'roadmap.db'
    if db_file.exists():
        shutil.copy2(db_file, backup_dir / f'roadmap-pre-migration-{timestamp}.db')

    logger.info(f"Backup created: {backup_path}")
    return backup_path


def restore_from_backup(backup_path: Path, roadmap_dir: Path):
    """
    Restore roadmap from backup.

    Args:
        backup_path: Path to backup directory
        roadmap_dir: Target roadmap directory
    """
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup not found: {backup_path}")

    logger.info(f"Restoring from backup: {backup_path}")

    # Remove current roadmap
    if roadmap_dir.exists():
        shutil.rmtree(roadmap_dir)

    # Restore from backup
    shutil.copytree(backup_path, roadmap_dir)

    logger.info(f"Restored from backup: {backup_path}")


# ==============================================================================
# Migration Execution
# ==============================================================================

def migrate_to_flat_structure(
    roadmap_dir: Path,
    dry_run: bool = True,
    backup: bool = True,
    use_git_mv: bool = True,
    verbose: bool = False,
) -> MigrationResult:
    """
    Migrate from hierarchical to flat ULID-based directory structure.

    Args:
        roadmap_dir: Path to .vibey/roadmap directory
        dry_run: If True, only simulate migration (no changes)
        backup: If True, create backup before migration
        use_git_mv: If True, use 'git mv' to preserve history
        verbose: If True, log detailed progress

    Returns:
        MigrationResult with migration details
    """
    result = MigrationResult()

    logger.info(f"Starting migration (dry_run={dry_run})")

    # Step 1: Create backup
    if backup and not dry_run:
        try:
            result.backup_path = create_backup(roadmap_dir)
        except Exception as e:
            result.errors.append(('backup', f"Failed to create backup: {e}"))
            return result

    # Step 2: Scan current structure
    logger.info("Scanning hierarchical structure...")
    try:
        tracks, sprints, tasks = scan_hierarchical_structure(roadmap_dir)
    except Exception as e:
        result.errors.append(('scan', f"Failed to scan structure: {e}"))
        return result

    logger.info(f"Found {len(tracks)} tracks, {len(sprints)} sprints, {len(tasks)} tasks")

    # Step 3: Create ID mapping files
    track_mapping = IdMappingFile(roadmap_dir / 'tracks' / '.id')
    sprint_mapping = IdMappingFile(roadmap_dir / 'sprints' / '.id')
    task_mapping = IdMappingFile(roadmap_dir / 'tasks' / '.id')

    for track in tracks:
        track_mapping.register(track.old_id, track.new_id)
    for sprint in sprints:
        sprint_mapping.register(sprint.old_id, sprint.new_id)
    for task in tasks:
        task_mapping.register(task.old_id, task.new_id)

    if not dry_run:
        track_mapping.save()
        sprint_mapping.save()
        task_mapping.save()
        logger.info("Created .id mapping files")

    # Step 4: Create new directory structure
    if not dry_run:
        (roadmap_dir / 'tracks').mkdir(exist_ok=True)
        (roadmap_dir / 'sprints').mkdir(exist_ok=True)
        (roadmap_dir / 'tasks').mkdir(exist_ok=True)
        (roadmap_dir / 'context' / 'tracks').mkdir(parents=True, exist_ok=True)
        (roadmap_dir / 'context' / 'sprints').mkdir(parents=True, exist_ok=True)
        (roadmap_dir / 'context' / 'tasks').mkdir(parents=True, exist_ok=True)
        logger.info("Created flat directory structure")

    # Step 5: Move tracks
    logger.info("Migrating tracks...")
    for track in tracks:
        try:
            _migrate_entity(track, roadmap_dir, use_git_mv, dry_run, verbose)
            result.tracks_migrated += 1
            result.files_moved += 1

            if track.context_path:
                result.context_dirs_migrated += 1
        except Exception as e:
            result.errors.append((f"track:{track.old_id}", str(e)))

    # Step 6: Move sprints
    logger.info("Migrating sprints...")
    for sprint in sprints:
        try:
            _migrate_entity(sprint, roadmap_dir, use_git_mv, dry_run, verbose)
            result.sprints_migrated += 1
            result.files_moved += 1

            if sprint.context_path:
                result.context_dirs_migrated += 1
        except Exception as e:
            result.errors.append((f"sprint:{sprint.old_id}", str(e)))

    # Step 7: Move tasks
    logger.info("Migrating tasks...")
    for task in tasks:
        try:
            _migrate_entity(task, roadmap_dir, use_git_mv, dry_run, verbose)
            result.tasks_migrated += 1
            result.files_moved += 1

            if task.context_path:
                result.context_dirs_migrated += 1
        except Exception as e:
            result.errors.append((f"task:{task.old_id}", str(e)))

    # Step 8: Update YAML references
    if not dry_run:
        logger.info("Updating YAML references...")
        try:
            refs_updated = update_yaml_references(
                roadmap_dir,
                track_mapping,
                sprint_mapping,
                task_mapping
            )
            result.references_updated = refs_updated
        except Exception as e:
            result.errors.append(('references', f"Failed to update references: {e}"))

    logger.info(f"Migration complete (entities: {result.total_entities}, files: {result.files_moved})")
    return result


def _migrate_entity(
    entity: EntityInfo,
    roadmap_dir: Path,
    use_git_mv: bool,
    dry_run: bool,
    verbose: bool
):
    """Migrate a single entity (track, sprint, or task)."""
    if verbose:
        logger.info(f"Migrating {entity.entity_type}: {entity.old_id} → {entity.new_id}")

    if dry_run:
        return

    # Move main YAML file
    if use_git_mv:
        subprocess.run(
            ['git', 'mv', str(entity.old_path), str(entity.new_path)],
            cwd=roadmap_dir,
            check=True,
            capture_output=True
        )
    else:
        shutil.copy2(entity.old_path, entity.new_path)

    # Move context directory (use slug-based path for readability)
    if entity.context_path and entity.context_path.exists():
        new_context_path = roadmap_dir / 'context' / f'{entity.entity_type}s' / entity.old_id

        if use_git_mv:
            # Git mv doesn't work well with directories, use cp + rm
            shutil.copytree(entity.context_path, new_context_path, dirs_exist_ok=True)
            # Add to git
            subprocess.run(
                ['git', 'add', str(new_context_path)],
                cwd=roadmap_dir,
                check=True,
                capture_output=True
            )
        else:
            shutil.copytree(entity.context_path, new_context_path, dirs_exist_ok=True)


def update_yaml_references(
    roadmap_dir: Path,
    track_mapping: IdMappingFile,
    sprint_mapping: IdMappingFile,
    task_mapping: IdMappingFile
) -> int:
    """
    Update all YAML files to use ULID references.

    Updates:
    - id field: slug → ULID
    - parent_ref field: slug → ULID
    - Add slug field for human readability

    Returns:
        Number of references updated
    """
    refs_updated = 0

    # Update tracks
    for track_file in (roadmap_dir / 'tracks').glob('*.yaml'):
        with open(track_file, 'r') as f:
            data = yaml.safe_load(f)

        if 'track' in data:
            track = data['track']
            old_id = track.get('id', '')

            # Get ULID from mapping (reverse lookup by filename)
            ulid = track_file.stem
            slug = track_mapping.get_slug(ulid)

            if slug:
                track['id'] = ulid
                track['slug'] = slug
                refs_updated += 1

        with open(track_file, 'w') as f:
            yaml.dump(data, f, sort_keys=False, allow_unicode=True)

    # Update sprints
    for sprint_file in (roadmap_dir / 'sprints').glob('*.yaml'):
        with open(sprint_file, 'r') as f:
            data = yaml.safe_load(f)

        if 'sprint' in data:
            sprint = data['sprint']

            # Update ID
            ulid = sprint_file.stem
            slug = sprint_mapping.get_slug(ulid)

            if slug:
                sprint['id'] = ulid
                sprint['slug'] = slug
                refs_updated += 1

            # Update parent_ref (track_id → track ULID)
            if 'track_id' in sprint:
                track_slug = sprint['track_id']
                track_ulid = track_mapping.get_ulid(track_slug)
                if track_ulid:
                    sprint['parent_ref'] = track_ulid
                    refs_updated += 1

        with open(sprint_file, 'w') as f:
            yaml.dump(data, f, sort_keys=False, allow_unicode=True)

    # Update tasks
    for task_file in (roadmap_dir / 'tasks').glob('*.yaml'):
        with open(task_file, 'r') as f:
            data = yaml.safe_load(f)

        if 'task' in data:
            task = data['task']

            # Update ID
            ulid = task_file.stem
            slug = task_mapping.get_slug(ulid)

            if slug:
                task['id'] = ulid
                task['slug'] = slug
                refs_updated += 1

            # Update parent_ref (sprint_id → sprint ULID)
            if 'sprint_id' in task:
                sprint_slug = task['sprint_id']
                sprint_ulid = sprint_mapping.get_ulid(sprint_slug)
                if sprint_ulid:
                    task['parent_ref'] = sprint_ulid
                    refs_updated += 1

        with open(task_file, 'w') as f:
            yaml.dump(data, f, sort_keys=False, allow_unicode=True)

    return refs_updated


# ==============================================================================
# Validation
# ==============================================================================

def validate_migration(roadmap_dir: Path) -> Tuple[bool, List[str]]:
    """
    Validate flat directory structure after migration.

    Args:
        roadmap_dir: Path to .vibey/roadmap directory

    Returns:
        Tuple of (valid, errors)
    """
    errors = []

    # Check directories exist
    required_dirs = [
        'tracks',
        'sprints',
        'tasks',
        'context/tracks',
        'context/sprints',
        'context/tasks',
    ]

    for dir_name in required_dirs:
        dir_path = roadmap_dir / dir_name
        if not dir_path.exists():
            errors.append(f"Missing directory: {dir_name}")

    # Check .id files exist
    for entity_type in ['tracks', 'sprints', 'tasks']:
        id_file = roadmap_dir / entity_type / '.id'
        if not id_file.exists():
            errors.append(f"Missing .id file: {entity_type}/.id")

    # Validate YAML files have ULIDs
    for entity_type in ['tracks', 'sprints', 'tasks']:
        entity_dir = roadmap_dir / entity_type
        if not entity_dir.exists():
            continue

        for yaml_file in entity_dir.glob('*.yaml'):
            if not yaml_file.stem or yaml_file.name == '.id':
                continue

            # Check filename is valid ULID
            if not validate_ulid(yaml_file.stem):
                errors.append(f"Invalid ULID filename: {yaml_file.name}")

            # Check YAML content
            try:
                with open(yaml_file, 'r') as f:
                    data = yaml.safe_load(f)

                entity_key = entity_type.rstrip('s')  # tracks → track
                if entity_key not in data:
                    errors.append(f"Missing '{entity_key}' key in {yaml_file.name}")
                    continue

                entity = data[entity_key]

                # Check has id field
                if 'id' not in entity:
                    errors.append(f"Missing 'id' field in {yaml_file.name}")
                elif not validate_ulid(entity['id']):
                    errors.append(f"Invalid ULID in 'id' field: {yaml_file.name}")

                # Check has slug field
                if 'slug' not in entity:
                    errors.append(f"Missing 'slug' field in {yaml_file.name}")

            except Exception as e:
                errors.append(f"Failed to validate {yaml_file.name}: {e}")

    return len(errors) == 0, errors


# ==============================================================================
# CLI Formatting
# ==============================================================================

def format_migration_result(result: MigrationResult) -> str:
    """Format migration result for CLI output."""
    lines = []

    lines.append("\n" + "=" * 70)
    lines.append("Directory Migration Summary")
    lines.append("=" * 70)

    lines.append(f"\nEntities Migrated:")
    lines.append(f"  Tracks:              {result.tracks_migrated}")
    lines.append(f"  Sprints:             {result.sprints_migrated}")
    lines.append(f"  Tasks:               {result.tasks_migrated}")
    lines.append(f"  Total:               {result.total_entities}")

    lines.append(f"\nFiles & Directories:")
    lines.append(f"  Files moved:         {result.files_moved}")
    lines.append(f"  Context dirs moved:  {result.context_dirs_migrated}")
    lines.append(f"  References updated:  {result.references_updated}")

    if result.backup_path:
        lines.append(f"\nBackup:")
        lines.append(f"  Location: {result.backup_path}")

    if result.warnings:
        lines.append(f"\nWarnings ({len(result.warnings)}):")
        for warning in result.warnings:
            lines.append(f"  ⚠️  {warning}")

    if result.errors:
        lines.append(f"\n❌ Errors ({len(result.errors)}):")
        for entity, error in result.errors:
            lines.append(f"  {entity}: {error}")
    else:
        lines.append(f"\n✅ Migration completed successfully!")

    lines.append("=" * 70)

    return '\n'.join(lines)
