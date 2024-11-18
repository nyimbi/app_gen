"""
version_control_mixin.py

This module provides a VersionControlMixin class for implementing version control
functionality in SQLAlchemy models for Flask-AppBuilder applications.

The VersionControlMixin allows for tracking changes to model instances over time,
storing different versions, and providing methods to retrieve, compare, and revert
to previous versions.

Dependencies:
    - SQLAlchemy
    - Flask-AppBuilder
    - jsonpatch (for efficient diff storage)
    - deepdiff (for complex object comparison)

Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.0
"""

from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.inspection import inspect
from flask import current_app
from datetime import datetime
import jsonpatch
import json
from deepdiff import DeepDiff

class VersionControlMixin:
    """
    A mixin class for adding version control capabilities to SQLAlchemy models.

    This mixin provides methods for tracking changes, storing versions, and
    managing the version history of model instances.

    Class Attributes:
        __versioned__ (list): List of attribute names to be versioned.
        __max_versions__ (int): Maximum number of versions to keep (0 for unlimited).
    """

    __versioned__ = []
    __max_versions__ = 0

    @declared_attr
    def versions(cls):
        return relationship('ModelVersion', back_populates='parent',
                            cascade='all, delete-orphan', order_by='ModelVersion.version_number.desc()')

    @classmethod
    def __declare_last__(cls):
        if not cls.__versioned__:
            cls.__versioned__ = [c.key for c in inspect(cls).column_attrs]

    def save_version(self, user_id=None, comment=None):
        """
        Save a new version of the model instance.

        Args:
            user_id (int, optional): ID of the user creating the version.
            comment (str, optional): Comment describing the changes in this version.

        Returns:
            ModelVersion: The newly created version instance.
        """
        if not self.versions:
            # First version
            data = {attr: getattr(self, attr) for attr in self.__versioned__}
            version = ModelVersion(parent=self, data=data, version_number=1,
                                   user_id=user_id, comment=comment)
        else:
            last_version = self.versions[0]
            new_data = {attr: getattr(self, attr) for attr in self.__versioned__}
            diff = jsonpatch.make_patch(last_version.data, new_data)
            version = ModelVersion(parent=self, data=diff.patch, version_number=last_version.version_number + 1,
                                   user_id=user_id, comment=comment)

        current_app.db.session.add(version)

        if self.__max_versions__ > 0 and len(self.versions) > self.__max_versions__:
            oldest_version = self.versions[-1]
            current_app.db.session.delete(oldest_version)

        return version

    def revert_to_version(self, version_number):
        """
        Revert the model instance to a specific version.

        Args:
            version_number (int): The version number to revert to.

        Raises:
            ValueError: If the specified version number doesn't exist.
        """
        version = next((v for v in self.versions if v.version_number == version_number), None)
        if not version:
            raise ValueError(f"Version {version_number} does not exist.")

        data = self.get_version_data(version_number)
        for attr, value in data.items():
            setattr(self, attr, value)

    def get_version_data(self, version_number):
        """
        Get the full data for a specific version.

        Args:
            version_number (int): The version number to retrieve.

        Returns:
            dict: The full data for the specified version.

        Raises:
            ValueError: If the specified version number doesn't exist.
        """
        versions = sorted(self.versions, key=lambda v: v.version_number)
        target_version = next((v for v in versions if v.version_number == version_number), None)
        if not target_version:
            raise ValueError(f"Version {version_number} does not exist.")

        data = versions[0].data  # Start with the most recent version
        for version in versions[1:]:
            if version.version_number <= version_number:
                data = jsonpatch.apply_patch(data, version.data)

        return data

    def compare_versions(self, version1, version2):
        """
        Compare two versions of the model instance.

        Args:
            version1 (int): First version number to compare.
            version2 (int): Second version number to compare.

        Returns:
            DeepDiff: A DeepDiff object showing the differences between the two versions.

        Raises:
            ValueError: If either of the specified version numbers doesn't exist.
        """
        data1 = self.get_version_data(version1)
        data2 = self.get_version_data(version2)
        return DeepDiff(data1, data2, ignore_order=True)

    def get_version_history(self):
        """
        Get the version history of the model instance.

        Returns:
            list: A list of dictionaries containing version information.
        """
        return [
            {
                'version_number': v.version_number,
                'created_at': v.created_at,
                'user_id': v.user_id,
                'comment': v.comment
            }
            for v in self.versions
        ]

    def create_branch(self, branch_name, base_version=None):
        """
        Create a new branch from the current state or a specific version.

        Args:
            branch_name (str): Name of the new branch.
            base_version (int, optional): Version number to base the branch on.
                                          If not provided, the current state is used.

        Returns:
            ModelBranch: The newly created branch instance.
        """
        data = self.get_version_data(base_version) if base_version else {attr: getattr(self, attr) for attr in self.__versioned__}
        branch = ModelBranch(parent=self, name=branch_name, data=data)
        current_app.db.session.add(branch)
        return branch

    def merge_branch(self, branch_name, resolve_conflicts=None):
        """
        Merge a branch into the main version.

        Args:
            branch_name (str): Name of the branch to merge.
            resolve_conflicts (callable, optional): Function to resolve conflicts.
                                                    Should take (main_data, branch_data) and return resolved data.

        Raises:
            ValueError: If the branch doesn't exist or if there are unresolved conflicts.
        """
        branch = next((b for b in self.branches if b.name == branch_name), None)
        if not branch:
            raise ValueError(f"Branch '{branch_name}' does not exist.")

        main_data = {attr: getattr(self, attr) for attr in self.__versioned__}
        branch_data = branch.data

        diff = DeepDiff(main_data, branch_data, ignore_order=True)
        if diff:
            if resolve_conflicts:
                resolved_data = resolve_conflicts(main_data, branch_data)
                for attr, value in resolved_data.items():
                    setattr(self, attr, value)
            else:
                raise ValueError("Conflicts detected. Provide a conflict resolution function.")

        self.save_version(comment=f"Merged branch '{branch_name}'")
        current_app.db.session.delete(branch)

