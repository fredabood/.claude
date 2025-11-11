"""
Config loader utility for tests.

Provides helper functions to load and query modular config files.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import yaml


class ConfigLoader:
    """Load and query modular Vibey config files."""

    def __init__(self, repo_path: Path):
        """
        Initialize ConfigLoader.

        Args:
            repo_path: Path to repository root
        """
        self.repo_path = Path(repo_path)
        self.config_dir = self.repo_path / ".vibey" / "config"
        self._cache: Dict[str, Dict[str, Any]] = {}

    def load_project_config(self) -> Dict[str, Any]:
        """Load project.yaml config."""
        if 'project' not in self._cache:
            config_file = self.config_dir / "project.yaml"
            if config_file.exists():
                with open(config_file) as f:
                    self._cache['project'] = yaml.safe_load(f)
            else:
                self._cache['project'] = {}
        return self._cache['project']

    def load_framework_config(self) -> Dict[str, Any]:
        """Load framework.yaml config."""
        if 'framework' not in self._cache:
            config_file = self.config_dir / "framework.yaml"
            if config_file.exists():
                with open(config_file) as f:
                    self._cache['framework'] = yaml.safe_load(f)
            else:
                self._cache['framework'] = {}
        return self._cache['framework']

    def load_agents_config(self) -> Dict[str, Any]:
        """Load agents.yaml config."""
        if 'agents' not in self._cache:
            config_file = self.config_dir / "agents.yaml"
            if config_file.exists():
                with open(config_file) as f:
                    self._cache['agents'] = yaml.safe_load(f)
            else:
                self._cache['agents'] = {}
        return self._cache['agents']

    def load_quality_gates_config(self) -> Dict[str, Any]:
        """Load quality-gates.yaml config."""
        if 'quality_gates' not in self._cache:
            config_file = self.config_dir / "quality-gates.yaml"
            if config_file.exists():
                with open(config_file) as f:
                    self._cache['quality_gates'] = yaml.safe_load(f)
            else:
                self._cache['quality_gates'] = {}
        return self._cache['quality_gates']

    def load_all_configs(self) -> Dict[str, Any]:
        """
        Load all config files and combine into single dict.

        Returns merged config dict matching old monolithic structure.
        """
        return {
            **self.load_project_config(),
            **self.load_framework_config(),
            **self.load_agents_config(),
            **self.load_quality_gates_config(),
        }

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get config value by dot-notation path.

        Examples:
            config.get('project.name')
            config.get('framework.orchestration_mode')
            config.get('agents.enabled')

        Args:
            key_path: Dot-separated path to value
            default: Default value if not found

        Returns:
            Config value or default
        """
        keys = key_path.split('.')

        # Determine which config file to load
        if keys[0] == 'project':
            config = self.load_project_config()
        elif keys[0] == 'framework':
            config = self.load_framework_config()
        elif keys[0] == 'agents':
            config = self.load_agents_config()
        elif keys[0] == 'quality_gates':
            config = self.load_quality_gates_config()
        else:
            return default

        # Navigate the nested structure
        value = config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def exists(self) -> bool:
        """Check if config directory exists."""
        return self.config_dir.exists()

    def get_orchestration_mode(self) -> Optional[str]:
        """Get orchestration mode from framework config."""
        return self.get('framework.orchestration_mode')

    def get_quality_gates_enabled(self) -> bool:
        """Check if quality gates are enabled."""
        return self.get('quality_gates.enabled', False)

    def get_project_name(self) -> Optional[str]:
        """Get project name."""
        return self.get('project.name')

    def get_project_type(self) -> Optional[str]:
        """Get project type."""
        return self.get('project.type')

    def get_enabled_agents(self) -> list:
        """Get list of enabled agents."""
        return self.get('agents.enabled', [])

    def config_files_exist(self) -> Dict[str, bool]:
        """Check which config files exist."""
        return {
            'project.yaml': (self.config_dir / 'project.yaml').exists(),
            'framework.yaml': (self.config_dir / 'framework.yaml').exists(),
            'agents.yaml': (self.config_dir / 'agents.yaml').exists(),
            'quality-gates.yaml': (self.config_dir / 'quality-gates.yaml').exists(),
        }

    def all_config_files_exist(self) -> bool:
        """Check if all required config files exist."""
        files = self.config_files_exist()
        return all(files.values())
