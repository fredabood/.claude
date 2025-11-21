# Pre-Commit Validation Hooks

**Created:** 2025-11-21
**Sprint:** roadmap-integrity-fixes-6
**Task:** roadmap-integrity-fixes-6-task-005
**Status:** ✅ Production Ready

---

## Overview

The Vibey pre-commit hook automatically validates roadmap data before allowing commits. This prevents corrupted or invalid data from being committed to the repository, maintaining roadmap integrity at the source control level.

### Key Features

- ✅ **Automatic Validation** - Runs when `.vibey/roadmap/` files are modified
- ✅ **Fast Performance** - Quick syntax validation (<1s for 470 files)
- ✅ **Optional Advanced Checks** - Enable comprehensive validation via environment variable
- ✅ **Emergency Bypass** - Use `--no-verify` when needed
- ✅ **Easy Installation** - One command to install/uninstall
- ✅ **Non-Intrusive** - Only runs when roadmap files change

---

## Installation

### Install Hook

```bash
# Install the pre-commit hook
vibey roadmap install-hooks

# Force install (overwrites existing hook)
vibey roadmap install-hooks --force
```

**Output:**
```
Installing Vibey pre-commit hook...

✅ Pre-commit hook installed successfully at /path/to/.git/hooks/pre-commit

ℹ️  Configuration:
  - Hook runs when .vibey/roadmap/ files are modified
  - Set VIBEY_HOOK_ADVANCED=true to enable advanced validation
  - Bypass with: git commit --no-verify (emergency only)
```

### Check Installation Status

```bash
vibey roadmap check-hooks
```

**Output:**
```
Git Hook Status
======================================================================

Git directory: /path/to/repo/.git
Hooks directory exists: ✅

Pre-commit hook: /path/to/repo/.git/hooks/pre-commit
  Is Vibey hook: ✅
  Is executable: ✅

✅ Vibey pre-commit hook is installed and active

Configuration:
  - VIBEY_HOOK_ADVANCED: Set to 'true' to enable advanced validation
  - Bypass: git commit --no-verify
```

### Uninstall Hook

```bash
vibey roadmap uninstall-hooks
```

---

## How It Works

### Validation Flow

```
User runs: git commit
    ↓
Pre-commit hook detects roadmap file changes
    ↓
YES: Run fast validation (YAML syntax, basic checks)
    ↓
Validation passes?
    ↓
YES: Allow commit → Commit succeeds
NO:  Block commit → Show errors
```

### When Hook Runs

The hook **only runs** when files matching `.vibey/roadmap/**` are staged for commit.

**Examples:**

```bash
# Hook WILL run:
git add .vibey/roadmap/track-1/sprint.yaml
git commit -m "update sprint status"
→ 🔍 Validation runs

# Hook WILL NOT run:
git add README.md
git commit -m "update readme"
→ No validation (no roadmap files changed)
```

---

## Configuration

### Basic Mode (Default)

By default, the hook runs **fast validation** (quick profile):

- YAML syntax checking
- File loading
- ~0.6s for 470 files

### Advanced Mode

Enable comprehensive validation by setting an environment variable:

```bash
# Enable advanced validation
export VIBEY_HOOK_ADVANCED=true

# Now commits will run advanced checks:
# - Circular dependency detection
# - Broken reference detection
# - Progress counter validation
# - Orphaned task detection
```

**Add to shell profile:**
```bash
# ~/.bashrc or ~/.zshrc
export VIBEY_HOOK_ADVANCED=true
```

**Per-commit override:**
```bash
# Just for this commit
VIBEY_HOOK_ADVANCED=true git commit -m "message"
```

---

## Usage Examples

### Normal Workflow

```bash
# 1. Make changes to roadmap
vim .vibey/roadmap/my-track/sprint-1/sprint.yaml

# 2. Stage changes
git add .vibey/roadmap/my-track/sprint-1/sprint.yaml

# 3. Commit (hook runs automatically)
git commit -m "Update sprint status"
```

**Hook Output:**
```
🔍 Roadmap files changed, running validation...

Modified roadmap files:
  - .vibey/roadmap/my-track/sprint-1/sprint.yaml

Running fast validation...

================================================================================
Roadmap Validation Report (QUICK profile)
================================================================================

Files validated: 470
  ✅ Valid: 470
  ❌ Invalid: 0

Duration: 0.63 seconds

✅ Validation PASSED
✅ All roadmap validations passed!

[main abc123] Update sprint status
 1 file changed, 1 insertion(+), 1 deletion(-)
```

### Validation Failure

