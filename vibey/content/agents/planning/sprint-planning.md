---
id: sprint-planning
name: Sprint Planning Agent
type: planning
version: 1.0.0
triggers:
  keywords:
  - sprint planning
  - plan sprint
  - roadmap
  - iteration
  - backlog
  - prioritize
  - dependencies
  - quarterly planning
  - sprint goals
  - sprint objectives
  contexts:
  - beginning of sprint
  - project planning phase
  - roadmap updates
  - dependency analysis
  - feature prioritization
  file_patterns:
  - ROADMAP.md
  - docs/sprints/*
  - .claude/project-config.yaml
  - backlog files
  priority: high
inputs:
- name: task
  type: string
  required: true
  description: Task or request for the Sprint Planning Agent
- name: context
  type: string
  required: false
  description: Additional context about the project or codebase
outputs:
- name: result
  type: string
  description: Result of the agent task
- name: files_modified
  type: array
  description: List of files created or modified
description: ''
---

# Sprint Planning Agent

**Version:** 2.0 (Sprint-Driven Orchestration)
**Type:** Planning Agent
**When to Use:** Planning sprint iterations, re-prioritizing roadmap, analyzing dependencies, designing agent orchestration

**Trigger Patterns:**
- **Keywords:** sprint planning, plan sprint, roadmap, iteration, backlog, prioritize, dependencies, quarterly planning, sprint goals, sprint objectives
- **Contexts:** beginning of sprint, project planning phase, roadmap updates, dependency analysis, feature prioritization
- **File Patterns:** ROADMAP.md, docs/sprints/*, .claude/project-config.yaml, backlog files
- **Priority:** High (foundational planning activity)

---

## 🎯 Purpose

The Sprint Planning Agent is responsible for:
- Analyzing current project state and collecting requirements
- Creating comprehensive sprint plans with clear objectives
- Ordering sprints based on dependencies and business value
- Tracking progress and updating roadmap documentation
- Ensuring alignment with project vision and architecture

**When to Use This Agent:**
- Planning new sprint iterations
- Re-prioritizing roadmap based on new requirements
- Analyzing sprint dependencies and blocking issues
- Creating quarterly/annual planning documents
- Updating roadmap with progress

---

## 📥 Input

**Required:**
1. **Current State Analysis:**
   - .claude/CLAUDE.md - Project current state
   - {% if config.custom.roadmap_location %}{{ config.custom.roadmap_location }}{% else %}ROADMAP.md{% endif %} - Current sprint status and roadmap
   - `git status` - Recent changes

2. **Requirements Source:**
   - User-provided requirements and objectives
   - Strategic goals and business priorities
   - Technical debt and architecture improvements
   - Stakeholder feedback and feature requests

**Optional:**
3. **Context Documents:**
   - Existing sprint plans in `docs/sprints/v*/`
   - Architecture documentation
   - Production metrics and monitoring data
   - Security review findings

---

## 🔄 Workflow

### Phase 1: Discovery & Analysis (1-2 hours)

#### Step 1.1: Read Current State
**Action:** Understand project current state and recent work

**Read These Files:**
```bash
# Critical context files
CLAUDE.md                    # Current state, focus, metrics
{% if config.custom.roadmap_location %}{{ config.custom.roadmap_location }}{% else %}ROADMAP.md{% endif %}                    # Current sprint, progress
git log --oneline -20        # Recent commits
```

**Analyze:**
- Current sprint status (what % complete?)
- Recently completed work
- Open issues and blockers
- Key project metrics
- Infrastructure maturity

**Questions to Answer:**
- What sprint/version are we currently on?
- What are the immediate blockers?
- What are the current key metrics?
- What infrastructure is in place?
- What's the current architecture state?

#### Step 1.2: Gather Requirements
**Action:** Collect and organize new requirements

**Sources:**
1. **User Input:** Direct requirements from sprint planning session
2. **Roadmap Gaps:** Incomplete items from existing roadmap
3. **Technical Debt:** Known issues in code, architecture
4. **Security Reviews:** Findings from security reviews
5. **Production Metrics:** Issues discovered in monitoring

**Organize Requirements:**
```markdown
## Feature Requirements
- [Feature name]: [Description]
- **Value:** [Business/user value]
- **Effort:** [Estimated days/weeks]
- **Dependencies:** [What must be complete first?]

## Technical Requirements
- [Infrastructure improvement]: [Why needed]
- **Criticality:** [High/Medium/Low]
- **Blocking:** [What features depend on this?]

## Security Requirements
- [Security improvement]: [Risk being mitigated]
- **Priority:** [Critical/High/Medium/Low]

## Debt Reduction
- [Refactoring/cleanup]: [Impact on maintainability]
```

#### Step 1.3: Analyze Dependencies
**Action:** Map dependencies between requirements

**Dependency Types:**
1. **Technical Dependencies:**
   - Infrastructure required before features
   - {% if config.architecture %}{{ config.architecture.pattern }}{% else %}Architecture{% endif %} layer completion
   - Authentication/authorization systems
   - Monitoring and alerting

2. **Logical Dependencies:**
   - Core functionality before advanced features
   - Data foundation before analytics
   - API before UI

3. **Business Dependencies:**
   - MVP features before advanced features
   - Free tier before paid tier
   - Single-user before multi-tenant

**Create Dependency Graph:**
```mermaid
graph TD
    A[Foundation] --> B[Core Features]
    B --> C[Advanced Features]
    B --> D[Analytics]
    C --> E[Production Deployment]
    D --> E
```

**Output:** Dependency matrix showing what blocks what

---

### Phase 2: Prioritization & Sequencing (2-3 hours)

#### Step 2.1: Score Requirements
**Action:** Assign scores to each requirement

**Scoring Framework:**
```python
# Business Value Score (0-10)
business_value = {
    'user_impact': 0-4,      # How many users benefit?
    'revenue_impact': 0-3,    # Revenue potential?
    'strategic_value': 0-3    # Aligns with vision?
}

