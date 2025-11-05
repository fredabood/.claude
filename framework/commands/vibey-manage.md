# Framework Management Implementation

**Loaded when:** User selects Option 5 (Framework Management) or runs `/vibey manage`

---

## Framework Management Execution

### Step 1: Load Current Configuration

```bash
# Read current config
if [ -f ".claude/project-config.yaml" ]; then
  CURRENT_CONFIG=$(cat .claude/project-config.yaml)
else
  echo "❌ No configuration found. Please run sprint planning first to initialize."
  exit 1
fi
```

---

### Step 2: Display Configuration Summary

```markdown
# ⚙️ Framework Management Mode

I'm your Vibey Framework Manager. I'll help you configure and optimize your framework setup.

Let me check your current configuration...

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

---

### Task 1: Update Quality Gate Thresholds

```markdown
## Updating Quality Gate Thresholds

**Current Thresholds:**
- Test Coverage: ≥{{ current_test_coverage }}%
- Security Score: ≥{{ current_security_score }}/100
- Logging Audit: ≥{{ current_logging_audit }}/100

**What would you like to change?**

1. Test coverage minimum
2. Security score minimum
3. Logging audit minimum
4. All thresholds
5. Cancel

Choose an option:
```

**Execute Update:**

**Ask the user:**
"What value would you like to set for [the selected quality gate threshold]?"

Parse their response and set `new_value` to the number they provide.

```bash
# Update project-config.yaml
python3 .claude/scripts/update-config.py \
  --config .claude/project-config.yaml \
  --key "quality_gates.unit_testing.coverage_minimum" \
  --value "$new_value"

# Regenerate CLAUDE.md to apply changes
python3 .claude/scripts/render-template.py \
  -c .claude/project-config.yaml \
  -t .claude/templates/CLAUDE.md.template \
  -o .claude/CLAUDE.md

echo "✓ Quality gate updated"
echo "✓ CLAUDE.md regenerated with new thresholds"
```

**Return to management menu**

---

### Task 2: Modify Tech Stack

```markdown
## Updating Tech Stack

**Current Tech Stack:**
- Backend: {{ backend }}
- Frontend: {{ frontend }}
- Database: {{ database }}
- Testing: {{ testing }}

**What would you like to update?**

1. Backend framework
2. Frontend framework
3. Database
4. Testing frameworks
5. All tech stack
6. Cancel

Choose an option:
```

**Execute Update:**
```bash
# Update tech stack in config
python3 .claude/scripts/update-config.py \
  --config .claude/project-config.yaml \
  --key "technology_stack.backend.framework" \
  --value "$new_backend"

# Regenerate CLAUDE.md
python3 .claude/scripts/render-template.py \
  -c .claude/project-config.yaml \
  -t .claude/templates/CLAUDE.md.template \
  -o .claude/CLAUDE.md

echo "✓ Tech stack updated"
echo "✓ CLAUDE.md regenerated"
```

**Return to management menu**

---

### Task 3: Change Framework Settings

```markdown
## Framework Settings

**Current Settings:**
- Auto Agent Launch: {{ auto_launch }}
- Quality Gates Required: {{ require_quality_gates }}
- Sprint-Driven Orchestration: {{ sprint_driven_orchestration.enabled }}

**What would you like to change?**

1. Toggle auto agent launch (currently: {{ auto_launch }})
2. Toggle required quality gates (currently: {{ require_quality_gates }})
3. Both settings
4. Cancel

Choose an option:
```

**Execute Update:**
```bash
# Toggle settings
python3 .claude/scripts/update-config.py \
  --config .claude/project-config.yaml \
  --key "framework.auto_agent_launch" \
  --value "$new_value"

# Regenerate CLAUDE.md
python3 .claude/scripts/render-template.py \
  -c .claude/project-config.yaml \
  -t .claude/templates/CLAUDE.md.template \
  -o .claude/CLAUDE.md

echo "✓ Framework settings updated"
```

**Return to management menu**

---

### Task 4: Regenerate CLAUDE.md

```markdown
## Regenerating CLAUDE.md

This will regenerate .claude/CLAUDE.md from the template using your current configuration.

**Warning:** If you've made manual edits to CLAUDE.md, they will be LOST.

**Options:**
1. Backup and regenerate (recommended)
2. Regenerate without backup
3. Cancel

Choose an option:
```

**Execute Regeneration:**
```bash
if [ "$choice" = "1" ]; then
  # Backup current CLAUDE.md
  cp .claude/CLAUDE.md .claude/CLAUDE.md.backup-$(date +%Y%m%d-%H%M%S)
  echo "✓ Backup created"
fi

# Regenerate CLAUDE.md
python3 .claude/scripts/render-template.py \
  -c .claude/project-config.yaml \
  -t .claude/templates/CLAUDE.md.template \
  -o .claude/CLAUDE.md

echo "✓ CLAUDE.md regenerated"
```

**Return to management menu**

---

### Task 5: Framework Health Check

```markdown
## Running Framework Health Check...

