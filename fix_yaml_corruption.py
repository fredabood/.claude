#!/usr/bin/env python3
"""
Quick fix script to remove Python object tags from YAML files.

The issue: Some YAML files contain:
  current_status: !!python/object/apply:vibey.roadmap.models.common.Status
  - completed

Should be:
  current_status: completed
"""

import re
from pathlib import Path

def fix_yaml_file(filepath: Path) -> bool:
    """Fix Python object tags in a YAML file."""
    content = filepath.read_text()

    # Pattern to match the Python object serialization
    pattern = r'current_status: !!python/object/apply:vibey\.roadmap\.models\.common\.Status\s+- (\w+)'

    # Replace with simple string
    fixed_content = re.sub(pattern, r'current_status: \1', content)

    if content != fixed_content:
        filepath.write_text(fixed_content)
        return True
    return False

def main():
    """Fix all corrupted track YAML files."""
    roadmap_dir = Path('.vibey/roadmap')

    corrupted_tracks = [
        'mcp-server',
        'goose-port',
        'multi-platform',
        'aider-port',
        'continue-port',
        'windsurf-port',
        'jetbrains-port',
    ]

    print("🔧 Fixing YAML corruption...\n")

    fixed_count = 0
    for track_id in corrupted_tracks:
        track_file = roadmap_dir / track_id / 'track.yaml'
        if track_file.exists():
            if fix_yaml_file(track_file):
                print(f"✅ Fixed: {track_id}/track.yaml")
                fixed_count += 1
            else:
                print(f"⚠️  No corruption found: {track_id}/track.yaml")
        else:
            print(f"❌ Not found: {track_id}/track.yaml")

    print(f"\n✨ Fixed {fixed_count} files")

if __name__ == '__main__':
    main()
