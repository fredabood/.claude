# Roadmap Examples

Example roadmap configurations demonstrating the roadmap system for different project types.

---

## Available Examples

### 1. ML Pipeline Roadmap
**File:** `ml-pipeline-roadmap.yaml`
**Project Type:** Machine Learning Platform
**Use Case:** Customer Churn Prediction

Demonstrates roadmap system for ML/data science projects with:
- **4 Tracks:** Data Pipeline, Model Development, ML Infrastructure, Monitoring
- **Data pipeline track** - Data ingestion, feature engineering, data validation
- **Model development track** - Baseline models, optimization, deployment (blocked by data-pipeline)
- **ML infrastructure track** - MLflow, training orchestration, deployment pipeline (independent)
- **Monitoring track** - Performance monitoring, drift detection, alerting (blocked by model-development)

**Key Features:**
- Track-level dependencies (model development blocked by data pipeline)
- ML-specific quality gates (data quality, model validation, drift detection)
- Complex task dependencies within sprints
- Feature engineering and model experimentation workflows

**Technologies:** Python, PyTorch, scikit-learn, MLflow, Apache Airflow, PostgreSQL

---

### 2. Mobile App Roadmap
**File:** `mobile-app-roadmap.yaml`
**Project Type:** Mobile Application
**Use Case:** FitLife Fitness Tracker

Demonstrates roadmap system for cross-platform mobile development with:
- **5 Tracks:** Core App, iOS Integration, Android Integration, Backend Services, Testing/QA
- **Core app track** - React Native setup, navigation, screens, state management (foundation)
- **iOS integration track** - HealthKit, notifications, widgets (blocked by core-app)
- **Android integration track** - Google Fit, notifications, widgets (blocked by core-app)
- **Backend services track** - Firebase auth, Firestore, cloud functions (independent)
- **Testing/QA track** - Unit tests, E2E tests, manual QA (blocked by core-app progress)

**Key Features:**
- Platform-specific tracks (iOS, Android) both depend on core app
- Independent backend development
- Testing track can start once core-app is in progress
- Mobile-specific quality gates (build validation, privacy compliance)

**Technologies:** React Native, TypeScript, Redux Toolkit, Firebase, HealthKit, Google Fit, Jest, Detox

---

## How to Use These Examples

### 1. View the Structure

```bash
# View ML pipeline roadmap
cat examples/roadmaps/ml-pipeline-roadmap.yaml

# View mobile app roadmap
cat examples/roadmaps/mobile-app-roadmap.yaml
```

### 2. Copy as Starting Point

```bash
# Copy to your project
cp examples/roadmaps/ml-pipeline-roadmap.yaml .vibey/roadmap.yaml

# Customize for your needs
# Edit .vibey/roadmap.yaml with your project details
```

### 3. Initialize from Example

```bash
# Create new roadmap based on example
python3 framework/scripts/roadmap-init.py \
  --id "my-ml-project" \
  --name "My ML Project" \
  --template examples/roadmaps/ml-pipeline-roadmap.yaml
```

### 4. Query the Example

```bash
# Query the roadmap structure
python3 framework/scripts/roadmap-query.py \
  --file examples/roadmaps/ml-pipeline-roadmap.yaml

# Show specific track
python3 framework/scripts/roadmap-query.py \
  --file examples/roadmaps/ml-pipeline-roadmap.yaml \
  --track data-pipeline

# Show dependencies
python3 framework/scripts/roadmap-query.py \
  --file examples/roadmaps/ml-pipeline-roadmap.yaml \
  --dependencies
```

---

## Key Concepts Demonstrated

### Track Dependencies

**ML Pipeline Example:**
```yaml
# Model development blocked by data pipeline
track:
  id: model-development
  blocked_by:
    - dependency_id: data-pipeline
      dependency_type: track
      required_status: completed
```

**Mobile App Example:**
```yaml
# iOS integration blocked by core app
track:
  id: ios-integration
  blocked_by:
    - dependency_id: core-app
      dependency_type: track
      required_status: completed
```

### Sprint Dependencies

**Sequential sprints:**
```yaml
# Sprint 2 depends on Sprint 1
sprint:
  id: data-pipeline-2
  blocked_by:
    - dependency_id: data-pipeline-1
      dependency_type: sprint
      required_status: completed
```

