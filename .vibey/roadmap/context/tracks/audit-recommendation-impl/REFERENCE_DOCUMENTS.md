# Reference Documents for Recommendation Implementation

This document lists all artifacts created during the User Journey Audit track, organized in the order they should be read to understand the project state before implementing recommendations.

## Reading Order

### 1. Executive Summaries (Start Here)

- `.vibey/roadmap/context/tracks/user-journey-audit/USER_JOURNEY_AUDIT_SUMMARY.md`
- `.vibey/roadmap/context/tracks/user-journey-audit/COVERAGE_MATRIX.md`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-6-1/FRICTION_ANALYSIS_REPORT.md`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-6-2/AUDIT_SYNTHESIS.md`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-6-2/FRICTION_SYNTHESIS.md`

---

### 2. Architecture & Design Decisions

- `docs/architecture/adr/0001-ulid-identifiers.md`
- `docs/architecture/adr/0002-flat-directory-structure.md`
- `docs/architecture/adr/0003-dual-storage-sqlite-yaml.md`
- `docs/architecture/adr/0004-click-cli-framework.md`
- `docs/architecture/adr/0005-mcp-integration.md`
- `docs/architecture/adr/README.md`
- `docs/architecture/adr/0000-template.md`

---

### 3. User-Facing Documentation

**For New Users**
- `docs/journeys/JOURNEY_NEW_USER.md`
- `docs/walkthroughs/WALKTHROUGH_NEW_USER.md`

**For Active Developers**
- `docs/journeys/JOURNEY_ACTIVE_DEVELOPER.md`
- `docs/walkthroughs/WALKTHROUGH_ACTIVE_DEVELOPER.md`

**For Project Leads**
- `docs/journeys/JOURNEY_PROJECT_LEAD.md`
- `docs/walkthroughs/WALKTHROUGH_PROJECT_LEAD.md`

**For Contributors**
- `docs/journeys/JOURNEY_CONTRIBUTOR.md`
- `docs/walkthroughs/WALKTHROUGH_CONTRIBUTOR.md`
- `docs/development/SETUP.md`
- `docs/development/CODING_STANDARDS.md`
- `docs/development/TEST_MAINTENANCE.md`

**For Platform Integrators**
- `docs/journeys/JOURNEY_PLATFORM_INTEGRATOR.md`
- `docs/walkthroughs/WALKTHROUGH_PLATFORM_INTEGRATOR.md`

**Template**
- `docs/walkthroughs/WALKTHROUGH_TEMPLATE.md`

---

### 4. Reference Guides

- `docs/reference/CLI_REFERENCE.md`
- `docs/reference/MCP_REFERENCE.md`
- `.vibey/roadmap/context/sprints/user-journey-phase-2-1/CLI_INTROSPECTION_DESIGN.md`
- `.vibey/roadmap/context/sprints/user-journey-phase-2-2/MCP_INTROSPECTION_DESIGN.md`

---

### 5. Codebase Structure & Classification

- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-1/CLASSIFICATION_TAXONOMY.md`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-1/FILE_INVENTORY.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-1/FILE_REGISTRY.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-1/FILE_DEPENDENCY_GRAPH.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-1/VIBEY_FILE_CLASSIFICATION.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-1/DOCS_FILE_CLASSIFICATION.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-1/TESTS_FILE_CLASSIFICATION.yaml`

---

### 6. Module-Level Audits

**Core Library**
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-2/CORE_LIB_AUDIT_CRITERIA.md`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-2/CORE_LIBRARY_AUDIT_SUMMARY.md`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-2/AUDIT_ROOT_FILES.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-2/AUDIT_CLI_MODULE.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-2/AUDIT_OPERATIONS_MODULE.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-2/AUDIT_ROADMAP_MODULE.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-2/AUDIT_MCP_ADAPTERS_MODULE.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-2/AUDIT_ADAPTERS_MODULE.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-2/AUDIT_COMMON_MODULE.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-2/AUDIT_CONFIG_MODULE.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-2/AUDIT_CONTENT_MODULE.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-2/AUDIT_PLATFORM_MODULE.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-2/OBSOLETE_CODE_REPORT.yaml`

**Documentation**
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-3/DOCS_AUDIT_CRITERIA.md`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-3/DOCUMENTATION_AUDIT_SUMMARY.md`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-3/AUDIT_DOCS_ROOT.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-3/AUDIT_GETTING_STARTED.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-3/AUDIT_GUIDES.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-3/AUDIT_REFERENCE.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-3/AUDIT_DEVELOPMENT.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-3/AUDIT_EXAMPLES.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-3/AUDIT_OPERATIONS.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-3/AUDIT_ROADMAP_DOCS.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-3/AUDIT_SPRINTS.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-3/AUDIT_TESTING.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-3/AUDIT_VALIDATION.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-3/AUDIT_ROOT_DOCS.yaml`

**Test Suite**
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-4/TEST_AUDIT_CRITERIA.md`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-4/TEST_SUITE_AUDIT_SUMMARY.md`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-4/COVERAGE_ANALYSIS_REPORT.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-4/AUDIT_TESTS_ROOT.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-4/AUDIT_TESTS_SUBDIRS.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-4/COVERAGE_GAP_ANALYSIS.yaml`

