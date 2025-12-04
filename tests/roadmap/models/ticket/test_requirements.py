"""
Tests for requirement system (CriterionTemplate, ApplicabilityRules, Requirement, Resolver).
"""

import pytest

from vibey.roadmap.models.ticket.requirements import (
    CriterionTemplate,
    ApplicabilityRules,
    Requirement,
    RequirementResolver,
    RequirementInstantiator,
)
from vibey.roadmap.models.ticket.enums import (
    CriterionTargetType,
    EnforcementMode,
    InheritMode,
    TaskType,
    ThresholdComparison,
    TicketStatus,
    TicketType,
)


class TestCriterionTemplate:
    """Tests for CriterionTemplate class."""

    def test_basic_creation(self):
        """Test basic template creation."""
        template = CriterionTemplate(
            target_type=CriterionTargetType.THRESHOLD,
            target_config={"metric_name": "coverage", "threshold": 85.0},
            description_template="Test coverage >= {threshold}%",
        )
        assert template.target_type == CriterionTargetType.THRESHOLD
        assert template.target_config["threshold"] == 85.0
        assert template.blocks_transition_to == TicketStatus.COMPLETED

    def test_custom_blocks_transition(self):
        """Test template with custom blocks_transition_to."""
        template = CriterionTemplate(
            target_type=CriterionTargetType.MANUAL,
            target_config={"assessor": "tech-lead"},
            description_template="Code review by tech lead",
            blocks_transition_to=TicketStatus.PRODUCTION_READY,
        )
        assert template.blocks_transition_to == TicketStatus.PRODUCTION_READY

    def test_render_description(self):
        """Test description template rendering."""
        template = CriterionTemplate(
            target_type=CriterionTargetType.THRESHOLD,
            target_config={"metric_name": "coverage", "threshold": 85.0},
            description_template="Test coverage for {ticket_name} >= {threshold}%",
        )
        desc = template.render_description("task-001", "Implement API")
        assert desc == "Test coverage for Implement API >= 85.0%"

    def test_render_description_with_missing_placeholder(self):
        """Test description rendering with missing placeholder."""
        template = CriterionTemplate(
            target_type=CriterionTargetType.THRESHOLD,
            target_config={"threshold": 85.0},
            description_template="Coverage >= {unknown}%",
        )
        # Should return template as-is when placeholder is missing
        desc = template.render_description("task-001", "Test")
        assert desc == "Coverage >= {unknown}%"


