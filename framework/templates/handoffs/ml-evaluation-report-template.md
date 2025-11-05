# ML Evaluation Report: {{ model_name }}

**Document Type:** Handoff Template
**From:** {{ config.roles.ml_engineer or 'ML Engineer / Data Scientist' }}
**To:** {{ config.roles.team or 'Team, Stakeholders, MLOps Engineer' }}
**Purpose:** Document model training results and production readiness
**Related Workflow:** ML Model Development Workflow - Evaluation Phase

---

## Document Metadata

| Field | Value |
|-------|-------|
| **ML Use Case** | {{ ml_use_case }} |
| **Model Name** | {{ model_name }} |
| **Model Type** | {{ model_type }} |
| **Created By** | {{ author_name }} |
| **Date** | {{ evaluation_date }} |
| **ML Platform** | {{ config.ml_platform.experiment_tracking or 'MLflow/W&B/TensorBoard' }} |
| **Experiment ID** | {{ experiment_id }} |
| **Best Run/Model ID** | {{ best_run_id }} |
| **Status** | {{ evaluation_status }} |

---

## 1. Executive Summary

### Model Performance Summary

{{ model_performance_summary }}

**Example ({{ ml_use_case_type }}):**
{% if ml_use_case_type == 'regression' %}
> The {{ algorithm_name }} regression model achieves {{ primary_metric_value }} {{ primary_metric_name }} on the test set, {{ meets_exceeds_target }}. The model explains {{ r2_value }}% of variance and meets all success criteria. Model is ready for production deployment.

{% elif ml_use_case_type == 'binary_classification' %}
> The {{ algorithm_name }} binary classifier achieves {{ accuracy_value }}% accuracy and {{ auc_value }} AUC-ROC on the test set, {{ meets_exceeds_target }}. The model has {{ precision_value }}% precision and {{ recall_value }}% recall at the target threshold. Model is ready for production deployment.

{% elif ml_use_case_type == 'multi_class_classification' %}
> The {{ algorithm_name }} multi-class classifier achieves {{ accuracy_value }}% accuracy and {{ macro_f1_value }} macro-F1 on the test set, {{ meets_exceeds_target }}. Per-class performance is balanced with F1 scores ranging from {{ min_f1 }} to {{ max_f1 }}. Model is ready for production deployment.

{% elif ml_use_case_type == 'object_detection' %}
> The {{ algorithm_name }} object detection model achieves {{ map_value }} mAP@0.5 on the test set, {{ meets_exceeds_target }}. The model detects {{ num_classes }} object classes with {{ fps_value }} FPS inference speed. Model is ready for production deployment.

{% elif ml_use_case_type == 'nlp' %}
> The {{ algorithm_name }} NLP model achieves {{ bleu_or_f1_value }} {{ metric_name }} on the test set, {{ meets_exceeds_target }}. The model handles {{ max_sequence_length }}-token sequences with {{ inference_latency }}ms latency. Model is ready for production deployment.

{% elif ml_use_case_type == 'forecasting' %}
> The {{ algorithm_name }} forecasting model achieves {{ mape_or_rmse_value }} {{ metric_name }} on the test set, {{ meets_exceeds_target }}. The model forecasts {{ forecast_horizon }} time steps ahead with {{ confidence_level }}% prediction intervals. Model is ready for production deployment.
{% endif %}

### Recommendation

- [ ] **✅ DEPLOY TO PRODUCTION** - Model meets all success criteria
- [ ] **⚠️ DEPLOY WITH MONITORING** - Model meets criteria but requires close monitoring
- [ ] **❌ DO NOT DEPLOY** - Model fails to meet requirements
- [ ] **🔄 ITERATE** - Model needs improvement before deployment

**Selected:** {{ deployment_recommendation }}

**Justification:** {{ justification_text }}

---

## 2. Test Set Performance Metrics

### Primary Metrics

