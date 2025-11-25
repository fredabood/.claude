# Roadmap System Examples

This directory contains complete, production-ready examples demonstrating the Roadmap Object Hierarchy system.

---

## Available Examples

### 1. REST API Project
**Path:** `rest-api-project/`
**Type:** Web API Development
**Duration:** 6 weeks (3 sprints)
**Complexity:** ⭐⭐ Medium

**What It Demonstrates:**
- Sprint-level quality gates
- Sequential task dependencies
- Agent routing for web development
- Version bumping on sprint completion

**Use Case:** Building a task management REST API with authentication, CRUD operations, and user management.

**Key Features:**
- FastAPI + PostgreSQL
- JWT authentication
- 90%+ test coverage
- OpenAPI documentation

[**View Details →**](rest-api-project/README.md)

---

### 2. Machine Learning Classifier
**Path:** `ml-classifier-project/`
**Type:** ML Model Development
**Duration:** 10 weeks (6 sprints across 3 tracks)
**Complexity:** ⭐⭐⭐ High

**What It Demonstrates:**
- Multi-track dependencies (Data → Model → Deployment)
- ML-specific quality gates (accuracy thresholds)
- Experiment tracking integration (MLflow)
- Iterative model development

**Use Case:** Building and deploying an image classification model for product categorization.

**Key Features:**
- PyTorch + AWS S3
- MLflow experiment tracking
- Model serving with FastAPI
- Performance monitoring

[**View Details →**](ml-classifier-project/README.md)

---

### 3. Infrastructure Migration
**Path:** `infrastructure-migration/`
**Type:** Infrastructure/DevOps
**Duration:** 10 weeks (7 sprints across 4 tracks)
**Complexity:** ⭐⭐⭐⭐ Very High

**What It Demonstrates:**
- Strict sequential track dependencies
- Risk management for high-risk tasks
- Coordinator agent for complex operations
- Zero-downtime migration strategy
- Rollback planning

**Use Case:** Migrating production application from AWS EC2 to EKS (Kubernetes) with zero downtime.

**Key Features:**
- Terraform + EKS
- Blue-green deployment
- Comprehensive monitoring
- Production cutover planning

[**View Details →**](infrastructure-migration/README.md)

---

## How to Use These Examples

### Option 1: Copy to Your Project

```bash
# Copy example structure to your project
cp -r rest-api-project/.vibey /path/to/your-project/

# Navigate to project
cd /path/to/your-project

# View status
roadmap status
```

### Option 2: Study and Adapt

1. **Read the README** - Understand the project structure
2. **Review YAML files** - See how tracks/sprints/tasks are structured
3. **Adapt to your needs** - Modify for your specific project
4. **Create your own** - Use as a template

### Option 3: Interactive Exploration

```bash
# Add roadmap CLI to PATH
export PATH="$PATH:/path/to/vibey/framework/scripts"

# Navigate to example
cd rest-api-project

# Explore the roadmap
roadmap status
roadmap show api-1
roadmap list tasks
roadmap deps
roadmap validate
```

---

## Comparison Matrix

| Feature | REST API | ML Classifier | Infrastructure |
|---------|----------|---------------|----------------|
| **Tracks** | 1 | 3 | 4 |
| **Sprints** | 3 | 6 | 7 |
| **Tasks** | 24 | 42 | 48 |
| **Duration** | 6 weeks | 10 weeks | 10 weeks |
| **Dependencies** | Simple | Sequential | Critical Sequential |
| **Risk Level** | Low | Medium | Very High |
| **Complexity** | Medium | High | Very High |

---

## Common Patterns Demonstrated

### 1. Sequential Sprints (REST API Example)
```
Sprint 1 (Auth)
  └─> Sprint 2 (CRUD) [depends on: Sprint 1 completed]
      └─> Sprint 3 (Advanced) [depends on: Sprint 2 completed]
```

### 2. Track Dependencies (ML Classifier Example)
```
Data Pipeline Track
  └─> Model Development Track [depends on: Data Pipeline completed]
      └─> Deployment Track [depends on: Model Development completed]
```

