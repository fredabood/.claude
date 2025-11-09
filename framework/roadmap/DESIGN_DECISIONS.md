# Roadmap System Design Decisions

**Version:** 2.1 (Gate Model)
**Date:** 2025-11-09
**Sprint:** roadmap-system-1
**Status:** Implemented

---

## Executive Summary

This document captures the key design decisions made during implementation of the Roadmap Object Hierarchy system (Sprint 1: Core Data Model & YAML Schema). These decisions establish the foundation for how roadmap state is structured, validated, and manipulated throughout the Vibey framework.

**Key Design Principles:**
- ✅ Type safety through dataclasses with strict validation
- ✅ Zero external dependencies (uses built-in Python dataclasses)
- ✅ Single source of truth for each concern
- ✅ Explicit validation at data boundaries
- ✅ Developer-friendly with clear error messages
- ✅ Performance-conscious with lazy evaluation where appropriate

---

## Table of Contents

1. [YAML Schema Decisions](#yaml-schema-decisions)
2. [Python Data Model Decisions](#python-data-model-decisions)
3. [Validation Strategy](#validation-strategy)
4. [Serialization Approach](#serialization-approach)
5. [Performance Considerations](#performance-considerations)
6. [Future Extensibility](#future-extensibility)

---

## YAML Schema Decisions

### Decision 1: Schema Format - JSON Schema in YAML

**Decision:** Use custom YAML schema format with validation rules (not JSON Schema)

**Rationale:**
- Existing schemas already implemented in custom format
- More readable for documentation purposes
- Easier to extend with framework-specific validation rules
- Can generate JSON Schema from these if needed later

**Alternative Considered:**
- JSON Schema format - rejected due to verbosity and existing implementation

**Impact:**
- Custom validator implementation required
- Schema documentation embedded in schema files
- Easier for contributors to understand

**Files Affected:**
- `framework/roadmap/schema/roadmap.schema.yaml`
- `framework/roadmap/schema/track.schema.yaml`
- `framework/roadmap/schema/sprint.schema.yaml`
- `framework/roadmap/schema/task.schema.yaml`

---

### Decision 2: ID Format Enforcement

**Decision:** Enforce strict ID patterns with regex validation

**Patterns:**
- Roadmap ID: `^[a-z0-9-]+$` (e.g., `vibey-framework-v2`)
- Track ID: `^[a-z0-9-]+$` (e.g., `backend`, `frontend`)
- Sprint ID: `^[a-z0-9-]+-\d+$` (e.g., `backend-1`, `frontend-2`)
- Task ID: `^[a-z0-9-]+-\d+-(task|gate-[cp])\d+$` (e.g., `backend-1-task-001`, `backend-1-gate-p001`)

**Rationale:**
- Ensures consistent naming across all roadmaps
- Makes parent-child relationships explicit
- Enables easy parsing and validation
- Prevents ambiguous or confusing IDs

**Alternative Considered:**
- Free-form IDs - rejected due to inconsistency risk
- UUID-based IDs - rejected as not human-readable

**Validation Rules:**
```yaml
# Sprint ID must start with track_id
rule: "sprint id must start with track_id"

# Task ID must start with sprint_id
rule: "task id must start with sprint_id"
```

---

### Decision 3: Status Enums - Different Sets for Different Objects

**Decision:** Define separate status enums for each object type

**Status Sets:**

**Tasks (limited set - no production concerns):**
- `not_started`, `in_progress`, `paused`, `completed`, `won't_do`

**Sprints (full set - production-deployable):**
- `not_started`, `in_progress`, `paused`, `completion_gate_check`, `completed`, `production_gate_check`, `production_ready`, `deployed`, `won't_do`

**Tracks (same as sprints):**
- Full status set

**Roadmaps (same as sprints):**
- Full status set

**Rationale:**
- Tasks are context-window units, not production concerns
- Sprints are logical units pushable to production
- Clear separation of concerns
- Prevents invalid state transitions

**Alternative Considered:**
- Single unified status enum - rejected as too permissive

---

### Decision 4: Required vs Optional Fields

**Decision:** Strict required field enforcement with explicit nullable fields

**Required Fields (all objects):**
- `id`, `status`, `blocked`, `created`, `metadata`

**Optional Fields (can be null):**
- All completion timestamps (`started`, `completed`, `deployed`, etc.)
- `estimated_duration`, `target_completion`
- `gate_info` (only for quality gate tasks)

**Rationale:**
- Ensures minimum viable object state
- Makes data contracts explicit
- Prevents accidental omissions
- Allows progressive state updates

**Implementation:**
```yaml
# Required
required:
  - id
  - status
  - created

# Optional (nullable: true)
fields:
  completed:
    type: datetime
    nullable: true
```

---

### Decision 5: Gate Model Representation

**Decision:** Quality gates are tasks with `task_type: "completion_gate"` or `"production_gate"`

**Gate Task Structure:**
```yaml
- id: "backend-1-gate-p001"
  task_type: "production_gate"
  gate_info:
    blocks_status: "production_ready"
    threshold: 90
    score: 92
    is_blocking: true
```

**Rationale:**
- Unified task model (gates are just special tasks)
- Highly isolated (cannot be depended on by external sprints)
- Clear blocking semantics
- Reuses task workflow

**Alternative Considered:**
- Separate `completion_gates` and `production_gates` arrays - rejected as duplicative
- Gate tasks mixed with development tasks - accepted as simpler

**Validation Rules:**
```yaml
- rule: "if task_type == 'completion_gate' then gate_info must not be null"
- rule: "if task_type == 'production_gate' then gate_info.blocks_status must be 'production_ready'"
```

---

### Decision 6: Dependency Model - Three Dependency Types

**Decision:** Use structured dependency objects with type discrimination

**Dependency Types:**
1. **Development Gates** (`dependencies` on sprint/task): External dependencies that must complete before starting
2. **Completion Gates** (quality gate tasks): Hygiene checks blocking completion
3. **Production Gates** (quality gate tasks): Production readiness checks

**Dependency Structure:**
```yaml
dependencies:
  - type: "task"  # or "sprint", "external"
    target_id: "backend-1-task-001"
    target_status: "completed"
    reason: "Requires user schema"
    optional: false
```

**Auto-Computed Blockers:**
```yaml
blocked_by:
  - dependency_id: "backend-1-task-001"
    dependency_type: "task"
    current_status: "in_progress"
    required_status: "completed"
    blocking_since: "2025-01-20T09:00:00Z"
```

**Rationale:**
- Explicit dependency tracking
- Automatic blocker computation
- Clear reason for each dependency
- Supports optional dependencies

---

## Python Data Model Decisions

### Decision 1: Dataclasses vs Pydantic Models

**Decision:** Use Python dataclasses with manual validation (not Pydantic)

**Rationale:**
- **Zero external dependencies** - Dataclasses are built-in (Python 3.7+)
- **Framework requirement** - Minimizing dependencies is critical for a framework
- **Explicit validation** - Manual validation in `__post_init__` is transparent and debuggable
- **Sufficient for our use case** - Loading validated YAML from our own system, not untrusted input
- **No type coercion needed** - We control the data format
- **Performance** - No overhead from validation framework
- **Simplicity** - No magic, just Python

**Alternatives Considered:**

**Pydantic models** - rejected because:
- ❌ External dependency (would require `pip install pydantic`)
- ❌ Overkill for our use case (we'd use <20% of features)
- ❌ Automatic type coercion not needed (we control YAML format)
- ❌ JSON Schema generation not needed (we have custom YAML schemas)
- ✅ Would provide better error messages (marginal benefit)
- ✅ Would reduce boilerplate (but our validation is clear)

**attrs** - rejected as less standard than dataclasses

**When Pydantic WOULD be worth it:**
- Building REST APIs (FastAPI integration)
- Processing untrusted external data
- Heavy JSON serialization/deserialization
- Auto-generating OpenAPI documentation
- Complex nested validation with type coercion

**Our use case (doesn't need Pydantic):**
- Loading validated YAML from our roadmap system
- Creating objects programmatically in Python scripts
- Framework code (minimize dependencies)
- Type hints + manual validation is sufficient

**Implementation:**
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
        # Explicit validation with clear error messages
        if not self.id.startswith(f"{self.sprint_id}-"):
            raise ValueError(f"Task ID {self.id} must start with sprint ID {self.sprint_id}")

        if self.task_type == TaskType.DEVELOPMENT:
            if self.gate_info is not None:
                raise ValueError("Development tasks cannot have gate_info")
```

**Trade-offs:**
- ✅ Pro: Zero dependencies, framework-friendly
- ✅ Pro: Explicit, transparent validation
- ✅ Pro: No magic, easier to debug
- ✅ Pro: Existing implementation is solid
- ⚠️ Con: More verbose validation code
- ⚠️ Con: Manual datetime parsing from YAML

---

### Decision 2: Type Annotations - Strict with Optional

**Decision:** Use strict type annotations with `Optional` for nullable fields

**Examples:**
```python
from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass, field

@dataclass
class Sprint:
    # Required
    id: str
    status: SprintStatus
    created: datetime

    # Optional
    started: Optional[datetime] = None
    completed: Optional[datetime] = None
    deliverables: List[str] = field(default_factory=list)
```

**Rationale:**
- Type safety catches bugs at development time
- IDE autocomplete and type checking
- Clear contract for what can be None
- Static type checkers (mypy, pyright) validate types
- Self-documenting code

**Alternative Considered:**
- Loose typing with Any - rejected as unsafe
- No type hints - rejected as unPythonic

**Note:** Use `field(default_factory=list)` for mutable defaults, not `= []`

---

### Decision 3: Enums for Status and Type Values

**Decision:** Use string-based Enums for all status values and types

**Implementation:**
```python
from enum import Enum

class TaskStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    WONT_DO = "won't_do"

class TaskType(str, Enum):
    DEVELOPMENT = "development"
    COMPLETION_GATE = "completion_gate"
    PRODUCTION_GATE = "production_gate"
```

**Rationale:**
- Type safety (invalid values rejected)
- IDE autocomplete
- Serializes as strings in YAML/JSON
- Self-documenting code

**Configuration:**
```python
class Config:
    use_enum_values = True  # Serialize as "in_progress", not "TaskStatus.IN_PROGRESS"
```

---

### Decision 4: Nested Dataclasses vs Flat Dictionaries

**Decision:** Use nested dataclasses for complex fields

**Examples:**
```python
@dataclass
class GateInfo:
    """Quality gate configuration"""
    blocks_status: str
    threshold: int
    is_blocking: bool
    score: Optional[int] = None

    def __post_init__(self):
        """Validate gate info."""
        if self.blocks_status not in ["completed", "production_ready"]:
            raise ValueError("blocks_status must be 'completed' or 'production_ready'")
        if not 0 <= self.threshold <= 100:
            raise ValueError("Threshold must be between 0 and 100")

@dataclass
class Task:
    gate_info: Optional[GateInfo] = None

@dataclass
class Progress:
    """Progress tracking"""
    tasks_total: int
    tasks_completed: int
    completion_percent: int

@dataclass
class Sprint:
    progress: Progress
```

**Rationale:**
- Type safety for nested structures
- Reusable components
- Clear validation in `__post_init__`
- Self-documenting

**Alternative Considered:**
- Dict with TypedDict - rejected as less validation
- Flat structure with prefixes - rejected as less clear

---

### Decision 5: Validation in `__post_init__` for Business Logic

**Decision:** Implement validation logic in `__post_init__` methods

**Examples:**
```python
@dataclass
class Task:
    task_type: TaskType
    gate_info: Optional[GateInfo] = None
    id: str
    sprint_id: str

    def __post_init__(self):
        """Validate task data."""
        # Validate task ID is sprint-scoped
        if not self.id.startswith(f"{self.sprint_id}-"):
            raise ValueError(f"Task ID {self.id} must start with sprint ID {self.sprint_id}")

        # Validate task type and gate_info consistency
        if self.task_type == TaskType.DEVELOPMENT:
            if self.gate_info is not None:
                raise ValueError("Development tasks cannot have gate_info")
        else:  # completion_gate or production_gate
            if self.gate_info is None:
                raise ValueError("Quality gate tasks must have gate_info")

            # Validate gate type matches blocks_status
            if self.task_type == TaskType.COMPLETION_GATE:
                if self.gate_info.blocks_status != "completed":
                    raise ValueError("Completion gates must block 'completed' status")
```

**Rationale:**
- Enforces business rules at construction time
- Prevents invalid state from being created
- Clear error messages with context
- Centralized validation logic per class
- Explicit and debuggable

**Validation Categories:**
1. **Structural:** ID format, parent-child relationships
2. **Business Logic:** Gate requirements, status transitions
3. **Computed Fields:** Progress calculations, blocked flags
4. **Cross-field:** Dependencies between multiple fields

---

### Decision 6: Serialization - External Functions (Not Methods)

**Decision:** Use external serialization functions in separate module, not methods on dataclasses

**Rationale:**
- Dataclasses are for data structure, not behavior
- Serialization logic belongs in `serialization/` module
- Cleaner separation of concerns
- Already implemented in `framework/roadmap/serialization/`

**Implementation:**
```python
# framework/roadmap/serialization/yaml_dumper.py
from framework.roadmap.models import Task
import yaml

def save_task(task: Task, file_path: Path) -> None:
    """Save task to YAML file."""
    task_dict = _task_to_dict(task)  # Convert dataclass to dict
    data = {'task': task_dict}  # Wrap in top-level key
    with open(file_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

# framework/roadmap/serialization/yaml_loader.py
def load_task(file_path: Path) -> Task:
    """Load task from YAML file."""
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
    task_data = data['task']
    return _task_from_dict(task_data)  # Convert dict to Task
```

**Existing Implementation:**
- `framework/roadmap/serialization/yaml_loader.py` - Load functions
- `framework/roadmap/serialization/yaml_dumper.py` - Save functions
- Handles datetime parsing, enum conversion, nested objects

**Alternative Considered:**
- Methods on dataclasses (`task.to_yaml()`) - rejected to keep dataclasses pure
- Direct YAML usage in scripts - rejected as inconsistent

---

## Validation Strategy

### Three-Tier Validation

**Tier 1: Type Validation (Python Type Hints + mypy)**
- Static type checking at development time
- Runtime type hints for documentation
- No automatic runtime validation (dataclasses don't enforce types)

**Tier 2: Business Logic Validation (`__post_init__`)**
- Runs automatically on dataclass instantiation
- Cross-field validation
- Status transition rules
- ID format validation
- Required field checks

**Tier 3: Schema Validation (Optional)**
- Validate against YAML schema files
- Useful for external data sources
- Can be disabled for performance
- Implemented in `framework/roadmap/validation/`

### Validation Error Handling

```python
try:
    task = Task(**data)
except ValueError as e:
    # Clear error message from __post_init__
    print(f"Validation error: {e}")
```

**Error Message Examples:**
```
ValueError: Task ID backend-1-task-001 must start with sprint ID backend-2
ValueError: Development tasks cannot have gate_info
ValueError: Completion gates must block 'completed' status
ValueError: Completed tasks must have a completion date
```

**Type Checking (Development Time):**
```bash
# Static type checking with mypy
mypy framework/roadmap/models/
```

---

## Serialization Approach

### YAML Format - Wrapped Objects

**Decision:** Wrap objects in top-level key matching object type

**Examples:**
```yaml
# task.yaml
task:
  id: "backend-1-task-001"
  status: "completed"
  # ...

# sprint.yaml
sprint:
  id: "backend-1"
  status: "in_progress"
  # ...
```

**Rationale:**
- Makes file type explicit
- Prevents accidental object type confusion
- Matches existing framework conventions
- Easier to merge/validate

### DateTime Serialization

**Decision:** ISO 8601 format with timezone

**Format:** `2025-01-20T09:00:00Z` or `2025-01-20T09:00:00+00:00`

**Implementation:**
```python
from datetime import datetime, timezone

class Task(BaseModel):
    created: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

---

## Performance Considerations

### Lazy Loading

**Decision:** Models are lightweight; lazy loading at file system level

**Rationale:**
- Models are cheap to instantiate
- Validation overhead is acceptable
- File I/O is the bottleneck, not model creation

### Caching Strategy

**Decision:** Cache validated objects, invalidate on file change

**Implementation:** Separate caching layer (not in models)

```python
# framework/scripts/roadmap-lib/cache.py
class RoadmapCache:
    def get_task(self, task_id: str) -> Task:
        # Check cache
        # Load from file if needed
        # Validate and cache
```

### Progress Calculation

**Decision:** Store progress in YAML, recompute on update

**Rationale:**
- Progress is derived state
- Must be consistent across reads
- Small performance cost on update
- Large performance gain on read

---

## Future Extensibility

### Plugin System (Future)

Models designed to support future plugin extensions:

```python
class Task(BaseModel):
    # Core fields
    id: str
    status: TaskStatus

    # Extension point
    extensions: Optional[Dict[str, Any]] = None

    class Config:
        extra = "allow"  # Allow additional fields
```

### Custom Validators (Future)

Support for user-defined validation rules:

```python
# User can register custom validators
from framework.roadmap.validation import register_validator

@register_validator('task', 'custom_rule')
def my_custom_rule(task: Task) -> bool:
    # Custom validation logic
    return True
```

### State Machine (Future)

Models prepared for future state machine integration:

```python
class Sprint(BaseModel):
    status: SprintStatus

    def can_transition_to(self, new_status: SprintStatus) -> bool:
        """Check if status transition is valid"""
        # Future: state machine logic
        pass
```

---

## Migration Path

### Backward Compatibility

**Decision:** Support both legacy and new formats during transition

**Implementation:**
- Models can load from legacy YAML
- Serialization always uses new format
- Migration scripts convert old → new

### Deprecation Strategy

1. **v2.0:** New format introduced, legacy supported
2. **v2.1:** Legacy format deprecated (warnings)
3. **v2.2:** Legacy format removed

---

## Dependencies

### Required Python Packages

```python
# pyproject.toml or requirements.txt
# NO EXTERNAL DEPENDENCIES for core models!
# Built-in packages only:
# - dataclasses (Python 3.7+)
# - typing (Python 3.5+)
# - datetime (built-in)
# - enum (built-in)

# Only for serialization (separate module):
pyyaml>=6.0           # YAML serialization
python-dateutil>=2.8.0 # DateTime parsing (optional, can use datetime.fromisoformat)
```

### Optional Packages

```python
# Development/testing
pytest>=7.0.0
pytest-cov>=4.0.0
mypy>=1.0.0           # Static type checking
```

### Why Zero Core Dependencies?

**Decision Rationale:**
- Framework code should minimize external dependencies
- Dataclasses are built-in to Python 3.7+
- Users don't need to `pip install` anything for core models
- Reduces dependency conflicts
- Makes framework more portable

---

## Testing Strategy

### Unit Tests

- Test each model in isolation
- Test all validators
- Test serialization round-trips
- Test error cases

### Integration Tests

- Test full object hierarchies
- Test file I/O
- Test migration scenarios

### Property-Based Tests (Future)

```python
from hypothesis import given
from hypothesis.strategies import text

@given(text())
def test_task_id_validation(task_id: str):
    # Property: invalid IDs always raise ValidationError
    pass
```

---

## Documentation

### Docstrings

All models, fields, and validation methods have docstrings:

```python
@dataclass
class Task:
    """
    Context-window sized work unit within a sprint.

    Tasks are the smallest unit of work in the roadmap system.
    They are sized to fit within a model's context window and
    have no production concerns.
    """

    id: str  # Sprint-scoped task ID (e.g., backend-1-task-001)
    status: TaskStatus  # Current task status

    def __post_init__(self):
        """Validate task data on instantiation."""
        # Validation logic with clear comments
```

### Type Hints as Documentation

Type hints serve as inline documentation:

```python
@dataclass
class Task:
    gate_info: Optional[GateInfo] = None  # None for development tasks
    dependencies: List[TaskDependency] = field(default_factory=list)
    created: datetime  # ISO 8601 format
```

---

## References

- **Design Document:** `docs/development/ROADMAP_OBJECT_HIERARCHY.md`
- **Implementation Plan:** `docs/development/ROADMAP_IMPLEMENTATION_PLAN.md`
- **YAML Schemas:** `framework/roadmap/schema/*.schema.yaml`
- **Python Models:** `framework/roadmap/models/*.py`
- **Pydantic Docs:** https://docs.pydantic.dev/

---

## Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-11-09 | Initial design decisions | Vibey Framework Team |

---

**Document Status:** ✅ Complete
**Implementation Status:** 🚧 In Progress (Sprint 1)
**Next Review:** After Sprint 1 completion
