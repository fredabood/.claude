---
id: ml-design
name: ML Design Document
version: 1.0.0
from_agent: architecture-agent
to_agents:
- web-developer
- backend-engineer
purpose: Template for ml design document
variables:
- name: additional_hyperparameters
  type: string
  required: true
  description: Additional Hyperparameters value
- name: algorithm_selection_rationale
  type: string
  required: true
  description: Algorithm Selection Rationale value
- name: api_authentication
  type: string
  required: true
  description: Api Authentication value
- name: api_framework
  type: string
  required: true
  description: Api Framework value
- name: api_rate_limiting
  type: string
  required: true
  description: Api Rate Limiting value
- name: api_sla
  type: string
  required: true
  description: Api Sla value
- name: author_name
  type: string
  required: true
  description: Author Name value
- name: base_model
  type: string
  required: true
  description: Base Model value
- name: baseline_improvement_target
  type: string
  required: true
  description: Baseline Improvement Target value
- name: batch_size
  type: string
  required: true
  description: Batch Size value
- name: bias_detection_plan
  type: string
  required: true
  description: Bias Detection Plan value
- name: business_impact_description
  type: string
  required: true
  description: Business Impact Description value
- name: business_problem_description
  type: string
  required: true
  description: Business Problem Description value
- name: creation_date
  type: string
  required: true
  description: Creation Date value
- name: criterion
  type: string
  required: true
  description: Criterion value
description: Template for ml design document
---

# ML Design Document: {{ ml_use_case_name }}

**Document Type:** Handoff Template
**From:** {{ config.roles.ml_engineer or 'ML Engineer' }}
**To:** Team Stakeholders, {{ next_role }}
**Purpose:** Document ML solution design before implementation
**Related Workflow:** ML Model Development Workflow - Step 2

---

## Document Metadata

| Field | Value |
|-------|-------|
| **ML Use Case** | {{ ml_use_case_name }} |
| **Created By** | {{ author_name }} |
| **Date** | {{ creation_date }} |
| **Status** | {{ document_status }} |
| **Reviewers** | {{ reviewers_list }} |
| **Version** | {{ version_number }} |

---

## 1. Problem Statement & ML Objective

### Business Problem
{{ business_problem_description }}

### ML Objective
{{ ml_objective_description }}

### Success Criteria
{{ success_criteria_description }}

**Metrics:**
- **Primary Metric:** {{ primary_metric }} {{ primary_metric_target }}
- **Secondary Metrics:** {{ secondary_metrics_list }}
- **Business Impact:** {{ business_impact_description }}
- **Deployment Target:** {{ deployment_target_date }}

---

## 2. ML Type & Methodology

### ML Problem Type
- [ ] **Classification** - Predict categorical outcome
- [ ] **Regression** - Predict continuous value
- [ ] **Clustering** - Group similar items
- [ ] **Forecasting** - Predict time-series
- [ ] **Recommendation** - Suggest items
- [ ] **Anomaly Detection** - Identify outliers
- [ ] **NLP** - Natural language processing
- [ ] **Computer Vision** - Image/video analysis
- [ ] **Reinforcement Learning** - Sequential decision making

**Selected Type:** {{ selected_ml_type }}

### Target Variable
**Variable Name:** `{{ target_variable_name }}`
**Data Type:** {{ target_variable_type }}
**Range:** {{ target_variable_range }}
**Distribution:** {{ target_variable_distribution }}

---

## 3. Data Requirements

### Data Sources

| Data Source | Purpose | Key Fields | Granularity |
|-------------|---------|------------|-------------|
{% for source in data_sources %}
| {{ source.name }} | {{ source.purpose }} | {{ source.key_fields }} | {{ source.granularity }} |
{% endfor %}

**Data Availability Check:**
- [ ] All required data sources accessible
- [ ] Sufficient historical data (minimum {{ minimum_data_period }})
- [ ] Data quality meets requirements ({{ data_quality_threshold }}% completeness)

**Missing Data:**
{{ missing_data_description }}

### Training Dataset Specification
- **Time Period:** {{ training_time_period }}
- **Geographic/Domain Scope:** {{ dataset_scope }}
- **Filters/Exclusions:** {{ dataset_filters }}
- **Expected Size:** {{ expected_dataset_size }}

---

## 4. Feature Engineering Plan

### Feature Categories

{% for category in feature_categories %}
**{{ loop.index }}. {{ category.name }}**
{% for feature in category.features %}
- `{{ feature.name }}` - {{ feature.description }}
{% endfor %}

{% endfor %}

{% if config.ml_platform.feature_store %}
### Feature Store Design
**Feature Store:** {{ config.ml_platform.feature_store }}
**Feature Table:** `{{ feature_table_name }}`
**Primary Key:** `{{ feature_primary_key }}`
**Online Store:** {{ feature_online_store_enabled }}
**Offline Store:** {{ feature_offline_store_enabled }}
**Update Frequency:** {{ feature_update_frequency }}