class TestApplicabilityRules:
    """Tests for ApplicabilityRules class."""

    def test_empty_rules_match_everything(self):
        """Test that empty rules match all tickets."""
        rules = ApplicabilityRules()
        assert rules.matches()
        assert rules.matches(ticket_type=TicketType.TASK)
        assert rules.matches(task_type=TaskType.DEVELOPMENT)

    def test_ticket_type_inclusion(self):
        """Test ticket type inclusion rules."""
        rules = ApplicabilityRules(ticket_types=[TicketType.TASK])
        assert rules.matches(ticket_type=TicketType.TASK)
        assert not rules.matches(ticket_type=TicketType.SPRINT)
        assert not rules.matches()  # None doesn't match

    def test_ticket_type_exclusion(self):
        """Test ticket type exclusion rules."""
        rules = ApplicabilityRules(exclude_ticket_types=[TicketType.TASK])
        assert not rules.matches(ticket_type=TicketType.TASK)
        assert rules.matches(ticket_type=TicketType.SPRINT)
        assert rules.matches()  # None is not excluded

    def test_task_type_inclusion(self):
        """Test task type inclusion rules."""
        rules = ApplicabilityRules(task_types=[TaskType.DEVELOPMENT, TaskType.TESTING])
        assert rules.matches(task_type=TaskType.DEVELOPMENT)
        assert rules.matches(task_type=TaskType.TESTING)
        assert not rules.matches(task_type=TaskType.DOCUMENTATION)
        assert not rules.matches()

    def test_task_type_exclusion(self):
        """Test task type exclusion rules."""
        rules = ApplicabilityRules(exclude_task_types=[TaskType.DOCUMENTATION])
        assert rules.matches(task_type=TaskType.DEVELOPMENT)
        assert not rules.matches(task_type=TaskType.DOCUMENTATION)

    def test_has_criterion_types(self):
        """Test criterion type requirement."""
        rules = ApplicabilityRules(
            has_criterion_types=[CriterionTargetType.TEST_PASSES]
        )
        assert rules.matches(criterion_types=[CriterionTargetType.TEST_PASSES])
        assert rules.matches(
            criterion_types=[CriterionTargetType.FILE_EXISTS, CriterionTargetType.TEST_PASSES]
        )
        assert not rules.matches(criterion_types=[CriterionTargetType.FILE_EXISTS])
        assert not rules.matches(criterion_types=[])
        assert not rules.matches()

    def test_has_file_patterns(self):
        """Test file pattern matching."""
        rules = ApplicabilityRules(has_file_patterns=["*.py", "*.ts"])
        assert rules.matches(file_paths=["src/main.py"])
        assert rules.matches(file_paths=["src/app.ts"])
        assert not rules.matches(file_paths=["README.md"])
        assert not rules.matches(file_paths=[])
        assert not rules.matches()

    def test_combined_rules(self):
        """Test multiple rules combined (AND logic)."""
        rules = ApplicabilityRules(
            ticket_types=[TicketType.TASK],
            task_types=[TaskType.DEVELOPMENT],
        )
        # Both must match
        assert rules.matches(ticket_type=TicketType.TASK, task_type=TaskType.DEVELOPMENT)
        # One missing
        assert not rules.matches(ticket_type=TicketType.TASK, task_type=TaskType.DOCUMENTATION)
        assert not rules.matches(ticket_type=TicketType.SPRINT, task_type=TaskType.DEVELOPMENT)


