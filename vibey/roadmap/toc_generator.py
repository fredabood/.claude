"""
Table of Contents Generator - Navigation manifests for hierarchical roadmap

This module generates table_of_contents.json files at each level of the roadmap
hierarchy (roadmap, track, sprint) to enable easy navigation and provide context
about the hierarchy position.

TOC Structure:
- level: Current hierarchy level (roadmap, track, sprint)
- parent: Link to parent object (null for roadmap root)
- current: Current object metadata (id, name, files, context)
- children: List of child objects (tracks for roadmap, sprints for track, tasks for sprint)
- metadata: Progress statistics (tasks/sprints completed, totals)

Key Features:
- Fast generation (<100ms per TOC)
- Accurate parent/child relationships
- Status and progress metadata
- Context file discovery
- Relative path navigation
"""

import json
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
import yaml


@dataclass
class TOCParent:
    """Parent reference in table of contents."""
    type: str  # 'roadmap', 'track', 'sprint'
    path: str  # Relative path to parent
    id: Optional[str] = None  # Parent ID (null for roadmap root)


@dataclass
class TOCFile:
    """File references for current object."""
    yaml: str
    markdown: str
    summary: Optional[str] = None  # COMPLETED summary (e.g., track-COMPLETED.md)


@dataclass
class TOCCurrent:
    """Current object metadata."""
    id: str
    name: str
    files: TOCFile
    context: Optional[List[str]] = None  # Context files in context/ directory


@dataclass
class TOCChild:
    """Child object reference."""
    type: str  # 'track', 'sprint', 'task'
    id: str
    name: str
    path: str  # Relative path to child
    status: str  # 'not_started', 'in_progress', 'completed', 'blocked'


@dataclass
class TOCMetadata:
    """Progress and statistics metadata."""
    # Level-specific totals
    tracks_total: Optional[int] = None
    tracks_completed: Optional[int] = None
    sprints_total: Optional[int] = None
    sprints_completed: Optional[int] = None
    tasks_total: Optional[int] = None
    tasks_completed: Optional[int] = None


@dataclass
class TableOfContents:
    """Complete table of contents structure."""
    level: str  # 'roadmap', 'track', 'sprint'
    parent: Optional[TOCParent]
    current: TOCCurrent
    children: List[TOCChild]
    metadata: TOCMetadata


