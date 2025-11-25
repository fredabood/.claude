"""
Vibey Content Operations.

Provides CRUD operations for managing framework content:
- Agents
- Workflows
- Templates
- Handoffs
- Schemas
- Examples

Usage:
    from vibey.operations.content import (
        list_content,
        load_content,
        create_content,
        update_content,
        delete_content,
        search_content,
        ContentType,
    )

    # List all agents
    agents = list_content(ContentType.AGENT)

    # Load a specific agent
    agent = load_content("coordinator")

    # Create new content
    result = create_content(
        ContentType.AGENT,
        frontmatter={"id": "my-agent", "name": "My Agent", "type": "core", "version": "1.0.0"},
        body="# My Agent\\n\\nAgent instructions here.",
        category="core",
    )

    # Update content
    result = update_content("my-agent", {"version": "1.1.0"})

    # Delete content
    result = delete_content("my-agent")

    # Search content
    results = search_content("database", content_type=ContentType.AGENT)
"""

from .models import (
    ContentType,
    ContentMetadata,
    ContentItem,
    ContentValidationResult,
    ContentOperationResult,
)
from .loader import (
    ContentLoader,
    extract_frontmatter,
    compose_content,
    load_content,
    list_content,
    get_loader,
)
from .writer import (
    ContentWriter,
    ContentValidator,
    create_content,
    update_content,
    delete_content,
    get_writer,
)
from .search import (
    ContentSearch,
    SearchResult,
    search_content,
    get_search,
)
from .backup import (
    ContentBackup,
    get_backup_manager,
)

__all__ = [
    # Models
    "ContentType",
    "ContentMetadata",
    "ContentItem",
    "ContentValidationResult",
    "ContentOperationResult",
    # Loader
    "ContentLoader",
    "extract_frontmatter",
    "compose_content",
    "load_content",
    "list_content",
    "get_loader",
    # Writer
    "ContentWriter",
    "ContentValidator",
    "create_content",
    "update_content",
    "delete_content",
    "get_writer",
    # Search
    "ContentSearch",
    "SearchResult",
    "search_content",
    "get_search",
    # Backup
    "ContentBackup",
    "get_backup_manager",
]
