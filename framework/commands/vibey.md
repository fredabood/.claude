# Vibey Framework Command

**Purpose:** Your gateway to agentic development with Vibey

**Usage:**
- **Interactive:** `/vibey` - Show menu with 5 options
- **Direct:** `/vibey <command>` - Skip menu and go directly to a task
  - `/vibey plan` - Sprint Planning
  - `/vibey code` - Execute Sprint
  - `/vibey think` - Brainstorming Mode
  - `/vibey audit` - Project Audit
  - `/vibey manage` - Framework Management

---

## Step 1: Detect Framework State

Check if this is a first-time session or returning session:

```bash
# Check if framework is fully initialized
if [ -f ".claude/project-config.yaml" ] && [ -f ".claude/CLAUDE.md" ] && grep -q "VIBEY_FRAMEWORK_MANAGED" .claude/CLAUDE.md; then
  FRAMEWORK_STATE="initialized"
  FIRST_SESSION=false
else
  FRAMEWORK_STATE="new"

  # Check for Vibey marker file (single source of truth)
  if [ -f ".claude/.vibey-initialized" ]; then
    # Vibey has been deployed before (at least partially)
    FIRST_SESSION=false
  else
    # No marker file - truly first time using Vibey
    FIRST_SESSION=true
  fi
fi
```

**Detection Logic:**
- **FRAMEWORK_STATE="initialized"** → All Vibey files present and configured
- **FRAMEWORK_STATE="new" + FIRST_SESSION=true** → No `.vibey-initialized` marker (show welcome intro)
- **FRAMEWORK_STATE="new" + FIRST_SESSION=false** → Marker exists but not fully configured (show brief setup message)

**Two Vibey Markers Working Together:**

1. **`.claude/.vibey-initialized`** (Deployment marker)
   - Created: During framework deployment (Section 5A)
   - Purpose: Indicates Vibey framework files have been deployed
   - Used for: First session detection
   - Committed: Yes (tells team Vibey is configured)

2. **`<!-- VIBEY_FRAMEWORK_MANAGED -->` in CLAUDE.md** (Generation marker)
   - Created: When CLAUDE.md is generated from template
   - Purpose: Indicates CLAUDE.md was created by Vibey (not hand-written)
   - Used for: Framework initialization detection
   - Committed: Yes (part of CLAUDE.md)
   - Location: First line of `.claude/CLAUDE.md`

**Why two markers?**
- `.vibey-initialized` = "Vibey files deployed" (tracks deployment)
- `VIBEY_FRAMEWORK_MANAGED` = "CLAUDE.md is Vibey-managed" (tracks configuration)
- Both needed to confirm full initialization

**Detection Flow:**
```
Step 1: Check for FULL initialization
├─ .claude/project-config.yaml exists? ✓
├─ .claude/CLAUDE.md exists? ✓
└─ VIBEY_FRAMEWORK_MANAGED in CLAUDE.md? ✓
    → FRAMEWORK_STATE="initialized" + FIRST_SESSION=false

Step 2: Check for PARTIAL deployment
└─ .claude/.vibey-initialized exists?
    ├─ YES → FRAMEWORK_STATE="new" + FIRST_SESSION=false (resume setup)
    └─ NO  → FRAMEWORK_STATE="new" + FIRST_SESSION=true (show welcome)

Step 3: Validate consistency (see below)
```

### Step 1.5: Validate State Consistency

After detecting framework state, validate that markers and files are consistent:

```bash
# Validate Vibey state consistency
validate_vibey_state() {
  local has_marker=$([ -f ".claude/.vibey-initialized" ] && echo "true" || echo "false")
  local has_agents=$([ -d ".claude/agents" ] && echo "true" || echo "false")
  local has_workflows=$([ -d ".claude/workflows" ] && echo "true" || echo "false")
  local has_config=$([ -f ".claude/project-config.yaml" ] && echo "true" || echo "false")

  # Case 1: Marker exists but framework files missing
  if [ "$has_marker" = "true" ] && [ "$has_agents" = "false" ]; then
    echo "⚠️ Inconsistent state detected!"
    echo ""
    echo "The .vibey-initialized marker exists, but framework files are missing."
    echo "This usually happens if .claude/ was partially deleted."
    echo ""
    echo "Options:"
    echo "  1. Delete marker and start fresh (recommended)"
    echo "  2. Re-deploy framework files (keeps marker)"
    echo "  3. Cancel"
    echo ""
```

**Ask the user which option they'd like:**
"I found an inconsistent state - the marker exists but framework files are missing. What would you like to do?"
- Option 1: Delete marker and start fresh (recommended)
- Option 2: Re-deploy framework files
- Option 3: Cancel

Parse their response and set `fix_choice` to "1", "2", or "3" accordingly.

```bash
    if [ "$fix_choice" = "1" ]; then
      rm .claude/.vibey-initialized
      echo "✓ Marker removed. Please run /vibey again to start fresh."
      exit 0
    elif [ "$fix_choice" = "2" ]; then
      echo "Continuing with framework deployment..."
      return 0
    else
      echo "Cancelled"
      exit 1
    fi
  fi

  # Case 2: Framework files exist but marker missing
  if [ "$has_marker" = "false" ] && [ "$has_agents" = "true" ]; then
    echo "⚠️ Inconsistent state detected!"
    echo ""
    echo "Framework files exist but .vibey-initialized marker is missing."
    echo "This usually happens if the marker was accidentally deleted."
    echo ""
    echo "Options:"
    echo "  1. Restore marker (recommended - preserves your setup)"
    echo "  2. Delete all Vibey files and start fresh"
    echo "  3. Cancel"
    echo ""
```

