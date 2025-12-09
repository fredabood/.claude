#!/usr/bin/env python3
"""
Standalone migration execution script.

Runs directory structure migration without importing full package.
"""

import sys
from pathlib import Path

# Load the migration module directly
migration_file = Path(__file__).parent.parent / "vibey" / "roadmap" / "serialization" / "directory_migration_v2.py"

# Read and exec the migration module
exec(open(migration_file).read(), globals())


def main():
    """Execute migration with dry-run option."""
    import argparse

    parser = argparse.ArgumentParser(description="Execute directory structure migration")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without making changes"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute the actual migration"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate existing flat structure"
    )
    parser.add_argument(
        "--roadmap-dir",
        type=Path,
        default=Path.cwd() / ".vibey" / "roadmap",
        help="Path to roadmap directory (default: .vibey/roadmap)"
    )

    args = parser.parse_args()

    roadmap_dir = Path(args.roadmap_dir)

    if not roadmap_dir.exists():
        print(f"❌ Roadmap directory not found: {roadmap_dir}")
        return 1

    # Validate only
    if args.validate:
        print(f"🔍 Validating flat structure in {roadmap_dir}\n")
        success, errors = validate_migration(roadmap_dir)

        if success:
            print("✅ Validation successful - flat structure is correct!")
            return 0
        else:
            print("❌ Validation failed:")
            for error in errors:
                print(f"  - {error}")
            return 1

    # Dry-run
    if args.dry_run:
        print(f"🔍 DRY RUN - No changes will be made\n")
        print(f"Roadmap directory: {roadmap_dir}\n")

        result = migrate_to_flat_structure(
            roadmap_dir=roadmap_dir,
            dry_run=True,
            backup=False,
            use_git_mv=True,
            verbose=True
        )

        print("\n" + "="*80)
        print("DRY RUN SUMMARY")
        print("="*80)
        print(f"Tracks to migrate: {result.tracks_migrated}")
        print(f"Sprints to migrate: {result.sprints_migrated}")
        print(f"Tasks to migrate: {result.tasks_migrated}")
        print(f"Context dirs to migrate: {result.context_dirs_migrated}")
        print(f"Files to move: {result.files_moved}")
        print(f"References to update: {result.references_updated}")

        if result.errors:
            print(f"\n⚠️  Errors found:")
            for error in result.errors:
                print(f"  - {error}")
            return 1
        else:
            print(f"\n✅ No errors found - ready to migrate!")

        return 0

    # Execute migration
    if args.execute:
        print(f"🚀 EXECUTING MIGRATION\n")
        print(f"Roadmap directory: {roadmap_dir}\n")

        # Confirm
        response = input("This will modify the directory structure. Continue? [y/N]: ")
        if response.lower() != 'y':
            print("Migration cancelled.")
            return 0

        print("\n📦 Creating backup before migration...")

        result = migrate_to_flat_structure(
            roadmap_dir=roadmap_dir,
            dry_run=False,
            backup=True,
            use_git_mv=True,
            verbose=True
        )

        print("\n" + "="*80)
        print("MIGRATION COMPLETE")
        print("="*80)
        print(f"Tracks migrated: {result.tracks_migrated}")
        print(f"Sprints migrated: {result.sprints_migrated}")
        print(f"Tasks migrated: {result.tasks_migrated}")
        print(f"Context dirs migrated: {result.context_dirs_migrated}")
        print(f"Files moved: {result.files_moved}")
        print(f"References updated: {result.references_updated}")

        if result.backup_path:
            print(f"\n💾 Backup saved to: {result.backup_path}")

        if result.errors:
            print(f"\n❌ Errors occurred:")
            for error in result.errors:
                print(f"  - {error}")
            return 1

        # Run validation
        print("\n🔍 Running post-migration validation...")
        success, errors = validate_migration(roadmap_dir)

        if success:
            print("✅ Validation successful!")
            return 0
        else:
            print("❌ Validation failed:")
            for error in errors:
                print(f"  - {error}")
            return 1

    # No action specified
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
