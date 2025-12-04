"""
Tests for RoadmapTicket domain model.

Tests cover:
- VersionHistoryEntry validation
- ActivityLogEntry creation
- PlatformDeployment tracking
- VersionStrategy configuration
- RoadmapTicket creation and validation
- Ultimate parent constraints
- Version management (bump, release)
- Activity logging
- Deployment tracking
- Track child accessors
- Lifecycle methods with logging
- Smart accessors inherited from L2
"""

from datetime import datetime, timezone, timedelta

import pytest

from vibey.roadmap.models.ticket import (
    # Support classes
    VersionHistoryEntry,
    ActivityLogEntry,
    PlatformDeployment,
    VersionStrategy,
    # Domain model
    RoadmapTicket,
    # Dependencies
    Criterion,
    CompletableTarget,
    FileExistsTarget,
    TicketStatus,
    TicketType,
    ActivityType,
    Priority,
)


# =============================================================================
# VERSION HISTORY ENTRY TESTS
# =============================================================================


class TestVersionHistoryEntry:
    """Tests for VersionHistoryEntry support class."""

    def test_create_valid_entry(self):
        """Test creating a valid version history entry."""
        entry = VersionHistoryEntry(
            version="1.0.0",
            released_at=datetime.now(timezone.utc),
            milestone="Initial Release",
            git_tag="v1.0.0",
            description="First production release",
        )
        assert entry.version == "1.0.0"
        assert entry.milestone == "Initial Release"
        assert entry.git_tag == "v1.0.0"

    def test_valid_semver_formats(self):
        """Test various valid semantic version formats."""
        valid_versions = [
            "0.0.1",
            "1.0.0",
            "10.20.30",
            "1.0.0-alpha",
            "1.0.0-alpha.1",
            "1.0.0-beta.2",
            "1.0.0-rc.1",
            "1.0.0+build",
            "1.0.0-alpha+001",
        ]
        now = datetime.now(timezone.utc)
        for v in valid_versions:
            entry = VersionHistoryEntry(version=v, released_at=now)
            assert entry.version == v

    def test_invalid_semver_format(self):
        """Test that invalid semver formats are rejected."""
        invalid_versions = [
            "1.0",  # Missing patch
            "v1.0.0",  # Leading 'v'
            "1",  # Just major
            "1.0.0.0",  # Too many parts
            "a.b.c",  # Non-numeric
            "",  # Empty
        ]
        now = datetime.now(timezone.utc)
        for v in invalid_versions:
            with pytest.raises(ValueError):
                VersionHistoryEntry(version=v, released_at=now)

    def test_optional_fields(self):
        """Test that optional fields default to None."""
        entry = VersionHistoryEntry(
            version="1.0.0",
            released_at=datetime.now(timezone.utc),
        )
        assert entry.milestone is None
        assert entry.git_tag is None
        assert entry.description is None


# =============================================================================
# ACTIVITY LOG ENTRY TESTS
# =============================================================================


class TestActivityLogEntry:
    """Tests for ActivityLogEntry support class."""

    def test_create_entry(self):
        """Test creating an activity log entry."""
        entry = ActivityLogEntry(
            action=ActivityType.ROADMAP_STARTED,
            ticket_id="roadmap-1",
            actor="developer",
            details="Started roadmap development",
            context={"phase": "planning"},
        )
        assert entry.action == ActivityType.ROADMAP_STARTED
        assert entry.ticket_id == "roadmap-1"
        assert entry.context == {"phase": "planning"}

    def test_timestamp_default(self):
        """Test that timestamp defaults to now."""
        before = datetime.now(timezone.utc)
        entry = ActivityLogEntry(action=ActivityType.ROADMAP_INITIALIZED)
        after = datetime.now(timezone.utc)
        assert before <= entry.timestamp <= after

    def test_optional_fields(self):
        """Test that optional fields default to None."""
        entry = ActivityLogEntry(action=ActivityType.TRACK_ADDED)
        assert entry.ticket_id is None
        assert entry.actor is None
        assert entry.details is None
        assert entry.context is None


