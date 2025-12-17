#!/usr/bin/env python3
"""
Migrate roadmap objects to dependency cache v2.0.

This script populates the new dependency tracking fields:
- depends_on: Cached dependency status for O(1) blocking checks
- depended_on_by: Reverse index for O(1) update propagation
- blocked: Recomputed from depends_on

Usage:
    python3 migrate-dependency-cache.py [roadmap-id]

    If roadmap-id not provided, uses .vibey/roadmap.yaml
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
from typing import List, Dict, Tuple

# Add framework to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from roadmap.models import (
    Task, Sprint, Track, DependencyStatus
)
from roadmap.serialization.yaml_loader import load_roadmap, load_track, load_sprint, load_task
from roadmap.serialization.yaml_dumper import save_track, save_sprint, save_tasks


class FileSystem:
    """Simple filesystem helper for roadmap paths."""

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)

    def get_task_path(self, task_id: str) -> Path:
        return self.base_dir / "tasks" / f"{task_id}.yaml"

    def get_sprint_path(self, sprint_id: str) -> Path:
        return self.base_dir / "sprints" / f"{sprint_id}.yaml"

    def get_track_path(self, track_id: str) -> Path:
        return self.base_dir / "tracks" / f"{track_id}.yaml"


class DependencyMigrator:
    """Migrates roadmap objects to dependency cache v2.0."""

    def __init__(self, fs: FileSystem):
        self.fs = fs
        self.object_status_cache: Dict[str, str] = {}
        self.reverse_index: Dict[str, List[str]] = defaultdict(list)

    def get_object_status(self, object_id: str, object_type: str) -> str:
        """
        Get current status of any roadmap object.

        Args:
            object_id: The object's ID
            object_type: task/sprint/track

        Returns:
            Current status as string
        """
        # Check cache first
        if object_id in self.object_status_cache:
            return self.object_status_cache[object_id]

        # Load object and get status
        try:
            if object_type == "task":
                task_path = self.fs.get_task_path(object_id)
                if task_path.exists():
                    task = load_task(task_path)
                    status = task.status.value
                else:
                    status = "not_started"

            elif object_type == "sprint":
                sprint_path = self.fs.get_sprint_path(object_id)
                if sprint_path.exists():
                    sprint = load_sprint(sprint_path)
                    status = sprint.status.value
                else:
                    status = "not_started"

            elif object_type == "track":
                track_path = self.fs.get_track_path(object_id)
                if track_path.exists():
                    track = load_track(track_path)
                    status = track.status.value
                else:
                    status = "not_started"

            elif object_type == "external":
                # External dependencies default to not_started
                status = "not_started"

            else:
                print(f"⚠️  Unknown object type: {object_type}")
                status = "not_started"

            # Cache result
            self.object_status_cache[object_id] = status
            return status

        except Exception as e:
            print(f"⚠️  Error loading {object_type} {object_id}: {e}")
            return "not_started"

    def migrate_task(self, task: Task) -> Tuple[Task, bool]:
        """
        Migrate a task to dependency cache v2.0.

        Args:
            task: Task to migrate

        Returns:
            (updated_task, was_modified)
        """
        modified = False

        # Build depends_on from dependencies
        new_depends_on = []
        for dep in task.dependencies:
            # Get current status of blocker
            current_status = self.get_object_status(dep.target_id, dep.type.value)

            # Determine what status this blocks
            # Default: blocks in_progress (hard blocker)
            blocks_transition_to = "in_progress"

            # If dependency reason mentions "complete" or "finish", it's a soft blocker
            reason_lower = dep.reason.lower()
            if any(word in reason_lower for word in ["complete", "finish", "done", "ready"]):
                blocks_transition_to = "completed"

            dep_status = DependencyStatus(
                blocker_id=dep.target_id,
                blocker_type=dep.type.value,
                required_status=dep.target_status,
                current_status=current_status,
                blocks_transition_to=blocks_transition_to,
                last_checked=datetime.now(timezone.utc)
            )
            new_depends_on.append(dep_status)

            # Build reverse index
            self.reverse_index[dep.target_id].append(task.id)

        # Update depends_on if changed
        if new_depends_on != task.depends_on:
            task.depends_on = new_depends_on
            modified = True

        # Recompute blocked status
        new_blocked = any(not dep.is_satisfied() for dep in task.depends_on)
        if new_blocked != task.blocked:
            task.blocked = new_blocked
            modified = True

        return task, modified

    def migrate_sprint(self, sprint: Sprint) -> Tuple[Sprint, bool]:
        """
        Migrate a sprint to dependency cache v2.0.

        Args:
            sprint: Sprint to migrate

        Returns:
            (updated_sprint, was_modified)
        """
        modified = False

        # Build depends_on from development_gates (Sprint uses development_gates not dependencies)
        new_depends_on = []
        for dep in sprint.development_gates:
            # Get current status of blocker
            current_status = self.get_object_status(dep.target_id, dep.type.value)

            # Determine what status this blocks
            # Sprint dependencies typically block completion
            blocks_transition_to = "completed"

            # If dependency mentions "start", it's a hard blocker
            reason_lower = dep.reason.lower()
            if any(word in reason_lower for word in ["start", "begin", "initialize"]):
                blocks_transition_to = "in_progress"
            # If dependency mentions "production", it blocks production_ready
            elif any(word in reason_lower for word in ["production", "deploy", "release"]):
                blocks_transition_to = "production_ready"

            dep_status = DependencyStatus(
                blocker_id=dep.target_id,
                blocker_type=dep.type.value,
                required_status=dep.target_status,
                current_status=current_status,
                blocks_transition_to=blocks_transition_to,
                last_checked=datetime.now(timezone.utc)
            )
            new_depends_on.append(dep_status)

            # Build reverse index
            self.reverse_index[dep.target_id].append(sprint.id)

        # Update depends_on if changed
        if new_depends_on != sprint.depends_on:
            sprint.depends_on = new_depends_on
            modified = True

        # Recompute blocked status
        new_blocked = any(not dep.is_satisfied() for dep in sprint.depends_on)
        if new_blocked != sprint.blocked:
            sprint.blocked = new_blocked
            modified = True

        return sprint, modified

    def migrate_track(self, track: Track) -> Tuple[Track, bool]:
        """
        Migrate a track to dependency cache v2.0.

        Args:
            track: Track to migrate

        Returns:
            (updated_track, was_modified)
        """
        modified = False

        # Build depends_on from dependencies
        new_depends_on = []
        for dep in track.dependencies:
            # Get current status of blocker
            current_status = self.get_object_status(dep.target_id, dep.type.value)

            # Determine what status this blocks
            # Track dependencies typically block completion
            blocks_transition_to = "completed"

            # If dependency mentions "start", it's a hard blocker
            reason_lower = dep.reason.lower()
            if any(word in reason_lower for word in ["start", "begin", "initialize"]):
                blocks_transition_to = "in_progress"
            # If dependency mentions "production", it blocks production_ready
            elif any(word in reason_lower for word in ["production", "deploy", "release"]):
                blocks_transition_to = "production_ready"

            dep_status = DependencyStatus(
                blocker_id=dep.target_id,
                blocker_type=dep.type.value,
                required_status=dep.target_status,
                current_status=current_status,
                blocks_transition_to=blocks_transition_to,
                last_checked=datetime.now(timezone.utc)
            )
            new_depends_on.append(dep_status)

            # Build reverse index
            self.reverse_index[dep.target_id].append(track.id)

        # Update depends_on if changed
        if new_depends_on != track.depends_on:
            track.depends_on = new_depends_on
            modified = True

        # Recompute blocked status
        new_blocked = any(not dep.is_satisfied() for dep in track.depends_on)
        if new_blocked != track.blocked:
            track.blocked = new_blocked
            modified = True

        return track, modified

    def apply_reverse_index(self, tasks: List[Task], sprints: List[Sprint], tracks: List[Track]) -> Tuple[int, int, int]:
        """
        Apply reverse index (depended_on_by) to all objects.

        Returns:
            (tasks_modified, sprints_modified, tracks_modified)
        """
        tasks_modified = 0
        sprints_modified = 0
        tracks_modified = 0

        # Update tasks
        for task in tasks:
            new_depended_on_by = self.reverse_index.get(task.id, [])
            if new_depended_on_by != task.depended_on_by:
                task.depended_on_by = new_depended_on_by
                tasks_modified += 1

        # Update sprints
        for sprint in sprints:
            new_depended_on_by = self.reverse_index.get(sprint.id, [])
            if new_depended_on_by != sprint.depended_on_by:
                sprint.depended_on_by = new_depended_on_by
                sprints_modified += 1

        # Update tracks
        for track in tracks:
            new_depended_on_by = self.reverse_index.get(track.id, [])
            if new_depended_on_by != track.depended_on_by:
                track.depended_on_by = new_depended_on_by
                tracks_modified += 1

        return tasks_modified, sprints_modified, tracks_modified

    def migrate_roadmap(self, roadmap_path: Path, dry_run: bool = False) -> None:
        """
        Migrate entire roadmap to dependency cache v2.0.

        Args:
            roadmap_path: Path to roadmap.yaml
            dry_run: If True, don't save changes
        """
        print(f"🔄 Migrating roadmap: {roadmap_path}")
        print()

        # Load roadmap
        roadmap = load_roadmap(roadmap_path)
        print(f"📋 Roadmap: {roadmap.id} - {roadmap.name}")
        print()

        # Collect all objects
        all_tasks = []
        all_sprints = []
        all_tracks = []

        # Load tracks
        for track_summary in roadmap.tracks:
            track_path = self.fs.get_track_path(track_summary.id)
            if not track_path.exists():
                print(f"⚠️  Track file not found: {track_path}")
                continue

            track = load_track(track_path)
            all_tracks.append(track)

            # Load sprints
            for sprint_summary in track.sprints:
                sprint_path = self.fs.get_sprint_path(sprint_summary.id)
                if not sprint_path.exists():
                    print(f"⚠️  Sprint file not found: {sprint_path}")
                    continue

                sprint = load_sprint(sprint_path)
                all_sprints.append(sprint)

                # Load tasks
                for task_summary in sprint.tasks:
                    task_path = self.fs.get_task_path(task_summary.id)
                    if not task_path.exists():
                        print(f"⚠️  Task file not found: {task_path}")
                        continue

                    task = load_task(task_path)
                    all_tasks.append(task)

        print(f"📊 Found {len(all_tasks)} tasks, {len(all_sprints)} sprints, {len(all_tracks)} tracks")
        print()

        # Phase 1: Migrate depends_on for all objects
        print("Phase 1: Building dependency caches...")

        tasks_modified = 0
        for task in all_tasks:
            task, modified = self.migrate_task(task)
            if modified:
                tasks_modified += 1

        sprints_modified = 0
        for sprint in all_sprints:
            sprint, modified = self.migrate_sprint(sprint)
            if modified:
                sprints_modified += 1

        tracks_modified = 0
        for track in all_tracks:
            track, modified = self.migrate_track(track)
            if modified:
                tracks_modified += 1

        print(f"  ✓ Tasks:   {tasks_modified}/{len(all_tasks)} modified")
        print(f"  ✓ Sprints: {sprints_modified}/{len(all_sprints)} modified")
        print(f"  ✓ Tracks:  {tracks_modified}/{len(all_tracks)} modified")
        print()

        # Phase 2: Apply reverse index (depended_on_by)
        print("Phase 2: Building reverse index...")

        reverse_tasks, reverse_sprints, reverse_tracks = self.apply_reverse_index(
            all_tasks, all_sprints, all_tracks
        )

        print(f"  ✓ Tasks:   {reverse_tasks} have dependents")
        print(f"  ✓ Sprints: {reverse_sprints} have dependents")
        print(f"  ✓ Tracks:  {reverse_tracks} have dependents")
        print()

        # Phase 3: Save changes
        if dry_run:
            print("🔍 Dry run - no changes saved")
            return

        print("Phase 3: Saving changes...")

        saved_tasks = 0
        for task in all_tasks:
            try:
                task_path = self.fs.get_task_path(task.id)
                # Save task individually using save_tasks with single-item list
                save_tasks([task], task_path)
                saved_tasks += 1
            except Exception as e:
                print(f"  ❌ Error saving task {task.id}: {e}")

        saved_sprints = 0
        for sprint in all_sprints:
            try:
                sprint_path = self.fs.get_sprint_path(sprint.id)
                save_sprint(sprint, sprint_path)
                saved_sprints += 1
            except Exception as e:
                print(f"  ❌ Error saving sprint {sprint.id}: {e}")

        saved_tracks = 0
        for track in all_tracks:
            try:
                track_path = self.fs.get_track_path(track.id)
                save_track(track, track_path)
                saved_tracks += 1
            except Exception as e:
                print(f"  ❌ Error saving track {track.id}: {e}")

        print(f"  ✓ Saved {saved_tasks} tasks")
        print(f"  ✓ Saved {saved_sprints} sprints")
        print(f"  ✓ Saved {saved_tracks} tracks")
        print()

        print("✅ Migration complete!")
        print()

        # Summary
        total_objects = len(all_tasks) + len(all_sprints) + len(all_tracks)
        total_modified = tasks_modified + sprints_modified + tracks_modified + reverse_tasks + reverse_sprints + reverse_tracks

        print(f"📊 Summary:")
        print(f"  Total objects: {total_objects}")
        print(f"  Modified: {total_modified}")
        print(f"  Reverse index entries: {len(self.reverse_index)}")


def main():
    parser = argparse.ArgumentParser(description="Migrate roadmap to dependency cache v2.0")
    parser.add_argument("roadmap_id", nargs="?", help="Roadmap ID (default: .vibey/roadmap.yaml)")
    parser.add_argument("--dry-run", action="store_true", help="Don't save changes, just show what would happen")
    parser.add_argument("--roadmap-dir", default=".vibey", help="Roadmap directory (default: .vibey)")

    args = parser.parse_args()

    # Determine roadmap path
    if args.roadmap_id:
        roadmap_path = Path(args.roadmap_dir) / f"{args.roadmap_id}.yaml"
    else:
        roadmap_path = Path(args.roadmap_dir) / "roadmap.yaml"

    if not roadmap_path.exists():
        print(f"❌ Roadmap not found: {roadmap_path}")
        sys.exit(1)

    # Create filesystem
    fs = FileSystem(Path(args.roadmap_dir))

    # Migrate
    migrator = DependencyMigrator(fs)
    migrator.migrate_roadmap(roadmap_path, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
