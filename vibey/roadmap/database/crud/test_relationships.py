"""
Tests for relationship and junction table CRUD operations.

Tests cover:
- Blocking relationships (entity_blocks, entity_blocked_by)
- Soft dependencies (entity_depends_on)
- Junction tables (entity_deliverables, entity_commits)
- Quality gates
- Dependency chain queries with recursive CTEs
"""

import pytest
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import os

from ..connection import get_connection, close_connection
from ..schema import create_schema
from .roadmap import create_roadmap
from .track import create_track
from .sprint import create_sprint
from .task import create_task
from .relationships import (
    # Blocking
    add_blocker,
    remove_blocker,
    get_blockers,
    get_blocked_by,
    is_blocked,
    # Dependencies
    add_dependency,
    remove_dependency,
    get_dependencies,
    get_dependents,
    # Deliverables
    create_deliverable,
    link_deliverable,
    unlink_deliverable,
    get_deliverables,
    # Commits
    create_commit,
    get_commit_by_hash,
    link_commit,
    unlink_commit,
    get_commits,
    # Quality gates
    add_quality_gate,
    update_quality_gate,
    remove_quality_gate,
    list_quality_gates,
    get_blocking_gates,
    # Chain queries
    get_dependency_chain,
    get_blocking_chain,
    detect_circular_dependencies,
    detect_circular_blockers,
)


@pytest.fixture
def db_path():
    """Create a temporary database file."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield Path(path)
    close_connection(Path(path))
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def conn(db_path):
    """Create a connection with schema initialized."""
    connection = get_connection(db_path=db_path)
    create_schema(conn=connection)
    connection.commit()
    return connection


@pytest.fixture
def sample_hierarchy(conn):
    """Create a sample roadmap > track > sprint > task hierarchy."""
    now = datetime.now(timezone.utc)

    # Create roadmap
    create_roadmap(
        id="test-roadmap",
        name="Test Roadmap",
        version="1.0.0",
        status="in_progress",
        created=now,
        conn=conn,
    )

    # Create tracks
    create_track(
        id="track-1",
        roadmap_id="test-roadmap",
        name="Track 1",
        status="in_progress",
        created=now,
        conn=conn,
    )
    create_track(
        id="track-2",
        roadmap_id="test-roadmap",
        name="Track 2",
        status="not_started",
        created=now,
        conn=conn,
    )

    # Create sprints
    create_sprint(
        id="sprint-1",
        track_id="track-1",
        roadmap_id="test-roadmap",
        name="Sprint 1",
        status="in_progress",
        created=now,
        conn=conn,
    )
    create_sprint(
        id="sprint-2",
        track_id="track-1",
        roadmap_id="test-roadmap",
        name="Sprint 2",
        status="not_started",
        created=now,
        conn=conn,
    )

    # Create tasks
    create_task(
        id="task-1",
        sprint_id="sprint-1",
        track_id="track-1",
        roadmap_id="test-roadmap",
        task_type="development",
        title="Task 1",
        status="in_progress",
        created=now,
        conn=conn,
    )
    create_task(
        id="task-2",
        sprint_id="sprint-1",
        track_id="track-1",
        roadmap_id="test-roadmap",
        task_type="development",
        title="Task 2",
        status="not_started",
        created=now,
        conn=conn,
    )
    create_task(
        id="task-3",
        sprint_id="sprint-2",
        track_id="track-1",
        roadmap_id="test-roadmap",
        task_type="development",
        title="Task 3",
        status="not_started",
        created=now,
        conn=conn,
    )

    conn.commit()
    return conn


# =============================================================================
# BLOCKING RELATIONSHIP TESTS
# =============================================================================

class TestBlockingRelationships:
    """Tests for blocking relationship operations."""

    def test_add_blocker(self, sample_hierarchy):
        """Test adding a blocking relationship."""
        conn = sample_hierarchy

        blocker_id = add_blocker(
            blocker_type="task",
            blocker_id="task-1",
            blocked_type="task",
            blocked_id="task-2",
            reason="task-1 must complete first",
            conn=conn,
        )
        conn.commit()

        assert blocker_id > 0

        # Verify in entity_blocks
        row = conn.execute(
            "SELECT * FROM entity_blocks WHERE id = ?",
            (blocker_id,),
        ).fetchone()
        assert row is not None
        assert row["blocker_id"] == "task-1"
        assert row["blocked_id"] == "task-2"

        # Verify in entity_blocked_by
        row = conn.execute(
            """SELECT * FROM entity_blocked_by
               WHERE blocked_id = ? AND blocker_id = ?""",
            ("task-2", "task-1"),
        ).fetchone()
        assert row is not None

    def test_remove_blocker(self, sample_hierarchy):
        """Test removing a blocking relationship."""
        conn = sample_hierarchy

        add_blocker("task", "task-1", "task", "task-2", conn=conn)
        conn.commit()

        result = remove_blocker("task", "task-1", "task", "task-2", conn=conn)
        conn.commit()

        assert result is True

        # Verify removed from both tables
        assert conn.execute(
            """SELECT COUNT(*) FROM entity_blocks
               WHERE blocker_id = ? AND blocked_id = ?""",
            ("task-1", "task-2"),
        ).fetchone()[0] == 0

        assert conn.execute(
            """SELECT COUNT(*) FROM entity_blocked_by
               WHERE blocked_id = ? AND blocker_id = ?""",
            ("task-2", "task-1"),
        ).fetchone()[0] == 0

    def test_remove_nonexistent_blocker(self, sample_hierarchy):
        """Test removing a blocker that doesn't exist."""
        conn = sample_hierarchy

        result = remove_blocker("task", "task-1", "task", "task-2", conn=conn)
        assert result is False

    def test_get_blockers(self, sample_hierarchy):
        """Test getting all blockers for an entity."""
        conn = sample_hierarchy

        add_blocker("task", "task-1", "task", "task-3", reason="reason 1", conn=conn)
        add_blocker("task", "task-2", "task", "task-3", reason="reason 2", conn=conn)
        conn.commit()

        blockers = get_blockers("task", "task-3", conn=conn)

        assert len(blockers) == 2
        blocker_ids = {b["blocker_id"] for b in blockers}
        assert blocker_ids == {"task-1", "task-2"}

    def test_get_blocked_by(self, sample_hierarchy):
        """Test getting all entities blocked by a given entity."""
        conn = sample_hierarchy

        add_blocker("task", "task-1", "task", "task-2", conn=conn)
        add_blocker("task", "task-1", "task", "task-3", conn=conn)
        conn.commit()

        blocked = get_blocked_by("task", "task-1", conn=conn)

        assert len(blocked) == 2
        blocked_ids = {b["blocked_id"] for b in blocked}
        assert blocked_ids == {"task-2", "task-3"}

    def test_is_blocked(self, sample_hierarchy):
        """Test checking if an entity is blocked."""
        conn = sample_hierarchy

        assert is_blocked("task", "task-2", conn=conn) is False

        add_blocker("task", "task-1", "task", "task-2", conn=conn)
        conn.commit()

        assert is_blocked("task", "task-2", conn=conn) is True
        assert is_blocked("task", "task-1", conn=conn) is False


