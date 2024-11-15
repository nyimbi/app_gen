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

Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.0
"""

from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, event
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm.attributes import get_history
from flask_appbuilder.models.mixins import AuditMixin
from flask import current_app, g
import json
from datetime import datetime

class AuditLog(Model):
    """
    Model to store audit log entries.
    """
    __tablename__ = 'nx_audit_logs'

    id = Column(Integer, primary_key=True)
    table_name = Column(String(100), nullable=False)
    row_id = Column(Integer, nullable=False)
    action = Column(String(10), nullable=False)  # 'INSERT', 'UPDATE', or 'DELETE'
    user_id = Column(Integer, ForeignKey('ab_user.id'), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    change_data = Column(Text, nullable=True)  # JSON string of changes
    custom_message = Column(Text, nullable=True)

    user = relationship('User')

    def __repr__(self):
        return f"<AuditLog {self.id}: {self.action} on {self.table_name}:{self.row_id} by User {self.user_id}>"

class AuditLogMixin(AuditMixin):
    """
    A mixin class for adding detailed audit logging to SQLAlchemy models.

    This mixin tracks all changes to model instances and records them in a
    separate audit log table. It provides methods for querying and analyzing
    the audit log.

    Class Attributes:
        __audit_exclude__ (list): List of field names to exclude from audit logging.
    """

    __audit_exclude__ = []

    @declared_attr
    def audit_logs(cls):
        return relationship(AuditLog, 
                            primaryjoin=f"and_({cls.__name__}.id==AuditLog.row_id, "
                                        f"AuditLog.table_name=='{cls.__tablename__}')",
                            foreign_keys=[AuditLog.row_id, AuditLog.table_name],
                            backref='audited_object',
                            order_by=AuditLog.timestamp.desc())

    @classmethod
    def __declare_last__(cls):
        event.listen(cls, 'after_insert', cls._after_insert)
        event.listen(cls, 'after_update', cls._after_update)
        event.listen(cls, 'after_delete', cls._after_delete)

    @staticmethod
    def _get_current_user_id():
        try:
            return g.user.id if g.user.is_authenticated else None
        except:
            return None

    @classmethod
    def _after_insert(cls, mapper, connection, target):
        cls._log_change(connection, target, 'INSERT')

    @classmethod
    def _after_update(cls, mapper, connection, target):
        cls._log_change(connection, target, 'UPDATE')

    @classmethod
    def _after_delete(cls, mapper, connection, target):
        cls._log_change(connection, target, 'DELETE')

    @classmethod
    def _log_change(cls, connection, target, action):
        change_data = {}
        if action != 'DELETE':
            for column in target.__table__.columns:
                if column.key not in cls.__audit_exclude__:
                    history = get_history(target, column.key)
                    if history.has_changes():
                        change_data[column.key] = {
                            'old': cls._serialize_value(history.deleted[0] if history.deleted else None),
                            'new': cls._serialize_value(history.added[0] if history.added else None)
                        }

        log_entry = AuditLog(
            table_name=target.__tablename__,
            row_id=target.id,
            action=action,
            user_id=cls._get_current_user_id(),
            change_data=json.dumps(change_data) if change_data else None
        )

        connection.execute(
            AuditLog.__table__.insert().values(
                table_name=log_entry.table_name,
                row_id=log_entry.row_id,
                action=log_entry.action,
                user_id=log_entry.user_id,
                change_data=log_entry.change_data,
                timestamp=datetime.utcnow()
            )
        )

    @staticmethod
    def _serialize_value(value):
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value) if value is not None else None

    @classmethod
    def get_audit_logs(cls, instance_id=None, action=None, user_id=None, start_date=None, end_date=None):
        """
        Query audit logs for the model.

        Args:
            instance_id (int, optional): Filter logs for a specific instance.
            action (str, optional): Filter logs by action type ('INSERT', 'UPDATE', 'DELETE').
            user_id (int, optional): Filter logs by user ID.
            start_date (datetime, optional): Start date for log query.
            end_date (datetime, optional): End date for log query.

        Returns:
            list: List of AuditLog instances matching the query criteria.
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

        return query.order_by(AuditLog.timestamp.desc()).all()

    @classmethod
    def add_custom_audit_log(cls, instance, message, user_id=None):
        """
        Add a custom audit log message for an instance.

        Args:
            instance: The model instance to log for.
            message (str): The custom message to log.
            user_id (int, optional): The ID of the user making the log entry.
        """
        log_entry = AuditLog(
            table_name=cls.__tablename__,
            row_id=instance.id,
            action='CUSTOM',
            user_id=user_id or cls._get_current_user_id(),
            custom_message=message
        )
        current_app.extensions['sqlalchemy'].db.session.add(log_entry)
        current_app.extensions['sqlalchemy'].db.session.commit()

    def get_audit_trail(self):
        """
        Get the full audit trail for this instance.

        Returns:
            list: List of AuditLog instances for this object, ordered by timestamp descending.
        """
        return AuditLog.query.filter_by(
            table_name=self.__class__.__tablename__,
            row_id=self.id
        ).order_by(AuditLog.timestamp.desc()).all()

# Example usage (commented out):
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
