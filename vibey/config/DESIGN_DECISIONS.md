# Config System Design Decisions

**Version:** 1.0
**Date:** 2025-11-10
**Sprint:** directory-migration-2
**Status:** Implemented (Task 002)

---

## Executive Summary

This document captures design decisions for the Vibey configuration system, specifically addressing the choice to use **Pydantic** for config validation, which differs from the roadmap system's use of dataclasses.

**Key Design Principles:**
- ✅ Strong validation for user-provided data (untrusted input)
- ✅ Rich error messages for configuration mistakes
- ✅ Type safety and IDE support
- ✅ Clean YAML serialization
- ✅ Acceptable dependency for user-facing config (not framework internals)

**Important Note:**
This design decision was reviewed and the recommendation is to **NOT migrate the roadmap system to Pydantic**. The different approaches (Pydantic for config, dataclasses for roadmap) are intentional and justified by different requirements. See the "Should We Standardize?" section below for details.

---

## Critical Design Decision: Pydantic vs Dataclasses

### Decision: Use Pydantic for Config System (Different from Roadmap System)

**Context:**
The roadmap system (vibey/roadmap/) uses dataclasses with manual validation to avoid external dependencies. This decision was documented in `vibey/roadmap/DESIGN_DECISIONS.md` (lines 230-297).

**Question:**
Should the config system follow the same pattern (dataclasses) or use Pydantic?

**Decision:** **Use Pydantic for config validation**

---

## Rationale for Pydantic in Config System

### Different Use Cases Require Different Tools

**Roadmap System (Dataclasses):**
- **Data Source:** Framework-controlled YAML files
- **Trust Level:** Trusted (created by framework scripts)
- **Validation Needs:** Business logic, relationships, state transitions
- **Audience:** Framework internals
- **Dependency Concern:** CRITICAL (framework must minimize dependencies)
- **Decision:** Dataclasses with manual validation ✅

**Config System (Pydantic):**
- **Data Source:** User-written YAML files
- **Trust Level:** Untrusted (users make mistakes)
- **Validation Needs:** Type coercion, rich error messages, nested validation
- **Audience:** User-facing (developers using Vibey)
- **Dependency Concern:** ACCEPTABLE (users already install framework)
- **Decision:** Pydantic for robust validation ✅

---

## Pydantic Benefits for Config System

### 1. User-Facing Validation

Config files are written by users who make mistakes:

**Bad Config (Common User Errors):**
```yaml
# config/project.yaml
project:
  name: "my-app"
  version: "1.0"        # ❌ Invalid: should be "1.0.0"
  type: "webapp"        # ❌ Invalid: should be "web-app"

tech_stack:
  languages: python     # ❌ Invalid: should be array ["python"]
```

**Pydantic Error Messages (Helpful):**
```
3 validation errors for ProjectConfig
project.version
  String should match pattern '^\d+\.\d+\.\d+$' [type=string_pattern_mismatch]

project.type
  Input should be 'web-app', 'api', 'library', 'ml', 'data-platform', or 'infrastructure' [type=enum]

tech_stack.languages
  Input should be a valid list [type=list_type]
```

**Dataclass Errors (Less Helpful):**
```
ValueError: Invalid version format
AttributeError: 'str' object has no attribute 'append'
```

### 2. Type Coercion

Users often provide valid data in wrong format:

```yaml
project:
  version: 1.0          # Number instead of string

tech_stack:
  languages: "python"   # String instead of list
```

**Pydantic:** Coerces to correct type or provides clear error
**Dataclasses:** Type hints are documentation only, no runtime enforcement

### 3. Nested Validation

Config has deep nesting with complex rules:

```python
class QualityGatesConfig(BaseModel):
    gates: Gates

class Gates(BaseModel):
    security: SecurityGate
    testing: TestingGate

class SecurityGate(BaseModel):
    threshold: int = Field(ge=0, le=100)
    checks: List[str]

    @validator('threshold')
    def validate_threshold(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Threshold must be 0-100')
        return v
```

