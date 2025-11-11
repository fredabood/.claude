"""
Repository builder utility for creating mock test repositories.

This module provides tools for creating realistic mock repositories
for testing Vibey framework functionality.
"""

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class TestRepo:
    """Represents a test repository."""

    path: Path
    repo_type: str
    name: str
    has_git: bool = False
    has_vibey: bool = False

    def __str__(self) -> str:
        return f"TestRepo({self.name}, type={self.repo_type}, path={self.path})"


class RepoBuilder:
    """
    Build mock repositories for testing.

    This class provides methods to create realistic mock repositories
    with different tech stacks, directory structures, and configurations.
    """

    def __init__(self, base_path: Path):
        """
        Initialize RepoBuilder.

        Args:
            base_path: Base directory for creating repositories
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def create_web_app_repo(self, name: str = "test-web-app") -> TestRepo:
        """
        Create a mock web application repository (React + Node.js + PostgreSQL).

        Args:
            name: Repository name

        Returns:
            TestRepo instance
        """
        repo_path = self.base_path / name
        repo_path.mkdir(parents=True, exist_ok=True)

        # Create directory structure
        (repo_path / "src").mkdir(exist_ok=True)
        (repo_path / "src" / "components").mkdir(exist_ok=True)
        (repo_path / "src" / "pages").mkdir(exist_ok=True)
        (repo_path / "src" / "utils").mkdir(exist_ok=True)
        (repo_path / "public").mkdir(exist_ok=True)
        (repo_path / "tests").mkdir(exist_ok=True)
        (repo_path / "server").mkdir(exist_ok=True)
        (repo_path / "server" / "routes").mkdir(exist_ok=True)
        (repo_path / "server" / "models").mkdir(exist_ok=True)

        # Create package.json
        package_json = {
            "name": name,
            "version": "1.0.0",
            "description": "Mock web application for testing",
            "main": "server/index.js",
            "scripts": {
                "start": "node server/index.js",
                "dev": "nodemon server/index.js",
                "test": "jest",
                "build": "react-scripts build"
            },
            "dependencies": {
                "express": "^4.18.2",
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "pg": "^8.11.3"
            },
            "devDependencies": {
                "jest": "^29.7.0",
                "nodemon": "^3.0.1"
            }
        }
        self._write_json(repo_path / "package.json", package_json)

        # Create basic source files
        self._write_file(
            repo_path / "src" / "App.jsx",
            """import React from 'react';

function App() {
  return (
    <div className="App">
      <h1>Mock Web Application</h1>
      <p>This is a test application for Vibey framework testing.</p>
    </div>
  );
}

export default App;
"""
        )

        self._write_file(
            repo_path / "server" / "index.js",
            """const express = require('express');
const app = express();
const port = 3000;

