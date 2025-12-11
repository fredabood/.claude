"""Tests for HandoffDiscovery module."""

import pytest
from pathlib import Path

from vibey.mcp.discovery.handoffs import (
    HandoffDiscovery,
    HandoffDefinition,
    HandoffVariable,
)


class TestHandoffVariable:
    """Tests for HandoffVariable dataclass."""

    def test_default_values(self):
        """Test default values for HandoffVariable."""
        var = HandoffVariable(name="test")
        assert var.name == "test"
        assert var.type == "string"
        assert var.required is False
        assert var.description is None
        assert var.default is None

    def test_all_values(self):
        """Test HandoffVariable with all values specified."""
        var = HandoffVariable(
            name="count",
            type="integer",
            required=True,
            description="Number of items",
            default=10,
        )
        assert var.name == "count"
        assert var.type == "integer"
        assert var.required is True
        assert var.description == "Number of items"
        assert var.default == 10


class TestHandoffDefinition:
    """Tests for HandoffDefinition dataclass."""

    def test_from_frontmatter_minimal(self, tmp_path):
        """Test parsing minimal frontmatter."""
        filepath = tmp_path / "test.md"
        frontmatter = {
            "id": "test-handoff",
            "name": "Test Handoff",
            "version": "1.0.0",
            "from_agent": "agent-a",
            "to_agents": ["agent-b"],
            "purpose": "Testing",
        }
        handoff = HandoffDefinition.from_frontmatter(frontmatter, filepath)
        assert handoff.id == "test-handoff"
        assert handoff.name == "Test Handoff"
        assert handoff.version == "1.0.0"
        assert handoff.from_agent == "agent-a"
        assert handoff.to_agents == ["agent-b"]
        assert handoff.purpose == "Testing"
        assert handoff.variables == []
        assert handoff.filepath == filepath

    def test_from_frontmatter_with_variables(self, tmp_path):
        """Test parsing frontmatter with variables."""
        filepath = tmp_path / "test.md"
        frontmatter = {
            "id": "test-handoff",
            "name": "Test Handoff",
            "version": "1.0.0",
            "from_agent": "agent-a",
            "to_agents": ["agent-b", "agent-c"],
            "purpose": "Testing",
            "description": "A test handoff",
            "variables": [
                {
                    "name": "task_description",
                    "type": "string",
                    "required": True,
                    "description": "Description of the task",
                },
                {
                    "name": "priority",
                    "type": "string",
                    "required": False,
                    "default": "medium",
                },
            ],
        }
        handoff = HandoffDefinition.from_frontmatter(frontmatter, filepath)
        assert len(handoff.variables) == 2
        assert handoff.variables[0].name == "task_description"
        assert handoff.variables[0].required is True
        assert handoff.variables[1].name == "priority"
        assert handoff.variables[1].default == "medium"

    def test_from_frontmatter_defaults(self, tmp_path):
        """Test default values when frontmatter is incomplete."""
        filepath = tmp_path / "my-handoff.md"
        frontmatter = {}
        handoff = HandoffDefinition.from_frontmatter(frontmatter, filepath)
        assert handoff.id == "my-handoff"  # Falls back to filename
        assert handoff.name == "my-handoff"
        assert handoff.version == "1.0.0"
        assert handoff.from_agent == "unknown"
        assert handoff.to_agents == []
        assert handoff.purpose == ""


