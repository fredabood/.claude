---
id: performance-optimization-report
name: Performance Optimization Report
version: 1.0.0
from_agent: performance-engineer
to_agents:
- web-developer
- documentation-engineer
purpose: Template for performance optimization report
variables:
- name: analysis_date
  type: string
  required: true
  description: Analysis Date value
- name: annual_benefit
  type: string
  required: true
  description: Annual Benefit value
- name: annual_savings
  type: string
  required: true
  description: Annual Savings value
- name: api_calls_count
  type: string
  required: true
  description: Api Calls Count value
- name: api_endpoint
  type: string
  required: true
  description: Api Endpoint value
- name: api_load_time
  type: string
  required: true
  description: Api Load Time value
- name: api_requests_count
  type: string
  required: true
  description: Api Requests Count value
- name: apm_tool_url
  type: string
  required: true
  description: Apm Tool Url value
- name: author_name
  type: string
  required: true
  description: Author Name value
- name: backward_pass_duration
  type: string
  required: true
  description: Backward Pass Duration value
- name: backward_pass_percentage
  type: string
  required: true
  description: Backward Pass Percentage value
- name: backward_pass_status
  type: string
  required: true
  description: Backward Pass Status value
- name: batch_size
  type: string
  required: true
  description: Batch Size value
- name: batch_size_recommendation
  type: string
  required: true
  description: Batch Size Recommendation value
- name: benchmark_after_expected
  type: string
  required: true
  description: Benchmark After Expected value
description: Template for performance optimization report
---

# Performance Optimization Report: {{ target_component }}

**Document Type:** Handoff Template
**From:** {{ config.roles.performance_engineer or 'Performance Engineer' }}
**To:** {{ config.roles.engineering_team or 'Engineering Team, Stakeholders' }}
**Purpose:** Document performance analysis and optimization recommendations
**Related Workflow:** Performance Optimization Workflow - Analysis Phase

---

## Document Metadata

| Field | Value |
|-------|-------|
| **Target Component** | {{ target_component }} |
| **Component Type** | {{ component_type }} |
| **Created By** | {{ author_name }} |
| **Date** | {{ analysis_date }} |
| **Project Type** | {{ config.project.type or 'web-app/API/data-platform/ML' }} |
| **Status** | {{ report_status }} |

---

## 1. Executive Summary

### Performance Issue Summary

{{ performance_issue_summary }}

**Example ({{ config.project.type }}):**
{% if config.project.type == 'data-platform' %}
> The daily ETL pipeline takes 90 minutes to complete, exceeding the 30-minute SLA by 3×. Analysis shows excessive shuffle operations and small file problems. Estimated cost savings: $990/month with proposed optimizations.

{% elif config.project.type == 'api' %}
> The /search endpoint has P95 latency of 3.2 seconds, exceeding the 500ms SLA by 6.4×. Analysis shows N+1 query problems and missing database indexes. Expected improvement: P95 latency reduced to 380ms (88% faster).

{% elif config.project.type == 'web-app' %}
> The dashboard page takes 8.5 seconds to render, exceeding the 2-second target by 4.25×. Analysis shows inefficient React re-renders and large bundle size. Expected improvement: First Contentful Paint reduced to 1.2 seconds (86% faster).

{% elif config.project.type == 'ml' %}
> Model training takes 6 hours per run, exceeding the 2-hour target by 3×. Analysis shows inefficient data loading and lack of distributed training. Expected improvement: Training time reduced to 1.8 hours (70% faster).
{% endif %}

### Current vs Target Metrics

| Metric | Current | Target | Gap |
|--------|---------|--------|-----|
{% for metric in performance_metrics %}
| **{{ metric.name }}** | {{ metric.current }} | {{ metric.target }} | {{ metric.gap }} |
{% endfor %}

### Recommendation Priority

- [ ] **🔴 CRITICAL** - Production incident, immediate action required
- [ ] **🟡 HIGH** - SLA violation, optimize within 1 week
- [ ] **🟢 MEDIUM** - Cost optimization opportunity, optimize within 1 month
- [ ] **⚪ LOW** - Nice-to-have, optimize when convenient

**Selected:** {{ priority_level }}

---

## 2. Component Analysis

### Component Overview

{% if config.project.type == 'data-platform' %}
| Attribute | Value |
|-----------|-------|
| **Pipeline/Job Name** | {{ pipeline_name }} |
| **Schedule** | {{ schedule }} |
| **Platform** | {{ config.cloud_provider or 'Databricks/EMR/Dataproc/Synapse' }} |
| **Cluster/Compute** | {{ cluster_config }} |
| **Runtime** | {{ runtime_version }} |
| **Data Volume** | {{ data_volume }} |
| **Execution Frequency** | {{ execution_frequency }} |

