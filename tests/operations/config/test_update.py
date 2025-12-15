"""
Tests for vibey.operations.config.update module.

Tests config update operations using dot notation.
"""

import pytest
from pathlib import Path
import tempfile
import yaml

from vibey.operations.config.update import (
    get_nested_value,
    set_nested_value,
    convert_value,
    validate_key_path,
    update_config_value,
    bulk_update_config,
)


class TestGetNestedValue:
    """Test get_nested_value function."""

    def test_single_level_key(self):
        """Test getting single level key."""
        data = {"key": "value"}
        result = get_nested_value(data, "key")
        assert result == "value"

    def test_nested_two_levels(self):
        """Test getting two level nested key."""
        data = {"outer": {"inner": "value"}}
        result = get_nested_value(data, "outer.inner")
        assert result == "value"

    def test_nested_three_levels(self):
        """Test getting three level nested key."""
        data = {"a": {"b": {"c": "deep"}}}
        result = get_nested_value(data, "a.b.c")
        assert result == "deep"

    def test_missing_key_returns_none(self):
        """Test missing key returns None."""
        data = {"key": "value"}
        result = get_nested_value(data, "missing")
        assert result is None

    def test_missing_nested_key_returns_none(self):
        """Test missing nested key returns None."""
        data = {"outer": {"inner": "value"}}
        result = get_nested_value(data, "outer.missing")
        assert result is None

    def test_partial_path_returns_none(self):
        """Test partial path that doesn't exist returns None."""
        data = {"a": "string"}
        result = get_nested_value(data, "a.b")
        assert result is None

    def test_returns_dict_value(self):
        """Test returning a dict value."""
        data = {"outer": {"inner": {"nested": "value"}}}
        result = get_nested_value(data, "outer.inner")
        assert result == {"nested": "value"}

    def test_returns_list_value(self):
        """Test returning a list value."""
        data = {"items": [1, 2, 3]}
        result = get_nested_value(data, "items")
        assert result == [1, 2, 3]


class TestSetNestedValue:
    """Test set_nested_value function."""

    def test_set_single_level(self):
        """Test setting single level key."""
        data = {"key": "old"}
        result = set_nested_value(data, "key", "new")
        assert result["key"] == "new"

    def test_set_nested_value(self):
        """Test setting nested value."""
        data = {"outer": {"inner": "old"}}
        result = set_nested_value(data, "outer.inner", "new")
        assert result["outer"]["inner"] == "new"

    def test_create_missing_path(self):
        """Test creating missing nested path."""
        data = {}
        result = set_nested_value(data, "a.b.c", "value")
        assert result["a"]["b"]["c"] == "value"

    def test_overwrite_non_dict(self):
        """Test overwriting non-dict with nested path."""
        data = {"a": "string"}
        result = set_nested_value(data, "a.b", "value")
        assert result["a"]["b"] == "value"

    def test_preserves_other_keys(self):
        """Test that other keys are preserved."""
        data = {"a": {"x": 1, "y": 2}}
        result = set_nested_value(data, "a.x", 10)
        assert result["a"]["x"] == 10
        assert result["a"]["y"] == 2


class TestConvertValue:
    """Test convert_value function."""

    def test_convert_true_string(self):
        """Test converting 'true' to boolean."""
        assert convert_value("true", None) is True
        assert convert_value("True", None) is True
        assert convert_value("yes", None) is True
        assert convert_value("1", None) == 1  # Converts to int first

    def test_convert_false_string(self):
        """Test converting 'false' to boolean."""
        assert convert_value("false", None) is False
        assert convert_value("False", None) is False
        assert convert_value("no", None) is False
        assert convert_value("0", None) == 0  # Converts to int

    def test_convert_integer(self):
        """Test converting integer string."""
        assert convert_value("42", None) == 42
        assert convert_value("-10", None) == -10

    def test_convert_float(self):
        """Test converting float string."""
        assert convert_value("3.14", None) == 3.14
        assert convert_value("-0.5", None) == -0.5

    def test_keep_string(self):
        """Test keeping non-convertible as string."""
        assert convert_value("hello", None) == "hello"

    def test_convert_based_on_bool_reference(self):
        """Test converting with boolean reference."""
        assert convert_value("true", False) is True
        assert convert_value("false", True) is False
        assert convert_value("1", False) is True
        assert convert_value("0", True) is False

    def test_convert_based_on_int_reference(self):
        """Test converting with int reference."""
        assert convert_value("42", 0) == 42
        assert convert_value("invalid", 0) == "invalid"  # Falls back to string

    def test_convert_based_on_float_reference(self):
        """Test converting with float reference."""
        assert convert_value("3.14", 0.0) == 3.14
        assert convert_value("invalid", 0.0) == "invalid"


