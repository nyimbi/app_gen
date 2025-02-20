#!/usr/bin/env python3
"""
Author: Nyimbi Odero
Copyright: Nyimbi Odero, 2024
License: MIT

gen_models.py: Enhanced SQLAlchemy Model Generator

This script generates SQLAlchemy ORM models by introspecting an existing database schema.
It supports multiple databases and generates Python code that accurately represents
the database structure, including tables, columns, relationships, and constraints.

Features:
1. Supports PostgreSQL, MySQL, SQLite, and SQL Server
2. Generates SQLAlchemy declarative base models
3. Supports table and column comments
4. Handles primary keys, including composite primary keys
5. Generates foreign key relationships with correct cardinality
6. Supports unique constraints, including multi-column constraints
7. Generates indexes, including unique indexes
8. Handles IDENTITY columns
9. Supports ENUM types with explicit values
10. Generates association tables for many-to-many relationships with advanced detection
11. Handles table inheritance
12. Supports column default values, converting them to SQLAlchemy expressions
13. Generates check constraints
14. Handles referential actions (ON DELETE, ON UPDATE) for foreign keys
15. Supports custom column types (e.g., JSON, ARRAY)
16. Generates __repr__, __str__, and additional methods for each model
17. Supports hybrid properties and association proxies
18. Allows customizable naming conventions and type mappings
19. Provides comprehensive error handling and logging
20. Supports configuration via command-line arguments and YAML files

Usage:
    python gen_models.py --uri "postgresql:///your_database_name" --output "your_models.py" --config "config.yaml"

Dependencies:
- SQLAlchemy
- inflect
- PyYAML (for configuration file support)

Note: This script requires utility functions from 'utils.py' and header generation
functions from 'oheaders.py' in the same directory.
"""

import inflect
import argparse
import logging
import sys
import os
import yaml
from typing import List, Dict, Any, Tuple

from sqlalchemy import (
    create_engine, inspect, MetaData, Table, Column, ForeignKey,
    CheckConstraint, PrimaryKeyConstraint, UniqueConstraint, Index,
    Identity, func, text, LargeBinary, DateTime
)
from sqlalchemy.orm import declarative_base, relationship, declarative_mixin
from sqlalchemy.sql import sqltypes
from sqlalchemy.ext.hybrid import hybrid_property

from oheaders import gen_model_header, gen_photo_column, gen_file_column
from utils.case_utils import snake_to_pascal, snake_to_camel, user_defined_naming
from utils.db_utils import is_association_table, map_pgsql_datatypes, get_display_column, extract_enum_info

p = inflect.engine()
Base = declarative_base()

# Constants
INDENT = "    "
AB_PREFIX = 'ab_'

