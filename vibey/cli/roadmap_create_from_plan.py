#!/usr/bin/env python3
"""
Create Roadmap Sprint from Plan

Parses a sprint plan markdown file and creates:
- Sprint YAML in flat ULID structure (.vibey/roadmap/sprints/{ULID}.yaml)
- Task YAMLs in flat ULID structure (.vibey/roadmap/tasks/{ULID}.yaml)
- Updates track to reference the sprint
- Updates .id mapping files for slug resolution

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

from ulid import ULID
from vibey.roadmap.models import Sprint, SprintProgress, SprintMetadata, Task, TaskMetadata, TaskStatus, TaskType, Priority, Complexity
from vibey.roadmap.serialization import save_sprint, save_task, load_track, save_track
from vibey.cli.roadmap_lib.filesystem import FileSystemManager


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


# Helper functions for ULID flat structure

def _resolve_track_id(track_id: str, roadmap_root: Path) -> Optional[str]:
    """Resolve a track slug or ULID to a ULID."""
    # If it looks like a ULID (26 chars, alphanumeric, uppercase), return as-is
    if len(track_id) == 26 and track_id.isalnum() and track_id.isupper():
        track_file = roadmap_root / "tracks" / f"{track_id}.yaml"
        if track_file.exists():
            return track_id
        return None

    # Otherwise, look up in .id file
    id_file = roadmap_root / "tracks" / ".id"
    if id_file.exists():
        for line in id_file.read_text().strip().split("\n"):
            if "=" in line:
                slug, ulid = line.split("=", 1)
                if slug == track_id:
                    return ulid

    return None


def _get_slug_for_ulid(item_type: str, ulid: str, roadmap_root: Path) -> Optional[str]:
    """Get the slug for a given ULID from .id file."""
    type_to_dir = {"track": "tracks", "sprint": "sprints", "task": "tasks"}
    id_file = roadmap_root / type_to_dir[item_type] / ".id"

    if id_file.exists():
        for line in id_file.read_text().strip().split("\n"):
            if "=" in line:
                slug, file_ulid = line.split("=", 1)
                if file_ulid == ulid:
                    return slug
    return None


def _update_id_mapping(item_type: str, slug: str, ulid: str, roadmap_root: Path):
    """Add a slug=ULID mapping to the .id file."""
    type_to_dir = {"track": "tracks", "sprint": "sprints", "task": "tasks"}
    id_file = roadmap_root / type_to_dir[item_type] / ".id"

    # Read existing content
    if id_file.exists():
        content = id_file.read_text()
        if not content.endswith("\n"):
            content += "\n"
    else:
        content = ""

    # Add new mapping
    content += f"{slug}={ulid}\n"
    id_file.write_text(content)


def _get_next_sprint_sequence(track_ulid: str, roadmap_root: Path) -> int:
    """Get the next sprint sequence number for a track."""
    import yaml

    track_file = roadmap_root / "tracks" / f"{track_ulid}.yaml"
    if not track_file.exists():
        return 1

    with open(track_file, 'r') as f:
        data = yaml.safe_load(f)

    sprints = data.get('track', {}).get('sprints', [])
    return len(sprints) + 1


def _update_sprint_tasks(sprint_yaml: Path, task_summaries: List[Dict]):
    """Update sprint YAML with task summaries."""
    import yaml

    with open(sprint_yaml, 'r') as f:
        data = yaml.safe_load(f)

    data['sprint']['tasks'] = task_summaries
    data['sprint']['progress'] = {
        'tasks_total': len(task_summaries),
        'tasks_completed': 0,
        'completion_percent': 0
    }

    with open(sprint_yaml, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def _add_sprint_to_track_file(roadmap_root: Path, track_ulid: str, sprint_slug: str, sprint_name: str):
    """Add a sprint reference to the track YAML file."""
    import yaml

    track_file = roadmap_root / "tracks" / f"{track_ulid}.yaml"
    if not track_file.exists():
        return

    with open(track_file, 'r') as f:
        data = yaml.safe_load(f)

    if 'track' not in data:
        data['track'] = {}
    if 'sprints' not in data['track']:
        data['track']['sprints'] = []

    # Add sprint summary
    sprint_entry = {
        'id': sprint_slug,
        'name': sprint_name,
        'status': 'not_started',
        'tasks_count': 0
    }
    data['track']['sprints'].append(sprint_entry)

    # Update progress
    if 'progress' not in data['track']:
        data['track']['progress'] = {}
    data['track']['progress']['sprints_total'] = len(data['track']['sprints'])

    with open(track_file, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


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

    # Initialize filesystem manager for flat ULID structure
    fs = FileSystemManager(root)
    roadmap_root = fs.roadmap_root

    # Resolve track ID (slug -> ULID if needed)
    resolved_track_id = _resolve_track_id(track_id, roadmap_root)
    if not resolved_track_id:
        print(f"❌ Track not found: {track_id}")
        return False

    # Generate ULID for sprint
    sprint_ulid = str(ULID())
    sprint_slug = sprint_id  # Use the sprint_id from plan as slug

    # Create sprint YAML in flat structure
    print(f"\n📁 Creating sprint in flat structure...")
    now = datetime.now(timezone.utc)

    # Get roadmap_id from roadmap.yaml
    try:
        from vibey.roadmap.serialization.yaml_loader import load_roadmap
        roadmap_path = fs.get_roadmap_path()
        roadmap = load_roadmap(roadmap_path)
        roadmap_id = roadmap.id
    except Exception:
        roadmap_id = "vibey-framework-v2"

    # Get track slug for parent reference
    track_slug = _get_slug_for_ulid("track", resolved_track_id, roadmap_root)

    # Create sprint object with new flat structure fields
    sprint_data = Sprint(
        id=sprint_ulid,
        name=metadata.get('name', sprint_id),
        track_id=track_slug or track_id,  # Use slug for reference
        roadmap_id=roadmap_id,
        status=TaskStatus.IN_PROGRESS if start else TaskStatus.NOT_STARTED,
        blocked=False,
        created=now,
        progress=SprintProgress(
            development_tasks_total=len(tasks),
            development_tasks_completed=0,
            completion_gate_tasks_total=0,
            completion_gate_tasks_completed=0,
            production_gate_tasks_total=0,
            production_gate_tasks_completed=0,
            tasks_total=len(tasks),
            tasks_completed=0,
            completion_percent=0,
        ),
        tasks=[],  # Will be populated with task summaries
        dependencies=[],
        blocked_by=[],
        depends_on=[],
        depended_on_by=[],
        deliverables=[],
        risks=[],
        metadata={
            'estimated_duration': metadata.get('estimated_duration', '2 weeks'),
            'plan_file': str(plan_path),
        },
        started=now if start else None,
        slug=sprint_slug,
        parent_ref=resolved_track_id,
        criteria=[],
        sequence=_get_next_sprint_sequence(resolved_track_id, roadmap_root),
    )

    # Save sprint to flat structure
    sprints_dir = roadmap_root / "sprints"
    sprints_dir.mkdir(parents=True, exist_ok=True)
    sprint_yaml = sprints_dir / f"{sprint_ulid}.yaml"
    save_sprint(sprint_data, sprint_yaml)
    print(f"✓ Created: {sprint_yaml.relative_to(root)}")

    # Update .id mapping for sprint
    _update_id_mapping("sprint", sprint_slug, sprint_ulid, roadmap_root)

    # Create task objects and save to flat structure
    print(f"\n📝 Creating {len(tasks)} tasks in flat structure...")
    tasks_dir = roadmap_root / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)

    task_summaries = []
    for i, task_data in enumerate(tasks, 1):
        task_now = datetime.now(timezone.utc)
        task_ulid = str(ULID())
        task_slug = f"{sprint_slug}-task-{i:03d}"

        task = Task(
            id=task_ulid,
            sprint_id=sprint_slug,  # Use sprint slug for reference
            track_id=track_slug or track_id,
            roadmap_id=roadmap_id,
            task_type=TaskType.DEVELOPMENT,
            title=task_data['title'],
            description=task_data.get('description', ''),
            status=TaskStatus.NOT_STARTED,
            created=task_now,
            priority=Priority(task_data.get('priority', 'medium')),
            complexity=Complexity(task_data.get('complexity', 'medium')),
            estimated_tokens=task_data.get('estimated_tokens', 5000),
            dependencies=[],
            blocked_by=[],
            depends_on=[],
            depended_on_by=[],
            deliverables=[],
            commits=[],
            metadata={},
            slug=task_slug,
            parent_ref=sprint_ulid,
            criteria=[],
            sequence=i,
        )

        # Save task to flat structure
        task_yaml = tasks_dir / f"{task_ulid}.yaml"
        save_task(task, task_yaml)

        # Update .id mapping for task
        _update_id_mapping("task", task_slug, task_ulid, roadmap_root)

        # Add to task summaries for sprint
        task_summaries.append({
            'id': task_slug,
            'title': task_data['title'],
            'status': 'not_started'
        })

    print(f"✓ Created {len(tasks)} task files")

    # Update sprint with task summaries
    _update_sprint_tasks(sprint_yaml, task_summaries)

    # Update track's sprint list
    _add_sprint_to_track_file(roadmap_root, resolved_track_id, sprint_slug, metadata.get('name', sprint_id))

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
