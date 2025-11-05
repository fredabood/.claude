# Sprint Plan: {{ sprint_version }}

**Document Type:** Handoff Template
**From:** {{ config.roles.sprint_planning or 'Sprint Planning Agent' }}
**To:** Team, Stakeholders
**Purpose:** Document comprehensive sprint plan with phases, milestones, dependencies
**Related Workflow:** Sprint Planning Workflow

---

## Sprint Metadata

| Field | Value |
|-------|-------|
| **Sprint Version** | {{ sprint_version }} |
| **Sprint Name** | {{ sprint_name }} |
| **Created By** | {{ config.roles.sprint_planning or 'Sprint Planning Agent' }} |
| **Date** | {{ creation_date }} |
| **Status** | {{ sprint_status }} |
| **Duration** | {{ sprint_duration }} |
| **Start Date** | {{ start_date }} |
| **Target End Date** | {{ end_date }} |

---

## 1. Sprint Objectives & Goals

### Primary Objective
{{ primary_objective }}

### Key Results (OKRs)

| Objective | Key Result | Success Metric |
|-----------|------------|----------------|
{% for okr in okrs %}
| {{ okr.objective }} | {{ okr.key_result }} | {{ okr.success_metric }} |
{% endfor %}

### Business Value
{{ business_value_description }}

---

## 2. Sprint Scope

### Features & Requirements

#### Must Have (Critical for Sprint Success)
{% for feature in must_have_features %}
{{ loop.index }}. **{{ feature.name }}**
   - Description: {{ feature.description }}
   - Success Criteria: {{ feature.success_criteria }}
   - Estimated Duration: {{ feature.duration }}
   - Assigned Workflow: {{ feature.workflow }}
   - Assigned Agent/Role: {{ feature.owner }}

{% endfor %}

#### Should Have (High Value, Not Blocking)
{% for feature in should_have_features %}
{{ loop.index }}. **{{ feature.name }}**
   - Description: {{ feature.description }}
   - Success Criteria: {{ feature.success_criteria }}
   - Estimated Duration: {{ feature.duration }}

{% endfor %}

#### Nice to Have (Stretch Goals)
{% for feature in nice_to_have_features %}
{{ loop.index }}. **{{ feature.name }}**
   - Description: {{ feature.description }}

{% endfor %}

### Out of Scope (Explicitly NOT Included)
{% for item in out_of_scope %}
- {{ item.feature }} - {{ item.reason }}
{% endfor %}

---

## 3. Dependency Graph

### Sprint Dependencies

**Upstream Dependencies (must complete before this sprint):**
{% for dependency in upstream_dependencies %}
- {{ dependency.sprint }}: {{ dependency.deliverable }} {{ dependency.status }}
{% endfor %}

**Internal Dependencies (within this sprint):**
```
{{ dependency_diagram }}
```

**Downstream Dependencies (blocked by this sprint):**
{% for dependency in downstream_dependencies %}
- {{ dependency.sprint }}: {{ dependency.feature }} (needs {{ dependency.dependency_reason }})
{% endfor %}

### Dependency Details

| Task | Depends On | Blocks | Type |
|------|------------|--------|------|
{% for dependency in dependency_details %}
| {{ dependency.task }} | {{ dependency.depends_on }} | {{ dependency.blocks }} | {{ dependency.type }} |
{% endfor %}

---

## 4. Sprint Phases & Timeline

### Phase Breakdown

{% for phase in sprint_phases %}
**Phase {{ loop.index }}: {{ phase.name }} ({{ phase.timeline }})**
- **Workflow:** {{ phase.workflow }}
- **Duration:** {{ phase.duration }}
- **Owner:** {{ phase.owner }}
- **Parallelization:** {{ phase.parallelization_note }}
- **Deliverables:**
{% for deliverable in phase.deliverables %}
  - {{ deliverable }}
{% endfor %}

{% endfor %}

### Timeline Visualization

```
{{ timeline_chart }}
```

{% if config.project.type == 'ml' %}
### ML-Specific Milestones
- **Data Collection:** {{ ml_data_collection_timeline }}
- **Feature Engineering:** {{ ml_feature_engineering_timeline }}
- **Model Training:** {{ ml_training_timeline }}
- **Model Evaluation:** {{ ml_evaluation_timeline }}
- **Model Deployment:** {{ ml_deployment_timeline }}
- **Monitoring Setup:** {{ ml_monitoring_timeline }}

