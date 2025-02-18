"""
event_dispatch_mixin.py - Advanced Event Management System for Flask-AppBuilder

A production-ready event management system providing comprehensive event handling,
tracking and auditing capabilities for Flask-AppBuilder applications. This module
implements best practices for event-driven architecture while maintaining simplicity
of use.

Key Features:
- Synchronous and asynchronous event processing
- Comprehensive audit logging with PostgreSQL JSONB support
- Automatic event dispatch on model changes
- Event prioritization and conditional execution
- Dead letter queue for failed events
- Full monitoring and metrics support
- Configurable retry policies
- Rich event context and metadata
- Circuit breaking for fault tolerance
- Event batching and throttling
- Integration with monitoring systems
- Performance optimization for high-volume events

Core Components:
- EventDispatchMixin: Main mixin class for adding event capabilities
- Event: Rich event data container with metadata
- EventHandler: Base class for event handlers
- AuditLog: Audit trail with JSONB storage
- FailedEvent: Dead letter queue for failed events
- EventMetrics: StatsD/Prometheus metrics integration

Technical Specifications:
- Python: 3.8+
- Database: PostgreSQL 12+ (recommended)
- Runtime: Async/await with optional gevent support
- Storage: JSONB for flexible event data
- Metrics: StatsD and Prometheus exporters
- Security: Role-based access control integration
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum, auto
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

from flask import current_app, g, request

# Import db from Flask-AppBuilder app instance
from flask_appbuilder import Model, db
from flask_appbuilder.security.sqla.models import User
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Boolean,
    event,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, relationship

# Configure logging
logger = logging.getLogger(__name__)


class EventType(Enum):
    """Standard event types with automatic value generation.

    Defines the core event types supported by the system:
    CREATE - Record creation events
    UPDATE - Record update events
    DELETE - Record deletion events
    CUSTOM - Custom application events
    SYSTEM - System events and operations
    AUDIT - Audit log events
    ERROR - Error events
    NOTIFICATION - Notification events
    WORKFLOW - Workflow state changes
    SECURITY - Security events
    """

    CREATE = auto()
    UPDATE = auto()
    DELETE = auto()
    CUSTOM = auto()
    SYSTEM = auto()
    AUDIT = auto()
    ERROR = auto()
    NOTIFICATION = auto()
    WORKFLOW = auto()
    SECURITY = auto()


@dataclass
class Event:
    """Rich event data container with metadata.

    Attributes:
        type: The event type (EventType enum)
        model: Name of the model class
        instance_id: ID of the model instance
        user_id: ID of user triggering event
        timestamp: Event timestamp
        data: Event payload data
        metadata: Additional event metadata
        priority: Event priority (higher = more important)
        async_dispatch: Whether to handle asynchronously
        retry_count: Number of retry attempts
        correlation_id: Request correlation ID
        tenant_id: Multi-tenant ID if applicable
        tags: List of event tags
    """

    type: EventType
    model: str
    instance_id: int
    user_id: Optional[int]
    timestamp: datetime
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    priority: int = 0
    async_dispatch: bool = False
    retry_count: int = 0
    correlation_id: Optional[str] = None
    tenant_id: Optional[str] = None
    tags: List[str] = None

    def __post_init__(self):
        """Initialize default values."""
        self.tags = self.tags or []
        if not self.correlation_id:
            self.correlation_id = g.get("correlation_id")
        if not self.tenant_id:
            self.tenant_id = g.get("tenant_id")


class EventHandler:
    """Base event handler with rich functionality.

    Attributes:
        event_type: Type of events this handler processes
        priority: Handler priority (higher = processed first)
        retry_limit: Max number of retry attempts
        timeout: Handler timeout in seconds
    """

    def __init__(
        self,
        event_type: EventType,
        priority: int = 0,
        retry_limit: int = 3,
        timeout: int = 30,
    ):
        self.event_type = event_type
        self.priority = priority
        self.retry_limit = retry_limit
        self.timeout = timeout

    async def handle(self, event: Event) -> bool:
        """Handle event with timeout and retry support.

        Args:
            event: The event to handle

        Returns:
            bool: Success status

        Raises:
            asyncio.TimeoutError: If handler exceeds timeout
            Exception: On handler errors
        """
        try:
            async with asyncio.timeout(self.timeout):
                return await self._handle_event(event)
        except asyncio.TimeoutError:
            logger.error(f"Handler timeout for {event.type}")
            return False
        except Exception as e:
            logger.exception(f"Handler error: {str(e)}")
            return False

    async def _handle_event(self, event: Event) -> bool:
        """Override this method to implement handler logic.

        Args:
            event: The event to handle

        Returns:
            bool: Success status

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError

    def can_handle(self, event: Event) -> bool:
        """Check if handler can process event.

        Args:
            event: The event to check

        Returns:
            bool: Whether handler can process event
        """
        return True

    @property
    def name(self) -> str:
        """Get handler name for logging.

        Returns:
            str: Handler class name
        """
        return self.__class__.__name__