# =============================================================================
# SOFT DEPENDENCY TESTS
# =============================================================================

class TestSoftDependencies:
    """Tests for soft dependency operations."""

    def test_add_dependency(self, sample_hierarchy):
        """Test adding a soft dependency."""
        conn = sample_hierarchy

        dep_id = add_dependency(
            dependent_type="sprint",
            dependent_id="sprint-2",
            dependency_type="sprint",
            dependency_id="sprint-1",
            reason="sprint-2 depends on sprint-1 work",
            conn=conn,
        )
        conn.commit()

        assert dep_id > 0

    def test_remove_dependency(self, sample_hierarchy):
        """Test removing a soft dependency."""
        conn = sample_hierarchy

        add_dependency("sprint", "sprint-2", "sprint", "sprint-1", conn=conn)
        conn.commit()

        result = remove_dependency("sprint", "sprint-2", "sprint", "sprint-1", conn=conn)
        conn.commit()

        assert result is True

    def test_get_dependencies(self, sample_hierarchy):
        """Test getting all dependencies for an entity."""
        conn = sample_hierarchy

        add_dependency("task", "task-3", "task", "task-1", reason="needs task-1", conn=conn)
        add_dependency("task", "task-3", "task", "task-2", reason="needs task-2", conn=conn)
        conn.commit()

        deps = get_dependencies("task", "task-3", conn=conn)

        assert len(deps) == 2
        dep_ids = {d["dependency_id"] for d in deps}
        assert dep_ids == {"task-1", "task-2"}

    def test_get_dependents(self, sample_hierarchy):
        """Test getting all entities that depend on a given entity."""
        conn = sample_hierarchy

        add_dependency("task", "task-2", "task", "task-1", conn=conn)
        add_dependency("task", "task-3", "task", "task-1", conn=conn)
        conn.commit()

        dependents = get_dependents("task", "task-1", conn=conn)

        assert len(dependents) == 2
        dependent_ids = {d["dependent_id"] for d in dependents}
        assert dependent_ids == {"task-2", "task-3"}


# =============================================================================
# DELIVERABLES JUNCTION TESTS
# =============================================================================