**Ask the user which option they'd like:**
"Framework files exist but the marker is missing. What would you like to do?"
- Option 1: Restore marker (recommended - preserves your setup)
- Option 2: Delete all and start fresh
- Option 3: Cancel

Parse their response and set `fix_choice` to "1", "2", or "3" accordingly.

```bash
    if [ "$fix_choice" = "1" ]; then
      touch .claude/.vibey-initialized
      echo "Restored: $(date)" > .claude/.vibey-initialized
      echo "Version: 2.0" >> .claude/.vibey-initialized
      echo "✓ Marker restored"
      # Update state variables
      FIRST_SESSION=false
      return 0
    elif [ "$fix_choice" = "2" ]; then
      rm -rf .claude/agents .claude/workflows .claude/templates .claude/commands .claude/scripts .claude/docs .claude/config
      [ -f ".claude/project-config.yaml" ] && rm .claude/project-config.yaml
      [ -f ".claude/CLAUDE.md" ] && rm .claude/CLAUDE.md
      echo "✓ Vibey files removed. Please run /vibey again to start fresh."
      exit 0
    else
      echo "Cancelled"
      exit 1
    fi
  fi

  # Case 3: Config exists but marker missing
  if [ "$has_marker" = "false" ] && [ "$has_config" = "true" ]; then
    echo "⚠️ Found project-config.yaml but no Vibey marker."
    echo ""
    echo "This might be an older Vibey installation."
```

**Ask the user:**
"I found a project config but no Vibey marker. This might be an older installation. Would you like me to restore the marker?"

Parse their response. If they say yes/okay/sure (default to yes), set `restore_choice=""`. If they say no, set `restore_choice="n"`.

```bash
    if [ "$restore_choice" != "n" ]; then
      touch .claude/.vibey-initialized
      echo "Restored: $(date)" > .claude/.vibey-initialized
      echo "Version: 2.0" >> .claude/.vibey-initialized
      echo "✓ Marker restored"
      FIRST_SESSION=false
    fi
  fi
}

# Run validation
validate_vibey_state
```

---

## Step 1.5: Check for Direct Command Arguments

**Support for bypassing the menu with positional arguments:**

```bash
# Check if user provided a command argument
COMMAND_ARG="$1"

if [ -n "$COMMAND_ARG" ]; then
  # User provided an argument - route directly
  case "$COMMAND_ARG" in
    plan)
      echo "🚀 Launching Sprint Planning..."
      # Route to Option 1: Sprint Planning
      # Load: .claude/commands/vibey-plan.md
      ;;
    code)
      echo "🚀 Launching Sprint Execution..."
      # Route to Option 2: Execute Sprint
      # Load: .claude/commands/vibey-code.md
      ;;
    think|audit)
      echo "💭 Launching Discovery Mode..."
      # Route to Option 3: Discovery Mode
      # Load: .claude/commands/vibey-think.md
      # Note: 'audit' is a legacy alias for 'think' (both go to Discovery Mode)
      ;;
    manage)
      echo "⚙️ Launching Framework Management..."
      # Route to Option 4: Framework Management
      # Load: .claude/commands/vibey-manage.md
      ;;
    *)
      # Invalid argument provided
      echo "❌ Invalid command: '$COMMAND_ARG'"
      echo ""
      echo "Valid commands:"
      echo "  /vibey plan    - Sprint Planning"
      echo "  /vibey code    - Execute Sprint"
      echo "  /vibey think   - Discovery Mode"
      echo "  /vibey manage  - Framework Management"
      echo ""
      echo "Or run '/vibey' without arguments to see the interactive menu."
      exit 1
      ;;
  esac

  # If we got here, a valid command was provided
  # Skip Step 2 and Step 3 (introduction and menu)
  # Continue directly to Step 4 (routing) with the selected option
fi

# If no argument provided, continue to Step 2 (show introduction/menu)
```

**Command Argument Mapping:**
- `/vibey plan` → Option 1 (Sprint Planning) → vibey-plan.md
- `/vibey code` → Option 2 (Execute Sprint) → vibey-code.md
- `/vibey think` → Option 3 (Discovery Mode) → vibey-think.md
- `/vibey audit` → Option 3 (Discovery Mode) → vibey-think.md [legacy alias]
- `/vibey manage` → Option 4 (Framework Management) → vibey-manage.md

**Benefits:**
- **Speed** - Experienced users can skip the menu
- **Scriptable** - Commands can be used in scripts or automation
- **Memorable** - Simple, intuitive command names
- **Backwards compatible** - Running `/vibey` alone still shows the menu

---

## Step 2: Show Introduction (First Session Only)

**If FIRST_SESSION=true**, display this introduction:

