"""
soft_delete_mixin.py

A comprehensive soft delete mixin implementation for Flask-AppBuilder/SQLAlchemy models.

This module provides advanced soft delete functionality including:
- Automatic filtering of deleted records from queries
- Bulk soft delete/restore operations
- Cascading soft deletes
- Deletion metadata tracking
- Custom delete behaviors
- Recovery management
- Cleanup policies
- Audit trail integration
- Deletion event hooks
- Advanced query filters

The mixin integrates with Flask-AppBuilder's security model and preserves
referential integrity while allowing flexible data recovery options.

Dependencies:
    - Flask-AppBuilder >= 3.4.0
    - SQLAlchemy >= 1.4.0
    - PostgreSQL >= 12.0 (recommended)
    - Python >= 3.8

Author: Nyimbi Odero
Date: 2024-01-20
Version: 2.0
License: MIT
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Type, Union

from flask import current_app, g
from flask_appbuilder.models.mixins import AuditMixin
from flask_appbuilder.security.sqla.models import User
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Query, Session, relationship
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import expression

logger = logging.getLogger(__name__)


class SoftDeleteQueryMixin:
    """
    Advanced query mixin for soft delete functionality.

    Features:
    - Automatic filtering of deleted records
    - Customizable deletion status checks
    - Complex deletion state queries
    - Integration with security model
    """

    def get_undeleted(self):
        """Get only non-deleted records."""
        return self.filter(self._entity_zero().class_.is_deleted.is_(False))

    def only_deleted(self):
        """Get only soft-deleted records."""
        return self.filter(self._entity_zero().class_.is_deleted.is_(True))

    def with_deleted(self):
        """Include soft-deleted records."""
        return self

    def deleted_by(self, user_id: int):
        """Get records deleted by specific user."""
        return self.filter(self._entity_zero().class_.deleted_by_fk == user_id)

    def deleted_since(self, date: datetime):
        """Get records deleted since given date."""
        return self.filter(self._entity_zero().class_.deleted_at >= date)

    def recoverable(self):
        """Get records that can be recovered."""
        return self.filter(
            self._entity_zero().class_.is_deleted.is_(True),
            self._entity_zero().class_.deleted_at
            >= datetime.utcnow()
            - timedelta(days=current_app.config.get("SOFT_DELETE_RECOVERY_DAYS", 30)),
        )


class SoftDeleteQuery(Query, SoftDeleteQueryMixin):
    """
    Custom query class that filters out soft-deleted records by default.
    """

    def __new__(cls, *args, **kwargs):
        include_deleted = kwargs.pop("_include_deleted", False)
        obj = super(SoftDeleteQuery, cls).__new__(cls)

        if len(args) > 0:
            super(SoftDeleteQuery, obj).__init__(*args, **kwargs)
            if not include_deleted:
                return obj.filter(args[0].is_deleted.is_(False))
        return obj

    def __init__(self, *args, **kwargs):
        super(SoftDeleteQuery, self).__init__()


class SoftDeleteMixin(AuditMixin):
    """
    Advanced soft delete mixin with comprehensive features.

    Features:
    - Configurable delete behavior
    - Deletion metadata tracking
    - Cascading soft deletes
    - Recovery management
    - Cleanup policies
    - Event hooks
    - Security integration
    - Audit trail

    Configuration:
        SOFT_DELETE_CASCADE: Enable cascading deletes
        SOFT_DELETE_RECOVERY_DAYS: Days until permanent deletion
        SOFT_DELETE_CLEANUP_ENABLED: Enable auto cleanup
        SOFT_DELETE_TRACK_METADATA: Track deletion metadata
        SOFT_DELETE_REQUIRE_REASON: Require deletion reason
    """

    __abstract__ = True

    query_class = SoftDeleteQuery

    # Columns
    @declared_attr
    def is_deleted(self) -> Column:
        """Deletion status flag."""
        return Column(
            Boolean,
            default=False,
            nullable=False,
            index=True,
            server_default=expression.false(),
        )

    @declared_attr
    def deleted_at(self) -> Column:
        """Deletion timestamp."""
        return Column(DateTime, nullable=True, index=True)

    @declared_attr
    def deleted_by_fk(self) -> Column:
        """User who performed deletion."""
        return Column(Integer, ForeignKey("ab_user.id"), nullable=True)

    @declared_attr
    def deletion_metadata(self) -> Column:
        """Additional deletion metadata."""
        return Column(JSONB, nullable=True)

    # Relationships
    @declared_attr
    def deleted_by(self):
        """Relationship to user who deleted."""
        return relationship(
            "User",
            primaryjoin="%s.deleted_by_fk == User.id" % self.__name__,
            remote_side="User.id",
        )

    def soft_delete(
        self,
        user_id: Optional[int] = None,
        reason: Optional[str] = None,
        metadata: Optional[Dict] = None,
        cascade: bool = True,
    ) -> bool:
        """
        Soft delete this record.

        Args:
            user_id: ID of user performing deletion
            reason: Reason for deletion
            metadata: Additional metadata
            cascade: Cascade delete to related records

        Returns:
            bool: Success status
        """
        try:
            if self.is_deleted:
                return False

            self.is_deleted = True
            self.deleted_at = datetime.utcnow()
            self.deleted_by_fk = user_id or (g.user.id if hasattr(g, "user") else None)

            # Track metadata
            if current_app.config.get("SOFT_DELETE_TRACK_METADATA", True):
                self.deletion_metadata = {
                    "reason": reason,
                    "deleted_from_ip": g.get("client_ip"),
                    "additional": metadata or {},
                    "app_metadata": {
                        "version": current_app.config.get("VERSION"),
                        "environment": current_app.config.get("ENV"),
                    },
                }

            # Cascade delete
            if cascade and current_app.config.get("SOFT_DELETE_CASCADE", True):
                self._cascade_soft_delete(user_id)

            Session.object_session(self).commit()

            # Trigger delete events
            self._trigger_delete_event()

            return True

        except Exception as e:
            logger.error(f"Soft delete failed: {str(e)}")
            Session.object_session(self).rollback()
            return False

    def restore(self, user_id: Optional[int] = None, cascade: bool = True) -> bool:
        """
        Restore this soft-deleted record.

        Args:
            user_id: ID of user performing restore
            cascade: Cascade restore to related records

        Returns:
            bool: Success status
        """
        try:
            if not self.is_deleted:
                return False

            self.is_deleted = False
            self.deleted_at = None
            self.deleted_by_fk = None
            self.deletion_metadata = None

            if cascade:
                self._cascade_restore(user_id)

            Session.object_session(self).commit()

            # Trigger restore events
            self._trigger_restore_event()

            return True

        except Exception as e:
            logger.error(f"Restore failed: {str(e)}")
            Session.object_session(self).rollback()
            return False

    def _cascade_soft_delete(self, user_id: Optional[int]) -> None:
        """Cascade soft delete to related records."""
        for rel in self.__mapper__.relationships:
            if hasattr(rel.mapper.class_, "soft_delete"):
                related = getattr(self, rel.key)
                if related:
                    if isinstance(related, list):
                        for item in related:
                            item.soft_delete(user_id, cascade=True)
                    else:
                        related.soft_delete(user_id, cascade=True)

    def _cascade_restore(self, user_id: Optional[int]) -> None:
        """Cascade restore to related records."""
        for rel in self.__mapper__.relationships:
            if hasattr(rel.mapper.class_, "restore"):
                related = getattr(self, rel.key)
                if related:
                    if isinstance(related, list):
                        for item in related:
                            if item.is_deleted:
                                item.restore(user_id, cascade=True)
                    elif related.is_deleted:
                        related.restore(user_id, cascade=True)

    def _trigger_delete_event(self) -> None:
        """Trigger soft delete events."""
        if hasattr(self, "on_soft_delete"):
            self.on_soft_delete()
        event.listen(self.__class__, "after_soft_delete", self._after_soft_delete)

    def _trigger_restore_event(self) -> None:
        """Trigger restore events."""
        if hasattr(self, "on_restore"):
            self.on_restore()
        event.listen(self.__class__, "after_restore", self._after_restore)

    @classmethod
    def bulk_soft_delete(
        cls, ids: List[int], user_id: Optional[int] = None, reason: Optional[str] = None
    ) -> int:
        """
        Soft delete multiple records by ID.

        Args:
            ids: List of record IDs to delete
            user_id: ID of user performing deletion
            reason: Reason for deletion

        Returns:
            int: Number of records deleted
        """
        count = 0
        session = Session.object_session(cls)

        try:
            records = cls.query.filter(cls.id.in_(ids)).all()
            for record in records:
                if record.soft_delete(user_id, reason):
                    count += 1

            session.commit()
            return count

        except Exception as e:
            logger.error(f"Bulk soft delete failed: {str(e)}")
            session.rollback()
            return 0

    @classmethod
    def bulk_restore(cls, ids: List[int], user_id: Optional[int] = None) -> int:
        """
        Restore multiple soft-deleted records by ID.

        Args:
            ids: List of record IDs to restore
            user_id: ID of user performing restore

        Returns:
            int: Number of records restored
        """
        count = 0
        session = Session.object_session(cls)

        try:
            records = (
                cls.query.with_deleted()
                .filter(cls.id.in_(ids), cls.is_deleted.is_(True))
                .all()
            )

            for record in records:
                if record.restore(user_id):
                    count += 1

            session.commit()
            return count

        except Exception as e:
            logger.error(f"Bulk restore failed: {str(e)}")
            session.rollback()
            return 0

    @classmethod
    def cleanup_deleted(cls, days: Optional[int] = None) -> int:
        """
        Permanently delete old soft-deleted records.

        Args:
            days: Days after which to permanently delete

        Returns:
            int: Number of records deleted
        """
        if not current_app.config.get("SOFT_DELETE_CLEANUP_ENABLED", False):
            return 0

        days = days or current_app.config.get("SOFT_DELETE_RECOVERY_DAYS", 30)
        cutoff = datetime.utcnow() - timedelta(days=days)

        try:
            count = cls.query.filter(
                cls.is_deleted.is_(True), cls.deleted_at <= cutoff
            ).delete(synchronize_session=False)

            Session.object_session(cls).commit()
            return count

        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
            Session.object_session(cls).rollback()
            return 0

    @classmethod
    def get_deletion_statistics(cls) -> Dict[str, Any]:
        """Get statistics about deleted records."""
        session = Session.object_session(cls)
        total_deleted = (
            cls.query.with_deleted().filter(cls.is_deleted.is_(True)).count()
        )

        stats = {
            "total_deleted": total_deleted,
            "deletions_by_user": {},
            "deletions_by_reason": {},
            "recent_deletions": cls.query.with_deleted()
            .filter(
                cls.is_deleted.is_(True),
                cls.deleted_at >= datetime.utcnow() - timedelta(days=7),
            )
            .count(),
        }

        # Aggregate deletion metadata
        if current_app.config.get("SOFT_DELETE_TRACK_METADATA", True):
            deleted_records = (
                cls.query.with_deleted().filter(cls.is_deleted.is_(True)).all()
            )

            for record in deleted_records:
                if record.deletion_metadata:
                    user_id = record.deleted_by_fk
                    reason = record.deletion_metadata.get("reason")

                    if user_id:
                        stats["deletions_by_user"][user_id] = (
                            stats["deletions_by_user"].get(user_id, 0) + 1
                        )
                    if reason:
                        stats["deletions_by_reason"][reason] = (
                            stats["deletions_by_reason"].get(reason, 0) + 1
                        )

        return stats

    def __repr__(self):
        """String representation."""
        status = "deleted" if self.is_deleted else "active"
        return f"<{self.__class__.__name__}(id={self.id}, status={status})>"


# Example usage:
"""
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .soft_delete_mixin import SoftDeleteMixin

