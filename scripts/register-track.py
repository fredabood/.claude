#!/usr/bin/env python3
"""
Track Registration Helper

Registers a track directory with the main roadmap.yaml file.
This ensures that new tracks created in .vibey/roadmap/* are properly
reflected in the main roadmap.

Usage:
    python3 scripts/register-track.py <track-id>
    python3 scripts/register-track.py <track-id> --auto  # Auto-detect from track.yaml
    python3 scripts/register-track.py --scan  # Scan for unregistered tracks
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional

# Add vibey to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TrackRegistrar:
    """Registers tracks with the main roadmap."""

    def __init__(self, root_dir: Path = None):
        self.root_dir = root_dir or Path.cwd()
        self.vibey_dir = self.root_dir / '.vibey'
        self.roadmap_file = self.vibey_dir / 'roadmap.yaml'
        self.roadmap_dir = self.vibey_dir / 'roadmap'

        self.roadmap_data = None

    def load_roadmap(self):
        """Load main roadmap.yaml."""
        if not self.roadmap_file.exists():
            raise FileNotFoundError(f"Roadmap not found: {self.roadmap_file}")

        with open(self.roadmap_file, 'r') as f:
            self.roadmap_data = yaml.safe_load(f)

    def save_roadmap(self):
        """Save updated roadmap.yaml."""
        # Create backup
        backup_file = self.roadmap_file.with_suffix('.yaml.bak')
        import shutil
        shutil.copy(self.roadmap_file, backup_file)

        # Save
        with open(self.roadmap_file, 'w') as f:
            yaml.dump(self.roadmap_data, f, default_flow_style=False, sort_keys=False)

        print(f"✅ Saved roadmap: {self.roadmap_file}")
        print(f"   Backup: {backup_file}")

    def get_track_data(self, track_id: str) -> Optional[Dict]:
        """Load track data from track.yaml file."""
        track_file = self.roadmap_dir / track_id / 'track.yaml'

        if not track_file.exists():
            return None

        with open(track_file, 'r') as f:
            return yaml.safe_load(f)['track']

    def is_track_registered(self, track_id: str) -> bool:
        """Check if track is already registered in roadmap."""
        tracks = self.roadmap_data['roadmap']['tracks']
        return any(t['id'] == track_id for t in tracks)

    def register_track(self, track_id: str, auto: bool = True) -> bool:
        """
        Register a track with the roadmap.

        Args:
            track_id: Track ID to register
            auto: If True, auto-detect details from track.yaml

        Returns:
            True if registered, False if already registered
        """
        # Check if already registered
        if self.is_track_registered(track_id):
            print(f"⚠️  Track '{track_id}' is already registered")
            return False

        # Get track data
        track_data = self.get_track_data(track_id)
        if not track_data:
            print(f"❌ Track file not found: .vibey/roadmap/{track_id}/track.yaml")
            return False

        # Create track entry
        track_entry = {
            'id': track_id,
            'name': track_data.get('name', track_id),
            'status': track_data.get('status', 'not_started'),
            'priority': track_data.get('priority', 'medium')
        }

        # Add to roadmap
        self.roadmap_data['roadmap']['tracks'].append(track_entry)

        # Update progress metrics
        self._update_progress()

        print(f"✅ Registered track: {track_id}")
        print(f"   Name: {track_entry['name']}")
        print(f"   Status: {track_entry['status']}")
        print(f"   Priority: {track_entry['priority']}")

        return True

    def scan_unregistered(self) -> List[str]:
        """Scan for unregistered tracks."""
        # Get registered track IDs
        registered = {t['id'] for t in self.roadmap_data['roadmap']['tracks']}

        # Get all track directories
        unregistered = []

        if self.roadmap_dir.exists():
            for track_dir in self.roadmap_dir.iterdir():
                if not track_dir.is_dir():
                    continue

                track_file = track_dir / 'track.yaml'
                if track_file.exists():
                    with open(track_file, 'r') as f:
                        track_data = yaml.safe_load(f)
                        track_id = track_data['track']['id']

                        if track_id not in registered:
                            unregistered.append(track_id)

        return unregistered

    def register_all_unregistered(self) -> int:
        """Register all unregistered tracks."""
        unregistered = self.scan_unregistered()

        if not unregistered:
            print("✅ All tracks are registered")
            return 0

        print(f"Found {len(unregistered)} unregistered track(s):\n")

        count = 0
        for track_id in unregistered:
            track_data = self.get_track_data(track_id)
            print(f"  • {track_id}")
            print(f"    Name: {track_data.get('name', 'N/A')}")
            print(f"    Status: {track_data.get('status', 'N/A')}")
            print()

            if self.register_track(track_id):
                count += 1
                print()

        return count

    def _update_progress(self):
        """Update progress metrics after track changes."""
        tracks = self.roadmap_data['roadmap']['tracks']

        # Update tracks_total
        self.roadmap_data['roadmap']['progress']['tracks_total'] = len(tracks)

        # Update tracks_completed
        completed = sum(
            1 for t in tracks
            if t['status'] in ['completed', 'production_ready', 'deployed']
        )
        self.roadmap_data['roadmap']['progress']['tracks_completed'] = completed

        print(f"   Updated progress: {completed}/{len(tracks)} tracks completed")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Register track with main roadmap',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'track_id',
        nargs='?',
        help='Track ID to register'
    )
    parser.add_argument(
        '--scan',
        action='store_true',
        help='Scan for and register all unregistered tracks'
    )
    parser.add_argument(
        '--auto',
        action='store_true',
        default=True,
        help='Auto-detect track details from track.yaml (default: True)'
    )
    parser.add_argument(
        '--dir',
        type=Path,
        help='Root directory (defaults to current directory)'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.scan and not args.track_id:
        parser.error("Either provide track_id or use --scan")

    try:
        registrar = TrackRegistrar(root_dir=args.dir)
        registrar.load_roadmap()

        if args.scan:
            # Scan and register all
            count = registrar.register_all_unregistered()

            if count > 0:
                registrar.save_roadmap()
                print(f"\n✅ Registered {count} track(s)")
            else:
                print("\n✅ No unregistered tracks found")

        else:
            # Register single track
            if registrar.register_track(args.track_id, auto=args.auto):
                registrar.save_roadmap()
            else:
                sys.exit(1)

    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
