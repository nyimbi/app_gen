"""
audit_log_mixin.py

This module provides an AuditLogMixin class for implementing detailed audit
logging in SQLAlchemy models for Flask-AppBuilder applications.

The AuditLogMixin tracks all changes (create, update, delete) to model instances,
recording who made the changes, when they were made, and the before and after
states of changed fields.

Dependencies:
    - SQLAlchemy
    - Flask-AppBuilder
    - Flask (for current_user)
    - PostgreSQL

Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.1
"""

import enum
import ipaddress
import json
import uuid
from datetime import datetime

from flask import current_app, g, request
from flask_appbuilder import Model
from flask_appbuilder.models.mixins import AuditMixin
from sqlalchemy import (
    ARRAY,
    JSON,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    event,
)
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import backref, relationship
from sqlalchemy.orm.attributes import get_history


class AuditActionType(enum.Enum):
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CUSTOM = "CUSTOM"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    VIEW = "VIEW"
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"


class AuditLog(Model):
    """
    Model to store detailed audit log entries.

    Attributes:
        id (int): Primary key
        table_name (str): Name of audited table
        row_id (int): Primary key of audited record
        action (AuditActionType): Type of action performed
        user_id (int): ID of user who performed action
        timestamp (datetime): When action occurred
        change_data (JSONB): Changes in JSON format
        custom_message (Text): Optional custom message
        client_ip (INET): Client IP address
        user_agent (Text): User agent string
        session_id (String): Session identifier
        request_id (UUID): Unique request identifier
        related_records (JSONB): Related record references
        change_reason (Text): Reason for change
        app_version (String): Application version
        environment (String): Environment (prod/dev/test)
        tags (ARRAY): Searchable tags
    """

    __tablename__ = "nx_audit_logs"

    id = Column(Integer, primary_key=True)
    table_name = Column(String(100), nullable=False, index=True)
    row_id = Column(Integer, nullable=False, index=True)
    action = Column(Enum(AuditActionType), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("ab_user.id"), nullable=True, index=True)
    timestamp = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )
    change_data = Column(JSONB, nullable=True)
    custom_message = Column(Text, nullable=True)
    client_ip = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(100), nullable=True)
    request_id = Column(String(36), default=lambda: str(uuid.uuid4()), nullable=False)
    related_records = Column(JSONB, nullable=True)
    change_reason = Column(Text, nullable=True)
    app_version = Column(String(50), nullable=True)
    environment = Column(String(20), nullable=True)
    tags = Column(ARRAY(String), nullable=True)

    # Relationships
    user = relationship("User", backref=backref("audit_logs", lazy="dynamic"))

    __table_args__ = (
        # Compound indexes
        {"postgresql_partition_by": "RANGE (timestamp)"}
    )

    def __repr__(self):
        return (
            f"<AuditLog {self.id}: {self.action.value} on {self.table_name}:"
            f"{self.row_id} by User {self.user_id} at {self.timestamp}>"
        )


