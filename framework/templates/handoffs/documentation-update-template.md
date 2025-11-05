# Documentation Update Handoff: {{ handoff_title }}

**Document Type:** Handoff Template
**From:** {{ from_agent or 'Triggering Agent' }}
**To:** {{ config.roles.documentation_maintenance_engineer or 'Documentation Maintenance Engineer' }}
**Trigger Type:** {{ trigger_type }}
**Priority:** {{ priority }}
**Date:** {{ handoff_date }}
**Purpose:** Update project documentation following {{ trigger_type }}
**Related Workflow:** Documentation Maintenance Workflow

---

## Handoff Metadata

| Field | Value |
|-------|-------|
| **Trigger Type** | {{ trigger_type }} |
| **Priority** | {{ priority }} |
| **Deadline** | {{ deadline or 'N/A' }} |
| **Documentation Files** | {{ document_count }} file(s) to update |
| **Estimated Duration** | {{ estimated_duration }} |
| **Verification Required** | {{ verification_required }} |

---

## 1. Update Request

### Trigger Information

**Type:** {{ trigger_type }}

{% if trigger_type == 'sprint_completion' %}
**Sprint/Version:** {{ sprint_version }}
**Sprint Name:** {{ sprint_name }}
**Duration:** {{ sprint_duration }}
**Start Date:** {{ sprint_start_date }}
**End Date:** {{ sprint_end_date }}

{% elif trigger_type == 'milestone_completion' %}
**Milestone:** {{ milestone_name }}
**Milestone Type:** {{ milestone_type }}
**Completion Date:** {{ completion_date }}

{% elif trigger_type == 'policy_change' %}
**Policy Name:** {{ policy_name }}
**Policy Type:** {{ policy_type }}
**Effective Date:** {{ effective_date }}

{% elif trigger_type == 'metric_update' %}
**Metric Name:** {{ metric_name }}
**Old Value:** {{ old_value }}
**New Value:** {{ new_value }}
**Change:** {{ change_amount }}

{% elif trigger_type == 'monthly_archival' %}
**Archive Date:** {{ archive_date }}
**Items to Archive:** {{ archive_count }}

{% elif trigger_type == 'manual' %}
**Requested By:** {{ requested_by }}
**Reason:** {{ update_reason }}
{% endif %}

---

## 2. Input Data

{% if trigger_type == 'sprint_completion' %}
### Sprint Completion Data

**Version:** {{ sprint_version }}
**Sprint Name:** {{ sprint_name }}
**Duration:** {{ sprint_duration }}
**Start Date:** {{ sprint_start_date }}
**End Date:** {{ sprint_end_date }}

**Deliverables:**
{% for deliverable in deliverables %}
- {{ deliverable }}
{% endfor %}

**Key Achievement:** {{ key_achievement }}

{% if config.project.type in ['web-app', 'api', 'data-platform'] %}
**Quality Metrics Impact:**
{% if quality_metrics.test_coverage %}
- **Test Coverage:** {{ quality_metrics.old_coverage }}% → {{ quality_metrics.new_coverage }}% ({{ quality_metrics.coverage_change }})
- **Tests Added:** {{ quality_metrics.tests_added }} new tests
{% endif %}
{% if quality_metrics.code_quality %}
- **Code Quality Score:** {{ quality_metrics.old_score }}/100 → {{ quality_metrics.new_score }}/100
{% endif %}
{% if quality_metrics.performance %}
- **Performance:** {{ quality_metrics.performance_improvement }}
{% endif %}
{% endif %}

{% if config.project.type == 'ml' %}
**ML Metrics Impact:**
- **Model Performance:** {{ ml_metrics.old_performance }} → {{ ml_metrics.new_performance }}
- **Training Time:** {{ ml_metrics.training_time_improvement }}
- **Accuracy:** {{ ml_metrics.accuracy_improvement }}
{% endif %}

**Integration Status:** {{ integration_status }}

{% elif trigger_type == 'milestone_completion' %}
### Milestone Completion Data

**Milestone:** {{ milestone_name }}
**Milestone Type:** {{ milestone_type }}
**Completion Date:** {{ completion_date }}

**Achievements:**
{% for achievement in milestone_achievements %}
- {{ achievement }}
{% endfor %}

**Impact:**
{% for impact_item in milestone_impact %}
- {{ impact_item }}
{% endfor %}

{% elif trigger_type == 'policy_change' %}
### Policy Change Data

