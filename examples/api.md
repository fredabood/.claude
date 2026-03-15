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
- Python 3.11+ with type hints on all public APIs
- Black formatter (88 char line length)
- Ruff for linting
- mypy for type checking

### Git Conventions
- Conventional commits: `feat:`, `fix:`, `docs:`
- Branch naming: `feature/<PROJ-123>-description`
- PR required for main, squash merge

### Architecture
- FastAPI with async endpoints
- PostgreSQL via SQLAlchemy 2.0 (async)
- Redis for caching and rate limiting
- Alembic for migrations
- Deployed on AWS ECS Fargate

### Testing
- pytest with pytest-asyncio
- httpx for API endpoint testing
- Target: 90% coverage, 100% on auth/payment paths
- Integration tests use test database (not mocks)

## Current Focus

- Sprint goal: API v2 with pagination and filtering
- Active: API-12 (cursor pagination), API-13 (field filtering)
- Next: API-15 (rate limiting per API key)