```bash
# 1. Make invalid change (corrupted YAML)
echo "invalid: yaml: syntax:" >> .vibey/roadmap/track.yaml

# 2. Try to commit
git add .vibey/roadmap/track.yaml
git commit -m "update"
```

**Hook Output:**
```
🔍 Roadmap files changed, running validation...

Modified roadmap files:
  - .vibey/roadmap/track.yaml

Running fast validation...

❌ Validation errors found in track.yaml:
  Line 42: Invalid YAML syntax

❌ Fast validation failed!

Fix the validation errors above before committing.
To bypass this check (emergency only): git commit --no-verify
```

Commit **blocked** - fix errors then retry.

### Emergency Bypass

**Use sparingly - only for emergencies!**

```bash
# Bypass validation (not recommended)
git commit --no-verify -m "emergency fix"
```

**When to use `--no-verify`:**
- ✅ Critical hotfix needed immediately
- ✅ Validation bug blocking valid commit
- ✅ Temporary workaround (fix validation later)

**When NOT to use:**
- ❌ Committing known invalid data
- ❌ Avoiding fixing validation errors
- ❌ Regular workflow

---

## Troubleshooting

### Hook Not Running

**Problem:** Commits succeed without validation

**Solutions:**
```bash
# 1. Check if hook is installed
vibey roadmap check-hooks

# 2. Verify hook is executable
ls -la .git/hooks/pre-commit
# Should show: -rwxr-xr-x

# 3. Make executable if needed
chmod +x .git/hooks/pre-commit

# 4. Reinstall hook
vibey roadmap install-hooks --force
```

### Hook Fails to Find Python

**Problem:** Hook error: `python3: command not found`

**Solutions:**
```bash
# 1. Ensure Python 3 is installed
which python3

# 2. Update PATH in shell profile
export PATH="/usr/local/bin:$PATH"

# 3. Or modify hook to use full path
# Edit .git/hooks/pre-commit:
/usr/local/bin/python3 -m vibey.cli.main roadmap validate-fast
```

### Hook Too Slow

**Problem:** Validation takes too long

**Solutions:**
```bash
# 1. Use quick profile (syntax only)
# This is already the default

# 2. Disable advanced validation if enabled
unset VIBEY_HOOK_ADVANCED

# 3. Use incremental validation (future enhancement)
# Coming in future version
```

### Different Hook Already Installed

**Problem:** Another pre-commit hook exists

**Solutions:**
```bash
# Option 1: Backup and force install
vibey roadmap install-hooks --force
# Existing hook backed up to: pre-commit.backup

# Option 2: Manually merge hooks
# Edit .git/hooks/pre-commit and combine both hooks
```

### Permission Denied

**Problem:** `Permission denied: .git/hooks/pre-commit`

**Solutions:**
```bash
# Fix permissions
chmod +x .git/hooks/pre-commit

# Or reinstall
vibey roadmap install-hooks --force
```

---

## Integration with Workflow

### Team Onboarding

Add to project setup documentation:

```markdown
## Setup Development Environment

1. Clone repository
2. Install dependencies
3. **Install pre-commit hook:**
   ```bash
   vibey roadmap install-hooks
   ```
4. Start development
```

### CI/CD Pipeline

Pre-commit hooks run locally. For CI/CD validation, see [CI_CD_VALIDATION.md](./CI_CD_VALIDATION.md).

**Local (pre-commit):**
- Fast validation before commit
- Catches errors early
- Developer-friendly

**CI/CD (GitHub Actions):**
- Comprehensive validation on push
- Blocks PR merge if invalid
- Team-wide enforcement

### Multiple Hooks

If you have other pre-commit hooks, you can chain them:

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run Vibey validation
/path/to/vibey-pre-commit

# Run other hooks
/path/to/eslint-pre-commit
/path/to/pytest-pre-commit

exit 0
```

Or use a pre-commit hook manager like [pre-commit](https://pre-commit.com/).

---

## Advanced Configuration

### Custom Validation Profile

Edit the hook script (`.git/hooks/pre-commit`) to change validation profile:

```bash
# Default: quick profile
python3 -m vibey.cli.main roadmap validate-fast --profile quick

# Change to standard profile (more thorough)
python3 -m vibey.cli.main roadmap validate-fast --profile standard

