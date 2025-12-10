class RoadmapTicket(HierarchicalTicket):
    """Roadmap-specific semantic fields."""

    # ... existing fields ...

    @property
    def all_project_documentation(self) -> List[str]:
        """All DOCUMENTATION type artifacts across the roadmap."""
        return [
            aid for aid in self.all_referenced_artifacts
            if self._get_artifact_type(aid) == ArtifactType.DOCUMENTATION
        ]

    @property
    def framework_components(self) -> List[str]:
        """All AGENT, WORKFLOW, TEMPLATE artifacts."""
        return [
            aid for aid in self.all_referenced_artifacts
            if self._get_artifact_type(aid) in {
                ArtifactType.AGENT,
                ArtifactType.WORKFLOW,
                ArtifactType.TEMPLATE
            }
        ]

    @property
    def orphan_artifacts(self) -> List[str]:
        """Artifacts that exist but aren't referenced by any ticket."""
        # Query from artifact registry
        return self._artifact_registry.get_orphans()


class SprintTicket(HierarchicalTicket):
    """Sprint-specific semantic fields."""

    # ... existing fields ...

    @property
    def sprint_context_artifacts(self) -> List[str]:
        """CONTEXT type artifacts for this sprint (planning docs, etc.)."""
        return [
            c.target.artifact_id for c in self.artifact_criteria
            if self._get_artifact_type(c.target.artifact_id) == ArtifactType.CONTEXT
        ]

    @property
    def planning_artifacts(self) -> List[str]:
        """Context artifacts that block IN_PROGRESS (must exist before starting)."""
        return [
            c.target.artifact_id for c in self.artifact_criteria
            if (self._get_artifact_type(c.target.artifact_id) == ArtifactType.CONTEXT
                and c.blocks_transition_to == TicketStatus.IN_PROGRESS)
        ]


class TaskTicket(HierarchicalTicket):
    """Task-specific semantic fields."""

    # ... existing fields ...

    @property
    def code_artifacts(self) -> List[str]:
        """CODE type artifacts created by this task."""
        return [
            c.target.artifact_id for c in self.artifact_criteria
            if self._get_artifact_type(c.target.artifact_id) == ArtifactType.CODE
        ]

    @property
    def documentation_artifacts(self) -> List[str]:
        """DOCUMENTATION type artifacts created by this task."""
        return [
            c.target.artifact_id for c in self.artifact_criteria
            if self._get_artifact_type(c.target.artifact_id) == ArtifactType.DOCUMENTATION
        ]

    @property
    def undocumented_code_artifacts(self) -> List[str]:
        """Code artifacts that have no documentation artifact linking to them."""
        documented = set()
        for aid in self.documentation_artifacts:
            artifact = self._load_artifact(aid)
            if artifact and artifact.documents_artifact_id:
                documented.add(artifact.documents_artifact_id)

        return [aid for aid in self.code_artifacts if aid not in documented]