```markdown
# Welcome to Vibey! 🎉

**What is Vibey?**
Vibey is an agentic orchestration framework that transforms Claude Code into a specialized development team. Instead of Claude doing everything alone, Vibey provides:

- **12 Specialized Agents** - Security Reviewer, Test Engineer, ML Engineer, Documentation Engineer, and more
- **Sprint-Driven Orchestration** - Phase-specific agent orchestration tailored to your sprint
- **Quality Gates** - Automated checks for security, testing, logging, and documentation
- **Structured Workflows** - Proven processes for sprint planning, feature development, and audits

**What You Get:**
✓ Context-aware agent orchestration (security sprint ≠ feature sprint)
✓ Consistent quality enforcement (no shipping incomplete work)
✓ Self-documenting sprints (sprint plans show WHAT and HOW)
✓ Reduced cognitive load (Claude knows when to use which agents)

**Using the /vibey Command:**

**Interactive Menu:**
Running `/vibey` gives you 4 options:
1. **Sprint Planning** - Plan your first (or next) sprint with agent orchestration
2. **Execute Sprint** - Execute your planned sprint with phase-specific orchestration
3. **Discovery Mode** ⭐ - Understand what you want to build (RECOMMENDED to start here!)
4. **Framework Management** - Configure settings and manage your Vibey setup

**Direct Commands (skip the menu):**
- `/vibey plan` - Go directly to Sprint Planning
- `/vibey code` - Go directly to Sprint Execution
- `/vibey think` - Go directly to Discovery Mode
- `/vibey manage` - Go directly to Framework Management

**First-time user?** Start with **Discovery Mode** (`/vibey think`) to explore your ideas and understand your project, then export to Sprint Planning when ready!

Let's get started! 🚀
```

**If FIRST_SESSION=false and FRAMEWORK_STATE="new"**, show brief message:
```
Vibey framework detected but not fully initialized. Let's complete setup!
```

**If FIRST_SESSION=false and FRAMEWORK_STATE="initialized"**, show brief message:
```
Welcome back! Vibey is ready to help.
```

---

## Step 3: Present Main Menu

**Always present these 4 options** (regardless of first session or returning):

```markdown
## What would you like to do?

### 1. 📋 Sprint Planning

Plan a sprint with comprehensive task breakdown and agent orchestration.

**What you'll get:**
- Conversational discovery of requirements
- Phase-by-phase task breakdown
- Agent orchestration rules for each phase
- Quality gates and success criteria
- Complete sprint plan document

**Best for:**
- You know what you want to build
- Starting a new feature or sprint
- Continuing existing sprint planning

**Time:** 15-45 minutes depending on sprint complexity

---

### 2. 🚀 Execute Sprint

Execute your planned sprint with phase-specific agent orchestration.

**What you'll get:**
- View current sprint status and progress
- Continue active sprint execution
- Phase-specific agent orchestration
- Quality gate monitoring
- Sprint completion and retrospective

**Best for:**
- You have a sprint plan ready to execute
- Continuing work on an active sprint
- Following structured phase-by-phase development
- Tracking sprint progress and quality gates

**Time:** Varies by phase and sprint complexity

---

### 3. 💭 Discovery Mode ⭐ RECOMMENDED FOR FIRST-TIME USERS

Understand what you want to build through conversation and/or automated analysis.

**What you'll get:**
- **Option A: Conversational Exploration** - Interactive Q&A to articulate your ideas
- **Option B: Project Audit** - Automated codebase and git history analysis
- **Option C: Both** - Audit first, then refine with conversation
- Build context iteratively
- Export to sprint planning when ready

**Best for:**
- **First-time Vibey users** - Learn the framework while building context
- You have ideas but need help articulating them
- Existing projects that need analysis before planning
- Want baseline metrics and context before sprint planning
- Exploring possibilities and tradeoffs

**Time:** 10-105 minutes depending on discovery depth

**Outputs:**
- `.claude/PROJECT-CONTEXT.md` - Discovery findings and project context
- `docs/codebase-audit-report.md` - Automated analysis (if audit selected)
- Ready-to-use context for sprint planning

---

### 4. ⚙️ Framework Management

Configure and manage your Vibey framework settings.

**What you'll get:**
- View current configuration
- Update quality gate thresholds
- Modify framework settings
- Regenerate CLAUDE.md
- Framework health check

**Best for:**
- Adjusting quality standards
- Updating framework configuration
- Troubleshooting framework issues
- Optimizing your Vibey setup

**Time:** 5-15 minutes

---

**Quick Access Commands:**
- `/vibey plan` - Sprint Planning
- `/vibey code` - Execute Sprint
- `/vibey think` - Discovery Mode
- `/vibey manage` - Framework Management

**Or:** Type your request directly (e.g., "I want to build user authentication")

**Choose an option (1, 2, 3, 4) or describe what you need:**
```

---

## Step 4: Route Based on User Choice

### Option 1: Sprint Planning

**Prerequisites Check:**

```bash
# If framework not initialized, deploy it first
if [ "$FRAMEWORK_STATE" = "new" ]; then
  echo "📦 First, I need to deploy the framework..."
  # Run deployment (see Section 5A)
fi

# Check if project audit was already run
if [ -f "docs/codebase-audit-report.md" ]; then
  echo "✓ Using existing project audit data"
  AUDIT_DATA_AVAILABLE=true
else
  AUDIT_DATA_AVAILABLE=false
fi
```

**Sprint Planning Flow:**

1. **If AUDIT_DATA_AVAILABLE=true:**
   - Load audit data from `docs/codebase-audit-report.md`
   - Pre-fill tech stack, quality scores, sprint velocity
   - Start conversational sprint planning with context
   - Skip 15-20 basic discovery questions

