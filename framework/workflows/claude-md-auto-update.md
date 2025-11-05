# CLAUDE.md Auto-Update Workflow

**Purpose:** Automatically keep CLAUDE.md up to date as the project evolves
**Agent:** {% if config.agents %}{{ config.agents.documentation_maintenance or 'Documentation Maintenance Engineer' }}{% else %}Documentation Maintenance Engineer{% endif %}
**Trigger:** Sprint completion, monthly archival, production score changes
**Duration:** 20-30 minutes
**Output:** Updated CLAUDE.md with current project state

---

## 📋 Workflow Overview

This workflow ensures CLAUDE.md remains the accurate, concise single source of truth for project state by automatically updating it at key milestones. It prevents documentation drift, reduces manual maintenance burden, and ensures AI assistants always have current context.

**Key Benefits:**
- Eliminates manual documentation maintenance
- Prevents documentation drift
- Ensures AI context stays current
- Maintains optimal file size (< 600 lines recommended)
- Archives old achievements automatically

---

## 🎯 Workflow Triggers

### Trigger 1: Sprint Completion (Primary)
**When:** After completing a sprint and creating the sprint completion commit
**Frequency:** After each sprint (varies by sprint cadence)
**Priority:** High (must complete before next sprint starts)

**Trigger Condition:**
```bash
# Detects new sprint completion in ROADMAP.md
if git diff HEAD~1 ROADMAP.md | grep "✅ v[0-9]\+\.[0-9]\+\.[0-9]\+ COMPLETE"; then
    trigger_claude_md_update --sprint-complete
fi
```

---

### Trigger 2: Monthly Archival (Scheduled)
**When:** 1st of each month at 00:00 UTC (or your preferred schedule)
**Frequency:** Monthly
**Priority:** Medium (keeps file size manageable)

**Trigger Condition:**
```bash
# Cron job or scheduled workflow
if [ $(date +%d) -eq 01 ]; then
    trigger_claude_md_update --monthly-archival
fi
```

**Purpose:** Archive achievements older than 30 days to maintain CLAUDE.md readability

---

### Trigger 3: Production Score Change (Event-Driven)
**When:** {% if config.monitoring %}{{ config.monitoring.metric or 'Production score' }}{% else %}Production score{% endif %} changes by ≥5 points
**Frequency:** Ad-hoc (typically after major infrastructure or quality improvements)
**Priority:** Medium

**Trigger Condition:**
{% if config.technology_stack.backend.language == 'python' %}```python
# In monitoring system
if abs(new_score - old_score) >= 5:
    trigger_claude_md_update(
        type="score_update",
        old_score=old_score,
        new_score=new_score,
        reason=reason
    )
```{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}```typescript
// In monitoring system
if (Math.abs(newScore - oldScore) >= 5) {
    triggerClaudeMdUpdate({
        type: 'score_update',
        oldScore: oldScore,
        newScore: newScore,
        reason: reason
    });
}
```{% elif config.technology_stack.backend.language == 'java' %}```java
// In monitoring system
if (Math.abs(newScore - oldScore) >= 5) {
    triggerClaudeMdUpdate(
        UpdateType.SCORE_UPDATE,
        oldScore,
        newScore,
        reason
    );
}
```{% else %}```
# In your monitoring system
if score_change >= 5:
    trigger_claude_md_update(score_change)
```{% endif %}

---

### Trigger 4: Manual Invocation (On-Demand)
**When:** CLAUDE.md is visibly out of sync with project state
**Frequency:** As needed
**Priority:** High when invoked

**Trigger Condition:**
```bash
# Manual command
./scripts/update-claude-md.sh --check-and-update
```

---

## 🔄 Workflow Steps

### Step 1: Detect Changes (5 minutes)

**Objective:** Identify what needs updating in CLAUDE.md

**Agent:** {% if config.agents %}{{ config.agents.documentation_maintenance or 'Documentation Maintenance Engineer' }}{% else %}Documentation Maintenance Engineer{% endif %}

**Actions:**
1. Read current CLAUDE.md
2. Read ROADMAP.md for sprint status
3. Check git commits since last CLAUDE.md update
4. {% if config.monitoring %}Query {{ config.monitoring.platform or 'monitoring system' }} for current scores/metrics{% else %}Query monitoring for current metrics{% endif %}
5. {% if config.testing %}Check {{ config.testing.backend.framework or 'test' }} coverage reports{% else %}Check test coverage reports{% endif %}
6. {% if config.project.type == 'api' %}Count API endpoints{% elif config.project.type == 'web-app' %}Count UI components{% elif config.project.type == 'data-platform' %}Count data sources integrated{% elif config.project.type == 'ml' %}Count ML models deployed{% else %}Count major features{% endif %}