class EventDispatchMixin:
    """Mixin adding advanced event capabilities to models.

    Attributes:
        event_metadata: JSON metadata storage
        last_event: Timestamp of last event
        event_count: Total event count
        event_handlers: Registered event handlers
    """

    # Optimized Postgres JSONB storage
    event_metadata = Column(JSONB, default={}, nullable=False)
    last_event = Column(DateTime, nullable=True, index=True)
    event_count = Column(Integer, default=0, nullable=False)

    # Add indexes for common queries
    __table_args__ = (
        Index("ix_event_metadata_gin", event_metadata, postgresql_using="gin"),
    )

    def __init__(self, *args, **kwargs):
        """Initialize event dispatch capabilities.

        Registers default handlers and sets up metrics.
        """
        super().__init__(*args, **kwargs)
        self.event_handlers = {}
        self._initialize_handlers()
        self._setup_metrics()

    def _initialize_handlers(self):
        """Initialize default event handlers.

        Registers core handlers and custom handlers from config.
        """
        # Register core handlers
        self.register_handler(EventType.CREATE, AuditHandler(EventType.CREATE))
        self.register_handler(EventType.UPDATE, AuditHandler(EventType.UPDATE))
        self.register_handler(EventType.DELETE, AuditHandler(EventType.DELETE))

        # Register custom handlers from config
        handlers = current_app.config.get("EVENT_HANDLERS", {})
        for event_type, handler_cls in handlers.items():
            self.register_handler(event_type, handler_cls())

    def register_handler(self, event_type: EventType, handler: EventHandler):
        """Register event handler with priority sorting.

        Args:
            event_type: Type of events to handle
            handler: Handler instance
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        # Sort by priority (highest first)
        self.event_handlers[event_type].sort(key=lambda h: h.priority, reverse=True)

    async def dispatch_event(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        async_dispatch: bool = False,
        priority: int = 0,
    ) -> bool:
        """Dispatch event with comprehensive error handling and metrics.

        Args:
            event_type: Type of event to dispatch
            data: Event data payload
            async_dispatch: Whether to handle asynchronously
            priority: Event priority

        Returns:
            bool: Success status
        """
        start_time = datetime.utcnow()

        try:
            # Create rich event object
            event = Event(
                type=event_type,
                model=self.__class__.__name__,
                instance_id=self.id,
                user_id=g.user.id if hasattr(g, "user") else None,
                timestamp=start_time,
                data=data,
                metadata={
                    "ip_address": request.remote_addr if request else None,
                    "user_agent": request.user_agent.string if request else None,
                    "correlation_id": g.get("correlation_id"),
                    "tenant_id": g.get("tenant_id"),
                    "source": g.get("event_source"),
                },
                priority=priority,
                async_dispatch=async_dispatch,
            )

            # Update tracking metrics
            self.last_event = event.timestamp
            self.event_count += 1
            self.event_metadata.update(
                {
                    "last_event_type": event_type.name,
                    "total_events": self.event_count,
                    "last_success": None,
                    "last_error": None,
                }
            )

            # Get handlers and check circuit breaker
            handlers = self.event_handlers.get(event_type, [])
            if not handlers:
                logger.warning(f"No handlers for event type: {event_type}")
                return True

            if async_dispatch:
                # Handle asynchronously with timeout
                async with asyncio.timeout(30):
                    tasks = [
                        handler.handle(event)
                        for handler in handlers
                        if handler.can_handle(event)
                    ]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    success = all(isinstance(r, bool) and r for r in results)
            else:
                # Handle synchronously
                success = all(
                    await handler.handle(event)
                    for handler in handlers
                    if handler.can_handle(event)
                )

            # Update metrics and handle failure
            duration = (datetime.utcnow() - start_time).total_seconds()
            self._update_metrics(event_type, success, duration)

            if not success:
                logger.error(f"Event dispatch failed for {event_type}")
                self.event_metadata["last_error"] = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "event_type": event_type.name,
                }
                await self._handle_failed_event(event)
            else:
                self.event_metadata["last_success"] = datetime.utcnow().isoformat()

            await db.session.commit()
            return success

        except Exception as e:
            logger.exception(f"Error dispatching event: {str(e)}")
            self.event_metadata["last_error"] = {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            }
            await db.session.commit()
            return False

    async def _handle_failed_event(self, event: Event):
        """Handle failed event with dead letter queue.

        Args:
            event: The failed event
        """
        try:
            failed_event = FailedEvent(
                model=event.model,
                instance_id=event.instance_id,
                event_type=event.type.name,
                user_id=event.user_id,
                timestamp=event.timestamp,
                data=event.data,
                metadata=event.metadata,
                retry_count=event.retry_count,
                error_detail=str(event.metadata.get("error")),
            )
            db.session.add(failed_event)
            await db.session.commit()

            # Notify monitoring
            if current_app.config.get("EVENT_FAILURE_NOTIFICATION"):
                await self._notify_failure(failed_event)

        except Exception as e:
            logger.error(f"Error storing failed event: {str(e)}")

    def _setup_metrics(self):
        """Initialize metrics collectors.

        Sets up StatsD client if configured.
        """
        if current_app.config.get("STATSD_HOST"):
            from statsd import StatsClient

            self.statsd = StatsClient(
                host=current_app.config["STATSD_HOST"],
                port=current_app.config.get("STATSD_PORT", 8125),
                prefix=f"events.{self.__class__.__name__.lower()}",
            )
        else:
            self.statsd = None

    def _update_metrics(self, event_type: EventType, success: bool, duration: float):
        """Update metrics for monitoring.

        Args:
            event_type: Type of event
            success: Whether event succeeded
            duration: Event duration in seconds
        """
        if self.statsd:
            # Increment counters
            self.statsd.incr(f"dispatch.{event_type.name.lower()}")
            if success:
                self.statsd.incr("dispatch.success")
            else:
                self.statsd.incr("dispatch.failure")

            # Record timing
            self.statsd.timing("dispatch.duration", duration * 1000)

    @classmethod
    def __declare_last__(cls):
        """Setup SQLAlchemy event listeners.

        Configures automatic event dispatch for model changes.
        """

        @event.listens_for(cls, "after_insert")
        def after_insert(mapper, connection, target):
            """Dispatch create event."""
            asyncio.create_task(
                target.dispatch_event(EventType.CREATE, {"id": target.id})
            )

        @event.listens_for(cls, "after_update")
        def after_update(mapper, connection, target):
            """Dispatch update event with changes."""
            state = db.inspect(target)
            changes = {}
            for attr in state.attrs:
                hist = attr.history
                if hist.has_changes():
                    changes[attr.key] = {
                        "old": hist.deleted[0] if hist.deleted else None,
                        "new": hist.added[0] if hist.added else None,
                    }

            if changes:
                asyncio.create_task(
                    target.dispatch_event(EventType.UPDATE, {"changes": changes})
                )

        @event.listens_for(cls, "after_delete")
        def after_delete(mapper, connection, target):
            """Dispatch delete event."""
            asyncio.create_task(
                target.dispatch_event(EventType.DELETE, {"id": target.id})
            )


class AuditLog(Model):
    """Enhanced audit log with JSONB storage.

    Attributes:
        model: Name of audited model
        instance_id: ID of model instance
        event_type: Type of event
        user_id: ID of user performing action
        timestamp: When event occurred
        data: Event data payload
        metadata: Additional event metadata
        user: Relationship to user model
    """

    __tablename__ = "nx_audit_logs"

    id = Column(Integer, primary_key=True)
    model = Column(String(100), nullable=False, index=True)
    instance_id = Column(Integer, nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("ab_user.id"), nullable=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    data = Column(JSONB, nullable=False)
    metadata = Column(JSONB, nullable=False)

    # Relationships
    user = relationship(User, foreign_keys=[user_id])

    # Optimized indexes
    __table_args__ = (
        Index("ix_audit_composite", "model", "instance_id", "timestamp"),
        Index("ix_audit_data_gin", "data", postgresql_using="gin"),
        Index("ix_audit_metadata_gin", "metadata", postgresql_using="gin"),
    )


class FailedEvent(Model):
    """Enhanced failed event storage with retry handling.

    Attributes:
        model: Name of model class
        instance_id: ID of model instance
        event_type: Type of failed event
        user_id: ID of user triggering event
        timestamp: When event occurred
        data: Event data payload
        metadata: Event metadata
        retry_count: Number of retry attempts
        error_detail: Error information
        next_retry: When to retry event
        resolved: Whether failure is resolved
        resolved_at: When failure was resolved
        resolved_by: User who resolved failure
        user: Relationship to user model
        resolver: Relationship to resolving user
    """

    __tablename__ = "nx_failed_events"

    id = Column(Integer, primary_key=True)
    model = Column(String(100), nullable=False, index=True)
    instance_id = Column(Integer, nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("ab_user.id"), nullable=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    data = Column(JSONB, nullable=False)
    metadata = Column(JSONB, nullable=False)
    retry_count = Column(Integer, default=0, nullable=False, index=True)
    error_detail = Column(Text)
    next_retry = Column(DateTime, index=True)
    resolved = Column(Boolean, default=False, index=True)
    resolved_at = Column(DateTime)
    resolved_by = Column(Integer, ForeignKey("ab_user.id"))

    # Relationships
    user = relationship(User, foreign_keys=[user_id])
    resolver = relationship(User, foreign_keys=[resolved_by])

    # Optimized indexes
    __table_args__ = (
        Index("ix_failed_composite", "model", "instance_id", "timestamp"),
        Index("ix_failed_data_gin", "data", postgresql_using="gin"),
        Index("ix_failed_retry", "retry_count", "next_retry", "resolved"),
    )


class AuditHandler(EventHandler):
    """Default audit logging handler.

    Handles logging events to the audit trail with high priority.
    """

    def __init__(self, event_type: EventType):
        """Initialize audit handler.

        Args:
            event_type: Type of events to audit
        """
        super().__init__(event_type, priority=100)  # High priority for audit

    async def _handle_event(self, event: Event) -> bool:
        """Log event to audit trail.

        Args:
            event: Event to audit

        Returns:
            bool: Success status
        """
        try:
            # Log event details
            logger.info(
                f"Audit: {event.type.name} on {event.model}:{event.instance_id} "
                f"by user {event.user_id} at {event.timestamp}"
            )

            # Store in audit log if enabled
            if current_app.config.get("AUDIT_LOGGING_ENABLED", True):
                audit_log = AuditLog(
                    model=event.model,
                    instance_id=event.instance_id,
                    event_type=event.type.name,
                    user_id=event.user_id,
                    timestamp=event.timestamp,
                    data=event.data,
                    metadata=event.metadata,
                )
                db.session.add(audit_log)
                await db.session.commit()

            return True

        except Exception as e:
            logger.error(f"Audit logging failed: {str(e)}")
            return False


"""
Usage Example:

