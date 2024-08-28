"""
cache_mixin.py

This module provides a CacheMixin class for implementing caching mechanisms
in SQLAlchemy models for Flask-AppBuilder applications.

The CacheMixin allows easy caching of model instances and query results,
improving application performance by reducing database queries for
frequently accessed data.

Dependencies:
    - SQLAlchemy
    - Flask-AppBuilder
    - Flask-Caching
    - pickle (for serialization)

Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.0
"""

from flask import current_app
from sqlalchemy import event
from sqlalchemy.orm import Query
from flask_appbuilder.models.mixins import AuditMixin
import pickle
from functools import wraps
from datetime import datetime, timedelta

class CachedQuery(Query):
    """
    Custom query class that integrates caching functionality.
    """
    def __init__(self, *args, **kwargs):
        super(CachedQuery, self).__init__(*args, **kwargs)
        self._cache_key = None
        self._cache_timeout = None

    def cache(self, key=None, timeout=None):
        """
        Mark the query for caching.

        Args:
            key (str, optional): Custom cache key. If not provided, one will be generated.
            timeout (int, optional): Cache timeout in seconds.

        Returns:
            CachedQuery: The query object for method chaining.
        """
        self._cache_key = key
        self._cache_timeout = timeout
        return self

    def _get_cache_key(self):
        """Generate a cache key if not provided."""
        if self._cache_key is None:
            query_string = str(self.statement.compile(compile_kwargs={"literal_binds": True}))
            self._cache_key = f"query_{hash(query_string)}"
        return self._cache_key

    def __iter__(self):
        """Override the iterator to implement caching."""
        if self._cache_key is None:
            return super(CachedQuery, self).__iter__()

        cache = current_app.extensions['cache']
        key = self._get_cache_key()
        result = cache.get(key)

        if result is None:
            result = list(super(CachedQuery, self).__iter__())
            cache.set(key, pickle.dumps(result), timeout=self._cache_timeout)
        else:
            result = pickle.loads(result)

        return iter(result)

class CacheMixin(AuditMixin):
    """
    A mixin class for adding caching functionality to SQLAlchemy models.

    This mixin provides methods for caching individual model instances and
    query results. It also handles cache invalidation on model updates.

    Class Attributes:
        __cache_timeout__ (int): Default cache timeout in seconds.
        query_class (CachedQuery): Custom query class for caching queries.
    """

    __cache_timeout__ = 3600  # Default cache timeout: 1 hour
    query_class = CachedQuery

    @classmethod
    def __declare_last__(cls):
        """Set up event listeners for cache invalidation."""
        event.listen(cls, 'after_update', cls._invalidate_cache)
        event.listen(cls, 'after_delete', cls._invalidate_cache)

    @classmethod
    def _invalidate_cache(cls, mapper, connection, target):
        """Invalidate the cache for the updated/deleted instance."""
        cache = current_app.extensions['cache']
        cache.delete(cls._get_instance_cache_key(target.id))

    @classmethod
    def _get_instance_cache_key(cls, instance_id):
        """Generate a cache key for an instance."""
        return f"{cls.__name__}:{instance_id}"

    @classmethod
    def cache_instance(cls, instance):
        """
        Cache a model instance.

        Args:
            instance: The model instance to cache.
        """
        cache = current_app.extensions['cache']
        key = cls._get_instance_cache_key(instance.id)
        cache.set(key, pickle.dumps(instance), timeout=cls.__cache_timeout__)

    @classmethod
    def get_cached(cls, instance_id):
        """
        Retrieve a cached model instance.

        Args:
            instance_id: The ID of the instance to retrieve.

        Returns:
            The cached instance if found, None otherwise.
        """
        cache = current_app.extensions['cache']
        key = cls._get_instance_cache_key(instance_id)
        cached_data = cache.get(key)
        if cached_data:
            return pickle.loads(cached_data)
        return None

    @classmethod
    def bulk_cache(cls, instances):
        """
        Cache multiple instances at once.

        Args:
            instances (list): List of model instances to cache.
        """
        cache = current_app.extensions['cache']
        with cache.pipeline() as pipe:
            for instance in instances:
                key = cls._get_instance_cache_key(instance.id)
                pipe.set(key, pickle.dumps(instance), timeout=cls.__cache_timeout__)

    @classmethod
    def cached_query(cls):
        """
        Start a cached query.

        Returns:
            CachedQuery: A query object with caching capabilities.
        """
        return cls.query.cache()

    @staticmethod
    def cached_method(timeout=None):
        """
        Decorator for caching method results.

        Args:
            timeout (int, optional): Cache timeout in seconds.

        Returns:
            function: Decorated method with caching.
        """
        def decorator(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                cache = current_app.extensions['cache']
                key = f"{self.__class__.__name__}:{self.id}:{func.__name__}:{args}:{kwargs}"
                result = cache.get(key)
                if result is None:
                    result = func(self, *args, **kwargs)
                    cache.set(key, pickle.dumps(result), timeout=timeout)
                else:
                    result = pickle.loads(result)
                return result
            return wrapper
        return decorator

    def refresh_cache(self):
        """Refresh the cache for this instance."""
        self.cache_instance(self)

    @classmethod
    def clear_cache(cls):
        """Clear all cached data for this model."""
        cache = current_app.extensions['cache']
        cache.delete_memoized(cls.get_cached)
        cache.delete_memoized(cls.cached_query)

# Example usage (commented out):
"""
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String
from mixins.cache_mixin import CacheMixin

class User(CacheMixin, Model):
    __tablename__ = 'nx_users'
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)

    __cache_timeout__ = 1800  # Set custom cache timeout to 30 minutes

    @CacheMixin.cached_method(timeout=600)
    def get_full_profile(self):
        # Simulating a complex operation
        return {
            "username": self.username,
            "email": self.email,
            "posts_count": len(self.posts),
            "followers_count": len(self.followers)
        }

# In your application code:
# Caching an instance
user = User.query.get(1)
User.cache_instance(user)

# Retrieving a cached instance
cached_user = User.get_cached(1)

# Using cached query
recent_users = User.cached_query().filter(User.created_on > datetime.utcnow() - timedelta(days=7)).all()

# Using cached method
user_profile = user.get_full_profile()  # This result will be cached

# Bulk caching
users = User.query.limit(100).all()
User.bulk_cache(users)

# Clear cache
User.clear_cache()
"""
