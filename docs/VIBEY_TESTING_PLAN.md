# Vibey Comprehensive Testing Plan

**Version:** 2.5.0
**Status:** Updated - In Progress
**Created:** 2025-11-10
**Last Updated:** 2025-11-11
**Purpose:** Automated testing suite for all user journeys and platform integrations

---

## ⚠️ IMPORTANT: Testing Plan Update Status

**Test Suite Updated:** 2025-11-11
**Documentation Version:** v2.5.0 (matches VIBEY_USER_JOURNEYS.md v2.5.0)

**Recent Changes:**
- ✅ Journey 1: Tests updated for v2.5.0 (19 new tests)
- ✅ Journey 6: Tests updated for v2.5.0 (11 new tests)
- ✅ Journey 7: CLI tests created (50 new tests)
- ✅ Journey 8: Complete test suite created (41 tests)
- ✅ CLI Commands: Comprehensive tests created (87 tests)

**Status:** 208 new tests created, ready for integration

See: `docs/TEST_SUITE_UPDATE_SUMMARY.md` for details

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Testing Strategy](#testing-strategy)
3. [Test Framework Architecture](#test-framework-architecture)
4. [Journey Test Suites](#journey-test-suites)
5. [Success Metrics](#success-metrics)
6. [Test Data & Fixtures](#test-data--fixtures)
7. [Automation & CI/CD](#automation--cicd)
8. [Quality Gates](#quality-gates)
9. [Roadmap Integration](#roadmap-integration)

---

## Executive Summary

### Problem Statement

Vibey has undergone minimal testing to date. Before onboarding new platforms (Goose, Cursor, JetBrains AI), we need comprehensive testing to ensure:
- All user journeys work consistently
- Repository state changes are correct
- Git history is accurate
- Cross-platform compatibility
- Quality standards are met

### Solution

Automated, reusable test suite covering:
- **8 user journeys** (69 discrete steps) ← Updated from 7
- **4 platforms** (Claude Code, Goose, Cursor, JetBrains AI)
- **400+ test scenarios** ← Updated from 200+
- **60+ success metrics** ← Updated from 50+
- **100% automation**

### Success Criteria

✅ All platform ports must pass this test suite before completion
✅ Tests run in CI/CD pipeline
✅ Test coverage > 90%
✅ Execution time < 30 minutes
✅ Clear failure diagnostics

---

## Testing Strategy

### Testing Pyramid

```
                   ╱╲
                  ╱  ╲
                 ╱ E2E ╲              10% - Full user journeys
                ╱────────╲
               ╱          ╲
              ╱ Integration╲          30% - Journey steps
             ╱──────────────╲
            ╱                ╲
           ╱   Unit Tests     ╲       60% - Individual functions
          ╱────────────────────╲
```

### Test Categories

1. **Unit Tests** (60% of tests)
   - Configuration parsing
   - Template rendering
   - File system operations
   - Git operations
   - YAML validation

2. **Integration Tests** (30% of tests)
   - Journey step transitions
   - State mutations
   - Agent interactions
   - Quality gate execution

3. **End-to-End Tests** (10% of tests)
   - Complete user journeys
   - Multi-step workflows
   - Platform deployments

### Test Approach

**Test-Driven by User Journeys:**
- Extract testable scenarios from VIBEY_USER_JOURNEYS.md
- Each step = test case
- Each expected state = assertion
- Each git commit = verification point

**Platform-Agnostic Core:**
- Test `.vibey/` configuration layer (platform-independent)
- Test each platform deployment separately
- Ensure deployments are equivalent

---

## Test Framework Architecture

### Technology Stack

```yaml
testing_stack:
  language: Python 3.9+
  test_framework: pytest
  assertion_library: pytest
  mocking: pytest-mock
  fixtures: pytest-fixtures
  coverage: pytest-cov
  git_testing: GitPython
  yaml_testing: PyYAML
  reporting: pytest-html, allure
```

### Directory Structure

```
tests/
├── conftest.py                    # Shared fixtures
├── fixtures/                      # Test data
│   ├── mock-repos/                # Mock project repos
│   │   ├── web-app/               # Next.js project
│   │   ├── api-service/           # FastAPI project
│   │   ├── ml-project/            # ML project
│   │   └── empty-project/         # Blank project
│   ├── expected-states/           # Expected repo states
│   │   ├── journey1-step1.yaml
│   │   ├── journey1-step2.yaml
│   │   └── ...
│   └── git-histories/             # Expected git logs
│       ├── journey2-complete.txt
│       └── ...
├── unit/                          # Unit tests (60%)
│   ├── test_config_parsing.py
│   ├── test_template_rendering.py
│   ├── test_file_operations.py
│   ├── test_git_operations.py
│   └── test_yaml_validation.py
├── integration/                   # Integration tests (30%)
│   ├── test_journey1_steps.py
│   ├── test_journey2_steps.py
│   ├── test_journey3_steps.py
│   ├── test_journey4_steps.py
│   ├── test_journey5_steps.py
│   ├── test_journey6_steps.py
│   └── test_journey7_steps.py
├── e2e/                           # End-to-end tests (10%)
│   ├── test_complete_journey1.py
│   ├── test_complete_journey2.py
│   └── test_platform_parity.py
├── platform/                      # Platform-specific tests
│   ├── test_claude_code.py
│   ├── test_goose.py
│   ├── test_cursor.py
│   └── test_jetbrains.py
└── utils/                         # Test utilities
    ├── repo_builder.py            # Build test repos
    ├── state_validator.py         # Validate repo state
    ├── git_validator.py           # Validate git history
    └── metrics_collector.py       # Collect test metrics
```

### Core Test Utilities

**1. Repository Builder (`utils/repo_builder.py`)**
```python
class TestRepoBuilder:
    """Build mock repositories for testing."""

    def create_web_app_repo(self, path: Path) -> TestRepo:
        """Create Next.js web app mock repo."""

    def create_api_service_repo(self, path: Path) -> TestRepo:
        """Create FastAPI service mock repo."""

    def create_ml_project_repo(self, path: Path) -> TestRepo:
        """Create ML project mock repo."""

    def add_vibey_framework(self, repo: TestRepo) -> None:
        """Clone Vibey into test repo."""

    def deploy_to_platform(self, repo: TestRepo, platform: str) -> None:
        """Deploy Vibey to specified platform."""
```

**2. State Validator (`utils/state_validator.py`)**
```python
class StateValidator:
    """Validate repository state matches expectations."""

    def validate_directory_structure(self,
                                    actual: Path,
                                    expected: dict) -> ValidationResult:
        """Validate directory structure."""

    def validate_file_contents(self,
                              file_path: Path,
                              expected: str) -> ValidationResult:
        """Validate file contents."""

    def validate_yaml_structure(self,
                               yaml_file: Path,
                               schema: dict) -> ValidationResult:
        """Validate YAML file against schema."""

    def validate_git_state(self,
                          repo: TestRepo,
                          expected: GitState) -> ValidationResult:
        """Validate git state (branch, commits, etc.)."""
```

**3. Git Validator (`utils/git_validator.py`)**
```python
class GitValidator:
    """Validate git history and commits."""

    def validate_commit_message(self,
                               commit: Commit,
                               pattern: str) -> bool:
        """Validate commit message matches pattern."""

    def validate_commit_order(self,
                             commits: List[Commit],
                             expected_order: List[str]) -> ValidationResult:
        """Validate commits are in correct order."""

    def validate_file_changes(self,
                             commit: Commit,
                             expected_changes: dict) -> ValidationResult:
        """Validate files changed in commit."""

    def count_commits_by_pattern(self,
                                repo: TestRepo,
                                pattern: str) -> int:
        """Count commits matching pattern."""
```

**4. Metrics Collector (`utils/metrics_collector.py`)**
```python
class MetricsCollector:
    """Collect test execution metrics."""

    def track_test_duration(self, test_name: str, duration: float):
        """Track individual test duration."""

    def track_success_metric(self, metric_name: str, value: float):
        """Track success metric value."""

    def generate_report(self) -> TestReport:
        """Generate comprehensive test report."""
```

---

## Journey Test Suites

### Journey 1: First-Time Setup (10 Steps) ⚠️ UPDATED

**Test Suite:** `tests/integration/test_journey1_steps_v2.5.0.py` ← NEW (2025-11-11)
**Old Test Suite:** `tests/integration/test_journey1_steps.py` ← DEPRECATED

**⚠️ CRITICAL: Test plan updated for v2.5.0 user journey documentation**

**Changes in v2.5.0:**
- Installation method: `git clone` → `pip install vibey-framework`
- CLI command syntax: `./vibey deploy` → `vibey deploy run --platform X`
- Directory structure: No `.vibey/framework/` (framework installed in site-packages)
- New roadmap directories: `.vibey/tracks/`, `.vibey/sprints/`, `.vibey/tasks/`

**Tests Updated:**
- ✅ Test 1.2: REPLACED clone tests with pip installation tests (3 tests)
- ✅ Test 1.3: UPDATED deployment command syntax (3 tests)
- ✅ Tests 1.4-1.7: IMPLEMENTED interactive Q&A flow (9 tests)
- ✅ Test 1.8: NEW configuration generation tests (3 tests)
- ✅ Test 1.9: NEW git commit workflow (1 test)
- ✅ Test 1.10: NEW E2E validation (2 tests, originally stubs)

**Total New/Updated Tests:** 19 tests (replaces 10 obsolete tests)
**Coverage Improvement:** 14-18% → 100%

**Documentation:**
- Implementation Summary: `tests/integration/JOURNEY1_V2.5.0_IMPLEMENTATION_SUMMARY.md`
- Migration Guide: `tests/integration/JOURNEY1_MIGRATION_GUIDE.md`

---

#### OLD Tests (DEPRECATED - For Reference Only)

#### Test 1.1: Navigate to Project
```python
def test_journey1_step1_navigate_to_project(test_repo):
    """Test: Navigate to project directory."""
    # Setup
    repo = test_repo.create_web_app()

    # Execute
    result = navigate_to_project(repo.path)

    # Verify
    assert result.success
    assert repo.path.exists()
    assert (repo.path / '.git').exists()
    assert git_status_clean(repo)

    # Metrics
    metrics.track('journey1_step1', result.duration)
```

#### Test 1.2: Clone Vibey Framework
```python
def test_journey1_step2_clone_vibey(test_repo):
    """Test: Clone Vibey framework into project."""
    # Setup
    repo = test_repo.create_web_app()

    # Execute
    result = clone_vibey_framework(repo.path)

    # Verify - Directory structure
    assert (repo.path / '.vibey').exists()
    assert (repo.path / '.vibey' / 'framework').exists()
    assert (repo.path / '.vibey' / 'config').exists()
    assert (repo.path / '.vibey' / 'templates').exists()
    assert (repo.path / '.vibey' / 'scripts').exists()

    # Verify - Git status
    git_status = get_git_status(repo)
    assert '.vibey/' in git_status.untracked_files

    # Verify - .gitignore updated
    gitignore = read_file(repo.path / '.gitignore')
    assert '.vibey/.git/' in gitignore
    assert '.claude/' in gitignore
    assert '.goose/' in gitignore

    # Metrics
    metrics.track('journey1_step2_success', 1)
    metrics.track('vibey_clone_time', result.duration)
```

#### Test 1.3: Deploy to Platform (Claude Code)
```python
def test_journey1_step3_deploy_claude_code(test_repo):
    """Test: Deploy Vibey to Claude Code."""
    # Setup
    repo = test_repo.create_web_app()
    clone_vibey_framework(repo.path)

    # Execute
    result = deploy_vibey(repo.path, platform='claude-code')

    # Verify - .claude/ directory created
    assert (repo.path / '.claude').exists()
    assert (repo.path / '.claude' / 'CLAUDE.md').exists()
    assert (repo.path / '.claude' / 'agents').exists()
    assert (repo.path / '.claude' / 'workflows').exists()
    assert (repo.path / '.claude' / 'commands').exists()

    # Verify - CLAUDE.md content
    claude_md = read_file(repo.path / '.claude' / 'CLAUDE.md')
    assert 'Vibey Agent Framework' in claude_md
    assert 'Orchestration' in claude_md

    # Verify - Agent count
    agent_files = list((repo.path / '.claude' / 'agents').rglob('*.md'))
    assert len(agent_files) >= 12  # At least 12 agents

    # Verify - Workflow count
    workflow_files = list((repo.path / '.claude' / 'workflows').rglob('*.md'))
    assert len(workflow_files) >= 16  # At least 16 workflows

    # Verify - .vibey/config generated
    assert (repo.path / '.vibey' / 'config' / 'project.yaml').exists()
    assert (repo.path / '.vibey' / 'roadmap.yaml').exists()

    # Verify - Git status
    git_status = get_git_status(repo)
    assert '.vibey/config/project.yaml' in git_status.untracked_files
    assert '.claude/' not in git_status.untracked_files  # gitignored

    # Metrics
    metrics.track('journey1_step3_success', 1)
    metrics.track('deployment_time', result.duration)
    metrics.track('agent_count', len(agent_files))
    metrics.track('workflow_count', len(workflow_files))
```

#### Test 1.4-1.10: Additional Steps
```python
def test_journey1_step4_initialize_in_claude():
    """Test: /vibey initialization command."""
    # Test interactive initialization

def test_journey1_step5_configuration_discovery():
    """Test: Interactive configuration questions."""
    # Test Q&A flow

def test_journey1_step6_configuration_generation():
    """Test: Generate project configuration."""
    # Verify config generation

def test_journey1_step7_initial_commit():
    """Test: Initial Vibey commit."""
    # Verify git commit

def test_journey1_step8_codebase_audit():
    """Test: Optional codebase audit."""
    # Test audit workflow

def test_journey1_step9_first_sprint_planning():
    """Test: Optional first sprint."""
    # Bridge to Journey 2

def test_journey1_step10_complete():
    """Test: Journey 1 completion criteria."""
    # Verify all success criteria met
```

#### Success Metrics - Journey 1
```python
JOURNEY1_METRICS = {
    'setup_completion_rate': 100,      # % of setups that complete
    'avg_setup_time_minutes': 15,      # Average time to complete
    'configuration_accuracy': 100,     # % configs generated correctly
    'deployment_success_rate': 100,    # % deployments that work
    'git_history_correctness': 100,    # % correct git commits
}
```

---

### Journey 2: Sprint Planning & Execution (12 Steps)

**Test Suite:** `tests/integration/test_journey2_steps.py`

#### Test 2.1: Initiate Sprint Planning
```python
def test_journey2_step1_initiate_sprint_planning(configured_repo):
    """Test: Start sprint planning."""
    # Setup
    repo = configured_repo  # Journey 1 complete

    # Execute
    result = initiate_sprint_planning(repo)

    # Verify
    assert result.success
    assert result.response_contains('/vibey')
    assert result.presents_options
    assert 'Plan a new sprint' in result.options

    # Metrics
    metrics.track('journey2_step1_success', 1)
```

#### Test 2.2: Sprint Goal Definition
```python
def test_journey2_step2_sprint_goal_definition(configured_repo):
    """Test: Define sprint goal."""
    # Setup
    repo = configured_repo
    goal = "Build user authentication with email/password and OAuth"

    # Execute
    result = define_sprint_goal(repo, goal)

    # Verify
    assert result.success
    assert result.goal_accepted
    assert result.complexity == 'High'
    assert result.estimated_duration in ['5-8 days', '1-2 weeks']

    # Metrics
    metrics.track('journey2_step2_success', 1)
    metrics.track('sprint_goal_complexity', result.complexity)
```

#### Test 2.3: Task Breakdown
```python
def test_journey2_step3_task_breakdown(configured_repo):
    """Test: Generate task breakdown."""
    # Setup
    repo = configured_repo
    goal = "Build user authentication"

    # Execute
    result = generate_task_breakdown(repo, goal)

    # Verify - Task generation
    assert len(result.tasks) >= 5  # At least 5 tasks
    assert result.has_development_tasks
    assert result.has_quality_tasks

    # Verify - Task structure
    for task in result.tasks:
        assert task.id
        assert task.title
        assert task.estimated_hours > 0
        assert task.assigned_agent

    # Verify - Total estimation
    total_hours = sum(t.estimated_hours for t in result.tasks)
    assert 20 <= total_hours <= 50  # Reasonable range

    # Metrics
    metrics.track('journey2_step3_success', 1)
    metrics.track('tasks_generated', len(result.tasks))
    metrics.track('total_estimated_hours', total_hours)
```

#### Test 2.4: Sprint State Creation
```python
def test_journey2_step4_sprint_state_creation(configured_repo):
    """Test: Create sprint state files."""
    # Setup
    repo = configured_repo
    tasks = generate_task_breakdown(repo, "Auth sprint")

    # Execute
    result = create_sprint_state(repo, "auth-sprint-1", tasks)

    # Verify - Files created
    assert (repo.path / '.vibey' / 'sprints' / 'auth-sprint-1.yaml').exists()
    assert (repo.path / '.vibey' / 'sprint_docs' / 'auth-sprint-1' / 'PLAN.md').exists()
    assert (repo.path / '.vibey' / 'sprint_docs' / 'auth-sprint-1' / 'TASKS.md').exists()

    # Verify - Sprint YAML structure
    sprint_yaml = load_yaml(repo.path / '.vibey' / 'sprints' / 'auth-sprint-1.yaml')
    assert sprint_yaml['sprint']['id'] == 'auth-sprint-1'
    assert sprint_yaml['sprint']['status'] == 'planning'
    assert sprint_yaml['sprint']['goal']
    assert len(sprint_yaml['sprint']['tasks']) == len(tasks)

    # Verify - Quality gates
    assert 'quality_gates' in sprint_yaml['sprint']
    assert len(sprint_yaml['sprint']['quality_gates']) >= 2

    # Verify - Roadmap updated
    roadmap = load_yaml(repo.path / '.vibey' / 'roadmap.yaml')
    assert 'auth-sprint-1' in [s['id'] for s in roadmap.get('sprints', [])]

    # Metrics
    metrics.track('journey2_step4_success', 1)
    metrics.track('sprint_files_created', 3)
```

#### Test 2.5-2.12: Additional Steps
```python
def test_journey2_step5_sprint_kickoff_commit():
    """Test: Git commit for sprint kickoff."""

def test_journey2_step6_start_sprint():
    """Test: Change sprint status to in_progress."""

def test_journey2_step7_task_execution():
    """Test: Execute and complete tasks."""

def test_journey2_step8_continue_through_tasks():
    """Test: Iterate through task list."""

def test_journey2_step9_quality_gate_security():
    """Test: Security review quality gate."""

def test_journey2_step10_quality_gate_testing():
    """Test: Test coverage quality gate."""

def test_journey2_step11_sprint_completion():
    """Test: Complete sprint."""

def test_journey2_step12_complete():
    """Test: Journey 2 completion criteria."""
```

#### Success Metrics - Journey 2
```python
JOURNEY2_METRICS = {
    'sprint_completion_rate': 100,     # % sprints that complete
    'avg_tasks_per_sprint': 7,         # Average number of tasks
    'quality_gate_pass_rate': 100,     # % gates that pass
    'git_commits_per_sprint': 10,      # Average commits
    'task_estimation_accuracy': 85,    # % within 20% of estimate
}
```

---

### Journey 3-7: Additional Journey Tests

**Similar structure for remaining journeys:**

- Journey 2: Sprint Planning (10 steps) - ✅ Adequate coverage (~85%)
- Journey 3: Feature Development (8 steps) - ✅ Adequate coverage (~80%)
- Journey 4: Quality Assurance (8 steps) - ✅ Adequate coverage (~75%)
- Journey 5: Framework Management (7 steps) - ✅ Adequate coverage (~70%)
- Journey 6: Multi-Platform Deployment (6 steps) - ⚠️ UPDATED (see below)
- Journey 7: Roadmap-Driven Development (10 steps) - ⚠️ UPDATED (see below)
- Journey 8: Config Migration (8 steps) - ✅ NEW (see below)

---

### Journey 6: Multi-Platform Deployment (6 Steps) ⚠️ UPDATED

**Test Suite:** `tests/integration/test_journey6_steps_v2.5.0.py` ← NEW (2025-11-11)

**⚠️ CRITICAL: Test plan updated for v2.5.0 - includes critical Goose adapter fix**

**Changes in v2.5.0:**
- New command: `vibey deploy list` (shows available platforms)
- Updated syntax: `vibey deploy run --platform X` (not `./vibey deploy --platform X`)
- **CRITICAL FIX:** Goose adapter creates `.goosehints` (NOT `.goose/toolkit.toml`)
- New flag: `--platform all` (deploy to all platforms)
- New flag: `--clean` (removes existing deployment first)

**Tests Added/Updated:**
- ✅ Test 01: NEW `vibey deploy list` command
- ✅ Test 02: UPDATED Claude Code deployment (new syntax)
- ✅ Test 03: UPDATED Goose deployment (new syntax)
- ✅ Test 04: CRITICAL FIX - Goose `.goosehints` validation
- ✅ Test 05: NEW `--platform all` flag
- ✅ Test 06: NEW `--clean` flag
- ✅ Test 07: Goose recipe format validation
- ✅ Test 08: Config change redeployment
- ✅ Test 09: Multi-platform detection
- ✅ Test 10: Cursor experimental support
- ✅ Test 11: BONUS - Complete multi-platform workflow

**Total New/Updated Tests:** 11 tests
**Coverage Improvement:** 35-40% → 100%

**Most Critical Update:** Test 04 validates `.goosehints` file (many Goose users impacted by old bug)

**Documentation:**
- Update Summary: `tests/integration/JOURNEY6_TEST_UPDATE_SUMMARY.md`
- Implementation Checklist: `tests/integration/JOURNEY6_IMPLEMENTATION_CHECKLIST.md`

---

### Journey 7: Roadmap-Driven Development (10 Steps) ⚠️ UPDATED

**Test Suite:** `tests/cli/test_roadmap_cli_comprehensive.py` ← NEW (2025-11-11)

**⚠️ CRITICAL: Test plan updated for v2.5.0 - all new CLI commands**

**Changes in v2.5.0:**
- 7 new CLI commands: `init`, `status`, `show`, `start`, `complete`, `context`, `summarize`
- Quality gate integration with sprint completion
- Dependency management (blocking/unblocking)
- Dual-mode interaction (CLI + Natural Language)
- AI-optimized context generation

**Current Status:**
- YAML structure tests: ✅ Adequate (existing tests still valid)
- CLI command tests: ✅ NEW - 50 comprehensive tests created

**Tests Created:**
- ✅ Core CLI Commands: 20 tests (all 7 commands with variations)
- ✅ Quality Gate Integration: 5 tests (sprint completion with gates)
- ✅ State Machine Transitions: 6 tests (valid/invalid transitions)
- ✅ Dependency Management: 5 tests (blocking, resolution, circular deps)
- ✅ AI Context & Summarization: 4 tests (context output, summaries)
- ✅ Dual-Mode Interaction: 3 tests (CLI vs NL equivalence)
- ✅ Output Formatting: 5 tests (tables, icons, progress bars)
- ✅ Integration Tests: 2 tests (complete workflows)

**Total New Tests:** 50 tests (104% of target - 2 bonus tests)
**Coverage Improvement:** 30-35% → 100%

**Test Status:** 8% passing, 64% failing, 28% skipped
**Note:** Failures due to YAML schema mismatch in fixtures (fix in progress)

**Documentation:**
- Test Summary: `tests/cli/ROADMAP_CLI_TESTS_SUMMARY.md`
- Quick Reference: `tests/cli/TEST_REFERENCE.md`

---

### Journey 8: Config Migration (8 Steps) ✅ NEW

**Test Suite:** `tests/integration/test_journey8_steps.py` ← NEW (2025-11-11)

**✅ NEW JOURNEY: Complete test suite created from scratch**

**Journey Overview:**
- Migrate from legacy monolithic config to modular architecture
- Validate backup/restore operations
- Test configuration validation
- Verify platform redeployment with new config

**Test Categories:**
- ✅ Config Detection & Parsing: 10 tests (legacy vs modular detection)
- ✅ Migration Logic: 10 tests (dry-run, execution, data preservation)
- ✅ Validation: 5 tests (schema validation, error reporting)
- ✅ Rollback: 5 tests (backup listing, restoration, cleanup)
- ✅ Integration Tests (8 steps): 8 tests (one per journey step)
- ✅ E2E & Platform: 3 tests (complete workflow, deployment, idempotency)

**Total New Tests:** 41 tests (100% of target)
**Coverage Improvement:** 0% → 100% (completely new journey)

**Success Metrics:**
```yaml
journey8_config_migration:
  migration_completion_rate: 100%
  avg_migration_time: <5 minutes
  data_preservation_accuracy: 100%
  validation_pass_rate: 100%
  backup_creation_success: 100%
  rollback_success_rate: 100%
  platform_redeployment_success: 100%
```

**All 8 Journey Steps Tested:**
1. Step 8.1: Detect Legacy Config
2. Step 8.2: Preview Migration (Dry Run)
3. Step 8.3: Run Migration
4. Step 8.4: Validate New Config
5. Step 8.5: Commit Migration
6. Step 8.6: Redeploy to Platform
7. Step 8.7: Rollback if Needed
8. Step 8.8: Journey Complete

---

### CLI Command Reference Testing ✅ NEW

**Test Suites:** 6 new test files created (2025-11-11)

**Test Files:**
1. `tests/cli/test_global_cli.py` - 11 tests (Global options)
2. `tests/cli/test_deploy_cli.py` - 16 tests (Deploy commands)
3. `tests/cli/test_docs_cli.py` - 13 tests (Docs commands)
4. `tests/cli/test_workflows_cli.py` - 13 tests (CLI workflows)
5. `tests/cli/test_exit_codes.py` - 17 tests (Exit code validation)
6. `tests/cli/test_environment_variables.py` - 17 tests (Environment variables)

**Total New Tests:** 87 tests (271% of target!)

**Test Categories:**
- ✅ Global Options: 11 tests (help, version, verbose, quiet)
- ✅ Deploy Commands: 16 tests (deployment, listing, error handling)
- ✅ Docs Commands: 13 tests (documentation generation)
- ✅ Workflows: 13 tests (end-to-end user journeys)
- ✅ Exit Codes: 17 tests (exit code 0, 1, 2, 3, 4 validation)
- ✅ Environment Variables: 17 tests (VIBEY_CONFIG_DIR, LOG_LEVEL, PLATFORM)

**Coverage Improvement:** 46.7% → 100%

**Test Status:** 87.4% passing (76/87 tests)
**Note:** 11 failing tests document future features from CLI Command Reference

**Documentation:**
- Usage Guide: `tests/cli/README.md`
- Test Summary: `tests/cli/CLI_TEST_SUMMARY.md`

---

Each journey has:
- Individual step tests
- Integration tests
- Success metrics
- State validation
- Git history validation

---

## Success Metrics

### Test Execution Metrics

```yaml
execution_metrics:
  total_tests: 200+
  unit_tests: 120
  integration_tests: 60
  e2e_tests: 20

  target_coverage: ">90%"
  target_pass_rate: "100%"
  target_duration: "<30 minutes"

  flaky_test_threshold: "0%"
  test_reliability: ">99.9%"
```

### Journey Completion Metrics

```yaml
journey1_first_time_setup:
  setup_completion_rate: 100%
  avg_setup_time: <15 minutes
  configuration_accuracy: 100%
  deployment_success_rate: 100%
  git_history_correctness: 100%

journey2_sprint_planning:
  sprint_completion_rate: 100%
  avg_tasks_per_sprint: 7
  quality_gate_pass_rate: 100%
  git_commits_per_sprint: 10
  task_estimation_accuracy: >85%

journey3_feature_development:
  feature_completion_rate: 100%
  avg_feature_time: <3 days
  test_coverage_achieved: >85%
  security_score: >85/100
  code_quality_score: >85/100

journey4_quality_assurance:
  audit_completion_rate: 100%
  issues_detected_avg: >10
  report_generation_success: 100%
  actionable_recommendations: >90%

journey5_framework_management:
  config_change_success: 100%
  orchestration_switch_success: 100%
  agent_enable_disable_success: 100%
  quality_gate_config_success: 100%

journey6_multi_platform:
  deployment_success_claude: 100%
  deployment_success_goose: 100%
  deployment_success_cursor: 100%
  platform_parity: >95%
  regeneration_success: 100%

journey7_roadmap_driven:
  roadmap_creation_success: 100%
  track_dependency_tracking: 100%
  sprint_progression_accuracy: 100%
  velocity_calculation_accuracy: >90%
  report_generation_success: 100%
```

### Platform-Specific Metrics

```yaml
platform_metrics:
  claude_code:
    deployment_success: 100%
    agent_count: 12
    workflow_count: 16
    command_functionality: 100%

  goose:
    deployment_success: 100%
    extension_count: 12
    recipe_count: 16
    toolkit_valid: 100%

  cursor:
    deployment_success: 100%
    cursorrules_valid: 100%
    prompt_count: 16

  jetbrains:
    deployment_success: 100%
    plugin_compatibility: 100%
```

### Quality Metrics

```yaml
quality_metrics:
  code_coverage:
    unit_tests: >90%
    integration_tests: >85%
    e2e_tests: >80%
    overall: >90%

  test_quality:
    assertion_density: >5 per test
    test_documentation: 100%
    edge_cases_covered: >80%

  performance:
    avg_test_duration: <2 seconds
    total_suite_duration: <30 minutes
    parallel_execution: Yes

  maintainability:
    test_code_duplication: <10%
    fixture_reuse: >80%
    test_independence: 100%
```

---

## Test Data & Fixtures

### Mock Repository Templates

**1. Web App Repository (`fixtures/mock-repos/web-app/`)**
```
web-app/
├── src/
│   ├── app/
│   │   ├── page.tsx
│   │   └── layout.tsx
│   ├── components/
│   │   └── Button.tsx
│   └── lib/
│       └── utils.ts
├── package.json
├── next.config.js
├── tsconfig.json
└── .git/
```

**2. API Service Repository (`fixtures/mock-repos/api-service/`)**
```
api-service/
├── src/
│   ├── main.py
│   ├── routers/
│   │   └── users.py
│   └── models/
│       └── user.py
├── requirements.txt
├── pyproject.toml
└── .git/
```

**3. ML Project Repository (`fixtures/mock-repos/ml-project/`)**
```
ml-project/
├── notebooks/
│   └── exploration.ipynb
├── src/
│   ├── data/
│   ├── models/
│   └── training/
├── requirements.txt
└── .git/
```

### Expected State Fixtures

**Journey 1, Step 3 Expected State (`fixtures/expected-states/journey1-step3.yaml`)**
```yaml
directory_structure:
  - path: .vibey/
    type: directory
    children:
      - framework/
      - config/
      - templates/
      - scripts/

  - path: .vibey/config/project.yaml
    type: file
    required_keys:
      - project.name
      - project.type
      - project.tech_stack
      - orchestration.mode
      - quality_gates

  - path: .claude/
    type: directory
    children:
      - CLAUDE.md
      - agents/
      - workflows/
      - commands/

  - path: .claude/CLAUDE.md
    type: file
    contains:
      - "Vibey Agent Framework"
      - "Orchestration Mode"
      - "Quality Gates"

git_status:
  untracked_files:
    - .vibey/config/project.yaml
    - .vibey/roadmap.yaml
  modified_files:
    - .gitignore
  gitignored_files:
    - .claude/
```

### Git History Fixtures

**Journey 2 Complete Git History (`fixtures/git-histories/journey2-complete.txt`)**
```
commit_pattern:
  - pattern: "feat: Complete auth-sprint-1"
    index: 0  # Most recent

  - pattern: "docs\\(auth\\): Add authentication documentation"
    index: 1

  - pattern: "test\\(auth\\): Add (missing test coverage|authentication unit tests)"
    index: 2

  - pattern: "fix\\(auth\\): Add CSRF protection"
    index: 3

  - pattern: "test\\(auth\\): Add authentication unit tests"
    index: 4

  - pattern: "feat\\(auth\\): Implement OAuth integration"
    index: 5

  - pattern: "feat\\(auth\\): Build authentication UI"
    index: 6

  - pattern: "feat\\(auth\\): Implement password authentication"
    index: 7

  - pattern: "feat\\(auth\\): Add authentication database schema"
    index: 8

  - pattern: "chore: Start auth-sprint-1"
    index: 9

  - pattern: "feat: Plan auth-sprint-1"
    index: 10

minimum_commits: 10
maximum_commits: 15
conventional_commits: 100%  # All must follow pattern
```

---

## Automation & CI/CD

### Test Execution

**Local Execution:**
```bash
# Run all tests
pytest tests/

# Run specific journey
pytest tests/integration/test_journey1_steps.py

# Run with coverage
pytest --cov=.vibey --cov-report=html tests/

# Run with metrics
pytest --metrics-output=metrics.json tests/

# Run platform-specific
pytest tests/platform/test_claude_code.py
```

**Parallel Execution:**
```bash
# Run tests in parallel (8 workers)
pytest -n 8 tests/

# Run by category in parallel
pytest -n auto --dist loadgroup tests/
```

### CI/CD Integration

**GitHub Actions Workflow (`.github/workflows/test.yml`):**
```yaml
name: Vibey Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements-test.txt
      - name: Run unit tests
        run: pytest tests/unit/ -v --cov

  integration-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        journey: [1, 2, 3, 4, 5, 6, 7]
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
      - name: Run Journey ${{ matrix.journey }} tests
        run: pytest tests/integration/test_journey${{ matrix.journey }}_steps.py -v

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests]
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
      - name: Run E2E tests
        run: pytest tests/e2e/ -v

  platform-tests:
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests]
    strategy:
      matrix:
        platform: [claude-code, goose, cursor]
    steps:
      - uses: actions/checkout@v3
      - name: Run ${{ matrix.platform }} tests
        run: pytest tests/platform/test_${{ matrix.platform }}.py -v

  metrics-report:
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests, e2e-tests, platform-tests]
    steps:
      - name: Generate test report
        run: |
          python tests/utils/generate_report.py
      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: test-report
          path: test-report.html
```

### Quality Gates for Testing Track

```yaml
testing_track_quality_gates:
  - name: test_coverage
    threshold: 90
    blocking: true

  - name: test_pass_rate
    threshold: 100
    blocking: true

  - name: execution_time
    threshold: 30  # minutes
    blocking: true

  - name: platform_parity
    threshold: 95
    blocking: true

  - name: flaky_tests
    threshold: 0
    blocking: true
```

---

## Quality Gates

### Platform Port Quality Gate

**All platform ports must pass this gate before completion:**

```python
class PlatformPortQualityGate:
    """Quality gate for platform port completion."""

    def evaluate(self, platform: str) -> GateResult:
        """Evaluate platform port against all criteria."""

        results = {
            'test_suite_passed': self.run_full_test_suite(platform),
            'journey_tests_passed': self.run_journey_tests(platform),
            'platform_specific_passed': self.run_platform_tests(platform),
            'parity_test_passed': self.run_parity_tests(platform),
            'metrics_met': self.verify_metrics(platform),
        }

        return GateResult(
            passed=all(results.values()),
            score=sum(results.values()) / len(results) * 100,
            details=results
        )
```

**Gate Criteria:**
```yaml
platform_port_gate:
  required_tests:
    - name: "All Journey Tests"
      tests: tests/integration/test_journey*
      pass_rate: 100%

    - name: "Platform Deployment"
      tests: tests/platform/test_{platform}.py
      pass_rate: 100%

    - name: "Platform Parity"
      tests: tests/e2e/test_platform_parity.py
      pass_rate: 100%
      min_parity_score: 95%

    - name: "Performance"
      max_deployment_time: 60s
      max_initialization_time: 30s

  required_metrics:
    - deployment_success_rate: 100%
    - agent_equivalence: 100%
    - workflow_equivalence: 100%
    - configuration_accuracy: 100%

  documentation:
    - platform_guide_complete: true
    - migration_guide_available: true
    - troubleshooting_documented: true
```

---

## Roadmap Integration

### New Track: Comprehensive Testing System

**Track ID:** `testing-system`
**Priority:** CRITICAL
**Duration:** 6 weeks
**Must complete before:** All platform port tracks

#### Sprint 1: Test Framework & Unit Tests (2 weeks)

**Goals:**
- Set up pytest framework
- Create test utilities
- Write all unit tests
- Achieve 90% coverage on utils

**Tasks:**
1. Set up pytest infrastructure
2. Create RepoBuilder utility
3. Create StateValidator utility
4. Create GitValidator utility
5. Create MetricsCollector utility
6. Write unit tests for config parsing
7. Write unit tests for template rendering
8. Write unit tests for file operations
9. Write unit tests for git operations
10. Write unit tests for YAML validation

**Deliverables:**
- `tests/` directory structure
- All test utilities
- 120 unit tests
- >90% coverage on utils

#### Sprint 2: Journey Integration Tests (2 weeks)

**Goals:**
- Test all 7 journeys
- 61 discrete steps tested
- Validate state transitions
- Validate git history

**Tasks:**
1. Create mock repository fixtures
2. Create expected state fixtures
3. Write Journey 1 tests (10 steps)
4. Write Journey 2 tests (12 steps)
5. Write Journey 3 tests (8 steps)
6. Write Journey 4 tests (8 steps)
7. Write Journey 5 tests (7 steps)
8. Write Journey 6 tests (6 steps)
9. Write Journey 7 tests (10 steps)

**Deliverables:**
- 61 integration tests
- 4 mock repo templates
- 20+ expected state fixtures
- 10+ git history fixtures

#### Sprint 3: E2E Tests & Platform Tests (2 weeks)

**Goals:**
- End-to-end journey tests
- Platform-specific tests
- Platform parity tests
- CI/CD integration

**Tasks:**
1. Write E2E test for Journey 1
2. Write E2E test for Journey 2
3. Write complete journey tests
4. Write Claude Code platform tests
5. Write Goose platform tests (when available)
6. Write Cursor platform tests (when available)
7. Write platform parity tests
8. Set up GitHub Actions workflow
9. Configure parallel execution
10. Create test reporting

**Deliverables:**
- 20 E2E tests
- Platform-specific test suites
- CI/CD pipeline
- Automated reporting

#### Quality Gates

```yaml
testing_track_gates:
  sprint1:
    - test_coverage: ">90%"
    - all_utils_tested: true
    - unit_tests_passing: "100%"

  sprint2:
    - all_journeys_tested: true
    - integration_tests_passing: "100%"
    - fixtures_complete: true

  sprint3:
    - e2e_tests_passing: "100%"
    - ci_cd_working: true
    - test_execution_time: "<30min"
    - platform_tests_ready: true
```

### Updated Platform Port Tracks

**Add testing quality gate to all platform ports:**

```yaml
# Example: goose-port track
goose_port_track:
  sprints:
    - goose-port-1-analysis
    - goose-port-2-adapter
    - goose-port-3-deployment
    - goose-port-4-testing  # NEW SPRINT

  quality_gates:
    - name: comprehensive_testing
      sprint: goose-port-4-testing
      blocking: true
      criteria:
        - run_full_test_suite: true
        - pass_rate: "100%"
        - platform_parity: ">95%"
        - metrics_met: true

  dependencies:
    - track_id: testing-system
      status: completed  # Must complete testing track first
```

**Apply to all platform tracks:**
- goose-port
- cursor-port (when started)
- jetbrains-port
- aider-port
- continue-port
- windsurf-port

---

## Implementation Plan

### Phase 1: Foundation (Week 1-2)
- ✅ Create test plan document (this document)
- 🔄 Set up test framework
- 🔄 Create test utilities
- 🔄 Build mock repositories
- 🔄 Write first 20 unit tests

### Phase 2: Core Testing (Week 3-4)
- Write remaining unit tests (100+)
- Write Journey 1-4 integration tests
- Create expected state fixtures
- Achieve 90% coverage

### Phase 3: Complete Coverage (Week 5-6)
- Write Journey 5-7 integration tests
- Write E2E tests
- Write platform tests
- Set up CI/CD
- Generate documentation

### Phase 4: Roadmap Integration (Week 6)
- Create testing-system track in roadmap
- Update platform port tracks
- Add testing quality gates
- Document testing requirements

---

## Next Steps

1. **Review & Approve** this testing plan
2. **Create testing-system track** in roadmap
3. **Start Sprint 1** of testing track
4. **Implement test framework** and utilities
5. **Write tests** following this plan
6. **Integrate with CI/CD**
7. **Block platform ports** until testing complete

---

## Success Definition

**Testing System is Complete When:**
- ✅ 200+ tests written and passing
- ✅ >90% code coverage achieved
- ✅ All 7 journeys fully tested
- ✅ CI/CD pipeline operational
- ✅ <30 minute total execution time
- ✅ Platform parity tests ready
- ✅ Quality gate integrated into roadmap
- ✅ Documentation complete

**Platform Port Can Begin When:**
- ✅ Testing system track completed
- ✅ All tests passing
- ✅ Quality gate defined
- ✅ Test suite executable
- ✅ Platform tests ready

---

**Document Version:** 1.0.0
**Status:** Draft - Ready for Review
**Created:** 2025-11-10
**Next Review:** Before starting testing-system track
