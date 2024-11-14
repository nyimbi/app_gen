"""
gv7.py: Advanced Flask-AppBuilder View Generator

This script generates comprehensive Flask-AppBuilder views from a database schema,
including ModelViews, MasterDetailViews, MultipleViews, WizardViews, ChartViews,
and RestApiViews. It also generates GraphQL schemas for the models.

Usage:
    python gv7.py --uri <database_uri> --output <output_file>

Dependencies:
    - SQLAlchemy
    - Flask-AppBuilder
    - graphene
    - inflect
"""

import sqlalchemy as sa
from sqlalchemy import inspect, Boolean, Date, DateTime, Enum, Float, Integer, Numeric, String, Text, Time, ForeignKey, Table, ForeignKeyConstraint, PrimaryKeyConstraint, MetaData, create_engine
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy.sql import sqltypes
import inflect
import math
import argparse
from typing import Any, Dict, List, Optional, Union, Tuple
import os
from flask import g, flash, redirect, url_for, session, request, render_template, make_response
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView, MasterDetailView, MultipleView, ModelRestApi
from flask_appbuilder.fields import AJAXSelectField, QuerySelectField, QuerySelectMultipleField, EnumField
from flask_appbuilder.fieldwidgets import Select2AJAXWidget, Select2SlaveAJAXWidget, Select2ManyWidget, BS3TextFieldWidget, BS3PasswordFieldWidget, DatePickerWidget, DateTimePickerWidget, Select2Widget
from flask_appbuilder.actions import action
from flask_appbuilder.security.decorators import has_access
from flask_appbuilder.forms import DynamicForm
from flask_appbuilder import AppBuilder, BaseView, expose, has_access
from flask_appbuilder.charts.views import GroupByChartView, ChartView
from flask_appbuilder.models.group import aggregate_count
from flask_appbuilder.widgets import ListThumbnail, FormVerticalWidget
from flask_login import current_user
from wtforms import StringField, BooleanField, IntegerField, FloatField, DateField, DateTimeField, SelectField, HiddenField, TextAreaField, DecimalField, validators
import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField

from view_utils import get_view_icon
from utils import snake_to_pascal, snake_to_words, pascal_to_words, get_class_name

# Set up logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize inflect engine
p = inflect.engine()

# Global variables
INDENT = "    "
AB_PREFIX = 'ab_'
generated_views = []
generated_code = []

# Initialize GraphQL schema
schema = graphene.Schema()

def generate_views(db_uri: str) -> None:
    """
    Generate Flask-AppBuilder views for all tables in the database.

    This function is the main entry point for view generation. It connects to the database,
    reflects the schema, and generates various types of views including ModelViews,
    MasterDetailViews, MultipleViews, WizardViews, ChartViews, and API views.

    Args:
        db_uri (str): SQLAlchemy database URI to connect to

    Returns:
        None
    """
    engine = create_engine(db_uri)
    inspector = inspect(engine)
    metadata = MetaData()
    metadata.reflect(bind=engine)

    # Add imports and initial setup
    generated_code.append([
        "imports",
        """from flask_appbuilder import ModelView, MasterDetailView, MultipleView, ModelRestApi
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.fieldwidgets import Select2Widget, DatePickerWidget
from flask_appbuilder.forms import DynamicForm
from wtforms import StringField, IntegerField, DateField, SelectField, TextAreaField
from flask_appbuilder.actions import action
from flask import flash, redirect, url_for, request, render_template, make_response
from flask_appbuilder.security.decorators import has_access
from flask_appbuilder.charts.views import GroupByChartView
from . import appbuilder, db
from .models import *
import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField

# Global list to store all generated views
generated_views = []
"""
    ])

    for table_name in inspector.get_table_names():
        if table_name.lower().startswith(AB_PREFIX):
            continue
        table = metadata.tables[table_name]
        generate_model_view(table, inspector, metadata)
        generate_master_detail_views(table, metadata)
        generate_multiple_views(table, metadata)
        generate_wizard_view(table)
        generate_graphql(table)
        generate_model_rest_api(table)
        generate_chart_view(table)

    # Add view registration function
    generated_code.append([
        "register_views",
        generate_view_registration_code()
    ])

