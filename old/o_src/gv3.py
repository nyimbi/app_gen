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
import ast
import redis
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
        self.relationships = self.get_all_relationships()

    # ... (previous methods remain the same)

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

    def get_widget_for_column(self, column: Column, table: Table) -> Tuple[str, List[str]]:
        """
        Determine the appropriate widget based on column type, properties, and relationships.
        """
        column_type = column.type
        column_name = column.name.lower()

        # Check for foreign key relationships
        for rel in self.relationships.get(table.name, []):
            if rel['constrained_column'] == column.name:
                return f"Select2AJAXWidget(endpoint='/api/{rel['referred_table'].lower()}/api/column/{rel['referred_column']}')", []

        # Rest of the widget selection logic remains the same
        # ... (previous widget selection code)

        # Default to text field if no specific type is matched
        return 'BS3TextFieldWidget()', []

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
        
        return template.render(
            table_name=table.name,
            columns=columns,
            relationships=relationships,
            list_columns=list_columns,
            form_fields=form_fields,
            config=self.config
        )

    def generate_api_view(self, table: Table):
        template = self.jinja_env.get_template('api_view.py.j2')
        columns = self.get_column_info(table)
        relationships = self.relationships.get(table.name, [])
        return template.render(
            table_name=table.name,
            columns=columns,
            relationships=relationships,
            config=self.config
        )

    # ... (rest of the code remains the same)

# Update the model_view.py.j2 template:

"""
from flask_appbuilder import ModelView
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.actions import action
from flask_appbuilder.fieldwidgets import *
from flask_appbuilder.forms import DynamicForm
from wtforms import validators
from . import appbuilder, db
from .models import {{ table_name }}

class {{ table_name }}View(ModelView):
    datamodel = SQLAInterface({{ table_name }})
    
    list_columns = {{ list_columns }}

    {% for field, props in form_fields.items() %}
    {{ field }} = {{ props['widget'] }}
    {% if props['validators'] %}
    {{ field }}_validators = [{% for validator in props['validators'] %}{{ validator }}{% if not loop.last %}, {% endif %}{% endfor %}]
    {% endif %}
    {% endfor %}

    add_form = edit_form = show_form = DynamicForm

    {% for rel in relationships %}
    @action("related_{{ rel.referred_table }}", "Related {{ rel.referred_table|capitalize }}", "Do you really want to view related {{ rel.referred_table }}?", "fa-link")
    def related_{{ rel.referred_table }}(self, item):
        related_view = appbuilder.get_view('{{ rel.referred_table|capitalize }}View')
        return redirect(url_for(f"{related_view}.list", _flt_0_{{ rel.referred_column }}=item.{{ rel.constrained_column }}))
    {% endfor %}

appbuilder.add_view(
    {{ table_name }}View,
    "{{ table_name }}",
    icon="fa-folder-open-o",
    category="Data"
)
"""

# Update the api_view.py.j2 template:

"""
from flask_appbuilder.api import BaseApi, expose, rison, safe
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.models.filters import FilterEqualFunction
from . import appbuilder, db
from .models import {{ table_name }}

class {{ table_name }}Api(BaseApi):
    resource_name = '{{ table_name.lower() }}'
    datamodel = SQLAInterface({{ table_name }})

    @expose('/api/column/<column_name>')
    @rison()
    def column(self, column_name, **kwargs):
        q = self.datamodel.session.query(getattr({{ table_name }}, column_name))
        filters = kwargs.get('rison', {}).get('filters', [])
        for flt in filters:
            col = getattr({{ table_name }}, flt['col'])
            if flt['opr'] == 'eq':
                q = q.filter(col == flt['value'])
            elif flt['opr'] == 'cont':
                q = q.filter(col.contains(flt['value']))
        return self.response(200, result=[{column_name: getattr(row, column_name)} for row in q.all()])

appbuilder.add_api({{ table_name }}Api)
"""
