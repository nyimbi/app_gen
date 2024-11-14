"""
gv9.py: Advanced Flask-AppBuilder View Generator

This script generates comprehensive Flask-AppBuilder views from a database schema,
including ModelViews, MasterDetailViews, MultipleViews, WizardViews, ChartViews,
and RestApiViews. It also generates GraphQL schemas for the models.

Usage:
    python gv9.py --uri <database_uri> --output <output_file>

Dependencies:
    - SQLAlchemy
    - Flask-AppBuilder
    - graphene
    - inflect
"""

import sqlalchemy as sa
from sqlalchemy import (
    inspect,
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    ForeignKey,
    Table,
    ForeignKeyConstraint,
    PrimaryKeyConstraint,
    MetaData,
    create_engine,
)
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy.sql import sqltypes
import inflect
import math
import argparse
from typing import Any, Dict, List, Optional, Union, Tuple, Set
import os
from wtforms import (
    StringField,
    BooleanField,
    IntegerField,
    FloatField,
    DateField,
    DateTimeField,
    SelectField,
    HiddenField,
    TextAreaField,
    DecimalField,
    validators,
)
from nx_widgets import (
    TimePickerWidget,
    RatingWidget,
    RangeSliderWidget,
    RichTextEditorWidget,
    RelationshipGraphWidget,
    DurationWidget,
    DateRangePickerWidget,
    GeoPointWidget,
    MarkdownEditorWidget,
    MultiSelectWidget,
    FileUploadFieldWidget,
)


from view_utils import get_view_icon, write_templates
from utils import snake_to_pascal, snake_to_words, pascal_to_words, snake_pascal

# Set up logging
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize inflect engine
p = inflect.engine()

# Global variables
INDENT = "    "
NINDENT = "\n    "
AB_PREFIX = "ab_"

WIDGET_IMPORTS = """

from flask_appbuilder.fieldwidgets import (
    BS3TextFieldWidget, BS3TextAreaFieldWidget, BS3PasswordFieldWidget,
    Select2Widget, Select2ManyWidget, DatePickerWidget, DateTimePickerWidget

)
from flask_appbuilder.upload import BS3FileUploadFieldWidget
from flask_appbuilder import expose
from flask_caching import Cache

from wtforms.fields import (
    StringField, TextAreaField, IntegerField, FloatField, DecimalField,
    BooleanField, DateField, DateTimeField, TimeField, SelectField,
    SelectMultipleField, FileField, PasswordField, TimeField
    )
from wtforms import ValidationError
from wtforms.validators import (
    Length, DataRequired, InputRequired, MacAddress, NumberRange, Optional, Regexp,
    Email, EqualTo, IPAddress, URL, UUID, AnyOf, NoneOf
    )

from wtforms_sqlalchemy.fields import QuerySelectField
# from flask_appbuilder.forms import JSONField

# Import custom widgets
from .nx_widgets import (
    RangeSliderWidget, TagInputWidget, JSONEditorWidget, MarkdownEditorWidget,
    GeoPointWidget, CurrencyInputWidget, PhoneNumberWidget, RatingWidget, DurationWidget,
    RelationshipGraphWidget, FileUploadFieldWidget, ColorPickerWidget, DateRangePickerWidget,
    RichTextEditorWidget, MultiSelectWidget, TimePickerWidget, CheckBoxWidget, SwitchWidget,
    StarRatingWidget, ToggleButtonWidget, SliderWidget, AutocompleteWidget, PasswordStrengthWidget
)


# MultipleView Layout Options
LAYOUT_OPTIONS = {
    'tabs': 'Tabbed Layout',
    'accordion': 'Accordion Layout',
    'grid': 'Grid Layout',
    'list': 'List Layout',
    'cards': 'Card Layout',
    'sidebar': 'Sidebar Layout',
    'split': 'Split View Layout',
    'wizard': 'Wizard Layout'
}
"""


generated_views = []
generated_code = []
enum_types = {}

# Initialize GraphQL schema
# schema = graphene.Schema()


def generate_views(db_uri: str, config: Dict[str, Any] = None) -> None:
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
    if config is None:
        config = {}

    # Add imports and initial setup
    generated_code.append(
        [
            "imports",
            f"""
import math
import os
from sqlalchemy.exc import SQLAlchemyError
from flask_appbuilder import ModelView, MasterDetailView, MultipleView, ModelRestApi, BaseView
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.actions import action
from flask_appbuilder.security.decorators import has_access, permission_name
from flask_appbuilder.forms import DynamicForm
from flask_appbuilder.actions import action
from flask import session, flash, redirect, url_for, request, render_template, make_response, current_app
from flask_appbuilder.security.decorators import has_access
from flask_appbuilder.charts.views import GroupByChartView

from .models import *

import graphene
from graphene import relay, ObjectType, Schema
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField
{WIDGET_IMPORTS}


# Get references to appbuilder and db
appbuilder = current_app.extensions['appbuilder']
db = current_app.extensions['sqlalchemy'].db
# cache = current_app.extensions['cache'].cache
# cache = current_app.config['cache']
cache = Cache()
cache.init_app(current_app, {{'CACHE_TYPE': 'SimpleCache'}})

# Global list to store all generated views
generated_views = []
""",
        ]
    )

    for table_name in inspector.get_table_names():
        if table_name.lower().startswith(AB_PREFIX) or is_association_table(
            table_name, inspector
        ):
            continue
        table = metadata.tables[table_name]
        generate_model_view(table, inspector, metadata)
        generate_master_detail_views(table, metadata)
        generate_multiple_views(table, metadata, config)  # Pass the cnfig here
        generate_wizard_view(table)
        generate_graphql(table)
        generate_model_rest_api(table)
        generate_chart_view(table)

    # TODO Uncomment below and resolve
    # generate_main_query_and_schema(metadata)
    # Add view registration function
    generated_code.append(["register_views", generate_view_registration_code()])


