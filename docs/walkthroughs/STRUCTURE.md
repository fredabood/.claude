# Walkthrough Structure Guide

> Organizing Vibey documentation by **what users want to accomplish** rather than **who they are**.

---

## Rationale

The current persona-based documentation (journeys and walkthroughs by role) has issues:

1. **Redundancy**: The same content appears in multiple personas (e.g., installation in New User AND Contributor)
2. **Search Mismatch**: Users search "how to create a track" not "active developer daily workflow"
3. **Maintenance Burden**: Updates require changes in multiple files
4. **Context Switching**: Users must decide which persona they are before finding help

## New Structure: Action-Oriented Walkthroughs

```
docs/walkthroughs/
├── STRUCTURE.md                  # This file
├── GETTING_STARTED.md            # First 30 minutes - installation to first task
├── DAILY_WORKFLOW.md             # Task management cycle - start, work, complete
├── ROADMAP_MANAGEMENT.md         # Creating/managing tracks, sprints, tasks
├── DEPLOYMENT.md                 # Platform deployment workflows
├── DATABASE_OPERATIONS.md        # DB maintenance, sync, troubleshooting
├── REPORTING_AND_STATUS.md       # Status checks, progress reports, exports
├── EXTENDING_VIBEY.md            # Plugins, adapters, MCP tools, contributing
└── TROUBLESHOOTING.md            # Common issues and solutions
```

---

## Walkthrough Descriptions

### GETTING_STARTED.md
**Purpose**: First successful experience with Vibey
**Target Time**: 30 minutes
**Entry Point**: New users, fresh installs

**Content**:
- Installation (pip, development setup)
- `vibey roadmap init` - first project initialization
- Understanding tracks/sprints/tasks hierarchy
- Creating first track, sprint, and task
- Completing first task
- Where to go next

### DAILY_WORKFLOW.md
**Purpose**: The core daily development cycle
**Target Time**: Reference document (10-15 min read)
**Entry Point**: Regular users working on tasks

**Content**:
- Session start: `vibey roadmap status`, context review
- Task selection: reviewing available tasks, checking blockers
- Starting work: `vibey roadmap start <task-id>`
- During work: viewing details, adding context
- Completing work: `vibey roadmap complete <task-id>`
- Session end: checkpoints, planning next session
- Integration with git workflow

### ROADMAP_MANAGEMENT.md
**Purpose**: Creating and organizing work
**Target Time**: 20-30 minutes
**Entry Point**: Team leads, project setup

**Content**:
- Creating tracks: `vibey roadmap create track`
- Creating sprints: `vibey roadmap create sprint`
- Creating tasks: `vibey roadmap create task`
- Updating items: `vibey roadmap update`
- Dependencies and blockers
- Bulk operations
- Standards and conventions

### DEPLOYMENT.md
**Purpose**: Deploying to AI platforms
**Target Time**: 15-20 minutes per platform
**Entry Point**: Users integrating with Claude, Cursor, etc.

**Content**:
- Platform overview (9 supported platforms)
- Pre-deployment audit: `vibey deploy audit`
- Deploying: `vibey deploy run --platform <name>`
- Platform-specific guides:
  - Claude Code
  - Cursor
  - VS Code/Copilot
  - Continue
  - Windsurf
  - Goose
  - Aider
  - Gemini
  - Replit

### DATABASE_OPERATIONS.md
**Purpose**: Database maintenance and troubleshooting
**Target Time**: 10-15 minutes
**Entry Point**: Users with sync issues, advanced users

**Content**:
- Understanding YAML + SQLite dual storage
- `vibey roadmap db status` - checking sync state
- `vibey roadmap db rebuild` - regenerating from YAML
- `vibey roadmap db validate` - checking integrity
- `vibey roadmap db vacuum` - optimizing
- Common issues and resolution

### REPORTING_AND_STATUS.md
**Purpose**: Visibility into project progress
**Target Time**: 15-20 minutes
**Entry Point**: Team leads, stakeholders

**Content**:
- Quick status: `vibey roadmap status`
- Detailed views: `vibey roadmap show`
- Listing items: `vibey roadmap status` and `vibey roadmap show`
- Activity tracking: `vibey roadmap activity`
- Summaries: `vibey roadmap summarize`
- Exporting data: `vibey roadmap export`
- Checkpoints: `vibey roadmap checkpoint`

### EXTENDING_VIBEY.md
**Purpose**: Customization and contribution
**Target Time**: 30-60 minutes
**Entry Point**: Advanced users, contributors

**Content**:
- Platform adapter development
- MCP tool creation
- Recipe development
- Plugin architecture
- Contributing code (links to CONTRIBUTING.md)
- Development setup (links to SETUP.md)
- Code standards (links to CODING_STANDARDS.md)

### TROUBLESHOOTING.md
**Purpose**: Problem resolution
**Target Time**: As needed (reference)
**Entry Point**: Users encountering errors

**Content**:
- Installation issues
- Database sync errors
- Command failures
- Platform deployment issues
- Performance problems
- Getting help (GitHub issues, community)

---

## Migration Mapping

### From Persona Documents to Action Walkthroughs

