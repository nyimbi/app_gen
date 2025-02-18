"""
commentable_mixin.py

This module provides a comprehensive CommentableMixin class for implementing
advanced commenting functionality on model instances in SQLAlchemy models
for Flask-AppBuilder applications.

The CommentableMixin supports hierarchical comments, comment editing,
moderation, voting, and advanced querying capabilities.

Dependencies:
    - SQLAlchemy
    - Flask-AppBuilder
    - Flask-Login (for current user tracking)
    - PostgreSQL 9.4+

Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.1
"""

import logging
from datetime import datetime

from flask import current_app, g
from flask_appbuilder import Model
from flask_login import current_user
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    event,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import backref, relationship

logger = logging.getLogger(__name__)


class CommentableMixin:
    """
    A comprehensive mixin class for adding advanced commenting capabilities to SQLAlchemy models.

    This mixin provides methods for adding, retrieving, and managing comments
    associated with model instances, including support for hierarchical comments,
    moderation, and voting.

    Class Attributes:
        __commentable__ (bool): Flag to enable/disable commenting for the model.
        __comment_moderation__ (bool): Flag to enable/disable comment moderation.
        __max_comment_depth__ (int): Maximum depth for nested comments.
        __comment_metadata__ (dict): Additional metadata for comment configuration.
    """

    __commentable__ = True
    __comment_moderation__ = False
    __max_comment_depth__ = 3
    __comment_metadata__ = MutableDict.as_mutable(JSONB)

    @declared_attr
    def comments(cls):
        return relationship(
            "Comment",
            back_populates="parent",
            cascade="all, delete-orphan",
            primaryjoin=f"and_(Comment.parent_id==cast({cls.__name__}.id, String), "
            f"Comment.parent_type=='{cls.__name__}')",
            order_by="Comment.created_at.desc()",
            lazy="dynamic",
        )

    def add_comment(self, content, user=None, parent_comment_id=None, metadata=None):
        """
        Add a new comment to the model instance.

        Args:
            content (str): The content of the comment.
            user: The user adding the comment. If None, uses current_user.
            parent_comment_id (int, optional): ID of the parent comment if this is a reply.
            metadata (dict, optional): Additional metadata for the comment.

        Returns:
            Comment: The newly created comment instance.

        Raises:
            ValueError: If commenting is disabled or max depth is exceeded.
            PermissionError: If user lacks permission to comment.
        """
        if not self.__commentable__:
            raise ValueError("Commenting is not enabled for this model")

        if not content or not content.strip():
            raise ValueError("Comment content cannot be empty")

        if user is None:
            user = current_user
            if not user or not user.is_authenticated:
                raise PermissionError("Must be authenticated to comment")

        if len(content) > 10000:  # Reasonable max length
            raise ValueError("Comment exceeds maximum length")

        try:
            if parent_comment_id:
                parent_comment = Comment.query.get(parent_comment_id)
                if not parent_comment:
                    raise ValueError("Parent comment not found")
                if parent_comment.depth >= self.__max_comment_depth__:
                    raise ValueError(
                        f"Maximum comment depth of {self.__max_comment_depth__} exceeded"
                    )
                if parent_comment.parent_id != str(self.id):
                    raise ValueError("Parent comment belongs to different parent")
                depth = parent_comment.depth + 1
            else:
                depth = 0

            comment = Comment(
                content=content,
                user_id=user.id,
                parent_id=str(self.id),
                parent_type=self.__class__.__name__,
                parent_comment_id=parent_comment_id,
                is_approved=not self.__comment_moderation__,
                depth=depth,
                metadata=metadata or {},
            )

            # Trigger pre-save event
            event.listen(Comment, "before_insert", self._on_comment_create)

            current_app.db.session.add(comment)
            current_app.db.session.commit()

            # Log activity
            logger.info(
                f"Comment added: {comment.id} by user {user.id} on {self.__class__.__name__}:{self.id}"
            )

            return comment

        except Exception as e:
            current_app.db.session.rollback()
            logger.error(f"Error adding comment: {str(e)}")
            raise

    def get_comments(
        self,
        include_unapproved=False,
        limit=None,
        offset=None,
        include_replies=True,
        user=None,
        sort_by="created_at",
        sort_dir="desc",
    ):
        """
        Get comments for the model instance.

        Args:
            include_unapproved (bool): Whether to include unapproved comments.
            limit (int, optional): Maximum number of top-level comments to return.
            offset (int, optional): Number of top-level comments to skip.
            include_replies (bool): Whether to include nested replies.
            user (User, optional): Filter comments by specific user.
            sort_by (str): Field to sort by ('created_at', 'vote_count', etc.)
            sort_dir (str): Sort direction ('asc' or 'desc')

        Returns:
            list: A list of Comment objects.
        """
        try:
            query = self.comments

            # Base filters
            if not include_unapproved:
                query = query.filter(Comment.is_approved.is_(True))
            if not include_replies:
                query = query.filter(Comment.parent_comment_id.is_(None))
            if user:
                query = query.filter(Comment.user_id == user.id)

            # Sorting
            sort_col = getattr(Comment, sort_by, Comment.created_at)
            if sort_dir.lower() == "desc":
                query = query.order_by(sort_col.desc())
            else:
                query = query.order_by(sort_col.asc())

            # Pagination
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)

            return query.all()

        except Exception as e:
            logger.error(f"Error retrieving comments: {str(e)}")
            return []

    def delete_comment(self, comment_id, user=None, force=False):
        """
        Delete a comment from the model instance.

        Args:
            comment_id (int): The ID of the comment to delete.
            user: The user attempting to delete the comment. If None, uses current_user.
            force (bool): If True, bypasses permission checks (admin only).

        Returns:
            bool: True if the comment was successfully deleted, False otherwise.

        Raises:
            PermissionError: If user lacks permission to delete the comment.
        """
        try:
            comment = Comment.query.get(comment_id)
            if (
                not comment
                or comment.parent_id != str(self.id)
                or comment.parent_type != self.__class__.__name__
            ):
                return False

            if user is None:
                user = current_user

            if not user or not user.is_authenticated:
                raise PermissionError("Must be authenticated to delete comments")

            # Permission check
            can_delete = (
                force
                and user.has_role("Admin")
                or user.id == comment.user_id
                or user.has_role("Moderator")
            )

            if not can_delete:
                raise PermissionError("Insufficient permissions to delete comment")

            # Trigger pre-delete event
            event.listen(Comment, "before_delete", self._on_comment_delete)

            current_app.db.session.delete(comment)
            current_app.db.session.commit()

            logger.info(f"Comment {comment_id} deleted by user {user.id}")
            return True

        except Exception as e:
            current_app.db.session.rollback()
            logger.error(f"Error deleting comment: {str(e)}")
            raise

    def update_comment(self, comment_id, new_content, user=None, metadata=None):
        """
        Update the content of a comment.

        Args:
            comment_id (int): The ID of the comment to update.
            new_content (str): The new content for the comment.
            user: The user attempting to update the comment. If None, uses current_user.
            metadata (dict, optional): Updated metadata for the comment.

        Returns:
            bool: True if the comment was successfully updated, False otherwise.

        Raises:
            ValueError: If new content is invalid.
            PermissionError: If user lacks permission to update the comment.
        """
        if not new_content or not new_content.strip():
            raise ValueError("Comment content cannot be empty")

        if len(new_content) > 10000:
            raise ValueError("Comment exceeds maximum length")

        try:
            comment = Comment.query.get(comment_id)
            if (
                not comment
                or comment.parent_id != str(self.id)
                or comment.parent_type != self.__class__.__name__
            ):
                return False

            if user is None:
                user = current_user

            if not user or not user.is_authenticated:
                raise PermissionError("Must be authenticated to update comments")

            if not (user.id == comment.user_id or user.has_role("Admin")):
                raise PermissionError("Insufficient permissions to update comment")

            # Store original for event
            original_content = comment.content

            comment.content = new_content
            comment.updated_at = datetime.utcnow()
            if metadata:
                comment.metadata.update(metadata)

            # Trigger pre-update event
            event.listen(
                Comment,
                "before_update",
                lambda target, value, oldvalue, initiator: self._on_comment_update(
                    target, original_content
                ),
            )

            current_app.db.session.commit()

            logger.info(f"Comment {comment_id} updated by user {user.id}")
            return True

        except Exception as e:
            current_app.db.session.rollback()
            logger.error(f"Error updating comment: {str(e)}")
            raise

    def approve_comment(self, comment_id, user=None):
        """
        Approve a comment.

        Args:
            comment_id (int): The ID of the comment to approve.
            user: The user attempting to approve the comment. If None, uses current_user.

        Returns:
            bool: True if the comment was successfully approved, False otherwise.

        Raises:
            PermissionError: If user lacks permission to approve comments.
        """
        if not self.__comment_moderation__:
            return False

        try:
            comment = Comment.query.get(comment_id)
            if (
                not comment
                or comment.parent_id != str(self.id)
                or comment.parent_type != self.__class__.__name__
            ):
                return False

            if user is None:
                user = current_user

            if not user or not user.is_authenticated or not user.has_role("Moderator"):
                raise PermissionError("Must be a moderator to approve comments")

            if comment.is_approved:
                return True

            comment.is_approved = True
            comment.approved_by_id = user.id
            comment.approved_at = datetime.utcnow()

            # Trigger pre-approve event
            event.listen(Comment, "before_update", self._on_comment_approve)

            current_app.db.session.commit()

            logger.info(f"Comment {comment_id} approved by user {user.id}")
            return True

        except Exception as e:
            current_app.db.session.rollback()
            logger.error(f"Error approving comment: {str(e)}")
            raise

    def vote_comment(self, comment_id, vote_type, user=None):
        """
        Vote on a comment (upvote or downvote).

        Args:
            comment_id (int): The ID of the comment to vote on.
            vote_type (str): 'up' for upvote, 'down' for downvote.
            user: The user voting on the comment. If None, uses current_user.

        Returns:
            bool: True if the vote was successfully recorded, False otherwise.

        Raises:
            ValueError: If vote type is invalid.
            PermissionError: If user lacks permission to vote.
        """
        if vote_type not in ("up", "down"):
            raise ValueError("Invalid vote type. Must be 'up' or 'down'")

        try:
            comment = Comment.query.get(comment_id)
            if (
                not comment
                or comment.parent_id != str(self.id)
                or comment.parent_type != self.__class__.__name__
            ):
                return False

            if user is None:
                user = current_user

            if not user or not user.is_authenticated:
                raise PermissionError("Must be authenticated to vote")

            # Prevent voting on own comments
            if user.id == comment.user_id:
                raise PermissionError("Cannot vote on your own comments")

            vote = CommentVote.query.filter_by(
                comment_id=comment_id, user_id=user.id
            ).first()

            if vote:
                if vote.vote_type == vote_type:
                    current_app.db.session.delete(vote)
                else:
                    vote.vote_type = vote_type
            else:
                vote = CommentVote(
                    comment_id=comment_id, user_id=user.id, vote_type=vote_type
                )
                current_app.db.session.add(vote)

            current_app.db.session.commit()

            logger.info(f"Vote recorded on comment {comment_id} by user {user.id}")
            return True

        except Exception as e:
            current_app.db.session.rollback()
            logger.error(f"Error recording vote: {str(e)}")
            raise

    @classmethod
    def get_most_commented(cls, limit=10, include_unapproved=False, since=None):
        """
        Get the most commented instances of the model.

        Args:
            limit (int): The maximum number of instances to return.
            include_unapproved (bool): Whether to include unapproved comments in the count.
            since (datetime, optional): Only count comments since this date.

        Returns:
            list: A list of tuples containing the model instance and its comment count.
        """
        try:
            query = current_app.db.session.query(
                cls, func.count(Comment.id).label("comment_count")
            ).join(Comment)

            if not include_unapproved:
                query = query.filter(Comment.is_approved.is_(True))

            if since:
                query = query.filter(Comment.created_at >= since)

            return (
                query.group_by(cls)
                .order_by(text("comment_count DESC"))
                .limit(limit)
                .all()
            )

        except Exception as e:
            logger.error(f"Error getting most commented: {str(e)}")
            return []

    @classmethod
    def get_recently_commented(cls, limit=10, include_unapproved=False):
        """
        Get the most recently commented instances of the model.

        Args:
            limit (int): The maximum number of instances to return.
            include_unapproved (bool): Whether to include unapproved comments.

        Returns:
            list: A list of tuples containing the model instance and its most recent comment.
        """
        try:
            subquery = current_app.db.session.query(
                Comment.parent_id, func.max(Comment.created_at).label("max_created_at")
            ).filter(Comment.parent_type == cls.__name__)

            if not include_unapproved:
                subquery = subquery.filter(Comment.is_approved.is_(True))

            subquery = subquery.group_by(Comment.parent_id).subquery()

            query = (
                current_app.db.session.query(cls, Comment)
                .join(subquery, cls.id == subquery.c.parent_id)
                .join(
                    Comment,
                    (Comment.parent_id == subquery.c.parent_id)
                    & (Comment.created_at == subquery.c.max_created_at),
                )
                .order_by(subquery.c.max_created_at.desc())
                .limit(limit)
            )

            return query.all()

        except Exception as e:
            logger.error(f"Error getting recently commented: {str(e)}")
            return []

    def _on_comment_create(self, mapper, connection, target):
        """Event handler for comment creation."""
        pass

    def _on_comment_update(self, target, original_content):
        """Event handler for comment updates."""
        pass

    def _on_comment_delete(self, mapper, connection, target):
        """Event handler for comment deletion."""
        pass

    def _on_comment_approve(self, mapper, connection, target):
        """Event handler for comment approval."""
        pass


