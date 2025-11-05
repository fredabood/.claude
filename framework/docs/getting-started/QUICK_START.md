# Vibey Framework - Quick Start Guide

Get up and running with Vibey in under 10 minutes! 🚀

---

## What is Vibey?

Vibey is an **agent orchestration framework** for Claude Code that provides:
- **12 specialized agents** (security, ML, web dev, performance, docs, etc.)
- **16 structured workflows** (sprint planning, feature development, ML model training)
- **22 handoff templates** (API specs, security reports, design docs)
- **Automatic quality gates** (security, testing, logging, documentation)
- **Config-driven orchestration** (Claude knows which agents to use automatically)

**Perfect for:** Web apps, APIs, ML projects, data platforms, infrastructure

---

## Installation (1 minute)

### Step 1: Install Python Dependencies

```bash
# Required for config validation and template rendering
pip install pyyaml jinja2
```

### Step 2: Clone Vibey Framework

```bash
# Navigate to your project
cd /path/to/your-project

# Clone framework
git clone https://github.com/fredabood/vibey.git .vibey
```

**That's it for installation!**

---

## Initialization (5-10 minutes)

### Step 3: Start Claude Code

```bash
# Start Claude Code in your project directory
claude-code
# or just open the project in your Claude Code editor
```

### Step 4: Run `/vibey` Command

In your first Claude Code conversation, type:

```
/vibey
```

**What happens next:** Claude will automatically deploy and initialize the framework through 3 phases:

**Phase 1: Deployment (1-2 minutes)**
- Detect if you have an existing `.claude/` directory
- If you do: Offer to backup and merge, or selectively merge
- If you don't: Deploy framework to `.claude/`
- Clean up `.vibey/` directory (removes framework repo metadata)

**Phase 2: Pre-Checks (<1 minute)**
- Check if git repository exists (offers to initialize)
- Verify Python dependencies installed
- Check for existing configuration

**Phase 3: Initialization (5-10 minutes conversational)**
Claude will start an interactive conversation to:

1. **Discover your project** (name, type, tech stack)
   - "What's your project called?"
   - "Is this a web app, API, ML project, data platform, or infrastructure?"
   - "What backend technology are you using?"
   - "What database?"

2. **Choose orchestration mode** (how agents are selected)
   - **Simple:** Explicit rules (best for learning)
   - **Balanced:** Smart pattern matching (⭐ recommended for most)
   - **Tiered:** Intelligent coordination (best for complex projects)

3. **Set quality standards**
   - Test coverage minimum (default: 90%)
   - Security score minimum (default: 85/100)
   - Logging audit minimum (default: 80/100)

4. **Generate configuration**
   - Creates `.claude/project-config.yaml` with all your answers
   - Validates configuration

5. **Generate .claude/CLAUDE.md**
   - Project-specific context file for Claude
   - Includes tech stack, standards, orchestration instructions

6. **Plan your first sprint**
   - "What are your goals for Sprint 1?"
   - Creates detailed sprint plan with tasks
   - Each task includes agent recommendations
   - Sets up quality gate requirements

**Duration:** 5-10 minutes of conversation

**Result:**
- ✅ `.claude/project-config.yaml` - Framework configuration
- ✅ `.claude/CLAUDE.md` - Project context for Claude
- ✅ `docs/sprints/sprint-001-plan.md` - First sprint plan
- ✅ `docs/` directory structure created
- ✅ Framework ready to use!

---

## Your First Sprint (Start Building!)

### Step 5: Pick a Task from Sprint Plan

Look at `docs/sprints/sprint-001-plan.md`. Each task includes:
- Clear description
- Estimated effort
- **Agent recommendations** (which agents to use)
- **Workflow guidance** (step-by-step process)
- **Handoff templates** (documentation to fill)
- Acceptance criteria

### Step 6: Tell Claude What to Build

Just describe what you want in natural language:

```
"I want to implement user authentication with JWT tokens"
```

**Claude automatically:**
1. Detects this is a security-critical feature
2. Launches appropriate agents:
   - Researcher Agent (if OAuth/JWT is new tech)
   - API Specialist (implement auth endpoints)
   - Security Reviewer (audit implementation)
   - Test Engineer (write comprehensive tests)
   - Documentation Engineer (document auth system)
