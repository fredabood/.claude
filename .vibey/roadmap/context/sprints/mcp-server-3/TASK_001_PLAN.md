# Task 001: Design MCP Resources Architecture

**Task ID:** 01KC79XW008MN6KHT4S4AVS7VG
**Sprint:** MCP Resources, Prompts & Handoff Discovery
**Complexity:** Medium
**Type:** Research/Design

## Problem Statement

The Vibey MCP server currently exposes roadmap operations as tools, but doesn't leverage MCP Resources for exposing content. MCP Resources provide a standardized way for clients to access content via URI-addressable resources, enabling:
- Direct content access without tool invocation
- Resource subscriptions for live updates
- Rich metadata for resource discovery
- Hierarchical resource organization

## Current State

### Existing MCP Server Architecture
```
vibey/mcp/
├── server.py           # Main server - has resource capability disabled
├── resources/          # Placeholder module (empty)
│   └── __init__.py     # "Resources will be implemented in Sprint 3"
├── prompts/            # Placeholder module (empty)
├── tools/              # Implemented (task, sprint, query, content tools)
├── discovery/          # Agent/workflow discovery (implemented)
└── adapters/           # Roadmap adapter (implemented)
```

### Server Capabilities (server.py:116-133)
```python
def get_capabilities(self) -> Dict[str, Any]:
    return {
        "resources": {
            "subscribe": False  # Resources not implemented in Sprint 1
        },
        ...
    }
```

### Content Available for Resources
1. **Workflows** (`vibey/content/workflows/`) - 16+ workflow markdown files
2. **Handoff Templates** (`vibey/content/templates/handoffs/`) - 23+ template files
3. **Agents** (`vibey/content/agents/`) - 12+ agent definition files
4. **Quality Gates** (embedded in workflows and roadmap data)

## Implementation Plan

### Phase 1: Resource Architecture Design

**1.1 Define Resource URI Scheme**
```
vibey://workflows/{workflow-id}
vibey://workflows/{workflow-id}/steps
vibey://handoffs/{handoff-id}
vibey://handoffs/{handoff-id}/variables
vibey://agents/{agent-id}
vibey://agents/{agent-id}/instructions
vibey://quality-gates/{gate-id}
```

**1.2 Define Resource Data Model**
```python
@dataclass
class VibeyResource:
    uri: str                    # Resource URI
    name: str                   # Human-readable name
    description: str            # Resource description
    mimeType: str              # text/markdown, application/json, etc.
    metadata: Dict[str, Any]   # Additional metadata
    content: Optional[str]      # Cached content (if loaded)
```

**1.3 Define Resource Categories**
| Category | URI Pattern | Content Type | Source |
|----------|-------------|--------------|--------|
| Workflows | `vibey://workflows/{id}` | text/markdown | vibey/content/workflows/*.md |
| Handoffs | `vibey://handoffs/{id}` | text/markdown+jinja2 | vibey/content/templates/handoffs/*.md |
| Agents | `vibey://agents/{id}` | text/markdown | vibey/content/agents/**/*.md |
| Quality Gates | `vibey://quality-gates/{id}` | application/json | Extracted from workflows |

### Phase 2: Resource Provider Interface

**2.1 Create ResourceProvider Base Class**
```python
# vibey/mcp/resources/provider.py
from abc import ABC, abstractmethod
from typing import List, Optional, AsyncIterator
from dataclasses import dataclass

@dataclass
class ResourceTemplate:
    """MCP Resource template definition."""
    uriTemplate: str
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None

@dataclass
class Resource:
    """MCP Resource definition."""
    uri: str
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ResourceContent:
    """Resource content response."""
    uri: str
    mimeType: str
    text: Optional[str] = None
    blob: Optional[bytes] = None

class ResourceProvider(ABC):
    """Base class for MCP resource providers."""

    @abstractmethod
    def get_templates(self) -> List[ResourceTemplate]:
        """Return resource templates this provider supports."""
        pass

    @abstractmethod
    def list_resources(self, uri_template: str) -> List[Resource]:
        """List all resources matching a template."""
        pass

    @abstractmethod
    async def read_resource(self, uri: str) -> ResourceContent:
        """Read resource content by URI."""
        pass

    def supports_uri(self, uri: str) -> bool:
        """Check if this provider handles the given URI."""
        pass
```

