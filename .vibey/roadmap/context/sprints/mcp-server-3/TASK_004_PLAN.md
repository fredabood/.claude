# Task 004: Design MCP Prompts Architecture

**Task ID:** 01KC79XW02AZ2V0JCE08C2VZ38
**Sprint:** MCP Resources, Prompts & Handoff Discovery
**Complexity:** Medium
**Type:** Research/Design

## Problem Statement

MCP Prompts provide a way to expose pre-configured prompt templates that AI assistants can use. Unlike tools (which perform actions) or resources (which provide content), prompts are structured templates designed to guide AI behavior. The Vibey framework has quality gates, review checklists, and workflow guidance that would benefit from prompt-based access.

## Current State

### Prompts Module Status
```python
# vibey/mcp/prompts/__init__.py
"""
MCP Prompts.
Prompt templates for common roadmap workflows.
"""
# Prompts will be implemented in Sprint 3
__all__ = []
```

### Server Capabilities
```python
# server.py:130-132
"prompts": {
    "listChanged": False  # Prompts not implemented in Sprint 1
}
```

### Existing Prompt-Like Content
1. **Quality Gates** - Checklists embedded in workflows
2. **Agent Instructions** - Guidance in agent markdown files
3. **Workflow Steps** - Step-by-step instructions
4. **Review Checklists** - Code review, security audit templates

## Implementation Plan

### Phase 1: MCP Prompt Protocol Understanding

**1.1 MCP Prompt Specification**
```typescript
// MCP Prompt types (from protocol spec)
interface Prompt {
  name: string;
  description?: string;
  arguments?: PromptArgument[];
}

interface PromptArgument {
  name: string;
  description?: string;
  required?: boolean;
}

interface GetPromptResult {
  description?: string;
  messages: PromptMessage[];
}

interface PromptMessage {
  role: "user" | "assistant";
  content: TextContent | ImageContent | EmbeddedResource;
}
```

**1.2 Vibey Prompt Categories**
| Category | Purpose | Arguments |
|----------|---------|-----------|
| Quality Gate | Run quality check | gate_type, threshold, context |
| Code Review | Structured review | code_diff, review_type, severity_filter |
| Sprint Planning | Plan sprint | sprint_goals, team_capacity, dependencies |
| Task Breakdown | Break down task | task_description, complexity, constraints |
| Workflow Guidance | Execute workflow | workflow_id, current_step, context |

### Phase 2: Prompt Provider Architecture

**2.1 Define PromptProvider Interface**
```python
# vibey/mcp/prompts/provider.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class PromptArgument:
    """Prompt argument definition."""
    name: str
    description: Optional[str] = None
    required: bool = False

@dataclass
class PromptDefinition:
    """MCP Prompt definition."""
    name: str
    description: Optional[str] = None
    arguments: List[PromptArgument] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PromptMessage:
    """Message in a prompt response."""
    role: str  # "user" or "assistant"
    content: str

@dataclass
class PromptResult:
    """Result of getting a prompt."""
    description: Optional[str] = None
    messages: List[PromptMessage] = field(default_factory=list)

class PromptProvider(ABC):
    """Base class for MCP prompt providers."""

    @abstractmethod
    def get_prompts(self) -> List[PromptDefinition]:
        """Return all prompts this provider offers."""
        pass

    @abstractmethod
    async def get_prompt(
        self,
        name: str,
        arguments: Optional[Dict[str, str]] = None
    ) -> PromptResult:
        """Generate prompt messages for the given prompt name."""
        pass

    def supports_prompt(self, name: str) -> bool:
        """Check if this provider handles the given prompt."""
        return any(p.name == name for p in self.get_prompts())
```

**2.2 Define PromptManager**
```python
# vibey/mcp/prompts/manager.py
class PromptManager:
    """Manages all prompt providers and handles MCP prompt operations."""

    def __init__(self, content_root: Path, roadmap_root: Path):
        self.content_root = content_root
        self.roadmap_root = roadmap_root
        self.providers: Dict[str, PromptProvider] = {}
        self._register_providers()

    def _register_providers(self):
        """Register all prompt providers."""
        self.providers['quality-gates'] = QualityGatePromptProvider(self.content_root)
        self.providers['workflows'] = WorkflowPromptProvider(self.content_root)
        self.providers['reviews'] = ReviewPromptProvider(self.content_root)
        self.providers['planning'] = PlanningPromptProvider(self.roadmap_root)

    def list_prompts(self) -> List[Dict[str, Any]]:
        """List all available prompts."""
        prompts = []
        for provider in self.providers.values():
            for prompt in provider.get_prompts():
                prompts.append({
                    "name": prompt.name,
                    "description": prompt.description,
                    "arguments": [
                        {
                            "name": arg.name,
                            "description": arg.description,
                            "required": arg.required
                        }
                        for arg in prompt.arguments
                    ]
                })
        return prompts

    async def get_prompt(
        self,
        name: str,
        arguments: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Get prompt messages for the given prompt name."""
        for provider in self.providers.values():
            if provider.supports_prompt(name):
                result = await provider.get_prompt(name, arguments)
                return {
                    "description": result.description,
                    "messages": [
                        {"role": m.role, "content": {"type": "text", "text": m.content}}
                        for m in result.messages
                    ]
                }
        raise PromptNotFoundError(f"Unknown prompt: {name}")
```

