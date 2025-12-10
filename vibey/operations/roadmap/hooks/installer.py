"""
Git Hook Installer for Roadmap Validation

Installs and manages git hooks for automatic roadmap validation.

Supported hooks:
- pre-commit: Validates YAML syntax and activity log entries
- pre-push: Verifies all commits have activity log entries

Task: git-integration-5-task-006
"""

import shutil
import stat
from pathlib import Path
from typing import Tuple, Optional, List


# Hooks that can be installed
SUPPORTED_HOOKS = ["pre-commit", "pre-push"]


def find_git_dir(start_path: Path = None) -> Optional[Path]:
    """
    Find the .git directory by walking up from start_path.

    Args:
        start_path: Directory to start search from (default: cwd)

    Returns:
        Path to .git directory or None if not found
    """
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()

    # Walk up the directory tree
    for parent in [current] + list(current.parents):
        git_dir = parent / ".git"
        if git_dir.exists() and git_dir.is_dir():
            return git_dir

    return None


def _install_single_hook(
    hooks_dir: Path,
    hook_name: str,
    force: bool = False
) -> Tuple[bool, str]:
    """
    Install a single hook.

    Args:
        hooks_dir: Path to .git/hooks directory
        hook_name: Name of the hook (e.g., "pre-commit", "pre-push")
        force: Overwrite existing hook if present

    Returns:
        Tuple of (success: bool, message: str)
    """
    hook_dest = hooks_dir / hook_name
    hook_source = Path(__file__).parent / hook_name

    # Check if source exists
    if not hook_source.exists():
        return False, f"Hook source not found: {hook_source}"

    # Check if hook already exists
    if hook_dest.exists() and not force:
        if hook_dest.is_file():
            content = hook_dest.read_text()
            if f"Vibey Roadmap {hook_name.title().replace('-', ' ')} Hook" in content:
                return True, f"Vibey {hook_name} hook is already installed"
            else:
                return False, (
                    f"A different {hook_name} hook already exists.\n"
                    f"Use --force to overwrite, or manually merge the hooks"
                )

    # Backup existing hook if forcing
    backup_msg = ""
    if hook_dest.exists() and force:
        backup_path = hook_dest.with_suffix(".backup")
        counter = 1
        while backup_path.exists():
            backup_path = hook_dest.with_suffix(f".backup.{counter}")
            counter += 1

        shutil.copy2(hook_dest, backup_path)
        backup_msg = f" (backed up to {backup_path.name})"

    # Copy hook script
    shutil.copy2(hook_source, hook_dest)

    # Make executable
    hook_dest.chmod(hook_dest.stat().st_mode | stat.S_IEXEC)

    return True, f"✓ {hook_name}{backup_msg}"


def install_hooks(project_root: Path = None, force: bool = False, hooks: List[str] = None) -> Tuple[bool, str]:
    """
    Install git hooks for roadmap validation.

    Args:
        project_root: Project root directory (default: cwd)
        force: Overwrite existing hooks if present
        hooks: List of hook names to install (default: all supported hooks)

    Returns:
        Tuple of (success: bool, message: str)
    """
    if project_root is None:
        project_root = Path.cwd()

    # Default to all supported hooks
    if hooks is None:
        hooks = SUPPORTED_HOOKS

    # Find .git directory
    git_dir = find_git_dir(project_root)
    if not git_dir:
        return False, "Not a git repository (no .git directory found)"

    # Ensure hooks directory exists
    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)

    # Install each hook
    results = []
    all_success = True

    for hook_name in hooks:
        if hook_name not in SUPPORTED_HOOKS:
            results.append(f"✗ {hook_name}: unsupported hook type")
            all_success = False
            continue

        success, message = _install_single_hook(hooks_dir, hook_name, force)
        results.append(message)
        if not success:
            all_success = False

    # Format output
    output_lines = ["Git hooks installation:"]
    output_lines.extend(f"  {r}" for r in results)

    if all_success:
        output_lines.append(f"\n✅ All hooks installed at {hooks_dir}")
    else:
        output_lines.append("\n⚠️ Some hooks failed to install")

    return all_success, "\n".join(output_lines)


