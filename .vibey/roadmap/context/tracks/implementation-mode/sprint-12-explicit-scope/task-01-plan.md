# Remove default full-roadmap execution

**Task ID**: `01KDC7N5Z1G71B3E111RJT4S8V`
**Sprint**: Sprint 12: Explicit Scope Requirements
**Complexity**: simple
**Estimated Tokens**: 2000

## Description

Change `vibey implement` without arguments to show usage help instead of executing all tasks. Display available options and prompt user to specify scope explicitly.

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
