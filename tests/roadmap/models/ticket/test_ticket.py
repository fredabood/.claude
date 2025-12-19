"""
Tests for Layer 1 Ticket class.

Tests cover:
- GitCommit class
- Ticket creation and defaults
- Lifecycle transitions (start, complete, pause, cancel, resume)
- Hierarchy computed properties
- Convenience accessors
- Progress shortcuts
- Commit and requirement management
- Validation rules
"""

import pytest
from datetime import datetime, timezone, timedelta
from vibey.roadmap.models.ticket import (
    Ticket,
    GitCommit,
    Criterion,
    CompletableTarget,
    FileExistsTarget,
    TestPassesTarget,
    ManualTarget,
    TicketStatus,
    Priority,
    Requirement,
    CriterionTemplate,
    CriterionTargetType,
    InheritMode,
    EnforcementMode,
)
from vibey.roadmap.models.ticket.ticket import parse_task_markers


# =============================================================================
# GITCOMMIT TESTS
# =============================================================================


class TestGitCommit:
    """Tests for GitCommit class."""

    def test_basic_commit(self):
        """Test basic commit creation."""
        commit = GitCommit(
            sha="abc123def456",
            message="feat: add new feature",
            date=datetime.now(timezone.utc),
            author="developer@example.com",
        )
        assert commit.sha == "abc123def456"
        assert commit.message == "feat: add new feature"
        assert commit.author == "developer@example.com"

    def test_commit_with_file_changes(self):
        """Test commit with file change tracking."""
        commit = GitCommit(
            sha="abc123def456",
            message="refactor: update models",
            date=datetime.now(timezone.utc),
            author="developer@example.com",
            files_added=["src/new_file.py"],
            files_modified=["src/existing.py", "src/another.py"],
            files_deleted=["src/old_file.py"],
        )
        assert commit.files_added == ["src/new_file.py"]
        assert commit.files_modified == ["src/existing.py", "src/another.py"]
        assert commit.files_deleted == ["src/old_file.py"]
        assert set(commit.all_changed_files) == {
            "src/new_file.py",
            "src/existing.py",
            "src/another.py",
            "src/old_file.py",
        }

    def test_commit_with_platform(self):
        """Test commit with platform tracking."""
        commit = GitCommit(
            sha="abc123",
            message="fix: bug fix",
            date=datetime.now(timezone.utc),
            author="dev@example.com",
            platform="claude-code",
            submitted_at=datetime.now(timezone.utc),
        )
        assert commit.platform == "claude-code"
        assert commit.submitted_at is not None

    def test_commit_with_artifact_links(self):
        """Test commit with artifact tracking."""
        commit = GitCommit(
            sha="def456",
            message="docs: update docs",
            date=datetime.now(timezone.utc),
            author="dev@example.com",
            creates_artifacts=["art-new-doc"],
            modifies_artifacts=["art-readme"],
            deletes_artifacts=["art-old-doc"],
        )
        assert set(commit.all_affected_artifacts) == {
            "art-new-doc",
            "art-readme",
            "art-old-doc",
        }

    def test_commit_completes_tickets(self):
        """Test commit with ticket completion markers."""
        commit = GitCommit(
            sha="ghi789",
            message="feat: implement feature (closes #123)",
            date=datetime.now(timezone.utc),
            author="dev@example.com",
            completes_tickets=["task-123", "task-124"],
        )
        assert commit.completes_tickets == ["task-123", "task-124"]

    def test_commit_references_tickets(self):
        """Test commit with ticket reference markers."""
        commit = GitCommit(
            sha="jkl012",
            message="feat: progress on feature",
            date=datetime.now(timezone.utc),
            author="dev@example.com",
            references_tickets=["01TASK_A", "01TASK_B"],
        )
        assert commit.references_tickets == ["01TASK_A", "01TASK_B"]

    def test_commit_all_referenced_tickets(self):
        """Test all_referenced_tickets combines both fields."""
        commit = GitCommit(
            sha="mno345",
            message="feat: complete feature",
            date=datetime.now(timezone.utc),
            author="dev@example.com",
            references_tickets=["01TASK_A", "01TASK_B"],
            completes_tickets=["01TASK_C"],
        )
        assert set(commit.all_referenced_tickets) == {"01TASK_A", "01TASK_B", "01TASK_C"}

    def test_commit_all_referenced_tickets_deduplicates(self):
        """Test all_referenced_tickets removes duplicates."""
        commit = GitCommit(
            sha="pqr678",
            message="feat: work on task",
            date=datetime.now(timezone.utc),
            author="dev@example.com",
            references_tickets=["01TASK_A", "01TASK_B"],
            completes_tickets=["01TASK_A"],  # Duplicate
        )
        all_refs = commit.all_referenced_tickets
        assert len(all_refs) == 2
        assert set(all_refs) == {"01TASK_A", "01TASK_B"}


