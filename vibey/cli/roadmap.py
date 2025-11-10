#!/usr/bin/env python3
"""
Vibey Roadmap Command

Interact with roadmap system: summarize sprints/tasks, load context.

Usage:
    python3 framework/scripts/roadmap.py summarize sprint <sprint-id>
    python3 framework/scripts/roadmap.py summarize task <task-id>
    python3 framework/scripts/roadmap.py context <task-id>
    python3 framework/scripts/roadmap.py context <task-id> --max-distance 2
    python3 framework/scripts/roadmap.py context <task-id> --format json

Created: 2025-11-09
Sprint: core-framework-2, Task 9
"""

import sys
import argparse
import json
from pathlib import Path

# Add framework to path
framework_dir = Path(__file__).parent.parent
sys.path.insert(0, str(framework_dir.parent))

from framework.roadmap.context_loader import ContextLoader, ContextMode
from framework.roadmap.summary_generator import SummaryGenerator


def print_banner():
    """Print Vibey roadmap banner."""
    print("=" * 60)
    print("🗺️  Vibey Roadmap - Context & Summary Tools")
    print("=" * 60)
    print()


def summarize_task(task_id: str, vibey_dir: Path = None, output_format: str = 'markdown') -> int:
    """
    Generate summary for a task.

    Args:
        task_id: Task ID (e.g., 'core-framework-2-task-003')
        vibey_dir: Path to .vibey directory
        output_format: Output format (markdown or json)

    Returns:
        Exit code
    """
    try:
        print(f"📋 Summarizing task: {task_id}\n")

        generator = SummaryGenerator(vibey_dir=vibey_dir)
        summary = generator.generate_task_summary(task_id, force_regenerate=False)

        if output_format == 'json':
            # Convert markdown to JSON structure
            output = {
                'task_id': task_id,
                'summary': summary,
                'format': 'markdown'
            }
            print(json.dumps(output, indent=2))
        else:
            print(summary)

        return 0

    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error generating summary: {e}")
        import traceback
        traceback.print_exc()
        return 1


def summarize_sprint(sprint_id: str, vibey_dir: Path = None, output_format: str = 'markdown') -> int:
    """
    Generate summary for a sprint.

    Args:
        sprint_id: Sprint ID (e.g., 'core-framework-2')
        vibey_dir: Path to .vibey directory
        output_format: Output format (markdown or json)

    Returns:
        Exit code
    """
    try:
        print(f"📋 Summarizing sprint: {sprint_id}\n")

        generator = SummaryGenerator(vibey_dir=vibey_dir)
        summary = generator.generate_sprint_summary(sprint_id)

        if output_format == 'json':
            # Convert markdown to JSON structure
            output = {
                'sprint_id': sprint_id,
                'summary': summary,
                'format': 'markdown'
            }
            print(json.dumps(output, indent=2))
        else:
            print(summary)

        return 0

    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error generating summary: {e}")
        import traceback
        traceback.print_exc()
        return 1


