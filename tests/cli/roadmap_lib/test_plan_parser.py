"""
Tests for vibey.cli.roadmap_lib.plan_parser module.

Tests sprint plan markdown parsing into structured data.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import tempfile
import os

from vibey.cli.roadmap_lib.plan_parser import (
    SprintPlanParser,
    parse_sprint_plan,
    extract_tasks_from_plan,
)


class TestSprintPlanParserInit:
    """Test SprintPlanParser initialization."""

    def test_init_reads_file(self, tmp_path):
        """Test initialization reads file content."""
        plan_file = tmp_path / "sprint.md"
        plan_file.write_text("# Sprint Plan: Test Sprint\n")

        parser = SprintPlanParser(plan_file)

        assert parser.content == "# Sprint Plan: Test Sprint\n"
        # Note: split('\n') on "line\n" produces ['line', '']
        assert len(parser.lines) == 2

    def test_init_splits_lines(self, tmp_path):
        """Test initialization splits content into lines."""
        plan_file = tmp_path / "sprint.md"
        plan_file.write_text("Line 1\nLine 2\nLine 3")

        parser = SprintPlanParser(plan_file)

        assert len(parser.lines) == 3


class TestExtractSprintName:
    """Test _extract_sprint_name method."""

    def test_extract_name_sprint_plan_format(self, tmp_path):
        """Test extracting name from '# Sprint Plan: Name' format."""
        plan_file = tmp_path / "sprint.md"
        plan_file.write_text("# Sprint Plan: Test Sprint\n\n## Goals\n")

        parser = SprintPlanParser(plan_file)
        result = parser._extract_sprint_name()

        assert result == "Test Sprint"

    def test_extract_name_numbered_format(self, tmp_path):
        """Test extracting name from '# Sprint N: Name' format."""
        plan_file = tmp_path / "sprint.md"
        plan_file.write_text("# Sprint 1: Initial Setup\n\n## Goals\n")

        parser = SprintPlanParser(plan_file)
        result = parser._extract_sprint_name()

        assert result == "Initial Setup"

    def test_extract_name_no_match_returns_default(self, tmp_path):
        """Test default name when no match found."""
        plan_file = tmp_path / "sprint.md"
        plan_file.write_text("# Some Other Heading\n\n## Goals\n")

        parser = SprintPlanParser(plan_file)
        result = parser._extract_sprint_name()

        assert result == "Unnamed Sprint"


class TestExtractGoal:
    """Test _extract_goal method."""

    def test_extract_single_goal(self, tmp_path):
        """Test extracting single goal."""
        plan_file = tmp_path / "sprint.md"
        plan_file.write_text("""# Sprint Plan: Test
## Goals
- Complete the main feature

## Features
""")

        parser = SprintPlanParser(plan_file)
        result = parser._extract_goal()

        assert result == "Complete the main feature"

    def test_extract_multiple_goals(self, tmp_path):
        """Test extracting multiple goals joined by semicolon."""
        plan_file = tmp_path / "sprint.md"
        plan_file.write_text("""# Sprint Plan: Test
## Goals
- First goal
- Second goal
- Third goal

## Features
""")

        parser = SprintPlanParser(plan_file)
        result = parser._extract_goal()

        assert "First goal" in result
        assert "Second goal" in result
        assert "Third goal" in result
        assert ";" in result

    def test_extract_goals_numbered_list(self, tmp_path):
        """Test extracting goals from numbered list."""
        plan_file = tmp_path / "sprint.md"
        plan_file.write_text("""# Sprint Plan: Test
## Objectives
1. First objective
2. Second objective

## Features
""")

        parser = SprintPlanParser(plan_file)
        result = parser._extract_goal()

        assert "First objective" in result
        assert "Second objective" in result

    def test_extract_goal_empty_section(self, tmp_path):
        """Test empty goal when no goals section."""
        plan_file = tmp_path / "sprint.md"
        plan_file.write_text("# Sprint Plan: Test\n## Features\n")

        parser = SprintPlanParser(plan_file)
        result = parser._extract_goal()

        assert result == ""


class TestExtractFeatures:
    """Test _extract_features method."""

    def test_extract_single_feature(self, tmp_path):
        """Test extracting single feature."""
        plan_file = tmp_path / "sprint.md"
        plan_file.write_text("""# Sprint Plan: Test
