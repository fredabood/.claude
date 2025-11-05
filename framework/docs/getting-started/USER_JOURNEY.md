# Vibey Framework - Complete User Journey

**Last Updated:** 2025-11-04
**Framework Version:** v1.0

## Universal Installation Flow

**Everyone uses the same installation flow, regardless of their situation:**

```bash
git clone https://github.com/fredabood/vibey.git .vibey
claude
# Type: /vibey
```

**Claude handles everything automatically:**
- Detects if you have an existing `.claude/` directory
- Deploys or merges the framework accordingly
- Preserves custom content if merging
- Cleans up `.vibey/` directory after deployment
- Initializes framework configuration
- Plans your first sprint

---

## What Happens in Each Scenario

This guide shows what Claude does automatically in three common scenarios:
1. **New repository** (no `.claude/` exists)
2. **Existing repo without `.claude/`** (fresh installation)
3. **Existing repo with `.claude/`** (merge/migration)

Each scenario uses the **same installation command** - Claude detects your situation and adapts.

---

## Table of Contents

- [Scenario 1: New Repository (Greenfield)](#scenario-1-new-repository-greenfield)
- [Scenario 2: Existing Repo Without .claude](#scenario-2-existing-repo-without-claude)
- [Scenario 3: Existing Repo With .claude (Merge)](#scenario-3-existing-repo-with-claude-merge)
- [Summary: Critical File Paths](#summary-critical-file-paths)
- [Quick Command Reference](#quick-command-reference)

---

## Scenario 1: New Repository (Greenfield)

**Situation:** You're starting a brand new project from scratch.

### Initial State
```
/Users/yourname/
└── (empty - no project yet)
```

### Step 1.1: Create Project & Install Framework
```bash
# Create project directory
mkdir -p /Users/yourname/Projects/taskmaster
cd /Users/yourname/Projects/taskmaster

# Install Python dependencies
pip install pyyaml jinja2

# Clone Vibey framework
git clone https://github.com/fredabood/vibey.git .vibey
```

**Directory state after clone:**
```
/Users/yourname/Projects/taskmaster/
├── .vibey/                     # ✓ Framework cloned here
│   ├── agents/
│   ├── workflows/
│   ├── templates/
│   ├── commands/
│   ├── scripts/
│   ├── config/
│   └── docs/
```

### Step 1.2: Start Claude Code and Run `/vibey`

```bash
# Start Claude Code
claude-code
```

In Claude Code, type:
```
/vibey
```

**Phase 1: Claude Detects New Installation**

Claude runs detection:
```bash
# Check for existing .claude directory
ls -d .claude 2>/dev/null
# Result: directory does not exist
```

Claude says:
"I don't see an existing `.claude/` directory. I'll deploy the Vibey framework now."

**Phase 1: Claude Deploys Framework**

Claude runs:
```bash
# Copy .vibey to .claude
cp -r .vibey .claude

# Verify deployment
ls -d .claude/agents .claude/workflows .claude/templates .claude/commands .claude/scripts
# Result: all 5 directories exist ✓

# Clean up .vibey
rm -rf .vibey

echo "✓ Framework deployed to .claude/"
echo "✓ Cleaned up temporary .vibey/ directory"
```

**Directory state after deployment:**
```
/Users/yourname/Projects/taskmaster/
├── .claude/                            # ✓ Framework deployed
│   ├── agents/                         # 12 specialized agents
│   │   ├── planning/
│   │   │   ├── sprint-planning.md
│   │   │   └── researcher.md
│   │   ├── development/
│   │   │   ├── web-developer.md            # Web developer agent
│   │   │   └── ml-engineer.md               # ML engineer agent
│   │   ├── quality/
│   │   │   ├── security-reviewer.md        # Security agent
│   │   │   ├── observability-engineer.md   # Logging agent
│   │   │   └── performance-engineer.md     # Performance agent
│   │   ├── documentation/
│   │   │   ├── documentation-engineer.md   # Docs agent
│   │   │   ├── diagram-engineer.md         # Diagram agent
│   │   │   ├── documentation-maintenance-engineer.md
│   │   │   └── git-committer.md            # Git agent
│   │   └── core/
│   │       └── coordinator.md               # Coordinator agent
│   ├── workflows/
│   │   ├── sprint-planning.md
│   │   ├── single-feature-development.md
│   │   ├── frontend-feature-development.md
│   │   ├── ml-model-development.md
│   │   ├── framework-initialization.md      # NEW - initialization workflow
│   │   └── [10 more workflows]
│   ├── templates/
│   │   ├── CLAUDE.md.template               # Main template
│   │   └── handoffs/
│   │       ├── api-spec-template.md
│   │       ├── security-report-template.md
│   │       ├── database-schema-design-template.md
│   │       └── [18 more templates]
│   ├── config/
│   │   ├── schema.yaml                      # Config schema
│   │   └── config-templates/
│   │       ├── web-app-config.yaml
│   │       ├── api-config.yaml
│   │       ├── ml-project-config.yaml
│   │       ├── data-platform-config.yaml
│   │       └── infrastructure-config.yaml
│   ├── commands/
│   │   └── vibey.md                         # NEW - /vibey command
│   └── README.md
├── scripts/
│   ├── validate-config.py                   # Config validator
│   └── render-template.py                   # Template renderer
├── docs/
│   └── ORCHESTRATION.md                     # Orchestration guide
├── src/
├── tests/
├── README.md
└── .gitignore
```

### Step 1.3: Start Claude Code
```bash
# Open project in Claude Code
claude-code .
# Or use your Claude Code editor to open /Users/yourname/Projects/taskmaster
```

### Step 1.4: Run `/vibey` Command

**In Claude Code, type:**
```
/vibey
```

**Claude's response:**
```
Welcome! I'm going to help you set up the Vibey Agent Framework for your project.

This will take about 20-30 minutes. I'll ask you questions about your project,
and together we'll:
- Configure the framework for your technology stack
- Choose how agents are orchestrated
- Create your project documentation
- Plan your first sprint

Let's get started!

I noticed this is a new project. Would you like to:
- Start fresh with Vibey configuration
- Skip initialization (framework already set up)

What's your project called, and what does it do?
```

**User response:**
```
It's called "TaskMaster" - a task management app for remote teams
```

**Claude continues:**
```
Got it! Is this primarily a:
- Web application (frontend + backend)
- API service (backend only)
- Data platform (ETL, pipelines, analytics)
- Machine learning project (models, training, inference)
- Infrastructure project (IaC, DevOps, deployment)
```

**User:**
```
Web application
```

**Claude:**
```
What's your backend technology stack?

For example:
- Python with FastAPI, Django, or Flask
- TypeScript/JavaScript with Express, NestJS
- Java with Spring Boot
- Go with Gin or Echo
- Other?
```

**User:**
```
Python with FastAPI
```

**Claude:**
```
And what about the frontend?

Common choices:
- React with TypeScript
- Vue with TypeScript
- Angular
- Svelte
- Other?
```

**User:**
```
React with TypeScript
```

**Claude:**
```
What database(s) are you using, or planning to use?

For example:
- Relational (PostgreSQL, MySQL)
- Document (MongoDB)
- Graph (Neo4j)
- Time-series (InfluxDB, TimescaleDB)
- Key-value (Redis, DynamoDB)
- Multiple databases
```

**User:**
```
PostgreSQL
```

**Claude continues asking about:**
- UI library (Material-UI, Tailwind, etc.)
- State management (Redux, Zustand, etc.)
- Team size
- Test coverage requirements
- Security standards

**Then presents orchestration mode choice:**
```
Now, an important choice: How should I orchestrate agents and workflows?

Here are your options:

**A) Simple & Transparent**
   - I follow clear rules documented in CLAUDE.md
   - You can see and modify all orchestration logic
   - Fast - no overhead
   - Best for: Small teams, simple projects, learning the framework

   Cons: Less intelligent, might miss opportunities to use agents

**D) Balanced & Discoverable [RECOMMENDED]**
   - High-level flow in CLAUDE.md + agents self-advertise when to use them
   - Smart pattern matching for agent selection
   - Good balance of speed and intelligence
   - Best for: Most projects, teams that want smart automation

   Cons: Slightly more complex than Simple mode

**F) Intelligent & Adaptive**
   - Simple requests handled directly (fast path)
   - Complex requests routed through coordinator agent (smart path)
   - Most sophisticated orchestration
   - Best for: Large projects, enterprise teams, complex domains

   Cons: Most complex, adds some overhead for complex requests

Most teams choose **D (Balanced)** - it provides smart automation without
unnecessary complexity.

Which orchestration mode would you like? [D]
```

**User:**
```
Balanced
```

### Step 1.5: Claude Generates Configuration

**Claude creates:**
```yaml
# /Users/yourname/Projects/taskmaster/project-config.yaml

project:
  name: "TaskMaster"
  type: "web-app"
  description: "A task management app for remote teams"
  version: "0.1.0"
  team_size: 3

technology_stack:
  backend:
    language: "python"
    version: ">=3.10"
    framework: "fastapi"
  frontend:
    language: "typescript"
    framework: "react"
    ui_library: "material-ui"
  database:
    type: "postgresql"
    orm: "sqlalchemy"
  testing:
    backend:
      framework: "pytest"
      coverage_tool: "pytest-cov"
    frontend:
      framework: "jest"
      testing_library: "react-testing-library"
      e2e: "playwright"

framework:
  orchestration_mode: "balanced"
  auto_agent_launch: true
  require_quality_gates: true
  version: "1.0"
  config_location: "root"

quality_gates:
  test_coverage_minimum: 90
  security_score_minimum: 85
  logging_audit_minimum: 80
  required_reviews:
    - security
    - testing
    - logging
    - documentation

coding_standards:
  python:
    formatter: "black"
    line_length: 88
    linter: "ruff"
    type_checker: "mypy"
  javascript:
    formatter: "prettier"
    linter: "eslint"
  test_coverage:
    minimum: 90
    fail_under: 90
```

**Claude validates:**
```bash
# Runs automatically
python3 scripts/validate-config.py project-config.yaml
# Output: ✓ Config is valid!
```

### Step 1.6: Claude Generates CLAUDE.md

**Claude creates:**
```bash
# Runs automatically
python3 scripts/render-template.py \
  --config project-config.yaml \
  --template .claude/templates/CLAUDE.md.template \
  --output CLAUDE.md
```

**Creates `/Users/yourname/Projects/taskmaster/CLAUDE.md`:**
```markdown
# TaskMaster

A task management app for remote teams

**Version:** 0.1.0

---

## Quick Start

Every session, follow this checklist:

1. ✅ **Read this file** (CLAUDE.md) - Project state and critical rules
2. 📋 **Check ROADMAP.md** - Current sprint status and completed versions
3. 🔍 **Run `git status`** - Understand current state
4. 🤖 **Check agent framework** - Review available agents and workflows

---

## Technology Stack

### Backend
- **Language:** python >=3.10
- **Framework:** fastapi

### Frontend
- **Language:** typescript
- **Framework:** react
- **UI Library:** material-ui

### Database
- **Type:** postgresql
- **ORM:** sqlalchemy

### Testing
- **Backend:** pytest with pytest-cov
- **Frontend:** jest with react-testing-library
- **E2E:** playwright

---

## Coding Standards

### Python
- **Formatter:** black (88 chars)
- **Linter:** ruff
- **Type Checker:** mypy

### JavaScript/TypeScript
- **Formatter:** prettier
- **Linter:** eslint

### Test Coverage
- **Minimum:** 90%
- **Build fails under:** 90%

---

## Critical Rules

### 1. NO CODE WITHOUT PLAN
- All changes require a sprint plan or phase plan
- Exception: Production emergencies (document within 24 hours)

### 2. TEST EVERYTHING
- Minimum 90% test coverage
- All tests must pass before merging

### 3. UPDATE DOCUMENTATION
- Update CLAUDE.md with every change
- Keep sprint documentation current
- Document architectural decisions

---

## Quality Gates

Every sprint must pass these mandatory reviews:

### 1. Security Review
- No critical or high vulnerabilities
- Secrets properly managed
- Authentication/authorization validated
- **Minimum score:** 85/100

### 2. Unit Testing Review
- Minimum 90% coverage
- All tests passing
- Edge cases covered
- Integration tests included

### 3. Logging Audit
- Minimum score: 80/100
- Correlation IDs propagating
- Error context sufficient
- Performance metrics tracked

### 4. Documentation Review
- Architecture diagrams current
- API documentation complete
- README up to date

---

## Agent Orchestration

**Orchestration Mode:** BALANCED
**Auto-launch agents:** Enabled
**Quality gates:** Required before sprint completion

### Balanced & Discoverable Mode (RECOMMENDED)

You use **two-layer orchestration**:
1. **High-level structure** from this file (sprint phases, quality gates)
2. **Agent trigger patterns** from agent files themselves

**How it works:**
- Each agent in `.claude/agents/` has a "Trigger Patterns" section
- Pattern-match user requests against agent keywords, contexts, and file patterns
- Launch relevant agents based on matches and priority
- Use sprint phase to guide which agents are appropriate

**Sprint Phase Detection:**
User request mentions:
- "plan sprint", "roadmap", "prioritize" → **Planning phase**
- "implement", "build", "create", "develop" → **Development phase**
- "review", "audit", "test coverage", "security check" → **Quality gates phase**
- "deploy", "release", "push to production" → **Deployment phase**

**Agent Selection Process:**
1. Scan all `.claude/agents/**/*.md` files for trigger patterns
2. Match user request keywords against agent triggers
3. Consider project type (web-app) for relevant agents
4. Consider sprint phase for appropriate agents
5. Apply priority (High → Medium → Low)
6. Launch matched agents in priority order

**Multi-agent Requests:**
If request involves multiple concerns, launch multiple agents:
- "Implement secure authentication" → Web Developer + Security Reviewer
- "Optimize slow API endpoint" → Performance Engineer + Test Engineer (verify no regressions)
- "Add feature and document it" → Development agent + Documentation Engineer

**Quality Gate Enforcement:**
Before marking sprint complete, you MUST run:
- Security review
- Testing review
- Logging review
- Documentation review

### Available Agents

**Planning:** (`.claude/agents/planning/`)
- Sprint Planning Agent - Plan iterations, prioritize features
- Researcher Agent - Research new APIs, libraries, platforms

**Development:** (`.claude/agents/development/`)
- Web Developer - Build web UIs, dashboards, frontend/backend
- ML Engineer - Train models, feature engineering, ML pipelines

**Quality:** (`.claude/agents/quality/`)
- Security Reviewer - Security audits, OWASP compliance
- Observability Engineer - Logging audits, monitoring setup
- Performance Engineer - Performance optimization, profiling

**Documentation:** (`.claude/agents/documentation/`)
- Documentation Engineer - Update docs after features
- Diagram Engineer - Create Mermaid architecture diagrams
- Documentation Maintenance Engineer - Keep CLAUDE.md current
- Git Committer - Create clean commits with good messages

### Workflows

Use workflows for structured, multi-step processes:
- `.claude/workflows/sprint-planning.md` - Plan new sprints
- `.claude/workflows/single-feature-development.md` - Implement features
- `.claude/workflows/frontend-feature-development.md` - Build UI features

### Handoff Templates

Use templates for agent-to-agent communication:
- `.claude/templates/handoffs/api-spec-template.md` - API specifications
- `.claude/templates/handoffs/security-report-template.md` - Security findings
- `.claude/templates/handoffs/database-schema-design-template.md` - DB changes
- `.claude/templates/handoffs/frontend-design-template.md` - UI specifications

Full list: `.claude/templates/handoffs/`

### Orchestration Tips

- **Trust pattern matching** - Agent trigger patterns are comprehensive
- **Launch multiple agents** - Don't hesitate to use multiple agents for complex requests
- **Respect priorities** - High priority agents (security, planning) run first
- **Consider project type** - web-app projects have specific agent needs
- **Quality gates are mandatory** - Don't skip required reviews
- **Document with agents** - Use documentation agents, don't manually update docs
- **Use workflows for structure** - Workflows provide step-by-step guidance

---

## Project Structure

```
TaskMaster/
├── src/           # Source code
├── tests/         # Test files
├── docs/          # Documentation
└── scripts/       # Utility scripts
```

---

## Getting Help

### For Developers
1. Read this file (CLAUDE.md)
2. Check ROADMAP.md for current sprint
3. Review sprint plans in docs/sprints/
4. Consult agent framework: .claude/README.md

### For Claude Code
1. Always read CLAUDE.md first
2. Check ROADMAP.md for sprint status
3. Follow critical rules above
4. Use agent framework when appropriate
5. Run all quality gates before completion

---

**Last Updated:** 2025-11-04
**Framework:** Vibey v1.0
**Configuration:** project-config.yaml
```

### Step 1.7: Claude Creates Directory Structure

```bash
# Claude runs automatically
mkdir -p docs/sprints
mkdir -p docs/operations
mkdir -p docs/architecture
mkdir -p docs/reference
mkdir -p docs/security
```

**Directory state:**
```
/Users/yourname/Projects/taskmaster/
├── .claude/                    # ✓ Framework installed
├── scripts/                    # ✓ Scripts installed
├── docs/
│   ├── sprints/               # ✓ Created
│   ├── operations/            # ✓ Created
│   ├── architecture/          # ✓ Created
│   ├── reference/             # ✓ Created
│   ├── security/              # ✓ Created
│   └── ORCHESTRATION.md       # ✓ Installed
├── src/
├── tests/
├── project-config.yaml         # ✓ Generated
├── CLAUDE.md                   # ✓ Generated
├── README.md
└── .gitignore
```

### Step 1.8: Claude Plans First Sprint

**Claude:**
```
Perfect! The framework is configured. Now let's plan your first sprint.

What are your goals for the first sprint? What features or improvements do you
want to tackle?
```

**User:**
```
User authentication, task dashboard, and basic CRUD operations for tasks
```

**Claude:**
```
Great goals! Let me analyze what we need for Sprint 1...

I'm analyzing:
- User authentication (JWT, login/register, password management)
- Task dashboard (UI, real-time updates, filtering)
- CRUD operations (create, read, update, delete tasks)

This will require:
- Backend: FastAPI endpoints, database models, authentication
- Frontend: React components, state management, API integration
- Infrastructure: Database setup, environment config
- Testing: Unit tests, integration tests, E2E tests
```

**Claude creates `/Users/yourname/Projects/taskmaster/docs/sprints/sprint-001-plan.md`:**

```markdown
# Sprint 1 Plan - TaskMaster

**Sprint Duration:** 2 weeks
**Sprint Goal:** User authentication and basic task management
**Team Size:** 3 developers
**Estimated Effort:** 80 hours

---

## Sprint Objectives

1. **User Authentication System**
   - Secure JWT-based authentication
   - User registration and login
   - Password hashing and validation

2. **Task Dashboard**
   - Display user's tasks
   - Real-time task updates
   - Task filtering and sorting

3. **Task CRUD Operations**
   - Create new tasks
   - View task details
   - Update task status/details
   - Delete tasks

---

## Tasks

### Task 1: Project Setup & Infrastructure
**Estimated Effort:** 8 hours
**Priority:** High
**Description:** Set up development environment, database, and project structure

**Subtasks:**
- Initialize FastAPI project structure
- Set up React app with TypeScript
- Configure PostgreSQL database
- Set up environment variables
- Create docker-compose for local development

**Agent Recommendations:**
- Use infrastructure setup workflow (`.claude/workflows/infrastructure-setup.md`)

**Acceptance Criteria:**
- [ ] FastAPI running on localhost:8000
- [ ] React app running on localhost:3000
- [ ] PostgreSQL database accessible
- [ ] Environment variables configured
- [ ] Docker compose working

---

### Task 2: Database Schema Design
**Estimated Effort:** 4 hours
**Priority:** High
**Description:** Design database schema for users and tasks

**Subtasks:**
- Design User table (id, email, hashed_password, created_at)
- Design Task table (id, user_id, title, description, status, priority, due_date, created_at, updated_at)
- Define relationships and indexes
- Create SQLAlchemy models
- Create Alembic migrations

**Agent Recommendations:**
- Use Database Schema Design template (`.claude/templates/handoffs/database-schema-design-template.md`)

**Workflow:** Single Feature Development (`.claude/workflows/single-feature-development.md`)

**Acceptance Criteria:**
- [ ] Database schema documented
- [ ] SQLAlchemy models created
- [ ] Migrations created and tested
- [ ] Foreign keys and indexes defined
- [ ] Schema validated

---

### Task 3: User Authentication API
**Estimated Effort:** 12 hours
**Priority:** High
**Description:** Implement JWT-based authentication endpoints

**Subtasks:**
- Create `/auth/register` endpoint (POST)
- Create `/auth/login` endpoint (POST)
- Create `/auth/me` endpoint (GET - current user)
- Implement JWT token generation
- Implement password hashing (bcrypt)
- Add input validation (Pydantic models)

**Agent Recommendations:**
- **Development:** Web Developer (`.claude/agents/development/web-developer.md`)
- **Quality:** Security Reviewer (`.claude/agents/quality/security-reviewer.md`)
- **Testing:** Comprehensive tests required

**Workflow:** Single Feature Development (`.claude/workflows/single-feature-development.md`)

**Handoff Templates:**
- API Specification (`.claude/templates/handoffs/api-spec-template.md`)
- Security Report (`.claude/templates/handoffs/security-report-template.md`)

**Acceptance Criteria:**
- [ ] Register endpoint working
- [ ] Login endpoint returns valid JWT
- [ ] Me endpoint requires authentication
- [ ] Passwords are hashed with bcrypt
- [ ] Input validation on all fields
- [ ] 90%+ test coverage
- [ ] Security review passed (no high/critical issues)
- [ ] API documentation generated

---

[Additional tasks 4-8 continue with similar detail...]

---

## Quality Gates

Before Sprint 1 is complete, ALL quality gates must pass:

### 1. Security Review
**Required Score:** ≥ 85/100
**Review Agent:** `.claude/agents/quality/security-reviewer.md`

**Must check:**
- [ ] No SQL injection vulnerabilities
- [ ] No XSS vulnerabilities
- [ ] JWT properly validated
- [ ] Passwords properly hashed (bcrypt)
- [ ] No secrets in code
- [ ] CORS configured correctly
- [ ] Rate limiting implemented
- [ ] Input validation on all endpoints

**Deliverable:** `docs/security/security-report-sprint-001.md`

---

### 2. Test Coverage
**Required Coverage:** ≥ 90%
**Must include:**
- [ ] Unit tests for all endpoints
- [ ] Unit tests for all components
- [ ] Integration tests for API
- [ ] E2E tests for user flows
- [ ] Edge cases covered
- [ ] Error cases covered

**Verification:**
```bash
# Backend
pytest --cov=src --cov-report=term-missing
# Must show ≥ 90%

# Frontend
npm test -- --coverage
# Must show ≥ 90%
```

---

### 3. Logging Audit
**Required Score:** ≥ 80/100
**Review Agent:** `.claude/agents/quality/observability-engineer.md`

**Must check:**
- [ ] Correlation IDs in all logs
- [ ] Authentication events logged
- [ ] Task operations logged
- [ ] Error context sufficient
- [ ] Log levels appropriate
- [ ] No sensitive data in logs

**Deliverable:** `docs/operations/logging-audit-sprint-001.md`

---

### 4. Documentation
**Must update:**
- [ ] README.md - Setup instructions, API overview
- [ ] CLAUDE.md - Sprint 1 completion, architecture updates
- [ ] API documentation (auto-generated from FastAPI)
- [ ] Architecture diagram (auth flow, task CRUD flow)

**Review Agent:** `.claude/agents/documentation/documentation-engineer.md`

---

## Success Criteria

Sprint 1 is complete when:
- [ ] All 8 tasks completed
- [ ] All acceptance criteria met
- [ ] Security review passed (≥ 85/100)
- [ ] Test coverage passed (≥ 90%)
- [ ] Logging audit passed (≥ 80/100)
- [ ] Documentation updated
- [ ] All tests passing
- [ ] Application runs successfully
- [ ] Demo ready

---

**Sprint 1 Plan Created:** 2025-11-04
**Framework:** Vibey v1.0
**Orchestration Mode:** Balanced
```

### Step 1.9: Sprint 1 Ready!

**Claude:**
```
✓ Sprint 1 plan created: docs/sprints/sprint-001-plan.md

Your first sprint includes:
- 8 tasks totaling ~80 hours estimated effort
- Infrastructure setup and database design
- User authentication (backend + frontend)
- Task CRUD operations (backend + frontend)
- Comprehensive testing

Each task includes:
- Agent recommendations (which agents to use)
- Workflow guidance (step-by-step processes)
- Handoff templates (documentation to fill)
- Acceptance criteria

Quality gates required before sprint completion:
✓ Security review (score ≥85)
✓ Test coverage (≥90%)
✓ Logging audit (score ≥80)
✓ Documentation updated

Ready to start? Just tell me which task you want to work on, and I'll
automatically use the recommended agents and workflows!

What would you like to work on first?
```

### Step 1.10: Start First Task

**User:**
```
Let's start with Task 1 - Project Setup & Infrastructure
```

**Claude automatically:**
1. Detects this is infrastructure setup
2. Matches trigger patterns:
   - "setup", "infrastructure" → No specific agent, but workflow available
3. Follows `.claude/workflows/infrastructure-setup.md`
4. Creates project structure

**Claude:**
```
I'll help you set up the infrastructure for TaskMaster.

Creating FastAPI project structure...
```

*[Creates backend structure, frontend structure, docker-compose, etc.]*

---

## Final Directory State (Scenario 1)

```
/Users/yourname/Projects/taskmaster/
├── .git/
├── .claude/                           # ✓ Framework
│   ├── agents/                       # ✓ 11 agents
│   ├── workflows/                    # ✓ 15 workflows (+ initialization)
│   ├── templates/                    # ✓ 22 handoff templates
│   ├── config/                       # ✓ Schema + config templates
│   ├── commands/                     # ✓ /vibey command
│   └── README.md
├── scripts/                          # ✓ Python scripts
│   ├── validate-config.py
│   └── render-template.py
├── docs/                             # ✓ Documentation
│   ├── sprints/
│   │   └── sprint-001-plan.md       # ✓ First sprint plan
│   ├── operations/
│   ├── architecture/
│   ├── reference/
│   ├── security/
│   └── ORCHESTRATION.md
├── backend/                          # ✓ Backend code (created by Claude)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── models.py
│   │   └── routers/
│   ├── tests/
│   ├── alembic/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                         # ✓ Frontend code (created by Claude)
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── contexts/
│   │   ├── services/
│   │   └── App.tsx
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml                # ✓ Created by Claude
├── .env.example                      # ✓ Created by Claude
├── project-config.yaml               # ✓ Generated by /vibey
├── CLAUDE.md                         # ✓ Generated by /vibey
├── README.md
└── .gitignore
```

**Time invested:** ~30 minutes conversational setup
**Result:** Complete framework setup + first sprint planned + infrastructure created

---

## Scenario 2: Existing Repo Without .claude

**Situation:** You have an existing project with code, but no `.claude/` directory yet.

**Installation:** Same as Scenario 1:
```bash
cd your-project
pip install pyyaml jinja2
git clone https://github.com/fredabood/vibey.git .vibey
claude
# Type: /vibey
```

**What's different:** Claude detects existing code and analyzes it to understand your tech stack, then suggests quality improvements + new features for Sprint 1.

### Initial State
```
/Users/yourname/Projects/existing-api/
├── .git/
├── src/
│   ├── main.py
│   ├── models.py
│   ├── routes/
│   └── utils/
├── tests/
│   └── test_main.py
├── requirements.txt
├── README.md
└── .gitignore
```

**Existing project:** A FastAPI project with ~5,000 lines of code, been in development for 3 months

### Step 2.1: Install Vibey Framework

```bash
cd /Users/yourname/Projects/existing-api

# Install dependencies
pip install pyyaml jinja2

# Clone Vibey directly as .claude directory
git clone https://github.com/fredabood/vibey.git .claude
```

**Directory state after installation:**
```
/Users/yourname/Projects/existing-api/
├── .git/
├── .claude/                          # ✓ NEW - Framework installed
│   ├── agents/
│   ├── workflows/
│   ├── templates/
│   ├── config/
│   ├── commands/
│   └── README.md
├── scripts/                          # ✓ NEW - Scripts installed
│   ├── validate-config.py
│   └── render-template.py
├── docs/                             # NEW or MERGED with existing
│   └── ORCHESTRATION.md
├── src/                              # ← EXISTING CODE
│   ├── main.py
│   ├── models.py
│   ├── routes/
│   └── utils/
├── tests/                            # ← EXISTING CODE
│   └── test_main.py
├── requirements.txt                  # ← EXISTING
├── README.md                         # ← EXISTING
└── .gitignore                        # ← EXISTING
```

### Step 2.2: Start Claude Code & Run `/vibey`

```bash
claude-code .
```

**In Claude Code:**
```
/vibey
```

**Claude:**
```
Welcome! I'm going to help you set up the Vibey Agent Framework for your project.

I noticed this project already has code! Let me analyze what you have...

[Claude analyzes the codebase]

I found:
- FastAPI project with ~5,000 lines of Python code
- 10 API endpoints in src/routes/
- 15 database models in src/models.py
- 40 tests in tests/
- PostgreSQL database (inferred from SQLAlchemy models)

This looks like an API service project. Is that correct?
```

**User:**
```
Yes, it's a RESTful API for managing user accounts and organizations
```

**Claude:**
```
Got it! Let me ask you a few questions to configure the framework properly...

What's the project called?
```

**User:**
```
OrganizationAPI
```

*[Claude continues with orchestration mode selection, quality standards, etc.]*

**Key difference from Scenario 1:** Claude analyzes existing code and infers:
- Project type (API)
- Technology stack (Python, FastAPI, PostgreSQL, SQLAlchemy)
- Current state (active development)
- Test coverage (calculates from existing tests)

**Claude generates `/Users/yourname/Projects/existing-api/project-config.yaml`:**

```yaml
project:
  name: "OrganizationAPI"
  type: "api"
  description: "RESTful API for managing user accounts and organizations"
  version: "0.5.0"  # ← Inferred from existing code
  repository: "git@github.com:yourorg/organization-api.git"  # ← From git remote

technology_stack:
  backend:
    language: "python"
    version: ">=3.10"  # ← Inferred from requirements.txt
    framework: "fastapi"  # ← Detected from imports
  database:
    type: "postgresql"  # ← Inferred from SQLAlchemy connection
    orm: "sqlalchemy"  # ← Detected

framework:
  orchestration_mode: "balanced"
  auto_agent_launch: true
  require_quality_gates: true
  version: "1.0"

quality_gates:
  test_coverage_minimum: 90
  security_score_minimum: 85
  logging_audit_minimum: 80
  required_reviews:
    - security
    - testing
    - logging
    - documentation
```

### Step 2.3: First Sprint for Existing Project

**Claude:**
```
Your project is already in active development. For the first sprint with Vibey,
I recommend focusing on:

1. **Code quality improvements**
   - Increase test coverage (currently 60%, target 90%)
   - Security audit (no audit has been run yet)
   - Logging improvements (add correlation IDs, structured logging)

2. **Documentation**
   - Generate API documentation
   - Create architecture diagrams
   - Update README

3. **New features** (if any)

What would you like to focus on for Sprint 1 with Vibey?
```

**User:**
```
Let's focus on security audit and test coverage improvements first, then add a new billing feature
```

**Claude creates `/Users/yourname/Projects/existing-api/docs/sprints/sprint-001-plan.md`:**

```markdown
# Sprint 1 Plan - OrganizationAPI (Vibey Integration)

**Sprint Duration:** 2 weeks
**Sprint Goal:** Security hardening, test coverage improvement, and billing feature
**Estimated Effort:** 60 hours

---

## Sprint Objectives

1. **Security Audit & Hardening**
   - Run comprehensive security review
   - Fix all critical and high vulnerabilities
   - Implement security best practices

2. **Test Coverage Improvement**
   - Increase coverage from 60% to 90%
   - Add integration tests
   - Add edge case tests

3. **Billing Feature**
   - Add subscription management
   - Add payment processing (Stripe)
   - Add billing history

---

## Tasks

### Task 1: Security Audit of Existing Code
**Estimated Effort:** 8 hours
**Priority:** Critical
**Description:** Comprehensive security review of existing codebase

**Agent Recommendations:**
- **Quality:** Security Reviewer (`.claude/agents/quality/security-reviewer.md`)

**Workflow:** Direct agent usage

**Focus Areas:**
- Authentication/authorization in existing endpoints
- SQL injection vulnerabilities
- Input validation
- Secrets management
- CORS configuration
- Rate limiting

**Acceptance Criteria:**
- [ ] Security report generated
- [ ] All critical issues identified
- [ ] All high issues identified
- [ ] Remediation plan created

**Deliverable:** `docs/security/security-audit-existing-code.md`

---

### Task 2: Fix Critical Security Issues
**Estimated Effort:** 12 hours
**Priority:** Critical
**Description:** Address all critical and high security issues found in audit

[Rest of tasks...]
```

### Final Directory State (Scenario 2)

```
/Users/yourname/Projects/existing-api/
├── .git/
├── .claude/                          # ✓ NEW - Framework added
│   ├── agents/
│   ├── workflows/
│   ├── templates/
│   ├── config/
│   ├── commands/
│   └── README.md
├── scripts/                          # ✓ NEW
│   ├── validate-config.py
│   └── render-template.py
├── docs/                             # ✓ EXPANDED
│   ├── sprints/
│   │   └── sprint-001-plan.md       # ✓ NEW - First sprint with Vibey
│   ├── security/                     # ✓ NEW
│   ├── ORCHESTRATION.md              # ✓ NEW
│   └── [existing docs]
├── src/                              # ← EXISTING CODE (unchanged)
│   ├── main.py
│   ├── models.py
│   ├── routes/
│   └── utils/
├── tests/                            # ← EXISTING (will be expanded)
│   └── test_main.py
├── requirements.txt                  # ← EXISTING
├── project-config.yaml               # ✓ NEW - Generated
├── CLAUDE.md                         # ✓ NEW - Generated
├── README.md                         # ← EXISTING (will be updated)
└── .gitignore                        # ← EXISTING
```

**Key differences from Scenario 1:**
- Existing code is analyzed and preserved
- Config inferred from existing code
- First sprint focuses on quality improvements + new features
- Framework added non-invasively

---

## Scenario 3: Existing Repo With .claude (Merge)

**Situation:** You already have a `.claude/` directory with custom agents, prompts, or configuration.

**Installation:** Same command as Scenarios 1 & 2:
```bash
cd your-project
pip install pyyaml jinja2
git clone https://github.com/fredabood/vibey.git .vibey
claude
# Type: /vibey
```

**What's different:** Claude detects existing `.claude/`, offers two merge options:
1. **Backup and merge** - Backs up your `.claude/` to `.claude-backup-{date}`, merges Vibey, preserves custom content
2. **Selective merge** - Keeps your existing files, adds only missing Vibey components

Claude guides you through the process conversationally and preserves all your custom work.

### Initial State

```
/Users/yourname/Projects/legacy-app/
├── .git/
├── .claude/                          # ← EXISTING .claude
│   ├── custom-agent.md               # Custom agent user created
│   ├── prompts/
│   │   └── code-review.md
│   └── README.md
├── src/
│   └── [application code]
├── CLAUDE.md                         # ← EXISTING CLAUDE.md (manual)
└── README.md
```

**Scenario:** Project already uses Claude Code with custom setup, now wants to add Vibey framework

### Step 3.1: Backup Existing .claude Directory

```bash
cd /Users/yourname/Projects/legacy-app

# IMPORTANT: Backup existing .claude directory
cp -r .claude .claude-backup-$(date +%Y%m%d)
```

**Result:**
```
/Users/yourname/Projects/legacy-app/
├── .claude/                          # Original
└── .claude-backup-20251104/          # ✓ Backup created
```

### Step 3.2: Install Vibey Framework (Merge Mode)

**Option A: Start Fresh (Recommended)**
```bash
# Rename existing .claude to preserve custom content
mv .claude .claude-custom

# Install dependencies
pip install pyyaml jinja2

# Clone Vibey as new .claude
git clone https://github.com/fredabood/vibey.git .claude

# Manually copy custom agents/prompts from .claude-custom into .claude
# (Review and merge what you want to keep)

# After merging, optionally remove backup
rm -rf .claude-custom
```

**Option B: Merge into Existing**
```bash
# Clone Vibey temporarily
git clone https://github.com/fredabood/vibey.git .vibey

# Install dependencies
pip install pyyaml jinja2

# Merge framework components INTO existing .claude
cp -r .vibey/agents .claude/
cp -r .vibey/workflows .claude/
cp -r .vibey/templates .claude/
cp -r .vibey/config .claude/
cp -r .vibey/commands .claude/
cp -r .vibey/scripts .claude/

# Clean up
rm -rf .vibey
```

**⚠️ Option B Warning:** This will overwrite any Vibey components you modified. Option A is safer.

**Directory state after merge:**
```
/Users/yourname/Projects/legacy-app/
├── .git/
├── .claude/
│   ├── agents/                       # ✓ NEW - Vibey agents
│   │   ├── planning/
│   │   ├── development/
│   │   ├── quality/
│   │   ├── documentation/
│   │   └── core/
│   ├── workflows/                    # ✓ NEW - Vibey workflows
│   │   └── [15 workflows]
│   ├── templates/                    # ✓ NEW - Vibey templates
│   │   ├── CLAUDE.md.template
│   │   └── handoffs/
│   ├── config/                       # ✓ NEW - Vibey config
│   │   ├── schema.yaml
│   │   └── config-templates/
│   ├── commands/                     # ✓ NEW - Vibey commands
│   │   └── vibey.md
│   ├── custom-agent.md               # ← PRESERVED - User's custom agent
│   ├── prompts/                      # ← PRESERVED - User's prompts
│   │   └── code-review.md
│   └── README.md                     # ← EXISTING (may need merge)
├── .claude-backup-20251104/          # Backup
├── scripts/                          # ✓ NEW
│   ├── validate-config.py
│   └── render-template.py
├── src/
├── CLAUDE.md                         # ← EXISTING (will be replaced/merged)
└── README.md
```

### Step 3.3: Handle Existing CLAUDE.md

**Option A: Preserve Existing Content**

```bash
# Rename existing CLAUDE.md
mv CLAUDE.md CLAUDE-original.md
```

**Option B: Merge Content (recommended)**

Keep existing CLAUDE.md for now, let Claude analyze it during `/vibey` setup

### Step 3.4: Start Claude Code & Run `/vibey`

```bash
claude-code .
```

**In Claude Code:**
```
/vibey
```

**Claude:**
```
Welcome! I'm going to help you set up the Vibey Agent Framework.

I noticed this project already has a .claude directory with some custom content:
- custom-agent.md
- prompts/code-review.md
- README.md

I also see an existing CLAUDE.md file.

Would you like me to:
1. **Merge** - Keep your existing .claude content and integrate Vibey framework
2. **Replace** - Replace with fresh Vibey setup (your content backed up)
3. **Cancel** - Skip Vibey initialization

I recommend: Merge (option 1)
```

**User:**
```
Merge
```

**Claude:**
```
Great! I'll integrate Vibey with your existing setup.

I'm analyzing your existing CLAUDE.md to understand your project...

[Claude reads CLAUDE-original.md or CLAUDE.md]

I found:
- Project: Legacy Application (accounting system)
- Tech stack: Django, PostgreSQL, jQuery (!)
- Custom rules about legacy code preservation
- Specific deployment process

I'll preserve all your existing rules and content while adding Vibey framework capabilities.

Let me ask a few questions to complete the setup...
```

*[Claude proceeds with discovery, but pre-fills answers from existing CLAUDE.md]*

**Claude:**
```
From your existing CLAUDE.md, I see:
- Project name: "Legacy Accounting System"
- Tech stack: Django + PostgreSQL
- Custom rule: "Never delete legacy accounting.py module"

Is this still accurate?
```

**User:**
```
Yes, but we're modernizing the frontend from jQuery to React
```

**Claude:**
```
Noted! I'll update the tech stack to reflect the React migration.

[Continues with orchestration mode selection, etc.]
```

### Step 3.5: Generated Config with Merged Content

**Claude generates `/Users/yourname/Projects/legacy-app/project-config.yaml`:**

```yaml
project:
  name: "Legacy Accounting System"
  type: "web-app"
  description: "Accounting system with Django backend, migrating frontend from jQuery to React"
  version: "2.5.0"  # From existing CLAUDE.md

technology_stack:
  backend:
    language: "python"
    framework: "django"
  frontend:
    language: "typescript"  # NEW - React migration
    framework: "react"      # NEW
  database:
    type: "postgresql"
    orm: "django-orm"

framework:
  orchestration_mode: "balanced"
  auto_agent_launch: true
  require_quality_gates: true
  version: "1.0"

quality_gates:
  test_coverage_minimum: 80  # Lower for legacy project
  security_score_minimum: 85
  logging_audit_minimum: 75  # Lower for legacy project
  required_reviews:
    - security
    - testing
    - documentation

# PRESERVED from existing CLAUDE.md
critical_rules:
  - id: 1
    rule: "Never delete or modify legacy accounting.py module"
    rationale: "Contains production accounting logic used by 500+ customers"
    exception: "Only with explicit approval from CTO"
    enforcement:
      - "Code review required"
      - "Customer notification required"

custom:
  deployment:
    process: "Manual deployment via deploy.sh script"
    approvers: ["john@company.com", "sarah@company.com"]
  legacy_modules:
    - "accounting.py"
    - "reports/legacy_reports.py"
    - "exports/quickbooks.py"
```

### Step 3.6: Generate Merged CLAUDE.md

**Claude:**
```
I'm generating a new CLAUDE.md that combines:
- Your existing project context
- Your custom rules
- Vibey framework orchestration
- Updated tech stack (React migration)

Your original CLAUDE.md is saved as: CLAUDE-original.md
```

**Claude creates `/Users/yourname/Projects/legacy-app/CLAUDE.md` with merged content including:**
- Existing critical rules preserved
- Legacy module warnings
- Vibey agent orchestration added
- React migration status table
- Custom deployment process maintained
- Both custom agents and Vibey agents listed

### Step 3.7: First Sprint with Merged Setup

**Claude:**
```
✓ Vibey framework integrated with your existing setup!

I've preserved:
- Your custom agent (custom-agent.md)
- Your custom prompts (prompts/code-review.md)
- All your critical rules (accounting.py protection, etc.)
- Your deployment process

Added:
- 11 Vibey agents
- 15 Vibey workflows
- 22 handoff templates
- Orchestration system
- Quality gates

Your project is in active development with frontend migration in progress.

For Sprint 1 with Vibey, I recommend:
1. Continue jQuery → React migration (Reports page)
2. Security audit (financial application)
3. Test coverage improvement (especially accounting module)
4. Add logging audit

What would you like to focus on?
```

**User:**
```
Let's migrate the Reports page to React and run security audit
```

*[Claude creates sprint plan with both legacy considerations and modern development]*

### Final Directory State (Scenario 3)

```
/Users/yourname/Projects/legacy-app/
├── .git/
├── .claude/
│   ├── agents/                       # ✓ NEW - Vibey agents (11 agents)
│   │   ├── planning/
│   │   ├── development/
│   │   ├── quality/
│   │   ├── documentation/
│   │   └── core/
│   ├── workflows/                    # ✓ NEW - Vibey workflows (15 workflows)
│   ├── templates/                    # ✓ NEW - Vibey templates (21 templates)
│   ├── config/                       # ✓ NEW - Vibey config
│   ├── commands/                     # ✓ NEW - /vibey command
│   ├── custom-agent.md               # ✓ PRESERVED - User's custom agent
│   ├── prompts/                      # ✓ PRESERVED - User's prompts
│   │   └── code-review.md
│   └── README.md                     # ✓ MERGED - Combined user + Vibey
├── .claude-backup-20251104/          # ✓ Backup of original .claude
├── scripts/                          # ✓ NEW
│   ├── validate-config.py
│   └── render-template.py
├── docs/
│   ├── sprints/
│   │   └── sprint-001-plan.md       # ✓ NEW - First sprint with Vibey
│   ├── migration/                    # ← EXISTING
│   ├── security/                     # ✓ NEW
│   └── ORCHESTRATION.md              # ✓ NEW
├── backend/                          # ← EXISTING (Django)
│   ├── accounting/                   # ⚠️ PROTECTED - Never modify
│   ├── reports/
│   ├── api/
│   └── exports/
├── frontend/                         # ← EXISTING
│   ├── legacy/                       # jQuery (being phased out)
│   └── react-app/                    # React (new)
├── tests/                            # ← EXISTING
├── deploy.sh                         # ← EXISTING
├── project-config.yaml               # ✓ NEW - Generated with legacy rules
├── CLAUDE.md                         # ✓ NEW - Merged version
├── CLAUDE-original.md                # ✓ BACKUP - Original CLAUDE.md
└── README.md                         # ← EXISTING
```

**Key differences from Scenarios 1 & 2:**
- Existing .claude directory backed up and merged
- Custom agents and prompts preserved
- Critical legacy rules preserved in config
- Hybrid approach (legacy + modern)
- Lower quality gate thresholds (accounting for legacy code)

---

## Summary: Critical File Paths

### Framework Core Files
```
.claude/
├── agents/                                    # 12 specialized agents
│   ├── planning/
│   │   ├── sprint-planning.md                 # Sprint planning agent
│   │   └── researcher.md                      # Research agent
│   ├── development/
│   │   ├── web-developer.md                   # Web development agent
│   │   └── ml-engineer.md                     # ML agent
│   ├── quality/
│   │   ├── security-reviewer.md               # Security agent
│   │   ├── observability-engineer.md          # Logging agent
│   │   └── performance-engineer.md            # Performance agent
│   ├── documentation/
│   │   ├── documentation-engineer.md          # Documentation agent
│   │   ├── diagram-engineer.md                # Diagram agent
│   │   ├── documentation-maintenance-engineer.md
│   │   └── git-committer.md                   # Git agent
│   └── core/
│       └── coordinator.md                     # Coordinator (Tiered mode)
├── workflows/
│   ├── framework-initialization.md            # ⭐ Initialization workflow
│   ├── sprint-planning.md                     # Sprint planning
│   ├── single-feature-development.md          # Feature development
│   └── [12 more workflows]
├── templates/
│   ├── CLAUDE.md.template                     # ⭐ Main template
│   └── handoffs/                              # 22 handoff templates
│       ├── api-spec-template.md
│       ├── security-report-template.md
│       └── [19 more templates]
├── config/
│   ├── schema.yaml                            # ⭐ Config schema
│   └── config-templates/                      # 5 example configs
│       ├── web-app-config.yaml
│       ├── api-config.yaml
│       └── [3 more configs]
└── commands/
    └── vibey.md                               # ⭐ /vibey command

scripts/
├── validate-config.py                         # ⭐ Config validator
└── render-template.py                         # ⭐ Template renderer
```

### Generated Files
```
project-config.yaml                            # ⭐ Your project config
CLAUDE.md                                      # ⭐ Generated context file
docs/
├── sprints/
│   └── sprint-001-plan.md                     # ⭐ First sprint plan
├── security/
│   └── security-report-sprint-001.md          # Security reports
├── operations/
│   └── logging-audit-sprint-001.md            # Logging audits
└── ORCHESTRATION.md                           # Orchestration guide
```

### Most Important Files
1. **`.claude/commands/vibey.md`** - Entry point for setup
2. **`.claude/workflows/framework-initialization.md`** - Setup workflow
3. **`.claude/templates/CLAUDE.md.template`** - Main template
4. **`config/schema.yaml`** - Config schema
5. **`scripts/validate-config.py`** - Config validator
6. **`scripts/render-template.py`** - Template renderer
7. **`project-config.yaml`** - Your project configuration (generated)
8. **`CLAUDE.md`** - Your project context (generated)

---

## Quick Command Reference

### Scenario 1: New Repo
```bash
mkdir my-project && cd my-project
git init
pip install pyyaml jinja2
git clone https://github.com/fredabood/vibey.git .claude
claude-code .
# Then type: /vibey
```

### Scenario 2: Existing Repo Without .claude
```bash
cd existing-project
pip install pyyaml jinja2
git clone https://github.com/fredabood/vibey.git .claude
claude-code .
# Then type: /vibey
```

### Scenario 3: Existing Repo With .claude
```bash
cd legacy-project
cp -r .claude .claude-backup-$(date +%Y%m%d)
mv .claude .claude-custom
pip install pyyaml jinja2
git clone https://github.com/fredabood/vibey.git .claude
# Manually merge custom content from .claude-custom
claude-code .
# Then type: /vibey
```

**Every scenario ends the same way: Type `/vibey` and have a conversation!**

---

## Key Takeaways

### All Scenarios Share:
1. **Install Python dependencies** (pyyaml, jinja2)
2. **Clone Vibey as .claude** directory (or merge with existing)
3. **Start Claude Code** in your project
4. **Type `/vibey`** to begin conversational setup
5. **First sprint planning** integrated into initialization

### Scenario-Specific Notes:

**Scenario 1 (New Repo):**
- Fastest setup (~30 minutes)
- No existing code to analyze
- Framework is the foundation

**Scenario 2 (Existing Without .claude):**
- Claude analyzes existing codebase
- Infers project type and tech stack
- First sprint focuses on quality + new features
- Non-invasive installation

**Scenario 3 (Existing With .claude):**
- Backup original .claude first!
- Merge Vibey with custom content
- Preserve critical rules and custom agents
- Lower quality thresholds for legacy code
- Most complex but most powerful

### Time Investment:
- **Installation:** 2-5 minutes
- **`/vibey` conversation:** 5-15 minutes
- **First sprint planning:** 10-20 minutes
- **Total:** 20-40 minutes to complete setup

### Result:
- Complete framework installed
- Project configured
- CLAUDE.md generated
- First sprint planned
- Ready to build with quality enforcement!

---

**Questions?** Check `docs/ORCHESTRATION.md` or `QUICK_START.md` for more details.