| Source Document | Source Section | Target Walkthrough | Target Section |
|-----------------|----------------|-------------------|----------------|
| JOURNEY_NEW_USER.md | Discovery & Installation | GETTING_STARTED.md | Installation |
| JOURNEY_NEW_USER.md | First Steps | GETTING_STARTED.md | First Project |
| JOURNEY_NEW_USER.md | Basic Usage | GETTING_STARTED.md | First Task |
| WALKTHROUGH_NEW_USER.md | All | GETTING_STARTED.md | All (merge) |
| JOURNEY_ACTIVE_DEVELOPER.md | Session Start | DAILY_WORKFLOW.md | Session Start |
| JOURNEY_ACTIVE_DEVELOPER.md | Task Selection | DAILY_WORKFLOW.md | Task Selection |
| JOURNEY_ACTIVE_DEVELOPER.md | Work Execution | DAILY_WORKFLOW.md | During Work |
| JOURNEY_ACTIVE_DEVELOPER.md | Progress Update | DAILY_WORKFLOW.md | Completing Work |
| WALKTHROUGH_ACTIVE_DEVELOPER.md | All | DAILY_WORKFLOW.md | All (merge) |
| JOURNEY_PROJECT_LEAD.md | Planning | ROADMAP_MANAGEMENT.md | Creating Items |
| JOURNEY_PROJECT_LEAD.md | Monitoring | REPORTING_AND_STATUS.md | Status Commands |
| JOURNEY_PROJECT_LEAD.md | Reporting | REPORTING_AND_STATUS.md | Exports & Summaries |
| WALKTHROUGH_PROJECT_LEAD.md | All | REPORTING_AND_STATUS.md | All (merge) |
| JOURNEY_CONTRIBUTOR.md | Setup | GETTING_STARTED.md | Dev Setup |
| JOURNEY_CONTRIBUTOR.md | Codebase | EXTENDING_VIBEY.md | Architecture |
| JOURNEY_CONTRIBUTOR.md | First PR | EXTENDING_VIBEY.md | Contributing |
| WALKTHROUGH_CONTRIBUTOR.md | All | EXTENDING_VIBEY.md | All (merge) |
| JOURNEY_PLATFORM_INTEGRATOR.md | Platform Setup | DEPLOYMENT.md | Platform Guides |
| WALKTHROUGH_PLATFORM_INTEGRATOR.md | All | DEPLOYMENT.md | All (merge) |

---

## Persona to Action Mapping

How different users find content in the new structure:

| Persona | Primary Walkthroughs | Secondary |
|---------|---------------------|-----------|
| New User | GETTING_STARTED | DAILY_WORKFLOW |
| Active Developer | DAILY_WORKFLOW | ROADMAP_MANAGEMENT, REPORTING_AND_STATUS |
| Project Lead | ROADMAP_MANAGEMENT, REPORTING_AND_STATUS | DAILY_WORKFLOW |
| Contributor | EXTENDING_VIBEY, GETTING_STARTED | TROUBLESHOOTING |
| Platform Integrator | DEPLOYMENT | GETTING_STARTED |
| Plugin Developer | EXTENDING_VIBEY | DATABASE_OPERATIONS |

---

## Documents to Archive After Migration

These files will be moved to `docs/archived/` after consolidation:

### Journey Files (docs/journeys/)
- `JOURNEY_NEW_USER.md` → archived
- `JOURNEY_ACTIVE_DEVELOPER.md` → archived
- `JOURNEY_PROJECT_LEAD.md` → archived
- `JOURNEY_CONTRIBUTOR.md` → archived
- `JOURNEY_PLATFORM_INTEGRATOR.md` → archived
- `COVERAGE_MATRIX.md` → archived (replaced by reference coverage)

### Walkthrough Files (docs/walkthroughs/)
- `WALKTHROUGH_NEW_USER.md` → archived
- `WALKTHROUGH_ACTIVE_DEVELOPER.md` → archived
- `WALKTHROUGH_PROJECT_LEAD.md` → archived
- `WALKTHROUGH_CONTRIBUTOR.md` → archived
- `WALKTHROUGH_PLATFORM_INTEGRATOR.md` → archived
- `WALKTHROUGH_TEMPLATE.md` → keep (useful for creating new walkthroughs)

**Total**: 11 files to archive

---

## Cross-Reference Index

Each walkthrough should include "See Also" links:

| Walkthrough | Links To |
|-------------|----------|
| GETTING_STARTED | DAILY_WORKFLOW, docs/reference/CLI_REFERENCE.md |
| DAILY_WORKFLOW | ROADMAP_MANAGEMENT, REPORTING_AND_STATUS, TROUBLESHOOTING |
| ROADMAP_MANAGEMENT | DAILY_WORKFLOW, docs/reference/CLI_REFERENCE.md |
| DEPLOYMENT | GETTING_STARTED, docs/guides/*.md (platform guides) |
| DATABASE_OPERATIONS | TROUBLESHOOTING, docs/architecture/adr/0003-dual-storage.md |
| REPORTING_AND_STATUS | DAILY_WORKFLOW, ROADMAP_MANAGEMENT |
| EXTENDING_VIBEY | CONTRIBUTING.md, SETUP.md, CODING_STANDARDS.md |
| TROUBLESHOOTING | DATABASE_OPERATIONS, GitHub Issues |

---

## Implementation Plan

### Phase 1: Structure Setup (Task 1 - This Task)
- [x] Create STRUCTURE.md (this document)
- [x] Define new walkthrough files
- [x] Create migration mapping
- [x] Identify files to archive

### Phase 2: Content Audit (Tasks 2-3)
- [ ] Audit architectural concept coverage
- [ ] Audit CLI/MCP command coverage
- [ ] Create coverage matrices

### Phase 3: Content Creation (Tasks 4-6)
- [ ] Create user-facing architecture overview
- [ ] Consolidate persona content into new walkthroughs
- [ ] Ensure 100% command coverage

### Phase 4: Refinement (Tasks 7-17)
- [ ] Add MCP integration sections
- [ ] Test all code examples
- [ ] Archive old files

---

## Success Metrics

- **Discoverability**: Users find answers in <2 clicks from docs root
- **Coverage**: 100% of CLI commands documented in context
- **Freshness**: All code examples tested and current
- **Maintainability**: Each concept documented in exactly one place