Pydantic validates all levels automatically with clear error paths.

### 4. Enum Serialization

**Problem with Dataclasses:**
```python
@dataclass
class ProjectConfig:
    project_type: ProjectType  # Enum
```

When saving to YAML:
```yaml
type: !!python/object/apply:vibey.config.models.ProjectType
- web-app
```

This creates Python-specific tags that can't be loaded by yaml.safe_load()!

**Solution with Pydantic:**
```python
class ProjectType(str, Enum):
    WEB_APP = "web-app"
```

Clean serialization:
```yaml
type: web-app
```

### 5. Schema Validation

Pydantic provides built-in JSON Schema generation:

```python
config_schema = ProjectConfig.model_json_schema()
# Can be used for IDE autocomplete, documentation generation, etc.
```

---

## Trade-offs Analysis

### Pydantic for Config System

✅ **Advantages:**
- Rich validation error messages (critical for users)
- Automatic type coercion (handles common mistakes)
- Nested model validation (complex config structures)
- Clean enum serialization (no Python tags)
- JSON Schema generation (tooling support)
- Wide adoption (FastAPI, many tools use it)
- Excellent documentation and community support

⚠️ **Disadvantages:**
- External dependency (requires `pip install pydantic`)
- Slightly larger package size (~500KB)
- Some "magic" (automatic coercion, validators)

### Dataclasses for Config System (Rejected)

✅ **Advantages:**
- No external dependencies (built-in)
- Explicit validation (manual __post_init__)
- Lighter weight

❌ **Disadvantages:**
- Poor error messages for user mistakes
- No type coercion (users must get types exactly right)
- Manual nested validation (lots of boilerplate)
- Enum serialization requires custom code
- No schema generation

---

## Why Different from Roadmap System?

### Different Requirements

| Aspect | Roadmap System | Config System |
|--------|---------------|---------------|
| **Data Source** | Framework scripts | User YAML files |
| **Trust Level** | Trusted | Untrusted |
| **Error Tolerance** | Bugs are framework bugs | Bugs are user mistakes |
| **Error Messages** | Stack traces OK | Must be user-friendly |
| **Dependency Impact** | Framework core | User-facing tool |
| **Validation Needs** | Business logic | Type safety + UX |

### Consistent Principle: Right Tool for Job

**Framework Principle:** Choose tools based on use case, not dogma

- **Roadmap system:** Framework-internal → dataclasses (zero deps) ✅
- **Config system:** User-facing → Pydantic (better UX) ✅
- **CLI commands:** User-facing → Click (better UX) ✅
- **Terminal output:** User-facing → Rich (better UX) ✅

All user-facing components prioritize UX and accept dependencies.
All framework-internal components minimize dependencies.

---

## Implementation Details

### Custom YAML Serializer

To avoid Python-specific tags, we use a custom serializer:

```python
def _serialize_for_yaml(data: Any) -> Any:
    """
    Recursively convert Pydantic models and enums to plain Python types.

    This ensures clean YAML serialization without Python-specific tags.
    """
    if isinstance(data, dict):
        return {k: _serialize_for_yaml(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_serialize_for_yaml(item) for item in data]
    elif isinstance(data, Enum):
        return data.value
    else:
        return data
```

### Clean Serialization

```python
def to_yaml(self, path: str | Path) -> None:
    """Save configuration to YAML file."""
    data = self.model_dump(mode='python', exclude_none=True)
    serialized = _serialize_for_yaml(data)  # Convert enums to strings
    with open(path, 'w') as f:
        yaml.dump(serialized, f, default_flow_style=False, sort_keys=False)
```

Result:
```yaml
# Clean, portable YAML
project:
  type: web-app
framework:
  orchestration_mode: balanced
quality_gates:
  mode: balanced
```

---

## Dependency Management

### pyproject.toml

```toml
dependencies = [
    "pyyaml>=6.0",
    "jinja2>=3.1.0",
    "click>=8.1.0",      # CLI framework (user-facing)
    "rich>=13.0.0",      # Terminal output (user-facing)
    "pydantic>=2.0.0",   # Config validation (user-facing)
]
```

