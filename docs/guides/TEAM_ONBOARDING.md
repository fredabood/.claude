# Team Onboarding Guide

This guide covers how to onboard new team members to a project using Vibey's roadmap system with signed activity logs.

## Overview

When a project has signing enabled, team members must be authorized before they can make roadmap changes. This ensures every change can be attributed to a known team member.

## For New Team Members

### Step 1: Install Vibey

```bash
pip install vibey
```

Or if using the development version:
```bash
pip install -e /path/to/vibey
```

### Step 2: Generate Your Keypair

Run the auth setup command:

```bash
vibey auth setup
```

You'll be prompted for:
- **Email address:** Use your work email (matches Git config)
- **Name:** Your full name

This creates:
- `~/.vibey/private.key` - Your private key (keep secret!)
- `~/.vibey/public.key` - Your public key
- `~/.vibey/identity.txt` - Your identity info

### Step 3: Export Your Public Key

```bash
vibey auth export
```

Output:
```
Your public key:
vibey-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGBLkT... your@email.com

Share this with a project owner to be authorized.
```

Copy the entire `vibey-ed25519 ...` line.

### Step 4: Send to Project Owner

Send your public key to a project owner or admin. They will:
1. Add you to the authorized signers list
2. Commit and push the change
3. Let you know when you're authorized

### Step 5: Verify Authorization

After the owner adds you:

```bash
git pull
vibey auth status
```

You should see:
```
Project Status:
  Signing enabled: Yes
  You are authorized: Yes (developer)
```

### Step 6: Start Making Changes

You can now use all `vibey roadmap` commands. Your changes will be signed automatically.

```bash
# Start a task
vibey roadmap start git-integration-5-task-001

# Complete a task
vibey roadmap complete git-integration-5-task-001

# View roadmap status
vibey roadmap status
```

## For Project Owners/Admins

### Initial Project Setup

If signing isn't enabled yet:

```bash
# 1. Generate your keypair (if not done)
vibey auth setup

# 2. Initialize signing for the project
vibey auth init-project

# 3. Commit the authorized signers
git add .vibey/authorized-signers/
git commit -m "Initialize roadmap signing"
git push
```

### Adding a New Team Member

When a team member sends you their public key:

```bash
# 1. Add them to authorized signers
vibey auth add-signer alice@example.com "Alice Smith" "vibey-ed25519 AAAA..."

# 2. Commit and push
git add .vibey/authorized-signers/
git commit -m "Add Alice Smith to authorized signers"
git push

# 3. Let them know they're authorized
```

### Adding with Specific Role

```bash
# Add as admin (can add/revoke other signers)
vibey auth add-signer bob@example.com "Bob Jones" "vibey-ed25519 AAAA..." --role admin

# Add as developer (default)
vibey auth add-signer carol@example.com "Carol White" "vibey-ed25519 AAAA..." --role developer
```

### Reviewing Signer Additions

When reviewing a PR that adds a new signer:

1. Verify the identity matches the person requesting access
2. Confirm with the person through a second channel (Slack, email)
3. Check the public key format is correct: `vibey-ed25519 <base64> <email>`
4. Approve and merge

### Listing Current Signers

```bash
vibey auth list
```

Output:
```
Authorized Signers:
  owner@example.com (Project Owner) - owner - active
  alice@example.com (Alice Smith) - admin - active
  bob@example.com (Bob Jones) - developer - active
```

### Revoking Access

When a team member leaves or should no longer have access:

```bash
# Revoke their authorization
vibey auth revoke alice@example.com

# Commit and push
git add .vibey/authorized-signers/
git commit -m "Revoke Alice Smith's access"
git push
```

**Important:** This is a soft revocation. Their historical signed entries remain valid. Only new changes will be rejected.

## Troubleshooting

### "Unknown or revoked signer" Error

The team member is not in the authorized signers list.

**Solution:** Have an owner/admin add them:
```bash
vibey auth add-signer their@email.com "Their Name" "vibey-ed25519 THEIR_KEY..."
```

### "Project signing not initialized" Error

Signing hasn't been set up for the project.

**Solution:** A project owner should run:
```bash
vibey auth init-project
```

### Team Member Can't Find Their Public Key

They may have deleted their keypair or are using a different machine.

**Solution:** They should run `vibey auth setup` again (this generates a new keypair) and send the new public key.

### Pre-commit Hook Rejects Commits

The pre-commit hook may reject commits from unauthorized users.

**Solution:**
1. Verify the user is authorized: `vibey auth status`
2. If not authorized, have an owner add them
3. If authorized but still failing, check the activity log exists for their changes

### Email Mismatch

The signer email must match their identity.txt email.

**Solution:** When adding a signer, use the exact email from their `vibey auth export` output.

## Best Practices

### Identity Consistency

Use the same email for:
- Git commits (`git config user.email`)
- Vibey identity (`vibey auth setup`)
- Authorized signers list

### Key Management

1. **Never share private keys** - Each team member has their own
2. **Use separate keys per project** - Not required, but increases isolation
3. **Rotate keys periodically** - Especially when someone leaves
4. **Back up keys securely** - Consider a password manager

### Code Review

When reviewing PRs that add signers:
- Verify identity through a second channel
- Check public key format
- Ensure email matches expected team member

### Offboarding

When someone leaves the team:
1. Revoke their signer access immediately
2. Consider rotating any shared secrets
3. Review any changes they made recently

## Workflow Example

### Day 1: New Developer Joins

```bash
# New developer (Alice)
pip install vibey
vibey auth setup  # Enter: alice@company.com, Alice Smith
vibey auth export  # Send output to project owner

# Project owner (Bob)
vibey auth add-signer alice@company.com "Alice Smith" "vibey-ed25519 AAAA..."
git add .vibey/authorized-signers/
git commit -m "Onboard Alice Smith"
git push
```

### Day 2: Alice Makes Her First Change

```bash
# Alice
git pull  # Get her authorization
vibey auth status  # Verify she's authorized

# Start working on a task
vibey roadmap start my-first-task

# ... do work ...

# Complete the task
vibey roadmap complete my-first-task

# Commit and push
git add .
git commit -m "Complete my first task"
git push
```

### Week 4: Alice Leaves the Team

```bash
# Project owner (Bob)
vibey auth revoke alice@company.com
git add .vibey/authorized-signers/
git commit -m "Offboard Alice Smith"
git push
```

## See Also

- [Key Management Guide](KEY_MANAGEMENT.md) - Detailed key management docs
- [CI Verification Guide](CI_VERIFICATION.md) - CI/CD pipeline setup
- [Roadmap User Guide](ROADMAP_USER_GUIDE.md) - Using the roadmap system