# =============================================================================
# PARSE_TASK_MARKERS TESTS
# =============================================================================


class TestParseTaskMarkers:
    """Tests for parse_task_markers function."""

    def test_parse_single_task_marker(self):
        """Test parsing a single Task: marker."""
        message = """feat: add new feature

Task: 01TASK_A
"""
        references, completes = parse_task_markers(message)
        assert references == ["01TASK_A"]
        assert completes == []

    def test_parse_comma_separated_task_markers(self):
        """Test parsing comma-separated Task: markers."""
        message = """feat: add new feature

Task: 01TASK_A, 01TASK_B, 01TASK_C
"""
        references, completes = parse_task_markers(message)
        assert references == ["01TASK_A", "01TASK_B", "01TASK_C"]
        assert completes == []

    def test_parse_single_completes_marker(self):
        """Test parsing a single Completes: marker."""
        message = """feat: complete feature

Completes: 01TASK_A
"""
        references, completes = parse_task_markers(message)
        assert references == []
        assert completes == ["01TASK_A"]

    def test_parse_both_task_and_completes(self):
        """Test parsing both Task: and Completes: markers."""
        message = """feat: complete feature

Task: 01TASK_A
Completes: 01TASK_B
"""
        references, completes = parse_task_markers(message)
        assert references == ["01TASK_A"]
        assert completes == ["01TASK_B"]

    def test_parse_multiple_task_lines(self):
        """Test parsing multiple Task: lines."""
        message = """feat: work on multiple tasks

Task: 01TASK_A
Task: 01TASK_B
"""
        references, completes = parse_task_markers(message)
        assert references == ["01TASK_A", "01TASK_B"]
        assert completes == []

    def test_parse_empty_message(self):
        """Test parsing empty message returns empty lists."""
        references, completes = parse_task_markers("")
        assert references == []
        assert completes == []

    def test_parse_message_without_markers(self):
        """Test parsing message without markers returns empty lists."""
        message = """feat: add new feature

This is a commit message without any markers.
"""
        references, completes = parse_task_markers(message)
        assert references == []
        assert completes == []

    def test_parse_whitespace_handling(self):
        """Test that whitespace is properly stripped."""
        message = """feat: add feature

  Task:   01TASK_A  ,  01TASK_B
  Completes:   01TASK_C
"""
        references, completes = parse_task_markers(message)
        assert references == ["01TASK_A", "01TASK_B"]
        assert completes == ["01TASK_C"]

    def test_parse_empty_task_line(self):
        """Test that empty Task: line is handled."""
        message = """feat: add feature

Task:
Completes: 01TASK_A
"""
        references, completes = parse_task_markers(message)
        assert references == []
        assert completes == ["01TASK_A"]

    def test_parse_comma_separated_completes(self):
        """Test parsing comma-separated Completes: markers."""
        message = """feat: complete multiple tasks

Completes: 01TASK_A, 01TASK_B
"""
        references, completes = parse_task_markers(message)
        assert references == []
        assert completes == ["01TASK_A", "01TASK_B"]

    def test_parse_ulid_format_ids(self):
        """Test parsing ULID format ticket IDs."""
        message = """feat: work on task

Task: 01KCQETNJKGDH3N4RC7J3G1EFP
Completes: 01KCMTJQ3JRRW6CZFC4E63W8D6
"""
        references, completes = parse_task_markers(message)
        assert references == ["01KCQETNJKGDH3N4RC7J3G1EFP"]
        assert completes == ["01KCMTJQ3JRRW6CZFC4E63W8D6"]


# =============================================================================
# GITCOMMIT FROM_GIT TESTS
# =============================================================================


