---
id: codebase-audit-report
name: Codebase Audit Report
version: 1.0.0
from_agent: researcher
to_agents:
- sprint-planning
- architecture-agent
purpose: Template for codebase audit report
variables:
- name: accomplishment
  type: string
  required: true
  description: Accomplishment value
- name: adr_count
  type: string
  required: true
  description: Adr Count value
- name: api_endpoints_documented
  type: string
  required: true
  description: Api Endpoints Documented value
- name: api_style
  type: string
  required: true
  description: Api Style value
- name: api_test_count
  type: string
  required: true
  description: Api Test Count value
- name: architecture_pattern
  type: string
  required: true
  description: Architecture Pattern value
- name: audit_commands_used
  type: string
  required: true
  description: Audit Commands Used value
- name: audit_date
  type: string
  required: true
  description: Audit Date value
- name: audit_duration
  type: string
  required: true
  description: Audit Duration value
- name: auth_method
  type: string
  required: true
  description: Auth Method value
- name: avg_commits_per_month
  type: string
  required: true
  description: Avg Commits Per Month value
- name: avg_commits_per_week
  type: string
  required: true
  description: Avg Commits Per Week value
- name: avg_dependency_age
  type: string
  required: true
  description: Avg Dependency Age value
- name: avg_file_size
  type: string
  required: true
  description: Avg File Size value
- name: avg_function_size
  type: string
  required: true
  description: Avg Function Size value
description: Template for codebase audit report
---

# Codebase Audit Report

**Project:** {{ config.project.name }}
**Audit Date:** {{ audit_date }}
**Analyzed By:** Vibey Framework - Codebase Audit & Discovery Workflow
**Report Version:** 1.0

---

## Executive Summary

**Overall Health Score:** {{ overall_health_score }}/100

**Quick Stats:**
- **Lines of Code:** {{ total_lines_of_code }}
- **Files:** {{ total_files }}
- **Tests:** {{ test_count }} ({{ test_coverage }}% coverage)
- **Security Score:** {{ security_score }}/100
- **Documentation Score:** {{ documentation_score }}/100

**Top Priorities for First Sprint:**
1. {{ priority_1 }}
2. {{ priority_2 }}
3. {{ priority_3 }}
4. {{ priority_4 }}
5. {{ priority_5 }}

---

## 1. Project Overview

### Project Classification
- **Type:** {{ project_type }} ({% if detection_confidence %}Confidence: {{ detection_confidence }}%{% else %}Detected{% endif %})
- **Architecture:** {{ architecture_pattern }}
- **Maturity:** {{ project_maturity }} ({{ project_age }} old, {{ commit_count }} commits)

### Directory Structure
```
{{ directory_structure }}
```

**Structure Assessment:**
- Organization: {{ structure_organization_score }}/10
- Consistency: {{ structure_consistency_score }}/10
- Best Practices: {{ structure_best_practices_score }}/10

---

## 2. Technology Stack

### Backend
- **Language:** {{ backend_language }} ({{ backend_language_version }})
- **Framework:** {{ backend_framework }} ({{ backend_framework_version }})
- **ORM/Database Library:** {{ database_library }}
- **API Style:** {{ api_style }}

### Frontend (if applicable)
{% if has_frontend %}
- **Language:** {{ frontend_language }}
- **Framework:** {{ frontend_framework }} ({{ frontend_framework_version }})
- **UI Library:** {{ ui_library }}
- **State Management:** {{ state_management }}
- **Build Tool:** {{ build_tool }}
{% else %}
*No frontend detected - Backend/API only project*
{% endif %}

### Database & Storage
- **Primary Database:** {{ primary_database }} ({{ database_version }})
- **ORM:** {{ orm_framework }}
- **Migrations:** {{ migration_tool }} {% if has_migrations %}({{ migration_count }} migrations found){% endif %}
- **Cache:** {% if has_cache %}{{ cache_system }}{% else %}None detected{% endif %}

