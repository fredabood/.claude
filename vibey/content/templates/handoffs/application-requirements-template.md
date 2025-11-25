---
id: application-requirements
name: Application Requirements
version: 1.0.0
from_agent: web-developer
to_agents:
- test-engineer
- documentation-engineer
purpose: Template for application requirements
variables:
- name: acceptance_criterion
  type: string
  required: true
  description: Acceptance Criterion value
- name: accessibility_compliance_level
  type: string
  required: true
  description: Accessibility Compliance Level value
- name: accessibility_requirement
  type: string
  required: true
  description: Accessibility Requirement value
- name: alerting_channels
  type: string
  required: true
  description: Alerting Channels value
- name: alt_flow
  type: string
  required: true
  description: Alt Flow value
- name: api_architecture
  type: string
  required: true
  description: Api Architecture value
- name: api_auth_method
  type: string
  required: true
  description: Api Auth Method value
- name: api_style
  type: string
  required: true
  description: Api Style value
- name: application_name
  type: string
  required: true
  description: Application Name value
- name: application_type
  type: string
  required: true
  description: Application Type value
- name: architecture_type
  type: string
  required: true
  description: Architecture Type value
- name: assumption
  type: string
  required: true
  description: Assumption value
- name: auth_requirements
  type: string
  required: true
  description: Auth Requirements value
- name: authentication_method
  type: string
  required: true
  description: Authentication Method value
- name: author_name
  type: string
  required: true
  description: Author Name value
description: Template for application requirements
---

# Application Requirements: {{ application_name }}

**Document Type:** Handoff Template
**From:** {{ config.roles.product_owner or 'Product Owner / Business Stakeholder' }}
**To:** {{ config.roles.development_team or 'Development Team / Project Lead' }}
**Purpose:** Comprehensive application requirements specification
**Related Workflow:** Application Development - Requirements Phase

---

## Document Metadata

| Field | Value |
|-------|-------|
| **Application Name** | {{ application_name }} |
| **Created By** | {{ author_name }} |
| **Date** | {{ creation_date }} |
| **Application Type** | {{ application_type }} |
| **Technology Stack** | {{ tech_stack_summary }} |
| **Status** | {{ document_status }} |
| **Version** | {{ requirements_version }} |

---

## 1. Executive Summary

### Business Context

**Problem Statement:** {{ problem_statement }}

**Business Objectives:**
{% for objective in business_objectives %}
- {{ objective }}
{% endfor %}

**Success Metrics:**
{% for metric in success_metrics %}
- **{{ metric.name }}**: {{ metric.target }} ({{ metric.measurement }})
{% endfor %}

### Target Audience

**Primary Users:** {{ primary_users }}
**Secondary Users:** {{ secondary_users }}
**Expected User Base:** {{ expected_user_count }}

**User Personas:**
{% for persona in user_personas %}
{{ loop.index }}. **{{ persona.name }}** ({{ persona.role }})
   - **Goals:** {{ persona.goals }}
   - **Pain Points:** {{ persona.pain_points }}
   - **Tech Proficiency:** {{ persona.tech_level }}
{% endfor %}

---

## 2. Application Overview

### Application Type

{% if config.project.type == 'web-app' %}
**Type:** Web Application
**Architecture:** {{ architecture_type }}
**Frontend:** {{ config.web_framework.frontend or 'React/Vue/Angular/Svelte' }}
**Backend:** {{ config.web_framework.backend or 'FastAPI/Express/Spring Boot/Django' }}

{% elif config.project.type == 'api' %}
**Type:** API / Backend Service
**Architecture:** {{ api_architecture }}
**Framework:** {{ config.web_framework.backend or 'FastAPI/Express/Spring Boot/Flask' }}
**API Style:** {{ api_style }}

{% elif config.project.type == 'data-platform' %}
**Type:** Data Application / Analytics Platform
**Architecture:** {{ data_app_architecture }}
**Frontend:** {{ data_app_frontend }}
**Data Access:** {{ data_access_method }}

{% elif config.project.type == 'ml' %}
**Type:** ML Application / Model Serving
**Architecture:** {{ ml_app_architecture }}
**Inference Type:** {{ inference_type }}
**ML Framework:** {{ ml_framework }}
{% endif %}

### Deployment Environment

