import inflect
import argparse
from typing import Any, Dict, List
from sqlalchemy import inspect, MetaData
from sqlalchemy.engine import create_engine
from sqlalchemy.sql import sqltypes
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy import Boolean, Date, DateTime, Enum, Float, Integer, Numeric, String, Text, Time
from sqlalchemy import Table, ForeignKeyConstraint, MetaData, create_engine, inspect
from flask_appbuilder.fields import AJAXSelectField, QuerySelectField, QuerySelectMultipleField
from flask_appbuilder.fieldwidgets import Select2Widget, Select2ManyWidget
# from flask_appbuilder.fieldwidgets import BS3TextFieldWidget, BS3PasswordFieldWidget, DatePickerWidget, DateTimePickerWidget, Select2Widget, Select2ManyWidget
# from flask_appbuilder.fields import AJAXSelectField, QuerySelectField, QuerySelectMultipleField

from utils import snake_to_pascal, snake_to_words, pascal_to_words

p = inflect.engine()

def generate_views(database_uri):
    """
    Generate Flask-AppBuilder views for all tables in the database.

    :param database_uri: SQLAlchemy database URI
    :return: String containing the generated views code
    """
    engine = create_engine(database_uri)
    metadata = MetaData()
    metadata.reflect(bind=engine)
    inspector = inspect(engine)

    views = []

    # Add necessary imports
    views.extend([
        "from flask_appbuilder import ModelView, MasterDetailView, MultipleView",
        "from flask_appbuilder.models.sqla.interface import SQLAInterface",
        "from flask_appbuilder.fields import AJAXSelectField",
        "from flask_appbuilder.fieldwidgets import Select2AJAXWidget, Select2SlaveAJAXWidget",
        "from flask_appbuilder.actions import action",
        "from flask_appbuilder.security.decorators import has_access",
        "from flask_appbuilder.forms import DynamicForm",
        "from flask_appbuilder.api import ModelRestApi"
        "from wtforms import StringField",
        "from . import appbuilder, db",
        "from .models import *\n\n"
    ])

    # Generate regular ModelViews
    model_views = generate_model_views(metadata, inspector)
    views.extend(model_views)

    # Generate MasterDetailViews
    master_detail_views = generate_master_detail_views(metadata, inspector)
    views.extend(master_detail_views)

    # Generate MultipleViews
    multiple_views = generate_multiple_views(metadata)
    views.extend(multiple_views)

    # Add view registration functions
    views.extend(generate_view_registration_functions())

    return "\n".join(views)

def generate_model_views(metadata, inspector):
    model_views = []
    for table in metadata.sorted_tables:
        model_name = snake_to_pascal(table.name)
        view_class = f"{model_name}View"

        # Skip Flask-AppBuilder system tables
        if table.name.lower().startswith('ab_'):
            continue

        model_views.append(generate_model_view(table, model_name, view_class, inspector))

    return model_views

