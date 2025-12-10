@dataclass
class ImpactReport:
    changed_files: List[str]
    directly_impacted_artifacts: List[Artifact]
    stale_documentation: List[Artifact]
    affected_tickets: List[str]

    @property
    def has_documentation_impact(self) -> bool: ...

    def to_warning_message(self) -> str: ...
