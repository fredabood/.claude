#!/usr/bin/env python3
"""
AI-Powered Agent Generator

Automatically generates specialized agents based on roadmap analysis recommendations.

Usage:
    python3 generate-agent.py \\
        --analysis /tmp/optimization-report.md \\
        --recommendation "terraform-specialist" \\
        --output .claude/agents/custom/terraform-specialist.md

    Or generate from analysis JSON:
    python3 generate-agent.py \\
        --analysis-json /tmp/optimization-report.json \\
        --index 0 \\
        --output .claude/agents/custom/terraform-specialist.md
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List


class AgentGenerator:
    """Generate custom agent files from recommendations."""

    AGENT_TEMPLATE = """# Agent: {name}

**Agent ID:** {agent_id}
**Purpose:** {purpose}
**Expertise:** {expertise}
**Trigger:** {trigger_context}

---

## Overview

You are the **{name}**, an agent specialized in {expertise_lower}.

**Your Role:**
{role_description}

**When You're Active:**
{activation_conditions}

---

## Capabilities

{capabilities}

## Trigger Patterns

**Keywords:** {keywords}
**Contexts:** {contexts}
**File Patterns:** {file_patterns}
**Priority:** {priority}

## Tools & Access

{tools}

## Responsibilities

{responsibilities}

## Process

{process_steps}

## Quality Criteria

{quality_criteria}

## Handoff Points

**Hand Off To:**
{handoff_to}

**Receive From:**
{handoff_from}

---

## Success Criteria

{success_criteria}
"""

    def __init__(self):
        self.recommendation = None
        self.roadmap_tasks = []

    def generate_from_recommendation(self, rec: Dict, output_file: Path):
        """Generate agent file from recommendation dict."""
        self.recommendation = rec

        # Extract recommendation details
        name = rec.get("name", "Custom Agent")
        agent_id = rec.get("agent_id", name.lower().replace(" ", "-"))
        technology = rec.get("technology", rec.get("pattern", ""))
        keywords = rec.get("keywords", [technology])

        # Generate agent content
        content = self._generate_agent_content(name, agent_id, technology, keywords)

        # Write to file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            f.write(content)

        print(f"✅ Agent generated: {output_file}", file=sys.stderr)

    def _generate_agent_content(self, name: str, agent_id: str, technology: str, keywords: List[str]) -> str:
        """Generate full agent markdown content."""

        # Determine agent type from technology
        agent_type = self._infer_agent_type(technology, keywords)

        # Generate sections
        sections = {
            "name": name,
            "agent_id": agent_id,
            "purpose": self._generate_purpose(technology, agent_type),
            "expertise": self._generate_expertise(technology, agent_type),
            "expertise_lower": self._generate_expertise(technology, agent_type).lower(),
            "trigger_context": self._generate_trigger_context(technology),
            "role_description": self._generate_role_description(technology, agent_type),
            "activation_conditions": self._generate_activation_conditions(technology),
            "capabilities": self._generate_capabilities(technology, agent_type),
            "keywords": ", ".join(keywords[:15]),
            "contexts": self._generate_contexts(technology, agent_type),
            "file_patterns": self._generate_file_patterns(technology),
            "priority": "High (when " + technology + " context detected)",
            "tools": self._generate_tools(technology, agent_type),
            "responsibilities": self._generate_responsibilities(technology, agent_type),
            "process_steps": self._generate_process_steps(technology, agent_type),
            "quality_criteria": self._generate_quality_criteria(technology),
            "handoff_to": self._generate_handoff_to(agent_type),
            "handoff_from": self._generate_handoff_from(agent_type),
            "success_criteria": self._generate_success_criteria(technology),
        }

        return self.AGENT_TEMPLATE.format(**sections)

    def _infer_agent_type(self, technology: str, keywords: List[str]) -> str:
        """Infer agent category from technology."""
        tech_lower = technology.lower()
        keywords_str = " ".join(keywords).lower()

        if any(t in tech_lower for t in ["terraform", "kubernetes", "docker", "ansible", "jenkins"]):
            return "infrastructure"
        elif any(t in tech_lower for t in ["react", "vue", "angular", "svelte", "frontend"]):
            return "frontend"
        elif any(t in tech_lower for t in ["graphql", "rest", "api", "grpc"]):
            return "api"
        elif any(t in tech_lower for t in ["postgres", "mysql", "mongodb", "database"]):
            return "database"
        elif any(t in tech_lower for t in ["python", "rust", "go", "java", "backend"]):
            return "backend"
        elif any(t in keywords_str for t in ["test", "qa", "testing"]):
            return "testing"
        else:
            return "development"

    def _generate_purpose(self, technology: str, agent_type: str) -> str:
        """Generate agent purpose statement."""
        type_purposes = {
            "infrastructure": f"Infrastructure as Code development and deployment using {technology.title()}",
            "frontend": f"Frontend development using {technology.title()} framework",
            "api": f"API development and integration using {technology.upper()}",
            "database": f"Database design, migration, and optimization for {technology.title()}",
            "backend": f"Backend development using {technology.title()}",
            "testing": f"Testing and quality assurance for {technology.title()} applications",
            "development": f"{technology.title()} development and implementation",
        }
        return type_purposes.get(agent_type, f"{technology.title()} development")

    def _generate_expertise(self, technology: str, agent_type: str) -> str:
        """Generate expertise description."""
        type_expertise = {
            "infrastructure": f"{technology.title()}, Cloud Infrastructure, Infrastructure as Code, DevOps",
            "frontend": f"{technology.title()}, JavaScript/TypeScript, UI/UX, Frontend Architecture",
            "api": f"{technology.upper()}, API Design, Backend Integration, Microservices",
            "database": f"{technology.title()}, Database Design, SQL, Performance Optimization",
            "backend": f"{technology.title()}, Backend Architecture, API Development, Data Processing",
            "testing": f"Test Automation, {technology.title()}, Quality Assurance, CI/CD",
            "development": f"{technology.title()}, Software Development, Best Practices",
        }
        return type_expertise.get(agent_type, f"{technology.title()}, Software Development")

    def _generate_trigger_context(self, technology: str) -> str:
        """Generate trigger context."""
        return f"{technology} development, implementation, or optimization tasks"

    def _generate_role_description(self, technology: str, agent_type: str) -> str:
        """Generate role description."""
        roles = {
            "infrastructure": f"""- Design and implement {technology} infrastructure code