class TestGitCommitFromGit:
    """Tests for GitCommit.from_git() factory method."""

    def test_from_git_basic(self):
        """Test from_git creates commit with basic fields."""
        commit = GitCommit.from_git(
            sha="abc123def456",
            message="feat: add new feature",
            date=datetime.now(timezone.utc),
            author="developer@example.com",
        )
        assert commit.sha == "abc123def456"
        assert commit.message == "feat: add new feature"
        assert commit.author == "developer@example.com"
        assert commit.submitted_at is not None

    def test_from_git_parses_task_markers(self):
        """Test from_git parses Task: markers."""
        message = """feat: add new feature

Task: 01TASK_A, 01TASK_B
"""
        commit = GitCommit.from_git(
            sha="abc123",
            message=message,
            date=datetime.now(timezone.utc),
            author="dev@example.com",
        )
        assert commit.references_tickets == ["01TASK_A", "01TASK_B"]

    def test_from_git_parses_completes_markers(self):
        """Test from_git parses Completes: markers."""
        message = """feat: complete feature

Completes: 01TASK_A
"""
        commit = GitCommit.from_git(
            sha="def456",
            message=message,
            date=datetime.now(timezone.utc),
            author="dev@example.com",
        )
        assert commit.completes_tickets == ["01TASK_A"]

    def test_from_git_parses_both_markers(self):
        """Test from_git parses both Task: and Completes: markers."""
        message = """feat: progress and complete

Task: 01TASK_A
Completes: 01TASK_B
"""
        commit = GitCommit.from_git(
            sha="ghi789",
            message=message,
            date=datetime.now(timezone.utc),
            author="dev@example.com",
        )
        assert commit.references_tickets == ["01TASK_A"]
        assert commit.completes_tickets == ["01TASK_B"]

    def test_from_git_with_platform(self):
        """Test from_git with platform parameter."""
        commit = GitCommit.from_git(
            sha="jkl012",
            message="feat: add feature",
            date=datetime.now(timezone.utc),
            author="dev@example.com",
            platform="claude-code",
        )
        assert commit.platform == "claude-code"

    def test_from_git_with_file_changes(self):
        """Test from_git with file change lists."""
        commit = GitCommit.from_git(
            sha="mno345",
            message="refactor: update models",
            date=datetime.now(timezone.utc),
            author="dev@example.com",
            files_added=["src/new_file.py"],
            files_modified=["src/existing.py"],
            files_deleted=["src/old_file.py"],
        )
        assert commit.files_added == ["src/new_file.py"]
        assert commit.files_modified == ["src/existing.py"]
        assert commit.files_deleted == ["src/old_file.py"]

    def test_from_git_empty_file_lists_default(self):
        """Test from_git defaults file lists to empty."""
        commit = GitCommit.from_git(
            sha="pqr678",
            message="docs: update readme",
            date=datetime.now(timezone.utc),
            author="dev@example.com",
        )
        assert commit.files_added == []
        assert commit.files_modified == []
        assert commit.files_deleted == []


# =============================================================================
# TICKET CREATION TESTS
# =============================================================================


class TestTicketCreation:
    """Tests for Ticket creation and defaults."""

    def test_minimal_ticket(self):
        """Test creating a ticket with minimal fields."""
        ticket = Ticket(id="task-001", name="Test Task")
        assert ticket.id == "task-001"
        assert ticket.name == "Test Task"
        assert ticket.status == TicketStatus.NOT_STARTED
        assert ticket.priority == Priority.MEDIUM
        assert ticket.parent_ref is None
        assert ticket.assigned_agents == []
        assert ticket.commits == []
        assert ticket.requirements_local == []
        assert ticket.criteria == []

    def test_ticket_with_all_fields(self):
        """Test creating a ticket with all fields."""
        created = datetime.now(timezone.utc) - timedelta(hours=2)
        started = datetime.now(timezone.utc) - timedelta(hours=1)

        ticket = Ticket(
            id="task-002",
            name="Full Task",
            description="A comprehensive task",
            parent_ref="sprint-001",
            status=TicketStatus.IN_PROGRESS,
            created_at=created,
            started_at=started,
            assigned_agents=["agent-1", "agent-2"],
            priority=Priority.CRITICAL,
            estimated_duration="2 days",
            metadata={"custom_field": "value"},
        )

        assert ticket.id == "task-002"
        assert ticket.description == "A comprehensive task"
        assert ticket.parent_ref == "sprint-001"
        assert ticket.status == TicketStatus.IN_PROGRESS
        assert ticket.started_at == started
        assert ticket.assigned_agents == ["agent-1", "agent-2"]
        assert ticket.priority == Priority.CRITICAL
        assert ticket.estimated_duration == "2 days"
        assert ticket.metadata == {"custom_field": "value"}

    def test_ticket_timestamps_auto_generated(self):
        """Test that timestamps are auto-generated."""
        before = datetime.now(timezone.utc)
        ticket = Ticket(id="task-003", name="Timestamp Test")
        after = datetime.now(timezone.utc)

        assert before <= ticket.created_at <= after
        assert before <= ticket.updated_at <= after


# =============================================================================
# LIFECYCLE TRANSITION TESTS
# =============================================================================


