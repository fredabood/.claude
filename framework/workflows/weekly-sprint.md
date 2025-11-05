# Workflow: Weekly Sprint

**Workflow ID:** Weekly Sprint
**Purpose:** Execute parallel feature development for weekly sprint completion
**Duration:** 3-5 days (3-7 features/components)
**Complexity:** High

---

## Overview

This workflow orchestrates parallel implementation of multiple related features or components, then integrates and documents them as a weekly unit. The key insight is **parallelization** - multiple development tracks run simultaneously, converging in integration and documentation phases.

**Use Cases:**
{% if config.project.type == 'web-app' %}- Parallel component development (3-7 UI components or API endpoints){% elif config.project.type == 'api' %}- Parallel endpoint development (3-7 REST endpoints){% elif config.project.type == 'data-platform' %}- Parallel data source integration (3-7 data sources){% elif config.project.type == 'ml' %}- Parallel model development (2-5 ML models){% else %}- Parallel feature development (3-7 related features){% endif %}
- Weekly sprint execution with multiple deliverables
- Batch integration and deployment
- Coordinated documentation across features

**Key Characteristics:**
- Multiple features built in parallel (Phase 1)
- Single integration phase for all features (Phase 2)
- Single week summary document (Phase 3)
- Single commit for entire week's work

**Prerequisites:**
- Week plan with list of features/components
- Category or theme for the week
- Expected completion date
- Development environment ready
- Access to necessary tools and services

---

## Workflow Phases

### Overview

```
PARALLEL PHASE (Days 1-3):
For each feature (parallel):
  1. {% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architect{% endif %} → Design specification
  2. {% if config.project.type == 'web-app' %}Web Developer{% elif config.project.type == 'api' %}API Developer{% elif config.project.type == 'ml' %}ML Engineer{% else %}Developer{% endif %} → Implementation
  3. Test Engineer → Comprehensive testing
  4. Security Reviewer → Security review

INTEGRATION PHASE (Day 4):
  5. Integration Engineer → Integrate all features

DOCUMENTATION PHASE (Day 5):
  6. Documentation Engineer → Create week summary
  7. Git Committer → Commit entire week
```

---

## Prerequisites Template

Before starting, you must have:

**1. Week Plan:**
```markdown
Week [X]: [Category/Theme]
Features/Components:
1. [Feature 1 name]
2. [Feature 2 name]
3. [Feature 3 name]
Target Completion: YYYY-MM-DD
```

{% if config.project.type == 'web-app' %}**Example:**
```
Week 7: User Dashboard Components
Features:
1. Profile Management Component
2. Activity Feed Component
3. Notifications Widget
Target: 2025-11-15
```{% elif config.project.type == 'api' %}**Example:**
```
Week 7: Analytics API Endpoints
Endpoints:
1. GET /api/analytics/users
2. GET /api/analytics/revenue
3. POST /api/analytics/custom-report
Target: 2025-11-15
```{% elif config.project.type == 'data-platform' %}**Example:**
```
Week 7: Financial Data Sources
Sources:
1. Stock Market API (Alpha Vantage)
2. Cryptocurrency API (CoinGecko)
3. Economic Indicators API (FRED)
Target: 2025-11-15
```{% else %}**Example:**
```
Week 7: Core Feature Set
Features:
1. User Authentication
2. Data Export
3. Admin Dashboard
Target: 2025-11-15
```{% endif %}

**2. Access & Credentials:**
- {% if config.ci_cd %}{{ config.ci_cd.platform or 'CI/CD' }}{% else %}CI/CD{% endif %} access
{% if config.cloud_provider %}- {{ config.cloud_provider }} credentials{% endif %}
- Development environment configured
{% if config.project.type == 'data-platform' %}- API keys for data sources{% endif %}

**3. Development Environment:**
{% if config.technology_stack and config.technology_stack.backend.language == 'python' %}```bash
# Python environment
pip install -e ".[dev]"
pytest --version
{% if config.linter %}{{ config.linter }} --version{% else %}ruff --version{% endif %}
```{% elif config.technology_stack and config.technology_stack.backend.language in ['javascript', 'typescript'] %}```bash
# Node.js environment
npm install
npm test
npm run lint
```{% elif config.technology_stack and config.technology_stack.backend.language == 'java' %}```bash
# Java environment
mvn clean install
mvn test
mvn checkstyle:check
```{% else %}```bash
# Development environment
# Install dependencies
# Run tests
# Run linter
```{% endif %}

