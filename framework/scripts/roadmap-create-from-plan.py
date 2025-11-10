#!/usr/bin/env python3
"""
Create Roadmap Sprint from Plan

Parses a sprint plan markdown file and creates:
- Sprint YAML in hierarchical structure
- Task YAMLs in hierarchical structure
- Updates track to reference the sprint

Usage:
    roadmap-create-from-plan.py --plan sprint-plan.md --track main --sprint sprint-1
    roadmap-create-from-plan.py --plan sprint-plan.md --track backend --start
"""

import sys
import re
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

# Add framework to path
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))

from framework.roadmap.models import Sprint, Task, TaskStatus, Priority, Complexity
from framework.roadmap.serialization import save_sprint, save_tasks, load_track, save_track
from framework.roadmap.directory_manager import DirectoryManager


class SprintPlanParser:
    """Parse sprint plan markdown to extract structure."""

    def __init__(self, plan_path: Path):
        self.plan_path = plan_path
        self.content = plan_path.read_text()

    def parse_metadata(self) -> Dict[str, str]:
        """Extract sprint metadata from plan header."""
        metadata = {}

        # Extract from header (first 50 lines)
        header = '\n'.join(self.content.split('\n')[:50])

        # Sprint ID
        if match := re.search(r'\*\*Sprint ID:\*\*\s*(.+)', header):
            metadata['sprint_id'] = match.group(1).strip()

        # Sprint Name
        if match := re.search(r'\*\*Sprint Name:\*\*\s*(.+)', header):
            metadata['name'] = match.group(1).strip()
        elif match := re.search(r'^# Sprint Plan:\s*(.+)', header, re.MULTILINE):
            metadata['name'] = match.group(1).strip()

        # Track
        if match := re.search(r'\*\*Track:\*\*\s*(.+)', header):
            metadata['track_id'] = match.group(1).strip()

        # Duration
        if match := re.search(r'\*\*Duration:\*\*\s*(.+)', header):
            metadata['estimated_duration'] = match.group(1).strip()

        # Priority
        if match := re.search(r'\*\*Priority:\*\*\s*(.+)', header):
            priority_str = match.group(1).strip().lower()
            if priority_str in ['critical', 'high', 'medium', 'low']:
                metadata['priority'] = priority_str

        return metadata

    def parse_tasks(self) -> List[Dict[str, any]]:
        """Extract tasks from plan."""
        tasks = []

        # Find Tasks section
        tasks_match = re.search(r'^## Tasks\s*$(.*?)(?=^## |\Z)', self.content, re.MULTILINE | re.DOTALL)
        if not tasks_match:
            print("⚠️  No '## Tasks' section found in plan")
            return tasks

        tasks_section = tasks_match.group(1)

        # Extract individual tasks
        # Pattern: #### Task N: Title or **ID:** task-id
        task_blocks = re.split(r'(?=####\s+Task\s+\d+:)', tasks_section)

        for block in task_blocks:
            if not block.strip():
                continue

            task_data = self._parse_task_block(block)
            if task_data:
                tasks.append(task_data)

        return tasks

    def _parse_task_block(self, block: str) -> Optional[Dict]:
        """Parse a single task block."""
        task = {}

        # Task title from #### Task N: Title
        if match := re.search(r'####\s+Task\s+\d+:\s*(.+)', block):
            task['title'] = match.group(1).strip()
        else:
            return None

        # Task ID
        if match := re.search(r'\*\*ID:\*\*\s*(.+)', block):
            task['id'] = match.group(1).strip()
        else:
            return None

        # Priority
        if match := re.search(r'\*\*Priority:\*\*\s*(.+)', block):
            priority_str = match.group(1).strip().lower()
            if priority_str in ['critical', 'high', 'medium', 'low']:
                task['priority'] = priority_str
            else:
                task['priority'] = 'medium'
        else:
            task['priority'] = 'medium'

        # Estimated hours
        if match := re.search(r'\*\*Estimated:\*\*\s*(\d+)\s*hours?', block):
            task['estimated_hours'] = int(match.group(1))
            task['estimated_tokens'] = int(match.group(1)) * 1000  # Rough estimate
        else:
            task['estimated_tokens'] = 5000

        # Agents
        if match := re.search(r'\*\*Agents?:\*\*\s*(.+)', block):
            agents_str = match.group(1).strip()
            agents = [a.strip() for a in agents_str.split(',')]
            task['assigned_agent'] = agents[0] if agents else 'web-developer'
        else:
            task['assigned_agent'] = 'web-developer'

        # Complexity (guess based on estimated hours)
        if 'estimated_hours' in task:
            if task['estimated_hours'] <= 4:
                task['complexity'] = 'simple'
            elif task['estimated_hours'] <= 12:
                task['complexity'] = 'medium'
            else:
                task['complexity'] = 'complex'
        else:
            task['complexity'] = 'medium'

        # Description
        if match := re.search(r'\*\*Description:\*\*\s*\n(.+?)(?=\n\*\*|\Z)', block, re.DOTALL):
            task['description'] = match.group(1).strip()
        else:
            # Use text after header as description
            lines = block.split('\n')
            desc_lines = []
            skip_next = False
            for line in lines[1:]:  # Skip title line
                if line.startswith('**'):
                    skip_next = True
                    continue
                if skip_next:
                    skip_next = False
                    continue
                if line.strip():
                    desc_lines.append(line)
                if len(desc_lines) >= 3:
                    break
            task['description'] = '\n'.join(desc_lines).strip()

        return task


