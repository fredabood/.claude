"""
Git Hook Installer for Roadmap Validation

Installs and manages pre-commit hooks for automatic roadmap validation.
"""

import shutil
import stat
from pathlib import Path
from typing import Tuple, Optional


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


def install_hooks(project_root: Path = None, force: bool = False) -> Tuple[bool, str]:
    """
    Install pre-commit hook for roadmap validation.

    Args:
        project_root: Project root directory (default: cwd)
        force: Overwrite existing hook if present

    Returns:
        Tuple of (success: bool, message: str)
    """
    if project_root is None:
        project_root = Path.cwd()

    # Find .git directory
    git_dir = find_git_dir(project_root)
    if not git_dir:
        return False, "Not a git repository (no .git directory found)"

    # Paths
    hooks_dir = git_dir / "hooks"
    hook_dest = hooks_dir / "pre-commit"
    hook_source = Path(__file__).parent / "pre-commit"

    # Ensure hooks directory exists
    hooks_dir.mkdir(exist_ok=True)

    # Check if hook already exists
    if hook_dest.exists() and not force:
        # Check if it's our hook
        if hook_dest.is_file():
            content = hook_dest.read_text()
            if "Vibey Roadmap Pre-Commit Hook" in content:
                return True, "Vibey pre-commit hook is already installed"
            else:
                return False, (
                    f"A different pre-commit hook already exists at {hook_dest}\n"
                    f"Use --force to overwrite, or manually merge the hooks"
                )

    # Backup existing hook if it exists and we're forcing
    if hook_dest.exists() and force:
        backup_path = hook_dest.with_suffix(".backup")
        counter = 1
        while backup_path.exists():
            backup_path = hook_dest.with_suffix(f".backup.{counter}")
            counter += 1

        shutil.copy2(hook_dest, backup_path)
        backup_msg = f"\nExisting hook backed up to: {backup_path.name}"
    else:
        backup_msg = ""

    # Copy hook script
    shutil.copy2(hook_source, hook_dest)

    # Make executable
    hook_dest.chmod(hook_dest.stat().st_mode | stat.S_IEXEC)

    return True, f"✅ Pre-commit hook installed successfully at {hook_dest}{backup_msg}"


def uninstall_hooks(project_root: Path = None) -> Tuple[bool, str]:
    """
    Uninstall Vibey pre-commit hook.

    Args:
        project_root: Project root directory (default: cwd)

    Returns:
        Tuple of (success: bool, message: str)
    """
    if project_root is None:
        project_root = Path.cwd()

    # Find .git directory
    git_dir = find_git_dir(project_root)
    if not git_dir:
        return False, "Not a git repository (no .git directory found)"

    hook_path = git_dir / "hooks" / "pre-commit"

    # Check if hook exists
    if not hook_path.exists():
        return True, "No pre-commit hook installed"

    # Check if it's our hook
    content = hook_path.read_text()
    if "Vibey Roadmap Pre-Commit Hook" not in content:
        return False, (
            "Pre-commit hook exists but is not a Vibey hook.\n"
            "Remove manually if needed."
        )

    # Remove the hook
    hook_path.unlink()

    return True, "✅ Pre-commit hook uninstalled successfully"


def check_hooks_installed(project_root: Path = None) -> Tuple[bool, str, Optional[Path]]:
    """
    Check if Vibey pre-commit hook is installed.

    Args:
        project_root: Project root directory (default: cwd)

    Returns:
        Tuple of (installed: bool, status_message: str, hook_path: Optional[Path])
    """
    if project_root is None:
        project_root = Path.cwd()

    # Find .git directory
    git_dir = find_git_dir(project_root)
    if not git_dir:
        return False, "Not a git repository", None

    hook_path = git_dir / "hooks" / "pre-commit"

    # Check if hook exists
    if not hook_path.exists():
        return False, "No pre-commit hook installed", None

    # Check if it's our hook
    content = hook_path.read_text()
    if "Vibey Roadmap Pre-Commit Hook" not in content:
        return False, "Different pre-commit hook installed", hook_path

    # Check if executable
    is_executable = hook_path.stat().st_mode & stat.S_IEXEC
    if not is_executable:
        return False, "Vibey hook installed but not executable", hook_path

    return True, "✅ Vibey pre-commit hook is installed and active", hook_path


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
        'pre_commit_exists': False,
        'is_vibey_hook': False,
        'is_executable': False,
        'hook_path': None,
    }

    if not git_dir:
        return status

    hooks_dir = git_dir / "hooks"
    status['hooks_dir_exists'] = hooks_dir.exists()

    if not hooks_dir.exists():
        return status

    hook_path = hooks_dir / "pre-commit"
    status['hook_path'] = str(hook_path)
    status['pre_commit_exists'] = hook_path.exists()

    if not hook_path.exists():
        return status

    # Check if it's our hook
    content = hook_path.read_text()
    status['is_vibey_hook'] = "Vibey Roadmap Pre-Commit Hook" in content

    # Check if executable
    status['is_executable'] = bool(hook_path.stat().st_mode & stat.S_IEXEC)

    return status
