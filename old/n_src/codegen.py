# TODO: Process _img fields in views to make them uploadable
# TODO: when it is all satisfactorily working, make into a python package
# from your_sqlalchemy_module.models import YourTableModel # Adjust this according to your SQLAlchemy model class
# Conventions: PostgreSQL Database
#   - id fields should always be in id serial and called id
#   - Foreign Keys should ALWAYS end in _id_fk
#   - association tables should end in _link, _map or _assoc
#   - Timestamps always default to func.now(), change generated code manually
#   - relationships will always have the foreign key name without the _id_fk
#   - Comments on fields are used to give descriptions in the UI
#
import inflect

p = inflect.engine()

from db_utils import *
import oheaders as headers
from utils import *


def inspect_metadata(database_uri):
    engine = create_engine(database_uri)
    metadata = MetaData()
    metadata.reflect(bind=engine)
    inspector = inspect(engine)
    return metadata, inspector


def gen_models(metadata, inspector):
    model_code = []
    enum_names = []  # To keep track of enums so that we don't repeat
    # Write the models.py header file first
    model_code.extend(headers.gen_model_header())

    # Generate Domains

    def gen_domains(inspector):
        # [{'name': 'topoelement',
        # 'schema': 'topology',
        # 'visible': True,
        # 'type': 'integer[]',
        # 'nullable': True,
        # 'default': None,
        # 'constraints': [{'name': 'dimensions', 'check': 'array_upper(VALUE, 2) IS NULL AND array_upper(VALUE, 1) = 2'},
        # {'name': 'lower_dimension', 'check': 'array_lower(VALUE, 1) = 1'},
        # {'name': 'type_range', 'check': '(VALUE)[2] > 0'}]},
        # {'name': 'topoelementarray', 'schema': 'topology', 'visible': True, 'type': 'integer[]', 'nullable': True, 'default': None, 'constraints': [{'name': 'type_range', 'check': 'array_upper(VALUE, 2) = 2 AND array_upper(VALUE, 3) IS NULL'}]}]

        domain_code = []
        domain_code.append("# Domains defined in the database")
        # Retrieve information about domain types
        domains = inspector.get_domains()
        print(domains)

        for domain in domains:
            domain_name = domain["name"]
            base_type = domain["type"]
            not_null = domain["nullable"]
            visible = domain["visible"]
            default = domain["default"]
            constraints = domain["constraints"]
            BaseType = map_pgsql_datatypes(base_type.lower())

            domain_code.append(
                f"\nclass {domain_name}({BaseType}):  # BaseType should be replaced with the actual base type"
            )

            # Check for default value
            if domain["default"]:
                domain_code.append(f"    default = {domain['default']}")

            # Check for not null constraint
            if not_null:
                domain_code.append(f"    not_null = True")

            # Handling constraints
            for constraint in domain.get("constraints", []):
                constraint_name = constraint["name"]
                constraint_check = constraint["check"]
                domain_code.append(f"    # Constraint: {constraint_name}")
                domain_code.append(f"    check = '{constraint_check}'")

            # domain_code.append('    pass')

        domain_code.append("\n ")
        return domain_code

    model_code.extend(gen_domains(inspector))

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

    model_code.extend(gen_enums(inspector))
    for t in metadata.sorted_tables:
        table = t.name
        cols = inspector.get_columns(table)
        # for col in cols:
        #     if isinstance(col["type"], Enum):
        #         # enum_vals = list(col["type"].enums)
        #         # enum_name = f"{table}{col['name'].capitalize()}Enum"
        #         enum_name = f"{col['name'].capitalize()}"
        #
        #         if enum_name not in enum_names:
        #             model_code.append(f"class {enum_name}(enum.Enum):")
        #             for en_val in enum_vals:
        #                 model_code.append(f"   {en_val.upper()} = '{en_val}'")
        #         enum_names.append(enum_name)
        #         model_code.append("\n\n")

    # Now generate Models
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
        # If the model is an extension of the user
        # if table.startswith('user_'):
        #     model_code.append(f"class {table_class}(User):")
        #     model_code.append(f'    __tablename__ = "ab_user"')
        # else:   # This is the normal path
        model_code.append(f"class {table_class}(Model):")
        model_code.append(f'    __tablename__ = "{table}"')
        model_code.append(f'    # __table_args__ = ( ) # tuple')
        if t_comment['text']:
            model_code.append(f'    __doc__ = """{t_comment["text"]}"""')  # Use the table comment in the docstring

        model_code.append(f'    # class_permission_name = "view"')

        for col in cols:
            # String parts to compose a column definition
            # https://docs.sqlalchemy.org/en/20/core/reflection.html#sqlalchemy.engine.interfaces.ReflectedColumn
            c_pk = "";
            c_fk = "";
            c_autoincrement = "";
            c_comment = "";
            c_computed = "";
            c_ck = ""  # Check constraints
            c_default = "";
            c_dialect_options = "";
            c_identity = "";
            c_column_name = "";
            c_nullable = "";
            c_type = "";
            c_unique = ""

            column_names_list.append(col["name"])

            # check if the column is an enum type
            if isinstance(col["type"], Enum):
                enum_name = col["type"].name
                model_code.append(
                    f"    {col['name']} = Column(Enum({enum_name}), nullable=False)"
                )
            else:
                ctype = col["type"].compile()
                ctype = map_pgsql_datatypes(ctype.lower())

                # First Primary Keys
                if col["name"] in pks["constrained_columns"]:
                    c_pk = ", primary_key=True"

                # The Foreign Keys
                for index, fk in enumerate(fks):
                    if col['name'] == fk["constrained_columns"][0]:
                        # print(col['name'])
                        fkname = fk["name"]
                        referred_table = fk["referred_table"]
                        fktable = snake_to_pascal(referred_table)
                        fkref = fk["referred_columns"][0]
                        fkcol = fk["constrained_columns"][0]
                        pjoin = snake_to_pascal(table) + '.' + fkcol + ' == ' + fktable + '.' + fkref
                        fkey = fk["referred_table"] + "." + fk["referred_columns"][0]

                        # Is this a self-referential column
                        if table == referred_table:  # means it is self-referential
                            c_pk = ""
                            c_fk = f", ForeignKey('{fkey}')"
                        else:
                            c_fk = f", ForeignKey('{fkey}')"
                        break

                # The Unique Keys
                if col["name"] in [uq["column_names"] for uq in uqs]:
                    c_unique = ", unique=True"

                # Finally all the fields from the ReflectedColumn Dictionary
                if col['nullable'] == True:
                    c_nullable = ", nullable=True"
                else:
                    c_nullable = ""  # default behaviour is nullable

                if col['autoincrement'] == True:
                    c_autoincrement = ", autoincrement=True"

                if col["comment"] != None:
                    c_comment = '\n\t\t, comment="""' + col["comment"] + '"""'

                if col['default'] != None:
                    c_default = f", default = {col['default']}"  # Might include sqltext, so we process further
                    if col['default'] == 'false':
                        c_default = ', default=False'
                    elif col['default'] == 'true':
                        c_default = ', default=True'
                    elif col['default'] == 'now()':
                        c_default = ', default=func.now()'
                    elif ":" in col['default']:
                        c_default = ''  # , default = ' + col['default'].split(':')[0]
                    elif col['default'].startswith('nextval'):  # Means it is autoincrement and uses a sequence
                        c_autoincrement = ", autoincrement=True"
                        c_default = ""
                    else:
                        c_default = ''
                # Address the case of a photo/doc/image
                if col["name"].endswith('_img') or col["name"].endswith('_photo'):
                    model_code.append(headers.gen_photo_column(col["name"], table_class))
                        # f"    {col['name']} = Column(ImageColumn(size=(300, 300, True), thumbnail_size=(30, 30, True)))")
                elif col["name"].endswith('_file') or col["name"].endswith('_doc'):
                    model_code.append(headers.gen_file_colum(col["name"], table_class))
                else:
                    model_code.append(
                        f"    {col['name']} = Column({ctype}{c_fk}{c_pk}{c_unique}{c_autoincrement}{c_default}{c_nullable}{c_comment})"
                    )

        # Now generate relationships for all fks
        # constrained_columns, options, referred_columns, referred_schema, referred_table
        # https://docs.sqlalchemy.org/en/20/core/reflection.html#sqlalchemy.engine.interfaces.ReflectedForeignKeyConstraint
        for fk in fks:
            # fkname = fk["name"].split('_id_')[0]
            qsr = ""  # Quote Self Referential Table Name
            fk_ref_table = snake_to_pascal(fk["referred_table"])
            fk_ref_col = fk["referred_columns"][0]
            fkcol = fk["constrained_columns"][0]
            fkname = fkcol
            if fkname.endswith('_id_fk'):
                fkname = fkname[:-6]
            fkname = fkcol.split('_fk')[0]
            fkname = fkcol.split('_id')[0]
            pjoin = f", primaryjoin='{snake_to_pascal(table)}.{fkcol} == {fk_ref_table}.{fk_ref_col}'"
            # back_ref = f", backref='{fk_ref_table}{fkname}s'"
            back_ref = f", backref='{table}s_{fkname}'"
            for_keys = f", foreign_keys=[{qsr}{fk_ref_table}.{fk_ref_col}{qsr}]"
            rem_side = ""

            if snake_to_pascal(
                    table) == fk_ref_table:  # We have a self-referential join, so we have to quote the table name
                qsr = "'"
                rem_side = f", remote_side=[{fk_ref_col}]"
                for_keys = f", foreign_keys=[{fkcol}]"

            rel_name = f"{qsr}{fk_ref_table}{qsr}"

            model_code.append(
                f"    {fkname} = relationship({rel_name}{back_ref}{pjoin}{rem_side})"
            )
        # Now write table level check constraints
        if len(cck) > 0:
            for cc in cck:
                constraint_name = cc['name']
                sql_expression = cc['sqltext']

                model_code.append(
                    f"    CheckConstraint('{sql_expression}', name='{constraint_name}')"
                )
        model_code.append("\n    def __repr__(self):")
        model_code.append("       return self." + get_display_column(column_names_list))
        model_code.append("\n ### \n\n")

    # model_gql = gen_graphql(metadata, inspector)    #Test TODO: delete
    # model_code.extend(model_gql)                    #Test TODO: delete
    return model_code  # Test TODO delete
    # return model_code


