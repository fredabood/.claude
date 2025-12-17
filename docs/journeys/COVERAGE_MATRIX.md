# Journey-to-Feature Coverage Matrix

**Version:** 1.1
**Last Updated:** 2025-12-15

This document maps Vibey features to user personas and their journeys, identifying which features serve which users and highlighting documentation coverage gaps.

---

## Legend

| Symbol | Meaning |
|--------|---------|
| **M** | Must Have - Critical for this persona |
| **S** | Should Have - Important but not blocking |
| **N** | Nice to Have - Useful but optional |
| **-** | Not applicable to this persona |

---

## CLI Command Coverage

### Roadmap Commands

| Command | Nina | Alex | Pat | Chris | Sam | Documented |
|---------|:----:|:----:|:---:|:-----:|:---:|:----------:|
| `roadmap status` | M | M | M | S | - | Yes |
| `roadmap show` | M | M | M | S | - | Yes |
| `roadmap start` | S | M | - | - | - | Yes |
| `roadmap complete` | S | M | - | - | - | Yes |
| `roadmap create-track` | S | - | M | - | - | Yes |
| `roadmap create-sprint` | S | - | M | - | - | Yes |
| `roadmap create-task` | S | - | M | - | - | Yes |
| `roadmap update` | - | S | M | - | - | Yes |
| `roadmap context` | - | M | S | - | - | Yes |
| `roadmap add-context` | - | M | S | - | - | Yes |
| `roadmap activity` | - | M | M | - | - | Yes |
| `roadmap checkpoint` | - | S | M | - | - | Yes |
| `roadmap summarize` | - | N | M | - | - | Yes |
| `roadmap db query blocked` | - | M | M | - | - | Yes |
| `roadmap list-dependencies` | - | S | M | - | - | Yes |
| `roadmap validate` | - | - | S | M | - | Yes |
| `roadmap repair` | - | - | S | S | - | Yes |
| `roadmap export` | - | - | M | - | S | Yes |
| `roadmap auto-progress` | - | S | S | - | - | Yes |
| `roadmap db sync` | - | - | S | S | - | Yes |
| `roadmap db rebuild` | - | - | S | S | - | Yes |

### Audit Trail Commands (Phase 3)

| Command | Nina | Alex | Pat | Chris | Sam | Documented |
|---------|:----:|:----:|:---:|:-----:|:---:|:----------:|
| `roadmap audit log` | - | M | M | S | - | Yes |
| `roadmap audit show` | - | M | M | S | - | Yes |
| `roadmap audit suspicious` | - | S | M | - | - | Yes |
| `roadmap audit report` | - | N | M | - | - | Yes |

### Init & Config Commands

| Command | Nina | Alex | Pat | Chris | Sam | Documented |
|---------|:----:|:----:|:---:|:-----:|:---:|:----------:|
| `init` | M | - | - | - | - | Yes |
| `config show` | S | - | S | S | - | Yes |
| `config validate` | - | - | S | M | - | Yes |
| `config migrate` | - | - | S | S | - | Yes |

### Git Commands

| Command | Nina | Alex | Pat | Chris | Sam | Documented |
|---------|:----:|:----:|:---:|:-----:|:---:|:----------:|
| `git hooks install` | - | S | - | M | - | Yes |
| `git hooks status` | - | S | - | M | - | Yes |

### Docs Commands

| Command | Nina | Alex | Pat | Chris | Sam | Documented |
|---------|:----:|:----:|:---:|:-----:|:---:|:----------:|
| `docs generate` | - | - | - | S | - | Yes |
| `docs generate-cli` | - | - | - | M | - | Yes |
| `docs generate-mcp` | - | - | - | M | M | Yes |
| `docs check-drift` | - | - | - | M | - | Yes |
| `docs check-mcp-drift` | - | - | - | M | M | Yes |
| `docs introspect` | - | - | - | S | S | Yes |
| `docs introspect-mcp` | - | - | - | S | M | Yes |

---

## MCP Tool Coverage

### Task Tools

| Tool | Nina | Alex | Pat | Chris | Sam | Documented |
|------|:----:|:----:|:---:|:-----:|:---:|:----------:|
| `vibey_start_task` | - | - | - | - | M | Yes |
| `vibey_complete_task` | - | - | - | - | M | Yes |
| `vibey_query_task` | - | - | - | - | M | Yes |

### Sprint Tools

| Tool | Nina | Alex | Pat | Chris | Sam | Documented |
|------|:----:|:----:|:---:|:-----:|:---:|:----------:|
| `vibey_start_sprint` | - | - | - | - | M | Yes |
| `vibey_complete_sprint` | - | - | - | - | M | Yes |
| `vibey_refresh_progress` | - | - | - | - | M | Yes |
| `vibey_query_sprint` | - | - | - | - | M | Yes |

