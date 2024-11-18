# SQLAlchemy Model Generator Project Structure

## Project Root
- `pyproject.toml` - Project metadata, dependencies, and build configuration
- `setup.py` - Package installation configuration
- `README.md` - Project documentation and usage instructions
- `requirements.txt` - Project dependencies
- `CHANGELOG.md` - Version history and changes
- `.gitignore` - Git ignore rules
- `LICENSE` - Project license

## Core Module (`sqlalchemy_model_generator/`)
- `__init__.py` - Package initialization and version info
- `cli.py` - Command line interface and argument parsing
- `main.py` - Main application entry point
- `exceptions.py` - Custom exception classes

### Configuration System (`sqlalchemy_model_generator/config/`)
- `__init__.py` - Configuration module initialization
- `base_config.py` - Base configuration dataclasses and loading logic
- `validators.py` - Configuration validation classes
- `defaults.py` - Default configuration values
- `types.py` - Configuration type definitions

### Core Engine (`sqlalchemy_model_generator/core/`)
- `__init__.py` - Core module initialization
- `generator.py` - Main model generation orchestrator
- `introspector.py` - Database schema analysis
- `writer.py` - Output file management and code writing
- `context.py` - Generation context management
- `registry.py` - Component and handler registry

### Handlers (`sqlalchemy_model_generator/handlers/`)
- `__init__.py` - Handler module initialization
- `base.py` - Base handler class and interfaces
- `type_handler.py` - Database type mapping and conversion
- `relationship_handler.py` - Relationship detection and generation
- `security_handler.py` - Security features and sensitive data
- `index_handler.py` - Index and constraint management
- `constraint_handler.py` - Database constraint handling
- `association_handler.py` - Association table handling
- `validator_handler.py` - Validation rules generation

### Template System (`sqlalchemy_model_generator/templates/`)
- `__init__.py` - Template module initialization
- `manager.py` - Template loading and rendering
- `filters.py` - Custom template filters
- `utils.py` - Template utility functions
- Templates:
  - `model.py.j2` - Main model template
  - `relationship.py.j2` - Relationship code template
  - `index.py.j2` - Index definition template
  - `constraint.py.j2` - Constraint definition template
  - `security.py.j2` - Security feature template
  - `validation.py.j2` - Validation code template
  - `header.py.j2` - File header template
  - `imports.py.j2` - Import statement template

### Utilities (`sqlalchemy_model_generator/utils/`)
- `__init__.py` - Utilities module initialization
- `case_utils.py` - Case conversion functions
- `string_utils.py` - String manipulation utilities
- `validation_utils.py` - Validation helper functions
- `type_utils.py` - Type handling utilities
- `file_utils.py` - File operations utilities
- `import_utils.py` - Import statement management

### Tests (`tests/`)
- `__init__.py` - Test package initialization
- `conftest.py` - pytest configuration and fixtures
- Unit Tests:
  - `test_config/` - Configuration tests
  - `test_core/` - Core engine tests
  - `test_handlers/` - Handler tests
  - `test_templates/` - Template system tests
  - `test_utils/` - Utility function tests
- Integration Tests:
  - `test_integration/` - Full system integration tests
  - `test_databases/` - Database-specific tests
- `test_data/` - Test data and fixtures

### Documentation (`docs/`)
- `conf.py` - Sphinx configuration
- `index.rst` - Documentation root
- `installation.rst` - Installation guide
- `usage.rst` - Usage documentation
- `configuration.rst` - Configuration guide
- `api/` - API documentation
- `examples/` - Example configurations and usage

## Key File Descriptions

### Core Components

1. `generator.py`
- Main orchestrator for model generation
- Coordinates handlers and manages generation flow
- Handles error conditions and logging

2. `introspector.py`
- Analyzes database schema using SQLAlchemy reflection
- Detects relationships and table types
- Builds metadata for code generation

3. `writer.py`
- Manages output file generation
- Handles code formatting and organization
- Manages file backups and overwrites

### Handlers

1. `type_handler.py`
- Maps database types to Python/SQLAlchemy types
- Handles custom type definitions
- Manages type-specific imports

2. `relationship_handler.py`
- Analyzes and classifies relationships
- Handles many-to-many, one-to-many, etc.
- Manages back references and circular dependencies

3. `security_handler.py`
- Handles sensitive field detection
- Implements security mixins
- Manages RBAC features

### Configuration

1. `base_config.py`
- Defines configuration structure
- Implements configuration loading
- Provides validation and merging

2. `validators.py`
- Validates configuration values
- Ensures consistency
- Provides error messages

### Templates

1. `model.py.j2`
- Main model class template
- Handles class definition and attributes
- Manages model documentation

2. `relationship.py.j2`
- Relationship definition template
- Manages relationship attributes
- Handles backref definitions

Each file follows these principles:
- Single Responsibility: Each file has a focused purpose
- Dependency Management: Clear import structure
- Error Handling: Comprehensive error checking
- Documentation: Detailed docstrings and comments
- Type Safety: Type hints and validation
