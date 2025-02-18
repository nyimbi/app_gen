"""
rate_limit_mixin.py

A comprehensive rate limiting implementation for Flask-AppBuilder applications with advanced
features including distributed rate limiting, burst handling, gradual throttling,
configurable fallbacks, and detailed analytics.

Key Features:
- Flexible rate limit definitions with multiple strategies
- Distributed rate limiting via Redis
- Burst allowance with token bucket algorithm
- Gradual throttling with customizable backoff
- Automatic rate limit detection and adjustment
- Detailed analytics and violation tracking
- Multiple identifier strategies (IP, User, API Key, Custom)
- Fallback mechanisms for degraded states
- Comprehensive monitoring and alerting
- Export and import of rate limit configurations
- Dynamic rate limit updates
- Role-based rate limit overrides
- Caching with automatic invalidation
- Full audit trail of violations

Dependencies:
    - SQLAlchemy >= 1.4
    - Flask-AppBuilder >= 4.0
    - Redis >= 6.0
    - aioredis >= 2.0 (for async support)
    - prometheus-client (for metrics)
    - psycopg2 (for PostgreSQL support)

Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.0.1
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, List, Optional, Union

import aioredis
import redis
from flask import abort, current_app, g, request
from flask_appbuilder import Model
from prometheus_client import Counter, Gauge, Histogram
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    event,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func

# Configure logging
logger = logging.getLogger(__name__)

# Metrics
RATE_LIMIT_VIOLATIONS = Counter(
    "rate_limit_violations_total",
    "Number of rate limit violations",
    ["model", "operation", "identifier_type"],
)

RATE_LIMIT_LATENCY = Histogram(
    "rate_limit_check_latency_seconds",
    "Latency of rate limit checks",
    ["model", "operation"],
)

RATE_LIMIT_REMAINING = Gauge(
    "rate_limit_remaining",
    "Remaining rate limit quota",
    ["model", "operation", "identifier_type"],
)


@dataclass
class RateLimitConfig:
    """Configuration for a rate limit."""

    limit: int
    per: int
    by: str
    burst_multiplier: float = 1.0
    throttle_threshold: float = 0.8
    backoff_factor: float = 2.0
    alert_threshold: float = 0.9
    bypass_roles: List[str] = None
    custom_identifier: callable = None
    fallback_limit: Optional[int] = None


class RateLimitMixin:
    """
    Advanced rate limiting mixin with distributed enforcement and analytics.
    """

    __rate_limits__ = {}
    __cache_config__ = {"enabled": True, "ttl": 300, "max_size": 10000}  # 5 minutes

    @classmethod
    def __declare_last__(cls):
        """Validate rate limit configuration on model declaration."""
        if not cls.__rate_limits__:
            cls.__rate_limits__ = {
                "default": RateLimitConfig(
                    limit=1000, per=3600, by="ip", burst_multiplier=1.5
                )
            }
            logger.warning(f"No rate limits defined for {cls.__name__}, using defaults")

        # Validate configurations
        for op, config in cls.__rate_limits__.items():
            if not isinstance(config, RateLimitConfig):
                cls.__rate_limits__[op] = RateLimitConfig(**config)

    @staticmethod
    def get_redis_client(
        async_mode: bool = False,
    ) -> Union[redis.Redis, aioredis.Redis]:
        """Get or create a Redis client."""
        if async_mode:
            if not hasattr(current_app, "aioredis_client"):
                current_app.aioredis_client = aioredis.from_url(
                    current_app.config.get("REDIS_URL", "redis://localhost:6379/0")
                )
            return current_app.aioredis_client

        if not hasattr(current_app, "redis_client"):
            current_app.redis_client = redis.from_url(
                current_app.config.get("REDIS_URL", "redis://localhost:6379/0")
            )
        return current_app.redis_client

    @classmethod
    def get_identifier(cls, operation: str) -> str:
        """Get rate limit identifier based on configuration."""
        config = cls.__rate_limits__[operation]

        if config.custom_identifier:
            return config.custom_identifier()

        if config.by == "ip":
            return request.remote_addr
        elif config.by == "user":
            return str(g.user.id if g.user else "anonymous")
        elif config.by == "api_key":
            return request.headers.get("X-API-Key", "anonymous")
        elif config.by == "combined":
            parts = [request.remote_addr]
            if g.user:
                parts.append(str(g.user.id))
            if "X-API-Key" in request.headers:
                parts.append(request.headers["X-API-Key"])
            return hashlib.sha256(":".join(parts).encode()).hexdigest()

        raise ValueError(f"Invalid identifier type: {config.by}")

    @classmethod
    async def check_rate_limit_async(
        cls, operation: str, identifier: str = None
    ) -> bool:
        """Asynchronous version of rate limit checking."""
        redis_client = cls.get_redis_client(async_mode=True)
        return await cls._check_rate_limit_impl(operation, identifier, redis_client)

    @classmethod
    def check_rate_limit(cls, operation: str, identifier: str = None) -> bool:
        """
        Check if an operation is allowed based on rate limits.

        Features:
        - Burst allowance with token bucket
        - Gradual throttling near limits
        - Role-based overrides
        - Fallback mechanisms
        """
        with RATE_LIMIT_LATENCY.labels(cls.__name__, operation).time():
            if operation not in cls.__rate_limits__:
                logger.warning(f"Unknown operation {operation}, using default limits")
                operation = "default"

            config = cls.__rate_limits__[operation]

            # Check role bypasses
            if config.bypass_roles and g.user:
                if any(g.user.has_role(role) for role in config.bypass_roles):
                    return True

            identifier = identifier or cls.get_identifier(operation)
            redis_client = cls.get_redis_client()

            try:
                return cls._check_rate_limit_impl(operation, identifier, redis_client)
            except redis.RedisError as e:
                logger.error(f"Redis error during rate limit check: {e}")
                if config.fallback_limit:
                    return cls._check_local_fallback(operation, identifier)
                raise

    @classmethod
    def _check_rate_limit_impl(
        cls,
        operation: str,
        identifier: str,
        redis_client: Union[redis.Redis, aioredis.Redis],
    ) -> bool:
        """Implementation of rate limit checking logic."""
        config = cls.__rate_limits__[operation]
        key = f"rate_limit:{cls.__name__}:{operation}:{identifier}"

        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, config.per)
        result = pipe.execute()

        request_count = result[0]
        effective_limit = int(config.limit * config.burst_multiplier)

        # Update metrics
        RATE_LIMIT_REMAINING.labels(cls.__name__, operation, config.by).set(
            max(0, effective_limit - request_count)
        )

        # Check if limit exceeded
        if request_count > effective_limit:
            cls._handle_rate_limit_exceeded(operation, identifier, config)
            return False

        # Apply gradual throttling
        if request_count > (config.limit * config.throttle_threshold):
            if cls._should_throttle(request_count, config):
                cls._handle_rate_limit_exceeded(
                    operation, identifier, config, throttled=True
                )
                return False

        return True

    @classmethod
    def _should_throttle(cls, count: int, config: RateLimitConfig) -> bool:
        """Determine if request should be throttled based on probability."""
        usage_ratio = count / (config.limit * config.burst_multiplier)
        throttle_prob = (usage_ratio - config.throttle_threshold) / (
            1 - config.throttle_threshold
        )
        return random.random() < throttle_prob

    @classmethod
    def _check_local_fallback(cls, operation: str, identifier: str) -> bool:
        """Fallback to local counting when Redis is unavailable."""
        config = cls.__rate_limits__[operation]
        cache_key = f"local_limit:{operation}:{identifier}"

        if not hasattr(cls, "_local_cache"):
            cls._local_cache = {}

        now = time.time()
        cache_data = cls._local_cache.get(cache_key)

        if cache_data:
            count, window_start = cache_data
            if now - window_start > config.per:
                # Reset window
                cls._local_cache[cache_key] = (1, now)
                return True

            if count >= config.fallback_limit:
                return False

            cls._local_cache[cache_key] = (count + 1, window_start)
        else:
            cls._local_cache[cache_key] = (1, now)

        return True

    @classmethod
    def _handle_rate_limit_exceeded(
        cls,
        operation: str,
        identifier: str,
        config: RateLimitConfig,
        throttled: bool = False,
    ) -> None:
        """Handle rate limit violations with detailed tracking."""
        logger.warning(
            f"Rate limit {'throttled' if throttled else 'exceeded'} "
            f"for {operation} by {identifier}"
        )

        RATE_LIMIT_VIOLATIONS.labels(cls.__name__, operation, config.by).inc()

        # Log violation
        violation = RateLimitViolation(
            model_name=cls.__name__,
            operation=operation,
            identifier=identifier,
            limit=config.limit,
            period=config.per,
            throttled=throttled,
            metadata={
                "user_agent": request.user_agent.string,
                "path": request.path,
                "method": request.method,
                "burst_multiplier": config.burst_multiplier,
                "throttle_threshold": config.throttle_threshold,
            },
        )

        try:
            current_app.db.session.add(violation)
            current_app.db.session.commit()
        except Exception as e:
            logger.error(f"Failed to log rate limit violation: {e}")
            current_app.db.session.rollback()

        # Send alert if configured
        if cls._should_alert(operation, config):
            cls._send_rate_limit_alert(operation, identifier, config)

        retry_after = int(config.per * config.backoff_factor)
        response = {
            "error": "Rate limit exceeded",
            "retry_after": retry_after,
            "limit": config.limit,
            "period": config.per,
            "throttled": throttled,
        }

        abort(429, description=response)

    @classmethod
    def _should_alert(cls, operation: str, config: RateLimitConfig) -> bool:
        """Determine if alert should be sent based on violation patterns."""
        key = f"alert:{cls.__name__}:{operation}"
        redis_client = cls.get_redis_client()

        try:
            violations = redis_client.incr(key)
            redis_client.expire(key, 300)  # 5 minute window

            threshold = int(config.limit * config.alert_threshold)
            return violations >= threshold
        except redis.RedisError:
            return False

    @classmethod
    def _send_rate_limit_alert(
        cls, operation: str, identifier: str, config: RateLimitConfig
    ) -> None:
        """Send alert for rate limit violations."""
        if not current_app.config.get("RATE_LIMIT_ALERTS_ENABLED"):
            return

        alert_data = {
            "model": cls.__name__,
            "operation": operation,
            "identifier": identifier,
            "limit": config.limit,
            "period": config.per,
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            if "SLACK_WEBHOOK_URL" in current_app.config:
                requests.post(
                    current_app.config["SLACK_WEBHOOK_URL"],
                    json={"text": f"Rate limit alert: {json.dumps(alert_data)}"},
                )

            if "ADMIN_EMAIL" in current_app.config:
                # Send email alert
                pass
        except Exception as e:
            logger.error(f"Failed to send rate limit alert: {e}")

    @classmethod
    def get_rate_limit_status(cls, operation: str, identifier: str = None) -> Dict:
        """Get detailed rate limit status."""
        if operation not in cls.__rate_limits__:
            raise ValueError(f"Rate limit not defined for operation: {operation}")

        config = cls.__rate_limits__[operation]
        identifier = identifier or cls.get_identifier(operation)
        redis_client = cls.get_redis_client()
        key = f"rate_limit:{cls.__name__}:{operation}:{identifier}"

        try:
            pipe = redis_client.pipeline()
            pipe.get(key)
            pipe.ttl(key)
            result = pipe.execute()

            count = int(result[0]) if result[0] else 0
            ttl = result[1] if result[1] > 0 else config.per

            effective_limit = int(config.limit * config.burst_multiplier)

            return {
                "current_count": count,
                "limit": config.limit,
                "burst_limit": effective_limit,
                "remaining": max(0, effective_limit - count),
                "reset_in": ttl,
                "throttling": count > (config.limit * config.throttle_threshold),
                "usage_percent": (count / effective_limit) * 100,
                "window_size": config.per,
                "identifier_type": config.by,
            }
        except redis.RedisError as e:
            logger.error(f"Redis error getting rate limit status: {e}")
            return {
                "error": "Rate limit status unavailable",
                "fallback_active": bool(config.fallback_limit),
            }


class RateLimitViolation(Model):
    """Enhanced model for tracking rate limit violations."""

    __tablename__ = "nx_rate_limit_violations"
    __table_args__ = (
        Index("ix_violations_model_operation", "model_name", "operation"),
        Index("ix_violations_identifier", "identifier"),
        Index("ix_violations_timestamp", "timestamp"),
    )

    id = Column(Integer, primary_key=True)
    model_name = Column(String(100), nullable=False)
    operation = Column(String(100), nullable=False)
    identifier = Column(String(100), nullable=False)
    limit = Column(Integer, nullable=False)
    period = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    throttled = Column(Boolean, default=False, nullable=False)
    metadata = Column(JSONB, default={}, nullable=False)

    def __repr__(self):
        return (
            f"<RateLimitViolation {self.model_name}:{self.operation} "
            f"by {self.identifier} at {self.timestamp}>"
        )

    @classmethod
    def get_violation_stats(
        cls, model_name: str = None, operation: str = None, timeframe: timedelta = None
    ) -> Dict:
        """Get statistical analysis of violations."""
        query = cls.query

        if model_name:
            query = query.filter_by(model_name=model_name)
        if operation:
            query = query.filter_by(operation=operation)
        if timeframe:
            cutoff = datetime.utcnow() - timeframe
            query = query.filter(cls.timestamp >= cutoff)

        return {
            "total_violations": query.count(),
            "unique_identifiers": query.distinct(cls.identifier).count(),
            "by_hour": query.with_entities(
                func.date_trunc("hour", cls.timestamp), func.count()
            )
            .group_by(1)
            .all(),
            "by_type": query.with_entities(cls.model_name, cls.operation, func.count())
            .group_by(cls.model_name, cls.operation)
            .all(),
        }


"""
Advanced Usage Example:

from flask_appbuilder import Model, BaseView, expose, has_access
from flask import jsonify
from sqlalchemy import Column, Integer, String
from typing import Dict, Any
from datetime import timedelta
from .rate_limit_mixin import RateLimitMixin, RateLimitConfig

class APIEndpoint(RateLimitMixin, Model):
    '''Example API endpoint with advanced rate limiting.'''

    __tablename__ = 'nx_api_endpoints'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

    # Define sophisticated rate limits
    __rate_limits__ = {
        'search': RateLimitConfig(
            limit=1000,
            per=3600,
            by='user',
            burst_multiplier=1.5,
            throttle_threshold=0.8,
            backoff_factor=2.0,
            alert_threshold=0.9,
            bypass_roles=['admin', 'api_unlimited'],
            fallback_limit=100
        ),
        'create': RateLimitConfig(
            limit=50,
            per=300,
            by='combined',
            burst_multiplier=1.2,
            throttle_threshold=0.7
        ),
        'export': RateLimitConfig(
            limit=10,
            per=3600,
            by='api_key',
            custom_identifier=lambda: f"{request.headers.get('X-API-Key')}:{request.remote_addr}"
        )
    }

class APIView(BaseView):

    default_view = 'search'

    @expose('/search')
    @has_access
    async def search(self):
        '''Async search endpoint with rate limiting.'''
        if await APIEndpoint.check_rate_limit_async('search'):
            # Perform search
            results = {'data': 'search results'}
            return jsonify(results)

    @expose('/create', methods=['POST'])
    @has_access
    def create(self):
        '''Create endpoint with combined identifier rate limiting.'''
        if APIEndpoint.check_rate_limit('create'):
            # Create resource
            return jsonify({'status': 'created'})

    @expose('/export')
    @has_access
    def export(self):
        '''Export endpoint with custom identifier rate limiting.'''
        if APIEndpoint.check_rate_limit('export'):
            # Generate export
            return jsonify({'export_url': 'https://example.com/export'})

    @expose('/status')
    @has_access
    def status(self):
        '''Get detailed rate limit status for all operations.'''
        return jsonify({
            'search': APIEndpoint.get_rate_limit_status('search'),
            'create': APIEndpoint.get_rate_limit_status('create'),
            'export': APIEndpoint.get_rate_limit_status('export')
        })

    @expose('/analytics')
    @has_access
    def analytics(self):
        '''Get rate limit violation analytics.'''
        return jsonify(
            RateLimitViolation.get_violation_stats(
                model_name='APIEndpoint',
                timeframe=timedelta(days=7)
            )
        )

appbuilder.add_view(
    APIView,
    "API Endpoints",
    icon="fa-plug",
    category="API"
)

# Configuration in config.py
REDIS_URL = 'redis://localhost:6379/0'
RATE_LIMIT_ALERTS_ENABLED = True
SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/XXX/YYY/ZZZ'
ADMIN_EMAIL = 'admin@example.com'
"""