def gen_views(metadata, inspector):
    views = []
    view_regs = []
    views.extend(headers.gen_view_header())

    def gen_col_names(table):
        col_names = []
        for col in table.columns:
            s = col.name
            if col.name == 'id': continue
            if s.endswith('_id_fk'):
                s = col.name[:-6]  # .split('_id')[0]
                # if s.endswith('_id'):
                #     s = s[:-6]
                col_names.append(f"'{s}'")
                continue
            col_names.append(f"'{s}'")
        # if "name" in col_names:
        #     col_names.remove("name")
        #     col_names.insert(0, "name")
        c = ', '.join(col_names)
        return c

    def gen_labels(table):
        label_names = []
        for col in table.columns:
            s = col.name
            if col.name == 'id': continue
            if s.endswith('_id_fk'):
                s = col.name[:-6]  # .split('_id')[0]
            label_names.append(f"'{s}':'{snake_to_words(s)}'")
        c = ', '.join(label_names)
        return '{' + c + '}'

    def gen_descriptions(table):
        desc = []
        desc.append('    description_columns = {')
        for col in table.columns:
            desc.append(f"        '{col.name}' : '{col.comment}',")
        desc.append('    }')
        return desc

    def gen_titles(table):
        titles = []
        titles.append(f"    list_title = 'List {snake_to_words(table.name)}'")  # title()
        titles.append(f"    show_title = 'Show {snake_to_words(table.name)}'")
        titles.append(f"    edit_title = 'Edit {snake_to_words(table.name)}'")
        titles.append(f"    add_title  = 'Add {snake_to_words(table.name)}'")
        titles.append(f' ')
        titles.append(f"    list_columns = [{gen_col_names(table)}]")
        titles.append(f"    # show_columns = [{gen_col_names(table)}]")
        titles.append(f"    # edit_columns = [{gen_col_names(table)}]")
        titles.append(f"    add_columns = [{gen_col_names(table)}]")
        titles.append(f"    # search_columns = [{gen_col_names(table)}]")
        titles.extend(gen_descriptions(table))

        titles.append(f"    # list_exclude_columns = [{gen_col_names(table)}]")
        titles.append(f"    # show_exclude_columns = [{gen_col_names(table)}]")
        titles.append(f"    # edit_exclude_columns = [{gen_col_names(table)}]")
        titles.append(f"    # add_exclude_columns = [{gen_col_names(table)}]")
        titles.append(f"    # search_exclude_columns = [{gen_col_names(table)}]")

        titles.append(f"    # order_columns = [{gen_col_names(table)}]")
        titles.append(f"    # add_columns = [{gen_col_names(table)}]")
        titles.append(f"    # add_columns = [{gen_col_names(table)}]")
        titles.append(f"    # add_columns = [{gen_col_names(table)}]")
        titles.append(f"    ")
        titles.append(f"    label_columns = {gen_labels(table)}")
        # titles.append(f"    ")
        # titles.append(f"    ")
        # titles.append(f"    ")
        titles.append(
            f"    # base_filters = [['created_by', FilterEqualFunction, get_user],['name', FilterStartsWith, 'a']]")
        titles.append(f'    # base_order = ("name", "asc")')
        # titles.append(f"    ")
        # titles.append(f"    ")
        # titles.append(f"    ")
        # titles.append(f"    ")
        # titles.append(f"    ")
        # titles.append(f"    ")
        titles.append(f'    # page_size = 100 ')
        return titles

    # Generate ModelViews for all tables
    for table in metadata.sorted_tables:
        model_name = snake_to_pascal(table.name)  # .capitalize()
        # Ignore flask-appbuilder system tables
        if model_name.lower().startswith('ab_'):
            continue
        view_class = model_name+'ModelView'
        views.append(f'class {view_class}(ModelView):')
        views.append(f'    datamodel = SQLAInterface({model_name})')
        c = gen_col_names(table)
        views.extend(gen_titles(table))
        views.append(f'#    list_columns = [{c}]')
        view_regs.append(
            f'appbuilder.add_view({view_class}, "{pascal_to_words(model_name)}", icon="fa-folder-open-o", category="Setup")\n')

    # Generate MasterDetailView for tables with foreign keys
    for table in metadata.sorted_tables:
        mviews = set()
        for fk in table.foreign_keys:
            parent_table = fk.column.table.name
            parent_model_name = snake_to_pascal(parent_table)  # .capitalize()
            child_model_name = snake_to_pascal(fk.parent.table.name)  # .capitalize()
            detail_view_name = f'{child_model_name}ModelView'

            # Generate a unique master-detail view class name
            master_detail_view_name = f'{parent_model_name}_{child_model_name}MasterDetailView'
            if master_detail_view_name not in mviews:
                views.append(f'class {master_detail_view_name}(MasterDetailView):')
                views.append(f'    datamodel = SQLAInterface({parent_model_name})')
                views.append(f'    related_views = [{detail_view_name}]')
                views.append(f"    show_template = 'appbuilder/general/model/show_cascade.html'")
                views.append('')
                view_regs.append(
                    f'appbuilder.add_view({master_detail_view_name}, "{pascal_to_words(parent_model_name)}", icon="fa-folder-open-o", category="Review")\n')
                mviews.add(master_detail_view_name)

    # Generate MultipleViews for tables that have multiple Foreign Keys
    # This needs to be re-examined
    mviews = set()
    for table in metadata.sorted_tables:
        related_views = set()
        child_model_name = snake_to_pascal(table.name)
        for fk in table.foreign_keys:
            parent_table = fk.column.table.name
            parent_model_name = snake_to_pascal(parent_table)
            # child_model_name = fk.parent.table.name.capitalize()
            detail_view_name = f'{parent_model_name}ModelView'
            related_views.add(detail_view_name)

        # If there are multiple foreign keys, create a MultipleView
        if len(related_views) > 1:
            multiple_view_name = f'{parent_model_name}MultipleView'
            if multiple_view_name not in mviews:
                views.append(f'class {multiple_view_name}(MultipleView):')
                views.append(f'    datamodel = SQLAInterface({parent_model_name})')
                views.append(f'    views = [{", ".join(related_views)}]')
                views.append('')
                # view_regs.append(
                view_regs.append(
                    f'appbuilder.add_view({multiple_view_name}, "{pascal_to_words(parent_model_name)}", icon="fa-folder-open-o", category="Inspect")\n')
                mviews.add(multiple_view_name)

    views.extend(view_regs)
    views.append(headers.VIEW_FILE_FOOTER)
    return views


