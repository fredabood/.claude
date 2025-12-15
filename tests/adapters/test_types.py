"""
Tests for vibey.adapters.types module.

Tests dataclasses for adapter results and capabilities.
"""

import pytest
from pathlib import Path

from vibey.adapters.types import (
    ExportResult,
    PlatformCapabilities,
    AdapterInfo,
)


class TestExportResult:
    """Test ExportResult dataclass."""

    def test_success_no_errors(self):
        """Test success is True when no errors."""
        result = ExportResult(
            platform="test-platform",
            files=[Path("file1.md"), Path("file2.yaml")],
            errors=[],
            warnings=["Minor warning"],
        )
        assert result.success is True

    def test_success_with_errors(self):
        """Test success is False when errors present."""
        result = ExportResult(
            platform="test-platform",
            files=[],
            errors=["Something went wrong"],
        )
        assert result.success is False

    def test_file_count(self):
        """Test file_count property."""
        result = ExportResult(
            platform="test-platform",
            files=[Path("a.md"), Path("b.md"), Path("c.md")],
        )
        assert result.file_count == 3

    def test_file_count_empty(self):
        """Test file_count when empty."""
        result = ExportResult(platform="test-platform")
        assert result.file_count == 0

    def test_to_dict(self):
        """Test to_dict serialization."""
        result = ExportResult(
            platform="goose",
            files=[Path("output/agent.md")],
            errors=[],
            warnings=["Check format"],
        )
        d = result.to_dict()
        assert d["platform"] == "goose"
        assert d["success"] is True
        assert d["file_count"] == 1
        assert d["files"] == ["output/agent.md"]
        assert d["errors"] == []
        assert d["warnings"] == ["Check format"]

    def test_default_factory_lists(self):
        """Test default factory creates empty lists."""
        result = ExportResult(platform="test")
        assert result.files == []
        assert result.errors == []
        assert result.warnings == []


class TestPlatformCapabilities:
    """Test PlatformCapabilities dataclass."""

    def test_default_values(self):
        """Test default capability values."""
        caps = PlatformCapabilities()
        assert caps.agents is True
        assert caps.workflows is True
        assert caps.handoffs is False
        assert caps.real_time_discovery is False
        assert caps.recipes is False
        assert caps.extension_manifest is False

    def test_custom_values(self):
        """Test custom capability values."""
        caps = PlatformCapabilities(
            agents=True,
            workflows=True,
            handoffs=True,
            real_time_discovery=True,
            recipes=True,
            extension_manifest=True,
        )
        assert caps.handoffs is True
        assert caps.recipes is True

    def test_to_dict(self):
        """Test to_dict serialization."""
        caps = PlatformCapabilities(recipes=True)
        d = caps.to_dict()
        assert d["agents"] is True
        assert d["workflows"] is True
        assert d["handoffs"] is False
        assert d["recipes"] is True
        assert d["extension_manifest"] is False


class TestAdapterInfo:
    """Test AdapterInfo dataclass."""

    def test_basic_info(self):
        """Test basic adapter info."""
        info = AdapterInfo(
            platform_name="goose",
            display_name="Goose AI",
            description="Adapter for Goose AI assistant",
            adapter_type="composite",
            base_platform="mcp",
        )
        assert info.platform_name == "goose"
        assert info.display_name == "Goose AI"
        assert info.adapter_type == "composite"
        assert info.base_platform == "mcp"

    def test_default_capabilities(self):
        """Test default capabilities factory."""
        info = AdapterInfo(
            platform_name="test",
            display_name="Test",
            description="Test adapter",
            adapter_type="base",
        )
        assert info.capabilities is not None
        assert info.capabilities.agents is True

    def test_to_dict(self):
        """Test to_dict serialization."""
        caps = PlatformCapabilities(recipes=True)
        info = AdapterInfo(
            platform_name="goose",
            display_name="Goose AI",
            description="Goose adapter",
            adapter_type="composite",
            base_platform="mcp",
            capabilities=caps,
        )
        d = info.to_dict()
        assert d["platform_name"] == "goose"
        assert d["display_name"] == "Goose AI"
        assert d["description"] == "Goose adapter"
        assert d["adapter_type"] == "composite"
        assert d["base_platform"] == "mcp"
        assert d["capabilities"]["recipes"] is True

    def test_base_adapter_no_base_platform(self):
        """Test base adapter has no base_platform."""
        info = AdapterInfo(
            platform_name="mcp",
            display_name="MCP",
            description="MCP adapter",
            adapter_type="base",
        )
        assert info.base_platform is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
