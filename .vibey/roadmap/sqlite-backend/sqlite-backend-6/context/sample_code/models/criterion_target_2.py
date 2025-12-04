class CriterionTarget(BaseModel):
    @abstractmethod
    def is_satisfied(self) -> bool: ...

    @property
    @abstractmethod
    def is_automatic(self) -> bool:
        """Can this target auto-evaluate without human intervention?"""
        ...

    def refresh(self, context: RefreshContext) -> None:
        """Refresh cached state from external source."""
        pass
