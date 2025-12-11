"""
Roadmap Summary Generator

Auto-generates dependency summaries and task summaries for completed sprints.
These summaries enable efficient context loading for dependent tasks.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional

from vibey.cli.roadmap_lib.filesystem import find_roadmap_root, load_yaml, save_yaml, FileSystemManager


class SummaryGenerator:
    """Generates dependency and task summaries from sprint documentation."""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.vibey_dir = root_dir / ".vibey"
        self.sprint_docs_dir = self.vibey_dir / "sprint_docs"
        # Use FileSystemManager for hierarchical paths
        self.fs = FileSystemManager(root_dir)

    def summarize_sprint(self, sprint_id: str, force: bool = False) -> bool:
        """
        Generate dependency summary for a sprint.

        Args:
            sprint_id: Sprint ID to summarize
            force: Force regeneration even if summary exists

        Returns:
            True if successful
        """
        print(f"📊 Generating summary for sprint: {sprint_id}")

        # Load sprint YAML using FileSystemManager for hierarchical structure
        sprint_path = self.fs.get_sprint_path(sprint_id)
        if not sprint_path.exists():
            print(f"❌ Sprint file not found: {sprint_path}")
            return False

        sprint_data = load_yaml(sprint_path)
        if not sprint_data or 'sprint' not in sprint_data:
            print(f"❌ Invalid sprint data in {sprint_path}")
            return False

        sprint = sprint_data['sprint']

        # Check if summary already exists
        if 'dependency_summary' in sprint and sprint['dependency_summary'] and not force:
            print(f"   Summary already exists (use --force to regenerate)")
            return True

        # Load sprint documentation
        sprint_docs_path = self.sprint_docs_dir / sprint_id
        if not sprint_docs_path.exists():
            print(f"⚠️  No sprint documentation found at {sprint_docs_path}")
            print(f"   Creating minimal summary from sprint YAML only")
            summary = self._generate_minimal_summary(sprint)
        else:
            docs = self._load_sprint_docs(sprint_docs_path)
            summary = self._generate_dependency_summary(sprint, docs)

        # Update sprint YAML
        sprint['dependency_summary'] = summary
        save_yaml(sprint_path, sprint_data)

        print(f"✅ Dependency summary generated ({len(summary.split())} words)")
        print(f"   Saved to: {sprint_path}")
        return True

    def summarize_task(self, sprint_id: str, task_id: str, force: bool = False) -> bool:
        """
        Generate task-level summary.

        Args:
            sprint_id: Sprint ID containing the task
            task_id: Task ID to summarize
            force: Force regeneration even if summary exists

        Returns:
            True if successful
        """
        print(f"📝 Generating task summary: {task_id}")

        # Find task in hierarchical structure
        tasks_dir = self._find_task_file(task_id)
        if not tasks_dir:
            print(f"❌ Task not found: {task_id}")
            return False

        # Load tasks using load_tasks which handles hierarchical structure
        from vibey.roadmap.serialization import load_tasks
        tasks = load_tasks(tasks_dir)
        if not tasks:
            print(f"❌ No tasks found in {tasks_dir}")
            return False

        # Find the specific task
        task = None
        for t in tasks:
            if t.id == task_id:
                task = t
                break

        if not task:
            print(f"❌ Task {task_id} not found in {tasks_dir}")
            return False

        # Load sprint YAML to update task_summaries using FileSystemManager
        sprint_path = self.fs.get_sprint_path(sprint_id)
        if not sprint_path.exists():
            print(f"❌ Sprint file not found: {sprint_path}")
            return False

        sprint_data = load_yaml(sprint_path)
        sprint = sprint_data['sprint']

        # Initialize task_summaries if needed
        if 'task_summaries' not in sprint:
            sprint['task_summaries'] = {}

        # Check if summary exists
        if task_id in sprint['task_summaries'] and not force:
            print(f"   Summary already exists (use --force to regenerate)")
            return True

        # Generate task summary
        sprint_docs_path = self.sprint_docs_dir / sprint_id
        docs = self._load_sprint_docs(sprint_docs_path) if sprint_docs_path.exists() else {}

        task_summary = self._generate_task_summary(task, docs)

        # Update sprint YAML
        sprint['task_summaries'][task_id] = task_summary
        save_yaml(sprint_path, sprint_data)

        print(f"✅ Task summary generated")
        print(f"   Saved to: {sprint_path}")
        return True

    def summarize_all_completed(self) -> int:
        """
        Generate summaries for all completed sprints.

        Returns:
            Number of sprints summarized
        """
        print(f"🔄 Generating summaries for all completed sprints...")

        roadmap_root = self.vibey_dir / "roadmap"
        if not roadmap_root.exists():
            print(f"❌ No roadmap directory found")
            return 0

        completed_count = 0

        # Iterate through flat sprints/ directory
        sprints_dir = roadmap_root / "sprints"
        if not sprints_dir.exists():
            print(f"❌ No sprints directory found")
            return 0

        for sprint_file in sprints_dir.glob("*.yaml"):
            if sprint_file.name.startswith('.'):
                continue

            sprint_data = load_yaml(sprint_file)
            if not sprint_data or 'sprint' not in sprint_data:
                continue

            sprint = sprint_data['sprint']
            if sprint.get('status') == 'completed':
                sprint_id = sprint['id']
                print(f"\n📊 {sprint_id}: {sprint['name']}")
                try:
                    if self.summarize_sprint(sprint_id, force=False):
                        completed_count += 1
                except Exception as e:
                    print(f"   ❌ Error: {e}")

        print(f"\n✅ Generated summaries for {completed_count} completed sprints")
        return completed_count

    def _load_sprint_docs(self, sprint_docs_path: Path) -> Dict[str, str]:
        """Load all documentation files for a sprint."""

        docs = {}
        for doc_name in ['plan.md', 'architecture.md', 'progress.md', 'lessons.md']:
            doc_path = sprint_docs_path / doc_name
            if doc_path.exists():
                docs[doc_name.replace('.md', '')] = doc_path.read_text()

        return docs

    def _generate_minimal_summary(self, sprint: Dict) -> str:
        """Generate minimal summary from sprint YAML only."""

        return f"""This sprint: {sprint.get('name', 'Unnamed sprint')}

