# Sprint Execution Implementation

**Loaded when:** User selects Option 2 (Execute Sprint) or runs `/vibey code`

---

## Sprint Execution Flow

### Step 1: Check for Active Sprint

```bash
# Read current sprint status from CLAUDE.md
if [ -f ".claude/CLAUDE.md" ]; then
  SPRINT_ACTIVE=$(grep -A 1 "current_sprint:" .claude/CLAUDE.md | grep "active:" | awk '{print $2}')

  if [ "$SPRINT_ACTIVE" = "true" ]; then
    SPRINT_NUMBER=$(grep -A 2 "current_sprint:" .claude/CLAUDE.md | grep "number:" | awk '{print $2}')
    SPRINT_NAME=$(grep -A 3 "current_sprint:" .claude/CLAUDE.md | grep "name:" | sed 's/.*name: //' | tr -d '"')
    CURRENT_PHASE=$(grep -A 5 "current_sprint:" .claude/CLAUDE.md | grep "phase:" | sed 's/.*phase: //' | tr -d '"')
    SPRINT_PLAN=$(grep -A 6 "current_sprint:" .claude/CLAUDE.md | grep "plan_file:" | awk '{print $2}' | tr -d '"')
    SPRINT_STATE=$(grep -A 7 "current_sprint:" .claude/CLAUDE.md | grep "state_file:" | awk '{print $2}' | tr -d '"')
  fi
fi
```

**If Active Sprint Exists** → Display Sprint Dashboard (Step 2)

**If No Active Sprint:**
```markdown
## No Active Sprint

You don't have an active sprint. Would you like to:

**A. Start an existing sprint plan**
   - Select from available sprint plans in `docs/sprints/`
   - Resume a paused sprint

**B. Create a new sprint plan**
   - Run `/vibey plan` to create a sprint

**C. Return to main menu**

**Choose an option (A/B/C):**
```

**Handle Choice:**
- **A:** List sprint plans → User selects → Update CLAUDE.md → Show Phase 1
- **B:** Route to Sprint Planning (load vibey-plan.md)
- **C:** Return to main menu

---

### Step 2: Display Sprint Dashboard

```bash
# Query sprint state for dashboard data
DASHBOARD_DATA=$(python3 .claude/scripts/query-sprint-state.py \
  --state "$SPRINT_STATE" \
  dashboard --format json)

# Extract key metrics
SPRINT_STATUS=$(echo "$DASHBOARD_DATA" | python3 -c "import sys, json; print(json.load(sys.stdin)['sprint']['status'])")
START_DATE=$(echo "$DASHBOARD_DATA" | python3 -c "import sys, json; print(json.load(sys.stdin)['sprint']['started'] or 'Not started')")

# Get current phase details
CURRENT_PHASE_DATA=$(python3 .claude/scripts/query-sprint-state.py \
  --state "$SPRINT_STATE" \
  current-phase)

# Get phase list
PHASE_LIST=$(python3 .claude/scripts/query-sprint-state.py \
  --state "$SPRINT_STATE" \
  list-phases)

# Get recent activity
RECENT_ACTIVITY=$(python3 .claude/scripts/query-sprint-state.py \
  --state "$SPRINT_STATE" \
  recent-activity --limit 5)
```

```markdown
# 🚀 Sprint Execution Dashboard

**Current Sprint:** Sprint $SPRINT_NUMBER - $SPRINT_NAME
**Status:** $SPRINT_STATUS
**Started:** $START_DATE

---

## 📊 Sprint Progress

$PHASE_LIST

---

## 📋 Current Phase Details

$CURRENT_PHASE_DATA

---

## 📝 Recent Activity

$RECENT_ACTIVITY

---

## What would you like to do?

1. **Continue current phase** - Resume work with phase orchestration
2. **View phase orchestration rules** - See agent sequence and quality gates
3. **Check quality gate status** - Run quality checks for current phase
4. **Mark phase complete** - Finish current phase and move to next
5. **View sprint plan** - Review full sprint plan document
6. **Update sprint progress** - Log completed tasks or activities
7. **Pause sprint** - Save progress and pause sprint execution
8. **Complete sprint** - Finish sprint and generate retrospective
9. **Return to main menu**

**Choose an option (1-9):**
```

---

### Option 1: Continue Current Phase

```markdown
## Continuing Phase {{ current_phase_number }}: {{ current_phase_name }}

**Loading phase orchestration from:** {{ sprint_plan_file }}

---

## 📋 Phase Context

{{ phase_description }}

**Agent Orchestration:**
```yaml
agents:
{% for agent in phase_agents %}
  - name: "{{ agent.name }}"
    priority: "{{ agent.priority }}"
    mode: "{{ agent.mode }}"
{% endfor %}

