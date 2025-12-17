# CLI/MCP Coverage Audit

> Audit of CLI command and MCP tool coverage in user journeys and walkthroughs

**Date:** 2024-12-16
**Task:** Sprint 3 Task 3 (01KCMKPY8CVHTZ1SCNQG38YN7T)

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **CLI Commands Total** | 199 |
| **CLI Commands Covered** | 65 (32.6%) |
| **CLI Commands Missing** | 134 (67.4%) |
| **MCP Tools Total** | 84 |
| **MCP Tools Covered** | 19 (22.6%) |
| **MCP Tools Missing** | 65 (77.4%) |

**Overall Finding:** Approximately 2/3 of CLI commands and 3/4 of MCP tools have no examples in user-facing walkthroughs or journeys.

---

## CLI Command Coverage by Group

### Fully Missing Groups (0% coverage in walkthroughs)

These command groups have NO mentions in journeys/walkthroughs:

| Group | Commands | Priority | Recommended Walkthrough |
|-------|----------|----------|------------------------|
| `artifact` | 9 | Medium | EXTENDING_VIBEY.md |
| `audit` | 2 | Medium | ROADMAP_MANAGEMENT.md |
| `auth` | 7 | High | GETTING_STARTED.md |
| `config platform` | 6 | Medium | DEPLOYMENT.md |
| `content` | 7 | Low | EXTENDING_VIBEY.md |
| `export` | 4 | Medium | REPORTING_AND_STATUS.md |
| `git` (most) | 25 | Medium | DAILY_WORKFLOW.md |
| `validate` | 2 | Low | TROUBLESHOOTING.md |

### Partially Covered Groups

| Group | Covered | Missing | Coverage |
|-------|---------|---------|----------|
| `roadmap` | ~20 | 26 | ~43% |
| `deploy` | 0 | 2 | 0% |
| `session` | ~5 | 6 | ~45% |
| `discover` | ~3 | 3 | ~50% |
| `context` | ~3 | 4 | ~43% |
| `docs` | ~2 | 5 | ~29% |

---

## Missing CLI Commands by Category

### artifact (9 commands) → EXTENDING_VIBEY.md

```
vibey artifact
vibey artifact adopt
vibey artifact delete
vibey artifact impact
vibey artifact list
vibey artifact orphans
vibey artifact refresh
vibey artifact show
vibey artifact stale
```

### audit (2 commands) → ROADMAP_MANAGEMENT.md

```
vibey audit classify
vibey audit inventory
```

### auth (7 commands) → GETTING_STARTED.md

```
vibey auth add-signer
vibey auth export
vibey auth init-project
vibey auth list
vibey auth revoke
vibey auth setup
vibey auth status
```

### config (7 commands) → DEPLOYMENT.md

```
vibey config platform
vibey config platform clear
vibey config platform detect
vibey config platform list
vibey config platform set
vibey config platform show
vibey config rollback
```

### content (7 commands) → EXTENDING_VIBEY.md

```
vibey content create
vibey content delete
vibey content edit
vibey content list
vibey content search
vibey content show
vibey content validate
```

### deploy (2 commands) → DEPLOYMENT.md

```
vibey deploy
vibey deploy list
vibey deploy run
```

### export (4 commands) → REPORTING_AND_STATUS.md

```
vibey export gemini
vibey export list
vibey export run
vibey export stats
```

### git (25 commands) → DAILY_WORKFLOW.md / DATABASE_OPERATIONS.md

```
vibey git analyze
vibey git branch create/link/list/status/unlink
vibey git check-merge
vibey git contributors
vibey git history
vibey git hooks uninstall/update
vibey git link-commit
vibey git mode
vibey git pr-description
vibey git progress
vibey git repair/repair-tags
vibey git rollback
vibey git sprint delete/end/list/range/start
vibey git state-at
vibey git sync
vibey git tag-move/tag-range/tags
vibey git tasks
vibey git update-status
vibey git validate/validate-roadmap/validate-tags
vibey git velocity
```

### roadmap (26 commands) → Various

**→ ROADMAP_MANAGEMENT.md:**
```
vibey roadmap add-standard
vibey roadmap bulk / bulk complete-sprint
vibey roadmap check-compatibility
vibey roadmap check-hooks
vibey roadmap check-standards
vibey roadmap checkpoint
vibey roadmap create activity
vibey roadmap dependency add/list/remove
vibey roadmap export
vibey roadmap restore
```

**→ DATABASE_OPERATIONS.md:**
```
vibey roadmap db migrate
vibey roadmap db stats
vibey roadmap db vacuum
```

**→ REPORTING_AND_STATUS.md:**
```
vibey roadmap history
vibey roadmap get-field
vibey roadmap summarize
```

---

## Missing MCP Tools by Category

### Task Tools (0 missing - good coverage!)
All 3 task tools are covered.

