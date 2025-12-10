"""
Test CLI operations work without SQLAlchemy installed.

These tests verify that the CLI can be used without SQLAlchemy,
which is an optional dependency for database functionality.

Task: dogfooding-bugs-01-task-004
Bug: #6 (SQLAlchemy unconditional import)
"""

import sys
from unittest.mock import patch

import pytest


class TestCLIWithoutSQLAlchemy:
    """Test CLI operations work without SQLAlchemy installed."""

    def test_ticket_module_orm_flag(self):
        """Verify _ORM_AVAILABLE flag indicates SQLAlchemy status."""
        # First clear any cached imports
        mods_to_clear = [k for k in sys.modules if k.startswith('vibey.roadmap.models.ticket')]
        for mod in mods_to_clear:
            sys.modules.pop(mod, None)

        # Import and check the flag
        from vibey.roadmap.models.ticket import _ORM_AVAILABLE
        # In test environment, SQLAlchemy may or may not be installed
        # The flag should be a boolean either way
        assert isinstance(_ORM_AVAILABLE, bool)

    def test_serialization_module_sql_flag(self):
        """Verify _SQL_AVAILABLE flag indicates SQLAlchemy status."""
        # First clear any cached imports
        mods_to_clear = [k for k in sys.modules if k.startswith('vibey.roadmap.serialization')]
        for mod in mods_to_clear:
            sys.modules.pop(mod, None)

        # Import and check the flag
        from vibey.roadmap.serialization import _SQL_AVAILABLE
        # In test environment, SQLAlchemy may or may not be installed
        # The flag should be a boolean either way
        assert isinstance(_SQL_AVAILABLE, bool)

    def test_yaml_loader_imports_without_sqlalchemy(self):
        """Verify YAML loader can be imported regardless of SQLAlchemy."""
        # Clear cached imports
        mods_to_clear = [k for k in sys.modules if k.startswith('vibey.roadmap')]
        for mod in mods_to_clear:
            sys.modules.pop(mod, None)

        # These should import successfully whether SQLAlchemy is installed or not
        from vibey.roadmap.serialization import (
            load_roadmap,
            load_track,
            load_sprint,
            load_task,
            save_roadmap,
            save_track,
            save_sprint,
            save_task,
        )

        assert load_roadmap is not None
        assert save_roadmap is not None

    def test_require_sqlalchemy_helper(self):
        """Verify require_sqlalchemy() helper provides useful error."""
        from vibey.roadmap.models.ticket import require_sqlalchemy, _ORM_AVAILABLE

        if _ORM_AVAILABLE:
            # If SQLAlchemy is installed, function should not raise
            require_sqlalchemy()  # Should not raise
        else:
            # If SQLAlchemy is not installed, function should raise ImportError
            with pytest.raises(ImportError) as exc_info:
                require_sqlalchemy()
            assert "sqlalchemy" in str(exc_info.value).lower()

    def test_require_sql_backend_helper(self):
        """Verify require_sql_backend() helper provides useful error."""
        from vibey.roadmap.serialization import require_sql_backend, _SQL_AVAILABLE

        if _SQL_AVAILABLE:
            # If SQLAlchemy is installed, function should not raise
            require_sql_backend()  # Should not raise
        else:
            # If SQLAlchemy is not installed, function should raise ImportError
            with pytest.raises(ImportError) as exc_info:
                require_sql_backend()
            assert "sqlalchemy" in str(exc_info.value).lower()


class TestCLIImportsWithMockedSQLAlchemy:
    """Test CLI imports with SQLAlchemy blocked at import time."""

    @pytest.fixture(autouse=True)
    def clear_vibey_modules(self):
        """Clear vibey modules before and after each test."""
        # Store original state
        original_modules = {k: v for k, v in sys.modules.items() if k.startswith('vibey')}

        # Clear before test
        for mod in list(sys.modules.keys()):
            if mod.startswith('vibey'):
                sys.modules.pop(mod, None)

        yield

        # Clear after test
        for mod in list(sys.modules.keys()):
            if mod.startswith('vibey'):
                sys.modules.pop(mod, None)

        # Restore original modules
        sys.modules.update(original_modules)

    def test_ticket_module_with_blocked_sqlalchemy(self):
        """Test ticket module loads with blocked SQLAlchemy."""
        # Block SQLAlchemy imports
        original_sqlalchemy = sys.modules.get('sqlalchemy')
        try:
            # Remove any existing sqlalchemy modules
            sqlalchemy_mods = [k for k in sys.modules if k.startswith('sqlalchemy')]
            for mod in sqlalchemy_mods:
                sys.modules.pop(mod, None)

            # Create an import blocker
            class SQLAlchemyBlocker:
                def __getattr__(self, name):
                    raise ImportError("Test: SQLAlchemy blocked")

            sys.modules['sqlalchemy'] = SQLAlchemyBlocker()

            # This should import without error
            from vibey.roadmap.models.ticket import (
                Ticket,
                _ORM_AVAILABLE,
            )

            # ORM should not be available
            assert _ORM_AVAILABLE is False
            # But core ticket model should work
            assert Ticket is not None

        finally:
            # Restore sqlalchemy
            if original_sqlalchemy is not None:
                sys.modules['sqlalchemy'] = original_sqlalchemy
            else:
                sys.modules.pop('sqlalchemy', None)

    def test_serialization_module_with_blocked_sqlalchemy(self):
        """Test serialization module loads with blocked SQLAlchemy."""
        # Block SQLAlchemy imports
        original_sqlalchemy = sys.modules.get('sqlalchemy')
        try:
            # Remove any existing sqlalchemy modules
            sqlalchemy_mods = [k for k in sys.modules if k.startswith('sqlalchemy')]
            for mod in sqlalchemy_mods:
                sys.modules.pop(mod, None)

            # Create an import blocker
            class SQLAlchemyBlocker:
                def __getattr__(self, name):
                    raise ImportError("Test: SQLAlchemy blocked")

            sys.modules['sqlalchemy'] = SQLAlchemyBlocker()

            # This should import without error
            from vibey.roadmap.serialization import (
                load_roadmap,
                save_roadmap,
                _SQL_AVAILABLE,
            )

            # SQL should not be available
            assert _SQL_AVAILABLE is False
            # But YAML functions should work
            assert load_roadmap is not None
            assert save_roadmap is not None

        finally:
            # Restore sqlalchemy
            if original_sqlalchemy is not None:
                sys.modules['sqlalchemy'] = original_sqlalchemy
            else:
                sys.modules.pop('sqlalchemy', None)
