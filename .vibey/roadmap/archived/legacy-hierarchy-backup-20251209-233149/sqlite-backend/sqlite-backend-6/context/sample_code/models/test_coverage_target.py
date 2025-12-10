class CoverageType(str, Enum):
    """Type of code coverage measurement."""
    LINE = "line"          # Statement/line coverage
    BRANCH = "branch"      # Branch/decision coverage
    BOTH = "both"          # Must meet both line and branch thresholds


class TestCoverageTarget(CriterionTarget):
    """Criterion met when test coverage meets thresholds."""

    # How to generate coverage data
    source_command: str  # e.g., "pytest --cov --cov-report=json"

    # What type of coverage to measure
    coverage_type: CoverageType = CoverageType.LINE

    # Overall thresholds
    overall_threshold: float = 80.0
    branch_threshold: Optional[float] = None  # Only if coverage_type includes BRANCH

    # Per-file thresholds (optional, stricter)
    per_file_threshold: Optional[float] = None  # e.g., 70.0 minimum per file
    per_file_branch_threshold: Optional[float] = None

    # Exclusions (files that don't count toward coverage)
    exclude_patterns: List[str] = Field(default_factory=list)
    # e.g., ["*/migrations/*", "*/tests/*", "*/__init__.py"]

    # Include patterns (if set, only these files count)
    include_patterns: Optional[List[str]] = None
    # e.g., ["src/**/*.py"]

    # Cached state (from last coverage run)
    overall_line_coverage: Optional[float] = None
    overall_branch_coverage: Optional[float] = None
    files_below_threshold: List[str] = Field(default_factory=list)
    total_lines: Optional[int] = None
    covered_lines: Optional[int] = None
    total_branches: Optional[int] = None
    covered_branches: Optional[int] = None
    last_checked: Optional[datetime] = None

    def is_satisfied(self) -> bool:
        # Must have run at least once
        if self.overall_line_coverage is None:
            return False

        # Check overall line coverage
        if self.overall_line_coverage < self.overall_threshold:
            return False

        # Check branch coverage if required
        if self.coverage_type in (CoverageType.BRANCH, CoverageType.BOTH):
            if self.overall_branch_coverage is None:
                return False
            threshold = self.branch_threshold or self.overall_threshold
            if self.overall_branch_coverage < threshold:
                return False

        # Check per-file thresholds if set
        if self.per_file_threshold is not None:
            if len(self.files_below_threshold) > 0:
                return False

        return True

    @property
    def summary(self) -> str:
        """Human-readable summary of coverage state."""
        if self.overall_line_coverage is None:
            return "Coverage not yet measured"

        parts = [f"Line: {self.overall_line_coverage:.1f}%"]
        if self.overall_branch_coverage is not None:
            parts.append(f"Branch: {self.overall_branch_coverage:.1f}%")
        if self.files_below_threshold:
            parts.append(f"{len(self.files_below_threshold)} files below threshold")

        return ", ".join(parts)
