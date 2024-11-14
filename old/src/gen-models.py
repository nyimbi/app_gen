import inflect
from sqlalchemy import inspect, MetaData, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import sqltypes

p = inflect.engine()

def gen_models(metadata, inspector):
    model_code = []
    model_code.extend(gen_model_header())
    model_code.extend(gen_domains(inspector))
    model_code.extend(gen_enums(inspector))
    model_code.extend(gen_tables(metadata, inspector))
    return model_code

def gen_model_header():
    return headers.gen_model_header()

def gen_domains(inspector):
    domain_code = ["# Domains defined in the database"]
    domains = inspector.get_domains()
    
    for domain in domains:
        domain_code.extend(gen_domain(domain))
    
    domain_code.append("\n ")
    return domain_code

def gen_domain(domain):
    domain_code = []
    domain_name = domain["name"]
    base_type = domain["type"]
    BaseType = map_pgsql_datatypes(base_type.lower())
    
    domain_code.append(f"\nclass {domain_name}({BaseType}):  # BaseType should be replaced with the actual base type")
    
    if domain["default"]:
        domain_code.append(f"    default = {domain['default']}")
    
    if not domain["nullable"]:
        domain_code.append(f"    not_null = True")
    
    for constraint in domain.get("constraints", []):
        constraint_name = constraint["name"]
        constraint_check = constraint["check"]
        domain_code.append(f"    # Constraint: {constraint_name}")
        domain_code.append(f"    check = '{constraint_check}'")
    
    return domain_code

def gen_enums(inspector):
    enum_code = ['# Enums defined in the database']
    enums = inspector.get_enums()
    
    for en in enums:
        enum_code.extend(gen_enum(en))
    
    enum_code.append("\n\n")
    return enum_code

def gen_enum(enum):
    enum_code = []
    enum_code.append(f"\nclass {enum['name']}(enum.Enum):")
    for label in enum["labels"]:
        enum_code.append(f"   {label.upper()} = '{label}'")
    return enum_code

def gen_tables(metadata, inspector):
    table_code = []
    for t in metadata.sorted_tables:
        table_code.extend(gen_table(t, inspector))
    return table_code

def gen_table(table, inspector):
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

    table_code.extend(gen_columns(columns, pks, fks, uqs))
    table_code.extend(gen_relationships(fks, table_name, table_class))
    table_code.extend(gen_constraints(inspector, table_name))
    table_code.extend(gen_repr_method(columns))
    
    table_code.append("\n ### \n\n")
    return table_code

def gen_columns(columns, pks, fks, uqs):
    column_code = []
    for col in columns:
        column_code.extend(gen_column(col, pks, fks, uqs))
    return column_code

def gen_column(col, pks, fks, uqs):
    column_code = []
    col_name = col["name"]
    col_type = map_pgsql_datatypes(col["type"].compile().lower())
    
    attributes = []
    if col_name in pks["constrained_columns"]:
        attributes.append("primary_key=True")
    
    for fk in fks:
        if col_name == fk["constrained_columns"][0]:
            attributes.append(f"ForeignKey('{fk['referred_table']}.{fk['referred_columns'][0]}')")
    
    if col_name in [uq["column_names"] for uq in uqs]:
        attributes.append("unique=True")
    
    if col["nullable"]:
        attributes.append("nullable=True")
    
    if col["default"]:
        default_value = process_default_value(col["default"])
        if default_value:
            attributes.append(f"default={default_value}")
    
    attributes_str = ", ".join(attributes)
    column_code.append(f"    {col_name} = Column({col_type}, {attributes_str})")
    
    return column_code

def gen_relationships(fks, table_name, table_class):
    relationship_code = []
    for fk in fks:
        relationship_code.extend(gen_relationship(fk, table_name, table_class))
    return relationship_code

def gen_relationship(fk, table_name, table_class):
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

def gen_constraints(inspector, table_name):
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
    repr_code = []
    repr_code.append("\n    def __repr__(self):")
    repr_code.append("       return self." + get_display_column([col["name"] for col in columns]))
    return repr_code

def process_default_value(default):
    if default == 'false':
        return 'False'
    elif default == 'true':
        return 'True'
    elif default == 'now()':
        return 'func.now()'
    elif default.startswith('nextval'):
        return None  # Let SQLAlchemy handle autoincrement
    else:
        return f"'{default}'"  # Return as string for other cases

# Utility functions like snake_to_pascal, map_pgsql_datatypes, and get_display_column should be defined elsewhere
