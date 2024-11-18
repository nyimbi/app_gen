"""
archive_mixin.py

This module provides an ArchiveMixin class for implementing archiving
functionality in SQLAlchemy models for Flask-AppBuilder applications.

The ArchiveMixin allows for marking records as archived without deleting them,
providing methods to archive and unarchive records, and automatically excluding
archived records from default queries.

Dependencies:
    - SQLAlchemy
    - Flask-AppBuilder

Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.0
"""

from flask_appbuilder import Model
from sqlalchemy import Column, Boolean, DateTime, event
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Query
from datetime import datetime, timedelta
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class ArchiveQuery(Query):
    """
    Custom query class that automatically filters out archived records.
    """
    def __new__(cls, *args, **kwargs):
        obj = super(ArchiveQuery, cls).__new__(cls)
        with_archived = kwargs.pop('_with_archived', False)
        if len(args) > 0:
            super(ArchiveQuery, obj).__init__(*args, **kwargs)
            return obj.filter(args[0].is_archived == False) if not with_archived else obj
        return obj

    def __init__(self, *args, **kwargs):
        pass

    def with_archived(self):
        """
        Include archived records in the query.

        Returns:
            ArchiveQuery: Query including archived records.
        """
        return self.__class__(self._only_full_mapper_zero('get'),
                              session=self.session,
                              _with_archived=True)

class ArchiveMixin:
    """
    A mixin class for adding archiving capabilities to SQLAlchemy models.

    This mixin provides methods for archiving and unarchiving records, as well as
    querying archived and active records.

    Class Attributes:
        __archive_cascade__ (list): List of relationship attribute names to cascade archive operations.
    """

    __archive_cascade__ = []

    @declared_attr
    def is_archived(cls):
        return Column(Boolean, nullable=False, default=False, index=True)

    @declared_attr
    def archived_at(cls):
        return Column(DateTime, nullable=True)

    @classmethod
    def __declare_last__(cls):
        cls.query_class = ArchiveQuery

    def archive(self, cascade=True):
        """
        Archive the record.

        Args:
            cascade (bool): Whether to cascade the archive operation to related records.

        Returns:
            bool: True if the record was archived, False if it was already archived.
        """
        if self.is_archived:
            return False

        self.is_archived = True
        self.archived_at = datetime.utcnow()

        if cascade:
            for attr_name in self.__archive_cascade__:
                related_obj = getattr(self, attr_name)
                if isinstance(related_obj, list):
                    for obj in related_obj:
                        if hasattr(obj, 'archive'):
                            obj.archive(cascade=True)
                elif hasattr(related_obj, 'archive'):
                    related_obj.archive(cascade=True)

        return True

    def unarchive(self, cascade=True):
        """
        Unarchive the record.

        Args:
            cascade (bool): Whether to cascade the unarchive operation to related records.

        Returns:
            bool: True if the record was unarchived, False if it wasn't archived.
        """
        if not self.is_archived:
            return False

        self.is_archived = False
        self.archived_at = None

        if cascade:
            for attr_name in self.__archive_cascade__:
                related_obj = getattr(self, attr_name)
                if isinstance(related_obj, list):
                    for obj in related_obj:
                        if hasattr(obj, 'unarchive'):
                            obj.unarchive(cascade=True)
                elif hasattr(related_obj, 'unarchive'):
                    related_obj.unarchive(cascade=True)

        return True

    @classmethod
    def archive_old_records(cls, age_days, cascade=True):
        """
        Archive records older than the specified age.

        Args:
            age_days (int): Age in days to determine which records to archive.
            cascade (bool): Whether to cascade the archive operation to related records.

        Returns:
            int: Number of records archived.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=age_days)
        query = cls.query.filter(cls.created_on <= cutoff_date, cls.is_archived == False)
        
        count = 0
        for record in query:
            if record.archive(cascade=cascade):
                count += 1

        current_app.db.session.commit()
        return count

    @classmethod
    def get_archive_stats(cls):
        """
        Get statistics on archived vs. active records.

        Returns:
            dict: Statistics including total, active, and archived record counts.
        """
        total_count = cls.query.count()
        archived_count = cls.query.with_archived().filter(cls.is_archived == True).count()
        active_count = total_count - archived_count

        return {
            "total_records": total_count,
            "active_records": active_count,
            "archived_records": archived_count,
            "archive_percentage": (archived_count / total_count * 100) if total_count > 0 else 0
        }

    @classmethod
    def get_archived(cls):
        """
        Get a query for archived records.

        Returns:
            Query: A query object for archived records.
        """
        return cls.query.with_archived().filter(cls.is_archived == True)

    @classmethod
    def get_active(cls):
        """
        Get a query for active (non-archived) records.

        Returns:
            Query: A query object for active records.
        """
        return cls.query

@event.listens_for(ArchiveMixin, 'before_update', propagate=True)
def prevent_update_of_archived_record(mapper, connection, target):
    """
    Prevent updates to archived records.

    This event listener will raise an exception if an attempt is made to update an archived record.
    """
    if target.is_archived:
        raise ValueError("Cannot update an archived record")

# Example usage (commented out):
"""
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from mixins.archive_mixin import ArchiveMixin

class Department(ArchiveMixin, Model):
    __tablename__ = 'nx_departments'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    employees = relationship('Employee', back_populates='department')

    __archive_cascade__ = ['employees']

class Employee(ArchiveMixin, Model):
    __tablename__ = 'nx_employees'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    department_id = Column(Integer, ForeignKey('nx_departments.id'))
    department = relationship('Department', back_populates='employees')

# In your application code:

# Creating and archiving a department
dept = Department(name="Old Department")
db.session.add(dept)
db.session.commit()

dept.archive()  # This will also archive all employees in the department
db.session.commit()

# Querying
active_depts = Department.get_active().all()
archived_depts = Department.get_archived().all()

# Unarchiving
dept.unarchive()
db.session.commit()

# Archiving old records
archived_count = Employee.archive_old_records(age_days=365)
print(f"Archived {archived_count} employees older than 1 year")

# Getting archive stats
stats = Department.get_archive_stats()
print(f"Archive stats: {stats}")

# Attempting to update an archived record (will raise an exception)
try:
    archived_dept = Department.get_archived().first()
    archived_dept.name = "New Name"
    db.session.commit()
except ValueError as e:
    print(f"Error: {str(e)}")
"""
