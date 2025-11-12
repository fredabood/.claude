"""
Update Project Config Operations

Updates specific keys in project-config.yaml using dot notation.
"""

from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError as e:
    raise ImportError("PyYAML not installed. Install with: pip install pyyaml") from e


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
            # Overwrite non-dict values
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
        Converted value with appropriate type
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
            # Keep as string if conversion fails
            return value
    elif isinstance(reference, float):
        try:
            return float(value)
        except ValueError:
            # Keep as string if conversion fails
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


def update_config_value(
    config_path: Path,
    key_path: str,
    value: str,
    create_missing: bool = False,
    verbose: bool = True
) -> int:
    """Update a specific key in project configuration.

    Args:
        config_path: Path to project-config.yaml
        key_path: Config key in dot notation (e.g., "quality_gates.unit_testing.coverage_minimum")
        value: New value (will be type-converted)
        create_missing: Create key if it doesn't exist (otherwise prompts user)
        verbose: Whether to print progress messages

    Returns:
        0 on success, non-zero on error
    """
    try:
        # Validate inputs
        if not config_path.exists():
            if verbose:
                print(f"Error: Config file not found: {config_path}")
            return 1

        if not validate_key_path(key_path):
            if verbose:
                print(f"Error: Invalid key path: {key_path}")
                print("Key path should use dot notation (e.g., 'quality_gates.unit_testing.enabled')")
            return 1

        # Load config
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            if verbose:
                print(f"Error: Failed to load config: {e}")
            return 1

        if not isinstance(config, dict):
            if verbose:
                print("Error: Config file is not a valid YAML dictionary")
            return 1

        # Check if key exists
        old_value = get_nested_value(config, key_path)

        if old_value is None:
            if create_missing:
                if verbose:
                    print(f"Warning: Key '{key_path}' not found, creating new key")
            else:
                if verbose:
                    print(f"Warning: Key '{key_path}' not found in config")
                    print("Use create_missing=True to create new keys automatically")
                return 1

        # Update value
        config = set_nested_value(config, key_path, value)
        new_value = get_nested_value(config, key_path)

        # Write back to file
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False, indent=2)

        if verbose:
            print(f"✓ Updated {key_path}")
            print(f"  Old value: {old_value}")
            print(f"  New value: {new_value}")
            print(f"  Type: {type(new_value).__name__}")

        return 0

    except Exception as e:
        if verbose:
            print(f"Error: Failed to update config: {e}")
        return 1


def bulk_update_config(
    config_path: Path,
    updates: dict[str, str],
    create_missing: bool = False,
    verbose: bool = True
) -> int:
    """Update multiple keys in project configuration.

    Args:
        config_path: Path to project-config.yaml
        updates: Dictionary mapping key paths to new values
        create_missing: Create keys if they don't exist
        verbose: Whether to print progress messages

    Returns:
        0 on success, non-zero on error
    """
    try:
        # Validate inputs
        if not config_path.exists():
            if verbose:
                print(f"Error: Config file not found: {config_path}")
            return 1

        # Load config once
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            if verbose:
                print(f"Error: Failed to load config: {e}")
            return 1

        if not isinstance(config, dict):
            if verbose:
                print("Error: Config file is not a valid YAML dictionary")
            return 1

        # Apply all updates
        updated_count = 0
        for key_path, value in updates.items():
            if not validate_key_path(key_path):
                if verbose:
                    print(f"Warning: Skipping invalid key path: {key_path}")
                continue

            old_value = get_nested_value(config, key_path)

            if old_value is None and not create_missing:
                if verbose:
                    print(f"Warning: Skipping missing key: {key_path}")
                continue

            config = set_nested_value(config, key_path, value)
            updated_count += 1

            if verbose:
                new_value = get_nested_value(config, key_path)
                print(f"✓ Updated {key_path}: {old_value} → {new_value}")

        # Write back to file
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False, indent=2)

        if verbose:
            print(f"\n✓ Updated {updated_count}/{len(updates)} keys")

        return 0

    except Exception as e:
        if verbose:
            print(f"Error: Failed to update config: {e}")
        return 1
