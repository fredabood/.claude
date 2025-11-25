# Handoff Templates

**Purpose:** Standardized templates for agent-to-agent communication and work handoffs
**Status:** 5 core templates extracted (22% of planned templates)
**Framework:** Vibey Agent Framework v1.0

---

## Overview

Handoff templates provide structured communication between agents in multi-step workflows. Each template:

- Uses Jinja2 syntax for config interpolation
- Supports multiple project types (web-app, API, data-platform, ML, infrastructure)
- Adapts to different technology stacks via `.claude/project-config.yaml`
- Ensures consistent information transfer between workflow steps
- Provides clear next steps and accountability

---

## Available Templates

**Status:** 21 core templates extracted (91% of planned)

### 1. API Specification Template

**File:** `api-spec-template.md`
**From:** API Architect
**To:** API Engineer / Backend Developer
**Purpose:** Comprehensive API integration specifications

**Use When:**
- Designing integration with external APIs
- Documenting API client requirements
- Planning data source integrations
- Specifying backend service contracts

**Key Sections:**
- Executive Summary (provider, category, complexity)
- Authentication (API key, OAuth2, custom)
- Endpoints (parameters, responses, errors)
- Rate limiting and throttling
- Caching strategy (for data-platform projects)
- Implementation guidance (multi-language)
- Testing requirements

**Supported Languages:** Python, TypeScript, JavaScript, Java, Go
**Supported Project Types:** All (especially data-platform, API)

**Related Workflows:**
- Single API Client Development
- Weekly Sprint (API integration phase)
- Data Platform Integration

---

### 2. Architecture Review Template

**File:** `architecture-review-template.md`
**From:** Architecture Specialist
**To:** Team, Stakeholders
**Purpose:** Document architecture assessment and recommendations

**Use When:**
- Sprint planning (technical feasibility review)
- Pre-implementation architecture validation
- Post-implementation architecture audit
- Major feature design review

**Key Sections:**
- Review scope (sprint, code, infrastructure, ML)
- Architecture assessment summary
- Best practices validation (project-type specific)
- Detailed findings (critical, high, medium, low)
- Recommendations with prioritization
- Risk assessment
- Action items and approval sign-off

**Supported Project Types:** All (web-app, API, data-platform, ML, infrastructure)

**Related Workflows:**
- Architecture Review Workflow
- Sprint Planning
- Infrastructure Setup

---

### 3. Security Report Template

**File:** `security-report-template.md`
**From:** Security Reviewer
**To:** Team, Integration Engineer, Next Agent in Workflow
**Purpose:** Comprehensive security audit and vulnerability assessment

**Use When:**
- After implementation (pre-integration security review)
- Weekly sprint security gate
- Pre-deployment security audit
- Dependency vulnerability scanning

**Key Sections:**
- Executive summary (risk level, issues found)
- Secrets management (no hardcoded credentials)
- Input validation (type checking, sanitization)
- Logging (no PII, no credentials)
- Rate limiting (API/web-app)
- TLS/HTTPS (certificate validation)
- Authentication & authorization (JWT, OAuth2, session)
- Dependencies (CVE scanning)
- Test security (no real credentials)
- Frontend security (XSS, CSRF, CSP - for web-app)
- Database security (SQL injection prevention)
- Risk assessment and approval decision

**Supported Languages:** Python, TypeScript, JavaScript, Java, Go
**Supported Project Types:** All

**Related Workflows:**
- Weekly Sprint (security review gate)
- Single Feature Development (security step)
- Frontend Security Hardening
- Infrastructure Setup (security validation)

---

### 4. Integration Template

**File:** `integration-template.md`
**From:** Integration Engineer
**To:** Documentation Engineer, Git Committer
**Purpose:** Document integration completion and test results

**Use When:**
- After completing component integration
- After feature merge into main codebase
- After API client registration
- After service deployment

**Key Sections:**
- Summary (component type, integration type)
- Changes made (files modified, code snippets)
- Test results (unit, integration, E2E)
- Authentication/configuration requirements
- Frontend integration (for web-app)
- Database changes (migrations, if applicable)
- Documentation updates needed
- Known issues
- Security review checklist
- Deliverables checklist
- Next steps and commit message

