class TestPassesTarget(CriterionTarget):
    """Criterion met when tests pass.

    Note: For coverage requirements, use TestCoverageTarget instead.
    """

    test_command: str
    pass_threshold: float = 100.0  # Percentage of tests that must pass

    # Cached state
    last_result: Optional[TestResult]

    @property
    def is_automatic(self) -> bool:
        return True
