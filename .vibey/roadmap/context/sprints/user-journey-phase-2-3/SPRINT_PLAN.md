# Sprint 2.3: Persona-Based User Journeys

**Sprint ID:** `01KC81GRE3GXVPVSCMD19FC4YQ`
**Track:** User Journey Audit & Documentation Coverage
**Status:** Not Started
**Tasks:** 7

## Overview

This sprint creates detailed user personas and maps their complete journeys through the Vibey framework. The goal is to ensure documentation covers all user types and their specific needs, from first-time setup to advanced integration.

## Success Criteria

1. 5 distinct user personas fully defined
2. Complete journey map for each persona
3. Every CLI command mapped to at least one persona journey
4. Every MCP tool mapped to at least one persona journey
5. Coverage matrix identifying documentation gaps

---

## Persona Overview

| Persona | Primary Goal | Key Features Used |
|---------|--------------|-------------------|
| **New User** | Get started quickly | `init`, `status`, `show`, basic workflow |
| **Active Developer** | Daily productivity | `start`, `complete`, `context`, `activity` |
| **Project Lead** | Roadmap management | `create-*`, `status`, `summarize`, `checkpoint` |
| **Contributor** | Framework development | `validate`, `test`, git hooks, code standards |
| **Platform Integrator** | MCP/adapter integration | MCP tools, `deploy`, `export`, adapters |

---

## Task Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  [Task 1] Define User Personas                                  │
│      │                                                          │
│      ├──────────────┬──────────────┬──────────────┬────────┐    │
│      ▼              ▼              ▼              ▼        ▼    │
│  [Task 2]       [Task 3]       [Task 4]       [Task 5]  [Task 6]│
│  New User       Active Dev     Project Lead   Contrib   Platform│
│  Journey        Journey        Journey        Journey   Journey │
│      │              │              │              │        │    │
│      └──────────────┴──────────────┴──────────────┴────────┘    │
│                              │                                  │
│                              ▼                                  │
│                    [Task 7] Coverage Matrix                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Task 1: Define User Personas

**ID:** `01KC81GRE3GXVPVSCMD19FC4YR`
**Type:** Documentation
**Priority:** Medium
**Estimated Tokens:** 20,000

### Objective

Create detailed persona definitions that capture the goals, context, pain points, and success criteria for each user type.

### Persona Template

```markdown
## Persona: [Name]

### Profile
- **Role:** [Job title/role]
- **Experience Level:** [Beginner/Intermediate/Expert]
- **Technical Background:** [Languages, tools, platforms]
- **Time Investment:** [Hours per week with Vibey]

### Goals
1. Primary goal
2. Secondary goal
3. Tertiary goal

### Context
- **Environment:** [IDE, terminal, OS]
- **Team Size:** [Solo/Small team/Large team]
- **Project Type:** [Web app, API, ML, etc.]

### Pain Points
1. Pain point 1
2. Pain point 2
3. Pain point 3

### Success Criteria
- What does success look like for this persona?

### Key Questions
- What questions do they ask most frequently?

### Feature Priorities
| Priority | Features |
|----------|----------|
| Must Have | ... |
| Should Have | ... |
| Nice to Have | ... |
```

### Persona Definitions

#### 1. New User (Nina)

```markdown
## Persona: Nina the New User

### Profile
- **Role:** Software Developer
- **Experience Level:** Beginner with Vibey, Intermediate developer
- **Technical Background:** Python, JavaScript, familiar with CLI tools
- **Time Investment:** 2-4 hours for initial setup, then as needed

### Goals
1. Get Vibey installed and configured quickly
2. Understand what Vibey can do for their project
3. See value within the first 30 minutes

### Context
- **Environment:** VS Code, macOS/Linux terminal
- **Team Size:** Solo or small team (2-5)
- **Project Type:** Web application or API

### Pain Points
1. Unclear installation steps
2. Too many options without guidance
3. Can't find "getting started" documentation
4. Overwhelmed by feature complexity

### Success Criteria
- Vibey initialized in under 10 minutes
- First roadmap created and understood
- Can run basic status commands

### Key Questions
- "How do I install Vibey?"
- "What's a track/sprint/task?"
- "Where do I start?"
- "What's the simplest workflow?"

### Feature Priorities
| Priority | Features |
|----------|----------|
| Must Have | `init`, `status`, `show`, basic help |
| Should Have | `create-track`, `create-sprint` |
| Nice to Have | Integrations, advanced features |
```