**Supported Languages:** Python, TypeScript, JavaScript, Java, Go
**Supported Project Types:** All

**Related Workflows:**
- Integration Only Workflow
- Weekly Sprint (integration phase)
- Single Feature Development (integration step)

---

### 5. Test Report Template

**File:** `test-report-template.md`
**From:** Test Engineer
**To:** Security Reviewer, Next Agent in Workflow
**Purpose:** Comprehensive test execution report and coverage analysis

**Use When:**
- After implementing comprehensive test suite
- Weekly sprint testing gate
- Pre-deployment test validation
- Test coverage audit

**Key Sections:**
- Test summary (files, total tests, pass rate, coverage)
- Test files created (by category)
- Coverage report (line, branch, function)
- Test execution results (framework-specific output)
- Test utilities created (builders, fixtures, mocks)
- Test categories (unit, integration, E2E, performance)
- Edge cases tested
- Quality metrics (best practices)
- Mocking strategy
- Known gaps
- CI integration
- Readiness checklist

**Supported Frameworks:** pytest (Python), Jest/Vitest (TypeScript/JavaScript), JUnit (Java), Go testing
**Supported Project Types:** All

**Related Workflows:**
- Weekly Sprint (testing gate)
- Single Feature Development (testing step)
- ML Model Development (testing step)
- Frontend Production Deployment (E2E tests)

---

### 6. Deployment Checklist Template

**File:** `deployment-checklist-template.md`
**From:** DevOps Engineer
**To:** Team, Stakeholders
**Purpose:** Comprehensive deployment checklist for production releases

**Use When:**
- Deploying to staging or production
- Multi-environment deployments
- Container deployments (Docker, Kubernetes)
- Serverless deployments
- Static site deployments

**Key Sections:**
- Pre-deployment checklist (code quality, security, documentation, infrastructure)
- Build checklist (backend, frontend, containers)
- Deployment steps (environment-specific)
- Post-deployment checklist (smoke tests, monitoring, performance)
- Rollback checklist (decision criteria, rollback steps)
- Environment variables and secrets
- Success criteria and sign-off

**Supported Deployment Targets:** Docker, Kubernetes, Serverless (AWS/Azure/GCP), Static (CDN), VM
**Supported Languages:** Python, TypeScript, JavaScript, Java, Go
**Supported Project Types:** All

**Related Workflows:**
- Frontend Production Deployment
- Infrastructure Setup
- Weekly Sprint (deployment phase)

---

### 7. Sprint Plan Template

**File:** `sprint-plan-template.md`
**From:** Sprint Planning Agent
**To:** Team, Stakeholders
**Purpose:** Comprehensive sprint plan with phases, milestones, dependencies

**Use When:**
- Starting a new sprint
- Planning multi-week development cycle
- Coordinating multiple team members
- Managing complex projects with dependencies

**Key Sections:**
- Sprint metadata (version, duration, dates)
- Sprint objectives & goals (OKRs)
- Sprint scope (must have, should have, nice to have, out of scope)
- Dependency graph (upstream, internal, downstream)
- Sprint phases & timeline (with Gantt chart)
- Prioritization scoring (value, effort, risk)
- Resource allocation (team assignments, constraints)
- Milestones & success criteria
- Risks & mitigation
- Quality gates (security, testing, logging, documentation)
- Communication & reporting (ceremonies, status updates)
- Budget & cost estimates (for infrastructure/ML projects)
- Testing strategy
- Deployment plan

**Supported Project Types:** All (web-app, API, data-platform, ML, infrastructure)

**Related Workflows:**
- Sprint Planning Workflow
- Architecture Review

---

### 8. ML Design Template

**File:** `ml-design-template.md`
**From:** ML Engineer
**To:** Team Stakeholders
**Purpose:** Comprehensive ML solution design before implementation

**Use When:**
- Designing new ML model
- Planning ML project
- Getting stakeholder buy-in for ML initiative
- Documenting ML architecture