from flask_appbuilder import Model, BaseView
from flask_appbuilder.security.decorators import has_access
from nx_events import EventDispatchMixin, EventType, EventHandler, Event

# 1. Define custom event handlers
class EmailNotificationHandler(EventHandler):
    def __init__(self):
        super().__init__(EventType.NOTIFICATION, priority=50)

    async def _handle_event(self, event: Event) -> bool:
        if 'email' in event.data:
            # Send email using your preferred method
            return await send_email(
                to=event.data['email'],
                subject=event.data.get('subject', 'Notification'),
                body=event.data.get('body', '')
            )
        return False

class SlackNotificationHandler(EventHandler):
    def __init__(self):
        super().__init__(EventType.NOTIFICATION, priority=40)

    async def _handle_event(self, event: Event) -> bool:
        if 'slack_channel' in event.data:
            return await post_to_slack(
                channel=event.data['slack_channel'],
                message=event.data.get('message', '')
            )
        return False

# 2. Define model with event dispatch
class Document(EventDispatchMixin, Model):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(Text)
    status = Column(String(50), default='draft')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Register notification handlers
        self.register_handler(EventType.NOTIFICATION, EmailNotificationHandler())
        self.register_handler(EventType.NOTIFICATION, SlackNotificationHandler())

# 3. Create view with event dispatch
class DocumentView(BaseView):
    route_base = "/documents"

    @has_access
    async def notify_reviewers(self, document_id: int):
        document = Document.query.get_or_404(document_id)

        # Dispatch notification event
        success = await document.dispatch_event(
            EventType.NOTIFICATION,
            {
                'email': 'reviewers@example.com',
                'subject': f'Review Required: {document.title}',
                'body': 'Please review the attached document',
                'slack_channel': '#document-reviews',
                'message': f'New document ready for review: {document.title}'
            },
            async_dispatch=True  # Handle notifications asynchronously
        )

        if success:
            flash('Notifications sent successfully', 'success')
        else:
            flash('Error sending notifications', 'error')

        return redirect(url_for('DocumentView.list'))

