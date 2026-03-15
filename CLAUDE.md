# Project Instructions

<!-- Vibey: Opinionated .claude/ directory for structured AI-assisted development -->
<!-- Customize this file for your project. The sections below are templates. -->

## Jira Workflow

All task tracking uses Jira via the Atlassian MCP tools.

**CloudId**: `YOUR_CLOUD_ID_HERE`

### Starting a task

Before beginning work on a Jira ticket, transition it to "In Progress":
```
transitionJiraIssue(cloudId, issueIdOrKey, transition: { id: "21" })
```

Or use: `/start-task <ISSUE-KEY>`

### During work

Add a comment on the ticket when:
- You hit a significant milestone
- You encounter a blocker or unexpected issue
- You make a design decision that deviates from the ticket description

### Completing a task

1. Add a summary comment describing what was done
2. Transition to "Done":
```
transitionJiraIssue(cloudId, issueIdOrKey, transition: { id: "31" })
```

Or use: `/complete-task <ISSUE-KEY>`

### Epic completion

Only transition an epic to "Done" after confirming all child tasks are done:
```
searchJiraIssuesUsingJql(cloudId, "parent = <epic-key> AND status != Done")
```

## Available Skills

| Command | Purpose |
|---------|---------|
| `/start-task <KEY>` | Start a Jira ticket, transition to In Progress |
| `/complete-task <KEY>` | Run quality gates, transition to Done |
| `/status` | Project overview from Jira |
| `/implement-feature "<desc>"` | 7-step dev lifecycle with quality gates |
| `/plan-sprint` | Sprint planning workflow |
| `/handoff` | Session summary for continuity |
| `/discovery` | Codebase analysis and roadmap |

## Project Conventions

<!-- Fill in your project-specific conventions below -->

### Code Style
- <!-- e.g., "Python: Black formatter, 88 char line length" -->
- <!-- e.g., "TypeScript: ESLint + Prettier" -->

### Git Conventions
- <!-- e.g., "Conventional commits: feat:, fix:, docs:" -->
- <!-- e.g., "Branch naming: feature/<ticket-key>-<description>" -->

### Architecture
- <!-- e.g., "Monorepo with packages/ directory" -->
- <!-- e.g., "FastAPI backend, React frontend" -->

## Current Focus

<!-- Update this section each sprint -->
- <!-- Current sprint goal -->
- <!-- Active tickets -->
