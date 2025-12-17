# Task 5: Add MCP Tool Unit Tests

## Task Metadata
- **ID:** `01KCMGW1PRG8ADMD0M4Q83PYQC`
- **Sprint:** Sprint 3: MCP/CLI Parity & Integration Tests
- **Priority:** High
- **Complexity:** Complex
- **Type:** Testing
- **Estimated Effort:** 4-6 hours

## Objective
Achieve 95%+ test coverage for all MCP tools, including both unified commands and legacy MCP tools.

## Current State Analysis

### Unified Commands (16 tools)
Located in `vibey/unified/commands/`:
- `roadmap.py`: 10 commands (status, show, start, complete, list-tracks, list-sprints, list-tasks, db-status, db-rebuild, db-validate)
- `deploy.py`: 3 commands (list, run, status)
- `docs.py`: 3 commands (generate-cli, generate-mcp, check-drift)

### Legacy MCP Tools (~76 tools)
Located in `vibey/mcp/tools/`:
- Need to audit existing test coverage
- Many may lack comprehensive tests

## Implementation Steps

### Step 1: Audit Current MCP Test Coverage
```bash
# Check existing MCP tests
find tests -name "*mcp*" -type f
pytest tests/mcp/ --cov=vibey/mcp --cov-report=term-missing
```

### Step 2: Create Test Infrastructure
**File:** `tests/mcp/conftest.py`
```python
import pytest
from pathlib import Path
from vibey.unified import COMMAND_REGISTRY

@pytest.fixture
def mcp_test_context(tmp_path):
    """Create isolated MCP test context."""
    roadmap_dir = tmp_path / ".vibey" / "roadmap"
    roadmap_dir.mkdir(parents=True)
    # Create minimal roadmap structure
    return {"root_dir": tmp_path, "roadmap_dir": roadmap_dir}

@pytest.fixture
def unified_tools():
    """Get all unified MCP tools."""
    return COMMAND_REGISTRY.list_for_interface("mcp")
```

### Step 3: Test Unified Tools via MCP Adapter
**File:** `tests/mcp/test_unified_tools.py`
```python
import pytest
from vibey.unified.adapters.mcp_adapter import (
    generate_mcp_tool_definition,
    handle_unified_tool_call,
)
from vibey.unified import COMMAND_REGISTRY

class TestUnifiedToolDefinitions:
    """Test MCP tool definition generation."""

    def test_all_unified_tools_have_definitions(self, unified_tools):
        for spec in unified_tools:
            definition = generate_mcp_tool_definition(spec)
            assert "name" in definition
            assert "description" in definition
            assert "inputSchema" in definition

    def test_tool_schema_has_required_fields(self, unified_tools):
        for spec in unified_tools:
            definition = generate_mcp_tool_definition(spec)
            schema = definition["inputSchema"]
            assert schema["type"] == "object"
            assert "properties" in schema

class TestUnifiedToolExecution:
    """Test MCP tool execution."""

    @pytest.mark.asyncio
    async def test_roadmap_status_tool(self, mcp_test_context):
        result = await handle_unified_tool_call(
            "vibey_roadmap_status",
            {},
            root_dir=mcp_test_context["root_dir"]
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_invalid_tool_name_raises(self):
        with pytest.raises(ValueError, match="Unknown tool"):
            await handle_unified_tool_call("invalid_tool", {})
```

### Step 4: Test Legacy MCP Tools
**File:** `tests/mcp/test_legacy_tools.py`
```python
import pytest
from vibey.mcp.server import get_all_tools

class TestLegacyToolDiscovery:
    def test_all_legacy_tools_registered(self):
        tools = get_all_tools()
        assert len(tools) >= 76  # Known tool count

    def test_tools_have_valid_schemas(self):
        tools = get_all_tools()
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert tool["description"]  # Not empty

class TestLegacyToolExecution:
    # Add tests for each tool category
    pass
```

### Step 5: Test Parameter Validation
**File:** `tests/mcp/test_tool_parameters.py`
```python
import pytest

class TestParameterValidation:
    @pytest.mark.asyncio
    async def test_missing_required_parameter(self):
        # Test that missing required params raise appropriate error
        pass

    @pytest.mark.asyncio
    async def test_invalid_parameter_type(self):
        # Test type validation
        pass

    @pytest.mark.asyncio
    async def test_default_values_applied(self):
        # Test that defaults work
        pass
```

### Step 6: Test Error Responses
**File:** `tests/mcp/test_tool_errors.py`
```python
import pytest

class TestToolErrorHandling:
    @pytest.mark.asyncio
    async def test_not_found_error(self):
        # Test 404-style errors
        pass

    @pytest.mark.asyncio
    async def test_validation_error(self):
        # Test input validation errors
        pass

    @pytest.mark.asyncio
    async def test_internal_error_handling(self):
        # Test graceful error handling
        pass
```

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `tests/mcp/conftest.py` | Create | Shared fixtures |
| `tests/mcp/test_unified_tools.py` | Create | Test unified commands via MCP |
| `tests/mcp/test_legacy_tools.py` | Create | Test legacy MCP tools |
| `tests/mcp/test_tool_parameters.py` | Create | Parameter validation tests |
| `tests/mcp/test_tool_errors.py` | Create | Error handling tests |

## Acceptance Criteria

- [ ] All 16 unified tools have unit tests
- [ ] All ~76 legacy tools have at least basic tests
- [ ] Parameter validation tested for all required params
- [ ] Error handling tested (not found, validation, internal)
- [ ] Coverage ≥95% for `vibey/mcp/` and `vibey/unified/adapters/mcp_adapter.py`
- [ ] All tests pass in CI

## Test Execution
```bash
# Run MCP tests
pytest tests/mcp/ -v

# Run with coverage
pytest tests/mcp/ --cov=vibey/mcp --cov=vibey/unified/adapters/mcp_adapter --cov-report=term-missing

# Target: 95%+ coverage
```

## Dependencies
- pytest
- pytest-asyncio
- pytest-cov

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Legacy tools have side effects | Use isolated tmp_path fixtures |
| Async test complexity | Use pytest-asyncio consistently |
| Coverage gaps in error paths | Explicitly test error scenarios |
