---
id: architecture-review
name: Architecture Review Report
version: 1.0.0
from_agent: architecture-agent
to_agents:
- web-developer
- backend-engineer
purpose: Template for architecture review report
variables:
- name: api_design_notes
  type: string
  required: true
  description: Api Design Notes value
- name: api_versioning_notes
  type: string
  required: true
  description: Api Versioning Notes value
- name: approval_date_1
  type: string
  required: true
  description: Approval Date 1 value
- name: approver_1_name
  type: string
  required: true
  description: Approver 1 Name value
- name: approver_1_role
  type: string
  required: true
  description: Approver 1 Role value
- name: auth_notes
  type: string
  required: true
  description: Auth Notes value
- name: cicd_notes
  type: string
  required: true
  description: Cicd Notes value
- name: code_organization_notes
  type: string
  required: true
  description: Code Organization Notes value
- name: component_architecture_notes
  type: string
  required: true
  description: Component Architecture Notes value
- name: cost_notes
  type: string
  required: true
  description: Cost Notes value
- name: cost_risk_impact
  type: string
  required: true
  description: Cost Risk Impact value
- name: cost_risk_mitigation
  type: string
  required: true
  description: Cost Risk Mitigation value
- name: cost_risk_prob
  type: string
  required: true
  description: Cost Risk Prob value
- name: critical_action_1
  type: string
  required: true
  description: Critical Action 1 value
- name: critical_issue_1_category
  type: string
  required: true
  description: Critical Issue 1 Category value
description: Template for architecture review report
---

# Architecture Review Report

**Document Type:** Handoff Template
**From:** {{ config.roles.architecture_specialist or 'Architecture Specialist' }}
**To:** Team, Stakeholders
**Purpose:** Document architecture assessment and recommendations
**Related Workflow:** Architecture Review Workflow - Step 4

---

## Report Metadata

| Field | Value |
|-------|-------|
| **Review Scope** | {{ review_scope }} |
| **Created By** | {{ reviewer_name }} |
| **Date** | {{ review_date }} |
| **Status** | {{ review_status }} |

---

## 1. Review Scope

### Items Reviewed

{% if config.project.type == 'web-app' %}
- [ ] Sprint plan (feasibility, dependencies, timeline)
- [ ] Application code ({{ config.web_framework.frontend }}, {{ config.web_framework.backend }})
- [ ] API design (endpoints, authentication, data models)
- [ ] Database schema ({{ config.database.type }})
- [ ] Infrastructure (deployment, scaling, monitoring)
- [ ] Security (authentication, authorization, data protection)
- [ ] Performance (caching, optimization, load handling)

{% elif config.project.type == 'api' %}
- [ ] Sprint plan (feasibility, dependencies, timeline)
- [ ] API design (endpoints, versioning, documentation)
- [ ] Code ({{ config.technology_stack.backend.language }}, {{ config.technology_stack.backend.framework }})
- [ ] Data models and validation
- [ ] Authentication and authorization
- [ ] Rate limiting and throttling
- [ ] Infrastructure (deployment, scaling, load balancing)
- [ ] Monitoring and observability

{% elif config.project.type == 'data-platform' %}
- [ ] Sprint plan (feasibility, dependencies, timeline)
- [ ] Data architecture (layers, schemas, pipelines)
- [ ] Code (API clients, transformations, orchestration)
- [ ] Infrastructure ({{ config.infrastructure.iac_tool }}, compute, storage)
- [ ] Data quality and validation
- [ ] Performance and optimization
- [ ] Cost optimization
- [ ] Monitoring and alerting

{% elif config.project.type == 'ml' %}
- [ ] Sprint plan (feasibility, dependencies, timeline)
- [ ] ML pipeline design (training, evaluation, deployment)
- [ ] Code (model code, feature engineering, serving)
- [ ] Data pipeline (sources, transformations, feature store)
- [ ] Model registry and versioning ({{ config.ml_platform.model_registry }})
- [ ] Infrastructure (training clusters, serving endpoints)
- [ ] Performance (training time, inference latency, cost)
- [ ] Monitoring (drift detection, model performance)

{% elif config.project.type == 'infrastructure' %}
- [ ] Sprint plan (feasibility, dependencies, timeline)
- [ ] Infrastructure design ({{ config.infrastructure.iac_tool }}, cloud resources)
- [ ] Security (IAM, secrets, network policies)
- [ ] Scalability and reliability
- [ ] Cost optimization
- [ ] Disaster recovery and backup
- [ ] Monitoring and alerting
- [ ] CI/CD pipeline

