"""
Roadmap Context Loader

Loads dependency context with configurable modes (minimal/summary/full).
Implements hierarchical loading based on dependency distance.
"""

from pathlib import Path
from collections import deque
from typing import Dict, List, Optional, Set

from vibey.cli.roadmap_lib.filesystem import find_roadmap_root, load_yaml
from vibey.cli.roadmap_lib.cache import RoadmapCache


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
            return None

        print(f"**Task:** {task.get('title', task.get('name', 'Unknown'))}")
        print(f"**Sprint:** {task['sprint_id']}")
        print(f"**Type:** {task.get('task_type', task.get('type', 'development'))}")

        # Show files to modify if present
        files_to_modify = task.get('files_to_modify', [])
        if files_to_modify:
            print(f"\n📝 Files to modify:")
            for file in files_to_modify:
                print(f"   - {file}")

        # Show quality requirements if present
        quality_reqs = task.get('quality_requirements', [])
        if quality_reqs:
            print(f"\n✅ Quality requirements:")
            for req in quality_reqs:
                print(f"   - {req}")

        print()  # Blank line before dependency graph

        # Show dependency graph snapshot
        dep_graph = self.roadmap_cache.get_dependency_graph()
        direct_deps = dep_graph.get(task_id, [])

        reverse_dep_graph = self.roadmap_cache.get_reverse_dependency_graph()
        direct_dependents = [dep_id for dep_id in reverse_dep_graph.get(task_id, []) if '-task-' in dep_id]

        print(f"📊 Dependency Graph Snapshot:")
        print(f"   Direct dependencies: {len(direct_deps)}")
        if direct_deps:
            for dep_id in direct_deps:
                print(f"     - {dep_id}")
        print(f"   Direct dependents (downstream): {len(direct_dependents)}")
        if direct_dependents:
            for dep_id in direct_dependents:
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

            # Still show downstream impact if requested
            if show_full:
                self._display_full_context(task, current_sprint_context, {})

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

        # Use cache to get all tasks (cache knows all task locations)
        for task in self.roadmap_cache.get_all_tasks():
            if task.get('id') == task_id:
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
                    # Handle both dict format (new) and string format (legacy)
                    if isinstance(dep, dict):
                        # New format: {"type": "task", "target_id": "task-001", ...}
                        if dep.get('type') == 'task':
                            dep_task = self._find_task(dep['target_id'])
                            if dep_task:
                                queue.append((dep_task, distance + 1))
                    elif isinstance(dep, str):
                        # Legacy format: "task-001"
                        dep_task = self._find_task(dep)
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
            'task_name': task.get('title', task.get('name', 'Unknown'))
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
            'task_name': task.get('title', task.get('name', 'Unknown'))
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
            'task_name': task.get('title', task.get('name', 'Unknown'))
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

    def _get_dependency_reason(self, dependent_task: Dict, dependency_id: str) -> str:
        """Get the reason why dependent_task depends on dependency_id."""

        if 'dependencies' in dependent_task:
            for dep in dependent_task['dependencies']:
                # Handle both dict format (new) and string format (legacy)
                if isinstance(dep, dict):
                    # New format: {"type": "task", "target_id": "task-001", "reason": "..."}
                    if dep.get('target_id') == dependency_id:
                        return dep.get('reason', 'Dependency relationship')
                elif isinstance(dep, str):
                    # Legacy format: "task-001"
                    if dep == dependency_id:
                        return 'Dependency relationship'

        return 'Depends on this task'

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

        # Show downstream impact (who depends on this task)
        reverse_dep_graph = self.roadmap_cache.get_reverse_dependency_graph()
        task_id = task['id']
        direct_dependents = [dep_id for dep_id in reverse_dep_graph.get(task_id, []) if '-task-' in dep_id]

        if direct_dependents:
            print(f"\n\n⚠️  DOWNSTREAM IMPACT ({len(direct_dependents)} tasks depend on this)")
            print("-" * 80)
            print("These tasks are blocked or affected by your work:")

            for idx, dependent_id in enumerate(direct_dependents, 1):
                dependent_task = self._find_task(dependent_id)
                if dependent_task:
                    task_name = dependent_task.get('title', dependent_task.get('name', 'Unknown'))
                    print(f"\n{idx}. {task_name} ({dependent_id})")
                    print(f"   Sprint: {dependent_task['sprint_id']}")
                    print(f"   Status: {dependent_task.get('status', 'unknown')}")

                    # Find reason from dependency
                    reason = self._get_dependency_reason(dependent_task, task_id)
                    print(f"   Why they depend on you: {reason}")


def get_task_context(
    task_id: str,
    show_full: bool = False,
    max_distance: int = 2,
    root_dir: Path = None
) -> int:
    """
    Load and analyze context for a task.

    Args:
        task_id: Task ID to load context for
        show_full: Display full context details
        max_distance: Maximum dependency distance to load
        root_dir: Root directory (auto-detected if None)

    Returns:
        Exit code (0 = success, 1 = error)
    """
    # Find roadmap root
    if root_dir is None:
        root_dir = find_roadmap_root()

    if not root_dir:
        print("❌ No roadmap found. Run 'roadmap init' first.")
        return 1

    loader = ContextLoader(root_dir, max_distance=max_distance)
    context = loader.load_context_for_task(task_id, show_full=show_full)

    return 0 if context else 1
