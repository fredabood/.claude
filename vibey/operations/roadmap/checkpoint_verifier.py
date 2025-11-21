"""
Checkpoint Verification Module

Provides functions for verifying checkpoint integrity, YAML syntax validation,
and roadmap command testing to ensure checkpoints are valid and restorable.

Author: Vibey Framework
Created: 2025-11-20
Sprint: roadmap-integrity-fixes-1
Task: roadmap-integrity-fixes-1-task-002
"""

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import yaml


class CheckpointVerificationError(Exception):
    """Raised when checkpoint verification fails."""
    pass


def calculate_file_checksum(file_path: Path) -> str:
    """
    Calculate SHA-256 checksum of a file.

    Args:
        file_path: Path to file

    Returns:
        Hex string of checksum
    """
    sha256 = hashlib.sha256()

    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)

    return sha256.hexdigest()


def generate_manifest(directory: Path, output_path: Path) -> Dict:
    """
    Generate manifest file with checksums for all files in directory.

    Args:
        directory: Directory to create manifest for
        output_path: Where to write manifest.json

    Returns:
        Dictionary containing manifest data
    """
    manifest = {
        'created': datetime.now(timezone.utc).isoformat(),
        'directory': str(directory.resolve()),
        'files': {},
        'total_files': 0,
        'total_size': 0
    }

    # Find all files
    for file_path in directory.rglob('*'):
        if file_path.is_file() and file_path != output_path:
            try:
                # Calculate checksum
                checksum = calculate_file_checksum(file_path)

                # Get relative path
                rel_path = file_path.relative_to(directory)

                # Store metadata
                manifest['files'][str(rel_path)] = {
                    'checksum': checksum,
                    'size': file_path.stat().st_size,
                    'modified': file_path.stat().st_mtime
                }

                manifest['total_files'] += 1
                manifest['total_size'] += file_path.stat().st_size
            except Exception as e:
                print(f"Warning: Could not process {file_path}: {e}", file=sys.stderr)

    # Write manifest
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    return manifest


def verify_checkpoint_integrity(checkpoint_path: Path) -> Tuple[bool, Dict]:
    """
    Verify all files in checkpoint match checksums in manifest.

    Args:
        checkpoint_path: Path to checkpoint directory

    Returns:
        Tuple of (success: bool, report: dict)
    """
    manifest_path = checkpoint_path / 'manifest.json'

    if not manifest_path.exists():
        return False, {
            'error': 'manifest_missing',
            'message': f'Manifest file not found: {manifest_path}'
        }

    # Load manifest
    try:
        with open(manifest_path) as f:
            manifest = json.load(f)
    except Exception as e:
        return False, {
            'error': 'manifest_invalid',
            'message': f'Could not load manifest: {e}'
        }

    # Verify each file
    report = {
        'checkpoint': str(checkpoint_path),
        'verified_at': datetime.now(timezone.utc).isoformat(),
        'total_files': len(manifest['files']),
        'verified_files': 0,
        'failed_files': 0,
        'missing_files': 0,
        'failures': []
    }

    for rel_path, file_info in manifest['files'].items():
        file_path = checkpoint_path / rel_path

        # Check file exists
        if not file_path.exists():
            report['missing_files'] += 1
            report['failures'].append({
                'file': rel_path,
                'error': 'missing',
                'expected_checksum': file_info['checksum']
            })
            continue

        # Verify checksum
        try:
            actual_checksum = calculate_file_checksum(file_path)
            expected_checksum = file_info['checksum']

            if actual_checksum == expected_checksum:
                report['verified_files'] += 1
            else:
                report['failed_files'] += 1
                report['failures'].append({
                    'file': rel_path,
                    'error': 'checksum_mismatch',
                    'expected': expected_checksum,
                    'actual': actual_checksum
                })
        except Exception as e:
            report['failed_files'] += 1
            report['failures'].append({
                'file': rel_path,
                'error': 'verification_failed',
                'message': str(e)
            })

    success = (report['failed_files'] == 0 and report['missing_files'] == 0)
    return success, report


def verify_yaml_syntax(directory: Path) -> Tuple[bool, Dict]:
    """
    Verify all YAML files in directory parse correctly.

    Args:
        directory: Directory to check

    Returns:
        Tuple of (success: bool, report: dict)
    """
    report = {
        'directory': str(directory),
        'verified_at': datetime.now(timezone.utc).isoformat(),
        'total_yaml_files': 0,
        'valid_files': 0,
        'invalid_files': 0,
        'errors': []
    }

    # Find all YAML files
    for yaml_file in directory.rglob('*.yaml'):
        if yaml_file.is_file():
            report['total_yaml_files'] += 1

            try:
                with open(yaml_file) as f:
                    yaml.safe_load(f)
                report['valid_files'] += 1
            except Exception as e:
                report['invalid_files'] += 1
                report['errors'].append({
                    'file': str(yaml_file.relative_to(directory)),
                    'error': str(e)
                })

    success = (report['invalid_files'] == 0)
    return success, report


