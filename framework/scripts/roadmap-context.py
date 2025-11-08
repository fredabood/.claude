#!/usr/bin/env python3
"""
Roadmap Context Loader

Loads dependency context with configurable modes (minimal/summary/full).
Implements hierarchical loading based on dependency distance.

Usage:
    roadmap context <task-id>
    roadmap context <task-id> --mode summary
    roadmap context <task-id> --show-full
"""

import os
import sys
import argparse
from pathlib import Path
from collections import deque
from typing import Dict, List, Optional, Set, Tuple

# Add parent directory and roadmap-lib to path for imports
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))
sys.path.insert(0, str(scripts_dir / "roadmap-lib"))

from filesystem import find_roadmap_root, load_yaml
from cache import RoadmapCache


class ContextLoader:
    """Loads dependency context based on mode and distance."""

    def __init__(self, root_dir: Path, max_distance: int = 2, cache: Optional['RoadmapCache'] = None):
        self.root_dir = root_dir
        self.vibey_dir = root_dir / ".vibey"
        self.sprint_docs_dir = self.vibey_dir / "sprint_docs"
        self.sprints_dir = self.vibey_dir / "roadmap" / "sprints"
        self.tasks_dir = self.vibey_dir / "roadmap" / "tasks"
        self.max_distance = max_distance
        self.roadmap_cache = cache or RoadmapCache(root_dir)
        self.summary_cache = {}  # For caching summaries during session

    def load_context_for_task(self, task_id: str, show_full: bool = False) -> Dict:
        """Load all context needed for a task."""

        print(f"🔍 Loading context for task: {task_id}\n")

        # Find the task
        task = self._find_task(task_id)
        if not task:
            print(f"❌ Task not found: {task_id}")
            sys.exit(1)

        print(f"**Task:** {task['name']}")
        print(f"**Sprint:** {task['sprint_id']}")
        print(f"**Type:** {task.get('type', 'development')}\n")

        # Show dependency graph snapshot
        dep_graph = self.roadmap_cache.get_dependency_graph()
        direct_deps = dep_graph.get(task_id, [])

        print(f"📊 Dependency Graph Snapshot:")
        print(f"   Direct dependencies: {len(direct_deps)}")
        if direct_deps:
            for dep_id in direct_deps:
                print(f"     - {dep_id}")
        print(f"   Branch: {self.roadmap_cache.current_branch}")
        print(f"   Total objects in graph: {len(dep_graph)}\n")

        # Load current sprint docs (always full)
        current_sprint_context = self._load_current_sprint(task['sprint_id'])
        current_tokens = self._estimate_tokens(current_sprint_context)
        print(f"📄 Current Sprint Docs: ~{current_tokens:,} tokens")

        # Build dependency graph and loading plan
        if 'dependencies' not in task or not task['dependencies']:
            print(f"\n✅ No dependencies - context loading complete")
            print(f"   Total context: ~{current_tokens:,} tokens")
            return {
                'task': task,
                'current_sprint': current_sprint_context,
                'dependencies': {},
                'total_tokens': current_tokens
            }

        dep_graph = self._build_dependency_graph(task)
        loading_plan = self._create_loading_plan(dep_graph)

        print(f"\n📚 Dependency Analysis:")
        print(f"   Total dependencies: {len(loading_plan)}")

        # Load dependencies by mode
        dependencies_context = {}
        dep_tokens = 0

        for entry in loading_plan:
            context = self._load_dependency_context(entry)
            dependencies_context[entry['task_id']] = context
            dep_tokens += self._estimate_tokens(context)

            mode_symbol = {
                'minimal': '⚪',
                'summary': '🔵',
                'full': '🟢'
            }.get(entry['mode'], '⚪')

            print(f"   {mode_symbol} {entry['task_id']} ({entry['mode']}) ~{self._estimate_tokens(context)} tokens")

        total_tokens = current_tokens + dep_tokens

        print(f"\n📊 Context Summary:")
        print(f"   Current sprint: ~{current_tokens:,} tokens")
        print(f"   Dependencies: ~{dep_tokens:,} tokens")
        print(f"   Total: ~{total_tokens:,} tokens")

        if show_full:
            self._display_full_context(task, current_sprint_context, dependencies_context)

        return {
            'task': task,
            'current_sprint': current_sprint_context,
            'dependencies': dependencies_context,
            'total_tokens': total_tokens
        }

    def _find_task(self, task_id: str) -> Optional[Dict]:
        """Find task by ID."""

        if not self.tasks_dir.exists():
            return None

        for task_file in self.tasks_dir.glob("*-tasks.yaml"):
            tasks_data = load_yaml(task_file)
            if tasks_data and 'tasks' in tasks_data:
                for task in tasks_data['tasks']:
                    if task['id'] == task_id:
                        return task

        return None

    def _load_current_sprint(self, sprint_id: str) -> Dict:
        """Load full documentation for current sprint."""

        context = {
            'mode': 'full',
            'sprint_id': sprint_id,
            'docs': {}
        }

        sprint_docs_path = self.sprint_docs_dir / sprint_id
        if sprint_docs_path.exists():
            for doc_name in ['plan.md', 'architecture.md', 'progress.md', 'lessons.md']:
                doc_path = sprint_docs_path / doc_name
                if doc_path.exists():
                    context['docs'][doc_name.replace('.md', '')] = doc_path.read_text()

        return context

    def _build_dependency_graph(self, task: Dict) -> Dict[str, Dict]:
        """Build dependency graph with distances."""

        graph = {}
        visited: Set[str] = set()
        queue = deque([(task, 0)])

        while queue:
            current_task, distance = queue.popleft()
            task_id = current_task['id']

            if task_id in visited:
                continue

            visited.add(task_id)

            # Skip if beyond max distance
            if distance > self.max_distance:
                continue

            # Store dependency info
            if distance > 0:  # Don't include current task
                graph[task_id] = {
                    'task': current_task,
                    'distance': distance,
                    'mode': self._select_context_mode(distance, current_task)
                }

            # Process dependencies
            if 'dependencies' in current_task:
                for dep in current_task['dependencies']:
                    if dep['type'] == 'task':
                        dep_task = self._find_task(dep['target_id'])
                        if dep_task:
                            queue.append((dep_task, distance + 1))

        return graph

    def _select_context_mode(self, distance: int, task: Dict) -> str:
        """Select context mode based on distance."""

        # Check for user override in dependency
        # (Future enhancement: support user-specified context_mode in dependencies)

        # Distance-based default
        if distance == 1:
            return "summary"  # Direct dependencies
        elif distance == 2:
            return "minimal"  # One step removed
        else:
            return "minimal"  # Deep dependencies

    def _create_loading_plan(self, graph: Dict[str, Dict]) -> List[Dict]:
        """Create optimized loading plan from dependency graph."""

        # Convert graph to list, sorted by distance
        plan = []
        for task_id, info in graph.items():
            plan.append({
                'task_id': task_id,
                'task': info['task'],
                'distance': info['distance'],
                'mode': info['mode']
            })

        # Sort by distance (closer first)
        plan.sort(key=lambda x: x['distance'])

        return plan

    def _load_dependency_context(self, entry: Dict) -> Dict:
        """Load context for a single dependency based on mode."""

        mode = entry['mode']
        task_id = entry['task_id']

        if mode == "minimal":
            return self._load_minimal(task_id, entry['task'])
        elif mode == "summary":
            return self._load_summary(task_id, entry['task'])
        elif mode == "full":
            return self._load_full(task_id, entry['task'])
        else:
            return {}

    def _load_minimal(self, task_id: str, task: Dict) -> Dict:
        """Load minimal context (outputs only)."""

        sprint_id = task['sprint_id']

        # Load sprint YAML to get task summary
        sprint_path = self.sprints_dir / f"{sprint_id}.yaml"
        sprint_data = load_yaml(sprint_path)
        sprint = sprint_data.get('sprint', {}) if sprint_data else {}

        task_summary = sprint.get('task_summaries', {}).get(task_id, {})

        return {
            'mode': 'minimal',
            'sprint_id': sprint_id,
            'sprint_name': sprint.get('name', 'Unknown'),
            'sprint_status': sprint.get('status', 'unknown'),
            'outputs': task_summary.get('outputs', []),
            'task_name': task['name']
        }

    def _load_summary(self, task_id: str, task: Dict) -> Dict:
        """Load summary context."""

        # Use cache if enabled
        if self.cache and task_id in self.summary_cache:
            return self.summary_cache[task_id]

        sprint_id = task['sprint_id']

        # Load sprint YAML
        sprint_path = self.sprints_dir / f"{sprint_id}.yaml"
        sprint_data = load_yaml(sprint_path)
        sprint = sprint_data.get('sprint', {}) if sprint_data else {}

        context = {
            'mode': 'summary',
            'sprint_id': sprint_id,
            'sprint_name': sprint.get('name', 'Unknown'),
            'sprint_summary': sprint.get('dependency_summary', 'No summary available'),
            'task_summary': sprint.get('task_summaries', {}).get(task_id, {}),
            'task_name': task['name']
        }

        if self.cache:
            self.summary_cache[task_id] = context

        return context

    def _load_full(self, task_id: str, task: Dict) -> Dict:
        """Load full context (all sprint docs)."""

        sprint_id = task['sprint_id']

        # Load sprint YAML
        sprint_path = self.sprints_dir / f"{sprint_id}.yaml"
        sprint_data = load_yaml(sprint_path)
        sprint = sprint_data.get('sprint', {}) if sprint_data else {}

        # Load sprint docs
        docs = {}
        sprint_docs_path = self.sprint_docs_dir / sprint_id
        if sprint_docs_path.exists():
            for doc_name in ['plan.md', 'architecture.md', 'progress.md', 'lessons.md']:
                doc_path = sprint_docs_path / doc_name
                if doc_path.exists():
                    docs[doc_name.replace('.md', '')] = doc_path.read_text()

        return {
            'mode': 'full',
            'sprint_id': sprint_id,
            'sprint_name': sprint.get('name', 'Unknown'),
            'sprint_summary': sprint.get('dependency_summary', ''),
            'task_summary': sprint.get('task_summaries', {}).get(task_id, {}),
            'sprint_docs': docs,
            'task_name': task['name']
        }

    def _estimate_tokens(self, context: Dict) -> int:
        """Estimate token count for context."""

        total = 0

        if 'docs' in context:
            for doc in context['docs'].values():
                total += len(doc.split()) * 1.3  # Rough token estimate

        if 'sprint_docs' in context:
            for doc in context['sprint_docs'].values():
                total += len(doc.split()) * 1.3

        if 'sprint_summary' in context:
            total += len(str(context['sprint_summary']).split()) * 1.3

        if 'task_summary' in context:
            summary_str = str(context['task_summary'])
            total += len(summary_str.split()) * 1.3

        return int(total)

    def _display_full_context(self, task: Dict, current_sprint: Dict, dependencies: Dict) -> None:
        """Display full context details."""

        print(f"\n" + "=" * 80)
        print(f"FULL CONTEXT FOR TASK: {task['id']}")
        print(f"=" * 80)

        print(f"\n📄 CURRENT SPRINT: {task['sprint_id']}")
        print("-" * 80)
        if 'docs' in current_sprint:
            for doc_name, content in current_sprint['docs'].items():
                print(f"\n### {doc_name.upper()} ###")
                print(content[:500] + "..." if len(content) > 500 else content)

        print(f"\n\n📚 DEPENDENCIES ({len(dependencies)} total)")
        print("-" * 80)
        for task_id, context in dependencies.items():
            print(f"\n### {task_id} ({context['mode'].upper()}) ###")
            print(f"Sprint: {context['sprint_id']} - {context['sprint_name']}")

            if context['mode'] == 'minimal':
                print(f"Outputs: {context.get('outputs', [])}")

            elif context['mode'] == 'summary':
                print(f"\n{context.get('sprint_summary', 'No summary')}")

            elif context['mode'] == 'full':
                if 'sprint_docs' in context:
                    for doc_name, content in context['sprint_docs'].items():
                        print(f"\n{doc_name}:")
                        print(content[:300] + "..." if len(content) > 300 else content)


def main():
    parser = argparse.ArgumentParser(
        description="Load and analyze context for a task"
    )
    parser.add_argument(
        'task_id',
        help="Task ID to load context for"
    )
    parser.add_argument(
        '--mode',
        choices=['minimal', 'summary', 'full'],
        help="Force specific context mode for all dependencies"
    )
    parser.add_argument(
        '--show-full',
        action='store_true',
        help="Display full context details"
    )
    parser.add_argument(
        '--max-distance',
        type=int,
        default=2,
        help="Maximum dependency distance to load (default: 2)"
    )
    parser.add_argument(
        '--dir',
        type=str,
        help="Root directory (default: find via .vibey/)"
    )

    args = parser.parse_args()

    # Find roadmap root
    if args.dir:
        root_dir = Path(args.dir)
    else:
        root_dir = find_roadmap_root()

    if not root_dir:
        print("❌ No roadmap found. Run 'roadmap init' first.")
        sys.exit(1)

    loader = ContextLoader(root_dir, max_distance=args.max_distance)
    context = loader.load_context_for_task(args.task_id, show_full=args.show_full)


if __name__ == '__main__':
    main()