def generate_model_view(
    table: sa.Table, inspector: sa.engine.reflection.Inspector, metadata: sa.MetaData
) -> None:
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
    class_name = snake_pascal(table.name, p)
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
        f"{INDENT}search_exclude_columns = ['file', 'photo', 'image', 'cert_img','rt_img','audio','video', 'map']",
        f"{INDENT}label_columns = {get_label_columns(table)}",
        generate_description_columns(table, inspector),
        "",
        f"{INDENT}# Field sets for add and edit forms",
        f"{INDENT}add_fieldsets = {field_sets}",
        f"{INDENT}edit_fieldsets = add_fieldsets",
        "",
        f"{INDENT}# Lazy loading for related data",
        f"{INDENT}list_template = 'list_with_lazy_loading.html'",
        "",
        "",
        f"{INDENT}@expose('/api/get_list')",
        f"{INDENT}@has_access",
        f"{INDENT}def api_get_list(self):",
        f"{INDENT}{INDENT}page = request.args.get('page', 1, type=int)",
        f"{INDENT}{INDENT}last_id = request.args.get('last_id', 0, type=int)",
        f"{INDENT}{INDENT}search = request.args.get('search', '')",
        f"{INDENT}{INDENT}",
        f"{INDENT}{INDENT}query = self.datamodel.session.query(self.datamodel.obj)",
        f"{INDENT}{INDENT}if last_id:",
        f"{INDENT}{INDENT}{INDENT}query = query.filter(self.datamodel.obj.id > last_id)",
        f"{INDENT}{INDENT}if search:",
        f"{INDENT}{INDENT}{INDENT}query = self.datamodel.query_search(query, search)",
        f"{INDENT}{INDENT}",
        f"{INDENT}{INDENT}items = query.order_by(self.datamodel.obj.id).limit(self.page_size).all()",
        f"{INDENT}{INDENT}",
        f"{INDENT}{INDENT}data = [{{col: getattr(item, col) for col in self.list_columns}} for item in items]",
        f"{INDENT}{INDENT}has_more = len(items) == self.page_size",
        f"{INDENT}{INDENT}",
        f"{INDENT}{INDENT}return jsonify({{",
        f"{INDENT}{INDENT}{INDENT}'data': data,",
        f"{INDENT}{INDENT}{INDENT}'has_more': has_more",
        f"{INDENT}{INDENT}}})",
        "",
        "",
        f"{INDENT}# Field sets for add and edit forms",
        f"{INDENT}add_fieldsets = {field_sets}",
        f"{INDENT}edit_fieldsets = add_fieldsets",
        "",
        f"{INDENT}# Lazy loading for related data",
        # f"""{INDENT}related_views = [{', '.join([f"'{snake_pascal(fk.column.table.name, p)}ModelView'" for fk in table.foreign_keys])}]""",
        f"{INDENT}list_template = 'list_with_lazy_loading.html'",
        "",
        # f"{INDENT}# Caching configuration",
        # f"{INDENT}cache_timeout = 60  # Cache for 60 seconds",
        "",
        # f"{INDENT}# Pagination configuration",
        # f"{INDENT}page_size = 20",
        # f"{INDENT}base_order = ('id', 'asc')",
        "",
        # f"{INDENT}# Search configuration",
        # f"{INDENT}search_form_query_rel_fields = {get_search_form_query_rel_fields(table, metadata)}",
        # "",
        # f"{INDENT}# Responsive design",
        # f"{INDENT}list_template = 'responsive_list.html'",
        # f"{INDENT}edit_template = 'responsive_edit.html'",
        # f"{INDENT}show_template = 'responsive_show.html'",
        "",
        f"""
    @expose('/filter/')
    @has_access
    def filter(self):
        filter_params = request.args.to_dict()
        page = filter_params.pop('page', 1, type=int)

        query = self.datamodel.session.query(self.datamodel.obj)

        # Apply filters
        for col, value in filter_params.items():
            if col in self.search_columns:
                if col in self.filter_rel_fields:
                    related_model = self.filter_rel_fields[col]
                    query = query.filter(getattr(self.datamodel.obj, col).has(related_model.id == value))
                else:
                    query = query.filter(FilterContains(getattr(self.datamodel.obj, col), value))

        # Paginate the results
        pagination = query.paginate(page=page, per_page=self.page_size, error_out=False)

        # Prepare the results
        items = [item.to_dict() for item in pagination.items]

        return self.render_template(
            self.filter_template,
            items=items,
            filter_params=filter_params,
            pagination=pagination,
            list_columns=self.list_columns,
            modelview_name=self.__class__.__name__,
            title=f"Filtered Results for {{self.datamodel.obj.__name__}}"
        )
        """,
        # f"{INDENT}# Interactive filters",
        # f"{INDENT}filter_rel_fields = {get_filter_rel_fields(table, metadata)}",
        # f"{INDENT}filter_exclude_columns = ['file', 'photo', 'image']",
        # f"{INDENT}filter_template = 'interactive_filters.html'",
        "",
        # f"{INDENT}# Base Filters",
        # f"{INDENT}base_filters = []",
        "",
        # generate_form_query_rel_fields(table, metadata),
        "",
        # f"{INDENT}# Form extra fields",
        # f"{INDENT}form_extra_fields = {{",
        # f"{generate_form_fields(table, metadata)}",
        # f"{INDENT}}}",
        "",
        # generate_validators(table),
        "",
        # TODO: Uncomment Custom Actions
        # generate_custom_actions(),
        "",
        # generate_lifecycle_hooks(),
        "",
        # f"{INDENT}@cache.memoize(timeout=cache_timeout)",
        # f"{INDENT}def query_count(self):",
        # f"{INDENT}{INDENT}return self.datamodel.count()",
        # "",
        # f"{INDENT}@cache.memoize(timeout=cache_timeout)",
        # f"{INDENT}def get_related_data(self, pk):",
        # f"{INDENT}{INDENT}item = self.datamodel.get(pk)",
        # f"{INDENT}{INDENT}related_data = {{}}",
        # f"{INDENT}{INDENT}for related_view in self.related_views:",
        # f"{INDENT}{INDENT}{INDENT}related_model = related_view.datamodel.obj",
        # f"{INDENT}{INDENT}{INDENT}relationship = next((r for r in self.datamodel.obj.__mapper__.relationships if r.mapper.class_ == related_model), None)",
        # f"{INDENT}{INDENT}{INDENT}if relationship:",
        # f"{INDENT}{INDENT}{INDENT}{INDENT}related_items = getattr(item, relationship.key)",
        # f"{INDENT}{INDENT}{INDENT}{INDENT}related_data[relationship.key] = [{{c: getattr(ri, c) for c in related_view.list_columns}} for ri in related_items]",
        # f"{INDENT}{INDENT}return related_data",
        # "",
        # f"{INDENT}@expose('/api/related/<pk>')",
        # f"{INDENT}@has_access",
        # f"{INDENT}def api_related(self, pk):",
        # f"{INDENT}{INDENT}related_data = self.get_related_data(pk)",
        # f"{INDENT}{INDENT}return jsonify(related_data)",
        f"",
        f"""
    @expose('/api/filter_results')
    @has_access
    def api_filter_results(self):
        page = request.args.get('page', 1, type=int)
        filters = {{key: value for key, value in request.args.items() if key not in ['page']}}

        query = self.datamodel.session.query(self.datamodel.obj)
        for col, value in filters.items():
            if value:
                if col in self.filter_rel_fields:
                    related_model = self.filter_rel_fields[col]
                    query = query.filter(getattr(self.datamodel.obj, col).has(related_model.id.in_(value.split(','))))
                else:
                    query = query.filter(getattr(self.datamodel.obj, col).ilike(f'%{{value}}%'))

        total_count = query.count()
        items = query.order_by(self.datamodel.obj.id).offset((page - 1) * self.page_size).limit(self.page_size).all()

        data = [{{col: getattr(item, col) for col in self.list_columns}} for item in items]

        return jsonify({{
            'data': data,
            'page': page,
            'total_pages': (total_count + self.page_size - 1) // self.page_size
        }})
        """,
        # f"{INDENT}def get_list(self):",
        # f"{INDENT}{INDENT}# Implement keyset pagination logic here",
        # f"{INDENT}{INDENT}last_id = request.args.get('last_id', 0, type=int)",
        # f"{INDENT}{INDENT}query = self.datamodel.session.query(self.datamodel.obj)",
        # f"{INDENT}{INDENT}if last_id:",
        # f"{INDENT}{INDENT}{INDENT}query = query.filter(self.datamodel.obj.id > last_id)",
        # f"{INDENT}{INDENT}query = query.order_by(self.datamodel.obj.id.asc()).limit(self.page_size)",
        # f"{INDENT}{INDENT}items = query.all()",
        # f"{INDENT}{INDENT}return self.render_template(",
        # f"{INDENT}{INDENT}{INDENT}self.list_template,",
        # f"{INDENT}{INDENT}{INDENT}items=items,",
        # f"{INDENT}{INDENT}{INDENT}last_id=items[-1].id if items else 0,",
        # f"{INDENT}{INDENT}{INDENT}has_more=len(items) == self.page_size",
        # f"{INDENT}{INDENT})",
        "",
        f"""
    @expose('/search/')
    @has_access
    def search(self):
        search_query = request.args.get('q', '')
        if search_query:
            query = self.datamodel.session.query(self.datamodel.obj)

            # Construct the search filter
            search_filter = []
            for col in self.search_columns:
                search_filter.append(FilterContains(getattr(self.datamodel.obj, col), search_query))

            # Apply the filter
            query = self.datamodel.query(query, search_filter)

            # Paginate the results
            page = request.args.get('page', 1, type=int)
            pagination = query.paginate(page=page, per_page=self.page_size, error_out=False)

            # Prepare the results with highlighting
            items = []
            for item in pagination.items:
                item_dict = item.to_dict()
                for col in self.search_columns:
                    value = str(getattr(item, col))
                    highlighted = value.replace(search_query, f'<mark>{{search_query}}</mark>')
                    item_dict[col + '_highlighted'] = highlighted
                items.append(item_dict)

            return self.render_template(
                self.search_template,
                items=items,
                search_query=search_query,
                pagination=pagination,
                list_columns=self.list_columns,
                modelview_name=self.__class__.__name__
            )

        return redirect(url_for(f'{{self.__class__.__name__}}.list'))
        """,
        "",
        # f"{INDENT}@expose('/filter/')",
        # f"{INDENT}@has_access",
        # f"{INDENT}def filter(self):",
        # f"{INDENT}{INDENT}filter_params = request.args.to_dict()",
        # f"{INDENT}{INDENT}query = self.datamodel.session.query(self.datamodel.obj)",
        # f"{INDENT}{INDENT}for column, value in filter_params.items():",
        # f"{INDENT}{INDENT}{INDENT}if column in self.filter_rel_fields:",
        # f"{INDENT}{INDENT}{INDENT}{INDENT}related_model = self.filter_rel_fields[column]",
        # f"{INDENT}{INDENT}{INDENT}{INDENT}query = query.join(related_model).filter(related_model.id == value)",
        # f"{INDENT}{INDENT}{INDENT}elif column not in self.filter_exclude_columns:",
        # f"{INDENT}{INDENT}{INDENT}{INDENT}query = query.filter(getattr(self.datamodel.obj, column) == value)",
        # f"{INDENT}{INDENT}items = query.all()",
        # f"{INDENT}{INDENT}return self.render_template(",
        # f"{INDENT}{INDENT}{INDENT}'filter_results.html',",
        # f"{INDENT}{INDENT}{INDENT}items=items,",
        # f"{INDENT}{INDENT}{INDENT}filter_params=filter_params",
        # f"{INDENT}{INDENT})",
        "",
        generate_repr_method(table),
    ]

    generated_code.append([view_name, "\n".join(view_code)])
    generated_views.append((view_name, "ModelView", table.name, icon))


