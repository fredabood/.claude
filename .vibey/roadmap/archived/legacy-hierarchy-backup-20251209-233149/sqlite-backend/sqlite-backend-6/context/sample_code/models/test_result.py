class TestResult(BaseModel):
    pass_rate: float
    coverage_percent: Optional[float]
    passed: int
    failed: int
    skipped: int
    duration_seconds: float
