"""
Config operations module.

Provides functions for generating and updating project configuration files.
"""

from vibey.operations.config.generate import (
    generate_config,
    load_template,
    populate_config,
    find_template_directory,
)

from vibey.operations.config.update import (
    update_config_value,
    bulk_update_config,
    get_nested_value,
    set_nested_value,
    convert_value,
    validate_key_path,
)

__all__ = [
    # Generate operations
    'generate_config',
    'load_template',
    'populate_config',
    'find_template_directory',
    # Update operations
    'update_config_value',
    'bulk_update_config',
    'get_nested_value',
    'set_nested_value',
    'convert_value',
    'validate_key_path',
]
