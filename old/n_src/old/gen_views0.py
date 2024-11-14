import inflect
import argparse
from sqlalchemy import inspect, MetaData
from sqlalchemy.engine import create_engine
from sqlalchemy.sql import sqltypes

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
    view_registrations = []

    # Add necessary imports
    views.extend([
        "from flask_appbuilder import ModelView, MasterDetailView, MultipleView",
        "from flask_appbuilder.models.sqla.interface import SQLAInterface",
        "from flask_appbuilder.fields import AJAXSelectField",
        "from flask_appbuilder.fieldwidgets import Select2AJAXWidget, Select2SlaveAJAXWidget",
        "from flask_appbuilder.actions import action",
        "from flask_appbuilder.security.decorators import has_access",
        "from flask_appbuilder.forms import DynamicForm",
        "from wtforms import StringField",
        "from . import appbuilder, db",
        "from .models import *\n\n"
    ])

    # Generate regular ModelViews
    for table in metadata.sorted_tables:
        model_name = snake_to_pascal(table.name)
        view_class = f"{model_name}View"

        # Skip Flask-AppBuilder system tables
        if model_name.lower().startswith('ab_'):
            continue

        views.append(generate_model_view(table, model_name, view_class, inspector))
        view_registrations.append(f"appbuilder.add_view({view_class}, '{pascal_to_words(model_name)}', icon='fa-table', category='Data')")

    # Generate MasterDetailViews
    master_detail_views = generate_master_detail_views(metadata, inspector)
    views.extend(master_detail_views)

    # Generate MultipleViews
    multiple_views = generate_multiple_views(metadata)
    views.extend(multiple_views)

    # Add view registrations at the end of the file
    views.extend(["\n# View registrations"])
    views.extend(view_registrations)

    return "\n".join(views)



def generate_model_view(table, model_name, view_class, inspector):
    """Generate a comprehensive ModelView for a table."""
    columns = get_columns(table)
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
    view_registrations = []

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
            view_registrations.append(
                f"appbuilder.add_view({view_class}, '{pascal_to_words(parent_model_name)} - {pascal_to_words(child_model_name)}', "
                f"icon='fa-link', category='Master-Detail')"
            )

    master_detail_views.extend(view_registrations)
    return master_detail_views

def generate_multiple_views(metadata):
    """Generate MultipleViews for tables with multiple related tables."""
    multiple_views = []
    view_registrations = []

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
            view_registrations.append(
                f"appbuilder.add_view({view_class}, '{pascal_to_words(model_name)} Multiple', "
                f"icon='fa-cubes', category='Multiple Views')"
            )

    multiple_views.extend(view_registrations)
    return multiple_views


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
