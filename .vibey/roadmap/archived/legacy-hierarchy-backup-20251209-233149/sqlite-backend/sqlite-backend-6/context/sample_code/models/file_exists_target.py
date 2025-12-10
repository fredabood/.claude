class FileExistsTarget(CriterionTarget):
    paths: List[str]
    all_required: bool = True
    deliverable_type: DeliverableType = DeliverableType.OTHER

    # Cached state
    existing_paths: List[str] = []
    missing_paths: List[str] = []
    last_checked: Optional[datetime]

    @property
    def is_automatic(self) -> bool:
        return True
