# MCP Server Testing Guide

**Version:** 1.0.0
**Date:** 2025-11-10
**Status:** Complete

---

## Overview

This directory contains comprehensive integration tests for the Vibey MCP Server. The tests validate the complete flow from tool handlers through the adapter layer to the roadmap system.

**Test Coverage:**
- **Task Tools:** 15+ test cases (200+ lines)
- **Sprint Tools:** 12+ test cases (180+ lines)
- **Query Tools:** 13+ test cases (190+ lines)
- **Validation:** 8+ test cases (100 lines)
- **Total:** 40+ test cases across 4 test files

---

## Quick Start

### Install Dependencies

```bash
# From repository root
pip install -r requirements.txt
```

**Required Packages:**
- `pytest>=7.4.0` - Testing framework
- `pytest-asyncio>=0.21.0` - Async test support
- `pytest-cov>=4.1.0` - Coverage reporting

### Run All Tests

```bash
# From repository root
python3 -m pytest framework/mcp/tests/ -v
```

### Run Specific Test Files

```bash
# Task tools only
python3 -m pytest framework/mcp/tests/test_task_tools.py -v

# Sprint tools only
python3 -m pytest framework/mcp/tests/test_sprint_tools.py -v

# Query tools only
python3 -m pytest framework/mcp/tests/test_query_tools.py -v

# Validation only
python3 -m pytest framework/mcp/tests/test_validation.py -v
```

### Run with Coverage

```bash
# Generate coverage report
python3 -m pytest framework/mcp/tests/ --cov=framework/mcp --cov-report=html

# View coverage report
open htmlcov/index.html
```

---

## Test Structure

### Directory Layout

```
framework/mcp/tests/
├── README.md                   # This file
├── conftest.py                 # Pytest configuration
├── test_task_tools.py          # Task management tests
├── test_sprint_tools.py        # Sprint management tests
├── test_query_tools.py         # Query tool tests
└── test_validation.py          # Validation utility tests
```

### Test Organization

Each test file follows this structure:

```python
# 1. Imports
import pytest
from unittest.mock import Mock
from framework.mcp.tools.xxx_tools import ...
from framework.mcp.adapters.roadmap_adapter import RoadmapAdapter
from framework.mcp.utils.errors import ...

# 2. Fixtures
@pytest.fixture
def mock_adapter():
    return Mock(spec=RoadmapAdapter)

# 3. Test Classes (grouped by functionality)
@pytest.mark.asyncio
class TestToolName:
    async def test_success_case(self, mock_adapter):
        # Arrange
        mock_adapter.method.return_value = {...}

        # Act
        result = await handle_tool({...}, mock_adapter)

        # Assert
        assert result["isError"] is False
        assert "expected text" in result["content"][0]["text"]
        mock_adapter.method.assert_called_once_with(...)

    async def test_error_case(self, mock_adapter):
        # Test error handling
        ...
```

---

## Test Files

### 1. test_task_tools.py (200+ lines)

**Purpose:** Integration tests for task management tools

**Tools Tested:**
- `vibey_start_task` - Start a task
- `vibey_complete_task` - Complete a task
- `vibey_query_task` - Query task details

**Test Classes:**
- `TestStartTask` - Task start operations
- `TestCompleteTask` - Task completion operations
- `TestQueryTask` - Task query operations
- `TestTaskToolsValidation` - Input validation
- `TestTaskToolsErrorHandling` - Error scenarios

**Key Test Cases:**
- ✅ Successful task start
- ✅ Task not found error
- ✅ Invalid state transition error
- ✅ Task completion with tokens
- ✅ Task completion without tokens
- ✅ Already completed task
- ✅ Query task with full data
- ✅ Query task with minimal data
- ✅ Invalid task ID format
- ✅ Negative tokens handling
- ✅ Unexpected error handling
- ✅ File permission errors

**Example:**
```bash
python3 -m pytest framework/mcp/tests/test_task_tools.py::TestStartTask::test_start_task_success -v
```

### 2. test_sprint_tools.py (180+ lines)

**Purpose:** Integration tests for sprint management tools

