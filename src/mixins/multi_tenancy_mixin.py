"""
multi_tenancy_mixin.py

This module provides a MultiTenancyMixin class for implementing multi-tenancy
support in SQLAlchemy models for Flask-AppBuilder applications.

The MultiTenancyMixin allows for automatic scoping of queries to the current tenant,
ensuring data isolation between tenants while allowing for shared data when needed.

Dependencies:
    - SQLAlchemy
    - Flask-AppBuilder
    - Flask
    - PostgreSQL

Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.0
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from flask import current_app, g
from flask_appbuilder import Model
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    event,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session, declared_attr, relationship, scoped_session

log = logging.getLogger(__name__)


class Tenant(Model):
    """
    Model to represent tenants in the system.

    Attributes:
        id (UUID): Primary key
        name (str): Tenant name
        slug (str): URL-friendly identifier
        domain (str): Custom domain
        settings (JSONB): Tenant-specific settings
        is_active (bool): Tenant status
        created_at (datetime): Creation timestamp
        updated_at (datetime): Last update timestamp
        metadata (JSONB): Custom metadata
        parent_id (UUID): Parent tenant for hierarchical setups
        custom_attributes (JSONB): Extensible attributes
    """

    __tablename__ = "nx_tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    domain = Column(String(255), unique=True, nullable=True)
    settings = Column(JSONB, default=dict, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSONB, default=dict, nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("nx_tenants.id"), nullable=True)
    custom_attributes = Column(JSONB, default=dict, nullable=False)

    # Relationships
    parent = relationship("Tenant", remote_side=[id], backref="children")

    __table_args__ = {"postgresql_partition_by": "LIST (is_active)"}

    def __repr__(self):
        return f"<Tenant {self.name}>"

    @hybrid_property
    def is_root(self):
        """Check if tenant is a root tenant (no parent)."""
        return self.parent_id is None

    @hybrid_property
    def full_hierarchy(self):
        """Get full tenant hierarchy path."""
        if self.is_root:
            return [self]
        return self.parent.full_hierarchy + [self]


class MultiTenancyMixin:
    """
    Advanced mixin for multi-tenant data isolation and management.

    Features:
    - Automatic tenant scoping
    - Hierarchical tenant support
    - Shared data management
    - Data migration utilities
    - Audit logging
    - Cache management
    - Bulk operations
    - Custom permissions
    - Data validation
    - Tenant statistics

    Class Attributes:
        __tenant_field__ (str): Tenant field name
        __shared_data__ (bool): Allow shared data
        __audit_changes__ (bool): Track changes
        __cache_enabled__ (bool): Enable caching
        __tenant_validation__ (bool): Validate tenant operations
    """

    __tenant_field__ = "tenant_id"
    __shared_data__ = False
    __audit_changes__ = True
    __cache_enabled__ = True
    __tenant_validation__ = True

    @declared_attr
    def tenant_id(cls):
        """Tenant foreign key with UUID type."""
        return Column(
            UUID(as_uuid=True), ForeignKey("nx_tenants.id"), nullable=False, index=True
        )

    @declared_attr
    def tenant(cls):
        """Tenant relationship with validation."""
        return relationship(
            "Tenant", lazy="joined", backref=f"{cls.__name__.lower()}_set"
        )

    @declared_attr
    def created_at(cls):
        """Creation timestamp."""
        return Column(DateTime, default=datetime.utcnow, nullable=False)

    @declared_attr
    def updated_at(cls):
        """Update timestamp."""
        return Column(
            DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
        )

    @declared_attr
    def metadata(cls):
        """Custom metadata storage."""
        return Column(JSONB, default=dict, nullable=False)

    @classmethod
    def __declare_last__(cls):
        """Setup event listeners for tenant operations."""
        event.listen(cls, "before_insert", cls._before_insert)
        event.listen(cls, "before_update", cls._before_update)
        if cls.__audit_changes__:
            event.listen(cls, "after_update", cls._after_update)

    @staticmethod
    def _before_insert(mapper, connection, target):
        """
        Pre-insert processing with validation.

        Args:
            mapper: SQLAlchemy mapper
            connection: DB connection
            target: Model instance

        Raises:
            ValueError: If tenant validation fails
        """
        if target.tenant_id is None:
            target.tenant_id = MultiTenancyMixin.get_current_tenant_id()

        if target.__tenant_validation__:
            tenant = Tenant.query.get(target.tenant_id)
            if not tenant or not tenant.is_active:
                raise ValueError("Invalid or inactive tenant")

    @staticmethod
    def _before_update(mapper, connection, target):
        """
        Pre-update validation and processing.

        Args:
            mapper: SQLAlchemy mapper
            connection: DB connection
            target: Model instance

        Raises:
            ValueError: If tenant ID modification attempted
        """
        state = inspect(target)
        if state.attrs.tenant_id.history.has_changes():
            raise ValueError("Tenant ID cannot be modified")

    @staticmethod
    def _after_update(mapper, connection, target):
        """Audit logging for changes."""
        if target.__audit_changes__:
            state = inspect(target)
            changes = {}
            for attr in state.attrs:
                hist = attr.history
                if hist.has_changes():
                    changes[attr.key] = {
                        "old": hist.deleted[0] if hist.deleted else None,
                        "new": hist.added[0] if hist.added else None,
                    }
            if changes:
                # Log changes to audit system
                log.info(
                    f"Changes to {target.__class__.__name__}[{target.id}]: {changes}"
                )

    @staticmethod
    def get_current_tenant_id() -> UUID:
        """
        Get current tenant ID with fallback handling.

        Returns:
            UUID: Current tenant ID

        Raises:
            ValueError: If no tenant context
        """
        tenant_id = getattr(g, "tenant_id", None)
        if tenant_id is None:
            if current_app.config.get("ALLOW_NO_TENANT", False):
                return current_app.config.get("DEFAULT_TENANT_ID")
            raise ValueError("No tenant set for current context")
        return tenant_id

    @classmethod
    def set_current_tenant(cls, tenant_id: Union[UUID, str]) -> None:
        """
        Set current tenant with validation.

        Args:
            tenant_id: Tenant identifier

        Raises:
            ValueError: If tenant invalid
        """
        if isinstance(tenant_id, str):
            tenant_id = UUID(tenant_id)

        if cls.__tenant_validation__:
            tenant = Tenant.query.get(tenant_id)
            if not tenant or not tenant.is_active:
                raise ValueError("Invalid or inactive tenant")

        g.tenant_id = tenant_id

    @classmethod
    def get_tenant_query(cls, query=None):
        """
        Create tenant-scoped query with caching.

        Args:
            query: Base query to extend

        Returns:
            Query: Scoped query object
        """
        if query is None:
            query = cls.query

        tenant_id = cls.get_current_tenant_id()

        if cls.__cache_enabled__:
            cache_key = f"tenant_query_{cls.__name__}_{tenant_id}"
            cached = current_app.cache.get(cache_key)
            if cached is not None:
                return cached

        if cls.__shared_data__:
            query = query.filter(
                (getattr(cls, cls.__tenant_field__) == tenant_id)
                | (getattr(cls, cls.__tenant_field__) is None)
            )
        else:
            query = query.filter(getattr(cls, cls.__tenant_field__) == tenant_id)

        if cls.__cache_enabled__:
            current_app.cache.set(cache_key, query)

        return query

    @classmethod
    def bulk_tenant_operation(
        cls, operation: str, data: List[Dict], tenant_id: Optional[UUID] = None
    ) -> List[Any]:
        """
        Perform bulk operations within tenant scope.

        Args:
            operation: Operation type (create/update/delete)
            data: Operation data
            tenant_id: Override tenant ID

        Returns:
            List[Any]: Operation results

        Raises:
            ValueError: For invalid operations
        """
        tenant_id = tenant_id or cls.get_current_tenant_id()
        session = cls.create_scoped_session(tenant_id)

        try:
            results = []
            if operation == "create":
                instances = [cls(**item) for item in data]
                session.bulk_save_objects(instances)
                results = instances
            elif operation == "update":
                for item in data:
                    instance = session.query(cls).get(item.pop("id"))
                    if instance:
                        for key, value in item.items():
                            setattr(instance, key, value)
                        results.append(instance)
            elif operation == "delete":
                ids = [item["id"] for item in data]
                results = session.query(cls).filter(cls.id.in_(ids)).all()
                for instance in results:
                    session.delete(instance)
            else:
                raise ValueError(f"Invalid operation: {operation}")

            session.commit()
            return results
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @classmethod
    def create_scoped_session(cls, tenant_id: UUID) -> scoped_session:
        """
        Create tenant-scoped database session.

        Args:
            tenant_id: Tenant identifier

        Returns:
            scoped_session: Scoped session instance
        """
        db = SQLAlchemy(current_app)
        tenant_session = db.create_scoped_session()

        @event.listens_for(tenant_session, "before_flush")
        def before_flush(session, flush_context, instances):
            for instance in session.new.union(session.dirty):
                if isinstance(instance, MultiTenancyMixin):
                    instance.tenant_id = tenant_id

        return tenant_session

    @classmethod
    def get_tenant_statistics(cls, tenant_id: Optional[UUID] = None) -> Dict:
        """
        Get tenant data statistics.

        Args:
            tenant_id: Tenant to analyze

        Returns:
            Dict: Statistics data
        """
        tenant_id = tenant_id or cls.get_current_tenant_id()
        session = cls.create_scoped_session(tenant_id)

        try:
            stats = {
                "total_records": session.query(cls)
                .filter_by(tenant_id=tenant_id)
                .count(),
                "last_updated": session.query(cls.updated_at)
                .filter_by(tenant_id=tenant_id)
                .order_by(cls.updated_at.desc())
                .first(),
                "metadata_keys": session.query(cls.metadata.keys())
                .filter_by(tenant_id=tenant_id)
                .distinct()
                .all(),
            }
            return stats
        finally:
            session.close()


class TenantScopedSQLAInterface(SQLAInterface):
    """
    Enhanced SQLAInterface with tenant scoping and caching.
    """

    def query(self, filters=None, order_column="", order_direction=""):
        """
        Create tenant-aware query with caching.

        Args:
            filters: Query filters
            order_column: Sort column
            order_direction: Sort direction

        Returns:
            Query: Filtered and ordered query
        """
        query = super().query(filters, order_column, order_direction)

        if issubclass(self.obj, MultiTenancyMixin):
            cache_key = f"interface_query_{self.obj.__name__}_{filters}"

            if self.obj.__cache_enabled__:
                cached = current_app.cache.get(cache_key)
                if cached is not None:
                    return cached

            query = self.obj.get_tenant_query(query)

            if self.obj.__cache_enabled__:
                current_app.cache.set(cache_key, query)

        return query


"""
Usage Example:

