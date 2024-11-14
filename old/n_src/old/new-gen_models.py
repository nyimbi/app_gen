import inflect
from sqlalchemy import inspect, MetaData, create_engine, Column, ForeignKey, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import sqltypes

from headers import gen_model_header, gen_photo_column, gen_file_column
from utils import snake_to_pascal
from db_utils import map_pgsql_datatypes, get_display_column

p = inflect.engine()

def gen_models(metadata, inspector):
    """Main function to generate model code."""
    model_code = []
    model_code.extend(gen_model_header())
    model_code.extend(gen_domains(inspector))
    model_code.extend(gen_enums(inspector))
    model_code.extend(gen_tables(metadata, inspector))
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
    base_type = domain["type"]
    BaseType = map_pgsql_datatypes(base_type.lower())
    
    domain_code.append(f"\nclass {domain_name}({BaseType}):")
    
    if domain["default"]:
        domain_code.append(f"    default = {domain['default']}")
    
    if not domain["nullable"]:
        domain_code.append(f"    not_null = True")
    
    for constraint in domain.get("constraints", []):
        domain_code.append(f"    # Constraint: {constraint['name']}")
        domain_code.append(f"    check = '{constraint['check']}'")
    
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
        enum_code.append(f"    {label.upper()} = '{label}'")
    return enum_code

def gen_tables(metadata, inspector):
    """Generate code for database tables."""
    table_code = []
    for table in metadata.sorted_tables:
        table_code.extend(gen_table(table, inspector))
    return table_code

def gen_table(table, inspector):
    """Generate code for a single table."""
    table_code = []
    table_name = table.name
    columns = inspector.get_columns(table_name)
    pks = inspector.get_pk_constraint(table_name)
    fks = inspector.get_foreign_keys(table_name)
    uqs = inspector.get_unique_constraints(table_name)
    table_comment = inspector.get_table_comment(table_name)

    table_class = snake_to_pascal(table_name)
    table_code.append(f"class {table_class}(Model):")
    table_code.append(f'    __tablename__ = "{table_name}"')
    
    if table_comment['text']:
        table_code.append(f'    __doc__ = """{table_comment["text"]}"""')

    table_code.extend(gen_columns(columns, pks, fks, uqs, table_class))
    table_code.extend(gen_relationships(fks, table_name, table_class))
    table_code.extend(gen_check_constraints(inspector, table_name))
    table_code.extend(gen_repr_method(columns))
    
    table_code.append("\n")
    return table_code

def gen_columns(columns, pks, fks, uqs, table_class):
    """Generate code for table columns."""
    column_code = []
    for column in columns:
        column_code.extend(gen_column(column, pks, fks, uqs, table_class))
    return column_code

def gen_column(column, pks, fks, uqs, table_class):
    """Generate code for a single column."""
    column_code = []
    column_name = column["name"]
    column_type = map_pgsql_datatypes(column["type"].compile().lower())
    
    attributes = []
    if column_name in pks["constrained_columns"]:
        attributes.append("primary_key=True")
    
    for fk in fks:
        if column_name == fk["constrained_columns"][0]:
            attributes.append(f"ForeignKey('{fk['referred_table']}.{fk['referred_columns'][0]}')")
    
    if column_name in [uq["column_names"] for uq in uqs]:
        attributes.append("unique=True")
    
    if column["nullable"]:
        attributes.append("nullable=True")
    
    if column["default"]:
        default_value = process_default_value(column["default"])
        if default_value:
            attributes.append(f"default={default_value}")
    
    attributes_str = ", ".join(attributes)
    
    if column_name.endswith('_img') or column_name.endswith('_photo'):
        column_code.append(gen_photo_column(column_name, table_class))
    elif column_name.endswith('_file') or column_name.endswith('_doc'):
        column_code.append(gen_file_column(column_name, table_class))
    else:
        column_code.append(f"    {column_name} = Column({column_type}, {attributes_str})")
    
    return column_code

def gen_relationships(fks, table_name, table_class):
    """Generate code for table relationships."""
    relationship_code = []
    for fk in fks:
        relationship_code.extend(gen_relationship(fk, table_name, table_class))
    return relationship_code

def gen_relationship(fk, table_name, table_class):
    """Generate code for a single relationship."""
    relationship_code = []
    fk_name = fk["constrained_columns"][0]
    if fk_name.endswith('_id_fk'):
        fk_name = fk_name[:-6]
    fk_name = fk_name.split('_fk')[0]
    fk_name = fk_name.split('_id')[0]
    
    referred_table = snake_to_pascal(fk["referred_table"])
    referred_column = fk["referred_columns"][0]
    
    back_ref = f", backref='{table_name}s_{fk_name}'"
    primaryjoin = f", primaryjoin='{table_class}.{fk['constrained_columns'][0]} == {referred_table}.{referred_column}'"
    
    if table_class == referred_table:  # self-referential
        remote_side = f", remote_side=[{referred_column}]"
        foreign_keys = f", foreign_keys=[{fk['constrained_columns'][0]}]"
    else:
        remote_side = ""
        foreign_keys = ""
    
    relationship_code.append(
        f"    {fk_name} = relationship('{referred_table}'{back_ref}{primaryjoin}{remote_side}{foreign_keys})"
    )
    
    return relationship_code

def gen_check_constraints(inspector, table_name):
    """Generate code for table check constraints."""
    constraint_code = []
    check_constraints = inspector.get_check_constraints(table_name)
    
    for cc in check_constraints:
        constraint_name = cc['name']
        sql_expression = cc['sqltext']
        constraint_code.append(
            f"    CheckConstraint('{sql_expression}', name='{constraint_name}')"
        )
    
    return constraint_code

def gen_repr_method(columns):
    """Generate code for the __repr__ method."""
    repr_code = []
    repr_code.append("\n    def __repr__(self):")
    repr_code.append("        return self." + get_display_column([col["name"] for col in columns]))
    return repr_code

def process_default_value(default):
    """Process default value for a column."""
    if default == 'false':
        return 'False'
    elif default == 'true':
        return 'True'
    elif default == 'now()':
        return 'func.now()'
    elif default.startswith('nextval'):
        return None  # Let SQLAlchemy handle autoincrement
    else:
        return f"'{default}'"

# Main execution
if __name__ == "__main__":
    # Example usage
    DATABASE_URI = "postgresql:///your_database_name"
    engine = create_engine(DATABASE_URI)
    metadata = MetaData()
    metadata.reflect(bind=engine)
    inspector = inspect(engine)
    
    model_code = gen_models(metadata, inspector)
    
    # Write the generated code to a file
    with open("generated_models.py", "w") as f:
        f.write("\n".join(model_code))
    
    print("Models generated successfully.")
