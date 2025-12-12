"""
Git Hooks for Roadmap Validation

Provides installation and management of git hooks for automatic
roadmap validation before commits.

Also provides session-aware hooks for tracking commits during
AI-assisted coding sessions.
"""

from .installer import install_hooks, uninstall_hooks, check_hooks_installed, get_hook_status
from .session_hooks import (
    on_post_commit,
    on_pre_push,
    enhance_commit_message,
    print_active_session_warning,
    get_commit_info_for_session,
)

__all__ = [
    # Installer
    'install_hooks',
    'uninstall_hooks',
    'check_hooks_installed',
    'get_hook_status',
    # Session hooks
    'on_post_commit',
    'on_pre_push',
    'enhance_commit_message',
    'print_active_session_warning',
    'get_commit_info_for_session',
]