def generate_model_view(table: sa.Table, inspector: sa.engine.reflection.Inspector, metadata: sa.MetaData) -> None:
    """
    Generate a comprehensive ModelView for a table with all improvements:
    - Lazy loading for related data
    - Caching for frequently accessed data
    - Keyset pagination for better performance
    - Search optimization
    - Responsive design
    - Interactive filters

    Args:
        table (sa.Table): SQLAlchemy Table object
        inspector (sa.engine.reflection.Inspector): SQLAlchemy Inspector object
        metadata (sa.MetaData): SQLAlchemy MetaData object

    Returns:
        None
    """
    class_name = get_class_name(table.name, p)
    view_name = f"{class_name}ModelView"
    columns = [c.name for c in table.columns]
    list_columns = get_list_columns(columns)
    field_sets = get_field_sets(table)
    icon = get_view_icon(table.name, "ModelView")

    view_code = [
        f"class {view_name}(ModelView):",
        f"{INDENT}datamodel = SQLAInterface({class_name})",
        f"{INDENT}list_title = '{snake_to_words(table.name)} List'",
        f"{INDENT}show_title = '{snake_to_words(table.name)} Details'",
        f"{INDENT}add_title = 'Add {snake_to_words(table.name)}'",
        f"{INDENT}edit_title = 'Edit {snake_to_words(table.name)}'",
        f"{INDENT}list_columns = {list_columns}",
        f"{INDENT}show_columns = list_columns",
        f"{INDENT}edit_columns = [col for col in list_columns if col != 'id']",
        f"{INDENT}add_columns = [col for col in list_columns if col != 'id']",
        f"{INDENT}search_columns = {get_search_columns(table)}",
        f"{INDENT}search_exclude_columns = ['file', 'photo', 'image']",
        f"{INDENT}label_columns = {get_label_columns(table)}",
        generate_description_columns(table, inspector),
        "",
        f"{INDENT}# Field sets for add and edit forms",
        f"{INDENT}add_fieldsets = {field_sets}",
        f"{INDENT}edit_fieldsets = add_fieldsets",
        "",
        f"{INDENT}# Lazy loading for related data",
        f"{INDENT}related_views = [{', '.join([f'{get_class_name(fk.column.table.name, p)}ModelView' for fk in table.foreign_keys])}]",
        f"{INDENT}list_template = 'list_with_lazy_loading.html'",
        "",
        f"{INDENT}# Caching configuration",
        f"{INDENT}cache_timeout = 60  # Cache for 60 seconds",
        "",
        f"{INDENT}# Pagination configuration",
        f"{INDENT}page_size = 20",
        f"{INDENT}base_order = ('id', 'asc')",
        "",
        f"{INDENT}# Search configuration",
        f"{INDENT}search_form_query_rel_fields = {get_search_form_query_rel_fields(table, metadata)}",
        "",
        f"{INDENT}# Responsive design",
        f"{INDENT}list_template = 'responsive_list.html'",
        f"{INDENT}edit_template = 'responsive_edit.html'",
        f"{INDENT}show_template = 'responsive_show.html'",
        "",
        f"{INDENT}# Interactive filters",
        f"{INDENT}filter_rel_fields = {get_filter_rel_fields(table, metadata)}",
        f"{INDENT}filter_exclude_columns = ['file', 'photo', 'image']",
        f"{INDENT}filter_template = 'interactive_filters.html'",
        "",
        f"{INDENT}# Base Filters",
        f"{INDENT}base_filters = []",
        "",
        generate_form_query_rel_fields(table, metadata),
        "",
        f"{INDENT}# Form extra fields",
        f"{INDENT}form_extra_fields = {{",
        f"{generate_form_fields(table, metadata)}",
        f"{INDENT}}}",
        "",
        generate_validators(table),
        "",
        generate_custom_actions(),
        "",
        generate_lifecycle_hooks(),
        "",
        f"{INDENT}@cache.memoize(timeout=cache_timeout)",
        f"{INDENT}def query_count(self):",
        f"{INDENT}{INDENT}return self.datamodel.count()",
        "",
        f"{INDENT}@cache.memoize(timeout=cache_timeout)",
        f"{INDENT}def get_related_data(self, pk):",
        f"{INDENT}{INDENT}item = self.datamodel.get(pk)",
        f"{INDENT}{INDENT}related_data = {{}}",
        f"{INDENT}{INDENT}for related_view in self.related_views:",
        f"{INDENT}{INDENT}{INDENT}related_model = related_view.datamodel.obj",
        f"{INDENT}{INDENT}{INDENT}relationship = next((r for r in self.datamodel.obj.__mapper__.relationships if r.mapper.class_ == related_model), None)",
        f"{INDENT}{INDENT}{INDENT}if relationship:",
        f"{INDENT}{INDENT}{INDENT}{INDENT}related_items = getattr(item, relationship.key)",
        f"{INDENT}{INDENT}{INDENT}{INDENT}related_data[relationship.key] = [{{c: getattr(ri, c) for c in related_view.list_columns}} for ri in related_items]",
        f"{INDENT}{INDENT}return related_data",
        "",
        f"{INDENT}@expose('/api/related/<pk>')",
        f"{INDENT}@has_access",
        f"{INDENT}def api_related(self, pk):",
        f"{INDENT}{INDENT}related_data = self.get_related_data(pk)",
        f"{INDENT}{INDENT}return jsonify(related_data)",
        "",
        f"{INDENT}def get_list(self):",
        f"{INDENT}{INDENT}# Implement keyset pagination logic here",
        f"{INDENT}{INDENT}last_id = request.args.get('last_id', 0, type=int)",
        f"{INDENT}{INDENT}query = self.datamodel.session.query(self.datamodel.obj)",
        f"{INDENT}{INDENT}if last_id:",
        f"{INDENT}{INDENT}{INDENT}query = query.filter(self.datamodel.obj.id > last_id)",
        f"{INDENT}{INDENT}query = query.order_by(self.datamodel.obj.id.asc()).limit(self.page_size)",
        f"{INDENT}{INDENT}items = query.all()",
        f"{INDENT}{INDENT}return self.render_template(",
        f"{INDENT}{INDENT}{INDENT}self.list_template,",
        f"{INDENT}{INDENT}{INDENT}items=items,",
        f"{INDENT}{INDENT}{INDENT}last_id=items[-1].id if items else 0,",
        f"{INDENT}{INDENT}{INDENT}has_more=len(items) == self.page_size",
        f"{INDENT}{INDENT})",
        "",
        f"{INDENT}@expose('/search/')",
        f"{INDENT}@has_access",
        f"{INDENT}def search(self):",
        f"{INDENT}{INDENT}search_query = request.args.get('q', '')",
        f"{INDENT}{INDENT}if search_query:",
        f"{INDENT}{INDENT}{INDENT}search_columns = [getattr(self.datamodel.obj, col) for col in self.search_columns]",
        f"{INDENT}{INDENT}{INDENT}query = self.datamodel.session.query(self.datamodel.obj)",
        f"{INDENT}{INDENT}{INDENT}query = query.filter(or_(*[col.ilike(f'%{{search_query}}%') for col in search_columns]))",
        f"{INDENT}{INDENT}{INDENT}items = query.all()",
        f"{INDENT}{INDENT}{INDENT}return self.render_template(",
        f"{INDENT}{INDENT}{INDENT}{INDENT}'search_results.html',",
        f"{INDENT}{INDENT}{INDENT}{INDENT}items=items,",
        f"{INDENT}{INDENT}{INDENT}{INDENT}search_query=search_query",
        f"{INDENT}{INDENT}{INDENT})",
        f"{INDENT}{INDENT}return redirect(url_for('.list'))",
        "",
        f"{INDENT}@expose('/filter/')",
        f"{INDENT}@has_access",
        f"{INDENT}def filter(self):",
        f"{INDENT}{INDENT}filter_params = request.args.to_dict()",
        f"{INDENT}{INDENT}query = self.datamodel.session.query(self.datamodel.obj)",
        f"{INDENT}{INDENT}for column, value in filter_params.items():",
        f"{INDENT}{INDENT}{INDENT}if column in self.filter_rel_fields:",
        f"{INDENT}{INDENT}{INDENT}{INDENT}related_model = self.filter_rel_fields[column]",
        f"{INDENT}{INDENT}{INDENT}{INDENT}query = query.join(related_model).filter(related_model.id == value)",
        f"{INDENT}{INDENT}{INDENT}elif column not in self.filter_exclude_columns:",
        f"{INDENT}{INDENT}{INDENT}{INDENT}query = query.filter(getattr(self.datamodel.obj, column) == value)",
        f"{INDENT}{INDENT}items = query.all()",
        f"{INDENT}{INDENT}return self.render_template(",
        f"{INDENT}{INDENT}{INDENT}'filter_results.html',",
        f"{INDENT}{INDENT}{INDENT}items=items,",
        f"{INDENT}{INDENT}{INDENT}filter_params=filter_params",
        f"{INDENT}{INDENT})",
        "",
        generate_repr_method(table)
    ]

    generated_code.append([view_name, "\n".join(view_code)])
    generated_views.append((view_name, "ModelView", table.name, icon))