### Infrastructure & DevOps
- **Containerization:** {% if has_docker %}Docker (Dockerfile, docker-compose.yml){% else %}None{% endif %}
- **Orchestration:** {% if has_kubernetes %}Kubernetes{% elif has_docker_swarm %}Docker Swarm{% else %}None{% endif %}
- **IaC:** {% if has_terraform %}Terraform{% elif has_pulumi %}Pulumi{% elif has_cloudformation %}CloudFormation{% else %}None{% endif %}
- **CI/CD:** {% if ci_cd_system %}{{ ci_cd_system }}{% else %}Not detected{% endif %}

### Development Tools
- **Package Manager:** {{ package_manager }}
- **Linter:** {% if has_linter %}{{ linter_tool }}{% else %}None detected ⚠️{% endif %}
- **Formatter:** {% if has_formatter %}{{ formatter_tool }}{% else %}None detected ⚠️{% endif %}
- **Type Checking:** {% if has_type_checking %}{{ type_checker }}{% else %}None detected ⚠️{% endif %}

**Technology Stack Health:** {{ tech_stack_health_score }}/100

**Findings:**
{% for finding in tech_stack_findings %}
- {{ finding.severity }}: {{ finding.description }}
{% endfor %}

---

## 3. Documentation Assessment

### Documentation Inventory

**Project Documentation:**
- README.md: {% if has_readme %}✓ Found ({{ readme_quality_score }}/10 quality){% else %}✗ Missing{% endif %}
- CONTRIBUTING.md: {% if has_contributing %}✓ Found{% else %}✗ Missing{% endif %}
- CHANGELOG.md: {% if has_changelog %}✓ Found{% else %}✗ Missing{% endif %}
- LICENSE: {% if has_license %}✓ Found ({{ license_type }}){% else %}✗ Missing{% endif %}

**API Documentation:**
- OpenAPI/Swagger: {% if has_openapi %}✓ Found{% else %}✗ Missing{% endif %}
- API Guide: {% if has_api_guide %}✓ Found{% else %}✗ Missing{% endif %}
- Endpoint Documentation: {% if api_endpoints_documented %}{{ api_endpoints_documented }}/{{ total_api_endpoints }} documented{% else %}Not assessed{% endif %}

**Architecture Documentation:**
- Architecture Overview: {% if has_architecture_doc %}✓ Found{% else %}✗ Missing{% endif %}
- Design Decisions (ADRs): {% if has_adrs %}✓ Found ({{ adr_count }} ADRs){% else %}✗ Missing{% endif %}
- System Diagrams: {% if has_diagrams %}✓ Found{% else %}✗ Missing{% endif %}

**Code Documentation:**
- Docstrings/JSDoc: {{ docstring_coverage }}% of functions documented
- Inline Comments: {{ comment_density }} comments per 100 lines
- Type Annotations: {% if has_type_annotations %}{{ type_annotation_coverage }}% coverage{% else %}Not used{% endif %}

**Documentation Score:** {{ documentation_score }}/100

**Gaps Identified:**
{% for gap in documentation_gaps %}
- {{ gap }}
{% endfor %}

**Recommendations:**
{% for recommendation in documentation_recommendations %}
- {{ recommendation }}
{% endfor %}

---

## 4. Security Assessment

**Overall Security Score:** {{ security_score }}/100

### Secrets & Credentials
{% if secrets_found %}
**⚠️  CRITICAL: {{ secrets_count }} Potential Secrets Found**
{% for secret in secrets_found %}
- {{ secret.file }}:{{ secret.line }} - {{ secret.type }} ({{ secret.pattern }})
{% endfor %}
{% else %}
**✓ No hardcoded secrets detected**
{% endif %}

**Environment Variables:**
- .env files committed: {% if env_files_committed %}⚠️  YES ({{ env_files_committed }}){% else %}✓ No{% endif %}
- Secrets management: {% if has_secrets_manager %}✓ {{ secrets_manager_tool }}{% else %}⚠️  None detected{% endif %}

