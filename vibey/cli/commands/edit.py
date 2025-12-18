"""
Safe YAML edit commands.

Provides safe editing, bulk editing, validation, and rollback functionality
for YAML files.
"""

from pathlib import Path
from typing import Optional


def edit_file_cmd(file_path: str, modifications: list, dry_run: bool = False) -> int:
    """Safely edit a single YAML file."""
    from vibey.operations.roadmap.safe_yaml_editor import SafeYAMLEditor

    # Parse modifications from "key=value" format
    mod_dict = {}
    for mod in modifications:
        if '=' not in mod:
            print(f"Error: Invalid modification format '{mod}' (expected key=value)")
            return 1

        key, value = mod.split('=', 1)
        mod_dict[key] = value

    if not mod_dict:
        print("Error: No modifications specified. Use --set key=value")
        return 1

    try:
        editor = SafeYAMLEditor(auto_backup=True, validate=True)

        if dry_run:
            print("🔍 Dry-run mode: Previewing changes (no files will be modified)")
            print()

        result = editor.edit_file(file_path, mod_dict, dry_run=dry_run)

        if result.success:
            print(f"✅ Successfully {'validated' if dry_run else 'edited'}: {result.file_path}")

            if result.changes_made:
                print("\nChanges:")
                for field, change in result.changes_made.items():
                    print(f"  {field}: {change['old']} → {change['new']}")

            if result.backup_path:
                print(f"\nBackup: {result.backup_path}")

            if result.warnings:
                print("\nWarnings:")
                for warning in result.warnings:
                    print(f"  ⚠️  {warning}")

            return 0
        else:
            print(f"❌ Edit failed: {result.file_path}")
            print("\nErrors:")
            for error in result.errors:
                print(f"  • {error}")
            return 1

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


def edit_bulk_cmd(file_pattern: str, modifications: list, dry_run: bool = False) -> int:
    """Safely bulk edit multiple YAML files."""
    from vibey.operations.roadmap.safe_yaml_editor import SafeYAMLEditor

    # Parse modifications
    mod_dict = {}
    for mod in modifications:
        if '=' not in mod:
            print(f"Error: Invalid modification format '{mod}' (expected key=value)")
            return 1

        key, value = mod.split('=', 1)
        mod_dict[key] = value

    if not mod_dict:
        print("Error: No modifications specified. Use --set key=value")
        return 1

    try:
        editor = SafeYAMLEditor(auto_backup=True, validate=True)

        if dry_run:
            print("🔍 Dry-run mode: Previewing changes (no files will be modified)")
            print()

        print(f"Finding files matching: {file_pattern}")
        result = editor.bulk_edit(file_pattern, mod_dict, dry_run=dry_run, root_dir=Path.cwd())

        print(f"\nFiles found: {result.total_files}")

        if result.success:
            print(f"✅ Bulk edit {'validated' if dry_run else 'completed'} successfully")
            print(f"  Files {'would be ' if dry_run else ''}changed: {result.files_changed}")

            if result.checkpoint_path:
                print(f"  Checkpoint: {result.checkpoint_path}")

            return 0
        else:
            print(f"❌ Bulk edit failed")
            print(f"  Files changed: {result.files_changed}")
            print(f"  Files failed: {result.files_failed}")

            if result.rollback_performed:
                print(f"  ✅ All changes rolled back")

            if result.errors:
                print("\nErrors:")
                for error in result.errors[:10]:  # Limit to first 10
                    print(f"  • {error}")

                if len(result.errors) > 10:
                    print(f"  ... and {len(result.errors) - 10} more errors")

            return 1

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


def edit_validate_cmd(file_path: Optional[str] = None, validate_all: bool = False) -> int:
    """Validate YAML file(s)."""
    from vibey.operations.roadmap.safe_yaml_editor import SafeYAMLEditor

    editor = SafeYAMLEditor()

    if validate_all:
        # Validate all YAML files in roadmap
        roadmap_dir = Path.cwd() / ".vibey" / "roadmap"

        if not roadmap_dir.exists():
            print("Error: Roadmap directory not found")
            return 1

        yaml_files = list(roadmap_dir.rglob("*.yaml"))
        print(f"Validating {len(yaml_files)} YAML files...")
        print()

        valid_count = 0
        invalid_count = 0
        error_files = []

        for yaml_file in yaml_files:
            result = editor.validate_yaml_file(yaml_file)

            if result.valid:
                valid_count += 1
                print(f"✅ {yaml_file.relative_to(Path.cwd())}")
            else:
                invalid_count += 1
                print(f"❌ {yaml_file.relative_to(Path.cwd())}")
                error_files.append((yaml_file, result))

                for error in result.errors[:3]:  # Show first 3 errors per file
                    print(f"   • {error}")

        print()
        print(f"Summary: {valid_count} valid, {invalid_count} invalid")

        if error_files:
            print("\nFiles with errors:")
            for yaml_file, _ in error_files:
                print(f"  • {yaml_file.relative_to(Path.cwd())}")

        return 0 if invalid_count == 0 else 1

    elif file_path:
        # Validate single file
        result = editor.validate_yaml_file(file_path)

        print(f"Validating: {file_path}")
        print()

        if result.valid:
            print("✅ Validation passed")

            if result.warnings:
                print("\nWarnings:")
                for warning in result.warnings:
                    print(f"  ⚠️  {warning}")

            return 0
        else:
            print("❌ Validation failed")
            print("\nErrors:")
            for error in result.errors:
                print(f"  • {error}")

            if result.warnings:
                print("\nWarnings:")
                for warning in result.warnings:
                    print(f"  ⚠️  {warning}")

            return 1

    else:
        print("Error: Specify --file <path> or --all")
        return 1


def edit_rollback_cmd(last_n: int = 1) -> int:
    """Rollback recent edit operations."""
    from vibey.operations.roadmap.safe_yaml_editor import SafeYAMLEditor

    editor = SafeYAMLEditor()

    print(f"Rolling back last {last_n} edit(s)...")
    print()

    success_count = 0
    for i in range(last_n):
        if editor.rollback_last_edit():
            success_count += 1
        else:
            if i == 0:
                print("No backups found to rollback")
            break

    if success_count > 0:
        print()
        print(f"✅ Rolled back {success_count} edit(s)")
        return 0
    else:
        print()
        print("❌ No edits rolled back")
        return 1
