#!/usr/bin/env python3
"""
Wrapper script to run the Vibey MCP server.

This script handles path setup so the server can be run from any directory.
IMPORTANT: Import mcp BEFORE adding vibey to path to avoid module shadowing.
"""

import os
import sys

# CRITICAL: Import mcp module BEFORE adding vibey to path
# This avoids our framework/mcp/server.py shadowing mcp.server
import mcp  # noqa: F401

# Add the vibey repo root to Python path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

# Change to repo root so relative paths work
os.chdir(REPO_ROOT)

# Now import and run the server
from framework.mcp.server import main

if __name__ == "__main__":
    main()
