"""
rate_limit_mixin.py

This module provides a RateLimitMixin class for implementing rate limiting
capabilities in SQLAlchemy models for Flask-AppBuilder applications.

The RateLimitMixin allows for defining and enforcing rate limits on operations,
tracking request counts, and handling rate limit violations.

Dependencies:
    - SQLAlchemy
    - Flask-AppBuilder
    - Redis (for distributed rate limiting)

Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.0
"""

from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from datetime import datetime, timedelta
from flask import current_app, request, abort
import redis
import json
import logging

logger = logging.getLogger(__name__)

class RateLimitMixin:
    """
    A mixin class for adding rate limiting capabilities to SQLAlchemy models.

    This mixin provides methods for defining rate limits, checking if operations
    are allowed based on these limits, and handling rate limit violations.

    Class Attributes:
        __rate_limits__ (dict): Defines the rate limits for different operations.
            Format: {
                'operation_name': {
                    'limit': int,  # number of allowed requests
                    'per': int,    # time window in seconds
                    'by': str      # 'ip', 'user', or 'api_key'
                }
            }
    """

    __rate_limits__ = {}

    @classmethod
    def __declare_last__(cls):
        if not cls.__rate_limits__:
            raise ValueError(f"__rate_limits__ must be defined for {cls.__name__}")

    @staticmethod
    def get_redis_client():
        """Get or create a Redis client."""
        if not hasattr(current_app, 'redis_client'):
            current_app.redis_client = redis.Redis.from_url(current_app.config['REDIS_URL'])
        return current_app.redis_client

    @classmethod
    def check_rate_limit(cls, operation, identifier=None):
        """
        Check if an operation is allowed based on the defined rate limit.

        Args:
            operation (str): The name of the operation to check.
            identifier (str, optional): The identifier for the rate limit (e.g., user ID, IP).
                If not provided, it will be determined based on the rate limit configuration.

        Returns:
            bool: True if the operation is allowed, False otherwise.

        Raises:
            ValueError: If the operation is not defined in __rate_limits__.
        """
        if operation not in cls.__rate_limits__:
            raise ValueError(f"Rate limit not defined for operation: {operation}")

        limit_config = cls.__rate_limits__[operation]
        redis_client = cls.get_redis_client()

        if not identifier:
            if limit_config['by'] == 'ip':
                identifier = request.remote_addr
            elif limit_config['by'] == 'user':
                identifier = str(current_app.user.id) if current_app.user else 'anonymous'
            elif limit_config['by'] == 'api_key':
                identifier = request.headers.get('X-API-Key', 'anonymous')
            else:
                raise ValueError(f"Invalid 'by' configuration for rate limit: {limit_config['by']}")

        key = f"rate_limit:{cls.__name__}:{operation}:{identifier}"
        
        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, limit_config['per'])
        result = pipe.execute()

        request_count = result[0]

        if request_count > limit_config['limit']:
            cls._handle_rate_limit_exceeded(operation, identifier, limit_config)
            return False

        return True

    @classmethod
    def _handle_rate_limit_exceeded(cls, operation, identifier, limit_config):
        """
        Handle the case when a rate limit is exceeded.

        Args:
            operation (str): The name of the operation that exceeded the rate limit.
            identifier (str): The identifier for the rate limit (e.g., user ID, IP).
            limit_config (dict): The rate limit configuration for the operation.
        """
        logger.warning(f"Rate limit exceeded for {operation} by {identifier}")
        
        # Log the violation
        violation = RateLimitViolation(
            model_name=cls.__name__,
            operation=operation,
            identifier=identifier,
            limit=limit_config['limit'],
            period=limit_config['per']
        )
        current_app.db.session.add(violation)
        current_app.db.session.commit()

        # Abort the request with a 429 Too Many Requests status
        abort(429, description=f"Rate limit exceeded. Try again in {limit_config['per']} seconds.")

    @classmethod
    def get_rate_limit_status(cls, operation, identifier=None):
        """
        Get the current status of a rate limit for an operation.

        Args:
            operation (str): The name of the operation to check.
            identifier (str, optional): The identifier for the rate limit.

        Returns:
            dict: A dictionary containing the current request count and time until reset.
        """
        if operation not in cls.__rate_limits__:
            raise ValueError(f"Rate limit not defined for operation: {operation}")

        limit_config = cls.__rate_limits__[operation]
        redis_client = cls.get_redis_client()

        if not identifier:
            if limit_config['by'] == 'ip':
                identifier = request.remote_addr
            elif limit_config['by'] == 'user':
                identifier = str(current_app.user.id) if current_app.user else 'anonymous'
            elif limit_config['by'] == 'api_key':
                identifier = request.headers.get('X-API-Key', 'anonymous')
            else:
                raise ValueError(f"Invalid 'by' configuration for rate limit: {limit_config['by']}")

        key = f"rate_limit:{cls.__name__}:{operation}:{identifier}"
        
        pipe = redis_client.pipeline()
        pipe.get(key)
        pipe.ttl(key)
        result = pipe.execute()

        count = int(result[0]) if result[0] else 0
        ttl = result[1] if result[1] > 0 else limit_config['per']

        return {
            'current_count': count,
            'limit': limit_config['limit'],
            'remaining': max(0, limit_config['limit'] - count),
            'reset_in': ttl
        }

class RateLimitViolation(Model):
    """
    Model to log rate limit violations.
    """
    __tablename__ = 'nx_rate_limit_violations'

    id = Column(Integer, primary_key=True)
    model_name = Column(String(100), nullable=False)
    operation = Column(String(100), nullable=False)
    identifier = Column(String(100), nullable=False)
    limit = Column(Integer, nullable=False)
    period = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<RateLimitViolation {self.model_name}:{self.operation} by {self.identifier}>"

# Example usage (commented out):
"""
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String
from mixins.rate_limit_mixin import RateLimitMixin

class APIEndpoint(RateLimitMixin, Model):
    __tablename__ = 'nx_api_endpoints'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

    __rate_limits__ = {
        'get_data': {'limit': 100, 'per': 3600, 'by': 'user'},  # 100 requests per hour per user
        'create_item': {'limit': 10, 'per': 60, 'by': 'ip'}     # 10 requests per minute per IP
    }

# In your Flask route or FAB ModelView method:

@expose('/api/get_data')
def get_data():
    if APIEndpoint.check_rate_limit('get_data'):
        # Process the request
        return jsonify({"data": "Here's your data"})
    else:
        # Rate limit exceeded, the mixin will have already aborted with a 429 status

@expose('/api/create_item', methods=['POST'])
def create_item():
    if APIEndpoint.check_rate_limit('create_item'):
        # Process the item creation
        return jsonify({"status": "Item created successfully"})
    else:
        # Rate limit exceeded, the mixin will have already aborted with a 429 status

# To get the current rate limit status:
@expose('/api/rate_limit_status')
def rate_limit_status():
    get_data_status = APIEndpoint.get_rate_limit_status('get_data')
    create_item_status = APIEndpoint.get_rate_limit_status('create_item')
    return jsonify({
        "get_data": get_data_status,
        "create_item": create_item_status
    })
"""
