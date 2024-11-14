# from _typeshed import Self
import sqlalchemy as sa
from sqlalchemy import inspect
import inflect
import math
import argparse
# from flask_appbuilder.charts.views import GroupByChartView
# from flask_appbuilder.models.group import aggregate_count
# from flask_appbuilder.widgets import ListThumbnail
# from flask import flash, redirect, request, render_template, make_response, url_for
# # from flask_appbuilder.security.decorators import has_access
# from flask_login import current_user
from view_utils import get_view_icon
from utils import get_class_name

# Global list to store all generated views
generated_views = []

# List to store generated code
generated_code = []

def generate_views(db_uri):
    engine = sa.create_engine(db_uri)
    inspector = inspect(engine)
    metadata = sa.MetaData()
    metadata.reflect(bind=engine)
    p = inflect.engine()

    # Add imports and initial setup
    generated_code.append([
        "imports",
        """from flask_appbuilder import ModelView, MasterDetailView, MultipleView, ModelRestApi
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.fieldwidgets import BS3TextFieldWidget, Select2Widget, DatePickerWidget
from flask_appbuilder.forms import DynamicForm
from wtforms import StringField, IntegerField, DateField, SelectField
from flask_appbuilder.actions import action
from flask import session, redirect, url_for, flash, Markup
from flask_appbuilder.baseviews import expose, BaseView
from flask_appbuilder.widgets import FormVerticalWidget, ListThumbnail
from flask_appbuilder.charts.views import GroupByChartView
from flask_appbuilder.models.group import aggregate_count
from flask_appbuilder.api import BaseApi, expose
from flask import flash, redirect, request, render_template, make_response, url_for
from flask_appbuilder.security.decorators import has_access
from flask_login import current_user
from . import appbuilder, db
from .models import *
from .view_utils import get_view_icon
import datetime
import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField

# Global list to store all generated views
generated_views = []

class BeautifulListWidget(ListThumbnail):
    template = 'beautiful_list.html'

class BeautifulFormWidget(FormVerticalWidget):
    template = 'beautiful_form.html'

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
        return self.render_template(
            'wizard.html',
            form=form,
            progress=self.get_progress(),
            current_step=step,
            total_steps=self.total_steps,
            step_description=step_description
        )

class SessionManagedView(BaseView):
    @expose("/")
    def list(self):
        return self.render_template("list.html", partial_data=session.get("partial_form_data"))

    @expose("/add", methods=["GET", "POST"])
    def add(self):
        form = self.add_form()
        if form.validate_on_submit():
            self._save_form_to_db(form)
            session.pop("partial_form_data", None)
            return redirect(url_for(f"{self.__class__.__name__}.list"))
        else:
            session["partial_form_data"] = form.data
        return self.render_template("add.html", form=form)
"""
    ])

    for table_name in inspector.get_table_names():
        table = metadata.tables[table_name]
        generate_model_view(table, p)
        generate_master_detail_views(table, metadata, p)
        generate_multiple_views(table, metadata, p)
        generate_wizard_view(table, p)
        generate_graphql(table, p)
        generate_ModelRestApi(table, p)
        generate_chart_view(table, p)

    # Add view registration function
    generated_code.append([
        "register_views",
        """
def register_views():
""" + "\n".join([f"    appbuilder.add_view({class_name}, '{table_name}', icon='{icon}', category='Views')"
                  for class_name, view_type, table_name, icon in generated_views]) + """

    # Gamification: Reminder for incomplete forms
    @appbuilder.app.context_processor
    def inject_notifications():
        notifications = []
        for view_name, view in appbuilder.baseviews.items():
            if isinstance(view, WizardView):
                progress = view.get_progress()
                if 0 < progress < 100:
                    notifications.append(f"Continue your {view.__class__.__name__[:-10]} form! You're {progress:.0f}% done.")
        return dict(notifications=notifications)

# GraphQL schema
schema = graphene.Schema(query=Query)
"""
    ])

def get_list_columns(columns):
    ignored_fields = {'id', 'updated_at', 'updated_by', 'created_at', 'created_by', 'is_bookmarked', 'is_archived'}
    return [col for col in columns if col not in ignored_fields]

def get_field_sets(table):
    ignored_fields = {'id', 'updated_at', 'updated_by', 'created_at', 'created_by', 'is_bookmarked', 'is_archived'}
    valid_columns = [col for col in table.columns if col.name not in ignored_fields]

    # Group fields into sets of 4
    field_sets = [valid_columns[i:i+4] for i in range(0, len(valid_columns), 4)]

    # Create field_sets dictionary
    field_sets_dict = {
        f"Field Set {i+1}": [
            (col.name, col.name.replace('_', ' ').title()) for col in field_set
        ] for i, field_set in enumerate(field_sets)
    }

    return field_sets_dict


