# Troubleshooting Guide

Common issues and solutions for the Vibey Agent Framework.

---

## Table of Contents

- [Installation Issues](#installation-issues)
- [Configuration Issues](#configuration-issues)
- [Deployment Issues](#deployment-issues)
- [Sprint Planning Issues](#sprint-planning-issues)
- [Sprint Execution Issues](#sprint-execution-issues)
- [Agent Issues](#agent-issues)
- [Script Issues](#script-issues)
- [Performance Issues](#performance-issues)
- [Getting Help](#getting-help)

---

## Installation Issues

### Python Not Found

**Error:**
```
❌ Error: Python 3 is required but not found
```

**Solution:**
```bash
# macOS
brew install python3

# Ubuntu/Debian
sudo apt-get install python3

# Verify installation
python3 --version
```

---

### Dependencies Not Installing

**Error:**
```
❌ Error: Failed to install dependencies
```

**Solution 1: Install Manually**
```bash
pip install pyyaml jinja2

# Or with pip3
pip3 install pyyaml jinja2

# Verify
python3 -c "import yaml, jinja2; print('OK')"
```

**Solution 2: Check pip**
```bash
# Install pip if missing
python3 -m ensurepip --upgrade

# Upgrade pip
python3 -m pip install --upgrade pip
```

**Solution 3: Use Virtual Environment**
```bash
# Create venv
python3 -m venv .venv

# Activate
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Install
pip install pyyaml jinja2
```

---

## Configuration Issues

### Config Validation Fails

**Error:**
```
❌ Configuration has errors
```

**Solution 1: Validate Manually**
```bash
python3 .claude/scripts/validate-config.py .claude/project-config.yaml
```

**Solution 2: Check Required Fields**
```yaml
# Ensure these sections exist:
project:
  name: "your-project"
  type: "web-app"  # or api, ml, data-platform, infrastructure

technology_stack:
  backend:
    language: "python"
  frontend:
    framework: "react"

framework:
  orchestration_mode: "balanced"
```

**Solution 3: Start from Template**
```bash
# Copy a working template
cp .claude/config/config-templates/web-application-fullstack.yaml .claude/project-config.yaml

# Edit for your project
```

---

### Missing Config File

**Error:**
```
❌ Configuration file missing
```

**Solution:**
```bash
# Generate new config
python3 .claude/scripts/generate-config.py \
  --project-name "Your Project" \
  --project-type web-app \
  --tech-stack "Python/FastAPI, React, PostgreSQL" \
  --output .claude/project-config.yaml
```

---

## Deployment Issues

### Framework Files Not Deployed

**Error:**
```
❌ .claude/agents/ missing
❌ .claude/workflows/ missing
```

**Solution:**
```bash
# Check if framework source exists
ls framework/agents framework/workflows

# If exists, deploy manually
cp -r framework/agents .claude/
cp -r framework/workflows .claude/
cp -r framework/templates .claude/
cp -r framework/config .claude/
cp -r framework/commands .claude/
cp -r framework/scripts .claude/
cp -r framework/docs .claude/

# Create marker
touch .claude/.vibey-initialized
echo "Deployed: $(date)" > .claude/.vibey-initialized
echo "Version: 1.2.0" >> .claude/.vibey-initialized
```

---

### Pre-Flight Checks Failed

**Error:**
```
❌ Python 3 not found
❌ PyYAML missing
```

**Solution:**
See [Installation Issues](#installation-issues) above.

---

### Deployment Backup Overwrites

**Issue:** Deployment created `.claude-backup-*` directory and I don't want it.

**Solution:**
```bash
# Remove backup (if you're sure)
rm -rf .claude-backup-*

# Or keep it until you've verified deployment works
# Then delete later
```

---

## Sprint Planning Issues

### Can't Generate Config

**Error:**
```
❌ generate-config.py: command not found
```

**Solution:**
```bash
# Check if script exists
ls -la .claude/scripts/generate-config.py

# If missing, re-deploy framework
# If exists but not executable:
chmod +x .claude/scripts/generate-config.py

# Run directly
python3 .claude/scripts/generate-config.py --help
```

---

### Sprint Plan Not Created

**Error:**
Sprint planning completes but no file in `docs/sprints/`.

**Solution 1: Check Directory**
```bash
# Create directory if missing
mkdir -p docs/sprints

# Try planning again
```

**Solution 2: Check Permissions**
```bash
# Ensure you can write to docs/
touch docs/test.txt
rm docs/test.txt
```

---

### Context Not Loading

**Issue:** Sprint planning isn't using existing PROJECT-CONTEXT.md.

**Solution:**
```bash
# Check context file location
ls -la .claude/PROJECT-CONTEXT.md

# Should be in .claude/, not docs/

# If in wrong location, move it
mv docs/PROJECT-CONTEXT.md .claude/

# Verify format
head -20 .claude/PROJECT-CONTEXT.md
```

---

## Sprint Execution Issues

### No Active Sprint

**Error:**
```
No Active Sprint

You don't have an active sprint.
```

**Solution 1: Start Sprint**
```
/vibey code
Choose Option A: Start an existing sprint plan
Select your sprint
```

**Solution 2: Create Sprint First**
```
/vibey plan
Complete sprint planning
Then: /vibey code
```

---

### Sprint State File Missing

**Error:**
```
⚠️ Sprint state file missing
```

**Solution:**
```bash
# Check if sprint plan exists
ls docs/sprints/sprint-1-plan.md

# Generate state from plan
python3 .claude/scripts/create-sprint-state.py \
  --plan-file docs/sprints/sprint-1-plan.md \
  --output docs/sprints/sprint-1-state.yaml
```

---

### Can't Mark Phase Complete

**Error:**
```
❌ Cannot complete phase - blockers detected
```

**Solution 1: Check Quality Gates**
```bash
# View quality gate status
python3 .claude/scripts/query-sprint-state.py \
  --state docs/sprints/sprint-1-state.yaml \
  quality-gates --phase 1
```

**Solution 2: Update Quality Gates**
```bash
# Mark quality gate as passed
python3 .claude/scripts/update-sprint-state.py \
  --state docs/sprints/sprint-1-state.yaml \
  quality-gate \
  --phase 1 \
  --gate "Security Audit" \
  --status passed \
  --score 85
```

**Solution 3: Override (Not Recommended)**
If gates are incorrect or you need to proceed:
- Choose "Override" option when prompted
- Document why gates were overridden

---

## Agent Issues

### Agents Not Triggering

**Issue:** Expected agent doesn't activate automatically.

**Solution 1: Check Orchestration Mode**
```yaml
# In .claude/project-config.yaml
framework:
  orchestration_mode: "balanced"  # or "simple" or "tiered"
```

**Solution 2: Use Explicit Agent Request**
```
# Instead of: "Review security"
# Say: "Run a security review using the Security Reviewer agent"
```

**Solution 3: Check Trigger Patterns**
```bash
# View agent trigger patterns
grep -A 5 "Trigger Patterns" .claude/agents/quality/security-reviewer.md
```

---

### Wrong Agent Selected

**Issue:** Different agent than expected was used.

**Solution:**
```
# Be explicit about which agent
"Use the [Agent Name] agent to [task]"

# Example:
"Use the Web Developer agent to implement authentication"
```

---

## Script Issues

### Script Not Executable

**Error:**
```
Permission denied: ./script-name.py
```

**Solution:**
```bash
# Make executable
chmod +x .claude/scripts/*.py

# Or run with python3
python3 .claude/scripts/script-name.py
```

---

### Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'yaml'
```

**Solution:**
```bash
pip install pyyaml jinja2

# Verify
python3 -c "import yaml; print('PyYAML OK')"
python3 -c "import jinja2; print('Jinja2 OK')"
```

---

### Script Fails on Nested Config

**Error:**
```
KeyError: 'quality_gates.unit_testing.coverage_minimum'
```

**Solution:**
```bash
# Update with correct key path
python3 .claude/scripts/update-config.py \
  --config .claude/project-config.yaml \
  --key "quality_gates.unit_testing.coverage_minimum" \
  --value "90"

# Note: Use dots for nested keys
```

---

## Performance Issues

### Slow Sprint Planning

**Issue:** Sprint planning takes very long.

**Solution 1: Skip Audit**
- If planning for new feature, skip codebase audit
- Use existing context from previous audits

**Solution 2: Reduce Audit Scope**
```
# Instead of: Full Audit
# Choose: Codebase Only (skip git history)
# Or: Git History Only (skip codebase scan)
```

---

### Large Context Files

**Issue:** PROJECT-CONTEXT.md or sprint plans are huge.

**Solution:**
```bash
# Archive old contexts
python3 .claude/scripts/manage-project-context.py archive --reason cleanup

# Check archive
ls docs/archive/discovery/
```

---

## Framework Maintenance

### Check Framework Health

**Run Health Check:**
```
/vibey manage
Choose Option 5: Framework health check
```

**Manual Health Check:**
```bash
# Check version
python3 .claude/scripts/check-version.py

# Check files
ls -la .claude/.vibey-initialized
ls -la .claude/CLAUDE.md
ls -la .claude/project-config.yaml

# Check directories
ls .claude/agents
ls .claude/workflows
ls .claude/templates
ls .claude/scripts
```

---

### Framework Update Available

**Check for Updates:**
```bash
python3 .claude/scripts/check-version.py
```

**Upgrade Framework:**
```bash
# 1. Pull latest framework code (in framework repo)
cd /path/to/vibey
git pull

# 2. Re-deploy to your project
cd /path/to/your/project
cp -r /path/to/vibey/framework/* .claude/

# 3. Update marker
echo "Version: 1.2.0" > .claude/.vibey-initialized
```

---

### Rollback Framework

**List Backups:**
```bash
python3 .claude/scripts/rollback-framework.py --list
```

**Rollback to Recent:**
```bash
python3 .claude/scripts/rollback-framework.py --auto
```

**Rollback to Specific:**
```bash
python3 .claude/scripts/rollback-framework.py \
  --backup .claude-backup-20241105-143022
```

---

## Common Error Messages

### "VIBEY_FRAMEWORK_MANAGED marker missing"

**Meaning:** CLAUDE.md doesn't have Vibey marker.

**Solution:**
```bash
# Add marker manually
echo "<!-- VIBEY_FRAMEWORK_MANAGED -->" >> .claude/CLAUDE.md

# Or regenerate CLAUDE.md
python3 .claude/scripts/render-template.py \
  -c .claude/project-config.yaml \
  -t .claude/templates/CLAUDE.md.template \
  -o .claude/CLAUDE.md
```

---

### "Sprint context section missing"

**Meaning:** CLAUDE.md needs sprint marker section.

**Solution:**
```bash
# Run framework health check
/vibey manage → Option 5

# Or regenerate CLAUDE.md
/vibey manage → Option 4 (Regenerate CLAUDE.md)
```

---

### "Framework version unknown"

**Meaning:** .vibey-initialized marker missing or invalid.

**Solution:**
```bash
# Recreate marker
touch .claude/.vibey-initialized
echo "Deployed: $(date)" > .claude/.vibey-initialized
echo "Version: 1.2.0" >> .claude/.vibey-initialized
```

---

## Getting Help

### Diagnostic Information

When asking for help, provide:

```bash
# 1. Version info
python3 .claude/scripts/check-version.py --version

# 2. Health check results
# /vibey manage → Option 5

# 3. Python version
python3 --version

# 4. Dependencies
python3 -c "import yaml; print('PyYAML:', yaml.__version__)"
python3 -c "import jinja2; print('Jinja2:', jinja2.__version__)"

# 5. Framework state
ls -la .claude/.vibey-initialized
cat .claude/.vibey-initialized

# 6. Error messages (copy exact text)
```

---

### Resources

- **Documentation:** `.claude/docs/` - Complete framework docs
- **Quick Start:** `.claude/docs/getting-started/QUICK_START.md`
- **FAQ:** `.claude/docs/FAQ.md`
- **GitHub Issues:** Report bugs or request features
- **Ask Claude:** Claude can explain any component

---

### Debug Mode

**Enable Verbose Logging:**
```bash
# Most scripts support --verbose or -v
python3 .claude/scripts/check-version.py --verbose
python3 .claude/scripts/query-sprint-state.py --state ... --verbose
```

**Check Script Help:**
```bash
python3 .claude/scripts/[script-name].py --help
```

---

## Still Stuck?

If this guide didn't help:

1. **Search Documentation** - Use grep to search all docs
   ```bash
   grep -r "your problem" .claude/docs/
   ```

2. **Ask Claude** - Describe your issue in natural language
   ```
   "I'm getting error X when trying to Y. How do I fix this?"
   ```

3. **Check GitHub Issues** - Someone may have had the same issue

4. **Open New Issue** - Provide diagnostic information above

---

**Last Updated:** 2024-11-05
**Framework Version:** 1.2.0