class TestDeliverables:
    """Tests for deliverable operations."""

    def test_create_deliverable(self, sample_hierarchy):
        """Test creating a deliverable."""
        conn = sample_hierarchy

        deliv_id = create_deliverable(
            description="API documentation",
            status="pending",
            artifact_path="docs/api.md",
            conn=conn,
        )
        conn.commit()

        assert deliv_id > 0

        row = conn.execute(
            "SELECT * FROM deliverables WHERE id = ?",
            (deliv_id,),
        ).fetchone()
        assert row["description"] == "API documentation"
        assert row["status"] == "pending"

    def test_link_deliverable(self, sample_hierarchy):
        """Test linking a deliverable to an entity."""
        conn = sample_hierarchy

        deliv_id = create_deliverable("Test deliverable", conn=conn)
        link_id = link_deliverable("task", "task-1", deliv_id, conn=conn)
        conn.commit()

        assert link_id > 0

    def test_unlink_deliverable(self, sample_hierarchy):
        """Test unlinking a deliverable from an entity."""
        conn = sample_hierarchy

        deliv_id = create_deliverable("Test deliverable", conn=conn)
        link_deliverable("task", "task-1", deliv_id, conn=conn)
        conn.commit()

        result = unlink_deliverable("task", "task-1", deliv_id, conn=conn)
        conn.commit()

        assert result is True

    def test_get_deliverables(self, sample_hierarchy):
        """Test getting all deliverables for an entity."""
        conn = sample_hierarchy

        deliv1_id = create_deliverable("Deliverable 1", conn=conn)
        deliv2_id = create_deliverable("Deliverable 2", status="completed", conn=conn)
        link_deliverable("sprint", "sprint-1", deliv1_id, conn=conn)
        link_deliverable("sprint", "sprint-1", deliv2_id, conn=conn)
        conn.commit()

        deliverables = get_deliverables("sprint", "sprint-1", conn=conn)

        assert len(deliverables) == 2
        descriptions = {d["description"] for d in deliverables}
        assert descriptions == {"Deliverable 1", "Deliverable 2"}

    def test_deliverable_shared_across_entities(self, sample_hierarchy):
        """Test that a deliverable can be linked to multiple entities."""
        conn = sample_hierarchy

        deliv_id = create_deliverable("Shared deliverable", conn=conn)
        link_deliverable("task", "task-1", deliv_id, conn=conn)
        link_deliverable("task", "task-2", deliv_id, conn=conn)
        conn.commit()

        assert len(get_deliverables("task", "task-1", conn=conn)) == 1
        assert len(get_deliverables("task", "task-2", conn=conn)) == 1


# =============================================================================
# COMMITS JUNCTION TESTS
# =============================================================================

class TestCommits:
    """Tests for commit operations."""

    def test_create_commit(self, sample_hierarchy):
        """Test creating a commit record."""
        conn = sample_hierarchy
        now = datetime.now(timezone.utc)

        commit_id = create_commit(
            commit_hash="abc123def456",
            commit_message="feat: add new feature",
            author="developer@example.com",
            committed_at=now,
            branch="main",
            conn=conn,
        )
        conn.commit()

        assert commit_id > 0

    def test_get_commit_by_hash(self, sample_hierarchy):
        """Test retrieving a commit by hash."""
        conn = sample_hierarchy
        now = datetime.now(timezone.utc)

        create_commit(
            commit_hash="abc123",
            commit_message="test commit",
            author="test@example.com",
            committed_at=now,
            conn=conn,
        )
        conn.commit()

        commit = get_commit_by_hash("abc123", conn=conn)

        assert commit is not None
        assert commit["commit_message"] == "test commit"
        assert commit["author"] == "test@example.com"

    def test_get_commit_by_hash_not_found(self, sample_hierarchy):
        """Test retrieving a non-existent commit."""
        conn = sample_hierarchy

        commit = get_commit_by_hash("nonexistent", conn=conn)
        assert commit is None

    def test_link_commit(self, sample_hierarchy):
        """Test linking a commit to an entity."""
        conn = sample_hierarchy

        commit_id = create_commit(commit_hash="xyz789", conn=conn)
        link_id = link_commit("task", "task-1", commit_id, conn=conn)
        conn.commit()

        assert link_id > 0

    def test_unlink_commit(self, sample_hierarchy):
        """Test unlinking a commit from an entity."""
        conn = sample_hierarchy

        commit_id = create_commit(commit_hash="xyz789", conn=conn)
        link_commit("task", "task-1", commit_id, conn=conn)
        conn.commit()

        result = unlink_commit("task", "task-1", commit_id, conn=conn)
        conn.commit()

        assert result is True

    def test_get_commits(self, sample_hierarchy):
        """Test getting all commits for an entity."""
        conn = sample_hierarchy
        now = datetime.now(timezone.utc)

        commit1_id = create_commit(
            commit_hash="commit1",
            commit_message="First commit",
            committed_at=now,
            conn=conn,
        )
        commit2_id = create_commit(
            commit_hash="commit2",
            commit_message="Second commit",
            committed_at=now,
            conn=conn,
        )
        link_commit("sprint", "sprint-1", commit1_id, conn=conn)
        link_commit("sprint", "sprint-1", commit2_id, conn=conn)
        conn.commit()

        commits = get_commits("sprint", "sprint-1", conn=conn)

        assert len(commits) == 2
        hashes = {c["commit_hash"] for c in commits}
        assert hashes == {"commit1", "commit2"}


