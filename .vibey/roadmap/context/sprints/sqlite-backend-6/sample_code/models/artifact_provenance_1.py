class ArtifactProvenance(BaseModel):
    provenance_type: ProvenanceType

    # TICKET_CREATED
    created_by_ticket_id: Optional[str]
    created_by_criterion_id: Optional[str]

    # PRE_EXISTING
    discovered_at: Optional[datetime]
    discovered_by: Optional[str]

    # GENERATED
    generator_type: Optional[str]        # "sphinx", "pdoc", "typedoc"
    generator_config: Optional[Dict]
    source_artifact_ids: Optional[List[str]]

    # EXTERNAL
    external_source: Optional[str]
    external_version: Optional[str]

    # FRAMEWORK
    framework_component_type: Optional[str]  # "agent", "workflow", "template"
