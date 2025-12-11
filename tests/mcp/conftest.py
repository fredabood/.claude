"""
Test fixtures for MCP module tests.

Provides fixtures for testing resources, prompts, and discovery components.
"""

import pytest
from pathlib import Path


@pytest.fixture
def content_root(tmp_path):
    """Create temporary content directory with test data."""
    # Create directory structure
    content_dir = tmp_path / "vibey" / "content"
    (content_dir / "workflows").mkdir(parents=True)
    (content_dir / "templates" / "handoffs").mkdir(parents=True)
    (content_dir / "agents").mkdir(parents=True)

    # Create test workflow
    workflow_content = '''---
id: test-workflow
name: Test Workflow
type: development
complexity: medium
duration: 2 hours
description: A test workflow for unit testing
steps:
  - order: 1
    name: Step 1
    agent: test-agent
    duration: 1 hour
  - order: 2
    name: Step 2
    agent: test-agent-2
    duration: 1 hour
quality_gates:
  - name: Test Coverage
    type: testing
    threshold: 80
    blocking: true
inputs:
  - name: project_name
    type: string
    required: true
    description: Name of the project
---
# Test Workflow

This is a test workflow for unit testing.

## Steps

1. Step 1 - Do something
2. Step 2 - Do something else
'''
    (content_dir / "workflows" / "test-workflow.md").write_text(workflow_content)

    # Create test handoff
    handoff_content = '''---
id: test-handoff
name: Test Handoff
version: 1.0.0
from_agent: agent-a
to_agents:
  - agent-b
  - agent-c
purpose: Test handoff template for unit testing
description: A simple handoff for testing
variables:
  - name: test_var
    type: string
    required: true
    description: Test variable
  - name: optional_var
    type: string
    required: false
    description: Optional variable
    default: default_value
---
# Test Handoff: {{ handoff_title }}

**Date:** {{ handoff_date }}

## Variables
- Test Variable: {{ test_var }}
- Optional Variable: {{ optional_var }}
'''
    (content_dir / "templates" / "handoffs" / "test-handoff.md").write_text(
        handoff_content
    )

    # Create test agent
    agent_content = '''---
id: test-agent
name: Test Agent
type: development
description: A test agent for unit testing
triggers:
  keywords:
    - test
    - testing
inputs:
  - name: task_description
    type: string
    required: true
    description: What to test
outputs:
  - name: test_results
    type: string
    description: Test results
---
# Test Agent

This is a test agent for unit testing.

## Instructions

Follow these test instructions.
'''
    (content_dir / "agents" / "test-agent.md").write_text(agent_content)

    return tmp_path


@pytest.fixture
def roadmap_root(tmp_path):
    """Create temporary roadmap directory."""
    roadmap_dir = tmp_path / ".vibey" / "roadmap"
    roadmap_dir.mkdir(parents=True)
    return roadmap_dir


@pytest.fixture
def resource_manager(content_root):
    """Create ResourceManager with test content."""
    from vibey.mcp.resources.manager import ResourceManager

    return ResourceManager(content_root)


@pytest.fixture
def prompt_manager(content_root, roadmap_root):
    """Create PromptManager with test content."""
    from vibey.mcp.prompts.manager import PromptManager

    return PromptManager(content_root, roadmap_root)


@pytest.fixture
def tool_discovery(content_root):
    """Create ToolDiscovery with test content."""
    from vibey.mcp.discovery import ToolDiscovery

    return ToolDiscovery(content_root)


@pytest.fixture
def handoff_discovery(content_root):
    """Create HandoffDiscovery with test content."""
    from vibey.mcp.discovery.handoffs import HandoffDiscovery

    return HandoffDiscovery(content_root)


@pytest.fixture
def quality_gate_provider(content_root):
    """Create QualityGatePromptProvider with test content."""
    from vibey.mcp.prompts.quality_gates import QualityGatePromptProvider

    return QualityGatePromptProvider(content_root)


# Use actual content root for integration tests
@pytest.fixture
def real_content_root():
    """Return actual vibey repository root for integration tests."""
    return Path(__file__).parent.parent.parent