# =============================================================================
# PLATFORM DEPLOYMENT TESTS
# =============================================================================


class TestPlatformDeployment:
    """Tests for PlatformDeployment support class."""

    def test_create_deployment(self):
        """Test creating a platform deployment record."""
        deployment = PlatformDeployment(
            platform="claude-code",
            context_window=100000,
            deployed_at=datetime.now(timezone.utc),
            primary=True,
            version="1.0.0",
        )
        assert deployment.platform == "claude-code"
        assert deployment.context_window == 100000
        assert deployment.primary is True

    def test_default_values(self):
        """Test default values for optional fields."""
        deployment = PlatformDeployment(platform="test")
        assert deployment.context_window is None
        assert deployment.deployed_at is None
        assert deployment.primary is False
        assert deployment.version is None


# =============================================================================
# VERSION STRATEGY TESTS
# =============================================================================


class TestVersionStrategy:
    """Tests for VersionStrategy support class."""

    def test_create_strategy(self):
        """Test creating a version strategy."""
        strategy = VersionStrategy(
            scheme="semver",
            auto_bump=True,
            major_triggers=["breaking_change"],
            minor_triggers=["new_feature"],
            patch_triggers=["bug_fix"],
        )
        assert strategy.scheme == "semver"
        assert strategy.auto_bump is True
        assert "breaking_change" in strategy.major_triggers

    def test_default_values(self):
        """Test default values."""
        strategy = VersionStrategy()
        assert strategy.scheme == "semver"
        assert strategy.auto_bump is False
        assert strategy.major_triggers == []
        assert strategy.minor_triggers == []
        assert strategy.patch_triggers == []


# =============================================================================
# ROADMAP TICKET TESTS - CREATION AND VALIDATION
# =============================================================================


class TestRoadmapTicketCreation:
    """Tests for RoadmapTicket creation and validation."""

    def test_create_minimal(self):
        """Test creating a minimal RoadmapTicket."""
        roadmap = RoadmapTicket(
            id="roadmap-1",
            name="Test Roadmap",
        )
        assert roadmap.id == "roadmap-1"
        assert roadmap.name == "Test Roadmap"
        assert roadmap.ticket_type == TicketType.ROADMAP
        assert roadmap.version == "0.1.0"

    def test_create_full(self):
        """Test creating a RoadmapTicket with all fields."""
        created = datetime.now(timezone.utc) - timedelta(hours=1)
        started = datetime.now(timezone.utc)
        strategy = VersionStrategy(scheme="semver", auto_bump=True)

        roadmap = RoadmapTicket(
            id="roadmap-1",
            name="Full Roadmap",
            description="A complete roadmap",
            version="1.0.0",
            version_strategy=strategy,
            target_completion=started + timedelta(days=90),
            status=TicketStatus.IN_PROGRESS,
            created_at=created,  # Must be before started_at
            started_at=started,  # Required for IN_PROGRESS
            priority=Priority.HIGH,
        )
        assert roadmap.version == "1.0.0"
        assert roadmap.version_strategy is not None
        assert roadmap.target_completion is not None

    def test_parent_ref_not_allowed(self):
        """Test that parent_ref cannot be set on RoadmapTicket."""
        with pytest.raises(ValueError, match="cannot have a parent_ref"):
            RoadmapTicket(
                id="roadmap-1",
                name="Test Roadmap",
                parent_ref="some-parent",
            )

    def test_valid_version_formats(self):
        """Test that valid semver versions are accepted."""
        valid_versions = ["0.1.0", "1.0.0", "2.5.3", "1.0.0-alpha"]
        for v in valid_versions:
            roadmap = RoadmapTicket(id="r1", name="Test", version=v)
            assert roadmap.version == v

    def test_invalid_version_format(self):
        """Test that invalid semver versions are rejected."""
        with pytest.raises(ValueError):
            RoadmapTicket(id="r1", name="Test", version="invalid")


