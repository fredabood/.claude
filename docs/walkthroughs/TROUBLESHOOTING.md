# Troubleshooting

> **Time Required:** Reference document
> **Difficulty:** All levels
> **Prerequisites:** Vibey installed

---

## Overview

This walkthrough covers common issues and their solutions, plus validation and repair tools.

---

## Quick Fixes

### Database Issues

**Symptom:** Commands fail with database errors

```bash
# Rebuild database from YAML (source of truth)
vibey roadmap db rebuild
```

**Symptom:** Database file corrupted

```bash
# Delete and rebuild
rm .vibey/roadmap.db
vibey roadmap db rebuild
```

### Import/Export Issues

**Symptom:** Installation not found

```bash
# Reinstall in development mode
pip install -e ".[dev]"
```

**Symptom:** Command not found

```bash
# Ensure virtual environment is active
source .venv/bin/activate
vibey --version
```

---

## Validation Commands

### Validate YAML Files

```bash
vibey validate
```

Checks:
- YAML syntax validity
- Required fields present
- ULID format correctness
- Reference integrity

### Validate Database

```bash
vibey roadmap db validate
```

Checks:
- Foreign key constraints
- Record count matching
- Schema compliance

---

## Git Integration Issues

### Validate Git State

```bash
vibey git validate
```

Checks git repository state against roadmap.

### Validate Git Tags

```bash
vibey git validate-tags
```

Ensures git tags match roadmap entities.

### Validate Roadmap Against Git

```bash
vibey git validate-roadmap
```

Cross-validates roadmap and git history.

### Repair Git Issues

```bash
# Repair general git issues
vibey git repair

# Repair tag issues
vibey git repair-tags
```

---

## Common Problems

### Tasks Not Showing

**Problem:** Created tasks don't appear in lists

**Solution:**
```bash
# Rebuild database
vibey roadmap db rebuild

# Verify task exists
vibey roadmap show <task-id>
```

### Progress Not Updating

**Problem:** Completing tasks doesn't update sprint/track progress

**Solution:**
```bash
# Rebuild database to recalculate
vibey roadmap db rebuild

# Verify status
vibey roadmap status
```

### Dependency Errors

**Problem:** Can't start task due to dependency issues

**Solution:**
```bash
# Check blockers
vibey roadmap db query blocked

# View dependencies
vibey roadmap dependency list --task <task-id>

# Remove problematic dependency
vibey roadmap dependency remove --task <task-id> --depends-on <dep-id>
```

### Git Hooks Failing

**Problem:** Pre-commit or post-commit hooks fail

**Solution:**
```bash
# Uninstall hooks temporarily
vibey git hooks uninstall

# Update hooks after fixing
vibey git hooks update
```

### Sync Issues

**Problem:** YAML and database out of sync

**Solution:**
```bash
# YAML is always source of truth
vibey roadmap db rebuild

# Validate after rebuild
vibey roadmap db validate
```

---

## Diagnostic Commands

### Check Installation

```bash
vibey --version
```

Shows version and installation status.

### Check Hooks

```bash
vibey roadmap check-hooks
```

Verifies git hooks are installed and configured.

### Check Standards

```bash
vibey roadmap check-standards
```

Validates roadmap items against defined standards.

### Check Compatibility

```bash
vibey roadmap check-compatibility
```

Checks for compatibility issues with current version.

---

## Recovery Operations

### Restore from Checkpoint

```bash
# List available checkpoints
vibey roadmap checkpoint --list

# Restore from checkpoint
vibey roadmap restore --checkpoint <name>
```

### Git Rollback

```bash
vibey git rollback
```

Rolls back recent git-related changes.

### Config Rollback

```bash
vibey config rollback
```

Rolls back platform configuration changes.

---

## Getting Help

### Command Help

```bash
# General help
vibey --help

# Command-specific help
vibey roadmap --help
vibey roadmap db --help
```

### Documentation

- [CLI Reference](../reference/CLI_REFERENCE.md) - All commands
- [Architecture Overview](../architecture/ARCHITECTURE_OVERVIEW.md) - System design
- [Database Operations](./DATABASE_OPERATIONS.md) - Database management

### Report Issues

Report bugs at [GitHub Issues](https://github.com/anthropics/vibey/issues)

---

## Command Reference

### Validation
```bash
vibey validate                       # Validate YAML files
vibey roadmap db validate            # Validate database
vibey git validate                   # Validate git state
vibey git validate-tags              # Validate git tags
vibey git validate-roadmap           # Cross-validate roadmap/git
vibey roadmap check-hooks            # Check hooks
vibey roadmap check-standards        # Check standards
vibey roadmap check-compatibility    # Check compatibility
```

### Repair
```bash
vibey git repair                     # Repair git issues
vibey git repair-tags                # Repair tag issues
vibey roadmap db rebuild             # Rebuild database
```

### Rollback
```bash
vibey git rollback                   # Rollback git changes
vibey config rollback                # Rollback config
vibey roadmap restore                # Restore from checkpoint
```

---

## See Also

- [Database Operations](./DATABASE_OPERATIONS.md) - Database management
- [Daily Workflow](./DAILY_WORKFLOW.md) - Normal operations
- [CLI Reference](../reference/CLI_REFERENCE.md) - All commands
