# Project Instructions

## Jira Workflow

**CloudId**: `3dfe4da3-9247-4090-bf57-0ad95e8ddadb`

### Starting a task
```
transitionJiraIssue(cloudId, issueIdOrKey, transition: { id: "21" })
```

### During work
Add comments on significant milestones, blockers, or design decisions.

### Completing a task
1. Add summary comment
2. `transitionJiraIssue(cloudId, issueIdOrKey, transition: { id: "31" })`

### Epic completion
Only close epics after all child tasks are done:
```
searchJiraIssuesUsingJql(cloudId, "parent = <epic-key> AND status != Done")
```

## Available Skills

| Command | Purpose |
|---------|---------|
| `/start-task <KEY>` | Start Jira ticket |
| `/complete-task <KEY>` | Complete Jira ticket with quality gates |
| `/status` | Sprint overview |
| `/implement-feature` | 7-step dev lifecycle |
| `/plan-sprint` | Sprint planning |
| `/handoff` | Session summary |
| `/discovery` | Codebase analysis |

## Project Conventions

### Structure
- `stacks/` — Docker Compose stacks for services
- `internal/` — Infrastructure config and scripts
- `submodules/` — Git submodules for related projects
- `docs/` — Documentation

### Git Conventions
- Descriptive commits referencing what changed and why
- Main branch is source of truth
- Submodule pointers updated as needed

### Infrastructure
- Docker Compose for service orchestration
- Cloudflare for DNS and tunnels
- Proxmox for VM management
- Self-hosted services on home server

## Current Focus

- Active infrastructure improvements
- Service consolidation and monitoring
