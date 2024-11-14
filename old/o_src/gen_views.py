import argparse
import os
import sys
from typing import Dict, List, Any, Tuple, Optional
import yaml
from sqlalchemy import create_engine, MetaData, inspect, Table, Column, ForeignKey, types
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import relationship
import black
import pylint.lint

# Constants for widget imports
WIDGET_IMPORTS = """
from flask_appbuilder.fieldwidgets import (
    BS3TextFieldWidget,
    BS3PasswordFieldWidget,
    BS3TextAreaFieldWidget,
    Select2Widget,
    Select2ManyWidget,
    DatePickerWidget,
    DateTimePickerWidget,
    TimePickerWidget,
    BS3DateTimeFieldWidget,
    ColorPickerWidget,
    FileUploadFieldWidget,
    Select2AJAXWidget,
    Select2SlaveAJAXWidget,
    BS3DateFieldWidget,
    CheckboxWidget,
    BS3FileUploadFieldWidget
)
from flask_appbuilder.forms import JSONField
"""

# Global registry to store all view registrations
view_registry = []

def register_view(view_class: str, name: str, icon: str, category: str):
    view_registry.append({
        'view_class': view_class,
        'name': name,
        'icon': icon,
        'category': category
    })

def load_config(config_file: str) -> Dict[str, Any]:
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

def get_all_relationships(metadata: MetaData) -> Dict[str, List[Dict[str, Any]]]:
    relationships = {}
    for table_name, table in metadata.tables.items():
        relationships[table_name] = get_relationship_info(table)
    return relationships

def get_relationship_info(table: Table) -> List[Dict[str, Any]]:
    relationships = []
    for fk in table.foreign_keys:
        relationships.append({
            'constrained_column': fk.parent.name,
            'referred_table': fk.column.table.name,
            'referred_column': fk.column.name
        })
    return relationships

def get_column_info(table: Table) -> List[Dict[str, Any]]:
    columns = []
    for column in table.columns:
        column_info = {
            'name': column.name,
            'type': str(column.type),
            'nullable': column.nullable,
            'primary_key': column.primary_key,
        }
        columns.append(column_info)
    return columns

def get_widget_for_column(column: Column, table: Table, relationships: Dict[str, List[Dict[str, Any]]]) -> Tuple[str, List[str]]:
    column_type = column.type
    column_name = column.name.lower()

    # Check for foreign key relationships
    for rel in relationships.get(table.name, []):
        if rel['constrained_column'] == column.name:
            return f"Select2AJAXWidget(endpoint='/api/{rel['referred_table'].lower()}/api/column/{rel['referred_column']}')", []

    # Check for specific column names
    if 'password' in column_name:
        return 'BS3PasswordFieldWidget()', ['validators.DataRequired()', 'validators.Length(min=8)']
    elif 'email' in column_name:
        return 'BS3TextFieldWidget()', ['validators.DataRequired()', 'validators.Email()']
    elif 'url' in column_name:
        return 'BS3TextFieldWidget()', ['validators.DataRequired()', 'validators.URL()']
    elif 'color' in column_name:
        return 'ColorPickerWidget()', []

    # Check column types
    if isinstance(column_type, types.String):
        if column_type.length > 200:
            return 'BS3TextAreaFieldWidget()', ['validators.Length(max=65535)']
        return 'BS3TextFieldWidget()', [f'validators.Length(max={column_type.length})']
    elif isinstance(column_type, types.Text):
        return 'BS3TextAreaFieldWidget()', ['validators.Length(max=65535)']
    elif isinstance(column_type, types.Integer):
        return 'BS3TextFieldWidget()', ['validators.NumberRange(min=-2147483648, max=2147483647)']
    elif isinstance(column_type, types.BigInteger):
        return 'BS3TextFieldWidget()', ['validators.NumberRange(min=-9223372036854775808, max=9223372036854775807)']
    elif isinstance(column_type, types.Float):
        return 'BS3TextFieldWidget()', ['validators.NumberRange()']
    elif isinstance(column_type, types.Numeric):
        return 'BS3TextFieldWidget()', ['validators.NumberRange()']
    elif isinstance(column_type, types.Date):
        return 'BS3DateFieldWidget()', ['validators.DataRequired()']
    elif isinstance(column_type, types.DateTime):
        return 'BS3DateTimeFieldWidget()', ['validators.DataRequired()']
    elif isinstance(column_type, types.Time):
        return 'TimePickerWidget()', ['validators.DataRequired()']
    elif isinstance(column_type, types.Boolean):
        return 'CheckboxWidget()', []
    elif isinstance(column_type, types.Enum):
        choices = [(choice, choice) for choice in column_type.enums]
        return f'Select2Widget(choices={choices})', ['validators.DataRequired()']
    elif isinstance(column_type, types.ARRAY):
        return 'Select2ManyWidget()', []
    elif isinstance(column_type, types.JSON):
        return 'JSONField()', []
    elif isinstance(column_type, types.LargeBinary):
        return 'BS3FileUploadFieldWidget()', []
    
    # Default to text field if no specific type is matched
    return 'BS3TextFieldWidget()', []

