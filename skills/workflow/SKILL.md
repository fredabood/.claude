---
description: Full lifecycle workflow — work tracking, planning, git, implementation, verification, completion, memory, handoff
user_invocable: true
---

# /workflow

**Before any Jira operations**, write the skill execution context marker:
Write `.skill-execution-context.json` with content: `{"skill": "workflow", "started_at": "<current ISO8601 timestamp>", "ticket_key": "<ticket key if known, null otherwise>"}`

End-to-end 12-phase development lifecycle with deterministic gates at every phase.
Phases 1-6: planning + implementation. Phase 7: Implementation Complete (PM fields). Phases 8-9: Doc Review + Review Complete. Phases 10-12: memory persistence, git cleanup, handoff.
Backed by a persistent state machine (postgres + file cache) that enables hook enforcement and cross-session resume.

When active, hooks on Edit/Write/Commit/Transition block out-of-sequence actions. When not active, Claude operates normally.

## Usage

```
/workflow <ISSUE-KEY>
/workflow "<description>"
```

Example: `/workflow LAB-123`
Example: `/workflow "Add user profile page with avatar upload"`

## State Machine

Each phase writes state to **both** postgres (`workflow.runs`) and `.workflow-state.json` (gitignored file cache for fast hook reads).

**State write helper** — run after every phase gate passes:

```bash
# DB write
docker exec postgres-memory psql -U postgres -d agent_memory -c \
  "UPDATE workflow.runs SET phase_<N>_at = NOW() WHERE work_item_key = '<KEY>' AND completed_at IS NULL"

# File write
python3 -c "
import json, os, datetime
f = '.workflow-state.json'
state = json.load(open(f)) if os.path.exists(f) else {}
state['phase_<N>_at'] = datetime.datetime.now().isoformat()
json.dump(state, open(f, 'w'), indent=2)
"
```

Replace `<N>` with the phase number and `<KEY>` with the work item key.

## Initialization

### If input is a key (e.g., LAB-123)

1. Check postgres for an active (incomplete) workflow:
   ```bash
   docker exec postgres-memory psql -U postgres -d agent_memory -t -A -c \
     "SELECT row_to_json(r) FROM workflow.runs r WHERE work_item_key = '<KEY>' AND completed_at IS NULL"
   ```
2. **If a row exists** (cross-session resume):
   - Write the DB state to `.workflow-state.json` (hydrate file cache)
   - Identify the next incomplete phase (first `phase_N_at` that is NULL)
   - Output: `> Resuming workflow <KEY> at Phase N: <name>`
   - Skip to that phase
3. **If no row exists** (fresh start):
   - Insert a new row:
     ```bash
     docker exec postgres-memory psql -U postgres -d agent_memory -c \
       "INSERT INTO workflow.runs (work_item_key) VALUES ('<KEY>')"
     ```
   - Write initial `.workflow-state.json`: `{"work_item_key": "<KEY>"}`
   - Proceed to Phase 1

### If input is a description

1. Search Jira for an existing ticket using `searchJiraIssuesUsingJql`
2. If found: use the existing key, follow the key path above
3. If not found: create a new ticket using `/create-ticket` logic, then follow the key path

## Phases

Execute each phase sequentially. Do not proceed to the next phase until the current gate passes.
Output a status line after each phase: `> Phase N: <name> ✓`

---

### Phase 1: Work Item

1. Fetch the work item with `getJiraIssue`
2. If not already "In Progress", transition using `transitionJiraIssue` (discover ID via `getTransitionsForJiraIssue`)
3. Set agent tracking fields:
   ```
   editJiraIssue(issueIdOrKey, fields={
       "customfield_10188": "<session-identifier>",   // Primary Agent
       "customfield_10189": "<session-identifier>",   // Assigned Agent
       "customfield_10193": 1.0                       // Workflow Phase = 1
   })
   ```
4. Post context comment: `"Starting workflow. Session: <date/time>"`
5. **Write state:** DB + file (`phase_1_at`)

**Gate:** Work item exists, is In Progress, and has Assigned Agent set.

---

### Phase 2: Acceptance Criteria

1. Parse the work item description for an `Acceptance Criteria` section
2. **If criteria exist:** Confirm they are measurable and deterministic. Display them.
3. **If criteria are missing:**
   - Draft criteria following the standard format (minimum: 1 functional + 1 test-based + 1 security)
   - Post drafted criteria to the work item as a comment using `addCommentToJiraIssue`
   - Confirm with the user before proceeding
4. **Write state:** DB + file (`phase_2_at`)

**Gate:** Acceptance criteria exist on the work item (in description or comment).

---