class TestValidateKeyPath:
    """Test validate_key_path function."""

    def test_valid_single_key(self):
        """Test valid single key."""
        assert validate_key_path("key") is True

    def test_valid_dotted_path(self):
        """Test valid dotted path."""
        assert validate_key_path("a.b.c") is True

    def test_empty_string_invalid(self):
        """Test empty string is invalid."""
        assert validate_key_path("") is False

    def test_brackets_invalid(self):
        """Test brackets are invalid."""
        assert validate_key_path("items[0]") is False
        assert validate_key_path("data{key}") is False

    def test_spaces_invalid(self):
        """Test spaces are invalid."""
        assert validate_key_path("key with space") is False

    def test_empty_segment_invalid(self):
        """Test empty segment is invalid."""
        assert validate_key_path("a..b") is False
        assert validate_key_path(".a") is False
        assert validate_key_path("a.") is False

    def test_underscores_valid(self):
        """Test underscores are valid."""
        assert validate_key_path("quality_gates.unit_testing") is True


class TestUpdateConfigValue:
    """Test update_config_value function."""

    @pytest.fixture
    def config_file(self, tmp_path):
        """Create a temporary config file."""
        config = {
            "project": {"name": "Test", "version": "1.0.0"},
            "settings": {"enabled": True, "count": 10},
        }
        config_path = tmp_path / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        return config_path

    def test_update_existing_value(self, config_file):
        """Test updating existing value."""
        result = update_config_value(config_file, "project.name", "NewName", verbose=False)
        assert result == 0

        with open(config_file) as f:
            config = yaml.safe_load(f)
        assert config["project"]["name"] == "NewName"

    def test_update_boolean_value(self, config_file):
        """Test updating boolean value."""
        result = update_config_value(config_file, "settings.enabled", "false", verbose=False)
        assert result == 0

        with open(config_file) as f:
            config = yaml.safe_load(f)
        assert config["settings"]["enabled"] is False

    def test_update_integer_value(self, config_file):
        """Test updating integer value."""
        result = update_config_value(config_file, "settings.count", "20", verbose=False)
        assert result == 0

        with open(config_file) as f:
            config = yaml.safe_load(f)
        assert config["settings"]["count"] == 20

    def test_missing_key_without_create(self, config_file):
        """Test missing key without create_missing returns error."""
        result = update_config_value(config_file, "missing.key", "value", verbose=False)
        assert result == 1

    def test_missing_key_with_create(self, config_file):
        """Test missing key with create_missing creates it."""
        result = update_config_value(
            config_file, "new.nested.key", "value", create_missing=True, verbose=False
        )
        assert result == 0

        with open(config_file) as f:
            config = yaml.safe_load(f)
        assert config["new"]["nested"]["key"] == "value"

    def test_file_not_found(self, tmp_path):
        """Test file not found returns error."""
        result = update_config_value(tmp_path / "missing.yaml", "key", "value", verbose=False)
        assert result == 1

    def test_invalid_key_path(self, config_file):
        """Test invalid key path returns error."""
        result = update_config_value(config_file, "invalid[0]", "value", verbose=False)
        assert result == 1


class TestBulkUpdateConfig:
    """Test bulk_update_config function."""

    @pytest.fixture
    def config_file(self, tmp_path):
        """Create a temporary config file."""
        config = {
            "project": {"name": "Test", "version": "1.0.0"},
            "settings": {"enabled": True, "count": 10, "threshold": 0.5},
        }
        config_path = tmp_path / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        return config_path

    def test_bulk_update_multiple_keys(self, config_file):
        """Test bulk updating multiple keys."""
        updates = {
            "project.name": "Updated",
            "settings.count": "20",
        }
        result = bulk_update_config(config_file, updates, verbose=False)
        assert result == 0

        with open(config_file) as f:
            config = yaml.safe_load(f)
        assert config["project"]["name"] == "Updated"
        assert config["settings"]["count"] == 20

    def test_bulk_update_skips_missing_keys(self, config_file):
        """Test bulk update skips missing keys without create_missing."""
        updates = {
            "project.name": "Updated",
            "missing.key": "value",
        }
        result = bulk_update_config(config_file, updates, verbose=False)
        assert result == 0  # Still succeeds for valid keys

        with open(config_file) as f:
            config = yaml.safe_load(f)
        assert config["project"]["name"] == "Updated"
        assert "missing" not in config

    def test_bulk_update_creates_missing_keys(self, config_file):
        """Test bulk update creates missing keys with flag."""
        updates = {
            "new.key": "value",
        }
        result = bulk_update_config(config_file, updates, create_missing=True, verbose=False)
        assert result == 0

        with open(config_file) as f:
            config = yaml.safe_load(f)
        assert config["new"]["key"] == "value"

    def test_bulk_update_skips_invalid_paths(self, config_file):
        """Test bulk update skips invalid key paths."""
        updates = {
            "project.name": "Updated",
            "invalid[0]": "value",
        }
        result = bulk_update_config(config_file, updates, verbose=False)
        assert result == 0

        with open(config_file) as f:
            config = yaml.safe_load(f)
        assert config["project"]["name"] == "Updated"

    def test_file_not_found(self, tmp_path):
        """Test file not found returns error."""
        result = bulk_update_config(tmp_path / "missing.yaml", {"key": "value"}, verbose=False)
        assert result == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
