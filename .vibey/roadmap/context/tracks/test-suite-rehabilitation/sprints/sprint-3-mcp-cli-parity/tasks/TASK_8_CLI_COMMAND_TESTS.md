# Task 8: Add Comprehensive CLI Command Tests

## Task Metadata
- **ID:** `01KCMKD53HSHBCSGAERGW7NVKT`
- **Sprint:** Sprint 3: MCP/CLI Parity & Integration Tests
- **Priority:** Medium
- **Complexity:** Complex
- **Type:** Testing
- **Estimated Effort:** 4-6 hours

## Objective
Achieve 100% test coverage for all CLI commands, testing both happy paths and error cases, with verification that CLI and MCP outputs match for unified commands.

## Current State Analysis

### CLI Command Structure
- **Total Commands:** 169
- **Unified Commands:** 16 (in `vibey/unified/commands/`)
- **Legacy Commands:** 153 (in `vibey/cli/commands.py`)

### Command Groups
- `roadmap` - Roadmap management (~40 commands)
- `deploy` - Platform deployment (~15 commands)
- `docs` - Documentation generation (~5 commands)
- `parity` - Parity checking (~3 commands)
- `mcp` - MCP server management (~5 commands)
- Others

## Implementation Steps

### Step 1: Create CLI Test Infrastructure
**File:** `tests/cli/conftest.py`
```python
import pytest
from click.testing import CliRunner
from pathlib import Path

@pytest.fixture
def cli_runner():
    """Create Click test runner."""
    return CliRunner()

@pytest.fixture
def cli_with_roadmap(tmp_path, cli_runner):
    """Create CLI runner with initialized roadmap."""
    # Set up .vibey/roadmap structure
    roadmap_dir = tmp_path / ".vibey" / "roadmap"
    roadmap_dir.mkdir(parents=True)

    # Create sample data
    tracks_dir = roadmap_dir / "tracks"
    tracks_dir.mkdir()
    # ... create sample YAML files

    # Initialize database
    db_path = roadmap_dir / "roadmap.db"
    # ... initialize SQLite

    return cli_runner, tmp_path
```

### Step 2: Test Unified Commands via CLI
**File:** `tests/cli/test_unified_commands.py`
```python
import pytest
from click.testing import CliRunner
from vibey.cli.main import cli

class TestRoadmapStatusCommand:
    def test_status_success(self, cli_with_roadmap):
        runner, root = cli_with_roadmap
        result = runner.invoke(cli, ["roadmap", "status"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "Tracks:" in result.output or "Track" in result.output

    def test_status_no_roadmap_shows_error(self, cli_runner, tmp_path):
        result = cli_runner.invoke(cli, ["roadmap", "status"])
        # Should handle missing roadmap gracefully
        assert result.exit_code != 0 or "not found" in result.output.lower()

class TestRoadmapShowCommand:
    def test_show_valid_item(self, cli_with_roadmap):
        runner, root = cli_with_roadmap
        result = runner.invoke(cli, ["roadmap", "show", "01KC..."])
        assert result.exit_code == 0

    def test_show_invalid_item_returns_error(self, cli_with_roadmap):
        runner, root = cli_with_roadmap
        result = runner.invoke(cli, ["roadmap", "show", "invalid"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()

class TestRoadmapStartCommand:
    def test_start_task_success(self, cli_with_roadmap):
        runner, root = cli_with_roadmap
        result = runner.invoke(cli, ["roadmap", "start", "01KC..."])
        assert result.exit_code == 0
        assert "started" in result.output.lower() or "in progress" in result.output.lower()

    def test_start_already_started_task(self, cli_with_roadmap):
        runner, root = cli_with_roadmap
        # Start once
        runner.invoke(cli, ["roadmap", "start", "01KC..."])
        # Start again
        result = runner.invoke(cli, ["roadmap", "start", "01KC..."])
        # Should either succeed (idempotent) or show appropriate message
        pass

class TestRoadmapCompleteCommand:
    def test_complete_in_progress_task(self, cli_with_roadmap):
        runner, root = cli_with_roadmap
        # First start the task
        runner.invoke(cli, ["roadmap", "start", "01KC..."])
        # Then complete it
        result = runner.invoke(cli, ["roadmap", "complete", "01KC..."])
        assert result.exit_code == 0

    def test_complete_not_started_task_fails(self, cli_with_roadmap):
        runner, root = cli_with_roadmap
        result = runner.invoke(cli, ["roadmap", "complete", "01KC..."])
        # Should fail - can't complete task that isn't started
        assert result.exit_code != 0
```

### Step 3: Test CLI/MCP Output Parity
**File:** `tests/cli/test_cli_mcp_parity.py`
```python
import pytest
import json
from click.testing import CliRunner
from vibey.cli.main import cli
from vibey.unified.adapters.mcp_adapter import handle_unified_tool_call

class TestCLIMCPOutputParity:
    """Verify CLI and MCP produce equivalent outputs."""

    @pytest.mark.asyncio
    async def test_roadmap_status_parity(self, cli_with_roadmap):
        runner, root = cli_with_roadmap

        # Get CLI output
        cli_result = runner.invoke(cli, ["roadmap", "status", "--format", "json"])

        # Get MCP output
        mcp_result = await handle_unified_tool_call(
            "vibey_roadmap_status",
            {},
            root_dir=root
        )

        # Compare data structures
        # (exact comparison depends on output format)
        assert cli_result.exit_code == 0
        assert mcp_result is not None

    @pytest.mark.asyncio
    async def test_roadmap_show_parity(self, cli_with_roadmap):
        runner, root = cli_with_roadmap
        item_id = "01KC..."

        cli_result = runner.invoke(cli, ["roadmap", "show", item_id, "--format", "json"])
        mcp_result = await handle_unified_tool_call(
            "vibey_roadmap_show",
            {"item_id": item_id},
            root_dir=root
        )

        # Compare outputs
        pass
```

