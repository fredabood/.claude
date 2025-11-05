# Vibey Agent Framework

**Version:** 1.1
**Status:** Production Ready

An intelligent agent orchestration framework for Claude Code that provides specialized agents, structured workflows, quality gates, and automatic agent selection for building production-quality software.

---

## Quick Start (3 Steps)

### 1. Navigate to Your Project

```bash
cd /path/to/your-project
```

### 2. Clone Framework

```bash
git clone https://github.com/fredabood/vibey.git .vibey
```

### 3. Start Claude Code and Initialize

```bash
claude
```

Then type in Claude Code:
```
/vibey
```

**That's it!** Claude will:
- Deploy the framework to `.claude/` (or merge with existing)
- Handle any file conflicts automatically
- Guide you through 5-10 minute conversational setup
- Clean up `.vibey/` directory when done

---

## What Is Vibey?

Vibey is an agent orchestration framework that transforms Claude Code into a specialized development team with:

### 🤖 12 Specialized Agents
- **Planning:** Sprint Planning Agent, Researcher
- **Development:** Web Developer, ML Engineer
- **Quality:** Security Reviewer, Observability Engineer, Performance Engineer
- **Documentation:** Documentation Engineer, Diagram Engineer, Git Committer
- **Core:** Coordinator Agent (intelligent routing), Vibey Manager

### 📋 16 Structured Workflows
- Sprint Planning & Roadmap Management
- Codebase Audit & Discovery
- Single Feature Development
- ML Model Development
- Infrastructure Setup
- Performance Optimization
- Security Audit
- And 9 more...

### 📝 22 Handoff Templates
- API Specifications
- Security Reports
- Codebase Audit Reports
- Research Summaries
- Architecture Decision Records
- ML Evaluation Reports
- And 16 more...

### 🎯 Automatic Quality Gates
- Security Review (≥85/100)
- Test Coverage (≥90%)
- Logging Audit (≥80/100)
- Documentation Completeness

### 🔀 3 Orchestration Modes
1. **Simple** - Explicit keyword-based rules (best for learning)
2. **Balanced** - Pattern matching (⭐ recommended for most projects)
3. **Tiered** - Intelligent coordination (best for complex projects)

---

## What You Get

After running `/vibey`:

```
your-project/
├── .claude/                          # All Vibey framework files
│   ├── agents/                       # 12 specialized agents
│   ├── workflows/                    # 16 structured workflows
│   ├── templates/                    # 22 handoff templates
│   ├── commands/                     # /vibey command
│   ├── config/                       # Schema and examples
│   ├── scripts/                      # Validation and rendering
│   ├── docs/                         # User-facing documentation
│   ├── project-config.yaml           # Your project configuration
│   └── CLAUDE.md                     # Project context for Claude
├── docs/                             # Your project documentation
│   ├── sprints/
│   │   └── sprint-001-plan.md        # First sprint plan
│   ├── security/                     # Security reports
│   ├── architecture/                 # Architecture docs
│   └── reference/                    # Reference documentation
└── [your code]
```

---

## Installation

### Prerequisites

- **Claude Code** - Latest version
- **Python 3.7+** - For config validation and template rendering
- **PyYAML & Jinja2** - Python dependencies

```bash
pip install pyyaml jinja2
```

### Install Framework

```bash
# Navigate to your project
cd /path/to/your-project

# Clone framework
git clone https://github.com/fredabood/vibey.git .vibey

# Start Claude Code
claude
```

### Use the `/vibey` Command

In Claude Code, type:
```
/vibey
```

**This command has two modes:**

#### First Time (Framework Initialization)

If running for the first time, Claude will:

**Phase 1: Deployment**
1. ✅ Detect if `.claude/` already exists
2. ✅ Deploy framework to `.claude/` (or merge with existing)
3. ✅ Preserve any custom agents/prompts if merging
4. ✅ Clean up `.vibey/` directory

**Phase 2: Pre-Checks**
5. ✅ Check if git repo exists (offers to initialize if not)
6. ✅ Verify Python dependencies installed
7. ✅ Check for existing configuration
8. ✅ Offer optional codebase/git history analysis

