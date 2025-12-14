# Integration Test Strategy

**Sprint:** Phase 5.3 - Integration Tests & CI Enforcement
**Task:** Design integration test strategy
**Generated:** 2025-12-14

---

## Executive Summary

This document defines the integration test strategy for Vibey, covering:
1. **End-to-End Flows** - Critical user journeys that span multiple modules
2. **Test Data Management** - How to create, isolate, and clean up test data
3. **Isolation Strategy** - Preventing test interference and ensuring reproducibility
4. **Performance Considerations** - Keeping integration tests fast and reliable

**Goals:**
- Achieve 80%+ integration test coverage for critical flows
- Reduce flaky test rate to <1%
- Maintain test execution time <5 minutes for CI pipeline

---

## 1. Critical End-to-End Flows

### 1.1 CLI-to-Database Flow (HIGHEST PRIORITY)

**Flow:** User runs CLI command -> Operations execute -> YAML/SQLite sync -> State persisted

**Test Cases:**
| Test Case | Entry Point | Expected Outcome |
|-----------|-------------|------------------|
| Create new task | `vibey roadmap add task` | Task exists in YAML + SQLite |
| Start sprint | `vibey roadmap start <sprint>` | Sprint status=in_progress, started timestamp set |
| Complete task | `vibey roadmap complete <task>` | Task status=completed, completed timestamp set |
| Query roadmap | `vibey roadmap status` | Accurate aggregated stats from SQLite |
| Update task | `vibey roadmap update <task> --status` | YAML updated, SQLite synced |

**Modules Involved:**
- `vibey/cli/commands.py` - Command parsing
- `vibey/operations/roadmap/update.py` - Business logic
- `vibey/roadmap/serialization/yaml_loader.py` - YAML read/write
- `vibey/roadmap/database/` - SQLite operations

**Test File:** `tests/integration/test_cli_database_flow.py`

### 1.2 MCP Server Integration (HIGH PRIORITY)

**Flow:** AI assistant calls MCP tool -> Server processes -> Response returned

**Test Cases:**
| Test Case | MCP Tool | Expected Outcome |
|-----------|----------|------------------|
| Get roadmap status | `roadmap_status` | JSON with track/sprint/task counts |
| Start task | `task_start` | Task started, confirmation returned |
| Query specific track | `track_status` | Track details with progress |
| List available tools | Tool discovery | All tools documented and accessible |

**Modules Involved:**
- `vibey/mcp/server.py` - MCP server
- `vibey/mcp/tools/` - Tool implementations
- `vibey/operations/roadmap/query.py` - Data retrieval

**Test File:** `tests/integration/test_mcp_server_flow.py`

### 1.3 Context Management Flow (MEDIUM PRIORITY)

**Flow:** User initializes context -> Writers generate files -> Readers load context -> Agent uses context

**Test Cases:**
| Test Case | Commands | Expected Outcome |
|-----------|----------|------------------|
| Init context directory | `vibey context init` | `.vibey/context/` created with structure |
| Capture work session | `vibey context capture` | Session YAML created with metadata |
| Export context | `vibey context export` | Markdown generated for AI consumption |
| Archive old context | `vibey context archive` | Items moved to archive directory |

**Modules Involved:**
- `vibey/cli/commands.py` - Context commands
- `vibey/operations/context/writers.py` - Context file generation
- `vibey/operations/context/readers.py` - Context file parsing
- `vibey/operations/context/agent_context.py` - AI integration

**Test File:** `tests/integration/test_context_management_flow.py`

### 1.4 YAML-SQLite Synchronization (HIGH PRIORITY)

**Flow:** YAML modified -> Sync triggered -> SQLite updated -> Query returns updated data

**Test Cases:**
| Test Case | Scenario | Expected Outcome |
|-----------|----------|------------------|
| Manual YAML edit | Edit task.yaml directly | SQLite reflects change after rebuild |
| Concurrent modifications | Two processes update | No data loss, last-write-wins or conflict detected |
| Schema migration | New field added | Backward compatible, old data preserved |
| Corruption recovery | Malformed YAML | Graceful error, no SQLite corruption |

**Modules Involved:**
- `vibey/roadmap/serialization/yaml_loader.py`
- `vibey/roadmap/serialization/sql_loader.py`
- `vibey/roadmap/database/connection.py`

