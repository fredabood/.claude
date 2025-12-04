class DeliverableType(str, Enum):
    CODE = "code"
    TEST = "test"
    DOCUMENTATION = "documentation"
    CONFIG = "config"
    OTHER = "other"


class FileExistsTarget(CriterionTarget):
    """Criterion met when file(s) exist."""

    paths: List[str]
    all_required: bool = True
    deliverable_type: DeliverableType = DeliverableType.OTHER  # Classification

    # Cached state
    existing_paths: List[str] = Field(default_factory=list)
    missing_paths: List[str] = Field(default_factory=list)
    last_checked: Optional[datetime] = None

    @property
    def is_automatic(self) -> bool:
        return True

    def is_satisfied(self) -> bool:
        if self.all_required:
            return len(self.missing_paths) == 0
        return len(self.existing_paths) > 0

    def refresh(self, context: "RefreshContext") -> None:
        self.existing_paths = [p for p in self.paths if Path(p).exists()]
        self.missing_paths = [p for p in self.paths if not Path(p).exists()]
        self.last_checked = datetime.now(timezone.utc)
