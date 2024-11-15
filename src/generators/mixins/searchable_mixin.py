"""
searchable_mixin.py

This module provides a SearchableMixin class for implementing advanced full-text
search capabilities in SQLAlchemy models for Flask-AppBuilder applications.

The SearchableMixin allows for efficient full-text search across specified model
fields, with support for ranking, highlighting, and language-specific configurations.

Dependencies:
    - SQLAlchemy
    - Flask-AppBuilder
    - psycopg2 (for PostgreSQL-specific features)
    - sqlalchemy.dialects.postgresql (for PostgreSQL-specific column types)

Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.0
"""

from flask_appbuilder import Model
from sqlalchemy import Column, Index, cast, func, event
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.sql import expression
from flask import current_app
import re

class SearchableMixin:
    """
    A mixin class for adding advanced full-text search capabilities to SQLAlchemy models.

    This mixin provides methods for creating and updating search vectors, performing
    full-text searches with ranking and highlighting, and managing search configurations.

    Class Attributes:
        __searchable__ (dict): A dictionary specifying searchable fields and their weights.
            Example: {'title': 'A', 'content': 'B', 'tags': 'C'}
        __search_language__ (str): The language for text search configuration (default: 'english').
    """

    __searchable__ = {}
    __search_language__ = 'english'

    @declared_attr
    def search_vector(cls):
        return Column(TSVECTOR)

    @classmethod
    def __declare_last__(cls):
        if not cls.__searchable__:
            raise ValueError(f"__searchable__ must be defined for {cls.__name__}")

        # Create the search vector expression
        search_vector = func.to_tsvector(
            cls.__search_language__,
            expression.concat_op(*[
                func.coalesce(cast(getattr(cls, field), expression.Text), '')
                if weight == 'D' else
                func.setweight(
                    func.to_tsvector(cls.__search_language__, func.coalesce(cast(getattr(cls, field), expression.Text), '')),
                    weight
                )
                for field, weight in cls.__searchable__.items()
            ])
        )

        # Create a GIN index on the search vector
        Index(
            f'ix_{cls.__tablename__}_search_vector',
            search_vector,
            postgresql_using='gin'
        )

        # Set up event listeners to update the search vector
        event.listen(cls, 'before_insert', cls._before_insert)
        event.listen(cls, 'before_update', cls._before_update)

    @classmethod
    def _before_insert(cls, mapper, connection, target):
        cls._update_search_vector(target)

    @classmethod
    def _before_update(cls, mapper, connection, target):
        cls._update_search_vector(target)

    @classmethod
    def _update_search_vector(cls, target):
        search_vector = func.to_tsvector(
            cls.__search_language__,
            expression.concat_op(*[
                func.coalesce(cast(getattr(target, field), expression.Text), '')
                if weight == 'D' else
                func.setweight(
                    func.to_tsvector(cls.__search_language__, func.coalesce(cast(getattr(target, field), expression.Text), '')),
                    weight
                )
                for field, weight in cls.__searchable__.items()
            ])
        )
        target.search_vector = search_vector

    @classmethod
    def search(cls, query, search_term, language=None, limit=None, offset=None):
        """
        Perform a full-text search query.

        Args:
            query (Query): The base SQLAlchemy query.
            search_term (str): The search term.
            language (str, optional): The language for the search configuration.
            limit (int, optional): Maximum number of results to return.
            offset (int, optional): Number of results to skip.

        Returns:
            Query: SQLAlchemy query with full-text search applied.
        """
        if language is None:
            language = cls.__search_language__

        search_query = func.plainto_tsquery(language, search_term)
        search_condition = cls.search_vector.op('@@')(search_query)
        
        result = query.filter(search_condition).order_by(
            func.ts_rank_cd(cls.search_vector, search_query).desc()
        )
        
        if limit is not None:
            result = result.limit(limit)
        if offset is not None:
            result = result.offset(offset)
        
        return result

    @classmethod
    def highlight_term(cls, column, search_term, language=None):
        """
        Generate SQL expression to highlight search term in a column.

        Args:
            column (Column): The column to search in.
            search_term (str): The search term to highlight.
            language (str, optional): The language for the search configuration.

        Returns:
            SQLAlchemy expression for highlighted text.
        """
        if language is None:
            language = cls.__search_language__

        return func.ts_headline(
            language,
            column,
            func.plainto_tsquery(language, search_term),
            'StartSel = <mark>, StopSel = </mark>, MaxWords=35, MinWords=15, ShortWord=3, HighlightAll=FALSE, MaxFragments=3, FragmentDelimiter = " ... "'
        )

    @classmethod
    def search_ranking(cls, search_term, language=None):
        """
        Generate SQL expression for search result ranking.

        Args:
            search_term (str): The search term.
            language (str, optional): The language for the search configuration.

        Returns:
            SQLAlchemy expression for ranking.
        """
        if language is None:
            language = cls.__search_language__

        return func.ts_rank_cd(cls.search_vector, func.plainto_tsquery(language, search_term))

    @classmethod
    def update_search_vector(cls, session):
        """
        Update the search vector for all instances of the model.

        Args:
            session: SQLAlchemy session.
        """
        search_vector = func.to_tsvector(
            cls.__search_language__,
            expression.concat_op(*[
                func.coalesce(cast(getattr(cls, field), expression.Text), '')
                if weight == 'D' else
                func.setweight(
                    func.to_tsvector(cls.__search_language__, func.coalesce(cast(getattr(cls, field), expression.Text), '')),
                    weight
                )
                for field, weight in cls.__searchable__.items()
            ])
        )
        session.query(cls).update({cls.search_vector: search_vector}, synchronize_session=False)
        session.commit()

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
    def get_searchable_fields(cls):
        """
        Get the list of searchable fields.

        Returns:
            dict: A dictionary of searchable fields and their weights.
        """
        return cls.__searchable__

    @classmethod
    def set_search_language(cls, language):
        """
        Set the language for text search configuration.

        Args:
            language (str): The language to set.
        """
        cls.__search_language__ = language

# Example usage (commented out):
"""
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, Text
from mixins.searchable_mixin import SearchableMixin

class Article(SearchableMixin, Model):
    __tablename__ = 'nx_articles'
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(String(200))

    __searchable__ = {'title': 'A', 'content': 'B', 'tags': 'C'}
    __search_language__ = 'english'

# In your application code:

# Performing a search
search_results = Article.search(db.session.query(Article), "python programming")

# Highlighting search results
for article in search_results:
    highlighted_title = Article.highlight_term(Article.title, "python programming")
    highlighted_content = Article.highlight_term(Article.content, "python programming")
    print(f"Title: {highlighted_title}")
    print(f"Content: {highlighted_content}")

# Ranking search results
ranked_results = db.session.query(
    Article,
    Article.search_ranking("python programming").label('rank')
).order_by('rank DESC').all()

# Updating search vectors for all articles
Article.update_search_vector(db.session)

# Changing search language
Article.set_search_language('spanish')

# Getting searchable fields
searchable_fields = Article.get_searchable_fields()
print(f"Searchable fields: {searchable_fields}")
"""
