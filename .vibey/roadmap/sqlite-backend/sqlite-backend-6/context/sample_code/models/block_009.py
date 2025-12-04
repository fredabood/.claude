# Example: Task with dependency and children
task = TaskTicket(
    id="task-main",
    criteria=[
        # DEPENDENCY: blocks starting
        Criterion(
            id="depends-on-setup",
            description="Setup task must be complete",
            target=CompletableTarget(completable_id="task-setup"),
            blocks_transition_to=TicketStatus.IN_PROGRESS  # <-- Dependency
        ),
        # CHILD: blocks completing
        Criterion(
            id="subtask-1-complete",
            description="Subtask 1 complete",
            target=CompletableTarget(completable_id="subtask-1"),
            blocks_transition_to=TicketStatus.COMPLETED  # <-- Child
        ),
    ]
)

# Only COMPLETED blockers count as children:
task.children  # Returns: ["subtask-1"]
task.dependencies  # Returns criteria with blocks_transition_to=IN_PROGRESS
