"""
Documentation tracking system for roadmap objects.

Tracks which roadmap objects (tasks/sprints/tracks) impact which project
documentation files using .meta.json sidecar files.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class ChangeType(str, Enum):
    """Types of documentation changes."""
    CREATED = "created"
    ADDED_SECTION = "added_section"
    UPDATED = "updated"
    REFACTORED = "refactored"
    REMOVED = "removed"
    FIXED = "fixed"


@dataclass
class DocImpact:
    """A single documentation impact record."""
    roadmap_object_id: str
    roadmap_object_type: str  # task, sprint, track
    change_type: ChangeType
    section: Optional[str] = None
    description: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "roadmap_object_id": self.roadmap_object_id,
            "roadmap_object_type": self.roadmap_object_type,
            "change_type": self.change_type.value if isinstance(self.change_type, ChangeType) else self.change_type,
            "section": self.section,
            "description": self.description,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocImpact":
        """Create from dictionary."""
        return cls(
            roadmap_object_id=data["roadmap_object_id"],
            roadmap_object_type=data["roadmap_object_type"],
            change_type=ChangeType(data["change_type"]) if isinstance(data["change_type"], str) else data["change_type"],
            section=data.get("section"),
            description=data.get("description"),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat())
        )


@dataclass
class DocMetadata:
    """Metadata for a documentation file."""
    doc_path: str
    title: Optional[str] = None
    created: Optional[str] = None
    last_modified: Optional[str] = None
    impacts: List[DocImpact] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "doc_path": self.doc_path,
            "title": self.title,
            "created": self.created,
            "last_modified": self.last_modified,
            "impacts": [i.to_dict() for i in self.impacts]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocMetadata":
        """Create from dictionary."""
        return cls(
            doc_path=data["doc_path"],
            title=data.get("title"),
            created=data.get("created"),
            last_modified=data.get("last_modified"),
            impacts=[DocImpact.from_dict(i) for i in data.get("impacts", [])]
        )

    def add_impact(self, impact: DocImpact):
        """Add an impact record."""
        self.impacts.append(impact)
        self.last_modified = datetime.now(timezone.utc).isoformat()

    def save(self, root_dir: Path):
        """Save metadata to .meta.json file."""
        meta_path = root_dir / f"{self.doc_path}.meta.json"
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        with open(meta_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, doc_path: str, root_dir: Path) -> Optional["DocMetadata"]:
        """Load metadata from .meta.json file."""
        meta_path = root_dir / f"{doc_path}.meta.json"
        if not meta_path.exists():
            return None
        with open(meta_path) as f:
            return cls.from_dict(json.load(f))

    @classmethod
    def load_or_create(cls, doc_path: str, root_dir: Path) -> "DocMetadata":
        """Load existing metadata or create new."""
        existing = cls.load(doc_path, root_dir)
        if existing:
            return existing
        return cls(
            doc_path=doc_path,
            created=datetime.now(timezone.utc).isoformat(),
            last_modified=datetime.now(timezone.utc).isoformat()
        )


class DocTracker:
    """Tracks documentation impacts from roadmap objects."""

    def __init__(self, root_dir: Path):
        """Initialize doc tracker.

        Args:
            root_dir: Project root directory
        """
        self.root_dir = root_dir

    def link_doc(
        self,
        doc_path: str,
        roadmap_object_id: str,
        change_type: str = "updated",
        section: Optional[str] = None,
        description: Optional[str] = None
    ) -> int:
        """Link a document to a roadmap object.

        Args:
            doc_path: Path to documentation file (relative to root)
            roadmap_object_id: ID of the roadmap object (task, sprint, or track)
            change_type: Type of change (created, added_section, updated, etc.)
            section: Specific section that was changed
            description: Description of the change

        Returns:
            Exit code: 0 for success, 1 for error
        """
        # Validate doc exists
        full_path = self.root_dir / doc_path
        if not full_path.exists():
            print(f"Error: Document not found: {doc_path}")
            return 1

        # Determine object type from ID
        if "-task-" in roadmap_object_id:
            object_type = "task"
        elif roadmap_object_id.count("-") >= 1 and roadmap_object_id.split("-")[-1].isdigit():
            object_type = "sprint"
        else:
            object_type = "track"

        # Parse change type
        try:
            ct = ChangeType(change_type)
        except ValueError:
            print(f"Error: Invalid change type: {change_type}")
            print(f"Valid types: {', '.join(t.value for t in ChangeType)}")
            return 1

        # Load or create metadata
        metadata = DocMetadata.load_or_create(doc_path, self.root_dir)

        # Add impact
        impact = DocImpact(
            roadmap_object_id=roadmap_object_id,
            roadmap_object_type=object_type,
            change_type=ct,
            section=section,
            description=description
        )
        metadata.add_impact(impact)

        # Save
        metadata.save(self.root_dir)

        print(f"Linked {doc_path} to {roadmap_object_id}")
        print(f"  Change type: {change_type}")
        if section:
            print(f"  Section: {section}")
        if description:
            print(f"  Description: {description}")

        return 0

    def list_docs(self, roadmap_object_id: Optional[str] = None) -> List[DocMetadata]:
        """List all tracked documents.

        Args:
            roadmap_object_id: If provided, filter to docs linked to this object

        Returns:
            List of DocMetadata objects
        """
        result = []

        # Find all .meta.json files
        for meta_path in self.root_dir.rglob("*.meta.json"):
            try:
                with open(meta_path) as f:
                    data = json.load(f)
                    metadata = DocMetadata.from_dict(data)

                    if roadmap_object_id:
                        # Filter to docs linked to this object
                        matching_impacts = [
                            i for i in metadata.impacts
                            if i.roadmap_object_id == roadmap_object_id
                        ]
                        if matching_impacts:
                            result.append(metadata)
                    else:
                        result.append(metadata)
            except (json.JSONDecodeError, KeyError):
                continue

        return result

    def generate_changelog(
        self,
        filter_object_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        group_by: str = "object"  # "object" or "time"
    ) -> str:
        """Generate a changelog from documentation impacts.

        Args:
            filter_object_id: Filter to specific roadmap object
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)
            group_by: How to group changes ("object" or "time")

        Returns:
            Markdown formatted changelog
        """
        docs = self.list_docs()

        # Collect all impacts
        all_impacts: List[tuple[str, DocImpact]] = []
        for doc in docs:
            for impact in doc.impacts:
                # Apply filters
                if filter_object_id and impact.roadmap_object_id != filter_object_id:
                    continue
                if start_date and impact.timestamp < start_date:
                    continue
                if end_date and impact.timestamp > end_date:
                    continue
                all_impacts.append((doc.doc_path, impact))

        if not all_impacts:
            return "# Documentation Changelog\n\nNo changes found matching the criteria."

        # Sort by timestamp
        all_impacts.sort(key=lambda x: x[1].timestamp, reverse=True)

        # Build changelog
        lines = ["# Documentation Changelog", ""]

        if group_by == "object":
            # Group by roadmap object
            by_object: Dict[str, List[tuple[str, DocImpact]]] = {}
            for doc_path, impact in all_impacts:
                obj_id = impact.roadmap_object_id
                if obj_id not in by_object:
                    by_object[obj_id] = []
                by_object[obj_id].append((doc_path, impact))

            for obj_id, impacts in by_object.items():
                lines.append(f"## {obj_id}")
                lines.append("")
                for doc_path, impact in impacts:
                    timestamp = impact.timestamp[:10]  # Date only
                    change = impact.change_type.value if isinstance(impact.change_type, ChangeType) else impact.change_type
                    section = f" ({impact.section})" if impact.section else ""
                    desc = f" - {impact.description}" if impact.description else ""
                    lines.append(f"- `{doc_path}`{section}: {change}{desc} ({timestamp})")
                lines.append("")

        else:  # group_by == "time"
            # Group by date
            by_date: Dict[str, List[tuple[str, DocImpact]]] = {}
            for doc_path, impact in all_impacts:
                date = impact.timestamp[:10]
                if date not in by_date:
                    by_date[date] = []
                by_date[date].append((doc_path, impact))

            for date in sorted(by_date.keys(), reverse=True):
                lines.append(f"## {date}")
                lines.append("")
                for doc_path, impact in by_date[date]:
                    obj_id = impact.roadmap_object_id
                    change = impact.change_type.value if isinstance(impact.change_type, ChangeType) else impact.change_type
                    section = f" ({impact.section})" if impact.section else ""
                    desc = f" - {impact.description}" if impact.description else ""
                    lines.append(f"- `{doc_path}`{section}: {change} [{obj_id}]{desc}")
                lines.append("")

        return "\n".join(lines)


# CLI command implementations

def link_doc_cmd(
    doc_path: str,
    roadmap_object_id: str,
    change_type: str = "updated",
    section: Optional[str] = None,
    description: Optional[str] = None
) -> int:
    """Link a document to a roadmap object."""
    tracker = DocTracker(Path.cwd())
    return tracker.link_doc(doc_path, roadmap_object_id, change_type, section, description)


def list_docs_cmd(roadmap_object_id: Optional[str] = None) -> int:
    """List all tracked documents."""
    tracker = DocTracker(Path.cwd())
    docs = tracker.list_docs(roadmap_object_id)

    if not docs:
        print("No tracked documents found.")
        return 0

    print(f"Found {len(docs)} tracked document(s):\n")

    for doc in docs:
        print(f"  {doc.doc_path}")
        if doc.title:
            print(f"    Title: {doc.title}")
        print(f"    Impacts: {len(doc.impacts)}")
        if doc.impacts:
            for impact in doc.impacts[-3:]:  # Show last 3
                change = impact.change_type.value if isinstance(impact.change_type, ChangeType) else impact.change_type
                print(f"      - {impact.roadmap_object_id}: {change} ({impact.timestamp[:10]})")
        print()

    return 0


def doc_changelog_cmd(
    filter_object_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    group_by: str = "object",
    output_file: Optional[str] = None
) -> int:
    """Generate a documentation changelog."""
    tracker = DocTracker(Path.cwd())
    changelog = tracker.generate_changelog(
        filter_object_id=filter_object_id,
        start_date=start_date,
        end_date=end_date,
        group_by=group_by
    )

    if output_file:
        with open(output_file, "w") as f:
            f.write(changelog)
        print(f"Changelog written to: {output_file}")
    else:
        print(changelog)

    return 0