def generate_custom_actions() -> str:
    """
    Generate custom actions for the view class.

    Returns:
        str: String representation of custom actions
    """
    return f"""
    # Enable in-place editing
    can_edit = True


    def pre_add(self, item):
        # Set created_at and updated_at if they exist
        if hasattr(item, 'created_at'):
            item.created_at = datetime.datetime.now()
        if hasattr(item, 'updated_at'):
            item.updated_at = datetime.datetime.now()

    def pre_update(self, item):
        # Update updated_at if it exists
        if hasattr(item, 'updated_at'):
            item.updated_at = datetime.datetime.now()

    # User-Specific Actions
    @expose('/favorite/<pk>')
    @has_access
    def favorite(self, pk):
        item = self.datamodel.get(pk)
        if item:
            current_user.favorites.append(item)
            db.session.commit()
            flash(f"Added {{item}} to favorites", "success")
        return redirect(request.referrer)

    @expose('/watchlist/<pk>')
    @has_access
    def watchlist(self, pk):
        item = self.datamodel.get(pk)
        if item:
            current_user.watchlist.append(item)
            db.session.commit()
            flash(f"Added {{item}} to watchlist", "success")
        return redirect(request.referrer)

    @expose('/personalize', methods=['GET', 'POST'])
    @has_access
    def personalize(self):
        form = PersonalizeForm()
        if form.validate_on_submit():
            # Save personalization settings
            session['custom_columns'] = request.form.getlist('columns')
            session['column_order'] = json.loads(request.form.get('column_order', '[]'))
            session['page_size'] = form.page_size.data
            flash('View settings updated successfully', 'success')
            return redirect(url_for(f'{self.__class__.__name__}.list'))

        # Get current settings
        current_columns = session.get('custom_columns', self.list_columns)
        current_page_size = session.get('page_size', self.page_size)

        return self.render_template(
            'personalize.html',
            form=form,
            columns=self.list_columns,
            current_columns=current_columns,
            current_page_size=current_page_size,
            modelview_name=self.__class__.__name__
        )

    def get_user_settings(self):
        return {{
            'list_columns': session.get('custom_columns', self.list_columns),
            'page_size': session.get('page_size', self.page_size)
        }}

    # Override the list method to use personalized settings
    @expose('/')
    @has_access
    def list(self):
        settings = self.get_user_settings()
        self._list_columns = settings['list_columns']
        self.page_size = settings['page_size']
        return super().list()

    # @expose('/personalize')
    # @has_access
    # def personalize(self):
    #     if request.method == 'POST':
    #         current_user.list_columns = request.form.getlist('columns')
    #         current_user.list_order = request.form.get('order')
    #         db.session.commit()
    #         flash("View settings updated", "success")
    #     return self.render_template('personalize.html', columns=self.list_columns, current_columns=current_user.list_columns, current_order=current_user.list_order)

    # Integration with External Services
    def post_add(self, item):
        pass  #TODO
        # Example: Send email notification
        # send_email_notification(f"New {{self.__class__.__name__}} added", f"A new {{self.__class__.__name__}} has been added: {{item}}")

    def post_update(self, item):
        pass #TODO
        # Example: Update external API
        # update_external_api(item)

    def post_delete(self, item):
        pass #TODO
        # Example: Log to external service
        # log_to_external_service(f"{{self.__class__.__name__}} deleted: {{item}}")

    # Custom actions
    @action("muldelete", "Delete", "Delete all Really?", "fa-trash", multiple=True)
    def muldelete(self, items):
        if isinstance(items, list):
            self.datamodel.delete_all(items)
            self.update_redirect()
        else:
            self.datamodel.delete(items)
        return redirect(self.get_redirect())

    @action("print", "Print", "Print selected items?", "fa-print", multiple=True)
    def print_items(self, items):
        if not isinstance(items, list):
            items = [items]

        # Convert items to dictionaries
        item_dicts = []
        for item in items:
            item_dict = {{col: getattr(item, col) for col in self.list_columns}}
            item_dicts.append(item_dict)

        return render_template(
            'print_items.html',
            items=item_dicts,
            list_columns=self.list_columns,
            model=self.datamodel.obj.__name__,
            now=datetime.now()
        )


    @expose('/print_preview')
    @has_access
    def print_preview(self):
        # Get all items or a subset based on your requirements
        items = self.datamodel.session.query(self.datamodel.obj).all()
        item_dicts = [{{col: getattr(item, col) for col in self.list_columns}} for item in items]

        return render_template(
            'print_items.html',
            items=item_dicts,
            list_columns=self.list_columns,
            model=self.datamodel.obj.__name__,
            now=datetime.now()
        )


    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]
        csv_data = self.datamodel.export_as_csv(items)
        response = make_response(csv_data)
        response.headers["Content-Disposition"] = f"attachment; filename={{self.__class__.__name__}}_export.csv"
        response.headers["Content-Type"] = "text/csv"
        return response

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]
        for item in items:
            if not hasattr(item, 'is_bookmarked'):
                logger.warning(f"Model {{self.__class__.__name__}} does not have 'is_bookmarked' attribute")
                flash(f"Cannot bookmark items of type {{self.__class__.__name__}}", "warning")
                return redirect(self.get_redirect())
            item.is_bookmarked = True
        self.datamodel.bulk_update(items)
        flash(f"{{len(items)}} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @action("merge", "Merge", "Merge selected items?", "fa-compress", single=False)
    def merge_items(self, items):
        if isinstance(items, list) and len(items) > 1:
            # Implement merge logic here
            flash(f"Merged {{len(items)}} items", "success")
        else:
            flash("Select at least two items to merge", "warning")
        return redirect(self.get_redirect())

    @action("split", "Split", "Split selected item?", "fa-scissors", single=True)
    def split_item(self, item):
        # Implement split logic here
        flash(f"Split item {{item}}", "success")
        return redirect(self.get_redirect())

    @action("clone", "Clone", "Clone selected item?", "fa-clone", single=True)
    def clone_item(self, item):
        new_item = self.datamodel.obj()
        for col in self.list_columns:
            setattr(new_item, col, getattr(item, col))
        self.datamodel.add(new_item)
        flash(f"Cloned item {{item}}", "success")
        return redirect(self.get_redirect())

    @action("archive", "Archive", "Archive selected items?", "fa-archive", single=False)
    def archive_items(self, items):
        if isinstance(items, list):
            for item in items:
                item.is_archived = True
            self.datamodel.bulk_update(items)
            flash(f"Archived {{len(items)}} items", "success")
        else:
            flash("No items selected", "warning")
        return redirect(self.get_redirect())

    @action("restore", "Restore", "Restore selected items?", "fa-undo", single=False)
    def restore_items(self, items):
        if isinstance(items, list):
            for item in items:
                item.is_archived = False
            self.datamodel.bulk_update(items)
            flash(f"Restored {{len(items)}} items", "success")
        else:
            flash("No items selected", "warning")
        return redirect(self.get_redirect())

    @action("bulk_edit", "Bulk Edit", "Edit selected items?", "fa-edit", single=False)
    def bulk_edit(self, items):
        if isinstance(items, list):
            return redirect(url_for('.bulk_edit_form', ids=','.join([str(item.id) for item in items])))
        else:
            flash("No items selected", "warning")
        return redirect(self.get_redirect())

    @action("bulk_edit", "Bulk Edit", "Bulk edit selected items?", "fa-edit", multiple=True)
    def bulk_edit(self, items):
        if not isinstance(items, list):
            items = [items]
        ids = [item.id for item in items]
        return redirect(url_for(f'{{self.__class__.__name__}}.bulk_edit_form', ids=','.join(map(str, ids))))

    @expose('/bulk_edit_form/<ids>', methods=['GET', 'POST'])
    @has_access
    def bulk_edit_form(self, ids):
        ids = [int(id) for id in ids.split(',')]
        items = self.datamodel.get_all_by_ids(ids)

        if not items:
            flash("No items selected for bulk edit.", "warning")
            return redirect(url_for(f'{{self.__class__.__name__}}.list'))

        form = BulkEditForm()

        if request.method == 'POST':
            if form.validate_on_submit():
                updated_fields = {{field.name: field.data for field in form if field.data is not None}}
                for item in items:
                    for field, value in updated_fields.items():
                        setattr(item, field, value)

                self.datamodel.session.commit()
                flash(f"Successfully updated {{len(items)}} items.", "success")
                return redirect(url_for(f'{{self.__class__.__name__}}.list'))

        return self.render_template(
            'bulk_edit.html',
            form=form,
            items=[item.to_dict() for item in items],
            ids=','.join(map(str, ids)),
            list_columns=self.list_columns,
            modelview_name=self.__class__.__name__,
            model_name=self.datamodel.obj.__name__
        )

    # Additional custom actions

    @action("export_pdf", "Export PDF", "Export selected items as PDF?", "fa-file-pdf-o", single=False)
    def export_pdf(self, items):
        if isinstance(items, list):
            # Implement PDF export logic here
            flash(f"Exported {{len(items)}} items to PDF", "success")
        else:
            flash("No items selected", "warning")
        return redirect(self.get_redirect())

    @action("send_email", "Send Email", "Send email about selected items?", "fa-envelope", single=False)
    def send_email(self, items):
        if isinstance(items, list):
            # Implement email sending logic here
            flash(f"Sent email about {{len(items)}} items", "success")
        else:
            flash("No items selected", "warning")
        return redirect(self.get_redirect())

    @action("generate_report", "Generate Report", "Generate report for selected items?", "fa-file-text", single=False)
    def generate_report(self, items):
        if isinstance(items, list):
            # Implement report generation logic here
            flash(f"Generated report for {{len(items)}} items", "success")
        else:
            flash("No items selected", "warning")
        return redirect(self.get_redirect())

    @action("add_tag", "Add Tag", "Add tag to selected items?", "fa-tag", single=False)
    def add_tag(self, items):
        if isinstance(items, list):
            # Implement tag adding logic here
            flash(f"Added tag to {{len(items)}} items", "success")
        else:
            flash("No items selected", "warning")
        return redirect(self.get_redirect())

    @action("remove_tag", "Remove Tag", "Remove tag from selected items?", "fa-tag", single=False)
    def remove_tag(self, items):
        if isinstance(items, list):
            # Implement tag removal logic here
            flash(f"Removed tag from {{len(items)}} items", "success")
        else:
            flash("No items selected", "warning")
        return redirect(self.get_redirect())

    @action("bulk_approve", "Bulk Approve", "Approve selected items?", "fa-check", single=False)
    def bulk_approve(self, items):
        if isinstance(items, list):
            for item in items:
                item.status = 'approved'  # Assuming there's a status field
            self.datamodel.bulk_update(items)
            flash(f"Approved {{len(items)}} items", "success")
        else:
            flash("No items selected", "warning")
        return redirect(self.get_redirect())

    @action("bulk_reject", "Bulk Reject", "Reject selected items?", "fa-times", single=False)
    def bulk_reject(self, items):
        if isinstance(items, list):
            for item in items:
                item.status = 'rejected'  # Assuming there's a status field
            self.datamodel.bulk_update(items)
            flash(f"Rejected {{len(items)}} items", "success")
        else:
            flash("No items selected", "warning")
        return redirect(self.get_redirect())

    @action("assign_to", "Assign To", "Assign selected items to a user?", "fa-user", single=False)
    def assign_to(self, items):
        if isinstance(items, list):
            # Implement user assignment logic here
            flash(f"Assigned {{len(items)}} items", "success")
        else:
            flash("No items selected", "warning")
        return redirect(self.get_redirect())

    @action("schedule", "Schedule", "Schedule action for selected items?", "fa-calendar", single=False)
    def schedule_action(self, items):
        if isinstance(items, list):
            # Implement scheduling logic here
            flash(f"Scheduled action for {{len(items)}} items", "success")
        else:
            flash("No items selected", "warning")
        return redirect(self.get_redirect())

    @action("export_json", "Export JSON", "Export selected items as JSON?", "fa-file-code-o", single=False)
    def export_json(self, items):
        if isinstance(items, list):
            # Implement JSON export logic here
            flash(f"Exported {{len(items)}} items to JSON", "success")
        else:
            flash("No items selected", "warning")
        return redirect(self.get_redirect())
    """


