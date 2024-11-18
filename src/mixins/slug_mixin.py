"""
slug_mixin.py

This module provides a SlugMixin class for automatically generating and managing
URL-friendly slugs for SQLAlchemy models in Flask-AppBuilder applications.

The SlugMixin allows easy creation of unique, URL-friendly identifiers for model
instances, which is particularly useful for creating clean, SEO-friendly URLs.

Dependencies:
    - SQLAlchemy
    - Flask-AppBuilder
    - python-slugify

Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.0
"""

from flask_appbuilder import Model
from sqlalchemy import Column, String, event
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import validates
from flask_appbuilder.models.mixins import AuditMixin
from slugify import slugify
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

class SlugMixin(AuditMixin):
    """
    A mixin class for adding slug functionality to SQLAlchemy models.

    This mixin automatically generates a URL-friendly slug based on a specified field.
    It ensures slug uniqueness within the model and provides methods for slug-based lookups.

    Attributes:
        __slug_source__ (str): The name of the field to generate the slug from.
        __slug_max_length__ (int): Maximum length of the generated slug (default: 100).
        __slug_separator__ (str): The separator to use in the slug (default: '-').
    """

    __slug_source__ = None  # Must be set in the implementing class
    __slug_max_length__ = 100
    __slug_separator__ = '-'

    @declared_attr
    def slug(cls):
        return Column(String(cls.__slug_max_length__), unique=True, index=True, nullable=False)

    @classmethod
    def __declare_last__(cls):
        if not cls.__slug_source__:
            raise AttributeError(f"__slug_source__ must be set on {cls.__name__}")

        @event.listens_for(cls, 'before_insert')
        def generate_slug(mapper, connection, target):
            target.slug = target.create_slug()

        @event.listens_for(cls, 'before_update')
        def update_slug(mapper, connection, target):
            if hasattr(target, '_slug_source_changed') and target._slug_source_changed:
                target.slug = target.create_slug()
                delattr(target, '_slug_source_changed')

    def create_slug(self):
        """
        Generate a unique slug for the instance.

        Returns:
            str: A unique slug for the instance.
        """
        base_slug = self._slugify(getattr(self, self.__slug_source__))
        slug = base_slug
        counter = 1
        while self._slug_exists(slug):
            slug = f"{base_slug}{self.__slug_separator__}{counter}"
            counter += 1
        return slug

    def _slugify(self, value):
        """
        Convert a string to a URL-friendly slug.

        Args:
            value (str): The string to convert to a slug.

        Returns:
            str: A URL-friendly slug.
        """
        return slugify(value, max_length=self.__slug_max_length__, separator=self.__slug_separator__)

    def _slug_exists(self, slug):
        """
        Check if a slug already exists in the database.

        Args:
            slug (str): The slug to check for existence.

        Returns:
            bool: True if the slug exists, False otherwise.
        """
        return self.query.filter(self.__class__.slug == slug).first() is not None

    @validates(f'{__slug_source__}')
    def validate_slug_source(self, key, value):
        """
        Validate the slug source field and mark it for update if changed.

        Args:
            key (str): The name of the attribute being set.
            value: The value being set.

        Returns:
            The value being set.
        """
        if getattr(self, key, None) != value:
            self._slug_source_changed = True
        return value

    @classmethod
    def get_by_slug(cls, slug):
        """
        Retrieve an instance by its slug.

        Args:
            slug (str): The slug to search for.

        Returns:
            An instance of the model with the given slug.

        Raises:
            NoResultFound: If no instance with the given slug is found.
        """
        instance = cls.query.filter(cls.slug == slug).first()
        if instance is None:
            raise NoResultFound(f"No {cls.__name__} found with slug: {slug}")
        return instance

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id}, slug='{self.slug}')>"

# Example usage (commented out):
"""
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String
from mixins.slug_mixin import SlugMixin

class Article(SlugMixin, Model):
    __tablename__ = 'nx_articles'
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(Text)

    __slug_source__ = 'title'
    __slug_max_length__ = 80  # Customize slug max length

# In your application code:
article = Article(title="My First Article")
db.session.add(article)
db.session.commit()

print(article.slug)  # Output: 'my-first-article'

# Retrieve by slug
try:
    retrieved_article = Article.get_by_slug('my-first-article')
    print(retrieved_article.title)  # Output: 'My First Article'
except NoResultFound:
    print("Article not found")

# Update title (slug will be automatically updated)
article.title = "Updated Article Title"
db.session.commit()
print(article.slug)  # Output: 'updated-article-title'
"""