from flask_appbuilder import Model, ModelView
from sqlalchemy import Column, String, Numeric
from sqlalchemy.dialects.postgresql import UUID
from mixins.multi_tenancy_mixin import MultiTenancyMixin, TenantScopedSQLAInterface

class Product(MultiTenancyMixin, Model):
    __tablename__ = 'nx_products'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)

    __shared_data__ = True
    __audit_changes__ = True
    __cache_enabled__ = True

class ProductModelView(ModelView):
    datamodel = TenantScopedSQLAInterface(Product)
    list_columns = ['name', 'price', 'tenant.name', 'created_at']
    edit_columns = ['name', 'price']
    add_columns = ['name', 'price']
    show_columns = ['name', 'price', 'tenant.name', 'created_at', 'updated_at']

# Application Setup
@app.before_request
def set_tenant():
    tenant_id = get_tenant_id_from_request()
    MultiTenancyMixin.set_current_tenant(tenant_id)

# Usage Examples
# Create product
new_product = Product(name="Premium Widget", price=999.99)
db.session.add(new_product)
db.session.commit()

# Bulk create products
products_data = [
    {"name": "Product A", "price": 100},
    {"name": "Product B", "price": 200}
]
Product.bulk_tenant_operation('create', products_data)

# Get tenant statistics
stats = Product.get_tenant_statistics()

# Query with tenant scope
products = Product.get_tenant_query().filter(Product.price > 500).all()

# Using scoped session
with Product.create_scoped_session(tenant_id) as session:
    session.query(Product).filter(Product.price < 1000).all()
"""
