#!/usr/bin/env python3
"""
Validate Vibey asset frontmatter.

Ensures all agents, workflows, and handoffs have valid YAML frontmatter
that the MCP server can parse for dynamic tool discovery.

Usage:
    python scripts/validate-frontmatter.py --all
    python scripts/validate-frontmatter.py --type agents
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
import yaml


# Required fields by asset type
REQUIRED_FIELDS = {
    'agents': ['id', 'name', 'type', 'version'],
    'workflows': ['id', 'name', 'type', 'version'],
    'handoffs': ['id', 'name', 'version'],
}

# Valid type values
VALID_AGENT_TYPES = ['core', 'planning', 'development', 'quality', 'documentation', 'architecture']
VALID_WORKFLOW_TYPES = ['planning', 'development', 'quality', 'documentation', 'deployment']
VALID_PRIORITIES = ['high', 'medium', 'low']
VALID_INPUT_TYPES = ['string', 'integer', 'boolean', 'array', 'object']


def extract_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Extract YAML frontmatter from markdown content."""
    if not content.strip().startswith('---'):
        return None, content

    match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if not match:
        return None, content

    try:
        frontmatter = yaml.safe_load(match.group(1))
        body = content[match.end():]
        return frontmatter, body
    except yaml.YAMLError as e:
        return {'_error': str(e)}, content


def validate_agent(frontmatter: Dict[str, Any], filepath: Path) -> List[str]:
    """Validate agent frontmatter."""
    errors = []

    # Check required fields
    for field in REQUIRED_FIELDS['agents']:
        if field not in frontmatter:
            errors.append(f"Missing required field: {field}")

    # Validate type
    if 'type' in frontmatter and frontmatter['type'] not in VALID_AGENT_TYPES:
        errors.append(f"Invalid agent type: {frontmatter['type']} (valid: {VALID_AGENT_TYPES})")

    # Validate triggers
    if 'triggers' in frontmatter:
        triggers = frontmatter['triggers']
        if 'priority' in triggers and triggers['priority'] not in VALID_PRIORITIES:
            errors.append(f"Invalid priority: {triggers['priority']} (valid: {VALID_PRIORITIES})")

    # Validate inputs
    if 'inputs' in frontmatter:
        for i, inp in enumerate(frontmatter['inputs']):
            if 'name' not in inp:
                errors.append(f"Input {i} missing 'name' field")
            if 'type' in inp and inp['type'] not in VALID_INPUT_TYPES:
                errors.append(f"Input {inp.get('name', i)} has invalid type: {inp['type']}")

    # Validate outputs
    if 'outputs' in frontmatter:
        for i, out in enumerate(frontmatter['outputs']):
            if 'name' not in out:
                errors.append(f"Output {i} missing 'name' field")

    return errors


def validate_workflow(frontmatter: Dict[str, Any], filepath: Path) -> List[str]:
    """Validate workflow frontmatter."""
    errors = []

    # Check required fields
    for field in REQUIRED_FIELDS['workflows']:
        if field not in frontmatter:
            errors.append(f"Missing required field: {field}")

    # Validate type
    if 'type' in frontmatter and frontmatter['type'] not in VALID_WORKFLOW_TYPES:
        errors.append(f"Invalid workflow type: {frontmatter['type']} (valid: {VALID_WORKFLOW_TYPES})")

    # Validate steps
    if 'steps' in frontmatter:
        for i, step in enumerate(frontmatter['steps']):
            if 'order' not in step:
                errors.append(f"Step {i} missing 'order' field")
            if 'name' not in step:
                errors.append(f"Step {i} missing 'name' field")

    # Validate inputs
    if 'inputs' in frontmatter:
        for i, inp in enumerate(frontmatter['inputs']):
            if 'name' not in inp:
                errors.append(f"Input {i} missing 'name' field")

    return errors


def validate_handoff(frontmatter: Dict[str, Any], filepath: Path) -> List[str]:
    """Validate handoff template frontmatter."""
    errors = []

    # Check required fields
    for field in REQUIRED_FIELDS['handoffs']:
        if field not in frontmatter:
            errors.append(f"Missing required field: {field}")

    # Validate variables
    if 'variables' in frontmatter:
        for i, var in enumerate(frontmatter['variables']):
            if 'name' not in var:
                errors.append(f"Variable {i} missing 'name' field")

    return errors


def validate_file(filepath: Path, asset_type: str) -> Tuple[bool, List[str]]:
    """Validate a single file's frontmatter."""
    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        return False, [f"Cannot read file: {e}"]

    frontmatter, _ = extract_frontmatter(content)

    if frontmatter is None:
        return False, ["No frontmatter found"]

    if '_error' in frontmatter:
        return False, [f"YAML parse error: {frontmatter['_error']}"]

    # Validate based on type
    if asset_type == 'agents':
        errors = validate_agent(frontmatter, filepath)
    elif asset_type == 'workflows':
        errors = validate_workflow(frontmatter, filepath)
    elif asset_type == 'handoffs':
        errors = validate_handoff(frontmatter, filepath)
    else:
        errors = [f"Unknown asset type: {asset_type}"]

    return len(errors) == 0, errors


def validate_assets(root_dir: Path, asset_type: str) -> Tuple[int, int, List[Tuple[Path, List[str]]]]:
    """Validate all assets of a given type."""
    if asset_type == 'agents':
        search_dir = root_dir / 'framework' / 'agents'
    elif asset_type == 'workflows':
        search_dir = root_dir / 'framework' / 'workflows'
    elif asset_type == 'handoffs':
        search_dir = root_dir / 'framework' / 'templates' / 'handoffs'
    else:
        print(f"Unknown asset type: {asset_type}")
        return 0, 0, []

    if not search_dir.exists():
        print(f"Directory not found: {search_dir}")
        return 0, 0, []

    valid_count = 0
    invalid_count = 0
    all_errors = []

    for filepath in search_dir.rglob('*.md'):
        # Skip README files
        if filepath.name.lower() == 'readme.md':
            continue

        is_valid, errors = validate_file(filepath, asset_type)

        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1
            all_errors.append((filepath, errors))

    return valid_count, invalid_count, all_errors


def main():
    parser = argparse.ArgumentParser(
        description='Validate Vibey asset frontmatter'
    )
    parser.add_argument(
        '--type',
        choices=['agents', 'workflows', 'handoffs'],
        help='Type of assets to validate'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Validate all asset types'
    )
    parser.add_argument(
        '--root',
        type=Path,
        default=Path.cwd(),
        help='Root directory of Vibey repository'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Show details for valid files too'
    )

    args = parser.parse_args()

    if not args.type and not args.all:
        parser.error('Either --type or --all must be specified')

    total_valid = 0
    total_invalid = 0
    all_errors = []

    asset_types = ['agents', 'workflows', 'handoffs'] if args.all else [args.type]

    for asset_type in asset_types:
        print(f"\nValidating {asset_type}...")
        valid, invalid, errors = validate_assets(args.root, asset_type)
        total_valid += valid
        total_invalid += invalid
        all_errors.extend(errors)

        print(f"  ✅ {valid} valid")
        if invalid > 0:
            print(f"  ❌ {invalid} invalid")

    # Show errors
    if all_errors:
        print(f"\n{'='*60}")
        print("VALIDATION ERRORS:")
        print('='*60)
        for filepath, errors in all_errors:
            print(f"\n{filepath}:")
            for error in errors:
                print(f"  - {error}")

    # Summary
    print(f"\n{'='*60}")
    print(f"TOTAL: {total_valid} valid, {total_invalid} invalid")
    print('='*60)

    return 0 if total_invalid == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