def generate_model_view(table: Table, model_name: str, view_class: str, inspector: Any, metadata: Any) -> str:
    """Generate a comprehensive ModelView for a table."""
    columns = get_columns(table)
    list_columns = get_columns(table, 'list')
    show_columns = get_columns(table, 'show')
    add_columns = get_columns(table, 'add')
    edit_columns = get_columns(table, 'edit')
    search_columns = get_search_columns(table)
    label_columns = get_label_columns(table)


    view_code = [
        f"class {view_class}(ModelView):",
        f"    datamodel = SQLAInterface({model_name})",
        f"    list_title = '{snake_to_words(table.name)} List'",
        f"    show_title = '{snake_to_words(table.name)} Details'",
        f"    add_title = 'Add {snake_to_words(table.name)}'",
        f"    edit_title = 'Edit {snake_to_words(table.name)}'",
        f"    list_columns = {columns}",
        f"    show_columns = {columns}",
        f"    add_columns = {columns}",
        f"    edit_columns = {columns}",
        f"    list_exclude_columns = []",
        f"    show_exclude_columns = []",
        f"    add_exclude_columns = []",
        f"    edit_exclude_columns = []",
        f"    search_columns = {get_search_columns(table)}",
        f"    label_columns = {get_label_columns(table)}",
        generate_description_columns(table, inspector),
        generate_fieldsets(table),
        generate_show_fieldsets(table),
        generate_add_fieldsets(table),
        generate_edit_fieldsets(table),
        generate_validators(table, inspector),
        "    # Base Order",
        "    # base_order = ('name', 'asc')",
        "",
        "    # Base Filters",
        "    # base_filters = [['name', FilterStartsWith, 'A']]",
        "",
        generate_form_query_rel_fields(table),
        "    # Forms",
        "    # add_form = None",
        "    # edit_form = None",
        "",
        "    # Widgets",
        "    # show_widget = None",
        "    # add_widget = None",
        "    # edit_widget = None",
        "    # list_widget = None",
        "",
        generate_custom_actions(),
        "",
        "    # Form fields",
        "    form_extra_fields = {",
        generate_form_fields(table),
        generate_relationship_fields(table),
        "    }",
        "",
        generate_search_widget(),
        "    # Related Views",
        "    # related_views = []",
        "",
        "    # List Widgets",
        "    # list_template = 'appbuilder/general/model/list.html'",
        "    # list_widget = ListWidget",
        "",
        "    # Show Widget",
        "    # show_template = 'appbuilder/general/model/show.html'",
        "    # show_widget = ShowWidget",
        "",
        "    # Add Widget",
        "    # add_template = 'appbuilder/general/model/add.html'",
        "    # add_widget = FormWidget",
        "",
        "    # Edit Widget",
        "    # edit_template = 'appbuilder/general/model/edit.html'",
        "    # edit_widget = FormWidget",
        "",
        "    # Query Select Fields",
        "    # query_select_fields = {}",
        "",
        "    # Pagination",
        "    # page_size = 10",
        "",
        "    # Inline Forms",
        "    # inline_models = None",
        "",
        "    # Custom Templates",
        "    # list_template = 'my_list_template.html'",
        "    # show_template = 'my_show_template.html'",
        "    # add_template = 'my_add_template.html'",
        "    # edit_template = 'my_edit_template.html'",
        generate_repr_method(table),
        ""
    ]
    return "\n".join(view_code)

def generate_master_detail_views(metadata, inspector):
    """Generate MasterDetailViews for tables with foreign key relationships."""
    master_detail_views = []

    for table in metadata.sorted_tables:
        for fk in table.foreign_keys:
            parent_table = fk.column.table
            parent_model_name = snake_to_pascal(parent_table.name)
            child_model_name = snake_to_pascal(table.name)
            view_class = f"{parent_model_name}{child_model_name}MasterDetailView"

            view_code = [
                f"class {view_class}(MasterDetailView):",
                f"    datamodel = SQLAInterface({parent_model_name})",
                f"    related_views = [{child_model_name}View]",
                f"    list_title = '{snake_to_words(parent_table.name)} with {snake_to_words(table.name)}'",
                f"    show_title = '{snake_to_words(parent_table.name)} Detail'",
                f"    add_title = 'Add {snake_to_words(parent_table.name)}'",
                f"    edit_title = 'Edit {snake_to_words(parent_table.name)}'",
                generate_description_columns(parent_table, inspector),
                generate_fieldsets(parent_table),
                generate_show_fieldsets(parent_table),
                generate_add_fieldsets(parent_table),
                generate_edit_fieldsets(parent_table),
                "",
                "    # Base Order",
                "    # base_order = ('name', 'asc')",
                "",
                "    # Base Filters",
                "    # base_filters = [['name', FilterStartsWith, 'A']]",
                "",
                "    # Forms",
                "    # add_form = None",
                "    # edit_form = None",
                "",
                "    # Widgets",
                "    # show_widget = None",
                "    # add_widget = None",
                "    # edit_widget = None",
                "    # list_widget = None",
                "",
                "    # List Widgets",
                "    # list_template = 'appbuilder/general/model/list.html'",
                "    # list_widget = ListWidget",
                "",
                "    # Pagination",
                "    # page_size = 10",
                "",
                "    # Custom Templates",
                "    # list_template = 'my_list_template.html'",
                "    # show_template = 'my_show_template.html'",
                "    # add_template = 'my_add_template.html'",
                "    # edit_template = 'my_edit_template.html'",
                "",
            ]
            master_detail_views.extend(view_code)

    return master_detail_views

def generate_multiple_views(metadata):
    """Generate MultipleViews for tables with multiple related tables."""
    multiple_views = []

    for table in metadata.sorted_tables:
        related_tables = set()
        for fk in table.foreign_keys:
            related_tables.add(fk.column.table)
        for fk in metadata.tables.values():
            if table in [fk.column.table for fk in fk.foreign_keys]:
                related_tables.add(fk)

        if len(related_tables) > 1:
            model_name = snake_to_pascal(table.name)
            view_class = f"{model_name}MultipleView"
            related_views = [f"{snake_to_pascal(t.name)}View" for t in related_tables]

            view_code = [
                f"class {view_class}(MultipleView):",
                f"    datamodel = SQLAInterface({model_name})",
                f"    views = [{', '.join(related_views)}]",
                "",
                "    # Base Order",
                "    # base_order = ('name', 'asc')",
                "",
                "    # List Widgets",
                "    # list_template = 'appbuilder/general/model/list.html'",
                "    # list_widget = ListWidget",
                "",
                "    # Pagination",
                "    # page_size = 10",
                "",
                "    # Custom Templates",
                "    # list_template = 'my_list_template.html'",
                "",
            ]
            multiple_views.extend(view_code)

    return multiple_views


