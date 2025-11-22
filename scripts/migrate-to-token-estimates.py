#!/usr/bin/env python3
"""
Migrate time-based estimates to token-based estimates.

This script converts existing `estimated_duration` fields (e.g., "4 hours")
to `estimated_tokens` fields using a 10K tokens/hour heuristic.

Usage:
    python scripts/migrate-to-token-estimates.py [--dry-run] [--verbose]

Options:
    --dry-run   Show what would be changed without making changes
    --verbose   Show detailed output for each file
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml

from vibey.roadmap.token_estimation import convert_time_to_tokens, categorize_by_tokens


def get_roadmap_root() -> Path:
    """Get the roadmap data directory."""
    return Path(__file__).parent.parent / ".vibey" / "roadmap"


def migrate_task_file(
    task_path: Path,
    dry_run: bool = False,
    verbose: bool = False,
) -> dict:
    """Migrate a single task.yaml file.

    Returns:
        Dict with migration stats
    """
    stats = {"migrated": False, "tokens": 0, "category": None, "had_tokens": False}

    with open(task_path) as f:
        data = yaml.safe_load(f)

    if not data or "task" not in data:
        return stats

    task = data["task"]

    # Check if already migrated
    if "estimated_tokens" in task and task["estimated_tokens"]:
        stats["had_tokens"] = True
        stats["tokens"] = task.get("estimated_tokens", 0)
        stats["category"] = task.get("size_category")
        return stats

    # Convert estimated_duration to estimated_tokens
    estimated_duration = task.get("estimated_duration", "")
    if estimated_duration:
        tokens = convert_time_to_tokens(estimated_duration)
    else:
        # Default to medium (20K) if no duration
        tokens = 20_000

    category = categorize_by_tokens(tokens)

    # Update task
    task["estimated_tokens"] = tokens
    task["size_category"] = category

    # Preserve original duration
    if "estimated_duration" in task:
        task["original_estimated_duration"] = task["estimated_duration"]

    stats["migrated"] = True
    stats["tokens"] = tokens
    stats["category"] = category

    if verbose:
        duration_str = estimated_duration or "none"
        print(f"  {task_path.name}: {duration_str} -> {tokens:,} tokens ({category})")

    if not dry_run:
        with open(task_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    return stats


def migrate_sprint_file(
    sprint_path: Path,
    task_tokens: dict,
    dry_run: bool = False,
    verbose: bool = False,
) -> dict:
    """Migrate a single sprint.yaml file.

    Args:
        sprint_path: Path to sprint.yaml
        task_tokens: Dict mapping task_id to estimated_tokens

    Returns:
        Dict with migration stats
    """
    stats = {"migrated": False, "total_tokens": 0}

    with open(sprint_path) as f:
        data = yaml.safe_load(f)

    if not data or "sprint" not in data:
        return stats

    sprint = data["sprint"]
    sprint_id = sprint.get("id", "")

    # Calculate total tokens for this sprint's tasks
    total_tokens = sum(
        tokens for task_id, tokens in task_tokens.items()
        if task_id.startswith(sprint_id)
    )

    # Ensure metadata exists
    if "metadata" not in sprint:
        sprint["metadata"] = {}

    # Update sprint metadata with token info
    if "estimated_tokens" not in sprint["metadata"] or not sprint["metadata"]["estimated_tokens"]:
        sprint["metadata"]["estimated_tokens"] = total_tokens
        stats["migrated"] = True

    stats["total_tokens"] = total_tokens

    if verbose:
        print(f"  {sprint_path.parent.name}: {total_tokens:,} total tokens")

    if not dry_run and stats["migrated"]:
        with open(sprint_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    return stats


def migrate_track_file(
    track_path: Path,
    sprint_tokens: dict,
    dry_run: bool = False,
    verbose: bool = False,
) -> dict:
    """Migrate a single track.yaml file.

    Args:
        track_path: Path to track.yaml
        sprint_tokens: Dict mapping sprint_id to total estimated_tokens

    Returns:
        Dict with migration stats
    """
    stats = {"migrated": False, "total_tokens": 0}

    with open(track_path) as f:
        data = yaml.safe_load(f)

    if not data or "track" not in data:
        return stats

    track = data["track"]
    track_id = track.get("id", "")

    # Calculate total tokens for this track's sprints
    total_tokens = sum(
        tokens for sprint_id, tokens in sprint_tokens.items()
        if sprint_id.startswith(track_id)
    )

    # Ensure metadata exists
    if "metadata" not in track:
        track["metadata"] = {}

    # Update track metadata with token info
    if "estimated_tokens" not in track["metadata"] or not track["metadata"]["estimated_tokens"]:
        track["metadata"]["estimated_tokens"] = total_tokens
        stats["migrated"] = True

    stats["total_tokens"] = total_tokens

    if verbose:
        print(f"  {track_path.parent.name}: {total_tokens:,} total tokens")

    if not dry_run and stats["migrated"]:
        with open(track_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    return stats


def main():
    parser = argparse.ArgumentParser(description="Migrate to token-based estimates")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without applying")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    roadmap_root = get_roadmap_root()

    if not roadmap_root.exists():
        print(f"Roadmap directory not found: {roadmap_root}")
        sys.exit(1)

    print("=" * 60)
    print("Token-Based Effort Estimation Migration")
    print("=" * 60)

    if args.dry_run:
        print("\n*** DRY RUN MODE - No changes will be made ***\n")

    # Phase 1: Migrate tasks
    print("\nPhase 1: Migrating tasks...")
    task_files = list(roadmap_root.glob("**/task.yaml"))
    task_tokens = {}  # task_id -> tokens
    tasks_migrated = 0
    tasks_already = 0
    size_distribution = {"S": 0, "M": 0, "L": 0, "XL": 0, "XXL": 0}

    for task_path in task_files:
        stats = migrate_task_file(task_path, args.dry_run, args.verbose)

        # Get task ID from the file
        try:
            with open(task_path) as f:
                data = yaml.safe_load(f)
                task_id = data.get("task", {}).get("id", "")
                if task_id:
                    task_tokens[task_id] = stats["tokens"]
        except:
            pass

        if stats["migrated"]:
            tasks_migrated += 1
        elif stats["had_tokens"]:
            tasks_already += 1

        if stats["category"]:
            size_distribution[stats["category"]] = size_distribution.get(stats["category"], 0) + 1

    print(f"  Tasks migrated: {tasks_migrated}")
    print(f"  Tasks already had tokens: {tasks_already}")
    print(f"  Total tasks: {len(task_files)}")
    print(f"  Size distribution: {size_distribution}")

    # Phase 2: Migrate sprints
    print("\nPhase 2: Migrating sprints...")
    sprint_files = list(roadmap_root.glob("*/*/sprint.yaml"))
    sprint_tokens = {}  # sprint_id -> total tokens
    sprints_migrated = 0

    for sprint_path in sprint_files:
        stats = migrate_sprint_file(sprint_path, task_tokens, args.dry_run, args.verbose)

        # Get sprint ID
        try:
            with open(sprint_path) as f:
                data = yaml.safe_load(f)
                sprint_id = data.get("sprint", {}).get("id", "")
                if sprint_id:
                    sprint_tokens[sprint_id] = stats["total_tokens"]
        except:
            pass

        if stats["migrated"]:
            sprints_migrated += 1

    print(f"  Sprints migrated: {sprints_migrated}")
    print(f"  Total sprints: {len(sprint_files)}")

    # Phase 3: Migrate tracks
    print("\nPhase 3: Migrating tracks...")
    track_files = list(roadmap_root.glob("*/track.yaml"))
    tracks_migrated = 0

    for track_path in track_files:
        stats = migrate_track_file(track_path, sprint_tokens, args.dry_run, args.verbose)
        if stats["migrated"]:
            tracks_migrated += 1

    print(f"  Tracks migrated: {tracks_migrated}")
    print(f"  Total tracks: {len(track_files)}")

    # Summary
    print("\n" + "=" * 60)
    print("Migration Summary")
    print("=" * 60)
    print(f"Total tokens estimated: {sum(task_tokens.values()):,}")
    print(f"Average per task: {sum(task_tokens.values()) // max(1, len(task_tokens)):,}")

    if args.dry_run:
        print("\n*** This was a dry run. Re-run without --dry-run to apply changes. ***")
    else:
        print("\nMigration complete!")


if __name__ == "__main__":
    main()
