import inflect
from sqlalchemy import create_engine, inspect, MetaData, Table, Column, ForeignKey, CheckConstraint, PrimaryKeyConstraint, UniqueConstraint, Index, Identity, func
from sqlalchemy.orm import declarative_base, relationship
import enum

from headers import gen_model_header, gen_photo_column, gen_file_column
from utils import snake_to_pascal, map_pgsql_datatypes, get_display_column

p = inflect.engine()

Base = declarative_base()

def gen_models(metadata, inspector):
    """Main function to generate model code."""
    model_code = []
    model_code.extend(gen_model_header())
    model_code.extend(gen_domains(inspector))
    model_code.extend(gen_enums(inspector))
    
    relationship_info = prepare_relationship_info(metadata, inspector)
    model_code.extend(gen_association_tables(metadata, inspector))
    model_code.extend(gen_tables(metadata, inspector, relationship_info))
    
    return model_code

# ... [previous functions remain the same] ...

def gen_table(table, inspector, relationship_info):
    """Generate code for a single table, including all constraints and indexes."""
    table_code = []
    table_name = table.name
    columns = inspector.get_columns(table_name)
    pk_constraint = inspector.get_pk_constraint(table_name)
    fks = inspector.get_foreign_keys(table_name)
    uqs = inspector.get_unique_constraints(table_name)
    indexes = inspector.get_indexes(table_name)
    table_comment = inspector.get_table_comment(table_name)

    table_class = snake_to_pascal(table_name)
    table_code.append(f"class {table_class}(Base):")
    table_code.append(f'    __tablename__ = "{table_name}"')
    
    if table_comment['text']:
        table_code.append(f'    __doc__ = """{table_comment["text"]}"""')

    table_code.extend(gen_columns(columns, pk_constraint, fks, uqs, table_class))
    table_code.extend(gen_relationships(fks, table_name, table_class, inspector, relationship_info))
    table_code.extend(gen_check_constraints(inspector, table_name))
    table_code.extend(gen_table_args(pk_constraint, uqs, indexes))
    table_code.extend(gen_repr_method(columns, pk_constraint))
    
    table_code.append("\n")
    return table_code

def gen_columns(columns, pk_constraint, fks, uqs, table_class):
    """Generate code for table columns, including identities and constraints."""
    column_code = []
    pk_columns = pk_constraint['constrained_columns']
    for column in columns:
        column_code.extend(gen_column(column, pk_columns, fks, uqs, table_class))
    return column_code

def gen_column(column, pk_columns, fks, uqs, table_class):
    """Generate code for a single column, including identity and constraints."""
    column_code = []
    column_name = column["name"]
    column_type = map_pgsql_datatypes(column["type"])
    
    attributes = []
    if column_name in pk_columns and len(pk_columns) == 1:
        attributes.append("primary_key=True")
    
    for fk in fks:
        if column_name in fk["constrained_columns"]:
            referred_table = fk["referred_table"]
            referred_columns = fk["referred_columns"]
            if len(fk["constrained_columns"]) == 1:
                onupdate = f", onupdate='{fk.get('options', {}).get('onupdate', 'NO ACTION')}'"
                ondelete = f", ondelete='{fk.get('options', {}).get('ondelete', 'NO ACTION')}'"
                attributes.append(f"ForeignKey('{referred_table}.{referred_columns[0]}'{onupdate}{ondelete})")
    
    if column_name in [uq["column_names"] for uq in uqs if len(uq["column_names"]) == 1]:
        attributes.append("unique=True")
    
    if not column["nullable"]:
        attributes.append("nullable=False")
    
    if column["default"]:
        default_value = process_default_value(column["default"])
        if default_value:
            attributes.append(f"default={default_value}")
    
    if "identity" in column and column["identity"]:
        identity = column["identity"]
        identity_args = []
        if identity.always:
            identity_args.append("always=True")
        if identity.start is not None:
            identity_args.append(f"start={identity.start}")
        if identity.increment is not None:
            identity_args.append(f"increment={identity.increment}")
        if identity_args:
            attributes.append(f"Identity({', '.join(identity_args)})")
    
    attributes_str = ", ".join(attributes)
    
    if column_name.endswith('_img') or column_name.endswith('_photo'):
        column_code.append(gen_photo_column(column_name, table_class))
    elif column_name.endswith('_file') or column_name.endswith('_doc'):
        column_code.append(gen_file_column(column_name, table_class))
    else:
        column_code.append(f"    {column_name} = Column({column_type}, {attributes_str})")
    
    return column_code

def gen_table_args(pk_constraint, uqs, indexes):
    """Generate __table_args__ for composite primary keys, unique constraints, and indexes."""
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
    
    if table_args:
        args_str = ",\n        ".join(table_args)
        return [f"    __table_args__ = (\n        {args_str},\n    )"]
    return []

# ... [rest of the code remains the same] ...

