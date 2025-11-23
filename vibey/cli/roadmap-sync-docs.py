#!/usr/bin/env python3
"""
Documentation Synchronization CLI

Synchronizes documentation from .vibey/roadmap/ to docs/roadmap/ with
support for various filtering and preview options.

Usage:
    python3 framework/scripts/roadmap-sync-docs.py              # Sync all
    python3 framework/scripts/roadmap-sync-docs.py --dry-run    # Preview
    python3 framework/scripts/roadmap-sync-docs.py --track mcp-server  # Sync one track
    python3 framework/scripts/roadmap-sync-docs.py --summary    # Show manifest summary
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

# Add framework to path
framework_root = Path(__file__).parent.parent
sys.path.insert(0, str(framework_root.parent))

from vibey.operations.docs.sync_engine import SyncEngine, SyncConfig
from vibey.operations.docs.sync_manifest import SyncManifest


def print_sync_result(result, dry_run: bool = False):
    """Print sync result in a user-friendly format."""
    prefix = "Would sync" if dry_run else "Synced"

    print()
    print("=" * 60)
    print(f"📄 Documentation Sync {'Preview' if dry_run else 'Complete'}")
    print("=" * 60)

    if result.files_copied:
        print(f"\n✓ {prefix} {len(result.files_copied)} file(s):")
        for file in result.files_copied:
            print(f"  • {file}")

    if result.files_skipped:
        print(f"\n⏭️  Skipped {len(result.files_skipped)} unchanged file(s)")
        if dry_run:
            for file in result.files_skipped[:10]:  # Show first 10
                print(f"  • {file}")
            if len(result.files_skipped) > 10:
                print(f"  ... and {len(result.files_skipped) - 10} more")

    if result.files_deleted:
        print(f"\n🗑️  {'Would delete' if dry_run else 'Deleted'} {len(result.files_deleted)} orphaned file(s):")
        for file in result.files_deleted:
            print(f"  • {file}")

    if result.errors:
        print(f"\n❌ {len(result.errors)} error(s):")
        for file, error in result.errors:
            print(f"  • {file}: {error}")

    print(f"\n⏱️  Duration: {result.duration_seconds:.2f}s")

    if not dry_run and result.success:
        print("\n✅ Synchronization completed successfully")
    elif dry_run:
        print("\n💡 Run without --dry-run to perform the sync")
    else:
        print("\n⚠️  Synchronization completed with errors")

    print()


def main():
    parser = argparse.ArgumentParser(
        description='Synchronize roadmap documentation from .vibey/roadmap to docs/roadmap'
    )
    parser.add_argument('--source', default='.vibey/roadmap', help='Source directory')
    parser.add_argument('--target', default='docs/roadmap', help='Target directory')
    parser.add_argument('--track', help='Sync specific track only')
    parser.add_argument('--sprint', help='Sync specific sprint only')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without syncing')
    parser.add_argument('--delete-orphaned', action='store_true', help='Delete files in target not in source')
    parser.add_argument('--summary', action='store_true', help='Show sync manifest summary')
    parser.add_argument('--include', action='append', help='Include pattern (can be used multiple times)')
    parser.add_argument('--exclude', action='append', help='Exclude pattern (can be used multiple times)')

    args = parser.parse_args()

    # Show manifest summary if requested
    if args.summary:
        manifest = SyncManifest(f"{args.source}/.sync-manifest.json")
        manifest.print_summary()
        return 0

    # Build config
    config = SyncConfig(
        source_dir=args.source,
        target_dir=args.target,
        delete_orphaned=args.delete_orphaned
    )

    # Override patterns if provided
    if args.include:
        config.include_patterns = args.include
    if args.exclude:
        config.exclude_patterns = args.exclude

    # Handle track/sprint filtering by adding to source path
    if args.track and args.sprint:
        print("❌ Error: Cannot specify both --track and --sprint")
        return 1

    if args.track:
        # Sync specific track
        track_slug = args.track
        config.source_dir = f"{args.source}/{track_slug}"
        config.target_dir = f"{args.target}/{track_slug}"
        print(f"🎯 Syncing track: {track_slug}")

    elif args.sprint:
        # Sync specific sprint (need to infer track from sprint ID)
        sprint_id = args.sprint
        # Sprint IDs are like "documentation-system-1"
        # Track ID is everything before the last dash and number
        parts = sprint_id.rsplit('-', 1)
        if len(parts) == 2 and parts[1].isdigit():
            track_slug = parts[0]
            sprint_slug = sprint_id
            config.source_dir = f"{args.source}/{track_slug}/{sprint_slug}"
            config.target_dir = f"{args.target}/{track_slug}/{sprint_slug}"
            print(f"🎯 Syncing sprint: {sprint_slug}")
        else:
            print(f"❌ Error: Invalid sprint ID format: {sprint_id}")
            return 1

    # Create sync engine
    engine = SyncEngine(config)

    # Perform sync
    try:
        result = engine.sync(dry_run=args.dry_run)
        print_sync_result(result, dry_run=args.dry_run)

        return 0 if result.success else 1

    except Exception as e:
        print(f"❌ Sync failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
