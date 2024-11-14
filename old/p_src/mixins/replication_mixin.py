"""
replication_mixin.py

This module provides a ReplicationMixin class for facilitating data replication
across multiple databases in SQLAlchemy models for Flask-AppBuilder applications.

The ReplicationMixin is useful for distributed systems or high-availability setups,
allowing seamless replication of data across different database instances.

Dependencies:
    - SQLAlchemy
    - Flask-AppBuilder
    - sqlalchemy-replicated (for multi-database session management)

Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.0
"""

from flask_appbuilder import Model
from sqlalchemy import Column, Integer, DateTime, event
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy_replicated import ReplicatedSession
from flask import current_app
from datetime import datetime
import uuid

class ReplicationMixin:
    """
    A mixin class for adding data replication capabilities to SQLAlchemy models.

    This mixin provides methods for replicating data across multiple databases,
    managing replication status, and handling conflict resolution.

    Class Attributes:
        __replication_key__ (str): The attribute name to use as the replication key.
        __replication_databases__ (list): List of database URLs for replication.
    """

    __replication_key__ = 'replication_id'
    __replication_databases__ = []

    @declared_attr
    def replication_id(cls):
        return Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))

    @declared_attr
    def last_replicated(cls):
        return Column(DateTime, nullable=True)

    @classmethod
    def __declare_last__(cls):
        event.listen(cls, 'after_insert', cls._after_insert)
        event.listen(cls, 'after_update', cls._after_update)

    @classmethod
    def _after_insert(cls, mapper, connection, target):
        cls._replicate(target, 'insert')

    @classmethod
    def _after_update(cls, mapper, connection, target):
        cls._replicate(target, 'update')

    @classmethod
    def _replicate(cls, instance, operation):
        """
        Replicate the instance to other databases.

        Args:
            instance: The model instance to replicate.
            operation (str): The operation type ('insert' or 'update').
        """
        replication_data = cls._prepare_replication_data(instance)
        
        for db_url in cls.__replication_databases__:
            replicated_session = ReplicatedSession(db_url)
            try:
                if operation == 'insert':
                    replicated_session.add(cls(**replication_data))
                elif operation == 'update':
                    replicated_obj = replicated_session.query(cls).filter_by(
                        replication_id=instance.replication_id).first()
                    if replicated_obj:
                        for key, value in replication_data.items():
                            setattr(replicated_obj, key, value)
                replicated_session.commit()
            except Exception as e:
                current_app.logger.error(f"Replication error for {cls.__name__}: {str(e)}")
                replicated_session.rollback()
            finally:
                replicated_session.close()

        instance.last_replicated = datetime.utcnow()

    @classmethod
    def _prepare_replication_data(cls, instance):
        """
        Prepare the data for replication.

        Args:
            instance: The model instance to prepare data from.

        Returns:
            dict: A dictionary of data to be replicated.
        """
        return {c.key: getattr(instance, c.key) for c in instance.__table__.columns
                if c.key not in ['id', 'last_replicated']}

    @classmethod
    def sync_from_primary(cls, primary_db_url):
        """
        Synchronize data from the primary database to all replicas.

        Args:
            primary_db_url (str): The database URL of the primary database.
        """
        primary_session = ReplicatedSession(primary_db_url)
        primary_data = primary_session.query(cls).all()

        for db_url in cls.__replication_databases__:
            if db_url != primary_db_url:
                replicated_session = ReplicatedSession(db_url)
                try:
                    for instance in primary_data:
                        replication_data = cls._prepare_replication_data(instance)
                        replicated_obj = replicated_session.query(cls).filter_by(
                            replication_id=instance.replication_id).first()
                        if replicated_obj:
                            for key, value in replication_data.items():
                                setattr(replicated_obj, key, value)
                        else:
                            replicated_session.add(cls(**replication_data))
                    replicated_session.commit()
                except Exception as e:
                    current_app.logger.error(f"Sync error for {cls.__name__}: {str(e)}")
                    replicated_session.rollback()
                finally:
                    replicated_session.close()

        primary_session.close()

    @classmethod
    def resolve_conflicts(cls, conflict_resolution_strategy=None):
        """
        Resolve conflicts across all replicated databases.

        Args:
            conflict_resolution_strategy (callable, optional): A function to resolve conflicts.
                If not provided, the latest update wins.
        """
        all_data = {}
        for db_url in cls.__replication_databases__:
            session = ReplicatedSession(db_url)
            all_data[db_url] = session.query(cls).all()
            session.close()

        resolved_data = {}
        for replication_id in set(instance.replication_id for instances in all_data.values() for instance in instances):
            conflicting_instances = [instance for instances in all_data.values() for instance in instances if instance.replication_id == replication_id]
            if conflict_resolution_strategy:
                resolved_instance = conflict_resolution_strategy(conflicting_instances)
            else:
                resolved_instance = max(conflicting_instances, key=lambda x: x.last_replicated)
            resolved_data[replication_id] = resolved_instance

        for db_url in cls.__replication_databases__:
            session = ReplicatedSession(db_url)
            try:
                for replication_id, resolved_instance in resolved_data.items():
                    local_instance = session.query(cls).filter_by(replication_id=replication_id).first()
                    if local_instance:
                        for key, value in cls._prepare_replication_data(resolved_instance).items():
                            setattr(local_instance, key, value)
                    else:
                        session.add(cls(**cls._prepare_replication_data(resolved_instance)))
                session.commit()
            except Exception as e:
                current_app.logger.error(f"Conflict resolution error for {cls.__name__}: {str(e)}")
                session.rollback()
            finally:
                session.close()

# Example usage (commented out):
"""
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String
from mixins.replication_mixin import ReplicationMixin

class User(ReplicationMixin, Model):
    __tablename__ = 'nx_users'
    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False, unique=True)
    email = Column(String(100), nullable=False)

    __replication_databases__ = [
        'postgresql://user:pass@db1/myapp',
        'postgresql://user:pass@db2/myapp',
        'postgresql://user:pass@db3/myapp'
    ]

# In your application code:

# Creating a new user (will be replicated automatically)
new_user = User(username="john_doe", email="john@example.com")
db.session.add(new_user)
db.session.commit()

# Updating a user (changes will be replicated)
user = User.query.filter_by(username="john_doe").first()
user.email = "john.doe@example.com"
db.session.commit()

# Syncing from primary database
User.sync_from_primary('postgresql://user:pass@primary_db/myapp')

# Resolving conflicts
def custom_conflict_resolution(conflicting_instances):
    # Custom logic to resolve conflicts
    return max(conflicting_instances, key=lambda x: x.id)

User.resolve_conflicts(custom_conflict_resolution)
"""
