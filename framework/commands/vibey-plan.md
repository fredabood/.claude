# Sprint Planning Implementation

**Loaded when:** User selects Option 1 (Sprint Planning) or runs `/vibey plan`

---

## Sprint Planning Execution

### Step 1: Check Prerequisites

```bash
# If framework not initialized, deploy it first
if [ "$FRAMEWORK_STATE" = "new" ]; then
  echo "=� First, I need to deploy the framework..."
  # Load and execute: .claude/commands/vibey-deploy.md (Section 5A)
fi
```

### Step 2: Check for Project Context

```bash
# Check if PROJECT-CONTEXT.md exists (from Discovery Mode)
if [ -f ".claude/PROJECT-CONTEXT.md" ]; then
  echo "✓ Found existing project context"
  echo ""

  # Show summary
  python3 .claude/scripts/manage-project-context.py query --field summary

  echo ""
```

**Ask the user:**
"I found existing project context. Would you like to use this for sprint planning?"

Parse their response. If they agree (default yes), set `use_context=""`. If they say no, set `use_context="n"`.

```bash
  if [ "$use_context" != "n" ] && [ "$use_context" != "N" ]; then
    echo "Loading context..."

    # Load context data
    CONTEXT_DATA=$(python3 .claude/scripts/manage-project-context.py query --all --format json)

    # Pre-fill variables from context
    # (Implementation would parse JSON and extract fields)

    CONTEXT_AVAILABLE=true
    SKIP_DISCOVERY=true

    echo "✓ Context loaded - will skip answered questions"
  else
    echo "Starting sprint planning from scratch..."
    CONTEXT_AVAILABLE=false
    SKIP_DISCOVERY=false
  fi
fi

# Fallback: Check for old-style audit report
if [ -f "docs/codebase-audit-report.md" ]; then
  echo " Using existing project audit data"
  AUDIT_DATA_AVAILABLE=true
else
  AUDIT_DATA_AVAILABLE=false
fi
```

**Note:** The above fallback is for backwards compatibility. New workflows should use PROJECT-CONTEXT.md from Discovery Mode (`/vibey think`).

### Step 3: Conversational Sprint Planning

**If CONTEXT_AVAILABLE=true:**
- Skip questions already answered in PROJECT-CONTEXT.md
- Only ask about gaps (usually timeline and phase breakdown)

**If AUDIT_DATA_AVAILABLE=true (legacy):**
- Load audit data from `docs/codebase-audit-report.md`
- Pre-fill tech stack, quality scores, sprint velocity
- Start conversational sprint planning with context
- Skip 15-20 basic discovery questions

**If AUDIT_DATA_AVAILABLE=false AND codebase exists:**
```markdown
Would you like me to run a project audit first? (Recommended for existing projects)

A project audit will:
- Detect your tech stack automatically
- Analyze security vulnerabilities
- Measure test coverage
- Establish quality baselines
- Skip 15-20 discovery questions

This takes 10-105 minutes depending on scope.

**Run audit first?** [Y/n]
```

**If yes** � Offer audit options (Full/Codebase/Git) � Run audit � Continue to planning
**If no** � Start sprint planning from scratch

### Step 4: Sprint Planning Process

```markdown
## Let's Plan Your Sprint! =�

I'll ask you some questions to understand what you want to build.

**First, tell me:** What do you want to accomplish in this sprint?
```

**Gather Requirements Conversationally:**

1. **Primary Goal**
   - "What's the main objective of this sprint?"
   - "What does success look like?"

2. **Features & Scope**
   - "What are the must-have features?"
   - "Any nice-to-have features?"
   - "What's in scope vs out of scope?"

3. **Security & Quality**
   - "Does this involve sensitive data or authentication?"
   - "Are there specific security concerns?"
   - "What are the quality requirements?"

4. **Performance & Scale**
   - "Are there performance requirements?"
   - "Expected load or scale?"

5. **Dependencies & Blockers**
   - "What needs to exist before you can start?"
   - "Any known blockers or unknowns?"
   - "External dependencies?"

6. **Timeline & Priority**
   - "What's the timeline or deadline?"
   - "What's the priority level?"

7. **Tech Stack** (if not from audit)
   - "What's your backend framework?"
   - "Frontend framework?"
   - "Database?"
   - "Testing frameworks?"

### Step 5: Launch Sprint Planning Agent

```markdown
## Analyzing Your Requirements...

I'm using the Sprint Planning Agent to create your sprint plan with:
- Phase-by-phase task breakdown
- Agent orchestration rules for each phase
- Quality gates and success criteria
- Timeline and effort estimates

This will take 2-3 minutes...
```

**Execute Sprint Planning Agent v2.0:**
- Read: `.claude/agents/planning/sprint-planning.md`
- Input: User requirements + audit data (if available) + tech stack
- Process:
  - Phase 1: Discovery & Analysis
  - Phase 2: Prioritization & Sequencing
  - Phase 3: Sprint Plan Creation (with orchestration design)
  - Phase 4: Roadmap Update
- Output: `docs/sprints/sprint-N-plan.md`

### Step 6: Generate Configuration (First Sprint Only)

