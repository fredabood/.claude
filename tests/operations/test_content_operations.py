"""
Content Operations Tests.

Tests for the vibey.operations.content module.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from vibey.operations.content import (
    ContentType,
    ContentMetadata,
    ContentItem,
    ContentValidationResult,
    ContentOperationResult,
    ContentLoader,
    ContentWriter,
    ContentValidator,
    ContentSearch,
    ContentBackup,
    extract_frontmatter,
    compose_content,
    list_content,
    load_content,
    create_content,
    update_content,
    delete_content,
    search_content,
)


class TestContentType:
    """Tests for ContentType enum."""

    def test_from_path_agent(self):
        """Test content type detection for agents."""
        path = Path("/some/path/agents/core/coordinator.md")
        assert ContentType.from_path(path) == ContentType.AGENT

    def test_from_path_workflow(self):
        """Test content type detection for workflows."""
        path = Path("/some/path/workflows/planning/sprint-planning.md")
        assert ContentType.from_path(path) == ContentType.WORKFLOW

    def test_from_path_template(self):
        """Test content type detection for templates."""
        path = Path("/some/path/templates/handoff.md")
        assert ContentType.from_path(path) == ContentType.TEMPLATE

    def test_from_path_unknown(self):
        """Test content type detection for unknown paths."""
        path = Path("/some/random/path/file.md")
        assert ContentType.from_path(path) is None

    def test_directory_name(self):
        """Test directory name property."""
        assert ContentType.AGENT.directory_name == "agents"
        assert ContentType.WORKFLOW.directory_name == "workflows"
        assert ContentType.TEMPLATE.directory_name == "templates"

    def test_file_extension(self):
        """Test file extension property."""
        assert ContentType.AGENT.file_extension == ".md"
        assert ContentType.SCHEMA.file_extension == ".yaml"


class TestContentMetadata:
    """Tests for ContentMetadata dataclass."""

    def test_from_frontmatter(self):
        """Test creating metadata from frontmatter dict."""
        frontmatter = {
            "id": "test-agent",
            "name": "Test Agent",
            "version": "1.0.0",
            "type": "core",
            "description": "A test agent",
            "tags": ["test", "example"],
            "custom_field": "custom_value"
        }

        metadata = ContentMetadata.from_frontmatter(frontmatter)

        assert metadata.id == "test-agent"
        assert metadata.name == "Test Agent"
        assert metadata.version == "1.0.0"
        assert metadata.type == "core"
        assert metadata.description == "A test agent"
        assert metadata.tags == ["test", "example"]
        assert "custom_field" in metadata.extra

    def test_to_frontmatter(self):
        """Test converting metadata back to frontmatter."""
        metadata = ContentMetadata(
            id="test-agent",
            name="Test Agent",
            version="1.0.0",
            type="core",
            description="A test agent",
            tags=["test"],
            extra={"custom": "value"}
        )

        frontmatter = metadata.to_frontmatter()

        assert frontmatter["id"] == "test-agent"
        assert frontmatter["name"] == "Test Agent"
        assert frontmatter["type"] == "core"
        assert frontmatter["custom"] == "value"


class TestFrontmatterParsing:
    """Tests for frontmatter extraction and composition."""

    def test_extract_frontmatter(self):
        """Test extracting frontmatter from content."""
        content = """---
id: test
name: Test
---
# Body