### Rationale for Each Dependency

1. **PyYAML** - Required (YAML is core data format)
2. **Jinja2** - Required (template rendering)
3. **Click** - User-facing (better CLI UX than argparse)
4. **Rich** - User-facing (better terminal output)
5. **Pydantic** - User-facing (better config validation UX)

All dependencies are for **user-facing** features, not framework internals.

---

## Backward Compatibility

### Migration from Legacy Config

The old `.claude/project-config.yaml` will be migrated using the Pydantic models:

```python
# Load legacy config
with open('.claude/project-config.yaml') as f:
    legacy_data = yaml.safe_load(f)

# Validate and migrate using Pydantic
try:
    project_config = ProjectConfig(**extract_project_fields(legacy_data))
    framework_config = FrameworkConfig(**extract_framework_fields(legacy_data))
    # ... etc

    # Save to new format
    project_config.to_yaml('.vibey/config/project.yaml')
    framework_config.to_yaml('.vibey/config/framework.yaml')

except ValidationError as e:
    print(f"❌ Invalid legacy config: {e}")
    # Show user-friendly error messages
```

Pydantic's validation ensures that only valid configs are migrated.

---

## When to Use Each Approach

### Use Dataclasses When:
- Framework-internal data structures
- Data is trusted (created by framework)
- Zero dependencies is critical
- Business logic validation is primary concern
- **Example:** Roadmap system models

### Use Pydantic When:
- User-facing configuration
- Data is untrusted (user input)
- Rich error messages are important
- Type coercion helps UX
- Nested validation is complex
- **Example:** Config system models

---

## Should We Standardize on One Approach?

### Question: Should we migrate the roadmap system to Pydantic for consistency?

**Answer: NO - Keep both approaches**

This question was explicitly reviewed and the recommendation is to **NOT migrate** the roadmap system to Pydantic.

### Analysis

**Current State:**
- **Roadmap system:** 31 dataclasses, ~1,500 lines of model code, ~8,000 lines total
- **Config system:** 15 Pydantic models, ~400 lines of model code

**Cost of Migration:**
- **Development time:** 2-3 days
- **Added dependency:** Pydantic becomes hard requirement for framework core
- **Risk:** Introducing bugs in working, tested code
- **Testing effort:** Rewrite 20+ tests
- **Refactoring scope:** 31 dataclasses + serialization layer

**Benefit of Migration:**
- **Consistency:** Single validation approach
- **Less custom code:** Pydantic handles serialization
- **Better type validation:** Runtime type enforcement

**Net Benefit: NEGATIVE ❌**

### Recommendation: Keep Both Approaches

**Rationale:**

1. **No User-Facing Benefit**
   - Roadmap YAML files are created by framework scripts, not users
   - Rich error messages not needed (data is trusted)
   - Current validation works correctly

2. **Framework Principle Violation**
   - Roadmap is framework internals → should minimize dependencies
   - Adding Pydantic would be dependency creep
   - Violates "minimal dependencies for core" principle

3. **Large Effort, Zero Gain**
   - 2-3 days of refactoring
   - No functional improvement
   - Risk of introducing bugs
   - Current implementation works correctly

4. **Intentional Diversity, Not a Problem**
   - Different requirements justify different tools
   - Config (user-facing) → Pydantic ✅
   - Roadmap (framework core) → Dataclasses ✅
   - This is **"right tool for the job"**, not inconsistency

### Cost-Benefit Table

| Aspect | Cost | Benefit |
|--------|------|---------|
| Development Time | 2-3 days | None (already works) |
| Dependencies | +1 hard dependency | None |
| Code Complexity | -100 lines validation<br>+50 lines config | Marginal |
| User Experience | No change | None |
| Risk | Bugs in working code | None |
| Testing | Rewrite 20+ tests | None |

### Conclusion

**"Consistency for consistency's sake is not a virtue"**

