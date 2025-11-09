# Roadmap Tutorial: Building an E-Commerce Platform

**Version:** 2.1
**Last Updated:** 2025-11-09

Step-by-step tutorial for building a complete roadmap for an e-commerce platform.

---

## Table of Contents

1. [Tutorial Overview](#tutorial-overview)
2. [Prerequisites](#prerequisites)
3. [Phase 1: Initialize Roadmap](#phase-1-initialize-roadmap)
4. [Phase 2: Define Tracks](#phase-2-define-tracks)
5. [Phase 3: Plan First Sprint](#phase-3-plan-first-sprint)
6. [Phase 4: Working Through Tasks](#phase-4-working-through-tasks)
7. [Phase 5: Quality Gates](#phase-5-quality-gates)
8. [Phase 6: Sprint Completion](#phase-6-sprint-completion)
9. [Phase 7: Track Dependencies](#phase-7-track-dependencies)
10. [Phase 8: Production Deployment](#phase-8-production-deployment)
11. [What You've Learned](#what-youve-learned)
12. [Next Steps](#next-steps)

---

## Tutorial Overview

### What We'll Build

An **e-commerce platform** with multiple tracks:
- **Backend Track** - API, database, authentication
- **Frontend Track** - Web app UI
- **Mobile Track** - iOS/Android apps
- **Infrastructure Track** - Cloud deployment, monitoring

### What You'll Learn

- Creating and initializing a roadmap
- Defining tracks with dependencies
- Planning sprints with tasks
- Managing dependencies between sprints and tracks
- Working through the development lifecycle
- Using quality gates effectively
- Completing sprints and tracking progress

### Tutorial Structure

- **Duration:** ~60 minutes
- **Sections:** 8 phases (each builds on the previous)
- **Format:** Interactive (you'll run real commands)
- **Difficulty:** Beginner to Intermediate

---

## Prerequisites

### Required

- Python 3.7+ installed
- Git installed
- Working directory for tutorial

### Setup

```bash
# Create tutorial directory
mkdir ecommerce-tutorial
cd ecommerce-tutorial

# Initialize git repo
git init

# Verify Python version
python3 --version  # Should be 3.7+
```

### File Structure

By the end, you'll have:

```
ecommerce-tutorial/
├── .vibey/
│   ├── roadmap.yaml
│   ├── tracks/
│   │   ├── backend.yaml
│   │   ├── frontend.yaml
│   │   ├── mobile.yaml
│   │   └── infrastructure.yaml
│   ├── sprints/
│   │   ├── backend-1.yaml
│   │   ├── backend-2.yaml
│   │   ├── frontend-1.yaml
│   │   └── ...
│   └── tasks/
│       ├── backend-1-tasks.yaml
│       ├── backend-2-tasks.yaml
│       └── ...
├── src/
│   ├── backend/
│   ├── frontend/
│   └── mobile/
└── infrastructure/
```

---

## Phase 1: Initialize Roadmap

### Step 1.1: Create Roadmap

Initialize the roadmap for our e-commerce platform.

```bash
python3 framework/scripts/roadmap-init.py \
  --id "ecommerce-platform" \
  --name "E-Commerce Platform" \
  --dir .vibey
```

**Expected Output:**

```
✓ Created roadmap directory: .vibey
✓ Created roadmap.yaml
✓ Created tracks/ directory
✓ Created sprints/ directory
✓ Created tasks/ directory

Roadmap initialized: ecommerce-platform
Next steps:
  1. Create tracks (python3 framework/scripts/roadmap-track.py create ...)
  2. Plan first sprint (python3 framework/scripts/roadmap-sprint.py create ...)
```

### Step 1.2: Verify Roadmap

Check that the roadmap was created correctly.

```bash
python3 framework/scripts/roadmap-query.py
```

**Expected Output:**

```
Roadmap: ecommerce-platform (E-Commerce Platform)
Version: 0.1.0
Status: not_started

Tracks: 0
Sprints: 0
Tasks: 0
```

### Step 1.3: Examine Roadmap File

```bash
cat .vibey/roadmap.yaml
```

**Contents:**

```yaml
roadmap:
  id: ecommerce-platform
  name: E-Commerce Platform
  version: 0.1.0
  status: not_started
  created_at: 2025-11-09T10:00:00Z
  updated_at: 2025-11-09T10:00:00Z

  metadata:
    description: "E-commerce platform with backend, frontend, and mobile apps"
    project_type: web-app

  progress:
    tracks_total: 0
    tracks_completed: 0
    sprints_total: 0
    sprints_completed: 0
    tasks_total: 0
    tasks_completed: 0
    completion_percent: 0
```

**Key Points:**

- ✅ Roadmap starts at version 0.1.0
- ✅ Status is `not_started` (will change when first sprint starts)
- ✅ Progress is all zeros (expected for new roadmap)
- ✅ Metadata includes project type and description

---

## Phase 2: Define Tracks

Tracks represent major work streams. Let's create four tracks for our platform.

### Step 2.1: Create Backend Track

```bash
python3 framework/scripts/roadmap-track.py create \
  --id "backend" \
  --name "Backend API & Database" \
  --description "RESTful API, PostgreSQL database, authentication system" \
  --priority "critical"
```

**Expected Output:**

```
✓ Created track: backend
✓ Track file: .vibey/tracks/backend.yaml

Track: backend (Backend API & Database)
Priority: critical
Status: not_started
```

### Step 2.2: Create Frontend Track

```bash
python3 framework/scripts/roadmap-track.py create \
  --id "frontend" \
  --name "Web Frontend" \
  --description "React web application for customers and admins" \
  --priority "high" \
  --depends-on "backend:completed"
```

**Expected Output:**

```
✓ Created track: frontend
✓ Added dependency: backend (must be completed)
✓ Track file: .vibey/tracks/frontend.yaml

Track: frontend (Web Frontend)
Priority: high
Status: blocked (waiting on: backend)
```

**Key Point:** Frontend depends on backend being completed. This creates a track-level dependency.

### Step 2.3: Create Mobile Track

```bash
python3 framework/scripts/roadmap-track.py create \
  --id "mobile" \
  --name "Mobile Apps" \
  --description "iOS and Android native applications" \
  --priority "high" \
  --depends-on "backend:completed"
```

**Expected Output:**

```
✓ Created track: mobile
✓ Added dependency: backend (must be completed)
✓ Track file: .vibey/tracks/mobile.yaml

Track: mobile (Mobile Apps)
Priority: high
Status: blocked (waiting on: backend)
```

### Step 2.4: Create Infrastructure Track

```bash
python3 framework/scripts/roadmap-track.py create \
  --id "infrastructure" \
  --name "Cloud Infrastructure" \
  --description "AWS deployment, monitoring, CI/CD pipelines" \
  --priority "medium"
```

**Expected Output:**

```
✓ Created track: infrastructure
✓ Track file: .vibey/tracks/infrastructure.yaml

Track: infrastructure (Cloud Infrastructure)
Priority: medium
Status: not_started
```

### Step 2.5: View All Tracks

```bash
python3 framework/scripts/roadmap-query.py --list-tracks
```

**Expected Output:**

```
Roadmap: ecommerce-platform
Tracks: 4

1. backend (Backend API & Database) [critical]
   Status: not_started
   Sprints: 0

2. frontend (Web Frontend) [high]
   Status: blocked (depends on: backend)
   Sprints: 0

3. mobile (Mobile Apps) [high]
   Status: blocked (depends on: backend)
   Sprints: 0

4. infrastructure (Cloud Infrastructure) [medium]
   Status: not_started
   Sprints: 0
```

### Step 2.6: Visualize Dependencies

```bash
python3 framework/scripts/roadmap-query.py --dependencies
```

**Expected Output:**

```
Dependency Graph:

backend (critical)
├── frontend (depends on backend:completed)
└── mobile (depends on backend:completed)

infrastructure (independent)
```

**Key Points:**

- ✅ 4 tracks created
- ✅ Backend is independent (no dependencies)
- ✅ Frontend and Mobile both depend on Backend
- ✅ Infrastructure is independent
- ✅ Dependencies are enforced automatically

---

## Phase 3: Plan First Sprint

Let's plan the first sprint for the backend track.

### Step 3.1: Create Sprint

```bash
python3 framework/scripts/roadmap-sprint.py create \
  --id "backend-1" \
  --track "backend" \
  --name "User Authentication System" \
  --description "JWT-based auth, user registration, login, password reset"
```

**Expected Output:**

```
✓ Created sprint: backend-1
✓ Sprint file: .vibey/sprints/backend-1.yaml
✓ Task file: .vibey/tasks/backend-1-tasks.yaml

Sprint: backend-1 (User Authentication System)
Track: backend
Status: not_started
Tasks: 0 (add with: roadmap-task.py create)
```

### Step 3.2: Add Development Tasks

Let's add several development tasks to this sprint.

**Task 1: Database Schema**

```bash
python3 framework/scripts/roadmap-task.py create \
  --sprint "backend-1" \
  --id "backend-1-task-001" \
  --type "development" \
  --title "Design and implement user database schema" \
  --description "PostgreSQL schema for users, sessions, password resets" \
  --priority "critical" \
  --estimated-tokens 8000
```

**Task 2: Registration Endpoint**

```bash
python3 framework/scripts/roadmap-task.py create \
  --sprint "backend-1" \
  --id "backend-1-task-002" \
  --type "development" \
  --title "Implement user registration endpoint" \
  --description "POST /api/auth/register with validation and email verification" \
  --priority "critical" \
  --estimated-tokens 12000 \
  --depends-on "backend-1-task-001:completed"
```

**Task 3: Login Endpoint**

```bash
python3 framework/scripts/roadmap-task.py create \
  --sprint "backend-1" \
  --id "backend-1-task-003" \
  --type "development" \
  --title "Implement login endpoint with JWT" \
  --description "POST /api/auth/login returns JWT access and refresh tokens" \
  --priority "critical" \
  --estimated-tokens 10000 \
  --depends-on "backend-1-task-001:completed"
```

**Task 4: Password Reset**

```bash
python3 framework/scripts/roadmap-task.py create \
  --sprint "backend-1" \
  --id "backend-1-task-004" \
  --type "development" \
  --title "Implement password reset flow" \
  --description "Email-based password reset with secure tokens" \
  --priority "high" \
  --estimated-tokens 15000 \
  --depends-on "backend-1-task-002:completed"
```

**Task 5: Token Refresh**

```bash
python3 framework/scripts/roadmap-task.py create \
  --sprint "backend-1" \
  --id "backend-1-task-005" \
  --type "development" \
  --title "Implement token refresh mechanism" \
  --description "POST /api/auth/refresh validates refresh token and issues new access token" \
  --priority "high" \
  --estimated-tokens 8000 \
  --depends-on "backend-1-task-003:completed"
```

### Step 3.3: Add Completion Gates

Quality gates that block sprint completion.

**Gate C001: Documentation**

```bash
python3 framework/scripts/roadmap-task.py create \
  --sprint "backend-1" \
  --id "backend-1-gate-c001" \
  --type "completion_gate" \
  --title "API documentation complete" \
  --description "OpenAPI/Swagger docs for all auth endpoints" \
  --priority "high" \
  --estimated-tokens 5000 \
  --gate-command "npx swagger-cli validate api-spec.yaml"
```

**Gate C002: Code Review**

```bash
python3 framework/scripts/roadmap-task.py create \
  --sprint "backend-1" \
  --id "backend-1-gate-c002" \
  --type "completion_gate" \
  --title "Code review completed" \
  --description "All auth code reviewed and approved" \
  --priority "high" \
  --estimated-tokens 3000
```

### Step 3.4: Add Production Gates

Quality gates that block production deployment.

**Gate P001: Unit Tests**

```bash
python3 framework/scripts/roadmap-task.py create \
  --sprint "backend-1" \
  --id "backend-1-gate-p001" \
  --type "production_gate" \
  --title "Unit tests >90% coverage" \
  --description "Comprehensive tests for auth system" \
  --priority "critical" \
  --estimated-tokens 20000 \
  --gate-command "pytest --cov=src/auth --cov-report=term --cov-fail-under=90"
```

**Gate P002: Security Audit**

```bash
python3 framework/scripts/roadmap-task.py create \
  --sprint "backend-1" \
  --id "backend-1-gate-p002" \
  --type "production_gate" \
  --title "Security audit passed" \
  --description "Check for SQL injection, XSS, CSRF, password storage" \
  --priority "critical" \
  --estimated-tokens 10000 \
  --gate-command "bandit -r src/auth/"
```

**Gate P003: Load Testing**

```bash
python3 framework/scripts/roadmap-task.py create \
  --sprint "backend-1" \
  --id "backend-1-gate-p003" \
  --type "production_gate" \
  --title "Load testing completed" \
  --description "Auth endpoints handle 1000 req/sec" \
  --priority "high" \
  --estimated-tokens 12000 \
  --gate-command "k6 run load-tests/auth.js"
```

### Step 3.5: View Sprint Plan

```bash
python3 framework/scripts/roadmap-query.py --sprint backend-1
```

**Expected Output:**

```
Sprint: backend-1 (User Authentication System)
Track: backend
Status: not_started
Progress: 0% (0/10 tasks)

Development Tasks: 5
  [not_started] backend-1-task-001 - Database schema (critical)
  [not_started] backend-1-task-002 - Registration endpoint (critical) [depends on: 001]
  [not_started] backend-1-task-003 - Login endpoint (critical) [depends on: 001]
  [not_started] backend-1-task-004 - Password reset (high) [depends on: 002]
  [not_started] backend-1-task-005 - Token refresh (high) [depends on: 003]

Completion Gates: 2
  [not_started] backend-1-gate-c001 - API documentation (high)
  [not_started] backend-1-gate-c002 - Code review (high)

Production Gates: 3
  [not_started] backend-1-gate-p001 - Unit tests >90% (critical)
  [not_started] backend-1-gate-p002 - Security audit (critical)
  [not_started] backend-1-gate-p003 - Load testing (high)

Estimated Total: 103,000 tokens
```

### Step 3.6: Visualize Task Dependencies

```bash
python3 framework/scripts/roadmap-query.py --dependencies --sprint backend-1
```

**Expected Output:**

```
Task Dependency Graph (backend-1):

backend-1-task-001 (Database schema) [READY]
├── backend-1-task-002 (Registration) [BLOCKED]
│   └── backend-1-task-004 (Password reset) [BLOCKED]
└── backend-1-task-003 (Login) [BLOCKED]
    └── backend-1-task-005 (Token refresh) [BLOCKED]

Completion Gates: 2 (all blocked until development tasks complete)
Production Gates: 3 (all blocked until completion gates pass)
```

**Key Points:**

- ✅ 10 tasks total (5 dev + 2 completion + 3 production)
- ✅ Task dependencies create a logical flow
- ✅ Only task-001 (database schema) is initially ready
- ✅ Quality gates enforce quality standards
- ✅ Clear separation: development → completion gates → production gates

---

## Phase 4: Working Through Tasks

Now let's work through the sprint, completing tasks in order.

### Step 4.1: Start the Sprint

```bash
python3 framework/scripts/roadmap-update.py --start-sprint backend-1
```

**Expected Output:**

```
✓ Sprint backend-1 status: not_started → in_progress
✓ Track backend status: not_started → in_progress
✓ Roadmap version: 0.1.0 → 0.2.0 (minor bump: first sprint started)

Sprint: backend-1 (User Authentication System)
Status: in_progress
Ready tasks: 1 (backend-1-task-001)
```

**What Changed:**

1. Sprint status: `not_started` → `in_progress`
2. Track status: `not_started` → `in_progress`
3. Roadmap version bumped: `0.1.0` → `0.2.0`
4. First task (001) is now ready to work on

### Step 4.2: Start First Task

```bash
python3 framework/scripts/roadmap-update.py --start-task backend-1-task-001
```

**Expected Output:**

```
✓ Task backend-1-task-001 status: not_started → in_progress
✓ Task file updated

Task: backend-1-task-001 (Database schema)
Status: in_progress
Started: 2025-11-09T10:30:00Z
No blockers
```

### Step 4.3: Simulate Work (Create Files)

In a real scenario, you'd implement the database schema. For this tutorial, we'll simulate:

```bash
# Create backend directory
mkdir -p src/backend/models

# Create schema file
cat > src/backend/models/user.py << 'EOF'
"""User database model."""
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    """User model for authentication."""
    __tablename__ = 'users'

    id = Column(String(26), primary_key=True)  # ULID
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
EOF

# Commit the work
git add src/backend/models/user.py
git commit -m "feat: Add user database model for authentication

Implements PostgreSQL schema for users table with:
- ULID-based IDs
- Email and password storage
- Email verification flag
- Timestamps

Related: backend-1-task-001"
```

### Step 4.4: Complete First Task

```bash
python3 framework/scripts/roadmap-update.py \
  --complete-task backend-1-task-001 \
  --commit $(git rev-parse HEAD)
```

**Expected Output:**

```
✓ Task backend-1-task-001 status: in_progress → completed
✓ Linked commit: abc123def456
✓ Sprint progress: 10% (1/10 tasks)
✓ Unblocked tasks: backend-1-task-002, backend-1-task-003

Task: backend-1-task-001 (Database schema)
Status: completed
Duration: 15 minutes
Commit: abc123def456

Next ready tasks:
  - backend-1-task-002 (Registration endpoint)
  - backend-1-task-003 (Login endpoint)
```

**What Changed:**

1. Task status: `in_progress` → `completed`
2. Sprint progress: 0% → 10%
3. Two tasks unblocked (002 and 003 both depend on 001)
4. Commit SHA linked to task for traceability

### Step 4.5: Work on Multiple Tasks in Parallel

Now that task-001 is complete, we can work on both task-002 and task-003 in parallel.

**Start both tasks:**

```bash
# Start registration endpoint
python3 framework/scripts/roadmap-update.py --start-task backend-1-task-002

# Start login endpoint
python3 framework/scripts/roadmap-update.py --start-task backend-1-task-003
```

**Expected Output:**

```
✓ Task backend-1-task-002 status: not_started → in_progress
✓ Task backend-1-task-003 status: not_started → in_progress

Sprint progress: 10% (1/10 completed, 2/10 in progress)
```

### Step 4.6: Complete Registration Endpoint

```bash
# Simulate implementation
mkdir -p src/backend/routes
cat > src/backend/routes/auth.py << 'EOF'
"""Authentication routes."""
from flask import Blueprint, request, jsonify
from src.backend.models.user import User
from src.backend.utils.email import send_verification_email

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration endpoint."""
    data = request.json

    # Validate input
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    # Create user
    user = User(email=email)
    user.set_password(password)

    # Send verification email
    send_verification_email(user)

    return jsonify({'message': 'Registration successful'}), 201
EOF

git add src/backend/routes/auth.py
git commit -m "feat: Implement user registration endpoint

POST /api/auth/register endpoint with:
- Email/password validation
- Password hashing
- Email verification flow

Related: backend-1-task-002"

# Complete the task
python3 framework/scripts/roadmap-update.py \
  --complete-task backend-1-task-002 \
  --commit $(git rev-parse HEAD)
```

**Expected Output:**

```
✓ Task backend-1-task-002 status: in_progress → completed
✓ Sprint progress: 20% (2/10 tasks)
✓ Unblocked tasks: backend-1-task-004

Next ready tasks:
  - backend-1-task-004 (Password reset) [depends on 002]
```

### Step 4.7: Fast-Forward Remaining Tasks

For tutorial purposes, let's fast-forward through the remaining development tasks.

```bash
# Complete login endpoint (task-003)
python3 framework/scripts/roadmap-update.py --complete-task backend-1-task-003
# This unblocks task-005

# Complete password reset (task-004)
python3 framework/scripts/roadmap-update.py --complete-task backend-1-task-004

# Complete token refresh (task-005)
python3 framework/scripts/roadmap-update.py --complete-task backend-1-task-005
```

**Check progress:**

```bash
python3 framework/scripts/roadmap-query.py --sprint backend-1
```

**Expected Output:**

```
Sprint: backend-1 (User Authentication System)
Status: in_progress
Progress: 50% (5/10 tasks)

Development Tasks: 5/5 completed ✓
Completion Gates: 0/2 completed
Production Gates: 0/3 completed
```

**Key Point:** Development tasks are complete, but sprint is still `in_progress` because quality gates haven't passed.

---

## Phase 5: Quality Gates

Quality gates enforce standards before moving forward.

### Step 5.1: Understanding Gate Blocking

Check what's blocking sprint completion:

```bash
python3 framework/scripts/roadmap-query.py --blockers --id backend-1
```

**Expected Output:**

```
Blockers for: backend-1

Status: in_progress (cannot transition to completed)

Blocking Issues:
  1. Completion gate not passed: backend-1-gate-c001 (API documentation)
  2. Completion gate not passed: backend-1-gate-c002 (Code review)

Completion gates MUST pass before sprint can be marked completed.
Production gates MUST pass before sprint can be marked production_ready.
```

### Step 5.2: Complete Completion Gates

**Gate C001: API Documentation**

```bash
# Start the gate task
python3 framework/scripts/roadmap-update.py --start-task backend-1-gate-c001

# Simulate creating documentation
cat > api-spec.yaml << 'EOF'
openapi: 3.0.0
info:
  title: Authentication API
  version: 1.0.0
paths:
  /api/auth/register:
    post:
      summary: Register new user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                email:
                  type: string
                password:
                  type: string
      responses:
        '201':
          description: User registered successfully
EOF

# Run the gate command (validation)
npx swagger-cli validate api-spec.yaml

# If validation passes, complete the gate
python3 framework/scripts/roadmap-update.py \
  --complete-task backend-1-gate-c001 \
  --gate-passed
```

**Expected Output:**

```
✓ Task backend-1-gate-c001 status: in_progress → completed
✓ Gate check: PASSED
✓ Sprint progress: 60% (6/10 tasks)

Completion gates: 1/2 passed
```

**Gate C002: Code Review**

```bash
# Start and complete code review
python3 framework/scripts/roadmap-update.py --start-task backend-1-gate-c002

# Simulate review process
# In real scenario: peer reviews code, leaves comments, approves

python3 framework/scripts/roadmap-update.py \
  --complete-task backend-1-gate-c002 \
  --gate-passed
```

**Expected Output:**

```
✓ Task backend-1-gate-c002 status: in_progress → completed
✓ Gate check: PASSED
✓ Sprint progress: 70% (7/10 tasks)

Completion gates: 2/2 passed ✓
Sprint can now be marked completed!
```

### Step 5.3: Check Sprint Status

```bash
python3 framework/scripts/roadmap-query.py --sprint backend-1
```

**Expected Output:**

```
Sprint: backend-1 (User Authentication System)
Status: in_progress
Progress: 70% (7/10 tasks)

Development Tasks: 5/5 completed ✓
Completion Gates: 2/2 completed ✓
Production Gates: 0/3 completed

Status: Ready for completion! (All completion gates passed)
Note: Production gates still needed for production_ready status
```

---

## Phase 6: Sprint Completion

### Step 6.1: Complete the Sprint

Now that all development tasks and completion gates are done, we can complete the sprint.

```bash
python3 framework/scripts/roadmap-update.py --complete-sprint backend-1
```

**Expected Output:**

```
✓ Sprint backend-1 status: in_progress → completed
✓ All completion gates passed
✓ Roadmap version: 0.2.0 → 0.3.0 (minor bump: sprint completed)

Sprint: backend-1 (User Authentication System)
Status: completed
Progress: 70% (7/10 tasks)
Completed: 2025-11-09T12:00:00Z
Duration: 1.5 hours

Note: Production gates not run (0/3 passed)
To deploy to production, run production gates and mark as production_ready
```

**What Changed:**

1. Sprint status: `in_progress` → `completed`
2. Roadmap version bumped: `0.2.0` → `0.3.0`
3. Sprint is functionally complete, but not production-ready yet

### Step 6.2: Understanding Status vs Production Readiness

```bash
python3 framework/scripts/roadmap-query.py --sprint backend-1
```

**Output:**

```
Sprint: backend-1 (User Authentication System)
Status: completed
Progress: 70% (7/10 development tasks + completion gates)

Development: ✓ Complete
Completion Gates: ✓ Passed
Production Gates: ✗ Not run (0/3)

Can deploy to staging: YES
Can deploy to production: NO (production gates required)
```

**Key Distinction:**

- **completed** = Development done, completion gates passed, ready for staging
- **production_ready** = Production gates also passed, ready for production

### Step 6.3: Run Production Gates

To deploy to production, we need to pass production gates.

**Gate P001: Unit Tests**

```bash
python3 framework/scripts/roadmap-update.py --start-task backend-1-gate-p001

# Simulate running tests
pytest --cov=src/auth --cov-report=term --cov-fail-under=90

# If tests pass
python3 framework/scripts/roadmap-update.py \
  --complete-task backend-1-gate-p001 \
  --gate-passed
```

**Expected Output:**

```
✓ Production gate backend-1-gate-p001: PASSED
✓ Coverage: 94% (exceeds 90% threshold)
✓ Sprint progress: 80% (8/10 tasks)

Production gates: 1/3 passed
```

**Gate P002: Security Audit**

```bash
python3 framework/scripts/roadmap-update.py --start-task backend-1-gate-p002

# Run security scan
bandit -r src/auth/

# If scan passes
python3 framework/scripts/roadmap-update.py \
  --complete-task backend-1-gate-p002 \
  --gate-passed
```

**Expected Output:**

```
✓ Production gate backend-1-gate-p002: PASSED
✓ No security issues found
✓ Sprint progress: 90% (9/10 tasks)

Production gates: 2/3 passed
```

**Gate P003: Load Testing**

```bash
python3 framework/scripts/roadmap-update.py --start-task backend-1-gate-p003

# Run load tests
k6 run load-tests/auth.js

# If load tests pass
python3 framework/scripts/roadmap-update.py \
  --complete-task backend-1-gate-p003 \
  --gate-passed
```

**Expected Output:**

```
✓ Production gate backend-1-gate-p003: PASSED
✓ All endpoints handle >1000 req/sec
✓ Sprint progress: 100% (10/10 tasks)

Production gates: 3/3 passed ✓
Sprint is now ready for production deployment!
```

### Step 6.4: Mark Sprint Production Ready

```bash
python3 framework/scripts/roadmap-update.py --mark-production-ready backend-1
```

**Expected Output:**

```
✓ Sprint backend-1 status: completed → production_ready
✓ All gates passed (2 completion + 3 production)
✓ Roadmap version: 0.3.0 → 1.0.0 (MAJOR bump: first production deployment)

Sprint: backend-1 (User Authentication System)
Status: production_ready
Progress: 100%
Ready for deployment: YES
```

**What Changed:**

1. Sprint status: `completed` → `production_ready`
2. Roadmap version: `0.3.0` → `1.0.0` (MAJOR bump for first production deployment)
3. Sprint is now safe to deploy to production

### Step 6.5: View Final Sprint Status

```bash
python3 framework/scripts/roadmap-query.py --sprint backend-1
```

**Expected Output:**

```
Sprint: backend-1 (User Authentication System)
Track: backend
Status: production_ready ✓
Progress: 100% (10/10 tasks)

Development Tasks: 5/5 completed ✓
Completion Gates: 2/2 passed ✓
Production Gates: 3/3 passed ✓

Completed: 2025-11-09T12:00:00Z
Production ready: 2025-11-09T13:30:00Z
Total duration: 1.5 hours

Commits: 5 linked commits
Ready for production deployment: YES
```

---

## Phase 7: Track Dependencies

Now that backend-1 is production-ready, let's see how this affects other tracks.

### Step 7.1: Check Track Dependencies

Remember: Frontend and Mobile tracks both depend on Backend track.

```bash
python3 framework/scripts/roadmap-query.py --blockers --id frontend
```

**Expected Output:**

```
Blockers for: frontend (Web Frontend)

Status: blocked

Blocking Issues:
  1. Track dependency: backend (required status: completed, current: in_progress)

Frontend track cannot start until Backend track is completed.
Backend track status: in_progress (1/3 sprints completed)
```

**Why Still Blocked:**

- Backend *track* is `in_progress` (not `completed`)
- backend-1 sprint is done, but there are more backend sprints
- Frontend must wait for the entire backend track

### Step 7.2: Create Second Backend Sprint

Let's create backend-2 to continue backend development.

```bash
python3 framework/scripts/roadmap-sprint.py create \
  --id "backend-2" \
  --track "backend" \
  --name "Product Catalog API" \
  --description "Products, categories, inventory management" \
  --depends-on "backend-1:completed"
```

**Expected Output:**

```
✓ Created sprint: backend-2
✓ Added dependency: backend-1 (must be completed)
✓ Sprint file: .vibey/sprints/backend-2.yaml

Sprint: backend-2 (Product Catalog API)
Status: not_started (dependency satisfied: backend-1 is completed)
Ready to start: YES
```

### Step 7.3: Create Third Backend Sprint

```bash
python3 framework/scripts/roadmap-sprint.py create \
  --id "backend-3" \
  --track "backend" \
  --name "Order Processing & Checkout" \
  --description "Shopping cart, checkout flow, payment integration" \
  --depends-on "backend-2:completed"
```

**Expected Output:**

```
✓ Created sprint: backend-3
✓ Added dependency: backend-2 (must be completed)
✓ Sprint file: .vibey/sprints/backend-3.yaml

Sprint: backend-3 (Order Processing & Checkout)
Status: blocked (waiting on: backend-2)
```

### Step 7.4: Fast-Forward Backend Track

For tutorial purposes, let's fast-forward the backend track completion.

```bash
# Start backend-2
python3 framework/scripts/roadmap-update.py --start-sprint backend-2

# Simulate completing all tasks
# (In reality, you'd go through the same process as backend-1)

# Complete backend-2
python3 framework/scripts/roadmap-update.py --complete-sprint backend-2

# Start backend-3
python3 framework/scripts/roadmap-update.py --start-sprint backend-3

# Complete backend-3
python3 framework/scripts/roadmap-update.py --complete-sprint backend-3

# Complete the backend track
python3 framework/scripts/roadmap-update.py --complete-track backend
```

**Expected Output:**

```
✓ Track backend status: in_progress → completed
✓ All sprints completed (3/3)
✓ Roadmap version: 1.0.0 → 1.1.0 (minor bump: track completed)
✓ Unblocked tracks: frontend, mobile

Track: backend (Backend API & Database)
Status: completed
Sprints: 3/3 completed
Progress: 100%
```

### Step 7.5: Check Frontend Track Status

```bash
python3 framework/scripts/roadmap-query.py --track frontend
```

**Expected Output:**

```
Track: frontend (Web Frontend)
Status: not_started (was blocked, now unblocked!)
Priority: high
Sprints: 0

Dependencies: backend (status: completed ✓)
Ready to start: YES
```

**What Changed:**

- Frontend track status: `blocked` → `not_started` (unblocked)
- Can now create and start frontend sprints
- Mobile track also unblocked

---

## Phase 8: Production Deployment

### Step 8.1: Check Production Readiness

```bash
python3 framework/scripts/roadmap-query.py --production-ready
```

**Expected Output:**

```
Production Ready Sprints:

backend-1 (User Authentication System)
  Status: production_ready
  All gates passed: YES
  Ready for deployment: YES

backend-2 (Product Catalog API)
  Status: completed
  Completion gates passed: YES
  Production gates passed: NO
  Ready for deployment: NO (run production gates first)

backend-3 (Order Processing & Checkout)
  Status: completed
  Completion gates passed: YES
  Production gates passed: NO
  Ready for deployment: NO (run production gates first)
```

**Key Points:**

- Only backend-1 is `production_ready`
- backend-2 and backend-3 are `completed` but haven't run production gates
- Each sprint can be deployed independently

### Step 8.2: Deploy to Production

```bash
# Simulate deployment
python3 framework/scripts/roadmap-deploy.py \
  --sprint backend-1 \
  --environment production \
  --version 1.0.0
```

**Expected Output:**

```
✓ Sprint backend-1 status: production_ready → deployed
✓ Deployment recorded
✓ Environment: production
✓ Version: 1.0.0
✓ Timestamp: 2025-11-09T14:00:00Z

Sprint: backend-1 (User Authentication System)
Status: deployed
Deployed to: production
Deployed at: 2025-11-09T14:00:00Z
```

### Step 8.3: View Deployment History

```bash
python3 framework/scripts/roadmap-query.py --deployments
```

**Expected Output:**

```
Deployment History:

2025-11-09 14:00:00 - backend-1 → production (v1.0.0)
  Sprint: User Authentication System
  Status: deployed
  All gates: PASSED
```

### Step 8.4: Check Overall Roadmap Status

```bash
python3 framework/scripts/roadmap-query.py
```

**Expected Output:**

```
Roadmap: ecommerce-platform (E-Commerce Platform)
Version: 1.1.0
Status: in_progress

Progress:
  Tracks: 1/4 completed (backend ✓)
  Sprints: 3/3 completed in backend track
  Tasks: 30/30 completed in backend sprints

Track Status:
  ✓ backend - completed (3/3 sprints)
  ○ frontend - not_started (ready)
  ○ mobile - not_started (ready)
  ○ infrastructure - not_started

Production Deployments: 1
  - backend-1 (User Authentication System) → production

Next Steps:
  1. Create frontend sprints (frontend track unblocked)
  2. Create mobile sprints (mobile track unblocked)
  3. Plan infrastructure deployment
```

---

## What You've Learned

### Core Concepts

✅ **Roadmap Hierarchy**
- Roadmap → Tracks → Sprints → Tasks
- Each level has dependencies and status
- Progress rolls up from tasks → sprints → tracks → roadmap

✅ **Task Types**
- **Development tasks** - Actual coding work
- **Completion gates** - Quality checks before completion
- **Production gates** - Quality checks before production

✅ **Status Progression**
- Tasks: `not_started` → `in_progress` → `completed`
- Sprints: `not_started` → `in_progress` → `completed` → `production_ready` → `deployed`
- Tracks: `not_started` → `in_progress` → `completed`

✅ **Dependencies**
- **Track dependencies** - Track A depends on Track B
- **Sprint dependencies** - Sprint 2 depends on Sprint 1
- **Task dependencies** - Task B depends on Task A
- **Blocking** - Dependencies prevent status transitions

✅ **Quality Gates**
- Automated or manual checks
- Can have validation commands
- Block progress until passed
- Enforce standards (testing, security, documentation)

✅ **Version Management**
- Semantic versioning (MAJOR.MINOR.PATCH)
- Auto-bumped based on milestones
- Tied to roadmap progress

### CLI Commands Mastered

```bash
# Initialization
roadmap-init.py              # Create new roadmap

# Object creation
roadmap-track.py create      # Create track
roadmap-sprint.py create     # Create sprint
roadmap-task.py create       # Create task

# Updates
roadmap-update.py --start-sprint       # Start sprint
roadmap-update.py --start-task         # Start task
roadmap-update.py --complete-task      # Complete task
roadmap-update.py --complete-sprint    # Complete sprint
roadmap-update.py --mark-production-ready  # Mark for production

# Queries
roadmap-query.py                      # Show roadmap summary
roadmap-query.py --track TRACK        # Show track
roadmap-query.py --sprint SPRINT      # Show sprint
roadmap-query.py --task TASK          # Show task
roadmap-query.py --blockers --id ID   # Show what's blocking
roadmap-query.py --dependencies       # Show dependency graph
```

### Best Practices

✅ **Planning**
- Start with tracks for major work streams
- Plan sprints with clear goals
- Break work into context-window sized tasks
- Define quality gates early

✅ **Dependencies**
- Use track dependencies for major blocking
- Use sprint dependencies for sequential work
- Use task dependencies for ordering within sprint
- Check blockers regularly

✅ **Quality Gates**
- Add completion gates for hygiene (docs, review)
- Add production gates for safety (tests, security)
- Use gate commands for automation
- Don't skip gates to save time

✅ **Version Management**
- Let versions auto-bump based on milestones
- Use semantic versioning correctly
- Track versions per deployment

✅ **Workflow**
1. Plan → Define tracks and sprints
2. Build → Complete development tasks
3. Review → Pass completion gates
4. Test → Pass production gates
5. Deploy → Mark production ready and deploy

---

## Next Steps

### Continue This Tutorial

1. **Create Frontend Sprint**
   - Plan frontend-1 for React app
   - Add tasks for components, routing, state
   - Define frontend-specific quality gates

2. **Create Mobile Sprint**
   - Plan mobile-1 for iOS/Android
   - Add tasks for screens, navigation, API integration
   - Define mobile-specific quality gates

3. **Create Infrastructure Sprint**
   - Plan infrastructure-1 for AWS deployment
   - Add tasks for Terraform, monitoring, CI/CD
   - Define infrastructure quality gates

### Explore Advanced Features

1. **Complex Dependencies**
   - Create cross-track dependencies
   - Handle dependency chains
   - Manage blockers

2. **Quality Gate Automation**
   - Write automated gate commands
   - Integrate with CI/CD
   - Custom validation scripts

3. **Reporting**
   - Generate progress reports
   - Track velocity and estimates
   - Analyze sprint metrics

### Real-World Usage

1. **Start Your Own Project**
   - Initialize roadmap for your project
   - Plan your first sprint
   - Use quality gates to enforce standards

2. **Integrate with Tools**
   - Link to GitHub issues
   - Integrate with CI/CD pipelines
   - Generate reports for stakeholders

3. **Team Workflow**
   - Define team conventions
   - Establish gate standards
   - Create reusable sprint templates

---

## Reference

### Quick Command Reference

```bash
# Show overall status
python3 framework/scripts/roadmap-query.py

# Show what's ready to work on
python3 framework/scripts/roadmap-query.py --ready-tasks

# Show what's blocked
python3 framework/scripts/roadmap-query.py --blockers

# Start working
python3 framework/scripts/roadmap-update.py --start-task TASK_ID

# Complete task
python3 framework/scripts/roadmap-update.py --complete-task TASK_ID

# Check sprint progress
python3 framework/scripts/roadmap-query.py --sprint SPRINT_ID
```

### Common Patterns

**Creating a Sprint:**
1. Create sprint with `roadmap-sprint.py create`
2. Add development tasks with `roadmap-task.py create`
3. Add completion gates
4. Add production gates
5. Start sprint with `roadmap-update.py --start-sprint`

**Working Through a Sprint:**
1. Check ready tasks: `roadmap-query.py --sprint SPRINT_ID`
2. Start task: `roadmap-update.py --start-task TASK_ID`
3. Do the work, commit changes
4. Complete task: `roadmap-update.py --complete-task TASK_ID --commit SHA`
5. Repeat until all development tasks done

**Completing a Sprint:**
1. Complete all development tasks
2. Run completion gates
3. Complete sprint: `roadmap-update.py --complete-sprint SPRINT_ID`
4. Run production gates
5. Mark production ready: `roadmap-update.py --mark-production-ready SPRINT_ID`

### File Structure Reference

```
.vibey/
├── roadmap.yaml              # Root roadmap file
├── tracks/
│   └── TRACK_ID.yaml         # One file per track
├── sprints/
│   └── SPRINT_ID.yaml        # One file per sprint
└── tasks/
    └── SPRINT_ID-tasks.yaml  # One file per sprint's tasks
```

---

## Troubleshooting

### Common Issues

**"Track is blocked"**
- Check track dependencies: `roadmap-query.py --track TRACK_ID`
- Complete prerequisite tracks first

**"Sprint can't be completed"**
- Check blockers: `roadmap-query.py --blockers --id SPRINT_ID`
- Complete all completion gates

**"Task is blocked"**
- Check task dependencies: `roadmap-query.py --task TASK_ID`
- Complete prerequisite tasks first

**"Version not bumping"**
- Versions only bump on significant milestones
- Check version bump triggers in DESIGN_DECISIONS.md

### Getting Help

- **User Guide:** `docs/guides/ROADMAP_USER_GUIDE.md`
- **CLI Reference:** `docs/guides/ROADMAP_CLI_REFERENCE.md`
- **Design Decisions:** `framework/roadmap/DESIGN_DECISIONS.md`

---

## Conclusion

Congratulations! You've completed the E-Commerce Platform roadmap tutorial.

**You now know how to:**
- ✅ Initialize roadmaps
- ✅ Create tracks, sprints, and tasks
- ✅ Manage dependencies
- ✅ Use quality gates
- ✅ Work through the development lifecycle
- ✅ Deploy to production safely

**Key Takeaways:**
1. **Structure** - Hierarchy keeps work organized
2. **Dependencies** - Explicit blocking prevents mistakes
3. **Quality Gates** - Automated checks enforce standards
4. **Traceability** - Everything is linked (commits, versions, deployments)
5. **Flexibility** - System adapts to your workflow

**Ready to build your own roadmap!** 🚀

---

**Tutorial Version:** 2.1
**Last Updated:** 2025-11-09
**Estimated Duration:** 60 minutes
**Difficulty:** Beginner to Intermediate