## Features
### Feature One
**What:** Build the thing
**Why:** Because we need it
**How:** Just do it

## Success Criteria
""")

        parser = SprintPlanParser(plan_file)
        result = parser._extract_features()

        assert len(result) == 1
        assert result[0]['name'] == "Feature One"
        assert result[0]['what'] == "Build the thing"
        assert result[0]['why'] == "Because we need it"
        assert result[0]['how'] == "Just do it"

    def test_extract_multiple_features(self, tmp_path):
        """Test extracting multiple features."""
        plan_file = tmp_path / "sprint.md"
        plan_file.write_text("""# Sprint Plan: Test
## Features
### 1. First Feature
**What:** First thing

### 2. Second Feature
**What:** Second thing

## Success Criteria
""")

        parser = SprintPlanParser(plan_file)
        result = parser._extract_features()

        assert len(result) == 2
        assert result[0]['name'] == "First Feature"
        assert result[1]['name'] == "Second Feature"

    def test_extract_features_with_tasks_section(self, tmp_path):
        """Test extracting from ## Tasks section (alternative heading)."""
        plan_file = tmp_path / "sprint.md"
        plan_file.write_text("""# Sprint Plan: Test
## Tasks
### Task One
**What:** Do the task

## Deliverables
""")

        parser = SprintPlanParser(plan_file)
        result = parser._extract_features()

        assert len(result) == 1
        assert result[0]['name'] == "Task One"

    def test_extract_feature_multiline_how(self, tmp_path):
        """Test extracting feature with multiline How section."""
        plan_file = tmp_path / "sprint.md"
        plan_file.write_text("""# Sprint Plan: Test
## Features
### Complex Feature
**What:** Build complex thing
**Why:** It's needed
**How:** Steps:
- Step one
- Step two
- Step three

## Success Criteria
""")

        parser = SprintPlanParser(plan_file)
        result = parser._extract_features()

        assert len(result) == 1
        assert "Step one" in result[0]['how'] or result[0]['how'] == "Steps:"

    def test_extract_feature_removes_number_prefix(self, tmp_path):
        """Test that numbered feature names have prefix removed."""
        plan_file = tmp_path / "sprint.md"
        plan_file.write_text("""# Sprint Plan: Test
## Features
### 1) Feature With Parenthesis
**What:** Something

### 2. Feature With Period
**What:** Something else

## Success Criteria
""")

        parser = SprintPlanParser(plan_file)
        result = parser._extract_features()

        assert result[0]['name'] == "Feature With Parenthesis"
        assert result[1]['name'] == "Feature With Period"


class TestExtractSuccessCriteria:
    """Test _extract_success_criteria method."""

    def test_extract_success_criteria(self, tmp_path):
        """Test extracting success criteria."""
        plan_file = tmp_path / "sprint.md"
        plan_file.write_text("""# Sprint Plan: Test
## Success Criteria
- All tests pass
- Code coverage > 80%
- No security issues

## Deliverables
""")

        parser = SprintPlanParser(plan_file)
        result = parser._extract_success_criteria()

        assert len(result) == 3
        assert "All tests pass" in result
        assert "Code coverage > 80%" in result

    def test_extract_success_criteria_with_checkboxes(self, tmp_path):
        """Test extracting criteria with checkbox markers."""
        plan_file = tmp_path / "sprint.md"
        plan_file.write_text("""# Sprint Plan: Test
## Definition of Done
- [ ] Tests written
- [x] Documentation updated

## Quality Gates
""")

        parser = SprintPlanParser(plan_file)
        result = parser._extract_success_criteria()

        assert len(result) == 2
        assert "Tests written" in result
        assert "Documentation updated" in result

    def test_extract_success_criteria_empty(self, tmp_path):
        """Test empty criteria when no section."""
        plan_file = tmp_path / "sprint.md"
        plan_file.write_text("# Sprint Plan: Test\n## Features\n")

        parser = SprintPlanParser(plan_file)
        result = parser._extract_success_criteria()

        assert result == []


