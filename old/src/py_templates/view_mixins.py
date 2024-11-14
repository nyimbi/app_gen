# view_mixins.py
import io
from flask_appbuilder import expose, AppBuilder
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_babel import lazy_gettext as _
from flask_appbuilder import action
from flask import render_template, flash, redirect, request, url_for, make_response
from flask_appbuilder.fieldwidgets import BS3TextFieldWidget
from flask_appbuilder.forms import DynamicForm
from wtforms import FormField, StringField
import pdfkit
import pandas as pd
# other necessary imports


hide_list = ['created_by', 'changed_by', 'created_on', 'changed_on']

"""
The SearchableModelViewMixin class defines a custom search view that uses the DocMixin search functionality. 
The _get_search_query method retrieves the search query from the request arguments, and the _get_search_widgets method 
creates a list of widgets for the search results.

The on_model_change method updates the search vector when a record is added or modified. 
This ensures that the search vector is always up-to-date.

To use the SearchableModelViewMixin in your application, simply import it and include it as a base class when defining your views:
# views.py

from flask_appbuilder import ModelView
from .models import MyDocument
from .view_mixins import SearchableModelViewMixin

class MyDocumentModelView(SearchableModelViewMixin, ModelView):
    datamodel = SQLAInterface(MyDocument)
    list_columns = ["id", "title", "content"]
    search_template = "search_template.html"

"""
class SearchableModelViewMixin(object):
    @expose("/search/", methods=["GET", "POST"])
    def search(self):
        """
        Custom search view that uses the DocMixin search functionality.
        """
        search_query = self.appbuilder.get_session.query(self.datamodel.obj).search
        query = self._get_search_query()
        results = search_query(self.appbuilder.get_session, query)

        widgets = self._get_search_widgets(results)
        return self.render_template(
            self.search_template,
            title=_("Search"),
            widgets=widgets,
            appbuilder=self.appbuilder,
        )

    def _get_search_query(self):
        return self.appbuilder.request.args.get("q", "")

    def _get_search_widgets(self, results):
        widgets = []

        for result in results:
            item_view = self.__class__(self.appbuilder, datamodel=SQLAInterface(type(result)))
            widgets.extend(item_view.show_widget(result.id, show_in_modal=True))

        return widgets

    def on_model_change(self, form, model, is_created):
        """
        Update the search vector when a record is added or modified.
        """
        model.search_vector = model.doc_title + " " + model.doc_text + " " + model.comments




class CustomActionsMixin(object):
    readonly = False  # Default to not read-only

    @action("print", "Print", "Print this page?", "fa-print", multiple=True)
    def action_print(self, items):
        if self.readonly:
            flash("Read-only mode is enabled.", "warning")
            return redirect(request.referrer)
        # Implement print functionality
        item_objects = [self.datamodel.get(item) for item in items]
        model_name = self.datamodel.obj.__class__.__name__  # Get the model name

        return render_template('print_template.html', items=item_objects, model_name=model_name)

    @action("export_pdf", "Export as PDF", "Export to PDF?", "fa-file-pdf-o", multiple=True)
    def action_export_pdf(self, items):
        if self.readonly:
            flash("Read-only mode is enabled.", "warning")
            return redirect(request.referrer)

        item_objects = [self.datamodel.get(item) for item in items]
        model_name = self.datamodel.obj.__class__.__name__  # Get the model name

        # Assuming all items have the same columns, get column names from the first item
        column_names = item_objects[0].__table__.columns.keys() if item_objects else []

        # Render a template with the item data
        rendered = render_template('pdf_template.html',
                                   items=item_objects,
                                   model_name=model_name,
                                   column_names=column_names)

        # Convert the rendered HTML to PDF
        pdf = pdfkit.from_string(rendered, False)

        # Create and send the response
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename={model_name}_export.pdf'

        return response


    @action("export_excel", "Export as Excel", "Export to Excel?", "fa-file-excel-o", multiple=True)
    def action_export_excel(self, items):
        if self.readonly:
            flash("Read-only mode is enabled.", "warning")
            return redirect(request.referrer)

        model_name = self.datamodel.obj.__class__.__name__  # Get the model name
        # Fetch the data for the items
        item_objects = [self.datamodel.get(item) for item in items]

        # Convert data to a Pandas DataFrame
        # Assuming all items have the same attributes
        if item_objects:
            data = [{col: getattr(item, col) for col in item.__table__.columns.keys()} for item in item_objects]
            df = pd.DataFrame(data)

            # Convert DataFrame to Excel
            excel_io = io.BytesIO()
            with pd.ExcelWriter(excel_io, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Sheet1')

            # Set up the response
            excel_io.seek(0)
            return Response (
                excel_io.read(),
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers={"Content-disposition":
                             f"attachment; filename={model_name}_export.xlsx"})
        else:
            flash("No items selected.", "warning")
            return redirect(request.referrer)

    @action("email_page", "Email Page", "Email this page?", "fa-envelope", multiple=True)
    def action_email_page(self, items):
        if self.readonly:
            flash("Read-only mode is enabled.", "warning")
            return redirect(request.referrer)
        # Implement email functionality

    @action("help", "Help", "Show help?", "fa-question-circle", multiple=False)
    def action_help(self, items):
        # Implement help functionality

    def is_action_allowed(self, name):
        if self.readonly and name in ['edit', 'delete', 'add']:
            return False
        return super(CustomActionsMixin, self).is_action_allowed(name)