def gen_api(metadata, inspector):
    api_code = []
    api_code.extend(headers.gen_api_header())
    for t in metadata.sorted_tables:
        table = t.name
        table_class = snake_to_pascal(table)
        api_code.append(f"\nclass {table_class}Api(ModelRestApi):")
        api_code.append(f'    resource = "{table}"')
        api_code.append(f'    datamodel = SQLAInterface({table_class})')
        api_code.append(f'    allow_browser_login = True')
        api_code.append(' ')
        api_code.append(f'appbuilder.add_api({table_class}Api)\n\n')

    return api_code


def gen_graphql(metadata, inspector):
    gql_code = []
    gql_hdr = []
    gql_code.append('')
    query_code = []

    query_code.append(headers.GQL_QUERY_HDR)
    for t in metadata.sorted_tables:
        exclude_fields = []
        table = t.name
        # Find excluded fields
        for col in inspector.get_columns(table):
            if col["name"].endswith('_img'):
                exclude_fields.append('"' + col["name"] + '"')
        gql_code.append(headers.gen_gql_class(snake_to_pascal(table), ', '.join(exclude_fields)))
        query_code.append(headers.gen_gql_query(table))
        cols = inspector.get_columns(table)
        for col in cols:
            if isinstance(col["type"], Enum):
                enum_name = col["type"].name
                enum_vals = list(col["type"].enums)
                gql_code.append(
                    f"    {col['name']} = graphene.Field({enum_name}_gql)"
                )
                gql_hdr.append(
                    f"{enum_name}_gql = graphene.Enum.from_enum({enum_name})"
                )

    gql = []
    gql.append(headers.gen_gql_header())
    gql.extend(gql_hdr)
    gql.extend(gql_code)
    gql.extend(query_code)
    gql.append(headers.GQL_FOOTER)
    return gql


