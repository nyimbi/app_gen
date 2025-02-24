"""
Author: Nyimbi Odero
Copyright: Nyimbi Odero, 2024
License: MIT

gen_models.py: SQLAlchemy Model Generator

This script generates SQLAlchemy ORM models by introspecting an existing database schema.
It supports PostgreSQL databases and generates Python code that accurately represents
the database structure, including tables, columns, relationships, and constraints.

Features:
1. Generates SQLAlchemy declarative base models
2. Supports table and column comments
3. Handles primary keys, including composite primary keys
4. Generates foreign key relationships with correct cardinality
5. Supports unique constraints, including multi-column constraints
6. Generates indexes, including unique indexes
7. Handles IDENTITY columns
8. Supports ENUM types
9. Generates association tables for many-to-many relationships
10. Handles table inheritance
11. Supports column default values, converting them to SQLAlchemy expressions
12. Generates check constraints
13. Handles referential actions (ON DELETE, ON UPDATE) for foreign keys
14. Supports custom column types (e.g., JSON, ARRAY)
15. Generates __repr__ methods for each model
16. Handles schema-qualified table names
17. Breaks circular relationships to avoid infinite recursion

Usage:
python gen_models.py --uri "postgresql:///your_database_name" --output "your_models.py"

Dependencies:
- SQLAlchemy
- inflect

Note: This script requires utility functions from 'utils.py' and header generation
functions from 'oheaders.py' in the same directory.
"""

