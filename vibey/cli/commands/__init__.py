"""
CLI command implementations.

This package contains modular command implementations split by functionality.
Each module contains related command functions that are imported and used by main.py.
"""

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
]
