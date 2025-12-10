# Task 002: Move ORM Imports Behind try/except ImportError

**Task ID:** dogfooding-bugs-01-task-002
**Bug Addressed:** #6 (SQLAlchemy unconditional import)
**Complexity:** Low
**Type:** Development

---

## Problem Statement

The file `vibey/roadmap/models/ticket/__init__.py` unconditionally imports from the `orm` module at line 129:

```python
from vibey.roadmap.models.ticket.orm import (
    Base,
    TicketORM,
    RoadmapTicketORM,
    TrackTicketORM,
    SprintTicketORM,
    TaskTicketORM,
    CriterionORM,
    deserialize_target,
    serialize_target,
    get_unified_schema_ddl,
    create_unified_schema,
    get_ticket_orm_class,
)
```

Even with lazy imports in `orm.py`, this line will trigger the lazy load at package import time.

---

## Solution Design

Wrap the ORM imports in a try/except block and provide stub references when SQLAlchemy is not available.

### Implementation

```python
# ORM imports - optional, requires SQLAlchemy
try:
    from vibey.roadmap.models.ticket.orm import (
        Base,
        TicketORM,
        RoadmapTicketORM,
        TrackTicketORM,
        SprintTicketORM,
        TaskTicketORM,
        CriterionORM,
        deserialize_target,
        serialize_target,
        get_unified_schema_ddl,
        create_unified_schema,
        get_ticket_orm_class,
    )
    _HAS_SQLALCHEMY = True
except ImportError:
    _HAS_SQLALCHEMY = False
    # Provide None placeholders for type checking
    Base = None
    TicketORM = None
    RoadmapTicketORM = None
    TrackTicketORM = None
    SprintTicketORM = None
    TaskTicketORM = None
    CriterionORM = None
    deserialize_target = None
    serialize_target = None
    get_unified_schema_ddl = None
    create_unified_schema = None
    get_ticket_orm_class = None
```

### Update __all__ Export

Conditionally include ORM exports:

```python
# Base __all__
__all__ = [
    # Enums - Ticket lifecycle
    "TicketStatus",
    # ... other exports
]

# Add ORM exports only if available
if _HAS_SQLALCHEMY:
    __all__.extend([
        "Base",
        "TicketORM",
        # ... other ORM exports
    ])
```

---

## Implementation Steps

1. Locate the ORM import block in `ticket/__init__.py` (line 129)
2. Wrap imports in try/except ImportError
3. Set `_HAS_SQLALCHEMY` flag for conditional logic
4. Provide `None` placeholders for unavailable classes
5. Update `__all__` to conditionally include ORM exports
6. Test package import without SQLAlchemy

---

## Files to Modify

| File | Changes |
|------|---------|
| `vibey/roadmap/models/ticket/__init__.py` | Wrap lines 129-147 in try/except |

---

## Testing Strategy

1. Uninstall SQLAlchemy: `pip uninstall sqlalchemy -y`
2. Import package: `from vibey.roadmap.models.ticket import *`
3. Verify no `ImportError`
4. Verify ORM classes are `None`
5. Reinstall SQLAlchemy and verify ORM classes work

---

## Success Criteria

- [ ] Package `vibey.roadmap.models.ticket` importable without SQLAlchemy
- [ ] `_HAS_SQLALCHEMY` flag available for conditional logic
- [ ] ORM class placeholders are `None` when SQLAlchemy unavailable
- [ ] Full functionality when SQLAlchemy is installed

---

## Dependencies

- **Task 001** should be completed first (lazy imports in orm.py)
  - However, this task can also work independently with a simpler approach

---

## Alternative Approach (If Task 001 Not Done)

If Task 001 is skipped or delayed, this task can still work by catching the ImportError from the unconditional SQLAlchemy import in orm.py:

```python
try:
    from vibey.roadmap.models.ticket.orm import ...
except ImportError as e:
    if 'sqlalchemy' in str(e).lower():
        _HAS_SQLALCHEMY = False
        # Set None placeholders
    else:
        raise
```

---

## Notes

This change maintains backward compatibility - code that imports ORM classes will still work if SQLAlchemy is installed. Code that doesn't need ORM will work regardless.