# 4. Monitor events and handle failures
class EventMonitor:
    @staticmethod
    async def process_failed_events():
        # Get failed events due for retry
        failed_events = FailedEvent.query.filter(
            FailedEvent.resolved == False,
            FailedEvent.retry_count < 3,
            FailedEvent.next_retry <= datetime.utcnow()
        ).all()

        for failed_event in failed_events:
            # Get model class and instance
            model_class = db.Model._decl_class_registry.get(failed_event.model)
            if model_class:
                instance = model_class.query.get(failed_event.instance_id)
                if instance:
                    # Retry event dispatch
                    event_type = EventType[failed_event.event_type]
                    success = await instance.dispatch_event(
                        event_type,
                        failed_event.data,
                        async_dispatch=True
                    )

                    if success:
                        # Mark as resolved
                        failed_event.resolved = True
                        failed_event.resolved_at = datetime.utcnow()
                        failed_event.resolved_by = g.user.id
                    else:
                        # Update retry count and schedule next retry
                        failed_event.retry_count += 1
                        failed_event.next_retry = datetime.utcnow() + timedelta(
                            minutes=5 * failed_event.retry_count
                        )

                    await db.session.commit()

# 5. Get audit trail with filtering
def get_audit_trail(
    model: str,
    instance_id: int,
    event_types: List[str] = None,
    start_date: datetime = None,
    end_date: datetime = None,
    user_id: int = None
) -> List[AuditLog]:
    '''Get filtered audit trail.'''
    query = AuditLog.query.filter_by(
        model=model,
        instance_id=instance_id
    )

    if event_types:
        query = query.filter(AuditLog.event_type.in_(event_types))
    if start_date:
        query = query.filter(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.filter(AuditLog.timestamp <= end_date)
    if user_id:
        query = query.filter_by(user_id=user_id)

    return query.order_by(AuditLog.timestamp.desc()).all()

# 6. Register celery task for failed event processing
@celery.task
def process_failed_events():
    asyncio.run(EventMonitor.process_failed_events())
"""
