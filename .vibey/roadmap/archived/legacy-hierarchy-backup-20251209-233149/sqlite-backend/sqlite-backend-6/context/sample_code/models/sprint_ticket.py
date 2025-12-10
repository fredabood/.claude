class SprintTicket(HierarchicalTicket):
    # Extended Lifecycle Timestamps
    completion_gate_check_at: Optional[datetime]
    production_gate_check_at: Optional[datetime]
    production_ready_at: Optional[datetime]
    deployed_at: Optional[datetime]

    # Sprint-specific
    plan_file: Optional[str]

    # Artifact Accessors
    @property
    def sprint_context_artifacts(self) -> List[str]: ...

    @property
    def planning_artifacts(self) -> List[str]: ...