def generate_model_view(table, p):
    class_name = get_class_name(table.name, p)
    view_name = f"{class_name}ModelView"
    columns = [c.name for c in table.columns]
    list_columns = get_list_columns(columns)
    field_sets = get_field_sets(table)
    icon = get_view_icon(table.name, "ModelView")

    generated_code.append([
        f"{view_name}",
        f"""
class {view_name}(ModelView):
    datamodel = SQLAInterface({class_name})
    list_columns = {list_columns}
    show_columns = list_columns
    edit_columns = list_columns
    add_columns = list_columns
    list_widget = BeautifulListWidget
    edit_widget = BeautifulFormWidget
    add_widget = BeautifulFormWidget
    show_widget = BeautifulFormWidget

    # Field sets for add and edit forms
    field_sets = {field_sets}

    # Enhanced search functionality
    search_columns = {list_columns}

    # Improved labels and descriptions
    label_columns = {{
        {', '.join([f"'{col}': '{col.replace('_', ' ').title()}'" for col in list_columns])}
    }}
    description_columns = {{
        {', '.join([f"'{col}': 'Enter the {col.replace('_', ' ')} here'" for col in list_columns])}
    }}

    # Custom formatters for better data presentation
    formatters_columns = {{
        'created_at': lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if x else '',
        'updated_at': lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if x else '',
    }}

    # Enhanced form field widgets
    add_form_extra_fields = {{
        {', '.join([generate_form_field(c) for c in table.columns if c.name in list_columns])}
    }}

    # Enable in-place editing
    can_edit = True

    # Custom actions
    @action("delete_all", "Delete All", "Are you sure you want to delete all records?", "fa-trash", multiple=True)
    def delete_all(self, items):
        if isinstance(items, list):
            self.datamodel.delete_all(items)
            flash(f"Deleted {{len(items)}} records", "success")
        else:
            flash("No records selected", "warning")
        return redirect(request.referrer)

    @action("print", "Print", "Print the selected items?", "fa-print", single=False)
    def print_items(self, items):
        if isinstance(items, list):
            return render_template('print_items.html', items=items, columns=self.list_columns)
        else:
            flash("No items selected", "warning")
        return redirect(request.referrer)

    @action("export_csv", "Export CSV", "Export selected items to CSV?", "fa-file-excel-o", single=False)
    def export_csv(self, items):
        if isinstance(items, list):
            csv_data = self.datamodel.export_as_csv(items)
            response = make_response(csv_data)
            response.headers["Content-Disposition"] = f"attachment; filename=export.csv"
            response.headers["Content-Type"] = "text/csv"
            return response
        else:
            flash("No items selected", "warning")
        return redirect(request.referrer)

    @action("bookmark", "Bookmark", "Bookmark selected items?", "fa-bookmark", single=False)
    def bookmark_items(self, items):
        if isinstance(items, list):
            for item in items:
                item.is_bookmarked = True
            self.datamodel.bulk_update(items)
            flash(f"Bookmarked {{len(items)}} items", "success")
        else:
            flash("No items selected", "warning")
        return redirect(request.referrer)

    @action("merge", "Merge", "Merge selected items?", "fa-compress", single=False)
    def merge_items(self, items):
        if isinstance(items, list) and len(items) > 1:
            # Implement merge logic here
            flash(f"Merged {{len(items)}} items", "success")
        else:
            flash("Select at least two items to merge", "warning")
        return redirect(request.referrer)

    @action("split", "Split", "Split selected item?", "fa-scissors", single=True)
    def split_item(self, item):
        # Implement split logic here
        flash(f"Split item {{item}}", "success")
        return redirect(request.referrer)

    @action("clone", "Clone", "Clone selected item?", "fa-clone", single=True)
    def clone_item(self, item):
        new_item = self.datamodel.obj()
        for col in self.list_columns:
            setattr(new_item, col, getattr(item, col))
        self.datamodel.add(new_item)
        flash(f"Cloned item {{item}}", "success")
        return redirect(request.referrer)

    @action("archive", "Archive", "Archive selected items?", "fa-archive", single=False)
    def archive_items(self, items):
        if isinstance(items, list):
            for item in items:
                item.is_archived = True
            self.datamodel.bulk_update(items)
            flash(f"Archived {{len(items)}} items", "success")
        else:
            flash("No items selected", "warning")
        return redirect(request.referrer)

    @action("restore", "Restore", "Restore selected items?", "fa-undo", single=False)
    def restore_items(self, items):
        if isinstance(items, list):
            for item in items:
                item.is_archived = False
            self.datamodel.bulk_update(items)
            flash(f"Restored {{len(items)}} items", "success")
        else:
            flash("No items selected", "warning")
        return redirect(request.referrer)

    @action("bulk_edit", "Bulk Edit", "Edit selected items?", "fa-edit", single=False)
    def bulk_edit(self, items):
        if isinstance(items, list):
            return redirect(url_for('.bulk_edit_form', ids=','.join([str(item.id) for item in items])))
        else:
            flash("No items selected", "warning")
        return redirect(request.referrer)

    @expose('/bulk_edit_form/<ids>')
    @has_access
    def bulk_edit_form(self, ids):
        items = self.datamodel.get_list_by_ids(ids.split(','))
        form = self.add_form()
        if request.method == 'POST':
            form = self.add_form(request.form)
            if form.validate():
                for item in items:
                    form.populate_obj(item)
                self.datamodel.bulk_update(items)
                return redirect(self.get_redirect())
        return self.render_template('bulk_edit.html', form=form, items=items)

    # Advanced Filtering and Sorting
    base_filters = []
    base_order = []

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

    @expose('/personalize')
    @has_access
    def personalize(self):
        if request.method == 'POST':
            current_user.list_columns = request.form.getlist('columns')
            current_user.list_order = request.form.get('order')
            db.session.commit()
            flash("View settings updated", "success")
        return self.render_template('personalize.html', columns=self.list_columns, current_columns=current_user.list_columns, current_order=current_user.list_order)

    # Integration with External Services
    def post_add(self, item):
        # Example: Send email notification
        send_email_notification(f"New {{self.__class__.__name__}} added", f"A new {{self.__class__.__name__}} has been added: {{item}}")

    def post_update(self, item):
        # Example: Update external API
        update_external_api(item)

    def post_delete(self, item):
        # Example: Log to external service
        log_to_external_service(f"{{self.__class__.__name__}} deleted: {{item}}")

"""
    ])
    generated_views.append((view_name, "ModelView", table.name, icon))

