# Workflow Selection Guide

**Purpose:** Help you choose the right workflow for your task
**Version:** 1.0
**Framework:** Vibey Agent Framework

---

## Quick Selection Matrix

| Your Task | Use This Workflow | Duration |
|-----------|-------------------|----------|
| Initializing Vibey for existing codebase | [Codebase Audit & Discovery](#codebase-audit--discovery) | 60-105 min |
| Planning a new sprint | [Sprint Planning](#sprint-planning) | 3-5 days |
| Adding a single feature | [Single Feature Development](#single-feature-development) | 1-3 days |
| Building multiple features in parallel | [Weekly Sprint](#weekly-sprint) | 3-5 days |
| Integrating completed components | [Integration Only](#integration-only) | 30min-2hr |
| Building an ML model | [ML Model Development](#ml-model-development) | 15-25 days |
| Setting up infrastructure | [Infrastructure Setup](#infrastructure-setup) | 12-18 days |
| Optimizing performance | [Performance Optimization](#performance-optimization) | 5-8 days |
| Reviewing architecture | [Architecture Review](#architecture-review) | 2-3 days |
| Conducting logging audit | [Logging Audit](#logging-audit) | 2-3 days |

---

## Workflow Details

### Codebase Audit & Discovery

**File:** `workflows/planning/codebase-audit-discovery.md`

**Important:** This workflow has **two independent components** that can be run separately:

#### Component 1: Codebase Audit (60-105 min)

**Use When:**
- Initializing Vibey on an **existing codebase** with source files
- You want to skip 20+ tech stack questions
- You want automated code quality, security, and testing analysis
- You want comprehensive health scores and gap analysis

**Don't Use When:**
- Starting a brand new project from scratch (greenfield)
- No source code exists yet
- Time is very limited (can do git history only instead)

**Process:** Detect Structure → Tech Stack Analysis → Documentation Scan → Security Scan → Test Analysis → Logging Review → Code Quality → Pattern Detection → Generate Report

#### Component 2: Git History Analysis (10-20 min)

**Use When:**
- Initializing Vibey on a project with **git commit history**
- You want to understand what was built in recent sprints
- You want to detect sprint cadence and development velocity
- You want historical context for roadmap planning
- Time is limited but you want some context

**Don't Use When:**
- No git repository exists
- Project is brand new with minimal commit history
- You prefer to explain recent work manually

**Process:** Analyze Commits → Detect Sprint Cadence → Summarize Recent Sprints → Calculate Velocity → Identify Migrations → Generate Report

#### Choose Your Combination

1. **Both components** (70-125 min) - Maximum context, best for mature projects
2. **Codebase audit only** (60-105 min) - Code quality focus, no historical context
3. **Git history only** (10-20 min) - Quick historical context, still answer tech questions
4. **Neither** (0 min) - Fastest start, answer all questions manually

**Key Deliverables (depends on option chosen):**

**If Both Components:**
- Comprehensive audit report with code analysis + git history (`docs/codebase-audit-report.md`)
- Pre-filled `project-config.yaml` with tech stack, health scores, velocity, and sprint cadence
- Health scores across 10 dimensions (0-100)
- Recent sprint summary (last 2-3 sprints)
- Development velocity baseline
- Identified gaps and priorities

**If Codebase Audit Only:**
- Audit report with code analysis only (no git history section)
- Pre-filled `project-config.yaml` with tech stack and health scores
- Health scores across 10 dimensions (0-100):
  - Project Structure, Technology Stack, Documentation, Security, Testing, Logging, Code Quality, Architecture, Deployment, Dependencies
- Identified gaps and priorities
- No velocity or sprint cadence data

**If Git History Only:**
- Lightweight git history report
- Pre-filled `project-config.yaml` with sprint cadence and velocity baselines
- Recent sprint summary (last 2-3 sprints)
- Development velocity (commits/week, lines/month)
- Team activity patterns
- Recent technology migrations
- No code quality or tech stack detection

**If Neither:**
- No audit report generated
- Empty `project-config.yaml` (manually filled during sprint planning)
- All information provided manually through questions

**Time:**
- Both: 70-125 minutes
- Codebase only: 60-105 minutes (varies by codebase size)
- Git history only: 10-20 minutes
- Neither: 0 minutes

**Integration:**
- **Offered as options** by `/vibey` command when existing project detected
- User chooses: Both / Codebase only / Git only / Neither
- Runs **before** framework initialization and sprint planning
- Completely optional - user can skip and provide information manually

**Benefits (depends on option):**

**Both Components:**
- ✅ Skip 20+ tech stack questions
- ✅ Understand what was built in recent sprints
- ✅ Get velocity baseline for realistic planning
- ✅ Identify security vulnerabilities and gaps
- ✅ Strategic sprint planning with full context

**Codebase Audit Only:**
- ✅ Skip 20+ tech stack questions
- ✅ Identify security vulnerabilities and gaps
- ✅ Get health scores and improvement priorities
- ❌ No historical context about recent work
- ❌ No velocity baseline

**Git History Only:**
- ✅ Understand what was built recently
- ✅ Get velocity baseline for realistic planning
- ✅ Detect sprint cadence automatically
- ❌ Still answer tech stack questions manually
- ❌ No code quality analysis

**Neither:**
- ✅ Fastest to start (0 minutes)
- ❌ Answer all questions manually
- ❌ No automated analysis

**Example Output (Both Components):**
```
=== CODE ANALYSIS ===
Overall Health Score: 78/100

Tech Stack:
- Backend: Python 3.11 + FastAPI 0.109.0 (confidence: 100%)
- Database: PostgreSQL (confidence: 95%)
- Tests: 127 tests, 78% coverage

Health Scores:
- Security: 72/100 ⚠️ (needs rate limiting, secrets in vault)
- Testing: 82/100 ✓
- Documentation: 85/100 ✓

=== GIT HISTORY ===
Sprint Cadence: Bi-weekly (detected from tags)

Recent Sprints:
- Sprint 8 (Oct 1-15): Auth overhaul (OAuth2, 2FA) - 47 commits
- Sprint 7 (Sep 15-30): Payment integration (Stripe) - 38 commits

Velocity: 45 commits/week average

=== RECOMMENDED FIRST SPRINT ===
Based on velocity and security gaps:
1. Security: Implement rate limiting (Est: 3-4 days)
2. Security: Move secrets to vault (Est: 1-2 days)
3. Testing: Increase coverage to 85%+ (Est: 2-3 days)
```

---

### Sprint Planning

**File:** `workflows/sprint-planning.md`

**Use When:**
- Starting a new sprint (quarterly, monthly, weekly)
- Reprioritizing the roadmap
- Planning multi-sprint dependencies
- Assessing feature feasibility

**Don't Use When:**
- You already have a sprint plan
- You're just implementing a single feature
- You're doing ad-hoc bug fixes

**Process:** Requirements → Research → Architecture → Dependencies → Planning → Roadmap → Documentation → Commit

**Key Deliverables:**
- Sprint plan document
- Updated roadmap
- Dependency graph
- Prioritization matrix

**Time:** 3-5 days (without research: 4 days)

---

### Single Feature Development

**File:** `workflows/single-feature-development.md`

**Use When:**
{% if config.project.type == 'web-app' %}- Adding a new UI component or page
- Implementing a new user feature
- Creating a new API endpoint{% elif config.project.type == 'api' %}- Adding a new REST endpoint
- Implementing new business logic
- Creating a new service{% elif config.project.type == 'data-platform' %}- Integrating a new data source
- Creating a new data transformation
- Adding a new analytics feature{% elif config.project.type == 'ml' %}- Implementing a new ML model
- Adding feature engineering
- Creating prediction endpoint{% else %}- Implementing a new feature
- Adding new functionality{% endif %}
- Learning a new technology
- Responding to urgent requests

**Don't Use When:**
- You have multiple features to build (use Weekly Sprint)
- You only need integration (use Integration Only)
- You're planning a sprint (use Sprint Planning)

**Process:** Design → Implement → Test → Security → Integrate → Document → Commit

**Key Deliverables:**
- Implemented feature
- Comprehensive tests ({{ config.test_coverage_target or '85' }}%+ coverage)
- Security review (APPROVED)
- Integration complete
- Documentation

**Time:** 1-3 days (simple: 1-1.5 days, complex: 2.5-3.5 days)

---

### Weekly Sprint

**File:** `workflows/weekly-sprint.md`

**Use When:**
- Building 3-7 related features in one week
- Executing weekly sprint goals
- Developing multiple components in parallel
- Batch integration and deployment

**Don't Use When:**
- You have only 1-2 features (use Single Feature Development)
- Features are unrelated (run Single Feature Development in parallel)
- You need faster delivery (use Single Feature Development)

**Process:**
- **Parallel Phase:** Design → Implement → Test → Security (for each feature)
- **Integration Phase:** Integrate all features
- **Documentation Phase:** Week summary → Commit

**Key Deliverables:**
- Multiple features implemented and tested
- All integrated into main system
- Week summary document
- Single commit for entire week

**Time:** 3-5 days (3 features: 3-4 days, 5 features: 4-5 days, 7 features: 5-6 days)

---

### Integration Only

**File:** `workflows/integration-only.md`

**Use When:**
- You have a completed component that needs integration
- Component is already implemented and tested
- Tests are passing with good coverage
- You just need to connect it to the main system

**Don't Use When:**
- Component isn't implemented yet (use Single Feature Development)
- Tests aren't passing or don't exist
- You need to make changes to the component

**Process:** Gather Metadata → Register/Connect → Integration Test → Manual Verify → Handoff

**Key Deliverables:**
{% if config.project.type == 'web-app' %}- Component registered in router
- Navigation updated
- State management connected{% elif config.project.type == 'api' %}- Endpoint registered in API
- Middleware configured
- API docs updated{% elif config.project.type == 'data-platform' %}- Data source registered
- Fetch method added
- Orchestration updated{% elif config.project.type == 'ml' %}- Model registered
- Inference endpoint deployed
- Serving configured{% else %}- Component registered
- Integration complete{% endif %}
- Integration tests passing

**Time:** 30 minutes - 2 hours per component

---

### ML Model Development

**File:** `workflows/ml-model-development.md`

**Use When:**
{% if config.project.type == 'ml' %}- Building a new ML model (classification, regression, forecasting, etc.)
- Developing recommendation systems
- Implementing anomaly detection
- Creating ML-powered features{% else %}- Adding ML capabilities to your application
- Building predictive models
- Implementing intelligent features{% endif %}

**Don't Use When:**
- You're just deploying an existing model (use Integration Only)
- You're fine-tuning without major changes (skip early steps)
- You don't have training data available yet

**Process:** Requirements → Design → Data Prep → Features → Training → Architecture Review → Optimization → Deployment → Monitoring → Documentation → Commit

**Key Deliverables:**
- Trained model {% if config.ml_platform %}in {{ config.ml_platform.experiment_tracking or 'experiment tracker' }}{% endif %}
- Model meeting success criteria
{% if config.ml_platform and config.ml_platform.model_registry %}- Model in {{ config.ml_platform.model_registry }} (Production){% endif %}
- Deployed (batch or real-time)
- Monitoring dashboard
- Model card documentation

**Time:** 15-25 days (~3-5 weeks, buffer 2-5 days)

**Variants:**
- Simple model (no feature store): 15-18 days
- Model refresh (retrain existing): 10-12 days
- Real-time inference: 25-28 days

---

### Infrastructure Setup

**File:** `workflows/infrastructure-setup.md`

**Use When:**
- Setting up new cloud infrastructure
- Deploying multi-environment setup (dev/staging/prod)
{% if config.iac_tool %}- Creating {{ config.iac_tool }} configurations{% else %}- Creating Infrastructure-as-Code{% endif %}
- Building CI/CD pipelines
- Major infrastructure migrations

**Don't Use When:**
- Infrastructure already exists (use Architecture Review)
- You're making small changes (edit directly)
- You're optimizing existing infrastructure (use Performance Optimization)

**Process:** Requirements → Architecture Review → IaC Design → Implementation → Security → CI/CD → Performance → Dev Deploy → Staging Deploy → Prod Deploy → Documentation → Commit

**Key Deliverables:**
{% if config.iac_tool %}- {{ config.iac_tool }} modules{% else %}- IaC modules{% endif %}
- Multi-environment deployment (dev/staging/prod)
- CI/CD pipelines
- Security review passed
- Complete documentation

**Time:** 12-18 days (~2.5-3.5 weeks, buffer 2-4 days)

---

### Performance Optimization

**File:** `workflows/performance-optimization.md`

**Use When:**
{% if config.project.type == 'web-app' %}- Pages loading slowly (>3 seconds)
- High server response times
- Frontend performance issues
- Large bundle sizes{% elif config.project.type == 'api' %}- Slow API endpoints (>500ms)
- High database query latency
- Memory leaks or high CPU
- Inefficient algorithms{% elif config.project.type == 'data-platform' %}- Slow data jobs (>1 hour)
- High resource costs
- Pipeline latency issues
- ETL bottlenecks{% elif config.project.type == 'ml' %}- Slow training (>24 hours)
- High inference latency (>1 second)
- Feature engineering bottlenecks
- GPU underutilization{% else %}- Application performance issues
- High resource consumption
- Latency problems{% endif %}
- Performance regression after changes
- Pre-production validation
{% if config.cloud_provider %}- {{ config.cloud_provider }} cost optimization{% endif %}

**Don't Use When:**
- Performance is already acceptable
- You haven't measured baseline metrics
- No clear performance targets

**Process:** Identify Issues → Analyze → Architecture Review → Implement → Test → Validate → Document → Commit

**Key Deliverables:**
- Performance analysis report
- Implemented optimizations
- Before/after benchmarks
- % improvement metrics
{% if config.cloud_provider %}- {{ config.cloud_provider }} cost savings{% endif %}
- Performance regression tests

**Time:** 5-8 days (~1-1.5 weeks)

---

### Architecture Review

**File:** `workflows/architecture-review.md`

**Use When:**
- Before starting a major sprint (preventive)
- After completing implementation (validation)
- Quarterly/monthly architecture audits
- Performance or cost issues arise
- After security incidents
- Technical debt is accumulating

**Don't Use When:**
- You're in the middle of development (finish first)
- No code or plans exist to review
- Issues are clearly not architectural

**Process:** Request → Review Plan/Design → Review Code & Infrastructure → Create Report → Implement Recommendations → Update Documentation → Commit

**Key Deliverables:**
- Architecture review report
- Prioritized recommendations (critical/high/medium/low)
- Critical fixes implemented
- Updated architecture documentation
- ADRs (Architecture Decision Records)

**Time:** 2-3 days (can extend to 5 days with implementation)

**Triggers:**
- **Preventive:** Before major features, quarterly reviews
- **Validation:** After major features, after deployments
- **Reactive:** Cost spikes, performance issues, security incidents

---

### Logging Audit

**File:** `workflows/logging-audit.md`

**Use When:**
- Pre-production deployment (mandatory quality gate)
- Production readiness certification
- Compliance audits (GDPR, SOC2, etc.)
- Post-incident logging improvement
- Quarterly logging health checks

**Don't Use When:**
- Application isn't implemented yet
- No services are running to audit
- Logging infrastructure isn't set up

**Process:** Preparation → Audit 5 Categories → Consolidate → Create Remediation Plan (if fail) → Update Documentation → Commit

**Audit Categories:**
1. Request Tracing (25 points)
2. Error Context (30 points)
3. Product Analytics (20 points)
4. Performance Metrics (15 points)
5. Log Accessibility (10 points)

**Pass/Fail:** Score ≥ 80/100 required for production deployment

**Key Deliverables:**
- Logging audit report (score /100)
- Remediation plan (if score <80)
- Audit evidence (screenshots, logs)

**Time:** 2-3 days (3 days if remediation needed)

---

## Decision Tree

```
START
  │
  ├─ Initializing Vibey on existing codebase?
  │   └─ YES → Codebase Audit & Discovery
  │
  ├─ Need to plan work?
  │   └─ YES → Sprint Planning
  │
  ├─ Need to build something?
  │   ├─ Single feature? → Single Feature Development
  │   ├─ Multiple features (3-7)? → Weekly Sprint
  │   ├─ ML model? → ML Model Development
  │   └─ Infrastructure? → Infrastructure Setup
  │
  ├─ Component already built?
  │   └─ YES → Integration Only
  │
  ├─ Need to improve something?
  │   ├─ Performance issues? → Performance Optimization
  │   ├─ Logging inadequate? → Logging Audit
  │   └─ Architecture concerns? → Architecture Review
  │
  └─ Not sure?
      └─ Read the "Use When" section for each workflow above
```

---

## Workflow Combinations

### Common Sequences

**Initializing Vibey on Existing Codebase:**
1. **Codebase Audit & Discovery** (analyze existing code, 60-105 min)
2. Sprint Planning (plan improvements based on audit findings)
3. Single Feature Development or Weekly Sprint (implement priorities)
4. Architecture Review (if audit revealed concerns)
5. Logging Audit (if logging score <80/100)
6. Performance Optimization (if needed)

**Starting a New Project (Greenfield):**
1. Sprint Planning (plan v1.0.0)
2. Infrastructure Setup (if needed)
3. Weekly Sprint or Single Feature Development (implement features)
4. Architecture Review (validate design)
5. Logging Audit (production readiness)
6. Performance Optimization (if needed)

**Adding a Major Feature:**
1. Sprint Planning (if multi-sprint) OR skip if single sprint
2. Single Feature Development OR Weekly Sprint
3. Integration Only (if needed)
4. Architecture Review (validation)
5. Performance Optimization (if issues arise)

**Production Readiness:**
1. Architecture Review
2. Logging Audit (mandatory, score ≥80/100)
3. Performance Optimization
4. Security Review (part of other workflows)
5. Documentation Review

**Regular Cadence:**
- **Weekly:** Weekly Sprint OR Single Feature Development
- **Monthly:** Architecture Review, Logging Audit health check
- **Quarterly:** Sprint Planning (roadmap update), Performance Optimization

---

## Workflow Selection FAQ

### Q: I have a bug to fix. Which workflow?

**A:** For bugs:
- **Quick fix (<1 hour):** No workflow, just fix and test
- **Complex bug (1+ days):** Use **Single Feature Development** (treat as feature work)
- **Performance bug:** Use **Performance Optimization**
- **Security bug:** Fix immediately, then use **Architecture Review** to prevent recurrence

### Q: Which workflow for urgent requests?

**A:** **Single Feature Development** (1-3 days) is fastest for complete feature delivery. For even faster:
- Skip sprint planning
- Use **Integration Only** if component already exists
- Focus on critical/high priorities only

### Q: Can I run multiple workflows in parallel?

**A:** Yes! Common parallel combinations:
- **Weekly Sprint** (features) + **Infrastructure Setup** (if deploying to new infra)
- **Single Feature Development** (urgent) + **ML Model Development** (background)
- Multiple **Single Feature Development** workflows (different teams)

### Q: I'm new to the framework. Where do I start?

**A:**
1. Read this guide completely
2. Start with **Single Feature Development** (simplest, 1-3 days)
3. Once comfortable, try **Weekly Sprint** (parallel features)
4. Use **Sprint Planning** when planning larger initiatives

### Q: How do I know if I need Sprint Planning?

**A:** Use **Sprint Planning** if:
- You have >5 features to build
- Features span multiple sprints/weeks
- Complex dependencies exist
- You're starting a new version (v2.0.0)
- Stakeholders need roadmap visibility

**Skip Sprint Planning** if:
- You have 1-3 features
- Work is straightforward
- No complex dependencies
- You're doing maintenance work

### Q: When should I use Architecture Review?

**A:** **Before** major work (preventive) OR **after** major work (validation):
- **Preventive:** Before v2.0.0, before infrastructure changes, quarterly reviews
- **Validation:** After major features, after cost spikes, after incidents

### Q: Is Logging Audit mandatory?

**A:** Yes, for **production deployments**. Score ≥80/100 required. This is a quality gate ensuring production-grade observability.

### Q: Should I run analysis when initializing Vibey on my existing project?

**A:** **Optional but recommended.** Choose based on time vs. quality tradeoff:

**Run Both (70-125 min) if:**
- ✅ You have time to invest upfront
- ✅ You want maximum context for sprint planning
- ✅ Project is mature with significant code and history
- ✅ You want strategic planning, not administrative Q&A

**Run Codebase Audit Only (60-105 min) if:**
- ✅ You want to skip tech stack questions
- ✅ Code quality/security analysis is priority
- ❌ You don't care about recent sprint history
- ❌ You can explain recent work manually

**Run Git History Only (10-20 min) if:**
- ✅ Time is very limited but you want some context
- ✅ You want velocity baseline for planning
- ✅ Understanding recent work is priority
- ❌ You don't mind answering tech stack questions

**Run Neither (0 min) if:**
- ✅ You need to start immediately
- ✅ Codebase is very small (<500 LOC)
- ✅ You prefer full manual control
- ✅ You don't mind answering all questions

### Q: Which option should I choose for my project?

**A:** Use this decision tree:

```
Time available?
├─ < 10 min → Neither (manual questions)
├─ 10-20 min → Git History Only (get velocity context)
├─ 60-105 min → Codebase Audit Only (get code quality)
└─ 70-125 min → Both (get maximum context)

OR

What's most valuable?
├─ Skip tech stack questions → Codebase Audit Only
├─ Understand recent work → Git History Only
├─ Both of above → Both Analyses
└─ Fastest start → Neither
```

### Q: Can I run the other analysis later?

**A:** Not easily. Both analyses are designed to run before first sprint planning. If you skip them during `/vibey`, you would need to:
- Manually run the audit workflow later
- Regenerate the audit report
- Update project-config.yaml manually

**Recommendation:** Choose "Both" if you have time - it's hard to go back later.

### Q: What's the difference between Codebase Audit and Architecture Review?

**A:**
- **Codebase Audit (this workflow):** Pre-initialization analysis to inform setup. Runs once during `/vibey`. Detects tech stack, tests, security for sprint planning. Optional.
- **Architecture Review:** Ongoing workflow for reviewing architecture design. Runs multiple times during development (preventive, validation, reactive). Creates ADRs and recommendations. Different purpose.

**Use both when:** Initializing Vibey on mature codebase - run Codebase Audit first during `/vibey`, then Architecture Review later if issues found during sprints.

---

## Workflow Metrics

### By Duration

**Immediate** (< 2 hours):
- Codebase Audit & Discovery (60-105 min)
- Integration Only (30min - 2hr)

**Short** (1-3 days):
- Single Feature Development (1-3 days)
- Architecture Review (2-3 days)
- Logging Audit (2-3 days)

**Medium** (3-8 days):
- Sprint Planning (3-5 days)
- Weekly Sprint (3-5 days)
- Performance Optimization (5-8 days)

**Long** (12+ days):
- Infrastructure Setup (12-18 days)
- ML Model Development (15-25 days)

### By Complexity

**Low:**
- Codebase Audit & Discovery (automated analysis)
- Integration Only

**Medium:**
- Single Feature Development
- Architecture Review
- Logging Audit

**Medium-High:**
- Performance Optimization
- Sprint Planning
- Weekly Sprint

**High:**
- Infrastructure Setup
- ML Model Development

---

## Getting Help

**If you're still unsure which workflow to use:**

1. **Describe your task:** What do you need to accomplish?
2. **Check duration:** How much time do you have?
3. **Check prerequisites:** Do you have what each workflow needs?
4. **Start simple:** When in doubt, use **Single Feature Development**
5. **Ask for help:** Consult with your team or {% if config.architecture %}{{ config.architecture.specialist }}{% else %}architecture specialist{% endif %}

**Remember:** Workflows are guidelines, not rigid rules. Adapt as needed for your specific situation.

---

## Related Documentation

**Workflow Files:**
- `workflows/planning/codebase-audit-discovery.md` (NEW - pre-initialization)
- `workflows/sprint-planning.md`
- `workflows/single-feature-development.md`
- `workflows/weekly-sprint.md`
- `workflows/integration-only.md`
- `workflows/ml-model-development.md`
- `workflows/infrastructure-setup.md`
- `workflows/performance-optimization.md`
- `workflows/architecture-review.md`
- `workflows/logging-audit.md`

**Configuration:**
- `schema.yaml` - Full configuration schema
- `examples/` - Example project configurations

---

**Created:** 2025-11-04
**Status:** ✅ Complete
**Version:** 1.0
**Framework:** Vibey Agent Framework
