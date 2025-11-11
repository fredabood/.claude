#!/usr/bin/env python3
"""
Generate Roadmap Documentation

Generates table_of_contents.json and markdown views for the entire
hierarchical roadmap structure.

This completes documentation-system Sprint 1 by generating all documentation
artifacts from the YAML source files.

Usage:
    python3 framework/scripts/generate-roadmap-docs.py              # Generate all
    python3 framework/scripts/generate-roadmap-docs.py --track mcp-server  # Generate one track
    python3 framework/scripts/generate-roadmap-docs.py --dry-run    # Show what would be generated
"""

import sys
import argparse
import json
import yaml
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Add framework to path
framework_root = Path(__file__).parent.parent
sys.path.insert(0, str(framework_root.parent))

from vibey.roadmap.toc_generator import TOCGenerator
from vibey.roadmap.markdown_generator import MarkdownGenerator


def main():
    parser = argparse.ArgumentParser(description='Generate roadmap documentation')
    parser.add_argument('--roadmap-root', default='.vibey/roadmap', help='Roadmap root directory')
    parser.add_argument('--roadmap-yaml', default='.vibey/roadmap.yaml', help='Roadmap YAML file')
    parser.add_argument('--track', help='Generate docs for specific track only')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be generated')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    roadmap_root = Path(args.roadmap_root)
    roadmap_yaml = Path(args.roadmap_yaml)

    if not roadmap_yaml.exists():
        print(f"❌ Roadmap YAML not found: {roadmap_yaml}")
        return 1

    if not roadmap_root.exists():
        print(f"❌ Roadmap root not found: {roadmap_root}")
        return 1

    # Initialize generators
    toc_gen = TOCGenerator(str(roadmap_root))
    md_gen = MarkdownGenerator(str(roadmap_root))

    # Load roadmap
    with open(roadmap_yaml) as f:
        roadmap_data = yaml.safe_load(f)

    roadmap_info = roadmap_data.get('roadmap', {})
    tracks = roadmap_info.get('tracks', [])

    print(f"🗺️  Generating documentation for: {roadmap_info.get('name', 'Roadmap')}")
    print(f"   Root: {roadmap_root}")
    print()

    stats = {
        'toc_files': 0,
        'markdown_files': 0,
        'tracks': 0,
        'sprints': 0,
        'tasks': 0,
    }

    # Filter tracks if specified
    if args.track:
        tracks = [t for t in tracks if t.get('id') == args.track]
        if not tracks:
            print(f"❌ Track not found: {args.track}")
            return 1

    # Generate roadmap-level TOC
    print("📋 Generating roadmap-level TOC...")
    try:
        roadmap_toc = toc_gen.generate_roadmap_toc(str(roadmap_yaml))
        toc_path = roadmap_root / 'table_of_contents.json'

        if args.dry_run:
            print(f"   Would create: {toc_path}")
        else:
            toc_gen.save_toc(roadmap_toc, str(toc_path))
            print(f"   ✓ Created: {toc_path}")
        stats['toc_files'] += 1
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Generate roadmap markdown
    print("📄 Generating roadmap markdown...")
    try:
        roadmap_md = md_gen.generate_roadmap_markdown(str(roadmap_yaml))
        md_path = roadmap_root / 'roadmap.md'

        if args.dry_run:
            print(f"   Would create: {md_path}")
        else:
            with open(md_path, 'w') as f:
                f.write(roadmap_md)
            print(f"   ✓ Created: {md_path}")
        stats['markdown_files'] += 1
    except Exception as e:
        print(f"   ✗ Error: {e}")

    print()

    # Generate track-level docs
    for track in tracks:
        track_id = track.get('id')
        track_name = track.get('name', track_id)
        track_slug = toc_gen._id_to_slug(track_id)
        track_dir = roadmap_root / track_slug

        if not track_dir.exists():
            if args.verbose:
                print(f"⚠️  Track directory not found: {track_dir}")
            continue

        print(f"📁 Track: {track_name}")
        stats['tracks'] += 1

        # Generate track TOC
        track_yaml_path = track_dir / "track.yaml"
        if track_yaml_path.exists():
            try:
                track_toc = toc_gen.generate_track_toc(track_slug, str(track_yaml_path))
                toc_path = track_dir / 'table_of_contents.json'

                if args.dry_run:
                    print(f"   Would create: {toc_path}")
                else:
                    toc_gen.save_toc(track_toc, str(toc_path))
                    print(f"   ✓ TOC: {toc_path.relative_to(roadmap_root.parent)}")
                stats['toc_files'] += 1
            except Exception as e:
                print(f"   ✗ TOC Error: {e}")

        # Generate track markdown
        if track_yaml_path.exists():
            try:
                track_md = md_gen.generate_track_markdown(str(track_yaml_path))
                md_path = track_dir / "track.md"

                if args.dry_run:
                    print(f"   Would create: {md_path}")
                else:
                    with open(md_path, 'w') as f:
                        f.write(track_md)
                    print(f"   ✓ MD: {md_path.relative_to(roadmap_root.parent)}")
                stats['markdown_files'] += 1
            except Exception as e:
                print(f"   ✗ MD Error: {e}")

        # Find sprints in this track
        sprint_dirs = sorted([d for d in track_dir.iterdir() if d.is_dir() and d.name.startswith(track_slug)])

        for sprint_dir in sprint_dirs:
            sprint_slug = sprint_dir.name
            sprint_yaml_path = sprint_dir / "sprint.yaml"

            if not sprint_yaml_path.exists():
                continue

            # Load sprint to get name
            with open(sprint_yaml_path) as f:
                sprint_data = yaml.safe_load(f)
            sprint_info = sprint_data.get('sprint', {})
            sprint_name = sprint_info.get('name', sprint_slug)

            if args.verbose:
                print(f"   📋 Sprint: {sprint_name}")
            stats['sprints'] += 1

            # Generate sprint TOC
            try:
                sprint_toc = toc_gen.generate_sprint_toc(track_slug, sprint_slug, str(sprint_yaml_path))
                toc_path = sprint_dir / 'table_of_contents.json'

                if args.dry_run:
                    if args.verbose:
                        print(f"      Would create: {toc_path}")
                else:
                    toc_gen.save_toc(sprint_toc, str(toc_path))
                    if args.verbose:
                        print(f"      ✓ TOC: {toc_path.relative_to(roadmap_root.parent)}")
                stats['toc_files'] += 1
            except Exception as e:
                if args.verbose:
                    print(f"      ✗ TOC Error: {e}")

            # Generate sprint markdown
            try:
                sprint_md = md_gen.generate_sprint_markdown(str(sprint_yaml_path))
                md_path = sprint_dir / "sprint.md"

                if args.dry_run:
                    if args.verbose:
                        print(f"      Would create: {md_path}")
                else:
                    with open(md_path, 'w') as f:
                        f.write(sprint_md)
                    if args.verbose:
                        print(f"      ✓ MD: {md_path.relative_to(roadmap_root.parent)}")
                stats['markdown_files'] += 1
            except Exception as e:
                if args.verbose:
                    print(f"      ✗ MD Error: {e}")

            # Find tasks in this sprint
            task_dirs = sorted([d for d in sprint_dir.iterdir() if d.is_dir() and d.name.startswith(sprint_slug)])
            stats['tasks'] += len(task_dirs)

            for task_dir in task_dirs:
                task_slug = task_dir.name
                task_yaml_path = task_dir / "task.yaml"

                if not task_yaml_path.exists():
                    continue

                # Generate task markdown
                try:
                    task_md = md_gen.generate_task_markdown(str(task_yaml_path))
                    md_path = task_dir / "task.md"

                    if args.dry_run:
                        if args.verbose:
                            print(f"         Would create: {md_path}")
                    else:
                        with open(md_path, 'w') as f:
                            f.write(task_md)
                        # Only show if very verbose
                    stats['markdown_files'] += 1
                except Exception as e:
                    if args.verbose:
                        print(f"         ✗ MD Error: {e}")

    # Summary
    print()
    print("=" * 60)
    print("📊 Generation Summary")
    print("=" * 60)
    print(f"Tracks processed:    {stats['tracks']}")
    print(f"Sprints processed:   {stats['sprints']}")
    print(f"Tasks processed:     {stats['tasks']}")
    print(f"TOC files:           {stats['toc_files']}")
    print(f"Markdown files:      {stats['markdown_files']}")
    print(f"Total files:         {stats['toc_files'] + stats['markdown_files']}")
    print()

    if args.dry_run:
        print("✓ Dry run complete (no files created)")
    else:
        print("✓ Documentation generation complete")

    return 0


if __name__ == '__main__':
    sys.exit(main())
