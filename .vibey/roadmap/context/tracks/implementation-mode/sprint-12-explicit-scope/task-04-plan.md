# Update TaskSelector for hierarchical ticket scope

**Task ID**: `01KDC7N5Z3QS3JTJGT536ZWSD3`
**Sprint**: Sprint 12: Explicit Scope Requirements
**Complexity**: medium
**Estimated Tokens**: 4000

## Description

Modify TaskSelector to filter tasks based on parent ticket ULID. Implement hierarchy traversal: if ULID is a track, include all sprints/tasks; if sprint, include all tasks; if task, include only that task and its criteria.

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