# Change to thorough profile (full validation)
python3 -m vibey.cli.main roadmap validate-fast --profile thorough
```

### Selective File Validation

Validate only changed files instead of entire roadmap:

```bash
# In .git/hooks/pre-commit, modify validation command:
python3 -m vibey.cli.main roadmap validate-fast --incremental
```

### Custom Error Messages

Edit `.git/hooks/pre-commit` to customize output:

```bash
# Change error message
echo "❌ Roadmap validation failed!"
echo "📚 See: https://docs.example.com/roadmap-validation"
echo "💬 Contact: #roadmap-help on Slack"
```

---

## Technical Details

### Hook Location

**Source:** `vibey/operations/roadmap/hooks/pre-commit`
**Installed:** `.git/hooks/pre-commit`
**Backup:** `.git/hooks/pre-commit.backup` (if --force used)

### Hook Script

```bash
#!/bin/bash
#
# Vibey Roadmap Pre-Commit Hook
#

set -e

# Check if roadmap files are being committed
roadmap_files_changed=$(git diff --cached --name-only | grep "^.vibey/roadmap/" || true)

if [ -z "$roadmap_files_changed" ]; then
    # No roadmap files changed, skip validation
    exit 0
fi

# Show which files changed
echo ""
echo "🔍 Roadmap files changed, running validation..."
echo "$roadmap_files_changed" | sed 's/^/  - /'
echo ""

# Run fast validation
echo "Running fast validation..."
if python3 -m vibey.cli.main roadmap validate-fast --profile quick; then
    echo "✅ Fast validation passed"
else
    echo "❌ Fast validation failed!"
    echo "Fix the validation errors above before committing."
    echo "To bypass: git commit --no-verify"
    exit 1
fi

# Optional: advanced validation
if [ "$VIBEY_HOOK_ADVANCED" = "true" ]; then
    if python3 -m vibey.cli.main roadmap validate-advanced; then
        echo "✅ Advanced validation passed"
    else
        echo "❌ Advanced validation found issues!"
        exit 1
    fi
fi

echo "✅ All roadmap validations passed!"
exit 0
```

### Exit Codes

- `0` - Validation passed, commit allowed
- `1` - Validation failed, commit blocked

### Performance

| Files | Profile | Duration | Cache Hit |
|-------|---------|----------|-----------|
| 470   | Quick   | ~0.6s    | 0% (cold) |
| 470   | Standard| ~0.6s    | 0% (cold) |
| 470   | Standard| ~0.03s   | 100% (warm) |

---

## Best Practices

### Do's ✅

- ✅ Install hooks immediately after cloning repository
- ✅ Run `vibey roadmap check-hooks` periodically
- ✅ Use fast validation for quick commits
- ✅ Enable advanced validation for critical changes
- ✅ Fix validation errors before committing
- ✅ Test changes locally before pushing

### Don'ts ❌

- ❌ Don't use `--no-verify` routinely
- ❌ Don't commit knowing validation will fail
- ❌ Don't disable hooks permanently
- ❌ Don't ignore validation warnings
- ❌ Don't commit without testing
- ❌ Don't bypass validation to "save time"

### Recommendations

1. **Install for all team members**
   - Add to onboarding checklist
   - Document in CONTRIBUTING.md
   - Verify in code reviews

2. **Monitor hook performance**
   - If slow, investigate which files cause delays
   - Consider incremental validation
   - Optimize validation rules

3. **Keep hooks updated**
   - Reinstall after Vibey framework updates
   - Check for new hook features
   - Review hook script changes

4. **Combine with CI/CD**
   - Local hooks catch errors early
   - CI/CD provides team-wide enforcement
   - Both layers = robust validation

---

## FAQ

**Q: Can I have multiple pre-commit hooks?**
A: Yes, chain them in the pre-commit script or use a hook manager.

**Q: What if I need to commit invalid data temporarily?**
A: Use `--no-verify` but create a follow-up task to fix the data.

**Q: Does the hook work with git GUI tools?**
A: Yes, it works with any tool that honors git hooks (most do).

**Q: Can I customize what gets validated?**
A: Yes, edit `.git/hooks/pre-commit` to change validation commands.

**Q: Will the hook slow down my commits?**
A: No, fast validation completes in <1s. Only runs when roadmap files change.

**Q: What happens if Python is not installed?**
A: Hook will fail. Ensure Python 3.7+ is installed and in PATH.

---

## Related Documentation

- [Advanced Validation](./ADVANCED_VALIDATION_AND_REPAIR.md) - Advanced integrity checks
- [CI/CD Validation](./CI_CD_VALIDATION.md) - GitHub Actions integration
- [Validation Rules](./VALIDATION_RULES.md) - Complete rule reference
- [Troubleshooting](./TROUBLESHOOTING.md) - Common issues and solutions

---

**Version:** 1.0.0
**Last Updated:** 2025-11-21
**Maintainer:** Vibey Framework Team