### Dependency Vulnerabilities
**Scan Results:**
- Critical: {{ vuln_critical_count }}
- High: {{ vuln_high_count }}
- Medium: {{ vuln_medium_count }}
- Low: {{ vuln_low_count }}

{% if dependency_vulnerabilities %}
**Top Vulnerabilities:**
{% for vuln in dependency_vulnerabilities %}
- {{ vuln.severity }}: {{ vuln.package }} {{ vuln.version }} - {{ vuln.title }}
{% endfor %}
{% endif %}

### Security Patterns

**Authentication & Authorization:**
- Auth implementation: {% if has_auth %}{{ auth_method }}{% else %}⚠️  Not detected{% endif %}
- JWT/Session management: {% if has_jwt %}✓ Found{% else %}⚠️  Not detected{% endif %}
- RBAC/Permissions: {% if has_rbac %}✓ Implemented{% else %}⚠️  Not detected{% endif %}

**Input Validation:**
- SQL Injection protection: {% if sql_injection_safe %}✓ Using ORM{% else %}⚠️  Raw queries found ({{ raw_query_count }}){% endif %}
- XSS Protection: {% if xss_protection %}✓ Implemented{% else %}⚠️  Not detected{% endif %}
- Input sanitization: {% if has_validation %}✓ {{ validation_library }}{% else %}⚠️  Limited{% endif %}

**API Security:**
- Rate limiting: {% if has_rate_limiting %}✓ Implemented{% else %}⚠️  Not detected{% endif %}
- CORS configuration: {% if has_cors %}✓ Configured{% else %}⚠️  Not detected{% endif %}
- HTTPS enforcement: {% if enforces_https %}✓ Yes{% else %}⚠️  Not detected{% endif %}

**OWASP Top 10 Compliance:**
{% for owasp_item in owasp_compliance %}
- {{ owasp_item.name }}: {% if owasp_item.compliant %}✓{% else %}⚠️{% endif %} ({{ owasp_item.notes }})
{% endfor %}

**Critical Security Issues:**
{% for issue in critical_security_issues %}
- {{ issue }}
{% endfor %}

---

## 5. Testing & Quality

**Test Coverage:** {{ test_coverage }}%
**Test Count:** {{ test_count }} tests
**Testing Score:** {{ testing_score }}/100

### Test Infrastructure

**Test Framework:** {{ test_framework }}
**Test Organization:**
```
{{ test_directory_structure }}
```

**Test Types Detected:**
- Unit Tests: {% if has_unit_tests %}✓ ({{ unit_test_count }}){% else %}✗{% endif %}
- Integration Tests: {% if has_integration_tests %}✓ ({{ integration_test_count }}){% else %}✗{% endif %}
- E2E Tests: {% if has_e2e_tests %}✓ ({{ e2e_test_count }}){% else %}✗{% endif %}
- API Tests: {% if has_api_tests %}✓ ({{ api_test_count }}){% else %}✗{% endif %}

### Coverage Analysis

**Overall Coverage:** {{ test_coverage }}%

**By Component:**
{% for component in coverage_by_component %}
- {{ component.name }}: {{ component.coverage }}%
{% endfor %}

**Uncovered Critical Paths:**
{% for path in uncovered_critical_paths %}
- {{ path }}
{% endfor %}

### Code Quality

**Linting:**
- Linter configured: {% if has_linter %}✓ {{ linter_tool }}{% else %}✗ None{% endif %}
- Linting issues: {% if linting_issues %}{{ linting_issues }} issues found{% else %}Not scanned{% endif %}

**Code Formatting:**
- Formatter configured: {% if has_formatter %}✓ {{ formatter_tool }}{% else %}✗ None{% endif %}
- Formatting consistency: {{ formatting_consistency_score }}/10

