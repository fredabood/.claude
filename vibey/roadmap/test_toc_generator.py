"""
Unit tests for table of contents generator.

Tests verify:
- TOC generation at all levels (roadmap/track/sprint)
- Parent/child relationships
- Context file discovery
- Metadata accuracy
- JSON output format
- Fast generation (<100ms per TOC)
"""

import unittest
import tempfile
import shutil
import json
import time
from pathlib import Path
import yaml
from framework.roadmap.toc_generator import (
    TOCGenerator,
    TableOfContents,
    TOCParent,
    TOCCurrent,
    TOCChild,
    TOCMetadata,
    TOCFile,
    generate_roadmap_toc,
    generate_track_toc,
    generate_sprint_toc,
)


class TestTOCGeneration(unittest.TestCase):
    """Test TOC generation at all hierarchy levels."""

    def setUp(self):
        """Create temporary directory with test roadmap structure."""
        self.temp_dir = tempfile.mkdtemp()
        self.roadmap_root = Path(self.temp_dir) / ".vibey" / "roadmap"
        self.roadmap_root.mkdir(parents=True)

        # Create test roadmap.yaml
        self.roadmap_yaml_path = Path(self.temp_dir) / ".vibey" / "roadmap.yaml"
        roadmap_data = {
            'roadmap': {
                'id': 'test-roadmap',
                'name': 'Test Roadmap',
                'tracks': [
                    {'id': 'track-1', 'name': 'Track One'},
                    {'id': 'track-2', 'name': 'Track Two'}
                ],
                'progress': {
                    'tracks_total': 2,
                    'tracks_completed': 0,
                    'sprints_total': 3,
                    'sprints_completed': 0,
                    'tasks_total': 10,
                    'tasks_completed': 0
                }
            }
        }

        with open(self.roadmap_yaml_path, 'w') as f:
            yaml.dump(roadmap_data, f)

        self.gen = TOCGenerator(str(self.roadmap_root))

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_generate_roadmap_toc(self):
        """Roadmap TOC is generated correctly."""
        toc = self.gen.generate_roadmap_toc(str(self.roadmap_yaml_path))

        self.assertEqual(toc.level, 'roadmap')
        self.assertIsNone(toc.parent)
        self.assertEqual(toc.current.id, 'test-roadmap')
        self.assertEqual(toc.current.name, 'Test Roadmap')
        self.assertEqual(len(toc.children), 2)
        self.assertEqual(toc.metadata.tracks_total, 2)
        self.assertEqual(toc.metadata.tasks_total, 10)

    def test_generate_track_toc(self):
        """Track TOC is generated correctly."""
        # Create track directory and YAML
        track_dir = self.roadmap_root / "track-1"
        track_dir.mkdir(parents=True)

        track_yaml = track_dir / "track-1.yaml"
        track_data = {
            'track': {
                'id': 'track-1',
                'name': 'Track One',
                'roadmap_id': 'test-roadmap',
                'status': 'in_progress',
                'progress': {
                    'sprints_total': 2,
                    'sprints_completed': 1,
                    'tasks_total': 5,
                    'tasks_completed': 3
                }
            }
        }

        with open(track_yaml, 'w') as f:
            yaml.dump(track_data, f)

        # Create sprint directories
        sprint1_dir = track_dir / "sprint-1"
        sprint1_dir.mkdir()

        sprint1_yaml = sprint1_dir / "sprint-1.yaml"
        sprint1_data = {
            'sprint': {
                'id': 'sprint-1',
                'name': 'Sprint One',
                'track_id': 'track-1',
                'status': 'completed'
            }
        }

        with open(sprint1_yaml, 'w') as f:
            yaml.dump(sprint1_data, f)

        # Generate TOC
        toc = self.gen.generate_track_toc('track-1')

        self.assertEqual(toc.level, 'track')
        self.assertIsNotNone(toc.parent)
        self.assertEqual(toc.parent.type, 'roadmap')
        self.assertEqual(toc.parent.path, '../')
        self.assertEqual(toc.current.id, 'track-1')
        self.assertEqual(len(toc.children), 1)
        self.assertEqual(toc.children[0].type, 'sprint')
        self.assertEqual(toc.children[0].status, 'completed')
        self.assertEqual(toc.metadata.sprints_total, 2)
        self.assertEqual(toc.metadata.tasks_completed, 3)

    def test_generate_sprint_toc(self):
        """Sprint TOC is generated correctly."""
        # Create track and sprint structure
        track_dir = self.roadmap_root / "track-1"
        track_dir.mkdir(parents=True)

        sprint_dir = track_dir / "sprint-1"
        sprint_dir.mkdir()

        sprint_yaml = sprint_dir / "sprint-1.yaml"
        sprint_data = {
            'sprint': {
                'id': 'sprint-1',
                'name': 'Sprint One',
                'track_id': 'track-1',
                'status': 'in_progress',
                'tasks': [
                    {'id': 'task-001', 'name': 'Task One', 'status': 'completed'},
                    {'id': 'task-002', 'name': 'Task Two', 'status': 'in_progress'},
                    {'id': 'task-003', 'name': 'Task Three', 'status': 'not_started'}
                ],
                'progress': {
                    'tasks_total': 3,
                    'tasks_completed': 1
                }
            }
        }

        with open(sprint_yaml, 'w') as f:
            yaml.dump(sprint_data, f)

        # Generate TOC
        toc = self.gen.generate_sprint_toc('track-1', 'sprint-1')

        self.assertEqual(toc.level, 'sprint')
        self.assertIsNotNone(toc.parent)
        self.assertEqual(toc.parent.type, 'track')
        self.assertEqual(toc.parent.id, 'track-1')
        self.assertEqual(toc.current.id, 'sprint-1')
        self.assertEqual(len(toc.children), 3)
        self.assertEqual(toc.children[0].type, 'task')
        self.assertEqual(toc.children[0].status, 'completed')
        self.assertEqual(toc.children[1].status, 'in_progress')
        self.assertEqual(toc.metadata.tasks_total, 3)
        self.assertEqual(toc.metadata.tasks_completed, 1)


