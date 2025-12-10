# Key Management Guide

This guide covers Vibey's cryptographic key management system for roadmap integrity. Signed activity log entries provide non-repudiation and authenticity verification for roadmap changes.

## Overview

Vibey uses Ed25519 digital signatures to prove who made each roadmap change. When signing is enabled:

- Every CLI command that modifies roadmap files creates a signed activity log entry
- Signatures can be verified against authorized team members
- The pre-commit hook can reject changes from unauthorized sources

## Quick Start

### Individual Setup

```bash
# Generate your keypair and configure identity
vibey auth setup

# View your public key
vibey auth export
```

### Project Setup (First Signer)

```bash
# Initialize signing for the project
vibey auth init-project

# Commit the authorized signers directory
git add .vibey/authorized-signers/
git commit -m "Initialize roadmap signing"
```

## Commands Reference

### `vibey auth setup`

Generate an Ed25519 keypair and configure your identity.

```bash
$ vibey auth setup
Enter your email address: alice@example.com
Enter your name: Alice Smith

Generating Ed25519 keypair...
Private key saved to: ~/.vibey/private.key (mode 0600)
Public key saved to: ~/.vibey/public.key
Identity saved to: ~/.vibey/identity.txt

Your public key (share this for authorization):
vibey-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGBLkT... alice@example.com
```

**Options:**
- `--force`: Overwrite existing keypair

### `vibey auth status`

Check your key configuration.

```bash
$ vibey auth status
Key Status:
  Private key: ~/.vibey/private.key (exists)
  Public key: ~/.vibey/public.key (exists)
  Identity: alice@example.com (Alice Smith)

Project Status:
  Signing enabled: Yes
  You are authorized: Yes (owner)
```

### `vibey auth export`

Export your public key for sharing with project owners.

```bash
$ vibey auth export
Your public key:
vibey-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGBLkT... alice@example.com

Share this with a project owner to be authorized.
```

### `vibey auth init-project`

Initialize signing for a project. You become the first authorized signer (owner).

```bash
$ vibey auth init-project
Initializing roadmap signing for this project...
Created .vibey/authorized-signers/
Added alice@example.com as owner

Commit and push to enable signed changes.
```

**Prerequisites:**
- You must have run `vibey auth setup` first

### `vibey auth add-signer`

Add an authorized signer to the project.

```bash
$ vibey auth add-signer bob@example.com "Bob Jones" "vibey-ed25519 AAAA..."
Adding authorized signer...
Created .vibey/authorized-signers/bob@example.com.pub
Updated manifest.yaml

Commit and push to authorize bob@example.com.
```

**Options:**
- `--role`: Signer role (owner, admin, developer). Default: developer

### `vibey auth list`

List all authorized signers for the project.

```bash
$ vibey auth list
Authorized Signers:
  alice@example.com (Alice Smith) - owner - active
  bob@example.com (Bob Jones) - developer - active
  carol@example.com (Carol White) - developer - revoked
```

### `vibey auth revoke`

Revoke a signer's authorization.

```bash
$ vibey auth revoke bob@example.com
Revoking authorization for bob@example.com...
Marked bob@example.com as inactive in manifest

Note: This is a soft revocation. Existing signed entries remain valid.
Commit and push to apply revocation.
```

## File Locations

### User Files (not committed)

```
~/.vibey/
  private.key    # Your Ed25519 private key (KEEP SECRET)
  public.key     # Your Ed25519 public key
  identity.txt   # Your identity (email, name)
```

**Important:** Never commit your private key. It should only exist in `~/.vibey/`.

### Project Files (committed)

```
.vibey/authorized-signers/
  manifest.yaml           # Signer metadata
  alice@example.com.pub   # Alice's public key
  bob@example.com.pub     # Bob's public key
```

These files are committed to the repository and reviewed in pull requests.

## Key Rotation

If your private key is compromised or you need to rotate keys:

1. **Generate new keypair:**
   ```bash
   vibey auth setup --force
   ```

2. **Export new public key:**
   ```bash
   vibey auth export
   ```

