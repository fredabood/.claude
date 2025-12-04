def migrate_context_files():
    """
    Migrate context files from scattered locations to consolidated structure.

    Source: .vibey/roadmap/<track>/context/
            .vibey/roadmap/<track>/<sprint>/context/
            .vibey/roadmap/<track>/<sprint>/<task>/context/

    Target: .vibey/roadmap/context/tracks/<track-id>/
            .vibey/roadmap/context/sprints/<sprint-id>/
            .vibey/roadmap/context/tasks/<task-id>/
    """
