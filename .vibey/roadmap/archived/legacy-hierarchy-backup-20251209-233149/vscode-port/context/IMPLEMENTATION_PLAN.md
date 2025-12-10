# VS Code Native MCP Port - Implementation Plan

**Track ID:** `vscode-port`
**Status:** Not Started
**Priority:** Medium
**Estimated Duration:** 3-4 weeks (2 sprints)
**Compatibility Score:** 85%

---

## Executive Summary

VS Code has native MCP (Model Context Protocol) support as of version 1.102 (July 2025). This enables direct integration with the existing Vibey MCP server without requiring additional AI assistant extensions. The VS Code port leverages the existing `framework/mcp/server.py` (46+ tools) as the backend, with a thin VS Code extension wrapper for configuration and UI integration.

**Key Advantages:**
- **Direct MCP Reuse:** Existing server.py works unmodified
- **Native VS Code Support:** Full MCP specification implemented
- **75% Developer Market Share:** VS Code is the dominant IDE
- **Marketplace Distribution:** Standard extension publishing

---

## Research Findings

### VS Code MCP Support (Generally Available - July 2025)

**Sources:**
- [VS Code MCP Developer Guide](https://code.visualstudio.com/api/extension-guides/ai/mcp)
- [Full MCP Spec Support Blog](https://code.visualstudio.com/blogs/2025/06/12/full-mcp-spec-support)
- [MCP Servers in VS Code](https://code.visualstudio.com/docs/copilot/chat/mcp-servers)
- [GitHub Changelog - GA Announcement](https://github.blog/changelog/2025-07-14-model-context-protocol-mcp-support-in-vs-code-is-generally-available/)

**Key Capabilities:**
1. **Full MCP Specification:** Tools, prompts, resources, authorization, sampling
2. **Transport Options:** Stdio (local process) and Streamable HTTP (remote)
3. **Extension API:** `vscode.lm.registerMcpServerDefinitionProvider()`
4. **Configuration:** `.vscode/mcp.json` for workspace-scoped servers
5. **OAuth Support:** Authorization spec for enterprise scenarios

### VS Code Extension API for MCP

**Registration Method:**
```typescript
vscode.lm.registerMcpServerDefinitionProvider(providerId, {
  onDidChangeMcpServerDefinitions: event,
  provideMcpServerDefinitions: () => McpServerDefinition[],
  resolveMcpServerDefinition: (definition) => resolvedDefinition
});
```

**Server Definition Types:**
- `vscode.McpStdioServerDefinition` - Local process via stdin/stdout
- `vscode.McpHttpServerDefinition` - Remote HTTP transport

**package.json Contribution:**
```json
{
  "contributes": {
    "mcpServerDefinitionProviders": [
      {
        "id": "vibey-mcp",
        "label": "Vibey Agent Framework"
      }
    ]
  }
}
```

### Configuration System

**.vscode/mcp.json format:**
```json
{
  "servers": {
    "vibey": {
      "command": "python",
      "args": ["-m", "framework.mcp.server"],
      "env": {
        "VIBEY_PROJECT_ROOT": "${workspaceFolder}"
      }
    }
  }
}
```

### Marketplace Requirements

- **Publisher Account:** Azure DevOps authentication
- **Unique Extension ID:** Required for marketplace
- **Personal Access Token:** For vsce CLI publishing
- **License Required:** MIT recommended
- **CLI Tool:** `npm install -g @vscode/vsce`

---

## Critical Architecture: Zero-Drift Design

> **All VS Code configuration files are GENERATED from Vibey source of truth.**

### Source of Truth Hierarchy

```
SOURCE OF TRUTH (edit these)              GENERATED OUTPUT (never edit)
----------------------------              ----------------------------
framework/agents/*.md            --->     VS Code MCP tools (via server.py)
framework/workflows/*.md         --->     VS Code MCP tools (via server.py)
.vibey/config/*.yaml             --->     .vscode/mcp.json (server config)
templates/vscode/*.j2            --->     VS Code extension settings
```

### Why This Architecture Works

1. **MCP Server is Already Built:** `framework/mcp/server.py` with 46+ tools
2. **Dynamic Tool Discovery:** `framework/mcp/discovery/` parses YAML frontmatter
3. **No Duplication:** VS Code calls existing MCP server directly
4. **Single Update Point:** Change agent/workflow, regenerate config, done

### Extension is Just a Connector

The VS Code extension's only job:
1. Register Vibey MCP server definition with VS Code
2. Auto-discover `.vibey/` directory in workspace
3. Provide settings UI for server configuration
4. Generate `.vscode/mcp.json` from `.vibey/config/`

---

## MCP Server Reuse Strategy

### Existing Infrastructure (No Changes Needed)

| Component | Location | Purpose |
|-----------|----------|---------|
| MCP Server | `framework/mcp/server.py` | 46+ tools, stdio transport |
| Tool Discovery | `framework/mcp/discovery/` | Dynamic frontmatter parsing |
| Agent Discovery | `framework/mcp/discovery/agents.py` | Agent -> MCP tool conversion |
| Workflow Discovery | `framework/mcp/discovery/workflows.py` | Workflow -> MCP tool conversion |
| Tool Generator | `framework/mcp/discovery/generator.py` | JSON Schema generation |
| Task Tools | `framework/mcp/tools/task_tools.py` | Roadmap task management |
| Sprint Tools | `framework/mcp/tools/sprint_tools.py` | Sprint lifecycle |
| Query Tools | `framework/mcp/tools/query_tools.py` | Roadmap queries |

### How VS Code Connects

```
VS Code                      Vibey MCP Server
--------                     ----------------
|      |  stdio (stdin/out)  |               |
| Chat | <----------------> | server.py     |
|      |                     | (46+ tools)   |
--------                     ----------------
                                   |
                                   v
                            framework/agents/*.md
                            framework/workflows/*.md
                            .vibey/roadmap/
```

### Server Launch Configuration

VS Code will spawn the MCP server as a child process:

```json
{
  "servers": {
    "vibey": {
      "command": "python",
      "args": ["-m", "framework.mcp.server", "--roadmap-root", ".vibey/roadmap"],
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}",
        "VIBEY_DEBUG": "false"
      }
    }
  }
}
```

---

## VS Code Extension Design

### Extension Architecture

```
vscode-vibey/
|-- package.json               # Extension manifest + MCP contribution
|-- src/
|   |-- extension.ts           # Main activation, server registration
|   |-- mcpProvider.ts         # McpServerDefinitionProvider implementation
|   |-- configGenerator.ts     # Generate .vscode/mcp.json from .vibey/
|   |-- settings.ts            # VS Code settings integration
|   |-- statusBar.ts           # Status bar item
|   |-- outputChannel.ts       # Vibey output panel
|   `-- utils/
|       |-- vibeyDetector.ts   # Detect .vibey/ directory
|       `-- configLoader.ts    # Load Vibey config
|-- templates/
|   |-- mcp.json.j2            # Template for .vscode/mcp.json
|   `-- settings.json.j2       # VS Code settings template
|-- test/
|   |-- extension.test.ts
|   `-- mcpProvider.test.ts
|-- .vscodeignore
|-- tsconfig.json
|-- LICENSE
`-- README.md
```

### package.json Contribution Points

```json
{
  "name": "vscode-vibey",
  "displayName": "Vibey Agent Framework",
  "description": "MCP integration for Vibey - intelligent agent orchestration for AI coding assistants",
  "version": "1.0.0",
  "publisher": "vibey-framework",
  "engines": {
    "vscode": "^1.102.0"
  },
  "categories": ["AI", "Machine Learning", "Programming Languages"],
  "activationEvents": [
    "workspaceContains:.vibey",
    "onCommand:vibey.initialize"
  ],
  "contributes": {
    "mcpServerDefinitionProviders": [
      {
        "id": "vibey-mcp",
        "label": "Vibey Agent Framework"
      }
    ],
    "commands": [
      {
        "command": "vibey.initialize",
        "title": "Initialize Vibey Framework",
        "category": "Vibey"
      },
      {
        "command": "vibey.refreshTools",
        "title": "Refresh MCP Tools",
        "category": "Vibey"
      },
      {
        "command": "vibey.showStatus",
        "title": "Show Roadmap Status",
        "category": "Vibey"
      },
      {
        "command": "vibey.generateConfig",
        "title": "Generate MCP Configuration",
        "category": "Vibey"
      }
    ],
    "configuration": {
      "title": "Vibey",
      "properties": {
        "vibey.serverPath": {
          "type": "string",
          "default": "",
          "description": "Path to Vibey MCP server (auto-detected if empty)"
        },
        "vibey.pythonPath": {
          "type": "string",
          "default": "python",
          "description": "Python interpreter to use for MCP server"
        },
        "vibey.autoStart": {
          "type": "boolean",
          "default": true,
          "description": "Automatically start MCP server when workspace opens"
        },
        "vibey.showStatusBar": {
          "type": "boolean",
          "default": true,
          "description": "Show Vibey status in the status bar"
        }
      }
    },
    "menus": {
      "commandPalette": [
        {
          "command": "vibey.initialize",
          "when": "workspaceFolderCount > 0"
        }
      ]
    }
  },
  "main": "./dist/extension.js",
  "scripts": {
    "vscode:prepublish": "npm run compile",
    "compile": "tsc -p ./",
    "watch": "tsc -watch -p ./",
    "test": "npm run compile && node ./out/test/runTest.js"
  },
  "devDependencies": {
    "@types/vscode": "^1.102.0",
    "@types/node": "^20.x",
    "typescript": "^5.x"
  }
}
```

### MCP Provider Implementation

```typescript
// src/mcpProvider.ts
import * as vscode from 'vscode';
import { VibeyDetector } from './utils/vibeyDetector';

export class VibeyMcpProvider implements vscode.McpServerDefinitionProvider {
    private _onDidChangeServers = new vscode.EventEmitter<void>();
    readonly onDidChangeMcpServerDefinitions = this._onDidChangeServers.event;

    private vibeyDetector: VibeyDetector;

    constructor() {
        this.vibeyDetector = new VibeyDetector();
    }

    async provideMcpServerDefinitions(
        token: vscode.CancellationToken
    ): Promise<vscode.McpServerDefinition[]> {
        const servers: vscode.McpServerDefinition[] = [];

        // Find workspaces with .vibey/
        for (const folder of vscode.workspace.workspaceFolders || []) {
            if (await this.vibeyDetector.hasVibeyFramework(folder.uri)) {
                const config = vscode.workspace.getConfiguration('vibey');
                const pythonPath = config.get<string>('pythonPath', 'python');

                servers.push(
                    new vscode.McpStdioServerDefinition(
                        `vibey-${folder.name}`,  // Label
                        pythonPath,               // Command
                        [
                            '-m',
                            'framework.mcp.server',
                            '--roadmap-root',
                            '.vibey/roadmap'
                        ],
                        {
                            cwd: folder.uri.fsPath,
                            env: {
                                PYTHONPATH: folder.uri.fsPath
                            }
                        }
                    )
                );
            }
        }

        return servers;
    }

    async resolveMcpServerDefinition(
        definition: vscode.McpServerDefinition,
        token: vscode.CancellationToken
    ): Promise<vscode.McpServerDefinition | undefined> {
        // Optional: perform additional setup (auth, user prompts)
        return definition;
    }

    refresh(): void {
        this._onDidChangeServers.fire();
    }

    dispose(): void {
        this._onDidChangeServers.dispose();
    }
}
```

### Extension Activation

```typescript
// src/extension.ts
import * as vscode from 'vscode';
import { VibeyMcpProvider } from './mcpProvider';
import { VibeyStatusBar } from './statusBar';
import { ConfigGenerator } from './configGenerator';

let mcpProvider: VibeyMcpProvider;
let statusBar: VibeyStatusBar;

export async function activate(context: vscode.ExtensionContext) {
    console.log('Vibey Agent Framework extension activated');

    // Register MCP server provider
    mcpProvider = new VibeyMcpProvider();
    const registration = vscode.lm.registerMcpServerDefinitionProvider(
        'vibey-mcp',
        mcpProvider
    );
    context.subscriptions.push(registration);

    // Status bar
    statusBar = new VibeyStatusBar();
    context.subscriptions.push(statusBar);

    // Commands
    context.subscriptions.push(
        vscode.commands.registerCommand('vibey.initialize', async () => {
            await ConfigGenerator.initialize();
        }),
        vscode.commands.registerCommand('vibey.refreshTools', () => {
            mcpProvider.refresh();
            vscode.window.showInformationMessage('Vibey MCP tools refreshed');
        }),
        vscode.commands.registerCommand('vibey.showStatus', async () => {
            // Show roadmap status via MCP tool call
            vscode.window.showInformationMessage('Querying roadmap status...');
        }),
        vscode.commands.registerCommand('vibey.generateConfig', async () => {
            await ConfigGenerator.generateMcpJson();
        })
    );

    // Watch for .vibey/ changes
    const watcher = vscode.workspace.createFileSystemWatcher(
        '**/.vibey/**/*.{yaml,md}'
    );
    watcher.onDidChange(() => mcpProvider.refresh());
    watcher.onDidCreate(() => mcpProvider.refresh());
    watcher.onDidDelete(() => mcpProvider.refresh());
    context.subscriptions.push(watcher);
}

export function deactivate() {
    // Cleanup
}
```

---

## Config Generation (Zero-Drift)

### Generate .vscode/mcp.json from .vibey/

```typescript
// src/configGenerator.ts
import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'yaml';

export class ConfigGenerator {
    static async generateMcpJson(): Promise<void> {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            vscode.window.showErrorMessage('No workspace folder open');
            return;
        }

        const vibeyConfigPath = path.join(
            workspaceFolder.uri.fsPath,
            '.vibey',
            'config',
            'framework.yaml'
        );

        if (!fs.existsSync(vibeyConfigPath)) {
            vscode.window.showWarningMessage(
                'Vibey framework not found. Run "vibey init" first.'
            );
            return;
        }

        // Read Vibey config
        const vibeyConfig = yaml.parse(
            fs.readFileSync(vibeyConfigPath, 'utf8')
        );

        // Generate mcp.json
        const mcpConfig = {
            // Generated header
            _comment: [
                "AUTO-GENERATED by Vibey Agent Framework",
                "DO NOT EDIT - regenerate with: vibey deploy --platform vscode",
                `Generated: ${new Date().toISOString()}`
            ],
            servers: {
                vibey: {
                    command: vscode.workspace.getConfiguration('vibey')
                        .get<string>('pythonPath', 'python'),
                    args: [
                        '-m',
                        'framework.mcp.server',
                        '--roadmap-root',
                        '.vibey/roadmap'
                    ],
                    env: {
                        PYTHONPATH: '${workspaceFolder}'
                    }
                }
            }
        };

        // Ensure .vscode directory exists
        const vscodeDir = path.join(workspaceFolder.uri.fsPath, '.vscode');
        if (!fs.existsSync(vscodeDir)) {
            fs.mkdirSync(vscodeDir, { recursive: true });
        }

        // Write mcp.json
        const mcpJsonPath = path.join(vscodeDir, 'mcp.json');
        fs.writeFileSync(
            mcpJsonPath,
            JSON.stringify(mcpConfig, null, 2)
        );

        vscode.window.showInformationMessage(
            `Generated ${mcpJsonPath}`
        );
    }

    static async initialize(): Promise<void> {
        // Initialize Vibey in workspace if not present
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) return;

        const vibeyDir = path.join(workspaceFolder.uri.fsPath, '.vibey');
        if (fs.existsSync(vibeyDir)) {
            await this.generateMcpJson();
            return;
        }

        // Prompt to run vibey init
        const choice = await vscode.window.showInformationMessage(
            'Vibey framework not found. Initialize now?',
            'Initialize',
            'Cancel'
        );

        if (choice === 'Initialize') {
            const terminal = vscode.window.createTerminal('Vibey');
            terminal.sendText('vibey init');
            terminal.show();
        }
    }
}
```

---

## Vibey Adapter Implementation

### VSCodeAdapter Class

```python
# vibey/adapters/vscode.py
"""
VS Code platform adapter.

This adapter deploys Vibey to VS Code's .vscode/ directory format.
"""

from pathlib import Path
from typing import Optional, List, Any
import json
import shutil
from datetime import datetime

from vibey.adapters.base import PlatformAdapter, DeploymentResult


class VSCodeAdapter(PlatformAdapter):
    """
    Adapter for VS Code MCP integration.

    Deploys Vibey framework to .vscode/ directory with:
    - mcp.json (MCP server configuration)
    - settings.json (VS Code settings)

    The VS Code extension handles server registration.
    """

    def get_platform_name(self) -> str:
        return "vscode"

    def get_deployment_dir(self, project_root: Optional[Path] = None) -> Path:
        if project_root is None:
            project_root = Path.cwd()
        return project_root / ".vscode"

    def deploy(
        self,
        source_dir: Path,
        config: Any,
        target_dir: Optional[Path] = None,
        clean: bool = False
    ) -> DeploymentResult:
        """
        Deploy to VS Code.

        Steps:
        1. Create .vscode/ directory
        2. Generate mcp.json with Vibey server config
        3. Merge into settings.json if needed
        4. Validate deployment
        """
        start_time = datetime.now()

        if target_dir is None:
            target_dir = self.get_deployment_dir(source_dir.parent)

        result = DeploymentResult(
            success=False,
            platform=self.get_platform_name(),
            target_dir=target_dir,
        )

        try:
            self.pre_deploy_hook(source_dir, target_dir)

            # Create directory
            target_dir.mkdir(parents=True, exist_ok=True)

            # Generate mcp.json
            mcp_json_path = target_dir / "mcp.json"
            self._generate_mcp_json(config, mcp_json_path)
            result.files_created.append(mcp_json_path)

            # Validate
            is_valid, errors = self.validate_deployment(target_dir)
            result.validation_passed = is_valid
            result.errors.extend(errors)

            result.success = len(result.errors) == 0
            self.post_deploy_hook(result)

        except Exception as e:
            result.success = False
            result.errors.append(f"Deployment failed: {e}")

        result.duration_seconds = (datetime.now() - start_time).total_seconds()
        return result

    def _generate_mcp_json(self, config: Any, output_path: Path) -> None:
        """Generate .vscode/mcp.json"""
        mcp_config = {
            "_comment": [
                "AUTO-GENERATED by Vibey Agent Framework",
                "DO NOT EDIT - regenerate with: vibey deploy --platform vscode",
                f"Generated: {datetime.now().isoformat()}"
            ],
            "servers": {
                "vibey": {
                    "command": "python",
                    "args": [
                        "-m",
                        "framework.mcp.server",
                        "--roadmap-root",
                        ".vibey/roadmap"
                    ],
                    "env": {
                        "PYTHONPATH": "${workspaceFolder}"
                    }
                }
            }
        }

        output_path.write_text(json.dumps(mcp_config, indent=2))

    def generate_context_file(self, config: Any, output_path: Path) -> None:
        """VS Code doesn't use a separate context file like CLAUDE.md"""
        pass

    def validate_deployment(self, deployment_dir: Path) -> tuple[bool, List[str]]:
        """Validate VS Code deployment."""
        errors = []

        if not deployment_dir.exists():
            errors.append(f"Deployment directory does not exist: {deployment_dir}")
            return (False, errors)

        mcp_json = deployment_dir / "mcp.json"
        if not mcp_json.exists():
            errors.append("Missing required file: mcp.json")
        else:
            try:
                content = json.loads(mcp_json.read_text())
                if "servers" not in content:
                    errors.append("mcp.json missing 'servers' key")
                if "vibey" not in content.get("servers", {}):
                    errors.append("mcp.json missing 'vibey' server definition")
            except json.JSONDecodeError as e:
                errors.append(f"mcp.json is not valid JSON: {e}")

        return (len(errors) == 0, errors)

    def get_required_files(self) -> List[str]:
        return ["mcp.json"]

    def supports_feature(self, feature: str) -> bool:
        """All features supported via MCP."""
        return True
```

---

## Sprint Plan

### Sprint 1: VS Code MCP Extension (2 weeks)

#### Task 1.1: Create VS Code Extension Scaffold (1-2 days)
**Files:**
- `vscode-vibey/package.json`
- `vscode-vibey/tsconfig.json`
- `vscode-vibey/.vscodeignore`
- `vscode-vibey/src/extension.ts`

**Acceptance Criteria:**
- Extension compiles without errors
- Loads in VS Code Extension Development Host
- Activates on workspace with `.vibey/`

#### Task 1.2: Implement MCP Server Provider (2-3 days)
**Files:**
- `vscode-vibey/src/mcpProvider.ts`
- `vscode-vibey/src/utils/vibeyDetector.ts`

**Acceptance Criteria:**
- `McpServerDefinitionProvider` implementation
- Auto-discovers workspaces with `.vibey/`
- Registers Vibey server with correct args

#### Task 1.3: Create VSCodeAdapter Class (1-2 days)
**Files:**
- `vibey/adapters/vscode.py`
- `templates/vscode/mcp.json.j2`

**Acceptance Criteria:**
- Extends `PlatformAdapter` base class
- Generates valid `.vscode/mcp.json`
- Validates deployment

#### Task 1.4: Config Generation Integration (1-2 days)
**Files:**
- `vscode-vibey/src/configGenerator.ts`
- `vscode-vibey/src/utils/configLoader.ts`

**Acceptance Criteria:**
- Reads `.vibey/config/*.yaml`
- Generates `.vscode/mcp.json`
- Includes generation timestamp

#### Task 1.5: Integration Testing (2-3 days)
**Files:**
- `vscode-vibey/test/extension.test.ts`
- `vscode-vibey/test/mcpProvider.test.ts`
- `tests/adapters/test_vscode.py`

**Acceptance Criteria:**
- Extension activates correctly
- MCP server starts and responds
- All 46+ tools discoverable
- Tool invocation works

#### Task 1.6: File System Watcher (1 day)
**Files:**
- `vscode-vibey/src/extension.ts` (update)

**Acceptance Criteria:**
- Watches `.vibey/**/*.{yaml,md}`
- Refreshes MCP tools on file change
- Triggers `onDidChangeMcpServerDefinitions`

---

### Sprint 2: Commands, UI, and Marketplace (1.5 weeks)

#### Task 2.1: Command Palette Integration (1-2 days)
**Files:**
- `vscode-vibey/src/commands/initialize.ts`
- `vscode-vibey/src/commands/refreshTools.ts`
- `vscode-vibey/src/commands/showStatus.ts`
- `vscode-vibey/src/commands/generateConfig.ts`

**Acceptance Criteria:**
- All commands visible in palette
- Commands execute correctly
- Error handling with user feedback

#### Task 2.2: Status Bar Integration (1 day)
**Files:**
- `vscode-vibey/src/statusBar.ts`

**Acceptance Criteria:**
- Shows Vibey status in status bar
- Click opens command palette
- Updates on server status change

#### Task 2.3: Output Panel (1 day)
**Files:**
- `vscode-vibey/src/outputChannel.ts`

**Acceptance Criteria:**
- Vibey output channel created
- Server logs visible
- Tool invocation logging

#### Task 2.4: Marketplace Preparation (1-2 days)
**Files:**
- `vscode-vibey/README.md`
- `vscode-vibey/CHANGELOG.md`
- `vscode-vibey/LICENSE`
- `vscode-vibey/images/` (icons, screenshots)

**Acceptance Criteria:**
- README with installation instructions
- Icon meets marketplace requirements
- Screenshots of extension in action
- License file (MIT)

#### Task 2.5: Documentation (1-2 days)
**Files:**
- `docs/guides/VSCODE_INTEGRATION.md`
- `docs/guides/VSCODE_MCP_SETUP.md`

**Acceptance Criteria:**
- Installation guide
- Configuration reference
- Troubleshooting guide
- Example usage

#### Task 2.6: Publish to Marketplace (1 day)
**Steps:**
1. Create publisher account
2. Generate Personal Access Token
3. Package extension with vsce
4. Publish to marketplace
5. Verify installation

---

## Quality Gates

### Gate 1: MCP Connection (100% threshold, blocking)
- VS Code connects to Vibey MCP server
- Server starts without errors
- stdio transport functional

### Gate 2: Tool Discovery (95% threshold, blocking)
- All 46+ tools discoverable
- Tool schemas correct
- Tool invocation works

### Gate 3: Config Generation (95% threshold, blocking)
- `.vscode/mcp.json` generated correctly
- Regeneration produces identical output
- Settings merge correctly

### Gate 4: Marketplace Ready (90% threshold, non-blocking)
- Extension passes vsce lint
- README complete
- Icons and screenshots ready
- Version numbering correct

---

## Risks and Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| VS Code MCP API changes | Medium | Pin to specific VS Code version, monitor release notes |
| Python path issues | Medium | Configurable python path, fallback detection |
| Extension activation timing | Low | Use `activationEvents` correctly, lazy loading |
| Marketplace rejection | Low | Follow all guidelines, test with vsce lint |
| Tool count limits | Low | Existing 46 tools well under any limits |

---

## Deliverables Checklist

### Core Implementation
- [ ] `vscode-vibey/package.json` - Extension manifest
- [ ] `vscode-vibey/src/extension.ts` - Main activation
- [ ] `vscode-vibey/src/mcpProvider.ts` - MCP provider
- [ ] `vscode-vibey/src/configGenerator.ts` - Config generation
- [ ] `vscode-vibey/src/statusBar.ts` - Status bar
- [ ] `vscode-vibey/src/outputChannel.ts` - Output panel
- [ ] `vibey/adapters/vscode.py` - VSCodeAdapter class
- [ ] `templates/vscode/mcp.json.j2` - Config template

### Testing
- [ ] `vscode-vibey/test/extension.test.ts` - Extension tests
- [ ] `vscode-vibey/test/mcpProvider.test.ts` - Provider tests
- [ ] `tests/adapters/test_vscode.py` - Adapter tests

### Documentation
- [ ] `docs/guides/VSCODE_INTEGRATION.md` - User guide
- [ ] `vscode-vibey/README.md` - Extension readme
- [ ] `vscode-vibey/CHANGELOG.md` - Change log

### Marketplace
- [ ] Publisher account created
- [ ] Extension icon (128x128, 256x256)
- [ ] Screenshots (3-5)
- [ ] Published to marketplace

---

## Success Criteria

1. **Functional Integration**
   - Extension installs from marketplace
   - MCP server starts on workspace open
   - All 46+ tools available in VS Code chat/agent mode

2. **Zero-Drift Architecture**
   - `vibey deploy --platform vscode` generates correct config
   - Modifying `framework/agents/*.md` and regenerating updates tools
   - Generated files contain regeneration instructions

3. **User Experience**
   - One-click initialization
   - Status bar shows server state
   - Output panel shows logs
   - Commands accessible from palette

4. **Documentation**
   - Complete installation guide
   - Configuration reference
   - Troubleshooting section

---

## References

- [VS Code MCP Developer Guide](https://code.visualstudio.com/api/extension-guides/ai/mcp)
- [VS Code MCP User Guide](https://code.visualstudio.com/docs/copilot/chat/mcp-servers)
- [VS Code Extension API](https://code.visualstudio.com/api)
- [VS Code Extension Publishing](https://code.visualstudio.com/api/working-with-extensions/publishing-extension)
- [Full MCP Spec Support Blog](https://code.visualstudio.com/blogs/2025/06/12/full-mcp-spec-support)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Vibey MCP Server](framework/mcp/server.py)

---

**Last Updated:** 2025-11-23
**Author:** Vibey Framework Team
**Architecture Review:** Zero-drift via MCP server reuse + config generation
