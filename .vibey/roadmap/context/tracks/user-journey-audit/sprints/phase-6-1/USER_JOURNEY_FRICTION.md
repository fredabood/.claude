# User Journey Friction Analysis

## Overview

Analysis of user journey documents for friction points that affect user experience.

**Analyzed**: 2025-12-16
**Documents Reviewed**:
- JOURNEY_NEW_USER.md
- JOURNEY_ACTIVE_DEVELOPER.md
- JOURNEY_PROJECT_LEAD.md

---

## New User Journey Friction Points

### High Impact Issues

#### 1. Documentation References May Be Broken
**Location**: Stage 1: Discovery, Actions & Documentation table
**Issue**: References `docs/getting-started/QUICK_START.md` and `docs/getting-started/USER_JOURNEY.md` - these paths may not exist
**Impact**: 4/5 - Users immediately hit broken links
**Complexity**: 2/5 - Verify paths and update or create files
**Recommendation**: Audit all documentation links and ensure they resolve

#### 2. Package Not Published
**Location**: Stage 2: Installation
**Issue**: Journey assumes `pip install vibey` works, but package may not be on PyPI
**Impact**: 5/5 - Installation fails completely
**Complexity**: 1/5 - Update to show editable install or publish package
**Recommendation**: Document correct installation method or publish to PyPI

### Medium Impact Issues

#### 3. Missing Error Handling Guidance
**Location**: Stage 2: Potential Blockers
**Issue**: Table is incomplete (line 100 cuts off)
**Impact**: 3/5 - Users stuck when encountering errors
**Complexity**: 2/5 - Complete the troubleshooting section
**Recommendation**: Add comprehensive error handling for common issues

#### 4. Prerequisites Not Fully Specified
**Location**: Stage 1
**Issue**: Python version, OS compatibility, and git requirements not explicitly stated
**Impact**: 3/5 - Users may have wrong environment
**Complexity**: 1/5 - Add explicit prerequisites
**Recommendation**: Add clear prerequisite checklist with versions

---

## Active Developer Journey Friction Points

### High Impact Issues

#### 1. Commands May Not Exist
**Location**: Phase 1: Session Start
**Issue**: Several commands referenced may not be implemented:
- `vibey roadmap status --filter in_progress`
- `vibey context list --type session --limit 3`
- `vibey discover status`
**Impact**: 4/5 - Users encounter "command not found" errors
**Complexity**: 3/5 - Implement commands or update documentation
**Recommendation**: Verify all commands exist and work as documented

#### 2. Context Directory Path Mismatch
**Location**: Phase 3: Work Execution
**Issue**: Shows `.vibey/roadmap/context/sprints/<sprint>/...` but actual structure uses ULID-based flat directories
**Impact**: 3/5 - Users can't find context files
**Complexity**: 1/5 - Update path examples
**Recommendation**: Update all path references to use current structure

### Medium Impact Issues

#### 3. Discovery Integration Unclear
**Location**: Phase 1
**Issue**: Discovery commands (`vibey discover refresh`, `vibey discover diff`) referenced but relationship to daily workflow unclear
**Impact**: 2/5 - Users unsure when to use discovery
**Complexity**: 2/5 - Add clearer guidance
**Recommendation**: Add "When to Use" section for discovery commands

#### 4. Missing MCP Alternative Workflows
**Location**: Entire document
**Issue**: Only shows CLI workflow, no mention of MCP tools for AI assistant integration
**Impact**: 2/5 - Users with AI assistants don't know about MCP
**Complexity**: 2/5 - Add MCP alternatives section
**Recommendation**: Add parallel MCP workflow for AI assistant users

---

## Project Lead Journey Friction Points

### High Impact Issues

#### 1. Commands May Not Exist or Have Different Options
**Location**: Multiple sections
**Issue**: Several command options referenced may not exist:
- `vibey roadmap show track --all`
- `vibey roadmap show sprint <id> --detailed`
- `vibey roadmap list-blockers --all-tracks`
- `vibey roadmap summarize --type sprint --format markdown`
**Impact**: 4/5 - Key project lead commands fail
**Complexity**: 3/5 - Implement or update documentation
**Recommendation**: Verify all commands and options exist

#### 2. Export Command Variations
**Location**: Friday: Reporting
**Issue**: `vibey roadmap export --format json` - export command may not exist or have different syntax
**Impact**: 3/5 - Reporting workflow broken
**Complexity**: 2/5 - Document correct export method
**Recommendation**: Verify export functionality and document

### Medium Impact Issues

#### 3. Checkpoint Command Unclear
**Location**: Friday: Reporting
**Issue**: `vibey roadmap checkpoint` referenced but checkpoint system may not be fully implemented
**Impact**: 2/5 - Users try to use unimplemented feature
**Complexity**: 3/5 - Implement or remove from docs
**Recommendation**: Verify checkpoint functionality or document alternative

---

## Cross-Journey Issues

### 1. Missing Journey: Contributor
**Issue**: No JOURNEY_CONTRIBUTOR.md despite Chris persona being defined
**Impact**: 3/5 - Contributors have no journey map
**Complexity**: 4/5 - Create entire document
**Recommendation**: Create contributor journey document

### 2. Missing Journey: Plugin Developer
**Issue**: No JOURNEY_PLUGIN_DEVELOPER.md for Taylor persona
**Impact**: 2/5 - Niche audience but important for extensibility
**Complexity**: 4/5 - Create entire document
**Recommendation**: Create plugin developer journey document

### 3. Inconsistent Command Syntax
**Issue**: Commands shown with different syntax patterns across journeys
**Example**: Some show `vibey roadmap show <type> <id>`, others show `vibey roadmap show <type> --id <id>`
**Impact**: 3/5 - Confuses users about correct syntax
**Complexity**: 2/5 - Standardize documentation
**Recommendation**: Audit and standardize all command examples

---

## Summary Statistics

| Journey | High | Medium | Low | Total |
|---------|------|--------|-----|-------|
| New User | 2 | 2 | 0 | 4 |
| Active Developer | 2 | 2 | 0 | 4 |
| Project Lead | 2 | 1 | 0 | 3 |
| Cross-Journey | 3 | - | - | 3 |
| **Total** | **9** | **5** | **0** | **14** |

## Priority Actions

### Immediate (Critical for Usability)
1. Verify package installation method and update docs
2. Audit all command references for existence
3. Update path references to use current structure

### Short-term
4. Complete all troubleshooting sections
5. Add MCP workflow alternatives
6. Standardize command syntax across docs

### Medium-term
7. Create missing journey documents (Contributor, Plugin Developer)
8. Add "When to Use" guidance for discovery commands
9. Implement or document checkpoint functionality