**Detection Checks:**

| Check | File/Source | What to Look For |
|-------|-------------|------------------|
| Sprint Completion | ROADMAP.md | New "✅ v{X}.{Y} COMPLETE" entry |
| {% if config.monitoring %}{{ config.monitoring.metric or 'Production Score' }}{% else %}Production Score{% endif %} | {% if config.monitoring %}{{ config.monitoring.platform or 'Monitoring dashboard' }}{% else %}Monitoring dashboard{% endif %} | Score change ≥ 5 points |
| {% if config.project.type == 'data-platform' %}Data Sources{% elif config.project.type == 'api' %}API Endpoints{% elif config.project.type == 'ml' %}ML Models{% else %}Features{% endif %} | {% if config.project.structure %}{{ config.project.structure.source_directory or 'src/' }}{% else %}Source code{% endif %} | New {% if config.project.type == 'data-platform' %}data source{% elif config.project.type == 'api' %}endpoint{% elif config.project.type == 'ml' %}model{% else %}feature{% endif %} files |
| Test Coverage | {% if config.testing %}.coverage, {{ config.testing.backend.framework or 'test' }} output{% else %}Test reports{% endif %} | Coverage % change ≥ 5% |
| New Policies | docs/operations/*.md | New policy documents |
| Archival Needed | CLAUDE.md Recent Achievements | Achievements > 30 days old |

**Output:**
```yaml
changes_detected:
  - type: sprint_completion
    version: v{{ config.current_version or '1.0.0' }}
    requires_update: true
  - type: {% if config.project.type == 'data-platform' %}data_sources{% elif config.project.type == 'api' %}api_endpoints{% elif config.project.type == 'ml' %}ml_models{% else %}features{% endif %}
    new_count: [N]
    old_count: [N-X]
    requires_update: true
  - type: monthly_archival
    achievements_to_archive: [N]
    requires_update: true
```

**Success Criteria:**
- ✅ All checks completed
- ✅ Change list generated
- ✅ No false positives (verified changes are real)

---

### Step 2: Gather Context (5 minutes)

**Objective:** Collect detailed information for each detected change

**Agent:** {% if config.agents %}{{ config.agents.documentation_maintenance or 'Documentation Maintenance Engineer' }}{% else %}Documentation Maintenance Engineer{% endif %}

**Actions:**

**For Sprint Completion:**
1. Read `docs/sprints/v{X}.{Y}/SPRINT_V{X}.{Y}_PLAN.md` (or your sprint plan location)
2. Extract: sprint name, duration, objectives, deliverables
3. Read sprint tracking/status docs for actual outcomes
4. Note {% if config.monitoring %}{{ config.monitoring.metric or 'production score' }}{% else %}production score{% endif %} impact (if any)

**For {% if config.monitoring %}{{ config.monitoring.metric or 'Production Score' }}{% else %}Production Score{% endif %} Change:**
1. Read {% if config.monitoring %}{{ config.monitoring.platform or 'monitoring dashboard' }}{% else %}production readiness assessment{% endif %}
2. Identify what changed (security improvements, new infrastructure, etc.)
3. Quantify impact (+X points)

**For {% if config.project.type == 'data-platform' %}Data Source{% elif config.project.type == 'api' %}API Endpoint{% elif config.project.type == 'ml' %}ML Model{% else %}Feature{% endif %} Integration:**
1. {% if config.project.type == 'data-platform' %}List new data source files
2. Check integration status
3. Note if credentials/API keys are required{% elif config.project.type == 'api' %}List new API endpoints
2. Check if integrated in main router
3. Note authentication requirements{% elif config.project.type == 'ml' %}List new ML models
2. Check if deployed
3. Note performance metrics{% else %}List new feature files
2. Check integration status
3. Note dependencies{% endif %}

**For Test Coverage:**
1. Read {% if config.testing %}.coverage or {{ config.testing.backend.framework or 'test' }} JSON report{% else %}test coverage reports{% endif %}
2. Extract current coverage percentage
3. Extract test count
4. Compare with CLAUDE.md current values

**For Policy Changes:**
1. Read new policy document in `docs/operations/`
2. Extract: policy name, effective date, key requirements
3. Identify which section of CLAUDE.md needs update (Critical Rules, Security & Production, etc.)

**For Monthly Archival:**
1. Parse Recent Achievements section in CLAUDE.md
2. Extract achievement entries with dates
3. Filter to achievements older than 30 days
4. Prepare full text for archival

**Output:**
```yaml
context_gathered:
  sprint_v{{ config.current_version or '1.0.0' }}:
    name: "{{ config.current_sprint_name or 'Sprint Name' }}"
    duration: "[N] weeks"
    deliverables:
      - "Deliverable 1"
      - "Deliverable 2"
    key_achievement: "Most significant outcome"
    {% if config.monitoring %}{{ config.monitoring.metric or 'prod_score' }}_impact: null{% endif %}

  {% if config.project.type == 'data-platform' %}data_sources:
    new: ["source1.py", "source2.py", ...]
    integrated: true
    requires_credentials: false
  {% elif config.project.type == 'api' %}api_endpoints:
    new: ["/api/endpoint1", "/api/endpoint2", ...]
    registered: true
    authenticated: true
  {% elif config.project.type == 'ml' %}ml_models:
    new: ["model1", "model2", ...]
    deployed: true
    metrics: {...}
  {% else %}features:
    new: ["feature1", "feature2", ...]
    integrated: true
  {% endif %}

  archival:
    - title: "Achievement Title"
      date: "YYYY-MM-DD"
      content: "..."
```

**Success Criteria:**
- ✅ Context collected for all detected changes
- ✅ All file reads successful
- ✅ Data validated (no malformed dates, scores, etc.)

---

### Step 3: Generate Updates (10 minutes)

**Objective:** Create precise edits for each section of CLAUDE.md

**Agent:** {% if config.agents %}{{ config.agents.documentation_maintenance or 'Documentation Maintenance Engineer' }}{% else %}Documentation Maintenance Engineer{% endif %}

**Actions:**

**3.1: Update Current Project State (if needed)**

**Section:** Top of CLAUDE.md (typically lines 10-25)

**Updates:**
- Versions Complete: Add new version (e.g., "✅ v1.2.0")
- {% if config.monitoring %}{{ config.monitoring.metric or 'Production Score' }}: Update if changed{% endif %}
- {% if config.project.type == 'data-platform' %}Data Sources: Update count{% elif config.project.type == 'api' %}API Endpoints: Update count{% elif config.project.type == 'ml' %}ML Models: Update count{% else %}Features: Update status{% endif %}
- Test Coverage: Update if changed ≥5%

**Example Edit:**
```markdown
OLD:
**Versions Complete:** ✅ v1.0.0 | ✅ v1.1.0{% if config.monitoring %}
**{{ config.monitoring.metric or 'Production Score' }}:** 85/100{% endif %}
**{% if config.project.type == 'data-platform' %}Data Sources{% elif config.project.type == 'api' %}API Endpoints{% elif config.project.type == 'ml' %}ML Models{% else %}Features{% endif %}:** [N] integrated

NEW:
**Versions Complete:** ✅ v1.0.0 | ✅ v1.1.0 | ✅ v1.2.0{% if config.monitoring %}
**{{ config.monitoring.metric or 'Production Score' }}:** 90/100{% endif %}
**{% if config.project.type == 'data-platform' %}Data Sources{% elif config.project.type == 'api' %}API Endpoints{% elif config.project.type == 'ml' %}ML Models{% else %}Features{% endif %}:** [N+X] integrated
```

---

**3.2: Add to Completed Versions (if sprint complete)**

**Section:** Completed Versions section in CLAUDE.md

**Insert After:** Last completed version (maintain chronological order, newest first)

**Template:**
```markdown
**✅ v{X}.{Y} COMPLETE ({DATE}):** {Sprint Name}
- **Duration:** {N} weeks/days
- **Deliverables:** {Brief list}
- **Key Achievement:** {Most significant outcome}
```

**Example:**
```markdown
**✅ v1.2.0 COMPLETE ({{ "now"|date("%Y-%m-%d") }}):** {% if config.project.type == 'data-platform' %}Data Pipeline Optimization{% elif config.project.type == 'api' %}API Rate Limiting{% elif config.project.type == 'ml' %}Model Performance Improvements{% else %}Feature Expansion{% endif %}
- **Duration:** {{ config.sprint_duration or '2' }} weeks
- **Deliverables:** {% if config.project.type == 'data-platform' %}5 new data sources, caching layer, monitoring{% elif config.project.type == 'api' %}Rate limiting, 10 new endpoints, auth improvements{% elif config.project.type == 'ml' %}3 models retrained, inference optimization, monitoring{% else %}New features, bug fixes, performance improvements{% endif %}
- **Key Achievement:** {% if config.project.type == 'data-platform' %}50% reduction in processing time{% elif config.project.type == 'api' %}99.9% API uptime{% elif config.project.type == 'ml' %}20% model accuracy improvement{% else %}Major feature milestone{% endif %}
```

---

**3.3: Update Current Work**

**Section:** Current Work or Sprint Status section

**Updates:**
- Update completed versions
- Update current sprint focus
- Update next sprint plans

**Example Edit:**
```markdown
OLD:
**Current Sprint:** v1.2.0 ({% if config.project.type == 'data-platform' %}Data Pipeline Optimization{% elif config.project.type == 'api' %}API Rate Limiting{% elif config.project.type == 'ml' %}Model Performance{% else %}Feature Development{% endif %})
**Next:** {% if config.project.type == 'data-platform' %}Real-time processing (v1.3.0){% elif config.project.type == 'api' %}GraphQL support (v1.3.0){% elif config.project.type == 'ml' %}Model deployment (v1.3.0){% else %}Next feature set (v1.3.0){% endif %}

NEW:
**Completed:** v1.0.0-v1.2.0
**Current Sprint:** v1.3.0 ({% if config.project.type == 'data-platform' %}Real-time Processing{% elif config.project.type == 'api' %}GraphQL Support{% elif config.project.type == 'ml' %}Production Deployment{% else %}Advanced Features{% endif %})
**Next:** {% if config.project.type == 'data-platform' %}Streaming architecture (v1.4.0){% elif config.project.type == 'api' %}Websockets (v1.4.0){% elif config.project.type == 'ml' %}AutoML integration (v1.4.0){% else %}Performance optimization (v1.4.0){% endif %}
```

---

**3.4: Add to Recent Achievements (if major achievement)**

**Section:** Recent Achievements (maintain rolling 30-day window)

**Insert At:** Top of section (maintain reverse chronological order)

**Template:**
```markdown
### {Achievement Title} ({DATE})

{Brief description of what was achieved}

**{% if config.project.type == 'data-platform' %}New Data Sources{% elif config.project.type == 'api' %}New Endpoints{% elif config.project.type == 'ml' %}Model Improvements{% else %}New Features{% endif %}:**
- ✅ **{Item 1}** - {Description}
- ✅ **{Item 2}** - {Description}

**{Benefits/Impact Section}:**
- {Benefit 1}
- {Benefit 2}

**Status:** {Current status}

---
```

**Example:**
```markdown
### {% if config.project.type == 'data-platform' %}Real-time Data Processing Complete{% elif config.project.type == 'api' %}GraphQL API Launched{% elif config.project.type == 'ml' %}Production Model Deployment{% else %}Major Feature Release{% endif %} ({{ "now"|date("%Y-%m-%d") }})

{% if config.project.type == 'data-platform' %}Implemented real-time data processing pipeline with sub-second latency.

**Deliverables:**
- ✅ **Streaming Pipeline** - Apache Kafka integration
- ✅ **Real-time Transformations** - In-memory processing
- ✅ **Monitoring Dashboard** - Latency and throughput metrics

**Performance:**
- Sub-second end-to-end latency
- 10,000 events/second throughput
- 99.9% uptime

{% elif config.project.type == 'api' %}Launched GraphQL API with real-time subscriptions.

**Deliverables:**
- ✅ **GraphQL Schema** - Type-safe queries and mutations
- ✅ **Subscriptions** - Real-time data updates
- ✅ **Performance** - Query optimization and caching

**Coverage:**
- 50+ GraphQL queries
- 20+ mutations
- Real-time subscriptions

{% elif config.project.type == 'ml' %}Deployed ML models to production with automated retraining.

**Deliverables:**
- ✅ **Model Deployment** - {{ config.ml_platform.model_registry or 'Production' }} deployment
- ✅ **Automated Retraining** - Weekly model updates
- ✅ **Monitoring** - Drift detection and alerts

**Performance:**
- 95% model accuracy
- <100ms inference latency
- Automated drift detection

{% else %}Released major features with enhanced user experience.

**Deliverables:**
- ✅ **New Features** - Core functionality expansion
- ✅ **Performance** - 50% faster response times
- ✅ **Quality** - 90%+ test coverage

**Impact:**
- Improved user satisfaction
- Enhanced performance
- Production-ready quality

{% endif %}**Status:** v1.3.0 complete, production ready

---
```

---

**3.5: Update Known Issues (if needed)**

**Section:** Known Issues section

**Actions:**
- Add new issues discovered
- Remove resolved issues
- Update issue status

**Example Edit (adding issue):**
```markdown
{% if config.project.type == 'data-platform' %}**Data Source Issues:**
- Source A: Rate limiting more aggressive than documented
- Source B: Requires authentication (credentials needed)
{% elif config.project.type == 'api' %}**API Issues:**
- Rate limiting needs tuning for high-volume clients
- Some endpoints require additional authentication
{% elif config.project.type == 'ml' %}**Model Issues:**
- Model A: Drift detected on recent data
- Model B: Requires retraining
{% else %}**Known Issues:**
- Feature A: Performance degradation under load
- Feature B: Edge case handling needed
{% endif %}```

**Example Edit (removing issue):**
```markdown
OLD:
- {% if config.project.type == 'api' %}Authentication bug on /api/users endpoint{% else %}Bug in feature X{% endif %}

REMOVED (issue resolved in v1.2.0)
```

---

**3.6: Archive Old Achievements (monthly)**

**Section:** Recent Achievements

**Archive To:** `docs/reference/ACHIEVEMENTS_ARCHIVE.md`

**Process:**
1. Identify achievements with date < (today - 30 days)
2. Extract full achievement text
3. Read ACHIEVEMENTS_ARCHIVE.md (create if doesn't exist)
4. Prepend archived achievements to archive file
5. Remove from CLAUDE.md

**Archive File Structure:**
```markdown
# {{ config.project.name or 'Project' }} Achievements Archive

**Last Updated:** {TODAY} ({MONTH YEAR} achievements archived)
**Active Achievements:** See CLAUDE.md "Recent Achievements" section (rolling 30-day window)
**Created:** {DATE}

This file contains detailed historical information about project achievements older than 30 days.

---

## {MONTH YEAR} Achievements

### {Achievement Title} ({DATE})
{Full achievement text}

---

### {Achievement Title} ({DATE})
{Full achievement text}

---

## {PREVIOUS MONTH} Achievements
...
```

**CLAUDE.md Update:**
Remove archived achievements, keeping only last 30 days.

---

**Output:**
```yaml
edits_generated:
  - section: "Current Project State"
    line_start: [N]
    line_end: [N]
    old_text: "✅ v1.0.0 | ✅ v1.1.0"
    new_text: "✅ v1.0.0 | ✅ v1.1.0 | ✅ v1.2.0"

  - section: "Completed Versions"
    line_start: [N]
    action: insert_after
    content: |
      **✅ v1.2.0 COMPLETE (YYYY-MM-DD):** Sprint Name
      - **Duration:** [N] weeks
      - **Deliverables:** Brief list
      - **Key Achievement:** Significant outcome
```

**Success Criteria:**
- ✅ All necessary edits generated
- ✅ Content follows templates
- ✅ Formatting consistent
- ✅ Chronological order maintained

---

### Step 4: Apply Updates (5 minutes)

**Objective:** Execute all edits to CLAUDE.md and ACHIEVEMENTS_ARCHIVE.md

**Agent:** {% if config.agents %}{{ config.agents.documentation_maintenance or 'Documentation Maintenance Engineer' }}{% else %}Documentation Maintenance Engineer{% endif %}

**Actions:**
1. For each edit in edits_generated, use Edit tool
2. Verify each edit succeeded
3. If archival needed, update ACHIEVEMENTS_ARCHIVE.md
4. Verify file structure intact

**Edit Execution:**
{% if config.technology_stack.backend.language == 'python' %}```python
# Execute edits
for edit in edits_generated:
    if edit['action'] == 'replace':
        Edit(
            file_path='CLAUDE.md',
            old_string=edit['old_text'],
            new_string=edit['new_text']
        )
    elif edit['action'] == 'insert_after':
        # Read file, find line, insert content
        insert_content(edit)
```{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}```typescript
// Execute edits
for (const edit of editsGenerated) {
    if (edit.action === 'replace') {
        await editFile({
            filePath: 'CLAUDE.md',
            oldString: edit.oldText,
            newString: edit.newText
        });
    } else if (edit.action === 'insert_after') {
        await insertContent(edit);
    }
}
```{% elif config.technology_stack.backend.language == 'java' %}```java
// Execute edits
for (Edit edit : editsGenerated) {
    if (edit.getAction().equals("replace")) {
        editFile(
            "CLAUDE.md",
            edit.getOldText(),
            edit.getNewText()
        );
    } else if (edit.getAction().equals("insert_after")) {
        insertContent(edit);
    }
}
```{% else %}```
# Execute all edits sequentially
for each edit:
    apply edit to CLAUDE.md
    verify success
```{% endif %}

**Rollback Plan:**
If any edit fails:
1. Restore CLAUDE.md from git HEAD
2. Log error with specific edit that failed
3. Create issue for human review

**Success Criteria:**
- ✅ All edits applied successfully
- ✅ No syntax errors in markdown
- ✅ File structure intact
- ✅ Archive updated if needed

---

### Step 5: Verify & Quality Check (3 minutes)

**Objective:** Ensure updates are correct and CLAUDE.md meets quality standards

**Agent:** {% if config.agents %}{{ config.agents.documentation_maintenance or 'Documentation Maintenance Engineer' }}{% else %}Documentation Maintenance Engineer{% endif %}

**Verification Checks:**

**1. Size Check:**
```bash
{% if config.scripts %}{{ config.scripts.check_docs or 'python3 scripts/check_doc_sizes.py' }}{% else %}wc -l CLAUDE.md{% endif %}
# Recommended: < 100KB (~600 lines)
# Warning: > 600 lines
```

**2. Format Check:**
- All markdown properly formatted
- No broken section headers
- Emoji usage consistent (if used)
- Bullet points aligned

**3. Accuracy Check:**
- Version numbers match ROADMAP.md
- {% if config.monitoring %}{{ config.monitoring.metric or 'Production score' }} matches {{ config.monitoring.platform or 'monitoring' }}{% endif %}
- {% if config.project.type == 'data-platform' %}Data source count matches source directory{% elif config.project.type == 'api' %}API endpoint count matches routes{% elif config.project.type == 'ml' %}Model count matches registry{% else %}Feature count matches implementation{% endif %}
- Test coverage matches test reports
- All dates in YYYY-MM-DD format

**4. Completeness Check:**
- No "TBD" or "TODO" placeholders
- No broken internal links
- All sections present
- Recent Achievements ≤ 5 entries (roughly 30 days)

**5. Chronological Check:**
- Completed Versions: Newest first
- Recent Achievements: Newest first
- Dates in proper order

**Error Handling:**
- If size > 600 lines: Flag for review, suggest additional archival
- If accuracy check fails: Rollback, log issue
- If format broken: Attempt auto-fix, else rollback

**Output:**
```yaml
verification_results:
  size_check: pass ([N] lines, [N]KB)
  format_check: pass
  accuracy_check: pass
  completeness_check: pass
  chronological_check: pass
  overall: PASS ✅
```

**Success Criteria:**
- ✅ All verification checks pass
- ✅ CLAUDE.md < 600 lines (recommended)
- ✅ No accuracy issues detected
- ✅ File properly formatted

---

### Step 6: Commit Changes (2 minutes)

**Objective:** Commit updated CLAUDE.md to version control

**Agent:** {% if config.agents %}{{ config.agents.git_committer or 'Git Committer' }}{% else %}Git Committer{% endif %}

**Actions:**
1. Stage files (CLAUDE.md, ACHIEVEMENTS_ARCHIVE.md if updated)
2. Create commit with descriptive message
3. Push to remote repository

**Commit Message Templates:**

**Sprint Completion:**
```
docs: Update CLAUDE.md - sprint v{X}.{Y} complete

- Added v{X}.{Y} to Versions Complete{% if config.monitoring %}
- Updated {{ config.monitoring.metric or 'Production Score' }} (if changed){% endif %}
- Added sprint summary to Completed Versions
- Added achievement to Recent Achievements
```

**Monthly Archival:**
```
docs: Archive {MONTH YEAR} achievements from CLAUDE.md

- Archived {N} achievements older than 30 days
- Moved to ACHIEVEMENTS_ARCHIVE.md
- Kept Recent Achievements focused on last 30 days
```

**{% if config.monitoring %}{{ config.monitoring.metric or 'Production Score' }}{% else %}Score{% endif %} Update:**
```
docs: Update CLAUDE.md - {% if config.monitoring %}{{ config.monitoring.metric or 'production score' }}{% else %}production score{% endif %} {OLD} → {NEW}

- Updated {% if config.monitoring %}{{ config.monitoring.metric or 'Production Score' }}{% else %}Production Score{% endif %} in Current Project State
- Added {% if config.project.type == 'data-platform' %}infrastructure{% elif config.project.type == 'api' %}performance{% elif config.project.type == 'ml' %}model quality{% else %}quality{% endif %} achievement to Recent Achievements
```

**Success Criteria:**
- ✅ Files committed successfully
- ✅ Commit message follows convention
- ✅ Changes pushed to remote

---

## 📊 Workflow Metrics

**Expected Duration:**
- Sprint Completion Update: 20-25 minutes
- Monthly Archival: 15-20 minutes
- {% if config.monitoring %}{{ config.monitoring.metric or 'Production Score' }}{% else %}Score{% endif %} Update: 10-15 minutes
- Manual Full Sync: 25-30 minutes

**Success Rate Target:** 95%+ automated updates succeed without human intervention

**Quality Targets:**
- CLAUDE.md always < 600 lines (recommended)
- Recent Achievements always ≤ 5 entries (30 days)
- 0 stale information (version numbers, scores, etc.)
- 100% of changes reflected within 1 hour of trigger

---

## 🔗 Related Workflows

**Upstream (Triggers This Workflow):**
- **Sprint Completion Workflow** - Triggers this workflow after sprint commit
- **Sprint Planning Workflow** - Triggers update for new sprint focus

**Downstream (This Workflow Triggers):**
- **Git Commit Workflow** - Commits CLAUDE.md changes

**Parallel Workflows:**
- Can run in parallel with README updates
- Should run AFTER sprint completion documentation

---

## ✅ Workflow Success Criteria

Workflow is successful when:

1. ✅ All detected changes are accurately reflected in CLAUDE.md
2. ✅ CLAUDE.md passes all verification checks (size, format, accuracy)
3. ✅ Old achievements archived if monthly trigger
4. ✅ Changes committed to version control with proper message
5. ✅ No manual intervention required
6. ✅ Execution time within expected duration

---

## 🚨 Error Scenarios & Handling

### Scenario 1: CLAUDE.md Locked (Concurrent Edit)
**Cause:** Another process editing CLAUDE.md simultaneously
**Detection:** Edit tool returns file locked error
**Handling:**
1. Wait 30 seconds
2. Retry up to 3 times
3. If still locked, fail gracefully with notification

**Notification:**
```
⚠️ CLAUDE.md Update Failed: File Locked
Another process is editing CLAUDE.md. Manual intervention required.
Detected changes: {list}
```

---

### Scenario 2: Section Structure Changed
**Cause:** CLAUDE.md manually edited, section headers moved/renamed
**Detection:** Edit tool can't find expected section
**Handling:**
1. Log warning with specific section not found
2. Attempt to find similar section (fuzzy match)
3. If found, proceed with edit
4. If not found, append to end of file with note

**Notification:**
```
⚠️ CLAUDE.md Update Warning: Section Not Found
Could not find "{section_name}" at expected location.
Appended update to end of file. Manual review recommended.
```

---

### Scenario 3: Size Exceeds 600 Lines
**Cause:** More content added than archived, or large sprint summary
**Detection:** Line count > 600 after updates
**Handling:**
1. Complete the update (don't rollback)
2. Flag for human review
3. Suggest additional entries for archival

**Notification:**
```
⚠️ CLAUDE.md Size Warning: {N} lines (target: < 600)
Updates applied successfully but file size exceeds target.
Suggestions:
- Archive achievements older than 20 days (instead of 30)
- Condense Completed Versions entries (3 lines max per sprint)
- Move detailed sprint info to ACHIEVEMENTS_ARCHIVE.md
```

---

### Scenario 4: Accuracy Check Fails
**Cause:** Detected changes don't match source data (edge case/bug)
**Detection:** Verification step finds mismatch
**Handling:**
1. Rollback all changes (git restore CLAUDE.md)
2. Log detailed error report
3. Notify for manual investigation

**Notification:**
```
❌ CLAUDE.md Update Failed: Accuracy Check
Verification found mismatches:
{% if config.monitoring %}- {{ config.monitoring.metric or 'Production Score' }} in CLAUDE.md (X) doesn't match {{ config.monitoring.platform or 'monitoring' }} (Y){% endif %}
- {% if config.project.type == 'data-platform' %}Data source{% elif config.project.type == 'api' %}Endpoint{% elif config.project.type == 'ml' %}Model{% else %}Feature{% endif %} count mismatch (CLAUDE.md: X, actual: Y)

Changes rolled back. Manual investigation required.
```

---

### Scenario 5: Archive File Missing
**Cause:** ACHIEVEMENTS_ARCHIVE.md deleted or moved
**Detection:** File not found when attempting archival
**Handling:**
1. Create new ACHIEVEMENTS_ARCHIVE.md with header
2. Proceed with archival to new file
3. Log warning (in case file was intentionally moved)

**File Created:**
```markdown
# {{ config.project.name or 'Project' }} Achievements Archive

**Purpose:** Historical archive of detailed project achievements
**Active Achievements:** See CLAUDE.md "Recent Achievements" section
**Created:** {TODAY} (auto-created during archival)

---

## {CURRENT MONTH} Achievements
...
```

---

## 🎓 Example Workflow Execution

### Example: Sprint v1.2.0 Completion

**Trigger:**
```bash
# Sprint completion commit just pushed
git log -1 --pretty=format:"%s"
# Output: "feat: Complete sprint v1.2.0 - {% if config.project.type == 'data-platform' %}data pipeline optimization{% elif config.project.type == 'api' %}API rate limiting{% elif config.project.type == 'ml' %}model performance improvements{% else %}feature expansion{% endif %}"

# CLAUDE.md Auto-Update workflow triggered automatically
```

**Step 1: Detect Changes (3 min)**
- ✅ Read ROADMAP.md: Found "✅ v1.2.0 COMPLETE"
- ✅ Check CLAUDE.md: v1.2.0 NOT in Versions Complete → UPDATE NEEDED
- ✅ Check {% if config.project.type == 'data-platform' %}data sources{% elif config.project.type == 'api' %}API endpoints{% elif config.project.type == 'ml' %}ML models{% else %}features{% endif %}: [X] new items → UPDATE NEEDED
- ✅ Check {% if config.monitoring %}{{ config.monitoring.metric or 'production score' }}{% else %}production metrics{% endif %}: {% if config.monitoring %}Changed{% else %}No change{% endif %}
- ✅ Check test coverage: {% if config.testing %}{{ config.coding_standards.test_coverage.minimum or '90' }}%{% else %}No change{% endif %}

**Step 2: Gather Context (4 min)**
- ✅ Read `docs/sprints/v1.2.0/SPRINT_V1.2.0_PLAN.md`
- ✅ Extracted: "{% if config.project.type == 'data-platform' %}Data Pipeline Optimization{% elif config.project.type == 'api' %}API Rate Limiting{% elif config.project.type == 'ml' %}Model Performance{% else %}Feature Expansion{% endif %}", "{{ config.sprint_duration or '2' }} weeks", deliverables
- ✅ Confirmed integration status
- ✅ Checked {% if config.monitoring %}{{ config.monitoring.platform or 'monitoring' }}{% endif %} for metrics

**Step 3: Generate Updates (8 min)**
- ✅ Generated edit for Versions Complete (add v1.2.0)
- ✅ Generated edit for {% if config.project.type == 'data-platform' %}data source count{% elif config.project.type == 'api' %}API endpoint count{% elif config.project.type == 'ml' %}model count{% else %}feature status{% endif %}
- ✅ Generated Completed Versions entry (4 lines)
- ✅ Generated Current Work update
- ✅ Generated Recent Achievement entry (~18 lines)

**Step 4: Apply Updates (3 min)**
- ✅ Applied 5 edits to CLAUDE.md
- ✅ All edits successful
- ✅ No archival needed (not monthly trigger)

**Step 5: Verify (2 min)**
- ✅ Size check: [N] lines (< 600 ✅)
- ✅ Format check: All markdown valid
- ✅ Accuracy: v1.2.0 matches ROADMAP.md{% if config.project.type == 'data-platform' %}, data sources match directory{% elif config.project.type == 'api' %}, endpoints match routes{% elif config.project.type == 'ml' %}, models match registry{% endif %}
- ✅ Completeness: No TODOs, all links working
- ✅ Chronological: v1.2.0 after v1.1.0 ✅

**Step 6: Commit (2 min)**
- ✅ Committed CLAUDE.md with proper message
- ✅ Pushed to remote

**Total Duration:** 22 minutes ✅
**Result:** CLAUDE.md updated, accurate, < 600 lines

---

## 📅 Maintenance Schedule

**Weekly:**
- Monitor workflow execution logs
- Check for failed updates
- Review accuracy of automated updates

**Monthly:**
- Verify archival occurred on schedule
- Review ACHIEVEMENTS_ARCHIVE.md structure
- Check CLAUDE.md size trend (should stay < 600 lines)

**Quarterly:**
- Review workflow success rate (target: 95%+)
- Optimize update templates if needed
- Update workflow instructions based on edge cases

---

## 💡 Best Practices

1. **Keep CLAUDE.md Focused:** Only current/recent information (30 days)
2. **Archive Regularly:** Monthly archival prevents file bloat
3. **Maintain Templates:** Update templates as project evolves
4. **Test Updates:** Validate edits in non-production branch first
5. **Monitor Automation:** Track success rate, fix issues promptly
6. **Document Changes:** Note any CLAUDE.md structure changes in this workflow

---

**Workflow Version:** 1.0
**Created:** {{ "now"|date("%Y-%m-%d") }}
**Maintained By:** {% if config.team %}{{ config.team.name }}{% else %}Project Team{% endif %}
**Framework:** Vibey Agent Framework