def generate_api_view(table: Any, model_name: str) -> str:
    """Generate an API view for a table."""
    columns = get_columns(table)
    api_view_code = [
        f"class {model_name}API(ModelRestApi):",
        f"    resource_name = '{snake_to_words(table.name).lower()}'",
        f"    datamodel = SQLAInterface({model_name})",
        f"    list_columns = {columns}",
        f"    show_columns = {columns}",
        f"    add_columns = {[col for col in columns if col != 'id']}",
        f"    edit_columns = {[col for col in columns if col != 'id']}",
        "    # Add any API-specific configuration here",
        ""
    ]
    return "\n".join(api_view_code)

def generate_view_registration_functions():
    """Generate functions for registering different types of views."""
    registration_functions = [
        "def register_model_views():",
        "    # Register regular model views",
        "    for table_name, model_class in db.Model._decl_class_registry.items():",
        "        if isinstance(model_class, type) and issubclass(model_class, db.Model):",
        "            view_class = globals().get(f'{model_class.__name__}View')",
        "            if view_class:",
        "                appbuilder.add_view(view_class, f'{pascal_to_words(model_class.__name__)}', icon='fa-table', category='Data')",
        "",
        "def register_master_detail_views():",
        "    # Register master-detail views",
        "    for name, obj in globals().items():",
        "        if isinstance(obj, type) and issubclass(obj, MasterDetailView):",
        "            appbuilder.add_view(obj, f'{pascal_to_words(name)}', icon='fa-link', category='Master-Detail')",
        "",
        "def register_multiple_views():",
        "    # Register multiple views",
        "    for name, obj in globals().items():",
        "        if isinstance(obj, type) and issubclass(obj, MultipleView):",
        "            appbuilder.add_view(obj, f'{pascal_to_words(name)}', icon='fa-cubes', category='Multiple Views')",
        "",
        "def register_all_views():",
        "    register_model_views()",
        "    register_master_detail_views()",
        "    register_multiple_views()",
        "",
        "# Call this function to register all views",
        "register_all_views()",
        ""
    ]
    return registration_functions



def get_columns(table):
    """Generate list of all columns for a table."""
    return [col.name for col in table.columns]


def get_search_columns(table):
    """Generate list of searchable columns."""
    return [col.name for col in table.columns if isinstance(col.type, (sqltypes.String, sqltypes.Text))]

def get_label_columns(table):
    """Generate dictionary of user-friendly labels for columns."""
    return {col.name: snake_to_words(col.name) for col in table.columns}

def generate_description_columns(table, inspector):
    """Generate description_columns dictionary with column comments as hints."""
    descriptions = {}
    for column in inspector.get_columns(table.name):
        if column['comment']:
            descriptions[column['name']] = column['comment']

    if descriptions:
        return f"    description_columns = {descriptions}"
    else:
        return "    description_columns = {}"

def generate_fieldsets(table):
    """Generate fieldsets for a table."""
    columns = get_columns(table)
    return f"""
    list_fieldsets = [
        ('Summary', {{'fields': {columns}}})
    ]
    """

def generate_show_fieldsets(table):
    """Generate show_fieldsets for a table."""
    columns = get_columns(table)
    return f"""
    show_fieldsets = [
        ('Summary', {{'fields': {columns}}})
    ]
    """

def generate_add_fieldsets(table):
    """Generate add_fieldsets for a table."""
    columns = [col for col in get_columns(table) if col != 'id']
    return f"""
    add_fieldsets = [
        ('Add {snake_to_words(table.name)}', {{'fields': {columns}}})
    ]
    """

def generate_edit_fieldsets(table):
    """Generate edit_fieldsets for a table."""
    columns = [col for col in get_columns(table) if col != 'id']
    return f"""
    edit_fieldsets = [
        ('Edit {snake_to_words(table.name)}', {{'fields': {columns}}})
    ]
    """

