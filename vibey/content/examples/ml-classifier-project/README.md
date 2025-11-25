# Example: Image Classification ML Project

This example demonstrates roadmap planning for a machine learning image classification project with data pipeline, model training, and deployment.

## Project Overview

**Goal:** Build and deploy an image classification model for product categorization.

**Duration:** 10 weeks
**Tracks:** 3 (sequential dependencies)
**Total Sprints:** 6
**Total Tasks:** 42

## Roadmap Structure

```
Image Classifier (roadmap)
  ├── Data Pipeline (track) - 2 sprints
  │   ├── Sprint 1: Data Collection & Validation
  │   └── Sprint 2: Preprocessing & Augmentation
  ├── Model Development (track) - 3 sprints
  │   ├── Sprint 1: Baseline Model
  │   ├── Sprint 2: Model Optimization
  │   └── Sprint 3: Hyperparameter Tuning
  └── Deployment (track) - 1 sprint
      └── Sprint 1: Model Serving & Monitoring
```

## Technology Stack

- **Language:** Python 3.9+
- **Framework:** PyTorch
- **Data:** AWS S3, DVC for versioning
- **Experiment Tracking:** MLflow
- **Serving:** FastAPI + TorchServe
- **Monitoring:** Prometheus + Grafana

## Track Dependencies

```
Data Pipeline (Track 1)
    ↓
Model Development (Track 2) [Need clean data before training]
    ↓
Deployment (Track 3) [Need trained model before deployment]
```

## Sprint Breakdown

### Track 1: Data Pipeline (3 weeks)

#### Sprint 1: Data Collection & Validation (1.5 weeks)
- Task 1: Set up AWS S3 data lake
- Task 2: Implement data collection scripts
- Task 3: Create data validation pipeline
- Task 4: Implement data versioning with DVC
- Task 5: Create train/val/test split logic
- Task 6: **Gate:** Data quality tests (100% pass rate)
- Task 7: **Gate:** Documentation for data pipeline

#### Sprint 2: Preprocessing & Augmentation (1.5 weeks)
- Task 1: Implement image preprocessing pipeline
- Task 2: Add data augmentation (rotation, flip, crop)
- Task 3: Create data loaders
- Task 4: Implement caching for performance
- Task 5: Add preprocessing validation
- Task 6: **Gate:** Preprocessing unit tests
- Task 7: **Gate:** Performance benchmarks (<100ms per image)

### Track 2: Model Development (5 weeks)

#### Sprint 1: Baseline Model (1.5 weeks)
- Task 1: Implement baseline CNN architecture
- Task 2: Set up training loop
- Task 3: Add evaluation metrics (accuracy, F1, confusion matrix)
- Task 4: Set up MLflow experiment tracking
- Task 5: Train baseline model
- Task 6: **Gate:** Model evaluation report (≥70% accuracy)
- Task 7: **Gate:** Code review for model code

#### Sprint 2: Model Optimization (2 weeks)
- Task 1: Implement ResNet50 architecture
- Task 2: Add transfer learning from ImageNet
- Task 3: Implement learning rate scheduling
- Task 4: Add early stopping and checkpointing
- Task 5: Implement cross-validation
- Task 6: Train optimized model
- Task 7: **Gate:** Model evaluation (≥85% accuracy)
- Task 8: **Gate:** Model comparison analysis

#### Sprint 3: Hyperparameter Tuning (1.5 weeks)
- Task 1: Set up Optuna for hyperparameter search
- Task 2: Define search space
- Task 3: Run hyperparameter optimization
- Task 4: Train final model with best params
- Task 5: Generate model cards (documentation)
- Task 6: **Gate:** Final model evaluation (≥90% accuracy)
- Task 7: **Gate:** Model interpretability analysis

### Track 3: Deployment (2 weeks)