**Tools Tested:**
- `vibey_start_sprint` - Start a sprint
- `vibey_complete_sprint` - Complete a sprint
- `vibey_query_sprint` - Query sprint details
- `vibey_refresh_progress` - Refresh progress calculations

**Test Classes:**
- `TestStartSprint` - Sprint start operations
- `TestCompleteSprint` - Sprint completion operations
- `TestRefreshProgress` - Progress refresh operations
- `TestQuerySprint` - Sprint query operations
- `TestSprintToolsValidation` - Input validation

**Key Test Cases:**
- ✅ Successful sprint start
- ✅ Sprint not found error
- ✅ Already started sprint
- ✅ Sprint completion with metrics
- ✅ Invalid state transition
- ✅ Progress refresh with progressions
- ✅ Progress refresh with no changes
- ✅ Query sprint with full progress
- ✅ Query sprint with completion gates
- ✅ Query sprint with production gates
- ✅ Invalid sprint ID format
- ✅ Refresh progress with no arguments

**Example:**
```bash
python3 -m pytest framework/mcp/tests/test_sprint_tools.py::TestRefreshProgress -v
```

### 3. test_query_tools.py (190+ lines)

**Purpose:** Integration tests for query tools

**Tools Tested:**
- `vibey_query_track` - Query track details
- `vibey_list_blockers` - List blockers
- `vibey_list_dependencies` - List dependencies
- `vibey_roadmap_status` - Get roadmap overview

**Test Classes:**
- `TestQueryTrack` - Track query operations
- `TestListBlockers` - Blocker listing operations
- `TestListDependencies` - Dependency listing operations
- `TestRoadmapStatus` - Roadmap status operations
- `TestQueryToolsErrorHandling` - Error scenarios

**Key Test Cases:**
- ✅ Query track with progress
- ✅ Track not found error
- ✅ List blockers with results
- ✅ List blockers with no results
- ✅ List blockers filtered by object ID
- ✅ List dependencies unsatisfied only
- ✅ List dependencies including satisfied
- ✅ Dependencies with no results
- ✅ Roadmap status with active sprints
- ✅ Roadmap status with no active sprints
- ✅ Unexpected error handling

**Example:**
```bash
python3 -m pytest framework/mcp/tests/test_query_tools.py::TestRoadmapStatus -v
```

### 4. test_validation.py (100 lines)

**Purpose:** Tests for validation utility functions

**Functions Tested:**
- `validate_task_id()` - Task ID format validation
- `validate_sprint_id()` - Sprint ID format validation
- `validate_track_id()` - Track ID format validation
- `validate_tool_input()` - JSON schema validation

**Test Classes:**
- `TestTaskIDValidation` - Task ID validation
- `TestSprintIDValidation` - Sprint ID validation
- `TestToolInputValidation` - Schema validation

**Example:**
```bash
python3 -m pytest framework/mcp/tests/test_validation.py -v
```

---

## Mock-Based Testing Strategy

### Why Mocks?

The tests use `unittest.mock.Mock` to isolate tool handlers from the adapter and roadmap system. This approach:

- ✅ **Fast execution** - No file I/O or subprocess calls
- ✅ **Deterministic** - No dependency on .vibey/ state
- ✅ **Focused** - Tests tool logic, not roadmap system
- ✅ **Easy setup** - No test fixtures or data files needed

### Mock Pattern

```python
@pytest.fixture
def mock_adapter():
    """Create a mock roadmap adapter for testing."""
    return Mock(spec=RoadmapAdapter)

async def test_tool(self, mock_adapter):
    # Arrange: Configure mock behavior
    mock_adapter.method.return_value = {
        "success": True,
        "data": "value"
    }

    # Act: Call tool handler
    result = await handle_tool(arguments, mock_adapter)

    # Assert: Verify results
    assert result["isError"] is False
    assert "expected" in result["content"][0]["text"]

    # Assert: Verify mock was called correctly
    mock_adapter.method.assert_called_once_with("expected_arg")
```

### What Gets Tested?

**Tool Handlers:**
- ✅ Argument extraction
- ✅ Validation calls
- ✅ Adapter method calls
- ✅ Response formatting
- ✅ Error handling
- ✅ Success messages