def get_list_columns(columns: List[str]) -> List[str]:
    """
    Get a list of column names suitable for list views, excluding certain system columns.

    Args:
        columns (List[str]): List of column names

    Returns:
        List[str]: List of column names suitable for list views
    """
    ignored_fields = {'created_at', 'updated_at', 'created_by_fk', 'changed_by_fk'}
    return [col for col in columns if col not in ignored_fields]

def get_field_sets(table: sa.Table) -> Dict[str, List[Tuple[str, str]]]:
    """
    Generate field sets for forms, grouping columns into sets of 4.

    Args:
        table (sa.Table): SQLAlchemy Table object

    Returns:
        Dict[str, List[Tuple[str, str]]]: Dictionary of field sets with labels
    """
    ignored_fields = {'id', 'created_at', 'updated_at', 'created_by_fk', 'changed_by_fk'}
    valid_columns = [col.name for col in table.columns if col.name not in ignored_fields]

    # Group fields into sets of 4
    field_sets = [valid_columns[i:i+4] for i in range(0, len(valid_columns), 4)]

    # Create field_sets dictionary
    field_sets_dict = {
        f"Field Set {i+1}": [
            (col, col.replace('_', ' ').title()) for col in field_set
        ] for i, field_set in enumerate(field_sets)
    }

    return field_sets_dict

def get_search_columns(table: sa.Table) -> List[str]:
    """
    Generate list of searchable columns.

    Args:
        table (sa.Table): SQLAlchemy Table object

    Returns:
        List[str]: List of column names suitable for searching
    """
    return [col.name for col in table.columns if isinstance(col.type, (sqltypes.String, sqltypes.Text))]