# Technical Urgency Score (0-10)
technical_urgency = {
    'blocking_count': 0-4,    # How many features blocked?
    'technical_debt': 0-3,    # Debt accumulation?
    'security_risk': 0-3      # Security vulnerabilities?
}

# Effort Score (inverse - lower is better)
effort_weeks = [1, 2, 3, 4, 5, 6+]  # Estimated weeks

# Priority = (business_value + technical_urgency) / effort_weeks
```

**Example Scoring:**
```yaml
requirements:
  - name: "Authentication System"
    business_value: 8/10 (needed for user management)
    technical_urgency: 9/10 (blocks multiple features)
    effort: 1 week
    priority: 17.0 (CRITICAL)

  - name: "Advanced Analytics Dashboard"
    business_value: 7/10 (nice competitive advantage)
    technical_urgency: 2/10 (not blocking)
    effort: 3 weeks
    priority: 3.0 (HIGH, but later)
```

#### Step 2.2: Create Sprint Sequence
**Action:** Order sprints based on priorities and dependencies

**Sequencing Rules:**
1. **Technical Foundation First:** Infrastructure before features
2. **Unblock Early:** High-blocking items prioritized
3. **Value Streams:** Group related features together
4. **{% if config.quality_gates %}Quality Gates{% else %}Production Readiness{% endif %}:** Maintain quality standards
5. **Parallel Tracks:** Independent work can run concurrently

**Sprint Sequencing Strategy:**
```yaml
# Example Multi-Sprint Sequence

v0.1.0: Core Infrastructure
  why: Foundation for all future work
  duration: 2-3 weeks
  dependencies: None (can start immediately)
  output: Basic project setup, CI/CD, testing framework

v0.2.0: MVP Features
  why: Deliver initial value to users
  duration: 3-4 weeks
  dependencies: v0.1.0 (infrastructure ready)
  output: Core functionality working

v0.3.0: Production Hardening
  why: Scale readiness, monitoring, reliability
  duration: 2-3 weeks
  dependencies: v0.2.0 (features to monitor)
  output: Monitoring, logging, error handling

v0.4.0: Advanced Features
  why: Competitive differentiation
  duration: 4-5 weeks
  dependencies: v0.2.0 (core features), v0.3.0 (infrastructure)
  output: Advanced functionality
```

#### Step 2.3: Validate Sequence
**Action:** Review sprint sequence for issues

**Validation Checklist:**
- [ ] All dependencies satisfied before dependent sprint?
- [ ] Quality standards maintained throughout?
- [ ] Parallel tracks clearly identified?
- [ ] MVP features before advanced features?
- [ ] {% if config.quality_gates and config.quality_gates.security_review and config.quality_gates.security_review.enabled %}Security reviews scheduled at sprint ends?{% else %}Reviews scheduled appropriately?{% endif %}
- [ ] Realistic effort estimates (team velocity)?
- [ ] Clear success criteria for each sprint?

**Common Issues:**
- **Waterfall Trap:** Too sequential, not enough parallelization
- **Dependency Hell:** Circular dependencies or too many blockers
- **Scope Creep:** Sprints too large (>8 weeks is a red flag)
- **Infrastructure Last:** Features before infrastructure (will fail at scale)

---

### Phase 3: Sprint Plan Creation (2-4 hours per sprint)

#### Step 3.1: Create Sprint Overview Document
**Action:** Write main sprint plan file

**File Location:** `docs/sprints/v0.X.0/SPRINT_V0.X.0_PLAN.md`

**Template:**
```markdown
# Sprint Plan: v0.X.0 - [Sprint Name]

**Sprint Duration:** [X weeks] ([Y days])
**Start Date:** [Date or "After vPREV.0 complete"]
**Target Completion:** [Date or TBD]
**Sprint Goal:** [One sentence goal]

---

## 🎯 Sprint Objectives

**Primary Goal:** [Main objective - what does this sprint achieve?]

{% if config.quality_gates %}**Quality Metrics:** [Current → Target]{% endif %}

**Key Deliverables:**
1. [Deliverable 1]
2. [Deliverable 2]
3. [Deliverable 3]
...

**Why This Sprint:**
- [Business value reason 1]
- [Business value reason 2]
- [Technical reason]

**Prerequisites:**
- ✅/❌ [Prerequisite 1] (what must be complete first)
- ✅/❌ [Prerequisite 2]

---

## 📋 Sprint Phases

This sprint is divided into [N] phases across [X] weeks:

### Week 1-2: [Phase Group Name] (Days 1-N)

**Phase 1: v0.X.1 - [Phase Name]** (Days 1-3)
- [Task 1]
- [Task 2]
- [Task 3]

**Phase 2: v0.X.2 - [Phase Name]** (Days 4-7)
- [Task 1]
- [Task 2]

### Week 3-4: [Phase Group Name] (Days N-M)

**Phase 3: v0.X.3 - [Phase Name]** (Days 8-12)
- [Task 1]
- [Task 2]

{% if config.quality_gates and config.quality_gates.security_review and config.quality_gates.security_review.enabled %}
### Final Day: Security Review (Day [LAST])

**Comprehensive Security Review** ⚠️ **MANDATORY**
- [Security concern 1]
- [Security concern 2]
- [Security concern 3]
{% endif %}

---

## 📊 Success Criteria

### Must Have
- [ ] [Critical success criterion 1]
- [ ] [Critical success criterion 2]
- [ ] All tests passing
{% if config.quality_gates and config.quality_gates.security_review and config.quality_gates.security_review.enabled %}- [ ] **Security review completed ⚠️ MANDATORY**{% endif %}

### Key Features
1. **[Feature Category 1]:**
   - [Sub-feature 1]
   - [Sub-feature 2]

2. **[Feature Category 2]:**
   - [Sub-feature 1]
   - [Sub-feature 2]

