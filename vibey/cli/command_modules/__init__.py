"""
CLI command modules.

This package contains modularized CLI commands, split from the original
monolithic commands.py for improved maintainability.

Command groups:
- roadmap: Roadmap management (tracks, sprints, tasks)
- db: Database operations (init, rebuild, query, validate)
- session: Development session tracking
- context: Context management
- discover: Project discovery
- checkpoint: Checkpoint management
- edit: File editing operations
- config: Configuration management
- audit: Audit trail and activity logging
- validate: Validation commands
- migrate: Migration utilities
- hooks: Git hook management
- deploy: Deployment commands
- docs: Documentation generation
"""

# Re-export all commands for backwards compatibility
# Imports are added as modules are created

from vibey.cli.command_modules.helpers import (
    slugify,
    resolve_id,
    get_roadmap_id,
    update_id_mapping,
    get_slug_for_ulid,
    detect_ulid_type,
)

from vibey.cli.command_modules.checkpoint import (
    checkpoint_create_cmd,
    checkpoint_list_cmd,
    checkpoint_verify_cmd,
    checkpoint_restore_cmd,
    checkpoint_clean_cmd,
    checkpoint_compare_cmd,
)

from vibey.cli.command_modules.hooks import (
    install_hooks_cmd,
    uninstall_hooks_cmd,
    check_hooks_cmd,
)

from vibey.cli.command_modules.config import (
    config_show_cmd,
    config_validate_cmd,
    config_generate_cmd,
    config_migrate_cmd,
    config_rollback_cmd,
    config_update_cmd,
)

from vibey.cli.command_modules.deploy import deploy_cmd
from vibey.cli.command_modules.docs import docs_generate_cmd

from vibey.cli.command_modules.edit import (
    edit_file_cmd,
    edit_bulk_cmd,
    edit_validate_cmd,
    edit_rollback_cmd,
)

from vibey.cli.command_modules.audit import (
    audit_log_cmd,
    audit_show_cmd,
    audit_suspicious_cmd,
    audit_report_cmd,
    activity_cmd,
    auto_progress_cmd,
)

from vibey.cli.command_modules.validate import (
    validate_docs_cmd,
    validate_assets_cmd,
    validate_structure_cmd,
)

from vibey.cli.command_modules.migrate import (
    migrate_to_roadmap_cmd,
    migrate_embedded_tasks_cmd,
    extract_embedded_cmd,
    migrate_format_cmd,
    migrate_docs_cmd,
)

from vibey.cli.command_modules.session import (
    session_start_cmd,
    session_end_cmd,
    session_pause_cmd,
    session_resume_cmd,
    session_status_cmd,
    session_show_cmd,
    session_list_cmd,
    session_report_cmd,
    session_timeline_cmd,
    session_export_cmd,
    session_decisions_cmd,
)

from vibey.cli.command_modules.discover import (
    discover_run_cmd,
    discover_show_cmd,
    discover_status_cmd,
    discover_history_cmd,
    discover_diff_cmd,
    discover_refresh_cmd,
)

from vibey.cli.command_modules.context import (
    context_init_cmd,
    context_list_cmd,
    context_show_cmd,
    context_archive_cmd,
    context_clean_cmd,
    context_export_cmd,
    context_search_cmd,
)

from vibey.cli.command_modules.db import (
    db_init_cmd,
    db_rebuild_cmd,
    db_dump_cmd,
    db_status_cmd,
    db_backup_cmd,
    db_query_blocked_cmd,
    db_query_progress_cmd,
    db_query_deps_cmd,
    db_query_stats_cmd,
    db_validate_cmd,
    db_config_cmd,
)

__all__ = [
    # Helpers
    "slugify",
    "resolve_id",
    "get_roadmap_id",
    "update_id_mapping",
    "get_slug_for_ulid",
    "detect_ulid_type",
    # Checkpoint
    "checkpoint_create_cmd",
    "checkpoint_list_cmd",
    "checkpoint_verify_cmd",
    "checkpoint_restore_cmd",
    "checkpoint_clean_cmd",
    "checkpoint_compare_cmd",
    # Hooks
    "install_hooks_cmd",
    "uninstall_hooks_cmd",
    "check_hooks_cmd",
    # Config
    "config_show_cmd",
    "config_validate_cmd",
    "config_generate_cmd",
    "config_migrate_cmd",
    "config_rollback_cmd",
    "config_update_cmd",
    # Deploy
    "deploy_cmd",
    # Docs
    "docs_generate_cmd",
    # Edit
    "edit_file_cmd",
    "edit_bulk_cmd",
    "edit_validate_cmd",
    "edit_rollback_cmd",
    # Audit
    "audit_log_cmd",
    "audit_show_cmd",
    "audit_suspicious_cmd",
    "audit_report_cmd",
    "activity_cmd",
    "auto_progress_cmd",
    # Validate
    "validate_docs_cmd",
    "validate_assets_cmd",
    "validate_structure_cmd",
    # Migrate
    "migrate_to_roadmap_cmd",
    "migrate_embedded_tasks_cmd",
    "extract_embedded_cmd",
    "migrate_format_cmd",
    "migrate_docs_cmd",
    # Session
    "session_start_cmd",
    "session_end_cmd",
    "session_pause_cmd",
    "session_resume_cmd",
    "session_status_cmd",
    "session_show_cmd",
    "session_list_cmd",
    "session_report_cmd",
    "session_timeline_cmd",
    "session_export_cmd",
    "session_decisions_cmd",
    # Discover
    "discover_run_cmd",
    "discover_show_cmd",
    "discover_status_cmd",
    "discover_history_cmd",
    "discover_diff_cmd",
    "discover_refresh_cmd",
    # Context
    "context_init_cmd",
    "context_list_cmd",
    "context_show_cmd",
    "context_archive_cmd",
    "context_clean_cmd",
    "context_export_cmd",
    "context_search_cmd",
    # Database
    "db_init_cmd",
    "db_rebuild_cmd",
    "db_dump_cmd",
    "db_status_cmd",
    "db_backup_cmd",
    "db_query_blocked_cmd",
    "db_query_progress_cmd",
    "db_query_deps_cmd",
    "db_query_stats_cmd",
    "db_validate_cmd",
    "db_config_cmd",
]