**Key Sections:**
- Problem statement & ML objective (business problem, success criteria)
- ML type & methodology (classification, regression, clustering, etc.)
- Data requirements (data sources, training dataset specification)
- Feature engineering plan (feature categories, Feature Store design)
- Model architecture & algorithm selection
- Hyperparameter tuning strategy
- Cross-validation strategy
- Evaluation metrics (primary, secondary, baseline comparison)
- Feature importance & interpretability
- Deployment strategy (batch, real-time, streaming, edge)
- Success criteria & definition of done
- Timeline & milestones
- Risks & mitigations
- Computational requirements
- Ethical considerations & bias analysis

**Supported ML Platforms:** MLflow, Weights & Biases, TensorBoard, Databricks, SageMaker
**Supported Project Types:** ML, data-platform

**Related Workflows:**
- ML Model Development Workflow

---

### 9. Research Summary Template

**File:** `research-summary-template.md`
**From:** Researcher
**To:** Requesting Agent
**Purpose:** Concise documentation summary with actionable insights

**Use When:**
- Researching new API documentation
- Learning new framework or library
- Documenting architecture patterns
- Compressing verbose documentation (80-95% reduction)
- Creating reusable knowledge base

**Key Sections:**
- Summary metadata (compression ratio, research type)
- Executive summary (what, why, use cases, when NOT to use)
- Quick reference (key facts, gotchas, prerequisites)
- Authentication (for APIs)
- Installation & setup (for libraries/frameworks)
- Core concepts/key endpoints
- Code templates (multi-language)
- Common patterns & best practices
- Error handling
- Testing
- Production considerations (security, performance, scalability)
- Integration examples
- Migration guide
- Troubleshooting
- Further reading & deep dives
- Quick start checklist

**Research Types:** API, REST API, GraphQL, Library, Framework, Package, Architecture, Design Pattern
**Supported Languages:** Python, TypeScript, JavaScript, Java, Go
**Supported Project Types:** All

**Related Workflows:**
- Documentation Research Workflow
- Single API Client (research phase)

---

### 10. Logging Audit Report Template

**File:** `logging-audit-report-template.md`
**From:** Observability Engineer
**To:** Implementation Team
**Purpose:** Comprehensive logging audit with 100-point scoring system

**Use When:**
- Mandatory quality gate before deployment (≥80/100 required)
- After implementing logging for new features
- Auditing observability capabilities
- Fixing logging deficiencies

**Key Sections:**
- 100-point scoring system (5 categories)
  - Request Tracing (25 points)
  - Error Context (30 points)
  - Product Analytics (20 points)
  - Performance Metrics (15 points)
  - Log Accessibility (10 points)
- Critical/High/Low priority issues with code examples
- Remediation roadmap (Phase 1: Critical, Phase 2: High, Phase 3: Low)
- Multi-language correlation ID propagation examples
- Error context logging patterns
- Product analytics tracking (for web-app)
- Re-audit process and verification checklists

**Supported Languages:** Python, TypeScript, JavaScript, Java, Go
**Supported Frameworks:** FastAPI, Express, Spring Boot, and more
**Supported Project Types:** All (especially web-app, API)

**Related Workflows:**
- Logging Audit Workflow
- Weekly Sprint (logging audit gate)

---

### 11. Phase Plan Template

**File:** `phase-plan-template.md`
**From:** Sprint Planning Agent
**To:** Implementation Team
**Purpose:** Sprint phase plan focusing on WHAT/WHY (not HOW)

**Use When:**
- Planning individual sprint phases
- Documenting phase objectives and deliverables
- Defining success criteria for phase completion
- Breaking down complex sprints into manageable phases

**Key Sections:**
- Phase objectives and key deliverables
- Technical requirements (project-type specific)
  - API: endpoints, authentication, rate limiting
  - Web-app: pages, components, state management
  - ML: model type, training data, deployment
  - Infrastructure: resources, environments, security
- Success criteria and quality gates
- Dependencies (upstream, downstream, external)
- Team roles and assignments
- Testing strategy
- Security considerations
- References to implementation guide (for HOW details)
- Definition of done with sign-off requirements

