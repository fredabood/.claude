# Phase Plan: {{ sprint_version }} - {{ phase_name }}

**Phase:** {{ phase_number }} of {{ total_phases }}
**Sprint:** {{ sprint_version }} - {{ sprint_name }}
**Duration:** {{ phase_duration }}
**Workflow:** {{ assigned_workflow }}

---

## 🎯 Objectives

**Primary Goal:** {{ phase_primary_goal }}

**Key Deliverables:**
{% for deliverable in key_deliverables %}
- {{ deliverable }}
{% endfor %}

---

## 📋 Technical Requirements

### Architecture & Design
{% for requirement in architecture_requirements %}
- {{ requirement }}
{% endfor %}

### Implementation Details
{% for detail in implementation_details %}
- {{ detail }}
{% endfor %}

{% if config.project.type == 'api' %}
### API Specifications
- **Endpoints:** {{ api_endpoints_summary }}
- **Authentication:** {{ api_authentication_method }}
- **Rate Limiting:** {{ api_rate_limiting }}
- **Versioning:** {{ api_versioning_strategy }}

{% elif config.project.type == 'web-app' %}
### UI/UX Requirements
- **Pages/Views:** {{ pages_to_implement }}
- **Components:** {{ components_to_create }}
- **State Management:** {{ state_management_approach }}
- **Responsive Design:** {{ responsive_design_requirements }}

{% elif config.project.type == 'ml' %}
### ML Model Requirements
- **Model Type:** {{ ml_model_type }}
- **Target Metric:** {{ ml_target_metric }}
- **Training Data:** {{ ml_training_data_source }}
- **Deployment:** {{ ml_deployment_type }}

{% elif config.project.type == 'infrastructure' %}
### Infrastructure Requirements
- **{{ config.infrastructure.iac_tool }} Resources:** {{ infrastructure_resources }}
- **Environments:** {{ infrastructure_environments }}
- **Security:** {{ infrastructure_security_requirements }}
- **Cost Estimate:** {{ infrastructure_cost_estimate }}
{% endif %}

### Performance & Quality Targets
{% for target in performance_quality_targets %}
- {{ target }}
{% endfor %}

**Test Coverage:** {{ test_coverage_target }}%

---

## ✅ Success Criteria

**Phase complete when:**
{% for criterion in success_criteria %}
- [ ] {{ criterion }}
{% endfor %}
- [ ] All tests passing ({{ test_coverage_target }}% coverage)
- [ ] Security review completed
- [ ] Documentation updated
- [ ] Code reviewed and merged

---

## 🚨 Key Risks & Mitigations

{% for risk in phase_risks %}
**Risk {{ loop.index }}:** {{ risk.description }}
- **Impact:** {{ risk.impact }}
- **Probability:** {{ risk.probability }}
- **Mitigation:** {{ risk.mitigation }}
- **Contingency:** {{ risk.contingency }}

{% endfor %}

---

## 🔀 Dependencies

### Upstream Dependencies (Must Complete First)
{% for dependency in upstream_dependencies %}
- {{ dependency.description }} ({{ dependency.status }})
{% endfor %}

### Downstream Dependencies (Blocked Until This Completes)
{% for dependency in downstream_dependencies %}
- {{ dependency.description }}
{% endfor %}

### External Dependencies
{% for dependency in external_dependencies %}
- {{ dependency.resource }}: {{ dependency.requirement }} ({{ dependency.availability }})
{% endfor %}

---

## 👥 Team & Roles

**Phase Owner:** {{ phase_owner }}

**Team Members:**
{% for member in team_members %}
- **{{ member.role }}:** {{ member.name }} ({{ member.responsibilities }})
{% endfor %}

**Reviewers:**
{% for reviewer in reviewers %}
- {{ reviewer.role }}: {{ reviewer.name }}
{% endfor %}

---

## 📚 Implementation Guide

**For detailed commands, code snippets, and step-by-step instructions:**

See `{{ implementation_guide_path }}` **Section {{ implementation_section_reference }}**

**Quick Reference:**
- **Configuration files:** {{ config_files_list }}
- **Key scripts:** {{ key_scripts_list }}
{% if config.project.type == 'api' %}
- **API endpoints:** {{ api_endpoints_list }}
{% elif config.project.type == 'web-app' %}
- **Routes:** {{ routes_list }}
- **Components:** {{ components_list }}
{% elif config.project.type == 'ml' %}
- **Notebooks:** {{ notebooks_list }}
- **Training scripts:** {{ training_scripts_list }}
{% elif config.project.type == 'infrastructure' %}
- **{{ config.infrastructure.iac_tool }} files:** {{ iac_files_list }}
- **Deployment scripts:** {{ deployment_scripts_list }}
{% endif %}

---