### Query Tools

| Tool | Nina | Alex | Pat | Chris | Sam | Documented |
|------|:----:|:----:|:---:|:-----:|:---:|:----------:|
| `vibey_query_track` | - | - | - | - | M | Yes |
| `vibey_list_blockers` | - | - | - | - | M | Yes |
| `vibey_list_dependencies` | - | - | - | - | S | Yes |
| `vibey_roadmap_status` | - | - | - | - | M | Yes |
| `vibey_query_standards` | - | - | - | - | S | Yes |

### Content Tools

| Tool | Nina | Alex | Pat | Chris | Sam | Documented |
|------|:----:|:----:|:---:|:-----:|:---:|:----------:|
| `vibey_content_list` | - | - | - | - | M | Yes |
| `vibey_content_show` | - | - | - | - | M | Yes |
| `vibey_content_search` | - | - | - | - | S | Yes |
| `vibey_content_create` | - | - | - | - | S | Yes |
| `vibey_content_update` | - | - | - | - | S | Yes |
| `vibey_content_delete` | - | - | - | - | N | Yes |
| `vibey_content_validate` | - | - | - | - | S | Yes |

---

## Resource Coverage (MCP)

| Resource Template | Nina | Alex | Pat | Chris | Sam | Documented |
|-------------------|:----:|:----:|:---:|:-----:|:---:|:----------:|
| `vibey://workflows/{id}` | - | - | - | - | M | Yes |
| `vibey://workflows/{id}/steps` | - | - | - | - | S | Yes |
| `vibey://workflows/{id}/metadata` | - | - | - | - | S | Yes |
| `vibey://workflows/{id}/quality-gates` | - | - | - | - | S | Yes |
| `vibey://handoffs/{id}` | - | - | - | - | M | Yes |
| `vibey://handoffs/{id}/variables` | - | - | - | - | S | Yes |
| `vibey://handoffs/{id}/metadata` | - | - | - | - | S | Yes |
| `vibey://handoffs/{id}/rendered` | - | - | - | - | N | Yes |

---

## Prompt Coverage (MCP)

| Prompt | Nina | Alex | Pat | Chris | Sam | Documented |
|--------|:----:|:----:|:---:|:-----:|:---:|:----------:|
| `vibey_quality_gate_check` | - | - | - | S | M | Yes |
| `vibey_security_scan` | - | - | - | S | S | Yes |
| `vibey_test_coverage` | - | - | - | M | S | Yes |
| `vibey_doc_check` | - | - | - | S | S | Yes |

---

## Documentation Coverage by Persona

### Nina (New User)

| Document | Status | Priority | Notes |
|----------|--------|----------|-------|
| README.md | Complete | Must | Entry point |
| QUICK_START.md | Complete | Must | First 30 minutes |
| USER_JOURNEY.md | Complete | Should | Detailed scenarios |
| CLI_REFERENCE.md | Complete | Should | Command lookup |
| JOURNEY_NEW_USER.md | Complete | Must | Primary journey |

**Coverage:** 100% of must-have docs exist

### Alex (Active Developer)

| Document | Status | Priority | Notes |
|----------|--------|----------|-------|
| CLI_REFERENCE.md | Complete | Must | Daily command lookup |
| ROADMAP_SYSTEM.md | Complete | Should | Conceptual understanding |
| GIT_HOOKS_GUIDE.md | Complete | Should | Git integration |
| JOURNEY_ACTIVE_DEVELOPER.md | Complete | Must | Primary journey |

**Coverage:** 100% of must-have docs exist

### Pat (Project Lead)

| Document | Status | Priority | Notes |
|----------|--------|----------|-------|
| CLI_REFERENCE.md | Complete | Must | Command reference |
| ROADMAP_SYSTEM.md | Complete | Must | Data model |
| ROADMAP_BEST_PRACTICES.md | Needed | Should | Planning guidance |
| JOURNEY_PROJECT_LEAD.md | Complete | Must | Primary journey |

**Coverage:** 67% (1 should-have doc missing)

### Chris (Contributor)

| Document | Status | Priority | Notes |
|----------|--------|----------|-------|
| CONTRIBUTING.md | Complete | Must | Contribution guide |
| CLAUDE.md | Complete | Must | Codebase context |
| CLI_REFERENCE.md | Complete | Should | Command reference |
| Development docs | Partial | Should | Architecture docs |
| JOURNEY_CONTRIBUTOR.md | Complete | Must | Primary journey |

**Coverage:** 80% (development docs partial)

### Sam (Platform Integrator)

