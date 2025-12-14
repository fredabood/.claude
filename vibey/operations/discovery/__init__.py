"""Discovery module for project analysis and context generation.

This module provides structured project discovery capabilities:
- Analyze project structure, dependencies, and patterns
- Generate versioned discovery outputs
- Integrate with context management system

Example usage:
    from vibey.operations.discovery import (
        DiscoveryOutput,
        DiscoveryMetadata,
        ProjectInfo,
        to_yaml,
        from_yaml,
    )

    # Create a discovery output
    discovery = DiscoveryOutput(
        metadata=DiscoveryMetadata(...),
        project=ProjectInfo(...),
    )

    # Serialize to YAML
    yaml_str = to_yaml(discovery)

    # Deserialize from YAML
    loaded = from_yaml(yaml_str)
"""

from .schema import (
    # Main output
    DiscoveryOutput,
    # Metadata
    DiscoveryMetadata,
    # Project
    ProjectInfo,
    LanguageInfo,
    FrameworkInfo,
    # Structure
    StructureInfo,
    DirectoryInfo,
    KeyFileInfo,
    # Dependencies
    DependenciesInfo,
    Dependency,
    SystemDependency,
    # Patterns
    PatternsInfo,
    Pattern,
    # Conventions
    ConventionsInfo,
    NamingConventions,
    OrganizationConventions,
    CodeStyleInfo,
    # Quality
    QualityInfo,
    # Recommendations
    RecommendationsInfo,
    Recommendation,
    # Git History
    GitHistoryInfo,
    ContributorInfo,
    SprintInfo,
    VelocityInfo,
    # Enums
    ProjectType,
    FrameworkCategory,
    DirectoryPurpose,
    FileRole,
    ArchitecturePattern,
    SystemDependencyCategory,
    NamingConvention,
    TestLocation,
    CommitConvention,
    RecommendationCategory,
    Priority,
    Effort,
    VulnerabilitySeverity,
)

from .serializers import (
    DiscoverySerializer,
    to_yaml,
    to_json,
    from_yaml,
    from_json,
    save_yaml,
    save_json,
    load_yaml,
    load_json,
)

from .versioning import (
    DiscoveryVersion,
    DiscoveryDiff,
    DiscoveryVersionManager,
    get_version_manager,
)

__all__ = [
    # Main output
    "DiscoveryOutput",
    # Metadata
    "DiscoveryMetadata",
    # Project
    "ProjectInfo",
    "LanguageInfo",
    "FrameworkInfo",
    # Structure
    "StructureInfo",
    "DirectoryInfo",
    "KeyFileInfo",
    # Dependencies
    "DependenciesInfo",
    "Dependency",
    "SystemDependency",
    # Patterns
    "PatternsInfo",
    "Pattern",
    # Conventions
    "ConventionsInfo",
    "NamingConventions",
    "OrganizationConventions",
    "CodeStyleInfo",
    # Quality
    "QualityInfo",
    # Recommendations
    "RecommendationsInfo",
    "Recommendation",
    # Git History
    "GitHistoryInfo",
    "ContributorInfo",
    "SprintInfo",
    "VelocityInfo",
    # Enums
    "ProjectType",
    "FrameworkCategory",
    "DirectoryPurpose",
    "FileRole",
    "ArchitecturePattern",
    "SystemDependencyCategory",
    "NamingConvention",
    "TestLocation",
    "CommitConvention",
    "RecommendationCategory",
    "Priority",
    "Effort",
    "VulnerabilitySeverity",
    # Serializers
    "DiscoverySerializer",
    "to_yaml",
    "to_json",
    "from_yaml",
    "from_json",
    "save_yaml",
    "save_json",
    "load_yaml",
    "load_json",
    # Versioning
    "DiscoveryVersion",
    "DiscoveryDiff",
    "DiscoveryVersionManager",
    "get_version_manager",
]