#### 2. Active Developer (Alex)

```markdown
## Persona: Alex the Active Developer

### Profile
- **Role:** Full-stack Developer
- **Experience Level:** Intermediate with Vibey
- **Technical Background:** Multiple languages, CI/CD, agile workflows
- **Time Investment:** 1-2 hours daily

### Goals
1. Track daily work efficiently
2. Quickly find context for current tasks
3. Update progress without friction
4. Maintain momentum between sessions

### Context
- **Environment:** IDE with terminal, multiple monitors
- **Team Size:** Small to medium team (3-10)
- **Project Type:** Active development project

### Pain Points
1. Context switching between tasks
2. Forgetting what was in progress
3. Losing track of blockers
4. Manual status updates feel tedious

### Success Criteria
- Resume work instantly each session
- Update task status in <30 seconds
- Always know what's blocked and why

### Key Questions
- "What was I working on?"
- "What's blocking this task?"
- "What should I work on next?"
- "How do I add context to a task?"

### Feature Priorities
| Priority | Features |
|----------|----------|
| Must Have | `start`, `complete`, `status`, `context` |
| Should Have | `activity`, `show`, `add-context` |
| Nice to Have | `auto-progress`, `summarize` |
```

#### 3. Project Lead (Pat)

```markdown
## Persona: Pat the Project Lead

### Profile
- **Role:** Tech Lead / Engineering Manager
- **Experience Level:** Advanced with Vibey
- **Technical Background:** Architecture, planning, team coordination
- **Time Investment:** 3-5 hours weekly for roadmap management

### Goals
1. Plan and organize work into tracks and sprints
2. Track progress across multiple workstreams
3. Communicate status to stakeholders
4. Identify and resolve blockers early

### Context
- **Environment:** Mixed CLI and potential UI
- **Team Size:** Medium to large (5-20)
- **Project Type:** Multi-track initiatives

### Pain Points
1. Keeping roadmap up to date
2. Progress visibility across tracks
3. Dependency management complexity
4. Reporting overhead

### Success Criteria
- Roadmap reflects reality
- Can generate status reports quickly
- Dependencies are visible and managed
- Team can self-serve progress info

### Key Questions
- "What's the overall progress?"
- "Which sprints are at risk?"
- "What are the cross-track dependencies?"
- "How do I restructure the roadmap?"

### Feature Priorities
| Priority | Features |
|----------|----------|
| Must Have | `status`, `create-*`, `show`, `summarize` |
| Should Have | `checkpoint`, `validate-*`, `repair` |
| Nice to Have | Reports, visualizations, exports |
```

#### 4. Contributor (Chris)

```markdown
## Persona: Chris the Contributor

### Profile
- **Role:** Open Source Contributor / Framework Developer
- **Experience Level:** Expert developer, learning Vibey internals
- **Technical Background:** Python, software architecture, testing
- **Time Investment:** Variable, project-based

### Goals
1. Understand framework architecture quickly
2. Make changes without breaking things
3. Follow contribution guidelines
4. Get PRs merged efficiently

### Context
- **Environment:** Full development setup, testing tools
- **Team Size:** Open source community
- **Project Type:** Framework development

### Pain Points
1. Understanding codebase organization
2. Running and writing tests
3. Meeting code quality standards
4. Understanding roadmap/task system

### Success Criteria
- Can navigate codebase confidently
- Tests pass locally before PR
- Understands commit message conventions
- Knows how roadmap relates to code

### Key Questions
- "How is the code organized?"
- "How do I run tests?"
- "What are the coding standards?"
- "How do I link commits to tasks?"

### Feature Priorities
| Priority | Features |
|----------|----------|
| Must Have | `validate`, git hooks, tests, CONTRIBUTING.md |
| Should Have | `add-commit`, `sync-commits`, `verify-*` |
| Nice to Have | Architecture docs, ADRs |
```

