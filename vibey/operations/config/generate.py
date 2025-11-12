"""
Generate Project Config Operations

Creates project-config.yaml from template and user inputs.
"""

from pathlib import Path
from datetime import datetime
from typing import Optional

try:
    import yaml
except ImportError as e:
    raise ImportError("PyYAML not installed. Install with: pip install pyyaml") from e


def load_template(project_type: str, template_dir: Path) -> dict:
    """Load config template based on project type.

    Args:
        project_type: Type of project (web-app, api, ml, cli)
        template_dir: Directory containing config templates

    Returns:
        Dictionary containing the loaded template configuration

    Raises:
        ValueError: If project type is unknown
        FileNotFoundError: If template file is not found
        yaml.YAMLError: If template file cannot be parsed
    """
    # Map project types to template files
    template_map = {
        'web-app': 'web-application-fullstack.yaml',
        'api': 'microservices.yaml',
        'ml': 'ml-application.yaml',
        'cli': 'cli-tool.yaml',
    }

    template_name = template_map.get(project_type)
    if not template_name:
        valid_types = ', '.join(template_map.keys())
        raise ValueError(
            f"Unknown project type '{project_type}'. Valid types: {valid_types}"
        )

    template_file = template_dir / template_name

    if not template_file.exists():
        raise FileNotFoundError(
            f"Template not found: {template_file}\n"
            f"Expected template directory: {template_dir}"
        )

    try:
        with open(template_file) as f:
            config = yaml.safe_load(f)
        return config
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Failed to load template: {e}") from e


def populate_config(config: dict, project_name: str, tech_stack: str) -> dict:
    """Populate config with user-provided values.

    Args:
        config: Base configuration dictionary to populate
        project_name: Name of the project
        tech_stack: Technology stack description

    Returns:
        Populated configuration dictionary
    """
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


def find_template_directory(base_path: Optional[Path] = None) -> Path:
    """Find config templates directory.

    Args:
        base_path: Optional base path to start searching from (defaults to this file's location)

    Returns:
        Path to config templates directory

    Raises:
        FileNotFoundError: If template directory cannot be found
    """
    if base_path is None:
        base_path = Path(__file__).parent

    # Try multiple locations
    possible_locations = [
        base_path.parent.parent / 'config' / 'config-templates',  # vibey/config/config-templates
        base_path.parent.parent.parent / 'framework' / 'config' / 'config-templates',  # Framework repo
    ]

    for location in possible_locations:
        if location.exists():
            return location

    locations_str = '\n'.join(f"  - {loc}" for loc in possible_locations)
    raise FileNotFoundError(
        f"Cannot find config templates directory. Tried:\n{locations_str}"
    )


def generate_config(
    project_name: str,
    project_type: str,
    output_path: Path,
    tech_stack: Optional[str] = None,
    template_dir: Optional[Path] = None,
    verbose: bool = True
) -> int:
    """Generate project configuration from template.

    Args:
        project_name: Name of the project (e.g., "E-commerce Platform")
        project_type: Type of project (web-app, api, ml, cli)
        output_path: Path where the config file should be written
        tech_stack: Optional technology stack description
        template_dir: Optional custom template directory
        verbose: Whether to print progress messages

    Returns:
        0 on success, non-zero on error
    """
    try:
        # Find or validate template directory
        if template_dir is None:
            template_dir = find_template_directory()
        elif not template_dir.exists():
            if verbose:
                print(f"Error: Template directory not found: {template_dir}")
            return 1

        if verbose:
            print(f"Loading template for project type: {project_type}")
            print(f"Template directory: {template_dir}")

        # Load template
        try:
            config = load_template(project_type, template_dir)
        except ValueError as e:
            if verbose:
                print(f"Error: {e}")
            return 1
        except FileNotFoundError as e:
            if verbose:
                print(f"Error: {e}")
            return 1
        except yaml.YAMLError as e:
            if verbose:
                print(f"Error: {e}")
            return 1

        # Populate with user values
        config = populate_config(config, project_name, tech_stack or '')

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write output
        with open(output_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False, indent=2)

        if verbose:
            print(f"✓ Configuration created: {output_path}")
            print(f"  Project: {project_name}")
            print(f"  Type: {project_type}")
            if tech_stack:
                print(f"  Tech stack: {tech_stack}")

        return 0

    except Exception as e:
        if verbose:
            print(f"Error: Failed to generate config: {e}")
        return 1
