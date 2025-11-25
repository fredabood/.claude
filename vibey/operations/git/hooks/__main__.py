"""
Entry point for running hooks as Python modules.

Usage:
    python -m vibey.operations.git.hooks
"""

import sys

def main():
    """Run the appropriate hook based on arguments."""
    args = sys.argv[1:]

    if not args or args[0] == "pre-commit":
        from vibey.operations.git.hooks.pre_commit import main as pre_commit_main
        return pre_commit_main()
    elif args[0] == "commit-msg":
        from vibey.operations.git.hooks.commit_msg import main as commit_msg_main
        # Pass remaining args (commit message file path)
        return commit_msg_main(args[1:])
    else:
        print(f"Unknown hook: {args[0]}")
        print("Usage: python -m vibey.operations.git.hooks [pre-commit|commit-msg <file>]")
        return 1

if __name__ == "__main__":
    sys.exit(main())
