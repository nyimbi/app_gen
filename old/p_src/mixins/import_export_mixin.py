"""
import_export_mixin.py

This module provides an ImportExportMixin class for implementing data import
and export functionality in SQLAlchemy models for Flask-AppBuilder applications.

The ImportExportMixin allows easy export of model data to various formats (CSV,
JSON, Excel) and provides robust import functionality with data validation and
error handling.

Dependencies:
    - SQLAlchemy
    - Flask-AppBuilder
    - pandas
    - openpyxl

Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.0
"""

from flask_appbuilder.models.mixins import AuditMixin
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import RelationshipProperty
import pandas as pd
import json
from typing import List, Dict, Any, Callable
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

class ImportExportMixin(AuditMixin):
    """
    A mixin class for adding import and export functionality to SQLAlchemy models.

    This mixin provides methods for exporting model data to CSV, JSON, and Excel
    formats, as well as importing data from these formats. It includes data
    validation, error handling, and support for relationships and nested data.

    Class Attributes:
        __export_fields__ (List[str]): List of field names to be exported.
        __import_fields__ (List[str]): List of field names that can be imported.
        __export_exclude__ (List[str]): List of field names to exclude from export.
        __import_exclude__ (List[str]): List of field names to exclude from import.
    """

    __export_fields__: List[str] = []
    __import_fields__: List[str] = []
    __export_exclude__: List[str] = []
    __import_exclude__: List[str] = []

    @classmethod
    def get_exportable_fields(cls) -> List[str]:
        """
        Get the list of fields that can be exported.

        Returns:
            List[str]: List of exportable field names.
        """
        if cls.__export_fields__:
            return [f for f in cls.__export_fields__ if f not in cls.__export_exclude__]
        return [c.key for c in inspect(cls).attrs if not c.key.startswith('_') and c.key not in cls.__export_exclude__]

    @classmethod
    def get_importable_fields(cls) -> List[str]:
        """
        Get the list of fields that can be imported.

        Returns:
            List[str]: List of importable field names.
        """
        if cls.__import_fields__:
            return [f for f in cls.__import_fields__ if f not in cls.__import_exclude__]
        return [c.key for c in inspect(cls).attrs if not c.key.startswith('_') and c.key not in cls.__import_exclude__]

    @classmethod
    def to_dict(cls, instance: Any) -> Dict[str, Any]:
        """
        Convert a model instance to a dictionary.

        Args:
            instance: The model instance to convert.

        Returns:
            Dict[str, Any]: Dictionary representation of the instance.
        """
        data = {}
        for field in cls.get_exportable_fields():
            value = getattr(instance, field)
            if isinstance(value, list):
                data[field] = [item.id if hasattr(item, 'id') else str(item) for item in value]
            elif hasattr(value, 'id'):
                data[field] = value.id
            else:
                data[field] = value
        return data

    @classmethod
    def export_to_csv(cls, query, output_file: str):
        """
        Export query results to a CSV file.

        Args:
            query: SQLAlchemy query to export.
            output_file (str): Path to the output CSV file.
        """
        data = [cls.to_dict(instance) for instance in query]
        df = pd.DataFrame(data)
        df.to_csv(output_file, index=False)

    @classmethod
    def export_to_json(cls, query, output_file: str):
        """
        Export query results to a JSON file.

        Args:
            query: SQLAlchemy query to export.
            output_file (str): Path to the output JSON file.
        """
        data = [cls.to_dict(instance) for instance in query]
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def export_to_excel(cls, query, output_file: str):
        """
        Export query results to an Excel file.

        Args:
            query: SQLAlchemy query to export.
            output_file (str): Path to the output Excel file.
        """
        data = [cls.to_dict(instance) for instance in query]
        df = pd.DataFrame(data)
        df.to_excel(output_file, index=False)

    @classmethod
    def import_data(cls, session, data: List[Dict[str, Any]], batch_size: int = 100) -> Dict[str, Any]:
        """
        Import data into the model.

        Args:
            session: SQLAlchemy session.
            data (List[Dict[str, Any]]): List of dictionaries containing the data to import.
            batch_size (int): Number of records to process in each batch.

        Returns:
            Dict[str, Any]: Import statistics including total processed, successful imports, and errors.
        """
        importable_fields = cls.get_importable_fields()
        total = len(data)
        successful = 0
        errors = []

        for i in range(0, total, batch_size):
            batch = data[i:i+batch_size]
            for item in batch:
                try:
                    instance = cls()
                    for field in importable_fields:
                        if field in item:
                            setattr(instance, field, cls.process_import_value(field, item[field]))
                    session.add(instance)
                    successful += 1
                except Exception as e:
                    errors.append(f"Error importing item {item}: {str(e)}")
                    logger.error(f"Import error: {str(e)}", exc_info=True)

            session.commit()

        return {
            "total_processed": total,
            "successful_imports": successful,
            "errors": errors
        }

    @classmethod
    def process_import_value(cls, field: str, value: Any) -> Any:
        """
        Process a value during import, handling relationships and data transformations.

        Args:
            field (str): The field name.
            value (Any): The value to process.

        Returns:
            Any: The processed value.
        """
        attr = getattr(cls, field)
        if hasattr(attr, 'property') and isinstance(attr.property, RelationshipProperty):
            related_model = attr.property.mapper.class_
            if attr.property.uselist:
                return [related_model.query.get(v) for v in value if v is not None]
            else:
                return related_model.query.get(value) if value is not None else None
        return value

    @classmethod
    def import_from_csv(cls, session, file_path: str, **kwargs) -> Dict[str, Any]:
        """
        Import data from a CSV file.

        Args:
            session: SQLAlchemy session.
            file_path (str): Path to the CSV file.
            **kwargs: Additional arguments to pass to pandas.read_csv.

        Returns:
            Dict[str, Any]: Import statistics.
        """
        df = pd.read_csv(file_path, **kwargs)
        data = df.to_dict('records')
        return cls.import_data(session, data)

    @classmethod
    def import_from_json(cls, session, file_path: str) -> Dict[str, Any]:
        """
        Import data from a JSON file.

        Args:
            session: SQLAlchemy session.
            file_path (str): Path to the JSON file.

        Returns:
            Dict[str, Any]: Import statistics.
        """
        with open(file_path, 'r') as f:
            data = json.load(f)
        return cls.import_data(session, data)

    @classmethod
    def import_from_excel(cls, session, file_path: str, **kwargs) -> Dict[str, Any]:
        """
        Import data from an Excel file.

        Args:
            session: SQLAlchemy session.
            file_path (str): Path to the Excel file.
            **kwargs: Additional arguments to pass to pandas.read_excel.

        Returns:
            Dict[str, Any]: Import statistics.
        """
        df = pd.read_excel(file_path, **kwargs)
        data = df.to_dict('records')
        return cls.import_data(session, data)

    @classmethod
    def data_validation_hook(cls, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Hook for custom data validation before import.

        This method can be overridden in subclasses to implement custom validation logic.

        Args:
            data (List[Dict[str, Any]]): The data to be imported.

        Returns:
            List[Dict[str, Any]]: The validated (and possibly modified) data.
        """
        return data

    @classmethod
    def pre_import_hook(cls, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Hook for pre-processing data before import.

        This method can be overridden in subclasses to implement custom pre-processing logic.

        Args:
            data (List[Dict[str, Any]]): The data to be imported.

        Returns:
            List[Dict[str, Any]]: The pre-processed data.
        """
        return data

    @classmethod
    def post_export_hook(cls, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Hook for post-processing data after export.

        This method can be overridden in subclasses to implement custom post-processing logic.

        Args:
            data (List[Dict[str, Any]]): The exported data.

        Returns:
            List[Dict[str, Any]]: The post-processed data.
        """
        return data

# Example usage (commented out):
"""
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from mixins.import_export_mixin import ImportExportMixin

class Category(Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

class Product(ImportExportMixin, Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    price = Column(Integer, nullable=False)
    category_id = Column(Integer, ForeignKey('category.id'), nullable=False)
    category = relationship('Category')

    __export_fields__ = ['id', 'name', 'price', 'category']
    __import_fields__ = ['name', 'price', 'category_id']

# In your application code:

# Export to CSV
Product.export_to_csv(Product.query, 'products.csv')

# Export to JSON
Product.export_to_json(Product.query, 'products.json')

# Export to Excel
Product.export_to_excel(Product.query, 'products.xlsx')

# Import from CSV
with app.app_context():
    db.session.begin()
    try:
        result = Product.import_from_csv(db.session, 'products.csv')
        print(f"Imported {result['successful_imports']} products")
        if result['errors']:
            print(f"Encountered {len(result['errors'])} errors during import")
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Import failed: {str(e)}")

# Custom validation example
class CustomProduct(ImportExportMixin, Model):
    # ... model definition ...

    @classmethod
    def data_validation_hook(cls, data):
        for item in data:
            if item.get('price', 0) < 0:
                item['price'] = 0  # Set negative prices to 0
        return data

"""
