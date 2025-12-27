"""
Vibey configuration system.

This package provides the modular configuration system for Vibey:
- Pydantic models for validation
- YAML-based configuration files
- Config loading and migration utilities

Directory structure:
    .vibey/config/
    ├── project.yaml          # Project-specific info
    ├── framework.yaml         # Framework settings
    ├── agents.yaml            # Agent configuration
    └── quality-gates.yaml     # Quality gate definitions
"""

from vibey.config.models import (
    # Enums
    ProjectType,
    OrchestrationMode,
    QualityGateMode,
    # Project Config
    Project,
    TechStack,
    Paths,
    ProjectConfig,
    # Framework Config
    Framework,
    Deployment,
    Features,
    FrameworkConfig,
    # Agents Config
    Agents,
    AgentPreference,
    AgentsConfig,
    # Quality Gates Config
    QualityGates,
    Gates,
    SecurityGate,
    TestingGate,
    LoggingGate,
    DocumentationGate,
    PerformanceGate,
    QualityGatesConfig,
    # Unified Config
    VibeyConfig,
)

from vibey.config.loader import (
    ConfigLoader,
    ConfigLocation,
    ConfigLoadError,
    ConfigNotFoundError,
    ConfigValidationError,
    load_config,
)

from vibey.config.submodule_config import (
    get_default_config as get_default_submodule_config,
    get_submodule_config_path,
    load_submodule_config,
    save_submodule_config,
)

__all__ = [
    # Enums
    "ProjectType",
    "OrchestrationMode",
    "QualityGateMode",
    # Project Config
    "Project",
    "TechStack",
    "Paths",
    "ProjectConfig",
    # Framework Config
    "Framework",
    "Deployment",
    "Features",
    "FrameworkConfig",
    # Agents Config
    "Agents",
    "AgentPreference",
    "AgentsConfig",
    # Quality Gates Config
    "QualityGates",
    "Gates",
    "SecurityGate",
    "TestingGate",
    "LoggingGate",
    "DocumentationGate",
    "PerformanceGate",
    "QualityGatesConfig",
    # Unified Config
    "VibeyConfig",
    # Loader
    "ConfigLoader",
    "ConfigLocation",
    "ConfigLoadError",
    "ConfigNotFoundError",
    "ConfigValidationError",
    "load_config",
    # Submodule Config
    "get_default_submodule_config",
    "get_submodule_config_path",
    "load_submodule_config",
    "save_submodule_config",
]
