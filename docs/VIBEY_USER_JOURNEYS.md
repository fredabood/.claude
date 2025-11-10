# Vibey User Journeys - Comprehensive Guide

**Version:** 1.3.0
**Last Updated:** 2025-11-10
**Status:** Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Journey Map](#journey-map)
3. [Journey 1: First-Time Setup](#journey-1-first-time-setup)
4. [Journey 2: Sprint Planning & Execution](#journey-2-sprint-planning--execution)
5. [Journey 3: Feature Development](#journey-3-feature-development)
6. [Journey 4: Quality Assurance & Review](#journey-4-quality-assurance--review)
7. [Journey 5: Framework Management](#journey-5-framework-management)
8. [Journey 6: Multi-Platform Deployment](#journey-6-multi-platform-deployment)
9. [Journey 7: Roadmap-Driven Development](#journey-7-roadmap-driven-development)
10. [Common Decision Points](#common-decision-points)
11. [Troubleshooting Journeys](#troubleshooting-journeys)
12. [Advanced Scenarios](#advanced-scenarios)

---

## Overview

This guide documents every possible path a user can take through Vibey's functionality, from initial setup to advanced multi-platform deployment. Each journey includes:

- **Step-by-step instructions**
- **Expected repository state** at each step
- **Git history snapshots**
- **Agent interactions**
- **Decision points and alternatives**

### User Types

Vibey serves four primary user personas:

1. **First-Time User** - Setting up Vibey for the first time
2. **Active Developer** - Using Vibey for daily development
3. **Framework Maintainer** - Managing Vibey configuration
4. **Multi-Platform User** - Deploying across multiple AI platforms

---

## Journey Map

```
┌─────────────────────────────────────────────────────────────┐
│                    VIBEY USER JOURNEYS                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Entry Point:    │
                    │  /vibey command  │
                    └──────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
    ┌──────────────────┐          ┌──────────────────┐
    │  NEW PROJECT     │          │  EXISTING        │
    │  (Initialize)    │          │  PROJECT         │
    └──────────────────┘          │  (Manage)        │
              │                   └──────────────────┘
              │                             │
              ▼                             ▼
    ┌──────────────────┐          ┌──────────────────┐
    │  JOURNEY 1:      │          │  JOURNEY 5:      │
    │  First-Time      │          │  Framework       │
    │  Setup           │          │  Management      │
    └──────────────────┘          └──────────────────┘
              │
              └─────────────┬─────────────┐
                            ▼             ▼
                  ┌──────────────┐  ┌──────────────┐
                  │  JOURNEY 2:  │  │  JOURNEY 7:  │
                  │  Sprint      │  │  Roadmap     │
                  │  Planning    │  │  Development │
                  └──────────────┘  └──────────────┘
                            │             │
                            └──────┬──────┘
                                   ▼
                         ┌──────────────────┐
                         │  JOURNEY 3:      │
                         │  Feature         │
                         │  Development     │
                         └──────────────────┘
                                   │
                                   ▼
                         ┌──────────────────┐
                         │  JOURNEY 4:      │
                         │  Quality         │
                         │  Assurance       │
                         └──────────────────┘
```

---

## Journey 1: First-Time Setup

**Goal:** Initialize Vibey in a new or existing project
**Duration:** 15-30 minutes
**Prerequisites:** Git repository, Claude Code (or target platform)

### Overview

This journey covers the complete initialization process from cloning Vibey to completing your first sprint plan.

---

### Step 1.1: Navigate to Your Project

**Action:**
```bash
cd /path/to/your-project
```

**Expected Repository State:**
```
your-project/
├── src/                    # Your existing code
├── package.json            # Your project files
├── .git/                   # Initialized git repo
└── README.md
```

**Git Status:**
```bash
$ git status
On branch main
Your branch is up to date with 'origin/main'.
nothing to commit, working tree clean
```

**Why This Matters:** Vibey integrates with your existing project structure without disrupting it.

---

### Step 1.2: Clone Vibey Framework

**Action:**
```bash
git clone https://github.com/fredabood/vibey.git .vibey
cd .vibey
```

**Expected Repository State:**
```
your-project/
├── src/
├── .vibey/                 # ✨ NEW: Vibey framework
│   ├── framework/          # Core framework files
│   ├── config/             # Configuration templates
│   ├── templates/          # Document templates
│   ├── scripts/            # Python utilities
│   └── README.md
├── .git/
└── package.json
```

**Git Status:**
```bash
$ git status
On branch main
Untracked files:
  .vibey/

$ cat .gitignore
# Add to your .gitignore:
.vibey/.git/
.claude/
.goose/
```

**Important Notes:**
- `.vibey/` is your permanent configuration directory
- `.claude/`, `.goose/` are platform deployments (gitignored)
- Vibey has its own git history (submodule-like)

---

### Step 1.3: Deploy to Platform (Claude Code)

**Action:**
```bash
./vibey deploy --platform claude-code
```

**What Happens:**
```
🚀 Vibey Deployment Engine
═══════════════════════════════════════

✓ Detected project type: web-app (Next.js, React)
✓ Analyzing codebase structure...
✓ Generating platform configuration...
✓ Creating .claude/ deployment...

📦 Deployment Summary:
   Platform: claude-code
   Agents: 12 specialized agents
   Workflows: 16 workflows
   Templates: 22 handoff templates

✓ Deployment complete!

📋 Next Steps:
   1. Run: /vibey in Claude Code
   2. Choose: Initialize project
   3. Follow guided setup
```

**Expected Repository State:**
```
your-project/
├── src/
├── .vibey/                 # Source configuration
│   ├── config/
│   │   ├── project.yaml    # ✨ NEW: Generated project config
│   │   ├── framework.yaml  # Framework settings
│   │   └── agents/         # Agent configurations
│   ├── roadmap.yaml        # ✨ NEW: Empty roadmap
│   └── framework/
├── .claude/                # ✨ NEW: Claude Code deployment
│   ├── CLAUDE.md           # Main context file (auto-read)
│   ├── agents/             # 12 agent markdown files
│   ├── workflows/          # 16 workflow markdown files
│   └── commands/           # /vibey command
├── .git/
└── .gitignore              # ✨ UPDATED: Ignores .claude/
```

**Git Status:**
```bash
$ git status
On branch main
Changes not staged for commit:
  modified:   .gitignore

Untracked files:
  .vibey/config/project.yaml
  .vibey/roadmap.yaml

# Note: .claude/ is gitignored (regenerable from .vibey/)
```

---

### Step 1.4: Initialize in Claude Code

**Action in Claude Code:**
```
User: /vibey
```

**Claude's Response:**
```
🎯 Vibey Framework Initialization

I see this is a new project. Let me help you set up Vibey!

📊 Project Analysis:
   Type: Web Application
   Stack: Next.js, React, TypeScript
   Database: PostgreSQL
   Testing: Jest, React Testing Library

Would you like to proceed with initialization?
```

**User Response:**
```
User: yes
```

---

### Step 1.5: Configuration Discovery (Interactive)

**Claude Asks Questions:**

**Q1: Project Type Confirmation**
```
I detected this is a web-app project. Is this correct?

Options:
1. ✅ Yes - Web Application
2. API Service
3. ML/Data Project
4. Infrastructure/DevOps
5. Other

Your choice:
```

**User Response:** `1` (or just "yes")

**Q2: Tech Stack Confirmation**
```
Detected tech stack:
- Framework: Next.js 14
- Language: TypeScript
- Styling: Tailwind CSS
- Database: PostgreSQL
- ORM: Prisma

Is this accurate? [Y/n]:
```

**User Response:** `Y`

**Q3: Orchestration Mode**
```
Choose orchestration mode:

1. Simple - Explicit agent selection (keywords like "security", "performance")
2. Balanced - Smart pattern matching (recommended for most projects)
3. Tiered - Coordinator agent routes all requests

Recommended: Balanced

Your choice [1-3]:
```

**User Response:** `2` (Balanced - recommended)

**Q4: Quality Gates**
```
Enable quality gates? These enforce standards before completion.

Quality gates available:
- Security review (recommended)
- Test coverage minimum
- Performance benchmarks
- Documentation completeness
- Logging standards

Enable quality gates? [Y/n]:
```

**User Response:** `Y`

---

### Step 1.6: Configuration Generation

**What Happens:**
```
✓ Generating project configuration...
✓ Creating .vibey/config/project.yaml
✓ Updating .claude/CLAUDE.md with project context
✓ Configuring agents for your stack
✓ Setting up workflows

📝 Configuration Summary:
   Project: your-project-name
   Type: web-app
   Orchestration: balanced
   Quality Gates: enabled (5 gates)
   Agents: 12 configured
   Workflows: 16 available
```

**Expected Repository State:**
```
.vibey/config/project.yaml:
───────────────────────────
project:
  name: your-project-name
  type: web-app
  tech_stack:
    framework: nextjs
    language: typescript
    styling: tailwind
    database: postgresql
    orm: prisma
  orchestration:
    mode: balanced
    coordinator_enabled: false
  quality_gates:
    enabled: true
    gates:
      - security_review
      - test_coverage
      - performance
      - documentation
      - logging
  agents:
    - web-developer
    - security-reviewer
    - performance-engineer
    # ... etc
```

**Git Status:**
```bash
$ git status
On branch main
Changes not staged for commit:
  modified:   .gitignore

Untracked files:
  .vibey/config/project.yaml
  .vibey/config/framework.yaml
  .vibey/roadmap.yaml

# .claude/ still gitignored
```

---

### Step 1.7: Initial Commit

**Action:**
```bash
git add .vibey/config/ .vibey/roadmap.yaml .gitignore
git commit -m "feat: Initialize Vibey framework

- Add project configuration
- Configure 12 specialized agents
- Enable quality gates
- Set up roadmap system

Framework version: 1.3.0
Orchestration mode: balanced"
```

**Git Log:**
```bash
$ git log --oneline -1
a1b2c3d feat: Initialize Vibey framework
```

**Repository State Now:**
```
✓ Vibey initialized
✓ Configuration committed
✓ Claude Code deployment ready
✓ Ready for sprint planning
```

---

### Step 1.8: Optional - Codebase Audit

**Action in Claude Code:**
```
User: Can you audit my codebase before we start planning?
```

**Claude's Response:**
```
I'll run a comprehensive codebase audit using the codebase-audit-discovery workflow.

🔍 Analyzing your project...

This will:
1. Analyze code structure and architecture
2. Identify patterns and conventions
3. Detect technical debt
4. Review dependencies
5. Generate recommendations

Proceed with audit? [Y/n]:
```

**User Response:** `Y`

**What Happens:**
```
Running codebase audit workflow...

✓ Step 1/5: Repository structure analysis
   - 47 TypeScript files
   - 23 React components
   - 12 API routes
   - 8 database models

✓ Step 2/5: Architecture pattern detection
   - Pattern: Next.js App Router
   - State management: React Context + hooks
   - API layer: tRPC

✓ Step 3/5: Code quality analysis
   - TypeScript coverage: 94%
   - Test coverage: 67%
   - ESLint issues: 12 warnings

✓ Step 4/5: Dependency analysis
   - Total dependencies: 34
   - Outdated packages: 3
   - Security vulnerabilities: 0

✓ Step 5/5: Generating recommendations

📊 Audit complete! Saving to .vibey/summaries/codebase-audit.md
```

**Expected Repository State:**
```
.vibey/
├── summaries/
│   └── codebase-audit.md    # ✨ NEW: 500+ line audit report
└── config/
    └── project.yaml         # ✨ UPDATED: Auto-detected patterns
```

**Git Status:**
```bash
$ git status
Untracked files:
  .vibey/summaries/codebase-audit.md

$ git add .vibey/summaries/
$ git commit -m "docs: Add codebase audit report

Generated by Vibey codebase-audit-discovery workflow

Key findings:
- TypeScript coverage: 94%
- Test coverage: 67% (recommend 80%)
- 3 outdated dependencies to update"
```

---

### Step 1.9: First Sprint Planning (Optional)

**Action in Claude Code:**
```
User: Let's plan our first sprint
```

**Claude's Response:**
```
🎯 Sprint Planning

I'll help you plan your first sprint using the sprint-planning workflow.

First, what would you like to accomplish in this sprint?

Examples:
- Build a new feature (e.g., "user authentication")
- Fix technical debt (e.g., "improve test coverage")
- Refactor (e.g., "migrate to App Router")
- Performance (e.g., "optimize page load times")

What's your focus?
```

**User Response:** `Add user authentication system`

**Sprint Planning Workflow Begins** (See Journey 2 for full details)

---

### Step 1.10: Journey 1 Complete

**Final Repository State:**
```
your-project/
├── src/                    # Your application code
├── .vibey/                 # ✅ Vibey configuration (committed)
│   ├── config/
│   │   ├── project.yaml    # Project configuration
│   │   ├── framework.yaml  # Framework settings
│   │   └── agents/         # Agent configs
│   ├── roadmap.yaml        # Roadmap system (may be empty)
│   ├── summaries/          # Optional: audit reports
│   └── framework/          # Core framework
├── .claude/                # Claude Code deployment (gitignored)
│   ├── CLAUDE.md           # Auto-generated context
│   ├── agents/             # 12 agent files
│   ├── workflows/          # 16 workflow files
│   └── commands/           # /vibey command
├── .git/
├── .gitignore              # ✅ Updated
└── package.json
```

**Git History:**
```bash
$ git log --oneline -3
b2c3d4e docs: Add codebase audit report
a1b2c3d feat: Initialize Vibey framework
9z8y7x6 Previous commit before Vibey
```

**✅ Success Criteria:**
- ✅ Vibey initialized and configured
- ✅ Configuration committed to git
- ✅ Claude Code deployment working
- ✅ Ready to start development

**Next Steps:**
- Proceed to Journey 2 (Sprint Planning) OR
- Proceed to Journey 3 (Feature Development) OR
- Proceed to Journey 7 (Roadmap-Driven Development)

---

## Journey 2: Sprint Planning & Execution

**Goal:** Plan and execute a complete development sprint
**Duration:** 1-2 weeks (sprint duration)
**Prerequisites:** Vibey initialized (Journey 1 complete)

### Overview

This journey covers planning a sprint, breaking down work into tasks, tracking progress, and completing the sprint with quality gates.

---

### Step 2.1: Initiate Sprint Planning

**Action in Claude Code:**
```
User: /vibey
```

**Claude Detects Existing Setup:**
```
🎯 Vibey Framework (Initialized)

I see you have Vibey set up. What would you like to do?

Options:
1. Plan a new sprint
2. Continue current sprint
3. Review sprint progress
4. Manage framework configuration
5. Other

Your choice:
```

**User Response:** `1` (Plan a new sprint)

---

### Step 2.2: Sprint Goal Definition

**Claude Asks:**
```
📋 Sprint Planning - Goal Definition

What's the main goal for this sprint? Be specific about what you want to accomplish.

Examples:
- "Build user authentication with email/password and OAuth"
- "Migrate database from MongoDB to PostgreSQL"
- "Implement real-time notifications system"
- "Improve page load performance by 50%"

Your sprint goal:
```

**User Response:** `Build user authentication with email/password and OAuth`

**Claude Acknowledges:**
```
✓ Sprint Goal: Build user authentication with email/password and OAuth

📊 Initial Analysis:
   Complexity: High
   Estimated: 5-8 days
   Required agents: web-developer, security-reviewer
   Workflows: feature-development, security-hardening

Let me break this down into tasks...
```

---

### Step 2.3: Task Breakdown

**Claude Generates Tasks:**
```
📋 Proposed Sprint Tasks:

Development Tasks:
─────────────────
1. Set up authentication database schema
   - User table with email, password_hash
   - Session management
   - OAuth provider table
   Estimated: 4 hours
   Agent: web-developer

2. Implement password authentication
   - Hash passwords with bcrypt
   - Login/logout endpoints
   - Session management
   Estimated: 6 hours
   Agent: web-developer

3. Implement OAuth integration
   - Google OAuth setup
   - GitHub OAuth setup
   - OAuth callback handling
   Estimated: 8 hours
   Agent: web-developer

4. Build authentication UI
   - Login form
   - Registration form
   - OAuth buttons
   Estimated: 6 hours
   Agent: web-developer

Quality Tasks:
──────────────
5. Security review
   - Password hashing validation
   - Session security audit
   - OAuth implementation review
   Estimated: 3 hours
   Agent: security-reviewer

6. Write authentication tests
   - Unit tests for auth logic
   - Integration tests for endpoints
   - E2E tests for flows
   Estimated: 5 hours
   Agent: web-developer

7. Documentation
   - API documentation
   - Authentication flow diagrams
   - Setup instructions
   Estimated: 2 hours
   Agent: documentation-engineer

Total Estimated: 34 hours (~4-5 days)

Does this breakdown look good? [Y/n/edit]:
```

**User Options:**

**Option A - Accept:** `Y`
**Option B - Modify:** `edit` → Interactive editing
**Option C - Reject:** `n` → Start over

**User Response:** `Y`

---

### Step 2.4: Sprint State Creation

**Claude Creates Sprint:**
```
✓ Creating sprint state...

📁 Sprint Files Created:
   .vibey/sprints/auth-sprint-1.yaml
   .vibey/sprint_docs/auth-sprint-1/PLAN.md
   .vibey/sprint_docs/auth-sprint-1/TASKS.md

Sprint ID: auth-sprint-1
Status: planning
Tasks: 7
Start Date: 2025-11-10
Target End: 2025-11-17
```

**Expected Repository State:**
```
.vibey/
├── sprints/
│   └── auth-sprint-1.yaml       # ✨ NEW: Sprint state tracking
├── sprint_docs/
│   └── auth-sprint-1/           # ✨ NEW: Sprint documentation
│       ├── PLAN.md              # Sprint plan
│       ├── TASKS.md             # Task details
│       └── PROGRESS.md          # Progress tracking (created later)
└── roadmap.yaml                 # ✨ UPDATED: Sprint registered
```

**Sprint State File (.vibey/sprints/auth-sprint-1.yaml):**
```yaml
sprint:
  id: auth-sprint-1
  name: "User Authentication Implementation"
  goal: "Build user authentication with email/password and OAuth"
  status: planning
  created: 2025-11-10T10:00:00Z
  started: null
  completed: null

  tasks:
    - id: auth-sprint-1-task-001
      title: "Set up authentication database schema"
      status: not_started
      assigned_agent: web-developer
      estimated_hours: 4

    - id: auth-sprint-1-task-002
      title: "Implement password authentication"
      status: not_started
      assigned_agent: web-developer
      estimated_hours: 6
      dependencies:
        - auth-sprint-1-task-001

    # ... remaining tasks

  quality_gates:
    - name: security_review
      status: not_run
      blocking: true
    - name: test_coverage
      status: not_run
      threshold: 80
      blocking: true

  metadata:
    created_by: vibey-framework
    estimated_duration: "4-5 days"
    agents_assigned:
      - web-developer
      - security-reviewer
      - documentation-engineer
```

**Git Status:**
```bash
$ git status
On branch main
Untracked files:
  .vibey/sprints/auth-sprint-1.yaml
  .vibey/sprint_docs/auth-sprint-1/

Changes not staged for commit:
  modified:   .vibey/roadmap.yaml
```

---

### Step 2.5: Sprint Kickoff Commit

**Action:**
```bash
git add .vibey/sprints/ .vibey/sprint_docs/ .vibey/roadmap.yaml
git commit -m "feat: Plan auth-sprint-1 - User Authentication

Sprint Goal: Build user authentication with email/password and OAuth

Tasks:
- Database schema setup
- Password authentication
- OAuth integration (Google, GitHub)
- Authentication UI
- Security review
- Testing
- Documentation

Estimated: 34 hours (4-5 days)
Quality gates: security_review, test_coverage"
```

**Git Log:**
```bash
$ git log --oneline -2
c3d4e5f feat: Plan auth-sprint-1 - User Authentication
a1b2c3d feat: Initialize Vibey framework
```

---

### Step 2.6: Start Sprint

**Action in Claude Code:**
```
User: Let's start the sprint
```

**Claude Confirms:**
```
🚀 Starting Sprint: auth-sprint-1

✓ Sprint status: planning → in_progress
✓ Start time recorded: 2025-11-10T10:30:00Z
✓ Created progress tracking file

📋 Ready to begin!

First task: "Set up authentication database schema"

Would you like to start this task now? [Y/n]:
```

**User Response:** `Y`

**Repository State Updated:**
```yaml
# .vibey/sprints/auth-sprint-1.yaml
sprint:
  status: in_progress      # ✨ CHANGED
  started: 2025-11-10T10:30:00Z  # ✨ NEW
```

**Git Commit:**
```bash
$ git add .vibey/sprints/auth-sprint-1.yaml
$ git commit -m "chore: Start auth-sprint-1

Sprint officially started at 2025-11-10 10:30 AM"
```

---

### Step 2.7: Task Execution (Task 1)

**Claude Begins Task:**
```
🔨 Task: Set up authentication database schema

I'll create the database schema for user authentication.

Working on:
1. User table (email, password_hash, created_at, updated_at)
2. Session table (user_id, token, expires_at)
3. OAuth provider table (user_id, provider, provider_user_id)

Creating migration file...
```

**Implementation:**
```typescript
// prisma/migrations/001_create_auth_tables.sql
-- User table
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sessions table
CREATE TABLE sessions (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  token VARCHAR(255) UNIQUE NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- OAuth providers table
CREATE TABLE oauth_providers (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  provider VARCHAR(50) NOT NULL,
  provider_user_id VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(provider, provider_user_id)
);
```

**Expected Repository State:**
```
your-project/
├── prisma/
│   ├── migrations/
│   │   └── 001_create_auth_tables.sql   # ✨ NEW
│   └── schema.prisma                     # ✨ UPDATED
└── .vibey/
    └── sprints/
        └── auth-sprint-1.yaml            # Task 1 status updating
```

**Task Completion:**
```
✓ Task complete: Set up authentication database schema

📋 Deliverables:
   - User table migration
   - Session table migration
   - OAuth providers table migration
   - Updated Prisma schema

Would you like to commit this work? [Y/n]:
```

**User Response:** `Y`

**Git Commit (Auto-generated):**
```bash
$ git add prisma/ .vibey/sprints/auth-sprint-1.yaml
$ git commit -m "feat(auth): Add authentication database schema

Implement database tables for user authentication:
- users table (email, password_hash)
- sessions table (token management)
- oauth_providers table (Google, GitHub)

Task: auth-sprint-1-task-001
Sprint: auth-sprint-1

🤖 Generated with Vibey Framework
Co-Authored-By: Claude <noreply@anthropic.com>"
```

**Sprint State Updated:**
```yaml
# .vibey/sprints/auth-sprint-1.yaml
sprint:
  tasks:
    - id: auth-sprint-1-task-001
      status: completed         # ✨ CHANGED
      completed: 2025-11-10T11:45:00Z
      actual_hours: 2.5
      commits:
        - sha: d4e5f6g
          message: "feat(auth): Add authentication database schema"
```

---

### Step 2.8: Continue Through Tasks (Example Pattern)

**Typical Task Flow:**

1. **Claude announces next task**
2. **User confirms or skips**
3. **Claude implements**
4. **Tests run (if applicable)**
5. **User reviews**
6. **Commit generated**
7. **Sprint state updated**
8. **Move to next task**

**Example Git History During Sprint:**
```bash
$ git log --oneline -8
h7i8j9k test(auth): Add authentication unit tests
g6h7i8j feat(auth): Implement OAuth integration
f5g6h7i feat(auth): Build authentication UI
e4f5g6h feat(auth): Implement password authentication
d4e5f6g feat(auth): Add authentication database schema
c3d4e5f feat: Plan auth-sprint-1 - User Authentication
a1b2c3d feat: Initialize Vibey framework
```

---

### Step 2.9: Quality Gate - Security Review

**When All Development Tasks Complete:**
```
✅ All development tasks complete!

📊 Sprint Progress: 6/7 tasks (86%)
   Remaining: Security review

🔒 Running Quality Gate: Security Review

Checking:
- Password hashing implementation
- Session security
- OAuth implementation
- SQL injection vulnerabilities
- XSS vulnerabilities
- CSRF protection
```

**Security Review Results:**
```
🔒 Security Review Complete

✅ Passed Checks:
   - Password hashing uses bcrypt (strength 12)
   - Sessions properly secured (httpOnly, secure flags)
   - OAuth implementation follows best practices
   - No SQL injection vulnerabilities detected
   - XSS protection in place

⚠️  Warnings:
   - Consider adding rate limiting to login endpoint
   - Add account lockout after failed attempts

❌ Failed Checks:
   - Missing CSRF tokens on auth forms

Score: 85/100 (Threshold: 80) ✅ PASSED

Recommendations saved to: .vibey/sprint_docs/auth-sprint-1/SECURITY_REVIEW.md
```

**User Must Address Failures:**
```
The security review found 1 critical issue:
- Missing CSRF tokens on auth forms

This is a blocking issue. Would you like me to fix it? [Y/n]:
```

**User Response:** `Y`

**Fix Applied and Committed:**
```bash
$ git log --oneline -1
i8j9k0l fix(auth): Add CSRF protection to auth forms

Add CSRF token validation to login and registration forms

Security review: auth-sprint-1
Issue: Missing CSRF tokens
```

---

### Step 2.10: Quality Gate - Test Coverage

**After Security Review:**
```
🧪 Running Quality Gate: Test Coverage

Analyzing test coverage...

📊 Coverage Results:
   Overall: 78%
   Authentication module: 75%

   Threshold: 80% ❌ FAILED

Missing coverage:
- OAuth error handling (0% covered)
- Session expiration logic (50% covered)
- Password reset flow (not tested)

Would you like me to add the missing tests? [Y/n]:
```

**User Response:** `Y`

**Tests Added:**
```bash
$ git log --oneline -1
j9k0l1m test(auth): Add missing test coverage

Add tests for:
- OAuth error handling
- Session expiration
- Password reset flow

New coverage: 82%

Quality gate: test_coverage
Sprint: auth-sprint-1
```

---

### Step 2.11: Sprint Completion

**When All Tasks and Gates Pass:**
```
🎉 Sprint Complete!

✅ All tasks completed: 7/7
✅ All quality gates passed:
   - security_review: 85/100
   - test_coverage: 82%

📊 Sprint Summary:
   Goal: Build user authentication with email/password and OAuth
   Duration: 4.5 days
   Tasks: 7
   Commits: 12
   Lines changed: +2,347 / -134

   Quality Metrics:
   - Security: Passed
   - Tests: 82% coverage
   - Documentation: Complete

Generate sprint completion summary? [Y/n]:
```

**User Response:** `Y`

**Sprint Summary Generated:**
```
✓ Created: .vibey/sprint_docs/auth-sprint-1/COMPLETION.md
✓ Updated: .vibey/sprints/auth-sprint-1.yaml (status: completed)
✓ Updated: .vibey/roadmap.yaml (sprint marked complete)
```

**Final Sprint Commit:**
```bash
$ git add .vibey/sprints/ .vibey/sprint_docs/ .vibey/roadmap.yaml
$ git commit -m "feat: Complete auth-sprint-1 - User Authentication

Sprint completed successfully!

✅ Deliverables:
- User authentication system (email/password)
- OAuth integration (Google, GitHub)
- Authentication UI (login, register)
- Comprehensive test suite (82% coverage)
- Security review passed (85/100)
- Full documentation

Duration: 4.5 days
Tasks: 7/7 completed
Commits: 12
Quality gates: All passed

🤖 Generated with Vibey Framework"
```

---

### Step 2.12: Journey 2 Complete

**Final Git History:**
```bash
$ git log --oneline -15
l1m2n3o feat: Complete auth-sprint-1 - User Authentication
k0l1m2n docs(auth): Add authentication documentation
j9k0l1m test(auth): Add missing test coverage
i8j9k0l fix(auth): Add CSRF protection to auth forms
h7i8j9k test(auth): Add authentication unit tests
g6h7i8j feat(auth): Implement OAuth integration (GitHub)
f5g6h7i feat(auth): Implement OAuth integration (Google)
e4f5g6h feat(auth): Build authentication UI
d4e5f6g feat(auth): Implement password authentication
c3d4e5f feat(auth): Add authentication database schema
b2c3d4e feat: Plan auth-sprint-1 - User Authentication
a1b2c3d feat: Initialize Vibey framework
```

**Repository State:**
```
your-project/
├── src/
│   ├── auth/                    # ✨ NEW: Authentication module
│   │   ├── password-auth.ts
│   │   ├── oauth.ts
│   │   └── session-manager.ts
│   └── components/
│       └── auth/                # ✨ NEW: Auth UI components
│           ├── LoginForm.tsx
│           └── RegisterForm.tsx
├── prisma/
│   ├── migrations/              # ✨ NEW: Auth migrations
│   └── schema.prisma            # ✨ UPDATED
├── tests/
│   └── auth/                    # ✨ NEW: Auth tests
│       ├── password-auth.test.ts
│       └── oauth.test.ts
├── .vibey/
│   ├── sprints/
│   │   └── auth-sprint-1.yaml   # ✅ STATUS: completed
│   ├── sprint_docs/
│   │   └── auth-sprint-1/
│   │       ├── PLAN.md
│   │       ├── TASKS.md
│   │       ├── PROGRESS.md
│   │       ├── SECURITY_REVIEW.md
│   │       └── COMPLETION.md    # ✨ NEW
│   └── roadmap.yaml             # ✅ Sprint registered as complete
└── package.json
```

**✅ Success Criteria:**
- ✅ Sprint planned with clear goal
- ✅ Tasks broken down and tracked
- ✅ All tasks completed
- ✅ Quality gates passed
- ✅ Documentation complete
- ✅ Git history clean and descriptive

**Next Steps:**
- Plan next sprint (repeat Journey 2)
- Focus on feature refinement (Journey 3)
- Deep quality review (Journey 4)

---

## Journey 3: Feature Development

**Goal:** Develop a single feature from concept to production
**Duration:** 1-5 days (feature dependent)
**Prerequisites:** Vibey initialized

### Overview

This journey focuses on developing individual features using Vibey's feature development workflow, including design, implementation, testing, and deployment.

---

### Step 3.1: Feature Request

**Action in Claude Code:**
```
User: I want to add a real-time notification system
```

**Claude Analyzes:**
```
🔍 Feature Analysis

I'll help you build a real-time notification system using the single-feature-development workflow.

📊 Initial Assessment:
   Complexity: Medium-High
   Components needed:
   - Backend: WebSocket server
   - Frontend: Real-time client
   - Database: Notification storage
   - UI: Notification bell, toast messages

   Estimated effort: 2-3 days

Should I create a detailed feature plan? [Y/n]:
```

**User Response:** `Y`

---

### Step 3.2: Feature Planning

**Claude Creates Plan:**
```
📋 Feature Plan: Real-Time Notifications

Architecture:
────────────
- WebSocket server (Socket.io)
- Redis for pub/sub
- Notification queue
- React notification components

Backend Tasks:
─────────────
1. Set up Socket.io server
2. Implement notification queue
3. Create notification API endpoints
4. Add database models

Frontend Tasks:
───────────────
5. Build notification bell component
6. Implement toast notifications
7. Add WebSocket client
8. Handle reconnection logic

Testing:
────────
9. Unit tests for notification logic
10. Integration tests for WebSocket
11. E2E tests for user flows

Save this plan? [Y/n]:
```

**User Response:** `Y`

**Plan Saved:**
```
✓ Created: .vibey/sprint_docs/notifications-feature/PLAN.md
✓ Feature registered in roadmap
```

---

### Step 3.3: Implementation Phase 1 - Backend

**Claude Begins:**
```
🔨 Phase 1: Backend Implementation

Starting with WebSocket server setup...

I'll:
1. Install required packages (socket.io, redis)
2. Create WebSocket server
3. Set up Redis connection
4. Implement notification queue
```

**Files Created:**
```
src/
├── notifications/
│   ├── socket-server.ts      # ✨ NEW
│   ├── notification-queue.ts # ✨ NEW
│   ├── notification-api.ts   # ✨ NEW
│   └── models.ts             # ✨ NEW
└── server.ts                  # ✨ UPDATED: Add WebSocket
```

**Git Commit:**
```bash
$ git add src/notifications/ src/server.ts
$ git commit -m "feat(notifications): Add WebSocket server and queue

Implement backend infrastructure for real-time notifications:
- Socket.io server with Redis adapter
- Notification queue with priority support
- API endpoints for notification management
- Database models for notification storage

Feature: real-time-notifications
Phase: backend

🤖 Generated with Vibey Framework"
```

---

### Step 3.4: Implementation Phase 2 - Frontend

**Claude Continues:**
```
🔨 Phase 2: Frontend Implementation

Building notification UI components...

Creating:
1. NotificationBell component
2. NotificationToast component
3. WebSocket client hook
4. Notification context provider
```

**Files Created:**
```
src/components/notifications/
├── NotificationBell.tsx      # ✨ NEW
├── NotificationToast.tsx     # ✨ NEW
├── NotificationList.tsx      # ✨ NEW
└── useNotifications.ts       # ✨ NEW: WebSocket hook
```

**Git Commit:**
```bash
$ git commit -m "feat(notifications): Add notification UI components

Implement frontend notification system:
- Notification bell with badge counter
- Toast notifications (success, error, info)
- WebSocket client with auto-reconnect
- Context provider for global state

Feature: real-time-notifications
Phase: frontend"
```

---

### Step 3.5: Testing

**Claude Adds Tests:**
```
🧪 Writing tests for notification system...

Test coverage:
- Unit tests: notification queue logic
- Integration tests: WebSocket connections
- E2E tests: End-to-end notification flow
```

**Git Commit:**
```bash
$ git commit -m "test(notifications): Add comprehensive test suite

Test coverage:
- Unit tests for notification queue (12 tests)
- Integration tests for WebSocket (8 tests)
- E2E tests for notification flows (5 tests)

Coverage: 87%

Feature: real-time-notifications
Phase: testing"
```

---

### Step 3.6: Quality Gate - Security Review

**Automatic Security Review:**
```
🔒 Running Security Review...

Analyzing:
- WebSocket authentication
- Message validation
- XSS vulnerabilities
- Rate limiting

Results:
✅ WebSocket requires authentication
✅ Message payloads validated
✅ XSS protection in place
⚠️  Consider adding rate limiting per user

Score: 90/100 ✅ PASSED
```

---

### Step 3.7: Feature Completion

**Claude Summarizes:**
```
🎉 Feature Complete: Real-Time Notifications

✅ Backend implementation
✅ Frontend components
✅ Comprehensive tests (87% coverage)
✅ Security review passed (90/100)
✅ Documentation added

📊 Summary:
   Files changed: 15 files
   Lines added: +1,247
   Lines removed: -23
   Commits: 5
   Duration: 2 days

Create feature completion summary? [Y/n]:
```

**Final Commit:**
```bash
$ git commit -m "feat: Complete real-time notifications feature

Full real-time notification system implemented:
- WebSocket server with Redis pub/sub
- Notification queue with priorities
- React components (bell, toasts)
- Comprehensive test suite (87% coverage)
- Security review passed (90/100)

Duration: 2 days
Files: 15 changed (+1,247/-23)

🤖 Generated with Vibey Framework"
```

---

### Step 3.8: Journey 3 Complete

**Git History:**
```bash
$ git log --oneline -6
p4q5r6s feat: Complete real-time notifications feature
o3p4q5r test(notifications): Add comprehensive test suite
n2o3p4q feat(notifications): Add notification UI components
m1n2o3p feat(notifications): Add WebSocket server and queue
l1m2n3o feat: Complete auth-sprint-1
```

**✅ Success Criteria:**
- ✅ Feature fully implemented
- ✅ Tests comprehensive
- ✅ Security reviewed
- ✅ Documented
- ✅ Production-ready

---

## Journey 4: Quality Assurance & Review

**Goal:** Deep quality review of codebase or feature
**Duration:** 2-4 hours
**Prerequisites:** Code to review

### Overview

This journey covers running comprehensive quality audits including security, performance, logging, and documentation reviews.

---

### Step 4.1: Initiate Quality Review

**Action in Claude Code:**
```
User: Run a full quality audit on the authentication feature
```

**Claude Responds:**
```
🔍 Quality Audit: Authentication Feature

I'll run comprehensive quality checks:

1. Security Review
2. Performance Analysis
3. Test Coverage Analysis
4. Code Quality Review
5. Documentation Review

This will take ~30 minutes. Proceed? [Y/n]:
```

**User Response:** `Y`

---

### Step 4.2: Security Review (Deep)

**Claude Runs Security Agent:**
```
🔒 Security Review - Deep Analysis

Scope: src/auth/

Checking:
✓ Authentication logic
✓ Password hashing
✓ Session management
✓ OAuth implementation
✓ SQL injection vulnerabilities
✓ XSS vulnerabilities
✓ CSRF protection
✓ Rate limiting
✓ Account security
✓ Dependency vulnerabilities

Results:
═══════════════════════════════════════

✅ PASSED (15 checks)
   - Password hashing: bcrypt strength 12
   - Sessions: httpOnly, secure, sameSite
   - OAuth: PKCE flow implemented
   - No SQL injection risks
   - XSS protection active
   - CSRF tokens present

⚠️  WARNINGS (3)
   - Rate limiting: Only 10 req/min (recommend 5)
   - Account lockout: 5 attempts (recommend 3)
   - Password requirements: Could be stricter

❌ ISSUES (1)
   - Missing: Multi-factor authentication support

Overall Score: 88/100

Recommendations:
───────────────
1. Add MFA support (high priority)
2. Stricter rate limiting
3. Stronger password requirements
4. Consider implementing security headers

Report saved: .vibey/sprint_docs/auth-sprint-1/SECURITY_AUDIT.md
```

---

### Step 4.3: Performance Analysis

**Claude Runs Performance Agent:**
```
⚡ Performance Analysis

Testing endpoints:
- POST /auth/login
- POST /auth/register
- POST /auth/oauth/google
- GET /auth/session

Results:
═══════════════════════════════════════

Endpoint Performance:
┌─────────────────────┬──────────┬──────────┬─────────┐
│ Endpoint            │ Avg      │ P95      │ P99     │
├─────────────────────┼──────────┼──────────┼─────────┤
│ POST /auth/login    │ 120ms    │ 180ms    │ 250ms   │
│ POST /auth/register │ 350ms    │ 450ms    │ 600ms   │
│ POST /auth/oauth    │ 280ms    │ 400ms    │ 550ms   │
│ GET /auth/session   │  45ms    │  60ms    │  80ms   │
└─────────────────────┴──────────┴──────────┴─────────┘

✅ All endpoints under 500ms target

Database Queries:
- Session lookup: 12ms avg (N+1 query detected)
- User lookup: 8ms avg
- OAuth lookup: 15ms avg

⚠️  Bottlenecks Detected:
   1. Registration: Password hashing takes 280ms
   2. N+1 query in session validation

Recommendations:
───────────────
1. Move password hashing to background job
2. Add database index on sessions.token
3. Fix N+1 query with eager loading
4. Consider Redis caching for sessions

Score: 85/100

Report saved: .vibey/sprint_docs/auth-sprint-1/PERFORMANCE_AUDIT.md
```

---

### Step 4.4: Test Coverage Deep Dive

**Claude Analyzes Tests:**
```
🧪 Test Coverage Analysis

Overall Coverage: 82%

By Module:
┌─────────────────────────┬──────────┬─────────┬──────────┐
│ Module                  │ Lines    │ Branches│ Functions│
├─────────────────────────┼──────────┼─────────┼──────────┤
│ auth/password-auth.ts   │ 95%      │ 88%     │ 100%     │
│ auth/oauth.ts           │ 78%      │ 70%     │ 85%      │
│ auth/session-manager.ts │ 82%      │ 75%     │ 90%      │
│ auth/middleware.ts      │ 65%      │ 60%     │ 70%      │
└─────────────────────────┴──────────┴─────────┴──────────┘

✅ Well-tested:
   - Password authentication (95%)
   - Session management (82%)

⚠️  Needs more tests:
   - OAuth error handling (70%)
   - Middleware edge cases (65%)

❌ Not tested:
   - Password reset flow (0%)
   - Email verification (0%)

Recommendations:
───────────────
1. Add tests for OAuth error scenarios
2. Test middleware with invalid tokens
3. Implement password reset tests
4. Add email verification tests
5. Target: 90% coverage

Report saved: .vibey/sprint_docs/auth-sprint-1/TEST_COVERAGE_AUDIT.md
```

---

### Step 4.5: Code Quality Review

**Claude Reviews Code:**
```
📊 Code Quality Review

Analyzing code patterns and best practices...

ESLint Results:
───────────────
✅ 0 errors
⚠️  12 warnings
   - 8x: Prefer const over let
   - 3x: Missing return type annotations
   - 1x: Unused variable

TypeScript Coverage:
────────────────────
✅ 94% strict type coverage
⚠️  6% any types (mostly in OAuth callbacks)

Code Patterns:
──────────────
✅ Consistent naming conventions
✅ Proper error handling
✅ Good separation of concerns
⚠️  Some functions > 50 lines (4 functions)
⚠️  Duplicate code in OAuth providers (Google/GitHub)

Recommendations:
───────────────
1. Extract common OAuth logic
2. Split large functions
3. Add missing type annotations
4. Remove unused variables
5. Reduce use of 'any' types

Score: 87/100

Report saved: .vibey/sprint_docs/auth-sprint-1/CODE_QUALITY_AUDIT.md
```

---

### Step 4.6: Documentation Review

**Claude Reviews Docs:**
```
📚 Documentation Review

Checking:
- Code comments
- API documentation
- Setup instructions
- Architecture diagrams

Results:
═══════════════════════════════════════

✅ Present:
   - API endpoint documentation
   - Setup instructions in README
   - Inline code comments

⚠️  Missing:
   - Architecture diagram
   - Database schema diagram
   - Authentication flow diagram
   - Troubleshooting guide

❌ Outdated:
   - README lists old OAuth providers
   - API docs missing rate limit info

Recommendations:
───────────────
1. Create architecture diagrams
2. Add authentication flow diagram
3. Update README
4. Add troubleshooting section
5. Document rate limits in API docs

Score: 75/100

Report saved: .vibey/sprint_docs/auth-sprint-1/DOCUMENTATION_AUDIT.md
```

---

### Step 4.7: Consolidated Audit Report

**Claude Creates Summary:**
```
📊 Quality Audit Complete

Overall Scores:
═══════════════════════════════════════
🔒 Security:        88/100  ✅ PASSED
⚡ Performance:     85/100  ✅ PASSED
🧪 Test Coverage:   82/100  ✅ PASSED
📊 Code Quality:    87/100  ✅ PASSED
📚 Documentation:   75/100  ⚠️  NEEDS WORK

Overall Grade: B+ (83.4/100)

Priority Actions:
────────────────
1. 🔴 Add MFA support (security)
2. 🟡 Fix N+1 query (performance)
3. 🟡 Add missing tests (coverage)
4. 🟡 Create diagrams (documentation)

All detailed reports saved to:
.vibey/sprint_docs/auth-sprint-1/audits/

Would you like me to create GitHub issues for priority actions? [Y/n]:
```

**User Response:** `Y`

**Git Commit:**
```bash
$ git add .vibey/sprint_docs/auth-sprint-1/audits/
$ git commit -m "docs: Add comprehensive quality audit reports

Quality audit results for authentication feature:
- Security: 88/100 (passed)
- Performance: 85/100 (passed)
- Test Coverage: 82/100 (passed)
- Code Quality: 87/100 (passed)
- Documentation: 75/100 (needs work)

Overall grade: B+ (83.4/100)

Priority actions identified and tracked

🤖 Generated with Vibey Framework"
```

---

### Step 4.8: Journey 4 Complete

**Repository State:**
```
.vibey/
└── sprint_docs/
    └── auth-sprint-1/
        ├── PLAN.md
        ├── COMPLETION.md
        └── audits/                    # ✨ NEW
            ├── SECURITY_AUDIT.md
            ├── PERFORMANCE_AUDIT.md
            ├── TEST_COVERAGE_AUDIT.md
            ├── CODE_QUALITY_AUDIT.md
            ├── DOCUMENTATION_AUDIT.md
            └── CONSOLIDATED_REPORT.md
```

**✅ Success Criteria:**
- ✅ Comprehensive security review
- ✅ Performance analysis
- ✅ Test coverage audit
- ✅ Code quality review
- ✅ Documentation review
- ✅ Actionable recommendations
- ✅ Reports saved for reference

---

## Journey 5: Framework Management

**Goal:** Configure and manage Vibey framework settings
**Duration:** 10-30 minutes
**Prerequisites:** Vibey initialized

### Overview

This journey covers managing Vibey configuration, updating agents, changing orchestration modes, and customizing workflows.

---

### Step 5.1: Access Framework Management

**Action in Claude Code:**
```
User: /vibey
```

**Claude Shows Options:**
```
🎯 Vibey Framework

What would you like to do?

1. Plan a new sprint
2. Continue current sprint
3. Review sprint progress
4. Manage framework configuration  ← SELECT THIS
5. Other

Your choice:
```

**User Response:** `4`

---

### Step 5.2: Framework Management Menu

**Claude Shows Management Options:**
```
⚙️  Framework Management

Configuration Options:

1. Change orchestration mode
2. Update agent configuration
3. Enable/disable quality gates
4. Customize workflows
5. Update project configuration
6. View framework status
7. Backup/restore configuration

Your choice:
```

---

### Step 5.3: Example - Change Orchestration Mode

**User Chooses:** `1` (Change orchestration mode)

**Claude Asks:**
```
🎚️  Orchestration Mode

Current mode: balanced

Available modes:

1. Simple
   - Explicit agent keywords (e.g., "security", "performance")
   - Best for: Users who want full control
   - Predictable behavior

2. Balanced ✓ (current)
   - Smart pattern matching
   - Best for: Most users
   - Good balance of automation and control

3. Tiered
   - Coordinator routes all requests
   - Best for: Complex projects
   - Maximum automation

Select new mode [1-3]:
```

**User Response:** `3` (Tiered)

**Claude Confirms:**
```
✓ Switching to Tiered orchestration mode

This will:
- Enable coordinator agent
- All requests routed through coordinator
- Coordinator decides which agents to use
- More automated workflow

Update configuration? [Y/n]:
```

**User Response:** `Y`

**Configuration Updated:**
```yaml
# .vibey/config/project.yaml
orchestration:
  mode: tiered           # ✨ CHANGED from 'balanced'
  coordinator_enabled: true  # ✨ CHANGED from false
```

**Git Commit:**
```bash
$ git add .vibey/config/project.yaml
$ git commit -m "config: Switch to tiered orchestration mode

Enable coordinator agent for automatic routing.

Previous: balanced (pattern matching)
Current: tiered (coordinator routing)

Reasoning: Project complexity increasing, want more
automated agent selection.

🤖 Generated with Vibey Framework"
```

---

### Step 5.4: Example - Update Agent Configuration

**User Chooses:** `2` (Update agent configuration)

**Claude Shows Agents:**
```
👥 Agent Configuration

Currently enabled agents:

Core:
✅ coordinator (newly enabled)
✅ vibey-manager

Development:
✅ web-developer
❌ ml-engineer (disabled)

Quality:
✅ security-reviewer
✅ performance-engineer
✅ observability-engineer

Documentation:
✅ documentation-engineer
✅ diagram-engineer
✅ git-committer

Which agent would you like to configure?
(Type agent name or 'all' to see all):
```

**User Response:** `ml-engineer`

**Claude Asks:**
```
🤖 ML Engineer Agent

Current status: Disabled

This agent specializes in:
- ML model development
- Training pipeline setup
- Model evaluation
- ML infrastructure

Enable this agent? [Y/n]:
```

**User Response:** `Y`

**Configuration Updated:**
```yaml
# .vibey/config/project.yaml
agents:
  - web-developer
  - ml-engineer        # ✨ ADDED
  - security-reviewer
  # ... etc
```

**Git Commit:**
```bash
$ git commit -m "config: Enable ml-engineer agent

Planning to add ML features for recommendation system.

🤖 Generated with Vibey Framework"
```

---

### Step 5.5: Example - Customize Quality Gates

**User Chooses:** `3` (Enable/disable quality gates)

**Claude Shows Quality Gates:**
```
🚧 Quality Gate Configuration

Currently enabled gates:

1. Security Review ✅
   Threshold: 80/100
   Blocking: Yes

2. Test Coverage ✅
   Threshold: 80%
   Blocking: Yes

3. Performance ❌ (disabled)
   Threshold: 90/100
   Blocking: No

4. Documentation ❌ (disabled)
   Threshold: 75/100
   Blocking: No

5. Logging Standards ❌ (disabled)
   Threshold: 100%
   Blocking: Yes

Which gate would you like to configure? [1-5]:
```

**User Response:** `3`

**Claude Asks:**
```
⚡ Performance Quality Gate

Current status: Disabled

When enabled, this gate checks:
- API response times
- Database query performance
- Frontend load times
- Memory usage
- N+1 query detection

Enable performance quality gate? [Y/n]:
```

**User Response:** `Y`

**Claude Asks Follow-up:**
```
⚙️  Performance Gate Configuration

1. Threshold (score out of 100): [default: 90]
2. Should this gate block completion? [Y/n]:
3. Max acceptable API response time (ms): [default: 500]

Your settings:
```

**User Responds:**
```
1. 85
2. n
3. 300
```

**Configuration Updated:**
```yaml
# .vibey/config/project.yaml
quality_gates:
  enabled: true
  gates:
    - name: security_review
      threshold: 80
      blocking: true
    - name: test_coverage
      threshold: 80
      blocking: true
    - name: performance          # ✨ ADDED
      threshold: 85
      blocking: false
      config:
        max_response_time_ms: 300
```

**Git Commit:**
```bash
$ git commit -m "config: Enable performance quality gate

Add performance checks to sprint workflow:
- Threshold: 85/100
- Non-blocking (warning only)
- Max response time: 300ms

Will help identify performance issues early.

🤖 Generated with Vibey Framework"
```

---

### Step 5.6: View Framework Status

**User Chooses:** `6` (View framework status)

**Claude Shows Status:**
```
📊 Vibey Framework Status

Version: 1.3.0
Initialized: 2025-11-10
Last updated: 2025-11-10

Project Configuration:
─────────────────────
Name: your-project-name
Type: web-app
Orchestration: tiered
Quality gates: 3 enabled

Active Agents (13):
──────────────────
✅ coordinator
✅ vibey-manager
✅ web-developer
✅ ml-engineer
✅ security-reviewer
✅ performance-engineer
✅ observability-engineer
✅ documentation-engineer
✅ diagram-engineer
✅ git-committer
✅ sprint-planning
✅ researcher

Workflows Available (16):
─────────────────────────
✅ sprint-planning
✅ single-feature-development
✅ ml-model-development
✅ frontend-production-deployment
✅ security-hardening
✅ performance-optimization
✅ logging-audit
✅ documentation-diagrams
✅ architecture-review
# ... etc

Roadmap Status:
───────────────
Total sprints: 1
Completed: 1 (auth-sprint-1)
In progress: 0
Planned: 0

Quality Metrics:
────────────────
Security audits: 2
Performance audits: 1
Test coverage avg: 82%

Recent Activity:
────────────────
2025-11-10 14:30 - Enabled ml-engineer agent
2025-11-10 14:25 - Switched to tiered orchestration
2025-11-10 12:00 - Completed auth-sprint-1

Configuration files:
────────────────────
✅ .vibey/config/project.yaml
✅ .vibey/config/framework.yaml
✅ .vibey/roadmap.yaml
✅ .claude/CLAUDE.md (auto-generated)
```

---

### Step 5.7: Journey 5 Complete

**Git History:**
```bash
$ git log --oneline -4
s7t8u9v config: Enable performance quality gate
r6s7t8u config: Enable ml-engineer agent
q5r6s7t config: Switch to tiered orchestration mode
p4q5r6s feat: Complete real-time notifications feature
```

**✅ Success Criteria:**
- ✅ Configuration easily modified
- ✅ Changes tracked in git
- ✅ Framework status visible
- ✅ Agents customized for project needs

---

## Journey 6: Multi-Platform Deployment

**Goal:** Deploy Vibey to multiple AI platforms
**Duration:** 30-60 minutes
**Prerequisites:** Vibey configured in .vibey/

### Overview

This journey covers deploying Vibey from a single `.vibey/` source to multiple platforms (Claude Code, Goose, Cursor).

---

### Step 6.1: Current State (Claude Code Only)

**Repository State:**
```
your-project/
├── .vibey/                  # ✅ Source configuration
│   └── config/
│       ├── project.yaml
│       └── framework.yaml
└── .claude/                 # ✅ Claude Code deployment
    ├── CLAUDE.md
    └── agents/
```

---

### Step 6.2: Deploy to Goose

**Action:**
```bash
cd .vibey
./vibey deploy --platform goose
```

**Output:**
```
🚀 Vibey Deployment Engine
Platform: Goose

✓ Reading source configuration (.vibey/config/)
✓ Detected: 13 agents, 16 workflows
✓ Generating Goose-specific files...
✓ Creating .goose/ directory...
✓ Converting agents to extensions...
✓ Converting workflows to recipes...
✓ Creating toolkit.toml...

📦 Goose Deployment Summary:
   Extensions: 13
   Recipes: 16
   Configuration: toolkit.toml

✓ Deployment complete!

Goose Setup:
────────────
1. Install Goose: pip install goose-ai
2. Link toolkit: goose toolkit add /path/to/your-project/.goose
3. Run: goose session start

Documentation: .goose/README.md
```

**Expected Repository State:**
```
your-project/
├── .vibey/                  # Source configuration
├── .claude/                 # Claude Code deployment
└── .goose/                  # ✨ NEW: Goose deployment
    ├── extensions/
    │   ├── web-developer.yaml
    │   ├── security-reviewer.yaml
    │   └── ... (13 extensions)
    ├── recipes/
    │   ├── sprint-planning.yaml
    │   ├── feature-development.yaml
    │   └── ... (16 recipes)
    ├── toolkit.toml
    └── README.md
```

**Git Status:**
```bash
$ git status
# .goose/ is gitignored (regenerable from .vibey/)
```

---

### Step 6.3: Deploy to Cursor (when available)

**Action:**
```bash
./vibey deploy --platform cursor
```

**Output:**
```
🚀 Vibey Deployment Engine
Platform: Cursor

✓ Reading source configuration (.vibey/config/)
✓ Generating Cursor-specific files...
✓ Creating .cursorrules...
✓ Creating .cursor/ directory...

⚠️  Note: Cursor has limited agent support
   - Single .cursorrules file created
   - Agent instructions consolidated
   - Workflow selection manual

📦 Cursor Deployment Summary:
   Rules file: .cursorrules (consolidated)
   Prompts: .cursor/prompts/

✓ Deployment complete!

Cursor Setup:
─────────────
1. Open project in Cursor
2. Cursor will automatically read .cursorrules
3. Use @vibey to invoke workflows

Documentation: .cursor/README.md
```

---

### Step 6.4: Multi-Platform Repository State

**Final Repository:**
```
your-project/
├── src/                     # Your application
├── .vibey/                  # ✅ Single source of truth (committed)
│   ├── config/
│   │   ├── project.yaml
│   │   ├── framework.yaml
│   │   └── agents/
│   ├── roadmap.yaml
│   └── framework/
├── .claude/                 # Claude Code deployment (gitignored)
├── .goose/                  # Goose deployment (gitignored)
└── .cursor/                 # Cursor deployment (gitignored)
    └── .cursorrules
```

**Git Configuration:**
```bash
# .gitignore
.vibey/.git/      # Vibey's own git history
.claude/          # Regenerable from .vibey/
.goose/           # Regenerable from .vibey/
.cursor/          # Regenerable from .vibey/
```

**Key Point:** Only `.vibey/` is committed. All platform deployments are regenerable.

---

### Step 6.5: Using Multiple Platforms

**Workflow:**

1. **Make configuration change in .vibey/:**
```bash
vim .vibey/config/project.yaml
# Add new agent, modify settings, etc.
```

2. **Commit change:**
```bash
git add .vibey/config/
git commit -m "config: Add new feature flags"
```

3. **Redeploy to all platforms:**
```bash
cd .vibey
./vibey deploy --all
```

**Output:**
```
🚀 Deploying to all platforms...

✓ Claude Code deployment updated
✓ Goose deployment updated
✓ Cursor deployment updated

All platforms synchronized with .vibey/ configuration!
```

---

### Step 6.6: Journey 6 Complete

**✅ Success Criteria:**
- ✅ Single source configuration (.vibey/)
- ✅ Multiple platform deployments
- ✅ Easy regeneration of deployments
- ✅ Git only tracks source config

**Benefits:**
- Change configuration once, deploy everywhere
- Platform-specific optimizations automatic
- No duplicate configuration maintenance
- Easy to add new platforms

---

## Journey 7: Roadmap-Driven Development

**Goal:** Use Vibey's roadmap system to track long-term project development
**Duration:** Ongoing (weeks/months)
**Prerequisites:** Vibey initialized

### Overview

This journey covers using Vibey's built-in roadmap system to plan tracks, manage sprints, track tasks, and measure progress over extended periods.

---

### Step 7.1: Initialize Roadmap

**Action in Claude Code:**
```
User: Set up a product roadmap for the next quarter
```

**Claude Responds:**
```
🗺️  Roadmap System

I'll help you set up a comprehensive roadmap.

Let's start by defining your tracks (major initiatives).

Common track types:
- Feature tracks (e.g., "User Management", "Payment System")
- Quality tracks (e.g., "Performance Optimization", "Security Hardening")
- Infrastructure tracks (e.g., "CI/CD Pipeline", "Monitoring Setup")

What tracks do you want to plan?
(You can add them one at a time or list several)
```

**User Response:**
```
1. User Management System
2. Payment Integration
3. Performance Optimization
4. Mobile App Development
```

---

### Step 7.2: Define Track 1 - User Management

**Claude Creates Track:**
```
📋 Track 1: User Management System

Let me break this down into sprints...

Suggested sprints:
───────────────────
Sprint 1: Authentication (1-2 weeks)
- User registration
- Login/logout
- Password reset
- OAuth integration

Sprint 2: User Profiles (1 week)
- Profile management
- Avatar upload
- User preferences
- Account settings

Sprint 3: Authorization (1 week)
- Role-based access control
- Permission system
- Admin panel
- Audit logging

Total: 3 sprints, 3-4 weeks

Does this breakdown work? [Y/n/edit]:
```

**User Response:** `Y`

---

### Step 7.3: Create Roadmap Structure

**Claude Creates Files:**
```
✓ Creating roadmap structure...

Created:
────────
.vibey/tracks/user-management.yaml
.vibey/sprints/user-mgmt-1-auth.yaml
.vibey/sprints/user-mgmt-2-profiles.yaml
.vibey/sprints/user-mgmt-3-authz.yaml
.vibey/roadmap.yaml (updated)
```

**Roadmap File (.vibey/roadmap.yaml):**
```yaml
roadmap:
  id: your-project-roadmap
  name: "Your Project Development Roadmap"
  version: "1.0"
  created: 2025-11-10T15:00:00Z

  tracks:
    - id: user-management
      name: "User Management System"
      status: not_started
      priority: high
      sprints:
        - user-mgmt-1-auth
        - user-mgmt-2-profiles
        - user-mgmt-3-authz
      estimated_duration: "3-4 weeks"

    - id: payment-integration
      name: "Payment Integration"
      status: not_started
      priority: high
      dependencies:
        - user-management  # Requires auth first
      sprints:
        - payment-1-setup
        - payment-2-processing
      estimated_duration: "2 weeks"

    - id: performance
      name: "Performance Optimization"
      status: not_started
      priority: medium
      sprints:
        - perf-1-frontend
        - perf-2-backend
        - perf-3-database
      estimated_duration: "3 weeks"

    - id: mobile-app
      name: "Mobile App Development"
      status: not_started
      priority: medium
      dependencies:
        - user-management
        - payment-integration
      sprints:
        - mobile-1-setup
        - mobile-2-core
        - mobile-3-release
      estimated_duration: "6 weeks"

  progress:
    tracks_total: 4
    tracks_completed: 0
    sprints_total: 11
    sprints_completed: 0
    completion_percent: 0
```

---

### Step 7.4: Start Track - User Management

**Action in Claude Code:**
```
User: Start the user management track
```

**Claude Responds:**
```
🚀 Starting Track: User Management System

This track has 3 sprints:
1. Authentication (1-2 weeks)
2. User Profiles (1 week)
3. Authorization (1 week)

Starting with Sprint 1: Authentication

Would you like to plan this sprint now? [Y/n]:
```

**User Response:** `Y`

**Sprint Planning Begins** (See Journey 2 for full sprint planning flow)

---

### Step 7.5: Track Progress Over Time

**Checking Progress:**
```bash
# Use roadmap query CLI
python3 framework/scripts/roadmap-query.py
```

**Output:**
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

---

### Step 7.6: Roadmap Visualization

**Repository State with Active Roadmap:**
```
.vibey/
├── roadmap.yaml             # Master roadmap
├── tracks/
│   ├── user-management.yaml
│   ├── payment-integration.yaml
│   ├── performance.yaml
│   └── mobile-app.yaml
├── sprints/
│   ├── user-mgmt-1-auth.yaml       # ✅ completed
│   ├── user-mgmt-2-profiles.yaml   # 🔵 in_progress
│   ├── user-mgmt-3-authz.yaml      # ⚪ not_started
│   └── ... (11 sprint files)
└── sprint_docs/
    ├── user-mgmt-1-auth/
    │   ├── PLAN.md
    │   ├── COMPLETION.md
    │   └── audits/
    └── user-mgmt-2-profiles/
        └── PLAN.md
```

**Git History Shows Progress:**
```bash
$ git log --oneline --grep="Sprint" -10
u9v0w1x feat: Complete user-mgmt-1-auth sprint
t8u9v0w feat: Plan user-mgmt-2-profiles sprint
s7t8u9v feat: Plan user-mgmt-1-auth sprint
r6s7t8u feat: Initialize roadmap system
```

---

### Step 7.7: Dependency Management

**When Payment Track Becomes Unblocked:**
```
✓ User Management track completed!

🔓 Unblocked tracks:
   - Payment Integration (depended on user-management)

Would you like to start Payment Integration now? [Y/n]:
```

**Roadmap automatically tracks dependencies:**
```yaml
# .vibey/tracks/payment-integration.yaml
track:
  id: payment-integration
  dependencies:
    - track_id: user-management
      status: completed        # ✨ Automatically updated
  blocked: false              # ✨ Auto-unblocked
  status: ready_to_start      # ✨ Status changed
```

---

### Step 7.8: Long-Term Progress Tracking

**After 6 Weeks:**
```bash
$ python3 framework/scripts/roadmap-query.py
```

**Output:**
```
============================================================
Roadmap: Your Project Development Roadmap
============================================================
Progress: 73% (8/11 sprints complete)

🛤️  Tracks:
  ✅ completed User Management System (user-management)
     Duration: 4 weeks
     Sprints: 3/3 complete

  ✅ completed Payment Integration (payment-integration)
     Duration: 2 weeks
     Sprints: 2/2 complete

  🔵 in_progress Performance Optimization (performance)
     Sprints: 2/3 complete
     Current: perf-3-database

  ⚪ not_started Mobile App Development (mobile-app)
     Ready to start (dependencies met)

Velocity:
─────────
Avg sprint duration: 5.2 days
Sprints per week: 1.3
Estimated completion: 2025-12-01 (3 weeks)

Quality Metrics:
────────────────
Security audits: 8 (all passed)
Test coverage avg: 84%
Performance score avg: 88/100
```

---

### Step 7.9: Roadmap Reports

**Generate Roadmap Summary:**
```
User: Generate a roadmap summary report
```

**Claude Creates:**
```
📊 Roadmap Summary Report

Generated: 2025-11-24
Period: 2025-11-10 to 2025-11-24 (2 weeks)

Completed Work:
═══════════════════════════════════════
✅ User Management System (3 sprints)
   - Authentication
   - User Profiles
   - Authorization
   Duration: 4 weeks
   Quality: All gates passed

✅ Payment Integration (2 sprints)
   - Payment Setup
   - Payment Processing
   Duration: 2 weeks
   Quality: All gates passed

In Progress:
═══════════════════════════════════════
🔵 Performance Optimization
   Current: Database optimization
   Progress: 67% (2/3 sprints)
   Estimated completion: 1 week

Upcoming:
═══════════════════════════════════════
⚪ Mobile App Development
   Dependencies met: Yes
   Can start: Yes
   Estimated: 6 weeks

Key Metrics:
═══════════════════════════════════════
Total sprints: 11
Completed: 8 (73%)
In progress: 1
Not started: 2

Avg velocity: 1.3 sprints/week
Avg sprint duration: 5.2 days

Quality:
────────
Security: 100% passed
Test coverage: 84% avg
Performance: 88/100 avg

Report saved: .vibey/summaries/roadmap-summary-2025-11-24.md
```

---

### Step 7.10: Journey 7 Complete

**Final Repository State:**
```
your-project/
├── src/                     # Evolved significantly
├── .vibey/
│   ├── roadmap.yaml         # ✅ 73% complete
│   ├── tracks/              # 4 tracks (2 complete)
│   ├── sprints/             # 11 sprints (8 complete)
│   ├── sprint_docs/         # Rich documentation
│   └── summaries/           # Roadmap reports
└── .git/
    # Rich history showing progress
```

**Git History:**
```bash
$ git log --oneline --all --graph -20
* w1x2y3z feat: Complete perf-2-backend sprint
* v0w1x2y feat: Complete perf-1-frontend sprint
* u9v0w1x feat: Complete payment-2-processing sprint
* t8u9v0w feat: Complete payment-1-setup sprint
* s7t8u9v feat: Complete user-mgmt-3-authz sprint
* r6s7t8u feat: Complete user-mgmt-2-profiles sprint
* q5r6s7t feat: Complete user-mgmt-1-auth sprint
* p4q5r6s feat: Initialize roadmap system
```

**✅ Success Criteria:**
- ✅ Long-term roadmap defined
- ✅ Track dependencies managed
- ✅ Sprint progress tracked
- ✅ Quality metrics maintained
- ✅ Velocity measured
- ✅ Reports generated
- ✅ Git history tells the story

---

## Common Decision Points

### Decision Point 1: Orchestration Mode

**When:** During initialization (Step 1.5)

**Options:**
```
1. Simple - Explicit keywords
   Choose if: You want full control

2. Balanced - Pattern matching
   Choose if: You trust smart defaults

3. Tiered - Coordinator routing
   Choose if: Complex project, want automation
```

**Can Change Later:** Yes (Journey 5)

---

### Decision Point 2: Quality Gates

**When:** During initialization or anytime

**Options:**
```
Enable:
- Security review (recommended)
- Test coverage (recommended)
- Performance checks
- Documentation standards
- Logging standards
```

**Consider:**
- Project maturity (early vs established)
- Team size (solo vs team)
- Criticality (internal tool vs production app)

**Can Change Later:** Yes (Journey 5)

---

### Decision Point 3: Sprint vs Feature Development

**When:** Starting new work

**Choose Sprint Planning (Journey 2) if:**
- Multiple related tasks
- 3+ days of work
- Need structured approach
- Want progress tracking

**Choose Feature Development (Journey 3) if:**
- Single focused feature
- 1-2 days of work
- Quick iteration
- Less overhead needed

---

### Decision Point 4: Codebase Audit

**When:** After initialization

**Run Audit if:**
- Existing large codebase
- Unfamiliar with project
- Want baseline metrics
- Planning major refactor

**Skip if:**
- Brand new project
- Small codebase (<1000 lines)
- Already familiar with code

---

### Decision Point 5: Roadmap System

**When:** Project planning

**Use Roadmap (Journey 7) if:**
- Multi-month project
- Multiple major initiatives
- Need dependency tracking
- Want long-term visibility

**Skip if:**
- Short project (<1 month)
- Single focus area
- Informal tracking sufficient

---

## Troubleshooting Journeys

### Problem: Vibey Not Responding

**Symptoms:**
```
User: /vibey
[No response from Claude]
```

**Diagnostic Steps:**

1. **Check CLAUDE.md exists:**
```bash
ls .claude/CLAUDE.md
# Should exist
```

2. **Check CLAUDE.md has content:**
```bash
head -20 .claude/CLAUDE.md
# Should show Vibey framework context
```

3. **Regenerate deployment:**
```bash
cd .vibey
./vibey deploy --platform claude-code --force
```

4. **Verify .claude/ structure:**
```bash
tree .claude/
# Should show agents/, workflows/, commands/
```

---

### Problem: Agent Not Triggering

**Symptoms:**
```
User: Run security review
[Wrong agent responds or no agent triggers]
```

**Diagnostic Steps:**

1. **Check orchestration mode:**
```bash
grep "mode:" .vibey/config/project.yaml
```

2. **Check agent enabled:**
```bash
grep "security-reviewer" .vibey/config/project.yaml
```

3. **Try explicit request:**
```
User: /vibey
[Select appropriate option]
```

4. **Check agent configuration:**
```bash
cat .claude/agents/quality/security-reviewer.md
# Verify trigger patterns
```

---

### Problem: Quality Gate Failing

**Symptoms:**
```
❌ Quality Gate Failed: security_review
Score: 65/100 (threshold: 80)
```

**Resolution Steps:**

1. **Review detailed report:**
```bash
cat .vibey/sprint_docs/[sprint-id]/audits/SECURITY_AUDIT.md
```

2. **Address critical issues:**
```
User: Fix the security issues found in the audit
```

3. **Re-run quality gate:**
```
User: Run security review again
```

4. **If still failing, adjust threshold:**
```yaml
# .vibey/config/project.yaml
quality_gates:
  gates:
    - name: security_review
      threshold: 70  # Temporarily lower
```

---

### Problem: Git History Messy

**Symptoms:**
```
$ git log --oneline -10
abc123 wip
def456 fix
ghi789 stuff
# Unclear commit messages
```

**Resolution:**

1. **Enable automatic commit messages:**
```yaml
# .vibey/config/project.yaml
git:
  auto_commit: true
  message_template: "feat: {task_title}\n\n{description}"
```

2. **Squash messy commits:**
```bash
git rebase -i HEAD~10
# Squash WIP commits
```

3. **Use Vibey's commit workflow:**
```
Always let Vibey generate commit messages
They follow conventional commits format
```

---

## Advanced Scenarios

### Scenario 1: Integrating Existing Sprint System

**Starting Point:** Team uses Jira for sprints

**Integration Strategy:**

1. **Mirror Jira structure:**
```
User: Set up roadmap to mirror our Jira sprints
```

2. **Sync sprint state:**
```bash
# Custom script
python3 .vibey/scripts/sync-from-jira.py
```

3. **Dual tracking:**
- Vibey: Technical execution
- Jira: Project management

4. **Report to Jira:**
```
User: Generate Jira update from sprint completion
```

---

### Scenario 2: Multi-Team Coordination

**Starting Point:** 3 teams working on same codebase

**Coordination Strategy:**

1. **Separate tracks per team:**
```yaml
# .vibey/roadmap.yaml
tracks:
  - id: frontend-team-work
  - id: backend-team-work
  - id: infrastructure-team-work
```

2. **Define inter-team dependencies:**
```yaml
- id: frontend-team-work
  dependencies:
    - track_id: backend-team-work
      sprints:
        - api-sprint-1
```

3. **Coordination points:**
```
User: Show dependencies blocking frontend team
```

---

### Scenario 3: Open Source Project

**Starting Point:** Public GitHub repo

**Adaptation:**

1. **Public roadmap:**
```bash
# Make roadmap visible
cp .vibey/roadmap.yaml ROADMAP.md
# Commit ROADMAP.md
```

2. **Contributor guidance:**
```bash
# In CONTRIBUTING.md
See ROADMAP.md for planned work
Vibey framework used for coordination
```

3. **Issue integration:**
```
User: Create GitHub issues for all planned tasks
```

---

### Scenario 4: Legacy Codebase Migration

**Starting Point:** Large legacy codebase

**Migration Strategy:**

1. **Start with audit:**
```
User: Run comprehensive codebase audit
```

2. **Create migration roadmap:**
```
User: Create roadmap for migrating from [old] to [new]
```

3. **Incremental sprints:**
```
Sprint 1: Audit and baseline
Sprint 2: Set up new architecture
Sprint 3: Migrate module A
Sprint 4: Migrate module B
...
```

4. **Quality gates critical:**
```yaml
quality_gates:
  gates:
    - name: test_coverage
      threshold: 90  # Higher for migration
    - name: security_review
      threshold: 95  # Higher for migration
```

---

## Conclusion

This comprehensive guide has documented all primary user journeys through Vibey:

1. ✅ **First-Time Setup** - Initialize and configure
2. ✅ **Sprint Planning** - Structure and execute sprints
3. ✅ **Feature Development** - Build individual features
4. ✅ **Quality Assurance** - Deep audits and reviews
5. ✅ **Framework Management** - Configure and customize
6. ✅ **Multi-Platform** - Deploy across platforms
7. ✅ **Roadmap-Driven** - Long-term project tracking

### Key Takeaways

**Git History Tells the Story:**
- Every sprint = clear commit sequence
- Quality gates = audit commits
- Roadmap progress = git log timeline

**Repository State Evolution:**
- `.vibey/` grows with project
- Rich documentation in `sprint_docs/`
- Roadmap tracks everything

**Flexibility:**
- Choose your own journey
- Mix and match workflows
- Customize to fit your process

### Getting Started

1. **New to Vibey?** Start with Journey 1
2. **Have Vibey set up?** Jump to Journey 2 or 3
3. **Long-term planning?** Use Journey 7
4. **Multi-platform?** See Journey 6

### Next Steps

- Try a journey hands-on
- Customize for your project
- Share feedback with Vibey team

---

**Document Version:** 1.0
**Last Updated:** 2025-11-10
**Feedback:** GitHub issues or discussions