**Policy Name:** {{ policy_name }}
**Policy Type:** {{ policy_type }}
**Effective Date:** {{ effective_date }}

**Key Requirements:**
{% for requirement in policy_requirements %}
- {{ requirement }}
{% endfor %}

**Impact on Documentation:**
{% for doc_impact in documentation_impact %}
- **{{ doc_impact.file }}**: {{ doc_impact.action }}
{% endfor %}

**Policy Document:** `{{ policy_document_path }}`

{% elif trigger_type == 'metric_update' %}
### Metric Update Data

**Metric Name:** {{ metric_name }}
**Old Value:** {{ old_value }}
**New Value:** {{ new_value }}
**Change:** {{ change_amount }} ({{ change_percentage }})

**Reason for Change:** {{ change_reason }}

**Details:**
{% for detail in metric_details %}
- {{ detail }}
{% endfor %}

**Supporting Evidence:**
{% for evidence in supporting_evidence %}
- {{ evidence.description }}: `{{ evidence.link_or_path }}`
{% endfor %}

{% elif trigger_type == 'monthly_archival' %}
### Monthly Archival Data

**Archive Date:** {{ archive_date }}
**Items to Archive:** {{ archive_count }}

**Items List:**
{% for item in archive_items %}
{{ loop.index }}. **{{ item.title }}** ({{ item.date }}) - {{ item.description }}
{% endfor %}

**Archive Location:** `{{ archive_location }}`

{% elif trigger_type == 'manual' %}
### Manual Update Request

**Requested By:** {{ requested_by }}
**Reason:** {{ update_reason }}

**Specific Changes Requested:**
{% for change in manual_changes %}
- {{ change }}
{% endfor %}

**Context:** {{ manual_context }}
{% endif %}

---

## 3. Documentation Files to Update

{% for file_update in files_to_update %}
### {{ loop.index }}. {{ file_update.file_path }}

**Update Type:** {{ file_update.update_type }}
**Priority:** {{ file_update.priority }}

**Sections to Update:**
{% for section in file_update.sections %}
- **{{ section.name }}** ({{ section.line_range or 'TBD' }})
  - Action: {{ section.action }}
  - New Content: {{ section.new_content or 'See details below' }}
{% endfor %}

**Specific Changes:**
{% for change in file_update.changes %}
- [ ] {{ change }}
{% endfor %}

{% endfor %}

---

## 4. Expected Updates

### Primary Documentation File ({{ primary_doc_file }})

{% for section_update in primary_doc_updates %}
**{{ section_update.section_name }}:**
{% for update_item in section_update.updates %}
- [ ] {{ update_item }}
{% endfor %}

{% endfor %}

### Related Documentation Files

{% for related_file in related_doc_updates %}
**{{ related_file.file_path }}:**
{% for update_item in related_file.updates %}
- [ ] {{ update_item }}
{% endfor %}

{% endfor %}

---

## 5. Version Control

### Git Commit Information

**Commit Message:**
```
{{ commit_message_prefix }}: {{ commit_message_subject }}

{{ commit_message_body }}
```

**Files to Commit:**
{% for file_to_commit in files_to_commit %}
- `{{ file_to_commit }}`
{% endfor %}

**Branch Strategy:** {{ branch_strategy or 'main' }}

---

## 6. Verification Checklist

**Pre-Update Verification:**
{% for precheck in pre_update_checks %}
- [ ] {{ precheck }}
{% endfor %}

**Post-Update Verification:**
{% for postcheck in post_update_checks %}
- [ ] {{ postcheck }}
{% endfor %}

**Quality Checks:**
{% if size_limit %}
- [ ] Size check: {{ primary_doc_file }} < {{ size_limit }} lines
{% endif %}
{% if format_check %}
- [ ] Format check: Markdown properly formatted (no broken tables, correct headings)
{% endif %}
{% if link_check %}
- [ ] Link check: No broken internal/external references
{% endif %}
{% if accuracy_check %}
- [ ] Accuracy check: All data matches source documents
{% endif %}
{% if consistency_check %}
- [ ] Consistency check: Terminology consistent across all docs
{% endif %}

---

## 7. Success Criteria

**This handoff is successful when:**
{% for success_criterion in success_criteria %}
{{ loop.index }}. {{ success_criterion }}
{% endfor %}

**Quality Gates:**
{% for quality_gate in quality_gates %}
- {{ quality_gate }}
{% endfor %}

