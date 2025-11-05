# Frequently Asked Questions

Common questions about the Vibey Agent Framework.

---

## Table of Contents

- [General Questions](#general-questions)
- [Getting Started](#getting-started)
- [Sprint Planning](#sprint-planning)
- [Sprint Execution](#sprint-execution)
- [Agents & Workflows](#agents--workflows)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)

---

## General Questions

### What is Vibey?

Vibey is an agent orchestration framework that transforms AI coding assistants (like Claude) into specialized development teams. It provides:

- **12 specialized agents** for different tasks (planning, development, quality, documentation)
- **16 structured workflows** for common development processes
- **Sprint-driven orchestration** for systematic project execution
- **Quality gates** to ensure code quality
- **Configuration-driven** to support any tech stack

### What platforms does Vibey support?

**Currently:**
- ✅ **Claude Code** (Production ready - v1.2.0)

**Planned:**
- 🔄 **Goose** (In research - 75-85% compatible)
- 🔄 **Cursor** (In research - 50-65% compatible)

See `docs/ROADMAP.md` for multi-platform plans.

### Do I need to know programming to use Vibey?

No! Vibey uses natural language conversation. Just describe what you want to build, and Vibey guides you through:
- Planning your project
- Organizing work into sprints
- Executing tasks systematically
- Ensuring quality standards

### How is Vibey different from just using Claude?

**Without Vibey:**
- No structure - ad-hoc conversations
- No memory - restarts every session
- No quality enforcement
- No systematic workflow

**With Vibey:**
- Structured sprints and phases
- Persistent state tracking
- Quality gates prevent shipping incomplete work
- Systematic, repeatable processes
- Specialized agents for different tasks

---

## Getting Started

### How do I install Vibey?

**Quick Start:**
```bash
# In your project directory
/vibey

# Follow the prompts to:
# 1. Deploy framework
# 2. Plan first sprint
# 3. Start execution
```

See [QUICK_START.md](getting-started/QUICK_START.md) for detailed instructions.

### What are the prerequisites?

- Python 3.7 or later
- Claude Code (or supported AI platform)
- Git (recommended but optional)

Vibey will install dependencies (PyYAML, Jinja2) automatically.

### Can I use Vibey on an existing project?

Yes! Vibey works great with existing projects:

1. Run `/vibey` in your project directory
2. Choose "Discovery Mode" to analyze your codebase
3. Vibey will:
   - Detect your tech stack
   - Analyze code quality
   - Review git history
   - Generate project context
4. Use this context for sprint planning

### Will Vibey modify my existing code?

**During Installation:**
- Creates `.claude/` directory for framework files
- Creates `docs/sprints/` for sprint plans
- **Does not modify your source code**

**During Use:**
- Only makes changes you explicitly request
- Uses quality gates to prevent unwanted changes
- Commits are clearly marked and can be reviewed

---

## Sprint Planning

### What is a sprint?

A sprint is a focused period of development work (typically 1-4 weeks) with:
- Clear goals and deliverables
- Organized into phases
- Quality gates for each phase
- Systematic execution plan

Vibey uses sprints to organize work systematically.

### How do I plan my first sprint?

```bash
/vibey plan

# Or from main menu:
/vibey → Option 1: Sprint Planning
```

Vibey will ask about:
- What you want to build
- Timeline and priorities
- Technical requirements
- Quality standards

Then creates a detailed sprint plan in `docs/sprints/`.

### Do I need to audit my codebase first?

**For Existing Projects:** Recommended
- Provides context about current state
- Detects tech stack automatically
- Identifies quality baseline
- Skips 15-20 discovery questions

**For New Projects:** Optional
- Start directly with sprint planning
- Describe your vision
- Vibey helps you plan from scratch

### Can I modify a sprint plan after creation?

Yes! Sprint plans are Markdown files in `docs/sprints/`:
- `sprint-1-plan.md` - Edit as needed
- Sprint state file tracks progress
- Re-run planning to create new sprint

### How long should a sprint be?

**Recommended:**
- **1 week** - Small feature or bug fix
- **2 weeks** - Medium feature (default)
- **3-4 weeks** - Large feature or refactor

**Avoid:**
- Less than 1 week - Too rushed
- More than 4 weeks - Loses focus

---

## Sprint Execution

### How do I start a sprint?

```bash
/vibey code

# Then:
# Option A: Start existing sprint plan
# Choose your sprint from the list
```

Vibey will:
- Load sprint plan
- Show current phase
- Track progress
- Enforce quality gates

### What happens during sprint execution?

Vibey provides:
1. **Phase-by-phase guidance** - Follow structured process
2. **Agent orchestration** - Right agents at right time
3. **Progress tracking** - Updates sprint state file
4. **Quality enforcement** - Gates must pass to proceed
5. **Continuous commits** - Git commits after each phase

### Can I pause a sprint?

Yes!
```
/vibey code → Option 7: Pause sprint
```

Progress is saved to sprint state file. Resume anytime:
```
/vibey code → Start sprint [number]
```

### What if a quality gate fails?

**Options:**
1. **Fix the issue** - Recommended approach
2. **Adjust threshold** - If gate is too strict
3. **Override** - Document why (not recommended)

Quality gates prevent shipping incomplete/insecure code.

### How do I complete a sprint?

```
/vibey code → Option 8: Complete sprint
```

Vibey will:
- Verify all phases complete
- Check quality gates
- Generate retrospective template
- Update ROADMAP.md
- Deactivate sprint

---

## Agents & Workflows

### What agents are available?

**Planning:**
- Sprint Planning - Plan sprints and roadmaps
- Researcher - Research technologies and APIs

**Development:**
- Web Developer - Frontend and backend development
- ML Engineer - ML model development

**Quality:**
- Security Reviewer - Security audits
- Observability Engineer - Logging and monitoring
- Performance Engineer - Performance optimization

**Documentation:**
- Documentation Engineer - Technical documentation
- Diagram Engineer - Architecture diagrams
- Git Committer - Git operations

**Core:**
- Coordinator - Intelligent task routing
- Vibey Manager - Framework management

See [reference/README.md](reference/README.md) for complete list.

### How do I use a specific agent?

**Automatic (Recommended):**
- Vibey selects agents based on task
- Uses trigger patterns and context
- No manual selection needed

**Manual:**
```
"Use the [Agent Name] agent to [task]"

Example:
"Use the Security Reviewer agent to audit authentication"
```

### What workflows are available?

**16 structured workflows** including:
- Sprint Planning
- Single Feature Development
- ML Model Development
- Frontend Feature Development
- Security Audit
- Performance Optimization
- Infrastructure Setup
- And more...

See [guides/WORKFLOW_SELECTION_GUIDE.md](guides/WORKFLOW_SELECTION_GUIDE.md).

### How do workflows differ from agents?

- **Agents** - Specialized roles (who does the work)
- **Workflows** - Structured processes (how work gets done)

Example:
- **Workflow:** "Single Feature Development" (5-phase process)
- **Agents:** Web Developer → Security Reviewer → Documentation Engineer

---

## Configuration

### Where is the configuration file?

`.claude/project-config.yaml`

Generated during first sprint planning.

### Can I modify the configuration?

Yes! Two ways:

**1. Framework Management UI:**
```
/vibey manage
Choose what to modify
Vibey updates config and regenerates CLAUDE.md
```

**2. Manual Edit:**
```bash
# Edit directly
nano .claude/project-config.yaml

# Validate
python3 .claude/scripts/validate-config.py .claude/project-config.yaml

# Regenerate CLAUDE.md
python3 .claude/scripts/render-template.py \
  -c .claude/project-config.yaml \
  -t .claude/templates/CLAUDE.md.template \
  -o .claude/CLAUDE.md
```

### What orchestration mode should I use?

**Simple Mode:**
- Keyword-based agent selection
- Transparent and predictable
- Best for learning Vibey

**Balanced Mode (Recommended):**
- Pattern-based agent selection
- Smart defaults
- Best for most projects

**Tiered Mode:**
- Coordinator agent routes complex tasks
- Intelligent decomposition
- Best for large, complex projects

Change in config:
```yaml
framework:
  orchestration_mode: "balanced"  # or "simple" or "tiered"
```

### How do I change quality gate thresholds?

```
/vibey manage → Option 1: Update quality gate thresholds
```

Or edit config:
```yaml
quality_gates:
  unit_testing:
    coverage_minimum: 90  # Percentage
  security:
    score_minimum: 85     # Out of 100
  logging:
    score_minimum: 80     # Out of 100
```

---

## Troubleshooting

### Framework not deploying

**Check:**
```bash
# Python installed?
python3 --version

# Dependencies installed?
python3 -c "import yaml, jinja2"

# Framework source exists?
ls framework/agents framework/workflows
```

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for solutions.

### Scripts not executable

```bash
chmod +x .claude/scripts/*.py
```

### Configuration invalid

```bash
python3 .claude/scripts/validate-config.py .claude/project-config.yaml
```

### Health check failing

```
/vibey manage → Option 5: Framework health check
```

Shows exactly what's wrong and how to fix it.

---

## Advanced Usage

### Can I create custom agents?

Yes! Follow the agent template pattern:

1. Create file in `.claude/agents/[category]/your-agent.md`
2. Follow structure of existing agents
3. Use `{{ config.* }}` for tech-specific references
4. Add trigger patterns for automatic selection

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for details.

### Can I create custom workflows?

Yes! Follow workflow template pattern:

1. Create file in `.claude/workflows/[category]/your-workflow.md`
2. Define phases with agent recommendations
3. Specify prerequisites and success criteria
4. Add to workflow selection guide

### How do I backup my framework?

**Automatic Backups:**
- Created during re-deployment
- Stored as `.claude-backup-YYYYMMDD-HHMMSS/`

**Manual Backup:**
```bash
cp -r .claude .claude-backup-$(date +%Y%m%d-%H%M%S)
```

**Restore:**
```bash
python3 .claude/scripts/rollback-framework.py --list
python3 .claude/scripts/rollback-framework.py --auto
```

### Can I use Vibey with a team?

Yes! Vibey is git-friendly:

**Commit to Git:**
```bash
git add .claude/
git add docs/sprints/
git commit -m "Add Vibey framework and Sprint 1 plan"
git push
```

**Team members get:**
- Same framework configuration
- Sprint plans and state
- Shared quality standards
- Consistent workflow

### How do I upgrade Vibey?

**Check Version:**
```bash
python3 .claude/scripts/check-version.py
```

**Upgrade:**
```bash
# 1. Pull latest framework code
cd /path/to/vibey
git pull

# 2. Re-deploy to project
cd /path/to/your/project
cp -r /path/to/vibey/framework/* .claude/

# 3. Backup created automatically
```

---

## Best Practices

### Sprint Planning

- ✅ Run codebase audit for existing projects
- ✅ Use PROJECT-CONTEXT from discovery mode
- ✅ Set realistic timelines
- ✅ Define clear success criteria
- ❌ Don't pack too much into one sprint

### Sprint Execution

- ✅ Follow phase order
- ✅ Complete quality gates before moving on
- ✅ Commit after each phase
- ✅ Update sprint state regularly
- ❌ Don't skip quality gates

### Quality Gates

- ✅ Start with achievable thresholds
- ✅ Gradually increase standards
- ✅ Adjust based on project phase
- ❌ Don't set unrealistic goals initially

### Documentation

- ✅ Keep sprint plans updated
- ✅ Document decisions in retrospectives
- ✅ Archive old contexts
- ❌ Don't let docs get stale

---

## Questions Not Answered Here?

1. **Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions
2. **Check [Getting Started Guide](getting-started/)** - Detailed setup instructions
3. **Check [Guides](guides/)** - In-depth usage guides
4. **Ask Claude** - Describe your question in natural language
5. **Open GitHub Issue** - Report bugs or request features

---

**Last Updated:** 2024-11-05
**Framework Version:** 1.2.0