### Phase 3: Resource Manager

**3.1 Create ResourceManager Class**
```python
# vibey/mcp/resources/manager.py
class ResourceManager:
    """Manages all resource providers and handles MCP resource operations."""

    def __init__(self, content_root: Path):
        self.providers: Dict[str, ResourceProvider] = {}
        self.content_root = content_root
        self._register_providers()

    def _register_providers(self):
        """Register all resource providers."""
        self.providers['workflows'] = WorkflowResourceProvider(self.content_root)
        self.providers['handoffs'] = HandoffResourceProvider(self.content_root)
        self.providers['agents'] = AgentResourceProvider(self.content_root)
        self.providers['quality-gates'] = QualityGateResourceProvider(self.content_root)

    def get_all_templates(self) -> List[ResourceTemplate]:
        """Get all resource templates from all providers."""
        templates = []
        for provider in self.providers.values():
            templates.extend(provider.get_templates())
        return templates

    def list_all_resources(self) -> List[Resource]:
        """List all available resources."""
        resources = []
        for provider in self.providers.values():
            for template in provider.get_templates():
                resources.extend(provider.list_resources(template.uriTemplate))
        return resources

    async def read_resource(self, uri: str) -> ResourceContent:
        """Read resource content by URI."""
        for provider in self.providers.values():
            if provider.supports_uri(uri):
                return await provider.read_resource(uri)
        raise ResourceNotFoundError(f"No provider for URI: {uri}")
```

### Phase 4: Server Integration

**4.1 Update server.py**
```python
# In VibeyMCPServer.__init__:
self.resource_manager = ResourceManager(self.content_root)

# In get_capabilities():
return {
    "resources": {
        "subscribe": True,  # Enable subscription support
        "listChanged": True  # Support list change notifications
    },
    ...
}

# Add new methods:
def get_resource_templates(self) -> List[Dict]:
    """Get all resource templates for MCP resources/templates/list."""
    return [asdict(t) for t in self.resource_manager.get_all_templates()]

def list_resources(self) -> List[Dict]:
    """List all resources for MCP resources/list."""
    return [asdict(r) for r in self.resource_manager.list_all_resources()]

async def read_resource(self, uri: str) -> Dict:
    """Read resource content for MCP resources/read."""
    content = await self.resource_manager.read_resource(uri)
    return asdict(content)
```

## Files to Create

| File | Purpose |
|------|---------|
| `vibey/mcp/resources/provider.py` | Base ResourceProvider class and data models |
| `vibey/mcp/resources/manager.py` | ResourceManager orchestration class |
| `vibey/mcp/resources/exceptions.py` | Resource-specific exceptions |
| `vibey/mcp/resources/types.py` | Type definitions and dataclasses |

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/mcp/resources/__init__.py` | Export new classes |
| `vibey/mcp/server.py` | Add resource manager and MCP resource methods |

## Success Criteria

1. [ ] Resource URI scheme designed and documented
2. [ ] ResourceProvider interface defined with abstract methods
3. [ ] ResourceManager class structure implemented
4. [ ] Server integration points identified
5. [ ] Type definitions complete with dataclasses
6. [ ] Architecture review document created

## Dependencies

- MCP Python SDK resource protocol support
- Existing content discovery module (`vibey/mcp/discovery/`)

## Deliverables

1. Architecture design document (this task plan)
2. Base provider interface implementation
3. Resource manager skeleton
4. Updated `resources/__init__.py` exports
