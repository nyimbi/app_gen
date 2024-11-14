from flask_appbuilder import ModelView, MasterDetailView, MultipleView
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.fields import AJAXSelectField, QuerySelectField
from flask_appbuilder.fieldwidgets import Select2AJAXWidget, Select2SlaveAJAXWidget
from flask_appbuilder.actions import action
from flask_appbuilder.security.decorators import has_access
from flask_appbuilder.forms import DynamicForm
from flask_appbuilder import AppBuilder, BaseView, expose, has_access
from flask_appbuilder.models.mixins import ImageColumn, FileColumn
from flask_appbuilder.api import ModelRestApi
from flask import g, flash, redirect, url_for
from flask_appbuilder.actions import action
from sqlalchemy.orm import session
from wtforms import StringField, BooleanField, IntegerField, DateField, DateTimeField, HiddenField, validators
from flask_appbuilder.models.sqla.filters import SearchWidget, FilterStartsWith
from flask_appbuilder.fieldwidgets import BS3TextFieldWidget, BS3PasswordFieldWidget, DatePickerWidget, DateTimePickerWidget, Select2Widget
from wtforms import StringField, BooleanField, DecimalField
from . import appbuilder, db
from .models import *


class BadgeView(ModelView):
    datamodel = SQLAInterface('Badge')
    list_title = 'Badge List'
    show_title = 'Badge Details'
    add_title = 'Add Badge'
    edit_title = 'Edit Badge'
    list_columns = ['id', 'name', 'description', 'criteria', 'icon']
    show_columns = ['id', 'name', 'description', 'criteria', 'icon']
    add_columns = ['name', 'description', 'criteria', 'icon']
    edit_columns = ['name', 'description', 'criteria', 'icon']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['name', 'description', 'criteria', 'icon']
    label_columns = {'id': 'Id', 'name': 'Name', 'description': 'Description', 'criteria': 'Criteria', 'icon': 'Icon'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'description', 'criteria', 'icon']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'description', 'criteria', 'icon']})
    ]
    

    add_fieldsets = [
        ('Add Badge', {'fields': ['name', 'description', 'criteria', 'icon']})
    ]
    

    edit_fieldsets = [
        ('Edit Badge', {'fields': ['name', 'description', 'criteria', 'icon']})
    ]
    
    validators_columns = {'name': '[validators.DataRequired(), validators.Length(max=50)]', 'description': '[validators.Length(max=200)]', 'criteria': '[validators.Length(max=200)]', 'icon': '[validators.Length(max=100)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]


    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'name': StringField('Name', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=50)]),
    'description': StringField('Description', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=200)]),
    'criteria': StringField('Criteria', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=200)]),
    'icon': StringField('Icon', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=100)]),
    # No relationship fields found
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.name
    

class ContactTypeView(ModelView):
    datamodel = SQLAInterface('ContactType')
    list_title = 'Contact Type List'
    show_title = 'Contact Type Details'
    add_title = 'Add Contact Type'
    edit_title = 'Edit Contact Type'
    list_columns = ['id', 'name', 'description', 'is_digital', 'requires_verification', 'max_length', 'icon_url', 'created_at', 'updated_at']
    show_columns = ['id', 'name', 'description', 'is_digital', 'requires_verification', 'max_length', 'icon_url', 'created_at', 'updated_at']
    add_columns = ['name', 'description', 'is_digital', 'requires_verification', 'max_length', 'icon_url']
    edit_columns = ['name', 'description', 'is_digital', 'requires_verification', 'max_length', 'icon_url']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['name', 'description', 'icon_url']
    label_columns = {'id': 'Id', 'name': 'Name', 'description': 'Description', 'is_digital': 'Is Digital', 'requires_verification': 'Requires Verification', 'max_length': 'Max Length', 'icon_url': 'Icon Url', 'created_at': 'Created At', 'updated_at': 'Updated At'}
    description_columns = {'id': 'Unique identifier for the address type.', 'name': 'Name or type of contact method, e.g., Mobile, Email, WhatsApp.', 'description': 'Brief description about the address type, providing context or usage scenarios.', 'is_digital': 'Indicates if the contact method is digital or physical.', 'requires_verification': 'Indicates if the address type typically requires a verification process, e.g., email confirmation.', 'max_length': 'If applicable, the maximum character length of a value of this address type. Useful for validation.', 'icon_url': 'URL or link to an icon or image representing this address type. Useful for UI/UX purposes.', 'created_at': 'Timestamp when the address type was added to the system.', 'updated_at': 'Timestamp when the address type was last updated.'}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'description', 'is_digital', 'requires_verification', 'max_length', 'icon_url', 'created_at', 'updated_at']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'description', 'is_digital', 'requires_verification', 'max_length', 'icon_url', 'created_at', 'updated_at']})
    ]
    

    add_fieldsets = [
        ('Add Contact Type', {'fields': ['name', 'description', 'is_digital', 'requires_verification', 'max_length', 'icon_url', 'created_at', 'updated_at']})
    ]
    

    edit_fieldsets = [
        ('Edit Contact Type', {'fields': ['name', 'description', 'is_digital', 'requires_verification', 'max_length', 'icon_url', 'created_at', 'updated_at']})
    ]
    
    validators_columns = {'name': '[validators.DataRequired(), validators.Length(max=50)]', 'icon_url': '[validators.Length(max=255)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]


    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'name': StringField('Name', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=50)]),
    'description': StringField('Description', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'is_digital' : BooleanField('Is_digital'),
    'requires_verification' : BooleanField('Requires_verification'),
    'max_length' : IntegerField('Max_length', validators=[validators.DataRequired()]),
    'icon_url': StringField('Icon_url', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=255)]),
    # No relationship fields found
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.name
    

class CountryView(ModelView):
    datamodel = SQLAInterface('Country')
    list_title = 'Country List'
    add_title = 'Add Country'
    edit_title = 'Edit Country'
    list_columns = ['id', 'iso_alpha2', 'iso_alpha3', 'iso_numeric', 'fips_code', 'name', 'capital', 'areainsqkm', 'population', 'continent', 'tld', 'currencycode', 'currencyname', 'phone', 'postalcode', 'postalcoderegex', 'languages', 'neighbors', 'equivfipscode', 'flag']
    show_columns = ['id', 'iso_alpha2', 'iso_alpha3', 'iso_numeric', 'fips_code', 'name', 'capital', 'areainsqkm', 'population', 'continent', 'tld', 'currencycode', 'currencyname', 'phone', 'postalcode', 'postalcoderegex', 'languages', 'neighbors', 'equivfipscode', 'flag']
    search_columns = ['iso_alpha2', 'iso_alpha3', 'fips_code', 'name', 'capital', 'continent', 'tld', 'currencycode', 'currencyname', 'phone', 'postalcode', 'postalcoderegex', 'languages', 'neighbors', 'equivfipscode', 'flag']
    label_columns = {'id': 'Id', 'iso_alpha2': 'Iso Alpha2', 'iso_alpha3': 'Iso Alpha3', 'iso_numeric': 'Iso Numeric', 'fips_code': 'Fips Code', 'name': 'Name', 'capital': 'Capital', 'areainsqkm': 'Areainsqkm', 'population': 'Population', 'continent': 'Continent', 'tld': 'Tld', 'currencycode': 'Currencycode', 'currencyname': 'Currencyname', 'phone': 'Phone', 'postalcode': 'Postalcode', 'postalcoderegex': 'Postalcoderegex', 'languages': 'Languages', 'neighbors': 'Neighbors', 'equivfipscode': 'Equivfipscode', 'flag': 'Flag'}
    description_columns = {'iso_alpha2': '2-letter ISO 3166-1 alpha code e.g., US for the United States', 'iso_alpha3': '3-letter ISO 3166-1 alpha code e.g., USA for the United States', 'iso_numeric': 'ISO 3166-1 numeric code e.g., 840 for the United States', 'fips_code': 'Federal Information Processing Standard code, used by the US government', 'name': 'Full name of the country', 'capital': 'Capital city of the country', 'areainsqkm': 'Total area of the country in square kilometers', 'population': 'Estimated population of the country', 'continent': 'Abbreviation of the continent the country is located in', 'tld': 'Top Level Domain for the country e.g., .us for the United States', 'currencycode': 'ISO code of the country’s currency e.g., USD for US Dollar', 'currencyname': 'Full name of the country’s currency e.g., Dollar for US Dollar', 'phone': 'Country dialing code e.g., +1 for the United States', 'postalcode': 'Template or format of postal codes in the country', 'postalcoderegex': 'Regular expression pattern to validate postal codes', 'languages': 'Commonly spoken languages in the country, represented as ISO codes', 'neighbors': 'Neighboring countries, usually represented as ISO codes', 'equivfipscode': 'Equivalent FIPS code in cases where it might differ from the primary FIPS code', 'flag': 'Field to store a link or representation of the country’s flag'}

    class AddForm(DynamicForm):
        step = HiddenField('step')

    add_form = AddForm

    def add_form_get(self, form):
        form.step.data = session.get('form_step', 1)
        return form

    def add_form_post(self, form):
        if form.step.data:
            session['form_step'] = int(form.step.data)
        return form

    def form_get(self, form):
        form = super().form_get(form)
        step = int(session.get('form_step', 1))
        start = (step - 1) * 5
        end = step * 5
        visible_fields = ['iso_alpha2', 'iso_alpha3', 'iso_numeric', 'fips_code', 'name', 'capital', 'areainsqkm', 'population', 'continent', 'tld', 'currencycode', 'currencyname', 'phone', 'postalcode', 'postalcoderegex', 'languages', 'neighbors', 'equivfipscode', 'flag'][start:end]
        for field in form._fields:
            if field not in visible_fields and field != 'step':
                form._fields[field].render_kw = {'style': 'display:none;'}
        return form

    def form_post(self, form):
        step = int(form.step.data)
        if step < 4:
            session['form_step'] = step + 1
            return self.update_redirect(), False  # Keep user on the same form
        else:
            session.pop('form_step', None)
            return super().form_post(form)

    add_fieldsets = [    ('Step 1', {'fields': ['step'] + ['iso_alpha2', 'iso_alpha3', 'iso_numeric', 'fips_code', 'name'], 'expanded': True}),     ('Step 2', {'fields': ['step'] + ['capital', 'areainsqkm', 'population', 'continent', 'tld'], 'expanded': True}),     ('Step 3', {'fields': ['step'] + ['currencycode', 'currencyname', 'phone', 'postalcode', 'postalcoderegex'], 'expanded': True}),     ('Step 4', {'fields': ['step'] + ['languages', 'neighbors', 'equivfipscode', 'flag'], 'expanded': True})]
    edit_fieldsets = add_fieldsets


    def __repr__(self):
        return self.name
    

class CurrencyView(ModelView):
    datamodel = SQLAInterface('Currency')
    list_title = 'Currency List'
    show_title = 'Currency Details'
    add_title = 'Add Currency'
    edit_title = 'Edit Currency'
    list_columns = ['id', 'name', 'symbol', 'numeric_code', 'full_name']
    show_columns = ['id', 'name', 'symbol', 'numeric_code', 'full_name']
    add_columns = ['name', 'symbol', 'numeric_code', 'full_name']
    edit_columns = ['name', 'symbol', 'numeric_code', 'full_name']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['name', 'symbol', 'numeric_code', 'full_name']
    label_columns = {'id': 'Id', 'name': 'Name', 'symbol': 'Symbol', 'numeric_code': 'Numeric Code', 'full_name': 'Full Name'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'symbol', 'numeric_code', 'full_name']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'symbol', 'numeric_code', 'full_name']})
    ]
    

    add_fieldsets = [
        ('Add Currency', {'fields': ['name', 'symbol', 'numeric_code', 'full_name']})
    ]
    

    edit_fieldsets = [
        ('Edit Currency', {'fields': ['name', 'symbol', 'numeric_code', 'full_name']})
    ]
    
    validators_columns = {'name': '[validators.Length(max=4)]', 'symbol': '[validators.Length(max=5)]', 'numeric_code': '[validators.Length(max=4)]', 'full_name': '[validators.Length(max=100)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]


    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'name': StringField('Name', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=4)]),
    'symbol': StringField('Symbol', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=5)]),
    'numeric_code': StringField('Numeric_code', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=4)]),
    'full_name': StringField('Full_name', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=100)]),
    # No relationship fields found
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.name
    

class LanguagecodesView(ModelView):
    datamodel = SQLAInterface('Languagecodes')
    list_title = 'Languagecodes List'
    show_title = 'Languagecodes Details'
    add_title = 'Add Languagecodes'
    edit_title = 'Edit Languagecodes'
    list_columns = ['id', 'iso_639_3', 'iso_639_2', 'iso_639_1', 'name']
    show_columns = ['id', 'iso_639_3', 'iso_639_2', 'iso_639_1', 'name']
    add_columns = ['iso_639_3', 'iso_639_2', 'iso_639_1', 'name']
    edit_columns = ['iso_639_3', 'iso_639_2', 'iso_639_1', 'name']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['iso_639_3', 'iso_639_2', 'iso_639_1', 'name']
    label_columns = {'id': 'Id', 'iso_639_3': 'Iso 639 3', 'iso_639_2': 'Iso 639 2', 'iso_639_1': 'Iso 639 1', 'name': 'Name'}
    description_columns = {'iso_639_3': 'ISO 639-3 code is a three-letter code that represents a specific language uniquely. It offers a comprehensive set of languages.', 'iso_639_2': 'ISO 639-2 code is a three-letter code, which could be either bibliographic or terminological, representing a set of similar languages.', 'iso_639_1': 'ISO 639-1 code is a two-letter code. It represents major languages but is not as exhaustive as ISO 639-3.', 'name': 'The descriptive name of the language in English.'}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'iso_639_3', 'iso_639_2', 'iso_639_1', 'name']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'iso_639_3', 'iso_639_2', 'iso_639_1', 'name']})
    ]
    

    add_fieldsets = [
        ('Add Languagecodes', {'fields': ['iso_639_3', 'iso_639_2', 'iso_639_1', 'name']})
    ]
    

    edit_fieldsets = [
        ('Edit Languagecodes', {'fields': ['iso_639_3', 'iso_639_2', 'iso_639_1', 'name']})
    ]
    
    validators_columns = {'iso_639_3': '[validators.Length(max=10)]', 'iso_639_2': '[validators.Length(max=10)]', 'iso_639_1': '[validators.Length(max=10)]', 'name': '[validators.Length(max=1000)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]


    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'iso_639_3': StringField('Iso_639_3', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=10)]),
    'iso_639_2': StringField('Iso_639_2', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=10)]),
    'iso_639_1': StringField('Iso_639_1', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=10)]),
    'name': StringField('Name', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=1000)]),
    # No relationship fields found
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.name
    

class PersonView(ModelView):
    datamodel = SQLAInterface('Person')
    list_title = 'Person List'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    list_columns = ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']
    show_columns = ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']
    search_columns = ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests']
    label_columns = {'id': 'Id', 'first_name': 'First Name', 'middle_name': 'Middle Name', 'last_name': 'Last Name', 'full_name': 'Full Name', 'nick_name': 'Nick Name', 'headline': 'Headline', 'location': 'Location', 'summary': 'Summary', 'email': 'Email', 'phone': 'Phone', 'date_of_birth': 'Date Of Birth', 'city': 'City', 'state_province': 'State Province', 'postal_code': 'Postal Code', 'country': 'Country', 'bio': 'Bio', 'skills_description': 'Skills Description', 'interests': 'Interests', 'is_volunteer': 'Is Volunteer', 'is_staff': 'Is Staff', 'onboarding_step': 'Onboarding Step', 'profile_completion': 'Profile Completion', 'last_profile_update': 'Last Profile Update', 'points': 'Points', 'level': 'Level', 'social_media_imported': 'Social Media Imported'}
    description_columns = {}

    class AddForm(DynamicForm):
        step = HiddenField('step')

    add_form = AddForm

    def add_form_get(self, form):
        form.step.data = session.get('form_step', 1)
        return form

    def add_form_post(self, form):
        if form.step.data:
            session['form_step'] = int(form.step.data)
        return form

    def form_get(self, form):
        form = super().form_get(form)
        step = int(session.get('form_step', 1))
        start = (step - 1) * 5
        end = step * 5
        visible_fields = ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported'][start:end]
        for field in form._fields:
            if field not in visible_fields and field != 'step':
                form._fields[field].render_kw = {'style': 'display:none;'}
        return form

    def form_post(self, form):
        step = int(form.step.data)
        if step < 6:
            session['form_step'] = step + 1
            return self.update_redirect(), False  # Keep user on the same form
        else:
            session.pop('form_step', None)
            return super().form_post(form)

    add_fieldsets = [    ('Step 1', {'fields': ['step'] + ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name'], 'expanded': True}),     ('Step 2', {'fields': ['step'] + ['headline', 'location', 'summary', 'email', 'phone'], 'expanded': True}),     ('Step 3', {'fields': ['step'] + ['date_of_birth', 'city', 'state_province', 'postal_code', 'country'], 'expanded': True}),     ('Step 4', {'fields': ['step'] + ['bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff'], 'expanded': True}),     ('Step 5', {'fields': ['step'] + ['onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level'], 'expanded': True}),     ('Step 6', {'fields': ['step'] + ['social_media_imported'], 'expanded': True})]
    edit_fieldsets = add_fieldsets


    def __repr__(self):
        return self.id
    

class SkillCategoryView(ModelView):
    datamodel = SQLAInterface('SkillCategory')
    list_title = 'Skill Category List'
    show_title = 'Skill Category Details'
    add_title = 'Add Skill Category'
    edit_title = 'Edit Skill Category'
    list_columns = ['id', 'name', 'description']
    show_columns = ['id', 'name', 'description']
    add_columns = ['name', 'description']
    edit_columns = ['name', 'description']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['name', 'description']
    label_columns = {'id': 'Id', 'name': 'Name', 'description': 'Description'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'description']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'description']})
    ]
    

    add_fieldsets = [
        ('Add Skill Category', {'fields': ['name', 'description']})
    ]
    

    edit_fieldsets = [
        ('Edit Skill Category', {'fields': ['name', 'description']})
    ]
    
    validators_columns = {'name': '[validators.DataRequired(), validators.Length(max=100)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]


    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'name': StringField('Name', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=100)]),
    'description': StringField('Description', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    # No relationship fields found
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.name
    

class TagView(ModelView):
    datamodel = SQLAInterface('Tag')
    list_title = 'Tag List'
    show_title = 'Tag Details'
    add_title = 'Add Tag'
    edit_title = 'Edit Tag'
    list_columns = ['id', 'name']
    show_columns = ['id', 'name']
    add_columns = ['name']
    edit_columns = ['name']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['name']
    label_columns = {'id': 'Id', 'name': 'Name'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name']})
    ]
    

    add_fieldsets = [
        ('Add Tag', {'fields': ['name']})
    ]
    

    edit_fieldsets = [
        ('Edit Tag', {'fields': ['name']})
    ]
    
    validators_columns = {'name': '[validators.DataRequired(), validators.Length(max=50)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]


    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'name': StringField('Name', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=50)]),
    # No relationship fields found
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.name
    

class ContactView(ModelView):
    datamodel = SQLAInterface('Contact')
    list_title = 'Contact List'
    add_title = 'Add Contact'
    edit_title = 'Edit Contact'
    list_columns = ['id', 'person_id_fk', 'contact_type_id_fk', 'contact_value', 'priority', 'best_time_to_contact_start', 'best_time_to_contact_end', 'active_from_date', 'active_to_date', 'for_business_use', 'for_personal_use', 'do_not_use', 'is_active', 'is_blocked', 'is_verified', 'notes']
    show_columns = ['id', 'person_id_fk', 'contact_type_id_fk', 'contact_value', 'priority', 'best_time_to_contact_start', 'best_time_to_contact_end', 'active_from_date', 'active_to_date', 'for_business_use', 'for_personal_use', 'do_not_use', 'is_active', 'is_blocked', 'is_verified', 'notes']
    search_columns = ['contact_value', 'notes']
    label_columns = {'id': 'Id', 'person_id_fk': 'Person Id Fk', 'contact_type_id_fk': 'Contact Type Id Fk', 'contact_value': 'Contact Value', 'priority': 'Priority', 'best_time_to_contact_start': 'Best Time To Contact Start', 'best_time_to_contact_end': 'Best Time To Contact End', 'active_from_date': 'Active From Date', 'active_to_date': 'Active To Date', 'for_business_use': 'For Business Use', 'for_personal_use': 'For Personal Use', 'do_not_use': 'Do Not Use', 'is_active': 'Is Active', 'is_blocked': 'Is Blocked', 'is_verified': 'Is Verified', 'notes': 'Notes'}
    description_columns = {'id': 'Unique identifier for the contact.', 'person_id_fk': 'Reference to the individual associated with this contact.', 'contact_type_id_fk': 'Reference to the type of contact.', 'contact_value': 'Actual contact value, e.g., phone number or email address.', 'priority': 'Ordering priority for displaying or using the contact. Lower value indicates higher priority.', 'best_time_to_contact_start': 'Preferred start time when the individual/organization is available for contact.', 'best_time_to_contact_end': 'Preferred end time for availability.', 'active_from_date': 'Date when this contact became active or relevant.', 'active_to_date': 'Date when this contact ceases to be active or relevant.', 'for_business_use': 'Indicates if the contact is primarily for business purposes.', 'for_personal_use': 'Indicates if the contact is primarily for personal use.', 'do_not_use': 'Indicates if there are any restrictions or requests not to use this contact.', 'is_active': 'Indicates if this contact is currently active and usable.', 'is_blocked': 'Indicates if this contact is blocked, maybe due to spam or other reasons.', 'is_verified': 'Indicates if this contact has been verified, e.g., via OTP or email confirmation.', 'notes': 'Additional notes or context about the contact.'}

    class AddForm(DynamicForm):
        step = HiddenField('step')

    add_form = AddForm

    def add_form_get(self, form):
        form.step.data = session.get('form_step', 1)
        return form

    def add_form_post(self, form):
        if form.step.data:
            session['form_step'] = int(form.step.data)
        return form

    def form_get(self, form):
        form = super().form_get(form)
        step = int(session.get('form_step', 1))
        start = (step - 1) * 5
        end = step * 5
        visible_fields = ['person_id_fk', 'contact_type_id_fk', 'contact_value', 'priority', 'best_time_to_contact_start', 'best_time_to_contact_end', 'active_from_date', 'active_to_date', 'for_business_use', 'for_personal_use', 'do_not_use', 'is_active', 'is_blocked', 'is_verified', 'notes'][start:end]
        for field in form._fields:
            if field not in visible_fields and field != 'step':
                form._fields[field].render_kw = {'style': 'display:none;'}
        return form

    def form_post(self, form):
        step = int(form.step.data)
        if step < 3:
            session['form_step'] = step + 1
            return self.update_redirect(), False  # Keep user on the same form
        else:
            session.pop('form_step', None)
            return super().form_post(form)

    add_fieldsets = [    ('Step 1', {'fields': ['step'] + ['person_id_fk', 'contact_type_id_fk', 'contact_value', 'priority', 'best_time_to_contact_start'], 'expanded': True}),     ('Step 2', {'fields': ['step'] + ['best_time_to_contact_end', 'active_from_date', 'active_to_date', 'for_business_use', 'for_personal_use'], 'expanded': True}),     ('Step 3', {'fields': ['step'] + ['do_not_use', 'is_active', 'is_blocked', 'is_verified', 'notes'], 'expanded': True})]
    edit_fieldsets = add_fieldsets


    def __repr__(self):
        return self.id
    

