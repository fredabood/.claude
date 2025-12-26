# Add completion detection for parent tickets

**Task ID**: `01KDC7N5Z4HSMXG430A6WA831Y`
**Sprint**: Sprint 12: Explicit Scope Requirements
**Complexity**: medium
**Estimated Tokens**: 4000

## Description

Implement logic to detect when all children of a --ticket ULID are complete. Auto-mark parent as complete when all children pass. Stop loop when target ticket reaches completed status.

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
