class RoadmapTicket(HierarchicalTicket):
    """Roadmap-specific semantic fields."""
    version: str
    activity_log: List[ActivityLogEntry] = Field(default_factory=list)
    deployed_platforms: List[str] = Field(default_factory=list)


class TrackTicket(HierarchicalTicket):
    """Track-specific semantic fields."""
    priority: Priority
    strategic_value: Optional[str] = None


class SprintTicket(HierarchicalTicket):
    """Sprint-specific semantic fields."""
    # Extended lifecycle timestamps
    completion_gate_check_at: Optional[datetime] = None
    production_gate_check_at: Optional[datetime] = None
    production_ready_at: Optional[datetime] = None
    deployed_at: Optional[datetime] = None

    plan_file: Optional[str] = None


class TaskTicket(HierarchicalTicket):
    """Task-specific semantic fields."""
    task_type: TaskType
    estimated_tokens: Optional[int] = None
    actual_tokens: Optional[int] = None
    complexity: Complexity = Complexity.MEDIUM
    phase_label: Optional[str] = None
