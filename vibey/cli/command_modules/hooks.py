"""
Git hook management commands.

Commands for installing, uninstalling, and checking git pre-commit hooks
for roadmap validation.
"""

from pathlib import Path


def install_hooks_cmd(force: bool = False) -> int:
    """Install git pre-commit hook."""
    from vibey.operations.roadmap.hooks import install_hooks

    print("Installing Vibey pre-commit hook...\n")

    success, message = install_hooks(project_root=Path.cwd(), force=force)

    print(message)

    if success:
        print("\nConfiguration:")
        print("  - Hook runs when .vibey/roadmap/ files are modified")
        print("  - Set VIBEY_HOOK_ADVANCED=true to enable advanced validation")
        print("  - Bypass with: git commit --no-verify (emergency only)")
        print("\nTest the hook:")
        print("  1. Make a change to a roadmap file")
        print("  2. Run: git add .vibey/roadmap/...")
        print("  3. Run: git commit -m 'test'")
        print("  4. Hook will validate before allowing commit")
        return 0
    else:
        return 1


def uninstall_hooks_cmd() -> int:
    """Uninstall git pre-commit hook."""
    from vibey.operations.roadmap.hooks import uninstall_hooks

    print("Uninstalling Vibey pre-commit hook...\n")

    success, message = uninstall_hooks(project_root=Path.cwd())

    print(message)

    return 0 if success else 1


def check_hooks_cmd() -> int:
    """Check git hook installation status."""
    from vibey.operations.roadmap.hooks import get_hook_status

    status = get_hook_status(project_root=Path.cwd())

    print("Git Hook Status")
    print("=" * 70)
    print()

    if not status['git_repo']:
        print("Not a git repository")
        return 1

    print(f"Git directory: {status['git_dir']}")
    print(f"Hooks directory exists: {'Yes' if status['hooks_dir_exists'] else 'No'}")
    print()

    if not status['pre_commit_exists']:
        print("No pre-commit hook installed")
        print()
        print("Install with: vibey roadmap install-hooks")
        return 1

    print(f"Pre-commit hook: {status['hook_path']}")
    print(f"  Is Vibey hook: {'Yes' if status['is_vibey_hook'] else 'No'}")
    print(f"  Is executable: {'Yes' if status['is_executable'] else 'No'}")
    print()

    if status['is_vibey_hook'] and status['is_executable']:
        print("Vibey pre-commit hook is installed and active")
        print()
        print("Configuration:")
        print("  - VIBEY_HOOK_ADVANCED: Set to 'true' to enable advanced validation")
        print("  - Bypass: git commit --no-verify")
        return 0
    elif status['is_vibey_hook'] and not status['is_executable']:
        print("Vibey hook installed but not executable")
        print()
        print(f"Fix with: chmod +x {status['hook_path']}")
        return 1
    else:
        print("A different pre-commit hook is installed")
        print()
        print("To install Vibey hook:")
        print("  1. Back up existing hook if needed")
        print("  2. Run: vibey roadmap install-hooks --force")
        return 1
