#!/usr/bin/env python3
"""
Update Sprint State File

Modifies a sprint state YAML file with various updates.

Usage Examples:

    # Start a sprint
    python3 update-sprint-state.py --state sprint-1-state.yaml start-sprint

    # Start a phase
    python3 update-sprint-state.py --state sprint-1-state.yaml start-phase --phase 1

    # Complete a phase
    python3 update-sprint-state.py --state sprint-1-state.yaml complete-phase --phase 1

    # Log agent execution
    python3 update-sprint-state.py --state sprint-1-state.yaml log-agent \\
        --phase 1 --agent web-developer --status completed --notes "Created 3 endpoints"

    # Update task
    python3 update-sprint-state.py --state sprint-1-state.yaml update-task \\
        --phase 1 --task "Implement user registration" --completed

    # Add task
    python3 update-sprint-state.py --state sprint-1-state.yaml add-task \\
        --phase 1 --task "Write integration tests"

    # Record quality gate result
    python3 update-sprint-state.py --state sprint-1-state.yaml quality-gate \\
        --phase 1 --gate "Security Audit" --status passed --score 92

    # Add activity log entry
    python3 update-sprint-state.py --state sprint-1-state.yaml log \\
        --type note --description "Completed code review"

    # Pause sprint
    python3 update-sprint-state.py --state sprint-1-state.yaml pause-sprint

    # Resume sprint
    python3 update-sprint-state.py --state sprint-1-state.yaml resume-sprint

    # Complete sprint
    python3 update-sprint-state.py --state sprint-1-state.yaml complete-sprint
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
except ImportError:
    print("Error: PyYAML not installed. Install with: pip install pyyaml")
    sys.exit(1)


class SprintStateUpdater:
    """Manages updates to sprint state file."""

    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        """Load the current state file."""
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Error: State file not found: {self.state_file}")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"Error parsing state file: {e}")
            sys.exit(1)

    def _save_state(self) -> None:
        """Save the updated state file."""
        # Update last_updated timestamp
        self.state['metadata']['last_updated'] = datetime.now().isoformat()

        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.state, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            print(f"✓ State updated: {self.state_file}")
        except Exception as e:
            print(f"Error writing state file: {e}")
            sys.exit(1)

    def _add_activity(self, activity_type: str, description: str, metadata: Optional[Dict] = None) -> None:
        """Add an entry to the activity log."""
        activity = {
            'timestamp': datetime.now().isoformat(),
            'type': activity_type,
            'description': description
        }
        if metadata:
            activity['metadata'] = metadata

        self.state['activity_log'].append(activity)

    def _get_phase(self, phase_num: int) -> Optional[Dict]:
        """Get phase by number."""
        for phase in self.state['phases']:
            if phase['number'] == phase_num:
                return phase
        return None

    def _update_progress(self, phase_num: int) -> None:
        """Recalculate progress percentage for a phase."""
        phase = self._get_phase(phase_num)
        if not phase or not phase.get('tasks'):
            return

        completed_tasks = sum(1 for task in phase['tasks'] if task.get('completed'))
        total_tasks = len(phase['tasks'])

        if total_tasks > 0:
            phase['progress_percent'] = int((completed_tasks / total_tasks) * 100)

    # =========================================================================
    # SPRINT OPERATIONS
    # =========================================================================

    def start_sprint(self) -> None:
        """Start the sprint."""
        if self.state['sprint']['status'] != 'not_started':
            print(f"Warning: Sprint already started (status: {self.state['sprint']['status']})")
            return

        now = datetime.now().isoformat()
        self.state['sprint']['status'] = 'in_progress'
        self.state['sprint']['started'] = now

        self._add_activity(
            'sprint_started',
            f"Started Sprint {self.state['sprint']['number']}: {self.state['sprint']['name']}"
        )

        print(f"✓ Sprint {self.state['sprint']['number']} started")
        self._save_state()

    def pause_sprint(self) -> None:
        """Pause the sprint."""
        if self.state['sprint']['status'] != 'in_progress':
            print(f"Error: Cannot pause sprint with status: {self.state['sprint']['status']}")
            sys.exit(1)

        now = datetime.now().isoformat()
        self.state['sprint']['status'] = 'paused'
        self.state['sprint']['paused'] = now

        self._add_activity(
            'sprint_paused',
            f"Paused Sprint {self.state['sprint']['number']}"
        )

        print(f"✓ Sprint {self.state['sprint']['number']} paused")
        self._save_state()

    def resume_sprint(self) -> None:
        """Resume a paused sprint."""
        if self.state['sprint']['status'] != 'paused':
            print(f"Error: Cannot resume sprint with status: {self.state['sprint']['status']}")
            sys.exit(1)

        self.state['sprint']['status'] = 'in_progress'
        self.state['sprint']['paused'] = None

        self._add_activity(
            'sprint_resumed',
            f"Resumed Sprint {self.state['sprint']['number']}"
        )

        print(f"✓ Sprint {self.state['sprint']['number']} resumed")
        self._save_state()

    def complete_sprint(self) -> None:
        """Complete the sprint."""
        if self.state['sprint']['status'] == 'completed':
            print("Warning: Sprint already completed")
            return

        now = datetime.now().isoformat()
        self.state['sprint']['status'] = 'completed'
        self.state['sprint']['completed'] = now

        self._add_activity(
            'sprint_completed',
            f"Completed Sprint {self.state['sprint']['number']}: {self.state['sprint']['name']}"
        )

        print(f"✓ Sprint {self.state['sprint']['number']} completed")
        self._save_state()

    # =========================================================================
    # PHASE OPERATIONS
    # =========================================================================

    def start_phase(self, phase_num: int) -> None:
        """Start a phase."""
        phase = self._get_phase(phase_num)
        if not phase:
            print(f"Error: Phase {phase_num} not found")
            sys.exit(1)

        if phase['status'] != 'not_started':
            print(f"Warning: Phase {phase_num} already started (status: {phase['status']})")
            return

        now = datetime.now().isoformat()
        phase['status'] = 'in_progress'
        phase['started'] = now

        # Update current_phase
        self.state['current_phase'] = {
            'number': phase_num,
            'name': phase['name'],
            'status': 'in_progress',
            'started': now,
            'completed': None
        }

        # If sprint not started, start it
        if self.state['sprint']['status'] == 'not_started':
            self.state['sprint']['status'] = 'in_progress'
            self.state['sprint']['started'] = now

        self._add_activity(
            'phase_started',
            f"Started Phase {phase_num}: {phase['name']}",
            {'phase': phase_num}
        )

        print(f"✓ Phase {phase_num} started: {phase['name']}")
        self._save_state()

    def complete_phase(self, phase_num: int) -> None:
        """Complete a phase."""
        phase = self._get_phase(phase_num)
        if not phase:
            print(f"Error: Phase {phase_num} not found")
            sys.exit(1)

        if phase['status'] == 'completed':
            print(f"Warning: Phase {phase_num} already completed")
            return

        now = datetime.now().isoformat()
        phase['status'] = 'completed'
        phase['completed'] = now
        phase['progress_percent'] = 100

        # Update current_phase
        self.state['current_phase']['status'] = 'completed'
        self.state['current_phase']['completed'] = now

        self._add_activity(
            'phase_completed',
            f"Completed Phase {phase_num}: {phase['name']}",
            {'phase': phase_num}
        )

        print(f"✓ Phase {phase_num} completed: {phase['name']}")
        self._save_state()

    # =========================================================================
    # AGENT OPERATIONS
    # =========================================================================

    def log_agent(self, phase_num: int, agent_name: str, status: str, notes: str = "") -> None:
        """Log agent execution."""
        phase = self._get_phase(phase_num)
        if not phase:
            print(f"Error: Phase {phase_num} not found")
            sys.exit(1)

        now = datetime.now().isoformat()
        agent_log = {
            'name': agent_name,
            'timestamp': now,
            'status': status,
            'notes': notes
        }

        phase['agents_run'].append(agent_log)

        self._add_activity(
            'agent_execution',
            f"Agent '{agent_name}' {status} in Phase {phase_num}",
            {'phase': phase_num, 'agent': agent_name, 'status': status}
        )

        print(f"✓ Logged agent execution: {agent_name} ({status})")
        self._save_state()

    # =========================================================================
    # TASK OPERATIONS
    # =========================================================================

    def add_task(self, phase_num: int, task_description: str) -> None:
        """Add a task to a phase."""
        phase = self._get_phase(phase_num)
        if not phase:
            print(f"Error: Phase {phase_num} not found")
            sys.exit(1)

        task = {
            'description': task_description,
            'completed': False,
            'completed_at': None
        }

        phase['tasks'].append(task)
        self._update_progress(phase_num)

        print(f"✓ Added task to Phase {phase_num}: {task_description}")
        self._save_state()

    def update_task(self, phase_num: int, task_description: str, completed: bool) -> None:
        """Update task completion status."""
        phase = self._get_phase(phase_num)
        if not phase:
            print(f"Error: Phase {phase_num} not found")
            sys.exit(1)

        # Find task by description
        task = None
        for t in phase['tasks']:
            if t['description'] == task_description:
                task = t
                break

        if not task:
            print(f"Error: Task not found: {task_description}")
            sys.exit(1)

        task['completed'] = completed
        if completed:
            task['completed_at'] = datetime.now().isoformat()
            self._add_activity(
                'task_completed',
                f"Completed task in Phase {phase_num}: {task_description}",
                {'phase': phase_num}
            )
        else:
            task['completed_at'] = None

        self._update_progress(phase_num)

        print(f"✓ Updated task: {task_description} (completed: {completed})")
        self._save_state()

    # =========================================================================
    # QUALITY GATE OPERATIONS
    # =========================================================================

    def quality_gate(
        self,
        phase_num: int,
        gate_name: str,
        status: str,
        score: Optional[int] = None,
        issues: Optional[list] = None
    ) -> None:
        """Record quality gate result."""
        phase = self._get_phase(phase_num)
        if not phase:
            print(f"Error: Phase {phase_num} not found")
            sys.exit(1)

        # Find or create quality gate
        gate = None
        for g in phase['quality_gates']:
            if g['name'] == gate_name:
                gate = g
                break

        if not gate:
            # Create new quality gate
            gate = {
                'name': gate_name,
                'status': status,
                'score': score,
                'threshold': 85,  # Default
                'blocking': True,  # Default
                'checked_at': None,
                'issues': issues or []
            }
            phase['quality_gates'].append(gate)
        else:
            gate['status'] = status
            gate['score'] = score
            if issues:
                gate['issues'] = issues

        gate['checked_at'] = datetime.now().isoformat()

        # Log activity
        if score is not None and gate.get('threshold'):
            desc = f"Quality gate '{gate_name}' {status} in Phase {phase_num} ({score}/{gate['threshold']})"
        else:
            desc = f"Quality gate '{gate_name}' {status} in Phase {phase_num}"

        self._add_activity(
            'quality_gate',
            desc,
            {
                'phase': phase_num,
                'gate': gate_name,
                'status': status,
                'score': score
            }
        )

        print(f"✓ Quality gate recorded: {gate_name} ({status})")
        self._save_state()

    # =========================================================================
    # ACTIVITY LOG
    # =========================================================================

    def add_log_entry(self, log_type: str, description: str, metadata: Optional[Dict] = None) -> None:
        """Add a custom activity log entry."""
        self._add_activity(log_type, description, metadata)
        print(f"✓ Activity logged: {description}")
        self._save_state()


def main():
    parser = argparse.ArgumentParser(
        description='Update sprint state file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--state', required=True, help='Path to sprint state file')

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Sprint commands
    subparsers.add_parser('start-sprint', help='Start the sprint')
    subparsers.add_parser('pause-sprint', help='Pause the sprint')
    subparsers.add_parser('resume-sprint', help='Resume the sprint')
    subparsers.add_parser('complete-sprint', help='Complete the sprint')

    # Phase commands
    phase_start = subparsers.add_parser('start-phase', help='Start a phase')
    phase_start.add_argument('--phase', type=int, required=True, help='Phase number')

    phase_complete = subparsers.add_parser('complete-phase', help='Complete a phase')
    phase_complete.add_argument('--phase', type=int, required=True, help='Phase number')

    # Agent command
    agent_log = subparsers.add_parser('log-agent', help='Log agent execution')
    agent_log.add_argument('--phase', type=int, required=True, help='Phase number')
    agent_log.add_argument('--agent', required=True, help='Agent name')
    agent_log.add_argument('--status', required=True, choices=['started', 'completed', 'failed'])
    agent_log.add_argument('--notes', default='', help='Optional notes')

    # Task commands
    task_add = subparsers.add_parser('add-task', help='Add a task')
    task_add.add_argument('--phase', type=int, required=True, help='Phase number')
    task_add.add_argument('--task', required=True, help='Task description')

    task_update = subparsers.add_parser('update-task', help='Update task status')
    task_update.add_argument('--phase', type=int, required=True, help='Phase number')
    task_update.add_argument('--task', required=True, help='Task description')
    task_update.add_argument('--completed', action='store_true', help='Mark as completed')
    task_update.add_argument('--not-completed', action='store_true', help='Mark as not completed')

    # Quality gate command
    gate = subparsers.add_parser('quality-gate', help='Record quality gate result')
    gate.add_argument('--phase', type=int, required=True, help='Phase number')
    gate.add_argument('--gate', required=True, help='Quality gate name')
    gate.add_argument('--status', required=True, choices=['not_run', 'running', 'passed', 'failed'])
    gate.add_argument('--score', type=int, help='Quality gate score')
    gate.add_argument('--issue', action='append', dest='issues', help='Issue found (can be repeated)')

    # Activity log command
    log = subparsers.add_parser('log', help='Add activity log entry')
    log.add_argument('--type', required=True, help='Activity type')
    log.add_argument('--description', required=True, help='Activity description')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Initialize updater
    updater = SprintStateUpdater(Path(args.state))

    # Execute command
    if args.command == 'start-sprint':
        updater.start_sprint()
    elif args.command == 'pause-sprint':
        updater.pause_sprint()
    elif args.command == 'resume-sprint':
        updater.resume_sprint()
    elif args.command == 'complete-sprint':
        updater.complete_sprint()
    elif args.command == 'start-phase':
        updater.start_phase(args.phase)
    elif args.command == 'complete-phase':
        updater.complete_phase(args.phase)
    elif args.command == 'log-agent':
        updater.log_agent(args.phase, args.agent, args.status, args.notes)
    elif args.command == 'add-task':
        updater.add_task(args.phase, args.task)
    elif args.command == 'update-task':
        if args.completed and args.not_completed:
            print("Error: Cannot specify both --completed and --not-completed")
            sys.exit(1)
        completed = args.completed if args.completed else False
        updater.update_task(args.phase, args.task, completed)
    elif args.command == 'quality-gate':
        updater.quality_gate(args.phase, args.gate, args.status, args.score, args.issues)
    elif args.command == 'log':
        updater.add_log_entry(args.type, args.description)


if __name__ == '__main__':
    main()
