#!/usr/bin/env python3
"""
Test and validate the commit-to-task mapping algorithm.

This script creates a test dataset of commits with known task mappings,
runs the mapper, and validates accuracy against expected results.

Usage:
    python3 scripts/test-commit-mapper.py

Sprint: roadmap-integrity-fixes-1
Task: roadmap-integrity-fixes-1-task-001
"""

from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from vibey.operations.roadmap.commit_mapper import (
    CommitMapper, Commit, Task, TaskMatch, load_tasks_from_roadmap
)


# Test dataset: commits with expected task mappings
TEST_COMMITS = [
    # High-confidence matches
    {
        'commit': Commit(
            sha='abc123',
            message='feat: Implement roadmap-integrity-fixes-1-task-001 commit mapping algorithm',
            timestamp=datetime(2025, 11, 20, 15, 0, 0, tzinfo=timezone.utc),
            author_name='Claude',
            author_email='noreply@anthropic.com',
            files_changed=[
                'vibey/operations/roadmap/commit_mapper.py',
                'tests/test_commit_mapper.py'
            ]
        ),
        'expected_task': 'roadmap-integrity-fixes-1-task-001',
        'expected_confidence': 'high',
        'description': 'Exact task ID in message + relevant files'
    },

    # Medium-confidence matches
    {
        'commit': Commit(
            sha='def456',
            message='feat: Add YAML validation safeguards to prevent corruption',
            timestamp=datetime(2025, 11, 20, 16, 0, 0, tzinfo=timezone.utc),
            author_name='Claude',
            author_email='noreply@anthropic.com',
            files_changed=[
                'vibey/operations/roadmap/yaml_editor.py',
                'tests/test_yaml_safeguards.py'
            ]
        ),
        'expected_task': 'roadmap-integrity-fixes-1-task-003',
        'expected_confidence': 'medium',
        'description': 'Keywords match task about YAML safeguards'
    },

    {
        'commit': Commit(
            sha='ghi789',
            message='refactor: Optimize roadmap validation performance for large datasets',
            timestamp=datetime(2025, 11, 20, 17, 0, 0, tzinfo=timezone.utc),
            author_name='Claude',
            author_email='noreply@anthropic.com',
            files_changed=[
                'vibey/operations/roadmap/validate.py',
                'scripts/validate-roadmap-schema.py'
            ]
        ),
        'expected_task': 'roadmap-integrity-fixes-1-task-004',
        'expected_confidence': 'medium',
        'description': 'Keywords match validation optimization task'
    },

    # Track-level match (should match roadmap-system tasks)
    {
        'commit': Commit(
            sha='jkl012',
            message='fix: Fix roadmap loader to handle missing sprint declarations',
            timestamp=datetime(2025, 11, 15, 10, 0, 0, tzinfo=timezone.utc),
            author_name='Fred',
            author_email='fred@example.com',
            files_changed=[
                'vibey/roadmap/loader.py',
                'tests/roadmap/test_loader.py'
            ]
        ),
        'expected_task': 'roadmap-system-',  # Should match some roadmap-system task
        'expected_confidence': 'medium',
        'description': 'Roadmap system files, should match roadmap-system track'
    },

    # Testing system match
    {
        'commit': Commit(
            sha='mno345',
            message='test: Add comprehensive test suite for validation',
            timestamp=datetime(2025, 11, 10, 14, 0, 0, tzinfo=timezone.utc),
            author_name='Fred',
            author_email='fred@example.com',
            files_changed=[
                'tests/test_validation.py',
                'tests/conftest.py',
                'pytest.ini'
            ]
        ),
        'expected_task': 'testing-system-',  # Should match testing-system tasks
        'expected_confidence': 'medium',
        'description': 'Test files, should match testing-system track'
    },

    # Documentation match
    {
        'commit': Commit(
            sha='pqr678',
            message='docs: Update architecture documentation with new diagrams',
            timestamp=datetime(2025, 11, 12, 9, 0, 0, tzinfo=timezone.utc),
            author_name='Fred',
            author_email='fred@example.com',
            files_changed=[
                'docs/architecture/OVERVIEW.md',
                'docs/diagrams/system-architecture.svg',
                'README.md'
            ]
        ),
        'expected_task': 'documentation-system-',  # Should match documentation-system
        'expected_confidence': 'medium',
        'description': 'Documentation files, should match documentation-system'
    },

    # Low-confidence: vague message, generic files
    {
        'commit': Commit(
            sha='stu901',
            message='fix: Fix bugs',
            timestamp=datetime(2025, 11, 18, 11, 0, 0, tzinfo=timezone.utc),
            author_name='Fred',
            author_email='fred@example.com',
            files_changed=['vibey/utils.py']
        ),
        'expected_task': None,  # Could match anything
        'expected_confidence': 'low',
        'description': 'Vague message, should have low confidence for any match'
    },

    # Merge commit (multiple files)
    {
        'commit': Commit(
            sha='vwx234',
            message='Merge branch \"feature/roadmap-validation\" into main\n\nBring in validation improvements',
            timestamp=datetime(2025, 11, 19, 16, 30, 0, tzinfo=timezone.utc),
            author_name='Fred',
            author_email='fred@example.com',
            files_changed=[
                'vibey/operations/roadmap/validate.py',
                'scripts/validate-roadmap-schema.py',
                'tests/test_validation.py',
                'docs/VALIDATION.md'
            ]
        ),
        'expected_task': 'roadmap-integrity-fixes-1-task-004',  # Validation task
        'expected_confidence': 'medium',
        'description': 'Merge commit with validation-related files'
    },

    # Commit with no message (edge case)
    {
        'commit': Commit(
            sha='yza567',
            message='',
            timestamp=datetime(2025, 11, 20, 12, 0, 0, tzinfo=timezone.utc),
            author_name='Fred',
            author_email='fred@example.com',
            files_changed=['vibey/operations/roadmap/commit_mapper.py']
        ),
        'expected_task': 'roadmap-integrity-fixes-1-task-001',
        'expected_confidence': 'medium',
        'description': 'No message, should still match based on file path'
    },

    # Timestamp edge case: commit before task created
    {
        'commit': Commit(
            sha='bcd890',
            message='feat: Early work on backup automation',
            timestamp=datetime(2025, 11, 1, 10, 0, 0, tzinfo=timezone.utc),  # Way before task
            author_name='Fred',
            author_email='fred@example.com',
            files_changed=['scripts/backup-roadmap.sh']
        ),
        'expected_task': 'roadmap-integrity-fixes-1-task-002',
        'expected_confidence': 'low',  # Temporal score will be low
        'description': 'Commit before task created, should have low temporal score'
    }
]


