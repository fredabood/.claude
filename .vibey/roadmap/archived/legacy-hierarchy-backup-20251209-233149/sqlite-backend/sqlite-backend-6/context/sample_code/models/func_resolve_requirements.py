def resolve_requirements(ticket: Ticket) -> List[Requirement]:
    """
    Resolve effective requirements for a ticket.

    Algorithm:
    1. Gather requirements from ancestors (roadmap → track → sprint)
    2. Partition inherited into enforceable vs non-enforceable
    3. For each local requirement:
       - If ancestor is enforceable: ignore local inherit_mode, use ancestor
       - If OVERRIDE: replace ancestor requirement with same type
       - If SKIP: mark ancestor requirement as not applicable
       - If INHERIT: use stricter of local vs ancestor
    4. Filter to only applicable requirements
    5. Return final list
    """
    inherited = collect_ancestor_requirements(ticket)
    local = ticket.requirements_local

    effective = []
    processed_types = set()

    # First pass: enforceable requirements from ancestors (cannot be overridden)
    for inh_req in inherited:
        if inh_req.enforceable:
            effective.append(inh_req)
            processed_types.add(inh_req.id)

    # Second pass: process local requirements
    for local_req in local:
        # Skip if already handled by enforceable ancestor
        if local_req.id in processed_types:
            continue

        if local_req.inherit_mode == InheritMode.SKIP:
            # Validate: SKIP requires justification
            if not local_req.skip_justification:
                raise ValueError(f"SKIP requires justification for {local_req.id}")
            processed_types.add(local_req.id)
            continue

        if local_req.inherit_mode == InheritMode.OVERRIDE:
            effective.append(local_req)
            processed_types.add(local_req.id)
            continue

        # INHERIT mode - find matching inherited and use stricter
        inherited_match = find_by_id(inherited, local_req.id)
        if inherited_match:
            stricter = resolve_stricter(local_req, inherited_match)
            effective.append(stricter)
        else:
            effective.append(local_req)
        processed_types.add(local_req.id)

    # Add inherited requirements not overridden locally
    for inh_req in inherited:
        if inh_req.id not in processed_types:
            effective.append(inh_req)

    # Filter to applicable requirements
    return [r for r in effective if r.applicability.matches(ticket)]