def get_validators_for_column(column: Column) -> List[str]:
    validators = []
    if not column.nullable:
        validators.append('validators.DataRequired()')
    
    column_type = column.type
    if isinstance(column_type, types.String):
        validators.append(f'validators.Length(max={column_type.length})')
    elif isinstance(column_type, types.Integer):
        validators.append('validators.NumberRange(min=-2147483648, max=2147483647)')
    elif isinstance(column_type, types.BigInteger):
        validators.append('validators.NumberRange(min=-9223372036854775808, max=9223372036854775807)')
    elif isinstance(column_type, (types.Float, types.Numeric)):
        validators.append('validators.NumberRange()')
    
    return validators

def generate_model_view(table: Table, relationships: Dict[str, List[Dict[str, Any]]], config: Dict[str, Any]) -> str:
    columns = get_column_info(table)
    list_columns = [col['name'] for col in columns if not col['primary_key']][:10]
    
    form_fields = {}
    for col in columns:
        if not col['primary_key']:
            widget, extra_validators = get_widget_for_column(col, table, relationships)
            validators = get_validators_for_column(col) + extra_validators
            form_fields[col['name']] = {
                'widget': widget,
                'validators': validators
            }
    
    view_code = f"""
class {table.name}View(ModelView):
    datamodel = SQLAInterface({table.name})
    
    list_columns = {list_columns}

"""
    
    for field, props in form_fields.items():
        view_code += f"    {field} = {props['widget']}\n"
        if props['validators']:
            validators_str = ', '.join(props['validators'])
            view_code += f"    {field}_validators = [{validators_str}]\n"
    
    view_code += """
    add_form = edit_form = show_form = DynamicForm

"""
    
    register_view(f"{table.name}View", table.name, "fa-folder-open-o", "Data")
    
    return view_code

def generate_multiple_view(table: Table, relationships: Dict[str, List[Dict[str, Any]]], config: Dict[str, Any]) -> str:
    related_views = [f"{rel['referred_table']}ModelView" for rel in relationships.get(table.name, [])]
    
    view_code = f"""
class {table.name}MultipleView(MultipleView):
    views = [{', '.join(related_views)}]

"""
    
    register_view(f"{table.name}MultipleView", f"{table.name} Multiple", "fa-folder-open-o", "Multiple")
    
    return view_code

def generate_master_detail_views(table: Table, relationships: Dict[str, List[Dict[str, Any]]], config: Dict[str, Any]) -> str:
    view_code = ""
    for relationship in relationships.get(table.name, []):
        detail_table = relationship['referred_table']
        view_code += f"""
class {table.name}{detail_table}MasterDetailView(MasterDetailView):
    datamodel = SQLAInterface({table.name})
    related_views = [{detail_table}ModelView]

"""
        register_view(f"{table.name}{detail_table}MasterDetailView", f"{table.name} {detail_table} Master Detail", "fa-folder-open-o", "Master Detail")
    
    return view_code