def get_list_columns(columns: List[str]) -> List[str]:
    """
    Get a list of column names suitable for list views, excluding certain system columns.

    Args:
        columns (List[str]): List of column names

    Returns:
        List[str]: List of column names suitable for list views
    """
    ignored_fields = {
        "id",
        "created_at",
        "updated_at",
        "created_by_fk",
        "changed_by_fk",
    }

    return [
        col
        for col in columns
        if (col not in ignored_fields)
        and (
            not col.endswith(
                ("_id_fk", "_img", "_audio", "_picture", "_blob", "_video")
            )
        )
    ]


def get_field_sets(table: sa.Table) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Generate field sets for forms, grouping columns into sets of 4.

    Args:
        table (sa.Table): SQLAlchemy Table object

    Returns:
        List[Tuple[str, Dict[str, Any]]]: List of field sets with labels
    """
    ignored_fields = {
        "id",
        "created_at",
        "updated_at",
        "created_by_fk",
        "changed_by_fk",
    }
    valid_columns = [
        col.name for col in table.columns if col.name not in ignored_fields
    ]

    # Group fields into sets of 4
    field_sets = [valid_columns[i : i + 4] for i in range(0, len(valid_columns), 4)]

    # Create field_sets list
    return [
        (
            f"Field Set {i+1}",
            {"fields": field_set, "expanded": True if i == 0 else False},
        )
        for i, field_set in enumerate(field_sets)
    ]


def get_search_columns(table: sa.Table) -> List[str]:
    """
    Get a list of columns suitable for searching.

    Args:
        table (sa.Table): SQLAlchemy Table object

    Returns:
        List[str]: List of column names suitable for searching
    """
    return [
        col.name
        for col in table.columns
        if isinstance(col.type, (sa.String, sa.Text, sa.Unicode, sa.UnicodeText))
        and not col.name.endswith(("_img", "_audio", "_picture", "_blob", "_video"))
    ]


def get_search_form_query_rel_fields(
    table: sa.Table, metadata: sa.MetaData
) -> Dict[str, Dict[str, Any]]:
    """
    Generate a dictionary of related fields that can be used for advanced search in the ModelView.

    Args:
        table (sa.Table): SQLAlchemy Table object
        metadata (sa.MetaData): SQLAlchemy MetaData object

    Returns:
        Dict[str, Dict[str, Any]]: A dictionary where keys are relationship field names and values are
                                   dictionaries containing query factory and label configurations
    """
    search_form_query_rel_fields = {}

    for fk in table.foreign_keys:
        parent_table = fk.column.table
        parent_class_name = snake_pascal(parent_table.name, p)
        relationship_name = fk.parent.name.replace("_id", "")

        # Determine the label column for the related model
        label_column = get_label_column(parent_table)

        search_form_query_rel_fields[relationship_name] = {
            "query_factory": f"lambda: db.session.query({parent_class_name})",
            "get_label": f"lambda x: str(x.{label_column})",
            "widget": "Select2Widget()",
        }

    # Check for many-to-many relationships
    for other_table in metadata.tables.values():
        if is_association_table(other_table):
            foreign_keys = [
                fk
                for fk in other_table.foreign_keys
                if fk.column.table.name != table.name
            ]
            if (
                table.name in [fk.column.table.name for fk in other_table.foreign_keys]
                and foreign_keys
            ):
                other_table_name = foreign_keys[0].column.table.name
                other_class_name = snake_pascal(other_table_name, p)
                relationship_name = p.plural(other_table_name.lower())

                # Determine the label column for the related model
                label_column = get_label_column(metadata.tables[other_table_name])

                search_form_query_rel_fields[relationship_name] = {
                    "query_factory": f"lambda: db.session.query({other_class_name})",
                    "get_label": f"lambda x: str(x.{label_column})",
                    "widget": "Select2ManyWidget()",
                }

    return search_form_query_rel_fields


def get_form_extra_fields(table: sa.Table, session) -> Dict[str, Any]:
    """
    Generate extra form fields for related models.

    Args:
        table (sa.Table): SQLAlchemy Table object
        session: SQLAlchemy session

    Returns:
        Dict[str, Any]: Dictionary of extra form fields
    """
    extra_fields = {}
    for fk in table.foreign_keys:
        col_name = fk.parent.name
        related_model = fk.column.table
        related_model_class = snake_pascal(related_model.name, p)
        extra_fields[col_name] = QuerySelectField(
            f"{snake_to_words(col_name)}",
            query_factory=lambda m=related_model_class: session.query(m),
            widget=Select2Widget(),
        )
    return extra_fields


def get_label_column(table: sa.Table) -> str:
    """
    Determine the most suitable column to use as a label for a table.

    This function tries to find a column in the following order of preference:
    1. Columns named 'name', 'title', 'label', or 'description'
    2. The first string column
    3. The primary key column

    Args:
        table (sa.Table): SQLAlchemy Table object

    Returns:
        str: Name of the column to use as a label
    """
    # Priority columns that are commonly used as labels
    priority_columns = ["name", "title", "label", "description"]

    # Check for priority columns
    for col_name in priority_columns:
        if col_name in table.columns:
            return col_name

    # If no priority column is found, use the first string column
    for column in table.columns:
        if isinstance(column.type, (sa.String, sa.Text, sa.Unicode, sa.UnicodeText)):
            return column.name

    # If no string column is found, use the primary key
    if table.primary_key:
        return next(col.name for col in table.primary_key.columns)

    # If there's no primary key (which should be rare), use the first column
    return table.columns[0].name


def get_label_columns(table: sa.Table) -> Dict[str, str]:
    """
    Generate dictionary of user-friendly labels for columns.

    Args:
        table (sa.Table): SQLAlchemy Table object

    Returns:
        Dict[str, str]: Dictionary of column names and their user-friendly labels
    """
    return {
        col.name: snake_to_words(col.name)
        for col in table.columns
        if not col.name.endswith(("_img", "_audio", "_picture", "_blob", "_video"))
    }


def generate_description_columns(
    table: sa.Table, inspector: sa.engine.reflection.Inspector
) -> str:
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
        if column["comment"]:
            descriptions[column["name"]] = column["comment"]

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
        referred_class = snake_pascal(referred_table.name, p)
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
        parent_class_name = snake_pascal(parent_table.name, p)
        relationship_name = fk.parent.name.replace("_id", "")
        filter_rel_fields[relationship_name] = parent_class_name

    # Check for many-to-many relationships
    for other_table in metadata.tables.values():
        if is_association_table(other_table):
            foreign_keys = [
                fk
                for fk in other_table.foreign_keys
                if fk.column.table.name != table.name
            ]
            if (
                table.name in [fk.column.table.name for fk in other_table.foreign_keys]
                and foreign_keys
            ):
                other_table_name = foreign_keys[0].column.table.name
                other_class_name = snake_pascal(other_table_name, p)
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

# def snake_pascal(table_name: str, p: inflect.engine) -> str:
#     """
#     Generate a class name from a table name.