2. **If AUDIT_DATA_AVAILABLE=false AND codebase exists:**
   - Ask: "Would you like me to run a project audit first? (Recommended for existing projects)"
   - If yes → Offer audit options → Run audit → Continue
   - If no → Start conversational sprint planning from scratch

3. **Sprint Planning Process:**
   - Ask: "What do you want to build in this sprint?"
   - Gather requirements conversationally
   - Ask clarifying questions:
     - "What's the primary goal?"
     - "Are there security concerns?"
     - "What's the priority?"
     - "Any dependencies or blockers?"
   - Use **Sprint Planning Agent v2.0** (`.claude/agents/planning/sprint-planning.md`)
   - Generate sprint plan with phase-specific orchestration
   - Save to `docs/sprints/sprint-N-plan.md`
   - Update current sprint marker in `.claude/CLAUDE.md`

4. **Output:**
   ```
   ✓ Sprint plan created: docs/sprints/sprint-3-plan.md
   ✓ Sprint marker updated in .claude/CLAUDE.md
   ✓ Ready to begin sprint execution!

   Next steps:
   - Review the sprint plan
   - Tell me: "Start sprint 3" or "Continue sprint 3"
   - I'll follow the phase orchestration to help you build
   ```

**Implementation:** Load `.claude/commands/vibey-plan.md` for detailed Sprint Planning implementation

---

### Option 3: Discovery Mode

**Launch Discovery Mode:**

```markdown
# 💭 Discovery Mode Activated

I'll help you understand what you want to build through conversation and/or automated analysis.

**Choose your discovery approach:**

**A. Conversational Exploration** - Interactive Q&A to articulate your ideas
**B. Project Audit** - Automated codebase and git history analysis
**C. Both** - Audit first, then refine with conversation

**Which would you like?**
```

**Route Based on User Choice:**

---

#### **Option A: Conversational Exploration**

**Launch Conversational Session:**

```markdown
Great! I'll help you explore and articulate your ideas through conversation.

**How This Works:**
- Share your ideas (rough or detailed)
- I'll ask clarifying questions
- I'll summarize what I understand
- We'll iterate until you have clarity
- When ready, we can turn this into a sprint plan

**Context Window Tracking:**
I'll track our conversation length and alert you when we're approaching context limits.

**Ready when you are!** Tell me about your idea, or describe the problem you're trying to solve.
```

**Conversational Loop:**

For each user response:

1. **Process User Input**
   - Extract key information
   - Identify gaps or ambiguities
   - Assess completeness

2. **Generate Response with 3 Parts:**

```markdown
## 📊 Context Summary

**What I Understand So Far:**
[Bullet points summarizing gathered information]
- Goal: [primary objective]
- Users: [target users or systems]
- Key features: [list of features mentioned]
- Tech stack: [technologies mentioned]
- Constraints: [limitations, deadlines, requirements]

**Gaps I've Identified:**
[Bullet points of missing information]
- Need to understand: [specific gap]
- Unclear about: [ambiguity]

**Confidence Level:** [Low/Medium/High] - [explanation]

---

## ❓ Clarifying Questions

[3-5 specific questions to fill gaps or enhance understanding]

1. [Question about primary goal or scope]
2. [Question about users or use cases]
3. [Question about technical approach]
4. [Question about constraints or priorities]
5. [Question about success criteria]

---

## 📏 Context Window Usage

**Estimated tokens used:** ~[X],000 / 200,000 ([Y]%)
**Remaining capacity:** ~[Z],000 tokens

[If > 50%: "⚠️ We're past halfway - consider wrapping up soon"]
[If > 75%: "🚨 Approaching limit - let's finalize your plan"]
```

3. **Exit Conditions:**

```markdown
## 🎯 Ready to Move Forward?

Based on our conversation, I can now:

A. **Create a sprint plan** - Turn this into a structured sprint with phases and tasks
B. **Continue exploring** - Explore more aspects or refine further
C. **Export summary** - Save this as PROJECT-CONTEXT.md
D. **Start over** - Reset and explore a different idea

What would you like to do?
```

**If user chooses A (Create sprint plan):**
- Save context to `.claude/PROJECT-CONTEXT.md`
- Use gathered context as input to Sprint Planning Agent
- Generate sprint plan with orchestration
- Save to `docs/sprints/sprint-N-plan.md`

**If user chooses B (Continue):**
- Continue conversational loop

**If user chooses C (Export summary):**
- Generate `.claude/PROJECT-CONTEXT.md` with all gathered context
- Provide next steps
- User can return to planning later

**If user chooses D (Start over):**
- Clear context summary
- Restart conversational loop

---

#### **Option B: Project Audit**

**Check Prerequisites:**

```bash
# Check if codebase exists
if [ -z "$(find . -maxdepth 3 -type f \( -name '*.py' -o -name '*.js' -o -name '*.ts' \) 2>/dev/null)" ]; then
  echo "⚠️ No codebase detected. Project audit works best with existing code."
  echo "Would you like to:"
  echo "  1. Continue anyway (git history only)"
  echo "  2. Go back to main menu"
  # Handle user choice
fi

# Check if git repository exists
if ! git rev-parse --is-inside-work-tree 2>/dev/null; then
  echo "⚠️ No git repository detected."
  echo "Code audit can still run, but git history analysis requires a git repo."
fi
```