#### 5. Platform Integrator (Sam)

```markdown
## Persona: Sam the Platform Integrator

### Profile
- **Role:** Platform Engineer / Tool Developer
- **Experience Level:** Expert developer
- **Technical Background:** APIs, protocols, integrations
- **Time Investment:** Project-based integration work

### Goals
1. Connect AI assistant to Vibey via MCP
2. Build custom adapters for their platform
3. Expose roadmap functionality programmatically
4. Extend Vibey for specific needs

### Context
- **Environment:** Multiple platforms, API testing tools
- **Team Size:** Platform team (2-5)
- **Project Type:** Integration/tooling

### Pain Points
1. MCP documentation gaps
2. Unclear adapter interface
3. Testing integrations
4. Versioning and compatibility

### Success Criteria
- MCP connection working
- Can call all relevant tools
- Understand resource/prompt patterns
- Can build custom tools

### Key Questions
- "How do I connect via MCP?"
- "What tools are available?"
- "How do I build an adapter?"
- "What's the resource URI format?"

### Feature Priorities
| Priority | Features |
|----------|----------|
| Must Have | MCP server, tools, MCP_REFERENCE.md |
| Should Have | `deploy`, `export`, adapter docs |
| Nice to Have | Custom tool creation, SDK |
```

### Output

**File:** `docs/personas/USER_PERSONAS.md`

### Acceptance Criteria

- [ ] All 5 personas fully defined
- [ ] Consistent template used
- [ ] Pain points reflect real user feedback
- [ ] Feature priorities align with CLI capabilities
- [ ] Personas are distinct and non-overlapping

---

## Task 2: Map New User Journey

**ID:** `01KC81GRE3GXVPVSCMD19FC4YS`
**Type:** Documentation
**Priority:** Medium
**Estimated Tokens:** 25,000

### Objective

Document the complete journey for a new user from discovery to productive usage.

### Journey Stages

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           NEW USER JOURNEY                                   │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────────────┤
│  Discovery  │ Installation│ First Steps │ Basic Usage │ Continued Learning  │
│             │             │             │             │                     │
│ - Hear about│ - pip/pipx  │ - vibey init│ - status    │ - Advanced features │
│   Vibey     │ - Clone repo│ - First     │ - show      │ - Join community    │
│ - Read docs │ - Verify    │   roadmap   │ - start     │ - Provide feedback  │
│ - Evaluate  │   install   │ - Config    │ - complete  │                     │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────────────┘
```

### Journey Map Document

**File:** `docs/journeys/JOURNEY_NEW_USER.md`

```markdown
# New User Journey

> From discovery to first productive use of Vibey

## Overview

| Attribute | Value |
|-----------|-------|
| **Persona** | Nina the New User |
| **Duration** | 30-60 minutes |
| **Outcome** | Working roadmap, basic commands mastered |

---

## Stage 1: Discovery (5-10 minutes)

### User Goal
Understand what Vibey is and if it fits my needs.

### Entry Points
1. GitHub repository
2. Recommendation from colleague
3. Search for "AI coding assistant roadmap tool"
4. Blog post or tutorial

### Information Needs
- What problem does Vibey solve?
- Is it right for my project/team?
- What does it cost? (Free/OSS)
- What platforms are supported?

### Key Content
- README.md (first impression)
- docs/getting-started/QUICK_START.md
- Feature overview
- Screenshots/demos

### Success Metrics
- User clicks "Get Started" or begins installation
- Spends >2 minutes reading docs

### CLI Commands
*None at this stage*

---

## Stage 2: Installation (5-10 minutes)

### User Goal
Get Vibey installed and ready to use.

### Steps

#### 2.1 Choose Installation Method

| Method | Command | Best For |
|--------|---------|----------|
| pipx (recommended) | `pipx install vibey` | Most users |
| pip | `pip install vibey` | Virtual env users |
| From source | `git clone && pip install -e .` | Contributors |

#### 2.2 Verify Installation

```bash
# Check version
vibey --version

# Expected output
Vibey Agent Framework v2.5.0
```