def gen_dbml(metadata, inspector):
    dbml_code = []
    for t in metadata.sorted_tables:
        table = t.name

    pass


def gen_kivy(metadata, inspector):
    kivy_code = []
    kv_screen = []
    python_class = []

    kivy_code.append(f"#:kivy 1.9.0")
    kivy_code.append(f"#:import fa_icon kivymd.icon_definitions.md_icons ")


    for t in metadata.sorted_tables:
        table_name = t.name.strip().lower().replace(" ", "_")

        cols = inspector.get_columns(table_name)
        column_names_list = []
        cols = inspector.get_columns(table_name)
        pks = inspector.get_pk_constraint(table_name)
        fks = inspector.get_foreign_keys(table_name)
        uqs = inspector.get_unique_constraints(table_name)
        cck = inspector.get_check_constraints(table_name)
        t_comment = inspector.get_table_comment(table_name)  # Table Comment

        kivy_code.append(f"<{snake_to_pascal(table_name)}Screen>:")
        kivy_code.append(f"    id: {table_name}")
        kivy_code.append(f"    name: '{table_name}'")
        kivy_code.append(f"    title: '{snake_to_pascal(table_name)}'")
        kivy_code.append(f"         MDBoxLayout:")
        kivy_code.append(f"             id: {table_name}_main_layout")
        kivy_code.append(f"             orientation:'vertical'")
        kivy_code.append(f"             MDTopAppBar:")
        kivy_code.append(f"                 title: 'Navigate {table_name}'")
        kivy_code.append(f"                 elevation: 10")
        kivy_code.append(f"                 left_action_items: [['arrow-left', lambda x: app.switch_to_screen('home')]]")
        kivy_code.append(f"                 right_action_items: [['home', lambda x: app.switch_to_screen('dashboard')]]")
        kivy_code.append(f"             MDBoxLayout:")
        kivy_code.append(f"                 id: {table_name}_table_layout")
        kivy_code.append(f"                 orientation:'vertical'")
        kivy_code.append(f"                 size_hint_y: None")
        kivy_code.append(f"                 height: self.minimum_height")
        kivy_code.append(f"                 padding: dp(10)")
        kivy_code.append(f"                 spacing: dp(10)")
        kivy_code.append(f"                     MDLabel:")
        kivy_code.append(f"                         text: ''")
        kivy_code.append(f"                     MDTextInput:")



        python_class.append(f"class {snake_to_pascal(table_name)}Screen(MDScreen):")
        python_class.append(f"    def __init__(self, **kwargs):")
        python_class.append(f"        super().__init__(**kwargs)")
        python_class.append(f"        self.app = App.get_running_app()")
        python_class.append(f"        self.app.root.ids.main_screen_manager.add_widget(self)")
        python_class.append(f"        self.app.root.ids.main_screen_manager.current = '{table_name}'")
        python_class.append(f"        self.app.root.ids.main_screen_manager.ids.{table_name}.ids.table.data = []")
        python_class.append(
            f"        self.app.root.ids.main_screen_manager.ids.{table_name}.ids.table.refresh_from_data_and_headers()")
        python_class.append(
            f"        self.app.root.ids.main_screen_manager.ids.{table_name}.ids.table.bind(on_row_press=self.on_row_press)")
        python_class.append(
            f"        self.app.root.ids.main_screen_manager.ids.{table_name}.ids.table.bind(on_row_release=self.on_row_release)")
        python_class.append(
            f"        self.app.root.ids.main_screen_manager.ids.{table_name}.ids.table.bind(on_row_double_tap=self.on_row_double_tap)")
        python_class.append(
            f"        self.app.root.ids.main_screen_manager.ids.{table_name}.ids.table.bind(on_row_long_press=self.on_row_long_press)")
        python_class.append(
            f"        self.app.root.ids.main_screen_manager.ids.{table_name}.ids.table.bind(on_row_release=self.on_row_release)")
        python_class.append(f"    def on_row_press(self, table, row):\n")
        python_class.append(f"        print('on_row_press', row.text)")
        python_class.append(f"")
        python_class.append(f"    def on_row_release(self, table, row):\n")
        python_class.append(f"        print('on_row_release', row.text)")
        python_class.append(f"")
        python_class.append(f"    def on_row_double_tap(self, table, row):\n")
        python_class.append(f"        print('on_row_double_tap', row.text)")
        python_class.append(f"")
        python_class.append(f"    def on_row_long_press(self, table, row):\n")
        python_class.append(f"        print('on_row_long_press', row.text)")
        python_class.append(f"")
        python_class.append(f"    def submit(self):\n")
        python_class.append(f"        # Implement submission logic here\n")
        python_class.append(f"        print('submit')")
        python_class.append(f"        pass")
        python_class.append(f"")
        python_class.append(f"")
        python_class.append(f"")












    for table_name, table in metadata.tables.items():
        form_code = f"# Form for {table_name}\n"
        form_code += f"class {table_name}Form(BoxLayout):\n"
        form_code += f"    orientation: 'vertical'\n"

        for column_name in table.columns.keys():
            form_code += f"    Label:\n"
            form_code += f"        text: '{column_name}'\n"
            form_code += f"    TextInput:\n"
            form_code += f"        hint_text: 'Enter {column_name}'\n"
            form_code += f"\n"

        kivy_code.append(form_code)

    return kivy_code


if __name__ == '__main__':
    # DATABASE_URI = 'postgresql://username:password@localhost:5432/mydatabase'
    DATABASE_URI = "postgresql:///kujatmp"
    metadata, inspector = inspect_metadata(DATABASE_URI)

    # m = gen_models(metadata, inspector)
    write_file('gen/models.py', gen_models(metadata, inspector))

    # a = gen_api(metadata, inspector)
    write_file('gen/apis.py', gen_api(metadata, inspector))

    # v = gen_views(metadata, inspector)
    write_file('gen/views.py', gen_views(metadata, inspector))
    write_file('gen/gql.py', gen_graphql(metadata, inspector))