class TestRequirement:
    """Tests for Requirement class."""

    def test_basic_creation(self):
        """Test basic requirement creation."""
        template = CriterionTemplate(
            target_type=CriterionTargetType.THRESHOLD,
            target_config={"metric_name": "coverage", "threshold": 85.0},
            description_template="Coverage >= 85%",
        )
        req = Requirement(
            id="test-coverage",
            name="Test Coverage",
            description="Code must have test coverage",
            criterion_template=template,
        )
        assert req.id == "test-coverage"
        assert req.inherit_mode == InheritMode.INHERIT
        assert req.enforcement == EnforcementMode.BLOCKING
        assert not req.enforceable

    def test_skip_requires_justification(self):
        """Test that SKIP mode requires justification."""
        template = CriterionTemplate(
            target_type=CriterionTargetType.MANUAL,
            target_config={},
            description_template="Manual review",
        )
        with pytest.raises(ValueError, match="requires skip_justification"):
            Requirement(
                id="manual-review",
                name="Manual Review",
                description="Requires review",
                criterion_template=template,
                inherit_mode=InheritMode.SKIP,
            )

    def test_skip_with_justification(self):
        """Test SKIP mode with justification."""
        template = CriterionTemplate(
            target_type=CriterionTargetType.MANUAL,
            target_config={},
            description_template="Manual review",
        )
        req = Requirement(
            id="manual-review",
            name="Manual Review",
            description="Requires review",
            criterion_template=template,
            inherit_mode=InheritMode.SKIP,
            skip_justification="Not applicable for documentation tasks",
        )
        assert req.inherit_mode == InheritMode.SKIP
        assert req.skip_justification is not None

    def test_is_applicable(self):
        """Test is_applicable method."""
        template = CriterionTemplate(
            target_type=CriterionTargetType.THRESHOLD,
            target_config={"threshold": 85.0},
            description_template="Test",
        )
        req = Requirement(
            id="test",
            name="Test",
            description="Test",
            criterion_template=template,
            applicability=ApplicabilityRules(ticket_types=[TicketType.TASK]),
        )
        assert req.is_applicable(ticket_type=TicketType.TASK)
        assert not req.is_applicable(ticket_type=TicketType.SPRINT)

    def test_compare_strictness_threshold_gte(self):
        """Test strictness comparison for GTE thresholds."""
        template_85 = CriterionTemplate(
            target_type=CriterionTargetType.THRESHOLD,
            target_config={"threshold": 85.0, "comparison": "gte"},
            description_template="Coverage >= 85%",
        )
        template_95 = CriterionTemplate(
            target_type=CriterionTargetType.THRESHOLD,
            target_config={"threshold": 95.0, "comparison": "gte"},
            description_template="Coverage >= 95%",
        )

        req_85 = Requirement(
            id="coverage", name="Coverage", description="Test",
            criterion_template=template_85,
        )
        req_95 = Requirement(
            id="coverage", name="Coverage", description="Test",
            criterion_template=template_95,
        )

        # 95% is stricter than 85% for GTE
        assert req_95.compare_strictness(req_85) == 1
        assert req_85.compare_strictness(req_95) == -1
        assert req_85.compare_strictness(req_85) == 0

    def test_compare_strictness_threshold_lte(self):
        """Test strictness comparison for LTE thresholds."""
        template_5 = CriterionTemplate(
            target_type=CriterionTargetType.THRESHOLD,
            target_config={"threshold": 5.0, "comparison": "lte"},
            description_template="Errors <= 5",
        )
        template_10 = CriterionTemplate(
            target_type=CriterionTargetType.THRESHOLD,
            target_config={"threshold": 10.0, "comparison": "lte"},
            description_template="Errors <= 10",
        )

        req_5 = Requirement(
            id="errors", name="Errors", description="Test",
            criterion_template=template_5,
        )
        req_10 = Requirement(
            id="errors", name="Errors", description="Test",
            criterion_template=template_10,
        )

        # 5 is stricter than 10 for LTE
        assert req_5.compare_strictness(req_10) == 1
        assert req_10.compare_strictness(req_5) == -1

    def test_compare_strictness_enforcement(self):
        """Test strictness comparison for non-threshold requirements."""
        template = CriterionTemplate(
            target_type=CriterionTargetType.MANUAL,
            target_config={},
            description_template="Manual review",
        )

        req_audit = Requirement(
            id="review", name="Review", description="Test",
            criterion_template=template,
            enforcement=EnforcementMode.AUDIT,
        )
        req_blocking = Requirement(
            id="review", name="Review", description="Test",
            criterion_template=template,
            enforcement=EnforcementMode.BLOCKING,
        )

        # BLOCKING is stricter than AUDIT
        assert req_blocking.compare_strictness(req_audit) == 1
        assert req_audit.compare_strictness(req_blocking) == -1

    def test_get_stricter(self):
        """Test get_stricter method."""
        template_85 = CriterionTemplate(
            target_type=CriterionTargetType.THRESHOLD,
            target_config={"threshold": 85.0},
            description_template="Coverage >= 85%",
        )
        template_95 = CriterionTemplate(
            target_type=CriterionTargetType.THRESHOLD,
            target_config={"threshold": 95.0},
            description_template="Coverage >= 95%",
        )

        req_85 = Requirement(
            id="coverage", name="Coverage", description="Test",
            criterion_template=template_85,
        )
        req_95 = Requirement(
            id="coverage", name="Coverage", description="Test",
            criterion_template=template_95,
        )

        stricter = req_85.get_stricter(req_95)
        assert stricter.criterion_template.target_config["threshold"] == 95.0