{% elif config.project.type == 'api' %}
| Attribute | Value |
|-----------|-------|
| **API Endpoint** | {{ api_endpoint }} |
| **Request Rate** | {{ request_rate }} requests/sec |
| **Framework** | {{ config.web_framework.backend or 'FastAPI/Express/Spring Boot' }} |
| **Database** | {{ config.technology_stack.database or 'PostgreSQL/MySQL/MongoDB' }} |
| **Caching** | {{ caching_strategy or 'Redis/Memcached/None' }} |
| **Load Balancer** | {{ load_balancer or 'ALB/NGINX/None' }} |

{% elif config.project.type == 'web-app' %}
| Attribute | Value |
|-----------|-------|
| **Page/Component** | {{ page_or_component }} |
| **Framework** | {{ config.web_framework.frontend or 'React/Vue/Angular' }} |
| **Bundle Size** | {{ bundle_size }} |
| **Page Weight** | {{ page_weight }} |
| **API Calls** | {{ api_calls_count }} |
| **User Traffic** | {{ user_traffic }} users/day |

{% elif config.project.type == 'ml' %}
| Attribute | Value |
|-----------|-------|
| **Model Name** | {{ model_name }} |
| **Training Data** | {{ training_data_size }} |
| **Model Type** | {{ model_type }} |
| **Framework** | {{ ml_framework or 'TensorFlow/PyTorch/XGBoost' }} |
| **Compute** | {{ compute_config }} |
| **Distributed Training** | {{ distributed_training or 'Yes/No' }} |
{% endif %}

### Current Performance Metrics

| Metric | Value | Status |
|--------|-------|--------|
{% for metric in current_metrics %}
| **{{ metric.name }}** | {{ metric.value }} | {{ metric.status }} |
{% endfor %}

---

## 3. Bottlenecks Identified

{% for bottleneck in bottlenecks %}
### {{ bottleneck.category }}: {{ bottleneck.title }}

**Severity:** {{ bottleneck.severity }}
**Impact:** {{ bottleneck.impact }}

**Details:**
{{ bottleneck.details_description }}

{% if config.project.type == 'data-platform' %}
**Evidence:**
- {{ bottleneck.evidence_data_platform }}

**Recommendation:**
```{{ config.technology_stack.backend.language }}
{{ bottleneck.recommendation_code_data_platform }}
```

{% elif config.project.type == 'api' %}
**Evidence:**
- {{ bottleneck.evidence_api }}

**Recommendation:**
```{{ config.technology_stack.backend.language }}
{{ bottleneck.recommendation_code_api }}
```

{% elif config.project.type == 'web-app' %}
**Evidence:**
- {{ bottleneck.evidence_web_app }}

**Recommendation:**
```{{ config.web_framework.frontend == 'react' and 'tsx' or 'javascript' }}
{{ bottleneck.recommendation_code_web_app }}
```

{% elif config.project.type == 'ml' %}
**Evidence:**
- {{ bottleneck.evidence_ml }}

**Recommendation:**
```python
{{ bottleneck.recommendation_code_ml }}
```
{% endif %}

**Expected Impact:** {{ bottleneck.expected_impact }}

---

{% endfor %}

## 4. Performance Profiling

{% if config.project.type == 'data-platform' %}
### Spark/Pipeline Stage Analysis

| Stage | Description | Duration | Shuffle Read | Shuffle Write | Bottleneck |
|-------|-------------|----------|--------------|---------------|------------|
{% for stage in pipeline_stages %}
| {{ stage.name }} | {{ stage.description }} | {{ stage.duration }} | {{ stage.shuffle_read }} | {{ stage.shuffle_write }} | {{ stage.bottleneck_status }} |
{% endfor %}

**Total Duration:** {{ total_duration }}

### Task-Level Analysis

| Metric | Min | Median | Max | P75 | P95 |
|--------|-----|--------|-----|-----|-----|
{% for metric in task_metrics %}
| {{ metric.name }} | {{ metric.min }} | {{ metric.median }} | {{ metric.max }} | {{ metric.p75 }} | {{ metric.p95 }} |
{% endfor %}

**Data Skew:** {{ data_skew_analysis }}

{% elif config.project.type == 'api' %}
### Request Breakdown

