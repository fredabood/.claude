---
description: Deterministic acceptance criteria — every issue must have measurable, binary pass/fail criteria before work begins
globs:
  - "**/*"
---

# Success Criteria — Deterministic Acceptance Standards

> Invoke `/workflow` for Phases 2 (criteria drafting) and 6 (verification) with deterministic hook enforcement.

Every GitHub issue must have deterministic, measurable acceptance criteria. Enforce this automatically.

## Before starting work (soft gate)

When moving an issue to board Status "In Progress", check for an `## Acceptance Criteria` task list in the issue **body** (`mcp__github__issue_read`, method `get`). If missing:

1. Prompt: "This issue has no acceptance criteria. Would you like me to draft some before we begin?"
2. If the user agrees, draft criteria based on the issue description and add them to the issue body via `mcp__github__issue_write` (the body is the canonical location — it renders task-list progress).
3. If the user declines, note the gap and proceed — but flag it again at completion time.

## Criteria format

Every issue's acceptance criteria must be a native task list under this heading in the issue **body**:

```
## Acceptance Criteria
- [ ] <Specific verifiable condition>
- [ ] Tests pass: `<command>`
- [ ] No security regressions
- [ ] Documentation updated (if applicable)
```

If a criterion needs standalone tracking, convert the task-list item to a sub-issue (`mcp__github__sub_issue_write`). Optional markers prepend to the criterion text, e.g. `- [ ] [pytest:test_foo] [HUMAN-APPROVAL] <condition>` (see `.claude/rules/custom-fields.md`).

## Criteria requirements

Each criterion must be:
- **Measurable** — verifiable with a test, command, or direct observation
- **Deterministic** — binary pass/fail, no subjective judgment
- **Complete** — covers happy path, error paths, and integration points

At minimum, every issue needs:
1. At least one **functional criterion** (the thing works as described)
2. At least one **test-based criterion** (`Tests pass: <command>`)
3. A **security criterion** (no regressions)

## Before completing work (hard gate)

When running `/complete-task` or closing an issue:

1. Extract the acceptance criteria task list from the issue body
2. Verify **each criterion individually** with evidence
3. Post a verification report as an issue comment (`mcp__github__add_issue_comment`) under the `## Verification Report` marker, with `### Criteria Tested` and `### Results Summary` sections
4. Check off the verified items in the body task list
5. **Do not close the issue as completed (`state_reason: completed`) if any criterion fails** — list what needs fixing instead