class GamificationChallengeView(ModelView):
    datamodel = SQLAInterface('GamificationChallenge')
    list_title = 'Gamification Challenge List'
    show_title = 'Gamification Challenge Details'
    add_title = 'Add Gamification Challenge'
    edit_title = 'Edit Gamification Challenge'
    list_columns = ['id', 'name', 'description', 'points_reward', 'badge_reward_id_fk', 'start_date', 'end_date']
    show_columns = ['id', 'name', 'description', 'points_reward', 'badge_reward_id_fk', 'start_date', 'end_date']
    add_columns = ['name', 'description', 'points_reward', 'badge_reward_id_fk', 'start_date', 'end_date']
    edit_columns = ['name', 'description', 'points_reward', 'badge_reward_id_fk', 'start_date', 'end_date']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['name', 'description']
    label_columns = {'id': 'Id', 'name': 'Name', 'description': 'Description', 'points_reward': 'Points Reward', 'badge_reward_id_fk': 'Badge Reward Id Fk', 'start_date': 'Start Date', 'end_date': 'End Date'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'description', 'points_reward', 'badge_reward_id_fk', 'start_date', 'end_date']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'description', 'points_reward', 'badge_reward_id_fk', 'start_date', 'end_date']})
    ]
    

    add_fieldsets = [
        ('Add Gamification Challenge', {'fields': ['name', 'description', 'points_reward', 'badge_reward_id_fk', 'start_date', 'end_date']})
    ]
    

    edit_fieldsets = [
        ('Edit Gamification Challenge', {'fields': ['name', 'description', 'points_reward', 'badge_reward_id_fk', 'start_date', 'end_date']})
    ]
    
    validators_columns = {'name': '[validators.DataRequired(), validators.Length(max=100)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'badge_reward_id_fk': 'db.session.query(Badge)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'name': StringField('Name', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=100)]),
    'description': StringField('Description', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'points_reward' : IntegerField('Points_reward', validators=[validators.DataRequired()]),
    'badge_reward_id_fk' : IntegerField('Badge_reward_id_fk', validators=[validators.DataRequired()]),
    'start_date' : DateTimeField('Start_date', widget=DateTimePickerWidget(), validators=[validators.DataRequired()]),
    'end_date' : DateTimeField('End_date', widget=DateTimePickerWidget(), validators=[validators.DataRequired()]),
    'badge_reward_fk': QuerySelectField('Badge_reward_fk', query_factory=lambda: db.session.query(Badge), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.name
    

class LeaderboardView(ModelView):
    datamodel = SQLAInterface('Leaderboard')
    list_title = 'Leaderboard List'
    show_title = 'Leaderboard Details'
    add_title = 'Add Leaderboard'
    edit_title = 'Edit Leaderboard'
    list_columns = ['id', 'person_id_fk', 'score', 'last_updated']
    show_columns = ['id', 'person_id_fk', 'score', 'last_updated']
    add_columns = ['person_id_fk', 'score', 'last_updated']
    edit_columns = ['person_id_fk', 'score', 'last_updated']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = []
    label_columns = {'id': 'Id', 'person_id_fk': 'Person Id Fk', 'score': 'Score', 'last_updated': 'Last Updated'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'score', 'last_updated']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'score', 'last_updated']})
    ]
    

    add_fieldsets = [
        ('Add Leaderboard', {'fields': ['person_id_fk', 'score', 'last_updated']})
    ]
    

    edit_fieldsets = [
        ('Edit Leaderboard', {'fields': ['person_id_fk', 'score', 'last_updated']})
    ]
    
    validators_columns = {'person_id_fk': '[validators.DataRequired()]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'person_id_fk': 'db.session.query(Person)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'person_id_fk' : IntegerField('Person_id_fk', validators=[validators.DataRequired()]),
    'score' : IntegerField('Score', validators=[validators.DataRequired()]),
    'last_updated' : DateTimeField('Last_updated', widget=DateTimePickerWidget(), validators=[validators.DataRequired()]),
    'person_fk': QuerySelectField('Person_fk', query_factory=lambda: db.session.query(Person), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class MessageView(ModelView):
    datamodel = SQLAInterface('Message')
    list_title = 'Message List'
    show_title = 'Message Details'
    add_title = 'Add Message'
    edit_title = 'Edit Message'
    list_columns = ['id', 'sender_id_fk', 'recipient_id_fk', 'subject', 'body', 'sent_date', 'read_date']
    show_columns = ['id', 'sender_id_fk', 'recipient_id_fk', 'subject', 'body', 'sent_date', 'read_date']
    add_columns = ['sender_id_fk', 'recipient_id_fk', 'subject', 'body', 'sent_date', 'read_date']
    edit_columns = ['sender_id_fk', 'recipient_id_fk', 'subject', 'body', 'sent_date', 'read_date']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['subject', 'body']
    label_columns = {'id': 'Id', 'sender_id_fk': 'Sender Id Fk', 'recipient_id_fk': 'Recipient Id Fk', 'subject': 'Subject', 'body': 'Body', 'sent_date': 'Sent Date', 'read_date': 'Read Date'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'sender_id_fk', 'recipient_id_fk', 'subject', 'body', 'sent_date', 'read_date']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'sender_id_fk', 'recipient_id_fk', 'subject', 'body', 'sent_date', 'read_date']})
    ]
    

    add_fieldsets = [
        ('Add Message', {'fields': ['sender_id_fk', 'recipient_id_fk', 'subject', 'body', 'sent_date', 'read_date']})
    ]
    

    edit_fieldsets = [
        ('Edit Message', {'fields': ['sender_id_fk', 'recipient_id_fk', 'subject', 'body', 'sent_date', 'read_date']})
    ]
    
    validators_columns = {'sender_id_fk': '[validators.DataRequired()]', 'recipient_id_fk': '[validators.DataRequired()]', 'subject': '[validators.Length(max=200)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'recipient_id_fk': 'db.session.query(Person)', 'sender_id_fk': 'db.session.query(Person)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'sender_id_fk' : IntegerField('Sender_id_fk', validators=[validators.DataRequired()]),
    'recipient_id_fk' : IntegerField('Recipient_id_fk', validators=[validators.DataRequired()]),
    'subject': StringField('Subject', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=200)]),
    'body': StringField('Body', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'sent_date' : DateTimeField('Sent_date', widget=DateTimePickerWidget(), validators=[validators.DataRequired()]),
    'read_date' : DateTimeField('Read_date', widget=DateTimePickerWidget(), validators=[validators.DataRequired()]),
    'recipient_fk': QuerySelectField('Recipient_fk', query_factory=lambda: db.session.query(Person), widget=Select2Widget(), allow_blank=True),
    'sender_fk': QuerySelectField('Sender_fk', query_factory=lambda: db.session.query(Person), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class NotificationView(ModelView):
    datamodel = SQLAInterface('Notification')
    list_title = 'Notification List'
    show_title = 'Notification Details'
    add_title = 'Add Notification'
    edit_title = 'Edit Notification'
    list_columns = ['id', 'person_id_fk', 'message', 'notification_type', 'created_date', 'read_date']
    show_columns = ['id', 'person_id_fk', 'message', 'notification_type', 'created_date', 'read_date']
    add_columns = ['person_id_fk', 'message', 'notification_type', 'created_date', 'read_date']
    edit_columns = ['person_id_fk', 'message', 'notification_type', 'created_date', 'read_date']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['message', 'notification_type']
    label_columns = {'id': 'Id', 'person_id_fk': 'Person Id Fk', 'message': 'Message', 'notification_type': 'Notification Type', 'created_date': 'Created Date', 'read_date': 'Read Date'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'message', 'notification_type', 'created_date', 'read_date']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'message', 'notification_type', 'created_date', 'read_date']})
    ]
    

    add_fieldsets = [
        ('Add Notification', {'fields': ['person_id_fk', 'message', 'notification_type', 'created_date', 'read_date']})
    ]
    

    edit_fieldsets = [
        ('Edit Notification', {'fields': ['person_id_fk', 'message', 'notification_type', 'created_date', 'read_date']})
    ]
    
    validators_columns = {'person_id_fk': '[validators.DataRequired()]', 'notification_type': '[validators.Length(max=50)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'person_id_fk': 'db.session.query(Person)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'person_id_fk' : IntegerField('Person_id_fk', validators=[validators.DataRequired()]),
    'message': StringField('Message', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'notification_type': StringField('Notification_type', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=50)]),
    'created_date' : DateTimeField('Created_date', widget=DateTimePickerWidget(), validators=[validators.DataRequired()]),
    'read_date' : DateTimeField('Read_date', widget=DateTimePickerWidget(), validators=[validators.DataRequired()]),
    'person_fk': QuerySelectField('Person_fk', query_factory=lambda: db.session.query(Person), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class OrganizationView(ModelView):
    datamodel = SQLAInterface('Organization')
    list_title = 'Organization List'
    add_title = 'Add Organization'
    edit_title = 'Edit Organization'
    list_columns = ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']
    show_columns = ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']
    search_columns = ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'description', 'mission_statement', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'legal_structure', 'compliance_status', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations']
    label_columns = {'id': 'Id', 'name': 'Name', 'legal_name': 'Legal Name', 'org_type': 'Org Type', 'org_cat': 'Org Cat', 'status': 'Status', 'industry': 'Industry', 'website': 'Website', 'is_verified': 'Is Verified', 'description': 'Description', 'mission_statement': 'Mission Statement', 'size': 'Size', 'revenue': 'Revenue', 'founded_date': 'Founded Date', 'country_of_operation_id_fk': 'Country Of Operation Id Fk', 'logo': 'Logo', 'social_media_links': 'Social Media Links', 'tax_id': 'Tax Id', 'registration_number': 'Registration Number', 'seeking_funding': 'Seeking Funding', 'providing_funding': 'Providing Funding', 'authorized_representative': 'Authorized Representative', 'legal_structure': 'Legal Structure', 'compliance_status': 'Compliance Status', 'financial_year_end': 'Financial Year End', 'last_audit_date': 'Last Audit Date', 'auditor_name': 'Auditor Name', 'phone_number': 'Phone Number', 'email': 'Email', 'address': 'Address', 'city': 'City', 'state': 'State', 'country': 'Country', 'postal_code': 'Postal Code', 'board_members': 'Board Members', 'governance_structure': 'Governance Structure', 'risk_assessment': 'Risk Assessment', 'insurance_coverage': 'Insurance Coverage', 'compliance_certifications': 'Compliance Certifications', 'ethics_policy': 'Ethics Policy', 'sustainability_policy': 'Sustainability Policy', 'primary_funding_source': 'Primary Funding Source', 'secondary_funding_source': 'Secondary Funding Source', 'main_areas_of_operation': 'Main Areas Of Operation', 'key_programs': 'Key Programs', 'beneficiary_info': 'Beneficiary Info', 'major_donors': 'Major Donors', 'partnerships_affiliations': 'Partnerships Affiliations', 'onboarding_step': 'Onboarding Step', 'profile_completion': 'Profile Completion', 'last_profile_update': 'Last Profile Update', 'associated_people_id_fk': 'Associated People Id Fk'}
    description_columns = {}

    class AddForm(DynamicForm):
        step = HiddenField('step')

    add_form = AddForm

    def add_form_get(self, form):
        form.step.data = session.get('form_step', 1)
        return form

    def add_form_post(self, form):
        if form.step.data:
            session['form_step'] = int(form.step.data)
        return form

    def form_get(self, form):
        form = super().form_get(form)
        step = int(session.get('form_step', 1))
        start = (step - 1) * 5
        end = step * 5
        visible_fields = ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk'][start:end]
        for field in form._fields:
            if field not in visible_fields and field != 'step':
                form._fields[field].render_kw = {'style': 'display:none;'}
        return form

    def form_post(self, form):
        step = int(form.step.data)
        if step < 11:
            session['form_step'] = step + 1
            return self.update_redirect(), False  # Keep user on the same form
        else:
            session.pop('form_step', None)
            return super().form_post(form)

    add_fieldsets = [    ('Step 1', {'fields': ['step'] + ['name', 'legal_name', 'org_type', 'org_cat', 'status'], 'expanded': True}),     ('Step 2', {'fields': ['step'] + ['industry', 'website', 'is_verified', 'description', 'mission_statement'], 'expanded': True}),     ('Step 3', {'fields': ['step'] + ['size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo'], 'expanded': True}),     ('Step 4', {'fields': ['step'] + ['social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding'], 'expanded': True}),     ('Step 5', {'fields': ['step'] + ['authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date'], 'expanded': True}),     ('Step 6', {'fields': ['step'] + ['auditor_name', 'phone_number', 'email', 'address', 'city'], 'expanded': True}),     ('Step 7', {'fields': ['step'] + ['state', 'country', 'postal_code', 'board_members', 'governance_structure'], 'expanded': True}),     ('Step 8', {'fields': ['step'] + ['risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy'], 'expanded': True}),     ('Step 9', {'fields': ['step'] + ['primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info'], 'expanded': True}),     ('Step 10', {'fields': ['step'] + ['major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update'], 'expanded': True}),     ('Step 11', {'fields': ['step'] + ['associated_people_id_fk'], 'expanded': True})]
    edit_fieldsets = add_fieldsets


    def __repr__(self):
        return self.name
    

class PersonBadgeView(ModelView):
    datamodel = SQLAInterface('PersonBadge')
    list_title = 'Person Badge List'
    show_title = 'Person Badge Details'
    add_title = 'Add Person Badge'
    edit_title = 'Edit Person Badge'
    list_columns = ['person_id_fk', 'badge_id_fk', 'date_earned']
    show_columns = ['person_id_fk', 'badge_id_fk', 'date_earned']
    add_columns = ['person_id_fk', 'badge_id_fk', 'date_earned']
    edit_columns = ['person_id_fk', 'badge_id_fk', 'date_earned']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = []
    label_columns = {'person_id_fk': 'Person Id Fk', 'badge_id_fk': 'Badge Id Fk', 'date_earned': 'Date Earned'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['person_id_fk', 'badge_id_fk', 'date_earned']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['person_id_fk', 'badge_id_fk', 'date_earned']})
    ]
    

    add_fieldsets = [
        ('Add Person Badge', {'fields': ['person_id_fk', 'badge_id_fk', 'date_earned']})
    ]
    

    edit_fieldsets = [
        ('Edit Person Badge', {'fields': ['person_id_fk', 'badge_id_fk', 'date_earned']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'person_id_fk': 'db.session.query(Person)', 'badge_id_fk': 'db.session.query(Badge)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'person_id_fk' : IntegerField('Person_id_fk', validators=[validators.DataRequired()]),
    'badge_id_fk' : IntegerField('Badge_id_fk', validators=[validators.DataRequired()]),
    'date_earned' : DateTimeField('Date_earned', widget=DateTimePickerWidget(), validators=[validators.DataRequired()]),
    'person_fk': QuerySelectField('Person_fk', query_factory=lambda: db.session.query(Person), widget=Select2Widget(), allow_blank=True),
    'badge_fk': QuerySelectField('Badge_fk', query_factory=lambda: db.session.query(Badge), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.person_id_fk
    

class PersonCertificationView(ModelView):
    datamodel = SQLAInterface('PersonCertification')
    list_title = 'Person Certification List'
    show_title = 'Person Certification Details'
    add_title = 'Add Person Certification'
    edit_title = 'Edit Person Certification'
    list_columns = ['id', 'person_id_fk', 'name', 'issuing_organization', 'issue_date', 'expiration_date', 'credential_id', 'credential_url']
    show_columns = ['id', 'person_id_fk', 'name', 'issuing_organization', 'issue_date', 'expiration_date', 'credential_id', 'credential_url']
    add_columns = ['person_id_fk', 'name', 'issuing_organization', 'issue_date', 'expiration_date', 'credential_id', 'credential_url']
    edit_columns = ['person_id_fk', 'name', 'issuing_organization', 'issue_date', 'expiration_date', 'credential_id', 'credential_url']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['name', 'issuing_organization', 'credential_id', 'credential_url']
    label_columns = {'id': 'Id', 'person_id_fk': 'Person Id Fk', 'name': 'Name', 'issuing_organization': 'Issuing Organization', 'issue_date': 'Issue Date', 'expiration_date': 'Expiration Date', 'credential_id': 'Credential Id', 'credential_url': 'Credential Url'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'name', 'issuing_organization', 'issue_date', 'expiration_date', 'credential_id', 'credential_url']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'name', 'issuing_organization', 'issue_date', 'expiration_date', 'credential_id', 'credential_url']})
    ]
    

    add_fieldsets = [
        ('Add Person Certification', {'fields': ['person_id_fk', 'name', 'issuing_organization', 'issue_date', 'expiration_date', 'credential_id', 'credential_url']})
    ]
    

    edit_fieldsets = [
        ('Edit Person Certification', {'fields': ['person_id_fk', 'name', 'issuing_organization', 'issue_date', 'expiration_date', 'credential_id', 'credential_url']})
    ]
    
    validators_columns = {'person_id_fk': '[validators.DataRequired()]', 'name': '[validators.DataRequired(), validators.Length(max=150)]', 'issuing_organization': '[validators.DataRequired(), validators.Length(max=150)]', 'issue_date': '[validators.DataRequired()]', 'credential_id': '[validators.Length(max=100)]', 'credential_url': '[validators.Length(max=255)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'person_id_fk': 'db.session.query(Person)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'person_id_fk' : IntegerField('Person_id_fk', validators=[validators.DataRequired()]),
    'name': StringField('Name', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=150)]),
    'issuing_organization': StringField('Issuing_organization', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=150)]),
    'issue_date' : DateField('Issue_date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'expiration_date' : DateField('Expiration_date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'credential_id': StringField('Credential_id', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=100)]),
    'credential_url': StringField('Credential_url', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=255)]),
    'person_fk': QuerySelectField('Person_fk', query_factory=lambda: db.session.query(Person), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.name
    

class PersonCourseView(ModelView):
    datamodel = SQLAInterface('PersonCourse')
    list_title = 'Person Course List'
    show_title = 'Person Course Details'
    add_title = 'Add Person Course'
    edit_title = 'Edit Person Course'
    list_columns = ['id', 'person_id_fk', 'name', 'institution', 'completion_date', 'description']
    show_columns = ['id', 'person_id_fk', 'name', 'institution', 'completion_date', 'description']
    add_columns = ['person_id_fk', 'name', 'institution', 'completion_date', 'description']
    edit_columns = ['person_id_fk', 'name', 'institution', 'completion_date', 'description']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['name', 'institution', 'description']
    label_columns = {'id': 'Id', 'person_id_fk': 'Person Id Fk', 'name': 'Name', 'institution': 'Institution', 'completion_date': 'Completion Date', 'description': 'Description'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'name', 'institution', 'completion_date', 'description']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'name', 'institution', 'completion_date', 'description']})
    ]
    

    add_fieldsets = [
        ('Add Person Course', {'fields': ['person_id_fk', 'name', 'institution', 'completion_date', 'description']})
    ]
    

    edit_fieldsets = [
        ('Edit Person Course', {'fields': ['person_id_fk', 'name', 'institution', 'completion_date', 'description']})
    ]
    
    validators_columns = {'person_id_fk': '[validators.DataRequired()]', 'name': '[validators.DataRequired(), validators.Length(max=150)]', 'institution': '[validators.DataRequired(), validators.Length(max=150)]', 'completion_date': '[validators.DataRequired()]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'person_id_fk': 'db.session.query(Person)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'person_id_fk' : IntegerField('Person_id_fk', validators=[validators.DataRequired()]),
    'name': StringField('Name', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=150)]),
    'institution': StringField('Institution', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=150)]),
    'completion_date' : DateField('Completion_date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'description': StringField('Description', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'person_fk': QuerySelectField('Person_fk', query_factory=lambda: db.session.query(Person), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.name
    

class PersonEducationView(ModelView):
    datamodel = SQLAInterface('PersonEducation')
    list_title = 'Person Education List'
    show_title = 'Person Education Details'
    add_title = 'Add Person Education'
    edit_title = 'Edit Person Education'
    list_columns = ['id', 'person_id_fk', 'school_name', 'degree', 'field_of_study', 'start_date', 'end_date', 'description']
    show_columns = ['id', 'person_id_fk', 'school_name', 'degree', 'field_of_study', 'start_date', 'end_date', 'description']
    add_columns = ['person_id_fk', 'school_name', 'degree', 'field_of_study', 'start_date', 'end_date', 'description']
    edit_columns = ['person_id_fk', 'school_name', 'degree', 'field_of_study', 'start_date', 'end_date', 'description']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['school_name', 'degree', 'field_of_study', 'description']
    label_columns = {'id': 'Id', 'person_id_fk': 'Person Id Fk', 'school_name': 'School Name', 'degree': 'Degree', 'field_of_study': 'Field Of Study', 'start_date': 'Start Date', 'end_date': 'End Date', 'description': 'Description'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'school_name', 'degree', 'field_of_study', 'start_date', 'end_date', 'description']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'school_name', 'degree', 'field_of_study', 'start_date', 'end_date', 'description']})
    ]
    

    add_fieldsets = [
        ('Add Person Education', {'fields': ['person_id_fk', 'school_name', 'degree', 'field_of_study', 'start_date', 'end_date', 'description']})
    ]
    

    edit_fieldsets = [
        ('Edit Person Education', {'fields': ['person_id_fk', 'school_name', 'degree', 'field_of_study', 'start_date', 'end_date', 'description']})
    ]
    
    validators_columns = {'person_id_fk': '[validators.DataRequired()]', 'school_name': '[validators.DataRequired(), validators.Length(max=150)]', 'degree': '[validators.Length(max=100)]', 'field_of_study': '[validators.Length(max=100)]', 'start_date': '[validators.DataRequired()]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'person_id_fk': 'db.session.query(Person)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'person_id_fk' : IntegerField('Person_id_fk', validators=[validators.DataRequired()]),
    'school_name': StringField('School_name', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=150)]),
    'degree': StringField('Degree', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=100)]),
    'field_of_study': StringField('Field_of_study', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=100)]),
    'start_date' : DateField('Start_date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'end_date' : DateField('End_date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'description': StringField('Description', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'person_fk': QuerySelectField('Person_fk', query_factory=lambda: db.session.query(Person), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class PersonExperienceView(ModelView):
    datamodel = SQLAInterface('PersonExperience')
    list_title = 'Person Experience List'
    show_title = 'Person Experience Details'
    add_title = 'Add Person Experience'
    edit_title = 'Edit Person Experience'
    list_columns = ['id', 'person_id_fk', 'job_title', 'company_name', 'location', 'start_date', 'end_date', 'description', 'awards']
    show_columns = ['id', 'person_id_fk', 'job_title', 'company_name', 'location', 'start_date', 'end_date', 'description', 'awards']
    add_columns = ['person_id_fk', 'job_title', 'company_name', 'location', 'start_date', 'end_date', 'description', 'awards']
    edit_columns = ['person_id_fk', 'job_title', 'company_name', 'location', 'start_date', 'end_date', 'description', 'awards']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['job_title', 'company_name', 'location', 'description', 'awards']
    label_columns = {'id': 'Id', 'person_id_fk': 'Person Id Fk', 'job_title': 'Job Title', 'company_name': 'Company Name', 'location': 'Location', 'start_date': 'Start Date', 'end_date': 'End Date', 'description': 'Description', 'awards': 'Awards'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'job_title', 'company_name', 'location', 'start_date', 'end_date', 'description', 'awards']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'job_title', 'company_name', 'location', 'start_date', 'end_date', 'description', 'awards']})
    ]
    

    add_fieldsets = [
        ('Add Person Experience', {'fields': ['person_id_fk', 'job_title', 'company_name', 'location', 'start_date', 'end_date', 'description', 'awards']})
    ]
    

    edit_fieldsets = [
        ('Edit Person Experience', {'fields': ['person_id_fk', 'job_title', 'company_name', 'location', 'start_date', 'end_date', 'description', 'awards']})
    ]
    
    validators_columns = {'person_id_fk': '[validators.DataRequired()]', 'job_title': '[validators.DataRequired(), validators.Length(max=150)]', 'company_name': '[validators.DataRequired(), validators.Length(max=150)]', 'location': '[validators.Length(max=150)]', 'start_date': '[validators.DataRequired()]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'person_id_fk': 'db.session.query(Person)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'person_id_fk' : IntegerField('Person_id_fk', validators=[validators.DataRequired()]),
    'job_title': StringField('Job_title', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=150)]),
    'company_name': StringField('Company_name', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=150)]),
    'location': StringField('Location', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=150)]),
    'start_date' : DateField('Start_date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'end_date' : DateField('End_date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'description': StringField('Description', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'awards': StringField('Awards', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'person_fk': QuerySelectField('Person_fk', query_factory=lambda: db.session.query(Person), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class PersonHonorAwardView(ModelView):
    datamodel = SQLAInterface('PersonHonorAward')
    list_title = 'Person Honor Award List'
    show_title = 'Person Honor Award Details'
    add_title = 'Add Person Honor Award'
    edit_title = 'Edit Person Honor Award'
    list_columns = ['id', 'person_id_fk', 'title', 'issuer', 'date_received', 'description']
    show_columns = ['id', 'person_id_fk', 'title', 'issuer', 'date_received', 'description']
    add_columns = ['person_id_fk', 'title', 'issuer', 'date_received', 'description']
    edit_columns = ['person_id_fk', 'title', 'issuer', 'date_received', 'description']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['title', 'issuer', 'description']
    label_columns = {'id': 'Id', 'person_id_fk': 'Person Id Fk', 'title': 'Title', 'issuer': 'Issuer', 'date_received': 'Date Received', 'description': 'Description'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'title', 'issuer', 'date_received', 'description']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'title', 'issuer', 'date_received', 'description']})
    ]
    

    add_fieldsets = [
        ('Add Person Honor Award', {'fields': ['person_id_fk', 'title', 'issuer', 'date_received', 'description']})
    ]
    

    edit_fieldsets = [
        ('Edit Person Honor Award', {'fields': ['person_id_fk', 'title', 'issuer', 'date_received', 'description']})
    ]
    
    validators_columns = {'person_id_fk': '[validators.DataRequired()]', 'title': '[validators.DataRequired(), validators.Length(max=150)]', 'issuer': '[validators.DataRequired(), validators.Length(max=150)]', 'date_received': '[validators.DataRequired()]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'person_id_fk': 'db.session.query(Person)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'person_id_fk' : IntegerField('Person_id_fk', validators=[validators.DataRequired()]),
    'title': StringField('Title', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=150)]),
    'issuer': StringField('Issuer', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=150)]),
    'date_received' : DateField('Date_received', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'description': StringField('Description', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'person_fk': QuerySelectField('Person_fk', query_factory=lambda: db.session.query(Person), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.title
    

class PersonLanguageView(ModelView):
    datamodel = SQLAInterface('PersonLanguage')
    list_title = 'Person Language List'
    show_title = 'Person Language Details'
    add_title = 'Add Person Language'
    edit_title = 'Edit Person Language'
    list_columns = ['id', 'person_id_fk', 'name', 'proficiency']
    show_columns = ['id', 'person_id_fk', 'name', 'proficiency']
    add_columns = ['person_id_fk', 'name', 'proficiency']
    edit_columns = ['person_id_fk', 'name', 'proficiency']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['name', 'proficiency']
    label_columns = {'id': 'Id', 'person_id_fk': 'Person Id Fk', 'name': 'Name', 'proficiency': 'Proficiency'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'name', 'proficiency']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'name', 'proficiency']})
    ]
    

    add_fieldsets = [
        ('Add Person Language', {'fields': ['person_id_fk', 'name', 'proficiency']})
    ]
    

    edit_fieldsets = [
        ('Edit Person Language', {'fields': ['person_id_fk', 'name', 'proficiency']})
    ]
    
    validators_columns = {'person_id_fk': '[validators.DataRequired()]', 'name': '[validators.DataRequired(), validators.Length(max=50)]', 'proficiency': '[validators.DataRequired(), validators.Length(max=12)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'person_id_fk': 'db.session.query(Person)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'person_id_fk' : IntegerField('Person_id_fk', validators=[validators.DataRequired()]),
    'name': StringField('Name', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=50)]),
    'proficiency': StringField('Proficiency', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=12)]),
    'person_fk': QuerySelectField('Person_fk', query_factory=lambda: db.session.query(Person), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.name
    

class PersonOrganizationMembershipView(ModelView):
    datamodel = SQLAInterface('PersonOrganizationMembership')
    list_title = 'Person Organization Membership List'
    show_title = 'Person Organization Membership Details'
    add_title = 'Add Person Organization Membership'
    edit_title = 'Edit Person Organization Membership'
    list_columns = ['id', 'person_id_fk', 'organization_name', 'role', 'start_date', 'end_date', 'description']
    show_columns = ['id', 'person_id_fk', 'organization_name', 'role', 'start_date', 'end_date', 'description']
    add_columns = ['person_id_fk', 'organization_name', 'role', 'start_date', 'end_date', 'description']
    edit_columns = ['person_id_fk', 'organization_name', 'role', 'start_date', 'end_date', 'description']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['organization_name', 'role', 'description']
    label_columns = {'id': 'Id', 'person_id_fk': 'Person Id Fk', 'organization_name': 'Organization Name', 'role': 'Role', 'start_date': 'Start Date', 'end_date': 'End Date', 'description': 'Description'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'organization_name', 'role', 'start_date', 'end_date', 'description']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'organization_name', 'role', 'start_date', 'end_date', 'description']})
    ]
    

    add_fieldsets = [
        ('Add Person Organization Membership', {'fields': ['person_id_fk', 'organization_name', 'role', 'start_date', 'end_date', 'description']})
    ]
    

    edit_fieldsets = [
        ('Edit Person Organization Membership', {'fields': ['person_id_fk', 'organization_name', 'role', 'start_date', 'end_date', 'description']})
    ]
    
    validators_columns = {'person_id_fk': '[validators.DataRequired()]', 'organization_name': '[validators.DataRequired(), validators.Length(max=150)]', 'role': '[validators.DataRequired(), validators.Length(max=150)]', 'start_date': '[validators.DataRequired()]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'person_id_fk': 'db.session.query(Person)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'person_id_fk' : IntegerField('Person_id_fk', validators=[validators.DataRequired()]),
    'organization_name': StringField('Organization_name', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=150)]),
    'role': StringField('Role', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=150)]),
    'start_date' : DateField('Start_date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'end_date' : DateField('End_date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'description': StringField('Description', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'person_fk': QuerySelectField('Person_fk', query_factory=lambda: db.session.query(Person), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class PersonPatentView(ModelView):
    datamodel = SQLAInterface('PersonPatent')
    list_title = 'Person Patent List'
    show_title = 'Person Patent Details'
    add_title = 'Add Person Patent'
    edit_title = 'Edit Person Patent'
    list_columns = ['id', 'person_id_fk', 'title', 'patent_office', 'patent_number', 'issue_date', 'description']
    show_columns = ['id', 'person_id_fk', 'title', 'patent_office', 'patent_number', 'issue_date', 'description']
    add_columns = ['person_id_fk', 'title', 'patent_office', 'patent_number', 'issue_date', 'description']
    edit_columns = ['person_id_fk', 'title', 'patent_office', 'patent_number', 'issue_date', 'description']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['title', 'patent_office', 'patent_number', 'description']
    label_columns = {'id': 'Id', 'person_id_fk': 'Person Id Fk', 'title': 'Title', 'patent_office': 'Patent Office', 'patent_number': 'Patent Number', 'issue_date': 'Issue Date', 'description': 'Description'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'title', 'patent_office', 'patent_number', 'issue_date', 'description']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'title', 'patent_office', 'patent_number', 'issue_date', 'description']})
    ]
    

    add_fieldsets = [
        ('Add Person Patent', {'fields': ['person_id_fk', 'title', 'patent_office', 'patent_number', 'issue_date', 'description']})
    ]
    

    edit_fieldsets = [
        ('Edit Person Patent', {'fields': ['person_id_fk', 'title', 'patent_office', 'patent_number', 'issue_date', 'description']})
    ]
    
    validators_columns = {'person_id_fk': '[validators.DataRequired()]', 'title': '[validators.DataRequired(), validators.Length(max=150)]', 'patent_office': '[validators.DataRequired(), validators.Length(max=150)]', 'patent_number': '[validators.DataRequired(), validators.Length(max=50)]', 'issue_date': '[validators.DataRequired()]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'person_id_fk': 'db.session.query(Person)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'person_id_fk' : IntegerField('Person_id_fk', validators=[validators.DataRequired()]),
    'title': StringField('Title', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=150)]),
    'patent_office': StringField('Patent_office', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=150)]),
    'patent_number': StringField('Patent_number', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=50)]),
    'issue_date' : DateField('Issue_date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'description': StringField('Description', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'person_fk': QuerySelectField('Person_fk', query_factory=lambda: db.session.query(Person), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.title
    

class PersonProjectView(ModelView):
    datamodel = SQLAInterface('PersonProject')
    list_title = 'Person Project List'
    show_title = 'Person Project Details'
    add_title = 'Add Person Project'
    edit_title = 'Edit Person Project'
    list_columns = ['id', 'person_id_fk', 'name', 'description', 'start_date', 'end_date', 'project_url']
    show_columns = ['id', 'person_id_fk', 'name', 'description', 'start_date', 'end_date', 'project_url']
    add_columns = ['person_id_fk', 'name', 'description', 'start_date', 'end_date', 'project_url']
    edit_columns = ['person_id_fk', 'name', 'description', 'start_date', 'end_date', 'project_url']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['name', 'description', 'project_url']
    label_columns = {'id': 'Id', 'person_id_fk': 'Person Id Fk', 'name': 'Name', 'description': 'Description', 'start_date': 'Start Date', 'end_date': 'End Date', 'project_url': 'Project Url'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'name', 'description', 'start_date', 'end_date', 'project_url']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'name', 'description', 'start_date', 'end_date', 'project_url']})
    ]
    

    add_fieldsets = [
        ('Add Person Project', {'fields': ['person_id_fk', 'name', 'description', 'start_date', 'end_date', 'project_url']})
    ]
    

    edit_fieldsets = [
        ('Edit Person Project', {'fields': ['person_id_fk', 'name', 'description', 'start_date', 'end_date', 'project_url']})
    ]
    
    validators_columns = {'person_id_fk': '[validators.DataRequired()]', 'name': '[validators.DataRequired(), validators.Length(max=150)]', 'start_date': '[validators.DataRequired()]', 'project_url': '[validators.Length(max=255)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'person_id_fk': 'db.session.query(Person)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'person_id_fk' : IntegerField('Person_id_fk', validators=[validators.DataRequired()]),
    'name': StringField('Name', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=150)]),
    'description': StringField('Description', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'start_date' : DateField('Start_date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'end_date' : DateField('End_date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'project_url': StringField('Project_url', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=255)]),
    'person_fk': QuerySelectField('Person_fk', query_factory=lambda: db.session.query(Person), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.name
    

class PersonPublicationView(ModelView):
    datamodel = SQLAInterface('PersonPublication')
    list_title = 'Person Publication List'
    show_title = 'Person Publication Details'
    add_title = 'Add Person Publication'
    edit_title = 'Edit Person Publication'
    list_columns = ['id', 'person_id_fk', 'title', 'publisher', 'date', 'url', 'description']
    show_columns = ['id', 'person_id_fk', 'title', 'publisher', 'date', 'url', 'description']
    add_columns = ['person_id_fk', 'title', 'publisher', 'date', 'url', 'description']
    edit_columns = ['person_id_fk', 'title', 'publisher', 'date', 'url', 'description']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['title', 'publisher', 'url', 'description']
    label_columns = {'id': 'Id', 'person_id_fk': 'Person Id Fk', 'title': 'Title', 'publisher': 'Publisher', 'date': 'Date', 'url': 'Url', 'description': 'Description'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'title', 'publisher', 'date', 'url', 'description']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'title', 'publisher', 'date', 'url', 'description']})
    ]
    

    add_fieldsets = [
        ('Add Person Publication', {'fields': ['person_id_fk', 'title', 'publisher', 'date', 'url', 'description']})
    ]
    

    edit_fieldsets = [
        ('Edit Person Publication', {'fields': ['person_id_fk', 'title', 'publisher', 'date', 'url', 'description']})
    ]
    
    validators_columns = {'person_id_fk': '[validators.DataRequired()]', 'title': '[validators.DataRequired(), validators.Length(max=150)]', 'publisher': '[validators.DataRequired(), validators.Length(max=150)]', 'date': '[validators.DataRequired()]', 'url': '[validators.Length(max=255)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'person_id_fk': 'db.session.query(Person)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'person_id_fk' : IntegerField('Person_id_fk', validators=[validators.DataRequired()]),
    'title': StringField('Title', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=150)]),
    'publisher': StringField('Publisher', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=150)]),
    'date' : DateField('Date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'url': StringField('Url', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=255)]),
    'description': StringField('Description', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'person_fk': QuerySelectField('Person_fk', query_factory=lambda: db.session.query(Person), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.title
    

class PersonVolunteerExperienceView(ModelView):
    datamodel = SQLAInterface('PersonVolunteerExperience')
    list_title = 'Person Volunteer Experience List'
    show_title = 'Person Volunteer Experience Details'
    add_title = 'Add Person Volunteer Experience'
    edit_title = 'Edit Person Volunteer Experience'
    list_columns = ['id', 'person_id_fk', 'role', 'organization', 'cause', 'start_date', 'end_date', 'description']
    show_columns = ['id', 'person_id_fk', 'role', 'organization', 'cause', 'start_date', 'end_date', 'description']
    add_columns = ['person_id_fk', 'role', 'organization', 'cause', 'start_date', 'end_date', 'description']
    edit_columns = ['person_id_fk', 'role', 'organization', 'cause', 'start_date', 'end_date', 'description']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['role', 'organization', 'cause', 'description']
    label_columns = {'id': 'Id', 'person_id_fk': 'Person Id Fk', 'role': 'Role', 'organization': 'Organization', 'cause': 'Cause', 'start_date': 'Start Date', 'end_date': 'End Date', 'description': 'Description'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'role', 'organization', 'cause', 'start_date', 'end_date', 'description']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'role', 'organization', 'cause', 'start_date', 'end_date', 'description']})
    ]
    

    add_fieldsets = [
        ('Add Person Volunteer Experience', {'fields': ['person_id_fk', 'role', 'organization', 'cause', 'start_date', 'end_date', 'description']})
    ]
    

    edit_fieldsets = [
        ('Edit Person Volunteer Experience', {'fields': ['person_id_fk', 'role', 'organization', 'cause', 'start_date', 'end_date', 'description']})
    ]
    
    validators_columns = {'person_id_fk': '[validators.DataRequired()]', 'role': '[validators.DataRequired(), validators.Length(max=150)]', 'organization': '[validators.DataRequired(), validators.Length(max=150)]', 'cause': '[validators.Length(max=150)]', 'start_date': '[validators.DataRequired()]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'person_id_fk': 'db.session.query(Person)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'person_id_fk' : IntegerField('Person_id_fk', validators=[validators.DataRequired()]),
    'role': StringField('Role', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=150)]),
    'organization': StringField('Organization', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=150)]),
    'cause': StringField('Cause', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=150)]),
    'start_date' : DateField('Start_date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'end_date' : DateField('End_date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'description': StringField('Description', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'person_fk': QuerySelectField('Person_fk', query_factory=lambda: db.session.query(Person), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class PointEarningActivityView(ModelView):
    datamodel = SQLAInterface('PointEarningActivity')
    list_title = 'Point Earning Activity List'
    show_title = 'Point Earning Activity Details'
    add_title = 'Add Point Earning Activity'
    edit_title = 'Edit Point Earning Activity'
    list_columns = ['id', 'person_id_fk', 'activity_type', 'points_earned', 'timestamp']
    show_columns = ['id', 'person_id_fk', 'activity_type', 'points_earned', 'timestamp']
    add_columns = ['person_id_fk', 'activity_type', 'points_earned', 'timestamp']
    edit_columns = ['person_id_fk', 'activity_type', 'points_earned', 'timestamp']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['activity_type']
    label_columns = {'id': 'Id', 'person_id_fk': 'Person Id Fk', 'activity_type': 'Activity Type', 'points_earned': 'Points Earned', 'timestamp': 'Timestamp'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'activity_type', 'points_earned', 'timestamp']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'activity_type', 'points_earned', 'timestamp']})
    ]
    

    add_fieldsets = [
        ('Add Point Earning Activity', {'fields': ['person_id_fk', 'activity_type', 'points_earned', 'timestamp']})
    ]
    

    edit_fieldsets = [
        ('Edit Point Earning Activity', {'fields': ['person_id_fk', 'activity_type', 'points_earned', 'timestamp']})
    ]
    
    validators_columns = {'person_id_fk': '[validators.DataRequired()]', 'activity_type': '[validators.DataRequired(), validators.Length(max=50)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'person_id_fk': 'db.session.query(Person)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'person_id_fk' : IntegerField('Person_id_fk', validators=[validators.DataRequired()]),
    'activity_type': StringField('Activity_type', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=50)]),
    'points_earned' : IntegerField('Points_earned', validators=[validators.DataRequired()]),
    'timestamp' : DateTimeField('Timestamp', widget=DateTimePickerWidget(), validators=[validators.DataRequired()]),
    'person_fk': QuerySelectField('Person_fk', query_factory=lambda: db.session.query(Person), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class ProfileUpdateReminderView(ModelView):
    datamodel = SQLAInterface('ProfileUpdateReminder')
    list_title = 'Profile Update Reminder List'
    show_title = 'Profile Update Reminder Details'
    add_title = 'Add Profile Update Reminder'
    edit_title = 'Edit Profile Update Reminder'
    list_columns = ['id', 'person_id_fk', 'last_reminder_date', 'reminder_count', 'next_reminder_date']
    show_columns = ['id', 'person_id_fk', 'last_reminder_date', 'reminder_count', 'next_reminder_date']
    add_columns = ['person_id_fk', 'last_reminder_date', 'reminder_count', 'next_reminder_date']
    edit_columns = ['person_id_fk', 'last_reminder_date', 'reminder_count', 'next_reminder_date']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = []
    label_columns = {'id': 'Id', 'person_id_fk': 'Person Id Fk', 'last_reminder_date': 'Last Reminder Date', 'reminder_count': 'Reminder Count', 'next_reminder_date': 'Next Reminder Date'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'last_reminder_date', 'reminder_count', 'next_reminder_date']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'last_reminder_date', 'reminder_count', 'next_reminder_date']})
    ]
    

    add_fieldsets = [
        ('Add Profile Update Reminder', {'fields': ['person_id_fk', 'last_reminder_date', 'reminder_count', 'next_reminder_date']})
    ]
    

    edit_fieldsets = [
        ('Edit Profile Update Reminder', {'fields': ['person_id_fk', 'last_reminder_date', 'reminder_count', 'next_reminder_date']})
    ]
    
    validators_columns = {'person_id_fk': '[validators.DataRequired()]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'person_id_fk': 'db.session.query(Person)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'person_id_fk' : IntegerField('Person_id_fk', validators=[validators.DataRequired()]),
    'last_reminder_date' : DateTimeField('Last_reminder_date', widget=DateTimePickerWidget(), validators=[validators.DataRequired()]),
    'reminder_count' : IntegerField('Reminder_count', validators=[validators.DataRequired()]),
    'next_reminder_date' : DateTimeField('Next_reminder_date', widget=DateTimePickerWidget(), validators=[validators.DataRequired()]),
    'person_fk': QuerySelectField('Person_fk', query_factory=lambda: db.session.query(Person), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class SkillView(ModelView):
    datamodel = SQLAInterface('Skill')
    list_title = 'Skill List'
    show_title = 'Skill Details'
    add_title = 'Add Skill'
    edit_title = 'Edit Skill'
    list_columns = ['id', 'name', 'skill_category_id_fk', 'description']
    show_columns = ['id', 'name', 'skill_category_id_fk', 'description']
    add_columns = ['name', 'skill_category_id_fk', 'description']
    edit_columns = ['name', 'skill_category_id_fk', 'description']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['name', 'description']
    label_columns = {'id': 'Id', 'name': 'Name', 'skill_category_id_fk': 'Skill Category Id Fk', 'description': 'Description'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'skill_category_id_fk', 'description']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'skill_category_id_fk', 'description']})
    ]
    

    add_fieldsets = [
        ('Add Skill', {'fields': ['name', 'skill_category_id_fk', 'description']})
    ]
    

    edit_fieldsets = [
        ('Edit Skill', {'fields': ['name', 'skill_category_id_fk', 'description']})
    ]
    
    validators_columns = {'name': '[validators.DataRequired(), validators.Length(max=100)]', 'skill_category_id_fk': '[validators.DataRequired()]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'skill_category_id_fk': 'db.session.query(SkillCategory)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'name': StringField('Name', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=100)]),
    'skill_category_id_fk' : IntegerField('Skill_category_id_fk', validators=[validators.DataRequired()]),
    'description': StringField('Description', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'skill_category_fk': QuerySelectField('Skill_category_fk', query_factory=lambda: db.session.query(SkillCategory), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.name
    

class TimezoneView(ModelView):
    datamodel = SQLAInterface('Timezone')
    list_title = 'Timezone List'
    show_title = 'Timezone Details'
    add_title = 'Add Timezone'
    edit_title = 'Edit Timezone'
    list_columns = ['id', 'country_id_fk', 'timezonename', 'comments']
    show_columns = ['id', 'country_id_fk', 'timezonename', 'comments']
    add_columns = ['country_id_fk', 'timezonename', 'comments']
    edit_columns = ['country_id_fk', 'timezonename', 'comments']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['timezonename', 'comments']
    label_columns = {'id': 'Id', 'country_id_fk': 'Country Id Fk', 'timezonename': 'Timezonename', 'comments': 'Comments'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'country_id_fk', 'timezonename', 'comments']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'country_id_fk', 'timezonename', 'comments']})
    ]
    

    add_fieldsets = [
        ('Add Timezone', {'fields': ['country_id_fk', 'timezonename', 'comments']})
    ]
    

    edit_fieldsets = [
        ('Edit Timezone', {'fields': ['country_id_fk', 'timezonename', 'comments']})
    ]
    
    validators_columns = {'timezonename': '[validators.Length(max=100)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'country_id_fk': 'db.session.query(Country)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'country_id_fk' : IntegerField('Country_id_fk', validators=[validators.DataRequired()]),
    'timezonename': StringField('Timezonename', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=100)]),
    'comments': StringField('Comments', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'country_fk': QuerySelectField('Country_fk', query_factory=lambda: db.session.query(Country), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class UserActivityView(ModelView):
    datamodel = SQLAInterface('UserActivity')
    list_title = 'User Activity List'
    show_title = 'User Activity Details'
    add_title = 'Add User Activity'
    edit_title = 'Edit User Activity'
    list_columns = ['id', 'person_id_fk', 'activity_type', 'timestamp', 'details']
    show_columns = ['id', 'person_id_fk', 'activity_type', 'timestamp', 'details']
    add_columns = ['person_id_fk', 'activity_type', 'timestamp', 'details']
    edit_columns = ['person_id_fk', 'activity_type', 'timestamp', 'details']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['activity_type', 'details']
    label_columns = {'id': 'Id', 'person_id_fk': 'Person Id Fk', 'activity_type': 'Activity Type', 'timestamp': 'Timestamp', 'details': 'Details'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'activity_type', 'timestamp', 'details']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'activity_type', 'timestamp', 'details']})
    ]
    

    add_fieldsets = [
        ('Add User Activity', {'fields': ['person_id_fk', 'activity_type', 'timestamp', 'details']})
    ]
    

    edit_fieldsets = [
        ('Edit User Activity', {'fields': ['person_id_fk', 'activity_type', 'timestamp', 'details']})
    ]
    
    validators_columns = {'person_id_fk': '[validators.DataRequired()]', 'activity_type': '[validators.Length(max=50)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'person_id_fk': 'db.session.query(Person)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'person_id_fk' : IntegerField('Person_id_fk', validators=[validators.DataRequired()]),
    'activity_type': StringField('Activity_type', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=50)]),
    'timestamp' : DateTimeField('Timestamp', widget=DateTimePickerWidget(), validators=[validators.DataRequired()]),
    'details': StringField('Details', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'person_fk': QuerySelectField('Person_fk', query_factory=lambda: db.session.query(Person), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class UserGamificationView(ModelView):
    datamodel = SQLAInterface('UserGamification')
    list_title = 'User Gamification List'
    show_title = 'User Gamification Details'
    add_title = 'Add User Gamification'
    edit_title = 'Edit User Gamification'
    list_columns = ['id', 'user_id_fk', 'points', 'level', 'last_point_earned', 'points_to_next_level']
    show_columns = ['id', 'user_id_fk', 'points', 'level', 'last_point_earned', 'points_to_next_level']
    add_columns = ['user_id_fk', 'points', 'level', 'last_point_earned', 'points_to_next_level']
    edit_columns = ['user_id_fk', 'points', 'level', 'last_point_earned', 'points_to_next_level']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = []
    label_columns = {'id': 'Id', 'user_id_fk': 'User Id Fk', 'points': 'Points', 'level': 'Level', 'last_point_earned': 'Last Point Earned', 'points_to_next_level': 'Points To Next Level'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'user_id_fk', 'points', 'level', 'last_point_earned', 'points_to_next_level']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'user_id_fk', 'points', 'level', 'last_point_earned', 'points_to_next_level']})
    ]
    

    add_fieldsets = [
        ('Add User Gamification', {'fields': ['user_id_fk', 'points', 'level', 'last_point_earned', 'points_to_next_level']})
    ]
    

    edit_fieldsets = [
        ('Edit User Gamification', {'fields': ['user_id_fk', 'points', 'level', 'last_point_earned', 'points_to_next_level']})
    ]
    
    validators_columns = {'user_id_fk': '[validators.DataRequired()]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'user_id_fk': 'db.session.query(Person)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'user_id_fk' : IntegerField('User_id_fk', validators=[validators.DataRequired()]),
    'points' : IntegerField('Points', validators=[validators.DataRequired()]),
    'level' : IntegerField('Level', validators=[validators.DataRequired()]),
    'last_point_earned' : DateTimeField('Last_point_earned', widget=DateTimePickerWidget(), validators=[validators.DataRequired()]),
    'points_to_next_level' : IntegerField('Points_to_next_level', validators=[validators.DataRequired()]),
    'user_fk': QuerySelectField('User_fk', query_factory=lambda: db.session.query(Person), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class BoardMemberView(ModelView):
    datamodel = SQLAInterface('BoardMember')
    list_title = 'Board Member List'
    show_title = 'Board Member Details'
    add_title = 'Add Board Member'
    edit_title = 'Edit Board Member'
    list_columns = ['id', 'organization_id_fk', 'person_id_fk', 'position', 'start_date', 'end_date']
    show_columns = ['id', 'organization_id_fk', 'person_id_fk', 'position', 'start_date', 'end_date']
    add_columns = ['organization_id_fk', 'person_id_fk', 'position', 'start_date', 'end_date']
    edit_columns = ['organization_id_fk', 'person_id_fk', 'position', 'start_date', 'end_date']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['position']
    label_columns = {'id': 'Id', 'organization_id_fk': 'Organization Id Fk', 'person_id_fk': 'Person Id Fk', 'position': 'Position', 'start_date': 'Start Date', 'end_date': 'End Date'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id_fk', 'person_id_fk', 'position', 'start_date', 'end_date']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id_fk', 'person_id_fk', 'position', 'start_date', 'end_date']})
    ]
    

    add_fieldsets = [
        ('Add Board Member', {'fields': ['organization_id_fk', 'person_id_fk', 'position', 'start_date', 'end_date']})
    ]
    

    edit_fieldsets = [
        ('Edit Board Member', {'fields': ['organization_id_fk', 'person_id_fk', 'position', 'start_date', 'end_date']})
    ]
    
    validators_columns = {'organization_id_fk': '[validators.DataRequired()]', 'person_id_fk': '[validators.DataRequired()]', 'position': '[validators.Length(max=100)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'organization_id_fk': 'db.session.query(Organization)', 'person_id_fk': 'db.session.query(Person)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'organization_id_fk' : IntegerField('Organization_id_fk', validators=[validators.DataRequired()]),
    'person_id_fk' : IntegerField('Person_id_fk', validators=[validators.DataRequired()]),
    'position': StringField('Position', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=100)]),
    'start_date' : DateField('Start_date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'end_date' : DateField('End_date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'organization_fk': QuerySelectField('Organization_fk', query_factory=lambda: db.session.query(Organization), widget=Select2Widget(), allow_blank=True),
    'person_fk': QuerySelectField('Person_fk', query_factory=lambda: db.session.query(Person), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class ContactApplicationView(ModelView):
    datamodel = SQLAInterface('ContactApplication')
    list_title = 'Contact Application List'
    show_title = 'Contact Application Details'
    add_title = 'Add Contact Application'
    edit_title = 'Edit Contact Application'
    list_columns = ['id', 'person_id_fk', 'organization_id_fk', 'position', 'message', 'application_date', 'status', 'review_date', 'review_notes']
    show_columns = ['id', 'person_id_fk', 'organization_id_fk', 'position', 'message', 'application_date', 'status', 'review_date', 'review_notes']
    add_columns = ['person_id_fk', 'organization_id_fk', 'position', 'message', 'application_date', 'status', 'review_date', 'review_notes']
    edit_columns = ['person_id_fk', 'organization_id_fk', 'position', 'message', 'application_date', 'status', 'review_date', 'review_notes']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['position', 'message', 'status', 'review_notes']
    label_columns = {'id': 'Id', 'person_id_fk': 'Person Id Fk', 'organization_id_fk': 'Organization Id Fk', 'position': 'Position', 'message': 'Message', 'application_date': 'Application Date', 'status': 'Status', 'review_date': 'Review Date', 'review_notes': 'Review Notes'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'organization_id_fk', 'position', 'message', 'application_date', 'status', 'review_date', 'review_notes']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'organization_id_fk', 'position', 'message', 'application_date', 'status', 'review_date', 'review_notes']})
    ]
    

    add_fieldsets = [
        ('Add Contact Application', {'fields': ['person_id_fk', 'organization_id_fk', 'position', 'message', 'application_date', 'status', 'review_date', 'review_notes']})
    ]
    

    edit_fieldsets = [
        ('Edit Contact Application', {'fields': ['person_id_fk', 'organization_id_fk', 'position', 'message', 'application_date', 'status', 'review_date', 'review_notes']})
    ]
    
    validators_columns = {'person_id_fk': '[validators.DataRequired()]', 'organization_id_fk': '[validators.DataRequired()]', 'position': '[validators.Length(max=100)]', 'status': '[validators.Length(max=11)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'organization_id_fk': 'db.session.query(Organization)', 'person_id_fk': 'db.session.query(Person)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'person_id_fk' : IntegerField('Person_id_fk', validators=[validators.DataRequired()]),
    'organization_id_fk' : IntegerField('Organization_id_fk', validators=[validators.DataRequired()]),
    'position': StringField('Position', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=100)]),
    'message': StringField('Message', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'application_date' : DateTimeField('Application_date', widget=DateTimePickerWidget(), validators=[validators.DataRequired()]),
    'status': StringField('Status', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=11)]),
    'review_date' : DateTimeField('Review_date', widget=DateTimePickerWidget(), validators=[validators.DataRequired()]),
    'review_notes': StringField('Review_notes', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'organization_fk': QuerySelectField('Organization_fk', query_factory=lambda: db.session.query(Organization), widget=Select2Widget(), allow_blank=True),
    'person_fk': QuerySelectField('Person_fk', query_factory=lambda: db.session.query(Person), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class DocumentSubmissionView(ModelView):
    datamodel = SQLAInterface('DocumentSubmission')
    list_title = 'Document Submission List'
    show_title = 'Document Submission Details'
    add_title = 'Add Document Submission'
    edit_title = 'Edit Document Submission'
    list_columns = ['id', 'organization_id_fk', 'document_type', 'document_name', 'file_path', 'upload_date', 'status', 'next_status', 'review_notes', 'review_date']
    show_columns = ['id', 'organization_id_fk', 'document_type', 'document_name', 'file_path', 'upload_date', 'status', 'next_status', 'review_notes', 'review_date']
    add_columns = ['organization_id_fk', 'document_type', 'document_name', 'file_path', 'upload_date', 'status', 'next_status', 'review_notes', 'review_date']
    edit_columns = ['organization_id_fk', 'document_type', 'document_name', 'file_path', 'upload_date', 'status', 'next_status', 'review_notes', 'review_date']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['document_type', 'document_name', 'file_path', 'status', 'next_status', 'review_notes']
    label_columns = {'id': 'Id', 'organization_id_fk': 'Organization Id Fk', 'document_type': 'Document Type', 'document_name': 'Document Name', 'file_path': 'File Path', 'upload_date': 'Upload Date', 'status': 'Status', 'next_status': 'Next Status', 'review_notes': 'Review Notes', 'review_date': 'Review Date'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id_fk', 'document_type', 'document_name', 'file_path', 'upload_date', 'status', 'next_status', 'review_notes', 'review_date']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id_fk', 'document_type', 'document_name', 'file_path', 'upload_date', 'status', 'next_status', 'review_notes', 'review_date']})
    ]
    

    add_fieldsets = [
        ('Add Document Submission', {'fields': ['organization_id_fk', 'document_type', 'document_name', 'file_path', 'upload_date', 'status', 'next_status', 'review_notes', 'review_date']})
    ]
    

    edit_fieldsets = [
        ('Edit Document Submission', {'fields': ['organization_id_fk', 'document_type', 'document_name', 'file_path', 'upload_date', 'status', 'next_status', 'review_notes', 'review_date']})
    ]
    
    validators_columns = {'organization_id_fk': '[validators.DataRequired()]', 'document_type': '[validators.Length(max=31)]', 'document_name': '[validators.Length(max=200)]', 'file_path': '[validators.Length(max=500)]', 'status': '[validators.Length(max=20)]', 'next_status': '[validators.Length(max=20)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'organization_id_fk': 'db.session.query(Organization)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'organization_id_fk' : IntegerField('Organization_id_fk', validators=[validators.DataRequired()]),
    'document_type': StringField('Document_type', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=31)]),
    'document_name': StringField('Document_name', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=200)]),
    'file_path': StringField('File_path', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=500)]),
    'upload_date' : DateTimeField('Upload_date', widget=DateTimePickerWidget(), validators=[validators.DataRequired()]),
    'status': StringField('Status', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=20)]),
    'next_status': StringField('Next_status', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=20)]),
    'review_notes': StringField('Review_notes', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'review_date' : DateTimeField('Review_date', widget=DateTimePickerWidget(), validators=[validators.DataRequired()]),
    'organization_fk': QuerySelectField('Organization_fk', query_factory=lambda: db.session.query(Organization), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class EventView(ModelView):
    datamodel = SQLAInterface('Event')
    list_title = 'Event List'
    show_title = 'Event Details'
    add_title = 'Add Event'
    edit_title = 'Edit Event'
    list_columns = ['id', 'organization_id_fk', 'name', 'description', 'start_datetime', 'end_datetime', 'location', 'is_virtual', 'max_participants']
    show_columns = ['id', 'organization_id_fk', 'name', 'description', 'start_datetime', 'end_datetime', 'location', 'is_virtual', 'max_participants']
    add_columns = ['organization_id_fk', 'name', 'description', 'start_datetime', 'end_datetime', 'location', 'is_virtual', 'max_participants']
    edit_columns = ['organization_id_fk', 'name', 'description', 'start_datetime', 'end_datetime', 'location', 'is_virtual', 'max_participants']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['name', 'description', 'location']
    label_columns = {'id': 'Id', 'organization_id_fk': 'Organization Id Fk', 'name': 'Name', 'description': 'Description', 'start_datetime': 'Start Datetime', 'end_datetime': 'End Datetime', 'location': 'Location', 'is_virtual': 'Is Virtual', 'max_participants': 'Max Participants'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id_fk', 'name', 'description', 'start_datetime', 'end_datetime', 'location', 'is_virtual', 'max_participants']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id_fk', 'name', 'description', 'start_datetime', 'end_datetime', 'location', 'is_virtual', 'max_participants']})
    ]
    

    add_fieldsets = [
        ('Add Event', {'fields': ['organization_id_fk', 'name', 'description', 'start_datetime', 'end_datetime', 'location', 'is_virtual', 'max_participants']})
    ]
    

    edit_fieldsets = [
        ('Edit Event', {'fields': ['organization_id_fk', 'name', 'description', 'start_datetime', 'end_datetime', 'location', 'is_virtual', 'max_participants']})
    ]
    
    validators_columns = {'organization_id_fk': '[validators.DataRequired()]', 'name': '[validators.DataRequired(), validators.Length(max=200)]', 'location': '[validators.Length(max=200)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'organization_id_fk': 'db.session.query(Organization)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'organization_id_fk' : IntegerField('Organization_id_fk', validators=[validators.DataRequired()]),
    'name': StringField('Name', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=200)]),
    'description': StringField('Description', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'start_datetime' : DateTimeField('Start_datetime', widget=DateTimePickerWidget(), validators=[validators.DataRequired()]),
    'end_datetime' : DateTimeField('End_datetime', widget=DateTimePickerWidget(), validators=[validators.DataRequired()]),
    'location': StringField('Location', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=200)]),
    'is_virtual' : BooleanField('Is_virtual'),
    'max_participants' : IntegerField('Max_participants', validators=[validators.DataRequired()]),
    'organization_fk': QuerySelectField('Organization_fk', query_factory=lambda: db.session.query(Organization), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.name
    

class ExecutivePositionView(ModelView):
    datamodel = SQLAInterface('ExecutivePosition')
    list_title = 'Executive Position List'
    show_title = 'Executive Position Details'
    add_title = 'Add Executive Position'
    edit_title = 'Edit Executive Position'
    list_columns = ['id', 'organization_id_fk', 'person_id_fk', 'title', 'start_date', 'end_date']
    show_columns = ['id', 'organization_id_fk', 'person_id_fk', 'title', 'start_date', 'end_date']
    add_columns = ['organization_id_fk', 'person_id_fk', 'title', 'start_date', 'end_date']
    edit_columns = ['organization_id_fk', 'person_id_fk', 'title', 'start_date', 'end_date']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['title']
    label_columns = {'id': 'Id', 'organization_id_fk': 'Organization Id Fk', 'person_id_fk': 'Person Id Fk', 'title': 'Title', 'start_date': 'Start Date', 'end_date': 'End Date'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id_fk', 'person_id_fk', 'title', 'start_date', 'end_date']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id_fk', 'person_id_fk', 'title', 'start_date', 'end_date']})
    ]
    

    add_fieldsets = [
        ('Add Executive Position', {'fields': ['organization_id_fk', 'person_id_fk', 'title', 'start_date', 'end_date']})
    ]
    

    edit_fieldsets = [
        ('Edit Executive Position', {'fields': ['organization_id_fk', 'person_id_fk', 'title', 'start_date', 'end_date']})
    ]
    
    validators_columns = {'organization_id_fk': '[validators.DataRequired()]', 'person_id_fk': '[validators.DataRequired()]', 'title': '[validators.DataRequired(), validators.Length(max=100)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'organization_id_fk': 'db.session.query(Organization)', 'person_id_fk': 'db.session.query(Person)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'organization_id_fk' : IntegerField('Organization_id_fk', validators=[validators.DataRequired()]),
    'person_id_fk' : IntegerField('Person_id_fk', validators=[validators.DataRequired()]),
    'title': StringField('Title', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=100)]),
    'start_date' : DateField('Start_date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'end_date' : DateField('End_date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'organization_fk': QuerySelectField('Organization_fk', query_factory=lambda: db.session.query(Organization), widget=Select2Widget(), allow_blank=True),
    'person_fk': QuerySelectField('Person_fk', query_factory=lambda: db.session.query(Person), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.title
    

class GrantView(ModelView):
    datamodel = SQLAInterface('Grant')
    list_title = 'Grant List'
    show_title = 'Grant Details'
    add_title = 'Add Grant'
    edit_title = 'Edit Grant'
    list_columns = ['id', 'donor_id_fk', 'recipient_id_fk', 'amount', 'start_date', 'end_date', 'status', 'description']
    show_columns = ['id', 'donor_id_fk', 'recipient_id_fk', 'amount', 'start_date', 'end_date', 'status', 'description']
    add_columns = ['donor_id_fk', 'recipient_id_fk', 'amount', 'start_date', 'end_date', 'status', 'description']
    edit_columns = ['donor_id_fk', 'recipient_id_fk', 'amount', 'start_date', 'end_date', 'status', 'description']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['status', 'description']
    label_columns = {'id': 'Id', 'donor_id_fk': 'Donor Id Fk', 'recipient_id_fk': 'Recipient Id Fk', 'amount': 'Amount', 'start_date': 'Start Date', 'end_date': 'End Date', 'status': 'Status', 'description': 'Description'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'donor_id_fk', 'recipient_id_fk', 'amount', 'start_date', 'end_date', 'status', 'description']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'donor_id_fk', 'recipient_id_fk', 'amount', 'start_date', 'end_date', 'status', 'description']})
    ]
    

    add_fieldsets = [
        ('Add Grant', {'fields': ['donor_id_fk', 'recipient_id_fk', 'amount', 'start_date', 'end_date', 'status', 'description']})
    ]
    

    edit_fieldsets = [
        ('Edit Grant', {'fields': ['donor_id_fk', 'recipient_id_fk', 'amount', 'start_date', 'end_date', 'status', 'description']})
    ]
    
    validators_columns = {'donor_id_fk': '[validators.DataRequired()]', 'recipient_id_fk': '[validators.DataRequired()]', 'status': '[validators.Length(max=14)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'donor_id_fk': 'db.session.query(Organization)', 'recipient_id_fk': 'db.session.query(Organization)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'donor_id_fk' : IntegerField('Donor_id_fk', validators=[validators.DataRequired()]),
    'recipient_id_fk' : IntegerField('Recipient_id_fk', validators=[validators.DataRequired()]),
    'amount' : DecimalField('Amount', validators=[validators.DataRequired()]),
    'start_date' : DateField('Start_date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'end_date' : DateField('End_date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'status': StringField('Status', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=14)]),
    'description': StringField('Description', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'donor_fk': QuerySelectField('Donor_fk', query_factory=lambda: db.session.query(Organization), widget=Select2Widget(), allow_blank=True),
    'recipient_fk': QuerySelectField('Recipient_fk', query_factory=lambda: db.session.query(Organization), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class OnboardingProgressView(ModelView):
    datamodel = SQLAInterface('OnboardingProgress')
    list_title = 'Onboarding Progress List'
    show_title = 'Onboarding Progress Details'
    add_title = 'Add Onboarding Progress'
    edit_title = 'Edit Onboarding Progress'
    list_columns = ['id', 'user_id_fk', 'organization_id_fk', 'step', 'completed_at']
    show_columns = ['id', 'user_id_fk', 'organization_id_fk', 'step', 'completed_at']
    add_columns = ['user_id_fk', 'organization_id_fk', 'step', 'completed_at']
    edit_columns = ['user_id_fk', 'organization_id_fk', 'step', 'completed_at']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = []
    label_columns = {'id': 'Id', 'user_id_fk': 'User Id Fk', 'organization_id_fk': 'Organization Id Fk', 'step': 'Step', 'completed_at': 'Completed At'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'user_id_fk', 'organization_id_fk', 'step', 'completed_at']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'user_id_fk', 'organization_id_fk', 'step', 'completed_at']})
    ]
    

    add_fieldsets = [
        ('Add Onboarding Progress', {'fields': ['user_id_fk', 'organization_id_fk', 'step', 'completed_at']})
    ]
    

    edit_fieldsets = [
        ('Edit Onboarding Progress', {'fields': ['user_id_fk', 'organization_id_fk', 'step', 'completed_at']})
    ]
    
    validators_columns = {'user_id_fk': '[validators.DataRequired()]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'organization_id_fk': 'db.session.query(Organization)', 'user_id_fk': 'db.session.query(Person)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'user_id_fk' : IntegerField('User_id_fk', validators=[validators.DataRequired()]),
    'organization_id_fk' : IntegerField('Organization_id_fk', validators=[validators.DataRequired()]),
    'step' : IntegerField('Step', validators=[validators.DataRequired()]),
    'completed_at' : DateTimeField('Completed_at', widget=DateTimePickerWidget(), validators=[validators.DataRequired()]),
    'organization_fk': QuerySelectField('Organization_fk', query_factory=lambda: db.session.query(Organization), widget=Select2Widget(), allow_blank=True),
    'user_fk': QuerySelectField('User_fk', query_factory=lambda: db.session.query(Person), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class OrganizationAwardView(ModelView):
    datamodel = SQLAInterface('OrganizationAward')
    list_title = 'Organization Award List'
    show_title = 'Organization Award Details'
    add_title = 'Add Organization Award'
    edit_title = 'Edit Organization Award'
    list_columns = ['id', 'organization_id_fk', 'name', 'awarding_body', 'date_received', 'description']
    show_columns = ['id', 'organization_id_fk', 'name', 'awarding_body', 'date_received', 'description']
    add_columns = ['organization_id_fk', 'name', 'awarding_body', 'date_received', 'description']
    edit_columns = ['organization_id_fk', 'name', 'awarding_body', 'date_received', 'description']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['name', 'awarding_body', 'description']
    label_columns = {'id': 'Id', 'organization_id_fk': 'Organization Id Fk', 'name': 'Name', 'awarding_body': 'Awarding Body', 'date_received': 'Date Received', 'description': 'Description'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id_fk', 'name', 'awarding_body', 'date_received', 'description']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id_fk', 'name', 'awarding_body', 'date_received', 'description']})
    ]
    

    add_fieldsets = [
        ('Add Organization Award', {'fields': ['organization_id_fk', 'name', 'awarding_body', 'date_received', 'description']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization Award', {'fields': ['organization_id_fk', 'name', 'awarding_body', 'date_received', 'description']})
    ]
    
    validators_columns = {'organization_id_fk': '[validators.DataRequired()]', 'name': '[validators.DataRequired(), validators.Length(max=200)]', 'awarding_body': '[validators.Length(max=200)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'organization_id_fk': 'db.session.query(Organization)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'organization_id_fk' : IntegerField('Organization_id_fk', validators=[validators.DataRequired()]),
    'name': StringField('Name', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=200)]),
    'awarding_body': StringField('Awarding_body', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=200)]),
    'date_received' : DateField('Date_received', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'description': StringField('Description', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'organization_fk': QuerySelectField('Organization_fk', query_factory=lambda: db.session.query(Organization), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.name
    

class OrganizationBadgeView(ModelView):
    datamodel = SQLAInterface('OrganizationBadge')
    list_title = 'Organization Badge List'
    show_title = 'Organization Badge Details'
    add_title = 'Add Organization Badge'
    edit_title = 'Edit Organization Badge'
    list_columns = ['id', 'organization_id_fk', 'badge_id_fk', 'date_earned']
    show_columns = ['id', 'organization_id_fk', 'badge_id_fk', 'date_earned']
    add_columns = ['organization_id_fk', 'badge_id_fk', 'date_earned']
    edit_columns = ['organization_id_fk', 'badge_id_fk', 'date_earned']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = []
    label_columns = {'id': 'Id', 'organization_id_fk': 'Organization Id Fk', 'badge_id_fk': 'Badge Id Fk', 'date_earned': 'Date Earned'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id_fk', 'badge_id_fk', 'date_earned']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id_fk', 'badge_id_fk', 'date_earned']})
    ]
    

    add_fieldsets = [
        ('Add Organization Badge', {'fields': ['organization_id_fk', 'badge_id_fk', 'date_earned']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization Badge', {'fields': ['organization_id_fk', 'badge_id_fk', 'date_earned']})
    ]
    
    validators_columns = {'organization_id_fk': '[validators.DataRequired()]', 'badge_id_fk': '[validators.DataRequired()]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'badge_id_fk': 'db.session.query(Badge)', 'organization_id_fk': 'db.session.query(Organization)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'organization_id_fk' : IntegerField('Organization_id_fk', validators=[validators.DataRequired()]),
    'badge_id_fk' : IntegerField('Badge_id_fk', validators=[validators.DataRequired()]),
    'date_earned' : DateTimeField('Date_earned', widget=DateTimePickerWidget(), validators=[validators.DataRequired()]),
    'badge_fk': QuerySelectField('Badge_fk', query_factory=lambda: db.session.query(Badge), widget=Select2Widget(), allow_blank=True),
    'organization_fk': QuerySelectField('Organization_fk', query_factory=lambda: db.session.query(Organization), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class OrganizationClimateCategoriesView(ModelView):
    datamodel = SQLAInterface('OrganizationClimateCategories')
    list_title = 'Organization Climate Categories List'
    show_title = 'Organization Climate Categories Details'
    add_title = 'Add Organization Climate Categories'
    edit_title = 'Edit Organization Climate Categories'
    list_columns = ['organization_id_fk', 'climate_category']
    show_columns = ['organization_id_fk', 'climate_category']
    add_columns = ['organization_id_fk', 'climate_category']
    edit_columns = ['organization_id_fk', 'climate_category']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['climate_category']
    label_columns = {'organization_id_fk': 'Organization Id Fk', 'climate_category': 'Climate Category'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['organization_id_fk', 'climate_category']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['organization_id_fk', 'climate_category']})
    ]
    

    add_fieldsets = [
        ('Add Organization Climate Categories', {'fields': ['organization_id_fk', 'climate_category']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization Climate Categories', {'fields': ['organization_id_fk', 'climate_category']})
    ]
    
    validators_columns = {'climate_category': '[validators.Length(max=22)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'organization_id_fk': 'db.session.query(Organization)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'organization_id_fk' : IntegerField('Organization_id_fk', validators=[validators.DataRequired()]),
    'climate_category': StringField('Climate_category', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=22)]),
    'organization_fk': QuerySelectField('Organization_fk', query_factory=lambda: db.session.query(Organization), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.organization_id_fk
    

class OrganizationContactView(ModelView):
    datamodel = SQLAInterface('OrganizationContact')
    list_title = 'Organization Contact List'
    add_title = 'Add Organization Contact'
    edit_title = 'Edit Organization Contact'
    list_columns = ['id', 'organization_id_fk', 'person_id_fk', 'org_email', 'org_phone', 'position', 'department', 'start_date', 'end_date', 'is_primary', 'status', 'notes']
    show_columns = ['id', 'organization_id_fk', 'person_id_fk', 'org_email', 'org_phone', 'position', 'department', 'start_date', 'end_date', 'is_primary', 'status', 'notes']
    search_columns = ['org_email', 'org_phone', 'position', 'department', 'status', 'notes']
    label_columns = {'id': 'Id', 'organization_id_fk': 'Organization Id Fk', 'person_id_fk': 'Person Id Fk', 'org_email': 'Org Email', 'org_phone': 'Org Phone', 'position': 'Position', 'department': 'Department', 'start_date': 'Start Date', 'end_date': 'End Date', 'is_primary': 'Is Primary', 'status': 'Status', 'notes': 'Notes'}
    description_columns = {}

    class AddForm(DynamicForm):
        step = HiddenField('step')

    add_form = AddForm

    def add_form_get(self, form):
        form.step.data = session.get('form_step', 1)
        return form

    def add_form_post(self, form):
        if form.step.data:
            session['form_step'] = int(form.step.data)
        return form

    def form_get(self, form):
        form = super().form_get(form)
        step = int(session.get('form_step', 1))
        start = (step - 1) * 5
        end = step * 5
        visible_fields = ['organization_id_fk', 'person_id_fk', 'org_email', 'org_phone', 'position', 'department', 'start_date', 'end_date', 'is_primary', 'status', 'notes'][start:end]
        for field in form._fields:
            if field not in visible_fields and field != 'step':
                form._fields[field].render_kw = {'style': 'display:none;'}
        return form

    def form_post(self, form):
        step = int(form.step.data)
        if step < 3:
            session['form_step'] = step + 1
            return self.update_redirect(), False  # Keep user on the same form
        else:
            session.pop('form_step', None)
            return super().form_post(form)

    add_fieldsets = [    ('Step 1', {'fields': ['step'] + ['organization_id_fk', 'person_id_fk', 'org_email', 'org_phone', 'position'], 'expanded': True}),     ('Step 2', {'fields': ['step'] + ['department', 'start_date', 'end_date', 'is_primary', 'status'], 'expanded': True}),     ('Step 3', {'fields': ['step'] + ['notes'], 'expanded': True})]
    edit_fieldsets = add_fieldsets


    def __repr__(self):
        return self.id
    

class OrganizationDocumentsView(ModelView):
    datamodel = SQLAInterface('OrganizationDocuments')
    list_title = 'Organization Documents List'
    show_title = 'Organization Documents Details'
    add_title = 'Add Organization Documents'
    edit_title = 'Edit Organization Documents'
    list_columns = ['id', 'organization_id', 'document_type', 'document_name', 'document_path', 'upload_date', 'document_summary']
    show_columns = ['id', 'organization_id', 'document_type', 'document_name', 'document_path', 'upload_date', 'document_summary']
    add_columns = ['organization_id', 'document_type', 'document_name', 'document_path', 'upload_date', 'document_summary']
    edit_columns = ['organization_id', 'document_type', 'document_name', 'document_path', 'upload_date', 'document_summary']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['document_type', 'document_name', 'document_path', 'document_summary']
    label_columns = {'id': 'Id', 'organization_id': 'Organization Id', 'document_type': 'Document Type', 'document_name': 'Document Name', 'document_path': 'Document Path', 'upload_date': 'Upload Date', 'document_summary': 'Document Summary'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id', 'document_type', 'document_name', 'document_path', 'upload_date', 'document_summary']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id', 'document_type', 'document_name', 'document_path', 'upload_date', 'document_summary']})
    ]
    

    add_fieldsets = [
        ('Add Organization Documents', {'fields': ['organization_id', 'document_type', 'document_name', 'document_path', 'upload_date', 'document_summary']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization Documents', {'fields': ['organization_id', 'document_type', 'document_name', 'document_path', 'upload_date', 'document_summary']})
    ]
    
    validators_columns = {'organization_id': '[validators.DataRequired()]', 'document_type': '[validators.DataRequired(), validators.Length(max=31)]', 'document_name': '[validators.DataRequired(), validators.Length(max=150)]', 'document_path': '[validators.DataRequired(), validators.Length(max=255)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'organization_id': 'db.session.query(Organization)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'organization_id' : IntegerField('Organization_id', validators=[validators.DataRequired()]),
    'document_type': StringField('Document_type', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=31)]),
    'document_name': StringField('Document_name', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=150)]),
    'document_path': StringField('Document_path', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=255)]),
    'upload_date' : DateTimeField('Upload_date', widget=DateTimePickerWidget(), validators=[validators.DataRequired()]),
    'document_summary': StringField('Document_summary', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'organization': QuerySelectField('Organization', query_factory=lambda: db.session.query(Organization), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class OrganizationHierarchyView(ModelView):
    datamodel = SQLAInterface('OrganizationHierarchy')
    list_title = 'Organization Hierarchy List'
    show_title = 'Organization Hierarchy Details'
    add_title = 'Add Organization Hierarchy'
    edit_title = 'Edit Organization Hierarchy'
    list_columns = ['id', 'parent_org_id_fk', 'child_org_id_fk', 'relationship_type']
    show_columns = ['id', 'parent_org_id_fk', 'child_org_id_fk', 'relationship_type']
    add_columns = ['parent_org_id_fk', 'child_org_id_fk', 'relationship_type']
    edit_columns = ['parent_org_id_fk', 'child_org_id_fk', 'relationship_type']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['relationship_type']
    label_columns = {'id': 'Id', 'parent_org_id_fk': 'Parent Org Id Fk', 'child_org_id_fk': 'Child Org Id Fk', 'relationship_type': 'Relationship Type'}
    description_columns = {'relationship_type': 'e.g., parent, subsidiary, department'}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'parent_org_id_fk', 'child_org_id_fk', 'relationship_type']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'parent_org_id_fk', 'child_org_id_fk', 'relationship_type']})
    ]
    

    add_fieldsets = [
        ('Add Organization Hierarchy', {'fields': ['parent_org_id_fk', 'child_org_id_fk', 'relationship_type']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization Hierarchy', {'fields': ['parent_org_id_fk', 'child_org_id_fk', 'relationship_type']})
    ]
    
    validators_columns = {'relationship_type': '[validators.Length(max=15)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'child_org_id_fk': 'db.session.query(Organization)', 'parent_org_id_fk': 'db.session.query(Organization)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'parent_org_id_fk' : IntegerField('Parent_org_id_fk', validators=[validators.DataRequired()]),
    'child_org_id_fk' : IntegerField('Child_org_id_fk', validators=[validators.DataRequired()]),
    'relationship_type': StringField('Relationship_type', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=15)]),
    'child_org_fk': QuerySelectField('Child_org_fk', query_factory=lambda: db.session.query(Organization), widget=Select2Widget(), allow_blank=True),
    'parent_org_fk': QuerySelectField('Parent_org_fk', query_factory=lambda: db.session.query(Organization), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class OrganizationProfileView(ModelView):
    datamodel = SQLAInterface('OrganizationProfile')
    list_title = 'Organization Profile List'
    add_title = 'Add Organization Profile'
    edit_title = 'Edit Organization Profile'
    list_columns = ['id', 'organization_id_fk', 'funding_focus_areas', 'average_grant_size', 'grant_making_process', 'funding_restrictions', 'focus_areas', 'target_beneficiaries', 'geographic_reach', 'years_of_operation', 'total_beneficiaries_last_year', 'annual_budget', 'num_employees', 'num_volunteers', 'last_year_revenue', 'last_year_expenditure']
    show_columns = ['id', 'organization_id_fk', 'funding_focus_areas', 'average_grant_size', 'grant_making_process', 'funding_restrictions', 'focus_areas', 'target_beneficiaries', 'geographic_reach', 'years_of_operation', 'total_beneficiaries_last_year', 'annual_budget', 'num_employees', 'num_volunteers', 'last_year_revenue', 'last_year_expenditure']
    search_columns = ['funding_focus_areas', 'grant_making_process', 'funding_restrictions', 'focus_areas', 'target_beneficiaries', 'geographic_reach']
    label_columns = {'id': 'Id', 'organization_id_fk': 'Organization Id Fk', 'funding_focus_areas': 'Funding Focus Areas', 'average_grant_size': 'Average Grant Size', 'grant_making_process': 'Grant Making Process', 'funding_restrictions': 'Funding Restrictions', 'focus_areas': 'Focus Areas', 'target_beneficiaries': 'Target Beneficiaries', 'geographic_reach': 'Geographic Reach', 'years_of_operation': 'Years Of Operation', 'total_beneficiaries_last_year': 'Total Beneficiaries Last Year', 'annual_budget': 'Annual Budget', 'num_employees': 'Num Employees', 'num_volunteers': 'Num Volunteers', 'last_year_revenue': 'Last Year Revenue', 'last_year_expenditure': 'Last Year Expenditure'}
    description_columns = {}

    class AddForm(DynamicForm):
        step = HiddenField('step')

    add_form = AddForm

    def add_form_get(self, form):
        form.step.data = session.get('form_step', 1)
        return form

    def add_form_post(self, form):
        if form.step.data:
            session['form_step'] = int(form.step.data)
        return form

    def form_get(self, form):
        form = super().form_get(form)
        step = int(session.get('form_step', 1))
        start = (step - 1) * 5
        end = step * 5
        visible_fields = ['organization_id_fk', 'funding_focus_areas', 'average_grant_size', 'grant_making_process', 'funding_restrictions', 'focus_areas', 'target_beneficiaries', 'geographic_reach', 'years_of_operation', 'total_beneficiaries_last_year', 'annual_budget', 'num_employees', 'num_volunteers', 'last_year_revenue', 'last_year_expenditure'][start:end]
        for field in form._fields:
            if field not in visible_fields and field != 'step':
                form._fields[field].render_kw = {'style': 'display:none;'}
        return form

    def form_post(self, form):
        step = int(form.step.data)
        if step < 3:
            session['form_step'] = step + 1
            return self.update_redirect(), False  # Keep user on the same form
        else:
            session.pop('form_step', None)
            return super().form_post(form)

    add_fieldsets = [    ('Step 1', {'fields': ['step'] + ['organization_id_fk', 'funding_focus_areas', 'average_grant_size', 'grant_making_process', 'funding_restrictions'], 'expanded': True}),     ('Step 2', {'fields': ['step'] + ['focus_areas', 'target_beneficiaries', 'geographic_reach', 'years_of_operation', 'total_beneficiaries_last_year'], 'expanded': True}),     ('Step 3', {'fields': ['step'] + ['annual_budget', 'num_employees', 'num_volunteers', 'last_year_revenue', 'last_year_expenditure'], 'expanded': True})]
    edit_fieldsets = add_fieldsets


    def __repr__(self):
        return self.id
    

class OrganizationProgramsView(ModelView):
    datamodel = SQLAInterface('OrganizationPrograms')
    list_title = 'Organization Programs List'
    show_title = 'Organization Programs Details'
    add_title = 'Add Organization Programs'
    edit_title = 'Edit Organization Programs'
    list_columns = ['id', 'organization_id', 'program_name', 'program_description', 'start_date', 'end_date', 'budget', 'impact_assessment']
    show_columns = ['id', 'organization_id', 'program_name', 'program_description', 'start_date', 'end_date', 'budget', 'impact_assessment']
    add_columns = ['organization_id', 'program_name', 'program_description', 'start_date', 'end_date', 'budget', 'impact_assessment']
    edit_columns = ['organization_id', 'program_name', 'program_description', 'start_date', 'end_date', 'budget', 'impact_assessment']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['program_name', 'program_description', 'impact_assessment']
    label_columns = {'id': 'Id', 'organization_id': 'Organization Id', 'program_name': 'Program Name', 'program_description': 'Program Description', 'start_date': 'Start Date', 'end_date': 'End Date', 'budget': 'Budget', 'impact_assessment': 'Impact Assessment'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id', 'program_name', 'program_description', 'start_date', 'end_date', 'budget', 'impact_assessment']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id', 'program_name', 'program_description', 'start_date', 'end_date', 'budget', 'impact_assessment']})
    ]
    

    add_fieldsets = [
        ('Add Organization Programs', {'fields': ['organization_id', 'program_name', 'program_description', 'start_date', 'end_date', 'budget', 'impact_assessment']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization Programs', {'fields': ['organization_id', 'program_name', 'program_description', 'start_date', 'end_date', 'budget', 'impact_assessment']})
    ]
    
    validators_columns = {'organization_id': '[validators.DataRequired()]', 'program_name': '[validators.DataRequired(), validators.Length(max=150)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'organization_id': 'db.session.query(Organization)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'organization_id' : IntegerField('Organization_id', validators=[validators.DataRequired()]),
    'program_name': StringField('Program_name', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=150)]),
    'program_description': StringField('Program_description', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'start_date' : DateField('Start_date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'end_date' : DateField('End_date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'budget' : DecimalField('Budget', validators=[validators.DataRequired()]),
    'impact_assessment': StringField('Impact_assessment', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'organization': QuerySelectField('Organization', query_factory=lambda: db.session.query(Organization), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class OrganizationSdgsView(ModelView):
    datamodel = SQLAInterface('OrganizationSdgs')
    list_title = 'Organization Sdgs List'
    show_title = 'Organization Sdgs Details'
    add_title = 'Add Organization Sdgs'
    edit_title = 'Edit Organization Sdgs'
    list_columns = ['organization_id_fk', 'sdg']
    show_columns = ['organization_id_fk', 'sdg']
    add_columns = ['organization_id_fk', 'sdg']
    edit_columns = ['organization_id_fk', 'sdg']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['sdg']
    label_columns = {'organization_id_fk': 'Organization Id Fk', 'sdg': 'Sdg'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['organization_id_fk', 'sdg']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['organization_id_fk', 'sdg']})
    ]
    

    add_fieldsets = [
        ('Add Organization Sdgs', {'fields': ['organization_id_fk', 'sdg']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization Sdgs', {'fields': ['organization_id_fk', 'sdg']})
    ]
    
    validators_columns = {'sdg': '[validators.Length(max=38)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'organization_id_fk': 'db.session.query(Organization)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'organization_id_fk' : IntegerField('Organization_id_fk', validators=[validators.DataRequired()]),
    'sdg': StringField('Sdg', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=38)]),
    'organization_fk': QuerySelectField('Organization_fk', query_factory=lambda: db.session.query(Organization), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.organization_id_fk
    

class OrganizationTagView(ModelView):
    datamodel = SQLAInterface('OrganizationTag')
    list_title = 'Organization Tag List'
    show_title = 'Organization Tag Details'
    add_title = 'Add Organization Tag'
    edit_title = 'Edit Organization Tag'
    list_columns = ['id', 'organization_id_fk', 'tag_id_fk']
    show_columns = ['id', 'organization_id_fk', 'tag_id_fk']
    add_columns = ['organization_id_fk', 'tag_id_fk']
    edit_columns = ['organization_id_fk', 'tag_id_fk']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = []
    label_columns = {'id': 'Id', 'organization_id_fk': 'Organization Id Fk', 'tag_id_fk': 'Tag Id Fk'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id_fk', 'tag_id_fk']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id_fk', 'tag_id_fk']})
    ]
    

    add_fieldsets = [
        ('Add Organization Tag', {'fields': ['organization_id_fk', 'tag_id_fk']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization Tag', {'fields': ['organization_id_fk', 'tag_id_fk']})
    ]
    
    validators_columns = {'organization_id_fk': '[validators.DataRequired()]', 'tag_id_fk': '[validators.DataRequired()]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'organization_id_fk': 'db.session.query(Organization)', 'tag_id_fk': 'db.session.query(Tag)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'organization_id_fk' : IntegerField('Organization_id_fk', validators=[validators.DataRequired()]),
    'tag_id_fk' : IntegerField('Tag_id_fk', validators=[validators.DataRequired()]),
    'organization_fk': QuerySelectField('Organization_fk', query_factory=lambda: db.session.query(Organization), widget=Select2Widget(), allow_blank=True),
    'tag_fk': QuerySelectField('Tag_fk', query_factory=lambda: db.session.query(Tag), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class OrganizationVerificationView(ModelView):
    datamodel = SQLAInterface('OrganizationVerification')
    list_title = 'Organization Verification List'
    show_title = 'Organization Verification Details'
    add_title = 'Add Organization Verification'
    edit_title = 'Edit Organization Verification'
    list_columns = ['id', 'organization_id_fk', 'registration_number', 'registration_date', 'registering_authority', 'registration_expiry', 'last_verification_date', 'verification_status', 'verification_notes']
    show_columns = ['id', 'organization_id_fk', 'registration_number', 'registration_date', 'registering_authority', 'registration_expiry', 'last_verification_date', 'verification_status', 'verification_notes']
    add_columns = ['organization_id_fk', 'registration_number', 'registration_date', 'registering_authority', 'registration_expiry', 'last_verification_date', 'verification_status', 'verification_notes']
    edit_columns = ['organization_id_fk', 'registration_number', 'registration_date', 'registering_authority', 'registration_expiry', 'last_verification_date', 'verification_status', 'verification_notes']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['registration_number', 'registering_authority', 'verification_status', 'verification_notes']
    label_columns = {'id': 'Id', 'organization_id_fk': 'Organization Id Fk', 'registration_number': 'Registration Number', 'registration_date': 'Registration Date', 'registering_authority': 'Registering Authority', 'registration_expiry': 'Registration Expiry', 'last_verification_date': 'Last Verification Date', 'verification_status': 'Verification Status', 'verification_notes': 'Verification Notes'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id_fk', 'registration_number', 'registration_date', 'registering_authority', 'registration_expiry', 'last_verification_date', 'verification_status', 'verification_notes']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id_fk', 'registration_number', 'registration_date', 'registering_authority', 'registration_expiry', 'last_verification_date', 'verification_status', 'verification_notes']})
    ]
    

    add_fieldsets = [
        ('Add Organization Verification', {'fields': ['organization_id_fk', 'registration_number', 'registration_date', 'registering_authority', 'registration_expiry', 'last_verification_date', 'verification_status', 'verification_notes']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization Verification', {'fields': ['organization_id_fk', 'registration_number', 'registration_date', 'registering_authority', 'registration_expiry', 'last_verification_date', 'verification_status', 'verification_notes']})
    ]
    
    validators_columns = {'organization_id_fk': '[validators.DataRequired()]', 'registration_number': '[validators.Length(max=100)]', 'registering_authority': '[validators.Length(max=200)]', 'verification_status': '[validators.Length(max=19)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'organization_id_fk': 'db.session.query(Organization)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'organization_id_fk' : IntegerField('Organization_id_fk', validators=[validators.DataRequired()]),
    'registration_number': StringField('Registration_number', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=100)]),
    'registration_date' : DateField('Registration_date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'registering_authority': StringField('Registering_authority', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=200)]),
    'registration_expiry' : DateField('Registration_expiry', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'last_verification_date' : DateField('Last_verification_date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'verification_status': StringField('Verification_status', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=19)]),
    'verification_notes': StringField('Verification_notes', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'organization_fk': QuerySelectField('Organization_fk', query_factory=lambda: db.session.query(Organization), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class PersonOrganizationClaimView(ModelView):
    datamodel = SQLAInterface('PersonOrganizationClaim')
    list_title = 'Person Organization Claim List'
    show_title = 'Person Organization Claim Details'
    add_title = 'Add Person Organization Claim'
    edit_title = 'Edit Person Organization Claim'
    list_columns = ['id', 'person_id', 'organization_id', 'claim_type', 'status', 'claim_date', 'review_date']
    show_columns = ['id', 'person_id', 'organization_id', 'claim_type', 'status', 'claim_date', 'review_date']
    add_columns = ['person_id', 'organization_id', 'claim_type', 'status', 'claim_date', 'review_date']
    edit_columns = ['person_id', 'organization_id', 'claim_type', 'status', 'claim_date', 'review_date']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['claim_type', 'status']
    label_columns = {'id': 'Id', 'person_id': 'Person Id', 'organization_id': 'Organization Id', 'claim_type': 'Claim Type', 'status': 'Status', 'claim_date': 'Claim Date', 'review_date': 'Review Date'}
    description_columns = {'claim_type': 'e.g., staff, volunteer, board_member', 'status': 'Pending, Approved, Rejected'}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id', 'organization_id', 'claim_type', 'status', 'claim_date', 'review_date']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id', 'organization_id', 'claim_type', 'status', 'claim_date', 'review_date']})
    ]
    

    add_fieldsets = [
        ('Add Person Organization Claim', {'fields': ['person_id', 'organization_id', 'claim_type', 'status', 'claim_date', 'review_date']})
    ]
    

    edit_fieldsets = [
        ('Edit Person Organization Claim', {'fields': ['person_id', 'organization_id', 'claim_type', 'status', 'claim_date', 'review_date']})
    ]
    
    validators_columns = {'person_id': '[validators.DataRequired()]', 'organization_id': '[validators.DataRequired()]', 'claim_type': '[validators.Length(max=17)]', 'status': '[validators.Length(max=14)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'organization_id': 'db.session.query(Organization)', 'person_id': 'db.session.query(Person)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'person_id' : IntegerField('Person_id', validators=[validators.DataRequired()]),
    'organization_id' : IntegerField('Organization_id', validators=[validators.DataRequired()]),
    'claim_type': StringField('Claim_type', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=17)]),
    'status': StringField('Status', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=14)]),
    'claim_date' : DateTimeField('Claim_date', widget=DateTimePickerWidget(), validators=[validators.DataRequired()]),
    'review_date' : DateTimeField('Review_date', widget=DateTimePickerWidget(), validators=[validators.DataRequired()]),
    'organization': QuerySelectField('Organization', query_factory=lambda: db.session.query(Organization), widget=Select2Widget(), allow_blank=True),
    'person': QuerySelectField('Person', query_factory=lambda: db.session.query(Person), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class PersonSkillView(ModelView):
    datamodel = SQLAInterface('PersonSkill')
    list_title = 'Person Skill List'
    show_title = 'Person Skill Details'
    add_title = 'Add Person Skill'
    edit_title = 'Edit Person Skill'
    list_columns = ['id', 'person_id_fk', 'skill_id_fk', 'proficiency_level', 'endorsements']
    show_columns = ['id', 'person_id_fk', 'skill_id_fk', 'proficiency_level', 'endorsements']
    add_columns = ['person_id_fk', 'skill_id_fk', 'proficiency_level', 'endorsements']
    edit_columns = ['person_id_fk', 'skill_id_fk', 'proficiency_level', 'endorsements']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = []
    label_columns = {'id': 'Id', 'person_id_fk': 'Person Id Fk', 'skill_id_fk': 'Skill Id Fk', 'proficiency_level': 'Proficiency Level', 'endorsements': 'Endorsements'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'skill_id_fk', 'proficiency_level', 'endorsements']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'skill_id_fk', 'proficiency_level', 'endorsements']})
    ]
    

    add_fieldsets = [
        ('Add Person Skill', {'fields': ['person_id_fk', 'skill_id_fk', 'proficiency_level', 'endorsements']})
    ]
    

    edit_fieldsets = [
        ('Edit Person Skill', {'fields': ['person_id_fk', 'skill_id_fk', 'proficiency_level', 'endorsements']})
    ]
    
    validators_columns = {'person_id_fk': '[validators.DataRequired()]', 'skill_id_fk': '[validators.DataRequired()]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'person_id_fk': 'db.session.query(Person)', 'skill_id_fk': 'db.session.query(Skill)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'person_id_fk' : IntegerField('Person_id_fk', validators=[validators.DataRequired()]),
    'skill_id_fk' : IntegerField('Skill_id_fk', validators=[validators.DataRequired()]),
    'proficiency_level' : IntegerField('Proficiency_level', validators=[validators.DataRequired()]),
    'endorsements' : IntegerField('Endorsements', validators=[validators.DataRequired()]),
    'person_fk': QuerySelectField('Person_fk', query_factory=lambda: db.session.query(Person), widget=Select2Widget(), allow_blank=True),
    'skill_fk': QuerySelectField('Skill_fk', query_factory=lambda: db.session.query(Skill), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class ProjectView(ModelView):
    datamodel = SQLAInterface('Project')
    list_title = 'Project List'
    show_title = 'Project Details'
    add_title = 'Add Project'
    edit_title = 'Edit Project'
    list_columns = ['id', 'organization_id_fk', 'name', 'description', 'start_date', 'end_date', 'budget', 'status', 'beneficiaries', 'outcomes']
    show_columns = ['id', 'organization_id_fk', 'name', 'description', 'start_date', 'end_date', 'budget', 'status', 'beneficiaries', 'outcomes']
    add_columns = ['organization_id_fk', 'name', 'description', 'start_date', 'end_date', 'budget', 'status', 'beneficiaries', 'outcomes']
    edit_columns = ['organization_id_fk', 'name', 'description', 'start_date', 'end_date', 'budget', 'status', 'beneficiaries', 'outcomes']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['name', 'description', 'status', 'outcomes']
    label_columns = {'id': 'Id', 'organization_id_fk': 'Organization Id Fk', 'name': 'Name', 'description': 'Description', 'start_date': 'Start Date', 'end_date': 'End Date', 'budget': 'Budget', 'status': 'Status', 'beneficiaries': 'Beneficiaries', 'outcomes': 'Outcomes'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id_fk', 'name', 'description', 'start_date', 'end_date', 'budget', 'status', 'beneficiaries', 'outcomes']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id_fk', 'name', 'description', 'start_date', 'end_date', 'budget', 'status', 'beneficiaries', 'outcomes']})
    ]
    

    add_fieldsets = [
        ('Add Project', {'fields': ['organization_id_fk', 'name', 'description', 'start_date', 'end_date', 'budget', 'status', 'beneficiaries', 'outcomes']})
    ]
    

    edit_fieldsets = [
        ('Edit Project', {'fields': ['organization_id_fk', 'name', 'description', 'start_date', 'end_date', 'budget', 'status', 'beneficiaries', 'outcomes']})
    ]
    
    validators_columns = {'organization_id_fk': '[validators.DataRequired()]', 'name': '[validators.DataRequired(), validators.Length(max=200)]', 'status': '[validators.Length(max=11)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'organization_id_fk': 'db.session.query(Organization)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'organization_id_fk' : IntegerField('Organization_id_fk', validators=[validators.DataRequired()]),
    'name': StringField('Name', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=200)]),
    'description': StringField('Description', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'start_date' : DateField('Start_date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'end_date' : DateField('End_date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'budget' : DecimalField('Budget', validators=[validators.DataRequired()]),
    'status': StringField('Status', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=11)]),
    'beneficiaries' : IntegerField('Beneficiaries', validators=[validators.DataRequired()]),
    'outcomes': StringField('Outcomes', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'organization_fk': QuerySelectField('Organization_fk', query_factory=lambda: db.session.query(Organization), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.name
    

class ReportView(ModelView):
    datamodel = SQLAInterface('Report')
    list_title = 'Report List'
    show_title = 'Report Details'
    add_title = 'Add Report'
    edit_title = 'Edit Report'
    list_columns = ['id', 'organization_id_fk', 'title', 'description', 'file_path', 'created_date', 'report_type']
    show_columns = ['id', 'organization_id_fk', 'title', 'description', 'file_path', 'created_date', 'report_type']
    add_columns = ['organization_id_fk', 'title', 'description', 'file_path', 'created_date', 'report_type']
    edit_columns = ['organization_id_fk', 'title', 'description', 'file_path', 'created_date', 'report_type']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['title', 'description', 'file_path', 'report_type']
    label_columns = {'id': 'Id', 'organization_id_fk': 'Organization Id Fk', 'title': 'Title', 'description': 'Description', 'file_path': 'File Path', 'created_date': 'Created Date', 'report_type': 'Report Type'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id_fk', 'title', 'description', 'file_path', 'created_date', 'report_type']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id_fk', 'title', 'description', 'file_path', 'created_date', 'report_type']})
    ]
    

    add_fieldsets = [
        ('Add Report', {'fields': ['organization_id_fk', 'title', 'description', 'file_path', 'created_date', 'report_type']})
    ]
    

    edit_fieldsets = [
        ('Edit Report', {'fields': ['organization_id_fk', 'title', 'description', 'file_path', 'created_date', 'report_type']})
    ]
    
    validators_columns = {'organization_id_fk': '[validators.DataRequired()]', 'title': '[validators.DataRequired(), validators.Length(max=200)]', 'file_path': '[validators.Length(max=500)]', 'report_type': '[validators.Length(max=50)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'organization_id_fk': 'db.session.query(Organization)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'organization_id_fk' : IntegerField('Organization_id_fk', validators=[validators.DataRequired()]),
    'title': StringField('Title', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=200)]),
    'description': StringField('Description', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'file_path': StringField('File_path', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=500)]),
    'created_date' : DateTimeField('Created_date', widget=DateTimePickerWidget(), validators=[validators.DataRequired()]),
    'report_type': StringField('Report_type', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=50)]),
    'organization_fk': QuerySelectField('Organization_fk', query_factory=lambda: db.session.query(Organization), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.title
    

class SocialMediaProfileView(ModelView):
    datamodel = SQLAInterface('SocialMediaProfile')
    list_title = 'Social Media Profile List'
    show_title = 'Social Media Profile Details'
    add_title = 'Add Social Media Profile'
    edit_title = 'Edit Social Media Profile'
    list_columns = ['id', 'person_id_fk', 'org_id_fk', 'platform', 'profile_id', 'access_token', 'refresh_token', 'token_expiry']
    show_columns = ['id', 'person_id_fk', 'org_id_fk', 'platform', 'profile_id', 'access_token', 'refresh_token', 'token_expiry']
    add_columns = ['person_id_fk', 'org_id_fk', 'platform', 'profile_id', 'access_token', 'refresh_token', 'token_expiry']
    edit_columns = ['person_id_fk', 'org_id_fk', 'platform', 'profile_id', 'access_token', 'refresh_token', 'token_expiry']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['platform', 'profile_id', 'access_token', 'refresh_token']
    label_columns = {'id': 'Id', 'person_id_fk': 'Person Id Fk', 'org_id_fk': 'Org Id Fk', 'platform': 'Platform', 'profile_id': 'Profile Id', 'access_token': 'Access Token', 'refresh_token': 'Refresh Token', 'token_expiry': 'Token Expiry'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'org_id_fk', 'platform', 'profile_id', 'access_token', 'refresh_token', 'token_expiry']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'org_id_fk', 'platform', 'profile_id', 'access_token', 'refresh_token', 'token_expiry']})
    ]
    

    add_fieldsets = [
        ('Add Social Media Profile', {'fields': ['person_id_fk', 'org_id_fk', 'platform', 'profile_id', 'access_token', 'refresh_token', 'token_expiry']})
    ]
    

    edit_fieldsets = [
        ('Edit Social Media Profile', {'fields': ['person_id_fk', 'org_id_fk', 'platform', 'profile_id', 'access_token', 'refresh_token', 'token_expiry']})
    ]
    
    validators_columns = {'platform': '[validators.DataRequired(), validators.Length(max=9)]', 'profile_id': '[validators.DataRequired(), validators.Length(max=100)]', 'access_token': '[validators.Length(max=500)]', 'refresh_token': '[validators.Length(max=500)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'org_id_fk': 'db.session.query(Organization)', 'person_id_fk': 'db.session.query(Person)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'person_id_fk' : IntegerField('Person_id_fk', validators=[validators.DataRequired()]),
    'org_id_fk' : IntegerField('Org_id_fk', validators=[validators.DataRequired()]),
    'platform': StringField('Platform', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=9)]),
    'profile_id': StringField('Profile_id', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=100)]),
    'access_token': StringField('Access_token', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=500)]),
    'refresh_token': StringField('Refresh_token', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=500)]),
    'token_expiry' : DateTimeField('Token_expiry', widget=DateTimePickerWidget(), validators=[validators.DataRequired()]),
    'org_fk': QuerySelectField('Org_fk', query_factory=lambda: db.session.query(Organization), widget=Select2Widget(), allow_blank=True),
    'person_fk': QuerySelectField('Person_fk', query_factory=lambda: db.session.query(Person), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class TrainingView(ModelView):
    datamodel = SQLAInterface('Training')
    list_title = 'Training List'
    show_title = 'Training Details'
    add_title = 'Add Training'
    edit_title = 'Edit Training'
    list_columns = ['id', 'offering_org_id_fk', 'name', 'description', 'start_date', 'end_date', 'is_certified']
    show_columns = ['id', 'offering_org_id_fk', 'name', 'description', 'start_date', 'end_date', 'is_certified']
    add_columns = ['offering_org_id_fk', 'name', 'description', 'start_date', 'end_date', 'is_certified']
    edit_columns = ['offering_org_id_fk', 'name', 'description', 'start_date', 'end_date', 'is_certified']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['name', 'description']
    label_columns = {'id': 'Id', 'offering_org_id_fk': 'Offering Org Id Fk', 'name': 'Name', 'description': 'Description', 'start_date': 'Start Date', 'end_date': 'End Date', 'is_certified': 'Is Certified'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'offering_org_id_fk', 'name', 'description', 'start_date', 'end_date', 'is_certified']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'offering_org_id_fk', 'name', 'description', 'start_date', 'end_date', 'is_certified']})
    ]
    

    add_fieldsets = [
        ('Add Training', {'fields': ['offering_org_id_fk', 'name', 'description', 'start_date', 'end_date', 'is_certified']})
    ]
    

    edit_fieldsets = [
        ('Edit Training', {'fields': ['offering_org_id_fk', 'name', 'description', 'start_date', 'end_date', 'is_certified']})
    ]
    
    validators_columns = {'offering_org_id_fk': '[validators.DataRequired()]', 'name': '[validators.DataRequired(), validators.Length(max=200)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'offering_org_id_fk': 'db.session.query(Organization)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'offering_org_id_fk' : IntegerField('Offering_org_id_fk', validators=[validators.DataRequired()]),
    'name': StringField('Name', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=200)]),
    'description': StringField('Description', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'start_date' : DateField('Start_date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'end_date' : DateField('End_date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'is_certified' : BooleanField('Is_certified'),
    'offering_org_fk': QuerySelectField('Offering_org_fk', query_factory=lambda: db.session.query(Organization), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.name
    

class UserChallengeView(ModelView):
    datamodel = SQLAInterface('UserChallenge')
    list_title = 'User Challenge List'
    show_title = 'User Challenge Details'
    add_title = 'Add User Challenge'
    edit_title = 'Edit User Challenge'
    list_columns = ['id', 'person_id_fk', 'challenge_id_fk', 'completed', 'completion_date']
    show_columns = ['id', 'person_id_fk', 'challenge_id_fk', 'completed', 'completion_date']
    add_columns = ['person_id_fk', 'challenge_id_fk', 'completed', 'completion_date']
    edit_columns = ['person_id_fk', 'challenge_id_fk', 'completed', 'completion_date']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = []
    label_columns = {'id': 'Id', 'person_id_fk': 'Person Id Fk', 'challenge_id_fk': 'Challenge Id Fk', 'completed': 'Completed', 'completion_date': 'Completion Date'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'challenge_id_fk', 'completed', 'completion_date']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'challenge_id_fk', 'completed', 'completion_date']})
    ]
    

    add_fieldsets = [
        ('Add User Challenge', {'fields': ['person_id_fk', 'challenge_id_fk', 'completed', 'completion_date']})
    ]
    

    edit_fieldsets = [
        ('Edit User Challenge', {'fields': ['person_id_fk', 'challenge_id_fk', 'completed', 'completion_date']})
    ]
    
    validators_columns = {'person_id_fk': '[validators.DataRequired()]', 'challenge_id_fk': '[validators.DataRequired()]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'person_id_fk': 'db.session.query(Person)', 'challenge_id_fk': 'db.session.query(GamificationChallenge)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'person_id_fk' : IntegerField('Person_id_fk', validators=[validators.DataRequired()]),
    'challenge_id_fk' : IntegerField('Challenge_id_fk', validators=[validators.DataRequired()]),
    'completed' : BooleanField('Completed'),
    'completion_date' : DateTimeField('Completion_date', widget=DateTimePickerWidget(), validators=[validators.DataRequired()]),
    'person_fk': QuerySelectField('Person_fk', query_factory=lambda: db.session.query(Person), widget=Select2Widget(), allow_blank=True),
    'challenge_fk': QuerySelectField('Challenge_fk', query_factory=lambda: db.session.query(GamificationChallenge), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class VolunteerLogView(ModelView):
    datamodel = SQLAInterface('VolunteerLog')
    list_title = 'Volunteer Log List'
    show_title = 'Volunteer Log Details'
    add_title = 'Add Volunteer Log'
    edit_title = 'Edit Volunteer Log'
    list_columns = ['id', 'person_id_fk', 'organization_id_fk', 'start_date', 'end_date', 'hours_contributed', 'role', 'skills_used']
    show_columns = ['id', 'person_id_fk', 'organization_id_fk', 'start_date', 'end_date', 'hours_contributed', 'role', 'skills_used']
    add_columns = ['person_id_fk', 'organization_id_fk', 'start_date', 'end_date', 'hours_contributed', 'role', 'skills_used']
    edit_columns = ['person_id_fk', 'organization_id_fk', 'start_date', 'end_date', 'hours_contributed', 'role', 'skills_used']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['role', 'skills_used']
    label_columns = {'id': 'Id', 'person_id_fk': 'Person Id Fk', 'organization_id_fk': 'Organization Id Fk', 'start_date': 'Start Date', 'end_date': 'End Date', 'hours_contributed': 'Hours Contributed', 'role': 'Role', 'skills_used': 'Skills Used'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'organization_id_fk', 'start_date', 'end_date', 'hours_contributed', 'role', 'skills_used']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'organization_id_fk', 'start_date', 'end_date', 'hours_contributed', 'role', 'skills_used']})
    ]
    

    add_fieldsets = [
        ('Add Volunteer Log', {'fields': ['person_id_fk', 'organization_id_fk', 'start_date', 'end_date', 'hours_contributed', 'role', 'skills_used']})
    ]
    

    edit_fieldsets = [
        ('Edit Volunteer Log', {'fields': ['person_id_fk', 'organization_id_fk', 'start_date', 'end_date', 'hours_contributed', 'role', 'skills_used']})
    ]
    
    validators_columns = {'person_id_fk': '[validators.DataRequired()]', 'organization_id_fk': '[validators.DataRequired()]', 'role': '[validators.Length(max=100)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'person_id_fk': 'db.session.query(Person)', 'organization_id_fk': 'db.session.query(Organization)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'person_id_fk' : IntegerField('Person_id_fk', validators=[validators.DataRequired()]),
    'organization_id_fk' : IntegerField('Organization_id_fk', validators=[validators.DataRequired()]),
    'start_date' : DateField('Start_date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'end_date' : DateField('End_date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'hours_contributed' : IntegerField('Hours_contributed', validators=[validators.DataRequired()]),
    'role': StringField('Role', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=100)]),
    'skills_used': StringField('Skills_used', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'person_fk': QuerySelectField('Person_fk', query_factory=lambda: db.session.query(Person), widget=Select2Widget(), allow_blank=True),
    'organization_fk': QuerySelectField('Organization_fk', query_factory=lambda: db.session.query(Organization), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class EventRegistrationView(ModelView):
    datamodel = SQLAInterface('EventRegistration')
    list_title = 'Event Registration List'
    show_title = 'Event Registration Details'
    add_title = 'Add Event Registration'
    edit_title = 'Edit Event Registration'
    list_columns = ['id', 'event_id_fk', 'person_id_fk', 'registration_date', 'attended']
    show_columns = ['id', 'event_id_fk', 'person_id_fk', 'registration_date', 'attended']
    add_columns = ['event_id_fk', 'person_id_fk', 'registration_date', 'attended']
    edit_columns = ['event_id_fk', 'person_id_fk', 'registration_date', 'attended']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = []
    label_columns = {'id': 'Id', 'event_id_fk': 'Event Id Fk', 'person_id_fk': 'Person Id Fk', 'registration_date': 'Registration Date', 'attended': 'Attended'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'event_id_fk', 'person_id_fk', 'registration_date', 'attended']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'event_id_fk', 'person_id_fk', 'registration_date', 'attended']})
    ]
    

    add_fieldsets = [
        ('Add Event Registration', {'fields': ['event_id_fk', 'person_id_fk', 'registration_date', 'attended']})
    ]
    

    edit_fieldsets = [
        ('Edit Event Registration', {'fields': ['event_id_fk', 'person_id_fk', 'registration_date', 'attended']})
    ]
    
    validators_columns = {'event_id_fk': '[validators.DataRequired()]', 'person_id_fk': '[validators.DataRequired()]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'event_id_fk': 'db.session.query(Event)', 'person_id_fk': 'db.session.query(Person)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'event_id_fk' : IntegerField('Event_id_fk', validators=[validators.DataRequired()]),
    'person_id_fk' : IntegerField('Person_id_fk', validators=[validators.DataRequired()]),
    'registration_date' : DateTimeField('Registration_date', widget=DateTimePickerWidget(), validators=[validators.DataRequired()]),
    'attended' : BooleanField('Attended'),
    'event_fk': QuerySelectField('Event_fk', query_factory=lambda: db.session.query(Event), widget=Select2Widget(), allow_blank=True),
    'person_fk': QuerySelectField('Person_fk', query_factory=lambda: db.session.query(Person), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class ImpactView(ModelView):
    datamodel = SQLAInterface('Impact')
    list_title = 'Impact List'
    show_title = 'Impact Details'
    add_title = 'Add Impact'
    edit_title = 'Edit Impact'
    list_columns = ['id', 'organization_id_fk', 'project_id_fk', 'metric_name', 'value', 'unit', 'date_measured', 'description']
    show_columns = ['id', 'organization_id_fk', 'project_id_fk', 'metric_name', 'value', 'unit', 'date_measured', 'description']
    add_columns = ['organization_id_fk', 'project_id_fk', 'metric_name', 'value', 'unit', 'date_measured', 'description']
    edit_columns = ['organization_id_fk', 'project_id_fk', 'metric_name', 'value', 'unit', 'date_measured', 'description']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['metric_name', 'unit', 'description']
    label_columns = {'id': 'Id', 'organization_id_fk': 'Organization Id Fk', 'project_id_fk': 'Project Id Fk', 'metric_name': 'Metric Name', 'value': 'Value', 'unit': 'Unit', 'date_measured': 'Date Measured', 'description': 'Description'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id_fk', 'project_id_fk', 'metric_name', 'value', 'unit', 'date_measured', 'description']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id_fk', 'project_id_fk', 'metric_name', 'value', 'unit', 'date_measured', 'description']})
    ]
    

    add_fieldsets = [
        ('Add Impact', {'fields': ['organization_id_fk', 'project_id_fk', 'metric_name', 'value', 'unit', 'date_measured', 'description']})
    ]
    

    edit_fieldsets = [
        ('Edit Impact', {'fields': ['organization_id_fk', 'project_id_fk', 'metric_name', 'value', 'unit', 'date_measured', 'description']})
    ]
    
    validators_columns = {'organization_id_fk': '[validators.DataRequired()]', 'metric_name': '[validators.DataRequired(), validators.Length(max=200)]', 'unit': '[validators.Length(max=50)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'project_id_fk': 'db.session.query(Project)', 'organization_id_fk': 'db.session.query(Organization)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'organization_id_fk' : IntegerField('Organization_id_fk', validators=[validators.DataRequired()]),
    'project_id_fk' : IntegerField('Project_id_fk', validators=[validators.DataRequired()]),
    'metric_name': StringField('Metric_name', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=200)]),
    'value' : DecimalField('Value', validators=[validators.DataRequired()]),
    'unit': StringField('Unit', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=50)]),
    'date_measured' : DateField('Date_measured', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'description': StringField('Description', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'project_fk': QuerySelectField('Project_fk', query_factory=lambda: db.session.query(Project), widget=Select2Widget(), allow_blank=True),
    'organization_fk': QuerySelectField('Organization_fk', query_factory=lambda: db.session.query(Organization), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class PersonTrainingView(ModelView):
    datamodel = SQLAInterface('PersonTraining')
    list_title = 'Person Training List'
    show_title = 'Person Training Details'
    add_title = 'Add Person Training'
    edit_title = 'Edit Person Training'
    list_columns = ['id', 'training_id_fk', 'person_id_fk', 'start_date', 'completion_date', 'completed', 'certificate_id']
    show_columns = ['id', 'training_id_fk', 'person_id_fk', 'start_date', 'completion_date', 'completed', 'certificate_id']
    add_columns = ['training_id_fk', 'person_id_fk', 'start_date', 'completion_date', 'completed', 'certificate_id']
    edit_columns = ['training_id_fk', 'person_id_fk', 'start_date', 'completion_date', 'completed', 'certificate_id']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['certificate_id']
    label_columns = {'id': 'Id', 'training_id_fk': 'Training Id Fk', 'person_id_fk': 'Person Id Fk', 'start_date': 'Start Date', 'completion_date': 'Completion Date', 'completed': 'Completed', 'certificate_id': 'Certificate Id'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'training_id_fk', 'person_id_fk', 'start_date', 'completion_date', 'completed', 'certificate_id']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'training_id_fk', 'person_id_fk', 'start_date', 'completion_date', 'completed', 'certificate_id']})
    ]
    

    add_fieldsets = [
        ('Add Person Training', {'fields': ['training_id_fk', 'person_id_fk', 'start_date', 'completion_date', 'completed', 'certificate_id']})
    ]
    

    edit_fieldsets = [
        ('Edit Person Training', {'fields': ['training_id_fk', 'person_id_fk', 'start_date', 'completion_date', 'completed', 'certificate_id']})
    ]
    
    validators_columns = {'training_id_fk': '[validators.DataRequired()]', 'person_id_fk': '[validators.DataRequired()]', 'certificate_id': '[validators.Length(max=100)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'training_id_fk': 'db.session.query(Training)', 'person_id_fk': 'db.session.query(Person)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'training_id_fk' : IntegerField('Training_id_fk', validators=[validators.DataRequired()]),
    'person_id_fk' : IntegerField('Person_id_fk', validators=[validators.DataRequired()]),
    'start_date' : DateField('Start_date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'completion_date' : DateField('Completion_date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'completed' : BooleanField('Completed'),
    'certificate_id': StringField('Certificate_id', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=100)]),
    'training_fk': QuerySelectField('Training_fk', query_factory=lambda: db.session.query(Training), widget=Select2Widget(), allow_blank=True),
    'person_fk': QuerySelectField('Person_fk', query_factory=lambda: db.session.query(Person), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class PjFeedbackView(ModelView):
    datamodel = SQLAInterface('PjFeedback')
    list_title = 'Pj Feedback List'
    show_title = 'Pj Feedback Details'
    add_title = 'Add Pj Feedback'
    edit_title = 'Edit Pj Feedback'
    list_columns = ['id', 'person_id_fk', 'organization_id_fk', 'project_id_fk', 'rating', 'comments', 'notes', 'date']
    show_columns = ['id', 'person_id_fk', 'organization_id_fk', 'project_id_fk', 'rating', 'comments', 'notes', 'date']
    add_columns = ['person_id_fk', 'organization_id_fk', 'project_id_fk', 'rating', 'comments', 'notes', 'date']
    edit_columns = ['person_id_fk', 'organization_id_fk', 'project_id_fk', 'rating', 'comments', 'notes', 'date']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['comments', 'notes']
    label_columns = {'id': 'Id', 'person_id_fk': 'Person Id Fk', 'organization_id_fk': 'Organization Id Fk', 'project_id_fk': 'Project Id Fk', 'rating': 'Rating', 'comments': 'Comments', 'notes': 'Notes', 'date': 'Date'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'organization_id_fk', 'project_id_fk', 'rating', 'comments', 'notes', 'date']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'person_id_fk', 'organization_id_fk', 'project_id_fk', 'rating', 'comments', 'notes', 'date']})
    ]
    

    add_fieldsets = [
        ('Add Pj Feedback', {'fields': ['person_id_fk', 'organization_id_fk', 'project_id_fk', 'rating', 'comments', 'notes', 'date']})
    ]
    

    edit_fieldsets = [
        ('Edit Pj Feedback', {'fields': ['person_id_fk', 'organization_id_fk', 'project_id_fk', 'rating', 'comments', 'notes', 'date']})
    ]
    
    validators_columns = {'person_id_fk': '[validators.DataRequired()]', 'organization_id_fk': '[validators.DataRequired()]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'organization_id_fk': 'db.session.query(Organization)', 'project_id_fk': 'db.session.query(Project)', 'person_id_fk': 'db.session.query(Person)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'person_id_fk' : IntegerField('Person_id_fk', validators=[validators.DataRequired()]),
    'organization_id_fk' : IntegerField('Organization_id_fk', validators=[validators.DataRequired()]),
    'project_id_fk' : IntegerField('Project_id_fk', validators=[validators.DataRequired()]),
    'rating' : IntegerField('Rating', validators=[validators.DataRequired()]),
    'comments': StringField('Comments', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'notes': StringField('Notes', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=None)]),
    'date' : DateField('Date', widget=DatePickerWidget(), validators=[validators.DataRequired()]),
    'organization_fk': QuerySelectField('Organization_fk', query_factory=lambda: db.session.query(Organization), widget=Select2Widget(), allow_blank=True),
    'project_fk': QuerySelectField('Project_fk', query_factory=lambda: db.session.query(Project), widget=Select2Widget(), allow_blank=True),
    'person_fk': QuerySelectField('Person_fk', query_factory=lambda: db.session.query(Person), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class ProjectLocationsView(ModelView):
    datamodel = SQLAInterface('ProjectLocations')
    list_title = 'Project Locations List'
    show_title = 'Project Locations Details'
    add_title = 'Add Project Locations'
    edit_title = 'Edit Project Locations'
    list_columns = ['id', 'project_id_fk', 'location_name', 'latitude', 'longitude']
    show_columns = ['id', 'project_id_fk', 'location_name', 'latitude', 'longitude']
    add_columns = ['project_id_fk', 'location_name', 'latitude', 'longitude']
    edit_columns = ['project_id_fk', 'location_name', 'latitude', 'longitude']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = ['location_name']
    label_columns = {'id': 'Id', 'project_id_fk': 'Project Id Fk', 'location_name': 'Location Name', 'latitude': 'Latitude', 'longitude': 'Longitude'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'project_id_fk', 'location_name', 'latitude', 'longitude']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'project_id_fk', 'location_name', 'latitude', 'longitude']})
    ]
    

    add_fieldsets = [
        ('Add Project Locations', {'fields': ['project_id_fk', 'location_name', 'latitude', 'longitude']})
    ]
    

    edit_fieldsets = [
        ('Edit Project Locations', {'fields': ['project_id_fk', 'location_name', 'latitude', 'longitude']})
    ]
    
    validators_columns = {'project_id_fk': '[validators.DataRequired()]', 'location_name': '[validators.Length(max=255)]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'project_id_fk': 'db.session.query(Project)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'project_id_fk' : IntegerField('Project_id_fk', validators=[validators.DataRequired()]),
    'location_name': StringField('Location_name', widget=BS3TextFieldWidget(), validators=[validators.DataRequired(), validators.Length(max=255)]),
    'latitude' : FloatField('Latitude', validators=[validators.DataRequired()]),
    'longitude' : FloatField('Longitude', validators=[validators.DataRequired()]),
    'project_fk': QuerySelectField('Project_fk', query_factory=lambda: db.session.query(Project), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class ProjectTagView(ModelView):
    datamodel = SQLAInterface('ProjectTag')
    list_title = 'Project Tag List'
    show_title = 'Project Tag Details'
    add_title = 'Add Project Tag'
    edit_title = 'Edit Project Tag'
    list_columns = ['id', 'project_id_fk', 'tag_id_fk']
    show_columns = ['id', 'project_id_fk', 'tag_id_fk']
    add_columns = ['project_id_fk', 'tag_id_fk']
    edit_columns = ['project_id_fk', 'tag_id_fk']
    list_exclude_columns = []
    show_exclude_columns = []
    add_exclude_columns = []
    edit_exclude_columns = []
    search_columns = []
    label_columns = {'id': 'Id', 'project_id_fk': 'Project Id Fk', 'tag_id_fk': 'Tag Id Fk'}
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'project_id_fk', 'tag_id_fk']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'project_id_fk', 'tag_id_fk']})
    ]
    

    add_fieldsets = [
        ('Add Project Tag', {'fields': ['project_id_fk', 'tag_id_fk']})
    ]
    

    edit_fieldsets = [
        ('Edit Project Tag', {'fields': ['project_id_fk', 'tag_id_fk']})
    ]
    
    validators_columns = {'project_id_fk': '[validators.DataRequired()]', 'tag_id_fk': '[validators.DataRequired()]'}
    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    form_query_rel_fields = {'project_id_fk': 'db.session.query(Project)', 'tag_id_fk': 'db.session.query(Tag)'}
    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None


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

        print_view = f"{self.__class__.__name__}PrintView"
        return redirect(url_for(print_view, pks=[item.id for item in items]))

    @action("export", "Export", "Export as CSV", "fa-file-excel-o")
    def export(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to export the items
        # This is a placeholder and should be customized based on your needs
        return redirect(url_for('export_items', model=self.datamodel.obj.__name__, ids=[item.id for item in items]))

    @action("bookmark", "Bookmark", "Bookmark selected items", "fa-bookmark")
    def bookmark(self, items):
        if not isinstance(items, list):
            items = [items]

        # Here you would implement the logic to bookmark the items
        # This is a placeholder and should be customized based on your needs
        for item in items:
            # Assuming you have a Bookmark model
            bookmark = Bookmark(user_id=g.user.id, item_id=item.id, item_type=self.datamodel.obj.__name__)
            db.session.add(bookmark)

        db.session.commit()
        flash(f"{len(items)} item(s) bookmarked successfully.", "success")
        return redirect(self.get_redirect())

    @expose('/print/<pks>')
    @has_access
    def print_view(self, pks):
        pks = pks.split(',')
        items = self.datamodel.get_many(pks)
        self.update_redirect()
        return self.render_template('print_view.html',
                                    items=items,
                                    title=self.list_title,
                                    widgets=self.show_columns)
    

    # Form fields
    form_extra_fields = {
    'project_id_fk' : IntegerField('Project_id_fk', validators=[validators.DataRequired()]),
    'tag_id_fk' : IntegerField('Tag_id_fk', validators=[validators.DataRequired()]),
    'project_fk': QuerySelectField('Project_fk', query_factory=lambda: db.session.query(Project), widget=Select2Widget(), allow_blank=True),
    'tag_fk': QuerySelectField('Tag_fk', query_factory=lambda: db.session.query(Tag), widget=Select2Widget(), allow_blank=True),
    }


    search_widget = SearchWidget(
        labels={"name": "Name", "description": "Description"},
        search_columns=["name", "description"],
        filters=[{"name": "name", "op": "ilike"}],
        filter_rel_fields={"category": [["name", FilterStartsWith, ""]]}
    )
    
    # Related Views
    # related_views = []

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Show Widget
    # show_template = 'appbuilder/general/model/show.html'
    # show_widget = ShowWidget

    # Add Widget
    # add_template = 'appbuilder/general/model/add.html'
    # add_widget = FormWidget

    # Edit Widget
    # edit_template = 'appbuilder/general/model/edit.html'
    # edit_widget = FormWidget

    # Query Select Fields
    # query_select_fields = {}

    # Pagination
    # page_size = 10

    # Inline Forms
    # inline_models = None

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

    def __repr__(self):
        return self.id
    

class ContactTypeContactMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('ContactType')
    related_views = [ContactView]
    list_title = 'Contact Type with Contact'
    show_title = 'Contact Type Detail'
    add_title = 'Add Contact Type'
    edit_title = 'Edit Contact Type'
    description_columns = {'id': 'Unique identifier for the address type.', 'name': 'Name or type of contact method, e.g., Mobile, Email, WhatsApp.', 'description': 'Brief description about the address type, providing context or usage scenarios.', 'is_digital': 'Indicates if the contact method is digital or physical.', 'requires_verification': 'Indicates if the address type typically requires a verification process, e.g., email confirmation.', 'max_length': 'If applicable, the maximum character length of a value of this address type. Useful for validation.', 'icon_url': 'URL or link to an icon or image representing this address type. Useful for UI/UX purposes.', 'created_at': 'Timestamp when the address type was added to the system.', 'updated_at': 'Timestamp when the address type was last updated.'}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'description', 'is_digital', 'requires_verification', 'max_length', 'icon_url', 'created_at', 'updated_at']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'description', 'is_digital', 'requires_verification', 'max_length', 'icon_url', 'created_at', 'updated_at']})
    ]
    

    add_fieldsets = [
        ('Add Contact Type', {'fields': ['name', 'description', 'is_digital', 'requires_verification', 'max_length', 'icon_url', 'created_at', 'updated_at']})
    ]
    

    edit_fieldsets = [
        ('Edit Contact Type', {'fields': ['name', 'description', 'is_digital', 'requires_verification', 'max_length', 'icon_url', 'created_at', 'updated_at']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonContactMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [ContactView]
    list_title = 'Person with Contact'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class BadgeGamificationChallengeMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Badge')
    related_views = [GamificationChallengeView]
    list_title = 'Badge with Gamification Challenge'
    show_title = 'Badge Detail'
    add_title = 'Add Badge'
    edit_title = 'Edit Badge'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'description', 'criteria', 'icon']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'description', 'criteria', 'icon']})
    ]
    

    add_fieldsets = [
        ('Add Badge', {'fields': ['name', 'description', 'criteria', 'icon']})
    ]
    

    edit_fieldsets = [
        ('Edit Badge', {'fields': ['name', 'description', 'criteria', 'icon']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonLeaderboardMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [LeaderboardView]
    list_title = 'Person with Leaderboard'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonMessageMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [MessageView]
    list_title = 'Person with Message'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonMessageMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [MessageView]
    list_title = 'Person with Message'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonNotificationMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [NotificationView]
    list_title = 'Person with Notification'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonOrganizationMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [OrganizationView]
    list_title = 'Person with Organization'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class CountryOrganizationMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Country')
    related_views = [OrganizationView]
    list_title = 'Country with Organization'
    show_title = 'Country Detail'
    add_title = 'Add Country'
    edit_title = 'Edit Country'
    description_columns = {'iso_alpha2': '2-letter ISO 3166-1 alpha code e.g., US for the United States', 'iso_alpha3': '3-letter ISO 3166-1 alpha code e.g., USA for the United States', 'iso_numeric': 'ISO 3166-1 numeric code e.g., 840 for the United States', 'fips_code': 'Federal Information Processing Standard code, used by the US government', 'name': 'Full name of the country', 'capital': 'Capital city of the country', 'areainsqkm': 'Total area of the country in square kilometers', 'population': 'Estimated population of the country', 'continent': 'Abbreviation of the continent the country is located in', 'tld': 'Top Level Domain for the country e.g., .us for the United States', 'currencycode': 'ISO code of the country’s currency e.g., USD for US Dollar', 'currencyname': 'Full name of the country’s currency e.g., Dollar for US Dollar', 'phone': 'Country dialing code e.g., +1 for the United States', 'postalcode': 'Template or format of postal codes in the country', 'postalcoderegex': 'Regular expression pattern to validate postal codes', 'languages': 'Commonly spoken languages in the country, represented as ISO codes', 'neighbors': 'Neighboring countries, usually represented as ISO codes', 'equivfipscode': 'Equivalent FIPS code in cases where it might differ from the primary FIPS code', 'flag': 'Field to store a link or representation of the country’s flag'}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'iso_alpha2', 'iso_alpha3', 'iso_numeric', 'fips_code', 'name', 'capital', 'areainsqkm', 'population', 'continent', 'tld', 'currencycode', 'currencyname', 'phone', 'postalcode', 'postalcoderegex', 'languages', 'neighbors', 'equivfipscode', 'flag']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'iso_alpha2', 'iso_alpha3', 'iso_numeric', 'fips_code', 'name', 'capital', 'areainsqkm', 'population', 'continent', 'tld', 'currencycode', 'currencyname', 'phone', 'postalcode', 'postalcoderegex', 'languages', 'neighbors', 'equivfipscode', 'flag']})
    ]
    

    add_fieldsets = [
        ('Add Country', {'fields': ['iso_alpha2', 'iso_alpha3', 'iso_numeric', 'fips_code', 'name', 'capital', 'areainsqkm', 'population', 'continent', 'tld', 'currencycode', 'currencyname', 'phone', 'postalcode', 'postalcoderegex', 'languages', 'neighbors', 'equivfipscode', 'flag']})
    ]
    

    edit_fieldsets = [
        ('Edit Country', {'fields': ['iso_alpha2', 'iso_alpha3', 'iso_numeric', 'fips_code', 'name', 'capital', 'areainsqkm', 'population', 'continent', 'tld', 'currencycode', 'currencyname', 'phone', 'postalcode', 'postalcoderegex', 'languages', 'neighbors', 'equivfipscode', 'flag']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonPersonBadgeMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [PersonBadgeView]
    list_title = 'Person with Person Badge'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class BadgePersonBadgeMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Badge')
    related_views = [PersonBadgeView]
    list_title = 'Badge with Person Badge'
    show_title = 'Badge Detail'
    add_title = 'Add Badge'
    edit_title = 'Edit Badge'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'description', 'criteria', 'icon']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'description', 'criteria', 'icon']})
    ]
    

    add_fieldsets = [
        ('Add Badge', {'fields': ['name', 'description', 'criteria', 'icon']})
    ]
    

    edit_fieldsets = [
        ('Edit Badge', {'fields': ['name', 'description', 'criteria', 'icon']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonPersonCertificationMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [PersonCertificationView]
    list_title = 'Person with Person Certification'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonPersonCourseMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [PersonCourseView]
    list_title = 'Person with Person Course'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonPersonEducationMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [PersonEducationView]
    list_title = 'Person with Person Education'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonPersonExperienceMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [PersonExperienceView]
    list_title = 'Person with Person Experience'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonPersonHonorAwardMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [PersonHonorAwardView]
    list_title = 'Person with Person Honor Award'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonPersonLanguageMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [PersonLanguageView]
    list_title = 'Person with Person Language'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonPersonOrganizationMembershipMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [PersonOrganizationMembershipView]
    list_title = 'Person with Person Organization Membership'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonPersonPatentMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [PersonPatentView]
    list_title = 'Person with Person Patent'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonPersonProjectMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [PersonProjectView]
    list_title = 'Person with Person Project'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonPersonPublicationMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [PersonPublicationView]
    list_title = 'Person with Person Publication'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonPersonVolunteerExperienceMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [PersonVolunteerExperienceView]
    list_title = 'Person with Person Volunteer Experience'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonPointEarningActivityMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [PointEarningActivityView]
    list_title = 'Person with Point Earning Activity'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonProfileUpdateReminderMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [ProfileUpdateReminderView]
    list_title = 'Person with Profile Update Reminder'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class SkillCategorySkillMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('SkillCategory')
    related_views = [SkillView]
    list_title = 'Skill Category with Skill'
    show_title = 'Skill Category Detail'
    add_title = 'Add Skill Category'
    edit_title = 'Edit Skill Category'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'description']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'description']})
    ]
    

    add_fieldsets = [
        ('Add Skill Category', {'fields': ['name', 'description']})
    ]
    

    edit_fieldsets = [
        ('Edit Skill Category', {'fields': ['name', 'description']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class CountryTimezoneMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Country')
    related_views = [TimezoneView]
    list_title = 'Country with Timezone'
    show_title = 'Country Detail'
    add_title = 'Add Country'
    edit_title = 'Edit Country'
    description_columns = {'iso_alpha2': '2-letter ISO 3166-1 alpha code e.g., US for the United States', 'iso_alpha3': '3-letter ISO 3166-1 alpha code e.g., USA for the United States', 'iso_numeric': 'ISO 3166-1 numeric code e.g., 840 for the United States', 'fips_code': 'Federal Information Processing Standard code, used by the US government', 'name': 'Full name of the country', 'capital': 'Capital city of the country', 'areainsqkm': 'Total area of the country in square kilometers', 'population': 'Estimated population of the country', 'continent': 'Abbreviation of the continent the country is located in', 'tld': 'Top Level Domain for the country e.g., .us for the United States', 'currencycode': 'ISO code of the country’s currency e.g., USD for US Dollar', 'currencyname': 'Full name of the country’s currency e.g., Dollar for US Dollar', 'phone': 'Country dialing code e.g., +1 for the United States', 'postalcode': 'Template or format of postal codes in the country', 'postalcoderegex': 'Regular expression pattern to validate postal codes', 'languages': 'Commonly spoken languages in the country, represented as ISO codes', 'neighbors': 'Neighboring countries, usually represented as ISO codes', 'equivfipscode': 'Equivalent FIPS code in cases where it might differ from the primary FIPS code', 'flag': 'Field to store a link or representation of the country’s flag'}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'iso_alpha2', 'iso_alpha3', 'iso_numeric', 'fips_code', 'name', 'capital', 'areainsqkm', 'population', 'continent', 'tld', 'currencycode', 'currencyname', 'phone', 'postalcode', 'postalcoderegex', 'languages', 'neighbors', 'equivfipscode', 'flag']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'iso_alpha2', 'iso_alpha3', 'iso_numeric', 'fips_code', 'name', 'capital', 'areainsqkm', 'population', 'continent', 'tld', 'currencycode', 'currencyname', 'phone', 'postalcode', 'postalcoderegex', 'languages', 'neighbors', 'equivfipscode', 'flag']})
    ]
    

    add_fieldsets = [
        ('Add Country', {'fields': ['iso_alpha2', 'iso_alpha3', 'iso_numeric', 'fips_code', 'name', 'capital', 'areainsqkm', 'population', 'continent', 'tld', 'currencycode', 'currencyname', 'phone', 'postalcode', 'postalcoderegex', 'languages', 'neighbors', 'equivfipscode', 'flag']})
    ]
    

    edit_fieldsets = [
        ('Edit Country', {'fields': ['iso_alpha2', 'iso_alpha3', 'iso_numeric', 'fips_code', 'name', 'capital', 'areainsqkm', 'population', 'continent', 'tld', 'currencycode', 'currencyname', 'phone', 'postalcode', 'postalcoderegex', 'languages', 'neighbors', 'equivfipscode', 'flag']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonUserActivityMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [UserActivityView]
    list_title = 'Person with User Activity'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonUserGamificationMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [UserGamificationView]
    list_title = 'Person with User Gamification'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class OrganizationBoardMemberMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Organization')
    related_views = [BoardMemberView]
    list_title = 'Organization with Board Member'
    show_title = 'Organization Detail'
    add_title = 'Add Organization'
    edit_title = 'Edit Organization'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    add_fieldsets = [
        ('Add Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonBoardMemberMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [BoardMemberView]
    list_title = 'Person with Board Member'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class OrganizationContactApplicationMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Organization')
    related_views = [ContactApplicationView]
    list_title = 'Organization with Contact Application'
    show_title = 'Organization Detail'
    add_title = 'Add Organization'
    edit_title = 'Edit Organization'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    add_fieldsets = [
        ('Add Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonContactApplicationMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [ContactApplicationView]
    list_title = 'Person with Contact Application'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class OrganizationDocumentSubmissionMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Organization')
    related_views = [DocumentSubmissionView]
    list_title = 'Organization with Document Submission'
    show_title = 'Organization Detail'
    add_title = 'Add Organization'
    edit_title = 'Edit Organization'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    add_fieldsets = [
        ('Add Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class OrganizationEventMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Organization')
    related_views = [EventView]
    list_title = 'Organization with Event'
    show_title = 'Organization Detail'
    add_title = 'Add Organization'
    edit_title = 'Edit Organization'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    add_fieldsets = [
        ('Add Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class OrganizationExecutivePositionMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Organization')
    related_views = [ExecutivePositionView]
    list_title = 'Organization with Executive Position'
    show_title = 'Organization Detail'
    add_title = 'Add Organization'
    edit_title = 'Edit Organization'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    add_fieldsets = [
        ('Add Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonExecutivePositionMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [ExecutivePositionView]
    list_title = 'Person with Executive Position'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class OrganizationGrantMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Organization')
    related_views = [GrantView]
    list_title = 'Organization with Grant'
    show_title = 'Organization Detail'
    add_title = 'Add Organization'
    edit_title = 'Edit Organization'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    add_fieldsets = [
        ('Add Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class OrganizationGrantMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Organization')
    related_views = [GrantView]
    list_title = 'Organization with Grant'
    show_title = 'Organization Detail'
    add_title = 'Add Organization'
    edit_title = 'Edit Organization'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    add_fieldsets = [
        ('Add Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class OrganizationOnboardingProgressMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Organization')
    related_views = [OnboardingProgressView]
    list_title = 'Organization with Onboarding Progress'
    show_title = 'Organization Detail'
    add_title = 'Add Organization'
    edit_title = 'Edit Organization'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    add_fieldsets = [
        ('Add Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonOnboardingProgressMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [OnboardingProgressView]
    list_title = 'Person with Onboarding Progress'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class OrganizationOrganizationAwardMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Organization')
    related_views = [OrganizationAwardView]
    list_title = 'Organization with Organization Award'
    show_title = 'Organization Detail'
    add_title = 'Add Organization'
    edit_title = 'Edit Organization'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    add_fieldsets = [
        ('Add Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class BadgeOrganizationBadgeMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Badge')
    related_views = [OrganizationBadgeView]
    list_title = 'Badge with Organization Badge'
    show_title = 'Badge Detail'
    add_title = 'Add Badge'
    edit_title = 'Edit Badge'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'description', 'criteria', 'icon']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'description', 'criteria', 'icon']})
    ]
    

    add_fieldsets = [
        ('Add Badge', {'fields': ['name', 'description', 'criteria', 'icon']})
    ]
    

    edit_fieldsets = [
        ('Edit Badge', {'fields': ['name', 'description', 'criteria', 'icon']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class OrganizationOrganizationBadgeMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Organization')
    related_views = [OrganizationBadgeView]
    list_title = 'Organization with Organization Badge'
    show_title = 'Organization Detail'
    add_title = 'Add Organization'
    edit_title = 'Edit Organization'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    add_fieldsets = [
        ('Add Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class OrganizationOrganizationClimateCategoriesMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Organization')
    related_views = [OrganizationClimateCategoriesView]
    list_title = 'Organization with Organization Climate Categories'
    show_title = 'Organization Detail'
    add_title = 'Add Organization'
    edit_title = 'Edit Organization'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    add_fieldsets = [
        ('Add Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonOrganizationContactMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [OrganizationContactView]
    list_title = 'Person with Organization Contact'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class OrganizationOrganizationContactMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Organization')
    related_views = [OrganizationContactView]
    list_title = 'Organization with Organization Contact'
    show_title = 'Organization Detail'
    add_title = 'Add Organization'
    edit_title = 'Edit Organization'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    add_fieldsets = [
        ('Add Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class OrganizationOrganizationDocumentsMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Organization')
    related_views = [OrganizationDocumentsView]
    list_title = 'Organization with Organization Documents'
    show_title = 'Organization Detail'
    add_title = 'Add Organization'
    edit_title = 'Edit Organization'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    add_fieldsets = [
        ('Add Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class OrganizationOrganizationHierarchyMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Organization')
    related_views = [OrganizationHierarchyView]
    list_title = 'Organization with Organization Hierarchy'
    show_title = 'Organization Detail'
    add_title = 'Add Organization'
    edit_title = 'Edit Organization'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    add_fieldsets = [
        ('Add Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class OrganizationOrganizationHierarchyMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Organization')
    related_views = [OrganizationHierarchyView]
    list_title = 'Organization with Organization Hierarchy'
    show_title = 'Organization Detail'
    add_title = 'Add Organization'
    edit_title = 'Edit Organization'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    add_fieldsets = [
        ('Add Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class OrganizationOrganizationProfileMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Organization')
    related_views = [OrganizationProfileView]
    list_title = 'Organization with Organization Profile'
    show_title = 'Organization Detail'
    add_title = 'Add Organization'
    edit_title = 'Edit Organization'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    add_fieldsets = [
        ('Add Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class OrganizationOrganizationProgramsMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Organization')
    related_views = [OrganizationProgramsView]
    list_title = 'Organization with Organization Programs'
    show_title = 'Organization Detail'
    add_title = 'Add Organization'
    edit_title = 'Edit Organization'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    add_fieldsets = [
        ('Add Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class OrganizationOrganizationSdgsMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Organization')
    related_views = [OrganizationSdgsView]
    list_title = 'Organization with Organization Sdgs'
    show_title = 'Organization Detail'
    add_title = 'Add Organization'
    edit_title = 'Edit Organization'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    add_fieldsets = [
        ('Add Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class OrganizationOrganizationTagMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Organization')
    related_views = [OrganizationTagView]
    list_title = 'Organization with Organization Tag'
    show_title = 'Organization Detail'
    add_title = 'Add Organization'
    edit_title = 'Edit Organization'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    add_fieldsets = [
        ('Add Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class TagOrganizationTagMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Tag')
    related_views = [OrganizationTagView]
    list_title = 'Tag with Organization Tag'
    show_title = 'Tag Detail'
    add_title = 'Add Tag'
    edit_title = 'Edit Tag'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name']})
    ]
    

    add_fieldsets = [
        ('Add Tag', {'fields': ['name']})
    ]
    

    edit_fieldsets = [
        ('Edit Tag', {'fields': ['name']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class OrganizationOrganizationVerificationMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Organization')
    related_views = [OrganizationVerificationView]
    list_title = 'Organization with Organization Verification'
    show_title = 'Organization Detail'
    add_title = 'Add Organization'
    edit_title = 'Edit Organization'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    add_fieldsets = [
        ('Add Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class OrganizationPersonOrganizationClaimMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Organization')
    related_views = [PersonOrganizationClaimView]
    list_title = 'Organization with Person Organization Claim'
    show_title = 'Organization Detail'
    add_title = 'Add Organization'
    edit_title = 'Edit Organization'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    add_fieldsets = [
        ('Add Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonPersonOrganizationClaimMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [PersonOrganizationClaimView]
    list_title = 'Person with Person Organization Claim'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonPersonSkillMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [PersonSkillView]
    list_title = 'Person with Person Skill'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class SkillPersonSkillMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Skill')
    related_views = [PersonSkillView]
    list_title = 'Skill with Person Skill'
    show_title = 'Skill Detail'
    add_title = 'Add Skill'
    edit_title = 'Edit Skill'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'skill_category_id_fk', 'description']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'skill_category_id_fk', 'description']})
    ]
    

    add_fieldsets = [
        ('Add Skill', {'fields': ['name', 'skill_category_id_fk', 'description']})
    ]
    

    edit_fieldsets = [
        ('Edit Skill', {'fields': ['name', 'skill_category_id_fk', 'description']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class OrganizationProjectMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Organization')
    related_views = [ProjectView]
    list_title = 'Organization with Project'
    show_title = 'Organization Detail'
    add_title = 'Add Organization'
    edit_title = 'Edit Organization'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    add_fieldsets = [
        ('Add Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class OrganizationReportMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Organization')
    related_views = [ReportView]
    list_title = 'Organization with Report'
    show_title = 'Organization Detail'
    add_title = 'Add Organization'
    edit_title = 'Edit Organization'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    add_fieldsets = [
        ('Add Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class OrganizationSocialMediaProfileMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Organization')
    related_views = [SocialMediaProfileView]
    list_title = 'Organization with Social Media Profile'
    show_title = 'Organization Detail'
    add_title = 'Add Organization'
    edit_title = 'Edit Organization'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    add_fieldsets = [
        ('Add Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonSocialMediaProfileMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [SocialMediaProfileView]
    list_title = 'Person with Social Media Profile'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class OrganizationTrainingMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Organization')
    related_views = [TrainingView]
    list_title = 'Organization with Training'
    show_title = 'Organization Detail'
    add_title = 'Add Organization'
    edit_title = 'Edit Organization'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    add_fieldsets = [
        ('Add Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonUserChallengeMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [UserChallengeView]
    list_title = 'Person with User Challenge'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class GamificationChallengeUserChallengeMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('GamificationChallenge')
    related_views = [UserChallengeView]
    list_title = 'Gamification Challenge with User Challenge'
    show_title = 'Gamification Challenge Detail'
    add_title = 'Add Gamification Challenge'
    edit_title = 'Edit Gamification Challenge'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'description', 'points_reward', 'badge_reward_id_fk', 'start_date', 'end_date']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'description', 'points_reward', 'badge_reward_id_fk', 'start_date', 'end_date']})
    ]
    

    add_fieldsets = [
        ('Add Gamification Challenge', {'fields': ['name', 'description', 'points_reward', 'badge_reward_id_fk', 'start_date', 'end_date']})
    ]
    

    edit_fieldsets = [
        ('Edit Gamification Challenge', {'fields': ['name', 'description', 'points_reward', 'badge_reward_id_fk', 'start_date', 'end_date']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonVolunteerLogMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [VolunteerLogView]
    list_title = 'Person with Volunteer Log'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class OrganizationVolunteerLogMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Organization')
    related_views = [VolunteerLogView]
    list_title = 'Organization with Volunteer Log'
    show_title = 'Organization Detail'
    add_title = 'Add Organization'
    edit_title = 'Edit Organization'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    add_fieldsets = [
        ('Add Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class EventEventRegistrationMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Event')
    related_views = [EventRegistrationView]
    list_title = 'Event with Event Registration'
    show_title = 'Event Detail'
    add_title = 'Add Event'
    edit_title = 'Edit Event'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id_fk', 'name', 'description', 'start_datetime', 'end_datetime', 'location', 'is_virtual', 'max_participants']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id_fk', 'name', 'description', 'start_datetime', 'end_datetime', 'location', 'is_virtual', 'max_participants']})
    ]
    

    add_fieldsets = [
        ('Add Event', {'fields': ['organization_id_fk', 'name', 'description', 'start_datetime', 'end_datetime', 'location', 'is_virtual', 'max_participants']})
    ]
    

    edit_fieldsets = [
        ('Edit Event', {'fields': ['organization_id_fk', 'name', 'description', 'start_datetime', 'end_datetime', 'location', 'is_virtual', 'max_participants']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonEventRegistrationMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [EventRegistrationView]
    list_title = 'Person with Event Registration'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class ProjectImpactMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Project')
    related_views = [ImpactView]
    list_title = 'Project with Impact'
    show_title = 'Project Detail'
    add_title = 'Add Project'
    edit_title = 'Edit Project'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id_fk', 'name', 'description', 'start_date', 'end_date', 'budget', 'status', 'beneficiaries', 'outcomes']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id_fk', 'name', 'description', 'start_date', 'end_date', 'budget', 'status', 'beneficiaries', 'outcomes']})
    ]
    

    add_fieldsets = [
        ('Add Project', {'fields': ['organization_id_fk', 'name', 'description', 'start_date', 'end_date', 'budget', 'status', 'beneficiaries', 'outcomes']})
    ]
    

    edit_fieldsets = [
        ('Edit Project', {'fields': ['organization_id_fk', 'name', 'description', 'start_date', 'end_date', 'budget', 'status', 'beneficiaries', 'outcomes']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class OrganizationImpactMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Organization')
    related_views = [ImpactView]
    list_title = 'Organization with Impact'
    show_title = 'Organization Detail'
    add_title = 'Add Organization'
    edit_title = 'Edit Organization'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    add_fieldsets = [
        ('Add Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class TrainingPersonTrainingMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Training')
    related_views = [PersonTrainingView]
    list_title = 'Training with Person Training'
    show_title = 'Training Detail'
    add_title = 'Add Training'
    edit_title = 'Edit Training'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'offering_org_id_fk', 'name', 'description', 'start_date', 'end_date', 'is_certified']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'offering_org_id_fk', 'name', 'description', 'start_date', 'end_date', 'is_certified']})
    ]
    

    add_fieldsets = [
        ('Add Training', {'fields': ['offering_org_id_fk', 'name', 'description', 'start_date', 'end_date', 'is_certified']})
    ]
    

    edit_fieldsets = [
        ('Edit Training', {'fields': ['offering_org_id_fk', 'name', 'description', 'start_date', 'end_date', 'is_certified']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonPersonTrainingMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [PersonTrainingView]
    list_title = 'Person with Person Training'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class OrganizationPjFeedbackMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Organization')
    related_views = [PjFeedbackView]
    list_title = 'Organization with Pj Feedback'
    show_title = 'Organization Detail'
    add_title = 'Add Organization'
    edit_title = 'Edit Organization'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    add_fieldsets = [
        ('Add Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    edit_fieldsets = [
        ('Edit Organization', {'fields': ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class ProjectPjFeedbackMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Project')
    related_views = [PjFeedbackView]
    list_title = 'Project with Pj Feedback'
    show_title = 'Project Detail'
    add_title = 'Add Project'
    edit_title = 'Edit Project'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id_fk', 'name', 'description', 'start_date', 'end_date', 'budget', 'status', 'beneficiaries', 'outcomes']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id_fk', 'name', 'description', 'start_date', 'end_date', 'budget', 'status', 'beneficiaries', 'outcomes']})
    ]
    

    add_fieldsets = [
        ('Add Project', {'fields': ['organization_id_fk', 'name', 'description', 'start_date', 'end_date', 'budget', 'status', 'beneficiaries', 'outcomes']})
    ]
    

    edit_fieldsets = [
        ('Edit Project', {'fields': ['organization_id_fk', 'name', 'description', 'start_date', 'end_date', 'budget', 'status', 'beneficiaries', 'outcomes']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class PersonPjFeedbackMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Person')
    related_views = [PjFeedbackView]
    list_title = 'Person with Pj Feedback'
    show_title = 'Person Detail'
    add_title = 'Add Person'
    edit_title = 'Edit Person'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    add_fieldsets = [
        ('Add Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    edit_fieldsets = [
        ('Edit Person', {'fields': ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class ProjectProjectLocationsMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Project')
    related_views = [ProjectLocationsView]
    list_title = 'Project with Project Locations'
    show_title = 'Project Detail'
    add_title = 'Add Project'
    edit_title = 'Edit Project'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id_fk', 'name', 'description', 'start_date', 'end_date', 'budget', 'status', 'beneficiaries', 'outcomes']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id_fk', 'name', 'description', 'start_date', 'end_date', 'budget', 'status', 'beneficiaries', 'outcomes']})
    ]
    

    add_fieldsets = [
        ('Add Project', {'fields': ['organization_id_fk', 'name', 'description', 'start_date', 'end_date', 'budget', 'status', 'beneficiaries', 'outcomes']})
    ]
    

    edit_fieldsets = [
        ('Edit Project', {'fields': ['organization_id_fk', 'name', 'description', 'start_date', 'end_date', 'budget', 'status', 'beneficiaries', 'outcomes']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class ProjectProjectTagMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Project')
    related_views = [ProjectTagView]
    list_title = 'Project with Project Tag'
    show_title = 'Project Detail'
    add_title = 'Add Project'
    edit_title = 'Edit Project'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id_fk', 'name', 'description', 'start_date', 'end_date', 'budget', 'status', 'beneficiaries', 'outcomes']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'organization_id_fk', 'name', 'description', 'start_date', 'end_date', 'budget', 'status', 'beneficiaries', 'outcomes']})
    ]
    

    add_fieldsets = [
        ('Add Project', {'fields': ['organization_id_fk', 'name', 'description', 'start_date', 'end_date', 'budget', 'status', 'beneficiaries', 'outcomes']})
    ]
    

    edit_fieldsets = [
        ('Edit Project', {'fields': ['organization_id_fk', 'name', 'description', 'start_date', 'end_date', 'budget', 'status', 'beneficiaries', 'outcomes']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class TagProjectTagMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface('Tag')
    related_views = [ProjectTagView]
    list_title = 'Tag with Project Tag'
    show_title = 'Tag Detail'
    add_title = 'Add Tag'
    edit_title = 'Edit Tag'
    description_columns = {}

    list_fieldsets = [
        ('Summary', {'fields': ['id', 'name']})
    ]
    

    show_fieldsets = [
        ('Summary', {'fields': ['id', 'name']})
    ]
    

    add_fieldsets = [
        ('Add Tag', {'fields': ['name']})
    ]
    

    edit_fieldsets = [
        ('Edit Tag', {'fields': ['name']})
    ]
    

    # Base Order
    # base_order = ('name', 'asc')

    # Base Filters
    # base_filters = [['name', FilterStartsWith, 'A']]

    # Forms
    # add_form = None
    # edit_form = None

    # Widgets
    # show_widget = None
    # add_widget = None
    # edit_widget = None
    # list_widget = None

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'
    # show_template = 'my_show_template.html'
    # add_template = 'my_add_template.html'
    # edit_template = 'my_edit_template.html'

class BadgeMultipleView(MultipleView):
    datamodel = SQLAInterface('Badge')
    views = [GamificationChallengeView, OrganizationBadgeView, PersonBadgeView]

    # Base Order
    # base_order = ('name', 'asc')

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'

class CountryMultipleView(MultipleView):
    datamodel = SQLAInterface('Country')
    views = [OrganizationView, TimezoneView]

    # Base Order
    # base_order = ('name', 'asc')

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'

class PersonMultipleView(MultipleView):
    datamodel = SQLAInterface('Person')
    views = [PersonOrganizationMembershipView, UserGamificationView, PersonHonorAwardView, OrganizationContactView, PersonPublicationView, PjFeedbackView, MessageView, PersonPatentView, PointEarningActivityView, PersonLanguageView, ContactView, BoardMemberView, PersonBadgeView, PersonOrganizationClaimView, LeaderboardView, OnboardingProgressView, ExecutivePositionView, PersonEducationView, PersonTrainingView, PersonProjectView, ContactApplicationView, SocialMediaProfileView, NotificationView, PersonExperienceView, PersonSkillView, PersonCourseView, OrganizationView, VolunteerLogView, UserActivityView, ProfileUpdateReminderView, PersonCertificationView, EventRegistrationView, UserChallengeView, PersonVolunteerExperienceView]

    # Base Order
    # base_order = ('name', 'asc')

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'

class TagMultipleView(MultipleView):
    datamodel = SQLAInterface('Tag')
    views = [ProjectTagView, OrganizationTagView]

    # Base Order
    # base_order = ('name', 'asc')

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'

class ContactMultipleView(MultipleView):
    datamodel = SQLAInterface('Contact')
    views = [PersonView, ContactTypeView]

    # Base Order
    # base_order = ('name', 'asc')

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'

class GamificationChallengeMultipleView(MultipleView):
    datamodel = SQLAInterface('GamificationChallenge')
    views = [UserChallengeView, BadgeView]

    # Base Order
    # base_order = ('name', 'asc')

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'

class OrganizationMultipleView(MultipleView):
    datamodel = SQLAInterface('Organization')
    views = [ProjectView, PjFeedbackView, OrganizationContactView, TrainingView, EventView, OrganizationProfileView, CountryView, BoardMemberView, PersonOrganizationClaimView, OrganizationClimateCategoriesView, OnboardingProgressView, ExecutivePositionView, OrganizationHierarchyView, OrganizationTagView, OrganizationDocumentsView, OrganizationAwardView, ContactApplicationView, PersonView, OrganizationProgramsView, OrganizationSdgsView, SocialMediaProfileView, GrantView, OrganizationBadgeView, ReportView, DocumentSubmissionView, VolunteerLogView, ImpactView, OrganizationVerificationView]

    # Base Order
    # base_order = ('name', 'asc')

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'

class PersonBadgeMultipleView(MultipleView):
    datamodel = SQLAInterface('PersonBadge')
    views = [PersonView, BadgeView]

    # Base Order
    # base_order = ('name', 'asc')

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'

class SkillMultipleView(MultipleView):
    datamodel = SQLAInterface('Skill')
    views = [PersonSkillView, SkillCategoryView]

    # Base Order
    # base_order = ('name', 'asc')

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'

class BoardMemberMultipleView(MultipleView):
    datamodel = SQLAInterface('BoardMember')
    views = [PersonView, OrganizationView]

    # Base Order
    # base_order = ('name', 'asc')

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'

class ContactApplicationMultipleView(MultipleView):
    datamodel = SQLAInterface('ContactApplication')
    views = [PersonView, OrganizationView]

    # Base Order
    # base_order = ('name', 'asc')

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'

class EventMultipleView(MultipleView):
    datamodel = SQLAInterface('Event')
    views = [OrganizationView, EventRegistrationView]

    # Base Order
    # base_order = ('name', 'asc')

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'

class ExecutivePositionMultipleView(MultipleView):
    datamodel = SQLAInterface('ExecutivePosition')
    views = [PersonView, OrganizationView]

    # Base Order
    # base_order = ('name', 'asc')

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'

class OnboardingProgressMultipleView(MultipleView):
    datamodel = SQLAInterface('OnboardingProgress')
    views = [PersonView, OrganizationView]

    # Base Order
    # base_order = ('name', 'asc')

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'

class OrganizationBadgeMultipleView(MultipleView):
    datamodel = SQLAInterface('OrganizationBadge')
    views = [OrganizationView, BadgeView]

    # Base Order
    # base_order = ('name', 'asc')

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'

class OrganizationContactMultipleView(MultipleView):
    datamodel = SQLAInterface('OrganizationContact')
    views = [OrganizationView, PersonView]

    # Base Order
    # base_order = ('name', 'asc')

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'

class OrganizationTagMultipleView(MultipleView):
    datamodel = SQLAInterface('OrganizationTag')
    views = [OrganizationView, TagView]

    # Base Order
    # base_order = ('name', 'asc')

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'

class PersonOrganizationClaimMultipleView(MultipleView):
    datamodel = SQLAInterface('PersonOrganizationClaim')
    views = [PersonView, OrganizationView]

    # Base Order
    # base_order = ('name', 'asc')

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'

class PersonSkillMultipleView(MultipleView):
    datamodel = SQLAInterface('PersonSkill')
    views = [SkillView, PersonView]

    # Base Order
    # base_order = ('name', 'asc')

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'

class ProjectMultipleView(MultipleView):
    datamodel = SQLAInterface('Project')
    views = [OrganizationView, ImpactView, PjFeedbackView, ProjectLocationsView, ProjectTagView]

    # Base Order
    # base_order = ('name', 'asc')

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'

class SocialMediaProfileMultipleView(MultipleView):
    datamodel = SQLAInterface('SocialMediaProfile')
    views = [PersonView, OrganizationView]

    # Base Order
    # base_order = ('name', 'asc')

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'

class TrainingMultipleView(MultipleView):
    datamodel = SQLAInterface('Training')
    views = [PersonTrainingView, OrganizationView]

    # Base Order
    # base_order = ('name', 'asc')

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'

class UserChallengeMultipleView(MultipleView):
    datamodel = SQLAInterface('UserChallenge')
    views = [GamificationChallengeView, PersonView]

    # Base Order
    # base_order = ('name', 'asc')

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'

class VolunteerLogMultipleView(MultipleView):
    datamodel = SQLAInterface('VolunteerLog')
    views = [OrganizationView, PersonView]

    # Base Order
    # base_order = ('name', 'asc')

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'

class EventRegistrationMultipleView(MultipleView):
    datamodel = SQLAInterface('EventRegistration')
    views = [PersonView, EventView]

    # Base Order
    # base_order = ('name', 'asc')

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'

class ImpactMultipleView(MultipleView):
    datamodel = SQLAInterface('Impact')
    views = [ProjectView, OrganizationView]

    # Base Order
    # base_order = ('name', 'asc')

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'

class PersonTrainingMultipleView(MultipleView):
    datamodel = SQLAInterface('PersonTraining')
    views = [TrainingView, PersonView]

    # Base Order
    # base_order = ('name', 'asc')

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'

class PjFeedbackMultipleView(MultipleView):
    datamodel = SQLAInterface('PjFeedback')
    views = [ProjectView, OrganizationView, PersonView]

    # Base Order
    # base_order = ('name', 'asc')

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'

class ProjectTagMultipleView(MultipleView):
    datamodel = SQLAInterface('ProjectTag')
    views = [ProjectView, TagView]

    # Base Order
    # base_order = ('name', 'asc')

    # List Widgets
    # list_template = 'appbuilder/general/model/list.html'
    # list_widget = ListWidget

    # Pagination
    # page_size = 10

    # Custom Templates
    # list_template = 'my_list_template.html'


class ContactTypeChartView(ChartView):
    datamodel = SQLAInterface('ContactType')
    chart_title = 'Contact Type Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by created_at',
            'group': 'created_at',
            'series': ['id']
        }
    ]


class PersonChartView(ChartView):
    datamodel = SQLAInterface('Person')
    chart_title = 'Person Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by date_of_birth',
            'group': 'date_of_birth',
            'series': ['id']
        }
    ]


class ContactChartView(ChartView):
    datamodel = SQLAInterface('Contact')
    chart_title = 'Contact Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by active_from_date',
            'group': 'active_from_date',
            'series': ['id']
        }
    ]


class GamificationChallengeChartView(ChartView):
    datamodel = SQLAInterface('GamificationChallenge')
    chart_title = 'Gamification Challenge Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by start_date',
            'group': 'start_date',
            'series': ['id']
        }
    ]


class LeaderboardChartView(ChartView):
    datamodel = SQLAInterface('Leaderboard')
    chart_title = 'Leaderboard Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by last_updated',
            'group': 'last_updated',
            'series': ['id']
        }
    ]


class MessageChartView(ChartView):
    datamodel = SQLAInterface('Message')
    chart_title = 'Message Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by sent_date',
            'group': 'sent_date',
            'series': ['id']
        }
    ]


class NotificationChartView(ChartView):
    datamodel = SQLAInterface('Notification')
    chart_title = 'Notification Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by created_date',
            'group': 'created_date',
            'series': ['id']
        }
    ]


class OrganizationChartView(ChartView):
    datamodel = SQLAInterface('Organization')
    chart_title = 'Organization Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by founded_date',
            'group': 'founded_date',
            'series': ['id']
        }
    ]


class PersonBadgeChartView(ChartView):
    datamodel = SQLAInterface('PersonBadge')
    chart_title = 'Person Badge Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'person_id_fk by date_earned',
            'group': 'date_earned',
            'series': ['person_id_fk']
        }
    ]


class PersonCertificationChartView(ChartView):
    datamodel = SQLAInterface('PersonCertification')
    chart_title = 'Person Certification Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by issue_date',
            'group': 'issue_date',
            'series': ['id']
        }
    ]


class PersonCourseChartView(ChartView):
    datamodel = SQLAInterface('PersonCourse')
    chart_title = 'Person Course Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by completion_date',
            'group': 'completion_date',
            'series': ['id']
        }
    ]


class PersonEducationChartView(ChartView):
    datamodel = SQLAInterface('PersonEducation')
    chart_title = 'Person Education Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by start_date',
            'group': 'start_date',
            'series': ['id']
        }
    ]


class PersonExperienceChartView(ChartView):
    datamodel = SQLAInterface('PersonExperience')
    chart_title = 'Person Experience Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by start_date',
            'group': 'start_date',
            'series': ['id']
        }
    ]


class PersonHonorAwardChartView(ChartView):
    datamodel = SQLAInterface('PersonHonorAward')
    chart_title = 'Person Honor Award Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by date_received',
            'group': 'date_received',
            'series': ['id']
        }
    ]


class PersonOrganizationMembershipChartView(ChartView):
    datamodel = SQLAInterface('PersonOrganizationMembership')
    chart_title = 'Person Organization Membership Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by start_date',
            'group': 'start_date',
            'series': ['id']
        }
    ]


class PersonPatentChartView(ChartView):
    datamodel = SQLAInterface('PersonPatent')
    chart_title = 'Person Patent Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by issue_date',
            'group': 'issue_date',
            'series': ['id']
        }
    ]


class PersonProjectChartView(ChartView):
    datamodel = SQLAInterface('PersonProject')
    chart_title = 'Person Project Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by start_date',
            'group': 'start_date',
            'series': ['id']
        }
    ]


class PersonPublicationChartView(ChartView):
    datamodel = SQLAInterface('PersonPublication')
    chart_title = 'Person Publication Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by date',
            'group': 'date',
            'series': ['id']
        }
    ]


class PersonVolunteerExperienceChartView(ChartView):
    datamodel = SQLAInterface('PersonVolunteerExperience')
    chart_title = 'Person Volunteer Experience Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by start_date',
            'group': 'start_date',
            'series': ['id']
        }
    ]