**Phase 3: Initialization**
9. ✅ Start conversational project discovery
10. ✅ Generate `project-config.yaml`
11. ✅ Generate `CLAUDE.md`
12. ✅ Create docs structure
13. ✅ Plan first sprint

**Duration:** 5-10 minutes (+ optional analysis time)
**Result:** Framework deployed, configured, and ready to use!

#### After Initialization (Framework Management)

If framework is already initialized, Claude will launch the **Vibey Manager Agent** to help you:

- 🔧 **Change orchestration mode** (Simple → Balanced → Tiered)
- 📊 **Adjust quality gates** (update thresholds)
- 🤖 **View/modify agents** (add custom agents)
- 💻 **Update tech stack** (reflect technology changes)
- 📝 **Regenerate CLAUDE.md** (refresh framework instructions)
- ✅ **Framework health check** (diagnose issues)
- 🔄 **Sprint retrospective** (review and adjust)
- ⚙️ **Advanced configuration** (fine-tune settings)

**Duration:** 2-5 minutes per task
**Result:** Optimized framework configuration!

---

## Usage

### After Initialization

Once initialized, just tell Claude what you want to build:

```
"I want to implement user authentication with JWT tokens"
```

Claude automatically:
1. Detects this is a security-critical feature
2. Launches appropriate agents:
   - API Specialist (implement endpoints)
   - Security Reviewer (audit implementation)
   - Test Engineer (write tests)
   - Documentation Engineer (document system)
3. Follows single-feature-development workflow
4. Runs quality gates before completion

**You don't specify agents or workflows** - Claude figures it out based on:
- Your orchestration mode (Simple/Balanced/Tiered)
- Agent trigger patterns
- Project type
- Sprint phase

### Orchestration Modes

**Simple Mode - Explicit Rules:**
```
You: "I need a security review"
Claude: [Matches "security" → Launches Security Reviewer]
```

**Balanced Mode ⭐ (Recommended):**
```
You: "Implement JWT authentication"
Claude: [Pattern matches:
  - "authentication" → Security Reviewer (high priority)
  - "JWT", "implement" → API Specialist (medium priority)
  - Implied: Test Engineer (development phase)
  → Launches all three agents]
```

**Tiered Mode - Intelligent Coordination:**
```
You: "Implement auth with OAuth, JWT, 2FA, email verification, and password reset"
Claude: [Detects complexity → Launches Coordinator Agent
  → Coordinator analyzes, sequences 8 agents, manages handoffs, verifies quality gates]
```

### Common Tasks

**Plan Sprint:**
```
"Let's plan sprint 2"
```

**Build Feature:**
```
"Build the user profile page"
```

**Security Review:**
```
"Run a security review on the auth code"
```

**Performance Optimization:**
```
"The dashboard is loading slowly"
```

**Update Documentation:**
```
"Update the README with the new auth features"
```

---

## Quality Gates

Every sprint enforces quality gates before completion:

### Security Review (≥85/100)
- OWASP Top 10 compliance
- Authentication/authorization
- Input validation
- Secrets management

### Test Coverage (≥90%)
- Unit tests
- Integration tests
- Edge cases
- Error paths

### Logging Audit (≥80/100)
- Correlation IDs present
- Error context sufficient
- Log levels appropriate
- Performance metrics tracked

### Documentation Review
- README.md current
- CLAUDE.md updated
- API documentation complete
- Code comments present

**If any gate fails, Claude will:**
- Report what failed
- Fix the issues
- Re-run the gate
- Only proceed when ALL gates pass

---

## Configuration

### project-config.yaml

Generated by `/vibey`, stored in project root:

```yaml
project:
  name: "MyProject"
  type: "web-app"  # or api, ml, data-platform, infrastructure
  description: "Project description"

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

### CLAUDE.md

Generated by `/vibey`, provides project context to Claude:
- Technology stack details
- Architecture overview
- Coding standards
- Critical rules
- Quality gate requirements
- Orchestration instructions (mode-specific)
- Available agents and workflows

Claude reads this file at the start of every session.

---

## Changing Orchestration Mode

### Option 1: Ask Claude

```
"I'd like to switch to tiered orchestration mode"
```

Claude will update config and regenerate CLAUDE.md.

### Option 2: Manual Edit

Edit `project-config.yaml`:
```yaml
framework:
  orchestration_mode: "tiered"  # Change from "balanced"