def generate_chart_view(table: Table, config: Dict[str, Any]) -> str:
    numeric_columns = [col for col in table.columns if isinstance(col.type, (types.Integer, types.Numeric))]
    date_columns = [col for col in table.columns if isinstance(col.type, (types.Date, types.DateTime))]
    
    if numeric_columns and date_columns:
        view_code = f"""
class {table.name}ChartView(ChartView):
    datamodel = SQLAInterface({table.name})
    chart_title = '{table.name} Chart'
    label_columns = {table.name}.label_columns
    group_by_columns = ['{date_columns[0].name}']
    definitions = [
        {{
            'group': '{date_columns[0].name}',
            'series': [('{numeric_columns[0].name}', aggregate_avg)]
        }}
    ]

"""
        register_view(f"{table.name}ChartView", f"{table.name} Chart", "fa-bar-chart", "Charts")
        
        return view_code
    return ""

def generate_wizard_view(table: Table, config: Dict[str, Any]) -> str:
    columns = get_column_info(table)
    
    if len(columns) > 8:
        steps = create_wizard_steps(columns)
        view_code = f"""
class {table.name}WizardView(ModelView):
    datamodel = SQLAInterface({table.name})
"""
        
        for i, step in enumerate(steps, 1):
            view_code += f"""
    step{i}_form = DynamicForm
"""
            for column in step:
                view_code += f"    {column['name']} = BS3TextFieldWidget()\n"
        
        view_code += f"""
    form_steps = {{
        'First Step': {[col['name'] for col in steps[0]]},
        'Second Step': {[col['name'] for col in steps[1]] if len(steps) > 1 else []},
        'Third Step': {[col['name'] for col in steps[2]] if len(steps) > 2 else []}
    }}

"""
        register_view(f"{table.name}WizardView", f"{table.name} Wizard", "fa-magic", "Wizards")
        return view_code
    return ""

