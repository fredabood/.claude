# CLI & MCP Tool Coverage Audit

**Task:** 01KDJKTRVZS618BM5ZZTQ34436
**Sprint:** Sprint 3 - Codebase Health Analysis
**Generated:** 2025-12-28T21:40:00+00:00

---

## Executive Summary

CLI test coverage is **moderate** with 4 untested command groups. MCP test coverage is **low** with only 12 of 76 tools having direct tests (16% coverage).

---

## CLI Command Coverage

### Coverage by Command Group

| Command | Test Files | Coverage Status |
|---------|------------|-----------------|
| artifact | 7 | Good |
| audit | 2 | Good |
| **auth** | **0** | **No tests** |
| config | 1 | Minimal |
| content | 1 | Minimal |
| context | 1 | Minimal |
| deploy | 1 | Minimal |
| discover | 2 | Good |
| docs | 1 | Minimal |
| **export** | **0** | **No tests** |
| git | 4 | Good |
| implement | 1 | Minimal |
| parity | 1 | Minimal |
| planned | 4 | Good |
| roadmap | 4 | Good |
| session | 6 | Good |
| **submodule** | **0** | **No tests** |
| **validate** | **0** | **No tests** |

### Untested CLI Command Groups (Priority Order)

1. **auth** - Critical for security features
   - add-signer, export, init-project, list, revoke, setup, status

2. **export** - Data export functionality
   - platform-native, gemini, list, run, stats

3. **submodule** - Git submodule integration
   - add-dep, aggregate, blockers, config, dep-graph, deps, discover, link, list, push, refresh, requirements, show, status, unlink, validate-deps

4. **validate** - Validation commands
   - frontmatter, assets, docs

---

## MCP Tool Coverage

### Summary

| Metric | Value |
|--------|-------|
| Total MCP Tools | 76 |
| Tools with Tests | 12 |
| Coverage | 16% |

### Tested MCP Tools (12)

- vibey_complete_task
- vibey_deploy
- vibey_deploy_list
- vibey_doc_check
- vibey_docs_generate_cli
- vibey_quality_gate_check
- vibey_query_roadmap
- vibey_roadmap_show
- vibey_roadmap_status
- vibey_security_scan
- vibey_start_task
- vibey_test_coverage

### Untested MCP Tools by Category (64)

#### Task Tools (4 untested)
- vibey_complete_sprint
- vibey_list_blockers
- vibey_list_dependencies
- vibey_refresh_progress

#### Query Tools (4 untested)
- vibey_query_sprint
- vibey_query_standards
- vibey_query_task
- vibey_query_track

#### Content Tools (6 untested)
- vibey_content_create
- vibey_content_delete
- vibey_content_list
- vibey_content_search
- vibey_content_show
- vibey_content_update
- vibey_content_validate

#### Agent Tools (15 untested)
- vibey_architecture_agent
- vibey_backend_engineer
- vibey_coordinator
- vibey_database_specialist
- vibey_diagram_engineer
- vibey_documentation_engineer
- vibey_documentation_maintenance_engineer
- vibey_frontend_engineer
- vibey_git_committer
- vibey_infrastructure_engineer
- vibey_ml_engineer
- vibey_observability_engineer
- vibey_performance_engineer
- vibey_researcher
- vibey_security_reviewer
- vibey_test_engineer
- vibey_vibey_manager
- vibey_web_developer

#### Handoff Tools (17 untested)
- vibey_handoff_api_spec
- vibey_handoff_application_requirements
- vibey_handoff_architecture_review
- vibey_handoff_codebase_audit_report
- vibey_handoff_component_design
- vibey_handoff_dashboard_specification
- vibey_handoff_database_schema_design
- vibey_handoff_deployment_checklist
- vibey_handoff_diagram_handoff
- vibey_handoff_documentation_update
- vibey_handoff_infrastructure_design
- vibey_handoff_integration
- vibey_handoff_logging_audit_report
- vibey_handoff_ml_design
- vibey_handoff_ml_evaluation_report
- vibey_handoff_performance_optimization_report
- vibey_handoff_phase_plan
- vibey_handoff_research_summary
- vibey_handoff_security_implementation_report
- vibey_handoff_security_report
- vibey_handoff_sprint_plan
- vibey_handoff_test_report

#### Workflow Tools (16 untested)
- vibey_sprint_planning
- vibey_start_sprint
- vibey_workflow_architecture_review
- vibey_workflow_claude_md_auto_update
- vibey_workflow_codebase_audit_discovery
- vibey_workflow_dashboard_visualization_creation
- vibey_workflow_documentation_diagrams
- vibey_workflow_documentation_research
- vibey_workflow_frontend_production_deployment
- vibey_workflow_frontend_security_hardening
- vibey_workflow_infrastructure_setup
- vibey_workflow_integration_only
- vibey_workflow_logging_audit
- vibey_workflow_ml_model_development
- vibey_workflow_performance_optimization
- vibey_workflow_single_feature_development
- vibey_workflow_sprint_planning
- vibey_workflow_weekly_sprint

---

## Priority Test Creation Order

### Critical (Security/Core)

1. **auth CLI commands** - Security-critical, no tests
2. **vibey_query_* tools** - Core query operations

### High (Frequently Used)

3. **submodule CLI commands** - Git integration features
4. **vibey_content_* tools** - Content management
5. **vibey_*_sprint tools** - Sprint lifecycle

### Medium (Agent/Workflow)

6. **Agent tools** - Can test via integration tests
7. **Workflow tools** - Complex, may need E2E tests
8. **Handoff tools** - Template generation

### Low (Less Used)

9. **export CLI commands** - Platform-specific
10. **validate CLI commands** - Utility commands

---

## Recommendations

1. **Add auth CLI tests first** - Security-critical functionality
2. **Add query MCP tool tests** - Core operations used by AI assistants
3. **Consider integration tests** for agent and workflow tools rather than unit tests
4. **Add submodule tests** - New feature area with no coverage

---

*Report generated: 2025-12-28T21:40:00+00:00*