**Offer Audit Options:**

```markdown
## 🔍 Project Audit Options

I can run two types of analysis. Choose what you need:

### A. Full Audit (Both)
**Includes:**
- Complete codebase analysis (tech stack, security, tests, logging, quality)
- Git history analysis (sprint patterns, velocity, recent work)

**Time:** 70-125 minutes
**Output:** Comprehensive audit report with all metrics
**Best for:** First time using Vibey on this project

---

### B. Codebase Audit Only
**Includes:**
- Tech stack detection and validation
- Security analysis (vulnerabilities, best practices)
- Test coverage and quality analysis
- Logging audit
- Code health metrics

**Time:** 60-105 minutes
**Output:** Detailed code health report
**Best for:** Projects without git history or focusing on code quality

---

### C. Git History Only
**Includes:**
- Sprint cadence detection (how often you release)
- Development velocity (commits, PRs, pace)
- Recent work analysis (what was built)
- Team activity patterns

**Time:** 10-20 minutes
**Output:** Historical insights and patterns
**Best for:** Quick context before sprint planning

---

**Choose an option (A, B, or C):**
```

**Run Selected Audit:**

**Option A (Full):**
- Run **Codebase Audit Workflow** (`.claude/workflows/planning/codebase-audit-discovery.md`) - Steps 1-11
- Generate `docs/codebase-audit-report.md` with all sections
- Pre-fill `.claude/project-config.yaml` with detected values
- Display summary of findings

**Option B (Code Only):**
- Run **Codebase Audit Workflow** - Steps 1-8, 10-11 (skip git history)
- Generate `docs/codebase-audit-report.md` without git section
- Pre-fill `.claude/project-config.yaml` with detected values (no velocity)
- Display summary of findings

**Option C (Git Only):**
- Run **Git History Analysis** only (Step 9 from workflow)
- Generate lightweight report: `docs/git-history-analysis.md`
- Pre-fill sprint cadence and velocity data
- Display summary of findings

**After Audit Completes:**

```markdown
## ✅ Audit Complete!

**Report saved to:** `docs/codebase-audit-report.md` [or git-history-analysis.md]
**Context saved to:** `.claude/PROJECT-CONTEXT.md`

**Key Findings:**
- [Top 3-5 key insights from audit]

**Pre-filled Configuration:**
- Tech stack detected and configured
- Quality baselines established
- Sprint velocity estimated

**What's Next?**

Would you like to:
A. Plan a sprint now (using audit data)
B. Continue with conversation (refine the audit findings)
C. Return to main menu
```

---

#### **Option C: Both (Audit + Conversation)**

**Workflow:**

1. **Run Project Audit First**
   - Execute audit (Full, Codebase Only, or Git Only based on user preference)
   - Generate `docs/codebase-audit-report.md`
   - Save findings to `.claude/PROJECT-CONTEXT.md`

2. **Transition to Conversational Exploration**
   ```markdown
   ## ✅ Audit Complete!

   I've analyzed your project. Let me summarize what I found, and then we can discuss:

   **Key Findings:**
   - [Summary of audit findings]

   Now let's explore what you want to build. I'll use the audit as context.

   **Tell me:** What would you like to focus on in your next sprint?
   ```

3. **Conversational Loop with Audit Context**
   - Use audit data to pre-fill technical context
   - Focus conversation on goals, features, priorities
   - Skip tech stack and quality baseline questions (already known from audit)

4. **Exit to Sprint Planning**
   - Combined context (audit + conversation) saved to `.claude/PROJECT-CONTEXT.md`
   - Ready for sprint planning with comprehensive understanding

**Implementation:** Load `.claude/commands/vibey-think.md` for detailed Discovery Mode implementation

---

### Option 4: Framework Management

**Launch Vibey Manager Agent:**

```markdown
# ⚙️ Framework Management Mode

I'm your Vibey Framework Manager. I'll help you configure and optimize your framework setup.

Let me check your current configuration...
```

**Load Current Configuration:**

```bash
# Read current config
if [ -f ".claude/project-config.yaml" ]; then
  CURRENT_CONFIG=$(cat .claude/project-config.yaml)
else
  echo "❌ No configuration found. Please run sprint planning first to initialize."
  exit 1
fi
```

**Display Configuration Summary:**

```markdown
## Current Vibey Configuration

**Framework Version:** 2.0 (Sprint-Driven Orchestration)
**Auto Agent Launch:** {{ auto_launch }}
**Quality Gates Required:** {{ require_quality_gates }}

**Quality Gate Thresholds:**
- Test Coverage: ≥{{ test_coverage_minimum }}%
- Security Score: ≥{{ security_score_minimum }}/100
- Logging Audit: ≥{{ logging_audit_minimum }}/100

**Project Type:** {{ project.type }}
**Tech Stack:**
- Backend: {{ technology_stack.backend }}
- Frontend: {{ technology_stack.frontend }}
- Database: {{ technology_stack.database }}

---

## What would you like to do?

**Configuration:**
1. **Update quality gate thresholds** - Adjust minimum scores
2. **Modify tech stack** - Update technologies used
3. **Change framework settings** - Auto-launch, quality gates required

**Maintenance:**
4. **Regenerate CLAUDE.md** - Refresh framework instructions
5. **Framework health check** - Diagnose any issues
6. **View framework files** - See agents, workflows, templates

**Other:**
7. **Return to main menu**
8. **Exit**

**Choose an option (1-8) or describe what you need:**
```

