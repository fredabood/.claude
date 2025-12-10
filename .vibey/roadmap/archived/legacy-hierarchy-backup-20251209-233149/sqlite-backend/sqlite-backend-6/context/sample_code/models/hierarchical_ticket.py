class HierarchicalTicket(Ticket):
    """Layer 2: Ticket with hierarchy-aware accessors."""

    # ═══════════════════════════════════════════════════════════════
    # HIERARCHY & ORDERING (See Part 14 for rationale)
    # ═══════════════════════════════════════════════════════════════
    parent_id: Optional[str] = None  # ULID reference to parent (not slug!)
    sequence: int = 0                 # Explicit ordering among siblings (mutable)
    slug: str = ""                    # Human-readable path segment (mutable)

    # === SIBLING NAVIGATION ===
    @property
    def siblings(self) -> List['HierarchicalTicket']:
        """Other children of same parent, sorted by sequence."""
        if self.parent_id is None:
            return []
        # Implementation: Query by parent_id, order by sequence
        return self._get_siblings_by_parent_id()

    @property
    def next_sibling(self) -> Optional['HierarchicalTicket']:
        """Next sibling by sequence (not by ID!)."""
        siblings = self.siblings
        for i, sib in enumerate(siblings):
            if sib.id == self.id and i + 1 < len(siblings):
                return siblings[i + 1]
        return None

    @property
    def prev_sibling(self) -> Optional['HierarchicalTicket']:
        """Previous sibling by sequence."""
        siblings = self.siblings
        for i, sib in enumerate(siblings):
            if sib.id == self.id and i > 0:
                return siblings[i - 1]
        return None

    def reorder(self, new_sequence: int) -> None:
        """Change position without changing identity."""
        self.sequence = new_sequence
        # Note: Does NOT change self.id - identity is immutable

    # === SMART ACCESSORS ===
    @property
    def commits(self) -> List[GitCommit]:
        """Commits: local if leaf, aggregated if parent."""
        if self.is_ultimate_child:
            return self.commits_local
        return self._aggregate_commits_from_children()

    @property
    def requirements_effective(self) -> List[Requirement]:
        """Requirements: resolved with inheritance modes."""
        return self._resolve_requirements()

    @property
    def all_criteria(self) -> List[Criterion]:
        """All criteria: explicit + instantiated from requirements."""
        return self.criteria + self._instantiate_requirement_criteria()

    # === CONVENIENCE ACCESSORS BY CRITERION TYPE ===
    @property
    def deliverables(self) -> List[Criterion]:
        """Criteria that are file-based."""
        return [c for c in self.criteria if isinstance(c.target, FileExistsTarget)]

    @property
    def tests(self) -> List[Criterion]:
        """Criteria that are test-based."""
        return [c for c in self.criteria if isinstance(c.target, TestPassesTarget)]

    @property
    def subtasks(self) -> List[Criterion]:
        """Criteria that reference other tickets (children)."""
        return [c for c in self.criteria if isinstance(c.target, CompletableTarget)]

    @property
    def dependencies(self) -> List[Criterion]:
        """Criteria that block starting (IN_PROGRESS)."""
        return [
            c for c in self.criteria
            if c.blocks_transition_to == TicketStatus.IN_PROGRESS
        ]

    @property
    def success_criteria(self) -> List[Criterion]:
        """Criteria that block completing (COMPLETED)."""
        return [
            c for c in self.criteria
            if c.blocks_transition_to == TicketStatus.COMPLETED
        ]

    @property
    def production_gates(self) -> List[Criterion]:
        """Criteria that block deployment (PRODUCTION_READY)."""
        return [
            c for c in self.criteria
            if c.blocks_transition_to == TicketStatus.PRODUCTION_READY
        ]
