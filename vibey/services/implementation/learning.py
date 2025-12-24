"""
LearningCapture - Knowledge base building from task learnings.

This module provides the LearningCapture class for extracting, categorizing,
and organizing learnings from completed tasks to build knowledge bases at
sprint and track levels.

Key Features:
- LearningCategory enum for classifying types of learnings
- Learning dataclass for structured learning records
- LearningCapture class for knowledge base operations
- Sprint retrospective generation
- Track knowledge base maintenance
- Similar task discovery for learning transfer

Usage:
    from vibey.services.implementation import (
        LearningCapture,
        LearningCategory,
        Learning,
    )
    from pathlib import Path

    # Initialize with context root
    capture = LearningCapture(context_root=Path(".vibey/roadmap"))

    # Capture learnings from a completed task
    learnings = capture.capture_task_learnings(task, post_mortem)

    # Update sprint retrospective
    capture.update_sprint_retrospective(sprint_id="01KCZF...")

    # Update track knowledge base
    capture.update_track_knowledge_base(track_id="01KCZF...")

    # Find similar tasks for learning transfer
    similar = capture.find_similar_tasks(task)

    # Get relevant learnings for an upcoming task
    relevant = capture.get_relevant_learnings(task)

Design Reference:
- Context System V2 Sprint 2
- Task: 01KCZF73PX9YNKWXKYVARY89NY
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from vibey.roadmap.models.ticket.hierarchical import HierarchicalTicket
from vibey.operations.context.models import PostMortemContext

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================


class LearningCategory(str, Enum):
    """
    Category for classifying learnings.

    Values:
        PATTERN: Good approaches that worked well and should be reused
        ANTI_PATTERN: Things that didn't work or caused problems, to avoid
        DISCOVERY: New information or findings uncovered during work
        TIP: Helpful hints and best practices
        BUG_PATTERN: Common bug types and how to prevent them
    """

    PATTERN = "pattern"
    ANTI_PATTERN = "anti_pattern"
    DISCOVERY = "discovery"
    TIP = "tip"
    BUG_PATTERN = "bug_pattern"

    @property
    def display_name(self) -> str:
        """Human-readable display name."""
        display_map = {
            LearningCategory.PATTERN: "Pattern",
            LearningCategory.ANTI_PATTERN: "Anti-Pattern",
            LearningCategory.DISCOVERY: "Discovery",
            LearningCategory.TIP: "Tip",
            LearningCategory.BUG_PATTERN: "Bug Pattern",
        }
        return display_map[self]

    @property
    def section_title(self) -> str:
        """Title for use in retrospective sections."""
        title_map = {
            LearningCategory.PATTERN: "Patterns (What Worked)",
            LearningCategory.ANTI_PATTERN: "Anti-Patterns (What to Avoid)",
            LearningCategory.DISCOVERY: "Discoveries",
            LearningCategory.TIP: "Tips",
            LearningCategory.BUG_PATTERN: "Bug Patterns",
        }
        return title_map[self]


# =============================================================================
# LEARNING DATACLASS
# =============================================================================


@dataclass
class Learning:
    """
    A captured learning from task execution.

    Attributes:
        source_task_id: ULID of the task that generated this learning
        category: Classification of the learning type
        description: Detailed description of what was learned
        applicability: Tags indicating where this learning applies
            (e.g., task types, file patterns, domains)
        created_at: When the learning was captured
    """

    source_task_id: str
    category: LearningCategory
    description: str
    applicability: List[str] = field(default_factory=list)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for storage."""
        return {
            "source_task_id": self.source_task_id,
            "category": self.category.value,
            "description": self.description,
            "applicability": self.applicability,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Learning":
        """Deserialize from storage."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        elif created_at is None:
            created_at = datetime.now(timezone.utc)

        return cls(
            source_task_id=data.get("source_task_id", ""),
            category=LearningCategory(data.get("category", "discovery")),
            description=data.get("description", ""),
            applicability=data.get("applicability", []),
            created_at=created_at,
        )

    def matches_tags(self, tags: List[str]) -> bool:
        """Check if this learning matches any of the given tags."""
        if not tags or not self.applicability:
            return False
        return bool(set(self.applicability) & set(tags))


# =============================================================================
# LEARNING CAPTURE
# =============================================================================


class LearningCapture:
    """
    Capture and organize learnings from task execution.

    LearningCapture extracts learnings from completed tasks and their
    post-mortems, categorizes them, and maintains knowledge bases at
    sprint and track levels.

    Attributes:
        context_root: Path to the context storage root (.vibey/roadmap)

    Example:
        >>> capture = LearningCapture(Path(".vibey/roadmap"))
        >>> learnings = capture.capture_task_learnings(task, post_mortem)
        >>> capture.update_sprint_retrospective("01KCZF...")
    """

    def __init__(self, context_root: Path):
        """
        Initialize LearningCapture with context root.

        Args:
            context_root: Path to .vibey/roadmap directory
        """
        self.context_root = Path(context_root)
        self._learnings_cache: Dict[str, List[Learning]] = {}

        logger.debug(f"LearningCapture initialized with context root: {context_root}")

    # =========================================================================
    # MAIN METHODS
    # =========================================================================

    def capture_task_learnings(
        self,
        task: HierarchicalTicket,
        post_mortem: PostMortemContext,
    ) -> List[Learning]:
        """
        Extract and categorize learnings from a completed task's post-mortem.

        Analyzes the post-mortem content to identify patterns, anti-patterns,
        discoveries, tips, and bug patterns.

        Args:
            task: The completed HierarchicalTicket
            post_mortem: PostMortemContext with completion details

        Returns:
            List of Learning objects extracted from the post-mortem
        """
        learnings: List[Learning] = []

        # Extract applicability tags from task
        applicability = self._extract_applicability_tags(task)

        # Process lessons learned
        for lesson in post_mortem.lessons_learned:
            category = self._categorize_learning(lesson)
            learnings.append(
                Learning(
                    source_task_id=task.id,
                    category=category,
                    description=lesson,
                    applicability=applicability,
                )
            )

        # Process detailed lessons if available
        for detailed in post_mortem.detailed_lessons:
            category = self._categorize_learning(detailed.lesson)
            applicability_with_tags = list(
                set(applicability + detailed.applies_to)
            )
            learnings.append(
                Learning(
                    source_task_id=task.id,
                    category=category,
                    description=f"{detailed.lesson}\n{detailed.details}".strip(),
                    applicability=applicability_with_tags,
                )
            )

        # Process key decisions as potential patterns
        for decision in post_mortem.key_decisions:
            learnings.append(
                Learning(
                    source_task_id=task.id,
                    category=LearningCategory.PATTERN,
                    description=f"Decision: {decision}",
                    applicability=applicability,
                )
            )

        # Process detailed decisions
        for detailed in post_mortem.detailed_key_decisions:
            learnings.append(
                Learning(
                    source_task_id=task.id,
                    category=LearningCategory.PATTERN,
                    description=(
                        f"Decision: {detailed.decision}\n"
                        f"Rationale: {detailed.rationale}\n"
                        f"Impact: {detailed.impact}"
                    ).strip(),
                    applicability=applicability,
                )
            )

        # Store learnings for the task
        self._store_learnings(task.id, learnings)

        logger.info(
            f"Captured {len(learnings)} learnings from task {task.id}"
        )
        return learnings

    def update_sprint_retrospective(self, sprint_id: str) -> Path:
        """
        Update sprint-level retrospective with aggregated learnings.

        Creates or updates the SPRINT_RETROSPECTIVE.md file with:
        - Summary of completed tasks
        - Key learnings by category
        - Metrics summary
        - Recommendations for future sprints

        Args:
            sprint_id: ULID of the sprint to update

        Returns:
            Path to the created/updated retrospective file
        """
        # Get sprint directory
        sprint_dir = self.context_root / "context" / "sprints" / sprint_id
        sprint_dir.mkdir(parents=True, exist_ok=True)

        retro_path = sprint_dir / "SPRINT_RETROSPECTIVE.md"

        # Gather all learnings for tasks in this sprint
        all_learnings = self._gather_sprint_learnings(sprint_id)

        # Get sprint info if available
        sprint_info = self._load_sprint_info(sprint_id)

        # Generate retrospective content
        content = self._generate_sprint_retrospective(
            sprint_id=sprint_id,
            learnings=all_learnings,
            sprint_info=sprint_info,
        )

        # Write the retrospective
        retro_path.write_text(content, encoding="utf-8")

        logger.info(
            f"Updated sprint retrospective at {retro_path} "
            f"with {len(all_learnings)} learnings"
        )
        return retro_path

    def update_track_knowledge_base(self, track_id: str) -> Path:
        """
        Update track-level knowledge base with accumulated learnings.

        Creates or updates the KNOWLEDGE_BASE.md file with:
        - Patterns that have proven successful
        - Anti-patterns to avoid
        - Key discoveries
        - Best practices and tips

        Args:
            track_id: ULID of the track to update

        Returns:
            Path to the created/updated knowledge base file
        """
        # Get track directory
        track_dir = self.context_root / "context" / "tracks" / track_id
        track_dir.mkdir(parents=True, exist_ok=True)

        kb_path = track_dir / "KNOWLEDGE_BASE.md"

        # Gather all learnings for the track
        all_learnings = self._gather_track_learnings(track_id)

        # Get track info if available
        track_info = self._load_track_info(track_id)

        # Generate knowledge base content
        content = self._generate_knowledge_base(
            track_id=track_id,
            learnings=all_learnings,
            track_info=track_info,
        )

        # Write the knowledge base
        kb_path.write_text(content, encoding="utf-8")

        logger.info(
            f"Updated track knowledge base at {kb_path} "
            f"with {len(all_learnings)} learnings"
        )
        return kb_path

    def find_similar_tasks(self, task: HierarchicalTicket) -> List[str]:
        """
        Find similar completed tasks for learning transfer.

        Uses task attributes like type, file patterns, and description
        to identify related tasks that might have relevant learnings.

        Args:
            task: The task to find similar tasks for

        Returns:
            List of task IDs that are similar to the given task
        """
        similar_ids: List[str] = []
        task_tags = self._extract_applicability_tags(task)

        # Search through stored learnings
        learnings_dir = self.context_root / "context" / "learnings"
        if not learnings_dir.exists():
            return similar_ids

        # Collect all task IDs with matching learnings
        seen_tasks: set = set()

        for learning_file in learnings_dir.glob("*.yaml"):
            try:
                with open(learning_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}

                for learning_data in data.get("learnings", []):
                    learning = Learning.from_dict(learning_data)

                    # Skip the same task
                    if learning.source_task_id == task.id:
                        continue

                    # Check for tag overlap
                    if learning.matches_tags(task_tags):
                        if learning.source_task_id not in seen_tasks:
                            similar_ids.append(learning.source_task_id)
                            seen_tasks.add(learning.source_task_id)

            except Exception as e:
                logger.warning(f"Error reading learning file {learning_file}: {e}")

        logger.debug(f"Found {len(similar_ids)} similar tasks for {task.id}")
        return similar_ids

    def get_relevant_learnings(self, task: HierarchicalTicket) -> List[Learning]:
        """
        Get learnings relevant to an upcoming task.

        Searches the knowledge base for learnings that match the task's
        characteristics and could help with implementation.

        Args:
            task: The upcoming task to find learnings for

        Returns:
            List of Learning objects relevant to the task
        """
        relevant: List[Learning] = []
        task_tags = self._extract_applicability_tags(task)

        # Search through stored learnings
        learnings_dir = self.context_root / "context" / "learnings"
        if not learnings_dir.exists():
            return relevant

        for learning_file in learnings_dir.glob("*.yaml"):
            try:
                with open(learning_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}

                for learning_data in data.get("learnings", []):
                    learning = Learning.from_dict(learning_data)

                    # Skip learnings from the same task
                    if learning.source_task_id == task.id:
                        continue

                    # Check for relevance
                    if learning.matches_tags(task_tags):
                        relevant.append(learning)

            except Exception as e:
                logger.warning(f"Error reading learning file {learning_file}: {e}")

        # Sort by category priority (patterns first, then tips, etc.)
        priority = {
            LearningCategory.PATTERN: 1,
            LearningCategory.TIP: 2,
            LearningCategory.ANTI_PATTERN: 3,
            LearningCategory.BUG_PATTERN: 4,
            LearningCategory.DISCOVERY: 5,
        }
        relevant.sort(key=lambda x: priority.get(x.category, 99))

        logger.debug(f"Found {len(relevant)} relevant learnings for {task.id}")
        return relevant

    # =========================================================================
    # HELPER METHODS - CATEGORIZATION
    # =========================================================================

    def _categorize_learning(self, text: str) -> LearningCategory:
        """
        Categorize a learning based on its content.

        Uses keyword matching to determine the most appropriate category.

        Args:
            text: The learning text to categorize

        Returns:
            The most appropriate LearningCategory
        """
        text_lower = text.lower()

        # Check for anti-pattern indicators
        anti_pattern_keywords = [
            "don't", "avoid", "never", "shouldn't", "failed",
            "mistake", "wrong", "problem", "issue", "broke",
            "anti-pattern", "antipattern",
        ]
        if any(kw in text_lower for kw in anti_pattern_keywords):
            return LearningCategory.ANTI_PATTERN

        # Check for bug pattern indicators
        bug_keywords = [
            "bug", "error", "exception", "crash", "fix",
            "null", "undefined", "race condition", "memory leak",
        ]
        if any(kw in text_lower for kw in bug_keywords):
            return LearningCategory.BUG_PATTERN

        # Check for discovery indicators
        discovery_keywords = [
            "discovered", "found", "learned", "realized",
            "unexpected", "surprise", "interesting",
        ]
        if any(kw in text_lower for kw in discovery_keywords):
            return LearningCategory.DISCOVERY

        # Check for tip indicators
        tip_keywords = [
            "tip", "hint", "trick", "shortcut", "faster",
            "easier", "better way", "pro tip",
        ]
        if any(kw in text_lower for kw in tip_keywords):
            return LearningCategory.TIP

        # Default to pattern for positive learnings
        pattern_keywords = [
            "worked", "success", "effective", "efficient",
            "pattern", "approach", "solution", "best practice",
        ]
        if any(kw in text_lower for kw in pattern_keywords):
            return LearningCategory.PATTERN

        # Default category
        return LearningCategory.DISCOVERY

    def _extract_applicability_tags(
        self, task: HierarchicalTicket
    ) -> List[str]:
        """
        Extract applicability tags from a task.

        Generates tags based on task type, file patterns, and content.

        Args:
            task: The task to extract tags from

        Returns:
            List of applicability tags
        """
        tags: List[str] = []

        # Add task type if available
        if hasattr(task, "task_type_detail") and task.task_type_detail:
            tags.append(f"task:{task.task_type_detail}")

        # Add ticket type
        if task.ticket_type:
            tags.append(f"type:{task.ticket_type.value}")

        # Extract file patterns from description
        if task.description:
            # Look for file paths in description
            file_patterns = re.findall(
                r'[\w\-]+/[\w\-/]+\.(?:py|ts|js|yaml|md|json)',
                task.description
            )
            for pattern in file_patterns:
                # Extract the directory/module name
                parts = pattern.split("/")
                if len(parts) >= 2:
                    tags.append(f"module:{parts[0]}")

        # Add complexity if available
        if hasattr(task, "complexity") and task.complexity:
            tags.append(f"complexity:{task.complexity}")

        # Deduplicate and return
        return list(set(tags))

    # =========================================================================
    # HELPER METHODS - STORAGE
    # =========================================================================

    def _store_learnings(self, task_id: str, learnings: List[Learning]) -> None:
        """Store learnings for a task."""
        learnings_dir = self.context_root / "context" / "learnings"
        learnings_dir.mkdir(parents=True, exist_ok=True)

        learnings_path = learnings_dir / f"{task_id}.yaml"

        data = {
            "task_id": task_id,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "learnings": [l.to_dict() for l in learnings],
        }

        with open(learnings_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        # Update cache
        self._learnings_cache[task_id] = learnings

    def _load_learnings(self, task_id: str) -> List[Learning]:
        """Load learnings for a task."""
        if task_id in self._learnings_cache:
            return self._learnings_cache[task_id]

        learnings_path = (
            self.context_root / "context" / "learnings" / f"{task_id}.yaml"
        )

        if not learnings_path.exists():
            return []

        try:
            with open(learnings_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            learnings = [
                Learning.from_dict(l) for l in data.get("learnings", [])
            ]
            self._learnings_cache[task_id] = learnings
            return learnings

        except Exception as e:
            logger.warning(f"Error loading learnings for {task_id}: {e}")
            return []

    # =========================================================================
    # HELPER METHODS - GATHERING
    # =========================================================================

    def _gather_sprint_learnings(self, sprint_id: str) -> List[Learning]:
        """Gather all learnings from tasks in a sprint."""
        learnings: List[Learning] = []
        learnings_dir = self.context_root / "context" / "learnings"

        if not learnings_dir.exists():
            return learnings

        # Load sprint tasks to get task IDs
        tasks_file = self.context_root / "sprints" / f"{sprint_id}.yaml"
        task_ids: List[str] = []

        if tasks_file.exists():
            try:
                with open(tasks_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                    sprint_data = data.get("sprint", data)
                    task_ids = sprint_data.get("children", [])
            except Exception as e:
                logger.warning(f"Error loading sprint {sprint_id}: {e}")

        # Load learnings for each task
        for task_id in task_ids:
            learnings.extend(self._load_learnings(task_id))

        return learnings

    def _gather_track_learnings(self, track_id: str) -> List[Learning]:
        """Gather all learnings from a track's sprints."""
        learnings: List[Learning] = []

        # Load track to get sprint IDs
        track_file = self.context_root / "tracks" / f"{track_id}.yaml"
        sprint_ids: List[str] = []

        if track_file.exists():
            try:
                with open(track_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                    track_data = data.get("track", data)
                    sprint_ids = track_data.get("children", [])
            except Exception as e:
                logger.warning(f"Error loading track {track_id}: {e}")

        # Gather learnings from each sprint
        for sprint_id in sprint_ids:
            learnings.extend(self._gather_sprint_learnings(sprint_id))

        return learnings

    def _load_sprint_info(self, sprint_id: str) -> Dict[str, Any]:
        """Load sprint metadata."""
        sprint_file = self.context_root / "sprints" / f"{sprint_id}.yaml"

        if not sprint_file.exists():
            return {}

        try:
            with open(sprint_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                return data.get("sprint", data)
        except Exception as e:
            logger.warning(f"Error loading sprint info {sprint_id}: {e}")
            return {}

    def _load_track_info(self, track_id: str) -> Dict[str, Any]:
        """Load track metadata."""
        track_file = self.context_root / "tracks" / f"{track_id}.yaml"

        if not track_file.exists():
            return {}

        try:
            with open(track_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                return data.get("track", data)
        except Exception as e:
            logger.warning(f"Error loading track info {track_id}: {e}")
            return {}

    # =========================================================================
    # HELPER METHODS - CONTENT GENERATION
    # =========================================================================

    def _generate_sprint_retrospective(
        self,
        sprint_id: str,
        learnings: List[Learning],
        sprint_info: Dict[str, Any],
    ) -> str:
        """Generate sprint retrospective markdown content."""
        name = sprint_info.get("name", sprint_id)
        start_date = sprint_info.get("start_date", "Unknown")
        end_date = sprint_info.get("end_date", "Unknown")

        # Group learnings by category
        by_category: Dict[LearningCategory, List[Learning]] = {}
        for learning in learnings:
            if learning.category not in by_category:
                by_category[learning.category] = []
            by_category[learning.category].append(learning)

        # Calculate metrics
        total_tasks = len(sprint_info.get("children", []))
        completed_tasks = sprint_info.get("completed_count", 0)
        total_tokens = sprint_info.get("total_tokens", 0)
        bugs_found = len(by_category.get(LearningCategory.BUG_PATTERN, []))

        # Build content
        lines = [
            f"# Sprint Retrospective: {name}",
            "",
            f"**Period:** {start_date} - {end_date}",
            f"**Tasks Completed:** {completed_tasks}/{total_tasks}",
            f"**Total Tokens:** {total_tokens:,}",
            "",
            "## Key Learnings",
            "",
        ]

        # Add sections for each category
        for category in LearningCategory:
            category_learnings = by_category.get(category, [])
            if category_learnings:
                lines.append(f"### {category.section_title}")
                lines.append("")
                for learning in category_learnings:
                    # Format multiline descriptions
                    desc = learning.description.split("\n")[0]
                    lines.append(f"- {desc}")
                lines.append("")

        # Add metrics table
        avg_efficiency = 0
        if total_tasks > 0 and total_tokens > 0:
            # Simplified efficiency calculation
            avg_efficiency = int((completed_tasks / max(total_tasks, 1)) * 100)

        lines.extend([
            "## Metrics",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Tasks | {completed_tasks}/{total_tasks} |",
            f"| Token Efficiency | {avg_efficiency}% |",
            f"| Bugs Found | {bugs_found} |",
            "",
        ])

        # Add recommendations
        lines.extend([
            "## Recommendations for Future Sprints",
            "",
        ])

        # Generate recommendations from patterns and anti-patterns
        recommendations: List[str] = []

        patterns = by_category.get(LearningCategory.PATTERN, [])
        if patterns:
            recommendations.append(
                f"Continue applying {len(patterns)} successful patterns identified"
            )

        anti_patterns = by_category.get(LearningCategory.ANTI_PATTERN, [])
        if anti_patterns:
            recommendations.append(
                f"Address {len(anti_patterns)} anti-patterns to improve efficiency"
            )

        tips = by_category.get(LearningCategory.TIP, [])
        if tips:
            recommendations.append(
                f"Document and share {len(tips)} helpful tips with team"
            )

        if not recommendations:
            recommendations.append("Continue current practices")

        for rec in recommendations:
            lines.append(f"- {rec}")

        lines.append("")
        lines.append(f"---")
        lines.append(f"*Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*")

        return "\n".join(lines)

    def _generate_knowledge_base(
        self,
        track_id: str,
        learnings: List[Learning],
        track_info: Dict[str, Any],
    ) -> str:
        """Generate track knowledge base markdown content."""
        name = track_info.get("name", track_id)

        # Group learnings by category
        by_category: Dict[LearningCategory, List[Learning]] = {}
        for learning in learnings:
            if learning.category not in by_category:
                by_category[learning.category] = []
            by_category[learning.category].append(learning)

        # Deduplicate learnings by description
        for category in by_category:
            seen: set = set()
            unique: List[Learning] = []
            for learning in by_category[category]:
                key = learning.description[:100]  # Use first 100 chars as key
                if key not in seen:
                    seen.add(key)
                    unique.append(learning)
            by_category[category] = unique

        # Build content
        lines = [
            f"# Knowledge Base: {name}",
            "",
            "This knowledge base contains learnings accumulated from work on this track.",
            "",
        ]

        # Table of contents
        lines.extend([
            "## Contents",
            "",
        ])
        for category in LearningCategory:
            if by_category.get(category):
                anchor = category.value.replace("_", "-")
                lines.append(f"- [{category.section_title}](#{anchor})")
        lines.append("")

        # Add sections for each category
        for category in LearningCategory:
            category_learnings = by_category.get(category, [])
            if category_learnings:
                anchor = category.value.replace("_", "-")
                lines.append(f"## {category.section_title} {{#{anchor}}}")
                lines.append("")

                for learning in category_learnings:
                    # Format as a learning entry
                    lines.append(f"### From Task: `{learning.source_task_id}`")
                    lines.append("")
                    lines.append(learning.description)
                    lines.append("")
                    if learning.applicability:
                        tags = ", ".join(f"`{t}`" for t in learning.applicability)
                        lines.append(f"**Applies to:** {tags}")
                        lines.append("")

        # Add summary statistics
        total_learnings = sum(len(l) for l in by_category.values())
        lines.extend([
            "---",
            "",
            "## Statistics",
            "",
            f"- **Total Learnings:** {total_learnings}",
        ])
        for category in LearningCategory:
            count = len(by_category.get(category, []))
            if count > 0:
                lines.append(f"- **{category.display_name}s:** {count}")

        lines.append("")
        lines.append(f"*Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*")

        return "\n".join(lines)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "LearningCategory",
    "Learning",
    "LearningCapture",
]
