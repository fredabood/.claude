# Workflow: ML Model Development

**Workflow ID:** ML Model Development
**Purpose:** End-to-end machine learning model lifecycle from requirements to production deployment
**Duration:** 15-25 days (3-5 weeks)
**Complexity:** High

---

## Overview

This workflow orchestrates the complete ML lifecycle: requirements gathering → design → feature engineering → training → evaluation → deployment → monitoring. It ensures systematic development of production-ready machine learning models with proper governance, monitoring, and documentation.

**Use Cases:**
{% if config.project.type == 'ml' %}- Prediction models (regression, classification)
- Forecasting models (time series)
- Recommendation systems
- Anomaly detection
- Clustering and segmentation{% else %}- Adding ML capabilities to existing applications
- Building intelligent features
- Automated decision-making
- Predictive analytics{% endif %}

**Prerequisites:**
- Training data available or strategy to obtain it
- Business requirements defined
- ML use case validated by stakeholders
{% if config.ml_platform %}- {{ config.ml_platform.experiment_tracking or 'ML platform' }} access configured{% else %}- ML experiment tracking platform configured{% endif %}
{% if config.cloud_provider %}- {{ config.cloud_provider }} resources provisioned{% endif %}

---

## Workflow Steps

### Step 1: Define ML Use Case Requirements (Day 1)

**Agent:** Sprint Planning Agent
**Duration:** 1 day
**Input:** Business problem statement, stakeholder requirements
**Output:** ML requirements document

**Activities:**
- Analyze business problem and define ML objective
- Identify target variable and success metrics
- Define data requirements (features, labels, granularity)
- Specify model constraints (latency, interpretability, fairness)
- Set success criteria and evaluation approach
- Create sprint plan for ML development

**Deliverables:**
- ML requirements document
- Success criteria and KPIs
- Sprint plan with milestones
- Resource requirements

**Handoff:** Pass requirements to ML Engineer

---

### Step 2: Design ML Solution (Days 2-3)

**Agent:** ML Engineer
**Duration:** 2 days
**Input:** ML requirements document
**Output:** ML Design Document

**Activities:**
- Select ML type (classification, regression, clustering, forecasting, etc.)
- Choose model architecture and algorithms
{% if config.ml_platform and config.ml_platform.feature_store %}- Design {{ config.ml_platform.feature_store }} feature store tables{% else %}- Design feature engineering pipeline{% endif %}
- Define hyperparameter tuning strategy
- Plan cross-validation approach
- Specify evaluation metrics
- Design deployment strategy (batch vs real-time)
- Select {% if config.ml_platform %}{{ config.ml_platform.experiment_tracking or 'experiment tracking' }}{% else %}experiment tracking platform{% endif %}