sequence:
  type: "{{ sequence_type }}"
  order: {{ agent_order | to_json }}

quality_gates:
{% for gate in quality_gates %}
  - gate: "{{ gate.name }}"
    threshold: {{ gate.threshold }}
    blocking: {{ gate.blocking }}
{% endfor %}
```

**I'll follow this orchestration to help you execute this phase.**

What specific task would you like to work on?
```

**Execution:**
- Follow agent sequence from phase orchestration
- Launch mandatory agents automatically
- Check quality gates before allowing phase completion
- Update sprint plan with progress as work completes

---

### Option 2: View Phase Orchestration

Display full orchestration rules for current phase including:
- Agent sequence and order
- Trigger conditions for each agent
- Quality gates with thresholds
- Completion criteria
- Rationale for orchestration design

---

### Option 3: Check Quality Gate Status

```bash
# Extract current phase number from state
CURRENT_PHASE_NUM=$(python3 .claude/scripts/query-sprint-state.py \
  --state "$SPRINT_STATE" \
  dashboard --format json | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['current_phase']['number'])")

# Get quality gates status
echo "Checking quality gates for Phase $CURRENT_PHASE_NUM..."
python3 .claude/scripts/query-sprint-state.py \
  --state "$SPRINT_STATE" \
  quality-gates --phase "$CURRENT_PHASE_NUM"
```

**Implementation Note:** Quality gate checks (test coverage, security audit, etc.) are run separately and results are recorded using:

```bash
# Example: Run security audit and record result
# (actual audit command depends on project type)
SECURITY_SCORE=$(run_security_audit)

python3 .claude/scripts/update-sprint-state.py \
  --state "$SPRINT_STATE" \
  quality-gate \
  --phase "$CURRENT_PHASE_NUM" \
  --gate "Security Audit" \
  --status passed \
  --score "$SECURITY_SCORE"
```

---

### Option 4: Mark Phase Complete

```bash
# Check if phase can be completed
echo "Running pre-flight checks..."

COMPLETION_CHECK=$(python3 .claude/scripts/query-sprint-state.py \
  --state "$SPRINT_STATE" \
  check-phase-completion --phase "$CURRENT_PHASE_NUM")

CAN_COMPLETE=$(echo "$COMPLETION_CHECK" | grep -q "can be completed" && echo "yes" || echo "no")

if [ "$CAN_COMPLETE" = "no" ]; then
  echo "❌ Cannot complete phase - blockers detected:"
  echo "$COMPLETION_CHECK"
  echo ""
  echo "Options:"
  echo "1. Continue working on blockers"
  echo "2. View quality gates details"
  echo "3. Override (not recommended)"
  echo "4. Cancel"
  # Handle user choice
else
  echo "✅ Phase $CURRENT_PHASE_NUM ready for completion"
  echo ""
```

**Ask the user:**
"Mark Phase $CURRENT_PHASE_NUM as complete?"

Parse their response. If they agree (default yes), set `confirm=""`. If they say no, set `confirm="n"`.

```bash
  if [ "$confirm" != "n" ] && [ "$confirm" != "N" ]; then
    # Mark phase complete in state
    python3 .claude/scripts/update-sprint-state.py \
      --state "$SPRINT_STATE" \
      complete-phase --phase "$CURRENT_PHASE_NUM"

    # Check if there's a next phase
    TOTAL_PHASES=$(python3 .claude/scripts/query-sprint-state.py \
      --state "$SPRINT_STATE" \
      list-phases | wc -l)

    if [ "$CURRENT_PHASE_NUM" -lt "$TOTAL_PHASES" ]; then
      NEXT_PHASE_NUM=$((CURRENT_PHASE_NUM + 1))

      # Start next phase
      python3 .claude/scripts/update-sprint-state.py \
        --state "$SPRINT_STATE" \
        start-phase --phase "$NEXT_PHASE_NUM"

      # Extract next phase name
      NEXT_PHASE_NAME=$(grep "^## Phase $NEXT_PHASE_NUM:" "$SPRINT_PLAN" | sed "s/^## Phase $NEXT_PHASE_NUM: //")

      # Update CLAUDE.md marker
      python3 .claude/scripts/update-sprint-marker.py \
        --claude-md .claude/CLAUDE.md \
        --phase-number "$NEXT_PHASE_NUM" \
        --phase-name "$NEXT_PHASE_NAME"

      # Git commit
      git add docs/sprints/sprint-$SPRINT_NUMBER-state.yaml .claude/CLAUDE.md
      git commit -m "Complete Phase $CURRENT_PHASE_NUM, start Phase $NEXT_PHASE_NUM

Sprint $SPRINT_NUMBER: $SPRINT_NAME

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

      echo ""
      echo "✅ Phase $CURRENT_PHASE_NUM complete!"
      echo "🚀 Starting Phase $NEXT_PHASE_NUM: $NEXT_PHASE_NAME"
    else
      echo ""
      echo "✅ Phase $CURRENT_PHASE_NUM complete!"
      echo "🎉 This was the final phase! Ready to complete sprint."
    fi
  fi
fi
```