def get_label_columns(table: sa.Table) -> Dict[str, str]:
    """
    Generate dictionary of user-friendly labels for columns.

    Args:
        table (sa.Table): SQLAlchemy Table object

    Returns:
        Dict[str, str]: Dictionary of column names and their user-friendly labels
    """
    return {col.name: snake_to_words(col.name) for col in table.columns}

def generate_description_columns(table: sa.Table, inspector: sa.engine.reflection.Inspector) -> str:
    """
    Generate description_columns dictionary with column comments as hints.

    Args:
        table (sa.Table): SQLAlchemy Table object
        inspector (sa.engine.reflection.Inspector): SQLAlchemy Inspector object

    Returns:
        str: String representation of the description_columns dictionary
    """
    descriptions = {}
    for column in inspector.get_columns(table.name):
        if column['comment']:
            descriptions[column['name']] = column['comment']

    if descriptions:
        return f"{INDENT}description_columns = {descriptions}"
    else:
        return f"{INDENT}description_columns = {{}}"

def generate_form_query_rel_fields(table: sa.Table, metadata: sa.MetaData) -> str:
    """
    Generate form_query_rel_fields for foreign key relationships.

    Args:
        table (sa.Table): SQLAlchemy Table object
        metadata (sa.MetaData): SQLAlchemy MetaData object

    Returns:
        str: String representation of the form_query_rel_fields dictionary
    """
    form_query_rel_fields = {}
    for fk in table.foreign_keys:
        referred_table = fk.column.table
        referred_class = get_class_name(referred_table.name, p)
        form_query_rel_fields[fk.parent.name] = f"db.session.query({referred_class})"

    if form_query_rel_fields:
        return f"{INDENT}form_query_rel_fields = {form_query_rel_fields}"
    return f"{INDENT}form_query_rel_fields = {{}}"


def get_filter_rel_fields(table: sa.Table, metadata: sa.MetaData) -> Dict[str, str]:
    """
    Generate a dictionary of related fields that can be used for filtering in the ModelView.

    Args:
        table (sa.Table): SQLAlchemy Table object
        metadata (sa.MetaData): SQLAlchemy MetaData object

    Returns:
        Dict[str, str]: A dictionary where keys are relationship field names and values are related model names
    """
    filter_rel_fields = {}

    for fk in table.foreign_keys:
        parent_table = fk.column.table
        parent_class_name = get_class_name(parent_table.name, p)
        relationship_name = fk.parent.name.replace('_id', '')
        filter_rel_fields[relationship_name] = parent_class_name

    # Check for many-to-many relationships
    for other_table in metadata.tables.values():
        if is_association_table(other_table):
            if table.name in [fk.column.table.name for fk in other_table.foreign_keys]:
                other_table_name = next(fk.column.table.name for fk in other_table.foreign_keys if fk.column.table.name != table.name)
                other_class_name = get_class_name(other_table_name, p)
                relationship_name = p.plural(other_table_name.lower())
                filter_rel_fields[relationship_name] = other_class_name

    return filter_rel_fields

# def is_association_table(table: sa.Table) -> bool:
#     """
#     Check if a table is an association table (for many-to-many relationships).

#     Args:
#         table (sa.Table): SQLAlchemy Table object

#     Returns:
#         bool: True if the table is an association table, False otherwise
#     """
#     # An association table typically has only two columns, both foreign keys
#     if len(table.columns) != 2:
#         return False

#     return all(isinstance(constraint, sa.ForeignKeyConstraint) for constraint in table.constraints
#                if isinstance(constraint, sa.ForeignKeyConstraint))

def get_class_name(table_name: str, p: inflect.engine) -> str:
    """
    Generate a class name from a table name.

    Args:
        table_name (str): Name of the table
        p (inflect.engine): Inflect engine for singular/plural conversions

    Returns:
        str: Generated class name
    """
    return ''.join(word.capitalize() for word in p.singular_noun(table_name).split('_'))


def generate_form_fields(table: sa.Table, metadata: sa.MetaData) -> str:
    """
    Generate form fields with appropriate widgets and validations based on column types.

    Args:
        table (sa.Table): SQLAlchemy Table object
        metadata (sa.MetaData): SQLAlchemy MetaData object

    Returns:
        str: String representation of the form_extra_fields dictionary
    """
    form_fields = []
    for column in table.columns:
        if column.name in ['id', 'created_at', 'updated_at', 'created_by_fk', 'changed_by_fk']:
            continue

        field_code = generate_form_field(column, metadata)
        if field_code:
            form_fields.append(f"{INDENT}{INDENT}{field_code}")

    return "\n".join(form_fields)

