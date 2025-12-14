"""
Integration tests for standard templates.

Tests the complete template workflow:
- Listing templates
- Loading templates
- Adding standards from templates
- Template overrides (custom ID, enforcement)
"""

import pytest
from pathlib import Path
from datetime import datetime, timezone
from argparse import Namespace

from vibey.roadmap.models import (
    Standard,
    StandardType,
    EnforcementMode,
    Roadmap,
    Track,
    Sprint,
    Status,
    Priority,
    VersionStrategy,
    VersionBumpTrigger,
    Progress,
    TrackSummary,
    Metadata,
    TrackProgress,
    SprintSummary,
    TrackMetadata,
    SprintProgress,
    SprintMetadata,
)
from vibey.roadmap.serialization import (
    save_roadmap,
    save_track,
    save_sprint,
    load_roadmap,
    load_track,
)
from vibey.roadmap.standards.templates import (
    list_templates,
    load_template,
    get_template_info,
)
from vibey.cli.roadmap_commands.list_templates import handle_list_templates
from vibey.cli.roadmap_commands.add_from_template import handle_add_from_template


@pytest.fixture
def test_roadmap(tmp_path):
    """Create a minimal test roadmap."""
    vibey_dir = tmp_path / ".vibey"
    vibey_dir.mkdir(parents=True)
    roadmap_dir = vibey_dir / "roadmap"
    roadmap_dir.mkdir(parents=True)

    now = datetime.now(timezone.utc)

    roadmap = Roadmap(
        id="test-roadmap",
        name="Test Roadmap",
        version="1.0.0",
        version_strategy=VersionStrategy(
            major_on=VersionBumpTrigger.ROADMAP_MILESTONE,
            minor_on=VersionBumpTrigger.TRACK_COMPLETION,
            patch_on=VersionBumpTrigger.SPRINT_PRODUCTION_READY,
        ),
        status=Status.IN_PROGRESS,
        blocked=False,
        created=now,
        started=now,
        progress=Progress(
            tracks_total=1,
            tracks_completed=0,
            sprints_total=1,
            sprints_completed=0,
            tasks_total=0,
            tasks_completed=0,
            completion_percent=0,
        ),
        tracks=[
            TrackSummary(
                id="backend",
                name="Backend Track",
                status=Status.IN_PROGRESS,
                priority=Priority.HIGH,
            )
        ],
        activity_log=[],
        metadata=Metadata(
            created_by="test",
            framework_version="1.3.0",
            schema_version="2.1",
            last_updated=now,
        ),
        standards=[],
    )

    save_roadmap(roadmap, roadmap_dir / "roadmap.yaml")

    # Create track
    track = Track(
        id="backend",
        name="Backend Track",
        roadmap_id="test-roadmap",
        status=Status.IN_PROGRESS,
        blocked=False,
        priority=Priority.HIGH,
        created=now,
        started=now,
        progress=TrackProgress(
            sprints_total=1,
            sprints_completed=0,
            tasks_total=0,
            tasks_completed=0,
            completion_percent=0,
        ),
        sprints=[
            SprintSummary(
                id="backend-1",
                name="Sprint 1",
                status=Status.IN_PROGRESS,
            )
        ],
        dependencies=[],
        blocks=[],
        blocked_by=[],
        depends_on=[],
        depended_on_by=[],
        quality_gates=[],
        assigned_agents=[],
        metadata=TrackMetadata(
            created_by="test",
            last_updated=now,
        ),
        standards=[],
    )

    track_dir = roadmap_dir / "backend"
    track_dir.mkdir()
    save_track(track, track_dir / "track.yaml")

    # Create sprint
    sprint = Sprint(
        id="backend-1",
        name="Sprint 1",
        track_id="backend",
        roadmap_id="test-roadmap",
        status=Status.IN_PROGRESS,
        blocked=False,
        created=now,
        started=now,
        progress=SprintProgress(
            development_tasks_total=0,
            development_tasks_completed=0,
            completion_gate_tasks_total=0,
            completion_gate_tasks_completed=0,
            production_gate_tasks_total=0,
            production_gate_tasks_completed=0,
            tasks_total=0,
            tasks_completed=0,
            completion_percent=0,
        ),
        tasks=[],
        development_gates=[],
        blocks=[],
        blocked_by=[],
        depends_on=[],
        depended_on_by=[],
        metadata=SprintMetadata(
            last_updated=now,
        ),
        standards=[],
    )

    sprint_dir = track_dir / "backend-1"
    sprint_dir.mkdir()
    save_sprint(sprint, sprint_dir / "sprint.yaml")

    return tmp_path


