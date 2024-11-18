"""
tree_mixin.py

This module provides a TreeMixin class for implementing hierarchical structures
in SQLAlchemy models. It allows for efficient tree operations and traversals.

Usage:
    from tree_mixin import TreeMixin

    class MyModel(TreeMixin, Model):
        __tablename__ = 'my_model'
        id = Column(Integer, primary_key=True)
        name = Column(String(50))

Dependencies:
    - SQLAlchemy
    - Flask-AppBuilder (for compatibility with FAB models)
"""

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, remote, foreign
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.collections import attribute_mapped_collection
from flask_appbuilder.models.mixins import AuditMixin

class TreeMixin(AuditMixin):
    """
    A mixin class for implementing tree structures in SQLAlchemy models.

    This mixin provides methods for tree traversal, manipulation, and querying.
    It sets up a parent-child relationship and includes utility methods for
    working with hierarchical data.
    """

    @declared_attr
    def parent_id(cls):
        return Column(Integer, ForeignKey(f'{cls.__tablename__}.id'), nullable=True)

    @declared_attr
    def parent(cls):
        return relationship(
            cls.__name__,
            remote_side=f'{cls.__name__}.id',
            backref=relationship(
                cls.__name__,
                collection_class=attribute_mapped_collection('id'),
                cascade='all, delete-orphan'
            ),
            uselist=False
        )

    @hybrid_property
    def children(self):
        return list(self.parent.values())

    @hybrid_property
    def depth(self):
        return len(self.ancestors)

    @property
    def ancestors(self):
        """Returns a list of ancestors, ordered from root to immediate parent."""
        node = self
        ancestors = []
        while node.parent:
            ancestors.insert(0, node.parent)
            node = node.parent
        return ancestors

    @property
    def root(self):
        """Returns the root node of the tree."""
        node = self
        while node.parent:
            node = node.parent
        return node

    def is_descendant_of(self, other):
        """Check if this node is a descendant of the other node."""
        return other in self.ancestors

    def is_ancestor_of(self, other):
        """Check if this node is an ancestor of the other node."""
        return self in other.ancestors

    def is_sibling_of(self, other):
        """Check if this node is a sibling of the other node."""
        return self.parent == other.parent and self != other

    @property
    def siblings(self):
        """Returns a list of siblings, excluding self."""
        if not self.parent:
            return []
        return [child for child in self.parent.children if child != self]

    def descendants(self, include_self=False):
        """
        Returns a generator of all descendants, optionally including self.

        Args:
            include_self (bool): Whether to include the current node in the result.

        Yields:
            TreeMixin: Descendant nodes in depth-first order.
        """
        if include_self:
            yield self
        for child in self.children:
            yield child
            yield from child.descendants()

    def ancestors_and_self(self):
        """Returns a list of ancestors and self, ordered from root to self."""
        return self.ancestors + [self]

    def move_to(self, new_parent):
        """
        Moves this node to a new parent.

        Args:
            new_parent (TreeMixin): The new parent node.

        Raises:
            ValueError: If the move would create a circular reference.
        """
        if new_parent is self or new_parent.is_descendant_of(self):
            raise ValueError("Cannot move node to its own descendant")
        self.parent = new_parent

    def get_tree_representation(self, include_self=True, max_depth=None):
        """
        Returns a nested dictionary representation of the tree.

        Args:
            include_self (bool): Whether to include the current node.
            max_depth (int, optional): Maximum depth to traverse.

        Returns:
            dict: A nested dictionary representing the tree structure.
        """
        def build_tree(node, current_depth=0):
            if max_depth is not None and current_depth > max_depth:
                return None
            return {
                'id': node.id,
                'children': [build_tree(child, current_depth + 1) 
                             for child in node.children 
                             if build_tree(child, current_depth + 1) is not None]
            }

        if include_self:
            return build_tree(self)
        return [build_tree(child) for child in self.children]

    @classmethod
    def get_roots(cls, session):
        """
        Returns all root nodes (nodes without parents).

        Args:
            session: SQLAlchemy session.

        Returns:
            list: A list of root nodes.
        """
        return session.query(cls).filter(cls.parent_id == None).all()

    @classmethod
    def get_nodes_at_depth(cls, session, depth):
        """
        Returns all nodes at a specific depth in the tree.

        Args:
            session: SQLAlchemy session.
            depth (int): The depth to query for.

        Returns:
            list: A list of nodes at the specified depth.
        """
        subq = session.query(cls).cte(name='tree', recursive=True)
        subq = subq.union_all(
            session.query(cls).filter(cls.parent_id == subq.c.id)
        )
        return session.query(cls).filter(subq.c.id == cls.id, subq.c.level == depth).all()

    def validate_tree(self):
        """
        Validates the tree structure, checking for circular references.

        Raises:
            ValueError: If a circular reference is detected.
        """
        visited = set()
        node = self
        while node:
            if node in visited:
                raise ValueError("Circular reference detected in tree structure")
            visited.add(node)
            node = node.parent

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id}, parent_id={self.parent_id})>"
