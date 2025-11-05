# Getting Started with Vibey

New to Vibey? Start here to get the framework installed and configured.

---

## Installation

**Universal installation command (works for all scenarios):**

```bash
cd your-project
git clone https://github.com/fredabood/vibey.git .vibey
claude
# Type: /vibey
```

Claude automatically handles deployment, configuration, and setup.

---

## Documentation

### [Quick Start Guide](QUICK_START.md)
**Time:** 10 minutes
**Best for:** Getting up and running quickly

Learn how to:
- Install the framework (1 minute)
- Initialize with `/vibey` (5-10 minutes)
- Understand what Claude does automatically
- Start building your first feature

**Start here if:** You want to get going fast

---

### [User Journey](USER_JOURNEY.md)
**Time:** 30-60 minutes read
**Best for:** Understanding detailed scenarios

Complete walkthroughs of three scenarios:
1. **New repository** (greenfield project)
2. **Existing repo without `.claude/`** (fresh installation)
3. **Existing repo with `.claude/`** (merge/migration)

Includes:
- Step-by-step commands
- Complete conversation examples
- Generated configuration files
- Before/after directory structures
- Sprint plan examples

**Start here if:** You want to see concrete examples before installing

---

## What Happens When You Run `/vibey`

**Phase 1: Deployment (1-2 minutes)**
- Claude detects your situation (new vs existing `.claude/`)
- Deploys framework from `.vibey/` to `.claude/`
- Merges with existing setup if needed (preserves your custom content)
- Cleans up `.vibey/` directory

**Phase 2: Pre-Checks (<1 minute)**
- Checks if git repository exists (offers to initialize)
- Verifies Python dependencies (pyyaml, jinja2)
- Checks for existing configuration

**Phase 3: Initialization (5-10 minutes)**
- Conversational project discovery
- Select orchestration mode (Simple/Balanced/Tiered)
- Generate `project-config.yaml`
- Generate `CLAUDE.md`
- Create documentation structure
- Plan your first sprint

---

## After Installation

Once initialized, the framework is ready to use:

- **Tell Claude what to build:** "I want to implement user authentication"
- **Claude automatically:** Selects agents, follows workflows, runs quality gates
- **You get:** Production-ready code with high quality standards

---

## Next Steps

After getting started:

1. **Read the [Orchestration Guide](../guides/ORCHESTRATION.md)** - Understand the three orchestration modes
2. **Review your sprint plan** - `docs/sprints/sprint-001-plan.md`
3. **Start building** - Pick a task and tell Claude what you want

---

**[← Back to Documentation Index](../README.md)**
