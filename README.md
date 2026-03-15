# Vibey

A deployable `.claude/` directory that gives any project structured AI-assisted development workflows.

Vibey bridges Jira, git, and Claude's context using native Claude Code primitives: skills, subagents, rules, and hooks.

## Deploy

```bash
git clone https://github.com/fredabood/vibey.git your-project/.claude
```

## What's Included

### Skills (`/slash-commands`)

| Command | What it does |
|---------|-------------|
| `/start-task <KEY>` | Transition Jira ticket to In Progress, set working context |
| `/complete-task <KEY>` | Run quality gates, summarize work, transition to Done |
| `/status` | Query Jira for active sprint overview |
| `/implement-feature` | 7-step dev lifecycle: design → implement → test → security → integrate → document → commit |
| `/plan-sprint` | 9-step sprint planning with prioritization framework |
| `/handoff` | Generate session summary for continuity |
| `/discovery` | Codebase analysis: structure, tech stack, quality, security, roadmap |

### Subagents (auto-delegated)

Claude automatically delegates to these specialists based on task context:

| Agent | Triggers on |
|-------|------------|
| Security Reviewer | Security review, vulnerability assessment, auth code |
| Test Engineer | Writing tests, coverage improvement, test failures |
| Performance Reviewer | Optimization, slow queries, profiling, benchmarking |
| Observability Reviewer | Logging audit, monitoring, production readiness |
| Code Reviewer | Code review, PR review, refactoring assessment |
| Architecture Reviewer | System design, ADRs, scalability assessment |

### Rules (path-scoped)

| Rule | Applies to |
|------|-----------|
| Security | `**/auth/**`, `**/*password*`, `**/*token*` |
| Testing | `**/*.test.*`, `**/tests/**`, `**/test_*` |

### Hooks (quality gates)

| Hook | Trigger | Behavior |
|------|---------|----------|
| Pre-commit tests | `git commit` | Runs test suite; blocks commit on failure |
| Jira ticket check | `git commit` (async) | Warns if commit message lacks ticket reference |

## Structure

```
your-project/.claude/
├── settings.json              # Hook configuration
├── skills/                    # 7 user-invocable /slash-commands
│   ├── start-task/
│   ├── complete-task/
│   ├── status/
│   ├── implement-feature/
│   ├── plan-sprint/
│   ├── handoff/
│   └── discovery/
├── agents/                    # 6 auto-delegated specialists
│   ├── security-reviewer.md
│   ├── test-engineer.md
│   ├── performance-reviewer.md
│   ├── observability-reviewer.md
│   ├── code-reviewer.md
│   └── architecture-reviewer.md
├── rules/                     # Path-scoped standards
│   ├── security.md
│   └── testing.md
└── hooks/                     # Shell scripts for quality gates
    ├── pre-commit-tests.sh
    └── jira-ticket-check.sh
```

## Customize

- **Add skills:** Create `skills/<name>/SKILL.md` with `user_invocable: true`
- **Add agents:** Create `agents/<name>.md` with a description for auto-delegation
- **Add rules:** Create `rules/<name>.md` with `globs:` for path matching
- **Edit hooks:** Modify `settings.json` and scripts in `hooks/`