def load_task_context(
    task_id: str,
    vibey_dir: Path = None,
    max_distance: int = 3,
    output_format: str = 'markdown',
    show_stats: bool = True
) -> int:
    """
    Load context for a task with dependency-based loading.

    Args:
        task_id: Task ID
        vibey_dir: Path to .vibey directory
        max_distance: Maximum dependency distance
        output_format: Output format (markdown or json)
        show_stats: Show context reduction statistics

    Returns:
        Exit code
    """
    print_banner()

    try:
        print(f"🔍 Loading context for task: {task_id}")
        print(f"   Max distance: {max_distance}")
        print()

        loader = ContextLoader(vibey_dir=vibey_dir)
        contexts = loader.load_task_context(task_id, max_distance=max_distance)

        if not contexts:
            print(f"⚠️  No context found for task: {task_id}")
            return 1

        print(f"📦 Loaded {len(contexts)} context(s):\n")

        if output_format == 'json':
            # JSON output
            output = {
                'task_id': task_id,
                'max_distance': max_distance,
                'contexts': []
            }

            for ctx in contexts:
                output['contexts'].append({
                    'task_id': ctx.task_id,
                    'distance': ctx.distance,
                    'mode': ctx.mode.value,
                    'size_kb': round(ctx.size_kb, 2),
                    'content': ctx.content
                })

            print(json.dumps(output, indent=2))

        else:
            # Markdown output
            for ctx in contexts:
                mode_emoji = {
                    ContextMode.FULL: "📄",
                    ContextMode.SUMMARY: "📝",
                    ContextMode.MINIMAL: "📌"
                }.get(ctx.mode, "📄")

                print(f"{mode_emoji} Distance {ctx.distance}: {ctx.task_id}")
                print(f"   Mode: {ctx.mode.value} ({ctx.size_kb:.1f} KB)")
                print()
                print("-" * 60)
                print(ctx.content)
                print("-" * 60)
                print()

        # Show statistics
        if show_stats:
            stats = loader.calculate_size_reduction(task_id, max_distance)
            print("\n" + "=" * 60)
            print("📊 Context Statistics:")
            print(f"   Tasks loaded: {stats['tasks_loaded']}")
            print(f"   Total size: {stats['after_kb']:.1f} KB")
            print(f"   Size without optimization: {stats['before_kb']:.1f} KB")
            print(f"   Reduction: {stats['reduction_percent']:.1f}%")
            print("=" * 60)

        return 0

    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("\nMake sure you're in a Vibey-managed project (with .vibey/ directory).")
        print("=" * 60)
        return 1
    except Exception as e:
        print(f"❌ Error loading context: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "=" * 60)
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Roadmap context and summary tools',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Summarize a task
  %(prog)s summarize task core-framework-2-task-003

  # Summarize a sprint
  %(prog)s summarize sprint core-framework-2

  # Load task context
  %(prog)s context core-framework-2-task-003

  # Load context with custom distance
  %(prog)s context core-framework-2-task-003 --max-distance 2

  # Output as JSON
  %(prog)s context core-framework-2-task-003 --format json
        """
    )

    parser.add_argument(
        '--vibey-dir',
        type=Path,
        default=None,
        help='Path to .vibey directory (auto-detected if not provided)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Summarize command
    summarize_parser = subparsers.add_parser(
        'summarize',
        help='Generate summary for task or sprint'
    )
    summarize_parser.add_argument(
        'type',
        choices=['task', 'sprint'],
        help='Type to summarize'
    )
    summarize_parser.add_argument(
        'id',
        help='Task or sprint ID'
    )
    summarize_parser.add_argument(
        '--format',
        choices=['markdown', 'json'],
        default='markdown',
        help='Output format (default: markdown)'
    )

    # Context command
    context_parser = subparsers.add_parser(
        'context',
        help='Load context for task'
    )
    context_parser.add_argument(
        'task_id',
        help='Task ID (e.g., core-framework-2-task-003)'
    )
    context_parser.add_argument(
        '--max-distance',
        type=int,
        default=3,
        help='Maximum dependency distance (default: 3)'
    )
    context_parser.add_argument(
        '--format',
        choices=['markdown', 'json'],
        default='markdown',
        help='Output format (default: markdown)'
    )
    context_parser.add_argument(
        '--no-stats',
        action='store_true',
        help='Hide context statistics'
    )

    args = parser.parse_args()

    # Show help if no command
    if not args.command:
        parser.print_help()
        print("\n❌ Error: command is required")
        print("\nAvailable commands:")
        print("  summarize    Generate summary for task or sprint")
        print("  context      Load context for task")
        return 1

    # Execute command
    if args.command == 'summarize':
        if args.type == 'task':
            return summarize_task(
                task_id=args.id,
                vibey_dir=args.vibey_dir,
                output_format=args.format
            )
        elif args.type == 'sprint':
            return summarize_sprint(
                sprint_id=args.id,
                vibey_dir=args.vibey_dir,
                output_format=args.format
            )

    elif args.command == 'context':
        return load_task_context(
            task_id=args.task_id,
            vibey_dir=args.vibey_dir,
            max_distance=args.max_distance,
            output_format=args.format,
            show_stats=not args.no_stats
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
