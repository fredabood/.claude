# Config System Edge Cases

**Version:** 1.0
**Date:** 2025-11-10
**Sprint:** directory-migration-2, Task 014

This document covers edge cases handled by the config system.

---

## Overview

The config system (loader + migration) handles various edge cases gracefully with clear error messages.

---

## Handled Edge Cases

### 1. Both Configs Exist

**Scenario:** Project has both `.vibey/config/` and `.claude/project-config.yaml`

**Behavior:**
- Modular config takes precedence
- Warning issued: "Found both... Using modular config"
- Legacy config ignored
- No migration prompt (already using modular)

**Test:**
```bash
cd /tmp/test-config-loader
vibey config validate
# Warning: Found both configs, using modular
```

---

### 2. No Config Exists

**Scenario:** Neither `.vibey/config/` nor `.claude/project-config.yaml` exists

**Behavior:**
- Clear error message
- Suggests running `vibey init`
- Exit code 1

**Test:**
```bash
cd /tmp/empty-project
vibey config validate
# Error: No Vibey configuration found
# Run 'vibey init' to create one.
```

---

### 3. Invalid YAML Syntax

**Scenario:** Config file has malformed YAML

**Behavior:**
- PyYAML parse error caught
- Clear error with line/column
- Exit code 1

**Test:**
```bash
echo "invalid: yaml: [[[" > .claude/project-config.yaml
vibey config validate
# Error: mapping values are not allowed here
#   in ".../project-config.yaml", line 1, column 14
```

---

### 4. Empty Config File

**Scenario:** Config file exists but is empty

**Behavior:**
- Detected as empty
- Clear error message
- Exit code 1

**Test:**
```bash
echo "" > .claude/project-config.yaml
vibey config validate
# Error: Empty config file: .../project-config.yaml
```

---

### 5. Missing Required Fields

**Scenario:** Config missing required fields (e.g., `project.version`, `tech_stack.languages`)

**Behavior:**
- Pydantic validation error
- Lists all missing/invalid fields
- Clear error messages
- Exit code 1

**Test:**
```bash
# Config without tech_stack.languages
vibey config validate
# Error: 1 validation error for TechStack
# languages
#   List should have at least 1 item after validation
```

---

### 6. Invalid Field Values

**Scenario:** Config has invalid enum values or wrong types

**Behavior:**
- Pydantic validation catches it
- Clear error with expected values
- Exit code 1

**Examples:**
- `project.type: "invalid-type"` → "Input should be 'web-app', 'api', 'library'..."
- `project.version: "1.0"` → "String should match pattern ^\\d+\\.\\d+\\.\\d+$"
- `quality_gates.mode: "invalid"` → "Input should be 'strict', 'balanced', or 'permissive'"

---

### 7. YAML Features (Anchors, Aliases, Comments)

**Scenario:** Config uses YAML anchors, aliases, or comments

**Behavior:**
- PyYAML resolves anchors/aliases automatically
- Comments preserved during read (lost on write)
- Works correctly

**Test:**
```yaml
project:
  name: &name my-project
  description: *name  # Reference
  # This is a comment

vibey config validate
# ✓ Configuration valid!
```

**Note:** When migrating, anchors/aliases are resolved to plain values in modular config.

---

### 8. Permission Errors

**Scenario:** Cannot read config file or write during migration

**Behavior:**
- OS error caught and reported
- Clear error message
- Exit code 1

**Examples:**
- Read permission denied: "Permission denied: .../project-config.yaml"
- Write permission denied during migration: "Failed to create directory: Permission denied"

---

### 9. Migration Declined

**Scenario:** User declines auto-migration prompt

**Behavior:**
- Marker file created (`.vibey/.migration-declined`)
- Won't prompt again
- Continues with legacy config
- User can remove marker to see prompt again

**Test:**
```bash
# First time
vibey config validate
# Prompt: Migrate to modular config? [Y/n]: n
# You can migrate later with: vibey config migrate

# Second time
vibey config validate
# No prompt (marker exists)

# Re-enable prompt
rm .vibey/.migration-declined
vibey config validate
# Prompt shows again
```

