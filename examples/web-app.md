# Project Instructions

## Jira Workflow

**CloudId**: `your-cloud-id-here`

### Starting a task
```
transitionJiraIssue(cloudId, issueIdOrKey, transition: { id: "21" })
```

### Completing a task
1. Add summary comment
2. `transitionJiraIssue(cloudId, issueIdOrKey, transition: { id: "31" })`

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

### Code Style
- TypeScript with strict mode
- ESLint + Prettier (run `npm run lint`)
- React functional components with hooks
- CSS Modules for styling

### Git Conventions
- Conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`
- Branch naming: `feature/<PROJ-123>-short-description`
- Squash merge to main

### Architecture
- Next.js 14 with App Router
- PostgreSQL via Prisma ORM
- Redis for session cache
- Deployed on Vercel (frontend) + Railway (API)

### Testing
- Jest + React Testing Library for components
- Playwright for E2E
- Target: 90% coverage on business logic

## Current Focus

- Sprint goal: User authentication and profile management
- Active: PROJ-45 (OAuth integration), PROJ-46 (profile page)
- Blocked: PROJ-47 (waiting on design assets)