{% if ml_use_case_type == 'regression' %}
| Metric | Target | Baseline | Our Model | Status |
|--------|--------|----------|-----------|---------|
| **{{ primary_metric }}** | {{ primary_target }} | {{ baseline_primary }} | **{{ our_model_primary }}** | {{ primary_status }} |
| **RMSE** | {{ rmse_target }} | {{ baseline_rmse }} | **{{ our_model_rmse }}** | {{ rmse_status }} |
| **R²** | {{ r2_target }} | {{ baseline_r2 }} | **{{ our_model_r2 }}** | {{ r2_status }} |
| **MAE** | {{ mae_target }} | {{ baseline_mae }} | **{{ our_model_mae }}** | {{ mae_status }} |

{% elif ml_use_case_type == 'binary_classification' %}
| Metric | Target | Baseline | Our Model | Status |
|--------|--------|----------|-----------|---------|
| **Accuracy** | {{ accuracy_target }} | {{ baseline_accuracy }} | **{{ our_model_accuracy }}** | {{ accuracy_status }} |
| **AUC-ROC** | {{ auc_target }} | {{ baseline_auc }} | **{{ our_model_auc }}** | {{ auc_status }} |
| **Precision** | {{ precision_target }} | {{ baseline_precision }} | **{{ our_model_precision }}** | {{ precision_status }} |
| **Recall** | {{ recall_target }} | {{ baseline_recall }} | **{{ our_model_recall }}** | {{ recall_status }} |
| **F1 Score** | {{ f1_target }} | {{ baseline_f1 }} | **{{ our_model_f1 }}** | {{ f1_status }} |

{% elif ml_use_case_type == 'multi_class_classification' %}
| Metric | Target | Baseline | Our Model | Status |
|--------|--------|----------|-----------|---------|
| **Accuracy** | {{ accuracy_target }} | {{ baseline_accuracy }} | **{{ our_model_accuracy }}** | {{ accuracy_status }} |
| **Macro F1** | {{ macro_f1_target }} | {{ baseline_macro_f1 }} | **{{ our_model_macro_f1 }}** | {{ macro_f1_status }} |
| **Weighted F1** | {{ weighted_f1_target }} | {{ baseline_weighted_f1 }} | **{{ our_model_weighted_f1 }}** | {{ weighted_f1_status }} |
| **Top-3 Accuracy** | {{ top3_target }} | {{ baseline_top3 }} | **{{ our_model_top3 }}** | {{ top3_status }} |

{% elif ml_use_case_type == 'object_detection' %}
| Metric | Target | Baseline | Our Model | Status |
|--------|--------|----------|-----------|---------|
| **mAP@0.5** | {{ map_05_target }} | {{ baseline_map_05 }} | **{{ our_model_map_05 }}** | {{ map_05_status }} |
| **mAP@0.5:0.95** | {{ map_target }} | {{ baseline_map }} | **{{ our_model_map }}** | {{ map_status }} |
| **Precision** | {{ precision_target }} | {{ baseline_precision }} | **{{ our_model_precision }}** | {{ precision_status }} |
| **Recall** | {{ recall_target }} | {{ baseline_recall }} | **{{ our_model_recall }}** | {{ recall_status }} |
| **FPS** | {{ fps_target }} | {{ baseline_fps }} | **{{ our_model_fps }}** | {{ fps_status }} |

{% elif ml_use_case_type == 'nlp' %}
| Metric | Target | Baseline | Our Model | Status |
|--------|--------|----------|-----------|---------|
| **{{ primary_nlp_metric }}** | {{ nlp_metric_target }} | {{ baseline_nlp_metric }} | **{{ our_model_nlp_metric }}** | {{ nlp_metric_status }} |
| **Perplexity** | {{ perplexity_target }} | {{ baseline_perplexity }} | **{{ our_model_perplexity }}** | {{ perplexity_status }} |
| **Latency** | {{ latency_target }} | {{ baseline_latency }} | **{{ our_model_latency }}** | {{ latency_status }} |
{% endif %}

### Secondary Metrics

{% for secondary_metric in secondary_metrics %}
| **{{ secondary_metric.name }}** | {{ secondary_metric.value }} | {{ secondary_metric.interpretation }} |
{% endfor %}

{% if ml_use_case_type in ['regression', 'binary_classification', 'multi_class_classification'] %}
### Prediction Distribution

