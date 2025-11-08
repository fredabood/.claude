"""
Roadmap caching layer for performance optimization.

Provides in-memory caching of roadmap objects with lazy loading,
dependency graph pre-computation, and cache invalidation.

Performance targets:
- Task lookup: < 5ms (vs 100ms without cache)
- Load all tasks: < 10ms (vs 150ms without cache)
- Dependency graph: < 20ms (vs 300ms without cache)
"""

from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from collections import deque
import time

from filesystem import FileSystemManager, load_yaml


class RoadmapCache:
    """In-memory cache for fast roadmap queries."""

    def __init__(self, root_dir: Path):
        """
        Initialize roadmap cache.

        Args:
            root_dir: Root directory containing .vibey/
        """
        self.root_dir = Path(root_dir)
        self.fs = FileSystemManager(root_dir)

        # Lazy-loaded indexes (id -> file_path)
        self._task_index: Dict[str, Path] = {}
        self._sprint_index: Dict[str, Path] = {}
        self._track_index: Dict[str, Path] = {}

        # Lazy-loaded object caches (id -> object data)
        self._task_cache: Dict[str, Dict] = {}
        self._sprint_cache: Dict[str, Dict] = {}
        self._track_cache: Dict[str, Dict] = {}

        # Pre-computed dependency graphs (built on first query)
        self._dep_graph: Optional[Dict[str, List[str]]] = None  # id -> [dependent_ids]
        self._reverse_dep_graph: Optional[Dict[str, List[str]]] = None  # id -> [dependency_ids]

        # File modification tracking
        self._file_mtimes: Dict[Path, float] = {}

        # Cache statistics
        self._hits = 0
        self._misses = 0
        self._builds = 0

        # Cache state
        self._indexes_built = False

    # =========================================================================
    # Public API - Task Operations
    # =========================================================================

    def get_task(self, task_id: str) -> Optional[Dict]:
        """
        Get task by ID with O(1) lookup after index built.

        Args:
            task_id: Task ID

        Returns:
            Task data dict, or None if not found
        """
        # Check object cache first
        if task_id in self._task_cache:
            self._hits += 1
            return self._task_cache[task_id]

        # Check if index is built
        if not self._indexes_built:
            self._build_indexes()

        # Check index
        if task_id in self._task_index:
            file_path = self._task_index[task_id]
            task = self._load_task_from_file(file_path, task_id)
            if task:
                self._task_cache[task_id] = task
                self._hits += 1
                return task

        # Not found
        self._misses += 1
        return None

    def get_all_tasks(self) -> List[Dict]:
        """
        Get all tasks.

        Returns:
            List of all task dicts
        """
        if not self._indexes_built:
            self._build_indexes()

        tasks = []
        for task_id, file_path in self._task_index.items():
            task = self.get_task(task_id)
            if task:
                tasks.append(task)

        return tasks

    def get_tasks_by_sprint(self, sprint_id: str) -> List[Dict]:
        """
        Get all tasks for a sprint.

        Args:
            sprint_id: Sprint ID

        Returns:
            List of task dicts
        """
        all_tasks = self.get_all_tasks()
        return [t for t in all_tasks if t.get('sprint_id') == sprint_id]

    # =========================================================================
    # Public API - Sprint Operations
    # =========================================================================

    def get_sprint(self, sprint_id: str) -> Optional[Dict]:
        """
        Get sprint by ID.

        Args:
            sprint_id: Sprint ID

        Returns:
            Sprint data dict, or None if not found
        """
        # Check object cache
        if sprint_id in self._sprint_cache:
            self._hits += 1
            return self._sprint_cache[sprint_id]

        # Check if index is built
        if not self._indexes_built:
            self._build_indexes()

        # Check index
        if sprint_id in self._sprint_index:
            file_path = self._sprint_index[sprint_id]
            data = load_yaml(file_path)
            if data and 'sprint' in data:
                sprint = data['sprint']
                self._sprint_cache[sprint_id] = sprint
                self._hits += 1
                return sprint

        # Not found
        self._misses += 1
        return None

    def get_all_sprints(self) -> List[Dict]:
        """
        Get all sprints.

        Returns:
            List of all sprint dicts
        """
        if not self._indexes_built:
            self._build_indexes()

        sprints = []
        for sprint_id in self._sprint_index.keys():
            sprint = self.get_sprint(sprint_id)
            if sprint:
                sprints.append(sprint)

        return sprints

    # =========================================================================
    # Public API - Track Operations
    # =========================================================================

    def get_track(self, track_id: str) -> Optional[Dict]:
        """
        Get track by ID.

        Args:
            track_id: Track ID

        Returns:
            Track data dict, or None if not found
        """
        # Check object cache
        if track_id in self._track_cache:
            self._hits += 1
            return self._track_cache[track_id]

        # Check if index is built
        if not self._indexes_built:
            self._build_indexes()

        # Check index
        if track_id in self._track_index:
            file_path = self._track_index[track_id]
            data = load_yaml(file_path)
            if data and 'track' in data:
                track = data['track']
                self._track_cache[track_id] = track
                self._hits += 1
                return track

        # Not found
        self._misses += 1
        return None

    def get_all_tracks(self) -> List[Dict]:
        """
        Get all tracks.

        Returns:
            List of all track dicts
        """
        if not self._indexes_built:
            self._build_indexes()

        tracks = []
        for track_id in self._track_index.keys():
            track = self.get_track(track_id)
            if track:
                tracks.append(track)

        return tracks

    # =========================================================================
    # Public API - Dependency Graph Operations
    # =========================================================================

    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """
        Get dependency graph (adjacency list).

        Returns:
            Dict mapping object_id -> list of dependency IDs
        """
        if self._dep_graph is None:
            self._build_dependency_graph()

        return self._dep_graph

    def get_reverse_dependency_graph(self) -> Dict[str, List[str]]:
        """
        Get reverse dependency graph.

        Returns:
            Dict mapping object_id -> list of IDs that depend on it
        """
        if self._reverse_dep_graph is None:
            self._build_dependency_graph()

        return self._reverse_dep_graph

    def get_dependencies(self, object_id: str) -> List[str]:
        """
        Get dependencies for an object.

        Args:
            object_id: Task, sprint, or track ID

        Returns:
            List of dependency IDs
        """
        dep_graph = self.get_dependency_graph()
        return dep_graph.get(object_id, [])

    def get_dependents(self, object_id: str) -> List[str]:
        """
        Get objects that depend on this object.

        Args:
            object_id: Task, sprint, or track ID

        Returns:
            List of dependent IDs
        """
        reverse_graph = self.get_reverse_dependency_graph()
        return reverse_graph.get(object_id, [])

    # =========================================================================
    # Public API - Cache Management
    # =========================================================================

    def invalidate(self, file_path: Optional[Path] = None):
        """
        Invalidate cache.

        Args:
            file_path: Specific file to invalidate, or None for full invalidation
        """
        if file_path:
            # Partial invalidation - remove file from tracking
            if file_path in self._file_mtimes:
                del self._file_mtimes[file_path]

            # Clear caches for objects from this file
            # This is conservative - could be more granular
            self._task_cache.clear()
            self._sprint_cache.clear()
            self._track_cache.clear()
        else:
            # Full invalidation
            self._task_index.clear()
            self._sprint_index.clear()
            self._track_index.clear()
            self._task_cache.clear()
            self._sprint_cache.clear()
            self._track_cache.clear()
            self._dep_graph = None
            self._reverse_dep_graph = None
            self._file_mtimes.clear()
            self._indexes_built = False

    def get_stats(self) -> Dict:
        """
        Get cache statistics.

        Returns:
            Dict with hits, misses, hit_rate, builds
        """
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0

        return {
            'hits': self._hits,
            'misses': self._misses,
            'total_queries': total,
            'hit_rate': round(hit_rate, 2),
            'index_builds': self._builds,
            'indexes_built': self._indexes_built,
            'tasks_indexed': len(self._task_index),
            'sprints_indexed': len(self._sprint_index),
            'tracks_indexed': len(self._track_index),
        }

    def get_mtime(self, file_path: Path) -> Optional[float]:
        """
        Get cached mtime for file.

        Args:
            file_path: File path

        Returns:
            Cached mtime, or None if not cached
        """
        return self._file_mtimes.get(file_path)

    def check_validity(self) -> bool:
        """
        Check if cache is still valid (no files modified).

        Returns:
            True if valid, False if any files were modified
        """
        for file_path, cached_mtime in self._file_mtimes.items():
            if file_path.exists():
                actual_mtime = file_path.stat().st_mtime
                if actual_mtime > cached_mtime:
                    return False
            else:
                # File was deleted
                return False

        return True

    # =========================================================================
    # Private Methods - Index Building
    # =========================================================================

    def _build_indexes(self):
        """Build all indexes by scanning filesystem."""
        if self._indexes_built:
            return

        self._builds += 1
        start_time = time.time()

        # Build task index
        self._build_task_index()

        # Build sprint index
        self._build_sprint_index()

        # Build track index
        self._build_track_index()

        self._indexes_built = True

        elapsed = (time.time() - start_time) * 1000  # Convert to ms
        # print(f"Built indexes in {elapsed:.1f}ms")

    def _build_task_index(self):
        """Build task ID -> file path index."""
        tasks_dir = self.fs.vibey_dir / self.fs.TASKS_DIR
        if not tasks_dir.exists():
            return

        for task_file in tasks_dir.glob("*-tasks.yaml"):
            # Track file mtime
            self._file_mtimes[task_file] = task_file.stat().st_mtime

            # Load and index tasks
            data = load_yaml(task_file)
            if data and 'tasks' in data:
                for task in data['tasks']:
                    task_id = task.get('id')
                    if task_id:
                        self._task_index[task_id] = task_file

    def _build_sprint_index(self):
        """Build sprint ID -> file path index."""
        sprints_dir = self.fs.vibey_dir / self.fs.SPRINTS_DIR
        if not sprints_dir.exists():
            return

        for sprint_file in sprints_dir.glob("*.yaml"):
            # Track file mtime
            self._file_mtimes[sprint_file] = sprint_file.stat().st_mtime

            # Load and index sprint
            data = load_yaml(sprint_file)
            if data and 'sprint' in data:
                sprint_id = data['sprint'].get('id')
                if sprint_id:
                    self._sprint_index[sprint_id] = sprint_file

    def _build_track_index(self):
        """Build track ID -> file path index."""
        tracks_dir = self.fs.vibey_dir / self.fs.TRACKS_DIR
        if not tracks_dir.exists():
            return

        for track_file in tracks_dir.glob("*.yaml"):
            # Track file mtime
            self._file_mtimes[track_file] = track_file.stat().st_mtime

            # Load and index track
            data = load_yaml(track_file)
            if data and 'track' in data:
                track_id = data['track'].get('id')
                if track_id:
                    self._track_index[track_id] = track_file

    def _load_task_from_file(self, file_path: Path, task_id: str) -> Optional[Dict]:
        """
        Load specific task from file.

        Args:
            file_path: Path to tasks file
            task_id: Task ID to find

        Returns:
            Task dict, or None if not found
        """
        data = load_yaml(file_path)
        if data and 'tasks' in data:
            for task in data['tasks']:
                if task.get('id') == task_id:
                    return task

        return None

    # =========================================================================
    # Private Methods - Dependency Graph Building
    # =========================================================================

    def _build_dependency_graph(self):
        """Build dependency and reverse dependency graphs."""
        # Initialize graphs
        self._dep_graph = {}
        self._reverse_dep_graph = {}

        # Process tasks
        for task in self.get_all_tasks():
            task_id = task.get('id')
            if not task_id:
                continue

            # Initialize lists
            if task_id not in self._dep_graph:
                self._dep_graph[task_id] = []

            # Process dependencies
            deps = task.get('dependencies', [])
            for dep in deps:
                target_id = dep.get('target_id')
                if target_id:
                    # Add to dependency graph
                    self._dep_graph[task_id].append(target_id)

                    # Add to reverse graph
                    if target_id not in self._reverse_dep_graph:
                        self._reverse_dep_graph[target_id] = []
                    self._reverse_dep_graph[target_id].append(task_id)

        # Process sprints
        for sprint in self.get_all_sprints():
            sprint_id = sprint.get('id')
            if not sprint_id:
                continue

            # Initialize lists
            if sprint_id not in self._dep_graph:
                self._dep_graph[sprint_id] = []

            # Process dependencies
            deps = sprint.get('dependencies', [])
            for dep in deps:
                target_id = dep.get('target_id')
                if target_id:
                    self._dep_graph[sprint_id].append(target_id)

                    if target_id not in self._reverse_dep_graph:
                        self._reverse_dep_graph[target_id] = []
                    self._reverse_dep_graph[target_id].append(sprint_id)

        # Process tracks
        for track in self.get_all_tracks():
            track_id = track.get('id')
            if not track_id:
                continue

            # Initialize lists
            if track_id not in self._dep_graph:
                self._dep_graph[track_id] = []

            # Process dependencies
            deps = track.get('dependencies', [])
            for dep in deps:
                target_id = dep.get('target_id')
                if target_id:
                    self._dep_graph[track_id].append(target_id)

                    if target_id not in self._reverse_dep_graph:
                        self._reverse_dep_graph[target_id] = []
                    self._reverse_dep_graph[track_id].append(track_id)
