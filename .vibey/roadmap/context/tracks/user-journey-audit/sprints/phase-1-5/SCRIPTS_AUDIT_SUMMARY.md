# Scripts & Project Config Audit Summary

**Generated:** 2025-12-12
**Sprint:** Phase 1.5 - Scripts & Project Config Audit
**Track:** User Journey Audit & Documentation Coverage

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Scripts audited | 4 |
| Config files audited | 6 |
| Scripts to deprecate | 4 (100%) |
| CLI migration candidates | 0 |
| Config settings to fix | 2 |
| Average script quality score | 40.3/100 (F) |
| Average config quality score | 89.0/100 (B+) |

**Key Finding:** All 4 scripts are one-time utilities that have completed their purpose and should be deprecated. Configuration files are generally well-maintained with 2 issues requiring immediate attention.

---

## Scripts Inventory

### Directory Overview

```
scripts/
├── consolidate_dogfooding_track.py  (589 lines, 25KB) - DEPRECATE
├── create_dogfooding_track.py       (565 lines, 25KB) - DEPRECATE
├── execute_migration.py             (161 lines, 5KB)  - DEPRECATE
└── run_migration_standalone.py      (159 lines, 5KB)  - DELETE (security)
```

**Total:** 1,474 lines, 60KB

### Script Quality Scores

| Script | Quality | Purpose | Code | Integration | Maintenance | Grade |
|--------|---------|---------|------|-------------|-------------|-------|
| consolidate_dogfooding_track.py | 40 | 5 | 18 | 5 | 12 | F |
| create_dogfooding_track.py | 32 | 3 | 16 | 3 | 10 | F |
| execute_migration.py | 63 | 8 | 22 | 18 | 15 | D |
| run_migration_standalone.py | 26 | 3 | 12 | 3 | 8 | F |

### Script Categories

| Category | Scripts | Total Lines | % of Total |
|----------|---------|-------------|------------|
| Roadmap Management | 2 | 1,154 | 78% |
| Migration | 2 | 320 | 22% |

---

## Configuration Files Overview

### Files Audited

| File | Purpose | Size | Grade |
|------|---------|------|-------|
| pyproject.toml | Python project config | 2.4KB | A (97) |
| pytest.ini | Test configuration | 1.0KB | B (82) |
| .coveragerc | Coverage config | 1.0KB | B (81) |
| .pre-commit-config.yaml | Pre-commit hooks | 2.2KB | A (93) |
| .gitignore | Git ignore patterns | 1.4KB | A (100) |
| MANIFEST.in | Package manifest | 86B | B (81) |

### Configuration Issues Found

#### Critical Issues (Fix Immediately)

1. **`.coveragerc` source path incorrect**
   - Current: `source = framework`
   - Should be: `source = vibey`
   - Impact: Coverage reports are incorrect

2. **Coverage threshold unrealistic**
   - Files: `pytest.ini`, `.coveragerc`
   - Current: `fail_under = 90`
   - Actual coverage: 28.5%
   - Recommended: `fail_under = 50` (increase incrementally)

#### Minor Issues

3. **Line length inconsistency**
   - `pyproject.toml` Black: 100
   - `.pre-commit-config.yaml` Black: 120
   - Recommendation: Standardize on one value

4. **Duplicated pytest config**
   - Present in both `pyproject.toml` and `pytest.ini`
   - Recommendation: Consolidate in `pyproject.toml`

---

## CLI Migration Assessment

### Summary

**Conclusion: No scripts warrant CLI migration**

All 4 scripts are one-time utilities that have completed their intended tasks:

| Script | Last Used | Task Status | CLI Candidate |
|--------|-----------|-------------|---------------|
| consolidate_dogfooding_track.py | 2025-12-10 | Complete | No |
| create_dogfooding_track.py | 2025-12-09 | Superseded | No |
| execute_migration.py | 2025-12-09 | Complete | No |
| run_migration_standalone.py | 2025-12-09 | Duplicate | No |

### Future Considerations

If similar functionality is needed in the future:

1. **Track consolidation** → Implement `vibey roadmap consolidate` command
2. **Data migration** → Implement versioned `vibey roadmap migrate` command
3. **Batch track creation** → Use existing `vibey roadmap create-from-plan`