{% if ml_use_case_type == 'regression' %}
| Error Range | Count | Percentage |
|-------------|-------|------------|
{% for error_bucket in error_buckets %}
| **{{ error_bucket.range }}** | {{ error_bucket.count }} | {{ error_bucket.percentage }}% |
{% endfor %}

{% elif ml_use_case_type in ['binary_classification', 'multi_class_classification'] %}
| Confidence Range | Count | Percentage | Accuracy |
|------------------|-------|------------|----------|
{% for confidence_bucket in confidence_buckets %}
| **{{ confidence_bucket.range }}** | {{ confidence_bucket.count }} | {{ confidence_bucket.percentage }}% | {{ confidence_bucket.accuracy }}% |
{% endfor %}
{% endif %}
{% endif %}

**Interpretation:** {{ prediction_distribution_interpretation }}

---

## 3. Comparison to Baseline Models

### Baseline Models Tested

| Model | {{ primary_metric }} | {{ secondary_metric_1 }} | {{ secondary_metric_2 }} | Training Time |
|-------|----------------------|--------------------------|--------------------------|---------------|
{% for baseline_model in baseline_models %}
| **{{ baseline_model.name }}** | {{ baseline_model.primary }} | {{ baseline_model.secondary1 }} | {{ baseline_model.secondary2 }} | {{ baseline_model.training_time }} |
{% endfor %}

### Improvement Over Baseline

| Comparison | {{ primary_metric }} Improvement | {{ secondary_metric }} Improvement | Interpretation |
|------------|----------------------------------|-------------------------------------|----------------|
{% for comparison in baseline_comparisons %}
| {{ comparison.name }} | **{{ comparison.primary_improvement }}** | **{{ comparison.secondary_improvement }}** | {{ comparison.interpretation }} |
{% endfor %}

**Conclusion:** {{ baseline_comparison_conclusion }}

---

## 4. Hyperparameter Tuning Results

### Tuning Methodology

- **Method:** {{ tuning_method }}
- **Trials/Iterations:** {{ tuning_trials }}
- **Parallelism:** {{ tuning_parallelism }}
- **Duration:** {{ tuning_duration }}
- **Search Space Size:** {{ search_space_size }}

### Best Hyperparameters

| Parameter | Search Space | Best Value | Impact |
|-----------|--------------|------------|--------|
{% for hyperparam in best_hyperparameters %}
| `{{ hyperparam.name }}` | {{ hyperparam.search_space }} | **{{ hyperparam.best_value }}** | {{ hyperparam.impact }} |
{% endfor %}

### Hyperparameter Sensitivity

{% for sensitivity in hyperparam_sensitivity %}
- **{{ sensitivity.importance_level }}**: {{ sensitivity.parameters }} ({{ sensitivity.impact_range }})
{% endfor %}

### Tuning Convergence

- **Trials to Convergence:** {{ trials_to_convergence }}
- **Best {{ primary_metric }}:** {{ best_metric_value }}
- **Overfitting Check:** {{ overfitting_check_description }}

---

## 5. Feature Importance Analysis

{% if has_feature_importance %}
### Top Features

| Rank | Feature Name | Importance | Data Type | Interpretation |
|------|--------------|------------|-----------|----------------|
{% for feature in top_features %}
| {{ loop.index }} | `{{ feature.name }}` | {{ feature.importance }} | {{ feature.data_type }} | {{ feature.interpretation }} |
{% endfor %}

**Top {{ top_n_features }} Features Account for:** {{ top_features_percentage }}% of total model importance

### Feature Categories Contribution

| Category | Importance | Top Features |
|----------|------------|--------------|
{% for category in feature_categories %}
| **{{ category.name }}** | {{ category.importance }}% | {{ category.top_features }} |
{% endfor %}

{% if has_shap_values %}
### SHAP Analysis

**SHAP Summary:** {{ shap_summary_description }}

**SHAP Dependence Plots:** {{ shap_plots_location }}
{% endif %}
{% endif %}

---

## 6. Model Strengths & Weaknesses

### Strengths ✅