class TestRequirementResolver:
    """Tests for RequirementResolver class."""

    def _make_requirement(
        self,
        req_id: str,
        threshold: float = 85.0,
        inherit_mode: InheritMode = InheritMode.INHERIT,
        enforceable: bool = False,
        enforcement: EnforcementMode = EnforcementMode.BLOCKING,
        skip_justification: str = None,
    ) -> Requirement:
        """Helper to create test requirements."""
        template = CriterionTemplate(
            target_type=CriterionTargetType.THRESHOLD,
            target_config={"metric_name": "coverage", "threshold": threshold},
            description_template=f"Coverage >= {threshold}%",
        )
        return Requirement(
            id=req_id,
            name=f"Requirement {req_id}",
            description=f"Test requirement {req_id}",
            criterion_template=template,
            inherit_mode=inherit_mode,
            enforceable=enforceable,
            enforcement=enforcement,
            skip_justification=skip_justification,
        )

    def test_empty_requirements(self):
        """Test resolver with no requirements."""
        resolver = RequirementResolver()
        result = resolver.resolve([], [])
        assert result == []

    def test_local_only(self):
        """Test resolver with local requirements only."""
        resolver = RequirementResolver()
        local = [self._make_requirement("coverage")]
        result = resolver.resolve(local, [])
        assert len(result) == 1
        assert result[0].id == "coverage"

    def test_inherited_only(self):
        """Test resolver with inherited requirements only."""
        resolver = RequirementResolver()
        inherited = [self._make_requirement("coverage")]
        result = resolver.resolve([], inherited)
        assert len(result) == 1
        assert result[0].id == "coverage"

    def test_inherit_mode_uses_stricter(self):
        """Test INHERIT mode uses stricter requirement."""
        resolver = RequirementResolver()
        local = [self._make_requirement("coverage", threshold=95.0)]
        inherited = [self._make_requirement("coverage", threshold=85.0)]

        result = resolver.resolve(local, inherited)
        assert len(result) == 1
        assert result[0].criterion_template.target_config["threshold"] == 95.0

    def test_override_mode(self):
        """Test OVERRIDE mode replaces inherited."""
        resolver = RequirementResolver()
        local = [self._make_requirement(
            "coverage",
            threshold=70.0,
            inherit_mode=InheritMode.OVERRIDE
        )]
        inherited = [self._make_requirement("coverage", threshold=85.0)]

        result = resolver.resolve(local, inherited)
        assert len(result) == 1
        # Override uses local value even though it's less strict
        assert result[0].criterion_template.target_config["threshold"] == 70.0

    def test_skip_mode(self):
        """Test SKIP mode excludes requirement."""
        resolver = RequirementResolver()
        local = [self._make_requirement(
            "coverage",
            inherit_mode=InheritMode.SKIP,
            skip_justification="Not applicable",
        )]
        inherited = [self._make_requirement("coverage", threshold=85.0)]

        result = resolver.resolve(local, inherited)
        assert len(result) == 0  # Skipped

    def test_enforceable_cannot_be_overridden(self):
        """Test enforceable requirements cannot be overridden."""
        resolver = RequirementResolver()
        local = [self._make_requirement(
            "coverage",
            threshold=70.0,
            inherit_mode=InheritMode.OVERRIDE,
        )]
        inherited = [self._make_requirement(
            "coverage",
            threshold=85.0,
            enforceable=True,
        )]

        result = resolver.resolve(local, inherited)
        assert len(result) == 1
        # Enforceable requirement is used despite OVERRIDE
        assert result[0].criterion_template.target_config["threshold"] == 85.0

    def test_enforceable_cannot_be_skipped(self):
        """Test enforceable requirements cannot be skipped."""
        resolver = RequirementResolver()
        local = [self._make_requirement(
            "coverage",
            inherit_mode=InheritMode.SKIP,
            skip_justification="Trying to skip",
        )]
        inherited = [self._make_requirement(
            "coverage",
            threshold=85.0,
            enforceable=True,
        )]

        result = resolver.resolve(local, inherited)
        assert len(result) == 1
        # Enforceable requirement is present despite SKIP attempt
        assert result[0].enforceable

    def test_applicability_filtering(self):
        """Test that only applicable requirements are returned."""
        resolver = RequirementResolver()

        template = CriterionTemplate(
            target_type=CriterionTargetType.THRESHOLD,
            target_config={"threshold": 85.0},
            description_template="Coverage",
        )
        req = Requirement(
            id="coverage",
            name="Coverage",
            description="Test",
            criterion_template=template,
            applicability=ApplicabilityRules(ticket_types=[TicketType.TASK]),
        )

        # Task tickets match
        result = resolver.resolve([req], [], ticket_type=TicketType.TASK)
        assert len(result) == 1

        # Sprint tickets don't match
        result = resolver.resolve([req], [], ticket_type=TicketType.SPRINT)
        assert len(result) == 0

    def test_multiple_requirements(self):
        """Test resolver with multiple different requirements."""
        resolver = RequirementResolver()
        local = [
            self._make_requirement("coverage", threshold=90.0),
            self._make_requirement("lint-score", threshold=8.0),
        ]
        inherited = [
            self._make_requirement("coverage", threshold=85.0),
            self._make_requirement("security", threshold=100.0),
        ]

        result = resolver.resolve(local, inherited)
        assert len(result) == 3
        req_ids = {r.id for r in result}
        assert req_ids == {"coverage", "lint-score", "security"}

        # Coverage should use stricter (90%)
        coverage = next(r for r in result if r.id == "coverage")
        assert coverage.criterion_template.target_config["threshold"] == 90.0


