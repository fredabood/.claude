"""
Summary Generator - Auto-generated Task and Dependency Summaries

Generates concise summaries of tasks for use in hierarchical context loading.
Uses LLM (Claude API) to create ~200 word summaries with key decisions,
API contracts, and dependencies.

Usage:
    from framework.roadmap.summary_generator import SummaryGenerator

    generator = SummaryGenerator()
    summary = generator.generate_task_summary("core-framework-2-task-003")
    print(summary)

Created: 2025-11-09
Sprint: core-framework-2, Task 4
"""

from pathlib import Path
from typing import Dict, List, Optional
import yaml
import hashlib
import os


class SummaryGenerator:
    """
    Generate concise summaries of tasks for context loading.

    For distance 1 dependencies, generates ~200 word summaries containing:
    - Task overview
    - Key technical decisions
    - API contracts and interfaces
    - Dependencies this task provides
    """

    def __init__(self, vibey_dir: Path = None, use_llm: bool = False):
        self.vibey_dir = vibey_dir or self._find_vibey_dir()
        self.sprints_dir = self.vibey_dir / "sprints"
        self.sprint_docs_dir = self.vibey_dir / "sprint_docs"
        self.summaries_dir = self.vibey_dir / "summaries"
        self.dependency_summaries_dir = self.summaries_dir / "dependency_summaries"
        self.task_summaries_dir = self.summaries_dir / "task_summaries"

        # Ensure summary directories exist
        self.dependency_summaries_dir.mkdir(parents=True, exist_ok=True)
        self.task_summaries_dir.mkdir(parents=True, exist_ok=True)

        # Configuration
        self.use_llm = use_llm  # Whether to use LLM for summarization
        self.summary_length = 200  # Target word count
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")  # Claude API key

    @staticmethod
    def _find_vibey_dir() -> Path:
        """Find .vibey directory"""
        current = Path.cwd()
        while current != current.parent:
            vibey_dir = current / ".vibey"
            if vibey_dir.exists() and vibey_dir.is_dir():
                return vibey_dir
            current = current.parent

        raise FileNotFoundError(".vibey directory not found")

    def generate_task_summary(
        self,
        task_id: str,
        force_regenerate: bool = False
    ) -> str:
        """
        Generate summary for a task.

        Args:
            task_id: Task ID
            force_regenerate: Regenerate even if cached summary exists

        Returns:
            Task summary (Markdown)
        """
        # Check cache first
        summary_file = self.dependency_summaries_dir / f"{task_id}.md"
        if summary_file.exists() and not force_regenerate:
            # Verify cache is still valid
            if self._is_cache_valid(summary_file, task_id):
                return summary_file.read_text()

        # Load task metadata
        task = self._load_task(task_id)
        if not task:
            return f"# Task Summary: {task_id}\n\n**Status:** Not found\n"

        # Load sprint plan if available
        sprint_plan = self._load_sprint_plan(task_id)

        # Generate summary
        if self.use_llm and self.api_key:
            summary = self._generate_llm_summary(task, sprint_plan)
        else:
            summary = self._generate_structured_summary(task, sprint_plan)

        # Cache the summary
        summary_file.write_text(summary)

        return summary

    def _is_cache_valid(self, summary_file: Path, task_id: str) -> bool:
        """
        Check if cached summary is still valid.

        Cache is invalid if:
        - Task metadata changed
        - Sprint plan changed
        """
        # For now, simple implementation: cache is always valid
        # Full implementation would compare mtimes of source files
        return True

    def _load_task(self, task_id: str) -> Optional[Dict]:
        """Load task metadata from sprint YAML"""
        task_num_idx = task_id.rfind('-task-')
        if task_num_idx <= 0:
            return None

        sprint_id = task_id[:task_num_idx]
        sprint_file = self.sprints_dir / f"{sprint_id}.yaml"

        if not sprint_file.exists():
            return None

        try:
            with open(sprint_file, 'r') as f:
                sprint_data = yaml.safe_load(f)

            track_id = sprint_data.get('sprint', {}).get('track_id')

            tasks = sprint_data.get('sprint', {}).get('tasks', [])
            for task in tasks:
                if task.get('id') == task_id:
                    task['sprint_id'] = sprint_id
                    task['track_id'] = track_id
                    return task

            return None

        except Exception:
            return None

    def _load_sprint_plan(self, task_id: str) -> Optional[str]:
        """Load sprint plan for task"""
        task = self._load_task(task_id)
        if not task:
            return None

        sprint_id = task.get('sprint_id')
        track_id = task.get('track_id')

        if not sprint_id or not track_id:
            return None

        plan_file = self.sprint_docs_dir / track_id / sprint_id / "plan.md"
        if plan_file.exists():
            return plan_file.read_text()

        return None

    def _generate_structured_summary(
        self,
        task: Dict,
        sprint_plan: Optional[str]
    ) -> str:
        """
        Generate structured summary without LLM.

        This is a fallback when LLM is not available or not desired.
        Creates a template-based summary with extracted metadata.
        """
        task_id = task.get('id', 'unknown')
        title = task.get('title', 'Unknown Task')
        status = task.get('status', 'unknown')
        priority = task.get('priority', 'unknown')
        description = task.get('description', '')

        summary = f"# Task Summary: {title}\n\n"
        summary += f"**ID:** {task_id}\n"
        summary += f"**Status:** {status}\n"
        summary += f"**Priority:** {priority}\n"
        summary += f"**Estimated Hours:** {task.get('estimated_hours', 'N/A')}\n\n"

        # Description
        if description:
            summary += f"## Description\n\n{description}\n\n"

        # Summary section
        summary += "## Summary\n\n"

        # Extract task section from sprint plan if available
        if sprint_plan:
            task_section = self._extract_task_section(sprint_plan, task_id, title)
            if task_section:
                # Truncate to ~200 words
                words = task_section.split()
                if len(words) > self.summary_length:
                    task_section = ' '.join(words[:self.summary_length]) + "..."
                summary += f"{task_section}\n\n"
            else:
                summary += "Task implementation details available in sprint plan.\n\n"
        else:
            summary += f"Implements {title.lower()}.\n\n"

        # Key decisions section
        summary += "## Key Decisions\n\n"
        if sprint_plan:
            summary += "(Key technical decisions would be extracted from sprint plan)\n\n"
        else:
            summary += "No key decisions documented yet.\n\n"

        # Dependencies provided
        summary += "## Dependencies Provided\n\n"
        summary += "(APIs, interfaces, and data structures this task provides to dependent tasks)\n\n"

        # Deliverables
        if task.get('deliverables'):
            summary += "## Deliverables\n\n"
            for deliverable in task.get('deliverables', []):
                summary += f"- {deliverable}\n"
            summary += "\n"

        return summary

    def _extract_task_section(
        self,
        sprint_plan: str,
        task_id: str,
        task_title: str
    ) -> Optional[str]:
        """
        Extract the section of sprint plan related to this task.

        Looks for headers containing the task title or ID.
        """
        lines = sprint_plan.split('\n')
        task_lines = []
        in_task_section = False
        header_level = 0

        for i, line in enumerate(lines):
            # Check if this is a task header
            if line.startswith('#'):
                current_level = len(line) - len(line.lstrip('#'))

                # Check if this header mentions the task
                if task_id in line or task_title in line:
                    in_task_section = True
                    header_level = current_level
                    continue

                # If we're in a task section and hit a same/higher level header, stop
                elif in_task_section and current_level <= header_level:
                    break

            # Collect lines if we're in the task section
            if in_task_section:
                task_lines.append(line)

        return '\n'.join(task_lines).strip() if task_lines else None

    def _generate_llm_summary(
        self,
        task: Dict,
        sprint_plan: Optional[str]
    ) -> str:
        """
        Generate summary using LLM (Claude API).

        NOTE: This is a placeholder implementation.
        Full implementation would:
        1. Construct prompt with task metadata and sprint plan
        2. Call Claude API
        3. Parse and format response
        """
        # For now, fall back to structured summary
        # Real implementation would call Anthropic API:
        #
        # import anthropic
        # client = anthropic.Anthropic(api_key=self.api_key)
        # response = client.messages.create(
        #     model="claude-3-5-sonnet-20241022",
        #     max_tokens=1024,
        #     messages=[{
        #         "role": "user",
        #         "content": prompt
        #     }]
        # )
        # return response.content[0].text

        return self._generate_structured_summary(task, sprint_plan)

    def generate_sprint_summary(self, sprint_id: str) -> str:
        """
        Generate summary for entire sprint.

        Args:
            sprint_id: Sprint ID

        Returns:
            Sprint summary (Markdown)
        """
        summary_file = self.task_summaries_dir / f"{sprint_id}.md"

        # Load sprint data
        sprint_file = self.sprints_dir / f"{sprint_id}.yaml"
        if not sprint_file.exists():
            return f"# Sprint Summary: {sprint_id}\n\n**Status:** Not found\n"

        try:
            with open(sprint_file, 'r') as f:
                sprint_data = yaml.safe_load(f)

            sprint = sprint_data.get('sprint', {})

            summary = f"# Sprint Summary: {sprint.get('name', sprint_id)}\n\n"
            summary += f"**ID:** {sprint_id}\n"
            summary += f"**Status:** {sprint.get('status', 'unknown')}\n"
            summary += f"**Progress:** {sprint.get('progress', {}).get('completion_percent', 0)}%\n\n"

            # Tasks overview
            tasks = sprint.get('tasks', [])
            summary += f"## Tasks ({len(tasks)} total)\n\n"

            completed = [t for t in tasks if t.get('status') == 'completed']
            in_progress = [t for t in tasks if t.get('status') == 'in_progress']
            not_started = [t for t in tasks if t.get('status') == 'not_started']

            summary += f"- ✅ Completed: {len(completed)}\n"
            summary += f"- 🔄 In Progress: {len(in_progress)}\n"
            summary += f"- ⏸️ Not Started: {len(not_started)}\n\n"

            # Deliverables
            deliverables = sprint.get('deliverables', [])
            if deliverables:
                summary += "## Deliverables\n\n"
                for deliverable in deliverables:
                    summary += f"- {deliverable}\n"
                summary += "\n"

            # Cache
            summary_file.write_text(summary)

            return summary

        except Exception as e:
            return f"# Sprint Summary: {sprint_id}\n\n**Error:** {e}\n"

    def clear_cache(self, task_id: Optional[str] = None):
        """
        Clear cached summaries.

        Args:
            task_id: If provided, clear only this task. Otherwise clear all.
        """
        if task_id:
            summary_file = self.dependency_summaries_dir / f"{task_id}.md"
            if summary_file.exists():
                summary_file.unlink()
        else:
            # Clear all cached summaries
            for summary_file in self.dependency_summaries_dir.glob("*.md"):
                summary_file.unlink()
            for summary_file in self.task_summaries_dir.glob("*.md"):
                summary_file.unlink()


def demo():
    """Demo the summary generator"""
    print("📝 Summary Generator Demo\n")

    try:
        generator = SummaryGenerator(use_llm=False)

        # Generate task summary
        task_id = "core-framework-2-task-003"
        print(f"Generating summary for: {task_id}\n")
        print("=" * 60)

        summary = generator.generate_task_summary(task_id)
        print(summary)

        print("\n" + "=" * 60)
        print(f"\n✅ Summary generated and cached at:")
        print(f"   {generator.dependency_summaries_dir / f'{task_id}.md'}")

        # Generate sprint summary
        print("\n" + "=" * 60)
        sprint_id = "core-framework-2"
        print(f"\nGenerating sprint summary for: {sprint_id}\n")
        print("=" * 60)

        sprint_summary = generator.generate_sprint_summary(sprint_id)
        print(sprint_summary)

        print("\n" + "=" * 60)
        print(f"\n✅ Sprint summary cached at:")
        print(f"   {generator.task_summaries_dir / f'{sprint_id}.md'}")

    except FileNotFoundError as e:
        print(f"❌ {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    demo()