# =============================================================================
# ROADMAP TICKET TESTS - ULTIMATE PARENT SEMANTICS
# =============================================================================


class TestRoadmapTicketHierarchy:
    """Tests for RoadmapTicket hierarchy semantics."""

    def test_is_ultimate_parent(self):
        """Test that Roadmap is always ultimate parent."""
        roadmap = RoadmapTicket(id="r1", name="Test")
        assert roadmap.is_ultimate_parent is True

    def test_is_not_child(self):
        """Test that Roadmap is never a child."""
        roadmap = RoadmapTicket(id="r1", name="Test")
        assert roadmap.is_child is False

    def test_is_not_ultimate_child(self):
        """Test that Roadmap is never an ultimate child."""
        roadmap = RoadmapTicket(id="r1", name="Test")
        assert roadmap.is_ultimate_child is False

    def test_parent_is_none(self):
        """Test that parent property returns None."""
        roadmap = RoadmapTicket(id="r1", name="Test")
        # Need to set loader first, but parent_ref is None so should return None
        assert roadmap.parent_ref is None

    def test_ticket_type_is_roadmap(self):
        """Test that ticket_type is always ROADMAP."""
        roadmap = RoadmapTicket(id="r1", name="Test")
        assert roadmap.ticket_type == TicketType.ROADMAP


# =============================================================================
# ROADMAP TICKET TESTS - VERSION MANAGEMENT
# =============================================================================


class TestRoadmapTicketVersionManagement:
    """Tests for RoadmapTicket version management."""

    def test_bump_patch(self):
        """Test bumping patch version."""
        roadmap = RoadmapTicket(id="r1", name="Test", version="1.0.0")
        bumped = roadmap.bump_version("patch")
        assert bumped.version == "1.0.1"
        assert roadmap.version == "1.0.0"  # Original unchanged
        assert len(bumped.version_history) == 1
        assert bumped.version_history[0].version == "1.0.0"

    def test_bump_minor(self):
        """Test bumping minor version."""
        roadmap = RoadmapTicket(id="r1", name="Test", version="1.2.3")
        bumped = roadmap.bump_version("minor")
        assert bumped.version == "1.3.0"  # Patch reset to 0
        assert len(bumped.version_history) == 1

    def test_bump_major(self):
        """Test bumping major version."""
        roadmap = RoadmapTicket(id="r1", name="Test", version="1.2.3")
        bumped = roadmap.bump_version("major")
        assert bumped.version == "2.0.0"  # Minor and patch reset to 0
        assert len(bumped.version_history) == 1

    def test_bump_invalid_part(self):
        """Test that invalid part raises error."""
        roadmap = RoadmapTicket(id="r1", name="Test", version="1.0.0")
        with pytest.raises(ValueError, match="Invalid version part"):
            roadmap.bump_version("invalid")

    def test_release(self):
        """Test creating a release."""
        roadmap = RoadmapTicket(id="r1", name="Test", version="1.0.0")
        released = roadmap.release(
            milestone="Sprint 1",
            git_tag="v1.0.0",
            description="First release",
        )
        assert len(released.version_history) == 1
        entry = released.version_history[0]
        assert entry.version == "1.0.0"
        assert entry.milestone == "Sprint 1"
        assert entry.git_tag == "v1.0.0"

    def test_version_with_prerelease(self):
        """Test bumping version with prerelease suffix."""
        roadmap = RoadmapTicket(id="r1", name="Test", version="1.0.0-alpha")
        bumped = roadmap.bump_version("patch")
        assert bumped.version == "1.0.1"  # Prerelease stripped


# =============================================================================
# ROADMAP TICKET TESTS - ACTIVITY LOGGING
# =============================================================================


