def map_old_to_new(old_path: str) -> str:
    """
    Map old scattered path to new consolidated path.

    Examples:
    .vibey/roadmap/sqlite-backend/context/AUDIT.md
      → .vibey/roadmap/context/tracks/sqlite-backend/AUDIT.md

    .vibey/roadmap/sqlite-backend/sqlite-backend-6/context/PLAN.md
      → .vibey/roadmap/context/sprints/sqlite-backend-6/PLAN.md
    """
    parts = old_path.split('/')

    # Find context/ position
    ctx_idx = parts.index('context')

    # Determine level by position
    if ctx_idx == 3:  # roadmap/<track>/context
        entity_type = 'tracks'
        entity_id = parts[2]
    elif ctx_idx == 4:  # roadmap/<track>/<sprint>/context
        entity_type = 'sprints'
        entity_id = parts[3]
    elif ctx_idx == 5:  # roadmap/<track>/<sprint>/<task>/context
        entity_type = 'tasks'
        entity_id = parts[4]

    filename = parts[-1]
    return f".vibey/roadmap/context/{entity_type}/{entity_id}/{filename}"
