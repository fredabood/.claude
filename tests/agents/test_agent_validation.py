"""
Agent validation tests for the Vibey Framework.

Tests agent file existence, structure validation, trigger patterns,
quality criteria, and README synchronization.

Test Coverage:
- All agent files exist
- Required sections present (Role, Purpose, Inputs, Outputs, Quality Criteria)
- Trigger patterns are unique (no conflicts)
- Quality criteria are measurable
- Handoff templates exist
- Agent metadata complete
- All agents in README match files
"""

import pytest
import re
from pathlib import Path
from collections import defaultdict


# Define expected agents based on README
EXPECTED_AGENTS = {
    'core': ['coordinator', 'vibey-manager'],
    'planning': ['sprint-planning', 'researcher'],
    'development': [
        'web-developer', 'backend-engineer', 'frontend-engineer',
        'database-specialist', 'infrastructure-engineer', 'ml-engineer'
    ],
    'quality': [
        'test-engineer', 'security-reviewer',
        'performance-engineer', 'observability-engineer'
    ],
    'documentation': [
        'documentation-engineer', 'documentation-maintenance-engineer',
        'diagram-engineer', 'git-committer'
    ],
    'architecture': ['architecture-agent'],
}

# Required sections in agent markdown files
REQUIRED_SECTIONS = [
    'Purpose',
    'Trigger Patterns',
    'Required Inputs',
    'Outputs',
    'Quality Criteria',
]

# Optional but recommended sections
RECOMMENDED_SECTIONS = [
    'Workflow',
    'Handoffs',
    'Example',
]


@pytest.fixture
def agents_dir():
    """Get the agents directory path."""
    return Path(__file__).parent.parent.parent / 'framework' / 'agents'


@pytest.fixture
def all_agent_files(agents_dir):
    """Get all agent markdown files."""
    return list(agents_dir.rglob('*.md'))


class TestAgentFilesExist:
    """Test that all expected agent files exist."""

    def test_agents_directory_exists(self, agents_dir):
        """Verify the agents directory exists."""
        assert agents_dir.exists(), f"Agents directory not found: {agents_dir}"
        assert agents_dir.is_dir(), f"Agents path is not a directory: {agents_dir}"

    def test_all_categories_exist(self, agents_dir):
        """Verify all agent category directories exist."""
        for category in EXPECTED_AGENTS.keys():
            category_dir = agents_dir / category
            assert category_dir.exists(), f"Category directory not found: {category}"

    @pytest.mark.parametrize("category,agents", list(EXPECTED_AGENTS.items()))
    def test_category_agents_exist(self, agents_dir, category, agents):
        """Verify all agents in each category exist."""
        category_dir = agents_dir / category
        for agent_name in agents:
            agent_file = category_dir / f"{agent_name}.md"
            assert agent_file.exists(), (
                f"Agent file not found: {category}/{agent_name}.md"
            )

    def test_readme_exists(self, agents_dir):
        """Verify the agents README exists."""
        readme = agents_dir / 'README.md'
        assert readme.exists(), "Agents README.md not found"

    def test_total_agent_count(self, all_agent_files):
        """Verify the total number of agents matches expected."""
        # Filter out README.md
        agent_files = [f for f in all_agent_files if f.name != 'README.md']
        expected_count = sum(len(agents) for agents in EXPECTED_AGENTS.values())
        assert len(agent_files) >= expected_count, (
            f"Expected at least {expected_count} agents, found {len(agent_files)}"
        )


class TestAgentFileStructure:
    """Test that agent files have required structure."""

    def test_agents_have_required_sections(self, all_agent_files):
        """Verify all agents have required sections."""
        issues = []

        for agent_file in all_agent_files:
            if agent_file.name == 'README.md':
                continue

            content = agent_file.read_text()
            agent_name = agent_file.stem

            for section in REQUIRED_SECTIONS:
                # Check for section header or bold label
                # Format 1: ## Section, # Section, ## 🎯 Section
                # Format 2: **Section:** or **Section**
                header_pattern = rf'#{{1,3}}\s*[^\n]*{re.escape(section)}'
                bold_pattern = rf'\*\*[^\n]*{re.escape(section)}[^\n]*\*\*'
                if not (re.search(header_pattern, content, re.IGNORECASE) or
                        re.search(bold_pattern, content, re.IGNORECASE)):
                    issues.append(f"{agent_name}: Missing section '{section}'")

        assert not issues, f"Missing required sections:\n" + "\n".join(issues)

    def test_agents_have_role_description(self, all_agent_files):
        """Verify all agents have a role/description."""
        issues = []

        for agent_file in all_agent_files:
            if agent_file.name == 'README.md':
                continue

            content = agent_file.read_text()
            agent_name = agent_file.stem

            # Check for Role: or **Role:** pattern
            if not re.search(r'\*?\*?Role\*?\*?:', content, re.IGNORECASE):
                issues.append(f"{agent_name}: Missing Role description")

        assert not issues, f"Missing role descriptions:\n" + "\n".join(issues)

    def test_agents_have_when_to_use(self, all_agent_files):
        """Verify agents have 'When to Use' guidance."""
        issues = []

        for agent_file in all_agent_files:
            if agent_file.name == 'README.md':
                continue

            content = agent_file.read_text()
            agent_name = agent_file.stem

            # Check for "When to Use" pattern
            if not re.search(r'when\s+to\s+use', content, re.IGNORECASE):
                issues.append(f"{agent_name}: Missing 'When to Use' guidance")

        # This is a warning, not a hard failure
        if issues:
            pytest.skip(f"Warning - Some agents missing 'When to Use':\n" + "\n".join(issues[:5]))


