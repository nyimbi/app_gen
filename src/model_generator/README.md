# README for the AppGen Model Code Generator
### filename: README.md
### Author: Nyimbi Odero
### Copyright: Nyimbi Odero, 2024
### License: MIT
### File Description: Project documentation and usage instructions.

# AppGen Model Generator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Versions](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-blue)](https://www.python.org/downloads/)
[![SQLAlchemy](https://img.shields.io/badge/sqlalchemy-1.4%20%7C%202.0-green)](https://www.sqlalchemy.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

An advanced SQLAlchemy model generator that creates rich, feature-complete models by introspecting your database schema. Built to handle complex database structures while providing extensive customization options.

## Features

### Database Support
- **Multiple Database Types**: Support for PostgreSQL, MySQL, SQLite, and Oracle
- **Schema Introspection**: Accurate analysis of database structure
- **Type Mapping**: Intelligent mapping of database types to Python types

### Relationship Handling
- **Automatic Detection**: Smart detection of relationships from foreign keys
- **Association Tables**: Proper handling of many-to-many relationships
- **Self-Referential**: Support for hierarchical and self-referential relationships
- **Circular Dependencies**: Intelligent handling of circular relationships

### Advanced Features
- **Custom Types**: Support for custom column types and type mapping
- **Validation**: Automatic generation of validation methods
- **Security**: Built-in security features and permission handling
- **Mixins**: Automatic inclusion of appropriate mixins based on table structure

### Code Quality
- **Type Hints**: Comprehensive type annotations
- **Documentation**: Detailed docstrings in multiple formats (Google, Sphinx, NumPy)
- **Code Style**: Adherence to PEP 8 and modern Python practices
- **Testing**: Automatic test generation for models

### Customization
- **Templates**: Customizable Jinja2 templates for all generated code
- **Output Format**: Single file or file-per-model output options
- **Naming Conventions**: Configurable naming strategies
- **Code Style**: Adjustable formatting preferences

## Installation

### From PyPI
```bash
pip install sqlalchemy-model-generator
```

### From Source
```bash
git clone https://github.com/username/sqlalchemy-model-generator.git
cd sqlalchemy-model-generator
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

## Quick Start

1. Create a basic configuration file (config.yaml):
```yaml
database:
  schema: public
  exclude_tables: []
  include_tables: []

generation:
  output_style: single
  indent_size: 4
  template_dir: templates
```

2. Generate models:
```bash
generate-models --config config.yaml --output models/
```

## Advanced Usage

### Configuration Options

The generator supports extensive configuration through YAML files. See examples/config_advanced.yaml for a full example with all options.

Key configuration sections:

```yaml
database:
  schema: public
  exclude_tables:
    - alembic_version
  postgres_array_handler: true

generation:
  class_case: pascal
  docstring_style: google
  add_type_hints: true

relationships:
  detect_one_to_one: true
  lazy_loading: select

security:
  enable_rbac: true
  password_fields:
    - password
    - secret
```

### Custom Type Mapping

Define custom type mappings for specific column patterns:

```yaml
custom_types:
  mappings:
    email: "EmailType"
    phone: "PhoneNumberType"
    url: "URLType"
    currency: "CurrencyType"
```

### Template Customization

Provide your own Jinja2 templates for complete control over generated code:

```yaml
output:
  template_dir: "my_templates"
  custom_templates:
    model: "custom_model.j2"
    view: "custom_view.j2"
```

## Model Features

### Generated Model Example

```python
class User(Model, AuditMixin):
    """
    User model representing the 'users' table.

    Attributes:
        id (int): Primary key
        email (EmailType): User's email address
        name (str): User's full name
        created_at (datetime): Timestamp of creation
        posts (List[Post]): Related blog posts
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(EmailType, nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    posts = relationship('Post', back_populates='author')

    def validate(self) -> List[str]:
        """Validates the model instance."""
        errors = []
        if not self.email:
            errors.append('Email is required')
        if not self.name:
            errors.append('Name is required')
        return errors
```

### Association Table Handling

```python
post_tags = Table(
    'post_tags',
    Model.metadata,
    Column('post_id', Integer, ForeignKey('posts.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

class Post(Model):
    __tablename__ = 'posts'
    tags = relationship('Tag', secondary=post_tags, back_populates='posts')
```

## Testing

Run the test suite:

```bash
pytest tests/
```

Generate test coverage report:

```bash
pytest --cov=model_generator tests/
```

## Contributing

Contributions are welcome! Please see our Contributing Guide for details.

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Documentation

Full documentation is available at [readthedocs.io](https://sqlalchemy-model-generator.readthedocs.io/).

### Building Documentation

```bash
cd docs
make html
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

Created by Nyimbi Odero. Copyright © 2024.

## Support

- Issue Tracker: GitHub Issues
- Documentation: [readthedocs.io](https://sqlalchemy-model-generator.readthedocs.io/)
- Email: nyimbi@gmail.com

## Project Status

The project is actively maintained and accepting contributions.