# =============================================================================
# QUALITY GATE TESTS
# =============================================================================

class TestQualityGates:
    """Tests for quality gate operations."""

    def test_add_quality_gate(self, sample_hierarchy):
        """Test adding a quality gate."""
        conn = sample_hierarchy

        gate_id = add_quality_gate(
            owner_type="track",
            owner_id="track-1",
            name="code_coverage",
            threshold=80,
            blocking=True,
            description="Code coverage must be at least 80%",
            conn=conn,
        )
        conn.commit()

        assert gate_id > 0

    def test_add_quality_gate_invalid_owner(self, sample_hierarchy):
        """Test adding a quality gate to invalid owner type."""
        conn = sample_hierarchy

        with pytest.raises(ValueError, match="tracks or sprints"):
            add_quality_gate(
                owner_type="task",  # Invalid - only track/sprint allowed
                owner_id="task-1",
                name="test_gate",
                conn=conn,
            )

    def test_update_quality_gate(self, sample_hierarchy):
        """Test updating a quality gate."""
        conn = sample_hierarchy
        now = datetime.now(timezone.utc)

        gate_id = add_quality_gate(
            owner_type="sprint",
            owner_id="sprint-1",
            name="test_gate",
            status="not_run",
            conn=conn,
        )
        conn.commit()

        result = update_quality_gate(
            gate_id,
            status="passed",
            score=95,
            last_run_at=now,
            last_run_by="ci-system",
            conn=conn,
        )
        conn.commit()

        assert result is True

        gates = list_quality_gates("sprint", "sprint-1", conn=conn)
        assert len(gates) == 1
        assert gates[0]["status"] == "passed"
        assert gates[0]["score"] == 95

    def test_remove_quality_gate(self, sample_hierarchy):
        """Test removing a quality gate."""
        conn = sample_hierarchy

        gate_id = add_quality_gate(
            owner_type="track",
            owner_id="track-1",
            name="test_gate",
            conn=conn,
        )
        conn.commit()

        result = remove_quality_gate(gate_id, conn=conn)
        conn.commit()

        assert result is True
        assert len(list_quality_gates("track", "track-1", conn=conn)) == 0

    def test_list_quality_gates(self, sample_hierarchy):
        """Test listing quality gates for an entity."""
        conn = sample_hierarchy

        add_quality_gate("track", "track-1", "gate1", status="passed", conn=conn)
        add_quality_gate("track", "track-1", "gate2", status="failed", conn=conn)
        add_quality_gate("track", "track-1", "gate3", status="not_run", conn=conn)
        conn.commit()

        all_gates = list_quality_gates("track", "track-1", conn=conn)
        assert len(all_gates) == 3

        failed_gates = list_quality_gates("track", "track-1", status="failed", conn=conn)
        assert len(failed_gates) == 1
        assert failed_gates[0]["name"] == "gate2"

    def test_get_blocking_gates(self, sample_hierarchy):
        """Test getting blocking gates that haven't passed."""
        conn = sample_hierarchy

        add_quality_gate("track", "track-1", "blocking_passed", blocking=True, status="passed", conn=conn)
        add_quality_gate("track", "track-1", "blocking_failed", blocking=True, status="failed", conn=conn)
        add_quality_gate("track", "track-1", "blocking_not_run", blocking=True, status="not_run", conn=conn)
        add_quality_gate("track", "track-1", "nonblocking_failed", blocking=False, status="failed", conn=conn)
        conn.commit()

        blocking = get_blocking_gates("track", "track-1", conn=conn)

        assert len(blocking) == 2
        names = {g["name"] for g in blocking}
        assert names == {"blocking_failed", "blocking_not_run"}


# =============================================================================
# DEPENDENCY CHAIN TESTS (Recursive CTEs)
# =============================================================================