**Hosting Platform:** {{ hosting_platform }}
**Cloud Provider:** {{ config.cloud_provider or 'AWS/Azure/GCP/On-premise' }}
**Environments:**
{% for environment in deployment_environments %}
- **{{ environment.name }}**: {{ environment.url }} ({{ environment.purpose }})
{% endfor %}

### Technology Stack

{% if config.project.type == 'web-app' %}
**Frontend:**
- **Framework:** {{ config.web_framework.frontend }}
- **UI Library:** {{ config.ui_library or 'Material-UI/Ant Design/Custom' }}
- **State Management:** {{ config.state_management.library or 'Redux/Zustand/Context API' }}
- **Build Tool:** {{ frontend_build_tool or 'Vite/Webpack/Parcel' }}

**Backend:**
- **Framework:** {{ config.web_framework.backend }}
- **Database:** {{ config.technology_stack.database or 'PostgreSQL/MySQL/MongoDB' }}
- **Cache:** {{ cache_layer or 'Redis/Memcached' }}
- **Authentication:** {{ auth_method or 'JWT/OAuth2/Session' }}

{% elif config.project.type == 'api' %}
**API:**
- **Framework:** {{ config.web_framework.backend }}
- **API Spec:** {{ api_spec_format or 'OpenAPI 3.0/GraphQL' }}
- **Database:** {{ config.technology_stack.database }}
- **Authentication:** {{ api_auth_method }}
- **Documentation:** {{ api_docs_tool or 'Swagger/Redoc/GraphQL Playground' }}

{% elif config.project.type == 'data-platform' %}
**Data Platform:**
- **Compute:** {{ data_compute_platform }}
- **Storage:** {{ data_storage_platform }}
- **Orchestration:** {{ orchestration_tool or 'Airflow/Dagster/Prefect' }}
- **Visualization:** {{ viz_tool or 'Streamlit/Dash/Gradio/Superset' }}

{% elif config.project.type == 'ml' %}
**ML Platform:**
- **Training:** {{ ml_training_platform }}
- **Serving:** {{ ml_serving_platform }}
- **Monitoring:** {{ ml_monitoring_platform }}
- **Experiment Tracking:** {{ config.ml_platform.experiment_tracking }}
{% endif %}

---

## 3. User Stories & Use Cases

### Core User Stories (Must Have)

{% for story in core_user_stories %}
**{{ loop.index }}. {{ story.title }}**

**As a** {{ story.user_role }}
**I want to** {{ story.action }}
**So that** {{ story.benefit }}

**Acceptance Criteria:**
{% for criterion in story.acceptance_criteria %}
- [ ] {{ criterion }}
{% endfor %}

**Priority:** {{ story.priority }}
**Effort Estimate:** {{ story.effort }}

---

{% endfor %}

### Additional User Stories (Nice to Have)

{% for story in additional_user_stories %}
**{{ loop.index }}. {{ story.title }}**
- **As a** {{ story.user_role }}, **I want to** {{ story.action }}
- **Priority:** {{ story.priority }}
{% endfor %}

### Use Cases

{% for use_case in use_cases %}
**Use Case {{ loop.index }}: {{ use_case.name }}**

**Actor:** {{ use_case.actor }}
**Preconditions:** {{ use_case.preconditions }}

**Main Flow:**
{% for step in use_case.main_flow %}
{{ loop.index }}. {{ step }}
{% endfor %}

**Alternative Flows:**
{% for alt_flow in use_case.alternative_flows %}
- {{ alt_flow }}
{% endfor %}

**Postconditions:** {{ use_case.postconditions }}

---

{% endfor %}

---

## 4. Functional Requirements

### Core Features (Must Have)

{% for feature in core_features %}
### {{ loop.index }}. {{ feature.name }}

**Description:** {{ feature.description }}

**User Flow:**
{% for step in feature.user_flow %}
{{ loop.index }}. {{ step }}
{% endfor %}

**Inputs:**
{% for input in feature.inputs %}
- **{{ input.name }}**: {{ input.type }} - {{ input.description }}
  - **Validation:** {{ input.validation }}
{% endfor %}

**Outputs:**
{% for output in feature.outputs %}
- **{{ output.name }}**: {{ output.description }}
{% endfor %}

**Business Rules:**
{% for rule in feature.business_rules %}
- {{ rule }}
{% endfor %}

**Dependencies:**
{% for dependency in feature.dependencies %}
- {{ dependency }}
{% endfor %}

---

{% endfor %}

### Additional Features (Should Have)