- Manage cloud resources and deployment
- Optimize infrastructure costs and performance
- Ensure infrastructure security best practices""",
            "frontend": f"""- Build user interfaces with {technology}
- Implement responsive and accessible designs
- Optimize frontend performance
- Integrate with backend APIs""",
            "api": f"""- Design {technology} APIs and schemas
- Implement API endpoints and resolvers
- Optimize query performance
- Ensure API security and validation""",
            "database": f"""- Design database schemas for {technology}
- Create and manage migrations
- Optimize query performance
- Ensure data integrity and security""",
            "backend": f"""- Develop backend services in {technology}
- Implement business logic and data processing
- Design scalable architectures
- Integrate with databases and external services""",
            "testing": f"""- Design and implement test strategies
- Create automated tests with {technology}
- Ensure code quality and coverage
- Integrate tests into CI/CD pipelines""",
            "development": f"""- Develop features using {technology}
- Follow best practices and patterns
- Write maintainable, well-documented code
- Collaborate with other agents""",
        }
        return roles.get(agent_type, f"- Develop solutions using {technology}")

    def _generate_activation_conditions(self, technology: str) -> str:
        """Generate activation conditions."""
        return f"""- Tasks involve {technology} code
- {technology.title()}-related features or changes required
- Technology-specific optimization needed
- {technology.title()} development work"""

    def _generate_capabilities(self, technology: str, agent_type: str) -> str:
        """Generate capabilities section."""
        capabilities = {
            "infrastructure": f"""### Infrastructure Management
- Design reusable infrastructure modules
- Manage cloud resource provisioning
- Handle configuration and state management
- Implement infrastructure versioning

### Deployment & Operations
- Automate deployment processes
- Configure monitoring and alerting
- Implement disaster recovery
- Optimize resource utilization

### Security & Compliance
- Implement security best practices
- Configure access controls and permissions
- Ensure compliance with standards
- Regular security audits""",
            "frontend": f"""### UI Development
- Build reusable components
- Implement responsive layouts
- Handle state management
- Optimize rendering performance

### Integration
- Connect to backend APIs
- Handle authentication flows
- Implement real-time updates
- Manage client-side routing

### Quality
- Write component tests
- Ensure accessibility (WCAG)
- Optimize bundle size
- Cross-browser compatibility""",
            "api": f"""### API Design
- Design schemas and types
- Define queries and mutations
- Handle subscriptions (if applicable)
- Version API contracts