**What's NOT Tested (Integration Tests):**
- ❌ Actual file I/O (roadmap YAML)
- ❌ Subprocess execution (roadmap scripts)
- ❌ Roadmap system logic (separate tests)

---

## Async Test Support

### pytest-asyncio

All tool handlers are async functions, requiring `pytest-asyncio`:

```python
@pytest.mark.asyncio
async def test_async_tool(self, mock_adapter):
    result = await handle_tool(args, mock_adapter)
    assert result["isError"] is False
```

**Configuration:** Set in `conftest.py`

```python
import sys
from pathlib import Path

# Add framework to Python path for imports
framework_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(framework_root))
```

---

## Running Tests

### Common Commands

```bash
# All tests with verbose output
python3 -m pytest framework/mcp/tests/ -v

# All tests with summary
python3 -m pytest framework/mcp/tests/

# Specific test class
python3 -m pytest framework/mcp/tests/test_task_tools.py::TestStartTask -v

# Specific test method
python3 -m pytest framework/mcp/tests/test_task_tools.py::TestStartTask::test_start_task_success -v

# Stop on first failure
python3 -m pytest framework/mcp/tests/ -x

# Run last failed tests
python3 -m pytest framework/mcp/tests/ --lf

# Run with output capture disabled (see print statements)
python3 -m pytest framework/mcp/tests/ -s
```

### Test Output

**Successful Test:**
```
test_task_tools.py::TestStartTask::test_start_task_success PASSED [1/40]
```

**Failed Test:**
```
test_task_tools.py::TestStartTask::test_start_task_success FAILED [1/40]

================================= FAILURES =================================
________________________ test_start_task_success _______________________

self = <test_task_tools.TestStartTask object at 0x...>
mock_adapter = <Mock spec='RoadmapAdapter' id='...'>

    async def test_start_task_success(self, mock_adapter):
        mock_adapter.start_task.return_value = {...}
>       result = await handle_start_task({...}, mock_adapter)
E       AssertionError: ...

framework/mcp/tests/test_task_tools.py:45: AssertionError
```

---

## Coverage Reporting

### Generate Coverage

```bash
# HTML report
python3 -m pytest framework/mcp/tests/ --cov=framework/mcp --cov-report=html

# Terminal report
python3 -m pytest framework/mcp/tests/ --cov=framework/mcp --cov-report=term

# Both
python3 -m pytest framework/mcp/tests/ --cov=framework/mcp --cov-report=html --cov-report=term
```

### View Coverage

```bash
# Open HTML report
open htmlcov/index.html
```

### Coverage Goals

**Target Coverage:**
- **Tools:** 90%+ (handlers, formatting, error handling)
- **Adapter:** 80%+ (method calls, integration points)
- **Utils:** 95%+ (validation, error classes)

**Coverage Gaps (Expected):**
- MCP server scaffold (awaiting SDK)
- Resource handlers (Sprint 3)
- Subscription handlers (Sprint 3)

---

## Adding New Tests

### Test File Template

```python
"""
Integration tests for [component name].

Tests the complete flow: tool handler → adapter → roadmap system.
"""

import pytest
from unittest.mock import Mock

from framework.mcp.tools.xxx_tools import (
    handle_xxx_tool,
)
from framework.mcp.adapters.roadmap_adapter import RoadmapAdapter
from framework.mcp.utils.errors import (
    XxxNotFoundError,
    InvalidStateTransitionError,
)


@pytest.fixture
def mock_adapter():
    """Create a mock roadmap adapter for testing."""
    return Mock(spec=RoadmapAdapter)


@pytest.mark.asyncio
class TestToolName:
    """Test vibey_tool_name tool."""

    async def test_success_case(self, mock_adapter):
        """Test successful operation."""
        # Arrange
        mock_adapter.method.return_value = {
            "success": True,
            "data": "value"
        }

        # Act
        result = await handle_xxx_tool(
            {"arg": "value"},
            mock_adapter
        )

        # Assert
        assert result["isError"] is False
        assert "expected text" in result["content"][0]["text"]
        mock_adapter.method.assert_called_once_with("value")

    async def test_error_case(self, mock_adapter):
        """Test error handling."""
        # Arrange
        mock_adapter.method.side_effect = XxxNotFoundError("xxx-id")

        # Act
        result = await handle_xxx_tool(
            {"arg": "value"},
            mock_adapter
        )

        # Assert
        assert result["isError"] is True
        assert "not found" in result["content"][0]["text"].lower()
```