{% for strength in model_strengths %}
{{ loop.index }}. **{{ strength.title }}**
   {{ strength.description }}
{% endfor %}

### Weaknesses ⚠️

{% for weakness in model_weaknesses %}
{{ loop.index }}. **{{ weakness.title }}**
   {{ weakness.description }}
   - **Mitigation:** {{ weakness.mitigation }}
{% endfor %}

---

## 7. Error Analysis

{% if ml_use_case_type == 'regression' %}
### Error Distribution by Target Value Range

| Value Range | Count | {{ primary_metric }} | RMSE | Max Error | Issues |
|-------------|-------|----------------------|------|-----------|--------|
{% for error_segment in error_segments %}
| **{{ error_segment.range }}** | {{ error_segment.count }} | {{ error_segment.primary_metric }} | {{ error_segment.rmse }} | {{ error_segment.max_error }} | {{ error_segment.issues }} |
{% endfor %}

{% elif ml_use_case_type in ['binary_classification', 'multi_class_classification'] %}
### Confusion Matrix

{% if ml_use_case_type == 'binary_classification' %}
|  | Predicted Negative | Predicted Positive |
|--|--------------------|--------------------|
| **Actual Negative** | {{ tn }} (TN) | {{ fp }} (FP) |
| **Actual Positive** | {{ fn }} (FN) | {{ tp }} (TP) |

**Key Errors:**
- **False Positives:** {{ fp_count }} ({{ fp_percentage }}%) - {{ fp_description }}
- **False Negatives:** {{ fn_count }} ({{ fn_percentage }}%) - {{ fn_description }}

{% elif ml_use_case_type == 'multi_class_classification' %}
**Full Confusion Matrix:** {{ confusion_matrix_location }}

**Per-Class Performance:**

| Class | Precision | Recall | F1 Score | Support | Issues |
|-------|-----------|--------|----------|---------|--------|
{% for class_perf in per_class_performance %}
| **{{ class_perf.class_name }}** | {{ class_perf.precision }}% | {{ class_perf.recall }}% | {{ class_perf.f1 }} | {{ class_perf.support }} | {{ class_perf.issues }} |
{% endfor %}
{% endif %}

{% elif ml_use_case_type == 'object_detection' %}
### Detection Errors by Category

| Category | Precision | Recall | AP@0.5 | Common Errors |
|----------|-----------|--------|--------|---------------|
{% for category_perf in detection_performance %}
| **{{ category_perf.category }}** | {{ category_perf.precision }}% | {{ category_perf.recall }}% | {{ category_perf.ap }} | {{ category_perf.common_errors }} |
{% endfor %}

**Localization Errors:** {{ localization_errors_description }}
**False Positives:** {{ false_positives_description }}
**Missed Detections:** {{ missed_detections_description }}
{% endif %}

### Error Pattern Analysis

{% for error_pattern in error_patterns %}
**Pattern {{ loop.index }}: {{ error_pattern.title }}**
- **Description:** {{ error_pattern.description }}
- **Frequency:** {{ error_pattern.frequency }}
- **Impact:** {{ error_pattern.impact }}
- **Root Cause:** {{ error_pattern.root_cause }}
{% endfor %}

{% if ml_use_case_type == 'regression' %}
### Residual Analysis

**Residual Plot:** {{ residual_plot_description }}

**Q-Q Plot:** {{ qq_plot_description }}

**Heteroscedasticity:** {{ heteroscedasticity_description }}
{% endif %}

---

## 8. Cross-Validation Results

### {{ cv_method_name }}

{% if cv_method == 'time_series' %}
| Fold | Train Period | Validation Period | Validation {{ primary_metric }} | Validation {{ secondary_metric }} |
|------|--------------|-------------------|----------------------------------|-------------------------------------|
{% for fold in cv_folds %}
| Fold {{ loop.index }} | {{ fold.train_period }} | {{ fold.val_period }} | {{ fold.val_primary }} | {{ fold.val_secondary }} |
{% endfor %}
| **Average** | | | **{{ cv_avg_primary }}** | **{{ cv_avg_secondary }}** |

