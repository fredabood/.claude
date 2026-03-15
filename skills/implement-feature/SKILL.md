---
description: 7-step feature development lifecycle — from design through commit with quality gates
user_invocable: true
---

# /implement-feature

Walk through a complete feature development lifecycle in 7 steps with quality gates between each phase.

## Usage

```
/implement-feature "<feature description>"
/implement-feature <ISSUE-KEY>
```

Example: `/implement-feature "Add user profile page with avatar upload"`
Example: `/implement-feature PROJ-42`

## Steps

Execute each step sequentially. Do not proceed to the next step until the current one passes its quality check.

### Step 1: Design

- **Ensure a ticket exists:**
  - If input is a ticket key (e.g., `PROJ-42`), fetch it with `getJiraIssue`
  - If input is a description, search Jira for an existing ticket. If none found, create one using `/create-ticket` logic.
- **Transition to In Progress** if not already (transition ID `"21"`)
- **Check acceptance criteria** — If the ticket has no acceptance criteria, draft them and confirm with the user before proceeding
- Understand the requirements (from the description or Jira ticket)
- Identify affected files and components
- Choose the implementation approach
- Note dependencies and risks
- **Post implementation plan to Jira** — Use `addCommentToJiraIssue` to post a plan comment including:
  - Files to modify
  - Approach and rationale
  - Testing strategy (types of tests, specific scenarios, commands)
  - Documentation plan (what docs/memory to update)
  - Risks and mitigations
- **Output:** Brief design summary with file list and approach

### Step 2: Implement

- Write the code following project conventions
- Keep changes minimal and focused
- Handle errors at system boundaries
- **Quality check:** Code passes linting / type checks if configured

### Step 3: Test

- Write tests for the new functionality
- Cover happy path, edge cases, and error paths
- For bug fixes, start with a failing test that reproduces the bug
- Run the full test suite to check for regressions
- **Quality check:** All tests pass, coverage adequate for business logic

### Step 4: Security Review

Review the changed code against these 9 areas:

1. **Hardcoded secrets** — grep for API keys, passwords, tokens in changed files
2. **Environment variables** — verify secrets come from env vars, not code
3. **Input sanitization** — check for SQL injection, XSS, URL injection risks
4. **Logging** — ensure no credentials or PII in log statements
5. **Rate limiting** — verify external API calls have appropriate limits
6. **TLS/HTTPS** — all external URLs use HTTPS, no disabled SSL verification
7. **Error messages** — no system internals or credentials leaked in errors
8. **Dependencies** — no known CVEs in new dependencies
9. **Test security** — no real credentials in test code, external calls mocked

- **Quality check:** No critical or high severity issues. Fix any found before proceeding.

### Step 5: Integration

- Ensure the feature integrates with the existing codebase
- Wire up routes, configuration, or registration as needed
- Run integration tests if they exist
- **Quality check:** Feature accessible and working end-to-end

### Step 6: Documentation

- Update relevant documentation (README, API docs, inline comments)
- Update docs in `docs/` if operational behavior changed
- Update memory files if project-level knowledge or decisions changed
- Only add docs where the code isn't self-explanatory
- **Quality check:** Key behaviors and non-obvious decisions documented

### Step 6.5: Update Jira

Post a milestone comment to Jira using `addCommentToJiraIssue` summarizing:
- What was implemented
- Tests added
- Documentation updated
- Any deviations from the plan posted in Step 1

### Step 7: Commit

- Review all changes with `git diff`
- Verify no secrets in staged files
- Create a descriptive commit with ticket reference in format `KEY-123: <description>`
- **Quality check:** Clean commit, all tests still pass

## Gate Policy

If any quality check fails, stop and fix the issue before proceeding. Do not skip gates. If the security review finds critical issues, return to Step 2 and fix them.

## Required MCP Tools

- `getJiraIssue` (cloudId, issueIdOrKey)
- `transitionJiraIssue` (cloudId, issueIdOrKey, transition: { id: "21" })
- `addCommentToJiraIssue` (cloudId, issueIdOrKey, body)
- `searchJiraIssuesUsingJql` (cloudId, jql)
- `createJiraIssue` (cloudId, fields)

## CloudId

Use the project's configured Jira CloudId from CLAUDE.md.