class TestRequirementInstantiator:
    """Tests for RequirementInstantiator class."""

    def test_instantiate_single_requirement(self):
        """Test instantiating a single requirement."""
        template = CriterionTemplate(
            target_type=CriterionTargetType.THRESHOLD,
            target_config={
                "metric_name": "coverage",
                "threshold": 85.0,
                "comparison": ThresholdComparison.GTE,
            },
            description_template="Test coverage >= {threshold}%",
        )
        req = Requirement(
            id="test-coverage",
            name="Test Coverage",
            description="Code must have test coverage",
            criterion_template=template,
        )

        instantiator = RequirementInstantiator()
        criteria = instantiator.instantiate([req], "task-001", "My Task")

        assert len(criteria) == 1
        criterion = criteria[0]
        assert criterion.id == "test-coverage-task-001"
        assert "85.0" in criterion.description
        assert criterion.required  # BLOCKING enforcement
        assert criterion.blocks_transition_to == TicketStatus.COMPLETED

    def test_instantiate_non_blocking_requirement(self):
        """Test instantiating a non-blocking requirement."""
        template = CriterionTemplate(
            target_type=CriterionTargetType.MANUAL,
            target_config={"assessor": "reviewer"},
            description_template="Optional review",
        )
        req = Requirement(
            id="optional-review",
            name="Optional Review",
            description="Non-blocking review",
            criterion_template=template,
            enforcement=EnforcementMode.WARNING,
        )

        instantiator = RequirementInstantiator()
        criteria = instantiator.instantiate([req], "task-001", "My Task")

        assert len(criteria) == 1
        criterion = criteria[0]
        assert not criterion.required  # WARNING enforcement

    def test_instantiate_multiple_requirements(self):
        """Test instantiating multiple requirements."""
        template1 = CriterionTemplate(
            target_type=CriterionTargetType.THRESHOLD,
            target_config={"metric_name": "coverage", "threshold": 85.0},
            description_template="Coverage",
        )
        template2 = CriterionTemplate(
            target_type=CriterionTargetType.MANUAL,
            target_config={"assessor": "tech-lead"},
            description_template="Review",
        )

        reqs = [
            Requirement(id="coverage", name="Coverage", description="Test",
                       criterion_template=template1),
            Requirement(id="review", name="Review", description="Test",
                       criterion_template=template2),
        ]

        instantiator = RequirementInstantiator()
        criteria = instantiator.instantiate(reqs, "task-001", "My Task")

        assert len(criteria) == 2
        criterion_ids = {c.id for c in criteria}
        assert criterion_ids == {"coverage-task-001", "review-task-001"}

    def test_instantiate_different_target_types(self):
        """Test instantiating requirements with different target types."""
        # File exists target
        template_file = CriterionTemplate(
            target_type=CriterionTargetType.FILE_EXISTS,
            target_config={"paths": ["README.md"]},
            description_template="README must exist",
        )
        req_file = Requirement(
            id="readme",
            name="README",
            description="Test",
            criterion_template=template_file,
        )

        # Test passes target
        template_test = CriterionTemplate(
            target_type=CriterionTargetType.TEST_PASSES,
            target_config={"test_command": "pytest"},
            description_template="Tests must pass",
        )
        req_test = Requirement(
            id="tests",
            name="Tests",
            description="Test",
            criterion_template=template_test,
        )

        instantiator = RequirementInstantiator()
        criteria = instantiator.instantiate([req_file, req_test], "task-001", "My Task")

        assert len(criteria) == 2
        # Verify target types
        target_types = {c.target.type for c in criteria}
        assert CriterionTargetType.FILE_EXISTS in target_types
        assert CriterionTargetType.TEST_PASSES in target_types