### Sprint Tools (1 missing)
```
vibey_refresh_progress → DAILY_WORKFLOW.md
```

### Query Tools (3 missing)
```
vibey_list_blockers → DAILY_WORKFLOW.md
vibey_query_standards → ROADMAP_MANAGEMENT.md
vibey_query_track → ROADMAP_MANAGEMENT.md
```

### Content Tools (6 missing)
```
vibey_content_create → EXTENDING_VIBEY.md
vibey_content_delete → EXTENDING_VIBEY.md
vibey_content_list → EXTENDING_VIBEY.md
vibey_content_search → EXTENDING_VIBEY.md
vibey_content_show → EXTENDING_VIBEY.md
vibey_content_update → EXTENDING_VIBEY.md
vibey_content_validate → EXTENDING_VIBEY.md
```

### Agent Tools (19 missing)
All 19 agent invocation tools are missing from walkthroughs:
```
vibey_architecture_agent
vibey_backend_engineer
vibey_coordinator
vibey_database_specialist
vibey_diagram_engineer
vibey_documentation_engineer
vibey_documentation_maintenance_engineer
vibey_frontend_engineer
vibey_git_committer
vibey_infrastructure_engineer
vibey_ml_engineer
vibey_platform_engineer
vibey_product_manager
vibey_qa_engineer
vibey_roadmap_manager
vibey_security_engineer
vibey_standards_agent
vibey_swarm_coordinator
vibey_technical_writer
```
**Recommendation:** Add to EXTENDING_VIBEY.md as "AI Agent Tools"

### Workflow Tools (16 missing)
All 16 workflow tools are missing:
```
vibey_workflow_execute
vibey_handoff_ai_to_human
vibey_handoff_architecture_design
vibey_handoff_code_review
vibey_handoff_implementation_complete
vibey_handoff_initial_analysis
vibey_handoff_planning_complete
vibey_handoff_qa_to_development
vibey_handoff_research_complete
vibey_handoff_sprint_completion
vibey_handoff_task_delegation
vibey_handoff_testing_complete
... etc
```
**Recommendation:** Add "Workflow Handoffs" section to DAILY_WORKFLOW.md

---

## Recommended Walkthrough Assignments

Based on command purpose, assign missing commands to new action-oriented walkthroughs:

| Walkthrough | Commands to Add | MCP Tools to Add |
|-------------|-----------------|------------------|
| **GETTING_STARTED.md** | auth (7) | - |
| **DAILY_WORKFLOW.md** | git (25), roadmap activity | workflow/handoff (16), refresh_progress |
| **ROADMAP_MANAGEMENT.md** | audit (2), roadmap bulk/export/checkpoint (15) | query_standards, query_track |
| **DEPLOYMENT.md** | deploy (2), config platform (6) | - |
| **DATABASE_OPERATIONS.md** | roadmap db (3) | - |
| **REPORTING_AND_STATUS.md** | export (4), roadmap summarize/history | - |
| **EXTENDING_VIBEY.md** | artifact (9), content (7), validate (2) | content tools (7), agent tools (19) |
| **TROUBLESHOOTING.md** | git repair, git validate | - |

---

## Priority Matrix

### High Priority (Core user workflows)
- [ ] `vibey roadmap` commands in DAILY_WORKFLOW
- [ ] `vibey deploy` commands in DEPLOYMENT
- [ ] `vibey auth` commands in GETTING_STARTED
- [ ] Task/Sprint MCP tools

### Medium Priority (Power user features)
- [ ] `vibey git` commands
- [ ] `vibey export` commands
- [ ] Agent MCP tools

### Low Priority (Specialized features)
- [ ] `vibey artifact` commands
- [ ] `vibey content` commands
- [ ] `vibey validate` commands

---

## Implementation Notes

### Task 6 Dependencies
This audit feeds directly into **Task 6: Ensure 100% Command Coverage in Action Walkthroughs**.

Task 6 should:
1. Use this command/tool list as the checklist
2. Add contextual examples for each command in the assigned walkthrough
3. Create a coverage matrix showing command → walkthrough mapping
4. Verify all 199 CLI commands and 84 MCP tools have at least one example

### Example Format for New Coverage

```markdown
## Managing Dependencies

Check blocked tasks:

**CLI:**
```bash
vibey roadmap list-blockers
```

**MCP Tool:**
```json
{
  "tool": "vibey_list_blockers",
  "arguments": {}
}
```

This shows all tasks that are blocked by unfinished dependencies.
```

---

## Audit Methodology

- Extracted 199 commands from CLI_REFERENCE.md command index
- Extracted 84 tools from MCP_REFERENCE.md tool sections
- Searched docs/journeys/ and docs/walkthroughs/ for each command/tool
- Excluded STRUCTURE.md (meta document)
- Counted occurrences to determine coverage
