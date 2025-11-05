#!/usr/bin/env python3
"""
Generate Project Config

Creates project-config.yaml from template and user inputs.

Usage:
    python3 generate-config.py \
        --project-name "My App" \
        --project-type web-app \
        --tech-stack "Python/FastAPI, React, PostgreSQL" \
        --output .claude/project-config.yaml

Project Types:
    - web-app: Full-stack web application
    - api: Microservices/REST API
    - ml: Machine learning application
    - cli: Command-line tool

Examples:
    # Web application
    python3 generate-config.py \
        --project-name "E-commerce Platform" \
        --project-type web-app \
        --tech-stack "Django, React, PostgreSQL" \
        --output .claude/project-config.yaml

    # API service
    python3 generate-config.py \
        --project-name "User Service API" \
        --project-type api \
        --tech-stack "FastAPI, MongoDB" \
        --output .claude/project-config.yaml
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

try:
    import yaml
except ImportError:
    print("Error: PyYAML not installed. Install with: pip install pyyaml")
    sys.exit(1)


def load_template(project_type: str, template_dir: Path) -> dict:
    """Load config template based on project type."""
    # Map project types to template files
    template_map = {
        'web-app': 'web-application-fullstack.yaml',
        'api': 'microservices.yaml',
        'ml': 'ml-application.yaml',
        'cli': 'cli-tool.yaml',
    }

    template_name = template_map.get(project_type)
    if not template_name:
        print(f"Error: Unknown project type '{project_type}'")
        print(f"Valid types: {', '.join(template_map.keys())}")
        sys.exit(1)

    template_file = template_dir / template_name

    if not template_file.exists():
        print(f"Error: Template not found: {template_file}")
        print(f"Expected template directory: {template_dir}")
        sys.exit(1)

    try:
        with open(template_file) as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"Error: Failed to load template: {e}")
        sys.exit(1)


def populate_config(config: dict, project_name: str, tech_stack: str) -> dict:
    """Populate config with user-provided values."""
    # Update project name
    if 'project' in config:
        config['project']['name'] = project_name
        config['project']['created_at'] = datetime.now().isoformat()

    # Update tech stack description
    if tech_stack and 'technology_stack' in config:
        config['technology_stack']['description'] = tech_stack

        # Try to parse tech stack components (simple heuristic)
        tech_lower = tech_stack.lower()

        # Backend detection
        if any(x in tech_lower for x in ['python', 'django', 'flask', 'fastapi']):
            config['technology_stack']['backend'] = 'Python'
        elif any(x in tech_lower for x in ['node', 'express', 'nestjs']):
            config['technology_stack']['backend'] = 'Node.js'
        elif any(x in tech_lower for x in ['java', 'spring']):
            config['technology_stack']['backend'] = 'Java'
        elif any(x in tech_lower for x in ['go', 'golang']):
            config['technology_stack']['backend'] = 'Go'

        # Frontend detection
        if any(x in tech_lower for x in ['react', 'reactjs']):
            config['technology_stack']['frontend'] = 'React'
        elif any(x in tech_lower for x in ['vue', 'vuejs']):
            config['technology_stack']['frontend'] = 'Vue.js'
        elif any(x in tech_lower for x in ['angular']):
            config['technology_stack']['frontend'] = 'Angular'
        elif any(x in tech_lower for x in ['svelte']):
            config['technology_stack']['frontend'] = 'Svelte'

        # Database detection
        if any(x in tech_lower for x in ['postgres', 'postgresql']):
            config['technology_stack']['database'] = 'PostgreSQL'
        elif any(x in tech_lower for x in ['mysql']):
            config['technology_stack']['database'] = 'MySQL'
        elif any(x in tech_lower for x in ['mongodb', 'mongo']):
            config['technology_stack']['database'] = 'MongoDB'
        elif any(x in tech_lower for x in ['redis']):
            config['technology_stack']['database'] = 'Redis'

    return config


def main():
    parser = argparse.ArgumentParser(
        description='Generate project configuration from template',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument('--project-name', required=True,
                        help='Project name (e.g., "E-commerce Platform")')
    parser.add_argument('--project-type', required=True,
                        choices=['web-app', 'api', 'ml', 'cli'],
                        help='Project type')
    parser.add_argument('--tech-stack',
                        help='Technology stack description (e.g., "Python/FastAPI, React, PostgreSQL")')
    parser.add_argument('--output', required=True,
                        help='Output file path (e.g., .claude/project-config.yaml)')
    parser.add_argument('--template-dir',
                        help='Template directory (default: auto-detect)')

    args = parser.parse_args()

    # Auto-detect template directory
    if args.template_dir:
        template_dir = Path(args.template_dir)
    else:
        # Try multiple locations
        script_dir = Path(__file__).parent
        possible_locations = [
            script_dir.parent / 'config' / 'config-templates',  # Deployed location
            script_dir.parent.parent / 'framework' / 'config' / 'config-templates',  # Framework repo
        ]

        template_dir = None
        for location in possible_locations:
            if location.exists():
                template_dir = location
                break

        if not template_dir:
            print("Error: Cannot find config templates directory")
            print("Tried:")
            for loc in possible_locations:
                print(f"  - {loc}")
            sys.exit(1)

    print(f"Loading template for project type: {args.project_type}")
    print(f"Template directory: {template_dir}")

    # Load template
    config = load_template(args.project_type, template_dir)

    # Populate with user values
    config = populate_config(config, args.project_name, args.tech_stack or '')

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write output
    try:
        with open(output_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False, indent=2)

        print(f"✓ Configuration created: {output_path}")
        print(f"  Project: {args.project_name}")
        print(f"  Type: {args.project_type}")
        if args.tech_stack:
            print(f"  Tech stack: {args.tech_stack}")

        return 0
    except Exception as e:
        print(f"Error: Failed to write config file: {e}")
        sys.exit(1)


if __name__ == '__main__':
    sys.exit(main())