def generate_form_field(column: sa.Column, metadata: sa.MetaData) -> str:
    """
    Generate a form field for a single column.

    Args:
        column (sa.Column): SQLAlchemy Column object
        metadata (sa.MetaData): SQLAlchemy MetaData object

    Returns:
        str: String representation of the form field
    """
    field_name = column.name
    label = snake_to_words(field_name).title()

    if isinstance(column.type, String):
        return f"'{field_name}': StringField('{label}', widget=BS3TextFieldWidget(), validators=[validators.DataRequired()])"
    elif isinstance(column.type, Text):
        return f"'{field_name}': TextAreaField('{label}', validators=[validators.DataRequired()])"
    elif isinstance(column.type, Integer):
        return f"'{field_name}': IntegerField('{label}', validators=[validators.DataRequired()])"
    elif isinstance(column.type, Float):
        return f"'{field_name}': FloatField('{label}', validators=[validators.DataRequired()])"
    elif isinstance(column.type, Boolean):
        return f"'{field_name}': BooleanField('{label}')"
    elif isinstance(column.type, Date):
        return f"'{field_name}': DateField('{label}', widget=DatePickerWidget())"
    elif isinstance(column.type, DateTime):
        return f"'{field_name}': DateTimeField('{label}', widget=DateTimePickerWidget())"
    elif isinstance(column.type, Enum):
        choices = [(choice, choice) for choice in column.type.enums]
        return f"'{field_name}': SelectField('{label}', choices={choices}, widget=Select2Widget())"
    elif isinstance(column.type, ForeignKey):
        related_table = column.foreign_keys[0].column.table
        related_model = get_class_name(related_table.name, p)
        return f"'{field_name}': QuerySelectField('{label}', query_factory=lambda: db.session.query({related_model}), widget=Select2Widget())"
    else:
        return f"'{field_name}': StringField('{label}', widget=BS3TextFieldWidget())"

def generate_validators(table: sa.Table) -> str:
    """
    Generate validators for table columns.

    Args:
        table (sa.Table): SQLAlchemy Table object

    Returns:
        str: String representation of the validators_columns dictionary
    """
    validators = {}
    for column in table.columns:
        column_validators = []
        if not column.nullable and not column.primary_key:
            column_validators.append('validators.DataRequired()')
        if isinstance(column.type, String) and column.type.length:
            column_validators.append(f'validators.Length(max={column.type.length})')
        if column_validators:
            validators[column.name] = column_validators

    if validators:
        return f"{INDENT}validators_columns = {validators}"
    return f"{INDENT}validators_columns = {{}}"

def generate_custom_actions() -> str:
    """
    Generate placeholders for custom actions including print, export, and bookmark.

    Returns:
        str: String representation of custom actions
    """
    return f"""
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
        return render_template('print_items.html', items=items, model=self.__class__.__name__)

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]
        csv_data = self.datamodel.export_as_csv(items)
        response = make_response(csv_data)
        response.headers["Content-Disposition"] = f"attachment; filename={self.__class__.__name__}_export.csv"
        response.headers["Content-Type"] = "text/csv"
        return response

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]
        for item in items:
            if not hasattr(item, 'is_bookmarked'):
                logger.warning(f"Model {self.__class__.__name__} does not have 'is_bookmarked' attribute")
                flash(f"Cannot bookmark items of type {self.__class__.__name__}", "warning")
                return redirect(self.get_redirect())
            item.is_bookmarked = True
        self.datamodel.bulk_update(items)
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())
    """

def generate_lifecycle_hooks() -> str:
    """
    Generate lifecycle hook methods for the view.

    Returns:
        str: String representation of lifecycle hook methods
    """
    return f"""
    def pre_add(self, item):
        if hasattr(item, 'created_at'):
            item.created_at = datetime.datetime.now()
        if hasattr(item, 'updated_at'):
            item.updated_at = datetime.datetime.now()

    def pre_update(self, item):
        if hasattr(item, 'updated_at'):
            item.updated_at = datetime.datetime.now()

    def post_add(self, item):
        logger.info(f"New {self.__class__.__name__} added: {{item}}")

    def post_update(self, item):
        logger.info(f"{self.__class__.__name__} updated: {{item}}")

    def post_delete(self, item):
        logger.info(f"{self.__class__.__name__} deleted: {{item}}")
    """

def generate_repr_method(table: sa.Table) -> str:
    """
    Generate a __repr__ method for a view class.

    Args:
        table (sa.Table): SQLAlchemy Table object

    Returns:
        str: String representation of the __repr__ method
    """
    display_column = next((col.name for col in table.columns if col.name in ['name', 'title', 'label']), 'id')
    return f"""
    def __repr__(self):
        return str(self.{display_column})
    """

def generate_master_detail_views(table: sa.Table, metadata: sa.MetaData) -> None:
    """
    Generate MasterDetailViews for tables with foreign key relationships.

    Args:
        table (sa.Table): SQLAlchemy Table object
        metadata (sa.MetaData): SQLAlchemy MetaData object

    Returns:
        None
    """
    for fk in table.foreign_keys:
        parent_table = metadata.tables[fk.column.table.name]
        parent_class_name = get_class_name(parent_table.name, p)
        child_class_name = get_class_name(table.name, p)
        view_name = f"{parent_class_name}{child_class_name}MasterDetailView"
        icon = get_view_icon(table.name, "MasterDetailView")

        view_code = f"""
class {view_name}(MasterDetailView):
    datamodel = SQLAInterface({parent_class_name})
    related_views = [{child_class_name}ModelView]
    list_title = '{snake_to_words(parent_table.name)} with {snake_to_words(table.name)}'
    show_title = '{snake_to_words(parent_table.name)} Detail'
    add_title = 'Add {snake_to_words(parent_table.name)}'
    edit_title = 'Edit {snake_to_words(parent_table.name)}'
    list_columns = {get_list_columns([c.name for c in parent_table.columns])}
    show_columns = list_columns
{generate_repr_method(parent_table)}
        """

        generated_code.append([view_name, view_code])
        generated_views.append((view_name, "MasterDetailView", f"{parent_table.name}_{table.name}", icon))