class TOCGenerator:
    """Generates table_of_contents.json files for roadmap hierarchy."""

    def __init__(self, roadmap_root: str = ".vibey/roadmap"):
        """
        Initialize TOC generator.

        Args:
            roadmap_root: Root directory for roadmap hierarchy
        """
        self.roadmap_root = Path(roadmap_root)

    def generate_roadmap_toc(self, roadmap_yaml_path: str) -> TableOfContents:
        """
        Generate TOC for roadmap root level.

        Args:
            roadmap_yaml_path: Path to roadmap.yaml file

        Returns:
            TableOfContents: Complete TOC structure for roadmap level

        Example:
            >>> gen = TOCGenerator()
            >>> toc = gen.generate_roadmap_toc(".vibey/roadmap.yaml")
            >>> toc.level
            'roadmap'
        """
        roadmap_path = Path(roadmap_yaml_path)

        # Load roadmap YAML
        with open(roadmap_path, 'r') as f:
            roadmap_data = yaml.safe_load(f)

        roadmap_info = roadmap_data.get('roadmap', {})

        # Current object
        current = TOCCurrent(
            id=roadmap_info.get('id', 'unknown'),
            name=roadmap_info.get('name', 'Roadmap'),
            files=TOCFile(
                yaml='roadmap.yaml',
                markdown='roadmap.md',
                summary=None  # Roadmap doesn't have completion summary
            ),
            context=None  # Roadmap root doesn't have context directory
        )

        # Children (tracks)
        children = []
        tracks = roadmap_info.get('tracks', [])

        for track in tracks:
            track_id = track.get('id')
            track_slug = self._id_to_slug(track_id)

            # Try to load track YAML for status
            track_yaml_path = self.roadmap_root / track_slug / f"{track_slug}.yaml"
            status = 'not_started'

            if track_yaml_path.exists():
                try:
                    with open(track_yaml_path, 'r') as f:
                        track_data = yaml.safe_load(f)
                        status = track_data.get('track', {}).get('status', 'not_started')
                except Exception:
                    pass

            children.append(TOCChild(
                type='track',
                id=track_id,
                name=track.get('name', track_id),
                path=f"{track_slug}/",
                status=status
            ))

        # Metadata
        progress = roadmap_info.get('progress', {})
        metadata = TOCMetadata(
            tracks_total=progress.get('tracks_total'),
            tracks_completed=progress.get('tracks_completed'),
            sprints_total=progress.get('sprints_total'),
            sprints_completed=progress.get('sprints_completed'),
            tasks_total=progress.get('tasks_total'),
            tasks_completed=progress.get('tasks_completed')
        )

        return TableOfContents(
            level='roadmap',
            parent=None,  # Roadmap root has no parent
            current=current,
            children=children,
            metadata=metadata
        )

    def generate_track_toc(
        self,
        track_slug: str,
        track_yaml_path: Optional[str] = None
    ) -> TableOfContents:
        """
        Generate TOC for track level.

        Args:
            track_slug: Track directory slug
            track_yaml_path: Optional path to track.yaml (defaults to track_slug/track.yaml)

        Returns:
            TableOfContents: Complete TOC structure for track level
        """
        track_dir = self.roadmap_root / track_slug

        # Default track YAML path
        if track_yaml_path is None:
            track_yaml_path = track_dir / "track.yaml"
        else:
            track_yaml_path = Path(track_yaml_path)

        # Load track YAML
        with open(track_yaml_path, 'r') as f:
            track_data = yaml.safe_load(f)

        track_info = track_data.get('track', {})

        # Discover context files
        context_files = self._discover_context_files(track_dir / "context")

        # Current object
        current = TOCCurrent(
            id=track_info.get('id', 'unknown'),
            name=track_info.get('name', track_slug),
            files=TOCFile(
                yaml="track.yaml",
                markdown="track.md",
                summary=f"{track_slug}-COMPLETED.md"
            ),
            context=context_files if context_files else None
        )

        # Parent (roadmap)
        parent = TOCParent(
            type='roadmap',
            path='../',
            id=track_info.get('roadmap_id')
        )

        # Children (sprints)
        children = []

        # Discover sprint directories
        for item in sorted(track_dir.iterdir()):
            if item.is_dir() and not item.name.startswith('.') and item.name != 'context':
                sprint_slug = item.name
                sprint_yaml_path = item / "sprint.yaml"

                if sprint_yaml_path.exists():
                    try:
                        with open(sprint_yaml_path, 'r') as f:
                            sprint_data = yaml.safe_load(f)
                            sprint_info = sprint_data.get('sprint', {})

                            children.append(TOCChild(
                                type='sprint',
                                id=sprint_info.get('id', sprint_slug),
                                name=sprint_info.get('name', sprint_slug),
                                path=f"{sprint_slug}/",
                                status=sprint_info.get('status', 'not_started')
                            ))
                    except Exception:
                        continue

        # Metadata
        progress = track_info.get('progress', {})
        metadata = TOCMetadata(
            sprints_total=progress.get('sprints_total'),
            sprints_completed=progress.get('sprints_completed'),
            tasks_total=progress.get('tasks_total'),
            tasks_completed=progress.get('tasks_completed')
        )

        return TableOfContents(
            level='track',
            parent=parent,
            current=current,
            children=children,
            metadata=metadata
        )

    def generate_sprint_toc(
        self,
        track_slug: str,
        sprint_slug: str,
        sprint_yaml_path: Optional[str] = None
    ) -> TableOfContents:
        """
        Generate TOC for sprint level.

        Args:
            track_slug: Track directory slug
            sprint_slug: Sprint directory slug
            sprint_yaml_path: Optional path to sprint.yaml

        Returns:
            TableOfContents: Complete TOC structure for sprint level
        """
        track_dir = self.roadmap_root / track_slug
        sprint_dir = track_dir / sprint_slug

        # Default sprint YAML path
        if sprint_yaml_path is None:
            sprint_yaml_path = sprint_dir / "sprint.yaml"
        else:
            sprint_yaml_path = Path(sprint_yaml_path)

        # Load sprint YAML
        with open(sprint_yaml_path, 'r') as f:
            sprint_data = yaml.safe_load(f)

        sprint_info = sprint_data.get('sprint', {})

        # Discover context files
        context_files = self._discover_context_files(sprint_dir / "context")

        # Current object
        current = TOCCurrent(
            id=sprint_info.get('id', 'unknown'),
            name=sprint_info.get('name', sprint_slug),
            files=TOCFile(
                yaml="sprint.yaml",
                markdown="sprint.md",
                summary=f"{sprint_slug}-COMPLETED.md"
            ),
            context=context_files if context_files else None
        )

        # Parent (track)
        parent = TOCParent(
            type='track',
            path='../',
            id=sprint_info.get('track_id')
        )

        # Children (tasks)
        children = []
        tasks = sprint_info.get('tasks', [])

        for task in tasks:
            task_id = task.get('id')
            task_slug = self._id_to_slug(task_id)

            children.append(TOCChild(
                type='task',
                id=task_id,
                name=task.get('name', task_id),
                path=f"{task_slug}/",
                status=task.get('status', 'not_started')
            ))

        # Metadata
        progress = sprint_info.get('progress', {})
        metadata = TOCMetadata(
            tasks_total=progress.get('tasks_total'),
            tasks_completed=progress.get('tasks_completed')
        )

        return TableOfContents(
            level='sprint',
            parent=parent,
            current=current,
            children=children,
            metadata=metadata
        )

    def save_toc(self, toc: TableOfContents, output_path: str) -> None:
        """
        Save TOC to JSON file.

        Args:
            toc: TableOfContents object to save
            output_path: Path to output JSON file
        """
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict, handling None values
        toc_dict = self._toc_to_dict(toc)

        with open(output, 'w') as f:
            json.dump(toc_dict, f, indent=2)

    def generate_and_save_roadmap_toc(
        self,
        roadmap_yaml_path: str,
        output_path: Optional[str] = None
    ) -> TableOfContents:
        """
        Generate and save roadmap TOC in one operation.

        Args:
            roadmap_yaml_path: Path to roadmap.yaml
            output_path: Optional output path (defaults to .vibey/roadmap/table_of_contents.json)

        Returns:
            TableOfContents: Generated TOC
        """
        toc = self.generate_roadmap_toc(roadmap_yaml_path)

        if output_path is None:
            output_path = self.roadmap_root / "table_of_contents.json"

        self.save_toc(toc, output_path)
        return toc

    def generate_and_save_track_toc(
        self,
        track_slug: str,
        track_yaml_path: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> TableOfContents:
        """Generate and save track TOC in one operation."""
        toc = self.generate_track_toc(track_slug, track_yaml_path)

        if output_path is None:
            output_path = self.roadmap_root / track_slug / "table_of_contents.json"

        self.save_toc(toc, output_path)
        return toc

    def generate_and_save_sprint_toc(
        self,
        track_slug: str,
        sprint_slug: str,
        sprint_yaml_path: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> TableOfContents:
        """Generate and save sprint TOC in one operation."""
        toc = self.generate_sprint_toc(track_slug, sprint_slug, sprint_yaml_path)

        if output_path is None:
            output_path = self.roadmap_root / track_slug / sprint_slug / "table_of_contents.json"

        self.save_toc(toc, output_path)
        return toc

    # Private helper methods

    def _discover_context_files(self, context_dir: Path) -> List[str]:
        """
        Discover all files in context directory.

        Args:
            context_dir: Path to context directory

        Returns:
            List of relative paths to context files
        """
        if not context_dir.exists():
            return []

        context_files = []
        for item in sorted(context_dir.rglob('*')):
            if item.is_file():
                rel_path = item.relative_to(context_dir)
                context_files.append(f"context/{rel_path}")

        return context_files

    def _id_to_slug(self, object_id: str) -> str:
        """
        Convert object ID to expected directory slug.

        For now, assumes slug matches ID pattern.
        In future, could read .id files to find correct directory.

        Args:
            object_id: Object ID (e.g., 'mcp-server-1')

        Returns:
            Directory slug
        """
        # Simple implementation: assume ID matches slug
        # Future: implement reverse lookup via .id files
        return object_id

    def _toc_to_dict(self, toc: TableOfContents) -> Dict[str, Any]:
        """
        Convert TableOfContents to dictionary, handling None values.

        Args:
            toc: TableOfContents object

        Returns:
            Dictionary representation
        """
        result = {
            'level': toc.level,
            'parent': self._parent_to_dict(toc.parent) if toc.parent else None,
            'current': self._current_to_dict(toc.current),
            'children': [self._child_to_dict(c) for c in toc.children],
            'metadata': self._metadata_to_dict(toc.metadata)
        }

        return result

    def _parent_to_dict(self, parent: TOCParent) -> Dict[str, Any]:
        """Convert TOCParent to dict."""
        result = {
            'type': parent.type,
            'path': parent.path
        }
        if parent.id:
            result['id'] = parent.id
        return result

    def _current_to_dict(self, current: TOCCurrent) -> Dict[str, Any]:
        """Convert TOCCurrent to dict."""
        result = {
            'id': current.id,
            'name': current.name,
            'files': {
                'yaml': current.files.yaml,
                'markdown': current.files.markdown
            }
        }

        if current.files.summary:
            result['files']['summary'] = current.files.summary

        if current.context:
            result['context'] = current.context

        return result

    def _child_to_dict(self, child: TOCChild) -> Dict[str, Any]:
        """Convert TOCChild to dict."""
        return {
            'type': child.type,
            'id': child.id,
            'name': child.name,
            'path': child.path,
            'status': child.status
        }

    def _metadata_to_dict(self, metadata: TOCMetadata) -> Dict[str, Any]:
        """Convert TOCMetadata to dict, excluding None values."""
        result = {}

        if metadata.tracks_total is not None:
            result['tracks_total'] = metadata.tracks_total
        if metadata.tracks_completed is not None:
            result['tracks_completed'] = metadata.tracks_completed
        if metadata.sprints_total is not None:
            result['sprints_total'] = metadata.sprints_total
        if metadata.sprints_completed is not None:
            result['sprints_completed'] = metadata.sprints_completed
        if metadata.tasks_total is not None:
            result['tasks_total'] = metadata.tasks_total
        if metadata.tasks_completed is not None:
            result['tasks_completed'] = metadata.tasks_completed

        return result


# Convenience functions

def generate_roadmap_toc(
    roadmap_yaml_path: str,
    output_path: Optional[str] = None
) -> TableOfContents:
    """Generate roadmap TOC (convenience function)."""
    gen = TOCGenerator()
    return gen.generate_and_save_roadmap_toc(roadmap_yaml_path, output_path)


def generate_track_toc(
    track_slug: str,
    track_yaml_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> TableOfContents:
    """Generate track TOC (convenience function)."""
    gen = TOCGenerator()
    return gen.generate_and_save_track_toc(track_slug, track_yaml_path, output_path)


def generate_sprint_toc(
    track_slug: str,
    sprint_slug: str,
    sprint_yaml_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> TableOfContents:
    """Generate sprint TOC (convenience function)."""
    gen = TOCGenerator()
    return gen.generate_and_save_sprint_toc(track_slug, sprint_slug, sprint_yaml_path, output_path)


if __name__ == "__main__":
    # Demo usage
    print("=== TOC Generator Demo ===\n")

    # This demo would work with actual roadmap files
    # For now, just show the structure

    print("Example usage:")
    print("1. Generate roadmap TOC:")
    print("   gen = TOCGenerator()")
    print("   toc = gen.generate_and_save_roadmap_toc('.vibey/roadmap.yaml')")
    print()
    print("2. Generate track TOC:")
    print("   toc = gen.generate_and_save_track_toc('core-framework')")
    print()
    print("3. Generate sprint TOC:")
    print("   toc = gen.generate_and_save_sprint_toc('core-framework', 'sprint-1')")
