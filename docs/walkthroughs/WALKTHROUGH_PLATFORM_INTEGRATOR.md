# Platform Integrator Walkthrough: Building with Vibey MCP

> **Time Required:** 45 minutes
> **Difficulty:** Advanced
> **Prerequisites:** Understanding of MCP protocol, Python or JS/TS

## Overview

This walkthrough guides you through integrating Vibey's MCP server into your platform or AI assistant. You'll learn how to connect to the server, use tools programmatically, and build custom integrations.

### What You'll Learn

- How to connect to Vibey's MCP server
- How to call MCP tools programmatically
- How to use resources and prompts
- How to build custom integrations

### What You'll Build

A working MCP integration that can query and manage roadmaps.

---

## Prerequisites

### Required

- [ ] Vibey installed and initialized
- [ ] Understanding of MCP protocol basics
- [ ] Python 3.9+ or Node.js 18+
- [ ] An MCP-compatible AI client (or ability to make HTTP/stdio calls)

### Recommended

- [ ] Familiarity with JSON-RPC 2.0
- [ ] Experience with async programming

### Verify Prerequisites

```bash
# Verify Vibey installation
vibey --version
# Expected: Vibey Agent Framework vX.Y.Z

# Verify MCP server exists
ls -la vibey/mcp/
# Should show server.py and related files
```

---

## Step 1: Understand MCP Architecture

### Goal

Understand how Vibey's MCP server is structured.

### Instructions

1. Review MCP components:

   ```
   Vibey MCP Server Structure:
   ├── Tools (76 total)      - Actions to perform
   │   ├── Task Tools        - Start, complete, query tasks
   │   ├── Sprint Tools      - Manage sprints
   │   ├── Query Tools       - Read roadmap state
   │   └── Content Tools     - Manage context files
   │
   ├── Resources (8 total)   - Data to read
   │   ├── vibey://workflows/{id}
   │   └── vibey://handoffs/{id}
   │
   └── Prompts (4 total)     - Pre-built prompts
       ├── quality_gate_check
       ├── security_scan
       ├── test_coverage
       └── doc_check
   ```

2. Introspect available tools:

   ```bash
   vibey docs introspect-mcp --format json | head -100
   ```

   **Expected Output:**
   ```json
   {
     "tools": [
       {
         "name": "vibey_start_task",
         "description": "Start working on a task",
         "parameters": {
           "type": "object",
           "properties": {
             "task_id": {"type": "string", "description": "Task identifier"}
           },
           "required": ["task_id"]
         }
       },
       ...
     ]
   }
   ```

3. Review the full reference:

   ```bash
   cat docs/reference/MCP_REFERENCE.md | head -200
   ```

### Checkpoint

> **Verify:** You understand tools, resources, and prompts structure

---

## Step 2: Start the MCP Server

### Goal

Run the Vibey MCP server for integration.

### Instructions

1. Start in stdio mode (for local integration):

   ```bash
   python -m vibey.mcp.server
   ```

   The server communicates over stdin/stdout using JSON-RPC 2.0.

2. For HTTP mode (if available):

   ```bash
   python -m vibey.mcp.server --mode http --port 8080
   ```

3. Test with a simple request (in another terminal):

   ```bash
   # Send initialize request
   echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | python -m vibey.mcp.server
   ```

   **Expected Output:**
   ```json
   {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{},"resources":{},"prompts":{}},"serverInfo":{"name":"vibey","version":"X.Y.Z"}}}
   ```
   *(Version field will reflect installed version)*

### Checkpoint

> **Verify:** Server starts and responds to initialize request

---

## Step 3: List Available Tools

### Goal

Discover all available MCP tools.

### Instructions

1. Send tools/list request:

   ```bash
   echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | python -m vibey.mcp.server
   ```

   **Expected Output:**
   ```json
   {
     "jsonrpc": "2.0",
     "id": 2,
     "result": {
       "tools": [
         {
           "name": "vibey_start_task",
           "description": "Start working on a task by ID",
           "inputSchema": {
             "type": "object",
             "properties": {
               "task_id": {"type": "string"}
             },
             "required": ["task_id"]
           }
         },
         ...
       ]
     }
   }
   ```

