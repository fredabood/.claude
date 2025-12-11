"""
Markdown Generator - Generate human-readable markdown views from YAML

This module generates markdown documentation from YAML roadmap files at each
level of the hierarchy (roadmap, track, sprint, task). Markdown files are
generated views of the source YAML data.

Key Features:
- Generate markdown from YAML (single source of truth)
- Human-readable formatting
- Progress indicators and status
- Links to related objects
- Context file listings
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class MarkdownGenerator:
    """Generates markdown documentation from roadmap YAML files."""

    def __init__(self, roadmap_root: str = ".vibey/roadmap"):
        """
        Initialize markdown generator.

        Args:
            roadmap_root: Root directory for roadmap hierarchy
        """
        self.roadmap_root = Path(roadmap_root)

    def _format_status(self, status: str) -> str:
        """Format status with emoji."""
        status_map = {
            'not_started': '⚪ Not Started',
            'in_progress': '🔵 In Progress',
            'paused': '⏸️  Paused',
            'blocked': '❌ Blocked',
            'completed': '✅ Completed',
            'production_ready': '🚀 Production Ready',
            'deployed': '🌟 Deployed',
        }
        return status_map.get(status, status)

    def _format_priority(self, priority: str) -> str:
        """Format priority with emoji."""
        priority_map = {
            'critical': '🔴 Critical',
            'high': '🟠 High',
            'medium': '🟡 Medium',
            'low': '🟢 Low',
        }
        return priority_map.get(priority, priority)

    def _format_date(self, date_str: Optional[str]) -> str:
        """Format ISO date string."""
        if not date_str:
            return 'Not set'
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M UTC')
        except:
            return date_str

    def generate_roadmap_markdown(self, roadmap_yaml_path: str) -> str:
        """
        Generate markdown view for roadmap root.

        Args:
            roadmap_yaml_path: Path to roadmap.yaml

        Returns:
            Markdown content as string
        """
        with open(roadmap_yaml_path) as f:
            data = yaml.safe_load(f)

        roadmap = data.get('roadmap', {})

        md = []
        md.append(f"# {roadmap.get('name', 'Roadmap')}")
        md.append("")
        md.append(f"**ID:** `{roadmap.get('id', 'unknown')}`  ")
        md.append(f"**Version:** {roadmap.get('version', '0.1.0')}  ")
        md.append(f"**Status:** {self._format_status(roadmap.get('status', 'not_started'))}  ")
        md.append("")

        # Description
        if 'metadata' in roadmap and 'description' in roadmap['metadata']:
            md.append("## Description")
            md.append("")
            md.append(roadmap['metadata']['description'])
            md.append("")

        # Progress
        if 'progress' in roadmap:
            progress = roadmap['progress']
            md.append("## Progress")
            md.append("")
            md.append(f"- **Tracks:** {progress.get('tracks_completed', 0)}/{progress.get('tracks_total', 0)} completed")
            md.append(f"- **Sprints:** {progress.get('sprints_completed', 0)}/{progress.get('sprints_total', 0)} completed")
            md.append(f"- **Tasks:** {progress.get('tasks_completed', 0)}/{progress.get('tasks_total', 0)} completed")
            md.append(f"- **Overall:** {progress.get('completion_percent', 0)}% complete")
            md.append("")

        # Tracks
        if 'tracks' in roadmap:
            md.append("## Tracks")
            md.append("")
            for track in roadmap['tracks']:
                track_id = track.get('id')
                track_name = track.get('name', track_id)
                track_status = track.get('status', 'not_started')
                track_priority = track.get('priority', 'medium')

                md.append(f"### {track_name}")
                md.append(f"- **ID:** `{track_id}`")
                md.append(f"- **Status:** {self._format_status(track_status)}")
                md.append(f"- **Priority:** {self._format_priority(track_priority)}")
                md.append("")

        # Timeline
        md.append("## Timeline")
        md.append("")
        md.append(f"- **Created:** {self._format_date(roadmap.get('created'))}")
        md.append(f"- **Started:** {self._format_date(roadmap.get('started'))}")
        if roadmap.get('target_completion'):
            md.append(f"- **Target Completion:** {self._format_date(roadmap.get('target_completion'))}")
        if roadmap.get('completed'):
            md.append(f"- **Completed:** {self._format_date(roadmap.get('completed'))}")
        md.append("")

        # Footer
        md.append("---")
        md.append("")
        md.append(f"*Generated from roadmap.yaml on {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*")
        md.append("")

        return '\n'.join(md)

    def generate_track_markdown(self, track_yaml_path: str) -> str:
        """
        Generate markdown view for a track.

        Args:
            track_yaml_path: Path to track.yaml

        Returns:
            Markdown content as string
        """
        with open(track_yaml_path) as f:
            data = yaml.safe_load(f)

        track = data.get('track', {})
        track_dir = Path(track_yaml_path).parent

        md = []
        md.append(f"# {track.get('name', 'Track')}")
        md.append("")
        md.append(f"**ID:** `{track.get('id', 'unknown')}`  ")
        md.append(f"**Status:** {self._format_status(track.get('status', 'not_started'))}  ")
        md.append(f"**Priority:** {self._format_priority(track.get('priority', 'medium'))}  ")
        md.append("")

        # Description
        if 'description' in track:
            md.append("## Description")
            md.append("")
            md.append(track['description'])
            md.append("")

        # Progress
        if 'progress' in track:
            progress = track['progress']
            md.append("## Progress")
            md.append("")
            md.append(f"- **Sprints:** {progress.get('sprints_completed', 0)}/{progress.get('sprints_total', 0)} completed")
            md.append(f"- **Tasks:** {progress.get('tasks_completed', 0)}/{progress.get('tasks_total', 0)} completed")
            md.append(f"- **Overall:** {progress.get('completion_percent', 0)}% complete")
            md.append("")

        # Sprints
        if 'sprints' in track:
            md.append("## Sprints")
            md.append("")
            for sprint in track['sprints']:
                sprint_id = sprint.get('id')
                sprint_name = sprint.get('name', sprint_id)
                sprint_status = sprint.get('status', 'not_started')

                md.append(f"### {sprint_name}")
                md.append(f"- **ID:** `{sprint_id}`")
                md.append(f"- **Status:** {self._format_status(sprint_status)}")
                md.append("")

        # Context files
        context_dir = track_dir / 'context'
        if context_dir.exists():
            context_files = sorted(context_dir.glob('*.md'))
            if context_files:
                md.append("## Context Documents")
                md.append("")
                for ctx_file in context_files:
                    md.append(f"- [{ctx_file.name}](context/{ctx_file.name})")
                md.append("")

        # Dependencies
        if 'blocked_by' in track and track['blocked_by']:
            md.append("## Dependencies")
            md.append("")
            for dep in track['blocked_by']:
                md.append(f"- **Blocked by:** `{dep.get('dependency_id')}` (requires: {dep.get('required_status')})")
            md.append("")

        # Timeline
        md.append("## Timeline")
        md.append("")
        md.append(f"- **Created:** {self._format_date(track.get('created'))}")
        if track.get('started'):
            md.append(f"- **Started:** {self._format_date(track.get('started'))}")
        if track.get('estimated_duration'):
            md.append(f"- **Estimated Duration:** {track.get('estimated_duration')}")
        if track.get('completed'):
            md.append(f"- **Completed:** {self._format_date(track.get('completed'))}")
        md.append("")

        # Footer
        md.append("---")
        md.append("")
        md.append(f"*Generated from {Path(track_yaml_path).name} on {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*")
        md.append("")

        return '\n'.join(md)

    def generate_sprint_markdown(self, sprint_yaml_path: str) -> str:
        """
        Generate markdown view for a sprint.

        Args:
            sprint_yaml_path: Path to sprint.yaml

        Returns:
            Markdown content as string
        """
        with open(sprint_yaml_path) as f:
            data = yaml.safe_load(f)

        sprint = data.get('sprint', {})
        sprint_dir = Path(sprint_yaml_path).parent

        md = []
        md.append(f"# {sprint.get('name', 'Sprint')}")
        md.append("")
        md.append(f"**ID:** `{sprint.get('id', 'unknown')}`  ")
        md.append(f"**Track:** `{sprint.get('track_id', 'unknown')}`  ")
        md.append(f"**Status:** {self._format_status(sprint.get('status', 'not_started'))}  ")
        md.append("")

        # Description
        if 'description' in sprint:
            md.append("## Description")
            md.append("")
            md.append(sprint['description'])
            md.append("")

        # Goals
        if 'metadata' in sprint and 'goals' in sprint['metadata']:
            md.append("## Goals")
            md.append("")
            for goal in sprint['metadata']['goals']:
                md.append(f"- {goal}")
            md.append("")

        # Progress
        if 'progress' in sprint:
            progress = sprint['progress']
            md.append("## Progress")
            md.append("")
            md.append(f"- **Tasks:** {progress.get('tasks_completed', 0)}/{progress.get('tasks_total', 0)} completed")
            md.append(f"- **Overall:** {progress.get('completion_percent', 0)}% complete")
            md.append("")

        # Tasks - load from standalone task files (tasks/*.yaml)
        sprint_id = sprint.get('id')
        tasks_dir = self.roadmap_root / "tasks"
        tasks = []

        # First, collect tasks for this sprint from standalone files
        if tasks_dir.exists() and sprint_id:
            for task_file in tasks_dir.glob("*.yaml"):
                if task_file.name.startswith('.'):
                    continue
                try:
                    with open(task_file) as f:
                        task_data = yaml.safe_load(f)
                    if task_data and 'task' in task_data:
                        t = task_data['task']
                        if t.get('sprint_id') == sprint_id:
                            tasks.append(t)
                except Exception:
                    continue

        # Fall back to embedded tasks if no standalone tasks found (DEPRECATED)
        if not tasks and 'tasks' in sprint:
            tasks = sprint['tasks']

        if tasks:
            md.append("## Tasks")
            md.append("")
            for task in tasks:
                task_id = task.get('id')
                task_title = task.get('title', task_id)
                task_status = task.get('status', 'not_started')
                task_type = task.get('type') or task.get('task_type', 'development')

                md.append(f"### {task_title}")
                md.append(f"- **ID:** `{task_id}`")
                md.append(f"- **Type:** {task_type}")
                md.append(f"- **Status:** {self._format_status(task_status)}")
                md.append("")

        # Context files
        context_dir = sprint_dir / 'context'
        if context_dir.exists():
            context_files = sorted(context_dir.glob('*.md'))
            if context_files:
                md.append("## Context Documents")
                md.append("")
                for ctx_file in context_files:
                    md.append(f"- [{ctx_file.name}](context/{ctx_file.name})")
                md.append("")

        # Dependencies
        if 'blocked_by' in sprint and sprint['blocked_by']:
            md.append("## Dependencies")
            md.append("")
            for dep in sprint['blocked_by']:
                md.append(f"- **Blocked by:** `{dep.get('dependency_id')}` (requires: {dep.get('required_status')})")
            md.append("")

        # Timeline
        md.append("## Timeline")
        md.append("")
        md.append(f"- **Created:** {self._format_date(sprint.get('created'))}")
        if sprint.get('started'):
            md.append(f"- **Started:** {self._format_date(sprint.get('started'))}")
        if sprint.get('estimated_duration'):
            md.append(f"- **Estimated Duration:** {sprint.get('estimated_duration')}")
        if sprint.get('completed'):
            md.append(f"- **Completed:** {self._format_date(sprint.get('completed'))}")
        md.append("")

        # Footer
        md.append("---")
        md.append("")
        md.append(f"*Generated from {Path(sprint_yaml_path).name} on {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*")
        md.append("")

        return '\n'.join(md)

    def generate_task_markdown(self, task_yaml_path: str) -> str:
        """
        Generate markdown view for a task.

        Args:
            task_yaml_path: Path to task.yaml

        Returns:
            Markdown content as string
        """
        with open(task_yaml_path) as f:
            data = yaml.safe_load(f)

        task = data.get('task', {})
        task_dir = Path(task_yaml_path).parent

        md = []
        md.append(f"# {task.get('title', 'Task')}")
        md.append("")
        md.append(f"**ID:** `{task.get('id', 'unknown')}`  ")
        md.append(f"**Sprint:** `{task.get('sprint_id', 'unknown')}`  ")
        md.append(f"**Type:** {task.get('type', 'development')}  ")
        md.append(f"**Status:** {self._format_status(task.get('status', 'not_started'))}  ")
        md.append(f"**Priority:** {self._format_priority(task.get('priority', 'medium'))}  ")
        md.append("")

        # Description
        if 'description' in task:
            md.append("## Description")
            md.append("")
            md.append(task['description'])
            md.append("")

        # Acceptance Criteria
        if 'acceptance_criteria' in task:
            md.append("## Acceptance Criteria")
            md.append("")
            for criteria in task['acceptance_criteria']:
                md.append(f"- {criteria}")
            md.append("")

        # Deliverables
        if 'metadata' in task and 'deliverables' in task['metadata']:
            md.append("## Deliverables")
            md.append("")
            for deliverable in task['metadata']['deliverables']:
                md.append(f"- {deliverable}")
            md.append("")

        # Context files
        context_dir = task_dir / 'context'
        if context_dir.exists():
            context_files = sorted(context_dir.glob('*'))
            if context_files:
                md.append("## Context Files")
                md.append("")
                for ctx_file in context_files:
                    if ctx_file.is_file():
                        md.append(f"- [{ctx_file.name}](context/{ctx_file.name})")
                md.append("")

        # Dependencies
        if 'blocked_by' in task and task['blocked_by']:
            md.append("## Dependencies")
            md.append("")
            for dep in task['blocked_by']:
                md.append(f"- **Blocked by:** `{dep.get('dependency_id')}` (requires: {dep.get('required_status')})")
            md.append("")

        # Metadata
        md.append("## Details")
        md.append("")
        if task.get('estimated_tokens'):
            md.append(f"- **Estimated Tokens:** {task.get('estimated_tokens'):,}")
        if task.get('complexity'):
            md.append(f"- **Complexity:** {task.get('complexity')}")
        md.append("")

        # Timeline
        md.append("## Timeline")
        md.append("")
        md.append(f"- **Created:** {self._format_date(task.get('created'))}")
        if task.get('started'):
            md.append(f"- **Started:** {self._format_date(task.get('started'))}")
        if task.get('completed'):
            md.append(f"- **Completed:** {self._format_date(task.get('completed'))}")
        md.append("")

        # Footer
        md.append("---")
        md.append("")
        md.append(f"*Generated from {Path(task_yaml_path).name} on {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*")
        md.append("")

        return '\n'.join(md)
