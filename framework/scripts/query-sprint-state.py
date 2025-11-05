#!/usr/bin/env python3
"""
Query Sprint State File

Reads and queries sprint state YAML file for various information.

Usage Examples:

    # Get sprint summary
    python3 query-sprint-state.py --state sprint-1-state.yaml summary

    # Get current phase info
    python3 query-sprint-state.py --state sprint-1-state.yaml current-phase

    # Check if phase can be completed
    python3 query-sprint-state.py --state sprint-1-state.yaml check-phase-completion --phase 1

    # List all phases
    python3 query-sprint-state.py --state sprint-1-state.yaml list-phases

    # Get phase details
    python3 query-sprint-state.py --state sprint-1-state.yaml phase-details --phase 1

    # Get recent activity
    python3 query-sprint-state.py --state sprint-1-state.yaml recent-activity --limit 5

    # Check mandatory agents run
    python3 query-sprint-state.py --state sprint-1-state.yaml check-agents --phase 1 --agents web-developer,security-auditor

    # Get quality gate results
    python3 query-sprint-state.py --state sprint-1-state.yaml quality-gates --phase 1

    # Export for dashboard (JSON format)
    python3 query-sprint-state.py --state sprint-1-state.yaml dashboard --format json
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    print("Error: PyYAML not installed. Install with: pip install pyyaml")
    sys.exit(1)


class SprintStateQuery:
    """Query sprint state information."""

    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        """Load the state file."""
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Error: State file not found: {self.state_file}")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"Error parsing state file: {e}")
            sys.exit(1)

    def _get_phase(self, phase_num: int) -> Optional[Dict]:
        """Get phase by number."""
        for phase in self.state.get('phases', []):
            if phase['number'] == phase_num:
                return phase
        return None

    def _format_output(self, data: Any, format_type: str = 'text') -> str:
        """Format output based on format type."""
        if format_type == 'json':
            return json.dumps(data, indent=2, default=str)
        elif format_type == 'yaml':
            return yaml.dump(data, default_flow_style=False, sort_keys=False)
        else:
            return str(data)

    # =========================================================================
    # SPRINT QUERIES
    # =========================================================================

    def summary(self, format_type: str = 'text') -> str:
        """Get sprint summary."""
        sprint = self.state['sprint']
        current = self.state['current_phase']
        phases = self.state['phases']

        completed_phases = sum(1 for p in phases if p['status'] == 'completed')
        total_phases = len(phases)

        if format_type == 'json':
            data = {
                'sprint_number': sprint['number'],
                'sprint_name': sprint['name'],
                'status': sprint['status'],
                'started': sprint['started'],
                'current_phase': current['number'],
                'current_phase_name': current['name'],
                'phases_completed': completed_phases,
                'total_phases': total_phases,
                'progress_percent': int((completed_phases / total_phases) * 100) if total_phases > 0 else 0
            }
            return self._format_output(data, 'json')

        # Text format
        output = []
        output.append(f"Sprint {sprint['number']}: {sprint['name']}")
        output.append(f"Status: {sprint['status']}")
        output.append(f"Started: {sprint['started'] or 'Not started'}")
        output.append(f"Current Phase: Phase {current['number']}: {current['name']}" if current['number'] else "No active phase")
        output.append(f"Progress: {completed_phases}/{total_phases} phases completed")
        return "\n".join(output)

    def current_phase_info(self, format_type: str = 'text') -> str:
        """Get current phase information."""
        current = self.state['current_phase']

        if not current['number']:
            return "No active phase"

        phase = self._get_phase(current['number'])
        if not phase:
            return "Error: Current phase not found"

        if format_type == 'json':
            return self._format_output(phase, 'json')

        # Text format
        output = []
        output.append(f"Phase {phase['number']}: {phase['name']}")
        output.append(f"Status: {phase['status']}")
        output.append(f"Progress: {phase['progress_percent']}%")
        output.append(f"Started: {phase['started'] or 'Not started'}")

        if phase.get('agents_run'):
            output.append(f"\nAgents run: {len(phase['agents_run'])}")
            for agent in phase['agents_run']:
                output.append(f"  - {agent['name']} ({agent['status']})")

        if phase.get('tasks'):
            completed = sum(1 for t in phase['tasks'] if t['completed'])
            output.append(f"\nTasks: {completed}/{len(phase['tasks'])} completed")

        if phase.get('quality_gates'):
            output.append(f"\nQuality Gates:")
            for gate in phase['quality_gates']:
                status_icon = "✓" if gate['status'] == 'passed' else "✗" if gate['status'] == 'failed' else "○"
                score_text = f" ({gate['score']}/{gate['threshold']})" if gate['score'] is not None else ""
                output.append(f"  {status_icon} {gate['name']}: {gate['status']}{score_text}")

        return "\n".join(output)

    def list_phases(self, format_type: str = 'text') -> str:
        """List all phases with their status."""
        phases = self.state['phases']

        if format_type == 'json':
            data = [
                {
                    'number': p['number'],
                    'name': p['name'],
                    'status': p['status'],
                    'progress_percent': p['progress_percent']
                }
                for p in phases
            ]
            return self._format_output(data, 'json')

        # Text format
        output = []
        for phase in phases:
            status_icon = "✓" if phase['status'] == 'completed' else "→" if phase['status'] == 'in_progress' else "○"
            output.append(f"{status_icon} Phase {phase['number']}: {phase['name']} ({phase['status']}, {phase['progress_percent']}%)")
        return "\n".join(output)

    def phase_details(self, phase_num: int, format_type: str = 'text') -> str:
        """Get detailed information about a specific phase."""
        phase = self._get_phase(phase_num)
        if not phase:
            return f"Error: Phase {phase_num} not found"

        if format_type == 'json':
            return self._format_output(phase, 'json')

        # Text format
        output = []
        output.append(f"=== Phase {phase['number']}: {phase['name']} ===")
        output.append(f"Status: {phase['status']}")
        output.append(f"Progress: {phase['progress_percent']}%")
        output.append(f"Started: {phase['started'] or 'Not started'}")
        output.append(f"Completed: {phase['completed'] or 'Not completed'}")

        if phase.get('agents_run'):
            output.append(f"\n--- Agents Run ({len(phase['agents_run'])}) ---")
            for agent in phase['agents_run']:
                output.append(f"  • {agent['name']}")
                output.append(f"    Status: {agent['status']}")
                output.append(f"    Time: {agent['timestamp']}")
                if agent.get('notes'):
                    output.append(f"    Notes: {agent['notes']}")

        if phase.get('tasks'):
            completed = sum(1 for t in phase['tasks'] if t['completed'])
            output.append(f"\n--- Tasks ({completed}/{len(phase['tasks'])} completed) ---")
            for task in phase['tasks']:
                status = "✓" if task['completed'] else "○"
                output.append(f"  {status} {task['description']}")
                if task['completed_at']:
                    output.append(f"    Completed: {task['completed_at']}")

        if phase.get('quality_gates'):
            output.append(f"\n--- Quality Gates ({len(phase['quality_gates'])}) ---")
            for gate in phase['quality_gates']:
                status_icon = "✓" if gate['status'] == 'passed' else "✗" if gate['status'] == 'failed' else "○"
                output.append(f"  {status_icon} {gate['name']}")
                output.append(f"    Status: {gate['status']}")
                if gate['score'] is not None:
                    output.append(f"    Score: {gate['score']}/{gate['threshold']}")
                output.append(f"    Blocking: {gate['blocking']}")
                if gate.get('issues'):
                    output.append(f"    Issues:")
                    for issue in gate['issues']:
                        output.append(f"      - {issue}")

        return "\n".join(output)

    # =========================================================================
    # VALIDATION QUERIES
    # =========================================================================

    def check_phase_completion(self, phase_num: int, format_type: str = 'text') -> str:
        """Check if a phase can be completed."""
        phase = self._get_phase(phase_num)
        if not phase:
            return f"Error: Phase {phase_num} not found"

        blockers = []

        # Check tasks
        if phase.get('tasks'):
            incomplete_tasks = [t for t in phase['tasks'] if not t['completed']]
            if incomplete_tasks:
                blockers.append({
                    'type': 'incomplete_tasks',
                    'count': len(incomplete_tasks),
                    'details': [t['description'] for t in incomplete_tasks]
                })

        # Check quality gates
        if phase.get('quality_gates'):
            for gate in phase['quality_gates']:
                if gate['blocking'] and gate['status'] != 'passed':
                    blocker = {
                        'type': 'quality_gate',
                        'gate': gate['name'],
                        'status': gate['status'],
                        'blocking': True
                    }
                    if gate.get('score') is not None:
                        blocker['score'] = gate['score']
                        blocker['threshold'] = gate['threshold']
                    if gate.get('issues'):
                        blocker['issues'] = gate['issues']
                    blockers.append(blocker)

        can_complete = len(blockers) == 0

        if format_type == 'json':
            data = {
                'phase': phase_num,
                'can_complete': can_complete,
                'blockers': blockers
            }
            return self._format_output(data, 'json')

        # Text format
        if can_complete:
            return f"✓ Phase {phase_num} can be completed (no blockers)"

        output = [f"✗ Phase {phase_num} has {len(blockers)} blocker(s):"]
        for blocker in blockers:
            if blocker['type'] == 'incomplete_tasks':
                output.append(f"\n  Incomplete Tasks ({blocker['count']}):")
                for task in blocker['details']:
                    output.append(f"    - {task}")
            elif blocker['type'] == 'quality_gate':
                output.append(f"\n  Quality Gate: {blocker['gate']}")
                output.append(f"    Status: {blocker['status']}")
                if 'score' in blocker:
                    output.append(f"    Score: {blocker['score']}/{blocker['threshold']}")
                if 'issues' in blocker:
                    output.append(f"    Issues:")
                    for issue in blocker['issues']:
                        output.append(f"      - {issue}")

        return "\n".join(output)

    def check_agents_run(self, phase_num: int, required_agents: List[str], format_type: str = 'text') -> str:
        """Check if required agents have been run."""
        phase = self._get_phase(phase_num)
        if not phase:
            return f"Error: Phase {phase_num} not found"

        agents_run = [a['name'] for a in phase.get('agents_run', [])]
        missing_agents = [a for a in required_agents if a not in agents_run]

        all_run = len(missing_agents) == 0

        if format_type == 'json':
            data = {
                'phase': phase_num,
                'all_agents_run': all_run,
                'agents_run': agents_run,
                'missing_agents': missing_agents
            }
            return self._format_output(data, 'json')

        # Text format
        if all_run:
            return f"✓ All required agents have been run for Phase {phase_num}"

        output = [f"✗ Missing required agents for Phase {phase_num}:"]
        for agent in missing_agents:
            output.append(f"  - {agent}")
        return "\n".join(output)

    def quality_gates_status(self, phase_num: int, format_type: str = 'text') -> str:
        """Get quality gates status for a phase."""
        phase = self._get_phase(phase_num)
        if not phase:
            return f"Error: Phase {phase_num} not found"

        gates = phase.get('quality_gates', [])

        if format_type == 'json':
            return self._format_output(gates, 'json')

        # Text format
        if not gates:
            return f"No quality gates defined for Phase {phase_num}"

        output = [f"Quality Gates for Phase {phase_num}:"]
        for gate in gates:
            status_icon = "✓" if gate['status'] == 'passed' else "✗" if gate['status'] == 'failed' else "○"
            blocking_text = " [BLOCKING]" if gate['blocking'] else ""
            score_text = f" ({gate['score']}/{gate['threshold']})" if gate['score'] is not None else ""
            output.append(f"  {status_icon} {gate['name']}: {gate['status']}{score_text}{blocking_text}")

        return "\n".join(output)

    # =========================================================================
    # ACTIVITY QUERIES
    # =========================================================================

    def recent_activity(self, limit: int = 10, format_type: str = 'text') -> str:
        """Get recent activity log entries."""
        activity = self.state.get('activity_log', [])
        recent = activity[-limit:] if len(activity) > limit else activity
        recent.reverse()  # Most recent first

        if format_type == 'json':
            return self._format_output(recent, 'json')

        # Text format
        output = [f"Recent Activity (last {len(recent)} entries):"]
        for entry in recent:
            output.append(f"  [{entry['timestamp']}] {entry['type']}: {entry['description']}")

        return "\n".join(output)

    # =========================================================================
    # DASHBOARD
    # =========================================================================

    def dashboard(self, format_type: str = 'text') -> str:
        """Generate dashboard data."""
        sprint = self.state['sprint']
        current = self.state['current_phase']
        phases = self.state['phases']
        recent_activity = self.state.get('activity_log', [])[-5:]

        data = {
            'sprint': {
                'number': sprint['number'],
                'name': sprint['name'],
                'status': sprint['status'],
                'started': sprint['started']
            },
            'current_phase': current,
            'phases_summary': [
                {
                    'number': p['number'],
                    'name': p['name'],
                    'status': p['status'],
                    'progress': p['progress_percent']
                }
                for p in phases
            ],
            'recent_activity': recent_activity
        }

        if current['number']:
            phase = self._get_phase(current['number'])
            if phase:
                data['current_phase_details'] = {
                    'tasks_total': len(phase.get('tasks', [])),
                    'tasks_completed': sum(1 for t in phase.get('tasks', []) if t['completed']),
                    'agents_run': len(phase.get('agents_run', [])),
                    'quality_gates': [
                        {
                            'name': g['name'],
                            'status': g['status'],
                            'score': g['score'],
                            'threshold': g['threshold']
                        }
                        for g in phase.get('quality_gates', [])
                    ]
                }

        return self._format_output(data, format_type)


def main():
    parser = argparse.ArgumentParser(
        description='Query sprint state file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--state', required=True, help='Path to sprint state file')
    parser.add_argument('--format', choices=['text', 'json', 'yaml'], default='text', help='Output format')

    subparsers = parser.add_subparsers(dest='command', help='Query command')

    # Simple queries
    subparsers.add_parser('summary', help='Get sprint summary')
    subparsers.add_parser('current-phase', help='Get current phase info')
    subparsers.add_parser('list-phases', help='List all phases')

    # Phase details
    phase_details = subparsers.add_parser('phase-details', help='Get phase details')
    phase_details.add_argument('--phase', type=int, required=True)

    # Validation
    check_completion = subparsers.add_parser('check-phase-completion', help='Check if phase can be completed')
    check_completion.add_argument('--phase', type=int, required=True)

    check_agents = subparsers.add_parser('check-agents', help='Check if required agents run')
    check_agents.add_argument('--phase', type=int, required=True)
    check_agents.add_argument('--agents', required=True, help='Comma-separated list of agent names')

    quality_gates = subparsers.add_parser('quality-gates', help='Get quality gates status')
    quality_gates.add_argument('--phase', type=int, required=True)

    # Activity
    activity = subparsers.add_parser('recent-activity', help='Get recent activity')
    activity.add_argument('--limit', type=int, default=10, help='Number of entries')

    # Dashboard
    subparsers.add_parser('dashboard', help='Get dashboard data')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Initialize query
    query = SprintStateQuery(Path(args.state))

    # Execute command
    result = ""
    if args.command == 'summary':
        result = query.summary(args.format)
    elif args.command == 'current-phase':
        result = query.current_phase_info(args.format)
    elif args.command == 'list-phases':
        result = query.list_phases(args.format)
    elif args.command == 'phase-details':
        result = query.phase_details(args.phase, args.format)
    elif args.command == 'check-phase-completion':
        result = query.check_phase_completion(args.phase, args.format)
    elif args.command == 'check-agents':
        agents = [a.strip() for a in args.agents.split(',')]
        result = query.check_agents_run(args.phase, agents, args.format)
    elif args.command == 'quality-gates':
        result = query.quality_gates_status(args.phase, args.format)
    elif args.command == 'recent-activity':
        result = query.recent_activity(args.limit, args.format)
    elif args.command == 'dashboard':
        result = query.dashboard(args.format)

    print(result)


if __name__ == '__main__':
    main()