{% elif cv_method == 'k_fold' %}
| Fold | Validation {{ primary_metric }} | Validation {{ secondary_metric }} |
|------|----------------------------------|-------------------------------------|
{% for fold in cv_folds %}
| Fold {{ loop.index }} | {{ fold.val_primary }} | {{ fold.val_secondary }} |
{% endfor %}
| **Average** | **{{ cv_avg_primary }}** | **{{ cv_avg_secondary }}** |
| **Std Dev** | {{ cv_std_primary }} | {{ cv_std_secondary }} |

{% elif cv_method == 'stratified_k_fold' %}
| Fold | Validation {{ primary_metric }} | Validation {{ secondary_metric }} |
|------|----------------------------------|-------------------------------------|
{% for fold in cv_folds %}
| Fold {{ loop.index }} | {{ fold.val_primary }} | {{ fold.val_secondary }} |
{% endfor %}
| **Average** | **{{ cv_avg_primary }}** | **{{ cv_avg_secondary }}** |
| **Std Dev** | {{ cv_std_primary }} | {{ cv_std_secondary }} |
{% endif %}

**Consistency:** {{ cv_consistency_description }}

{% if has_holdout_validation %}
### {{ holdout_validation_name }}

**Holdout Set:** {{ holdout_description }}

| Metric | In-Sample | Holdout | Difference |
|--------|-----------|---------|------------|
{% for metric in holdout_metrics %}
| {{ metric.name }} | {{ metric.in_sample }} | {{ metric.holdout }} | {{ metric.difference }} |
{% endfor %}

**Conclusion:** {{ holdout_conclusion }}
{% endif %}

---

## 9. Bias & Fairness Analysis

{% if has_fairness_analysis %}
### Performance by {{ fairness_dimension_1 }}

| {{ fairness_dimension_1 }} | {{ primary_metric }} | Bias (Avg Error) | Issues |
|----------------------------|----------------------|------------------|--------|
{% for group in fairness_groups_1 %}
| **{{ group.name }}** | {{ group.primary_metric }} | {{ group.bias }} | {{ group.issues }} |
{% endfor %}

**Concern:** {{ fairness_concern_1 }}

**Mitigation:** {{ fairness_mitigation_1 }}

### Performance by {{ fairness_dimension_2 }}

| {{ fairness_dimension_2 }} | {{ primary_metric }} | Bias | Issues |
|----------------------------|----------------------|------|--------|
{% for group in fairness_groups_2 %}
| **{{ group.name }}** | {{ group.primary_metric }} | {{ group.bias }} | {{ group.issues }} |
{% endfor %}

**Concern:** {{ fairness_concern_2 }}

**Action:** {{ fairness_action_2 }}
{% endif %}

---

## 10. Production Deployment Recommendations

### Deployment Readiness Assessment

| Criteria | Status | Notes |
|----------|--------|-------|
| **Meets Performance Requirements** | {{ meets_performance_status }} | {{ meets_performance_notes }} |
| **Interpretable & Explainable** | {{ interpretable_status }} | {{ interpretable_notes }} |
| **Bias Analysis Complete** | {{ bias_analysis_status }} | {{ bias_analysis_notes }} |
| **Model Registered** | {{ model_registered_status }} | {{ model_registered_notes }} |
| **Monitoring Plan Defined** | {{ monitoring_plan_status }} | {{ monitoring_plan_notes }} |
| **Stakeholder Approval** | {{ stakeholder_approval_status }} | {{ stakeholder_approval_notes }} |

**Overall Readiness:** {{ overall_readiness_status }}

### Recommended Deployment Configuration

**Deployment Type:** {{ deployment_type }}

{% if deployment_type == 'batch' %}
**Batch Configuration:**
- **Schedule:** {{ batch_schedule }}
- **Compute:** {{ batch_compute }}
- **Input:** {{ batch_input }}
- **Output:** {{ batch_output }}
- **Latency SLA:** {{ batch_latency_sla }}

{% elif deployment_type == 'real_time' %}
**Real-Time Configuration:**
- **API Endpoint:** {{ api_endpoint }}
- **Compute:** {{ realtime_compute }}
- **Scaling:** {{ realtime_scaling }}
- **Latency SLA:** {{ realtime_latency_sla }}
- **Throughput:** {{ realtime_throughput }}

