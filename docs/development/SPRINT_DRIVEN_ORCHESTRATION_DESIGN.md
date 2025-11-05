# Sprint-Driven Orchestration System - Design Document

**Version:** 2.0 (Proposed)
**Status:** Design Phase
**Last Updated:** 2025-11-05
**Authors:** Vibey Framework Team

---

## Executive Summary

This document specifies the design for **Sprint-Driven Orchestration**, a simplified replacement for the current three-mode orchestration system (Simple/Balanced/Tiered).

**Core Concept:** Sprint planning generates phase-specific agent orchestration rules, eliminating the need for users to choose orchestration modes while providing adaptive, context-aware agent routing.

**Key Benefits:**
- Eliminates 3 orchestration modes → 1 unified approach
- Context-aware orchestration (adapts to sprint type and phase)
- Removes CLAUDE.md orchestration bloat
- Maintains flexibility for ad-hoc work outside sprints
- Self-documenting execution through sprint retrospectives

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Sprint Context Detection](#sprint-context-detection)
3. [Orchestration Rules Format](#orchestration-rules-format)
4. [Sprint Planning Agent Enhancement](#sprint-planning-agent-enhancement)
5. [Execution Logic](#execution-logic)
6. [Ad-Hoc Mode Specification](#ad-hoc-mode-specification)
7. [Sprint Retrospective Format](#sprint-retrospective-format)
8. [Configuration Changes](#configuration-changes)
9. [CLAUDE.md Template Changes](#claudemd-template-changes)
10. [Migration from Current System](#migration-from-current-system)
11. [Examples](#examples)

---

## 1. Architecture Overview

### 1.1 Two Operating Modes

```
┌─────────────────────────────────────────────────────────────┐
│                  Vibey Agent Framework                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────┐  ┌───────────────────────┐  │
│  │     SPRINT MODE          │  │     AD-HOC MODE       │  │
│  │  (Structured Planning)   │  │   (Flexible Work)     │  │
│  ├──────────────────────────┤  ├───────────────────────┤  │
│  │                          │  │                       │  │
│  │ 1. Sprint Planning       │  │ • Quick bug fixes     │  │
│  │    ├─ Requirements       │  │ • Exploration         │  │
│  │    ├─ Phase Breakdown    │  │ • Research            │  │
│  │    └─ Orchestration      │  │ • Prototyping         │  │
│  │       Design             │  │ • Code review         │  │
│  │                          │  │                       │  │
│  │ 2. Execution             │  │ Characteristics:      │  │
│  │    ├─ Load Phase Rules   │  │ • No sprint required  │  │
│  │    ├─ Follow Agent       │  │ • Agent triggers as   │  │
│  │    │   Orchestration     │  │   suggestions         │  │
│  │    ├─ Run Quality Gates  │  │ • Claude autonomy     │  │
│  │    └─ Update Progress    │  │ • Lightweight         │  │
│  │                          │  │                       │  │
│  │ 3. Retrospective         │  │ No formal structure   │  │
│  │    └─ Document           │  │                       │  │
│  │       Execution          │  │                       │  │
│  │                          │  │                       │  │
│  └──────────────────────────┘  └───────────────────────┘  │
│                                                             │
│  Detection: Sprint markers + user intent + file system     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Mode Selection Logic

```yaml
# Decision Flow
IF sprint_context_detected:
    mode = SPRINT_MODE
    load_phase_orchestration_from_sprint_plan()
ELSE:
    mode = AD_HOC_MODE
    use_agent_triggers_as_suggestions()
```

### 1.3 Key Principles

1. **Planning Precedes Coding** - Knowing what to build enables intelligent orchestration
2. **Context Determines Orchestration** - Security sprint ≠ Feature sprint
3. **Phases Drive Agent Selection** - Research phase ≠ Development phase
4. **Documentation Through Execution** - Retrospectives capture what happened
5. **Flexibility Outside Structure** - Ad-hoc work isn't forced into sprint model

---

## 2. Sprint Context Detection

### 2.1 Detection Mechanisms (Priority Order)

Claude determines mode using multiple detection layers:

#### Layer 1: Explicit Sprint Marker (Highest Priority)

**Location:** `.claude/CLAUDE.md`

```yaml
# Current Sprint Status
current_sprint:
  active: true
  number: 3
  name: "User Authentication System"
  start_date: "2025-11-01"
  phase: "Development Phase 2"
  plan_file: "docs/sprints/sprint-3-plan.md"
  phase_anchor: "## Phase 2: Backend Implementation (Days 4-6)"
```

**Detection Rule:**
```python
if current_sprint.active == true:
    return SPRINT_MODE
```

#### Layer 2: User Intent Keywords

**Sprint Mode Triggers:**
- "continue sprint [N]"
- "work on sprint task [N]"
- "execute phase [N]"
- "start sprint [N]"
- "resume sprint"

**Ad-Hoc Mode Triggers:**
- "quick fix"
- "help me understand"
- "research whether"
- "explore"
- "work outside the sprint"

**Detection Rule:**
```python
if user_message contains sprint_trigger_keywords:
    return SPRINT_MODE
elif user_message contains adhoc_trigger_keywords:
    return AD_HOC_MODE
```

#### Layer 3: File System Detection

**Check for:**
```
docs/sprints/sprint-{N}-plan.md with:
  - status: in-progress
  - current_date within sprint date range
```

**Detection Rule:**
```python
active_sprint_plan = find_active_sprint_plan()
if active_sprint_plan exists:
    return SPRINT_MODE
```

#### Layer 4: Recent Activity

**Git History Analysis:**
```bash
# Check recent commits for sprint references
git log -10 --oneline | grep "sprint-[0-9]"

# Check current branch
git branch --show-current | grep "sprint-[0-9]"
```

**Detection Rule:**
```python
if recent_commits reference sprint OR current_branch contains "sprint":
    return SPRINT_MODE (with confirmation)
```

### 2.2 Detection Implementation in CLAUDE.md

```markdown
## Determining Current Operating Mode

At the start of each session, determine your operating mode:

### Step 1: Check Sprint Marker
Read the "Current Sprint Status" section above.
- If `current_sprint.active: true` → **SPRINT MODE**
- If `current_sprint.active: false` → Continue to Step 2

### Step 2: Check User Intent
Analyze the user's request:
- Sprint keywords ("continue sprint", "sprint task", "execute phase") → **SPRINT MODE**
- Ad-hoc keywords ("quick fix", "explore", "help understand") → **AD-HOC MODE**
- Ambiguous → Continue to Step 3

### Step 3: Check File System
Look for active sprint plan:
```bash
find docs/sprints -name "sprint-*-plan.md" -exec grep -l "status: in-progress" {} \;
```
- If found → **SPRINT MODE** (ask user to confirm)
- If not found → **AD-HOC MODE**

### When in SPRINT MODE:
1. Load current sprint plan: `{current_sprint.plan_file}`
2. Navigate to current phase: `{current_sprint.phase_anchor}`
3. Read orchestration rules for this phase
4. Follow agent orchestration as specified
5. Run quality gates as defined in phase
6. Update sprint progress after completing work

### When in AD-HOC MODE:
1. Use agent triggers as suggestions (not requirements)
2. Make autonomous decisions about agent usage
3. Prioritize speed and flexibility
4. Optional quality gates based on task severity
```

### 2.3 Mode Transition Rules

```yaml
# Transitioning INTO Sprint Mode
triggers:
  - User starts sprint: "Let's plan sprint 4"
  - User resumes sprint: "Continue sprint 3"
  - System detects sprint plan with status: in-progress

actions:
  - Update current_sprint.active: true in CLAUDE.md
  - Load sprint plan
  - Announce: "Entering Sprint Mode - Sprint {N}: {name}"

# Transitioning OUT OF Sprint Mode
triggers:
  - Sprint completed (all phases done + retrospective written)
  - User pauses sprint: "Pause the sprint"
  - User works outside sprint: "Work outside the sprint"

actions:
  - Update current_sprint.active: false in CLAUDE.md
  - Announce: "Entering Ad-Hoc Mode - Flexible operations"
```

---

## 3. Orchestration Rules Format

### 3.1 Location

Orchestration rules are embedded within each phase of the sprint plan:

```
docs/sprints/sprint-{N}-plan.md
  ├─ Phase 1
  │   ├─ Tasks
  │   ├─ Timeline
  │   └─ Orchestration Rules ← HERE
  ├─ Phase 2
  │   ├─ Tasks
  │   ├─ Timeline
  │   └─ Orchestration Rules ← HERE
  └─ Phase N...
```

### 3.2 Orchestration Rules Schema

```yaml
# Within each phase section

orchestration:
  # Agent selection and priority
  agents:
    - name: "Security Reviewer"
      priority: "high"              # high, medium, low
      trigger_conditions:
        - "implementing authentication"
        - "handling sensitive data"
        - "user input validation"
      mode: "mandatory"             # mandatory, recommended, optional
      quality_gate:
        metric: "security_score"
        threshold: 85
        blocking: true              # blocks progression if fails

    - name: "Web Developer"
      priority: "high"
      trigger_conditions:
        - "any development work"
      mode: "mandatory"

    - name: "Test Engineer"
      priority: "medium"
      trigger_conditions:
        - "after implementation"
      mode: "mandatory"
      quality_gate:
        metric: "test_coverage"
        threshold: 90
        blocking: true

    - name: "Documentation Engineer"
      priority: "low"
      trigger_conditions:
        - "API changes"
        - "architecture changes"
      mode: "recommended"

  # Execution sequence
  sequence:
    type: "sequential"              # sequential, parallel, conditional
    order:
      - "Researcher"                # Phase-specific if research needed
      - "Web Developer"
      - "Security Reviewer"
      - "Test Engineer"
      - "Observability Engineer"
      - "Documentation Engineer"
      - "Git Committer"

    # Optional: parallel execution groups
    parallel_groups:
      - ["Security Reviewer", "Test Engineer"]  # Can run simultaneously

  # Quality gates for this phase
  quality_gates:
    required:
      - gate: "security_review"
        threshold: 85
        blocking: true

      - gate: "test_coverage"
        threshold: 90
        blocking: true

      - gate: "logging_audit"
        threshold: 80
        blocking: false           # Warning only

    optional:
      - gate: "performance_check"
        threshold: 90
        blocking: false

  # Phase completion criteria
  completion_criteria:
    - "All mandatory agents have run"
    - "All blocking quality gates passed"
    - "All phase tasks marked complete"
    - "Code committed to git"

  # Context for Claude
  rationale: |
    This phase involves implementing authentication endpoints which are
    security-critical. Security Reviewer runs with high priority before
    and after development. Test Engineer ensures comprehensive test coverage.
    Observability Engineer audits authentication logging (critical for security).
```

### 3.3 Simplified Format (Optional)

For simple phases, use abbreviated format:

```yaml
orchestration:
  agents: ["Web Developer", "Test Engineer", "Documentation Engineer"]
  sequence: "sequential"
  quality_gates:
    - test_coverage: 90
    - security_score: 85
  rationale: "Standard development phase with testing and documentation"
```

### 3.4 Context Window Constraint

**Rule for Sprint Planning Agent:**

```markdown
## Phase Size Constraint

Each phase MUST fit within context window limits:
- **Maximum tokens per phase:** ~8,000 tokens
  - Tasks: ~3,000 tokens
  - Orchestration: ~2,000 tokens
  - Context/rationale: ~2,000 tokens
  - Buffer: ~1,000 tokens

If a phase exceeds this limit:
1. Break into sub-phases (e.g., "Phase 2A", "Phase 2B")
2. Each sub-phase has its own orchestration rules
3. Sub-phases can reference each other for context

Example:
- Phase 2: Backend Implementation (too large)
  ↓
- Phase 2A: Backend - Auth Endpoints
- Phase 2B: Backend - User Management
- Phase 2C: Backend - Database Integration
```

---

## 4. Sprint Planning Agent Enhancement

### 4.1 New Two-Phase Structure

```markdown
# Sprint Planning Agent - Enhanced for Orchestration Design

## Phase 1: Sprint Planning (Existing)
1. Requirements gathering
2. Phase breakdown
3. Task identification
4. Timeline estimation
5. Dependency mapping
6. Risk identification

## Phase 2: Orchestration Design (NEW)
1. Domain analysis per phase
2. Agent selection
3. Sequence design
4. Quality gate definition
5. Orchestration rule generation
6. Integration into sprint plan
```

### 4.2 Orchestration Design Process

```markdown
## Orchestration Design Algorithm

For EACH phase in sprint plan:

### Step 1: Analyze Phase Domains
Examine phase tasks and categorize:

**Security Domain Detection:**
- Keywords: authentication, authorization, permissions, user input,
  sensitive data, encryption, tokens, passwords, API keys
- File patterns: */auth/*, */security/*, *login*, *password*
- Verdict: security_critical = true/false

**Performance Domain Detection:**
- Keywords: optimization, slow, latency, throughput, caching,
  real-time, large dataset, streaming
- File patterns: */performance/*, */optimization/*
- Verdict: performance_critical = true/false

**ML Domain Detection:**
- Keywords: model, training, inference, prediction, ML, AI,
  neural network, dataset, features
- File patterns: */models/*, */ml/*, */training/*
- Verdict: ml_related = true/false

**Infrastructure Domain Detection:**
- Keywords: deployment, scaling, infrastructure, containers,
  kubernetes, terraform, CI/CD
- File patterns: */infrastructure/*, */deploy/*, *.tf
- Verdict: infrastructure_related = true/false

**Documentation Domain Detection:**
- Keywords: API changes, architecture changes, user-facing features,
  breaking changes, deprecation
- Indicators: Public API modifications, user docs needed
- Verdict: documentation_heavy = true/false

### Step 2: Select Agents by Domain

**Security Domain:**
IF security_critical == true:
  - Add: Security Reviewer (priority: high, mode: mandatory)
  - Quality gate: security_score >= 85 (blocking)
  - Sequence: Before development AND after development

**Performance Domain:**
IF performance_critical == true:
  - Add: Performance Engineer (priority: medium, mode: mandatory)
  - Quality gate: performance_score >= 80 (non-blocking)
  - Sequence: After development, before deployment

**ML Domain:**
IF ml_related == true:
  - Add: ML Engineer (priority: high, mode: mandatory)
  - Add: Researcher (priority: high, mode: recommended) if new_ml_technique
  - Quality gate: model_validation (blocking)
  - Sequence: Researcher → ML Engineer → Test Engineer

**Infrastructure Domain:**
IF infrastructure_related == true:
  - Add: (Future) Infrastructure Specialist (priority: high, mode: mandatory)
  - Quality gate: infrastructure_tests (blocking)
  - Sequence: After code changes

**Documentation Domain:**
IF documentation_heavy == true OR api_changes == true:
  - Add: Documentation Engineer (priority: medium, mode: mandatory)
  - Add: Diagram Engineer (priority: low, mode: recommended) if architecture_changes
  - Quality gate: documentation_complete (blocking)
  - Sequence: After implementation

**Always Include:**
- Web Developer / ML Engineer / Backend Engineer (depends on project type)
- Test Engineer (priority: high, mode: mandatory)
- Git Committer (priority: low, mode: mandatory, sequence: last)

### Step 3: Design Sequence

**Standard Sequence Template:**
```
1. Research/Planning Agents (if new technology/patterns)
   - Researcher
   - Architecture Specialist (if architecture changes)

2. Development Agents
   - Web Developer / ML Engineer / Backend Developer
   - (Security Reviewer can be consulted during development)

3. Quality Agents (run after development)
   - Security Reviewer (comprehensive audit)
   - Test Engineer (coverage verification)
   - Performance Engineer (if performance-critical)
   - Observability Engineer (logging audit)

4. Documentation Agents
   - Documentation Engineer
   - Diagram Engineer (if architecture changes)
   - Documentation Maintenance Engineer (if CLAUDE.md needs update)

5. Finalization
   - Git Committer
```

**Sequence Adaptations:**
- **Security-critical:** Security Reviewer runs TWICE (design review + implementation audit)
- **Research-heavy:** Researcher runs FIRST
- **Architecture changes:** Architecture Specialist runs in planning phase
- **Parallel opportunities:** Security + Testing can run simultaneously

### Step 4: Define Quality Gates

**Per Phase, determine required gates:**

```python
quality_gates = []

# Always required
quality_gates.append({
    "gate": "test_coverage",
    "threshold": config.quality_gates.test_coverage_minimum,
    "blocking": true
})

# Conditional based on domain
if security_critical:
    quality_gates.append({
        "gate": "security_review",
        "threshold": config.quality_gates.security_score_minimum,
        "blocking": true
    })

if any_code_changes:
    quality_gates.append({
        "gate": "logging_audit",
        "threshold": config.quality_gates.logging_audit_minimum,
        "blocking": false  # Warning only
    })

if performance_critical:
    quality_gates.append({
        "gate": "performance_check",
        "threshold": 80,
        "blocking": false
    })

if documentation_heavy:
    quality_gates.append({
        "gate": "documentation_complete",
        "threshold": 100,  # Binary: complete or not
        "blocking": true
    })
```

### Step 5: Generate Orchestration Rules

Format rules according to schema (Section 3.2) and embed in phase.

### Step 6: Add Rationale

Explain orchestration decisions:
```markdown
**Orchestration Rationale:**
This phase implements JWT-based authentication which is security-critical.
Security Reviewer runs with high priority at design stage and after
implementation. Test Engineer focuses on auth-specific tests (token validation,
permission checks). Observability Engineer ensures all auth events are logged
(login attempts, failures, token refresh). Documentation Engineer updates
both user guide (how to authenticate) and developer docs (auth endpoints).
```

### Step 7: Validate Phase Size

```python
phase_token_count = estimate_tokens(phase_content + orchestration_rules)

if phase_token_count > 8000:
    # Break into sub-phases
    sub_phases = split_phase(phase, max_tokens=8000)
    for sub_phase in sub_phases:
        generate_orchestration_rules(sub_phase)
```

---

## 5. Execution Logic

### 5.1 Sprint Mode Execution Flow

```markdown
## When User Makes Request During Sprint

### Step 1: Load Current Phase Context
```python
# From CLAUDE.md
sprint_number = current_sprint.number
phase_name = current_sprint.phase
plan_file = current_sprint.plan_file
phase_anchor = current_sprint.phase_anchor

# Load sprint plan
sprint_plan = read_file(plan_file)

# Navigate to current phase
current_phase = extract_section(sprint_plan, phase_anchor)

# Extract orchestration rules
orchestration = parse_orchestration_rules(current_phase)
```

### Step 2: Analyze User Request Against Orchestration

```python
user_request = "Implement login endpoint with JWT tokens"

# Match against trigger conditions
matched_agents = []

for agent in orchestration.agents:
    if matches_trigger_conditions(user_request, agent.trigger_conditions):
        matched_agents.append(agent)

# Sort by priority
matched_agents.sort(by="priority", order="descending")
```

### Step 3: Determine Agent Launch Sequence

```python
# Use predefined sequence from orchestration rules
sequence = orchestration.sequence.order

# Filter sequence to only include matched agents
active_sequence = [agent for agent in sequence if agent in matched_agents]

# Check for parallel opportunities
parallel_groups = orchestration.sequence.parallel_groups
```

### Step 4: Execute Agent Sequence

```python
for agent_name in active_sequence:
    agent_config = get_agent_config(agent_name)

    # Check if mandatory
    if agent_config.mode == "mandatory":
        launch_agent(agent_name, context=user_request)
    elif agent_config.mode == "recommended":
        if user_approves or auto_launch_enabled:
            launch_agent(agent_name, context=user_request)
    elif agent_config.mode == "optional":
        if user_explicitly_requests:
            launch_agent(agent_name, context=user_request)

    # Wait for completion (if sequential)
    if orchestration.sequence.type == "sequential":
        wait_for_agent_completion(agent_name)

    # Collect output for next agent
    agent_output = get_agent_output(agent_name)
    context = merge_context(context, agent_output)
```

### Step 5: Run Quality Gates

```python
for gate in orchestration.quality_gates.required:
    result = run_quality_gate(gate.gate)

    if result.score < gate.threshold:
        if gate.blocking:
            # Block progression
            report_failure(gate, result)
            suggest_remediation(gate, result)
            return BLOCKED
        else:
            # Warning only
            report_warning(gate, result)

# Check completion criteria
if all_criteria_met(orchestration.completion_criteria):
    mark_phase_complete()
    suggest_next_phase()
```

### Step 6: Update Sprint Progress

```python
# Update sprint plan with progress
update_sprint_plan(
    phase=current_phase,
    status="in-progress" or "completed",
    completed_tasks=[...],
    agents_used=[...],
    quality_gate_results=[...]
)

# Update CLAUDE.md if phase completed
if phase_complete:
    next_phase = get_next_phase(sprint_plan)
    update_claude_md(
        current_sprint.phase = next_phase.name,
        current_sprint.phase_anchor = next_phase.anchor
    )
```

### 5.2 Agent Launch Context

When launching agents, provide:

```markdown
## Context for Agent: {agent_name}

**Sprint Context:**
- Sprint: {sprint_number} - {sprint_name}
- Phase: {phase_name}
- Task: {user_request}

**Previous Phase Output:**
{summary_of_previous_phase_work}

**Current Phase Goals:**
{phase_goals_from_sprint_plan}

**Quality Gate Requirements:**
{quality_gates_for_this_agent}

**Your Role:**
{agent_specific_orchestration_instructions}

---

Please proceed with your specialized work.
```

---

## 6. Ad-Hoc Mode Specification

### 6.1 Ad-Hoc Mode Characteristics

```yaml
mode: AD_HOC
description: "Flexible, autonomous operations outside sprint structure"

characteristics:
  - no_sprint_plan_required: true
  - agent_triggers_are_suggestions: true
  - claude_autonomous_decisions: true
  - lightweight_quality_gates: true
  - no_formal_documentation: true

when_to_use:
  - "Quick bug fixes"
  - "Exploratory research"
  - "Code review requests"
  - "Understanding codebase"
  - "Prototyping ideas"
  - "Between sprints"

agent_usage:
  strategy: "trigger-based suggestions"
  description: |
    Agent trigger patterns are available but not enforced.
    Claude makes autonomous decisions about whether to use agents
    based on task complexity, risk, and user preferences.
```

### 6.2 Agent Trigger Patterns (Ad-Hoc Mode)

Each agent still defines trigger patterns for ad-hoc mode:

```markdown
# Security Reviewer Agent

**Trigger Patterns (Ad-Hoc Mode):**
- **Keywords:** security, vulnerability, authentication, authorization,
  OWASP, XSS, SQL injection, CSRF, input validation
- **Contexts:** Reviewing auth code, handling user input, processing sensitive data
- **File Patterns:** */auth/*, */security/*, *login*, *password*, *token*
- **Severity Indicators:** "review", "audit", "secure this"

**Ad-Hoc Usage Guidance:**
- HIGH priority trigger: User explicitly requests security review
- MEDIUM priority trigger: Modifying authentication or authorization code
- LOW priority trigger: General code changes (Claude decides if security relevant)
```

### 6.3 Ad-Hoc Execution Logic

```markdown
## Ad-Hoc Mode Decision Making

When user makes request outside sprint:

### Step 1: Assess Task Complexity
```python
complexity = assess_complexity(user_request)
# Simple: Single file change, no risk
# Medium: Multi-file change, some risk
# Complex: Architecture change, high risk
```

### Step 2: Identify Domains
```python
domains = identify_domains(user_request)
# e.g., ["security", "testing"] if auth-related bug fix
```

### Step 3: Check Agent Triggers
```python
triggered_agents = []

for agent in all_agents:
    if matches_trigger_patterns(user_request, agent.trigger_patterns):
        triggered_agents.append({
            "agent": agent,
            "confidence": calculate_match_confidence(user_request, agent)
        })
```

### Step 4: Autonomous Decision
```python
# Claude decides whether to use agents based on:
decision_factors = {
    "task_complexity": complexity,
    "risk_level": assess_risk(user_request),
    "user_urgency": detect_urgency(user_request),  # "quick fix" = high urgency
    "triggered_agents": triggered_agents,
    "cost_benefit": estimate_agent_overhead_vs_value()
}

# Decision matrix
if complexity == "simple" and risk_level == "low" and urgency == "high":
    # Handle directly, no agents
    use_agents = false

elif complexity == "medium" or risk_level == "medium":
    # Selective agent usage
    use_agents = filter(triggered_agents, confidence > 0.7)

elif complexity == "complex" or risk_level == "high":
    # Use all triggered agents
    use_agents = triggered_agents
    suggest_sprint_planning()  # Complex work should be planned
```

### Step 5: Explain Decision
```markdown
"I'm going to {handle this directly / use Security Reviewer} because:
- Task complexity: {simple/medium/complex}
- Risk level: {low/medium/high}
- {Security-sensitive code / Quick fix / Architecture change}

{If using agents: I'll launch {agent names} to ensure {quality aspect}}"
```

### 6.4 Ad-Hoc Quality Gates

```yaml
quality_gates:
  mode: "optional"
  strategy: "risk-based"

  rules:
    - if: risk_level == "high"
      then: run_quality_gates(["security", "testing"])

    - if: security_sensitive == true
      then: run_quality_gates(["security"])

    - if: complexity == "complex"
      then: suggest("Consider sprint planning for this complexity level")

    - if: risk_level == "low" and urgency == "high"
      then: skip_quality_gates()
```

---

## 7. Sprint Retrospective Format

### 7.1 Purpose

Sprint retrospectives document:
1. What was built
2. How agents were orchestrated
3. Which agents were used
4. Quality gate results
5. What worked / didn't work
6. Learnings for next sprint

### 7.2 Retrospective Template

```markdown
# Sprint {N} Retrospective

**Sprint Name:** {sprint_name}
**Duration:** {start_date} - {end_date} ({X} days)
**Status:** {completed / paused / cancelled}

---

## Sprint Overview

**Goals:**
1. {goal_1}
2. {goal_2}
3. {goal_3}

**Outcome:**
- ✓ {completed_goal_1}
- ✓ {completed_goal_2}
- ✗ {incomplete_goal_3} - Reason: {explanation}

**Key Metrics:**
- Tasks completed: {X} / {Y}
- Code commits: {Z}
- Test coverage: {percent}%
- Quality gates: {X} passed, {Y} failed

---

## Phase Execution Log

### Phase 1: {phase_name}
**Duration:** {X} hours
**Status:** Completed ✓

**Orchestration Executed:**
```yaml
agents_used:
  - name: "Researcher"
    duration: "45 min"
    output: "OAuth 2.0 research document"
    quality: "Excellent - comprehensive analysis"

  - name: "Security Reviewer"
    duration: "30 min"
    output: "Architecture security review"
    quality: "Good - identified 2 design improvements"
    notes: "Recommended using refresh tokens (adopted)"

quality_gates:
  - architecture_review: PASSED
```

**What Worked:**
- Security review at design stage caught issues early
- Researcher provided valuable OAuth insights

**What Didn't Work:**
- N/A

**Adjustments Made:**
- None

---

### Phase 2: {phase_name}
**Duration:** {X} hours
**Status:** Completed ✓

**Orchestration Executed:**
```yaml
agents_used:
  - name: "Web Developer"
    duration: "4 hours"
    output: "Login/register UI, auth endpoints"
    quality: "Excellent"

  - name: "Security Reviewer"
    duration: "1 hour"
    output: "Security audit report"
    quality_gate_score: 88/100
    findings:
      - "Missing rate limiting (fixed)"
      - "Password strength requirements needed (added)"

  - name: "Test Engineer"
    duration: "2 hours"
    output: "47 auth tests added"
    quality_gate_score: 94% coverage
    notes: "Excellent edge case coverage"

quality_gates:
  - security_review: PASSED (88/100, threshold: 85)
  - test_coverage: PASSED (94%, threshold: 90%)
```

**What Worked:**
- Security Reviewer caught rate limiting gap
- Test Engineer added excellent edge case tests

**What Didn't Work:**
- Initial security audit found 2 issues (but caught before deployment)

**Adjustments Made:**
- Added rate limiting middleware
- Implemented password strength validator

---

### Phase 3: {phase_name}
...

---

## Orchestration Effectiveness Analysis

### What Worked Well

1. **Security Reviewer in Multiple Phases**
   - Design review (Phase 1) caught architectural issues
   - Implementation audit (Phase 2) caught security gaps
   - Result: No security issues in production

2. **Test Engineer Emphasis**
   - 94% coverage achieved
   - Edge cases well-covered
   - Result: Confidence in auth system stability

3. **Researcher Early**
   - OAuth research informed design
   - Prevented poor design choices
   - Result: Industry-standard implementation

### What Didn't Work

1. **Missing Performance Engineer**
   - Auth endpoints slower than expected (300ms avg)
   - Should have included Performance Engineer in Phase 3
   - Action: Add to next security-related sprint

2. **Documentation Engineer Too Late**
   - Docs written after implementation
   - Hard to remember design decisions
   - Action: Run Documentation Engineer in parallel with development

### Orchestration Adjustments for Next Sprint

1. **Add Performance Engineer** to quality phase for API-heavy sprints
2. **Run Documentation Engineer in parallel** with development
3. **Keep Security Reviewer in design + implementation** phases (worked well)

---

## Quality Gate Summary

| Gate | Threshold | Result | Status |
|------|-----------|--------|--------|
| Security Review | ≥85 | 88 | ✓ PASS |
| Test Coverage | ≥90% | 94% | ✓ PASS |
| Logging Audit | ≥80 | 85 | ✓ PASS |
| Documentation | Complete | Complete | ✓ PASS |

**Overall:** All quality gates passed ✓

---

## Sprint Statistics

**Time Breakdown:**
- Planning: 2 hours
- Research: 1 hour
- Development: 12 hours
- Quality assurance: 5 hours
- Documentation: 2 hours
- Total: 22 hours

**Agent Usage:**
- Researcher: 1x (1 hour)
- Sprint Planning Agent: 1x (2 hours)
- Security Reviewer: 3x (3 hours total)
- Web Developer: 1x (12 hours)
- Test Engineer: 1x (3 hours)
- Observability Engineer: 1x (1 hour)
- Documentation Engineer: 1x (2 hours)
- Git Committer: 1x (15 min)

**Code Metrics:**
- Files created: 12
- Files modified: 8
- Lines added: 1,247
- Lines removed: 89
- Tests added: 47
- Test coverage: 94%

---

## Key Learnings

1. **Security-critical features benefit from multi-phase security review**
2. **Research phase is valuable for unfamiliar technologies**
3. **Performance should be considered during quality phase**
4. **Documentation during development is better than after**

---

## Recommendations for Next Sprint

1. Include Performance Engineer in quality phase
2. Run Documentation Engineer in parallel with development
3. Continue Security Reviewer in design + implementation phases
4. Consider adding architecture diagrams earlier (helped in this sprint)

---

**Retrospective Completed:** {date}
**Generated by:** Git Committer Agent + Documentation Engineer
```

### 7.3 Retrospective Generation

```markdown
## When to Generate Retrospective

**Trigger:** Sprint completion (all phases done + quality gates passed)

**Process:**
1. Git Committer Agent collects execution data
2. Documentation Engineer formats retrospective
3. Agents collaborate to analyze effectiveness
4. Output saved to: `docs/sprints/sprint-{N}-retrospective.md`

**Automation:**
```yaml
retrospective_generation:
  automated: true
  template: "templates/sprint-retrospective.md.template"
  data_sources:
    - sprint_plan_file
    - git_commit_history
    - quality_gate_results
    - agent_execution_logs

  analysis:
    - what_worked: extract_successes()
    - what_didnt_work: extract_failures()
    - orchestration_effectiveness: analyze_agent_usage()
    - recommendations: generate_recommendations()
```

---

## 8. Configuration Changes

### 8.1 Updated Schema

```yaml
# project-config.yaml (NEW)

framework:
  # REMOVED: orchestration_mode (no longer needed)

  # NEW: Sprint-driven orchestration
  sprint_driven_orchestration:
    enabled: true                    # Enable sprint-driven orchestration
    default: true
    description: "Use sprint planning to generate orchestration rules"

  # Existing settings
  auto_agent_launch: true
  require_quality_gates: true
  version: "2.0"
  config_location: ".claude"

# Rest of config unchanged...
quality_gates: {...}
technology_stack: {...}
coding_standards: {...}
```

### 8.2 Migration from 1.x Config

```python
# Migration script: migrate-config.py

def migrate_config_1x_to_2x(old_config):
    new_config = old_config.copy()

    # Remove orchestration_mode
    if "orchestration_mode" in new_config["framework"]:
        old_mode = new_config["framework"]["orchestration_mode"]
        del new_config["framework"]["orchestration_mode"]

        print(f"Migrated: orchestration_mode '{old_mode}' → sprint_driven_orchestration")

    # Add new field
    new_config["framework"]["sprint_driven_orchestration"] = {
        "enabled": true
    }

    # Update version
    new_config["framework"]["version"] = "2.0"

    return new_config
```

---

## 9. CLAUDE.md Template Changes

### 9.1 Removed Sections

**DELETE:**
- Orchestration mode explanations (Simple/Balanced/Tiered)
- Orchestration rules (keyword matching)
- Coordinator agent invocation logic

### 9.2 New Sections

**ADD:**

```markdown
## Operating Mode Detection

{SEE SECTION 2.2 above for full content}

## Current Sprint Status

```yaml
current_sprint:
  active: false
  number: null
  name: null
  start_date: null
  phase: null
  plan_file: null
  phase_anchor: null
```

(This section is auto-updated by Sprint Planning Agent and Git Committer)

## Sprint Execution Guidelines

### When in Sprint Mode

1. **Load Phase Context**
   - Read: `{current_sprint.plan_file}`
   - Navigate to: `{current_sprint.phase_anchor}`
   - Extract orchestration rules

2. **Follow Orchestration Rules**
   - Launch agents as specified in phase orchestration
   - Respect priority ordering
   - Run mandatory agents always
   - Run recommended agents unless user declines

3. **Execute Quality Gates**
   - Run all required quality gates for phase
   - Block progression if blocking gates fail
   - Report warnings for non-blocking gates

4. **Update Progress**
   - Mark tasks complete as you finish them
   - Update sprint plan with progress
   - Move to next phase when criteria met

### When in Ad-Hoc Mode

1. **Autonomous Operation**
   - Use agent triggers as suggestions
   - Make decisions based on task complexity and risk
   - Prioritize speed and flexibility

2. **Optional Quality Gates**
   - Run quality gates for high-risk changes
   - Skip for low-risk, urgent fixes

3. **No Formal Structure**
   - No sprint plan updates required
   - No retrospective documentation

## Agent Trigger Patterns (Ad-Hoc Mode)

{Consolidated list of all agent trigger patterns for quick reference}

### Security Reviewer
- Keywords: security, vulnerability, auth, OWASP...
- Contexts: Security-sensitive code, user input, sensitive data...

### Web Developer
- Keywords: frontend, UI, component, React...
- Contexts: User interface work, web development...

{etc. for all agents}
```

### 9.3 Template Generation

```python
# scripts/render-template.py enhancement

def render_claude_md_v2(config, sprint_status=None):
    template = load_template("templates/CLAUDE.md.template")

    context = {
        "project": config["project"],
        "technology_stack": config["technology_stack"],
        "quality_gates": config["quality_gates"],

        # NEW: Sprint status
        "current_sprint": sprint_status or {
            "active": false,
            "number": null,
            "name": null,
            ...
        },

        # NEW: Agent trigger patterns
        "agent_triggers": load_all_agent_triggers(),

        # REMOVED: orchestration_mode logic
    }

    return template.render(context)
```

---

## 10. Migration from Current System

### 10.1 Migration Path for Existing Projects

**Phase 1: Update Framework Files**
```bash
# Update Vibey framework
cd /path/to/vibey
git pull origin main

# Run migration script
python3 scripts/migrate-to-v2.py --project-dir /path/to/my-project
```

**Phase 2: Update Project Config**
```bash
# Backup existing config
cp .claude/project-config.yaml .claude/project-config.v1.yaml

# Migrate config
python3 scripts/migrate-config.py \
  -i .claude/project-config.v1.yaml \
  -o .claude/project-config.yaml
```

**Phase 3: Regenerate CLAUDE.md**
```bash
# Regenerate with new template
python3 scripts/render-template.py \
  -c .claude/project-config.yaml \
  -t templates/CLAUDE.md.template \
  -o .claude/CLAUDE.md
```

**Phase 4: Update Active Sprint Plans (if any)**
```bash
# If you have active sprint plans, add orchestration rules
python3 scripts/add-orchestration-to-sprint.py \
  -s docs/sprints/sprint-3-plan.md \
  -c .claude/project-config.yaml
```

### 10.2 Backward Compatibility

**None.** Version 2.0 is a breaking change.

Rationale:
- Vibey has no users yet (per user confirmation)
- Clean architecture is more important than backward compatibility
- Fresh start allows optimal design

### 10.3 Migration Script Specification

```python
# scripts/migrate-to-v2.py

import argparse
import os
from pathlib import Path

def migrate_project_to_v2(project_dir):
    """Migrate a Vibey 1.x project to 2.0."""

    print("Vibey Framework Migration: 1.x → 2.0")
    print("=" * 50)

    # Step 1: Check if project uses Vibey
    if not is_vibey_project(project_dir):
        print("ERROR: Not a Vibey project")
        return False

    # Step 2: Backup existing files
    backup_dir = create_backup(project_dir)
    print(f"✓ Backup created: {backup_dir}")

    # Step 3: Migrate config
    old_config = load_config(f"{project_dir}/.claude/project-config.yaml")
    new_config = migrate_config_1x_to_2x(old_config)
    save_config(f"{project_dir}/.claude/project-config.yaml", new_config)
    print("✓ Config migrated")

    # Step 4: Regenerate CLAUDE.md
    regenerate_claude_md(project_dir, new_config)
    print("✓ CLAUDE.md regenerated")

    # Step 5: Update sprint plans (if any)
    sprint_plans = find_sprint_plans(project_dir)
    if sprint_plans:
        print(f"Found {len(sprint_plans)} sprint plans")
        for plan in sprint_plans:
            add_orchestration_rules(plan, new_config)
        print("✓ Sprint plans updated")

    # Step 6: Remove deprecated files
    remove_deprecated_files(project_dir)
    print("✓ Deprecated files removed")

    print("\n" + "=" * 50)
    print("Migration complete! ✓")
    print(f"\nBackup location: {backup_dir}")
    print("Next steps:")
    print("  1. Review .claude/CLAUDE.md")
    print("  2. Review .claude/project-config.yaml")
    print("  3. Review updated sprint plans (if any)")
    print("  4. Test with: 'Claude, what sprint are we on?'")

    return True

def migrate_config_1x_to_2x(old_config):
    # See Section 8.2 for implementation
    pass

def add_orchestration_rules(sprint_plan_file, config):
    """Add orchestration rules to existing sprint plan."""

    plan = load_sprint_plan(sprint_plan_file)

    # For each phase, generate orchestration rules
    for phase in plan.phases:
        orchestration = generate_orchestration_for_phase(phase, config)
        phase.add_section("orchestration", orchestration)

    save_sprint_plan(sprint_plan_file, plan)
```

---

## 11. Examples

### 11.1 Example: Feature Sprint

```markdown
# Sprint 3 Plan: User Authentication System

**Type:** Feature Development
**Duration:** 9 days
**Status:** in-progress

---

## Phase 1: Research & Architecture (Days 1-2)

### Tasks
1. Research OAuth 2.0 and JWT best practices
2. Design authentication architecture
3. Security review of architecture
4. Document authentication flow

### Timeline
- Start: 2025-11-01
- End: 2025-11-02
- Duration: 2 days

### Orchestration

```yaml
orchestration:
  agents:
    - name: "Researcher"
      priority: "high"
      trigger_conditions:
        - "any research task"
      mode: "mandatory"

    - name: "Security Reviewer"
      priority: "high"
      trigger_conditions:
        - "design review"
        - "architecture review"
      mode: "mandatory"
      quality_gate:
        metric: "architecture_security_review"
        threshold: 85
        blocking: true

    - name: "Diagram Engineer"
      priority: "medium"
      trigger_conditions:
        - "architecture documentation"
      mode: "recommended"

  sequence:
    type: "sequential"
    order:
      - "Researcher"
      - "Security Reviewer"
      - "Diagram Engineer"

  quality_gates:
    required:
      - gate: "architecture_security_review"
        threshold: 85
        blocking: true
      - gate: "documentation_complete"
        threshold: 100
        blocking: true

  completion_criteria:
    - "Research document complete"
    - "Architecture diagram created"
    - "Security review passed"
    - "Authentication flow documented"

  rationale: |
    Research phase for unfamiliar OAuth 2.0 patterns. Security Reviewer
    evaluates architecture before implementation to catch design flaws early.
    Diagram Engineer creates visual representation of auth flow.
```

---

## Phase 2: Frontend Implementation (Days 3-4)

### Tasks
1. Implement login page UI
2. Implement registration page UI
3. Implement password reset flow
4. Add form validation
5. Write frontend tests

### Timeline
- Start: 2025-11-03
- End: 2025-11-04
- Duration: 2 days

### Orchestration

```yaml
orchestration:
  agents:
    - name: "Web Developer"
      priority: "high"
      trigger_conditions:
        - "any frontend development"
      mode: "mandatory"

    - name: "Security Reviewer"
      priority: "medium"
      trigger_conditions:
        - "form handling"
        - "password inputs"
      mode: "recommended"
      notes: "Consult during development for security guidance"

    - name: "Test Engineer"
      priority: "high"
      trigger_conditions:
        - "after UI implementation"
      mode: "mandatory"
      quality_gate:
        metric: "test_coverage"
        threshold: 90
        blocking: true

  sequence:
    type: "sequential"
    order:
      - "Web Developer"
      - "Test Engineer"

    parallel_groups:
      - ["Web Developer", "Security Reviewer"]  # Security can consult during dev

  quality_gates:
    required:
      - gate: "test_coverage"
        threshold: 90
        blocking: true
        scope: "frontend auth components"

      - gate: "form_validation_complete"
        threshold: 100
        blocking: true

  completion_criteria:
    - "All UI components implemented"
    - "Form validation working"
    - "Tests passing with ≥90% coverage"
    - "Code committed"

  rationale: |
    Standard frontend development phase. Test Engineer ensures component
    tests cover auth UI. Security Reviewer available for consultation on
    form handling and password inputs.
```

---

## Phase 3: Backend Implementation (Days 5-6)

### Tasks
1. Implement JWT token generation/validation
2. Implement OAuth 2.0 endpoints
3. Implement password reset endpoints
4. Add rate limiting
5. Write backend tests

### Timeline
- Start: 2025-11-05
- End: 2025-11-06
- Duration: 2 days

### Orchestration

```yaml
orchestration:
  agents:
    - name: "Web Developer"
      priority: "high"
      trigger_conditions:
        - "any backend development"
      mode: "mandatory"

    - name: "Security Reviewer"
      priority: "high"
      trigger_conditions:
        - "implementing authentication"
        - "JWT tokens"
        - "OAuth endpoints"
      mode: "mandatory"
      quality_gate:
        metric: "security_score"
        threshold: 85
        blocking: true

    - name: "Test Engineer"
      priority: "high"
      trigger_conditions:
        - "after implementation"
      mode: "mandatory"
      quality_gate:
        metric: "test_coverage"
        threshold: 90
        blocking: true

    - name: "Observability Engineer"
      priority: "medium"
      trigger_conditions:
        - "authentication endpoints"
      mode: "mandatory"
      quality_gate:
        metric: "logging_audit"
        threshold: 80
        blocking: false

  sequence:
    type: "sequential"
    order:
      - "Web Developer"
      - "Security Reviewer"
      - "Test Engineer"
      - "Observability Engineer"

  quality_gates:
    required:
      - gate: "security_review"
        threshold: 85
        blocking: true
        focus: "authentication implementation, JWT, OAuth"

      - gate: "test_coverage"
        threshold: 90
        blocking: true
        scope: "auth endpoints"

      - gate: "logging_audit"
        threshold: 80
        blocking: false
        focus: "authentication events"

  completion_criteria:
    - "All endpoints implemented"
    - "Security audit passed (≥85)"
    - "Tests passing with ≥90% coverage"
    - "Authentication events logged"
    - "Code committed"

  rationale: |
    Security-critical phase implementing authentication. Security Reviewer
    runs comprehensive audit after implementation focusing on OWASP auth
    vulnerabilities. Test Engineer ensures thorough test coverage of auth
    logic. Observability Engineer verifies all auth events (login attempts,
    failures, token refresh) are properly logged.
```

---

## Phase 4: Quality Assurance (Days 7-8)

### Tasks
1. Comprehensive security audit
2. Performance testing of auth endpoints
3. Integration testing
4. Edge case testing

### Timeline
- Start: 2025-11-07
- End: 2025-11-08
- Duration: 2 days

### Orchestration

```yaml
orchestration:
  agents:
    - name: "Security Reviewer"
      priority: "high"
      trigger_conditions:
        - "any quality assurance work"
      mode: "mandatory"
      quality_gate:
        metric: "comprehensive_security_audit"
        threshold: 90
        blocking: true

    - name: "Test Engineer"
      priority: "high"
      trigger_conditions:
        - "any testing work"
      mode: "mandatory"
      quality_gate:
        metric: "test_coverage"
        threshold: 95
        blocking: true

    - name: "Performance Engineer"
      priority: "medium"
      trigger_conditions:
        - "performance testing"
      mode: "recommended"
      quality_gate:
        metric: "auth_endpoint_latency"
        threshold: 200  # ms
        blocking: false

  sequence:
    type: "parallel"
    parallel_groups:
      - ["Security Reviewer", "Test Engineer", "Performance Engineer"]

  quality_gates:
    required:
      - gate: "comprehensive_security_audit"
        threshold: 90
        blocking: true

      - gate: "test_coverage"
        threshold: 95
        blocking: true

      - gate: "all_tests_passing"
        threshold: 100
        blocking: true

    optional:
      - gate: "performance_check"
        threshold: 200  # ms
        blocking: false

  completion_criteria:
    - "Security audit passed (≥90)"
    - "Test coverage ≥95%"
    - "All tests passing"
    - "Performance acceptable"

  rationale: |
    Dedicated quality phase. All quality agents run in parallel.
    Security Reviewer does final comprehensive audit. Test Engineer
    verifies coverage and adds edge case tests. Performance Engineer
    checks auth endpoint latency (recommendation for future optimization).
```

---

## Phase 5: Documentation & Deployment (Day 9)

### Tasks
1. Write user documentation (how to authenticate)
2. Write developer documentation (auth API)
3. Update architecture docs
4. Commit sprint work

### Timeline
- Start: 2025-11-09
- End: 2025-11-09
- Duration: 1 day

### Orchestration

```yaml
orchestration:
  agents:
    - name: "Documentation Engineer"
      priority: "high"
      trigger_conditions:
        - "any documentation work"
      mode: "mandatory"
      quality_gate:
        metric: "documentation_complete"
        threshold: 100
        blocking: true

    - name: "Diagram Engineer"
      priority: "medium"
      trigger_conditions:
        - "architecture documentation"
      mode: "recommended"

    - name: "Git Committer"
      priority: "low"
      trigger_conditions:
        - "final sprint commit"
      mode: "mandatory"

  sequence:
    type: "sequential"
    order:
      - "Documentation Engineer"
      - "Diagram Engineer"
      - "Git Committer"

  quality_gates:
    required:
      - gate: "documentation_complete"
        threshold: 100
        blocking: true
        items:
          - "User guide updated"
          - "API documentation complete"
          - "Architecture docs updated"

  completion_criteria:
    - "All documentation written"
    - "Diagrams updated"
    - "Sprint work committed"
    - "Sprint marked complete"

  rationale: |
    Final documentation phase. Documentation Engineer updates all
    user-facing and developer docs. Diagram Engineer updates architecture
    diagrams if needed. Git Committer saves sprint work and generates
    retrospective.
```

---

**End of Sprint Plan**
```

### 11.2 Example: Security Hardening Sprint

```markdown
# Sprint 5 Plan: Security Hardening

**Type:** Security Enhancement
**Duration:** 5 days
**Status:** not-started

---

## Phase 1: Security Audit (Days 1-2)

### Tasks
1. Comprehensive security audit of entire codebase
2. OWASP Top 10 vulnerability check
3. Dependency security scan
4. Document findings

### Orchestration

```yaml
orchestration:
  agents:
    - name: "Security Reviewer"
      priority: "high"
      trigger_conditions:
        - "any security work"
      mode: "mandatory"
      quality_gate:
        metric: "security_audit_complete"
        threshold: 100
        blocking: true

  sequence:
    type: "sequential"
    order:
      - "Security Reviewer"

  quality_gates:
    required:
      - gate: "security_audit_complete"
        threshold: 100
        blocking: true
        scope: "entire codebase"

  rationale: |
    Security-focused sprint. Security Reviewer dominates orchestration
    with comprehensive audit across all phases.
```

---

## Phase 2: Fix Critical Issues (Days 3-4)

### Tasks
1. Fix all critical and high-severity issues
2. Test fixes
3. Re-audit fixed code

### Orchestration

```yaml
orchestration:
  agents:
    - name: "Web Developer"
      priority: "high"
      trigger_conditions:
        - "implementing fixes"
      mode: "mandatory"

    - name: "Security Reviewer"
      priority: "high"
      trigger_conditions:
        - "verify fixes"
      mode: "mandatory"
      quality_gate:
        metric: "security_score"
        threshold: 95
        blocking: true

    - name: "Test Engineer"
      priority: "high"
      trigger_conditions:
        - "regression testing"
      mode: "mandatory"

  sequence:
    type: "sequential"
    order:
      - "Web Developer"
      - "Security Reviewer"
      - "Test Engineer"

  quality_gates:
    required:
      - gate: "critical_issues_fixed"
        threshold: 100
        blocking: true

      - gate: "security_score"
        threshold: 95
        blocking: true

      - gate: "no_regressions"
        threshold: 100
        blocking: true

  rationale: |
    Fix phase with tight security loop. Security Reviewer verifies
    each fix immediately. Test Engineer ensures no regressions.
```

---

**Note:** Security sprint has different orchestration than feature sprint:
- Security Reviewer appears in EVERY phase (not just quality phase)
- Higher security thresholds (95 vs 85)
- More emphasis on comprehensive auditing
```

### 11.3 Example: Ad-Hoc Work

```markdown
## Example: Quick Bug Fix (Ad-Hoc Mode)

**User Request:** "Quick fix: login button not working on mobile"

**Claude's Analysis:**
```yaml
mode: AD_HOC
complexity: simple
risk_level: low
urgency: high
domains: ["frontend"]

triggered_agents:
  - Web Developer (confidence: 0.9)
  - Test Engineer (confidence: 0.4)

decision: Handle directly, no agent launch
rationale: |
  Simple UI bug fix. Low risk (styling issue). High urgency.
  Will test manually and commit directly.
```

**Claude's Response:**
"I'll fix this directly - it's a simple styling issue and you need it quickly.

Looking at the button CSS... found the issue: missing `display: block` in mobile media query.

Fixed and tested in mobile viewport. Committing now."

**No sprint plan, no formal orchestration, no quality gates.**

---

## Example: Security-Sensitive Ad-Hoc Work

**User Request:** "Quick fix: user can access other users' data in /api/profile endpoint"

**Claude's Analysis:**
```yaml
mode: AD_HOC
complexity: medium
risk_level: HIGH
urgency: high
domains: ["security", "backend"]

triggered_agents:
  - Security Reviewer (confidence: 1.0)
  - Test Engineer (confidence: 0.8)

decision: Use Security Reviewer (despite ad-hoc mode)
rationale: |
  HIGH RISK: Security vulnerability allowing unauthorized data access.
  Must run Security Reviewer to ensure fix is complete and doesn't
  introduce new vulnerabilities.
```

**Claude's Response:**
"This is a serious security issue - I'll launch the Security Reviewer to ensure we fix it properly.

Launching Security Reviewer...

[Security Reviewer identifies issue: missing user ID validation]
[Security Reviewer suggests fix + additional validation]
[Security Reviewer audits fix]

✓ Security audit passed. Fix is secure.

Now writing regression test to prevent this issue in the future..."

**Security Reviewer used despite ad-hoc mode due to high risk.**
```

---

## Summary

This design document specifies the complete sprint-driven orchestration system for Vibey Framework 2.0. Key changes:

1. **Simplified orchestration:** 3 modes → 1 unified approach
2. **Context-aware:** Sprint type and phase determine orchestration
3. **Self-documenting:** Sprint plans show both WHAT and HOW
4. **Flexible:** Ad-hoc mode for quick work outside sprints
5. **Intelligent:** Sprint Planning Agent designs optimal orchestration per sprint

**Next Steps:**
1. Review and approve this design
2. Implement Sprint Planning Agent enhancements
3. Create new CLAUDE.md template
4. Update config schema
5. Test with example sprints
6. Document user-facing changes

---

**Document Version:** 1.0
**Status:** Ready for Review
**Feedback:** Please provide feedback on any section
