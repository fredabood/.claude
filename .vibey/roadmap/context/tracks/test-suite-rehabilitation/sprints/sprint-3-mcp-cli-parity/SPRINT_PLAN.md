# Sprint 3: MCP/CLI Parity & Integration Tests

## Overview
- **Track:** Test Suite Rehabilitation
- **Sprint ID:** 01KCMTMZQF4CD2GCV1GCJB8KKE
- **Tasks:** 11
- **Focus:** Achieve 100% MCP/CLI parity and comprehensive integration tests

## Success Criteria
- [ ] MCP tools match CLI commands 1:1 (169 tools for 169 commands)
- [ ] MCP tool test coverage: 95%+
- [ ] Integration tests for full request/response cycle
- [ ] CI enforces coverage thresholds
- [ ] Parity enforcement mechanism in place

---

## Task 1: Root Cause Analysis: MCP/CLI Drift
**ID:** `01KCMKG14YEJT49VVQ7GJQNWBW`
**Priority:** High | **Complexity:** Medium | **Type:** Development

### Problem
MCP tools drifted from CLI commands despite architecture designed to prevent this.

### Investigation Areas
1. **CLI Command Addition Process:**
   - How are new CLI commands added?
   - Is there a checklist requiring MCP equivalent?
   - Review recent CLI additions without MCP tools

2. **MCP Tool Addition Process:**
   - How are new MCP tools added?
   - Is there linkage to CLI definitions?
   - Why are they independently maintained?

3. **Existing Enforcement:**
   - What checks exist today?
   - Why did they fail?
   - Review CI/CD pipeline

### Deliverables
```markdown
# MCP/CLI Drift Root Cause Analysis

## Current State
- CLI Commands: 169
- MCP Tools: 76
- Parity: 45%

## Root Causes Identified
1. [Root cause 1]
2. [Root cause 2]

## Recommended Fixes
1. [Architectural fix]
2. [Process fix]
3. [Enforcement fix]
```

### Acceptance Criteria
- [ ] Root causes documented
- [ ] Architectural fixes proposed
- [ ] Implementation plan for parity enforcement

---

## Task 2: Audit MCP to CLI Command Mapping for Gaps
**ID:** `01KCMKFMMSAEC4VFAVXDQRV68Y`
**Priority:** High | **Complexity:** Complex | **Type:** Development

### Implementation Steps
1. Extract all CLI commands:
   ```bash
   vibey --help 2>/dev/null
   # Parse all command groups
   ```

2. Extract all MCP tools:
   ```python
   from vibey.mcp.server import get_all_tools
   tools = get_all_tools()
   ```

3. Create mapping document:
   ```markdown
   | CLI Command | MCP Tool | Status |
   |-------------|----------|--------|
   | roadmap status | roadmap_status | ✅ |
   | roadmap start | task_start | ✅ |
   | deploy audit | - | ❌ MISSING |
   ```

4. Categorize gaps:
   - Easy to add (simple mapping)
   - Medium (needs design)
   - Complex (architectural)

### Deliverables
- `MCP_CLI_PARITY_AUDIT.md`
- Gap categorization
- Implementation priority list

### Acceptance Criteria
- [ ] All 169 CLI commands audited
- [ ] Gaps categorized by complexity
- [ ] Priority list for implementation

---

## Task 3: Add Missing MCP Tools to Achieve CLI Parity
**ID:** `01KCMKGGPPCKATCJ9KMAF5DZE8`
**Priority:** High | **Complexity:** Complex | **Type:** Development

### Files to Modify
- `vibey/mcp/tools/` - Add new tool modules
- `vibey/mcp/server.py` - Register new tools

### Implementation Pattern
```python
# For each missing CLI command, create MCP tool:

@mcp_tool
def deploy_audit(platform: str) -> dict:
    """
    Audit deployment configuration for a platform.

    Equivalent CLI: vibey deploy audit --platform <platform>
    """
    from vibey.operations.deploy import audit_deployment
    return audit_deployment(platform)
```

### Implementation Steps
1. For each gap from audit:
   - Create tool function
   - Map CLI parameters to MCP parameters
   - Implement using same operations layer
   - Add to tool registry

2. Maintain CLI/MCP parity:
   - Same parameter names where possible
   - Same return data structure
   - Same error messages

### Acceptance Criteria
- [ ] All 93 missing tools implemented (169 - 76)
- [ ] Each tool tested
- [ ] 100% parity achieved

---

