class ExternalTarget(CriterionTarget):
    system_name: str
    endpoint: Optional[str]
    expected_status: str = "success"

    # Cached state
    current_status: Optional[str]
    last_checked: Optional[datetime]

    @property
    def is_automatic(self) -> bool:
        return True