#### 2.3 Explore Help

```bash
# See all commands
vibey --help

# See roadmap commands
vibey roadmap --help
```

### Troubleshooting

| Problem | Solution |
|---------|----------|
| Command not found | Check PATH, restart terminal |
| Permission denied | Use `--user` flag or virtual env |
| Missing dependencies | `pip install vibey[all]` |

### CLI Commands Used
- `vibey --version`
- `vibey --help`
- `vibey roadmap --help`

---

## Stage 3: First Steps (10-15 minutes)

### User Goal
Initialize Vibey for my project and create first roadmap items.

### Steps

#### 3.1 Navigate to Project

```bash
cd /path/to/my/project
```

#### 3.2 Initialize Roadmap

```bash
vibey roadmap init

# Interactive prompts:
# - Project name: My Web App
# - Description: A modern web application
# - Create example track? (Y/n): Y
```

**What happens:**
- Creates `.vibey/` directory
- Creates `.vibey/roadmap/` structure
- Initializes SQLite database
- Creates example track if requested

#### 3.3 Understand the Structure

```
.vibey/
├── config/
│   └── roadmap.yaml      # Roadmap configuration
├── roadmap/
│   ├── tracks/           # Track YAML files
│   ├── sprints/          # Sprint YAML files
│   ├── tasks/            # Task YAML files
│   └── context/          # Context documents
└── roadmap.db            # SQLite database
```

#### 3.4 View Initial Status

```bash
vibey roadmap status

# Output shows:
# - Tracks with progress bars
# - Active sprints
# - Task counts
```

### CLI Commands Used
- `vibey roadmap init`
- `vibey roadmap status`

### Key Concepts Introduced
- Track: Major work area (like an epic)
- Sprint: Time-boxed iteration
- Task: Individual work item

---

## Stage 4: Basic Usage (10-15 minutes)

### User Goal
Create and manage roadmap items, track progress.

### Steps

#### 4.1 Create a Track

```bash
vibey roadmap create-track \
  --name "Authentication System" \
  --priority high
```

#### 4.2 Create a Sprint

```bash
vibey roadmap create-sprint \
  --track <track-id> \
  --name "Sprint 1: Basic Auth"
```

#### 4.3 Create Tasks

```bash
vibey roadmap create-task \
  --sprint <sprint-id> \
  --title "Implement login form" \
  --type development
```

#### 4.4 Start Working

```bash
# Start a task
vibey roadmap start <task-id>

# Check status
vibey roadmap status

# Complete when done
vibey roadmap complete <task-id>
```

#### 4.5 View Details

```bash
# Show track details
vibey roadmap show <track-id>

# Show sprint with tasks
vibey roadmap show <sprint-id>
```

### CLI Commands Used
- `vibey roadmap create-track`
- `vibey roadmap create-sprint`
- `vibey roadmap create-task`
- `vibey roadmap start`
- `vibey roadmap complete`
- `vibey roadmap show`

---

## Stage 5: Continued Learning

### User Goal
Deepen knowledge, discover advanced features.

### Next Steps
1. Read CLI_REFERENCE.md for all commands
2. Explore `vibey roadmap context` for AI integration
3. Try `vibey roadmap summarize` for reports
4. Set up git hooks: `vibey roadmap install-hooks`
5. Join community/provide feedback

### Graduation Criteria
- Can create and manage roadmap items independently
- Understands track → sprint → task hierarchy
- Knows where to find help

### Paths Forward
- → Active Developer journey (daily usage)
- → Project Lead journey (team management)
- → Contributor journey (framework development)

---

## Command Summary

| Stage | Commands |
|-------|----------|
| Installation | `--version`, `--help` |
| First Steps | `init`, `status` |
| Basic Usage | `create-*`, `start`, `complete`, `show` |
| Advanced | `context`, `summarize`, `install-hooks` |

---

## Common Mistakes

| Mistake | Prevention |
|---------|------------|
| Skipping `init` | Clear error message guides to init |
| Wrong directory | Check for `.vibey/` presence |
| Using IDs vs slugs | Both work, show examples of each |
| Forgetting to start tasks | Status shows "not_started" tasks |