**Type Safety:**
- Type system: {% if has_type_system %}✓ {{ type_system }}{% else %}✗ Dynamic typing only{% endif %}
- Type coverage: {% if type_coverage %}{{ type_coverage }}%{% else %}N/A{% endif %}

**Code Metrics:**
- Average file size: {{ avg_file_size }} lines
- Average function size: {{ avg_function_size }} lines
- Complexity score: {{ complexity_score }}/10 (lower is better)

---

## 6. Logging & Observability

**Logging Score:** {{ logging_score }}/100
**Observability Score:** {{ observability_score }}/100

### Logging Implementation

**Logging Framework:** {% if logging_framework %}{{ logging_framework }}{% else %}⚠️  None detected{% endif %}

**Logging Patterns:**
- Structured logging: {% if has_structured_logging %}✓ Yes{% else %}⚠️  No (console.log/print statements){% endif %}
- Log levels: {% if uses_log_levels %}✓ Configured{% else %}⚠️  Not used{% endif %}
- Correlation IDs: {% if has_correlation_ids %}✓ Implemented{% else %}⚠️  Not found{% endif %}

**Logging Coverage:**
- API endpoints logged: {{ endpoints_with_logging }}/{{ total_endpoints }}
- Error handling logged: {% if errors_logged %}✓ Yes{% else %}⚠️  Incomplete{% endif %}
- Business events logged: {% if business_events_logged %}✓ Yes{% else %}⚠️  Limited{% endif %}

### Monitoring & Observability

**APM/Monitoring Tools:** {% if apm_tools %}{{ apm_tools | join(', ') }}{% else %}⚠️  None detected{% endif %}

**Metrics:**
- Metrics collection: {% if has_metrics %}✓ {{ metrics_system }}{% else %}⚠️  Not implemented{% endif %}
- Custom metrics: {% if has_custom_metrics %}✓ Found{% else %}⚠️  None{% endif %}
- Performance tracking: {% if has_performance_tracking %}✓ Yes{% else %}⚠️  No{% endif %}

**Health Checks:**
- Health endpoint: {% if has_health_endpoint %}✓ {{ health_endpoint }}{% else %}⚠️  Missing{% endif %}
- Readiness checks: {% if has_readiness %}✓ Yes{% else %}⚠️  No{% endif %}
- Liveness checks: {% if has_liveness %}✓ Yes{% else %}⚠️  No{% endif %}

**Alerting:**
- Alert configuration: {% if has_alerts %}✓ Found{% else %}⚠️  None detected{% endif %}
- Error tracking: {% if has_error_tracking %}✓ {{ error_tracking_tool }}{% else %}⚠️  Not implemented{% endif %}

---

## 7. Code Organization & Patterns

**Organization Score:** {{ organization_score }}/100

### Architecture Pattern
**Pattern Detected:** {{ architecture_pattern }}

**Pattern Implementation:**
{% for aspect in architecture_aspects %}
- {{ aspect.name }}: {% if aspect.implemented %}✓{% else %}⚠️{% endif %} ({{ aspect.notes }})
{% endfor %}

### Naming Conventions
- Files: {{ file_naming_convention }}
- Functions: {{ function_naming_convention }}
- Classes: {{ class_naming_convention }}
- Variables: {{ variable_naming_convention }}

**Consistency:** {{ naming_consistency_score }}/10

### Code Organization
- Separation of concerns: {{ separation_of_concerns_score }}/10
- Module cohesion: {{ module_cohesion_score }}/10
- Dependency management: {{ dependency_management_score }}/10

### Design Patterns Used
{% for pattern in design_patterns %}
- {{ pattern.name }}: {{ pattern.usage }}
{% endfor %}

---

## 8. Deployment & Infrastructure

**Deployment Maturity:** {{ deployment_maturity_score }}/100

### Deployment Configuration

