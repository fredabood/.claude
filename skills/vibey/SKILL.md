---
description: "Vibey development workflows — task management, feature implementation, sprint planning, and more. Subcommands: start, complete, status, implement, plan, handoff, discover"
user_invocable: true
---

# /vibey

Unified entry point for Vibey development workflows. Parse the first argument as a subcommand and execute the corresponding workflow.

## Usage

```
/vibey <subcommand> [args]
```

| Subcommand | What it does |
|------------|-------------|
| `start <KEY>` | Transition Jira ticket to In Progress, set working context |
| `complete <KEY>` | Run quality gates, summarize work, transition to Done |
| `status [KEY]` | Query Jira for active sprint overview |
| `implement "<desc>" or <KEY>` | 7-step dev lifecycle with quality gates |
| `plan [KEY]` | 9-step sprint planning with prioritization |
| `handoff` | Generate session summary for continuity |
| `discover [path]` | Codebase analysis: structure, stack, quality, roadmap |

## CloudId

Use the project's configured Jira CloudId from CLAUDE.md for all Jira API calls.

---

## Subcommand: `start`

Start working on a Jira ticket. Transitions the issue to "In Progress", adds a context comment, and sets up the working context for the session.

### Usage

```
/vibey start <ISSUE-KEY>
```

### Steps

1. **Fetch the ticket** — Use `getJiraIssue` to retrieve the issue details (summary, description, acceptance criteria, status, assignee)

2. **Validate state** — Confirm the ticket is not already "Done". If it's already "In Progress", note that and skip the transition.

3. **Transition to In Progress** — Call `transitionJiraIssue` with transition ID `"21"` to move the ticket to "In Progress"

4. **Add a context comment** — Use `addCommentToJiraIssue` to post:
   ```
   Starting work on this ticket.
   Session: [current date/time]
   ```

5. **Set working context** — Summarize the ticket for the session:
   - Issue key and summary
   - Description / acceptance criteria
   - Any linked issues or blockers
   - Relevant files (if mentioned in the ticket)

6. **Output** — Display a brief summary confirming the task is started and what needs to be done.

### Required MCP Tools

- `getJiraIssue` (cloudId, issueIdOrKey)
- `transitionJiraIssue` (cloudId, issueIdOrKey, transition: { id: "21" })
- `addCommentToJiraIssue` (cloudId, issueIdOrKey, body)

---

## Subcommand: `complete`

Finish work on a Jira ticket. Runs quality checks, adds a summary comment documenting what was done, and transitions the issue to "Done".

### Usage

```
/vibey complete <ISSUE-KEY>
```

### Steps

1. **Fetch the ticket** — Use `getJiraIssue` to retrieve current state and confirm it's "In Progress"

