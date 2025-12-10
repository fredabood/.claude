class ThresholdTarget(CriterionTarget):
    metric_name: str
    threshold: float
    comparison: ThresholdComparison = ThresholdComparison.GTE

    # Cached state
    current_value: Optional[float]
    last_checked: Optional[datetime]

    @property
    def is_automatic(self) -> bool:
        return True
