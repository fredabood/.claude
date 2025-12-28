# Task 1.5.1: Re-audit CLI Module Quality - Detailed Plan

## Task Overview

| Field | Value |
|-------|-------|
| Task ID | 01KDJNKE2B2W5NJRTSRZWN4QT4 |
| Sprint | Sprint 1.5: Module Quality Re-Audit |
| Type | research |
| Complexity | **medium** |
| Priority | high |
| Estimated Tokens | 3,000 |
| Dependencies | Sprint 1 (File Inventory Refresh) |

## Objective

Re-audit the CLI module which has seen significant structural changes since Dec 12, including the split of commands.py into modular command files. Update quality metrics, identify architectural improvements, and document the current state.

## Module Scope

```
vibey/cli/                           # 123 Python files total
├── __init__.py
├── __main__.py
├── main.py                          # Entry point (~240KB, largest file)
├── commands_legacy.py               # Legacy commands (~247KB)
├── formatters.py                    # Output formatting (~16KB)
├── error_handler.py                 # Error handling (~11KB)
├── implement.py                     # Implementation commands (~37KB)
├── git_commands.py                  # Git integration (~141KB)
├── submodule.py                     # Submodule commands (~28KB)
│
├── command_modules/                 # NEW: Modular commands (17 files)
│   ├── __init__.py
│   ├── audit.py                     # Audit commands
│   ├── checkpoint.py                # Checkpoint commands
│   ├── config.py                    # Config commands
│   ├── context.py                   # Context commands
│   ├── db.py                        # Database commands
│   ├── deploy.py                    # Deploy commands
│   ├── discover.py                  # Discover commands
│   ├── docs.py                      # Docs commands
│   ├── edit.py                      # Edit commands
│   ├── helpers.py                   # Command helpers
│   ├── hooks.py                     # Hook commands
│   ├── migrate.py                   # Migration commands
│   ├── roadmap.py                   # Roadmap commands
│   ├── session.py                   # Session commands
│   └── validate.py                  # Validation commands
│
├── commands/                        # Command implementations (16 files)
│   ├── __init__.py
│   ├── audit.py
│   ├── checkpoint.py
│   ├── config.py
│   ├── context.py                   # Context commands (~21KB)
│   ├── deploy.py
│   ├── discover.py
│   ├── docs.py
│   ├── edit.py
│   ├── hooks.py
│   ├── migrate.py
│   ├── relationship.py              # Relationship commands (~29KB)
│   ├── session.py
│   ├── tokens.py                    # Token commands (~20KB)
│   └── validate.py
│
├── roadmap_commands/                # Roadmap-specific commands (27 files)
│   ├── __init__.py
│   ├── add_from_template.py
│   ├── add_standard.py
│   ├── agents.py
│   ├── assign.py
│   ├── batch.py
│   ├── check_standards.py
│   ├── complete.py
│   ├── context.py
│   ├── deps.py
│   ├── find.py
│   ├── gate.py
│   ├── init.py
│   ├── list_cmd.py
│   ├── list_templates.py
│   ├── override_standard.py
│   ├── plan.py
│   ├── prepare.py
│   ├── progress.py
│   ├── recommend.py
│   ├── show.py                      # Show command (~15KB)
│   ├── start.py
│   ├── status.py
│   ├── summarize.py
│   ├── validate.py                  # Validation (~13KB)
│   └── version.py
│
├── roadmap_lib/                     # Roadmap CLI utilities (18 files)
│   ├── __init__.py
│   ├── activity.py
│   ├── agents.py                    # Agent helpers (~23KB)
│   ├── blockers.py
│   ├── cache_helpers.py
│   ├── cache.py                     # Caching (~29KB)
│   ├── dependencies.py
│   ├── error_messages.py            # Error formatting (~15KB)
│   ├── filesystem.py
│   ├── formatting.py
│   ├── help_formatter.py            # Help text (~14KB)
│   ├── plan_parser.py
│   ├── standards_formatter.py       # Standards (~12KB)
│   ├── status.py                    # Status display (~12KB)
│   └── versioning.py
│
├── tests/                           # CLI tests (14 files)
│
└── [standalone scripts]             # Various .py scripts
    ├── analyze-project-roadmap.py
    ├── check-version.py
    ├── deploy.py
    ├── docs.py
    ├── generate-agent.py
    ├── generate-config.py
    ├── generate-roadmap-docs.py
    ├── manage-project-context.py
    ├── migrate-dependency-cache.py
    ├── migrate-embedded-tasks.py
    ├── remediate_roadmap_system.py
    ├── render-template.py
    ├── roadmap (script)
    ├── roadmap_create_from_plan.py
    ├── roadmap-add-commit.py
    ├── roadmap-context.py
    ├── roadmap-init.py
    ├── roadmap-prepare.py
    ├── roadmap-query.py
    ├── roadmap-summarize.py
    ├── roadmap-sync-docs.py
    ├── roadmap-update.py
    ├── roadmap.py
    ├── rollback-framework.py
    ├── update-config.py
    ├── validate-config.py
    ├── validate-roadmap-format.py
    └── validate-vibey-config.py
```

