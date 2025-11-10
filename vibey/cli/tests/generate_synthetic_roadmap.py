"""
Generate synthetic roadmap for benchmarking.

Creates roadmaps of different sizes for performance testing.
"""

import sys
from pathlib import Path
from typing import Tuple
import random

# Add roadmap-lib to path
test_dir = Path(__file__).parent
scripts_dir = test_dir.parent
roadmap_lib_dir = scripts_dir / "roadmap-lib"
sys.path.insert(0, str(roadmap_lib_dir))

from filesystem import FileSystemManager, save_yaml


def generate_roadmap(root_dir: Path, num_tasks: int = 53) -> Tuple[int, int, int]:
    """
    Generate synthetic roadmap for benchmarking.

    Args:
        root_dir: Root directory for roadmap
        num_tasks: Target number of tasks (actual may vary slightly)

    Returns:
        Tuple of (num_tracks, num_sprints, num_tasks)
    """
    fs = FileSystemManager(root_dir)
    fs.ensure_structure()

    # Calculate structure based on target task count
    # Heuristic: ~10 tasks per sprint, ~3 sprints per track
    num_sprints = max(1, num_tasks // 10)
    num_tracks = max(1, num_sprints // 3)
    tasks_per_sprint = num_tasks // num_sprints

    # Create roadmap.yaml
    roadmap_data = {
        'roadmap': {
            'id': f'benchmark-roadmap-{num_tasks}',
            'name': f'Benchmark Roadmap ({num_tasks} tasks)',
            'version': '1.0.0',
            'description': f'Synthetic roadmap for performance benchmarking with ~{num_tasks} tasks',
        }
    }
    save_yaml(fs.get_roadmap_path(), roadmap_data)

    # Create tracks
    sprints_per_track = num_sprints // num_tracks
    sprint_counter = 0

    for track_idx in range(num_tracks):
        track_id = f'track-{track_idx + 1:03d}'

        track_data = {
            'track': {
                'id': track_id,
                'name': f'Track {track_idx + 1}',
                'roadmap_id': roadmap_data['roadmap']['id'],
                'status': random.choice(['planning', 'in_progress', 'completed']),
                'description': f'Benchmark track {track_idx + 1} with {sprints_per_track} sprints',
            }
        }
        save_yaml(fs.get_track_path(track_id), track_data)

        # Create sprints for this track
        for sprint_idx in range(sprints_per_track):
            sprint_counter += 1
            sprint_id = f'sprint-{sprint_counter:03d}'

            sprint_data = {
                'sprint': {
                    'id': sprint_id,
                    'name': f'Sprint {sprint_counter}',
                    'track_id': track_id,
                    'roadmap_id': roadmap_data['roadmap']['id'],
                    'status': random.choice(['planning', 'in_progress', 'completed']),
                    'description': f'Benchmark sprint {sprint_counter}',
                }
            }
            save_yaml(fs.get_sprint_path(sprint_id), sprint_data)

            # Create tasks for this sprint
            tasks = []
            for task_idx in range(tasks_per_sprint):
                task_num = (sprint_counter - 1) * tasks_per_sprint + task_idx + 1
                task_id = f'task-{task_num:05d}'

                task = {
                    'id': task_id,
                    'sprint_id': sprint_id,
                    'name': f'Task {task_num}',
                    'status': random.choice(['pending', 'in_progress', 'completed', 'blocked']),
                    'description': f'Benchmark task {task_num}',
                }

                # Add some dependencies (20% of tasks)
                if task_idx > 0 and random.random() < 0.2:
                    # Depend on previous task in same sprint
                    prev_task_num = task_num - 1
                    prev_task_id = f'task-{prev_task_num:05d}'
                    task['dependencies'] = [
                        {'target_id': prev_task_id, 'type': 'blocks'}
                    ]

                tasks.append(task)

            # Save tasks file
            tasks_data = {'tasks': tasks}
            save_yaml(fs.get_tasks_path(sprint_id), tasks_data)

    actual_tasks = num_sprints * tasks_per_sprint
    return num_tracks, num_sprints, actual_tasks


def main():
    """Generate roadmaps for different benchmark sizes."""
    import tempfile

    # Standard benchmark sizes
    sizes = [
        (53, "small"),     # Current Vibey roadmap size
        (200, "medium"),   # Medium project
        (500, "large"),    # Large project
    ]

    print("\n" + "="*70)
    print("Synthetic Roadmap Generator")
    print("="*70 + "\n")

    for num_tasks, size_name in sizes:
        with tempfile.TemporaryDirectory() as tmpdir:
            root_dir = Path(tmpdir)

            print(f"Generating {size_name} roadmap ({num_tasks} tasks)...")
            num_tracks, num_sprints, actual_tasks = generate_roadmap(root_dir, num_tasks)

            print(f"  Tracks:  {num_tracks}")
            print(f"  Sprints: {num_sprints}")
            print(f"  Tasks:   {actual_tasks}")
            print()


if __name__ == '__main__':
    main()
