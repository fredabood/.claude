class ManualTarget(CriterionTarget):
    assessor: Optional[str]
    instructions: Optional[str]

    # Assessment state
    assessed: bool = False
    met: Optional[bool]
    assessed_at: Optional[datetime]
    assessed_by: Optional[str]
    evidence: Optional[str]

    @property
    def is_automatic(self) -> bool:
        return False  # Requires human
