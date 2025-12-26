# Implement --ticket ULID option for targeted execution

**Task ID**: `01KDC7N5Z2FQZEH01CCXKXQZ91`
**Sprint**: Sprint 12: Explicit Scope Requirements
**Complexity**: medium
**Estimated Tokens**: 5000

## Description

Add --ticket option accepting a ULID. Determine ticket type (track/sprint/task) and execute all child tickets until the specified ULID can be marked complete. This replaces --track and --sprint with a unified approach.

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