Status: {sprint.get('status', 'unknown')}

{sprint.get('description', 'No description available')}

Note: Full sprint documentation not available. This is a minimal summary generated from sprint metadata only.
"""

    def _generate_dependency_summary(self, sprint: Dict, docs: Dict) -> str:
        """Generate comprehensive dependency summary from sprint docs."""

        summary_parts = []

        # Header
        summary_parts.append(f"This sprint implemented: {sprint['name']}\n")

        # Extract goals from plan
        if 'plan' in docs:
            goals = self._extract_section(docs['plan'], ['## Goals', '## Objectives'])
            if goals:
                summary_parts.append("**Goals Achieved:**")
                summary_parts.append(goals)
                summary_parts.append("")

        # Extract key outputs
        outputs = self._extract_outputs(docs)
        if outputs:
            summary_parts.append("**Key Outputs:**")
            for output in outputs[:5]:  # Top 5
                summary_parts.append(f"- {output}")
            summary_parts.append("")

        # Extract interfaces/APIs
        interfaces = self._extract_interfaces(docs)
        if interfaces:
            summary_parts.append("**Key Interfaces:**")
            for interface in interfaces[:3]:  # Top 3
                summary_parts.append(f"- {interface}")
            summary_parts.append("")

        # Extract learnings
        learnings = self._extract_learnings(docs)
        if learnings:
            summary_parts.append("**Critical Learnings:**")
            for learning in learnings[:3]:  # Top 3
                summary_parts.append(f"- {learning}")
            summary_parts.append("")

        # Add reference to full docs
        summary_parts.append(f"**For dependencies:** Use the outputs and interfaces listed above.")
        summary_parts.append(f"**Full context:** See `.vibey/sprint_docs/{sprint['id']}/`")

        return "\n".join(summary_parts)

    def _generate_task_summary(self, task: Dict, docs: Dict) -> Dict:
        """Generate task-level summary."""

        summary = {
            'summary': task.get('description', task['name']),
            'outputs': [],
            'interfaces': [],
            'gotchas': []
        }

        # Extract task-specific info from progress.md
        if 'progress' in docs:
            # Look for task mentions
            task_sections = self._find_task_sections(docs['progress'], task['id'], task['name'])

            # Extract outputs from task sections
            outputs = self._extract_outputs_from_text(task_sections)
            summary['outputs'] = outputs[:5]  # Top 5

            # Extract gotchas/learnings
            gotchas = self._extract_gotchas_from_text(task_sections)
            summary['gotchas'] = gotchas[:3]  # Top 3

        # Extract interfaces from architecture
        if 'architecture' in docs:
            interfaces = self._extract_interfaces_from_text(docs['architecture'], task['name'])
            summary['interfaces'] = interfaces[:3]  # Top 3

        # Add reference to full context
        summary['full_context'] = f"sprint_docs/{task['sprint_id']}/"

        return summary

    def _extract_section(self, text: str, headers: List[str]) -> str:
        """Extract content from first matching section header."""

        lines = text.split('\n')
        in_section = False
        section_lines = []

        for line in lines:
            # Check if this is a matching header
            if any(header in line for header in headers):
                in_section = True
                continue
            # Check if we hit another header (stop)
            elif line.startswith('##') and in_section:
                break
            elif in_section:
                section_lines.append(line)

        return '\n'.join(section_lines).strip()

    def _extract_outputs(self, docs: Dict) -> List[str]:
        """Extract key outputs from documentation."""

        outputs = []

        # Look in plan for features/deliverables
        if 'plan' in docs:
            features_section = self._extract_section(docs['plan'], ['## Features', '## Deliverables'])
            if features_section:
                # Extract bullet points
                for line in features_section.split('\n'):
                    if line.strip().startswith('-') or line.strip().startswith('*'):
                        outputs.append(line.strip().lstrip('-*').strip())

        # Look in progress for completed items
        if 'progress' in docs:
            for line in docs['progress'].split('\n'):
                if '✅' in line or 'completed' in line.lower():
                    clean = line.replace('✅', '').strip()
                    if clean and len(clean) < 100:
                        outputs.append(clean)

        return outputs

    def _extract_interfaces(self, docs: Dict) -> List[str]:
        """Extract API/interface definitions."""

        interfaces = []

        if 'architecture' in docs:
            arch = docs['architecture']

            # Look for function signatures, API endpoints
            patterns = [
                r'def\s+(\w+)\([^)]*\)',  # Python functions
                r'(POST|GET|PUT|DELETE)\s+(/[\w/]+)',  # HTTP endpoints
                r'function\s+(\w+)\(',  # JavaScript functions
                r'class\s+(\w+)',  # Classes
            ]

            for pattern in patterns:
                matches = re.findall(pattern, arch)
                for match in matches:
                    if isinstance(match, tuple):
                        interfaces.append(' '.join(match))
                    else:
                        interfaces.append(match)

        return interfaces

    def _extract_learnings(self, docs: Dict) -> List[str]:
        """Extract key learnings and gotchas."""

        learnings = []

        if 'progress' in docs:
            for line in docs['progress'].split('\n'):
                lower = line.lower()
                if any(kw in lower for kw in ['learning:', 'learned:', 'gotcha:', 'issue:', 'mistake:']):
                    clean = re.sub(r'\*\*[^*]+:\*\*', '', line).strip()
                    if clean and len(clean) < 150:
                        learnings.append(clean)

        if 'lessons' in docs:
            lessons_section = self._extract_section(docs['lessons'], ['## Key Learning', '## What Didn'])
            if lessons_section:
                for line in lessons_section.split('\n'):
                    if line.strip().startswith('-') or line.strip().startswith('*'):
                        learnings.append(line.strip().lstrip('-*').strip())

        return learnings

    def _find_task_sections(self, text: str, task_id: str, task_name: str) -> str:
        """Find sections of text mentioning a specific task."""

        sections = []
        lines = text.split('\n')

        for i, line in enumerate(lines):
            if task_id in line or task_name.lower() in line.lower():
                # Get surrounding context (5 lines before and after)
                start = max(0, i - 5)
                end = min(len(lines), i + 6)
                sections.append('\n'.join(lines[start:end]))

        return '\n\n'.join(sections)

    def _extract_outputs_from_text(self, text: str) -> List[str]:
        """Extract outputs from text."""

        outputs = []
        for line in text.split('\n'):
            if '✅' in line or 'completed' in line.lower() or 'implemented' in line.lower():
                clean = line.replace('✅', '').strip()
                if clean and len(clean) < 100:
                    outputs.append(clean)

        return outputs

    def _extract_gotchas_from_text(self, text: str) -> List[str]:
        """Extract gotchas/learnings from text."""

        gotchas = []
        for line in text.split('\n'):
            lower = line.lower()
            if any(kw in lower for kw in ['gotcha:', 'issue:', 'problem:', 'learning:', 'avoid:']):
                clean = re.sub(r'\*\*[^*]+:\*\*', '', line).strip()
                if clean and len(clean) < 150:
                    gotchas.append(clean)

        return gotchas

    def _extract_interfaces_from_text(self, text: str, task_name: str) -> List[str]:
        """Extract interfaces relevant to a task."""

        interfaces = []
        # Simple extraction - look for code blocks near task mentions
        # This is a simplified version; real implementation would be more sophisticated

        return interfaces

    def _find_task_file(self, task_id: str) -> Optional[Path]:
        """Find the sprint directory containing a task in hierarchical structure."""

        # Extract sprint ID from task ID (e.g., user-management-1-auth-task-001 -> user-management-1-auth)
        parts = task_id.split('-task-')
        if len(parts) != 2:
            return None

        sprint_id = parts[0]

        # Use FileSystemManager to get tasks path (sprint directory in hierarchical structure)
        tasks_path = self.fs.get_tasks_path(sprint_id)
        if tasks_path.exists():
            return tasks_path

        return None


def summarize_sprint(
    sprint_id: str,
    force: bool = False,
    root_dir: Path = None
) -> int:
    """
    Generate dependency summary for a sprint.

    Args:
        sprint_id: Sprint ID to summarize
        force: Force regeneration even if summary exists
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

    generator = SummaryGenerator(root_dir)
    success = generator.summarize_sprint(sprint_id, force=force)

    return 0 if success else 1


def summarize_task(
    sprint_id: str,
    task_id: str,
    force: bool = False,
    root_dir: Path = None
) -> int:
    """
    Generate task-level summary.

    Args:
        sprint_id: Sprint ID containing the task
        task_id: Task ID to summarize
        force: Force regeneration even if summary exists
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

    generator = SummaryGenerator(root_dir)
    success = generator.summarize_task(sprint_id, task_id, force=force)

    return 0 if success else 1


def summarize_all_completed(root_dir: Path = None) -> int:
    """
    Generate summaries for all completed sprints.

    Args:
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

    generator = SummaryGenerator(root_dir)
    count = generator.summarize_all_completed()

    return 0 if count > 0 else 1
