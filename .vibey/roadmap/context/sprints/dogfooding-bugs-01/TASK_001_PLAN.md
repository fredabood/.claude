# Task 001: Implement Lazy Imports in orm.py

**Task ID:** dogfooding-bugs-01-task-001
**Bug Addressed:** #6 (SQLAlchemy unconditional import)
**Complexity:** Medium
**Type:** Development

---

## Problem Statement

The file `vibey/roadmap/models/ticket/orm.py` imports SQLAlchemy at module level (lines 23-43), causing:
```python
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, ...
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, Session, ...
)
```

This breaks the CLI for users who don't have SQLAlchemy installed, even though ORM functionality is only needed for database operations.

---

## Solution Design

Implement lazy imports using a common pattern that defers SQLAlchemy import until the ORM classes are actually used.

### Approach: Module-Level Lazy Import Pattern

```python
# At module level
_sqlalchemy = None
_sqlalchemy_orm = None

def _ensure_sqlalchemy():
    """Lazy load SQLAlchemy modules."""
    global _sqlalchemy, _sqlalchemy_orm
    if _sqlalchemy is None:
        try:
            import sqlalchemy as _sqlalchemy
            import sqlalchemy.orm as _sqlalchemy_orm
        except ImportError:
            raise ImportError(
                "SQLAlchemy is required for ORM functionality. "
                "Install with: pip install vibey-framework[db]"
            )
    return _sqlalchemy, _sqlalchemy_orm
```

### Class-Level Implementation

Use `__init_subclass__` or metaclass to ensure SQLAlchemy is loaded before class body executes:

```python
class Base:
    """SQLAlchemy declarative base - lazy loaded."""

    def __init_subclass__(cls, **kwargs):
        _ensure_sqlalchemy()
        super().__init_subclass__(**kwargs)
```

Or use a factory function pattern:

```python
def get_base_class():
    """Get SQLAlchemy Base class (lazy loaded)."""
    sa, sa_orm = _ensure_sqlalchemy()

    class Base(sa_orm.DeclarativeBase):
        pass

    return Base
```

---

## Implementation Steps

1. Create `_ensure_sqlalchemy()` function at top of orm.py
2. Replace direct imports with lazy loading
3. Update `Base` class to use lazy loading
4. Update all ORM model classes to call `_ensure_sqlalchemy()` in their class body or `__init__`
5. Update type hints to use string annotations or `TYPE_CHECKING` block
6. Test that module can be imported without SQLAlchemy

---

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/roadmap/models/ticket/orm.py` | Replace lines 23-43 with lazy import pattern |

---

## Type Hint Strategy

Use `TYPE_CHECKING` block for static analysis while keeping runtime lazy:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy import Column, String, ...
    from sqlalchemy.orm import DeclarativeBase, Mapped, ...
```

---

## Testing Strategy

1. Import `orm.py` in a fresh Python environment without SQLAlchemy
2. Verify no `ImportError` is raised on import
3. Verify `ImportError` with helpful message when ORM classes are instantiated

---

## Success Criteria

- [ ] `vibey/roadmap/models/ticket/orm.py` can be imported without SQLAlchemy installed
- [ ] ORM classes raise helpful `ImportError` when used without SQLAlchemy
- [ ] Type hints still work for IDE/mypy analysis
- [ ] Existing ORM functionality unchanged when SQLAlchemy is installed

---

## Dependencies

None - this task can start immediately.

---

## Notes

This is part of a larger effort to make SQLAlchemy an optional dependency. The goal is to allow basic CLI operations (roadmap status, listing, etc.) without requiring SQLAlchemy, while database operations require the optional `[db]` extra.