**Time Constraint:** {{ time_constraint or 'No specific deadline' }}

---

## 8. Reference Links

**Source Documents:**
{% for source_doc in source_documents %}
- {{ source_doc.description }}: `{{ source_doc.path }}`
{% endfor %}

{% if config.project.type in ['web-app', 'api', 'data-platform', 'ml'] %}
**Related Sprint Documents:**
{% if sprint_plan_path %}
- Sprint Plan: `{{ sprint_plan_path }}`
{% endif %}
{% if roadmap_path %}
- Roadmap: `{{ roadmap_path }}`
{% endif %}
{% if implementation_guide_path %}
- Implementation Guide: `{{ implementation_guide_path }}`
{% endif %}
{% endif %}

**Agent/Workflow Documentation:**
{% if documentation_maintenance_agent_path %}
- Documentation Maintenance Agent: `{{ documentation_maintenance_agent_path }}`
{% endif %}
{% if documentation_maintenance_workflow_path %}
- Documentation Maintenance Workflow: `{{ documentation_maintenance_workflow_path }}`
{% endif %}

---

## 9. Automation Notes

{% if automation_enabled %}
**Automation Status:** {{ automation_status }}

**Automated Checks:**
{% for auto_check in automated_checks %}
- {{ auto_check }}
{% endfor %}

**Manual Review Required:** {{ manual_review_required }}
{% else %}
**Automation Status:** Not configured for this project
**Manual Process:** All updates require manual review
{% endif %}

---

## 10. Archival Strategy (if applicable)

{% if trigger_type == 'monthly_archival' %}
**Archive File:** `{{ archive_file_path }}`

**Archival Rules:**
{% for rule in archival_rules %}
- {{ rule }}
{% endfor %}

**Retention Policy:**
- **Primary Documentation:** Keep recent {{ retention_period_primary }} of entries
- **Archive:** Store historical entries older than {{ retention_cutoff }}
- **Archive Structure:** {{ archive_structure_description }}

**Archive Format:**
```markdown
{{ archive_format_example }}
```
{% endif %}

---

## 11. Rollback Plan

**If Update Introduces Issues:**

**Rollback Steps:**
{% for rollback_step in rollback_steps %}
{{ loop.index }}. {{ rollback_step }}
{% endfor %}

**Backup Location:** `{{ backup_location or 'Git history' }}`

**Verification After Rollback:**
{% for verification in rollback_verification %}
- [ ] {{ verification }}
{% endfor %}

---

## 12. Communication Plan

**Stakeholders to Notify:**
{% for stakeholder in stakeholders %}
- **{{ stakeholder.name }}** ({{ stakeholder.role }}) - {{ stakeholder.notification_method }}
{% endfor %}

**Notification Message:**
```
{{ notification_message }}
```

**Notification Timing:** {{ notification_timing }}

---

## 13. Additional Context

{% if additional_notes %}
**Notes:**
{{ additional_notes }}
{% endif %}

{% if special_instructions %}
**Special Instructions:**
{% for instruction in special_instructions %}
- {{ instruction }}
{% endfor %}
{% endif %}

{% if dependencies %}
**Dependencies:**
{% for dependency in dependencies %}
- {{ dependency }}
{% endfor %}
{% endif %}

---

## 14. Example: Sprint Completion Update

{% if config.project.type == 'web-app' %}
```yaml
trigger_type: sprint_completion
sprint_version: v2.5.0
sprint_name: "User Authentication & Authorization"
sprint_duration: "3 weeks"
start_date: 2025-10-15
end_date: 2025-11-05

deliverables:
  - "JWT authentication implementation"
  - "Role-based access control (RBAC)"
  - "OAuth2 provider integration (Google, GitHub)"
  - "User profile management UI"

key_achievement: "Complete authentication system with 99.9% uptime"

quality_metrics:
  old_coverage: 87.5%
  new_coverage: 91.2%
  coverage_change: +3.7%
  tests_added: 42
  old_score: 85
  new_score: 92

integration_status: "Fully integrated and deployed to staging"

primary_doc_file: "README.md"
primary_doc_updates:
  - section_name: "Current Sprint Status"
    updates:
      - "Update version to v2.5.0"
      - "Mark authentication feature as complete"
      - "Update test coverage to 91.2%"

  - section_name: "Recent Changes"
    updates:
      - "Add v2.5.0 authentication sprint summary"
      - "Archive entries older than 30 days"

files_to_update:
  - file_path: "README.md"
    update_type: "sprint_completion"
    priority: "high"
  - file_path: "docs/ROADMAP.md"
    update_type: "milestone_progress"
    priority: "medium"

success_criteria:
  - "All specified sections updated accurately"
  - "Documentation passes format validation"
  - "Changes committed to main branch"
  - "Update completed within 30 minutes"
```

