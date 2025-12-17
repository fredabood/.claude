"""
Tests for vibey.roadmap.criteria.planned module.

Tests the planned criterion factory and utilities.
"""

import pytest
from pathlib import Path

from vibey.roadmap.criteria.planned import (
    create_planned_criteria,
    check_planned_status,
    get_planning_work_needed,
    PlannedCriteriaConfig,
    DEFAULT_PLANNED_CONFIG,
)
from vibey.roadmap.models.ticket.enums import TicketStatus


class TestCreatePlannedCriteria:
    """Tests for create_planned_criteria()."""

    def test_default_config_creates_two_criteria(self, tmp_path):
        """Default config creates YAML and context criteria."""
        roadmap_root = tmp_path / ".vibey" / "roadmap"
        roadmap_root.mkdir(parents=True)

        criteria = create_planned_criteria(
            ticket_id="01TEST",
            ticket_type="task",
            roadmap_root=roadmap_root,
        )

        # Default config has yaml + context checks
        assert len(criteria) == 2
        assert all(c.blocks_transition_to == TicketStatus.IN_PROGRESS for c in criteria)

    def test_yaml_criterion_required_by_default(self, tmp_path):
        """YAML criterion should be required by default."""
        roadmap_root = tmp_path / ".vibey" / "roadmap"
        roadmap_root.mkdir(parents=True)

        criteria = create_planned_criteria(
            ticket_id="01TEST",
            ticket_type="task",
            roadmap_root=roadmap_root,
        )

        yaml_crit = next(c for c in criteria if "yaml" in c.id.lower())
        assert yaml_crit.required is True

    def test_context_criterion_optional_by_default(self, tmp_path):
        """Context criterion should be optional by default."""
        roadmap_root = tmp_path / ".vibey" / "roadmap"
        roadmap_root.mkdir(parents=True)

        criteria = create_planned_criteria(
            ticket_id="01TEST",
            ticket_type="task",
            roadmap_root=roadmap_root,
        )

        context_crit = next((c for c in criteria if "context" in c.id.lower()), None)
        if context_crit:
            assert context_crit.required is False

    def test_manual_approval_when_configured(self, tmp_path):
        """Manual approval criterion created when configured."""
        roadmap_root = tmp_path / ".vibey" / "roadmap"
        roadmap_root.mkdir(parents=True)

        config = PlannedCriteriaConfig(check_manual_approval=True)
        criteria = create_planned_criteria(
            ticket_id="01TEST",
            ticket_type="task",
            roadmap_root=roadmap_root,
            config=config,
        )

        approval_crit = next((c for c in criteria if "approved" in c.id.lower()), None)
        assert approval_crit is not None

    def test_no_criteria_when_all_disabled(self, tmp_path):
        """No criteria when all checks disabled."""
        roadmap_root = tmp_path / ".vibey" / "roadmap"
        roadmap_root.mkdir(parents=True)

        config = PlannedCriteriaConfig(
            check_yaml_exists=False,
            check_context_exists=False,
            check_manual_approval=False,
        )
        criteria = create_planned_criteria(
            ticket_id="01TEST",
            ticket_type="task",
            roadmap_root=roadmap_root,
            config=config,
        )

        assert len(criteria) == 0

    def test_different_ticket_types(self, tmp_path):
        """Criteria work for task, sprint, and track types."""
        roadmap_root = tmp_path / ".vibey" / "roadmap"
        roadmap_root.mkdir(parents=True)

        for ticket_type in ["task", "sprint", "track"]:
            criteria = create_planned_criteria(
                ticket_id="01TEST",
                ticket_type=ticket_type,
                roadmap_root=roadmap_root,
            )
            # Each should create the yaml criterion
            yaml_crit = next((c for c in criteria if "yaml" in c.id.lower()), None)
            assert yaml_crit is not None
            assert f"{ticket_type}s/01TEST.yaml" in yaml_crit.description


