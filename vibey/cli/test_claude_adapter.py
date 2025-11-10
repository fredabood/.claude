#!/usr/bin/env python3
"""
Test Claude Adapter Deployment Generation

Tests the Claude Code platform adapter by generating a deployment.

Usage:
    python3 framework/scripts/test_claude_adapter.py

Created: 2025-11-09
Sprint: core-framework-2, Task 6
"""

import sys
from pathlib import Path

# Add framework to path
framework_dir = Path(__file__).parent.parent
sys.path.insert(0, str(framework_dir.parent))

from framework.platform_adapters.claude_adapter import ClaudeAdapter


def main():
    """Test the Claude adapter."""
    print("🎯 Testing Claude Code Platform Adapter\n")
    print("=" * 60)

    try:
        # Initialize adapter
        print("\n1. Initializing adapter...")
        adapter = ClaudeAdapter()
        print(f"   ✅ Platform: {adapter.get_platform_name()}")
        print(f"   ✅ Deployment Directory: {adapter.get_deployment_dir()}")
        print(f"   ✅ Instructions File: {adapter.get_instructions_filename()}")

        # Validate config
        print("\n2. Validating configuration...")
        if not adapter.validate_config():
            print("   ❌ Configuration invalid - cannot proceed")
            return 1

        print("   ✅ Configuration valid")

        # Check what will be generated
        print("\n3. Checking configured content...")
        agents = adapter.load_all_agents()
        workflows = adapter.load_all_workflows()
        print(f"   ✅ Agents configured: {len(agents)}")
        print(f"   ✅ Workflows configured: {len(workflows)}")

        # Generate deployment
        print("\n4. Generating deployment...")
        print("   (This will create .claude/ directory with backup)")
        adapter.deploy(clean=False, validate=True, backup=True)

        # Verify deployment
        print("\n5. Verifying deployment...")
        deployment_dir = adapter.get_deployment_dir()
        instructions_file = deployment_dir / adapter.get_instructions_filename()

        if not deployment_dir.exists():
            print(f"   ❌ Deployment directory not created: {deployment_dir}")
            return 1

        if not instructions_file.exists():
            print(f"   ❌ Instructions file not created: {instructions_file}")
            return 1

        print(f"   ✅ Deployment directory: {deployment_dir}")
        print(f"   ✅ Instructions file: {instructions_file}")

        # Check agents
        agents_dir = deployment_dir / adapter.get_agents_dirname()
        if agents_dir.exists():
            agent_files = list(agents_dir.glob("*.md"))
            print(f"   ✅ Agent files generated: {len(agent_files)}")
            for agent_file in agent_files:
                print(f"      - {agent_file.name}")

        # Check workflows
        workflows_dir = deployment_dir / adapter.get_workflows_dirname()
        if workflows_dir.exists():
            workflow_files = list(workflows_dir.glob("*.md"))
            print(f"   ✅ Workflow files generated: {len(workflow_files)}")
            for workflow_file in workflow_files:
                print(f"      - {workflow_file.name}")

        # Show instructions file preview
        print("\n6. Instructions file preview (first 20 lines):")
        print("-" * 60)
        lines = instructions_file.read_text().split('\n')
        for line in lines[:20]:
            print(line)
        if len(lines) > 20:
            print(f"\n   ... ({len(lines) - 20} more lines)")
        print("-" * 60)

        print("\n" + "=" * 60)
        print("✅ Claude adapter test PASSED!")
        print(f"\nDeployment location: {deployment_dir}")
        print("\nYou can now use this deployment with Claude Code.")
        return 0

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
