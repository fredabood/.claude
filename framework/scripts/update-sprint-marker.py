#!/usr/bin/env python3
"""
Update Sprint Marker in CLAUDE.md

Updates the current_sprint section in CLAUDE.md with sprint execution state.

Usage:
    # Activate sprint
    python3 update-sprint-marker.py \\
        --claude-md .claude/CLAUDE.md \\
        --sprint-number 1 \\
        --sprint-name "User Authentication System" \\
        --plan-file "docs/sprints/sprint-1-plan.md" \\
        --state-file "docs/sprints/sprint-1-state.yaml" \\
        --phase-number 1 \\
        --phase-name "API Development" \\
        --active

    # Update phase
    python3 update-sprint-marker.py \\
        --claude-md .claude/CLAUDE.md \\
        --phase-number 2 \\
        --phase-name "Frontend Implementation"

    # Deactivate sprint
    python3 update-sprint-marker.py \\
        --claude-md .claude/CLAUDE.md \\
        --deactivate

    # Read from state file (auto-populate from sprint state)
    python3 update-sprint-marker.py \\
        --claude-md .claude/CLAUDE.md \\
        --state-file docs/sprints/sprint-1-state.yaml
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import yaml
except ImportError:
    print("Error: PyYAML not installed. Install with: pip install pyyaml")
    sys.exit(1)


class CLAUDEMarkdownUpdater:
    """Updates sprint marker section in CLAUDE.md."""

    def __init__(self, claude_md_path: Path):
        self.claude_md_path = claude_md_path
        self.content = self._read_file()

    def _read_file(self) -> str:
        """Read CLAUDE.md file."""
        try:
            with open(self.claude_md_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Error: CLAUDE.md not found: {self.claude_md_path}")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading CLAUDE.md: {e}")
            sys.exit(1)

    def _write_file(self, content: str) -> None:
        """Write CLAUDE.md file."""
        try:
            with open(self.claude_md_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ CLAUDE.md updated: {self.claude_md_path}")
        except Exception as e:
            print(f"Error writing CLAUDE.md: {e}")
            sys.exit(1)

    def _find_sprint_section(self) -> Optional[tuple]:
        """Find the current_sprint section in CLAUDE.md.

        Returns (start_pos, end_pos) if found, None otherwise.
        """
        # Look for current_sprint: section (YAML-style in markdown)
        pattern = re.compile(
            r'^current_sprint:\s*\n((?:  .+\n)*)',
            re.MULTILINE
        )
        match = pattern.search(self.content)
        if match:
            return (match.start(), match.end())

        # Alternative: Look for ## Current Sprint section
        section_pattern = re.compile(
            r'^##\s+Current Sprint\s*\n(.*?)(?=^##|\Z)',
            re.MULTILINE | re.DOTALL
        )
        match = section_pattern.search(self.content)
        if match:
            return (match.start(), match.end())

        return None

    def _generate_sprint_marker(
        self,
        active: bool,
        sprint_number: Optional[int] = None,
        sprint_name: Optional[str] = None,
        plan_file: Optional[str] = None,
        state_file: Optional[str] = None,
        phase_number: Optional[int] = None,
        phase_name: Optional[str] = None,
        start_date: Optional[str] = None
    ) -> str:
        """Generate the sprint marker YAML block."""

        if not active:
            return """current_sprint:
  active: false
  number: null
  name: null
  start_date: null
  phase: null
  plan_file: null
  state_file: null
  phase_anchor: null
"""

        # Active sprint
        marker = f"""current_sprint:
  active: true
  number: {sprint_number}
  name: "{sprint_name}"
  start_date: "{start_date or datetime.now().strftime('%Y-%m-%d')}"
  phase: "Phase {phase_number}: {phase_name}"
  plan_file: "{plan_file}"
  state_file: "{state_file}"
  phase_anchor: "## Phase {phase_number}: {phase_name}"
