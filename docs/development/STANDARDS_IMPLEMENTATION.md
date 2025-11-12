# Standards System Implementation

**Developer Guide for Architecture and Extension**

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Core Components](#core-components)
- [Data Model](#data-model)
- [Standards Resolution](#standards-resolution)
- [Validation Framework](#validation-framework)
- [Enforcement Integration](#enforcement-integration)
- [Template System](#template-system)
- [CLI Commands](#cli-commands)
- [Extending the System](#extending-the-system)
- [Testing](#testing)
- [Performance Considerations](#performance-considerations)

---

## Architecture Overview

The Standards System follows a layered architecture:

```
┌─────────────────────────────────────────────────┐
│           CLI Layer (Commands)                   │
│  list-templates, add-from-template,             │
│  check-standards, override-standard              │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│      Operations Layer (Enforcement)              │
│  enforce_standards(), complete_task(),           │
│  complete_sprint()                               │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│    Standards Resolution (Hierarchical)           │
│  StandardsResolver, resolve_for_task(),          │
│  resolve_for_sprint(), resolve_for_track()       │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│    Validation Framework (Validators)             │
│  ValidatorBase, ValidatorRegistry,               │
│  CommitCheckValidator, FileCheckValidator,       │
│  TestRunValidator, CustomScriptValidator         │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│         Data Model (Standards)                   │
│  Standard, StandardType, EnforcementMode,        │
│  StandardOverride, ValidationResult              │
└──────────────────────────────────────────────────┘
```

### Design Principles

1. **Hierarchical Resolution** - Standards cascade from roadmap → track → sprint → task
2. **Pluggable Validators** - Easy to add new validation types
3. **Separation of Concerns** - Resolution, validation, and enforcement are separate
4. **Override Mechanism** - Escape hatch with full audit trail
5. **Performance** - Lazy loading, caching where appropriate

---

## Core Components

### 1. Data Model (`vibey/roadmap/models/standard.py`)

Defines core data structures:

```python
@dataclass
class Standard:
    """A quality standard that can be applied to roadmap items."""
    id: str
    name: str
    description: str
    type: StandardType
    enforcement: EnforcementMode
    validation: Dict[str, Any]
    enabled: bool = True
    created: datetime
    overrides: List[StandardOverride] = field(default_factory=list)
```

**Key Methods:**
- `add_override()` - Add override for specific item
- `has_override_for()` - Check if override exists
- `get_override_for()` - Retrieve override details
- `has_overrides()` - Check if any overrides exist

### 2. Standards Resolver (`vibey/roadmap/standards/resolver.py`)

Resolves which standards apply to an item:

```python
class StandardsResolver:
    """Resolves effective standards for roadmap items."""

    def resolve_for_task(self, task_id: str) -> List[Standard]:
        """Get all standards that apply to a task."""
        # 1. Load roadmap standards
        # 2. Load track standards
        # 3. Load sprint standards
        # 4. Deduplicate by ID (lowest level wins)
        # 5. Return merged list
```

**Resolution Algorithm:**
1. Extract hierarchy IDs from item ID (task → sprint → track)
2. Load standards from each level (roadmap, track, sprint)
3. Merge with deduplication (sprint overrides track overrides roadmap)
4. Return effective standards list

### 3. Validator Framework (`vibey/roadmap/standards/validators/`)

Pluggable validation system:

```python
class ValidatorBase(ABC):
    """Base class for all standard validators."""

    @abstractmethod
    def validate(self, standard: Standard, item_id: str, root_dir: Path) -> ValidationResult:
        """Validate a standard for an item."""
        pass

    @abstractmethod
    def get_supported_type(self) -> StandardType:
        """Return the standard type this validator handles."""
        pass
```

**Built-in Validators:**
- `CommitCheckValidator` - Validates git commits
- `FileCheckValidator` - Validates file modifications
- `TestRunValidator` - Runs tests and checks coverage
- `CustomScriptValidator` - Runs custom validation scripts

### 4. Enforcement Integration (`vibey/operations/roadmap/standards_enforcement.py`)

Integrates validation into completion workflow:

```python
def enforce_standards(
    item_id: str,
    root_dir: Path,
    operation: str = "complete"
) -> EnforcementResult:
    """
    Enforce standards for a roadmap item.

    Returns:
        EnforcementResult with:
        - can_proceed: bool
        - blocking_failures: List[ValidationResult]
        - warnings: List[ValidationResult]
        - passed: List[ValidationResult]
    """
```

**Enforcement Flow:**
1. Resolve standards for item
2. Check overrides (skip if override exists)
3. Run validators
4. Categorize by enforcement mode
5. Return EnforcementResult

---

## Data Model

### Standard

```python
@dataclass
class Standard:
    id: str                          # Unique identifier
    name: str                        # Display name
    description: str                 # What this standard checks
    type: StandardType               # commit_check, file_check, test_run, custom_script
    enforcement: EnforcementMode     # blocking, warning, audit
    validation: Dict[str, Any]       # Type-specific validation config
    enabled: bool                    # Can be disabled without removing
    created: datetime                # When standard was created
    overrides: List[StandardOverride]  # Override audit trail
```

### StandardType

```python
class StandardType(str, Enum):
    COMMIT_CHECK = "commit_check"       # Check git commits
    FILE_CHECK = "file_check"           # Check file modifications
    TEST_RUN = "test_run"               # Run tests
    CUSTOM_SCRIPT = "custom_script"     # Custom validation script
```

### EnforcementMode

```python
class EnforcementMode(str, Enum):
    BLOCKING = "blocking"   # Prevents completion if fails
    WARNING = "warning"     # Shows warning, allows completion
    AUDIT = "audit"         # Logs only, no enforcement
```

### StandardOverride

```python
@dataclass
class StandardOverride:
    target_id: str          # Task/sprint/track ID
    reason: str             # Why override was needed
    overridden_by: str      # Who created override
    created: datetime       # When override was created
    expires: Optional[datetime]  # Optional expiration
```

### ValidationResult

```python
@dataclass
class ValidationResult:
    standard_id: str
    status: ValidationStatus  # PASSED, FAILED, SKIPPED, ERROR
    message: str
    details: Optional[str]
```

---

## Standards Resolution

### Hierarchical Inheritance

Standards cascade through the hierarchy:

```python
# Example: Resolving standards for task-id-001

1. Load roadmap.yaml
   standards: [commit-required, multi-platform-testing]

2. Extract track ID from task ID: "backend"
   Load .vibey/roadmap/backend/track.yaml
   standards: [test-coverage-required, doc-review-required]

3. Extract sprint ID from task ID: "backend-1"
   Load .vibey/roadmap/backend/backend-1/sprint.yaml
   standards: [security-review]

4. Merge and deduplicate:
   Effective standards: [
     commit-required (roadmap),
     multi-platform-testing (roadmap),
     test-coverage-required (track),
     doc-review-required (track),
     security-review (sprint)
   ]
```

### Deduplication Logic

When same standard ID appears at multiple levels:

```python
# Lower level (closer to task) wins
roadmap_standards = [Standard(id="test-cov", enforcement=BLOCKING)]
track_standards = [Standard(id="test-cov", enforcement=WARNING)]

# After deduplication:
effective_standards = [Standard(id="test-cov", enforcement=WARNING)]
# Track-level WARNING overrides roadmap-level BLOCKING
```

### ID Extraction

```python
def _extract_ids_from_item_id(item_id: str) -> Tuple[str, str, str]:
    """
    Extract roadmap, track, and sprint IDs from item ID.

    Examples:
        backend-1-task-001 → (roadmap_id, "backend", "backend-1")
        backend-1 → (roadmap_id, "backend", "backend-1")
        backend → (roadmap_id, "backend", None)
    """
```

---

## Validation Framework

### Creating a Validator

```python
from vibey.roadmap.standards.validators import ValidatorBase, ValidationStatus, ValidationResult
from vibey.roadmap.models import Standard, StandardType

class MyCustomValidator(ValidatorBase):
    """Validates custom project requirements."""

    def get_supported_type(self) -> StandardType:
        return StandardType.CUSTOM_SCRIPT

    def validate(
        self,
        standard: Standard,
        item_id: str,
        root_dir: Path
    ) -> ValidationResult:
        """Run validation logic."""
        try:
            # Your validation logic here
            validation_passed = self._check_requirements(standard, item_id, root_dir)

            if validation_passed:
                return ValidationResult(
                    standard_id=standard.id,
                    status=ValidationStatus.PASSED,
                    message="Validation passed",
                    details=None
                )
            else:
                return ValidationResult(
                    standard_id=standard.id,
                    status=ValidationStatus.FAILED,
                    message="Validation failed",
                    details="Specific failure reason"
                )
        except Exception as e:
            return ValidationResult(
                standard_id=standard.id,
                status=ValidationStatus.ERROR,
                message=f"Validation error: {str(e)}",
                details=None
            )

    def _check_requirements(self, standard, item_id, root_dir):
        # Implement your validation logic
        pass
```

### Registering a Validator

```python
from vibey.roadmap.standards.validators import ValidatorRegistry

# Create registry
registry = ValidatorRegistry()

# Register your validator
registry.register(MyCustomValidator())

# Use registry
results = registry.validate_all(standards, item_id)
```

### Validator Best Practices

1. **Fail Fast** - Return early on errors
2. **Clear Messages** - Provide actionable error messages
3. **Safe Execution** - Catch exceptions, don't crash
4. **Idempotent** - Running twice should give same result
5. **Performance** - Cache results when possible

---

## Enforcement Integration

### Complete Task Flow

```python
def complete_task(root_dir: Path, task_id: str, completed_by: str) -> int:
    """Complete a task with standards enforcement."""

    # 1. Enforce standards
    enforcement_result = enforce_standards(task_id, root_dir, operation="complete")

    # 2. Print results
    print_enforcement_results(enforcement_result, task_id, verbose=False)

    # 3. Check if can proceed
    if not enforcement_result.can_proceed:
        failure_summary = get_failure_summary(enforcement_result)
        print(f"\n❌ Cannot complete task: {failure_summary}")
        print(f"   Use 'vibey roadmap override-standard' to override blocking standards")
        return 1  # Failure

    # 4. Show warnings (if any)
    if enforcement_result.warnings:
        print(f"\n⚠️  Task has warnings but will proceed with completion")

    # 5. Proceed with normal completion
    # ... rest of completion logic ...

    return 0  # Success
```

### Categorization by Enforcement Mode

```python
# After validation, categorize results
for result in validation_results:
    standard = find_standard_by_id(result.standard_id, resolved_standards)
    enforcement_mode = standard.enforcement

    if result.status == ValidationStatus.PASSED:
        passed.append(result)
    elif result.status == ValidationStatus.SKIPPED:
        skipped.append(result)
    elif result.status in (ValidationStatus.FAILED, ValidationStatus.ERROR):
        if enforcement_mode == EnforcementMode.BLOCKING:
            blocking_failures.append(result)
        else:  # WARNING or AUDIT
            warnings.append(result)

# Can proceed only if no blocking failures
can_proceed = len(blocking_failures) == 0
```

---

## Template System

### Template Format

Templates are YAML files in `vibey/roadmap/standards/templates/`:

```yaml
template:
  id: my-template
  name: My Template
  description: What this template checks
  type: commit_check
  enforcement: blocking

  validation:
    min_commits: 1

  use_case: |
    Explanation of when to use this template

  typical_level: roadmap

  examples:
    - level: roadmap
      scenario: Organization-wide
      description: All tasks need commits

  override_scenarios:
    - reason: Emergency hotfix
      justification: Critical fix, tests added later

  configuration:
    min_commits:
      description: Minimum commits required
      type: integer
      default: 1
```

### Loading Templates

```python
from vibey.roadmap.standards.templates import load_template

# Load with defaults
standard = load_template('commit-required')

# Load with overrides
standard = load_template(
    'commit-required',
    id='my-commit-check',
    enforcement='warning',
    validation={'min_commits': 2}
)
```

### Creating New Templates

1. Create YAML file in `vibey/roadmap/standards/templates/`
2. Follow template format above
3. Document use cases and configuration
4. Add examples and override scenarios
5. Test template loading and validation

---

## CLI Commands

### Architecture

CLI commands follow this pattern:

```python
# vibey/cli/roadmap_commands/my_command.py

def handle_my_command(args):
    """Handle 'roadmap my-command' command."""
    # 1. Parse arguments
    root_dir = Path(args.dir) if args.dir else Path.cwd()

    # 2. Perform operation
    try:
        result = perform_operation(root_dir, args)
    except Exception as e:
        print(f"❌ Failed: {e}")
        return 1

    # 3. Display results
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_human_readable(result)

    return 0  # Success
```

### Registering Commands

In `vibey/cli/roadmap`:

```python
# Add argument parser
my_command_parser = subparsers.add_parser('my-command', help='Description')
my_command_parser.add_argument('arg1', type=str, help='Argument 1')
my_command_parser.add_argument('--flag', action='store_true', help='Optional flag')

# Add command handler
elif args.command == 'my-command':
    from roadmap_commands.my_command import handle_my_command
    handle_my_command(args)

# Add to cache invalidation list (if state-changing)
if cache and args.command in ['...',  'my-command']:
    cache.invalidate()
```

---

## Extending the System

### Adding a New Standard Type

1. **Add enum value:**
```python
# vibey/roadmap/models/standard.py
class StandardType(str, Enum):
    # ... existing types ...
    MY_NEW_TYPE = "my_new_type"
```

2. **Create validator:**
```python
# vibey/roadmap/standards/validators/my_validator.py
class MyNewTypeValidator(ValidatorBase):
    def get_supported_type(self) -> StandardType:
        return StandardType.MY_NEW_TYPE

    def validate(self, standard, item_id, root_dir) -> ValidationResult:
        # Validation logic
        pass
```

3. **Register validator:**
```python
# vibey/roadmap/standards/validators/__init__.py
from .my_validator import MyNewTypeValidator

def create_default_registry(root_dir: str) -> ValidatorRegistry:
    registry = ValidatorRegistry()
    # ... existing validators ...
    registry.register(MyNewTypeValidator())
    return registry
```

4. **Create template (optional):**
```yaml
# vibey/roadmap/standards/templates/my-template.yaml
template:
  id: my-template
  type: my_new_type
  # ... template config ...
```

5. **Write tests:**
```python
# tests/unit/test_my_validator.py
def test_my_validator():
    validator = MyNewTypeValidator()
    result = validator.validate(standard, item_id, root_dir)
    assert result.status == ValidationStatus.PASSED
```

### Adding Custom Validation Logic

For project-specific needs without modifying Vibey:

**Option 1: Use CustomScriptValidator**
```bash
vibey roadmap add-standard roadmap \
  my-check \
  "My Custom Check" \
  "Project-specific validation" \
  custom_script \
  blocking \
  '{"script": "#!/bin/bash\n# Your validation\nexit 0"}'
```

**Option 2: Extend in User Code**
```python
# my_project/standards/my_validator.py
from vibey.roadmap.standards.validators import ValidatorBase

class MyProjectValidator(ValidatorBase):
    # Your custom validator
    pass

# Register before running enforcement
from vibey.roadmap.standards.validators import create_default_registry
registry = create_default_registry(root_dir)
registry.register(MyProjectValidator())
```

---

## Testing

### Unit Tests

Test individual components in isolation:

```python
# tests/unit/test_standard_model.py
def test_standard_add_override():
    standard = Standard(
        id="test-standard",
        # ... other fields ...
    )

    standard.add_override(
        target_id="task-001",
        reason="Test",
        overridden_by="test@example.com"
    )

    assert standard.has_override_for("task-001")
    assert len(standard.overrides) == 1
```

### Integration Tests

Test complete workflows:

```python
# tests/cli/test_standards_cli.py
def test_complete_workflow(test_roadmap_with_task):
    # Add standard
    result = handle_add_standard(add_args)
    assert result == 0

    # Check standards (should fail)
    result = handle_check_standards(check_args)
    assert result == 1

    # Override standard
    result = handle_override_standard(override_args)
    assert result == 0

    # Complete task (should succeed)
    result = complete_task(root_dir, "task-001", completed_by="test")
    assert result == 0
```

### Test Fixtures

Reusable test data:

```python
@pytest.fixture
def test_roadmap_with_standard(tmp_path):
    """Create test roadmap with blocking standard."""
    # Create roadmap
    roadmap = Roadmap(...)

    # Add standard
    standard = Standard(
        id="test-coverage",
        enforcement=EnforcementMode.BLOCKING,
        # ...
    )
    roadmap.add_standard(standard)

    # Save and return
    save_roadmap(roadmap, tmp_path / ".vibey" / "roadmap.yaml")
    return tmp_path
```

---

## Performance Considerations

### Lazy Loading

Load standards only when needed:

```python
# Good - lazy
def enforce_standards(item_id, root_dir):
    standards = resolver.resolve_for_task(item_id)  # Load on demand
    results = validate_all(standards, item_id)
    return results

# Bad - eager
def load_all_standards_at_startup():
    # Don't load everything upfront
    pass
```

### Caching

Cache resolved standards for repeated checks:

```python
class StandardsResolver:
    def __init__(self, root_dir):
        self._cache = {}

    def resolve_for_task(self, task_id):
        if task_id in self._cache:
            return self._cache[task_id]

        standards = self._resolve(task_id)
        self._cache[task_id] = standards
        return standards
```

### Validation Optimization

1. **Skip disabled standards** - Check `standard.enabled` before validating
2. **Check overrides first** - Skip validation if override exists
3. **Fail fast** - Return on first BLOCKING failure if appropriate
4. **Parallel validation** - Run independent validators concurrently

### File System Access

Minimize redundant file reads:

```python
# Good - load once
roadmap = load_roadmap(roadmap_path)
track = load_track(track_path)
sprint = load_sprint(sprint_path)

# Bad - load multiple times
for standard in standards:
    roadmap = load_roadmap(roadmap_path)  # Redundant!
```

---

## Debugging

### Enable Verbose Output

```bash
# Check standards with verbose output
vibey roadmap check-standards task-001 --verbose

# Shows all standards including passed ones
```

### Check Standards Resolution

```python
from vibey.roadmap.standards import StandardsResolver

resolver = StandardsResolver(root_dir)
standards = resolver.resolve_for_task("task-001")

print(f"Found {len(standards)} standards:")
for std in standards:
    print(f"  - {std.id}: {std.enforcement.value}")
```

### Validate Individual Standard

```python
from vibey.roadmap.standards.validators import create_default_registry

registry = create_default_registry(str(root_dir))
result = registry.validate_one(standard, item_id)

print(f"Status: {result.status}")
print(f"Message: {result.message}")
if result.details:
    print(f"Details: {result.details}")
```

---

## Migration Guide

### Adding Standards to Existing Roadmap

Existing roadmaps work without standards (backward compatible):

```yaml
# Old roadmap.yaml (still works)
roadmap:
  id: my-roadmap
  # No standards field

# New roadmap.yaml (with standards)
roadmap:
  id: my-roadmap
  standards:
    - id: commit-required
      # ... standard config ...
```

Standards field is optional and defaults to empty list.

### Updating Standard Definitions

To update a standard:

1. Load roadmap/track/sprint
2. Modify standard in standards list
3. Save back to YAML

```python
from vibey.roadmap.serialization import load_roadmap, save_roadmap

roadmap = load_roadmap(roadmap_path)
standard = roadmap.get_standard("test-coverage")
standard.enforcement = EnforcementMode.WARNING  # Change enforcement
save_roadmap(roadmap, roadmap_path)
```

---

## Additional Resources

- **User Guide:** `docs/guides/ROADMAP_STANDARDS.md`
- **Validator API:** `docs/development/STANDARD_VALIDATOR_API.md`
- **Source Code:** `vibey/roadmap/standards/`
- **Tests:** `tests/cli/test_standards_cli.py`
- **Templates:** `vibey/roadmap/standards/templates/`

---

**Version:** 1.0.0 (Standards System)
**Last Updated:** 2025-11-13