**Feature Metadata:**
- All features registered with descriptions
- Lineage tracked to source data
- Feature validation rules defined (min/max, nullability)
{% endif %}

---

## 5. Model Architecture & Algorithm Selection

### Algorithm Candidates

| Algorithm | Pros | Cons | Priority |
|-----------|------|------|----------|
{% for algorithm in algorithm_candidates %}
| **{{ algorithm.name }}** | {{ algorithm.pros }} | {{ algorithm.cons }} | {{ algorithm.priority }} |
{% endfor %}

**Selected Primary Algorithm:** {{ selected_algorithm }}

**Rationale:**
{{ algorithm_selection_rationale }}

### Model Architecture Specifics

{% if selected_algorithm in ['xgboost', 'lightgbm', 'catboost', 'gradient_boosting'] %}
**For {{ selected_algorithm }}:**
- **Objective:** `{{ model_objective }}`
- **Evaluation Metric:** {{ model_evaluation_metrics }}
- **Initial Hyperparameters:**
  - `max_depth`: {{ max_depth_range }}
  - `learning_rate`: {{ learning_rate_range }}
  - `n_estimators`: {{ n_estimators_range }}
  - {{ additional_hyperparameters }}

{% elif selected_algorithm in ['neural_network', 'deep_learning'] %}
**For Neural Network:**
- **Architecture:** {{ nn_architecture }}
- **Layers:** {{ nn_layers_description }}
- **Activation Functions:** {{ nn_activations }}
- **Optimizer:** {{ nn_optimizer }}
- **Loss Function:** {{ nn_loss_function }}
- **Regularization:** {{ nn_regularization }}

{% elif selected_algorithm in ['random_forest', 'decision_tree'] %}
**For Tree-Based Model:**
- **n_estimators:** {{ n_estimators }}
- **max_depth:** {{ max_depth }}
- **min_samples_split:** {{ min_samples_split }}
- **criterion:** {{ criterion }}

{% elif selected_algorithm in ['linear_regression', 'logistic_regression'] %}
**For Linear Model:**
- **Regularization:** {{ regularization_type }}
- **Alpha:** {{ regularization_alpha }}
- **Solver:** {{ solver }}

{% elif selected_algorithm in ['transformers', 'bert', 'gpt'] %}
**For Transformer Model:**
- **Base Model:** {{ base_model }}
- **Fine-tuning Strategy:** {{ finetuning_strategy }}
- **Sequence Length:** {{ sequence_length }}
- **Batch Size:** {{ batch_size }}

{% endif %}

---

## 6. Hyperparameter Tuning Strategy

### Tuning Approach
- [ ] **Manual Tuning** - Iterative parameter adjustment
- [ ] **Grid Search** - Exhaustive search over parameter grid
- [ ] **Random Search** - Random sampling of parameters
- [ ] **Bayesian Optimization** - Smart parameter search (Hyperopt, Optuna)
- [ ] **AutoML** - Automated ML platform

**Selected:** {{ tuning_approach }}

### Parameters to Tune

| Parameter | Search Space | Rationale |
|-----------|--------------|-----------|
{% for param in tuning_parameters %}
| `{{ param.name }}` | {{ param.search_space }} | {{ param.rationale }} |
{% endfor %}

**Tuning Configuration:**
- **Max Evaluations:** {{ max_tuning_evaluations }}
- **Parallelism:** {{ tuning_parallelism }}
- **Early Stopping:** {{ tuning_early_stopping }}

---

## 7. Cross-Validation Strategy

### Validation Approach
- [ ] **Time-Based Split** - Train on older data, validate on recent
- [ ] **K-Fold Cross-Validation** - Random K-fold splits
- [ ] **Stratified K-Fold** - Balanced splits for classification
- [ ] **Group K-Fold** - Grouped splits (e.g., by user/entity)
- [ ] **Leave-One-Out** - Each sample as validation once

**Selected:** {{ validation_approach }}

### Split Strategy
- **Training Set:** {{ training_set_description }}
- **Validation Set:** {{ validation_set_description }}
- **Test Set:** {{ test_set_description }}

**Rationale:** {{ split_strategy_rationale }}

---

## 8. Evaluation Metrics

### Primary Metrics
{% for metric in primary_metrics %}
{{ loop.index }}. **{{ metric.name }}** - Target: {{ metric.target }}
   - Formula: `{{ metric.formula }}`
   - Interpretability: {{ metric.interpretation }}

{% endfor %}

### Secondary Metrics
{% for metric in secondary_metrics %}
- **{{ metric.name }}** - {{ metric.description }}
{% endfor %}

