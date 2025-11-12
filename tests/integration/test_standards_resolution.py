"""
Integration tests for standards resolution engine.

Tests hierarchical inheritance, deduplication, and override handling.
"""

import pytest
from pathlib import Path
from datetime import datetime, timezone
from vibey.roadmap.standards import StandardsResolver, ResolvedStandard
from vibey.roadmap.models import (
    Standard, StandardType, EnforcementMode,
    Roadmap, Track, Sprint,
    VersionStrategy, Progress, TrackSummary, Metadata,
    TrackProgress, SprintSummary, TrackMetadata,
    SprintProgress, TaskSummary, SprintMetadata,
    Status, Priority, TaskType, VersionBumpTrigger,
)
from vibey.roadmap.serialization import save_roadmap, save_track, save_sprint


@pytest.fixture
def test_roadmap_with_standards(tmp_path):
    """
    Create a test roadmap with standards at all levels.

    Hierarchy:
    - Roadmap: commit-required (blocking), test-coverage (blocking)
    - Track (backend): doc-review (warning), test-coverage (blocking, stricter)
    - Sprint (backend-1): security-review (blocking)
    """
    vibey_dir = tmp_path / ".vibey"
    vibey_dir.mkdir(parents=True)

    roadmap_dir = vibey_dir / "roadmap"
    roadmap_dir.mkdir(parents=True)

    # Create roadmap with 2 standards
    roadmap_standards = [
        Standard(
            id="commit-required",
            name="Commit Required",
            description="All tasks must have commits",
            type=StandardType.COMMIT_CHECK,
            enforcement=EnforcementMode.BLOCKING,
            validation={"min_commits": 1},
            created=datetime.now(timezone.utc),
        ),
        Standard(
            id="test-coverage",
            name="Test Coverage",
            description="80% test coverage required",
            type=StandardType.TEST_RUN,
            enforcement=EnforcementMode.BLOCKING,
            validation={"command": "pytest --cov", "threshold": 80},
            created=datetime.now(timezone.utc),
        ),
    ]

    roadmap = Roadmap(
        id="test-roadmap",
        name="Test Roadmap",
        version="1.0.0",
        version_strategy=VersionStrategy(
            major_on=VersionBumpTrigger.ROADMAP_MILESTONE,
            minor_on=VersionBumpTrigger.TRACK_COMPLETION,
            patch_on=VersionBumpTrigger.SPRINT_PRODUCTION_READY,
        ),
        status=Status.IN_PROGRESS,
        blocked=False,
        created=datetime.now(timezone.utc),
        started=datetime.now(timezone.utc),
        progress=Progress(
            tracks_total=1,
            tracks_completed=0,
            sprints_total=1,
            sprints_completed=0,
            tasks_total=0,
            tasks_completed=0,
            completion_percent=0,
        ),
        tracks=[
            TrackSummary(
                id="backend",
                name="Backend Track",
                status=Status.IN_PROGRESS,
                priority=Priority.HIGH,
            )
        ],
        activity_log=[],
        metadata=Metadata(
            created_by="test",
            framework_version="1.3.0",
            schema_version="2.1",
            last_updated=datetime.now(timezone.utc),
        ),
        standards=roadmap_standards,
    )

    # Save roadmap to .vibey/roadmap.yaml (not .vibey/roadmap/roadmap.yaml)
    save_roadmap(roadmap, vibey_dir / "roadmap.yaml")

    # Create track with 2 standards (one override, one new)
    track_standards = [
        Standard(
            id="doc-review",
            name="Documentation Review",
            description="All tasks should update docs",
            type=StandardType.FILE_CHECK,
            enforcement=EnforcementMode.WARNING,
            validation={"pattern": "**/*.md", "min_files": 1},
            created=datetime.now(timezone.utc),
        ),
        Standard(
            id="test-coverage",
            name="Test Coverage (Strict)",
            description="90% test coverage required (stricter than roadmap)",
            type=StandardType.TEST_RUN,
            enforcement=EnforcementMode.BLOCKING,
            validation={"command": "pytest --cov", "threshold": 90},  # Stricter
            created=datetime.now(timezone.utc),
        ),
    ]

    track = Track(
        id="backend",
        name="Backend Track",
        roadmap_id="test-roadmap",
        status=Status.IN_PROGRESS,
        blocked=False,
        priority=Priority.HIGH,
        created=datetime.now(timezone.utc),
        started=datetime.now(timezone.utc),
        progress=TrackProgress(
            sprints_total=1,
            sprints_completed=0,
            tasks_total=0,
            tasks_completed=0,
            completion_percent=0,
        ),
        sprints=[
            SprintSummary(
                id="backend-1",
                name="Sprint 1",
                status=Status.IN_PROGRESS,
            )
        ],
        dependencies=[],
        blocks=[],
        blocked_by=[],
        depends_on=[],
        depended_on_by=[],
        quality_gates=[],
        assigned_agents=[],
        metadata=TrackMetadata(
            created_by="test",
            last_updated=datetime.now(timezone.utc),
        ),
        standards=track_standards,
    )

    track_dir = roadmap_dir / "backend"
    track_dir.mkdir()
    save_track(track, track_dir / "track.yaml")

    # Create sprint with 1 standard
    sprint_standards = [
        Standard(
            id="security-review",
            name="Security Review",
            description="Security review required",
            type=StandardType.CUSTOM_SCRIPT,
            enforcement=EnforcementMode.BLOCKING,
            validation={"script": "scripts/security-audit.sh"},
            created=datetime.now(timezone.utc),
        ),
    ]

    sprint = Sprint(
        id="backend-1",
        name="Sprint 1",
        track_id="backend",
        roadmap_id="test-roadmap",
        status=Status.IN_PROGRESS,
        blocked=False,
        created=datetime.now(timezone.utc),
        started=datetime.now(timezone.utc),
        progress=SprintProgress(
            development_tasks_total=0,
            development_tasks_completed=0,
            completion_gate_tasks_total=0,
            completion_gate_tasks_completed=0,
            production_gate_tasks_total=0,
            production_gate_tasks_completed=0,
            tasks_total=0,
            tasks_completed=0,
            completion_percent=0,
        ),
        tasks=[],
        development_gates=[],
        blocks=[],
        blocked_by=[],
        depends_on=[],
        depended_on_by=[],
        metadata=SprintMetadata(
            last_updated=datetime.now(timezone.utc),
        ),
        standards=sprint_standards,
    )

    sprint_dir = track_dir / "backend-1"
    sprint_dir.mkdir()
    save_sprint(sprint, sprint_dir / "sprint.yaml")

    return tmp_path