class ModelVersion(Model):
    """
    Model to represent versions of versioned models.
    """
    __tablename__ = 'nx_model_versions'

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('parent_table.id'))  # Replace 'parent_table' with actual table name
    parent = relationship('ParentModel', back_populates='versions')  # Replace 'ParentModel' with actual model name
    version_number = Column(Integer, nullable=False)
    data = Column(MutableDict.as_mutable(JSON), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('ab_user.id'))
    comment = Column(Text)

    def __repr__(self):
        return f"<ModelVersion {self.version_number}>"

class ModelBranch(Model):
    """
    Model to represent branches of versioned models.
    """
    __tablename__ = 'nx_model_branches'

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('parent_table.id'))  # Replace 'parent_table' with actual table name
    parent = relationship('ParentModel', back_populates='branches')  # Replace 'ParentModel' with actual model name
    name = Column(String(100), nullable=False)
    data = Column(MutableDict.as_mutable(JSON), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ModelBranch {self.name}>"

# Example usage (commented out):
"""
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String
from mixins.version_control_mixin import VersionControlMixin

class Document(VersionControlMixin, Model):
    __tablename__ = 'nx_documents'
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    content = Column(Text)

    __versioned__ = ['title', 'content']
    __max_versions__ = 10  # Keep only the last 10 versions

# In your application code:

# Creating and updating a document with versions
doc = Document(title="Initial Title", content="Initial content")
db.session.add(doc)
db.session.commit()
doc.save_version(user_id=1, comment="Initial version")

doc.title = "Updated Title"
doc.content = "Updated content"
db.session.commit()
doc.save_version(user_id=1, comment="Updated title and content")

# Retrieving version history
history = doc.get_version_history()
print(history)

# Comparing versions
diff = doc.compare_versions(1, 2)
print(diff)

# Reverting to a previous version
doc.revert_to_version(1)
db.session.commit()

# Creating a branch
doc.create_branch("experimental")

# Making changes in the main version
doc.title = "Main version title"
db.session.commit()

# Merging the branch
def resolve_conflicts(main_data, branch_data):
    # Simple resolution strategy: prefer branch data
    return branch_data

doc.merge_branch("experimental", resolve_conflicts=resolve_conflicts)
db.session.commit()
"""