class PointEarningActivityChartView(ChartView):
    datamodel = SQLAInterface('PointEarningActivity')
    chart_title = 'Point Earning Activity Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by timestamp',
            'group': 'timestamp',
            'series': ['id']
        }
    ]


class ProfileUpdateReminderChartView(ChartView):
    datamodel = SQLAInterface('ProfileUpdateReminder')
    chart_title = 'Profile Update Reminder Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by last_reminder_date',
            'group': 'last_reminder_date',
            'series': ['id']
        }
    ]


class UserActivityChartView(ChartView):
    datamodel = SQLAInterface('UserActivity')
    chart_title = 'User Activity Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by timestamp',
            'group': 'timestamp',
            'series': ['id']
        }
    ]


class UserGamificationChartView(ChartView):
    datamodel = SQLAInterface('UserGamification')
    chart_title = 'User Gamification Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by last_point_earned',
            'group': 'last_point_earned',
            'series': ['id']
        }
    ]


class BoardMemberChartView(ChartView):
    datamodel = SQLAInterface('BoardMember')
    chart_title = 'Board Member Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by start_date',
            'group': 'start_date',
            'series': ['id']
        }
    ]


class ContactApplicationChartView(ChartView):
    datamodel = SQLAInterface('ContactApplication')
    chart_title = 'Contact Application Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by application_date',
            'group': 'application_date',
            'series': ['id']
        }
    ]