---

## Feedback Collection

At journey end, prompt user to:
1. Rate experience (1-5)
2. Report confusion points
3. Suggest improvements
4. Join community
```

### Acceptance Criteria

- [ ] All 5 stages documented
- [ ] CLI commands listed per stage
- [ ] Troubleshooting included
- [ ] Common mistakes addressed
- [ ] Links to next journeys

---

## Task 3: Map Active Developer Journey

**ID:** `01KC81GRE3GXVPVSCMD19FC4YT`
**Type:** Documentation
**Priority:** Medium
**Estimated Tokens:** 25,000

### Objective

Document the daily workflow for developers actively using Vibey.

### Journey Map Document

**File:** `docs/journeys/JOURNEY_ACTIVE_DEVELOPER.md`

### Journey Stages

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ACTIVE DEVELOPER JOURNEY                              │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────────────┤
│ Session     │ Task        │ Working     │ Progress    │ Session             │
│ Start       │ Selection   │ on Task     │ Updates     │ End                 │
│             │             │             │             │                     │
│ - activity  │ - status    │ - context   │ - complete  │ - summarize         │
│ - status    │ - show      │ - add-ctx   │ - add-commit│ - checkpoint        │
│ - resume    │ - start     │ - blockers  │ - activity  │                     │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────────────┘
```

### Daily Workflow

#### Morning Routine
```bash
# 1. See what happened since last session
vibey roadmap activity

# 2. Check current status
vibey roadmap status

# 3. Resume in-progress task or pick new one
vibey roadmap show <task-id>
vibey roadmap start <task-id>
```

#### During Work
```bash
# Get task context for AI assistant
vibey roadmap context <task-id>

# Add context files as you work
vibey roadmap add-context <task-id> --file notes.md

# Check for blockers
vibey roadmap show <task-id>
```

#### Completing Work
```bash
# Link your commit
vibey roadmap add-commit <task-id> --sha abc123

# Complete the task
vibey roadmap complete <task-id>

# Start next task
vibey roadmap start <next-task-id>
```

#### End of Day
```bash
# Summarize progress
vibey roadmap summarize <sprint-id>

# Create checkpoint
vibey roadmap checkpoint create "End of day Dec 12"
```

### CLI Commands Used
- `vibey roadmap activity`
- `vibey roadmap status`
- `vibey roadmap show`
- `vibey roadmap start`
- `vibey roadmap context`
- `vibey roadmap add-context`
- `vibey roadmap add-commit`
- `vibey roadmap complete`
- `vibey roadmap summarize`
- `vibey roadmap checkpoint`

### Acceptance Criteria

- [ ] Daily workflow fully documented
- [ ] Context management covered
- [ ] Git integration explained
- [ ] Efficiency tips included
- [ ] Links to reference docs

---

## Task 4: Map Project Lead Journey

**ID:** `01KC81GRE3GXVPVSCMD19FC4YV`
**Type:** Documentation
**Priority:** Medium
**Estimated Tokens:** 25,000

### Objective

Document the roadmap management workflow for project leads.

### Journey Map Document

**File:** `docs/journeys/JOURNEY_PROJECT_LEAD.md`

### Journey Stages

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PROJECT LEAD JOURNEY                                 │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────────────┤
│ Planning    │ Sprint      │ Progress    │ Maintenance │ Reporting           │
│             │ Management  │ Tracking    │             │                     │
│ - create-   │ - create-   │ - status    │ - repair    │ - summarize         │
│   track     │   sprint    │ - show      │ - validate  │ - doc-changelog     │
│ - create-   │ - start     │ - activity  │ - checkpoint│ - export            │
│   from-plan │ - complete  │ - blockers  │ - db ops    │                     │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────────────┘
```

### Key Workflows

#### Creating from Plan Document
```bash
# Convert a planning doc to sprint
vibey roadmap create-from-plan plan.md --track <track-id>
```

#### Progress Monitoring
```bash
# Overall status
vibey roadmap status

# Detailed track view
vibey roadmap show <track-id> --verbose

