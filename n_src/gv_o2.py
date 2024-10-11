import inflect
import argparse
from typing import Any, Dict, List
import math
import sqlalchemy as sa
from sqlalchemy import Boolean, Date, DateTime, Enum, Float, Integer, Numeric, String, Text, Time, ForeignKey, Table, inspect
from sqlalchemy.orm import RelationshipProperty
from flask import g, flash, redirect, url_for, session, make_response, render_template
from utils import snake_to_pascal, snake_to_words, pascal_to_words
from view_utils import get_view_icon
import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField
import csv
from io import StringIO
from flask_appbuilder.forms import DynamicForm
import logging

# Initialize inflect engine and logger
p = inflect.engine()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global list for registering views
REGISTERED_VIEWS = []  # Keep track of generated views for registration


# Beautiful custom widgets for enhanced UI
class BeautifulListWidget(ListThumbnail):
    template = 'beautiful_list.html'


class BeautifulFormWidget(FormVerticalWidget):
    template = 'beautiful_form.html'


# Base Wizard View
class WizardView(BaseView):
    default_view = 'step1'

    def _init_steps(self):
        self.steps = {}
        for step in range(1, self.total_steps + 1):
            step_name = f'step{step}'
            self.steps[step_name] = getattr(self, step_name)

    def is_step_complete(self, step):
        return session.get(f'{self.__class__.__name__}_step{step}_complete', False)

    def mark_step_complete(self, step):
        session[f'{self.__class__.__name__}_step{step}_complete'] = True

    def get_progress(self):
        completed_steps = sum(self.is_step_complete(step) for step in range(1, self.total_steps + 1))
        return (completed_steps / self.total_steps) * 100

    @expose('/reset')
    def reset(self):
        for step in range(1, self.total_steps + 1):
            session.pop(f'{self.__class__.__name__}_step{step}_complete', None)
        flash('Your progress has been reset. Start again from the beginning!', 'info')
        return redirect(url_for(f'.step1'))

    def render_wizard(self, step, form, step_description):
        try:
            return self.render_template(
                'wizard.html',
                form=form,
                progress=self.get_progress(),
                current_step=step,
                total_steps=self.total_steps,
                step_description=step_description
            )
        except TemplateNotFound:
            flash('Wizard template not found. Please check your templates.', 'danger')
            return redirect(url_for(f'.step{step}'))

    def submit_wizard(self):
        combined_data = {}
        for step in range(1, self.total_steps + 1):
            step_data = session.get(f'{self.__class__.__name__}_step{step}_data', {})
            combined_data.update(step_data)

        # Create new record
        new_entry = self.datamodel.obj()
        for key, value in combined_data.items():
            setattr(new_entry, key, value)
        self.datamodel.add(new_entry)

        # Clean session data
        for step in range(1, self.total_steps + 1):
            session.pop(f'{self.__class__.__name__}_step{step}_data', None)

        logger.info(f"Wizard completed for {self.__class__.__name__}")
        flash('Wizard completed successfully!', 'success')
        return redirect(url_for('.step1'))


