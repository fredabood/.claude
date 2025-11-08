"""
Dependency resolution utilities for roadmap state.

Handles dependency tracking and circular dependency detection.
"""

from typing import List, Dict, Set, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass
import sys

# Add framework to path
framework_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(framework_root))

from roadmap.models import Roadmap, Track, Sprint, Task
from roadmap.serialization import load_roadmap, load_track, load_sprint, load_tasks
from filesystem import FileSystemManager


@dataclass
class DependencyNode:
    """Represents a node in the dependency graph."""

    id: str
    type: str  # "roadmap", "track", "sprint", "task"
    depends_on: List[str]  # List of IDs this node depends on


class DependencyResolver:
    """Resolves dependencies and detects circular dependencies."""

    def __init__(self, root_dir: Optional[Path] = None):
        """
        Initialize dependency resolver.

        Args:
            root_dir: Root directory (defaults to current working directory)
        """
        self.fs = FileSystemManager(root_dir)
        self.dependency_graph: Dict[str, DependencyNode] = {}

    def build_dependency_graph(self) -> Dict[str, DependencyNode]:
        """
        Build complete dependency graph for the roadmap.

        Returns:
            Dictionary mapping object ID to DependencyNode
        """
        self.dependency_graph = {}

        # Load roadmap
        roadmap_path = self.fs.get_roadmap_path()
        if not roadmap_path.exists():
            return self.dependency_graph

        roadmap = load_roadmap(roadmap_path)

        # Add roadmap node
        self.dependency_graph[roadmap.id] = DependencyNode(
            id=roadmap.id,
            type="roadmap",
            depends_on=[],
        )

        # Process each track
        for track_summary in roadmap.tracks:
            track_path = self.fs.get_track_path(track_summary.id)
            if not track_path.exists():
                continue

            track = load_track(track_path)
            self._add_track_dependencies(track)

        return self.dependency_graph

    def _add_track_dependencies(self, track: Track):
        """Add track and its sprints to dependency graph."""
        # Add track dependencies
        depends_on = [dep.target_id for dep in track.dependencies]

        self.dependency_graph[track.id] = DependencyNode(
            id=track.id,
            type="track",
            depends_on=depends_on,
        )

        # Process each sprint in track
        for sprint_summary in track.sprints:
            sprint_path = self.fs.get_sprint_path(sprint_summary.id)
            if not sprint_path.exists():
                continue

            sprint = load_sprint(sprint_path)
            self._add_sprint_dependencies(sprint)

    def _add_sprint_dependencies(self, sprint: Sprint):
        """Add sprint and its tasks to dependency graph."""
        # Add sprint development gates (external dependencies)
        depends_on = [dep.target_id for dep in sprint.development_gates]

        self.dependency_graph[sprint.id] = DependencyNode(
            id=sprint.id,
            type="sprint",
            depends_on=depends_on,
        )

        # Process tasks
        tasks_path = self.fs.get_tasks_path(sprint.id)
        if not tasks_path.exists():
            return

        tasks = load_tasks(tasks_path)
        for task in tasks:
            self._add_task_dependencies(task)

    def _add_task_dependencies(self, task: Task):
        """Add task to dependency graph."""
        # Only add development tasks to the graph
        # Quality gate tasks are highly isolated and can't be depended on
        if task.is_quality_gate():
            return

        depends_on = [dep.target_id for dep in task.dependencies]

        self.dependency_graph[task.id] = DependencyNode(
            id=task.id,
            type="task",
            depends_on=depends_on,
        )

    def detect_circular_dependencies(self) -> List[List[str]]:
        """
        Detect circular dependencies in the graph.

        Returns:
            List of circular dependency cycles (each cycle is a list of IDs)
        """
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node_id: str, path: List[str]) -> bool:
            """DFS to detect cycles."""
            if node_id not in self.dependency_graph:
                return False

            if node_id in rec_stack:
                # Found a cycle
                cycle_start = path.index(node_id)
                cycle = path[cycle_start:] + [node_id]
                cycles.append(cycle)
                return True

            if node_id in visited:
                return False

            visited.add(node_id)
            rec_stack.add(node_id)

            node = self.dependency_graph[node_id]
            for dep_id in node.depends_on:
                dfs(dep_id, path + [node_id])

            rec_stack.remove(node_id)
            return False

        # Check each node
        for node_id in self.dependency_graph:
            if node_id not in visited:
                dfs(node_id, [])

        return cycles

    def get_dependencies(self, object_id: str) -> List[str]:
        """
        Get direct dependencies for an object.

        Args:
            object_id: ID of object

        Returns:
            List of dependency IDs
        """
        if object_id not in self.dependency_graph:
            return []

        return self.dependency_graph[object_id].depends_on

    def get_dependents(self, object_id: str) -> List[str]:
        """
        Get objects that depend on this object.

        Args:
            object_id: ID of object

        Returns:
            List of dependent IDs
        """
        dependents = []

        for node_id, node in self.dependency_graph.items():
            if object_id in node.depends_on:
                dependents.append(node_id)

        return dependents

    def get_transitive_dependencies(self, object_id: str) -> Set[str]:
        """
        Get all transitive dependencies for an object.

        Args:
            object_id: ID of object

        Returns:
            Set of all dependency IDs (direct and indirect)
        """
        if object_id not in self.dependency_graph:
            return set()

        visited = set()

        def visit(node_id: str):
            if node_id in visited or node_id not in self.dependency_graph:
                return

            visited.add(node_id)
            node = self.dependency_graph[node_id]

            for dep_id in node.depends_on:
                visit(dep_id)

        # Start DFS from object
        for dep_id in self.dependency_graph[object_id].depends_on:
            visit(dep_id)

        return visited


def resolve_dependencies(root_dir: Optional[Path] = None) -> DependencyResolver:
    """
    Build and return dependency resolver.

    Args:
        root_dir: Root directory (defaults to current working directory)

    Returns:
        DependencyResolver with built graph
    """
    resolver = DependencyResolver(root_dir)
    resolver.build_dependency_graph()
    return resolver


def detect_circular_dependencies(root_dir: Optional[Path] = None) -> List[List[str]]:
    """
    Detect circular dependencies in roadmap.

    Args:
        root_dir: Root directory (defaults to current working directory)

    Returns:
        List of circular dependency cycles
    """
    resolver = resolve_dependencies(root_dir)
    return resolver.detect_circular_dependencies()