import inflect
from autoimport import fix_files
from typing import List, Dict, Any, Tuple, TypedDict
from sqlalchemy import (
    create_engine,
    inspect,
    MetaData,
    Table,
    Column,
    ForeignKey,
    CheckConstraint,
    PrimaryKeyConstraint,
    UniqueConstraint,
    Index,
    Identity,
    func,
    text,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import sqltypes
import enum
import argparse

from oheaders import gen_model_header, gen_photo_column, gen_file_column
from utils.case_utils import snake_to_pascal
from utils.db_utils import is_association_table
from utils.db_utils import map_pgsql_datatypes, get_display_column


# Add comprehensive logging
import logging

logger = logging.getLogger(__name__)


p = inflect.engine()
Base = declarative_base()

# Constants
INDENT = "    "
AB_PREFIX = "ab_"


# Add configuration file support
class ModelConfig(TypedDict):
    indent_size: int
    naming_convention: str
    relationship_style: str
    template_directory: str


# Track processed relationships to detect circular dependencies
processed_relationships: set = set()


def gen_models(metadata: MetaData, inspector: Any) -> List[str]:
    # logger.debug(f"Generating table {table.name}")
    model_code: List[str] = []
    reverse_relationships: Dict[str, List[str]] = {}
    association_tables: List[str] = []

    # Generate header, domains, and enums
    model_code.extend(gen_model_header())
    model_code.extend(gen_domains(inspector))
    model_code.extend(gen_enums(inspector))

    # Generate miscellaneous tables (including FlaskSession)
    model_code.extend(gen_misc_tables())

    # Identify association tables
    for table_name in inspector.get_table_names():
        if is_association_table(table_name, inspector):
            association_tables.append(table_name)

    # Prepare relationship information
    relationship_info = prepare_relationship_info(
        metadata, inspector, association_tables
    )

    # Generate regular tables and association tables
    for table_name in inspector.get_table_names():
        table = metadata.tables[table_name]
        if table_name in association_tables:
            table_code = gen_association_table(table, inspector)
        else:
            table_code, reverse_rels_info = gen_table(
                table, inspector, relationship_info, association_tables
            )
            for rev_rel in reverse_rels_info:
                if rev_rel["table"] not in reverse_relationships:
                    reverse_relationships[rev_rel["table"]] = []
                reverse_relationships[rev_rel["table"]].append(rev_rel["code"])
        model_code.extend(table_code)

    # Add reverse relationships to the appropriate tables
    for table_name, relationships in reverse_relationships.items():
        table_index = next(
            (
                i
                for i, line in enumerate(model_code)
                if line.startswith(f"class {snake_to_pascal(table_name)}(")
            ),
            None,
        )
        if table_index is None:
            continue
        for rel in relationships:
            insert_index = find_insertion_index(model_code, table_index)
            model_code.insert(insert_index, f"{INDENT}{rel}")
            model_code.insert(insert_index + 1, "")  # Add a blank line for readability

    return model_code


def gen_domains(inspector: Any) -> List[str]:
    """
    Generate code for database domains.

    In PostgreSQL, domains are not directly accessible through SQLAlchemy's inspector.
    This function returns an empty list, but can be extended in the future
    if a way to retrieve domain information is found.

    Args:
        inspector (Any): SQLAlchemy Inspector object.

    Returns:
        List[str]: An empty list, as domain information is not directly accessible.
    """
    print("Note: Domain generation is not implemented for this database.")
    return []


def gen_enums(inspector: Any) -> List[str]:
    """
    Generate code for database enums.

    Args:
        inspector (Any): SQLAlchemy Inspector object.

    Returns:
        List[str]: Generated enum code as a list of strings.
    """
    enum_code = ["# Enums defined in the database"]
    enums = inspector.get_enums()

    for enum in enums:
        enum_code.extend(gen_enum(enum))

    enum_code.append("\n")
    return enum_code


def gen_enum(enum: Dict[str, Any]) -> List[str]:
    """
    Generate code for a single enum.

    Args:
        enum (Dict[str, Any]): Dictionary containing enum information.

    Returns:
        List[str]: Generated enum code as a list of strings.
    """
    enum_code = []
    enum_code.append(f"\nclass {enum['name']}(enum.Enum):")
    for label in enum["labels"]:
        enum_code.append(f"{INDENT}{label.upper()} = '{label}'")
    return enum_code


def gen_association_table(table, inspector):
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
    table_code.append(f"{INDENT}__tablename__ = '{table_name}'")

    # Generate columns
    pk_columns = pk_constraint["constrained_columns"]
    for column in columns:
        column_code = gen_column(
            column, pk_columns, fks, uqs, table_name, is_association_table=True
        )
        table_code.extend(column_code)

    if table_comment["text"]:
        table_code.append(
            f"{INDENT}__table_args__ = {{'comment': \"{table_comment['text']}\"}}"
        )

    table_code.append("\n")
    return table_code


def update_related_tables_for_association(table_name, metadata, inspector, model_code):
    """Update related tables to include the association relationship for many-to-many relationships."""
    fks = inspector.get_foreign_keys(table_name)

    if len(fks) < 2:
        return model_code

    for fk in fks:
        referred_table = fk["referred_table"]
        referred_table_class = snake_to_pascal(referred_table)

        relationship_name = p.plural(table_name)

        table_start_index = next(
            (
                i
                for i, line in enumerate(model_code)
                if line.startswith(f"class {referred_table_class}(")
            ),
            None,
        )

        if table_start_index is None:
            continue

        insert_index = find_insertion_index(model_code, table_start_index)

        existing_relationship = any(
            f"{relationship_name} = relationship(" in line
            for line in model_code[table_start_index:insert_index]
        )

        if not existing_relationship:
            other_fk = next(f for f in fks if f != fk)
            other_table = other_fk["referred_table"]
            other_table_class = snake_to_pascal(other_table)

            # Determine the correct back_populates value
            back_populates = p.plural(referred_table.lower())

            relationship_str = (
                f"{INDENT}{relationship_name} = relationship('{other_table_class}', "
                f"secondary='{table_name}', "
                f"back_populates='{back_populates}')"
            )
            model_code.insert(insert_index, relationship_str)
            model_code.insert(insert_index + 1, "")

    return model_code


def find_insertion_index(model_code, table_start_index):
    """Find the correct index to insert the relationship in the model code."""
    for i, line in enumerate(
        model_code[table_start_index + 1 :], start=table_start_index + 1
    ):
        if line.strip().startswith("def __repr__") or line.startswith("class "):
            return i  # + table_start_index
    return len(model_code)  # If no suitable position is found, append at the end


def gen_tables(metadata, inspector, relationship_info, association_tables):
    """Generate code for database tables, excluding association tables."""
    table_code = []
    for table_name in inspector.get_table_names():
        if table_name not in association_tables:
            table = metadata.tables[table_name]
            table_code.extend(
                gen_table(table, inspector, relationship_info, association_tables)
            )
    return table_code


def gen_table(table, inspector, relationship_info, association_tables):
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
    table_code.extend(gen_table_args(pk_constraint, uqs, indexes, table_comment))

    table_code.extend(gen_columns(columns, pk_constraint, fks, uqs, table_name))

    for fk in fks:
        local_rel, reverse_rel_info = gen_relationship(
            fk,
            table_name,
            table_class,
            inspector,
            relationship_info,
            association_tables,
        )
        if local_rel:
            table_code.extend(local_rel)
        if reverse_rel_info:
            reverse_relationships_info.append(reverse_rel_info)

    table_code.extend(gen_check_constraints(inspector, table_name))
    table_code.extend(gen_repr_method(columns, pk_constraint))

    table_code.append("\n")
    return table_code, reverse_relationships_info


def gen_columns(columns, pk_constraint, fks, uqs, table_name):
    """Generate code for table columns, including identities, constraints, and comments."""
    column_code = []
    pk_columns = pk_constraint["constrained_columns"]
    for column in columns:
        column_code.extend(gen_column(column, pk_columns, fks, uqs, table_name))
    return column_code


def gen_column(column, pk_columns, fks, uqs, table_name, is_association_table=False):
    """Generate code for a single column, including identity, constraints, and comments."""
    column_code = []
    column_name = column["name"]
    column_type = column["type"].compile()
    column_type = map_pgsql_datatypes(column_type.lower())

    attributes = []

    for fk in fks:
        if column_name in fk["constrained_columns"]:
            referred_table = fk["referred_table"]
            referred_columns = fk["referred_columns"]
            if len(fk["constrained_columns"]) == 1:
                fk_str = f"ForeignKey('{referred_table}.{referred_columns[0]}')"
                attributes.append(fk_str)

                # Add secondary parameter for association tables
                # if is_association_table:
                #     attributes.append(f"secondary='{table_name}'")

    if column_name == "id":
        attributes.append("autoincrement=True")

    if column_name in pk_columns:
        attributes.append("primary_key=True")

    if not column.get("nullable", True):
        attributes.append("nullable=False")

    if column_name in [
        uq["column_names"][0] for uq in uqs if len(uq["column_names"]) == 1
    ]:
        attributes.append("unique=True")

    if column.get("default") is not None:
        default_value = process_default_value(
            column_name, column_type, column["default"]
        )
        if default_value:
            pass
            # attributes.append(f"default={default_value}")

    if column.get("comment"):
        attributes.append(f'comment="{column["comment"]}"')

    attributes_str = ", ".join(attributes)

    if is_enum_type(column_type, column.get("default")):
        try:
            enum_name, enum_options = extract_enum_info(column)
            column_type = f"Enum({enum_name})"
        except Exception as e:
            print(
                f"Warning: Could not extract enum info for column {column_name}: {str(e)}"
            )
            # Fall back to using the original column type
            column_type = column["type"].compile()

    if column_name.endswith("_img") or column_name.endswith("_photo"):
        column_code.append(gen_photo_column(column_name, table_name))
    elif column_name.endswith("_file") or column_name.endswith("_doc"):
        column_code.append(gen_file_column(column_name, table_name))
    else:
        if attributes_str:
            column_code.append(
                f"{INDENT}{column_name} = Column({column_type}, {attributes_str})"
            )
        else:
            column_code.append(f"{INDENT}{column_name} = Column({column_type})")

    return column_code


def is_enum_type(column_type, default):
    """Determine if the column is an enum type."""
    return "enum" in column_type.lower() or (default and "::t_" in default)


def extract_enum_info(column):
    """Extract enum name and options from column information."""
    column_name = column["name"]

    # Extract enum name from the type or default value
    if "enum" in column["type"].compile().lower():
        enum_name = column["type"].compile().lower().split(".")[-1]
    elif column["default"] and "::t_" in column["default"]:
        enum_name = column["default"].split("::")[1].split("'")[0]
    else:
        enum_name = f"t_{column_name}_enum"

    # Try to extract enum options from default value
    if column["default"] and "::t_" in column["default"]:
        enum_type = column["default"].split("::")[1].split(")")[0]
        enum_options = [opt.strip("'") for opt in enum_type.split(",")]
    # If not in default, try to extract from comment
    elif column.get("comment") and "," in column["comment"]:
        enum_options = [opt.strip() for opt in column["comment"].split(",")]

    enum_options_str = ", ".join([f"'{opt}'" for opt in enum_options])
    return enum_name, enum_options_str


def gen_relationship(
    fk, table_name, table_class, inspector, relationship_info, association_tables
):
    relationship_code = []
    reverse_relationship_info = None

    fk_cols = fk["constrained_columns"]
    referred_table = fk["referred_table"]
    referred_class = snake_to_pascal(referred_table)

    # Check for circular relationships
    relationship_key = (table_name, referred_table)
    if relationship_key in processed_relationships:
        return [], None

    cardinality = relationship_info[table_name].get(referred_table, "many-to-one")

    local_relationship_name = determine_relationship_name(
        fk_cols, table_name, referred_table, cardinality, inspector
    )
    remote_relationship_name = determine_remote_relationship_name(
        cardinality, table_name, referred_table, inspector
    )

    # Handle many-to-many relationships
    if cardinality == "many-to-many":
        assoc_table = find_association_table(
            table_name, referred_table, association_tables, inspector
        )
        if assoc_table:
            relationship_args = [
                f"'{referred_class}'",
                f"secondary='{assoc_table}'",
                f"back_populates='{remote_relationship_name}'",
            ]
        else:
            # If no association table found, fall back to many-to-one
            cardinality = "many-to-one"
            relationship_args = [
                f"'{referred_class}'",
                f"back_populates='{remote_relationship_name}'",
                f"foreign_keys='[{', '.join([f'{table_class}.{col}' for col in fk_cols])}]'",
            ]
    else:
        relationship_args = [
            f"'{referred_class}'",
            f"back_populates='{remote_relationship_name}'",
            f"foreign_keys='[{', '.join([f'{table_class}.{col}' for col in fk_cols])}]'",
        ]

    if cardinality in ["many-to-one", "one-to-one"]:
        relationship_args.append("lazy='select'")
    elif cardinality in ["one-to-many", "many-to-many"]:
        relationship_args.append("lazy='select'")

    relationship_str = ", ".join(relationship_args)
    relationship_code.append(
        f"{INDENT}{local_relationship_name} = relationship({relationship_str})"
    )

    # Generate reverse relationship
    if cardinality == "many-to-many":
        reverse_relationship_args = [
            f"'{table_class}'",
            f"secondary='{assoc_table}'",
            f"back_populates='{local_relationship_name}'",
        ]
    else:
        reverse_relationship_args = [
            f"'{table_class}'",
            f"back_populates='{local_relationship_name}'",
            f"foreign_keys='[{table_class}.{fk_cols[0]}]'",
        ]

    if cardinality in ["one-to-many", "many-to-many"]:
        reverse_relationship_args.append("lazy='select'")
    elif cardinality in ["many-to-one", "one-to-one"]:
        reverse_relationship_args.append("lazy='select'")

    reverse_relationship_str = ", ".join(reverse_relationship_args)
    reverse_relationship_info = {
        "table": referred_table,
        "code": f"{remote_relationship_name} = relationship({reverse_relationship_str})",
    }

    processed_relationships.add(relationship_key)
    return relationship_code, reverse_relationship_info


def determine_relationship_name(
    fk_cols, table_name, referred_table, cardinality, inspector
):
    """
    Determine the relationship name based on foreign key columns and table names.

    Args:
    fk_cols (list): List of foreign key column names
    table_name (str): Name of the current table
    referred_table (str): Name of the table being referred to
    cardinality (str): Type of relationship ('one-to-many', 'many-to-one', 'one-to-one', 'many-to-many')
    inspector (sqlalchemy.engine.reflection.Inspector): SQLAlchemy inspector object

    Returns:
    str: The determined relationship name
    """
    # Handle composite foreign keys
    if len(fk_cols) > 1:
        base_name = "_".join(
            col.replace("_id_fk", "").replace("_id", "") for col in fk_cols
        )
    else:
        base_name = fk_cols[0].replace("_id_fk", "").replace("_id", "")

    # Check if the base_name is a prefix or suffix of the referred_table
    if referred_table.lower().startswith(base_name) or referred_table.lower().endswith(
        base_name
    ):
        base_name = referred_table.lower()

    # Handle special cases like association tables
    if is_association_table(table_name, inspector):
        other_fk = next(
            fk
            for fk in inspector.get_foreign_keys(table_name)
            if fk["referred_table"] != referred_table
        )
        other_table = other_fk["referred_table"]
        return p.plural(other_table.lower())

    # Determine the appropriate name based on cardinality
    if cardinality in ["one-to-many", "many-to-many"]:
        return p.plural(base_name)
    elif cardinality == "many-to-one":
        # Check if there are multiple FKs to the same table
        fks_to_referred = [
            fk
            for fk in inspector.get_foreign_keys(table_name)
            if fk["referred_table"] == referred_table
        ]
        if len(fks_to_referred) > 1:
            # If multiple FKs exist, use a more specific name
            specific_name = "_".join(fk_cols)
            return f"{specific_name}_{base_name}"
        return p.plural(base_name)
    else:  # one-to-one
        return p.plural(base_name)


def determine_remote_relationship_name(
    cardinality, table_name, referred_table, inspector
):
    """
    Determine the name for the remote side of the relationship.

    Args:
    cardinality (str): Type of relationship ('one-to-many', 'many-to-one', 'one-to-one', 'many-to-many')
    table_name (str): Name of the current table
    referred_table (str): Name of the table being referred to
    inspector (sqlalchemy.engine.reflection.Inspector): SQLAlchemy inspector object

    Returns:
    str: The determined remote relationship name
    """
    if is_association_table(referred_table, inspector):
        # For association tables, use the plural of the current table
        return p.plural(table_name.lower())

    if cardinality in ["one-to-many", "many-to-many"]:
        return p.plural(table_name.lower())
    elif cardinality == "many-to-one":
        # Check if there are multiple relationships to this table
        fks_from_referred = [
            fk
            for fk in inspector.get_foreign_keys(referred_table)
            if fk["referred_table"] == table_name
        ]
        if len(fks_from_referred) > 1:
            # If multiple relationships exist, use a more specific name
            fk_cols = fks_from_referred[0]["constrained_columns"]
            specific_name = "_".join(
                col.replace("_id_fk", "").replace("_id", "") for col in fk_cols
            )
            return f"{specific_name}_{table_name.lower()}"
        return table_name.lower()
    else:  # one-to-one
        return table_name.lower()


def gen_table_args(pk_constraint, uqs, indexes, table_comment):
    """Generate __table_args__ for composite primary keys, unique constraints, indexes, and table comments."""
    table_args = []
    pk_columns = pk_constraint["constrained_columns"]

    if len(pk_columns) > 1:
        pk_columns_str = ", ".join([f"'{col}'" for col in pk_columns])
        table_args.append(f"PrimaryKeyConstraint({pk_columns_str})")

    for uq in uqs:
        if len(uq["column_names"]) > 1:
            uq_columns_str = ", ".join([f"'{col}'" for col in uq["column_names"]])
            table_args.append(
                f"UniqueConstraint({uq_columns_str}, name='{uq['name']}')"
            )

    for idx in indexes:
        idx_columns_str = ", ".join([f"'{col}'" for col in idx["column_names"]])
        unique_str = ", unique=True" if idx["unique"] else ""
        table_args.append(f"# Index('{idx['name']}', {idx_columns_str}{unique_str})")

    if table_comment["text"]:
        cmnt = {"comment": table_comment["text"]}
        table_args.append(str(cmnt))

    if table_args:
        if len(table_args) == 1 and table_comment["text"]:
            return [f"{INDENT}__table_args__ = ({table_args[0]})"]
        else:
            args_str = f",\n{INDENT}{INDENT}".join(table_args)
            return [
                f"{INDENT}__table_args__ = (\n{INDENT}{INDENT}{args_str},\n{INDENT})"
            ]
    return []


def gen_check_constraints(inspector, table_name):
    """Generate code for table check constraints."""
    constraint_code = []
    check_constraints = inspector.get_check_constraints(table_name)

    for cc in check_constraints:
        constraint_name = cc["name"]
        sql_expression = cc["sqltext"]
        constraint_code.append(
            f"{INDENT}__table_args__ = (\n"
            f"{INDENT}{INDENT}CheckConstraint('{sql_expression}', name='{constraint_name}'),\n"
            f"{INDENT}{INDENT}*__table_args__\n"
            f"{INDENT})"
        )

    return constraint_code


def gen_repr_method(columns, pk_constraint):
    """Generate code for the __repr__ method, using a combination of meaningful columns."""
    repr_code = []
    repr_code.append(f"\n{INDENT}def __repr__(self):")

    pk_columns = pk_constraint["constrained_columns"]

    # Candidate fields to be used in the __repr__ method
    candidate_fields = ["name", "title", "email", "username", "description"]

    # Determine which fields to use in __repr__
    selected_columns = []
    for column in columns:
        col_name = column["name"]
        if col_name in candidate_fields:
            selected_columns.append(col_name)
        if len(selected_columns) >= 2:  # We limit to two for a concise __repr__
            break

    # Fallback to using primary key if no suitable column is found
    if not selected_columns:
        selected_columns = pk_columns

    # Handle computed values (e.g., hybrid properties)
    if "full_name" in [col["name"] for col in columns]:
        selected_columns.append("full_name")

    # Construct the repr string
    if len(selected_columns) == 1:
        repr_code.append(
            f"{INDENT}{INDENT}return f'<{{self.__class__.__name__}} {{self.{selected_columns[0]}}}>'"
        )
    else:
        repr_attrs = ", ".join([f"{col}={{self.{col}}}" for col in selected_columns])
        repr_code.append(
            f"{INDENT}{INDENT}return f'<{{self.__class__.__name__}}({repr_attrs})>'"
        )

    return repr_code


def process_default_value(column_name, column_type, default):
    """Process and convert the default value to a Flask-SQLAlchemy compatible format."""

    # Handle auto-increment columns explicitly
    if column_name == "id" and default and "nextval" in default.lower():
        # return "autoincrement=True"
        return None

    if isinstance(default, str):
        default_lower = default.lower()

        # Translate known PostgreSQL default expressions to SQLAlchemy equivalents
        if default_lower in ("now()", "current_timestamp"):
            return "func.now()"
        elif "::t_" in default:
            enum_name = default.split("::")[1].split("'")[0]
            enum_value = default.split("'")[1].upper()
            # return f"{enum_name}.{enum_value}"
            return f"'{enum_value}'"
        elif default_lower == "true":
            return "True"
        elif default_lower == "false":
            return "False"
        elif "::timestamp" in default_lower:
            return "func.now()"
        elif "current_timestamp" in default_lower:
            return "func.now()"
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


def analyze_cardinality(table_name, fk, inspector, association_tables):
    referred_table = fk["referred_table"]
    constrained_columns = fk["constrained_columns"]
    referred_columns = fk["referred_columns"]

    # Handle self-referencing tables
    if table_name == referred_table:
        return analyze_self_referencing_relationship(
            table_name, constrained_columns, referred_columns, inspector
        )

    # Check for association tables (many-to-many)
    if table_name in association_tables or referred_table in association_tables:
        return "many-to-many"

    # Analyze primary keys and unique constraints
    pk_constraint = inspector.get_pk_constraint(table_name)
    pk_columns = set(pk_constraint["constrained_columns"])
    unique_constraints = inspector.get_unique_constraints(table_name)

    # One-to-one relationship checks
    if is_one_to_one_relationship(constrained_columns, pk_columns, unique_constraints):
        return "one-to-one"

    # Many-to-one relationship check
    referred_pk_constraint = inspector.get_pk_constraint(referred_table)
    referred_pk_columns = set(referred_pk_constraint["constrained_columns"])
    if set(referred_columns).issubset(referred_pk_columns):
        return "many-to-one"

    # Default to one-to-many if no other condition is met
    return "one-to-many"


# def is_association_table(table_name, inspector):
#     """Improved detection of association tables.
#     Check if a table is likely an association table.

#     An association table typically has the following characteristics:
#     0. The name ends in _assoc (our formal convention)
#     1. Has at least two foreign keys
#     2. May have additional columns for metadata (e.g., creation date, status)
#     3. Usually has a relatively small number of columns compared to regular entity tables
#     4. The name often follows a pattern like 'table1_table2' or 'table1_to_table2'

#     Args:
#             table_name (str): Name of the table to check
#             inspector (sa.engine.reflection.Inspector): SQLAlchemy Inspector object

#         Returns:
#             bool: True if the table is likely an association table, False otherwise
#     """
#     if table_name.endswith("_assoc"):
#         return True

#     fks = inspector.get_foreign_keys(table_name)
#     columns = inspector.get_columns(table_name)

#     if len(fks) < 2:
#         return False

#     non_fk_columns = [col for col in columns if col['name'] not in
#                       [c for fk in fks for c in fk['constrained_columns']]]

#     # Allow for id, timestamps, and a couple of additional metadata columns
#     allowed_extra = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']
#     extra_columns = [col for col in non_fk_columns if col['name'] not in allowed_extra]

#    # Check if the table name follows the pattern 'table1_table2' or 'table1_to_table2'
#     name_parts = table_name.split('_')
#     if len(name_parts) >= 2 and (name_parts[-1] in fks[0]['referred_table'] or name_parts[-1] in fks[1]['referred_table']):
#         return True

#     return len(extra_columns) <= 2


def is_one_to_one_relationship(constrained_columns, pk_columns, unique_constraints):
    """Check if the relationship is one-to-one based on constraints."""
    if set(constrained_columns) == pk_columns:
        return True
    for constraint in unique_constraints:
        if set(constrained_columns).issubset(set(constraint["column_names"])):
            return True
    return False


def analyze_composite_key_relationship(table_name, constrained_columns, inspector):
    """Analyze relationships involving composite keys."""
    # Implementation depends on specific composite key scenarios
    # This is a placeholder for more complex logic
    return "many-to-one"  # Default assumption for composite keys


def has_unique_index_on_foreign_key(table_name, constrained_columns, inspector):
    """Check if there's a unique index on the foreign key columns."""
    indexes = inspector.get_indexes(table_name)
    for index in indexes:
        if index["unique"] and set(constrained_columns).issubset(
            set(index["column_names"])
        ):
            return True
    return False


def follows_many_to_many_naming_convention(table_name, referred_table):
    """Check if the table name follows a common many-to-many naming convention."""
    parts = table_name.split("_")
    return len(parts) == 2 and (
        parts[0] == referred_table or parts[1] == referred_table
    )


def analyze_self_referencing_relationship(
    table_name, constrained_columns, referred_columns, inspector
):
    """
    Analyze self-referencing relationships to determine their nature.

    This function examines the structure of a self-referencing relationship
    to classify it as one of several types:
    - Hierarchical (tree-like structure)
    - Graph-like (many-to-many self-reference)
    - Linked list (one-to-one self-reference)
    - Generic one-to-many self-reference

    Args:
    table_name (str): Name of the table
    constrained_columns (list): Columns that form the foreign key
    referred_columns (list): Columns being referred to (usually primary key)
    inspector (SQLAlchemy Inspector): Database inspector object

    Returns:
    str: The determined relationship type
    """

    # Get all columns of the table
    columns = inspector.get_columns(table_name)
    column_names = [col["name"] for col in columns]

    # Get primary key information
    pk_constraint = inspector.get_pk_constraint(table_name)
    pk_columns = set(pk_constraint["constrained_columns"])

    # Get unique constraints
    unique_constraints = inspector.get_unique_constraints(table_name)

    # Check if the foreign key is part of a unique constraint
    is_unique_fk = any(
        set(constrained_columns).issubset(set(constraint["column_names"]))
        for constraint in unique_constraints
    )

    # Check if there are additional foreign keys to this table
    other_fks = [
        fk
        for fk in inspector.get_foreign_keys(table_name)
        if fk["referred_table"] == table_name
        and fk["constrained_columns"] != constrained_columns
    ]

    # Check for common hierarchical structure column names
    hierarchical_columns = [
        "parent_id_fk",
        "parent",
        "ancestor_id_fk",
        "superior_id_fk",
    ]
    has_hierarchical_column = any(
        col in hierarchical_columns for col in constrained_columns
    )

    # Check for closure table pattern (for efficient tree traversal)
    closure_table_name = f"{table_name}_closure"
    has_closure_table = closure_table_name in inspector.get_table_names()

    # Analyze the relationship
    if is_unique_fk and len(constrained_columns) == len(referred_columns) == 1:
        return "one-to-one-self"  # Linked list-like structure

    elif has_hierarchical_column or has_closure_table:
        return "hierarchical-self"  # Tree-like structure

    elif len(other_fks) > 0:
        return "graph-self"  # Complex graph-like structure

    elif set(constrained_columns) == pk_columns:
        return "one-to-one-self"  # Each record points to exactly one other record

    elif "level" in column_names or "depth" in column_names:
        return "hierarchical-self"  # Likely a leveled hierarchy

    else:
        return "one-to-many-self"  # Generic self-reference, assuming one-to-many


def get_self_referencing_relationship_details(table_name, relationship_type, inspector):
    """
    Get additional details about the self-referencing relationship.

    Args:
    table_name (str): Name of the table
    relationship_type (str): Type of self-referencing relationship
    inspector (SQLAlchemy Inspector): Database inspector object

    Returns:
    dict: Additional details about the relationship
    """
    details = {"type": relationship_type, "suggestion": "", "additional_info": {}}

    if relationship_type == "one-to-one-self":
        details["suggestion"] = (
            "Consider using 'uselist=False' in the relationship definition."
        )
    elif relationship_type == "hierarchical-self":
        details["suggestion"] = (
            "Consider using a tree structure library like SQLAlchemy-Utils' TreeNode."
        )

        # Check for closure table
        closure_table_name = f"{table_name}_closure"
        if closure_table_name in inspector.get_table_names():
            details["additional_info"]["has_closure_table"] = True
            details["suggestion"] += (
                " A closure table is detected, which can be used for efficient tree traversal."
            )
    elif relationship_type == "graph-self":
        details["suggestion"] = (
            "This is a complex self-referencing structure. Consider using a graph database if the relationships are central to your application."
        )
    elif relationship_type == "one-to-many-self":
        details["suggestion"] = (
            "This is a standard self-referencing relationship. No special handling is typically needed."
        )

    return details


def handle_self_referencing_table(
    table_name, constrained_columns, referred_columns, inspector
):
    """Handle the analysis of self-referencing tables."""
    pk_constraint = inspector.get_pk_constraint(table_name)
    pk_columns = set(pk_constraint["constrained_columns"])

    # Check if the FK is part of the PK
    if set(constrained_columns).issubset(pk_columns):
        return "one-to-one"

    unique_constraints = inspector.get_unique_constraints(table_name)
    for constraint in unique_constraints:
        if set(constrained_columns).issubset(set(constraint["column_names"])):
            return "one-to-one"

    # Check for hierarchical relationships
    if set(referred_columns) == set(pk_columns):
        return "one-to-many"

    return "many-to-many"


def prepare_relationship_info(metadata, inspector, association_tables):
    relationship_info = {}
    for table_name in inspector.get_table_names():
        if table_name not in association_tables:
            relationship_info[table_name] = {}
            for fk in inspector.get_foreign_keys(table_name):
                referred_table = fk["referred_table"]
                cardinality = analyze_cardinality(
                    table_name, fk, inspector, association_tables
                )
                relationship_info[table_name][referred_table] = cardinality
    return relationship_info


def find_association_table(table1, table2, association_tables, inspector):
    for assoc_table in association_tables:
        fks = inspector.get_foreign_keys(assoc_table)
        if len(fks) == 2:
            referred_tables = {fk["referred_table"] for fk in fks}
            if table1 in referred_tables and table2 in referred_tables:
                return assoc_table
    return None


def gen_misc_tables() -> List[str]:
    """
    Generate code for miscellaneous tables needed by the application.
    Currently includes:
    1. FlaskSession table for persistent session storage

    Returns:
        List[str]: List of code strings for miscellaneous tables
    """
    misc_code = []

    # Add header comment
    misc_code.extend(
        [
            "\n# Miscellaneous Tables",
            "# These tables are used by the application for various purposes\n",
        ]
    )

    # Generate FlaskSession table
    misc_code.extend(
        [
            "class FlaskSession(Model):",
            f"{INDENT}__tablename__ = 'nx_sessions'",
            "",
            f"{INDENT}id = Column(String(256), primary_key=True)",
            f"{INDENT}data = Column(LargeBinary)",
            f"{INDENT}expiry = Column(DateTime, nullable=False)",
            f"{INDENT}created = Column(DateTime, default=func.now())",
            f"{INDENT}modified = Column(DateTime, default=func.now(), onupdate=func.now())",
            "",
            f"{INDENT}def __repr__(self):",
            f"{INDENT}{INDENT}return f'<Session {{self.id}}>'",
            "",
            f"{INDENT}@classmethod",
            f"{INDENT}def cleanup_expired(cls, db_session):",
            f'{INDENT}{INDENT}"""Remove expired sessions from the database"""',
            f"{INDENT}{INDENT}cls.query.filter(cls.expiry < func.now()).delete()",
            f"{INDENT}{INDENT}db_session.commit()",
            "\n",
        ]
    )

    return misc_code


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Generate SQLAlchemy models from database schema."
    )
    parser.add_argument("--uri", type=str, required=True, help="Database URI")
    parser.add_argument(
        "--output", type=str, default="generated_models.py", help="Output file name"
    )
    args = parser.parse_args()

    engine = create_engine(args.uri)
    inspector = inspect(engine)
    metadata = MetaData()
    metadata.reflect(bind=engine)

    model_code = gen_models(metadata, inspector)

    with open(args.output, "w") as f:
        f.write("\n".join(model_code))

    print(f"Models generated successfully. Output written to {args.output}")


if __name__ == "__main__":
    main()
