"""
metadata_mixin.py

This module provides a MetadataMixin class for adding flexible, schema-less
metadata to SQLAlchemy models in Flask-AppBuilder applications.

The MetadataMixin allows storing additional, non-structured data with model
instances, providing flexibility for evolving data requirements.

Dependencies:
    - SQLAlchemy
    - Flask-AppBuilder
    - sqlalchemy.ext.mutable (for mutable JSON type)

Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.0
"""

from flask_appbuilder import Model
from sqlalchemy import Column, JSON
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.ext.declarative import declared_attr
from flask import current_app
import json

class MetadataMixin:
    """
    A mixin class for adding flexible metadata capabilities to SQLAlchemy models.

    This mixin provides methods for storing and retrieving schema-less metadata,
    allowing for dynamic addition of data fields without altering the database schema.

    Class Attributes:
        __metadata_fields__ (list): Optional list of predefined metadata fields.
    """

    __metadata_fields__ = []

    @declared_attr
    def metadata(cls):
        return Column(MutableDict.as_mutable(JSON), default=dict, nullable=False)

    def set_metadata(self, key, value):
        """
        Set a metadata value.

        Args:
            key (str): The metadata key.
            value: The value to store (must be JSON serializable).
        """
        if self.__metadata_fields__ and key not in self.__metadata_fields__:
            raise ValueError(f"Invalid metadata key: {key}")
        
        self.metadata[key] = value

    def get_metadata(self, key, default=None):
        """
        Get a metadata value.

        Args:
            key (str): The metadata key.
            default: The default value to return if the key is not found.

        Returns:
            The value associated with the key, or the default value if not found.
        """
        return self.metadata.get(key, default)

    def update_metadata(self, data):
        """
        Update multiple metadata fields at once.

        Args:
            data (dict): A dictionary of metadata key-value pairs to update.
        """
        if self.__metadata_fields__:
            invalid_keys = set(data.keys()) - set(self.__metadata_fields__)
            if invalid_keys:
                raise ValueError(f"Invalid metadata keys: {', '.join(invalid_keys)}")
        
        self.metadata.update(data)

    def delete_metadata(self, key):
        """
        Delete a metadata field.

        Args:
            key (str): The metadata key to delete.

        Returns:
            bool: True if the key was deleted, False if it didn't exist.
        """
        return self.metadata.pop(key, None) is not None

    def clear_metadata(self):
        """Clear all metadata."""
        self.metadata.clear()

    def get_all_metadata(self):
        """
        Get all metadata.

        Returns:
            dict: A dictionary containing all metadata.
        """
        return dict(self.metadata)

    @classmethod
    def search_by_metadata(cls, session, **kwargs):
        """
        Search for instances based on metadata values.

        Args:
            session: SQLAlchemy session.
            **kwargs: Metadata key-value pairs to search for.

        Returns:
            list: A list of instances matching the metadata criteria.
        """
        query = session.query(cls)
        for key, value in kwargs.items():
            query = query.filter(cls.metadata[key].astext == json.dumps(value))
        return query.all()

    @classmethod
    def get_unique_metadata_keys(cls, session):
        """
        Get a list of all unique metadata keys used across all instances.

        Args:
            session: SQLAlchemy session.

        Returns:
            list: A list of unique metadata keys.
        """
        result = session.query(cls.metadata).all()
        keys = set()
        for row in result:
            keys.update(row[0].keys())
        return list(keys)

    def validate_metadata(self):
        """
        Validate the metadata against any defined constraints.

        This method can be overridden in subclasses to implement custom validation logic.

        Raises:
            ValueError: If the metadata is invalid.
        """
        if self.__metadata_fields__:
            invalid_keys = set(self.metadata.keys()) - set(self.__metadata_fields__)
            if invalid_keys:
                raise ValueError(f"Invalid metadata keys: {', '.join(invalid_keys)}")

    @classmethod
    def get_metadata_schema(cls):
        """
        Get the metadata schema if __metadata_fields__ is defined.

        Returns:
            dict: A dictionary representing the metadata schema, or None if not defined.
        """
        if cls.__metadata_fields__:
            return {field: {"type": "any"} for field in cls.__metadata_fields__}
        return None

# Example usage (commented out):
"""
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String
from mixins.metadata_mixin import MetadataMixin

class Product(MetadataMixin, Model):
    __tablename__ = 'nx_products'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

    __metadata_fields__ = ['color', 'size', 'material']  # Optional: restrict metadata fields

# In your application code:

# Creating a new product with metadata
new_product = Product(name="T-Shirt")
new_product.set_metadata('color', 'blue')
new_product.set_metadata('size', 'L')
db.session.add(new_product)
db.session.commit()

# Updating metadata
new_product.update_metadata({'material': 'cotton', 'size': 'XL'})
db.session.commit()

# Retrieving metadata
color = new_product.get_metadata('color')  # Returns 'blue'
all_metadata = new_product.get_all_metadata()  # Returns {'color': 'blue', 'size': 'XL', 'material': 'cotton'}

# Searching by metadata
large_products = Product.search_by_metadata(db.session, size='XL')

# Getting unique metadata keys
all_keys = Product.get_unique_metadata_keys(db.session)

# Validating metadata (will raise ValueError if invalid keys are present)
new_product.validate_metadata()

# Getting metadata schema
schema = Product.get_metadata_schema()
"""
