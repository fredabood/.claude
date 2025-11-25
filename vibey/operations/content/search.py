"""
Content Search.

Search content by keywords, tags, and other criteria.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional

from .models import ContentType, ContentItem
from .loader import ContentLoader, get_loader


@dataclass
class SearchResult:
    """A single search result with relevance score."""

    item: ContentItem
    score: float
    matched_fields: List[str] = field(default_factory=list)

    @property
    def id(self) -> str:
        return self.item.id

    @property
    def name(self) -> str:
        return self.item.name


class ContentSearch:
    """
    Search content by various criteria.

    Supports:
    - Keyword search across name, description, body
    - Tag filtering
    - Type filtering
    - Category filtering
    """

    def __init__(self, loader: Optional[ContentLoader] = None):
        """
        Initialize search.

        Args:
            loader: Content loader instance
        """
        self.loader = loader or get_loader()

    def search(
        self,
        query: str,
        content_type: Optional[ContentType] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
    ) -> List[SearchResult]:
        """
        Search content by query string.

        Args:
            query: Search query (keywords)
            content_type: Filter by content type
            category: Filter by category
            tags: Filter by tags (content must have all specified tags)
            limit: Maximum results to return

        Returns:
            List of SearchResult ordered by relevance
        """
        # Load all content matching type/category filters
        items = self.loader.list_content(content_type, category)

        # Filter by tags
        if tags:
            items = [
                item for item in items
                if all(tag in item.metadata.tags for tag in tags)
            ]

        # Score each item against query
        results = []
        query_lower = query.lower()
        query_words = query_lower.split()

        for item in items:
            score, matched_fields = self._score_item(item, query_lower, query_words)
            if score > 0:
                results.append(SearchResult(item=item, score=score, matched_fields=matched_fields))

        # Sort by score (descending)
        results.sort(key=lambda r: r.score, reverse=True)

        return results[:limit]

    def _score_item(
        self,
        item: ContentItem,
        query_lower: str,
        query_words: List[str]
    ) -> tuple[float, List[str]]:
        """
        Calculate relevance score for an item.

        Returns:
            Tuple of (score, list of matched field names)
        """
        score = 0.0
        matched_fields = []

        # Exact ID match (highest priority)
        if item.id.lower() == query_lower:
            score += 100
            matched_fields.append("id")
        elif query_lower in item.id.lower():
            score += 50
            matched_fields.append("id")

        # Name match
        name_lower = item.name.lower()
        if query_lower in name_lower:
            score += 40
            matched_fields.append("name")
        else:
            # Check individual words
            name_word_matches = sum(1 for w in query_words if w in name_lower)
            if name_word_matches > 0:
                score += 10 * name_word_matches
                matched_fields.append("name")

        # Description match
        desc_lower = item.metadata.description.lower()
        if query_lower in desc_lower:
            score += 20
            matched_fields.append("description")
        else:
            desc_word_matches = sum(1 for w in query_words if w in desc_lower)
            if desc_word_matches > 0:
                score += 5 * desc_word_matches
                matched_fields.append("description")

        # Tag match
        for tag in item.metadata.tags:
            if query_lower in tag.lower():
                score += 15
                if "tags" not in matched_fields:
                    matched_fields.append("tags")

        # Body match (lower priority)
        body_lower = item.body.lower()
        body_word_matches = sum(1 for w in query_words if w in body_lower)
        if body_word_matches > 0:
            score += 2 * body_word_matches
            matched_fields.append("body")

        # Type/category bonus if query matches
        if item.metadata.type and query_lower in item.metadata.type.lower():
            score += 10
            matched_fields.append("type")

        if item.category and query_lower in item.category.lower():
            score += 10
            matched_fields.append("category")

        return score, matched_fields

    def find_by_trigger(
        self,
        trigger: str,
        content_type: ContentType = ContentType.AGENT
    ) -> List[SearchResult]:
        """
        Find content by trigger pattern.

        Searches the triggers.keywords field for agents.

        Args:
            trigger: Trigger keyword to search for
            content_type: Content type (default: agent)

        Returns:
            List of matching SearchResult
        """
        items = self.loader.list_content(content_type)
        results = []
        trigger_lower = trigger.lower()

        for item in items:
            # Check triggers.keywords in extra fields
            triggers = item.metadata.extra.get("triggers", {})
            keywords = triggers.get("keywords", [])

            if isinstance(keywords, list):
                for kw in keywords:
                    if trigger_lower in str(kw).lower():
                        results.append(SearchResult(
                            item=item,
                            score=100 if str(kw).lower() == trigger_lower else 50,
                            matched_fields=["triggers.keywords"]
                        ))
                        break

        results.sort(key=lambda r: r.score, reverse=True)
        return results

    def find_related(
        self,
        content_id: str,
        limit: int = 10
    ) -> List[SearchResult]:
        """
        Find content related to the given content.

        Searches for content that:
        - References this content
        - Has similar tags
        - Is in the same category

        Args:
            content_id: ID of content to find related items for
            limit: Maximum results

        Returns:
            List of related SearchResult
        """
        # Load the source content
        source = self.loader.load_by_id(content_id)
        if source is None:
            return []

        all_items = self.loader.list_content()
        results = []

        for item in all_items:
            if item.id == content_id:
                continue

            score = 0.0
            matched_fields = []

            # Check for direct references
            if content_id in item.body or content_id in str(item._raw_frontmatter):
                score += 50
                matched_fields.append("reference")

            # Check tag overlap
            source_tags = set(source.metadata.tags)
            item_tags = set(item.metadata.tags)
            common_tags = source_tags & item_tags
            if common_tags:
                score += 10 * len(common_tags)
                matched_fields.append("tags")

            # Same category bonus
            if source.category and item.category == source.category:
                score += 20
                matched_fields.append("category")

            # Same type bonus
            if source.content_type == item.content_type:
                score += 5
                matched_fields.append("type")

            if score > 0:
                results.append(SearchResult(item=item, score=score, matched_fields=matched_fields))

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]


# Module-level convenience functions
_default_search: Optional[ContentSearch] = None


def get_search() -> ContentSearch:
    """Get the default search instance."""
    global _default_search
    if _default_search is None:
        _default_search = ContentSearch()
    return _default_search


def search_content(
    query: str,
    content_type: Optional[ContentType] = None,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    limit: int = 50,
) -> List[SearchResult]:
    """Search content by query."""
    return get_search().search(query, content_type, category, tags, limit)
