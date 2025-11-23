---
id: sprint-planning
name: Sprint Planning & Roadmap Management
type: planning
version: 1.0.0
duration: 3-5 days (ongoing sprints) | 20-40 minutes (first sprint with framework
  initialization)
complexity: medium
steps:
- order: 1
  name: Analyze Current State (Day 1)
  agent: sprint-planning-agent
  duration: 0.5 days
- order: 2
  name: Collect Sprint Requirements (Day 1)
  agent: sprint-planning-agent
  duration: 0.5 days
- order: 3
  name: Research New Technologies/APIs (Day 2) [OPTIONAL]
  agent: researcher
  duration: 1 day (skip if no new tech)
- order: 4
  name: Review Technical Feasibility & Architecture (Day 2-3)
  agent: '{%-if-config.architecture-%}{{-config.architecture.specialist-}}{%-else-%}architecture-specialist{%-endif-%}'
  duration: 1 day
- order: 5
  name: Create Dependency Graph & Prioritization (Day 3-4)
  agent: sprint-planning-agent
  duration: 1 day
- order: 6
  name: Sequence Sprints & Create Sprint Plan (Day 4)
  agent: sprint-planning-agent
  duration: 1 day
- order: 7
  name: Update ROADMAP.md (Day 5)
  agent: sprint-planning-agent
  duration: 0.5 days
- order: 8
  name: Update .claude/CLAUDE.md (Day 5)
  agent: documentation-engineer
  duration: 0.5 days
- order: 9
  name: Commit Roadmap & Sprint Plan (Day 5)
  agent: git-committer
  duration: 0.5 days
inputs:
- name: feature_name
  type: string
  required: true
  description: Name of the feature or task
- name: requirements
  type: string
  required: true
  description: Requirements and acceptance criteria
- name: project_type
  type: string
  required: false
  default: web-app
  description: Project type (web-app, api, ml, data-platform)
description: Orchestrate sprint planning, prioritization, dependency analysis, and
  roadmap updates
---

# Workflow: Sprint Planning & Roadmap Management

**Workflow ID:** Sprint Planning
**Purpose:** Orchestrate sprint planning, prioritization, dependency analysis, and roadmap updates
**Duration:** 3-5 days (ongoing sprints) | 20-40 minutes (first sprint with framework initialization)
**Complexity:** Medium

---

## Overview