class TestLifecycleTransitions:
    """Tests for lifecycle transition methods."""

    def test_start_ticket(self):
        """Test starting a ticket."""
        ticket = Ticket(id="task-001", name="Test")
        started = ticket.start()

        assert started.status == TicketStatus.IN_PROGRESS
        assert started.started_at is not None
        assert started.id == "task-001"  # Unchanged

    def test_start_blocked_ticket_fails(self):
        """Test that starting a blocked ticket raises error."""
        # Create ticket with unsatisfied dependency criterion
        # The target has current_status=None, so is_satisfied returns False
        ticket = Ticket(
            id="task-001",
            name="Blocked Task",
            criteria=[
                Criterion(
                    id="dep-1",
                    description="Depends on task-000",
                    target=CompletableTarget(
                        completable_id="task-000",
                        required_status=TicketStatus.COMPLETED,
                        current_status=None,  # Not yet checked, so unsatisfied
                    ),
                    blocks_transition_to=TicketStatus.IN_PROGRESS,
                )
            ],
        )

        with pytest.raises(ValueError, match="Cannot start"):
            ticket.start()

    def test_complete_ticket(self):
        """Test completing a ticket."""
        created = datetime.now(timezone.utc) - timedelta(hours=2)
        started = datetime.now(timezone.utc) - timedelta(hours=1)
        ticket = Ticket(
            id="task-001",
            name="Test",
            status=TicketStatus.IN_PROGRESS,
            created_at=created,
            started_at=started,
        )
        completed = ticket.complete()

        assert completed.status == TicketStatus.COMPLETED
        assert completed.completed_at is not None

    def test_complete_with_unsatisfied_criteria_fails(self):
        """Test that completing with unsatisfied criteria raises error."""
        created = datetime.now(timezone.utc) - timedelta(hours=2)
        started = datetime.now(timezone.utc) - timedelta(hours=1)
        ticket = Ticket(
            id="task-001",
            name="Test",
            status=TicketStatus.IN_PROGRESS,
            created_at=created,
            started_at=started,
            criteria=[
                Criterion(
                    id="crit-1",
                    description="Must be done",
                    target=FileExistsTarget(paths=["test.py"]),
                    blocks_transition_to=TicketStatus.COMPLETED,
                    # Target's is_satisfied returns False since file doesn't exist
                )
            ],
        )

        with pytest.raises(ValueError, match="Cannot complete"):
            ticket.complete()

    def test_pause_ticket(self):
        """Test pausing a ticket."""
        created = datetime.now(timezone.utc) - timedelta(hours=2)
        started = datetime.now(timezone.utc) - timedelta(hours=1)
        ticket = Ticket(
            id="task-001",
            name="Test",
            status=TicketStatus.IN_PROGRESS,
            created_at=created,
            started_at=started,
        )
        paused = ticket.pause()

        assert paused.status == TicketStatus.PAUSED

    def test_pause_terminal_ticket_fails(self):
        """Test that pausing a terminal ticket raises error."""
        # WONT_DO is a terminal status (not COMPLETED)
        ticket = Ticket(id="task-001", name="Test")
        cancelled = ticket.cancel()  # Sets status to WONT_DO (terminal)

        with pytest.raises(ValueError, match="terminal"):
            cancelled.pause()

    def test_cancel_ticket(self):
        """Test cancelling a ticket."""
        ticket = Ticket(id="task-001", name="Test")
        cancelled = ticket.cancel()

        assert cancelled.status == TicketStatus.WONT_DO

    def test_resume_paused_ticket(self):
        """Test resuming a paused ticket."""
        created = datetime.now(timezone.utc) - timedelta(hours=2)
        started = datetime.now(timezone.utc) - timedelta(hours=1)
        ticket = Ticket(
            id="task-001",
            name="Test",
            status=TicketStatus.IN_PROGRESS,
            created_at=created,
            started_at=started,
        )
        paused = ticket.pause()
        resumed = paused.resume()

        assert resumed.status == TicketStatus.IN_PROGRESS

    def test_resume_non_paused_ticket_fails(self):
        """Test that resuming a non-paused ticket raises error."""
        ticket = Ticket(id="task-001", name="Test")

        with pytest.raises(ValueError, match="not paused"):
            ticket.resume()


# =============================================================================
# HIERARCHY PROPERTY TESTS
# =============================================================================