# Find blockers across roadmap
vibey roadmap show blockers
```

#### Roadmap Maintenance
```bash
# Validate integrity
vibey roadmap validate-fast

# Repair issues
vibey roadmap repair --all

# Create checkpoint before changes
vibey roadmap checkpoint create "Pre-restructure"
```

### CLI Commands Used
- `vibey roadmap create-track`
- `vibey roadmap create-sprint`
- `vibey roadmap create-task`
- `vibey roadmap create-from-plan`
- `vibey roadmap status`
- `vibey roadmap show`
- `vibey roadmap summarize`
- `vibey roadmap validate-fast`
- `vibey roadmap repair`
- `vibey roadmap checkpoint`
- `vibey roadmap doc-changelog`

### Acceptance Criteria

- [ ] Planning workflow documented
- [ ] Progress tracking covered
- [ ] Maintenance tasks explained
- [ ] Reporting capabilities shown
- [ ] Team coordination patterns

---

## Task 5: Map Contributor Journey

**ID:** `01KC81GRE3GXVPVSCMD19FC4YW`
**Type:** Documentation
**Priority:** Medium
**Estimated Tokens:** 25,000

### Objective

Document the workflow for contributors to the Vibey framework.

### Journey Map Document

**File:** `docs/journeys/JOURNEY_CONTRIBUTOR.md`

### Journey Stages

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CONTRIBUTOR JOURNEY                                 │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────────────┤
│ Setup       │ Understand  │ Make        │ Testing     │ Submit              │
│             │ Architecture│ Changes     │             │                     │
│ - Clone     │ - Read docs │ - Edit code │ - pytest    │ - Commit format     │
│ - Install   │ - Explore   │ - Follow    │ - validate  │ - PR process        │
│ - Verify    │   codebase  │   standards │ - hooks     │ - Review            │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────────────┘
```

### Key Workflows

#### Development Setup
```bash
# Clone and install
git clone https://github.com/fredabood/vibey.git
cd vibey
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Install git hooks
vibey roadmap install-hooks

# Verify setup
pytest tests/ -v
```

#### Making Changes
```bash
# Create branch
git checkout -b feature/my-feature

# Make changes following standards
# - Use type hints
# - Add docstrings
# - Follow existing patterns

# Run validation
vibey validate

# Run tests
pytest tests/ -v
```

#### Submitting Changes
```bash
# Commit with roadmap link
git commit -m "feat(roadmap): Add new feature

Task: 01KC2D0JK7READW9KAK1HBX4B8"

# Or use CLI to link
vibey roadmap add-commit <task-id> --sha HEAD
```

### CLI Commands Used
- `vibey roadmap install-hooks`
- `vibey roadmap check-hooks`
- `vibey roadmap add-commit`
- `vibey roadmap sync-commits`
- `vibey roadmap verify-commits`
- `vibey validate`

### Acceptance Criteria

- [ ] Setup steps complete
- [ ] Coding standards documented
- [ ] Test requirements explained
- [ ] Commit message format specified
- [ ] PR process outlined

---

## Task 6: Map Platform Integrator Journey

**ID:** `01KC81GRE3GXVPVSCMD19FC4YX`
**Type:** Documentation
**Priority:** Medium
**Estimated Tokens:** 25,000

### Objective

Document the MCP integration workflow for platform integrators.

### Journey Map Document

**File:** `docs/journeys/JOURNEY_PLATFORM_INTEGRATOR.md`

### Journey Stages

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PLATFORM INTEGRATOR JOURNEY                            │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────────────┤
│ Understand  │ Connect     │ Use Tools   │ Build       │ Deploy              │
│ MCP         │ Server      │             │ Adapter     │                     │
│             │             │             │             │                     │
│ - Protocol  │ - Start     │ - List      │ - Adapter   │ - deploy            │
│   overview  │   server    │   tools     │   pattern   │ - export            │
│ - Ref docs  │ - Configure │ - Call      │ - Custom    │ - Production        │
│             │   client    │   tools     │   tools     │   setup             │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────────────┘
```

### Key Workflows

#### Starting MCP Server
```bash
# Start MCP server
vibey mcp start

