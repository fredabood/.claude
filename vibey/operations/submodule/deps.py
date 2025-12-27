"""
Cross-repo dependency tracking for submodule integration.

Implements dependency tracking across repo boundaries.

Design reference: SUBMODULE_ISOLATION_AND_PUSHDOWN.md

Key principle: Dependencies stored ONLY in parent repo via ExternalBlockerInfo.
Submodule has no knowledge of being depended upon (isolation principle).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

import yaml

from vibey.roadmap.models.cross_repo import (
    ExternalBlockerInfo,
    ExternalBlockerType,
)


class DependencyType(str, Enum):
    """Type of cross-repo dependency."""

    COMPLETION = "completion"  # Wait for task completion
    ARTIFACT = "artifact"  # Wait for artifact generation
    MILESTONE = "milestone"  # Wait for milestone/sprint


@dataclass
class CyclePath:
    """Represents a dependency cycle path."""

    path: list[tuple[str, str]]  # List of (repo_path, task_id) tuples
    description: str = ""

    def __str__(self) -> str:
        parts = [f"{repo}:{task}" for repo, task in self.path]
        return " -> ".join(parts)


@dataclass
class DependencyNode:
    """Node in the dependency graph."""

    repo_path: str  # "" for parent repo
    task_id: str
    title: str = ""
    status: str = "unknown"


@dataclass
class DependencyEdge:
    """Edge in the dependency graph."""

    from_node: DependencyNode
    to_node: DependencyNode
    dependency_type: DependencyType = DependencyType.COMPLETION
    is_satisfied: bool = False


@dataclass
class DependencyGraph:
    """Graph of cross-repo dependencies."""

    nodes: list[DependencyNode] = field(default_factory=list)
    edges: list[DependencyEdge] = field(default_factory=list)
    root_task_id: Optional[str] = None

    def add_node(self, node: DependencyNode) -> None:
        """Add node if not already present."""
        key = (node.repo_path, node.task_id)
        if not any((n.repo_path, n.task_id) == key for n in self.nodes):
            self.nodes.append(node)

    def add_edge(self, edge: DependencyEdge) -> None:
        """Add edge to graph."""
        self.add_node(edge.from_node)
        self.add_node(edge.to_node)
        self.edges.append(edge)


@dataclass
class ValidationError:
    """Validation error for dependencies."""

    task_id: str
    blocker_id: str
    error_type: str
    message: str


class DependencyResolver:
    """
    Resolves and tracks dependencies across repo boundaries.

    All dependency data stored in parent repo via ExternalBlockerInfo.
    Submodules remain isolated with no knowledge of dependencies.
    """

    def __init__(self, parent_repo_path: Optional[Path] = None):
        """
        Initialize DependencyResolver.

        Args:
            parent_repo_path: Path to parent repository. Defaults to cwd.
        """
        self.parent_repo_path = Path(parent_repo_path) if parent_repo_path else Path.cwd()
        self.parent_vibey = self.parent_repo_path / ".vibey"
        self.parent_roadmap = self.parent_vibey / "roadmap"
        self.parent_tasks = self.parent_roadmap / "tasks"

    def add_dependency(
        self,
        parent_task_id: str,
        submodule_path: str,
        submodule_task_ref: str,
        dep_type: DependencyType = DependencyType.COMPLETION,
        description: Optional[str] = None,
    ) -> ExternalBlockerInfo:
        """
        Add a cross-repo dependency to a parent task.

        Args:
            parent_task_id: ULID of parent task.
            submodule_path: Path to submodule.
            submodule_task_ref: Task reference (ULID or human-readable).
            dep_type: Type of dependency.
            description: Optional description.

        Returns:
            Created ExternalBlockerInfo.
        """
        submodule_path = submodule_path.replace("\\", "/").strip("/")

        # Load parent task
        parent_task_path = self.parent_tasks / f"{parent_task_id}.yaml"
        if not parent_task_path.exists():
            raise FileNotFoundError(f"Parent task not found: {parent_task_id}")

        with open(parent_task_path) as f:
            data = yaml.safe_load(f)

        task = data.get("task", data)

        # Determine if ref is ULID (26 chars, alphanumeric)
        is_ulid = len(submodule_task_ref) == 26 and submodule_task_ref.isalnum()

        # Create ExternalBlockerInfo
        blocker_id = f"{submodule_path}:{submodule_task_ref}"
        blocker = {
            "blocker_id": blocker_id,
            "blocker_type": ExternalBlockerType.SUBMODULE_TASK.value,
            "resolved_to": submodule_task_ref if is_ulid else None,
            "required_status": "completed" if dep_type == DependencyType.COMPLETION else "in_progress",
            "submodule_path": submodule_path,
            "current_status": None,
            "is_satisfied": False,
            "last_synced": None,
            "description": description or f"Depends on {submodule_task_ref} in {submodule_path}",
        }

        # Add to blocked_by list
        blocked_by = task.get("blocked_by", [])
        blocked_by.append(blocker)
        task["blocked_by"] = blocked_by
        task["blocked"] = True

        # Save task
        with open(parent_task_path, "w") as f:
            yaml.dump({"task": task}, f, default_flow_style=False, sort_keys=False)

        return ExternalBlockerInfo(
            blocker_id=blocker_id,
            blocker_type=ExternalBlockerType.SUBMODULE_TASK,
            resolved_to=submodule_task_ref if is_ulid else None,
            required_status=blocker["required_status"],
            submodule_path=submodule_path,
            description=blocker["description"],
        )

    def resolve_dependency(
        self,
        parent_task_id: str,
        blocker_id: str,
        submodule_task_id: str,
    ) -> Optional[ExternalBlockerInfo]:
        """
        Resolve a dependency by linking to a specific submodule task.

        Args:
            parent_task_id: ULID of parent task.
            blocker_id: Blocker ID to resolve.
            submodule_task_id: ULID of submodule task to link.

        Returns:
            Updated ExternalBlockerInfo, or None if not found.
        """
        parent_task_path = self.parent_tasks / f"{parent_task_id}.yaml"
        if not parent_task_path.exists():
            return None

        with open(parent_task_path) as f:
            data = yaml.safe_load(f)

        task = data.get("task", data)
        blocked_by = task.get("blocked_by", [])

        # Find and update the blocker
        updated_blocker = None
        for blocker in blocked_by:
            if blocker.get("blocker_id") == blocker_id:
                blocker["resolved_to"] = submodule_task_id
                # Update blocker_id to include ULID
                submodule_path = blocker.get("submodule_path", "")
                blocker["blocker_id"] = f"{submodule_path}:{submodule_task_id}"
                updated_blocker = ExternalBlockerInfo(
                    blocker_id=blocker["blocker_id"],
                    blocker_type=ExternalBlockerType(blocker.get("blocker_type", "submodule_task")),
                    resolved_to=submodule_task_id,
                    required_status=blocker.get("required_status", "completed"),
                    submodule_path=submodule_path,
                    description=blocker.get("description"),
                )
                break

        if updated_blocker:
            task["blocked_by"] = blocked_by
            with open(parent_task_path, "w") as f:
                yaml.dump({"task": task}, f, default_flow_style=False, sort_keys=False)

        return updated_blocker

    def check_satisfied(self, blocker: ExternalBlockerInfo) -> bool:
        """
        Check if an external blocker is satisfied.

        Args:
            blocker: ExternalBlockerInfo to check.

        Returns:
            True if dependency is satisfied.
        """
        if not blocker.resolved_to or not blocker.submodule_path:
            return False

        # Read submodule task status
        submodule_abs = self.parent_repo_path / blocker.submodule_path
        task_file = submodule_abs / ".vibey" / "roadmap" / "tasks" / f"{blocker.resolved_to}.yaml"

        if not task_file.exists():
            return False

        try:
            with open(task_file) as f:
                data = yaml.safe_load(f) or {}
            task = data.get("task", data)
            current_status = task.get("status")

            if not current_status:
                return False

            # Update blocker state
            blocker.current_status = current_status
            blocker.last_synced = datetime.now(timezone.utc)

            # Check if satisfied
            return blocker.check_satisfied()
        except Exception:
            return False

    def detect_cycles(self, start_task_id: str) -> list[CyclePath]:
        """
        Detect dependency cycles starting from a task.

        Args:
            start_task_id: Task ID to start from.

        Returns:
            List of cycle paths found.
        """
        cycles = []
        visited = set()
        path = []

        def visit(repo_path: str, task_id: str) -> None:
            key = (repo_path, task_id)

            # Check for cycle
            if key in visited:
                # Find where cycle starts
                try:
                    cycle_start = path.index(key)
                    cycle_path = path[cycle_start:] + [key]
                    cycles.append(CyclePath(
                        path=cycle_path,
                        description=f"Cycle detected: {' -> '.join(f'{r}:{t}' for r, t in cycle_path)}",
                    ))
                except ValueError:
                    pass
                return

            visited.add(key)
            path.append(key)

            # Get dependencies for this task
            deps = self._get_task_dependencies(repo_path, task_id)
            for dep_repo, dep_task in deps:
                visit(dep_repo, dep_task)

            path.pop()

        visit("", start_task_id)
        return cycles

    def _get_task_dependencies(self, repo_path: str, task_id: str) -> list[tuple[str, str]]:
        """Get external dependencies for a task."""
        if repo_path:
            task_file = self.parent_repo_path / repo_path / ".vibey" / "roadmap" / "tasks" / f"{task_id}.yaml"
        else:
            task_file = self.parent_tasks / f"{task_id}.yaml"

        if not task_file.exists():
            return []

        try:
            with open(task_file) as f:
                data = yaml.safe_load(f) or {}
            task = data.get("task", data)

            deps = []
            for blocker in task.get("blocked_by", []):
                if blocker.get("blocker_type") == "submodule_task":
                    submodule_path = blocker.get("submodule_path", "")
                    resolved_to = blocker.get("resolved_to")
                    if resolved_to:
                        deps.append((submodule_path, resolved_to))

            return deps
        except Exception:
            return []

    def build_dependency_graph(self, task_id: str) -> DependencyGraph:
        """
        Build a dependency graph starting from a task.

        Args:
            task_id: Root task ID.

        Returns:
            DependencyGraph with nodes and edges.
        """
        graph = DependencyGraph(root_task_id=task_id)
        visited = set()

        def visit(repo_path: str, task_id: str) -> DependencyNode:
            key = (repo_path, task_id)
            if key in visited:
                # Return existing node
                for node in graph.nodes:
                    if (node.repo_path, node.task_id) == key:
                        return node
                return DependencyNode(repo_path=repo_path, task_id=task_id)

            visited.add(key)

            # Read task info
            if repo_path:
                task_file = self.parent_repo_path / repo_path / ".vibey" / "roadmap" / "tasks" / f"{task_id}.yaml"
            else:
                task_file = self.parent_tasks / f"{task_id}.yaml"

            title = ""
            status = "unknown"
            blocked_by = []

            if task_file.exists():
                try:
                    with open(task_file) as f:
                        data = yaml.safe_load(f) or {}
                    task = data.get("task", data)
                    title = task.get("title", "")
                    status = task.get("status", "unknown")
                    blocked_by = task.get("blocked_by", [])
                except Exception:
                    pass

            node = DependencyNode(
                repo_path=repo_path,
                task_id=task_id,
                title=title,
                status=status,
            )
            graph.add_node(node)

            # Process dependencies
            for blocker in blocked_by:
                if blocker.get("blocker_type") == "submodule_task":
                    submodule_path = blocker.get("submodule_path", "")
                    resolved_to = blocker.get("resolved_to")
                    if resolved_to:
                        dep_node = visit(submodule_path, resolved_to)
                        edge = DependencyEdge(
                            from_node=node,
                            to_node=dep_node,
                            dependency_type=DependencyType.COMPLETION,
                            is_satisfied=blocker.get("is_satisfied", False),
                        )
                        graph.add_edge(edge)

            return node

        visit("", task_id)
        return graph

    def validate_dependencies(self) -> list[ValidationError]:
        """
        Validate all external dependencies in parent tasks.

        Returns:
            List of validation errors found.
        """
        errors = []

        if not self.parent_tasks.exists():
            return errors

        for task_file in self.parent_tasks.glob("*.yaml"):
            try:
                with open(task_file) as f:
                    data = yaml.safe_load(f) or {}
                task = data.get("task", data)
                task_id = task.get("id", task_file.stem)

                for blocker in task.get("blocked_by", []):
                    if blocker.get("blocker_type") != "submodule_task":
                        continue

                    blocker_id = blocker.get("blocker_id", "")
                    submodule_path = blocker.get("submodule_path")
                    resolved_to = blocker.get("resolved_to")

                    # Check submodule path exists
                    if submodule_path:
                        submodule_abs = self.parent_repo_path / submodule_path
                        if not submodule_abs.exists():
                            errors.append(ValidationError(
                                task_id=task_id,
                                blocker_id=blocker_id,
                                error_type="invalid_path",
                                message=f"Submodule path does not exist: {submodule_path}",
                            ))
                            continue

                    # Check resolved task exists
                    if resolved_to and submodule_path:
                        submodule_task = submodule_abs / ".vibey" / "roadmap" / "tasks" / f"{resolved_to}.yaml"
                        if not submodule_task.exists():
                            errors.append(ValidationError(
                                task_id=task_id,
                                blocker_id=blocker_id,
                                error_type="invalid_task",
                                message=f"Submodule task does not exist: {resolved_to}",
                            ))

            except Exception as e:
                errors.append(ValidationError(
                    task_id=task_file.stem,
                    blocker_id="",
                    error_type="parse_error",
                    message=str(e),
                ))

        return errors

    def remove_dependency(self, parent_task_id: str, blocker_id: str) -> bool:
        """
        Remove a dependency from a parent task.

        Args:
            parent_task_id: ULID of parent task.
            blocker_id: Blocker ID to remove.

        Returns:
            True if removed, False otherwise.
        """
        parent_task_path = self.parent_tasks / f"{parent_task_id}.yaml"
        if not parent_task_path.exists():
            return False

        with open(parent_task_path) as f:
            data = yaml.safe_load(f)

        task = data.get("task", data)
        blocked_by = task.get("blocked_by", [])
        original_count = len(blocked_by)

        blocked_by = [b for b in blocked_by if b.get("blocker_id") != blocker_id]
        task["blocked_by"] = blocked_by
        task["blocked"] = bool(blocked_by)

        with open(parent_task_path, "w") as f:
            yaml.dump({"task": task}, f, default_flow_style=False, sort_keys=False)

        return len(blocked_by) < original_count