def generate_multiple_views(table: sa.Table, metadata: sa.MetaData) -> None:
    """
    Generate MultipleViews for tables with multiple related tables.

    Args:
        table (sa.Table): SQLAlchemy Table object
        metadata (sa.MetaData): SQLAlchemy MetaData object

    Returns:
        None
    """
    related_tables = set()
    for fk in table.foreign_keys:
        related_tables.add(fk.column.table)
    for other_table in metadata.tables.values():
        for fk in other_table.foreign_keys:
            if fk.column.table == table:
                related_tables.add(other_table)

    if len(related_tables) > 1:
        class_name = get_class_name(table.name, p)
        view_name = f"{class_name}MultipleView"
        icon = get_view_icon(table.name, "MultipleView")
        related_views = [f"{get_class_name(t.name, p)}ModelView" for t in related_tables]

        view_code = f"""
class {view_name}(MultipleView):
    views = [{', '.join(related_views)}]
    list_title = '{snake_to_words(table.name)} Multiple View'

    @expose('/custom_view')
    @has_access
    def custom_view(self):
        return self.render_template('custom_multiple_view.html', views=self.views)

{generate_repr_method(table)}
        """

        generated_code.append([view_name, view_code])
        generated_views.append((view_name, "MultipleView", table.name, icon))

def generate_wizard_view(table: sa.Table) -> None:
    """
    Generate a WizardView for complex forms with multiple steps.

    Args:
        table (sa.Table): SQLAlchemy Table object

    Returns:
        None
    """
    class_name = get_class_name(table.name, p)
    view_name = f"{class_name}WizardView"
    icon = get_view_icon(table.name, "WizardView")
    columns = [c.name for c in table.columns if c.name not in ['id', 'created_at', 'updated_at', 'created_by_fk', 'changed_by_fk']]
    total_steps = math.ceil(len(columns) / 5)

    wizard_code = f"""
class {view_name}(BaseView):
    route_base = '/{table.name}_wizard'
    datamodel = SQLAInterface({class_name})
    total_steps = {total_steps}

    def _init_steps(self):
        self.steps = {{}}
        for step in range(1, self.total_steps + 1):
            step_name = f'step{{step}}'
            self.steps[step_name] = getattr(self, step_name)

    def __init__(self):
        super().__init__()
        self._init_steps()

    def is_step_complete(self, step):
        return session.get(f'{{self.__class__.__name__}}_step{{step}}_complete', False)

    def mark_step_complete(self, step):
        session[f'{{self.__class__.__name__}}_step{{step}}_complete'] = True

    def get_progress(self):
        completed_steps = sum(self.is_step_complete(step) for step in range(1, self.total_steps + 1))
        return (completed_steps / self.total_steps) * 100

    @expose('/reset')
    def reset(self):
        for step in range(1, self.total_steps + 1):
            session.pop(f'{{self.__class__.__name__}}_step{{step}}_complete', None)
        flash('Your progress has been reset. Start again from the beginning!', 'info')
        return redirect(url_for(f'.step1'))

    def render_wizard(self, step, form, step_description):
        return self.render_template(
            'wizard.html',
            form=form,
            progress=self.get_progress(),
            current_step=step,
            total_steps=self.total_steps,
            step_description=step_description
        )
    """

    for step in range(1, total_steps + 1):
        start_idx = (step - 1) * 5
        end_idx = min(step * 5, len(columns))
        step_columns = columns[start_idx:end_idx]

        wizard_code += f"""
    @expose('/step{step}', methods=['GET', 'POST'])
    def step{step}(self):
        form = DynamicForm()
        {generate_form_fields_for_wizard(step_columns, table)}

        if form.validate_on_submit():
            session['step{step}_data'] = form.data
            self.mark_step_complete({step})
            next_step = {step + 1 if step < total_steps else 'submit'}
            return redirect(url_for(f'.{{next_step}}'))

        form_data = session.get('step{step}_data', {{}})
        form = DynamicForm(**form_data)
        return self.render_wizard({step}, form, 'Step {step}: {", ".join(step_columns)}')
    """

    wizard_code += f"""
    @expose('/submit', methods=['GET', 'POST'])
    def submit(self):
        if all(self.is_step_complete(step) for step in range(1, self.total_steps + 1)):
            combined_data = {{}}
            for step in range(1, self.total_steps + 1):
                combined_data.update(session.get(f'step{{step}}_data', {{}}))

            item = self.datamodel.obj()
            for key, value in combined_data.items():
                setattr(item, key, value)
            self.datamodel.add(item)

            for step in range(1, self.total_steps + 1):
                session.pop(f'step{{step}}_data', None)
                session.pop(f'{{self.__class__.__name__}}_step{{step}}_complete', None)

            flash('Form submitted successfully!', 'success')
            return redirect(url_for('.step1'))
        else:
            flash('Please complete all steps before submitting.', 'warning')
            return redirect(url_for('.step1'))

{generate_repr_method(table)}
    """

    generated_code.append([view_name, wizard_code])
    generated_views.append((view_name, "WizardView", table.name, icon))

