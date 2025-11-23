"""
Unit tests for FrontmatterParser.

Tests the YAML frontmatter extraction from markdown files
used for agent and workflow discovery.
"""

import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile
import yaml

from framework.mcp.discovery.parser import FrontmatterParser


class TestFrontmatterParser:
    """Tests for FrontmatterParser class."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance."""
        return FrontmatterParser()

    # =========================================================================
    # Basic Parsing Tests
    # =========================================================================

    def test_parse_valid_frontmatter(self, parser):
        """Test parsing valid YAML frontmatter."""
        content = """---
id: test-agent
name: Test Agent
type: quality
---

# Test Agent

This is the body content.
"""
        frontmatter, body = parser.parse_content(content)

        assert frontmatter is not None
        assert frontmatter['id'] == 'test-agent'
        assert frontmatter['name'] == 'Test Agent'
        assert frontmatter['type'] == 'quality'
        assert '# Test Agent' in body
        assert 'This is the body content.' in body

    def test_parse_no_frontmatter(self, parser):
        """Test parsing content without frontmatter."""
        content = """# Just a Regular Markdown File

No frontmatter here.
"""
        frontmatter, body = parser.parse_content(content)

        assert frontmatter is None
        assert '# Just a Regular Markdown File' in body

    def test_parse_empty_frontmatter(self, parser):
        """Test parsing content with empty frontmatter block."""
        content = """---
---

# Empty Frontmatter
"""
        frontmatter, body = parser.parse_content(content)

        # Empty YAML returns None
        assert frontmatter is None

    def test_parse_malformed_frontmatter(self, parser):
        """Test parsing content with malformed frontmatter (missing closing ---)."""
        content = """---
id: test
name: Test

# Missing closing delimiter
"""
        frontmatter, body = parser.parse_content(content)

        # Should return None for malformed frontmatter
        assert frontmatter is None
        assert '---' in body

    def test_parse_complex_frontmatter(self, parser):
        """Test parsing frontmatter with nested structures."""
        content = """---
id: complex-agent
name: Complex Agent
triggers:
  keywords:
    - write tests
    - pytest
    - coverage
  file_patterns:
    - tests/*
    - test_*.py
inputs:
  - name: code_to_test
    type: string
    required: true
  - name: coverage_threshold
    type: number
    required: false
    default: 80
outputs:
  - name: test_results
    type: object
---

# Complex Agent
"""
        frontmatter, body = parser.parse_content(content)

        assert frontmatter is not None
        assert frontmatter['id'] == 'complex-agent'
        assert frontmatter['triggers']['keywords'] == ['write tests', 'pytest', 'coverage']
        assert len(frontmatter['inputs']) == 2
        assert frontmatter['inputs'][0]['name'] == 'code_to_test'
        assert frontmatter['inputs'][1]['default'] == 80

    # =========================================================================
    # File Parsing Tests
    # =========================================================================

    def test_parse_file(self, parser, tmp_path):
        """Test parsing a markdown file from disk."""
        test_file = tmp_path / "test-agent.md"
        test_file.write_text("""---
id: file-agent
name: File Agent
---

# File Agent Content
""")
        frontmatter, body = parser.parse_file(test_file)

        assert frontmatter is not None
        assert frontmatter['id'] == 'file-agent'
        assert '# File Agent Content' in body

    def test_parse_nonexistent_file(self, parser):
        """Test parsing a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            parser.parse_file(Path("/nonexistent/file.md"))

    def test_parse_file_invalid_yaml(self, parser, tmp_path):
        """Test parsing a file with invalid YAML raises error."""
        test_file = tmp_path / "invalid.md"
        test_file.write_text("""---
id: [unclosed bracket
name: Invalid
---

# Content
""")
        with pytest.raises(yaml.YAMLError):
            parser.parse_file(test_file)

    # =========================================================================
    # has_frontmatter Tests
    # =========================================================================

    def test_has_frontmatter_true(self, parser):
        """Test has_frontmatter returns True for valid frontmatter."""
        content = """---
id: test
---

Body
"""
        assert parser.has_frontmatter(content) is True

    def test_has_frontmatter_false_no_delimiters(self, parser):
        """Test has_frontmatter returns False when no delimiters."""
        content = "# Just markdown\n\nNo frontmatter."
        assert parser.has_frontmatter(content) is False

    def test_has_frontmatter_false_malformed(self, parser):
        """Test has_frontmatter returns False for malformed."""
        content = """---
id: test
# Missing closing delimiter
"""
        assert parser.has_frontmatter(content) is False

    # =========================================================================
    # validate_frontmatter Tests
    # =========================================================================

    def test_validate_frontmatter_all_required_present(self, parser):
        """Test validation passes when all required fields present."""
        frontmatter = {
            'id': 'test-agent',
            'name': 'Test Agent',
            'type': 'quality'
        }
        is_valid, errors = parser.validate_frontmatter(
            frontmatter,
            required_fields=['id', 'name', 'type']
        )

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_frontmatter_missing_required(self, parser):
        """Test validation fails when required fields missing."""
        frontmatter = {
            'id': 'test-agent',
            # missing 'name' and 'type'
        }
        is_valid, errors = parser.validate_frontmatter(
            frontmatter,
            required_fields=['id', 'name', 'type']
        )

        assert is_valid is False
        assert len(errors) == 2
        assert any('name' in e for e in errors)
        assert any('type' in e for e in errors)

    def test_validate_frontmatter_null_value(self, parser):
        """Test validation fails when required field is null."""
        frontmatter = {
            'id': 'test-agent',
            'name': None,
            'type': 'quality'
        }
        is_valid, errors = parser.validate_frontmatter(
            frontmatter,
            required_fields=['id', 'name', 'type']
        )

        assert is_valid is False
        assert any('null' in e.lower() for e in errors)

    def test_validate_frontmatter_empty_string(self, parser):
        """Test validation fails when required field is empty string."""
        frontmatter = {
            'id': 'test-agent',
            'name': '   ',  # whitespace only
            'type': 'quality'
        }
        is_valid, errors = parser.validate_frontmatter(
            frontmatter,
            required_fields=['id', 'name', 'type']
        )

        assert is_valid is False
        assert any('empty' in e.lower() for e in errors)

    # =========================================================================
    # Edge Cases
    # =========================================================================

    def test_parse_frontmatter_with_special_characters(self, parser):
        """Test parsing frontmatter with special characters."""
        content = """---
id: special-chars
description: "Contains: colons, 'quotes', and # hashes"
emoji: "🚀"
---

# Content
"""
        frontmatter, body = parser.parse_content(content)

        assert frontmatter is not None
        assert frontmatter['id'] == 'special-chars'
        assert 'colons' in frontmatter['description']
        assert frontmatter['emoji'] == '🚀'

    def test_parse_frontmatter_with_multiline_string(self, parser):
        """Test parsing frontmatter with multiline strings."""
        content = """---
id: multiline
description: |
  This is a multiline
  description that spans
  multiple lines.
---

# Content
"""
        frontmatter, body = parser.parse_content(content)

        assert frontmatter is not None
        assert 'multiline' in frontmatter['description']
        assert 'multiple lines' in frontmatter['description']

    def test_parse_whitespace_before_frontmatter(self, parser):
        """Test parsing fails gracefully when whitespace before frontmatter."""
        content = """
---
id: test
---

# Content
"""
        frontmatter, body = parser.parse_content(content)

        # Leading whitespace means no frontmatter detected
        assert frontmatter is None
