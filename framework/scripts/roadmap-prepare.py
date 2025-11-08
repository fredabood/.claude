#!/usr/bin/env python3
"""
Roadmap Preparation Mode

Generates task-specific preparation documents by deeply analyzing all dependencies.
Uses full context window for comprehensive analysis before complex task execution.

Usage:
    roadmap prepare <task-id>
    roadmap prepare <task-id> --regenerate
    roadmap prepare <task-id> --show
"""

import os
import sys
import yaml
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directory and roadmap-lib to path for imports
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))
sys.path.insert(0, str(scripts_dir / "roadmap-lib"))

from filesystem import find_roadmap_root, load_yaml, save_yaml
from cache import RoadmapCache


class PreparationMode:
    """Deep dependency analysis for complex tasks."""

    def __init__(self, root_dir: Path, cache: Optional['RoadmapCache'] = None):
        self.root_dir = root_dir
        self.vibey_dir = root_dir / ".vibey"
        self.sprint_docs_dir = self.vibey_dir / "sprint_docs"
        self.cache = cache or RoadmapCache(root_dir)

    def prepare_task(self, task_id: str, regenerate: bool = False, show: bool = False) -> None:
        """Generate or show preparation document for task."""

        # Find the task
        task_data = self._find_task(task_id)
        if not task_data:
            print(f"❌ Task not found: {task_id}")
            sys.exit(1)

        sprint_id = task_data['sprint_id']

        # Show existing prep doc if requested
        if show:
            self._show_prep_doc(sprint_id, task_id)
            return

        # Check if prep doc already exists
        prep_path = self._get_prep_path(sprint_id, task_id)
        if prep_path.exists() and not regenerate:
            print(f"📄 Preparation document already exists: {prep_path}")
            print(f"   Use --regenerate to recreate")
            print(f"   Use --show to view")
            print(f"\n   cat {prep_path}")
            return

        # Generate preparation document
        print(f"🔍 Analyzing task: {task_data['name']}")
        print(f"   ID: {task_id}")

        # Load all dependencies
        dependencies = self._load_all_dependencies(task_data)

        if not dependencies:
            print(f"⚠️  No dependencies found - preparation mode most useful for tasks with 5+ dependencies")
            response = input("Continue anyway? (y/n): ")
            if response.lower() != 'y':
                return

        print(f"\n📚 Loading dependency documentation...")
        print(f"   Dependencies: {len(dependencies)}")

        dep_docs = self._load_dependency_docs(dependencies)

        # Estimate context size
        total_tokens = sum(len(str(doc).split()) * 1.3 for doc in dep_docs.values())
        print(f"   Context size: ~{int(total_tokens):,} tokens")

        # Generate preparation prompt
        print(f"\n🤖 Generating preparation document...")
        print(f"   This may take 30-60 seconds...")

        prep_doc = self._generate_prep_document(task_data, dep_docs)

        # Save preparation document
        prep_path.parent.mkdir(parents=True, exist_ok=True)
        prep_path.write_text(prep_doc)

        # Update task metadata
        self._update_task_metadata(task_id, prep_path, len(dependencies), int(total_tokens))

        print(f"\n✅ Preparation document created: {prep_path}")
        print(f"   Dependencies analyzed: {len(dependencies)}")
        print(f"   Context used: ~{int(total_tokens):,} tokens")
        print(f"\n📖 Read before starting task:")
        print(f"   cat {prep_path}")
        print(f"\n💡 Reference this document during task execution")

    def _find_task(self, task_id: str) -> Optional[Dict]:
        """Find task by ID in task files."""

        tasks_dir = self.vibey_dir / "roadmap" / "tasks"
        if not tasks_dir.exists():
            return None

        for task_file in tasks_dir.glob("*-tasks.yaml"):
            tasks_data = load_yaml(task_file)
            if tasks_data and 'tasks' in tasks_data:
                for task in tasks_data['tasks']:
                    if task['id'] == task_id:
                        return task

        return None

    def _get_prep_path(self, sprint_id: str, task_id: str) -> Path:
        """Get path for preparation document."""

        # Extract task number from ID (e.g., "backend-1-task-007" -> "task-007")
        task_num = task_id.split('-task-')[-1] if '-task-' in task_id else task_id

        prep_dir = self.sprint_docs_dir / sprint_id / "prep"
        return prep_dir / f"task-{task_num}.md"

    def _show_prep_doc(self, sprint_id: str, task_id: str) -> None:
        """Display existing preparation document."""

        prep_path = self._get_prep_path(sprint_id, task_id)

        if not prep_path.exists():
            print(f"❌ No preparation document found for {task_id}")
            print(f"   Run: roadmap prepare {task_id}")
            sys.exit(1)

        print(prep_path.read_text())

    def _load_all_dependencies(self, task: Dict) -> List[Dict]:
        """Load all dependencies (direct and transitive)."""

        dependencies = []
        visited = set()

        def load_deps(current_task: Dict):
            task_id = current_task['id']
            if task_id in visited:
                return
            visited.add(task_id)

            if 'dependencies' in current_task:
                for dep in current_task['dependencies']:
                    if dep['type'] == 'task':
                        dep_task = self._find_task(dep['target_id'])
                        if dep_task:
                            dependencies.append({
                                'task': dep_task,
                                'type': dep['type'],
                                'reason': dep.get('reason', '')
                            })
                            # Recursively load transitive dependencies
                            load_deps(dep_task)

        load_deps(task)
        return dependencies

    def _load_dependency_docs(self, dependencies: List[Dict]) -> Dict[str, Dict]:
        """Load all documentation for dependencies."""

        dep_docs = {}

        for dep in dependencies:
            task = dep['task']
            sprint_id = task['sprint_id']

            # Load sprint docs
            sprint_docs_path = self.sprint_docs_dir / sprint_id

            if not sprint_docs_path.exists():
                continue

            docs = {}

            # Load standard sprint docs
            for doc_name in ['plan.md', 'architecture.md', 'progress.md', 'lessons.md']:
                doc_path = sprint_docs_path / doc_name
                if doc_path.exists():
                    docs[doc_name.replace('.md', '')] = doc_path.read_text()

            if docs:
                dep_docs[sprint_id] = {
                    'sprint_id': sprint_id,
                    'task': task,
                    'docs': docs,
                    'reason': dep['reason']
                }

        return dep_docs

    def _generate_prep_document(self, task: Dict, dep_docs: Dict) -> str:
        """Generate preparation document (currently uses template, will use Claude API)."""

        # For now, generate a structured template
        # TODO: Replace with actual Claude API call

        # Load dependency graph snapshot
        dep_graph = self.cache.get_dependency_graph()
        task_id = task['id']
        direct_deps = dep_graph.get(task_id, [])

        # Get all dependencies loaded (for audit trail)
        all_loaded_deps = list(dep_docs.keys())

        prep_doc = f"""# Task Preparation: {task['name']}
# Task ID: {task['id']}
# Generated: {datetime.now().isoformat()}

## Task Overview

**Task:** {task['name']}

**Description:** {task.get('description', 'No description provided')}

**Estimated Duration:** {task.get('estimated_duration', 'Not specified')}

**Type:** {task.get('type', 'development')}

---

## Dependency Graph Snapshot

**Captured at preparation time for audit/reproducibility.**

**Direct Dependencies:** {len(direct_deps)}
{chr(10).join(f"  - {dep_id}" for dep_id in direct_deps)}

**Transitive Dependencies Loaded:** {len(all_loaded_deps)}
{chr(10).join(f"  - {dep_id}" for dep_id in all_loaded_deps)}

**Graph Metadata:**
  - Branch: {self.cache.current_branch}
  - Timestamp: {datetime.now().isoformat()}
  - Total dependency objects in graph: {len(dep_graph)}

---

## Dependencies Analyzed

This preparation document analyzes {len(dep_docs)} sprint dependencies to help you implement this task successfully.

"""

        # Add dependency analysis
        for idx, (sprint_id, dep_data) in enumerate(dep_docs.items(), 1):
            task_dep = dep_data['task']
            docs = dep_data['docs']

            prep_doc += f"""
### {idx}. {sprint_id}: {task_dep['name']}

**Why this dependency matters:**
{dep_data.get('reason', 'Dependency relationship')}

**What it provides:**
"""

            # Extract key information from plan
            if 'plan' in docs:
                prep_doc += f"""
*From sprint plan:*
{self._extract_key_sections(docs['plan'], ['Goals', 'Features', 'What'])}
"""

            # Extract architecture decisions
            if 'architecture' in docs:
                prep_doc += f"""
**Architecture & Design:**
{self._extract_key_sections(docs['architecture'], ['Design', 'Architecture', 'Decisions'])}
"""

            # Extract learnings
            if 'progress' in docs:
                prep_doc += f"""
**Key Learnings:**
{self._extract_learnings(docs['progress'])}
"""

            if 'lessons' in docs:
                prep_doc += f"""
**Lessons Learned:**
{self._extract_key_sections(docs['lessons'], ['What Went', 'Key Learning', 'Recommendations'])}
"""

            prep_doc += "\n---\n"

        # Add integration guidance
        prep_doc += """
## Critical Integration Points

**Review the dependency analysis above and consider:**

1. **Integration Flow** - What is the correct sequence for using these dependencies?
2. **Error Handling** - How should errors from dependencies be handled?
3. **Data Flow** - What data needs to pass between this task and dependencies?
4. **Side Effects** - What side effects do dependency functions have?

---

## Implementation Checklist

**Before starting:**
- [ ] Review all dependency documentation above
- [ ] Understand integration patterns
- [ ] Identify potential conflicts
- [ ] Set up development environment

**During implementation:**
- [ ] Follow integration patterns from dependencies
- [ ] Handle errors appropriately
- [ ] Add logging with context
- [ ] Test integration points
- [ ] Reference gotchas from dependency learnings

**After implementation:**
- [ ] Integration tests with dependencies
- [ ] Error scenario testing
- [ ] Update sprint docs with learnings
- [ ] Document any new patterns discovered

---

## Questions to Resolve

Before starting implementation, clarify any uncertainties:

1. Are there any conflicting patterns between dependencies?
2. What error handling strategy should be used?
3. Are there performance considerations from dependencies?
4. What testing approach is needed?

---

## References

**Dependency documentation:**
"""

        for sprint_id in dep_docs.keys():
            prep_doc += f"- `.vibey/sprint_docs/{sprint_id}/` - Full sprint documentation\n"

        prep_doc += """
---

**💡 This preparation document was generated by analyzing all dependency documentation.**

**Use this as your primary reference during task implementation.**

**Update `.vibey/sprint_docs/{}/progress.md` with any new learnings as you work.**
""".format(task['sprint_id'])

        return prep_doc

    def _extract_key_sections(self, text: str, keywords: List[str]) -> str:
        """Extract sections containing keywords."""

        lines = text.split('\n')
        extracted = []
        in_section = False
        section_lines = []

        for line in lines:
            # Check if this is a header with a keyword
            is_header = line.startswith('#')
            has_keyword = any(kw.lower() in line.lower() for kw in keywords)

            if is_header and has_keyword:
                # Save previous section
                if section_lines:
                    extracted.append('\n'.join(section_lines))
                    section_lines = []
                in_section = True
                section_lines.append(line)
            elif is_header and in_section:
                # New section, stop capturing
                if section_lines:
                    extracted.append('\n'.join(section_lines))
                    section_lines = []
                in_section = False
            elif in_section:
                section_lines.append(line)

        # Add final section
        if section_lines:
            extracted.append('\n'.join(section_lines))

        return '\n\n'.join(extracted) if extracted else "No relevant sections found."

    def _extract_learnings(self, progress_text: str) -> str:
        """Extract learning/issue sections from progress."""

        lines = progress_text.split('\n')
        learnings = []

        for line in lines:
            lower = line.lower()
            if any(kw in lower for kw in ['learning:', 'learned:', 'issue:', 'problem:', 'gotcha:', 'mistake:']):
                learnings.append(line.strip())

        return '\n'.join(learnings) if learnings else "No specific learnings documented."

    def _update_task_metadata(self, task_id: str, prep_path: Path, dep_count: int, tokens: int) -> None:
        """Update task with preparation metadata."""

        tasks_dir = self.vibey_dir / "roadmap" / "tasks"

        for task_file in tasks_dir.glob("*-tasks.yaml"):
            tasks_data = load_yaml(task_file)
            if not tasks_data or 'tasks' not in tasks_data:
                continue

            modified = False
            for task in tasks_data['tasks']:
                if task['id'] == task_id:
                    # Add preparation metadata
                    task['preparation'] = {
                        'document': str(prep_path.relative_to(self.vibey_dir)),
                        'generated': datetime.now().isoformat(),
                        'dependencies_analyzed': dep_count,
                        'context_tokens': tokens,
                        'model_used': 'template-based'  # Will be 'claude-sonnet-4-5' when API integrated
                    }
                    modified = True
                    break

            if modified:
                save_yaml(task_file, tasks_data)
                break


def main():
    parser = argparse.ArgumentParser(
        description="Generate task preparation documents by analyzing dependencies"
    )
    parser.add_argument(
        'task_id',
        nargs='?',
        help="Task ID to prepare"
    )
    parser.add_argument(
        '--regenerate',
        action='store_true',
        help="Regenerate preparation document even if it exists"
    )
    parser.add_argument(
        '--show',
        action='store_true',
        help="Show existing preparation document"
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help="List all tasks with preparation documents"
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

    prep_mode = PreparationMode(root_dir)

    # List mode
    if args.list:
        print("📋 Tasks with preparation documents:")
        # TODO: Implement list functionality
        print("   (Not yet implemented)")
        return

    # Require task_id for other operations
    if not args.task_id:
        parser.print_help()
        sys.exit(1)

    # Generate or show preparation document
    prep_mode.prepare_task(args.task_id, regenerate=args.regenerate, show=args.show)


if __name__ == '__main__':
    main()
