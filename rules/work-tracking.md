---
description: GitHub-Issues-first work tracking — automatically search for and create issues, post updates, include identifiers in commits
globs:
  - "**/*"
---

# Work Tracking — GitHub-Issues-First Behavior

> Invoke `/workflow` for full gated lifecycle with deterministic enforcement. This rule covers issue search/create mechanics and is active in all sessions.

All implementation work is tracked in GitHub Issues by default. Follow these behaviors automatically without waiting for the user to invoke a skill.

**Repo routing:** Infer the target repo from the work context:
- Working in the homelab repo root or `stacks/`, `internal/`, `.claude/` → **`fredabood/homelab`** (keys `LAB-<n>`; `HL-*` prefix deprecated 2026-07-12, LAB-963)
- Working in `submodules/dirtydata/` or on DRTY-prefixed issues → **`fredabood/dirtydata`** (keys `DRTY-<n>`; `DD-*` deprecated)
- Working in `submodules/9215resort/` or on RESORT-prefixed issues → **`fredabood/9215resort`** (keys `RESORT-<n>`; the LAB-221 + LAB-228 trees transferred here 2026-07-12 — old↔new map in `public.resort_transfer_key_map`, LAB-962)

All open issues from all three repos live on the Projects v2 board **"Homelab Work"** (user `fredabood`, project number 1). Board Status values: `Backlog`, `In Progress`, `Implementation Complete`, `Review Complete`, `Deferred`. See `.claude/rules/custom-fields.md` for stable board/field IDs.

## On any implementation request

Before writing code:

1. **Search GitHub Issues** for a matching issue using `mcp__github__search_issues` (or `mcp__github__list_issues`). Search by keywords from the request; scope to the target repo. The postgres mirror (`jira.*`) can also be queried read-only for richer SQL search.
2. **If found:** Set it as the active issue for the session. Move its board Status to "In Progress" using `mcp__github__projects_write` if not already.
3. **If not found:** Prompt the user: "No GitHub issue found for this work. Should I create one?" If yes, follow the `/create-ticket` workflow to create a structured issue with acceptance criteria (task list in the body).
4. **Evaluate decomposition:** Before beginning work, assess whether it should be multiple issues:
   - Multiple independent codebase areas?
   - Independently verifiable acceptance criteria?
   - More than one session of effort?
   - Mix of setup/infrastructure and feature work?

   If decomposition is warranted, present the proposed breakdown to the user. Use `/create-ticket` for each piece, then create blocked-by dependency links between them:
   ```bash
   gh api -X POST repos/fredabood/<repo>/issues/<BLOCKED#>/dependencies/blocked_by \
     -H "X-GitHub-Api-Version: 2026-03-10" -F issue_id=<BLOCKER-database-id>
   ```
   (Get the blocker's database id with `gh api repos/fredabood/<repo>/issues/<BLOCKER#> --jq .id`.)

## Taxonomy label requirement

When creating or updating issues, apply taxonomy labels per `.claude/rules/label-taxonomy.md`:

- **Work pattern:** exactly one of `scraper`, `agent`, `workflow`, `deployment`, `pipeline`, `migration`, `platform`
- **Infrastructure layer:** exactly one of `L1-platform`, `L2-services`, `L3-framework`, `L4-domain`
- If work matches a known pattern, offer the standard decomposition template from the label-taxonomy rule
- Cross-repo blocked-by links must flow downward: L1 → L2 → L3 → L4

## Stale in-progress issues

At session start, if an issue is already at board Status "In Progress":

1. Check `git log --oneline -20` for recent commits referencing the issue identifier (`HL-<n>`/`DD-<n>`, historical `LAB-*`/`DRTY-*`, or `#<n>`)
2. **If commits exist within ~24h:** Treat it as actively in progress — resume normally
3. **If the last relevant commit is older than 24h:** Note the gap to the user and ask whether to resume or restart
4. **If no commits reference the identifier at all:** Flag it as potentially stale — ask the user to confirm intent before proceeding
5. **If an `Assigned Agent:` comment exists** and differs from the current session: another agent started but did not finish — warn the user and ask whether to take over or leave it

Do not silently assume a stale In Progress issue is active work.

## Exceptions

- **Trivial changes** (typo fixes, single-line formatting, comment updates) skip tracking
- The user can say **"skip tracking"** to bypass for any change
- If the user explicitly says they don't want an issue, respect that and don't ask again in the session

## Agent assignment protocol

Before moving an issue to "In Progress":

1. Post an assignment comment via `mcp__github__add_issue_comment` (there are no custom fields on GitHub Issues):
   ```
   Assigned Agent: <session-id>
   Session: <ISO timestamp>
   ```
2. Set board Status to "In Progress" using `mcp__github__projects_write`
3. Post context comment: "Starting work. Assigned Agent: `<session-id>`. Session: `<timestamp>`" (may be combined with step 1)

If the issue already has an `Assigned Agent:` comment (most recent wins):
- **Same agent:** Resume normally
- **Different agent:** Warn the user that another agent claimed this issue — ask whether to override or pick a different issue

## Suggesting next work (Planned+Unblocked agent queue)

When an issue is completed or the user asks what to work on next, use the agent work queue
defined in `.claude/rules/label-taxonomy.md`:

1. **Query base candidates:** open issues with acceptance criteria at board Status "Backlog":
   - `mcp__github__search_issues` with `repo:fredabood/homelab is:open "Acceptance Criteria" in:body` (repeat for `fredabood/dirtydata`), or `mcp__github__list_issues` filtered by state/labels
   - Cross-check board Status = `Backlog` via `mcp__github__projects_get` (or read the mirror: `jira.issues WHERE status = 'Backlog'`)
2. For each candidate, use `mcp__github__issue_read` (methods `get`, `get_comments`) and apply three filters:
   - **Planned check:** Body has an `## Acceptance Criteria` task list AND a comment contains `## Implementation Plan`
   - **Blocker check:** No open blockers — `gh api repos/fredabood/<repo>/issues/<n>/dependencies/blocked_by` returns only closed issues (or mirror `jira.issue_links` shows no open blockers)
   - **Assignment check:** If the latest `Assigned Agent:` comment names another agent, skip
3. An issue is **eligible** only if: Planned = true AND Blocked = false AND (unassigned or assigned to current agent)
4. Present results in three tiers:
   - **Ready for pickup:** Eligible items, ordered by priority
   - **Blocked:** Planned but waiting on dependencies — show which blockers are closest to completion
   - **Needs planning:** Missing acceptance criteria or plan comment — note what's missing
5. For blocked candidates, identify which blockers are closest to completion

If no eligible items exist, report: (a) unplanned issues that need criteria/plans, (b) which blockers need resolving to unlock the next tier.
