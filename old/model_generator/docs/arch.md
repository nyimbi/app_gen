# SQLAlchemy Model Generator Architecture Overview

## Project Context
This model generator auto-generates SQLAlchemy models from existing database schemas. It handles complex cases like circular dependencies, association tables, and custom types while providing extensive customization options through configuration.

## Core Components

### 1. Configuration System (`config/`)
Houses all configuration-related code with strong type safety and validation.

#### base_config.py
- Defines configuration dataclasses with type hints
- Implements configuration loading and validation
- Provides default values and merging capabilities
```python
@dataclass
class DatabaseConfig:
    schema: str
    exclude_tables: List[str]
    ...

@dataclass
class GenerationConfig:
    output_style: str
    indent_size: int
    ...
```

#### validators.py
- Validates configuration values
- Ensures consistency across related settings
- Provides detailed error messages
```python
class ConfigValidator:
    def validate_database_config(self)
    def validate_generation_config(self)
    def check_consistency(self)
```

#### defaults.py
- Defines system-wide default values
- Documents each default's purpose
- Provides override mechanisms

### 2. Core Engine (`core/`)
Central generation logic and coordination.

#### generator.py
Main orchestrator that:
- Coordinates the generation process
- Manages dependencies between components
- Handles errors and logging
```python
class ModelGenerator:
    def generate_models(self)
    def process_table(self)
    def handle_circular_deps(self)
```

#### introspector.py
Database schema analysis:
- Analyzes database structure
- Detects relationships
- Identifies table types (regular, association, etc.)
```python
class DatabaseIntrospector:
    def analyze_schema(self)
    def detect_relationships(self)
    def detect_association_tables(self)
```

#### writer.py
Output management:
- Handles file writing
- Manages single/multiple file output
- Formats generated code
```python
class ModelWriter:
    def write_models(self)
    def format_code(self)
    def organize_imports(self)
```

### 3. Specialized Handlers (`handlers/`)
Each handler manages a specific aspect of model generation.

#### type_handler.py
Type mapping and conversion:
- Maps database types to Python types
- Handles custom types
- Manages type imports
```python
class TypeHandler:
    def map_column_type(self)
    def resolve_custom_type(self)
    def generate_type_imports(self)
```

#### relationship_handler.py
Relationship management:
- Detects and classifies relationships
- Handles circular dependencies
- Manages back references
```python
class RelationshipHandler:
    def analyze_relationships(self)
    def detect_cycles(self)
    def generate_relationship_code(self)
```

#### security_handler.py
Security feature management:
- Handles password fields
- Manages RBAC features
- Implements security mixins
```python
class SecurityHandler:
    def handle_sensitive_fields(self)
    def generate_permission_methods(self)
    def add_security_mixins(self)
```

#### index_handler.py
Index management:
- Analyzes and generates indexes
- Handles unique constraints
- Manages composite indexes
```python
class IndexHandler:
    def analyze_indexes(self)
    def generate_index_code(self)
    def handle_unique_constraints(self)
```

#### constraint_handler.py
Constraint management:
- Handles check constraints
- Manages foreign key constraints
- Implements validation methods
```python
class ConstraintHandler:
    def analyze_constraints(self)
    def generate_constraint_code(self)
    def generate_validation_methods(self)
```

#### association_handler.py
Association table management:
- Identifies association tables
- Generates association code
- Manages many-to-many relationships
```python
class AssociationHandler:
    def identify_association_tables(self)
    def generate_association_code(self)
    def link_many_to_many(self)
```

### 4. Template System (`templates/`)
Template management and rendering.

#### manager.py
Template orchestration:
- Loads and manages templates
- Handles template inheritance
- Provides custom filters
```python
class TemplateManager:
    def load_templates(self)
    def render_template(self)
    def register_filters(self)
```

### 5. Utility Functions (`utils/`)
Common functionality used across the system.

#### case_utils.py
Case conversion utilities:
- Converts between naming conventions
- Validates identifiers
- Handles special cases
```python
def to_pascal_case(text: str) -> str
def to_snake_case(text: str) -> str
def is_valid_identifier(text: str) -> bool
```

#### string_utils.py
String manipulation:
- Handles text formatting
- Manages line length
- Implements text wrapping
```python
def wrap_text(text: str, length: int) -> str
def format_docstring(text: str) -> str
def clean_identifier(text: str) -> str
```

#### validation_utils.py
Validation utilities:
- Validates data types
- Checks constraints
- Handles error messages
```python
def validate_type(value: Any, expected_type: Type) -> bool
def check_constraints(value: Any, constraints: List[Callable]) -> List[str]
def format_error(error_type: str, details: Dict) -> str
```

### 6. Command Line Interface (`cli.py`)
Command-line interface:
- Parses arguments
- Handles commands
- Provides help and usage
```python
def main()
def parse_args()
def handle_command()
```

## Key Design Principles
1. **Modularity**: Each component has a single responsibility
2. **Extensibility**: Easy to add new features via handlers
3. **Configuration**: All behavior configurable via YAML
4. **Error Handling**: Comprehensive error handling and reporting
5. **Type Safety**: Full type hinting and runtime checking

## Flow of Execution
1. CLI parses arguments and loads configuration
2. Generator initializes components and validates config
3. Introspector analyzes database schema
4. Handlers process their specific aspects
5. Templates render the final code
6. Writer outputs the generated files

## Extension Points
1. **Custom Handlers**: Add new handlers for specific features
2. **Template Customization**: Override or extend templates
3. **Type Mapping**: Add custom type mappings
4. **Validation Rules**: Define custom validation rules
5. **Output Formats**: Implement new output formats

Would you like me to provide more details about:
1. Any specific component?
2. The interaction between components?
3. Specific implementation patterns to use?
4. Testing strategy for components?


--