---

### 10. Concurrent Modifications

**Scenario:** Config file modified during migration

**Behavior:**
- Backup created before migration starts
- Migration uses loaded config (in-memory)
- If error occurs, backup available for rollback

**Mitigation:**
- Backup system provides safety net
- `vibey config rollback` available
- User can restore from `.vibey/config-backups/`

---

### 11. Circular References (Not Possible)

**Scenario:** YAML with circular anchors

**Behavior:**
- PyYAML detects and raises error
- Clear error message
- Exit code 1

**Example:**
```yaml
project: &self
  name: test
  data: *self  # Circular reference

# Error: found undefined alias 'self'
```

---

### 12. Corrupted Backup Files

**Scenario:** Backup file exists but is corrupted during rollback

**Behavior:**
- Rollback attempts to restore
- If backup invalid, error reported
- Original legacy file still exists (backup creation copies, doesn't move)

**Protection:**
- Backups include README with instructions
- Multiple backups kept (timestamped)
- User can manually restore

---

### 13. Large Config Files

**Scenario:** Config file > 1MB (unlikely but possible)

**Behavior:**
- PyYAML and Pydantic handle it
- May be slow but works
- No size limits enforced

**Recommendation:**
- If config is huge, consider refactoring
- Modular format naturally limits size (4 separate files)

---

### 14. Unicode and Special Characters

**Scenario:** Config contains unicode, emojis, or special characters

**Behavior:**
- UTF-8 encoding used throughout
- Works correctly
- Preserved during migration

**Test:**
```yaml
project:
  name: "My Project 🚀"
  description: "Über cool project with Ñoño"

vibey config validate
# ✓ Configuration valid!
```

---

### 15. Symlinked Config Files

**Scenario:** Config files are symlinks

**Behavior:**
- Python's Path.resolve() follows symlinks
- Reads actual file
- Works correctly

**Caveat:** Migration creates backup of symlink target, not symlink itself.

---

## Edge Cases NOT Handled

### Network File Systems

**Issue:** Config on NFS/SMB share with network issues

**Behavior:** OS-level errors (timeout, connection lost) will propagate as Python exceptions

**Mitigation:** Run config operations on local filesystem

---

### File System Corruption

**Issue:** Underlying filesystem corruption

**Behavior:** OS errors will be reported

**Mitigation:** Regular backups, filesystem checks

---

### Out of Disk Space

**Issue:** No space left on device during migration

**Behavior:** Write error during migration

**Mitigation:** Migration checks available before starting (TODO: implement check)

---

## Testing Checklist

When adding config features, test these cases:

- [ ] Both configs exist
- [ ] No config exists
- [ ] Invalid YAML syntax
- [ ] Empty config file
- [ ] Missing required fields
- [ ] Invalid enum values
- [ ] YAML anchors/aliases
- [ ] Comments in YAML
- [ ] Permission errors (read)
- [ ] Permission errors (write)
- [ ] Unicode characters
- [ ] Large config files (10KB+)
- [ ] Migration declined (marker file)
- [ ] Migration accepted
- [ ] Rollback with valid backup
- [ ] Multiple backups exist

---

## Future Improvements

### Disk Space Check

Add pre-flight check before migration:

```python
import shutil

def check_disk_space(path: Path, required_bytes: int) -> bool:
    stat = shutil.disk_usage(path)
    return stat.free >= required_bytes
```

### Config Size Warnings

Warn if config files are unusually large:

```python
MAX_REASONABLE_SIZE = 100_000  # 100KB

if config_file.stat().st_size > MAX_REASONABLE_SIZE:
    warnings.warn("Config file is unusually large (>100KB)")
```

### Atomic Writes

Use atomic writes for config updates:

```python
import tempfile

def atomic_write(path: Path, content: str):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(content)
    tmp.replace(path)  # Atomic on POSIX
```

---

**Last Updated:** 2025-11-10
**Sprint:** directory-migration-2
**Task:** 014 - Handle edge cases
