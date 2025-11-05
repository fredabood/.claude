# Discovery Mode Implementation

**Loaded when:** User selects Option 3 (Discovery Mode) or runs `/vibey think`

**Purpose:** Unified discovery workflow combining project audit and brainstorming for building project context

**Note:** This mode is **recommended for first-time users** and **existing projects**. It helps you understand what you have and plan what to build next.

---

## Discovery Mode Flow

### Step 0: Check for Existing Context

```bash
# Check if PROJECT-CONTEXT.md exists
if [ -f ".claude/PROJECT-CONTEXT.md" ]; then
  echo "📋 Found existing project context"
  echo ""

  # Show summary
  python3 .claude/scripts/manage-project-context.py query --field summary

  echo ""
  echo "───────────────────────────────────────"
  echo ""
fi
```

**If PROJECT-CONTEXT.md exists:**

```markdown
## Found Existing Project Context

I found existing context from a previous discovery session.

**What would you like to do?**

**A. Resume this context** - Continue building on what we have
   - Add more information through audit or brainstorming
   - Refine existing details
   - Merge new audit data

**B. Replace this context** - Start fresh
   - Archive current context to `docs/archive/discovery/`
   - Begin new discovery session
   - Previous context preserved but not active

**C. View current context** - Review what we have
   - Display PROJECT-CONTEXT.md
   - Then return to this menu

**D. Restore from archive** - Use a previous context
   - List available archived contexts
   - Replace current with selected archive

**Your choice (A/B/C/D):**
```

**Handle user choice:**

**Choice A: Resume**
```bash
echo "Great! Let's build on your existing context."
echo ""
echo "Would you like to:"
echo "  1. Add audit data (analyze codebase)"
echo "  2. Continue brainstorming (Q&A)"
echo ""
```

**Ask the user:**
"How would you like to expand on your existing context?"
- Option 1: Add audit data (analyze codebase)
- Option 2: Continue brainstorming (Q&A)

Parse their response and set `choice` to "1" or "2" accordingly.

```bash
if [ "$choice" = "1" ]; then
  # Go to Audit flow (Step A1)
  # Will merge audit data into existing context
  RESUME_CONTEXT=true
elif [ "$choice" = "2" ]; then
  # Go to Brainstorm flow (Step B1)
  # Will append to existing context
  RESUME_CONTEXT=true
fi
```

**Choice B: Replace**
```bash
echo "Archiving current context..."

python3 .claude/scripts/manage-project-context.py archive --reason replaced

echo "✓ Context archived to docs/archive/discovery/"
echo ""
echo "Starting fresh discovery session..."

# Continue to Step 1 (new discovery)
```

**Choice C: View**
```bash
echo "Current Context:"
echo "═══════════════════════════════════════"
echo ""

cat .claude/PROJECT-CONTEXT.md

echo ""
echo "═══════════════════════════════════════"
echo ""
echo "Press Enter to return to menu..."
read

# Return to Step 0 (show menu again)
```

**Choice D: Restore from Archive**
```bash
echo "📦 Available Archived Contexts:"
echo ""

python3 .claude/scripts/manage-project-context.py list-archives

echo ""
echo "Enter the path to the archive you want to restore:"
echo "(or press Enter to cancel)"
```

**Ask the user:**
"Which archive would you like to restore? (Provide the full path from the list above, or say 'cancel' to skip)"

Parse their response and set `ARCHIVE_PATH` to the path they provide (empty string if they cancel).

```bash
if [ -n "$ARCHIVE_PATH" ]; then
  python3 .claude/scripts/manage-project-context.py restore --file "$ARCHIVE_PATH"

  echo ""
  echo "✓ Context restored!"
  echo ""
  echo "What would you like to do next?"
  echo "  A - Continue with this context (resume)"
  echo "  B - View the restored context"
  echo "  C - Start fresh (replace)"
  echo ""
```

**Ask the user:**
"What would you like to do with the restored context?"
- Option A: Continue with this context (resume)
- Option B: View the restored context
- Option C: Start fresh (replace)

Parse their response and set `next_choice` to "A", "B", or "C" accordingly.

