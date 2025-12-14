"""Discovery output schema using Pydantic models.

This module defines the structured output format for project discovery.
All models are serializable to YAML and JSON.

Schema Version: 1.0.0
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================


class ProjectType(str, Enum):
    """Project type classification."""

    WEB_APP = "web-app"
    API = "api"
    CLI = "cli"
    LIBRARY = "library"
    ML_MODEL = "ml-model"
    DATA_PIPELINE = "data-pipeline"
    INFRASTRUCTURE = "infrastructure"
    MONOREPO = "monorepo"
    UNKNOWN = "unknown"


class FrameworkCategory(str, Enum):
    """Framework category."""

    BACKEND = "backend"
    FRONTEND = "frontend"
    TESTING = "testing"
    BUILD = "build"
    ORM = "orm"
    OTHER = "other"


class DirectoryPurpose(str, Enum):
    """Directory purpose classification."""

    SOURCE = "source"
    TESTS = "tests"
    DOCS = "docs"
    CONFIG = "config"
    SCRIPTS = "scripts"
    ASSETS = "assets"
    GENERATED = "generated"
    VENDOR = "vendor"
    UNKNOWN = "unknown"


class FileRole(str, Enum):
    """Key file role classification."""

    ENTRY_POINT = "entry_point"
    CONFIG = "config"
    README = "readme"
    CHANGELOG = "changelog"
    LICENSE = "license"
    MANIFEST = "manifest"
    SCHEMA = "schema"
    MIGRATION = "migration"
    TEST_CONFIG = "test_config"
    CI_CONFIG = "ci_config"
    DOCKER = "docker"
    OTHER = "other"


class ArchitecturePattern(str, Enum):
    """Architectural pattern classification."""

    LAYERED = "layered"
    MVC = "mvc"
    CLEAN = "clean"
    HEXAGONAL = "hexagonal"
    MICROSERVICES = "microservices"
    MONOLITH = "monolith"
    SERVERLESS = "serverless"
    UNKNOWN = "unknown"


class SystemDependencyCategory(str, Enum):
    """System dependency category."""

    DATABASE = "database"
    CACHE = "cache"
    QUEUE = "queue"
    STORAGE = "storage"
    SEARCH = "search"
    OTHER = "other"


class NamingConvention(str, Enum):
    """Naming convention types."""

    SNAKE_CASE = "snake_case"
    KEBAB_CASE = "kebab-case"
    PASCAL_CASE = "PascalCase"
    CAMEL_CASE = "camelCase"
    MIXED = "mixed"


class TestLocation(str, Enum):
    """Test file location relative to source."""

    ALONGSIDE = "alongside"
    SEPARATE = "separate"
    BOTH = "both"


class CommitConvention(str, Enum):
    """Commit message convention."""

    CONVENTIONAL_COMMITS = "conventional_commits"
    ANGULAR = "angular"
    SEMANTIC = "semantic"
    NONE_DETECTED = "none_detected"


class RecommendationCategory(str, Enum):
    """Recommendation category."""

    SECURITY = "security"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    DEPENDENCIES = "dependencies"
    ARCHITECTURE = "architecture"


class Priority(str, Enum):
    """Priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Effort(str, Enum):
    """Effort estimates."""

    TRIVIAL = "trivial"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    EPIC = "epic"


