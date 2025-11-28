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
    elif args[0] == "post-commit":
        from vibey.operations.git.hooks.post_commit import main as post_commit_main
        return post_commit_main()
    elif args[0] == "post-merge":
        from vibey.operations.git.hooks.post_merge import main as post_merge_main
        return post_merge_main("post-merge")
    elif args[0] == "post-checkout":
        from vibey.operations.git.hooks.post_merge import main as post_checkout_main
        return post_checkout_main("post-checkout")
    else:
        print(f"Unknown hook: {args[0]}")
        print("Usage: python -m vibey.operations.git.hooks [pre-commit|commit-msg <file>|post-commit|post-merge|post-checkout]")
        return 1

if __name__ == "__main__":
    sys.exit(main())