class TestRoadmapTicketActivityLogging:
    """Tests for RoadmapTicket activity logging."""

    def test_log_activity(self):
        """Test logging an activity."""
        roadmap = RoadmapTicket(id="r1", name="Test")
        logged = roadmap.log_activity(
            action=ActivityType.TRACK_ADDED,
            details="Added core track",
            ticket_id="track-core",
            actor="developer",
            context={"track_name": "core"},
        )
        assert len(logged.activity_log) == 1
        entry = logged.activity_log[0]
        assert entry.action == ActivityType.TRACK_ADDED
        assert entry.ticket_id == "track-core"
        assert entry.context == {"track_name": "core"}

    def test_log_multiple_activities(self):
        """Test logging multiple activities."""
        roadmap = RoadmapTicket(id="r1", name="Test")
        logged1 = roadmap.log_activity(action=ActivityType.ROADMAP_INITIALIZED)
        logged2 = logged1.log_activity(action=ActivityType.TRACK_ADDED)
        logged3 = logged2.log_activity(action=ActivityType.SPRINT_STARTED)
        assert len(logged3.activity_log) == 3

    def test_start_logs_activity(self):
        """Test that start() logs activity."""
        roadmap = RoadmapTicket(
            id="r1",
            name="Test",
            status=TicketStatus.NOT_STARTED,
        )
        started = roadmap.start()
        assert started.status == TicketStatus.IN_PROGRESS
        assert len(started.activity_log) == 1
        assert started.activity_log[0].action == ActivityType.ROADMAP_STARTED

    def test_complete_logs_activity(self):
        """Test that complete() logs activity."""
        # Create roadmap with criteria met
        created = datetime.now(timezone.utc) - timedelta(hours=1)
        started = datetime.now(timezone.utc)
        roadmap = RoadmapTicket(
            id="r1",
            name="Test",
            status=TicketStatus.IN_PROGRESS,
            created_at=created,  # Must be before started_at
            started_at=started,  # Required for IN_PROGRESS
        )
        completed = roadmap.complete()
        assert completed.status == TicketStatus.COMPLETED
        assert len(completed.activity_log) == 1
        assert completed.activity_log[0].action == ActivityType.ROADMAP_COMPLETED


# =============================================================================
# ROADMAP TICKET TESTS - DEPLOYMENT TRACKING
# =============================================================================


class TestRoadmapTicketDeployment:
    """Tests for RoadmapTicket deployment tracking."""

    def test_deploy_to_platform(self):
        """Test deploying to a platform."""
        roadmap = RoadmapTicket(id="r1", name="Test", version="1.0.0")
        deployed = roadmap.deploy_to_platform(
            platform="claude-code",
            primary=True,
            context_window=100000,
        )
        assert deployed.deployed_at is not None
        assert len(deployed.deployed_platforms) == 1
        assert deployed.deployed_platforms[0].platform == "claude-code"
        assert deployed.deployed_platforms[0].primary is True
        assert deployed.deployed_platforms[0].version == "1.0.0"

    def test_deploy_multiple_platforms(self):
        """Test deploying to multiple platforms."""
        roadmap = RoadmapTicket(id="r1", name="Test")
        d1 = roadmap.deploy_to_platform("claude-code", primary=True)
        d2 = d1.deploy_to_platform("goose", primary=False)
        assert len(d2.deployed_platforms) == 2

    def test_primary_platform_changes(self):
        """Test that setting new primary unsets old primary."""
        roadmap = RoadmapTicket(id="r1", name="Test")
        d1 = roadmap.deploy_to_platform("claude-code", primary=True)
        d2 = d1.deploy_to_platform("goose", primary=True)

        # Old primary should be False
        claude_platform = next(p for p in d2.deployed_platforms if p.platform == "claude-code")
        goose_platform = next(p for p in d2.deployed_platforms if p.platform == "goose")
        assert claude_platform.primary is False
        assert goose_platform.primary is True

    def test_get_primary_platform(self):
        """Test getting the primary platform."""
        roadmap = RoadmapTicket(id="r1", name="Test")
        d1 = roadmap.deploy_to_platform("claude-code", primary=True)
        d2 = d1.deploy_to_platform("goose", primary=False)

        primary = d2.get_primary_platform()
        assert primary is not None
        assert primary.platform == "claude-code"

    def test_get_primary_platform_none(self):
        """Test getting primary platform when none set."""
        roadmap = RoadmapTicket(id="r1", name="Test")
        deployed = roadmap.deploy_to_platform("claude-code", primary=False)
        assert deployed.get_primary_platform() is None


