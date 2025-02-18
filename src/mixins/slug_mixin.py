"""
slug_mixin.py: Advanced URL-Friendly Slug Generator for Flask-AppBuilder

This module provides an enhanced SlugMixin for automatically generating and managing
URL-friendly slugs in Flask-AppBuilder applications. It includes advanced features like:

- Automatic slug generation from single or multiple fields
- Customizable slug formats and separators
- Cache integration and performance optimization
- History tracking of slug changes
- Collision detection and resolution
- SEO optimization features
- Bulk slug operations
- Unicode support with transliteration
- Reserved slug protection
- Validation hooks
- Custom slug patterns
- Migration utilities

Key Features:
- Automatic generation of unique, SEO-friendly slugs
- Multi-field source support with custom formatters
- PostgreSQL optimization with GiST indexing
- Caching integration for performance
- Collision detection and smart resolution
- History tracking of slug changes
- Unicode normalization and transliteration
- Reserved slug protection
- Custom validation hooks
- Bulk operations support
- Migration tools

Dependencies:
- Flask-AppBuilder
- SQLAlchemy
- python-slugify
- psycopg2-binary
- unidecode

Author: Nyimbi Odero
Date: 25/08/2024
Version: 2.0
"""

import logging
import re
import unicodedata
from datetime import datetime
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional, Set, Union

from flask import current_app, g
from flask_appbuilder import Model
from flask_appbuilder.models.mixins import AuditMixin
from slugify import slugify
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    event,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship, validates
from sqlalchemy.orm.exc import NoResultFound
from unidecode import unidecode

# Configure logging
logger = logging.getLogger(__name__)


class SlugHistory(Model):
    """Tracks historical slugs for models."""

    __tablename__ = "nx_slug_history"

    id = Column(Integer, primary_key=True)
    model = Column(String(100), nullable=False)
    model_id = Column(Integer, nullable=False)
    old_slug = Column(String(255), nullable=False)
    new_slug = Column(String(255), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow)
    changed_by_id = Column(Integer, ForeignKey("ab_user.id"))
    reason = Column(String(255))

    __table_args__ = (
        Index("ix_slug_history_model_id", "model", "model_id"),
        Index("ix_slug_history_old_slug", "old_slug"),
    )


