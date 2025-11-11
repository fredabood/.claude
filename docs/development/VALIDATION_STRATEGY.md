# Vibey Framework Validation Strategy

**Version:** 1.0
**Date:** 2025-11-10
**Status:** Active

---

## Overview

The Vibey framework uses **two different validation approaches** for different parts of the system:

1. **Dataclasses with manual validation** - For framework internals (roadmap system)
2. **Pydantic models** - For user-facing features (config system)

This is **intentional design diversity**, not inconsistency.

---

## Quick Reference

| Component | Validation | Why |
|-----------|-----------|-----|
| **Roadmap System** | Dataclasses | Framework internals, zero deps |
| **Config System** | Pydantic | User-facing, better UX |
| **CLI Commands** | Click | User-facing, better UX |
| **Terminal Output** | Rich | User-facing, better UX |

**Pattern:** Framework internals minimize dependencies, user-facing features prioritize UX.

---

## Roadmap System (Dataclasses)

**Location:** `vibey/roadmap/models/`

**Approach:** Python dataclasses with manual validation

**Why:**
- Framework internals (not user-facing)
- Trusted data source (created by framework scripts)
- Zero external dependencies (built-in Python 3.7+)
- Explicit validation in `__post_init__` methods

**Example:**
```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Task:
    id: str
    status: TaskStatus
    created: datetime

    def __post_init__(self):
        """Validate task data."""
        if not self.id.startswith(f"{self.sprint_id}-"):
            raise ValueError(f"Task ID {self.id} must start with {self.sprint_id}")
```

**Dependencies:** None (uses built-in modules only)

**See:** `vibey/roadmap/DESIGN_DECISIONS.md` (lines 230-297)

---

## Config System (Pydantic)

**Location:** `vibey/config/models.py`

**Approach:** Pydantic v2 models with automatic validation

**Why:**
- User-facing (users edit YAML files)
- Untrusted data source (users make mistakes)
- Rich validation error messages
- Type coercion handles common errors
- Clean enum serialization

**Example:**
```python
from pydantic import BaseModel, Field
from enum import Enum

class ProjectType(str, Enum):
    WEB_APP = "web-app"
    API = "api"
    LIBRARY = "library"

class Project(BaseModel):
    name: str
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    type: ProjectType

# Rich validation errors
try:
    project = Project(name="test", version="1.0", type="webapp")
except ValidationError as e:
    print(e)
    # ValidationError: 2 validation errors
    # version: String should match pattern '^\d+\.\d+\.\d+$'
    # type: Input should be 'web-app', 'api', or 'library'
```

**Dependencies:** `pydantic>=2.0.0`

**See:** `vibey/config/DESIGN_DECISIONS.md`

---

## Framework Principle: Right Tool for the Job

### User-Facing Features → Prioritize UX

**Accept dependencies if they improve user experience:**

✅ **Pydantic** - Better validation errors for config files
✅ **Click** - Better CLI experience than argparse
✅ **Rich** - Better terminal output than print()

**Examples:**
- Config validation (Pydantic)
- CLI commands (Click)
- Terminal output (Rich)
- Template rendering (Jinja2)

### Framework Internals → Minimize Dependencies

**Avoid dependencies for internal data structures:**

✅ **Dataclasses** - Zero dependencies for core models
✅ **Built-in types** - Use standard library when possible
✅ **Manual validation** - Explicit, debuggable code

**Examples:**
- Roadmap models (dataclasses)
- State tracking (built-in types)
- Business logic (pure Python)

---

## Comparison

### Dataclasses vs Pydantic

| Aspect | Dataclasses | Pydantic |
|--------|-------------|----------|
| **Dependencies** | None (built-in) | External (pydantic) |
| **Type Validation** | None (hints only) | Automatic runtime |
| **Error Messages** | Basic ValueError | Rich, detailed errors |
| **Type Coercion** | None | Automatic |
| **Serialization** | Manual | Automatic |
| **Performance** | Faster | Slight overhead |
| **Learning Curve** | Lower | Moderate |
| **Best For** | Framework internals | User-facing input |