## Task 4: Implement MCP/CLI Parity Enforcement
**ID:** `01KCMKG7Z740QY2CCWTFRZ6P2D`
**Priority:** High | **Complexity:** Complex | **Type:** Development

### Design Options

**Option A: Auto-generate MCP tools from CLI**
```python
# Generate MCP tools from Click commands
for command in cli.commands.values():
    generate_mcp_tool(command)
```

**Option B: Shared command registry**
```python
# Both CLI and MCP consume same registry
COMMANDS = {
    "roadmap_status": CommandDef(
        handler=roadmap_status_handler,
        params=[...],
        description="..."
    )
}
```

**Option C: CI parity check**
```yaml
# .github/workflows/parity.yml
- name: Check MCP/CLI Parity
  run: python scripts/check_parity.py
  # Fails if any CLI command lacks MCP equivalent
```

### Recommended: Option C (immediate) + Option A (long-term)

### Implementation Steps
1. Create parity check script:
   ```python
   # scripts/check_parity.py
   def check_parity():
       cli_commands = get_all_cli_commands()
       mcp_tools = get_all_mcp_tools()

       missing = cli_commands - mcp_tools
       if missing:
           print(f"Missing MCP tools: {missing}")
           sys.exit(1)
   ```

2. Add to CI pipeline

3. Plan auto-generation for future

### Acceptance Criteria
- [ ] CI check implemented
- [ ] Parity violations fail builds
- [ ] Documentation updated

---

## Task 5: Add MCP Tool Unit Tests
**ID:** `01KCMGW1PRG8ADMD0M4Q83PYQC`
**Priority:** High | **Complexity:** Complex | **Type:** Testing

### Files to Create
- `tests/mcp/test_tools.py`
- `tests/mcp/test_roadmap_tools.py`
- `tests/mcp/test_deploy_tools.py`
- etc.

### Test Pattern
```python
@pytest.fixture
def mcp_context():
    """Create MCP request context."""
    return MCPContext(roadmap_path=tmp_path)

def test_roadmap_status_tool(mcp_context):
    result = roadmap_status(mcp_context)
    assert "tracks" in result
    assert isinstance(result["tracks"], list)

def test_task_start_tool(mcp_context, sample_task):
    result = task_start(mcp_context, task_id=sample_task.id)
    assert result["status"] == "in_progress"
```

### Coverage Target
- 95% coverage for all 76+ MCP tools
- Test happy path and error cases

### Acceptance Criteria
- [ ] All MCP tools have unit tests
- [ ] Coverage ≥95%
- [ ] Error handling tested

---

## Task 6: Add MCP Server Integration Tests
**ID:** `01KCMGW5F2CF5XNFPWBGF9YZH0`
**Priority:** High | **Complexity:** Complex | **Type:** Testing

### Test full request/response cycle:
```python
async def test_mcp_request_response():
    server = MCPServer()
    request = {
        "method": "tools/call",
        "params": {
            "name": "roadmap_status",
            "arguments": {}
        }
    }
    response = await server.handle_request(request)
    assert response["result"]["tracks"] is not None
```

### Areas to Test
- Tool discovery
- Parameter validation
- Error responses
- Timeout handling
- Concurrent requests

### Acceptance Criteria
- [ ] Full request cycle tested
- [ ] Error handling tested
- [ ] Performance acceptable

---

## Tasks 7-11: Remaining Tasks

### Task 7: Add Tests for All Operations Modules
**ID:** `01KCMKCXP4MZHWR7W6S9WZ1CF0`
Test all `vibey/operations/` submodules.

### Task 8: Add Comprehensive CLI Command Tests
**ID:** `01KCMKD53HSHBCSGAERGW7NVKT`
Expand CLI test coverage to 100%.

### Task 9: Implement CI Test Coverage Enforcement
**ID:** `01KCMKDJ7JYGHGSYME2V7EEG6Q`
Add CI step to enforce 100% coverage, fail on drops.

### Task 10: Add MCP Error Documentation
**ID:** `01KCMGW9859M6C6VPKKHB5BQMR`
Document error responses for all MCP tools.

### Task 11: Add MCP Workflow Examples
**ID:** `01KCMGWD1SYQYZB676RM0896YR`
Document common MCP tool sequences.

---

## Sprint Completion Checklist
- [ ] 100% MCP/CLI parity achieved
- [ ] All MCP tools tested (95%+ coverage)
- [ ] Integration tests passing
- [ ] CI enforcement in place
- [ ] Documentation complete
