"""
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
11. Supports column default values
12. Generates check constraints
13. Handles referential actions (ON DELETE, ON UPDATE) for foreign keys
14. Supports custom column types (e.g., JSON, ARRAY)
15. Generates __repr__ methods for each model
16. Handles schema-qualified table names

Usage:
python gen_models.py --uri "postgresql:///your_database_name" --output "your_models.py"

Dependencies:
- SQLAlchemy
- inflect

Note: This script requires utility functions from 'utils.py' and header generation
functions from 'headers.py' in the same directory.
"""

import inflect
from sqlalchemy import (
    create_engine, inspect, MetaData, Table, Column, ForeignKey,
    CheckConstraint, PrimaryKeyConstraint, UniqueConstraint, Index,
    Identity, func, text
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import sqltypes
import enum
import argparse

from oheaders import gen_model_header, gen_photo_column, gen_file_column
from utils import snake_to_pascal
from db_utils import map_pgsql_datatypes, get_display_column

p = inflect.engine()
Base = declarative_base()

# Set the indentation to 4 spaces
INDENT = "    "

def gen_models(metadata, inspector):
    """Main function to generate model code."""
    model_code = []

    # Generate header, domains, and enums
    model_code.extend(gen_model_header())
    model_code.extend(gen_domains(inspector))
    model_code.extend(gen_enums(inspector))

    # Prepare relationship information
    relationship_info = prepare_relationship_info(metadata, inspector)

    # Generate regular tables and collect reverse relationships
    reverse_relationships = {}
    for table_name in inspector.get_table_names():
        if not is_association_table(table_name, inspector):
            table = metadata.tables[table_name]
            table_code, reverse_rels = gen_table(table, inspector, relationship_info)
            model_code.extend(table_code)
            reverse_relationships[table_name] = reverse_rels

    # Add reverse relationships to the appropriate tables
    for table_name, relationships in reverse_relationships.items():
        table_index = next(i for i, line in enumerate(model_code) if line.startswith(f"class {snake_to_pascal(table_name)}("))
        for rel in relationships:
            insert_index = next((i for i, line in enumerate(model_code[table_index:]) if line.strip().startswith("def __repr__")), None)
            if insert_index is not None:
                insert_index += table_index
            else:
                insert_index = len(model_code)
            model_code.insert(insert_index, f"{INDENT}{rel}")
            model_code.insert(insert_index + 1, "")  # Add a blank line for readability

    # Generate association tables
    for table_name in inspector.get_table_names():
        if is_association_table(table_name, inspector):
            model_code.extend(gen_association_table(table_name, metadata, inspector))

    # Update related tables for associations
    for table_name in inspector.get_table_names():
        if is_association_table(table_name, inspector):
            model_code = update_related_tables_for_association(table_name, metadata, inspector, model_code)

    return model_code

def gen_domains(inspector):
    """Generate code for database domains."""
    domain_code = ["# Domains defined in the database"]
    domains = inspector.get_domains()

    for domain in domains:
        domain_code.extend(gen_domain(domain))

    domain_code.append("\n")
    return domain_code

def gen_domain(domain):
    """Generate code for a single domain."""
    domain_code = []
    domain_name = domain["name"]
    base_type = domain["type"].compile()
    BaseType = map_pgsql_datatypes(base_type.lower())

    domain_code.append(f"\nclass {domain_name}({BaseType}):")

    if domain["default"]:
        domain_code.append(f"{INDENT}default = {domain['default']}")

    if not domain["nullable"]:
        domain_code.append(f"{INDENT}not_null = True")

    for constraint in domain.get("constraints", []):
        domain_code.append(f"{INDENT}# Constraint: {constraint['name']}")
        domain_code.append(f"{INDENT}check = '{constraint['check']}'")

    return domain_code

def gen_enums(inspector):
    """Generate code for database enums."""
    enum_code = ['# Enums defined in the database']
    enums = inspector.get_enums()

    for enum in enums:
        enum_code.extend(gen_enum(enum))

    enum_code.append("\n")
    return enum_code

def gen_enum(enum):
    """Generate code for a single enum."""
    enum_code = []
    enum_code.append(f"\nclass {enum['name']}(enum.Enum):")
    for label in enum["labels"]:
        enum_code.append(f"{INDENT}{label.upper()} = '{label}'")
    return enum_code

def gen_association_table(table_name, metadata, inspector):
    """Generate code for a single association table."""
    table_code = []
    columns = inspector.get_columns(table_name)
    fks = inspector.get_foreign_keys(table_name)
    table_comment = inspector.get_table_comment(table_name)

    table_class = snake_to_pascal(table_name)
    table_code.append(f"class {table_class}(Model):")
    table_code.append(f"{INDENT}__tablename__ = '{table_name}'")

    for column in columns:
        col_name = column['name']
        col_type = column['type'].compile()
        col_type = map_pgsql_datatypes(col_type.lower())

        attributes = []
        fk = next((fk for fk in fks if col_name in fk['constrained_columns']), None)

        if fk:
            referred_table = fk['referred_table']
            referred_column = fk['referred_columns'][0]
            attributes.append(f"ForeignKey('{referred_table}.{referred_column}')")

        if col_name in inspector.get_pk_constraint(table_name)['constrained_columns']:
            attributes.append("primary_key=True")

        if not column['nullable']:
            attributes.append("nullable=False")

        if column.get('default') is not None:
            default_value = process_default_value(column['default'])
            if default_value:
                attributes.append(f"default={default_value}")

        if column.get('comment'):
            attributes.append(f"comment=\"{column['comment']}\"")

        attributes_str = ", ".join(attributes)
        table_code.append(f"{INDENT}{col_name} = Column({col_type}, {attributes_str})")

    # Generate relationships for the association table
    for fk in fks:
        referred_table = snake_to_pascal(fk['referred_table'])
        backref_name = p.plural(table_name)
        relationship_str = f"relationship('{referred_table}', back_populates='{backref_name}')"
        rel_name = fk['constrained_columns'][0].replace('_id_fk', '').replace('_id', '')
        table_code.append(f"{INDENT}{rel_name} = {relationship_str}")

    if table_comment['text']:
        table_code.append(f"{INDENT}__table_args__ = {{'comment': \"{table_comment['text']}\"}}")

    table_code.append("")
    return table_code

def update_related_tables_for_association(table_name, metadata, inspector, model_code):
    """Update related tables to include the association relationship for many-to-many relationships."""
    fks = inspector.get_foreign_keys(table_name)
    table = metadata.tables[table_name]

    if len(fks) != 2:
        return  # Only handle tables with exactly two foreign keys (typical for many-to-many)

    for fk in fks:
        referred_table = fk['referred_table']
        referred_table_class = snake_to_pascal(referred_table)
        local_cols = fk['constrained_columns']
        remote_cols = fk['referred_columns']

        # Determine the relationship name
        relationship_name = p.plural(table_name)

        # Find the index of the related table in the model_code
        table_start_index = next((i for i, line in enumerate(model_code)
                                  if line.startswith(f"class {referred_table_class}(")), None)

        if table_start_index is None:
            continue  # Skip if the related table is not found

        # Find the index to insert the new relationship
        insert_index = next((i for i, line in enumerate(model_code[table_start_index:])
                             if line.strip().startswith("def __repr__")), None)

        if insert_index is not None:
            insert_index += table_start_index
        else:
            insert_index = next((i for i, line in enumerate(model_code[table_start_index:])
                                 if line.startswith("class ")), None)
            if insert_index is not None:
                insert_index += table_start_index
            else:
                insert_index = len(model_code)

        # Check if the relationship already exists
        existing_relationship = any(f"{relationship_name} = relationship(" in line
                                    for line in model_code[table_start_index:insert_index])

        if not existing_relationship:
            # Add the relationship to the related table
            other_fk = next(f for f in fks if f != fk)
            other_table = other_fk['referred_table']
            other_table_class = snake_to_pascal(other_table)

            relationship_str = (f"{INDENT}{relationship_name} = relationship('{other_table_class}', "
                                f"secondary='{table_name}', "
                                f"back_populates='{p.plural(referred_table)}')")
            print(relationship_str)
            model_code.insert(insert_index, relationship_str)
            model_code.insert(insert_index + 1, "")  # Add a blank line for readability

    return model_code

def gen_tables(metadata, inspector, relationship_info, association_tables):
    """Generate code for database tables, excluding association tables."""
    table_code = []
    for table_name in inspector.get_table_names():
        if table_name not in association_tables:
            table = metadata.tables[table_name]
            table_code.extend(gen_table(table, inspector, relationship_info))
    return table_code

def gen_table(table, inspector, relationship_info):
    """Generate code for a single table, including all constraints, indexes, and comments."""
    table_code = []
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

    table_code.extend(gen_columns(columns, pk_constraint, fks, uqs, table_class))

    reverse_relationships = []
    for fk in fks:
        local_rel, reverse_rel = gen_relationship(fk, table_name, table_class, inspector, relationship_info)
        table_code.extend(local_rel)
        reverse_relationships.extend(reverse_rel)

    table_code.extend(gen_check_constraints(inspector, table_name))
    table_code.extend(gen_repr_method(columns, pk_constraint))

    table_code.append("\n")
    return table_code, reverse_relationships

def gen_columns(columns, pk_constraint, fks, uqs, table_class):
    """Generate code for table columns, including identities, constraints, and comments."""
    column_code = []
    pk_columns = pk_constraint['constrained_columns']
    for column in columns:
        column_code.extend(gen_column(column, pk_columns, fks, uqs, table_class))
    return column_code

def gen_column(column, pk_columns, fks, uqs, table_class):
    """Generate code for a single column, including identity, constraints, and comments."""
    column_code = []
    column_name = column["name"]
    column_type = column['type'].compile()
    column_type = map_pgsql_datatypes(column_type.lower())
    c_default = ''

    attributes = []
    if column_name in pk_columns and len(pk_columns) == 1:
        attributes.append("primary_key=True")

    for fk in fks:
        if column_name in fk["constrained_columns"]:
            referred_table = fk["referred_table"]
            referred_columns = fk["referred_columns"]
            if len(fk["constrained_columns"]) == 1:
                onupdate = fk.get('options', {}).get('onupdate', 'NO ACTION')
                ondelete = fk.get('options', {}).get('ondelete', 'NO ACTION')
                fk_str = f"ForeignKey('{referred_table}.{referred_columns[0]}'"
                if onupdate != 'NO ACTION':
                    fk_str += f", onupdate='{onupdate}'"
                if ondelete != 'NO ACTION':
                    fk_str += f", ondelete='{ondelete}'"
                fk_str += ")"
                attributes.append(fk_str)

    if not column.get("nullable", True):
        attributes.append("nullable=False")

    if column_name in [uq["column_names"] for uq in uqs if len(uq["column_names"]) == 1]:
        attributes.append("unique=True")
    if column.get('default') is not None:
        default_value = process_default_value(column['default'])
        if default_value == 'autoincrement':
            attributes.append("autoincrement=True")
        else:
            if default_value is not None:
                attributes.append(f"default={default_value}")

    if column.get("comment"):
        attributes.append(f"comment=\"{column['comment']}\"")

    attributes_str = ", ".join(attributes)

    if column_name.endswith('_img') or column_name.endswith('_photo'):
        column_code.append(gen_photo_column(column_name, table_class))
    elif column_name.endswith('_file') or column_name.endswith('_doc'):
        column_code.append(gen_file_column(column_name, table_class))
    else:
        if attributes_str:
            column_code.append(f"{INDENT}{column_name} = Column({column_type}, {attributes_str})")
        else:
            column_code.append(f"{INDENT}{column_name} = Column({column_type})")

    return column_code

def gen_relationships(fks, table_name, table_class, inspector, relationship_info):
    """Generate code for table relationships, considering composite foreign keys."""
    relationship_code = []
    for fk in fks:
        relationship_code.extend(gen_relationship(fk, table_name, table_class, inspector, relationship_info))
    return relationship_code

def gen_relationship(fk, table_name, table_class, inspector, relationship_info):
    """Generate code for relationships, handling both sides of the relationship."""
    relationship_code = []
    fk_cols = fk["constrained_columns"]
    referred_table = fk["referred_table"]
    referred_columns = fk["referred_columns"]
    referred_class = snake_to_pascal(referred_table)

    # Determine relationship type
    cardinality = relationship_info[table_name].get(referred_table, 'many-to-one')

    # Generate relationship for the current table
    local_relationship_name = '_'.join(fk_cols) if len(fk_cols) > 1 else fk_cols[0]
    if local_relationship_name.endswith('_id'):
        local_relationship_name = local_relationship_name[:-3]
    if local_relationship_name.endswith('_fk'):
        local_relationship_name = local_relationship_name[:-3]

    remote_relationship_name = p.plural(table_name) if cardinality in ['one-to-many', 'many-to-many'] else table_name

    # Handle many-to-many relationships
    if cardinality == 'many-to-many':
        association_table = find_association_table(table_name, referred_table, inspector)
        if association_table:
            relationship_code.append(f"{INDENT}{p.plural(referred_table)} = relationship('{referred_class}', secondary='{association_table}', back_populates='{remote_relationship_name}')")
            # We'll handle the other side of the relationship in update_related_tables_for_association
            return relationship_code, []

    # Generate relationship for the current table
    relationship_args = [f"'{referred_class}'", f"back_populates='{remote_relationship_name}'"]

    if cardinality == 'many-to-one':
        relationship_args.append("lazy='joined'")
    elif cardinality == 'one-to-many':
        relationship_args.append("lazy='selectin'")

    if table_class == referred_class:  # self-referential
        relationship_args.append(f"remote_side=[{', '.join([f'{referred_class}.{col}' for col in referred_columns])}]")

    relationship_str = ', '.join(relationship_args)
    relationship_code.append(f"{INDENT}{local_relationship_name} = relationship({relationship_str})")

    # Generate the reverse relationship (to be added to the referred table)
    reverse_relationship_code = []
    reverse_relationship_args = [f"'{table_class}'", f"back_populates='{local_relationship_name}'"]

    if cardinality == 'one-to-many':
        reverse_relationship_args.append("lazy='selectin'")
    elif cardinality == 'many-to-one':
        reverse_relationship_args.append("lazy='joined'")

    reverse_relationship_str = ', '.join(reverse_relationship_args)
    reverse_relationship_code.append(f"{remote_relationship_name} = relationship({reverse_relationship_str})")

    return relationship_code, reverse_relationship_code

def gen_table_args(pk_constraint, uqs, indexes, table_comment):
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
        table_args.append(f"Index('{idx['name']}', {idx_columns_str}{unique_str})")

    if table_comment['text']:
        cmnt = {'comment': table_comment['text']}
        table_args.append(str(cmnt))

    if table_args:
        if len(table_args) == 1 and table_comment['text']:
            return [f"{INDENT}__table_args__ = ({table_args[0]})"]
        else:
            args_str = f",\n{INDENT}{INDENT}".join(table_args)
            return [f"{INDENT}__table_args__ = (\n{INDENT}{INDENT}{args_str},\n{INDENT})"]
    return []

def gen_check_constraints(inspector, table_name):
    """Generate code for table check constraints."""
    constraint_code = []
    check_constraints = inspector.get_check_constraints(table_name)

    for cc in check_constraints:
        constraint_name = cc['name']
        sql_expression = cc['sqltext']
        constraint_code.append(
            f"{INDENT}__table_args__ = (\n"
            f"{INDENT}{INDENT}CheckConstraint('{sql_expression}', name='{constraint_name}'),\n"
            f"{INDENT}{INDENT}*__table_args__\n"
            f"{INDENT})"
        )

    return constraint_code

def gen_repr_method(columns, pk_constraint):
    """Generate code for the __repr__ method, using the selected display column."""
    repr_code = []
    repr_code.append(f"\n{INDENT}def __repr__(self):")
    pk_columns = pk_constraint['constrained_columns']

    display_expr, is_expression = get_display_column(columns)

    if len(pk_columns) > 1:
        pk_attrs = ", ".join([f"{pk}={{self.{pk}}}" for pk in pk_columns])
        repr_code.append(f"{INDENT}{INDENT}return f'<{{self.__class__.__name__}}({pk_attrs})>'")
    elif is_expression:
        repr_code.append(f"{INDENT}{INDENT}return f'<{{self.__class__.__name__}} {{{{self.{display_expr.strip('f')}}}}}>'")
    else:
        repr_code.append(f"{INDENT}{INDENT}return f'<{{self.__class__.__name__}} {{self.{display_expr}}}>'")

    return repr_code

def process_default_value(default):
    """Process default value for a column."""
    if default.lower() == 'false':
        return 'False'
    elif default.lower() == 'true':
        return 'True'
    elif default.lower() == 'now()':
        return 'func.now()'
    elif default.startswith('nextval'):
        return 'autoincrement'
    else:
        return None

def is_association_table(table_name, inspector):
    """
    Check if a table is an association table.

    An association table typically has the following characteristics:
    1. At least two foreign keys
    2. All foreign key columns are part of the primary key
    3. May have additional columns (e.g., for additional association data)
    4. Usually has no more than one or two non-foreign key columns
    """
    fks = inspector.get_foreign_keys(table_name)
    if len(fks) < 2:
        return False  # Association tables should have at least two foreign keys

    pk_constraint = inspector.get_pk_constraint(table_name)
    pk_columns = set(pk_constraint['constrained_columns'])
    fk_columns = set(col for fk in fks for col in fk['constrained_columns'])

    columns = inspector.get_columns(table_name)
    all_columns = set(col['name'] for col in columns)

    # Check if all foreign key columns are part of the primary key
    if not fk_columns.issubset(pk_columns):
        return False

    # Check the number of non-foreign key columns
    non_fk_columns = all_columns - fk_columns
    if len(non_fk_columns) > 3:
        return False  # Probably not an association table if it has more than two non-FK columns

    # If we've passed all checks, it's likely an association table
    return True

def analyze_cardinality(table_name, fk, inspector):
    """Analyze the cardinality of a relationship."""
    referred_table = fk["referred_table"]
    constrained_columns = fk["constrained_columns"]
    referred_columns = fk["referred_columns"]

    if is_association_table(table_name, inspector):
        return 'many-to-many'

    pk_constraint = inspector.get_pk_constraint(table_name)
    pk_columns = pk_constraint['constrained_columns']
    if set(constrained_columns).issubset(set(pk_columns)):
        return 'one-to-one' if len(constrained_columns) == len(pk_columns) else 'many-to-one'

    unique_constraints = inspector.get_unique_constraints(table_name)
    for constraint in unique_constraints:
        if set(constrained_columns).issubset(set(constraint['column_names'])):
            return 'one-to-one'

    referred_pk_constraint = inspector.get_pk_constraint(referred_table)
    referred_pk_columns = referred_pk_constraint['constrained_columns']
    if set(referred_columns) == set(referred_pk_columns):
        return 'many-to-one'

    for other_fk in inspector.get_foreign_keys(table_name):
        if other_fk != fk and other_fk['referred_table'] != referred_table:
            return 'many-to-many'

    return 'one-to-many'

def prepare_relationship_info(metadata, inspector):
    """Prepare relationship information for all tables."""
    relationship_info = {}
    for table_name in inspector.get_table_names():
        relationship_info[table_name] = {}
        for fk in inspector.get_foreign_keys(table_name):
            referred_table = fk['referred_table']
            cardinality = analyze_cardinality(table_name, fk, inspector)
            relationship_info[table_name][referred_table] = cardinality
    return relationship_info

def find_association_table(table1, table2, inspector):
    """Find the association table for a many-to-many relationship."""
    for table_name in inspector.get_table_names():
        if is_association_table(table_name, inspector):
            fks = inspector.get_foreign_keys(table_name)
            referred_tables = {fk['referred_table'] for fk in fks}
            if table1 in referred_tables and table2 in referred_tables:
                return table_name
    return None

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Generate SQLAlchemy models from database schema.')
    parser.add_argument('--uri', type=str, required=True, help='Database URI')
    parser.add_argument('--output', type=str, default='generated_models.py', help='Output file name')
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
