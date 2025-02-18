# Examples Guide

A comprehensive collection of examples demonstrating various use cases of the Python Code Refactoring Tool.

## Table of Contents
- [Basic Usage Examples](#basic-usage-examples)
- [Complex Refactoring Scenarios](#complex-refactoring-scenarios)
- [Configuration Examples](#configuration-examples)
- [Custom Rule Examples](#custom-rule-examples)
- [Integration Examples](#integration-examples)

## Basic Usage Examples

### 1. Simple Class Refactoring

**Original Code:**
```python
# original.py
class DataProcessor:
    def __init__(self):
        self.data = []
        self.config = {}

    def process(self, input_data):
        # Process data
        return input_data * 2

    def validate(self, data):
        # Validate data
        return len(data) > 0

class DataValidator:
    def check_format(self, data):
        # Check format
        return isinstance(data, list)
```

**Configuration:**
```yaml
# config.yaml
version: "1.0"
project_name: "DataTools"
project_description: "Data processing utilities"

modules:
  processing:
    description: "Data processing module"
    classes:
      - DataProcessor
    dependencies: []

  validation:
    description: "Data validation module"
    classes:
      - DataValidator
    dependencies: []

settings:
  format_code: true
  generate_docs: true
  check_dependencies: true
  validate_structure: true
```

**Usage:**
```bash
python refactor.py original.py ./refactored config.yaml
```

**Result:**
```
refactored/
├── src/
│   ├── processing/
│   │   ├── __init__.py
│   │   ├── data_processor.py
│   │   └── data_processor.pyi
│   └── validation/
│       ├── __init__.py
│       ├── data_validator.py
│       └── data_validator.pyi
├── tests/
├── docs/
└── setup.py
```

### 2. Adding Type Hints

**Original Code:**
```python
def process_data(data, config=None):
    if config is None:
        config = {}
    result = []
    for item in data:
        if item.get('active'):
            result.append(transform(item))
    return result

def transform(item):
    return {
        'id': item.get('id'),
        'value': item.get('value', 0) * 2
    }
```

**Configuration:**
```yaml
settings:
  add_type_hints: true
  type_checking: strict
```

**Result:**
```python
from typing import Dict, List, Optional, Any

def process_data(
    data: List[Dict[str, Any]],
    config: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    if config is None:
        config = {}
    result: List[Dict[str, Any]] = []
    for item in data:
        if item.get('active'):
            result.append(transform(item))
    return result

def transform(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'id': item.get('id'),
        'value': item.get('value', 0) * 2
    }
```

## Complex Refactoring Scenarios

### 1. Web Scraper Refactoring

**Original Code:**
```python
# scraper.py
class WebScraper:
    def __init__(self):
        self.session = None
        self.cache = {}
        self.parser = None

    def fetch(self, url):
        # Fetch webpage
        pass

    def parse(self, content):
        # Parse content
        pass

    def cache_result(self, key, data):
        # Cache data
        pass

    def process_page(self, url):
        # Process webpage
        pass
```

**Configuration:**
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
      - network
      - parser
      - cache

  network:
    description: "Network handling"
    classes:
      - SessionManager
      - RequestHandler
    dependencies: []

  parser:
    description: "Content parsing"
    classes:
      - ContentParser
      - HTMLCleaner
    dependencies: []

  cache:
    description: "Caching system"
    classes:
      - CacheManager
      - CacheStrategy
    dependencies: []

settings:
  format_code: true
  generate_docs: true
  check_dependencies: true
  validate_structure: true
  async_support: true
```

**Result Structure:**
```
src/
├── core/
│   ├── __init__.py
│   ├── web_scraper.py
│   └── web_scraper.pyi
├── network/
│   ├── __init__.py
│   ├── session_manager.py
│   └── request_handler.py
├── parser/
│   ├── __init__.py
│   ├── content_parser.py
│   └── html_cleaner.py
└── cache/
    ├── __init__.py
    ├── cache_manager.py
    └── cache_strategy.py
```

## Configuration Examples

### 1. Microservices Architecture

```yaml
version: "1.0"
project_name: "MicroService"
project_description: "Microservice architecture example"

modules:
  api:
    description: "API endpoints"
    classes:
      - UserAPI
      - OrderAPI
    dependencies:
      - service
      - auth

  service:
    description: "Business logic"
    classes:
      - UserService
      - OrderService
    dependencies:
      - repository
      - events

  repository:
    description: "Data access"
    classes:
      - UserRepository
      - OrderRepository
    dependencies:
      - database

  database:
    description: "Database handlers"
    classes:
      - DatabaseConnection
      - QueryBuilder
    dependencies: []

  auth:
    description: "Authentication"
    classes:
      - AuthManager
      - TokenHandler
    dependencies:
      - database

  events:
    description: "Event system"
    classes:
      - EventBus
      - EventHandler
    dependencies: []

settings:
  format_code: true
  generate_docs: true
  async_support: true
  type_checking: strict
  test_generation: true
```

### 2. Data Processing Pipeline

```yaml
version: "1.0"
project_name: "DataPipeline"
project_description: "Data processing pipeline"

modules:
  pipeline:
    description: "Pipeline orchestration"
    classes:
      - Pipeline
      - PipelineStage
    dependencies:
      - processors
      - validation

  processors:
    description: "Data processors"
    classes:
      - CSVProcessor
      - JSONProcessor
      - XMLProcessor
    dependencies:
      - validation
      - utils

  validation:
    description: "Data validation"
    classes:
      - SchemaValidator
      - DataCleaner
    dependencies:
      - utils

  utils:
    description: "Utilities"
    classes:
      - Logger
      - ConfigManager
    dependencies: []

settings:
  logging: detailed
  error_handling: strict
  validation: strict
```

## Custom Rule Examples

### 1. Custom Import Rules

```python
# custom_rules.py
class ImportRules:
    def __init__(self):
        self.patterns = {
            'stdlib': r'^(os|sys|json|datetime)$',
            'vendor': r'^(requests|numpy|pandas)$',
            'internal': r'^myapp\.',
        }
        
    def sort_imports(self, imports):
        """Sort imports according to custom rules."""
        groups = {
            'stdlib': [],
            'vendor': [],
            'internal': [],
            'other': []
        }
        
        for imp in imports:
            matched = False
            for category, pattern in self.patterns.items():
                if re.match(pattern, imp):
                    groups[category].append(imp)
                    matched = True
                    break
            if not matched:
                groups['other'].append(imp)
                
        return groups
```

### 2. Custom Documentation Rules

```python
# doc_rules.py
class DocRules:
    def validate_docstring(self, docstring):
        """Validate docstring against custom rules."""
        rules = [
            self._check_description,
            self._check_args,
            self._check_returns,
            self._check_examples
        ]
        
        results = []
        for rule in rules:
            results.append(rule(docstring))
        
        return all(results)
    
    def _check_description(self, docstring):
        """Check if description meets length and clarity rules."""
        first_line = docstring.split('\n')[0].strip()
        return len(first_line) >= 10 and first_line.endswith('.')
```

## Integration Examples

### 1. CI/CD Integration

```yaml
# .github/workflows/refactor.yml
name: Code Refactoring

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  refactor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          
      - name: Run refactoring
        run: |
          python refactor.py src/legacy.py ./refactored config.yaml
          
      - name: Run tests
        run: pytest tests/
```

### 2. IDE Plugin Integration

```python
# vscode_extension.py
class VSCodeRefactorExtension:
    def __init__(self):
        self.refactorer = CodeRefactorer()
        
    def on_save(self, document):
        """Handle document save event."""
        if self._should_refactor(document):
            self._refactor_document(document)
    
    def _should_refactor(self, document):
        """Check if document should be refactored."""
        return (
            document.language_id == "python" and
            self._has_refactor_marker(document)
        )
    
    def _refactor_document(self, document):
        """Refactor document and update editor."""
        try:
            result = self.refactorer.refactor_text(document.text)
            self._update_editor(result)
        except Exception as e:
            self._show_error(str(e))
```

### 3. Build System Integration

```python
# setup.py
from setuptools import setup, Command
class RefactorCommand(Command):
    description = 'Run code refactoring'
    user_options = [
        ('config=', 'c', 'path to config file'),
        ('source=', 's', 'source directory'),
        ('output=', 'o', 'output directory'),
    ]
    
    def initialize_options(self):
        self.config = None
        self.source = None
        self.output = None
    
    def finalize_options(self):
        assert self.config is not None, 'Config file required'
        assert self.source is not None, 'Source directory required'
        assert self.output is not None, 'Output directory required'
    
    def run(self):
        """Run refactoring process."""
        from refactoring_tool import CodeRefactorer
        refactorer = CodeRefactorer(
            self.config,
            self.source,
            self.output
        )
        refactorer.run()

setup(
    # ... other setup parameters ...
    cmdclass={
        'refactor': RefactorCommand,
    },
)
```

---

These examples demonstrate various ways to use and integrate the refactoring tool. Each example includes detailed configurations and explanations of the results.