Checking framework integrity...
```

**Health Check Function:**
```bash
health_check_vibey_framework() {
  local issues=0

  echo "Checking framework files..."

  # Check marker file
  if [ ! -f ".claude/.vibey-initialized" ]; then
    echo "❌ Missing .vibey-initialized marker"
    issues=$((issues + 1))
  else
    echo "✓ Vibey marker present"
  fi

  # Check CLAUDE.md marker
  if [ -f ".claude/CLAUDE.md" ]; then
    if grep -q "VIBEY_FRAMEWORK_MANAGED" .claude/CLAUDE.md; then
      echo "✓ CLAUDE.md has Vibey marker"
    else
      echo "⚠️ CLAUDE.md missing Vibey marker"
      issues=$((issues + 1))
    fi
  else
    echo "❌ CLAUDE.md missing"
    issues=$((issues + 1))
  fi

  # Check config
  if [ -f ".claude/project-config.yaml" ]; then
    echo "✓ Configuration file present"
    # Validate config
    if python3 .claude/scripts/validate-config.py .claude/project-config.yaml 2>/dev/null; then
      echo "✓ Configuration valid"
    else
      echo "❌ Configuration has errors"
      issues=$((issues + 1))
    fi
  else
    echo "❌ Configuration file missing"
    issues=$((issues + 1))
  fi

  # Check framework directories
  for dir in agents workflows templates commands scripts; do
    if [ -d ".claude/$dir" ]; then
      echo "✓ .claude/$dir/ present"
    else
      echo "❌ .claude/$dir/ missing"
      issues=$((issues + 1))
    fi
  done

  # Check sprint context
  if [ -f ".claude/CLAUDE.md" ]; then
    if grep -q "current_sprint:" .claude/CLAUDE.md; then
      echo "✓ Sprint context section present"
    else
      echo "⚠️ Sprint context section missing (may need CLAUDE.md regeneration)"
    fi
  fi

  echo ""
  if [ $issues -eq 0 ]; then
    echo "✅ Framework health: GOOD (no issues detected)"
  else
    echo "⚠️ Framework health: ISSUES DETECTED ($issues issues found)"
    echo ""
    echo "Recommended actions:"
    if [ ! -f ".claude/.vibey-initialized" ]; then
      echo "  - Run consistency validation (automatic on next /vibey)"
    fi
    if [ $issues -gt 2 ]; then
      echo "  - Consider running /vibey to repair framework"
    fi
  fi
}

health_check_vibey_framework
```

**Display Results:**
```markdown
## Health Check Complete

{{ health_check_results }}

**What would you like to do?**
1. Fix detected issues
2. Return to framework management menu
3. Return to main menu
```

**Return to management menu**

---

### Task 6: View Framework Files

```markdown
## Framework Files

**Available Agents:** (`.claude/agents/`)
```

```bash
# List agents by category
echo "**Planning Agents:**"
ls -1 .claude/agents/planning/*.md | sed 's/.*\///; s/\.md$//' | sed 's/^/- /'

echo ""
echo "**Development Agents:**"
ls -1 .claude/agents/development/*.md | sed 's/.*\///; s/\.md$//' | sed 's/^/- /'

echo ""
echo "**Quality Agents:**"
ls -1 .claude/agents/quality/*.md | sed 's/.*\///; s/\.md$//' | sed 's/^/- /'

echo ""
echo "**Documentation Agents:**"
ls -1 .claude/agents/documentation/*.md | sed 's/.*\///; s/\.md$//' | sed 's/^/- /'
```

```markdown
**Available Workflows:** (`.claude/workflows/`)
- Sprint Planning
- Single Feature Development
- Frontend Feature Development
- ML Model Development
- Infrastructure Setup
- Security Audit
- Performance Optimization
- Logging Implementation
- Codebase Audit Discovery

**Available Templates:** (`.claude/templates/handoffs/`)
- API Spec Template
- Security Report Template
- Database Schema Design Template
- ML Evaluation Report Template
- Frontend Design Template
- And more...

**What would you like to do?**
1. View a specific agent file
2. View a specific workflow
3. Return to framework management menu
```

**Return to management menu**

---

### Task 7: Return to Main Menu

Return to main `/vibey` menu

---

### Task 8: Exit

```markdown
Framework management complete. Goodbye!
```

---

## Management Session Loop

After completing any task (1-6), return to framework management menu with updated configuration displayed.

**Loop Flow:**
1. Display configuration summary
2. User selects task
3. Execute task
4. Show success message
5. Ask: "Return to framework management menu? [Y/n]"
6. If yes → Loop to step 1
7. If no → Return to main menu

---

## Guidelines for Framework Management

### Do's:
✅ Show current configuration before allowing changes
✅ Validate configuration after updates
✅ Regenerate CLAUDE.md after config changes
✅ Backup before destructive operations
✅ Provide clear success/error messages
✅ Return to management menu after each task

### Don'ts:
❌ Don't allow invalid configuration values
❌ Don't regenerate CLAUDE.md without warning about manual edits
❌ Don't skip health checks when issues detected
❌ Don't forget to update sprint plans if quality gates change mid-sprint

---

## Configuration Management Best Practices

### Quality Gate Adjustments

**When to lower thresholds:**
- Starting new project (build up gradually)
- Legacy codebase (set realistic baselines)
- Rapid prototyping (relax temporarily)

**When to raise thresholds:**
- After successful sprint (incremental improvement)
- Production-ready phase (enforce higher quality)
- Security-critical projects (strict from start)

### Tech Stack Updates

**When to update:**
- Framework version upgrades
- Adding new technologies
- Migrating to different stack
- Correcting detection errors

**Impact:**
- Sprint Planning Agent adapts questions
- Agent selection may change
- Workflow recommendations update
- Quality gate criteria may adjust

### Framework Settings

**Auto Agent Launch:**
- `true`: Agents launch automatically based on triggers
- `false`: User must explicitly request agents

**Required Quality Gates:**
- `true`: Block phase completion if gates fail
- `false`: Gates are advisory only (not recommended for production)

---

**Framework management ready!** Users can optimize their Vibey configuration at any time.