```bash
if [ ! -f ".claude/project-config.yaml" ]; then
  echo "=� Generating project configuration..."

  # Generate project-config.yaml from gathered requirements
  python3 .claude/scripts/generate-config.py \
    --project-name "$PROJECT_NAME" \
    --project-type "$PROJECT_TYPE" \
    --tech-stack "$TECH_STACK" \
    --output .claude/project-config.yaml

  echo " Configuration created"
fi
```

### Step 7: Generate CLAUDE.md (First Sprint Only)

```bash
if [ ! -f ".claude/CLAUDE.md" ]; then
  echo "=� Generating CLAUDE.md from template..."

  python3 .claude/scripts/render-template.py \
    -c .claude/project-config.yaml \
    -t .claude/templates/CLAUDE.md.template \
    -o .claude/CLAUDE.md

  echo " CLAUDE.md generated with Vibey marker"
fi
```

### Step 8: Create Sprint in Roadmap

```bash
echo "📊 Creating sprint in roadmap..."

# Create sprint entry in roadmap system
# This will:
# - Create .vibey/sprints/sprint-N.yaml with sprint metadata
# - Create .vibey/tasks/sprint-N-tasks.yaml with tasks from plan
# - Update .vibey/tracks/main.yaml to reference the sprint
# - Auto-detect dependencies between tasks

SPRINT_ID="sprint-${SPRINT_NUMBER}"

# For now, manually prompt user to create sprint YAML
# TODO: Implement 'roadmap plan create' command to automate this
echo ""
echo "⚠️  Manual step required:"
echo "   Create sprint YAML at: .vibey/sprints/${SPRINT_ID}.yaml"
echo "   Create tasks YAML at: .vibey/tasks/${SPRINT_ID}-tasks.yaml"
echo ""
echo "   Or use the roadmap-update.py helper (once implemented)"
echo ""
read -p "Press Enter once sprint YAML files are created..."

# Start the sprint
python3 .claude/scripts/roadmap-update.py --start-sprint ${SPRINT_ID}

echo "✓ Sprint ${SPRINT_ID} created and started in roadmap"
```

### Step 9: Update Sprint Marker in CLAUDE.md

```bash
echo "📝 Updating CLAUDE.md with sprint context..."

# Update CLAUDE.md sprint marker to point to roadmap sprint
SPRINT_ID="sprint-${SPRINT_NUMBER}"

# Simple marker update - just update the sprint number section
# The sprint details will be loaded from roadmap when needed
sed -i.bak "s/<!-- CURRENT_SPRINT: .* -->/<!-- CURRENT_SPRINT: ${SPRINT_ID} -->/" .claude/CLAUDE.md
sed -i.bak "s/\*\*Current Sprint:\*\* .*/\*\*Current Sprint:\*\* ${SPRINT_ID} (${SPRINT_NAME})/" .claude/CLAUDE.md

echo "✓ CLAUDE.md updated with sprint marker: ${SPRINT_ID}"
```

### Step 10: Archive Project Context

```bash
# If PROJECT-CONTEXT.md exists, archive it with the sprint
if [ -f ".claude/PROJECT-CONTEXT.md" ]; then
  echo "📦 Archiving project context with sprint..."

  python3 .claude/scripts/manage-project-context.py archive \
    --reason sprint_created \
    --sprint "$SPRINT_NUMBER"

  echo "✓ Context archived to docs/sprints/sprint-$SPRINT_NUMBER-context.md"
  echo "   (PROJECT-CONTEXT.md cleared for next discovery session)"
else
  echo "ℹ️  No PROJECT-CONTEXT.md to archive"
fi
```

**Why archive?**
- PROJECT-CONTEXT.md represents "what to build next"
- Once converted to a sprint, that context has been "consumed"
- Archiving with the sprint preserves the planning rationale
- Clearing PROJECT-CONTEXT.md allows fresh discovery for next sprint

### Step 11: Display Sprint Plan Summary

```markdown
##  Sprint Plan Created!

**Sprint:** Sprint {{ sprint_number }} - {{ sprint_name }}
**Duration:** {{ total_days }} days
**Phases:** {{ total_phases }}

**Phase Orchestration Highlights:**
{% for phase in phases %}
- Phase {{ loop.index }} ({{ phase.name }}): {{ phase.agents | join(' � ') }}
{% endfor %}

**Quality Gates:**
- Security score e {{ security_threshold }}
- Test coverage e {{ test_threshold }}%
- Logging audit e {{ logging_threshold }}

**Files created:**
- Sprint plan: `docs/sprints/sprint-{{ sprint_number }}-plan.md`
- Sprint state: `docs/sprints/sprint-{{ sprint_number }}-state.yaml`

**Next Steps:**
1. Review the sprint plan
2. Tell me: "Start sprint {{ sprint_number }}" or run `/vibey code`
3. I'll track your progress in the state file and follow phase orchestration

**Ready to start?**
```

---

## Guidelines for Sprint Planning

### Do's:
 Ask clarifying questions to understand requirements fully
 Use audit data when available to skip redundant questions
 Generate realistic timelines based on complexity
 Design phase-specific orchestration based on domains
 Set appropriate quality gates for sprint type
 Update ROADMAP.md with sprint info

### Don'ts:
L Don't skip important discovery questions
L Don't create phases larger than 8,000 tokens
L Don't forget to update sprint marker in CLAUDE.md
L Don't proceed without user confirmation on timeline

---

**Sprint planning complete!** User can now run `/vibey code` to begin execution.
