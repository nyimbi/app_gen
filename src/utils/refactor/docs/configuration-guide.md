# Configuration Guide - Python Code Refactoring Tool

This guide provides a comprehensive overview of the configuration system used by the Python Code Refactoring Tool. The configuration file, written in YAML, controls every aspect of the refactoring process.

## Table of Contents
- [YAML Configuration Structure](#yaml-configuration-structure)
- [Required Fields](#required-fields)
- [Module Configuration](#module-configuration)
- [Settings Options](#settings-options)
- [Dependency Rules](#dependency-rules)
- [Example Configurations](#example-configurations)
- [Best Practices](#best-practices)

## YAML Configuration Structure

The configuration file follows a hierarchical structure with four main sections:
1. Version information
2. Project metadata
3. Module definitions
4. Global settings

Basic structure:
```yaml
version: "1.0"
project_name: "ProjectName"
project_description: "Project description"

modules:
  module_name:
    description: "Module description"
    classes: []
    dependencies: []

settings:
  option1: true
  option2: false
```

## Required Fields

### Top-Level Required Fields

| Field | Type | Description | Required? |
|-------|------|-------------|-----------|
| `version` | string | Configuration format version | Yes |
| `project_name` | string | Name of the project | Yes |
| `project_description` | string | Project description | Yes |
| `modules` | object | Module definitions | Yes |
| `settings` | object | Global settings | Yes |

### Version Field
```yaml
version: "1.0"  # Currently supported versions: 1.0
```
- Must be a string
- Controls configuration format compatibility
- Used for future upgrades and backward compatibility

### Project Name and Description
```yaml
project_name: "WebScraper"
project_description: "Advanced web scraping library with caching and async support"
```
- `project_name`: Used for package naming and documentation
  - Must be a valid Python package name
  - Should be unique and descriptive
  - Avoid Python reserved words
- `project_description`: Used in documentation and package metadata
  - Should be concise but informative
  - Supports multi-line descriptions using YAML syntax

## Module Configuration

### Module Structure
Each module must define:
```yaml
modules:
  module_name:
    description: "Module purpose and functionality"
    classes:
      - ClassOne
      - ClassTwo
    dependencies:
      - other_module
```

### Required Module Fields

| Field | Type | Description | Required? |
|-------|------|-------------|-----------|
| `description` | string | Module purpose | Yes |
| `classes` | list | Classes in module | Yes |
| `dependencies` | list | Module dependencies | Yes |

### Optional Module Fields
```yaml
modules:
  module_name:
    description: "Module description"
    classes: ["Class1"]
    dependencies: ["dep1"]
    test_config:
      coverage_min: 85
      async_tests: true
    doc_config:
      generate_examples: true
      include_private: false
```

## Settings Options

### Global Settings
```yaml
settings:
  format_code: true        # Apply code formatting
  generate_docs: true      # Generate documentation
  check_dependencies: true # Validate dependencies
  validate_structure: true # Verify output structure
```

### Advanced Settings
```yaml
settings:
  # Code formatting
  format_code: true
  line_length: 88
  use_black: true
  use_isort: true

  # Documentation
  generate_docs: true
  doc_format: "sphinx"
  include_examples: true
  
  # Validation
  check_dependencies: true
  validate_structure: true
  strict_typing: true

  # Testing
  generate_tests: true
  min_coverage: 85
  async_test_support: true

  # Safety
  create_backups: true
  rollback_on_error: true
```

## Dependency Rules

### Basic Dependencies
```yaml
modules:
  core:
    dependencies: ["utils", "cache"]  # Core depends on utils and cache
  utils:
    dependencies: []                  # Utils has no dependencies
  cache:
    dependencies: ["utils"]          # Cache depends on utils
```

### Dependency Resolution Rules

1. **No Circular Dependencies**
   ```yaml
   # INVALID - Circular dependency
   modules:
     module_a:
       dependencies: ["module_b"]
     module_b:
       dependencies: ["module_a"]
   ```

2. **Hierarchical Dependencies**
   ```yaml
   # VALID - Clear hierarchy
   modules:
     high_level:
       dependencies: ["mid_level"]
     mid_level:
       dependencies: ["low_level"]
     low_level:
       dependencies: []
   ```

3. **Multiple Dependencies**
   ```yaml
   # VALID - Multiple dependency specification
   modules:
     complex_module:
       dependencies:
         - base
         - utils
         - helpers
     base:
       dependencies: []
     utils:
       dependencies: []
     helpers:
       dependencies: ["utils"]
   ```

## Example Configurations

### 1. Basic Web Scraper
```yaml
version: "1.0"
project_name: "SimpleScraper"
project_description: "Basic web scraping tool"

modules:
  core:
    description: "Core scraping functionality"
    classes:
      - WebScraper
      - ScraperConfig
    dependencies:
      - utils
      - http

  http:
    description: "HTTP handling"
    classes:
      - HTTPClient
      - RequestManager
    dependencies:
      - utils

  utils:
    description: "Utility functions"
    classes:
      - URLHelper
      - Logger
    dependencies: []

settings:
  format_code: true
  generate_docs: true
  check_dependencies: true
  validate_structure: true
```

### 2. Complex Data Processing System
```yaml
version: "1.0"
project_name: "DataProcessor"
project_description: "Advanced data processing pipeline"

modules:
  pipeline:
    description: "Main processing pipeline"
    classes:
      - Pipeline
      - PipelineStage
      - PipelineConfig
    dependencies:
      - processors
      - storage
      - utils

  processors:
    description: "Data processors"
    classes:
      - CSVProcessor
      - JSONProcessor
      - XMLProcessor
    dependencies:
      - utils
      - validation

  storage:
    description: "Data storage handlers"
    classes:
      - StorageManager
      - CacheManager
      - DatabaseConnector
    dependencies:
      - utils

  validation:
    description: "Data validation"
    classes:
      - Validator
      - SchemaValidator
      - DataChecker
    dependencies:
      - utils

  utils:
    description: "Utility functions"
    classes:
      - Logger
      - ConfigManager
      - ErrorHandler
    dependencies: []

settings:
  format_code: true
  generate_docs: true
  check_dependencies: true
  validate_structure: true
  strict_typing: true
  async_test_support: true
  min_coverage: 90
```

## Best Practices

1. **Module Organization**
   - Keep modules focused and single-purpose
   - Group related classes together
   - Minimize cross-module dependencies
   - Use descriptive module names

2. **Dependency Management**
   - Keep dependency chains short
   - Avoid circular dependencies
   - Use dependency injection when appropriate
   - Document dependency relationships

3. **Configuration Maintenance**
   - Use version control for configurations
   - Document configuration changes
   - Validate configurations before use
   - Keep configurations DRY (Don't Repeat Yourself)

4. **Testing and Documentation**
   - Enable test generation where possible
   - Set appropriate coverage minimums
   - Generate comprehensive documentation
   - Include examples in documentation

5. **Safety and Validation**
   - Enable code validation
   - Use strict typing when possible
   - Enable backups for safety
   - Configure appropriate error handling

---

Remember: The configuration file is the blueprint for your refactored project. Taking time to properly configure the refactoring process will result in better organized, more maintainable code.