Some content here.
"""
        frontmatter, body = extract_frontmatter(content)

        assert frontmatter is not None
        assert frontmatter["id"] == "test"
        assert frontmatter["name"] == "Test"
        assert "# Body" in body

    def test_extract_no_frontmatter(self):
        """Test extracting from content without frontmatter."""
        content = "# Just a heading\n\nSome content."
        frontmatter, body = extract_frontmatter(content)

        assert frontmatter is None
        assert body == content

    def test_compose_content(self):
        """Test composing content from frontmatter and body."""
        frontmatter = {"id": "test", "name": "Test"}
        body = "# Body\n\nContent here."

        content = compose_content(frontmatter, body)

        assert content.startswith("---")
        assert "id: test" in content
        assert "# Body" in content


class TestContentValidator:
    """Tests for ContentValidator."""

    def test_validate_agent_valid(self):
        """Test validating a valid agent."""
        validator = ContentValidator()
        frontmatter = {
            "id": "test-agent",
            "name": "Test Agent",
            "type": "core",
            "version": "1.0.0"
        }

        result = validator.validate(ContentType.AGENT, frontmatter)

        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_agent_missing_required(self):
        """Test validating agent with missing required fields."""
        validator = ContentValidator()
        frontmatter = {
            "id": "test-agent",
            "name": "Test Agent"
            # missing type and version
        }

        result = validator.validate(ContentType.AGENT, frontmatter)

        assert not result.is_valid
        assert any("type" in e.lower() for e in result.errors)
        assert any("version" in e.lower() for e in result.errors)

    def test_validate_agent_invalid_type(self):
        """Test validating agent with invalid type."""
        validator = ContentValidator()
        frontmatter = {
            "id": "test-agent",
            "name": "Test Agent",
            "type": "invalid-type",
            "version": "1.0.0"
        }

        result = validator.validate(ContentType.AGENT, frontmatter)

        assert not result.is_valid
        assert any("invalid agent type" in e.lower() for e in result.errors)

    def test_validate_workflow_valid(self):
        """Test validating a valid workflow."""
        validator = ContentValidator()
        frontmatter = {
            "id": "test-workflow",
            "name": "Test Workflow",
            "type": "planning",
            "version": "1.0.0"
        }

        result = validator.validate(ContentType.WORKFLOW, frontmatter)

        assert result.is_valid


class TestContentBackup:
    """Tests for ContentBackup."""

    def test_create_backup(self, tmp_path):
        """Test creating a backup."""
        backup = ContentBackup(project_root=tmp_path)

        # Create a file to backup
        test_file = tmp_path / "test.md"
        test_file.write_text("Original content")

        # Create backup
        backup_path = backup.create_backup(test_file, operation="modify")

        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.read_text() == "Original content"

    def test_move_to_trash(self, tmp_path):
        """Test moving file to trash."""
        backup = ContentBackup(project_root=tmp_path)

        # Create a file to trash
        test_file = tmp_path / "test.md"
        test_file.write_text("Content to trash")

        # Move to trash
        trash_path = backup.move_to_trash(test_file)

        assert trash_path is not None
        assert trash_path.exists()
        assert not test_file.exists()

    def test_restore_backup(self, tmp_path):
        """Test restoring from backup."""
        backup = ContentBackup(project_root=tmp_path)

        # Create backup directory and a backup file
        backup_dir = tmp_path / ".vibey/backups/content"
        backup_dir.mkdir(parents=True)
        backup_file = backup_dir / "backup_test.md"
        backup_file.write_text("Backup content")

        # Target file
        target = tmp_path / "restored.md"

        # Restore
        success = backup.restore_backup(backup_file, target)

        assert success
        assert target.exists()
        assert target.read_text() == "Backup content"


class TestContentLoaderWithFixtures:
    """Tests for ContentLoader using test fixtures."""

    @pytest.fixture
    def content_dir(self, tmp_path):
        """Create a temporary content directory with test files."""
        # Create agent
        agents_dir = tmp_path / "agents" / "core"
        agents_dir.mkdir(parents=True)

        agent_content = """---
id: test-agent
name: Test Agent
type: core
version: 1.0.0
description: A test agent
---
# Test Agent

This is a test agent.
"""
        (agents_dir / "test-agent.md").write_text(agent_content)

        # Create workflow
        workflows_dir = tmp_path / "workflows" / "planning"
        workflows_dir.mkdir(parents=True)

        workflow_content = """---
id: test-workflow
name: Test Workflow
type: planning
version: 1.0.0
---
# Test Workflow