**Route Based on User Choice:**

User selects option → Launch Vibey Manager Agent with specific task

**Implementation:** Load `.claude/commands/vibey-manage.md` for detailed Framework Management implementation

---

### Option 2: Execute Sprint

**Check for Active Sprint:**

```bash
# Read current sprint status from CLAUDE.md
if [ -f ".claude/CLAUDE.md" ]; then
  SPRINT_ACTIVE=$(grep -A 1 "current_sprint:" .claude/CLAUDE.md | grep "active:" | awk '{print $2}')

  if [ "$SPRINT_ACTIVE" = "true" ]; then
    SPRINT_NUMBER=$(grep -A 2 "current_sprint:" .claude/CLAUDE.md | grep "number:" | awk '{print $2}')
    SPRINT_NAME=$(grep -A 3 "current_sprint:" .claude/CLAUDE.md | grep "name:" | sed 's/.*name: //')
    CURRENT_PHASE=$(grep -A 5 "current_sprint:" .claude/CLAUDE.md | grep "phase:" | sed 's/.*phase: //')
    SPRINT_PLAN=$(grep -A 6 "current_sprint:" .claude/CLAUDE.md | grep "plan_file:" | awk '{print $2}')
  fi
fi
```

**If Active Sprint Exists:**

Display Sprint Dashboard → **Implementation:** Load `.claude/commands/vibey-code.md` for Sprint Execution implementation

**If No Active Sprint:**

```markdown
## No Active Sprint

You don't have an active sprint. Would you like to:

**A. Start an existing sprint plan**
   - Select from available sprint plans in `docs/sprints/`
   - Resume a paused sprint

**B. Create a new sprint plan**
   - Launch Sprint Planning (Option 1)

**C. Return to main menu**

**Choose an option (A/B/C):**
```

**Handle Choice:**

**If A (Start existing):**
```bash
# List available sprint plans
echo "Available Sprint Plans:"
ls -1 docs/sprints/sprint-*-plan.md 2>/dev/null | nl
echo ""
```

**Ask the user which sprint to start:**
Show the list of available sprint plans and ask: "Which sprint would you like to start?"

Parse their response to extract the sprint number and set `sprint_choice` to that number.

```bash
# Update CLAUDE.md with selected sprint
# Set active: true
# Load sprint plan
# Show Phase 1 overview
```

**If B (Create new):**
- Route to Option 1 (Sprint Planning)

**If C (Return):**
- Return to main menu (Step 3)

**Implementation:** Load `.claude/commands/vibey-code.md` for Sprint Execution implementation

---

## Section 5A: Framework Deployment

**Triggered when:** Framework not initialized (FRAMEWORK_STATE="new")

### Deployment Process

1. **Detect Installation Location**

```bash
# Check where framework is located
if [ -d ".vibey/framework" ]; then
  FRAMEWORK_SOURCE=".vibey/framework"
elif [ -d "framework" ]; then
  FRAMEWORK_SOURCE="framework"
else
  echo "❌ Error: Cannot find framework source"
  exit 1
fi
```

2. **Check for Existing .claude Directory and Files**

```bash
# Check if .claude directory exists
if [ -d ".claude" ]; then
  echo "⚠️ Found existing .claude/ directory"

  # Check if Vibey files already exist (safety check)
  if [ -d ".claude/agents" ] && [ -d ".claude/workflows" ]; then
    echo ""
    echo "⚠️ SAFETY CHECK: Vibey framework files already exist!"
    echo ""
    echo "It looks like Vibey was previously deployed but the .vibey-initialized marker is missing."
    echo "Re-deploying could overwrite any customizations you've made."
    echo ""
    echo "Options:"
    echo "  1. Restore marker only (recommended - keeps existing files)"
    echo "  2. Backup and re-deploy (saves existing files, deploys fresh)"
    echo "  3. Re-deploy fresh (⚠️ OVERWRITES existing files)"
    echo "  4. Cancel"
    echo ""
```

**Ask the user for safety choice:**
"Vibey files already exist in .claude/ but the marker is missing. This could overwrite customizations. What would you like to do?"
- Option 1: Restore marker only (recommended)
- Option 2: Backup and re-deploy
- Option 3: Re-deploy fresh (overwrites)
- Option 4: Cancel

Parse their response and set `safety_choice` to "1", "2", "3", or "4" accordingly.

```bash
    if [ "$safety_choice" = "1" ]; then
      # Just recreate marker
      touch .claude/.vibey-initialized
      echo "Restored: $(date)" > .claude/.vibey-initialized
      echo "Version: 2.0" >> .claude/.vibey-initialized
      echo "✓ Marker restored. Existing files preserved."
      return 0  # Skip deployment
    elif [ "$safety_choice" = "2" ]; then
      # Backup before deploying
      backup_dir=".claude-backup-$(date +%Y%m%d-%H%M%S)"
      cp -r .claude "$backup_dir"
      echo "✓ Backup created: $backup_dir"
      echo "Proceeding with fresh deployment..."
      # Continue with deployment
    elif [ "$safety_choice" = "3" ]; then
      echo "⚠️ This will OVERWRITE existing Vibey files."
```

**Ask for confirmation:**
"This will overwrite existing Vibey files. Are you sure you want to continue?"

