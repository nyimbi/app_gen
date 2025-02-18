"""
full_text_search_mixin.py

This module provides a FullTextSearchMixin class for implementing full-text
search capabilities in SQLAlchemy models for Flask-AppBuilder applications.

The FullTextSearchMixin allows easy integration of powerful full-text search
features, focusing on PostgreSQL's built-in full-text search functionality.

Dependencies:
    - SQLAlchemy>=1.4.0
    - Flask-AppBuilder>=3.4.0
    - psycopg2-binary>=2.9.0
    - PostgreSQL>=12.0

Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.1
"""

import logging
import re
from typing import Any, Dict, List, Optional, Union

from flask_appbuilder.models.mixins import AuditMixin
from sqlalchemy import DDL, Column, Index, event, func, text
from sqlalchemy.dialects.postgresql import REGCONFIG, TSVECTOR
from sqlalchemy.event import listen
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Query
from sqlalchemy.sql import expression

logger = logging.getLogger(__name__)


class FullTextSearchMixin(AuditMixin):
    """
    A mixin class for adding full-text search capabilities to SQLAlchemy models.

    This mixin provides comprehensive full-text search functionality using PostgreSQL's
    built-in text search features including weighted searches, relevance ranking,
    and result highlighting.

    Class Attributes:
        __fulltext_columns__ (dict): Maps field names to search weights (A,B,C,D).
            Example: {'title': 'A', 'content': 'B', 'tags': 'C', 'notes': 'D'}
        __tsvector_column__ (str): Name of the column storing the search vector.
        __search_config__ (str): PostgreSQL text search configuration (default: 'english').
        __index_type__ (str): PostgreSQL index type ('gin' or 'gist').
        __highlight_opts__ (dict): Default options for highlighting search results.

    Example:
        class Article(FullTextSearchMixin, Model):
            __tablename__ = 'articles'
            id = Column(Integer, primary_key=True)
            title = Column(String(200), nullable=False)
            content = Column(Text)

            __fulltext_columns__ = {
                'title': 'A',    # Highest priority
                'content': 'B'   # Secondary priority
            }
            __search_config__ = 'english'
            __index_type__ = 'gin'
    """

    __fulltext_columns__: Dict[str, str] = {}
    __tsvector_column__ = "search_vector"
    __search_config__ = "english"
    __index_type__ = "gin"
    __highlight_opts__ = {
        "StartSel": "<mark>",
        "StopSel": "</mark>",
        "MaxWords": 35,
        "MinWords": 15,
        "ShortWord": 3,
        "HighlightAll": False,
        "MaxFragments": 3,
        "FragmentDelimiter": " ... ",
    }

    @declared_attr
    def search_vector(cls):
        """TSVector column for storing pre-computed search vectors."""
        return Column(TSVECTOR, nullable=True)

    @declared_attr
    def search_config(cls):
        """Column for storing text search configuration."""
        return Column(
            REGCONFIG,
            nullable=False,
            server_default=text(f"'{cls.__search_config__}'::regconfig"),
        )

    @classmethod
    def __declare_last__(cls):
        if not cls.__fulltext_columns__:
            raise ValueError(f"__fulltext_columns__ must be defined for {cls.__name__}")

        # Validate weights
        valid_weights = {"A", "B", "C", "D"}
        invalid_weights = {
            w for w in cls.__fulltext_columns__.values() if w not in valid_weights
        }
        if invalid_weights:
            raise ValueError(
                f"Invalid weights {invalid_weights}. Must be one of {valid_weights}"
            )

        # Create the search vector expression
        weight_groups = {}
        for col, weight in cls.__fulltext_columns__.items():
            weight_groups.setdefault(weight, []).append(col)

        search_vector = None
        for weight, columns in weight_groups.items():
            col_list = " || ".join(f"coalesce({c}, '')" for c in columns)
            weighted_vector = func.setweight(
                func.to_tsvector(cls.search_config, text(col_list)), weight
            )
            if search_vector is None:
                search_vector = weighted_vector
            else:
                search_vector = search_vector.op("||")(weighted_vector)

        # Create GIN/GiST index on search vector
        index_name = f"ix_{cls.__tablename__}_{cls.__tsvector_column__}"
        index = Index(
            index_name,
            "search_vector",
            postgresql_using=cls.__index_type__.lower(),
            postgresql_where=text("search_vector IS NOT NULL"),
        )

        # Create triggers for automatic vector updates
        trigger_ddl = DDL(
            f"""
            CREATE TRIGGER {cls.__tablename__}_search_vector_update
            BEFORE INSERT OR UPDATE ON {cls.__tablename__}
            FOR EACH ROW EXECUTE FUNCTION tsvector_update_trigger(
                {cls.__tsvector_column__},
                '{cls.__search_config__}',
                {', '.join(cls.__fulltext_columns__.keys())}
            );
        """
        )

        # Set up event listeners
        @event.listens_for(cls, "after_create")
        def create_trigger(target, connection, **kw):
            connection.execute(trigger_ddl)

        @event.listens_for(cls, "before_insert")
        @event.listens_for(cls, "before_update")
        def update_search_vector(mapper, connection, target):
            try:
                target.search_vector = search_vector
            except Exception as e:
                logger.error(f"Error updating search vector: {str(e)}")
                raise

    @classmethod
    def search(
        cls,
        query: Query,
        search_term: str,
        sort: bool = True,
        highlight: Optional[List[str]] = None,
        language: Optional[str] = None,
    ) -> Query:
        """
        Perform a full-text search query with optional highlighting.

        Args:
            query (Query): Base SQLAlchemy query
            search_term (str): Search term(s)
            sort (bool): Sort results by relevance
            highlight (List[str]): Columns to highlight
            language (str): Override default language configuration

        Returns:
            Query: SQLAlchemy query with search filters applied

        Example:
            # Basic search
            results = Article.search(Article.query, "climate change").all()

            # Search with highlighting
            results = Article.search(
                Article.query,
                "climate change",
                highlight=['title', 'content']
            ).all()
        """
        if not search_term:
            return query

        try:
            config = language or cls.__search_config__
            search_query = func.plainto_tsquery(config, search_term)
            search_condition = cls.search_vector.op("@@")(search_query)

            result = query.filter(search_condition)

            # Add highlighting if requested
            if highlight:
                for column in highlight:
                    if column in cls.__fulltext_columns__:
                        result = result.add_columns(
                            cls.highlight_term(
                                getattr(cls, column), search_term, language=language
                            ).label(f"{column}_highlighted")
                        )

            # Sort by relevance if requested
            if sort:
                result = result.order_by(
                    cls.search_ranking(search_term, language).desc()
                )

            return result

        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            raise

    @classmethod
    def highlight_term(
        cls,
        column: Column,
        search_term: str,
        language: Optional[str] = None,
        options: Optional[Dict] = None,
    ) -> expression:
        """
        Generate SQL expression to highlight search terms in text.

        Args:
            column (Column): Column to search
            search_term (str): Search term to highlight
            language (str): Override default language configuration
            options (dict): Override default highlighting options

        Returns:
            expression: SQLAlchemy expression for highlighted text
        """
        config = language or cls.__search_config__
        highlight_opts = {**cls.__highlight_opts__, **(options or {})}

        opts_str = ", ".join(
            f"{k}={v}" if isinstance(v, (int, bool)) else f"{k}={str(v)}"
            for k, v in highlight_opts.items()
        )

        return func.ts_headline(
            config, column, func.plainto_tsquery(config, search_term), opts_str
        )

    @classmethod
    def search_ranking(
        cls,
        search_term: str,
        language: Optional[str] = None,
        weights: Optional[List[float]] = None,
    ) -> expression:
        """
        Generate ranking expression for search results.

        Args:
            search_term (str): Search term
            language (str): Override default language configuration
            weights (List[float]): Custom weight values for ranking [D,C,B,A]

        Returns:
            expression: Ranking expression
        """
        config = language or cls.__search_config__
        if weights:
            return func.ts_rank_cd(
                cls.search_vector, func.plainto_tsquery(config, search_term), weights
            )
        return func.ts_rank_cd(
            cls.search_vector, func.plainto_tsquery(config, search_term)
        )

    @staticmethod
    def remove_html_tags(text: str) -> str:
        """
        Remove HTML tags from text.

        Args:
            text (str): Text containing HTML tags

        Returns:
            str: Clean text with tags removed
        """
        if not text:
            return ""
        clean = re.compile("<.*?>")
        return re.sub(clean, "", text)

    @classmethod
    def reindex_all(cls, session, batch_size: int = 1000) -> None:
        """
        Reindex all instances of the model.

        Args:
            session: SQLAlchemy session
            batch_size (int): Number of records to process per batch

        This method updates search vectors for all existing records
        using batching to handle large datasets efficiently.
        """
        try:
            total = session.query(cls).count()
            processed = 0

            while processed < total:
                batch = session.query(cls).limit(batch_size).offset(processed).all()
                for item in batch:
                    # Trigger search vector update
                    session.expire(item)
                    session.refresh(item)
                processed += len(batch)
                session.commit()
                logger.info(f"Reindexed {processed}/{total} records")

        except Exception as e:
            logger.error(f"Reindexing error: {str(e)}")
            session.rollback()
            raise


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
    summary = Column(Text)
    tags = Column(String(500))

    __fulltext_columns__ = {
        'title': 'A',      # Highest priority
        'content': 'B',    # Secondary priority
        'summary': 'C',    # Tertiary priority
        'tags': 'D'        # Lowest priority
    }
    __search_config__ = 'english'
    __index_type__ = 'gin'

# In your application code:

# Basic search
search_term = "climate change"
results = Article.search(Article.query, search_term).all()

# Search with highlighting
results = Article.search(
    Article.query,
    search_term,
    highlight=['title', 'content']
).all()

for article in results:
    print(f"Title: {article.title_highlighted}")
    print(f"Content: {article.content_highlighted}")

# Advanced search with custom ranking
results = Article.query.order_by(
    Article.search_ranking(
        search_term,
        weights=[0.1, 0.2, 0.4, 1.0]  # Custom weights D,C,B,A
    ).desc()
).all()

# Reindex after bulk import
Article.reindex_all(db.session, batch_size=500)
"""
