"""
Dependency-aware merge ordering for git operations.

This module provides:
- Roadmap dependency graph analysis
- Branch/PR state comparison with dependencies
- Merge order recommendations
- Dependency satisfaction checking
- Override capability for exceptions
"""

import subprocess
import yaml
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set


class DependencyLevel(Enum):
    """Level of dependency relationship."""
    TRACK = "track"
    SPRINT = "sprint"
    TASK = "task"


class MergeRecommendation(Enum):
    """Merge recommendation type."""
    SAFE = "safe"           # All dependencies satisfied
    WARNING = "warning"     # Dependencies exist but not blocking
    BLOCKED = "blocked"     # Dependencies must be merged first
    OVERRIDE = "override"   # Blocked but override requested


@dataclass
class DependencyNode:
    """A node in the dependency graph."""
    id: str
    level: DependencyLevel
    name: str
    status: str
    depends_on: List[str] = field(default_factory=list)
    blocks: List[str] = field(default_factory=list)
    branch_name: Optional[str] = None
    pr_number: Optional[int] = None


@dataclass
class DependencyEdge:
    """An edge in the dependency graph."""
    from_id: str
    to_id: str
    dependency_type: str  # 'depends_on', 'blocks', 'blocked_by'
    required_status: str = 'completed'


@dataclass
class MergeOrderItem:
    """An item in the recommended merge order."""
    item_id: str
    level: DependencyLevel
    name: str
    order: int
    branch_name: Optional[str]
    dependencies_satisfied: bool
    blocking_dependencies: List[str] = field(default_factory=list)
    recommendation: MergeRecommendation = MergeRecommendation.SAFE


@dataclass
class DependencyCheckResult:
    """Result of checking dependencies for a branch."""
    branch_name: str
    item_id: Optional[str]
    level: Optional[DependencyLevel]
    recommendation: MergeRecommendation
    satisfied_dependencies: List[str]
    unsatisfied_dependencies: List[str]
    message: str
    can_merge: bool