The framework's principle of **"right tool for the job"** means intentionally using different approaches for different requirements:

- **Config system** (user-facing) → Pydantic for better UX ✅
- **Roadmap system** (framework core) → Dataclasses for zero deps ✅

This is **intentional design diversity**, not a problem requiring standardization.

### Documentation Instead of Migration

Instead of migrating, we:
1. ✅ Documented the decision in `vibey/config/DESIGN_DECISIONS.md`
2. ✅ Added explanation to `vibey/roadmap/models/__init__.py`
3. ✅ Clarified when to use each approach
4. ✅ Explained framework principles

This prevents future confusion without unnecessary refactoring.

---

## Future Considerations

### Potential Issues

1. **Pydantic v3 Migration**
   - Pydantic may release breaking changes
   - **Mitigation:** Pin to `pydantic>=2.0.0,<3.0.0`

2. **Dependency Conflicts**
   - Users may have conflicting Pydantic versions
   - **Mitigation:** Use broad version range `>=2.0.0`

3. **Package Size**
   - Pydantic adds ~500KB to install
   - **Mitigation:** Acceptable for a dev tool

### Alternative Considered: attrs

**attrs** is a middle ground between dataclasses and Pydantic:

✅ Pros:
- Lighter than Pydantic
- More features than dataclasses
- Good validation support

❌ Cons:
- Less popular than Pydantic
- No automatic type coercion
- Smaller ecosystem

**Decision:** Pydantic's popularity and features outweigh attrs' lighter weight.

---

## Testing Strategy

### Validation Tests

```python
def test_invalid_version_format():
    """Test that invalid version format is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        ProjectConfig(**{
            'project': {'name': 'test', 'version': '1.0', 'type': 'web-app'},
            'tech_stack': {'languages': ['python']}
        })

    assert 'String should match pattern' in str(exc_info.value)
```

### Round-trip Tests

```python
def test_yaml_round_trip():
    """Test that configs can be saved and loaded."""
    config = ProjectConfig.from_yaml('examples/project.yaml')
    config.to_yaml('/tmp/test.yaml')
    loaded = ProjectConfig.from_yaml('/tmp/test.yaml')
    assert config == loaded
```

### Enum Serialization Tests

```python
def test_enum_serialization():
    """Test that enums serialize as plain strings."""
    config = ProjectConfig(...)
    config.to_yaml('/tmp/test.yaml')

    with open('/tmp/test.yaml') as f:
        content = f.read()

    # No Python tags
    assert '!!python' not in content
    # Clean enum values
    assert 'type: web-app' in content
```

---

## Documentation

All models include comprehensive docstrings:

```python
class ProjectConfig(BaseModel):
    """
    Project configuration model.

    This model validates project-specific settings including:
    - Project metadata (name, version, type)
    - Technology stack (languages, frameworks, databases)
    - Directory paths (source, tests, docs)

    Example:
        config = ProjectConfig.from_yaml('.vibey/config/project.yaml')
        print(f"Project: {config.project.name} v{config.project.version}")
    """
```

---

## Conclusion

**Decision Summary:**

1. **Roadmap System:** Uses dataclasses (zero dependencies for framework internals) ✅
2. **Config System:** Uses Pydantic (better UX for user-facing validation) ✅

These are **different decisions for different use cases**, not a conflict.

**Framework Principle:**
> Choose the right tool for the job. Minimize dependencies for framework internals,
> prioritize UX for user-facing features.

---

## References

- **Roadmap Design Decisions:** `vibey/roadmap/DESIGN_DECISIONS.md` (lines 230-297)
- **Pydantic Documentation:** https://docs.pydantic.dev/
- **Config Models Implementation:** `vibey/config/models.py`
- **Config Schema Design:** `vibey/config/schemas/README.md`

---

## Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-11-10 | Initial design decisions documenting Pydantic choice | Vibey Team |

---

**Document Status:** ✅ Complete
**Implementation Status:** ✅ Complete (Task 002)
**Next Review:** After Sprint 2 completion