class TestDependencyChains:
    """Tests for recursive CTE dependency chain queries."""

    def test_get_dependency_chain(self, sample_hierarchy):
        """Test getting transitive dependency chain."""
        conn = sample_hierarchy

        # Create chain: task-3 -> task-2 -> task-1
        add_dependency("task", "task-3", "task", "task-2", conn=conn)
        add_dependency("task", "task-2", "task", "task-1", conn=conn)
        conn.commit()

        chain = get_dependency_chain("task", "task-3", conn=conn)

        assert len(chain) == 2
        # task-2 at depth 1, task-1 at depth 2
        depths = {(c["dependency_id"], c["depth"]) for c in chain}
        assert ("task-2", 1) in depths
        assert ("task-1", 2) in depths

    def test_get_dependency_chain_with_max_depth(self, sample_hierarchy):
        """Test dependency chain with depth limit."""
        conn = sample_hierarchy

        # Create chain: task-3 -> task-2 -> task-1
        add_dependency("task", "task-3", "task", "task-2", conn=conn)
        add_dependency("task", "task-2", "task", "task-1", conn=conn)
        conn.commit()

        chain = get_dependency_chain("task", "task-3", max_depth=1, conn=conn)

        # Only direct dependency at depth 1
        assert len(chain) == 1
        assert chain[0]["dependency_id"] == "task-2"

    def test_get_blocking_chain(self, sample_hierarchy):
        """Test getting transitive blocking chain."""
        conn = sample_hierarchy

        # task-3 blocked by task-2 blocked by task-1
        add_blocker("task", "task-2", "task", "task-3", conn=conn)
        add_blocker("task", "task-1", "task", "task-2", conn=conn)
        conn.commit()

        chain = get_blocking_chain("task", "task-3", conn=conn)

        assert len(chain) == 2
        blocker_ids = {c["blocker_id"] for c in chain}
        assert blocker_ids == {"task-1", "task-2"}

    def test_detect_circular_dependencies_none(self, sample_hierarchy):
        """Test detecting no circular dependencies."""
        conn = sample_hierarchy

        # Linear chain: task-3 -> task-2 -> task-1
        add_dependency("task", "task-3", "task", "task-2", conn=conn)
        add_dependency("task", "task-2", "task", "task-1", conn=conn)
        conn.commit()

        cycles = detect_circular_dependencies(conn=conn)
        assert len(cycles) == 0

    def test_detect_circular_dependencies_simple(self, sample_hierarchy):
        """Test detecting a simple circular dependency."""
        conn = sample_hierarchy

        # Create cycle: task-1 -> task-2 -> task-1
        add_dependency("task", "task-1", "task", "task-2", conn=conn)
        add_dependency("task", "task-2", "task", "task-1", conn=conn)
        conn.commit()

        cycles = detect_circular_dependencies(conn=conn)
        assert len(cycles) > 0

    def test_detect_circular_blockers_none(self, sample_hierarchy):
        """Test detecting no circular blockers."""
        conn = sample_hierarchy

        add_blocker("task", "task-1", "task", "task-2", conn=conn)
        add_blocker("task", "task-2", "task", "task-3", conn=conn)
        conn.commit()

        cycles = detect_circular_blockers(conn=conn)
        assert len(cycles) == 0

    def test_detect_circular_blockers_simple(self, sample_hierarchy):
        """Test detecting a simple circular blocker."""
        conn = sample_hierarchy

        # Create cycle: task-1 blocks task-2 blocks task-1
        add_blocker("task", "task-1", "task", "task-2", conn=conn)
        add_blocker("task", "task-2", "task", "task-1", conn=conn)
        conn.commit()

        cycles = detect_circular_blockers(conn=conn)
        assert len(cycles) > 0


# =============================================================================
# CROSS-ENTITY TYPE TESTS
# =============================================================================

