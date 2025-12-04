class TaskTicket(HierarchicalTicket):
    # Semantic Fields
    task_type: TaskType
    estimated_tokens: int                # Required for tasks
    actual_tokens: Optional[int]
    complexity: Complexity = Complexity.MEDIUM
    phase_label: Optional[str]

    # Artifact Accessors
    @property
    def code_artifacts(self) -> List[str]: ...

    @property
    def documentation_artifacts(self) -> List[str]: ...

    @property
    def undocumented_code_artifacts(self) -> List[str]: ...
