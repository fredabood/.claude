"""
Roadmap caching layer for performance optimization.

Provides in-memory caching of roadmap objects with lazy loading,
dependency graph pre-computation, and cache invalidation.

Supports optional persistent disk cache for faster startup.

Performance targets:
- Task lookup: < 5ms (vs 100ms without cache)
- Load all tasks: < 10ms (vs 150ms without cache)
- Dependency graph: < 20ms (vs 300ms without cache)
- Cache load from disk: < 10ms (vs ~100ms to rebuild)
"""

from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from collections import deque
import time
import json
import subprocess

from .filesystem import FileSystemManager, load_yaml


class RoadmapCache:
    """In-memory cache for fast roadmap queries."""

    # Cache directory (gitignored - performance only)
    CACHE_DIR = ".cache"

    def __init__(self, root_dir: Path, enable_disk_cache: bool = True):
        """
        Initialize roadmap cache.

        Args:
            root_dir: Root directory containing .vibey/
            enable_disk_cache: Enable persistent disk cache for faster startup (default: True)
        """
        self.root_dir = Path(root_dir)
        self.fs = FileSystemManager(root_dir)
        self.enable_disk_cache = enable_disk_cache

        # Detect current git branch
        self.current_branch = self._get_current_branch()
        self.is_main_branch = self.current_branch in ['main', 'master']

        # Cache directory (gitignored - for indexes and mtimes only)
        self.cache_dir = self.fs.vibey_dir / self.CACHE_DIR

        # Graphs location (versioned on feature branches, not on main)
        self.graphs_file = self.fs.vibey_dir / "graphs.json"

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
        self._disk_loads = 0

        # Cache state
        self._indexes_built = False

        # Try loading from disk if enabled
        if self.enable_disk_cache:
            self._try_load_from_disk()

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

            # Delete disk cache (partial invalidation still clears all disk cache)
            if self.enable_disk_cache:
                self._delete_disk_cache()
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

            # Delete disk cache
            if self.enable_disk_cache:
                self._delete_disk_cache()

    def get_stats(self) -> Dict:
        """
        Get cache statistics.

        Returns:
            Dict with hits, misses, hit_rate, builds, disk_loads
        """
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0

        return {
            'hits': self._hits,
            'misses': self._misses,
            'total_queries': total,
            'hit_rate': round(hit_rate, 2),
            'index_builds': self._builds,
            'disk_loads': self._disk_loads,
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
    # Branch Detection
    # =========================================================================

    def _get_current_branch(self) -> str:
        """
        Get current git branch name.

        Returns:
            Branch name, or 'unknown' if not in a git repo
        """
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        return 'unknown'

    # =========================================================================
    # Persistent Disk Cache Methods
    # =========================================================================

    def _try_load_from_disk(self):
        """
        Try loading cache from disk if available and valid.

        Loads two types of cache:
        1. Performance cache (.cache/ - gitignored): indexes and mtimes
        2. Versioned graphs (.vibey/graphs.json - versioned on feature branches)
        """
        # Try loading performance cache (indexes + mtimes)
        if self.cache_dir.exists():
            self._try_load_performance_cache()

        # Try loading graphs (versioned on feature branches, not main)
        if self.graphs_file.exists():
            self._try_load_graphs()

    def _try_load_performance_cache(self):
        """Load performance cache (indexes and mtimes) from .cache/"""
        indexes_file = self.cache_dir / "indexes.json"
        mtimes_file = self.cache_dir / "mtimes.json"

        # Both files must exist
        if not (indexes_file.exists() and mtimes_file.exists()):
            return

        try:
            # Load file mtimes first to check validity
            with open(mtimes_file, 'r') as f:
                mtimes_data = json.load(f)
                # Convert path strings back to Path objects
                self._file_mtimes = {Path(p): mtime for p, mtime in mtimes_data.items()}

            # Check if cache is still valid
            if not self.check_validity():
                # Cache is stale, clear and return
                self._file_mtimes.clear()
                return

            # Load indexes
            with open(indexes_file, 'r') as f:
                indexes_data = json.load(f)
                # Convert path strings back to Path objects
                self._task_index = {k: Path(v) for k, v in indexes_data.get('tasks', {}).items()}
                self._sprint_index = {k: Path(v) for k, v in indexes_data.get('sprints', {}).items()}
                self._track_index = {k: Path(v) for k, v in indexes_data.get('tracks', {}).items()}

            # Mark indexes as built
            self._indexes_built = True
            self._disk_loads += 1

        except (json.JSONDecodeError, KeyError, OSError):
            # Cache load failed, clear and rebuild later
            self._task_index.clear()
            self._sprint_index.clear()
            self._track_index.clear()
            self._file_mtimes.clear()
            self._indexes_built = False

    def _try_load_graphs(self):
        """
        Load dependency graphs from .vibey/graphs.json

        On feature branches: graphs.json is versioned for session continuity
        On main branch: graphs.json is ignored (always rebuild from YAML)
        """
        try:
            with open(self.graphs_file, 'r') as f:
                graphs_data = json.load(f)
                self._dep_graph = graphs_data.get('dependencies', {})
                self._reverse_dep_graph = graphs_data.get('reverse_dependencies', {})

        except (json.JSONDecodeError, KeyError, OSError):
            # Graphs load failed, will rebuild when requested
            self._dep_graph = None
            self._reverse_dep_graph = None

    def _save_to_disk(self):
        """
        Save cache to disk for faster subsequent loads.

        Saves two types of cache:
        1. Performance cache (.cache/ - gitignored): indexes and mtimes
        2. Versioned graphs (.vibey/graphs.json - feature branches only)
        """
        if not self.enable_disk_cache:
            return

        # Save performance cache (always)
        self._save_performance_cache()

        # Save graphs (feature branches only, not main)
        if self._dep_graph is not None:
            self._save_graphs()

    def _save_performance_cache(self):
        """Save performance cache (indexes and mtimes) to .cache/"""
        # Create cache directory if needed
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Save indexes (absolute paths for fast loading)
        indexes_file = self.cache_dir / "indexes.json"
        indexes_data = {
            'tasks': {k: str(v) for k, v in self._task_index.items()},
            'sprints': {k: str(v) for k, v in self._sprint_index.items()},
            'tracks': {k: str(v) for k, v in self._track_index.items()},
        }
        with open(indexes_file, 'w') as f:
            json.dump(indexes_data, f, indent=2)

        # Save file mtimes
        mtimes_file = self.cache_dir / "mtimes.json"
        mtimes_data = {str(p): mtime for p, mtime in self._file_mtimes.items()}
        with open(mtimes_file, 'w') as f:
            json.dump(mtimes_data, f, indent=2)

    def _save_graphs(self):
        """
        Save dependency graphs to .vibey/graphs.json

        Only saves on feature branches (not main/master).
        Main branch always rebuilds graphs from YAML (source of truth).
        """
        # Don't save graphs on main branch
        if self.is_main_branch:
            return

        # Save graphs for session continuity on feature branches
        graphs_data = {
            'dependencies': self._dep_graph,
            'reverse_dependencies': self._reverse_dep_graph,
            'metadata': {
                'branch': self.current_branch,
                'generated_at': time.time(),
            }
        }
        with open(self.graphs_file, 'w') as f:
            json.dump(graphs_data, f, indent=2)

    def _delete_disk_cache(self):
        """
        Delete disk cache files.

        Deletes:
        1. Performance cache (.cache/): indexes.json, mtimes.json
        2. Versioned graphs (.vibey/graphs.json) - feature branches only
        """
        # Delete performance cache
        if self.cache_dir.exists():
            for cache_file in ['indexes.json', 'mtimes.json']:
                file_path = self.cache_dir / cache_file
                if file_path.exists():
                    file_path.unlink()

        # Delete graphs (feature branches only)
        if not self.is_main_branch and self.graphs_file.exists():
            self.graphs_file.unlink()

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

        # Save to disk for faster subsequent loads
        self._save_to_disk()

    def _build_task_index(self):
        """Build task ID -> file path index (hierarchical structure)."""
        # Traverse hierarchical structure
        for track_slug, _ in self.fs.dir_manager.list_tracks():
            for sprint_slug, _ in self.fs.dir_manager.list_sprints(track_slug):
                for task_slug, _ in self.fs.dir_manager.list_tasks(track_slug, sprint_slug):
                    paths = self.fs.dir_manager.get_paths(track_slug, sprint_slug, task_slug)
                    task_file = paths.task_path("task.yaml")

                    if not task_file.exists():
                        continue

                    # Track file mtime
                    self._file_mtimes[task_file] = task_file.stat().st_mtime

                    # Load and index task
                    data = load_yaml(task_file)
                    if data and 'task' in data:
                        task_id = data['task'].get('id')
                        if task_id:
                            self._task_index[task_id] = task_file

    def _build_sprint_index(self):
        """Build sprint ID -> file path index (hierarchical structure)."""
        # Traverse hierarchical structure
        for track_slug, _ in self.fs.dir_manager.list_tracks():
            for sprint_slug, _ in self.fs.dir_manager.list_sprints(track_slug):
                paths = self.fs.dir_manager.get_paths(track_slug, sprint_slug)
                sprint_file = paths.sprint_path("sprint.yaml")

                if not sprint_file.exists():
                    continue

                # Track file mtime
                self._file_mtimes[sprint_file] = sprint_file.stat().st_mtime

                # Load and index sprint
                data = load_yaml(sprint_file)
                if data and 'sprint' in data:
                    sprint_id = data['sprint'].get('id')
                    if sprint_id:
                        self._sprint_index[sprint_id] = sprint_file

    def _build_track_index(self):
        """Build track ID -> file path index (hierarchical structure)."""
        # Traverse hierarchical structure
        for track_slug, _ in self.fs.dir_manager.list_tracks():
            paths = self.fs.dir_manager.get_paths(track_slug)
            track_file = paths.track_path("track.yaml")

            if not track_file.exists():
                continue

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
        Load specific task from file (hierarchical structure).

        Args:
            file_path: Path to task.yaml file
            task_id: Task ID to find

        Returns:
            Task dict, or None if not found
        """
        data = load_yaml(file_path)

        # New hierarchical format: single task per file
        if data and 'task' in data:
            task = data['task']
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
            if task_id not in self._reverse_dep_graph:
                self._reverse_dep_graph[task_id] = []

            # Process dependencies (forward dependencies)
            deps = task.get('dependencies', [])
            for dep in deps:
                # Handle both dict format (new) and string format (legacy)
                if isinstance(dep, dict):
                    # New format: {"type": "task", "target_id": "task-001", ...}
                    target_id = dep.get('target_id')
                elif isinstance(dep, str):
                    # Legacy format: "task-001"
                    target_id = dep
                else:
                    continue

                if target_id:
                    # Add to dependency graph
                    if target_id not in self._dep_graph[task_id]:
                        self._dep_graph[task_id].append(target_id)

                    # Add to reverse graph
                    if target_id not in self._reverse_dep_graph:
                        self._reverse_dep_graph[target_id] = []
                    if task_id not in self._reverse_dep_graph[target_id]:
                        self._reverse_dep_graph[target_id].append(task_id)

            # Process depended_on_by (reverse dependencies from v2.0)
            # This ensures reverse graph includes cached information
            depended_on_by = task.get('depended_on_by', [])
            for dependent_id in depended_on_by:
                if dependent_id not in self._reverse_dep_graph[task_id]:
                    self._reverse_dep_graph[task_id].append(dependent_id)

        # Process sprints
        for sprint in self.get_all_sprints():
            sprint_id = sprint.get('id')
            if not sprint_id:
                continue

            # Initialize lists
            if sprint_id not in self._dep_graph:
                self._dep_graph[sprint_id] = []
            if sprint_id not in self._reverse_dep_graph:
                self._reverse_dep_graph[sprint_id] = []

            # Process dependencies (forward dependencies)
            # Note: Sprints use 'development_gates' not 'dependencies'
            deps = sprint.get('development_gates', sprint.get('dependencies', []))
            for dep in deps:
                # Handle both dict format (new) and string format (legacy)
                if isinstance(dep, dict):
                    # New format: {"type": "sprint", "target_id": "sprint-001", ...}
                    target_id = dep.get('target_id')
                elif isinstance(dep, str):
                    # Legacy format: "sprint-001"
                    target_id = dep
                else:
                    continue

                if target_id:
                    if target_id not in self._dep_graph[sprint_id]:
                        self._dep_graph[sprint_id].append(target_id)

                    if target_id not in self._reverse_dep_graph:
                        self._reverse_dep_graph[target_id] = []
                    if sprint_id not in self._reverse_dep_graph[target_id]:
                        self._reverse_dep_graph[target_id].append(sprint_id)

            # Process depended_on_by (reverse dependencies from v2.0)
            depended_on_by = sprint.get('depended_on_by', [])
            for dependent_id in depended_on_by:
                if dependent_id not in self._reverse_dep_graph[sprint_id]:
                    self._reverse_dep_graph[sprint_id].append(dependent_id)

        # Process tracks
        for track in self.get_all_tracks():
            track_id = track.get('id')
            if not track_id:
                continue

            # Initialize lists
            if track_id not in self._dep_graph:
                self._dep_graph[track_id] = []
            if track_id not in self._reverse_dep_graph:
                self._reverse_dep_graph[track_id] = []

            # Process dependencies (forward dependencies)
            deps = track.get('dependencies', [])
            for dep in deps:
                # Handle both dict format (new) and string format (legacy)
                if isinstance(dep, dict):
                    # New format: {"type": "track", "target_id": "track-001", ...}
                    target_id = dep.get('target_id')
                elif isinstance(dep, str):
                    # Legacy format: "track-001"
                    target_id = dep
                else:
                    continue

                if target_id:
                    if target_id not in self._dep_graph[track_id]:
                        self._dep_graph[track_id].append(target_id)

                    if target_id not in self._reverse_dep_graph:
                        self._reverse_dep_graph[target_id] = []
                    if track_id not in self._reverse_dep_graph[target_id]:
                        self._reverse_dep_graph[target_id].append(track_id)

            # Process depended_on_by (reverse dependencies from v2.0)
            depended_on_by = track.get('depended_on_by', [])
            for dependent_id in depended_on_by:
                if dependent_id not in self._reverse_dep_graph[track_id]:
                    self._reverse_dep_graph[track_id].append(dependent_id)

        # Save to disk for faster subsequent loads
        self._save_to_disk()
