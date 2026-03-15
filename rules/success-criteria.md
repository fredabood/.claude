---
description: Deterministic acceptance criteria — every ticket must have measurable, binary pass/fail criteria before work begins
globs:
  - "**/*"
---

# Success Criteria — Deterministic Acceptance Standards

Every Jira ticket must have deterministic, measurable acceptance criteria. Enforce this automatically.

## Before starting work (soft gate)

When transitioning a ticket to "In Progress", check for an `Acceptance Criteria` section in the description. If missing:

1. Prompt: "This ticket has no acceptance criteria. Would you like me to draft some before we begin?"
2. If the user agrees, draft criteria based on the ticket description and post as a Jira comment (or suggest editing the description).
3. If the user declines, note the gap and proceed — but flag it again at completion time.

## Criteria format

Every ticket's acceptance criteria must follow this structure:

```
## Acceptance Criteria
- [ ] <Specific verifiable condition>
- [ ] Tests pass: `<command>`
- [ ] No security regressions
- [ ] Documentation updated (if applicable)
```

## Criteria requirements

Each criterion must be:
- **Measurable** — verifiable with a test, command, or direct observation
- **Deterministic** — binary pass/fail, no subjective judgment
- **Complete** — covers happy path, error paths, and integration points

At minimum, every ticket needs:
1. At least one **functional criterion** (the thing works as described)
2. At least one **test-based criterion** (`Tests pass: <command>`)
3. A **security criterion** (no regressions)

## Before completing work (hard gate)

When running `/complete-task` or closing a ticket:

1. Extract the acceptance criteria checklist from the ticket
2. Verify **each criterion individually** with evidence
3. Post a verification report to Jira as a comment
4. **Do not transition to Done if any criterion fails** — list what needs fixing instead