#### Sprint 1: Model Serving & Monitoring (2 weeks)
- Task 1: Package model with TorchServe
- Task 2: Create FastAPI serving endpoint
- Task 3: Add request validation
- Task 4: Implement batch inference
- Task 5: Set up Prometheus metrics
- Task 6: Create Grafana dashboards
- Task 7: Deploy to staging environment
- Task 8: Load testing
- Task 9: **Gate:** Performance tests (<200ms latency)
- Task 10: **Gate:** Security review for API
- Task 11: **Gate:** Deployment documentation

## Agent Assignments

**Recommended agents:**
- **ml-engineer** - All model development, data pipeline tasks
- **test-engineer** - All testing gates
- **docs-writer** - Documentation gates
- **security-auditor** - Security review
- **performance-engineer** - Performance optimization, load testing

## Quality Gates by Track

### Data Pipeline Gates
- Data quality tests (100% pass)
- Preprocessing unit tests (≥90% coverage)
- Performance benchmarks (<100ms per image)

### Model Development Gates
- Baseline accuracy (≥70%)
- Optimized accuracy (≥85%)
- Final accuracy (≥90%)
- Model comparison analysis
- Model interpretability

### Deployment Gates
- API performance (<200ms latency)
- Load testing (1000 req/sec)
- Security review (≥95% score)

## Usage Example

```bash
# Start data pipeline track
roadmap start data-pipeline

# Sprint 1: Data collection
roadmap start data-pipeline-1
roadmap recommend --agent ml-engineer

# Day 1-5: Data collection tasks
roadmap start data-pipeline-1-task-001
roadmap assign data-pipeline-1-task-001 ml-engineer
# ... work on tasks ...

# Day 10: Check if ready for model development
roadmap deps model-1 --blockers
# Output: ⚠️ Blocked by data-pipeline track (need: completed)

# Complete data pipeline
roadmap complete data-pipeline

# Now model development unblocked
roadmap deps model-1 --blockers
# Output: No blockers

# Start model development
roadmap start model
roadmap start model-1
roadmap recommend --agent ml-engineer
```

## Experiment Tracking

Each model training task logs to MLflow:

```python
# In training script
import mlflow

with mlflow.start_run():
    mlflow.log_param("architecture", "resnet50")
    mlflow.log_param("learning_rate", 0.001)
    mlflow.log_metric("accuracy", accuracy)
    mlflow.log_metric("f1_score", f1)
    mlflow.pytorch.log_model(model, "model")
```

Track experiments with roadmap:

```bash
# After training
roadmap show model-2-task-006
# Shows: Task status, MLflow run ID, metrics

# Compare models
roadmap list tasks --type development | grep "Train model"
```

## Expected Timeline

| Weeks | Track | Focus | Status |
|-------|-------|-------|--------|
| 1-3   | Data Pipeline | Data collection & prep | ✅ completed |
| 4-8   | Model Dev | Training & optimization | 🔵 in_progress |
| 9-10  | Deployment | Serving & monitoring | ⚪ not_started |

## Success Criteria

✅ Data pipeline validated (100% pass rate)
✅ Model accuracy ≥90%
✅ API latency <200ms
✅ Load test: 1000 req/sec
✅ Security score ≥95%
✅ Complete documentation
✅ Production deployment

## Key Learnings

This example demonstrates:
- **Sequential track dependencies** - Each track blocks the next
- **ML-specific quality gates** - Accuracy thresholds, performance benchmarks
- **Experiment tracking integration** - MLflow integration
- **Iterative model development** - Baseline → Optimized → Tuned
- **End-to-end ML pipeline** - Data → Model → Deployment

## Files Structure

```
ml-classifier-project/
└── .vibey/
    ├── roadmap.yaml
    ├── tracks/
    │   ├── data-pipeline.yaml
    │   ├── model.yaml
    │   └── deployment.yaml
    ├── sprints/
    │   ├── data-pipeline-1.yaml
    │   ├── data-pipeline-2.yaml
    │   ├── model-1.yaml
    │   ├── model-2.yaml
    │   ├── model-3.yaml
    │   └── deployment-1.yaml
    └── tasks/
        └── [6 task files]
```