{% else %}
- [ ] Sprint plan (feasibility, dependencies, timeline)
- [ ] Code architecture and design
- [ ] Infrastructure and deployment
- [ ] Security and compliance
- [ ] Performance and scalability
- [ ] Testing and quality assurance
{% endif %}

---

## 2. Architecture Assessment Summary

**Overall Score:** {{ overall_score }}
- Excellent: No issues, best practices followed
- Good: Minor improvements possible, no blockers
- Needs Improvement: Several issues to address
- Critical Issues: Must fix before proceeding

**Key Findings:**
- {{ key_finding_1 }}
- {{ key_finding_2 }}
- {{ key_finding_3 }}

---

## 3. Best Practices Validation

{% if config.project.type == 'web-app' %}
| Practice | Status | Notes |
|----------|--------|-------|
| Component architecture (modularity, reusability) | ✅ / ⚠️ / ❌ | {{ component_architecture_notes }} |
| State management ({{ config.web_framework.state_management or 'Context/Redux' }}) | ✅ / ⚠️ / ❌ | {{ state_management_notes }} |
| API design (RESTful, versioning) | ✅ / ⚠️ / ❌ | {{ api_design_notes }} |
| Authentication/Authorization | ✅ / ⚠️ / ❌ | {{ auth_notes }} |
| Error handling | ✅ / ⚠️ / ❌ | {{ error_handling_notes }} |
| Logging and monitoring | ✅ / ⚠️ / ❌ | {{ logging_notes }} |
| Testing (unit, integration, E2E) | ✅ / ⚠️ / ❌ | {{ testing_notes }} |
| Performance (bundle size, lazy loading) | ✅ / ⚠️ / ❌ | {{ performance_notes }} |
| Security (XSS, CSRF, input validation) | ✅ / ⚠️ / ❌ | {{ security_notes }} |
| Database design (normalization, indexes) | ✅ / ⚠️ / ❌ | {{ database_notes }} |

{% elif config.project.type == 'api' %}
| Practice | Status | Notes |
|----------|--------|-------|
| RESTful design principles | ✅ / ⚠️ / ❌ | {{ restful_design_notes }} |
| API versioning | ✅ / ⚠️ / ❌ | {{ api_versioning_notes }} |
| Authentication ({{ config.authentication.method or 'JWT/OAuth2' }}) | ✅ / ⚠️ / ❌ | {{ auth_notes }} |
| Rate limiting | ✅ / ⚠️ / ❌ | {{ rate_limiting_notes }} |
| Input validation | ✅ / ⚠️ / ❌ | {{ validation_notes }} |
| Error handling and status codes | ✅ / ⚠️ / ❌ | {{ error_handling_notes }} |
| Documentation (OpenAPI/Swagger) | ✅ / ⚠️ / ❌ | {{ documentation_notes }} |
| Logging and observability | ✅ / ⚠️ / ❌ | {{ logging_notes }} |
| Testing (unit, integration, contract) | ✅ / ⚠️ / ❌ | {{ testing_notes }} |
| Performance and caching | ✅ / ⚠️ / ❌ | {{ performance_notes }} |

{% elif config.project.type == 'data-platform' %}
| Practice | Status | Notes |
|----------|--------|-------|
| Data architecture (layers, schemas) | ✅ / ⚠️ / ❌ | {{ data_architecture_notes }} |
| Data quality validation | ✅ / ⚠️ / ❌ | {{ data_quality_notes }} |
| Schema management | ✅ / ⚠️ / ❌ | {{ schema_management_notes }} |
| Data partitioning strategy | ✅ / ⚠️ / ❌ | {{ partitioning_notes }} |
| Performance optimization | ✅ / ⚠️ / ❌ | {{ performance_notes }} |
| Secrets management | ✅ / ⚠️ / ❌ | {{ secrets_notes }} |
| Cost optimization | ✅ / ⚠️ / ❌ | {{ cost_notes }} |
| Monitoring and alerting | ✅ / ⚠️ / ❌ | {{ monitoring_notes }} |
| Data lineage and cataloging | ✅ / ⚠️ / ❌ | {{ lineage_notes }} |
| Error handling and retry logic | ✅ / ⚠️ / ❌ | {{ error_handling_notes }} |

