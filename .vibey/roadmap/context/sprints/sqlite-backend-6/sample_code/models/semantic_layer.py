"""
Pluggable Semantic Layer Architecture

The semantic layer (Layer 3) is interchangeable. Different providers
can define their own hierarchy and field sets while sharing the core
Completable → Ticket → HierarchicalTicket foundation.

Semantic layers define:
- Ticket type hierarchy (what types exist, their parent-child relationships)
- Type-specific fields (beyond what HierarchicalTicket provides)
- Status mappings (how statuses translate to/from TicketStatus)
- Validation rules (type-specific constraints)
- Display conventions (how to render in CLI/UI)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Type, Optional, Any
from enum import Enum


class SemanticLayer(ABC):
    """
    Abstract base for semantic layer implementations.

    A semantic layer defines the domain-specific ticket types
    that extend HierarchicalTicket.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this semantic layer."""
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name."""
        ...

    @property
    @abstractmethod
    def ticket_types(self) -> List[str]:
        """
        Ordered list of ticket types from root to leaf.
        e.g., ["roadmap", "track", "sprint", "task"]
        """
        ...

    @property
    @abstractmethod
    def hierarchy(self) -> Dict[str, Optional[str]]:
        """
        Parent type for each ticket type.
        e.g., {"roadmap": None, "track": "roadmap", "sprint": "track", "task": "sprint"}
        """
        ...

    @abstractmethod
    def get_ticket_class(self, ticket_type: str) -> Type["HierarchicalTicket"]:
        """Return the class for a given ticket type."""
        ...

    @abstractmethod
    def get_type_fields(self, ticket_type: str) -> Dict[str, Any]:
        """Return type-specific field definitions."""
        ...

    @abstractmethod
    def map_status_to_canonical(self, ticket_type: str, external_status: str) -> "TicketStatus":
        """Map external status to canonical TicketStatus."""
        ...

    @abstractmethod
    def map_status_from_canonical(self, ticket_type: str, status: "TicketStatus") -> str:
        """Map canonical TicketStatus to external status."""
        ...


# ═══════════════════════════════════════════════════════════════════════════════
# VIBEY SEMANTIC LAYER (DEFAULT)
# ═══════════════════════════════════════════════════════════════════════════════

class VibeySemanticLayer(SemanticLayer):
    """
    Default Vibey semantic layer.

    Hierarchy: Roadmap → Track → Sprint → Task
    """

    @property
    def name(self) -> str:
        return "vibey"

    @property
    def display_name(self) -> str:
        return "Vibey Roadmap System"

    @property
    def ticket_types(self) -> List[str]:
        return ["roadmap", "track", "sprint", "task"]

    @property
    def hierarchy(self) -> Dict[str, Optional[str]]:
        return {
            "roadmap": None,
            "track": "roadmap",
            "sprint": "track",
            "task": "sprint"
        }

    def get_ticket_class(self, ticket_type: str) -> Type["HierarchicalTicket"]:
        return {
            "roadmap": RoadmapTicket,
            "track": TrackTicket,
            "sprint": SprintTicket,
            "task": TaskTicket,
        }[ticket_type]

    def get_type_fields(self, ticket_type: str) -> Dict[str, Any]:
        """Vibey-specific fields per type."""
        fields = {
            "roadmap": {
                "version": {"type": "str", "required": False},
                "deployed_platforms": {"type": "List[str]", "required": False},
            },
            "track": {
                "strategic_value": {"type": "List[str]", "required": False},
            },
            "sprint": {
                "plan_file": {"type": "str", "required": False},
            },
            "task": {
                "task_type": {"type": "TaskType", "required": False},
                "complexity": {"type": "Complexity", "required": False},
            },
        }
        return fields.get(ticket_type, {})

    def map_status_to_canonical(self, ticket_type: str, external_status: str) -> "TicketStatus":
        # Vibey uses canonical statuses directly
        return TicketStatus(external_status)

    def map_status_from_canonical(self, ticket_type: str, status: "TicketStatus") -> str:
        return status.value


# ═══════════════════════════════════════════════════════════════════════════════
# JIRA SEMANTIC LAYER (INTEGRATION)
# ═══════════════════════════════════════════════════════════════════════════════

