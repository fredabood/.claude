#!/usr/bin/env python3
"""
Template Renderer for Vibey Framework

Renders Jinja2 templates with config values

Usage:
    python scripts/render-template.py --config project-config.yaml --template templates/CLAUDE.md.template --output CLAUDE.md
    python scripts/render-template.py -c config.yaml -t template.md -o output.md
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)

try:
    from jinja2 import Environment, FileSystemLoader, TemplateNotFound, TemplateSyntaxError
except ImportError:
    print("Error: Jinja2 is required. Install with: pip install jinja2")
    sys.exit(1)


class TemplateRenderer:
    """Renders Jinja2 templates with config values"""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load the config YAML file"""
        if not self.config_path.exists():
            print(f"Error: Config file not found at {self.config_path}")
            sys.exit(1)

        with open(self.config_path) as f:
            try:
                config = yaml.safe_load(f)
            except yaml.YAMLError as e:
                print(f"Error: Invalid YAML syntax in config: {e}")
                sys.exit(1)

        if config is None:
            print("Error: Config file is empty")
            sys.exit(1)

        return config

    def render_template(self, template_path: Path, output_path: Path = None) -> str:
        """Render a Jinja2 template with the config"""
        if not template_path.exists():
            print(f"Error: Template file not found at {template_path}")
            sys.exit(1)

        # Set up Jinja2 environment
        template_dir = template_path.parent
        template_name = template_path.name

        env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

        # Add custom filters
        env.filters["datetime"] = lambda fmt: datetime.now().strftime(fmt)

        try:
            template = env.get_template(template_name)
        except TemplateNotFound:
            print(f"Error: Template not found: {template_name}")
            sys.exit(1)
        except TemplateSyntaxError as e:
            print(f"Error: Template syntax error at line {e.lineno}: {e.message}")
            sys.exit(1)

        # Prepare template context
        context = {
            "config": self.config,
            "now": datetime.now(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        # Render template
        try:
            rendered = template.render(context)
        except Exception as e:
            print(f"Error: Failed to render template: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)

        # Write output
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                f.write(rendered)
            print(f"✓ Rendered: {output_path}")

        return rendered

    def render_all_templates(self, template_dir: Path, output_dir: Path):
        """Render all templates in a directory"""
        if not template_dir.exists():
            print(f"Error: Template directory not found: {template_dir}")
            sys.exit(1)

        template_files = list(template_dir.glob("*.template"))
        if not template_files:
            print(f"No .template files found in {template_dir}")
            return

        print(f"Found {len(template_files)} templates")
        print()

        for template_file in template_files:
            # Output filename: remove .template extension
            output_name = template_file.stem  # Gets filename without .template
            output_path = output_dir / output_name

            print(f"Rendering {template_file.name} → {output_path}")
            self.render_template(template_file, output_path)

        print()
        print(f"✓ Rendered {len(template_files)} templates to {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Render Vibey Jinja2 templates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Render single template
  python scripts/render-template.py \\
    --config project-config.yaml \\
    --template templates/CLAUDE.md.template \\
    --output CLAUDE.md

  # Render all templates in directory
  python scripts/render-template.py \\
    --config project-config.yaml \\
    --template-dir templates/ \\
    --output-dir .

  # Short form
  python scripts/render-template.py -c config.yaml -t template.md -o output.md
        """,
    )

    parser.add_argument(
        "--config",
        "-c",
        required=True,
        help="Path to project config YAML file",
    )

    parser.add_argument(
        "--template",
        "-t",
        help="Path to Jinja2 template file",
    )

    parser.add_argument(
        "--output",
        "-o",
        help="Path to output file (if not specified, prints to stdout)",
    )

    parser.add_argument(
        "--template-dir",
        "-d",
        help="Directory containing .template files (renders all)",
    )

    parser.add_argument(
        "--output-dir",
        help="Output directory for rendered templates (used with --template-dir)",
    )

    args = parser.parse_args()

    # Validate arguments
    if args.template and args.template_dir:
        print("Error: Cannot specify both --template and --template-dir")
        sys.exit(1)

    if not args.template and not args.template_dir:
        print("Error: Must specify either --template or --template-dir")
        sys.exit(1)

    if args.template_dir and not args.output_dir:
        print("Error: --output-dir required when using --template-dir")
        sys.exit(1)

    # Initialize renderer
    config_path = Path(args.config)
    renderer = TemplateRenderer(config_path)

    # Render templates
    if args.template:
        # Single template mode
        template_path = Path(args.template)
        output_path = Path(args.output) if args.output else None

        rendered = renderer.render_template(template_path, output_path)

        if not output_path:
            # Print to stdout if no output file specified
            print(rendered)
    else:
        # Directory mode
        template_dir = Path(args.template_dir)
        output_dir = Path(args.output_dir)

        renderer.render_all_templates(template_dir, output_dir)


if __name__ == "__main__":
    main()
