# Obsolete Code Inventory

## Overview

Inventory of code that may be obsolete or redundant based on system redesigns and audits.

**Analyzed**: 2025-12-16
**Sources**: Phase 1 audit findings, directory structure analysis

---

## Identified Obsolete Code

### High Confidence (Safe to Remove)

#### 1. Hierarchical Directory Support
**Location**: Various loaders and serializers
**Reason**: Flat ULID structure replaced hierarchical nesting
**Evidence**: ADR-0002 documents the migration
**Impact**: Medium - affects loading code paths
**Action**: Remove hierarchical path handling after verifying no usage

#### 2. Slug-Based ID Handling
**Location**: CLI commands, validators
**Reason**: ULID identifiers are now standard
**Evidence**: ADR-0001 documents ULID adoption
**Impact**: Low - backward compatibility code
**Action**: Can remove after deprecation period

### Medium Confidence (Needs Verification)

#### 3. Legacy YAML Schema Support
**Location**: `vibey/roadmap/serialization/`
**Reason**: Schema may have evolved
**Evidence**: Multiple YAML format versions observed
**Impact**: Medium - affects data loading
**Action**: Audit schema versions in use before removal

#### 4. Old Activity Log Format
**Location**: Activity log handlers
**Reason**: Migrated to JSONL format
**Evidence**: Sprint 7 (Activity Log Migration) completed
**Impact**: Low - migration completed
**Action**: Verify no old format files exist before removal

### Low Confidence (Keep for Now)

#### 5. Backup File Handlers
**Location**: `.vibey/safe-edit-backups/`
**Reason**: May still be needed for recovery
**Evidence**: Backup files found in repo
**Impact**: Very Low - disk space only
**Action**: Implement cleanup policy rather than removal

---

## Dead Code Analysis

### Unreferenced Functions

Based on code review, the following patterns may indicate dead code:

| Pattern | Potential Location | Action |
|---------|-------------------|--------|
| `_old_*` functions | Various modules | Audit and remove |
| `legacy_*` functions | Serialization | Audit and remove |
| Commented code blocks | Throughout | Review and remove |

### Unused Imports

Run static analysis to find unused imports:
```bash
# Recommended command
ruff check vibey/ --select F401
```

---

## Redundant Code

### Duplicate Logic

#### 1. Multiple ID Validation Functions
**Locations**: CLI validators, model validators, serialization
**Issue**: Same validation logic repeated
**Action**: Consolidate to single validation module

#### 2. Path Construction Utilities
**Locations**: Multiple modules construct roadmap paths
**Issue**: Repeated path logic
**Action**: Centralize in single path utilities module

---

## Deprecated Patterns

### Patterns to Phase Out

| Pattern | Replacement | Timeline |
|---------|-------------|----------|
| Slug-based file lookup | ULID-based lookup | Q1 2026 |
| Nested directory traversal | Flat directory scan | Immediate |
| Manual progress calculation | Trigger-based updates | Q1 2026 |

---

## Summary

| Category | Items | Priority |
|----------|-------|----------|
| High Confidence Removals | 2 | High |
| Medium Confidence | 2 | Medium |
| Low Confidence | 1 | Low |
| Dead Code | 3 patterns | Medium |
| Redundant Code | 2 | Medium |
| Deprecated Patterns | 3 | Low |

## Recommended Actions

### Immediate (Low Risk)
1. Remove commented code blocks
2. Run ruff to identify unused imports
3. Document deprecated patterns

### Short-term (Medium Risk)
4. Consolidate ID validation functions
5. Remove old activity log format support
6. Centralize path construction

### Medium-term (Higher Risk)
7. Remove hierarchical directory support
8. Remove slug-based ID handling (after deprecation)
9. Clean up legacy YAML schema support

## Technical Debt Impact

Removing identified obsolete code could:
- Reduce codebase by ~5-10%
- Improve maintainability
- Reduce test surface area
- Simplify onboarding

**Estimated Cleanup Effort**: 8-16 hours for full cleanup
