"""
Test deliverable type normalization in YAML loader.

Tests that the yaml_loader correctly normalizes legacy deliverable type
values to current enum values (e.g., "configuration" → "config").
"""

import pytest
from vibey.roadmap.models.common import DeliverableType
from vibey.roadmap.serialization.yaml_loader import load_task
from vibey.roadmap.models.task import Task
import tempfile
import os


def test_deliverable_type_config_accepted():
    """Test that 'config' deliverable type is accepted (current standard)."""
    yaml_content = """
task:
  id: test-sprint-1-task-001
  sprint_id: test-sprint-1
  track_id: test-track
  roadmap_id: vibey-framework-v2
  task_type: development
  title: Test Task
  description: Test task with config deliverable
  estimated_tokens: 1000
  deliverables:
    - type: config
      paths:
        - config/example.yaml
  status: not_started
  priority: medium
  complexity: simple
  metadata:
    created_at: 2025-11-20T00:00:00Z
    last_updated: 2025-11-20T00:00:00Z
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        temp_path = f.name

    try:
        data = load_task(temp_path)
        assert isinstance(data, Task)
        assert len(data.deliverables) == 1
        assert data.deliverables[0].type == DeliverableType.CONFIG
        assert data.deliverables[0].paths == ['config/example.yaml']
    finally:
        os.unlink(temp_path)


def test_deliverable_type_configuration_normalized():
    """Test that legacy 'configuration' type is normalized to 'config'."""
    yaml_content = """
task:
  id: test-sprint-1-task-002
  sprint_id: test-sprint-1
  track_id: test-track
  roadmap_id: vibey-framework-v2
  task_type: development
  title: Test Task with Legacy Type
  description: Test task with legacy configuration deliverable type
  estimated_tokens: 1000
  deliverables:
    - type: configuration
      paths:
        - config/legacy.yaml
  status: not_started
  priority: medium
  complexity: simple
  metadata:
    created_at: 2025-11-20T00:00:00Z
    last_updated: 2025-11-20T00:00:00Z
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        temp_path = f.name

    try:
        data = load_task(temp_path)
        assert isinstance(data, Task)
        assert len(data.deliverables) == 1
        # Verify that "configuration" was normalized to "config"
        assert data.deliverables[0].type == DeliverableType.CONFIG
        assert data.deliverables[0].paths == ['config/legacy.yaml']
    finally:
        os.unlink(temp_path)


def test_deliverable_type_mixed_formats():
    """Test that both 'config' and 'configuration' can coexist and are normalized."""
    yaml_content = """
task:
  id: test-sprint-1-task-003
  sprint_id: test-sprint-1
  track_id: test-track
  roadmap_id: vibey-framework-v2
  task_type: development
  title: Test Task with Mixed Types
  description: Test task with both config and configuration types
  estimated_tokens: 1000
  deliverables:
    - type: config
      paths:
        - config/new.yaml
    - type: configuration
      paths:
        - config/old.yaml
    - type: code
      paths:
        - src/main.py
  status: not_started
  priority: medium
  complexity: simple
  metadata:
    created_at: 2025-11-20T00:00:00Z
    last_updated: 2025-11-20T00:00:00Z
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        temp_path = f.name

    try:
        data = load_task(temp_path)
        assert isinstance(data, Task)
        assert len(data.deliverables) == 3

        # First deliverable: "config" → CONFIG
        assert data.deliverables[0].type == DeliverableType.CONFIG
        assert data.deliverables[0].paths == ['config/new.yaml']

        # Second deliverable: "configuration" → CONFIG (normalized)
        assert data.deliverables[1].type == DeliverableType.CONFIG
        assert data.deliverables[1].paths == ['config/old.yaml']

        # Third deliverable: "code" → CODE
        assert data.deliverables[2].type == DeliverableType.CODE
        assert data.deliverables[2].paths == ['src/main.py']
    finally:
        os.unlink(temp_path)


def test_deliverable_type_all_standard_values():
    """Test that all standard DeliverableType enum values are accepted."""
    yaml_content = """
task:
  id: test-sprint-1-task-004
  sprint_id: test-sprint-1
  track_id: test-track
  roadmap_id: vibey-framework-v2
  task_type: development
  title: Test Task with All Types
  description: Test task with all deliverable types
  estimated_tokens: 1000
  deliverables:
    - type: code
      paths:
        - src/main.py
    - type: test
      paths:
        - tests/test_main.py
    - type: documentation
      paths:
        - docs/README.md
    - type: config
      paths:
        - config/settings.yaml
    - type: other
      paths:
        - misc/notes.txt
  status: not_started
  priority: medium
  complexity: simple
  metadata:
    created_at: 2025-11-20T00:00:00Z
    last_updated: 2025-11-20T00:00:00Z
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        temp_path = f.name

    try:
        data = load_task(temp_path)
        assert isinstance(data, Task)
        assert len(data.deliverables) == 5

        assert data.deliverables[0].type == DeliverableType.CODE
        assert data.deliverables[1].type == DeliverableType.TEST
        assert data.deliverables[2].type == DeliverableType.DOCUMENTATION
        assert data.deliverables[3].type == DeliverableType.CONFIG
        assert data.deliverables[4].type == DeliverableType.OTHER
    finally:
        os.unlink(temp_path)