### Task Dependencies

**Within a sprint:**
```yaml
# Task 002 depends on Task 001
task:
  id: data-pipeline-1-task-002
  blocked_by:
    - dependency_id: data-pipeline-1-task-001
      dependency_type: task
      required_status: completed
      blocks_transition_to: in_progress
```

### Quality Gates

**Completion Gates (block sprint completion):**
```yaml
task:
  id: core-app-1-gate-c001
  task_type: completion_gate
  title: Development standards documentation
  gate_info:
    gate_type: completion
    blocking_scope: sprint_completion
```

**Production Gates (block production deployment):**
```yaml
task:
  id: data-pipeline-1-gate-p001
  task_type: production_gate
  title: Data quality tests passing
  gate_info:
    gate_type: production
    validation_command: pytest tests/data_quality/ --cov-fail-under=85
    blocking_scope: production_deployment
```

---

## Customizing Examples

### 1. Change Project Details

```yaml
roadmap:
  id: your-project-id          # Your project ID
  name: Your Project Name       # Your project name

  metadata:
    description: Your description
    project_type: your-type     # web-app, mobile-app, ml-platform, etc.
    tech_stack:                  # Your tech stack
      - Python
      - Your frameworks
```

### 2. Add/Remove Tracks

```yaml
roadmap:
  tracks:
    - your-track-1
    - your-track-2
    - your-track-3
```

### 3. Adjust Dependencies

```yaml
# Change which tracks depend on what
track:
  id: your-track
  blocked_by:
    - dependency_id: prerequisite-track
      required_status: completed  # or in_progress
```

### 4. Customize Quality Gates

```yaml
# Add your own quality gates
task:
  id: your-gate-p001
  task_type: production_gate
  gate_info:
    validation_command: your-validation-script
    validation_criteria:
      - Your criterion 1
      - Your criterion 2
```

---

## Common Patterns

### Pattern 1: Foundation Track + Dependent Tracks

Used in **Mobile App** example:
- **Core App** = Foundation (everyone depends on it)
- **iOS Integration** = Depends on Core App
- **Android Integration** = Depends on Core App
- **Backend Services** = Independent
- **Testing/QA** = Depends on Core App progress

### Pattern 2: Sequential Pipeline

Used in **ML Pipeline** example:
- **Data Pipeline** = First (no dependencies)
- **Model Development** = Second (depends on Data Pipeline)
- **Monitoring** = Third (depends on Model Development)
- **ML Infrastructure** = Independent (can run in parallel)

### Pattern 3: Task Fan-Out

Multiple tasks depend on one prerequisite:
```yaml
# Task 001 (database schema)
#   ├── Task 002 (registration) - depends on 001
#   ├── Task 003 (login) - depends on 001
#   └── Task 004 (password reset) - depends on 001
```

### Pattern 4: Task Chain

Tasks form a sequential chain:
```yaml
# Task 001 (setup)
#   └── Task 002 (connector) - depends on 001
#       └── Task 003 (validation) - depends on 002
#           └── Task 004 (optimization) - depends on 003
```

---

## Testing Your Roadmap

### 1. Validate Structure

```bash
# Validate YAML syntax and structure
python3 framework/scripts/validate-roadmap.py \
  --file examples/roadmaps/ml-pipeline-roadmap.yaml
```

### 2. Check Dependencies

```bash
# Visualize dependency graph
python3 framework/scripts/roadmap-query.py \
  --file examples/roadmaps/ml-pipeline-roadmap.yaml \
  --dependencies
```

### 3. Identify Blockers

```bash
# Find what's blocked
python3 framework/scripts/roadmap-query.py \
  --file examples/roadmaps/ml-pipeline-roadmap.yaml \
  --blockers
```

### 4. Simulate Progress

```bash
# Copy example to .vibey/
cp examples/roadmaps/ml-pipeline-roadmap.yaml .vibey/roadmap.yaml

# Start first sprint
python3 framework/scripts/roadmap-update.py --start-sprint data-pipeline-1

# Complete first task
python3 framework/scripts/roadmap-update.py --complete-task data-pipeline-1-task-001

# Check what unblocked
python3 framework/scripts/roadmap-query.py --sprint data-pipeline-1
```

