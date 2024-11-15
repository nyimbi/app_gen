"""
full_text_search_mixin.py

This module provides a FullTextSearchMixin class for implementing full-text
search capabilities in SQLAlchemy models for Flask-AppBuilder applications.

The FullTextSearchMixin allows easy integration of powerful full-text search
features, focusing on PostgreSQL's built-in full-text search functionality.

Dependencies:
    - SQLAlchemy
    - Flask-AppBuilder
    - psycopg2 (for PostgreSQL-specific features)

Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.0
"""

from flask_appbuilder.models.mixins import AuditMixin
from sqlalchemy import Column, Index, cast, func, event
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Query
from sqlalchemy.sql import expression
import re

class FullTextSearchMixin(AuditMixin):
    """
    A mixin class for adding full-text search capabilities to SQLAlchemy models.

    This mixin provides methods for creating and querying a full-text search
    vector, as well as utilities for ranking and highlighting search results.

    Class Attributes:
        __fulltext_columns__ (dict): A dictionary mapping field names to their search weights.
        __tsvector_column__ (str): The name of the column to store the search vector.
        __search_config__ (str): The text search configuration to use (default: 'english').
    """

    __fulltext_columns__ = {}  # e.g., {'title': 'A', 'content': 'B'}
    __tsvector_column__ = 'search_vector'
    __search_config__ = 'english'

    @declared_attr
    def search_vector(cls):
        return Column(TSVECTOR)

    @classmethod
    def __declare_last__(cls):
        if not cls.__fulltext_columns__:
            raise ValueError("__fulltext_columns__ must be defined.")

        # Create the search vector expression
        search_vector = func.to_tsvector(
            cls.__search_config__,
            expression.text(' '.join([
                f"coalesce({col}, '')" if weight == 'D' else f"setweight(to_tsvector('{cls.__search_config__}', coalesce({col}, '')), '{weight}')"
                for col, weight in cls.__fulltext_columns__.items()
            ]))
        )

        # Create the search vector column
        setattr(cls, cls.__tsvector_column__, Column(TSVECTOR))

        # Create a GIN index on the search vector
        Index(
            f'ix_{cls.__tablename__}_{cls.__tsvector_column__}',
            cls.search_vector,
            postgresql_using='gin'
        )

        # Set up event listeners to update the search vector
        @event.listens_for(cls, 'before_insert')
        @event.listens_for(cls, 'before_update')
        def update_search_vector(mapper, connection, target):
            target.search_vector = search_vector

    @classmethod
    def search(cls, query, search_term, sort=True):
        """
        Perform a full-text search query.

        Args:
            query (Query): The base SQLAlchemy query.
            search_term (str): The search term.
            sort (bool): Whether to sort results by relevance.

        Returns:
            Query: SQLAlchemy query with full-text search applied.
        """
        search_query = func.plainto_tsquery(cls.__search_config__, search_term)
        search_condition = cls.search_vector.op('@@')(search_query)
        
        result = query.filter(search_condition)
        
        if sort:
            result = result.order_by(func.ts_rank_cd(cls.search_vector, search_query).desc())
        
        return result

    @classmethod
    def highlight_term(cls, column, search_term):
        """
        Generate SQL expression to highlight search term in a column.

        Args:
            column (Column): The column to search in.
            search_term (str): The search term to highlight.

        Returns:
            SQLAlchemy expression for highlighted text.
        """
        return func.ts_headline(
            cls.__search_config__,
            column,
            func.plainto_tsquery(cls.__search_config__, search_term),
            'StartSel = <mark>, StopSel = </mark>, MaxWords=35, MinWords=15, ShortWord=3, HighlightAll=FALSE, MaxFragments=3, FragmentDelimiter = " ... "'
        )

    @classmethod
    def search_ranking(cls, search_term):
        """
        Generate SQL expression for search result ranking.

        Args:
            search_term (str): The search term.

        Returns:
            SQLAlchemy expression for ranking.
        """
        return func.ts_rank_cd(cls.search_vector, func.plainto_tsquery(cls.__search_config__, search_term))

    @staticmethod
    def remove_html_tags(text):
        """
        Remove HTML tags from a string.

        Args:
            text (str): The text to clean.

        Returns:
            str: Text with HTML tags removed.
        """
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)

    @classmethod
    def reindex_all(cls, session):
        """
        Reindex all instances of the model.

        This method updates the search vector for all existing records.

        Args:
            session: SQLAlchemy session.
        """
        search_vector = func.to_tsvector(
            cls.__search_config__,
            expression.text(' '.join([
                f"coalesce({col}, '')" if weight == 'D' else f"setweight(to_tsvector('{cls.__search_config__}', coalesce({col}, '')), '{weight}')"
                for col, weight in cls.__fulltext_columns__.items()
            ]))
        )

        session.query(cls).update(
            {cls.__tsvector_column__: search_vector},
            synchronize_session=False
        )
        session.commit()

# Example usage (commented out):
"""
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, Text
from mixins.full_text_search_mixin import FullTextSearchMixin

class Article(FullTextSearchMixin, Model):
    __tablename__ = 'nx_articles'
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)

    __fulltext_columns__ = {
        'title': 'A',
        'content': 'B'
    }
    __search_config__ = 'english'  # Use English text search configuration

# In your application code:

# Perform a search
search_term = "example search"
results = Article.search(Article.query, search_term).all()

# Get highlighted results
for article in results:
    highlighted_title = Article.highlight_term(Article.title, search_term)
    highlighted_content = Article.highlight_term(Article.content, search_term)
    print(f"Title: {highlighted_title}")
    print(f"Content: {highlighted_content}")

# Sort by relevance
sorted_results = Article.query.order_by(Article.search_ranking(search_term).desc()).all()

# Reindex all articles (e.g., after bulk import)
Article.reindex_all(db.session)
"""
