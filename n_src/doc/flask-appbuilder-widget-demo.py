# models.py

from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, Float, JSON, Text, Boolean
from sqlalchemy.orm import relationship

class Product(Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    price_range = Column(String(50))  # Stored as "min,max"
    tags = Column(String(250))
    config = Column(JSON)
    description = Column(Text)
    location = Column(String(100))  # Stored as "lat,lng"
    price = Column(Float)
    contact_number = Column(String(20))
    rating = Column(Float)
    production_time = Column(Integer)  # Stored in seconds
    related_products = Column(Text)  # Stored as JSON string

    def __repr__(self):
        return self.name

# views.py

from flask_appbuilder import ModelView
from flask_appbuilder.models.sqla.interface import SQLAInterface
from .models import Product
from wtforms.validators import DataRequired
from . import appbuilder, db
from .nx_widgets import (
    RangeSliderWidget, TagInputWidget, JSONEditorWidget, MarkdownEditorWidget,
    GeoPointWidget, CurrencyInputWidget, PhoneNumberWidget, RatingWidget,
    DurationWidget, RelationshipGraphWidget
)

class ProductView(ModelView):
    datamodel = SQLAInterface(Product)

    label_columns = {
        'price_range': 'Price Range',
        'config': 'Configuration',
        'contact_number': 'Contact Number',
        'production_time': 'Production Time',
        'related_products': 'Related Products'
    }

    list_columns = ['name', 'price', 'rating']

    edit_form_extra_fields = {
        'price_range': {
            'label': 'Price Range',
            'widget': RangeSliderWidget(),
            'validators': [DataRequired()],
        },
        'tags': {
            'label': 'Tags',
            'widget': TagInputWidget(),
            'validators': [DataRequired()],
        },
        'config': {
            'label': 'Configuration',
            'widget': JSONEditorWidget(),
            'validators': [DataRequired()],
        },
        'description': {
            'label': 'Description',
            'widget': MarkdownEditorWidget(),
            'validators': [DataRequired()],
        },
        'location': {
            'label': 'Location',
            'widget': GeoPointWidget(),
            'validators': [DataRequired()],
        },
        'price': {
            'label': 'Price',
            'widget': CurrencyInputWidget(),
            'validators': [DataRequired()],
        },
        'contact_number': {
            'label': 'Contact Number',
            'widget': PhoneNumberWidget(),
            'validators': [DataRequired()],
        },
        'rating': {
            'label': 'Rating',
            'widget': RatingWidget(),
            'validators': [DataRequired()],
        },
        'production_time': {
            'label': 'Production Time',
            'widget': DurationWidget(),
            'validators': [DataRequired()],
        },
        'related_products': {
            'label': 'Related Products',
            'widget': RelationshipGraphWidget(),
            'validators': [DataRequired()],
        },
    }

    add_form_extra_fields = edit_form_extra_fields

    def pre_add(self, item):
        self._pre_process_data(item)

    def pre_update(self, item):
        self._pre_process_data(item)

    def _pre_process_data(self, item):
        # Convert price range to string
        if isinstance(item.price_range, list):
            item.price_range = f"{item.price_range[0]},{item.price_range[1]}"
        
        # Convert tags to comma-separated string
        if isinstance(item.tags, list):
            item.tags = ",".join(item.tags)
        
        # Ensure config is a valid JSON string
        if isinstance(item.config, dict):
            item.config = json.dumps(item.config)
        
        # Convert location to string
        if isinstance(item.location, dict):
            item.location = f"{item.location['lat']},{item.location['lng']}"
        
        # Convert production time to seconds
        if isinstance(item.production_time, dict):
            item.production_time = (
                item.production_time.get('hours', 0) * 3600 +
                item.production_time.get('minutes', 0) * 60 +
                item.production_time.get('seconds', 0)
            )
        
        # Ensure related_products is a valid JSON string
        if isinstance(item.related_products, dict):
            item.related_products = json.dumps(item.related_products)

appbuilder.add_view(
    ProductView,
    "Products",
    icon="fa-cube",
    category="Catalog"
)

# app/__init__.py

from flask import Flask
from flask_appbuilder import AppBuilder, SQLA
from flask_appbuilder.menu import Menu

app = Flask(__name__)
app.config.from_object('config')
db = SQLA(app)
appbuilder = AppBuilder(app, db.session, menu=Menu())

from . import views

# config.py

import os
from flask_appbuilder.security.manager import AUTH_OID, AUTH_REMOTE_USER, AUTH_DB, AUTH_LDAP, AUTH_OAUTH

basedir = os.path.abspath(os.path.dirname(__file__))

CSRF_ENABLED = True
SECRET_KEY = '\2\1thisismyscretkey\1\2\e\y\y\h'

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False

AUTH_TYPE = AUTH_DB

APP_NAME = "Widget Demo"
APP_ICON = "static/img/logo.jpg"
#APP_THEME = "bootstrap-theme.css"

# run.py

from app import app

app.run(host='0.0.0.0', port=8080, debug=True)

"""
To run this Flask-AppBuilder application:

1. Create a new directory for your project and navigate to it.
2. Create the following directory structure:
   - project_directory/
     - app/
       - __init__.py
       - models.py
       - views.py
       - nx_widgets.py (copy the previously created file here)
     - config.py
     - run.py

3. Copy the content of each file provided above into the corresponding files in your project structure.

4. Install the required dependencies:
   pip install flask-appbuilder sqlalchemy

5. Initialize the database:
   flask fab create-admin

6. Run the application:
   python run.py

This example demonstrates a simple product catalog application using all the custom widgets we created. The ProductView uses each widget for different fields of the Product model, showcasing how they can be integrated into a Flask-AppBuilder application.

Remember to adjust the base template (base.html) as shown in the previous response to include all necessary JavaScript and CSS files for the widgets to function properly.
"""