---

## 🎯 Definition of Done

- [ ] All success criteria met
- [ ] All tests passing (≥{{ config.coding_standards.test_coverage.minimum if config.coding_standards and config.coding_standards.test_coverage else 90 }}% coverage)
- [ ] Documentation complete
{% if config.quality_gates %}
{% if config.quality_gates.security_review and config.quality_gates.security_review.enabled %}- [ ] **⚠️ MANDATORY: Security review completed**
- [ ] **⚠️ MANDATORY: All critical issues fixed**{% endif %}
{% if config.quality_gates.unit_testing and config.quality_gates.unit_testing.enabled %}- [ ] Unit testing review completed{% endif %}
{% if config.quality_gates.logging_audit and config.quality_gates.logging_audit.enabled %}- [ ] Logging audit completed (≥{{ config.quality_gates.logging_audit.minimum_score }}/100){% endif %}
{% if config.quality_gates.documentation and config.quality_gates.documentation.enabled %}- [ ] Documentation review completed{% endif %}
{% endif %}

---

## 🔗 Phase Documents

For detailed implementation plans, see individual phase documents:

- **Phase 1:** `docs/sprints/v0.X.0/SPRINT_V0.X.1_PLAN.md` - [Phase Name]
- **Phase 2:** `docs/sprints/v0.X.0/SPRINT_V0.X.2_PLAN.md` - [Phase Name]
...

---

## 📈 Sprint Metrics

**Tracking:**
- Daily progress updates in standup
- Weekly sprint review
- Burndown chart tracking
- Test coverage monitoring

**Key Metrics:**
- [ ] [Metric 1]: Target [X]
- [ ] [Metric 2]: Target [Y]

---

## ⚠️ Risks & Mitigation

### High Risk
- **[Risk 1]:** [Description]
  - **Impact:** [What happens if this materializes?]
  - **Mitigation:** [How to prevent/handle?]

### Medium Risk
- **[Risk 2]:** [Description]
  - **Impact:** [Consequence]
  - **Mitigation:** [Strategy]

---

## 🔄 Dependencies

**Blocks These Sprints:**
- v0.Y.0 - [Sprint that depends on this one]

**Blocked By:**
- v0.Z.0 - [Sprint that must complete first]

**Parallel Tracks:**
- v0.W.0 - [Sprint running concurrently]

---

## 📚 References

- Previous sprint: `docs/sprints/v0.PREV.0/SPRINT_V0.PREV.0_PLAN.md`
- Architecture: {% if config.custom.architecture_doc %}{{ config.custom.architecture_doc }}{% else %}`docs/architecture/`{% endif %}
- Current state: `.claude/CLAUDE.md`
```

#### Step 3.2: Create Phase Plans
**Action:** Write detailed phase plans for each sprint phase

**File Location:** `docs/sprints/v0.X.0/SPRINT_V0.X.Y_PLAN.md`

**Phase Plan Template:**
```markdown
# Phase Plan: v0.X.Y - [Phase Name]

**Parent Sprint:** v0.X.0 - [Sprint Name]
**Phase Duration:** [N] days (Days [START]-[END] of sprint)
**Phase Goal:** [One sentence - what does this phase achieve?]

---

## 🎯 Phase Objectives