def verify_roadmap_commands(python_cmd: str = 'python3') -> Tuple[bool, Dict]:
    """
    Test that vibey roadmap commands work correctly.

    Args:
        python_cmd: Python command to use

    Returns:
        Tuple of (success: bool, report: dict)
    """
    report = {
        'tested_at': datetime.now(timezone.utc).isoformat(),
        'commands_tested': 0,
        'commands_passed': 0,
        'commands_failed': 0,
        'results': []
    }

    # Test commands
    test_commands = [
        ['vibey/cli/main.py', 'roadmap', 'status'],
        # Add more test commands as needed
    ]

    for cmd in test_commands:
        report['commands_tested'] += 1

        try:
            result = subprocess.run(
                [python_cmd] + cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                report['commands_passed'] += 1
                report['results'].append({
                    'command': ' '.join(cmd),
                    'status': 'passed',
                    'exit_code': 0
                })
            else:
                report['commands_failed'] += 1
                report['results'].append({
                    'command': ' '.join(cmd),
                    'status': 'failed',
                    'exit_code': result.returncode,
                    'stderr': result.stderr[:500]  # Limit error output
                })
        except subprocess.TimeoutExpired:
            report['commands_failed'] += 1
            report['results'].append({
                'command': ' '.join(cmd),
                'status': 'timeout',
                'error': 'Command timed out after 30 seconds'
            })
        except Exception as e:
            report['commands_failed'] += 1
            report['results'].append({
                'command': ' '.join(cmd),
                'status': 'error',
                'error': str(e)
            })

    success = (report['commands_failed'] == 0)
    return success, report


def generate_checkpoint_report(checkpoint_path: Path) -> Dict:
    """
    Generate detailed report about a checkpoint.

    Args:
        checkpoint_path: Path to checkpoint directory

    Returns:
        Dictionary containing checkpoint report
    """
    report = {
        'checkpoint_path': str(checkpoint_path),
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'exists': checkpoint_path.exists()
    }

    if not checkpoint_path.exists():
        report['error'] = 'Checkpoint directory does not exist'
        return report

    # Get checkpoint info
    manifest_path = checkpoint_path / 'manifest.json'
    if manifest_path.exists():
        try:
            with open(manifest_path) as f:
                manifest = json.load(f)

            report['created'] = manifest.get('created')
            report['total_files'] = manifest.get('total_files', 0)
            report['total_size_bytes'] = manifest.get('total_size', 0)
            report['total_size_mb'] = round(manifest.get('total_size', 0) / (1024 * 1024), 2)
        except Exception as e:
            report['manifest_error'] = str(e)
    else:
        report['manifest_exists'] = False

    # Run verifications
    integrity_ok, integrity_report = verify_checkpoint_integrity(checkpoint_path)
    report['integrity_check'] = {
        'passed': integrity_ok,
        'verified_files': integrity_report.get('verified_files', 0),
        'failed_files': integrity_report.get('failed_files', 0),
        'missing_files': integrity_report.get('missing_files', 0)
    }

    # Check for .vibey/roadmap directory
    roadmap_dir = checkpoint_path / '.vibey' / 'roadmap'
    if roadmap_dir.exists():
        yaml_ok, yaml_report = verify_yaml_syntax(roadmap_dir)
        report['yaml_syntax_check'] = {
            'passed': yaml_ok,
            'valid_files': yaml_report.get('valid_files', 0),
            'invalid_files': yaml_report.get('invalid_files', 0),
            'total_files': yaml_report.get('total_yaml_files', 0)
        }

    # Overall status
    report['status'] = 'valid' if (
        report.get('integrity_check', {}).get('passed') and
        report.get('yaml_syntax_check', {}).get('passed', True)
    ) else 'invalid'

    return report


def compare_checkpoints(checkpoint1: Path, checkpoint2: Path) -> Dict:
    """
    Compare two checkpoints and report differences.

    Args:
        checkpoint1: First checkpoint path
        checkpoint2: Second checkpoint path

    Returns:
        Dictionary containing comparison report
    """
    report = {
        'checkpoint1': str(checkpoint1),
        'checkpoint2': str(checkpoint2),
        'compared_at': datetime.now(timezone.utc).isoformat()
    }

    # Load manifests
    manifest1_path = checkpoint1 / 'manifest.json'
    manifest2_path = checkpoint2 / 'manifest.json'

    if not manifest1_path.exists():
        report['error'] = f'Manifest not found for checkpoint1'
        return report

    if not manifest2_path.exists():
        report['error'] = f'Manifest not found for checkpoint2'
        return report

    try:
        with open(manifest1_path) as f:
            manifest1 = json.load(f)
        with open(manifest2_path) as f:
            manifest2 = json.load(f)
    except Exception as e:
        report['error'] = f'Could not load manifests: {e}'
        return report

    # Compare file sets
    files1 = set(manifest1.get('files', {}).keys())
    files2 = set(manifest2.get('files', {}).keys())

    report['files_only_in_checkpoint1'] = sorted(list(files1 - files2))
    report['files_only_in_checkpoint2'] = sorted(list(files2 - files1))
    report['files_in_both'] = len(files1 & files2)

    # Compare checksums for common files
    changed_files = []
    for file_path in (files1 & files2):
        checksum1 = manifest1['files'][file_path]['checksum']
        checksum2 = manifest2['files'][file_path]['checksum']

        if checksum1 != checksum2:
            changed_files.append({
                'file': file_path,
                'size1': manifest1['files'][file_path]['size'],
                'size2': manifest2['files'][file_path]['size']
            })

    report['changed_files'] = changed_files
    report['total_changes'] = (
        len(report['files_only_in_checkpoint1']) +
        len(report['files_only_in_checkpoint2']) +
        len(changed_files)
    )

    return report