"""
        return marker

    def update_from_params(
        self,
        active: bool,
        sprint_number: Optional[int] = None,
        sprint_name: Optional[str] = None,
        plan_file: Optional[str] = None,
        state_file: Optional[str] = None,
        phase_number: Optional[int] = None,
        phase_name: Optional[str] = None,
        start_date: Optional[str] = None
    ) -> None:
        """Update sprint marker from explicit parameters."""

        section_pos = self._find_sprint_section()

        new_marker = self._generate_sprint_marker(
            active=active,
            sprint_number=sprint_number,
            sprint_name=sprint_name,
            plan_file=plan_file,
            state_file=state_file,
            phase_number=phase_number,
            phase_name=phase_name,
            start_date=start_date
        )

        if section_pos:
            # Replace existing section
            start, end = section_pos
            new_content = self.content[:start] + new_marker + self.content[end:]
        else:
            # Add section at the end (before final closing if exists)
            # Try to find a good insertion point
            insertion_patterns = [
                (r'\n---\n$', '\n'),  # Before final separator
                (r'\Z', '\n\n')  # At end of file
            ]

            inserted = False
            for pattern, suffix in insertion_patterns:
                match = re.search(pattern, self.content)
                if match:
                    insert_pos = match.start()
                    new_content = (
                        self.content[:insert_pos] +
                        '\n## Current Sprint Context\n\n' +
                        new_marker +
                        suffix +
                        self.content[insert_pos:]
                    )
                    inserted = True
                    break

            if not inserted:
                # Fallback: append at end
                new_content = self.content + '\n\n## Current Sprint Context\n\n' + new_marker

        self._write_file(new_content)

    def update_from_state_file(self, state_file_path: Path) -> None:
        """Update sprint marker from a sprint state file."""
        try:
            with open(state_file_path, 'r', encoding='utf-8') as f:
                state = yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Error: State file not found: {state_file_path}")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading state file: {e}")
            sys.exit(1)

        sprint = state.get('sprint', {})
        current_phase = state.get('current_phase', {})

        # Determine if sprint is active
        active = sprint.get('status') in ['in_progress', 'paused']

        self.update_from_params(
            active=active,
            sprint_number=sprint.get('number'),
            sprint_name=sprint.get('name'),
            plan_file=sprint.get('plan_file'),
            state_file=str(state_file_path),
            phase_number=current_phase.get('number'),
            phase_name=current_phase.get('name'),
            start_date=sprint.get('started', '').split('T')[0] if sprint.get('started') else None
        )

    def update_phase_only(self, phase_number: int, phase_name: str) -> None:
        """Update only the current phase (keep other sprint info)."""

        # Extract current sprint info
        section_pos = self._find_sprint_section()
        if not section_pos:
            print("Error: No current_sprint section found in CLAUDE.md")
            sys.exit(1)

        # Parse existing sprint info
        start, end = section_pos
        section_content = self.content[start:end]

        # Extract current values using regex
        number_match = re.search(r'number:\s*(\d+)', section_content)
        name_match = re.search(r'name:\s*"([^"]+)"', section_content)
        date_match = re.search(r'start_date:\s*"([^"]+)"', section_content)
        plan_match = re.search(r'plan_file:\s*"([^"]+)"', section_content)
        state_match = re.search(r'state_file:\s*"([^"]+)"', section_content)

        if not number_match:
            print("Error: Cannot determine current sprint number")
            sys.exit(1)

        self.update_from_params(
            active=True,
            sprint_number=int(number_match.group(1)),
            sprint_name=name_match.group(1) if name_match else "Unknown",
            plan_file=plan_match.group(1) if plan_match else None,
            state_file=state_match.group(1) if state_match else None,
            phase_number=phase_number,
            phase_name=phase_name,
            start_date=date_match.group(1) if date_match else None
        )

    def deactivate(self) -> None:
        """Deactivate the current sprint."""
        self.update_from_params(active=False)


def main():
    parser = argparse.ArgumentParser(
        description='Update sprint marker in CLAUDE.md',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--claude-md', required=True, help='Path to CLAUDE.md file')

    # Source options (mutually exclusive)
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument('--state-file', help='Update from sprint state file')
    source_group.add_argument('--deactivate', action='store_true', help='Deactivate sprint')

    # Manual parameters
    parser.add_argument('--sprint-number', type=int, help='Sprint number')
    parser.add_argument('--sprint-name', help='Sprint name')
    parser.add_argument('--plan-file', help='Sprint plan file path')
    parser.add_argument('--phase-number', type=int, help='Current phase number')
    parser.add_argument('--phase-name', help='Current phase name')
    parser.add_argument('--active', action='store_true', help='Activate sprint')

    args = parser.parse_args()

    updater = CLAUDEMarkdownUpdater(Path(args.claude_md))

    # Determine operation mode
    if args.state_file:
        # Update from state file
        updater.update_from_state_file(Path(args.state_file))
    elif args.deactivate:
        # Deactivate sprint
        updater.deactivate()
    elif args.phase_number and args.phase_name and not args.sprint_number:
        # Update phase only (keep existing sprint info)
        updater.update_phase_only(args.phase_number, args.phase_name)
    else:
        # Manual update
        if args.active and not args.sprint_number:
            print("Error: --sprint-number required when using --active")
            sys.exit(1)

        updater.update_from_params(
            active=args.active,
            sprint_number=args.sprint_number,
            sprint_name=args.sprint_name,
            plan_file=args.plan_file,
            state_file=args.state_file,
            phase_number=args.phase_number,
            phase_name=args.phase_name
        )


if __name__ == '__main__':
    main()
