class CriterionTarget(BaseModel):
    """Base for all criterion targets."""

    @abstractmethod
    def is_satisfied(self) -> bool: ...


class CompletableTarget(CriterionTarget):
    """Criterion met when another Completable reaches required status."""

    completable_id: str
    required_status: TicketStatus = TicketStatus.COMPLETED

    # Cached state (updated by sync)
    current_status: Optional[TicketStatus] = None
    last_checked: Optional[datetime] = None

    def is_satisfied(self) -> bool:
        if self.current_status is None:
            return False
        return status_gte(self.current_status, self.required_status)


class FileExistsTarget(CriterionTarget):
    """Criterion met when file(s) exist."""

    paths: List[str]
    all_required: bool = True

    # Cached state
    existing_paths: List[str] = Field(default_factory=list)
    missing_paths: List[str] = Field(default_factory=list)
    last_checked: Optional[datetime] = None

    def is_satisfied(self) -> bool:
        if self.all_required:
            return len(self.missing_paths) == 0
        return len(self.existing_paths) > 0


class TestPassesTarget(CriterionTarget):
    """Criterion met when tests pass.

    Note: For coverage requirements, use TestCoverageTarget instead.
    This keeps test pass/fail separate from coverage metrics.
    """

    test_command: str
    pass_threshold: float = 100.0  # Percentage of tests that must pass

    # Cached state (latest result)
    last_result: Optional[TestResult] = None

    def is_satisfied(self) -> bool:
        if self.last_result is None:
            return False
        return self.last_result.pass_rate >= self.pass_threshold


class ThresholdTarget(CriterionTarget):
    """Criterion met when a metric meets a threshold."""

    metric_name: str
    threshold: float
    comparison: ThresholdComparison = ThresholdComparison.GTE

    # Current value
    current_value: Optional[float] = None
    last_checked: Optional[datetime] = None

    def is_satisfied(self) -> bool:
        if self.current_value is None:
            return False
        return compare(self.current_value, self.threshold, self.comparison)


class ManualTarget(CriterionTarget):
    """Criterion met when manually assessed."""

    assessor: Optional[str] = None
    instructions: Optional[str] = None

    # Assessment state
    assessed: bool = False
    met: Optional[bool] = None
    assessed_at: Optional[datetime] = None
    assessed_by: Optional[str] = None
    evidence: Optional[str] = None

    def is_satisfied(self) -> bool:
        return self.assessed and self.met == True


class ExternalTarget(CriterionTarget):
    """Criterion met when external system reports success."""

    system_name: str
    endpoint: Optional[str] = None
    expected_status: str = "success"

    # Cached state
    current_status: Optional[str] = None
    last_checked: Optional[datetime] = None

    def is_satisfied(self) -> bool:
        return self.current_status == self.expected_status