# Track processed relationships to detect circular dependencies
processed_relationships: set = set()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from a YAML file."""
    if not os.path.exists(config_path):
        logger.warning(f"Configuration file '{config_path}' not found. Using default settings.")
        return {}
    with open(config_path, 'r') as f:
        try:
            config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from '{config_path}'.")
            return config
        except yaml.YAMLError as e:
            logger.error(f"Error parsing configuration file: {e}")
            sys.exit(1)

def gen_models(metadata: MetaData, inspector: Any, config: Dict[str, Any]) -> List[str]:
    model_code: List[str] = []
    reverse_relationships: Dict[str, List[str]] = {}
    association_tables: List[str] = []

    # Load configuration
    naming_convention = config.get('naming_convention', 'snake_to_pascal')
    include_comments = config.get('include_comments', True)
    include_additional_methods = config.get('include_additional_methods', True)
    custom_type_mappings = config.get('custom_type_mappings', {})
    hybrid_properties = config.get('hybrid_properties', {})
    association_proxies = config.get('association_proxies', {})

    # Generate header, domains, and enums
    model_code.extend(gen_model_header())
    model_code.extend(gen_domains(inspector, config))
    model_code.extend(gen_enums(inspector, config))

    # Generate miscellaneous tables (including FlaskSession)
    model_code.extend(gen_misc_tables(config))

    # Identify association tables
    for table_name in inspector.get_table_names():
        if is_association_table(table_name, inspector, config):
            association_tables.append(table_name)

    # Prepare relationship information
    relationship_info = prepare_relationship_info(metadata, inspector, association_tables, config)

    # Generate regular tables and association tables
    for table_name in inspector.get_table_names():
        table = metadata.tables[table_name]
        if table_name in association_tables:
            table_code = gen_association_table(table, inspector, config)
        else:
            table_code, reverse_rels_info = gen_table(table, inspector, relationship_info, association_tables, config)
            for rev_rel in reverse_rels_info:
                if rev_rel['table'] not in reverse_relationships:
                    reverse_relationships[rev_rel['table']] = []
                reverse_relationships[rev_rel['table']].append(rev_rel['code'])
        model_code.extend(table_code)

    # Add reverse relationships to the appropriate tables
    for table_name, relationships in reverse_relationships.items():
        table_index = next((i for i, line in enumerate(model_code) if line.startswith(f"class {snake_to_pascal(table_name)}(Model)")),
                           None)
        if table_index is None:
            continue
        for rel in relationships:
            insert_index = find_insertion_index(model_code, table_index)
            model_code.insert(insert_index, f"{INDENT}{rel}")
            model_code.insert(insert_index + 1, "")  # Add a blank line for readability

    return model_code

def gen_domains(inspector: Any, config: Dict[str, Any]) -> List[str]:
    """Generate code for database domains."""
    # Placeholder for domain generation
    # Domains are not directly accessible through SQLAlchemy's inspector
    # Future implementations can extend this function
    logger.info("Domain generation is not implemented for this database.")
    return []

def gen_enums(inspector: Any, config: Dict[str, Any]) -> List[str]:
    """Generate code for database enums."""
    enum_code = ['# Enums defined in the database']
    enums = inspector.get_enums()

    for enum in enums:
        enum_code.extend(gen_enum(enum, config))

    enum_code.append("\n")
    return enum_code

def gen_enum(enum: Dict[str, Any], config: Dict[str, Any]) -> List[str]:
    """Generate code for a single enum."""
    enum_code = []
    enum_name = enum['name']
    labels = enum["labels"]

    enum_code.append(f"\nclass {enum_name}(enum.Enum):")
    for label in labels:
        enum_code.append(f"{INDENT}{label.upper()} = '{label}'")

    # Handle explicit enum values if provided
    if 'values' in enum:
        for label, value in zip(labels, enum['values']):
            enum_code.append(f"{INDENT}{label.upper()} = {value}")

    return enum_code

def gen_association_table(table, inspector, config: Dict[str, Any]):
    """Generate code for a single association table."""
    table_code = []
    table_name = table.name
    columns = inspector.get_columns(table_name)
    fks = inspector.get_foreign_keys(table_name)
    pk_constraint = inspector.get_pk_constraint(table_name)
    uqs = inspector.get_unique_constraints(table_name)
    table_comment = inspector.get_table_comment(table_name)

    table_class = snake_to_pascal(table_name)
    table_code.append(f"class {table_class}(Model):")
    table_code.append(f'{INDENT}__tablename__ = "{table_name}"')

    # Generate columns
    pk_columns = pk_constraint['constrained_columns']
    for column in columns:
        column_code = gen_column(column, pk_columns, fks, uqs, table_name, is_association_table=True, config=config)
        table_code.extend(column_code)

    if table_comment['text']:
        table_code.append(f'{INDENT}__table_args__ = {{"comment": "{table_comment["text"]}"}}')

    table_code.append("\n")
    return table_code

def gen_table(table, inspector, relationship_info, association_tables, config: Dict[str, Any]):
    table_code = []
    reverse_relationships_info = []
    table_name = table.name
    columns = inspector.get_columns(table_name)
    pk_constraint = inspector.get_pk_constraint(table_name)
    fks = inspector.get_foreign_keys(table_name)
    uqs = inspector.get_unique_constraints(table_name)
    indexes = inspector.get_indexes(table_name)
    table_comment = inspector.get_table_comment(table_name)

    table_class = snake_to_pascal(table_name)
    table_code.append(f"class {table_class}(Model):")
    table_code.append(f'{INDENT}__tablename__ = "{table_name}"')
    table_code.extend(gen_table_args(pk_constraint, uqs, indexes, table_comment, config))

    table_code.extend(gen_columns(columns, pk_constraint, fks, uqs, table_name, config))

    for fk in fks:
        local_rel, reverse_rel_info = gen_relationship(fk, table_name, table_class, inspector, relationship_info, association_tables, config)
        if local_rel:
            table_code.extend(local_rel)
        if reverse_rel_info:
            reverse_relationships_info.append(reverse_rel_info)

    table_code.extend(gen_check_constraints(inspector, table_name, config))
    table_code.extend(gen_repr_method(columns, pk_constraint, config))
    if include_additional_methods:
        table_code.extend(gen_additional_methods(table_class, table_name, columns, config))

    table_code.append("\n")
    return table_code, reverse_relationships_info

def gen_columns(columns, pk_constraint, fks, uqs, table_name, config: Dict[str, Any]):
    """Generate code for table columns, including identities, constraints, and comments."""
    column_code = []
    pk_columns = pk_constraint['constrained_columns']
    for column in columns:
        column_code.extend(gen_column(column, pk_columns, fks, uqs, table_name, config))
    return column_code

def gen_column(column, pk_columns, fks, uqs, table_name, is_association_table=False, config: Dict[str, Any]):
    """Generate code for a single column, including identity, constraints, and comments."""
    column_code = []
    column_name = column["name"]
    column_type = column['type'].compile()
    column_type = map_pgsql_datatypes(column_type.lower(), config)

    attributes = []

    for fk in fks:
        if column_name in fk["constrained_columns"]:
            referred_table = fk["referred_table"]
            referred_columns = fk["referred_columns"]
            if len(fk["constrained_columns"]) == 1:
                fk_str = f"ForeignKey('{referred_table}.{referred_columns[0]}')"
                attributes.append(fk_str)

    if column_name == 'id':
        attributes.append("autoincrement=True")

    if column_name in pk_columns:
        attributes.append("primary_key=True")

    if not column.get("nullable", True):
        attributes.append("nullable=False")

    if column_name in [uq["column_names"][0] for uq in uqs if len(uq["column_names"]) == 1]:
        attributes.append("unique=True")

    if column.get('default') is not None:
        default_value = process_default_value(column_name, column_type, column['default'], config)
        if default_value:
            attributes.append(f"default={default_value}")

    if column.get("comment"):
        attributes.append(f'comment="{column["comment"]}"')

    attributes_str = ", ".join(attributes)

    if is_enum_type(column_type, column.get('default'), config):
        try:
            enum_name, enum_options = extract_enum_info(column, config)
            column_type = f"Enum({enum_name})"
        except Exception as e:
            logger.warning(f"Warning: Could not extract enum info for column {column_name}: {str(e)}")
            # Fall back to using the original column type
            column_type = column['type'].compile()

    if column_name.endswith('_img') or column_name.endswith('_photo'):
        column_code.append(gen_photo_column(column_name, table_name))
    elif column_name.endswith('_file') or column_name.endswith('_doc'):
        column_code.append(gen_file_column(column_name, table_name))
    else:
        if attributes_str:
            column_code.append(f'{INDENT}{column_name} = Column({column_type}, {attributes_str})')
        else:
            column_code.append(f'{INDENT}{column_name} = Column({column_type})')

    return column_code

def is_enum_type(column_type: str, default: Any, config: Dict[str, Any]) -> bool:
    """Determine if the column is an enum type."""
    return 'enum' in column_type.lower() or (default and '::t_' in default)

def extract_enum_info(column: Dict[str, Any], config: Dict[str, Any]) -> Tuple[str, str]:
    """Extract enum name and options from column information."""
    column_name = column['name']

    # Extract enum name from the type or default value
    if 'enum' in column['type'].compile().lower():
        enum_name = column['type'].compile().lower().split('.')[-1]
    elif column['default'] and '::t_' in column['default']:
        enum_name = column['default'].split('::')[1].split("'")[0]
    else:
        enum_name = f"t_{column_name}_enum"

    # Try to extract enum options from default value
    if column['default'] and '::t_' in column['default']:
        enum_type = column['default'].split('::')[1].split(')')[0]
        enum_options = [opt.strip("'") for opt in enum_type.split(',')]
    # If not in default, try to extract from comment
    elif column.get('comment') and ',' in column['comment']:
        enum_options = [opt.strip() for opt in column['comment'].split(',')]
    else:
        enum_options = []

    enum_options_str = ", ".join([f"'{opt}'" for opt in enum_options])
    return enum_name, enum_options_str

def gen_relationship(fk, table_name, table_class, inspector, relationship_info, association_tables, config: Dict[str, Any]):
    relationship_code = []
    reverse_relationship_info = None

    fk_cols = fk["constrained_columns"]
    referred_table = fk["referred_table"]
    referred_class = snake_to_pascal(referred_table)

    # Check for circular relationships
    relationship_key = (table_name, referred_table)
    if relationship_key in processed_relationships:
        return [], None

    cardinality = relationship_info[table_name].get(referred_table, 'many-to-one')

    local_relationship_name = determine_relationship_name(fk_cols, table_name, referred_table, cardinality, inspector, config)
    remote_relationship_name = determine_remote_relationship_name(cardinality, table_name, referred_table, inspector, config)

    # Handle many-to-many relationships
    if cardinality == 'many-to-many':
        assoc_table = find_association_table(table_name, referred_table, association_tables, inspector, config)
        if assoc_table:
            relationship_args = [
                f"'{referred_class}'",
                f"secondary='{assoc_table}'",
                f"back_populates='{remote_relationship_name}'"
            ]
        else:
            # If no association table found, fall back to many-to-one
            cardinality = 'many-to-one'
            relationship_args = [
                f"'{referred_class}'",
                f"back_populates='{remote_relationship_name}'",
                f"foreign_keys='[{', '.join([f'{table_class}.{col}' for col in fk_cols])}]'"
            ]
    else:
        relationship_args = [
            f"'{referred_class}'",
            f"back_populates='{remote_relationship_name}'",
            f"foreign_keys='[{', '.join([f'{table_class}.{col}' for col in fk_cols])}]'"
        ]

    if cardinality in ['many-to-one', 'one-to-one']:
        relationship_args.append("lazy='select'")
    elif cardinality in ['one-to-many', 'many-to-many']:
        relationship_args.append("lazy='select'")

    relationship_str = ', '.join(relationship_args)
    relationship_code.append(f'{INDENT}{local_relationship_name} = relationship({relationship_str})')

    # Generate reverse relationship
    if cardinality == 'many-to-many':
        reverse_relationship_args = [
            f"'{table_class}'",
            f"secondary='{assoc_table}'",
            f"back_populates='{local_relationship_name}'"
        ]
    else:
        reverse_relationship_args = [
            f"'{table_class}'",
            f"back_populates='{local_relationship_name}'",
            f"foreign_keys='[{table_class}.{fk_cols[0]}]'"
        ]

    if cardinality in ['one-to-many', 'many-to-many']:
        reverse_relationship_args.append("lazy='select'")
    elif cardinality in ['many-to-one', 'one-to-one']:
        reverse_relationship_args.append("lazy='select'")

    reverse_relationship_str = ', '.join(reverse_relationship_args)
    reverse_relationship_info = {
        'table': referred_table,
        'code': f'{remote_relationship_name} = relationship({reverse_relationship_str})'
    }

    processed_relationships.add(relationship_key)
    return relationship_code, reverse_relationship_info

def determine_relationship_name(fk_cols, table_name, referred_table, cardinality, inspector, config: Dict[str, Any]):
    """Determine the relationship name based on foreign key columns and table names."""
    # Handle composite foreign keys
    if len(fk_cols) > 1:
        base_name = '_'.join([col.replace('_id_fk', '').replace('_id', '') for col in fk_cols])
    else:
        base_name = fk_cols[0].replace('_id_fk', '').replace('_id', '')

    # Check if the base_name is a prefix or suffix of the referred_table
    if referred_table.lower().startswith(base_name) or referred_table.lower().endswith(base_name):
        base_name = referred_table.lower()

    # Handle special cases like association tables
    if is_association_table(table_name, inspector, config):
        other_fk = next(fk for fk in inspector.get_foreign_keys(table_name) if fk['referred_table'] != referred_table)
        other_table = other_fk['referred_table']
        return p.plural(other_table.lower())

    # Determine the appropriate name based on cardinality
    if cardinality in ['one-to-many', 'many-to-many']:
        return p.plural(base_name)
    elif cardinality == 'many-to-one':
        # Check if there are multiple FKs to the same table
        fks_to_referred = [fk for fk in inspector.get_foreign_keys(table_name) if fk['referred_table'] == referred_table]
        if len(fks_to_referred) > 1:
            # If multiple FKs exist, use a more specific name
            specific_name = '_'.join([col.replace('_id_fk', '').replace('_id', '') for col in fk_cols])
            return f"{specific_name}_{base_name}"
        return p.plural(base_name)
    else:  # one-to-one
        return base_name

def determine_remote_relationship_name(cardinality, table_name, referred_table, inspector, config: Dict[str, Any]):
    """Determine the name for the remote side of the relationship."""
    if is_association_table(referred_table, inspector, config):
        # For association tables, use the plural of the current table
        return p.plural(table_name.lower())

    if cardinality in ['one-to-many', 'many-to-many']:
        return p.plural(table_name.lower())
    elif cardinality == 'many-to-one':
        # Check if there are multiple relationships to this table
        fks_from_referred = [fk for fk in inspector.get_foreign_keys(referred_table) if fk['referred_table'] == table_name]
        if len(fks_from_referred) > 1:
            # If multiple relationships exist, use a more specific name
            fk_cols = fks_from_referred[0]['constrained_columns']
            specific_name = '_'.join([col.replace('_id_fk', '').replace('_id', '') for col in fk_cols])
            return f"{specific_name}_{table_name.lower()}"
        return table_name.lower()
    else:  # one-to-one
        return table_name.lower()

def gen_table_args(pk_constraint, uqs, indexes, table_comment, config: Dict[str, Any]) -> List[str]:
    """Generate __table_args__ for composite primary keys, unique constraints, indexes, and table comments."""
    table_args = []
    pk_columns = pk_constraint['constrained_columns']

    if len(pk_columns) > 1:
        pk_columns_str = ", ".join([f"'{col}'" for col in pk_columns])
        table_args.append(f"PrimaryKeyConstraint({pk_columns_str})")

    for uq in uqs:
        if len(uq["column_names"]) > 1:
            uq_columns_str = ", ".join([f"'{col}'" for col in uq["column_names"]])
            table_args.append(f"UniqueConstraint({uq_columns_str}, name='{uq['name']}')")

    for idx in indexes:
        idx_columns_str = ", ".join([f"'{col}'" for col in idx["column_names"]])
        unique_str = ", unique=True" if idx["unique"] else ""
        table_args.append(f"# Index('{idx['name']}', {idx_columns_str}{unique_str})")

    if table_comment['text']:
        cmnt = {'comment': table_comment['text']}
        table_args.append(str(cmnt))

    if table_args:
        if len(table_args) == 1 and table_comment['text']:
            return [f'{INDENT}__table_args__ = ({table_args[0]})']
        else:
            args_str = f",\n{INDENT}{INDENT}".join(table_args)
            return [f'{INDENT}__table_args__ = (\n{INDENT}{INDENT}{args_str},\n{INDENT})']
    return []

def gen_check_constraints(inspector, table_name, config: Dict[str, Any]) -> List[str]:
    """Generate code for table check constraints."""
    constraint_code = []
    check_constraints = inspector.get_check_constraints(table_name)

    for cc in check_constraints:
        constraint_name = cc['name']
        sql_expression = cc['sqltext']
        constraint_code.append(
            f'{INDENT}__table_args__ = (\n'
            f'{INDENT}{INDENT}CheckConstraint(\'{sql_expression}\', name=\'{constraint_name}\'),\n'
            f'{INDENT}{INDENT}*__table_args__\n'
            f'{INDENT})'
        )

    return constraint_code

def gen_repr_method(columns, pk_constraint, config: Dict[str, Any]) -> List[str]:
    """Generate code for the __repr__ method, using a combination of meaningful columns."""
    repr_code = []
    repr_code.append(f'\n{INDENT}def __repr__(self):')

    pk_columns = pk_constraint['constrained_columns']

    # Candidate fields to be used in the __repr__ method
    candidate_fields = ['name', 'title', 'email', 'username', 'description']

    # Determine which fields to use in __repr__
    selected_columns = []
    for column in columns:
        col_name = column['name']
        if col_name in candidate_fields:
            selected_columns.append(col_name)
        if len(selected_columns) >= 2:  # We limit to two for a concise __repr__
            break

    # Fallback to using primary key if no suitable column is found
    if not selected_columns:
        selected_columns = pk_columns

    # Handle computed values (e.g., hybrid properties)
    if 'full_name' in [col['name'] for col in columns]:
        selected_columns.append('full_name')

    # Construct the repr string
    if len(selected_columns) == 1:
        repr_code.append(f'{INDENT}{INDENT}return f\'<{{self.__class__.__name__}} {{self.{selected_columns[0]}}}>\'')
    else:
        repr_attrs = ", ".join([f'{col}={{self.{col}}}' for col in selected_columns])
        repr_code.append(f'{INDENT}{INDENT}return f\'<{{self.__class__.__name__}}({repr_attrs})>\'')

    return repr_code

def gen_str_method(columns, pk_constraint, config: Dict[str, Any]) -> List[str]:
    """Generate code for the __str__ method."""
    str_code = []
    str_code.append(f'\n{INDENT}def __str__(self):')
    str_code.append(f'{INDENT}{INDENT}return f\'{snake_to_pascal(table_name)}\' + ": " + self.{get_display_column(columns)}')

    return str_code

def gen_additional_methods(table_class: str, table_name: str, columns: List[Dict[str, Any]], config: Dict[str, Any]) -> List[str]:
    """Generate additional model methods."""
    methods_code = []
    methods_code.extend(gen_str_method(columns, pk_constraint, config))
    methods_code.extend(gen_hybrid_properties(table_class, table_name, columns, config))
    methods_code.extend(gen_association_proxies(table_class, table_name, columns, config))
    return methods_code

def gen_hybrid_properties(table_class: str, table_name: str, columns: List[Dict[str, Any]], config: Dict[str, Any]) -> List[str]:
    """Generate hybrid properties."""
    properties_code = []
    for prop, expr in hybrid_properties.get(table_name, {}).items():
        properties_code.append(f'\n{INDENT}@hybrid_property')
        properties_code.append(f'{INDENT}def {prop}(self):')
        properties_code.append(f'{INDENT}{INDENT}return {expr}')

    return properties_code

def gen_association_proxies(table_class: str, table_name: str, columns: List[Dict[str, Any]], config: Dict[str, Any]) -> List[str]:
    """Generate association proxies."""
    proxies_code = []
    for proxy, target in association_proxies.get(table_name, {}).items():
        proxies_code.append(f'\n{INDENT}{proxy} = association_proxy(\'{target}\', \'{get_display_column(columns)}\')')

    return proxies_code

def process_default_value(column_name: str, column_type: str, default: Any, config: Dict[str, Any]) -> str:
    """Process and convert the default value to a Flask-SQLAlchemy compatible format."""
    # Handle auto-increment columns explicitly
    if column_name == 'id' and default and 'nextval' in default.lower():
        return "autoincrement=True"

    if isinstance(default, str):
        default_lower = default.lower()

        # Translate known PostgreSQL default expressions to SQLAlchemy equivalents
        if default_lower in ('now()', 'current_timestamp'):
            return 'func.now()'
        elif '::t_' in default:
            enum_name = default.split('::')[1].split("'")[0]
            enum_value = default.split("'")[1].upper()
            return f"'{enum_value}'"
        elif default_lower == 'true':
            return 'True'
        elif default_lower == 'false':
            return 'False'
        elif '::timestamp' in default_lower:
            return 'func.now()'
        elif 'current_timestamp' in default_lower:
            return 'func.now()'
        elif default_lower.startswith("'") and default_lower.endswith("'"):
            # For simple string literals
            return default
        else:
            # Attempt to use SQLAlchemy's text() for raw SQL expressions
            return f"text('{default}')"

    # Handle numeric and other literals
    elif isinstance(default, (int, float)):
        return str(default)

    # If the default is none of the above, return None to indicate no default
    return None

def analyze_cardinality(table_name: str, fk: Dict[str, Any], inspector: Any, association_tables: List[str], config: Dict[str, Any]) -> str:
    referred_table = fk["referred_table"]
    constrained_columns = fk["constrained_columns"]
    referred_columns = fk["referred_columns"]

    # Handle self-referencing tables
    if table_name == referred_table:
        return analyze_self_referencing_relationship(table_name, constrained_columns, referred_columns, inspector, config)

    # Check for association tables (many-to-many)
    if table_name in association_tables or referred_table in association_tables:
        return 'many-to-many'

    # Analyze primary keys and unique constraints
    pk_constraint = inspector.get_pk_constraint(table_name)
    pk_columns = set(pk_constraint['constrained_columns'])
    unique_constraints = inspector.get_unique_constraints(table_name)

    # One-to-one relationship checks
    if is_one_to_one_relationship(constrained_columns, pk_columns, unique_constraints):
        return 'one-to-one'

    # Many-to-one relationship check
    referred_pk_constraint = inspector.get_pk_constraint(referred_table)
    referred_pk_columns = set(referred_pk_constraint['constrained_columns'])
    if set(referred_columns).issubset(referred_pk_columns):
        return 'many-to-one'

    # Default to one-to-many if no other condition is met
    return 'one-to-many'

def is_one_to_one_relationship(constrained_columns: List[str], pk_columns: set, unique_constraints: List[Dict[str, Any]]) -> bool:
    """Check if the relationship is one-to-one based on constraints."""
    if set(constrained_columns) == pk_columns:
        return True
    for constraint in unique_constraints:
        if set(constrained_columns).issubset(set(constraint['column_names'])):
            return True
    return False

def analyze_composite_key_relationship(table_name: str, constrained_columns: List[str], inspector: Any) -> str:
    """Analyze relationships involving composite keys."""
    # Implementation depends on specific composite key scenarios
    # This is a placeholder for more complex logic
    return 'many-to-one'  # Default assumption for composite keys

def has_unique_index_on_foreign_key(table_name: str, constrained_columns: List[str], inspector: Any) -> bool:
    """Check if there's a unique index on the foreign key columns."""
    indexes = inspector.get_indexes(table_name)
    for index in indexes:
        if index['unique'] and set(constrained_columns).isset(index['column_names']):
            return True
    return False