Parse their response. If they explicitly confirm (yes/sure/ok/confirm), set `confirm_overwrite="y"`. Otherwise set `confirm_overwrite="n"`.

```bash
      if [ "$confirm_overwrite" != "y" ]; then
        echo "Cancelled"
        exit 1
      fi
      # Continue with deployment
    else
      echo "Cancelled"
      exit 1
    fi
  else
    # .claude exists but no Vibey files - ask about merge
    echo "How would you like to proceed?"
    echo "  1. Backup and merge (recommended)"
    echo "  2. Selective merge (preserve custom files)"
    echo "  3. Cancel"
    echo ""
```

**Ask the user:**
"The .claude directory exists but doesn't have Vibey files. How would you like to proceed?"
- Option 1: Backup and merge (recommended)
- Option 2: Selective merge (preserve custom files)
- Option 3: Cancel

Parse their response and set `merge_choice` to "1", "2", or "3" accordingly.

```bash
    # Handle merge choices (existing logic)
  fi
else
  echo "📦 Deploying framework to .claude/..."
  mkdir -p .claude
fi
```

3. **Pre-Flight Checks**

```bash
echo "Running pre-flight checks..."

# Check Python 3 is available
if ! command -v python3 &> /dev/null; then
  echo "❌ Error: Python 3 is required but not found"
  echo "Please install Python 3.7 or later"
  exit 1
fi

# Check if dependencies installed
if ! python3 -c "import yaml; import jinja2" 2>/dev/null; then
  echo "📦 Installing required Python dependencies (PyYAML, Jinja2)..."
  if pip install pyyaml jinja2; then
    echo "✓ Dependencies installed successfully"
  else
    echo "❌ Error: Failed to install dependencies"
    echo "Please manually install: pip install pyyaml jinja2"
    exit 1
  fi
else
  echo "✓ Dependencies already installed"
fi

echo "✓ Pre-flight checks passed"
echo ""
```

4. **Deploy Framework**

```bash
echo "Deploying framework files..."

# Copy framework components
cp -r $FRAMEWORK_SOURCE/agents .claude/
cp -r $FRAMEWORK_SOURCE/workflows .claude/
cp -r $FRAMEWORK_SOURCE/templates .claude/
cp -r $FRAMEWORK_SOURCE/config .claude/
cp -r $FRAMEWORK_SOURCE/commands .claude/
cp -r $FRAMEWORK_SOURCE/scripts .claude/
cp -r $FRAMEWORK_SOURCE/docs .claude/

# Create Vibey marker file (indicates Vibey has been deployed)
# This file helps detect first-time vs returning sessions
touch .claude/.vibey-initialized
echo "Deployed: $(date)" > .claude/.vibey-initialized
echo "Version: 2.0" >> .claude/.vibey-initialized

# Note: .vibey-initialized should be committed to git so team members
# know Vibey is configured for this project

# Verify deployment
if [ -d ".claude/agents" ] && [ -d ".claude/workflows" ] && [ -d ".claude/templates" ]; then
  echo "✓ Framework deployed successfully"
else
  echo "❌ Deployment failed - missing directories"
  exit 1
fi
```

5. **Clean Up**

```bash
# Remove .vibey directory if it exists (temporary installation location)
if [ -d ".vibey" ]; then
  rm -rf .vibey
  echo "✓ Cleaned up temporary files"
fi
```

6. **Create Initial Project Structure**

```bash
# Create directory structure for Vibey workflows
mkdir -p docs/sprints
mkdir -p docs/archive/discovery

echo "✓ Project structure created"
```

7. **Initialize Git (if needed)**

```bash
if ! git rev-parse --is-inside-work-tree 2>/dev/null; then
  echo "This project is not a git repository."
```

**Ask the user:**
"Would you like me to initialize a git repository? (Recommended for version control)"

Parse their response. If they agree, set `init_git="y"`. Otherwise set `init_git="n"`.

```bash
  if [ "$init_git" = "y" ]; then
    git init
    echo "✓ Git repository initialized"
  fi
fi
```

**Deployment Complete:** Return to main menu flow

---


## Important Guidelines

### For All Modes

- **Be conversational** - Natural language, not robotic
- **Ask one thing at a time** - Don't overwhelm with 20 questions
- **Confirm understanding** - Repeat back what you heard
- **Show progress** - Let user know what's happening
- **Be transparent** - Explain why you're asking questions

### For Sprint Planning

- **Context is key** - More context = better orchestration rules
- **Quality matters** - Set appropriate quality gates for sprint type
- **Phase breakdown** - Keep phases under 8,000 tokens (context window)
- **Orchestration design** - Analyze domains → Select agents → Design sequence

### For Discovery Mode

**Conversational Exploration:**
- **No judgment** - All ideas are valid during exploration
- **Build incrementally** - Start broad, get specific
- **Watch context window** - Track and warn about usage
- **Export before limit** - Don't lose valuable context

**Project Audit:**
- **Set expectations** - Audits take time, tell user upfront
- **Show progress** - Update as each section completes
- **Highlight critical** - Emphasize security/quality issues
- **Actionable recommendations** - Provide next steps

**Combined Approach:**
- **Audit first** - Get baseline understanding of project
- **Conversation second** - Refine goals and priorities
- **Comprehensive context** - Best of both worlds

### For Sprint Execution

