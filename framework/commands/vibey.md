# Vibey Framework Command

**Purpose:** Initialize OR manage the Vibey Agent Framework for this project

---

## Phase 0: Detect Framework State

**IMPORTANT:** This command has two different behaviors depending on whether the framework is already initialized.

### Detection Check

```bash
# Check if framework is already initialized
if [ -f "project-config.yaml" ] && [ -f "CLAUDE.md" ]; then
  echo "✓ Framework already initialized"
  FRAMEWORK_STATE="initialized"
else
  echo "✗ Framework not initialized"
  FRAMEWORK_STATE="new"
fi
```

### Route Based on State

**If FRAMEWORK_STATE="initialized":**
- **Action:** Launch **Vibey Framework Manager Agent**
- **Purpose:** Help user configure and manage their agentic experience
- **Agent File:** `.claude/agents/core/vibey-manager.md`
- **Skip to:** [Framework Management Mode](#framework-management-mode)

**If FRAMEWORK_STATE="new":**
- **Action:** Run **Framework Initialization Flow**
- **Purpose:** Deploy and configure framework for the first time
- **Continue with:** Phase 1 (Deployment) → Phase 2 (Pre-checks) → Phase 3 (Initialization)

---

## Framework Management Mode

**Triggered when:** Framework already initialized (project-config.yaml and CLAUDE.md exist)

**Launch Vibey Manager Agent:**

Read and follow instructions from `.claude/agents/core/vibey-manager.md`

**Initial Greeting:**
```
Hello! I'm your Vibey Framework Manager. I see you already have Vibey initialized.

**Current Configuration:**
- Orchestration Mode: {{ current_mode }}
- Quality Gates: {{ gates_enabled }}
- Active Agents: {{ agent_count }}

What would you like to do?

1. **Change orchestration mode** - Switch between Simple/Balanced/Tiered
2. **Adjust quality gates** - Update thresholds or requirements
3. **View/modify agents** - See available agents or add custom ones
4. **Update tech stack** - Reflect technology changes in config
5. **Regenerate CLAUDE.md** - Refresh framework instructions
6. **Framework health check** - Diagnose any issues
7. **Sprint retrospective** - Review and adjust based on learnings
8. **Advanced configuration** - Fine-tune framework settings

Or tell me what you'd like to change, and I'll guide you!
```

**Capabilities:**
- View current configuration
- Change orchestration mode (Simple/Balanced/Tiered)
- Adjust quality gates
- Add/modify custom agents
- Update technology stack
- Regenerate CLAUDE.md
- Run framework health checks
- Sprint retrospective support
- Advanced configuration tuning

**Exit Condition:** User is satisfied with configuration changes

**Important:** All changes to project-config.yaml should be followed by regenerating CLAUDE.md

---

## Framework Initialization Mode

**Triggered when:** Framework not initialized (first time running `/vibey`)

### Overview

This command performs a three-phase process:
1. **Deployment Phase:** Deploy framework from `.vibey/framework/` to `.claude/` (or merge with existing)
2. **Pre-check Phase:** Validate prerequisites and detect existing project
3. **Initialization Phase:** Configure framework for this specific project

---

## Phase 1: Framework Deployment

### Step 1: Detect Installation Location

Check where the framework is currently located:

```bash
# Check if running from .vibey directory
pwd | grep -q "\.vibey" && echo "Running from .vibey" || echo "Running from .claude"

# Check if .claude directory already exists in parent
ls -d ../.claude 2>/dev/null && echo ".claude exists" || echo ".claude does not exist"
```

### Step 2A: If .claude Does NOT Exist (New Installation)

**Action:** Deploy framework to `.claude/` directory

```bash
# Copy framework contents from .vibey/framework/ to .claude/
cp -r .vibey/framework/* .claude/

# Verify deployment
ls -d .claude/agents .claude/workflows .claude/templates .claude/commands .claude/scripts
```

**Result:** Framework deployed to `.claude/` directory

### Step 2B: If .claude DOES Exist (Merge/Migration)

**Action:** Guide user through consolidation

**Inform user:**
"I detected an existing `.claude/` directory in your project. I'll help you merge the Vibey framework with your existing setup."

**Ask user:**
"How would you like to proceed?"
1. **Backup and merge** - Backup existing `.claude/` to `.claude-backup-{date}`, then merge Vibey framework
2. **Selective merge** - Keep your custom content, add only Vibey components
3. **Cancel** - Exit without changes

**If user chooses "Backup and merge":**
```bash
# Backup existing .claude
cp -r .claude .claude-backup-$(date +%Y%m%d-%H%M%S)

# Check for custom files that should be preserved
ls .claude/prompts/ 2>/dev/null && echo "Found custom prompts"
ls .claude/custom-agents/ 2>/dev/null && echo "Found custom agents"

# Merge Vibey framework into existing .claude
cp -r .vibey/framework/agents .claude/
cp -r .vibey/framework/workflows .claude/
cp -r .vibey/framework/templates .claude/
cp -r .vibey/framework/config .claude/
cp -r .vibey/framework/commands .claude/
cp -r .vibey/framework/scripts .claude/
cp -r .vibey/framework/docs .claude/

# If custom prompts exist, preserve them
if [ -d .claude-backup-*/prompts ]; then
  mkdir -p .claude/prompts-custom
  cp -r .claude-backup-*/prompts/* .claude/prompts-custom/
  echo "✓ Custom prompts preserved in .claude/prompts-custom/"
fi

# If custom agents exist, preserve them
if [ -d .claude-backup-*/custom-agents ]; then
  mkdir -p .claude/agents/custom
  cp -r .claude-backup-*/custom-agents/* .claude/agents/custom/
  echo "✓ Custom agents preserved in .claude/agents/custom/"
fi

echo "✓ Backup created: .claude-backup-{date}"
echo "✓ Vibey framework merged into .claude/"
```

**If user chooses "Selective merge":**
```bash
# Check what's in existing .claude
ls -la .claude/

# Ask user what to preserve
echo "I found the following in your .claude/ directory:"
ls .claude/ | sed 's/^/  - /'
echo ""
echo "I'll add Vibey components without overwriting your files."

# Copy Vibey components that don't exist
[ ! -d .claude/agents ] && cp -r .vibey/framework/agents .claude/
[ ! -d .claude/workflows ] && cp -r .vibey/framework/workflows .claude/
[ ! -d .claude/templates ] && cp -r .vibey/framework/templates .claude/
[ ! -d .claude/config ] && cp -r .vibey/framework/config .claude/
[ ! -d .claude/commands ] && cp -r .vibey/framework/commands .claude/
[ ! -d .claude/scripts ] && cp -r .vibey/framework/scripts .claude/

echo "✓ Vibey framework components added to .claude/"
echo "✓ Your existing files preserved"
```

### Step 3: Validate Framework Deployment

```bash
# Verify critical directories exist in .claude
ls -d .claude/agents .claude/workflows .claude/templates .claude/commands .claude/scripts 2>/dev/null | wc -l
```

**Expected:** 5 directories

**If deployment incomplete:**
- Error: "⚠️ Framework deployment incomplete. Expected 5 directories, found X."
- Suggest: "Let me retry the deployment."
- Retry deployment or exit

### Step 4: Clean Up .vibey Directory

After successful deployment:

```bash
# Remove .vibey directory (contains framework repo metadata, not needed)
rm -rf .vibey

echo "✓ Framework deployed to .claude/"
echo "✓ Cleaned up temporary .vibey/ directory"
```

**Why remove .vibey?**
- Contains framework repository files (README.md, CLAUDE.md, dev docs)
- Contains .git history from framework repo
- Contains meta files not relevant to user's project (SESSION_HANDOFF.md, roadmap.md)
- Clean separation between framework repo and deployed framework
- Only `framework/` subdirectory is needed for user projects

---

## Phase 2: Pre-Initialization Checks

After deployment, perform these checks before initialization:

### Check 1: Git Repository Status

```bash
git rev-parse --is-inside-work-tree 2>/dev/null
```

**If NO git repository exists:**
- Ask user: "I notice this project isn't a git repository yet. Would you like me to initialize one? (Recommended for version control)"
- If yes: `git init`
- If no: Warn about missing git features, confirm to proceed

### Check 2: Python Dependencies

```bash
python3 -c "import yaml; import jinja2" 2>/dev/null && echo "✓ Dependencies installed" || echo "✗ Missing dependencies"
```

**If dependencies missing:**
- Inform: "Framework requires PyYAML and Jinja2"
- Provide: `pip install pyyaml jinja2`
- Wait for install, verify again

### Check 3: Existing Configuration

```bash
# Check for existing project-config.yaml or CLAUDE.md
ls project-config.yaml 2>/dev/null || ls CLAUDE.md 2>/dev/null
```

**If configuration exists:**
- Inform: "✓ Found existing framework configuration"
- Ask: "Reconfigure (start over) / Update (modify existing) / Skip (already set up)?"
- Handle user choice

### Check 4: Existing Project Analysis Options

```bash
# Check if codebase exists (source files present)
find . -maxdepth 3 -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.java" -o -name "*.go" -o -name "*.rs" \) 2>/dev/null | head -1

# Check if git repository exists
git rev-parse --is-inside-work-tree 2>/dev/null
```

**If codebase exists OR git repository exists:**

Inform user: "I detected an existing project. Before we plan the first sprint, I can analyze the project to reduce your discovery burden and improve sprint planning quality. This is optional but recommended."

**Offer two independent analysis options:**

"I can run two types of analysis (both optional, choose any combination):

1. **Codebase Audit** (60-105 min)
   - Analyzes code structure, tech stack, security, testing, logging
   - Generates comprehensive health report with scores
   - Pre-fills configuration with detected values
   - Identifies gaps and improvement opportunities
   - **Benefit:** Skip 20+ basic questions, focus on strategy

2. **Git History Analysis** (10-20 min)
   - Analyzes last 6 months of commits and releases
   - Detects sprint cadence and recent work patterns
   - Calculates development velocity and team activity
   - Identifies recent technology migrations
   - **Benefit:** Understand what was built recently, plan next sprint with context

Would you like me to run:
- Both analyses? (70-125 min total, maximum context)
- Codebase audit only? (60-105 min)
- Git history only? (10-20 min)
- Neither? (0 min, I'll ask questions during sprint planning)"

**Based on user selection:**

**Option 1: Both analyses**
- Run **Codebase Audit Workflow** (`.claude/workflows/planning/codebase-audit-discovery.md`) - Steps 1-8, 10-11
- Run **Git History Analysis** (Step 9 from audit workflow)
- Generate comprehensive audit report with both sections (`docs/codebase-audit-report.md`)
- Pre-fill `project-config.yaml` with detected values, velocity baselines, and sprint cadence
- Proceed to Phase 3 with maximum context

**Option 2: Codebase audit only**
- Run **Codebase Audit Workflow** (Steps 1-8, 10-11) - skip git history
- Generate audit report without git history section
- Pre-fill `project-config.yaml` with detected values (no velocity data)
- Proceed to Phase 3 with code context

**Option 3: Git history only**
- Skip codebase audit
- Run **Git History Analysis** only (Step 9)
- Generate lightweight report with git history insights
- Pre-fill sprint cadence and velocity in `project-config.yaml`
- Proceed to Phase 3 with historical context (still ask tech stack questions)

**Option 4: Neither**
- Skip all analysis
- Proceed to Phase 3 with standard discovery questions
- User provides all information manually
- Fastest to start sprint planning, but more questions to answer

**If no codebase AND no git repository exists (greenfield project):**
- Skip all analysis options
- Proceed directly to Phase 3
- Standard initialization flow

---

## Phase 3: Framework Initialization

After deployment, pre-checks, and optional audit, follow the **Framework Initialization Workflow** at `.claude/workflows/framework-initialization.md` to:

1. **Discover the project** through conversational questions
2. **Select orchestration mode** (Simple / Balanced / Tiered)
3. **Generate project configuration** (`project-config.yaml`)
4. **Generate CLAUDE.md** (project context for Claude)
5. **Set up directory structure** (`docs/`, `docs/sprints/`, etc.)
6. **Plan the first sprint** with detailed tasks and agent recommendations

## Important Guidelines

- This is a **conversational process** - ask questions naturally
- Be thorough understanding the project's technology stack and goals
- Ensure user understands orchestration mode options before choosing
- Generate all configuration and documentation files in the **project root**
- Make first sprint planning comprehensive and actionable
- Set quality gate requirements based on best practices for the stack

## File Locations After Deployment

All paths relative to project root:

- **Framework:** `.claude/` (agents, workflows, templates, commands, scripts, config)
- **Configuration:** `project-config.yaml` (project root)
- **CLAUDE.md:** `CLAUDE.md` (project root)
- **Documentation:** `docs/` (project root)
- **Sprint Plans:** `docs/sprints/` (project root)

## Validation and Generation Commands

### Validate Configuration
```bash
python3 .claude/scripts/validate-config.py project-config.yaml
```

### Generate CLAUDE.md
```bash
python3 .claude/scripts/render-template.py \
  -c project-config.yaml \
  -t .claude/templates/CLAUDE.md.template \
  -o CLAUDE.md
```

### Generate Sprint Plan
```bash
python3 .claude/scripts/render-template.py \
  -c project-config.yaml \
  -t .claude/templates/handoffs/sprint-plan-template.md \
  -o docs/sprints/sprint-001-plan.md
```

## Summary

**Phase 1:** Deploy framework from `.vibey/framework/` to `.claude/` (handle existing `.claude/` if present)
**Phase 2:** Run pre-initialization checks (git, dependencies, existing config)
**Phase 3:** Run framework initialization workflow (discover project, configure, plan sprint)

**Result:** Framework deployed, configured, and ready to use!

---

**Now proceed with Phase 1 (Deployment), then Phase 2 (Pre-checks), then Phase 3 (Initialization).**