def create_wizard_steps(columns: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    steps = []
    current_step = []
    for column in columns:
        if not column['primary_key']:
            current_step.append(column)
            if len(current_step) == 5:
                steps.append(current_step)
                current_step = []
    if current_step:
        steps.append(current_step)
    return steps

def generate_report_view(table: Table, config: Dict[str, Any]) -> str:
    columns = get_column_info(table)
    
    view_code = f"""
class {table.name}ReportView(ModelView):
    datamodel = SQLAInterface({table.name})
    report_columns = {[col['name'] for col in columns if not col['primary_key']]}

"""
    register_view(f"{table.name}ReportView", f"{table.name} Report", "fa-files-o", "Reports")
    return view_code

def generate_calendar_view(table: Table, config: Dict[str, Any]) -> str:
    date_columns = [col for col in table.columns if isinstance(col.type, (types.Date, types.DateTime))]
    
    if date_columns:
        view_code = f"""
class {table.name}CalendarView(ModelView):
    datamodel = SQLAInterface({table.name})
    calendar_view = {{
        'start_date': '{date_columns[0].name}',
        'end_date': '{date_columns[-1].name if len(date_columns) > 1 else date_columns[0].name}'
    }}

"""
        register_view(f"{table.name}CalendarView", f"{table.name} Calendar", "fa-calendar", "Calendars")
        return view_code
    return ""

def generate_api_view(table: Table, config: Dict[str, Any]) -> str:
    columns = get_column_info(table)
    
    view_code = f"""
class {table.name}ModelApi(ModelRestApi):
    resource_name = '{table.name.lower()}'
    datamodel = SQLAInterface({table.name})
    allow_browser_login = True

"""
    return view_code

def generate_graphql_schema(table: Table, config: Dict[str, Any]) -> str:
    columns = get_column_info(table)
    
    schema_code = f"""
{table.name} = SQLAlchemyObjectType(
    model={table.name},
    name='{table.name.capitalize()}Type',
    meta={{
        'interfaces': (relay.Node,),
        'connection': Connection,
    }}
)

class {table.name}Connection(Connection):
    class Meta:
        node = {table.name}

class {table.name}Query(graphene.ObjectType):
    {table.name.lower()} = relay.Node.Field({table.name})
    all_{table.name.lower()}s = SQLAlchemyConnectionField({table.name}Connection)

"""
    return schema_code

def generate_caching(config: Dict[str, Any]) -> str:
    cache_config = config.get('caching', {})
    if cache_config.get('enabled', False):
        cache_type = cache_config.get('type', 'simple')
        if cache_type == 'redis':
            cache_code = f"""
from flask_caching import Cache

cache = Cache(app, config={{
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': '{cache_config.get('redis_url', 'redis://localhost:6379/0')}'
}})
"""
        else:
            cache_code = """
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})
"""
        return cache_code
    return ""

def generate_security_manager(config: Dict[str, Any]) -> str:
    security_config = config.get('security', {})
    if security_config.get('custom', False):
        security_code = """
from flask_appbuilder.security.manager import SecurityManager
from flask_appbuilder.security.views import UserDBModelView
from flask_appbuilder.security.views import RoleModelView
from flask_appbuilder.security.registerviews import RegisterUserDBView

class MySecurityManager(SecurityManager):
    userdbmodelview = UserDBModelView
    rolemodelview = RoleModelView
    registeruserdbview = RegisterUserDBView

appbuilder.security_manager_class = MySecurityManager
"""
        return security_code
    return ""

def generate_graphql_view(metadata: MetaData, config: Dict[str, Any]) -> str:
    graphql_code = """
import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField
from graphene.relay import Connection, Node
from flask_graphql import GraphQLView
"""

    schema_definitions = []
    query_fields = []

    for table_name, table in metadata.tables.items():
        schema_definitions.append(generate_graphql_schema(table, config))
        query_fields.append(f"    {table_name.lower()} = relay.Node.Field({table_name})")
        query_fields.append(f"    all_{table_name.lower()}s = SQLAlchemyConnectionField({table_name}Connection)")

    graphql_code += "\n".join(schema_definitions)

    graphql_code += """
class Query(graphene.ObjectType):
"""
    graphql_code += "\n".join(query_fields)

    graphql_code += """

schema = graphene.Schema(query=Query)

app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True  # for having the GraphiQL interface
    )
)
"""

    return graphql_code

def write_view_file(output_dir: str, filename: str, content: str):
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w') as f:
        f.write(content)
    format_and_lint_file(filepath)

def format_and_lint_file(filepath: str):
    # Format the file using black
    black.format_file_in_place(filepath, fast=False, mode=black.FileMode())

    # Lint the file using pylint
    pylint_opts = ['--disable=C0111', filepath]
    pylint.lint.Run(pylint_opts, exit=False)

def generate_views(db_uri: str, output_dir: str, config: Dict[str, Any], single_file: bool):
    engine = create_engine(db_uri)
    metadata = MetaData()
    metadata.reflect(bind=engine)
    inspector = inspect(engine)
    Base = automap_base(metadata=metadata)
    Base.prepare()
    relationships = get_all_relationships(metadata)

    all_views_code = ""

    if single_file:
        all_views_code += """
from flask_appbuilder import ModelView, MultipleView, MasterDetailView, CompactCRUDMixin
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.charts.views import ChartView
from flask_appbuilder.models.group import aggregate_count, aggregate_avg
from flask_appbuilder.views import CompactCRUDMixin
from flask_appbuilder import ModelView
from flask_appbuilder.fieldwidgets import Select2Widget
from flask_appbuilder.actions import action
from flask_appbuilder.forms import DynamicForm
from flask_appbuilder.widgets import FormWidget, ListWidget, ShowWidget
from flask_babel import lazy_gettext as _
from flask_appbuilder.models.sqla.filters import FilterEqualFunction, FilterStartsWith
from flask_appbuilder.models.generic import PSSession
from flask_appbuilder.views import BaseCRUDView
from flask_appbuilder.charts.views import DirectByChartView
from flask_appbuilder.models.group import aggregate_avg
from flask_appbuilder.views import CompactCRUDMixin, ModelView
from flask_appbuilder.fields import AJAXSelectField
from flask_appbuilder.widgets import FormWidget, FormHorizontalWidget, FormInlineWidget, FormVerticalWidget
from wtforms import validators
from . import appbuilder, db
from .models import *
"""
        all_views_code += WIDGET_IMPORTS

    for table_name, table in metadata.tables.items():
        model_view = generate_model_view(table, relationships, config)
        multiple_view = generate_multiple_view(table, relationships, config)
        master_detail_views = generate_master_detail_views(table, relationships, config)
        chart_view = generate_chart_view(table, config)
        wizard_view = generate_wizard_view(table, config)
        report_view = generate_report_view(table, config)
        calendar_view = generate_calendar_view(table, config)
        api_view = generate_api_view(table, config)

        if single_file:
            all_views_code += model_view + multiple_view + master_detail_views + chart_view + wizard_view + report_view + calendar_view + api_view
        else:
            write_view_file(output_dir, f"{table_name}_view.py", model_view + multiple_view + master_detail_views + chart_view + wizard_view + report_view + calendar_view + api_view)

    caching_code = generate_caching(config)
    security_code = generate_security_manager(config)
    graphql_code = generate_graphql_view(metadata, config)

    if single_file:
        all_views_code += caching_code + security_code + graphql_code
        
        # Add view registrations
        all_views_code += "\n# View Registrations\n"
        for view in view_registry:
            all_views_code += f"appbuilder.add_view({view['view_class']}, '{view['name']}', icon='{view['icon']}', category='{view['category']}')\n"
        
        write_view_file(output_dir, "views.py", all_views_code)
    else:
        if caching_code:
            write_view_file(output_dir, "cache_config.py", caching_code)
        if security_code:
            write_view_file(output_dir, "security_manager.py", security_code)
        write_view_file(output_dir, "graphql_view.py", graphql_code)
        
        # Write view registrations to a separate file
        registrations_code = "# View Registrations\n"
        for view in view_registry:
            registrations_code += f"appbuilder.add_view({view['view_class']}, '{view['name']}', icon='{view['icon']}', category='{view['category']}')\n"
        write_view_file(output_dir, "view_registrations.py", registrations_code)

    generate_main_app_file(config, single_file, output_dir)

def generate_main_app_file(config: Dict[str, Any], single_file: bool, output_dir: str):
    if single_file:
        views = ['views']
    else:
        views = [f[:-3] for f in os.listdir(output_dir) if f.endswith('_view.py')]
    
    main_app_code = """
from flask import Flask
from flask_appbuilder import AppBuilder, SQLA
"""

    if single_file:
        main_app_code += "from .views import *\n"
    else:
        for view in views:
            main_app_code += f"from .{view} import *\n"
        main_app_code += "from .view_registrations import *\n"
        main_app_code += "from .graphql_view import *\n"

    main_app_code += """
app = Flask(__name__)
app.config.from_object('config')
db = SQLA(app)
appbuilder = AppBuilder(app, db.session)

db.create_all()
"""

    write_view_file(output_dir, 'app.py', main_app_code)

def main():
    parser = argparse.ArgumentParser(description="Generate Flask-AppBuilder views from a PostgreSQL database")
    parser.add_argument('--db-uri', required=True, help="PostgreSQL database URI")
    parser.add_argument('--output-dir', required=True, help="Output directory for generated views")
    parser.add_argument('--config', required=True, help="Configuration file path")
    parser.add_argument('--single-file', action='store_true', help="Generate all views in a single file")
    args = parser.parse_args()

    config = load_config(args.config)
    generate_views(args.db_uri, args.output_dir, config, args.single_file)

if __name__ == "__main__":
    main()