2. **Run quality gates** — Before completing, verify:
   - All tests pass (run the project's test suite)
   - No obvious security issues in changed files (grep for hardcoded secrets)
   - Changed files are committed

3. **Generate summary** — Collect:
   - Files changed (`git diff --name-only` against the branch start)
   - Key decisions made during implementation
   - Any deviations from the original ticket description
   - Anything the next person should know

4. **Add summary comment** — Use `addCommentToJiraIssue` to post the summary in Markdown format

5. **Transition to Done** — Call `transitionJiraIssue` with transition ID `"31"` to move the ticket to "Done"

6. **Check parent epic** — If this ticket has a parent epic, use `searchJiraIssuesUsingJql` with `parent = <epic-key> AND status != Done` to check if all sibling tasks are done. If so, note that the epic may be ready to close.

7. **Output** — Confirm completion with a brief summary.

### Required MCP Tools

- `getJiraIssue` (cloudId, issueIdOrKey)
- `transitionJiraIssue` (cloudId, issueIdOrKey, transition: { id: "31" })
- `addCommentToJiraIssue` (cloudId, issueIdOrKey, body)
- `searchJiraIssuesUsingJql` (cloudId, jql)

---

## Subcommand: `status`

Query Jira for a project overview showing active work, blockers, and progress.

### Usage

```
/vibey status
/vibey status <PROJECT-KEY>
```

### Steps

1. **Determine project** — Use the project key from the argument, or infer from CLAUDE.md / recent git history

2. **Query active sprint** — Use `searchJiraIssuesUsingJql`:
   ```
   project = <KEY> AND sprint in openSprints() ORDER BY status ASC, priority DESC
   ```

3. **Query blockers** — Use `searchJiraIssuesUsingJql`:
   ```
   project = <KEY> AND status != Done AND (labels = blocker OR priority = Highest)
   ```

4. **Format overview** — Display a structured summary:

   ```
   ## Project Status: <PROJECT-KEY>

   ### Active Sprint: <sprint name>
   | Key | Summary | Status | Assignee |
   |-----|---------|--------|----------|
   | ... | ...     | ...    | ...      |

   ### Progress
   - To Do: X
   - In Progress: Y
   - Done: Z

   ### Blockers
   - <KEY>: <summary> (reason)
   ```

5. **Output** — Display the formatted overview.

### Required MCP Tools

- `searchJiraIssuesUsingJql` (cloudId, jql)

---

## Subcommand: `implement`

Walk through a complete feature development lifecycle in 7 steps with quality gates between each phase.

### Usage

```
/vibey implement "<feature description>"
/vibey implement <ISSUE-KEY>
```

### Steps

Execute each step sequentially. Do not proceed to the next step until the current one passes its quality check.

#### Step 1: Design

- Understand the requirements (from the description or Jira ticket)
- Identify affected files and components
- Choose the implementation approach
- Note dependencies and risks
- **Output:** Brief design summary with file list and approach

#### Step 2: Implement

- Write the code following project conventions
- Keep changes minimal and focused
- Handle errors at system boundaries
- **Quality check:** Code passes linting / type checks if configured

#### Step 3: Test

- Write tests for the new functionality
- Cover happy path, edge cases, and error paths
- Run the full test suite to check for regressions
- **Quality check:** All tests pass, coverage adequate for business logic

#### Step 4: Security Review

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

#### Step 5: Integration

- Ensure the feature integrates with the existing codebase
- Wire up routes, configuration, or registration as needed
- Run integration tests if they exist
- **Quality check:** Feature accessible and working end-to-end

#### Step 6: Documentation

- Update relevant documentation (README, API docs, inline comments)
- Only add docs where the code isn't self-explanatory
- **Quality check:** Key behaviors and non-obvious decisions documented

#### Step 7: Commit

- Review all changes with `git diff`
- Verify no secrets in staged files
- Create a descriptive commit with ticket reference
- **Quality check:** Clean commit, all tests still pass

### Gate Policy

If any quality check fails, stop and fix the issue before proceeding. Do not skip gates. If the security review finds critical issues, return to Step 2 and fix them.

---

## Subcommand: `plan`

Run a structured sprint planning process that analyzes current project state, gathers requirements, and produces an actionable sprint plan.

### Usage

```
/vibey plan
/vibey plan <PROJECT-KEY>
```

### Steps

#### Step 1: Analyze Current State

- Review CLAUDE.md for project context and conventions
- Check `git log --oneline -20` for recent development activity
- Query Jira for current sprint status:
  ```
  project = <KEY> AND sprint in openSprints()
  ```
- Identify what's done, what's in progress, what's blocked

#### Step 2: Gather Requirements

- Query Jira backlog:
  ```
  project = <KEY> AND status = "To Do" ORDER BY priority DESC
  ```
- Identify any epics with remaining work:
  ```
  project = <KEY> AND type = Epic AND status != Done
  ```
- Ask the user about priorities, deadlines, or new requirements

#### Step 3: Assess Technical Feasibility

- For each candidate item, consider:
  - Is the approach clear or does it need research?
  - Are there dependencies on other tickets?
  - Are there infrastructure or access requirements?
- Flag high-risk items that need spikes or prototypes

#### Step 4: Map Dependencies

- Identify which tickets block others
- Determine what can be parallelized
- Find the critical path (longest sequential chain)

#### Step 5: Prioritize

Score each item using Value / Effort / Risk:

- **Value (1-5):** Business impact, user value
- **Effort (1-5):** Time and complexity
- **Risk (1-5):** Unknowns, technical risk

**Priority = (Value x 2) - (Effort + Risk)**
- High priority: score >= 5
- Medium priority: score 2-4
- Low priority: score <= 1

#### Step 6: Create Sprint Plan

Produce a structured plan:

```markdown
## Sprint Plan: <Sprint Name>
**Duration:** <X weeks>
**Goal:** <one-line sprint goal>

### Tickets (ordered by priority)
| Key | Summary | Priority | Estimate | Dependencies |
|-----|---------|----------|----------|-------------|
| ... | ...     | High     | 2d       | None        |

### Milestones
- Week 1: <milestone>
- Week 2: <milestone>

### Risks
- <risk and mitigation>
```

#### Step 7: Update Jira

- Create any new tickets identified during planning
- Update priorities and sprint assignments in Jira
- Link dependent tickets

#### Step 8: Update CLAUDE.md

- Update the project's CLAUDE.md with current sprint focus
- Document any new conventions or decisions

#### Step 9: Commit Planning Artifacts

- Commit any documentation changes
- Include sprint plan reference in commit message

### Required MCP Tools

- `searchJiraIssuesUsingJql` (cloudId, jql)
- `createJiraIssue` (cloudId, fields)
- `editJiraIssue` (cloudId, issueIdOrKey, fields)
- `addCommentToJiraIssue` (cloudId, issueIdOrKey, body)

---

## Subcommand: `handoff`

Generate a summary of the current session for continuity. Captures what was done, what's pending, key decisions, and context the next session needs.

### Usage

```
/vibey handoff
```

### Steps

1. **Collect session activity:**
   - Files changed: `git diff --name-only` (staged and unstaged)
   - Commits made: `git log --oneline` since session start (compare to recent history)
   - Jira tickets touched (if any `start` or `complete` was used)

2. **Summarize work done:**
   - What features were implemented or bugs fixed
   - What tests were added or updated
   - What documentation was changed

3. **Capture decisions:**
   - Any design choices made and their rationale
   - Any trade-offs accepted
   - Any deviations from the original plan

4. **Identify open items:**
   - Uncommitted changes and their purpose
   - Failing tests or known issues
   - Tickets still in progress
   - Next steps that should be taken

5. **Note blockers:**
   - Anything that prevented completion
   - Questions that need answers
   - External dependencies waiting on

6. **Format and output:**

```markdown
## Session Handoff — <date>

### Completed
- <what was done>

### Decisions
- <decision and why>

### Open Items
- <what's pending>

### Blockers
- <what's blocked and why>

### Next Steps
1. <recommended next action>
2. <follow-up>

### Files Changed
- <file list>
```

### Notes

This subcommand produces output in the conversation — it does not write to a file or update Jira. Copy the output to wherever makes sense for your workflow (Jira comment, CLAUDE.md memory, etc.).

---

## Subcommand: `discover`

Perform a comprehensive codebase analysis to understand project structure, technology stack, code quality, and identify improvement opportunities.

### Usage

```
/vibey discover
/vibey discover <path>
```

### Steps

#### Step 1: Project Structure

- Identify project type (web app, API, library, CLI, monorepo, etc.)
- Map directory structure and key entry points
- Identify build system and package manager
- Count files by type and size

#### Step 2: Technology Stack

- Detect languages and their versions
- Identify frameworks and libraries (from dependency files)
- Note database, caching, and messaging technologies
- Identify CI/CD configuration
- Check for containerization (Docker, etc.)

#### Step 3: Documentation Audit

- Check for README, CONTRIBUTING, CHANGELOG, LICENSE
- Check for API documentation (OpenAPI, etc.)
- Check for architecture decision records (ADRs)
- Assess inline documentation quality (sample files)

#### Step 4: Security Scan

- Search for hardcoded secrets: `grep -rE "(api[_-]key|password|secret|token)=" --include="*.py" --include="*.js" --include="*.ts"`
- Check for `.env` files committed to git
- Check `.gitignore` for sensitive patterns
- Review dependency files for known vulnerable packages
- Check for SSL verification disabled

#### Step 5: Test Coverage

- Identify test framework and configuration
- Count test files vs source files
- Run tests if possible and report results
- Identify untested areas

#### Step 6: Code Quality

- Check for linter / formatter configuration
- Check for type checking configuration
- Identify code patterns (consistent naming, error handling)
- Note any anti-patterns (god classes, circular imports, etc.)

#### Step 7: Git History Analysis (optional)

- Recent activity: `git log --oneline -20`
- Contributors: `git shortlog -sn --no-merges`
- Hot files: most frequently changed files
- Velocity: commits per week over last month

#### Step 8: Generate Report

Output a structured analysis:

```markdown
## Codebase Discovery Report

### Project Overview
- **Type:** <project type>
- **Languages:** <languages with percentages>
- **Framework:** <primary framework>
- **Size:** <file count, LOC estimate>

### Tech Stack
| Component | Technology | Version |
|-----------|-----------|---------|
| Language  | ...       | ...     |
| Framework | ...       | ...     |
| Database  | ...       | ...     |
| CI/CD     | ...       | ...     |

### Quality Assessment
| Area | Score | Notes |
|------|-------|-------|
| Documentation | X/5 | ... |
| Test Coverage | X/5 | ... |
| Security | X/5 | ... |
| Code Quality | X/5 | ... |

### Key Findings
1. <finding>
2. <finding>

### Improvement Roadmap
1. **Quick wins** (< 1 day): ...
2. **Short-term** (1-5 days): ...
3. **Long-term** (1+ weeks): ...
```