**Test File:** `tests/integration/test_yaml_sqlite_sync.py`

---

## 2. Test Data Management

### 2.1 Test Data Strategy

**Principle:** Each test creates its own isolated data, cleans up after itself.

**Approach:**
```python
@pytest.fixture
def isolated_roadmap(tmp_path):
    """Create a minimal roadmap structure for testing."""
    roadmap_dir = tmp_path / ".vibey" / "roadmap"
    roadmap_dir.mkdir(parents=True)

    # Create minimal roadmap.yaml
    (roadmap_dir / "roadmap.yaml").write_text(MINIMAL_ROADMAP_YAML)

    # Create tracks/sprints/tasks directories
    for subdir in ["tracks", "sprints", "tasks"]:
        (roadmap_dir / subdir).mkdir()

    yield roadmap_dir

    # Cleanup handled by tmp_path fixture
```

### 2.2 Test Data Templates

**Minimal Roadmap:**
```yaml
roadmap:
  id: test-roadmap
  name: Test Roadmap
  status: in_progress
```

**Test Track:**
```yaml
track:
  id: 01TEST000000000000000000001
  name: Test Track
  roadmap_id: test-roadmap
  status: in_progress
```

**Test Sprint:**
```yaml
sprint:
  id: 01TEST000000000000000000002
  name: Test Sprint 1
  track_id: 01TEST000000000000000000001
  roadmap_id: test-roadmap
  status: not_started
```

**Test Task:**
```yaml
task:
  id: 01TEST000000000000000000003
  title: Test Task 1
  sprint_id: 01TEST000000000000000000002
  track_id: 01TEST000000000000000000001
  roadmap_id: test-roadmap
  status: not_started
  task_type: development
```

### 2.3 Data Generation Helpers

```python
# tests/fixtures/roadmap_factory.py

class RoadmapFactory:
    """Factory for creating test roadmap structures."""

    @staticmethod
    def create_minimal(tmp_path: Path) -> Path:
        """Create minimal valid roadmap."""
        pass

    @staticmethod
    def create_with_tasks(tmp_path: Path, task_count: int = 5) -> Path:
        """Create roadmap with N tasks for testing."""
        pass

    @staticmethod
    def create_with_all_statuses(tmp_path: Path) -> Path:
        """Create roadmap with tasks in every status."""
        pass
```

---

## 3. Isolation Strategy

### 3.1 File System Isolation

**Approach:** Use `tmp_path` fixture for all file operations.

```python
@pytest.fixture
def isolated_workspace(tmp_path, monkeypatch):
    """Isolate test from real file system."""
    # Override home directory
    monkeypatch.setenv("HOME", str(tmp_path))

    # Override vibey config path
    monkeypatch.setenv("VIBEY_CONFIG_PATH", str(tmp_path / ".vibey"))

    # Override database path
    monkeypatch.setenv("VIBEY_DB_PATH", str(tmp_path / ".vibey" / "roadmap.db"))

    yield tmp_path
```

### 3.2 Database Isolation

**Approach:** In-memory SQLite for unit tests, temp file for integration tests.

```python
@pytest.fixture
def isolated_db(tmp_path):
    """Create isolated SQLite database."""
    db_path = tmp_path / "test_roadmap.db"

    # Initialize schema
    from vibey.roadmap.database.schema import create_tables
    engine = create_engine(f"sqlite:///{db_path}")
    create_tables(engine)

    yield db_path

    # Cleanup handled by tmp_path
```

### 3.3 Environment Isolation

**Approach:** Mock environment variables and configuration.

```python
@pytest.fixture
def isolated_env(monkeypatch):
    """Isolate environment variables."""
    # Clear potentially conflicting env vars
    for var in ["VIBEY_DEBUG", "VIBEY_VERBOSE", "VIBEY_CONFIG_PATH"]:
        monkeypatch.delenv(var, raising=False)

    yield
```

### 3.4 Git Repository Isolation

**Approach:** Create temporary git repos for tests that need version control.

```python
@pytest.fixture
def isolated_git_repo(tmp_path):
    """Create isolated git repository."""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()

    subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_path)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path)

    yield repo_path
```

---

## 4. Performance Considerations

### 4.1 Test Execution Targets

| Test Category | Target Time | Max Time |
|---------------|-------------|----------|
| Single integration test | <500ms | 2s |
| Integration test suite | <2min | 5min |
| Full CI pipeline | <5min | 10min |

