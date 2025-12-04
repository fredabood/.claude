class ProvenanceType(str, Enum):
    TICKET_CREATED = "ticket_created"
    PRE_EXISTING = "pre_existing"
    GENERATED = "generated"
    EXTERNAL = "external"
    FRAMEWORK = "framework"