- **Show context** - Display current sprint status and progress
- **Follow orchestration** - Respect phase-specific agent sequences
- **Enforce quality gates** - Block phase completion if gates fail
- **Track progress** - Update sprint plan continuously
- **Commit often** - Git commit after each phase completion

---

## Summary

The `/vibey` command provides a **unified entry point** for all Vibey interactions:

**First Session:**
1. Show introduction (what is Vibey, what you get)
2. Present 4 options (sprint planning, execution, discovery, management)
3. **Recommend Discovery Mode** for first-time users

**Returning Sessions:**
1. Brief welcome message
2. Present 4 options (same menu)

**All paths lead to productive work:**
- **Sprint Planning** → Structured development with agent orchestration
- **Execute Sprint** → Phase-by-phase execution with agent orchestration and quality gates
- **Discovery Mode** ⭐ → Understand what to build (RECOMMENDED for first-time users)
  - **Option A:** Conversational exploration (idea articulation)
  - **Option B:** Project audit (automated analysis)
  - **Option C:** Both (audit + conversation)
- **Framework Management** → Configure settings, update quality gates, health checks

**Direct Command Access:**
Experienced users can bypass the menu with positional arguments:
- `/vibey plan` → Sprint Planning (Option 1)
- `/vibey code` → Execute Sprint (Option 2)
- `/vibey think` → Discovery Mode (Option 3)
- `/vibey audit` → Discovery Mode (Option 3) [legacy alias]
- `/vibey manage` → Framework Management (Option 4)

**Benefits:**
- **Speed** - Skip the menu, go directly to your task
- **Scriptable** - Use in automation or scripts
- **Memorable** - Simple, intuitive command names
- **Backwards compatible** - `/vibey` alone still shows the menu

**Sprint Execution Dashboard:**
- Accessible via Option 2 (Execute Sprint)
- Shows current sprint status, phase progress, and recent activity
- Provides 9 execution tasks (continue phase, view orchestration, check quality gates, mark phase complete, view plan, update progress, pause sprint, complete sprint, return)
- Loops back to sprint dashboard after each task
- Can pause/resume sprints at any time

**Vibey Manager Agent Integration:**
- Accessible via Option 4 (Framework Management)
- Provides 8 management tasks (quality gates, tech stack, settings, regenerate, health check, view files, return, exit)
- Loops back to management menu after each task
- Can return to main menu at any time

**No separate onboarding flow needed** - The menu works for first-time and experienced users alike. First-time users are guided toward **Discovery Mode** (Option 3) to build context before sprint planning.

---

## Usage Examples

### Interactive Menu (Standard)

```
User: /vibey

Claude: # Welcome to Vibey! 🎉
        [Shows full introduction and menu with 4 options]

User: 3

Claude: # 💭 Discovery Mode Activated
        [Shows 3 discovery options: A, B, C]

User: A

Claude: Great! I'll help you explore and articulate your ideas through conversation.
        [Launches conversational session]
```

### Direct Commands (Fast)

**Example 1: Quick Sprint Planning**
```
User: /vibey plan

Claude: 🚀 Launching Sprint Planning...
        Let's plan your sprint! What do you want to build?
        [Skips menu, goes directly to sprint planning]
```

**Example 2: Continue Active Sprint**
```
User: /vibey code

Claude: 🚀 Launching Sprint Execution...
        # 🚀 Sprint Execution Dashboard
        **Current Sprint:** Sprint 3 - User Authentication
        [Shows sprint dashboard with 9 execution options]
```

**Example 3: Discovery Mode (First-Time User)**
```
User: /vibey think

Claude: 💭 Launching Discovery Mode...
        I'll help you understand what you want to build.

        Choose your discovery approach:
        A. Conversational Exploration
        B. Project Audit
        C. Both
```

**Example 4: Legacy Audit Command**
```
User: /vibey audit

Claude: 💭 Launching Discovery Mode...
        [Same as /vibey think - routes to Discovery Mode]
```

**Example 5: Manage Framework Settings**
```
User: /vibey manage

Claude: ⚙️ Launching Framework Management...
        ## Current Vibey Configuration
        [Shows configuration and 8 management tasks]
```

### Common Workflows

**First-Time User Journey (With Direct Commands):**
```bash
/vibey think          # Discovery Mode → Choose Option A (Conversational)
  → Export to planning
/vibey plan           # Create sprint plan
/vibey code           # Execute sprint
/vibey manage         # Adjust quality gates mid-sprint
```

**Existing Project Journey:**
```bash
/vibey think          # Discovery Mode → Choose Option C (Audit + Conversation)
  → Audit runs first (70-125 min)
  → Refine with conversation
  → Export to planning
/vibey plan           # Create sprint plan with rich context
/vibey code           # Execute sprint
```

**Quick Audit Only:**
```bash
/vibey think          # Discovery Mode → Choose Option B (Audit Only)
  → Select audit scope (Full, Code, or Git)
  → Review findings
/vibey plan           # Plan sprint with audit data
```

**Error Handling:**
```
User: /vibey test

Claude: ❌ Invalid command: 'test'

        Valid commands:
          /vibey plan    - Sprint Planning
          /vibey code    - Execute Sprint
          /vibey think   - Discovery Mode
          /vibey manage  - Framework Management

        Or run '/vibey' without arguments to see the interactive menu.
```

---

**Now execute based on detected framework state and user choice!**