class AuditLogMixin(AuditMixin):
    """
    A mixin class for adding detailed audit logging to SQLAlchemy models.

    This mixin tracks all changes to model instances and records them in a
    separate audit log table. It provides methods for querying and analyzing
    the audit log.

    Class Attributes:
        __audit_exclude__ (list): Fields to exclude from audit logging
        __audit_include__ (list): Fields to specifically include in audit logging
        __audit_handlers__ (dict): Custom handlers for specific fields
        __audit_masked_fields__ (list): Fields to mask in logs (e.g. passwords)
        __audit_serialize_rules__ (dict): Custom serialization rules
    """

    __audit_exclude__ = ["created_by", "created_on", "changed_by", "changed_on"]
    __audit_include__ = None
    __audit_handlers__ = {}
    __audit_masked_fields__ = ["password", "secret", "key", "token"]
    __audit_serialize_rules__ = {}

    @declared_attr
    def audit_logs(cls):
        """Define relationship to audit logs"""
        return relationship(
            AuditLog,
            primaryjoin=f"and_({cls.__name__}.id==AuditLog.row_id, "
            f"AuditLog.table_name=='{cls.__tablename__}')",
            foreign_keys=[AuditLog.row_id, AuditLog.table_name],
            backref="audited_object",
            order_by=AuditLog.timestamp.desc(),
            cascade="all, delete-orphan",
        )

    @classmethod
    def __declare_last__(cls):
        event.listen(cls, "after_insert", cls._after_insert)
        event.listen(cls, "after_update", cls._after_update)
        event.listen(cls, "after_delete", cls._after_delete)

    @staticmethod
    def _get_current_user_id():
        """Get current user ID safely"""
        try:
            return g.user.id if hasattr(g, "user") and g.user.is_authenticated else None
        except Exception:
            return None

    @staticmethod
    def _get_request_info():
        """Get current request information"""
        try:
            return {
                "client_ip": ipaddress.ip_address(request.remote_addr).exploded,
                "user_agent": request.user_agent.string if request.user_agent else None,
                "session_id": request.cookies.get("session"),
            }
        except Exception:
            return {"client_ip": None, "user_agent": None, "session_id": None}

    @classmethod
    def _after_insert(cls, mapper, connection, target):
        """Handle after insert event"""
        cls._log_change(connection, target, AuditActionType.INSERT)

    @classmethod
    def _after_update(cls, mapper, connection, target):
        """Handle after update event"""
        cls._log_change(connection, target, AuditActionType.UPDATE)

    @classmethod
    def _after_delete(cls, mapper, connection, target):
        """Handle after delete event"""
        cls._log_change(connection, target, AuditActionType.DELETE)

    @classmethod
    def _should_audit_field(cls, field_name):
        """Determine if field should be audited"""
        if field_name in cls.__audit_masked_fields__:
            return False
        if cls.__audit_include__ is not None:
            return field_name in cls.__audit_include__
        return field_name not in cls.__audit_exclude__

    @classmethod
    def _log_change(cls, connection, target, action):
        """Log a change to the audit log"""
        change_data = {}
        related_records = {}

        if action != AuditActionType.DELETE:
            for column in target.__table__.columns:
                if cls._should_audit_field(column.key):
                    history = get_history(target, column.key)
                    if history.has_changes():
                        old_value = history.deleted[0] if history.deleted else None
                        new_value = history.added[0] if history.added else None

                        # Apply custom handler if exists
                        if column.key in cls.__audit_handlers__:
                            old_value, new_value = cls.__audit_handlers__[column.key](
                                old_value, new_value
                            )

                        change_data[column.key] = {
                            "old": cls._serialize_value(old_value),
                            "new": cls._serialize_value(new_value),
                        }

                        # Track related record changes
                        if isinstance(column, ForeignKey):
                            related_records[column.key] = {
                                "table": column.target_fullname,
                                "id": new_value,
                            }

        request_info = cls._get_request_info()

        log_entry = AuditLog(
            table_name=target.__tablename__,
            row_id=target.id,
            action=action,
            user_id=cls._get_current_user_id(),
            change_data=change_data if change_data else None,
            client_ip=request_info["client_ip"],
            user_agent=request_info["user_agent"],
            session_id=request_info["session_id"],
            related_records=related_records if related_records else None,
            app_version=current_app.config.get("APP_VERSION"),
            environment=current_app.config.get("ENVIRONMENT"),
            tags=cls._generate_tags(target, action, change_data),
        )

        connection.execute(
            AuditLog.__table__.insert().values(
                table_name=log_entry.table_name,
                row_id=log_entry.row_id,
                action=log_entry.action,
                user_id=log_entry.user_id,
                change_data=log_entry.change_data,
                timestamp=datetime.utcnow(),
                client_ip=log_entry.client_ip,
                user_agent=log_entry.user_agent,
                session_id=log_entry.session_id,
                request_id=log_entry.request_id,
                related_records=log_entry.related_records,
                app_version=log_entry.app_version,
                environment=log_entry.environment,
                tags=log_entry.tags,
            )
        )

    @classmethod
    def _generate_tags(cls, target, action, change_data):
        """Generate searchable tags for the audit log entry"""
        tags = [
            f"table:{target.__tablename__}",
            f"action:{action.value}",
            f"id:{target.id}",
        ]

        if hasattr(target, "tags"):
            tags.extend(getattr(target, "tags", []))

        return tags

    @staticmethod
    def _serialize_value(value):
        """Serialize a value for storage"""
        if value is None:
            return None
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, enum.Enum):
            return value.value
        if isinstance(value, (list, dict)):
            return json.dumps(value)
        return str(value)

    @classmethod
    def get_audit_logs(
        cls,
        instance_id=None,
        action=None,
        user_id=None,
        start_date=None,
        end_date=None,
        tags=None,
        limit=None,
    ):
        """
        Query audit logs with advanced filtering.

        Args:
            instance_id (int, optional): Filter by instance ID
            action (AuditActionType, optional): Filter by action type
            user_id (int, optional): Filter by user ID
            start_date (datetime, optional): Start date for query
            end_date (datetime, optional): End date for query
            tags (list, optional): Filter by tags
            limit (int, optional): Limit number of results

        Returns:
            list: Matching AuditLog instances
        """
        query = AuditLog.query.filter_by(table_name=cls.__tablename__)

        if instance_id is not None:
            query = query.filter_by(row_id=instance_id)
        if action:
            query = query.filter_by(action=action)
        if user_id:
            query = query.filter_by(user_id=user_id)
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        if tags:
            query = query.filter(AuditLog.tags.contains(tags))

        query = query.order_by(AuditLog.timestamp.desc())

        if limit:
            query = query.limit(limit)

        return query.all()

    @classmethod
    def add_custom_audit_log(
        cls,
        instance,
        message,
        user_id=None,
        tags=None,
        reason=None,
        related_records=None,
    ):
        """
        Add a custom audit log entry.

        Args:
            instance: Model instance to log for
            message (str): Custom message
            user_id (int, optional): User ID override
            tags (list, optional): Additional tags
            reason (str, optional): Change reason
            related_records (dict, optional): Related record references
        """
        request_info = cls._get_request_info()

        log_entry = AuditLog(
            table_name=cls.__tablename__,
            row_id=instance.id,
            action=AuditActionType.CUSTOM,
            user_id=user_id or cls._get_current_user_id(),
            custom_message=message,
            client_ip=request_info["client_ip"],
            user_agent=request_info["user_agent"],
            session_id=request_info["session_id"],
            change_reason=reason,
            related_records=related_records,
            app_version=current_app.config.get("APP_VERSION"),
            environment=current_app.config.get("ENVIRONMENT"),
            tags=tags or [],
        )

        db = current_app.extensions["sqlalchemy"].db
        db.session.add(log_entry)
        db.session.commit()

    def get_audit_trail(self, include_related=False, limit=None):
        """
        Get full audit trail for this instance.

        Args:
            include_related (bool): Include related record changes
            limit (int, optional): Limit number of results

        Returns:
            list: AuditLog instances ordered by timestamp
        """
        query = AuditLog.query.filter_by(
            table_name=self.__class__.__tablename__, row_id=self.id
        )

        if include_related:
            query = query.filter(
                or_(
                    AuditLog.row_id == self.id,
                    AuditLog.related_records.contains({"id": self.id}),
                )
            )

        query = query.order_by(AuditLog.timestamp.desc())

        if limit:
            query = query.limit(limit)

        return query.all()


# Example usage remains the same
"""
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, Float
from mixins.audit_log_mixin import AuditLogMixin

class Product(AuditLogMixin, Model):
    __tablename__ = 'nx_products'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)

    __audit_exclude__ = ['updated_at']  # Exclude 'updated_at' from audit logs

# In your application code:

# Create a new product (this will generate an INSERT audit log)
new_product = Product(name="New Widget", price=19.99)
db.session.add(new_product)
db.session.commit()

# Update the product (this will generate an UPDATE audit log)
new_product.price = 24.99
db.session.commit()

# Add a custom audit log
Product.add_custom_audit_log(new_product, "Price increased due to supply shortage")

# Query audit logs
audit_logs = Product.get_audit_logs(instance_id=new_product.id)
for log in audit_logs:
    print(f"{log.action} at {log.timestamp} by User {log.user_id}")
    if log.change_data:
        changes = json.loads(log.change_data)
        for field, change in changes.items():
            print(f"  {field}: {change['old']} -> {change['new']}")

# Get full audit trail for a specific product
product = Product.query.get(1)
audit_trail = product.get_audit_trail()
for log in audit_trail:
    print(f"{log.action} at {log.timestamp}")
"""
