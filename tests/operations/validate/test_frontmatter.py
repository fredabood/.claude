"""
Tests for vibey.operations.validate.frontmatter module.

Tests frontmatter validation for agents, workflows, and handoffs.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from vibey.operations.validate.frontmatter import (
    extract_frontmatter,
    validate_agent,
    validate_workflow,
    validate_handoff,
    AssetValidationResult,
    FrontmatterValidationReport,
    FrontmatterValidator,
    validate_assets,
    REQUIRED_FIELDS,
    VALID_AGENT_TYPES,
    VALID_WORKFLOW_TYPES,
    VALID_PRIORITIES,
    VALID_INPUT_TYPES,
)


class TestExtractFrontmatter:
    """Test extract_frontmatter function."""

    def test_valid_frontmatter(self):
        """Test extracting valid frontmatter."""
        content = """---
id: test-agent
name: Test Agent
type: core
version: "1.0.0"
---

# Agent Content
"""
        frontmatter, body = extract_frontmatter(content)
        assert frontmatter is not None
        assert frontmatter["id"] == "test-agent"
        assert frontmatter["name"] == "Test Agent"
        assert "# Agent Content" in body

    def test_no_frontmatter(self):
        """Test content without frontmatter."""
        content = "# Just a markdown file"
        frontmatter, body = extract_frontmatter(content)
        assert frontmatter is None
        assert body == content

    def test_incomplete_frontmatter(self):
        """Test content with incomplete frontmatter markers."""
        content = """---
id: test
name: Test
"""
        frontmatter, body = extract_frontmatter(content)
        assert frontmatter is None
        assert body == content

    def test_invalid_yaml_frontmatter(self):
        """Test content with invalid YAML in frontmatter."""
        content = """---