**Containerization:**
{% if has_docker %}
- Dockerfile: ✓ Found
- docker-compose.yml: {% if has_docker_compose %}✓ Found{% else %}✗ Missing{% endif %}
- Multi-stage builds: {% if has_multistage_docker %}✓ Yes{% else %}⚠️  No{% endif %}
{% else %}
- ⚠️  No Docker configuration found
{% endif %}

**Infrastructure as Code:**
{% if has_iac %}
- IaC Tool: {{ iac_tool }}
- Environments: {{ iac_environments | join(', ') }}
- Modules/Components: {{ iac_component_count }}
{% else %}
- ⚠️  No IaC detected
{% endif %}

**CI/CD:**
{% if has_ci_cd %}
- Platform: {{ ci_cd_platform }}
- Pipelines: {{ pipeline_count }}
- Automated tests: {% if ci_runs_tests %}✓ Yes{% else %}⚠️  No{% endif %}
- Automated deployment: {% if ci_deploys %}✓ Yes{% else %}⚠️  No{% endif %}
{% else %}
- ⚠️  No CI/CD configuration found
{% endif %}

---

## 9. Dependencies & Maintenance

**Dependency Health:** {{ dependency_health_score }}/100

### Dependency Analysis

**Total Dependencies:**
- Production: {{ prod_dependency_count }}
- Development: {{ dev_dependency_count }}

**Outdated Dependencies:**
- Major updates available: {{ major_updates_count }}
- Minor updates available: {{ minor_updates_count }}
- Patch updates available: {{ patch_updates_count }}

**Dependency Age:**
- Average age: {{ avg_dependency_age }}
- Oldest dependency: {{ oldest_dependency }} ({{ oldest_dependency_age }})

**Maintenance Indicators:**
- Last commit: {{ last_commit_date }} ({{ days_since_last_commit }} days ago)
- Commit frequency: {{ avg_commits_per_month }} commits/month
- Active maintenance: {% if actively_maintained %}✓ Yes{% else %}⚠️  Low activity{% endif %}

---

## 10. Git History Analysis (Optional)

{% if git_history_analyzed %}

**Analysis Period:** {{ git_analysis_period }} ({{ git_analysis_start_date }} to {{ git_analysis_end_date }})
**Total Commits Analyzed:** {{ total_commits_analyzed }}

### Sprint Cadence & Release Pattern

**Detected Sprint Cadence:** {{ detected_sprint_cadence }}
{% if sprint_cadence_confidence %}(Confidence: {{ sprint_cadence_confidence }}%){% endif %}

**Recent Releases:**
{% for release in recent_releases %}
- **{{ release.tag }}** ({{ release.date }}) - "{{ release.title }}"
  {% if release.description %}- {{ release.description }}{% endif %}
{% endfor %}

**Release Pattern:** {{ release_pattern }}
**Branch Strategy:** {{ branch_strategy }}

### Recent Sprint Summary

{% for sprint in recent_sprints %}
**{{ sprint.name }} ({{ sprint.date_range }}):** {{ sprint.title }}
{% for accomplishment in sprint.accomplishments %}
- {{ accomplishment }}
{% endfor %}
- {{ sprint.commit_count }} commits, {{ sprint.lines_changed }} lines changed
{% if sprint.breaking_changes %}- Breaking changes: {{ sprint.breaking_changes }}{% endif %}

{% endfor %}

### Development Velocity & Activity

**Commit Activity:**
- Average: {{ avg_commits_per_week }} commits/week
- Peak activity: {{ peak_activity_period }} ({{ peak_commits }} commits)
- Lowest activity: {{ low_activity_period }} ({{ low_commits }} commits)

**Code Churn:**
- Average: {{ avg_lines_per_month }} lines/month
- Total additions ({{ git_analysis_period }}): {{ total_lines_added }} lines
- Total deletions ({{ git_analysis_period }}): {{ total_lines_deleted }} lines
- Net change: {{ net_lines_changed }} lines

