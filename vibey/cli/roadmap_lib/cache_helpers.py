"""
Helper functions for using RoadmapCache in command handlers.

Provides convenient functions for command handlers to use caching.
"""

from pathlib import Path
from typing import Optional, List, Dict

from .cache import RoadmapCache
from .filesystem import find_roadmap_root, load_yaml, FileSystemManager


def get_cached_task(cache: Optional[RoadmapCache], task_id: str, root_dir: Optional[Path] = None) -> Optional[Dict]:
    """
    Get task by ID, using cache if available.

    Args:
        cache: RoadmapCache instance, or None to load directly
        task_id: Task ID
        root_dir: Root directory (if cache is None)

    Returns:
        Task dict, or None if not found
    """
    if cache:
        return cache.get_task(task_id)

    # Fallback: load directly from hierarchical structure
    root = root_dir or find_roadmap_root()
    if not root:
        return None

    fs = FileSystemManager(root)

    # Search hierarchical structure for task
    # Try to find task directory by ID
    task_dir = fs.dir_manager.find_directory_by_id(task_id)
    if task_dir:
        task_file = task_dir / "task.yaml"
        if task_file.exists():
            data = load_yaml(task_file)
            return data.get('task') if data else None

    # Fallback: linear scan through all tracks/sprints/tasks
    for track_slug, _ in fs.dir_manager.list_tracks():
        for sprint_slug, _ in fs.dir_manager.list_sprints(track_slug):
            for task_slug, tid in fs.dir_manager.list_tasks(track_slug, sprint_slug):
                if tid == task_id:
                    paths = fs.dir_manager.get_paths(track_slug, sprint_slug, task_slug)
                    task_file = paths.task_path("task.yaml")
                    data = load_yaml(task_file)
                    return data.get('task') if data else None

    return None


def get_cached_sprint(cache: Optional[RoadmapCache], sprint_id: str, root_dir: Optional[Path] = None) -> Optional[Dict]:
    """
    Get sprint by ID, using cache if available.

    Args:
        cache: RoadmapCache instance, or None to load directly
        sprint_id: Sprint ID
        root_dir: Root directory (if cache is None)

    Returns:
        Sprint dict, or None if not found
    """
    if cache:
        return cache.get_sprint(sprint_id)

    # Fallback: load directly
    root = root_dir or find_roadmap_root()
    if not root:
        return None

    fs = FileSystemManager(root)
    sprint_file = fs.get_sprint_path(sprint_id)
    if not sprint_file.exists():
        return None

    data = load_yaml(sprint_file)
    return data.get('sprint') if data else None


def get_cached_track(cache: Optional[RoadmapCache], track_id: str, root_dir: Optional[Path] = None) -> Optional[Dict]:
    """
    Get track by ID, using cache if available.

    Args:
        cache: RoadmapCache instance, or None to load directly
        track_id: Track ID
        root_dir: Root directory (if cache is None)

    Returns:
        Track dict, or None if not found
    """
    if cache:
        return cache.get_track(track_id)

    # Fallback: load directly
    root = root_dir or find_roadmap_root()
    if not root:
        return None

    fs = FileSystemManager(root)
    track_file = fs.get_track_path(track_id)
    if not track_file.exists():
        return None

    data = load_yaml(track_file)
    return data.get('track') if data else None


def get_all_cached_tasks(cache: Optional[RoadmapCache], root_dir: Optional[Path] = None) -> List[Dict]:
    """
    Get all tasks, using cache if available.

    Args:
        cache: RoadmapCache instance, or None to load directly
        root_dir: Root directory (if cache is None)

    Returns:
        List of task dicts
    """
    if cache:
        return cache.get_all_tasks()

    # Fallback: load directly from hierarchical structure
    root = root_dir or find_roadmap_root()
    if not root:
        return []

    fs = FileSystemManager(root)
    all_tasks = []

    # Traverse hierarchical structure
    for track_slug, _ in fs.dir_manager.list_tracks():
        for sprint_slug, _ in fs.dir_manager.list_sprints(track_slug):
            for task_slug, _ in fs.dir_manager.list_tasks(track_slug, sprint_slug):
                paths = fs.dir_manager.get_paths(track_slug, sprint_slug, task_slug)
                task_file = paths.task_path("task.yaml")
                if task_file.exists():
                    data = load_yaml(task_file)
                    if data and 'task' in data:
                        all_tasks.append(data['task'])

    return all_tasks


