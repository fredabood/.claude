# Sprint-Driven Orchestration Guide

**Framework Version:** 2.0
**Last Updated:** 2025-11-05

---

## Overview

Vibey Framework 2.0 introduces **Sprint-Driven Orchestration**, a simplified approach that eliminates complex orchestration modes in favor of context-aware, adaptive agent routing.

**Core Concept:** Sprint planning generates phase-specific orchestration rules. Claude follows these rules during sprint execution and operates flexibly outside sprints.

---

## Two Operating Modes

### Sprint Mode (Structured)

**When:** You're executing within a planned sprint
**Behavior:** Follow phase-specific orchestration rules embedded in sprint plan
**Benefits:** Consistent, quality-driven execution with appropriate agents for each phase

### Ad-Hoc Mode (Flexible)

**When:** Quick fixes, exploration, work outside sprint structure
**Behavior:** Autonomous agent decisions based on complexity, risk, and urgency
**Benefits:** Speed and flexibility without sprint overhead

---

## Sprint Mode

### How It Works

1. **Sprint Planning** generates orchestration rules for each phase
2. **Claude reads** current phase orchestration from sprint plan
3. **Agents launch** according to phase rules (priority, sequence, quality gates)
4. **Progress tracked** and sprint plan updated

### Example Phase Orchestration

```yaml
# From: docs/sprints/sprint-3-plan.md
## Phase 2: Backend Implementation

orchestration:
  agents:
    - name: "Web Developer"
      priority: "high"
      mode: "mandatory"

    - name: "Security Reviewer"
      priority: "high"
      mode: "mandatory"
      trigger_conditions:
        - "implementing authentication"
      quality_gate:
        metric: "security_score"
        threshold: 85
        blocking: true

    - name: "Test Engineer"
      priority: "high"
      mode: "mandatory"
      quality_gate:
        metric: "test_coverage"
        threshold: 90
        blocking: true

  sequence:
    type: "sequential"
    order:
      - "Web Developer"
      - "Security Reviewer"
      - "Test Engineer"
      - "Observability Engineer"
      - "Git Committer"

  quality_gates:
    required:
      - gate: "security_review"
        threshold: 85
        blocking: true
      - gate: "test_coverage"
        threshold: 90
        blocking: true

  completion_criteria:
    - "All mandatory agents have run"
    - "All blocking quality gates passed"
    - "Code committed"
```

### Sprint Context Detection

Claude determines it's in Sprint Mode when:

1. **Current Sprint Marker** in CLAUDE.md shows `active: true`
2. **User mentions sprint** ("continue sprint 3", "work on sprint task")
3. **Active sprint plan** found in `docs/sprints/`

### Sprint Execution Flow

```
User Request → Check Sprint Status → Load Phase Orchestration
            ↓
  Match Trigger Conditions → Launch Agents in Sequence
            ↓
  Run Quality Gates → Update Progress → Move to Next Phase
```

---

## Ad-Hoc Mode

### How It Works

Claude makes autonomous decisions about agent usage based on:

1. **Task Complexity** - Simple, medium, or complex
2. **Risk Level** - Low, medium, or high
3. **Urgency** - How quickly user needs results

### Decision Logic

```python
# Simple + Low Risk + High Urgency → Handle directly
if complexity == "simple" and risk == "low" and urgency == "high":
    use_agents = false
    explain("Quick fix, handling directly for speed")

# Medium complexity OR Medium risk → Selective agents
elif complexity == "medium" or risk == "medium":
    use_agents = [high_confidence_matches]
    explain("Using {agents} due to {reason}")

# Complex OR High Risk → Use all relevant agents
elif complexity == "complex" or risk == "high":
    use_agents = all_triggered_agents
    suggest_sprint_planning("This is complex enough to benefit from planning")
```

### Agent Trigger Patterns

Agents define trigger patterns for ad-hoc usage:

