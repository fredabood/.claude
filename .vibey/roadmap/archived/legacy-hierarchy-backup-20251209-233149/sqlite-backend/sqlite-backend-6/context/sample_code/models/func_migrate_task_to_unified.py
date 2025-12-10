def migrate_task_to_unified(old_task: dict) -> TaskTicket:
    """Convert legacy task to unified model."""
    criteria = []

    # Convert deliverables → FileExistsTarget criteria
    for d in old_task.get('deliverables', []):
        criteria.append(Criterion(
            id=f"{old_task['id']}-deliv-{len(criteria)}",
            description=f"Deliverable: {d['paths'][0]}",
            target=FileExistsTarget(paths=d['paths']),
            blocks_transition_to=TicketStatus.COMPLETED
        ))

    # Convert blocked_by → CompletableTarget criteria
    for b in old_task.get('blocked_by', []):
        criteria.append(Criterion(
            id=f"{old_task['id']}-dep-{b['blocker_id']}",
            description=f"Depends on: {b['blocker_id']}",
            target=CompletableTarget(
                completable_id=b['blocker_id'],
                required_status=TicketStatus(b.get('required_status', 'completed'))
            ),
            blocks_transition_to=TicketStatus.IN_PROGRESS
        ))

    # Convert dependencies → CompletableTarget criteria
    for d in old_task.get('dependencies', []):
        criteria.append(Criterion(
            id=f"{old_task['id']}-dep-{d['target_id']}",
            description=f"Depends on: {d['target_id']}",
            target=CompletableTarget(
                completable_id=d['target_id'],
                required_status=TicketStatus(d.get('target_status', 'completed'))
            ),
            blocks_transition_to=TicketStatus.IN_PROGRESS
        ))

    # Convert gate_info → ThresholdTarget criterion
    if gate := old_task.get('gate_info'):
        criteria.append(Criterion(
            id=f"{old_task['id']}-gate",
            description="Quality gate",
            target=ThresholdTarget(
                metric_name="gate_score",
                threshold=gate['threshold']
            ),
            blocks_transition_to=TicketStatus.COMPLETED
        ))

    return TaskTicket(
        id=old_task['id'],
        name=old_task.get('title', old_task['id']),
        description=old_task.get('description'),
        status=TicketStatus(old_task.get('status', 'not_started')),
        criteria=criteria,
        commits_local=old_task.get('commits', []),
        task_type=TaskType(old_task.get('task_type', 'development')),
        # ... other fields
    )