**Team Activity:**
{% for contributor in top_contributors %}
- {{ contributor.name }}: {{ contributor.commits }} commits ({{ contributor.percentage }}%)
{% endfor %}

**Commit Type Breakdown:**
- Features: {{ feature_commits_count }} ({{ feature_commits_percentage }}%)
- Bug fixes: {{ bugfix_commits_count }} ({{ bugfix_commits_percentage }}%)
- Refactoring: {{ refactor_commits_count }} ({{ refactor_commits_percentage }}%)
- Documentation: {{ docs_commits_count }} ({{ docs_commits_percentage }}%)
- Testing: {{ test_commits_count }} ({{ test_commits_percentage }}%)
- Security: {{ security_commits_count }} ({{ security_commits_percentage }}%)
- Other: {{ other_commits_count }} ({{ other_commits_percentage }}%)

### Technology Evolution & Migrations

**Recent Technology Changes:**
{% for change in recent_tech_changes %}
- **{{ change.date }}:** {{ change.description }}
{% endfor %}

**Dependency Updates (Last {{ git_analysis_period }}):**
- Major updates: {{ major_dep_updates_count }}
- Minor updates: {{ minor_dep_updates_count }}
- Security patches: {{ security_patch_count }}

**Infrastructure Changes:**
{% for infra_change in infrastructure_changes %}
- {{ infra_change.date }}: {{ infra_change.description }}
{% endfor %}

### Most Active Development Areas

**Top 10 Modified Files/Directories:**
{% for area in most_active_areas %}
{{ loop.index }}. `{{ area.path }}` - {{ area.commits }} commits
   {% if area.context %}- {{ area.context }}{% endif %}
{% endfor %}

### Recent Focus Areas & Patterns

**Development Focus:**
{{ development_focus_description }}

**Identified Patterns:**
{% for pattern in identified_patterns %}
- {{ pattern.name }}: {{ pattern.description }}
{% endfor %}

**Breaking Changes:**
{% if breaking_changes_count > 0 %}
{{ breaking_changes_count }} breaking changes identified in the last {{ git_analysis_period }}:
{% for breaking_change in breaking_changes %}
- **{{ breaking_change.date }}:** {{ breaking_change.description }}
  - Commit: {{ breaking_change.commit_hash }}
  {% if breaking_change.migration_notes %}- Migration: {{ breaking_change.migration_notes }}{% endif %}
{% endfor %}
{% else %}
No breaking changes detected in the last {{ git_analysis_period }}.
{% endif %}

### Context for Roadmap Planning

Based on the git history analysis, the project is:
{% for insight in roadmap_insights %}
- **{{ insight.aspect }}**: {{ insight.observation }}
{% endfor %}

**Recent Work Trajectory:**
{{ work_trajectory_description }}

**Recommended Next Steps Based on History:**
{% for recommendation in history_based_recommendations %}
{{ loop.index }}. {{ recommendation }}
{% endfor %}

**Development Velocity Baseline:**
- Sustainable sprint size: {{ sustainable_sprint_size }} (based on {{ avg_commits_per_week }} commits/week)
- Recommended sprint length: {{ recommended_sprint_length }} (matches detected {{ detected_sprint_cadence }} pattern)

### Commit Convention Compliance

**Conventional Commits Usage:** {{ conventional_commits_percentage }}% of commits
**Commit Message Quality:** {{ commit_message_quality_score }}/10

**Examples of Recent Good Commits:**
{% for commit in good_commit_examples %}
- `{{ commit.hash }}` - {{ commit.message }}
{% endfor %}

{% if commit_quality_issues %}
**Commit Quality Issues:**
{% for issue in commit_quality_issues %}
- {{ issue }}
{% endfor %}
{% endif %}

{% else %}
*Git history analysis was not performed. To include git history insights, run the audit with git analysis enabled.*