def generate_master_detail_views(table, metadata, p):
    for fk in table.foreign_keys:
        parent_table = metadata.tables[fk.column.table.name]
        parent_class_name = get_class_name(parent_table.name, p)
        child_class_name = get_class_name(table.name, p)
        icon = get_view_icon(table.name, "MasterDetailView")
        view_name = f"{parent_class_name}{child_class_name}MasterDetailView"
        generated_code.append([
            view_name,
            f"""
class {view_name}(MasterDetailView):
    datamodel = SQLAInterface({parent_class_name})
    related_views = [{child_class_name}ModelView]
    list_widget = BeautifulListWidget
    edit_widget = BeautifulFormWidget
    show_widget = BeautifulFormWidget
"""
        ])
        generated_views.append((view_name, "MasterDetailView", f"{parent_table.name}_{table.name}", icon))


def generate_multiple_views(table, metadata, p):
    if len(table.foreign_keys) > 1:
        class_name = get_class_name(table.name, p)
        icon = get_view_icon(table.name, "MultipleView")
        view_name = f"{class_name}MultipleView"
        related_views = [f"{get_class_name(fk.column.table.name, p)}ModelView" for fk in table.foreign_keys]
        generated_code.append([
            view_name,
            f"""
class {view_name}(MultipleView):
    views = [{', '.join(related_views)}]
"""
        ])
        generated_views.append((view_name, "MultipleView", table.name, icon))

