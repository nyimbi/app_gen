# Aligned Development Sequence Based on Architecture Design

## Phase 1: Project Foundation & Utilities
Based on `/utils/` in the architecture:

```
model_generator/
├── __init__.py
├── utils/
│   ├── __init__.py
│   ├── case_utils.py       # Case conversion utilities as per architecture
│   ├── string_utils.py     # String manipulation utilities
│   └── validation_utils.py # Validation utilities
```

Key implementations:
- `case_utils.py`: `to_pascal_case()`, `to_snake_case()`, `is_identifier()`
- `string_utils.py`: Text formatting and manipulation
- `validation_utils.py`: Basic validation functions

## Phase 2: Configuration System
Based on `/config/` in the architecture:

```
model_generator/config/
├── __init__.py
├── base_config.py     # Base configuration classes using dataclasses
└── validators.py      # Configuration validation
```

Key classes:
- `DatabaseConfig`
- `GenerationConfig`
- `ConfigValidator`

## Phase 3: Core Components
Based on `/core/` in the architecture:

```
model_generator/core/
├── __init__.py
├── introspector.py    # DatabaseIntrospector class
├── generator.py       # ModelGenerator class
└── writer.py         # ModelWriter class
```

Key classes as defined in architecture:
- `DatabaseIntrospector`:
  - `get_tables()`
  - `analyze_relationships()`
  - `detect_association_tables()`
- `ModelGenerator`:
  - `__init__()`
  - `generate_models()`
  - `process_table()`
- `ModelWriter`:
  - `write_single_file()`
  - `write_multiple_files()`

## Phase 4: Basic Handlers
Based on `/handlers/` in the architecture:

```
model_generator/handlers/
├── __init__.py
├── type_handler.py          # TypeHandler class
└── relationship_handler.py  # RelationshipHandler class
```

Key implementations:
- `TypeHandler`:
  - `map_type()`
  - `handle_custom_types()`
- `RelationshipHandler`:
  - `analyze_relationship()`
  - `handle_circular_dependencies()`
  - `generate_relationship_code()`

## Phase 5: Template System
Based on `/templates/` in the architecture:

```
model_generator/templates/
├── __init__.py
├── manager.py         # TemplateManager class
├── model.py.j2       # Main model template
└── imports.py.j2     # Imports template
```

Key class:
- `TemplateManager`:
  - `__init__()`
  - `render_model()`
  - `render_imports()`

## Phase 6: Additional Handlers
Additional handlers from architecture:

```
model_generator/handlers/
├── index_handler.py    # IndexHandler class from architecture
├── association_handler.py  # AssociationTableHandler from architecture
└── foreign_key_handler.py # ForeignKeyHandler from architecture
```

Key implementations:
- `IndexHandler`:
  - `analyze_indexes()`
  - `generate_index_code()`
- `AssociationTableHandler`:
  - `is_association_table()`
  - `generate_association_table()`
  - `link_association_relationships()`
- `CircularRelationshipResolver`:
  - `detect_cycles()`
  - `resolve_circular_dependencies()`

## Phase 7: Main CLI
Based on the usage example in architecture:

```python
model_generator/
└── cli.py   # Main CLI implementation
```

Key function:
```python
def main():
    # Load and validate configuration
    config_loader = ConfigLoader()
    config = config_loader.load("config.yaml")
    
    # Initialize components
    introspector = DatabaseIntrospector(config.database)
    type_handler = TypeHandler(config.types)
    relationship_handler = RelationshipHandler(config.relationships)
    template_manager = TemplateManager(config.templates)
    
    # Create main generator
    generator = ModelGenerator(
        config=config,
        introspector=introspector,
        type_handler=type_handler,
        relationship_handler=relationship_handler,
        template_manager=template_manager
    )
    
    # Generate models
    generator.generate_models()
```

## Testing Strategy

Tests should mirror the architecture's component structure:

1. Utilities:
```
tests/test_utils/
├── test_case_utils.py
├── test_string_utils.py
└── test_validation_utils.py
```

2. Core Components:
```
tests/test_core/
├── test_introspector.py
├── test_generator.py
└── test_writer.py
```

3. Handlers:
```
tests/test_handlers/
├── test_type_handler.py
├── test_relationship_handler.py
└── test_index_handler.py
```

4. Templates:
```
tests/test_templates/
├── test_manager.py
└── test_rendering.py
```

## Development Guidelines

1. Follow the architecture's class signatures exactly
2. Implement interfaces as defined in the architecture
3. Maintain the defined separation of concerns
4. Use the error handling patterns from the architecture
5. Keep the component interaction patterns as specified

Each component should be developed in this order:
1. Interfaces and base classes
2. Core functionality
3. Error handling
4. Tests
5. Documentation
