#!/usr/bin/env python3
"""
Comprehensive Roadmap State Audit Script

Validates roadmap integrity, progress calculations, track consistency,
sprint/task relationships, and metadata accuracy.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Tuple
from collections import Counter

class RoadmapAuditor:
    def __init__(self, roadmap_path: Path):
        self.roadmap_path = roadmap_path
        self.roadmap_dir = roadmap_path.parent
        self.errors = []
        self.warnings = []
        self.info = []

    def load_yaml(self, file_path: Path) -> dict:
        """Load and parse YAML file."""
        try:
            with open(file_path) as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.errors.append(f"Failed to load {file_path}: {e}")
            return {}

    def audit_roadmap_structure(self) -> Dict:
        """Audit main roadmap.yaml structure."""
        print("📋 Auditing roadmap.yaml structure...")

        roadmap_data = self.load_yaml(self.roadmap_path)
        if not roadmap_data:
            return {}

        roadmap = roadmap_data.get('roadmap', {})

        # Check required fields
        required_fields = ['id', 'name', 'version', 'status', 'progress', 'tracks']
        missing_fields = [f for f in required_fields if f not in roadmap]

        if missing_fields:
            self.errors.append(f"Missing required fields in roadmap: {missing_fields}")

        # Validate progress structure
        progress = roadmap.get('progress', {})
        progress_fields = ['tracks_total', 'tracks_completed', 'sprints_total',
                          'sprints_completed', 'tasks_total', 'tasks_completed']

        missing_progress = [f for f in progress_fields if f not in progress]
        if missing_progress:
            self.errors.append(f"Missing progress fields: {missing_progress}")

        self.info.append(f"✅ Roadmap ID: {roadmap.get('id')}")
        self.info.append(f"✅ Version: {roadmap.get('version')}")
        self.info.append(f"✅ Status: {roadmap.get('status')}")

        return roadmap

    def audit_track_files(self, roadmap: Dict) -> Dict[str, Dict]:
        """Audit all track files and compare with roadmap."""
        print("\n🛤️  Auditing track files...")

        # Get tracks from roadmap
        roadmap_tracks = {t['id']: t for t in roadmap.get('tracks', [])}
        self.info.append(f"Tracks in roadmap.yaml: {len(roadmap_tracks)}")

        # Find all track files (they're in .vibey/roadmap/*/track.yaml)
        tracks_base = self.roadmap_dir / 'roadmap'
        track_files = list(tracks_base.glob('*/track.yaml')) if tracks_base.exists() else []
        self.info.append(f"Track files found: {len(track_files)}")

        track_data = {}
        for track_file in track_files:
            track_id = track_file.parent.name
            data = self.load_yaml(track_file)
            track_info = data.get('track', {})
            track_data[track_id] = track_info

            # Check if track is in roadmap
            if track_id not in roadmap_tracks:
                self.warnings.append(f"Track '{track_id}' has file but not in roadmap.yaml")
            else:
                # Validate status consistency
                roadmap_status = roadmap_tracks[track_id].get('status')
                file_status = track_info.get('status')

                if roadmap_status != file_status:
                    self.errors.append(
                        f"Track '{track_id}' status mismatch: "
                        f"roadmap.yaml='{roadmap_status}' vs file='{file_status}'"
                    )

        # Check for tracks in roadmap but no file
        for track_id in roadmap_tracks:
            if track_id not in track_data:
                self.warnings.append(f"Track '{track_id}' in roadmap.yaml but no file found")

        return track_data

    def audit_sprint_files(self, track_data: Dict) -> Dict[str, Dict]:
        """Audit all sprint files."""
        print("\n🏃 Auditing sprint files...")

        sprint_data = {}
        total_sprints = 0
        completed_sprints = 0

        for track_id, track_info in track_data.items():
            track_dir = self.roadmap_dir / 'roadmap' / track_id
            sprint_files = list(track_dir.glob('*/sprint.yaml'))
            total_sprints += len(sprint_files)

            for sprint_file in sprint_files:
                sprint_id = sprint_file.parent.name
                data = self.load_yaml(sprint_file)
                sprint_info = data.get('sprint', {})
                sprint_data[sprint_id] = sprint_info

                # Check sprint belongs to correct track
                file_track_id = sprint_info.get('track_id')
                if file_track_id != track_id:
                    self.errors.append(
                        f"Sprint '{sprint_id}' track_id mismatch: "
                        f"directory='{track_id}' vs file='{file_track_id}'"
                    )

                # Count completed sprints
                if sprint_info.get('status') == 'completed':
                    completed_sprints += 1

        self.info.append(f"Total sprint files: {total_sprints}")
        self.info.append(f"Completed sprints: {completed_sprints}")

        return sprint_data

    def audit_task_files(self, sprint_data: Dict) -> Dict[str, Dict]:
        """Audit all task files."""
        print("\n📋 Auditing task files...")

        task_data = {}
        total_tasks = 0
        completed_tasks = 0

        for sprint_id, sprint_info in sprint_data.items():
            sprint_track = sprint_info.get('track_id')
            sprint_dir = self.roadmap_dir / 'roadmap' / sprint_track / sprint_id
            task_files = list(sprint_dir.glob('*/task.yaml'))
            total_tasks += len(task_files)

            for task_file in task_files:
                task_id = task_file.parent.name
                data = self.load_yaml(task_file)
                task_info = data.get('task', {})
                task_data[task_id] = task_info

                # Check task belongs to correct sprint
                file_sprint_id = task_info.get('sprint_id')
                if file_sprint_id != sprint_id:
                    self.errors.append(
                        f"Task '{task_id}' sprint_id mismatch: "
                        f"directory='{sprint_id}' vs file='{file_sprint_id}'"
                    )

                # Count completed tasks
                if task_info.get('status') == 'completed':
                    completed_tasks += 1

        self.info.append(f"Total task files: {total_tasks}")
        self.info.append(f"Completed tasks: {completed_tasks}")

        return task_data

    def audit_progress_calculations(self, roadmap: Dict, track_data: Dict,
                                   sprint_data: Dict, task_data: Dict):
        """Verify progress calculations are accurate."""
        print("\n📊 Auditing progress calculations...")

        progress = roadmap.get('progress', {})

        # Count actual tracks
        actual_tracks_total = len(track_data)
        actual_tracks_completed = sum(1 for t in track_data.values()
                                     if t.get('status') == 'completed')

        # Count actual sprints
        actual_sprints_total = len(sprint_data)
        actual_sprints_completed = sum(1 for s in sprint_data.values()
                                      if s.get('status') == 'completed')

        # Count actual tasks
        actual_tasks_total = len(task_data)
        actual_tasks_completed = sum(1 for t in task_data.values()
                                    if t.get('status') == 'completed')

        # Compare with roadmap progress
        checks = [
            ('tracks_total', progress.get('tracks_total'), actual_tracks_total),
            ('tracks_completed', progress.get('tracks_completed'), actual_tracks_completed),
            ('sprints_total', progress.get('sprints_total'), actual_sprints_total),
            ('sprints_completed', progress.get('sprints_completed'), actual_sprints_completed),
            ('tasks_total', progress.get('tasks_total'), actual_tasks_total),
            ('tasks_completed', progress.get('tasks_completed'), actual_tasks_completed),
        ]

        for field, reported, actual in checks:
            if reported != actual:
                self.errors.append(
                    f"Progress mismatch for '{field}': "
                    f"roadmap={reported}, actual={actual}"
                )
            else:
                self.info.append(f"✅ {field}: {reported} (verified)")

    def audit_dependencies(self, track_data: Dict):
        """Check track dependencies and blocking relationships."""
        print("\n🔗 Auditing dependencies...")

        track_ids = set(track_data.keys())

        for track_id, track_info in track_data.items():
            dependencies = track_info.get('dependencies', [])
            # Handle case where dependencies might be a dict
            if isinstance(dependencies, dict):
                dependencies = []

            for dep in dependencies:
                # Dependencies are structured objects
                if isinstance(dep, dict):
                    dep_target = dep.get('target_id')
                    dep_type = dep.get('type')

                    if dep_type == 'track':
                        # Check if dependency exists
                        if dep_target not in track_ids:
                            self.errors.append(
                                f"Track '{track_id}' depends on non-existent track '{dep_target}'"
                            )

                        # Check if dependency is completed
                        if dep_target in track_data:
                            dep_status = track_data[dep_target].get('status')
                            track_status = track_info.get('status')
                            required_status = dep.get('target_status', 'completed')

                            if track_status == 'completed' and dep_status != required_status:
                                self.warnings.append(
                                    f"Track '{track_id}' is completed but dependency '{dep_target}' "
                                    f"is '{dep_status}' (expected: '{required_status}')"
                                )
                else:
                    # Old format: simple string
                    if dep not in track_ids:
                        self.errors.append(
                            f"Track '{track_id}' depends on non-existent track '{dep}'"
                        )

    def audit_platform_tracking(self, task_data: Dict):
        """Audit platform tracking in commits."""
        print("\n🖥️  Auditing platform tracking...")

        tasks_with_commits = 0
        commits_without_platform = []
        commits_without_timestamp = []
        platform_usage = Counter()

        for task_id, task_info in task_data.items():
            commits = task_info.get('commits', [])
            if commits:
                tasks_with_commits += 1

                for commit in commits:
                    # Check platform field
                    if 'platform' not in commit:
                        commits_without_platform.append((task_id, commit.get('sha', 'unknown')))
                    else:
                        platform_usage[commit['platform']] += 1

                    # Check submitted_at field
                    if 'submitted_at' not in commit:
                        commits_without_timestamp.append((task_id, commit.get('sha', 'unknown')))

        self.info.append(f"Tasks with commits: {tasks_with_commits}")
        self.info.append(f"Platform usage: {dict(platform_usage)}")

        if commits_without_platform:
            self.warnings.append(
                f"Found {len(commits_without_platform)} commits without platform field "
                f"(legacy commits, will be skipped on load)"
            )

        if commits_without_timestamp:
            self.warnings.append(
                f"Found {len(commits_without_timestamp)} commits without submitted_at "
                f"(legacy commits)"
            )

    def generate_report(self) -> str:
        """Generate final audit report."""
        report = []
        report.append("=" * 80)
        report.append("ROADMAP STATE AUDIT REPORT")
        report.append("=" * 80)
        report.append("")

        # Summary
        report.append("📊 AUDIT SUMMARY")
        report.append("-" * 80)
        report.append(f"❌ Errors:   {len(self.errors)}")
        report.append(f"⚠️  Warnings: {len(self.warnings)}")
        report.append(f"ℹ️  Info:     {len(self.info)}")
        report.append("")

        # Errors
        if self.errors:
            report.append("❌ ERRORS (Critical Issues)")
            report.append("-" * 80)
            for error in self.errors:
                report.append(f"  • {error}")
            report.append("")
        else:
            report.append("✅ NO ERRORS FOUND")
            report.append("")

        # Warnings
        if self.warnings:
            report.append("⚠️  WARNINGS (Non-Critical Issues)")
            report.append("-" * 80)
            for warning in self.warnings:
                report.append(f"  • {warning}")
            report.append("")

        # Info
        if self.info:
            report.append("ℹ️  INFORMATION")
            report.append("-" * 80)
            for info in self.info:
                report.append(f"  {info}")
            report.append("")

        # Final verdict
        report.append("=" * 80)
        if not self.errors:
            report.append("✅ AUDIT PASSED - Roadmap state is consistent")
        else:
            report.append("❌ AUDIT FAILED - Critical issues found")
        report.append("=" * 80)

        return "\n".join(report)

    def run_full_audit(self):
        """Run complete audit."""
        print("\n🔍 Starting Comprehensive Roadmap Audit...")
        print("=" * 80)

        # Load and audit roadmap
        roadmap = self.audit_roadmap_structure()
        if not roadmap:
            print("\n❌ Failed to load roadmap.yaml - aborting audit")
            return

        # Audit tracks
        track_data = self.audit_track_files(roadmap)

        # Audit sprints
        sprint_data = self.audit_sprint_files(track_data)

        # Audit tasks
        task_data = self.audit_task_files(sprint_data)

        # Audit progress calculations
        self.audit_progress_calculations(roadmap, track_data, sprint_data, task_data)

        # Audit dependencies
        self.audit_dependencies(track_data)

        # Audit platform tracking
        self.audit_platform_tracking(task_data)

        # Generate and print report
        print("\n")
        print(self.generate_report())

        return len(self.errors) == 0


if __name__ == '__main__':
    roadmap_path = Path('.vibey/roadmap.yaml')

    if not roadmap_path.exists():
        print(f"❌ Roadmap file not found: {roadmap_path}")
        exit(1)

    auditor = RoadmapAuditor(roadmap_path)
    success = auditor.run_full_audit()

    exit(0 if success else 1)
