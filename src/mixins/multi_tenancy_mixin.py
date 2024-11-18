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

Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.0
"""

from flask_appbuilder import Model
from sqlalchemy import Column, Integer, ForeignKey, event
from sqlalchemy.orm import declared_attr, relationship, Query
from sqlalchemy.ext.declarative import declared_attr
from flask import g, current_app
from flask_appbuilder.models.sqla.interface import SQLAInterface

class Tenant(Model):
    """
    Model to represent tenants in the system.
    """
    __tablename__ = 'nx_tenants'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    # Add any other tenant-specific fields here

    def __repr__(self):
        return self.name

class MultiTenancyMixin:
    """
    A mixin class for adding multi-tenancy support to SQLAlchemy models.

    This mixin automatically scopes queries to the current tenant and provides
    utilities for working with multi-tenant data.

    Class Attributes:
        __tenant_field__ (str): The name of the tenant field (default: 'tenant_id').
        __shared_data__ (bool): Whether this model can have data shared across tenants (default: False).
    """

    __tenant_field__ = 'tenant_id'
    __shared_data__ = False

    @declared_attr
    def tenant_id(cls):
        return Column(Integer, ForeignKey('nx_tenants.id'), nullable=False)

    @declared_attr
    def tenant(cls):
        return relationship('Tenant')

    @classmethod
    def __declare_last__(cls):
        event.listen(cls, 'before_insert', cls._before_insert)
        event.listen(cls, 'before_update', cls._before_update)

    @staticmethod
    def _before_insert(mapper, connection, target):
        """Automatically set the tenant_id before insert if not already set."""
        if target.tenant_id is None:
            target.tenant_id = MultiTenancyMixin.get_current_tenant_id()

    @staticmethod
    def _before_update(mapper, connection, target):
        """Ensure the tenant_id is not changed on update."""
        state = db.inspect(target)
        if state.attrs.tenant_id.history.has_changes():
            raise ValueError("Tenant ID cannot be changed")

    @staticmethod
    def get_current_tenant_id():
        """Get the current tenant ID from the application context."""
        tenant_id = getattr(g, 'tenant_id', None)
        if tenant_id is None:
            raise ValueError("No tenant set for current context")
        return tenant_id

    @classmethod
    def set_current_tenant(cls, tenant_id):
        """Set the current tenant in the application context."""
        g.tenant_id = tenant_id

    @classmethod
    def get_tenant_query(cls, query=None):
        """
        Scope a query to the current tenant.

        Args:
            query (Query, optional): Existing query to build upon. If None, a new query is created.

        Returns:
            Query: Query scoped to the current tenant.
        """
        if query is None:
            query = cls.query

        if cls.__shared_data__:
            return query.filter((getattr(cls, cls.__tenant_field__) == cls.get_current_tenant_id()) |
                                (getattr(cls, cls.__tenant_field__) == None))
        else:
            return query.filter(getattr(cls, cls.__tenant_field__) == cls.get_current_tenant_id())

    @classmethod
    def create_scoped_session(cls, tenant_id):
        """
        Create a database session scoped to a specific tenant.

        Args:
            tenant_id (int): The ID of the tenant to scope the session to.

        Returns:
            scoped_session: A database session scoped to the specified tenant.
        """
        from flask_sqlalchemy import SQLAlchemy
        db = SQLAlchemy(current_app)
        tenant_session = db.create_scoped_session()
        
        @event.listens_for(tenant_session, 'before_flush')
        def before_flush(session, flush_context, instances):
            for instance in session.new.union(session.dirty):
                if isinstance(instance, MultiTenancyMixin):
                    instance.tenant_id = tenant_id
        
        return tenant_session

    @classmethod
    def copy_to_tenant(cls, instance_id, from_tenant_id, to_tenant_id):
        """
        Copy a record from one tenant to another.

        Args:
            instance_id (int): The ID of the instance to copy.
            from_tenant_id (int): The source tenant ID.
            to_tenant_id (int): The destination tenant ID.

        Returns:
            Model: The newly created instance in the destination tenant.
        """
        source_session = cls.create_scoped_session(from_tenant_id)
        dest_session = cls.create_scoped_session(to_tenant_id)

        try:
            source_instance = source_session.query(cls).get(instance_id)
            if not source_instance:
                raise ValueError(f"No {cls.__name__} found with id {instance_id} for tenant {from_tenant_id}")

            dest_instance = cls()
            for col in cls.__table__.columns:
                if col.name != 'id' and col.name != cls.__tenant_field__:
                    setattr(dest_instance, col.name, getattr(source_instance, col.name))
            
            dest_session.add(dest_instance)
            dest_session.commit()

            return dest_instance
        finally:
            source_session.close()
            dest_session.close()

    @classmethod
    def get_shared_data(cls):
        """
        Get data that is shared across all tenants.

        Returns:
            Query: Query for shared data (tenant_id is NULL).
        """
        if not cls.__shared_data__:
            raise ValueError(f"{cls.__name__} does not support shared data")
        return cls.query.filter(getattr(cls, cls.__tenant_field__) == None)

# Extend SQLAInterface to automatically apply tenant scoping
class TenantScopedSQLAInterface(SQLAInterface):
    def query(self, filters=None, order_column='', order_direction=''):
        query = super().query(filters, order_column, order_direction)
        if issubclass(self.obj, MultiTenancyMixin):
            query = self.obj.get_tenant_query(query)
        return query

# Example usage (commented out):
"""
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, ForeignKey
from mixins.multi_tenancy_mixin import MultiTenancyMixin, TenantScopedSQLAInterface

class Product(MultiTenancyMixin, Model):
    __tablename__ = 'nx_products'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    price = Column(Integer, nullable=False)

    __shared_data__ = True  # Allow some products to be shared across tenants

# In your Flask-AppBuilder view
class ProductModelView(ModelView):
    datamodel = TenantScopedSQLAInterface(Product)

# In your application code:

# Set the current tenant
@app.before_request
def set_tenant():
    tenant_id = get_tenant_id_from_request()  # Implement this based on your authentication logic
    MultiTenancyMixin.set_current_tenant(tenant_id)

# Create a new product
new_product = Product(name="Widget", price=1000)
db.session.add(new_product)
db.session.commit()  # This will automatically set the tenant_id

# Query products (automatically scoped to the current tenant)
products = Product.get_tenant_query().all()

# Get shared products
shared_products = Product.get_shared_data().all()

# Copy a product to another tenant
copied_product = Product.copy_to_tenant(product_id=1, from_tenant_id=1, to_tenant_id=2)

# Using scoped session for operations on behalf of a specific tenant
with Product.create_scoped_session(tenant_id=3) as session:
    new_product = Product(name="Tenant 3 Specific Product", price=2000)
    session.add(new_product)
    session.commit()
"""
