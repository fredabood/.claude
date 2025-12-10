# Task 003: Add SQLAlchemy to Optional Dependencies

**Task ID:** dogfooding-bugs-01-task-003
**Bug Addressed:** #6 (SQLAlchemy unconditional import)
**Complexity:** Low
**Type:** Development

---

## Problem Statement

Currently, `pyproject.toml` lists SQLAlchemy as a required dependency (line 38):

```toml
dependencies = [
    "pyyaml>=6.0",
    "jinja2>=3.1.0",
    "click>=8.1.0",
    "rich>=13.0.0",
    "pydantic>=2.0.0",
    "jsonschema>=4.0.0",
    "sqlalchemy>=2.0.0",   # <-- Should be optional
    "python-ulid>=3.0.0",
]
```

This forces all users to install SQLAlchemy even if they only use YAML-based roadmap operations.

---

## Solution Design

Move SQLAlchemy to optional dependencies under a `[db]` extra.

### New Dependency Structure

```toml
dependencies = [
    "pyyaml>=6.0",
    "jinja2>=3.1.0",
    "click>=8.1.0",
    "rich>=13.0.0",
    "pydantic>=2.0.0",
    "jsonschema>=4.0.0",
    "python-ulid>=3.0.0",
]

[project.optional-dependencies]
db = [
    "sqlalchemy>=2.0.0",
]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
    "sqlalchemy>=2.0.0",  # Include for dev testing
]
all = [
    "sqlalchemy>=2.0.0",
]
```

---

## Implementation Steps

1. Open `pyproject.toml`
2. Remove `"sqlalchemy>=2.0.0"` from `dependencies`
3. Add `[project.optional-dependencies].db` section
4. Add SQLAlchemy to `dev` dependencies (for testing)
5. Optionally create `all` extra that includes everything
6. Update README/docs to document optional extras

---

## Files to Modify

| File | Changes |
|------|---------|
| `pyproject.toml` | Move sqlalchemy from required to optional |

---

## Installation Commands

After this change:

```bash
# Basic install (no SQLAlchemy)
pip install vibey-framework

# With database support
pip install vibey-framework[db]

# Development install
pip install vibey-framework[dev]

# Full install
pip install vibey-framework[all]
```

---

## Documentation Updates

Add to README.md or docs:

```markdown
## Installation

### Basic Install
pip install vibey-framework

### With SQLite Database Support
pip install vibey-framework[db]

The `[db]` extra is required for:
- `vibey roadmap db rebuild`
- `vibey roadmap db validate`
- SQLite-backed roadmap queries
```

---

## Testing Strategy

1. Create fresh virtual environment
2. Install package without extras: `pip install .`
3. Verify `import vibey` works
4. Verify `vibey roadmap status` works (YAML-only operations)
5. Verify database commands show helpful error message
6. Install with db extra: `pip install .[db]`
7. Verify database commands work

---

## Success Criteria

- [ ] `pip install vibey-framework` succeeds without SQLAlchemy
- [ ] `pip install vibey-framework[db]` includes SQLAlchemy
- [ ] YAML-based CLI commands work without SQLAlchemy
- [ ] Database commands show helpful error when SQLAlchemy missing
- [ ] Documentation updated with installation options

---

## Dependencies

This task is independent but should be coordinated with:
- **Task 001**: Lazy imports in orm.py
- **Task 002**: try/except in __init__.py

All three tasks work together to make SQLAlchemy truly optional.

---

## Notes

Consider also updating CI/CD to test both with and without SQLAlchemy:

```yaml
jobs:
  test-minimal:
    - pip install .
    - pytest tests/test_yaml_operations.py

  test-full:
    - pip install .[db,dev]
    - pytest
```