### Best Practices

1. **One test file per tool module** - `test_xxx_tools.py` for `xxx_tools.py`
2. **Group tests by tool** - Use test classes for organization
3. **Clear test names** - `test_operation_scenario` format
4. **Arrange-Act-Assert** - Clear test structure
5. **Test both paths** - Success and error cases
6. **Mock at boundary** - Mock adapter, test handler logic
7. **Verify mock calls** - Use `assert_called_once_with()`
8. **Test error messages** - Verify user-facing text

---

## Continuous Integration

### GitHub Actions (Future)

```yaml
name: MCP Server Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python3 -m pytest framework/mcp/tests/ --cov=framework/mcp --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Troubleshooting

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'framework'`

**Solution:** Run from repository root, `conftest.py` adds framework to path

```bash
# Correct
cd /path/to/vibey
python3 -m pytest framework/mcp/tests/ -v

# Incorrect
cd /path/to/vibey/framework/mcp/tests
python3 -m pytest . -v
```

### Pytest Not Found

**Problem:** `No module named pytest`

**Solution:** Install dependencies

```bash
pip install -r requirements.txt
```

### Async Test Warnings

**Problem:** `RuntimeWarning: coroutine 'test_xxx' was never awaited`

**Solution:** Add `@pytest.mark.asyncio` decorator

```python
@pytest.mark.asyncio
async def test_async_operation(self, mock_adapter):
    result = await handle_tool(args, mock_adapter)
```

### Mock Attribute Errors

**Problem:** `AttributeError: Mock object has no attribute 'method'`

**Solution:** Configure mock return value before calling

```python
# Configure first
mock_adapter.method.return_value = {...}

# Then call
result = await handle_tool(args, mock_adapter)
```

---

## Test Metrics

### Current Statistics

**Test Files:** 4
**Test Classes:** 13
**Test Cases:** 40+
**Lines of Test Code:** ~670 lines
**Coverage:** (Run `pytest --cov` to generate)

**Test Breakdown:**
- Task Tools: 15+ tests (success, errors, validation)
- Sprint Tools: 12+ tests (lifecycle, gates, refresh)
- Query Tools: 13+ tests (track, blockers, dependencies, status)
- Validation: 8+ tests (ID formats, schema validation)

### Test Execution Time

**Expected:** < 1 second (mock-based, no I/O)

```bash
$ python3 -m pytest framework/mcp/tests/ -v
================================ 40 passed in 0.34s ================================
```

---

## Next Steps

### Sprint 3: Resources & Subscriptions

When implementing Sprint 3, add:

1. **`test_resource_handlers.py`**
   - Test resource URI handling
   - Test data serialization
   - Test caching behavior

2. **`test_subscriptions.py`**
   - Test subscription lifecycle
   - Test notification triggering
   - Test state change events

### Sprint 4: Production Readiness

1. **Integration Tests**
   - Test with real `.vibey/` data
   - Test end-to-end workflows
   - Test MCP protocol compliance

2. **Performance Tests**
   - Benchmark tool response times
   - Test resource caching
   - Test concurrent requests

---

## Resources

### Documentation

- **MCP Server Design:** `docs/development/MCP_SERVER_DESIGN.md`
- **Sprint 1 Complete:** `docs/development/MCP_SPRINT_1_TASKS.md`
- **Sprint 2 Complete:** `docs/development/MCP_SPRINT_2_COMPLETE.md`
- **User Guide:** `framework/mcp/README.md`

### External Links

- **pytest:** https://docs.pytest.org/
- **pytest-asyncio:** https://pytest-asyncio.readthedocs.io/
- **unittest.mock:** https://docs.python.org/3/library/unittest.mock.html
- **MCP Protocol:** https://spec.modelcontextprotocol.io/

---

**Testing Guide Version:** 1.0.0
**Date:** 2025-11-10
**Status:** Complete