class DocumentSubmissionChartView(ChartView):
    datamodel = SQLAInterface('DocumentSubmission')
    chart_title = 'Document Submission Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by upload_date',
            'group': 'upload_date',
            'series': ['id']
        }
    ]


class EventChartView(ChartView):
    datamodel = SQLAInterface('Event')
    chart_title = 'Event Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by start_datetime',
            'group': 'start_datetime',
            'series': ['id']
        }
    ]


class ExecutivePositionChartView(ChartView):
    datamodel = SQLAInterface('ExecutivePosition')
    chart_title = 'Executive Position Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by start_date',
            'group': 'start_date',
            'series': ['id']
        }
    ]


class GrantChartView(ChartView):
    datamodel = SQLAInterface('Grant')
    chart_title = 'Grant Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by start_date',
            'group': 'start_date',
            'series': ['id']
        }
    ]


class OnboardingProgressChartView(ChartView):
    datamodel = SQLAInterface('OnboardingProgress')
    chart_title = 'Onboarding Progress Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by completed_at',
            'group': 'completed_at',
            'series': ['id']
        }
    ]


class OrganizationAwardChartView(ChartView):
    datamodel = SQLAInterface('OrganizationAward')
    chart_title = 'Organization Award Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by date_received',
            'group': 'date_received',
            'series': ['id']
        }
    ]