```bash
  if [ "$next_choice" = "A" ]; then
    # Go back to Step 0 Choice A logic
    RESUME_CONTEXT=true
  elif [ "$next_choice" = "B" ]; then
    cat .claude/PROJECT-CONTEXT.md
    # Return to menu
  fi
else
  echo "Cancelled - keeping current context"
fi
```

---

**If PROJECT-CONTEXT.md does NOT exist:**

### Step 1: Welcome and Audit Option

```markdown
# 🔍 Discovery Mode

**Welcome!** I'll help you understand your project and plan what to build next.

I can start in two ways:

## Option 1: Start with Project Audit (Recommended for existing projects)
**If you have existing code:**
- I'll analyze your codebase automatically
- Detect tech stack, security issues, test coverage
- Review git history for sprint patterns
- Build comprehensive project context
- **Time:** 10-105 minutes depending on scope

## Option 2: Start with Conversation (For new projects)
**If you're starting from scratch:**
- Interactive Q&A to explore your ideas
- Build context iteratively
- I'll ask clarifying questions as we go
- **Time:** 10-60 minutes

---

**Which would you like to do?**
- **A** - Start with project audit (I have existing code)
- **B** - Start with conversation (New project or brainstorming)

**Your choice (A/B):**
```

---

## Path A: Audit-First Discovery

### Step A1: Offer Audit Options

```markdown
## Project Audit Options

I can analyze different aspects of your project:

### A. Full Audit (Recommended)
**Includes:**
- Complete codebase analysis (tech stack, security, tests, logging)
- Git history analysis (sprint patterns, velocity)
- **Time:** 70-125 minutes

### B. Codebase Only
**Includes:**
- Tech stack detection
- Security vulnerabilities
- Test coverage
- Code quality metrics
- **Time:** 60-105 minutes

### C. Git History Only
**Includes:**
- Sprint cadence detection
- Development velocity
- Recent work patterns
- **Time:** 10-20 minutes

**Which audit would you like? (A/B/C):**
```

### Step A2: Execute Audit

```bash
# User selects audit type (A, B, or C)

echo "🔍 Running audit... This will take a while."
echo ""

# Execute the selected audit workflow
case $AUDIT_TYPE in
  A)
    # Load and execute: .claude/workflows/planning/codebase-audit-discovery.md
    # Execute all steps (codebase + git)
    ;;
  B)
    # Load and execute: .claude/workflows/planning/codebase-audit-discovery.md
    # Execute codebase steps only (skip git history)
    ;;
  C)
    # Execute git history analysis only
    ;;
esac

# Audit completes and generates docs/codebase-audit-report.md
echo "✅ Audit complete!"
```

### Step A3: Generate Project Context from Audit

```bash
echo "📝 Creating project context..."

# Create PROJECT-CONTEXT.md from audit findings
python3 .claude/scripts/manage-project-context.py create \
  --source audit \
  --audit-file docs/codebase-audit-report.md \
  --confidence high \
  --ready-for-sprint false

echo "✓ Project context saved: .claude/PROJECT-CONTEXT.md"
```

### Step A4: Display Audit Summary and Offer Choices

```markdown
## ✅ Audit Complete!

I've analyzed your project. Here's what I found:

### Tech Stack Detected
- **Backend:** {{ backend_framework }}
- **Frontend:** {{ frontend_framework }}
- **Database:** {{ database_type }}
- **Testing:** {{ test_frameworks }}

### Quality Scores
- **Security:** {{ security_score }}/100 {% if security_score < 85 %}⚠️{% else %}✓{% endif %}
- **Test Coverage:** {{ test_coverage }}% {% if test_coverage < 90 %}⚠️{% else %}✓{% endif %}
- **Logging:** {{ logging_score }}/100 {% if logging_score < 80 %}⚠️{% else %}✓{% endif %}
- **Code Health:** {{ code_health }}/100

{% if git_analysis_available %}
### Sprint Patterns
- **Cadence:** {{ sprint_cadence }}
- **Velocity:** {{ velocity }} commits/week
- **Last Release:** {{ last_release }}
{% endif %}

### Top Recommendations
1. {{ recommendation_1 }}
2. {{ recommendation_2 }}
3. {{ recommendation_3 }}

**Full report:** `docs/codebase-audit-report.md`
**Project context:** `.claude/PROJECT-CONTEXT.md`

---

## What would you like to do next?

**A. Continue with Q&A** - I'll ask about your goals and what you want to build next
   - Refine this context with your vision
   - Add features and priorities
   - Identify what's missing

**B. Plan sprint now** - Skip Q&A, go straight to sprint planning
   - Use audit findings to create sprint
   - Good if you already know what to build

**C. Save context for later** - Exit and review the reports
   - Come back when ready
   - Context is saved in PROJECT-CONTEXT.md

**Your choice (A/B/C):**
```