class TestTemplateLibrary:
    """Test template library functions."""

    def test_list_templates_returns_all_templates(self):
        """list_templates should return all available templates."""
        templates = list_templates()

        # Should have at least 5 templates
        assert len(templates) >= 5

        # Check for expected templates
        template_ids = [t['id'] for t in templates]
        assert 'commit-required' in template_ids
        assert 'doc-review-required' in template_ids
        assert 'test-coverage-required' in template_ids
        assert 'multi-platform-testing' in template_ids
        assert 'security-review' in template_ids

    def test_list_templates_includes_metadata(self):
        """list_templates should include template metadata."""
        templates = list_templates()

        for template in templates:
            assert 'id' in template
            assert 'name' in template
            assert 'description' in template
            assert 'type' in template
            assert 'enforcement' in template

    def test_load_template_returns_standard(self):
        """load_template should return a Standard object."""
        standard = load_template('commit-required')

        assert standard is not None
        assert isinstance(standard, Standard)
        assert standard.id == 'commit-required'
        assert standard.type == StandardType.COMMIT_CHECK
        assert standard.enforcement == EnforcementMode.BLOCKING

    def test_load_template_with_custom_id(self):
        """load_template should allow custom standard ID."""
        standard = load_template('commit-required', id='my-custom-commit-check')

        assert standard is not None
        assert standard.id == 'my-custom-commit-check'
        assert standard.name == 'Commit Required'  # Name unchanged

    def test_load_template_with_enforcement_override(self):
        """load_template should allow enforcement override."""
        standard = load_template('commit-required', enforcement='warning')

        assert standard is not None
        assert standard.enforcement == EnforcementMode.WARNING

    def test_load_nonexistent_template_returns_none(self):
        """load_template should return None for nonexistent template."""
        standard = load_template('nonexistent-template')

        assert standard is None

    def test_get_template_info_returns_metadata(self):
        """get_template_info should return template metadata."""
        info = get_template_info('commit-required')

        assert info is not None
        assert info['id'] == 'commit-required'
        assert info['name'] == 'Commit Required'
        assert 'use_case' in info
        assert 'examples' in info

    def test_get_template_info_nonexistent_returns_none(self):
        """get_template_info should return None for nonexistent template."""
        info = get_template_info('nonexistent-template')

        assert info is None


class TestListTemplatesCommand:
    """Test list-templates CLI command."""

    def test_list_templates_command_succeeds(self, test_roadmap, capsys):
        """list-templates command should display all templates."""
        args = Namespace(
            dir=str(test_roadmap),
            verbose=False
        )

        result = handle_list_templates(args)

        assert result == 0  # Success

        # Check output
        captured = capsys.readouterr()
        assert 'Available Standard Templates' in captured.out
        assert 'commit-required' in captured.out
        assert 'test-coverage-required' in captured.out

    def test_list_templates_command_verbose(self, test_roadmap, capsys):
        """list-templates --verbose should show detailed info."""
        args = Namespace(
            dir=str(test_roadmap),
            verbose=True
        )

        result = handle_list_templates(args)

        assert result == 0  # Success

        # Check output includes use cases
        captured = capsys.readouterr()
        assert 'Use Case:' in captured.out