invalid: yaml: [broken
---

Content
"""
        frontmatter, body = extract_frontmatter(content)
        assert frontmatter is not None
        assert "_error" in frontmatter

    def test_empty_frontmatter(self):
        """Test content with empty frontmatter."""
        content = """---

---

# Content
"""
        frontmatter, body = extract_frontmatter(content)
        assert frontmatter is None or frontmatter == {}

    def test_frontmatter_with_lists(self):
        """Test frontmatter containing lists."""
        content = """---
id: test
inputs:
  - name: input1
  - name: input2
---
"""
        frontmatter, body = extract_frontmatter(content)
        assert frontmatter is not None
        assert len(frontmatter["inputs"]) == 2


class TestValidateAgent:
    """Test validate_agent function."""

    def test_valid_agent_frontmatter(self):
        """Test validating complete agent frontmatter."""
        frontmatter = {
            "id": "test-agent",
            "name": "Test Agent",
            "type": "core",
            "version": "1.0.0",
        }
        errors = validate_agent(frontmatter)
        assert len(errors) == 0

    def test_missing_required_fields(self):
        """Test missing required fields."""
        frontmatter = {"id": "test-agent"}
        errors = validate_agent(frontmatter)
        assert any("name" in e for e in errors)
        assert any("type" in e for e in errors)
        assert any("version" in e for e in errors)

    def test_invalid_agent_type(self):
        """Test invalid agent type."""
        frontmatter = {
            "id": "test",
            "name": "Test",
            "type": "invalid_type",
            "version": "1.0.0",
        }
        errors = validate_agent(frontmatter)
        assert any("Invalid agent type" in e for e in errors)

    def test_all_valid_agent_types(self):
        """Test all valid agent types are accepted."""
        for agent_type in VALID_AGENT_TYPES:
            frontmatter = {
                "id": "test",
                "name": "Test",
                "type": agent_type,
                "version": "1.0.0",
            }
            errors = validate_agent(frontmatter)
            assert len(errors) == 0

    def test_invalid_trigger_priority(self):
        """Test invalid trigger priority."""
        frontmatter = {
            "id": "test",
            "name": "Test",
            "type": "core",
            "version": "1.0.0",
            "triggers": {"priority": "invalid"},
        }
        errors = validate_agent(frontmatter)
        assert any("Invalid priority" in e for e in errors)

    def test_valid_trigger_priorities(self):
        """Test all valid priorities are accepted."""
        for priority in VALID_PRIORITIES:
            frontmatter = {
                "id": "test",
                "name": "Test",
                "type": "core",
                "version": "1.0.0",
                "triggers": {"priority": priority},
            }
            errors = validate_agent(frontmatter)
            assert len(errors) == 0

    def test_input_missing_name(self):
        """Test input without name field."""
        frontmatter = {
            "id": "test",
            "name": "Test",
            "type": "core",
            "version": "1.0.0",
            "inputs": [{"type": "string"}],
        }
        errors = validate_agent(frontmatter)
        assert any("missing 'name'" in e for e in errors)

    def test_input_invalid_type(self):
        """Test input with invalid type."""
        frontmatter = {
            "id": "test",
            "name": "Test",
            "type": "core",
            "version": "1.0.0",
            "inputs": [{"name": "input1", "type": "invalid_type"}],
        }
        errors = validate_agent(frontmatter)
        assert any("invalid type" in e for e in errors)

    def test_all_valid_input_types(self):
        """Test all valid input types are accepted."""
        for input_type in VALID_INPUT_TYPES:
            frontmatter = {
                "id": "test",
                "name": "Test",
                "type": "core",
                "version": "1.0.0",
                "inputs": [{"name": "input1", "type": input_type}],
            }
            errors = validate_agent(frontmatter)
            assert len(errors) == 0

    def test_output_missing_name(self):
        """Test output without name field."""
        frontmatter = {
            "id": "test",
            "name": "Test",
            "type": "core",
            "version": "1.0.0",
            "outputs": [{"description": "output"}],
        }
        errors = validate_agent(frontmatter)
        assert any("Output 0 missing 'name'" in e for e in errors)


class TestValidateWorkflow:
    """Test validate_workflow function."""

    def test_valid_workflow_frontmatter(self):
        """Test validating complete workflow frontmatter."""
        frontmatter = {
            "id": "test-workflow",
            "name": "Test Workflow",
            "type": "development",
            "version": "1.0.0",
        }
        errors = validate_workflow(frontmatter)
        assert len(errors) == 0

    def test_missing_required_fields(self):
        """Test missing required fields."""
        frontmatter = {"id": "test"}
        errors = validate_workflow(frontmatter)
        assert any("name" in e for e in errors)
        assert any("type" in e for e in errors)
        assert any("version" in e for e in errors)

    def test_invalid_workflow_type(self):
        """Test invalid workflow type."""
        frontmatter = {
            "id": "test",
            "name": "Test",
            "type": "invalid_type",
            "version": "1.0.0",
        }
        errors = validate_workflow(frontmatter)
        assert any("Invalid workflow type" in e for e in errors)

    def test_all_valid_workflow_types(self):
        """Test all valid workflow types are accepted."""
        for workflow_type in VALID_WORKFLOW_TYPES:
            frontmatter = {
                "id": "test",
                "name": "Test",
                "type": workflow_type,
                "version": "1.0.0",
            }
            errors = validate_workflow(frontmatter)
            assert len(errors) == 0

    def test_step_missing_order(self):
        """Test step without order field."""
        frontmatter = {
            "id": "test",
            "name": "Test",
            "type": "development",
            "version": "1.0.0",
            "steps": [{"name": "Step 1"}],
        }
        errors = validate_workflow(frontmatter)
        assert any("missing 'order'" in e for e in errors)

    def test_step_missing_name(self):
        """Test step without name field."""
        frontmatter = {
            "id": "test",
            "name": "Test",
            "type": "development",
            "version": "1.0.0",
            "steps": [{"order": 1}],
        }
        errors = validate_workflow(frontmatter)
        assert any("missing 'name'" in e for e in errors)

    def test_valid_steps(self):
        """Test valid steps are accepted."""
        frontmatter = {
            "id": "test",
            "name": "Test",
            "type": "development",
            "version": "1.0.0",
            "steps": [
                {"order": 1, "name": "Step 1"},
                {"order": 2, "name": "Step 2"},
            ],
        }
        errors = validate_workflow(frontmatter)
        assert len(errors) == 0

    def test_input_missing_name(self):
        """Test workflow input without name field."""
        frontmatter = {
            "id": "test",
            "name": "Test",
            "type": "development",
            "version": "1.0.0",
            "inputs": [{"description": "input"}],
        }
        errors = validate_workflow(frontmatter)
        assert any("missing 'name'" in e for e in errors)


class TestValidateHandoff:
    """Test validate_handoff function."""

    def test_valid_handoff_frontmatter(self):
        """Test validating complete handoff frontmatter."""
        frontmatter = {
            "id": "test-handoff",
            "name": "Test Handoff",
            "version": "1.0.0",
        }
        errors = validate_handoff(frontmatter)
        assert len(errors) == 0

    def test_missing_required_fields(self):
        """Test missing required fields."""
        frontmatter = {"id": "test"}
        errors = validate_handoff(frontmatter)
        assert any("name" in e for e in errors)
        assert any("version" in e for e in errors)

    def test_variable_missing_name(self):
        """Test variable without name field."""
        frontmatter = {
            "id": "test",
            "name": "Test",
            "version": "1.0.0",
            "variables": [{"type": "string"}],
        }
        errors = validate_handoff(frontmatter)
        assert any("missing 'name'" in e for e in errors)

    def test_valid_variables(self):
        """Test valid variables are accepted."""
        frontmatter = {
            "id": "test",
            "name": "Test",
            "version": "1.0.0",
            "variables": [
                {"name": "var1"},
                {"name": "var2", "type": "string"},
            ],
        }
        errors = validate_handoff(frontmatter)
        assert len(errors) == 0


class TestAssetValidationResult:
    """Test AssetValidationResult dataclass."""

    def test_valid_result(self):
        """Test creating valid result."""
        result = AssetValidationResult(
            filepath=Path("test.md"),
            asset_type="agents",
            is_valid=True,
            errors=[],
        )
        assert result.is_valid
        assert len(result.errors) == 0

    def test_invalid_result(self):
        """Test creating invalid result."""
        result = AssetValidationResult(
            filepath=Path("test.md"),
            asset_type="agents",
            is_valid=False,
            errors=["Error 1", "Error 2"],
        )
        assert not result.is_valid
        assert len(result.errors) == 2


class TestFrontmatterValidationReport:
    """Test FrontmatterValidationReport dataclass."""

    def test_empty_report(self):
        """Test empty report is valid."""
        report = FrontmatterValidationReport()
        assert report.is_valid
        assert report.assets_checked == 0

    def test_add_valid_result(self):
        """Test adding valid result."""
        report = FrontmatterValidationReport()
        result = AssetValidationResult(
            filepath=Path("test.md"),
            asset_type="agents",
            is_valid=True,
        )
        report.add_result(result)
        assert report.assets_checked == 1
        assert report.valid_count == 1
        assert report.invalid_count == 0
        assert report.is_valid

    def test_add_invalid_result(self):
        """Test adding invalid result."""
        report = FrontmatterValidationReport()
        result = AssetValidationResult(
            filepath=Path("test.md"),
            asset_type="agents",
            is_valid=False,
            errors=["Error"],
        )
        report.add_result(result)
        assert report.assets_checked == 1
        assert report.valid_count == 0
        assert report.invalid_count == 1
        assert not report.is_valid

    def test_mixed_results(self):
        """Test adding mixed results."""
        report = FrontmatterValidationReport()
        report.add_result(
            AssetValidationResult(
                filepath=Path("valid.md"), asset_type="agents", is_valid=True
            )
        )
        report.add_result(
            AssetValidationResult(
                filepath=Path("invalid.md"),
                asset_type="agents",
                is_valid=False,
                errors=["Error"],
            )
        )
        assert report.assets_checked == 2
        assert report.valid_count == 1
        assert report.invalid_count == 1
        assert not report.is_valid


class TestFrontmatterValidator:
    """Test FrontmatterValidator class."""

    @pytest.fixture
    def validator(self, tmp_path):
        """Create a validator instance."""
        return FrontmatterValidator(tmp_path)

    def test_validate_valid_file(self, tmp_path):
        """Test validating a file with valid frontmatter."""
        agent_file = tmp_path / "test-agent.md"
        agent_file.write_text(
            """---
id: test-agent
name: Test Agent
type: core
version: "1.0.0"
---

# Agent Content
"""
        )
        validator = FrontmatterValidator(tmp_path)
        result = validator.validate_file(agent_file, "agents")
        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_file_no_frontmatter(self, tmp_path):
        """Test validating a file without frontmatter."""
        agent_file = tmp_path / "test-agent.md"
        agent_file.write_text("# Just a markdown file")
        validator = FrontmatterValidator(tmp_path)
        result = validator.validate_file(agent_file, "agents")
        assert not result.is_valid
        assert "No frontmatter found" in result.errors[0]

    def test_validate_file_unreadable(self, tmp_path):
        """Test validating an unreadable file."""
        validator = FrontmatterValidator(tmp_path)
        result = validator.validate_file(tmp_path / "nonexistent.md", "agents")
        assert not result.is_valid
        assert "Cannot read file" in result.errors[0]

    def test_validate_file_yaml_error(self, tmp_path):
        """Test validating a file with YAML parse error."""
        agent_file = tmp_path / "test-agent.md"
        agent_file.write_text(
            """---
invalid: yaml: [broken
---

Content
"""
        )
        validator = FrontmatterValidator(tmp_path)
        result = validator.validate_file(agent_file, "agents")
        assert not result.is_valid
        assert "YAML parse error" in result.errors[0]

    def test_validate_file_unknown_asset_type(self, tmp_path):
        """Test validating with unknown asset type."""
        agent_file = tmp_path / "test.md"
        agent_file.write_text(
            """---
id: test
---

Content
"""
        )
        validator = FrontmatterValidator(tmp_path)
        result = validator.validate_file(agent_file, "unknown_type")
        assert not result.is_valid
        assert "Unknown asset type" in result.errors[0]

    @patch("vibey.operations.validate.frontmatter.get_agents_dir")
    def test_validate_assets_agents(self, mock_get_agents, tmp_path):
        """Test validating all agents."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        mock_get_agents.return_value = agents_dir

        # Create a valid agent
        (agents_dir / "valid.md").write_text(
            """---
id: valid-agent
name: Valid Agent
type: core
version: "1.0.0"
---
"""
        )
        # Create an invalid agent
        (agents_dir / "invalid.md").write_text("# No frontmatter")

        validator = FrontmatterValidator(tmp_path)
        report = validator.validate_assets("agents")
        assert report.assets_checked == 2
        assert report.valid_count == 1
        assert report.invalid_count == 1

    @patch("vibey.operations.validate.frontmatter.get_agents_dir")
    def test_validate_assets_skips_readme(self, mock_get_agents, tmp_path):
        """Test that README.md files are skipped."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        mock_get_agents.return_value = agents_dir

        # Create a README (should be skipped)
        (agents_dir / "README.md").write_text("# Readme")
        # Create a valid agent
        (agents_dir / "agent.md").write_text(
            """---
id: agent
name: Agent
type: core
version: "1.0.0"
---
"""
        )

        validator = FrontmatterValidator(tmp_path)
        report = validator.validate_assets("agents")
        assert report.assets_checked == 1  # Only the agent, not README


class TestValidateAssetsFunction:
    """Test validate_assets convenience function."""

    @patch("vibey.operations.validate.frontmatter.get_agents_dir")
    @patch("vibey.operations.validate.frontmatter.get_workflows_dir")
    @patch("vibey.operations.validate.frontmatter.get_templates_dir")
    def test_validate_all(self, mock_templates, mock_workflows, mock_agents, tmp_path):
        """Test validating all asset types."""
        # Set up mock directories
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        mock_agents.return_value = agents_dir

        workflows_dir = tmp_path / "workflows"
        workflows_dir.mkdir()
        mock_workflows.return_value = workflows_dir

        templates_dir = tmp_path / "templates"
        handoffs_dir = templates_dir / "handoffs"
        handoffs_dir.mkdir(parents=True)
        mock_templates.return_value = templates_dir

        report = validate_assets(tmp_path, asset_type="all")
        assert isinstance(report, FrontmatterValidationReport)

    @patch("vibey.operations.validate.frontmatter.get_agents_dir")
    def test_validate_specific_type(self, mock_agents, tmp_path):
        """Test validating specific asset type."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        mock_agents.return_value = agents_dir

        report = validate_assets(tmp_path, asset_type="agents")
        assert isinstance(report, FrontmatterValidationReport)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