#     Args:
#         table_name (str): Name of the table
#         p (inflect.engine): Inflect engine for singular/plural conversions

#     Returns:
#         str: Generated class name
#     """
#     return ''.join(word.capitalize() for word in p.singular_noun(table_name).split('_'))


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
        if column.name in [
            "id",
            "created_at",
            "updated_at",
            "created_by_fk",
            "changed_by_fk",
        ]:
            continue

        field_code = generate_form_field(column, metadata)
        if field_code:
            form_fields.append(f"{INDENT}{INDENT}{field_code},")

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
        if column.type.length and column.type.length > 200:
            return f"TextAreaField('{label}', widget=BS3TextAreaFieldWidget())"
        return f"StringField('{label}', widget=BS3TextFieldWidget())"
    elif isinstance(column.type, Text):
        return f"TextAreaField('{label}', widget=BS3TextAreaFieldWidget())"
    elif isinstance(column.type, Integer):
        return f"IntegerField('{label}', widget=BS3TextFieldWidget())"
    elif isinstance(column.type, Float):
        return f"FloatField('{label}', widget=BS3TextFieldWidget())"
    elif isinstance(column.type, Numeric):
        return f"DecimalField('{label}', widget=BS3TextFieldWidget())"
    elif isinstance(column.type, Boolean):
        return f"BooleanField('{label}', widget=CheckBoxWidget())"
    elif isinstance(column.type, Date):
        return f"DateField('{label}', widget=DatePickerWidget())"
    elif isinstance(column.type, DateTime):
        return f"DateTimeField('{label}', widget=DateTimePickerWidget())"
    elif isinstance(column.type, Time):
        return f"TimeField('{label}', widget=TimePickerWidget())"
    elif isinstance(column.type, Enum):
        choices = [(choice, choice) for choice in column.type.enums]
        return f"SelectField('{label}', choices={choices}, widget=Select2Widget())"
    elif isinstance(column.type, ForeignKey):
        related_table = column.foreign_keys[0].column.table
        related_model = snake_pascal(related_table.name, p)
        return f"QuerySelectField('{label}', query_factory=lambda: db.session.query({related_model}), widget=Select2Widget())"
    elif isinstance(column.type, JSON):
        return f"JSONField('{label}', widget=JSONEditorWidget())"
    elif isinstance(column.type, ARRAY):
        return f"SelectMultipleField('{label}', widget=Select2ManyWidget())"
    elif isinstance(column.type, LargeBinary):
        return f"FileField('{label}', widget=BS3FileUploadFieldWidget())"
    elif isinstance(column.type, postgresql.JSONB):
        return f"JSONField('{label}', widget=JSONEditorWidget())"
    elif isinstance(column.type, postgresql.ARRAY):
        return f"SelectMultipleField('{label}', widget=Select2ManyWidget())"
    elif isinstance(column.type, postgresql.HSTORE):
        return f"JSONField('{label}', widget=JSONEditorWidget())"

    # Custom widgets based on field name
    elif field_name.endswith("_color"):
        return f"StringField('{label}', widget=ColorPickerWidget())"
    elif field_name.endswith("_range"):
        return f"StringField('{label}', widget=RangeSliderWidget())"
    elif field_name.endswith("_rating"):
        return f"FloatField('{label}', widget=StarRatingWidget())"
    elif field_name.endswith("_duration"):
        return f"StringField('{label}', widget=DurationWidget())"
    elif field_name.endswith("_markdown"):
        return f"TextAreaField('{label}', widget=MarkdownEditorWidget())"
    elif field_name.endswith("_rich_text"):
        return f"TextAreaField('{label}', widget=RichTextEditorWidget())"
    elif field_name.endswith("_tags"):
        return f"StringField('{label}', widget=TagInputWidget())"
    elif field_name.endswith("_relationship"):
        return f"StringField('{label}', widget=RelationshipGraphWidget())"
    elif field_name.endswith("_geopoint"):
        return f"StringField('{label}', widget=GeoPointWidget())"
    elif field_name.endswith("_daterange"):
        return f"StringField('{label}', widget=DateRangePickerWidget())"
    elif field_name.endswith("_switch"):
        return f"BooleanField('{label}', widget=SwitchWidget())"
    elif field_name.endswith("_toggle"):
        return f"BooleanField('{label}', widget=ToggleButtonWidget())"
    elif field_name.endswith("_slider"):
        return f"IntegerField('{label}', widget=SliderWidget())"
    elif field_name.endswith("_autocomplete"):
        return f"StringField('{label}', widget=AutocompleteWidget())"
    elif field_name.endswith("_password"):
        return f"PasswordField('{label}', widget=PasswordStrengthWidget())"

    # Default to StringField if type is not recognized
    return f"StringField('{label}', widget=BS3TextFieldWidget())"


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
        # TODO: Uncomment the folliwng 2 lines
        if not column.nullable and not column.primary_key:
            column_validators.append("InputRequired()")
        if isinstance(column.type, String) and column.type.length:
            column_validators.append(f"Length(max={column.type.length})")

        if column_validators:
            validators[column.name] = column_validators

    if validators:
        # Use a list comprehension to create the string representation without quotes
        validator_strings = [
            f"'{column_name}': [{', '.join(column_validators)}]"
            for column_name, column_validators in validators.items()
        ]
        return f"{INDENT}validators_columns = {{{', '.join(validator_strings)}}}"
    return f"{INDENT}validators_columns = {{}}"

    # if validators:
    #     return f"{INDENT}validators_columns = {validators}"
    # return f"{INDENT}validators_columns = {{}}"


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
        logger.info(f"New {{self.__class__.__name__}} added: {{item}}")

    def post_update(self, item):
        logger.info(f"{{self.__class__.__name__}} updated: {{item}}")

    def post_delete(self, item):
        logger.info(f"{{self.__class__.__name__}} deleted: {{item}}")
    """


def generate_repr_method(table: sa.Table) -> str:
    """
    Generate a __repr__ method for a view class.

    Args:
        table (sa.Table): SQLAlchemy Table object

    Returns:
        str: String representation of the __repr__ method
    """
    display_column = next(
        (col.name for col in table.columns if col.name in ["name", "title", "label"]),
        "id",
    )
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
        parent_class_name = snake_pascal(parent_table.name, p)
        child_class_name = snake_pascal(table.name, p)
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
        generated_views.append(
            (view_name, "MasterDetailView", f"{parent_table.name}_{table.name}", icon)
        )


# Define layout options
LAYOUT_OPTIONS = {
    "tabs": "Tabbed Layout",
    "accordion": "Accordion Layout",
    "grid": "Grid Layout",
    "list": "List Layout",
    "cards": "Card Layout",
    "sidebar": "Sidebar Layout",
    "split": "Split View Layout",
    "wizard": "Wizard Layout",
}


def get_related_tables(
    table: sa.Table, metadata: sa.MetaData, config: Dict[str, Any]
) -> Set[sa.Table]:
    """
    Get related tables based on foreign key relationships and configuration.

    Args:
        table (sa.Table): The main table
        metadata (sa.MetaData): SQLAlchemy MetaData object
        config (Dict[str, Any]): Configuration dictionary

    Returns:
        Set[sa.Table]: Set of related tables
    """
    related_tables = set()
    for fk in table.foreign_keys:
        related_tables.add(fk.column.table)
    for other_table in metadata.tables.values():
        for fk in other_table.foreign_keys:
            if fk.column.table == table:
                related_tables.add(other_table)

    # Filter related tables based on configuration
    if "included_tables" in config:
        related_tables = {
            t for t in related_tables if t.name in config["included_tables"]
        }
    if "excluded_tables" in config:
        related_tables = {
            t for t in related_tables if t.name not in config["excluded_tables"]
        }

    return related_tables


def generate_related_views_dict(related_tables: Set[sa.Table]) -> str:
    """
    Generate a dictionary of related views.

    Args:
        related_tables (Set[sa.Table]): Set of related tables

    Returns:
        str: String representation of the related views dictionary
    """
    views_dict = []
    for table in related_tables:
        class_name = snake_pascal(table.name, p)
        views_dict.append(f"'{table.name}': '{class_name}ModelView'")
    return ", ".join(views_dict)


def generate_multiple_views(
    table: sa.Table, metadata: sa.MetaData, config: Dict[str, Any]
) -> None:
    """
    Generate enhanced MultipleViews for tables with multiple related tables.

    Args:
        table (sa.Table): SQLAlchemy Table object
        metadata (sa.MetaData): SQLAlchemy MetaData object
        config (Dict[str, Any]): Configuration dictionary

    Returns:
        None
    """
    related_tables = get_related_tables(table, metadata, config)

    if len(related_tables) > 1:
        class_name = snake_pascal(table.name, p)
        view_name = f"{class_name}MultipleView"
        icon = get_view_icon(table.name, "MultipleView")

        # Get layout configuration
        layout_config = config.get("multiple_view_layout", "tabs")
        if layout_config not in LAYOUT_OPTIONS:
            layout_config = "tabs"  # Default to tabs if invalid option is provided

        view_code = f"""
