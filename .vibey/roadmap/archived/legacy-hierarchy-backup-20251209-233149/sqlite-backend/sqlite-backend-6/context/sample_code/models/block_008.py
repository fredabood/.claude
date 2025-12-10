# Example: Sprint with 3 child tasks
sprint = SprintTicket(
    id="sprint-1",
    name="Authentication Sprint",
    criteria=[
        Criterion(
            id="task-001-complete",
            description="Login API complete",
            target=CompletableTarget(completable_id="task-001"),
            blocks_transition_to=TicketStatus.COMPLETED  # Child completion
        ),
        Criterion(
            id="task-002-complete",
            description="Logout API complete",
            target=CompletableTarget(completable_id="task-002"),
            blocks_transition_to=TicketStatus.COMPLETED
        ),
        Criterion(
            id="task-003-complete",
            description="Session management complete",
            target=CompletableTarget(completable_id="task-003"),
            blocks_transition_to=TicketStatus.COMPLETED
        ),
        # Sprint-level requirement (not a child)
        Criterion(
            id="integration-tests",
            description="Integration tests pass",
            target=TestPassesTarget(
                test_command="pytest tests/integration/auth/",
                pass_threshold=100.0
            ),
            blocks_transition_to=TicketStatus.COMPLETED
        ),
    ]
)

# Children are derived:
sprint.children  # Returns: ["task-001", "task-002", "task-003"]