class TestHierarchicalInheritance:
    """Test standards inheritance through the hierarchy."""

    def test_task_inherits_from_all_levels(self, test_roadmap_with_standards):
        """Task should inherit standards from roadmap, track, and sprint."""
        resolver = StandardsResolver(test_roadmap_with_standards)

        # Resolve for a task (format: sprint-id-task-nnn)
        resolved = resolver.resolve_for_task("backend-1-task-001")

        # Should have 4 standards:
        # - commit-required (roadmap)
        # - test-coverage (track - overrides roadmap)
        # - doc-review (track)
        # - security-review (sprint)
        standard_ids = [r.standard.id for r in resolved]
        assert len(standard_ids) == 4
        assert "commit-required" in standard_ids
        assert "test-coverage" in standard_ids
        assert "doc-review" in standard_ids
        assert "security-review" in standard_ids

    def test_sprint_inherits_from_roadmap_and_track(self, test_roadmap_with_standards):
        """Sprint should inherit standards from roadmap and track."""
        resolver = StandardsResolver(test_roadmap_with_standards)

        resolved = resolver.resolve_for_sprint("backend-1")

        # Should have 4 standards:
        # - commit-required (roadmap)
        # - test-coverage (track - overrides roadmap)
        # - doc-review (track)
        # - security-review (sprint)
        standard_ids = [r.standard.id for r in resolved]
        assert len(standard_ids) == 4
        assert "commit-required" in standard_ids
        assert "test-coverage" in standard_ids
        assert "doc-review" in standard_ids
        assert "security-review" in standard_ids

    def test_track_inherits_from_roadmap(self, test_roadmap_with_standards):
        """Track should inherit standards from roadmap."""
        resolver = StandardsResolver(test_roadmap_with_standards)

        resolved = resolver.resolve_for_track("backend")

        # Should have 3 standards:
        # - commit-required (roadmap)
        # - test-coverage (track - overrides roadmap)
        # - doc-review (track)
        standard_ids = [r.standard.id for r in resolved]
        assert len(standard_ids) == 3
        assert "commit-required" in standard_ids
        assert "test-coverage" in standard_ids
        assert "doc-review" in standard_ids


