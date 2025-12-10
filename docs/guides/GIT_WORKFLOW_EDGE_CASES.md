# Git Workflow Edge Cases

This guide explains how Vibey's roadmap integrity system handles various Git workflow edge cases.

## Overview

The roadmap integrity system uses **content hashes** (SHA256 of file contents) rather than commit hashes to verify changes. This design makes it robust against most Git operations that rewrite history.

## How Verification Works

When you make a roadmap change via the CLI:

1. CLI writes the change to the YAML file
2. CLI computes SHA256 hash of the new file content
3. CLI logs the hash to the activity log
4. On verify, we compare current file hash against activity log

This content-based approach means the same file content will always verify, regardless of which commit it's in.

## Handled Edge Cases

### Rebases

**Scenario:** You rebase your feature branch onto main.

**What happens:**
- Commits are recreated with new hashes
- File contents remain the same
- Activity log entries still match by content hash
- **Verification passes**

```bash
# Before rebase
git log --oneline
abc1234 feat: Complete task-001
def5678 Initial commit

# After rebase
git rebase main

git log --oneline
newHash feat: Complete task-001  # New commit hash
oldHash Initial commit

# Verification still works - content hash unchanged
vibey roadmap verify-commits main..HEAD
✅ All changes verified
```

### Cherry-picks

**Scenario:** You cherry-pick a roadmap change from another branch.

**What happens:**
- New commit created with same file content
- Content hash matches original activity log entry
- **Verification passes**

```bash
git cherry-pick feature/task-update

# The cherry-picked file has same content
# Activity log entry from original commit still matches
vibey roadmap verify .vibey/roadmap/tasks/01KC...yaml
✅ Verified
```

### Amends

**Scenario:** You amend a commit that includes roadmap changes.

**What happens:**
- If file content unchanged: verification passes
- If file content changed: depends on how it changed

```bash
# Amend without changing roadmap files
git commit --amend -m "Better message"
# ✅ Still verified

# Amend with roadmap file changes
git commit --amend
# ⚠️ If content changed without CLI, bypass detected
```

**Best practice:** If you need to change roadmap files in an amend, use the CLI first:

```bash
# Make changes via CLI
vibey roadmap update task 01KC... --status in_progress

# Now amend safely
git add .vibey/roadmap/
git commit --amend
```

### Force Pushes

**Scenario:** You force push a branch with rewritten history.

**What happens:**
- If file contents unchanged: remote verification passes
- CI verifies by content hash, not commit ancestry

```bash
# Rewrite history locally
git rebase -i HEAD~3

# Force push
git push --force

# CI verification still works
# It checks content hashes, not commit hashes
```

### Merge Conflicts

**Scenario:** You have a merge conflict in a roadmap file.

**Recommended approach:**

1. **Option A: Regenerate via CLI (preferred)**
   ```bash
   # Accept one version
   git checkout --ours .vibey/roadmap/tasks/01KC...yaml
   # Or
   git checkout --theirs .vibey/roadmap/tasks/01KC...yaml

   # Then make the correct change via CLI
   vibey roadmap update task 01KC... --status completed

   # Add and continue merge
   git add .vibey/roadmap/
   git merge --continue
   ```

2. **Option B: Manual merge with awareness**
   ```bash
   # Manually resolve conflict
   vim .vibey/roadmap/tasks/01KC...yaml

   # This will trigger bypass detection
   # but commit will succeed with warning
   git add .vibey/roadmap/
   git merge --continue
   # ⚠️ Warning: Bypass detected
   ```

### Squash Merges

**Scenario:** You squash-merge a PR with multiple roadmap changes.

**What happens:**
- Final file content is what matters
- If final content matches an activity log entry: verified
- Multiple intermediate changes may be lost in history (but final state is verified)

```bash
git merge --squash feature/sprint-work
git commit -m "Complete sprint 5"

# Verification checks final file state
# Activity log entry for final state still matches
```

### Interactive Rebases

**Scenario:** You squash/reorder commits in an interactive rebase.

**What happens:**
- File content hashes are recalculated
- If final content matches activity log: verified
- Squashing multiple CLI changes into one commit works fine

```bash
git rebase -i HEAD~5
# Squash multiple commits

# Each file's final content is verified
# against the activity log
```

## Cases That Trigger Bypass Detection

These scenarios will correctly trigger bypass detection:

### Manual File Edits

```bash
# Editing roadmap files directly
vim .vibey/roadmap/tasks/01KC...yaml
git add .vibey/roadmap/
git commit -m "Manual update"
# ⚠️ Bypass detected
```

**Fix:** Use CLI commands instead:
```bash
vibey roadmap update task 01KC... --status completed
```

### External Tool Modifications

```bash
# Script modifying roadmap files
python scripts/batch-update.py
git add .vibey/roadmap/
git commit
# ⚠️ Bypass detected
```

**Fix:** Use CLI or generate activity log entries programmatically.

### Merge Conflict Manual Resolution

When you manually edit a file to resolve a merge conflict:

```bash
git merge feature
# CONFLICT in .vibey/roadmap/tasks/01KC...yaml
vim .vibey/roadmap/tasks/01KC...yaml  # Manual edit
git add .vibey/roadmap/
git commit
# ⚠️ Bypass detected
```

**Fix:** See "Merge Conflicts" section above.

## CI/CD Considerations

### GitHub Actions

The verification workflow handles edge cases:

```yaml
# Verifies content hashes, not commit ancestry
- run: vibey roadmap verify-commits ${{ github.event.before }}..${{ github.sha }}
```

This works correctly even after:
- Rebases
- Force pushes
- Squash merges

### Pull Request Verification

For PRs, verify the range from base to head:

```yaml
- run: vibey roadmap verify-commits origin/${{ github.base_ref }}..HEAD
```

## Troubleshooting

### "Unverified files" After Rebase

**Symptom:** Files show as unverified after rebasing.

**Cause:** Usually means the file content actually changed during rebase (conflict resolution, manual edit).

**Solution:**
1. Check if content is correct
2. If needed, use CLI to recreate the correct state
3. The new content hash will be logged

### Activity Log Out of Sync

**Symptom:** Activity log entries don't match file hashes.

**Possible causes:**
- Activity log was manually edited
- File was modified outside CLI
- Merge conflict resolution changed content

**Solution:**
```bash
# Check what's in the activity log
cat .vibey/roadmap/activity_log/*.jsonl | grep file_hash

# Check current file hash
sha256sum .vibey/roadmap/tasks/01KC...yaml

# If mismatch, make change via CLI to create correct entry
vibey roadmap update task 01KC... --status <correct-status>
```

### Signed Entries After Rebase

**Symptom:** Signatures don't verify after rebase.

**Cause:** Signatures are based on content, so if content is unchanged, signatures should still verify.

**If signatures fail:**
1. Check if file content actually changed
2. Verify the signer is still authorized
3. Check activity log entry integrity

## Best Practices

1. **Always use CLI for roadmap changes** - This ensures activity log entries are created.

2. **Resolve conflicts carefully** - When resolving merge conflicts in roadmap files, prefer using the CLI to set the final state.

3. **Don't manually edit activity logs** - The activity log should only be written by the CLI.

4. **Review roadmap changes in PRs** - Check that roadmap file changes have corresponding activity log entries.

5. **Use force push with caution** - While verification is robust to force pushes, other team members' work may be affected.

## See Also

- [CI Verification Guide](CI_VERIFICATION.md) - Setting up CI verification
- [Key Management Guide](KEY_MANAGEMENT.md) - Signature verification
- [Roadmap CLI Reference](ROADMAP_CLI_REFERENCE.md) - CLI command reference
