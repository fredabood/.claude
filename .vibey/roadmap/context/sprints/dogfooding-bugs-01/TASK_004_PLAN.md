# Task 004: Add Test for CLI Without SQLAlchemy Installed

**Task ID:** dogfooding-bugs-01-task-004
**Bug Addressed:** #6 (SQLAlchemy unconditional import)
**Complexity:** Medium
**Type:** Testing

---

## Problem Statement

There's no automated test to verify that the CLI works without SQLAlchemy installed. This means regressions could reintroduce the unconditional import.

---

## Solution Design

Create tests that verify CLI functionality in a minimal environment without SQLAlchemy.

### Test Approaches

1. **subprocess test** - Run CLI in subprocess with modified PYTHONPATH
2. **mock-based test** - Mock `sys.modules` to simulate missing SQLAlchemy
3. **tox environment** - Separate test environment without SQLAlchemy

---

## Implementation

### Approach 1: Mock-Based Test (Recommended for CI)

```python
# tests/test_cli_no_sqlalchemy.py

import sys
import pytest
from unittest.mock import patch

class TestCLIWithoutSQLAlchemy:
    """Test CLI operations work without SQLAlchemy installed."""

    def setup_method(self):
        """Remove SQLAlchemy from sys.modules before each test."""
        # Store original modules
        self.original_modules = {}
        sqlalchemy_modules = [
            key for key in sys.modules.keys()
            if key.startswith('sqlalchemy')
        ]
        for mod in sqlalchemy_modules:
            self.original_modules[mod] = sys.modules.pop(mod)

    def teardown_method(self):
        """Restore SQLAlchemy modules after each test."""
        sys.modules.update(self.original_modules)

    @patch.dict(sys.modules, {'sqlalchemy': None})
    def test_import_vibey_cli(self):
        """Verify vibey.cli can be imported without SQLAlchemy."""
        # Clear cached imports
        for mod in list(sys.modules.keys()):
            if mod.startswith('vibey'):
                sys.modules.pop(mod, None)

        # Should not raise ImportError
        from vibey.cli import main
        assert main is not None

    def test_roadmap_status_without_sqlalchemy(self, tmp_path, monkeypatch):
        """Verify roadmap status works without SQLAlchemy."""
        # Create minimal roadmap.yaml
        roadmap_dir = tmp_path / ".vibey" / "roadmap"
        roadmap_dir.mkdir(parents=True)
        (roadmap_dir / "roadmap.yaml").write_text("""
roadmap:
  id: test-roadmap
  name: Test
  version: 1.0.0
  status: in_progress
""")

        # Mock sys.modules to block SQLAlchemy
        with patch.dict(sys.modules, {'sqlalchemy': None}):
            from click.testing import CliRunner
            from vibey.cli.main import cli

            runner = CliRunner()
            result = runner.invoke(cli, ['roadmap', 'status'],
                                   catch_exceptions=False)

            assert result.exit_code == 0 or 'status' in result.output.lower()
```

### Approach 2: Subprocess Test

```python
def test_cli_subprocess_no_sqlalchemy(tmp_path):
    """Test CLI in subprocess without SQLAlchemy."""
    import subprocess

    # Create test script that blocks SQLAlchemy
    test_script = tmp_path / "test_import.py"
    test_script.write_text('''
import sys
# Block SQLAlchemy import
sys.modules["sqlalchemy"] = None

try:
    from vibey.cli.main import cli
    print("SUCCESS: CLI imported without SQLAlchemy")
    sys.exit(0)
except ImportError as e:
    if "sqlalchemy" in str(e).lower():
        print(f"FAIL: SQLAlchemy required - {e}")
        sys.exit(1)
    raise
''')

    result = subprocess.run(
        [sys.executable, str(test_script)],
        capture_output=True,
        text=True,
        cwd=str(tmp_path.parent.parent)  # Project root
    )

    assert result.returncode == 0, f"CLI requires SQLAlchemy: {result.stderr}"
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `tests/test_cli_no_sqlalchemy.py` | Test CLI without SQLAlchemy |

---

## Test Cases

1. **test_import_vibey_package** - Package imports without error
2. **test_import_cli_main** - CLI module imports without error
3. **test_roadmap_status** - Status command works with YAML only
4. **test_roadmap_list** - List command works with YAML only
5. **test_db_command_shows_error** - Database commands show helpful error

### Expected Behaviors

| Command | Without SQLAlchemy |
|---------|-------------------|
| `vibey roadmap status` | Works (YAML only) |
| `vibey roadmap list tracks` | Works (YAML only) |
| `vibey roadmap db rebuild` | Shows "Install with: pip install vibey[db]" |
| `vibey roadmap db validate` | Shows "Install with: pip install vibey[db]" |

---

## CI Integration

Add to `.github/workflows/test.yml`:

```yaml
jobs:
  test-minimal:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install minimal dependencies
        run: |
          pip install . --no-deps
          pip install pyyaml jinja2 click rich pydantic jsonschema python-ulid
      - name: Test without SQLAlchemy
        run: |
          pytest tests/test_cli_no_sqlalchemy.py -v
```

---

## Success Criteria

- [ ] Test file created at `tests/test_cli_no_sqlalchemy.py`
- [ ] All test cases pass
- [ ] CI runs tests in minimal environment
- [ ] Tests catch regressions if SQLAlchemy becomes required again

---

## Dependencies

- **Task 001, 002, 003** must be completed first
- Tests will fail until lazy import changes are made

---

## Notes

Consider adding a marker for these tests:

```python
@pytest.mark.no_sqlalchemy
class TestCLIWithoutSQLAlchemy:
    ...
```

Then run specifically with: `pytest -m no_sqlalchemy`