# Or run directly
python -m vibey.mcp.server
```

#### Connecting from Client
```python
# Example Python client
import mcp

async def connect():
    client = mcp.Client()
    await client.connect("stdio", ["vibey", "mcp", "start"])

    # List available tools
    tools = await client.list_tools()
    for tool in tools:
        print(f"- {tool.name}: {tool.description}")

    # Call a tool
    result = await client.call_tool(
        "vibey_roadmap_status",
        {}
    )
    print(result)
```

#### Using Resources and Prompts
```python
# List resources
resources = await client.list_resources()

# Read a resource
content = await client.read_resource(
    "vibey://workflows/planning/sprint-planning"
)

# Get a prompt
prompt = await client.get_prompt(
    "quality_gate_security",
    {"task_id": "01KC..."}
)
```

### MCP Tools Used
- `vibey_roadmap_status`
- `vibey_start_task`
- `vibey_complete_task`
- `vibey_query_track`
- `vibey_list_blockers`
- All other MCP tools

### CLI Commands Used
- `vibey mcp start`
- `vibey deploy`
- `vibey export`

### Acceptance Criteria

- [ ] MCP protocol explained
- [ ] Connection examples provided
- [ ] All tool categories covered
- [ ] Resource/prompt usage shown
- [ ] Adapter pattern documented

---

## Task 7: Create Journey-to-Feature Coverage Matrix

**ID:** `01KC81GRE3GXVPVSCMD19FC4YY`
**Type:** Research
**Priority:** Medium
**Estimated Tokens:** 15,000

### Objective

Build a matrix showing which features are covered by which persona journeys, identifying documentation gaps.

### Output

**File:** `docs/journeys/JOURNEY_COVERAGE_MATRIX.yaml`

### Matrix Structure

```yaml
# JOURNEY_COVERAGE_MATRIX.yaml
# Maps CLI commands and MCP tools to persona journeys

metadata:
  generated: 2025-12-12
  version: 1.0.0
  total_commands: 50+
  total_tools: 24+
  personas: 5

cli_commands:
  # Roadmap Core
  roadmap_init:
    description: "Initialize new roadmap"
    journeys: [new_user]
    stage: first_steps
    priority: must_have
    documentation:
      - docs/getting-started/QUICK_START.md
      - docs/journeys/JOURNEY_NEW_USER.md

  roadmap_status:
    description: "Show roadmap status"
    journeys: [new_user, active_developer, project_lead]
    stage: all
    priority: must_have
    documentation:
      - docs/reference/CLI_REFERENCE.md

  roadmap_start:
    description: "Start a task or sprint"
    journeys: [new_user, active_developer]
    stage: basic_usage
    priority: must_have
    documentation:
      - docs/journeys/JOURNEY_NEW_USER.md
      - docs/journeys/JOURNEY_ACTIVE_DEVELOPER.md

  roadmap_complete:
    description: "Complete a task or sprint"
    journeys: [new_user, active_developer]
    stage: basic_usage
    priority: must_have

  roadmap_context:
    description: "Get AI-optimized context"
    journeys: [active_developer, platform_integrator]
    stage: working
    priority: should_have

  roadmap_create_track:
    description: "Create a new track"
    journeys: [new_user, project_lead]
    stage: planning
    priority: must_have

  roadmap_create_sprint:
    description: "Create a new sprint"
    journeys: [new_user, project_lead]
    stage: planning
    priority: must_have

  roadmap_create_task:
    description: "Create a new task"
    journeys: [new_user, project_lead]
    stage: planning
    priority: must_have

  roadmap_show:
    description: "Show details for item"
    journeys: [new_user, active_developer, project_lead]
    stage: all
    priority: must_have

  roadmap_activity:
    description: "Show recent activity"
    journeys: [active_developer, project_lead]
    stage: monitoring
    priority: should_have

  roadmap_summarize:
    description: "Generate summary"
    journeys: [active_developer, project_lead]
    stage: reporting
    priority: should_have

  roadmap_add_commit:
    description: "Link git commit to task"
    journeys: [active_developer, contributor]
    stage: git_integration
    priority: should_have

  roadmap_install_hooks:
    description: "Install git hooks"
    journeys: [contributor, project_lead]
    stage: setup
    priority: must_have

  roadmap_validate_fast:
    description: "Fast validation"
    journeys: [contributor, project_lead]
    stage: maintenance
    priority: should_have

  roadmap_repair:
    description: "Auto-repair issues"
    journeys: [project_lead]
    stage: maintenance
    priority: should_have

  roadmap_checkpoint:
    description: "Create checkpoint"
    journeys: [project_lead, active_developer]
    stage: maintenance
    priority: nice_to_have

  # ... continue for all commands