### Phase 3: Implementation Plan

1. Draft an implementation plan including:
   - **Approach:** files to modify, components affected, rationale
   - **Testing strategy:** types of tests, specific scenarios, verification commands
   - **Documentation plan:** what docs/memory/vault to update
   - **Risk assessment:** what could go wrong, mitigations, fallback approaches
2. Post the plan to the work item as a comment using `addCommentToJiraIssue`
3. Write plan sections to custom fields:
   ```
   editJiraIssue(issueIdOrKey, fields={
       "customfield_10173": "<Jira tracking plan>",
       "customfield_10174": "<Testing strategy>",
       "customfield_10175": "<Documentation plan>",
       "customfield_10176": "<Success criteria>",
       "customfield_10177": "<Risk assessment>",
       "customfield_10190": [{"id":"10130"},{"id":"10131"},{"id":"10132"},{"id":"10133"},{"id":"10134"}],
       "customfield_10193": 3.0   // Workflow Phase = 3
   })
   ```
4. **Ask the user to confirm the plan before proceeding.** Do not continue until confirmed.
5. **Write state:** DB + file (`phase_3_at`)

**Gate:** Plan posted to work item AND user has confirmed.

> After this phase completes, the Edit/Write hook gate opens — code edits are now allowed.

---

### Phase 4: Git Setup

1. Check `git status` for uncommitted changes
   - If uncommitted changes exist: stash them (`git stash push -m "workflow: stashing for <KEY>"`) or commit with context
2. Create a feature branch: `git checkout -b <KEY>-<kebab-description>`
   - Example: `LAB-123-add-user-profile`
3. **Write state:** DB + file (`phase_4_at`, `branch_name`)
   - Also update DB: `UPDATE workflow.runs SET branch_name = '<branch>' WHERE ...`
   - Also update file: add `"branch_name": "<branch>"` to `.workflow-state.json`

**Gate:** Currently on a feature branch named after the work item.

---

### Phase 5: Implementation

1. Write code following project conventions
2. Write tests:
   - Unit tests for business logic (target 90%+ coverage on new code)
   - Integration tests for external service interactions
   - Cover happy path, edge cases, and error paths
   - For bug fixes: write a failing test that reproduces the bug first
3. Security review (9-point checklist):
   - Hardcoded secrets, environment variables, input sanitization, logging, rate limiting, TLS/HTTPS, error messages, dependencies (CVEs), test security
4. Update `docs/` if operational behavior changed
5. Commit with ticket reference: `<KEY>: <description>`
6. Post milestone comment(s) to the work item at significant checkpoints (tests passing, integration working, docs updated)
7. **Write state:** DB + file (`phase_5_at`)

**Gate:** Code compiles/lints, tests written, security review clean, changes committed.

---

### Phase 6: Verification

1. Run the full test suite — all tests must pass
2. For each acceptance criterion:
   - Run the specified verification (test command, file check, behavior walkthrough)
   - Record pass/fail with evidence
3. Post a verification report to the work item using `addCommentToJiraIssue`:

```markdown
## Verification Report: <KEY>

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | <criterion text> | PASS/FAIL | <how verified> |
| 2 | ... | ... | ... |

**Result:** ALL PASS / <N> FAILURES
```

4. Write verification results to custom fields:
   ```
   editJiraIssue(issueIdOrKey, fields={
       "customfield_10178": "<all criteria tested list>",
       "customfield_10179": "<results summary — X/Y pass>",
       "customfield_10191": [{"id":"10135"},{"id":"10136"}],  // + {"id":"10137"} if ALL pass
       "customfield_10193": 6.0   // Workflow Phase = 6
   })
   ```
5. **Write state:** DB + file (`phase_6_at`)

**Hard gate:** ALL criteria must pass. If any fail, stop and fix before retrying Phase 6. Do not proceed with failures.

---

### Phase 7: Completion (Implementation Complete)

1. Generate a structured post-mortem (same format as before)
2. Post the post-mortem to the work item using `addCommentToJiraIssue`
3. Write post-mortem sections to custom fields:
   ```
   editJiraIssue(issueIdOrKey, fields={
       "customfield_10180": "<What Went Well>",
       "customfield_10181": "<What Didn't Go Well>",
       "customfield_10182": "<Lessons Learned>",
       "customfield_10183": "<Metrics>",
       "customfield_10184": "<Follow-Up Items>",
       "customfield_10192": [{"id":"10138"},{"id":"10139"},{"id":"10140"},{"id":"10141"},{"id":"10142"}],
       "customfield_10193": 7.0   // Workflow Phase = 7
   })
   ```
