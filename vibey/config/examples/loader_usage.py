"""
Example usage of the config loader.

This demonstrates how to use the ConfigLoader to load Vibey configuration
with automatic fallback between modular and legacy formats.
"""

from pathlib import Path
from vibey.config import (
    load_config,
    ConfigLoader,
    ConfigLocation,
    ConfigNotFoundError,
    ConfigValidationError
)


def simple_usage():
    """Simple usage: just load the config."""
    print("Simple Usage")
    print("=" * 60)

    try:
        # Load config from current directory
        config = load_config()

        print(f"✅ Loaded config for: {config.project.project.name}")
        print(f"   Type: {config.project.project.type.value}")
        print(f"   Version: {config.project.project.version}")

    except ConfigNotFoundError as e:
        print(f"❌ No config found: {e}")
    except ConfigValidationError as e:
        print(f"❌ Invalid config: {e}")


def advanced_usage():
    """Advanced usage: detect config location first."""
    print("\nAdvanced Usage")
    print("=" * 60)

    loader = ConfigLoader()
    project_root = Path.cwd()

    # Detect which config format is present
    location = loader.detect_config_location(project_root)

    print(f"Config location: {location.value}")

    if location == ConfigLocation.NONE:
        print("❌ No configuration found")
        print("   Run 'vibey init' to create one")
        return

    elif location == ConfigLocation.LEGACY:
        print("⚠️  Using legacy config (.claude/project-config.yaml)")
        print("   Consider migrating with 'vibey migrate config'")

    elif location == ConfigLocation.MODULAR:
        print("✅ Using modular config (.vibey/config/)")

    elif location == ConfigLocation.BOTH:
        print("⚠️  Both configs found, using modular")
        print("   Legacy config will be ignored")

    # Load the config
    config = loader.load_config(project_root)

    print(f"\nLoaded: {config.project.project.name}")
    print(f"Languages: {', '.join(config.project.tech_stack.languages)}")
    print(f"Orchestration: {config.framework.framework.orchestration_mode.value}")


def custom_project_root():
    """Load config from a specific directory."""
    print("\nCustom Project Root")
    print("=" * 60)

    # Load from a different directory
    other_project = Path("/path/to/other/project")

    if other_project.exists():
        try:
            config = load_config(other_project)
            print(f"✅ Loaded config from: {other_project}")
            print(f"   Project: {config.project.project.name}")
        except ConfigNotFoundError:
            print(f"❌ No config in: {other_project}")
    else:
        print(f"Project directory doesn't exist: {other_project}")


def disable_warnings():
    """Load legacy config without warnings."""
    print("\nDisable Warnings")
    print("=" * 60)

    # Suppress legacy config warnings
    loader = ConfigLoader(warn_on_legacy=False)

    try:
        config = loader.load_config()
        print("✅ Loaded without warnings")
    except ConfigNotFoundError:
        print("❌ No config found")


def access_config_details():
    """Access specific config sections."""
    print("\nAccess Config Details")
    print("=" * 60)

    try:
        config = load_config()

        # Access project config
        print("Project:")
        print(f"  Name: {config.project.project.name}")
        print(f"  Version: {config.project.project.version}")
        print(f"  Type: {config.project.project.type.value}")

        # Access framework config
        print("\nFramework:")
        print(f"  Version: {config.framework.framework.version}")
        print(f"  Mode: {config.framework.framework.orchestration_mode.value}")
        print(f"  Sprint state: {config.framework.framework.sprint_state_enabled}")

        # Access agents config
        print("\nAgents:")
        print(f"  Enabled: {', '.join(config.agents.agents.enabled)}")
        if config.agents.agent_preferences:
            print(f"  Preferences: {len(config.agents.agent_preferences)} configured")

        # Access quality gates
        print("\nQuality Gates:")
        print(f"  Enabled: {config.quality_gates.quality_gates.enabled}")
        print(f"  Mode: {config.quality_gates.quality_gates.mode.value}")
        print(f"  Security threshold: {config.quality_gates.gates.security.threshold}%")
        print(f"  Test coverage: {config.quality_gates.gates.testing.coverage_threshold}%")

    except ConfigNotFoundError:
        print("❌ No config found")


if __name__ == "__main__":
    # Run all examples
    simple_usage()
    advanced_usage()
    custom_project_root()
    disable_warnings()
    access_config_details()
