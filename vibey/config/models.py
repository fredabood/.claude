"""
Pydantic models for Vibey configuration validation.

This module defines the data models for the modular configuration system:
- ProjectConfig: Project-specific information
- FrameworkConfig: Vibey framework settings
- AgentsConfig: Agent selection and preferences
- QualityGatesConfig: Quality gate definitions

All models support loading from YAML files and validation against schemas.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
import yaml


def _serialize_for_yaml(data: Any) -> Any:
    """
    Recursively convert Pydantic models and enums to plain Python types.

    This ensures clean YAML serialization without Python-specific tags.
    """
    if isinstance(data, dict):
        return {k: _serialize_for_yaml(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_serialize_for_yaml(item) for item in data]
    elif isinstance(data, Enum):
        return data.value
    else:
        return data


# ============================================================================
# Enums
# ============================================================================

class ProjectType(str, Enum):
    """Supported project types."""
    WEB_APP = "web-app"
    API = "api"
    LIBRARY = "library"
    ML = "ml"
    DATA_PLATFORM = "data-platform"
    INFRASTRUCTURE = "infrastructure"


class OrchestrationMode(str, Enum):
    """Agent orchestration modes."""
    SIMPLE = "simple"
    BALANCED = "balanced"
    TIERED = "tiered"


class QualityGateMode(str, Enum):
    """Quality gate enforcement modes."""
    STRICT = "strict"
    BALANCED = "balanced"
    PERMISSIVE = "permissive"


# ============================================================================
# Project Configuration
# ============================================================================

class Project(BaseModel):
    """Core project information."""
    name: str = Field(..., description="Project name")
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$", description="Semantic version")
    type: ProjectType = Field(..., description="Project type")
    description: Optional[str] = Field(None, description="Project description")
    repository: Optional[str] = Field(None, description="Git repository URL")


class TechStack(BaseModel):
    """Technology stack configuration."""
    languages: List[str] = Field(..., min_length=1, description="Programming languages")
    frameworks: Optional[List[str]] = Field(default_factory=list, description="Frameworks and libraries")
    databases: Optional[List[str]] = Field(default_factory=list, description="Databases")
    infrastructure: Optional[List[str]] = Field(default_factory=list, description="Infrastructure tools")


class Paths(BaseModel):
    """Project directory paths."""
    source: str = Field(default="src", description="Source code directory")
    tests: str = Field(default="tests", description="Test directory")
    docs: str = Field(default="docs", description="Documentation directory")
    config: str = Field(default=".vibey/config", description="Configuration directory")


class ProjectConfig(BaseModel):
    """Project configuration model."""
    project: Project
    tech_stack: TechStack
    paths: Optional[Paths] = Field(default_factory=Paths)

    @classmethod
    def from_yaml(cls, path: str | Path) -> ProjectConfig:
        """Load configuration from YAML file."""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def to_yaml(self, path: str | Path) -> None:
        """Save configuration to YAML file."""
        data = self.model_dump(mode='python', exclude_none=True)
        serialized = _serialize_for_yaml(data)
        with open(path, 'w') as f:
            yaml.dump(
                serialized,
                f,
                default_flow_style=False,
                sort_keys=False
            )


# ============================================================================
# Framework Configuration
# ============================================================================

class Framework(BaseModel):
    """Framework configuration."""
    version: str = Field(..., description="Vibey framework version")
    orchestration_mode: OrchestrationMode = Field(
        default=OrchestrationMode.BALANCED,
        description="Agent orchestration mode"
    )
    sprint_state_enabled: bool = Field(default=True, description="Enable sprint state tracking")
    project_context_enabled: bool = Field(default=True, description="Enable PROJECT-CONTEXT.md")


class Deployment(BaseModel):
    """Deployment configuration."""
    platforms: Optional[List[str]] = Field(
        default_factory=lambda: ["claude-code"],
        description="Target platforms"
    )
    auto_deploy: bool = Field(default=False, description="Auto-deploy on updates")
    deployment_dir: Optional[str] = Field(default=".claude", description="Deployment directory")


class Features(BaseModel):
    """Feature flags."""
    roadmap_system: bool = Field(default=True, description="Enable roadmap system")
    documentation_generation: bool = Field(default=True, description="Enable auto docs")
    codebase_audit: bool = Field(default=True, description="Enable codebase audit")
    git_history_analysis: bool = Field(default=True, description="Enable git history analysis")


class FrameworkConfig(BaseModel):
    """Framework configuration model."""
    framework: Framework
    deployment: Optional[Deployment] = Field(default_factory=Deployment)
    features: Optional[Features] = Field(default_factory=Features)

    @classmethod
    def from_yaml(cls, path: str | Path) -> FrameworkConfig:
        """Load configuration from YAML file."""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def to_yaml(self, path: str | Path) -> None:
        """Save configuration to YAML file."""
        data = self.model_dump(mode='python', exclude_none=True)
        serialized = _serialize_for_yaml(data)
        with open(path, 'w') as f:
            yaml.dump(
                serialized,
                f,
                default_flow_style=False,
                sort_keys=False
            )


# ============================================================================
# Agents Configuration
# ============================================================================

class AgentPreference(BaseModel):
    """Per-agent preferences."""
    priority: int = Field(ge=1, le=10, description="Agent priority (1-10)")
    auto_trigger: bool = Field(default=True, description="Allow auto-triggering")
    custom_prompts: Optional[Dict[str, Any]] = Field(default=None, description="Custom prompt overrides")


class Agents(BaseModel):
    """Agent configuration."""
    enabled: List[str] = Field(..., min_length=1, description="Enabled agents")
    disabled: Optional[List[str]] = Field(default_factory=list, description="Disabled agents")


class AgentsConfig(BaseModel):
    """Agents configuration model."""
    agents: Agents
    agent_preferences: Optional[Dict[str, AgentPreference]] = Field(
        default_factory=dict,
        description="Per-agent preferences"
    )

    @classmethod
    def from_yaml(cls, path: str | Path) -> AgentsConfig:
        """Load configuration from YAML file."""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def to_yaml(self, path: str | Path) -> None:
        """Save configuration to YAML file."""
        data = self.model_dump(mode='python', exclude_none=True)
        serialized = _serialize_for_yaml(data)
        with open(path, 'w') as f:
            yaml.dump(
                serialized,
                f,
                default_flow_style=False,
                sort_keys=False
            )


# ============================================================================
# Quality Gates Configuration
# ============================================================================

class GateConfig(BaseModel):
    """Individual gate configuration."""
    enabled: bool = Field(default=True, description="Enable this gate")
    threshold: int = Field(ge=0, le=100, description="Pass threshold (percentage)")
    blocking: bool = Field(default=True, description="Block deployment if failed")


class SecurityGate(GateConfig):
    """Security gate configuration."""
    checks: Optional[List[str]] = Field(
        default_factory=lambda: ["dependency-scan", "code-scan", "secrets-scan"],
        description="Security checks to run"
    )
    threshold: int = Field(default=95, ge=0, le=100)


class TestingGate(GateConfig):
    """Testing gate configuration."""
    coverage_threshold: int = Field(default=80, ge=0, le=100, description="Min coverage %")
    threshold: int = Field(default=100, ge=0, le=100)  # All tests must pass


class LoggingGate(GateConfig):
    """Logging gate configuration."""
    threshold: int = Field(default=90, ge=0, le=100)
    blocking: bool = Field(default=False)


class DocumentationGate(GateConfig):
    """Documentation gate configuration."""
    threshold: int = Field(default=85, ge=0, le=100)
    blocking: bool = Field(default=False)


class PerformanceGate(GateConfig):
    """Performance gate configuration."""
    enabled: bool = Field(default=False)
    threshold: int = Field(default=90, ge=0, le=100)
    blocking: bool = Field(default=False)


class QualityGates(BaseModel):
    """Quality gates configuration."""
    enabled: bool = Field(default=True, description="Enable quality gates")
    mode: QualityGateMode = Field(default=QualityGateMode.BALANCED, description="Enforcement mode")


class Gates(BaseModel):
    """Individual gate configurations."""
    security: Optional[SecurityGate] = Field(default_factory=SecurityGate)
    testing: Optional[TestingGate] = Field(default_factory=TestingGate)
    logging: Optional[LoggingGate] = Field(default_factory=LoggingGate)
    documentation: Optional[DocumentationGate] = Field(default_factory=DocumentationGate)
    performance: Optional[PerformanceGate] = Field(default_factory=PerformanceGate)


class QualityGatesConfig(BaseModel):
    """Quality gates configuration model."""
    quality_gates: QualityGates
    gates: Optional[Gates] = Field(default_factory=Gates)

    @classmethod
    def from_yaml(cls, path: str | Path) -> QualityGatesConfig:
        """Load configuration from YAML file."""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def to_yaml(self, path: str | Path) -> None:
        """Save configuration to YAML file."""
        data = self.model_dump(mode='python', exclude_none=True)
        serialized = _serialize_for_yaml(data)
        with open(path, 'w') as f:
            yaml.dump(
                serialized,
                f,
                default_flow_style=False,
                sort_keys=False
            )


# ============================================================================
# Unified Configuration Loader
# ============================================================================

class VibeyConfig(BaseModel):
    """Unified Vibey configuration (all modules)."""
    project: ProjectConfig
    framework: FrameworkConfig
    agents: AgentsConfig
    quality_gates: QualityGatesConfig

    @classmethod
    def from_directory(cls, config_dir: str | Path) -> VibeyConfig:
        """
        Load all configuration files from a directory.

        Args:
            config_dir: Path to .vibey/config/ directory

        Returns:
            VibeyConfig with all loaded configurations

        Raises:
            FileNotFoundError: If required config files are missing
            ValidationError: If config files are invalid
        """
        config_path = Path(config_dir)

        return cls(
            project=ProjectConfig.from_yaml(config_path / "project.yaml"),
            framework=FrameworkConfig.from_yaml(config_path / "framework.yaml"),
            agents=AgentsConfig.from_yaml(config_path / "agents.yaml"),
            quality_gates=QualityGatesConfig.from_yaml(config_path / "quality-gates.yaml")
        )

    def to_directory(self, config_dir: str | Path) -> None:
        """
        Save all configuration files to a directory.

        Args:
            config_dir: Path to .vibey/config/ directory
        """
        config_path = Path(config_dir)
        config_path.mkdir(parents=True, exist_ok=True)

        self.project.to_yaml(config_path / "project.yaml")
        self.framework.to_yaml(config_path / "framework.yaml")
        self.agents.to_yaml(config_path / "agents.yaml")
        self.quality_gates.to_yaml(config_path / "quality-gates.yaml")


# ============================================================================
# Exports
# ============================================================================

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
]
