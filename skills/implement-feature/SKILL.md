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
Example: `/implement-feature VIBEY-42`

## Steps

Execute each step sequentially. Do not proceed to the next step until the current one passes its quality check.

### Step 1: Design

- Understand the requirements (from the description or Jira ticket)
- Identify affected files and components
- Choose the implementation approach
- Note dependencies and risks
- **Output:** Brief design summary with file list and approach

### Step 2: Implement

- Write the code following project conventions
- Keep changes minimal and focused
- Handle errors at system boundaries
- **Quality check:** Code passes linting / type checks if configured

### Step 3: Test

- Write tests for the new functionality
- Cover happy path, edge cases, and error paths
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
- Only add docs where the code isn't self-explanatory
- **Quality check:** Key behaviors and non-obvious decisions documented

### Step 7: Commit

- Review all changes with `git diff`
- Verify no secrets in staged files
- Create a descriptive commit with ticket reference
- **Quality check:** Clean commit, all tests still pass

## Gate Policy

If any quality check fails, stop and fix the issue before proceeding. Do not skip gates. If the security review finds critical issues, return to Step 2 and fix them.