def generate_repr_method(table):
    """Generate __repr__ method for the view."""
    display_column = next((col.name for col in table.columns if col.name in ['name', 'title', 'label']), table.columns[0].name)
    return f"""
    def __repr__(self):
        return self.{display_column}
    """

def generate_validators(table: Any, inspector: Any) -> str:
    """Generate form validators based on column constraints."""
    validators = {}
    for column in table.columns:
        column_validators = []
        if not column.nullable and not column.primary_key:
            column_validators.append('validators.DataRequired()')
        if column.unique:
            column_validators.append('validators.Unique()')
        if isinstance(column.type, sqltypes.String) and column.type.length:
            column_validators.append(f'validators.Length(max={column.type.length})')
        if column_validators:
            validators[column.name] = f"[{', '.join(column_validators)}]"

    if validators:
        return f"    validators_columns = {validators}"
    return ""

def generate_form_query_rel_fields(table: Any) -> str:
    """Generate form_query_rel_fields for foreign key relationships."""
    form_query_rel_fields = {}
    for fk in table.foreign_keys:
        referred_table = fk.column.table
        form_query_rel_fields[fk.parent.name] = f"db.session.query({snake_to_pascal(referred_table.name)})"

    if form_query_rel_fields:
        return f"    form_query_rel_fields = {form_query_rel_fields}"
    return ""

# def generate_custom_actions() -> str:
#     """Generate placeholder for custom actions."""
#     return """
#     @action("muldelete", "Delete", "Delete all Really?", "fa-rocket")
#     def muldelete(self, items):
#         if isinstance(items, list):
#             self.datamodel.delete_all(items)
#             self.update_redirect()
#         else:
#             self.datamodel.delete(items)
#         return redirect(self.get_redirect())
#     """

def generate_custom_actions() -> str:
    """Generate placeholders for custom actions including print, export, and bookmark.

    To Use you would typically add them to the class_action_list attribute of your view::

    class YourModelView(ModelView):
        datamodel = SQLAInterface(YourModel)
        class_action_list = ['muldelete', 'print', 'export', 'bookmark']

    """
    return """
    @action("muldelete", "Delete", "Delete all Really?", "fa-trash")
    def muldelete(self, items):
        if isinstance(items, list):
            self.datamodel.delete_all(items)
            self.update_redirect()
        else:
            self.datamodel.delete(items)
        return redirect(self.get_redirect())

    @action("print", "Print", "Print selected items", "fa-print")
    def print_items(self, items):
        if not isinstance(items, list):
            items = [items]

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)

    """

# The rest of your script remains unchanged


def generate_search_widget() -> str:
    """Generate search widget configuration."""
    return """
    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    """

def get_columns(table: Any, purpose: str = 'list') -> List[str]:
    """
    Generate list of columns for a table, handling different column types intelligently.

    :param table: SQLAlchemy Table object
    :param purpose: 'list', 'show', 'add', or 'edit'
    :return: List of column names
    """
    columns = []
    for column in table.columns:
        if purpose in ['add', 'edit'] and column.name == 'id':
            continue
        if isinstance(column.type, Boolean):
            columns.append(column.name)
        elif isinstance(column.type, (String, Text)):
            columns.append(column.name)
        elif isinstance(column.type, (Integer, Float, Numeric)):
            columns.append(column.name)
        elif isinstance(column.type, (Date, DateTime, Time)):
            columns.append(column.name)
        elif isinstance(column.type, Enum):
            columns.append(column.name)
        elif isinstance(column.type, ForeignKey):
            if purpose in ['add', 'edit']:
                columns.append(column.name.replace('_id', ''))
            else:
                columns.append(column.name)
    return columns