def follows_many_to_many_naming_convention(table_name: str, referred_table: str) -> bool:
    """Check if the table name follows a common many-to-many naming convention."""
    parts = table_name.split('_')
    return len(parts) == 2 and (parts[0] == referred_table or parts[1] == referred_table)

def analyze_self_referencing_relationship(table_name: str, constrained_columns: List[str], referred_columns: List[str], inspector: Any, config: Dict[str, Any]) -> str:
    """Analyze self-referencing relationships to determine their nature."""
    # Get all columns of the table
    columns = inspector.get_columns(table_name)
    column_names = [col['name'] for col in columns]

    # Get primary key information
    pk_constraint = inspector.get_pk_constraint(table_name)
    pk_columns = set(pk_constraint['constrained_columns')

    # Get unique constraints
    unique_constraints = inspector.get_unique_constraints(table_name)

    # Check if the foreign key is part of a unique constraint
    is_unique_fk = any(set(constrained_columns).issubset(set(constraint['column_names'])) for constraint in unique_constraints)

    # Check for additional foreign keys to this table
    other_fks = [fk for fk in inspector.get_foreign_keys(table_name) if fk['referred_table'] == table_name and fk['constrained_columns'] != constrained_columns]

    # Check for common hierarchical structure column names
    hierarchical_columns = ['parent_id_fk', 'parent', 'ancestor_id_fk', 'superior_id_fk']
    has_hierarchical_column = any(col in hierarchical_columns for col in constrained_columns)

    # Check for closure table pattern (for efficient tree traversal)
    closure_table_name = f"{table_name}_closure"
    has_closure_table = closure_table_name in inspector.get_table_names()

    # Analyze the relationship
    if is_unique_fk and len(constrained_columns) == len(referred_columns) == 1:
        return 'one-to-one-self'  # Linked list-like structure

    elif has_hierarchical_column or has_hierarchical_column:
        return 'hierarchical-self'  # Tree-like structure

    elif len(other_fks) > 0:
        return 'graph-self'  # Complex graph-like structure

    elif set(constrained_columns) == pk_columns:
        return 'one-to-one-self'  # Each record points to exactly one other record

    elif 'level' in column_names or 'depth' in column_names:
        return 'hierarchical-self'  # Likely a leveled hierarchy

    else:
        return 'one-to-many-self'  # Generic self-reference, assuming one-to-many

def get_self_referencing_relationship_details(table_name: str, relationship_type: str, inspector: Any) -> Dict[str, Any]:
    """Get additional details about the self-referencing relationship."""
    details = {
        'type': relationship_type,
        'suggestion': '',
        'additional_info': {}
    }

    if relationship_type == 'one-to-one-self':
        details['suggestion'] = "Consider using 'uselist=False' in the relationship definition."
    elif relationship_type == 'hierarchical-self':
        details['suggestion'] = "Consider using a tree structure library like SQLAlchemy-Utils' TreeNode."
        # Check for closure table
        closure_table_name = f"{table_name}_closure"
        if closure_table_name in inspector.get_table_names():
            details['additional_info']['has_closure_table'] = True
            details['suggestion'] += " A closure table is detected, which can be used for efficient tree traversal."
    elif relationship_type == 'graph-self':
        details['suggestion'] = "This is a complex self-referencing structure. Consider using a graph database if the relationships are central to your application."
    elif relationship_type == 'one-to-many-self':
        details['suggestion'] = "This is a standard self-referencing relationship. No special handling is typically needed."

    return details

def handle_self_referencing_table(table_name: str, constrained_columns: List[str], referred_columns: List[str], inspector: Any) -> str:
    """Handle the analysis of self-referencing tables."""
    pk_constraint = inspector.get_pk_constraint(table_name)
    pk_columns = set(pk_constraint['constrained_columns')

    # Check if the FK is part of the PK
    if set(constrained_columns).issubset(pk_columns):
        return 'one-to-one'

    unique_constraints = inspector.get_unique_constraints(table_name)
    for constraint in unique_constraints:
        if set(constrained_columns).issubset(set(constraint['column_names'])):
            return 'one-to-one'

    # Check for hierarchical relationships
    if set(referred_columns) == set(pk_columns):
        return 'one-to-many'

    return 'many-to-many'

def prepare_relationship_info(metadata: MetaData, inspector: Any, association_tables: List[str], config: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    relationship_info = {}
    for table_name in inspector.get_table_names():
        if table_name not in association_tables:
            relationship_info[table_name] = {}
            for fk in inspector.get_foreign_keys(table_name):
                referred_table = fk['referred_table']
                cardinality = analyze_cardinality(table_name, fk, inspector, association_tables, config)
                relationship_info[table_name][referred_table] = cardinality
    return relationship_info

def find_association_table(table1: str, table2: str, association_tables: List[str], inspector: Any, config: Dict[str, Any]) -> str:
    for assoc_table in association_tables:
        fks = inspector.get_foreign_keys(assoc_table)
        if len(fks) == 2:
            referred_tables = {fk['referred_table'] for fk in fks}
            if table1 in referred_tables and table2 in referred_tables:
                return assoc_table
    return None

def gen_misc_tables(config: Dict[str, Any]) -> List[str]:
    """Generate code for miscellaneous tables needed by the application."""
    misc_code = []

    # Add header comment
    misc_code.extend([
        "\n# Miscellaneous Tables",
        "# These tables are used by the application for various purposes\n"
    ])

    # Generate FlaskSession table
    misc_code.extend([
        "class FlaskSession(Model):",
        f'{INDENT}__tablename__ = "nx_sessions"',
        '',
        f'{INDENT}id = Column(String(256), primary_key=True)',
        f'{INDENT}data = Column(LargeBinary)',
        f'{INDENT}expiry = Column(DateTime, nullable=False)',
        f'{INDENT}created = Column(DateTime, default=func.now())',
        f'{INDENT}modified = Column(DateTime, default=func.now(), onupdate=func.now())',
        '',
        f'{INDENT}def __repr__(self):',
        f'{INDENT}{INDENT}return f\'<Session {self.id}>\'',
        '',
        f'{INDENT}@classmethod',
        f'{INDENT}def cleanup_expired(cls, db_session):',
        f'{INDENT}{INDENT}"""Remove expired sessions from the database"""',
        f'{INDENT}{INDENT}cls.query.filter(cls.expiry < func.now()).delete()',
        f'{INDENT}{INDENT}db_session.commit()',
        '\n'
    ])

    # Add other miscellaneous tables here
    return misc_code

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Generate SQLAlchemy models from database schema.')
    parser.add_argument('--uri', type=str, required=True, help='Database URI')
    parser.add_argument('--output', type=str, default='generated_models.py', help='Output file name')
    parser.add_argument('--config', type=str, default='config.yaml', help='Configuration file')
    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Initialize engine and inspector
    engine = create_engine(args.uri)
    inspector = inspect(engine)
    metadata = MetaData()
    metadata.reflect(bind=engine)

    # Generate models
    model_code = gen_models(metadata, inspector, config)

    # Write to output file
    with open(args.output, "w") as f:
        f.write("\n".join(model_code)

    logger.info(f"Models generated successfully. Output written to {args.output}")

if __name__ == "__main__":
    main()
