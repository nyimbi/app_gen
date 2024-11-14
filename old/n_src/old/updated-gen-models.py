import inflect
from sqlalchemy import inspect, MetaData, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import sqltypes

from headers import gen_model_header, gen_photo_column, gen_file_column

p = inflect.engine()

def gen_models(metadata, inspector):
    model_code = []
    enum_names = []  # To keep track of enums so that we don't repeat

    # Use the new optimized header generation
    model_code.extend(gen_model_header())

    # Generate Domains
    model_code.extend(gen_domains(inspector))

    # Generate Enums
    model_code.extend(gen_enums(inspector))

    # Generate Models
    for t in metadata.sorted_tables:
        table = t.name
        column_names_list = []
        cols = inspector.get_columns(table)
        pks = inspector.get_pk_constraint(table)
        fks = inspector.get_foreign_keys(table)
        uqs = inspector.get_unique_constraints(table)
        cck = inspector.get_check_constraints(table)
        t_comment = inspector.get_table_comment(table)  # Table Comment

        table_class = snake_to_pascal(table)
        model_code.append(f"class {table_class}(Model):")
        model_code.append(f'    __tablename__ = "{table}"')
        model_code.append(f'    # __table_args__ = ( ) # tuple')
        if t_comment['text']:
            model_code.append(f'    __doc__ = """{t_comment["text"]}"""')

        for col in cols:
            column_names_list.append(col["name"])
            column_def = gen_column(col, pks, fks, uqs, table_class)
            model_code.extend(column_def)

        # Generate relationships
        model_code.extend(gen_relationships(fks, table, table_class))

        # Generate table level check constraints
        model_code.extend(gen_check_constraints(cck))

        # Generate __repr__ method
        model_code.extend(gen_repr_method(column_names_list))

        model_code.append("\n ### \n\n")

    return model_code

def gen_domains(inspector):
    domain_code = []
    domain_code.append("# Domains defined in the database")
    domains = inspector.get_domains()

    for domain in domains:
        domain_name = domain["name"]
        base_type = domain["type"]
        not_null = domain["nullable"]
        default = domain["default"]
        constraints = domain["constraints"]
        BaseType = map_pgsql_datatypes(base_type.lower())

        domain_code.append(f"\nclass {domain_name}({BaseType}):  # BaseType should be replaced with the actual base type")

        if default:
            domain_code.append(f"    default = {default}")

        if not_null:
            domain_code.append(f"    not_null = True")

        for constraint in constraints:
            constraint_name = constraint["name"]
            constraint_check = constraint["check"]
            domain_code.append(f"    # Constraint: {constraint_name}")
            domain_code.append(f"    check = '{constraint_check}'")

    domain_code.append("\n ")
    return domain_code

def gen_enums(inspector):
    enum_code = []
    enum_code.append('# Enums defined in the database')
    enums = inspector.get_enums()
    for en in enums:
        enum_code.append(f"\nclass {en['name']}(enum.Enum):")
        for label in en["labels"]:
            enum_code.append(f"   {label.upper()} = '{label}'")
    enum_code.append("\n\n")
    return enum_code

def gen_column(col, pks, fks, uqs, table_class):
    column_def = []
    column_name = col["name"]
    column_type = col["type"].compile()
    column_type = map_pgsql_datatypes(column_type.lower())

    attributes = []
    if column_name in pks["constrained_columns"]:
        attributes.append("primary_key=True")

    for fk in fks:
        if column_name == fk["constrained_columns"][0]:
            fkey = f"{fk['referred_table']}.{fk['referred_columns'][0]}"
            attributes.append(f"ForeignKey('{fkey}')")

    if column_name in [uq["column_names"] for uq in uqs]:
        attributes.append("unique=True")

    if col["nullable"]:
        attributes.append("nullable=True")

    if col["default"]:
        default = process_default(col["default"])
        if default:
            attributes.append(f"default={default}")

    if col["comment"]:
        attributes.append(f'comment="{col["comment"]}"')

    attributes_str = ", ".join(attributes)

    if column_name.endswith('_img') or column_name.endswith('_photo'):
        column_def.append(gen_photo_column(column_name, table_class))
    elif column_name.endswith('_file') or column_name.endswith('_doc'):
        column_def.append(gen_file_column(column_name, table_class))
    else:
        column_def.append(f"    {column_name} = Column({column_type}, {attributes_str})")

    return column_def

def gen_relationships(fks, table, table_class):
    relationship_code = []
    for fk in fks:
        fk_name = fk["constrained_columns"][0].split('_fk')[0].split('_id')[0]
        referred_table = snake_to_pascal(fk["referred_table"])
        referred_column = fk["referred_columns"][0]
        
        back_ref = f", backref='{table}s_{fk_name}'"
        pjoin = f", primaryjoin='{table_class}.{fk['constrained_columns'][0]} == {referred_table}.{referred_column}'"
        
        if table_class == referred_table:  # self-referential
            remote_side = f", remote_side=[{referred_column}]"
            foreign_keys = f", foreign_keys=[{fk['constrained_columns'][0]}]"
        else:
            remote_side = ""
            foreign_keys = ""
        
        relationship_code.append(
            f"    {fk_name} = relationship('{referred_table}'{back_ref}{pjoin}{remote_side}{foreign_keys})"
        )
    
    return relationship_code

def gen_check_constraints(cck):
    constraint_code = []
    for cc in cck:
        constraint_name = cc['name']
        sql_expression = cc['sqltext']
        constraint_code.append(
            f"    CheckConstraint('{sql_expression}', name='{constraint_name}')"
        )
    return constraint_code

def gen_repr_method(column_names_list):
    repr_code = []
    repr_code.append("\n    def __repr__(self):")
    repr_code.append("       return self." + get_display_column(column_names_list))
    return repr_code

def process_default(default):
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

# Utility functions
def snake_to_pascal(string):
    return ''.join(word.capitalize() for word in string.split('_'))

def map_pgsql_datatypes(datatype):
    # Implement your datatype mapping logic here
    pass

def get_display_column(column_names_list):
    # Implement your display column selection logic here
    pass