**What:** [What we're building/doing]
**Why:** [Why this is important]
**Success:** [How we know we're done]

**Deliverables:**
1. [Concrete deliverable 1]
2. [Concrete deliverable 2]
3. [Concrete deliverable 3]

---

## 📋 Tasks

### Task 1: [Task Name] (Day [N])
**Owner:** [Team/Person]
**Effort:** [Hours/Days]
**Priority:** [Critical/High/Medium/Low]

**Description:**
[What needs to be done]

**Acceptance Criteria:**
- [ ] [Criterion 1]
- [ ] [Criterion 2]

**Dependencies:**
- [Dependency 1]

### Task 2: [Task Name] (Day [N])
...

---

## 🧪 Testing Strategy

**Unit Tests:**
- [What to test]

**Integration Tests:**
- [What to test]

**E2E Tests:**
- [What to test]

**Coverage Target:** ≥{{ config.coding_standards.test_coverage.minimum if config.coding_standards and config.coding_standards.test_coverage else 90 }}%

---

## 📊 Success Metrics

**Phase Completion Criteria:**
- [ ] All tasks completed
- [ ] All tests passing
- [ ] Code reviewed
- [ ] Documentation updated

**Quality Gates:**
- [ ] Test coverage ≥ {{ config.coding_standards.test_coverage.minimum if config.coding_standards and config.coding_standards.test_coverage else 90 }}%
- [ ] No critical bugs
- [ ] Performance benchmarks met

---

## ⚠️ Risks

**Phase-Specific Risks:**
1. **[Risk]:** [Description]
   - **Mitigation:** [Strategy]

---

## 🔗 References

- Sprint plan: `docs/sprints/v0.X.0/SPRINT_V0.X.0_PLAN.md`
- Implementation guide: `docs/sprints/v0.X.0/SPRINT_V0.X.0_IMPLEMENTATION_GUIDE.md` **§X.Y**
```

**Note:** Phase plans should be 75-120 lines (WHAT/WHY only). All code goes in the implementation guide.

#### Step 3.3: Design Phase Orchestration (NEW - V2.0)
**Action:** Generate agent orchestration rules for each sprint phase

**Purpose:** Create phase-specific orchestration rules that determine which agents run, when, and with what quality gates during sprint execution.

**For Each Phase in Sprint:**

##### Substep 1: Analyze Phase Domains

Examine phase tasks and categorize by domain:

**Security Domain Detection:**
```python
security_indicators = {
    'keywords': ['authentication', 'authorization', 'permissions', 'user input',
                 'sensitive data', 'encryption', 'tokens', 'passwords', 'API keys',
                 'OAuth', 'JWT', 'SAML', 'CSRF', 'XSS', 'SQL injection'],
    'file_patterns': ['*/auth/*', '*/security/*', '*login*', '*password*'],
    'contexts': ['handling user data', 'payment processing', 'admin functions']
}

# Evaluate
security_critical = (
    any(keyword in phase_tasks for keyword in security_indicators['keywords']) or
    any(pattern in phase_files for pattern in security_indicators['file_patterns'])
)
```

**Performance Domain Detection:**
```python
performance_indicators = {
    'keywords': ['optimization', 'slow', 'latency', 'throughput', 'caching',
                 'real-time', 'large dataset', 'streaming', 'response time'],
    'contexts': ['high traffic', 'data processing', 'API endpoints']
}

performance_critical = any(keyword in phase_tasks for keyword in performance_indicators['keywords'])
```

**ML Domain Detection:**
```python
ml_indicators = {
    'keywords': ['model', 'training', 'inference', 'prediction', 'ML', 'AI',
                 'neural network', 'dataset', 'features', 'embedding'],
    'file_patterns': ['*/models/*', '*/ml/*', '*/training/*']
}

ml_related = any(keyword in phase_tasks for keyword in ml_indicators['keywords'])
```

**Infrastructure Domain Detection:**
```python
infrastructure_indicators = {
    'keywords': ['deployment', 'scaling', 'infrastructure', 'containers',
                 'kubernetes', 'terraform', 'CI/CD', 'docker'],
    'file_patterns': ['*/infrastructure/*', '*/deploy/*', '*.tf', 'Dockerfile']
}

infrastructure_related = any(keyword in phase_tasks for keyword in infrastructure_indicators['keywords'])
```

**Documentation Domain Detection:**
```python
documentation_indicators = {
    'keywords': ['API changes', 'architecture changes', 'user-facing features',
                 'breaking changes', 'deprecation', 'migration'],
    'contexts': ['public API modifications', 'user documentation needed']
}

documentation_heavy = (
    'API' in phase_name or
    'architecture' in phase_name or
    any(keyword in phase_tasks for keyword in documentation_indicators['keywords'])
)
```

##### Substep 2: Select Agents by Domain

Based on domain analysis, select required agents:

**Security Domain → Security Reviewer**
```yaml
IF security_critical:
  agent:
    name: "Security Reviewer"
    priority: "high"
    mode: "mandatory"
    trigger_conditions:
      - "implementing authentication"
      - "handling sensitive data"
      - "user input validation"
    quality_gate:
      metric: "security_score"
      threshold: {{ config.quality_gates.security_score_minimum if config.quality_gates else 85 }}
      blocking: true
```

**Performance Domain → Performance Engineer**
```yaml
IF performance_critical:
  agent:
    name: "Performance Engineer"
    priority: "medium"
    mode: "recommended"
    trigger_conditions:
      - "performance optimization"
      - "latency concerns"
    quality_gate:
      metric: "performance_score"
      threshold: 80
      blocking: false
```

**ML Domain → ML Engineer + Researcher**
```yaml
IF ml_related:
  agents:
    - name: "ML Engineer"
      priority: "high"
      mode: "mandatory"
    - name: "Researcher"
      priority: "high"
      mode: "recommended"
      trigger_conditions:
        - "new ML technique"
        - "unfamiliar algorithm"
```

**Always Include (based on project type):**
```yaml
# For web-app projects
IF project.type == 'web-app':
  - name: "Web Developer"
    priority: "high"
    mode: "mandatory"

# For ML projects
IF project.type == 'ml':
  - name: "ML Engineer"
    priority: "high"
    mode: "mandatory"

# Always include
- name: "Test Engineer"
  priority: "high"
  mode: "mandatory"
  quality_gate:
    metric: "test_coverage"
    threshold: {{ config.quality_gates.test_coverage_minimum if config.quality_gates else 90 }}
    blocking: true

- name: "Documentation Engineer"
  priority: "medium"
  mode: "recommended" if not documentation_heavy else "mandatory"

- name: "Git Committer"
  priority: "low"
  mode: "mandatory"
```

##### Substep 3: Design Execution Sequence

Order agents based on dependencies:

**Standard Sequence Template:**
```yaml
sequence:
  type: "sequential"
  order:
    # Phase 1: Research/Planning (if needed)
    - "Researcher"                    # If new technology
    - "Architecture Specialist"       # If architecture changes

    # Phase 2: Development
    - "Web Developer"                 # Or ML Engineer, etc.
    # Security Reviewer can run during development for consultation

    # Phase 3: Quality (after development)
    - "Security Reviewer"             # Comprehensive audit
    - "Test Engineer"                 # Coverage verification
    - "Performance Engineer"          # If performance-critical
    - "Observability Engineer"        # Logging audit

    # Phase 4: Documentation
    - "Documentation Engineer"
    - "Diagram Engineer"              # If architecture changes

    # Phase 5: Finalization
    - "Git Committer"

  # Optional: parallel execution groups
  parallel_groups:
    - ["Security Reviewer", "Test Engineer"]  # Can run simultaneously in quality phase
```

**Sequence Adaptations:**
- **Security-critical phases:** Security Reviewer runs TWICE (design review + implementation audit)
- **Research phases:** Researcher runs FIRST
- **Quality phases:** All quality agents run in parallel
- **Documentation phases:** Documentation + Diagram engineers run in parallel

##### Substep 4: Define Phase Quality Gates

```python
quality_gates = {
    'required': []
}

# Always required
quality_gates['required'].append({
    'gate': 'test_coverage',
    'threshold': config.quality_gates.test_coverage_minimum,
    'blocking': True
})

# Conditional based on domain
if security_critical:
    quality_gates['required'].append({
        'gate': 'security_review',
        'threshold': config.quality_gates.security_score_minimum,
        'blocking': True
    })

if any_code_changes:
    quality_gates['required'].append({
        'gate': 'logging_audit',
        'threshold': config.quality_gates.logging_audit_minimum,
        'blocking': False  # Warning only
    })

if performance_critical:
    quality_gates['optional'] = [{
        'gate': 'performance_check',
        'threshold': 80,
        'blocking': False
    }]

if documentation_heavy:
    quality_gates['required'].append({
        'gate': 'documentation_complete',
        'threshold': 100,
        'blocking': True
    })
```

##### Substep 5: Generate Orchestration YAML

Format orchestration rules:

```yaml
orchestration:
  # Agent selection and configuration
  agents:
    - name: "Security Reviewer"
      priority: "high"
      trigger_conditions:
        - "implementing authentication"
        - "handling sensitive data"
      mode: "mandatory"
      quality_gate:
        metric: "security_score"
        threshold: 85
        blocking: true

    - name: "Web Developer"
      priority: "high"
      trigger_conditions:
        - "any development work"
      mode: "mandatory"

    - name: "Test Engineer"
      priority: "high"
      trigger_conditions:
        - "after implementation"
      mode: "mandatory"
      quality_gate:
        metric: "test_coverage"
        threshold: 90
        blocking: true

    - name: "Documentation Engineer"
      priority: "medium"
      trigger_conditions:
        - "API changes"
      mode: "recommended"

  # Execution sequence
  sequence:
    type: "sequential"
    order:
      - "Web Developer"
      - "Security Reviewer"
      - "Test Engineer"
      - "Observability Engineer"
      - "Documentation Engineer"
      - "Git Committer"

    # Optional: parallel execution
    parallel_groups:
      - ["Security Reviewer", "Test Engineer"]

  # Quality gates
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
        blocking: false

    optional:
      - gate: "performance_check"
        threshold: 80
        blocking: false

  # Phase completion criteria
  completion_criteria:
    - "All mandatory agents have run"
    - "All blocking quality gates passed"
    - "All phase tasks marked complete"
    - "Code committed to git"

  # Rationale for orchestration decisions
  rationale: |
    This phase implements authentication endpoints which are security-critical.
    Security Reviewer runs with high priority to audit implementation.
    Test Engineer ensures comprehensive test coverage of auth logic.
    Observability Engineer verifies authentication events are properly logged.
```

##### Substep 6: Embed Orchestration in Phase Plan

Add orchestration section to phase plan document:

```markdown
# Phase Plan: v0.X.Y - [Phase Name]

[Existing phase plan content...]

---

## 🤖 Agent Orchestration

This section defines which agents will be used during this phase and how they'll be orchestrated.

```yaml
orchestration:
  [Generated YAML from Substep 5]
```

**Orchestration Rationale:**
[Generated rationale explaining why these agents, this sequence, and these quality gates]

**Expected Agent Execution:**
1. **Web Developer** - Implement authentication endpoints (3-4 hours)
2. **Security Reviewer** - Audit implementation for vulnerabilities (1 hour)
3. **Test Engineer** - Write comprehensive tests for auth logic (2 hours)
4. **Observability Engineer** - Verify auth logging (30 min)
5. **Documentation Engineer** - Document auth API endpoints (1 hour)
6. **Git Committer** - Commit phase work (15 min)

Total estimated agent time: ~8 hours
```

##### Substep 7: Validate Phase Size (Context Window Constraint)

**CRITICAL:** Each phase must fit within context window limits.

```python
# Calculate phase token count
phase_content_tokens = estimate_tokens(phase_tasks + phase_description)
orchestration_tokens = estimate_tokens(orchestration_yaml + rationale)
buffer_tokens = 1000

total_tokens = phase_content_tokens + orchestration_tokens + buffer_tokens

MAX_PHASE_TOKENS = 8000  # Leaves room for code context during execution

if total_tokens > MAX_PHASE_TOKENS:
    # Split phase into sub-phases
    print(f"⚠️ Phase {phase_name} exceeds context limit ({total_tokens} tokens)")
    print(f"Splitting into sub-phases...")

    sub_phases = split_phase_intelligently(
        phase,
        max_tokens=MAX_PHASE_TOKENS,
        preserve_orchestration_coherence=True
    )

    for sub_phase in sub_phases:
        generate_orchestration_rules(sub_phase)

    print(f"✓ Created {len(sub_phases)} sub-phases")
```

**Phase Splitting Guidelines:**
- Keep related tasks together
- Each sub-phase has its own orchestration
- Sub-phases reference each other for context
- Example: "Phase 2: Backend Implementation" → "Phase 2A: Auth Endpoints" + "Phase 2B: User Management"

##### Substep 8: Document Orchestration Design

Add summary to sprint plan:

```markdown
## 🤖 Sprint Orchestration Summary

This sprint uses **sprint-driven orchestration** where each phase has tailored agent orchestration rules.

**Phase 1: Research & Architecture**
- Primary Agents: Researcher, Security Reviewer, Diagram Engineer
- Focus: Design validation, security architecture review
- Quality Gates: Architecture security review (≥85)

**Phase 2: Frontend Implementation**
- Primary Agents: Web Developer, Test Engineer
- Focus: UI components with tests
- Quality Gates: Test coverage (≥90%)

**Phase 3: Backend Implementation**
- Primary Agents: Web Developer, Security Reviewer, Test Engineer, Observability Engineer
- Focus: Secure API implementation with comprehensive testing
- Quality Gates: Security (≥85), Test coverage (≥90%), Logging audit (≥80)

**Phase 4: Quality Assurance**
- Primary Agents: Security Reviewer, Test Engineer, Performance Engineer
- Focus: Comprehensive quality checks
- Quality Gates: Security (≥90), All tests passing, Performance acceptable

**Phase 5: Documentation & Deployment**
- Primary Agents: Documentation Engineer, Diagram Engineer, Git Committer
- Focus: Complete documentation and sprint finalization
- Quality Gates: Documentation complete

**Orchestration Strategy:**
Security-critical sprint with emphasis on Security Reviewer in multiple phases.
Test Engineer ensures high coverage throughout. Observability Engineer validates
logging for authentication events.
```

---

**Orchestration Design Complete:** All phases now have embedded orchestration rules that Claude will follow during sprint execution.

#### Step 3.4: Update Implementation Guide
**Action:** Add code/SQL/commands to implementation guide

**File Location:** `docs/sprints/v0.X.0/SPRINT_V0.X.0_IMPLEMENTATION_GUIDE.md`

**Structure:**
```markdown
# Implementation Guide: Sprint v0.X.0

**Sprint:** v0.X.0 - [Sprint Name]
**Created:** [Date]
**Status:** [IN_PROGRESS / COMPLETE]

---

## §X.1 Phase 1: [Phase Name]

[Complete code, SQL, commands, configuration for Phase 1]

---

## §X.2 Phase 2: [Phase Name]

[Complete code, SQL, commands, configuration for Phase 2]

...
```

**This file contains ALL code** - keeps phase plans concise.

---

### Phase 4: Roadmap Update (30 mins - 1 hour)

#### Step 4.1: Update Roadmap
**Action:** Add new sprint to product roadmap

**Location:** {% if config.custom.roadmap_location %}{{ config.custom.roadmap_location }}{% else %}`ROADMAP.md`{% endif %}

**Updates Required:**

1. **Current Sprint Status Section (top of file):**
```markdown
## 📍 Current Sprint Status

**Sprint:** v0.X.0 - [Sprint Name]
**Started:** [Date]
**Progress:** [N] of [M] phases complete ([P]%)

### ✅ Phase 1 Complete ([Date])
- [Achievement 1]
- [Achievement 2]

### 🚧 Phase 2 In Progress
- [Current work]

### 🎯 Next Actions
1. [Next action 1]
2. [Next action 2]
```

2. **Add to Sprint Timeline:**
```markdown
### v0.X.0 - [Sprint Name] (Weeks [START]-[END])
**Goal:** [One sentence goal]
**Duration:** [X weeks]
**Status:** [NOT_STARTED / IN_PROGRESS / COMPLETE]

**Key Deliverables:**
- [Deliverable 1]
- [Deliverable 2]

**Dependencies:** v0.PREV.0 complete

**Details:** [Link to sprint plan]
```

3. **Update Metrics:**
```markdown
**Current Version:** v0.X.0
**Key Metrics:** [Update project-specific metrics]
```

#### Step 4.2: Update Project Context
**Action:** Update current focus in .claude/CLAUDE.md

**Location:** `.claude/CLAUDE.md`

**Updates:**
```markdown
## 🚀 QUICK START

### Current Focus

**Sprint:** v0.X.0 - [Sprint Name]
**Status:** [Status description]
**Priority:** [What's most important right now]

**Current Phase:** v0.X.Y - [Phase Name]
[Brief description of current work]

**Next Actions:**
1. [Action 1]
2. [Action 2]
```

---

### Phase 5: Progress Tracking (Ongoing)

#### Step 5.1: Daily Progress Updates
**Action:** Track daily sprint progress

**What to Update:**
- Task completion status in phase plans
- Blockers and risks identified
- Test results and coverage
- Project metrics

**Update Frequency:** Daily during active sprints

#### Step 5.2: Weekly Sprint Reviews
**Action:** Conduct weekly sprint reviews

**Review Checklist:**
- [ ] Phase completion status
- [ ] Success criteria progress
- [ ] Blockers identified and escalated
- [ ] Scope changes needed?
- [ ] Timeline still realistic?

**Output:** Weekly status update in sprint plan

#### Step 5.3: Sprint Retrospectives
**Action:** Conduct retrospective at sprint end

**Retrospective Template:**
```markdown
# Sprint Retrospective: v0.X.0

**Sprint:** v0.X.0 - [Sprint Name]
**Completed:** [Date]
**Duration:** [Planned] vs [Actual]

## ✅ What Went Well
1. [Success 1]
2. [Success 2]

## ❌ What Didn't Go Well
1. [Challenge 1]
2. [Challenge 2]

## 💡 Lessons Learned
1. [Lesson 1]
2. [Lesson 2]

## 🔄 Process Improvements
1. [Improvement 1]
2. [Improvement 2]

## 📊 Metrics
- **Planned Duration:** [X weeks]
- **Actual Duration:** [Y weeks]
- **Velocity:** [Story points completed]
- **Test Coverage:** [%]

## 🎯 Impact
- [Impact metric 1]
- [Impact metric 2]
```

**Save Location:** `docs/sprints/v0.X.0/SPRINT_V0.X.0_RETROSPECTIVE.md`

---

## 📤 Output

### Primary Deliverables

1. **Sprint Plan (Main):**
   - `docs/sprints/v0.X.0/SPRINT_V0.X.0_PLAN.md`
   - Comprehensive sprint overview
   - 100-200 lines
   - WHAT/WHY focused

2. **Phase Plans:**
   - `docs/sprints/v0.X.0/SPRINT_V0.X.Y_PLAN.md` (one per phase)
   - Detailed phase objectives and tasks
   - 75-120 lines each
   - WHAT/WHY focused

3. **Implementation Guide:**
   - `docs/sprints/v0.X.0/SPRINT_V0.X.0_IMPLEMENTATION_GUIDE.md`
   - ALL code, SQL, commands
   - Organized by §X.Y sections
   - No line limit

4. **Roadmap Updates:**
   - {% if config.custom.roadmap_location %}{{ config.custom.roadmap_location }}{% else %}`ROADMAP.md`{% endif %} - Updated with new sprint
   - `.claude/CLAUDE.md` - Updated current focus

### Supporting Documents

5. **Dependency Analysis:**
   - Dependency graph (Mermaid diagram)
   - Blocking/blocked by relationships
   - Parallel track identification

6. **Risk Assessment:**
   - Risk register with mitigation strategies
   - Critical path analysis
   - Contingency planning

7. **Sprint Retrospective** (after completion):
   - `docs/sprints/v0.X.0/SPRINT_V0.X.0_RETROSPECTIVE.md`
   - Lessons learned
   - Process improvements

---

## 📊 Quality Gates

**Sprint Plan Quality:**
- [ ] Clear, measurable objectives
- [ ] Dependencies identified and validated
- [ ] Realistic effort estimates
- [ ] Success criteria defined
{% if config.quality_gates and config.quality_gates.security_review and config.quality_gates.security_review.enabled %}- [ ] Security review scheduled{% endif %}

**Documentation Quality:**
- [ ] All templates followed
- [ ] Cross-references correct
- [ ] File structure organized

**Prioritization Quality:**
- [ ] Business value justified
- [ ] Technical dependencies mapped
- [ ] Parallel opportunities identified
- [ ] MVP before advanced features

---

## 🎯 Best Practices

### Do's ✅

1. **Start with Current State:** Always read .claude/CLAUDE.md and roadmap first
2. **Dependency-First:** Unblock early, sequence by dependencies
3. **Parallel Tracks:** Identify independent work that can run concurrently
4. **Clear Success Criteria:** Make Definition of Done measurable
5. **Regular Updates:** Keep roadmap and .claude/CLAUDE.md current
{% if config.quality_gates and config.quality_gates.security_review and config.quality_gates.security_review.enabled %}6. **Security Mandatory:** Every sprint ends with security review{% endif %}
7. **Realistic Estimates:** Account for testing, documentation, reviews
8. **Value Streams:** Group related features for coherent sprints

### Don'ts ❌

1. **Don't Waterfall:** Avoid purely sequential sprints when parallelization is possible
2. **Don't Skip Dependencies:** Don't schedule dependent work before dependencies complete
3. **Don't Overload:** Keep sprints to 6-8 weeks max (break into phases if larger)
4. **Don't Skip Testing:** {{ 20 if not config.quality_gates or not config.quality_gates.unit_testing else 'Significant' }}% of sprint time for testing
{% if config.quality_gates and config.quality_gates.security_review and config.quality_gates.security_review.enabled %}5. **Don't Defer Security:** Security review at end of EVERY sprint (mandatory){% endif %}
6. **Don't Skip Docs:** Update roadmap and .claude/CLAUDE.md with every sprint change
7. **Don't Plan in Isolation:** Consider team velocity and capacity

### Sprint Planning Principles

**Principle 1: Dependencies Before Features**
Infrastructure and foundations before features that depend on them.

**Principle 2: Quality Matters**
{% if config.quality_gates %}Maintain quality gates throughout development.{% else %}Maintain quality standards throughout development.{% endif %}

{% if config.quality_gates and config.quality_gates.security_review and config.quality_gates.security_review.enabled %}**Principle 3: Security Is Not Optional**
MANDATORY security review at end of every sprint. All critical issues must be fixed.
{% endif %}

**Principle 4: Test Everything**
{{ config.coding_standards.test_coverage.minimum if config.coding_standards and config.coding_standards.test_coverage else 90 }}%+ coverage required for all new code.

**Principle 5: Document as You Go**
Update docs with every sprint. Roadmap and .claude/CLAUDE.md are living documents.

**Principle 6: Value Early, Often**
Deliver value incrementally. MVP before advanced features.

**Principle 7: Parallel When Possible**
Independent work streams should run concurrently. Don't artificially serialize.

---

## 🛠️ Tools & Commands

**Essential Commands:**
```bash
# Read current state
cat .claude/CLAUDE.md
cat {% if config.custom.roadmap_location %}{{ config.custom.roadmap_location }}{% else %}ROADMAP.md{% endif %}

# Check recent work
git log --oneline -20
git status

# Find existing sprint plans
ls -la docs/sprints/v*/SPRINT_V*_PLAN.md

# Check test coverage
{% if config.technology_stack.backend.language == 'python' %}pytest --cov={{ config.project.name }}{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}npm test -- --coverage{% elif config.technology_stack.backend.language == 'java' %}mvn test jacoco:report{% endif %}
```

**Dependency Analysis Tools:**
```bash
# Find blockers in codebase
grep -r "TODO" src/
grep -r "FIXME" src/
```

---

## 📚 Examples

### Example 1: Simple Feature Sprint

**Requirement:** Add user authentication

**Analysis:**
- Dependencies: Database setup
- Effort: 1 week
- Priority: High (blocks user features)

**Sprint Plan:**
```yaml
Sprint: v0.2.0
Duration: 1 week (5 days)
Dependencies: v0.1.0 (database) complete
Deliverable: User authentication working

Phases:
  Days 1-2: Auth system implementation
  Days 3-4: Tests and integration
  Day 5: Documentation and review
```

### Example 2: Complex Multi-Phase Sprint

**Requirement:** Production Deployment

**Analysis:**
- Dependencies: Infrastructure, core features
- Effort: 3-4 weeks
- Priority: Critical (blocks users)

**Sprint Plan:**
```yaml
Sprint: v0.5.0 - Production Deployment
Duration: 4 weeks (20 days)
Dependencies: v0.3.0 (infrastructure), v0.4.0 (features)
Deliverables: Live production environment, CI/CD, monitoring

Phases:
  Phase 1 (Days 1-5): Environment setup, CI/CD
  Phase 2 (Days 6-10): Data migration, validation
  Phase 3 (Days 11-15): User access, authentication
  Phase 4 (Days 16-19): Load testing, optimization
  Day 20: {% if config.quality_gates and config.quality_gates.security_review and config.quality_gates.security_review.enabled %}Security review (MANDATORY){% else %}Final review{% endif %}
```

### Example 3: Parallel Track Sprint

**Requirement:** Core Features + Infrastructure

**Analysis:**
- Two independent work streams
- Can run concurrently
- Reduces total time from 8 weeks to 5 weeks

**Sprint Plan:**
```yaml
Sprint: v0.3.0 - Core Features (Track 1)
Duration: 4-5 weeks
Effort: 70% team capacity
Parallel with: v0.4.0 - Infrastructure (Track 2, 30% effort)

Benefits:
  - Get features AND infrastructure done together
  - Reduce time to value
  - No artificial blocking
```

---

## 🚨 Common Pitfalls

### Pitfall 1: Waterfall Sequencing
**Problem:** Scheduling all sprints sequentially when parallelization is possible
**Solution:** Identify independent work streams and run concurrently

### Pitfall 2: Ignoring Dependencies
**Problem:** Scheduling sprints before their dependencies are complete
**Solution:** Build dependency graph, sequence by critical path

### Pitfall 3: Scope Creep
**Problem:** Sprints become too large (>8 weeks)
**Solution:** Break into smaller sprints or phases, deliver incrementally

{% if config.quality_gates and config.quality_gates.security_review and config.quality_gates.security_review.enabled %}
### Pitfall 4: Skipping Security
**Problem:** Deferring security reviews to "later"
**Solution:** MANDATORY security review at end of EVERY sprint
{% endif %}

### Pitfall 5: Optimistic Estimates
**Problem:** Underestimating effort, missing deadlines
**Solution:** Add 20% buffer, account for testing and documentation

### Pitfall 6: Documentation Debt
**Problem:** Not updating roadmap and .claude/CLAUDE.md
**Solution:** Update docs as part of sprint planning workflow

---

## 📈 Success Metrics

**Sprint Planning Effectiveness:**
- **On-Time Delivery:** >80% of sprints complete on schedule
- **Scope Accuracy:** <20% scope changes mid-sprint
- **Dependency Management:** Zero critical path blockers discovered mid-sprint
{% if config.quality_gates and config.quality_gates.security_review and config.quality_gates.security_review.enabled %}- **Security Compliance:** 100% of sprints have security review{% endif %}
- **Documentation Currency:** Roadmap and .claude/CLAUDE.md updated within 24 hours

**Planning Quality:**
- **Dependency Accuracy:** >90% of dependencies identified upfront
- **Effort Estimation:** <20% variance from estimates
- **Parallel Utilization:** >50% of possible parallel work identified
- **Value Delivery:** Incremental value every 2-4 weeks

---

## 🎓 Decision Framework

### When to Create New Sprint vs Extend Existing

**Create New Sprint When:**
- Major architectural change
- New category of work
- Dependencies require sequential execution
- >4 weeks of work

**Extend Existing Sprint When:**
- Related work in same category
- Natural continuation of current sprint
- <2 weeks of work
- No new dependencies

### When to Parallelize vs Sequence

**Parallelize When:**
- No technical dependencies between work
- Different team members can work independently
- Infrastructure + features can coexist
- Reduces total time by >20%

**Sequence When:**
- Strong technical dependencies
- Shared resources (same files, same systems)
- Learning from one informs the other
- Risk of conflicts or rework

### When to Prioritize Technical Debt

**High Priority When:**
- Blocking new features
- Security vulnerabilities
- Production incidents
- Technical debt interest > 20% of velocity

**Medium Priority When:**
- Slowing development
- Code quality issues
- Test coverage gaps
- Documentation outdated

**Low Priority When:**
- Cosmetic issues
- Nice-to-have refactors
- Not impacting delivery

---

## 🤖 Agent Routing Integration

**Added in v2.1:** Integration with automated agent routing system.

### Using Agent Recommendations During Planning

When creating sprint plans, use the agent routing utilities to get intelligent agent recommendations for tasks:

```python
# Get agent recommendations for a sprint's tasks
from vibey.cli.roadmap_lib.agents import (
    enhance_sprint_with_agent_recommendations,
    plan_sprint_agents,
    detect_parallel_tasks,
    get_task_execution_order,
)

# Analyze sprint and get agent recommendations
recommendations = enhance_sprint_with_agent_recommendations(
    sprint_id="roadmap-system-5",
    auto_assign=False,  # Set True to auto-assign high-confidence matches
    min_confidence=0.5
)

# Plan agent assignments with workload balancing
assignments = plan_sprint_agents(
    sprint_id="roadmap-system-5",
    balance_workload=True  # Distribute work across agents
)

# Detect which tasks can run in parallel
parallel_info = detect_parallel_tasks(sprint_id="roadmap-system-5")

# Get optimal execution order (tasks grouped by phase)
execution_phases = get_task_execution_order(sprint_id="roadmap-system-5")
```

### CLI Commands for Agent Routing

```bash
# Get agent recommendations for a sprint
vibey roadmap recommend-agents --sprint roadmap-system-5

# Show current agent workloads
vibey roadmap agent-workload

# Detect parallel tasks in a sprint
vibey roadmap parallel-tasks --sprint roadmap-system-5
```

### Agent Assignment Best Practices

1. **Use recommendations as guidance** - Human review of automated suggestions
2. **Balance workload** - Don't overload a single agent type
3. **Consider task dependencies** - Sequential tasks may need same agent
4. **Review confidence scores** - Low scores (<0.3) need manual assignment
5. **Track assignment effectiveness** - Monitor completion rates by agent

### Parallel Task Execution

During sprint execution, tasks can be parallelized when:
- No dependency relationships exist between them
- Different agents can handle them simultaneously
- Resources don't conflict (different files/systems)

Use `detect_parallel_tasks()` during planning to identify parallelization opportunities and reduce sprint duration.

---

**End of Sprint Planning Agent Instructions**

**Agent Version:** 2.1 (Agent Routing Integration)
**Framework:** Vibey Agent Framework
**Last Updated:** 2025-11-22
