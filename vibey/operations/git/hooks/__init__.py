"""
Git Hooks for Vibey Roadmap System

Provides pre-commit, commit-msg, post-merge, and post-checkout hooks
for validating and syncing Git operations with roadmap integration.

Tasks: git-integration-2-task-001, git-integration-2-task-002, sqlite-backend-3-task-003, sqlite-backend-3-task-004
"""

from vibey.operations.git.hooks.pre_commit import PreCommitHook
from vibey.operations.git.hooks.pre_commit import ValidationIssue, HookConfig
from vibey.operations.git.hooks.commit_msg import CommitMsgHook
from vibey.operations.git.hooks.post_merge import PostMergeHook, PostCheckoutHook

__all__ = [
    "PreCommitHook",
    "CommitMsgHook",
    "PostMergeHook",
    "PostCheckoutHook",
    "ValidationIssue",
    "HookConfig",
]