class {view_name}(MultipleView):
    related_views = {{
        {generate_related_views_dict(related_tables)}
    }}
    list_title = '{snake_to_words(table.name)} Multiple View'
    layout_config = '{layout_config}'
    layout_options = {LAYOUT_OPTIONS}
    items_per_page = {config.get('items_per_page', 10)}
    search_columns = {config.get('search_columns', '[]')}

    def get_views(self):
        return [view for view_name, view in self.related_views.items() if self.can_access(view)]

    @expose('/')
    @has_access
    def list(self):
        relationships = []
        for fk in {class_name}.__table__.foreign_keys:
            relationships.append({{
                'from': '{table.name}',
                'to': fk.column.table.name,
                'from_col': fk.parent.name,
                'to_col': fk.column.name
            }})
        for related_view_name, related_view in self.related_views.items():
            for fk in related_view.datamodel.obj.__table__.foreign_keys:
                if fk.column.table.name == '{table.name}':
                    relationships.append({{
                        'from': related_view.datamodel.obj.__tablename__,
                        'to': '{table.name}',
                        'from_col': fk.parent.name,
                        'to_col': fk.column.name
                    }})
        return self.render_template(
            'multiple_view.html',
            views=self.get_views(),
            layout=self.layout_config,
            layout_options=self.layout_options,
            main_table='{table.name}',
            relationships=relationships
        )

    @expose('/api/data/<view_name>')
    @has_access
    def api_data(self, view_name):
        page = request.args.get('page', 1, type=int)
        view_instance = self.related_views.get(view_name)
        if view_instance:
            query = self.datamodel.session.query(view_instance.datamodel.obj)
            count = query.count()
            query = self.apply_filters(query, view_name)
            items = query.offset((page - 1) * self.items_per_page).limit(self.items_per_page).all()
            data = [item.to_dict() for item in items]
            return jsonify({{
                'data': data,
                'total': count,
                'page': page,
                'pages': (count + self.items_per_page - 1) // self.items_per_page
            }})
        return jsonify({{'error': 'View not found'}}), 404

    @expose('/api/search')
    @has_access
    def search(self):
        search_term = request.args.get('q', '')
        results = {{}}
        for view_name, view in self.related_views.items():
            query = self.datamodel.session.query(view.datamodel.obj)
            query = self.apply_search(query, view_name, search_term)
            results[view_name] = [item.to_dict() for item in query.all()]
        return jsonify(results)

    def apply_filters(self, query, view_name):
        filters = request.args.get('filters', '{{}}')
        filters = json.loads(filters)
        view = self.related_views[view_name]
        for column, value in filters.items():
            if hasattr(view.datamodel.obj, column):
                query = query.filter(getattr(view.datamodel.obj, column) == value)
        return query

    def apply_search(self, query, view_name, search_term):
        view = self.related_views[view_name]
        if search_term and self.search_columns:
            search_query = []
            for column in self.search_columns:
                if hasattr(view.datamodel.obj, column):
                    search_query.append(getattr(view.datamodel.obj, column).ilike(f'%{{search_term}}%'))
            if search_query:
                query = query.filter(sa.or_(*search_query))
        return query

    @expose('/api/aggregate/<view_name>')
    @has_access
    def aggregate(self, view_name):
        view_instance = self.related_views.get(view_name)
        if view_instance:
            query = self.datamodel.session.query(view_instance.datamodel.obj)
            aggregations = request.args.get('aggregations', '{{}}')
            aggregations = json.loads(aggregations)
            result = {{}}
            for column, func_name in aggregations.items():
                if hasattr(view_instance.datamodel.obj, column):
                    col = getattr(view_instance.datamodel.obj, column)
                    if func_name == 'count':
                        result[column] = query.count()
                    elif func_name == 'sum':
                        result[column] = query.with_entities(sa.func.sum(col)).scalar()
                    elif func_name == 'avg':
                        result[column] = query.with_entities(sa.func.avg(col)).scalar()
                    elif func_name == 'min':
                        result[column] = query.with_entities(sa.func.min(col)).scalar()
                    elif func_name == 'max':
                        result[column] = query.with_entities(sa.func.max(col)).scalar()
            return jsonify(result)
        return jsonify({{'error': 'View not found'}}), 404

    @action('export_all', 'Export All', 'Export data from all related views?', 'fa-download')
    def export_all(self):
        data = {{}}
        for view_name, view in self.related_views.items():
            query = self.datamodel.session.query(view.datamodel.obj)
            data[view_name] = [item.to_dict() for item in query.all()]
        return self.response(200, result=data, export_name='{class_name}_export')

    # def get_relationships_json(self):
    #     relationships = []
    #     for fk in {table.name}.foreign_keys:
    #         relationships.append({{
    #             'from': '{table.name}',
    #             'to': fk.column.table.name,
    #             'from_col': fk.parent.name,
    #             'to_col': fk.column.name
    #         }})
    #     for other_table in self.related_views.values():
    #         for fk in other_table.datamodel.obj.__table__.foreign_keys:
    #             if fk.column.table.name == '{table.name}':
    #                 relationships.append({{
    #                     'from': other_table.datamodel.obj.__tablename__,
    #                     'to': '{table.name}',
    #                     'from_col': fk.parent.name,
    #                     'to_col': fk.column.name
    #                 }})
    #     return json.dumps(relationships)

    @expose('/change_layout/<layout>')
    @has_access
    def change_layout(self, layout):
        if layout in self.layout_options:
            self.layout_config = layout
            return redirect(url_for('.list'))
        flash('Invalid layout option', 'error')
        return redirect(url_for('.list'))

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
    class_name = snake_pascal(table.name, p)
    view_name = f"{class_name}WizardView"
    icon = get_view_icon(table.name, "WizardView")
    columns = [
        c.name
        for c in table.columns
        if c.name
        not in ["id", "created_at", "updated_at", "created_by_fk", "changed_by_fk"]
    ]
    total_steps = math.ceil(len(columns) / 5)

    wizard_code = f"""

class {view_name}(BaseView):
    route_base = '/{table.name.lower()}_wizard'
    datamodel = SQLAInterface({class_name})
    total_steps = {total_steps}

    def __init__(self):
        super().__init__()
        self._init_steps()

    def _init_steps(self):
        self.steps = {{}}
        for step in range(1, self.total_steps + 1):
            step_name = f'step{{step}}'
            self.steps[step_name] = getattr(self, step_name)

    def is_step_complete(self, step):
        return session.get(f'{{self.__class__.__name__}}_step{{step}}_complete', False)

    def mark_step_complete(self, step):
        session[f'{{self.__class__.__name__}}_step{{step}}_complete'] = True

    def get_progress(self):
        completed_steps = sum(self.is_step_complete(step) for step in range(1, self.total_steps + 1))
        return (completed_steps / self.total_steps) * 100

    @expose('/')
    @has_access
    def list(self):
        return redirect(url_for(f'.step1'))

    @expose('/reset')
    @has_access
    def reset(self):
        for step in range(1, self.total_steps + 1):
            session.pop(f'{{self.__class__.__name__}}_step{{step}}_complete', None)
            session.pop(f'step{{step}}_data', None)
        flash('Your progress has been reset. Start again from the beginning!', 'info')
        return redirect(url_for(f'.step1'))

    def render_wizard(self, step, form, step_description):
        return self.render_template(
            'wizard.html',
            form=form,
            progress=self.get_progress(),
            current_step=step,
            total_steps=self.total_steps,
            step_description=step_description,
            previous_step=step-1 if step > 1 else None,
            next_step=step+1 if step < self.total_steps else 'submit'
        )

    def get_form_data(self, step):
        return session.get(f'step{{step}}_data', {{}})

    def save_form_data(self, step, data):
        session[f'step{{step}}_data'] = data

    @expose('/back/<int:step>', methods=['GET'])
    @has_access
    def back(self, step):
        if step > 1:
            return redirect(url_for(f'.step{{step-1}}'))
        return redirect(url_for('.list'))

    """

    for step in range(1, total_steps + 1):
        start_idx = (step - 1) * 5
        end_idx = min(step * 5, len(columns))
        step_columns = columns[start_idx:end_idx]

        wizard_code += f"""
    @expose('/step{step}', methods=['GET', 'POST'])
    @has_access
    @permission_name('step{step}')
    def step{step}(self):
        form = DynamicForm()
        {generate_form_fields_for_wizard(step_columns, table)}

        if request.method == 'POST':
            if form.validate_on_submit():
                self.save_form_data({step}, form.data)
                self.mark_step_complete({step})
                next_step = {step + 1 if step < total_steps else 'submit'}
                return redirect(url_for(f'.{{next_step}}'))
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f'{{field}}: {{error}}', 'error')

        form_data = self.get_form_data({step})
        for field in form:
            if field.name in form_data:
                field.data = form_data[field.name]

        return self.render_wizard({step}, form, 'Step {step}: {", ".join(step_columns)}')
    """

    wizard_code += f"""
    @expose('/submit', methods=['GET', 'POST'])
    @has_access
    @permission_name('submit')
    def submit(self):
        if all(self.is_step_complete(step) for step in range(1, self.total_steps + 1)):
            combined_data = {{}}
            for step in range(1, self.total_steps + 1):
                combined_data.update(self.get_form_data(step))

            item = self.datamodel.obj()
            try:
                for key, value in combined_data.items():
                    setattr(item, key, value)
                self.pre_add(item)
                self.datamodel.add(item)
                self.post_add(item)

                for step in range(1, self.total_steps + 1):
                    session.pop(f'step{{step}}_data', None)
                    session.pop(f'{{self.__class__.__name__}}_step{{step}}_complete', None)

                flash('Form submitted successfully!', 'success')
                return redirect(url_for('.list'))
            except SQLAlchemyError as e:
                flash(f'An database error occurred: {{str(e)}}', 'error')
                self.datamodel.session.rollback()
            except Exception as e:
                flash(f'An error occurred: {{str(e)}}', 'error')
            return redirect(url_for('.step1'))
        else:
            flash('Please complete all steps before submitting.', 'warning')
            return redirect(url_for('.step1'))

    def pre_add(self, item):
        pass

    def post_add(self, item):
        pass
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
        field_def = generate_form_field(col_obj, table.metadata)
        form_fields.append(f"form.{column} = {field_def}")
    return "\n        ".join(form_fields)


def generate_graphql(table: sa.Table) -> None:
    """
    Generate GraphQL schema and queries for a table.

    Args:
        table (sa.Table): SQLAlchemy Table object

    Returns:
        None
    """
    class_name = snake_pascal(table.name, p)

    # Generate enum types first
    enum_fields = ""
    for column in table.columns:
        if isinstance(column.type, sa.Enum):
            enum_name = f"{table.name.upper()}_{column.name.upper()}_ENUM"
            if enum_name not in enum_types:
                enum_values = [value for value in column.type.enums]
                enum_fields += f"""