### 4.2 Performance Optimization Techniques

**1. Fixture Reuse:**
```python
# Use session-scoped fixtures for expensive setup
@pytest.fixture(scope="session")
def database_schema():
    """Create schema once per test session."""
    pass

# Use function-scoped for test-specific data
@pytest.fixture(scope="function")
def test_data(database_schema):
    """Create fresh data for each test."""
    pass
```

**2. Parallel Execution:**
```bash
# Run tests in parallel with pytest-xdist
pytest tests/integration/ -n auto
```

**3. Selective Test Running:**
```bash
# Run only changed integration tests
pytest tests/integration/ --changed-only
```

**4. Database Optimization:**
```python
# Use WAL mode for concurrent reads
connection.execute("PRAGMA journal_mode=WAL")

# Use in-memory for read-only tests
engine = create_engine("sqlite:///:memory:")
```

### 4.3 Flaky Test Prevention

**1. Avoid timing dependencies:**
```python
# BAD: Sleep-based waiting
time.sleep(1)
assert result is not None

# GOOD: Polling with timeout
result = wait_for(lambda: get_result(), timeout=5)
assert result is not None
```

**2. Deterministic data ordering:**
```python
# BAD: Rely on dictionary order
tasks = get_tasks()
assert tasks[0].name == "First"

# GOOD: Explicit ordering
tasks = sorted(get_tasks(), key=lambda t: t.created)
assert tasks[0].name == "First"
```

**3. Isolated randomness:**
```python
# BAD: Global random state
import random
task_id = random.choice(task_ids)

# GOOD: Seeded random for reproducibility
import random
rng = random.Random(42)
task_id = rng.choice(task_ids)
```

---

## 5. CI Integration

### 5.1 GitHub Actions Workflow

```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  integration:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run integration tests
        run: |
          pytest tests/integration/ \
            --cov=vibey \
            --cov-report=xml \
            --cov-fail-under=60 \
            -v

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
          fail_ci_if_error: true
```

### 5.2 Coverage Enforcement

**Thresholds:**
| Module | Minimum Coverage |
|--------|------------------|
| `vibey/cli/` | 60% |
| `vibey/operations/roadmap/` | 70% |
| `vibey/mcp/` | 50% |
| `vibey/roadmap/serialization/` | 65% |

**Enforcement:**
```bash
# Fail if coverage drops below threshold
pytest --cov=vibey --cov-fail-under=60
```

### 5.3 Quality Gates

**Pre-merge requirements:**
1. All integration tests pass
2. Coverage threshold met
3. No new flaky tests introduced
4. Performance regression check passes

---

## 6. Implementation Roadmap

### Phase 1: Foundation (Week 1)

1. Create test fixture infrastructure
   - `RoadmapFactory` class
   - Isolation fixtures
   - Database fixtures

2. Implement CLI-Database flow tests
   - Task lifecycle tests
   - Sprint lifecycle tests
   - Query tests

### Phase 2: MCP & Context (Week 2)

1. MCP server integration tests
   - Tool availability tests
   - Request/response cycle tests
   - Error handling tests

2. Context management tests
   - Init/capture/export cycle
   - Archive functionality

### Phase 3: Sync & CI (Week 3)

1. YAML-SQLite sync tests
   - Roundtrip integrity
   - Concurrent access
   - Recovery scenarios

2. CI pipeline setup
   - GitHub Actions workflow
   - Coverage reporting
   - Quality gates

---

## 7. Success Metrics

| Metric | Current | Target | Timeline |
|--------|---------|--------|----------|
| Integration test count | ~20 | 60+ | 3 weeks |
| Integration test coverage | ~15% | 60% | 3 weeks |
| Flaky test rate | Unknown | <1% | 3 weeks |
| CI execution time | N/A | <5 min | 3 weeks |

---

## 8. Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Flaky tests slow CI | Medium | Strict isolation, retry logic |
| Slow test execution | Low | Parallel execution, fixture reuse |
| Test data conflicts | Medium | Unique IDs per test, cleanup fixtures |
| Platform differences | Low | CI matrix testing (Linux/macOS/Windows) |

---

## Next Steps

1. Review this strategy with team
2. Begin Phase 1 implementation
3. Track progress in sprint status
4. Adjust strategy based on findings