### Step A5: Handle Post-Audit Choice

#### Choice A: Continue with Q&A

```bash
echo "Great! Let's explore what you want to build..."
echo ""

# Initialize brainstorming session with audit context pre-loaded
session = {
    'context_gathered': {
        # Pre-fill from PROJECT-CONTEXT.md
        'tech_stack': load_from_context('tech_stack'),
        'quality_baseline': load_from_context('quality_scores'),
        'sprint_velocity': load_from_context('sprint_velocity'),
        # Empty fields to gather:
        'goal': null,
        'features': [],
        'priorities': null
    },
    'tokens_used': 5000,  # Audit consumed some
    'turn_count': 0,
    'confidence': 'medium'  # Start medium due to audit data
}

# Go to Step B1 (Brainstorming Loop)
```

**First Question:**
```markdown
## Building on Your Audit Results

I understand your technical foundation. Now let's talk about what you want to build.

**What's your main goal for the next sprint?**
- What problem are you solving?
- What do you want to accomplish?
```

#### Choice B: Plan Sprint Now

```bash
echo "🚀 Launching sprint planning with audit context..."

# Mark context as ready
python3 .claude/scripts/manage-project-context.py update \
  --ready-for-sprint true

# Load sprint planning with context
# Load: .claude/commands/vibey-plan.md
# Sprint planning will detect PROJECT-CONTEXT.md and use it
```

#### Choice C: Save for Later

```bash
echo "✓ Context saved to .claude/PROJECT-CONTEXT.md"
echo ""
echo "When you're ready:"
echo "  - Run '/vibey think' to continue with Q&A"
echo "  - Run '/vibey plan' to create a sprint"
echo ""
echo "Your audit findings are preserved."
```

---

## Path B: Conversation-First Discovery

### Step B1: Initialize Brainstorming Session

```markdown
# 💭 Discovery Mode - Brainstorming

**Session ID:** discover-{{ timestamp }}

I'm here to help you explore and refine your ideas. Let's start:

**Tell me about your idea:**
- What problem are you trying to solve?
- What do you want to build?
```

**Initialize State Variables:**
```python
session = {
    'context_gathered': {},
    'tokens_used': 0,
    'turn_count': 0,
    'confidence': 'low'  # low, medium, high
}
```

### Step B2: Brainstorming Loop

**For Each User Turn:**

#### 2.1: Process User Input

```python
user_input = get_user_message()

# Extract information
extracted = {
    'goal': extract_goal(user_input),
    'users': extract_target_users(user_input),
    'features': extract_features(user_input),
    'tech_stack': extract_tech_mentions(user_input),
    'constraints': extract_constraints(user_input),
    'priorities': extract_priorities(user_input),
    'success_criteria': extract_success_criteria(user_input)
}

# Update session context
session['context_gathered'].update(extracted)
session['tokens_used'] += estimate_tokens(user_input + response)
session['turn_count'] += 1

# Identify gaps and ambiguities
gaps = identify_gaps(session['context_gathered'])
ambiguities = identify_ambiguities(session['context_gathered'])

# Calculate confidence level
if len(gaps) == 0 and len(ambiguities) == 0:
    session['confidence'] = 'high'
elif len(gaps) <= 2 and len(ambiguities) <= 1:
    session['confidence'] = 'medium'
else:
    session['confidence'] = 'low'
```

