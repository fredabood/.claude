# User Personas

**Version:** 1.0
**Last Updated:** 2025-12-12

This document defines the five primary user personas for the Vibey framework. Each persona represents a distinct user type with specific goals, pain points, and feature priorities.

---

## Overview

| Persona | Role | Experience | Primary Goal |
|---------|------|------------|--------------|
| **Nina** (New User) | Software Developer | Beginner | Get started quickly |
| **Alex** (Active Developer) | Full-stack Developer | Intermediate | Daily productivity |
| **Pat** (Project Lead) | Tech Lead | Advanced | Roadmap management |
| **Chris** (Contributor) | Framework Developer | Expert | Framework development |
| **Sam** (Platform Integrator) | Platform Engineer | Expert | MCP/adapter integration |

---

## Persona 1: Nina the New User

### Profile

| Attribute | Value |
|-----------|-------|
| **Role** | Software Developer |
| **Experience Level** | Beginner with Vibey, Intermediate developer |
| **Technical Background** | Python, JavaScript, familiar with CLI tools |
| **Time Investment** | 2-4 hours for initial setup, then as needed |

### Goals

1. Get Vibey installed and configured quickly
2. Understand what Vibey can do for their project
3. See value within the first 30 minutes

### Context

- **Environment:** VS Code, macOS/Linux terminal
- **Team Size:** Solo or small team (2-5)
- **Project Type:** Web application or API

### Pain Points

1. Unclear installation steps
2. Too many options without guidance
3. Can't find "getting started" documentation
4. Overwhelmed by feature complexity

### Success Criteria

- Vibey initialized in under 10 minutes
- First roadmap created and understood
- Can run basic status commands

### Key Questions

- "How do I install Vibey?"
- "What's a track/sprint/task?"
- "Where do I start?"
- "What's the simplest workflow?"

### Feature Priorities

| Priority | Features |
|----------|----------|
| **Must Have** | `init`, `status`, `show`, basic help |
| **Should Have** | `create-track`, `create-sprint` |
| **Nice to Have** | Integrations, advanced features |

---

## Persona 2: Alex the Active Developer

### Profile

| Attribute | Value |
|-----------|-------|
| **Role** | Full-stack Developer |
| **Experience Level** | Intermediate with Vibey |
| **Technical Background** | Multiple languages, CI/CD, agile workflows |
| **Time Investment** | 1-2 hours daily |

### Goals

1. Track daily work efficiently
2. Quickly find context for current tasks
3. Update progress without friction
4. Maintain momentum between sessions

### Context

- **Environment:** IDE with terminal, multiple monitors
- **Team Size:** Small to medium team (3-10)
- **Project Type:** Active development project

### Pain Points

1. Context switching between tasks
2. Forgetting what was in progress
3. Losing track of blockers
4. Manual status updates feel tedious

### Success Criteria

- Resume work instantly each session
- Update task status in <30 seconds
- Always know what's blocked and why

### Key Questions

- "What was I working on?"
- "What's blocking this task?"
- "What should I work on next?"
- "How do I add context to a task?"

### Feature Priorities

| Priority | Features |
|----------|----------|
| **Must Have** | `start`, `complete`, `status`, `context` |
| **Should Have** | `activity`, `show`, `add-context` |
| **Nice to Have** | `auto-progress`, `summarize` |

---

## Persona 3: Pat the Project Lead

### Profile

| Attribute | Value |
|-----------|-------|
| **Role** | Tech Lead / Engineering Manager |
| **Experience Level** | Advanced with Vibey |
| **Technical Background** | Architecture, planning, team coordination |
| **Time Investment** | 3-5 hours weekly for roadmap management |

### Goals

1. Plan and organize work into tracks and sprints
2. Track progress across multiple workstreams
3. Communicate status to stakeholders
4. Identify and resolve blockers early

### Context

- **Environment:** Mixed CLI and potential UI
- **Team Size:** Medium to large (5-20)
- **Project Type:** Multi-track initiatives

### Pain Points

1. Keeping roadmap up to date
2. Progress visibility across tracks
3. Dependency management complexity
4. Reporting overhead

### Success Criteria

- Roadmap reflects reality
- Can generate status reports quickly
- Dependencies are visible and managed
- Team can self-serve progress info

### Key Questions

- "What's the overall progress?"
- "Which sprints are at risk?"
- "What are the cross-track dependencies?"
- "How do I restructure the roadmap?"

### Feature Priorities

| Priority | Features |
|----------|----------|
| **Must Have** | `status`, `create-*`, `show`, `summarize` |
| **Should Have** | `checkpoint`, `validate-*`, `repair` |
| **Nice to Have** | Reports, visualizations, exports |

