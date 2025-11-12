#!/usr/bin/env python3
"""
Test hierarchical commit tracking implementation.

Tests:
1. TaskCompletionCommit creation and validation
2. GitCommit with REQUIRED platform tracking (Unix timestamps)
3. SprintCompletionCommit creation and validation
4. Sprint loading/saving with commits
5. Task loading/saving with platform-tracked commits (Unix timestamps)
6. Track loading/saving with commits

Note: Platform tracking is REQUIRED for all new commits.
Timestamps use Unix time (seconds since epoch) to avoid timezone issues.
"""

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import yaml

from vibey.roadmap.models import (
    GitCommit,
    TaskCompletionCommit,
    SprintCompletionCommit,
)
from vibey.roadmap.serialization.yaml_loader import load_sprint, load_track, load_tasks
from vibey.roadmap.serialization.yaml_dumper import save_sprint, save_track, save_tasks


def test_task_completion_commit():
    """Test TaskCompletionCommit creation and validation."""
    print("Testing TaskCompletionCommit...")

    commit = TaskCompletionCommit(
        task_id="test-1-task-001",
        sha="40c760091cb87cb8afc2edbd291469766d942858",
        message="fix: Complete task",
        date=datetime.now(timezone.utc),
        author="Test User <test@example.com>",
    )

    assert commit.task_id == "test-1-task-001"
    assert len(commit.sha) == 40
    print("✅ TaskCompletionCommit validation passed")


def test_git_commit_with_platform():
    """Test GitCommit with platform tracking."""
    print("\nTesting GitCommit with platform tracking...")

    # Test commit with platform (required)
    now_unix = int(datetime.now(timezone.utc).timestamp())
    commit = GitCommit(
        sha="a1b2c3d4e5f6",
        message="feat: Implement user authentication",
        date=datetime.now(timezone.utc),
        author="Test User <test@example.com>",
        platform="claude-code",
        submitted_at=now_unix,
    )

    assert commit.sha == "a1b2c3d4e5f6"
    assert commit.platform == "claude-code"
    assert commit.submitted_at == now_unix
    assert isinstance(commit.submitted_at, int)
    print("✅ GitCommit with platform tracking passed")

    # Test that platform is required
    try:
        commit_no_platform = GitCommit(
            sha="b2c3d4e5f6a7",
            message="fix: Bug fix",
            date=datetime.now(timezone.utc),
            author="Test User <test@example.com>",
            platform="",  # Empty platform should fail
            submitted_at=now_unix,
        )
        assert False, "Should have raised ValueError for empty platform"
    except TypeError:
        # Missing required argument
        print("✅ GitCommit requires platform field")
    except ValueError as e:
        # Empty platform validation
        assert "Platform is required" in str(e)
        print("✅ GitCommit validates non-empty platform")


def test_sprint_completion_commit():
    """Test SprintCompletionCommit creation and validation."""
    print("\nTesting SprintCompletionCommit...")

    commit = SprintCompletionCommit(
        sprint_id="test-1",
        sha="f0711771465374cabeac87f4809e005f07ac7aa1",
        message="fix: Complete sprint",
        date=datetime.now(timezone.utc),
        author="Test User <test@example.com>",
    )

    assert commit.sprint_id == "test-1"
    assert len(commit.sha) == 40
    print("✅ SprintCompletionCommit validation passed")


def test_sprint_commits_round_trip():
    """Test sprint loading and saving with commits."""
    print("\nTesting Sprint commits round-trip...")

    # Load existing sprint
    sprint_path = Path(".vibey/roadmap/infrastructure-fixes/infrastructure-fixes-1/sprint.yaml")
    if not sprint_path.exists():
        print("⚠️  Skipping - test sprint not found")
        return

    sprint = load_sprint(sprint_path)
    print(f"   Loaded sprint: {sprint.id}")
    print(f"   Original commits: {len(sprint.commits)}")

    # Add a test commit
    test_commit = TaskCompletionCommit(
        task_id="infrastructure-fixes-1-task-005",
        sha="40c760091cb87cb8afc2edbd291469766d942858",
        message="fix: Test task completion",
        date=datetime.now(timezone.utc),
        author="Test User <test@example.com>",
    )
    sprint.commits.append(test_commit)
    print(f"   Added test commit, total: {len(sprint.commits)}")

    # Save to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_path = Path(f.name)

    save_sprint(sprint, temp_path)
    print(f"   Saved to: {temp_path}")

    # Load back
    loaded_sprint = load_sprint(temp_path)
    print(f"   Reloaded commits: {len(loaded_sprint.commits)}")

    # Verify
    assert len(loaded_sprint.commits) == len(sprint.commits)
    assert loaded_sprint.commits[-1].task_id == "infrastructure-fixes-1-task-005"
    assert loaded_sprint.commits[-1].sha == "40c760091cb87cb8afc2edbd291469766d942858"

    # Cleanup
    temp_path.unlink()

    print("✅ Sprint commits round-trip passed")