### Implementation
- Implement endpoints/resolvers
- Handle authentication/authorization
- Implement caching strategies
- Error handling and validation

### Optimization
- Prevent N+1 queries
- Implement efficient data loading
- Optimize response times
- Monitor API performance""",
        }

        return capabilities.get(agent_type, f"""### Core Capabilities
- Implement features using {technology}
- Follow {technology} best practices
- Write clean, maintainable code
- Integrate with existing systems

### Quality & Testing
- Write comprehensive tests
- Ensure code quality
- Document implementations
- Handle edge cases""")

    def _generate_contexts(self, technology: str, agent_type: str) -> str:
        """Generate contexts."""
        contexts = {
            "infrastructure": "Infrastructure provisioning, Cloud deployment, DevOps tasks",
            "frontend": "Frontend development, UI implementation, Component building",
            "api": "API development, Backend integration, Service communication",
            "database": "Database design, Data modeling, Migration tasks",
            "backend": "Backend development, Business logic, Data processing",
            "testing": "Test development, Quality assurance, CI/CD integration",
            "development": "Feature development, Implementation tasks, Code changes",
        }
        return contexts.get(agent_type, f"{technology.title()} development")

    def _generate_file_patterns(self, technology: str) -> str:
        """Generate file patterns based on technology."""
        patterns = {
            "terraform": "`**/*.tf`, `**/*.tfvars`, `**/terraform/**/*`",
            "kubernetes": "`**/*.yaml`, `**/*.yml`, `**/k8s/**/*`, `**/manifests/**/*`",
            "react": "`**/*.tsx`, `**/*.jsx`, `**/components/**/*`, `**/pages/**/*`",
            "graphql": "`**/*.graphql`, `**/*.gql`, `**/schema/**/*`, `**/resolvers/**/*`",
            "python": "`**/*.py`, `**/src/**/*.py`, `**/tests/**/*.py`",
            "rust": "`**/*.rs`, `**/src/**/*.rs`, `**/Cargo.toml`",
            "docker": "`**/Dockerfile`, `**/docker-compose.yml`, `**/.dockerignore`",
        }

        return patterns.get(technology.lower(), f"`**/*.{technology.lower()}`")

    def _generate_tools(self, technology: str, agent_type: str) -> str:
        """Generate tools section."""
        tools = {
            "infrastructure": f"""- {technology.title()} CLI
- Cloud provider CLIs (AWS, Azure, GCP)
- Infrastructure validation tools
- Configuration management tools""",
            "frontend": f"""- {technology.title()} development tools
- Build tools (Vite, Webpack, etc.)
- Testing frameworks
- Browser DevTools""",
            "api": f"""- {technology.upper()} development tools
- API testing tools (Postman, GraphQL Playground)
- Schema validation
- Performance profiling""",
            "testing": f"""- {technology.title()} test framework
- Code coverage tools
- CI/CD integration
- Test reporting tools""",
        }

        return tools.get(agent_type, f"""- {technology.title()} development environment
- Code linters and formatters
- Testing frameworks
- Version control (Git)""")

    def _generate_responsibilities(self, technology: str, agent_type: str) -> str:
        """Generate responsibilities."""
        return f"""- Design and implement {technology} solutions
- Follow {technology} best practices and patterns
- Write comprehensive tests for {technology} code
- Document {technology} implementations
- Optimize {technology} performance
- Handle error cases and edge conditions
- Collaborate with other agents on integration"""

    def _generate_process_steps(self, technology: str, agent_type: str) -> str:
        """Generate process steps."""
        return f"""1. **Requirements Analysis**
   - Review task requirements
   - Identify {technology} components needed
   - Plan implementation approach

2. **Design Phase**
   - Design {technology} solution architecture
   - Define interfaces and contracts
   - Plan testing strategy

3. **Implementation Phase**
   - Write {technology} code
   - Follow coding standards
   - Implement error handling

4. **Testing Phase**
   - Write unit tests
   - Run integration tests
   - Verify functionality

5. **Review & Optimization**
   - Code review
   - Performance optimization
   - Security review

6. **Documentation**
   - Update technical documentation
   - Add code comments
   - Document usage examples

7. **Handoff**
   - Prepare handoff documentation
   - Transfer to next agent (if applicable)
   - Ensure all artifacts complete"""

    def _generate_quality_criteria(self, technology: str) -> str:
        """Generate quality criteria."""
        return f"""- ✅ All {technology} code follows best practices