def run_tests():
    """Run commit mapper tests and report results."""

    print("=" * 80)
    print("Commit-to-Task Mapping Algorithm - Test Suite")
    print("=" * 80)
    print()

    # Load real tasks from roadmap
    roadmap_path = Path('.vibey/roadmap')
    if not roadmap_path.exists():
        print(f"❌ Roadmap path not found: {roadmap_path}")
        print("   Run this script from repository root")
        return False

    print(f"Loading tasks from {roadmap_path}...")
    tasks = load_tasks_from_roadmap(roadmap_path)
    print(f"✅ Loaded {len(tasks)} tasks")
    print()

    # Initialize mapper
    mapper = CommitMapper(tasks)

    # Run tests
    results = {
        'total': len(TEST_COMMITS),
        'passed': 0,
        'failed': 0,
        'high_confidence_correct': 0,
        'medium_confidence_correct': 0,
        'low_confidence_correct': 0,
        'details': []
    }

    print("Running test commits...")
    print("=" * 80)
    print()

    for i, test_case in enumerate(TEST_COMMITS, 1):
        commit = test_case['commit']
        expected_task = test_case['expected_task']
        expected_confidence = test_case['expected_confidence']
        description = test_case['description']

        print(f"Test {i}/{len(TEST_COMMITS)}: {description}")
        print(f"  Commit: {commit.sha} - {commit.message[:60]}")

        # Map commit
        matches = mapper.map_commit_to_tasks(commit, top_n=3)

        if matches:
            top_match = matches[0]
            confidence_level = mapper.get_confidence_level(top_match.confidence)

            print(f"  Top match: {top_match.task_id} (confidence: {top_match.confidence:.1f}% - {confidence_level})")
            print(f"    - Keywords: {top_match.keyword_score:.1f}%")
            print(f"    - File paths: {top_match.file_path_score:.1f}%")
            print(f"    - Temporal: {top_match.temporal_score:.1f}%")
            print(f"    - Author: {top_match.author_score:.1f}%")

            # Check if match is correct
            if expected_task:
                if expected_task.endswith('-'):
                    # Partial match (track level)
                    match_correct = top_match.task_id.startswith(expected_task)
                else:
                    # Exact match
                    match_correct = top_match.task_id == expected_task

                confidence_correct = confidence_level == expected_confidence

                if match_correct and confidence_correct:
                    print(f"  ✅ PASS: Correct task and confidence level")
                    results['passed'] += 1

                    # Track confidence-level accuracy
                    if confidence_level == 'high':
                        results['high_confidence_correct'] += 1
                    elif confidence_level == 'medium':
                        results['medium_confidence_correct'] += 1
                    elif confidence_level == 'low':
                        results['low_confidence_correct'] += 1
                elif match_correct:
                    print(f"  ⚠️  PARTIAL: Correct task, wrong confidence (expected {expected_confidence})")
                    results['passed'] += 0.5
                    results['failed'] += 0.5
                else:
                    print(f"  ❌ FAIL: Wrong task (expected {expected_task})")
                    results['failed'] += 1
            else:
                # No expected task - just check confidence level
                if confidence_level == expected_confidence:
                    print(f"  ✅ PASS: Confidence level correct")
                    results['passed'] += 1
                else:
                    print(f"  ⚠️  PARTIAL: Expected {expected_confidence} confidence")
                    results['passed'] += 0.5
                    results['failed'] += 0.5
        else:
            print(f"  ❌ FAIL: No matches found")
            results['failed'] += 1

        print()

    # Print summary
    print("=" * 80)
    print("Test Results Summary")
    print("=" * 80)
    print()
    print(f"Total tests: {results['total']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Pass rate: {results['passed'] / results['total'] * 100:.1f}%")
    print()

    high_total = sum(1 for t in TEST_COMMITS if t['expected_confidence'] == 'high')
    medium_total = sum(1 for t in TEST_COMMITS if t['expected_confidence'] == 'medium')
    low_total = sum(1 for t in TEST_COMMITS if t['expected_confidence'] == 'low')

    if high_total > 0:
        print(f"High-confidence accuracy: {results['high_confidence_correct']}/{high_total} "
              f"({results['high_confidence_correct'] / high_total * 100:.1f}%)")
    if medium_total > 0:
        print(f"Medium-confidence accuracy: {results['medium_confidence_correct']}/{medium_total} "
              f"({results['medium_confidence_correct'] / medium_total * 100:.1f}%)")
    if low_total > 0:
        print(f"Low-confidence accuracy: {results['low_confidence_correct']}/{low_total} "
              f"({results['low_confidence_correct'] / low_total * 100:.1f}%)")
    print()

    # Acceptance criteria
    pass_rate = results['passed'] / results['total'] * 100
    target_pass_rate = 85.0

    print("Acceptance Criteria:")
    if pass_rate >= target_pass_rate:
        print(f"  ✅ Pass rate {pass_rate:.1f}% >= {target_pass_rate}% target")
        return True
    else:
        print(f"  ❌ Pass rate {pass_rate:.1f}% < {target_pass_rate}% target")
        return False


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
