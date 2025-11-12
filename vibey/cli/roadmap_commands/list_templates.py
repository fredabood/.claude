"""
'roadmap list-templates' command - List available standard templates.
"""

import sys
from pathlib import Path

from ...roadmap.standards.templates import list_templates, get_template_info


def handle_list_templates(args):
    """
    Handle 'roadmap list-templates' command.

    Lists all available standard templates with their metadata.

    Args:
        args: Parsed command-line arguments with:
            - verbose: Optional flag to show detailed info

    Returns:
        Exit code: 0 for success, 1 for error
    """
    verbose = getattr(args, 'verbose', False)

    print("\n📚 Available Standard Templates")
    print("=" * 80)

    try:
        templates = list_templates()

        if not templates:
            print("\nNo templates found.")
            return 0

        # Group templates by type
        by_type = {}
        for template in templates:
            template_type = template.get('type', 'unknown')
            if template_type not in by_type:
                by_type[template_type] = []
            by_type[template_type].append(template)

        # Display templates grouped by type
        for template_type, type_templates in sorted(by_type.items()):
            print(f"\n{_format_type_name(template_type)}:")
            print("-" * 80)

            for template in type_templates:
                template_id = template.get('id', 'unknown')
                name = template.get('name', 'Unknown')
                description = template.get('description', '')
                enforcement = template.get('enforcement', 'unknown')

                # Format enforcement with color emoji
                enforcement_display = _format_enforcement(enforcement)

                print(f"\n  🏷️  {template_id}")
                print(f"      Name: {name}")
                print(f"      Enforcement: {enforcement_display}")
                print(f"      {description}")

                if verbose:
                    # Show detailed info in verbose mode
                    info = get_template_info(template_id)
                    if info:
                        use_case = info.get('use_case', '').strip()
                        if use_case:
                            print(f"\n      Use Case:")
                            for line in use_case.split('\n'):
                                if line.strip():
                                    print(f"        {line.strip()}")

                        typical_level = info.get('typical_level', '')
                        if typical_level:
                            print(f"\n      Typical Level: {typical_level}")

        # Show usage examples
        print("\n" + "=" * 80)
        print("\n💡 Usage Examples:")
        print(f"   vibey roadmap list-templates --verbose")
        print(f"   vibey roadmap add-from-template commit-required roadmap")
        print(f"   vibey roadmap add-from-template test-coverage-required track backend")
        print()

        return 0

    except Exception as e:
        print(f"\n❌ Failed to list templates: {e}")
        return 1


def _format_type_name(template_type: str) -> str:
    """Format template type name for display."""
    type_names = {
        'commit_check': '📝 Commit Checks',
        'file_check': '📄 File Checks',
        'test_run': '🧪 Test Requirements',
        'custom_script': '⚙️  Custom Scripts',
    }
    return type_names.get(template_type, f"❓ {template_type}")


def _format_enforcement(enforcement: str) -> str:
    """Format enforcement mode with emoji."""
    enforcement_formats = {
        'blocking': '🔴 BLOCKING',
        'warning': '🟡 WARNING',
        'audit': '🟢 AUDIT',
    }
    return enforcement_formats.get(enforcement, f"❓ {enforcement}")