{% elif config.project.type == 'infrastructure' %}
### Infrastructure Milestones
- **Design & Planning:** {{ infra_design_timeline }}
- **{{ config.infrastructure.iac_tool }} Development:** {{ infra_development_timeline }}
- **Security Review:** {{ infra_security_timeline }}
- **Staging Deployment:** {{ infra_staging_timeline }}
- **Production Deployment:** {{ infra_production_timeline }}
- **Monitoring Setup:** {{ infra_monitoring_timeline }}

{% elif config.project.type == 'web-app' %}
### Web App Milestones
- **Design & UX:** {{ webapp_design_timeline }}
- **Backend API Development:** {{ webapp_backend_timeline }}
- **Frontend Development:** {{ webapp_frontend_timeline }}
- **Integration & Testing:** {{ webapp_integration_timeline }}
- **Security Hardening:** {{ webapp_security_timeline }}
- **Deployment:** {{ webapp_deployment_timeline }}

{% elif config.project.type == 'api' %}
### API Development Milestones
- **API Design (OpenAPI):** {{ api_design_timeline }}
- **Implementation:** {{ api_implementation_timeline }}
- **Testing (unit, integration, contract):** {{ api_testing_timeline }}
- **Security Review:** {{ api_security_timeline }}
- **Documentation:** {{ api_documentation_timeline }}
- **Deployment:** {{ api_deployment_timeline }}
{% endif %}

---

## 5. Prioritization Scoring

### Scoring Framework

**Priority = (Value × 2) - (Effort + Risk)**

| Feature | Value (1-5) | Effort (1-5) | Risk (1-5) | Priority | Rank |
|---------|-------------|--------------|------------|----------|------|
{% for feature in prioritized_features %}
| {{ feature.name }} | {{ feature.value }} | {{ feature.effort }} | {{ feature.risk }} | {{ feature.priority }} | {{ feature.rank }} |
{% endfor %}

**Rationale:**
{{ prioritization_rationale }}

---

## 6. Resource Allocation

### Team Assignments

| Team Member | Role | Phases Assigned | Utilization |
|-------------|------|-----------------|-------------|
{% for assignment in team_assignments %}
| {{ assignment.name }} | {{ assignment.role }} | {{ assignment.phases }} | {{ assignment.utilization }} |
{% endfor %}

### Resource Constraints
{{ resource_constraints_description }}

{% if external_dependencies %}
### External Dependencies
{% for dependency in external_dependencies %}
- **{{ dependency.name }}:** {{ dependency.description }} (Available: {{ dependency.availability }})
{% endfor %}
{% endif %}

---

## 7. Milestones & Success Criteria

### Sprint Milestones

| Milestone | Target Date | Deliverable | Success Criteria |
|-----------|-------------|-------------|------------------|
{% for milestone in milestones %}
| **{{ milestone.name }}** | {{ milestone.target_date }} | {{ milestone.deliverable }} | {{ milestone.success_criteria }} |
{% endfor %}

### Sprint Success Criteria

**Must Have (Pass/Fail):**
{% for criteria in must_have_success_criteria %}
- [ ] {{ criteria }}
{% endfor %}

**Should Have:**
{% for criteria in should_have_success_criteria %}
- [ ] {{ criteria }}
{% endfor %}

**Nice to Have:**
{% for criteria in nice_to_have_success_criteria %}
- [ ] {{ criteria }}
{% endfor %}

---

## 8. Risks & Mitigation

### Risk Register

| Risk | Probability | Impact | Mitigation Strategy | Owner |
|------|------------|--------|---------------------|-------|
{% for risk in risks %}
| **{{ risk.description }}** | {{ risk.probability }} | {{ risk.impact }} | {{ risk.mitigation }} | {{ risk.owner }} |
{% endfor %}

### Contingency Plans

{% for contingency in contingency_plans %}
**{{ contingency.trigger }}:**
{% for plan in contingency.plans %}
- Plan {{ loop.index }}: {{ plan }}
{% endfor %}

{% endfor %}

{% if config.project.type == 'ml' %}
### ML-Specific Risks
- **Model Performance:** {{ ml_performance_risk_mitigation }}
- **Data Quality:** {{ ml_data_quality_risk_mitigation }}
- **Training Time/Cost:** {{ ml_training_cost_risk_mitigation }}
- **Drift in Production:** {{ ml_drift_risk_mitigation }}

{% elif config.project.type == 'infrastructure' %}
### Infrastructure-Specific Risks
- **Cost Overruns:** {{ infra_cost_risk_mitigation }}
- **Security Vulnerabilities:** {{ infra_security_risk_mitigation }}
- **Deployment Failures:** {{ infra_deployment_risk_mitigation }}
- **Downtime:** {{ infra_downtime_risk_mitigation }}
{% endif %}