class TestCrossEntityRelationships:
    """Tests for relationships across different entity types."""

    def test_sprint_blocks_track(self, sample_hierarchy):
        """Test sprint blocking a track."""
        conn = sample_hierarchy

        add_blocker("sprint", "sprint-1", "track", "track-2", reason="track-2 waits for sprint-1", conn=conn)
        conn.commit()

        assert is_blocked("track", "track-2", conn=conn)
        blockers = get_blockers("track", "track-2", conn=conn)
        assert len(blockers) == 1
        assert blockers[0]["blocker_type"] == "sprint"
        assert blockers[0]["blocker_id"] == "sprint-1"

    def test_track_depends_on_track(self, sample_hierarchy):
        """Test track depending on another track."""
        conn = sample_hierarchy

        add_dependency("track", "track-2", "track", "track-1", reason="track-2 builds on track-1", conn=conn)
        conn.commit()

        deps = get_dependencies("track", "track-2", conn=conn)
        assert len(deps) == 1
        assert deps[0]["dependency_id"] == "track-1"

    def test_deliverable_linked_to_track(self, sample_hierarchy):
        """Test deliverable linked to a track."""
        conn = sample_hierarchy

        deliv_id = create_deliverable("Track-level documentation", conn=conn)
        link_deliverable("track", "track-1", deliv_id, conn=conn)
        conn.commit()

        deliverables = get_deliverables("track", "track-1", conn=conn)
        assert len(deliverables) == 1
        assert deliverables[0]["description"] == "Track-level documentation"

    def test_commit_linked_to_multiple_entity_types(self, sample_hierarchy):
        """Test commit linked to sprint, track, and task."""
        conn = sample_hierarchy

        commit_id = create_commit(commit_hash="multi123", commit_message="multi-entity commit", conn=conn)
        link_commit("task", "task-1", commit_id, conn=conn)
        link_commit("sprint", "sprint-1", commit_id, conn=conn)
        link_commit("track", "track-1", commit_id, conn=conn)
        conn.commit()

        assert len(get_commits("task", "task-1", conn=conn)) == 1
        assert len(get_commits("sprint", "sprint-1", conn=conn)) == 1
        assert len(get_commits("track", "track-1", conn=conn)) == 1


# =============================================================================
# EDGE CASES AND ERROR HANDLING
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_duplicate_blocker(self, sample_hierarchy):
        """Test adding duplicate blocking relationship."""
        conn = sample_hierarchy

        add_blocker("task", "task-1", "task", "task-2", conn=conn)
        conn.commit()

        with pytest.raises(sqlite3.IntegrityError):
            add_blocker("task", "task-1", "task", "task-2", conn=conn)

    def test_duplicate_dependency(self, sample_hierarchy):
        """Test adding duplicate dependency relationship."""
        conn = sample_hierarchy

        add_dependency("task", "task-1", "task", "task-2", conn=conn)
        conn.commit()

        with pytest.raises(sqlite3.IntegrityError):
            add_dependency("task", "task-1", "task", "task-2", conn=conn)

    def test_duplicate_commit_hash(self, sample_hierarchy):
        """Test creating commit with duplicate hash."""
        conn = sample_hierarchy

        create_commit(commit_hash="unique123", conn=conn)
        conn.commit()

        with pytest.raises(sqlite3.IntegrityError):
            create_commit(commit_hash="unique123", conn=conn)

    def test_update_quality_gate_no_fields(self, sample_hierarchy):
        """Test updating quality gate with no fields raises error."""
        conn = sample_hierarchy

        gate_id = add_quality_gate("track", "track-1", "test", conn=conn)
        conn.commit()

        with pytest.raises(ValueError, match="No update fields"):
            update_quality_gate(gate_id, conn=conn)

    def test_update_quality_gate_unknown_field(self, sample_hierarchy):
        """Test updating quality gate with unknown field raises error."""
        conn = sample_hierarchy

        gate_id = add_quality_gate("track", "track-1", "test", conn=conn)
        conn.commit()

        with pytest.raises(ValueError, match="Unknown field"):
            update_quality_gate(gate_id, unknown_field="value", conn=conn)

    def test_empty_dependency_chain(self, sample_hierarchy):
        """Test getting dependency chain for entity with no dependencies."""
        conn = sample_hierarchy

        chain = get_dependency_chain("task", "task-1", conn=conn)
        assert chain == []

    def test_empty_blocking_chain(self, sample_hierarchy):
        """Test getting blocking chain for entity with no blockers."""
        conn = sample_hierarchy

        chain = get_blocking_chain("task", "task-1", conn=conn)
        assert chain == []


# =============================================================================
# DB_PATH PARAMETER TESTS
# =============================================================================

