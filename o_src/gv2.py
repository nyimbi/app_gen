import argparse
import os
import sys
from typing import Dict, List, Any
import yaml
from sqlalchemy import create_engine, MetaData, inspect
from sqlalchemy.ext.automap import automap_base
from jinja2 import Environment, FileSystemLoader
import black
import pylint.lint
import ast

class ViewGenerator:
    def __init__(self, db_uri: str, output_dir: str, config_file: str):
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

    def load_config(self, config_file: str) -> Dict[str, Any]:
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)

    def generate_views(self):
        self.generate_model_views()
        self.generate_master_detail_views()
        self.generate_multiple_views()
        self.generate_chart_views()
        self.generate_calendar_views()
        self.generate_timeline_views()
        self.generate_api_views()
        self.generate_main_app_file()

    def generate_model_views(self):
        for table_name in self.metadata.tables:
            table = self.metadata.tables[table_name]
            view_code = self.generate_model_view(table)
            self.write_view_file(f"{table_name}_view.py", view_code)

    def generate_model_view(self, table):
        template = self.jinja_env.get_template('model_view.py.j2')
        columns = self.get_column_info(table)
        relationships = self.get_relationship_info(table)
        return template.render(
            table_name=table.name,
            columns=columns,
            relationships=relationships,
            config=self.config
        )

    def get_column_info(self, table) -> List[Dict[str, Any]]:
        columns = []
        for column in table.columns:
            column_info = {
                'name': column.name,
                'type': str(column.type),
                'nullable': column.nullable,
                'primary_key': column.primary_key,
                'widget': self.get_widget_for_column(column),
                'validators': self.get_validators_for_column(column)
            }
            columns.append(column_info)
        return columns

    def get_widget_for_column(self, column):
        # Logic to determine the appropriate widget based on column type
        # This is a simplified example
        if isinstance(column.type, sqlalchemy.types.String):
            return 'StringField'
        elif isinstance(column.type, sqlalchemy.types.Integer):
            return 'IntegerField'
        elif isinstance(column.type, sqlalchemy.types.DateTime):
            return 'DateTimeField'
        # Add more type checks and corresponding widgets
        return 'StringField'  # Default to StringField

    def get_validators_for_column(self, column):
        validators = []
        if not column.nullable:
            validators.append('DataRequired()')
        # Add more validators based on column properties
        return validators

    def get_relationship_info(self, table) -> List[Dict[str, Any]]:
        relationships = []
        for relationship in self.inspector.get_foreign_keys(table.name):
            rel_info = {
                'name': relationship['name'],
                'referred_table': relationship['referred_table'],
                'constrained_columns': relationship['constrained_columns'],
                'referred_columns': relationship['referred_columns']
            }
            relationships.append(rel_info)
        return relationships

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

    def generate_master_detail_views(self):
        for table_name in self.metadata.tables:
            table = self.metadata.tables[table_name]
            foreign_keys = self.inspector.get_foreign_keys(table_name)
            for fk in foreign_keys:
                master_table = self.metadata.tables[fk['referred_table']]
                view_code = self.generate_master_detail_view(master_table, table)
                self.write_view_file(f"{master_table.name}_{table.name}_master_detail_view.py", view_code)

    def generate_master_detail_view(self, master_table, detail_table):
        template = self.jinja_env.get_template('master_detail_view.py.j2')
        master_columns = self.get_column_info(master_table)
        detail_columns = self.get_column_info(detail_table)
        return template.render(
            master_table_name=master_table.name,
            detail_table_name=detail_table.name,
            master_columns=master_columns,
            detail_columns=detail_columns,
            config=self.config
        )

    def generate_multiple_views(self):
        for table_name in self.metadata.tables:
            table = self.metadata.tables[table_name]
            foreign_keys = self.inspector.get_foreign_keys(table_name)
            if len(foreign_keys) > 1:
                view_code = self.generate_multiple_view(table, foreign_keys)
                self.write_view_file(f"{table_name}_multiple_view.py", view_code)

    def generate_multiple_view(self, table, foreign_keys):
        template = self.jinja_env.get_template('multiple_view.py.j2')
        columns = self.get_column_info(table)
        related_tables = [self.metadata.tables[fk['referred_table']] for fk in foreign_keys]
        return template.render(
            table_name=table.name,
            columns=columns,
            related_tables=related_tables,
            config=self.config
        )

    def generate_chart_views(self):
        for table_name in self.metadata.tables:
            table = self.metadata.tables[table_name]
            numeric_columns = [c for c in table.columns if isinstance(c.type, (sqlalchemy.types.Integer, sqlalchemy.types.Float))]
            date_columns = [c for c in table.columns if isinstance(c.type, sqlalchemy.types.DateTime)]
            if numeric_columns and date_columns:
                view_code = self.generate_chart_view(table, numeric_columns, date_columns)
                self.write_view_file(f"{table_name}_chart_view.py", view_code)

    def generate_chart_view(self, table, numeric_columns, date_columns):
        template = self.jinja_env.get_template('chart_view.py.j2')
        return template.render(
            table_name=table.name,
            numeric_columns=numeric_columns,
            date_columns=date_columns,
            config=self.config
        )

    def generate_calendar_views(self):
        for table_name in self.metadata.tables:
            table = self.metadata.tables[table_name]
            date_columns = [c for c in table.columns if isinstance(c.type, sqlalchemy.types.DateTime)]
            if date_columns:
                view_code = self.generate_calendar_view(table, date_columns)
                self.write_view_file(f"{table_name}_calendar_view.py", view_code)

    def generate_calendar_view(self, table, date_columns):
        template = self.jinja_env.get_template('calendar_view.py.j2')
        return template.render(
            table_name=table.name,
            date_columns=date_columns,
            config=self.config
        )

    def generate_timeline_views(self):
        for table_name in self.metadata.tables:
            table = self.metadata.tables[table_name]
            date_columns = [c for c in table.columns if isinstance(c.type, sqlalchemy.types.DateTime)]
            if len(date_columns) >= 2:  # We need at least a start and end date for a timeline
                view_code = self.generate_timeline_view(table, date_columns)
                self.write_view_file(f"{table_name}_timeline_view.py", view_code)

    def generate_timeline_view(self, table, date_columns):
        template = self.jinja_env.get_template('timeline_view.py.j2')
        return template.render(
            table_name=table.name,
            date_columns=date_columns,
            config=self.config
        )

    def generate_api_views(self):
        for table_name in self.metadata.tables:
            table = self.metadata.tables[table_name]
            view_code = self.generate_api_view(table)
            self.write_view_file(f"{table_name}_api.py", view_code)

    def generate_api_view(self, table):
        template = self.jinja_env.get_template('api_view.py.j2')
        columns = self.get_column_info(table)
        return template.render(
            table_name=table.name,
            columns=columns,
            config=self.config
        )

    def generate_main_app_file(self):
        template = self.jinja_env.get_template('main_app.py.j2')
        views = [f for f in os.listdir(self.output_dir) if f.endswith('_view.py')]
        api_views = [f for f in os.listdir(self.output_dir) if f.endswith('_api.py')]
        content = template.render(views=views, api_views=api_views, config=self.config)
        self.write_view_file('app.py', content)

def main():
    parser = argparse.ArgumentParser(description="Generate Flask-AppBuilder views from a PostgreSQL database")
    parser.add_argument('--db-uri', required=True, help="PostgreSQL database URI")
    parser.add_argument('--output-dir', required=True, help="Output directory for generated views")
    parser.add_argument('--config', required=True, help="Configuration file path")
    args = parser.parse_args()

    generator = ViewGenerator(args.db_uri, args.output_dir, args.config)
    generator.generate_views()

if __name__ == "__main__":
    main()