**Supported Project Types:** All (web-app, API, data-platform, ML, infrastructure)

**Related Workflows:**
- Weekly Sprint (phase-based execution)
- Single Feature Development (phase breakdown)

**Template Usage Note:**
- Phase plans focus on WHAT/WHY (100-200 lines)
- Implementation guides cover HOW (with all code/commands)

---

### 12. Infrastructure Design Template

**File:** `infrastructure-design-template.md`
**From:** DevOps Engineer
**To:** Implementation Team, Security Reviewer
**Purpose:** Complete infrastructure-as-code design document

**Use When:**
- Designing new infrastructure before implementation
- Planning multi-environment deployments
- Documenting infrastructure architecture
- Getting stakeholder approval for infrastructure changes

**Key Sections:**
- Infrastructure overview (environments, architecture diagram)
- Cloud provider & platform selection
  - AWS services (EC2, RDS, S3, Lambda, etc.)
  - Azure services (VMs, SQL Database, Storage, Functions)
  - GCP services (Compute Engine, Cloud SQL, Cloud Storage, Cloud Functions)
- Resource hierarchy
  - Compute (servers, Kubernetes, serverless)
  - Storage (databases, object storage)
  - Networking (VPC, load balancers, NAT gateways)
- IaC structure (Terraform/Pulumi/CloudFormation)
- State management (remote backend, locking, backup)
- Variable structure (global, environment-specific, sensitive)
- CI/CD pipeline design with deployment gates
- Secrets management (AWS Secrets Manager, Azure Key Vault, GCP Secret Manager)
- IAM & access control (users, groups, service accounts)
- Monitoring & alerting (metrics, alerts, cost tracking)
- Security configuration (network, encryption, compliance)
- Disaster recovery & backup (RTO, RPO, recovery steps)
- Cost estimation and optimization strategies
- Timeline, risks, and approval sign-off

**Supported Cloud Providers:** AWS, Azure, GCP
**Supported IaC Tools:** Terraform, Pulumi, CloudFormation
**Supported Deployment Targets:** Kubernetes, Serverless, VM, Containers
**Supported Project Types:** All (especially infrastructure, data-platform)

**Related Workflows:**
- Infrastructure Setup Workflow

---

### 13. Component/Feature Design Template

**File:** `component-design-template.md`
**From:** Product Designer / UI/UX Designer
**To:** Frontend Engineer
**Purpose:** Comprehensive component/feature design specification

**Use When:**
- Designing new UI components or features
- Planning complex frontend functionality
- Specifying component behavior and interactions
- Defining component props, state, and styling

**Key Sections:**
- Component overview (file location, hierarchy)
- Props/input interface (React/Vue/Angular/Svelte)
- State management (local and global)
- API integration
- UI states (loading, error, empty, success)
- User interactions and event handlers
- UI component library usage
- Accessibility requirements (WCAG, ARIA, keyboard nav)
- Form validation (Yup/Zod/Joi)
- Styling (CSS/SCSS/CSS-in-JS)
- Performance optimizations (memoization, debouncing, virtualization)
- Testing requirements (unit, integration, accessibility)
- Documentation requirements (JSDoc/TSDoc)

**Supported Frameworks:** React, Vue, Angular, Svelte
**Supported UI Libraries:** Material-UI, Ant Design, Blueprint, Chakra UI, Custom
**Supported Languages:** TypeScript, JavaScript
**Supported Project Types:** web-app (especially frontend components)

**Related Workflows:**
- Single Feature Development (design phase)
- Frontend Development
- Component Development

---

### 14. Performance Optimization Report Template

**File:** `performance-optimization-report-template.md`
**From:** Performance Engineer
**To:** Engineering Team, Stakeholders
**Purpose:** Document performance analysis and optimization recommendations

**Use When:**
- Diagnosing performance issues
- Optimizing slow pipelines, APIs, or pages
- Reducing infrastructure costs
- Meeting performance SLAs

