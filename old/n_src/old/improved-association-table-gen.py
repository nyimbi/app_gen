import inflect
from sqlalchemy import inspect, MetaData, create_engine, Column, ForeignKey, CheckConstraint, PrimaryKeyConstraint, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import sqltypes

from headers import gen_model_header, gen_photo_column, gen_file_column
from utils import snake_to_pascal, map_pgsql_datatypes, get_display_column

p = inflect.engine()

# ... [previous code remains the same] ...

def gen_models(metadata, inspector):
    """Main function to generate model code."""
    model_code = []
    model_code.extend(gen_model_header())
    model_code.extend(gen_domains(inspector))
    model_code.extend(gen_enums(inspector))
    model_code.extend(gen_association_tables(metadata, inspector))
    model_code.extend(gen_tables(metadata, inspector))
    return model_code

def gen_association_tables(metadata, inspector):
    """Generate code for association tables."""
    association_code = []
    association_code.append("\n# Association Tables")
    
    for table in metadata.tables.values():
        if is_association_table(table, inspector):
            association_code.extend(gen_association_table(table, inspector))
    
    association_code.append("\n")
    return association_code

def is_association_table(table, inspector):
    """Check if a table is an association table."""
    if len(table.columns) != 2:
        return False
    
    fks = inspector.get_foreign_keys(table.name)
    if len(fks) != 2:
        return False
    
    # Check if both columns are part of the primary key
    pk = inspector.get_pk_constraint(table.name)
    return set(pk['constrained_columns']) == set(col.name for col in table.columns)

def gen_association_table(table, inspector):
    """Generate code for a single association table."""
    table_code = []
    table_name = table.name
    fks = inspector.get_foreign_keys(table_name)
    
    table_code.append(f"{table_name} = Table(")
    table_code.append(f"    '{table_name}', Model.metadata,")
    
    for column in table.columns:
        fk = next((fk for fk in fks if column.name in fk['constrained_columns']), None)
        if fk:
            referred_table = fk['referred_table']
            referred_column = fk['referred_columns'][0]
            table_code.append(f"    Column('{column.name}', ForeignKey('{referred_table}.{referred_column}'), primary_key=True),")
    
    table_code.append(")")
    table_code.append("")
    
    return table_code

def gen_relationship(fk, table_name, table_class, inspector):
    """Generate code for a single relationship, handling association tables."""
    relationship_code = []
    fk_cols = fk["constrained_columns"]
    fk_name = "_".join(fk_cols) if len(fk_cols) > 1 else fk_cols[0]
    if fk_name.endswith('_id_fk'):
        fk_name = fk_name[:-6]
    fk_name = fk_name.split('_fk')[0]
    fk_name = fk_name.split('_id')[0]
    
    referred_table = snake_to_pascal(fk["referred_table"])
    referred_columns = fk["referred_columns"]
    
    # Analyze cardinality
    cardinality = analyze_cardinality(table_name, fk, inspector)
    
    # Determine backref name and if it should be a list
    backref_name = f'{p.plural(table_name)}' if cardinality in ['one-to-many', 'many-to-many'] else table_name
    backref_type = 'backref' if cardinality in ['one-to-one', 'many-to-one'] else 'back_populates'
    
    # Set up relationship arguments
    rel_args = [f"'{referred_table}'"]
    rel_args.append(f"{backref_type}='{backref_name}'")
    
    if cardinality in ['one-to-many', 'many-to-many']:
        rel_args.append("lazy='dynamic'")
    
    # Handle self-referential relationships
    if table_class == referred_table:
        rel_args.append(f"remote_side=[{', '.join([f'{referred_table}.{col}' for col in referred_columns])}]")
    
    # Add primaryjoin for complex relationships
    if len(fk_cols) > 1:
        joins = [f"{table_class}.{local} == {referred_table}.{remote}"
                 for local, remote in zip(fk_cols, referred_columns)]
        primaryjoin = " and ".join(joins)
        rel_args.append(f"primaryjoin='{primaryjoin}'")
    else:
        primaryjoin = f"{table_class}.{fk_cols[0]} == {referred_table}.{referred_columns[0]}"
        rel_args.append(f"primaryjoin='{primaryjoin}'")
    
    # Handle many-to-many relationships
    if cardinality == 'many-to-many':
        association_table = find_association_table(table_name, fk["referred_table"], inspector)
        if association_table:
            rel_args.append(f"secondary={association_table}")
    
    relationship_str = ", ".join(rel_args)
    relationship_code.append(f"    {fk_name} = relationship({relationship_str})")
    
    return relationship_code

def find_association_table(table1, table2, inspector):
    """Find the association table for a many-to-many relationship."""
    for table_name in inspector.get_table_names():
        table = inspector.get_table(table_name)
        if is_association_table(table, inspector):
            fks = inspector.get_foreign_keys(table_name)
            referred_tables = {fk['referred_table'] for fk in fks}
            if table1 in referred_tables and table2 in referred_tables:
                return table_name
    return None

# ... [rest of the code remains the same] ...