---

## 9. Quality Gates

### Mandatory Reviews

Every sprint phase must pass these quality gates:

1. **Security Review**
   - Checklist: {{ security_review_checklist_path }}
   - Score Required: ≥ {{ config.quality_gates.security_score_minimum or 90 }}/100
   - Owner: {{ config.roles.security_reviewer or 'Security Reviewer' }}

2. **Unit Testing**
   - Coverage Required: ≥ {{ config.coding_standards.test_coverage.minimum or 90 }}%
   - All Tests: Must pass
   - Owner: {{ config.roles.test_engineer or 'Test Engineer' }}

3. **Logging Audit**
   - Score Required: ≥ {{ config.quality_gates.logging_score_minimum or 80 }}/100
   - Checklist: {{ logging_audit_checklist_path }}
   - Owner: {{ config.roles.observability_engineer or 'Observability Engineer' }}

4. **Documentation Review**
   - All docs updated: {{ documentation_files_list }}
   - API docs complete: {{ 'Yes' if config.project.type == 'api' else 'N/A' }}
   - Owner: {{ config.roles.documentation_engineer or 'Documentation Engineer' }}

### Phase Gate Criteria

{% for phase in sprint_phases %}
**{{ phase.name }} Gate:**
- [ ] {{ phase.gate_criteria_1 }}
- [ ] {{ phase.gate_criteria_2 }}
- [ ] {{ phase.gate_criteria_3 }}

{% endfor %}

---

## 10. Communication & Reporting

### Sprint Ceremonies

| Ceremony | Frequency | Duration | Attendees |
|----------|-----------|----------|-----------|
| **Sprint Planning** | Start of sprint | {{ sprint_planning_duration }} | {{ sprint_planning_attendees }} |
| **Daily Standup** | Daily | {{ daily_standup_duration }} | {{ daily_standup_attendees }} |
| **Sprint Review** | End of sprint | {{ sprint_review_duration }} | {{ sprint_review_attendees }} |
| **Sprint Retrospective** | End of sprint | {{ retrospective_duration }} | {{ retrospective_attendees }} |
{% if config.project.type == 'ml' %}
| **ML Model Review** | Weekly | 30 min | ML team + stakeholders |
{% endif %}

### Status Reporting

**Weekly Status Update ({{ status_update_day }}):**
- Phase progress (% complete)
- Milestones achieved
- Blockers and risks
- Next week's focus
- Burn-down chart update

**Stakeholder Demo ({{ demo_schedule }}):**
{{ stakeholder_demo_description }}

### Communication Channels

- **Team Chat:** {{ team_chat_channel }}
- **Status Updates:** {{ status_update_location }}
- **Documentation:** {{ documentation_location }}
- **Issue Tracking:** {{ issue_tracker }}

---

## 11. Budget & Cost Estimates

{% if config.project.type == 'infrastructure' or config.project.type == 'ml' %}
### Estimated Costs

| Category | Estimated Cost | Notes |
|----------|----------------|-------|
{% if config.project.type == 'infrastructure' %}
| {{ config.cloud_provider }} Compute | {{ compute_cost_estimate }} | {{ compute_cost_notes }} |
| {{ config.cloud_provider }} Storage | {{ storage_cost_estimate }} | {{ storage_cost_notes }} |
| {{ config.cloud_provider }} Network | {{ network_cost_estimate }} | {{ network_cost_notes }} |
{% elif config.project.type == 'ml' %}
| Training Compute ({{ config.ml_platform.compute or 'GPU' }}) | {{ training_cost_estimate }} | {{ training_cost_notes }} |
| Model Serving | {{ serving_cost_estimate }} | {{ serving_cost_notes }} |
| Feature Store | {{ feature_store_cost_estimate }} | {{ feature_store_cost_notes }} |
| Experiment Tracking ({{ config.ml_platform.experiment_tracking }}) | {{ experiment_tracking_cost }} | {{ experiment_tracking_notes }} |
{% endif %}
| **Total Estimated** | **{{ total_cost_estimate }}** | {{ total_cost_notes }} |

### Cost Monitoring
- Budget Alert Threshold: {{ budget_alert_threshold }}
- Cost Dashboard: {{ cost_dashboard_link }}
- Review Frequency: {{ cost_review_frequency }}
{% endif %}

---

## 12. Testing Strategy

### Test Coverage Goals

