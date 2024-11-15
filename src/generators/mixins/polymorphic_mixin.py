"""
polymorphic_mixin.py

This module provides a PolymorphicMixin class for implementing polymorphic
relationships in SQLAlchemy models for Flask-AppBuilder applications.

The PolymorphicMixin allows for flexible model inheritance and associations,
supporting both single table and joined table inheritance strategies.

Dependencies:
    - SQLAlchemy
    - Flask-AppBuilder

Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.0
"""

from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship, polymorphic_union
from sqlalchemy.ext.hybrid import hybrid_property
from flask_appbuilder.models.mixins import AuditMixin

class PolymorphicMixin:
    """
    A mixin class for implementing polymorphic relationships in SQLAlchemy models.

    This mixin provides functionality for both single table and joined table
    inheritance strategies, as well as polymorphic associations.

    Class Attributes:
        __polymorphic_on__ (str): The name of the discriminator column.
        __polymorphic_identity__ (str): The identity value for this specific model.
    """

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    @declared_attr
    def id(cls):
        return Column(Integer, primary_key=True)

    @declared_attr
    def type(cls):
        return Column(String(50))

    @declared_attr
    def __mapper_args__(cls):
        if hasattr(cls, '__polymorphic_on__') and hasattr(cls, '__polymorphic_identity__'):
            return {
                'polymorphic_on': cls.__polymorphic_on__,
                'polymorphic_identity': cls.__polymorphic_identity__
            }
        return {}

    @classmethod
    def polymorphic_query(cls):
        """
        Create a query that includes all polymorphic subclasses.

        Returns:
            Query: SQLAlchemy query object for polymorphic queries.
        """
        return cls.query.with_polymorphic('*')

    @classmethod
    def create_polymorphic(cls, data):
        """
        Create a new instance of the appropriate polymorphic subclass based on the data.

        Args:
            data (dict): Dictionary of attribute values including the discriminator.

        Returns:
            PolymorphicMixin: An instance of the appropriate subclass.

        Raises:
            ValueError: If the polymorphic identity is not recognized.
        """
        if cls.__polymorphic_on__ not in data:
            raise ValueError(f"Discriminator '{cls.__polymorphic_on__}' not provided in data")

        identity = data[cls.__polymorphic_on__]
        for subclass in cls.__subclasses__():
            if subclass.__polymorphic_identity__ == identity:
                return subclass(**data)

        raise ValueError(f"Unknown polymorphic identity: {identity}")

    @hybrid_property
    def polymorphic_type(self):
        """
        Get the polymorphic type of the instance.

        Returns:
            str: The polymorphic identity of the instance.
        """
        return getattr(self, self.__polymorphic_on__)

    @polymorphic_type.setter
    def polymorphic_type(self, value):
        """
        Set the polymorphic type of the instance.

        Args:
            value (str): The polymorphic identity to set.

        Raises:
            ValueError: If the polymorphic identity is not valid.
        """
        if value not in [subcls.__polymorphic_identity__ for subcls in self.__class__.__subclasses__()]:
            raise ValueError(f"Invalid polymorphic identity: {value}")
        setattr(self, self.__polymorphic_on__, value)

class PolymorphicAssociationMixin:
    """
    A mixin class for implementing polymorphic associations.

    This mixin allows a model to be associated with multiple other models
    through a polymorphic relationship.
    """

    @declared_attr
    def associated_id(cls):
        return Column(Integer, nullable=False)

    @declared_attr
    def associated_type(cls):
        return Column(String(50), nullable=False)

    @classmethod
    def associate_with(cls, associated_class):
        """
        Create an association with another model class.

        Args:
            associated_class: The SQLAlchemy model class to associate with.

        Returns:
            relationship: SQLAlchemy relationship object.
        """
        return relationship(
            associated_class,
            primaryjoin=f"and_({cls.__name__}.associated_id == {associated_class.__name__}.id, "
                        f"{cls.__name__}.associated_type == '{associated_class.__name__}')",
            foreign_keys=[cls.associated_id],
            backref=f"{cls.__name__.lower()}_associations"
        )

# Example usage (commented out):
"""
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, Float
from mixins.polymorphic_mixin import PolymorphicMixin, PolymorphicAssociationMixin

# Single Table Inheritance Example
class Vehicle(PolymorphicMixin, Model):
    __tablename__ = 'nx_vehicles'
    __polymorphic_on__ = 'type'
    __polymorphic_identity__ = 'vehicle'

    make = Column(String(50))
    model = Column(String(50))

class Car(Vehicle):
    __polymorphic_identity__ = 'car'
    doors = Column(Integer)

class Motorcycle(Vehicle):
    __polymorphic_identity__ = 'motorcycle'
    has_sidecar = Column(Boolean)

# Joined Table Inheritance Example
class Employee(PolymorphicMixin, Model):
    __tablename__ = 'nx_employees'
    __polymorphic_on__ = 'type'
    __polymorphic_identity__ = 'employee'

    name = Column(String(100))
    salary = Column(Float)

class Manager(Employee):
    __tablename__ = 'nx_managers'
    __polymorphic_identity__ = 'manager'

    id = Column(Integer, ForeignKey('nx_employees.id'), primary_key=True)
    department = Column(String(50))

class Engineer(Employee):
    __tablename__ = 'nx_engineers'
    __polymorphic_identity__ = 'engineer'

    id = Column(Integer, ForeignKey('nx_employees.id'), primary_key=True)
    programming_language = Column(String(50))

# Polymorphic Association Example
class Tag(PolymorphicAssociationMixin, Model):
    __tablename__ = 'nx_tags'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))

    vehicle_association = associate_with(Vehicle)
    employee_association = associate_with(Employee)

# In your application code:

# Creating instances
car = Car(make="Toyota", model="Corolla", doors=4)
motorcycle = Motorcycle(make="Harley-Davidson", model="Sportster", has_sidecar=False)

manager = Manager(name="John Doe", salary=100000, department="Sales")
engineer = Engineer(name="Jane Smith", salary=90000, programming_language="Python")

db.session.add_all([car, motorcycle, manager, engineer])
db.session.commit()

# Querying
all_vehicles = Vehicle.polymorphic_query().all()
all_employees = Employee.polymorphic_query().all()

# Creating polymorphic instance based on data
vehicle_data = {"type": "car", "make": "Ford", "model": "Mustang", "doors": 2}
new_vehicle = Vehicle.create_polymorphic(vehicle_data)

# Using polymorphic associations
car_tag = Tag(name="Sedan", associated_id=car.id, associated_type="Car")
employee_tag = Tag(name="Management", associated_id=manager.id, associated_type="Manager")

db.session.add_all([car_tag, employee_tag])
db.session.commit()

# Querying associations
car_tags = car.tag_associations
manager_tags = manager.tag_associations
"""