def generate_views(database_uri):
    """
    Generate Flask-AppBuilder views for all tables in the database.

    :param database_uri: SQLAlchemy database URI
    :return: String containing the generated views code
    """
    engine = sa.create_engine(database_uri)
    metadata = sa.MetaData()

    try:
        metadata.reflect(bind=engine)
        logger.info("Successfully connected to the database and reflected the schema.")
    except sa.exc.SQLAlchemyError as e:
        logger.error(f"Error reflecting database schema: {e}")
        return

    inspector = inspect(engine)
    views = []

    # Add necessary imports for Flask-AppBuilder views
    views.extend([
        "from flask_appbuilder import ModelView, MasterDetailView, MultipleView, ModelRestApi",
        "from flask_appbuilder.models.sqla.interface import SQLAInterface",
        "from flask_appbuilder.fieldwidgets import BS3TextFieldWidget, Select2Widget, DatePickerWidget",
        "from flask_appbuilder.actions import action",
        "from flask_appbuilder.baseviews import expose",
        "from flask_appbuilder.charts.views import GroupByChartView",
        "from flask import flash, redirect, url_for, request, session",
        "from .models import *",
        "import datetime",
        "import graphene",
        "from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField",
        "from .view_utils import get_view_icon"
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

    # Generate wizard views
    wizard_views = generate_wizard_views(metadata)
    views.extend(wizard_views)

    # Generate GraphQL views
    graphql_views = generate_graphql_views(metadata)
    views.extend(graphql_views)

    # Generate API views
    api_views = generate_api_views(metadata, inspector)
    views.extend(api_views)

    # Generate chart views
    chart_views = generate_chart_views(metadata, inspector)
    views.extend(chart_views)

    # Add view registration functions
    views.append(generate_view_registration_code())

    return "\n\n".join(views)


def generate_model_view(table, model_name, view_class, inspector, metadata):
    """Generate a ModelView for a table."""
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
        f"    list_columns = {list_columns}",
        f"    show_columns = {show_columns}",
        f"    add_columns = {add_columns}",
        f"    edit_columns = {edit_columns}",
        f"    search_columns = {search_columns}",
        f"    label_columns = {label_columns}",
        "    list_widget = BeautifulListWidget",
        "    edit_widget = BeautifulFormWidget",
        "    add_widget = BeautifulFormWidget",
        "    show_widget = BeautifulFormWidget",
        "    # Custom Actions",
        generate_custom_actions(),
        "    # Automatically Generated Descriptions for Columns",
        generate_description_columns(table, inspector),  # Automatically generate column descriptions
        "    # Form Fields based on Table Structure",
        generate_form_fields(table, metadata),  # Dynamic form field generation
        "    # Handling Foreign Keys and Relationships",
        generate_relationship_fields(table, metadata),  # Handling foreign key and relationship fields
        "    related_views = []",  # You can dynamically inject related views here
        "",
        "    base_order = ('name', 'asc')",  # Default ordering by name, change to any default you want
    ]

    icon = get_view_icon(model_name, 'ModelView')
    REGISTERED_VIEWS.append((view_class, model_name, 'ModelView', icon))

    return "\n".join(view_code)


def generate_wizard_view(table, model_name, step_size=5):
    """Generate a multi-step form wizard view for a table."""
    columns = get_columns(table, 'add')
    num_steps = math.ceil(len(columns) / step_size)  # Default is 5 fields per step

    wizard_view_code = f"""
class {model_name}WizardView(WizardView):
    datamodel = SQLAInterface({model_name})
    total_steps = {num_steps}

    def __init__(self):
        super().__init__()
        self._init_steps()
"""

    for step in range(1, num_steps + 1):
        start_idx = (step - 1) * step_size
        end_idx = min(step * step_size, len(columns))
        step_columns = columns[start_idx:end_idx]

        wizard_view_code += f"""
    @expose('/step{step}', methods=['GET', 'POST'])
    def step{step}(self):
        form = DynamicForm()
"""
        for column in step_columns:
            wizard_view_code += f"        form.{column} = {generate_form_field(table.columns[column.name])}\n"

        wizard_view_code += f"""
        if form.validate_on_submit():
            self.mark_step_complete({step})
            if {step} == {num_steps}:
                return self.submit_wizard()
            else:
                return redirect(url_for('.step{step + 1}'))

        return self.render_wizard({step}, form, 'Step {step}: {", ".join(step_columns)}')
"""

    # Final submission logic
    wizard_view_code += f"""
    def submit_wizard(self):
        combined_data = {{}}
        for step in range(1, self.total_steps + 1):
            step_data = session.get(f'{self.__class__.__name__}_step{step}_data', {{} })
            combined_data.update(step_data)
        new_entry = self.datamodel.obj()
        for key, value in combined_data.items():
            setattr(new_entry, key, value)
        self.datamodel.add(new_entry)

        for step in range(1, self.total_steps + 1):
            session.pop(f'{self.__class__.__name__}_step{step}_data', None)

        flash('Wizard completed successfully!', 'success')
        return redirect(url_for('.step1'))
"""

    REGISTERED_VIEWS.append((f"{model_name}WizardView", model_name, 'WizardView', get_view_icon(model_name, 'WizardView')))
    return wizard_view_code


def generate_graphql_views(metadata):
    """Generate GraphQL views for all tables."""
    graphql_views = []
    query_fields = []

    # Adding GraphQL Types (ObjectType, Connection) and Fields for each table
    for table in metadata.sorted_tables:
        model_name = snake_to_pascal(table.name)

        try:
            # Define the GraphQL ObjectType and Connection for each table
            graphql_views.append(f"""
class {model_name}Object(SQLAlchemyObjectType):
    class Meta:
        model = {model_name}
        interfaces = (graphene.relay.Node,)

class {model_name}Connection(graphene.relay.Connection):
    class Meta:
        node = {model_name}Object
""")

            # Accumulate the field in the Query class
            query_fields.append(f"    all_{table.name} = SQLAlchemyConnectionField({model_name}Connection)")
        except Exception as e:
            logger.error(f"Error while generating GraphQL for table {table.name}: {e}")

    # Defining the main Query class with all accumulated fields
    graphql_views.append(f"""
class Query(graphene.ObjectType):
    node = graphene.relay.Node.Field()
{"\n".join(query_fields)}
""")

    return graphql_views


def generate_custom_actions():
    """Generate common custom actions for views."""

    return """
    @action("delete_all", "Delete All", "Are you sure you want to delete all records?", "fa-trash", multiple=True)
    def delete_all(self, items):
        self.datamodel.delete_all(items)
        flash(f"Deleted {len(items)} records", "success")
        return redirect(request.referrer)

    @action("print", "Print", "Print selected items?", "fa-print", single=False)
    def print_items(self, items):
        return render_template('print_items.html', items=items)

    @action("export_csv", "Export CSV", "Export selected items to CSV?", "fa-file-excel-o", single=False)
    def export_csv(self, items):
        csv_data = self.datamodel.export_as_csv(items)
        response = make_response(csv_data)
        response.headers["Content-Disposition"] = "attachment; filename=export.csv"
        response.headers["Content-Type"] = "text/csv"
        return response

    @action("bookmark", "Bookmark", "Bookmark selected items?", "fa-bookmark", single=False)
    def bookmark_items(self, items):
        for item in items:
            item.is_bookmarked = True
        self.datamodel.bulk_update(items)
        flash(f"Bookmarked {len(items)} items", "success")
        return redirect(request.referrer)

    @action("archive", "Archive", "Archive selected items?", "fa-archive", single=False)
    def archive_items(self, items):
        for item in items:
            item.is_archived = True
        self.datamodel.bulk_update(items)
        flash(f"Archived {len(items)} items", "success")
        return redirect(request.referrer)

    @action("restore", "Restore", "Restore selected items?", "fa-undo", single=False)
    def restore_items(self, items):
        for item in items:
            item.is_archived = False
        self.datamodel.bulk_update(items)
        flash(f"Restored {len(items)} items", "success")
        return redirect(request.referrer)

    @action("clone", "Clone", "Clone selected item?", "fa-clone", single=True)
    def clone_item(self, item):
        new_item = self.datamodel.obj()
        for col in self.list_columns:
            setattr(new_item, col, getattr(item, col))
        self.datamodel.add(new_item)
        flash(f"Cloned item {item}", "success")
        return redirect(request.referrer)

    @action("merge", "Merge", "Merge selected items?", "fa-compress", single=False)
    def merge_items(self, items):
        if isinstance(items, list) and len(items) > 1:
            flash(f"Merged {len(items)} items", "success")
        else:
            flash("Select at least two items to merge", "warning")
        return redirect(request.referrer)

    @action("split", "Split", "Split selected item?", "fa-scissors", single=True)
    def split_item(self, item):
        flash(f"Split item {item}", "success")
        return redirect(request.referrer)

    @action("remind_me", "Remind Me", "Set a reminder for selected items?", "fa-bell", single=False)
    def remind_me(self, items):
        flash(f"Reminder set for {len(items)} items", "success")
        return redirect(request.referrer)
    """


def generate_chart_views(metadata, inspector):
    """
    Generate chart views for suitable tables in the database.

    :param metadata: SQLAlchemy MetaData object
    :param inspector: SQLAlchemy Inspector object
    :return: List of strings containing the generated chart view code
    """
    chart_views = []

    for table in metadata.sorted_tables:
        if is_suitable_for_chart(table):
            chart_views.append(generate_chart_view(table))

    return chart_views


def is_suitable_for_chart(table: Table) -> bool:
    """
    Check if a table is suitable for generating a chart view.

    :param table: SQLAlchemy Table object
    :return: Boolean indicating if the table is suitable for a chart
    """
    # A table is suitable for charts if it contains numeric or date fields
    numeric_columns = [col for col in table.columns if isinstance(col.type, (Integer, Float, Numeric))]
    date_columns = [col for col in table.columns if isinstance(col.type, (Date, DateTime))]

    # If the table has numeric or date columns, it's suitable for charting
    return len(numeric_columns) > 0 or len(date_columns) > 0


def generate_chart_view(table: Table) -> str:
    """
    Generate a chart view for a suitable table.

    :param table: SQLAlchemy Table object
    :return: String containing the generated chart view code
    """
    model_name = snake_to_pascal(table.name)
    chart_type = determine_chart_type(table)
    x_axis = get_suitable_x_axis(table)
    y_axis = get_suitable_y_axis(table)

    chart_view_code = f"""
class {model_name}ChartView(GroupByChartView):
    datamodel = SQLAInterface({model_name})
    chart_title = '{snake_to_words(table.name)} Chart'
    chart_type = '{chart_type}'
    definitions = [
        {{
            'label': '{y_axis} by {x_axis}',
            'group': '{x_axis}',
            'series': ['{y_axis}']
        }}
    ]
"""
    icon = get_view_icon(model_name, 'ChartView')
    REGISTERED_VIEWS.append((f"{model_name}ChartView", model_name, 'ChartView', icon))
    return chart_view_code


def determine_chart_type(table: Table) -> str:
    """
    Determine the most suitable chart type for a table.

    :param table: SQLAlchemy Table object
    :return: String representing the chart type (e.g., 'LineChart' or 'BarChart')
    """
    date_columns = [col for col in table.columns if isinstance(col.type, (Date, DateTime))]

    # If the table contains date columns, prefer line charts for time-series data
    if date_columns:
        return 'LineChart'
    else:
        # Otherwise, default to bar charts
        return 'BarChart'


def get_suitable_x_axis(table: Table) -> str:
    """
    Determine a suitable x-axis for a chart based on the table structure.

    :param table: SQLAlchemy Table object
    :return: String representing the column name for the x-axis
    """
    date_columns = [col.name for col in table.columns if isinstance(col.type, (Date, DateTime))]

    # Prefer date columns for the x-axis if they exist
    if date_columns:
        return date_columns[0]
    else:
        # Otherwise, use the first string or text column
        string_columns = [col.name for col in table.columns if isinstance(col.type, (String, Text))]
        return string_columns[0] if string_columns else table.columns[0].name


def get_suitable_y_axis(table: Table) -> str:
    """
    Determine a suitable y-axis for a chart based on the table structure.

    :param table: SQLAlchemy Table object
    :return: String representing the column name for the y-axis
    """
    numeric_columns = [col.name for col in table.columns if isinstance(col.type, (Integer, Float, Numeric))]

    # Prefer numeric columns for the y-axis
    return numeric_columns[0] if numeric_columns else table.columns[0].name


def generate_view_registration_code():
    """Generate the view registration code."""
    registration_code = ["def register_views(appbuilder):", "    # Register generated views"]
    for view_class, model_name, view_type, icon in REGISTERED_VIEWS:
        registration_code.append(f"    appbuilder.add_view({view_class}, '{model_name}', icon='{icon}', category='Data')")
    return "\n".join(registration_code)


def main():
    parser = argparse.ArgumentParser(description="Generate Flask-AppBuilder views from a database schema.")
    parser.add_argument("--uri", required=True, help="Database URI to connect to")
    parser.add_argument("--output", default="views.py", help="Output file to write the generated views")
    args = parser.parse_args()

    views_code = generate_views(args.uri)

    with open(args.output, "w") as f:
        f.write(views_code)

    print(f"Views generated successfully and written to {args.output}")


if __name__ == "__main__":
    main()
