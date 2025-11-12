#!/usr/bin/env python3
"""
Test platform validation at roadmap level.

Tests:
1. PlatformDeployment creation and validation
2. Roadmap platform helper methods
3. Platform validation when adding commits
4. Error messages for invalid platforms
5. YAML round-trip with deployed platforms
"""

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from vibey.roadmap.models import (
    Roadmap,
    Task,
    PlatformDeployment,
    VersionStrategy,
    Progress,
    Metadata,
    Status,
    TaskStatus,
    Priority,
    TaskType,
    Complexity,
    TaskMetadata,
    DependencyStatus,
    VersionBumpTrigger,
)
from vibey.roadmap.serialization.yaml_dumper import save_roadmap, save_tasks
from vibey.roadmap.serialization.yaml_loader import load_roadmap, load_tasks
from vibey.roadmap.validation import (
    validate_commit_platform,
    add_commit_with_validation,
    PlatformValidationError,
)


def test_platform_deployment_creation():
    """Test PlatformDeployment creation and validation."""
    print("Testing PlatformDeployment creation...")

    now_unix = int(datetime.now(timezone.utc).timestamp())

    # Valid platform deployment
    platform = PlatformDeployment(
        platform="claude-code",
        context_window=200000,
        deployed_at=now_unix,
        deployed_by="alice@example.com",
        primary=True,
    )

    assert platform.platform == "claude-code"
    assert platform.context_window == 200000
    assert platform.primary is True
    print("✅ Valid PlatformDeployment created")

    # Test validation: empty platform
    try:
        PlatformDeployment(
            platform="",
            context_window=200000,
            deployed_at=now_unix,
            deployed_by="alice@example.com",
        )
        assert False, "Should have raised ValueError for empty platform"
    except ValueError as e:
        assert "Platform name is required" in str(e)
        print("✅ Empty platform rejected")

    # Test validation: negative context window
    try:
        PlatformDeployment(
            platform="claude-code",
            context_window=-1,
            deployed_at=now_unix,
            deployed_by="alice@example.com",
        )
        assert False, "Should have raised ValueError for negative context window"
    except ValueError as e:
        assert "Context window must be positive" in str(e)
        print("✅ Negative context window rejected")

    # Test validation: negative timestamp
    try:
        PlatformDeployment(
            platform="claude-code",
            context_window=200000,
            deployed_at=-1,
            deployed_by="alice@example.com",
        )
        assert False, "Should have raised ValueError for negative timestamp"
    except ValueError as e:
        assert "positive Unix timestamp" in str(e)
        print("✅ Negative timestamp rejected")


def test_roadmap_platform_helpers():
    """Test Roadmap platform helper methods."""
    print("\nTesting Roadmap platform helper methods...")

    now_unix = int(datetime.now(timezone.utc).timestamp())

    # Create roadmap with deployed platforms
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
            tasks_total=1,
            tasks_completed=0,
            completion_percent=0,
        ),
        tracks=[],
        activity_log=[],
        metadata=Metadata(
            created_by="test",
            framework_version="1.0.0",
            schema_version="2.1",
            last_updated=datetime.now(timezone.utc),
        ),
        deployed_platforms=[
            PlatformDeployment(
                platform="claude-code",
                context_window=200000,
                deployed_at=now_unix,
                deployed_by="alice@example.com",
                primary=True,
            ),
            PlatformDeployment(
                platform="goose",
                context_window=128000,
                deployed_at=now_unix + 3600,
                deployed_by="bob@example.com",
                primary=False,
            ),
        ],
    )

    # Test is_platform_deployed
    assert roadmap.is_platform_deployed("claude-code") is True
    assert roadmap.is_platform_deployed("goose") is True
    assert roadmap.is_platform_deployed("cursor") is False
    print("✅ is_platform_deployed() works correctly")

    # Test get_platform_deployment
    claude = roadmap.get_platform_deployment("claude-code")
    assert claude is not None
    assert claude.platform == "claude-code"
    assert claude.context_window == 200000
    print("✅ get_platform_deployment() works correctly")

    # Test get_deployed_platform_names
    names = roadmap.get_deployed_platform_names()
    assert "claude-code" in names
    assert "goose" in names
    assert len(names) == 2
    print("✅ get_deployed_platform_names() works correctly")

    # Test get_primary_platform
    primary = roadmap.get_primary_platform()
    assert primary is not None
    assert primary.platform == "claude-code"
    assert primary.primary is True
    print("✅ get_primary_platform() works correctly")


