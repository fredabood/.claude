# Platform Adapter Development Guide

**Version:** 1.0
**Date:** 2025-11-10
**Sprint:** directory-migration-3, Task 014

Complete guide for creating new platform adapters for Vibey Framework.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Adapter Interface](#adapter-interface)
5. [Implementation Guide](#implementation-guide)
6. [Testing](#testing)
7. [Best Practices](#best-practices)
8. [Examples](#examples)
9. [Troubleshooting](#troubleshooting)

---

## Overview

### What is a Platform Adapter?

A platform adapter transforms Vibey's `.vibey/` source of truth into platform-specific deployment formats (`.claude/`, `.goose/`, `.cursor/`, etc.).

**Key Concepts:**
- **Source of Truth:** `.vibey/` directory (platform-agnostic)
- **Adapter:** Transforms source → platform format
- **Deployment:** Platform-specific directory (generated, disposable)

### When to Create an Adapter

Create a new adapter when:
- Adding support for a new AI coding assistant platform
- Platform has its own directory structure (e.g., `.cursor/`)
- Platform needs platform-specific context files

---

## Architecture

### Adapter Pattern

```
┌─────────────────────────────────────────────────┐
│ .vibey/ (Source of Truth)                      │
│ ├── config/                                     │
│ │   ├── project.yaml                            │
│ │   ├── framework.yaml                          │
│ │   ├── agents.yaml                             │
│ │   └── quality-gates.yaml                      │
│ └── roadmap.yaml                                │
└─────────────────────────────────────────────────┘
                    ↓
         ┌──────────────────────┐
         │ PlatformAdapter      │
         │ .deploy()            │
         └──────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ Platform Deployment (Generated)                 │
│ .claude/  OR  .goose/  OR  .cursor/             │
└─────────────────────────────────────────────────┘
```

### Adapter Lifecycle

1. **Load Config:** Read from `.vibey/config/`
2. **Transform:** Convert to platform format
3. **Generate:** Create context files and structure
4. **Validate:** Ensure deployment is correct
5. **Report:** Return DeploymentResult

---

## Quick Start

### 1. Create Adapter File

Create `vibey/adapters/my_platform.py`:

```python
from pathlib import Path
from typing import Optional, List, Any
from vibey.adapters.base import PlatformAdapter, DeploymentResult

class MyPlatformAdapter(PlatformAdapter):
    """Adapter for My Platform."""

    def get_platform_name(self) -> str:
        return "my-platform"

    def get_deployment_dir(self, project_root: Optional[Path] = None) -> Path:
        if project_root is None:
            project_root = Path.cwd()
        return project_root / ".myplatform"

    def deploy(self, source_dir: Path, config: Any,
               target_dir: Optional[Path] = None,
               clean: bool = False) -> DeploymentResult:
        # Implementation here
        pass

    def generate_context_file(self, config: Any, output_path: Path) -> None:
        # Implementation here
        pass

    def validate_deployment(self, deployment_dir: Path) -> tuple[bool, List[str]]:
        # Implementation here
        pass
```

### 2. Register Adapter

Add to `vibey/cli/deploy.py`:

```python
from vibey.adapters.my_platform import MyPlatformAdapter

PLATFORMS = {
    "claude-code": ClaudeCodeAdapter,
    "goose": GooseAdapter,
    "my-platform": MyPlatformAdapter,  # Add this
}
```

### 3. Export Adapter

Add to `vibey/adapters/__init__.py`:

```python
from vibey.adapters.my_platform import MyPlatformAdapter

__all__ = [
    'PlatformAdapter',
    'DeploymentResult',
    'ClaudeCodeAdapter',
    'GooseAdapter',
    'MyPlatformAdapter',  # Add this
]
```

### 4. Test

```bash
vibey deploy run --platform my-platform
```

---

## Adapter Interface

### Required Methods

#### `get_platform_name() -> str`

Returns platform identifier (lowercase, hyphenated).

```python
def get_platform_name(self) -> str:
    return "my-platform"
```

**Examples:**
- `"claude-code"`
- `"goose"`
- `"cursor"`
- `"aider"`

---

#### `get_deployment_dir(project_root) -> Path`

Returns deployment directory path.

```python
def get_deployment_dir(self, project_root: Optional[Path] = None) -> Path:
    if project_root is None:
        project_root = Path.cwd()
    return project_root / ".myplatform"
```

**Common patterns:**
- Claude Code: `.claude/`
- Goose: `.goose/`
- Cursor: `.cursor/`

---

#### `deploy(source_dir, config, target_dir, clean) -> DeploymentResult`

Main deployment logic.

```python
def deploy(
    self,
    source_dir: Path,        # .vibey/ directory
    config: Any,             # VibeyConfig object
    target_dir: Optional[Path] = None,
    clean: bool = False
) -> DeploymentResult:
    start_time = datetime.now()

    if target_dir is None:
        target_dir = self.get_deployment_dir(source_dir.parent)

    result = DeploymentResult(
        success=False,
        platform=self.get_platform_name(),
        target_dir=target_dir,
    )

    try:
        # Pre-deployment hook
        self.pre_deploy_hook(source_dir, target_dir)

        # 1. Clean if requested
        if clean and target_dir.exists():
            shutil.rmtree(target_dir)
            result.files_deleted.append(target_dir)

        # 2. Create directory structure
        target_dir.mkdir(parents=True, exist_ok=True)

        # 3. Generate context file
        context_file = target_dir / "CONTEXT.md"
        self.generate_context_file(config, context_file)
        result.files_created.append(context_file)

        # 4. Copy/transform components
        # ... platform-specific logic ...

        # 5. Validate
        is_valid, errors = self.validate_deployment(target_dir)
        result.validation_passed = is_valid
        result.errors.extend(errors)

        result.success = len(result.errors) == 0

        # Post-deployment hook
        self.post_deploy_hook(result)

    except Exception as e:
        result.success = False
        result.errors.append(f"Deployment failed: {e}")

    result.duration_seconds = (datetime.now() - start_time).total_seconds()
    return result
```

---

#### `generate_context_file(config, output_path) -> None`

Generate platform-specific context file.

```python
def generate_context_file(self, config: Any, output_path: Path) -> None:
    content = f"""# {config.project.project.name}

**Project Type:** {config.project.project.type.value}
**Version:** {config.project.project.version}

## Tech Stack

**Languages:** {', '.join(config.project.tech_stack.languages)}

---

<!-- VIBEY_FRAMEWORK_MANAGED -->
*Generated by Vibey Agent Framework*
"""
    output_path.write_text(content)
```

**Platform-Specific Examples:**
- Claude Code: `CLAUDE.md`
- Goose: `.goosehints`
- Cursor: `.cursorrules`
- Aider: `.aider.md`

---

#### `validate_deployment(deployment_dir) -> tuple[bool, List[str]]`

Validate deployment correctness.

```python
def validate_deployment(self, deployment_dir: Path) -> tuple[bool, List[str]]:
    errors = []

    # Check directory exists
    if not deployment_dir.exists():
        errors.append(f"Deployment directory missing: {deployment_dir}")
        return (False, errors)

    # Check required files
    context_file = deployment_dir / "CONTEXT.md"
    if not context_file.exists():
        errors.append("Missing context file: CONTEXT.md")

    # Check file contents
    if context_file.exists():
        content = context_file.read_text()
        if not content.strip():
            errors.append("Context file is empty")
        if "VIBEY_FRAMEWORK_MANAGED" not in content:
            errors.append("Context file missing Vibey marker")

    return (len(errors) == 0, errors)
```

---

### Optional Methods

#### `get_required_files() -> List[str]`

List required files for platform.

```python
def get_required_files(self) -> List[str]:
    return [
        "CONTEXT.md",
        "config.json",
    ]
```

---

#### `get_optional_files() -> List[str]`

List optional files for platform.

```python
def get_optional_files(self) -> List[str]:
    return [
        "agents/",
        "workflows/",
        "templates/",
    ]
```

---

#### `supports_feature(feature) -> bool`

Check if platform supports a feature.

```python
def supports_feature(self, feature: str) -> bool:
    supported = {
        "agents",
        "workflows",
        "quality-gates",
        "roadmap",
        "templates",
    }
    return feature in supported
```

---

#### `pre_deploy_hook(source_dir, target_dir) -> None`

Hook called before deployment.

```python
def pre_deploy_hook(self, source_dir: Path, target_dir: Path) -> None:
    # Custom pre-deployment logic
    print(f"Deploying from {source_dir} to {target_dir}")
```

---

#### `post_deploy_hook(result) -> None`

Hook called after deployment.

```python
def post_deploy_hook(self, result: DeploymentResult) -> None:
    # Custom post-deployment logic
    if result.success:
        print("Deployment successful!")
```

---

## Implementation Guide

### Step-by-Step Checklist

- [ ] Create adapter file in `vibey/adapters/`
- [ ] Implement required methods
- [ ] Add to platform registry
- [ ] Export from `__init__.py`
- [ ] Test with real config
- [ ] Document platform-specific notes
- [ ] Add to CLI choices

### Common Patterns

#### Pattern 1: Direct File Copy

For platforms that support Vibey components directly:

```python
components = [
    ("agents", "agents"),
    ("workflows", "workflows"),
    ("templates", "templates"),
]

for source_name, target_name in components:
    source_path = source_dir.parent / source_name
    if source_path.exists():
        target_path = target_dir / target_name
        shutil.copytree(source_path, target_path)
        result.files_created.append(target_path)
```

#### Pattern 2: Transform and Convert

For platforms with different formats:

```python
# Convert workflows to platform-specific format
workflows_dir = source_dir.parent / "workflows"
if workflows_dir.exists():
    for workflow_file in workflows_dir.rglob("*.md"):
        # Transform workflow
        platform_workflow = transform_workflow(workflow_file)

        # Write to platform directory
        output_path = target_dir / "recipes" / workflow_file.name
        output_path.write_text(platform_workflow)
        result.files_created.append(output_path)
```

#### Pattern 3: Generate from Config

For platforms that need generated files:

```python
# Generate platform-specific config
platform_config = {
    "name": config.project.project.name,
    "languages": config.project.tech_stack.languages,
    "features": self.get_supported_features(),
}

config_file = target_dir / "config.json"
config_file.write_text(json.dumps(platform_config, indent=2))
result.files_created.append(config_file)
```

---

## Testing

### Manual Testing

```bash
# Deploy to your platform
cd /tmp/test-project
vibey deploy run --platform my-platform

# Deploy with clean
vibey deploy run --platform my-platform --clean

# Test validation
vibey deploy run --platform my-platform --no-validate
```

### Automated Testing

Create `tests/adapters/test_my_platform.py`:

```python
import pytest
from pathlib import Path
from vibey.adapters.my_platform import MyPlatformAdapter
from vibey.config import load_config

def test_adapter_instantiation():
    adapter = MyPlatformAdapter()
    assert adapter.get_platform_name() == "my-platform"

def test_deployment_dir():
    adapter = MyPlatformAdapter()
    deploy_dir = adapter.get_deployment_dir(Path("/tmp/test"))
    assert deploy_dir == Path("/tmp/test/.myplatform")

def test_deploy(tmp_path):
    adapter = MyPlatformAdapter()
    source = tmp_path / ".vibey"
    source.mkdir()

    # Create test config
    config = create_test_config()

    result = adapter.deploy(
        source_dir=source,
        config=config,
        clean=True
    )

    assert result.success
    assert result.validation_passed
    assert len(result.errors) == 0
```

---

## Best Practices

### DO ✅

1. **Use DeploymentResult:** Always return complete deployment result
2. **Validate After Deploy:** Call `validate_deployment()` in `deploy()`
3. **Track Files:** Add all created/updated/deleted files to result
4. **Handle Errors:** Wrap deployment in try/except
5. **Use Hooks:** Implement pre/post hooks for extensibility
6. **Document Warnings:** Add warnings for unsupported features
7. **Test Thoroughly:** Test with real configs and edge cases

### DON'T ❌

1. **Modify Source:** Never modify `.vibey/` directory
2. **Skip Validation:** Always validate deployment
3. **Hardcode Paths:** Use `target_dir` parameter
4. **Ignore Errors:** Always populate `result.errors`
5. **Break Interface:** Implement all required methods
6. **Forget Marker:** Add `VIBEY_FRAMEWORK_MANAGED` to context files

---

## Examples

### Example 1: Claude Code Adapter

See `vibey/adapters/claude_code.py` for complete implementation.

**Key Features:**
- Generates `CLAUDE.md`
- Copies agents, workflows, templates
- Validates required files
- Supports all Vibey features

### Example 2: Goose Adapter

See `vibey/adapters/goose.py` for complete implementation.

**Key Features:**
- Generates `.goosehints`
- Converts workflows → recipes
- Documents agent incompatibility
- Platform-specific warnings

---

## Troubleshooting

### Common Issues

**Issue: Deployment fails silently**
- **Cause:** Exception not caught
- **Fix:** Wrap deployment in try/except

**Issue: Validation always fails**
- **Cause:** Wrong file paths in validation
- **Fix:** Check `deployment_dir` vs `deployment_dir.parent`

**Issue: Files not tracked in result**
- **Cause:** Forgot to add to `result.files_created`
- **Fix:** Add all created files to appropriate list

**Issue: Context file location wrong**
- **Cause:** Platform expects file in different location
- **Fix:** Check platform documentation for correct path

### Debug Tips

1. **Enable verbose logging:**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Print deployment result:**
   ```python
   print(result)
   print(f"Errors: {result.errors}")
   print(f"Warnings: {result.warnings}")
   ```

3. **Check created files:**
   ```bash
   ls -la .myplatform/
   cat .myplatform/CONTEXT.md
   ```

---

## Platform-Specific Considerations

### Claude Code
- **Context:** `CLAUDE.md` (markdown)
- **Agents:** Native support (markdown files)
- **Workflows:** Native support
- **Quality Gates:** Supported

### Goose
- **Context:** `.goosehints` (markdown, project root)
- **Agents:** Not supported (Python toolkits instead)
- **Workflows:** Recipes (similar format)
- **Quality Gates:** Not supported

### Cursor
- **Context:** `.cursorrules` (markdown)
- **Agents:** Limited support (custom rules)
- **Workflows:** Not applicable
- **Quality Gates:** Not supported

### Aider
- **Context:** `.aider.md` (markdown)
- **Agents:** Not supported
- **Workflows:** Limited support
- **Quality Gates:** Not supported

---

## Checklist for New Platform

- [ ] Research platform directory structure
- [ ] Identify context file name and location
- [ ] Determine feature compatibility
- [ ] Create adapter class
- [ ] Implement required methods
- [ ] Add platform-specific transformations
- [ ] Write validation logic
- [ ] Register in platform registry
- [ ] Export from __init__.py
- [ ] Add to CLI choices
- [ ] Test deployment
- [ ] Test validation
- [ ] Test cleanup
- [ ] Document platform notes
- [ ] Add example to this guide

---

## Reference

**Base Classes:**
- `vibey/adapters/base.py` - PlatformAdapter, DeploymentResult

**Existing Adapters:**
- `vibey/adapters/claude_code.py` - Full-featured example
- `vibey/adapters/goose.py` - Conversion example

**CLI Integration:**
- `vibey/cli/deploy.py` - Deployment command
- `vibey/cli/main.py` - CLI wiring

**Testing:**
- `tests/adapters/` - Adapter test suite

---

**Last Updated:** 2025-11-10
**Sprint:** directory-migration-3
**Task:** 014 - Document adapter development guide
