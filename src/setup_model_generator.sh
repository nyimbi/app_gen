#!/bin/bash

# Model Generator Project Setup Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to create a Python file with standardized header
create_py_file() {
    local file=$1
    local description=$2
    echo "Creating $file..."
    cat > "$file" << EOF
#!/usr/bin/env python3
"""
filename: $file
Author: Nyimbi Odero
Copyright: Nyimbi Odero, 2024
License: MIT
File Description: $description

This module is part of the SQLAlchemy Model Generator project.
"""

from typing import List, Dict, Any, Optional, Union, Set, Tuple
from pathlib import Path

EOF
}

# Function to create a Jinja2 template file with standardized header
create_template_file() {
    local file=$1
    local description=$2
    echo "Creating template $file..."
    cat > "$file" << EOF
{#
filename: $file
Author: Nyimbi Odero
Copyright: Nyimbi Odero, 2024
License: MIT
File Description: $description
#}

EOF
}

# Function to create YAML file with standardized header
create_yaml_file() {
    local file=$1
    local description=$2
    echo "Creating $file..."
    cat > "$file" << EOF
# filename: $file
# Author: Nyimbi Odero
# Copyright: Nyimbi Odero, 2024
# License: MIT
# File Description: $description

EOF
}

# Function to create Markdown file with standardized header
create_md_file() {
    local file=$1
    local description=$2
    echo "Creating $file..."
    cat > "$file" << EOF
<!--
filename: $file
Author: Nyimbi Odero
Copyright: Nyimbi Odero, 2024
License: MIT
File Description: $description
-->

EOF
}

echo -e "${BLUE}Creating Model Generator Project Structure...${NC}"

# Create main project directory
mkdir -p model_generator
cd model_generator

# Create main package file
create_py_file "__init__.py" "Model Generator main package initialization. Defines package version and exports main interfaces."

# Create CLI file
create_py_file "cli.py" "Command-line interface for the Model Generator. Handles argument parsing and command execution."

# Create config directory and files
mkdir -p config
cd config
create_py_file "__init__.py" "Configuration package initialization. Exports configuration classes and utilities."
create_py_file "base_config.py" "Base configuration classes using dataclasses for type-safe configuration management."
create_py_file "validators.py" "Configuration validation utilities for ensuring correct configuration values."
create_py_file "defaults.py" "Default configuration values for all configurable options."
cd ..

# Create core directory and files
mkdir -p core
cd core
create_py_file "__init__.py" "Core functionality package initialization. Exports main generator components."
create_py_file "generator.py" "Main model generation orchestration. Coordinates the entire generation process."
create_py_file "introspector.py" "Database schema introspection. Analyzes database structure and relationships."
create_py_file "writer.py" "Model file writing and organization. Handles output file generation and formatting."
cd ..

# Create handlers directory and files
mkdir -p handlers
cd handlers
create_py_file "__init__.py" "Handlers package initialization. Exports specialized component handlers."
create_py_file "type_handler.py" "Type mapping and conversion. Handles database to Python type mapping."
create_py_file "relationship_handler.py" "Relationship detection and generation. Manages model relationships."
create_py_file "security_handler.py" "Security and permissions handling. Manages model security features."
create_py_file "index_handler.py" "Index generation and management. Handles database index creation."
create_py_file "constraint_handler.py" "Database constraints handling. Manages various database constraints."
create_py_file "association_handler.py" "Association table handling. Manages many-to-many relationships."
cd ..

# Create templates directory and files
mkdir -p templates
cd templates
create_py_file "__init__.py" "Templates package initialization. Exports template management utilities."
create_py_file "manager.py" "Template management system. Handles template loading and rendering."
create_template_file "model.py.j2" "Main model template for generating SQLAlchemy models."
create_template_file "imports.py.j2" "Imports section template for model files."
create_template_file "utils.py.j2" "Utility methods template for model classes."
create_template_file "relationship.py.j2" "Relationship definitions template for model associations."
create_template_file "index.py.j2" "Index definitions template for database indexes."
create_template_file "constraint.py.j2" "Constraint definitions template for database constraints."
cd ..

# Create utils directory and files
mkdir -p utils
cd utils
create_py_file "__init__.py" "Utilities package initialization. Exports utility functions."
create_py_file "case_utils.py" "Case conversion utilities for naming convention management."
create_py_file "string_utils.py" "String manipulation utilities for text processing."
create_py_file "validation_utils.py" "Validation utilities for data verification."
create_py_file "file_utils.py" "File handling utilities for I/O operations."
cd ..

# Create tests directory and basic test files
mkdir -p tests
cd tests
create_py_file "__init__.py" "Tests package initialization. Sets up testing environment."
create_py_file "test_generator.py" "Tests for the main generator functionality."
create_py_file "test_config.py" "Tests for configuration handling and validation."
create_py_file "test_relationships.py" "Tests for relationship detection and generation."
create_py_file "test_types.py" "Tests for type mapping and conversion."
cd ..

# Create example config directory
mkdir -p examples
cd examples

# Create basic config example
create_yaml_file "config.yaml" "Basic configuration file showing common options."
cat >> "config.yaml" << EOF
database:
  schema: public
  exclude_tables: []
  include_tables: []

generation:
  output_style: single
  indent_size: 4
  template_dir: templates
EOF

# Create advanced config example
create_yaml_file "config_advanced.yaml" "Comprehensive configuration file showing all available options and features."
cat >> "config_advanced.yaml" << EOF
#######################
# Database Settings
#######################
database:
  # Schema to use (PostgreSQL specific, comment out for other databases)
  schema: public

  # Tables to exclude from generation
  exclude_tables:
    - alembic_version
    - spatial_ref_sys
    - pg_stat_statements

  # Tables to explicitly include (if empty, all tables except excluded ones will be processed)
  include_tables: []

  # Handle PostgreSQL-specific types
  postgres_array_handler: true
  postgres_json_handler: true
  postgres_geometry_handler: false

#######################
# Code Generation
#######################
generation:
  # Basic formatting
  indent_size: 4
  max_line_length: 100
  quote_char: "'"

  # Class naming
  class_case: pascal  # options: pascal, camel
  class_prefix: ""
  class_suffix: "Model"

  # Column naming
  column_case: snake  # options: snake, camel

  # Documentation
  include_comments: true
  docstring_style: google  # options: google, sphinx, numpy
  add_type_hints: true

#######################
# Model Features
#######################
features:
  # Validation
  generate_validation: true
  validation_methods:
    - basic  # null checks, type validation
    - length  # string length validation
    - range  # numeric range validation
    - custom  # custom validation methods

  # Representation
  generate_repr: true
  repr_fields:
    - name
    - title
    - code
    - email
    fallback_to_pk: true

  # Mixins
  mixins:
    audit: true  # Adds AuditMixin for timestamp tracking
    file_handler: true  # Adds FileColumn mixin for file fields
    image_handler: true  # Adds ImageColumn mixin for image fields
    searchable: true  # Adds SearchableMixin for full-text search

  # Additional Methods
  additional_methods:
    - to_dict
    - from_dict
    - clone
    - diff

#######################
# Relationships
#######################
relationships:
  # Relationship detection
  detect_one_to_one: true
  detect_back_populates: true

  # Naming conventions
  naming:
    one_to_many: "plural"  # Use plural form for one-to-many relationships
    many_to_one: "singular"  # Use singular form for many-to-one relationships
    one_to_one: "singular"  # Use singular form for one-to-one relationships

  # Self-referential relationships
  self_referential:
    parent_suffix: "_parent"
    children_suffix: "_children"

  # Relationship options
  lazy_loading: select  # options: select, joined, immediate
  enable_backref: true
  backref_suffix: "_ref"

  # Association tables
  association_tables:
    naming_pattern: "{table1}_{table2}_assoc"
    detect_automatic: true

#######################
# Custom Types
#######################
custom_types:
  # Custom type mappings
  mappings:
    email: "EmailType"
    phone: "PhoneNumberType"
    url: "URLType"
    currency: "CurrencyType"

  # Enum handling
  enum_naming: pascal
  enum_prefix: ""
  enum_suffix: "Enum"

#######################
# Security
#######################
security:
  # Password field handling
  password_fields:
    - password
    - secret
    - api_key
  password_hash_method: "generate_password_hash"

  # Role-based access control
  enable_rbac: true
  default_permissions:
    - can_list
    - can_show
    - can_add
    - can_edit
    - can_delete

#######################
# File Generation
#######################
output:
  # Output structure
  single_file: true  # If false, generates one file per model

  # File organization
  directory_structure:
    models: "app/models"
    views: "app/views"
    api: "app/api"

  # File naming
  file_naming:
    model_suffix: "_model.py"
    view_suffix: "_view.py"
    api_suffix: "_api.py"

  # Generated files
  generate_files:
    models: true
    views: true
    api: true
    tests: true

  # Template customization
  template_dir: "templates"
  custom_templates:
    model: "custom_model.j2"
    view: "custom_view.j2"
    api: "custom_api.j2"

#######################
# Testing
#######################
testing:
  # Test generation
  generate_tests: true
  test_framework: pytest  # options: pytest, unittest

  # Test coverage
  test_types:
    - unit
    - integration
    - validation

  # Test data
  generate_factories: true
  factory_framework: factory_boy  # options: factory_boy, mixer

#######################
# Logging
#######################
logging:
  level: INFO  # options: DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  output: "generator.log"
  console_output: true
EOF

cd ..

# Create requirements.txt
create_md_file "requirements.txt" "Project dependencies and version requirements."
cat >> "requirements.txt" << EOF
SQLAlchemy>=1.4.0
Jinja2>=3.0.0
PyYAML>=5.4.0
inflect>=5.3.0
pytest>=6.0.0
black>=21.0.0
mypy>=0.900
pylint>=2.8.0
EOF

# Create setup.py
create_py_file "setup.py" "Package setup configuration for installation."
cat >> "setup.py" << EOF
from setuptools import setup, find_packages

setup(
    name="sqlalchemy-model-generator",
    version="0.1.0",
    author="Nyimbi Odero",
    author_email="nyimbi@gmail.com",
    description="Advanced SQLAlchemy model generator",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'SQLAlchemy>=1.4.0',
        'Jinja2>=3.0.0',
        'PyYAML>=5.4.0',
        'inflect>=5.3.0',
    ],
    entry_points={
        'console_scripts': [
            'generate-models=model_generator.cli:main',
        ],
    },
)
EOF

# Create README.md
create_md_file "README.md" "Project documentation and usage instructions."
cat >> "README.md" << EOF
# SQLAlchemy Model Generator

Advanced SQLAlchemy model generator with support for:
- Multiple database types
- Complex relationships
- Association tables
- Custom types
- Security features
- Template customization

## Installation

\`\`\`bash
pip install -r requirements.txt
python setup.py install
\`\`\`

## Usage

\`\`\`bash
generate-models --config config.yaml --output models/
\`\`\`

## Configuration

See \`examples/config.yaml\` for a full configuration example.
EOF

# Create .gitignore
create_md_file ".gitignore" "Git ignore patterns for the project."
cat >> ".gitignore" << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
env/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Testing
.coverage
htmlcov/
.pytest_cache/

# Generated files
*.log
EOF

echo -e "${GREEN}Project structure created successfully!${NC}"
echo -e "Next steps:"
echo -e "1. Create a virtual environment: ${BLUE}python -m venv venv${NC}"
echo -e "2. Activate it: ${BLUE}source venv/bin/activate${NC}"
echo -e "3. Install dependencies: ${BLUE}pip install -r requirements.txt${NC}"
echo -e "4. Install development version: ${BLUE}pip install -e .${NC}"