### Step 4: Test Deploy Commands
**File:** `tests/cli/test_deploy_commands.py`
```python
import pytest
from click.testing import CliRunner
from vibey.cli.main import cli

class TestDeployListCommand:
    def test_list_platforms(self, cli_runner):
        result = cli_runner.invoke(cli, ["deploy", "list"])
        assert result.exit_code == 0
        assert "claude-code" in result.output.lower() or "cursor" in result.output.lower()

class TestDeployRunCommand:
    def test_deploy_dry_run(self, cli_with_roadmap):
        runner, root = cli_with_roadmap
        result = runner.invoke(cli, ["deploy", "run", "--platform", "cursor", "--dry-run"])
        assert result.exit_code == 0
        assert "dry run" in result.output.lower()

    def test_deploy_invalid_platform(self, cli_with_roadmap):
        runner, root = cli_with_roadmap
        result = runner.invoke(cli, ["deploy", "run", "--platform", "invalid"])
        assert result.exit_code != 0
```

### Step 5: Test Docs Commands
**File:** `tests/cli/test_docs_commands.py`
```python
import pytest
from click.testing import CliRunner
from vibey.cli.main import cli

class TestDocsGenerateCLI:
    def test_generate_cli_reference(self, cli_with_roadmap, tmp_path):
        runner, root = cli_with_roadmap
        output = tmp_path / "CLI_REFERENCE.md"
        result = runner.invoke(cli, ["docs", "generate-cli", "-o", str(output)])
        assert result.exit_code == 0
        assert output.exists()

class TestDocsCheckDrift:
    def test_check_drift_no_drift(self, cli_with_roadmap):
        runner, root = cli_with_roadmap
        result = runner.invoke(cli, ["docs", "check-drift"])
        # May pass or fail depending on state
        pass
```

### Step 6: Test Parity Commands
**File:** `tests/cli/test_parity_commands.py`
```python
import pytest
from click.testing import CliRunner
from vibey.cli.main import cli

class TestParityCheck:
    def test_parity_check_runs(self, cli_runner):
        result = cli_runner.invoke(cli, ["parity", "check"])
        assert result.exit_code in [0, 1]  # 0 = pass, 1 = violations
        assert "Parity" in result.output

    def test_parity_check_verbose(self, cli_runner):
        result = cli_runner.invoke(cli, ["parity", "check", "--verbose"])
        assert "commands" in result.output.lower()

class TestParityReport:
    def test_parity_report_json(self, cli_runner):
        result = cli_runner.invoke(cli, ["parity", "report", "--format", "json"])
        assert result.exit_code == 0
        # Should be valid JSON
        import json
        data = json.loads(result.output)
        assert "total_commands" in data
```

### Step 7: Test Error Messages
**File:** `tests/cli/test_error_messages.py`
```python
import pytest
from click.testing import CliRunner
from vibey.cli.main import cli

class TestErrorMessages:
    def test_missing_required_argument(self, cli_runner):
        result = cli_runner.invoke(cli, ["roadmap", "show"])
        assert result.exit_code != 0
        assert "missing" in result.output.lower() or "required" in result.output.lower()

    def test_invalid_option(self, cli_runner):
        result = cli_runner.invoke(cli, ["roadmap", "status", "--invalid-option"])
        assert result.exit_code != 0

    def test_helpful_error_messages(self, cli_runner):
        result = cli_runner.invoke(cli, ["roadmap", "show", "invalid-id"])
        # Should suggest valid format or show help
        pass
```

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `tests/cli/conftest.py` | Create/Expand | CLI test fixtures |
| `tests/cli/test_unified_commands.py` | Create | Test unified CLI commands |
| `tests/cli/test_cli_mcp_parity.py` | Create | Verify CLI/MCP output match |
| `tests/cli/test_deploy_commands.py` | Create | Deploy command tests |
| `tests/cli/test_docs_commands.py` | Create | Docs command tests |
| `tests/cli/test_parity_commands.py` | Create | Parity command tests |
| `tests/cli/test_error_messages.py` | Create | Error handling tests |

## Acceptance Criteria

- [ ] All unified commands tested via CLI
- [ ] All deploy commands tested
- [ ] All docs commands tested
- [ ] All parity commands tested
- [ ] CLI/MCP output parity verified for unified commands
- [ ] Error messages are helpful
- [ ] Coverage ≥100% for CLI commands
- [ ] All tests pass in CI

## Test Execution
```bash
# Run CLI tests
pytest tests/cli/ -v

# Run with coverage
pytest tests/cli/ --cov=vibey/cli --cov-report=term-missing
```

## Dependencies
- pytest
- click (CliRunner)
- pytest-asyncio (for parity tests)

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| CLI state dependencies | Isolated tmp_path per test |
| Output format changes | Test structure not exact strings |
| Interactive prompts | Use CliRunner with input |