def generate_form_fields(table: Any) -> str:
    """Generate form fields with appropriate widgets based on column types."""
    form_fields = []
    for column in table.columns:
        if column.name == 'id':
            continue
        if isinstance(column.type, String):
            if 'password' in column.name:
                form_fields.append(f"    {column.name} = StringField('{column.name.capitalize()}', widget=BS3PasswordFieldWidget())")
            else:
                form_fields.append(f"    {column.name} = StringField('{column.name.capitalize()}', widget=BS3TextFieldWidget())")
        elif isinstance(column.type, Text):
            form_fields.append(f"    {column.name} = TextAreaField('{column.name.capitalize()}', widget=BS3TextFieldWidget())")
        elif isinstance(column.type, Boolean):
            form_fields.append(f"    {column.name} = BooleanField('{column.name.capitalize()}')")
        elif isinstance(column.type, Integer):
            form_fields.append(f"    {column.name} = IntegerField('{column.name.capitalize()}')")
        elif isinstance(column.type, Float):
            form_fields.append(f"    {column.name} = FloatField('{column.name.capitalize()}')")
        elif isinstance(column.type, Numeric):
            form_fields.append(f"    {column.name} = DecimalField('{column.name.capitalize()}')")
        elif isinstance(column.type, Date):
            form_fields.append(f"    {column.name} = DateField('{column.name.capitalize()}', widget=DatePickerWidget())")
        elif isinstance(column.type, DateTime):
            form_fields.append(f"    {column.name} = DateTimeField('{column.name.capitalize()}', widget=DateTimePickerWidget())")
        elif isinstance(column.type, Time):
            form_fields.append(f"    {column.name} = TimeField('{column.name.capitalize()}')")
        elif isinstance(column.type, Enum):
            enum_choices = [(choice, choice) for choice in column.type.enums]
            form_fields.append(f"    {column.name} = SelectField('{column.name.capitalize()}', choices={enum_choices})")
        elif isinstance(column.type, ForeignKey):
            related_model = column.foreign_keys[0].column.table.name
            form_fields.append(f"    {column.name.replace('_id', '')} = QuerySelectField('{column.name.capitalize()}', query_factory=lambda: db.session.query({related_model.capitalize()}), widget=Select2Widget())")
    return "\n".join(form_fields)

# def generate_relationship_fields(table: Any) -> str:
#     """Generate relationship fields using Select2 widgets for foreign key fields."""
#     relationship_fields = []
#     for relationship in table.relationships:
#         if relationship.direction.name == 'MANYTOONE':
#             related_model = relationship.mapper.class_.__name__
#             field_name = relationship.key
#             relationship_fields.append(f"    {field_name} = QuerySelectField('{field_name.capitalize()}', query_factory=lambda: db.session.query({related_model}), widget=Select2Widget())")
#         elif relationship.direction.name == 'MANYTOMANY':
#             related_model = relationship.mapper.class_.__name__
#             field_name = relationship.key
#             relationship_fields.append(f"    {field_name} = QuerySelectMultipleField('{field_name.capitalize()}', query_factory=lambda: db.session.query({related_model}), widget=Select2ManyWidget())")
#     return "\n".join(relationship_fields)


def generate_relationship_fields(table: Table, metadata: Any) -> str:
    """
    Generate relationship fields using Select2 widgets for foreign key fields.

    :param table: SQLAlchemy Table object
    :param metadata: SQLAlchemy MetaData object
    :return: String containing the generated relationship fields
    """
    relationship_fields = []

    for fk in table.foreign_keys:
        related_table = fk.column.table
        related_model = related_table.name.capitalize()
        field_name = fk.parent.name.replace('_id', '')

        relationship_fields.append(
            f"    {field_name} = QuerySelectField('{field_name.capitalize()}', "
            f"query_factory=lambda: db.session.query({related_model}), "
            f"widget=Select2Widget(), "
            f"allow_blank=True)"
        )

    # Check for many-to-many relationships
    for table_name, other_table in metadata.tables.items():
        if is_association_table(other_table):
            if table.name in [fk.column.table.name for fk in other_table.foreign_keys]:
                other_table_name = \
                [fk.column.table.name for fk in other_table.foreign_keys if fk.column.table.name != table.name][0]
                related_model = other_table_name.capitalize()
                field_name = f"{other_table_name.lower()}s"

                relationship_fields.append(
                    f"    {field_name} = QuerySelectMultipleField('{field_name.capitalize()}', "
                    f"query_factory=lambda: db.session.query({related_model}), "
                    f"widget=Select2ManyWidget())"
                )

    if not relationship_fields:
        return "    # No relationship fields found"

    return "\n".join(relationship_fields)


def is_association_table(table: Table) -> bool:
    """
    Check if a table is an association table (for many-to-many relationships).

    :param table: SQLAlchemy Table object
    :return: Boolean indicating if the table is an association table
    """
    if len(table.columns) != 2:
        return False

    return all(isinstance(constraint, ForeignKeyConstraint) for constraint in table.constraints
               if isinstance(constraint, ForeignKeyConstraint))


def main():
    parser = argparse.ArgumentParser(description='Generate Flask-AppBuilder views from database schema.')
    parser.add_argument('--uri', type=str, required=True, help='Database URI')
    parser.add_argument('--output', type=str, default='views.py', help='Output file name')
    args = parser.parse_args()

    views_code = generate_views(args.uri)

    with open(args.output, "w") as f:
        f.write(views_code)

    print(f"Views generated successfully in {args.output}")

if __name__ == '__main__':
    main()
