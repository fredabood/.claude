def migrate_legacy_yaml_to_unified(legacy: dict, entity_type: str) -> dict:
    """
    Migrate legacy YAML to unified model, preserving all data.
    """
    # Core field mapping
    unified = map_core_fields(legacy, entity_type)

    # Transform relationships to criteria
    unified['criteria'] = []
    unified['criteria'].extend(migrate_dependencies(legacy))
    unified['criteria'].extend(migrate_children(legacy))
    unified['criteria'].extend(migrate_deliverables(legacy))
    unified['criteria'].extend(migrate_gates(legacy))

    # Transform standards to requirements
    unified['requirements_local'] = migrate_standards(legacy)

    # Add new fields
    unified['priority'] = legacy.get('priority')
    unified['deferred'] = legacy.get('deferred', False)
    unified['estimated_duration_local'] = legacy.get('estimated_duration')

    # Validate no data loss
    validate_round_trip(legacy, unified)

    return unified


def migrate_dependencies(legacy: dict) -> List[Criterion]:
    """Convert blocked_by/depends_on to criteria."""
    criteria = []

    for dep in legacy.get('blocked_by', []) + legacy.get('depends_on', []):
        blocker_id = dep.get('blocker_id') or dep.get('target_id')
        criteria.append(Criterion(
            id=f"dep-{blocker_id}",
            description=f"Depends on: {blocker_id}",
            target=CompletableTarget(
                completable_id=blocker_id,
                required_status=TicketStatus(dep.get('required_status', 'completed'))
            ),
            blocks_transition_to=TicketStatus.IN_PROGRESS
        ))

    return criteria


def migrate_deliverables(legacy: dict) -> List[Criterion]:
    """Convert deliverables to FileExistsTarget criteria."""
    criteria = []

    for d in legacy.get('deliverables', []):
        paths = d if isinstance(d, list) else [d]
        criteria.append(Criterion(
            id=f"deliv-{len(criteria)}",
            description=f"Deliverable: {paths[0]}",
            target=FileExistsTarget(paths=paths),
            blocks_transition_to=TicketStatus.COMPLETED
        ))

    return criteria


def migrate_standards(legacy: dict) -> List[Requirement]:
    """Convert standards to requirements."""
    requirements = []

    for std in legacy.get('standards', []):
        target_type_map = {
            'COMMIT_CHECK': CriterionTargetType.THRESHOLD,
            'FILE_CHECK': CriterionTargetType.FILE_EXISTS,
            'TEST_RUN': CriterionTargetType.TEST_PASSES,
            'CUSTOM_SCRIPT': CriterionTargetType.EXTERNAL,
        }

        requirements.append(Requirement(
            id=std['id'],
            name=std['name'],
            description=std.get('description', ''),
            criterion_template=CriterionTemplate(
                target_type=target_type_map.get(std['type'], CriterionTargetType.EXTERNAL),
                target_config=std.get('validation', {}),
                blocks_transition_to=TicketStatus.COMPLETED,
            ),
            applicability=ApplicabilityRules(),
            inherit_mode=InheritMode.INHERIT,
            enabled=std.get('enabled', True),
        ))

    return requirements
