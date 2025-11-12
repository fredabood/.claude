# Roadmap Standards System

**User Guide for Quality Policy Enforcement**

---

## Table of Contents

- [Overview](#overview)
- [What Are Standards?](#what-are-standards)
- [Why Use Standards?](#why-use-standards)
- [Standard Types](#standard-types)
- [Enforcement Modes](#enforcement-modes)
- [Adding Standards](#adding-standards)
- [Using Templates](#using-templates)
- [Checking Standards](#checking-standards)
- [Override Mechanism](#override-mechanism)
- [Hierarchical Inheritance](#hierarchical-inheritance)
- [Best Practices](#best-practices)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

---

## Overview

The Roadmap Standards System enables you to enforce quality policies automatically across your roadmap. Standards cascade from roadmap → track → sprint → task, ensuring consistent quality enforcement at all levels.

**Key Features:**
- ✅ Hierarchical standards (inherit from parent levels)
- ✅ Multiple enforcement modes (blocking, warning, audit)
- ✅ Pre-built templates for common use cases
- ✅ Override mechanism with audit trail
- ✅ Automatic validation during completion
- ✅ Custom validators for project-specific needs

---

## What Are Standards?

Standards are quality requirements that must be met before completing roadmap items (tasks, sprints, tracks). Each standard defines:

- **What to check** (commits, files, tests, custom scripts)
- **Validation rules** (minimum commits, file patterns, test thresholds)
- **Enforcement mode** (blocking, warning, or audit)
- **Where it applies** (roadmap, track, sprint, or task level)

### Example Standard

```yaml
standard:
  id: commit-required
  name: Commit Required
  description: All tasks must have at least one git commit
  type: commit_check
  enforcement: blocking
  validation:
    min_commits: 1
```

---

## Why Use Standards?

Standards help you:

1. **Enforce Quality Policies** - Ensure code quality, test coverage, documentation
2. **Prevent Incomplete Work** - Block completion until requirements are met
3. **Maintain Consistency** - Apply same rules across all development
4. **Track Compliance** - Audit which standards are met and overridden
5. **Automate Reviews** - Run checks automatically during completion

### Real-World Use Cases

**Startup wanting to enforce testing:**
- Add `test-coverage-required` at roadmap level
- All tasks must include tests and meet 80% coverage
- Blocks completion if coverage drops below threshold

**Open source project requiring documentation:**
- Add `doc-review-required` at track level for public API
- Tasks should update documentation (warning mode)
- Encourages but doesn't block for internal tasks

**Security-sensitive application:**
- Add `security-review` at sprint level for auth work
- Runs security scans and requires manual review
- Blocks completion until security team approves

---

## Standard Types

### 1. Commit Check (`commit_check`)

Ensures tasks have git commits for traceability.

**Validation Config:**
```json
{
  "min_commits": 1,
  "require_message": false
}
```

**Use Cases:**
- Ensure all work is version controlled
- Track code changes for audit
- Prevent completion without commits

### 2. File Check (`file_check`)

Checks if specific files were modified in task commits.

**Validation Config:**
```json
{
  "pattern": "**/*.md",
  "min_files": 1,
  "exclude_patterns": ["**/node_modules/**"]
}
```

**Use Cases:**
- Ensure documentation is updated
- Check configuration files changed
- Verify specific files modified

### 3. Test Run (`test_run`)

Runs tests and checks coverage thresholds.

**Validation Config:**
```json
{
  "command": "pytest --cov --cov-report=term",
  "threshold": 80,
  "require_test_files": true
}
```

**Use Cases:**
- Enforce test coverage requirements
- Run test suite automatically
- Block completion on test failures

### 4. Custom Script (`custom_script`)

Runs a custom validation script.

**Validation Config:**
```json
{
  "script": "#!/bin/bash\n# Your validation script\nexit 0",
  "require_reviewer": false
}
```

**Use Cases:**
- Security scanning
- Custom quality checks
- Project-specific validations

---

## Enforcement Modes

### 🔴 BLOCKING

**Prevents completion** if standard fails.

**When to use:**
- Critical quality requirements
- Mandatory security checks
- Essential test coverage

**Example:**
```bash
# Task cannot be completed until standard passes
vibey roadmap complete task backend-1-task-001
❌ Cannot complete task: 1 blocking standard(s) failed
   • test-coverage-required: Coverage 65% below threshold 80%
```

### 🟡 WARNING

**Shows warnings** but allows completion.

**When to use:**
- Encouraging best practices
- Soft requirements
- Gradual adoption

**Example:**
```bash
# Task completes with warnings
vibey roadmap complete task backend-1-task-001
⚠️  Task has warnings but will proceed with completion
   • doc-review-required: No documentation files modified
✅ Task completed successfully
```

### 🟢 AUDIT

**Logs results** without enforcement.

**When to use:**
- Tracking metrics
- Experimental standards
- Optional checks

**Example:**
```bash
# Task completes, audit logged
vibey roadmap complete task backend-1-task-001
ℹ️  Audit: security-review completed
✅ Task completed successfully
```

---

## Adding Standards

### Option 1: Use Pre-Built Templates (Recommended)

```bash
# List available templates
vibey roadmap list-templates

# Add from template to roadmap
vibey roadmap add-from-template commit-required roadmap

# Add to track with custom ID
vibey roadmap add-from-template test-coverage-required track \
  --target-id backend \
  --custom-id my-coverage-check

# Override enforcement mode
vibey roadmap add-from-template doc-review-required track \
  --target-id backend \
  --enforcement blocking
```

### Option 2: Add Custom Standard

```bash
# Add custom standard to roadmap
vibey roadmap add-standard roadmap \
  my-custom-check \
  "My Custom Check" \
  "Description of what this checks" \
  commit_check \
  blocking \
  '{"min_commits": 2}'

# Add to track
vibey roadmap add-standard track \
  my-track-check \
  "Track-Specific Check" \
  "Only applies to this track" \
  file_check \
  warning \
  '{"pattern": "src/**/*.py", "min_files": 1}' \
  --target-id backend
```

---

## Using Templates

Vibey ships with 5 pre-built standard templates:

### 1. commit-required

Ensures all tasks have git commits.

```bash
vibey roadmap add-from-template commit-required roadmap
```

**Default Config:**
- Type: commit_check
- Enforcement: blocking
- Min commits: 1

### 2. doc-review-required

Encourages documentation updates.

```bash
vibey roadmap add-from-template doc-review-required track \
  --target-id backend
```

**Default Config:**
- Type: file_check
- Enforcement: warning
- Pattern: `**/*.md`
- Min files: 1

### 3. test-coverage-required

Enforces test coverage thresholds.

```bash
vibey roadmap add-from-template test-coverage-required roadmap
```

**Default Config:**
- Type: test_run
- Enforcement: blocking
- Command: `pytest --cov`
- Threshold: 80%

### 4. multi-platform-testing

Tests across multiple platforms.

```bash
vibey roadmap add-from-template multi-platform-testing roadmap
```

**Default Config:**
- Type: test_run
- Enforcement: blocking
- Platforms: claude-code (required), goose/cursor (optional)

### 5. security-review

Security scanning and review.

```bash
vibey roadmap add-from-template security-review sprint \
  --target-id auth-sprint-1
```

**Default Config:**
- Type: custom_script
- Enforcement: blocking
- Includes: secret detection, SQL injection checks, unsafe eval detection

---

## Checking Standards

### Preview Standards Before Completion

```bash
# Check standards for a task
vibey roadmap check-standards backend-1-task-001

# Check with verbose output (shows all standards)
vibey roadmap check-standards backend-1-task-001 --verbose
```

**Output Example:**
```
🔍 Checking standards for Task: backend-1-task-001
================================================================================

Standards Compliance: 3/4 passed (75%)
  ✅ commit-required (roadmap) - PASSED
  ✅ test-coverage-required (roadmap) - PASSED
  ✅ doc-review-required (track) - PASSED
  ❌ security-review (sprint) - FAILED: Security scan detected issues

❌ Item cannot proceed - 1 blocking failure(s)
   Use 'vibey roadmap override-standard' to override specific standards
```

### View Standards in Status

```bash
# Roadmap status shows standards counts
vibey roadmap status

# Output includes standards info:
🛤️  Tracks
--------------------------------------------------------------------------------
🔵 in_progress Backend Track
   Progress: 5/10 tasks, 2/3 sprints (50% complete)
   📋 Standards: 3 (🔴 2 blocking, 🟡 1 warning)
```

### View Standards in Show

```bash
# Show track with standards details
vibey roadmap show backend

# Output includes:
📋 Standards: 3 standards (🔴 2 blocking, 🟡 1 warning)
   Standards Applied:
   • commit-required: Commit Required
     Type: commit_check | 🔴 BLOCKING
   • test-coverage-required: Test Coverage Required
     Type: test_run | 🔴 BLOCKING
   • doc-review-required: Documentation Review Required
     Type: file_check | 🟡 WARNING
```

---

## Override Mechanism

Sometimes you need to bypass a standard temporarily. Overrides provide an escape hatch with full audit trail.

### Creating an Override

```bash
# Override a standard for specific item
vibey roadmap override-standard \
  test-coverage-required \
  backend-1-task-001 \
  "Emergency hotfix - will add tests in follow-up task" \
  --overridden-by "john@example.com"
```

### When to Use Overrides

**Legitimate Reasons:**
- Emergency hotfixes
- Legacy code refactoring (tests added incrementally)
- Documentation-only changes (no code)
- External work not tracked in git

**Poor Reasons:**
- Laziness or time pressure
- Avoiding writing tests
- Skipping quality for convenience

### Override Audit Trail

All overrides are tracked with:
- **Who** created the override
- **When** it was created
- **Why** (justification reason)
- **What** item it applies to

This creates accountability and enables later review of override patterns.

---

## Hierarchical Inheritance

Standards cascade down through the roadmap hierarchy:

```
Roadmap Standards
   ↓ (inherited by all tracks)
Track Standards
   ↓ (inherited by all sprints in track)
Sprint Standards
   ↓ (inherited by all tasks in sprint)
Task
```

### Example Hierarchy

**Roadmap-level:**
- `commit-required` (blocking) - ALL items must have commits

**Track-level (backend):**
- `test-coverage-required` (blocking) - Backend code needs tests
- `doc-review-required` (warning) - Backend should update docs

**Sprint-level (auth-sprint-1):**
- `security-review` (blocking) - Auth code needs security review

**Effective standards for task `auth-sprint-1-task-001`:**
1. commit-required (from roadmap)
2. test-coverage-required (from track)
3. doc-review-required (from track)
4. security-review (from sprint)

### Deduplication

If the same standard ID appears at multiple levels, the **lowest level** (closest to task) takes precedence. This allows overriding parent standards with different enforcement modes.

---

## Best Practices

### 1. Start with Templates

Use pre-built templates instead of creating custom standards. They're battle-tested and well-documented.

```bash
# Good
vibey roadmap add-from-template commit-required roadmap

# Less ideal
vibey roadmap add-standard roadmap custom-commit-check ...
```

### 2. Use Appropriate Enforcement

- **BLOCKING** for critical requirements (tests, security)
- **WARNING** for encouragement (docs, code style)
- **AUDIT** for tracking and metrics

### 3. Apply at the Right Level

- **Roadmap** - Organization-wide policies (all code needs commits)
- **Track** - Domain-specific rules (backend needs high test coverage)
- **Sprint** - Temporary requirements (security review for auth sprint)
- **Task** - Rare, use sparingly

### 4. Document Why Standards Exist

When adding custom standards, document:
- Why this standard is needed
- What it prevents
- When to override it

### 5. Review Override Patterns

Regularly review overrides. Frequent overrides for the same standard indicate:
- Standard may be too strict
- Team needs training
- Standard should be WARNING not BLOCKING

### 6. Gradual Adoption

When introducing standards to existing projects:

1. Start with **AUDIT** mode (track metrics)
2. Move to **WARNING** mode (encourage compliance)
3. Finally **BLOCKING** once team is ready

### 7. Combine Related Standards

For comprehensive quality:
- `commit-required` + `test-coverage-required` ensures testable code
- `doc-review-required` + `test-coverage-required` ensures documented, tested features
- `security-review` + `test-coverage-required` for security-critical code with tests

---

## Examples

### Example 1: Startup Enforcing Tests

**Goal:** Ensure all code has tests before deployment.

```bash
# Add test coverage requirement at roadmap level
vibey roadmap add-from-template test-coverage-required roadmap

# All tasks now require 80% test coverage
# Blocks completion if coverage is below threshold
```

**Result:**
- All tasks must include tests
- Coverage tracked automatically
- Blocks deployment of untested code

### Example 2: Open Source Project Documentation

**Goal:** Encourage documentation updates without blocking.

```bash
# Add doc review at track level for public API
vibey roadmap add-from-template doc-review-required track \
  --target-id public-api \
  --enforcement warning

# Internal tools track doesn't have this requirement
```

**Result:**
- API changes show warnings if docs not updated
- Warnings visible but don't block
- Gradual culture shift toward documentation

### Example 3: Security-Critical Sprint

**Goal:** Require security review for authentication work.

```bash
# Add security review for auth sprint
vibey roadmap add-from-template security-review sprint \
  --target-id auth-sprint-1

# Check standards before starting work
vibey roadmap check-standards auth-sprint-1-task-001
```

**Result:**
- Security scans run automatically
- Tasks blocked until review complete
- Full audit trail of security checks

### Example 4: Multi-Platform Framework

**Goal:** Ensure code works on all target platforms.

```bash
# Add multi-platform testing at roadmap level
vibey roadmap add-from-template multi-platform-testing roadmap

# Tests run on claude-code, goose, cursor
```

**Result:**
- Tests must pass on all platforms
- Platform-specific issues caught early
- Consistent cross-platform quality

---

## Troubleshooting

### Problem: Standard Always Fails

**Symptom:**
```
❌ test-coverage-required: Command failed: pytest --cov
```

**Solutions:**
1. Check if test command is correct
2. Verify dependencies installed
3. Run command manually to debug
4. Check validation config matches project setup

### Problem: Override Not Working

**Symptom:**
```
❌ Cannot complete task: 1 blocking standard(s) failed
```

**Solutions:**
1. Verify override applied: `vibey roadmap show <task-id>`
2. Check standard ID matches exactly
3. Ensure override created for correct item
4. Override applies to specific item, not all tasks

### Problem: Standards Not Showing

**Symptom:** Standards not displayed in status/show commands

**Solutions:**
1. Check standards exist: `vibey roadmap list-templates`
2. Verify standards added at appropriate level
3. Check standards inheritance (may be at parent level)
4. Ensure roadmap system up to date

### Problem: Too Many Override Requests

**Symptom:** Team frequently requesting overrides

**Solutions:**
1. Review standard threshold (may be too strict)
2. Change enforcement from BLOCKING → WARNING
3. Provide tooling to help meet standard
4. Additional training on why standard exists

### Problem: Standard Passes But Shouldn't

**Symptom:** Validation passes when it should fail

**Solutions:**
1. Check validation config is correct
2. Verify validator logic is working
3. Test validator in isolation
4. Check for known limitations of validator

---

## Additional Resources

- **Developer Guide:** `docs/development/STANDARDS_IMPLEMENTATION.md`
- **Validator API:** `docs/development/STANDARD_VALIDATOR_API.md`
- **Templates Source:** `vibey/roadmap/standards/templates/`
- **CLI Reference:** `vibey roadmap --help`

---

## Quick Reference

### Common Commands

```bash
# List templates
vibey roadmap list-templates

# Add standard from template
vibey roadmap add-from-template <template-id> <level> [--target-id <id>]

# Check standards
vibey roadmap check-standards <item-id>

# Override standard
vibey roadmap override-standard <standard-id> <item-id> "<reason>" [--overridden-by <email>]

# View standards in status
vibey roadmap status

# View standards in show
vibey roadmap show <item-id>
```

### Standard Types Quick Reference

| Type | Use Case | Example Config |
|------|----------|----------------|
| `commit_check` | Git commits required | `{"min_commits": 1}` |
| `file_check` | Specific files modified | `{"pattern": "**/*.md", "min_files": 1}` |
| `test_run` | Test coverage | `{"command": "pytest --cov", "threshold": 80}` |
| `custom_script` | Custom validation | `{"script": "#!/bin/bash\n..."}` |

### Enforcement Modes Quick Reference

| Mode | Emoji | Behavior |
|------|-------|----------|
| BLOCKING | 🔴 | Prevents completion if fails |
| WARNING | 🟡 | Shows warning, allows completion |
| AUDIT | 🟢 | Logs only, no enforcement |

---

**Version:** 1.0.0 (Standards System)
**Last Updated:** 2025-11-13
