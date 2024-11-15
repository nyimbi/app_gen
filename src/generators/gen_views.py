import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import yaml
from sqlalchemy import create_engine, MetaData, inspect, Table, Column, ForeignKey, types
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import relationship
from jinja2 import Environment, FileSystemLoader
import black
from oheaders import VIEW_IMPORTS
import pylint.lint
# from flask_appbuilder.fieldwidgets import (
#     BS3TextFieldWidget,
#     BS3PasswordFieldWidget,
#     BS3TextAreaFieldWidget,
#     Select2Widget,
#     Select2ManyWidget,
#     DatePickerWidget,
#     DateTimePickerWidget,
#     TimePickerWidget,
#     BS3DateTimePickerWidget,
#     ColorPickerWidget,
#     FileUploadFieldWidget,
#     Select2AJAXWidget,
#     Select2SlaveAJAXWidget,
#     BS3DateTimeFieldWidget,
#     BS3DateFieldWidget,
#     CheckboxWidget,
#     BS3FileUploadFieldWidget
# )
# from flask_appbuilder.forms import JSONField
from flask_babel import lazy_gettext as _

class ViewGenerator:
    def __init__(self, db_uri: str, output_dir: str, config_file: str, single_file: bool):
        self.db_uri = db_uri
        self.output_dir = output_dir
        self.config = self.load_config(config_file)
        self.engine = create_engine(db_uri)
        self.metadata = MetaData()
        self.metadata.reflect(bind=self.engine)
        self.inspector = inspect(self.engine)
        self.Base = automap_base(metadata=self.metadata)
        self.Base.prepare()
        self.jinja_env = Environment(loader=FileSystemLoader('templates'))
        self.relationships = self.get_all_relationships()
        self.single_file = single_file
        self.all_views_code = ""  # For single file mode

    def load_config(self, config_file: str) -> Dict[str, Any]:
        if config_file:
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        else:
            return {}

    def get_all_relationships(self) -> Dict[str, List[Dict[str, Any]]]:
        relationships = {}
        for table_name in self.metadata.tables:
            relationships[table_name] = self.get_relationship_info(self.metadata.tables[table_name])
        return relationships

    def get_relationship_info(self, table: Table) -> List[Dict[str, Any]]:
        relationships = []
        for fk in table.foreign_keys:
            relationships.append({
                'constrained_column': fk.parent.name,
                'referred_table': fk.column.table.name,
                'referred_column': fk.column.name
            })
        return relationships



    def generate_imports(self):
        imports = VIEW_IMPORTS
        self.all_views_code += imports

    def generate_model_view(self, table: Table):
        template = self.jinja_env.get_template('model_view.py.j2')
        columns = self.get_column_info(table)
        relationships = self.relationships.get(table.name, [])

        list_columns = [col['name'] for col in columns if not col['primary_key']][:10]

        form_fields = {}
        for col in columns:
            if not col['primary_key']:
                widget, extra_validators = self.get_widget_for_column(col, table)
                validators = self.get_validators_for_column(col) + extra_validators
                form_fields[col['name']] = {
                    'widget': widget,
                    'validators': validators
                }

        view_code = template.render(
            table_name=table.name,
            columns=columns,
            relationships=relationships,
            list_columns=list_columns,
            form_fields=form_fields,
            config=self.config,
            single_file=self.single_file
        )

        if self.single_file:
            self.all_views_code += view_code + "\n\n"
        else:
            self.write_view_file(f"{table.name}_model_view.py", view_code)

    def generate_multiple_view(self, table: Table):
        template = self.jinja_env.get_template('multiple_view.py.j2')
        related_views = self.get_related_views(table)

        view_code = template.render(
            table_name=table.name,
            related_views=related_views,
            config=self.config,
            single_file=self.single_file
        )

        if self.single_file:
            self.all_views_code += view_code + "\n\n"
        else:
            self.write_view_file(f"{table.name}_multiple_view.py", view_code)

    def generate_master_detail_views(self, table: Table):
        template = self.jinja_env.get_template('master_detail_view.py.j2')
        for relationship in self.relationships.get(table.name, []):
            detail_table = self.metadata.tables[relationship['referred_table']]
            view_code = template.render(
                master_table=table,
                detail_table=detail_table,
                relationship=relationship,
                config=self.config,
                single_file=self.single_file
            )

            if self.single_file:
                self.all_views_code += view_code + "\n\n"
            else:
                self.write_view_file(f"{table.name}_{detail_table.name}_master_detail_view.py", view_code)

    def generate_chart_view(self, table: Table):
        template = self.jinja_env.get_template('chart_view.py.j2')
        numeric_columns = [col for col in table.columns if isinstance(col.type, (types.Integer, types.Numeric))]
        date_columns = [col for col in table.columns if isinstance(col.type, (types.Date, types.DateTime))]

        if numeric_columns and date_columns:
            view_code = template.render(
                table_name=table.name,
                numeric_columns=numeric_columns,
                date_columns=date_columns,
                config=self.config,
                single_file=self.single_file
            )

            if self.single_file:
                self.all_views_code += view_code + "\n\n"
            else:
                self.write_view_file(f"{table.name}_chart_view.py", view_code)

    def generate_wizard_view(self, table: Table):
        template = self.jinja_env.get_template('wizard_view.py.j2')
        columns = self.get_column_info(table)

        if len(columns) > 8:
            steps = self.create_wizard_steps(columns)
            view_code = template.render(
                table_name=table.name,
                columns=columns,
                steps=steps,
                config=self.config,
                single_file=self.single_file
            )

            if self.single_file:
                self.all_views_code += view_code + "\n\n"
            else:
                self.write_view_file(f"{table.name}_wizard_view.py", view_code)

    def generate_report_view(self, table: Table):
        template = self.jinja_env.get_template('report_view.py.j2')
        columns = self.get_column_info(table)

        view_code = template.render(
            table_name=table.name,
            columns=columns,
            config=self.config,
            single_file=self.single_file
        )

        if self.single_file:
            self.all_views_code += view_code + "\n\n"
        else:
            self.write_view_file(f"{table.name}_report_view.py", view_code)

    def generate_calendar_view(self, table: Table):
        template = self.jinja_env.get_template('calendar_view.py.j2')
        date_columns = [col.name for col in table.columns if isinstance(col.type, (types.Date, types.DateTime))]

        if date_columns:
            view_code = template.render(
                table_name=table.name,
                columns=self.get_column_info(table),
                date_columns=date_columns,
                config=self.config,
                single_file=self.single_file
            )

            if self.single_file:
                self.all_views_code += view_code + "\n\n"
            else:
                self.write_view_file(f"{table.name}_calendar_view.py", view_code)


    def get_column_info(self, table: Table) -> List[Dict[str, Any]]:
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

    def get_widget_for_column(self, column: Column, table: Table) -> Tuple[str, List[str]]:
        column_type = column['type']
        column_name = column['name'].lower()

        # Check for foreign key relationships
        for rel in self.relationships.get(table.name, []):
            if rel['constrained_column'] == column['name']:
                return f"Select2AJAXWidget(endpoint='/api/{rel['referred_table'].lower()}/api/column/{rel['referred_column']}')", []

        # Check for specific column names
        if 'password' in column_name:
            return 'BS3PasswordFieldWidget()', []
        elif 'email' in column_name:
            return 'BS3TextFieldWidget()', ['Email()']
        elif 'url' in column_name:
            return 'BS3TextFieldWidget()', ['URL()']
        elif 'color' in column_name:
            return 'ColorPickerWidget()', []

        # Check column types
        if isinstance(column_type, types.String):
            if column_type.length > 200:
                return 'BS3TextAreaFieldWidget()', []
            return 'BS3TextFieldWidget()', []
        elif isinstance(column_type, types.Text):
            return 'BS3TextAreaFieldWidget()', []
        elif isinstance(column_type, types.Integer):
            return 'BS3TextFieldWidget()', ['IntegerValidator()']
        elif isinstance(column_type, types.Numeric):
            return 'BS3TextFieldWidget()', ['NumberValidator()']
        elif isinstance(column_type, types.Date):
            return 'BS3DateFieldWidget()', []
        elif isinstance(column_type, types.DateTime):
            return 'BS3DateTimeFieldWidget()', []
        elif isinstance(column_type, types.Time):
            return 'TimePickerWidget()', []
        elif isinstance(column_type, types.Boolean):
            return 'CheckboxWidget()', []
        elif isinstance(column_type, types.Enum):
            choices = [(choice, choice) for choice in column_type.enums]
            return f'Select2Widget(choices={choices})', []
        elif isinstance(column_type, types.ARRAY):
            return 'Select2ManyWidget()', []
        elif isinstance(column_type, types.JSON):
            return 'JSONField()', []
        elif isinstance(column_type, types.LargeBinary):
            return 'BS3FileUploadFieldWidget()', []

        # Default to text field if no specific type is matched
        return 'BS3TextFieldWidget()', []

    def get_validators_for_column(self, column: Column) -> List[str]:
        validators = []
        if not column['nullable']:
            validators.append('DataRequired()')

        column_type = column['type']
        if isinstance(column_type, types.String):
            validators.append(f'Length(max={column_type.length})')
        elif isinstance(column_type, (types.Integer, types.Numeric)):
            validators.append('NumberRange()')

        return validators

    def get_related_views(self, table: Table) -> List[str]:
        related_views = []
        for relationship in self.relationships.get(table.name, []):
            related_views.append(f"{relationship['referred_table']}ModelView")
        return related_views

    def create_wizard_steps(self, columns: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
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

    def write_view_file(self, filename: str, content: str):
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        self.format_and_lint_file(filepath)

    def format_and_lint_file(self, filepath: str):
        # Format the file using black
        path = Path(filepath)
        black.format_file_in_place(path, fast=False, mode=black.FileMode())

        # Lint the file using pylint
        pylint_opts = ['--disable=C0111', filepath]
        pylint.lint.Run(pylint_opts, exit=False)

    def generate_main_app_file(self):
        template = self.jinja_env.get_template('main_app.py.j2')
        if self.single_file:
            views = ['views']
            table_names = [table.name for table in self.metadata.tables.values()]
        else:
            views = [f[:-3] for f in os.listdir(self.output_dir) if f.endswith('_view.py')]
            table_names = []

        content = template.render(
            views=views,
            table_names=table_names,
            config=self.config,
            single_file=self.single_file
        )
        self.write_view_file('app.py', content)

    def generate_caching(self):
        cache_config = self.config.get('caching', {})
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

            if self.single_file:
                self.all_views_code += cache_code + "\n\n"
            else:
                self.write_view_file('cache_config.py', cache_code)

    def generate_security_manager(self):
        security_config = self.config.get('security', {})
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
            if self.single_file:
                self.all_views_code += security_code + "\n\n"
            else:
                self.write_view_file('security_manager.py', security_code)

    def generate_api_views(self):
        template = self.jinja_env.get_template('api_view.py.j2')
        for table_name in self.metadata.tables:
            table = self.metadata.tables[table_name]
            columns = self.get_column_info(table)

            view_code = template.render(
                table_name=table.name,
                columns=columns,
                config=self.config,
                single_file=self.single_file
            )

            if self.single_file:
                self.all_views_code += view_code + "\n\n"
            else:
                self.write_view_file(f"{table.name}_api.py", view_code)

    def generate_views(self):
        if self.single_file:
            self.generate_imports()

        for table_name in self.metadata.tables:
            table = self.metadata.tables[table_name]
            self.generate_model_view(table)
            self.generate_multiple_view(table)
            self.generate_master_detail_views(table)
            self.generate_chart_view(table)
            self.generate_wizard_view(table)
            self.generate_report_view(table)
            self.generate_calendar_view(table)

        self.generate_caching()
        self.generate_security_manager()
        self.generate_api_views()

        if self.single_file:
            self.write_view_file("views.py", self.all_views_code)

        self.generate_main_app_file()

def main():
    parser = argparse.ArgumentParser(description="Generate Flask-AppBuilder views from a PostgreSQL database")
    parser.add_argument('--uri', required=True, help="PostgreSQL database URI")
    parser.add_argument('--output-dir', required=True, help="Output directory for generated views")
    parser.add_argument('--config', required=False, help="Configuration file path")
    parser.add_argument('--single-file', action='store_true', help="Generate all views in a single file")
    args = parser.parse_args()

    # Ensure the output directory is an absolute path
    output_dir = os.path.abspath(args.output_dir)
    generator = ViewGenerator(args.uri, args.output_dir, args.config, args.single_file)
    generator.generate_views()

if __name__ == "__main__":
    main()
