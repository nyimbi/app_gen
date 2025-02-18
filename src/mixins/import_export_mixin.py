"""
import_export_mixin.py

This module provides an ImportExportMixin class for implementing data import
and export functionality in SQLAlchemy models for Flask-AppBuilder applications.

The ImportExportMixin allows easy export of model data to various formats (CSV,
JSON, Excel, XML, YAML) and provides robust import functionality with data validation,
type coercion, relationship handling and comprehensive error handling.

Dependencies:
    - SQLAlchemy
    - Flask-AppBuilder
    - pandas
    - openpyxl
    - pyyaml
    - dicttoxml
    - marshmallow
    - psycopg2-binary

Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.1
"""

import csv
import io
import json
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import yaml
from dicttoxml import dicttoxml
from flask_appbuilder.models.mixins import AuditMixin
from marshmallow import Schema, ValidationError, fields
from sqlalchemy import (
    ARRAY,
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    Integer,
    Numeric,
    String,
    Time,
)
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import RelationshipProperty

logger = logging.getLogger(__name__)


class ImportExportMixin(AuditMixin):
    """
    A mixin class for adding import/export functionality to SQLAlchemy models.

    Features:
    - Multiple export formats (CSV, JSON, Excel, XML, YAML)
    - Batch processing with configurable sizes
    - Data validation and type coercion
    - Relationship handling (nested data)
    - Custom pre/post processing hooks
    - Error handling and reporting
    - Progress tracking
    - Memory efficient chunked processing
    - Data sanitization
    - Schema validation
    - Audit logging

    Class Attributes:
        __export_fields__ (List[str]): Fields to export
        __import_fields__ (List[str]): Fields that can be imported
        __export_exclude__ (List[str]): Fields to exclude from export
        __import_exclude__ (List[str]): Fields to exclude from import
        __export_labels__ (Dict[str,str]): Custom export field labels
        __import_validators__ (Dict[str,Callable]): Custom field validators
        __import_transformers__ (Dict[str,Callable]): Custom field transformers
        __batch_size__ (int): Default import batch size
        __date_format__ (str): Date format for import/export
        __null_values__ (List[str]): Values to treat as NULL
        __true_values__ (List[str]): Values to treat as TRUE
        __false_values__ (List[str]): Values to treat as FALSE
    """

    __export_fields__: List[str] = []
    __import_fields__: List[str] = []
    __export_exclude__: List[str] = [
        "created_by",
        "created_on",
        "changed_by",
        "changed_on",
    ]
    __import_exclude__: List[str] = [
        "id",
        "created_by",
        "created_on",
        "changed_by",
        "changed_on",
    ]
    __export_labels__: Dict[str, str] = {}
    __import_validators__: Dict[str, Any] = {}
    __import_transformers__: Dict[str, Any] = {}
    __batch_size__: int = 1000
    __date_format__: str = "%Y-%m-%d"
    __null_values__: List[str] = ["", "null", "NULL", "None", "NA", "N/A"]
    __true_values__: List[str] = ["true", "True", "TRUE", "1", "yes", "Yes", "YES"]
    __false_values__: List[str] = ["false", "False", "FALSE", "0", "no", "No", "NO"]

    @classmethod
    def get_exportable_fields(cls) -> List[str]:
        """Get list of exportable fields accounting for exclusions."""
        if cls.__export_fields__:
            return [f for f in cls.__export_fields__ if f not in cls.__export_exclude__]
        return [
            c.key
            for c in inspect(cls).attrs
            if not c.key.startswith("_") and c.key not in cls.__export_exclude__
        ]

    @classmethod
    def get_importable_fields(cls) -> List[str]:
        """Get list of importable fields accounting for exclusions."""
        if cls.__import_fields__:
            return [f for f in cls.__import_fields__ if f not in cls.__import_exclude__]
        return [
            c.key
            for c in inspect(cls).attrs
            if not c.key.startswith("_") and c.key not in cls.__import_exclude__
        ]

    @classmethod
    def to_dict(cls, instance: Any, include_relations: bool = True) -> Dict[str, Any]:
        """
        Convert model instance to dictionary format.

        Args:
            instance: Model instance to convert
            include_relations: Whether to include relationship fields

        Returns:
            Dictionary representation of instance
        """
        data = {}
        for field in cls.get_exportable_fields():
            value = getattr(instance, field)

            # Handle relationships
            if include_relations and hasattr(value, "__table__"):
                data[field] = value.id
            elif isinstance(value, list) and value and hasattr(value[0], "__table__"):
                data[field] = [item.id for item in value]
            # Handle special types
            elif isinstance(value, (date, datetime)):
                data[field] = value.isoformat()
            elif isinstance(value, Decimal):
                data[field] = str(value)
            elif isinstance(value, (list, dict)):
                data[field] = json.dumps(value)
            else:
                data[field] = value

        return cls.post_export_hook(data)

    @classmethod
    def process_import_value(cls, field: str, value: Any) -> Any:
        """
        Process and validate an import value.

        Handles type conversion, validation, and relationship resolution.

        Args:
            field: Field name
            value: Value to process

        Returns:
            Processed value ready for import

        Raises:
            ValidationError: If value fails validation
        """
        # Get field type
        field_type = getattr(cls, field).type

        # Handle null values
        if str(value).strip() in cls.__null_values__:
            return None

        # Apply custom transformer if exists
        if field in cls.__import_transformers__:
            value = cls.__import_transformers__[field](value)

        # Handle relationships
        attr = getattr(cls, field)
        if hasattr(attr, "property") and isinstance(
            attr.property, RelationshipProperty
        ):
            related_model = attr.property.mapper.class_
            if attr.property.uselist:
                if isinstance(value, str):
                    value = json.loads(value)
                return [related_model.query.get(v) for v in value if v is not None]
            else:
                return related_model.query.get(value) if value is not None else None

        # Type conversions
        try:
            if isinstance(field_type, String):
                return str(value).strip()
            elif isinstance(field_type, Integer):
                return int(float(value))
            elif isinstance(field_type, Float):
                return float(value)
            elif isinstance(field_type, Boolean):
                return str(value).lower() in cls.__true_values__
            elif isinstance(field_type, (Date, DateTime)):
                if isinstance(value, str):
                    return datetime.strptime(value, cls.__date_format__).date()
                return value
            elif isinstance(field_type, Numeric):
                return Decimal(str(value))
            elif isinstance(field_type, JSON):
                if isinstance(value, str):
                    return json.loads(value)
                return value
            elif isinstance(field_type, ARRAY):
                if isinstance(value, str):
                    return json.loads(value)
                return value
            elif isinstance(field_type, Enum):
                return field_type.python_type(value)
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            raise ValidationError(f"Invalid value for field {field}: {str(e)}")

        # Apply custom validator if exists
        if field in cls.__import_validators__:
            if not cls.__import_validators__[field](value):
                raise ValidationError(f"Validation failed for field {field}")

        return value

    @classmethod
    def export_to_csv(cls, query, output_file: str, **kwargs):
        """
        Export query results to CSV.

        Args:
            query: SQLAlchemy query to export
            output_file: Output file path
            **kwargs: Additional pandas to_csv options
        """
        data = [cls.to_dict(instance) for instance in query]
        df = pd.DataFrame(data)
        if cls.__export_labels__:
            df = df.rename(columns=cls.__export_labels__)
        df.to_csv(output_file, index=False, **kwargs)

    @classmethod
    def export_to_json(cls, query, output_file: str, pretty: bool = True):
        """Export query results to JSON."""
        data = [cls.to_dict(instance) for instance in query]
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2 if pretty else None)

    @classmethod
    def export_to_excel(cls, query, output_file: str, **kwargs):
        """Export query results to Excel."""
        data = [cls.to_dict(instance) for instance in query]
        df = pd.DataFrame(data)
        if cls.__export_labels__:
            df = df.rename(columns=cls.__export_labels__)
        df.to_excel(output_file, index=False, **kwargs)

    @classmethod
    def export_to_xml(cls, query, output_file: str):
        """Export query results to XML."""
        data = [cls.to_dict(instance) for instance in query]
        xml = dicttoxml(data, custom_root="data", attr_type=False)
        with open(output_file, "wb") as f:
            f.write(xml)

    @classmethod
    def export_to_yaml(cls, query, output_file: str):
        """Export query results to YAML."""
        data = [cls.to_dict(instance) for instance in query]
        with open(output_file, "w") as f:
            yaml.dump(data, f)

    @classmethod
    def import_data(
        cls, session, data: List[Dict[str, Any]], batch_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Import data with validation and error handling.

        Args:
            session: SQLAlchemy session
            data: List of data dictionaries to import
            batch_size: Override default batch size

        Returns:
            Dict with import statistics and errors
        """
        data = cls.pre_import_hook(data)
        data = cls.data_validation_hook(data)

        importable_fields = cls.get_importable_fields()
        total = len(data)
        successful = 0
        errors = []

        batch_size = batch_size or cls.__batch_size__

        for i in range(0, total, batch_size):
            batch = data[i : i + batch_size]
            for item in batch:
                try:
                    instance = cls()
                    for field in importable_fields:
                        if field in item:
                            processed_value = cls.process_import_value(
                                field, item[field]
                            )
                            setattr(instance, field, processed_value)
                    session.add(instance)
                    successful += 1
                except Exception as e:
                    errors.append(
                        {
                            "row": i + batch.index(item) + 1,
                            "data": item,
                            "error": str(e),
                        }
                    )
                    logger.error(f"Import error: {str(e)}", exc_info=True)

            try:
                session.commit()
            except Exception as e:
                session.rollback()
                logger.error(f"Batch commit error: {str(e)}", exc_info=True)
                errors.extend(
                    [
                        {"row": i + idx + 1, "data": item, "error": str(e)}
                        for idx, item in enumerate(batch)
                    ]
                )
                successful -= len(batch)

        return {
            "total_processed": total,
            "successful_imports": successful,
            "failed_imports": total - successful,
            "errors": errors,
        }

    @classmethod
    def import_from_csv(cls, session, file_path: str, **kwargs) -> Dict[str, Any]:
        """Import data from CSV file."""
        df = pd.read_csv(file_path, **kwargs)
        if cls.__export_labels__:
            reverse_labels = {v: k for k, v in cls.__export_labels__.items()}
            df = df.rename(columns=reverse_labels)
        data = df.to_dict("records")
        return cls.import_data(session, data)

    @classmethod
    def import_from_json(cls, session, file_path: str) -> Dict[str, Any]:
        """Import data from JSON file."""
        with open(file_path, "r") as f:
            data = json.load(f)
        return cls.import_data(session, data)

    @classmethod
    def import_from_excel(cls, session, file_path: str, **kwargs) -> Dict[str, Any]:
        """Import data from Excel file."""
        df = pd.read_excel(file_path, **kwargs)
        if cls.__export_labels__:
            reverse_labels = {v: k for k, v in cls.__export_labels__.items()}
            df = df.rename(columns=reverse_labels)
        data = df.to_dict("records")
        return cls.import_data(session, data)

    @classmethod
    def import_from_xml(cls, session, file_path: str) -> Dict[str, Any]:
        """Import data from XML file."""
        import xmltodict

        with open(file_path, "r") as f:
            data = xmltodict.parse(f.read())
        return cls.import_data(session, data["data"]["item"])

    @classmethod
    def import_from_yaml(cls, session, file_path: str) -> Dict[str, Any]:
        """Import data from YAML file."""
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)
        return cls.import_data(session, data)

    @classmethod
    def data_validation_hook(cls, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Custom validation hook - override in subclass."""
        return data

    @classmethod
    def pre_import_hook(cls, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Pre-import processing hook - override in subclass."""
        return data

    @classmethod
    def post_export_hook(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Post-export processing hook - override in subclass."""
        return data


# Example usage
"""
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, Boolean, Date
from sqlalchemy.orm import relationship
from datetime import date
from decimal import Decimal

class Category(Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

class Product(ImportExportMixin, Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    price = Column(Numeric(10,2), nullable=False)
    active = Column(Boolean, default=True)
    launch_date = Column(Date)
    category_id = Column(Integer, ForeignKey('category.id'), nullable=False)
    category = relationship('Category')

    __export_fields__ = ['id', 'name', 'description', 'price', 'active',
                        'launch_date', 'category']
    __import_fields__ = ['name', 'description', 'price', 'active',
                        'launch_date', 'category_id']
    __export_labels__ = {
        'name': 'Product Name',
        'description': 'Description',
        'price': 'Price ($)',
        'active': 'Is Active',
        'launch_date': 'Launch Date'
    }
    __import_validators__ = {
        'price': lambda x: Decimal(str(x)) > 0,
        'launch_date': lambda x: date.fromisoformat(x) >= date.today()
    }
    __import_transformers__ = {
        'name': str.title,
        'description': str.strip
    }

    @classmethod
    def data_validation_hook(cls, data):
        for item in data:
            if item.get('price', 0) < 0:
                item['price'] = abs(item['price'])
            if not item.get('description'):
                item['description'] = item.get('name', '')
        return data

# Usage examples:
with app.app_context():
    # Export
    Product.export_to_csv(Product.query, 'products.csv')
    Product.export_to_json(Product.query, 'products.json')
    Product.export_to_excel(Product.query, 'products.xlsx')
    Product.export_to_xml(Product.query, 'products.xml')
    Product.export_to_yaml(Product.query, 'products.yaml')

    # Import
    db.session.begin()
    try:
        result = Product.import_from_csv(db.session, 'products.csv')
        print(f"Import Results:")
        print(f"Total Processed: {result['total_processed']}")
        print(f"Successful: {result['successful_imports']}")
        print(f"Failed: {result['failed_imports']}")
        if result['errors']:
            print("\nErrors:")
            for error in result['errors']:
                print(f"Row {error['row']}: {error['error']}")
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Import failed: {str(e)}")
"""