class TestDbPathParameter:
    """Tests for using db_path parameter instead of conn."""

    @pytest.fixture
    def db_with_data(self, db_path):
        """Create database with sample data."""
        conn = get_connection(db_path=db_path)
        create_schema(conn=conn)
        now = datetime.now(timezone.utc)

        create_roadmap(
            id="test-roadmap", name="Test", version="1.0.0",
            status="in_progress", created=now, conn=conn,
        )
        create_track(
            id="track-1", roadmap_id="test-roadmap", name="Track 1",
            status="in_progress", created=now, conn=conn,
        )
        create_sprint(
            id="sprint-1", track_id="track-1", roadmap_id="test-roadmap",
            name="Sprint 1", status="in_progress", created=now, conn=conn,
        )
        create_task(
            id="task-1", sprint_id="sprint-1", track_id="track-1",
            roadmap_id="test-roadmap", task_type="development",
            title="Task 1", status="in_progress", created=now, conn=conn,
        )
        create_task(
            id="task-2", sprint_id="sprint-1", track_id="track-1",
            roadmap_id="test-roadmap", task_type="development",
            title="Task 2", status="not_started", created=now, conn=conn,
        )
        conn.commit()
        return db_path

    def test_add_blocker_with_db_path(self, db_with_data):
        """add_blocker works with db_path parameter."""
        result = add_blocker("task", "task-1", "task", "task-2", db_path=db_with_data)
        assert result > 0

    def test_remove_blocker_with_db_path(self, db_with_data):
        """remove_blocker works with db_path parameter."""
        add_blocker("task", "task-1", "task", "task-2", db_path=db_with_data)
        result = remove_blocker("task", "task-1", "task", "task-2", db_path=db_with_data)
        assert result is True

    def test_get_blockers_with_db_path(self, db_with_data):
        """get_blockers works with db_path parameter."""
        add_blocker("task", "task-1", "task", "task-2", db_path=db_with_data)
        blockers = get_blockers("task", "task-2", db_path=db_with_data)
        assert len(blockers) == 1

    def test_get_blocked_by_with_db_path(self, db_with_data):
        """get_blocked_by works with db_path parameter."""
        add_blocker("task", "task-1", "task", "task-2", db_path=db_with_data)
        blocked = get_blocked_by("task", "task-1", db_path=db_with_data)
        assert len(blocked) == 1

    def test_is_blocked_with_db_path(self, db_with_data):
        """is_blocked works with db_path parameter."""
        assert is_blocked("task", "task-2", db_path=db_with_data) is False
        add_blocker("task", "task-1", "task", "task-2", db_path=db_with_data)
        assert is_blocked("task", "task-2", db_path=db_with_data) is True

    def test_add_dependency_with_db_path(self, db_with_data):
        """add_dependency works with db_path parameter."""
        result = add_dependency("task", "task-2", "task", "task-1", db_path=db_with_data)
        assert result > 0

    def test_remove_dependency_with_db_path(self, db_with_data):
        """remove_dependency works with db_path parameter."""
        add_dependency("task", "task-2", "task", "task-1", db_path=db_with_data)
        result = remove_dependency("task", "task-2", "task", "task-1", db_path=db_with_data)
        assert result is True

    def test_get_dependencies_with_db_path(self, db_with_data):
        """get_dependencies works with db_path parameter."""
        add_dependency("task", "task-2", "task", "task-1", db_path=db_with_data)
        deps = get_dependencies("task", "task-2", db_path=db_with_data)
        assert len(deps) == 1

    def test_get_dependents_with_db_path(self, db_with_data):
        """get_dependents works with db_path parameter."""
        add_dependency("task", "task-2", "task", "task-1", db_path=db_with_data)
        dependents = get_dependents("task", "task-1", db_path=db_with_data)
        assert len(dependents) == 1

    def test_create_deliverable_with_db_path(self, db_with_data):
        """create_deliverable works with db_path parameter."""
        result = create_deliverable("Test deliverable", db_path=db_with_data)
        assert result > 0

    def test_link_deliverable_with_db_path(self, db_with_data):
        """link_deliverable works with db_path parameter."""
        deliv_id = create_deliverable("Test", db_path=db_with_data)
        result = link_deliverable("task", "task-1", deliv_id, db_path=db_with_data)
        assert result > 0

    def test_unlink_deliverable_with_db_path(self, db_with_data):
        """unlink_deliverable works with db_path parameter."""
        deliv_id = create_deliverable("Test", db_path=db_with_data)
        link_deliverable("task", "task-1", deliv_id, db_path=db_with_data)
        result = unlink_deliverable("task", "task-1", deliv_id, db_path=db_with_data)
        assert result is True

    def test_get_deliverables_with_db_path(self, db_with_data):
        """get_deliverables works with db_path parameter."""
        deliv_id = create_deliverable("Test", db_path=db_with_data)
        link_deliverable("task", "task-1", deliv_id, db_path=db_with_data)
        deliverables = get_deliverables("task", "task-1", db_path=db_with_data)
        assert len(deliverables) == 1

    def test_create_commit_with_db_path(self, db_with_data):
        """create_commit works with db_path parameter."""
        result = create_commit(commit_hash="abc123", db_path=db_with_data)
        assert result > 0

    def test_get_commit_by_hash_with_db_path(self, db_with_data):
        """get_commit_by_hash works with db_path parameter."""
        create_commit(commit_hash="abc123", db_path=db_with_data)
        commit = get_commit_by_hash("abc123", db_path=db_with_data)
        assert commit is not None

    def test_link_commit_with_db_path(self, db_with_data):
        """link_commit works with db_path parameter."""
        commit_id = create_commit(commit_hash="abc123", db_path=db_with_data)
        result = link_commit("task", "task-1", commit_id, db_path=db_with_data)
        assert result > 0

    def test_unlink_commit_with_db_path(self, db_with_data):
        """unlink_commit works with db_path parameter."""
        commit_id = create_commit(commit_hash="abc123", db_path=db_with_data)
        link_commit("task", "task-1", commit_id, db_path=db_with_data)
        result = unlink_commit("task", "task-1", commit_id, db_path=db_with_data)
        assert result is True

    def test_get_commits_with_db_path(self, db_with_data):
        """get_commits works with db_path parameter."""
        commit_id = create_commit(commit_hash="abc123", db_path=db_with_data)
        link_commit("task", "task-1", commit_id, db_path=db_with_data)
        commits = get_commits("task", "task-1", db_path=db_with_data)
        assert len(commits) == 1

    def test_add_quality_gate_with_db_path(self, db_with_data):
        """add_quality_gate works with db_path parameter."""
        result = add_quality_gate("track", "track-1", "test_gate", db_path=db_with_data)
        assert result > 0

    def test_update_quality_gate_with_db_path(self, db_with_data):
        """update_quality_gate works with db_path parameter."""
        gate_id = add_quality_gate("track", "track-1", "test", db_path=db_with_data)
        result = update_quality_gate(gate_id, status="passed", db_path=db_with_data)
        assert result is True

    def test_remove_quality_gate_with_db_path(self, db_with_data):
        """remove_quality_gate works with db_path parameter."""
        gate_id = add_quality_gate("track", "track-1", "test", db_path=db_with_data)
        result = remove_quality_gate(gate_id, db_path=db_with_data)
        assert result is True

    def test_list_quality_gates_with_db_path(self, db_with_data):
        """list_quality_gates works with db_path parameter."""
        add_quality_gate("track", "track-1", "test", db_path=db_with_data)
        gates = list_quality_gates("track", "track-1", db_path=db_with_data)
        assert len(gates) == 1

    def test_get_blocking_gates_with_db_path(self, db_with_data):
        """get_blocking_gates works with db_path parameter."""
        add_quality_gate("track", "track-1", "test", blocking=True, db_path=db_with_data)
        gates = get_blocking_gates("track", "track-1", db_path=db_with_data)
        assert len(gates) == 1

    def test_get_dependency_chain_with_db_path(self, db_with_data):
        """get_dependency_chain works with db_path parameter."""
        add_dependency("task", "task-2", "task", "task-1", db_path=db_with_data)
        chain = get_dependency_chain("task", "task-2", db_path=db_with_data)
        assert len(chain) == 1

    def test_get_blocking_chain_with_db_path(self, db_with_data):
        """get_blocking_chain works with db_path parameter."""
        add_blocker("task", "task-1", "task", "task-2", db_path=db_with_data)
        chain = get_blocking_chain("task", "task-2", db_path=db_with_data)
        assert len(chain) == 1

    def test_detect_circular_dependencies_with_db_path(self, db_with_data):
        """detect_circular_dependencies works with db_path parameter."""
        cycles = detect_circular_dependencies(db_path=db_with_data)
        assert isinstance(cycles, list)

    def test_detect_circular_blockers_with_db_path(self, db_with_data):
        """detect_circular_blockers works with db_path parameter."""
        cycles = detect_circular_blockers(db_path=db_with_data)
        assert isinstance(cycles, list)