- ✅ Comprehensive test coverage (≥80%)
- ✅ No linting errors or warnings
- ✅ Performance meets requirements
- ✅ Security best practices followed
- ✅ Documentation complete and accurate
- ✅ Code reviewed and approved"""

    def _generate_handoff_to(self, agent_type: str) -> str:
        """Generate handoff to section."""
        handoffs = {
            "infrastructure": "- deployment-engineer (for deployment)\n- security-reviewer (for security audit)\n- docs-writer (for infrastructure documentation)",
            "frontend": "- test-engineer (for testing)\n- docs-writer (for component documentation)\n- security-reviewer (for security review)",
            "api": "- test-engineer (for API testing)\n- docs-writer (for API documentation)\n- frontend-developer (for client integration)",
            "backend": "- test-engineer (for testing)\n- database-specialist (for database changes)\n- api-developer (for API exposure)",
            "testing": "- docs-writer (for test documentation)\n- deployment-engineer (for CI/CD integration)",
            "database": "- backend-developer (for implementation)\n- test-engineer (for data validation)\n- docs-writer (for schema documentation)",
        }
        return handoffs.get(agent_type, "- test-engineer (for testing)\n- docs-writer (for documentation)")

    def _generate_handoff_from(self, agent_type: str) -> str:
        """Generate handoff from section."""
        handoffs = {
            "infrastructure": "- sprint-planner (task assignments)\n- architecture-specialist (infrastructure design)\n- backend-developer (infrastructure requirements)",
            "frontend": "- sprint-planner (task assignments)\n- designer (UI/UX designs)\n- api-developer (API contracts)",
            "api": "- sprint-planner (task assignments)\n- architecture-specialist (API design)\n- database-specialist (data models)",
            "backend": "- sprint-planner (task assignments)\n- architecture-specialist (system design)\n- database-specialist (schema design)",
            "testing": "- Any development agent (code to test)",
            "database": "- sprint-planner (task assignments)\n- architecture-specialist (data architecture)\n- backend-developer (data requirements)",
        }
        return handoffs.get(agent_type, "- sprint-planner (task assignments)\n- coordinator (task routing)")

    def _generate_success_criteria(self, technology: str) -> str:
        """Generate success criteria."""
        return f"""You've successfully completed your work when:
- ✅ {technology.title()} implementation is complete and functional
- ✅ All tests pass successfully
- ✅ Code meets quality standards
- ✅ Documentation is complete
- ✅ Security requirements met
- ✅ Performance benchmarks achieved
- ✅ Handoff to next agent complete (if applicable)"""


def main():
    parser = argparse.ArgumentParser(description="Generate custom agent from recommendation")
    parser.add_argument("--analysis", type=Path, help="Path to analysis markdown file")
    parser.add_argument("--analysis-json", type=Path, help="Path to analysis JSON file")
    parser.add_argument("--recommendation", help="Technology name for recommendation (for markdown)")
    parser.add_argument("--index", type=int, help="Recommendation index (for JSON)")
    parser.add_argument("--output", required=True, type=Path, help="Output agent file path")

    args = parser.parse_args()

    # Load recommendation
    recommendation = None

    if args.analysis_json:
        with open(args.analysis_json) as f:
            recommendations = json.load(f)
            if args.index is not None:
                recommendation = recommendations[args.index]
            else:
                print("❌ --index required when using --analysis-json", file=sys.stderr)
                sys.exit(1)

    elif args.analysis and args.recommendation:
        # Parse markdown report (basic parsing)
        # For production, would parse full markdown
        # For now, create a minimal recommendation dict
        recommendation = {
            "name": args.recommendation.replace("-", " ").title() + " Specialist",
            "agent_id": args.recommendation,
            "technology": args.recommendation,
            "keywords": [args.recommendation],
        }

    else:
        print("❌ Provide either --analysis-json and --index, or --analysis and --recommendation", file=sys.stderr)
        sys.exit(1)

    # Generate agent
    generator = AgentGenerator()
    generator.generate_from_recommendation(recommendation, args.output)

    print(f"✅ Agent file created: {args.output}", file=sys.stderr)
    print(f"   - Agent ID: {recommendation['agent_id']}", file=sys.stderr)
    print(f"   - Technology: {recommendation.get('technology', 'N/A')}", file=sys.stderr)


if __name__ == "__main__":
    main()
