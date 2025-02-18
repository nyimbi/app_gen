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
    Custom query class that automatically filters out archived records unless explicitly included.

    This query class integrates with SQLAlchemy to provide automatic filtering of archived records
    while allowing opt-in inclusion of archived records when needed. It maintains compatibility with
    all standard SQLAlchemy query operations.

    Usage:
        # Normal query - excludes archived records
        Model.query.all()

        # Include archived records
        Model.query.with_archived().all()
    """

    def __new__(cls, *args, **kwargs):
        obj = super(ArchiveQuery, cls).__new__(cls)
        with_archived = kwargs.pop("_with_archived", False)
        if len(args) > 0:
            super(ArchiveQuery, obj).__init__(*args, **kwargs)
            return obj.filter(not args[0].is_archived) if not with_archived else obj
        return obj

    def __init__(self, *args, **kwargs):
        super(ArchiveQuery, self).__init__(*args, **kwargs)

    def with_archived(self):
        """
        Include archived records in the query.

        Returns:
            ArchiveQuery: Query including archived records.
        """
        return self.__class__(
            self._only_full_mapper_zero("get"),
            session=self.session,
            _with_archived=True,
        )


class ArchiveMixin:
    """
    A mixin class for adding archiving capabilities to SQLAlchemy models.

    This mixin adds soft-delete functionality through archiving, allowing records to be
    hidden without being permanently deleted. It supports cascading operations and
    provides methods for managing archived records.

    Features:
    - Automatic filtering of archived records
    - Cascading archive operations
    - Archive/unarchive timestamps
    - Bulk archiving operations
    - Archive statistics
    - Prevention of archived record updates

    Class Attributes:
        __archive_cascade__ (list): List of relationship attribute names to cascade archive operations
        __allow_archive_update__ (bool): Whether to allow updates to archived records (default: False)
        __archive_on_delete__ (bool): Whether to archive instead of delete (default: True)
    """

    __archive_cascade__ = []
    __allow_archive_update__ = False
    __archive_on_delete__ = True

    @declared_attr
    def is_archived(cls):
        """Boolean flag indicating if the record is archived."""
        return Column(
            "is_archived",
            Boolean,
            nullable=False,
            default=False,
            index=True,
            server_default="false",
            comment="Indicates if the record is archived",
        )

    @declared_attr
    def archived_at(cls):
        """Timestamp when the record was archived."""
        return Column(
            "archived_at",
            DateTime(timezone=True),
            nullable=True,
            index=True,
            comment="Timestamp when record was archived",
        )

    @declared_attr
    def archived_by_id(cls):
        """ID of the user who archived the record."""
        return Column(
            "archived_by_id",
            Integer,
            nullable=True,
            index=True,
            comment="ID of user who archived the record",
        )

    @classmethod
    def __declare_last__(cls):
        """Configure the query class and set up event listeners."""
        cls.query_class = ArchiveQuery

    def archive(self, cascade=True, user_id=None):
        """
        Archive the record and optionally cascade to related records.

        Args:
            cascade (bool): Whether to cascade the archive operation to related records
            user_id (int): ID of the user performing the archive operation

        Returns:
            bool: True if the record was archived, False if already archived

        Raises:
            ValueError: If the record cannot be archived
        """
        if self.is_archived:
            return False

        try:
            setattr(self, "is_archived", True)
            setattr(self, "archived_at", datetime.utcnow())
            setattr(self, "archived_by_id", user_id)

            if cascade:
                for attr_name in self.__archive_cascade__:
                    related_obj = getattr(self, attr_name, None)
                    if related_obj is not None:
                        if isinstance(related_obj, list):
                            for obj in related_obj:
                                if hasattr(obj, "archive"):
                                    obj.archive(cascade=True, user_id=user_id)
                        elif hasattr(related_obj, "archive"):
                            related_obj.archive(cascade=True, user_id=user_id)

            return True
        except Exception as e:
            logger.error(f"Error archiving record: {str(e)}")
            raise ValueError(f"Failed to archive record: {str(e)}")

    def unarchive(self, cascade=True, user_id=None):
        """
        Unarchive the record and optionally cascade to related records.

        Args:
            cascade (bool): Whether to cascade the unarchive operation
            user_id (int): ID of the user performing the unarchive operation

        Returns:
            bool: True if unarchived, False if not archived

        Raises:
            ValueError: If the record cannot be unarchived
        """
        if not self.is_archived:
            return False

        try:
            setattr(self, "is_archived", False)
            setattr(self, "archived_at", None)
            setattr(self, "archived_by_id", None)

            if cascade:
                for attr_name in self.__archive_cascade__:
                    related_obj = getattr(self, attr_name, None)
                    if related_obj is not None:
                        if isinstance(related_obj, list):
                            for obj in related_obj:
                                if hasattr(obj, "unarchive"):
                                    obj.unarchive(cascade=True, user_id=user_id)
                        elif hasattr(related_obj, "unarchive"):
                            related_obj.unarchive(cascade=True, user_id=user_id)

            return True
        except Exception as e:
            logger.error(f"Error unarchiving record: {str(e)}")
            raise ValueError(f"Failed to unarchive record: {str(e)}")

    @classmethod
    def archive_old_records(cls, age_days, cascade=True, user_id=None):
        """
        Archive records older than the specified age.

        Args:
            age_days (int): Age in days to determine which records to archive
            cascade (bool): Whether to cascade the archive operation
            user_id (int): ID of the user performing the bulk archive

        Returns:
            int: Number of records archived

        Raises:
            ValueError: If the operation fails
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=age_days)
            records = cls.query.filter(
                cls.created_date <= cutoff_date, not cls.is_archived
            ).all()

            count = 0
            for record in records:
                if record.archive(cascade=cascade, user_id=user_id):
                    count += 1

            return count
        except Exception as e:
            logger.error(f"Error in bulk archive: {str(e)}")
            raise ValueError(f"Failed to archive old records: {str(e)}")

    @classmethod
    def get_archive_stats(cls):
        """
        Get detailed statistics on archived vs. active records.

        Returns:
            dict: Statistics including counts, percentages, and timing information
        """
        try:
            base_query = db.session.query(cls)
            total_count = base_query.count()
            archived_count = base_query.filter(cls.is_archived).count()
            active_count = total_count - archived_count

            latest_archive = (
                base_query.filter(cls.is_archived)
                .order_by(cls.archived_at.desc())
                .first()
            )

            return {
                "total_records": total_count,
                "active_records": active_count,
                "archived_records": archived_count,
                "archive_percentage": (
                    (archived_count / total_count * 100) if total_count > 0 else 0
                ),
                "latest_archive_date": (
                    latest_archive.archived_at if latest_archive else None
                ),
                "latest_archive_by": (
                    latest_archive.archived_by_id if latest_archive else None
                ),
            }
        except Exception as e:
            logger.error(f"Error getting archive stats: {str(e)}")
            raise ValueError(f"Failed to get archive statistics: {str(e)}")

    @classmethod
    def get_archived(cls):
        """
        Get a query for archived records.

        Returns:
            Query: A query object for archived records
        """
        return db.session.query(cls).filter(cls.is_archived)

    @classmethod
    def get_active(cls):
        """
        Get a query for active (non-archived) records.

        Returns:
            Query: A query object for active records
        """
        return db.session.query(cls).filter(not cls.is_archived)


@event.listens_for(ArchiveMixin, "before_update", propagate=True)
def prevent_update_of_archived_record(mapper, connection, target):
    """
    Prevent updates to archived records unless explicitly allowed.

    Args:
        mapper: The Mapper object
        connection: The Connection object
        target: The model instance being updated

    Raises:
        ValueError: If an attempt is made to update an archived record
    """
    if target.is_archived and not getattr(target, "__allow_archive_update__", False):
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