---

### Option 5: View Sprint Plan

Open and display full sprint plan document:
- `docs/sprints/sprint-{{ sprint_number }}-plan.md`

---

### Option 6: Update Sprint Progress

```markdown
## Log Sprint Activity

What would you like to log?

1. **Mark task complete**
2. **Log agent execution**
3. **Add quality gate result**
4. **Add note or observation**

Choose an option (1-4):
```

**Option 1: Mark task complete**
```bash
# List incomplete tasks
PHASE_DETAILS=$(python3 .claude/scripts/query-sprint-state.py \
  --state "$SPRINT_STATE" \
  phase-details --phase "$CURRENT_PHASE_NUM")

echo "Incomplete tasks:"
echo "$PHASE_DETAILS" | grep "○" | nl
echo ""
```

**Ask the user:**
"Which task would you like to mark as complete? (Provide the task description or number from the list above)"

Parse their response and set `TASK_DESC` to the task description they provide.

```bash
python3 .claude/scripts/update-sprint-state.py \
  --state "$SPRINT_STATE" \
  update-task \
  --phase "$CURRENT_PHASE_NUM" \
  --task "$TASK_DESC" \
  --completed

echo "✓ Task marked complete"
```

**Option 2: Log agent execution**
```markdown
```

**Ask the user these questions:**
1. "Which agent was executed?"
2. "What was the status? (completed or failed)"
3. "Any notes or observations? (optional - press enter to skip)"

Parse their responses and set:
- `AGENT_NAME` to their answer to question 1
- `AGENT_STATUS` to their answer to question 2
- `AGENT_NOTES` to their answer to question 3 (can be empty)

```bash
python3 .claude/scripts/update-sprint-state.py \
  --state "$SPRINT_STATE" \
  log-agent \
  --phase "$CURRENT_PHASE_NUM" \
  --agent "$AGENT_NAME" \
  --status "$AGENT_STATUS" \
  --notes "$AGENT_NOTES"

echo "✓ Agent execution logged"
```

**Option 3: Add quality gate result**
```markdown
```

**Ask the user these questions:**
1. "Which quality gate are you recording? (e.g., Security Audit, Test Coverage, Code Review)"
2. "What was the result? (passed or failed)"
3. "What was the score? (optional - press enter to skip)"

Parse their responses and set:
- `GATE_NAME` to their answer to question 1
- `GATE_STATUS` to their answer to question 2
- `GATE_SCORE` to their answer to question 3 (can be empty)

```bash
python3 .claude/scripts/update-sprint-state.py \
  --state "$SPRINT_STATE" \
  quality-gate \
  --phase "$CURRENT_PHASE_NUM" \
  --gate "$GATE_NAME" \
  --status "$GATE_STATUS" \
  ${GATE_SCORE:+--score "$GATE_SCORE"}

echo "✓ Quality gate result recorded"
```

**Option 4: Add note**
```markdown
```

**Ask the user:**
"What note or observation would you like to add to the sprint activity log?"

Parse their response and set `NOTE_TEXT` to the note they provide.

```bash
python3 .claude/scripts/update-sprint-state.py \
  --state "$SPRINT_STATE" \
  log \
  --type note \
  --description "$NOTE_TEXT"

echo "✓ Note added to activity log"
```

---

### Option 7: Pause Sprint

```markdown
```

**Ask the user:**
"Pause sprint and save progress?"

Parse their response. If they agree (default yes), set `confirm=""`. If they say no, set `confirm="n"`.

```bash
if [ "$confirm" != "n" ] && [ "$confirm" != "N" ]; then
  # Pause sprint in state
  python3 .claude/scripts/update-sprint-state.py \
    --state "$SPRINT_STATE" \
    pause-sprint

  # Update CLAUDE.md marker (deactivate)
  python3 .claude/scripts/update-sprint-marker.py \
    --claude-md .claude/CLAUDE.md \
    --deactivate

  # Git commit
  git add docs/sprints/sprint-$SPRINT_NUMBER-state.yaml .claude/CLAUDE.md
  git commit -m "Pause Sprint $SPRINT_NUMBER

All progress preserved in state file.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

  echo ""
  echo "✅ Sprint paused"
  echo "📁 Progress saved to: $SPRINT_STATE"
  echo ""
  echo "To resume: run /vibey code and select the sprint"
fi
```