**Key Sections:**
- Executive summary (current vs target metrics)
- Component analysis (job/query, API endpoint, page, model training)
- Bottlenecks identified (critical, high, medium priority)
- Performance profiling
  - Data-platform: Spark stage analysis, task metrics, query plans
  - API: Request breakdown, database query analysis
  - Web-app: Page load metrics (FCP, LCP, TTI, TBT, CLS), bundle analysis
  - ML: Training pipeline breakdown, resource utilization
- Platform-specific analysis (Spark, database, bundle, model config)
- Optimization recommendations (critical, quick wins, medium priority)
- Expected improvements (performance forecast, cost impact, ROI)
- Implementation plan (3 phases)
- Quality gates & success criteria
- Risks & mitigations
- Monitoring & regression prevention

**Supported Platforms:** Databricks/Spark, AWS EMR, GCP Dataproc, Databases, Web Apps, ML Training
**Supported Project Types:** All (data-platform, API, web-app, ML, infrastructure)

**Related Workflows:**
- Performance Optimization Workflow
- Infrastructure Optimization

---

### 15. Dashboard Specification Template

**File:** `dashboard-specification-template.md`
**From:** Product Owner / Data Analyst / Business User
**To:** BI Developer / Data Analyst / Frontend Developer
**Purpose:** Comprehensive dashboard requirements specification

**Use When:**
- Creating new dashboards or reports
- Migrating dashboards to new platforms
- Documenting dashboard requirements
- Planning data visualization needs

**Key Sections:**
- Dashboard overview (purpose, audience, success criteria)
- Data sources & refresh strategy
- Dashboard layout & structure (wireframes, grid layout)
- Visualizations specification (KPI cards, charts, tables, maps, gauges)
- Filters & parameters (global, local, date ranges)
- Metrics & calculations (KPIs, calculated fields)
- Interactivity (click actions, drill-downs, cross-filtering)
- Styling & branding (color palette, typography, logo)
- Performance requirements (load time, data volume, caching)
- Access control & permissions (user roles, row-level security)
- Export & download options
- Alerts & notifications
- Testing requirements

**Supported Platforms:** Tableau, Power BI, Looker, Databricks Lakeview, Metabase, Grafana, Superset, Custom
**Supported Project Types:** All (especially data-platform, web-app)

**Related Workflows:**
- Dashboard Creation Workflow
- Data Visualization

---

### 16. ML Evaluation Report Template

**File:** `ml-evaluation-report-template.md`
**From:** ML Engineer / Data Scientist
**To:** Team, Stakeholders, MLOps Engineer
**Purpose:** Document model training results and production readiness

**Use When:**
- Evaluating trained ML models
- Deciding whether to deploy models to production
- Comparing model versions
- Documenting model performance

**Key Sections:**
- Executive summary (performance summary, recommendation)
- Test set performance metrics
  - Regression: MAPE, RMSE, R², MAE
  - Binary Classification: Accuracy, AUC-ROC, Precision, Recall, F1
  - Multi-class: Accuracy, Macro F1, Weighted F1, Top-K
  - Object Detection: mAP, Precision, Recall, FPS
  - NLP: BLEU/F1/Perplexity, Latency
  - Forecasting: MAPE/RMSE, Prediction intervals
- Comparison to baseline models
- Hyperparameter tuning results
- Feature importance analysis (SHAP values)
- Model strengths & weaknesses
- Error analysis (confusion matrix, error patterns, residuals)
- Cross-validation results
- Bias & fairness analysis
- Production deployment recommendations
- Deployment configuration (batch, real-time, streaming, edge)
- Monitoring & maintenance plan
- ML platform experiment details (MLflow, W&B, TensorBoard)

**Supported ML Types:** Regression, Classification, Object Detection, NLP, Forecasting, Recommendation, Clustering
**Supported ML Platforms:** MLflow, Weights & Biases, TensorBoard, SageMaker, Databricks
**Supported Frameworks:** TensorFlow, PyTorch, scikit-learn, XGBoost, LightGBM
**Supported Project Types:** ML, data-platform

**Related Workflows:**
- ML Model Development Workflow (evaluation phase)
- Model Deployment

