"""
Migration commands.

Provides migration functionality for roadmap files, formats, and documentation.
"""

from pathlib import Path
from typing import Optional


def migrate_to_roadmap_cmd() -> int:
    """Migrate legacy sprint files to roadmap."""
    from vibey.operations.roadmap.migrations import migrate_to_roadmap

    return migrate_to_roadmap(
        root_dir=Path.cwd() / ".vibey",  # Migration expects .vibey/ path
        dry_run=False,
        backup=True
    )


def migrate_embedded_tasks_cmd() -> int:
    """Migrate embedded tasks to separate files."""
    from vibey.operations.roadmap.migrations import migrate_embedded_tasks

    return migrate_embedded_tasks(
        root_dir=Path.cwd() / ".vibey",  # Migration expects .vibey/ path
        dry_run=False
    )


def extract_embedded_cmd(dry_run: bool = True, verbose: bool = True) -> int:
    """Extract embedded tasks from sprint files to standalone task files.

    Scans all sprint YAML files for embedded tasks[] arrays and creates
    individual task files in the flat .vibey/roadmap/tasks/ directory.

    Args:
        dry_run: If True, only show what would be extracted without creating files
        verbose: If True, print detailed output

    Returns:
        0 if successful, 1 if errors occurred
    """
    from vibey.operations.migrations.extract_embedded_tasks import (
        extract_embedded_tasks,
    )

    root_dir = Path.cwd()
    roadmap_dir = root_dir / ".vibey" / "roadmap"

    if not roadmap_dir.exists():
        print("❌ Roadmap directory not found")
        print("   Run 'vibey roadmap init' first")
        return 1

    stats = extract_embedded_tasks(
        roadmap_dir=roadmap_dir,
        dry_run=dry_run,
        verbose=verbose,
    )

    if stats.get("errors"):
        return 1

    return 0


