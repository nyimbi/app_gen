"""
versioning_mixin.py

This module provides a VersioningMixin class for implementing version control
for SQLAlchemy models in Flask-AppBuilder applications.

The VersioningMixin allows tracking changes to model instances over time,
retrieving previous versions, and reverting to earlier states. It's useful
for maintaining a historical record of data changes and enabling undo operations.

Dependencies:
    - SQLAlchemy
    - Flask-AppBuilder
    - jsonpickle (for serialization)

Author: [Your Name]
Date: [Current Date]
Version: 1.0
"""

from flask_appbuilder import Model
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.event import listens_for
from flask_appbuilder.models.mixins import AuditMixin
import jsonpickle
from datetime import datetime

class VersioningMixin(AuditMixin):
    """
    A mixin class for adding versioning capabilities to SQLAlchemy models.

    This mixin creates a separate table to store version history for the model.
    It provides methods to save versions, retrieve version history, and revert
    to previous versions.

    Attributes:
        versions (relationship): Relationship to the version history table.
    """

    @declared_attr
    def versions(cls):
        class ModelVersion(Model):
            __tablename__ = f'nx_{cls.__tablename__}_versions'
            
            id = Column(Integer, primary_key=True)
            model_id = Column(Integer, ForeignKey(f'{cls.__tablename__}.id'), nullable=False)
            data = Column(Text, nullable=False)
            version_number = Column(Integer, nullable=False)
            created_on = Column(DateTime, default=datetime.utcnow, nullable=False)
            created_by_fk = Column(Integer, ForeignKey('ab_user.id'), nullable=False)
            
            __table_args__ = (
                cls.metadata,
            )

        return relationship(ModelVersion, backref='parent', cascade='all, delete-orphan')

    @hybrid_property
    def current_version(self):
        """Returns the current version number of the instance."""
        return max([v.version_number for v in self.versions]) if self.versions else 0

    def save_version(self, user_id):
        """
        Saves a new version of the instance.

        Args:
            user_id (int): ID of the user creating the version.

        Returns:
            ModelVersion: The newly created version instance.
        """
        version_data = jsonpickle.encode(self.to_dict())
        new_version = self.versions.append(
            self.versions.property.mapper.class_(
                model_id=self.id,
                data=version_data,
                version_number=self.current_version + 1,
                created_by_fk=user_id
            )
        )
        return new_version

    def get_version(self, version_number):
        """
        Retrieves a specific version of the instance.

        Args:
            version_number (int): The version number to retrieve.

        Returns:
            dict: A dictionary representation of the instance at the specified version.

        Raises:
            ValueError: If the specified version number doesn't exist.
        """
        version = next((v for v in self.versions if v.version_number == version_number), None)
        if not version:
            raise ValueError(f"Version {version_number} does not exist.")
        return jsonpickle.decode(version.data)

    def revert_to_version(self, version_number, user_id):
        """
        Reverts the instance to a previous version.

        Args:
            version_number (int): The version number to revert to.
            user_id (int): ID of the user performing the revert operation.

        Raises:
            ValueError: If the specified version number doesn't exist.
        """
        version_data = self.get_version(version_number)
        for key, value in version_data.items():
            setattr(self, key, value)
        self.save_version(user_id)

    def get_version_history(self):
        """
        Retrieves the complete version history of the instance.

        Returns:
            list: A list of dictionaries containing version information,
                  sorted by version number in descending order.
        """
        return [
            {
                'version_number': v.version_number,
                'created_on': v.created_on,
                'created_by': v.created_by.username
            }
            for v in sorted(self.versions, key=lambda x: x.version_number, reverse=True)
        ]

    def compare_versions(self, version1, version2):
        """
        Compares two versions of the instance.

        Args:
            version1 (int): First version number to compare.
            version2 (int): Second version number to compare.

        Returns:
            dict: A dictionary showing the differences between the two versions.

        Raises:
            ValueError: If either of the specified version numbers doesn't exist.
        """
        data1 = self.get_version(version1)
        data2 = self.get_version(version2)
        
        differences = {}
        for key in set(data1.keys()) | set(data2.keys()):
            if data1.get(key) != data2.get(key):
                differences[key] = {
                    'version1': data1.get(key),
                    'version2': data2.get(key)
                }
        
        return differences

@listens_for(VersioningMixin, 'after_update', propagate=True)
def versioning_after_update_listener(mapper, connection, target):
    """
    SQLAlchemy event listener to automatically save a new version after updates.

    This listener is triggered after each update operation on a model that
    uses the VersioningMixin.

    Args:
        mapper: The mapper that is the target of this event.
        connection: The Connection being used to emit UPDATE statements.
        target: The instance being updated.
    """
    user_id = target.changed_by_fk if hasattr(target, 'changed_by_fk') else None
    target.save_version(user_id)

# Example usage (commented out):
"""
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String
from mixins.versioning_mixin import VersioningMixin

class MyModel(VersioningMixin, Model):
    __tablename__ = 'my_model'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    value = Column(Integer)

# In your application code:
my_instance = MyModel(name="Example", value=10)
db.session.add(my_instance)
db.session.commit()

# Update the instance
my_instance.value = 20
db.session.commit()  # This will automatically create a new version

# Revert to the first version
my_instance.revert_to_version(1, user_id=current_user.id)
db.session.commit()

# Get version history
history = my_instance.get_version_history()

# Compare versions
diff = my_instance.compare_versions(1, 2)
"""
