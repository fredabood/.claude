# Workflow: Architecture Review

**Workflow ID:** Architecture Review
**Purpose:** Systematic architecture review for sprints, code, infrastructure, and system design
**Duration:** 2-3 days
**Complexity:** Medium

---

## Overview

This workflow orchestrates comprehensive architecture reviews: sprint plan review → code review → infrastructure review → recommendations → implementation → documentation. Ensures best practices, cost optimization, scalability, and maintainability.

**Use Cases:**
- Pre-sprint architecture validation
- Post-implementation code review
- Quarterly architecture audits
- Performance/cost optimization reviews
- Security architecture validation
- Scalability planning
{% if config.project.type == 'ml' %}- ML pipeline architecture review{% endif %}
{% if config.cloud_provider %}- {{ config.cloud_provider }} architecture optimization{% endif %}

**Prerequisites:**
- Sprint plans or completed code to review
{% if config.architecture %}- {{ config.architecture.specialist }} available{% else %}- Architecture specialist available{% endif %}
- Access to codebase and infrastructure configurations
{% if config.iac_tool %}- Access to {{ config.iac_tool }} configurations{% endif %}

---

## Workflow Steps

### Step 1: Request Architecture Review (Day 1, Morning)

**Agent:** Sprint Planning Agent
**Duration:** 0.5 days
**Input:** Review request (pre-sprint or post-implementation)
**Output:** Architecture review scope document

**Activities:**
- Identify review scope
  - Sprint plan review (preventive)
  - Code review (post-implementation validation)
  - Infrastructure review (cost/performance optimization)
  {% if config.project.type == 'ml' %}- ML pipeline review (model architecture, feature engineering){% endif %}
- Gather artifacts for review
  - Sprint plans (if pre-sprint)
  - Source code (if post-implementation)
  {% if config.iac_tool %}- {{ config.iac_tool }} configurations{% endif %}
  {% if config.architecture %}- {{ config.architecture.pattern }} architecture diagrams{% endif %}
  - Database schemas
  {% if config.cloud_provider %}- {{ config.cloud_provider }} resource configurations{% endif %}
- Set review objectives
  - Performance optimization
  - Cost reduction
  - Scalability improvement
  - Security hardening
  - Best practices compliance

**Deliverables:**
- Architecture review scope document
- Artifacts list
- Review objectives
- Timeline