**Deliverables:**
- **ML Design Document** ({% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/ml-design-[use-case].md)
  - Problem formulation and model selection
  - Feature engineering strategy
  {% if config.ml_platform and config.ml_platform.feature_store %}- {{ config.ml_platform.feature_store }} schema{% else %}- Feature pipeline design{% endif %}
  - Model architecture diagram
  - Deployment plan
- Technology stack decisions
  {% if config.ml_platform %}- {{ config.ml_platform.experiment_tracking or 'Experiment tracking' }} setup plan{% endif %}

**Handoff:** Pass ML Design to Data Engineer / ML Engineer (data prep)

---

### Step 3: Ensure Training Data Availability (Days 3-4)

**Agent:** {% if config.project.type == 'data-platform' %}Gold Transformation Engineer{% else %}Data Engineer{% endif %}
**Duration:** 1-2 days
**Input:** ML Design Document (data requirements)
**Output:** Training data ready

**Activities:**
{% if config.project.type == 'data-platform' %}- Verify required Gold layer tables exist
- Create additional aggregations/joins if needed{% else %}- Identify and access data sources
- Create data extraction pipelines{% endif %}
- Validate data quality for ML (completeness, accuracy)
- Create training/validation/test splits
- Document data lineage and transformations
{% if config.database %}- Store prepared data in {{ config.database.type }}{% endif %}

**Deliverables:**
{% if config.project.type == 'data-platform' %}- Gold layer training data tables{% else %}- Training data tables/files{% endif %}
- Data quality report
- Train/validation/test split {% if config.database %}tables{% else %}datasets{% endif %}
- Data documentation and lineage

**Handoff:** Confirm data availability to ML Engineer

---

### Step 4: Feature Engineering {% if config.ml_platform and config.ml_platform.feature_store %}& Feature Store Creation{% endif %} (Days 5-7)

**Agent:** ML Engineer
**Duration:** 3 days
**Input:** Training data, ML Design
**Output:** {% if config.ml_platform and config.ml_platform.feature_store %}Feature Store with{% else %}Dataset with{% endif %} engineered features

**Activities:**
{% if config.ml_platform and config.ml_platform.feature_store %}- Create {{ config.ml_platform.feature_store }} feature store tables
- Register features with metadata{% else %}- Create feature engineering pipelines
- Store features in versioned datasets{% endif %}
- Implement feature engineering pipelines
- Calculate derived features (ratios, lags, aggregations, embeddings)
- Handle missing values and outliers
- Encode categorical variables
- Normalize/standardize features
{% if config.technology_stack and config.technology_stack.backend.language == 'python' %}- Implement feature transformations in Python/scikit-learn{% endif %}
- Validate feature distributions

**Deliverables:**
{% if config.ml_platform and config.ml_platform.feature_store %}- {{ config.ml_platform.feature_store }} feature tables (online and offline){% else %}- Feature datasets (training/validation/test){% endif %}
- Feature engineering {% if config.technology_stack and config.technology_stack.backend.language == 'python' %}notebooks/scripts{% else %}code{% endif %}
- Feature metadata and lineage
- Feature validation tests

**Handoff:** {% if config.ml_platform and config.ml_platform.feature_store %}Feature Store{% else %}Features{% endif %} ready for model training

---

### Step 5: Model Training, Tuning, Evaluation (Days 8-12)

**Agent:** ML Engineer
**Duration:** 5 days
**Input:** {% if config.ml_platform and config.ml_platform.feature_store %}Feature Store tables{% else %}Feature datasets{% endif %}, ML Design
**Output:** ML Evaluation Report

**Activities:**
{% if config.ml_platform %}- Set up {{ config.ml_platform.experiment_tracking or 'experiment tracking' }} ({% if config.ml_platform.experiment_tracking == 'mlflow' %}MLflow{% elif config.ml_platform.experiment_tracking == 'wandb' %}Weights & Biases{% elif config.ml_platform.experiment_tracking == 'tensorboard' %}TensorBoard{% else %}experiment tracking{% endif %}){% else %}- Set up experiment tracking{% endif %}
- Train baseline model (simple heuristic or linear model)
- Implement hyperparameter tuning
  {% if config.technology_stack and config.technology_stack.backend.language == 'python' %}- Using Optuna, Hyperopt, or GridSearchCV{% endif %}
- Cross-validation and performance evaluation
- Feature importance analysis
- Error analysis (residuals, confusion matrix, calibration curves, etc.)
- Compare to baseline and business requirements
{% if config.ml_platform and config.ml_platform.experiment_tracking == 'mlflow' %}- Log best model to MLflow{% elif config.ml_platform and config.ml_platform.experiment_tracking == 'wandb' %}- Log best model to W&B{% else %}- Save best model{% endif %}

**Deliverables:**
- Trained models {% if config.ml_platform %}in {{ config.ml_platform.experiment_tracking or 'experiment tracker' }}{% else %}(serialized){% endif %}
- **ML Evaluation Report** ({% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/ml-evaluation-[use-case].md)
  - Model performance metrics
  - Cross-validation results
  - Feature importance analysis
  - Error analysis and residual plots
  - Comparison to baseline and requirements
- Training {% if config.technology_stack and config.technology_stack.backend.language == 'python' %}notebooks/scripts{% else %}code{% endif %}
- Hyperparameter tuning results

**Handoff:** Pass ML Evaluation Report to {% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architecture Specialist{% endif %} for review

---

### Step 6: Review ML Infrastructure & Best Practices (Days 13-14)

**Agent:** {% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architecture Specialist{% endif %}
**Duration:** 2 days
**Input:** ML code, {% if config.ml_platform and config.ml_platform.feature_store %}Feature Store design{% else %}feature pipeline{% endif %}, ML Evaluation Report
**Output:** Architecture review with recommendations

**Activities:**
{% if config.ml_platform and config.ml_platform.feature_store %}- Review {{ config.ml_platform.feature_store }} implementation (online/offline, freshness){% else %}- Review feature pipeline implementation{% endif %}
{% if config.ml_platform %}- Validate {{ config.ml_platform.experiment_tracking or 'experiment tracking' }} and model registry usage{% endif %}
{% if config.cloud_provider %}- Check model training performance ({{ config.cloud_provider }} resource optimization){% else %}- Check model training performance (resource optimization){% endif %}
- Review model deployment strategy (batch vs streaming/real-time)
{% if config.architecture and config.architecture.governance %}- Ensure {{ config.architecture.governance }} governance (model access control){% endif %}
- Recommend cost optimizations
- Validate security patterns
{% if config.technology_stack and config.technology_stack.backend.language == 'python' %}- Review Python code quality and best practices{% endif %}

**Deliverables:**
- Architecture review document
- Optimization recommendations
- Security validation checklist
{% if config.cloud_provider %}- {{ config.cloud_provider }} cost estimate{% else %}- Cost estimate{% endif %}
- Scalability assessment

**Handoff:** Pass recommendations to Performance Engineer

---

### Step 7: Optimize Feature Computation & Inference (Days 15-16)

**Agent:** Performance Engineer
**Duration:** 2 days
**Input:** {% if config.ml_platform and config.ml_platform.feature_store %}Feature Store code{% else %}Feature pipeline code{% endif %}, model inference code, architecture review
**Output:** Performance optimization report

**Activities:**
- Profile feature computation pipelines
{% if config.project.type == 'data-platform' and config.big_data_framework %}- Optimize {{ config.big_data_framework }} jobs (caching, partitioning, joins){% elif config.technology_stack and config.technology_stack.backend.language == 'python' %}- Optimize Python code (vectorization, caching, parallelization){% else %}- Optimize feature computation{% endif %}
- Tune model inference performance
  - Batch scoring optimization
  {% if config.technology_stack and config.technology_stack.backend.language == 'python' %}- Model serialization (pickle, ONNX, TorchScript){% endif %}
  - Inference batching and parallelization
{% if config.cloud_provider %}- Right-size {{ config.cloud_provider }} resources for training and inference{% else %}- Right-size compute resources{% endif %}
- Implement incremental feature updates (not full recompute)
- Create performance benchmarks

**Deliverables:**
- Performance optimization report
- Optimized feature pipelines
- Inference performance benchmarks (latency, throughput)
{% if config.cloud_provider %}- {{ config.cloud_provider }} configuration recommendations{% else %}- Resource configuration recommendations{% endif %}
- Profiling results and optimization gains

**Handoff:** Confirm optimizations with ML Engineer

---

### Step 8: Model Registration & Deployment (Days 17-18)

**Agent:** ML Engineer
**Duration:** 2 days
**Input:** Best model {% if config.ml_platform %}from {{ config.ml_platform.experiment_tracking or 'experiment tracker' }}{% endif %}, deployment plan, optimizations
**Output:** Model deployed to production

**Activities:**
{% if config.ml_platform and config.ml_platform.experiment_tracking == 'mlflow' %}- Register model in MLflow Model Registry
- Transition model to "Production" stage{% elif config.ml_platform and config.ml_platform.model_registry %}- Register model in {{ config.ml_platform.model_registry }}{% else %}- Register model in model registry{% endif %}
- Deploy batch scoring job (if batch inference)
  {% if config.orchestration %}- Using {{ config.orchestration }} for scheduling{% endif %}
- Deploy model serving endpoint (if real-time inference)
  {% if config.deployment_platform %}- Deploy to {{ config.deployment_platform }}{% elif config.technology_stack and config.technology_stack.backend.language == 'python' %}- Create FastAPI/Flask endpoint{% endif %}
- Set up model versioning and rollback strategy
- Create inference pipeline using registered model
- Test production deployment

**Deliverables:**
{% if config.ml_platform and config.ml_platform.model_registry %}- Model registered in {{ config.ml_platform.model_registry }} (Production){% else %}- Model registered in production registry{% endif %}
- Batch scoring job {% if config.orchestration %}({{ config.orchestration }} workflow){% endif %} OR model serving endpoint deployed
- Inference pipeline code
- Deployment documentation
- Rollback procedure

**Handoff:** Pass deployment info to Data Analyst / ML Engineer for monitoring

---

### Step 9: Create Model Monitoring Dashboard (Days 19-20)

**Agent:** {% if config.project.type == 'data-platform' %}Data Analyst{% else %}ML Engineer{% endif %}
**Duration:** 2 days
**Input:** Model deployment info, evaluation metrics, {% if config.ml_platform and config.ml_platform.feature_store %}Feature Store{% else %}features{% endif %}
**Output:** Model monitoring dashboard

**Activities:**
{% if config.dashboarding_tool %}- Create dashboard in {{ config.dashboarding_tool }}{% else %}- Create model monitoring dashboard{% endif %}
- Track prediction distribution (drift detection)
- Monitor feature distributions (feature drift)
- Display evaluation metrics over time
- Set up alerts for performance degradation
  {% if config.alerting_platform %}- Configure {{ config.alerting_platform }} alerts{% endif %}
- Create model comparison dashboard (A/B testing, champion/challenger)
- Monitor inference latency and throughput

**Deliverables:**
{% if config.dashboarding_tool %}- {{ config.dashboarding_tool }} dashboard for model monitoring{% else %}- Model monitoring dashboard{% endif %}
- Drift detection alerts
- Performance tracking visualizations
- Inference latency metrics
- Dashboard documentation

**Handoff:** Pass dashboard and all artifacts to Documentation Engineer

---

### Step 10: Document ML Model & Use Case (Days 21-22)

**Agent:** Documentation Engineer
**Duration:** 2 days
**Input:** All ML artifacts (design, evaluation, code, dashboard)
**Output:** Complete ML documentation

**Activities:**
- Document ML use case and business value
- Create model card (architecture, training data, performance, limitations)
{% if config.ml_platform and config.ml_platform.feature_store %}- Document {{ config.ml_platform.feature_store }} tables and feature definitions{% else %}- Document features and feature engineering{% endif %}
- Update data lineage documentation
- Create user guide for consuming model predictions
- Document model limitations, bias considerations, and ethical implications
- Update {% if config.documentation.main_doc %}{{ config.documentation.main_doc }}{% else %}README.md{% endif %} with ML model status
- Document deployment and rollback procedures

**Deliverables:**
- **ML Model Card** (docs/models/[use-case]-model-card.md)
  - Problem statement and business value
  - Model architecture and algorithms
  - Training data description
  - Performance metrics and evaluation
  - Limitations and bias analysis
  - Ethical considerations
{% if config.ml_platform and config.ml_platform.feature_store %}- {{ config.ml_platform.feature_store }} documentation{% else %}- Feature documentation{% endif %}
- Inference API user guide
- Updated {% if config.documentation.main_doc %}{{ config.documentation.main_doc }}{% else %}README.md{% endif %}
- Model lineage documentation

**Handoff:** Pass all code and documentation to Git Committer

---

### Step 11: Commit All ML Artifacts (Day 23)

**Agent:** Git Committer
**Duration:** 1 day
**Input:** All ML code, {% if config.technology_stack and config.technology_stack.backend.language == 'python' %}notebooks{% else %}scripts{% endif %}, configuration, documentation
**Output:** Committed and pushed changes

**Activities:**
- Stage all ML code (feature engineering, training, inference)
{% if config.ml_platform and config.ml_platform.feature_store %}- Stage {{ config.ml_platform.feature_store }} definitions{% endif %}
{% if config.ml_platform %}- Stage {{ config.ml_platform.experiment_tracking or 'experiment tracking' }} configurations{% endif %}
- Stage deployment scripts {% if config.orchestration %}and {{ config.orchestration }} definitions{% endif %}
- Stage model card and documentation updates
- Create descriptive commit message following conventions
- Push to remote repository
- {% if config.version_control_tagging %}Create git tag for model version{% endif %}

**Deliverables:**
- Git commit with all ML artifacts
{% if config.version_control_tagging %}- Tagged release (e.g., `model-v1.0.0`){% endif %}
- Updated remote repository

**Completion:** ML model development workflow complete

---

## Workflow Diagram

```mermaid
graph TD
    A[Sprint Planning<br/>Requirements] --> B[ML Engineer<br/>Design]
    B --> C[Data Engineer<br/>Data Prep]
    C --> D[ML Engineer<br/>Feature Engineering]
    D --> E[ML Engineer<br/>Training & Eval]
    E --> F{% raw %}{{% endraw %}{% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architect{% endif %}<br/>Review{% raw %}}{% endraw %}
    F --> G[Performance Engineer<br/>Optimize]
    G --> H[ML Engineer<br/>Deploy]
    H --> I[ML/Data Analyst<br/>Monitor]
    I --> J[Documentation Engineer<br/>Document]
    J --> K[Git Committer<br/>Commit]
```

---

## Duration Estimates

| Phase | Agent | Duration | Cumulative |
|-------|-------|----------|------------|
| Requirements | Sprint Planning | 1 day | Day 1 |
| Design | ML Engineer | 2 days | Day 3 |
| Data Prep | Data Engineer | 1-2 days | Day 4-5 |
| Feature Engineering | ML Engineer | 3 days | Day 7-8 |
| Training & Evaluation | ML Engineer | 5 days | Day 12-13 |
| Architecture Review | {% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architect{% endif %} | 2 days | Day 14-15 |
| Performance Optimization | Performance Engineer | 2 days | Day 16-17 |
| Deployment | ML Engineer | 2 days | Day 18-19 |
| Monitoring Dashboard | ML/Data Analyst | 2 days | Day 20-21 |
| Documentation | Documentation Engineer | 2 days | Day 22-23 |
| Git Commit | Git Committer | 1 day | Day 23 |
| **Total** | | **23 days** | **~4.5 weeks** |

**Buffer:** Add 2-5 days for iterations, bug fixes, and stakeholder feedback

---

## Success Criteria

### Must Have
- [ ] ML Design Document created and reviewed
{% if config.ml_platform and config.ml_platform.feature_store %}- [ ] {{ config.ml_platform.feature_store }} feature tables created and validated{% else %}- [ ] Feature pipelines created and validated{% endif %}
{% if config.ml_platform %}- [ ] Model trained with {{ config.ml_platform.experiment_tracking or 'experiment tracking' }}{% else %}- [ ] Model trained with experiment tracking{% endif %}
- [ ] Model evaluation meets success criteria (from requirements)
{% if config.ml_platform and config.ml_platform.model_registry %}- [ ] Model registered in {{ config.ml_platform.model_registry }} (Production){% else %}- [ ] Model registered in production registry{% endif %}
- [ ] Model deployed (batch or real-time)
- [ ] Monitoring dashboard created
- [ ] Complete documentation available (model card)

### Should Have
- [ ] Architecture review completed with recommendations implemented
- [ ] Performance optimizations applied
- [ ] Feature drift detection implemented
- [ ] A/B testing capability enabled (champion/challenger)

### Nice to Have
- [ ] Automated retraining pipeline
- [ ] Advanced fairness and bias analysis
- [ ] Explainability dashboard (SHAP values, feature importance)
- [ ] Canary deployments for gradual rollout

---

## Workflow Variants

### Variant 1: Simple Model (No Feature Store)
{% if config.ml_platform and config.ml_platform.feature_store %}- Skip {{ config.ml_platform.feature_store }} creation (Step 4){% else %}- Simplify feature engineering (Step 4){% endif %}
- Use simple features directly from data layer
- Duration: 15-18 days

### Variant 2: Model Refresh (Retrain Existing)
- Skip Steps 1-4 (requirements, design, data prep, feature engineering)
- Start at Step 5 (training with new data)
- Duration: 10-12 days

### Variant 3: Real-Time Inference
- Add model serving endpoint setup in Step 8
- Add latency testing in Step 7
- Add real-time monitoring in Step 9
- Duration: 25-28 days

### Variant 4: Deep Learning Model
- Extend Step 5 (training) to 7-10 days
- Add GPU resource provisioning
{% if config.technology_stack and config.technology_stack.backend.language == 'python' %}- Use PyTorch/TensorFlow{% endif %}
- Add model architecture experiments
- Duration: 28-35 days

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| **Training data insufficient** | Loop back to Step 3, expand data collection |
| **Model performance below target** | Iterate Step 5 (more features, different algorithm, more tuning) |
{% if config.ml_platform and config.ml_platform.feature_store %} | **{{ config.ml_platform.feature_store }} too slow** | Invoke Performance Engineer earlier (after Step 4) |{% else %}| **Feature computation too slow** | Invoke Performance Engineer earlier (after Step 4) |{% endif %}
| **Model deployment fails** | Check model signature/schema, test locally first |
| **Feature drift detected** | Schedule model retraining, update feature pipeline |
| **Inference latency too high** | Optimize model (quantization, pruning, ONNX), use batch inference |

---

## Integration with Other Workflows

**Depends on:**
{% if config.project.type == 'data-platform' %}- Integration workflows - Data must be available for training{% else %}- Data collection workflows{% endif %}
- Sprint Planning - Creates ML requirements

**Triggers other workflows:**
- {% if config.dashboarding_tool %}Dashboard Creation{% else %}Monitoring Setup{% endif %} - Dashboard for model monitoring
- Performance Optimization - If optimization needed

**Can run in parallel with:**
- Single Feature Development - If new features needed for model input
{% if config.project.type == 'data-platform' %}- Data Integration - If new data sources needed{% endif %}

---

## Handoff Templates

This workflow uses the following handoff templates:

1. **ML Design Document** → `{% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/ml-design-template.md`
   - Used in Step 2 (ML Engineer → Data Engineer)

2. **ML Evaluation Report** → `{% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/ml-evaluation-template.md`
   - Used in Step 5 (ML Engineer → {% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architect{% endif %})

3. **Performance Optimization Report** → `{% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/performance-optimization-report-template.md`
   - Used in Step 7 (Performance Engineer → ML Engineer)

4. **Model Card** → `docs/models/[use-case]-model-card.md`
   - Created in Step 10 (Documentation Engineer)

---

## Related Documentation

**Agent Instructions:**
- `agents/development/ml-engineer.md`
- `agents/planning/sprint-planning.md`
{% if config.project.type == 'data-platform' %}- `agents/development/gold-transformation-engineer.md`{% else %}- `agents/development/data-engineer.md`{% endif %}
{% if config.architecture %}- `agents/architecture/{{ config.architecture.specialist | lower | replace(' ', '-') }}.md`{% endif %}
- `agents/quality/performance-engineer.md`
- `agents/documentation/documentation-engineer.md`

**Other Workflows:**
- `workflows/sprint-planning.md`
- `workflows/performance-optimization.md`
{% if config.project.type == 'data-platform' %}- `workflows/single-feature-development.md` (for data integration){% endif %}

---

**Created:** 2025-11-04
**Status:** ✅ Generic
**Version:** 1.0
**Framework:** Vibey Agent Framework