class TestDeduplication:
    """Test that more specific standards override less specific ones."""

    def test_track_standard_overrides_roadmap(self, test_roadmap_with_standards):
        """When same standard ID at track and roadmap, track wins."""
        resolver = StandardsResolver(test_roadmap_with_standards)

        resolved = resolver.resolve_for_track("backend")

        # Find test-coverage standard
        test_cov = next(r for r in resolved if r.standard.id == "test-coverage")

        # Should be from track, not roadmap
        assert test_cov.source_level == "track"
        assert test_cov.source_id == "backend"

        # Threshold should be 90 (track) not 80 (roadmap)
        assert test_cov.standard.validation["threshold"] == 90

    def test_sprint_standard_would_override_track(self, test_roadmap_with_standards):
        """If sprint defined same standard, it would override track/roadmap."""
        resolver = StandardsResolver(test_roadmap_with_standards)

        # Test current state first
        resolved = resolver.resolve_for_sprint("backend-1")
        test_cov = next(r for r in resolved if r.standard.id == "test-coverage")

        # Currently comes from track
        assert test_cov.source_level == "track"
        assert test_cov.standard.validation["threshold"] == 90


class TestOverrideHandling:
    """Test standard override mechanism."""

    def test_override_marks_standard_as_overridden(self, test_roadmap_with_standards):
        """When a standard has an override for an item, it should be marked."""
        from vibey.roadmap.serialization import save_roadmap

        resolver = StandardsResolver(test_roadmap_with_standards)

        # First add an override to commit-required for a specific task
        roadmap = resolver._get_roadmap()
        commit_std = roadmap.get_standard("commit-required")
        commit_std.add_override(
            target_id="backend-1-task-001",
            reason="Emergency hotfix - no tests needed",
            overridden_by="admin",
        )

        # Save roadmap to persist the override
        vibey_dir = test_roadmap_with_standards / ".vibey"
        save_roadmap(roadmap, vibey_dir / "roadmap.yaml")

        # Clear cache to reload
        resolver.clear_cache()

        # Resolve for the task
        resolved = resolver.resolve_for_task("backend-1-task-001")

        # Find commit-required
        commit_resolved = next(r for r in resolved if r.standard.id == "commit-required")

        # Should be marked as overridden
        assert commit_resolved.is_overridden
        assert commit_resolved.override_reason == "Emergency hotfix - no tests needed"

    def test_override_only_applies_to_specific_item(self, test_roadmap_with_standards):
        """Override for one task shouldn't affect other tasks."""
        from vibey.roadmap.serialization import save_roadmap

        resolver = StandardsResolver(test_roadmap_with_standards)

        # Add override for task-001
        roadmap = resolver._get_roadmap()
        commit_std = roadmap.get_standard("commit-required")
        commit_std.add_override(
            target_id="backend-1-task-001",
            reason="Emergency hotfix",
            overridden_by="admin",
        )

        # Save roadmap to persist the override
        vibey_dir = test_roadmap_with_standards / ".vibey"
        save_roadmap(roadmap, vibey_dir / "roadmap.yaml")

        resolver.clear_cache()

        # task-001 should have override
        resolved_001 = resolver.resolve_for_task("backend-1-task-001")
        commit_001 = next(r for r in resolved_001 if r.standard.id == "commit-required")
        assert commit_001.is_overridden

        # task-002 should NOT have override
        resolved_002 = resolver.resolve_for_task("backend-1-task-002")
        commit_002 = next(r for r in resolved_002 if r.standard.id == "commit-required")
        assert not commit_002.is_overridden


