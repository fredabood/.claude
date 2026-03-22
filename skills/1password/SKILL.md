---
name: 1password
user_invocable: true
description: Secure secret access via 1Password CLI — lookup, inject, and run with secrets from the Homelab vault
---

# /1password

Access secrets from the 1Password Homelab vault. All commands use `OP_BIOMETRIC_UNLOCK_ENABLED=true` for desktop app authentication.

## Safety Rules — MANDATORY

1. **Never output full secret values** to the conversation. If you must show a secret, mask it: show only the first 4 and last 4 characters (e.g., `ac6J...COHi`).
2. **Never store secrets in memory files** or vault notes. Secrets belong in 1Password only.
3. **Never log secrets** in Jira comments, git commits, or any persisted artifact.
4. **Use `--fields`** to retrieve only the specific field needed — never dump entire items.
5. **Prefer `op run`** over `op item get` when a command needs a secret — this avoids the secret touching the shell.

## Operations

### Lookup a secret

```bash
OP_BIOMETRIC_UNLOCK_ENABLED=true op item get "<Item Name>" --vault Homelab --fields password
```

Use when: you need a specific secret value for a one-time operation (e.g., manual database connection).

### List vault contents

```bash
OP_BIOMETRIC_UNLOCK_ENABLED=true op item list --vault Homelab
```

Use when: browsing available secrets or verifying an item exists.

### Filter by tag

```bash
OP_BIOMETRIC_UNLOCK_ENABLED=true op item list --vault Homelab --tags database
```

Tags: `database`, `api-key`, `cloud-service`, `vpn`

### Inject secrets into .env

```bash
./internal/scripts/inject-secrets.sh
# or directly:
OP_BIOMETRIC_UNLOCK_ENABLED=true op inject -i .env.tpl -o .env --force
```

Use when: populating `.env` from the template after a fresh clone, secret rotation, or `.env.tpl` change.

### Run a command with secrets

```bash
OP_BIOMETRIC_UNLOCK_ENABLED=true op run --env-file .env.tpl -- docker compose -f stacks/<name>.yml up -d
```

Use when: running a command that needs secrets without writing them to disk. Secrets are injected as environment variables for the subprocess only.

## Item Naming Convention

See `docs/operations/setup/1PASSWORD_VAULT_STRUCTURE.md` for the full item-to-env-var mapping.

## Adding a New Secret

1. Create item: `OP_BIOMETRIC_UNLOCK_ENABLED=true op item create --category password --vault Homelab --title "<Name>" --tags <tag> "password=<value>"`
2. Add `op://Homelab/<Name>/password` reference to `.env.tpl`
3. Update `docs/operations/setup/1PASSWORD_VAULT_STRUCTURE.md` mapping table
4. Run `./internal/scripts/inject-secrets.sh` to regenerate `.env`