class TestAddFromTemplateCommand:
    """Test add-from-template CLI command."""

    def test_add_from_template_to_roadmap(self, test_roadmap):
        """add-from-template should add standard to roadmap."""
        args = Namespace(
            template_id='commit-required',
            level='roadmap',
            target_id=None,
            custom_id=None,
            enforcement=None,
            show_info=False,
            dir=str(test_roadmap)
        )

        result = handle_add_from_template(args)

        assert result == 0  # Success

        # Verify standard was added
        roadmap_path = test_roadmap / ".vibey" / "roadmap" / "roadmap.yaml"
        roadmap = load_roadmap(roadmap_path)

        standard = roadmap.get_standard('commit-required')
        assert standard is not None
        assert standard.name == 'Commit Required'
        assert standard.type == StandardType.COMMIT_CHECK
        assert standard.enforcement == EnforcementMode.BLOCKING

    def test_add_from_template_to_track(self, test_roadmap):
        """add-from-template should add standard to track."""
        from vibey.cli.roadmap_lib.filesystem import FileSystemManager

        args = Namespace(
            template_id='doc-review-required',
            level='track',
            target_id='backend',
            custom_id=None,
            enforcement=None,
            show_info=False,
            dir=str(test_roadmap)
        )

        result = handle_add_from_template(args)

        assert result == 0  # Success

        # Verify standard was added
        fs = FileSystemManager(test_roadmap)
        track_path = fs.get_track_path('backend')
        track = load_track(track_path)

        standard = track.get_standard('doc-review-required')
        assert standard is not None
        assert standard.name == 'Documentation Review Required'
        assert standard.type == StandardType.FILE_CHECK

    def test_add_from_template_with_custom_id(self, test_roadmap):
        """add-from-template should allow custom standard ID."""
        args = Namespace(
            template_id='commit-required',
            level='roadmap',
            target_id=None,
            custom_id='my-commit-check',
            enforcement=None,
            show_info=False,
            dir=str(test_roadmap)
        )

        result = handle_add_from_template(args)

        assert result == 0  # Success

        # Verify standard has custom ID
        roadmap_path = test_roadmap / ".vibey" / "roadmap" / "roadmap.yaml"
        roadmap = load_roadmap(roadmap_path)

        standard = roadmap.get_standard('my-commit-check')
        assert standard is not None
        assert standard.id == 'my-commit-check'

    def test_add_from_template_with_enforcement_override(self, test_roadmap):
        """add-from-template should allow enforcement override."""
        args = Namespace(
            template_id='commit-required',
            level='roadmap',
            target_id=None,
            custom_id=None,
            enforcement='warning',
            show_info=False,
            dir=str(test_roadmap)
        )

        result = handle_add_from_template(args)

        assert result == 0  # Success

        # Verify enforcement was overridden
        roadmap_path = test_roadmap / ".vibey" / "roadmap" / "roadmap.yaml"
        roadmap = load_roadmap(roadmap_path)

        standard = roadmap.get_standard('commit-required')
        assert standard is not None
        assert standard.enforcement == EnforcementMode.WARNING

    def test_add_from_template_duplicate_fails(self, test_roadmap):
        """add-from-template should fail if standard already exists."""
        # Add standard first time
        args = Namespace(
            template_id='commit-required',
            level='roadmap',
            target_id=None,
            custom_id=None,
            enforcement=None,
            show_info=False,
            dir=str(test_roadmap)
        )

        result1 = handle_add_from_template(args)
        assert result1 == 0  # First add succeeds

        # Try to add same standard again
        result2 = handle_add_from_template(args)
        assert result2 == 1  # Second add fails

    def test_add_from_template_nonexistent_fails(self, test_roadmap):
        """add-from-template should fail for nonexistent template."""
        args = Namespace(
            template_id='nonexistent-template',
            level='roadmap',
            target_id=None,
            custom_id=None,
            enforcement=None,
            show_info=False,
            dir=str(test_roadmap)
        )

        result = handle_add_from_template(args)

        assert result == 1  # Failure

    def test_add_from_template_show_info(self, test_roadmap, capsys):
        """add-from-template --show-info should display template info."""
        args = Namespace(
            template_id='commit-required',
            level='roadmap',
            target_id=None,
            custom_id=None,
            enforcement=None,
            show_info=True,
            dir=str(test_roadmap)
        )

        result = handle_add_from_template(args)

        assert result == 0  # Success

        # Check output
        captured = capsys.readouterr()
        assert 'Template: commit-required' in captured.out
        assert 'Commit Required' in captured.out

        # Verify standard was NOT added (info only)
        roadmap_path = test_roadmap / ".vibey" / "roadmap" / "roadmap.yaml"
        roadmap = load_roadmap(roadmap_path)
        assert roadmap.get_standard('commit-required') is None


class TestTemplateValidation:
    """Test template validation configs."""

    def test_commit_required_validation_config(self):
        """commit-required template should have correct validation config."""
        standard = load_template('commit-required')

        assert 'min_commits' in standard.validation
        assert standard.validation['min_commits'] == 1

    def test_doc_review_validation_config(self):
        """doc-review-required template should have correct validation config."""
        standard = load_template('doc-review-required')

        assert 'pattern' in standard.validation
        assert standard.validation['pattern'] == '**/*.md'
        assert 'min_files' in standard.validation
        assert standard.validation['min_files'] == 1

    def test_test_coverage_validation_config(self):
        """test-coverage-required template should have correct validation config."""
        standard = load_template('test-coverage-required')

        assert 'command' in standard.validation
        assert 'pytest' in standard.validation['command']
        assert 'threshold' in standard.validation
        assert standard.validation['threshold'] == 80

    def test_multi_platform_validation_config(self):
        """multi-platform-testing template should have correct validation config."""
        standard = load_template('multi-platform-testing')

        assert 'command' in standard.validation
        assert 'platforms' in standard.validation
        platforms = standard.validation['platforms']
        assert len(platforms) >= 1
        assert any(p['name'] == 'claude-code' for p in platforms)

    def test_security_review_validation_config(self):
        """security-review template should have correct validation config."""
        standard = load_template('security-review')

        assert 'script' in standard.validation
        assert '#!/bin/bash' in standard.validation['script']