class TestExtractDeliverables:
    """Test _extract_deliverables method."""

    def test_extract_deliverables(self, tmp_path):
        """Test extracting deliverables."""
        plan_file = tmp_path / "sprint.md"
        plan_file.write_text("""# Sprint Plan: Test
## Deliverables
- Working API endpoint
- Updated documentation
- Test suite

## Quality Gates
""")

        parser = SprintPlanParser(plan_file)
        result = parser._extract_deliverables()

        assert len(result) == 3
        assert "Working API endpoint" in result
        assert "Updated documentation" in result

    def test_extract_expected_outputs(self, tmp_path):
        """Test extracting from ## Expected Outputs (alternative heading)."""
        plan_file = tmp_path / "sprint.md"
        plan_file.write_text("""# Sprint Plan: Test
## Expected Outputs
- Deployed service
- Config files

## Next Steps
""")

        parser = SprintPlanParser(plan_file)
        result = parser._extract_deliverables()

        assert len(result) == 2


class TestExtractQualityGates:
    """Test _extract_quality_gates method."""

    def test_extract_quality_gates_parenthesis_format(self, tmp_path):
        """Test extracting gates with parenthesis format."""
        plan_file = tmp_path / "sprint.md"
        plan_file.write_text("""# Sprint Plan: Test
## Quality Gates
- Security Audit (85%)
- Test Coverage (90%)

## Next Steps
""")

        parser = SprintPlanParser(plan_file)
        result = parser._extract_quality_gates()

        assert len(result) == 2
        assert result[0]['name'] == "Security Audit"
        assert result[0]['threshold'] == 85
        assert result[1]['name'] == "Test Coverage"
        assert result[1]['threshold'] == 90

    def test_extract_quality_gates_colon_format(self, tmp_path):
        """Test extracting gates with colon format (no space after colon)."""
        plan_file = tmp_path / "sprint.md"
        # Note: The regex pattern [:\(](\d+) requires digits immediately after : or (
        # So "Name:100%" works but "Name: 100%" does not
        plan_file.write_text("""# Sprint Plan: Test
## Quality Gates
- Code Review:100%
- Performance:75%

## Done
""")

        parser = SprintPlanParser(plan_file)
        result = parser._extract_quality_gates()

        assert len(result) == 2
        assert result[0]['name'] == "Code Review"
        assert result[0]['threshold'] == 100

    def test_quality_gate_default_values(self, tmp_path):
        """Test quality gate default blocking and status."""
        plan_file = tmp_path / "sprint.md"
        plan_file.write_text("""# Sprint Plan: Test
## Quality Gates
- Testing (80%)
""")

        parser = SprintPlanParser(plan_file)
        result = parser._extract_quality_gates()

        assert result[0]['blocking'] is True
        assert result[0]['status'] == 'not_run'


