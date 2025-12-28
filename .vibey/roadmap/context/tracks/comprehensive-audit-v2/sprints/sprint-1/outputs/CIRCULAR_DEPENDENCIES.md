# Circular Dependencies Report

**Generated:** 2025-12-28
**Audit Version:** comprehensive-audit-v2

## Summary

| Metric | Value |
|--------|-------|
| Total Circular Dependencies | 9 |
| Severity: High (3+ modules) | 2 |
| Severity: Medium (2-3 modules) | 7 |

## Circular Dependencies Detected

### 1. CLI Config Migration Cycle (Length: 3)
```
vibey/cli/config_migrate.py
  -> vibey/cli/config_utils.py
    -> vibey/cli/config_migrate.py
```
**Severity:** Medium
**Impact:** Config migration commands may have initialization order issues.
**Recommendation:** Extract shared utilities to a separate module.

### 2. Session Manager Cycle (Length: 6)
```
vibey/__init__.py
  -> vibey/cli/main.py
    -> vibey/cli/commands/__init__.py
      -> vibey/cli/commands/session.py
        -> vibey/operations/roadmap/session_manager.py
          -> vibey/__init__.py
```
**Severity:** High
**Impact:** Package initialization may depend on itself through session manager.
**Recommendation:** Lazy import session_manager or restructure imports.

### 3. Commands Legacy Cycle (Length: 3)
```
vibey/cli/commands/__init__.py
  -> vibey/cli/commands_legacy.py
    -> vibey/cli/commands/__init__.py
```
**Severity:** Medium
**Impact:** Legacy command migration may have issues.
**Recommendation:** Complete commands_legacy.py deprecation.

### 4. Hierarchical Self-Reference (Length: 2)
```
vibey/roadmap/models/ticket/hierarchical.py
  -> vibey/roadmap/models/ticket/hierarchical.py
```
**Severity:** Low (likely false positive from TYPE_CHECKING imports)
**Impact:** None expected.

### 5. Ticket ORM Cycle (Length: 3)
```
vibey/roadmap/models/ticket/__init__.py
  -> vibey/roadmap/models/ticket/orm.py
    -> vibey/roadmap/models/ticket/__init__.py
```
**Severity:** Medium
**Impact:** ORM models may need careful import ordering.
**Recommendation:** Use TYPE_CHECKING guards.

### 6. Ticket Repository Cycle (Length: 3)
```
vibey/roadmap/models/ticket/__init__.py
  -> vibey/roadmap/models/ticket/repository.py
    -> vibey/roadmap/models/ticket/__init__.py
```
**Severity:** Medium
**Impact:** Repository pattern may have import issues.

### 7. Git Operations Cycle (Length: 3)
```
vibey/operations/git/__init__.py
  -> vibey/operations/git/status_updater.py
    -> vibey/operations/git/__init__.py
```
**Severity:** Medium
**Impact:** Git status updates may have initialization issues.

### 8. CLI Introspector Cycle (Length: 3)
```
vibey/cli/main.py
  -> vibey/operations/docs/cli_introspector.py
    -> vibey/cli/main.py
```
**Severity:** Medium
**Impact:** CLI documentation generation has circular dependency.
**Recommendation:** Lazy import in introspector.

### 9. MCP Introspector Cycle (Length: 3)
```
vibey/cli/main.py
  -> vibey/operations/docs/mcp_introspector.py
    -> vibey/cli/main.py
```
**Severity:** Medium
**Impact:** MCP documentation generation has circular dependency.
**Recommendation:** Lazy import in introspector.

## Recommendations

1. **Use TYPE_CHECKING guards** for type-only imports
2. **Lazy imports** for heavy dependencies
3. **Extract shared utilities** to break cycles
4. **Complete legacy code migration** to remove transitional cycles

---

*Report generated: 2025-12-28*
