# Getting Started with the Python Code Refactoring Tool

Welcome to the Python Code Refactoring Tool! This comprehensive guide will walk you through setting up and using the tool to refactor your Python codebase into a well-structured, maintainable project.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Configuration Guide](#configuration-guide)
- [Step-by-Step Tutorial](#step-by-step-tutorial)
- [Common Use Cases](#common-use-cases)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before you begin, ensure your system meets the following requirements:

### System Requirements
- Python 3.7 or higher
- 500MB free disk space (minimum)
- Write permissions in the output directory

### Required Python Packages
```bash
networkx>=2.5
black>=22.0
isort>=5.0
jinja2>=3.0
pyyaml>=5.1
sphinx>=4.0
pytest>=6.0
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/python-refactoring-tool.git
cd python-refactoring-tool
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Verify installation:
```bash
python refactor.py --version
```

## Basic Usage

The basic command structure is:
```bash
python refactor.py <source_file> <output_dir> <config_file>
```

Example:
```bash
python refactor.py mysource.py ./refactored config.yaml
```

### Command Line Arguments

- `source_file`: Path to your Python source file
- `output_dir`: Directory where the refactored code will be generated
- `config_file`: Path to your YAML configuration file

## Configuration Guide

The configuration file (YAML) is crucial for controlling the refactoring process. Here's a basic template:

```yaml
version: "1.0"
project_name: "MyProject"
project_description: "Project description"

modules:
  core:
    description: "Core functionality"
    classes:
      - MainClass
      - HelperClass
    dependencies:
      - utils

  utils:
    description: "Utility functions"
    classes:
      - UtilityClass
    dependencies: []

settings:
  format_code: true
  generate_docs: true
  check_dependencies: true
  validate_structure: true
```

### Configuration Fields Explained

1. Top-Level Fields:
   - `version`: Configuration format version
   - `project_name`: Your project's name
   - `project_description`: Brief project description
   - `modules`: Module definitions
   - `settings`: Refactoring settings

2. Module Configuration:
   - `description`: Module purpose
   - `classes`: List of classes to include
   - `dependencies`: Other modules this module depends on

3. Settings Options:
   - `format_code`: Apply code formatting (using black and isort)
   - `generate_docs`: Generate documentation
   - `check_dependencies`: Validate dependencies
   - `validate_structure`: Verify output structure

## Step-by-Step Tutorial

Let's walk through a complete refactoring example.

### 1. Prepare Your Source Code

Assume you have a file `webscraper.py` with multiple classes:

```python
class WebScraper:
    # ... scraping logic

class ContentProcessor:
    # ... processing logic

class CacheManager:
    # ... caching logic
```

### 2. Create Configuration File

Create `refactor_config.yaml`:

```yaml
version: "1.0"
project_name: "WebScraper"
project_description: "Advanced web scraping library"

modules:
  core:
    description: "Core scraping functionality"
    classes:
      - WebScraper
    dependencies:
      - content
      - cache

  content:
    description: "Content processing"
    classes:
      - ContentProcessor
    dependencies:
      - utils

  cache:
    description: "Caching implementation"
    classes:
      - CacheManager
    dependencies:
      - utils

settings:
  format_code: true
  generate_docs: true
  check_dependencies: true
  validate_structure: true
```

### 3. Run the Refactoring

```bash
python refactor.py webscraper.py ./refactored refactor_config.yaml
```

### 4. Examine the Output

The tool will create a structured project:

```
refactored/
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── web_scraper.py
│   │   └── web_scraper.pyi
│   ├── content/
│   │   ├── __init__.py
│   │   ├── content_processor.py
│   │   └── content_processor.pyi
│   └── cache/
│       ├── __init__.py
│       ├── cache_manager.py
│       └── cache_manager.pyi
├── tests/
├── docs/
├── setup.py
└── pyproject.toml
```

## Common Use Cases

### 1. Refactoring with Dependencies

When your classes have interdependencies:

```yaml
modules:
  module_a:
    classes: ["ClassA"]
    dependencies: ["module_b"]
  module_b:
    classes: ["ClassB"]
    dependencies: []
```

### 2. Handling Async Code

The tool automatically detects async code and generates appropriate test fixtures:

```python
class AsyncWebScraper:
    async def fetch_data(self):
        # ... async code
```

### 3. Preserving Type Hints

The tool maintains type information and generates stub files:

```python
class DataProcessor:
    def process(self, data: List[Dict[str, Any]]) -> ProcessedData:
        # ... processing logic
```

## Best Practices

1. **Before Refactoring**:
   - Back up your code
   - Run your test suite
   - Document known dependencies
   - Review the configuration file

2. **Configuration Tips**:
   - Keep modules focused and cohesive
   - Minimize cross-module dependencies
   - Use descriptive module names
   - Include comprehensive descriptions

3. **After Refactoring**:
   - Review generated documentation
   - Run the test suite
   - Check type stub accuracy
   - Verify dependency graphs

## Troubleshooting

### Common Issues and Solutions

1. **Circular Dependencies**
   
   Error:
   ```
   ValueError: Circular dependencies detected
   ```
   
   Solution:
   - Review your module dependencies
   - Split problematic modules
   - Use dependency injection

2. **Permission Errors**
   
   Error:
   ```
   PermissionError: No write permission for output_dir
   ```
   
   Solution:
   - Check directory permissions
   - Run with appropriate privileges
   - Verify output directory exists

3. **Invalid Configuration**
   
   Error:
   ```
   ValueError: Missing required configuration fields
   ```
   
   Solution:
   - Compare with template configuration
   - Check YAML syntax
   - Verify all required fields

### Getting Help

If you encounter issues:

1. Check the logs in `refactor.log`
2. Review error messages
3. Consult the documentation
4. Open an issue on GitHub

## Next Steps

After successfully refactoring your code:

1. Review the generated documentation in `docs/`
2. Examine the dependency graph in `dependencies.png`
3. Run the generated test suite
4. Check the metrics report in `metrics.json`

For more advanced usage and features, consult the full documentation.

---

Remember: The refactoring tool includes automatic backup and rollback mechanisms, so you can safely experiment with different configurations and options. If anything goes wrong, your original code remains intact.

Need help? Join our community:
- GitHub Issues: [Link to Issues]
- Documentation: [Link to Docs]
- Community Forum: [Link to Forum]
