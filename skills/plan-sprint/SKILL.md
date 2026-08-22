---
name: plan-sprint
description: Planning-cycle workflow — analyze board state, prioritize work, create actionable plan with dependencies
user_invocable: true
---

# /plan-sprint

**Before any GitHub issue operations**, set the skill execution context marker:
Run: `bash "${CLAUDE_PROJECT_DIR:-.}/.claude/hooks/lib/skill-marker.sh" set plan-sprint`

Run a structured planning process that analyzes current project state, gathers requirements, and produces an actionable plan for the next work cycle.

> **Note:** GitHub Issues has no sprint construct. Planning is done against the "Homelab Work" Projects v2 board (all open issues, both repos) + labels + dependencies. The plan artifact is posted as a comment on the relevant epic issue (or a dedicated planning epic).

## Usage

```
/plan-sprint
/plan-sprint <repo>          # homelab | dirtydata (default: both)
```

## Steps

### Step 1: Analyze Current State

- Review CLAUDE.md for project context and conventions
- Check `git log --oneline -20` for recent development activity
- Query the mirror for the current board snapshot (read-only analytical queries):
  ```bash
  docker exec postgres-memory psql -U postgres -d agent_memory -c \
    "SELECT gh_repo, status, count(*) FROM jira.issues
     WHERE status_category <> 'Done' GROUP BY 1, 2 ORDER BY 1, 2;"
  ```
- Recent completions (last 14 days):
  ```bash
  docker exec postgres-memory psql -U postgres -d agent_memory -c \
    "SELECT issue_key, summary, resolved_at::date FROM jira.issues
     WHERE status_category = 'Done' AND resolved_at > now() - interval '14 days'
     ORDER BY resolved_at DESC;"
  ```
- Identify what's done, what's in progress, what's blocked

### Step 2: Gather Requirements

- Query the backlog (mirror, or `mcp__github__list_issues` with `state: open`):
  ```bash
  docker exec postgres-memory psql -U postgres -d agent_memory -c \
    "SELECT issue_key, summary, priority, labels FROM jira.issues
     WHERE status = 'Backlog' AND gh_repo = '<repo>'
     ORDER BY priority NULLS LAST, created_at;"
  ```
- Identify epics with remaining work (epic-ness is derived — an issue with sub-issues):
  ```bash
  docker exec postgres-memory psql -U postgres -d agent_memory -c \
    "SELECT e.issue_key, e.summary, count(*) FILTER (WHERE c.status_category <> 'Done') AS open_children
     FROM jira.issues e JOIN jira.issues c ON c.epic_key = e.issue_key OR c.parent_key = e.issue_key
     WHERE e.status_category <> 'Done' GROUP BY 1, 2 HAVING count(*) FILTER (WHERE c.status_category <> 'Done') > 0
     ORDER BY open_children DESC;"
  ```
- Ask the user about priorities, deadlines, or new requirements

### Step 3: Assess Technical Feasibility

- For each candidate item, consider:
  - Is the approach clear or does it need research?
  - Are there dependencies on other issues?
  - Are there infrastructure or access requirements?
- Flag high-risk items that need spikes or prototypes

### Step 4: Map Dependencies

#### 4a: Audit existing links
Read existing Blocks links from the mirror (`source_key` = blocker, `target_key` = blocked):
```bash
docker exec postgres-memory psql -U postgres -d agent_memory -c \
  "SELECT l.source_key AS blocker, s.status AS blocker_status, l.target_key AS blocked
   FROM jira.issue_links l JOIN jira.issues s ON s.issue_key = l.source_key
   JOIN jira.issues b ON b.issue_key = l.target_key
   WHERE l.link_type = 'Blocks' AND b.status_category <> 'Done';"
```
For authoritative per-issue readback: `gh api repos/fredabood/<repo>/issues/<n>/dependencies/blocked_by`. Flag circular dependencies as errors.

#### 4b: Identify missing dependencies
Based on the feasibility assessment in Step 3, identify issues that should have dependency links but don't. Create each (blocked issue declares its blocker; `issue_id` is the blocker's **database id**, not its number):
```bash
BLOCKER_ID=$(gh api repos/fredabood/<repo>/issues/<BLOCKER#> --jq .id)
gh api -X POST repos/fredabood/<repo>/issues/<BLOCKED#>/dependencies/blocked_by \
  -H "X-GitHub-Api-Version: 2026-03-10" -F issue_id=$BLOCKER_ID
```
Cross-repo dependencies work. Validate direction: cross-layer links flow L1 → L4 (never upward).

