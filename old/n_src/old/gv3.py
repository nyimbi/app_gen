import sqlalchemy as sa
from sqlalchemy import inspect
import inflect
import math
from flask_appbuilder.charts.views import GroupByChartView
from flask_appbuilder.models.group import aggregate_count
from flask_appbuilder.widgets import ListThumbnail
from .view_utils import get_view_icon
from .utils import get_class_name

# Global list to store all generated views
generated_views = []

def generate_views(db_uri, output_file='views.py'):
    engine = sa.create_engine(db_uri)
    inspector = inspect(engine)
    metadata = sa.MetaData()
    metadata.reflect(bind=engine)
    p = inflect.engine()

    with open(output_file, 'w') as f:
        f.write("""from flask_appbuilder import ModelView, MasterDetailView, MultipleView, ModelRestApi
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

""")

        for table_name in inspector.get_table_names():
            table = metadata.tables[table_name]
            generate_model_view(f, table, p)
            generate_master_detail_views(f, table, metadata, p)
            generate_multiple_views(f, table, metadata, p)
            generate_wizard_view(f, table, p)
            generate_graphql(f, table, p)
            generate_ModelRestApi(f, table, p)
            generate_chart_view(f, table, p)

        f.write("""
def register_views():
""")
        for view in generated_views:
            class_name, view_type, table_name = view
            icon = f"get_view_icon('{table_name}', '{view_type}')"
            f.write(f"    appbuilder.add_view({class_name}, '{table_name}', icon={icon}, category='Generated Views')\n")

        f.write("""
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
""")

def generate_model_view(f, table, p):
    class_name = get_class_name(table.name, p)
    view_name = f"{class_name}ModelView"
    columns = [c.name for c in table.columns]
    f.write(f"""
class {view_name}(ModelView):
    datamodel = SQLAInterface({class_name})
    list_columns = {columns}
    show_columns = list_columns
    edit_columns = list_columns
    add_columns = list_columns
    list_widget = BeautifulListWidget
    edit_widget = BeautifulFormWidget
    add_widget = BeautifulFormWidget
    show_widget = BeautifulFormWidget

    # Enhanced search functionality
    search_columns = {columns}

    # Improved labels and descriptions
    label_columns = {{
        {', '.join([f"'{col}': '{col.replace('_', ' ').title()}'" for col in columns])}
    }}
    description_columns = {{
        {', '.join([f"'{col}': 'Enter the {col.replace('_', ' ')} here'" for col in columns])}
    }}

    # Custom formatters for better data presentation
    formatters_columns = {{
        'created_at': lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if x else '',
        'updated_at': lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if x else '',
    }}

    # Enhanced form field widgets
    add_form_extra_fields = {{
        {', '.join([generate_form_field(c) for c in table.columns])}
    }}

    @action("export", "Export", "Export the data?", "fa-rocket", multiple=False)
    def export(self, item):
        # Implement export logic here
        pass

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

""")
    generated_views.append((view_name, "ModelView", table.name))

def generate_master_detail_views(f, table, metadata, p):
    for fk in table.foreign_keys:
        parent_table = metadata.tables[fk.column.table.name]
        parent_class_name = get_class_name(parent_table.name, p)
        child_class_name = get_class_name(table.name, p)
        view_name = f"{parent_class_name}{child_class_name}MasterDetailView"
        f.write(f"""
class {view_name}(MasterDetailView):
    datamodel = SQLAInterface({parent_class_name})
    related_views = [{child_class_name}ModelView]
    list_widget = BeautifulListWidget
    edit_widget = BeautifulFormWidget
    show_widget = BeautifulFormWidget

""")
        generated_views.append((view_name, "MasterDetailView", f"{parent_table.name}_{table.name}"))

def generate_multiple_views(f, table, metadata, p):
    if len(table.foreign_keys) > 1:
        class_name = get_class_name(table.name, p)
        view_name = f"{class_name}MultipleView"
        related_views = [f"{get_class_name(fk.column.table.name, p)}ModelView" for fk in table.foreign_keys]
        f.write(f"""
class {view_name}(MultipleView):
    views = [{', '.join(related_views)}]

""")
        generated_views.append((view_name, "MultipleView", table.name))