```markdown
# Security Reviewer Agent

**Trigger Patterns (Ad-Hoc Mode):**
- **Keywords:** security, vulnerability, authentication, OWASP, XSS
- **Contexts:** Reviewing auth code, handling user input
- **File Patterns:** */auth/*, */security/*, *login*, *password*
```

Claude uses these as **suggestions** (not requirements) in ad-hoc mode.

### Example Ad-Hoc Scenarios

#### Scenario 1: Quick Bug Fix

**Request:** "Fix login button styling on mobile"

**Claude's Analysis:**
- Complexity: Simple (styling fix)
- Risk: Low (no logic changes)
- Urgency: High ("fix" implies urgency)

**Decision:** Handle directly, no agents needed

**Output:**
```
"I'll fix this directly - it's a simple styling issue.
Fixed CSS for mobile viewport. Testing manually and committing."
```

#### Scenario 2: Security-Sensitive Fix

**Request:** "Fix: users can access other users' data"

**Claude's Analysis:**
- Complexity: Medium (auth bug)
- Risk: HIGH (security vulnerability)
- Urgency: High (active security issue)

**Decision:** Use Security Reviewer despite ad-hoc mode

**Output:**
```
"This is a security vulnerability - launching Security Reviewer
to ensure complete fix.

[Security Reviewer identifies issue and suggests fix]
[Security Reviewer audits fix]

✓ Security audit passed. Fix is secure."
```

---

## How Sprint Planning Designs Orchestration

### Domain Analysis

Sprint Planning Agent analyzes each phase for:

- **Security domains** → Security Reviewer needed
- **Performance domains** → Performance Engineer needed
- **ML domains** → ML Engineer + Researcher needed
- **Infrastructure domains** → (Future) Infrastructure agents
- **Documentation domains** → Documentation Engineer mandatory

### Agent Selection Rules

```yaml
# Security-critical phase
IF security_keywords_detected OR handling_sensitive_data:
  agents:
    - Security Reviewer (priority: high, mandatory)
  quality_gates:
    - security_score >= 85 (blocking)

# Performance-critical phase
IF performance_keywords_detected:
  agents:
    - Performance Engineer (priority: medium, recommended)
  quality_gates:
    - performance_score >= 80 (non-blocking warning)

# Always included
agents:
  - Development agent (based on project type)
  - Test Engineer (mandatory)
  - Documentation Engineer (recommended or mandatory)
  - Git Committer (mandatory, runs last)
```

### Sequence Design

**Standard Sequence:**
1. Research/Planning agents (if new tech)
2. Development agents
3. Quality agents (security, testing, performance, logging)
4. Documentation agents
5. Git Committer

**Adaptations:**
- Security-critical: Security Reviewer runs TWICE (design + implementation)
- Research-heavy: Researcher runs FIRST
- Quality phases: All quality agents run in PARALLEL

### Phase Size Constraint

**Rule:** Each phase must fit within ~8,000 tokens

**If phase exceeds limit:**
- Split into sub-phases (2A, 2B, 2C...)
- Each sub-phase has own orchestration
- Maintains context coherence

**Benefit:** Forces good sprint decomposition

---

## Comparison with v1.0 Orchestration Modes

### v1.0: Three Modes

**Simple Mode:** Explicit keyword rules in CLAUDE.md
**Balanced Mode:** CLAUDE.md + agent trigger patterns
**Tiered Mode:** Fast/Coordinator/Explicit paths

**Problems:**
- High cognitive load (learn 3 modes)
- Configuration complexity (choose mode)
- Static orchestration (same rules for all sprints)
- CLAUDE.md bloat (rules take up space)

### v2.0: Sprint-Driven

**Sprint Mode:** Phase-specific orchestration from sprint planning
**Ad-Hoc Mode:** Flexible, autonomous decisions

**Benefits:**
- One approach (not three)
- Context-aware (security sprint ≠ feature sprint)
- Adaptive (early phase ≠ late phase)
- Cleaner CLAUDE.md (rules in sprint plans)

---

## Best Practices

### For Sprint Mode

