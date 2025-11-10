# Mock ML Project

This is a mock machine learning project repository template for testing the Vibey framework.

## Tech Stack

- **Framework:** TensorFlow 2.14
- **Language:** Python 3.11+
- **Notebooks:** Jupyter
- **Data:** NumPy, Pandas
- **Testing:** pytest

## Purpose

This mock repository is used by the Vibey test suite to:
- Test framework deployment to ML projects
- Validate sprint planning for data science workflows
- Test ML-specific quality gates
- Validate notebook integration

## Structure

```
ml-project/
├── notebooks/         # Jupyter notebooks
├── src/
│   ├── models/       # Model definitions
│   └── data/         # Data processing
├── tests/            # Test files
└── requirements.txt  # Dependencies
```

## Usage in Tests

```python
from tests.utils import RepoBuilder

builder = RepoBuilder(temp_dir)
repo = builder.create_ml_project_repo()
builder.add_vibey_framework(repo)
builder.init_git(repo)
```

## Realistic Features

- Actual requirements.txt with TensorFlow stack
- Training script with model definition
- Proper .gitignore for ML projects
- Data and model directories
- README with setup instructions