class JiraSemanticLayer(SemanticLayer):
    """
    Jira semantic layer for Atlassian integration.

    Hierarchy: Project → Epic/Sprint → Issue → Subtask

    Fields are dynamically loaded from Jira project configuration.
    """

    def __init__(self, project_config: "JiraProjectConfig"):
        self.project_config = project_config
        self._status_map = project_config.status_map
        self._custom_fields = project_config.custom_fields

    @property
    def name(self) -> str:
        return f"jira:{self.project_config.project_key}"

    @property
    def display_name(self) -> str:
        return f"Jira Project: {self.project_config.project_name}"

    @property
    def ticket_types(self) -> List[str]:
        # Jira types depend on project configuration
        base_types = ["project"]

        if self.project_config.has_epics:
            base_types.append("epic")
        if self.project_config.has_sprints:
            base_types.append("sprint")

        base_types.extend(["issue", "subtask"])
        return base_types

    @property
    def hierarchy(self) -> Dict[str, Optional[str]]:
        hierarchy = {"project": None}

        if self.project_config.has_epics:
            hierarchy["epic"] = "project"
            issue_parent = "epic"
        elif self.project_config.has_sprints:
            hierarchy["sprint"] = "project"
            issue_parent = "sprint"
        else:
            issue_parent = "project"

        hierarchy["issue"] = issue_parent
        hierarchy["subtask"] = "issue"
        return hierarchy

    def get_ticket_class(self, ticket_type: str) -> Type["HierarchicalTicket"]:
        return {
            "project": JiraProject,
            "epic": JiraEpic,
            "sprint": JiraSprint,
            "issue": JiraIssue,
            "subtask": JiraSubtask,
        }[ticket_type]

    def get_type_fields(self, ticket_type: str) -> Dict[str, Any]:
        """
        Jira fields are dynamic based on project configuration.
        Includes standard fields + custom fields from Jira.
        """
        standard_fields = {
            "project": {
                "project_key": {"type": "str", "required": True},
                "project_type": {"type": "str", "required": False},  # software, business, etc.
                "lead": {"type": "str", "required": False},
            },
            "epic": {
                "epic_key": {"type": "str", "required": True},
                "epic_color": {"type": "str", "required": False},
            },
            "sprint": {
                "sprint_id": {"type": "int", "required": True},
                "board_id": {"type": "int", "required": True},
                "start_date": {"type": "datetime", "required": False},
                "end_date": {"type": "datetime", "required": False},
                "goal": {"type": "str", "required": False},
            },
            "issue": {
                "issue_key": {"type": "str", "required": True},  # PROJ-123
                "issue_type": {"type": "JiraIssueType", "required": True},  # Story, Bug, Task
                "story_points": {"type": "float", "required": False},
                "components": {"type": "List[str]", "required": False},
                "labels": {"type": "List[str]", "required": False},
                "fix_versions": {"type": "List[str]", "required": False},
                "affected_versions": {"type": "List[str]", "required": False},
                "reporter": {"type": "str", "required": False},
                "resolution": {"type": "str", "required": False},
                "environment": {"type": "str", "required": False},
            },
            "subtask": {
                "issue_key": {"type": "str", "required": True},
                "parent_issue_key": {"type": "str", "required": True},
            },
        }

        # Merge with custom fields from Jira project
        fields = standard_fields.get(ticket_type, {})
        if ticket_type in ["issue", "subtask"]:
            for cf_id, cf_config in self._custom_fields.items():
                fields[cf_id] = cf_config

        return fields

    def map_status_to_canonical(self, ticket_type: str, jira_status: str) -> "TicketStatus":
        """Map Jira status to canonical TicketStatus."""
        # Use configured mapping, with fallbacks
        if jira_status in self._status_map:
            return TicketStatus(self._status_map[jira_status])

        # Default mappings for common Jira statuses
        default_map = {
            "To Do": TicketStatus.NOT_STARTED,
            "Open": TicketStatus.NOT_STARTED,
            "Backlog": TicketStatus.NOT_STARTED,
            "In Progress": TicketStatus.IN_PROGRESS,
            "In Development": TicketStatus.IN_PROGRESS,
            "In Review": TicketStatus.IN_PROGRESS,
            "Code Review": TicketStatus.IN_PROGRESS,
            "Testing": TicketStatus.IN_PROGRESS,
            "Done": TicketStatus.COMPLETED,
            "Closed": TicketStatus.COMPLETED,
            "Resolved": TicketStatus.COMPLETED,
            "Released": TicketStatus.DEPLOYED,
            "Won't Do": TicketStatus.WONT_DO,
            "Won't Fix": TicketStatus.WONT_DO,
        }

        return default_map.get(jira_status, TicketStatus.NOT_STARTED)

    def map_status_from_canonical(self, ticket_type: str, status: "TicketStatus") -> str:
        """Map canonical TicketStatus to Jira status."""
        # Reverse lookup in status map
        for jira_status, canonical in self._status_map.items():
            if canonical == status.value:
                return jira_status

        # Default reverse mappings
        default_reverse = {
            TicketStatus.NOT_STARTED: "To Do",
            TicketStatus.IN_PROGRESS: "In Progress",
            TicketStatus.PAUSED: "On Hold",
            TicketStatus.COMPLETED: "Done",
            TicketStatus.PRODUCTION_READY: "Ready for Release",
            TicketStatus.DEPLOYED: "Released",
            TicketStatus.WONT_DO: "Won't Do",
            TicketStatus.SUPERSEDED: "Won't Do",
        }

        return default_reverse.get(status, "To Do")