3. Follows single-feature-development workflow
4. Runs quality gates before completion

**You don't have to specify agents or workflows** - Claude figures it out based on:
- Your orchestration mode (Simple/Balanced/Tiered)
- Agent trigger patterns
- Project type
- Sprint phase

### Step 7: Review Quality Gates

Before any task is marked complete, Claude runs quality gates:

- ✅ **Security review** (score ≥ 85)
- ✅ **Test coverage** (≥ 90%)
- ✅ **Logging audit** (score ≥ 80)
- ✅ **Documentation** updated

**If any gate fails, Claude will:**
- Tell you what failed
- Fix the issues
- Re-run the gate
- Only proceed when ALL gates pass

### Step 8: Continue Building

Repeat for each task in your sprint:
- Pick task
- Tell Claude what to build
- Claude orchestrates agents automatically
- Quality gates ensure high standards
- Task complete!

---

## Example: Complete First Sprint

### Real Conversation Flow

```
You: /vibey

Claude: Welcome! I'm going to help you set up the Vibey Agent Framework...
        What's your project called, and what does it do?

You: It's called "TaskMaster" - a task management app for remote teams

Claude: Got it! Is this primarily a:
        - Web application (frontend + backend)
        - API service (backend only)
        - ...

You: Web application

Claude: What's your backend technology stack?

You: Python with FastAPI

Claude: And what about the frontend?

You: React with TypeScript

Claude: What database(s) are you using?

You: PostgreSQL

Claude: [Continues with more questions about tech stack, team size, quality standards...]

        Now, an important choice: How should I orchestrate agents?
        [Explains 3 modes...]
        Which orchestration mode would you like? [D]

You: Balanced

Claude: ✓ Created .claude/project-config.yaml
        ✓ Generated .claude/CLAUDE.md
        ✓ Created documentation directories

        Perfect! Now let's plan your first sprint.
        What are your goals for the first sprint?

You: User authentication, task dashboard, and basic CRUD operations

Claude: [Analyzes requirements, creates sprint plan...]

        ✓ Sprint 1 plan created: docs/sprints/sprint-001-plan.md

        Your first sprint includes:
        - 8 tasks totaling ~40 hours estimated effort
        - Infrastructure setup (FastAPI + React + PostgreSQL)
        - User authentication with JWT
        - Task dashboard UI
        - CRUD endpoints for tasks

        Ready to start? Just tell me which task you want to work on!

You: Let's start with user authentication

Claude: [Automatically launches Researcher Agent to understand JWT best practices...]
        [Launches API Specialist to implement endpoints...]
        [Launches Security Reviewer to audit implementation...]
        [Launches Test Engineer to write tests...]
        [Runs quality gates...]

        ✅ User authentication complete!

        Quality gates:
        - Security: 92/100 ✅
        - Test coverage: 94% ✅
        - Logging audit: 88/100 ✅
        - Documentation: ✅

        What's next?
```

**Result:** Sprint 1 feature complete with high quality in ~2-4 hours!

---

## Orchestration Modes Explained

### Simple Mode - Explicit Rules

**How it works:** Claude follows keyword-based rules in .claude/CLAUDE.md

**Example:**
```
You: "I need a security review"
Claude: [Matches "security" → Launches Security Reviewer agent]
```

**Best for:** Small teams, learning the framework, maximum transparency

### Balanced Mode ⭐ (Recommended)

**How it works:** Claude pattern-matches your request against agent "trigger patterns"

**Example:**
```
You: "Implement JWT authentication"
Claude: [Matches patterns:]
        - "authentication" → Security Reviewer (high priority)
        - "JWT", "implement" → API Specialist (medium priority)
        - Implied: Test Engineer (development phase)
        [Launches all three agents automatically]
```

**Best for:** Most projects (90% of users should choose this)

### Tiered Mode - Intelligent Coordination

**How it works:** Three routing paths
- **Fast path:** Simple tasks handled directly
- **Smart path:** Complex tasks routed through Coordinator agent
- **Explicit path:** You name specific agent

**Example:**
```
You: "Implement auth with OAuth, JWT, 2FA, email verification, and password reset"
Claude: [Detects complexity → Launches Coordinator Agent]
Coordinator: [Analyzes requirements, reads project context, sequences 8 agents...]
             [Manages handoffs between agents...]
             [Verifies quality gates...]
             [Provides progress updates...]
```

