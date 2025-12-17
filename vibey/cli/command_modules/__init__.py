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
]