# ═══════════════════════════════════════════════════════════════════════════════
# JIRA TICKET TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class JiraIssueType(str, Enum):
    """Jira issue types."""
    STORY = "Story"
    BUG = "Bug"
    TASK = "Task"
    EPIC = "Epic"
    SUBTASK = "Sub-task"
    SPIKE = "Spike"
    FEATURE = "Feature"
    IMPROVEMENT = "Improvement"


class JiraProject(HierarchicalTicket):
    """Jira Project mapped to top-level ticket."""

    project_key: str  # e.g., "PROJ"
    project_type: Optional[str] = None  # software, business, service_desk
    lead: Optional[str] = None

    # Jira-specific metadata
    jira_id: str  # Jira's internal ID
    jira_url: str  # Direct link to project


class JiraEpic(HierarchicalTicket):
    """Jira Epic mapped to mid-level ticket."""

    epic_key: str  # e.g., "PROJ-100"
    epic_color: Optional[str] = None

    # Jira-specific
    jira_id: str


class JiraSprint(HierarchicalTicket):
    """Jira Sprint mapped to sprint-level ticket."""

    sprint_id: int  # Jira sprint ID
    board_id: int  # Jira board ID
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    goal: Optional[str] = None
    state: str = "future"  # future, active, closed


class JiraIssue(HierarchicalTicket):
    """Jira Issue (Story/Bug/Task) mapped to work-level ticket."""

    issue_key: str  # e.g., "PROJ-123"
    issue_type: JiraIssueType

    # Standard Jira fields
    story_points: Optional[float] = None
    components: List[str] = Field(default_factory=list)
    labels: List[str] = Field(default_factory=list)
    fix_versions: List[str] = Field(default_factory=list)
    affected_versions: List[str] = Field(default_factory=list)
    reporter: Optional[str] = None
    resolution: Optional[str] = None
    environment: Optional[str] = None

    # Custom fields (dynamically added)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)

    # Jira-specific
    jira_id: str
    jira_url: str


class JiraSubtask(HierarchicalTicket):
    """Jira Subtask mapped to leaf-level ticket."""

    issue_key: str  # e.g., "PROJ-124"
    parent_issue_key: str  # e.g., "PROJ-123"

    # Jira-specific
    jira_id: str


# ═══════════════════════════════════════════════════════════════════════════════
# SEMANTIC LAYER REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════

class SemanticLayerRegistry:
    """
    Registry of available semantic layers.

    Allows dynamic registration and lookup of semantic layers.
    """

    _layers: Dict[str, SemanticLayer] = {}
    _default: str = "vibey"

    @classmethod
    def register(cls, layer: SemanticLayer) -> None:
        """Register a semantic layer."""
        cls._layers[layer.name] = layer

    @classmethod
    def get(cls, name: str) -> SemanticLayer:
        """Get a semantic layer by name."""
        if name not in cls._layers:
            raise ValueError(f"Unknown semantic layer: {name}")
        return cls._layers[name]

    @classmethod
    def get_default(cls) -> SemanticLayer:
        """Get the default semantic layer."""
        return cls._layers[cls._default]

    @classmethod
    def set_default(cls, name: str) -> None:
        """Set the default semantic layer."""
        if name not in cls._layers:
            raise ValueError(f"Unknown semantic layer: {name}")
        cls._default = name

    @classmethod
    def list_layers(cls) -> List[str]:
        """List all registered semantic layers."""
        return list(cls._layers.keys())


# Register default Vibey layer
SemanticLayerRegistry.register(VibeySemanticLayer())
