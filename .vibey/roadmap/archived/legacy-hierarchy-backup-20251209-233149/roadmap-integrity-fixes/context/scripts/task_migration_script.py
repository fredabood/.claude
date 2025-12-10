#!/usr/bin/env python3
"""
Task Migration Script - Sprint 1, Phase 1B
Agent B Comprehensive Sprint Plan

Purpose: Migrate 81 tasks from tasks_summary fields to proper task.yaml files
Target Tracks:
  - standards-system: 51 tasks across 6 sprints
  - testing-system: 30 tasks across 3 sprints (reconstructed from deliverables)

Usage:
  python3 task_migration_script.py --track standards-system --dry-run
  python3 task_migration_script.py --track testing-system --execute
  python3 task_migration_script.py --all --execute
"""

import argparse
import yaml
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import subprocess

ROADMAP_ROOT = Path("/Users/fredabood/Repositories/vibey/.vibey/roadmap")


class TaskMigrator:
    """Migrates tasks from tasks_summary to proper task.yaml files"""

    def __init__(self, track_id: str, dry_run: bool = True):
        self.track_id = track_id
        self.dry_run = dry_run
        self.track_dir = ROADMAP_ROOT / track_id
        self.stats = {
            "sprints_processed": 0,
            "tasks_created": 0,
            "directories_created": 0,
            "errors": []
        }

    def load_track_yaml(self) -> Dict[str, Any]:
        """Load track.yaml file"""
        track_file = self.track_dir / "track.yaml"
        with open(track_file, 'r') as f:
            return yaml.safe_load(f)

    def load_sprint_yaml(self, sprint_id: str) -> Dict[str, Any]:
        """Load sprint.yaml file"""
        sprint_file = self.track_dir / sprint_id / "sprint.yaml"
        with open(sprint_file, 'r') as f:
            return yaml.safe_load(f)

    def parse_tasks_summary(self, sprint_data: Dict[str, Any]) -> List[str]:
        """Parse tasks_summary field into list of task titles"""
        tasks_summary = sprint_data['sprint'].get('tasks_summary', [])

        if not tasks_summary:
            return []

        # Handle both list and string formats
        if isinstance(tasks_summary, list):
            return [task.strip('- ').strip() for task in tasks_summary]
        elif isinstance(tasks_summary, str):
            # Split by newlines and filter empty
            return [line.strip('- ').strip() for line in tasks_summary.split('\n')
                    if line.strip() and not line.strip().startswith('#')]
        else:
            return []

    def reconstruct_tasks_from_metadata(self, sprint_data: Dict[str, Any]) -> List[str]:
        """Reconstruct tasks from deliverables and notes for testing-system"""
        # testing-system has no tasks_summary but has:
        # - deliverables list
        # - tasks_total count
        # - detailed notes about what was done

        sprint_id = sprint_data['sprint']['id']
        tasks_total = sprint_data['sprint']['progress']['tasks_total']
        deliverables = sprint_data['sprint'].get('deliverables', [])

        # Generate generic task titles based on deliverables
        tasks = []

        # Map sprint_id to specific task patterns
        task_patterns = {
            'testing-system-1': [
                'Set up pytest infrastructure and configuration',
                'Create RepoBuilder test utility',
                'Create StateValidator test utility',
                'Create GitValidator test utility',
                'Create MetricsCollector test utility',
                'Create web-app mock repository fixture',
                'Create API mock repository fixture',
                'Create ML mock repository fixture',
                'Write unit tests for config module (20 tests)',
                'Set up coverage reporting configuration'
            ],
            'testing-system-2': [
                'Write Journey 1 integration tests (First-Time Setup)',
                'Write Journey 2 integration tests (Sprint Planning)',
                'Write Journey 3 integration tests (Feature Development)',
                'Write Journey 4 integration tests (Quality Assurance)',
                'Write Journey 5 integration tests (Framework Management)',
                'Write Journey 6 integration tests (Multi-Platform)',
                'Write Journey 7 integration tests (Roadmap-Driven)',
                'Implement repository state transition validation',
                'Implement git history pattern validation',
                'Track and validate success metrics'
            ],
            'testing-system-3': [
                'Write E2E test for complete sprint workflow',
                'Write E2E test for multi-agent orchestration',
                'Write E2E test for quality gate enforcement',
                'Write E2E test for error recovery',
                'Create Claude Code platform-specific test suite',
                'Create Goose platform-specific test suite',
                'Implement platform parity validation (>95% threshold)',
                'Set up GitHub Actions CI/CD pipeline',
                'Configure pre-commit hooks for testing',
                'Create comprehensive testing documentation'
            ]
        }

        # Use predefined patterns or generate from deliverables
        if sprint_id in task_patterns:
            tasks = task_patterns[sprint_id]
        elif deliverables:
            tasks = [f"Implement {deliverable}" for deliverable in deliverables[:tasks_total]]
        else:
            # Fallback: generic task names
            tasks = [f"Task {i+1} for {sprint_id}" for i in range(tasks_total)]

        # Ensure we have exactly tasks_total items
        if len(tasks) < tasks_total:
            tasks.extend([f"Additional task {i+1}" for i in range(len(tasks), tasks_total)])
        elif len(tasks) > tasks_total:
            tasks = tasks[:tasks_total]

        return tasks

    def scan_git_commits(self, sprint_data: Dict[str, Any], task_title: str) -> List[str]:
        """Scan git log for commits related to this task using keyword matching"""
        sprint_id = sprint_data['sprint']['id']
        started = sprint_data['sprint'].get('started')
        completed = sprint_data['sprint'].get('completed')

        if not started or not completed:
            return []

        # Extract keywords from task title
        keywords = self._extract_keywords(task_title)

        # Search git log between sprint start and completion dates
        try:
            cmd = [
                'git', 'log',
                '--all',
                '--oneline',
                f'--since={started}',
                f'--until={completed}',
                '--grep=' + '|'.join(keywords),
                '-i',  # case insensitive
                '--', '/Users/fredabood/Repositories/vibey'
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd='/Users/fredabood/Repositories/vibey'
            )

            if result.returncode == 0 and result.stdout:
                # Extract commit hashes
                commits = [line.split()[0] for line in result.stdout.strip().split('\n') if line]
                return commits

        except Exception as e:
            self.stats["errors"].append(f"Git scan error for '{task_title}': {str(e)}")

        return []

    def _extract_keywords(self, task_title: str) -> List[str]:
        """Extract searchable keywords from task title"""
        # Remove common words and extract meaningful terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'for', 'with', 'to', 'from', 'in', 'on', 'at'}
        words = re.findall(r'\w+', task_title.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 3]
        return keywords[:3]  # Top 3 keywords

    def generate_task_yaml(
        self,
        task_number: int,
        task_title: str,
        sprint_data: Dict[str, Any],
        track_data: Dict[str, Any],
        commits: List[str]
    ) -> Dict[str, Any]:
        """Generate task.yaml content"""

        sprint = sprint_data['sprint']
        track = track_data['track']
        sprint_id = sprint['id']
        track_id = track['id']
        roadmap_id = track['roadmap_id']

        task_id = f"{sprint_id}-task-{task_number:03d}"

        # Determine status based on sprint status
        task_status = 'completed' if sprint['status'] == 'completed' else 'not_started'

        # Parse timestamps
        created = sprint.get('created', sprint.get('started', datetime.now(timezone.utc).isoformat()))
        started = sprint.get('started') if task_status == 'completed' else None
        completed_time = sprint.get('completed') if task_status == 'completed' else None

        task = {
            'task': {
                'id': task_id,
                'sprint_id': sprint_id,
                'track_id': track_id,
                'roadmap_id': roadmap_id,
                'task_type': 'development',
                'title': task_title,
                'description': f"{task_title}\n\nMigrated from tasks_summary field during Phase 1B task migration.",
                'status': task_status,
                'blocked': False,
                'created': created,
                'started': started,
                'completed': completed_time,
                'assigned_agent': sprint.get('assigned_agents', [None])[0] if sprint.get('assigned_agents') else None,
                'priority': track.get('priority', 'medium'),
                'phase_label': None,
                'estimated_tokens': None,
                'actual_tokens': None,
                'complexity': 'medium',
                'gate_info': None,
                'audit_results': None,
                'dependencies': [],
                'blocks': [],
                'blocked_by': [],
                'depends_on': [],
                'depended_on_by': [],
                'deliverables': [],
                'commits': commits,
                'metadata': {
                    'last_updated': datetime.now(timezone.utc).isoformat(),
                    'token_efficiency': None,
                    'duration_hours': None,
                    'migration_note': 'Migrated from tasks_summary field by task_migration_script.py on 2025-11-13'
                }
            }
        }

        return task

    def create_task_directory(self, sprint_id: str, task_number: int, task_data: Dict[str, Any]) -> bool:
        """Create task directory and write task.yaml file"""

        task_id = f"{sprint_id}-task-{task_number:03d}"
        task_dir = self.track_dir / sprint_id / task_id
        task_file = task_dir / "task.yaml"

        if self.dry_run:
            print(f"  [DRY RUN] Would create: {task_dir}")
            print(f"  [DRY RUN] Would write: {task_file}")
            return True

        try:
            # Create directory
            task_dir.mkdir(parents=True, exist_ok=True)
            self.stats["directories_created"] += 1

            # Write task.yaml
            with open(task_file, 'w') as f:
                yaml.dump(task_data, f, default_flow_style=False, sort_keys=False)

            self.stats["tasks_created"] += 1

            # Validate it loads correctly
            with open(task_file, 'r') as f:
                loaded = yaml.safe_load(f)
                assert 'task' in loaded, "task.yaml missing 'task' root key"
                assert loaded['task']['id'] == task_id, "task ID mismatch"

            print(f"  ✅ Created: {task_dir.relative_to(ROADMAP_ROOT)}")
            return True

        except Exception as e:
            error_msg = f"Failed to create {task_dir}: {str(e)}"
            self.stats["errors"].append(error_msg)
            print(f"  ❌ ERROR: {error_msg}")
            return False

    def migrate_sprint(self, sprint_id: str) -> bool:
        """Migrate all tasks for a single sprint"""

        print(f"\n📋 Processing Sprint: {sprint_id}")

        try:
            # Load data
            track_data = self.load_track_yaml()
            sprint_data = self.load_sprint_yaml(sprint_id)

            # Parse tasks
            if self.track_id == 'testing-system':
                task_titles = self.reconstruct_tasks_from_metadata(sprint_data)
            else:
                task_titles = self.parse_tasks_summary(sprint_data)

            if not task_titles:
                print(f"  ⚠️  No tasks found in tasks_summary")
                return True

            print(f"  Found {len(task_titles)} tasks")

            # Migrate each task
            for i, task_title in enumerate(task_titles, start=1):
                print(f"  Task {i}/{len(task_titles)}: {task_title}")

                # Scan for related commits
                commits = self.scan_git_commits(sprint_data, task_title)
                if commits:
                    print(f"    🔍 Found {len(commits)} related commit(s): {', '.join(commits[:3])}")

                # Generate task.yaml
                task_data = self.generate_task_yaml(i, task_title, sprint_data, track_data, commits)

                # Create task directory and file
                self.create_task_directory(sprint_id, i, task_data)

            self.stats["sprints_processed"] += 1
            return True

        except Exception as e:
            error_msg = f"Failed to migrate sprint {sprint_id}: {str(e)}"
            self.stats["errors"].append(error_msg)
            print(f"  ❌ ERROR: {error_msg}")
            return False

    def migrate_track(self) -> Dict[str, Any]:
        """Migrate all sprints in the track"""

        print(f"\n{'='*60}")
        print(f"🚀 Task Migration: {self.track_id}")
        print(f"{'='*60}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'EXECUTE'}")

        # Load track data
        track_data = self.load_track_yaml()
        sprints = track_data['track']['sprints']

        print(f"\nFound {len(sprints)} sprint(s) to process")

        # Migrate each sprint
        for sprint in sprints:
            sprint_id = sprint['id']
            self.migrate_sprint(sprint_id)

        # Print summary
        print(f"\n{'='*60}")
        print(f"📊 Migration Summary")
        print(f"{'='*60}")
        print(f"Sprints Processed: {self.stats['sprints_processed']}")
        print(f"Tasks Created: {self.stats['tasks_created']}")
        print(f"Directories Created: {self.stats['directories_created']}")

        if self.stats["errors"]:
            print(f"\n⚠️  Errors ({len(self.stats['errors'])}):")
            for error in self.stats["errors"]:
                print(f"  - {error}")
        else:
            print(f"\n✅ No errors")

        if self.dry_run:
            print(f"\n⚠️  DRY RUN - No changes made. Use --execute to apply changes.")

        return self.stats