#### 2.2: Generate Structured Response

```markdown
---

## 📊 Context Summary

**What I Understand So Far:**

**Goal:**
{{ session.context_gathered.goal or '[Not yet clear]' }}

**Target Users/Systems:**
{{ session.context_gathered.users or '[Not specified]' }}

**Key Features:**
{% for feature in session.context_gathered.features %}
- {{ feature }}
{% endfor %}
{% if not session.context_gathered.features %}[No features mentioned yet]{% endif %}

**Technology Mentioned:**
{{ session.context_gathered.tech_stack or '[Tech stack not discussed]' }}

**Constraints:**
{% for constraint in session.context_gathered.constraints %}
- {{ constraint }}
{% endfor %}
{% if not session.context_gathered.constraints %}[No constraints identified]{% endif %}

**Priorities:**
{{ session.context_gathered.priorities or '[Not specified]' }}

**Success Criteria:**
{{ session.context_gathered.success_criteria or '[Not defined]' }}

---

**Gaps I've Identified:**
{% for gap in gaps %}
- {{ gap }}
{% endfor %}
{% if not gaps %}[No major gaps - looking good!]{% endif %}

**Ambiguities:**
{% for ambiguity in ambiguities %}
- {{ ambiguity }}
{% endfor %}
{% if not ambiguities %}[Everything seems clear]{% endif %}

**Confidence Level:** {{ session.confidence | upper }}
{% if session.confidence == 'low' %}
- We're still exploring - keep sharing ideas!
{% elif session.confidence == 'medium' %}
- Getting clearer - a few more questions will get us there
{% elif session.confidence == 'high' %}
- I have a clear picture - we can move forward or refine further
{% endif %}

---

## ❓ Clarifying Questions

{% if session.confidence == 'low' %}
Let's dig deeper:

1. **Scope & Goal:** {{ question_about_primary_goal }}
2. **Users:** {{ question_about_target_users }}
3. **Approach:** {{ question_about_technical_approach }}
4. **Success:** {{ question_about_success_criteria }}
5. **Constraints:** {{ question_about_constraints }}

{% elif session.confidence == 'medium' %}
A few more things to clarify:

1. {{ gap_question_1 }}
2. {{ gap_question_2 }}
3. {{ ambiguity_question_1 }}

{% elif session.confidence == 'high' %}
We're in good shape! A couple final questions:

1. {{ refinement_question_1 }}
2. {{ edge_case_question }}

{% endif %}

---

## 📏 Context Window Usage

**Estimated tokens used:** ~{{ session.tokens_used | format_number }},000 / 200,000 ({{ (session.tokens_used / 200000 * 100) | round }}%)
**Remaining capacity:** ~{{ (200000 - session.tokens_used) | format_number }},000 tokens
**Turns:** {{ session.turn_count }}

{% if session.tokens_used > 100000 %}
⚠️ **We're past halfway** - Consider wrapping up soon to preserve context
{% endif %}
{% if session.tokens_used > 150000 %}
🚨 **Approaching limit** - Let's finalize your plan in the next few turns
{% endif %}

---

{% if session.confidence in ['medium', 'high'] %}
## 🎯 Ready to Move Forward?

Based on our conversation, I can now:

**A. Save context and plan sprint** - Turn this into a structured sprint
**B. Save context for later** - Preserve this conversation, continue later
**C. Continue brainstorming** - Explore more aspects or refine further
**D. Start over** - Reset and explore a different idea

**What would you like to do? (A/B/C/D or continue sharing ideas)**
{% endif %}
```

### Step B3: Handle Brainstorming Exit

#### Exit Option A: Save Context and Plan Sprint

```bash
echo "Saving project context..."

# Create/update PROJECT-CONTEXT.md
python3 .claude/scripts/manage-project-context.py create \
  --source "brainstorm" \
  --goal "$GOAL" \
  --users "$USERS" \
  --features "$FEATURES" \
  --tech-stack "$TECH_STACK" \
  --constraints "$CONSTRAINTS" \
  --priorities "$PRIORITIES" \
  --success-criteria "$SUCCESS_CRITERIA" \
  --confidence "$CONFIDENCE_LEVEL" \
  --ready-for-sprint true

echo "✓ Context saved to .claude/PROJECT-CONTEXT.md"
echo ""
echo "🚀 Launching sprint planning with this context..."

# Load sprint planning
# Load: .claude/commands/vibey-plan.md
```

