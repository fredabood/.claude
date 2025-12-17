#!/usr/bin/env python3
"""
AI-Powered Roadmap Analyzer

Analyzes project roadmap to identify optimization opportunities for:
- Missing specialized agents
- Unused/underutilized agents
- Workflow gaps
- Handoff inefficiencies
- Technology-specific enhancements

Usage:
    python3 analyze-project-roadmap.py \\
        --roadmap .vibey/roadmap.yaml \\
        --agents .claude/agents \\
        --workflows .claude/workflows \\
        --output /tmp/optimization-report.md
"""

import argparse
import json
import yaml
import sys
from pathlib import Path
from typing import Dict, List, Optional
from collections import Counter, defaultdict
import re


class ProjectAnalyzer:
    """Analyze project roadmap and recommend agent library optimizations."""

    def __init__(self, roadmap_file: Path, agents_dir: Path, workflows_dir: Path):
        self.roadmap_file = roadmap_file
        self.agents_dir = agents_dir
        self.workflows_dir = workflows_dir

        self.roadmap_data = None
        self.tasks = []
        self.agents = {}
        self.workflows = {}
        self.recommendations = []

    def analyze(self) -> List[Dict]:
        """Run complete analysis and return recommendations."""
        print("🔍 Analyzing project roadmap...", file=sys.stderr)

        # Load data
        self._load_roadmap()
        self._load_tasks()
        self._load_agents()
        self._load_workflows()

        # Run analyses
        self.recommendations = []
        self.recommendations.extend(self._find_missing_agents())
        self.recommendations.extend(self._find_unused_agents())
        self.recommendations.extend(self._find_workflow_opportunities())
        self.recommendations.extend(self._find_technology_enhancements())

        # Sort by impact and confidence
        self.recommendations.sort(
            key=lambda r: (
                {"high": 3, "medium": 2, "low": 1}[r["impact"]],
                r["confidence"]
            ),
            reverse=True
        )

        return self.recommendations

    def _load_roadmap(self):
        """Load roadmap YAML file."""
        with open(self.roadmap_file) as f:
            self.roadmap_data = yaml.safe_load(f)
        print(f"✓ Loaded roadmap: {self.roadmap_data.get('roadmap', {}).get('id', 'unknown')}", file=sys.stderr)

    def _load_tasks(self):
        """Load all tasks from .vibey/tasks/."""
        tasks_dir = self.roadmap_file.parent / "tasks"
        if not tasks_dir.exists():
            print("⚠️  No tasks directory found", file=sys.stderr)
            return

        for task_file in tasks_dir.glob("*.yaml"):
            with open(task_file) as f:
                data = yaml.safe_load(f)
                if "tasks" in data:
                    self.tasks.extend(data["tasks"])

        print(f"✓ Loaded {len(self.tasks)} tasks", file=sys.stderr)

    def _load_agents(self):
        """Load all agent definitions."""
        for agent_file in self.agents_dir.rglob("*.md"):
            # Skip custom agents for base analysis
            if "custom" in agent_file.parts:
                continue

            agent_id = agent_file.stem
            with open(agent_file) as f:
                content = f.read()

                # Extract agent metadata
                agent_data = {
                    "id": agent_id,
                    "file": str(agent_file),
                    "purpose": self._extract_field(content, "Purpose"),
                    "expertise": self._extract_field(content, "Expertise"),
                    "keywords": self._extract_keywords(content),
                }
                self.agents[agent_id] = agent_data

        print(f"✓ Loaded {len(self.agents)} agents", file=sys.stderr)

    def _load_workflows(self):
        """Load all workflow definitions."""
        for workflow_file in self.workflows_dir.rglob("*.md"):
            if "custom" in workflow_file.parts:
                continue

            workflow_id = workflow_file.stem
            with open(workflow_file) as f:
                content = f.read()

                workflow_data = {
                    "id": workflow_id,
                    "file": str(workflow_file),
                    "purpose": self._extract_field(content, "Purpose"),
                }
                self.workflows[workflow_id] = workflow_data

        print(f"✓ Loaded {len(self.workflows)} workflows", file=sys.stderr)

    def _extract_field(self, content: str, field_name: str) -> Optional[str]:
        """Extract a field value from agent/workflow markdown."""
        pattern = rf"\*\*{field_name}:\*\*\s*(.+?)(?:\n|$)"
        match = re.search(pattern, content)
        return match.group(1).strip() if match else None

    def _extract_keywords(self, content: str) -> List[str]:
        """Extract trigger keywords from agent markdown."""
        keywords = []

        # Find Keywords section
        keywords_match = re.search(r"\*\*Keywords:\*\*\s*(.+?)(?:\n\n|\*\*)", content, re.DOTALL)
        if keywords_match:
            keywords_text = keywords_match.group(1)
            # Extract keywords from bullet list or comma-separated
            keywords = re.findall(r"(?:^|\s|,|-)\s*([a-z][a-z0-9-]+)", keywords_text, re.IGNORECASE | re.MULTILINE)

        return [k.lower() for k in keywords if len(k) > 2]

    def _find_missing_agents(self) -> List[Dict]:
        """Identify missing specialized agents based on task patterns."""
        recommendations = []

        # Collect all keywords from tasks
        task_keywords = []
        task_technologies = []

        for task in self.tasks:
            title = task.get("title", "").lower()
            description = task.get("description", "").lower()

            # Extract potential keywords
            words = re.findall(r"\b([a-z]{3,})\b", title + " " + description)
            task_keywords.extend(words)

            # Extract technology mentions
            tech_patterns = [
                r"\b(terraform|kubernetes|docker|ansible|jenkins)\b",  # Infrastructure
                r"\b(react|vue|angular|svelte|next\.?js)\b",  # Frontend
                r"\b(graphql|rest|grpc|websocket)\b",  # API
                r"\b(postgres|mysql|mongodb|redis|dynamodb)\b",  # Database
                r"\b(aws|azure|gcp|cloudflare)\b",  # Cloud
            ]
            for pattern in tech_patterns:
                matches = re.findall(pattern, title + " " + description, re.IGNORECASE)
                task_technologies.extend([m.lower() for m in matches])

        # Count keyword frequencies
        keyword_freq = Counter(task_keywords)
        tech_freq = Counter(task_technologies)

        # Find technologies with high frequency but no specialized agent
        for tech, count in tech_freq.most_common(10):
            if count < 3:  # At least 3 tasks
                continue

            # Check if we have an agent for this technology
            has_agent = any(
                tech in agent["keywords"] or tech in (agent.get("expertise") or "").lower()
                for agent in self.agents.values()
            )

            if not has_agent:
                # Calculate confidence based on frequency
                total_tasks = len(self.tasks)
                percentage = (count / total_tasks * 100) if total_tasks > 0 else 0
                confidence = min(95, 60 + percentage * 2)  # Scale to 60-95%

                impact = "high" if percentage > 20 else "medium" if percentage > 10 else "low"

                recommendations.append({
                    "type": "create_agent",
                    "name": f"{tech.title()} Specialist",
                    "agent_id": f"{tech}-specialist",
                    "technology": tech,
                    "reason": f"{count} tasks involve {tech} ({percentage:.0f}% of roadmap)",
                    "confidence": confidence,
                    "impact": impact,
                    "task_count": count,
                    "keywords": [tech] + [k for k, c in keyword_freq.most_common(20) if tech in k],
                })

        return recommendations

    def _find_unused_agents(self) -> List[Dict]:
        """Identify agents that aren't being used."""
        recommendations = []

        # Count agent assignments
        agent_usage = Counter()
        for task in self.tasks:
            assigned_agents = task.get("assigned_agents", [])
            for agent in assigned_agents:
                agent_usage[agent] += 1

        # Find unused agents
        for agent_id, agent_data in self.agents.items():
            usage_count = agent_usage.get(agent_id, 0)

            # Skip core agents
            if agent_id in ["coordinator", "vibey-manager"]:
                continue

            if usage_count == 0:
                recommendations.append({
                    "type": "disable_agent",
                    "name": agent_id.replace("-", " ").title(),
                    "agent_id": agent_id,
                    "reason": "0 tasks assigned, not used in roadmap",
                    "confidence": 60,
                    "impact": "low",
                    "task_count": 0,
                })

        return recommendations

    def _find_workflow_opportunities(self) -> List[Dict]:
        """Identify common task patterns that could be workflows."""
        recommendations = []

        # Group tasks by similarity
        task_patterns = defaultdict(list)

        for task in self.tasks:
            # Extract key pattern indicators
            title = task.get("title", "").lower()

            # Look for common patterns
            patterns = [
                ("component", r"(component|widget|ui element)"),
                ("api", r"(api|endpoint|route|controller)"),
                ("database", r"(database|migration|schema|model)"),
                ("test", r"(test|testing|qa|integration test)"),
                ("documentation", r"(documentation|docs|readme|guide)"),
            ]

            for pattern_name, pattern_regex in patterns:
                if re.search(pattern_regex, title):
                    task_patterns[pattern_name].append(task)

        # Recommend workflows for patterns with 4+ tasks
        for pattern_name, pattern_tasks in task_patterns.items():
            if len(pattern_tasks) < 4:
                continue

            # Check if workflow already exists
            has_workflow = any(
                pattern_name in workflow["id"] or pattern_name in (workflow.get("purpose") or "").lower()
                for workflow in self.workflows.values()
            )

            if not has_workflow:
                total_tasks = len(self.tasks)
                percentage = (len(pattern_tasks) / total_tasks * 100) if total_tasks > 0 else 0
                confidence = min(95, 55 + percentage * 3)

                impact = "high" if percentage > 15 else "medium" if percentage > 8 else "low"

                recommendations.append({
                    "type": "create_workflow",
                    "name": f"{pattern_name.title()} Development Workflow",
                    "workflow_id": f"{pattern_name}-development",
                    "pattern": pattern_name,
                    "reason": f"{len(pattern_tasks)} tasks follow similar pattern",
                    "confidence": confidence,
                    "impact": impact,
                    "task_count": len(pattern_tasks),
                    "sample_tasks": [t.get("id") for t in pattern_tasks[:3]],
                })

        return recommendations

    def _find_technology_enhancements(self) -> List[Dict]:
        """Identify technology-specific enhancements to existing agents."""
        recommendations = []

        # Extract technologies from tasks
        tech_keywords = []
        for task in self.tasks:
            title = task.get("title", "").lower()
            description = task.get("description", "").lower()

            # Technology patterns
            techs = re.findall(
                r"\b(graphql|typescript|python|rust|go|java|kotlin|swift)\b",
                title + " " + description,
                re.IGNORECASE
            )
            tech_keywords.extend([t.lower() for t in techs])

        tech_freq = Counter(tech_keywords)

        # Find technologies used frequently but not well-supported in agents
        for tech, count in tech_freq.most_common(5):
            if count < 3:
                continue

            # Find which agent should handle this
            candidate_agents = ["web-developer", "ml-engineer", "backend-specialist"]

            for agent_id in candidate_agents:
                if agent_id not in self.agents:
                    continue

                agent = self.agents[agent_id]
                keywords = agent.get("keywords", [])

                # Check if agent lacks this technology
                if tech not in keywords:
                    total_tasks = len(self.tasks)
                    percentage = (count / total_tasks * 100) if total_tasks > 0 else 0
                    confidence = min(90, 50 + percentage * 2)

                    impact = "medium" if percentage > 10 else "low"

                    recommendations.append({
                        "type": "enhance_agent",
                        "name": agent_id.replace("-", " ").title(),
                        "agent_id": agent_id,
                        "technology": tech,
                        "reason": f"{count} tasks involve {tech}, but {agent_id} lacks specific support",
                        "confidence": confidence,
                        "impact": impact,
                        "task_count": count,
                        "enhancement": f"Add {tech.title()} expertise section",
                    })
                    break  # Only recommend once per technology

        return recommendations

    def generate_report(self, output_file: Path):
        """Generate markdown report of recommendations."""
        with open(output_file, "w") as f:
            f.write("# Roadmap Optimization Report\n\n")
            f.write(f"**Generated:** {self.roadmap_data.get('roadmap', {}).get('id', 'unknown')}\n\n")

            # Summary
            f.write("## Analysis Summary\n\n")
            f.write(f"- **Tasks Analyzed:** {len(self.tasks)}\n")
            f.write(f"- **Current Agents:** {len(self.agents)}\n")
            f.write(f"- **Current Workflows:** {len(self.workflows)}\n")
            f.write(f"- **Recommendations:** {len(self.recommendations)}\n\n")

            # Recommendations by impact
            for impact_level in ["high", "medium", "low"]:
                impact_recs = [r for r in self.recommendations if r["impact"] == impact_level]
                if not impact_recs:
                    continue

                emoji = {"high": "🟢", "medium": "🟡", "low": "🔵"}[impact_level]
                f.write(f"## {emoji} {impact_level.title()} Impact Recommendations\n\n")

                for i, rec in enumerate(impact_recs, 1):
                    f.write(f"### {i}. {rec['name']} (Confidence: {rec['confidence']:.0f}%)\n\n")
                    f.write(f"**Type:** {rec['type'].replace('_', ' ').title()}\n\n")
                    f.write(f"**Reason:** {rec['reason']}\n\n")

                    if rec["type"] == "create_agent":
                        f.write(f"**Technology:** {rec['technology']}\n\n")
                        f.write(f"**Suggested Keywords:** {', '.join(rec['keywords'][:10])}\n\n")
                    elif rec["type"] == "create_workflow":
                        f.write(f"**Pattern:** {rec['pattern']}\n\n")
                        f.write(f"**Sample Tasks:** {', '.join(rec['sample_tasks'])}\n\n")
                    elif rec["type"] == "enhance_agent":
                        f.write(f"**Enhancement:** {rec['enhancement']}\n\n")

                    f.write(f"**Impact:** {rec['task_count']} tasks affected\n\n")
                    f.write("---\n\n")

        print(f"✅ Report generated: {output_file}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Analyze project roadmap for optimization opportunities")
    parser.add_argument("--roadmap", required=True, type=Path, help="Path to roadmap.yaml")
    parser.add_argument("--agents", required=True, type=Path, help="Path to agents directory")
    parser.add_argument("--workflows", required=True, type=Path, help="Path to workflows directory")
    parser.add_argument("--output", required=True, type=Path, help="Output report file")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of markdown")

    args = parser.parse_args()

    # Validate inputs
    if not args.roadmap.exists():
        print(f"❌ Roadmap file not found: {args.roadmap}", file=sys.stderr)
        sys.exit(1)

    if not args.agents.exists():
        print(f"❌ Agents directory not found: {args.agents}", file=sys.stderr)
        sys.exit(1)

    if not args.workflows.exists():
        print(f"❌ Workflows directory not found: {args.workflows}", file=sys.stderr)
        sys.exit(1)

    # Run analysis
    analyzer = ProjectAnalyzer(args.roadmap, args.agents, args.workflows)
    recommendations = analyzer.analyze()

    # Output results
    if args.json:
        with open(args.output, "w") as f:
            json.dump(recommendations, f, indent=2)
        print(f"✅ JSON report generated: {args.output}", file=sys.stderr)
    else:
        analyzer.generate_report(args.output)

    # Print summary to stderr
    print(f"\n📊 Analysis Complete:", file=sys.stderr)
    print(f"   - {len([r for r in recommendations if r['impact'] == 'high'])} high-impact recommendations", file=sys.stderr)
    print(f"   - {len([r for r in recommendations if r['impact'] == 'medium'])} medium-impact recommendations", file=sys.stderr)
    print(f"   - {len([r for r in recommendations if r['impact'] == 'low'])} low-impact recommendations", file=sys.stderr)


if __name__ == "__main__":
    main()
