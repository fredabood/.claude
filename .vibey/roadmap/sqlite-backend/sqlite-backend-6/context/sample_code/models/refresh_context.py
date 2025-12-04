class RefreshContext(BaseModel):
    ticket_registry: TicketRegistry
    artifact_registry: ArtifactRegistry
    test_runner: TestRunner
    metrics: MetricsCollector
    http_client: HttpClient
    activity_log: List[ActivityLogEntry]
