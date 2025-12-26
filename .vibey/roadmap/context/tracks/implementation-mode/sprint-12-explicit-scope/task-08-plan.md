# Add tests for explicit scope requirements

**Task ID**: `01KDC7N5Z6BEX8F9V0V8Q5DK40`
**Sprint**: Sprint 12: Explicit Scope Requirements
**Complexity**: medium
**Estimated Tokens**: 5000

## Description

Write tests for: (1) bare command shows help, (2) --all-tickets enables full execution, (3) --ticket filters correctly by hierarchy, (4) completion detection works for parent tickets, (5) deprecated options still work with warnings.

## Sprint Context

This sprint updates the `vibey implement` command to require explicit scope specification, preventing accidental full-roadmap execution.

**Key Changes:**
1. Bare `vibey implement` command shows help instead of executing
2. `--all-tickets` flag required for full roadmap execution
3. `--ticket ULID` replaces `--track` and `--sprint` with unified hierarchical targeting

## Acceptance Criteria

- [ ] Implementation matches description
- [ ] Tests pass
- [ ] Documentation updated
- [ ] Backward compatibility maintained for deprecated options
