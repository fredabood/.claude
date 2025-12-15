# Phase 6.1: Friction Analysis & Gap Identification

## Sprint Overview
Analyze all documentation, user journeys, and implementation for friction points and gaps. This is the diagnostic phase that feeds into Phase 6.2's recommendations.

## Tasks

### Task 1: Analyze reference guide friction points (01KC81GRE5RYQCQFWQD4GSC5V1)

**Objective**: Review CLI and MCP reference guides for friction.

**Steps**:
1. Read through docs/reference/CLI_REFERENCE.md
   - Check for unclear command descriptions
   - Identify missing examples
   - Note confusing organization
   - Find missing cross-references
2. Read through docs/reference/MCP_REFERENCE.md
   - Same analysis as CLI reference
3. Document findings in REFERENCE_GUIDE_FRICTION.md

**Analysis Criteria**:
- Clarity: Is the description understandable without prior knowledge?
- Examples: Does each command have a usage example?
- Organization: Are related commands grouped logically?
- Cross-references: Do commands reference related commands?

**Deliverables**:
- REFERENCE_GUIDE_FRICTION.md

---

### Task 2: Analyze user journey friction points (01KC81GRE5RYQCQFWQD4GSC5V2)

**Objective**: Walk through each persona journey looking for friction.

**Steps**:
1. Review docs/journeys/JOURNEY_NEW_USER.md
   - Execute each step mentally or actually
   - Note confusing steps, missing prerequisites
2. Review docs/journeys/JOURNEY_ACTIVE_DEVELOPER.md
3. Review docs/journeys/JOURNEY_PROJECT_LEAD.md
4. Review docs/journeys/JOURNEY_CONTRIBUTOR.md (if exists)
5. Document friction points in USER_JOURNEY_FRICTION.md

**Analysis Criteria**:
- Prerequisites: Are all prerequisites clearly stated?
- Flow: Does one step logically lead to the next?
- Outcomes: Is the expected outcome of each step clear?
- Completeness: Are there any missing steps?

**Deliverables**:
- USER_JOURNEY_FRICTION.md

---

### Task 3: Analyze walkthrough friction points (01KC81GRE5RYQCQFWQD4GSC5V3)

**Objective**: Execute each walkthrough step-by-step, documenting issues.

**Steps**:
1. Execute docs/walkthroughs/WALKTHROUGH_NEW_USER.md
   - Run each command
   - Compare actual vs expected output
   - Note outdated commands
2. Execute docs/walkthroughs/WALKTHROUGH_ACTIVE_DEVELOPER.md
3. Execute docs/walkthroughs/WALKTHROUGH_CONTRIBUTOR.md
4. Execute docs/walkthroughs/WALKTHROUGH_PROJECT_LEAD.md
5. Document findings in WALKTHROUGH_FRICTION.md

**Analysis Criteria**:
- Commands: Do all commands work as documented?
- Output: Does actual output match expected output?
- Steps: Are all steps present and in correct order?
- Instructions: Are instructions clear and unambiguous?

**Deliverables**:
- WALKTHROUGH_FRICTION.md

---

### Task 4: Analyze context engineering gaps (01KC81GRE5RYQCQFWQD4GSC5V4)

**Objective**: Compare context engineering design against implementation.

**Steps**:
1. Review context engineering design docs in .vibey/roadmap/context/
2. Check vibey/operations/context/ implementation
3. Identify:
   - Unimplemented features
   - Partial implementations
   - Design/implementation mismatches
4. Document in CONTEXT_ENGINEERING_GAPS.md

**Deliverables**:
- CONTEXT_ENGINEERING_GAPS.md

---

### Task 5: Identify redundant/obsolete code (01KC81GRE6NHSPP7X34M5MT21V)

**Objective**: Compile list of code made obsolete by redesigns.

**Steps**:
1. Review Phase 1 audit findings
2. Check for:
   - Dead code (unreachable functions)
   - Redundant functions (duplicate logic)
   - Deprecated patterns (old approaches)
3. Use grep/ast analysis to find unused imports/functions
4. Document in OBSOLETE_CODE_INVENTORY.md

**Deliverables**:
- OBSOLETE_CODE_INVENTORY.md

---

### Task 6: Prioritize friction remediation (01KC81GRE6NHSPP7X34M5MT21W)

**Objective**: Score and prioritize all identified friction points.

**Steps**:
1. Collect all friction findings from previous tasks
2. Score each friction point:
   - User Impact (1-5): How much does this affect users?
   - Fix Complexity (1-5): How hard is this to fix?
   - Frequency (1-5): How often is this encountered?
3. Calculate priority score: Impact * Frequency / Complexity
4. Sort by priority score
5. Output to FRICTION_REMEDIATION_PRIORITY.yaml

**Deliverables**:
- FRICTION_REMEDIATION_PRIORITY.yaml

---

### Task 7: Create Friction Analysis Report (01KC81GRE6NHSPP7X34M5MT21X)

**Objective**: Consolidate all friction analysis into comprehensive report.

**Steps**:
1. Consolidate findings from all previous tasks
2. Create executive summary
3. Organize by category:
   - Reference Guide Friction
   - User Journey Friction
   - Walkthrough Friction
   - Context Engineering Gaps
   - Obsolete Code
4. Include prioritized remediation list
5. Output to FRICTION_ANALYSIS_REPORT.md

**Deliverables**:
- FRICTION_ANALYSIS_REPORT.md

---

## Success Criteria
- All friction points documented and categorized
- Priority scores assigned to each friction point
- Comprehensive report ready for Phase 6.2 recommendations
- Clear connection between findings and recommended actions
