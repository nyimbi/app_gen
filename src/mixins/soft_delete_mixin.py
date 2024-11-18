"""
soft_delete_mixin.py

This module provides a SoftDeleteMixin class for implementing soft delete
functionality in SQLAlchemy models for Flask-AppBuilder applications.

The SoftDeleteMixin allows records to be marked as deleted without physically
removing them from the database. This is useful for maintaining data integrity,
allowing for data recovery, and implementing features like trash/recycle bin.

Dependencies:
    - SQLAlchemy
    - Flask-AppBuilder

Author: [Your Name]
Date: [Current Date]
Version: 1.0
"""

from sqlalchemy import Column, Boolean, DateTime
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Query
from sqlalchemy.orm.exc import NoResultFound
from flask_appbuilder.models.mixins import AuditMixin
from datetime import datetime

class SoftDeleteQuery(Query):
    """
    Custom query class that filters out soft-deleted records by default.
    """
    def __new__(cls, *args, **kwargs):
        obj = super(SoftDeleteQuery, cls).__new__(cls)
        with_deleted = kwargs.pop('_with_deleted', False)
        if len(args) > 0:
            super(SoftDeleteQuery, obj).__init__(*args, **kwargs)
            return obj.filter(args[0].is_deleted == False) if not with_deleted else obj
        return obj

    def __init__(self, *args, **kwargs):
        pass

    def with_deleted(self):
        """
        Include soft-deleted records in the query.

        Returns:
            SoftDeleteQuery: Query including soft-deleted records.
        """
        return self.__class__(self._only_full_mapper_zero('get'),
                              session=self.session,
                              _with_deleted=True)

    def _get(self):
        """
        Execute the query and return a result.

        Raises:
            NoResultFound: If no results are found.

        Returns:
            Model: The result of the query.
        """
        return self.with_deleted()

class SoftDeleteMixin(AuditMixin):
    """
    A mixin class for adding soft delete functionality to SQLAlchemy models.

    This mixin adds an 'is_deleted' column to the model and overrides the default
    query class to filter out soft-deleted records. It also provides methods for
    soft deleting and restoring records.

    Attributes:
        is_deleted (Column): Boolean column indicating if the record is soft-deleted.
        deleted_at (Column): DateTime column indicating when the record was soft-deleted.
    """

    __abstract__ = True

    @declared_attr
    def is_deleted(cls):
        return Column(Boolean, nullable=False, default=False, index=True)

    @declared_attr
    def deleted_at(cls):
        return Column(DateTime, nullable=True)

    @classmethod
    def __declare_last__(cls):
        cls.query_class = SoftDeleteQuery

    def soft_delete(self):
        """
        Mark the record as soft-deleted.
        """
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

    def restore(self):
        """
        Restore a soft-deleted record.
        """
        self.is_deleted = False
        self.deleted_at = None

    @classmethod
    def get_by_id(cls, record_id):
        """
        Get a record by its ID, including soft-deleted records.

        Args:
            record_id: The ID of the record to retrieve.

        Returns:
            Model: The retrieved record.

        Raises:
            NoResultFound: If no record with the given ID exists.
        """
        return cls.query.with_deleted().filter_by(id=record_id).one()

    @classmethod
    def get_active(cls):
        """
        Get a query for active (not soft-deleted) records.

        Returns:
            Query: A query object for active records.
        """
        return cls.query.filter_by(is_deleted=False)

    @classmethod
    def get_deleted(cls):
        """
        Get a query for soft-deleted records.

        Returns:
            Query: A query object for soft-deleted records.
        """
        return cls.query.with_deleted().filter_by(is_deleted=True)

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id}, is_deleted={self.is_deleted})>"

# Example usage (commented out):
"""
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String
from mixins.soft_delete_mixin import SoftDeleteMixin

class MyModel(SoftDeleteMixin, Model):
    __tablename__ = 'nx_my_model'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))

# In your application code:
# Create and add a new instance
instance = MyModel(name="Example")
db.session.add(instance)
db.session.commit()

# Soft delete the instance
instance.soft_delete()
db.session.commit()

# Query will not return soft-deleted records by default
active_records = MyModel.query.all()  # Does not include soft-deleted records

# Include soft-deleted records in query
all_records = MyModel.query.with_deleted().all()

# Get only soft-deleted records
deleted_records = MyModel.get_deleted().all()

# Restore a soft-deleted record
deleted_instance = MyModel.get_by_id(1)  # Retrieves the record even if it's soft-deleted
deleted_instance.restore()
db.session.commit()
"""
