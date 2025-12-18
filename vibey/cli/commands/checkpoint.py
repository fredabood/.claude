"""
Checkpoint management commands.

Provides checkpoint creation, verification, and management functionality
for roadmap integrity.
"""

from pathlib import Path
from typing import Optional


def checkpoint_create_cmd(name: Optional[str] = None) -> int:
    """Create a new integrity checkpoint."""
    import subprocess
    from datetime import datetime

    # Default to timestamped name if not provided
    if not name:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"checkpoint_{timestamp}"

    script_path = Path(__file__).parent.parent.parent.parent / "scripts" / "create-integrity-checkpoint.sh"

    try:
        result = subprocess.run(
            [str(script_path), name],
            cwd=Path.cwd(),
            check=False
        )
        return result.returncode
    except Exception as e:
        print(f"Error creating checkpoint: {e}")
        return 1


def checkpoint_list_cmd() -> int:
    """List all available checkpoints."""
    import subprocess

    script_path = Path(__file__).parent.parent.parent.parent / "scripts" / "manage-checkpoints.sh"

    try:
        result = subprocess.run(
            [str(script_path), "list"],
            cwd=Path.cwd(),
            check=False
        )
        return result.returncode
    except Exception as e:
        print(f"Error listing checkpoints: {e}")
        return 1


def checkpoint_verify_cmd(name: str) -> int:
    """Verify checkpoint integrity."""
    import subprocess

    script_path = Path(__file__).parent.parent.parent.parent / "scripts" / "manage-checkpoints.sh"

    try:
        result = subprocess.run(
            [str(script_path), "verify", name],
            cwd=Path.cwd(),
            check=False
        )
        return result.returncode
    except Exception as e:
        print(f"Error verifying checkpoint: {e}")
        return 1


def checkpoint_restore_cmd(name: str, verify_only: bool = False) -> int:
    """Restore from a checkpoint."""
    import subprocess

    script_path = Path(__file__).parent.parent.parent.parent / "scripts" / "restore-integrity-checkpoint.sh"

    args = [str(script_path), name]
    if verify_only:
        args.append("--verify-only")

    try:
        result = subprocess.run(
            args,
            cwd=Path.cwd(),
            check=False
        )
        return result.returncode
    except Exception as e:
        print(f"Error restoring checkpoint: {e}")
        return 1


def checkpoint_clean_cmd(keep: int = 5) -> int:
    """Clean old checkpoints."""
    import subprocess

    script_path = Path(__file__).parent.parent.parent.parent / "scripts" / "manage-checkpoints.sh"

    try:
        result = subprocess.run(
            [str(script_path), "clean", str(keep)],
            cwd=Path.cwd(),
            check=False
        )
        return result.returncode
    except Exception as e:
        print(f"Error cleaning checkpoints: {e}")
        return 1


def checkpoint_compare_cmd(checkpoint1: str, checkpoint2: str) -> int:
    """Compare two checkpoints."""
    import subprocess

    script_path = Path(__file__).parent.parent.parent.parent / "scripts" / "manage-checkpoints.sh"

    try:
        result = subprocess.run(
            [str(script_path), "compare", checkpoint1, checkpoint2],
            cwd=Path.cwd(),
            check=False
        )
        return result.returncode
    except Exception as e:
        print(f"Error comparing checkpoints: {e}")
        return 1