def generate_form_fields_for_wizard(columns: List[str], table: sa.Table) -> str:
    """
    Generate form fields for a wizard step.

    Args:
        columns (List[str]): List of column names for the current step
        table (sa.Table): SQLAlchemy Table object

    Returns:
        str: String representation of form field definitions
    """
    form_fields = []
    for column in columns:
        col_obj = table.columns[column]
        form_fields.append(f"form.{column} = {generate_form_field(col_obj, table.metadata)}")
    return "\n        ".join(form_fields)

def generate_graphql(table: sa.Table) -> None:
    """
    Generate GraphQL schema and queries for a table.

    Args:
        table (sa.Table): SQLAlchemy Table object

    Returns:
        None
    """
    class_name = get_class_name(table.name, p)
    generated_code.append([
        f"{class_name}GraphQL",
        f"""
class {class_name}Node(SQLAlchemyObjectType):
    class Meta:
        model = {class_name}
        interfaces = (graphene.relay.Node, )

class {class_name}Connection(graphene.relay.Connection):
    class Meta:
        node = {class_name}Node

class Query(graphene.ObjectType):
    node = graphene.relay.Node.Field()
    all_{table.name} = SQLAlchemyConnectionField({class_name}Connection)

    {class_name.lower()} = graphene.Field({class_name}Node, id=graphene.Int())
    def resolve_{class_name.lower()}(self, info, id):
        return {class_name}.query.get(id)

schema.query = Query
        """
    ])

def generate_model_rest_api(table: sa.Table) -> None:
    """
    Generate a ModelRestApi for RESTful API access to a table.

    Args:
        table (sa.Table): SQLAlchemy Table object

    Returns:
        None
    """
    class_name = get_class_name(table.name, p)
    view_name = f"{class_name}RestApi"
    columns = [c.name for c in table.columns]
    icon = get_view_icon(table.name, "ModelRestApi")
    generated_code.append([
        view_name,
        f"""
class {view_name}(ModelRestApi):
    resource_name = '{table.name}'
    datamodel = SQLAInterface({class_name})
    allow_browser_login = True
    list_columns = {columns}
    show_columns = list_columns
    edit_columns = [col for col in list_columns if col != 'id']
    add_columns = [col for col in list_columns if col != 'id']

    # Customize API endpoints
    @expose('/custom_endpoint', methods=['GET'])
    def custom_endpoint(self):
        # Add custom API logic here
        return self.response(200, result='Custom endpoint reached')

    # Add data validation
    def pre_add(self, item):
        # Perform data validation before adding
        self.validate_data(item)
        super().pre_add(item)

    def pre_update(self, item):
        # Perform data validation before updating
        self.validate_data(item)
        super().pre_update(item)

    def validate_data(self, item):
        # Add custom validation logic here
        pass

{generate_repr_method(table)}
"""
    ])
    generated_views.append((view_name, "ModelRestApi", table.name, icon))

def generate_chart_view(table: sa.Table) -> None:
    """
    Generate a ChartView for data visualization of a table.

    Args:
        table (sa.Table): SQLAlchemy Table object

    Returns:
        None
    """
    class_name = get_class_name(table.name, p)
    view_name = f"{class_name}ChartView"
    icon = get_view_icon(table.name, "ChartView")
    chart_type = determine_chart_type(table)
    x_axis = get_suitable_x_axis(table)
    y_axis = get_suitable_y_axis(table)

    generated_code.append([
        view_name,
        f"""
class {view_name}(GroupByChartView):
    datamodel = SQLAInterface({class_name})
    chart_title = '{class_name} Distribution'
    label_columns = {class_name}ModelView.label_columns
    chart_type = '{chart_type}'
    definitions = [
        {{
            'label': '{y_axis} by {x_axis}',
            'group': '{x_axis}',
            'series': ['{y_axis}']
        }}
    ]

    # Add custom chart options
    chart_options = {{
        'legend': {{'position': 'bottom'}},
        'animation': {{'duration': 1000, 'easing': 'easeOutQuad'}}
    }}

    # Customize data query
    def query_init(self, query):
        # Add any custom query logic here
        return query

    # Add drill-down capability
    @expose('/drilldown/<col>/<val>')
    @has_access
    def drilldown(self, col, val):
        # Implement drill-down logic here
        pass

{generate_repr_method(table)}
"""
    ])
    generated_views.append((view_name, "ChartView", table.name, icon))

