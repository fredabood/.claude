#!/usr/bin/env python3
"""
Update Project Config

Updates a specific key in project-config.yaml using dot notation.

Usage:
    python3 update-config.py \
        --config .claude/project-config.yaml \
        --key "quality_gates.unit_testing.coverage_minimum" \
        --value "80"

Key Path Format:
    Use dot notation to specify nested keys:
    - "project.name" → config['project']['name']
    - "quality_gates.unit_testing.enabled" → config['quality_gates']['unit_testing']['enabled']
    - "orchestration.mode" → config['orchestration']['mode']

Type Conversion:
    Values are automatically converted based on existing type:
    - Booleans: "true", "yes", "1" → True; "false", "no", "0" → False
    - Integers: "80" → 80
    - Floats: "3.14" → 3.14
    - Strings: Everything else

Examples:
    # Update quality gate threshold
    python3 update-config.py \
        --config .claude/project-config.yaml \
        --key "quality_gates.unit_testing.coverage_minimum" \
        --value "85"

    # Enable a feature
    python3 update-config.py \
        --config .claude/project-config.yaml \
        --key "quality_gates.security_scanning.enabled" \
        --value "true"

    # Change orchestration mode
    python3 update-config.py \
        --config .claude/project-config.yaml \
        --key "orchestration.mode" \
        --value "balanced"
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:
    print("Error: PyYAML not installed. Install with: pip install pyyaml")
    sys.exit(1)


def get_nested_value(data: dict, key_path: str) -> Optional[Any]:
    """Get value from nested dict using dot notation.

    Args:
        data: Dictionary to search
        key_path: Dot-notation path (e.g., "quality_gates.unit_testing.enabled")

    Returns:
        Value at specified path, or None if not found
    """
    keys = key_path.split('.')
    current = data

    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None

    return current


def set_nested_value(data: dict, key_path: str, value: Any) -> dict:
    """Set value in nested dict using dot notation.

    Args:
        data: Dictionary to update
        key_path: Dot-notation path (e.g., "quality_gates.unit_testing.coverage_minimum")
        value: New value (will be type-converted)

    Returns:
        Updated dictionary
    """
    keys = key_path.split('.')
    current = data

    # Navigate to parent of target key, creating dicts as needed
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        elif not isinstance(current[key], dict):
            print(f"Warning: '{key}' is not a dictionary, overwriting")
            current[key] = {}
        current = current[key]

    # Set the value with type conversion
    final_key = keys[-1]
    old_value = current.get(final_key)

    # Type conversion based on existing value type
    converted_value = convert_value(value, old_value)

    current[final_key] = converted_value
    return data


def convert_value(value: str, reference: Any) -> Any:
    """Convert string value to appropriate type based on reference value.

    Args:
        value: String value to convert
        reference: Existing value to use as type hint

    Returns:
        Converted value
    """
    # If no reference, try to infer type
    if reference is None:
        # Try boolean
        if value.lower() in ('true', 'yes', '1'):
            return True
        if value.lower() in ('false', 'no', '0'):
            return False

        # Try integer
        try:
            return int(value)
        except ValueError:
            pass

        # Try float
        try:
            return float(value)
        except ValueError:
            pass

        # Return as string
        return value

    # Convert based on reference type
    if isinstance(reference, bool):
        return value.lower() in ('true', 'yes', '1')
    elif isinstance(reference, int):
        try:
            return int(value)
        except ValueError:
            print(f"Warning: Cannot convert '{value}' to integer, keeping as string")
            return value
    elif isinstance(reference, float):
        try:
            return float(value)
        except ValueError:
            print(f"Warning: Cannot convert '{value}' to float, keeping as string")
            return value
    else:
        return value


def validate_key_path(key_path: str) -> bool:
    """Validate that key path is well-formed.

    Args:
        key_path: Dot-notation path to validate

    Returns:
        True if valid, False otherwise
    """
    if not key_path:
        return False

    # Check for invalid characters
    if any(char in key_path for char in ['[', ']', '{', '}', ' ']):
        return False

    # Check for empty segments
    keys = key_path.split('.')
    if any(not key for key in keys):
        return False

    return True


def main():
    parser = argparse.ArgumentParser(
        description='Update project configuration value',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument('--config', required=True,
                        help='Path to project-config.yaml')
    parser.add_argument('--key', required=True,
                        help='Config key in dot notation (e.g., "quality_gates.unit_testing.coverage_minimum")')
    parser.add_argument('--value', required=True,
                        help='New value')
    parser.add_argument('--create-missing', action='store_true',
                        help='Create key if it doesn\'t exist (default: warn only)')

    args = parser.parse_args()

    # Validate inputs
    config_path = Path(args.config)

    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)

    if not validate_key_path(args.key):
        print(f"Error: Invalid key path: {args.key}")
        print("Key path should use dot notation (e.g., 'quality_gates.unit_testing.enabled')")
        sys.exit(1)

    # Load config
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"Error: Failed to load config: {e}")
        sys.exit(1)

    if not isinstance(config, dict):
        print(f"Error: Config file is not a valid YAML dictionary")
        sys.exit(1)

    # Check if key exists
    old_value = get_nested_value(config, args.key)

    if old_value is None:
        if args.create_missing:
            print(f"Warning: Key '{args.key}' not found, creating new key")
        else:
            print(f"Warning: Key '{args.key}' not found in config")
            response = input("Create new key? [y/N]: ").strip().lower()
            if response not in ('y', 'yes'):
                print("Cancelled - no changes made")
                sys.exit(0)

    # Update value
    config = set_nested_value(config, args.key, args.value)
    new_value = get_nested_value(config, args.key)

    # Write back to file
    try:
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False, indent=2)

        print(f"✓ Updated {args.key}")
        print(f"  Old value: {old_value}")
        print(f"  New value: {new_value}")
        print(f"  Type: {type(new_value).__name__}")

        return 0
    except Exception as e:
        print(f"Error: Failed to write config file: {e}")
        sys.exit(1)


if __name__ == '__main__':
    sys.exit(main())
