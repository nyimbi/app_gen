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

Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.0
"""

from flask_appbuilder import Model
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Boolean, func, event
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declared_attr
from flask_login import current_user
from flask import current_app
from datetime import datetime

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
    """

    __commentable__ = True
    __comment_moderation__ = False
    __max_comment_depth__ = 3

    @declared_attr
    def comments(cls):
        return relationship('Comment',
                            back_populates='parent',
                            cascade='all, delete-orphan',
                            primaryjoin=f"and_(Comment.parent_id==cast({cls.__name__}.id, String), "
                                        f"Comment.parent_type=='{cls.__name__}')",
                            order_by='Comment.created_at.desc()')

    def add_comment(self, content, user=None, parent_comment_id=None):
        """
        Add a new comment to the model instance.

        Args:
            content (str): The content of the comment.
            user: The user adding the comment. If None, uses current_user.
            parent_comment_id (int, optional): ID of the parent comment if this is a reply.

        Returns:
            Comment: The newly created comment instance.

        Raises:
            ValueError: If commenting is disabled or max depth is exceeded.
        """
        if not self.__commentable__:
            raise ValueError("Commenting is not enabled for this model")

        if user is None:
            user = current_user

        if parent_comment_id:
            parent_comment = Comment.query.get(parent_comment_id)
            if parent_comment.depth >= self.__max_comment_depth__:
                raise ValueError(f"Maximum comment depth of {self.__max_comment_depth__} exceeded")
            depth = parent_comment.depth + 1
        else:
            depth = 0

        comment = Comment(
            content=content,
            user_id=user.id if user and user.is_authenticated else None,
            parent_id=str(self.id),
            parent_type=self.__class__.__name__,
            parent_comment_id=parent_comment_id,
            is_approved=not self.__comment_moderation__,
            depth=depth
        )
        current_app.db.session.add(comment)
        current_app.db.session.commit()
        return comment

    def get_comments(self, include_unapproved=False, limit=None, offset=None, include_replies=True):
        """
        Get comments for the model instance.

        Args:
            include_unapproved (bool): Whether to include unapproved comments.
            limit (int, optional): Maximum number of top-level comments to return.
            offset (int, optional): Number of top-level comments to skip.
            include_replies (bool): Whether to include nested replies.

        Returns:
            list: A list of Comment objects.
        """
        query = self.comments
        if not include_unapproved:
            query = query.filter(Comment.is_approved == True)
        if not include_replies:
            query = query.filter(Comment.parent_comment_id == None)
        
        query = query.order_by(Comment.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        
        return query.all()

    def delete_comment(self, comment_id, user=None):
        """
        Delete a comment from the model instance.

        Args:
            comment_id (int): The ID of the comment to delete.
            user: The user attempting to delete the comment. If None, uses current_user.

        Returns:
            bool: True if the comment was successfully deleted, False otherwise.
        """
        comment = Comment.query.get(comment_id)
        if comment and comment.parent_id == str(self.id) and comment.parent_type == self.__class__.__name__:
            if user is None:
                user = current_user
            if user.is_authenticated and (user.id == comment.user_id or user.has_role('Admin')):
                current_app.db.session.delete(comment)
                current_app.db.session.commit()
                return True
        return False

    def update_comment(self, comment_id, new_content, user=None):
        """
        Update the content of a comment.

        Args:
            comment_id (int): The ID of the comment to update.
            new_content (str): The new content for the comment.
            user: The user attempting to update the comment. If None, uses current_user.

        Returns:
            bool: True if the comment was successfully updated, False otherwise.
        """
        comment = Comment.query.get(comment_id)
        if comment and comment.parent_id == str(self.id) and comment.parent_type == self.__class__.__name__:
            if user is None:
                user = current_user
            if user.is_authenticated and user.id == comment.user_id:
                comment.content = new_content
                comment.updated_at = datetime.utcnow()
                current_app.db.session.commit()
                return True
        return False

    def approve_comment(self, comment_id, user=None):
        """
        Approve a comment.

        Args:
            comment_id (int): The ID of the comment to approve.
            user: The user attempting to approve the comment. If None, uses current_user.

        Returns:
            bool: True if the comment was successfully approved, False otherwise.
        """
        if not self.__comment_moderation__:
            return False

        comment = Comment.query.get(comment_id)
        if comment and comment.parent_id == str(self.id) and comment.parent_type == self.__class__.__name__:
            if user is None:
                user = current_user
            if user.is_authenticated and user.has_role('Moderator'):
                comment.is_approved = True
                current_app.db.session.commit()
                return True
        return False

    def vote_comment(self, comment_id, vote_type, user=None):
        """
        Vote on a comment (upvote or downvote).

        Args:
            comment_id (int): The ID of the comment to vote on.
            vote_type (str): 'up' for upvote, 'down' for downvote.
            user: The user voting on the comment. If None, uses current_user.

        Returns:
            bool: True if the vote was successfully recorded, False otherwise.
        """
        comment = Comment.query.get(comment_id)
        if comment and comment.parent_id == str(self.id) and comment.parent_type == self.__class__.__name__:
            if user is None:
                user = current_user
            if user.is_authenticated:
                vote = CommentVote.query.filter_by(comment_id=comment_id, user_id=user.id).first()
                if vote:
                    if vote.vote_type == vote_type:
                        current_app.db.session.delete(vote)
                    else:
                        vote.vote_type = vote_type
                else:
                    vote = CommentVote(comment_id=comment_id, user_id=user.id, vote_type=vote_type)
                    current_app.db.session.add(vote)
                current_app.db.session.commit()
                return True
        return False

    @classmethod
    def get_most_commented(cls, limit=10, include_unapproved=False):
        """
        Get the most commented instances of the model.

        Args:
            limit (int): The maximum number of instances to return.
            include_unapproved (bool): Whether to include unapproved comments in the count.

        Returns:
            list: A list of tuples containing the model instance and its comment count.
        """
        query = current_app.db.session.query(
            cls,
            func.count(Comment.id).label('comment_count')
        ).join(Comment)
        
        if not include_unapproved:
            query = query.filter(Comment.is_approved == True)
        
        return query.group_by(cls).order_by(func.count(Comment.id).desc()).limit(limit).all()

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
        subquery = current_app.db.session.query(
            Comment.parent_id,
            func.max(Comment.created_at).label('max_created_at')
        ).filter(Comment.parent_type == cls.__name__)
        
        if not include_unapproved:
            subquery = subquery.filter(Comment.is_approved == True)
        
        subquery = subquery.group_by(Comment.parent_id).subquery()

        query = current_app.db.session.query(cls, Comment).join(
            subquery,
            cls.id == subquery.c.parent_id
        ).join(
            Comment,
            (Comment.parent_id == subquery.c.parent_id) &
            (Comment.created_at == subquery.c.max_created_at)
        ).order_by(subquery.c.max_created_at.desc()).limit(limit)

        return query.all()

class Comment(Model):
    """
    Model to represent comments on commentable models.
    """
    __tablename__ = 'nx_comments'

    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    user_id = Column(Integer, ForeignKey('ab_user.id'), nullable=True)
    parent_id = Column(String, nullable=False)
    parent_type = Column(String(100), nullable=False)
    parent_comment_id = Column(Integer, ForeignKey('nx_comments.id'), nullable=True)
    is_approved = Column(Boolean, default=True, nullable=False)
    depth = Column(Integer, default=0, nullable=False)

    user = relationship('User', backref='comments')
    replies = relationship('Comment', backref=backref('parent_comment', remote_side=[id]))
    votes = relationship('CommentVote', backref='comment', cascade='all, delete-orphan')

    @property
    def vote_count(self):
        return sum(1 if vote.vote_type == 'up' else -1 for vote in self.votes)

    def __repr__(self):
        return f"<Comment {self.id} by User {self.user_id} on {self.parent_type}:{self.parent_id}>"

class CommentVote(Model):
    """
    Model to represent votes on comments.
    """
    __tablename__ = 'nx_comment_votes'

    id = Column(Integer, primary_key=True)
    comment_id = Column(Integer, ForeignKey('nx_comments.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('ab_user.id'), nullable=False)
    vote_type = Column(String(4), nullable=False)  # 'up' or 'down'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('comment_id', 'user_id', name='uq_comment_vote'),
    )

# Example usage (commented out):
"""
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, Text
from mixins.commentable_mixin import CommentableMixin

class Article(CommentableMixin, Model):
    __tablename__ = 'nx_articles'
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)

    __commentable__ = True
    __comment_moderation__ = True
    __max_comment_depth__ = 3

# In your application code:

# Creating an article and adding comments
article = Article(title="Sample Article", content="This is a sample article content.")
db.session.add(article)
db.session.commit()

user1 = User.query.get(1)
user2 = User.query.get(2)

comment1 = article.add_comment("Great article!", user1)
comment2 = article.add_comment("I agree, very informative.", user2)
reply1 = article.add_comment("Thanks for your feedback!", user1, parent_comment_id=comment1.id)

# Approving a comment (if moderation is enabled)
moderator = User.query.filter_by(username='moderator').first()
article.approve_comment(comment2.id, moderator)

# Voting on comments
article.vote_comment(comment1.id, 'up', user2)
article.vote_comment(comment2.id, 'down', user1)

# Retrieving comments
all_comments = article.get_comments(include_unapproved=True, include_replies=True)
top_level_comments = article.get_comments(include_replies=False, limit=5)

# Getting most commented articles
most_commented = Article.get_most_commented(limit=5)

# Getting recently commented articles
recent_comments = Article.get_recently_commented(limit=5)

# Updating a comment
article.update_comment(comment1.id, "Updated: Great article, I learned a lot!", user1)

# Deleting a comment
article.delete_comment(comment2.id, user2)
"""