class OrganizationBadgeChartView(ChartView):
    datamodel = SQLAInterface('OrganizationBadge')
    chart_title = 'Organization Badge Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by date_earned',
            'group': 'date_earned',
            'series': ['id']
        }
    ]


class OrganizationContactChartView(ChartView):
    datamodel = SQLAInterface('OrganizationContact')
    chart_title = 'Organization Contact Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by start_date',
            'group': 'start_date',
            'series': ['id']
        }
    ]


class OrganizationDocumentsChartView(ChartView):
    datamodel = SQLAInterface('OrganizationDocuments')
    chart_title = 'Organization Documents Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by upload_date',
            'group': 'upload_date',
            'series': ['id']
        }
    ]


class OrganizationProgramsChartView(ChartView):
    datamodel = SQLAInterface('OrganizationPrograms')
    chart_title = 'Organization Programs Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by start_date',
            'group': 'start_date',
            'series': ['id']
        }
    ]


class OrganizationVerificationChartView(ChartView):
    datamodel = SQLAInterface('OrganizationVerification')
    chart_title = 'Organization Verification Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by registration_date',
            'group': 'registration_date',
            'series': ['id']
        }
    ]


class PersonOrganizationClaimChartView(ChartView):
    datamodel = SQLAInterface('PersonOrganizationClaim')
    chart_title = 'Person Organization Claim Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by claim_date',
            'group': 'claim_date',
            'series': ['id']
        }
    ]