class TestContextDiscovery(unittest.TestCase):
    """Test context file discovery."""

    def setUp(self):
        """Create temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.roadmap_root = Path(self.temp_dir) / ".vibey" / "roadmap"
        self.roadmap_root.mkdir(parents=True)
        self.gen = TOCGenerator(str(self.roadmap_root))

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_discover_context_files_empty(self):
        """Empty context directory returns empty list."""
        context_dir = self.roadmap_root / "track-1" / "context"
        context_dir.mkdir(parents=True)

        files = self.gen._discover_context_files(context_dir)
        self.assertEqual(files, [])

    def test_discover_context_files_with_files(self):
        """Context files are discovered correctly."""
        track_dir = self.roadmap_root / "track-1"
        track_dir.mkdir(parents=True)

        context_dir = track_dir / "context"
        context_dir.mkdir()

        # Create context files
        (context_dir / "design.md").write_text("Design doc")
        (context_dir / "architecture.md").write_text("Architecture doc")

        # Create track YAML
        track_yaml = track_dir / "track-1.yaml"
        track_data = {
            'track': {
                'id': 'track-1',
                'name': 'Track One',
                'roadmap_id': 'test-roadmap'
            }
        }

        with open(track_yaml, 'w') as f:
            yaml.dump(track_data, f)

        # Generate TOC
        toc = self.gen.generate_track_toc('track-1')

        self.assertIsNotNone(toc.current.context)
        self.assertEqual(len(toc.current.context), 2)
        self.assertIn('context/architecture.md', toc.current.context)
        self.assertIn('context/design.md', toc.current.context)

    def test_discover_nested_context_files(self):
        """Nested context files are discovered."""
        context_dir = self.roadmap_root / "track-1" / "context"
        context_dir.mkdir(parents=True)

        # Create nested structure
        subdir = context_dir / "research"
        subdir.mkdir()

        (context_dir / "top-level.md").write_text("Top")
        (subdir / "nested.md").write_text("Nested")

        files = self.gen._discover_context_files(context_dir)

        self.assertEqual(len(files), 2)
        self.assertIn('context/top-level.md', files)
        self.assertIn('context/research/nested.md', files)

    def test_context_none_when_no_directory(self):
        """Context is None when directory doesn't exist."""
        track_dir = self.roadmap_root / "track-1"
        track_dir.mkdir(parents=True)

        track_yaml = track_dir / "track-1.yaml"
        track_data = {
            'track': {
                'id': 'track-1',
                'name': 'Track One',
                'roadmap_id': 'test-roadmap'
            }
        }

        with open(track_yaml, 'w') as f:
            yaml.dump(track_data, f)

        toc = self.gen.generate_track_toc('track-1')
        self.assertIsNone(toc.current.context)