def get_all_cached_sprints(cache: Optional[RoadmapCache], root_dir: Optional[Path] = None) -> List[Dict]:
    """
    Get all sprints, using cache if available.

    Args:
        cache: RoadmapCache instance, or None to load directly
        root_dir: Root directory (if cache is None)

    Returns:
        List of sprint dicts
    """
    if cache:
        return cache.get_all_sprints()

    # Fallback: load directly from hierarchical structure
    root = root_dir or find_roadmap_root()
    if not root:
        return []

    fs = FileSystemManager(root)
    all_sprints = []

    # Traverse hierarchical structure
    for track_slug, _ in fs.dir_manager.list_tracks():
        for sprint_slug, _ in fs.dir_manager.list_sprints(track_slug):
            paths = fs.dir_manager.get_paths(track_slug, sprint_slug)
            sprint_file = paths.sprint_path("sprint.yaml")
            if sprint_file.exists():
                data = load_yaml(sprint_file)
                if data and 'sprint' in data:
                    all_sprints.append(data['sprint'])

    return all_sprints


def get_all_cached_tracks(cache: Optional[RoadmapCache], root_dir: Optional[Path] = None) -> List[Dict]:
    """
    Get all tracks, using cache if available.

    Args:
        cache: RoadmapCache instance, or None to load directly
        root_dir: Root directory (if cache is None)

    Returns:
        List of track dicts
    """
    if cache:
        return cache.get_all_tracks()

    # Fallback: load directly from hierarchical structure
    root = root_dir or find_roadmap_root()
    if not root:
        return []

    fs = FileSystemManager(root)
    all_tracks = []

    # Traverse hierarchical structure
    for track_slug, _ in fs.dir_manager.list_tracks():
        paths = fs.dir_manager.get_paths(track_slug)
        track_file = paths.track_path("track.yaml")
        if track_file.exists():
            data = load_yaml(track_file)
            if data and 'track' in data:
                all_tracks.append(data['track'])

    return all_tracks


def get_cached_dependencies(cache: Optional[RoadmapCache], object_id: str, root_dir: Optional[Path] = None) -> List[str]:
    """
    Get dependencies for an object, using cache if available.

    Args:
        cache: RoadmapCache instance, or None to compute directly
        object_id: Task, sprint, or track ID
        root_dir: Root directory (if cache is None)

    Returns:
        List of dependency IDs
    """
    if cache:
        return cache.get_dependencies(object_id)

    # Fallback: compute directly (slower)
    # Try to find the object
    obj = None

    # Try as task
    obj = get_cached_task(cache, object_id, root_dir)
    if not obj:
        # Try as sprint
        obj = get_cached_sprint(cache, object_id, root_dir)
    if not obj:
        # Try as track
        obj = get_cached_track(cache, object_id, root_dir)

    if not obj:
        return []

    # Extract dependency IDs
    deps = obj.get('dependencies', [])
    return [dep.get('target_id') for dep in deps if dep.get('target_id')]


def get_cached_dependents(cache: Optional[RoadmapCache], object_id: str, root_dir: Optional[Path] = None) -> List[str]:
    """
    Get dependents for an object, using cache if available.

    Args:
        cache: RoadmapCache instance, or None to compute directly
        object_id: Task, sprint, or track ID
        root_dir: Root directory (if cache is None)

    Returns:
        List of dependent IDs
    """
    if cache:
        return cache.get_dependents(object_id)

    # Fallback: compute directly (very slow - requires loading everything)
    all_tasks = get_all_cached_tasks(cache, root_dir)
    all_sprints = get_all_cached_sprints(cache, root_dir)
    all_tracks = get_all_cached_tracks(cache, root_dir)

    dependents = []

    # Check all objects for dependencies on object_id
    for task in all_tasks:
        deps = task.get('dependencies', [])
        for dep in deps:
            if dep.get('target_id') == object_id:
                dependents.append(task['id'])
                break

    for sprint in all_sprints:
        deps = sprint.get('dependencies', [])
        for dep in deps:
            if dep.get('target_id') == object_id:
                dependents.append(sprint['id'])
                break

    for track in all_tracks:
        deps = track.get('dependencies', [])
        for dep in deps:
            if dep.get('target_id') == object_id:
                dependents.append(track['id'])
                break

    return dependents