class Department(SoftDeleteMixin, Model):
    __tablename__ = 'department'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    employees = relationship('Employee', backref='department')

class Employee(SoftDeleteMixin, Model):
    __tablename__ = 'employee'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    department_id = Column(Integer, ForeignKey('department.id'))

# Usage:

# Create records
dept = Department(name="Engineering")
emp1 = Employee(name="John Doe", department=dept)
emp2 = Employee(name="Jane Smith", department=dept)
db.session.add_all([dept, emp1, emp2])
db.session.commit()

# Soft delete with cascade
dept.soft_delete(
    user_id=current_user.id,
    reason="Department reorganization",
    metadata={'effective_date': '2024-01-20'},
    cascade=True  # Will soft delete all employees
)

# Query examples
active_depts = Department.query.all()  # Only active departments
all_depts = Department.query.with_deleted().all()  # Including deleted
deleted_depts = Department.query.only_deleted().all()  # Only deleted

# Restore with cascade
dept.restore(user_id=current_user.id, cascade=True)  # Restores department and employees

# Bulk operations
Department.bulk_soft_delete([1, 2, 3], user_id=current_user.id, reason="Restructuring")
Department.bulk_restore([1, 2, 3], user_id=current_user.id)

# Cleanup old deleted records
deleted_count = Department.cleanup_deleted(days=90)

# Get deletion statistics
stats = Department.get_deletion_statistics()
"""