app.get('/', (req, res) => {
  res.send('Hello from mock web app!');
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
"""
        )

        # Create README
        self._write_file(
            repo_path / "README.md",
            f"""# {name}

Mock web application for Vibey framework testing.

## Tech Stack

- Frontend: React
- Backend: Node.js + Express
- Database: PostgreSQL

## Getting Started

```bash
npm install
npm run dev
```

## Testing

```bash
npm test
```
"""
        )

        # Create .gitignore
        self._write_file(
            repo_path / ".gitignore",
            """node_modules/
dist/
build/
.env
.DS_Store
*.log
"""
        )

        return TestRepo(
            path=repo_path,
            repo_type="web-app",
            name=name,
            has_git=False,
            has_vibey=False
        )

    def create_api_service_repo(self, name: str = "test-api-service") -> TestRepo:
        """
        Create a mock API service repository (FastAPI + MongoDB).

        Args:
            name: Repository name

        Returns:
            TestRepo instance
        """
        repo_path = self.base_path / name
        repo_path.mkdir(parents=True, exist_ok=True)

        # Create directory structure
        (repo_path / "app").mkdir(exist_ok=True)
        (repo_path / "app" / "routers").mkdir(exist_ok=True)
        (repo_path / "app" / "models").mkdir(exist_ok=True)
        (repo_path / "app" / "services").mkdir(exist_ok=True)
        (repo_path / "tests").mkdir(exist_ok=True)

        # Create requirements.txt
        self._write_file(
            repo_path / "requirements.txt",
            """fastapi==0.104.1
uvicorn[standard]==0.24.0
pymongo==4.5.0
pydantic==2.5.0
python-dotenv==1.0.0
pytest==7.4.3
httpx==0.25.1
"""
        )

        # Create main application file
        self._write_file(
            repo_path / "app" / "main.py",
            """from fastapi import FastAPI
from app.routers import users

app = FastAPI(title="Mock API Service")

app.include_router(users.router)

@app.get("/")
def read_root():
    return {"message": "Mock API Service for Vibey testing"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
"""
        )

        # Create router
        self._write_file(
            repo_path / "app" / "routers" / "users.py",
            """from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/")
def list_users():
    return {"users": []}

@router.post("/")
def create_user(name: str):
    return {"user": {"name": name, "id": 1}}
"""
        )

        # Create README
        self._write_file(
            repo_path / "README.md",
            f"""# {name}

Mock API service for Vibey framework testing.

## Tech Stack

- Framework: FastAPI
- Database: MongoDB
- Language: Python 3.11+

## Getting Started

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Testing

```bash
pytest
```
"""
        )

        # Create .gitignore
        self._write_file(
            repo_path / ".gitignore",
            """__pycache__/
*.py[cod]
*$py.class
venv/
.env
.pytest_cache/
.coverage
htmlcov/
"""
        )

        return TestRepo(
            path=repo_path,
            repo_type="api-service",
            name=name,
            has_git=False,
            has_vibey=False
        )

    def create_ml_project_repo(self, name: str = "test-ml-project") -> TestRepo:
        """
        Create a mock ML project repository (Python + Jupyter + TensorFlow).

        Args:
            name: Repository name

        Returns:
            TestRepo instance
        """
        repo_path = self.base_path / name
        repo_path.mkdir(parents=True, exist_ok=True)

        # Create directory structure
        (repo_path / "notebooks").mkdir(exist_ok=True)
        (repo_path / "src").mkdir(exist_ok=True)
        (repo_path / "src" / "models").mkdir(exist_ok=True)
        (repo_path / "src" / "data").mkdir(exist_ok=True)
        (repo_path / "tests").mkdir(exist_ok=True)
        (repo_path / "data").mkdir(exist_ok=True)

        # Create requirements.txt
        self._write_file(
            repo_path / "requirements.txt",
            """tensorflow==2.14.0
numpy==1.26.1
pandas==2.1.2
jupyter==1.0.0
scikit-learn==1.3.2
matplotlib==3.8.1
pytest==7.4.3
"""
        )

        # Create main training script
        self._write_file(
            repo_path / "src" / "train.py",
            """import numpy as np
import tensorflow as tf

def train_model():
    \"\"\"Mock training function.\"\"\"
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dense(10, activation='softmax')
    ])

    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )

    print("Mock model trained successfully")
    return model

if __name__ == "__main__":
    train_model()
"""
        )

        # Create README
        self._write_file(
            repo_path / "README.md",
            f"""# {name}

Mock ML project for Vibey framework testing.

## Tech Stack

- Framework: TensorFlow
- Language: Python 3.11+
- Notebooks: Jupyter

## Getting Started

```bash
pip install -r requirements.txt
python src/train.py
```

## Notebooks

Jupyter notebooks are in the `notebooks/` directory.

## Testing

```bash
pytest
```
"""
        )

        # Create .gitignore
        self._write_file(
            repo_path / ".gitignore",
            """__pycache__/
