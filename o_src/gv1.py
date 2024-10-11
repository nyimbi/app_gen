import argparse
import os
import sys
from typing import Dict, List, Any, Tuple
import yaml
from sqlalchemy import create_engine, MetaData, inspect, Table, Column, ForeignKey
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import relationship
from jinja2 import Environment, FileSystemLoader
import black
import pylint.lint
from sqlalchemy import types
from flask_appbuilder.fieldwidgets import (
    BS3TextFieldWidget,
    BS3PasswordFieldWidget,
    BS3TextAreaFieldWidget,
    Select2Widget,
    Select2ManyWidget,
    DatePickerWidget,
    DateTimePickerWidget,
    TimePickerWidget,
    BS3DateTimePickerWidget,
    ColorPickerWidget,
    FileUploadFieldWidget,
    Select2AJAXWidget,
    Select2SlaveAJAXWidget
)
from flask_appbuilder.forms import JSONField

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
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)

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

    def generate_views(self):
        if self.single_file:
            self.all_views_code = "from flask_appbuilder import ModelView\n"
            self.all_views_code += "from flask_appbuilder.models.sqla.interface import SQLAInterface\n"
            self.all_views_code += "from flask_appbuilder.actions import action\n"
            self.all_views_code += "from flask_appbuilder.fieldwidgets import *\n"
            self.all_views_code += "from flask_appbuilder.forms import DynamicForm\n"
            self.all_views_code += "from wtforms import validators\n"
            self.all_views_code += "from . import appbuilder, db\n"
            self.all_views_code += "from .models import *\n\n"

        for table_name in self.metadata.tables:
            table = self.metadata.tables[table_name]
            view_code = self.generate_model_view(table)
            if self.single_file:
                self.all_views_code += view_code + "\n\n"
            else:
                self.write_view_file(f"{table_name}_view.py", view_code)

        if self.single_file:
            self.write_view_file("views.py", self.all_views_code)

        self.generate_main_app_file()

    def generate_model_view(self, table: Table) -> str:
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
        
        return template.render(
            table_name=table.name,
            columns=columns,
            relationships=relationships,
            list_columns=list_columns,
            form_fields=form_fields,
            config=self.config,
            single_file=self.single_file
        )

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
        column_type = column.type
        column_name = column.name.lower()

        # Check for foreign key relationships
        for rel in self.relationships.get(table.name, []):
            if rel['constrained_column'] == column.name:
                return f"Select2AJAXWidget(endpoint='/api/{rel['referred_table'].lower()}/api/column/{rel['referred_column']}')", []

        # Check for specific column names
        if 'password' in column_name:
            return 'BS3PasswordFieldWidget()', []
        elif 'email' in column_name:
            return 'BS3TextFieldWidget()', ['Email()']
        elif 'url' in column_name:
            return 'BS3TextFieldWidget()', ['URL()']

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
            return 'DatePickerWidget()', []
        elif isinstance(column_type, types.DateTime):
            return 'DateTimePickerWidget()', []
        elif isinstance(column_type, types.Time):
            return 'TimePickerWidget()', []
        elif isinstance(column_type, types.Boolean):
            return 'Select2Widget(choices=[("y","Yes"),("n","No")])', []
        elif isinstance(column_type, types.Enum):
            choices = [(choice, choice) for choice in column_type.enums]
            return f'Select2Widget(choices={choices})', []
        elif isinstance(column_type, types.ARRAY):
            return 'Select2ManyWidget()', []
        elif isinstance(column_type, types.JSON):
            return 'JSONField()', []
        elif isinstance(column_type, types.LargeBinary):
            return 'FileUploadFieldWidget()', []
        
        # Default to text field if no specific type is matched
        return 'BS3TextFieldWidget()', []

    def get_validators_for_column(self, column: Column) -> List[str]:
        validators = []
        if not column.nullable:
            validators.append('DataRequired()')
        
        column_type = column.type
        if isinstance(column_type, types.String):
            validators.append(f'Length(max={column_type.length})')
        
        return validators

    def write_view_file(self, filename: str, content: str):
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        self.format_and_lint_file(filepath)

    def format_and_lint_file(self, filepath: str):
        # Format the file using black
        black.format_file_in_place(filepath, fast=False, mode=black.FileMode())

        # Lint the file using pylint
        pylint_opts = ['--disable=C0111', filepath]
        pylint.lint.Run(pylint_opts, exit=False)

    def generate_main_app_file(self):
        template = self.jinja_env.get_template('main_app.py.j2')
        if self.single_file:
            views = ['views']
            table_names = [table.name for table in self.metadata.tables.values()]
        else:
            views = [f for f in os.listdir(self.output_dir) if f.endswith('_view.py')]
            table_names = []
        content = template.render(views=views, table_names=table_names, config=self.config, single_file=self.single_file)
        self.write_view_file('app.py', content)

def main():
    parser = argparse.ArgumentParser(description="Generate Flask-AppBuilder views from a PostgreSQL database")
    parser.add_argument('--db-uri', required=True, help="PostgreSQL database URI")
    parser.add_argument('--output-dir', required=True, help="Output directory for generated views")
    parser.add_argument('--config', required=True, help="Configuration file path")
    parser.add_argument('--single-file', action='store_true', help="Generate all views in a single file")
    args = parser.parse_args()

    generator = ViewGenerator(args.db_uri, args.output_dir, args.config, args.single_file)
    generator.generate_views()

if __name__ == "__main__":
    main()