---

### Option 8: Complete Sprint

```bash
# Check if all phases are complete
INCOMPLETE_PHASES=$(python3 .claude/scripts/query-sprint-state.py \
  --state "$SPRINT_STATE" \
  list-phases | grep -v "✓" | grep -v "^$")

if [ -n "$INCOMPLETE_PHASES" ]; then
  echo "❌ Cannot complete sprint - incomplete phases:"
  echo "$INCOMPLETE_PHASES"
  echo ""
  echo "Options:"
  echo "1. Return to dashboard"
  echo "2. Complete anyway (not recommended)"
  # Handle user choice
else
```

**Ask the user:**
"All phases complete! Mark Sprint $SPRINT_NUMBER as complete and generate retrospective?"

Parse their response. If they agree (default yes), set `confirm=""`. If they say no, set `confirm="n"`.

```bash
  if [ "$confirm" != "n" ] && [ "$confirm" != "N" ]; then
    # Mark sprint complete
    python3 .claude/scripts/update-sprint-state.py \
      --state "$SPRINT_STATE" \
      complete-sprint

    # Update CLAUDE.md marker (deactivate)
    python3 .claude/scripts/update-sprint-marker.py \
      --claude-md .claude/CLAUDE.md \
      --deactivate

    # Generate retrospective
    echo "📝 Generating sprint retrospective..."

    # Extract summary from state
    SUMMARY=$(python3 .claude/scripts/query-sprint-state.py \
      --state "$SPRINT_STATE" \
      summary)

    ACTIVITY=$(python3 .claude/scripts/query-sprint-state.py \
      --state "$SPRINT_STATE" \
      recent-activity --limit 20)

    # Create retrospective file
    cat > "docs/sprints/sprint-$SPRINT_NUMBER-retrospective.md" << EOF
# Sprint $SPRINT_NUMBER Retrospective: $SPRINT_NAME

**Completed:** $(date +%Y-%m-%d)

## Sprint Summary

$SUMMARY

## Key Activities

$ACTIVITY

## What Went Well

- [To be filled in]

## What Could Be Improved

- [To be filled in]

## Action Items for Next Sprint

- [To be filled in]

---

*Retrospective template - fill in observations and learnings*
EOF

    # Update ROADMAP.md (if exists)
    if [ -f "docs/ROADMAP.md" ]; then
      echo "" >> docs/ROADMAP.md
      echo "## ✅ Sprint $SPRINT_NUMBER: $SPRINT_NAME (Completed $(date +%Y-%m-%d))" >> docs/ROADMAP.md
      echo "See: docs/sprints/sprint-$SPRINT_NUMBER-retrospective.md" >> docs/ROADMAP.md
    fi

    # Git commit
    git add docs/sprints/sprint-$SPRINT_NUMBER-*.* .claude/CLAUDE.md docs/ROADMAP.md
    git commit -m "Complete Sprint $SPRINT_NUMBER: $SPRINT_NAME

🎉 Sprint successfully completed!

See retrospective: docs/sprints/sprint-$SPRINT_NUMBER-retrospective.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

    echo ""
    echo "🎉 Sprint $SPRINT_NUMBER completed!"
    echo "📄 Retrospective: docs/sprints/sprint-$SPRINT_NUMBER-retrospective.md"
    echo ""
    echo "Ready to plan your next sprint? Run /vibey plan"
  fi
fi
```

---

### Option 9: Return to Main Menu

Return to main `/vibey` menu

---

## Sprint Execution Loop

After any action → Return to Sprint Dashboard (unless user chooses Return to Main Menu)

This creates a continuous execution loop:
1. View dashboard
2. Choose action
3. Execute action
4. Return to dashboard
5. Repeat

---

## Guidelines for Sprint Execution

### Do's:
✅ Follow phase orchestration rules
✅ Enforce quality gates (block phase completion if gates fail)
✅ Update sprint plan continuously
✅ Git commit after each phase completion
✅ Track progress for retrospective

### Don'ts:
❌ Don't skip mandatory agents
❌ Don't ignore blocking quality gate failures
❌ Don't move to next phase without completing current
❌ Don't forget to update sprint marker in CLAUDE.md

---

**Sprint execution ready!** User can work through phases systematically with quality enforcement.