---

### 17. Application Requirements Template

**File:** `application-requirements-template.md`
**From:** Product Owner / Business Analyst
**To:** Engineering Team, Stakeholders
**Purpose:** Comprehensive application requirements specification

**Use When:**
- Starting a new application project
- Gathering requirements from stakeholders
- Planning application architecture and features
- Defining project scope and success criteria

**Key Sections:**
- Executive summary (vision, objectives, success metrics)
- Business context (market opportunity, competitive landscape)
- User personas & user stories
- Functional requirements (core features, user flows)
- Data requirements (data sources, data model, quality requirements)
- UI/UX requirements (wireframes, design system, accessibility)
- Non-functional requirements (performance, scalability, security, reliability)
- Integration requirements (external APIs, authentication providers, third-party services)
- Deployment strategy (environments, CI/CD, monitoring)
- Testing requirements & UAT plan
- Documentation requirements
- Constraints & assumptions
- Risks & mitigations
- Timeline & milestones (high-level roadmap)
- Budget & resource requirements
- Approval & sign-off

**Supported Project Types:** All (web-app, API, data-platform, ML, infrastructure)
**Supported Languages:** Python, TypeScript, JavaScript, Java, Go

**Related Workflows:**
- Sprint Planning (requirements phase)
- Architecture Review (requirements input)
- Single Feature Development (requirements definition)

---

### 18. Database Schema Design Template

**File:** `database-schema-design-template.md`
**From:** Database Architect / Backend Engineer
**To:** Backend Developer, DevOps Engineer
**Purpose:** Complete database schema design document

**Use When:**
- Designing new database schema
- Planning data model for application
- Documenting database architecture
- Planning database migrations

**Key Sections:**
- Schema overview (database type, purpose, design principles)
- Technology selection (PostgreSQL, MySQL, MongoDB, Neo4j, etc.)
- Entity/table/collection definitions
  - Relational: Full DDL with columns, types, constraints
  - Document: JSON schemas with validation
  - Graph: Node types, relationship types, Cypher patterns
- Relationships & constraints (foreign keys, unique constraints, check constraints)
- Indexes & query optimization (primary, secondary, composite indexes)
- Data integrity & validation rules
- Denormalization & materialized views
- Partitioning & sharding strategy
- Data migration scripts
- Backup & recovery plan (RTO, RPO, recovery procedures)
- Security & access control (authentication, authorization, encryption at rest/in transit)
- Monitoring & observability (query performance, replication lag)
- Capacity planning & growth projections
- Related diagrams (ER diagrams, schema diagrams)

**Supported Database Types:** Relational (PostgreSQL, MySQL), Document (MongoDB), Graph (Neo4j), Time-series, Key-value, Columnar
**Supported Project Types:** All (especially data-platform, web-app, API)

**Related Workflows:**
- Infrastructure Setup (database provisioning)
- Data Platform Integration (schema design)
- API Development (backend data model)

---

### 19. Diagram Handoff Template

**File:** `diagram-handoff-template.md`
**From:** Diagram Engineer / Technical Writer
**To:** Documentation Engineer / Team
**Purpose:** Handoff diagrams and documentation assets

**Use When:**
- Completing diagram creation for documentation
- Handing off diagrams to documentation team
- Documenting diagram maintenance procedures
- Creating diagram index for project

**Key Sections:**
- Handoff metadata (date, diagram count, tool used, target documentation)
- Diagrams created (each with file path, type, format, purpose)
- Diagram index (categorized diagram list)
- Quality verification (syntax, rendering, accuracy, consistency, context)
- Component names & terminology standards
- Embedding recommendations (where to place diagrams in docs)
- Related diagrams suggested (future diagram ideas)
- Documentation updates needed (files to update with diagrams)
- Cross-references (diagram-to-diagram, doc-to-diagram links)
- Maintenance guidelines (when to update, versioning strategy)
- Style guide (color palette, typography, shapes, arrows)
- Testing checklist (rendering, content, style, documentation, accessibility)
- Embedding examples (markdown code examples)
- Export specifications (resolution, DPI, color space, transparency)
- Source files (editable source locations, editing instructions)
- Tool-specific notes (Mermaid, Draw.io, PlantUML, Lucidchart, Figma)