3. **Have a project owner add your new key:**
   ```bash
   vibey auth add-signer your@email.com "Your Name" "vibey-ed25519 NEW_KEY..."
   ```

4. **Revoke your old key:**
   ```bash
   vibey auth revoke your@email.com
   ```

   Note: If you have the same email for both keys, you'll need to temporarily use a different email for the new key, or have the owner manually update the public key file.

## Security Considerations

### Private Key Protection

- File permissions are set to `0600` (user read/write only)
- Store in `~/.vibey/` which is outside any repository
- Add `~/.vibey/` to your global gitignore if needed
- Never share your private key or add it to a repository

### Trust Model

1. **First Signer:** Self-authorizes (bootstrap)
2. **Subsequent Signers:** Must be added by an existing authorized signer
3. **Review Process:** Public key additions are reviewed in pull requests
4. **Revocation:** Soft revocation via manifest (set `active: false`)

### What Signing Protects Against

| Threat | Protection |
|--------|------------|
| Unauthorized changes | Verification fails for unknown signers |
| Tampering after signing | Signature verification fails |
| Replay attacks | ULID-based event IDs prevent replay |
| Non-repudiation | Can prove who made each change |

### What Signing Does NOT Protect Against

- **Authorized malicious user:** An authorized signer can still make bad changes
- **Compromised machine:** If an attacker has access to your private key
- **Social engineering:** Owner adding an unauthorized person
- **Revoked key reuse:** Historical entries remain valid after revocation

Signing proves *who* made a change, not *whether* the change is correct.

## Verification

### Verify a Single File

```bash
vibey roadmap verify .vibey/roadmap/tasks/01KC2D0JK7READW9KAK1HBX4BF.yaml
```

Output shows signature status:
```
Verified: .vibey/roadmap/tasks/01KC2D0JK7READW9KAK1HBX4BF.yaml
   Command: vibey roadmap complete git-integration-5-task-013
   Time: 2025-12-10T15:30:00.000000+00:00
   Signed by: alice@example.com (verified)
```

### Verify Commits

```bash
vibey roadmap verify-commits origin/main..HEAD
```

### JSON Output

```bash
vibey roadmap verify .vibey/roadmap/tasks/*.yaml --json
```

## Troubleshooting

### "No keypair configured"

Run `vibey auth setup` to generate your keypair.

### "Project signing not initialized"

Run `vibey auth init-project` to initialize signing for the project.

### "Unknown or revoked signer"

The signer is not in the authorized signers list or has been revoked. Contact a project owner to be added.

### "Invalid signature"

The signature doesn't match the activity log entry. This could indicate:
- The entry was tampered with
- The signer's key was changed
- A bug in the signing process

### "Cryptography library not available"

Install the cryptography library:
```bash
pip install cryptography
```

## Disabling Signing

Signing is optional. If you don't want to use it:

1. Don't run `vibey auth init-project`
2. Activity log entries will be created without signatures
3. Verification will still work based on file hashes

To remove signing from an initialized project:
```bash
rm -rf .vibey/authorized-signers/
git add .vibey/
git commit -m "Remove roadmap signing"
```

## Technical Details

### Algorithm

Vibey uses **Ed25519** signatures:
- 32-byte public keys
- 64-byte signatures
- Fast signing and verification
- No padding oracle attacks
- Widely supported (SSH, GPG, libsodium)

### Canonical Serialization

Activity log entries are signed using a canonical (deterministic) serialization:

```python
{
    "id": "evt_...",
    "timestamp": "2025-12-10T15:30:00.000000+00:00",
    "command": "vibey roadmap complete ...",
    "object_type": "task",
    "object_id": "01KC2D0...",
    "changes": [...],  # sorted by field name
    "file_path": ".vibey/roadmap/tasks/...",
    "file_hash_after": "sha256:..."
}
```

This ensures signatures are reproducible across different systems.

### Dependencies

- `cryptography` Python library (PyPI)

## See Also

- [Team Onboarding Guide](TEAM_ONBOARDING.md) - Onboarding new team members
- [CI Verification Guide](CI_VERIFICATION.md) - CI/CD integration
- [Git Integration Guide](GIT_INTEGRATION.md) - Pre-commit hooks