class TestHandoffDiscovery:
    """Tests for HandoffDiscovery class."""

    def test_discover_test_handoff(self, handoff_discovery):
        """Test discovering the test handoff from fixtures."""
        handoffs = handoff_discovery.discover()
        assert len(handoffs) >= 1
        assert any(h.id == "test-handoff" for h in handoffs)

    def test_handoff_has_correct_fields(self, handoff_discovery):
        """Test that discovered handoff has correct fields."""
        handoffs = handoff_discovery.discover()
        test_handoff = next((h for h in handoffs if h.id == "test-handoff"), None)
        assert test_handoff is not None
        assert test_handoff.name == "Test Handoff"
        assert test_handoff.from_agent == "agent-a"
        assert "agent-b" in test_handoff.to_agents
        assert test_handoff.purpose == "Test handoff template for unit testing"

    def test_handoff_variables(self, handoff_discovery):
        """Test that handoff variables are parsed correctly."""
        handoffs = handoff_discovery.discover()
        test_handoff = next((h for h in handoffs if h.id == "test-handoff"), None)
        assert test_handoff is not None
        assert len(test_handoff.variables) >= 1
        test_var = next((v for v in test_handoff.variables if v.name == "test_var"), None)
        assert test_var is not None
        assert test_var.required is True
        assert test_var.type == "string"

    def test_get_handoff_by_id(self, handoff_discovery):
        """Test getting a specific handoff by ID."""
        handoff = handoff_discovery.get_handoff_by_id("test-handoff")
        assert handoff is not None
        assert handoff.name == "Test Handoff"

    def test_get_handoff_by_id_not_found(self, handoff_discovery):
        """Test getting a non-existent handoff."""
        handoff = handoff_discovery.get_handoff_by_id("non-existent-handoff")
        assert handoff is None

    def test_get_handoffs_from_agent(self, handoff_discovery):
        """Test getting handoffs from a specific agent."""
        handoffs = handoff_discovery.get_handoffs_from_agent("agent-a")
        assert len(handoffs) >= 1
        assert all(h.from_agent == "agent-a" for h in handoffs)

    def test_get_handoffs_from_agent_none_found(self, handoff_discovery):
        """Test getting handoffs from an agent with no handoffs."""
        handoffs = handoff_discovery.get_handoffs_from_agent("non-existent-agent")
        assert len(handoffs) == 0

    def test_get_handoffs_to_agent(self, handoff_discovery):
        """Test getting handoffs to a specific agent."""
        handoffs = handoff_discovery.get_handoffs_to_agent("agent-b")
        assert len(handoffs) >= 1
        assert all("agent-b" in h.to_agents for h in handoffs)

    def test_get_handoffs_to_agent_none_found(self, handoff_discovery):
        """Test getting handoffs to an agent with no incoming handoffs."""
        handoffs = handoff_discovery.get_handoffs_to_agent("non-existent-agent")
        assert len(handoffs) == 0

    def test_cache_behavior(self, handoff_discovery):
        """Test that discovery results are cached."""
        handoffs1 = handoff_discovery.discover()
        handoffs2 = handoff_discovery.discover()
        # Should return the same cached list
        assert handoffs1 is handoffs2

    def test_force_refresh(self, handoff_discovery):
        """Test force refresh bypasses cache."""
        handoffs1 = handoff_discovery.discover()
        handoffs2 = handoff_discovery.discover(force_refresh=True)
        # Should not be the same object (new list created)
        assert handoffs1 is not handoffs2
        # But should have same content
        assert len(handoffs1) == len(handoffs2)

    def test_invalidate_cache(self, handoff_discovery):
        """Test cache invalidation."""
        handoffs1 = handoff_discovery.discover()
        handoff_discovery.invalidate_cache()
        handoffs2 = handoff_discovery.discover()
        # Should not be the same object after cache invalidation
        assert handoffs1 is not handoffs2

    def test_empty_directory(self, tmp_path):
        """Test discovery with empty handoffs directory."""
        # Create empty directory structure
        handoffs_dir = tmp_path / "vibey" / "content" / "templates" / "handoffs"
        handoffs_dir.mkdir(parents=True)

        discovery = HandoffDiscovery(tmp_path)
        handoffs = discovery.discover()
        assert len(handoffs) == 0

    def test_missing_directory(self, tmp_path):
        """Test discovery with missing handoffs directory."""
        discovery = HandoffDiscovery(tmp_path)
        handoffs = discovery.discover()
        assert len(handoffs) == 0

    def test_skip_readme_files(self, content_root):
        """Test that README.md files are skipped."""
        # Add a README file to the handoffs directory
        handoffs_dir = content_root / "vibey" / "content" / "templates" / "handoffs"
        readme = handoffs_dir / "README.md"
        readme.write_text("# Handoffs\n\nThis is a readme.")

        discovery = HandoffDiscovery(content_root)
        handoffs = discovery.discover()
        # README should not be included
        assert not any(h.name == "README" for h in handoffs)

    def test_malformed_frontmatter_skipped(self, content_root):
        """Test that files with malformed YAML are skipped."""
        handoffs_dir = content_root / "vibey" / "content" / "templates" / "handoffs"
        bad_file = handoffs_dir / "bad-handoff.md"
        bad_file.write_text("---\nthis: is: bad: yaml:\n---\nContent")

        discovery = HandoffDiscovery(content_root)
        handoffs = discovery.discover()
        # Bad file should be skipped, not crash
        assert not any(h.id == "bad-handoff" for h in handoffs)

    def test_no_frontmatter_skipped(self, content_root):
        """Test that files without frontmatter are skipped."""
        handoffs_dir = content_root / "vibey" / "content" / "templates" / "handoffs"
        no_fm = handoffs_dir / "no-frontmatter.md"
        no_fm.write_text("# Just a markdown file\n\nNo frontmatter here.")

        discovery = HandoffDiscovery(content_root)
        handoffs = discovery.discover()
        # File without frontmatter should be skipped
        assert not any(h.id == "no-frontmatter" for h in handoffs)
