"""
internationalization_mixin.py

This module provides an InternationalizationMixin class for implementing
multi-language support in SQLAlchemy models for Flask-AppBuilder applications.

The InternationalizationMixin allows for storing and retrieving translated
content for specified fields, with support for fallback languages and
integration with Flask-Babel.

Dependencies:
    - SQLAlchemy
    - Flask-AppBuilder
    - Flask-Babel

Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.0
"""

from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, JSON, event
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from flask_babel import get_locale
from flask import current_app
import json

class InternationalizationMixin:
    """
    A mixin class for adding internationalization support to SQLAlchemy models.

    This mixin provides methods for storing and retrieving translated content
    for specified fields, with support for fallback languages.

    Class Attributes:
        __translatable__ (list): List of field names that should be translatable.
        __fallback_locale__ (str): Fallback locale to use when a translation is not available.
    """

    __translatable__ = []
    __fallback_locale__ = 'en'

    @declared_attr
    def translations(cls):
        return Column(JSON, default=dict, nullable=False)

    @classmethod
    def __declare_last__(cls):
        if not cls.__translatable__:
            raise ValueError(f"__translatable__ must be defined for {cls.__name__}")

        for field in cls.__translatable__:
            setattr(cls, f"{field}_translations", hybrid_property(
                fget=lambda self, field=field: self._get_translation(field),
                fset=lambda self, value, field=field: self._set_translation(field, value)
            ))

        event.listen(cls, 'before_insert', cls._before_insert)
        event.listen(cls, 'before_update', cls._before_update)

    def _get_translation(self, field):
        """
        Get the translated value for a field.

        Args:
            field (str): The name of the field to translate.

        Returns:
            str: The translated value, or the original value if no translation is found.
        """
        locale = str(get_locale())
        translations = self.translations.get(field, {})
        
        if locale in translations:
            return translations[locale]
        elif self.__fallback_locale__ in translations:
            return translations[self.__fallback_locale__]
        else:
            return getattr(self, field)

    def _set_translation(self, field, value):
        """
        Set a translation for a field.

        Args:
            field (str): The name of the field to translate.
            value (dict): A dictionary of locale-value pairs for the translation.
        """
        if not isinstance(value, dict):
            raise ValueError("Translations must be provided as a dictionary of locale-value pairs")
        
        if field not in self.translations:
            self.translations[field] = {}
        
        self.translations[field].update(value)

    @classmethod
    def _before_insert(cls, mapper, connection, target):
        """Ensure translations are JSON serialized before insert."""
        target.translations = json.dumps(target.translations)

    @classmethod
    def _before_update(cls, mapper, connection, target):
        """Ensure translations are JSON serialized before update."""
        target.translations = json.dumps(target.translations)

    def set_translation(self, field, locale, value):
        """
        Set a translation for a specific field and locale.

        Args:
            field (str): The name of the field to translate.
            locale (str): The locale code for the translation.
            value (str): The translated value.
        """
        if field not in self.__translatable__:
            raise ValueError(f"Field '{field}' is not marked as translatable")
        
        if field not in self.translations:
            self.translations[field] = {}
        
        self.translations[field][locale] = value

    def get_translation(self, field, locale=None):
        """
        Get a translation for a specific field and locale.

        Args:
            field (str): The name of the field to translate.
            locale (str, optional): The locale code for the translation. If not provided,
                                    the current locale will be used.

        Returns:
            str: The translated value, or the original value if no translation is found.
        """
        if field not in self.__translatable__:
            raise ValueError(f"Field '{field}' is not marked as translatable")
        
        if locale is None:
            locale = str(get_locale())
        
        translations = self.translations.get(field, {})
        
        if locale in translations:
            return translations[locale]
        elif self.__fallback_locale__ in translations:
            return translations[self.__fallback_locale__]
        else:
            return getattr(self, field)

    @classmethod
    def export_translations(cls, session):
        """
        Export all translations for this model.

        Args:
            session: SQLAlchemy session.

        Returns:
            dict: A dictionary of all translations for all instances of this model.
        """
        translations = {}
        for instance in session.query(cls).all():
            translations[instance.id] = instance.translations
        return translations

    @classmethod
    def import_translations(cls, session, translations_data):
        """
        Import translations for this model.

        Args:
            session: SQLAlchemy session.
            translations_data (dict): A dictionary of translations keyed by instance id.
        """
        for instance_id, translations in translations_data.items():
            instance = session.query(cls).get(instance_id)
            if instance:
                instance.translations.update(translations)
        session.commit()

    @classmethod
    def get_missing_translations(cls, session, locales):
        """
        Get a report of missing translations.

        Args:
            session: SQLAlchemy session.
            locales (list): List of locale codes to check.

        Returns:
            dict: A dictionary of missing translations for each instance and field.
        """
        missing = {}
        for instance in session.query(cls).all():
            instance_missing = {}
            for field in cls.__translatable__:
                for locale in locales:
                    if locale not in instance.translations.get(field, {}):
                        if field not in instance_missing:
                            instance_missing[field] = []
                        instance_missing[field].append(locale)
            if instance_missing:
                missing[instance.id] = instance_missing
        return missing

# Example usage (commented out):
"""
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String
from mixins.internationalization_mixin import InternationalizationMixin

class Product(InternationalizationMixin, Model):
    __tablename__ = 'nx_products'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))

    __translatable__ = ['name', 'description']
    __fallback_locale__ = 'en'

# In your application code:

# Creating a new product with translations
product = Product(name="Laptop", description="A powerful laptop")
product.set_translation('name', 'es', 'Portátil')
product.set_translation('name', 'fr', 'Ordinateur portable')
product.set_translation('description', 'es', 'Un portátil potente')
product.set_translation('description', 'fr', 'Un ordinateur portable puissant')

db.session.add(product)
db.session.commit()

# Getting translations
print(product.get_translation('name', 'es'))  # Output: Portátil
print(product.get_translation('description', 'fr'))  # Output: Un ordinateur portable puissant

# Using hybrid properties (assumes 'es' is the current locale)
print(product.name_translations)  # Output: Portátil

# Exporting translations
all_translations = Product.export_translations(db.session)

# Importing translations
new_translations = {
    1: {
        'name': {'de': 'Laptop'},
        'description': {'de': 'Ein leistungsstarker Laptop'}
    }
}
Product.import_translations(db.session, new_translations)

# Checking for missing translations
missing = Product.get_missing_translations(db.session, ['en', 'es', 'fr', 'de'])
print(missing)
"""