**Handoff:** Pass scope to {% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architecture Specialist{% endif %}

---

### Step 2: Review Sprint Plan / Design (Day 1, Afternoon)

**Agent:** {% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architecture Specialist{% endif %}
**Duration:** 0.5 days
**Input:** Sprint plan, architecture diagrams, design documents
**Output:** Sprint/design review notes

**Activities:**

**For Pre-Sprint Reviews:**
- Review sprint feasibility
  {% if config.project.type == 'web-app' %}- UI/UX architecture alignment
  - Component design patterns
  - State management strategy
  - API integration patterns{% elif config.project.type == 'api' %}- API design patterns (REST, GraphQL, gRPC)
  - Data model design
  - Service boundaries
  - Integration patterns{% elif config.project.type == 'data-platform' %}- Data pipeline architecture
  - ETL design patterns
  - Data modeling (star schema, data vault, etc.)
  - Partitioning and indexing strategy{% elif config.project.type == 'ml' %}- ML pipeline architecture
  - Model architecture selection
  - Feature engineering design
  - Training/serving strategy{% endif %}
- Identify architectural concerns
  - Scalability bottlenecks
  - Performance risks
  - Security vulnerabilities
  - Technical debt introduction
- Validate {% if config.architecture %}{{ config.architecture.pattern }}{% else %}architecture pattern{% endif %} alignment
- Review technology choices
  {% if config.web_framework %}- {{ config.web_framework.frontend or 'Frontend' }} / {{ config.web_framework.backend or 'Backend' }} stack appropriateness{% endif %}
  {% if config.database %}- {{ config.database.type }} suitability for use case{% endif %}
  {% if config.cloud_provider %}- {{ config.cloud_provider }} service selection{% endif %}

**For Post-Implementation Reviews:**
- Review implemented architecture vs design
- Identify deviations from plan
- Assess technical debt introduced
- Evaluate maintainability

**Deliverables:**
- Sprint/design review notes
- Architectural concerns list
- Technology validation
- Recommendations

**Handoff:** Pass review notes to {% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architecture Specialist{% endif %} (code review phase)

---

### Step 3: Review Code & Infrastructure (Day 2)

**Agent:** {% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architecture Specialist{% endif %}
**Duration:** 1 day
**Input:** Source code, infrastructure configurations, review notes
**Output:** Code and infrastructure review findings

**Activities:**

**Code Review:**
{% if config.project.type == 'web-app' %}- Review frontend code
  {% if config.web_framework and config.web_framework.frontend == 'react' %}- React component architecture (composition, props drilling, context usage)
  - State management patterns (Redux, Zustand, Context API)
  - Performance optimizations (memoization, code splitting){% elif config.web_framework and config.web_framework.frontend == 'vue' %}- Vue component architecture (composition API vs options API)
  - State management (Pinia, Vuex)
  - Performance optimizations{% endif %}
  - Routing architecture
  - API integration patterns
- Review backend code
  {% if config.technology_stack and config.technology_stack.backend.language == 'python' %}- Python code structure (modules, packages)
  - FastAPI/Flask route organization
  - Database ORM usage (SQLAlchemy, Django ORM){% elif config.technology_stack and config.technology_stack.backend.language in ['javascript', 'typescript'] %}- TypeScript/JavaScript structure
  - Express/NestJS architecture
  - Database integration (Prisma, TypeORM){% elif config.technology_stack and config.technology_stack.backend.language == 'java' %}- Java package structure
  - Spring Boot architecture
  - JPA/Hibernate usage{% endif %}
  - API design patterns
  - Error handling patterns{% elif config.project.type == 'api' %}- Review API design
  - Endpoint organization and naming
  - Request/response schemas
  - Error handling and status codes
  - Authentication/authorization patterns
- Review business logic
  {% if config.technology_stack and config.technology_stack.backend.language == 'python' %}- Python code quality (type hints, docstrings){% elif config.technology_stack and config.technology_stack.backend.language in ['javascript', 'typescript'] %}- TypeScript type safety{% elif config.technology_stack and config.technology_stack.backend.language == 'java' %}- Java design patterns{% endif %}
  - Service layer architecture
  - Data access patterns{% elif config.project.type == 'data-platform' %}- Review data pipeline code
  {% if config.big_data_framework == 'Spark' %}- Spark job architecture
  - DataFrame transformations
  - Join strategies
  - Partitioning and bucketing{% elif config.big_data_framework %}- {{ config.big_data_framework }} job structure{% endif %}
  - ETL patterns
  - Data quality checks
- Review data transformations
  - SQL query patterns
  - Data validation logic{% elif config.project.type == 'ml' %}- Review ML pipeline code
  - Feature engineering architecture
  - Model training code structure
  - Hyperparameter tuning approach
  - Model evaluation patterns
- Review inference code
  - Batch vs real-time serving
  - Model loading and caching
  - Preprocessing pipelines{% else %}- Review code structure
  - Design patterns
  - Error handling
  - Testing coverage{% endif %}

**Common Code Review Items (All Project Types):**
- Code organization and modularity
- Design patterns usage
- SOLID principles compliance
- DRY (Don't Repeat Yourself) violations
- Error handling and logging
- Security vulnerabilities
  - Input validation
  - SQL injection prevention
  - XSS prevention
  - Authentication/authorization
- Performance anti-patterns
  - N+1 queries
  - Unnecessary loops
  - Memory leaks
- Test coverage and quality

**Infrastructure Review:**
{% if config.iac_tool == 'Terraform' %}- Review Terraform configurations
  - Module structure and reusability
  - State management
  - Variable organization
  - Resource naming conventions{% elif config.iac_tool == 'Pulumi' %}- Review Pulumi code
  - Component structure
  - Configuration management
  - Resource organization{% elif config.iac_tool == 'CloudFormation' %}- Review CloudFormation templates
  - Stack structure
  - Parameter organization
  - Nested stack usage{% elif config.iac_tool %}- Review {{ config.iac_tool }} configurations{% endif %}
{% if config.cloud_provider == 'AWS' %}- Review AWS architecture
  - VPC design
  - Security groups and NACLs
  - IAM roles and policies
  - Service selection (EC2, Lambda, ECS, etc.)
  - Cost optimization opportunities{% elif config.cloud_provider == 'Azure' %}- Review Azure architecture
  - VNet design
  - Network security groups
  - Azure RBAC
  - Service selection (VMs, Functions, AKS, etc.)
  - Cost optimization opportunities{% elif config.cloud_provider == 'GCP' %}- Review GCP architecture
  - VPC design
  - Firewall rules
  - Cloud IAM
  - Service selection (Compute Engine, Cloud Run, GKE, etc.)
  - Cost optimization opportunities{% elif config.cloud_provider %}- Review {{ config.cloud_provider }} architecture{% endif %}
- Review scalability configurations
  - Auto-scaling policies
  - Load balancing
  - Database replication/sharding
- Review disaster recovery
  - Backup strategies
  - Multi-region deployment
  - Failover procedures

**Deliverables:**
- Code review findings
  - Critical issues (must fix)
  - High priority issues (should fix)
  - Medium priority issues (nice to fix)
  - Low priority issues (technical debt)
- Infrastructure review findings
- Security vulnerabilities identified
- Performance optimization opportunities
{% if config.cloud_provider %}- {{ config.cloud_provider }} cost optimization recommendations{% endif %}

**Handoff:** Pass findings to {% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architecture Specialist{% endif %} (report creation)

---

### Step 4: Create Architecture Review Report (Day 2-3)

**Agent:** {% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architecture Specialist{% endif %}
**Duration:** 0.5 days
**Input:** All review findings
**Output:** Architecture Review Report

**Activities:**
- Compile all findings into structured report
- Prioritize recommendations by impact and effort
  - **Critical:** Security vulnerabilities, data loss risks, scalability blockers
  - **High:** Performance issues, cost inefficiencies, maintainability problems
  - **Medium:** Code quality issues, minor technical debt
  - **Low:** Style inconsistencies, documentation gaps
- Calculate impact metrics
  - Performance improvement potential: X% faster
  {% if config.cloud_provider %}- {{ config.cloud_provider }} cost reduction potential: $X/month{% endif %}
  - Development velocity improvement: X% faster iterations
- Create action plan with timelines
- Document best practices for future reference

**Deliverables:**
- **Architecture Review Report** ({% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/architecture-review-YYYY-MM-DD.md)
  - Executive summary
  - Review scope and methodology
  - Findings by category (code, infrastructure, security, performance)
  - Prioritized recommendations
  - Action plan with owners and timelines
  - Best practices documentation
  - Appendix: Detailed findings

**Handoff:** Pass report to relevant development teams

---

### Step 5: Implement Recommendations (Day 3)

**Agent:** Relevant development agents ({% if config.project.type == 'web-app' %}Web Developer{% elif config.project.type == 'api' %}API Developer{% elif config.project.type == 'ml' %}ML Engineer{% else %}Developers{% endif %}, DevOps Engineer, etc.)
**Duration:** Variable (0.5-2 days for critical items)
**Input:** Architecture Review Report
**Output:** Implemented fixes and improvements

**Activities:**
- Implement critical recommendations immediately
  - Security vulnerabilities (MUST fix before deployment)
  - Data loss risks
  - Scalability blockers
- Schedule high-priority recommendations
  - Add to current sprint backlog
  - Assign owners
- Create technical debt tickets for medium/low priority items
- Validate fixes don't introduce regressions

**Deliverables:**
- Fixed code for critical issues
- Pull requests for high-priority improvements
- Technical debt backlog items created
- Validation test results

**Handoff:** Pass implemented changes to Documentation Engineer

---

### Step 6: Update Architecture Documentation (Day 3)

**Agent:** Documentation Engineer
**Duration:** 0.5 days
**Input:** Architecture Review Report, implemented changes
**Output:** Updated architecture documentation

**Activities:**
- Update architecture diagrams
  {% if config.diagramming_tool %}- Update {{ config.diagramming_tool }} diagrams{% endif %}
  - System architecture diagram
  - Data flow diagrams
  {% if config.project.type == 'data-platform' %}- ETL pipeline diagrams{% endif %}
  {% if config.project.type == 'ml' %}- ML pipeline diagrams{% endif %}
- Document architectural patterns applied
- Update best practices guide
- Document architecture decisions (ADRs - Architecture Decision Records)
  - Context
  - Decision
  - Consequences
  - Alternatives considered
- Update {% if config.documentation.main_doc %}{{ config.documentation.main_doc }}{% else %}README.md{% endif %} with architecture improvements

**Deliverables:**
- Updated architecture diagrams
- Architecture Decision Records (ADRs)
- Best practices guide updates
- Updated {% if config.documentation.main_doc %}{{ config.documentation.main_doc }}{% else %}README.md{% endif %}

**Handoff:** Pass documentation to Git Committer

---

### Step 7: Commit Changes (Day 3)

**Agent:** Git Committer
**Duration:** 0.25 days
**Input:** Code fixes, documentation updates, architecture review report
**Output:** Committed changes

**Activities:**
- Stage all code fixes
- Stage documentation updates
- Stage architecture review report
- Create descriptive commit message
- Push to remote repository

**Commit Message Example:**
```
docs: Architecture review YYYY-MM-DD - {{ config.project.name }}

Completed comprehensive architecture review:
- Reviewed {% if config.project.type == 'web-app' %}web application architecture{% elif config.project.type == 'api' %}API architecture{% elif config.project.type == 'data-platform' %}data pipeline architecture{% elif config.project.type == 'ml' %}ML pipeline architecture{% else %}system architecture{% endif %}
- Identified X critical, Y high, Z medium priority issues
- Implemented X critical fixes
{% if config.cloud_provider %}- Estimated {{ config.cloud_provider }} cost savings: $X/month{% endif %}

Key improvements:
- [List major improvements]

See docs/handoffs/architecture-review-YYYY-MM-DD.md for full report.
```

**Deliverables:**
- Git commit with all changes
- Architecture review report in version control
- Updated remote repository

**Completion:** Architecture review workflow complete

---

## Workflow Diagram

```mermaid
graph LR
    A[Sprint Planning<br/>Request Review] --> B[{% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architect{% endif %}<br/>Review Plan/Design]
    B --> C[{% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architect{% endif %}<br/>Review Code & Infra]
    C --> D[{% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architect{% endif %}<br/>Create Report]
    D --> E[Developers<br/>Implement Fixes]
    E --> F[Documentation<br/>Update Docs]
    F --> G[Git Committer<br/>Commit]
```

---

## Duration Estimates

| Phase | Agent | Duration | Cumulative |
|-------|-------|----------|------------|
| Request Review | Sprint Planning | 0.5 days | Day 0.5 |
| Review Plan/Design | {% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architect{% endif %} | 0.5 days | Day 1 |
| Review Code & Infrastructure | {% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architect{% endif %} | 1 day | Day 2 |
| Create Report | {% if config.architecture %}{{ config.architecture.specialist }}{% else %}Architect{% endif %} | 0.5 days | Day 2.5 |
| Implement Recommendations | Developers | 0.5-2 days | Day 3-4.5 |
| Update Documentation | Documentation Engineer | 0.5 days | Day 3.5-5 |
| Commit Changes | Git Committer | 0.25 days | Day 3.75-5.25 |
| **Total** | | **3-5 days** | **~4 days avg** |

**Note:** Duration varies based on:
- Scope of review (sprint plan vs full system)
- Number of findings
- Complexity of fixes required

---

## Success Criteria

### Must Have
- [ ] Architecture review scope defined
- [ ] Sprint/design reviewed (if pre-sprint)
- [ ] Code reviewed (if post-implementation)
- [ ] Infrastructure reviewed
- [ ] Architecture Review Report created
- [ ] Critical recommendations implemented
- [ ] Documentation updated

### Should Have
- [ ] High-priority recommendations scheduled
- [ ] Architecture diagrams updated
- [ ] ADRs (Architecture Decision Records) created
- [ ] Best practices guide updated
{% if config.cloud_provider %}- [ ] {{ config.cloud_provider }} cost optimization identified{% endif %}

### Nice to Have
- [ ] All medium-priority recommendations implemented
- [ ] Automated architecture checks added to CI/CD
- [ ] Architecture review checklist created for future reviews

---

## Review Triggers

**When to conduct architecture reviews:**

**Preventive (Pre-Sprint):**
- Before major feature development
- Before infrastructure changes
- Quarterly scheduled reviews
- Before architectural changes

**Validation (Post-Implementation):**
- After major feature completion
- After infrastructure deployment
- After performance issues resolved
- After security incidents

**Reactive:**
{% if config.cloud_provider %}- {{ config.cloud_provider }} cost spikes{% endif %}
- Performance degradation
- Scalability issues
- Security vulnerabilities discovered
- Technical debt accumulation

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| **Too many findings** | Prioritize critical/high only, create backlog for medium/low |
| **Resistance to recommendations** | Include impact analysis (performance %, cost $), show data |
| **No time to implement fixes** | Implement critical fixes only, schedule high-priority items |
| **Architectural drift** | Establish regular review cadence (quarterly), enforce code reviews |
| **Inconsistent patterns** | Create architecture decision records (ADRs), document patterns |

---

## Integration with Other Workflows

**Triggers other workflows:**
- Performance Optimization - If performance issues identified
- Security Hardening - If security vulnerabilities found
- Infrastructure Setup - If infrastructure changes needed
- Refactoring - If technical debt is high

**Invoked by:**
- Sprint Planning - Before major sprints
- Performance issues - When optimization needed
- Security incidents - After vulnerabilities discovered
- Regular cadence - Quarterly/monthly reviews

---

## Handoff Templates

This workflow uses the following handoff template:

**Architecture Review Report** → `{% if config.custom.handoff_location %}{{ config.custom.handoff_location }}{% else %}docs/handoffs{% endif %}/architecture-review-template.md`

**Template Structure:**
```markdown
# Architecture Review Report - YYYY-MM-DD

## Executive Summary
- Review scope
- Key findings (X critical, Y high, Z medium)
{% if config.cloud_provider %}- Estimated {{ config.cloud_provider }} cost impact: $X/month{% endif %}
- Performance impact: X% improvement potential
- Recommendations summary

## Review Scope
- Sprint/code reviewed
- Infrastructure reviewed
- Review objectives

## Findings by Category

### Code Architecture
[Critical/High/Medium/Low findings]

### Infrastructure
[Findings]

### Security
[Findings]

### Performance
[Findings]

### Cost Optimization
[Findings]

## Prioritized Recommendations
1. [Critical items - must fix]
2. [High priority - should fix]
3. [Medium priority - nice to fix]
4. [Low priority - technical debt]

## Action Plan
| Recommendation | Priority | Owner | Timeline | Estimated Effort |
|----------------|----------|-------|----------|------------------|
| ... | Critical | ... | ... | ... |

## Best Practices
[Patterns to adopt going forward]

## Appendix
[Detailed findings, code samples, diagrams]
```

---

## Related Documentation

**Agent Instructions:**
- `agents/planning/sprint-planning.md`
{% if config.architecture %}- `agents/architecture/{{ config.architecture.specialist | lower | replace(' ', '-') }}.md`{% endif %}
- `agents/documentation/documentation-engineer.md`
- `agents/documentation/git-committer.md`

**Other Workflows:**
- `workflows/sprint-planning.md`
- `workflows/performance-optimization.md`
- `workflows/infrastructure-setup.md`

---

**Created:** 2025-11-04
**Status:** ✅ Generic
**Version:** 1.0
**Framework:** Vibey Agent Framework
