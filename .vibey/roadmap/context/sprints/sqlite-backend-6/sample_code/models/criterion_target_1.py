class CriterionTarget(BaseModel):
    """Base for all criterion targets."""

    @abstractmethod
    def is_satisfied(self) -> bool: ...

    @property
    @abstractmethod
    def is_automatic(self) -> bool:
        """Can this target auto-evaluate without human intervention?"""
        ...

    def refresh(self, context: "RefreshContext") -> None:
        """
        Refresh cached state from external source.

        Override in subclasses that support automatic refresh.
        """
        pass


class CompletableTarget(CriterionTarget):
    @property
    def is_automatic(self) -> bool:
        return True  # Can check referenced ticket's status

    def refresh(self, context: "RefreshContext") -> None:
        ticket = context.ticket_registry.get(self.completable_id)
        self.current_status = ticket.status if ticket else None
        self.last_checked = datetime.now(timezone.utc)


class FileExistsTarget(CriterionTarget):
    @property
    def is_automatic(self) -> bool:
        return True  # Can check filesystem

    def refresh(self, context: "RefreshContext") -> None:
        self.existing_paths = [p for p in self.paths if Path(p).exists()]
        self.missing_paths = [p for p in self.paths if not Path(p).exists()]
        self.last_checked = datetime.now(timezone.utc)


class TestPassesTarget(CriterionTarget):
    @property
    def is_automatic(self) -> bool:
        return True  # Can run test command

    def refresh(self, context: "RefreshContext") -> None:
        # Run test_command, parse results
        result = context.test_runner.run(self.test_command)
        self.last_result = result
        self.last_checked = datetime.now(timezone.utc)


class ManualTarget(CriterionTarget):
    @property
    def is_automatic(self) -> bool:
        return False  # Requires human assessment

    # No refresh() - must be set via assess() method


class ThresholdTarget(CriterionTarget):
    @property
    def is_automatic(self) -> bool:
        return True  # Can query metric source

    def refresh(self, context: "RefreshContext") -> None:
        self.current_value = context.metrics.get(self.metric_name)
        self.last_checked = datetime.now(timezone.utc)


class ExternalTarget(CriterionTarget):
    @property
    def is_automatic(self) -> bool:
        return True  # Can query external system

    def refresh(self, context: "RefreshContext") -> None:
        if self.endpoint:
            self.current_status = context.http_client.get_status(self.endpoint)
        self.last_checked = datetime.now(timezone.utc)