def test_platform_validation_success():
    """Test successful platform validation."""
    print("\nTesting successful platform validation...")

    now_unix = int(datetime.now(timezone.utc).timestamp())

    # Create roadmap with deployed platform
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
            tasks_total=1,
            tasks_completed=0,
            completion_percent=0,
        ),
        tracks=[],
        activity_log=[],
        metadata=Metadata(
            created_by="test",
            framework_version="1.0.0",
            schema_version="2.1",
            last_updated=datetime.now(timezone.utc),
        ),
        deployed_platforms=[
            PlatformDeployment(
                platform="claude-code",
                context_window=200000,
                deployed_at=now_unix,
                deployed_by="alice@example.com",
                primary=True,
            ),
        ],
    )

    # Create task
    task = Task(
        id="test-1-task-001",
        sprint_id="test-1",
        track_id="test",
        roadmap_id="test-roadmap",
        task_type=TaskType.DEVELOPMENT,
        title="Test Task",
        description="Test task",
        status=TaskStatus.NOT_STARTED,
        blocked=False,
        created=datetime.now(timezone.utc),
        assigned_agent="test-agent",
        priority=Priority.MEDIUM,
        estimated_tokens=10000,
        complexity=Complexity.MEDIUM,
        dependencies=[],
        blocks=[],
        blocked_by=[],
        depends_on=[],
        depended_on_by=[],
        metadata=TaskMetadata(last_updated=datetime.now(timezone.utc)),
    )

    # Validate platform - should succeed
    validate_commit_platform(task, "claude-code", roadmap=roadmap)
    print("✅ Platform validation succeeded for deployed platform")

    # Add commit with validation - should succeed
    add_commit_with_validation(
        task,
        sha="a1b2c3d4",
        message="feat: Test feature",
        author="Alice <alice@example.com>",
        platform="claude-code",
        roadmap=roadmap,
    )

    assert len(task.commits) == 1
    assert task.commits[0].platform == "claude-code"
    print("✅ add_commit_with_validation() succeeded")


def test_platform_validation_failure():
    """Test platform validation failures."""
    print("\nTesting platform validation failures...")

    now_unix = int(datetime.now(timezone.utc).timestamp())

    # Create roadmap with deployed platform
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
            tasks_total=1,
            tasks_completed=0,
            completion_percent=0,
        ),
        tracks=[],
        activity_log=[],
        metadata=Metadata(
            created_by="test",
            framework_version="1.0.0",
            schema_version="2.1",
            last_updated=datetime.now(timezone.utc),
        ),
        deployed_platforms=[
            PlatformDeployment(
                platform="claude-code",
                context_window=200000,
                deployed_at=now_unix,
                deployed_by="alice@example.com",
                primary=True,
            ),
        ],
    )

    # Create task
    task = Task(
        id="test-1-task-001",
        sprint_id="test-1",
        track_id="test",
        roadmap_id="test-roadmap",
        task_type=TaskType.DEVELOPMENT,
        title="Test Task",
        description="Test task",
        status=TaskStatus.NOT_STARTED,
        blocked=False,
        created=datetime.now(timezone.utc),
        assigned_agent="test-agent",
        priority=Priority.MEDIUM,
        estimated_tokens=10000,
        complexity=Complexity.MEDIUM,
        dependencies=[],
        blocks=[],
        blocked_by=[],
        depends_on=[],
        depended_on_by=[],
        metadata=TaskMetadata(last_updated=datetime.now(timezone.utc)),
    )

    # Try to validate undeployed platform - should fail
    try:
        validate_commit_platform(task, "goose", roadmap=roadmap)
        assert False, "Should have raised PlatformValidationError"
    except PlatformValidationError as e:
        assert "goose" in str(e)
        assert "not deployed" in str(e)
        assert "claude-code" in str(e)  # Should mention deployed platforms
        print("✅ Platform validation failed for undeployed platform")
        print(f"   Error message: {str(e)[:100]}...")


def test_roadmap_yaml_round_trip_with_platforms():
    """Test roadmap YAML serialization with deployed platforms."""
    print("\nTesting roadmap YAML round-trip with platforms...")

    now_unix = int(datetime.now(timezone.utc).timestamp())

    # Create roadmap with platforms
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
            tasks_total=1,
            tasks_completed=0,
            completion_percent=0,
        ),
        tracks=[],
        activity_log=[],
        metadata=Metadata(
            created_by="test",
            framework_version="1.0.0",
            schema_version="2.1",
            last_updated=datetime.now(timezone.utc),
        ),
        deployed_platforms=[
            PlatformDeployment(
                platform="claude-code",
                context_window=200000,
                deployed_at=now_unix,
                deployed_by="alice@example.com",
                primary=True,
            ),
            PlatformDeployment(
                platform="goose",
                context_window=128000,
                deployed_at=now_unix + 3600,
                deployed_by="bob@example.com",
                primary=False,
            ),
        ],
    )

    print(f"   Created roadmap with {len(roadmap.deployed_platforms)} platforms")

    # Save to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_path = Path(f.name)

    save_roadmap(roadmap, temp_path)
    print(f"   Saved to: {temp_path}")

    # Load back
    loaded_roadmap = load_roadmap(temp_path)
    print(f"   Loaded roadmap with {len(loaded_roadmap.deployed_platforms)} platforms")

    # Verify
    assert len(loaded_roadmap.deployed_platforms) == 2

    # Check first platform
    claude = loaded_roadmap.get_platform_deployment("claude-code")
    assert claude is not None
    assert claude.platform == "claude-code"
    assert claude.context_window == 200000
    assert claude.deployed_at == now_unix
    assert claude.deployed_by == "alice@example.com"
    assert claude.primary is True

    # Check second platform
    goose = loaded_roadmap.get_platform_deployment("goose")
    assert goose is not None
    assert goose.platform == "goose"
    assert goose.context_window == 128000
    assert goose.deployed_at == now_unix + 3600
    assert goose.deployed_by == "bob@example.com"
    assert goose.primary is False

    # Cleanup
    temp_path.unlink()

    print("✅ Roadmap YAML round-trip with platforms passed")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Platform Validation - Test Suite")
    print("=" * 60)

    try:
        test_platform_deployment_creation()
        test_roadmap_platform_helpers()
        test_platform_validation_success()
        test_platform_validation_failure()
        test_roadmap_yaml_round_trip_with_platforms()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