class {enum_name}(graphene.Enum):
    {f'{NINDENT}'.join([f'{value.upper()} = "{value}"' for value in enum_values])}
"""
                enum_types[enum_name] = True

    graphql_code = f"""
{enum_fields}

class {class_name}Node(SQLAlchemyObjectType):
    class Meta:
        model = {class_name}
        interfaces = (graphene.relay.Node, )

{class_name}Connection = graphene.relay.Connection.create_type(
    "{class_name}Connection",
    node={class_name}Node
)

class {class_name}Query(graphene.ObjectType):
    node = graphene.relay.Node.Field()
    all_{table.name} = SQLAlchemyConnectionField({class_name}Connection)

    {table.name.lower()} = graphene.Field({class_name}Node, id=graphene.Int())
    def resolve_{table.name.lower()}(self, info, id):
        return {class_name}.query.get(id)
"""

    generated_code.append([f"{class_name}GraphQL", graphql_code])


def generate_main_query_and_schema(metadata):
    """
    Generate the main Query class and Schema after all models have been processed.
    """
    query_classes = [
        f"{snake_pascal(table.name, p)}Query" for table in metadata.tables.values()
    ]

    main_query_code = f"""
class Query({', '.join(query_classes)}):
    pass

schema = graphene.Schema(query=Query)
"""

    generated_code.append(["MainQueryAndSchema", main_query_code])


def generate_model_rest_api(table: sa.Table) -> None:
    """
    Generate a ModelRestApi for RESTful API access to a table.

    Args:
        table (sa.Table): SQLAlchemy Table object

    Returns:
        None
    """
    class_name = snake_pascal(table.name, p)
    view_name = f"{class_name}RestApi"
    columns = [c.name for c in table.columns]
    icon = get_view_icon(table.name, "ModelRestApi")
    generated_code.append(
        [
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
""",
        ]
    )
    generated_views.append((view_name, "ModelRestApi", table.name, icon))