def migrate_format_cmd(
    dry_run: bool = False,
    backup: bool = True,
    path: Optional[str] = None,
    force: bool = False,
    verbose: bool = False,
) -> int:
    """
    Migrate YAML files from v1 format to v2 format.

    V1 format uses legacy field names:
    - created, started, completed → created_at, started_at, completed_at
    - assigned_agent (singular) → assigned_agents (list)
    - title → name
    - sprint_id/track_id/roadmap_id → parent_ref
    - blocked_by (list of IDs) → criteria with CompletableTarget

    V2 format uses:
    - format_version: 'v2'
    - ticket_type field
    - parent_ref for hierarchy
    - criteria for unified blocking
    - _at suffix on timestamps
    """
    import shutil
    from datetime import datetime

    import yaml

    # Import format detection from yaml_loader
    from vibey.roadmap.serialization.yaml_loader import detect_yaml_format

    root_dir = Path.cwd()
    roadmap_dir = Path(path) if path else root_dir / ".vibey" / "roadmap"

    if not roadmap_dir.exists():
        print(f"❌ Roadmap directory not found: {roadmap_dir}")
        return 1

    print("🔄 Scanning YAML files for format migration...")
    print(f"   Directory: {roadmap_dir}")
    print()

    # Find all YAML files
    yaml_files = list(roadmap_dir.glob("**/*.yaml"))
    yaml_files = [f for f in yaml_files if f.name not in ('.sync-manifest.yaml',)]

    # Categorize files by format
    v1_files = []
    v2_files = []
    error_files = []

    for yaml_file in yaml_files:
        try:
            with open(yaml_file, 'r') as f:
                data = yaml.safe_load(f)

            if data is None:
                continue

            # Get the root key (task, sprint, track, roadmap)
            root_keys = ['task', 'sprint', 'track', 'roadmap']
            entity_data = None
            entity_type = None
            for key in root_keys:
                if key in data:
                    entity_data = data[key]
                    entity_type = key
                    break

            if entity_data is None:
                continue

            # Detect format
            format_version = detect_yaml_format(entity_data)

            if format_version == 'v1':
                v1_files.append((yaml_file, entity_type, entity_data))
            else:
                v2_files.append(yaml_file)

        except Exception as e:
            error_files.append((yaml_file, str(e)))

    # Report discovery results
    print("📊 Discovery Results:")
    print(f"   Files scanned:  {len(yaml_files)}")
    print(f"   V1 format:      {len(v1_files)} (need migration)")
    print(f"   V2 format:      {len(v2_files)} (already migrated)")
    print(f"   Parse errors:   {len(error_files)}")
    print()

    if error_files and verbose:
        print("⚠️  Files with parse errors:")
        for file_path, error in error_files[:5]:
            print(f"   {file_path.relative_to(roadmap_dir)}: {error[:50]}")
        if len(error_files) > 5:
            print(f"   ... and {len(error_files) - 5} more")
        print()

    if not v1_files:
        print("✅ All files already in v2 format. Nothing to migrate.")
        return 0

    # Show what will change
    if dry_run or verbose:
        print("📝 Migration Preview:")
        print("-" * 60)
        for yaml_file, entity_type, entity_data in v1_files[:10]:
            rel_path = yaml_file.relative_to(roadmap_dir)
            changes = _count_field_changes(entity_type, entity_data)
            print(f"   {rel_path}: {changes} field changes")
        if len(v1_files) > 10:
            print(f"   ... and {len(v1_files) - 10} more files")
        print()

    if dry_run:
        print("🔍 Dry run complete. No files were modified.")
        print("   Use 'vibey roadmap migrate-format' to apply changes.")
        return 0

    # Confirm if not forced
    if not force:
        print(f"⚠️  This will modify {len(v1_files)} files.")
        if backup:
            print("   Backups will be created (.v1.bak extension)")
        response = input("   Continue? [y/N]: ").strip().lower()
        if response not in ('y', 'yes'):
            print("   Aborted.")
            return 1

    # Perform migration
    print()
    print("🔄 Migrating files...")

    migrated = 0
    failed = 0
    backup_dir = roadmap_dir / ".migration-backups" / datetime.now().strftime("%Y%m%d_%H%M%S")

    for i, (yaml_file, entity_type, entity_data) in enumerate(v1_files):
        rel_path = yaml_file.relative_to(roadmap_dir)

        try:
            # Create backup
            if backup:
                backup_path = backup_dir / rel_path.with_suffix('.yaml.v1.bak')
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(yaml_file, backup_path)

            # Transform v1 to v2
            migrated_data = _migrate_entity_to_v2(entity_type, entity_data)

            # Write back
            with open(yaml_file, 'w') as f:
                yaml.dump({entity_type: migrated_data}, f,
                         default_flow_style=False,
                         allow_unicode=True,
                         sort_keys=False)

            migrated += 1
            if verbose:
                print(f"   [{migrated}/{len(v1_files)}] ✅ {rel_path}")
            else:
                # Progress indicator every 10 files
                if (i + 1) % 10 == 0:
                    print(f"   [{i + 1}/{len(v1_files)}] files processed...")

        except Exception as e:
            failed += 1
            print(f"   ❌ {rel_path}: {e}")

    print()
    print("=" * 60)
    print("📊 Migration Summary:")
    print(f"   Migrated:  {migrated} files")
    print(f"   Failed:    {failed} files")
    if backup:
        print(f"   Backups:   {backup_dir}")
    print()

    # Validate migrated files
    print("🔍 Validating migrated files...")
    validation_errors = 0

    for yaml_file, _, _ in v1_files[:migrated]:
        try:
            with open(yaml_file, 'r') as f:
                data = yaml.safe_load(f)

            # Get entity data
            for key in ['task', 'sprint', 'track', 'roadmap']:
                if key in data:
                    entity_data = data[key]
                    break

            # Verify it's now v2
            if detect_yaml_format(entity_data) != 'v2':
                validation_errors += 1
                print(f"   ⚠️  {yaml_file.relative_to(roadmap_dir)}: Still shows as v1")

        except Exception as e:
            validation_errors += 1
            print(f"   ❌ {yaml_file.relative_to(roadmap_dir)}: {e}")

    if validation_errors == 0:
        print("   ✅ All migrated files validate as v2 format")
    else:
        print(f"   ⚠️  {validation_errors} files failed validation")

    print()
    if failed == 0 and validation_errors == 0:
        print("✅ Migration complete!")
        return 0
    else:
        print("⚠️  Migration completed with errors")
        return 1


def _count_field_changes(entity_type: str, data: dict) -> int:
    """Count how many fields will change during migration."""
    changes = 0

    # Timestamp renames
    for old in ['created', 'started', 'completed']:
        if old in data:
            changes += 1

    # assigned_agent → assigned_agents
    if 'assigned_agent' in data:
        changes += 1

    # title → name (for tasks)
    if 'title' in data and entity_type == 'task':
        changes += 1

    # Hierarchy fields → parent_ref
    if any(k in data for k in ['sprint_id', 'track_id', 'roadmap_id']):
        changes += 1

    # blocked_by → criteria
    if 'blocked_by' in data and data['blocked_by']:
        changes += 1

    # Add format_version and ticket_type
    if 'format_version' not in data:
        changes += 1
    if 'ticket_type' not in data:
        changes += 1

    return changes