{% elif deployment_type == 'streaming' %}
**Streaming Configuration:**
- **Stream Source:** {{ stream_source }}
- **Compute:** {{ streaming_compute }}
- **Latency:** {{ streaming_latency }}
- **Throughput:** {{ streaming_throughput }}

{% elif deployment_type == 'edge' %}
**Edge Configuration:**
- **Target Device:** {{ edge_device }}
- **Model Size:** {{ edge_model_size }}
- **Inference Time:** {{ edge_inference_time }}
- **Power Consumption:** {{ edge_power }}
{% endif %}

### Monitoring & Maintenance Plan

**Performance Monitoring:**
{% for perf_monitor in performance_monitoring %}
- {{ perf_monitor }}
{% endfor %}

**Data Drift Monitoring:**
{% for drift_monitor in drift_monitoring %}
- {{ drift_monitor }}
{% endfor %}

**Model Retraining:**
{% for retrain_trigger in retraining_triggers %}
- **Trigger {{ loop.index }}**: {{ retrain_trigger }}
{% endfor %}
- **Schedule:** {{ retraining_schedule }}

---

## 11. Next Steps & Recommendations

### Immediate Actions (Before Deployment)

{% for action in immediate_actions %}
{{ loop.index }}. **{{ action.name }}** ({{ action.timeline }})
   {{ action.description }}
{% endfor %}

### Future Improvements ({{ next_version }})

{% for improvement in future_improvements %}
{{ loop.index }}. **{{ improvement.name }}**
   {{ improvement.description }}
   - **Expected Impact:** {{ improvement.expected_impact }}
{% endfor %}

---

## 12. {{ config.ml_platform.experiment_tracking or 'ML Platform' }} Experiment Details

### Experiment Metadata

| Field | Value |
|-------|-------|
| **Platform** | {{ config.ml_platform.experiment_tracking or 'MLflow/W&B/TensorBoard' }} |
| **Experiment Name** | {{ experiment_name }} |
| **Experiment ID** | {{ experiment_id }} |
| **Total Runs** | {{ total_runs }} |
| **Best Run ID** | {{ best_run_id }} |
| **Best Run Date** | {{ best_run_date }} |

{% if config.ml_platform.experiment_tracking == 'mlflow' %}
### MLflow Run Artifacts

| Artifact | Location | Description |
|----------|----------|-------------|
| **Model** | `models:/{{ model_name }}/{{ model_stage }}` | {{ model_artifact_description }} |
| **Feature Importance** | `runs:/{{ best_run_id }}/feature_importance.csv` | {{ feature_importance_description }} |
| **Training Metrics** | `runs:/{{ best_run_id }}/metrics.json` | {{ training_metrics_description }} |
| **Plots** | `runs:/{{ best_run_id }}/plots/` | {{ plots_description }} |

{% elif config.ml_platform.experiment_tracking == 'wandb' %}
### Weights & Biases Run Artifacts

| Artifact | Location | Description |
|----------|----------|-------------|
| **Model** | `{{ wandb_project }}/{{ wandb_run_id }}` | {{ model_artifact_description }} |
| **Metrics Dashboard** | {{ wandb_dashboard_url }} | {{ dashboard_description }} |
| **Artifact Collection** | {{ wandb_artifact_url }} | {{ artifacts_description }} |
{% endif %}

### Model Input/Output Schema

**Input Schema:**
```{{ config.technology_stack.backend.language }}
{{ model_input_schema }}
```

**Output Schema:**
```{{ config.technology_stack.backend.language }}
{{ model_output_schema }}
```

---

## 13. Stakeholder Sign-Off

### Required Approvals

{% for approval in required_approvals %}
- [ ] **{{ approval.role }}**: {{ approval.criteria }}
{% endfor %}

### Deployment Approval

**Approved By:** _________________________
**Date:** _________________________
**Comments:** _________________________

---

**Template Version:** 1.0 (Vibey Framework)
**Created:** {{ template_creation_date }}
**Last Updated:** {{ last_updated_date }}