#### Exit Option B: Save Context for Later

```bash
python3 .claude/scripts/manage-project-context.py create \
  --source "brainstorm" \
  --goal "$GOAL" \
  --users "$USERS" \
  --features "$FEATURES" \
  --tech-stack "$TECH_STACK" \
  --constraints "$CONSTRAINTS" \
  --priorities "$PRIORITIES" \
  --success-criteria "$SUCCESS_CRITERIA" \
  --confidence "$CONFIDENCE_LEVEL" \
  --ready-for-sprint false

echo "✓ Context saved to .claude/PROJECT-CONTEXT.md"
echo ""
echo "Run '/vibey plan' when ready to create a sprint"
```

#### Exit Option C: Continue Brainstorming

```bash
# Continue the brainstorming loop
# Ask more probing questions
# Refine understanding
# Return to Step B2
```

#### Exit Option D: Start Over

```python
# Reset session
session = {
    'context_gathered': {},
    'tokens_used': 0,
    'turn_count': 0,
    'confidence': 'low'
}

echo "Session reset. Let's start fresh."
# Return to Step B1
```

---

## Context Window Safety

```python
# Before each turn, check token usage
if session['tokens_used'] > 180000:
    print("🚨 Context limit approaching - must finalize now")
    print("Options:")
    print("A. Save context and plan sprint")
    print("B. Save context for later")
    force_exit = True
```

---

## Question Generation Strategy

### For Low Confidence:
- Ask broad, open-ended questions
- Explore problem space
- Understand user's vision
- Identify core requirements

### For Medium Confidence:
- Fill specific gaps
- Clarify ambiguities
- Validate assumptions
- Explore edge cases

### For High Confidence:
- Refine details
- Challenge assumptions
- Consider trade-offs
- Finalize approach

---

## Guidelines for Discovery Mode

### Do's:
✅ Recommend audit for existing projects
✅ Offer choice between audit and brainstorming
✅ Allow skipping Q&A if audit is sufficient
✅ Save unified PROJECT-CONTEXT.md regardless of path
✅ Build context iteratively in brainstorming
✅ Track token usage (warn at 50% and 75%)
✅ Summarize understanding after each turn
✅ Offer exit options when confidence is medium/high

### Don'ts:
❌ Don't force audit on new projects
❌ Don't skip context saving on any exit path
❌ Don't judge or dismiss ideas in brainstorming
❌ Don't skip the context summary in brainstorming
❌ Don't let context window fill up
❌ Don't lose gathered context

---

## Context Handoff to Sprint Planning

When user chooses to plan sprint, `PROJECT-CONTEXT.md` contains:

```yaml
source: "audit" or "brainstorm" or "audit+brainstorm"
confidence: "low" / "medium" / "high"
ready_for_sprint: true

# From audit (if available)
tech_stack:
  backend: "{{ backend }}"
  frontend: "{{ frontend }}"
  database: "{{ database }}"
quality_baseline:
  security: {{ score }}
  test_coverage: {{ percentage }}
  logging: {{ score }}
sprint_velocity:
  cadence: "{{ cadence }}"
  velocity: {{ commits_per_week }}

# From brainstorming (if available)
goal: "{{ goal }}"
users: "{{ users }}"
features:
  - feature1
  - feature2
constraints:
  - constraint1
priorities: "{{ priorities }}"
success_criteria: "{{ success_criteria }}"
```

Sprint Planning Agent uses this to:
- Skip questions already answered
- Pre-fill configuration
- Set realistic quality gates based on baseline
- Estimate velocity based on history
- Focus on gaps (usually just timeline and phase breakdown)

---

**Discovery mode ready!** Integrates audit and brainstorming into unified workflow with consistent PROJECT-CONTEXT.md output.
