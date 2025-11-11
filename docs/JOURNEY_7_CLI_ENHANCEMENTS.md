# Journey 7 CLI Enhancements

This document contains the enhanced content for Journey 7 (Roadmap-Driven Development) in VIBEY_USER_JOURNEYS.md, adding the new `vibey roadmap` CLI commands based on the gap analysis.

## Summary of Changes

The following sections should be added/modified in Journey 7 to include the new CLI commands:

### 1. Step 7.1: Initialize Roadmap (ADD Option A)

**Insert BEFORE existing content:**

```markdown
### Step 7.1: Initialize Roadmap

**Option A: Using CLI Command**
```bash
# Initialize roadmap with basic settings
vibey roadmap init --name "Q1 Product Roadmap" --version "1.0"
```

**CLI Output:**
```
✓ Roadmap initialized: .vibey/roadmap.yaml
✓ Created directory: .vibey/tracks/
✓ Created directory: .vibey/sprints/
✓ Created directory: .vibey/tasks/

Roadmap: Q1 Product Roadmap (v1.0)
Status: Empty - ready for tracks

Next steps:
  1. Define tracks in .vibey/tracks/*.yaml
  2. Or let Claude help plan your tracks
```

**Option B: Using Natural Language (Claude Code)**
```
User: Set up a product roadmap for the next quarter
```
```

### 2. Step 7.4: Start Track - User Management (ADD Option A)

**Insert BEFORE existing content:**

```markdown
### Step 7.4: Start Track - User Management

**Option A: Using CLI Commands**
```bash
# Check current status
vibey roadmap status

# Start the first sprint of the track
vibey roadmap start user-mgmt-1-auth
```

**CLI Output:**
```
Starting sprint: user-mgmt-1-auth (Authentication)

Status changed: not_started → in_progress
Started at: 2025-11-10T15:30:00Z
Track: user-management

Sprint tasks (4):
  1. task-001: User registration API
  2. task-002: Login/logout endpoints
  3. task-003: Password reset flow
  4. task-004: OAuth integration

✓ Sprint started successfully
```

**Option B: Using Natural Language (Claude Code)**
```
User: Start the user management track
```
```

### 3. Step 7.5: Track Progress Over Time (REPLACE)

**REPLACE the existing "Checking Progress" section with:**

```markdown
### Step 7.5: Track Progress with New CLI Commands

**Using Modern CLI Commands:**
```bash
# Check overall roadmap status
vibey roadmap status

# Check specific track status
vibey roadmap status --track user-management

# Check specific sprint status
vibey roadmap status --sprint user-mgmt-2-profiles

# Show detailed information about a sprint
vibey roadmap show user-mgmt-1-auth

# Get AI-optimized context for a specific task
vibey roadmap context task-001

# Summarize a sprint
vibey roadmap summarize sprint user-mgmt-1-auth
```

**Example: `vibey roadmap status` Output:**
```
============================================================
Roadmap: Your Project Development Roadmap
============================================================
Progress: 18% (2/11 sprints complete)

🛤️  Tracks:
  🔵 in_progress User Management System (user-management)
     Sprints: 1/3 complete
     Current: user-mgmt-2-profiles

  ⚪ not_started Payment Integration (payment-integration)
     Blocked by: user-management

  ⚪ not_started Performance Optimization (performance)

  ⚪ not_started Mobile App Development (mobile-app)
     Blocked by: user-management, payment-integration

Recent Activity:
────────────────
2025-11-12 - Completed user-mgmt-1-auth
2025-11-10 - Started user-management track
2025-11-10 - Created roadmap
```

**Example: `vibey roadmap show user-mgmt-1-auth` Output:**
```
Sprint: user-mgmt-1-auth (Authentication)
════════════════════════════════════════════════════

Status: completed
Track: user-management
Duration: 1.5 weeks
Started: 2025-11-10T15:30:00Z
Completed: 2025-11-12T14:20:00Z

Tasks (4):
  ✅ task-001: User registration API (completed)
  ✅ task-002: Login/logout endpoints (completed)
  ✅ task-003: Password reset flow (completed)
  ✅ task-004: OAuth integration (completed)

Quality Gates:
  ✅ Security audit: 92/100 (passed)
  ✅ Test coverage: 88% (passed)
  ✅ Performance: 90/100 (passed)

Artifacts:
  - .vibey/sprint_docs/user-mgmt-1-auth/PLAN.md
  - .vibey/sprint_docs/user-mgmt-1-auth/COMPLETION.md
  - .vibey/sprint_docs/user-mgmt-1-auth/audits/
```

**Example: `vibey roadmap context task-001` Output:**
```
Task Context for AI Assistant
══════════════════════════════════════════════════

Task: task-001 (User registration API)
Sprint: user-mgmt-1-auth (Authentication)
Track: user-management

Description:
  Build REST API endpoint for user registration with email
  verification and password validation.

Prerequisites:
  - Database schema defined
  - Email service configured
  - Validation library installed

Related Tasks:
  - task-002: Login/logout endpoints (depends on this)
  - task-003: Password reset flow (depends on this)

Files to Modify:
  - src/api/auth.py
  - src/models/user.py
  - tests/test_auth.py

Quality Requirements:
  - Security: Input validation, password hashing
  - Testing: Unit tests, integration tests
  - Documentation: API docs, error codes
```
```

### 4. NEW SECTION: Step 7.5a: Complete Sprints and Tasks

**INSERT AFTER Step 7.5, BEFORE Step 7.6:**

```markdown
### Step 7.5a: Complete Sprints and Tasks

**Complete a task:**
```bash
# Mark a task as complete
vibey roadmap complete task-001
```

**Output:**
```
✓ Task completed: task-001 (User registration API)
✓ Status changed: in_progress → completed
✓ Completed at: 2025-11-11T16:45:00Z

Sprint progress: 1/4 tasks completed (25%)
```

**Complete a sprint (with quality gates):**
```bash
# Complete sprint - runs quality gates automatically
vibey roadmap complete user-mgmt-1-auth
```

**Output:**
```
Running quality gates for user-mgmt-1-auth...

  ✓ Security audit: 92/100 (threshold: 85) PASSED
  ✓ Test coverage: 88% (threshold: 80%) PASSED
  ✓ Performance: 90/100 (threshold: 85) PASSED

All quality gates passed!

✓ Sprint completed: user-mgmt-1-auth (Authentication)
✓ Status changed: in_progress → completed
✓ Completed at: 2025-11-12T14:20:00Z
✓ Duration: 1.5 weeks

Track progress: 1/3 sprints completed (33%)

Next sprint: user-mgmt-2-profiles (User Profiles)
Ready to start? [Y/n]
```

**Sprint Progression Workflow:**
```
not_started
    ↓ (vibey roadmap start <sprint-id>)
in_progress
    ↓ (vibey roadmap complete <sprint-id>)
completion_gate_check
    ↓ (quality gates pass)
completed

If quality gates fail:
completion_gate_check → in_progress (fix issues and retry)
```

**Working with Tasks:**
```bash
# Start a task
vibey roadmap start task-001

# Get context for a task (useful for AI assistants)
vibey roadmap context task-001

# Complete a task
vibey roadmap complete task-001

# Summarize task progress
vibey roadmap summarize task task-001
```
```

### 5. Step 7.7: Dependency Management (ADD CLI examples)

**ADD after existing dependency content:**

```markdown
**Using CLI to Check Dependencies:**
```bash
# Check if tracks are blocked
vibey roadmap status

# Show details of a blocked track
vibey roadmap show payment-integration
```

**Example Output:**
```
Track: payment-integration (Payment Integration)
════════════════════════════════════════════════════

Status: not_started
Priority: high
Dependencies:
  ❌ user-management (Status: in_progress) - BLOCKING

Cannot start: dependencies not met

Estimated duration: 2 weeks
Sprints: 2 (payment-1-setup, payment-2-processing)
```

**After Dependency Resolved:**
```bash
vibey roadmap show payment-integration
```

**Output:**
```
Track: payment-integration (Payment Integration)
════════════════════════════════════════════════════

Status: ready_to_start
Priority: high
Dependencies:
  ✅ user-management (Status: completed)

✓ All dependencies met - ready to start!

Estimated duration: 2 weeks
Sprints: 2 (payment-1-setup, payment-2-processing)

Start this track? Run: vibey roadmap start payment-1-setup
```
```

## Complete CLI Command Reference for Journey 7

### Initialization
```bash
vibey roadmap init [--name <name>] [--version <version>]
```

### Status & Information
```bash
vibey roadmap status                           # Overall roadmap status
vibey roadmap status --track <track-id>        # Track-specific status
vibey roadmap status --sprint <sprint-id>      # Sprint-specific status
vibey roadmap show <item-id>                   # Detailed item info
```

### Starting Items
```bash
vibey roadmap start <sprint-id>    # Start a sprint
vibey roadmap start <task-id>      # Start a task
```

### Completing Items
```bash
vibey roadmap complete <sprint-id>  # Complete sprint (runs quality gates)
vibey roadmap complete <task-id>    # Complete a task
```

### AI Assistant Integration
```bash
vibey roadmap context <task-id>     # Get AI-optimized task context
vibey roadmap summarize sprint <sprint-id>   # Summarize a sprint
vibey roadmap summarize task <task-id>       # Summarize a task
vibey roadmap summarize track <track-id>     # Summarize a track
```

## Location Information

- **File to modify:** `/Users/fredabood/Repositories/vibey/docs/VIBEY_USER_JOURNEYS.md`
- **Journey 7 starts at:** Line 2586
- **Step 7.1 starts at:** Line 2598
- **Step 7.4 starts at:** Line 2768
- **Step 7.5 starts at:** Line 2821
- **Step 7.6 starts at:** Line 2858

## Impact

These enhancements address the gaps identified in `USER_JOURNEY_GAP_ANALYSIS.md` for Journey 7/Journey 9:

- ✅ Documented `vibey roadmap init`
- ✅ Documented `vibey roadmap status` (with filtering options)
- ✅ Documented `vibey roadmap start`
- ✅ Documented `vibey roadmap complete`
- ✅ Documented `vibey roadmap show`
- ✅ Documented `vibey roadmap context`
- ✅ Documented `vibey roadmap summarize`
- ✅ Added dependency management workflow examples
- ✅ Added sprint progression workflow diagram
- ✅ Provided both CLI and natural language options for each step

## Priority

**HIGH** - These are core roadmap system features that users need to effectively use the framework for long-term project planning.
