"""
Standard templates package.

Provides pre-built standard templates for common quality enforcement scenarios.
Templates make it easy to add well-tested standards to any roadmap without
having to configure them from scratch.

Available Templates:
- commit-required: Ensures all tasks have git commits
- doc-review-required: Ensures documentation is updated
- test-coverage-required: Enforces minimum test coverage
- multi-platform-testing: Tests across multiple platforms
- security-review: Requires security review for certain tasks

Usage:
    from vibey.roadmap.standards.templates import list_templates, load_template

    # List available templates
    templates = list_templates()

    # Load a specific template
    standard = load_template('commit-required')
"""

import yaml
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timezone
from vibey.roadmap.models import Standard, StandardType, EnforcementMode


TEMPLATES_DIR = Path(__file__).parent


def list_templates() -> List[Dict[str, str]]:
    """
    List all available standard templates.

    Returns:
        List of dicts with template metadata (id, name, description, type, enforcement)
    """
    templates = []

    for template_file in TEMPLATES_DIR.glob("*.yaml"):
        if template_file.name == "__init__.py":
            continue

        try:
            with open(template_file, 'r') as f:
                data = yaml.safe_load(f)
                template_info = data.get('template', {})
                templates.append({
                    'id': template_info.get('id'),
                    'name': template_info.get('name'),
                    'description': template_info.get('description'),
                    'type': template_info.get('type'),
                    'enforcement': template_info.get('enforcement'),
                    'use_case': template_info.get('use_case', ''),
                })
        except Exception as e:
            # Skip invalid template files
            continue

    return sorted(templates, key=lambda t: t['id'])


def load_template(template_id: str, **overrides) -> Optional[Standard]:
    """
    Load a standard template by ID.

    Args:
        template_id: Template ID (e.g., 'commit-required')
        **overrides: Optional overrides for template fields
            - id: Override standard ID
            - name: Override standard name
            - enforcement: Override enforcement mode
            - validation: Override validation config

    Returns:
        Standard object if template found, None otherwise

    Example:
        # Load template with default values
        standard = load_template('commit-required')

        # Load template with custom ID and enforcement
        standard = load_template(
            'commit-required',
            id='my-commit-check',
            enforcement='warning'
        )
    """
    template_file = TEMPLATES_DIR / f"{template_id}.yaml"

    if not template_file.exists():
        return None

    try:
        with open(template_file, 'r') as f:
            data = yaml.safe_load(f)
            template_data = data.get('template', {})

        # Apply overrides
        standard_id = overrides.get('id', template_data.get('id'))
        name = overrides.get('name', template_data.get('name'))
        description = overrides.get('description', template_data.get('description'))

        # Parse type and enforcement
        standard_type = StandardType(overrides.get('type', template_data.get('type')))
        enforcement = EnforcementMode(overrides.get('enforcement', template_data.get('enforcement')))

        # Get validation config
        validation = overrides.get('validation', template_data.get('validation', {}))

        # Create standard
        standard = Standard(
            id=standard_id,
            name=name,
            description=description,
            type=standard_type,
            enforcement=enforcement,
            validation=validation,
            enabled=True,
            created=datetime.now(timezone.utc),
            overrides=[],
        )

        return standard

    except Exception as e:
        return None


def get_template_info(template_id: str) -> Optional[Dict]:
    """
    Get detailed information about a template.

    Args:
        template_id: Template ID

    Returns:
        Dict with template metadata, or None if not found
    """
    template_file = TEMPLATES_DIR / f"{template_id}.yaml"

    if not template_file.exists():
        return None

    try:
        with open(template_file, 'r') as f:
            data = yaml.safe_load(f)
            return data.get('template', {})
    except Exception:
        return None


__all__ = [
    'list_templates',
    'load_template',
    'get_template_info',
]