def generate_wizard_view(f, table, p):
    class_name = get_class_name(table.name, p)
    view_name = f"{class_name}WizardView"
    columns = [c.name for c in table.columns]
    total_steps = math.ceil(len(columns) / 5)

    f.write(f"""
class {view_name}(WizardView):
    datamodel = SQLAInterface({class_name})
    total_steps = {total_steps}

    def __init__(self):
        super().__init__()
        self._init_steps()

""")

    for step in range(1, total_steps + 1):
        start_idx = (step - 1) * 5
        end_idx = min(step * 5, len(columns))
        step_columns = columns[start_idx:end_idx]

        f.write(f"""
    @expose('/step{step}', methods=['GET', 'POST'])
    def step{step}(self):
        form = DynamicForm()
""")
        for column in step_columns:
            f.write(f"        form.{column} = {generate_form_field(table.columns[columns.index(column)]).split(': ')[1]}\n")

        f.write(f"""
        if form.validate_on_submit():
            session['step{step}_data'] = form.data
            self.mark_step_complete({step})
            next_step = {step + 1 if step < total_steps else 1}
            return redirect(url_for(f'.step{{next_step}}'))

        form_data = session.get('step{step}_data', {{}})
        form = DynamicForm(**form_data)
        widget = BeautifulFormWidget()
        return self.render_wizard({step}, widget(form), 'Step {step}: {", ".join(step_columns)}')

""")

    f.write(f"""
    @expose('/submit', methods=['GET', 'POST'])
    def submit(self):
        if all(self.is_step_complete(step) for step in range(1, self.total_steps + 1)):
            # Combine data from all steps
            combined_data = {{}}
            for step in range(1, self.total_steps + 1):
                combined_data.update(session.get(f'step{{step}}_data', {{}}))

            # Create new record
            item = self.datamodel.obj()
            for key, value in combined_data.items():
                setattr(item, key, value)
            self.datamodel.add(item)

            # Clear session data
            for step in range(1, self.total_steps + 1):
                session.pop(f'step{{step}}_data', None)
                session.pop(f'{self.__class__.__name__}_step{{step}}_complete', None)

            flash('Form submitted successfully!', 'success')
            return redirect(url_for('.step1'))
        else:
            flash('Please complete all steps before submitting.', 'warning')
            return redirect(url_for('.step1'))

""")
    generated_views.append((view_name, "WizardView", table.name))

def generate_graphql(f, table, p):
    class_name = get_class_name(table.name, p)
    f.write(f"""
class {class_name}Object(SQLAlchemyObjectType):
    class Meta:
        model = {class_name}
        interfaces = (graphene.relay.Node, )

class {class_name}Connection(graphene.relay.Connection):
    class Meta:
        node = {class_name}Object

""")

    # Add to Query class
    f.write(f"""
class Query(graphene.ObjectType):
    node = graphene.relay.Node.Field()
    all_{table.name} = SQLAlchemyConnectionField({class_name}Connection)

""")

def generate_ModelRestApi(f, table, p):
    class_name = get_class_name(table.name, p)
    view_name = f"{class_name}RestApi"
    columns = [c.name for c in table.columns]
    f.write(f"""
class {view_name}(ModelRestApi):
    resource_name = '{table.name}'
    datamodel = SQLAInterface({class_name})
    allow_browser_login = True
    list_columns = {columns}
    show_columns = list_columns
    edit_columns = list_columns
    add_columns = list_columns

""")
    generated_views.append((view_name, "ModelRestApi", table.name))

def generate_chart_view(f, table, p):
    class_name = get_class_name(table.name, p)
    view_name = f"{class_name}ChartView"
    columns = [c.name for c in table.columns]
    f.write(f"""
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

""")
    generated_views.append((view_name, "ChartView", table.name))

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

if __name__ == "__main__":
    db_uri = "postgresql://username:password@localhost:5432/your_database"
    generate_views(db_uri)
    print("views.py has been generated successfully.")
