"""
CLI command implementations.

This package contains modular command implementations split by functionality.
Each module contains related command functions that are imported and used by main.py.

During the transition from commands.py to modular commands, this package re-exports
all commands - both from the new modules and from the legacy commands.py file.
"""

# Import everything from the legacy commands.py file for backwards compatibility
# This will be removed once all commands are migrated to modules
from vibey.cli.commands_legacy import *  # noqa: F401, F403

# Then override with the new modular implementations
# Checkpoint commands
from vibey.cli.commands.checkpoint import (
    checkpoint_create_cmd,
    checkpoint_list_cmd,
    checkpoint_verify_cmd,
    checkpoint_restore_cmd,
    checkpoint_clean_cmd,
    checkpoint_compare_cmd,
)

# Hook commands
from vibey.cli.commands.hooks import (
    install_hooks_cmd,
    uninstall_hooks_cmd,
    check_hooks_cmd,
)

# Config commands
from vibey.cli.commands.config import (
    config_show_cmd,
    config_validate_cmd,
    config_generate_cmd,
    config_migrate_cmd,
    config_rollback_cmd,
    config_update_cmd,
)

# Deploy commands
from vibey.cli.commands.deploy import (
    deploy_cmd,
)

# Docs commands
from vibey.cli.commands.docs import (
    docs_generate_cmd,
)

# Edit commands
from vibey.cli.commands.edit import (
    edit_file_cmd,
    edit_bulk_cmd,
    edit_validate_cmd,
    edit_rollback_cmd,
)

# Audit commands
from vibey.cli.commands.audit import (
    audit_log_cmd,
    audit_show_cmd,
    audit_suspicious_cmd,
    audit_report_cmd,
    activity_cmd,
)

# Validate commands
from vibey.cli.commands.validate import (
    validate_docs_cmd,
    validate_assets_cmd,
    validate_structure_cmd,
)

# Session commands
from vibey.cli.commands.session import (
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

# Discover commands
from vibey.cli.commands.discover import (
    discover_run_cmd,
    discover_show_cmd,
    discover_status_cmd,
    discover_history_cmd,
    discover_diff_cmd,
    discover_refresh_cmd,
)

# Context commands
from vibey.cli.commands.context import (
    context_init_cmd,
    context_list_cmd,
    context_show_cmd,
    context_archive_cmd,
    context_clean_cmd,
    context_export_cmd,
    context_search_cmd,
)

__all__ = [
    # Checkpoint
    'checkpoint_create_cmd',
    'checkpoint_list_cmd',
    'checkpoint_verify_cmd',
    'checkpoint_restore_cmd',
    'checkpoint_clean_cmd',
    'checkpoint_compare_cmd',
    # Hooks
    'install_hooks_cmd',
    'uninstall_hooks_cmd',
    'check_hooks_cmd',
    # Config
    'config_show_cmd',
    'config_validate_cmd',
    'config_generate_cmd',
    'config_migrate_cmd',
    'config_rollback_cmd',
    'config_update_cmd',
    # Deploy
    'deploy_cmd',
    # Docs
    'docs_generate_cmd',
    # Edit
    'edit_file_cmd',
    'edit_bulk_cmd',
    'edit_validate_cmd',
    'edit_rollback_cmd',
    # Audit
    'audit_log_cmd',
    'audit_show_cmd',
    'audit_suspicious_cmd',
    'audit_report_cmd',
    'activity_cmd',
    # Validate
    'validate_docs_cmd',
    'validate_assets_cmd',
    'validate_structure_cmd',
    # Session
    'session_start_cmd',
    'session_end_cmd',
    'session_pause_cmd',
    'session_resume_cmd',
    'session_status_cmd',
    'session_show_cmd',
    'session_list_cmd',
    'session_report_cmd',
    'session_timeline_cmd',
    'session_export_cmd',
    'session_decisions_cmd',
    # Discover
    'discover_run_cmd',
    'discover_show_cmd',
    'discover_status_cmd',
    'discover_history_cmd',
    'discover_diff_cmd',
    'discover_refresh_cmd',
    # Context
    'context_init_cmd',
    'context_list_cmd',
    'context_show_cmd',
    'context_archive_cmd',
    'context_clean_cmd',
    'context_export_cmd',
    'context_search_cmd',
]