class TestHierarchyProperties:
    """Tests for hierarchy computed properties."""

    def test_is_blocked_when_dependencies_not_met(self):
        """Test is_blocked is True when dependencies not satisfied."""
        ticket = Ticket(
            id="task-001",
            name="Blocked Task",
            criteria=[
                Criterion(
                    id="dep-1",
                    description="Depends on task-000",
                    target=CompletableTarget(
                        completable_id="task-000",
                        required_status=TicketStatus.COMPLETED,
                        current_status=TicketStatus.IN_PROGRESS,  # Not yet completed
                    ),
                    blocks_transition_to=TicketStatus.IN_PROGRESS,
                )
            ],
        )
        assert ticket.is_blocked is True

    def test_is_blocked_false_when_dependencies_met(self):
        """Test is_blocked is False when dependencies satisfied."""
        ticket = Ticket(
            id="task-001",
            name="Ready Task",
            criteria=[
                Criterion(
                    id="dep-1",
                    description="Depends on task-000",
                    target=CompletableTarget(
                        completable_id="task-000",
                        required_status=TicketStatus.COMPLETED,
                        current_status=TicketStatus.COMPLETED,  # Matches required
                    ),
                    blocks_transition_to=TicketStatus.IN_PROGRESS,
                )
            ],
        )
        assert ticket.is_blocked is False

    def test_is_parent_true_with_children(self):
        """Test is_parent is True when has child criteria."""
        ticket = Ticket(
            id="sprint-001",
            name="Sprint",
            criteria=[
                Criterion(
                    id="child-1",
                    description="Child task",
                    target=CompletableTarget(
                        completable_id="task-001",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                )
            ],
        )
        assert ticket.is_parent is True

    def test_is_parent_false_without_children(self):
        """Test is_parent is False when no child criteria."""
        ticket = Ticket(id="task-001", name="Leaf Task")
        assert ticket.is_parent is False

    def test_is_child_true_with_parent_ref(self):
        """Test is_child is True when parent_ref set."""
        ticket = Ticket(
            id="task-001",
            name="Child Task",
            parent_ref="sprint-001",
        )
        assert ticket.is_child is True

    def test_is_child_false_without_parent_ref(self):
        """Test is_child is False when no parent_ref."""
        ticket = Ticket(id="roadmap-001", name="Root")
        assert ticket.is_child is False

    def test_is_ultimate_parent(self):
        """Test is_ultimate_parent (root ticket)."""
        ticket = Ticket(
            id="roadmap-001",
            name="Roadmap",
            criteria=[
                Criterion(
                    id="child-1",
                    description="Track",
                    target=CompletableTarget(
                        completable_id="track-001",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                )
            ],
        )
        assert ticket.is_ultimate_parent is True
        assert ticket.is_ultimate_child is False

    def test_is_ultimate_child(self):
        """Test is_ultimate_child (leaf ticket)."""
        ticket = Ticket(
            id="task-001",
            name="Task",
            parent_ref="sprint-001",
        )
        assert ticket.is_ultimate_child is True
        assert ticket.is_ultimate_parent is False

    def test_is_intermediate(self):
        """Test is_intermediate (has both parent and children)."""
        ticket = Ticket(
            id="sprint-001",
            name="Sprint",
            parent_ref="track-001",
            criteria=[
                Criterion(
                    id="child-1",
                    description="Task",
                    target=CompletableTarget(
                        completable_id="task-001",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                )
            ],
        )
        assert ticket.is_intermediate is True
        assert ticket.is_parent is True
        assert ticket.is_child is True


# =============================================================================
# CONVENIENCE ACCESSOR TESTS
# =============================================================================


class TestConvenienceAccessors:
    """Tests for convenience accessor properties."""

    def test_deliverables_filter(self):
        """Test deliverables returns FileExistsTarget criteria."""
        ticket = Ticket(
            id="task-001",
            name="Task",
            criteria=[
                Criterion(
                    id="file-1",
                    description="Create file",
                    target=FileExistsTarget(paths=["src/main.py"]),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="test-1",
                    description="Pass tests",
                    target=TestPassesTarget(test_command="pytest"),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )

        deliverables = ticket.deliverables
        assert len(deliverables) == 1
        assert deliverables[0].id == "file-1"

    def test_tests_filter(self):
        """Test tests returns TestPassesTarget criteria."""
        ticket = Ticket(
            id="task-001",
            name="Task",
            criteria=[
                Criterion(
                    id="test-1",
                    description="Unit tests",
                    target=TestPassesTarget(test_command="pytest unit/"),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="test-2",
                    description="Integration tests",
                    target=TestPassesTarget(test_command="pytest integration/"),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="file-1",
                    description="Create file",
                    target=FileExistsTarget(paths=["src/main.py"]),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )

        tests = ticket.tests
        assert len(tests) == 2
        assert {t.id for t in tests} == {"test-1", "test-2"}

    def test_subtasks_filter(self):
        """Test subtasks returns CompletableTarget with COMPLETED blocking."""
        ticket = Ticket(
            id="sprint-001",
            name="Sprint",
            criteria=[
                Criterion(
                    id="subtask-1",
                    description="Task 1",
                    target=CompletableTarget(
                        completable_id="task-001",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="dep-1",
                    description="Dependency",
                    target=CompletableTarget(
                        completable_id="task-000",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.IN_PROGRESS,  # Dependency!
                ),
            ],
        )

        subtasks = ticket.subtasks
        assert len(subtasks) == 1
        assert subtasks[0].id == "subtask-1"

    def test_dependencies_filter(self):
        """Test dependencies returns CompletableTarget with IN_PROGRESS blocking."""
        ticket = Ticket(
            id="task-002",
            name="Task",
            criteria=[
                Criterion(
                    id="dep-1",
                    description="Must wait for task-001",
                    target=CompletableTarget(
                        completable_id="task-001",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.IN_PROGRESS,
                ),
                Criterion(
                    id="subtask-1",
                    description="Subtask",
                    target=CompletableTarget(
                        completable_id="task-002a",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,  # Not a dependency
                ),
            ],
        )

        deps = ticket.dependencies
        assert len(deps) == 1
        assert deps[0].id == "dep-1"

    def test_manual_checks_filter(self):
        """Test manual_checks returns ManualTarget criteria."""
        ticket = Ticket(
            id="task-001",
            name="Task",
            criteria=[
                Criterion(
                    id="review-1",
                    description="Code review",
                    target=ManualTarget(
                        assessor="senior-engineer",
                        instructions="Review for quality",
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="file-1",
                    description="Create file",
                    target=FileExistsTarget(paths=["src/main.py"]),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )

        checks = ticket.manual_checks
        assert len(checks) == 1
        assert checks[0].id == "review-1"

    def test_production_gates_filter(self):
        """Test production_gates returns PRODUCTION_READY blocking criteria."""
        ticket = Ticket(
            id="sprint-001",
            name="Sprint",
            criteria=[
                Criterion(
                    id="completion-1",
                    description="Tasks complete",
                    target=CompletableTarget(
                        completable_id="task-001",
                        required_status=TicketStatus.COMPLETED,
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="deploy-1",
                    description="Deploy gate",
                    target=ManualTarget(
                        assessor="ops-team",
                        instructions="Verify deployment ready",
                    ),
                    blocks_transition_to=TicketStatus.PRODUCTION_READY,
                ),
            ],
        )

        gates = ticket.production_gates
        assert len(gates) == 1
        assert gates[0].id == "deploy-1"


# =============================================================================
# PROGRESS SHORTCUT TESTS
# =============================================================================


class TestProgressShortcuts:
    """Tests for progress shortcut properties."""

    def test_start_progress(self):
        """Test start_progress shows progress toward IN_PROGRESS."""
        ticket = Ticket(
            id="task-001",
            name="Task",
            criteria=[
                Criterion(
                    id="dep-1",
                    description="Dependency",
                    target=CompletableTarget(
                        completable_id="task-000",
                        required_status=TicketStatus.COMPLETED,
                        current_status=TicketStatus.COMPLETED,  # Satisfied
                    ),
                    blocks_transition_to=TicketStatus.IN_PROGRESS,
                ),
                Criterion(
                    id="dep-2",
                    description="Dependency 2",
                    target=CompletableTarget(
                        completable_id="task-000b",
                        required_status=TicketStatus.COMPLETED,
                        current_status=TicketStatus.IN_PROGRESS,  # Not satisfied
                    ),
                    blocks_transition_to=TicketStatus.IN_PROGRESS,
                ),
            ],
        )

        progress = ticket.start_progress
        assert progress.total == 2
        assert progress.completed == 1
        assert progress.completion_percent == 50

    def test_completion_progress(self):
        """Test completion_progress shows progress toward COMPLETED."""
        ticket = Ticket(
            id="task-001",
            name="Task",
            criteria=[
                Criterion(
                    id="crit-1",
                    description="Criteria 1",
                    target=CompletableTarget(
                        completable_id="subtask-1",
                        required_status=TicketStatus.COMPLETED,
                        current_status=TicketStatus.COMPLETED,  # Satisfied
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="crit-2",
                    description="Criteria 2",
                    target=CompletableTarget(
                        completable_id="subtask-2",
                        required_status=TicketStatus.COMPLETED,
                        current_status=TicketStatus.COMPLETED,  # Satisfied
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
                Criterion(
                    id="crit-3",
                    description="Criteria 3",
                    target=CompletableTarget(
                        completable_id="subtask-3",
                        required_status=TicketStatus.COMPLETED,
                        current_status=TicketStatus.NOT_STARTED,  # Not satisfied
                    ),
                    blocks_transition_to=TicketStatus.COMPLETED,
                ),
            ],
        )

        progress = ticket.completion_progress
        assert progress.total == 3
        assert progress.completed == 2
        assert int(progress.completion_percent) == 66  # 2/3 = 66.7, truncated

    def test_deploy_progress(self):
        """Test deploy_progress shows progress toward PRODUCTION_READY."""
        ticket = Ticket(
            id="sprint-001",
            name="Sprint",
            criteria=[
                Criterion(
                    id="gate-1",
                    description="Gate 1",
                    target=ManualTarget(assessor="ops", instructions="Check"),
                    blocks_transition_to=TicketStatus.PRODUCTION_READY,
                    # ManualTarget.is_satisfied() returns False until approved
                ),
            ],
        )

        progress = ticket.deploy_progress
        assert progress.total == 1
        assert progress.completed == 0
        assert progress.completion_percent == 0


# =============================================================================
# COMMIT MANAGEMENT TESTS
# =============================================================================


class TestCommitManagement:
    """Tests for commit management methods."""

    def test_add_commit(self):
        """Test adding a commit to a ticket."""
        ticket = Ticket(id="task-001", name="Task")
        commit = GitCommit(
            sha="abc123",
            message="feat: add feature",
            date=datetime.now(timezone.utc),
            author="dev@example.com",
        )

        updated = ticket.add_commit(commit)

        assert len(updated.commits) == 1
        assert updated.commits[0].sha == "abc123"
        assert len(ticket.commits) == 0  # Original unchanged

    def test_add_multiple_commits(self):
        """Test adding multiple commits."""
        ticket = Ticket(id="task-001", name="Task")
        commit1 = GitCommit(
            sha="abc123",
            message="feat: add feature",
            date=datetime.now(timezone.utc),
            author="dev@example.com",
        )
        commit2 = GitCommit(
            sha="def456",
            message="fix: bug fix",
            date=datetime.now(timezone.utc),
            author="dev@example.com",
        )

        updated = ticket.add_commit(commit1).add_commit(commit2)

        assert len(updated.commits) == 2
        assert updated.commits[0].sha == "abc123"
        assert updated.commits[1].sha == "def456"


# =============================================================================
# REQUIREMENT MANAGEMENT TESTS
# =============================================================================


class TestRequirementManagement:
    """Tests for requirement management methods."""

    def test_add_requirement(self):
        """Test adding a requirement to a ticket."""
        ticket = Ticket(id="sprint-001", name="Sprint")
        requirement = Requirement(
            id="test-coverage",
            name="Test Coverage",
            description="Code must have test coverage",
            criterion_template=CriterionTemplate(
                target_type=CriterionTargetType.MANUAL,
                target_config={"assessor": "ci", "instructions": "Check coverage"},
                description_template="Test coverage check",
            ),
        )

        updated = ticket.add_requirement(requirement)

        assert len(updated.requirements_local) == 1
        assert updated.requirements_local[0].id == "test-coverage"
        assert len(ticket.requirements_local) == 0  # Original unchanged

    def test_add_duplicate_requirement_fails(self):
        """Test that adding duplicate requirement raises error."""
        requirement = Requirement(
            id="test-coverage",
            name="Test Coverage",
            description="Check coverage",
            criterion_template=CriterionTemplate(
                target_type=CriterionTargetType.MANUAL,
                target_config={"assessor": "ci", "instructions": "Check"},
                description_template="Coverage",
            ),
        )
        ticket = Ticket(
            id="sprint-001",
            name="Sprint",
            requirements_local=[requirement],
        )

        with pytest.raises(ValueError, match="already exists"):
            ticket.add_requirement(requirement)

    def test_remove_requirement(self):
        """Test removing a requirement from a ticket."""
        requirement = Requirement(
            id="test-coverage",
            name="Test Coverage",
            description="Check coverage",
            criterion_template=CriterionTemplate(
                target_type=CriterionTargetType.MANUAL,
                target_config={"assessor": "ci", "instructions": "Check"},
                description_template="Coverage",
            ),
        )
        ticket = Ticket(
            id="sprint-001",
            name="Sprint",
            requirements_local=[requirement],
        )

        updated = ticket.remove_requirement("test-coverage")

        assert len(updated.requirements_local) == 0
        assert len(ticket.requirements_local) == 1  # Original unchanged

    def test_remove_nonexistent_requirement(self):
        """Test removing nonexistent requirement returns unchanged ticket."""
        ticket = Ticket(id="sprint-001", name="Sprint")
        updated = ticket.remove_requirement("nonexistent")

        assert updated is ticket  # Same object returned

    def test_get_requirement(self):
        """Test getting a requirement by ID."""
        requirement = Requirement(
            id="test-coverage",
            name="Test Coverage",
            description="Check coverage",
            criterion_template=CriterionTemplate(
                target_type=CriterionTargetType.MANUAL,
                target_config={"assessor": "ci", "instructions": "Check"},
                description_template="Coverage",
            ),
        )
        ticket = Ticket(
            id="sprint-001",
            name="Sprint",
            requirements_local=[requirement],
        )

        found = ticket.get_requirement("test-coverage")
        assert found is not None
        assert found.name == "Test Coverage"

        not_found = ticket.get_requirement("nonexistent")
        assert not_found is None


# =============================================================================
# VALIDATION TESTS
# =============================================================================


class TestValidation:
    """Tests for validation rules."""

    def test_in_progress_auto_sets_started_at(self):
        """Test IN_PROGRESS status auto-sets started_at if missing."""
        created = datetime.now(timezone.utc) - timedelta(hours=1)
        ticket = Ticket(
            id="task-001",
            name="Task",
            status=TicketStatus.IN_PROGRESS,
            created_at=created,
            # Missing started_at - should be auto-set
        )
        # started_at should be auto-set to created_at
        assert ticket.started_at is not None
        assert ticket.started_at == created

    def test_completed_auto_sets_completed_at(self):
        """Test COMPLETED status auto-sets completed_at if missing."""
        created = datetime.now(timezone.utc) - timedelta(hours=2)
        started = datetime.now(timezone.utc) - timedelta(hours=1)
        ticket = Ticket(
            id="task-001",
            name="Task",
            status=TicketStatus.COMPLETED,
            created_at=created,
            started_at=started,
            # Missing completed_at - should be auto-set
        )
        # completed_at should be auto-set to started_at
        assert ticket.completed_at is not None
        assert ticket.completed_at == started

    def test_started_at_must_be_after_created_at(self):
        """Test started_at must be >= created_at."""
        created = datetime.now(timezone.utc)
        started = created - timedelta(hours=1)  # Before created

        with pytest.raises(ValueError, match="started_at cannot be before created_at"):
            Ticket(
                id="task-001",
                name="Task",
                created_at=created,
                started_at=started,
                status=TicketStatus.IN_PROGRESS,
            )

    def test_completed_at_must_be_after_started_at(self):
        """Test completed_at must be >= started_at."""
        created = datetime.now(timezone.utc) - timedelta(hours=3)
        started = datetime.now(timezone.utc) - timedelta(hours=1)
        completed = started - timedelta(minutes=30)  # Before started

        with pytest.raises(ValueError, match="completed_at cannot be before started_at"):
            Ticket(
                id="task-001",
                name="Task",
                created_at=created,
                started_at=started,
                completed_at=completed,
                status=TicketStatus.COMPLETED,
            )


# =============================================================================
# IMMUTABILITY TESTS
# =============================================================================


class TestImmutability:
    """Tests for immutable update patterns."""

    def test_start_returns_new_ticket(self):
        """Test start() returns a new Ticket instance."""
        ticket = Ticket(id="task-001", name="Task")
        started = ticket.start()

        assert ticket is not started
        assert ticket.status == TicketStatus.NOT_STARTED
        assert started.status == TicketStatus.IN_PROGRESS

    def test_complete_returns_new_ticket(self):
        """Test complete() returns a new Ticket instance."""
        created = datetime.now(timezone.utc) - timedelta(hours=2)
        started = datetime.now(timezone.utc) - timedelta(hours=1)
        ticket = Ticket(
            id="task-001",
            name="Task",
            status=TicketStatus.IN_PROGRESS,
            created_at=created,
            started_at=started,
        )
        completed = ticket.complete()

        assert ticket is not completed
        assert ticket.status == TicketStatus.IN_PROGRESS
        assert completed.status == TicketStatus.COMPLETED

    def test_add_commit_returns_new_ticket(self):
        """Test add_commit() returns a new Ticket instance."""
        ticket = Ticket(id="task-001", name="Task")
        commit = GitCommit(
            sha="abc123",
            message="feat",
            date=datetime.now(timezone.utc),
            author="dev",
        )
        updated = ticket.add_commit(commit)

        assert ticket is not updated
        assert len(ticket.commits) == 0
        assert len(updated.commits) == 1