def determine_chart_type(table: sa.Table) -> str:
    """
    Determine the most suitable chart type for a table.

    Args:
        table (sa.Table): SQLAlchemy Table object

    Returns:
        str: Suggested chart type
    """
    date_columns = [col for col in table.columns if isinstance(col.type, (sa.Date, sa.DateTime))]
    if date_columns:
        return 'LineChart'
    else:
        return 'BarChart'

def get_suitable_x_axis(table: sa.Table) -> str:
    """
    Determine a suitable x-axis for a chart based on the table structure.

    Args:
        table (sa.Table): SQLAlchemy Table object

    Returns:
        str: Name of the suggested x-axis column
    """
    date_columns = [col.name for col in table.columns if isinstance(col.type, (sa.Date, sa.DateTime))]
    if date_columns:
        return date_columns[0]
    else:
        string_columns = [col.name for col in table.columns if isinstance(col.type, (sa.String, sa.Text))]
        return string_columns[0] if string_columns else table.columns[0].name

def get_suitable_y_axis(table: sa.Table) -> str:
    """
    Determine a suitable y-axis for a chart based on the table structure.

    Args:
        table (sa.Table): SQLAlchemy Table object

    Returns:
        str: Name of the suggested y-axis column
    """
    numeric_columns = [col.name for col in table.columns if isinstance(col.type, (sa.Integer, sa.Float, sa.Numeric))]
    return numeric_columns[0] if numeric_columns else table.columns[0].name

def is_association_table(table: sa.Table) -> bool:
    """
    Check if a table is an association table (for many-to-many relationships).

    Args:
        table (sa.Table): SQLAlchemy Table object

    Returns:
        bool: True if the table is an association table, False otherwise
    """
    if len(table.columns) != 2:
        return False

    return all(isinstance(constraint, sa.ForeignKeyConstraint) for constraint in table.constraints
               if isinstance(constraint, sa.ForeignKeyConstraint))

def determine_relationship_name(fk_cols: List[str], table_name: str, referred_table: str) -> str:
    """
    Determine the relationship name based on foreign key columns.

    Args:
        fk_cols (List[str]): List of foreign key column names
        table_name (str): Name of the table containing the foreign key
        referred_table (str): Name of the table being referred to

    Returns:
        str: Determined relationship name
    """
    base_name = fk_cols[0].replace('_id', '').replace('_fk', '')

    # If the base name is the same as the referred table, use it as is
    if base_name == referred_table:
        return base_name

    # Otherwise, combine the base name with the referred table name
    return f"{base_name}_{referred_table}"

def determine_remote_relationship_name(cardinality: str, table_name: str, referred_table: str) -> str:
    """
    Determine the remote relationship name based on cardinality.

    Args:
        cardinality (str): Relationship cardinality ('one-to-many', 'many-to-many', etc.)
        table_name (str): Name of the table containing the foreign key
        referred_table (str): Name of the table being referred to

    Returns:
        str: Determined remote relationship name
    """
    if cardinality in ['one-to-many', 'many-to-many']:
        return p.plural(table_name)
    return f"{table_name}_{referred_table}"

def generate_view_registration_code() -> str:
    """
    Generate code for registering all created views.

    Returns:
        str: Python code for registering views
    """
    registration_code = [
        "def register_views(appbuilder):",
        "    # Register generated views"
    ]

    for view_class, model_name, view_type, icon in generated_views:
        if view_type == 'ModelView':
            registration_code.append(f"    appbuilder.add_view({view_class}, '{model_name}', icon='{icon}', category='Data')")
        elif view_type == 'MasterDetailView':
            registration_code.append(f"    appbuilder.add_view({view_class}, '{model_name}', icon='{icon}', category='Master Detail')")
        elif view_type == 'MultipleView':
            registration_code.append(f"    appbuilder.add_view({view_class}, '{model_name}', icon='{icon}', category='Multiple Views')")
        elif view_type == 'WizardView':
            registration_code.append(f"    appbuilder.add_view({view_class}, '{model_name} Wizard', icon='{icon}', category='Wizards')")
        elif view_type == 'ChartView':
            registration_code.append(f"    appbuilder.add_view({view_class}, '{model_name} Chart', icon='{icon}', category='Charts')")
        elif view_type == 'ModelRestApi':
            registration_code.append(f"    appbuilder.add_api({view_class})")

    return "\n".join(registration_code)

def write_to_file(output_file: str) -> None:
    """
    Write the generated code to a file.

    Args:
        output_file (str): Path to the output file

    Returns:
        None
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        for section_name, code in generated_code:
            f.write(f"# {section_name}\n")
            f.write(code)
            f.write("\n\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Flask-AppBuilder views from a database schema.")
    parser.add_argument("--uri", type=str, required=True, help="Database URI to connect to")
    parser.add_argument("--output", type=str, default="generated_views.py", help="Output file to write the generated views")
    args = parser.parse_args()

    try:
        generate_views(args.uri)
        write_to_file(args.output)
        print(f"{len(generated_views)} Views have been generated successfully and written to {args.output}")
    except Exception as e:
        logger.error(f"An error occurred during view generation: {str(e)}")
        raise

# End of gv8.py