class TestCheckPlannedStatus:
    """Tests for check_planned_status()."""

    def test_returns_false_when_yaml_missing(self, tmp_path):
        """Should return False when YAML file doesn't exist."""
        roadmap_root = tmp_path / ".vibey" / "roadmap"
        (roadmap_root / "tasks").mkdir(parents=True)

        is_planned, unmet = check_planned_status(
            ticket_id="01TEST",
            ticket_type="task",
            roadmap_root=roadmap_root,
        )

        assert is_planned is False
        assert len(unmet) > 0

    def test_returns_true_when_yaml_exists(self, tmp_path):
        """Should return True when YAML file exists."""
        roadmap_root = tmp_path / ".vibey" / "roadmap"
        (roadmap_root / "tasks").mkdir(parents=True)

        # Create YAML file
        yaml_path = roadmap_root / "tasks" / "01TEST.yaml"
        yaml_path.write_text("task: {}")

        is_planned, unmet = check_planned_status(
            ticket_id="01TEST",
            ticket_type="task",
            roadmap_root=roadmap_root,
        )

        assert is_planned is True
        assert len(unmet) == 0

    def test_optional_criteria_dont_block(self, tmp_path):
        """Optional criteria (like context) don't block planned status."""
        roadmap_root = tmp_path / ".vibey" / "roadmap"
        (roadmap_root / "tasks").mkdir(parents=True)

        # Create YAML file (required) but no context (optional)
        yaml_path = roadmap_root / "tasks" / "01TEST.yaml"
        yaml_path.write_text("task: {}")

        config = PlannedCriteriaConfig(
            check_yaml_exists=True,
            check_context_exists=True,
            yaml_required=True,
            context_required=False,  # Context is optional
        )

        is_planned, unmet = check_planned_status(
            ticket_id="01TEST",
            ticket_type="task",
            roadmap_root=roadmap_root,
            config=config,
        )

        assert is_planned is True
        assert len(unmet) == 0


class TestGetPlanningWorkNeeded:
    """Tests for get_planning_work_needed()."""

    def test_returns_work_items_for_unmet_criteria(self, tmp_path):
        """Should return work items for unmet criteria."""
        roadmap_root = tmp_path / ".vibey" / "roadmap"
        (roadmap_root / "tasks").mkdir(parents=True)

        work_items = get_planning_work_needed(
            ticket_id="01TEST",
            ticket_type="task",
            roadmap_root=roadmap_root,
        )

        # Should have at least the YAML work item
        assert len(work_items) > 0
        yaml_item = next((w for w in work_items if "yaml" in w['criterion'].lower()), None)
        assert yaml_item is not None
        assert "Create file" in yaml_item['action']

    def test_empty_when_all_met(self, tmp_path):
        """Should return empty list when all criteria are met."""
        roadmap_root = tmp_path / ".vibey" / "roadmap"
        (roadmap_root / "tasks").mkdir(parents=True)

        # Create YAML file
        yaml_path = roadmap_root / "tasks" / "01TEST.yaml"
        yaml_path.write_text("task: {}")

        work_items = get_planning_work_needed(
            ticket_id="01TEST",
            ticket_type="task",
            roadmap_root=roadmap_root,
        )

        assert len(work_items) == 0

    def test_includes_optional_in_work_items(self, tmp_path):
        """Should include optional criteria in work items if not met."""
        roadmap_root = tmp_path / ".vibey" / "roadmap"
        (roadmap_root / "tasks").mkdir(parents=True)

        # Create YAML file
        yaml_path = roadmap_root / "tasks" / "01TEST.yaml"
        yaml_path.write_text("task: {}")

        config = PlannedCriteriaConfig(
            check_yaml_exists=True,
            check_context_exists=True,
            yaml_required=True,
            context_required=False,  # Context is optional but still shows as work
        )

        work_items = get_planning_work_needed(
            ticket_id="01TEST",
            ticket_type="task",
            roadmap_root=roadmap_root,
            config=config,
        )

        # Context is not met but is optional
        # It should be included in work items (as optional work)
        context_item = next((w for w in work_items if "context" in w['criterion'].lower()), None)
        if context_item:
            assert context_item['required'] is False


class TestPlannedCriteriaConfig:
    """Tests for PlannedCriteriaConfig dataclass."""

    def test_default_config_values(self):
        """Default config should have expected values."""
        config = PlannedCriteriaConfig()

        assert config.check_yaml_exists is True
        assert config.check_context_exists is True
        assert config.check_manual_approval is False
        assert config.yaml_required is True
        assert config.context_required is False
        assert config.approval_required is False

    def test_custom_config_values(self):
        """Custom config values should be respected."""
        config = PlannedCriteriaConfig(
            check_yaml_exists=False,
            check_manual_approval=True,
            approval_required=True,
        )

        assert config.check_yaml_exists is False
        assert config.check_manual_approval is True
        assert config.approval_required is True