{% elif config.project.type == 'ml' %}
| Practice | Status | Notes |
|----------|--------|-------|
| Feature engineering pipeline | ✅ / ⚠️ / ❌ | {{ feature_engineering_notes }} |
| Model versioning ({{ config.ml_platform.model_registry }}) | ✅ / ⚠️ / ❌ | {{ model_versioning_notes }} |
| Experiment tracking ({{ config.ml_platform.experiment_tracking }}) | ✅ / ⚠️ / ❌ | {{ experiment_tracking_notes }} |
{% if config.ml_platform.feature_store %}
| Feature Store usage ({{ config.ml_platform.feature_store }}) | ✅ / ⚠️ / ❌ | {{ feature_store_notes }} |
{% endif %}
| Data validation and drift detection | ✅ / ⚠️ / ❌ | {{ data_validation_notes }} |
| Model evaluation and metrics | ✅ / ⚠️ / ❌ | {{ evaluation_notes }} |
| Training pipeline orchestration | ✅ / ⚠️ / ❌ | {{ orchestration_notes }} |
| Model serving and inference | ✅ / ⚠️ / ❌ | {{ serving_notes }} |
| Monitoring (performance, drift) | ✅ / ⚠️ / ❌ | {{ monitoring_notes }} |
| Cost optimization (compute, storage) | ✅ / ⚠️ / ❌ | {{ cost_notes }} |

{% elif config.project.type == 'infrastructure' %}
| Practice | Status | Notes |
|----------|--------|-------|
| Infrastructure-as-Code ({{ config.infrastructure.iac_tool }}) | ✅ / ⚠️ / ❌ | {{ iac_notes }} |
| Resource organization (tags, naming) | ✅ / ⚠️ / ❌ | {{ organization_notes }} |
| Security (IAM, network policies) | ✅ / ⚠️ / ❌ | {{ security_notes }} |
| Secrets management | ✅ / ⚠️ / ❌ | {{ secrets_notes }} |
| High availability and failover | ✅ / ⚠️ / ❌ | {{ ha_notes }} |
| Disaster recovery and backup | ✅ / ⚠️ / ❌ | {{ dr_notes }} |
| Monitoring and alerting | ✅ / ⚠️ / ❌ | {{ monitoring_notes }} |
| Cost optimization | ✅ / ⚠️ / ❌ | {{ cost_notes }} |
| CI/CD pipeline | ✅ / ⚠️ / ❌ | {{ cicd_notes }} |
| Documentation | ✅ / ⚠️ / ❌ | {{ documentation_notes }} |

{% else %}
| Practice | Status | Notes |
|----------|--------|-------|
| Code organization and modularity | ✅ / ⚠️ / ❌ | {{ code_organization_notes }} |
| Error handling | ✅ / ⚠️ / ❌ | {{ error_handling_notes }} |
| Logging and monitoring | ✅ / ⚠️ / ❌ | {{ logging_notes }} |
| Testing (unit, integration, E2E) | ✅ / ⚠️ / ❌ | {{ testing_notes }} |
| Security | ✅ / ⚠️ / ❌ | {{ security_notes }} |
| Performance | ✅ / ⚠️ / ❌ | {{ performance_notes }} |
| Documentation | ✅ / ⚠️ / ❌ | {{ documentation_notes }} |
{% endif %}

---

## 4. Detailed Findings

### 4.1 Critical Issues (Must Fix)

#### Issue 1: {{ critical_issue_1_title }}
- **Category:** {{ critical_issue_1_category }}
- **Description:** {{ critical_issue_1_description }}
- **Impact:** {{ critical_issue_1_impact }}
- **Recommendation:** {{ critical_issue_1_recommendation }}
- **Effort:** {{ critical_issue_1_effort }}

### 4.2 High Priority (Fix This Week)

#### Issue 1: {{ high_priority_issue_1_title }}
- **Category:** {{ high_priority_issue_1_category }}
- **Description:** {{ high_priority_issue_1_description }}
- **Impact:** {{ high_priority_issue_1_impact }}
- **Recommendation:** {{ high_priority_issue_1_recommendation }}
- **Effort:** {{ high_priority_issue_1_effort }}

### 4.3 Medium Priority (Fix This Month)

