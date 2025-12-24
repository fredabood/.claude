"""
CriterionDependencyGraph - Build and analyze dependency graphs from ticket criteria.

This module provides a graph-based view of ticket dependencies using networkx.
It enables analysis of how tickets relate to each other through their criteria,
particularly CompletableTarget criteria that represent dependencies.

Key Features:
- Build dependency graphs from all tickets with criteria
- Find upstream criteria (what a ticket depends on)
- Find downstream criteria (what depends on a ticket)
- Analyze file-based impacts (which criteria affected by file changes)
- Compute transitive closures for dependency chains

Usage:
    from vibey.services.implementation import CriterionDependencyGraph
    from pathlib import Path

    # Build graph from roadmap
    graph = CriterionDependencyGraph(roadmap_root=Path(".vibey/roadmap"))
    graph.build()

    # Get upstream dependencies
    upstream = graph.get_upstream_criteria("01KC...")

    # Get downstream dependents
    downstream = graph.get_downstream_criteria("01KC...")

    # Find affected criteria by file changes
    affected = graph.get_affected_criteria(["src/foo.py", "tests/test_foo.py"])

    # Get all transitively connected tickets
    closure = graph.get_transitive_closure("01KC...")

Design Reference:
- Context System V2: Dependency Analysis
- ADR-0001: ULID Identifiers
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

try:
    import networkx as nx
except ImportError:
    raise ImportError(
        "networkx is required for CriterionDependencyGraph. "
        "Install with: pip install networkx"
    )

from vibey.roadmap.models.ticket.completable import Criterion
from vibey.roadmap.models.ticket.enums import CriterionTargetType, TicketStatus
from vibey.roadmap.models.ticket.targets import (
    ArtifactTarget,
    CompletableTarget,
    FileExistsTarget,
)
from vibey.roadmap.database.connection import get_connection

logger = logging.getLogger(__name__)


# =============================================================================
# DATA MODELS
# =============================================================================


@dataclass
class CriterionRef:
    """
    Reference to a criterion with context for dependency analysis.

    Captures all relevant information about a criterion needed for
    dependency graph operations without requiring the full ticket model.

    Attributes:
        ticket_id: ULID of the ticket containing this criterion
        criterion_index: Index of the criterion in the ticket's criteria list
        criterion_type: Type of the criterion target (completable, file_exists, etc.)
        description: Human-readable description of the criterion
        file_refs: List of file paths referenced by this criterion (if applicable)
        status: Whether the criterion is currently met

    Example:
        >>> ref = CriterionRef(
        ...     ticket_id="01KCZF73PX9YNKWXKYVARY89N3",
        ...     criterion_index=0,
        ...     criterion_type=CriterionTargetType.COMPLETABLE,
        ...     description="Task 001 must complete",
        ...     file_refs=[],
        ...     status=False,
        ... )
    """

    ticket_id: str
    criterion_index: int
    criterion_type: CriterionTargetType
    description: str
    file_refs: List[str] = field(default_factory=list)
    status: bool = False

    @property
    def id(self) -> str:
        """Unique identifier for this criterion reference."""
        return f"{self.ticket_id}:{self.criterion_index}"

    def __hash__(self) -> int:
        """Hash based on unique id for set operations."""
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """Equality based on unique id."""
        if not isinstance(other, CriterionRef):
            return False
        return self.id == other.id


# =============================================================================
# DEPENDENCY GRAPH
# =============================================================================


class CriterionDependencyGraph:
    """
    Build and analyze dependency graphs from ticket criteria.

    Uses networkx DiGraph to model dependencies between tickets.
    Edges represent criterion-based dependencies where one ticket's
    completion depends on another ticket reaching a required status.

    Graph Structure:
    - Nodes: Ticket IDs (strings)
    - Edges: Directed from dependent ticket to dependency
    - Edge data includes the CriterionRef that created the dependency

    Attributes:
        root: Path to the roadmap directory (.vibey/roadmap)
        db_path: Path to the SQLite database
        graph: networkx DiGraph of ticket dependencies
        criteria_by_ticket: Mapping of ticket_id to list of CriterionRef
        file_index: Mapping of file paths to affecting CriterionRef objects

    Example:
        >>> graph = CriterionDependencyGraph(Path(".vibey/roadmap"))
        >>> graph.build()
        >>> upstream = graph.get_upstream_criteria("01KC...")
        >>> print(f"Depends on {len(upstream)} criteria")
    """

    def __init__(self, roadmap_root: Path):
        """
        Initialize CriterionDependencyGraph.

        Args:
            roadmap_root: Path to .vibey/roadmap directory

        Raises:
            FileNotFoundError: If database doesn't exist
        """
        self.root = roadmap_root
        self.db_path = roadmap_root / "roadmap.db"

        if not self.db_path.exists():
            # Try parent directory
            alt_path = roadmap_root.parent / "roadmap.db"
            if alt_path.exists():
                self.db_path = alt_path
            else:
                raise FileNotFoundError(
                    f"Database not found at {self.db_path} or {alt_path}"
                )

        # Initialize graph structures
        self.graph: nx.DiGraph = nx.DiGraph()
        self.criteria_by_ticket: Dict[str, List[CriterionRef]] = {}
        self.file_index: Dict[str, List[CriterionRef]] = {}

        logger.debug(f"CriterionDependencyGraph initialized with db: {self.db_path}")

    def build(self) -> "CriterionDependencyGraph":
        """
        Build dependency graph from all tickets with criteria.

        Scans all tickets in the database, extracts their criteria,
        and builds a directed graph of dependencies.

        Returns:
            Self for method chaining.

        Example:
            >>> graph = CriterionDependencyGraph(path).build()
            >>> print(f"Graph has {graph.graph.number_of_nodes()} nodes")
        """
        # Clear existing state
        self.graph.clear()
        self.criteria_by_ticket.clear()
        self.file_index.clear()

        # Load all tickets and their criteria
        tickets_with_criteria = self._load_tickets_with_criteria()

        for ticket_id, criteria in tickets_with_criteria.items():
            # Add ticket as node
            self.graph.add_node(ticket_id)
            self.criteria_by_ticket[ticket_id] = []

            for idx, criterion in enumerate(criteria):
                criterion_ref = self._create_criterion_ref(ticket_id, idx, criterion)
                self.criteria_by_ticket[ticket_id].append(criterion_ref)

                # Build dependency edges for CompletableTarget criteria
                if isinstance(criterion.target, CompletableTarget):
                    dependency_id = criterion.target.completable_id
                    # Add edge from dependent (ticket_id) to dependency (dependency_id)
                    self.graph.add_edge(
                        ticket_id,
                        dependency_id,
                        criterion=criterion_ref,
                        blocks_transition_to=criterion.blocks_transition_to.value,
                    )

                # Build file index for file-based criteria
                for file_ref in criterion_ref.file_refs:
                    if file_ref not in self.file_index:
                        self.file_index[file_ref] = []
                    self.file_index[file_ref].append(criterion_ref)

        logger.info(
            f"Built dependency graph: {self.graph.number_of_nodes()} nodes, "
            f"{self.graph.number_of_edges()} edges, "
            f"{len(self.file_index)} indexed files"
        )

        return self

    def get_upstream_criteria(self, ticket_id: str) -> List[CriterionRef]:
        """
        Get criteria this ticket depends on.

        Returns all CriterionRef objects from this ticket that reference
        other tickets (i.e., CompletableTarget criteria).

        Args:
            ticket_id: The ticket to get upstream dependencies for

        Returns:
            List of CriterionRef objects representing upstream dependencies.

        Example:
            >>> upstream = graph.get_upstream_criteria("01KC...")
            >>> for ref in upstream:
            ...     print(f"Depends on: {ref.description}")
        """
        upstream: List[CriterionRef] = []

        if ticket_id not in self.criteria_by_ticket:
            return upstream

        for criterion_ref in self.criteria_by_ticket[ticket_id]:
            if criterion_ref.criterion_type == CriterionTargetType.COMPLETABLE:
                upstream.append(criterion_ref)

        return upstream

    def get_downstream_criteria(self, ticket_id: str) -> List[CriterionRef]:
        """
        Get criteria that depend on this ticket.

        Returns CriterionRef objects from other tickets that reference
        this ticket via CompletableTarget criteria.

        Args:
            ticket_id: The ticket to get downstream dependents for

        Returns:
            List of CriterionRef objects that depend on this ticket.

        Example:
            >>> downstream = graph.get_downstream_criteria("01KC...")
            >>> print(f"{len(downstream)} criteria depend on this ticket")
        """
        downstream: List[CriterionRef] = []

        # Find all edges pointing TO this ticket (predecessors)
        if ticket_id not in self.graph:
            return downstream

        for predecessor in self.graph.predecessors(ticket_id):
            edge_data = self.graph.get_edge_data(predecessor, ticket_id)
            if edge_data and "criterion" in edge_data:
                downstream.append(edge_data["criterion"])

        return downstream

    def get_affected_criteria(self, files: List[str]) -> List[CriterionRef]:
        """
        Get criteria affected by file changes.

        Returns all CriterionRef objects that reference any of the
        specified files through FileExistsTarget or ArtifactTarget criteria.

        Args:
            files: List of file paths that have changed

        Returns:
            List of CriterionRef objects affected by the file changes.

        Example:
            >>> affected = graph.get_affected_criteria(["src/foo.py"])
            >>> for ref in affected:
            ...     print(f"Affected: {ref.ticket_id} - {ref.description}")
        """
        affected: List[CriterionRef] = []
        seen: Set[str] = set()  # Track by CriterionRef.id to avoid duplicates

        for file_path in files:
            # Normalize path for matching
            normalized = str(Path(file_path))

            # Direct match
            if normalized in self.file_index:
                for ref in self.file_index[normalized]:
                    if ref.id not in seen:
                        affected.append(ref)
                        seen.add(ref.id)

            # Try glob-style matching for indexed patterns
            for indexed_path, refs in self.file_index.items():
                if self._path_matches_pattern(normalized, indexed_path):
                    for ref in refs:
                        if ref.id not in seen:
                            affected.append(ref)
                            seen.add(ref.id)

        return affected

    def get_transitive_closure(self, ticket_id: str) -> Set[str]:
        """
        Get all transitively connected ticket IDs.

        Returns the set of all ticket IDs that are reachable from
        or can reach the specified ticket through dependency chains.

        Args:
            ticket_id: Starting ticket for transitive closure

        Returns:
            Set of all transitively connected ticket IDs.

        Example:
            >>> closure = graph.get_transitive_closure("01KC...")
            >>> print(f"Connected to {len(closure)} tickets")
        """
        connected: Set[str] = set()

        if ticket_id not in self.graph:
            return connected

        # Get all tickets this one depends on (upstream transitive)
        upstream = nx.ancestors(self.graph, ticket_id)
        connected.update(upstream)

        # Get all tickets that depend on this one (downstream transitive)
        downstream = nx.descendants(self.graph, ticket_id)
        connected.update(downstream)

        return connected

    def get_dependency_path(
        self, source_id: str, target_id: str
    ) -> Optional[List[str]]:
        """
        Get the shortest dependency path between two tickets.

        Finds the shortest path of ticket IDs from source to target
        following dependency edges.

        Args:
            source_id: Starting ticket
            target_id: Target ticket

        Returns:
            List of ticket IDs representing the path, or None if no path exists.

        Example:
            >>> path = graph.get_dependency_path("01KC1...", "01KC2...")
            >>> if path:
            ...     print(" -> ".join(path))
        """
        if source_id not in self.graph or target_id not in self.graph:
            return None

        try:
            return nx.shortest_path(self.graph, source_id, target_id)
        except nx.NetworkXNoPath:
            return None

    def has_cycle(self) -> bool:
        """
        Check if the dependency graph contains cycles.

        Returns True if there are any circular dependencies.

        Returns:
            True if cycles exist, False otherwise.

        Example:
            >>> if graph.has_cycle():
            ...     print("Warning: Circular dependencies detected!")
        """
        try:
            nx.find_cycle(self.graph)
            return True
        except nx.NetworkXNoCycle:
            return False

    def get_execution_order(self) -> Optional[List[str]]:
        """
        Get topologically sorted execution order for tickets.

        Returns tickets in an order that respects dependencies
        (dependencies come before dependents).

        Returns:
            List of ticket IDs in execution order, or None if cycles exist.

        Example:
            >>> order = graph.get_execution_order()
            >>> if order:
            ...     for ticket_id in order:
            ...         print(f"Execute: {ticket_id}")
        """
        try:
            # Reverse because edges go from dependent to dependency
            return list(reversed(list(nx.topological_sort(self.graph))))
        except nx.NetworkXUnfeasible:
            # Graph has cycles
            return None

    def get_blocking_criteria(
        self, ticket_id: str, target_status: TicketStatus = TicketStatus.IN_PROGRESS
    ) -> List[CriterionRef]:
        """
        Get criteria blocking a ticket from reaching a status.

        Returns CriterionRef objects that block the ticket's transition
        to the specified status and are not yet satisfied.

        Args:
            ticket_id: The ticket to check
            target_status: The status transition to check (default IN_PROGRESS)

        Returns:
            List of unsatisfied CriterionRef objects blocking the transition.

        Example:
            >>> blocking = graph.get_blocking_criteria("01KC...", TicketStatus.COMPLETED)
            >>> for ref in blocking:
            ...     print(f"Blocked by: {ref.description}")
        """
        blocking: List[CriterionRef] = []

        if ticket_id not in self.graph:
            return blocking

        # Check outgoing edges (dependencies)
        for successor in self.graph.successors(ticket_id):
            edge_data = self.graph.get_edge_data(ticket_id, successor)
            if edge_data:
                blocks_transition = edge_data.get("blocks_transition_to")
                criterion = edge_data.get("criterion")
                if (
                    blocks_transition == target_status.value
                    and criterion is not None
                    and not criterion.status
                ):
                    blocking.append(criterion)

        return blocking

    # =========================================================================
    # PRIVATE METHODS
    # =========================================================================

    def _load_tickets_with_criteria(self) -> Dict[str, List[Criterion]]:
        """
        Load all tickets with their criteria from YAML files.

        Returns:
            Dictionary mapping ticket_id to list of Criterion objects.
        """
        from vibey.roadmap.serialization.yaml_loader import (
            load_task_ticket,
            load_sprint_ticket,
            load_track_ticket,
        )

        tickets_with_criteria: Dict[str, List[Criterion]] = {}

        # Load tasks
        tasks_dir = self.root / "tasks"
        if tasks_dir.exists():
            for task_file in tasks_dir.glob("*.yaml"):
                try:
                    ticket = load_task_ticket(task_file)
                    if ticket.criteria:
                        tickets_with_criteria[ticket.id] = list(ticket.criteria)
                except Exception as e:
                    logger.warning(f"Failed to load task {task_file}: {e}")

        # Load sprints
        sprints_dir = self.root / "sprints"
        if sprints_dir.exists():
            for sprint_file in sprints_dir.glob("*.yaml"):
                try:
                    ticket = load_sprint_ticket(sprint_file)
                    if ticket.criteria:
                        tickets_with_criteria[ticket.id] = list(ticket.criteria)
                except Exception as e:
                    logger.warning(f"Failed to load sprint {sprint_file}: {e}")

        # Load tracks
        tracks_dir = self.root / "tracks"
        if tracks_dir.exists():
            for track_file in tracks_dir.glob("*.yaml"):
                try:
                    ticket = load_track_ticket(track_file)
                    if ticket.criteria:
                        tickets_with_criteria[ticket.id] = list(ticket.criteria)
                except Exception as e:
                    logger.warning(f"Failed to load track {track_file}: {e}")

        logger.debug(f"Loaded {len(tickets_with_criteria)} tickets with criteria")
        return tickets_with_criteria

    def _create_criterion_ref(
        self, ticket_id: str, index: int, criterion: Criterion
    ) -> CriterionRef:
        """
        Create a CriterionRef from a Criterion object.

        Args:
            ticket_id: ID of the ticket containing the criterion
            index: Index of the criterion in the ticket's criteria list
            criterion: The Criterion object

        Returns:
            CriterionRef with extracted information.
        """
        # Determine criterion type
        criterion_type = CriterionTargetType.MANUAL  # Default
        if hasattr(criterion.target, "type"):
            criterion_type = criterion.target.type

        # Extract file references
        file_refs: List[str] = []

        if isinstance(criterion.target, FileExistsTarget):
            file_refs = list(criterion.target.paths)
        elif isinstance(criterion.target, ArtifactTarget):
            # Artifact targets reference files indirectly through artifact_id
            # We could resolve this to actual files if artifact registry is available
            pass

        return CriterionRef(
            ticket_id=ticket_id,
            criterion_index=index,
            criterion_type=criterion_type,
            description=criterion.description,
            file_refs=file_refs,
            status=criterion.is_met,
        )

    def _path_matches_pattern(self, path: str, pattern: str) -> bool:
        """
        Check if a path matches a glob pattern.

        Simple matching for common patterns. For full glob support,
        use fnmatch or pathlib.

        Args:
            path: The file path to check
            pattern: The pattern to match against

        Returns:
            True if the path matches the pattern.
        """
        from fnmatch import fnmatch

        return fnmatch(path, pattern)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "CriterionRef",
    "CriterionDependencyGraph",
]
