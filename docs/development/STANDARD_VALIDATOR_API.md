# Standard Validator API Reference

**Developer Reference for Creating Custom Validators**

---

## Table of Contents

- [Overview](#overview)
- [ValidatorBase Class](#validatorbase-class)
- [ValidationResult Class](#validationresult-class)
- [Creating Custom Validators](#creating-custom-validators)
- [Validator Registry](#validator-registry)
- [Complete Examples](#complete-examples)
- [Testing Validators](#testing-validators)
- [Best Practices](#best-practices)
- [Common Patterns](#common-patterns)
- [Error Handling](#error-handling)

---

## Overview

The Vibey Standards System uses a pluggable validator architecture. Each validator is a Python class that implements the `ValidatorBase` abstract interface.

**Key Concepts:**
- **ValidatorBase** - Abstract base class all validators must inherit from
- **ValidationResult** - Standardized result object with status, message, and metadata
- **Validator Registry** - Maps standard types to validator classes
- **Async Support** - Validators can be sync or async methods

---

## ValidatorBase Class

### Class Definition

```python
from abc import ABC, abstractmethod
from typing import Dict, Any
from pathlib import Path
from vibey.roadmap.models import Standard
from vibey.roadmap.standards.validators import ValidationResult, ValidationStatus

class ValidatorBase(ABC):
    """
    Abstract base class for all standard validators.

    Validators implement the logic for checking if a standard is met.
    Each validator type corresponds to a StandardType enum value.
    """

    @abstractmethod
    async def validate(
        self,
        root_dir: Path,
        item_id: str,
        standard: Standard
    ) -> ValidationResult:
        """
        Validate a standard for a given item.

        Args:
            root_dir: Root directory containing .vibey/
            item_id: Task, sprint, or track ID being validated
            standard: Standard configuration to validate against

        Returns:
            ValidationResult with status, message, and optional metadata

        Raises:
            ValidationError: If validation cannot be performed
        """
        pass
```

### Method Signature

**Parameters:**

- `root_dir: Path` - Absolute path to repository root containing `.vibey/` directory
  - Use this to construct paths to roadmap files, git repo, etc.
  - Example: `/Users/user/projects/my-app`

- `item_id: str` - ID of the item being validated
  - Format depends on level: `track-id`, `sprint-id`, or `task-id`
  - Example: `backend-1-task-003`
  - Use to find relevant commits, files, etc.

- `standard: Standard` - Standard object containing validation configuration
  - Access via `standard.validation` (Dict[str, Any])
  - Contains thresholds, patterns, commands, etc.
  - Example: `{"min_commits": 1, "require_message": false}`

**Returns:**

- `ValidationResult` - Object with status, message, and metadata
  - Must return one of four statuses: PASSED, FAILED, SKIPPED, ERROR
  - Include helpful messages for users
  - Add metadata for debugging or display

**Raises:**

- `ValidationError` - If validation cannot be performed
  - Use for configuration errors, missing dependencies, etc.
  - Include clear error message for troubleshooting

---

## ValidationResult Class

### Class Definition

```python
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass

class ValidationStatus(Enum):
    """Status of validation check."""
    PASSED = "passed"      # Standard met
    FAILED = "failed"      # Standard not met
    SKIPPED = "skipped"    # Validation skipped (e.g., override)
    ERROR = "error"        # Validation error occurred

@dataclass
class ValidationResult:
    """Result of standard validation."""

    status: ValidationStatus
    message: str
    metadata: Optional[Dict[str, Any]] = None

    def __init__(
        self,
        status: ValidationStatus,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.status = status
        self.message = message
        self.metadata = metadata or {}
```

### Creating ValidationResult Objects

**PASSED - Standard met:**
```python
return ValidationResult(
    status=ValidationStatus.PASSED,
    message="Found 5 commits associated with task",
    metadata={"commit_count": 5, "commit_hashes": ["abc123", "def456"]}
)
```

**FAILED - Standard not met:**
```python
return ValidationResult(
    status=ValidationStatus.FAILED,
    message=f"Coverage {actual}% below threshold {threshold}%",
    metadata={"actual": 65, "threshold": 80, "missing": 15}
)
```

**SKIPPED - Validation skipped:**
```python
return ValidationResult(
    status=ValidationStatus.SKIPPED,
    message="Task has override: Emergency hotfix",
    metadata={"override_reason": "Emergency hotfix", "overridden_by": "john@example.com"}
)
```

**ERROR - Validation error:**
```python
return ValidationResult(
    status=ValidationStatus.ERROR,
    message="Git repository not found at root directory",
    metadata={"root_dir": str(root_dir), "error": "NotAGitRepository"}
)
```

### Metadata Guidelines

**Purpose:**
- Store additional data for debugging
- Provide context for failed validations
- Enable rich display in CLI/UI

**Common Metadata Keys:**
- `commit_count`, `commit_hashes` - Git commits
- `file_count`, `file_paths` - File checks
- `actual`, `threshold`, `missing` - Numeric comparisons
- `test_output`, `coverage_report` - Test results
- `error`, `error_type`, `stack_trace` - Error details

---

## Creating Custom Validators

### Step-by-Step Guide

#### Step 1: Create Validator Class

Create a new file in `vibey/roadmap/standards/validators/`:

```python
# vibey/roadmap/standards/validators/my_custom_validator.py

from pathlib import Path
from typing import Dict, Any
from .base import ValidatorBase, ValidationResult, ValidationStatus
from vibey.roadmap.models import Standard

class MyCustomValidator(ValidatorBase):
    """
    Validator for my custom standard type.

    Validation Config:
        my_threshold: int - Threshold value to check
        my_pattern: str - Pattern to match
    """

    async def validate(
        self,
        root_dir: Path,
        item_id: str,
        standard: Standard
    ) -> ValidationResult:
        """Validate my custom standard."""

        # 1. Extract validation config
        config = standard.validation
        threshold = config.get('my_threshold', 100)
        pattern = config.get('my_pattern', '*')

        # 2. Perform validation logic
        try:
            actual_value = self._get_actual_value(root_dir, item_id)

            if actual_value >= threshold:
                return ValidationResult(
                    status=ValidationStatus.PASSED,
                    message=f"Value {actual_value} meets threshold {threshold}",
                    metadata={"actual": actual_value, "threshold": threshold}
                )
            else:
                return ValidationResult(
                    status=ValidationStatus.FAILED,
                    message=f"Value {actual_value} below threshold {threshold}",
                    metadata={"actual": actual_value, "threshold": threshold}
                )

        except Exception as e:
            return ValidationResult(
                status=ValidationStatus.ERROR,
                message=f"Validation error: {str(e)}",
                metadata={"error": str(e), "error_type": type(e).__name__}
            )

    def _get_actual_value(self, root_dir: Path, item_id: str) -> int:
        """Helper method to get actual value."""
        # Your custom logic here
        return 42
```

#### Step 2: Add to StandardType Enum

Update `vibey/roadmap/models.py`:

```python
class StandardType(Enum):
    """Types of standards that can be enforced."""
    COMMIT_CHECK = "commit_check"
    FILE_CHECK = "file_check"
    TEST_RUN = "test_run"
    CUSTOM_SCRIPT = "custom_script"
    MY_CUSTOM_TYPE = "my_custom_type"  # ADD THIS
```

#### Step 3: Register Validator

Update `vibey/roadmap/standards/validators/__init__.py`:

```python
from .my_custom_validator import MyCustomValidator

# Validator registry
VALIDATOR_REGISTRY = {
    StandardType.COMMIT_CHECK: CommitCheckValidator,
    StandardType.FILE_CHECK: FileCheckValidator,
    StandardType.TEST_RUN: TestRunValidator,
    StandardType.CUSTOM_SCRIPT: CustomScriptValidator,
    StandardType.MY_CUSTOM_TYPE: MyCustomValidator,  # ADD THIS
}
```

#### Step 4: Create Tests

Create test file `tests/roadmap/standards/test_my_custom_validator.py`:

```python
import pytest
from pathlib import Path
from vibey.roadmap.models import Standard, StandardType, EnforcementMode
from vibey.roadmap.standards.validators import MyCustomValidator, ValidationStatus
from datetime import datetime, timezone

@pytest.mark.asyncio
async def test_my_custom_validator_passes():
    """Test validator passes when threshold met."""
    validator = MyCustomValidator()

    standard = Standard(
        id="test-standard",
        name="Test Standard",
        description="Test",
        type=StandardType.MY_CUSTOM_TYPE,
        enforcement=EnforcementMode.BLOCKING,
        validation={"my_threshold": 50},
        enabled=True,
        created=datetime.now(timezone.utc),
        overrides=[],
    )

    result = await validator.validate(
        root_dir=Path("/tmp/test"),
        item_id="test-task-001",
        standard=standard
    )

    assert result.status == ValidationStatus.PASSED
    assert "meets threshold" in result.message.lower()

@pytest.mark.asyncio
async def test_my_custom_validator_fails():
    """Test validator fails when threshold not met."""
    validator = MyCustomValidator()

    standard = Standard(
        id="test-standard",
        name="Test Standard",
        description="Test",
        type=StandardType.MY_CUSTOM_TYPE,
        enforcement=EnforcementMode.BLOCKING,
        validation={"my_threshold": 100},
        enabled=True,
        created=datetime.now(timezone.utc),
        overrides=[],
    )

    result = await validator.validate(
        root_dir=Path("/tmp/test"),
        item_id="test-task-001",
        standard=standard
    )

    assert result.status == ValidationStatus.FAILED
    assert "below threshold" in result.message.lower()
```

#### Step 5: Create Template (Optional)

Create template file `vibey/roadmap/standards/templates/my-custom-template.yaml`:

```yaml
template:
  id: my-custom-check
  name: My Custom Check
  description: Validates my custom metric
  type: my_custom_type
  enforcement: blocking

  validation:
    my_threshold: 100
    my_pattern: "*.py"

  use_case: |
    Use this standard to ensure your custom metric meets requirements.

  configuration:
    my_threshold:
      description: Minimum threshold value
      type: integer
      default: 100

    my_pattern:
      description: File pattern to match
      type: string
      default: "*"

  examples:
    basic: |
      vibey roadmap add-from-template my-custom-check roadmap

    custom_threshold: |
      # Override threshold to 200
      vibey roadmap add-standard roadmap \
        my-custom-check \
        "My Custom Check" \
        "Check with custom threshold" \
        my_custom_type \
        blocking \
        '{"my_threshold": 200}'
```

---

## Validator Registry

### Registry Structure

The validator registry maps `StandardType` enum values to validator classes:

```python
# vibey/roadmap/standards/validators/__init__.py

from vibey.roadmap.models import StandardType
from .commit_check import CommitCheckValidator
from .file_check import FileCheckValidator
from .test_run import TestRunValidator
from .custom_script import CustomScriptValidator

VALIDATOR_REGISTRY: Dict[StandardType, Type[ValidatorBase]] = {
    StandardType.COMMIT_CHECK: CommitCheckValidator,
    StandardType.FILE_CHECK: FileCheckValidator,
    StandardType.TEST_RUN: TestRunValidator,
    StandardType.CUSTOM_SCRIPT: CustomScriptValidator,
}

def get_validator(standard_type: StandardType) -> ValidatorBase:
    """Get validator instance for standard type."""
    validator_class = VALIDATOR_REGISTRY.get(standard_type)
    if not validator_class:
        raise ValueError(f"No validator registered for type: {standard_type}")
    return validator_class()
```

### Adding New Validators

1. Import your validator class at top of file
2. Add entry to `VALIDATOR_REGISTRY` dictionary
3. Key = `StandardType` enum value
4. Value = Validator class (not instance)

---

## Complete Examples

### Example 1: Branch Protection Validator

Checks if a task has modified the main/master branch:

```python
# vibey/roadmap/standards/validators/branch_protection.py

import subprocess
from pathlib import Path
from .base import ValidatorBase, ValidationResult, ValidationStatus
from vibey.roadmap.models import Standard

class BranchProtectionValidator(ValidatorBase):
    """
    Validates that task commits are not on protected branches.

    Validation Config:
        protected_branches: List[str] - Branches to protect (default: ["main", "master"])
        allow_merge_commits: bool - Allow merge commits (default: true)
    """

    async def validate(
        self,
        root_dir: Path,
        item_id: str,
        standard: Standard
    ) -> ValidationResult:
        """Validate branch protection."""

        config = standard.validation
        protected_branches = config.get('protected_branches', ['main', 'master'])
        allow_merge = config.get('allow_merge_commits', True)

        try:
            # Get commits for task
            commits = self._get_task_commits(root_dir, item_id)

            if not commits:
                return ValidationResult(
                    status=ValidationStatus.FAILED,
                    message="No commits found for task",
                    metadata={"commit_count": 0}
                )

            # Check each commit's branch
            violations = []
            for commit_hash in commits:
                branches = self._get_commit_branches(root_dir, commit_hash)
                for branch in branches:
                    if branch in protected_branches:
                        # Check if it's a merge commit
                        if allow_merge and self._is_merge_commit(root_dir, commit_hash):
                            continue
                        violations.append({
                            "commit": commit_hash,
                            "branch": branch
                        })

            if violations:
                return ValidationResult(
                    status=ValidationStatus.FAILED,
                    message=f"Found {len(violations)} commits on protected branches",
                    metadata={
                        "violations": violations,
                        "protected_branches": protected_branches
                    }
                )
            else:
                return ValidationResult(
                    status=ValidationStatus.PASSED,
                    message=f"No commits on protected branches ({', '.join(protected_branches)})",
                    metadata={
                        "commit_count": len(commits),
                        "protected_branches": protected_branches
                    }
                )

        except subprocess.CalledProcessError as e:
            return ValidationResult(
                status=ValidationStatus.ERROR,
                message=f"Git command failed: {e.stderr.decode()}",
                metadata={"error": str(e)}
            )

    def _get_task_commits(self, root_dir: Path, item_id: str) -> list:
        """Get commits with task ID in message."""
        result = subprocess.run(
            ['git', 'log', '--all', '--grep', item_id, '--format=%H'],
            cwd=root_dir,
            capture_output=True,
            check=True
        )
        return result.stdout.decode().strip().split('\n')

    def _get_commit_branches(self, root_dir: Path, commit_hash: str) -> list:
        """Get branches containing commit."""
        result = subprocess.run(
            ['git', 'branch', '-a', '--contains', commit_hash],
            cwd=root_dir,
            capture_output=True,
            check=True
        )
        branches = result.stdout.decode().strip().split('\n')
        # Remove leading "* " and whitespace
        return [b.strip().lstrip('* ').replace('remotes/origin/', '') for b in branches]

    def _is_merge_commit(self, root_dir: Path, commit_hash: str) -> bool:
        """Check if commit is a merge commit."""
        result = subprocess.run(
            ['git', 'rev-list', '--parents', '-n', '1', commit_hash],
            cwd=root_dir,
            capture_output=True,
            check=True
        )
        # Merge commits have 2+ parents
        return len(result.stdout.decode().strip().split()) > 2
```

### Example 2: Code Complexity Validator

Checks code complexity metrics using radon:

```python
# vibey/roadmap/standards/validators/code_complexity.py

import subprocess
import json
from pathlib import Path
from .base import ValidatorBase, ValidationResult, ValidationStatus
from vibey.roadmap.models import Standard

class CodeComplexityValidator(ValidatorBase):
    """
    Validates code complexity using radon.

    Validation Config:
        max_complexity: int - Maximum cyclomatic complexity (default: 10)
        max_maintainability: str - Minimum maintainability grade (default: "B")
        file_patterns: List[str] - File patterns to check (default: ["*.py"])

    Requirements:
        pip install radon
    """

    async def validate(
        self,
        root_dir: Path,
        item_id: str,
        standard: Standard
    ) -> ValidationResult:
        """Validate code complexity."""

        config = standard.validation
        max_complexity = config.get('max_complexity', 10)
        max_maintainability = config.get('max_maintainability', 'B')
        file_patterns = config.get('file_patterns', ['*.py'])

        try:
            # Check if radon is installed
            subprocess.run(['radon', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return ValidationResult(
                status=ValidationStatus.ERROR,
                message="radon not installed (pip install radon)",
                metadata={"missing_dependency": "radon"}
            )

        try:
            # Get files modified in task
            files = self._get_modified_files(root_dir, item_id, file_patterns)

            if not files:
                return ValidationResult(
                    status=ValidationStatus.SKIPPED,
                    message="No Python files modified",
                    metadata={"file_count": 0}
                )

            # Check cyclomatic complexity
            violations = []
            for file_path in files:
                full_path = root_dir / file_path
                if not full_path.exists():
                    continue

                result = subprocess.run(
                    ['radon', 'cc', '-j', str(full_path)],
                    capture_output=True,
                    check=True
                )

                complexity_data = json.loads(result.stdout.decode())
                for file_key, functions in complexity_data.items():
                    for func in functions:
                        if func['complexity'] > max_complexity:
                            violations.append({
                                "file": file_path,
                                "function": func['name'],
                                "complexity": func['complexity'],
                                "threshold": max_complexity
                            })

            if violations:
                return ValidationResult(
                    status=ValidationStatus.FAILED,
                    message=f"Found {len(violations)} functions exceeding complexity {max_complexity}",
                    metadata={
                        "violations": violations,
                        "files_checked": len(files)
                    }
                )
            else:
                return ValidationResult(
                    status=ValidationStatus.PASSED,
                    message=f"All functions below complexity threshold {max_complexity}",
                    metadata={
                        "files_checked": len(files),
                        "max_complexity": max_complexity
                    }
                )

        except subprocess.CalledProcessError as e:
            return ValidationResult(
                status=ValidationStatus.ERROR,
                message=f"Radon command failed: {str(e)}",
                metadata={"error": str(e)}
            )

    def _get_modified_files(
        self,
        root_dir: Path,
        item_id: str,
        patterns: list
    ) -> list:
        """Get files modified in task commits matching patterns."""
        # Get commits for task
        result = subprocess.run(
            ['git', 'log', '--all', '--grep', item_id, '--format=%H'],
            cwd=root_dir,
            capture_output=True,
            check=True
        )
        commits = result.stdout.decode().strip().split('\n')

        # Get files modified in commits
        files = set()
        for commit in commits:
            result = subprocess.run(
                ['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', commit],
                cwd=root_dir,
                capture_output=True,
                check=True
            )
            commit_files = result.stdout.decode().strip().split('\n')

            # Filter by patterns
            for file_path in commit_files:
                for pattern in patterns:
                    if Path(file_path).match(pattern):
                        files.add(file_path)

        return list(files)
```

---

## Testing Validators

### Test Structure

```python
# tests/roadmap/standards/test_my_validator.py

import pytest
from pathlib import Path
from datetime import datetime, timezone
from vibey.roadmap.models import Standard, StandardType, EnforcementMode
from vibey.roadmap.standards.validators import MyValidator, ValidationStatus

@pytest.fixture
def standard():
    """Fixture providing standard configuration."""
    return Standard(
        id="test-standard",
        name="Test Standard",
        description="Test",
        type=StandardType.MY_CUSTOM_TYPE,
        enforcement=EnforcementMode.BLOCKING,
        validation={"my_config": "value"},
        enabled=True,
        created=datetime.now(timezone.utc),
        overrides=[],
    )

@pytest.fixture
def validator():
    """Fixture providing validator instance."""
    return MyValidator()

@pytest.mark.asyncio
async def test_validator_passes(validator, standard, tmp_path):
    """Test validator passes when requirements met."""
    result = await validator.validate(
        root_dir=tmp_path,
        item_id="test-task-001",
        standard=standard
    )

    assert result.status == ValidationStatus.PASSED
    assert result.message
    assert isinstance(result.metadata, dict)

@pytest.mark.asyncio
async def test_validator_fails(validator, standard, tmp_path):
    """Test validator fails when requirements not met."""
    # Modify standard to fail
    standard.validation['my_threshold'] = 999999

    result = await validator.validate(
        root_dir=tmp_path,
        item_id="test-task-001",
        standard=standard
    )

    assert result.status == ValidationStatus.FAILED
    assert "threshold" in result.message.lower()

@pytest.mark.asyncio
async def test_validator_error_handling(validator, standard, tmp_path):
    """Test validator handles errors gracefully."""
    # Use invalid path to trigger error
    result = await validator.validate(
        root_dir=Path("/nonexistent/path"),
        item_id="test-task-001",
        standard=standard
    )

    assert result.status == ValidationStatus.ERROR
    assert result.message
```

### Test Coverage Goals

- ✅ **Pass scenarios** - Validator passes when requirements met
- ✅ **Fail scenarios** - Validator fails when requirements not met
- ✅ **Edge cases** - Empty inputs, missing files, etc.
- ✅ **Error handling** - Invalid config, missing dependencies
- ✅ **Metadata** - Proper metadata returned
- ✅ **Integration** - Works with resolver and enforcement engine

---

## Best Practices

### 1. Clear Error Messages

**Good:**
```python
return ValidationResult(
    status=ValidationStatus.FAILED,
    message=f"Coverage {actual}% below threshold {threshold}% (missing {missing}%)",
    metadata={"actual": actual, "threshold": threshold, "missing": missing}
)
```

**Bad:**
```python
return ValidationResult(
    status=ValidationStatus.FAILED,
    message="Failed",
    metadata={}
)
```

### 2. Rich Metadata

Include debugging information:
```python
metadata={
    "actual": actual_value,
    "threshold": threshold_value,
    "files_checked": len(files),
    "violations": violations_list,
    "config": config_used
}
```

### 3. Graceful Degradation

Handle missing dependencies:
```python
try:
    import optional_library
except ImportError:
    return ValidationResult(
        status=ValidationStatus.ERROR,
        message="Missing dependency: optional_library (pip install optional_library)",
        metadata={"missing_dependency": "optional_library"}
    )
```

### 4. Performance Optimization

Cache expensive operations:
```python
class MyValidator(ValidatorBase):
    def __init__(self):
        self._cache = {}

    async def validate(self, root_dir, item_id, standard):
        cache_key = f"{root_dir}:{item_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        result = self._perform_validation()
        self._cache[cache_key] = result
        return result
```

### 5. Configuration Validation

Validate config early:
```python
async def validate(self, root_dir, item_id, standard):
    config = standard.validation

    # Validate required keys
    if 'required_key' not in config:
        return ValidationResult(
            status=ValidationStatus.ERROR,
            message="Missing required config key: 'required_key'",
            metadata={"config": config}
        )

    # Validate types
    threshold = config.get('threshold')
    if not isinstance(threshold, int):
        return ValidationResult(
            status=ValidationStatus.ERROR,
            message=f"Invalid threshold type: {type(threshold)} (expected int)",
            metadata={"threshold": threshold}
        )

    # Continue with validation...
```

---

## Common Patterns

### Pattern 1: Git-Based Validation

```python
def _get_task_commits(self, root_dir: Path, item_id: str) -> list:
    """Get commits for a task."""
    result = subprocess.run(
        ['git', 'log', '--all', '--grep', item_id, '--format=%H'],
        cwd=root_dir,
        capture_output=True,
        check=True
    )
    return result.stdout.decode().strip().split('\n')

def _get_modified_files(self, root_dir: Path, commits: list) -> list:
    """Get files modified in commits."""
    files = set()
    for commit in commits:
        result = subprocess.run(
            ['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', commit],
            cwd=root_dir,
            capture_output=True,
            check=True
        )
        files.update(result.stdout.decode().strip().split('\n'))
    return list(files)
```

### Pattern 2: File System Checks

```python
def _find_files_matching_pattern(
    self,
    root_dir: Path,
    pattern: str,
    exclude_patterns: List[str] = None
) -> list:
    """Find files matching glob pattern."""
    files = []
    for file_path in root_dir.rglob(pattern):
        # Check exclusions
        if exclude_patterns:
            excluded = False
            for exclude in exclude_patterns:
                if file_path.match(exclude):
                    excluded = True
                    break
            if excluded:
                continue

        if file_path.is_file():
            files.append(file_path.relative_to(root_dir))

    return files
```

### Pattern 3: Command Execution

```python
def _run_command(
    self,
    command: list,
    root_dir: Path,
    timeout: int = 300
) -> tuple:
    """Run command and return (success, stdout, stderr)."""
    try:
        result = subprocess.run(
            command,
            cwd=root_dir,
            capture_output=True,
            timeout=timeout,
            check=False
        )
        return (
            result.returncode == 0,
            result.stdout.decode(),
            result.stderr.decode()
        )
    except subprocess.TimeoutExpired:
        return (False, "", f"Command timed out after {timeout}s")
    except Exception as e:
        return (False, "", str(e))
```

---

## Error Handling

### Error Types

**ValidationError - Configuration/setup errors:**
```python
from vibey.roadmap.standards.validators import ValidationError

if 'required_config' not in standard.validation:
    raise ValidationError("Missing required config: 'required_config'")
```

**Return ERROR status - Runtime errors:**
```python
try:
    result = dangerous_operation()
except Exception as e:
    return ValidationResult(
        status=ValidationStatus.ERROR,
        message=f"Operation failed: {str(e)}",
        metadata={"error": str(e), "error_type": type(e).__name__}
    )
```

### Error Recovery

```python
async def validate(self, root_dir, item_id, standard):
    try:
        # Primary validation method
        return self._primary_validation(root_dir, item_id, standard)
    except PrimaryValidationError:
        # Fallback validation method
        return self._fallback_validation(root_dir, item_id, standard)
    except Exception as e:
        # Ultimate fallback
        return ValidationResult(
            status=ValidationStatus.ERROR,
            message=f"All validation methods failed: {str(e)}",
            metadata={"error": str(e)}
        )
```

---

## Additional Resources

- **Implementation Guide:** `STANDARDS_IMPLEMENTATION.md`
- **User Guide:** `docs/guides/ROADMAP_STANDARDS.md`
- **Existing Validators:** `vibey/roadmap/standards/validators/`
- **Test Examples:** `tests/roadmap/standards/`

---

**Version:** 1.0.0 (Standards System)
**Last Updated:** 2025-11-13