@dataclass
class MergeOrderReport:
    """Complete merge order recommendation report."""
    items: List[MergeOrderItem]
    dependency_graph: Dict[str, List[str]]
    blocked_merges: List[str]
    warnings: List[str]
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class MergeOrderAnalyzer:
    """
    Analyze roadmap dependencies and recommend merge order.

    Builds a dependency graph from roadmap files and compares
    with git branch state to suggest optimal merge sequence.
    """

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.roadmap_root = self.repo_path / ".vibey" / "roadmap"
        self._dependency_graph: Dict[str, DependencyNode] = {}
        self._edges: List[DependencyEdge] = []

    def _run_git(self, args: List[str], check: bool = True) -> Tuple[bool, str, str]:
        """Run a git command and return (success, stdout, stderr)."""
        try:
            result = subprocess.run(
                ['git'] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=check
            )
            return True, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            if check:
                raise
            return False, e.stdout, e.stderr

    def _load_yaml_file(self, file_path: Path) -> Optional[dict]:
        """Load and parse a YAML file."""
        try:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    return yaml.safe_load(f)
        except Exception:
            pass
        return None

    def _extract_item_id_from_branch(self, branch_name: str) -> Optional[Tuple[str, DependencyLevel]]:
        """
        Extract roadmap item ID from branch name.

        Recognizes patterns like:
        - feature/task-001
        - sprint/sprint-1
        - track/my-track
        - git-integration-3-task-004
        """
        import re

        # Strip common prefixes first
        name = branch_name
        for prefix in ['feature/', 'sprint/', 'track/', 'bugfix/', 'hotfix/']:
            if name.startswith(prefix):
                name = name[len(prefix):]
                break

        # Pattern: *-task-NNN (task ID)
        task_match = re.search(r'([\w-]+-task-\d+)', name)
        if task_match:
            return task_match.group(1), DependencyLevel.TASK

        # Pattern: *-sprint-N or sprint-N (sprint ID)
        sprint_match = re.search(r'([\w-]+-\d+)(?!-task)', name)
        if sprint_match and 'sprint' in name.lower():
            return sprint_match.group(1), DependencyLevel.SPRINT

        # Pattern: track name (remaining after prefix strip)
        if branch_name.startswith('track/') or branch_name.startswith('feature/track-'):
            return name, DependencyLevel.TRACK

        return None

    def _build_dependency_graph(self) -> None:
        """Build the dependency graph from roadmap files."""
        self._dependency_graph = {}
        self._edges = []

        # Load tracks
        for track_dir in self.roadmap_root.iterdir():
            if not track_dir.is_dir() or track_dir.name.startswith('.'):
                continue

            track_file = track_dir / "track.yaml"
            if not track_file.exists():
                continue

            data = self._load_yaml_file(track_file)
            if not data or 'track' not in data:
                continue

            track = data['track']
            track_id = track.get('id', track_dir.name)

            node = DependencyNode(
                id=track_id,
                level=DependencyLevel.TRACK,
                name=track.get('name', track_id),
                status=track.get('status', 'not_started'),
                depends_on=[d if isinstance(d, str) else d.get('dependency_id', '')
                           for d in track.get('depends_on', []) + track.get('blocked_by', [])],
                blocks=[b if isinstance(b, str) else b.get('target_id', '')
                       for b in track.get('blocks', [])]
            )
            self._dependency_graph[track_id] = node

            # Add edges
            for dep in node.depends_on:
                if dep:
                    self._edges.append(DependencyEdge(
                        from_id=track_id,
                        to_id=dep,
                        dependency_type='depends_on'
                    ))

            # Load sprints
            for sprint_dir in track_dir.iterdir():
                if not sprint_dir.is_dir() or sprint_dir.name.startswith('.') or sprint_dir.name == 'context':
                    continue

                sprint_file = sprint_dir / "sprint.yaml"
                if not sprint_file.exists():
                    continue

                sprint_data = self._load_yaml_file(sprint_file)
                if not sprint_data or 'sprint' not in sprint_data:
                    continue

                sprint = sprint_data['sprint']
                sprint_id = sprint.get('id', sprint_dir.name)

                sprint_node = DependencyNode(
                    id=sprint_id,
                    level=DependencyLevel.SPRINT,
                    name=sprint.get('name', sprint_id),
                    status=sprint.get('status', 'not_started'),
                    depends_on=[d if isinstance(d, str) else d.get('dependency_id', '')
                               for d in sprint.get('dependencies', []) + sprint.get('blocked_by', [])],
                    blocks=[]
                )
                self._dependency_graph[sprint_id] = sprint_node

                for dep in sprint_node.depends_on:
                    if dep:
                        self._edges.append(DependencyEdge(
                            from_id=sprint_id,
                            to_id=dep,
                            dependency_type='depends_on'
                        ))

                # Load tasks
                for task_dir in sprint_dir.iterdir():
                    if not task_dir.is_dir() or task_dir.name.startswith('.'):
                        continue

                    task_file = task_dir / "task.yaml"
                    if not task_file.exists():
                        continue

                    task_data = self._load_yaml_file(task_file)
                    if not task_data or 'task' not in task_data:
                        continue

                    task = task_data['task']
                    task_id = task.get('id', task_dir.name)

                    task_node = DependencyNode(
                        id=task_id,
                        level=DependencyLevel.TASK,
                        name=task.get('title', task.get('name', task_id)),
                        status=task.get('status', 'not_started'),
                        depends_on=[d if isinstance(d, str) else d.get('target_id', '')
                                   for d in task.get('dependencies', []) + task.get('blocked_by', [])],
                        blocks=[b if isinstance(b, str) else b.get('target_id', '')
                               for b in task.get('blocks', [])]
                    )
                    self._dependency_graph[task_id] = task_node

                    for dep in task_node.depends_on:
                        if dep:
                            self._edges.append(DependencyEdge(
                                from_id=task_id,
                                to_id=dep,
                                dependency_type='depends_on'
                            ))

    def _get_branches_with_items(self) -> Dict[str, str]:
        """
        Get mapping of branch names to roadmap item IDs.

        Returns:
            Dict mapping branch name to item ID
        """
        branch_to_item = {}

        success, stdout, _ = self._run_git(['branch', '-a', '--format=%(refname:short)'], check=False)
        if not success:
            return branch_to_item

        for line in stdout.strip().split('\n'):
            branch = line.strip()
            if not branch:
                continue

            result = self._extract_item_id_from_branch(branch)
            if result:
                item_id, _ = result
                if item_id in self._dependency_graph:
                    branch_to_item[branch] = item_id
                    self._dependency_graph[item_id].branch_name = branch

        return branch_to_item

    def _is_dependency_satisfied(self, dep_id: str) -> bool:
        """
        Check if a dependency is satisfied (completed).

        Args:
            dep_id: ID of the dependency

        Returns:
            True if dependency is completed
        """
        if dep_id not in self._dependency_graph:
            # Unknown dependency - assume satisfied
            return True

        node = self._dependency_graph[dep_id]
        return node.status == 'completed'

    def _topological_sort(self) -> List[str]:
        """
        Perform topological sort on dependency graph.

        Returns:
            List of item IDs in dependency order (dependencies first)
        """
        # Build adjacency list and in-degree count
        in_degree = {node_id: 0 for node_id in self._dependency_graph}
        adjacency = {node_id: [] for node_id in self._dependency_graph}

        for edge in self._edges:
            if edge.to_id in adjacency and edge.from_id in in_degree:
                adjacency[edge.to_id].append(edge.from_id)
                in_degree[edge.from_id] += 1

        # Kahn's algorithm
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            node_id = queue.pop(0)
            result.append(node_id)

            for dependent in adjacency.get(node_id, []):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        return result

    def get_merge_order(self, include_completed: bool = False) -> MergeOrderReport:
        """
        Get recommended merge order for all branches.

        Args:
            include_completed: Include completed items in the order

        Returns:
            MergeOrderReport with ordered items and recommendations
        """
        self._build_dependency_graph()
        self._get_branches_with_items()

        # Get topological order
        topo_order = self._topological_sort()

        items = []
        blocked_merges = []
        warnings = []

        for order, item_id in enumerate(topo_order):
            node = self._dependency_graph[item_id]

            # Skip completed unless requested
            if not include_completed and node.status == 'completed':
                continue

            # Skip items without branches
            if not node.branch_name:
                continue

            # Check dependencies
            unsatisfied = [dep for dep in node.depends_on if not self._is_dependency_satisfied(dep)]

            if unsatisfied:
                recommendation = MergeRecommendation.BLOCKED
                blocked_merges.append(item_id)
            elif node.depends_on:
                recommendation = MergeRecommendation.WARNING
                warnings.append(f"{item_id} has dependencies that should be verified")
            else:
                recommendation = MergeRecommendation.SAFE

            items.append(MergeOrderItem(
                item_id=item_id,
                level=node.level,
                name=node.name,
                order=order,
                branch_name=node.branch_name,
                dependencies_satisfied=len(unsatisfied) == 0,
                blocking_dependencies=unsatisfied,
                recommendation=recommendation
            ))

        # Build simple dependency graph for output
        dep_graph = {
            node_id: node.depends_on
            for node_id, node in self._dependency_graph.items()
            if node.depends_on
        }

        return MergeOrderReport(
            items=items,
            dependency_graph=dep_graph,
            blocked_merges=blocked_merges,
            warnings=warnings
        )

    def check_branch_dependencies(self, branch_name: str,
                                  allow_override: bool = False) -> DependencyCheckResult:
        """
        Check if a branch's dependencies are satisfied for merging.

        Args:
            branch_name: Name of the branch to check
            allow_override: Allow merge even with unsatisfied dependencies

        Returns:
            DependencyCheckResult
        """
        self._build_dependency_graph()

        # Extract item ID from branch
        result = self._extract_item_id_from_branch(branch_name)
        if not result:
            return DependencyCheckResult(
                branch_name=branch_name,
                item_id=None,
                level=None,
                recommendation=MergeRecommendation.SAFE,
                satisfied_dependencies=[],
                unsatisfied_dependencies=[],
                message="Branch does not match any roadmap item - safe to merge",
                can_merge=True
            )

        item_id, level = result

        if item_id not in self._dependency_graph:
            return DependencyCheckResult(
                branch_name=branch_name,
                item_id=item_id,
                level=level,
                recommendation=MergeRecommendation.SAFE,
                satisfied_dependencies=[],
                unsatisfied_dependencies=[],
                message=f"Item {item_id} not found in roadmap - safe to merge",
                can_merge=True
            )

        node = self._dependency_graph[item_id]
        satisfied = []
        unsatisfied = []

        for dep_id in node.depends_on:
            if self._is_dependency_satisfied(dep_id):
                satisfied.append(dep_id)
            else:
                unsatisfied.append(dep_id)

        if unsatisfied:
            if allow_override:
                recommendation = MergeRecommendation.OVERRIDE
                can_merge = True
                message = f"OVERRIDE: Merging despite unsatisfied dependencies: {', '.join(unsatisfied)}"
            else:
                recommendation = MergeRecommendation.BLOCKED
                can_merge = False
                message = f"BLOCKED: Dependencies not satisfied: {', '.join(unsatisfied)}"
        elif satisfied:
            recommendation = MergeRecommendation.WARNING
            can_merge = True
            message = f"OK: All {len(satisfied)} dependencies satisfied"
        else:
            recommendation = MergeRecommendation.SAFE
            can_merge = True
            message = "OK: No dependencies - safe to merge"

        return DependencyCheckResult(
            branch_name=branch_name,
            item_id=item_id,
            level=level,
            recommendation=recommendation,
            satisfied_dependencies=satisfied,
            unsatisfied_dependencies=unsatisfied,
            message=message,
            can_merge=can_merge
        )

    def format_merge_order(self, report: MergeOrderReport) -> str:
        """
        Format merge order report for display.

        Args:
            report: MergeOrderReport to format

        Returns:
            Formatted string
        """
        lines = []
        lines.append("=" * 60)
        lines.append("Recommended Merge Order")
        lines.append(f"Generated: {report.generated_at.isoformat()}")
        lines.append("=" * 60)
        lines.append("")

        if not report.items:
            lines.append("No branches found matching roadmap items")
            return "\n".join(lines)

        # Group by recommendation
        safe_items = [i for i in report.items if i.recommendation == MergeRecommendation.SAFE]
        warning_items = [i for i in report.items if i.recommendation == MergeRecommendation.WARNING]
        blocked_items = [i for i in report.items if i.recommendation == MergeRecommendation.BLOCKED]

        if safe_items:
            lines.append("✅ Safe to Merge (no blocking dependencies):")
            for item in safe_items:
                lines.append(f"   {item.order + 1}. [{item.level.value}] {item.branch_name}")
                lines.append(f"      → {item.name}")
            lines.append("")

        if warning_items:
            lines.append("⚠️  Merge with Caution (has dependencies):")
            for item in warning_items:
                lines.append(f"   {item.order + 1}. [{item.level.value}] {item.branch_name}")
                lines.append(f"      → {item.name}")
            lines.append("")

        if blocked_items:
            lines.append("🚫 Blocked (dependencies not satisfied):")
            for item in blocked_items:
                lines.append(f"   {item.order + 1}. [{item.level.value}] {item.branch_name}")
                lines.append(f"      → {item.name}")
                lines.append(f"      Blocked by: {', '.join(item.blocking_dependencies)}")
            lines.append("")

        if report.warnings:
            lines.append("Warnings:")
            for w in report.warnings:
                lines.append(f"  - {w}")

        return "\n".join(lines)

    def format_dependency_check(self, result: DependencyCheckResult) -> str:
        """
        Format dependency check result for display.

        Args:
            result: DependencyCheckResult to format

        Returns:
            Formatted string
        """
        lines = []
        lines.append("=" * 60)
        lines.append(f"Dependency Check: {result.branch_name}")
        lines.append("=" * 60)
        lines.append("")

        status_icon = {
            MergeRecommendation.SAFE: "✅",
            MergeRecommendation.WARNING: "⚠️",
            MergeRecommendation.BLOCKED: "🚫",
            MergeRecommendation.OVERRIDE: "⚡"
        }.get(result.recommendation, "❓")

        lines.append(f"{status_icon} {result.message}")
        lines.append("")

        if result.item_id:
            lines.append(f"Roadmap Item: {result.item_id} ({result.level.value if result.level else 'unknown'})")
            lines.append("")

        if result.satisfied_dependencies:
            lines.append("✅ Satisfied Dependencies:")
            for dep in result.satisfied_dependencies:
                lines.append(f"   - {dep}")
            lines.append("")

        if result.unsatisfied_dependencies:
            lines.append("❌ Unsatisfied Dependencies:")
            for dep in result.unsatisfied_dependencies:
                lines.append(f"   - {dep}")
            lines.append("")

        lines.append(f"Can Merge: {'Yes' if result.can_merge else 'No'}")

        return "\n".join(lines)