4. Transition to **Implementation Complete** using `getTransitionsForJiraIssue` to discover the transition ID (look for `to.name == "Implementation Complete"`)
5. Check if the work item has a parent epic — if all sibling items are Done/Implementation Complete, note it
6. **Write state:** DB + file (`phase_7_at`)

**Gate:** Post-mortem posted, PM fields populated, work item in Implementation Complete.

---

### Phase 8: Doc Review

1. Review all documentation changes from the session:
   - What docs in `docs/` were created or updated?
   - What memory files were written or updated?
   - What vault notes were created?
   - What Jira comments were posted?
2. Generate a documentation summary and a memory update summary
3. Write to custom fields:
   ```
   editJiraIssue(issueIdOrKey, fields={
       "customfield_10185": "<Documentation summary — what was updated and why>",
       "customfield_10186": "<Memory updates — what was persisted and where>",
       "customfield_10193": 8.0   // Workflow Phase = 8
   })
   ```
4. Post a doc review comment to the work item
5. **Write state:** DB + file (`phase_8_at`)

**Gate:** Doc Review fields populated.

---

### Phase 9: Review Complete

1. Transition to **Review Complete** using `getTransitionsForJiraIssue` (look for `to.name == "Review Complete"`)
2. **Write state:** DB + file (`phase_9_at`)

**Gate:** Work item in Review Complete status.

---

### Phase 10: Memory & Knowledge Persistence

1. Review all decisions made during the session
2. For each decision or lesson learned, route to the correct store:

| Scope | Store | Method |
|-------|-------|--------|
| Ticket-specific (approach, trade-off) | Already posted as work item comment | Done in earlier phases |
| Claude behavioral (user correction, preference) | Auto-memory (`~/.claude/projects/.../memory/`) | Write memory file + update MEMORY.md |
| Architectural (chose X over Y because Z) | Vault → `submodules/memory/homelab/decisions/` | Use `/vault-add` logic |
| Operational knowledge (how to run, deploy, configure) | Vault → `submodules/memory/homelab/knowledge/` | Use `/vault-add` logic |
| Research findings (evaluation, comparison, analysis) | Vault → `submodules/memory/homelab/research/` | Use `/vault-add` logic |

3. If follow-up items were identified in the post-mortem, present them to the user and offer to create new work items
4. **Write state:** DB + file (`phase_10_at`)

**Gate:** At least one persistence action taken, or explicitly noted "nothing to persist" with justification.

---

### Phase 11: Git Cleanup

1. Switch to main: `git checkout main`
2. Merge the feature branch: `git merge <branch>`
3. Delete the feature branch: `git branch -d <branch>`
4. **Write state:** DB + file (`phase_11_at`)

**Gate:** On main branch, feature branch deleted.

---

### Phase 12: Handoff

1. Transition to **Done** using `getTransitionsForJiraIssue` (look for `to.name == "Done"`)
2. Mark the workflow as complete:
   ```bash
   docker exec postgres-memory psql -U postgres -d agent_memory -c \
     "UPDATE workflow.runs SET phase_12_at = NOW(), completed_at = NOW() WHERE work_item_key = '<KEY>' AND completed_at IS NULL"
   ```
2. Delete `.workflow-state.json` (deactivates hook enforcement)
3. Output final summary:

```markdown
## Workflow Complete: <KEY>

- **Work item:** <KEY> — <summary> → Done
- **Branch:** <branch> → merged to main
- **Commits:** <count>
- **Verification:** <X/Y> criteria passed
- **Post-mortem:** posted
- **Memory:** <what was persisted>
- **Follow-ups:** <created / none>
```

---

## Aborting a Workflow

If the user needs to abort an active workflow:

1. Delete `.workflow-state.json` (deactivates hooks immediately)
2. Update the DB row: `UPDATE workflow.runs SET completed_at = NOW(), metadata = metadata || '{"aborted": true}' WHERE work_item_key = '<KEY>' AND completed_at IS NULL`
3. The work item remains in its current Jira state — no automatic transition

## Required MCP Tools

- `getJiraIssue` (cloudId, issueIdOrKey)
- `transitionJiraIssue` (cloudId, issueIdOrKey, transition: { id })
- `addCommentToJiraIssue` (cloudId, issueIdOrKey, body)
- `searchJiraIssuesUsingJql` (cloudId, jql)
- `createJiraIssue` (cloudId, fields) — for follow-ups
- `createIssueLink` (cloudId, linkType, inwardIssue, outwardIssue) — for follow-ups

## CloudId

Use the project's configured Jira CloudId from CLAUDE.md.

**Cleanup:** Delete `.skill-execution-context.json` to release the skill gate.