## 🧪 Testing Strategy

### Test Types Required
{% for test_type in required_test_types %}
- **{{ test_type.name }}:** {{ test_type.description }} ({{ test_type.target_coverage }}% coverage)
{% endfor %}

### Test Scenarios
{% for scenario in test_scenarios %}
- {{ scenario }}
{% endfor %}

### Testing Tools
- **Framework:** {{ config.testing.framework or 'pytest/Jest/JUnit' }}
- **Coverage Tool:** {{ coverage_tool }}
- **CI/CD:** {{ config.ci_cd.platform or 'GitHub Actions' }}

---

## 🔐 Security Considerations

{% for consideration in security_considerations %}
- {{ consideration }}
{% endfor %}

**Security Review Required:** {{ security_review_required }}
**Security Score Target:** {{ config.quality_gates.security_score_minimum or 90 }}/100

---

## 📈 Quality Gates

### Pre-Implementation Gates
{% for gate in pre_implementation_gates %}
- [ ] {{ gate }}
{% endfor %}

### Post-Implementation Gates
{% for gate in post_implementation_gates %}
- [ ] {{ gate }}
{% endfor %}

### Mandatory Reviews (Before Phase Completion)
- [ ] **Security Review** - Score ≥ {{ config.quality_gates.security_score_minimum or 90 }}/100
- [ ] **Code Review** - All PRs approved
- [ ] **Testing Review** - Coverage ≥ {{ test_coverage_target }}%
{% if config.project.type in ['api', 'web-app'] %}
- [ ] **Logging Audit** - Score ≥ {{ config.quality_gates.logging_score_minimum or 80 }}/100
{% endif %}
- [ ] **Documentation Review** - All docs updated

---

## 📊 Progress Tracking

### Milestones

| Milestone | Target Date | Deliverable | Status |
|-----------|-------------|-------------|---------|
{% for milestone in phase_milestones %}
| {{ milestone.name }} | {{ milestone.target_date }} | {{ milestone.deliverable }} | {{ milestone.status }} |
{% endfor %}

### Daily Targets
{{ daily_targets_description }}

---

## 🔗 Related Documentation

**Prerequisites:**
{% for prereq in prerequisite_docs %}
- {{ prereq.title }}: `{{ prereq.path }}`
{% endfor %}

**References:**
{% for reference in reference_docs %}
- {{ reference.title }}: `{{ reference.path }}`
{% endfor %}

**Handoff From:**
- Previous Phase: `{{ previous_phase_plan_path }}`
- {{ handoff_from_role }}: `{{ handoff_from_document_path }}`

**Handoff To:**
- Next Phase: `{{ next_phase_plan_path }}`
- {{ handoff_to_role }}: `{{ handoff_to_document_type }}`

---

## 📝 Notes & Decisions

### Architectural Decisions
{% for decision in architectural_decisions %}
- **{{ decision.title }}:** {{ decision.rationale }}
{% endfor %}

### Trade-offs
{% for tradeoff in tradeoffs %}
- **{{ tradeoff.decision }}:** {{ tradeoff.reasoning }}
{% endfor %}

### Open Questions
{% for question in open_questions %}
- {{ question }} (Owner: {{ question_owner }})
{% endfor %}

---

## 🎯 Definition of Done

**This phase is complete when ALL of the following are true:**

{% for done_criterion in definition_of_done %}
- [ ] {{ done_criterion }}
{% endfor %}

**Sign-off Required From:**
{% for signoff in required_signoffs %}
- [ ] {{ signoff.role }}: {{ signoff.name }}
{% endfor %}

---

**Phase Status:** {{ phase_status }}
**Owner:** {{ phase_owner }}
**Start Date:** {{ phase_start_date }}
**Target Completion:** {{ phase_target_completion }}
**Actual Completion:** {{ phase_actual_completion }}

---

## Template Usage Notes

**What belongs in this document:**
- High-level objectives and goals (WHAT and WHY)
- Technical requirements and architectural decisions
- Integration points and dependencies
- Success criteria (what "done" looks like)
- Key risks and how to mitigate them
- Team assignments and roles
- Quality gates and review requirements

**What does NOT belong here:**
- Full bash commands (put in implementation guide)
- Complete code snippets (put in implementation guide)
- Step-by-step tutorials (put in implementation guide)
- Detailed troubleshooting (put in implementation guide)
- Empty placeholder sections

**Keep phase documents:**
- Focused on WHAT needs to be done and WHY
- Implementation guide covers HOW to do it (with all code, commands, SQL)
- Target: 100-200 lines per phase document
- Reference implementation guide sections for detailed instructions

---

**Template Version:** 1.0 (Vibey Framework)
**Created:** {{ template_creation_date }}
**Last Updated:** {{ last_updated_date }}