{% for feature in additional_features %}
**{{ loop.index }}. {{ feature.name }}**
- **Description:** {{ feature.description }}
- **Priority:** {{ feature.priority }}
- **Estimated Effort:** {{ feature.effort }}
{% endfor %}

### Future Features (Nice to Have)

{% for feature in future_features %}
- **{{ feature.name }}**: {{ feature.description }}
{% endfor %}

---

## 5. Data Requirements

### Data Sources

{% for data_source in data_sources %}
**{{ loop.index }}. {{ data_source.name }}**
- **Type:** {{ data_source.type }}
- **Location:** {{ data_source.location }}
- **Access Method:** {{ data_source.access_method }}
- **Permissions:** {{ data_source.permissions }}
- **Refresh Frequency:** {{ data_source.refresh_frequency }}
- **Data Volume:** {{ data_source.data_volume }}
- **Owner:** {{ data_source.owner }}

{% if data_source.schema %}
**Schema:**
```{{ data_source.schema_format or 'sql' }}
{{ data_source.schema }}
```
{% endif %}
{% endfor %}

### Data Models

{% for data_model in data_models %}
**{{ data_model.name }}**

```{{ config.technology_stack.backend.language }}
{{ data_model.definition }}
```

**Relationships:**
{% for relationship in data_model.relationships %}
- {{ relationship }}
{% endfor %}
{% endfor %}

### Data Quality Requirements

{% for requirement in data_quality_requirements %}
- **{{ requirement.dimension }}**: {{ requirement.requirement }}
  - **Validation:** {{ requirement.validation }}
  - **Action on Failure:** {{ requirement.action }}
{% endfor %}

---

## 6. UI/UX Requirements

{% if config.project.type in ['web-app', 'data-platform'] %}
### Layout & Navigation

**Layout Type:** {{ layout_type }}
**Navigation Pattern:** {{ navigation_pattern }}

**Page Structure:**
{% for page in pages %}
{{ loop.index }}. **{{ page.name }}** - {{ page.route }}
   - **Purpose:** {{ page.purpose }}
   - **Components:** {{ page.components }}
   - **Access:** {{ page.access_level }}
{% endfor %}

### Wireframes

**Wireframe Location:** {{ wireframe_location }}

{% if wireframe_description %}
{{ wireframe_description }}
{% endif %}

### Design System

**UI Library:** {{ config.ui_library or 'Material-UI/Ant Design/Custom' }}

**Color Palette:**
{% for color in color_palette %}
- **{{ color.name }}**: {{ color.hex }} ({{ color.usage }})
{% endfor %}

**Typography:**
- **Headings:** {{ heading_font }} ({{ heading_sizes }})
- **Body:** {{ body_font }} ({{ body_size }})
- **Code:** {{ code_font }}

**Spacing:** {{ spacing_system }}

**Responsive Breakpoints:**
{% for breakpoint in responsive_breakpoints %}
- **{{ breakpoint.name }}**: {{ breakpoint.width }} ({{ breakpoint.description }})
{% endfor %}

### Accessibility Requirements

**Compliance Level:** {{ accessibility_compliance_level }}

**Requirements:**
{% for accessibility_requirement in accessibility_requirements %}
- {{ accessibility_requirement }}
{% endfor %}
{% endif %}

---

## 7. Non-Functional Requirements

### Performance Requirements

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
{% for perf_req in performance_requirements %}
| **{{ perf_req.metric }}** | {{ perf_req.target }} | {{ perf_req.measurement }} |
{% endfor %}

### Scalability Requirements

**Expected Load:**
- **Users:** {{ expected_concurrent_users }} concurrent users
- **Requests:** {{ expected_requests_per_second }} req/sec
- **Data Volume:** {{ expected_data_volume }}

**Scaling Strategy:** {{ scaling_strategy }}

### Reliability & Availability

**Uptime Target:** {{ uptime_target }}%
**MTTR Target:** {{ mttr_target }}
**Backup Strategy:** {{ backup_strategy }}
**Disaster Recovery:** {{ disaster_recovery_rto }} RTO, {{ disaster_recovery_rpo }} RPO

### Security Requirements

**Authentication:** {{ auth_requirements }}
**Authorization:** {{ authz_requirements }}
**Data Encryption:** {{ encryption_requirements }}
**Compliance:** {{ compliance_requirements }}

**Security Standards:**
{% for security_standard in security_standards %}
- {{ security_standard }}
{% endfor %}

### Maintainability

