---
name: sync-homelab
user_invocable: true
description: Regenerate the homelab-services.md service catalog from Caddyfile — keeps Claude primitives in sync with deployed services
---

# /sync-homelab

Regenerate the Service Catalog table in `.claude/rules/homelab-services.md` from the live `internal/caddy/Caddyfile`, then commit the submodule change.

Run this after any Caddyfile addition or removal. Convention: every PR that changes the Caddyfile includes a `/sync-homelab` run before merge.

## Steps

### Step 1: Read the Caddyfile

Read `internal/caddy/Caddyfile`. Parse all `reverse_proxy` directives in the **production** block (`*.dirtydata.studio:80`, not `staging-*.dirtydata.studio:80`).

For each `handle @<name>` block, extract:
- **Hostname:** from the `@<name> host <hostname>` matcher
- **Container:port:** from the `reverse_proxy <container>:<port>` directive
- **Container name:** the part before `:` in the reverse_proxy target

### Step 2: Read current homelab-services.md

Read `.claude/rules/homelab-services.md`. Locate the **Production Services** table (between the `### Production Services` heading and the next `###` heading).

Extract the current service rows to build the existing service map (hostname → row).

### Step 3: Diff

Compare Caddyfile entries against the current table:
- **Added:** services in Caddyfile not in the table
- **Removed:** services in the table not in the Caddyfile
- **No change:** services present in both

If no changes: report "Service catalog is already up to date." and stop.

### Step 4: Update the table

For **added** services: append a new row with:
- Service name: derive from the Caddyfile `@<name>` matcher (title-case)
- Container: container name from `reverse_proxy`
- External URL: the hostname from the matcher
- Internal host:port: `<container>:<port>`
- Purpose: leave as `(add description)` — prompt the user to fill it in
- Access pattern: leave as `(add access pattern)`

For **removed** services: remove the row from the table.

Preserve all other sections (Infrastructure Services, MCP Server Capabilities, Data Store Schemas, Docker/Infrastructure Conventions) unchanged.

### Step 5: Write the updated file

Write the updated `.claude/rules/homelab-services.md`.

### Step 6: Commit in submodule

```bash
cd .claude
git add rules/homelab-services.md
git commit -m "sync: update homelab-services catalog from Caddyfile"
cd ..
git add .claude
git commit -m "sync: update .claude submodule pointer"
```

### Step 7: Report

Output a summary:
```
/sync-homelab complete
  Added: <N> services (<name>, <name>, ...)
  Removed: <N> services (<name>, <name>, ...)
  Unchanged: <N> services
  Commit: <hash>
```

If any added rows have placeholder Purpose/Access pattern, list them and remind the user to fill them in.

## Notes

- Only parse the production block — ignore the `staging-*.dirtydata.studio:80` block
- The `health` subdomain (`health.dirtydata.studio`) is a health check, not a service — skip it
- The `api` subdomain is the API gateway — it has its own section, don't add it to the service table
- Do not modify the Infrastructure Services table — those are manually maintained
