# Architecture: Config-Driven Framework

## Design Decisions

### Decision 1: YAML for Configuration

**Choice:** Use YAML files instead of JSON or Python dicts
**Rationale:**
- Human-readable and editable
- Comments supported
- Standard in DevOps tooling
- Easy schema validation

### Decision 2: Modular Config Files

**Choice:** Separate files (project, framework, agents, quality-gates)
**Rationale:**
- Clear separation of concerns
- Easier to maintain
- Can update one without touching others
- Better for version control (smaller diffs)

### Decision 3: Config Parser as Separate Module

**Choice:** Standalone Python module, not integrated into main code
**Rationale:**
- Reusable across different Vibey components
- Easier to test
- Could be extracted to separate package
- Clear interface boundary

## Key Interfaces

### Config Loader

```python
from vibey_config import load_config

# Load all configs
config = load_config('.vibey/config/')

# Access specific configs
project = config.project
framework = config.framework
agents = config.agents
```

### Validation

```python
from vibey_config import validate_config

# Validate with schema
errors = validate_config('.vibey/config/project.yaml')
if errors:
    print(f"Validation failed: {errors}")
```

## Critical Gotchas

### 1. YAML Anchors and References

**Problem:** YAML allows anchors (&) and references (*) which can be confusing
**Solution:** Keep configs simple, avoid complex YAML features

### 2. Type Coercion

**Problem:** YAML auto-converts values (yes/no → boolean, numbers → int/float)
**Solution:** Explicit type validation in schema

### 3. Circular Imports

**Problem:** Config module might be imported by many components
**Solution:** Keep config module dependency-free (only PyYAML)