def generate_chart_view(table: sa.Table) -> None:
    """
    Generate a ChartView for data visualization of a table.

    Args:
        table (sa.Table): SQLAlchemy Table object

    Returns:
        None
    """
    class_name = snake_pascal(table.name, p)
    view_name = f"{class_name}ChartView"
    icon = get_view_icon(table.name, "ChartView")
    chart_type = determine_chart_type(table)
    x_axis = get_suitable_x_axis(table)
    y_axis = get_suitable_y_axis(table)

    generated_code.append(
        [
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
""",
        ]
    )
    generated_views.append((view_name, "ChartView", table.name, icon))


def determine_chart_type(table: sa.Table) -> str:
    """
    Determine the most suitable chart type for a table.

    Args:
        table (sa.Table): SQLAlchemy Table object

    Returns:
        str: Suggested chart type
    """
    date_columns = [
        col for col in table.columns if isinstance(col.type, (sa.Date, sa.DateTime))
    ]
    if date_columns:
        return "LineChart"
    else:
        return "BarChart"


def get_suitable_x_axis(table: sa.Table) -> str:
    """
    Determine a suitable x-axis for a chart based on the table structure.

    Args:
        table (sa.Table): SQLAlchemy Table object

    Returns:
        str: Name of the suggested x-axis column
    """
    date_columns = [
        col.name
        for col in table.columns
        if isinstance(col.type, (sa.Date, sa.DateTime))
    ]
    if date_columns:
        return date_columns[0]
    else:
        string_columns = [
            col.name
            for col in table.columns
            if isinstance(col.type, (sa.String, sa.Text))
        ]
        return string_columns[0] if string_columns else table.columns[0].name


def get_suitable_y_axis(table: sa.Table) -> str:
    """
    Determine a suitable y-axis for a chart based on the table structure.

    Args:
        table (sa.Table): SQLAlchemy Table object

    Returns:
        str: Name of the suggested y-axis column
    """
    numeric_columns = [
        col.name
        for col in table.columns
        if isinstance(col.type, (sa.Integer, sa.Float, sa.Numeric))
    ]
    return numeric_columns[0] if numeric_columns else table.columns[0].name


# def is_association_table(table: sa.Table) -> bool:
#     """
#     Check if a table is an association table (for many-to-many relationships).

#     Args:
#         table (sa.Table): SQLAlchemy Table object

#     Returns:
#         bool: True if the table is an association table, False otherwise
#     """
#     if len(table.columns) != 2:
#         return False

#     return all(isinstance(constraint, sa.ForeignKeyConstraint) for constraint in table.constraints
#                if isinstance(constraint, sa.ForeignKeyConstraint))


def determine_relationship_name(
    fk_cols: List[str], table_name: str, referred_table: str
) -> str:
    """
    Determine the relationship name based on foreign key columns.

    Args:
        fk_cols (List[str]): List of foreign key column names
        table_name (str): Name of the table containing the foreign key
        referred_table (str): Name of the table being referred to

    Returns:
        str: Determined relationship name
    """
    base_name = fk_cols[0].replace("_id", "").replace("_fk", "")

    # If the base name is the same as the referred table, use it as is
    if base_name == referred_table:
        return base_name

    # Otherwise, combine the base name with the referred table name
    return f"{base_name}_{referred_table}"


def determine_remote_relationship_name(
    cardinality: str, table_name: str, referred_table: str
) -> str:
    """
    Determine the remote relationship name based on cardinality.

    Args:
        cardinality (str): Relationship cardinality ('one-to-many', 'many-to-many', etc.)
        table_name (str): Name of the table containing the foreign key
        referred_table (str): Name of the table being referred to

    Returns:
        str: Determined remote relationship name
    """
    if cardinality in ["one-to-many", "many-to-many"]:
        return p.plural(table_name)
    return f"{table_name}_{referred_table}"


def is_association_table(table_name, inspector):
    """Improved detection of association tables.
    Check if a table is likely an association table.

    #     An association table typically has the following characteristics:
    #     0. The name ends in _assoc (our formal convention)
    #     1. At least two foreign keys
    #     2. May have additional columns for metadata (e.g., creation date, status)
    #     3. Usually has a relatively small number of columns compared to regular entity tables
    #     4. The name often follows a pattern like 'table1_table2' or 'table1_to_table2'
    """
    if table_name.endswith("_assoc"):
        return True

    fks = inspector.get_foreign_keys(table_name)
    columns = inspector.get_columns(table_name)

    if len(fks) < 2:
        return False

    non_fk_columns = [
        col
        for col in columns
        if col["name"] not in [c for fk in fks for c in fk["constrained_columns"]]
    ]

    # Allow for id, timestamps, and a couple of additional metadata columns
    allowed_extra = ["id", "created_at", "updated_at", "created_by", "updated_by"]
    return len([col for col in non_fk_columns if col["name"] not in allowed_extra]) <= 2


def generate_view_registration_code() -> str:
    """
    Generate code for registering all created views.

    Returns:
        str: Python code for registering views
    """
    registration_code = [
        "def register_views(appbuilder):",
        "    # Register generated views",
    ]

    for view_class, view_type, model_name, icon in generated_views:
        if view_type == "ModelView":
            registration_code.append(
                f"    appbuilder.add_view({view_class}, '{model_name}', icon='{icon}', category='Data')"
            )
        elif view_type == "MasterDetailView":
            registration_code.append(
                f"    appbuilder.add_view({view_class}, '{model_name}', icon='{icon}', category='Master Detail')"
            )
        elif view_type == "MultipleView":
            registration_code.append(
                f"    appbuilder.add_view({view_class}, '{model_name}', icon='{icon}', category='Multiple Views')"
            )
        elif view_type == "WizardView":
            registration_code.append(
                f"    appbuilder.add_view({view_class}, '{model_name} Wizard', icon='{icon}', category='Wizards')"
            )
        elif view_type == "ChartView":
            registration_code.append(
                f"    appbuilder.add_view({view_class}, '{model_name} Chart', icon='{icon}', category='Charts')"
            )
        elif view_type == "ModelRestApi":
            registration_code.append(f"    appbuilder.add_api({view_class})")

    # Add custom theming
    registration_code.extend(
        [
            "",
            "    # Set custom theme",
            "    appbuilder.app.config['FAB_THEME'] = 'cyborg'  # You can change 'cyborg' to any other supported theme",
        ]
    )

    # Add any global view customizations
    registration_code.extend(
        [
            "",
            "    # Global view customizations",
            "    # for view in appbuilder.baseviews:",
            "    #    if hasattr(view, 'datamodel') and hasattr(view.datamodel, 'obj'):",
            "    #        view.search_columns = get_search_columns(view.datamodel.obj.__table__)",
            "    #        view.add_form_extra_fields = get_form_extra_fields(view.datamodel.obj.__table__, appbuilder.get_session)",
            "    #        view.edit_form_extra_fields = view.add_form_extra_fields",
        ]
    )

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
    with open(output_file, "w") as f:
        for section_name, code in generated_code:
            f.write(f"# {section_name}\n")
            f.write(code)
            f.write("\n\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Flask-AppBuilder views from a database schema."
    )
    parser.add_argument(
        "--uri", type=str, required=True, help="Database URI to connect to"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="generated_views.py",
        help="Output file to write the generated views",
    )
    args = parser.parse_args()

    try:
        generate_views(args.uri, {})
        write_to_file(args.output)
        print(
            f"{len(generated_views)} Views have been generated successfully and written to {args.output}"
        )
    except Exception as e:
        logger.error(f"An error occurred during view generation: {str(e)}")
        raise

# End of gv8.py