| Component | Duration | % of Total | Status |
|-----------|----------|------------|--------|
| **Database Query** | {{ db_query_duration }} | {{ db_query_percentage }}% | {{ db_query_status }} |
| **External API Calls** | {{ external_api_duration }} | {{ external_api_percentage }}% | {{ external_api_status }} |
| **Business Logic** | {{ business_logic_duration }} | {{ business_logic_percentage }}% | {{ business_logic_status }} |
| **Serialization** | {{ serialization_duration }} | {{ serialization_percentage }}% | {{ serialization_status }} |
| **Network** | {{ network_duration }} | {{ network_percentage }}% | {{ network_status }} |

**Total Request Time:** {{ total_request_time }}

### Database Query Analysis

{% for query in slow_queries %}
**Query {{ loop.index }}:**
```sql
{{ query.sql }}
```
- **Execution Time:** {{ query.execution_time }}
- **Rows Scanned:** {{ query.rows_scanned }}
- **Rows Returned:** {{ query.rows_returned }}
- **Issue:** {{ query.issue }}
{% endfor %}

{% elif config.project.type == 'web-app' %}
### Page Load Breakdown

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **First Contentful Paint (FCP)** | {{ fcp }} | <1.8s | {{ fcp_status }} |
| **Largest Contentful Paint (LCP)** | {{ lcp }} | <2.5s | {{ lcp_status }} |
| **Time to Interactive (TTI)** | {{ tti }} | <3.8s | {{ tti_status }} |
| **Total Blocking Time (TBT)** | {{ tbt }} | <200ms | {{ tbt_status }} |
| **Cumulative Layout Shift (CLS)** | {{ cls }} | <0.1 | {{ cls_status }} |

### Resource Breakdown

| Resource Type | Size | Count | Load Time |
|---------------|------|-------|-----------|
| **JavaScript** | {{ js_size }} | {{ js_count }} | {{ js_load_time }} |
| **CSS** | {{ css_size }} | {{ css_count }} | {{ css_load_time }} |
| **Images** | {{ images_size }} | {{ images_count }} | {{ images_load_time }} |
| **Fonts** | {{ fonts_size }} | {{ fonts_count }} | {{ fonts_load_time }} |
| **API Requests** | N/A | {{ api_requests_count }} | {{ api_load_time }} |

### React DevTools Profiler

- **Total Components:** {{ total_components }}
- **Re-renders:** {{ rerender_count }} ({{ unnecessary_rerenders }} unnecessary)
- **Slowest Component:** {{ slowest_component }} ({{ slowest_component_time }}ms)

{% elif config.project.type == 'ml' %}
### Training Pipeline Breakdown

| Phase | Duration | % of Total | Status |
|-------|----------|------------|--------|
| **Data Loading** | {{ data_loading_duration }} | {{ data_loading_percentage }}% | {{ data_loading_status }} |
| **Preprocessing** | {{ preprocessing_duration }} | {{ preprocessing_percentage }}% | {{ preprocessing_status }} |
| **Forward Pass** | {{ forward_pass_duration }} | {{ forward_pass_percentage }}% | {{ forward_pass_status }} |
| **Backward Pass** | {{ backward_pass_duration }} | {{ backward_pass_percentage }}% | {{ backward_pass_status }} |
| **Optimizer Step** | {{ optimizer_duration }} | {{ optimizer_percentage }}% | {{ optimizer_status }} |
| **Checkpointing** | {{ checkpoint_duration }} | {{ checkpoint_percentage }}% | {{ checkpoint_status }} |

**Total Training Time:** {{ total_training_time }}

### Resource Utilization

| Resource | Utilization | Target | Status |
|----------|-------------|--------|--------|
| **GPU Utilization** | {{ gpu_util }}% | >80% | {{ gpu_status }} |
| **GPU Memory** | {{ gpu_memory }}% | 70-90% | {{ gpu_memory_status }} |
| **CPU Utilization** | {{ cpu_util }}% | >60% | {{ cpu_status }} |
| **I/O Wait** | {{ io_wait }}% | <10% | {{ io_status }} |
{% endif %}

---

## 5. Platform-Specific Analysis

{% if config.project.type == 'data-platform' %}
### Spark Configuration Review

| Setting | Current | Recommended | Rationale |
|---------|---------|-------------|-----------|
{% for config_item in spark_configs %}
| **{{ config_item.name }}** | {{ config_item.current }} | {{ config_item.recommended }} | {{ config_item.rationale }} |
{% endfor %}

**Recommended Spark Configurations:**
```python
{{ spark_config_code }}
```

### Delta Lake / Data Lake Optimization

