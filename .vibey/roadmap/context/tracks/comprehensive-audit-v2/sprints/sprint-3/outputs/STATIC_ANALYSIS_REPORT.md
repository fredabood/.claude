# Static Analysis Report

**Task:** 01KDJKTRVZS618BM5ZZTQ34435
**Sprint:** Sprint 3 - Codebase Health Analysis
**Generated:** 2025-12-28T21:30:00+00:00

---

## Executive Summary

Static analysis reveals **6,783 ruff issues** and **133 mypy errors**. The majority of issues are style-related (deprecated type annotations) rather than functional bugs.

---

## Ruff Linter Results

| Metric | Value |
|--------|-------|
| Total Issues | 6,783 |
| Auto-fixable | 1,352 |
| Unsafe-fixable | 3,412 |

### Issue Distribution by Category

| Code | Count | Description | Severity |
|------|-------|-------------|----------|
| UP006 | 3,168 | non-pep585-annotation (use `list` not `List`) | Style |
| E501 | 1,122 | line-too-long (>100 chars) | Style |
| I001 | 628 | unsorted-imports | Style |
| UP035 | 577 | deprecated-import (`typing.List` etc) | Style |
| F541 | 432 | f-string-missing-placeholders | Warning |
| UP045 | 183 | non-pep604-annotation-optional | Style |
| E402 | 168 | module-import-not-at-top-of-file | Warning |
| UP015 | 165 | redundant-open-modes | Style |
| F401 | 85 | unused-import | Warning |
| F841 | 71 | unused-variable | Warning |
| **F821** | **53** | **undefined-name** | **Error** |
| N999 | 22 | invalid-module-name | Warning |
| UP037 | 19 | quoted-annotation | Style |
| E741 | 17 | ambiguous-variable-name | Warning |
| N806 | 14 | non-lowercase-variable-in-function | Style |
| E722 | 13 | bare-except | Warning |
| F402 | 10 | import-shadowed-by-loop-var | Warning |
| Others | 36 | Various minor issues | Mixed |

### Priority Analysis

| Priority | Issue Types | Count | Action |
|----------|-------------|-------|--------|
| **High** | F821 (undefined-name) | 53 | Fix immediately |
| **Medium** | F401, F841, E722, F402 | 179 | Fix in next sprint |
| **Low** | Style issues (UP*, I001, E501) | 6,551 | Batch fix with --fix |

---

## Mypy Type Checker Results

| Metric | Value |
|--------|-------|
| Total Errors | 133 |
| Files with Errors | 133 |

### Error Categories

| Category | Count | Description |
|----------|-------|-------------|
| import-untyped | 132 | Missing YAML type stubs |
| syntax | 1 | Python 3.10+ pattern matching in dependency |

### Resolution

```bash
# Install missing type stubs
pip install types-PyYAML

# Or add to pyproject.toml
[tool.mypy]
ignore_missing_imports = true
```

---

## Prioritized Fix List

### Immediate (Errors)

1. **F821: undefined-name (53 issues)**
   - These are actual runtime errors waiting to happen
   - Review each for missing imports or typos

### Short-term (Warnings)

2. **F401: unused-import (85 issues)**
   - Dead code, increases load time
   - Safe to auto-fix: `ruff check --fix --select F401`

3. **F841: unused-variable (71 issues)**
   - Dead code, memory waste
   - Review before fixing (may indicate incomplete code)

4. **E722: bare-except (13 issues)**
   - Security/debugging concern
   - Replace with specific exception types

### Long-term (Style)

5. **UP006/UP035: deprecated annotations (3,745 issues)**
   - Batch fix: `ruff check --fix --select UP006,UP035`
   - Low risk, high impact on code modernization

6. **I001: import sorting (628 issues)**
   - Batch fix: `ruff check --fix --select I001`
   - Purely cosmetic

7. **E501: line-too-long (1,122 issues)**
   - Review case-by-case
   - Some may be acceptable (URLs, strings)

---

## Recommendations

1. **Install type stubs**: `pip install types-PyYAML`
2. **Run safe auto-fix**: `ruff check vibey/ --fix --select I001,UP015,UP037`
3. **Review F821 errors**: These are real bugs
4. **Update pyproject.toml**: Move `select` to `lint.select`
5. **Consider pre-commit hook**: Auto-fix on commit

---

## Configuration Issues

```
warning: The top-level linter settings are deprecated in favour of their counterparts in the `lint` section. Please update the following options in `pyproject.toml`:
  - 'select' -> 'lint.select'
```

---

*Report generated: 2025-12-28T21:30:00+00:00*