def generate_wizard_view(table, p):
    class_name = get_class_name(table.name, p)
    view_name = f"{class_name}WizardView"
    icon = get_view_icon(table.name, "WizardView")
    columns = [c.name for c in table.columns]
    total_steps = math.ceil(len(columns) / 5)

    wizard_code = f"""
class {view_name}(WizardView):
    datamodel = SQLAInterface({class_name})
    total_steps = {total_steps}

    def __init__(self):
        super().__init__()
        self._init_steps()

"""

    for step in range(1, total_steps + 1):
        start_idx = (step - 1) * 5
        end_idx = min(step * 5, len(columns))
        step_columns = columns[start_idx:end_idx]

        wizard_code += f"""
    @expose('/step{step}', methods=['GET', 'POST'])
    def step{step}(self):
        form = DynamicForm()
"""
        for column in step_columns:
            wizard_code += f"        form.{column} = {generate_form_field(table.columns[columns.index(column)]).split(': ')[1]}\n"

        wizard_code += f"""
        if form.validate_on_submit():
            session['step{step}_data'] = form.data
            self.mark_step_complete({step})
            next_step = {step + 1 if step < total_steps else 1}
            return redirect(url_for(f'.step{{next_step}}'))

        form_data = session.get('step{step}_data', {{}})
        form = DynamicForm(**form_data)
        widget = BeautifulFormWidget()
        return self.render_wizard({step}, widget(form), 'Step {step}: {", ".join(step_columns)}')

"""

    wizard_code += """
    @expose('/submit', methods=['GET', 'POST'])
    def submit(self):
        if all(self.is_step_complete(step) for step in range(1, self.total_steps + 1)):
            # Combine data from all steps
            combined_data = {}
            for step in range(1, self.total_steps + 1):
                combined_data.update(session.get(f'step{step}_data', {}))

            # Create new record
            item = self.datamodel.obj()
            for key, value in combined_data.items():
                setattr(item, key, value)
            self.datamodel.add(item)

            # Clear session data
            for step in range(1, self.total_steps + 1):
                session.pop(f'step{step}_data', None)
                session.pop(f'{self.__class__.__name__}_step{step}_complete', None)

            flash('Form submitted successfully!', 'success')
            return redirect(url_for('.step1'))
        else:
            flash('Please complete all steps before submitting.', 'warning')
            return redirect(url_for('.step1'))
"""

    generated_code.append([view_name, wizard_code])
    generated_views.append((view_name, "WizardView", table.name, icon))

def generate_graphql(table, p):
    class_name = get_class_name(table.name, p)
    generated_code.append([
        f"{class_name}GraphQL",
        f"""
class {class_name}Object(SQLAlchemyObjectType):
    class Meta:
        model = {class_name}
        interfaces = (graphene.relay.Node, )

class {class_name}Connection(graphene.relay.Connection):
    class Meta:
        node = {class_name}Object

class Query(graphene.ObjectType):
    node = graphene.relay.Node.Field()
    all_{table.name} = SQLAlchemyConnectionField({class_name}Connection)
"""
    ])

def generate_ModelRestApi(table, p):
    class_name = get_class_name(table.name, p)
    view_name = f"{class_name}RestApi"
    columns = [c.name for c in table.columns]
    icon = get_view_icon(table.name, "ModelRestApiView")
    generated_code.append([
        view_name,
        f"""
class {view_name}(ModelRestApi):
    resource_name = '{table.name}'
    datamodel = SQLAInterface({class_name})
    allow_browser_login = True
    list_columns = {columns}
    show_columns = list_columns
    edit_columns = list_columns
    add_columns = list_columns
"""
    ])
    generated_views.append((view_name, "ModelRestApi", table.name, icon))

def generate_chart_view(table, p):
    class_name = get_class_name(table.name, p)
    view_name = f"{class_name}ChartView"
    columns = [c.name for c in table.columns]
    icon = get_view_icon(table.name, "ChartView")
    generated_code.append([
        view_name,
        f"""
class {view_name}(GroupByChartView):
    datamodel = SQLAInterface({class_name})
    chart_title = '{class_name} Distribution'
    label_columns = {class_name}ModelView.label_columns
    definitions = [
        {{
            'label': 'Distribution',
            'group': '{columns[0]}',
            'series': [(aggregate_count, '{columns[0]}')]
        }}
    ]
"""
    ])
    generated_views.append((view_name, "ChartView", table.name, icon))

def generate_form_field(column):
    if isinstance(column.type, sa.String):
        return f"'{column.name}': StringField('{column.name.replace('_', ' ').title()}', widget=BS3TextFieldWidget())"
    elif isinstance(column.type, sa.Integer):
        return f"'{column.name}': IntegerField('{column.name.replace('_', ' ').title()}')"
    elif isinstance(column.type, sa.Date):
        return f"'{column.name}': DateField('{column.name.replace('_', ' ').title()}', widget=DatePickerWidget())"
    elif isinstance(column.type, sa.Enum):
        choices = [(choice, choice) for choice in column.type.enums]
        return f"'{column.name}': SelectField('{column.name.replace('_', ' ').title()}', choices={choices}, widget=Select2Widget())"
    else:
        return f"'{column.name}': StringField('{column.name.replace('_', ' ').title()}', widget=BS3TextFieldWidget())"

def write_to_file(output_file):
    with open(output_file, 'w') as f:
        for section_name, code in generated_code:
            f.write(f"# {section_name}\n")
            f.write(code)
            f.write("\n\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Flask-AppBuilder views from a database schema.")
    parser.add_argument("--uri", help="Database URI to connect to")
    parser.add_argument("--output", help="Output file to write the generated views")
    args = parser.parse_args()

    generate_views(args.uri)
    write_to_file(args.output)
    print(f"{len(generated_views)} Views have been generated successfully and written to {args.output}")