**Code Quality:**
- **Test Coverage:** ≥ {{ test_coverage_target }}%
- **Documentation:** {{ documentation_requirements }}
- **Code Style:** {{ code_style_guide }}

**Monitoring:**
{% for monitoring_requirement in monitoring_requirements %}
- {{ monitoring_requirement }}
{% endfor %}

---

## 8. Integration Requirements

### External Integrations

{% for integration in external_integrations %}
**{{ loop.index }}. {{ integration.name }}**
- **Type:** {{ integration.type }}
- **Purpose:** {{ integration.purpose }}
- **Protocol:** {{ integration.protocol }}
- **Authentication:** {{ integration.auth }}
- **Data Format:** {{ integration.data_format }}
- **Frequency:** {{ integration.frequency }}
- **Error Handling:** {{ integration.error_handling }}
{% endfor %}

### APIs to Consume

{% for api in apis_to_consume %}
**{{ api.name }}**
- **Provider:** {{ api.provider }}
- **Endpoint:** {{ api.endpoint }}
- **Rate Limit:** {{ api.rate_limit }}
- **SLA:** {{ api.sla }}
{% endfor %}

### APIs to Provide

{% if provides_api %}
{% for api_endpoint in api_endpoints %}
**{{ api_endpoint.method }} {{ api_endpoint.path }}**
- **Description:** {{ api_endpoint.description }}
- **Request:** {{ api_endpoint.request_format }}
- **Response:** {{ api_endpoint.response_format }}
- **Authentication:** {{ api_endpoint.auth_required }}
- **Rate Limit:** {{ api_endpoint.rate_limit }}
{% endfor %}
{% endif %}

---

## 9. Authentication & Authorization

### Authentication Method

**Method:** {{ authentication_method }}

{% if authentication_method == 'oauth2' %}
**OAuth2 Configuration:**
- **Provider:** {{ oauth_provider }}
- **Scopes:** {{ oauth_scopes }}
- **Redirect URI:** {{ oauth_redirect_uri }}

{% elif authentication_method == 'jwt' %}
**JWT Configuration:**
- **Secret Storage:** {{ jwt_secret_storage }}
- **Token Expiry:** {{ jwt_token_expiry }}
- **Refresh Token:** {{ jwt_refresh_enabled }}

{% elif authentication_method == 'session' %}
**Session Configuration:**
- **Session Store:** {{ session_store }}
- **Session Duration:** {{ session_duration }}
- **Secure Cookies:** {{ secure_cookies_enabled }}
{% endif %}

### User Roles & Permissions

| Role | Permissions | Access Level |
|------|-------------|--------------|
{% for role in user_roles %}
| **{{ role.name }}** | {{ role.permissions }} | {{ role.access_level }} |
{% endfor %}

### Authorization Rules

{% for authz_rule in authorization_rules %}
- **{{ authz_rule.resource }}**: {{ authz_rule.rule }}
{% endfor %}

---

## 10. Deployment & Operations

### Deployment Strategy

**Deployment Method:** {{ deployment_method }}
**CI/CD Platform:** {{ config.ci_cd.platform or 'GitHub Actions/GitLab CI/Jenkins' }}

**Deployment Pipeline:**
{% for stage in deployment_pipeline %}
{{ loop.index }}. **{{ stage.name }}**: {{ stage.description }}
{% endfor %}

### Environment Configuration

{% for env in deployment_environments %}
**{{ env.name }} Environment:**
- **URL:** {{ env.url }}
- **Infrastructure:** {{ env.infrastructure }}
- **Scaling:** {{ env.scaling }}
- **Monitoring:** {{ env.monitoring }}
- **Deployment Approval:** {{ env.approval_required }}
{% endfor %}

### Environment Variables

**Required Environment Variables:**
{% for env_var in environment_variables %}
- `{{ env_var.name }}`: {{ env_var.description }}
  - **Required:** {{ env_var.required }}
  - **Default:** {{ env_var.default }}
  - **Secret:** {{ env_var.is_secret }}
{% endfor %}

### Monitoring & Alerting

**Monitoring Tools:** {{ monitoring_tools }}

**Key Metrics to Monitor:**
{% for metric in metrics_to_monitor %}
- **{{ metric.name }}**: {{ metric.description }}
  - **Alert Threshold:** {{ metric.alert_threshold }}
{% endfor %}

**Alerting Channels:** {{ alerting_channels }}

---

## 11. Testing Requirements