✅ **Trust the orchestration** - Phase rules are designed for this sprint
✅ **Follow sequence** - Agent order is intentional (dependencies)
✅ **Respect quality gates** - Blocking gates prevent poor quality
✅ **Update progress** - Keep sprint plan current

❌ **Don't skip agents** - Mandatory agents are mandatory for a reason
❌ **Don't skip quality gates** - Blocking gates must pass
❌ **Don't freelance** - Follow phase orchestration unless user overrides

### For Ad-Hoc Mode

✅ **Assess before acting** - Consider complexity, risk, urgency
✅ **Explain decisions** - Tell user why you used or skipped agents
✅ **Suggest planning** - Complex work benefits from sprint structure
✅ **Security always matters** - High-risk changes get Security Reviewer

❌ **Don't over-automate** - Simple fixes don't need agents
❌ **Don't under-protect** - Security-sensitive code needs review
❌ **Don't ignore complexity** - Complex tasks deserve sprint planning

---

## Frequently Asked Questions

### Do I need to plan a sprint for every task?

No. Sprint mode is for structured, planned work. Ad-hoc mode handles:
- Quick bug fixes
- Exploration and research
- Code review
- Understanding the codebase

Use sprint planning when you know what you're building and it's non-trivial (>1 day of work).

### What if I want different orchestration mid-sprint?

You can:
1. **Edit sprint plan** - Modify phase orchestration rules directly
2. **Override in request** - "Use X agent even though it's not in the plan"
3. **Adjust for next phase** - Phase orchestration can differ

### How do I switch between Sprint and Ad-Hoc mode?

**Entering Sprint Mode:**
- Start sprint planning
- User says "continue sprint X"
- System detects active sprint

**Entering Ad-Hoc Mode:**
- Sprint completes
- User says "work outside the sprint"
- User says "pause sprint"

**It's automatic** - Claude detects mode based on context.

### Can I customize orchestration for my project?

Yes! Two ways:

1. **During sprint planning** - Sprint Planning Agent generates orchestration based on your project's needs
2. **Edit sprint plans directly** - Modify orchestration sections in phase plans

### What happened to the Coordinator Agent?

The Coordinator Agent (v1.0 Tiered mode) is **deprecated**. Its intelligence has been moved to the Sprint Planning Agent, which now designs orchestration as part of sprint planning.

Sprint Planning Agent has the same context-awareness but generates orchestration upfront (during planning) rather than dynamically (during execution).

---

## Migration from v1.0

### If You Used Simple Mode

**v1.0:**
```yaml
framework:
  orchestration_mode: "simple"
```

**v2.0:**
```yaml
framework:
  sprint_driven_orchestration:
    enabled: true
```

**Changes:**
- Orchestration rules move from CLAUDE.md to sprint plans
- Ad-hoc work uses agent triggers (similar to before)

### If You Used Balanced Mode

**v1.0:**
```yaml
framework:
  orchestration_mode: "balanced"
```

**v2.0:**
```yaml
framework:
  sprint_driven_orchestration:
    enabled: true
```

**Changes:**
- Agent trigger patterns still work (for ad-hoc mode)
- Sprint mode adds structure (phase-specific orchestration)

### If You Used Tiered Mode

**v1.0:**
```yaml
framework:
  orchestration_mode: "tiered"
```

**v2.0:**
```yaml
framework:
  sprint_driven_orchestration:
    enabled: true
```

**Changes:**
- Coordinator Agent deprecated
- Intelligence moved to Sprint Planning Agent
- Fast path = Ad-hoc mode
- Smart path = Sprint mode

---

## Additional Resources

- **Design Document:** `docs/development/SPRINT_DRIVEN_ORCHESTRATION_DESIGN.md`
- **Sprint Planning Agent:** `framework/agents/planning/sprint-planning.md`
- **Example Sprint Plan:** `docs/examples/sprint-with-orchestration.md`
- **Sprint Retrospective Template:** `framework/templates/sprint-retrospective.md.template`

---

**Questions?** See framework documentation or review example sprint plans.

**Happy building!** 🚀