---

## Persona 4: Chris the Contributor

### Profile

| Attribute | Value |
|-----------|-------|
| **Role** | Open Source Contributor / Framework Developer |
| **Experience Level** | Expert developer, learning Vibey internals |
| **Technical Background** | Python, software architecture, testing |
| **Time Investment** | Variable, project-based |

### Goals

1. Understand framework architecture quickly
2. Make changes without breaking things
3. Follow contribution guidelines
4. Get PRs merged efficiently

### Context

- **Environment:** Full development setup, testing tools
- **Team Size:** Open source community
- **Project Type:** Framework development

### Pain Points

1. Understanding codebase organization
2. Running and writing tests
3. Meeting code quality standards
4. Understanding roadmap/task system

### Success Criteria

- Can navigate codebase confidently
- Tests pass locally before PR
- Understands commit message conventions
- Knows how roadmap relates to code

### Key Questions

- "How is the code organized?"
- "How do I run tests?"
- "What are the coding standards?"
- "How do I link commits to tasks?"

### Feature Priorities

| Priority | Features |
|----------|----------|
| **Must Have** | `validate`, git hooks, tests, CONTRIBUTING.md |
| **Should Have** | `add-commit`, `sync-commits`, `verify-*` |
| **Nice to Have** | Architecture docs, ADRs |

---

## Persona 5: Sam the Platform Integrator

### Profile

| Attribute | Value |
|-----------|-------|
| **Role** | Platform Engineer / Tool Developer |
| **Experience Level** | Expert developer |
| **Technical Background** | APIs, protocols, integrations |
| **Time Investment** | Project-based integration work |

### Goals

1. Connect AI assistant to Vibey via MCP
2. Build custom adapters for their platform
3. Expose roadmap functionality programmatically
4. Extend Vibey for specific needs

### Context

- **Environment:** Multiple platforms, API testing tools
- **Team Size:** Platform team (2-5)
- **Project Type:** Integration/tooling

### Pain Points

1. MCP documentation gaps
2. Unclear adapter interface
3. Testing integrations
4. Versioning and compatibility

### Success Criteria

- MCP connection working
- Can call all relevant tools
- Understand resource/prompt patterns
- Can build custom tools

### Key Questions

- "How do I connect via MCP?"
- "What tools are available?"
- "How do I build an adapter?"
- "What's the resource URI format?"

### Feature Priorities

| Priority | Features |
|----------|----------|
| **Must Have** | MCP server, tools, MCP_REFERENCE.md |
| **Should Have** | `deploy`, `export`, adapter docs |
| **Nice to Have** | Custom tool creation, SDK |

---

## Persona Overlap Matrix

Shows which features are shared across personas:

| Feature | Nina | Alex | Pat | Chris | Sam |
|---------|:----:|:----:|:---:|:-----:|:---:|
| `status` | Y | Y | Y | - | - |
| `show` | Y | Y | Y | - | - |
| `start` | - | Y | - | - | - |
| `complete` | - | Y | - | - | - |
| `create-*` | ? | - | Y | - | - |
| `validate` | - | - | ? | Y | - |
| MCP tools | - | - | - | - | Y |
| git hooks | - | - | - | Y | - |
| `context` | - | Y | - | - | - |
| `summarize` | - | ? | Y | - | - |

**Legend:** Y = Must Have, ? = Should Have, - = Not priority

---

## Journey References

Each persona has a corresponding journey document:

| Persona | Journey Document |
|---------|------------------|
| Nina | [JOURNEY_NEW_USER.md](../journeys/JOURNEY_NEW_USER.md) |
| Alex | [JOURNEY_ACTIVE_DEVELOPER.md](../journeys/JOURNEY_ACTIVE_DEVELOPER.md) |
| Pat | [JOURNEY_PROJECT_LEAD.md](../journeys/JOURNEY_PROJECT_LEAD.md) |
| Chris | [JOURNEY_CONTRIBUTOR.md](../journeys/JOURNEY_CONTRIBUTOR.md) |
| Sam | [JOURNEY_PLATFORM_INTEGRATOR.md](../journeys/JOURNEY_PLATFORM_INTEGRATOR.md) |

---

## Using These Personas

### For Documentation

When writing documentation, ask:
- "Which persona(s) is this for?"
- "Does it address their pain points?"
- "Does it answer their key questions?"

### For Feature Development

When building features, consider:
- "Which personas benefit?"
- "Does it match their priorities?"
- "Does it fit their time investment?"

### For Testing

When testing, verify:
- "Can each persona complete their goals?"
- "Are success criteria achievable?"
- "Are pain points addressed?"