---

## Example Queries

### Show Overall Status

```bash
python3 framework/scripts/roadmap-query.py \
  --file examples/roadmaps/ml-pipeline-roadmap.yaml
```

**Output:**
```
Roadmap: ml-pipeline (Customer Churn Prediction ML Pipeline)
Version: 0.1.0
Status: not_started

Tracks: 4
  - data-pipeline (not_started)
  - model-development (blocked - depends on data-pipeline)
  - ml-infrastructure (not_started)
  - monitoring (blocked - depends on model-development)

Sprints: 0 started
```

### Show Track Details

```bash
python3 framework/scripts/roadmap-query.py \
  --file examples/roadmaps/ml-pipeline-roadmap.yaml \
  --track data-pipeline
```

**Output:**
```
Track: data-pipeline (Data Pipeline & Feature Engineering)
Status: not_started
Priority: critical

Sprints: 3
  1. data-pipeline-1 (Data Ingestion System) - not_started
  2. data-pipeline-2 (Feature Engineering) - blocked by data-pipeline-1
  3. data-pipeline-3 (Data Validation) - blocked by data-pipeline-2

No blockers (ready to start)
```

### Show Sprint Tasks

```bash
python3 framework/scripts/roadmap-query.py \
  --file examples/roadmaps/ml-pipeline-roadmap.yaml \
  --sprint data-pipeline-1
```

**Output:**
```
Sprint: data-pipeline-1 (Data Ingestion System)
Track: data-pipeline
Status: not_started

Development Tasks: 5
  - data-pipeline-1-task-001: Design schema (critical) - READY
  - data-pipeline-1-task-002: CRM connector (critical) - BLOCKED by 001
  - data-pipeline-1-task-003: Transaction connector (critical) - BLOCKED by 001
  - data-pipeline-1-task-004: Support connector (high) - BLOCKED by 001
  - data-pipeline-1-task-005: Deduplication (high) - BLOCKED by 002, 003, 004

Completion Gates: 1
Production Gates: 1

Estimated Total: 77,000 tokens
```

---

## Contributing Examples

Want to add your own example roadmap? Follow these guidelines:

### 1. Choose a Distinct Project Type

Current examples:
- ✅ ML Pipeline
- ✅ Mobile App
- ⬜ Backend API
- ⬜ Data Platform
- ⬜ DevOps/Infrastructure
- ⬜ Frontend SPA

### 2. Include All Required Fields

```yaml
roadmap:
  id: your-example-id
  name: Your Example Name
  version: 0.1.0
  status: not_started

  metadata:
    description: Clear description
    project_type: specific-type
    tech_stack: [list, of, technologies]

  tracks: [list-of-tracks]
```

### 3. Demonstrate Key Concepts

- ✅ Track dependencies
- ✅ Sprint dependencies
- ✅ Task dependencies
- ✅ Quality gates (completion + production)
- ✅ Different priority levels
- ✅ Realistic token estimates

### 4. Add Documentation

Update this README with:
- Description of your example
- Key features demonstrated
- Technologies used
- Unique patterns shown

### 5. Test Your Example

```bash
# Validate structure
python3 framework/scripts/validate-roadmap.py --file your-example.yaml

# Test queries
python3 framework/scripts/roadmap-query.py --file your-example.yaml
python3 framework/scripts/roadmap-query.py --file your-example.yaml --dependencies
```

---

## See Also

- **Tutorial:** [ROADMAP_TUTORIAL.md](../../docs/guides/ROADMAP_TUTORIAL.md) - Complete walkthrough
- **User Guide:** [ROADMAP_USER_GUIDE.md](../../docs/guides/ROADMAP_USER_GUIDE.md) - Comprehensive guide
- **CLI Reference:** [ROADMAP_CLI_REFERENCE.md](../../docs/guides/ROADMAP_CLI_REFERENCE.md) - Command reference
- **Design Decisions:** [DESIGN_DECISIONS.md](../../framework/roadmap/DESIGN_DECISIONS.md) - Architecture details

---

**Examples Version:** 2.1
**Last Updated:** 2025-11-09