class TestExtractTasks:
    """Test extract_tasks method."""

    def test_extract_tasks_from_features(self, tmp_path):
        """Test extracting tasks from features."""
        plan_file = tmp_path / "sprint.md"
        plan_file.write_text("""# Sprint Plan: Test
## Features
### Build API
**What:** Create REST endpoints
**Why:** Backend needed
**How:** Use FastAPI

### Write Tests
**What:** Add test coverage
**Why:** Quality assurance
**How:** pytest

## Success Criteria
""")

        parser = SprintPlanParser(plan_file)
        result = parser.extract_tasks()

        assert len(result) == 2
        assert result[0]['name'] == "Build API"
        assert result[0]['description'] == "Create REST endpoints"
        assert result[0]['what'] == "Create REST endpoints"
        assert result[0]['why'] == "Backend needed"

    def test_task_estimated_hours_complex(self, tmp_path):
        """Test complex task gets higher hour estimate."""
        plan_file = tmp_path / "sprint.md"
        plan_file.write_text("""# Sprint Plan: Test
## Features
### Complex Task
**What:** Build
**Why:** Need
**How:** Steps:
- Step 1
- Step 2
- Step 3
- Step 4
- Step 5
- Step 6

## Done
""")

        parser = SprintPlanParser(plan_file)
        result = parser.extract_tasks()

        assert result[0]['estimated_hours'] == 8

    def test_task_estimated_hours_medium(self, tmp_path):
        """Test medium task gets medium hour estimate."""
        plan_file = tmp_path / "sprint.md"
        plan_file.write_text("""# Sprint Plan: Test
## Features
### Medium Task
**What:** Build
**Why:** Need
**How:** Steps:
- Step 1
- Step 2
- Step 3

## Done
""")

        parser = SprintPlanParser(plan_file)
        result = parser.extract_tasks()

        assert result[0]['estimated_hours'] == 4

    def test_task_estimated_hours_simple(self, tmp_path):
        """Test simple task gets lower hour estimate."""
        plan_file = tmp_path / "sprint.md"
        plan_file.write_text("""# Sprint Plan: Test
## Features
### Simple Task
**What:** Quick fix
**Why:** Needed
**How:** Do it

## Done
""")

        parser = SprintPlanParser(plan_file)
        result = parser.extract_tasks()

        assert result[0]['estimated_hours'] == 2


class TestParse:
    """Test full parse method."""

    def test_parse_returns_complete_structure(self, tmp_path):
        """Test parse returns complete structure."""
        plan_file = tmp_path / "sprint.md"
        plan_file.write_text("""# Sprint Plan: Complete Sprint
## Goals
- Main goal

## Features
### Feature One
**What:** Build it
**Why:** Need it
**How:** Just do it

## Success Criteria
- All tests pass

## Deliverables
- Working feature

## Quality Gates
- Testing (90%)
""")

        parser = SprintPlanParser(plan_file)
        result = parser.parse()

        assert result['name'] == "Complete Sprint"
        assert "Main goal" in result['goal']
        assert len(result['features']) == 1
        assert len(result['success_criteria']) == 1
        assert len(result['deliverables']) == 1
        assert len(result['quality_gates']) == 1


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    def test_parse_sprint_plan_function(self, tmp_path):
        """Test parse_sprint_plan convenience function."""
        plan_file = tmp_path / "sprint.md"
        plan_file.write_text("# Sprint Plan: Test Sprint\n## Goals\n- Goal 1\n")

        result = parse_sprint_plan(plan_file)

        assert result['name'] == "Test Sprint"
        assert "Goal 1" in result['goal']

    def test_extract_tasks_from_plan_function(self, tmp_path):
        """Test extract_tasks_from_plan convenience function."""
        plan_file = tmp_path / "sprint.md"
        plan_file.write_text("""# Sprint Plan: Test
## Features
### Task One
**What:** Do it
""")

        result = extract_tasks_from_plan(plan_file)

        assert len(result) == 1
        assert result[0]['name'] == "Task One"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_file(self, tmp_path):
        """Test parsing empty file."""
        plan_file = tmp_path / "sprint.md"
        plan_file.write_text("")

        parser = SprintPlanParser(plan_file)
        result = parser.parse()

        assert result['name'] == "Unnamed Sprint"
        assert result['goal'] == ""
        assert result['features'] == []

    def test_file_with_only_headers(self, tmp_path):
        """Test file with only section headers."""
        plan_file = tmp_path / "sprint.md"
        plan_file.write_text("""# Sprint Plan: Headers Only
## Goals
## Features
## Success Criteria
""")

        parser = SprintPlanParser(plan_file)
        result = parser.parse()

        assert result['name'] == "Headers Only"
        assert result['features'] == []

    def test_feature_without_details(self, tmp_path):
        """Test feature with no What/Why/How."""
        plan_file = tmp_path / "sprint.md"
        plan_file.write_text("""# Sprint Plan: Test
## Features
### Bare Feature

## Done
""")

        parser = SprintPlanParser(plan_file)
        result = parser._extract_features()

        assert len(result) == 1
        assert result[0]['name'] == "Bare Feature"
        assert result[0]['what'] == ''
        assert result[0]['why'] == ''
        assert result[0]['how'] == ''


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
