"""
Sprint Plan Parser

Parses markdown sprint plans into structured data for roadmap system.
Handles simple format used by Vibey sprint plans.
"""

import re
from pathlib import Path
from typing import Dict, List


class SprintPlanParser:
    """Parse sprint plan markdown into structured data."""

    def __init__(self, plan_file: Path):
        self.plan_file = plan_file
        self.content = plan_file.read_text()
        self.lines = self.content.split('\n')

    def parse(self) -> Dict:
        """
        Parse complete sprint plan.

        Returns:
            {
                'name': str,
                'goal': str,
                'features': [{'name': str, 'what': str, 'why': str, 'how': str}],
                'success_criteria': [str],
                'deliverables': [str],
                'quality_gates': [{'name': str, 'threshold': int}],
            }
        """
        return {
            'name': self._extract_sprint_name(),
            'goal': self._extract_goal(),
            'features': self._extract_features(),
            'success_criteria': self._extract_success_criteria(),
            'deliverables': self._extract_deliverables(),
            'quality_gates': self._extract_quality_gates(),
        }

    def _extract_sprint_name(self) -> str:
        """Extract sprint name from # heading."""
        for line in self.lines:
            # Match: # Sprint Plan: Name
            if line.startswith('# Sprint Plan:'):
                return line.replace('# Sprint Plan:', '').strip()
            # Match: # Sprint N: Name
            match = re.match(r'^# Sprint \d+:\s*(.+)$', line)
            if match:
                return match.group(1).strip()
        return "Unnamed Sprint"

    def _extract_goal(self) -> str:
        """Extract main goal/objective."""
        goals = []
        in_goals = False

        for line in self.lines:
            if line.startswith('## Goals') or line.startswith('## Objectives'):
                in_goals = True
                continue

            if in_goals:
                if line.startswith('##'):
                    break
                if line.strip() and (line.strip().startswith('-') or re.match(r'^\d+\.', line.strip())):
                    # Remove bullet or number prefix
                    goal = re.sub(r'^[-\d.]+\s*', '', line.strip())
                    goals.append(goal)

        return '; '.join(goals) if goals else ""

    def _extract_features(self) -> List[Dict]:
        """Extract features with their details."""
        features = []
        current_feature = None
        in_features = False
        current_field = None

        for line in self.lines:
            # Section detection
            if line.startswith('## Features') or line.startswith('## Tasks'):
                in_features = True
                continue

            # Exit features section if we hit another ## heading
            if in_features and line.startswith('##') and not line.startswith('###'):
                break

            if in_features:
                # Feature heading: ### 1. Feature Name or ### Feature Name
                if line.startswith('###'):
                    # Save previous feature
                    if current_feature:
                        features.append(current_feature)

                    # Extract name (remove ### and optional number)
                    name = line.replace('###', '').strip()
                    # Remove leading number like "1. " or "1) "
                    name = re.sub(r'^\d+[\.\)]\s*', '', name)

                    current_feature = {
                        'name': name,
                        'what': '',
                        'why': '',
                        'how': ''
                    }
                    current_field = None
                    continue

                if current_feature:
                    # Extract What/Why/How
                    if line.startswith('**What:**'):
                        current_field = 'what'
                        current_feature['what'] = line.replace('**What:**', '').strip()
                    elif line.startswith('**Why:**'):
                        current_field = 'why'
                        current_feature['why'] = line.replace('**Why:**', '').strip()
                    elif line.startswith('**How:**'):
                        current_field = 'how'
                        current_feature['how'] = line.replace('**How:**', '').strip()
                    # Accumulate multi-line content for current field
                    elif line.strip().startswith('-') and current_field:
                        if current_feature[current_field]:
                            current_feature[current_field] += '\n' + line.strip()
                        else:
                            current_feature[current_field] = line.strip()

        # Add last feature
        if current_feature:
            features.append(current_feature)

        return features

    def _extract_success_criteria(self) -> List[str]:
        """Extract success criteria."""
        criteria = []
        in_criteria = False

        for line in self.lines:
            if line.startswith('## Success Criteria') or line.startswith('## Definition of Done'):
                in_criteria = True
                continue

            if in_criteria:
                if line.startswith('##'):
                    break

                # Match: - ✅ Criterion or - [ ] Criterion
                if line.strip().startswith('-'):
                    criterion = re.sub(r'^-\s*[✅✓☑️\[\]x\s]*', '', line.strip())
                    if criterion:
                        criteria.append(criterion)

        return criteria

    def _extract_deliverables(self) -> List[str]:
        """Extract deliverables."""
        deliverables = []
        in_deliverables = False

        for line in self.lines:
            if line.startswith('## Deliverables') or line.startswith('## Expected Outputs'):
                in_deliverables = True
                continue

            if in_deliverables:
                if line.startswith('##'):
                    break
                if line.strip().startswith('-'):
                    deliverable = line.strip().replace('-', '').strip()
                    deliverables.append(deliverable)

        return deliverables

    def _extract_quality_gates(self) -> List[Dict]:
        """Extract quality gates with thresholds."""
        gates = []
        in_gates = False

        for line in self.lines:
            if line.startswith('## Quality Gates'):
                in_gates = True
                continue

            if in_gates:
                if line.startswith('##'):
                    break

                # Parse: - Security Audit (85%) or - Security Audit: 85%
                match = re.match(r'-\s+(.+?)\s*[:\(](\d+)%?[\)]?', line.strip())
                if match:
                    gates.append({
                        'name': match.group(1).strip(),
                        'threshold': int(match.group(2)),
                        'blocking': True,
                        'status': 'not_run'
                    })

        return gates

    def extract_tasks(self) -> List[Dict]:
        """
        Extract individual tasks for roadmap task creation.

        Returns:
            [
                {
                    'name': str,
                    'description': str,
                    'feature': str,  # Parent feature name
                    'estimated_hours': int,
                },
                ...
            ]
        """
        tasks = []
        features = self._extract_features()

        for feature in features:
            # Each feature becomes a task
            task = {
                'name': feature['name'],
                'description': feature['what'] or feature['name'],
                'feature': feature['name'],
                'what': feature['what'],
                'why': feature['why'],
                'how': feature['how'],
                'estimated_hours': self._estimate_hours(feature)
            }
            tasks.append(task)

        return tasks

    def _estimate_hours(self, feature: Dict) -> int:
        """Estimate hours for a feature based on complexity."""
        # Simple heuristic based on "how" description length
        how_text = feature.get('how', '')
        lines = [l for l in how_text.split('\n') if l.strip()]

        if len(lines) > 5:
            return 8  # Complex task
        elif len(lines) > 2:
            return 4  # Medium task
        else:
            return 2  # Simple task


def parse_sprint_plan(plan_file: Path) -> Dict:
    """
    Convenience function to parse a sprint plan.

    Args:
        plan_file: Path to sprint plan markdown file

    Returns:
        Parsed sprint plan data
    """
    parser = SprintPlanParser(plan_file)
    return parser.parse()


def extract_tasks_from_plan(plan_file: Path) -> List[Dict]:
    """
    Convenience function to extract tasks from plan.

    Args:
        plan_file: Path to sprint plan markdown file

    Returns:
        List of task dictionaries
    """
    parser = SprintPlanParser(plan_file)
    return parser.extract_tasks()