def test_task_commits_with_platform_round_trip():
    """Test task git commits with platform tracking round-trip."""
    print("\nTesting Task commits with platform tracking round-trip...")

    # Load existing tasks
    tasks_path = Path(".vibey/roadmap/infrastructure-fixes/infrastructure-fixes-1/tasks.yaml")
    if not tasks_path.exists():
        print("⚠️  Skipping - test tasks not found")
        return

    tasks = load_tasks(tasks_path)
    if not tasks:
        print("⚠️  Skipping - no tasks found")
        return

    task = tasks[0]
    print(f"   Loaded task: {task.id}")
    print(f"   Original commits: {len(task.commits)}")

    # Add test commits with platform tracking (Unix timestamps)
    now_unix_1 = int(datetime.now(timezone.utc).timestamp())
    test_commit_1 = GitCommit(
        sha="a1b2c3d4e5f6",
        message="feat: Start implementation",
        date=datetime.now(timezone.utc),
        author="Test User <test@example.com>",
        platform="claude-code",
        submitted_at=now_unix_1,
    )
    task.commits.append(test_commit_1)

    now_unix_2 = int(datetime.now(timezone.utc).timestamp())
    test_commit_2 = GitCommit(
        sha="b2c3d4e5f6a7",
        message="fix: Bug fix from different platform",
        date=datetime.now(timezone.utc),
        author="Another User <another@example.com>",
        platform="goose",
        submitted_at=now_unix_2,
    )
    task.commits.append(test_commit_2)

    print(f"   Added 2 test commits with platform tracking, total: {len(task.commits)}")

    # Update tasks list
    tasks[0] = task

    # Save to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_path = Path(f.name)

    save_tasks(tasks, temp_path)
    print(f"   Saved to: {temp_path}")

    # Load back
    loaded_tasks = load_tasks(temp_path)
    loaded_task = loaded_tasks[0]
    print(f"   Reloaded commits: {len(loaded_task.commits)}")

    # Verify
    assert len(loaded_task.commits) == len(task.commits)

    # Check platform tracking on last two commits
    if len(loaded_task.commits) >= 2:
        second_last = loaded_task.commits[-2]
        last = loaded_task.commits[-1]

        assert second_last.sha == "a1b2c3d4e5f6"
        assert second_last.platform == "claude-code"
        assert second_last.submitted_at == now_unix_1
        assert isinstance(second_last.submitted_at, int)

        assert last.sha == "b2c3d4e5f6a7"
        assert last.platform == "goose"
        assert last.submitted_at == now_unix_2
        assert isinstance(last.submitted_at, int)

    # Cleanup
    temp_path.unlink()

    print("✅ Task commits with platform tracking round-trip passed")


def test_track_commits_round_trip():
    """Test track loading and saving with commits."""
    print("\nTesting Track commits round-trip...")

    # Load existing track
    track_path = Path(".vibey/roadmap/infrastructure-fixes/track.yaml")
    if not track_path.exists():
        print("⚠️  Skipping - test track not found")
        return

    track = load_track(track_path)
    print(f"   Loaded track: {track.id}")
    print(f"   Original commits: {len(track.commits)}")

    # Add a test commit
    test_commit = SprintCompletionCommit(
        sprint_id="infrastructure-fixes-1",
        sha="f0711771465374cabeac87f4809e005f07ac7aa1",
        message="fix: Test sprint completion",
        date=datetime.now(timezone.utc),
        author="Test User <test@example.com>",
    )
    track.commits.append(test_commit)
    print(f"   Added test commit, total: {len(track.commits)}")

    # Save to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_path = Path(f.name)

    save_track(track, temp_path)
    print(f"   Saved to: {temp_path}")

    # Load back
    loaded_track = load_track(temp_path)
    print(f"   Reloaded commits: {len(loaded_track.commits)}")

    # Verify
    assert len(loaded_track.commits) == len(track.commits)
    assert loaded_track.commits[-1].sprint_id == "infrastructure-fixes-1"
    assert loaded_track.commits[-1].sha == "f0711771465374cabeac87f4809e005f07ac7aa1"

    # Cleanup
    temp_path.unlink()

    print("✅ Track commits round-trip passed")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Hierarchical Commit Tracking - Test Suite")
    print("=" * 60)

    try:
        test_task_completion_commit()
        test_git_commit_with_platform()
        test_sprint_completion_commit()
        test_sprint_commits_round_trip()
        test_task_commits_with_platform_round_trip()
        test_track_commits_round_trip()

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
    import sys
    sys.exit(main())
