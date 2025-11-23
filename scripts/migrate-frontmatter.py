#!/usr/bin/env python3
"""
Migrate Vibey assets to include YAML frontmatter.

This script adds structured frontmatter to agent, workflow, and handoff
markdown files, enabling dynamic MCP tool discovery.

Usage:
    python scripts/migrate-frontmatter.py --type agents
    python scripts/migrate-frontmatter.py --type workflows
    python scripts/migrate-frontmatter.py --type handoffs
    python scripts/migrate-frontmatter.py --all
    python scripts/migrate-frontmatter.py --all --dry-run
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml


# Type mappings
AGENT_TYPES = {
    'core': 'core',
    'planning': 'planning',
    'development': 'development',
    'quality': 'quality',
    'documentation': 'documentation',
    'architecture': 'architecture',
}

WORKFLOW_TYPES = {
    'planning': 'planning',
    'development': 'development',
    'quality': 'quality',
    'documentation': 'documentation',
    'deployment': 'deployment',
}


def parse_agent_markdown(content: str, filepath: Path) -> Dict[str, Any]:
    """Extract metadata from agent markdown content."""
    frontmatter = {
        'id': filepath.stem,
        'name': '',
        'type': 'development',
        'version': '1.0.0',
        'triggers': {
            'keywords': [],
            'contexts': [],
            'file_patterns': [],
            'priority': 'medium',
        },
        'inputs': [],
        'outputs': [],
        'description': '',
    }

    # Extract name from first heading
    name_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if name_match:
        frontmatter['name'] = name_match.group(1).strip()

    # Extract role (description)
    role_match = re.search(r'\*\*Role:\*\*\s*(.+)$', content, re.MULTILINE)
    if role_match:
        frontmatter['description'] = role_match.group(1).strip()

    # Extract type
    type_match = re.search(r'\*\*Type:\*\*\s*(.+)$', content, re.MULTILINE)
    if type_match:
        type_str = type_match.group(1).strip().lower()
        for key in AGENT_TYPES:
            if key in type_str:
                frontmatter['type'] = key
                break

    # Extract aliases
    alias_match = re.search(r'\*\*Aliases?:\*\*\s*(.+)$', content, re.MULTILINE)
    if alias_match:
        aliases = [a.strip() for a in alias_match.group(1).split(',')]
        # Clean up parenthetical notes
        aliases = [re.sub(r'\s*\([^)]+\)', '', a).strip() for a in aliases]
        frontmatter['aliases'] = aliases

    # Extract trigger patterns
    triggers_section = re.search(
        r'\*\*Trigger Patterns:\*\*(.+?)(?=\n---|\n##|\Z)',
        content,
        re.DOTALL
    )
    if triggers_section:
        triggers_text = triggers_section.group(1)

        # Keywords
        keywords_match = re.search(
            r'\*\*Keywords:\*\*\s*(.+?)(?=\n-\s*\*\*|\Z)',
            triggers_text,
            re.DOTALL
        )
        if keywords_match:
            keywords_str = keywords_match.group(1).strip()
            keywords = [k.strip() for k in keywords_str.split(',')]
            frontmatter['triggers']['keywords'] = keywords[:20]  # Limit to 20

        # Contexts
        contexts_match = re.search(
            r'\*\*Contexts:\*\*\s*(.+?)(?=\n-\s*\*\*|\Z)',
            triggers_text,
            re.DOTALL
        )
        if contexts_match:
            contexts_str = contexts_match.group(1).strip()
            contexts = [c.strip() for c in contexts_str.split(',')]
            frontmatter['triggers']['contexts'] = contexts[:10]

        # File patterns
        patterns_match = re.search(
            r'\*\*File Patterns:\*\*\s*(.+?)(?=\n-\s*\*\*|\Z)',
            triggers_text,
            re.DOTALL
        )
        if patterns_match:
            patterns_str = patterns_match.group(1).strip()
            patterns = [p.strip() for p in patterns_str.split(',')]
            frontmatter['triggers']['file_patterns'] = patterns[:10]

        # Priority
        priority_match = re.search(
            r'\*\*Priority:\*\*\s*(\w+)',
            triggers_text
        )
        if priority_match:
            priority_str = priority_match.group(1).lower()
            if 'high' in priority_str or 'critical' in priority_str:
                frontmatter['triggers']['priority'] = 'high'
            elif 'low' in priority_str:
                frontmatter['triggers']['priority'] = 'low'
            else:
                frontmatter['triggers']['priority'] = 'medium'

    # Generate default inputs based on agent type
    frontmatter['inputs'] = [
        {
            'name': 'task',
            'type': 'string',
            'required': True,
            'description': f'Task or request for the {frontmatter["name"]}'
        },
        {
            'name': 'context',
            'type': 'string',
            'required': False,
            'description': 'Additional context about the project or codebase'
        }
    ]

    # Generate default outputs
    frontmatter['outputs'] = [
        {
            'name': 'result',
            'type': 'string',
            'description': 'Result of the agent task'
        },
        {
            'name': 'files_modified',
            'type': 'array',
            'description': 'List of files created or modified'
        }
    ]

    return frontmatter


def parse_workflow_markdown(content: str, filepath: Path) -> Dict[str, Any]:
    """Extract metadata from workflow markdown content."""
    frontmatter = {
        'id': filepath.stem,
        'name': '',
        'type': 'development',
        'version': '1.0.0',
        'duration': '1-3 days',
        'complexity': 'medium',
        'steps': [],
        'quality_gates': [],
        'inputs': [],
        'description': '',
    }

    # Extract name from first heading or Purpose
    name_match = re.search(r'^#\s+(?:Workflow:?\s*)?(.+)$', content, re.MULTILINE)
    if name_match:
        frontmatter['name'] = name_match.group(1).strip()

    # Extract purpose (description)
    purpose_match = re.search(r'\*\*Purpose:\*\*\s*(.+)$', content, re.MULTILINE)
    if purpose_match:
        frontmatter['description'] = purpose_match.group(1).strip()

    # Extract duration
    duration_match = re.search(r'\*\*Duration:\*\*\s*(.+)$', content, re.MULTILINE)
    if duration_match:
        frontmatter['duration'] = duration_match.group(1).strip()

    # Extract complexity
    complexity_match = re.search(r'\*\*Complexity:\*\*\s*(\w+)', content, re.MULTILINE)
    if complexity_match:
        frontmatter['complexity'] = complexity_match.group(1).lower()

    # Determine type from path or content
    path_str = str(filepath).lower()
    if 'planning' in path_str:
        frontmatter['type'] = 'planning'
    elif 'quality' in path_str or 'security' in path_str or 'test' in path_str:
        frontmatter['type'] = 'quality'
    elif 'doc' in path_str:
        frontmatter['type'] = 'documentation'
    elif 'deploy' in path_str or 'infrastructure' in path_str:
        frontmatter['type'] = 'deployment'
    else:
        frontmatter['type'] = 'development'

    # Extract steps from "### Step N:" pattern
    step_pattern = re.compile(
        r'###\s+Step\s+(\d+)[:\s]+(.+?)(?=\n\*\*Agent:\*\*|\n\*\*Duration:\*\*)',
        re.DOTALL
    )
    agent_pattern = re.compile(r'\*\*Agent:\*\*\s*(.+?)(?:\n|$)')
    duration_pattern = re.compile(r'\*\*Duration:\*\*\s*(.+?)(?:\n|$)')

    steps = []
    for match in re.finditer(r'###\s+Step\s+(\d+)[:\s]+(.+?)(?=###\s+Step|\n---|\Z)', content, re.DOTALL):
        step_num = int(match.group(1))
        step_content = match.group(2)
        step_name_line = step_content.split('\n')[0].strip()

        agent_match = agent_pattern.search(step_content)
        duration_match = duration_pattern.search(step_content)

        step = {
            'order': step_num,
            'name': step_name_line,
            'agent': agent_match.group(1).strip().lower().replace(' ', '-') if agent_match else 'web-developer',
            'duration': duration_match.group(1).strip() if duration_match else '0.5 days',
        }
        steps.append(step)

    if steps:
        frontmatter['steps'] = steps

    # Default inputs for workflows
    frontmatter['inputs'] = [
        {
            'name': 'feature_name',
            'type': 'string',
            'required': True,
            'description': 'Name of the feature or task'
        },
        {
            'name': 'requirements',
            'type': 'string',
            'required': True,
            'description': 'Requirements and acceptance criteria'
        },
        {
            'name': 'project_type',
            'type': 'string',
            'required': False,
            'default': 'web-app',
            'description': 'Project type (web-app, api, ml, data-platform)'
        }
    ]

    return frontmatter


def parse_handoff_markdown(content: str, filepath: Path) -> Dict[str, Any]:
    """Extract metadata from handoff template markdown content."""
    frontmatter = {
        'id': filepath.stem.replace('-template', ''),
        'name': '',
        'version': '1.0.0',
        'from_agent': '',
        'to_agents': [],
        'purpose': '',
        'variables': [],
        'description': '',
    }

    # Extract name from first heading
    name_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if name_match:
        raw_name = name_match.group(1).strip()
        # Remove Jinja2 variables from name
        clean_name = re.sub(r'\{\{.+?\}\}', '', raw_name).strip()
        clean_name = re.sub(r':\s*$', '', clean_name).strip()
        frontmatter['name'] = clean_name if clean_name else filepath.stem.replace('-template', '').replace('-', ' ').title()

    # Infer from_agent and to_agents from filename
    filename = filepath.stem.lower()
    if 'security' in filename:
        frontmatter['from_agent'] = 'security-reviewer'
        frontmatter['to_agents'] = ['web-developer', 'documentation-engineer']
    elif 'test' in filename:
        frontmatter['from_agent'] = 'test-engineer'
        frontmatter['to_agents'] = ['web-developer', 'security-reviewer']
    elif 'api' in filename or 'spec' in filename:
        frontmatter['from_agent'] = 'backend-engineer'
        frontmatter['to_agents'] = ['frontend-engineer', 'documentation-engineer']
    elif 'design' in filename or 'architecture' in filename:
        frontmatter['from_agent'] = 'architecture-agent'
        frontmatter['to_agents'] = ['web-developer', 'backend-engineer']
    elif 'sprint' in filename or 'plan' in filename:
        frontmatter['from_agent'] = 'sprint-planning'
        frontmatter['to_agents'] = ['web-developer', 'test-engineer']
    elif 'doc' in filename:
        frontmatter['from_agent'] = 'documentation-engineer'
        frontmatter['to_agents'] = ['git-committer']
    elif 'deploy' in filename:
        frontmatter['from_agent'] = 'infrastructure-engineer'
        frontmatter['to_agents'] = ['documentation-engineer']
    elif 'research' in filename:
        frontmatter['from_agent'] = 'researcher'
        frontmatter['to_agents'] = ['sprint-planning', 'web-developer']
    elif 'ml' in filename:
        frontmatter['from_agent'] = 'ml-engineer'
        frontmatter['to_agents'] = ['test-engineer', 'documentation-engineer']
    elif 'performance' in filename:
        frontmatter['from_agent'] = 'performance-engineer'
        frontmatter['to_agents'] = ['web-developer', 'documentation-engineer']
    elif 'logging' in filename:
        frontmatter['from_agent'] = 'observability-engineer'
        frontmatter['to_agents'] = ['web-developer', 'documentation-engineer']
    elif 'diagram' in filename:
        frontmatter['from_agent'] = 'diagram-engineer'
        frontmatter['to_agents'] = ['documentation-engineer']
    elif 'database' in filename:
        frontmatter['from_agent'] = 'database-specialist'
        frontmatter['to_agents'] = ['backend-engineer', 'documentation-engineer']
    elif 'component' in filename:
        frontmatter['from_agent'] = 'frontend-engineer'
        frontmatter['to_agents'] = ['test-engineer', 'documentation-engineer']
    elif 'integration' in filename:
        frontmatter['from_agent'] = 'web-developer'
        frontmatter['to_agents'] = ['test-engineer', 'security-reviewer']
    elif 'codebase' in filename or 'audit' in filename:
        frontmatter['from_agent'] = 'researcher'
        frontmatter['to_agents'] = ['sprint-planning', 'architecture-agent']
    elif 'infrastructure' in filename:
        frontmatter['from_agent'] = 'infrastructure-engineer'
        frontmatter['to_agents'] = ['security-reviewer', 'documentation-engineer']
    elif 'dashboard' in filename or 'application' in filename:
        frontmatter['from_agent'] = 'web-developer'
        frontmatter['to_agents'] = ['test-engineer', 'documentation-engineer']
    else:
        frontmatter['from_agent'] = 'web-developer'
        frontmatter['to_agents'] = ['documentation-engineer']

    # Extract Jinja2 variables
    variables = []
    var_pattern = re.compile(r'\{\{\s*(\w+)\s*\}\}')
    found_vars = set(var_pattern.findall(content))

    # Filter out config variables and common ones
    excluded = {'config', 'now', 'date', 'loop', 'item'}
    for var in sorted(found_vars):
        if var not in excluded and not var.startswith('config'):
            variables.append({
                'name': var,
                'type': 'string',
                'required': True,
                'description': f'{var.replace("_", " ").title()} value'
            })

    frontmatter['variables'] = variables[:15]  # Limit to 15

    # Generate purpose from filename
    frontmatter['purpose'] = f'Template for {frontmatter["name"].lower()}'
    frontmatter['description'] = frontmatter['purpose']

    return frontmatter


def has_frontmatter(content: str) -> bool:
    """Check if content already has YAML frontmatter."""
    return content.strip().startswith('---')


def add_frontmatter(content: str, frontmatter: Dict[str, Any]) -> str:
    """Add YAML frontmatter to markdown content."""
    # Remove empty lists and None values for cleaner output
    cleaned = {}
    for key, value in frontmatter.items():
        if value is None:
            continue
        if isinstance(value, list) and len(value) == 0:
            continue
        if isinstance(value, dict):
            cleaned_dict = {k: v for k, v in value.items() if v is not None and v != []}
            if cleaned_dict:
                cleaned[key] = cleaned_dict
        else:
            cleaned[key] = value

    yaml_str = yaml.dump(cleaned, default_flow_style=False, allow_unicode=True, sort_keys=False)
    return f"---\n{yaml_str}---\n\n{content}"


def migrate_file(filepath: Path, asset_type: str, dry_run: bool = False) -> bool:
    """Migrate a single file to include frontmatter."""
    try:
        content = filepath.read_text(encoding='utf-8')

        # Skip if already has frontmatter
        if has_frontmatter(content):
            print(f"  SKIP (has frontmatter): {filepath}")
            return False

        # Skip README files
        if filepath.name.lower() == 'readme.md':
            print(f"  SKIP (README): {filepath}")
            return False

        # Parse based on type
        if asset_type == 'agents':
            frontmatter = parse_agent_markdown(content, filepath)
        elif asset_type == 'workflows':
            frontmatter = parse_workflow_markdown(content, filepath)
        elif asset_type == 'handoffs':
            frontmatter = parse_handoff_markdown(content, filepath)
        else:
            print(f"  ERROR: Unknown asset type: {asset_type}")
            return False

        # Add frontmatter
        new_content = add_frontmatter(content, frontmatter)

        if dry_run:
            print(f"  DRY-RUN: {filepath}")
            print(f"    Would add frontmatter with id={frontmatter['id']}, name={frontmatter['name']}")
        else:
            filepath.write_text(new_content, encoding='utf-8')
            print(f"  MIGRATED: {filepath}")

        return True

    except Exception as e:
        print(f"  ERROR: {filepath}: {e}")
        return False


def migrate_assets(root_dir: Path, asset_type: str, dry_run: bool = False) -> int:
    """Migrate all assets of a given type."""
    if asset_type == 'agents':
        search_dir = root_dir / 'framework' / 'agents'
    elif asset_type == 'workflows':
        search_dir = root_dir / 'framework' / 'workflows'
    elif asset_type == 'handoffs':
        search_dir = root_dir / 'framework' / 'templates' / 'handoffs'
    else:
        print(f"Unknown asset type: {asset_type}")
        return 0

    if not search_dir.exists():
        print(f"Directory not found: {search_dir}")
        return 0

    print(f"\nMigrating {asset_type} in {search_dir}...")

    migrated = 0
    for filepath in search_dir.rglob('*.md'):
        if migrate_file(filepath, asset_type, dry_run):
            migrated += 1

    return migrated


def main():
    parser = argparse.ArgumentParser(
        description='Migrate Vibey assets to include YAML frontmatter'
    )
    parser.add_argument(
        '--type',
        choices=['agents', 'workflows', 'handoffs'],
        help='Type of assets to migrate'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Migrate all asset types'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    parser.add_argument(
        '--root',
        type=Path,
        default=Path.cwd(),
        help='Root directory of Vibey repository'
    )

    args = parser.parse_args()

    if not args.type and not args.all:
        parser.error('Either --type or --all must be specified')

    total_migrated = 0

    if args.all:
        for asset_type in ['agents', 'workflows', 'handoffs']:
            migrated = migrate_assets(args.root, asset_type, args.dry_run)
            total_migrated += migrated
            print(f"  → {migrated} {asset_type} {'would be ' if args.dry_run else ''}migrated")
    else:
        total_migrated = migrate_assets(args.root, args.type, args.dry_run)

    print(f"\nTotal: {total_migrated} files {'would be ' if args.dry_run else ''}migrated")
    return 0


if __name__ == '__main__':
    sys.exit(main())