### 3. Parallel Tasks (All Examples)
```
Task A (no dependencies)
Task B (no dependencies)
  ↓
Task C (depends on: A + B completed)
```

### 4. Quality Gate Tasks (All Examples)
```
Development Tasks (task-001 through task-005)
  ↓
Sprint auto-progresses to completion_gate_check
  ↓
Gate Tasks (task-gate-001 through task-gate-003)
  ↓
Sprint can be completed when all gates pass
```

---

## Best Practices from Examples

### 1. Task Granularity
- **Good:** "Implement user registration endpoint" (4-6 hours)
- **Too Large:** "Build entire authentication system" (2 weeks)
- **Too Small:** "Write docstring for function" (15 minutes)

### 2. Dependency Clarity
```yaml
dependencies:
  - type: "task"
    target_id: "backend-1-task-001"
    at_status: "completed"
    reason: "Need schema before implementing endpoints"  # Always include reason!
```

### 3. Quality Gate Design
- 2-4 gates per sprint
- Use `blocking: true` for critical gates
- Set realistic thresholds (80-95%)
- Include both automated tests and manual reviews

### 4. Agent Assignment
```yaml
# Development tasks
assigned_agent: "web-developer"

# Testing gates
assigned_agent: "test-engineer"

# Security gates
assigned_agent: "security-auditor"

# Documentation gates
assigned_agent: "docs-writer"
```

### 5. Status Progression
Let the system handle progression automatically:
- Complete all dev tasks → System moves to `completion_gate_check`
- Complete all gate tasks → Sprint can be completed
- Don't manually set status unless necessary

---

## Learning Path

**Beginner:** Start with **REST API Example**
- Simple single-track structure
- Clear sequential sprints
- Standard web development patterns
- Good introduction to quality gates

**Intermediate:** Progress to **ML Classifier Example**
- Multi-track dependencies
- ML-specific patterns
- Experiment tracking
- More complex workflow

**Advanced:** Study **Infrastructure Migration**
- Critical sequential dependencies
- Risk management
- Coordinator agent usage
- Production-grade complexity

---

## Customizing Examples

### Modify for Your Tech Stack

**REST API Example:**
```yaml
# Original: FastAPI + PostgreSQL
# Modify to: Express + MongoDB

technology_stack:
  backend:
    language: "TypeScript"
    framework: "Express"
  database:
    type: "MongoDB"
```

**ML Classifier Example:**
```yaml
# Original: PyTorch
# Modify to: TensorFlow

technology_stack:
  framework: "TensorFlow"
  serving: "TensorFlow Serving"
```

### Adjust Complexity

**Reduce Sprints:**
```yaml
# From 3 sprints → 2 sprints
# Combine Sprint 2 and Sprint 3
```

**Increase Quality Gates:**
```yaml
# Add more gates
quality_gates:
  - name: "Performance Tests"
    threshold: 95
    blocking: true
  - name: "Accessibility Audit"
    threshold: 90
    blocking: true
```

---

## Additional Resources

- **[User Guide](../docs/development/ROADMAP_USER_GUIDE.md)** - Complete user guide (700+ lines)
- **[CLI Reference](../scripts/CLI.md)** - All commands documented (730+ lines)
- **[Examples Document](../docs/development/ROADMAP_EXAMPLES.md)** - Additional workflow examples (900+ lines)
- **[Migration Guide](../docs/development/ROADMAP_MIGRATION_GUIDE.md)** - Migrating existing projects

---

## Contributing Examples

Have a great example? Contribute it!

**Requirements:**
- Complete roadmap structure (roadmap.yaml, tracks, sprints, tasks)
- Comprehensive README explaining the use case
- Real-world applicability
- Demonstrates specific patterns or techniques
- Includes recommended agent assignments

**Submission:**
Create a pull request with your example in a new directory under `examples/`.

---

## Questions?

Refer to the User Guide or CLI Reference for detailed information on:
- Creating tracks and sprints
- Defining dependencies
- Setting up quality gates
- Using agent routing
- Managing roadmap health

---

**Start with an example, customize for your needs, and build great software!** 🚀