# Convenience functions

def get_merge_order(repo_path: str = ".", include_completed: bool = False) -> MergeOrderReport:
    """
    Get recommended merge order for all branches.

    Args:
        repo_path: Path to repository
        include_completed: Include completed items

    Returns:
        MergeOrderReport
    """
    analyzer = MergeOrderAnalyzer(repo_path)
    return analyzer.get_merge_order(include_completed)


def check_branch_dependencies(branch_name: str, repo_path: str = ".",
                             allow_override: bool = False) -> DependencyCheckResult:
    """
    Check if a branch's dependencies are satisfied.

    Args:
        branch_name: Branch to check
        repo_path: Path to repository
        allow_override: Allow merge override

    Returns:
        DependencyCheckResult
    """
    analyzer = MergeOrderAnalyzer(repo_path)
    return analyzer.check_branch_dependencies(branch_name, allow_override)


def format_merge_order_report(report: MergeOrderReport) -> str:
    """
    Format merge order report for display.

    Args:
        report: MergeOrderReport

    Returns:
        Formatted string
    """
    analyzer = MergeOrderAnalyzer()
    return analyzer.format_merge_order(report)


def format_dependency_check_result(result: DependencyCheckResult) -> str:
    """
    Format dependency check result for display.

    Args:
        result: DependencyCheckResult

    Returns:
        Formatted string
    """
    analyzer = MergeOrderAnalyzer()
    return analyzer.format_dependency_check(result)