class TestQualityGateUpdateFields:
    """Tests for quality gate update with different field types."""

    def test_update_quality_gate_with_metadata(self, sample_hierarchy):
        """update_quality_gate handles metadata JSON field."""
        conn = sample_hierarchy

        gate_id = add_quality_gate("track", "track-1", "test", conn=conn)
        conn.commit()

        result = update_quality_gate(
            gate_id,
            metadata={"custom": "data", "count": 42},
            conn=conn,
        )
        conn.commit()

        assert result is True

        # Verify metadata was stored
        gates = list_quality_gates("track", "track-1", conn=conn)
        assert len(gates) == 1
        # Metadata is stored as JSON, verify it exists
        row = conn.execute(
            "SELECT metadata FROM quality_gates WHERE id = ?", (gate_id,)
        ).fetchone()
        assert row is not None

    def test_update_quality_gate_with_blocking(self, sample_hierarchy):
        """update_quality_gate handles blocking boolean field."""
        conn = sample_hierarchy

        gate_id = add_quality_gate("track", "track-1", "test", blocking=False, conn=conn)
        conn.commit()

        result = update_quality_gate(gate_id, blocking=True, conn=conn)
        conn.commit()

        assert result is True

        # Verify blocking was updated
        blocking_gates = get_blocking_gates("track", "track-1", conn=conn)
        assert len(blocking_gates) == 1