class TestJSONOutput(unittest.TestCase):
    """Test JSON output format."""

    def setUp(self):
        """Create temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.roadmap_root = Path(self.temp_dir) / ".vibey" / "roadmap"
        self.roadmap_root.mkdir(parents=True)

        # Create roadmap.yaml
        self.roadmap_yaml_path = Path(self.temp_dir) / ".vibey" / "roadmap.yaml"
        roadmap_data = {
            'roadmap': {
                'id': 'test-roadmap',
                'name': 'Test Roadmap',
                'tracks': [
                    {'id': 'track-1', 'name': 'Track One'}
                ],
                'progress': {
                    'tracks_total': 1,
                    'tracks_completed': 0
                }
            }
        }

        with open(self.roadmap_yaml_path, 'w') as f:
            yaml.dump(roadmap_data, f)

        self.gen = TOCGenerator(str(self.roadmap_root))

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_save_toc_creates_json(self):
        """TOC is saved as valid JSON."""
        toc = self.gen.generate_roadmap_toc(str(self.roadmap_yaml_path))

        output_path = self.roadmap_root / "table_of_contents.json"
        self.gen.save_toc(toc, str(output_path))

        self.assertTrue(output_path.exists())

        # Verify valid JSON
        with open(output_path, 'r') as f:
            data = json.load(f)

        self.assertEqual(data['level'], 'roadmap')
        self.assertIsNone(data['parent'])
        self.assertEqual(data['current']['id'], 'test-roadmap')

    def test_json_structure_matches_spec(self):
        """JSON structure matches specification."""
        toc = self.gen.generate_roadmap_toc(str(self.roadmap_yaml_path))

        output_path = self.roadmap_root / "table_of_contents.json"
        self.gen.save_toc(toc, str(output_path))

        with open(output_path, 'r') as f:
            data = json.load(f)

        # Required fields
        self.assertIn('level', data)
        self.assertIn('parent', data)
        self.assertIn('current', data)
        self.assertIn('children', data)
        self.assertIn('metadata', data)

        # Current object structure
        current = data['current']
        self.assertIn('id', current)
        self.assertIn('name', current)
        self.assertIn('files', current)

        # Files structure
        files = current['files']
        self.assertIn('yaml', files)
        self.assertIn('markdown', files)

        # Children structure
        children = data['children']
        self.assertIsInstance(children, list)

        if children:
            child = children[0]
            self.assertIn('type', child)
            self.assertIn('id', child)
            self.assertIn('name', child)
            self.assertIn('path', child)
            self.assertIn('status', child)

    def test_metadata_excludes_none_values(self):
        """Metadata excludes None values from JSON."""
        track_dir = self.roadmap_root / "track-1"
        track_dir.mkdir(parents=True)

        track_yaml = track_dir / "track-1.yaml"
        track_data = {
            'track': {
                'id': 'track-1',
                'name': 'Track One',
                'roadmap_id': 'test-roadmap',
                'progress': {
                    'tasks_total': 5,
                    'tasks_completed': 3
                    # No sprints data
                }
            }
        }

        with open(track_yaml, 'w') as f:
            yaml.dump(track_data, f)

        toc = self.gen.generate_track_toc('track-1')

        output_path = track_dir / "table_of_contents.json"
        self.gen.save_toc(toc, str(output_path))

        with open(output_path, 'r') as f:
            data = json.load(f)

        metadata = data['metadata']

        # Should have tasks data
        self.assertIn('tasks_total', metadata)
        self.assertIn('tasks_completed', metadata)

        # Should NOT have tracks data (track level doesn't track tracks)
        self.assertNotIn('tracks_total', metadata)
        self.assertNotIn('tracks_completed', metadata)


class TestPerformance(unittest.TestCase):
    """Test TOC generation performance."""

    def setUp(self):
        """Create temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.roadmap_root = Path(self.temp_dir) / ".vibey" / "roadmap"
        self.roadmap_root.mkdir(parents=True)
        self.gen = TOCGenerator(str(self.roadmap_root))

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_roadmap_toc_fast_generation(self):
        """Roadmap TOC generates in <100ms."""
        # Create roadmap with many tracks
        roadmap_yaml_path = Path(self.temp_dir) / ".vibey" / "roadmap.yaml"
        tracks = [
            {'id': f'track-{i}', 'name': f'Track {i}'}
            for i in range(20)
        ]

        roadmap_data = {
            'roadmap': {
                'id': 'test-roadmap',
                'name': 'Test Roadmap',
                'tracks': tracks,
                'progress': {
                    'tracks_total': 20,
                    'tracks_completed': 0
                }
            }
        }

        with open(roadmap_yaml_path, 'w') as f:
            yaml.dump(roadmap_data, f)

        # Time generation
        start = time.time()
        toc = self.gen.generate_roadmap_toc(str(roadmap_yaml_path))
        elapsed = time.time() - start

        self.assertLess(elapsed, 0.1, f"TOC generation took {elapsed:.3f}s (should be <100ms)")
        self.assertEqual(len(toc.children), 20)

    def test_track_toc_fast_generation(self):
        """Track TOC generates in <100ms."""
        # Create track with many sprints
        track_dir = self.roadmap_root / "track-1"
        track_dir.mkdir(parents=True)

        track_yaml = track_dir / "track-1.yaml"
        track_data = {
            'track': {
                'id': 'track-1',
                'name': 'Track One',
                'roadmap_id': 'test-roadmap',
                'progress': {
                    'sprints_total': 10,
                    'tasks_total': 50
                }
            }
        }

        with open(track_yaml, 'w') as f:
            yaml.dump(track_data, f)

        # Create multiple sprint directories
        for i in range(10):
            sprint_dir = track_dir / f"sprint-{i}"
            sprint_dir.mkdir()

            sprint_yaml = sprint_dir / f"sprint-{i}.yaml"
            sprint_data = {
                'sprint': {
                    'id': f'sprint-{i}',
                    'name': f'Sprint {i}',
                    'track_id': 'track-1',
                    'status': 'not_started'
                }
            }

            with open(sprint_yaml, 'w') as f:
                yaml.dump(sprint_data, f)

        # Time generation
        start = time.time()
        toc = self.gen.generate_track_toc('track-1')
        elapsed = time.time() - start

        self.assertLess(elapsed, 0.1, f"TOC generation took {elapsed:.3f}s (should be <100ms)")
        self.assertEqual(len(toc.children), 10)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""

    def setUp(self):
        """Create temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.roadmap_root = Path(self.temp_dir) / ".vibey" / "roadmap"
        self.roadmap_root.mkdir(parents=True)

        # Create roadmap.yaml
        self.roadmap_yaml_path = Path(self.temp_dir) / ".vibey" / "roadmap.yaml"
        roadmap_data = {
            'roadmap': {
                'id': 'test-roadmap',
                'name': 'Test Roadmap',
                'tracks': [],
                'progress': {}
            }
        }

        with open(self.roadmap_yaml_path, 'w') as f:
            yaml.dump(roadmap_data, f)

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_generate_roadmap_toc_convenience(self):
        """Convenience function generates and saves TOC."""
        # Use direct instantiation instead of patching
        gen = TOCGenerator(str(self.roadmap_root))
        output_path = self.roadmap_root / "table_of_contents.json"

        toc = gen.generate_and_save_roadmap_toc(str(self.roadmap_yaml_path), str(output_path))

        self.assertEqual(toc.level, 'roadmap')
        self.assertTrue(output_path.exists())


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def setUp(self):
        """Create temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.roadmap_root = Path(self.temp_dir) / ".vibey" / "roadmap"
        self.roadmap_root.mkdir(parents=True)
        self.gen = TOCGenerator(str(self.roadmap_root))

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_roadmap_with_no_tracks(self):
        """Roadmap with no tracks generates valid TOC."""
        roadmap_yaml_path = Path(self.temp_dir) / ".vibey" / "roadmap.yaml"
        roadmap_data = {
            'roadmap': {
                'id': 'empty-roadmap',
                'name': 'Empty Roadmap',
                'tracks': [],
                'progress': {
                    'tracks_total': 0,
                    'tracks_completed': 0
                }
            }
        }

        with open(roadmap_yaml_path, 'w') as f:
            yaml.dump(roadmap_data, f)

        toc = self.gen.generate_roadmap_toc(str(roadmap_yaml_path))

        self.assertEqual(len(toc.children), 0)
        self.assertEqual(toc.metadata.tracks_total, 0)

    def test_track_with_no_sprints(self):
        """Track with no sprints generates valid TOC."""
        track_dir = self.roadmap_root / "track-1"
        track_dir.mkdir(parents=True)

        track_yaml = track_dir / "track-1.yaml"
        track_data = {
            'track': {
                'id': 'track-1',
                'name': 'Empty Track',
                'roadmap_id': 'test-roadmap',
                'progress': {
                    'sprints_total': 0
                }
            }
        }

        with open(track_yaml, 'w') as f:
            yaml.dump(track_data, f)

        toc = self.gen.generate_track_toc('track-1')

        self.assertEqual(len(toc.children), 0)
        self.assertEqual(toc.metadata.sprints_total, 0)

    def test_sprint_with_no_tasks(self):
        """Sprint with no tasks generates valid TOC."""
        track_dir = self.roadmap_root / "track-1"
        track_dir.mkdir(parents=True)

        sprint_dir = track_dir / "sprint-1"
        sprint_dir.mkdir()

        sprint_yaml = sprint_dir / "sprint-1.yaml"
        sprint_data = {
            'sprint': {
                'id': 'sprint-1',
                'name': 'Empty Sprint',
                'track_id': 'track-1',
                'tasks': [],
                'progress': {
                    'tasks_total': 0
                }
            }
        }

        with open(sprint_yaml, 'w') as f:
            yaml.dump(sprint_data, f)

        toc = self.gen.generate_sprint_toc('track-1', 'sprint-1')

        self.assertEqual(len(toc.children), 0)
        self.assertEqual(toc.metadata.tasks_total, 0)


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