class VulnerabilitySeverity(str, Enum):
    """Vulnerability severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# =============================================================================
# Metadata
# =============================================================================


class DiscoveryMetadata(BaseModel):
    """Discovery execution metadata."""

    schema_version: str = Field(
        default="1.0.0",
        description="Schema version (semver)",
        pattern=r"^\d+\.\d+\.\d+$",
    )
    discovered_at: datetime = Field(
        description="ISO 8601 timestamp of discovery execution"
    )
    project_root: str = Field(description="Absolute path to project root")
    git_commit: Optional[str] = Field(
        default=None,
        description="Git commit SHA at discovery time",
    )
    git_branch: Optional[str] = Field(
        default=None,
        description="Git branch at discovery time",
    )
    discovery_duration_ms: Optional[int] = Field(
        default=None,
        description="Time taken to run discovery in milliseconds",
    )
    previous_discovery_id: Optional[str] = Field(
        default=None,
        description="ID of previous discovery for diff tracking",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Warnings encountered during discovery",
    )
    completeness: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Fraction of analyzers that succeeded (0.0-1.0)",
    )


# =============================================================================
# Project Info
# =============================================================================


class LanguageInfo(BaseModel):
    """Programming language information."""

    name: str = Field(description="Language name (lowercase)")
    percentage: float = Field(
        ge=0.0, le=100.0, description="Percentage of codebase"
    )
    version: Optional[str] = Field(
        default=None, description="Language version if detected"
    )


class FrameworkInfo(BaseModel):
    """Framework information."""

    name: str = Field(description="Framework name")
    category: FrameworkCategory = Field(description="Framework category")
    version: Optional[str] = Field(default=None, description="Framework version")
    confidence: float = Field(
        default=100.0,
        ge=0.0,
        le=100.0,
        description="Detection confidence (0-100)",
    )


class ProjectInfo(BaseModel):
    """High-level project information."""

    name: str = Field(description="Project name")
    type: ProjectType = Field(description="Project type classification")
    type_confidence: float = Field(
        default=100.0,
        ge=0.0,
        le=100.0,
        description="Confidence score for type detection",
    )
    description: Optional[str] = Field(
        default=None, description="Project description"
    )
    languages: List[LanguageInfo] = Field(
        default_factory=list, description="Programming languages detected"
    )
    frameworks: List[FrameworkInfo] = Field(
        default_factory=list, description="Frameworks detected"
    )


# =============================================================================
# Structure Info
# =============================================================================


class DirectoryInfo(BaseModel):
    """Directory information."""

    path: str = Field(description="Relative path from project root")
    purpose: DirectoryPurpose = Field(description="Directory purpose")
    file_count: Optional[int] = Field(default=None, description="Number of files")
    line_count: Optional[int] = Field(default=None, description="Total lines of code")
    primary_language: Optional[str] = Field(
        default=None, description="Primary language in directory"
    )


class KeyFileInfo(BaseModel):
    """Key file information."""

    path: str = Field(description="Relative path from project root")
    role: FileRole = Field(description="File role")
    lines: Optional[int] = Field(default=None, description="Number of lines")
    description: Optional[str] = Field(default=None, description="File description")


class StructureInfo(BaseModel):
    """Project structure analysis."""

    total_files: int = Field(default=0, description="Total number of source files")
    total_lines: int = Field(default=0, description="Total lines of code")
    directories: List[DirectoryInfo] = Field(
        default_factory=list, description="Key directories"
    )
    key_files: List[KeyFileInfo] = Field(
        default_factory=list, description="Important files"
    )
    entry_points: List[str] = Field(
        default_factory=list, description="Application entry points"
    )
    architecture_pattern: Optional[ArchitecturePattern] = Field(
        default=None, description="Detected architectural pattern"
    )
    architecture_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Architecture detection confidence",
    )


# =============================================================================
# Dependencies Info
# =============================================================================


class Dependency(BaseModel):
    """Dependency information."""

    name: str = Field(description="Package name")
    version: Optional[str] = Field(default=None, description="Installed version")
    version_constraint: Optional[str] = Field(
        default=None, description="Version constraint"
    )
    latest_version: Optional[str] = Field(
        default=None, description="Latest available version"
    )
    is_outdated: bool = Field(default=False, description="Whether outdated")
    has_vulnerability: bool = Field(
        default=False, description="Has known vulnerability"
    )
    vulnerability_severity: Optional[VulnerabilitySeverity] = Field(
        default=None, description="Vulnerability severity"
    )


class SystemDependency(BaseModel):
    """System-level dependency."""

    name: str = Field(description="Service name")
    category: SystemDependencyCategory = Field(description="Dependency category")
    version: Optional[str] = Field(default=None, description="Version if detected")
    detected_from: Optional[str] = Field(
        default=None, description="How this was detected"
    )


class DependenciesInfo(BaseModel):
    """Project dependencies analysis."""

    runtime: List[Dependency] = Field(
        default_factory=list, description="Runtime dependencies"
    )
    development: List[Dependency] = Field(
        default_factory=list, description="Development dependencies"
    )
    system: List[SystemDependency] = Field(
        default_factory=list, description="System-level dependencies"
    )
    outdated_count: int = Field(default=0, description="Number of outdated deps")
    vulnerable_count: int = Field(default=0, description="Number of vulnerable deps")


# =============================================================================
# Patterns Info
# =============================================================================


class Pattern(BaseModel):
    """Code pattern information."""

    name: str = Field(description="Pattern name")
    description: str = Field(description="Pattern description")
    locations: List[str] = Field(
        default_factory=list, description="File paths where pattern is found"
    )
    confidence: float = Field(
        default=100.0,
        ge=0.0,
        le=100.0,
        description="Detection confidence",
    )


class PatternsInfo(BaseModel):
    """Code patterns detected."""

    architectural: List[Pattern] = Field(
        default_factory=list, description="Architectural patterns"
    )
    coding: List[Pattern] = Field(
        default_factory=list, description="Coding patterns"
    )
    testing: List[Pattern] = Field(
        default_factory=list, description="Testing patterns"
    )


# =============================================================================
# Conventions Info
# =============================================================================


class NamingConventions(BaseModel):
    """Naming conventions detected."""

    files: Optional[NamingConvention] = Field(default=None, description="File naming")
    functions: Optional[NamingConvention] = Field(
        default=None, description="Function naming"
    )
    classes: Optional[NamingConvention] = Field(
        default=None, description="Class naming"
    )
    variables: Optional[NamingConvention] = Field(
        default=None, description="Variable naming"
    )


class OrganizationConventions(BaseModel):
    """Code organization conventions."""

    module_structure: Optional[str] = Field(
        default=None, description="How modules are organized"
    )
    test_location: Optional[TestLocation] = Field(
        default=None, description="Where tests are located"
    )
    import_style: Optional[str] = Field(
        default=None, description="Import organization pattern"
    )


class CodeStyleInfo(BaseModel):
    """Code style tools detected."""

    formatter: Optional[str] = Field(default=None, description="Code formatter")
    linter: Optional[str] = Field(default=None, description="Linter")
    type_checker: Optional[str] = Field(default=None, description="Type checker")


class ConventionsInfo(BaseModel):
    """Project conventions."""

    naming: Optional[NamingConventions] = Field(
        default=None, description="Naming conventions"
    )
    organization: Optional[OrganizationConventions] = Field(
        default=None, description="Organization conventions"
    )
    commit_convention: Optional[CommitConvention] = Field(
        default=None, description="Commit message convention"
    )
    code_style: Optional[CodeStyleInfo] = Field(
        default=None, description="Code style tools"
    )


# =============================================================================
# Quality Info
# =============================================================================


class QualityInfo(BaseModel):
    """Code quality metrics."""

    test_coverage: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Test coverage percentage",
    )
    test_count: Optional[int] = Field(default=None, description="Number of test cases")
    documentation_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Documentation coverage score",
    )
    security_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Security assessment score",
    )
    overall_health: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Overall project health score",
    )


# =============================================================================
# Recommendations
# =============================================================================


class Recommendation(BaseModel):
    """Improvement recommendation."""

    category: RecommendationCategory = Field(description="Recommendation category")
    title: str = Field(description="Short title")
    description: str = Field(description="Detailed description")
    priority: Priority = Field(default=Priority.MEDIUM, description="Priority level")
    effort: Optional[Effort] = Field(default=None, description="Effort estimate")
    files: List[str] = Field(default_factory=list, description="Affected files")


class RecommendationsInfo(BaseModel):
    """Improvement recommendations."""

    immediate: List[Recommendation] = Field(
        default_factory=list, description="High-priority recommendations"
    )
    suggested: List[Recommendation] = Field(
        default_factory=list, description="Nice-to-have recommendations"
    )


# =============================================================================
# Git History Info
# =============================================================================


class ContributorInfo(BaseModel):
    """Contributor information."""

    name: str = Field(description="Contributor name")
    commits: int = Field(description="Number of commits")


class SprintInfo(BaseModel):
    """Detected sprint information."""

    name: str = Field(description="Sprint name/tag")
    start_date: Optional[str] = Field(default=None, description="Sprint start date")
    end_date: Optional[str] = Field(default=None, description="Sprint end date")
    commits: Optional[int] = Field(default=None, description="Number of commits")
    summary: Optional[str] = Field(default=None, description="Sprint summary")


class VelocityInfo(BaseModel):
    """Development velocity metrics."""

    commits_per_week: Optional[float] = Field(
        default=None, description="Average commits per week"
    )
    lines_per_month: Optional[int] = Field(
        default=None, description="Lines changed per month"
    )


class GitHistoryInfo(BaseModel):
    """Git history analysis."""

    total_commits: Optional[int] = Field(
        default=None, description="Total commits in analysis period"
    )
    contributors: List[ContributorInfo] = Field(
        default_factory=list, description="Contributors"
    )
    recent_sprints: List[SprintInfo] = Field(
        default_factory=list, description="Detected recent sprints"
    )
    velocity: Optional[VelocityInfo] = Field(
        default=None, description="Development velocity"
    )
    sprint_cadence: Optional[str] = Field(
        default=None, description="Detected sprint length"
    )


# =============================================================================
# Main Discovery Output
# =============================================================================


class DiscoveryOutput(BaseModel):
    """Complete discovery output.

    This is the main model that contains all discovery results.
    It can be serialized to YAML or JSON for storage and transport.
    """

    metadata: DiscoveryMetadata = Field(description="Discovery execution metadata")
    project: ProjectInfo = Field(description="High-level project information")
    structure: StructureInfo = Field(
        default_factory=StructureInfo, description="Project structure analysis"
    )
    dependencies: DependenciesInfo = Field(
        default_factory=DependenciesInfo, description="Dependencies analysis"
    )
    patterns: Optional[PatternsInfo] = Field(
        default=None, description="Code patterns detected"
    )
    conventions: Optional[ConventionsInfo] = Field(
        default=None, description="Project conventions"
    )
    quality: Optional[QualityInfo] = Field(
        default=None, description="Quality metrics"
    )
    recommendations: Optional[RecommendationsInfo] = Field(
        default=None, description="Improvement recommendations"
    )
    git_history: Optional[GitHistoryInfo] = Field(
        default=None, description="Git history analysis"
    )

    class Config:
        """Pydantic config."""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
