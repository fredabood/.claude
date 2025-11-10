# Mock Web Application

This is a mock web application repository template for testing the Vibey framework.

## Tech Stack

- **Frontend:** React 18.2
- **Backend:** Node.js + Express 4.18
- **Database:** PostgreSQL
- **Testing:** Jest

## Purpose

This mock repository is used by the Vibey test suite to:
- Test framework deployment to web application projects
- Validate sprint planning for full-stack projects
- Test quality gates (security, testing, performance)
- Validate git workflow integration

## Structure

```
web-app/
├── src/
│   ├── components/    # React components
│   ├── pages/         # Page components
│   └── utils/         # Utility functions
├── server/
│   ├── routes/        # Express routes
│   └── models/        # Database models
├── tests/             # Test files
├── public/            # Static assets
└── package.json       # Dependencies
```

## Usage in Tests

```python
from tests.utils import RepoBuilder

builder = RepoBuilder(temp_dir)
repo = builder.create_web_app_repo()
builder.add_vibey_framework(repo)
builder.init_git(repo)
```

## Realistic Features

- Actual package.json with real dependencies
- React component with JSX
- Express server with routes
- Proper .gitignore
- README with getting started guide
