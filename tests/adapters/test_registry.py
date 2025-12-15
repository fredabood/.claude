"""
Tests for vibey.adapters.registry module.

Tests AdapterRegistry for managing platform adapters.
"""

import pytest
from pathlib import Path
from typing import List

from vibey.adapters.registry import AdapterRegistry
from vibey.adapters.types import ExportResult, AdapterInfo, PlatformCapabilities


class MockRegistryAdapter:
    """Mock adapter compatible with AdapterRegistry interface."""

    def __init__(self, platform: str, display: str = None):
        self._platform_name = platform
        self._display_name = display or platform.title()
        self._validation_errors: List[str] = []

    @property
    def platform_name(self) -> str:
        return self._platform_name

    @property
    def display_name(self) -> str:
        return self._display_name

    def get_info(self) -> AdapterInfo:
        return AdapterInfo(
            platform_name=self._platform_name,
            display_name=self._display_name,
            description=f"Mock {self._platform_name} adapter",
            adapter_type="base",
            capabilities=PlatformCapabilities(),
        )

    def export(self, output_dir: Path) -> ExportResult:
        # Simulate creating a file
        output_file = output_dir / f"{self._platform_name}.md"
        output_file.write_text(f"# {self._display_name}")
        return ExportResult(
            platform=self._platform_name,
            files=[output_file],
        )

    def validate(self) -> List[str]:
        return self._validation_errors


class FailingAdapter(MockRegistryAdapter):
    """Adapter that fails export."""

    def export(self, output_dir: Path) -> ExportResult:
        raise RuntimeError("Export failed intentionally")


class TestAdapterRegistry:
    """Test AdapterRegistry class."""

    @pytest.fixture
    def registry(self):
        """Create a fresh registry."""
        return AdapterRegistry()

    @pytest.fixture
    def mock_adapter(self):
        """Create a mock adapter."""
        return MockRegistryAdapter("test-platform", "Test Platform")

    def test_register_adapter(self, registry, mock_adapter):
        """Test registering an adapter."""
        registry.register(mock_adapter)
        assert "test-platform" in registry
        assert len(registry) == 1

    def test_register_duplicate_raises(self, registry, mock_adapter):
        """Test registering duplicate platform raises."""
        registry.register(mock_adapter)
        duplicate = MockRegistryAdapter("test-platform")
        with pytest.raises(ValueError, match="already registered"):
            registry.register(duplicate)

    def test_unregister_existing(self, registry, mock_adapter):
        """Test unregistering existing adapter."""
        registry.register(mock_adapter)
        result = registry.unregister("test-platform")
        assert result is True
        assert "test-platform" not in registry

    def test_unregister_nonexistent(self, registry):
        """Test unregistering non-existent adapter."""
        result = registry.unregister("nonexistent")
        assert result is False

    def test_get_existing(self, registry, mock_adapter):
        """Test getting existing adapter."""
        registry.register(mock_adapter)
        adapter = registry.get("test-platform")
        assert adapter is mock_adapter

    def test_get_nonexistent(self, registry):
        """Test getting non-existent adapter returns None."""
        adapter = registry.get("nonexistent")
        assert adapter is None

    def test_get_required_existing(self, registry, mock_adapter):
        """Test get_required with existing platform."""
        registry.register(mock_adapter)
        adapter = registry.get_required("test-platform")
        assert adapter is mock_adapter

    def test_get_required_nonexistent(self, registry):
        """Test get_required with non-existent platform raises."""
        with pytest.raises(KeyError, match="not found"):
            registry.get_required("nonexistent")

    def test_get_required_shows_available(self, registry, mock_adapter):
        """Test get_required error message shows available platforms."""
        registry.register(mock_adapter)
        try:
            registry.get_required("other")
        except KeyError as e:
            assert "test-platform" in str(e)

    def test_list_platforms(self, registry):
        """Test listing registered platforms."""
        registry.register(MockRegistryAdapter("platform-a"))
        registry.register(MockRegistryAdapter("platform-b"))
        platforms = registry.list_platforms()
        assert "platform-a" in platforms
        assert "platform-b" in platforms
        assert len(platforms) == 2

    def test_list_platforms_empty(self, registry):
        """Test listing platforms when empty."""
        platforms = registry.list_platforms()
        assert platforms == []

    def test_list_adapters(self, registry):
        """Test listing adapter info."""
        registry.register(MockRegistryAdapter("platform-a", "Platform A"))
        registry.register(MockRegistryAdapter("platform-b", "Platform B"))
        infos = registry.list_adapters()
        assert len(infos) == 2
        names = [i.platform_name for i in infos]
        assert "platform-a" in names
        assert "platform-b" in names

    def test_export_single(self, registry, tmp_path):
        """Test exporting to single platform."""
        registry.register(MockRegistryAdapter("goose", "Goose"))
        result = registry.export("goose", tmp_path)
        assert result.success is True
        assert result.platform == "goose"
        assert (tmp_path / "goose.md").exists()

    def test_export_nonexistent_raises(self, registry, tmp_path):
        """Test export to non-existent platform raises."""
        with pytest.raises(KeyError):
            registry.export("nonexistent", tmp_path)

    def test_export_creates_directory(self, registry, tmp_path):
        """Test export creates output directory if needed."""
        registry.register(MockRegistryAdapter("test"))
        output_dir = tmp_path / "nested" / "output"
        result = registry.export("test", output_dir)
        assert result.success is True
        assert output_dir.exists()

    def test_export_all(self, registry, tmp_path):
        """Test exporting to all platforms."""
        registry.register(MockRegistryAdapter("platform-a"))
        registry.register(MockRegistryAdapter("platform-b"))
        results = registry.export_all(tmp_path)
        assert "platform-a" in results
        assert "platform-b" in results
        assert (tmp_path / "platform-a" / "platform-a.md").exists()
        assert (tmp_path / "platform-b" / "platform-b.md").exists()

    def test_export_all_with_failure(self, registry, tmp_path):
        """Test export_all handles failures gracefully."""
        registry.register(MockRegistryAdapter("good"))
        registry.register(FailingAdapter("bad"))
        results = registry.export_all(tmp_path)
        assert results["good"].success is True
        assert results["bad"].success is False
        assert len(results["bad"].errors) > 0

    def test_validate_all_no_errors(self, registry):
        """Test validate_all with no errors."""
        registry.register(MockRegistryAdapter("platform"))
        results = registry.validate_all()
        assert results == {}

    def test_validate_all_with_errors(self, registry):
        """Test validate_all with validation errors."""
        adapter = MockRegistryAdapter("broken")
        adapter._validation_errors = ["Error 1", "Error 2"]
        registry.register(adapter)
        results = registry.validate_all()
        assert "broken" in results
        assert len(results["broken"]) == 2

    def test_len(self, registry):
        """Test __len__ method."""
        assert len(registry) == 0
        registry.register(MockRegistryAdapter("a"))
        assert len(registry) == 1
        registry.register(MockRegistryAdapter("b"))
        assert len(registry) == 2

    def test_contains(self, registry, mock_adapter):
        """Test __contains__ method."""
        assert "test-platform" not in registry
        registry.register(mock_adapter)
        assert "test-platform" in registry

    def test_iter(self, registry):
        """Test __iter__ method."""
        adapter_a = MockRegistryAdapter("a")
        adapter_b = MockRegistryAdapter("b")
        registry.register(adapter_a)
        registry.register(adapter_b)
        adapters = list(registry)
        assert adapter_a in adapters
        assert adapter_b in adapters


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