---

## Deprecation Plan

### Immediate Actions (Do Now)

| Action | Item | Reason | Risk |
|--------|------|--------|------|
| DELETE | `run_migration_standalone.py` | exec() security risk + duplicate | Low |
| DELETE | `create_dogfooding_track.py` | Superseded, obsolete | Low |
| FIX | `.coveragerc` source | Points to wrong directory | Low |

### Short-term Actions (Within 30 Days)

| Action | Item | Reason |
|--------|------|--------|
| ARCHIVE | `consolidate_dogfooding_track.py` | One-time, task complete |
| ARCHIVE | `execute_migration.py` | One-time, migration complete |
| FIX | Coverage threshold | Set achievable target |

### Archive Process

For scripts being archived:
1. Create `scripts/deprecated/` directory
2. Move scripts with `.deprecated` suffix
3. Add README explaining purpose and completion date
4. Remove after 30 days if no issues

---

## Security Assessment

### Concerns Found

| Severity | Script | Issue |
|----------|--------|-------|
| Medium | run_migration_standalone.py | Uses `exec(open(file).read())` |

**Recommendation:** Delete `run_migration_standalone.py` immediately. The `exec()` pattern allows arbitrary code execution if the migration file is compromised.

### No Concerns

- No hardcoded credentials
- No external network calls
- No sensitive data handling
- No shell injection risks (except exec pattern above)

---

## Recommendations

### Priority 1 - Immediate (This Sprint)

- [ ] **DELETE** `scripts/run_migration_standalone.py` (security concern)
- [ ] **DELETE** `scripts/create_dogfooding_track.py` (obsolete)
- [ ] **FIX** `.coveragerc` source to `vibey`

### Priority 2 - Short Term (Next Sprint)

- [ ] **ARCHIVE** remaining scripts to `scripts/deprecated/`
- [ ] **FIX** coverage threshold to achievable level (50%)
- [ ] **STANDARDIZE** line length across tools

### Priority 3 - Long Term (Future)

- [ ] **CONSOLIDATE** pytest config into `pyproject.toml` only
- [ ] **REMOVE** `scripts/` directory when confident
- [ ] **DOCUMENT** migration patterns for future reference

---

## Cross-File Analysis

### Consistency Check

| Setting | pyproject.toml | pytest.ini | .pre-commit | .coveragerc |
|---------|----------------|------------|-------------|-------------|
| Python version | >=3.9 | - | - | - |
| Line length | 100 | - | 120 | - |
| Coverage source | vibey | vibey | - | framework (BUG) |
| Coverage threshold | - | 90 | - | 90 |

### Redundancies

1. **pytest configuration** duplicated in `pyproject.toml` and `pytest.ini`
2. **coverage configuration** split between `pytest.ini` and `.coveragerc`

**Recommendation:** Consolidate all tool configuration in `pyproject.toml` where possible.

---

## Appendix: Deliverables Created

| File | Type | Description |
|------|------|-------------|
| SCRIPTS_AUDIT_CRITERIA.md | Criteria | Audit criteria framework |
| SCRIPTS_INVENTORY.yaml | Data | Complete scripts inventory |
| AUDIT_PROJECT_CONFIG.yaml | Data | Configuration files audit |
| AUDIT_SCRIPTS_CONSOLIDATED.yaml | Data | Individual script audits |
| CLI_MIGRATION_CANDIDATES.yaml | Analysis | CLI migration assessment |
| DEPRECATION_CANDIDATES.yaml | Analysis | Deprecation recommendations |
| SCRIPTS_AUDIT_SUMMARY.md | Summary | This document |

---

## Conclusion

The scripts directory contains only one-time utilities that have completed their purpose. All 4 scripts should be deprecated, with 2 deleted immediately (security/obsolete) and 2 archived for 30 days before deletion.

Configuration files are generally well-maintained with 2 immediate fixes needed:
1. Fix `.coveragerc` source path
2. Lower unrealistic coverage threshold

**No scripts need CLI migration.** If similar functionality is needed in the future, implement as proper CLI commands with tests and documentation.

---

*Generated by Sprint 1.5 - Scripts & Project Config Audit*