class TestDisabledStandards:
    """Test that disabled standards are excluded from resolution."""

    def test_disabled_standard_not_included(self, test_roadmap_with_standards):
        """Disabled standards should not be included in resolved list."""
        from vibey.roadmap.serialization import save_roadmap

        resolver = StandardsResolver(test_roadmap_with_standards)

        # Disable commit-required
        roadmap = resolver._get_roadmap()
        commit_std = roadmap.get_standard("commit-required")
        commit_std.enabled = False

        # Save roadmap to persist the change
        vibey_dir = test_roadmap_with_standards / ".vibey"
        save_roadmap(roadmap, vibey_dir / "roadmap.yaml")

        resolver.clear_cache()

        # Resolve for task
        resolved = resolver.resolve_for_task("backend-1-task-001")

        # commit-required should not be in the list
        standard_ids = [r.standard.id for r in resolved]
        assert "commit-required" not in standard_ids


class TestHelperMethods:
    """Test resolver helper methods."""

    def test_has_standard(self, test_roadmap_with_standards):
        """has_standard should correctly identify if standard applies."""
        resolver = StandardsResolver(test_roadmap_with_standards)

        # Task should have commit-required
        assert resolver.has_standard("commit-required", "backend-1-task-001")

        # Track should NOT have security-review (sprint-level only)
        assert not resolver.has_standard("security-review", "backend")

    def test_get_standard(self, test_roadmap_with_standards):
        """get_standard should return ResolvedStandard if it applies."""
        resolver = StandardsResolver(test_roadmap_with_standards)

        # Get test-coverage for task
        resolved = resolver.get_standard("test-coverage", "backend-1-task-001")

        assert resolved is not None
        assert resolved.standard.id == "test-coverage"
        assert resolved.source_level == "track"  # Track overrides roadmap
        assert resolved.standard.validation["threshold"] == 90

    def test_get_standard_returns_none_if_not_found(self, test_roadmap_with_standards):
        """get_standard should return None if standard doesn't apply."""
        resolver = StandardsResolver(test_roadmap_with_standards)

        # nonexistent-standard doesn't exist
        resolved = resolver.get_standard("nonexistent-standard", "backend-1-task-001")

        assert resolved is None

    def test_get_blocking_standards(self, test_roadmap_with_standards):
        """get_blocking_standards should return only blocking standards."""
        resolver = StandardsResolver(test_roadmap_with_standards)

        blocking = resolver.get_blocking_standards("backend-1-task-001")

        # Should have 3 blocking standards:
        # - commit-required (roadmap)
        # - test-coverage (track)
        # - security-review (sprint)
        # NOT doc-review (warning mode)
        blocking_ids = [r.standard.id for r in blocking]
        assert len(blocking_ids) == 3
        assert "commit-required" in blocking_ids
        assert "test-coverage" in blocking_ids
        assert "security-review" in blocking_ids
        assert "doc-review" not in blocking_ids  # Warning, not blocking


class TestCaching:
    """Test resolver caching behavior."""

    def test_cache_avoids_repeated_file_loads(self, test_roadmap_with_standards):
        """Resolver should cache loaded objects."""
        resolver = StandardsResolver(test_roadmap_with_standards)

        # First call loads from file
        resolved1 = resolver.resolve_for_task("backend-1-task-001")

        # Second call uses cache
        resolved2 = resolver.resolve_for_task("backend-1-task-001")

        # Should get same result
        assert len(resolved1) == len(resolved2)

        # Cache should have objects
        assert resolver._roadmap_cache is not None
        assert "backend" in resolver._track_cache
        assert "backend-1" in resolver._sprint_cache

    def test_clear_cache_resets_cache(self, test_roadmap_with_standards):
        """clear_cache should reset all cached objects."""
        resolver = StandardsResolver(test_roadmap_with_standards)

        # Load some data
        resolver.resolve_for_task("backend-1-task-001")

        # Cache should be populated
        assert resolver._roadmap_cache is not None

        # Clear cache
        resolver.clear_cache()

        # Cache should be empty
        assert resolver._roadmap_cache is None
        assert len(resolver._track_cache) == 0
        assert len(resolver._sprint_cache) == 0