**Scripts & Config**
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-5/SCRIPTS_AUDIT_CRITERIA.md`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-5/SCRIPTS_AUDIT_SUMMARY.md`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-5/SCRIPTS_INVENTORY.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-5/AUDIT_PROJECT_CONFIG.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-5/AUDIT_SCRIPTS_CONSOLIDATED.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-5/CLI_MIGRATION_CANDIDATES.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-5/DEPRECATION_CANDIDATES.yaml`

**Database & Artifacts**
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-6/DATABASE_SCHEMA_DOCUMENTATION.md`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-6/DATABASE_ARTIFACT_AUDIT_SUMMARY.md`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-6/ARTIFACT_RELATIONSHIP_MODEL.md`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-6/ARTIFACT_TABLES_INVENTORY.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-6/FILE_TO_ARTIFACT_MAPPING.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-6/MISSING_ARTIFACT_TYPES.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-6/MISSING_RELATIONSHIP_TYPES.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-6/ARTIFACT_METADATA_ASSESSMENT.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-6/ARTIFACT_QUERY_ASSESSMENT.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-6/ARTIFACT_AUDIT_CROSS_REFERENCE.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-1-6/ARTIFACT_TRACKING_IMPROVEMENTS_DESIGN.md`

---

### 7. Context & Discovery System Design

- `.vibey/roadmap/context/sprints/user-journey-phase-3-1/CONTEXT_ENGINEERING_LANDSCAPE.md`
- `.vibey/roadmap/context/sprints/user-journey-phase-3-1/CURRENT_CONTEXT_AUDIT.md`
- `.vibey/roadmap/context/sprints/user-journey-phase-3-1/SESSION_CONTEXT_REQUIREMENTS.md`
- `.vibey/roadmap/context/sprints/user-journey-phase-3-1/CONTEXT_VERSIONING_DESIGN.md`
- `.vibey/roadmap/context/sprints/user-journey-phase-3-1/CONTEXT_RETRIEVAL_DESIGN.md`
- `.vibey/roadmap/context/sprints/user-journey-phase-3-1/PHASE_3_1_SYNTHESIS.md`
- `.vibey/roadmap/context/sprints/user-journey-phase-4-2/DISCOVERY_AUDIT.md`
- `.vibey/roadmap/context/sprints/user-journey-phase-4-2/DISCOVERY_SCHEMA.md`
- `.vibey/roadmap/context/sprints/user-journey-phase-4-2/DISCOVERY_SCHEMA.yaml`
- `.vibey/roadmap/context/sprints/user-journey-phase-4-2/DISCOVERY_CONTEXT_INTEGRATION.md`
- `.vibey/roadmap/context/sprints/user-journey-phase-4-4/CONTEXT_DIRECTORY_DESIGN.md`

---

### 8. Friction & Gap Analysis

- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-6-1/REFERENCE_GUIDE_FRICTION.md`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-6-1/USER_JOURNEY_FRICTION.md`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-6-1/WALKTHROUGH_FRICTION.md`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-6-1/CONTEXT_ENGINEERING_GAPS.md`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-6-1/OBSOLETE_CODE_INVENTORY.md`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-6-1/FRICTION_REMEDIATION_PRIORITY.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-5-1/PRIORITIZED_COVERAGE_GAPS.md`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-5-3/INTEGRATION_TEST_STRATEGY.md`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-5-5/BUGFIX_FILE_CHANGES.md`

---

### 9. Recommendations & Next Steps (End Here)

- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-6-2/QUICK_WINS.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-6-2/STRATEGIC_IMPROVEMENTS.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-6-2/TECHNICAL_DEBT_INVENTORY.yaml`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-6-2/IMPROVEMENT_ROADMAP.md`
- `.vibey/roadmap/context/tracks/user-journey-audit/sprints/phase-6-2/SUCCESS_METRICS.yaml`

---

## Reading Priority Guide

| Group | Docs | Priority |
|-------|------|----------|
| 1. Executive Summaries | 5 | Must read |
| 2. Architecture | 7 | Must read |
| 3. User-Facing | 17 | Skim relevant personas |
| 4. Reference Guides | 4 | Reference as needed |
| 5. Structure | 7 | Skim |
| 6. Module Audits | 42 | Deep dive if needed |
| 7. Context Design | 11 | Read if building on context system |
| 8. Friction Analysis | 9 | Read before fixing issues |
| 9. Recommendations | 5 | Must read |

**Suggested Approach:** Read groups 1, 2, and 9 completely. Skim group 3 for your persona. Reference the rest as needed.

---

## Document Statistics

**Total: 104 documents**

| Category | Count |
|----------|-------|
| Executive Summaries | 5 |
| Architecture ADRs | 7 |
| User Journeys | 5 |
| Walkthroughs | 6 |
| Development Docs | 3 |
| Reference Guides | 4 |
| File Classification | 7 |
| Core Library Audit | 13 |
| Documentation Audit | 14 |
| Test Suite Audit | 6 |
| Scripts Audit | 7 |
| Database Audit | 11 |
| Context Design | 11 |
| Friction Analysis | 9 |
| Recommendations | 5 |