| Document | Status | Priority | Notes |
|----------|--------|----------|-------|
| MCP_REFERENCE.md | Complete | Must | Tool reference |
| Adapter docs | Needed | Should | Custom adapters |
| JOURNEY_PLATFORM_INTEGRATOR.md | Complete | Must | Primary journey |

**Coverage:** 67% (adapter docs missing)

---

## Coverage Summary

### By Persona

| Persona | CLI Commands | MCP Tools | Documentation |
|---------|:------------:|:---------:|:-------------:|
| Nina (New User) | 12/12 (100%) | N/A | 5/5 (100%) |
| Alex (Active Developer) | 19/19 (100%) | N/A | 4/4 (100%) |
| Pat (Project Lead) | 22/22 (100%) | N/A | 3/4 (75%) |
| Chris (Contributor) | 14/14 (100%) | N/A | 4/5 (80%) |
| Sam (Platform Integrator) | 8/8 (100%) | 76/76 (100%) | 2/3 (67%) |

**Note:** Phase 3 added 4 audit trail commands that are now mapped to relevant personas.

### Gap Analysis

| Gap Type | Count | Details |
|----------|-------|---------|
| Missing Docs | 2 | ROADMAP_BEST_PRACTICES.md, Adapter Guide |
| Partial Docs | 1 | Development/architecture docs |
| Missing Features | 0 | All needed features exist |

---

## Walkthrough Coverage

Each persona has a dedicated step-by-step walkthrough with copy-paste commands and expected outputs:

| Persona | Walkthrough | Duration |
|---------|-------------|----------|
| Nina (New User) | [WALKTHROUGH_NEW_USER.md](../walkthroughs/WALKTHROUGH_NEW_USER.md) | 30 min |
| Alex (Active Developer) | [WALKTHROUGH_ACTIVE_DEVELOPER.md](../walkthroughs/WALKTHROUGH_ACTIVE_DEVELOPER.md) | 20 min |
| Pat (Project Lead) | [WALKTHROUGH_PROJECT_LEAD.md](../walkthroughs/WALKTHROUGH_PROJECT_LEAD.md) | 45 min |
| Chris (Contributor) | [WALKTHROUGH_CONTRIBUTOR.md](../walkthroughs/WALKTHROUGH_CONTRIBUTOR.md) | 60 min |
| Sam (Platform Integrator) | [WALKTHROUGH_PLATFORM_INTEGRATOR.md](../walkthroughs/WALKTHROUGH_PLATFORM_INTEGRATOR.md) | 45 min |

---

## Test Coverage (Phase 5)

### Summary

| Metric | Phase 1.4 | Current | Change |
|--------|-----------|---------|--------|
| Total Tests | 2,681 | 3,730 | +1,049 (+39%) |
| Pass Rate | 93.0% | 95.8% | +2.8% |
| Integration Tests | 0 | 59 | +59 |

### Test Distribution by Type

| Category | Count | Coverage |
|----------|-------|----------|
| Unit Tests | ~300 | Core functions |
| Model Tests | ~550 | Data models |
| CLI Tests | ~240 | Command interface |
| MCP Tests | ~111 | MCP tools/resources |
| Integration Tests | 59 | Cross-module flows |
| Platform Tests | ~249 | Platform adapters |
| E2E Tests | ~48 | Full workflows |

### Integration Test Coverage

| Test File | Tests | Coverage |
|-----------|-------|----------|
| test_cli_workflows.py | 23 | CLI to DB flows |
| test_mcp_workflows.py | 13 | MCP tool workflows |
| test_cross_module.py | 23 | Cross-module integration |

### CI/CD Quality Gates

| Gate | Threshold | Enforcement |
|------|-----------|-------------|
| Test Pass | 100% | Blocking |
| Coverage | 90% | Blocking |
| Lint (ruff) | 0 errors | Blocking |
| Type Check (mypy) | 0 errors | Blocking |
| Security (bandit) | 0 high | Blocking |

---

## Recommendations

### High Priority

1. **Create ROADMAP_BEST_PRACTICES.md** for Project Leads
   - Planning strategies
   - Progress tracking patterns
   - Stakeholder communication

2. **Create Adapter/Extension Guide** for Platform Integrators
   - Custom adapter development
   - Tool extension patterns
   - Testing integrations

### Medium Priority

3. **Expand Development Documentation**
   - Architecture decision records
   - Module-level documentation
   - API design patterns

### Low Priority

4. **Add More Examples**
   - More CLI command examples
   - MCP tool examples with responses
   - End-to-end workflow examples

---

## Maintenance

This matrix should be updated when:

1. New CLI commands are added
2. New MCP tools are added
3. New personas are identified
4. Documentation is created or modified

**Review Frequency:** Monthly or with each major release