**Best for:** Large/complex projects, enterprise teams

---

## Common Workflows

### Sprint Planning (Sprint 2+)

```
You: "Let's plan sprint 2"

Claude: [Automatically uses Sprint Planning Agent]
        [Reviews Sprint 1 results]
        [Asks about Sprint 2 goals]
        [Creates sprint-002-plan.md]
```

### Feature Development

```
You: "Build the user profile page"

Claude: [Launches Web Developer agent]
        [Follows frontend-feature-development workflow]
        [Builds components, styling, state management]
        [Runs quality gates]
        [Updates documentation]
```

### Security Review

```
You: "Run a security review on the auth code"

Claude: [Launches Security Reviewer agent]
        [Audits: OWASP Top 10, secrets, auth patterns]
        [Generates security report]
        [Provides recommendations]
```

### Performance Optimization

```
You: "The dashboard is loading slowly"

Claude: [Launches Performance Engineer agent]
        [Profiles code, identifies bottlenecks]
        [Recommends optimizations]
        [Launches Web Developer to implement fixes]
        [Verifies improvements]
```

### Documentation Updates

```
You: "Update the README with the new auth features"

Claude: [Launches Documentation Engineer agent]
        [Updates README.md, API docs, .claude/CLAUDE.md]
        [Ensures consistency]
```

---

## Quality Gates in Action

Every sprint enforces quality gates before completion:

### 1. Security Review
**What's checked:**
- OWASP Top 10 compliance
- Authentication/authorization
- Input validation
- Secrets management
- XSS, SQL injection, CSRF prevention

**Minimum score:** 85/100

### 2. Test Coverage
**What's checked:**
- Unit tests
- Integration tests
- Edge cases
- Error paths

**Minimum coverage:** 90%

### 3. Logging Audit
**What's checked:**
- Correlation IDs present
- Error context sufficient
- Log levels appropriate
- Performance metrics tracked

**Minimum score:** 80/100

### 4. Documentation Review
**What's checked:**
- README.md current
- .claude/CLAUDE.md updated
- API documentation complete
- Code comments present

**Result:** High-quality, production-ready code automatically

---

## Configuration Files

### .claude/project-config.yaml

Your project's configuration (generated by `/vibey`):

```yaml
project:
  name: "TaskMaster"
  type: "web-app"
  description: "Task management app for remote teams"

technology_stack:
  backend:
    language: "python"
    framework: "fastapi"
  frontend:
    language: "typescript"
    framework: "react"
  database:
    type: "postgresql"

framework:
  orchestration_mode: "balanced"  # simple, balanced, or tiered
  auto_agent_launch: true
  require_quality_gates: true

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

### .claude/CLAUDE.md

Project context for Claude (generated by `/vibey`):
- Technology stack details
- Architecture overview
- Coding standards
- Critical rules
- Quality gate requirements
- **Orchestration instructions** (mode-specific)
- Available agents and workflows

**Claude reads this file at the start of every session.**

---

## Changing Orchestration Mode

You can switch modes anytime:

```
You: "I'd like to switch to tiered orchestration mode"

Claude: [Updates .claude/project-config.yaml]
        [Regenerates .claude/CLAUDE.md with new instructions]
        "Switched to tiered orchestration mode!"
```

Or manually edit `.claude/project-config.yaml`:
```yaml
framework:
  orchestration_mode: "tiered"  # Change from "balanced"
```

Then regenerate .claude/CLAUDE.md:
```bash
python3 scripts/render-template.py \
  -c .claude/project-config.yaml \
  -t .claude/templates/CLAUDE.md.template \
  -o .claude/CLAUDE.md
```

---

## Advanced: Manual Config/Docs Generation

If you prefer not to use `/vibey`:

### Validate Config
```bash
python3 scripts/validate-config.py .claude/project-config.yaml
```

### Generate .claude/CLAUDE.md
```bash
python3 scripts/render-template.py \
  -c .claude/project-config.yaml \
  -t .claude/templates/CLAUDE.md.template \
  -o .claude/CLAUDE.md