## Key Changes Since Dec 12

| Change | Description |
|--------|-------------|
| commands.py split | Major refactoring into command_modules/ and commands/ |
| New command_modules/ | 17 modular command files |
| New commands/ | 16 command implementation files |
| New tokens.py | Token management commands (~20KB) |
| New relationship.py | Relationship commands (~29KB) |
| Updated context.py | Enhanced context commands (~21KB) |

## Audit Checklist

### 1. Structure Analysis

**File Inventory:**
- [ ] Count total Python files (current: ~123)
- [ ] Compare with Dec 12 baseline (original: 45)
- [ ] Identify new files added since Dec 12
- [ ] Identify deprecated/removed files
- [ ] Document file size distribution

**Directory Organization:**
- [ ] Review command_modules/ structure
- [ ] Review commands/ structure
- [ ] Review roadmap_commands/ structure
- [ ] Review roadmap_lib/ structure
- [ ] Check for orphaned standalone scripts

### 2. Code Quality Metrics

**Size Analysis:**
```bash
# Count lines of code
find vibey/cli -name "*.py" -exec wc -l {} + | sort -n

# Find largest files (>500 lines)
find vibey/cli -name "*.py" -exec wc -l {} + | awk '$1 > 500' | sort -rn

# Count functions per file
grep -c "def " vibey/cli/*.py vibey/cli/**/*.py
```

**Docstring Coverage:**
```bash
# Count functions
grep -r "def " vibey/cli --include="*.py" | wc -l

# Count docstrings
grep -r '"""' vibey/cli --include="*.py" | wc -l
```

**Type Hint Coverage:**
```bash
# Check type hints with mypy
mypy vibey/cli/ --ignore-missing-imports --show-error-counts
```

### 3. Architecture Review

**Command Migration Status:**
- [ ] Is commands.py fully deprecated?
- [ ] Are all commands migrated to command_modules/?
- [ ] Is there code duplication between old and new?
- [ ] Are imports properly updated?

**Modularity Assessment:**
- [ ] Single responsibility per module?
- [ ] Clear boundaries between modules?
- [ ] Appropriate abstraction levels?
- [ ] Circular import issues?

**Consistency Checks:**
- [ ] Consistent error handling patterns?
- [ ] Consistent output formatting?
- [ ] Consistent CLI argument patterns?
- [ ] Consistent help text style?

### 4. Dependency Analysis

**Internal Dependencies:**
```bash
# Check imports from other vibey modules
grep -r "from vibey\." vibey/cli --include="*.py" | grep -v "__pycache__"
```

**External Dependencies:**
```bash
# Check external imports
grep -r "^import \|^from [^v]" vibey/cli --include="*.py" | head -50
```

### 5. Test Coverage

```bash
# Run CLI tests with coverage
pytest tests/cli/ --cov=vibey/cli --cov-report=term-missing
```

## Quality Metrics to Collect

```python
metrics = {
    "structure": {
        "total_files": 123,           # Current count
        "python_files": 123,
        "directories": 6,
        "max_depth": 3,
    },
    "size": {
        "total_lines": 0,             # To measure
        "largest_file": "main.py",
        "largest_file_lines": 0,
        "avg_lines_per_file": 0,
        "files_over_500_lines": 0,
    },
    "quality": {
        "docstring_coverage": 0,      # Percentage
        "type_hint_coverage": 0,      # Percentage
        "test_coverage": 0,           # Percentage
    },
    "complexity": {
        "avg_cyclomatic": 0,
        "max_cyclomatic": 0,
        "files_above_10": 0,
    },
    "architecture": {
        "command_modules_migrated": 17,
        "legacy_commands_remaining": 0,
        "circular_imports": 0,
    },
}
```