def create_sprint_from_plan(
    plan_path: Path,
    track_id: str,
    sprint_id: Optional[str] = None,
    start: bool = False,
    dry_run: bool = False
) -> bool:
    """
    Create sprint and tasks from plan file.

    Args:
        plan_path: Path to sprint plan markdown
        track_id: Track ID to add sprint to
        sprint_id: Override sprint ID from plan
        start: Mark sprint as started
        dry_run: Show what would be created without creating

    Returns:
        Success status
    """
    if not plan_path.exists():
        print(f"❌ Plan file not found: {plan_path}")
        return False

    print(f"📋 Parsing sprint plan: {plan_path}")

    # Parse plan
    parser = SprintPlanParser(plan_path)
    metadata = parser.parse_metadata()
    tasks = parser.parse_tasks()

    # Use sprint_id from argument or metadata
    if sprint_id:
        metadata['sprint_id'] = sprint_id
    elif 'sprint_id' not in metadata:
        print("❌ No sprint ID specified and none found in plan")
        print("   Use --sprint flag or add '**Sprint ID:** sprint-name' to plan")
        return False

    sprint_id = metadata['sprint_id']

    print(f"\n📊 Sprint: {metadata.get('name', sprint_id)}")
    print(f"   ID: {sprint_id}")
    print(f"   Track: {track_id}")
    print(f"   Tasks: {len(tasks)}")

    if dry_run:
        print("\n🔍 DRY RUN - Tasks to be created:")
        for i, task in enumerate(tasks, 1):
            print(f"   {i}. {task['id']}: {task['title']}")
        return True

    # Find repository root
    root = Path.cwd()
    while root != root.parent:
        if (root / ".vibey").exists():
            break
        root = root.parent
    else:
        print("❌ No .vibey/ directory found in current or parent directories")
        return False

    # Initialize directory manager
    roadmap_root = root / ".vibey" / "roadmap"
    dir_manager = DirectoryManager(str(roadmap_root))

    # Create sprint directory
    print(f"\n📁 Creating sprint directory...")
    sprint_dir = dir_manager.create_sprint_directory(
        track_slug=track_id,
        sprint_id=sprint_id,
        sprint_slug=sprint_id,
        create_context=True
    )

    # Create sprint YAML
    sprint_data = Sprint(
        id=sprint_id,
        sprint_id=sprint_id,
        track_id=track_id,
        roadmap_id="vibey-framework-v2",  # TODO: Get from roadmap
        name=metadata.get('name', sprint_id),
        description=f"Sprint from plan: {plan_path.name}",
        status=TaskStatus.IN_PROGRESS if start else TaskStatus.NOT_STARTED,
        blocked=False,
        created=datetime.now(timezone.utc),
        started=datetime.now(timezone.utc) if start else None,
        completed=None,
        estimated_duration=metadata.get('estimated_duration', '2 weeks'),
        priority=Priority(metadata.get('priority', 'medium')),
        tasks_total=len(tasks),
        tasks_completed=0,
        progress_percent=0,
        dependencies=[],
        blocks=[],
        blocked_by=[],
        depends_on=[],
        depended_on_by=[],
        metadata={
            'source_plan': str(plan_path),
            'created_from_plan': datetime.now(timezone.utc).isoformat(),
        }
    )

    sprint_yaml = sprint_dir / "sprint.yaml"
    save_sprint(sprint_data, sprint_yaml)
    print(f"✓ Created: {sprint_yaml}")

    # Create task YAMLs
    print(f"\n📝 Creating {len(tasks)} tasks...")
    for task_data in tasks:
        task = Task(
            id=task_data['id'],
            task_id=task_data['id'],
            sprint_id=sprint_id,
            track_id=track_id,
            roadmap_id="vibey-framework-v2",
            task_type='development',
            title=task_data['title'],
            description=task_data.get('description', ''),
            status=TaskStatus.NOT_STARTED,
            blocked=False,
            created=datetime.now(timezone.utc),
            started=None,
            completed=None,
            assigned_agent=task_data.get('assigned_agent', 'web-developer'),
            priority=Priority(task_data.get('priority', 'medium')),
            complexity=Complexity(task_data.get('complexity', 'medium')),
            estimated_tokens=task_data.get('estimated_tokens', 5000),
            actual_tokens=None,
            dependencies=[],
            blocks=[],
            blocked_by=[],
            depends_on=[],
            depended_on_by=[],
            deliverables=[],
            commits=[],
            metadata={}
        )

        # Create task directory and YAML
        task_dir = dir_manager.create_task_directory(
            track_slug=track_id,
            sprint_slug=sprint_id,
            task_id=task_data['id'],
            task_slug=task_data['id'],
            create_context=True
        )

        task_yaml = task_dir / "task.yaml"
        from framework.roadmap.serialization import save_task
        save_task(task, task_yaml)

    print(f"✓ Created {len(tasks)} task files")

    print(f"\n✅ Sprint {sprint_id} created successfully!")
    print(f"   Sprint: {sprint_yaml}")
    print(f"   Tasks: {len(tasks)}")

    if start:
        print(f"   Status: Started")

    return True


def main():
    parser = argparse.ArgumentParser(
        description='Create roadmap sprint from plan file',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--plan',
        required=True,
        help='Path to sprint plan markdown file'
    )

    parser.add_argument(
        '--track',
        required=True,
        help='Track ID to add sprint to'
    )

    parser.add_argument(
        '--sprint',
        help='Override sprint ID (uses ID from plan if not specified)'
    )

    parser.add_argument(
        '--start',
        action='store_true',
        help='Mark sprint as started'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be created without creating'
    )

    args = parser.parse_args()

    plan_path = Path(args.plan)
    success = create_sprint_from_plan(
        plan_path=plan_path,
        track_id=args.track,
        sprint_id=args.sprint,
        start=args.start,
        dry_run=args.dry_run
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