# =============================================================================
# ROADMAP TICKET TESTS - TRACK CHILDREN
# =============================================================================


class TestRoadmapTicketTrackChildren:
    """Tests for RoadmapTicket track child accessors."""

    def test_track_criteria_empty(self):
        """Test track_criteria with no criteria."""
        roadmap = RoadmapTicket(id="r1", name="Test")
        assert roadmap.track_criteria == []
        assert roadmap.tracks_total == 0
        assert roadmap.tracks_completed == 0

    def test_track_criteria_with_tracks(self):
        """Test track_criteria with CompletableTarget criteria."""
        roadmap = RoadmapTicket(
            id="r1",
            name="Test",
            criteria=[
                Criterion(
                    id="crit-1",
                    name="Core Track Complete",
                    description="Core track must be completed",
                    target=CompletableTarget(
                        completable_id="track-core",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="crit-2",
                    name="Platform Track Complete",
                    description="Platform track must be completed",
                    target=CompletableTarget(
                        completable_id="track-platform",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )
        assert len(roadmap.track_criteria) == 2
        assert roadmap.tracks_total == 2

    def test_get_track_ids(self):
        """Test getting track IDs from criteria."""
        roadmap = RoadmapTicket(
            id="r1",
            name="Test",
            criteria=[
                Criterion(
                    id="crit-1",
                    name="Core Track",
                    description="Core track must be completed",
                    target=CompletableTarget(
                        completable_id="track-core",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )
        track_ids = roadmap.get_track_ids()
        assert track_ids == ["track-core"]

    def test_tracks_completed_count(self):
        """Test counting completed tracks."""
        roadmap = RoadmapTicket(
            id="r1",
            name="Test",
            criteria=[
                Criterion(
                    id="crit-1",
                    name="Core Track",
                    description="Core track must be completed",
                    target=CompletableTarget(
                        completable_id="track-core",
                        required_status=TicketStatus.COMPLETED,
                        current_status=TicketStatus.COMPLETED,  # Met!
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="crit-2",
                    name="Platform Track",
                    description="Platform track must be completed",
                    target=CompletableTarget(
                        completable_id="track-platform",
                        required_status=TicketStatus.COMPLETED,
                        current_status=TicketStatus.IN_PROGRESS,  # Not met
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )
        assert roadmap.tracks_completed == 1
        assert roadmap.tracks_total == 2

    def test_non_track_criteria_not_counted(self):
        """Test that non-CompletableTarget criteria aren't counted as tracks."""
        roadmap = RoadmapTicket(
            id="r1",
            name="Test",
            criteria=[
                Criterion(
                    id="crit-1",
                    name="Track Criterion",
                    description="Track must be completed",
                    target=CompletableTarget(
                        completable_id="track-core",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="crit-2",
                    name="File Criterion",
                    description="README file must exist",
                    target=FileExistsTarget(paths=["README.md"]),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )
        assert roadmap.tracks_total == 1  # Only the CompletableTarget


# =============================================================================
# ROADMAP TICKET TESTS - INHERITED BEHAVIOR
# =============================================================================


class TestRoadmapTicketInheritedBehavior:
    """Tests for behavior inherited from L1/L2."""

    def test_lifecycle_from_ticket(self):
        """Test lifecycle methods work."""
        roadmap = RoadmapTicket(
            id="r1",
            name="Test",
            status=TicketStatus.NOT_STARTED,
        )

        # Start
        started = roadmap.start()
        assert started.status == TicketStatus.IN_PROGRESS
        assert started.started_at is not None

        # Complete
        completed = started.complete()
        assert completed.status == TicketStatus.COMPLETED
        assert completed.completed_at is not None

    def test_convenience_accessors(self):
        """Test convenience accessors from HierarchicalTicket."""
        roadmap = RoadmapTicket(
            id="r1",
            name="Test",
            criteria=[
                Criterion(
                    id="c1",
                    name="File",
                    description="README file must exist",
                    target=FileExistsTarget(paths=["README.md"]),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="c2",
                    name="Track",
                    description="Track must be completed",
                    target=CompletableTarget(
                        completable_id="track-1",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )

        # deliverables (FileExistsTarget)
        assert len(roadmap.deliverables) == 1

        # subtasks (CompletableTarget blocking COMPLETED)
        assert len(roadmap.subtasks) == 1

    def test_progress_computation(self):
        """Test progress computation from Completable."""
        roadmap = RoadmapTicket(
            id="r1",
            name="Test",
            criteria=[
                Criterion(
                    id="c1",
                    name="Met Criterion",
                    description="Track 1 must be completed",
                    target=CompletableTarget(
                        completable_id="track-1",
                        required_status=TicketStatus.COMPLETED,
                        current_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="c2",
                    name="Unmet Criterion",
                    description="Track 2 must be completed",
                    target=CompletableTarget(
                        completable_id="track-2",
                        required_status=TicketStatus.COMPLETED,
                        current_status=TicketStatus.NOT_STARTED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )

        progress = roadmap.progress
        assert progress.total == 2
        assert progress.completed == 1
        assert progress.completion_percent == 50.0

    def test_immutable_copy(self):
        """Test that modifications return new instances."""
        roadmap = RoadmapTicket(id="r1", name="Test", version="1.0.0")

        bumped = roadmap.bump_version("patch")
        assert bumped is not roadmap
        assert bumped.version != roadmap.version

        logged = roadmap.log_activity(action=ActivityType.ROADMAP_INITIALIZED)
        assert logged is not roadmap
        assert len(logged.activity_log) == 1
        assert len(roadmap.activity_log) == 0

    def test_children_property(self):
        """Test children property from Completable."""
        roadmap = RoadmapTicket(
            id="r1",
            name="Test",
            criteria=[
                Criterion(
                    id="c1",
                    name="Track 1",
                    description="Core track must be completed",
                    target=CompletableTarget(
                        completable_id="track-core",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="c2",
                    name="Track 2",
                    description="Platform track must be completed",
                    target=CompletableTarget(
                        completable_id="track-platform",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )

        # children property extracts completable_ids
        children = roadmap.children
        assert "track-core" in children
        assert "track-platform" in children

    def test_is_complete(self):
        """Test is_complete from Completable."""
        # All criteria met
        complete_roadmap = RoadmapTicket(
            id="r1",
            name="Test",
            criteria=[
                Criterion(
                    id="c1",
                    name="Track",
                    description="Track must be completed",
                    target=CompletableTarget(
                        completable_id="track-1",
                        required_status=TicketStatus.COMPLETED,
                        current_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )
        assert complete_roadmap.is_complete is True

        # Not all criteria met
        incomplete_roadmap = RoadmapTicket(
            id="r2",
            name="Test",
            criteria=[
                Criterion(
                    id="c1",
                    name="Track",
                    description="Track must be completed",
                    target=CompletableTarget(
                        completable_id="track-1",
                        required_status=TicketStatus.COMPLETED,
                        current_status=TicketStatus.IN_PROGRESS,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )
        assert incomplete_roadmap.is_complete is False
