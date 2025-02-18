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
    - psycopg2-binary (for PostgreSQL JSONB support)

Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.1
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from flask import current_app
from flask_appbuilder import Model
from sqlalchemy import JSON, Column, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Query
from sqlalchemy.types import TypeDecorator

logger = logging.getLogger(__name__)


class JSONBType(TypeDecorator):
    """Custom type for handling JSONB in PostgreSQL with fallback to JSON"""

    impl = JSONB

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())


class MetadataMixin:
    """
    A mixin class for adding flexible metadata capabilities to SQLAlchemy models.

    This mixin provides methods for storing and retrieving schema-less metadata,
    allowing for dynamic addition of data fields without altering the database schema.

    Features:
    - Schema-less metadata storage using PostgreSQL JSONB
    - Optional metadata field validation
    - Metadata versioning
    - Audit trail
    - Type validation
    - Default values
    - Computed fields
    - Search capabilities
    - Bulk operations
    - Import/Export functionality

    Class Attributes:
        __metadata_fields__ (list): Optional list of predefined metadata fields
        __metadata_types__ (dict): Optional type definitions for metadata fields
        __metadata_defaults__ (dict): Default values for metadata fields
        __metadata_required__ (list): Required metadata fields
        __metadata_computed__ (dict): Computed metadata field definitions
        __metadata_validators__ (dict): Custom validation functions
        __track_metadata__ (bool): Enable metadata change tracking
        __metadata_version__ (bool): Enable metadata versioning
    """

    __metadata_fields__: List[str] = []
    __metadata_types__: Dict[str, type] = {}
    __metadata_defaults__: Dict[str, Any] = {}
    __metadata_required__: List[str] = []
    __metadata_computed__: Dict[str, callable] = {}
    __metadata_validators__: Dict[str, callable] = {}
    __track_metadata__: bool = False
    __metadata_version__: bool = False

    @declared_attr
    def metadata(cls):
        """Define the metadata column using PostgreSQL JSONB"""
        return Column(
            MutableDict.as_mutable(JSONBType),
            default=lambda: cls.__metadata_defaults__.copy(),
            nullable=False,
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_metadata = dict(self.metadata or {})
        if self.__metadata_version__:
            self.metadata["_version"] = 1
            self.metadata["_updated_at"] = datetime.utcnow().isoformat()

    def set_metadata(self, key: str, value: Any, validate: bool = True) -> None:
        """
        Set a metadata value with validation.

        Args:
            key (str): The metadata key
            value: The value to store (must be JSON serializable)
            validate (bool): Whether to validate the value

        Raises:
            ValueError: If key or value is invalid
            TypeError: If value type doesn't match schema
        """
        if self.__metadata_fields__ and key not in self.__metadata_fields__:
            raise ValueError(f"Invalid metadata key: {key}")

        if validate:
            self._validate_field(key, value)

        self.metadata[key] = value

        if self.__metadata_version__:
            self.metadata["_version"] += 1
            self.metadata["_updated_at"] = datetime.utcnow().isoformat()

        if self.__track_metadata__:
            self._track_change(key, value)

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get a metadata value with type conversion.

        Args:
            key (str): The metadata key
            default: Default value if key not found

        Returns:
            The value associated with the key, or default if not found
        """
        value = self.metadata.get(key, default)
        if key in self.__metadata_types__:
            try:
                return self.__metadata_types__[key](value)
            except (ValueError, TypeError):
                return default
        return value

    def update_metadata(self, data: Dict[str, Any], validate: bool = True) -> None:
        """
        Update multiple metadata fields with validation.

        Args:
            data (dict): Dictionary of metadata key-value pairs
            validate (bool): Whether to validate the values

        Raises:
            ValueError: If any key or value is invalid
        """
        if self.__metadata_fields__:
            invalid_keys = set(data.keys()) - set(self.__metadata_fields__)
            if invalid_keys:
                raise ValueError(f"Invalid metadata keys: {', '.join(invalid_keys)}")

        if validate:
            for key, value in data.items():
                self._validate_field(key, value)

        self.metadata.update(data)

        if self.__metadata_version__:
            self.metadata["_version"] += 1
            self.metadata["_updated_at"] = datetime.utcnow().isoformat()

    def delete_metadata(self, key: str) -> bool:
        """
        Delete a metadata field.

        Args:
            key (str): The metadata key to delete

        Returns:
            bool: True if deleted, False if not found

        Raises:
            ValueError: If key is required
        """
        if key in self.__metadata_required__:
            raise ValueError(f"Cannot delete required metadata field: {key}")

        result = key in self.metadata
        if result:
            del self.metadata[key]

            if self.__metadata_version__:
                self.metadata["_version"] += 1
                self.metadata["_updated_at"] = datetime.utcnow().isoformat()

        return result

    def clear_metadata(self, keep_required: bool = True) -> None:
        """
        Clear all metadata fields.

        Args:
            keep_required (bool): Keep required fields

        Raises:
            ValueError: If required fields would be cleared
        """
        if keep_required:
            required_values = {
                k: v
                for k, v in self.metadata.items()
                if k in self.__metadata_required__
            }
            self.metadata.clear()
            self.metadata.update(required_values)
        else:
            self.metadata.clear()
            self.metadata.update(self.__metadata_defaults__)

    def get_all_metadata(self, include_system: bool = False) -> Dict[str, Any]:
        """
        Get all metadata with optional filtering.

        Args:
            include_system (bool): Include system fields (_version, etc)

        Returns:
            dict: Copy of metadata dictionary
        """
        if not include_system:
            return {k: v for k, v in self.metadata.items() if not k.startswith("_")}
        return dict(self.metadata)

    @classmethod
    def search_by_metadata(
        cls, session: Any, operator: str = "and_", **kwargs
    ) -> Query:
        """
        Search for instances based on metadata values.

        Args:
            session: SQLAlchemy session
            operator (str): Query operator ('and_' or 'or_')
            **kwargs: Metadata key-value pairs to search for

        Returns:
            Query object with search criteria
        """
        query = session.query(cls)
        conditions = []

        for key, value in kwargs.items():
            if isinstance(value, (list, tuple)):
                conditions.append(
                    cls.metadata[key].astext.in_([json.dumps(v) for v in value])
                )
            else:
                conditions.append(cls.metadata[key].astext == json.dumps(value))

        if operator == "or_":
            query = query.filter(or_(*conditions))
        else:
            query = query.filter(and_(*conditions))

        return query

    @classmethod
    def get_unique_metadata_keys(cls, session: Any) -> List[str]:
        """
        Get all unique metadata keys used across instances.

        Args:
            session: SQLAlchemy session

        Returns:
            list: Unique metadata keys
        """
        result = session.query(cls.metadata).all()
        keys = set()
        for row in result:
            if row[0]:  # Check for None
                keys.update(row[0].keys())
        return sorted(list(keys))

    def validate_metadata(self, raise_error: bool = True) -> Union[bool, List[str]]:
        """
        Validate all metadata against schema and constraints.

        Args:
            raise_error (bool): Raise exception on validation failure

        Returns:
            bool or list: True if valid, or list of validation errors

        Raises:
            ValueError: If validation fails and raise_error is True
        """
        errors = []

        # Check required fields
        missing = set(self.__metadata_required__) - set(self.metadata.keys())
        if missing:
            errors.append(f"Missing required fields: {', '.join(missing)}")

        # Check field restrictions
        if self.__metadata_fields__:
            invalid = set(self.metadata.keys()) - set(self.__metadata_fields__)
            if invalid:
                errors.append(f"Invalid fields: {', '.join(invalid)}")

        # Type validation
        for key, value in self.metadata.items():
            if key in self.__metadata_types__:
                try:
                    self.__metadata_types__[key](value)
                except (ValueError, TypeError):
                    errors.append(
                        f"Invalid type for {key}: expected {self.__metadata_types__[key].__name__}"
                    )

        # Custom validators
        for key, validator in self.__metadata_validators__.items():
            if key in self.metadata:
                try:
                    if not validator(self.metadata[key]):
                        errors.append(f"Validation failed for {key}")
                except Exception as e:
                    errors.append(f"Validator error for {key}: {str(e)}")

        if errors and raise_error:
            raise ValueError("\n".join(errors))

        return True if not errors else errors

    def compute_metadata(self) -> None:
        """Update computed metadata fields."""
        for key, computer in self.__metadata_computed__.items():
            try:
                self.metadata[key] = computer(self)
            except Exception as e:
                logger.error(f"Error computing {key}: {str(e)}")

    def _validate_field(self, key: str, value: Any) -> None:
        """
        Validate a single metadata field.

        Args:
            key (str): Field name
            value: Field value

        Raises:
            ValueError: If validation fails
            TypeError: If type validation fails
        """
        if key in self.__metadata_types__:
            try:
                self.__metadata_types__[key](value)
            except (ValueError, TypeError):
                raise TypeError(
                    f"Invalid type for {key}: expected {self.__metadata_types__[key].__name__}"
                )

        if key in self.__metadata_validators__:
            if not self.__metadata_validators__[key](value):
                raise ValueError(f"Validation failed for {key}")

    def _track_change(self, key: str, value: Any) -> None:
        """Track metadata changes for auditing."""
        if not hasattr(self, "_metadata_changes"):
            self._metadata_changes = []

        self._metadata_changes.append(
            {
                "field": key,
                "old_value": self._original_metadata.get(key),
                "new_value": value,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    @classmethod
    def get_metadata_schema(cls) -> Optional[Dict[str, Any]]:
        """
        Get complete metadata schema definition.

        Returns:
            dict: Schema definition including types, defaults, etc.
        """
        if not (cls.__metadata_fields__ or cls.__metadata_types__):
            return None

        schema = {}
        for field in set(cls.__metadata_fields__) | set(cls.__metadata_types__.keys()):
            field_schema = {
                "type": cls.__metadata_types__.get(field, Any).__name__,
                "required": field in cls.__metadata_required__,
                "default": cls.__metadata_defaults__.get(field),
                "computed": field in cls.__metadata_computed__,
                "validator": bool(cls.__metadata_validators__.get(field)),
            }
            schema[field] = field_schema

        return schema


# SQLAlchemy event listeners
@event.listens_for(MetadataMixin, "before_update", propagate=True)
def validate_before_update(mapper, connection, target):
    """Validate metadata before updates."""
    if hasattr(target, "validate_metadata"):
        target.validate_metadata()


@event.listens_for(MetadataMixin, "before_insert", propagate=True)
def validate_before_insert(mapper, connection, target):
    """Validate metadata before inserts."""
    if hasattr(target, "validate_metadata"):
        target.validate_metadata()


# Example usage (commented out):
"""
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String
from mixins.metadata_mixin import MetadataMixin

class Product(MetadataMixin, Model):
    __tablename__ = 'nx_products'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

    # Metadata configuration
    __metadata_fields__ = ['color', 'size', 'material', 'price']
    __metadata_types__ = {
        'price': float,
        'size': str,
        'color': str,
        'material': str
    }
    __metadata_defaults__ = {
        'size': 'M',
        'color': 'black'
    }
    __metadata_required__ = ['color', 'size']
    __metadata_validators__ = {
        'price': lambda x: x >= 0,
        'size': lambda x: x in ['S', 'M', 'L', 'XL']
    }
    __metadata_computed__ = {
        'price_category': lambda obj: 'premium' if obj.metadata['price'] > 100 else 'standard'
    }
    __track_metadata__ = True
    __metadata_version__ = True

# Usage in application:

# Create with metadata
product = Product(
    name="T-Shirt",
    metadata={
        'color': 'blue',
        'size': 'L',
        'price': 29.99
    }
)

# Add and commit
db.session.add(product)
db.session.commit()

# Update metadata
product.update_metadata({
    'material': 'cotton',
    'price': 34.99
})

# Get computed fields
product.compute_metadata()

# Search products
premium_products = Product.search_by_metadata(
    db.session,
    price_category='premium'
)

# Get schema
schema = Product.get_metadata_schema()
"""
