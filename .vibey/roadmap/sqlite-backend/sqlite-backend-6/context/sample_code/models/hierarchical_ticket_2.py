class HierarchicalTicket(Ticket):
    # === HIERARCHY & ORDERING ===
    parent_id: Optional[str]             # ULID reference (not slug)
    sequence: int = 0                    # Explicit ordering among siblings
    slug: str = ""                       # Human-readable path segment

    # === SIBLING NAVIGATION ===
    @property
    def siblings(self) -> List['HierarchicalTicket']: ...

    @property
    def next_sibling(self) -> Optional['HierarchicalTicket']: ...

    @property
    def prev_sibling(self) -> Optional['HierarchicalTicket']: ...

    def reorder(self, new_sequence: int) -> None:
        """Change position without changing identity."""
        ...

    # === SMART ACCESSORS ===
    @property
    def commits(self) -> List[GitCommit]:
        """Local if leaf, aggregated if parent."""
        ...

    @property
    def requirements_effective(self) -> List[Requirement]:
        """Resolved with inheritance modes."""
        ...

    @property
    def all_criteria(self) -> List[Criterion]:
        """Explicit + instantiated from requirements."""
        ...

    # === CONVENIENCE BY CRITERION TYPE ===
    @property
    def deliverables(self) -> List[Criterion]: ...

    @property
    def tests(self) -> List[Criterion]: ...

    @property
    def subtasks(self) -> List[Criterion]: ...

    @property
    def dependencies(self) -> List[Criterion]:
        """Criteria blocking IN_PROGRESS."""
        ...

    @property
    def success_criteria(self) -> List[Criterion]:
        """Criteria blocking COMPLETED."""
        ...

    @property
    def production_gates(self) -> List[Criterion]:
        """Criteria blocking PRODUCTION_READY."""
        ...

    # === ARTIFACT AGGREGATION ===
    @property
    def all_referenced_artifacts(self) -> List[str]: ...

    @property
    def stale_documentation_artifacts(self) -> List[str]: ...

    @property
    def has_stale_documentation(self) -> bool: ...

    @property
    def documentation_health(self) -> DocumentationHealth: ...

    # === INHERITED COMPUTED FIELDS ===
    @property
    def effective_priority(self) -> Priority: ...

    @computed_field
    def computed_tokens(self) -> int: ...

    @property
    def estimated_duration(self) -> Optional[str]: ...

    @property
    def required_children(self) -> List[str]:
        """Children that are not deferred."""
        ...