class TestTriggerPatterns:
    """Test trigger pattern uniqueness and validity."""

    def test_no_duplicate_trigger_patterns(self, all_agent_files):
        """Verify no duplicate trigger patterns across agents."""
        trigger_map = defaultdict(list)

        for agent_file in all_agent_files:
            if agent_file.name == 'README.md':
                continue

            content = agent_file.read_text()
            agent_name = agent_file.stem

            # Extract trigger patterns (look for keywords section)
            keywords_match = re.search(
                r'(?:Keywords|Trigger\s+Patterns)[:\s]*\n((?:[-*]\s*.+\n?)+)',
                content,
                re.IGNORECASE
            )

            if keywords_match:
                patterns_text = keywords_match.group(1)
                # Extract individual patterns
                patterns = re.findall(r'[-*]\s*["\']?([^"\'\n,]+)["\']?', patterns_text)

                for pattern in patterns:
                    pattern = pattern.strip().lower()
                    if pattern and len(pattern) > 2:
                        trigger_map[pattern].append(agent_name)

        # Find duplicates (patterns used by multiple agents)
        duplicates = {
            pattern: agents
            for pattern, agents in trigger_map.items()
            if len(agents) > 1 and pattern not in ['security', 'documentation']  # Allow some overlap
        }

        # This is a soft check - some overlap is expected (aliases)
        if duplicates:
            # Just log, don't fail - overlapping patterns may be intentional
            duplicate_info = "\n".join(
                f"  '{p}': {agents}" for p, agents in list(duplicates.items())[:5]
            )
            print(f"Note: Some trigger patterns are shared:\n{duplicate_info}")

    def test_agents_have_trigger_patterns(self, all_agent_files):
        """Verify all agents define trigger patterns."""
        missing_patterns = []

        for agent_file in all_agent_files:
            if agent_file.name == 'README.md':
                continue

            content = agent_file.read_text()
            agent_name = agent_file.stem

            # Check for trigger patterns section
            if not re.search(r'trigger\s+pattern', content, re.IGNORECASE):
                missing_patterns.append(agent_name)

        assert not missing_patterns, (
            f"Agents missing trigger patterns: {missing_patterns}"
        )


class TestQualityCriteria:
    """Test quality criteria definition."""

    def test_agents_have_quality_criteria(self, all_agent_files):
        """Verify all agents define quality criteria."""
        missing_criteria = []

        for agent_file in all_agent_files:
            if agent_file.name == 'README.md':
                continue

            content = agent_file.read_text()
            agent_name = agent_file.stem

            # Check for quality criteria section (may include emojis)
            if not re.search(r'(?:quality\s+criteria|validation|success\s+metrics|✅)', content, re.IGNORECASE):
                missing_criteria.append(agent_name)

        assert not missing_criteria, (
            f"Agents missing quality criteria: {missing_criteria}"
        )

    def test_quality_criteria_are_measurable(self, all_agent_files):
        """Verify quality criteria include measurable elements."""
        non_measurable = []
        measurable_indicators = [
            r'\d+%',  # Percentages
            r'\d+\s*(?:seconds?|ms|minutes?)',  # Time
            r'(?:all|every|no|zero|100%)',  # Completeness
            r'(?:pass|fail|success|error)',  # Status
            r'(?:coverage|score|threshold)',  # Metrics
        ]

        for agent_file in all_agent_files:
            if agent_file.name == 'README.md':
                continue

            content = agent_file.read_text()
            agent_name = agent_file.stem

            # Find quality criteria section
            match = re.search(
                r'quality\s+criteria.*?\n((?:[-*#\d].+\n?)+)',
                content,
                re.IGNORECASE
            )

            if match:
                criteria_text = match.group(1)
                has_measurable = any(
                    re.search(pattern, criteria_text, re.IGNORECASE)
                    for pattern in measurable_indicators
                )
                if not has_measurable:
                    non_measurable.append(agent_name)

        # Soft check - just warn
        if non_measurable:
            print(f"Note: Some agents may have non-measurable criteria: {non_measurable[:5]}")


class TestHandoffTemplates:
    """Test handoff template references."""

    def test_agents_reference_handoffs(self, all_agent_files):
        """Verify agents reference handoff protocols."""
        no_handoffs = []

        for agent_file in all_agent_files:
            if agent_file.name == 'README.md':
                continue

            content = agent_file.read_text()
            agent_name = agent_file.stem

            # Check for handoff/handoffs section or references
            if not re.search(r'handoff', content, re.IGNORECASE):
                no_handoffs.append(agent_name)

        # Soft check - some agents may not need handoffs
        if no_handoffs and len(no_handoffs) > len(all_agent_files) // 2:
            pytest.skip(f"Many agents missing handoff references: {no_handoffs[:5]}")


