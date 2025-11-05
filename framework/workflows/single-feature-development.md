# Workflow: Single Feature Development

**Workflow ID:** Single Feature Development
**Purpose:** Complete development of a single feature from specification to deployment
**Duration:** 1-3 days (depending on complexity)
**Complexity:** Medium

---

## Overview

This workflow orchestrates the complete development lifecycle for a single feature, from design through testing, security review, integration, and documentation. It follows a sequential process with quality gates at each step.

**Use Cases:**
{% if config.project.type == 'web-app' %}- Adding a new UI component or page
- Implementing a new user feature
- Creating a new API endpoint{% elif config.project.type == 'api' %}- Adding a new REST endpoint
- Implementing new business logic
- Creating a new service{% elif config.project.type == 'data-platform' %}- Integrating a new data source
- Creating a new data transformation
- Adding a new analytics feature{% elif config.project.type == 'ml' %}- Implementing a new ML model
- Adding a new feature engineering pipeline
- Creating a new prediction endpoint{% else %}- Implementing any new feature
- Adding new functionality
- Creating new components{% endif %}
- Learning new technologies
- Urgent feature requests

**Key Characteristics:**
- Sequential execution (one step at a time)
- Quality gates (testing, security, documentation)
- Complete in 1-3 days
- Single commit per feature

**Prerequisites:**
- Feature requirements documented
- Development environment ready
- Access to necessary tools and services

---

## Workflow Steps

### Step 1: Architecture & Design