This workflow orchestrates comprehensive sprint planning: requirements gathering → research → architecture review → dependency analysis → prioritization → sprint plan creation → roadmap updates. Ensures Sprint Planning Agent, Researcher, {% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architecture Specialist{% endif %}, Documentation Engineer, and Git Committer work together to create well-structured sprint plans.

**Use Cases:**
- **First sprint in a new project** (combined with framework initialization via `/vibey`)
- New sprint planning (quarterly, monthly, weekly)
- Roadmap reprioritization
- Multi-sprint dependency sequencing
- Feature feasibility assessment

**Prerequisites:**

**For first sprint:**
- None! Run `/vibey` command in Claude Code to initialize framework and plan first sprint simultaneously
- Framework initialization workflow handles: project discovery → config generation → .claude/CLAUDE.md creation → first sprint planning

**For subsequent sprints:**
- Current project state documented (CLAUDE.md)
- Existing roadmap ({% if config.custom.roadmap_location %}{{ config.custom.roadmap_location }}{% else %}docs/sprints/ROADMAP.md{% endif %})
- Stakeholder requirements available

---

## ⚠️ First Sprint? Use `/vibey` Instead

**If this is your first sprint in a new project, DO NOT follow this workflow directly.**

Instead:
1. Run `/vibey` command in Claude Code
2. Framework initialization workflow will:
   - Discover project details conversationally
   - Generate .claude/project-config.yaml
   - Create .claude/CLAUDE.md
   - Set up directory structure
   - **Plan your first sprint** (integrated into initialization)
3. After `/vibey` completes, you'll have Sprint 1 plan ready

**This workflow below is for Sprint 2+** when framework is already initialized.

---

## Workflow Steps

### Step 1: Analyze Current State (Day 1)
**Agent:** Sprint Planning Agent
**Duration:** 0.5 days
**Input:** .claude/CLAUDE.md, {% if config.custom.roadmap_location %}{{ config.custom.roadmap_location }}{% else %}docs/sprints/ROADMAP.md{% endif %}, project status
**Output:** Current state analysis

**Activities:**
- Read .claude/CLAUDE.md for latest project state
- Review ROADMAP.md for completed vs incomplete sprints
- Assess technical debt and blockers
- Review recent retrospectives for lessons learned
- Identify constraints (budget, timeline, resources)

**Deliverables:**
- Current state summary
- Completed sprint analysis
- Technical debt inventory
- Resource availability assessment

**Handoff:** Pass current state to Sprint Planning Agent (requirements phase)

---

### Step 2: Collect Sprint Requirements (Day 1)
**Agent:** Sprint Planning Agent
**Duration:** 0.5 days
**Input:** Current state analysis, stakeholder input
**Output:** Sprint requirements list

**Activities:**
- Gather stakeholder requirements (features, bugs, tech debt)
- Document business objectives and success criteria
- Identify compliance requirements
- Collect user feedback and pain points
- Document "must-have" vs "nice-to-have"

**Deliverables:**
- Sprint requirements list (ranked by stakeholder priority)
- Business objectives
- Success metrics
- Compliance requirements

**Handoff:** Pass requirements to Researcher (if new technologies needed)

---

### Step 3: Research New Technologies/APIs (Day 2) [OPTIONAL]
**Agent:** Researcher
**Duration:** 1 day (skip if no new tech)
**Input:** Sprint requirements mentioning new APIs/technologies
**Output:** Research summary documents

**Activities:**
- Research new API documentation (if new data sources/integrations)
- Create API summaries (authentication, endpoints, rate limits)
- Research new technologies (libraries, frameworks, platforms)
- Create code templates for integrations
- Document gotchas and best practices

**Deliverables:**
- Research summary documents
- API quick reference guides
- Code templates
- Technology assessment (pros/cons)

**Handoff:** Pass research summaries to {% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architecture Specialist{% endif %}

---

### Step 4: Review Technical Feasibility & Architecture (Day 2-3)
**Agent:** {% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architecture Specialist{% endif %}
**Duration:** 1 day
**Input:** Sprint requirements, research summaries
**Output:** Architecture feasibility assessment

**Activities:**
- Review technical feasibility of requirements
{% if config.architecture %}- Assess {{ config.architecture.pattern }} architecture implications{% else %}- Assess platform capabilities{% endif %}
- Identify architectural patterns needed
- Estimate infrastructure requirements
- Flag high-risk items
- Recommend alternatives for infeasible items

**Deliverables:**
- Technical feasibility assessment
- Architecture recommendations
- Risk assessment (high/medium/low risk items)
- Infrastructure requirements
- Infeasible items with alternatives

**Handoff:** Pass feasibility assessment to Sprint Planning Agent

---

### Step 5: Create Dependency Graph & Prioritization (Day 3-4)
**Agent:** Sprint Planning Agent
**Duration:** 1 day
**Input:** Requirements, feasibility assessment, research
**Output:** Dependency graph and prioritization matrix

**Activities:**
- Create dependency graph (which tasks depend on others)
- Identify critical path items
- Score requirements by value/effort/risk
- Prioritize using scoring framework
- Identify parallel vs sequential work streams
- Estimate duration per requirement

**Deliverables:**
- Dependency graph (visual diagram)
- Prioritization scoring matrix
- Critical path analysis
- Duration estimates
- Parallel work stream identification

**Handoff:** Pass dependency analysis to Sprint Planning Agent (sprint creation)

---

### Step 6: Sequence Sprints & Create Sprint Plan (Day 4)
**Agent:** Sprint Planning Agent
**Duration:** 1 day
**Input:** Dependency graph, prioritization matrix
**Output:** Sprint Plan Document

**Activities:**
- Sequence requirements into sprint phases
- Assign requirements to weeks/phases
- Define sprint milestones
- Create detailed sprint plan document
- Document success criteria per phase
- Identify risks and mitigation strategies
- Define sprint retrospective schedule

**Deliverables:**
- **Sprint Plan Document** (`docs/sprints/v{X}.{Y}/sprint-plan-v{X}.{Y}.md`)
- Sprint phase breakdown
- Week-by-week task assignments
- Milestone definitions
- Risk register

**Handoff:** Pass Sprint Plan to Sprint Planning Agent (roadmap update)

---

### Step 7: Update ROADMAP.md (Day 5)
**Agent:** Sprint Planning Agent
**Duration:** 0.5 days
**Input:** Sprint Plan document
**Output:** Updated {% if config.custom.roadmap_location %}{{ config.custom.roadmap_location }}{% else %}ROADMAP.md{% endif %}

**Activities:**
- Update roadmap with new sprint
- Mark previous sprint as complete
- Update sprint status (planned, in progress, complete)
- Update overall progress percentages
- Add new sprint to sprint list
- Update timeline and milestones

**Deliverables:**
- Updated {% if config.custom.roadmap_location %}{{ config.custom.roadmap_location }}{% else %}ROADMAP.md{% endif %}
- Sprint status updates
- Progress metrics updated
- Timeline adjustments

**Handoff:** Pass ROADMAP updates to Documentation Engineer

---

### Step 8: Update .claude/CLAUDE.md (Day 5)
**Agent:** Documentation Engineer
**Duration:** 0.5 days
**Input:** Sprint Plan, updated ROADMAP
**Output:** Updated .claude/CLAUDE.md

**Activities:**
- Update .claude/CLAUDE.md with new sprint focus
- Document sprint objectives in current focus section
{% if config.project.type == 'data-platform' %}- Update data source counts{% elif config.project.type == 'web-app' %}- Update feature counts{% elif config.project.type == 'api' %}- Update endpoint counts{% else %}- Update component counts{% endif %}
- Update architecture status
- Document any new patterns or approaches

**Deliverables:**
- Updated .claude/CLAUDE.md
- Current focus updated
- Sprint objectives documented
- Architecture updates

**Handoff:** Pass all documentation to Git Committer

---

### Step 9: Commit Roadmap & Sprint Plan (Day 5)
**Agent:** Git Committer
**Duration:** 0.5 days
**Input:** Sprint plan, ROADMAP.md, .claude/CLAUDE.md updates
**Output:** Committed and pushed changes

**Activities:**
- Stage sprint plan documents
- Stage ROADMAP.md updates
- Stage .claude/CLAUDE.md updates
- Create descriptive commit message
- Push to remote repository

**Deliverables:**
- Git commit with sprint planning artifacts
- Updated remote repository

**Completion:** Sprint planning workflow complete

---

## Workflow Diagram

```mermaid
graph LR
    A[Sprint Planning<br/>Analyze State] --> B[Sprint Planning<br/>Requirements]
    B --> C{New Tech<br/>Needed?}
    C -->|Yes| D[Researcher<br/>Research Tech]
    C -->|No| E
    D --> E[{% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architect{% endif %}<br/>Feasibility]
    E --> F[Sprint Planning<br/>Dependencies]
    F --> G[Sprint Planning<br/>Create Plan]
    G --> H[Sprint Planning<br/>Update Roadmap]
    H --> I[Doc Engineer<br/>Update .claude/CLAUDE.md]
    I --> J[Git Committer<br/>Commit & Push]
```

---

## Duration Estimates

| Phase | Agent | Duration | Cumulative |
|-------|-------|----------|------------|
| Analyze Current State | Sprint Planning | 0.5 days | Day 0.5 |
| Collect Requirements | Sprint Planning | 0.5 days | Day 1 |
| Research (optional) | Researcher | 1 day | Day 2 |
| Technical Feasibility | {% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architect{% endif %} | 1 day | Day 3 |
| Dependencies & Priority | Sprint Planning | 1 day | Day 4 |
| Create Sprint Plan | Sprint Planning | 1 day | Day 5 |
| Update ROADMAP | Sprint Planning | 0.5 days | Day 5 |
| Update .claude/CLAUDE.md | Documentation Engineer | 0.5 days | Day 5 |
| Git Commit | Git Committer | 0.5 days | Day 5 |
| **Total** | | **5 days** | **~1 week** |

**Without Research:** 4 days

---

## Success Criteria

### Must Have
- [ ] Current state analyzed
- [ ] Sprint requirements documented
- [ ] Dependency graph created
- [ ] Sprint Plan created with phases and milestones
- [ ] ROADMAP.md updated
- [ ] .claude/CLAUDE.md updated

### Should Have
- [ ] Technical feasibility validated by architecture specialist
- [ ] Research completed for new technologies
- [ ] Prioritization scoring applied
- [ ] Risk mitigation strategies defined

### Nice to Have
- [ ] Visual dependency diagram
- [ ] Resource allocation plan
- [ ] Cost estimates per sprint
- [ ] Retrospective schedule

---

## Prioritization Framework

### Value/Effort/Risk Scoring

**Value Score (1-5):**
- 5: Critical business need, high revenue impact
- 4: Important business need, medium revenue
- 3: Useful feature, improves user experience
- 2: Nice-to-have, low business impact
- 1: Optional, minimal impact

**Effort Score (1-5):**
- 5: >4 weeks, high complexity, many dependencies
- 4: 2-4 weeks, medium-high complexity
- 3: 1-2 weeks, medium complexity
- 2: 3-7 days, low-medium complexity
- 1: <3 days, low complexity, minimal dependencies

**Risk Score (1-5):**
- 5: High technical risk, unproven technology, many unknowns
- 4: Medium-high risk, some unknowns
- 3: Medium risk, mostly known approach
- 2: Low-medium risk, proven patterns
- 1: Low risk, well-understood, minimal dependencies

**Priority Formula:**
```
Priority = (Value × 2) - (Effort + Risk)

High Priority: Score ≥ 5
Medium Priority: Score 2-4
Low Priority: Score ≤ 1
```

**Example:**
- Feature: User authentication system
- Value: 5 (critical business need)
- Effort: 3 (1-2 weeks)
- Risk: 2 (proven patterns available)
- **Priority = (5 × 2) - (3 + 2) = 5 (High Priority)**

---

## Dependency Graph Example

```
Sprint v1.2.0: {% if config.project.type == 'web-app' %}User Authentication & Dashboard{% elif config.project.type == 'api' %}API v2 & Rate Limiting{% elif config.project.type == 'data-platform' %}ETL Pipeline & Analytics{% else %}Core Feature Set{% endif %}

Dependencies:
v1.1.0 (Foundation) → v1.2.0 Phase 1 (Core Feature)
                      ↓
                v1.2.0 Phase 2 (Integration A)
                      ↓
                v1.2.0 Phase 3 (Integration B)
                      ↓
                v1.2.0 Phase 4 (Advanced Features)

Parallel Work:
- Phase 2 & 3 can run in parallel (independent components)
- Phase 4 depends on Phase 1 (core feature must exist)

Critical Path: v1.1.0 → Phase 1 → Phase 4 (8-12 weeks total)
```

---

## Integration with Other Workflows

**Triggers other workflows:**
{% if config.project.type == 'ml' %}- ML Model Development - If ML sprint planned{% endif %}
- Infrastructure Setup - If infrastructure sprint planned
- Feature Development - For feature implementation sprints
- Testing & QA - For all sprints

**Invoked by:**
- Quarterly/monthly planning cycle
- Major pivot or reprioritization event
- Completion of current sprint

---

## Related Documentation

**Agent Instructions:**
- `agents/planning/sprint-planning.md`
- `agents/planning/researcher.md`
{% if config.architecture %}- `agents/architecture/{{ config.architecture.specialist | lower | replace(' ', '-') }}.md`{% endif %}
- `agents/documentation/documentation-engineer.md`

**Templates:**
- Sprint plan template
- Research summary template

---

**Created:** 2025-11-04
**Status:** ✅ Generic
**Version:** 1.0
**Framework:** Vibey Agent Framework
