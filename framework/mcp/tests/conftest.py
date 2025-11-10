"""
Pytest configuration for MCP server tests.

Common fixtures and configuration for all test files.
"""

import sys
from pathlib import Path

# Add framework to Python path for imports
framework_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(framework_root))
