#!/usr/bin/env python3
"""
Create Sprint State File

Initializes a sprint state YAML file from a sprint plan.

Usage:
    python3 create-sprint-state.py \\
        --sprint-number 1 \\
        --sprint-name "User Authentication System" \\
        --plan-file "docs/sprints/sprint-1-plan.md" \\
        --output "docs/sprints/sprint-1-state.yaml"

Or:
    python3 create-sprint-state.py \\
        --plan-file "docs/sprints/sprint-1-plan.md"
    (Auto-detects sprint number, name, and output path from plan file)
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    import yaml
except ImportError:
    print("Error: PyYAML not installed. Install with: pip install pyyaml")
    sys.exit(1)


class SprintPlanParser:
    """Parse sprint plan markdown to extract phase information."""

    def __init__(self, plan_file: Path):
        self.plan_file = plan_file
        self.content = self._read_file()

    def _read_file(self) -> str:
        """Read the sprint plan file."""
        try:
            with open(self.plan_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Error: Sprint plan file not found: {self.plan_file}")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading sprint plan file: {e}")
            sys.exit(1)

    def extract_sprint_number(self) -> int:
        """Extract sprint number from plan file."""
        # Try from filename first (sprint-1-plan.md)
        match = re.search(r'sprint-(\d+)-', self.plan_file.name)
        if match:
            return int(match.group(1))

        # Try from content (# Sprint 1:)
        match = re.search(r'^#\s+Sprint\s+(\d+):', self.content, re.MULTILINE)
        if match:
            return int(match.group(1))

        print("Warning: Could not detect sprint number from plan file")
        return 1

    def extract_sprint_name(self) -> str:
        """Extract sprint name from plan file."""
        # Try: # Sprint 1: Sprint Name
        match = re.search(r'^#\s+Sprint\s+\d+:\s*(.+)$', self.content, re.MULTILINE)
        if match:
            return match.group(1).strip()

        # Try: **Sprint Name:** Value
        match = re.search(r'\*\*Sprint Name:\*\*\s*(.+)$', self.content, re.MULTILINE)
        if match:
            return match.group(1).strip()

        print("Warning: Could not detect sprint name from plan file")
        return "Unnamed Sprint"

    def extract_phases(self) -> List[Dict]:
        """Extract all phases from sprint plan."""
        phases = []

        # Pattern: ## Phase 1: Phase Name
        phase_pattern = re.compile(r'^##\s+Phase\s+(\d+):\s*(.+)$', re.MULTILINE)

        for match in phase_pattern.finditer(self.content):
            phase_num = int(match.group(1))
            phase_name = match.group(2).strip()

            # Extract orchestration info for this phase
            agents, quality_gates = self._extract_phase_orchestration(phase_num)

            phases.append({
                'number': phase_num,
                'name': phase_name,
                'status': 'not_started',
                'progress_percent': 0,
                'started': None,
                'completed': None,
                'agents_run': [],
                'tasks': [],
                'quality_gates': quality_gates
            })

        if not phases:
            print("Warning: No phases found in sprint plan")

        return phases

    def _extract_phase_orchestration(self, phase_num: int) -> tuple:
        """Extract orchestration rules for a specific phase."""
        # This is a simplified version - real implementation would parse
        # the orchestration YAML block from the plan
        # For now, return empty lists - can be enhanced later

        agents = []
        quality_gates = []

        # Try to find orchestration section for this phase
        # Pattern: Look for YAML block after "## Phase N:"
        phase_section = self._extract_phase_section(phase_num)
        if phase_section:
            # Look for quality_gates in YAML
            gates_match = re.search(
                r'quality_gates:\s*\n((?:[ ]{2,}-[^\n]+\n)+)',
                phase_section,
                re.MULTILINE
            )
            if gates_match:
                # Parse quality gates (simplified)
                for line in gates_match.group(1).split('\n'):
                    gate_match = re.search(r'-\s*gate:\s*"([^"]+)"', line)
                    if gate_match:
                        gate_name = gate_match.group(1)
                        quality_gates.append({
                            'name': gate_name,
                            'status': 'not_run',
                            'score': None,
                            'threshold': 85,  # Default
                            'blocking': True,  # Default
                            'checked_at': None,
                            'issues': []
                        })

        return agents, quality_gates

    def _extract_phase_section(self, phase_num: int) -> Optional[str]:
        """Extract the content section for a specific phase."""
        # Find start of phase section
        phase_start = re.search(
            rf'^##\s+Phase\s+{phase_num}:',
            self.content,
            re.MULTILINE
        )
        if not phase_start:
            return None

        # Find start of next phase or end of document
        next_phase = re.search(
            rf'^##\s+Phase\s+{phase_num + 1}:',
            self.content[phase_start.end():],
            re.MULTILINE
        )

        if next_phase:
            return self.content[phase_start.start():phase_start.end() + next_phase.start()]
        else:
            return self.content[phase_start.start():]


def create_sprint_state(
    sprint_number: int,
    sprint_name: str,
    plan_file: str,
    output_file: str
) -> None:
    """Create a new sprint state file."""

    print(f"Creating sprint state file...")
    print(f"  Sprint: #{sprint_number} - {sprint_name}")
    print(f"  Plan: {plan_file}")
    print(f"  Output: {output_file}")

    # Parse sprint plan
    parser = SprintPlanParser(Path(plan_file))
    phases = parser.extract_phases()

    print(f"  Phases detected: {len(phases)}")

    # Create state structure
    now = datetime.now().isoformat()
    state = {
        'sprint': {
            'number': sprint_number,
            'name': sprint_name,
            'status': 'not_started',
            'started': None,
            'paused': None,
            'completed': None,
            'plan_file': plan_file
        },
        'current_phase': {
            'number': None,
            'name': None,
            'status': None,
            'started': None,
            'completed': None
        },
        'phases': phases,
        'activity_log': [
            {
                'timestamp': now,
                'type': 'note',
                'description': f'Sprint state file created for Sprint {sprint_number}',
                'metadata': {
                    'sprint_number': sprint_number,
                    'sprint_name': sprint_name
                }
            }
        ],
        'metadata': {
            'created_at': now,
            'last_updated': now,
            'framework_version': '2.0',
            'state_schema_version': '1.0'
        }
    }

    # Ensure output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write state file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        print(f"✓ Sprint state file created: {output_file}")
    except Exception as e:
        print(f"Error writing state file: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Create a sprint state file from a sprint plan',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--sprint-number',
        type=int,
        help='Sprint number (auto-detected if not provided)'
    )
    parser.add_argument(
        '--sprint-name',
        type=str,
        help='Sprint name (auto-detected if not provided)'
    )
    parser.add_argument(
        '--plan-file',
        required=True,
        help='Path to sprint plan markdown file'
    )
    parser.add_argument(
        '--output',
        help='Output path for state file (auto-generated if not provided)'
    )

    args = parser.parse_args()

    # Parse plan file for auto-detection
    plan_parser = SprintPlanParser(Path(args.plan_file))

    # Auto-detect sprint number
    sprint_number = args.sprint_number
    if sprint_number is None:
        sprint_number = plan_parser.extract_sprint_number()

    # Auto-detect sprint name
    sprint_name = args.sprint_name
    if sprint_name is None:
        sprint_name = plan_parser.extract_sprint_name()

    # Auto-generate output path
    output_file = args.output
    if output_file is None:
        plan_path = Path(args.plan_file)
        output_file = str(plan_path.parent / f"sprint-{sprint_number}-state.yaml")

    # Create state file
    create_sprint_state(
        sprint_number=sprint_number,
        sprint_name=sprint_name,
        plan_file=args.plan_file,
        output_file=output_file
    )


if __name__ == '__main__':
    main()