| Test Type | Coverage Target | Owner |
|-----------|-----------------|-------|
| Unit Tests | {{ config.coding_standards.test_coverage.minimum or 90 }}% | {{ config.roles.test_engineer or 'Developers' }} |
| Integration Tests | {{ integration_test_coverage_target or '80%' }} | {{ config.roles.test_engineer or 'Test Engineer' }} |
| E2E Tests | {{ e2e_test_coverage_target or 'Critical paths' }} | {{ config.roles.test_engineer or 'QA Team' }} |
{% if config.project.type == 'api' %}
| Contract Tests | {{ contract_test_coverage or '100% of public APIs' }} | API Team |
{% endif %}
{% if config.project.type == 'ml' %}
| Model Tests | {{ ml_test_coverage or 'All models' }} | ML Engineer |
{% endif %}

### Testing Timeline

{{ testing_timeline_description }}

---

## 13. Deployment Plan

### Deployment Strategy

**Approach:** {{ deployment_strategy }}

**Environments:**
{% for env in deployment_environments %}
- **{{ env.name }}:** {{ env.purpose }} (Deployment: {{ env.deployment_schedule }})
{% endfor %}

### Deployment Checklist

See: `{{ deployment_checklist_path }}`

Key milestones:
{% for milestone in deployment_milestones %}
- {{ milestone.name }}: {{ milestone.target_date }}
{% endfor %}

---

## 14. Updated Roadmap Section

### {{ sprint_version }} Roadmap Entry

**Sprint:** {{ sprint_version }} - {{ sprint_name }}
**Status:** {{ roadmap_status }}
**Duration:** {{ sprint_duration }}
**Start:** {{ start_date }}
**End:** {{ end_date }}

**Objectives:**
{% for objective in roadmap_objectives %}
- {{ objective }}
{% endfor %}

**Key Deliverables:**
{% for deliverable in key_deliverables %}
- {{ deliverable }}
{% endfor %}

**Dependencies:**
{% for dependency in roadmap_dependencies %}
- {{ dependency }}
{% endfor %}

**Blocks:**
{% for block in roadmap_blocks %}
- {{ block }}
{% endfor %}

---

## 15. Success Metrics & KPIs

### Performance Metrics

{% if config.project.type == 'ml' %}
| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Model Accuracy ({{ ml_metric_type or 'MAPE/R²' }}) | {{ ml_accuracy_target }} | {{ ml_measurement_method }} |
| Inference Latency | {{ ml_latency_target }} | {{ ml_latency_measurement }} |
| Model Drift | {{ ml_drift_target }} | {{ ml_drift_measurement }} |
| Cost per Prediction | {{ ml_cost_target }} | {{ ml_cost_measurement }} |

{% elif config.project.type == 'api' %}
| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Response Time (p95) | {{ api_response_time_target }} | {{ api_response_time_measurement }} |
| Throughput (req/sec) | {{ api_throughput_target }} | {{ api_throughput_measurement }} |
| Error Rate | {{ api_error_rate_target }} | {{ api_error_rate_measurement }} |
| Availability | {{ api_availability_target }} | {{ api_availability_measurement }} |

{% elif config.project.type == 'web-app' %}
| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Page Load Time | {{ page_load_time_target }} | {{ page_load_measurement }} |
| Time to Interactive | {{ tti_target }} | {{ tti_measurement }} |
| Core Web Vitals | {{ cwv_target }} | {{ cwv_measurement }} |
| User Satisfaction (CSAT) | {{ csat_target }} | {{ csat_measurement }} |

{% elif config.project.type == 'infrastructure' %}
| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Deployment Success Rate | {{ deployment_success_target }} | {{ deployment_success_measurement }} |
| Infrastructure Cost | {{ infra_cost_target }} | {{ infra_cost_measurement }} |
| Uptime/Availability | {{ uptime_target }} | {{ uptime_measurement }} |
| Mean Time to Recovery (MTTR) | {{ mttr_target }} | {{ mttr_measurement }} |
{% endif %}

### Business Metrics

{{ business_metrics_description }}

---

## Appendix: Related Documents

**Implementation Guide:** `{{ implementation_guide_path }}`
**Architecture Design:** `{{ architecture_design_path }}`
**Security Review:** `{{ security_review_path }}`
**Test Plan:** `{{ test_plan_path }}`
**Deployment Checklist:** `{{ deployment_checklist_path }}`

---

**Template Version:** 1.0 (Vibey Framework)
**Created:** {{ template_creation_date }}
**Last Updated:** {{ last_updated_date }}