class ProjectChartView(ChartView):
    datamodel = SQLAInterface('Project')
    chart_title = 'Project Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by start_date',
            'group': 'start_date',
            'series': ['id']
        }
    ]


class ReportChartView(ChartView):
    datamodel = SQLAInterface('Report')
    chart_title = 'Report Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by created_date',
            'group': 'created_date',
            'series': ['id']
        }
    ]


class SocialMediaProfileChartView(ChartView):
    datamodel = SQLAInterface('SocialMediaProfile')
    chart_title = 'Social Media Profile Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by token_expiry',
            'group': 'token_expiry',
            'series': ['id']
        }
    ]


class TrainingChartView(ChartView):
    datamodel = SQLAInterface('Training')
    chart_title = 'Training Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by start_date',
            'group': 'start_date',
            'series': ['id']
        }
    ]


class UserChallengeChartView(ChartView):
    datamodel = SQLAInterface('UserChallenge')
    chart_title = 'User Challenge Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by completion_date',
            'group': 'completion_date',
            'series': ['id']
        }
    ]


class VolunteerLogChartView(ChartView):
    datamodel = SQLAInterface('VolunteerLog')
    chart_title = 'Volunteer Log Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by start_date',
            'group': 'start_date',
            'series': ['id']
        }
    ]


class EventRegistrationChartView(ChartView):
    datamodel = SQLAInterface('EventRegistration')
    chart_title = 'Event Registration Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by registration_date',
            'group': 'registration_date',
            'series': ['id']
        }
    ]


