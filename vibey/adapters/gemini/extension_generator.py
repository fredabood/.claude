"""
Gemini Extension Generator.

Generates the Gemini extension manifest and settings files.
This packages GEMINI.md, commands, and MCP configuration into
an installable extension.

Gemini Extension Structure:
- gemini-extension.json - Extension manifest
- settings.json - MCP server configuration
- GEMINI.md - Context file
- commands/ - TOML command files
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ExtensionManifest:
    """Gemini extension manifest."""
    name: str
    version: str
    description: str
    author: str
    repository: Optional[str] = None
    license: str = "MIT"
    gemini_cli_version: str = ">=0.1.0"


@dataclass
class MCPServerConfig:
    """MCP server configuration for settings.json."""
    command: str
    args: List[str]
    env: Dict[str, str]
    trust: bool = False
    include_tools: Optional[List[str]] = None
    exclude_tools: Optional[List[str]] = None


class GeminiExtensionGenerator:
    """
    Generate Gemini extension package.

    Creates:
    - gemini-extension.json (manifest)
    - settings.json (MCP server config)
    - Installation script

    Example:
        >>> generator = GeminiExtensionGenerator()
        >>> generator.generate_manifest(output_dir)
        >>> generator.generate_settings(output_dir, mcp_server_path)
    """

    DEFAULT_MANIFEST = ExtensionManifest(
        name="vibey",
        version="1.0.0",
        description="Vibey Agent Framework - Intelligent workflow management for AI coding assistants",
        author="Vibey Framework Team",
        repository="https://github.com/vibey/vibey",
        license="MIT",
    )

    # Tools that should be excluded for safety
    EXCLUDED_TOOLS = [
        "vibey_dangerous_operation",  # Example - no actual dangerous tools
    ]

    def __init__(self, manifest: Optional[ExtensionManifest] = None):
        """
        Initialize extension generator.

        Args:
            manifest: Custom manifest or use default
        """
        self.manifest = manifest or self.DEFAULT_MANIFEST

    def generate_manifest(self, output_dir: Path) -> Path:
        """
        Generate gemini-extension.json manifest.

        Args:
            output_dir: Directory to write manifest

        Returns:
            Path to generated manifest file
        """
        manifest_data = {
            "name": self.manifest.name,
            "version": self.manifest.version,
            "description": self.manifest.description,
            "author": self.manifest.author,
            "license": self.manifest.license,
            "gemini_cli_version": self.manifest.gemini_cli_version,
            "components": {
                "context": "GEMINI.md",
                "commands": "commands/vibey/",
                "settings": "settings.json",
            },
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "generator": "vibey-export-gemini",
                "framework_version": "2.5.0",
            },
        }

        if self.manifest.repository:
            manifest_data["repository"] = self.manifest.repository

        output_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = output_dir / "gemini-extension.json"
        manifest_path.write_text(
            json.dumps(manifest_data, indent=2),
            encoding='utf-8'
        )

        logger.info(f"Generated extension manifest: {manifest_path}")
        return manifest_path

    def generate_settings(
        self,
        output_dir: Path,
        mcp_server_command: str = "python",
        mcp_server_args: Optional[List[str]] = None,
        mcp_server_env: Optional[Dict[str, str]] = None,
    ) -> Path:
        """
        Generate settings.json with MCP server configuration.

        Args:
            output_dir: Directory to write settings
            mcp_server_command: Command to run MCP server
            mcp_server_args: Arguments for MCP server
            mcp_server_env: Environment variables

        Returns:
            Path to generated settings file
        """
        if mcp_server_args is None:
            mcp_server_args = ["-m", "framework.mcp.server"]

        settings_data = {
            "mcpServers": {
                "vibey": {
                    "command": mcp_server_command,
                    "args": mcp_server_args,
                    "env": mcp_server_env or {},
                    "trust": False,  # User should explicitly trust
                }
            },
            "context": {
                "fileName": "GEMINI.md",
            },
        }

        # Add tool exclusions if any
        if self.EXCLUDED_TOOLS:
            settings_data["mcpServers"]["vibey"]["excludeTools"] = self.EXCLUDED_TOOLS

        output_dir.mkdir(parents=True, exist_ok=True)
        settings_path = output_dir / "settings.json"
        settings_path.write_text(
            json.dumps(settings_data, indent=2),
            encoding='utf-8'
        )

        logger.info(f"Generated settings: {settings_path}")
        return settings_path

    def generate_install_script(self, output_dir: Path) -> Path:
        """
        Generate installation helper script.

        Args:
            output_dir: Directory to write script

        Returns:
            Path to generated script
        """
        script_content = '''#!/bin/bash
# Vibey Gemini Extension Installer
# Generated by vibey export gemini

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GEMINI_DIR="${HOME}/.gemini"
EXTENSIONS_DIR="${GEMINI_DIR}/extensions/vibey"

echo "Installing Vibey Gemini Extension..."

# Create directories
mkdir -p "${EXTENSIONS_DIR}"
mkdir -p "${GEMINI_DIR}/commands"

# Copy extension files
cp -r "${SCRIPT_DIR}/commands/vibey" "${GEMINI_DIR}/commands/"
cp "${SCRIPT_DIR}/GEMINI.md" "${GEMINI_DIR}/"
cp "${SCRIPT_DIR}/settings.json" "${EXTENSIONS_DIR}/"
cp "${SCRIPT_DIR}/gemini-extension.json" "${EXTENSIONS_DIR}/"

echo ""
echo "Installation complete!"
echo ""
echo "Next steps:"
echo "1. Add Vibey MCP server to your project's .gemini/settings.json"
echo "2. Or run: gemini extensions install ${SCRIPT_DIR}"
echo ""
echo "Commands available:"
echo "  /vibey:status  - Check roadmap status"
echo "  /vibey:sprint  - Sprint management"
echo "  /vibey:task    - Task management"
echo "  /vibey:<workflow-id> - Run workflows"
echo ""
'''

        output_dir.mkdir(parents=True, exist_ok=True)
        script_path = output_dir / "install.sh"
        script_path.write_text(script_content, encoding='utf-8')
        script_path.chmod(0o755)

        logger.info(f"Generated install script: {script_path}")
        return script_path

    def generate_readme(self, output_dir: Path) -> Path:
        """
        Generate README for the extension.

        Args:
            output_dir: Directory to write README

        Returns:
            Path to generated README
        """
        readme_content = f'''# {self.manifest.name} - Gemini Extension

{self.manifest.description}

## Installation

### Option 1: Gemini CLI Extensions

```bash
gemini extensions install ./vibey-gemini-extension
```

### Option 2: Manual Installation

```bash
./install.sh
```

### Option 3: Project-Specific

Copy the contents to your project's `.gemini/` directory.

## Usage

### Custom Commands

All commands are prefixed with `/vibey:`:

- `/vibey:status` - Check roadmap and sprint status
- `/vibey:sprint` - Sprint management
- `/vibey:task` - Task management
- `/vibey:<workflow-id>` - Run any workflow

### MCP Tools

Use `/mcp` to see available Vibey tools. All tools are prefixed with `vibey_`:

- `vibey_roadmap_status` - Get roadmap overview
- `vibey_query_task` - Query task details
- `vibey_start_task` - Start a task
- `vibey_complete_task` - Complete a task
- And many more...

## Structure

```
vibey-gemini-extension/
├── gemini-extension.json  # Extension manifest
├── settings.json          # MCP server configuration
├── GEMINI.md             # Context file (agents/workflows docs)
├── commands/
│   └── vibey/
│       ├── status.toml
│       ├── sprint.toml
│       ├── task.toml
│       └── <workflow>.toml
├── install.sh            # Installation script
└── README.md             # This file
```

## Version

- Extension: {self.manifest.version}
- Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}

## License

{self.manifest.license}
'''

        output_dir.mkdir(parents=True, exist_ok=True)
        readme_path = output_dir / "README.md"
        readme_path.write_text(readme_content, encoding='utf-8')

        logger.info(f"Generated README: {readme_path}")
        return readme_path