*.py[cod]
venv/
.ipynb_checkpoints/
data/
models/
*.h5
*.pkl
"""
        )

        return TestRepo(
            path=repo_path,
            repo_type="ml-project",
            name=name,
            has_git=False,
            has_vibey=False
        )

    def add_vibey_framework(
        self,
        repo: TestRepo,
        orchestration_mode: str = "balanced",
        quality_gates_enabled: bool = True,
        platform: str = "claude-code",
        agents: Optional[List[str]] = None
    ) -> None:
        """
        Deploy Vibey framework to a test repository.

        Args:
            repo: TestRepo to deploy Vibey to
            orchestration_mode: Orchestration mode (simple, balanced, tiered)
            quality_gates_enabled: Whether quality gates are enabled
            platform: Platform name (claude-code, goose, cursor, etc.)
            agents: List of agent names to enable
        """
        if agents is None:
            agents = ["web-developer", "test-engineer"]

        vibey_dir = repo.path / ".vibey"
        vibey_dir.mkdir(exist_ok=True)
        config_dir = vibey_dir / "config"
        config_dir.mkdir(exist_ok=True)

        # Create minimal CLAUDE.md (still in root for platform compatibility)
        self._write_file(
            repo.path / "CLAUDE.md",
            f"""# {repo.name} - Project Context

**Project Type:** {repo.repo_type}
**Version:** 1.0.0

Mock project for Vibey framework testing.

---

## Tech Stack

**Languages:** python, javascript
**Frameworks:** react, express

---

## Available Agents

{', '.join(agents)}

---

## Orchestration Mode

**Current Mode:** {orchestration_mode}

<!-- VIBEY_FRAMEWORK_MANAGED -->
"""
        )

        # Create modular config files

        # 1. project.yaml
        project_config = f"""project:
  name: {repo.name}
  type: {repo.repo_type}
  version: 1.0.0
  description: Mock project for Vibey framework testing
  tech_stack:
    languages:
      - python
      - javascript
    frameworks:
      - react
      - express
"""
        self._write_file(config_dir / "project.yaml", project_config)

        # 2. framework.yaml
        framework_config = f"""framework:
  version: 2.0.0
  orchestration_mode: {orchestration_mode}
  platform: {platform}
  features:
    quality_gates: {str(quality_gates_enabled).lower()}
    roadmap_integration: true
"""
        self._write_file(config_dir / "framework.yaml", framework_config)

        # 3. agents.yaml
        agents_yaml = '\n'.join(f'  - {agent}' for agent in agents)
        agents_config = f"""agents:
  enabled:
{agents_yaml}
  preferences:
    auto_select: true
    require_confirmation: false
"""
        self._write_file(config_dir / "agents.yaml", agents_config)

        # 4. quality-gates.yaml
        quality_gates_config = """quality_gates:
  enabled: true
  gates:
    security:
      enabled: true
      blocking: true
      threshold: 80
    testing:
      enabled: true
      blocking: true
      threshold: 90
    performance:
      enabled: true
      blocking: false
      threshold: 80
    logging:
      enabled: true
      blocking: false
      threshold: 70
"""
        self._write_file(config_dir / "quality-gates.yaml", quality_gates_config)

        repo.has_vibey = True

    def init_git(self, repo: TestRepo, initial_commit: bool = True) -> None:
        """
        Initialize git repository.

        Args:
            repo: TestRepo to initialize git for
            initial_commit: Whether to create initial commit
        """
        subprocess.run(
            ["git", "init"],
            cwd=repo.path,
            capture_output=True,
            check=True
        )

        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo.path,
            capture_output=True,
            check=True
        )

        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo.path,
            capture_output=True,
            check=True
        )

        if initial_commit:
            subprocess.run(
                ["git", "add", "."],
                cwd=repo.path,
                capture_output=True,
                check=True
            )

            subprocess.run(
                ["git", "commit", "-m", "Initial commit"],
                cwd=repo.path,
                capture_output=True,
                check=True
            )

            # Rename default branch to 'main' to match test expectations
            subprocess.run(
                ["git", "branch", "-M", "main"],
                cwd=repo.path,
                capture_output=True,
                check=True
            )

        repo.has_git = True

    @staticmethod
    def _write_file(path: Path, content: str) -> None:
        """Write content to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    @staticmethod
    def _write_json(path: Path, data: dict) -> None:
        """Write JSON data to file."""
        import json
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))