class ImpactChartView(ChartView):
    datamodel = SQLAInterface('Impact')
    chart_title = 'Impact Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by date_measured',
            'group': 'date_measured',
            'series': ['id']
        }
    ]


class PersonTrainingChartView(ChartView):
    datamodel = SQLAInterface('PersonTraining')
    chart_title = 'Person Training Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by start_date',
            'group': 'start_date',
            'series': ['id']
        }
    ]


class PjFeedbackChartView(ChartView):
    datamodel = SQLAInterface('PjFeedback')
    chart_title = 'Pj Feedback Chart'
    chart_type = 'LineChart'
    definitions = [
        {
            'label': 'id by date',
            'group': 'date',
            'series': ['id']
        }
    ]

class BadgeAPI(ModelRestApi):
    resource_name = 'badge'
    datamodel = SQLAInterface('Badge')
    list_columns = ['id', 'name', 'description', 'criteria', 'icon']
    show_columns = ['id', 'name', 'description', 'criteria', 'icon']
    add_columns = ['name', 'description', 'criteria', 'icon']
    edit_columns = ['name', 'description', 'criteria', 'icon']
    # Add any API-specific configuration here

class ContactTypeAPI(ModelRestApi):
    resource_name = 'contact type'
    datamodel = SQLAInterface('ContactType')
    list_columns = ['id', 'name', 'description', 'is_digital', 'requires_verification', 'max_length', 'icon_url', 'created_at', 'updated_at']
    show_columns = ['id', 'name', 'description', 'is_digital', 'requires_verification', 'max_length', 'icon_url', 'created_at', 'updated_at']
    add_columns = ['name', 'description', 'is_digital', 'requires_verification', 'max_length', 'icon_url', 'created_at', 'updated_at']
    edit_columns = ['name', 'description', 'is_digital', 'requires_verification', 'max_length', 'icon_url', 'created_at', 'updated_at']
    # Add any API-specific configuration here

class CountryAPI(ModelRestApi):
    resource_name = 'country'
    datamodel = SQLAInterface('Country')
    list_columns = ['id', 'iso_alpha2', 'iso_alpha3', 'iso_numeric', 'fips_code', 'name', 'capital', 'areainsqkm', 'population', 'continent', 'tld', 'currencycode', 'currencyname', 'phone', 'postalcode', 'postalcoderegex', 'languages', 'neighbors', 'equivfipscode', 'flag']
    show_columns = ['id', 'iso_alpha2', 'iso_alpha3', 'iso_numeric', 'fips_code', 'name', 'capital', 'areainsqkm', 'population', 'continent', 'tld', 'currencycode', 'currencyname', 'phone', 'postalcode', 'postalcoderegex', 'languages', 'neighbors', 'equivfipscode', 'flag']
    add_columns = ['iso_alpha2', 'iso_alpha3', 'iso_numeric', 'fips_code', 'name', 'capital', 'areainsqkm', 'population', 'continent', 'tld', 'currencycode', 'currencyname', 'phone', 'postalcode', 'postalcoderegex', 'languages', 'neighbors', 'equivfipscode', 'flag']
    edit_columns = ['iso_alpha2', 'iso_alpha3', 'iso_numeric', 'fips_code', 'name', 'capital', 'areainsqkm', 'population', 'continent', 'tld', 'currencycode', 'currencyname', 'phone', 'postalcode', 'postalcoderegex', 'languages', 'neighbors', 'equivfipscode', 'flag']
    # Add any API-specific configuration here

class CurrencyAPI(ModelRestApi):
    resource_name = 'currency'
    datamodel = SQLAInterface('Currency')
    list_columns = ['id', 'name', 'symbol', 'numeric_code', 'full_name']
    show_columns = ['id', 'name', 'symbol', 'numeric_code', 'full_name']
    add_columns = ['name', 'symbol', 'numeric_code', 'full_name']
    edit_columns = ['name', 'symbol', 'numeric_code', 'full_name']
    # Add any API-specific configuration here

class LanguagecodesAPI(ModelRestApi):
    resource_name = 'languagecodes'
    datamodel = SQLAInterface('Languagecodes')
    list_columns = ['id', 'iso_639_3', 'iso_639_2', 'iso_639_1', 'name']
    show_columns = ['id', 'iso_639_3', 'iso_639_2', 'iso_639_1', 'name']
    add_columns = ['iso_639_3', 'iso_639_2', 'iso_639_1', 'name']
    edit_columns = ['iso_639_3', 'iso_639_2', 'iso_639_1', 'name']
    # Add any API-specific configuration here

class PersonAPI(ModelRestApi):
    resource_name = 'person'
    datamodel = SQLAInterface('Person')
    list_columns = ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']
    show_columns = ['id', 'first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']
    add_columns = ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']
    edit_columns = ['first_name', 'middle_name', 'last_name', 'full_name', 'nick_name', 'headline', 'location', 'summary', 'email', 'phone', 'date_of_birth', 'city', 'state_province', 'postal_code', 'country', 'bio', 'skills_description', 'interests', 'is_volunteer', 'is_staff', 'onboarding_step', 'profile_completion', 'last_profile_update', 'points', 'level', 'social_media_imported']
    # Add any API-specific configuration here

class SkillCategoryAPI(ModelRestApi):
    resource_name = 'skill category'
    datamodel = SQLAInterface('SkillCategory')
    list_columns = ['id', 'name', 'description']
    show_columns = ['id', 'name', 'description']
    add_columns = ['name', 'description']
    edit_columns = ['name', 'description']
    # Add any API-specific configuration here

class TagAPI(ModelRestApi):
    resource_name = 'tag'
    datamodel = SQLAInterface('Tag')
    list_columns = ['id', 'name']
    show_columns = ['id', 'name']
    add_columns = ['name']
    edit_columns = ['name']
    # Add any API-specific configuration here

class ContactAPI(ModelRestApi):
    resource_name = 'contact'
    datamodel = SQLAInterface('Contact')
    list_columns = ['id', 'person_id_fk', 'contact_type_id_fk', 'contact_value', 'priority', 'best_time_to_contact_start', 'best_time_to_contact_end', 'active_from_date', 'active_to_date', 'for_business_use', 'for_personal_use', 'do_not_use', 'is_active', 'is_blocked', 'is_verified', 'notes']
    show_columns = ['id', 'person_id_fk', 'contact_type_id_fk', 'contact_value', 'priority', 'best_time_to_contact_start', 'best_time_to_contact_end', 'active_from_date', 'active_to_date', 'for_business_use', 'for_personal_use', 'do_not_use', 'is_active', 'is_blocked', 'is_verified', 'notes']
    add_columns = ['person_id_fk', 'contact_type_id_fk', 'contact_value', 'priority', 'best_time_to_contact_start', 'best_time_to_contact_end', 'active_from_date', 'active_to_date', 'for_business_use', 'for_personal_use', 'do_not_use', 'is_active', 'is_blocked', 'is_verified', 'notes']
    edit_columns = ['person_id_fk', 'contact_type_id_fk', 'contact_value', 'priority', 'best_time_to_contact_start', 'best_time_to_contact_end', 'active_from_date', 'active_to_date', 'for_business_use', 'for_personal_use', 'do_not_use', 'is_active', 'is_blocked', 'is_verified', 'notes']
    # Add any API-specific configuration here

class GamificationChallengeAPI(ModelRestApi):
    resource_name = 'gamification challenge'
    datamodel = SQLAInterface('GamificationChallenge')
    list_columns = ['id', 'name', 'description', 'points_reward', 'badge_reward_id_fk', 'start_date', 'end_date']
    show_columns = ['id', 'name', 'description', 'points_reward', 'badge_reward_id_fk', 'start_date', 'end_date']
    add_columns = ['name', 'description', 'points_reward', 'badge_reward_id_fk', 'start_date', 'end_date']
    edit_columns = ['name', 'description', 'points_reward', 'badge_reward_id_fk', 'start_date', 'end_date']
    # Add any API-specific configuration here

class LeaderboardAPI(ModelRestApi):
    resource_name = 'leaderboard'
    datamodel = SQLAInterface('Leaderboard')
    list_columns = ['id', 'person_id_fk', 'score', 'last_updated']
    show_columns = ['id', 'person_id_fk', 'score', 'last_updated']
    add_columns = ['person_id_fk', 'score', 'last_updated']
    edit_columns = ['person_id_fk', 'score', 'last_updated']
    # Add any API-specific configuration here

class MessageAPI(ModelRestApi):
    resource_name = 'message'
    datamodel = SQLAInterface('Message')
    list_columns = ['id', 'sender_id_fk', 'recipient_id_fk', 'subject', 'body', 'sent_date', 'read_date']
    show_columns = ['id', 'sender_id_fk', 'recipient_id_fk', 'subject', 'body', 'sent_date', 'read_date']
    add_columns = ['sender_id_fk', 'recipient_id_fk', 'subject', 'body', 'sent_date', 'read_date']
    edit_columns = ['sender_id_fk', 'recipient_id_fk', 'subject', 'body', 'sent_date', 'read_date']
    # Add any API-specific configuration here

class NotificationAPI(ModelRestApi):
    resource_name = 'notification'
    datamodel = SQLAInterface('Notification')
    list_columns = ['id', 'person_id_fk', 'message', 'notification_type', 'created_date', 'read_date']
    show_columns = ['id', 'person_id_fk', 'message', 'notification_type', 'created_date', 'read_date']
    add_columns = ['person_id_fk', 'message', 'notification_type', 'created_date', 'read_date']
    edit_columns = ['person_id_fk', 'message', 'notification_type', 'created_date', 'read_date']
    # Add any API-specific configuration here

class OrganizationAPI(ModelRestApi):
    resource_name = 'organization'
    datamodel = SQLAInterface('Organization')
    list_columns = ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']
    show_columns = ['id', 'name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']
    add_columns = ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']
    edit_columns = ['name', 'legal_name', 'org_type', 'org_cat', 'status', 'industry', 'website', 'is_verified', 'description', 'mission_statement', 'size', 'revenue', 'founded_date', 'country_of_operation_id_fk', 'logo', 'social_media_links', 'tax_id', 'registration_number', 'seeking_funding', 'providing_funding', 'authorized_representative', 'legal_structure', 'compliance_status', 'financial_year_end', 'last_audit_date', 'auditor_name', 'phone_number', 'email', 'address', 'city', 'state', 'country', 'postal_code', 'board_members', 'governance_structure', 'risk_assessment', 'insurance_coverage', 'compliance_certifications', 'ethics_policy', 'sustainability_policy', 'primary_funding_source', 'secondary_funding_source', 'main_areas_of_operation', 'key_programs', 'beneficiary_info', 'major_donors', 'partnerships_affiliations', 'onboarding_step', 'profile_completion', 'last_profile_update', 'associated_people_id_fk']
    # Add any API-specific configuration here

class PersonBadgeAPI(ModelRestApi):
    resource_name = 'person badge'
    datamodel = SQLAInterface('PersonBadge')
    list_columns = ['person_id_fk', 'badge_id_fk', 'date_earned']
    show_columns = ['person_id_fk', 'badge_id_fk', 'date_earned']
    add_columns = ['person_id_fk', 'badge_id_fk', 'date_earned']
    edit_columns = ['person_id_fk', 'badge_id_fk', 'date_earned']
    # Add any API-specific configuration here

class PersonCertificationAPI(ModelRestApi):
    resource_name = 'person certification'
    datamodel = SQLAInterface('PersonCertification')
    list_columns = ['id', 'person_id_fk', 'name', 'issuing_organization', 'issue_date', 'expiration_date', 'credential_id', 'credential_url']
    show_columns = ['id', 'person_id_fk', 'name', 'issuing_organization', 'issue_date', 'expiration_date', 'credential_id', 'credential_url']
    add_columns = ['person_id_fk', 'name', 'issuing_organization', 'issue_date', 'expiration_date', 'credential_id', 'credential_url']
    edit_columns = ['person_id_fk', 'name', 'issuing_organization', 'issue_date', 'expiration_date', 'credential_id', 'credential_url']
    # Add any API-specific configuration here

class PersonCourseAPI(ModelRestApi):
    resource_name = 'person course'
    datamodel = SQLAInterface('PersonCourse')
    list_columns = ['id', 'person_id_fk', 'name', 'institution', 'completion_date', 'description']
    show_columns = ['id', 'person_id_fk', 'name', 'institution', 'completion_date', 'description']
    add_columns = ['person_id_fk', 'name', 'institution', 'completion_date', 'description']
    edit_columns = ['person_id_fk', 'name', 'institution', 'completion_date', 'description']
    # Add any API-specific configuration here

class PersonEducationAPI(ModelRestApi):
    resource_name = 'person education'
    datamodel = SQLAInterface('PersonEducation')
    list_columns = ['id', 'person_id_fk', 'school_name', 'degree', 'field_of_study', 'start_date', 'end_date', 'description']
    show_columns = ['id', 'person_id_fk', 'school_name', 'degree', 'field_of_study', 'start_date', 'end_date', 'description']
    add_columns = ['person_id_fk', 'school_name', 'degree', 'field_of_study', 'start_date', 'end_date', 'description']
    edit_columns = ['person_id_fk', 'school_name', 'degree', 'field_of_study', 'start_date', 'end_date', 'description']
    # Add any API-specific configuration here