### Phase 3: Prompt Types Design

**3.1 Quality Gate Prompts**
```python
# Prompt: vibey_quality_gate_check
# Arguments: gate_type (required), threshold (optional), file_path (optional)
# Returns: Structured prompt to perform quality check

PromptDefinition(
    name="vibey_quality_gate_check",
    description="Run a quality gate check on code or documentation",
    arguments=[
        PromptArgument(name="gate_type", description="Type of gate: security, testing, logging, documentation", required=True),
        PromptArgument(name="threshold", description="Pass threshold percentage (default: 80)"),
        PromptArgument(name="file_path", description="Specific file to check")
    ]
)
```

**3.2 Workflow Guidance Prompts**
```python
# Prompt: vibey_workflow_step
# Arguments: workflow_id (required), step_number (optional)
# Returns: Guidance for executing workflow step

PromptDefinition(
    name="vibey_workflow_step",
    description="Get guidance for executing a workflow step",
    arguments=[
        PromptArgument(name="workflow_id", description="Workflow to execute", required=True),
        PromptArgument(name="step_number", description="Step number (default: 1)"),
        PromptArgument(name="context", description="Additional context for the step")
    ]
)
```

**3.3 Review Prompts**
```python
# Prompt: vibey_code_review
# Arguments: review_type (required), severity (optional)
# Returns: Structured code review prompt

PromptDefinition(
    name="vibey_code_review",
    description="Structured code review prompt",
    arguments=[
        PromptArgument(name="review_type", description="Type: security, performance, maintainability, all", required=True),
        PromptArgument(name="severity_filter", description="Min severity: critical, high, medium, low"),
        PromptArgument(name="code_context", description="Code or diff to review")
    ]
)
```

**3.4 Planning Prompts**
```python
# Prompt: vibey_task_breakdown
# Arguments: task_description (required), complexity (optional)
# Returns: Prompt for breaking down task into subtasks

PromptDefinition(
    name="vibey_task_breakdown",
    description="Break down a complex task into subtasks",
    arguments=[
        PromptArgument(name="task_description", description="Description of the task", required=True),
        PromptArgument(name="complexity", description="Expected complexity: low, medium, high"),
        PromptArgument(name="constraints", description="Time or resource constraints")
    ]
)
```

### Phase 4: Server Integration Design

**4.1 Update Server Capabilities**
```python
def get_capabilities(self) -> Dict[str, Any]:
    return {
        "prompts": {
            "listChanged": True  # Support prompt list changes
        },
        ...
    }
```

**4.2 Add Prompt Handlers**
```python
# In VibeyMCPServer:
def list_prompts(self) -> List[Dict]:
    """List all available prompts for MCP prompts/list."""
    return self.prompt_manager.list_prompts()

async def get_prompt(self, name: str, arguments: Optional[Dict[str, str]] = None) -> Dict:
    """Get prompt messages for MCP prompts/get."""
    return await self.prompt_manager.get_prompt(name, arguments)
```

## Files to Create

| File | Purpose |
|------|---------|
| `vibey/mcp/prompts/provider.py` | Base PromptProvider class and data models |
| `vibey/mcp/prompts/manager.py` | PromptManager orchestration class |
| `vibey/mcp/prompts/exceptions.py` | Prompt-specific exceptions |
| `vibey/mcp/prompts/types.py` | Type definitions and dataclasses |

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/mcp/prompts/__init__.py` | Export new classes |
| `vibey/mcp/server.py` | Add prompt manager and MCP prompt methods |

## Success Criteria

1. [ ] PromptProvider interface designed
2. [ ] PromptManager class structure defined
3. [ ] 4 prompt categories identified with arguments
4. [ ] Server integration points documented
5. [ ] Type definitions complete
6. [ ] Architecture document created

## Dependencies

- MCP Python SDK prompt protocol support
- Task 001 (Resource architecture) for patterns

## Deliverables

1. Architecture design document (this task plan)
2. Base provider interface implementation
3. Prompt manager skeleton
4. Type definitions
5. Server integration design