2. Filter for specific tool categories:

   ```bash
   vibey docs introspect-mcp --format json | jq '.tools[] | select(.name | contains("task"))'
   ```

### Checkpoint

> **Verify:** You can see the list of 76+ available tools

---

## Step 4: Call a Tool

### Goal

Execute MCP tools programmatically.

### Instructions

1. Call `vibey_roadmap_status`:

   ```bash
   echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"vibey_roadmap_status","arguments":{}}}' | python -m vibey.mcp.server
   ```

   **Expected Output:**
   ```json
   {
     "jsonrpc": "2.0",
     "id": 3,
     "result": {
       "content": [
         {
           "type": "text",
           "text": "Vibey Roadmap Status\n====================\nTracks: 5\nSprints: 23\nTasks: 89\n..."
         }
       ]
     }
   }
   ```

2. Call `vibey_query_task` with parameters:

   ```bash
   echo '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"vibey_query_task","arguments":{"task_id":"01KC..."}}}' | python -m vibey.mcp.server
   ```

3. Call `vibey_list_blockers`:

   ```bash
   echo '{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"vibey_list_blockers","arguments":{}}}' | python -m vibey.mcp.server
   ```

### Checkpoint

> **Verify:** Tools return expected results

---

## Step 5: Access Resources

### Goal

Read data from MCP resources.

### Instructions

1. List available resources:

   ```bash
   echo '{"jsonrpc":"2.0","id":6,"method":"resources/list","params":{}}' | python -m vibey.mcp.server
   ```

   **Expected Output:**
   ```json
   {
     "jsonrpc": "2.0",
     "id": 6,
     "result": {
       "resources": [
         {
           "uri": "vibey://workflows/{id}",
           "name": "Workflow",
           "description": "Access workflow definitions"
         },
         ...
       ]
     }
   }
   ```

2. Read a specific resource:

   ```bash
   echo '{"jsonrpc":"2.0","id":7,"method":"resources/read","params":{"uri":"vibey://workflows/sprint-planning"}}' | python -m vibey.mcp.server
   ```

   **Expected Output:**
   ```json
   {
     "jsonrpc": "2.0",
     "id": 7,
     "result": {
       "contents": [
         {
           "uri": "vibey://workflows/sprint-planning",
           "mimeType": "text/markdown",
           "text": "# Sprint Planning Workflow\n..."
         }
       ]
     }
   }
   ```

### Checkpoint

> **Verify:** Resources return workflow and handoff content

---

## Step 6: Use Prompts

### Goal

Leverage pre-built prompts for common tasks.

### Instructions

1. List available prompts:

   ```bash
   echo '{"jsonrpc":"2.0","id":8,"method":"prompts/list","params":{}}' | python -m vibey.mcp.server
   ```

   **Expected Output:**
   ```json
   {
     "jsonrpc": "2.0",
     "id": 8,
     "result": {
       "prompts": [
         {
           "name": "vibey_quality_gate_check",
           "description": "Run quality gate checks on code",
           "arguments": [
             {"name": "path", "description": "Path to check", "required": true}
           ]
         },
         ...
       ]
     }
   }
   ```

2. Get a prompt:

   ```bash
   echo '{"jsonrpc":"2.0","id":9,"method":"prompts/get","params":{"name":"vibey_quality_gate_check","arguments":{"path":"src/"}}}' | python -m vibey.mcp.server
   ```

   **Expected Output:**
   ```json
   {
     "jsonrpc": "2.0",
     "id": 9,
     "result": {
       "description": "Quality gate check for src/",
       "messages": [
         {
           "role": "user",
           "content": {"type": "text", "text": "Please run quality gate checks on src/..."}
         }
       ]
     }
   }
   ```

### Checkpoint

> **Verify:** Prompts return structured messages for AI assistants

---

## Step 7: Build a Python Client

### Goal

Create a reusable Python client for Vibey MCP.

### Instructions

