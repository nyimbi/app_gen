# Development Guide

This guide outlines the development standards and procedures for contributing to the Python Code Refactoring Tool.

## Table of Contents
- [Contributing Guidelines](#contributing-guidelines)
- [Code Style Requirements](#code-style-requirements)
- [Testing Requirements](#testing-requirements)
- [Documentation Standards](#documentation-standards)
- [Release Procedures](#release-procedures)

## Contributing Guidelines

### Getting Started

1. **Fork and Clone**
```bash
git clone https://github.com/your-username/python-refactoring-tool.git
cd python-refactoring-tool
```

2. **Set Up Development Environment**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install development dependencies
pip install -r requirements-dev.txt
```

3. **Create Feature Branch**
```bash
git checkout -b feature/your-feature-name
```

### Pull Request Process

1. **Before Submitting**
```bash
# Run all checks
make check

# Run tests
make test

# Build documentation
make docs
```

2. **PR Requirements**
- Reference relevant issue(s)
- Include test coverage
- Update documentation
- Follow commit message format

### Commit Message Format
```
type(scope): Brief description

Detailed description of changes

Fixes #123
```

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- style: Code style changes
- refactor: Code refactoring
- test: Test updates
- chore: Build/maintenance updates

## Code Style Requirements

### Python Code Style

1. **General Guidelines**
```python
# Good - Clear variable names
user_data = process_input(raw_data)

# Bad - Unclear names
ud = proc(rd)

# Good - Type hints
def process_data(data: List[Dict[str, Any]]) -> ProcessedResult:
    pass

# Bad - Missing type hints
def process_data(data):
    pass
```

2. **Class Structure**
```python
class DataProcessor:
    """
    Process data according to specified rules.
    
    Attributes:
        config: Configuration settings
        logger: Logging instance
    """
    
    def __init__(self, config: Config) -> None:
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def process(self, data: Data) -> Result:
        """
        Process input data.
        
        Args:
            data: Input data to process
            
        Returns:
            Processed result
            
        Raises:
            ValidationError: If data is invalid
        """
        self._validate(data)
        return self._process_validated_data(data)
```

3. **Import Organization**
```python
# Standard library
import os
from typing import Dict, List, Optional

# Third-party imports
import numpy as np
import pandas as pd

# Local imports
from .utils import helpers
from .core import processor
```

### Code Quality Tools

1. **Tool Configuration**

`.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        args: [--line-length=88]
        
  - repo: https://github.com/PyCQA/isort
    rev: 5.10.1
    hooks:
      - id: isort
        args: [--profile=black]
        
  - repo: https://github.com/PyCQA/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
        args: [--max-line-length=88]
```

2. **Running Checks**
```bash
# Format code
black .
isort .

# Check style
flake8 .

# Check types
mypy .
```

## Testing Requirements

### Test Structure

1. **Test Organization**
```
tests/
├── unit/
│   ├── test_processor.py
│   └── test_utils.py
├── integration/
│   └── test_workflow.py
├── e2e/
│   └── test_refactoring.py
└── conftest.py
```

2. **Test Implementation**
```python
import pytest
from unittest.mock import Mock, patch

class TestDataProcessor:
    @pytest.fixture
    def processor(self):
        """Create test processor instance."""
        config = Config(test_mode=True)
        return DataProcessor(config)
    
    def test_process_valid_data(self, processor):
        """Test processing of valid data."""
        data = {"key": "value"}
        result = processor.process(data)
        assert result.status == "success"
    
    @pytest.mark.parametrize("invalid_input", [
        None,
        "",
        {},
        {"invalid": "structure"}
    ])
    def test_process_invalid_data(self, processor, invalid_input):
        """Test handling of invalid data."""
        with pytest.raises(ValidationError):
            processor.process(invalid_input)
```

### Coverage Requirements

```toml
# pyproject.toml
[tool.coverage]
minimum = 90
exclude_paths = [
    "tests/*",
    "docs/*",
    "setup.py",
]
```

### Test Running
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test types
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

## Documentation Standards

### Docstring Format

1. **Module Docstrings**
```python
"""
Core functionality for the refactoring tool.

This module provides the main classes and functions
for analyzing and refactoring Python code.

Classes:
    DataProcessor: Processes input data
    ConfigManager: Manages configuration
"""
```

2. **Class Docstrings**
```python
class DataProcessor:
    """
    Process and transform input data.
    
    This class handles the validation, processing,
    and transformation of input data according to
    specified rules.
    
    Attributes:
        config (Config): Configuration settings
        logger (Logger): Logging instance
        
    Examples:
        >>> processor = DataProcessor(config)
        >>> result = processor.process(data)
    """
```

3. **Method Docstrings**
```python
def process_data(
    self,
    data: Dict[str, Any],
    options: Optional[Dict[str, Any]] = None
) -> ProcessedResult:
    """
    Process input data with optional configuration.
    
    Args:
        data: Input data to process
        options: Optional processing configuration
        
    Returns:
        ProcessedResult containing the processed data
        
    Raises:
        ValidationError: If input data is invalid
        ProcessingError: If processing fails
        
    Examples:
        >>> result = processor.process_data({"key": "value"})
        >>> assert result.status == "success"
    """
```

### Documentation Building

```bash
# Generate API documentation
sphinx-apidoc -o docs/api src/

# Build documentation
sphinx-build -b html docs/ docs/_build/html
```

## Release Procedures

### Version Management

1. **Version Format**
```python
# src/__init__.py
__version__ = "1.2.3"  # Major.Minor.Patch
```

2. **Version Bump Script**
```python
def bump_version(version_type: str) -> str:
    """
    Bump version number.
    
    Args:
        version_type: One of 'major', 'minor', 'patch'
    """
    current = __version__.split('.')
    if version_type == 'major':
        current[0] = str(int(current[0]) + 1)
        current[1] = current[2] = '0'
    elif version_type == 'minor':
        current[1] = str(int(current[1]) + 1)
        current[2] = '0'
    else:  # patch
        current[2] = str(int(current[2]) + 1)
    
    new_version = '.'.join(current)
    update_version_files(new_version)
    return new_version
```

### Release Process

1. **Pre-release Checklist**
```bash
# Run all checks
make check-all

# Run integration tests
make test-integration

# Build and verify documentation
make docs
```

2. **Release Steps**
```bash
# Create release branch
git checkout -b release/v1.2.3

# Bump version
python scripts/bump_version.py patch

# Update changelog
python scripts/update_changelog.py

# Create distribution
python -m build

# Create release commit
git commit -am "Release v1.2.3"

# Tag release
git tag -a v1.2.3 -m "Version 1.2.3"

# Push to remote
git push origin release/v1.2.3 --tags
```

3. **Post-release**
```bash
# Publish to PyPI
python -m twine upload dist/*

# Merge to main
git checkout main
git merge release/v1.2.3

# Clean up
git branch -d release/v1.2.3
```

### Release Notes Template
```markdown
# Release v1.2.3

## New Features
- Feature 1
- Feature 2

## Bug Fixes
- Fix 1
- Fix 2

## Documentation
- Doc update 1
- Doc update 2

## Breaking Changes
- Breaking change 1

## Migration Guide
Steps to upgrade from v1.2.2 to v1.2.3...
```

---

This development guide provides comprehensive standards and procedures for contributing to the project. Always refer to the latest version of this guide in the repository.