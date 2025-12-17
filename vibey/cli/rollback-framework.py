#!/usr/bin/env python3
"""
Vibey Framework Rollback Tool

Rollback the Vibey framework to a previous backup.

This script helps recover from failed upgrades by restoring from
.claude-backup-* directories created during deployment.

Usage:
    python3 rollback-framework.py [--list]
    python3 rollback-framework.py --backup BACKUP_DIR
    python3 rollback-framework.py --auto (use most recent backup)
"""

import sys
import argparse
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Tuple


def find_backups(search_dir: Path = Path('.')) -> List[Tuple[Path, datetime]]:
    """
    Find all Vibey framework backup directories.

    Returns:
        List of (backup_path, timestamp) tuples, sorted by timestamp (newest first)
    """
    backups = []

    for item in search_dir.glob('.claude-backup-*'):
        if item.is_dir():
            # Extract timestamp from directory name
            # Format: .claude-backup-YYYYMMDD-HHMMSS
            try:
                timestamp_str = item.name.replace('.claude-backup-', '')
                timestamp = datetime.strptime(timestamp_str, '%Y%m%d-%H%M%S')
                backups.append((item, timestamp))
            except ValueError:
                # Skip if timestamp doesn't match expected format
                continue

    # Sort by timestamp, newest first
    backups.sort(key=lambda x: x[1], reverse=True)

    return backups


def list_backups() -> int:
    """
    List all available backups.

    Returns:
        0 if backups found, 1 if no backups
    """
    backups = find_backups()

    if not backups:
        print("No Vibey framework backups found")
        print()
        print("Backups are automatically created when you:")
        print("  - Re-deploy the framework with existing files")
        print("  - Upgrade to a new framework version")
        print()
        print("Backup directories are named: .claude-backup-YYYYMMDD-HHMMSS")
        return 1

    print(f"Found {len(backups)} backup(s):")
    print()

    for i, (backup_path, timestamp) in enumerate(backups, 1):
        # Check backup size
        try:
            size = sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file())
            size_mb = size / (1024 * 1024)

            # Note: Marker is now .vibey/ai-reference.md (outside .claude/ backup)
            # Backups don't include the marker anymore
            version = "unknown"

            print(f"{i}. {backup_path.name}")
            print(f"   Created: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Version: {version}")
            print(f"   Size: {size_mb:.1f} MB")
            print()
        except Exception as e:
            print(f"{i}. {backup_path.name}")
            print(f"   Created: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Error reading backup: {e}")
            print()

    return 0


def rollback(backup_path: Path, dry_run: bool = False) -> int:
    """
    Rollback to a specific backup.

    Args:
        backup_path: Path to backup directory
        dry_run: If True, show what would happen without actually doing it

    Returns:
        0 on success, 1 on error
    """
    claude_dir = Path('.claude')

    # Validate backup exists
    if not backup_path.exists() or not backup_path.is_dir():
        print(f"❌ Error: Backup directory not found: {backup_path}")
        return 1

    # Check if backup looks valid
    required_dirs = ['agents', 'workflows', 'templates']
    missing_dirs = [d for d in required_dirs if not (backup_path / d).exists()]

    if missing_dirs:
        print(f"⚠️  Warning: Backup may be incomplete (missing: {', '.join(missing_dirs)})")
        response = input("Continue anyway? [y/N] ")
        if response.lower() not in ['y', 'yes']:
            print("Cancelled")
            return 1

    if dry_run:
        print("DRY RUN MODE - No changes will be made")
        print()

    # Show what will happen
    print("Rollback Plan:")
    print(f"  From: {backup_path}")
    print(f"  To:   {claude_dir}")
    print()

    if claude_dir.exists():
        print("  Step 1: Backup current .claude/ to .claude-rollback-backup/")
    else:
        print("  Step 1: (skip - no current .claude/ directory)")

    print("  Step 2: Restore files from backup")
    print("  Step 3: Update marker file")
    print()

    if dry_run:
        print("✓ Dry run complete (no changes made)")
        return 0

    # Confirm
    response = input("Proceed with rollback? [y/N] ")
    if response.lower() not in ['y', 'yes']:
        print("Cancelled")
        return 1

    try:
        # Step 1: Backup current .claude if it exists
        if claude_dir.exists():
            rollback_backup = Path('.claude-rollback-backup')
            if rollback_backup.exists():
                shutil.rmtree(rollback_backup)

            print(f"Creating safety backup: {rollback_backup}")
            shutil.copytree(claude_dir, rollback_backup)

            # Remove current .claude
            shutil.rmtree(claude_dir)

        # Step 2: Restore from backup
        print(f"Restoring from: {backup_path}")
        shutil.copytree(backup_path, claude_dir)

        # Step 3: Note about marker
        # Marker (.vibey/ai-reference.md) is outside .claude/ so not affected by rollback
        print()
        print("✅ Rollback complete!")
        print()
        print(f"Restored from backup: {backup_path.name}")
        print()
        print("⚠️  Note: Framework marker (.vibey/ai-reference.md) was not affected by rollback")
        print("   If you need to update it, run /vibey")

        print()
        print("Safety backup saved to: .claude-rollback-backup/")
        print("(You can delete this once you've verified everything works)")

        return 0

    except Exception as e:
        print(f"❌ Error during rollback: {e}")
        print()
        print("If .claude/ is in a broken state, you can:")
        print("  1. Restore from .claude-rollback-backup/ if it exists")
        print("  2. Manually copy files from the backup directory")
        print("  3. Re-deploy the framework fresh")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Rollback Vibey framework to a previous backup"
    )
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List available backups'
    )
    parser.add_argument(
        '--backup', '-b',
        type=Path,
        help='Path to backup directory to restore from'
    )
    parser.add_argument(
        '--auto', '-a',
        action='store_true',
        help='Automatically rollback to most recent backup'
    )
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Show what would happen without actually doing it'
    )

    args = parser.parse_args()

    # List backups
    if args.list:
        return list_backups()

    # Auto mode - use most recent backup
    if args.auto:
        backups = find_backups()
        if not backups:
            print("❌ No backups found")
            return 1

        backup_path, timestamp = backups[0]
        print(f"Using most recent backup: {backup_path.name}")
        print(f"Created: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        return rollback(backup_path, args.dry_run)

    # Manual backup selection
    if args.backup:
        return rollback(args.backup, args.dry_run)

    # No action specified - show help
    print("Vibey Framework Rollback Tool")
    print()
    print("Usage:")
    print("  List available backups:")
    print("    python3 rollback-framework.py --list")
    print()
    print("  Rollback to most recent backup:")
    print("    python3 rollback-framework.py --auto")
    print()
    print("  Rollback to specific backup:")
    print("    python3 rollback-framework.py --backup .claude-backup-20241105-120000")
    print()
    print("  Dry run (show what would happen):")
    print("    python3 rollback-framework.py --auto --dry-run")
    print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