---

## Phase 1: Parallel Implementation (Days 1-3)

**For each feature/component, run in parallel:**

### Step 1A: Architecture & Design (Parallel)

**Agent:** {% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architecture Specialist{% endif %}
**Duration:** 0.5-1 day per feature
**Output:** Design specifications for all features

**Activation Prompts (run for each feature):**

```markdown
[Feature 1]:
You are the {% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architecture Specialist{% endif %} subagent.
{% if config.architecture %}Read: agents/architecture/{{ config.architecture.specialist | lower | replace(' ', '-') }}.md{% else %}Read: agents/architecture/architecture-specialist.md{% endif %}

Task: Design specification for [Feature 1 Name]

Requirements: [Specific requirements]
{% if config.architecture %}Architecture Pattern: {{ config.architecture.pattern }}{% endif %}
{% if config.project.type == 'web-app' %}UI/UX Guidelines: [Link to design system]{% endif %}

Create: {% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/design-spec-feature1.md

---

[Feature 2]:
[Repeat for each feature]
```

**Strategy:**
- Can work on multiple specs simultaneously
- Complete simpler features first
- More complex features may take longer
- Review dependencies between features

**Deliverables:**
- `{% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/design-spec-feature1.md`
- `{% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/design-spec-feature2.md`
- `{% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/design-spec-feature3.md`

**Handoff:** Pass specifications to Development Agent

---

### Step 1B: Implementation (Parallel)

**Agent:** {% if config.project.type == 'web-app' %}Web Developer{% elif config.project.type == 'api' %}API Developer{% elif config.project.type == 'ml' %}ML Engineer{% else %}Development Agent{% endif %}
**Duration:** 1-2 days per feature
**Output:** Implemented features

**Activation Prompts (run for each feature as specs complete):**

```markdown
[Feature 1]:
You are the {% if config.project.type == 'web-app' %}Web Developer{% elif config.project.type == 'api' %}API Developer{% elif config.project.type == 'ml' %}ML Engineer{% else %}Development Agent{% endif %} subagent.
{% if config.project.type == 'web-app' %}Read: agents/development/web-developer.md{% elif config.project.type == 'api' %}Read: agents/development/api-developer.md{% elif config.project.type == 'ml' %}Read: agents/development/ml-engineer.md{% else %}Read: agents/development/developer.md{% endif %}

Task: Implement [Feature 1 Name]
Input: {% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/design-spec-feature1.md

Create:
{% if config.project.type == 'web-app' and config.web_framework and config.web_framework.frontend == 'react' %}- src/components/Feature1Component.tsx
- src/services/feature1Service.ts{% elif config.project.type == 'api' and config.technology_stack and config.technology_stack.backend.language == 'python' %}- src/api/routes/feature1.py
- src/api/models/feature1.py{% elif config.project.type == 'ml' and config.technology_stack and config.technology_stack.backend.language == 'python' %}- src/models/feature1_model.py
- src/training/feature1_training.py{% else %}- src/feature1/implementation{% endif %}
- test_feature1_manual.{% if config.technology_stack %}{{ config.technology_stack.backend.test_extension or 'py' }}{% else %}py{% endif %}
- {% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/impl-feature1.md

---

[Feature 2]:
[Repeat for each feature]
```

**Strategy:**
- Start implementing as soon as spec is ready
- Can implement multiple features in parallel
- Run manual tests to verify each works
- Document any deviations from spec

**Deliverables:**
{% if config.project.type == 'web-app' %}- Implementation files (components, services, styles)
- Manual test scripts{% elif config.project.type == 'api' %}- Route handlers and models
- Manual API tests (Postman/curl){% elif config.project.type == 'ml' %}- Model implementations
- Training scripts and notebooks{% else %}- Implementation files
- Manual test scripts{% endif %}
- Handoff documents

**Handoff:** Pass implementations to Test Engineer

---

### Step 1C: Testing (Parallel)

**Agent:** Test Engineer
**Duration:** 0.5-1 day per feature
**Output:** Comprehensive test suites

**Activation Prompts (run for each feature as implementation completes):**

```markdown
[Feature 1]:
You are the Test Engineer subagent.
Read: agents/quality/test-engineer.md

Task: Write comprehensive test suite for [Feature 1 Name]
Input:
- Implementation: [Implementation files]
- Handoff: {% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/impl-feature1.md

Target: {{ config.test_coverage_target or '85' }}%+ coverage, all tests passing

Create:
{% if config.technology_stack and config.technology_stack.backend.language == 'python' %}- tests/test_feature1.py{% elif config.technology_stack and config.technology_stack.backend.language in ['javascript', 'typescript'] %}- tests/feature1.test.ts{% elif config.technology_stack and config.technology_stack.backend.language == 'java' %}- src/test/java/com/example/Feature1Test.java{% else %}- tests/test_feature1{% endif %}
- {% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/test-complete-feature1.md

---

[Feature 2]:
[Repeat for each feature]
```

**Strategy:**
- Write tests as implementations complete
- Can test multiple features in parallel
- Aim for consistent coverage across all features
- Include unit, integration, and {% if config.project.type == 'web-app' %}component{% else %}functional{% endif %} tests

**Deliverables:**
- Test files for each feature
- Test execution reports
- Coverage reports (target: {{ config.test_coverage_target or '85' }}%+)
- Test handoff documents

**Handoff:** Pass test results to Security Reviewer

---

### Step 1D: Security Review (Parallel)

**Agent:** Security Reviewer
**Duration:** 0.25-0.5 days per feature
**Output:** Security review reports

**Activation Prompts (run for each feature as tests complete):**

```markdown
[Feature 1]:
You are the Security Reviewer subagent.
Read: agents/quality/security-reviewer.md

Task: Conduct security review of [Feature 1 Name]

Input:
- Implementation: [Implementation files]
- Tests: [Test files]
- Test Results: {% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/test-complete-feature1.md

Review for:
{% if config.project.type == 'web-app' %}- XSS, CSRF, injection attacks
- Authentication/authorization issues
- Client-side data exposure{% elif config.project.type == 'api' %}- SQL injection, API abuse
- Authentication/authorization
- Rate limiting and DoS{% elif config.project.type == 'ml' %}- Model poisoning, data leakage
- Input validation
- Inference security{% else %}- Input validation
- Authentication/authorization
- Data exposure{% endif %}

Create:
- {% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/security-review-feature1.md

---

[Feature 2]:
[Repeat for each feature]
```

**Strategy:**
- Review as tests complete
- Can review multiple features in parallel
- All must be APPROVED before integration phase
- Document all findings (critical/high/medium/low)

**Deliverables:**
- Security review reports (APPROVED/REJECTED)
- Vulnerability findings (if any)
- Remediation recommendations

**Quality Gate:** All features must have security APPROVED to proceed to Phase 2

**Handoff:** Pass approved features to Integration Engineer

---

## Phase 2: Integration (Day 4)

**After all features are implemented, tested, and security approved:**

### Step 2: Integration Engineering

**Agent:** Integration Engineer
**Duration:** 0.5-1 day
**Input:** All approved features
**Output:** Integrated system

**Activation Prompt:**

```markdown
You are the Integration Engineer subagent.
Read: agents/development/integration-engineer.md

Task: Integrate ALL Week [X] features into {{ config.project.name or 'the system' }}

Features to integrate:
1. [Feature 1] - [Brief description]
   {% if config.project.type == 'web-app' %}- Component: [Component name]
   - Route: [Route path]{% elif config.project.type == 'api' %}- Endpoint: [Endpoint path]
   - Method: [HTTP method]{% elif config.project.type == 'data-platform' %}- Data source: [Source name]
   - Update frequency: [Frequency]{% endif %}

2. [Feature 2] - [Brief description]
   [Similar details]

3. [Feature 3] - [Brief description]
   [Similar details]

For each feature:
{% if config.project.type == 'web-app' %}1. Register routes in router configuration
2. Add navigation links (if applicable)
3. Integrate with state management
4. Test UI integration{% elif config.project.type == 'api' %}1. Register routes in API router
2. Add to API documentation
3. Configure middleware (auth, validation)
4. Test endpoint integration{% elif config.project.type == 'data-platform' %}1. Register in data source registry
2. Add fetch methods to main interface
3. Configure caching/rate limiting
4. Test data integration{% else %}1. Register in main application
2. Configure dependencies
3. Test integration{% endif %}

Create:
{% if config.technology_stack and config.technology_stack.backend.language == 'python' %}- tests/test_integration_week{{ '{X}' }}.py{% elif config.technology_stack and config.technology_stack.backend.language in ['javascript', 'typescript'] %}- tests/integration/week{{ '{X}' }}.test.ts{% else %}- tests/test_integration_week{{ '{X}' }}{% endif %}
- {% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/integration-complete-week{{ '{X}' }}.md
```

**Strategy:**
- Integrate features one at a time
- Test each integration before moving to next
- Create one comprehensive integration test for all features
- Verify no conflicts or regressions

**Deliverables:**
{% if config.project.type == 'web-app' %}- Updated router configuration
- Updated navigation/menu
- Integration tests{% elif config.project.type == 'api' %}- Updated API router
- Updated API documentation
- Integration tests{% elif config.project.type == 'data-platform' %}- Updated data source registry
- Updated main data interface
- Integration tests{% else %}- Updated application configuration
- Integration tests{% endif %}
- Integration handoff document

**Quality Check:**
{% if config.technology_stack and config.technology_stack.backend.language == 'python' %}```bash
# Test all features work together
pytest tests/test_integration_week{{ '{X}' }}.py -v
```{% elif config.technology_stack and config.technology_stack.backend.language in ['javascript', 'typescript'] %}```bash
# Test all features work together
npm test tests/integration/week{{ '{X}' }}.test.ts
```{% else %}```bash
# Run integration tests
[test command]
```{% endif %}

**Handoff:** Pass integration results to Documentation Engineer

---

## Phase 3: Documentation (Day 5)

**After all features are integrated:**

### Step 3A: Documentation Engineering

**Agent:** Documentation Engineer
**Duration:** 0.5-1 day
**Input:** Integration results, test results, security reviews
**Output:** Comprehensive week summary

**Activation Prompt:**

```markdown
You are the Documentation Engineer subagent.
Read: agents/documentation/documentation-engineer.md

Task: Document Week [X] completion - [Category/Theme]

Input:
- Integration: {% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/integration-complete-week{{ '{X}' }}.md
- Security reviews: {% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/security-review-feature*.md
- Test results: {% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/test-complete-feature*.md

Week Details:
- Week: [X]
- Category: [Category/Theme]
- Features: [Count] ([Feature 1], [Feature 2], [Feature 3])
- Tests: [Total] total, [Passing] passing, avg [Coverage]% coverage
- Sprint Progress: [X]% ([Completed]/[Total] weeks complete)

Updates needed:

1. {% if config.documentation.main_doc %}{{ config.documentation.main_doc }}{% else %}CLAUDE.md{% endif %}
   - Update "Last Updated" to [Date]
   - Mark "Week [X] Complete" in Current Focus
   - Add all features to implementation status
   - Update feature counts
   - Add new components/endpoints to "Key Files" section

2. {% if config.custom.roadmap_location %}{{ config.custom.roadmap_location }}{% else %}ROADMAP.md{% endif %}
   - Mark Week [X] complete
   - Update sprint progress
   - Update overall feature counts

3. docs/sprints/v{{ '{X}' }}.{{ '{Y}' }}/WEEK_{{ '{X}' }}_COMPLETE.md
   - Create comprehensive week summary
   - Include all features with details
   - Integration status for all
   - Test summary table
   {% if config.project.type == 'web-app' %}- UI screenshots (if applicable){% elif config.project.type == 'api' %}- API documentation links{% elif config.project.type == 'data-platform' %}- Data coverage summary{% endif %}
   - Known issues (if any)

4. [Optional] Create individual feature documentation if needed

Create:
- {% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/docs-complete-week{{ '{X}' }}.md
```

**Deliverables:**
- Updated {% if config.documentation.main_doc %}{{ config.documentation.main_doc }}{% else %}CLAUDE.md{% endif %}
- Updated {% if config.custom.roadmap_location %}{{ config.custom.roadmap_location }}{% else %}ROADMAP.md{% endif %}
- New `docs/sprints/v{X}.{Y}/WEEK_{X}_COMPLETE.md`
- Documentation handoff

**Quality Check:**
{% if config.documentation.size_check_script %}```bash
# Verify documentation sizes
{{ config.documentation.size_check_script }}

# Review changes
git diff docs/
```{% else %}```bash
# Review documentation changes
git diff docs/
```{% endif %}

**Handoff:** Pass documentation to Git Committer

---

### Step 3B: Git Commit & Push

**Agent:** Git Committer
**Duration:** 0.25 days
**Input:** Documentation handoff
**Output:** Committed and pushed changes

**Activation Prompt:**

```markdown
You are the Git Committer subagent.
Read: agents/documentation/git-committer.md

Task: Commit Week [X] - [Category/Theme] ([Count] features)

Input:
- Documentation handoff: {% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/docs-complete-week{{ '{X}' }}.md

Commit message format:

```
feat: Complete Week [X] - [Category/Theme] ([Count]/[Count] features, [Tests]/[Tests] tests)

Implemented [Count] [category] features:

1. [Feature 1 Name]
   {% if config.project.type == 'web-app' %}- Component: [Component path]
   - Route: [Route path]{% elif config.project.type == 'api' %}- Endpoint: [Endpoint path]
   - Method: [HTTP method]{% elif config.project.type == 'data-platform' %}- Data source: [Source name]
   - Geographic level: [Level]{% endif %}
   - Tests: [X]/[X] passing, [Coverage]% coverage
   - [Key details]

2. [Feature 2 Name]
   [Similar format]

3. [Feature 3 Name]
   [Similar format]

Week [X] Summary:
- Total features: [Count]/[Count] (100% complete)
- Total tests: [Tests]/[Tests] passing (100% pass rate)
- Average coverage: [Coverage]%
- Security: All features APPROVED

Sprint Progress: [X]% ([Completed]/[Total] weeks, [Total Features] features total)

Files Modified:
- [Implementation files]
- [Test files]
{% if config.project.type == 'web-app' %}- [Router configuration]
- [Navigation components]{% elif config.project.type == 'api' %}- [API router]
- [API documentation]{% elif config.project.type == 'data-platform' %}- [Data source registry]
- [Main data interface]{% endif %}
- {% if config.documentation.main_doc %}{{ config.documentation.main_doc }}{% else %}CLAUDE.md{% endif %} (Week [X] complete, [Total Features] features)
- {% if config.custom.roadmap_location %}{{ config.custom.roadmap_location }}{% else %}ROADMAP.md{% endif %} (Week [X] complete, sprint [X]%)
- docs/sprints/v{{ '{X}' }}.{{ '{Y}' }}/WEEK_{{ '{X}' }}_COMPLETE.md
```

Files to stage:
- All implementation files
- All test files
- Updated configuration/registry files
- Updated documentation files

Steps:
1. Review changes (git status, git diff)
2. Check for secrets
3. Stage all files
4. Run final checks (tests, docs, code quality)
5. Commit with message above
6. Push to remote

Create:
- {% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/commit-complete-week{{ '{X}' }}.md
```

**Quality Check:**
{% if config.technology_stack and config.technology_stack.backend.language == 'python' %}```bash
# All tests must pass
pytest tests/ -v

# Code quality
black src/ tests/
ruff check src/ tests/
mypy src/
```{% elif config.technology_stack and config.technology_stack.backend.language in ['javascript', 'typescript'] %}```bash
# All tests must pass
npm test

# Code quality
npm run lint
npm run type-check
```{% elif config.technology_stack and config.technology_stack.backend.language == 'java' %}```bash
# All tests must pass
mvn test

# Code quality
mvn checkstyle:check
mvn pmd:check
```{% else %}```bash
# Run all tests
[test command]

# Run code quality checks
[linter command]
```{% endif %}

**Deliverables:**
- One commit with all Week [X] changes
- Pushed to remote
- Commit handoff document

**Completion:** Weekly sprint workflow complete

---

## Workflow Diagram

```mermaid
graph TB
    subgraph "Phase 1: Parallel Implementation"
    A1[{% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architect{% endif %}<br/>Design Feature 1]
    A2[{% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architect{% endif %}<br/>Design Feature 2]
    A3[{% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architect{% endif %}<br/>Design Feature 3]

    B1[Developer<br/>Implement Feature 1]
    B2[Developer<br/>Implement Feature 2]
    B3[Developer<br/>Implement Feature 3]

    C1[Test Engineer<br/>Test Feature 1]
    C2[Test Engineer<br/>Test Feature 2]
    C3[Test Engineer<br/>Test Feature 3]

    D1[Security<br/>Review Feature 1]
    D2[Security<br/>Review Feature 2]
    D3[Security<br/>Review Feature 3]

    A1 --> B1 --> C1 --> D1
    A2 --> B2 --> C2 --> D2
    A3 --> B3 --> C3 --> D3
    end

    subgraph "Phase 2: Integration"
    E[Integration Engineer<br/>Integrate All Features]
    D1 --> E
    D2 --> E
    D3 --> E
    end

    subgraph "Phase 3: Documentation"
    F[Documentation Engineer<br/>Week Summary]
    G[Git Committer<br/>Commit & Push]
    E --> F --> G
    end
```

---

## Duration Estimates

| Phase | Activities | Duration | Cumulative |
|-------|-----------|----------|------------|
| **Phase 1A: Design** | Architecture specs for 3 features | 0.5-1 day | Day 1 |
| **Phase 1B: Implementation** | Parallel development | 1-2 days | Day 2-3 |
| **Phase 1C: Testing** | Parallel testing | 0.5-1 day | Day 3 |
| **Phase 1D: Security** | Parallel security reviews | 0.25-0.5 day | Day 3.5 |
| **Phase 2: Integration** | Integrate all features | 0.5-1 day | Day 4 |
| **Phase 3A: Documentation** | Week summary docs | 0.5-1 day | Day 4.5 |
| **Phase 3B: Commit** | Git commit and push | 0.25 day | Day 5 |
| **Total** | | **3-5 days** | **~1 week** |

**Scaling:**
- 3 features: 3-4 days
- 5 features: 4-5 days
- 7 features: 5-6 days

---

## Success Criteria

### Phase 1 - Parallel Implementation
- [ ] All architecture specs completed
- [ ] All features implemented
- [ ] All test suites completed (100% passing, {{ config.test_coverage_target or '85' }}%+ avg coverage)
- [ ] All security reviews completed (all APPROVED)

### Phase 2 - Integration
- [ ] All features integrated into main system
{% if config.project.type == 'web-app' %}- [ ] All routes registered
- [ ] Navigation updated{% elif config.project.type == 'api' %}- [ ] All endpoints registered
- [ ] API documentation updated{% elif config.project.type == 'data-platform' %}- [ ] All sources registered
- [ ] Main data interface updated{% endif %}
- [ ] Integration test passes for all features

### Phase 3 - Documentation
- [ ] {% if config.documentation.main_doc %}{{ config.documentation.main_doc }}{% else %}CLAUDE.md{% endif %} updated with all features
- [ ] {% if config.custom.roadmap_location %}{{ config.custom.roadmap_location }}{% else %}ROADMAP.md{% endif %} updated with week completion
- [ ] WEEK_[X]_COMPLETE.md created
{% if config.documentation.size_check_script %}- [ ] Doc size check passes{% endif %}
- [ ] All changes committed and pushed

---

## Common Issues & Solutions

### Issue: One Feature Failing Tests
**Problem:** Features 1 and 2 tests pass, Feature 3 failing

**Solution:**
1. Don't proceed to integration until all tests pass
2. Fix failing tests for Feature 3
3. Re-run test engineer for Feature 3
4. Re-run security reviewer for Feature 3
5. Then proceed to integration phase

---

### Issue: Security Review Rejected for One Feature
**Problem:** 2 features APPROVED, 1 feature REJECTED

**Solution:**
1. Fix critical security issues in rejected feature
2. Re-run security reviewer
3. Don't proceed to integration until all features APPROVED

---

### Issue: Integration Test Fails
**Problem:** Individual features work, but integration test fails

**Solution:**
1. Test each feature individually
2. Check for naming conflicts
3. Check for import errors
4. Verify all features registered correctly
5. Check integration test code for bugs

---

### Issue: Week Running Long
**Problem:** Day 4, still implementing features

**Solution:**
1. Prioritize features by importance
2. Complete high-priority features fully
3. Move lower-priority features to next week if needed
4. Document which features deferred and why

---

{% if config.documentation.size_check_script %}### Issue: Doc Size Check Fails
**Problem:** Main documentation too large after adding multiple features

**Solution:**
1. Create detailed feature docs in separate files
2. Keep only summaries in main documentation
3. Use links to detailed docs
4. Consider consolidating older week summaries

---
{% endif %}

## Comparison with Single Feature Workflow

| Aspect | Single Feature | Weekly Sprint |
|--------|---------------|---------------|
| **Duration** | 1-2 days | 3-5 days |
| **Features** | 1 | 3-7 |
| **Parallelization** | Sequential | Parallel in Phase 1 |
| **Integration** | Per feature | Batch for week |
| **Documentation** | Per feature | Week summary |
| **Commits** | Per feature | One for week |
| **Use When** | Learning, urgent need | Planned weekly work |

---

## Expected Deliverables

### Implementation Files (per feature)
{% if config.project.type == 'web-app' and config.web_framework and config.web_framework.frontend == 'react' %}- Component implementations (`src/components/*.tsx`)
- Service files (`src/services/*.ts`)
- Style files (`src/styles/*.css`){% elif config.project.type == 'api' and config.technology_stack and config.technology_stack.backend.language == 'python' %}- Route handlers (`src/api/routes/*.py`)
- Models (`src/api/models/*.py`)
- Schemas (`src/api/schemas/*.py`){% elif config.project.type == 'ml' and config.technology_stack and config.technology_stack.backend.language == 'python' %}- Model implementations (`src/models/*_model.py`)
- Training scripts (`src/training/*_training.py`)
- Evaluation notebooks (`notebooks/*_eval.ipynb`){% else %}- Implementation files
- Configuration files{% endif %}
- Test files
- Manual test scripts

### Integration Files
{% if config.project.type == 'web-app' %}- Updated router configuration
- Updated navigation components
- Integration tests{% elif config.project.type == 'api' %}- Updated API router
- Updated API documentation
- Integration tests{% elif config.project.type == 'data-platform' %}- Updated data source registry
- Updated main data interface
- Integration tests{% else %}- Updated application configuration
- Integration tests{% endif %}

### Documentation Files
- Updated {% if config.documentation.main_doc %}{{ config.documentation.main_doc }}{% else %}CLAUDE.md{% endif %}
- Updated {% if config.custom.roadmap_location %}{{ config.custom.roadmap_location }}{% else %}ROADMAP.md{% endif %}
- New `docs/sprints/v{X}.{Y}/WEEK_{X}_COMPLETE.md`

### Handoff Files (in `{% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/`)
- Per-feature handoffs (spec, impl, test, security) for each feature
- `integration-complete-week{X}.md`
- `docs-complete-week{X}.md`
- `commit-complete-week{X}.md`

---

## Integration with Other Workflows

**Triggers other workflows:**
- Feature Development - If follow-up features identified
- Production Deployment - If week represents release milestone
- Performance Optimization - If performance issues identified

**Invoked by:**
- Sprint Planning - During sprint execution
- Quarterly Planning - For multi-week initiatives

**Complements:**
- Single Feature workflow (for individual urgent features)
- Testing & QA workflow (comprehensive testing phase)

---

## Related Documentation

**Agent Instructions:**
{% if config.architecture %}- `agents/architecture/{{ config.architecture.specialist | lower | replace(' ', '-') }}.md`{% endif %}
{% if config.project.type == 'web-app' %}- `agents/development/web-developer.md`{% elif config.project.type == 'api' %}- `agents/development/api-developer.md`{% elif config.project.type == 'ml' %}- `agents/development/ml-engineer.md`{% else %}- `agents/development/developer.md`{% endif %}
- `agents/quality/test-engineer.md`
- `agents/quality/security-reviewer.md`
- `agents/development/integration-engineer.md`
- `agents/documentation/documentation-engineer.md`
- `agents/documentation/git-committer.md`

**Templates:**
- Week plan template
- Design specification template
- Week summary template

---

**Created:** 2025-11-04
**Status:** ✅ Generic
**Version:** 1.0
**Framework:** Vibey Agent Framework