```

Then tell Claude:
```
"Regenerate CLAUDE.md with the new orchestration mode"
```

---

## Deployed Framework Structure

After running `/vibey`, this is deployed to `.claude/`:

```
.claude/                              # Deployed framework (from .vibey/framework/)
├── agents/                           # 12 specialized agents
│   ├── core/
│   │   ├── coordinator.md            # Intelligent router (650 lines)
│   │   └── vibey-manager.md          # Framework manager (500 lines)
│   ├── planning/
│   │   ├── sprint-planning.md        # Sprint planning agent
│   │   └── researcher.md             # Research agent
│   ├── development/
│   │   ├── web-developer.md          # Web development agent
│   │   └── ml-engineer.md            # ML engineering agent
│   ├── quality/
│   │   ├── security-reviewer.md      # Security audit agent
│   │   ├── observability-engineer.md # Logging/monitoring agent
│   │   └── performance-engineer.md   # Performance optimization
│   ├── documentation/
│   │   ├── documentation-engineer.md # Documentation agent
│   │   ├── diagram-engineer.md       # Diagram generation
│   │   └── git-committer.md          # Git operations
│   └── architecture/
│       └── architecture-specialist.md # Architecture review
├── workflows/                        # 16 structured workflows
│   ├── planning/
│   │   ├── sprint-planning.md        # Sprint planning process
│   │   └── codebase-audit-discovery.md # Automated project analysis
│   ├── single-feature-development.md # Feature development
│   ├── ml-model-development.md       # ML model lifecycle
│   ├── infrastructure-setup.md       # IaC deployment
│   ├── performance-optimization.md   # Performance tuning
│   └── [10 more workflows...]
├── templates/                        # 22 handoff templates
│   ├── CLAUDE.md.template            # Project context template
│   └── handoffs/
│       ├── api-specification-template.md
│       ├── security-report-template.md
│       ├── codebase-audit-report-template.md
│       └── [19 more templates...]
├── commands/
│   └── vibey.md                      # /vibey slash command
├── config/
│   ├── schema.yaml                   # Config schema (400+ lines)
│   └── config-templates/
│       ├── web-app-config.yaml       # Web app example
│       ├── api-config.yaml           # API example
│       └── ml-project-config.yaml    # ML example
├── scripts/
│   ├── validate-config.py            # Config validator
│   └── render-template.py            # Jinja2 renderer
└── docs/                             # User-facing documentation
    ├── README.md                     # Documentation index
    ├── getting-started/              # Installation & setup guides
    │   ├── QUICK_START.md            # Quick start (10 minutes)
    │   └── USER_JOURNEY.md           # Detailed scenarios
    ├── guides/                       # In-depth guides
    │   ├── ORCHESTRATION.md          # Orchestration modes
    │   └── WORKFLOW_SELECTION_GUIDE.md # Workflow selection
    └── reference/                    # Component reference
        └── README.md                 # Reference index