| Table | File Count | Avg File Size | Last Optimize | Status |
|-------|------------|---------------|---------------|--------|
{% for table in tables %}
| {{ table.name }} | {{ table.file_count }} | {{ table.avg_file_size }} | {{ table.last_optimize }} | {{ table.status }} |
{% endfor %}

**Recommendations:**
{% for table_rec in table_recommendations %}
- {{ table_rec }}
{% endfor %}

{% elif config.project.type == 'api' %}
### Database Configuration

**Database:** {{ config.technology_stack.database }}

**Indexes:**
{% for index_issue in index_issues %}
- **Table:** `{{ index_issue.table }}`, **Issue:** {{ index_issue.issue }}
  - **Recommendation:** {{ index_issue.recommendation }}
{% endfor %}

**Connection Pool:**
- **Current Size:** {{ connection_pool_current }}
- **Recommended Size:** {{ connection_pool_recommended }}
- **Rationale:** {{ connection_pool_rationale }}

**Query Caching:**
- **Current Strategy:** {{ query_caching_current }}
- **Recommended Strategy:** {{ query_caching_recommended }}

{% elif config.project.type == 'web-app' %}
### Bundle Analysis

**JavaScript Bundles:**
{% for bundle in js_bundles %}
- **{{ bundle.name }}**: {{ bundle.size }} ({{ bundle.gzipped }} gzipped)
  - **Recommendation:** {{ bundle.recommendation }}
{% endfor %}

**Dependencies:**
- **Total:** {{ total_dependencies }} packages
- **Largest:** {{ largest_dependencies }}
- **Duplicates:** {{ duplicate_dependencies }}

**Code Splitting:**
- **Current Strategy:** {{ code_splitting_current }}
- **Recommended Strategy:** {{ code_splitting_recommended }}

**Image Optimization:**
- **Total Images:** {{ total_images }}
- **Unoptimized:** {{ unoptimized_images }}
- **Recommendation:** {{ image_optimization_recommendation }}

{% elif config.project.type == 'ml' %}
### Model Configuration

**Model Size:** {{ model_size }}
**Parameters:** {{ model_parameters }}
**FLOPs per Forward Pass:** {{ model_flops }}

**Data Pipeline:**
- **Prefetching:** {{ data_prefetching_status }}
- **Batch Size:** {{ batch_size }} ({{ batch_size_recommendation }})
- **Num Workers:** {{ num_workers }} ({{ num_workers_recommendation }})
- **Pin Memory:** {{ pin_memory_status }}

**Mixed Precision Training:**
- **Current:** {{ mixed_precision_current }}
- **Recommended:** {{ mixed_precision_recommended }}

**Distributed Training:**
- **Current:** {{ distributed_training_current }}
- **Recommended:** {{ distributed_training_recommended }}
{% endif %}

---

## 6. Optimization Recommendations

### Critical Optimizations (Implement Immediately)

| # | Optimization | Expected Impact | Effort | Priority |
|---|--------------|-----------------|--------|----------|
{% for opt in critical_optimizations %}
| {{ loop.index }} | **{{ opt.name }}** | {{ opt.impact }} | {{ opt.effort }} | {{ opt.priority }} |
{% endfor %}

**Combined Impact:** {{ combined_impact }}

### Quick Wins (Low Effort, High Impact)

{% for quick_win in quick_wins %}
{{ loop.index }}. **{{ quick_win.name }}**: {{ quick_win.description }}
{% endfor %}

### Medium-Priority Optimizations

{% for med_opt in medium_optimizations %}
{{ loop.index }}. **{{ med_opt.name }}**: {{ med_opt.description }}
   - **Impact:** {{ med_opt.impact }}
   - **Effort:** {{ med_opt.effort }}
{% endfor %}

---

## 7. Expected Improvements

### Performance Forecast

| Metric | Current | After Optimization | Improvement |
|--------|---------|-------------------|-------------|
{% for forecast in performance_forecast %}
| **{{ forecast.metric }}** | {{ forecast.current }} | {{ forecast.optimized }} | **{{ forecast.improvement }}** |
{% endfor %}

### Cost Impact

{% if has_cost_impact %}
| Cost Category | Current | After Optimization | Savings |
|---------------|---------|-------------------|---------|
{% for cost in cost_forecast %}
| **{{ cost.category }}** | {{ cost.current }} | {{ cost.optimized }} | {{ cost.savings }} |
{% endfor %}

**Annual Savings:** {{ annual_savings }}
{% endif %}

### ROI Calculation