class Comment(Model):
    """
    Model to represent comments on commentable models.

    Attributes:
        id (int): Primary key
        content (Text): Comment content
        created_at (DateTime): Creation timestamp
        updated_at (DateTime): Last update timestamp
        user_id (int): Foreign key to user
        parent_id (String): ID of parent object
        parent_type (String): Type of parent object
        parent_comment_id (int): ID of parent comment for replies
        is_approved (bool): Approval status
        depth (int): Nesting depth of comment
        metadata (JSONB): Additional metadata
        approved_by_id (int): ID of approving moderator
        approved_at (DateTime): Approval timestamp
    """

    __tablename__ = "nx_comments"

    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    user_id = Column(Integer, ForeignKey("ab_user.id"), nullable=False)
    parent_id = Column(String, nullable=False)
    parent_type = Column(String(100), nullable=False)
    parent_comment_id = Column(Integer, ForeignKey("nx_comments.id"), nullable=True)
    is_approved = Column(Boolean, default=True, nullable=False)
    depth = Column(Integer, default=0, nullable=False)
    metadata = Column(MutableDict.as_mutable(JSONB), default={}, nullable=False)
    approved_by_id = Column(Integer, ForeignKey("ab_user.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="comments")
    approved_by = relationship(
        "User", foreign_keys=[approved_by_id], backref="approved_comments"
    )
    replies = relationship(
        "Comment",
        backref=backref("parent_comment", remote_side=[id]),
        cascade="all, delete-orphan",
    )
    votes = relationship("CommentVote", backref="comment", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint(
            "parent_id", "parent_type", "parent_comment_id", name="uq_comment_parent"
        ),
    )

    @property
    def vote_count(self):
        """Get total vote count (upvotes - downvotes)."""
        return sum(1 if vote.vote_type == "up" else -1 for vote in self.votes)

    @property
    def upvotes(self):
        """Get number of upvotes."""
        return sum(1 for vote in self.votes if vote.vote_type == "up")

    @property
    def downvotes(self):
        """Get number of downvotes."""
        return sum(1 for vote in self.votes if vote.vote_type == "down")

    def __repr__(self):
        return f"<Comment {self.id} by User {self.user_id} on {self.parent_type}:{self.parent_id}>"


class CommentVote(Model):
    """
    Model to represent votes on comments.

    Attributes:
        id (int): Primary key
        comment_id (int): Foreign key to comment
        user_id (int): Foreign key to user
        vote_type (str): Vote type ('up' or 'down')
        created_at (DateTime): Vote timestamp
        metadata (JSONB): Additional metadata
    """

    __tablename__ = "nx_comment_votes"

    id = Column(Integer, primary_key=True)
    comment_id = Column(Integer, ForeignKey("nx_comments.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("ab_user.id"), nullable=False)
    vote_type = Column(String(4), nullable=False)  # 'up' or 'down'
    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    metadata = Column(MutableDict.as_mutable(JSONB), default={}, nullable=False)

    __table_args__ = (
        UniqueConstraint("comment_id", "user_id", name="uq_comment_vote"),
    )

    def __repr__(self):
        return f"<CommentVote {self.id} by User {self.user_id} on Comment {self.comment_id}>"


# Example usage remains unchanged