def uninstall_hooks(project_root: Path = None, hooks: List[str] = None) -> Tuple[bool, str]:
    """
    Uninstall Vibey git hooks.

    Args:
        project_root: Project root directory (default: cwd)
        hooks: List of hook names to uninstall (default: all supported hooks)

    Returns:
        Tuple of (success: bool, message: str)
    """
    if project_root is None:
        project_root = Path.cwd()

    # Default to all supported hooks
    if hooks is None:
        hooks = SUPPORTED_HOOKS

    # Find .git directory
    git_dir = find_git_dir(project_root)
    if not git_dir:
        return False, "Not a git repository (no .git directory found)"

    hooks_dir = git_dir / "hooks"
    results = []
    all_success = True

    for hook_name in hooks:
        hook_path = hooks_dir / hook_name

        # Check if hook exists
        if not hook_path.exists():
            results.append(f"✓ {hook_name}: not installed")
            continue

        # Check if it's our hook
        content = hook_path.read_text()
        hook_title = f"Vibey Roadmap {hook_name.title().replace('-', ' ')} Hook"
        if hook_title not in content:
            results.append(f"✗ {hook_name}: exists but is not a Vibey hook")
            all_success = False
            continue

        # Remove the hook
        hook_path.unlink()
        results.append(f"✓ {hook_name}: uninstalled")

    # Format output
    output_lines = ["Git hooks uninstallation:"]
    output_lines.extend(f"  {r}" for r in results)

    if all_success:
        output_lines.append("\n✅ Hooks uninstalled successfully")

    return all_success, "\n".join(output_lines)


def check_hooks_installed(project_root: Path = None) -> Tuple[bool, str, Optional[Path]]:
    """
    Check if Vibey git hooks are installed.

    Args:
        project_root: Project root directory (default: cwd)

    Returns:
        Tuple of (all_installed: bool, status_message: str, hooks_dir: Optional[Path])
    """
    if project_root is None:
        project_root = Path.cwd()

    # Find .git directory
    git_dir = find_git_dir(project_root)
    if not git_dir:
        return False, "Not a git repository", None

    hooks_dir = git_dir / "hooks"
    results = []
    all_installed = True

    for hook_name in SUPPORTED_HOOKS:
        hook_path = hooks_dir / hook_name

        if not hook_path.exists():
            results.append(f"✗ {hook_name}: not installed")
            all_installed = False
            continue

        content = hook_path.read_text()
        hook_title = f"Vibey Roadmap {hook_name.title().replace('-', ' ')} Hook"

        if hook_title not in content:
            results.append(f"✗ {hook_name}: different hook installed")
            all_installed = False
            continue

        is_executable = hook_path.stat().st_mode & stat.S_IEXEC
        if not is_executable:
            results.append(f"⚠ {hook_name}: installed but not executable")
            all_installed = False
            continue

        results.append(f"✓ {hook_name}: active")

    status_msg = "Git hooks status:\n" + "\n".join(f"  {r}" for r in results)

    if all_installed:
        status_msg += "\n\n✅ All Vibey hooks are installed and active"

    return all_installed, status_msg, hooks_dir


def get_hook_status(project_root: Path = None) -> dict:
    """
    Get detailed status of git hooks.

    Args:
        project_root: Project root directory (default: cwd)

    Returns:
        Dictionary with hook status information
    """
    if project_root is None:
        project_root = Path.cwd()

    git_dir = find_git_dir(project_root)

    status = {
        'git_repo': git_dir is not None,
        'git_dir': str(git_dir) if git_dir else None,
        'hooks_dir_exists': False,
        'hooks': {},
    }

    if not git_dir:
        return status

    hooks_dir = git_dir / "hooks"
    status['hooks_dir_exists'] = hooks_dir.exists()

    if not hooks_dir.exists():
        return status

    # Check each supported hook
    for hook_name in SUPPORTED_HOOKS:
        hook_path = hooks_dir / hook_name
        hook_status = {
            'exists': hook_path.exists(),
            'is_vibey_hook': False,
            'is_executable': False,
            'path': str(hook_path),
        }

        if hook_path.exists():
            content = hook_path.read_text()
            hook_title = f"Vibey Roadmap {hook_name.title().replace('-', ' ')} Hook"
            hook_status['is_vibey_hook'] = hook_title in content
            hook_status['is_executable'] = bool(hook_path.stat().st_mode & stat.S_IEXEC)

        status['hooks'][hook_name] = hook_status

    return status