```

### Generate All Documentation
```bash
# Render all templates in a directory
python3 scripts/render-template.py \
  -c .claude/project-config.yaml \
  -d .claude/templates/handoffs/ \
  --output-dir docs/handoffs/
```

---

## Troubleshooting

### "PyYAML not found"
```bash
pip install pyyaml
```

### "Jinja2 not found"
```bash
pip install jinja2
```

### "Claude isn't using agents"
**Check:**
1. `.claude/CLAUDE.md` is current (regenerate if needed)
2. `framework.auto_agent_launch: true` in config
3. Your request is specific enough for pattern matching

**Solution:** Be more explicit or name the agent:
```
"Run a security review using the security reviewer agent"
```

### "Quality gates keep failing"
**This is good!** Quality gates catch issues early.

**Solutions:**
- Read the quality gate report
- Fix the identified issues
- Re-run the quality check
- Only proceed when gates pass

---

## Directory Structure After Setup

```
your-project/
├── .claude/
│   ├── agents/              # 12 specialized agents
│   │   ├── planning/        # Sprint planning, researcher
│   │   ├── development/     # Web developer, ML engineer
│   │   ├── quality/         # Security, observability, performance
│   │   ├── documentation/   # Docs, diagrams, git
│   │   └── core/            # Coordinator (tiered mode)
│   ├── workflows/           # 16 structured workflows
│   ├── templates/           # 22 handoff templates
│   ├── config/              # Config schema and templates
│   ├── commands/            # /vibey slash command
│   └── README.md            # Framework documentation
├── scripts/
│   ├── validate-config.py   # Config validator
│   └── render-template.py   # Template renderer
├── docs/
│   ├── sprints/             # Sprint plans and summaries
│   ├── operations/          # Operational guides
│   ├── architecture/        # Architecture diagrams
│   ├── reference/           # Reference documentation
│   └── security/            # Security reports
├── .claude/project-config.yaml      # Project configuration
├── .claude/CLAUDE.md                # Project context for Claude
└── [your code]
```

---

## Next Steps

1. **✅ You're done with setup!** Framework is ready.

2. **Build your first feature**
   - Pick a task from sprint plan
   - Tell Claude what to build
   - Let orchestration and quality gates handle the rest

3. **Learn the framework**
   - Read `.claude/README.md` for agent details
   - Review workflows in `.claude/workflows/`
   - Check handoff templates in `.claude/templates/handoffs/`

4. **Explore orchestration modes**
   - Read `docs/ORCHESTRATION.md` for deep dive
   - Try different modes for your project

5. **Customize for your needs**
   - Adjust quality gate thresholds in `.claude/project-config.yaml`
   - Add custom rules to `.claude/CLAUDE.md`
   - Create custom handoff templates

---

## Key Concepts

### Agents
**Specialized experts** that handle specific concerns:
- Sprint Planning Agent (planning)
- Web Developer (development)
- Security Reviewer (quality)
- Documentation Engineer (documentation)

### Workflows
**Step-by-step processes** for complex tasks:
- Single Feature Development (implement feature)
- Sprint Planning (plan iterations)
- ML Model Development (train/evaluate models)

### Handoff Templates
**Structured communication** between agents:
- API Specification (API Specialist → Web Developer)
- Security Report (Security Reviewer → Developer)
- ML Evaluation Report (ML Engineer → Team)

### Quality Gates
**Mandatory checkpoints** before completion:
- Security review
- Test coverage
- Logging audit
- Documentation

### Orchestration
**Automatic agent selection** based on your request:
- Simple: Explicit keyword rules
- Balanced: Pattern matching (recommended)
- Tiered: Intelligent coordination

---

## Support

**Framework Documentation:**
- `.claude/README.md` - Agent framework guide
- `docs/ORCHESTRATION.md` - Orchestration deep dive
- `.claude/config/schema.yaml` - Config schema reference

**Example Configs:**
- `.claude/config/config-templates/web-app-config.yaml`
- `.claude/config/config-templates/api-config.yaml`
- `.claude/config/config-templates/ml-.claude/project-config.yaml`

**Workflows:**
- `.claude/workflows/` - All 15 workflows

**Handoff Templates:**
- `.claude/templates/handoffs/` - All 21 templates

---

**Ready to build with Vibey!** 🎉

Start with `/vibey` and let the framework guide you to production-ready code.