**Supported Diagram Tools:** Mermaid, Draw.io, PlantUML, Lucidchart, Figma, Visio
**Supported Diagram Types:** Architecture, Workflow, Data Model, Sequence, UI/UX
**Supported Project Types:** All

**Related Workflows:**
- Documentation & Diagrams Workflow
- Architecture Documentation
- Technical Writing

---

### 20. Documentation Update Template

**File:** `documentation-update-template.md`
**From:** Triggering Agent (varies)
**To:** Documentation Maintenance Engineer
**Purpose:** Update project documentation following triggers

**Use When:**
- Sprint or milestone completion
- Policy changes or new standards
- Metric updates (test coverage, performance, etc.)
- Monthly archival of old content
- Manual documentation updates

**Key Sections:**
- Update request with trigger information
- Input data (sprint completion, milestone, policy change, metric update, archival)
- Documentation files to update (specific sections and changes)
- Expected updates (primary and related docs)
- Version control (commit message, files to commit)
- Verification checklist (pre/post update, quality checks)
- Success criteria and quality gates
- Reference links to source documents
- Automation notes (if configured)
- Archival strategy (retention policy, archive format)
- Rollback plan
- Communication plan (stakeholder notifications)

**Trigger Types:** sprint_completion, milestone_completion, policy_change, metric_update, monthly_archival, manual

**Supported Project Types:** All (web-app, API, data-platform, ML, infrastructure)

**Related Workflows:**
- Documentation Maintenance Workflow
- Sprint Completion
- .claude/CLAUDE.md Auto-Update

---

### 21. Security Implementation Report Template

**File:** `security-implementation-report-template.md`
**From:** Security Engineer
**To:** Documentation Engineer / Next Agent
**Purpose:** Document security features implemented and issues fixed

**Use When:**
- After implementing security hardening
- Completing security sprint phase
- Fixing security vulnerabilities
- Production security audit

**Key Sections:**
- Executive summary (security score, issues found/fixed)
- Security features implemented:
  - Authentication & authorization (JWT, OAuth2, session)
  - Input validation (Bean Validation, Joi/Yup/Zod, Pydantic)
  - XSS prevention (DOMPurify, sanitization)
  - Security headers (CSP, X-Frame-Options, etc.)
  - Rate limiting
  - Secrets management
  - CSRF protection (for web-app)
  - CORS configuration
- Security checklist results (9 categories, scored)
- Issues found and fixed (critical, high, medium, low)
- OWASP Top 10 assessment
- Testing evidence (authentication, authorization, validation, XSS, rate limiting)
- Penetration testing results (if performed)
- Security scanning results (npm audit, pip-audit, dependency-check, gosec)
- Compliance assessment (if applicable)
- Recommendations (production, future sprints)
- Security documentation created
- Monitoring & alerting configuration
- Ready criteria for next step

**Supported Languages:** Python, TypeScript, JavaScript, Java, Go
**Supported Frameworks:** Spring Boot, Express, FastAPI, Django, Flask, React, Vue, Angular, Svelte
**Supported Project Types:** All (especially web-app, API)

**Related Workflows:**
- Frontend Security Hardening
- Backend Security Hardening
- Security Review Workflow

---

## Usage Guide

### 1. Select Appropriate Template

Choose the template that matches your current workflow step:

```yaml
# Example: API integration workflow
Step 1: API Architect → api-spec-template.md
Step 2: API Engineer → (implement based on spec)
Step 3: Test Engineer → test-report-template.md
Step 4: Security Reviewer → security-report-template.md
Step 5: Integration Engineer → integration-template.md
```

### 2. Fill in Template Variables

Replace Jinja2 template variables with actual values:

```markdown
# Before (template)
**Created by:** {{ config.roles.api_architect or 'API Architect' }}
**Date:** {{ review_date }}
**API Name:** {{ api_name }}

# After (filled)
**Created by:** API Architect
**Date:** 2025-11-04
**API Name:** GitHub REST API
```

