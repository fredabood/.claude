# Git Management — Guidelines

Best practices for git operations. These are guidelines for all sessions.
When `/workflow` is active, git phases become mandatory gates enforced by hooks.

> Invoke `/workflow` for full gated lifecycle with deterministic git enforcement (Phases 4 and 9).

## Branch Strategy

- **Non-trivial work:** create a feature branch named `<KEY>-kebab-description` (e.g., `HL-123-add-user-profile`)
- **Trivial changes** (typos, config, formatting): direct commits to `main` are acceptable
- Before creating a new branch: check `git status` for uncommitted changes — stash or commit them first

## Commit Hygiene

- Every commit references the active work item: `HL-123: <description>` (homelab, issue #123) or `DD-45: <description>` (dirtydata, issue #45)
- Historical `LAB-*`/`DRTY-*` prefixes remain valid when touching migrated issues
- Optionally append `(#123)` for GitHub auto-linking — never start the subject with a bare `#123` (git strips it as a comment)
- Atomic commits — one logical change per commit
- Don't mix unrelated changes in a single commit
- Allowlisted prefixes for commits without an issue: `chore:`, `typo:`, `docs:`, `sync:`

## Uncommitted Changes

- Before starting new work: check `git status`
- If uncommitted changes exist: stash (`git stash push -m "context"`) or commit with context before branching
- End of session: ensure all changes are committed — no silent uncommitted work left behind

## PR Workflow

- Multi-commit work: consider creating a PR
- PR title matches work item summary
- PR body includes acceptance criteria summary
- Use `gh pr create` for GitHub-hosted repos