mcp_tools:
  vibey_roadmap_status:
    description: "Get roadmap status via MCP"
    journeys: [platform_integrator]
    priority: must_have

  vibey_start_task:
    description: "Start task via MCP"
    journeys: [platform_integrator]
    priority: must_have

  vibey_complete_task:
    description: "Complete task via MCP"
    journeys: [platform_integrator]
    priority: must_have

  # ... continue for all MCP tools

coverage_summary:
  by_persona:
    new_user:
      cli_commands: 12
      mcp_tools: 0
      coverage_percent: 24%

    active_developer:
      cli_commands: 18
      mcp_tools: 0
      coverage_percent: 36%

    project_lead:
      cli_commands: 22
      mcp_tools: 0
      coverage_percent: 44%

    contributor:
      cli_commands: 10
      mcp_tools: 0
      coverage_percent: 20%

    platform_integrator:
      cli_commands: 5
      mcp_tools: 24
      coverage_percent: 58%

  gaps:
    uncovered_commands:
      - roadmap_db_*
      - roadmap_migrate_*
      - roadmap_sync_*

    documentation_needed:
      - "Database operations guide"
      - "Migration guide"
      - "Sync workflow documentation"

    low_coverage_features:
      - "Validation commands"
      - "Advanced editing"
      - "Standards system"
```

### Analysis Requirements

1. **Completeness Check:** Every CLI command mapped to at least one journey
2. **Gap Identification:** Commands not covered by any journey
3. **Priority Analysis:** Critical features vs. nice-to-have
4. **Documentation Links:** Connect commands to existing docs

### Acceptance Criteria

- [ ] All CLI commands mapped
- [ ] All MCP tools mapped
- [ ] Coverage percentages calculated
- [ ] Gaps clearly identified
- [ ] Recommendations for gap closure

---

## File Structure After Sprint

```
docs/
├── personas/
│   └── USER_PERSONAS.md           # Task 1
├── journeys/
│   ├── JOURNEY_NEW_USER.md        # Task 2
│   ├── JOURNEY_ACTIVE_DEVELOPER.md # Task 3
│   ├── JOURNEY_PROJECT_LEAD.md    # Task 4
│   ├── JOURNEY_CONTRIBUTOR.md     # Task 5
│   ├── JOURNEY_PLATFORM_INTEGRATOR.md # Task 6
│   └── JOURNEY_COVERAGE_MATRIX.yaml # Task 7
│
.vibey/roadmap/context/sprints/user-journey-phase-2-3/
└── SPRINT_PLAN.md                 # This document
```

---

## Dependencies

| Sprint | Dependency Type | Notes |
|--------|-----------------|-------|
| 2.1 CLI Reference | Soft | Reference generated CLI docs |
| 2.2 MCP Reference | Soft | Reference generated MCP docs |

**Note:** This sprint can run in parallel with 2.1 and 2.2.

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Personas too similar | Medium | Medium | Distinct goals and pain points |
| Journeys too long | Medium | Low | Stage-based breakdown |
| CLI changes invalidate content | Low | Medium | Link to generated refs |
| Missing user feedback | High | Medium | Use existing gap analysis |
| Scope creep | Medium | Medium | Strict task boundaries |

---

## Definition of Done

- [ ] All 7 tasks completed
- [ ] 5 personas fully defined
- [ ] 5 journey maps complete
- [ ] Coverage matrix generated
- [ ] All gaps identified
- [ ] Documentation reviewed
- [ ] Cross-links to reference docs working
- [ ] Sprint summary written