1. Create `vibey_mcp_client.py`:

   ```python
   """Vibey MCP Client - Programmatic access to Vibey MCP server."""
   import json
   import subprocess
   from typing import Any, Dict, Optional

   class VibeyMCPClient:
       """Client for interacting with Vibey MCP server."""

       def __init__(self):
           self._id = 0
           self._process = None

       def _next_id(self) -> int:
           self._id += 1
           return self._id

       def _send_request(self, method: str, params: Optional[Dict] = None) -> Dict:
           """Send a JSON-RPC request and return the response."""
           request = {
               "jsonrpc": "2.0",
               "id": self._next_id(),
               "method": method,
               "params": params or {}
           }

           # Start server process
           proc = subprocess.Popen(
               ["python", "-m", "vibey.mcp.server"],
               stdin=subprocess.PIPE,
               stdout=subprocess.PIPE,
               stderr=subprocess.PIPE,
               text=True
           )

           # Send request
           stdout, stderr = proc.communicate(json.dumps(request))

           # Parse response
           return json.loads(stdout)

       def initialize(self) -> Dict:
           """Initialize the MCP connection."""
           return self._send_request("initialize", {
               "protocolVersion": "2024-11-05",
               "capabilities": {},
               "clientInfo": {"name": "python-client", "version": "1.0"}
           })

       def list_tools(self) -> list:
           """Get list of available tools."""
           response = self._send_request("tools/list")
           return response.get("result", {}).get("tools", [])

       def call_tool(self, name: str, arguments: Optional[Dict] = None) -> Any:
           """Call an MCP tool."""
           response = self._send_request("tools/call", {
               "name": name,
               "arguments": arguments or {}
           })
           return response.get("result", {})

       def roadmap_status(self) -> str:
           """Get roadmap status."""
           result = self.call_tool("vibey_roadmap_status")
           content = result.get("content", [])
           if content:
               return content[0].get("text", "")
           return ""

       def query_task(self, task_id: str) -> Dict:
           """Query a specific task."""
           return self.call_tool("vibey_query_task", {"task_id": task_id})

       def start_task(self, task_id: str) -> Dict:
           """Start working on a task."""
           return self.call_tool("vibey_start_task", {"task_id": task_id})

       def complete_task(self, task_id: str) -> Dict:
           """Complete a task."""
           return self.call_tool("vibey_complete_task", {"task_id": task_id})

       def list_blockers(self) -> Dict:
           """Get all blocked items."""
           return self.call_tool("vibey_list_blockers")


   # Example usage
   if __name__ == "__main__":
       client = VibeyMCPClient()

       # Initialize
       init_response = client.initialize()
       print(f"Initialized: {init_response}")

       # Get status
       status = client.roadmap_status()
       print(f"\nRoadmap Status:\n{status}")

       # List tools
       tools = client.list_tools()
       print(f"\nAvailable tools: {len(tools)}")
       for tool in tools[:5]:
           print(f"  - {tool['name']}")
   ```

2. Run the client:

   ```bash
   python vibey_mcp_client.py
   ```

   **Expected Output:**
   ```
   Initialized: {'jsonrpc': '2.0', 'id': 1, 'result': {...}}

   Roadmap Status:
   Vibey Roadmap Status
   ====================
   Tracks: 5
   ...

   Available tools: 76
     - vibey_start_task
     - vibey_complete_task
     - vibey_query_task
     - vibey_query_sprint
     - vibey_roadmap_status
   ```

### Checkpoint

> **Verify:** Python client successfully communicates with MCP server

---

## Step 8: Build an Integration

### Goal

Create a practical integration using the client.

### Instructions

1. Create `roadmap_dashboard.py`:

   ```python
   """Simple roadmap dashboard using Vibey MCP."""
   from vibey_mcp_client import VibeyMCPClient

   def print_dashboard():
       """Display a roadmap dashboard."""
       client = VibeyMCPClient()
       client.initialize()

       print("=" * 60)
       print("VIBEY ROADMAP DASHBOARD")
       print("=" * 60)

       # Get overall status
       status = client.roadmap_status()
       print("\n📊 STATUS")
       print("-" * 40)
       print(status)

       # Get blockers
       blockers = client.list_blockers()
       content = blockers.get("content", [])
       if content:
           print("\n🚧 BLOCKERS")
           print("-" * 40)
           print(content[0].get("text", "No blockers"))

       print("\n" + "=" * 60)

   if __name__ == "__main__":
       print_dashboard()
   ```