**To enable git history analysis:**
When running the Codebase Audit & Discovery workflow, opt in when prompted: "Would you like me to analyze the git history?"
{% endif %}

---

## 11. Identified Gaps & Opportunities

### Critical Gaps (Address Immediately)
{% for gap in critical_gaps %}
- **{{ gap.title }}**: {{ gap.description }}
  - Impact: {{ gap.impact }}
  - Effort: {{ gap.effort }}
  - Priority: {{ gap.priority }}
{% endfor %}

### Important Improvements (Address in Sprint 1-2)
{% for improvement in important_improvements %}
- **{{ improvement.title }}**: {{ improvement.description }}
  - Impact: {{ improvement.impact }}
  - Effort: {{ improvement.effort }}
{% endfor %}

### Nice to Have (Address Later)
{% for nice_to_have in nice_to_haves %}
- {{ nice_to_have }}
{% endfor %}

---

## 12. Recommendations for First Sprint

### Immediate Actions (Week 1)
{% for action in immediate_actions %}
{{ loop.index }}. **{{ action.title }}**
   - Why: {{ action.rationale }}
   - How: {{ action.approach }}
   - Expected outcome: {{ action.outcome }}
{% endfor %}

### Sprint Goals Suggestion
Based on the audit, I recommend focusing the first sprint on:

**Theme:** {{ recommended_sprint_theme }}

**Objectives:**
{% for objective in recommended_sprint_objectives %}
- {{ objective }}
{% endfor %}

**Estimated Effort:** {{ estimated_sprint_effort }}

### Quality Gate Recommendations
Based on current metrics, I recommend these quality gates:

```yaml
quality_gates:
  test_coverage_minimum: {{ recommended_test_coverage }}  # Current: {{ test_coverage }}%
  security_score_minimum: {{ recommended_security_score }}  # Current: {{ security_score }}/100
  logging_audit_minimum: {{ recommended_logging_score }}  # Current: {{ logging_score }}/100
```

---

## 13. Health Scores Summary

| Dimension | Score | Status |
|-----------|-------|--------|
| Overall Health | {{ overall_health_score }}/100 | {{ overall_health_status }} |
| Security | {{ security_score }}/100 | {{ security_status }} |
| Testing | {{ testing_score }}/100 | {{ testing_status }} |
| Documentation | {{ documentation_score }}/100 | {{ documentation_status }} |
| Code Quality | {{ code_quality_score }}/100 | {{ code_quality_status }} |
| Logging | {{ logging_score }}/100 | {{ logging_status }} |
| Observability | {{ observability_score }}/100 | {{ observability_status }} |
| Organization | {{ organization_score }}/100 | {{ organization_status }} |
| Deployment | {{ deployment_maturity_score }}/100 | {{ deployment_status }} |
| Dependencies | {{ dependency_health_score }}/100 | {{ dependency_status }} |

**Legend:**
- 85-100: ✅ Excellent
- 70-84: ✓ Good
- 50-69: ⚠️  Needs Improvement
- 0-49: ❌ Critical

---

## Appendix A: Detailed Metrics

### Lines of Code by Language
{% for lang in lines_by_language %}
- {{ lang.language }}: {{ lang.lines }} lines ({{ lang.percentage }}%)
{% endfor %}

### File Count by Type
{% for type in files_by_type %}
- {{ type.extension }}: {{ type.count }} files
{% endfor %}

### Largest Files
{% for file in largest_files %}
- {{ file.path }}: {{ file.lines }} lines
{% endfor %}

---

## Appendix B: Commands Used

This audit was performed using the following analysis commands:

```bash
{{ audit_commands_used }}
```

---

**Report Generated:** {{ audit_date }}
**Analysis Duration:** {{ audit_duration }}
**Vibey Framework Version:** 1.0

---

*This report was automatically generated by the Vibey Framework Codebase Audit & Discovery workflow. Review findings with your team and adjust recommendations based on your specific context and priorities.*