{% elif config.project.type == 'ml' %}
```yaml
trigger_type: sprint_completion
sprint_version: v1.3.0
sprint_name: "Model Performance Optimization"
sprint_duration: "2 weeks"

deliverables:
  - "Hyperparameter tuning (Grid Search + Bayesian Optimization)"
  - "Feature engineering (10 new features)"
  - "Model ensemble (XGBoost + LightGBM + CatBoost)"

key_achievement: "Improved model accuracy from 87.2% to 93.4%"

ml_metrics:
  old_performance: "87.2% accuracy"
  new_performance: "93.4% accuracy"
  training_time_improvement: "30% faster (GPU optimization)"
  accuracy_improvement: "+6.2% accuracy"

primary_doc_file: "README.md"
primary_doc_updates:
  - section_name: "Model Performance"
    updates:
      - "Update accuracy to 93.4%"
      - "Add model ensemble details"
      - "Update training time metrics"
```
{% endif %}

---

## Appendix A: Documentation Structure Reference

**Common Documentation Files:**

{% if config.project.type in ['web-app', 'api'] %}
- `README.md` - Project overview, setup instructions, current status
- `CHANGELOG.md` - Version history and release notes
- `CONTRIBUTING.md` - Contribution guidelines
- `docs/ROADMAP.md` - Product roadmap and sprint planning
- `docs/ARCHITECTURE.md` - System architecture documentation
- `docs/API.md` - API documentation
{% endif %}

{% if config.project.type == 'data-platform' %}
- `README.md` - Platform overview and current status
- `docs/DATA_SOURCES.md` - Data source catalog
- `docs/PIPELINE_ARCHITECTURE.md` - Data pipeline documentation
- `docs/SCHEMA.md` - Data schema documentation
- `docs/ROADMAP.md` - Feature roadmap
{% endif %}

{% if config.project.type == 'ml' %}
- `README.md` - Project overview and model performance
- `docs/MODEL_CARD.md` - Model documentation (performance, training, deployment)
- `docs/EXPERIMENTS.md` - Experiment tracking and results
- `docs/ROADMAP.md` - Research and development roadmap
- `docs/DATA.md` - Training data documentation
{% endif %}

---

## Appendix B: Update Triggers

**Common Trigger Types:**

1. **sprint_completion** - Sprint or release completed
2. **milestone_completion** - Major milestone achieved
3. **policy_change** - New policy or standard adopted
4. **metric_update** - Key metric changed (test coverage, performance, etc.)
5. **monthly_archival** - Regular archival of old content
6. **manual** - Ad-hoc documentation update request
7. **bug_fix** - Critical bug fixed requiring documentation update
8. **security_incident** - Security issue resolved requiring documentation

---

## Appendix C: Automation Configuration

{% if automation_enabled %}
**Trigger Configuration:**
```yaml
documentation_automation:
  enabled: {{ automation_enabled }}
  triggers:
    sprint_completion:
      auto_update: {{ auto_update_sprint_completion }}
      require_review: {{ require_review_sprint_completion }}

    metric_update:
      auto_update: {{ auto_update_metric }}
      require_review: {{ require_review_metric }}

    monthly_archival:
      enabled: {{ auto_archival_enabled }}
      schedule: "{{ archival_schedule }}"
      retention_days: {{ retention_days }}
```

**Automated Workflow:**
1. Trigger detected (e.g., sprint completion)
2. Documentation maintenance agent invoked
3. Changes generated and previewed
4. {% if manual_review_required %}Manual review required{% else %}Changes auto-committed{% endif %}
5. Stakeholders notified
{% endif %}

---

**Handoff Complete:** {{ handoff_date }}
**From:** {{ from_agent or 'Triggering Agent' }}
**To:** {{ config.roles.documentation_maintenance_engineer or 'Documentation Maintenance Engineer' }}

---

**Template Version:** 1.0 (Vibey Framework)
**Created:** {{ template_creation_date }}
**Last Updated:** {{ last_updated_date }}