2. Run the dashboard:

   ```bash
   python roadmap_dashboard.py
   ```

### Checkpoint

> **Verify:** Dashboard displays live roadmap data

---

## Step 9: Handle Errors

### Goal

Implement robust error handling for MCP calls.

### Instructions

1. Update your client with error handling:

   ```python
   class VibeyMCPError(Exception):
       """Error from Vibey MCP server."""
       def __init__(self, code: int, message: str, data: Any = None):
           self.code = code
           self.message = message
           self.data = data
           super().__init__(f"MCP Error {code}: {message}")

   class VibeyMCPClient:
       # ... existing code ...

       def _send_request(self, method: str, params: Optional[Dict] = None) -> Dict:
           """Send a JSON-RPC request and return the response."""
           request = {
               "jsonrpc": "2.0",
               "id": self._next_id(),
               "method": method,
               "params": params or {}
           }

           try:
               proc = subprocess.Popen(
                   ["python", "-m", "vibey.mcp.server"],
                   stdin=subprocess.PIPE,
                   stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE,
                   text=True
               )

               stdout, stderr = proc.communicate(json.dumps(request), timeout=30)

               if proc.returncode != 0:
                   raise VibeyMCPError(-1, f"Server error: {stderr}")

               response = json.loads(stdout)

               if "error" in response:
                   error = response["error"]
                   raise VibeyMCPError(
                       error.get("code", -1),
                       error.get("message", "Unknown error"),
                       error.get("data")
                   )

               return response

           except subprocess.TimeoutExpired:
               raise VibeyMCPError(-2, "Request timed out")
           except json.JSONDecodeError as e:
               raise VibeyMCPError(-3, f"Invalid JSON response: {e}")
   ```

2. Use with try/except:

   ```python
   try:
       result = client.query_task("invalid-id")
   except VibeyMCPError as e:
       print(f"Error: {e.message} (code: {e.code})")
   ```

### Checkpoint

> **Verify:** Errors are caught and handled gracefully

---

## Summary

### What You Accomplished

- Started and communicated with Vibey MCP server
- Listed and called MCP tools
- Accessed resources and prompts
- Built a Python client for MCP integration
- Created a practical dashboard integration
- Implemented error handling

### Commands Used

| Command | Purpose |
|---------|---------|
| `python -m vibey.mcp.server` | Start MCP server |
| `vibey docs introspect-mcp` | Introspect server structure |
| JSON-RPC requests | Communicate with server |

### MCP Methods Reference

| Method | Purpose |
|--------|---------|
| `initialize` | Start MCP session |
| `tools/list` | List available tools |
| `tools/call` | Execute a tool |
| `resources/list` | List resources |
| `resources/read` | Read a resource |
| `prompts/list` | List prompts |
| `prompts/get` | Get a prompt |

### Next Steps

1. **Full Reference:** [MCP Reference](../reference/MCP_REFERENCE.md) - All 76 tools documented
2. **Build Adapter:** Create an adapter for your AI platform
3. **Contribute:** Add new tools to the MCP server
4. **Join Community:** Share your integration

---

## Quick Reference

### MCP Request Format

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "METHOD_NAME",
  "params": {}
}
```

### Common Tools

```bash
# Get roadmap status
{"method":"tools/call","params":{"name":"vibey_roadmap_status","arguments":{}}}

# Query a task
{"method":"tools/call","params":{"name":"vibey_query_task","arguments":{"task_id":"01KC..."}}}

# Start a task
{"method":"tools/call","params":{"name":"vibey_start_task","arguments":{"task_id":"01KC..."}}}

# List blockers
{"method":"tools/call","params":{"name":"vibey_list_blockers","arguments":{}}}
```

### Related Documentation

- [MCP Reference](../reference/MCP_REFERENCE.md)
- [CLI Reference](../reference/CLI_REFERENCE.md)
- [Platform Integrator Journey](../journeys/JOURNEY_PLATFORM_INTEGRATOR.md)
- [User Personas](../personas/USER_PERSONAS.md#sam)