```

## Repository Structure

The vibey repository contains both deployable and development files:

```
vibey/                                # Repository root
├── framework/                        # DEPLOYABLE (becomes .claude/)
│   ├── agents/                       # All agents (deployed)
│   ├── workflows/                    # All workflows (deployed)
│   ├── templates/                    # All templates (deployed)
│   ├── commands/                     # /vibey command (deployed)
│   ├── config/                       # Schema and examples (deployed)
│   ├── scripts/                      # Validation tools (deployed)
│   └── docs/                         # User documentation (deployed)
├── docs/                             # Repository documentation (NOT deployed)
│   ├── ROADMAP.md                    # Multi-platform strategy
│   ├── SESSION_HANDOFF.md            # Session context
│   ├── DEVELOPMENT_HISTORY.md        # Development history
│   └── README.md                     # Development guide
├── CLAUDE.md                         # Repository context (NOT deployed)
├── README.md                         # This file (NOT deployed)
├── LICENSE                           # Framework license (NOT deployed)
└── .gitignore
```

---

## Supported Project Types

- ✅ **Web Applications** - Frontend + Backend (React, Vue, Angular, FastAPI, Express, etc.)
- ✅ **API Services** - Backend only (REST, GraphQL, gRPC)
- ✅ **ML Projects** - Model training, experimentation, deployment (MLflow, W&B, TensorBoard)
- ✅ **Data Platforms** - ETL, analytics, data pipelines (Airflow, dbt, Spark)
- ✅ **Infrastructure** - IaC, cloud deployments (Terraform, Pulumi, CloudFormation)

## Supported Technologies

### Languages
- Python, TypeScript, JavaScript, Java, Go, Rust

### Frontend Frameworks
- React, Vue, Angular, Svelte, Next.js, Nuxt

### Backend Frameworks
- FastAPI, Flask, Express, NestJS, Spring Boot, Django

### Databases
- PostgreSQL, MySQL, MongoDB, Redis, DynamoDB

### ML Platforms
- MLflow, Weights & Biases, TensorBoard, Databricks

### Cloud Providers
- AWS, Azure, GCP

### IaC Tools
- Terraform, Pulumi, CloudFormation, CDK

---

## Documentation

### Framework Documentation
- **README.md** - This file (installation and overview)
- **QUICK_START.md** - Quick start guide (675 lines)
- **USER_JOURNEY.md** - User adoption scenarios (1,800+ lines)
- **docs/ORCHESTRATION.md** - Orchestration deep dive (500+ lines)

### Configuration
- **config/schema.yaml** - Config schema reference (400+ lines)
- **config/config-templates/** - Example configs for each project type

### Agents
- **agents/** - 11 agent instructions (5,000+ lines total)

### Workflows
- **workflows/** - 15 workflow guides (10,000+ lines total)

### Templates
- **templates/handoffs/** - 21 handoff templates (8,000+ lines total)

---

## Troubleshooting

### "PyYAML not found" or "Jinja2 not found"

```bash
pip install pyyaml jinja2
```

### "Claude isn't using agents"

**Check:**
1. `CLAUDE.md` is current (regenerate if needed)
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

### "Git commands don't work"

Framework requires git for commit operations. Initialize if needed:
```bash
git init
```

---

## Contributing

Contributions welcome! Areas for improvement:

- Additional agents (DevOps, QA, etc.)
- More workflows (incident response, release management)
- Language-specific templates
- Framework translations
- Example projects

---

## License

MIT License - see LICENSE file

---

## Framework Statistics

**Total Lines:** ~50,600+ across 68 components

**Components:**
- 12 specialized agents (including Vibey Manager)
- 16 structured workflows (including Codebase Audit)
- 22 handoff templates (including Audit Report)
- 3 orchestration modes
- 1 coordinator agent
- 5 deployment tools
- Complete documentation

**Supported:**
- 5 project types
- 6+ programming languages
- 20+ frameworks/platforms
- 3 cloud providers
- Universal tech stack support

---

## Documentation

**📚 [Complete Documentation →](docs/)**

**Quick Links:**
- **[Quick Start Guide](docs/getting-started/QUICK_START.md)** - Get up and running in 10 minutes
- **[User Journey](docs/getting-started/USER_JOURNEY.md)** - Detailed installation scenarios
- **[Orchestration Guide](docs/guides/ORCHESTRATION.md)** - Understanding orchestration modes
- **[Workflow Selection](docs/guides/WORKFLOW_SELECTION_GUIDE.md)** - Choosing the right workflow

**Reference:**
- [All Documentation](docs/) - Complete documentation index
- [Agents](agents/) - 11 specialized agents
- [Workflows](workflows/) - 15 structured workflows
- [Templates](templates/) - 21 handoff templates
- [Config Schema](config/schema.yaml) - Configuration reference

---

## Support & Community

**Issues:**
- Report bugs or request features on GitHub Issues

**Questions:**
- Ask Claude! The framework is self-documenting

---

**Ready to build production-quality software with Vibey!** 🚀

Install in 3 steps:
```bash
cd your-project
git clone https://github.com/fredabood/vibey.git .vibey
claude  # then type: /vibey
```