#### 4c: Build dependency graph
Document the full graph:
```
LAB-1 blocks LAB-2 — <reason>
LAB-3 (no dependencies)
```

#### 4d: Critical path
Identify the longest sequential chain. This determines minimum elapsed time.
```
Critical path: LAB-1 → LAB-2 → LAB-5 (3 issues)
Parallelizable: LAB-3, LAB-4 (can start immediately)
```

#### 4e: Next-eligible issues
Identify Backlog issues where all blockers are closed (or no blockers). These can start immediately:
```bash
docker exec postgres-memory psql -U postgres -d agent_memory -c \
  "SELECT i.issue_key, i.summary, i.priority FROM jira.issues i
   WHERE i.status = 'Backlog' AND NOT EXISTS (
     SELECT 1 FROM jira.issue_links l JOIN jira.issues s ON s.issue_key = l.source_key
     WHERE l.link_type = 'Blocks' AND l.target_key = i.issue_key AND s.status_category <> 'Done')
   ORDER BY i.priority NULLS LAST, i.created_at;"
```

### Step 5: Prioritize

Score each item using Value / Effort / Risk:

- **Value (1-5):** Business impact, user value
- **Effort (1-5):** Time and complexity
- **Risk (1-5):** Unknowns, technical risk

**Priority = (Value x 2) - (Effort + Risk)**
- High priority: score >= 5
- Medium priority: score 2-4
- Low priority: score <= 1

### Step 6: Create Plan

Produce a structured plan:

```markdown
## Plan: <Cycle Name>
**Duration:** <X weeks>
**Goal:** <one-line goal>

### Definition of Done
- All acceptance criteria verified with evidence
- Tests pass (unit + integration)
- No security regressions
- Documentation updated where applicable
- Post-mortem posted to issue
- Code reviewed

### Issues (ordered by priority)
| Key | Summary | Priority | Estimate | Dependencies | Criteria Status |
|-----|---------|----------|----------|-------------|-----------------|
| ... | ...     | High     | 2d       | None        | Has criteria / Needs criteria |

### Milestones
- Week 1: <milestone>
- Week 2: <milestone>

### Dependency Graph
LAB-1 blocks LAB-2 — <reason>
...

### Critical Path
LAB-X → LAB-Y → LAB-Z (N sequential issues)

### Next Eligible (ready to start)
| Key | Summary | Priority | Notes |
|-----|---------|----------|-------|
| ... | ...     | High     | No blockers / Just unblocked |

### Risks
- <risk and mitigation>
```

**Post the plan** as a comment on the relevant epic issue using `mcp__github__add_issue_comment` (if the planned work spans multiple epics, post on the dominant epic and cross-reference the others by key). If no epic fits, create a planning epic via `/create-ticket` logic and attach the in-scope issues as sub-issues with `mcp__github__sub_issue_write`.

**Acceptance criteria enforcement:** For any backlog item lacking acceptance criteria, draft them during planning and add them to the issue **body** (`## Acceptance Criteria` task list) using `mcp__github__issue_write`.

### Step 7: Update GitHub

- Create any new issues identified during planning (`/create-ticket` logic — taxonomy labels required: one work pattern + one layer)
- Set board Status for items being pulled into active work via `mcp__github__projects_write` (IDs in `.claude/rules/custom-fields.md`); park de-prioritized items as `Deferred`
- Create blocked-by links for dependent issues (Step 4b command)
- Ensure all planned issues have acceptance criteria in their bodies

### Step 8: Update CLAUDE.md

- Update the project's CLAUDE.md with current cycle focus
- Document any new conventions or decisions

### Step 9: Commit Planning Artifacts

- Commit any documentation changes
- Include the plan/epic reference in the commit message (e.g., `LAB-963: Plan 2026-07 cycle`)

## Required Tools

- `mcp__github__list_issues` / `mcp__github__search_issues`
- `mcp__github__issue_read` (methods `get`, `get_comments`, `get_sub_issues`)
- `mcp__github__issue_write` (create/update — body criteria)
- `mcp__github__add_issue_comment` (plan comment on epic)
- `mcp__github__sub_issue_write` (epic membership)
- `mcp__github__projects_write` (board Status)
- `gh api .../dependencies/blocked_by` (dependency create/read — no MCP tool)
- `docker exec postgres-memory psql ...` — mirror analytics (read-only)

**Cleanup:** Run `bash "${CLAUDE_PROJECT_DIR:-.}/.claude/hooks/lib/skill-marker.sh" clear` to release the skill gate.