**Agent:** {% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architecture Specialist{% endif %}
**Duration:** 0.5-1 day
**Input:** Feature requirements
**Output:** Design specification

**Activation Prompt:**

```markdown
You are the {% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architecture Specialist{% endif %} subagent.
{% if config.architecture %}Read: agents/architecture/{{ config.architecture.specialist | lower | replace(' ', '-') }}.md{% else %}Read: agents/architecture/architecture-specialist.md{% endif %}

Task: Design specification for [Feature Name]

Requirements:
- [Functional requirements]
- [Non-functional requirements]
- [Technical constraints]

{% if config.architecture %}Architecture Pattern: {{ config.architecture.pattern }}{% endif %}
{% if config.design_system %}Design System: {{ config.design_system }}{% endif %}

Create: {% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/design-spec-[feature-name].md
```

**Activities:**
{% if config.project.type == 'web-app' %}- Design UI/UX (wireframes, component structure)
- Define component architecture
- Specify state management approach
- Design API contracts{% elif config.project.type == 'api' %}- Design API endpoints and contracts
- Define request/response schemas
- Specify business logic flow
- Design data models{% elif config.project.type == 'data-platform' %}- Design data ingestion approach
- Define transformation logic
- Specify data quality rules
- Design schema (Bronze/Silver/Gold){% elif config.project.type == 'ml' %}- Design model architecture
- Define feature engineering pipeline
- Specify training/inference workflow
- Design evaluation metrics{% else %}- Design feature architecture
- Define interfaces and contracts
- Specify implementation approach{% endif %}
- Identify dependencies
- Define success criteria

**Deliverables:**
- Design specification document
- {% if config.project.type == 'web-app' %}Component diagram{% elif config.project.type == 'api' %}API specification{% elif config.project.type == 'data-platform' %}Data flow diagram{% elif config.project.type == 'ml' %}Model architecture diagram{% else %}Architecture diagram{% endif %}
- Implementation checklist

**Quality Check:**
- [ ] All requirements addressed
- [ ] Technical approach is sound
{% if config.architecture %}- [ ] Follows {{ config.architecture.pattern }} pattern{% endif %}
- [ ] Dependencies identified
- [ ] Success criteria defined

**Handoff:** Pass specification to Developer

---

### Step 2: Implementation

**Agent:** {% if config.project.type == 'web-app' %}Web Developer{% elif config.project.type == 'api' %}API Developer{% elif config.project.type == 'ml' %}ML Engineer{% else %}Developer{% endif %}
**Duration:** 0.5-1.5 days
**Input:** Design specification
**Output:** Implemented feature

**Activation Prompt:**

```markdown
You are the {% if config.project.type == 'web-app' %}Web Developer{% elif config.project.type == 'api' %}API Developer{% elif config.project.type == 'ml' %}ML Engineer{% else %}Developer{% endif %} subagent.
{% if config.project.type == 'web-app' %}Read: agents/development/web-developer.md{% elif config.project.type == 'api' %}Read: agents/development/api-developer.md{% elif config.project.type == 'ml' %}Read: agents/development/ml-engineer.md{% else %}Read: agents/development/developer.md{% endif %}

Task: Implement [Feature Name]
Input: {% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/design-spec-[feature-name].md

Create:
{% if config.project.type == 'web-app' and config.web_framework and config.web_framework.frontend == 'react' %}- src/components/[FeatureName].tsx
- src/services/[featureName]Service.ts
- src/styles/[FeatureName].css{% elif config.project.type == 'api' and config.technology_stack and config.technology_stack.backend.language == 'python' %}- src/api/routes/[feature_name].py
- src/api/models/[feature_name].py
- src/api/schemas/[feature_name].py{% elif config.project.type == 'ml' and config.technology_stack and config.technology_stack.backend.language == 'python' %}- src/models/[feature_name]_model.py
- src/features/[feature_name]_features.py
- notebooks/[feature_name]_experiment.ipynb{% else %}- src/[feature_name]/implementation{% endif %}
- test_[feature_name]_manual.{% if config.technology_stack %}{{ config.technology_stack.backend.test_extension or 'py' }}{% else %}py{% endif %}
- {% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/impl-[feature-name].md
```

**Activities:**
{% if config.project.type == 'web-app' %}- Implement UI components
- Integrate with state management
- Connect to backend APIs
- Add validation and error handling
- Style components{% elif config.project.type == 'api' %}- Implement route handlers
- Create data models
- Add business logic
- Implement validation
- Add error handling{% elif config.project.type == 'data-platform' %}- Implement data ingestion
- Create transformation logic
- Add data quality checks
- Implement caching/optimization
- Add error handling{% elif config.project.type == 'ml' %}- Implement model architecture
- Create feature engineering
- Add training pipeline
- Implement inference endpoint
- Add evaluation metrics{% else %}- Implement core functionality
- Add validation
- Implement error handling{% endif %}
- Write manual tests
- Document implementation notes

**Deliverables:**
- Implementation files
- Manual test script
- Implementation handoff document

**Quality Check:**
{% if config.technology_stack and config.technology_stack.backend.language == 'python' %}```bash
# Code quality
black src/
ruff check src/
mypy src/

# Manual test
python test_[feature_name]_manual.py
```{% elif config.technology_stack and config.technology_stack.backend.language in ['javascript', 'typescript'] %}```bash
# Code quality
npm run lint
npm run type-check

# Manual test
node test_[feature_name]_manual.js
```{% elif config.technology_stack and config.technology_stack.backend.language == 'java' %}```bash
# Code quality
mvn checkstyle:check
mvn pmd:check

# Manual test
mvn exec:java -Dexec.mainClass="TestFeature"
```{% else %}```bash
# Run code quality checks
[linter command]

# Run manual test
[test command]
```{% endif %}

- [ ] Feature works as specified
- [ ] Code passes quality checks
- [ ] Manual test passes
- [ ] Error handling implemented
- [ ] Code follows project conventions

**Handoff:** Pass implementation to Test Engineer

---

### Step 3: Comprehensive Testing

**Agent:** Test Engineer
**Duration:** 0.25-0.75 days
**Input:** Implementation files
**Output:** Test suite

**Activation Prompt:**

```markdown
You are the Test Engineer subagent.
Read: agents/quality/test-engineer.md

Task: Write comprehensive test suite for [Feature Name]

Input:
- Implementation: [Implementation files]
- Handoff: {% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/impl-[feature-name].md

Test coverage needed:
{% if config.project.type == 'web-app' %}- Component rendering tests
- User interaction tests
- State management tests
- API integration tests
- Error handling tests{% elif config.project.type == 'api' %}- Endpoint tests (success cases)
- Endpoint tests (error cases)
- Validation tests
- Business logic tests
- Integration tests{% elif config.project.type == 'data-platform' %}- Data ingestion tests
- Transformation tests
- Data quality tests
- Error handling tests
- Integration tests{% elif config.project.type == 'ml' %}- Model training tests
- Feature engineering tests
- Inference tests
- Performance tests
- Data validation tests{% else %}- Unit tests
- Integration tests
- Error handling tests{% endif %}

Target: {{ config.test_coverage_target or '85' }}%+ coverage, all tests passing

Create:
{% if config.technology_stack and config.technology_stack.backend.language == 'python' %}- tests/test_[feature_name].py{% elif config.technology_stack and config.technology_stack.backend.language in ['javascript', 'typescript'] %}- tests/[featureName].test.ts{% elif config.technology_stack and config.technology_stack.backend.language == 'java' %}- src/test/java/com/example/[FeatureName]Test.java{% else %}- tests/test_[feature_name]{% endif %}
- {% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/test-complete-[feature-name].md
```

**Activities:**
- Write unit tests for core logic
- Write integration tests
- Test error handling and edge cases
- {% if config.project.type == 'web-app' %}Write component tests{% elif config.project.type == 'api' %}Write API endpoint tests{% elif config.project.type == 'ml' %}Write model evaluation tests{% else %}Write functional tests{% endif %}
- Achieve target coverage ({{ config.test_coverage_target or '85' }}%+)
- Verify all tests pass

**Deliverables:**
- Test files
- Test execution report
- Coverage report
- Test handoff document

**Quality Check:**
{% if config.technology_stack and config.technology_stack.backend.language == 'python' %}```bash
# Run tests
pytest tests/test_[feature_name].py -v

# Check coverage
pytest tests/test_[feature_name].py --cov --cov-report=term-missing
```{% elif config.technology_stack and config.technology_stack.backend.language in ['javascript', 'typescript'] %}```bash
# Run tests
npm test [featureName].test.ts

# Check coverage
npm run test:coverage
```{% elif config.technology_stack and config.technology_stack.backend.language == 'java' %}```bash
# Run tests
mvn test -Dtest=[FeatureName]Test

# Check coverage
mvn jacoco:report
```{% else %}```bash
# Run tests
[test command]

# Check coverage
[coverage command]
```{% endif %}

- [ ] All tests passing (100% pass rate)
- [ ] Coverage ≥ {{ config.test_coverage_target or '85' }}%
- [ ] All edge cases tested
- [ ] Error handling tested
- [ ] No flaky tests

**Handoff:** Pass test results to Security Reviewer

---

### Step 4: Security Review

**Agent:** Security Reviewer
**Duration:** 0.25-0.5 days
**Input:** Implementation and tests
**Output:** Security review report

**Activation Prompt:**

```markdown
You are the Security Reviewer subagent.
Read: agents/quality/security-reviewer.md

Task: Conduct security review of [Feature Name]

Input:
- Implementation: [Implementation files]
- Tests: [Test files]
- Test Results: {% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/test-complete-[feature-name].md

Review for:
{% if config.project.type == 'web-app' %}- XSS vulnerabilities
- CSRF protection
- Client-side data exposure
- Authentication/authorization
- Input validation{% elif config.project.type == 'api' %}- SQL injection
- Authentication/authorization
- Rate limiting
- Input validation
- Data exposure{% elif config.project.type == 'data-platform' %}- Data access controls
- API key security
- Data validation
- Injection attacks
- Logging security{% elif config.project.type == 'ml' %}- Model poisoning
- Input validation
- Data leakage
- Inference security
- Authentication{% else %}- Input validation
- Authentication/authorization
- Data exposure
- Injection attacks
- Logging security{% endif %}

Create:
- {% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/security-review-[feature-name].md

Mark: APPROVED / CONDITIONALLY APPROVED / REJECTED
```

**Activities:**
- Review code for security vulnerabilities
- Check for hardcoded secrets
- Verify input validation
- Review authentication/authorization
- Check for data exposure
- Verify secure logging practices

**Deliverables:**
- Security review report
- Vulnerability findings (if any)
- Remediation recommendations

**Quality Check:**
- [ ] No hardcoded secrets
- [ ] Input validation implemented
- [ ] Authentication/authorization correct
- [ ] No sensitive data in logs
- [ ] All critical issues fixed
- [ ] All high issues fixed or accepted

**Decision Point:**
- **APPROVED** → Continue to Step 5
- **CONDITIONALLY APPROVED** → Fix issues, then continue
- **REJECTED** → Fix critical issues, re-review

**Handoff:** Pass approved feature to Integration Engineer

---

### Step 5: Integration

**Agent:** Integration Engineer
**Duration:** 0.25-0.5 days
**Input:** Approved implementation
**Output:** Integrated feature

**Activation Prompt:**

```markdown
You are the Integration Engineer subagent.
Read: agents/development/integration-engineer.md

Task: Integrate [Feature Name] into {{ config.project.name or 'the application' }}

Input:
- Implementation: [Implementation files] (SECURITY APPROVED)
- Tests passing: [XX/XX]
- Coverage: [XX]%

Integration tasks:
{% if config.project.type == 'web-app' %}1. Register routes in router
2. Add to navigation menu
3. Integrate with state management
4. Test UI integration
5. Verify routing works{% elif config.project.type == 'api' %}1. Register routes in API router
2. Add to API documentation
3. Configure middleware (auth, validation)
4. Test endpoint integration
5. Update OpenAPI/Swagger spec{% elif config.project.type == 'data-platform' %}1. Register in data source registry
2. Add to main data interface
3. Configure caching/rate limiting
4. Test data integration
5. Update data catalog{% elif config.project.type == 'ml' %}1. Register model in model registry
2. Add inference endpoint
3. Configure deployment
4. Test model integration
5. Update model documentation{% else %}1. Register in main application
2. Configure dependencies
3. Test integration
4. Update configuration{% endif %}

Create:
{% if config.technology_stack and config.technology_stack.backend.language == 'python' %}- tests/test_integration_[feature_name].py{% elif config.technology_stack and config.technology_stack.backend.language in ['javascript', 'typescript'] %}- tests/integration/[featureName].test.ts{% else %}- tests/test_integration_[feature_name]{% endif %}
- {% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/integration-complete-[feature-name].md
```

**Activities:**
{% if config.project.type == 'web-app' %}- Register routes
- Update navigation
- Integrate state management
- Test UI flow{% elif config.project.type == 'api' %}- Register API routes
- Update API documentation
- Configure middleware
- Test endpoints{% elif config.project.type == 'data-platform' %}- Register data source
- Update main interface
- Configure caching
- Test data flow{% elif config.project.type == 'ml' %}- Register model
- Deploy inference endpoint
- Configure serving
- Test predictions{% else %}- Register feature
- Configure dependencies
- Test integration{% endif %}
- Create integration tests
- Verify no regressions

**Deliverables:**
{% if config.project.type == 'web-app' %}- Updated router configuration
- Updated navigation
- Integration tests{% elif config.project.type == 'api' %}- Updated API router
- Updated API docs
- Integration tests{% elif config.project.type == 'data-platform' %}- Updated registry
- Updated interface
- Integration tests{% elif config.project.type == 'ml' %}- Updated model registry
- Deployed endpoint
- Integration tests{% else %}- Updated configuration
- Integration tests{% endif %}
- Integration handoff document

**Quality Check:**
{% if config.technology_stack and config.technology_stack.backend.language == 'python' %}```bash
# Test integration
pytest tests/test_integration_[feature_name].py -v
```{% elif config.technology_stack and config.technology_stack.backend.language in ['javascript', 'typescript'] %}```bash
# Test integration
npm test tests/integration/[featureName].test.ts
```{% else %}```bash
# Test integration
[test command]
```{% endif %}

- [ ] Feature integrated successfully
- [ ] Integration tests pass
- [ ] No regressions introduced
- [ ] Feature accessible via main interface

**Handoff:** Pass integration to Documentation Engineer

---

### Step 6: Documentation

**Agent:** Documentation Engineer
**Duration:** 0.25-0.5 days
**Input:** Integration results
**Output:** Updated documentation

**Activation Prompt:**

```markdown
You are the Documentation Engineer subagent.
Read: agents/documentation/documentation-engineer.md

Task: Document [Feature Name] completion

Input:
- Integration: {% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/integration-complete-[feature-name].md
- Security: {% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/security-review-[feature-name].md
- Tests: {% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/test-complete-[feature-name].md

Update:
1. {% if config.documentation.main_doc %}{{ config.documentation.main_doc }}{% else %}README.md{% endif %}
   - Add feature to feature list
   - Update status
2. {% if config.custom.roadmap_location %}{{ config.custom.roadmap_location }}{% else %}ROADMAP.md{% endif %} (if applicable)
   - Mark feature complete
3. Create feature documentation:
   - {% if config.project.type == 'web-app' %}docs/features/[feature-name].md (user guide)
   - docs/components/[FeatureName].md (component docs){% elif config.project.type == 'api' %}docs/api/[feature-name].md (API reference)
   - Update OpenAPI spec{% elif config.project.type == 'data-platform' %}docs/data-sources/[feature-name].md (data docs)
   - Update data catalog{% elif config.project.type == 'ml' %}docs/models/[feature-name].md (model docs)
   - Update model card{% else %}docs/features/[feature-name].md{% endif %}
4. Update changelog

{% if config.documentation.size_check_script %}Verify: {{ config.documentation.size_check_script }}{% endif %}

Create:
- {% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/docs-complete-[feature-name].md
```

**Activities:**
- Update main documentation
- Create feature-specific docs
{% if config.project.type == 'web-app' %}- Add screenshots/demos{% elif config.project.type == 'api' %}- Update API reference{% elif config.project.type == 'data-platform' %}- Document data schema{% elif config.project.type == 'ml' %}- Create model card{% endif %}
- Update changelog
- Verify documentation completeness

**Deliverables:**
- Updated {% if config.documentation.main_doc %}{{ config.documentation.main_doc }}{% else %}README.md{% endif %}
- Feature documentation
- Updated changelog
- Documentation handoff

**Quality Check:**
{% if config.documentation.size_check_script %}```bash
# Verify documentation
{{ config.documentation.size_check_script }}

# Review changes
git diff docs/
```{% else %}```bash
# Review documentation changes
git diff docs/
```{% endif %}

- [ ] Main docs updated
- [ ] Feature docs created
- [ ] Changelog updated
{% if config.documentation.size_check_script %}- [ ] Doc size check passes{% endif %}
- [ ] No typos or broken links

**Handoff:** Pass documentation to Git Committer

---

### Step 7: Commit & Push

**Agent:** Git Committer
**Duration:** 0.25 days
**Input:** Documentation handoff
**Output:** Committed changes

**Activation Prompt:**

```markdown
You are the Git Committer subagent.
Read: agents/documentation/git-committer.md

Task: Commit [Feature Name] implementation

Input:
- Documentation handoff: {% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/docs-complete-[feature-name].md

Commit message format:

```
feat: Add [Feature Name]

[Brief description of what the feature does]

{% if config.project.type == 'web-app' %}- Component: [Component name]
- Route: [Route path]{% elif config.project.type == 'api' %}- Endpoint: [Endpoint path]
- Method: [HTTP method]{% elif config.project.type == 'data-platform' %}- Data source: [Source name]
- Schema: [Schema info]{% elif config.project.type == 'ml' %}- Model: [Model name]
- Endpoint: [Inference endpoint]{% endif %}
- Tests: [XX]/[XX] passing, [Coverage]% coverage
- Security: APPROVED

Files Modified:
- [List key files]

[Additional notes if needed]
```

Steps:
1. Review changes (git status, git diff)
2. Check for secrets (CRITICAL)
3. Stage all files
4. Run final checks (tests, docs, code quality)
5. Commit with message above
6. Push to remote

Create:
- {% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/commit-complete-[feature-name].md
```

**Activities:**
- Review all changes
- Check for secrets
- Stage files
- Run final quality checks
- Create commit
- Push to remote

**Deliverables:**
- Git commit
- Pushed to remote
- Commit handoff document

**Quality Check:**
{% if config.technology_stack and config.technology_stack.backend.language == 'python' %}```bash
# All tests must pass
pytest -v

# Code quality
black --check src/
ruff check src/
mypy src/

# Push
git push origin main
```{% elif config.technology_stack and config.technology_stack.backend.language in ['javascript', 'typescript'] %}```bash
# All tests must pass
npm test

# Code quality
npm run lint
npm run type-check

# Push
git push origin main
```{% elif config.technology_stack and config.technology_stack.backend.language == 'java' %}```bash
# All tests must pass
mvn test

# Code quality
mvn checkstyle:check

# Push
git push origin main
```{% else %}```bash
# Run all checks
[test/lint commands]

# Push
git push origin main
```{% endif %}

- [ ] All tests pass
- [ ] No secrets committed
- [ ] Commit message follows conventions
- [ ] Push successful

**Completion:** Single feature development complete

---

## Quality Gate Enforcement

{% if config.framework and config.framework.require_quality_gates %}
**⚠️ MANDATORY QUALITY GATES ⚠️**

Before marking this feature as complete, ALL quality gates must pass:

### Required Quality Gates

{% if config.quality_gates and config.quality_gates.required_reviews %}
{% for review in config.quality_gates.required_reviews %}
#### {{ loop.index }}. {{ review | capitalize }} Review
{% if review == 'security' %}
**Status:** {% raw %}Must pass before completion{% endraw %}
**Minimum Score:** {{ config.quality_gates.security_score_minimum or 85 }}/100
**Completed in:** Step 4 (Security Review)
**Evidence Required:**
- Security report (`.claude/templates/handoffs/security-report-template.md`)
- No critical or high vulnerabilities
- OWASP Top 10 compliance
- Secrets management validated

**Verification:**
```bash
# Security report should exist
ls docs/security/security-report-*.md

# Report should show APPROVED status
grep "APPROVED" docs/security/security-report-*.md
```

{% elif review == 'testing' %}
**Status:** {% raw %}Must pass before completion{% endraw %}
**Minimum Coverage:** {{ config.quality_gates.test_coverage_minimum or 90 }}%
**Completed in:** Step 3 (Comprehensive Testing)
**Evidence Required:**
- Test coverage report
- All tests passing
- Edge cases covered
- Integration tests included

**Verification:**
```bash
{% if config.technology_stack and config.technology_stack.backend.language == 'python' %}# Check test coverage
pytest --cov --cov-report=term-missing
# Must show ≥ {{ config.quality_gates.test_coverage_minimum or 90 }}%{% elif config.technology_stack and config.technology_stack.backend.language in ['javascript', 'typescript'] %}# Check test coverage
npm test -- --coverage
# Must show ≥ {{ config.quality_gates.test_coverage_minimum or 90 }}%{% else %}# Run tests with coverage
[test command for {{ config.technology_stack.backend.language if config.technology_stack }}]{% endif %}
```

{% elif review == 'logging' %}
**Status:** {% raw %}Must pass before completion{% endraw %}
**Minimum Score:** {{ config.quality_gates.logging_audit_minimum or 80 }}/100
**Completed in:** Post-implementation (use Observability Engineer)
**Evidence Required:**
- Logging audit report
- Correlation IDs present
- Error context sufficient
- Log levels appropriate

**Verification:**
```bash
# Check for correlation ID usage
grep -r "correlation_id\|request_id\|trace_id" src/

# Check logging in new feature
grep -r "logger\|log\|logging" [feature files]
```

{% elif review == 'documentation' %}
**Status:** {% raw %}Must pass before completion{% endraw %}
**Completed in:** Step 6 (Documentation)
**Evidence Required:**
- README.md updated (if user-facing)
- .claude/CLAUDE.md updated (if architecture changed)
- API documentation current
- Code comments present

**Verification:**
```bash
# Check documentation files updated recently
ls -lt README.md .claude/CLAUDE.md docs/

# Ensure feature is documented
grep -r "[Feature Name]" docs/ README.md
```

{% endif %}

---

{% endfor %}
{% else %}
#### 1. Security Review
**Status:** {% raw %}Must pass before completion{% endraw %}
**Minimum Score:** {{ config.quality_gates.security_score_minimum or 85 }}/100
**Completed in:** Step 4
- Security report exists
- No critical/high vulnerabilities
- OWASP Top 10 compliant

#### 2. Test Coverage
**Status:** {% raw %}Must pass before completion{% endraw %}
**Minimum Coverage:** {{ config.quality_gates.test_coverage_minimum or 90 }}%
**Completed in:** Step 3
- All tests passing
- Coverage ≥ {{ config.quality_gates.test_coverage_minimum or 90 }}%
- Edge cases covered

#### 3. Logging Audit
**Status:** {% raw %}Must pass before completion{% endraw %}
**Minimum Score:** {{ config.quality_gates.logging_audit_minimum or 80 }}/100
**Completed in:** Post-implementation
- Correlation IDs present
- Error context sufficient
- Log levels appropriate

#### 4. Documentation
**Status:** {% raw %}Must pass before completion{% endraw %}
**Completed in:** Step 6
- README/CLAUDE.md updated
- API docs current
- Code commented
{% endif %}

### Quality Gate Checklist

Before proceeding to commit (Step 7), verify:

- [ ] **Security review PASSED** (score ≥ {{ config.quality_gates.security_score_minimum or 85 }})
- [ ] **Test coverage PASSED** (≥ {{ config.quality_gates.test_coverage_minimum or 90 }}%)
- [ ] **Logging audit PASSED** (score ≥ {{ config.quality_gates.logging_audit_minimum or 80 }})
- [ ] **Documentation COMPLETE** (all required docs updated)
- [ ] **All tests passing** (100% pass rate)
- [ ] **Code quality checks pass** (linting, formatting, type checking)
- [ ] **No secrets in code** (API keys, passwords, tokens)

**If any quality gate fails, DO NOT proceed to Step 7 (Commit & Push).**

Return to the relevant step and address issues:
- Security fails → Return to Step 4
- Tests fail → Return to Step 3
- Documentation incomplete → Return to Step 6

### Enforcement Mode

**Current mode:** {{ config.framework.orchestration_mode | upper }}

{% if config.framework.orchestration_mode == 'tiered' %}
The Coordinator Agent will verify all quality gates before allowing Step 7.
{% elif config.framework.orchestration_mode == 'balanced' %}
You must verify all quality gates before proceeding to Step 7.
{% else %}
You must check each quality gate explicitly before proceeding to Step 7.
{% endif %}

**Quality gates are NON-NEGOTIABLE.** Do not skip or compromise quality standards.

{% else %}
**Quality gates are recommended but not enforced.**

Consider running:
- Security review
- Test coverage check (target: {{ config.quality_gates.test_coverage_minimum or 90 }}%)
- Documentation review

{% endif %}

---

## Workflow Diagram

```mermaid
graph LR
    A[{% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architect{% endif %}<br/>Design] --> B[Developer<br/>Implement]
    B --> C[Test Engineer<br/>Test]
    C --> D[Security Reviewer<br/>Review]
    D --> E{Approved?}
    E -->|Yes| F[Integration Engineer<br/>Integrate]
    E -->|No| B
    F --> G[Documentation Engineer<br/>Document]
    G --> H[Git Committer<br/>Commit & Push]
```

---

## Duration Estimates

| Step | Agent | Duration | Cumulative |
|------|-------|----------|------------|
| Design | {% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architect{% endif %} | 0.5-1 day | Day 0.5-1 |
| Implementation | Developer | 0.5-1.5 days | Day 1-2.5 |
| Testing | Test Engineer | 0.25-0.75 days | Day 1.5-3 |
| Security Review | Security Reviewer | 0.25-0.5 days | Day 2-3.5 |
| Integration | Integration Engineer | 0.25-0.5 days | Day 2.5-4 |
| Documentation | Documentation Engineer | 0.25-0.5 days | Day 3-4.5 |
| Commit | Git Committer | 0.25 days | Day 3.5-5 |
| **Total** | | **1-3 days** | **~2 days avg** |

**Complexity Factors:**
- Simple feature: 1-1.5 days
- Medium feature: 1.5-2.5 days
- Complex feature: 2.5-3.5 days

---

## Success Criteria

### Must Have
- [ ] Design specification created
- [ ] Feature implemented
- [ ] Tests written ({{ config.test_coverage_target or '85' }}%+ coverage, 100% passing)
- [ ] Security review APPROVED
- [ ] Feature integrated
- [ ] Documentation updated
- [ ] Changes committed and pushed

### Should Have
- [ ] Manual testing completed
- [ ] Integration tests pass
- [ ] No regressions introduced
- [ ] Code quality checks pass

### Nice to Have
{% if config.project.type == 'web-app' %}- [ ] Screenshots/demos created{% elif config.project.type == 'api' %}- [ ] API examples provided{% elif config.project.type == 'ml' %}- [ ] Model card complete{% endif %}
- [ ] Performance benchmarks documented
- [ ] User guide created

---

## Common Issues & Solutions

### Issue: Security Review Fails
**Problem:** Security reviewer found vulnerabilities

**Solution:**
1. Fix all critical and high issues immediately
2. Document accepted medium/low issues
3. Re-run security review
4. Only proceed when APPROVED

---

### Issue: Tests Not Reaching Coverage Target
**Problem:** Coverage is {{ config.test_coverage_target or '85' | int - 15 }}%, need {{ config.test_coverage_target or '85' }}%+

**Solution:**
1. Run coverage report with `--cov-report=term-missing`
2. Identify uncovered lines
3. Add tests for edge cases and error paths
4. Use parametrized tests for different inputs

---

### Issue: Integration Breaks Existing Features
**Problem:** Integration tests fail for existing features

**Solution:**
1. Identify what broke
2. Fix integration to avoid conflicts
3. Run full test suite to verify
4. Consider refactoring if conflicts persist

---

{% if config.documentation.size_check_script %}### Issue: Documentation Too Large
**Problem:** Documentation exceeds size limits

**Solution:**
1. Move detailed content to separate files
2. Use links instead of duplicating content
3. Create feature-specific docs
4. Re-run size check

---
{% endif %}

## Expected Deliverables

### Code Files
{% if config.project.type == 'web-app' and config.web_framework and config.web_framework.frontend == 'react' %}- Component implementation (`src/components/*.tsx`)
- Service files (`src/services/*.ts`)
- Styles (`src/styles/*.css`){% elif config.project.type == 'api' and config.technology_stack and config.technology_stack.backend.language == 'python' %}- Route handlers (`src/api/routes/*.py`)
- Models (`src/api/models/*.py`)
- Schemas (`src/api/schemas/*.py`){% elif config.project.type == 'ml' and config.technology_stack and config.technology_stack.backend.language == 'python' %}- Model implementation (`src/models/*.py`)
- Feature engineering (`src/features/*.py`)
- Inference endpoint (`src/api/*.py`){% else %}- Implementation files{% endif %}
- Test files
- Manual test script

### Integration Files
{% if config.project.type == 'web-app' %}- Updated router
- Updated navigation{% elif config.project.type == 'api' %}- Updated API router
- Updated API docs{% elif config.project.type == 'data-platform' %}- Updated registry
- Updated interface{% elif config.project.type == 'ml' %}- Updated model registry
- Deployed endpoint{% endif %}
- Integration tests

### Documentation Files
- Updated {% if config.documentation.main_doc %}{{ config.documentation.main_doc }}{% else %}README.md{% endif %}
- Feature documentation
- Updated changelog

### Handoff Files
- `design-spec-[feature-name].md`
- `impl-[feature-name].md`
- `test-complete-[feature-name].md`
- `security-review-[feature-name].md`
- `integration-complete-[feature-name].md`
- `docs-complete-[feature-name].md`
- `commit-complete-[feature-name].md`

---

## Integration with Other Workflows

**Triggers other workflows:**
- Performance Optimization - If performance issues identified
- Production Deployment - If feature ready for release

**Invoked by:**
- Sprint Planning - During sprint execution
- Bug Fix workflow - For complex bug fixes
- Weekly Sprint - As part of multi-feature sprint

**Complements:**
- Testing & QA workflow
- Security Review workflow
- Documentation workflow

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
- Design specification template
- Feature documentation template

---

**Created:** 2025-11-04
**Status:** ✅ Generic
**Version:** 1.0
**Framework:** Vibey Agent Framework