class PersonExperienceAPI(ModelRestApi):
    resource_name = 'person experience'
    datamodel = SQLAInterface('PersonExperience')
    list_columns = ['id', 'person_id_fk', 'job_title', 'company_name', 'location', 'start_date', 'end_date', 'description', 'awards']
    show_columns = ['id', 'person_id_fk', 'job_title', 'company_name', 'location', 'start_date', 'end_date', 'description', 'awards']
    add_columns = ['person_id_fk', 'job_title', 'company_name', 'location', 'start_date', 'end_date', 'description', 'awards']
    edit_columns = ['person_id_fk', 'job_title', 'company_name', 'location', 'start_date', 'end_date', 'description', 'awards']
    # Add any API-specific configuration here

class PersonHonorAwardAPI(ModelRestApi):
    resource_name = 'person honor award'
    datamodel = SQLAInterface('PersonHonorAward')
    list_columns = ['id', 'person_id_fk', 'title', 'issuer', 'date_received', 'description']
    show_columns = ['id', 'person_id_fk', 'title', 'issuer', 'date_received', 'description']
    add_columns = ['person_id_fk', 'title', 'issuer', 'date_received', 'description']
    edit_columns = ['person_id_fk', 'title', 'issuer', 'date_received', 'description']
    # Add any API-specific configuration here

class PersonLanguageAPI(ModelRestApi):
    resource_name = 'person language'
    datamodel = SQLAInterface('PersonLanguage')
    list_columns = ['id', 'person_id_fk', 'name', 'proficiency']
    show_columns = ['id', 'person_id_fk', 'name', 'proficiency']
    add_columns = ['person_id_fk', 'name', 'proficiency']
    edit_columns = ['person_id_fk', 'name', 'proficiency']
    # Add any API-specific configuration here

class PersonOrganizationMembershipAPI(ModelRestApi):
    resource_name = 'person organization membership'
    datamodel = SQLAInterface('PersonOrganizationMembership')
    list_columns = ['id', 'person_id_fk', 'organization_name', 'role', 'start_date', 'end_date', 'description']
    show_columns = ['id', 'person_id_fk', 'organization_name', 'role', 'start_date', 'end_date', 'description']
    add_columns = ['person_id_fk', 'organization_name', 'role', 'start_date', 'end_date', 'description']
    edit_columns = ['person_id_fk', 'organization_name', 'role', 'start_date', 'end_date', 'description']
    # Add any API-specific configuration here

class PersonPatentAPI(ModelRestApi):
    resource_name = 'person patent'
    datamodel = SQLAInterface('PersonPatent')
    list_columns = ['id', 'person_id_fk', 'title', 'patent_office', 'patent_number', 'issue_date', 'description']
    show_columns = ['id', 'person_id_fk', 'title', 'patent_office', 'patent_number', 'issue_date', 'description']
    add_columns = ['person_id_fk', 'title', 'patent_office', 'patent_number', 'issue_date', 'description']
    edit_columns = ['person_id_fk', 'title', 'patent_office', 'patent_number', 'issue_date', 'description']
    # Add any API-specific configuration here

class PersonProjectAPI(ModelRestApi):
    resource_name = 'person project'
    datamodel = SQLAInterface('PersonProject')
    list_columns = ['id', 'person_id_fk', 'name', 'description', 'start_date', 'end_date', 'project_url']
    show_columns = ['id', 'person_id_fk', 'name', 'description', 'start_date', 'end_date', 'project_url']
    add_columns = ['person_id_fk', 'name', 'description', 'start_date', 'end_date', 'project_url']
    edit_columns = ['person_id_fk', 'name', 'description', 'start_date', 'end_date', 'project_url']
    # Add any API-specific configuration here

class PersonPublicationAPI(ModelRestApi):
    resource_name = 'person publication'
    datamodel = SQLAInterface('PersonPublication')
    list_columns = ['id', 'person_id_fk', 'title', 'publisher', 'date', 'url', 'description']
    show_columns = ['id', 'person_id_fk', 'title', 'publisher', 'date', 'url', 'description']
    add_columns = ['person_id_fk', 'title', 'publisher', 'date', 'url', 'description']
    edit_columns = ['person_id_fk', 'title', 'publisher', 'date', 'url', 'description']
    # Add any API-specific configuration here

class PersonVolunteerExperienceAPI(ModelRestApi):
    resource_name = 'person volunteer experience'
    datamodel = SQLAInterface('PersonVolunteerExperience')
    list_columns = ['id', 'person_id_fk', 'role', 'organization', 'cause', 'start_date', 'end_date', 'description']
    show_columns = ['id', 'person_id_fk', 'role', 'organization', 'cause', 'start_date', 'end_date', 'description']
    add_columns = ['person_id_fk', 'role', 'organization', 'cause', 'start_date', 'end_date', 'description']
    edit_columns = ['person_id_fk', 'role', 'organization', 'cause', 'start_date', 'end_date', 'description']
    # Add any API-specific configuration here

class PointEarningActivityAPI(ModelRestApi):
    resource_name = 'point earning activity'
    datamodel = SQLAInterface('PointEarningActivity')
    list_columns = ['id', 'person_id_fk', 'activity_type', 'points_earned', 'timestamp']
    show_columns = ['id', 'person_id_fk', 'activity_type', 'points_earned', 'timestamp']
    add_columns = ['person_id_fk', 'activity_type', 'points_earned', 'timestamp']
    edit_columns = ['person_id_fk', 'activity_type', 'points_earned', 'timestamp']
    # Add any API-specific configuration here

class ProfileUpdateReminderAPI(ModelRestApi):
    resource_name = 'profile update reminder'
    datamodel = SQLAInterface('ProfileUpdateReminder')
    list_columns = ['id', 'person_id_fk', 'last_reminder_date', 'reminder_count', 'next_reminder_date']
    show_columns = ['id', 'person_id_fk', 'last_reminder_date', 'reminder_count', 'next_reminder_date']
    add_columns = ['person_id_fk', 'last_reminder_date', 'reminder_count', 'next_reminder_date']
    edit_columns = ['person_id_fk', 'last_reminder_date', 'reminder_count', 'next_reminder_date']
    # Add any API-specific configuration here

class SkillAPI(ModelRestApi):
    resource_name = 'skill'
    datamodel = SQLAInterface('Skill')
    list_columns = ['id', 'name', 'skill_category_id_fk', 'description']
    show_columns = ['id', 'name', 'skill_category_id_fk', 'description']
    add_columns = ['name', 'skill_category_id_fk', 'description']
    edit_columns = ['name', 'skill_category_id_fk', 'description']
    # Add any API-specific configuration here

class TimezoneAPI(ModelRestApi):
    resource_name = 'timezone'
    datamodel = SQLAInterface('Timezone')
    list_columns = ['id', 'country_id_fk', 'timezonename', 'comments']
    show_columns = ['id', 'country_id_fk', 'timezonename', 'comments']
    add_columns = ['country_id_fk', 'timezonename', 'comments']
    edit_columns = ['country_id_fk', 'timezonename', 'comments']
    # Add any API-specific configuration here

class UserActivityAPI(ModelRestApi):
    resource_name = 'user activity'
    datamodel = SQLAInterface('UserActivity')
    list_columns = ['id', 'person_id_fk', 'activity_type', 'timestamp', 'details']
    show_columns = ['id', 'person_id_fk', 'activity_type', 'timestamp', 'details']
    add_columns = ['person_id_fk', 'activity_type', 'timestamp', 'details']
    edit_columns = ['person_id_fk', 'activity_type', 'timestamp', 'details']
    # Add any API-specific configuration here

class UserGamificationAPI(ModelRestApi):
    resource_name = 'user gamification'
    datamodel = SQLAInterface('UserGamification')
    list_columns = ['id', 'user_id_fk', 'points', 'level', 'last_point_earned', 'points_to_next_level']
    show_columns = ['id', 'user_id_fk', 'points', 'level', 'last_point_earned', 'points_to_next_level']
    add_columns = ['user_id_fk', 'points', 'level', 'last_point_earned', 'points_to_next_level']
    edit_columns = ['user_id_fk', 'points', 'level', 'last_point_earned', 'points_to_next_level']
    # Add any API-specific configuration here

class BoardMemberAPI(ModelRestApi):
    resource_name = 'board member'
    datamodel = SQLAInterface('BoardMember')
    list_columns = ['id', 'organization_id_fk', 'person_id_fk', 'position', 'start_date', 'end_date']
    show_columns = ['id', 'organization_id_fk', 'person_id_fk', 'position', 'start_date', 'end_date']
    add_columns = ['organization_id_fk', 'person_id_fk', 'position', 'start_date', 'end_date']
    edit_columns = ['organization_id_fk', 'person_id_fk', 'position', 'start_date', 'end_date']
    # Add any API-specific configuration here

class ContactApplicationAPI(ModelRestApi):
    resource_name = 'contact application'
    datamodel = SQLAInterface('ContactApplication')
    list_columns = ['id', 'person_id_fk', 'organization_id_fk', 'position', 'message', 'application_date', 'status', 'review_date', 'review_notes']
    show_columns = ['id', 'person_id_fk', 'organization_id_fk', 'position', 'message', 'application_date', 'status', 'review_date', 'review_notes']
    add_columns = ['person_id_fk', 'organization_id_fk', 'position', 'message', 'application_date', 'status', 'review_date', 'review_notes']
    edit_columns = ['person_id_fk', 'organization_id_fk', 'position', 'message', 'application_date', 'status', 'review_date', 'review_notes']
    # Add any API-specific configuration here

class DocumentSubmissionAPI(ModelRestApi):
    resource_name = 'document submission'
    datamodel = SQLAInterface('DocumentSubmission')
    list_columns = ['id', 'organization_id_fk', 'document_type', 'document_name', 'file_path', 'upload_date', 'status', 'next_status', 'review_notes', 'review_date']
    show_columns = ['id', 'organization_id_fk', 'document_type', 'document_name', 'file_path', 'upload_date', 'status', 'next_status', 'review_notes', 'review_date']
    add_columns = ['organization_id_fk', 'document_type', 'document_name', 'file_path', 'upload_date', 'status', 'next_status', 'review_notes', 'review_date']
    edit_columns = ['organization_id_fk', 'document_type', 'document_name', 'file_path', 'upload_date', 'status', 'next_status', 'review_notes', 'review_date']
    # Add any API-specific configuration here

class EventAPI(ModelRestApi):
    resource_name = 'event'
    datamodel = SQLAInterface('Event')
    list_columns = ['id', 'organization_id_fk', 'name', 'description', 'start_datetime', 'end_datetime', 'location', 'is_virtual', 'max_participants']
    show_columns = ['id', 'organization_id_fk', 'name', 'description', 'start_datetime', 'end_datetime', 'location', 'is_virtual', 'max_participants']
    add_columns = ['organization_id_fk', 'name', 'description', 'start_datetime', 'end_datetime', 'location', 'is_virtual', 'max_participants']
    edit_columns = ['organization_id_fk', 'name', 'description', 'start_datetime', 'end_datetime', 'location', 'is_virtual', 'max_participants']
    # Add any API-specific configuration here

class ExecutivePositionAPI(ModelRestApi):
    resource_name = 'executive position'
    datamodel = SQLAInterface('ExecutivePosition')
    list_columns = ['id', 'organization_id_fk', 'person_id_fk', 'title', 'start_date', 'end_date']
    show_columns = ['id', 'organization_id_fk', 'person_id_fk', 'title', 'start_date', 'end_date']
    add_columns = ['organization_id_fk', 'person_id_fk', 'title', 'start_date', 'end_date']
    edit_columns = ['organization_id_fk', 'person_id_fk', 'title', 'start_date', 'end_date']
    # Add any API-specific configuration here

class GrantAPI(ModelRestApi):
    resource_name = 'grant'
    datamodel = SQLAInterface('Grant')
    list_columns = ['id', 'donor_id_fk', 'recipient_id_fk', 'amount', 'start_date', 'end_date', 'status', 'description']
    show_columns = ['id', 'donor_id_fk', 'recipient_id_fk', 'amount', 'start_date', 'end_date', 'status', 'description']
    add_columns = ['donor_id_fk', 'recipient_id_fk', 'amount', 'start_date', 'end_date', 'status', 'description']
    edit_columns = ['donor_id_fk', 'recipient_id_fk', 'amount', 'start_date', 'end_date', 'status', 'description']
    # Add any API-specific configuration here

class OnboardingProgressAPI(ModelRestApi):
    resource_name = 'onboarding progress'
    datamodel = SQLAInterface('OnboardingProgress')
    list_columns = ['id', 'user_id_fk', 'organization_id_fk', 'step', 'completed_at']
    show_columns = ['id', 'user_id_fk', 'organization_id_fk', 'step', 'completed_at']
    add_columns = ['user_id_fk', 'organization_id_fk', 'step', 'completed_at']
    edit_columns = ['user_id_fk', 'organization_id_fk', 'step', 'completed_at']
    # Add any API-specific configuration here

class OrganizationAwardAPI(ModelRestApi):
    resource_name = 'organization award'
    datamodel = SQLAInterface('OrganizationAward')
    list_columns = ['id', 'organization_id_fk', 'name', 'awarding_body', 'date_received', 'description']
    show_columns = ['id', 'organization_id_fk', 'name', 'awarding_body', 'date_received', 'description']
    add_columns = ['organization_id_fk', 'name', 'awarding_body', 'date_received', 'description']
    edit_columns = ['organization_id_fk', 'name', 'awarding_body', 'date_received', 'description']
    # Add any API-specific configuration here

class OrganizationBadgeAPI(ModelRestApi):
    resource_name = 'organization badge'
    datamodel = SQLAInterface('OrganizationBadge')
    list_columns = ['id', 'organization_id_fk', 'badge_id_fk', 'date_earned']
    show_columns = ['id', 'organization_id_fk', 'badge_id_fk', 'date_earned']
    add_columns = ['organization_id_fk', 'badge_id_fk', 'date_earned']
    edit_columns = ['organization_id_fk', 'badge_id_fk', 'date_earned']
    # Add any API-specific configuration here

class OrganizationClimateCategoriesAPI(ModelRestApi):
    resource_name = 'organization climate categories'
    datamodel = SQLAInterface('OrganizationClimateCategories')
    list_columns = ['organization_id_fk', 'climate_category']
    show_columns = ['organization_id_fk', 'climate_category']
    add_columns = ['organization_id_fk', 'climate_category']
    edit_columns = ['organization_id_fk', 'climate_category']
    # Add any API-specific configuration here

class OrganizationContactAPI(ModelRestApi):
    resource_name = 'organization contact'
    datamodel = SQLAInterface('OrganizationContact')
    list_columns = ['id', 'organization_id_fk', 'person_id_fk', 'org_email', 'org_phone', 'position', 'department', 'start_date', 'end_date', 'is_primary', 'status', 'notes']
    show_columns = ['id', 'organization_id_fk', 'person_id_fk', 'org_email', 'org_phone', 'position', 'department', 'start_date', 'end_date', 'is_primary', 'status', 'notes']
    add_columns = ['organization_id_fk', 'person_id_fk', 'org_email', 'org_phone', 'position', 'department', 'start_date', 'end_date', 'is_primary', 'status', 'notes']
    edit_columns = ['organization_id_fk', 'person_id_fk', 'org_email', 'org_phone', 'position', 'department', 'start_date', 'end_date', 'is_primary', 'status', 'notes']
    # Add any API-specific configuration here

class OrganizationDocumentsAPI(ModelRestApi):
    resource_name = 'organization documents'
    datamodel = SQLAInterface('OrganizationDocuments')
    list_columns = ['id', 'organization_id', 'document_type', 'document_name', 'document_path', 'upload_date', 'document_summary']
    show_columns = ['id', 'organization_id', 'document_type', 'document_name', 'document_path', 'upload_date', 'document_summary']
    add_columns = ['organization_id', 'document_type', 'document_name', 'document_path', 'upload_date', 'document_summary']
    edit_columns = ['organization_id', 'document_type', 'document_name', 'document_path', 'upload_date', 'document_summary']
    # Add any API-specific configuration here

class OrganizationHierarchyAPI(ModelRestApi):
    resource_name = 'organization hierarchy'
    datamodel = SQLAInterface('OrganizationHierarchy')
    list_columns = ['id', 'parent_org_id_fk', 'child_org_id_fk', 'relationship_type']
    show_columns = ['id', 'parent_org_id_fk', 'child_org_id_fk', 'relationship_type']
    add_columns = ['parent_org_id_fk', 'child_org_id_fk', 'relationship_type']
    edit_columns = ['parent_org_id_fk', 'child_org_id_fk', 'relationship_type']
    # Add any API-specific configuration here

class OrganizationProfileAPI(ModelRestApi):
    resource_name = 'organization profile'
    datamodel = SQLAInterface('OrganizationProfile')
    list_columns = ['id', 'organization_id_fk', 'funding_focus_areas', 'average_grant_size', 'grant_making_process', 'funding_restrictions', 'focus_areas', 'target_beneficiaries', 'geographic_reach', 'years_of_operation', 'total_beneficiaries_last_year', 'annual_budget', 'num_employees', 'num_volunteers', 'last_year_revenue', 'last_year_expenditure']
    show_columns = ['id', 'organization_id_fk', 'funding_focus_areas', 'average_grant_size', 'grant_making_process', 'funding_restrictions', 'focus_areas', 'target_beneficiaries', 'geographic_reach', 'years_of_operation', 'total_beneficiaries_last_year', 'annual_budget', 'num_employees', 'num_volunteers', 'last_year_revenue', 'last_year_expenditure']
    add_columns = ['organization_id_fk', 'funding_focus_areas', 'average_grant_size', 'grant_making_process', 'funding_restrictions', 'focus_areas', 'target_beneficiaries', 'geographic_reach', 'years_of_operation', 'total_beneficiaries_last_year', 'annual_budget', 'num_employees', 'num_volunteers', 'last_year_revenue', 'last_year_expenditure']
    edit_columns = ['organization_id_fk', 'funding_focus_areas', 'average_grant_size', 'grant_making_process', 'funding_restrictions', 'focus_areas', 'target_beneficiaries', 'geographic_reach', 'years_of_operation', 'total_beneficiaries_last_year', 'annual_budget', 'num_employees', 'num_volunteers', 'last_year_revenue', 'last_year_expenditure']
    # Add any API-specific configuration here

class OrganizationProgramsAPI(ModelRestApi):
    resource_name = 'organization programs'
    datamodel = SQLAInterface('OrganizationPrograms')
    list_columns = ['id', 'organization_id', 'program_name', 'program_description', 'start_date', 'end_date', 'budget', 'impact_assessment']
    show_columns = ['id', 'organization_id', 'program_name', 'program_description', 'start_date', 'end_date', 'budget', 'impact_assessment']
    add_columns = ['organization_id', 'program_name', 'program_description', 'start_date', 'end_date', 'budget', 'impact_assessment']
    edit_columns = ['organization_id', 'program_name', 'program_description', 'start_date', 'end_date', 'budget', 'impact_assessment']
    # Add any API-specific configuration here

class OrganizationSdgsAPI(ModelRestApi):
    resource_name = 'organization sdgs'
    datamodel = SQLAInterface('OrganizationSdgs')
    list_columns = ['organization_id_fk', 'sdg']
    show_columns = ['organization_id_fk', 'sdg']
    add_columns = ['organization_id_fk', 'sdg']
    edit_columns = ['organization_id_fk', 'sdg']
    # Add any API-specific configuration here

class OrganizationTagAPI(ModelRestApi):
    resource_name = 'organization tag'
    datamodel = SQLAInterface('OrganizationTag')
    list_columns = ['id', 'organization_id_fk', 'tag_id_fk']
    show_columns = ['id', 'organization_id_fk', 'tag_id_fk']
    add_columns = ['organization_id_fk', 'tag_id_fk']
    edit_columns = ['organization_id_fk', 'tag_id_fk']
    # Add any API-specific configuration here

class OrganizationVerificationAPI(ModelRestApi):
    resource_name = 'organization verification'
    datamodel = SQLAInterface('OrganizationVerification')
    list_columns = ['id', 'organization_id_fk', 'registration_number', 'registration_date', 'registering_authority', 'registration_expiry', 'last_verification_date', 'verification_status', 'verification_notes']
    show_columns = ['id', 'organization_id_fk', 'registration_number', 'registration_date', 'registering_authority', 'registration_expiry', 'last_verification_date', 'verification_status', 'verification_notes']
    add_columns = ['organization_id_fk', 'registration_number', 'registration_date', 'registering_authority', 'registration_expiry', 'last_verification_date', 'verification_status', 'verification_notes']
    edit_columns = ['organization_id_fk', 'registration_number', 'registration_date', 'registering_authority', 'registration_expiry', 'last_verification_date', 'verification_status', 'verification_notes']
    # Add any API-specific configuration here

class PersonOrganizationClaimAPI(ModelRestApi):
    resource_name = 'person organization claim'
    datamodel = SQLAInterface('PersonOrganizationClaim')
    list_columns = ['id', 'person_id', 'organization_id', 'claim_type', 'status', 'claim_date', 'review_date']
    show_columns = ['id', 'person_id', 'organization_id', 'claim_type', 'status', 'claim_date', 'review_date']
    add_columns = ['person_id', 'organization_id', 'claim_type', 'status', 'claim_date', 'review_date']
    edit_columns = ['person_id', 'organization_id', 'claim_type', 'status', 'claim_date', 'review_date']
    # Add any API-specific configuration here

class PersonSkillAPI(ModelRestApi):
    resource_name = 'person skill'
    datamodel = SQLAInterface('PersonSkill')
    list_columns = ['id', 'person_id_fk', 'skill_id_fk', 'proficiency_level', 'endorsements']
    show_columns = ['id', 'person_id_fk', 'skill_id_fk', 'proficiency_level', 'endorsements']
    add_columns = ['person_id_fk', 'skill_id_fk', 'proficiency_level', 'endorsements']
    edit_columns = ['person_id_fk', 'skill_id_fk', 'proficiency_level', 'endorsements']
    # Add any API-specific configuration here

class ProjectAPI(ModelRestApi):
    resource_name = 'project'
    datamodel = SQLAInterface('Project')
    list_columns = ['id', 'organization_id_fk', 'name', 'description', 'start_date', 'end_date', 'budget', 'status', 'beneficiaries', 'outcomes']
    show_columns = ['id', 'organization_id_fk', 'name', 'description', 'start_date', 'end_date', 'budget', 'status', 'beneficiaries', 'outcomes']
    add_columns = ['organization_id_fk', 'name', 'description', 'start_date', 'end_date', 'budget', 'status', 'beneficiaries', 'outcomes']
    edit_columns = ['organization_id_fk', 'name', 'description', 'start_date', 'end_date', 'budget', 'status', 'beneficiaries', 'outcomes']
    # Add any API-specific configuration here

class ReportAPI(ModelRestApi):
    resource_name = 'report'
    datamodel = SQLAInterface('Report')
    list_columns = ['id', 'organization_id_fk', 'title', 'description', 'file_path', 'created_date', 'report_type']
    show_columns = ['id', 'organization_id_fk', 'title', 'description', 'file_path', 'created_date', 'report_type']
    add_columns = ['organization_id_fk', 'title', 'description', 'file_path', 'created_date', 'report_type']
    edit_columns = ['organization_id_fk', 'title', 'description', 'file_path', 'created_date', 'report_type']
    # Add any API-specific configuration here

class SocialMediaProfileAPI(ModelRestApi):
    resource_name = 'social media profile'
    datamodel = SQLAInterface('SocialMediaProfile')
    list_columns = ['id', 'person_id_fk', 'org_id_fk', 'platform', 'profile_id', 'access_token', 'refresh_token', 'token_expiry']
    show_columns = ['id', 'person_id_fk', 'org_id_fk', 'platform', 'profile_id', 'access_token', 'refresh_token', 'token_expiry']
    add_columns = ['person_id_fk', 'org_id_fk', 'platform', 'profile_id', 'access_token', 'refresh_token', 'token_expiry']
    edit_columns = ['person_id_fk', 'org_id_fk', 'platform', 'profile_id', 'access_token', 'refresh_token', 'token_expiry']
    # Add any API-specific configuration here

class TrainingAPI(ModelRestApi):
    resource_name = 'training'
    datamodel = SQLAInterface('Training')
    list_columns = ['id', 'offering_org_id_fk', 'name', 'description', 'start_date', 'end_date', 'is_certified']
    show_columns = ['id', 'offering_org_id_fk', 'name', 'description', 'start_date', 'end_date', 'is_certified']
    add_columns = ['offering_org_id_fk', 'name', 'description', 'start_date', 'end_date', 'is_certified']
    edit_columns = ['offering_org_id_fk', 'name', 'description', 'start_date', 'end_date', 'is_certified']
    # Add any API-specific configuration here

class UserChallengeAPI(ModelRestApi):
    resource_name = 'user challenge'
    datamodel = SQLAInterface('UserChallenge')
    list_columns = ['id', 'person_id_fk', 'challenge_id_fk', 'completed', 'completion_date']
    show_columns = ['id', 'person_id_fk', 'challenge_id_fk', 'completed', 'completion_date']
    add_columns = ['person_id_fk', 'challenge_id_fk', 'completed', 'completion_date']
    edit_columns = ['person_id_fk', 'challenge_id_fk', 'completed', 'completion_date']
    # Add any API-specific configuration here

class VolunteerLogAPI(ModelRestApi):
    resource_name = 'volunteer log'
    datamodel = SQLAInterface('VolunteerLog')
    list_columns = ['id', 'person_id_fk', 'organization_id_fk', 'start_date', 'end_date', 'hours_contributed', 'role', 'skills_used']
    show_columns = ['id', 'person_id_fk', 'organization_id_fk', 'start_date', 'end_date', 'hours_contributed', 'role', 'skills_used']
    add_columns = ['person_id_fk', 'organization_id_fk', 'start_date', 'end_date', 'hours_contributed', 'role', 'skills_used']
    edit_columns = ['person_id_fk', 'organization_id_fk', 'start_date', 'end_date', 'hours_contributed', 'role', 'skills_used']
    # Add any API-specific configuration here

class EventRegistrationAPI(ModelRestApi):
    resource_name = 'event registration'
    datamodel = SQLAInterface('EventRegistration')
    list_columns = ['id', 'event_id_fk', 'person_id_fk', 'registration_date', 'attended']
    show_columns = ['id', 'event_id_fk', 'person_id_fk', 'registration_date', 'attended']
    add_columns = ['event_id_fk', 'person_id_fk', 'registration_date', 'attended']
    edit_columns = ['event_id_fk', 'person_id_fk', 'registration_date', 'attended']
    # Add any API-specific configuration here

class ImpactAPI(ModelRestApi):
    resource_name = 'impact'
    datamodel = SQLAInterface('Impact')
    list_columns = ['id', 'organization_id_fk', 'project_id_fk', 'metric_name', 'value', 'unit', 'date_measured', 'description']
    show_columns = ['id', 'organization_id_fk', 'project_id_fk', 'metric_name', 'value', 'unit', 'date_measured', 'description']
    add_columns = ['organization_id_fk', 'project_id_fk', 'metric_name', 'value', 'unit', 'date_measured', 'description']
    edit_columns = ['organization_id_fk', 'project_id_fk', 'metric_name', 'value', 'unit', 'date_measured', 'description']
    # Add any API-specific configuration here

class PersonTrainingAPI(ModelRestApi):
    resource_name = 'person training'
    datamodel = SQLAInterface('PersonTraining')
    list_columns = ['id', 'training_id_fk', 'person_id_fk', 'start_date', 'completion_date', 'completed', 'certificate_id']
    show_columns = ['id', 'training_id_fk', 'person_id_fk', 'start_date', 'completion_date', 'completed', 'certificate_id']
    add_columns = ['training_id_fk', 'person_id_fk', 'start_date', 'completion_date', 'completed', 'certificate_id']
    edit_columns = ['training_id_fk', 'person_id_fk', 'start_date', 'completion_date', 'completed', 'certificate_id']
    # Add any API-specific configuration here

class PjFeedbackAPI(ModelRestApi):
    resource_name = 'pj feedback'
    datamodel = SQLAInterface('PjFeedback')
    list_columns = ['id', 'person_id_fk', 'organization_id_fk', 'project_id_fk', 'rating', 'comments', 'notes', 'date']
    show_columns = ['id', 'person_id_fk', 'organization_id_fk', 'project_id_fk', 'rating', 'comments', 'notes', 'date']
    add_columns = ['person_id_fk', 'organization_id_fk', 'project_id_fk', 'rating', 'comments', 'notes', 'date']
    edit_columns = ['person_id_fk', 'organization_id_fk', 'project_id_fk', 'rating', 'comments', 'notes', 'date']
    # Add any API-specific configuration here

class ProjectLocationsAPI(ModelRestApi):
    resource_name = 'project locations'
    datamodel = SQLAInterface('ProjectLocations')
    list_columns = ['id', 'project_id_fk', 'location_name', 'latitude', 'longitude']
    show_columns = ['id', 'project_id_fk', 'location_name', 'latitude', 'longitude']
    add_columns = ['project_id_fk', 'location_name', 'latitude', 'longitude']
    edit_columns = ['project_id_fk', 'location_name', 'latitude', 'longitude']
    # Add any API-specific configuration here

class ProjectTagAPI(ModelRestApi):
    resource_name = 'project tag'
    datamodel = SQLAInterface('ProjectTag')
    list_columns = ['id', 'project_id_fk', 'tag_id_fk']
    show_columns = ['id', 'project_id_fk', 'tag_id_fk']
    add_columns = ['project_id_fk', 'tag_id_fk']
    edit_columns = ['project_id_fk', 'tag_id_fk']
    # Add any API-specific configuration here

def register_model_views():
    # Register regular model views
    for table_name, model_class in db.Model._decl_class_registry.items():
        if isinstance(model_class, type) and issubclass(model_class, db.Model):
            view_class = globals().get(f'{model_class.__name__}View')
            if view_class:
                appbuilder.add_view(view_class, f'{pascal_to_words(model_class.__name__)}', icon='fa-table', category='Data')

def register_master_detail_views():
    # Register master-detail views
    for name, obj in globals().items():
        if isinstance(obj, type) and issubclass(obj, MasterDetailView):
            appbuilder.add_view(obj, f'{pascal_to_words(name)}', icon='fa-link', category='Master-Detail')

def register_multiple_views():
    # Register multiple views
    for name, obj in globals().items():
        if isinstance(obj, type) and issubclass(obj, MultipleView):
            appbuilder.add_view(obj, f'{pascal_to_words(name)}', icon='fa-cubes', category='Multiple Views')

def register_all_views():
    register_model_views()
    register_master_detail_views()
    register_multiple_views()

# Call this function to register all views
register_all_views()