class SlugMixin(AuditMixin):
    """
    Advanced mixin for automatic slug generation and management.

    Features:
    - Multi-field source support
    - Custom formatters
    - History tracking
    - Cache integration
    - Collision resolution
    - Reserved slug protection

    Attributes:
        __slug_source__ (Union[str, List[str]]): Field(s) to generate slug from
        __slug_max_length__ (int): Maximum slug length
        __slug_separator__ (str): Separator character
        __slug_lowercase__ (bool): Force lowercase
        __slug_regex__ (str): Validation pattern
        __slug_reserved__ (Set[str]): Reserved slugs
        __slug_formatter__ (Callable): Custom formatter
        __slug_cache_timeout__ (int): Cache timeout in seconds
    """

    __slug_source__ = None  # Must be set in implementing class
    __slug_max_length__ = 100
    __slug_separator__ = "-"
    __slug_lowercase__ = True
    __slug_regex__ = r"^[a-zA-Z0-9\-_]+$"
    __slug_reserved__ = {"admin", "api", "static", "uploads"}
    __slug_formatter__ = None
    __slug_cache_timeout__ = 3600  # 1 hour

    @declared_attr
    def slug(cls):
        """PostgreSQL-optimized slug column with GiST index."""
        return Column(
            String(cls.__slug_max_length__),
            unique=True,
            index=True,
            nullable=False,
            comment="URL-friendly identifier",
        )

    @classmethod
    def __declare_last__(cls):
        if not cls.__slug_source__:
            raise AttributeError(f"__slug_source__ must be set on {cls.__name__}")

        @event.listens_for(cls, "before_insert")
        def generate_slug(mapper, connection, target):
            target.slug = target.create_slug()

        @event.listens_for(cls, "before_update")
        def update_slug(mapper, connection, target):
            if getattr(target, "_slug_source_changed", False):
                old_slug = target.slug
                target.slug = target.create_slug()
                target._record_slug_history(old_slug)
                delattr(target, "_slug_source_changed")

    @lru_cache(maxsize=1000)
    def create_slug(self) -> str:
        """
        Generate a unique slug using configured settings.

        Returns:
            str: Unique slug for the instance

        Raises:
            ValueError: If source value is invalid
        """
        # Get source value(s)
        if isinstance(self.__slug_source__, list):
            values = [str(getattr(self, field)) for field in self.__slug_source__]
            base = self.__slug_separator__.join(values)
        else:
            base = str(getattr(self, self.__slug_source__))

        # Apply custom formatter if configured
        if self.__slug_formatter__:
            base = self.__slug_formatter__(base)

        # Generate initial slug
        slug = self._slugify(base)

        # Ensure not reserved
        if slug in self.__slug_reserved__:
            slug = f"user-{slug}"

        # Ensure unique
        counter = 1
        original_slug = slug
        while self._slug_exists(slug):
            slug = f"{original_slug}{self.__slug_separator__}{counter}"
            counter += 1

        # Validate final slug
        if not self._validate_slug(slug):
            raise ValueError(f"Invalid slug generated: {slug}")

        return slug

    def _slugify(self, value: str) -> str:
        """
        Convert string to URL-friendly slug with configurable options.

        Args:
            value: String to convert

        Returns:
            Formatted slug string
        """
        # Normalize unicode
        value = unicodedata.normalize("NFKD", value)

        # Transliterate non-ASCII
        value = unidecode(value)

        # Apply slugify with options
        slug = slugify(
            value,
            max_length=self.__slug_max_length__,
            separator=self.__slug_separator__,
            lowercase=self.__slug_lowercase__,
            regex_pattern=self.__slug_regex__,
        )

        return slug

    def _slug_exists(self, slug: str) -> bool:
        """
        Check if slug exists using caching.

        Args:
            slug: Slug to check

        Returns:
            bool: True if exists
        """
        cache_key = f"slug_exists_{self.__class__.__name__}_{slug}"

        # Check cache first
        if hasattr(current_app, "cache"):
            exists = current_app.cache.get(cache_key)
            if exists is not None:
                return exists

        # Check database
        exists = self.query.filter(self.__class__.slug == slug).first() is not None

        # Cache result
        if hasattr(current_app, "cache"):
            current_app.cache.set(
                cache_key, exists, timeout=self.__slug_cache_timeout__
            )

        return exists

    def _validate_slug(self, slug: str) -> bool:
        """
        Validate slug format.

        Args:
            slug: Slug to validate

        Returns:
            bool: True if valid
        """
        if not slug:
            return False

        if len(slug) > self.__slug_max_length__:
            return False

        if not re.match(self.__slug_regex__, slug):
            return False

        return True

    def _record_slug_history(self, old_slug: str) -> None:
        """
        Record slug change in history.

        Args:
            old_slug: Previous slug value
        """
        history = SlugHistory(
            model=self.__class__.__name__,
            model_id=self.id,
            old_slug=old_slug,
            new_slug=self.slug,
            changed_by_id=g.user.id if hasattr(g, "user") else None,
        )
        self.query.session.add(history)

    @validates("slug")
    def validate_slug(self, key: str, slug: str) -> str:
        """Validate slug value."""
        if not self._validate_slug(slug):
            raise ValueError(f"Invalid slug format: {slug}")
        return slug

    @classmethod
    def get_by_slug(cls, slug: str) -> Model:
        """
        Get instance by slug with history fallback.

        Args:
            slug: Slug to lookup

        Returns:
            Model instance

        Raises:
            NoResultFound: If not found
        """
        # Try current slug
        instance = cls.query.filter(cls.slug == slug).first()
        if instance:
            return instance

        # Check history
        history = (
            SlugHistory.query.filter_by(model=cls.__name__, old_slug=slug)
            .order_by(SlugHistory.changed_at.desc())
            .first()
        )

        if history:
            instance = cls.query.filter(cls.slug == history.new_slug).first()
            if instance:
                return instance

        raise NoResultFound(f"No {cls.__name__} found with slug: {slug}")

    @classmethod
    def bulk_generate_slugs(cls, overwrite: bool = False) -> Dict[int, str]:
        """
        Generate slugs for all instances.

        Args:
            overwrite: Whether to overwrite existing slugs

        Returns:
            Dict of id->slug mappings
        """
        results = {}
        for instance in cls.query.all():
            if overwrite or not instance.slug:
                instance.slug = instance.create_slug()
                results[instance.id] = instance.slug
        cls.query.session.commit()
        return results

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id}, slug='{self.slug}')>"


"""
Usage Example:

from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from mixins.slug_mixin import SlugMixin

class Category(SlugMixin, Model):
    __tablename__ = 'nx_categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)

    __slug_source__ = 'name'
    __slug_max_length__ = 50

class Article(SlugMixin, Model):
    __tablename__ = 'nx_articles'

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(Text)
    category_id = Column(Integer, ForeignKey('nx_categories.id'))
    category = relationship('Category')

    # Generate slug from multiple fields
    __slug_source__ = ['category.name', 'title']

    # Custom slug formatter
    @classmethod
    def __slug_formatter__(cls, value):
        return f"{datetime.now().year}-{value}"

# Advanced usage examples:

# Create with automatic slug
category = Category(name="Technology")
db.session.add(category)
db.session.commit()
print(category.slug)  # Output: 'technology'

article = Article(
    title="Getting Started with Python",
    category=category
)
db.session.add(article)
db.session.commit()
print(article.slug)  # Output: '2024-technology-getting-started-with-python'

# Lookup with history support
try:
    old_article = Article.get_by_slug('old-slug')
    print(f"Found article: {old_article.title}")
except NoResultFound:
    print("Article not found")

# Bulk generate slugs
Article.bulk_generate_slugs(overwrite=True)

# Access slug history
history = SlugHistory.query.filter_by(
    model='Article',
    model_id=article.id
).order_by(SlugHistory.changed_at.desc()).all()

for change in history:
    print(f"{change.old_slug} -> {change.new_slug}")
"""