### When to Use Each

**Use Dataclasses:**
- ✅ Framework-internal data structures
- ✅ Trusted data sources
- ✅ Zero dependencies critical
- ✅ Business logic validation primary
- ✅ Performance sensitive

**Use Pydantic:**
- ✅ User-facing configuration
- ✅ Untrusted user input
- ✅ Rich error messages important
- ✅ Type coercion helpful
- ✅ Complex nested validation

---

## Should We Standardize?

### Question: Should we migrate roadmap system to Pydantic?

**Answer: NO**

**Rationale:**
1. No user-facing benefit (roadmap is framework internals)
2. Large refactoring effort (2-3 days) for zero functional gain
3. Adds unnecessary dependency to framework core
4. Current implementation works correctly
5. Different requirements justify different tools

**Net Benefit:** NEGATIVE ❌

**See:** `vibey/config/DESIGN_DECISIONS.md` - "Should We Standardize?" section

---

## Guidelines for Contributors

### Adding New Models

**Ask yourself:**

1. **Who uses this data?**
   - Framework internals → Dataclasses
   - Users directly → Pydantic

2. **Where does data come from?**
   - Framework scripts → Dataclasses
   - User input → Pydantic

3. **What happens on error?**
   - Internal bug → Dataclasses (stack trace OK)
   - User mistake → Pydantic (rich errors needed)

4. **Is zero dependencies important?**
   - Core framework → Dataclasses
   - User-facing tools → Pydantic OK

### Examples

**Scenario 1: New internal state tracking**
```python
# Use dataclasses (framework internal)
from dataclasses import dataclass

@dataclass
class BuildState:
    started: datetime
    completed: Optional[datetime] = None

    def __post_init__(self):
        if self.completed and self.completed < self.started:
            raise ValueError("Completion cannot be before start")
```

**Scenario 2: New user configuration file**
```python
# Use Pydantic (user-facing)
from pydantic import BaseModel, Field

class BuildConfig(BaseModel):
    parallel: bool = True
    workers: int = Field(ge=1, le=32, default=4)
    timeout: int = Field(ge=0, default=300)
```

---

## Testing Strategy

### Dataclass Testing

```python
def test_task_validation():
    """Test manual validation in __post_init__."""
    with pytest.raises(ValueError) as exc:
        Task(id="invalid-id", sprint_id="sprint-1", ...)

    assert "must start with" in str(exc.value)
```

### Pydantic Testing

```python
def test_config_validation():
    """Test Pydantic validation."""
    with pytest.raises(ValidationError) as exc:
        ProjectConfig(project={"version": "1.0"})  # Invalid format

    assert "String should match pattern" in str(exc.value)
```

---

## Migration Policy

### No Migration Planned

The decision to use different validation approaches is **intentional and final**.

**We will NOT:**
- ❌ Migrate roadmap system to Pydantic
- ❌ Migrate config system to dataclasses
- ❌ Standardize on one approach

**We will:**
- ✅ Document why different approaches are used
- ✅ Clarify guidelines for new code
- ✅ Maintain both approaches appropriately

---

## References

**Design Decisions:**
- `vibey/config/DESIGN_DECISIONS.md` - Config system (Pydantic)
- `vibey/roadmap/DESIGN_DECISIONS.md` - Roadmap system (Dataclasses)

**Implementation:**
- `vibey/config/models.py` - Pydantic models
- `vibey/roadmap/models/` - Dataclass models

**Documentation:**
- `vibey/config/README.md` - Config API reference
- `vibey/roadmap/models/__init__.py` - Roadmap model explanation

---

## Summary

**Two validation approaches, one framework:**

1. **Roadmap system** → Dataclasses (framework internals, zero deps)
2. **Config system** → Pydantic (user-facing, better UX)

This is **"right tool for the job"**, not inconsistency.

**Framework Principle:**
> Minimize dependencies for framework internals,
> prioritize UX for user-facing features.

---

**Document Status:** ✅ Complete
**Last Updated:** 2025-11-10
**Next Review:** After Sprint 2 completion
