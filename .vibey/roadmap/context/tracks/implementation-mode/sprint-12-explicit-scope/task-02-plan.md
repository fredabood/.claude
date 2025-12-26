# Add --all-tickets flag for full roadmap execution

**Task ID**: `01KDC7N5Z2FQZEH01CCXKXQZ90`
**Sprint**: Sprint 12: Explicit Scope Requirements
**Complexity**: simple
**Estimated Tokens**: 3000

## Description

Implement --all-tickets flag that explicitly enables full-roadmap execution. This flag replaces the current default behavior. Add confirmation prompt: 'This will execute all planned tasks across the entire roadmap. Continue? [y/N]'

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