### 3. Adapt to Project Type

Templates automatically adapt based on `config.project.type`:

```yaml
# .claude/project-config.yaml
project:
  type: "web-app"  # Templates show web-app specific sections

# vs

project:
  type: "data-platform"  # Templates show data-platform specific sections
```

### 4. Save to Handoff Directory

Save completed handoffs in your project's handoff directory:

```bash
.claude/handoffs/
├── api-spec-github.md
├── security-review-user-auth.md
├── integration-payment-service.md
└── test-report-sprint-10.md
```

### 5. Reference in Workflow

Link handoff documents in sprint plans and implementation guides:

```markdown
## Phase 2: API Integration

**Input:** API Specification (`.claude/handoffs/api-spec-github.md`)
**Agent:** API Engineer
**Output:** Implemented client + tests
**Next:** Test Engineer (generate test report)
```

---

## Template Development Guide

### Adding New Templates

To add a new handoff template to Vibey:

1. **Identify the workflow step** that needs standardized handoff
2. **Analyze existing handoffs** from existing projects
3. **Generalize with Jinja2:**
   - Replace project-specific values with `{{ variables }}`
   - Add conditional sections: `{% if config.condition %}`
   - Support multiple languages/frameworks
4. **Test with sample config** to ensure rendering works
5. **Document in this README** with usage guidance

### Template Best Practices

**Structure:**
- Clear metadata (from, to, date, purpose)
- Executive summary at top
- Detailed sections with consistent formatting
- Checklists for deliverables
- Next steps clearly identified

**Config Integration:**
- Use `{{ config.property }}` for project-specific values
- Use `{% if config.condition %}` for optional sections
- Support at least 3-4 project types
- Support at least 3-4 programming languages

**Clarity:**
- Include examples for each section
- Provide code snippets in appropriate language
- Use emojis sparingly for visual hierarchy (📊 🧪 🔑 etc.)
- Keep sections focused and scannable

**Completeness:**
- Cover all necessary information for next agent
- Include quality gates and approval criteria
- Provide suggested next steps
- Include commit message template (if applicable)

---

## Template Roadmap

### Phase 5.1: Core Templates ✅ (5/5 = 100%)

- ✅ API Specification
- ✅ Architecture Review
- ✅ Security Report
- ✅ Integration Report
- ✅ Test Report

### Phase 5.2: Design Templates ✅ (4/4 = 100%)

- ✅ ML Model Design
- ✅ Infrastructure Design
- ✅ Database Schema Design
- ✅ Component/Feature Design

### Phase 5.3: Planning Templates ✅ (4/4 = 100%)

- ✅ Sprint Plan
- ✅ Phase Plan
- ✅ Research Summary
- ✅ Application Requirements

### Phase 5.4: Operations Templates ✅ (4/4 = 100%)

- ✅ Deployment Checklist
- ✅ Logging Audit Report
- ✅ Performance Optimization Report
- ✅ Documentation Update

### Phase 5.5: Specialized Templates ✅ (3/3 = 100%)

- ✅ Dashboard Specification
- ✅ ML Evaluation Report
- ✅ Diagram Handoff

### Phase 5.6: Security Templates ✅ (1/1 = 100%)

- ✅ Security Implementation Report

**Total Planned:** 23 templates (21 universal + 2 framework-specific optional)
**Current Status:** 21 templates extracted (91%)
**Framework-Specific (Optional):** 2 remaining (Java/React test reports - redundant with universal Test Report template)

---

## Related Documentation

**Agent Framework:** `../../agents/README.md`
**Workflows:** `../../workflows/README.md`
**Config Schema:** `../../config/schema.yaml`
**Config Templates:** `../../config/config-templates/`

---

## Contributing

To contribute new handoff templates:

1. Follow existing template structure
2. Use Jinja2 for config interpolation
3. Support multiple project types
4. Test with sample configs
5. Document in this README
6. Submit PR with examples

---

**Last Updated:** 2025-11-04
**Version:** 1.0
**Maintainer:** Vibey Framework Team