class TestIntegration:
    """Integration tests for the requirement system."""

    def test_full_workflow(self):
        """Test complete requirement resolution and instantiation workflow."""
        # Define roadmap-level requirement (enforceable)
        roadmap_template = CriterionTemplate(
            target_type=CriterionTargetType.THRESHOLD,
            target_config={
                "metric_name": "coverage",
                "threshold": 80.0,
                "comparison": ThresholdComparison.GTE,
            },
            description_template="Minimum coverage {threshold}%",
        )
        roadmap_req = Requirement(
            id="coverage",
            name="Minimum Coverage",
            description="All code must have minimum test coverage",
            criterion_template=roadmap_template,
            enforceable=True,
        )

        # Task tries to override (should fail because enforceable)
        task_template = CriterionTemplate(
            target_type=CriterionTargetType.THRESHOLD,
            target_config={
                "metric_name": "coverage",
                "threshold": 60.0,  # Trying to be less strict
                "comparison": ThresholdComparison.GTE,
            },
            description_template="Coverage {threshold}%",
        )
        task_req = Requirement(
            id="coverage",
            name="Local Coverage",
            description="Local override attempt",
            criterion_template=task_template,
            inherit_mode=InheritMode.OVERRIDE,
        )

        # Resolve
        resolver = RequirementResolver()
        effective = resolver.resolve([task_req], [roadmap_req])

        assert len(effective) == 1
        # Should use roadmap's 80% because it's enforceable
        assert effective[0].criterion_template.target_config["threshold"] == 80.0

        # Instantiate
        instantiator = RequirementInstantiator()
        criteria = instantiator.instantiate(effective, "task-001", "Feature Task")

        assert len(criteria) == 1
        criterion = criteria[0]
        assert criterion.target.threshold == 80.0

    def test_inheritance_chain(self):
        """Test requirement inheritance from roadmap -> track -> sprint -> task."""
        # Roadmap: 70%
        roadmap_req = self._make_requirement("coverage", 70.0)
        # Track: 80% (stricter)
        track_req = self._make_requirement("coverage", 80.0)
        # Sprint: 75% (less strict, but INHERIT mode)
        sprint_req = self._make_requirement("coverage", 75.0)
        # Task: 90% (strictest)
        task_req = self._make_requirement("coverage", 90.0)

        resolver = RequirementResolver()

        # Simulate inheritance chain
        # Roadmap -> Track: 80% wins
        effective_track = resolver.resolve([track_req], [roadmap_req])
        assert effective_track[0].criterion_template.target_config["threshold"] == 80.0

        # Track -> Sprint: 80% wins (inherited is stricter)
        effective_sprint = resolver.resolve([sprint_req], effective_track)
        assert effective_sprint[0].criterion_template.target_config["threshold"] == 80.0

        # Sprint -> Task: 90% wins (local is stricter)
        effective_task = resolver.resolve([task_req], effective_sprint)
        assert effective_task[0].criterion_template.target_config["threshold"] == 90.0

    def _make_requirement(self, req_id: str, threshold: float) -> Requirement:
        """Helper to create test requirements."""
        template = CriterionTemplate(
            target_type=CriterionTargetType.THRESHOLD,
            target_config={"metric_name": "coverage", "threshold": threshold},
            description_template=f"Coverage >= {threshold}%",
        )
        return Requirement(
            id=req_id,
            name=f"Requirement {req_id}",
            description=f"Test requirement",
            criterion_template=template,
        )