**Implementation Cost:** {{ implementation_cost }}
**Annual Savings/Benefit:** {{ annual_benefit }}
**ROI:** {{ roi_percentage }}% (payback in {{ payback_period }})

---

## 8. Implementation Plan

### Phase 1: Quick Wins ({{ phase1_timeline }})

{% for task in phase1_tasks %}
- [ ] {{ task.name }} ({{ task.effort }})
{% endfor %}
- [ ] **Test:** {{ phase1_testing }}

### Phase 2: Medium Optimizations ({{ phase2_timeline }})

{% for task in phase2_tasks %}
- [ ] {{ task.name }} ({{ task.effort }})
{% endfor %}
- [ ] **Test:** {{ phase2_testing }}

### Phase 3: Validation & Documentation ({{ phase3_timeline }})

- [ ] Create performance regression tests
- [ ] Document optimizations applied
- [ ] Update configuration docs
- [ ] Benchmark before/after
- [ ] Commit changes and create handoff

**Total Timeline:** {{ total_implementation_timeline }}

---

## 9. Quality Gates & Success Criteria

### Performance Gates

| Gate | Threshold | Current | Target | Pass/Fail |
|------|-----------|---------|--------|-----------|
{% for gate in performance_gates %}
| **{{ gate.name }}** | {{ gate.threshold }} | {{ gate.current }} | {{ gate.target }} | {{ gate.status }} |
{% endfor %}

### Validation Checklist

{% for validation_item in validation_checklist %}
- [ ] {{ validation_item }}
{% endfor %}

---

## 10. Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
{% for risk in risks %}
| **{{ risk.description }}** | {{ risk.probability }} | {{ risk.impact }} | {{ risk.mitigation }} |
{% endfor %}

---

## 11. Monitoring & Regression Prevention

### Performance Metrics to Monitor

{% for metric in monitoring_metrics %}
- **{{ metric.name }}**: {{ metric.description }}
  - **Threshold:** {{ metric.threshold }}
  - **Alert If:** {{ metric.alert_condition }}
{% endfor %}

### Regression Tests

{% for test in regression_tests %}
**{{ test.name }}:**
```{{ config.technology_stack.backend.language }}
{{ test.code }}
```
{% endfor %}

### Performance Dashboard

**Dashboard Location:** {{ dashboard_url }}

**Key Metrics Tracked:**
{% for dashboard_metric in dashboard_metrics %}
- {{ dashboard_metric }}
{% endfor %}

---

## 12. Next Steps

**After Report Review:**
1. {{ config.roles.architecture_specialist or 'Architect' }} reviews recommendations
2. {{ config.roles.performance_engineer or 'Performance Engineer' }} + Code Owners implement optimizations
3. {{ config.roles.test_engineer or 'Test Engineer' }} creates regression tests
4. {{ config.roles.performance_engineer or 'Performance Engineer' }} validates improvements
5. {{ config.roles.documentation_engineer or 'Documentation Engineer' }} updates docs
6. {{ config.roles.git_committer or 'Git Committer' }} commits changes

**Approval Required From:**
{% for approver in approvers %}
- [ ] {{ approver.role }}: {{ approver.approval_criteria }}
{% endfor %}

---

## Appendix: Supporting Evidence

### Performance Profiling Data

{% if config.project.type == 'data-platform' %}
**Spark UI:** {{ spark_ui_url }}
**Query Execution Plans:** {{ query_plans_location }}

{% elif config.project.type == 'api' %}
**APM Tool:** {{ apm_tool_url }}
**Database Query Logs:** {{ query_logs_location }}
**Load Testing Results:** {{ load_testing_results }}

{% elif config.project.type == 'web-app' %}
**Lighthouse Report:** {{ lighthouse_report_url }}
**Chrome DevTools Traces:** {{ devtools_traces_location }}
**Bundle Analyzer:** {{ bundle_analyzer_url }}

{% elif config.project.type == 'ml' %}
**TensorBoard:** {{ tensorboard_url }}
**Profiler Output:** {{ profiler_output_location }}
**Resource Utilization Graphs:** {{ resource_graphs_location }}
{% endif %}

### Screenshots

[Attach relevant screenshots showing:]
{% for screenshot_type in screenshot_types %}
- {{ screenshot_type }}
{% endfor %}

### Benchmark Data

**Before Optimization:**
```
{{ benchmark_before }}
```

**After Optimization (Expected):**
```
{{ benchmark_after_expected }}
```

---

**Template Version:** 1.0 (Vibey Framework)
**Created:** {{ template_creation_date }}
**Last Updated:** {{ last_updated_date }}