### Test Strategy

**Testing Levels:**
{% for test_level in test_levels %}
- **{{ test_level.type }}**: {{ test_level.coverage_target }}% coverage
  - **Scope:** {{ test_level.scope }}
{% endfor %}

### Test Scenarios

{% for test_scenario in test_scenarios %}
**{{ loop.index }}. {{ test_scenario.name }}**
- **Type:** {{ test_scenario.type }}
- **Description:** {{ test_scenario.description }}
- **Expected Result:** {{ test_scenario.expected_result }}
- **Priority:** {{ test_scenario.priority }}
{% endfor %}

### User Acceptance Testing

**UAT Participants:** {{ uat_participants }}
**UAT Environment:** {{ uat_environment }}
**UAT Duration:** {{ uat_duration }}

**UAT Checklist:**
{% for uat_item in uat_checklist %}
- [ ] {{ uat_item }}
{% endfor %}

---

## 12. Documentation Requirements

### Technical Documentation

{% for doc in technical_documentation %}
- **{{ doc.name }}**: {{ doc.description }}
  - **Location:** {{ doc.location }}
  - **Owner:** {{ doc.owner }}
{% endfor %}

### User Documentation

{% for user_doc in user_documentation %}
- **{{ user_doc.name }}**: {{ user_doc.description }}
  - **Format:** {{ user_doc.format }}
  - **Audience:** {{ user_doc.audience }}
{% endfor %}

### Training Requirements

{% if requires_training %}
**Training Materials:**
{% for training in training_materials %}
- {{ training }}
{% endfor %}
{% endif %}

---

## 13. Constraints & Assumptions

### Technical Constraints

{% for constraint in technical_constraints %}
- {{ constraint }}
{% endfor %}

### Business Constraints

{% for constraint in business_constraints %}
- {{ constraint }}
{% endfor %}

### Assumptions

{% for assumption in assumptions %}
- {{ assumption }}
{% endfor %}

---

## 14. Risks & Mitigation

| Risk | Probability | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
{% for risk in risks %}
| **{{ risk.description }}** | {{ risk.probability }} | {{ risk.impact }} | {{ risk.mitigation }} |
{% endfor %}

---

## 15. Timeline & Milestones

### Project Phases

{% for phase in project_phases %}
**Phase {{ loop.index }}: {{ phase.name }}** ({{ phase.duration }})
- **Start:** {{ phase.start_date }}
- **End:** {{ phase.end_date }}
- **Deliverables:** {{ phase.deliverables }}
{% endfor %}

### Key Milestones

| Milestone | Target Date | Deliverables | Status |
|-----------|-------------|--------------|--------|
{% for milestone in milestones %}
| **{{ milestone.name }}** | {{ milestone.target_date }} | {{ milestone.deliverables }} | {{ milestone.status }} |
{% endfor %}

---

## 16. Success Criteria & Acceptance

### Launch Criteria

{% for criterion in launch_criteria %}
- [ ] {{ criterion }}
{% endfor %}

### Post-Launch Success Metrics

{% for metric in post_launch_metrics %}
- **{{ metric.name }}**: {{ metric.target }} within {{ metric.timeframe }}
{% endfor %}

### Acceptance Criteria

**Application is accepted when:**
{% for acceptance_criterion in acceptance_criteria %}
- [ ] {{ acceptance_criterion }}
{% endfor %}

---

## 17. Stakeholder Sign-Off

### Review & Approval

{% for stakeholder in stakeholders %}
- [ ] **{{ stakeholder.role }}**: {{ stakeholder.name }}
  - **Approval Criteria:** {{ stakeholder.approval_criteria }}
{% endfor %}

### Requirements Approved

**Approved By:** _________________________
**Date:** _________________________
**Comments:** _________________________

---

## 18. Change Management

### Change Request Process

**Process:** {{ change_request_process }}

**Change Log:**

| Date | Change | Requested By | Approved By | Impact |
|------|--------|--------------|-------------|--------|
{% for change in change_log %}
| {{ change.date }} | {{ change.description }} | {{ change.requester }} | {{ change.approver }} | {{ change.impact }} |
{% endfor %}

---

## Appendix: Glossary

{% for term in glossary %}
**{{ term.term }}**: {{ term.definition }}
{% endfor %}

---

**Template Version:** 1.0 (Vibey Framework)
**Created:** {{ template_creation_date }}
**Last Updated:** {{ last_updated_date }}
