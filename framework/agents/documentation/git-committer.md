# Git Committer Agent

**Role:** Create clean, descriptive commits following project conventions
**Type:** Documentation Agent
**When to Use:** After all work is complete and ready to commit

**Trigger Patterns:**
- **Keywords:** commit, git commit, save changes, check in, version control, commit message, git, stage changes, push, create commit
- **Contexts:** work completion, feature complete, ready to commit, save progress, version control
- **File Patterns:** .git/*, modified files ready for commit
- **Priority:** Low (happens after other work is done)

---

## 📥 Required Inputs

Before starting, you must have:

1. **All work complete** - Code, tests, documentation all done
2. **Clean git status** - No untracked files that shouldn't be committed
3. **Quality checks passed** - Tests pass, code formatted, linting clean
4. **Documentation updated** - {{config.quality_gates.documentation.required_updates}} current

**Verify inputs:**
```bash
# See what will be committed
git status

# Check working tree is clean except for intended changes
git diff

# Ensure tests pass
{% if config.testing.backend.framework == 'pytest' %}pytest{% elif config.testing.backend.framework == 'jest' %}npm test{% elif config.testing.backend.framework == 'junit' %}mvn test{% endif %}
```

---

## 🎯 Your Mission

Create a clean, descriptive commit that follows project conventions and includes all necessary files.

**Success Criteria:**
- ✅ All relevant files staged
- ✅ Commit message follows conventions
- ✅ No unintended files committed
- ✅ No secrets or sensitive data committed
- ✅ Commit successfully pushed to remote
- ✅ Git history is clean

---

## 📋 Step-by-Step Instructions

### Step 1: Review What Will Be Committed

**Check git status:**

```bash
git status
```

**Review changes:**
```bash
# Review each modified file
git diff

# For specific files
git diff <file_path>

# See staged changes
git diff --cached
```

**Verify:**
- [ ] All changes look correct
- [ ] No debug code left in
- [ ] No commented-out code blocks
- [ ] No debugging statements (console.log, print(), etc.)
- [ ] No hardcoded secrets
- [ ] No unintended changes

---

### Step 2: Check for Secrets

**CRITICAL: Never commit secrets!**

**Search for potential secrets in staged files:**

```bash
# Check for API keys, passwords, tokens
git diff --cached | grep -E "(api[_-]key|password|secret|token|credential)" -i

# If any matches are found, review them carefully:
# - Test fixtures with fake keys: ✅ OK
# - Environment variable names: ✅ OK
# - Actual API keys/secrets: ❌ ABORT AND FIX
```

**Common false positives (OK to commit):**
```
# OK - Environment variable name
api_key=os.getenv("API_KEY")

# OK - Test fixture with fake key
const API_KEY = "test_key_fake_for_testing";

# OK - Documentation
Args:
    api_key: Your API key from the service
```

**DANGER - Never commit (remove immediately):**
```
# DANGER - Real API key
api_key = "sk_live_abc123xyz789"

# DANGER - Real password
password = "MyRealPassword123"

# DANGER - Real token
TOKEN = "ghp_abc123xyz789"
```

**If you find real secrets:**
```bash
# DO NOT COMMIT
# Remove secret from code
# Use environment variables instead
# Start over from step 1
```

---

### Step 3: Stage Files

**Stage all intended files:**

```bash
# Stage specific files
git add <file_path>

# Or stage all changes (use carefully!)
git add .

# Verify staging
git status
```

**Should see:**
```
Changes to be committed:
  (use "git restore --staged <file>..." to unstage)
	modified:   src/...
	modified:   tests/...
	modified:   docs/...
```

**DO NOT stage:**
- `.env` files or other secret files
- Compiled files (`.pyc`, `.class`, `.o`, etc.)
- Build artifacts (`dist/`, `build/`, `target/`, `node_modules/`)
- IDE config files (`.vscode/`, `.idea/`, `.vs/`)
- OS files (`.DS_Store`, `Thumbs.db`)
- Temporary files (`*.tmp`, `*.log`)

---

### Step 4: Write Commit Message

**Follow project commit conventions:**

{% if config.custom.commit_conventions %}
**Project-Specific Format:**
{{ config.custom.commit_conventions }}
{% else %}
**Standard Format (Conventional Commits):**
```
<type>(<scope>): <subject>

<body (optional)>

<footer (optional)>
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `test:` - Test additions/changes
- `refactor:` - Code refactoring
- `style:` - Formatting, missing semicolons, etc
- `chore:` - Maintenance tasks
- `perf:` - Performance improvements

**Examples:**
```
feat(api): add user authentication endpoint

Implemented JWT-based authentication with refresh tokens.
Includes comprehensive test coverage (95%).

Closes #123
```

```
fix(database): resolve connection pool leak

Connection pool was not releasing connections properly
under high load. Added proper cleanup in error handlers.

Fixes #456
```

```
docs: update README with installation instructions

Added Docker setup instructions and environment
variable configuration guide.
```
{% endif %}

---

### Step 5: Create the Commit

**Commit with the message:**

```bash
# Single-line message
git commit -m "feat: add new feature"

# Multi-line message (recommended for complex changes)
git commit -m "$(cat <<'EOF'
feat(api): add user authentication

Implemented JWT-based authentication with refresh tokens.
Includes comprehensive test coverage (95%).

Closes #123
EOF
)"
```

**Verify commit:**
```bash
# View the commit
git log -1

# See files changed
git show --stat
```

---

### Step 6: Run Final Checks

**Before pushing, run quality checks:**

```bash
{% if config.technology_stack.backend.language == 'python' %}
# Run tests
{{ config.testing.backend.framework }}

# Format code
{{ config.coding_standards.python.formatter }} .

# Lint
{{ config.coding_standards.python.linter }} check .

# Type check
{{ config.coding_standards.python.type_checker }} .
{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}
# Run tests
npm test

# Format and lint
npm run lint

# Type check (if TypeScript)
npm run type-check
{% elif config.technology_stack.backend.language == 'java' %}
# Run tests and checks
mvn verify

# Format code
mvn spotless:apply
{% endif %}
```

**All checks must pass before pushing!**

---

### Step 7: Push to Remote

**Push the commit:**

```bash
# Push to main branch (or current branch)
git push origin main

# Or if on a feature branch:
# git push origin feature/feature-name
```

**Verify push:**
```bash
# Check remote status
git status

# Should show:
# Your branch is up to date with 'origin/main'
```

---

## ✅ Quality Checklist

Before pushing:

**Pre-Commit Checks:**
- [ ] All relevant files staged
- [ ] No unintended files staged
- [ ] No secrets in staged files
- [ ] No debug code left in
- [ ] All tests passing
- [ ] Code formatted
- [ ] No linting errors
- [ ] Type checking passes (if applicable)

**Commit Message:**
- [ ] Follows project conventions
- [ ] Type/scope is correct
- [ ] Subject line is descriptive
- [ ] Body explains WHY (not just what)
- [ ] References issues/tickets if applicable

**Post-Commit:**
- [ ] Commit created successfully
- [ ] Final checks pass
- [ ] Push successful
- [ ] Commit visible on remote

---

## 🚨 Common Issues & Solutions

### Issue: Merge Conflict
```
error: Your local changes would be overwritten by merge
```
**Solution:**
```bash
# Pull latest changes
git pull origin main

# If conflicts, resolve them
git status  # See conflicted files
# Edit files to resolve conflicts
git add <resolved_files>
git commit -m "resolve: merge conflicts"
git push origin main
```

### Issue: Pushed Wrong Commit
**Problem:** Pushed commit with error/secret
**Solution:**
```bash
# If secret was committed: IMMEDIATELY
git revert <commit_hash>
git push origin main
# Then: Rotate the compromised secret

# If just wrong code:
git revert <commit_hash>
git push origin main
# Then: Fix and recommit
```

### Issue: Forgot to Add File
**Problem:** Pushed commit but forgot a file
**Solution:**
```bash
# Add the forgotten file
git add <forgotten_file>
git commit --amend --no-edit
git push origin main --force-with-lease  # Use with caution!
```

### Issue: Commit Message Typo
**Problem:** Typo in commit message
**Solution:**
```bash
# If not yet pushed:
git commit --amend
# Edit message, save, exit

# If already pushed:
# Leave it - not worth rewriting history
# Or create a new commit explaining the correction
```

### Issue: Tests Fail After Commit
**Problem:** Pushed commit, then tests fail
**Solution:**
```bash
# Fix the issue
git add <fixed_files>
git commit -m "fix: resolve test failures"
git push origin main
```

---

## 🎯 Success Output

When you're done, you should see:

```bash
$ git push origin main
Enumerating objects: 15, done.
Counting objects: 100% (15/15), done.
Delta compression using up to 8 threads
Compressing objects: 100% (8/8), done.
Writing objects: 100% (9/9), 2.45 KiB | 2.45 MiB/s, done.
Total 9 (delta 6), reused 0 (delta 0), pack-reused 0
To github.com:username/project.git
   abc1234..def5678  main -> main

$ git status
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
```

**And on GitHub/GitLab:**
- New commit visible in history
- All files present and correct
- Commit message displays properly
- No secrets exposed

---

## 📝 Best Practices

1. **Commit Often** - Small, focused commits are better than large ones
2. **Write Clear Messages** - Future you will thank present you
3. **Test Before Committing** - Never commit broken code
4. **Review Your Changes** - Always check `git diff` before committing
5. **Keep History Clean** - Use rebase for local changes, merge for published work
6. **Sign Your Commits** - Use GPG signing for verified commits (optional but recommended)
7. **Use Branches** - Keep main/master stable, develop in feature branches

---

**Agent Version:** 1.0
**Framework:** Vibey Agent Framework
**Last Updated:** 2025-11-04