#### Issue 1: {{ medium_priority_issue_1_title }}
- **Category:** {{ medium_priority_issue_1_category }}
- **Description:** {{ medium_priority_issue_1_description }}
- **Impact:** {{ medium_priority_issue_1_impact }}
- **Recommendation:** {{ medium_priority_issue_1_recommendation }}
- **Effort:** {{ medium_priority_issue_1_effort }}

### 4.4 Low Priority (Future Enhancement)

#### Issue 1: {{ low_priority_issue_1_title }}
- **Category:** {{ low_priority_issue_1_category }}
- **Description:** {{ low_priority_issue_1_description }}
- **Impact:** {{ low_priority_issue_1_impact }}
- **Recommendation:** {{ low_priority_issue_1_recommendation }}
- **Effort:** {{ low_priority_issue_1_effort }}

---

## 5. Recommendations Summary

### Quick Wins (< 4 hours)
{{ quick_wins_summary }}

### High Impact Improvements
{{ high_impact_improvements_summary }}

### Long-term Strategic Improvements
{{ strategic_improvements_summary }}

---

## 6. Action Items

**Critical (Fix Immediately):**
- [ ] {{ critical_action_1 }} (Owner: {{ owner_1 }}, Due: {{ due_date_1 }})

**High Priority (This Week):**
- [ ] {{ high_priority_action_1 }} (Owner: {{ owner_2 }}, Due: {{ due_date_2 }})

**Medium Priority (This Month):**
- [ ] {{ medium_priority_action_1 }} (Owner: {{ owner_3 }}, Due: {{ due_date_3 }})

**Low Priority (Future):**
- [ ] {{ low_priority_action_1 }} (Owner: {{ owner_4 }}, Due: {{ due_date_4 }})

---

## 7. Risk Assessment

{% if config.project.type == 'data-platform' %}
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Data quality issues | {{ data_quality_risk_prob }} | {{ data_quality_risk_impact }} | {{ data_quality_risk_mitigation }} |
| Performance degradation | {{ performance_risk_prob }} | {{ performance_risk_impact }} | {{ performance_risk_mitigation }} |
| Cost overruns | {{ cost_risk_prob }} | {{ cost_risk_impact }} | {{ cost_risk_mitigation }} |
| Security vulnerabilities | {{ security_risk_prob }} | {{ security_risk_impact }} | {{ security_risk_mitigation }} |

{% elif config.project.type == 'ml' %}
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Model performance degradation | {{ model_perf_risk_prob }} | {{ model_perf_risk_impact }} | {{ model_perf_risk_mitigation }} |
| Data drift | {{ data_drift_risk_prob }} | {{ data_drift_risk_impact }} | {{ data_drift_risk_mitigation }} |
| Training cost overruns | {{ training_cost_risk_prob }} | {{ training_cost_risk_impact }} | {{ training_cost_risk_mitigation }} |
| Inference latency issues | {{ latency_risk_prob }} | {{ latency_risk_impact }} | {{ latency_risk_mitigation }} |

{% elif config.project.type == 'web-app' %}
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Security vulnerabilities | {{ security_risk_prob }} | {{ security_risk_impact }} | {{ security_risk_mitigation }} |
| Performance issues | {{ performance_risk_prob }} | {{ performance_risk_impact }} | {{ performance_risk_mitigation }} |
| Scalability bottlenecks | {{ scalability_risk_prob }} | {{ scalability_risk_impact }} | {{ scalability_risk_mitigation }} |
| Database bottlenecks | {{ database_risk_prob }} | {{ database_risk_impact }} | {{ database_risk_mitigation }} |

{% else %}
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| {{ risk_1_name }} | {{ risk_1_prob }} | {{ risk_1_impact }} | {{ risk_1_mitigation }} |
| {{ risk_2_name }} | {{ risk_2_prob }} | {{ risk_2_impact }} | {{ risk_2_mitigation }} |
| {{ risk_3_name }} | {{ risk_3_prob }} | {{ risk_3_impact }} | {{ risk_3_mitigation }} |
{% endif %}

---

## 8. Approval and Sign-off

**Review Status:** {{ review_approval_status }}

**Approved By:**
- {{ approver_1_name }} ({{ approver_1_role }}) - {{ approval_date_1 }}

**Next Steps:**
{{ next_steps }}

---

**Template Version:** 1.0 (Vibey Framework)
**Created:** {{ template_creation_date }}
**Related Workflows:** Architecture Review Workflow
