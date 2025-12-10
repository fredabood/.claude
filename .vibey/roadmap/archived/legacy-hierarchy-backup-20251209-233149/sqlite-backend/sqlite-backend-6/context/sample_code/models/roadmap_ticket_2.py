class RoadmapTicket(HierarchicalTicket):
    # Semantic Fields
    version: str
    activity_log: List[ActivityLogEntry] = []
    deployed_platforms: List[str] = []

    # Artifact Accessors
    @property
    def all_project_documentation(self) -> List[str]: ...

    @property
    def framework_components(self) -> List[str]: ...

    @property
    def orphan_artifacts(self) -> List[str]: ...