### Baseline Comparison
- **Naive Baseline:** {{ naive_baseline_description }}
- **Simple Baseline:** {{ simple_baseline_description }}
- **Target:** {{ baseline_improvement_target }}

---

## 9. Feature Importance & Interpretability

### Feature Importance Analysis
- **SHAP Values:** {{ shap_analysis_plan }}
- **Permutation Importance:** {{ permutation_importance_plan }}
- **Feature Contribution:** {{ feature_contribution_plan }}

### Interpretability Requirements
{{ interpretability_requirements }}

---

## 10. Deployment Strategy

### Inference Type
- [ ] **Batch Inference** - Scheduled batch scoring
- [ ] **Real-Time Inference** - On-demand predictions via API
- [ ] **Streaming Inference** - Continuous scoring on streaming data
- [ ] **Edge Inference** - On-device predictions

**Selected:** {{ inference_type }}

### Deployment Plan
- **Frequency:** {{ deployment_frequency }}
- **Input:** {{ deployment_input_source }}
- **Output:** {{ deployment_output_destination }}
- **Latency Requirement:** {{ latency_requirement }}
- **Throughput:** {{ throughput_requirement }}

### Model Serving Configuration
**ML Platform:** {{ config.ml_platform.experiment_tracking }}
{% if config.ml_platform.model_registry %}
**Model Registry:** {{ config.ml_platform.model_registry }}
{% endif %}
**Serving Framework:** {{ serving_framework }}
**Deployment Target:** {{ deployment_target }}

{% if inference_type == 'real_time' %}
**API Configuration:**
- **Framework:** {{ api_framework }}
- **Authentication:** {{ api_authentication }}
- **Rate Limiting:** {{ api_rate_limiting }}
- **SLA:** {{ api_sla }}
{% endif %}

### Monitoring & Retraining
- **Performance Monitoring:** {{ performance_monitoring_plan }}
- **Feature Drift:** {{ feature_drift_monitoring }}
- **Retraining Trigger:** {{ retraining_trigger_conditions }}
- **Retraining Data:** {{ retraining_data_strategy }}

---

## 11. Success Criteria & Definition of Done

### Model Performance
{% for criterion in model_performance_criteria %}
- [ ] {{ criterion }}
{% endfor %}

### Model Quality
{% for criterion in model_quality_criteria %}
- [ ] {{ criterion }}
{% endfor %}

### Deployment Readiness
{% for criterion in deployment_readiness_criteria %}
- [ ] {{ criterion }}
{% endfor %}

### Production Validation
{% for criterion in production_validation_criteria %}
- [ ] {{ criterion }}
{% endfor %}

---

## 12. Timeline & Milestones

| Milestone | Deliverable | Owner | Target Date | Status |
|-----------|------------|-------|-------------|---------|
{% for milestone in ml_milestones %}
| {{ milestone.name }} | {{ milestone.deliverable }} | {{ milestone.owner }} | {{ milestone.target_date }} | [ ] |
{% endfor %}

---

## 13. Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
{% for risk in ml_risks %}
| {{ risk.description }} | {{ risk.probability }} | {{ risk.impact }} | {{ risk.mitigation }} |
{% endfor %}

---

## 14. Computational Requirements

### Training Resources
- **Compute Type:** {{ training_compute_type }}
- **Instance Type:** {{ training_instance_type }}
- **GPU Requirements:** {{ gpu_requirements }}
- **Estimated Training Time:** {{ estimated_training_time }}
- **Estimated Cost:** {{ estimated_training_cost }}

### Inference Resources
- **Compute Type:** {{ inference_compute_type }}
- **Instance Type:** {{ inference_instance_type }}
- **Scaling Strategy:** {{ scaling_strategy }}
- **Estimated Monthly Cost:** {{ estimated_monthly_inference_cost }}

---

## 15. Ethical Considerations & Bias Analysis

### Fairness Analysis
{{ fairness_analysis_plan }}

### Bias Detection
{{ bias_detection_plan }}

### Privacy & Compliance
{{ privacy_compliance_considerations }}

### Explainability Requirements
{{ explainability_requirements }}

---

## 16. Next Steps

**After Design Approval:**
{% for step in next_steps %}
{{ loop.index }}. {{ step }}
{% endfor %}

**Approval Required From:**
{% for approver in required_approvers %}
- [ ] {{ approver.role }}: {{ approver.name }}
{% endfor %}

---

## Appendix: Related Documents

**Training Data Specification:** `{{ training_data_spec_path }}`
**Feature Engineering Notebook:** `{{ feature_engineering_notebook_path }}`
**Model Training Code:** `{{ model_training_code_path }}`
**Evaluation Report:** `{{ evaluation_report_path }}`
**Deployment Guide:** `{{ deployment_guide_path }}`

---

**Template Version:** 1.0 (Vibey Framework)
**Created:** {{ template_creation_date }}
**Last Updated:** {{ last_updated_date }}