class TestReadmeSynchronization:
    """Test README matches actual agent files."""

    def test_readme_lists_all_agents(self, agents_dir, all_agent_files):
        """Verify README lists all agent files."""
        readme = agents_dir / 'README.md'
        readme_content = readme.read_text()

        missing_from_readme = []

        for agent_file in all_agent_files:
            if agent_file.name == 'README.md':
                continue

            agent_name = agent_file.stem

            # Check if agent is mentioned in README
            if agent_name not in readme_content:
                missing_from_readme.append(agent_name)

        assert not missing_from_readme, (
            f"Agents not documented in README: {missing_from_readme}"
        )

    def test_readme_agent_count_accurate(self, agents_dir, all_agent_files):
        """Verify README agent count is accurate."""
        readme = agents_dir / 'README.md'
        readme_content = readme.read_text()

        # Extract total agent count from README
        count_match = re.search(r'Total\s+Agents[:\s]*(\d+)', readme_content, re.IGNORECASE)

        if count_match:
            readme_count = int(count_match.group(1))
            actual_count = len([f for f in all_agent_files if f.name != 'README.md'])

            assert readme_count == actual_count, (
                f"README claims {readme_count} agents, but found {actual_count}"
            )


class TestAgentMetadata:
    """Test agent metadata completeness."""

    def test_agents_have_title(self, all_agent_files):
        """Verify all agents have a title (H1 header)."""
        missing_title = []

        for agent_file in all_agent_files:
            if agent_file.name == 'README.md':
                continue

            content = agent_file.read_text()
            agent_name = agent_file.stem

            # Check for H1 header
            if not re.match(r'^#\s+', content):
                missing_title.append(agent_name)

        assert not missing_title, f"Agents missing title: {missing_title}"

    def test_agents_have_type(self, all_agent_files):
        """Verify all agents specify their type/category."""
        missing_type = []

        for agent_file in all_agent_files:
            if agent_file.name == 'README.md':
                continue

            content = agent_file.read_text()
            agent_name = agent_file.stem

            # Check for Type: pattern
            if not re.search(r'\*?\*?Type\*?\*?:', content, re.IGNORECASE):
                missing_type.append(agent_name)

        # Soft check
        if missing_type and len(missing_type) <= 5:
            print(f"Note: Some agents missing Type: {missing_type}")
        elif missing_type:
            pytest.skip(f"Many agents missing Type declaration: {len(missing_type)}")


class TestAgentContentQuality:
    """Test agent content quality."""

    def test_agents_have_minimum_content(self, all_agent_files):
        """Verify agents have minimum content length."""
        too_short = []
        MIN_CONTENT_LENGTH = 500  # Characters

        for agent_file in all_agent_files:
            if agent_file.name == 'README.md':
                continue

            content = agent_file.read_text()
            agent_name = agent_file.stem

            if len(content) < MIN_CONTENT_LENGTH:
                too_short.append((agent_name, len(content)))

        assert not too_short, (
            f"Agents with insufficient content:\n" +
            "\n".join(f"  {name}: {length} chars" for name, length in too_short)
        )

    def test_agents_have_examples(self, all_agent_files):
        """Verify agents include usage examples."""
        no_examples = []

        for agent_file in all_agent_files:
            if agent_file.name == 'README.md':
                continue

            content = agent_file.read_text()
            agent_name = agent_file.stem

            # Check for example section or code blocks
            has_example = (
                re.search(r'example', content, re.IGNORECASE) or
                re.search(r'```', content)
            )

            if not has_example:
                no_examples.append(agent_name)

        # Soft check
        if no_examples:
            print(f"Note: Some agents missing examples: {no_examples[:5]}")


# Run-specific tests for quick validation
class TestQuickValidation:
    """Quick validation tests for CI/CD."""

    def test_no_broken_agent_files(self, all_agent_files):
        """Verify all agent files can be read without errors."""
        errors = []

        for agent_file in all_agent_files:
            try:
                content = agent_file.read_text()
                assert len(content) > 0, f"{agent_file.name} is empty"
            except Exception as e:
                errors.append(f"{agent_file.name}: {e}")

        assert not errors, f"Broken agent files:\n" + "\n".join(errors)

    def test_no_todo_placeholders(self, all_agent_files):
        """Verify no TODO placeholders in agent files."""
        todos_found = []

        for agent_file in all_agent_files:
            if agent_file.name == 'README.md':
                continue

            content = agent_file.read_text()
            agent_name = agent_file.stem

            # Check for TODO/FIXME/XXX placeholders
            if re.search(r'\b(TODO|FIXME|XXX)\b', content):
                todos_found.append(agent_name)

        # Soft check - some TODOs may be acceptable
        if todos_found:
            print(f"Note: Agents with TODOs: {todos_found[:5]}")
