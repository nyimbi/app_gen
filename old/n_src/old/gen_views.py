import inflect
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
        "from flask_appbuilder import ModelView",
        "from flask_appbuilder.models.sqla.interface import SQLAInterface",
        "from flask_appbuilder.actions import action",
        "from flask_appbuilder.security.decorators import has_access",
        "from . import appbuilder, db",
        "from .models import *\n\n"
    ])

    for table in metadata.sorted_tables:
        model_name = snake_to_pascal(table.name)
        view_class = f"{model_name}View"
        
        # Skip Flask-AppBuilder system tables
        if model_name.lower().startswith('ab_'):
            continue

        views.append(f"class {view_class}(ModelView):")
        views.append(f"    datamodel = SQLAInterface({model_name})")
        views.append(f"    list_title = '{snake_to_words(table.name)} List'")
        views.append(f"    show_title = '{snake_to_words(table.name)} Details'")
        views.append(f"    add_title = 'Add {snake_to_words(table.name)}'")
        views.append(f"    edit_title = 'Edit {snake_to_words(table.name)}'")
        
        list_columns = get_list_columns(table)
        views.append(f"    list_columns = {list_columns}")
        
        label_columns = get_label_columns(table)
        views.append(f"    label_columns = {label_columns}")
        
        search_columns = get_search_columns(table)
        views.append(f"    search_columns = {search_columns}")
        
        show_columns = get_show_columns(table)
        views.append(f"    show_columns = {show_columns}")
        
        add_columns = get_add_columns(table)
        views.append(f"    add_columns = {add_columns}")
        
        edit_columns = get_edit_columns(table)
        views.append(f"    edit_columns = {edit_columns}")
        
        views.append(generate_repr_method(table))
        views.append("")

        # Generate view registration
        view_registrations.append(f"appbuilder.add_view({view_class}, '{pascal_to_words(model_name)}', icon='fa-table', category='Data')")

    # Add view registrations at the end of the file
    views.extend(["\n# View registrations"])
    views.extend(view_registrations)

    return "\n".join(views)

def get_list_columns(table):
    """Generate list of columns for list view."""
    return [col.name for col in table.columns if not col.name.endswith('_id')]

def get_label_columns(table):
    """Generate dictionary of user-friendly labels for columns."""
    return {col.name: snake_to_words(col.name) for col in table.columns}

def get_search_columns(table):
    """Generate list of searchable columns."""
    return [col.name for col in table.columns if isinstance(col.type, (sqltypes.String, sqltypes.Text))]

def get_show_columns(table):
    """Generate list of columns for show view."""
    return [col.name for col in table.columns]

def get_add_columns(table):
    """Generate list of columns for add view."""
    return [col.name for col in table.columns if col.name != 'id' and not col.name.endswith('_id')]

def get_edit_columns(table):
    """Generate list of columns for edit view."""
    return [col.name for col in table.columns if col.name != 'id']

def generate_repr_method(table):
    """Generate __repr__ method for the view."""
    display_column = next((col.name for col in table.columns if col.name in ['name', 'title', 'label']), table.columns[0].name)
    return f"""
    def __repr__(self):
        return self.{display_column}
    """

if __name__ == '__main__':
    DATABASE_URI = "postgresql:///your_database_name"
    views_code = generate_views(DATABASE_URI)
    
    with open('views.py', 'w') as f:
        f.write(views_code)
    
    print("Views generated successfully in views.py")