This is a test workflow.
"""
        (workflows_dir / "test-workflow.md").write_text(workflow_content)

        return tmp_path

    def test_load_file(self, content_dir):
        """Test loading a single content file."""
        loader = ContentLoader(content_root=content_dir)
        filepath = content_dir / "agents" / "core" / "test-agent.md"

        item = loader.load_file(filepath)

        assert item is not None
        assert item.id == "test-agent"
        assert item.name == "Test Agent"
        assert item.content_type == ContentType.AGENT
        assert item.category == "core"

    def test_load_by_id(self, content_dir):
        """Test loading content by ID."""
        loader = ContentLoader(content_root=content_dir)

        item = loader.load_by_id("test-agent", ContentType.AGENT)

        assert item is not None
        assert item.id == "test-agent"

    def test_list_content(self, content_dir):
        """Test listing all content."""
        loader = ContentLoader(content_root=content_dir)

        items = loader.list_content()

        assert len(items) == 2  # 1 agent + 1 workflow

    def test_list_content_by_type(self, content_dir):
        """Test listing content filtered by type."""
        loader = ContentLoader(content_root=content_dir)

        agents = loader.list_content(ContentType.AGENT)

        assert len(agents) == 1
        assert agents[0].content_type == ContentType.AGENT


class TestContentWriter:
    """Tests for ContentWriter."""

    @pytest.fixture
    def content_setup(self, tmp_path):
        """Set up temporary content directory."""
        agents_dir = tmp_path / "agents" / "core"
        agents_dir.mkdir(parents=True)
        return tmp_path

    def test_create_content(self, content_setup):
        """Test creating new content."""
        writer = ContentWriter(
            content_root=content_setup,
            backup_manager=ContentBackup(project_root=content_setup.parent)
        )

        frontmatter = {
            "id": "new-agent",
            "name": "New Agent",
            "type": "core",
            "version": "1.0.0"
        }
        body = "# New Agent\n\nNew agent content."

        result = writer.create(ContentType.AGENT, frontmatter, body, category="core")

        assert result.success
        assert result.content is not None
        assert result.content.id == "new-agent"

    def test_create_duplicate_fails(self, content_setup):
        """Test creating duplicate content fails."""
        writer = ContentWriter(
            content_root=content_setup,
            backup_manager=ContentBackup(project_root=content_setup.parent)
        )

        frontmatter = {
            "id": "dup-agent",
            "name": "Dup Agent",
            "type": "core",
            "version": "1.0.0"
        }

        # Create first time
        result1 = writer.create(ContentType.AGENT, frontmatter, "", category="core")
        assert result1.success

        # Create again should fail
        result2 = writer.create(ContentType.AGENT, frontmatter, "", category="core")
        assert not result2.success

    def test_update_content(self, content_setup):
        """Test updating existing content."""
        writer = ContentWriter(
            content_root=content_setup,
            backup_manager=ContentBackup(project_root=content_setup.parent)
        )

        # Create content first
        frontmatter = {
            "id": "update-test",
            "name": "Update Test",
            "type": "core",
            "version": "1.0.0"
        }
        writer.create(ContentType.AGENT, frontmatter, "Original body", category="core")

        # Update
        result = writer.update("update-test", {"version": "1.1.0"}, ContentType.AGENT)

        assert result.success

        # Verify update
        loader = ContentLoader(content_root=content_setup)
        item = loader.load_by_id("update-test", ContentType.AGENT)
        assert item.metadata.version == "1.1.0"


class TestContentSearch:
    """Tests for ContentSearch."""

    @pytest.fixture
    def searchable_content(self, tmp_path):
        """Create content for search testing."""
        agents_dir = tmp_path / "agents" / "development"
        agents_dir.mkdir(parents=True)

        # Create multiple agents with different keywords
        agents = [
            ("database-agent", "Database Agent", "Handles database operations"),
            ("api-agent", "API Agent", "Handles API requests"),
            ("test-agent", "Test Agent", "Runs tests"),
        ]

        for aid, name, desc in agents:
            content = f"""---
id: {aid}
name: {name}
type: development
version: 1.0.0
description: {desc}
tags: [{aid.split('-')[0]}]
---
# {name}

{desc}
"""
            (agents_dir / f"{aid}.md").write_text(content)

        return tmp_path

    def test_search_by_keyword(self, searchable_content):
        """Test searching content by keyword."""
        loader = ContentLoader(content_root=searchable_content)
        search = ContentSearch(loader=loader)

        results = search.search("database")

        assert len(results) > 0
        assert results[0].item.id == "database-agent"

    def test_search_with_type_filter(self, searchable_content):
        """Test searching with type filter."""
        loader = ContentLoader(content_root=searchable_content)
        search = ContentSearch(loader=loader)

        results = search.search("agent", ContentType.AGENT)

        assert all(r.item.content_type == ContentType.AGENT for r in results)

    def test_search_scores_exact_match_higher(self, searchable_content):
        """Test that exact ID matches score higher."""
        loader = ContentLoader(content_root=searchable_content)
        search = ContentSearch(loader=loader)

        results = search.search("test-agent")

        # Exact ID match should be first
        assert results[0].item.id == "test-agent"
        assert results[0].score > results[1].score if len(results) > 1 else True


class TestIntegration:
    """Integration tests for content operations."""

    def test_full_crud_cycle(self, tmp_path):
        """Test complete create-read-update-delete cycle."""
        content_root = tmp_path / "content"
        agents_dir = content_root / "agents" / "test"
        agents_dir.mkdir(parents=True)

        loader = ContentLoader(content_root=content_root)
        backup = ContentBackup(project_root=tmp_path)
        writer = ContentWriter(content_root=content_root, backup_manager=backup)

        # Create
        frontmatter = {
            "id": "crud-test",
            "name": "CRUD Test Agent",
            "type": "development",
            "version": "1.0.0"
        }
        create_result = writer.create(ContentType.AGENT, frontmatter, "Test body", category="test")
        assert create_result.success

        # Read
        item = loader.load_by_id("crud-test", ContentType.AGENT)
        assert item is not None
        assert item.name == "CRUD Test Agent"

        # Update
        update_result = writer.update("crud-test", {"version": "2.0.0"}, ContentType.AGENT)
        assert update_result.success

        # Verify update
        item = loader.load_by_id("crud-test", ContentType.AGENT)
        assert item.metadata.version == "2.0.0"

        # Delete
        delete_result = writer.delete("crud-test", ContentType.AGENT)
        assert delete_result.success

        # Verify deleted
        item = loader.load_by_id("crud-test", ContentType.AGENT)
        assert item is None
