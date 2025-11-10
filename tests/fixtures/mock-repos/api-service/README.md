# Mock API Service

This is a mock API service repository template for testing the Vibey framework.

## Tech Stack

- **Framework:** FastAPI 0.104
- **Database:** MongoDB
- **Language:** Python 3.11+
- **Testing:** pytest

## Purpose

This mock repository is used by the Vibey test suite to:
- Test framework deployment to API projects
- Validate sprint planning for backend services
- Test API-specific quality gates
- Validate Python project workflows

## Structure

```
api-service/
├── app/
│   ├── routers/       # API routes
│   ├── models/        # Pydantic models
│   └── services/      # Business logic
├── tests/             # Test files
└── requirements.txt   # Dependencies
```

## Usage in Tests

```python
from tests.utils import RepoBuilder

builder = RepoBuilder(temp_dir)
repo = builder.create_api_service_repo()
builder.add_vibey_framework(repo)
builder.init_git(repo)
```

## Realistic Features

- Actual requirements.txt with FastAPI stack
- FastAPI application with routers
- Pydantic models for validation
- Proper .gitignore for Python
- Health check endpoint