## Commands for Analysis

```bash
# File count comparison
echo "=== CLI File Counts ==="
find vibey/cli -name "*.py" | wc -l
find vibey/cli/command_modules -name "*.py" | wc -l
find vibey/cli/commands -name "*.py" | wc -l
find vibey/cli/roadmap_commands -name "*.py" | wc -l
find vibey/cli/roadmap_lib -name "*.py" | wc -l

# Lines of code
echo "=== Lines of Code ==="
find vibey/cli -name "*.py" -exec cat {} + | wc -l

# Largest files
echo "=== Largest Files ==="
find vibey/cli -name "*.py" -exec wc -l {} + | sort -rn | head -20

# Check for circular imports
echo "=== Circular Import Check ==="
python -c "import vibey.cli.main" 2>&1

# Type checking
echo "=== Type Checking ==="
mypy vibey/cli/ --ignore-missing-imports 2>&1 | tail -20

# Test coverage
echo "=== Test Coverage ==="
pytest tests/cli/ --cov=vibey/cli --cov-report=term 2>&1 | tail -30
```

## Deliverables

1. **MODULE_QUALITY_AUDIT_CLI.md**
   - Comprehensive module quality report
   - Updated file inventory
   - Quality metrics with Dec 12 comparison
   - Architectural analysis
   - Issue identification

2. **CLI_MODULE_METRICS.yaml**
   - Machine-readable metrics
   - Historical comparison data

3. **CLI_MIGRATION_STATUS.md** (if applicable)
   - commands.py migration status
   - Remaining legacy code
   - Migration recommendations

## Output Template

```markdown
# CLI Module Quality Audit
**Date:** December 28, 2024
**Baseline:** December 12, 2024

## Executive Summary

The CLI module has undergone significant restructuring since Dec 12...

## Structure Analysis

### File Counts
| Category | Dec 12 | Dec 28 | Change |
|----------|--------|--------|--------|
| Total Python files | 45 | 123 | +78 |
| command_modules/ | 0 | 17 | +17 |
| commands/ | 0 | 16 | +16 |
| roadmap_commands/ | X | 27 | +Y |
| roadmap_lib/ | X | 18 | +Y |

### Lines of Code
| Metric | Dec 12 | Dec 28 | Change |
|--------|--------|--------|--------|
| Total LoC | X | Y | +Z |
| Largest file | X | main.py | - |
| Avg per file | X | Y | +Z |

## Quality Metrics

### Documentation
| Metric | Dec 12 | Dec 28 | Change |
|--------|--------|--------|--------|
| Docstring coverage | 65% | X% | +Y% |
| Type hint coverage | 40% | X% | +Y% |

### Test Coverage
| Component | Coverage |
|-----------|----------|
| command_modules/ | X% |
| commands/ | X% |
| roadmap_commands/ | X% |
| roadmap_lib/ | X% |
| Overall | X% |

## Architecture Assessment

### Command Migration
- commands.py: [DEPRECATED/ACTIVE]
- commands_legacy.py: [STATUS]
- Migration completeness: X%

### Modularity Score
- Single responsibility: [GOOD/NEEDS WORK]
- Coupling level: [LOW/MEDIUM/HIGH]
- Cohesion level: [LOW/MEDIUM/HIGH]

## Issues Found

### Critical
- [None or list]

### High Priority
1. [Issue description]
2. [Issue description]

### Medium Priority
1. [Issue description]

## Recommendations

### Immediate Actions
1. [Recommendation]

### Short-term Improvements
1. [Recommendation]

### Long-term Architecture
1. [Recommendation]
```

## Acceptance Criteria

- [ ] All 123+ Python files inventoried
- [ ] Quality metrics collected and documented
- [ ] Comparison with Dec 12 baseline complete
- [ ] Command migration status documented
- [ ] Architectural issues identified
- [ ] Recommendations prioritized
- [ ] MODULE_QUALITY_AUDIT_CLI.md updated

## Estimated Time

- File inventory: 15 minutes
- Metrics collection: 20 minutes
- Architecture review: 30 minutes
- Documentation: 25 minutes
- **Total: ~1.5 hours**