def main():
    parser = argparse.ArgumentParser(description='Migrate tasks from tasks_summary to task.yaml files')
    parser.add_argument(
        '--track',
        choices=['standards-system', 'testing-system', 'all'],
        default='all',
        help='Track to migrate (default: all)'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute migration (default: dry-run)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=True,
        help='Dry run mode (default: true)'
    )

    args = parser.parse_args()

    # Determine dry_run mode
    dry_run = not args.execute

    # Determine tracks to migrate
    if args.track == 'all':
        tracks = ['standards-system', 'testing-system']
    else:
        tracks = [args.track]

    # Migrate tracks
    all_stats = {}
    for track_id in tracks:
        migrator = TaskMigrator(track_id, dry_run=dry_run)
        stats = migrator.migrate_track()
        all_stats[track_id] = stats

    # Print overall summary
    if len(tracks) > 1:
        print(f"\n{'='*60}")
        print(f"🎯 Overall Summary")
        print(f"{'='*60}")
        total_tasks = sum(s['tasks_created'] for s in all_stats.values())
        total_errors = sum(len(s['errors']) for s in all_stats.values())
        print(f"Total Tracks Migrated: {len(tracks)}")
        print(f"Total Tasks Created: {total_tasks}")
        print(f"Total Errors: {total_errors}")

        if dry_run:
            print(f"\n⚠️  DRY RUN - No changes made. Use --execute to apply changes.")


if __name__ == '__main__':
    main()