def _migrate_entity_to_v2(entity_type: str, data: dict) -> dict:
    """
    Transform a v1 entity dict to v2 format.

    This performs in-place field migrations:
    - Timestamp renames (created → created_at, etc.)
    - Field renames (title → name, assigned_agent → assigned_agents)
    - Hierarchy consolidation (sprint_id/track_id → parent_ref)
    - blocked_by → criteria conversion
    - Add format markers
    """
    result = dict(data)  # Copy to avoid modifying original

    # Add format markers
    result['format_version'] = 'v2'
    result['ticket_type'] = entity_type

    # Rename timestamps
    timestamp_renames = [
        ('created', 'created_at'),
        ('started', 'started_at'),
        ('completed', 'completed_at'),
    ]
    for old, new in timestamp_renames:
        if old in result:
            result[new] = result.pop(old)

    # Convert assigned_agent (singular) to assigned_agents (list)
    if 'assigned_agent' in result:
        agent = result.pop('assigned_agent')
        if agent:
            result['assigned_agents'] = [agent] if isinstance(agent, str) else agent
        else:
            result['assigned_agents'] = []

    # Convert title to name (for tasks)
    if 'title' in result and entity_type == 'task':
        result['name'] = result.pop('title')

    # Consolidate hierarchy fields to parent_ref
    hierarchy_fields = {
        'task': 'sprint_id',
        'sprint': 'track_id',
        'track': 'roadmap_id',
    }
    if entity_type in hierarchy_fields:
        parent_field = hierarchy_fields[entity_type]
        if parent_field in result:
            result['parent_ref'] = result.pop(parent_field)
            # Also remove the other hierarchy fields that are redundant
            for field in ['sprint_id', 'track_id', 'roadmap_id']:
                if field != parent_field and field in result:
                    del result[field]

    # Convert blocked_by to criteria
    if 'blocked_by' in result and result['blocked_by']:
        blocked_by = result.pop('blocked_by')
        if 'criteria' not in result:
            result['criteria'] = []

        for i, blocker_id in enumerate(blocked_by):
            if isinstance(blocker_id, str):
                criterion = {
                    'id': f"dep-{i+1}",
                    'description': f"Depends on {blocker_id}",
                    'target': {
                        'type': 'completable',
                        'target_id': blocker_id,
                    },
                    'blocks_transition_to': 'in_progress',
                    'required': True,
                }
                result['criteria'].append(criterion)
    else:
        # Remove empty blocked_by
        if 'blocked_by' in result:
            del result['blocked_by']

    # Remove deprecated fields
    deprecated_fields = ['blocked', 'dependencies', 'blocks', 'depended_on_by']
    for field in deprecated_fields:
        if field in result and not result[field]:
            del result[field]

    # Ensure criteria exists
    if 'criteria' not in result:
        result['criteria'] = []

    # Rename commits to commits_local for serialization clarity
    # (keeping internal field as 'commits' but marking for v2 output)
    if 'commits' in result:
        result['commits_local'] = result.pop('commits')

    # Same for deliverables → requirements_local
    if 'deliverables' in result:
        deliverables = result.pop('deliverables')
        if deliverables and 'requirements_local' not in result:
            result['requirements_local'] = [
                {'id': f'deliverable-{i+1}', 'description': d}
                for i, d in enumerate(deliverables)
                if isinstance(d, str)
            ]

    return result


def migrate_docs_cmd(
    dry_run: bool = False,
    path: Optional[str] = None,
    verbose: bool = False,
) -> int:
    """
    Migrate documentation fields from YAML to markdown files.

    Migrates:
    - version_strategy → VERSIONING_POLICY.md (in roadmap dir)
    - version_history → CHANGELOG.md (in repo root)
    - metadata.notes → NOTES.md (per entity directory)

    Benefits of markdown:
    - Rich formatting (headings, tables, code blocks)
    - Git-diffable content
    - Searchable with grep/ripgrep
    - Human readable without tooling
    """
    from vibey.roadmap.serialization.markdown_migration import (
        migrate_roadmap_docs,
        format_migration_report,
    )

    root_dir = Path.cwd()
    roadmap_dir = Path(path) if path else root_dir / ".vibey" / "roadmap"

    if not roadmap_dir.exists():
        print(f"❌ Roadmap directory not found: {roadmap_dir}")
        return 1

    print("📝 Migrating documentation fields to markdown files...")
    print(f"   Roadmap directory: {roadmap_dir}")
    print(f"   Repository root:   {root_dir}")
    if dry_run:
        print("   Mode:              DRY RUN (no files will be created)")
    print()

    # Run migration
    result = migrate_roadmap_docs(
        roadmap_dir=roadmap_dir,
        repo_root=root_dir,
        dry_run=dry_run,
        verbose=verbose,
    )

    # Print report
    report = format_migration_report(result, verbose=verbose)
    print(report)

    if result.total_errors > 0:
        print("\n❌ Migration completed with errors")
        return 1
    elif result.total_migrated > 0:
        if dry_run:
            print("\n✅ Dry run complete. Run without --dry-run to apply changes.")
        else:
            print("\n✅ Migration complete!")
            print("\nNext steps:")
            print("  1. Review the created markdown files")
            print("  2. git add the new .md files")
            print("  3. Commit with: git commit -m 'docs: Migrate YAML docs to markdown'")
        return 0
    else:
        print("\n✅ Nothing to migrate (files already exist or no source data)")
        return 0
