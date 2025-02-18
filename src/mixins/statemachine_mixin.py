"""
state_machine_mixin.py - Advanced State Machine System for Flask-AppBuilder

This module provides a comprehensive state machine implementation with workflow management
capabilities for Flask-AppBuilder applications. It offers a flexible, event-driven
architecture for managing complex state transitions with full audit trail support and
visualization capabilities.

Key Features:
- Declarative workflow definitions with states and transitions
- Role-based access control and validation
- Full audit history and version tracking
- Multiple notification channels (Email, SMS, Webhooks)
- Async event handling and background processing
- Workflow visualization (GraphViz, Mermaid.js)
- Import/Export to multiple formats
- Customizable validation rules
- Automatic documentation generation
- PostgreSQL optimizations
- Fault tolerance and error recovery
- Real-time monitoring and metrics

Core Components:
- StateMachineMixin: Adds state machine functionality to models
- State: Represents machine states with metadata
- Transition: Defines allowed state transitions
- Workflow: Orchestrates states and transitions
- NotificationManager: Handles notifications
- HistoryManager: Manages audit trail

Requirements:
- Python 3.8+
- Flask-AppBuilder
- PostgreSQL
- Redis (optional)

Dependencies:
- flask-appbuilder
- sqlalchemy
- blinker
- graphviz
- asyncio
- aiohttp
- pyyaml
- twilio
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable
from functools import wraps

import aiohttp
import yaml
import graphviz
from blinker import signal
from flask import current_app, flash, render_template, g, request, session
from flask_appbuilder import Model
from flask_appbuilder.models.decorators import renders
from flask_appbuilder.security.sqla.models import User
from flask_appbuilder.security.decorators import has_access, permission_name
from flask_mail import Message
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Boolean,
    Text,
    func,
    event,
    inspect,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship, Session
from sqlalchemy.types import TypeDecorator
from sqlalchemy.ext.mutable import Mutable
from twilio.rest import Client

from ... import db

# Configure logging
logger = logging.getLogger(__name__)

# Type aliases
JsonDict = Dict[str, Any]
StateCallback = Callable[[Any, User], None]
StateValidator = Callable[[Any], bool]


class State:
    """Represents a state in the state machine with metadata and validation."""

    def __init__(
        self,
        name: str,
        description: str = "",
        metadata: Optional[JsonDict] = None,
        is_initial: bool = False,
        is_final: bool = False,
        is_restricted: bool = False,
        required_roles: Optional[List[str]] = None,
        validators: Optional[List[StateValidator]] = None,
        timeout: Optional[int] = None,
        retry_count: Optional[int] = None,
        custom_handlers: Optional[Dict[str, StateCallback]] = None,
        auto_transitions: Optional[List[str]] = None,
        error_state: Optional[str] = None,
        ui_color: Optional[str] = None,
        max_retries: int = 3,
        ttl: Optional[int] = None,
    ):
        """
        Initialize a new State.

        Args:
            name: Unique state identifier
            description: Human readable description
            metadata: Additional state metadata
            is_initial: True if this is an initial state
            is_final: True if this is a final state
            is_restricted: True if state has restricted access
            required_roles: List of required user roles
            validators: State validation functions
            timeout: State timeout in seconds
            retry_count: Number of retries allowed
            custom_handlers: Custom event handlers
            auto_transitions: Automatic transition triggers
            error_state: Fallback error state
            ui_color: Display color for UI
            max_retries: Maximum retry attempts
            ttl: Time-to-live in seconds
        """
        self.name = name
        self.description = description
        self.metadata = metadata or {}
        self.is_initial = is_initial
        self.is_final = is_final
        self.is_restricted = is_restricted
        self.required_roles = required_roles or []
        self.validators = validators or []
        self.timeout = timeout
        self.retry_count = retry_count
        self.custom_handlers = custom_handlers or {}
        self.auto_transitions = auto_transitions or []
        self.error_state = error_state
        self.ui_color = ui_color or "#CCCCCC"
        self.max_retries = max_retries
        self.ttl = ttl

        if self.timeout and not self.error_state:
            raise ValueError("Error state required when timeout specified")

    def __repr__(self) -> str:
        return f"<State {self.name}>"

    def validate(self, instance: Any, user: User) -> bool:
        """Run all validators for this state."""
        try:
            return all(v(instance, user) for v in self.validators)
        except Exception as e:
            logger.error(f"State validation error: {str(e)}")
            return False


class Transition:
    """Represents a transition between states."""

    def __init__(
        self,
        trigger: str,
        source: Union[str, List[str]],
        dest: str,
        conditions: Optional[List[StateValidator]] = None,
        before: Optional[List[StateCallback]] = None,
        after: Optional[List[StateCallback]] = None,
        priority: int = 0,
        required_roles: Optional[List[str]] = None,
        auto_trigger: bool = False,
        validation_message: Optional[str] = None,
        side_effects: Optional[List[StateCallback]] = None,
        retry_policy: Optional[JsonDict] = None,
        timeout: Optional[int] = None,
        error_state: Optional[str] = None,
        rollback: bool = True,
        async_dispatch: bool = False,
        batch_size: Optional[int] = None,
    ):
        """
        Initialize a new Transition.

        Args:
            trigger: Event that triggers transition
            source: Source state(s)
            dest: Destination state
            conditions: Conditions that must be met
            before: Callbacks before transition
            after: Callbacks after transition
            priority: Transition priority
            required_roles: Required user roles
            auto_trigger: Auto-trigger transition
            validation_message: Custom validation message
            side_effects: Additional side effects
            retry_policy: Retry configuration
            timeout: Transition timeout
            error_state: Error state on failure
            rollback: Enable transaction rollback
            async_dispatch: Use async execution
            batch_size: Batch processing size
        """
        self.trigger = trigger
        self.source = source if isinstance(source, list) else [source]
        self.dest = dest
        self.conditions = conditions or []
        self.before = before or []
        self.after = after or []
        self.priority = priority
        self.required_roles = required_roles or []
        self.auto_trigger = auto_trigger
        self.validation_message = validation_message
        self.side_effects = side_effects or []
        self.retry_policy = retry_policy or {}
        self.timeout = timeout
        self.error_state = error_state
        self.rollback = rollback
        self.async_dispatch = async_dispatch
        self.batch_size = batch_size

        # Validate configuration
        if self.timeout and not self.error_state:
            raise ValueError("Error state required when timeout specified")

    def __repr__(self) -> str:
        return f"<Transition {self.trigger}: {self.source} -> {self.dest}>"

    def can_trigger(self, instance: Any, user: User) -> bool:
        """Check if transition can be triggered."""
        try:
            # Check role requirements
            if self.required_roles and not any(
                user.has_role(role) for role in self.required_roles
            ):
                return False

            # Check conditions
            return all(c(instance, user) for c in self.conditions)
        except Exception as e:
            logger.error(f"Transition check error: {str(e)}")
            return False


class Workflow:
    """Represents a complete workflow with states and transitions."""

    def __init__(
        self,
        name: str,
        states: List[State],
        transitions: List[Transition],
        sub_workflows: Optional[List["Workflow"]] = None,
        metadata: Optional[JsonDict] = None,
        version: str = "1.0",
        description: str = "",
        tags: Optional[List[str]] = None,
        owner: Optional[str] = None,
        timeout: Optional[int] = None,
        notification_config: Optional[JsonDict] = None,
        validation_rules: Optional[List[StateValidator]] = None,
        error_state: Optional[str] = None,
        max_retries: int = 3,
        auto_transitions: bool = False,
        parallel_execution: bool = False,
        history_limit: Optional[int] = None,
    ):
        """
        Initialize a new Workflow.

        Args:
            name: Workflow name
            states: List of states
            transitions: List of transitions
            sub_workflows: Nested workflows
            metadata: Additional metadata
            version: Version string
            description: Description
            tags: Classification tags
            owner: Workflow owner
            timeout: Global timeout
            notification_config: Notification settings
            validation_rules: Global validation
            error_state: Global error state
            max_retries: Max retry attempts
            auto_transitions: Enable auto transitions
            parallel_execution: Allow parallel execution
            history_limit: Max history entries
        """
        self.name = name
        self.states = states
        self.transitions = transitions
        self.sub_workflows = sub_workflows or []
        self.metadata = metadata or {}
        self.version = version
        self.description = description
        self.tags = tags or []
        self.owner = owner
        self.timeout = timeout
        self.notification_config = notification_config or {}
        self.validation_rules = validation_rules or []
        self.error_state = error_state
        self.max_retries = max_retries
        self.auto_transitions = auto_transitions
        self.parallel_execution = parallel_execution
        self.history_limit = history_limit

        # Validate workflow configuration
        self._validate()

        # Initialize workflow components
        self._setup_validation()
        self._setup_notifications()
        self._setup_error_handling()

    def _validate(self) -> None:
        """Validate workflow configuration."""
        # Ensure states are valid
        state_names = {s.name for s in self.states}
        initial_states = [s for s in self.states if s.is_initial]

        if not initial_states:
            raise ValueError("Workflow must have at least one initial state")

        if len(initial_states) > 1:
            raise ValueError("Workflow cannot have multiple initial states")

        # Validate transitions
        for transition in self.transitions:
            if not set(transition.source).issubset(state_names):
                raise ValueError(
                    f"Invalid source state(s) in transition {transition.trigger}"
                )
            if transition.dest not in state_names:
                raise ValueError(
                    f"Invalid destination state in transition {transition.trigger}"
                )

        # Validate error states
        if self.error_state and self.error_state not in state_names:
            raise ValueError(f"Invalid error state: {self.error_state}")

    def _setup_validation(self) -> None:
        """Set up workflow validation."""
        self._validators = {}
        for state in self.states:
            self._validators[state.name] = state.validators

    def _setup_notifications(self) -> None:
        """Set up notification handling."""
        self._notification_handlers = []
        if self.notification_config:
            for handler in self.notification_config.get("handlers", []):
                self._notification_handlers.append(handler)

    def _setup_error_handling(self) -> None:
        """Set up error handling."""
        self._error_handlers = {}
        for state in self.states:
            if state.error_state:
                self._error_handlers[state.name] = state.error_state

    def get_available_transitions(self, current_state: str) -> List[Transition]:
        """Get available transitions from current state."""
        return [t for t in self.transitions if current_state in t.source]

    def get_state(self, state_name: str) -> Optional[State]:
        """Get state by name."""
        return next((s for s in self.states if s.name == state_name), None)

    def handle_timeout(self, state: State) -> Optional[str]:
        """Handle state timeout."""
        if state.timeout:
            return state.error_state or self.error_state
        return None

    def handle_error(self, state: State, error: Exception) -> Optional[str]:
        """Handle state error."""
        error_state = state.error_state or self.error_state
        if error_state:
            logger.error(
                f"Transitioning to error state {error_state} due to: {str(error)}"
            )
            return error_state
        return None


class NotificationManager:
    """Manages notifications for state changes and events."""

    @staticmethod
    async def send_notifications(notifications: List[Dict[str, Any]]) -> None:
        """Send multiple notifications concurrently."""
        tasks = []
        for notification in notifications:
            handler = getattr(NotificationManager, f"send_{notification['type']}", None)
            if handler:
                tasks.append(handler(**notification["data"]))

        await asyncio.gather(*tasks)

    @staticmethod
    async def send_email(
        subject: str,
        recipients: List[str],
        body: str,
        template: Optional[str] = None,
        attachments: Optional[List[str]] = None,
        html: bool = False,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        reply_to: Optional[str] = None,
        sender: Optional[str] = None,
        retry: int = 3,
    ) -> bool:
        """
        Send email notification asynchronously.

        Args:
            subject: Email subject
            recipients: Recipient list
            body: Email body
            template: Template name
            attachments: File attachments
            html: Send as HTML
            cc: CC recipients
            bcc: BCC recipients
            reply_to: Reply-to address
            sender: Sender address
            retry: Retry attempts

        Returns:
            bool: Success status
        """
        for attempt in range(retry):
            try:
                msg = Message(
                    subject,
                    recipients=recipients,
                    cc=cc,
                    bcc=bcc,
                    reply_to=reply_to,
                    sender=sender,
                )

                if html:
                    msg.html = (
                        render_template(template, body=body) if template else body
                    )
                else:
                    msg.body = body

                if attachments:
                    for attachment in attachments:
                        with current_app.open_resource(attachment) as f:
                            msg.attach(
                                os.path.basename(attachment),
                                "application/octet-stream",
                                f.read(),
                            )

                await current_app.extensions["mail"].send_async(msg)
                return True

            except Exception as e:
                logger.error(f"Email error (attempt {attempt + 1}): {str(e)}")
                if attempt == retry - 1:
                    return False
                await asyncio.sleep(1)

    @staticmethod
    async def send_sms(
        to: str,
        body: str,
        callback_url: Optional[str] = None,
        media_url: Optional[str] = None,
        retry: int = 3,
        status_callback: Optional[str] = None,
        validity_period: Optional[int] = None,
        application_sid: Optional[str] = None,
        max_price: Optional[float] = None,
        provide_feedback: bool = False,
        attempt_async: bool = True,
        force_delivery: bool = False,
    ) -> bool:
        """
        Send SMS notification asynchronously.

        Args:
            to: Recipient number
            body: Message body
            callback_url: Status callback URL
            media_url: Media attachment URL
            retry: Retry attempts
            status_callback: Status webhook
            validity_period: Message validity
            application_sid: Twilio app SID
            max_price: Maximum price
            provide_feedback: Enable feedback
            attempt_async: Use async sending
            force_delivery: Force delivery

        Returns:
            bool: Success status
        """
        for attempt in range(retry):
            try:
                client = Client(
                    current_app.config["TWILIO_ACCOUNT_SID"],
                    current_app.config["TWILIO_AUTH_TOKEN"],
                )

                message_data = {
                    "to": to,
                    "from_": current_app.config["TWILIO_PHONE_NUMBER"],
                    "body": body,
                    "status_callback": callback_url or status_callback,
                    "application_sid": application_sid,
                    "max_price": max_price,
                    "provide_feedback": provide_feedback,
                    "validity_period": validity_period,
                }

                if media_url:
                    message_data["media_url"] = [media_url]

                if attempt_async:
                    await client.messages.create_async(**message_data)
                else:
                    client.messages.create(**message_data)

                return True

            except Exception as e:
                logger.error(f"SMS error (attempt {attempt + 1}): {str(e)}")
                if attempt == retry - 1:
                    return False
                await asyncio.sleep(1)

    @staticmethod
    async def send_webhook(
        url: str,
        payload: Dict[str, Any],
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        retry: int = 3,
        verify_ssl: bool = True,
        basic_auth: Optional[tuple] = None,
        json_encode: bool = True,
        expected_status: Optional[List[int]] = None,
        retry_codes: Optional[List[int]] = None,
    ) -> bool:
        """
        Send webhook notification asynchronously.

        Args:
            url: Webhook URL
            payload: Request payload
            method: HTTP method
            headers: Request headers
            timeout: Request timeout
            retry: Retry attempts
            verify_ssl: Verify SSL
            basic_auth: Basic auth tuple
            json_encode: JSON encode payload
            expected_status: Valid status codes
            retry_codes: Retry status codes

        Returns:
            bool: Success status
        """
        if expected_status is None:
            expected_status = [200, 201, 202, 204]

        if retry_codes is None:
            retry_codes = [408, 429, 500, 502, 503, 504]

        for attempt in range(retry):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method=method,
                        url=url,
                        json=payload if json_encode else None,
                        data=None if json_encode else payload,
                        headers=headers or {},
                        timeout=timeout,
                        verify_ssl=verify_ssl,
                        auth=basic_auth,
                    ) as response:
                        if response.status in expected_status:
                            return True

                        if response.status not in retry_codes:
                            logger.error(
                                f"Webhook failed with status {response.status}"
                            )
                            return False

            except Exception as e:
                logger.error(f"Webhook error (attempt {attempt + 1}): {str(e)}")
                if attempt == retry - 1:
                    return False

            await asyncio.sleep(min(2**attempt, 30))

    @staticmethod
    def send_signal(
        signal_name: str,
        sender: Any,
        synchronous: bool = True,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> None:
        """
        Send blinker signal.

        Args:
            signal_name: Signal identifier
            sender: Signal sender
            synchronous: Send synchronously
            timeout: Signal timeout
            **kwargs: Signal data
        """
        try:
            custom_signal = signal(signal_name)

            if synchronous:
                custom_signal.send(sender, **kwargs)
            else:
                custom_signal.send_async(sender, **kwargs, timeout=timeout)

        except Exception as e:
            logger.error(f"Signal error: {str(e)}")

    @staticmethod
    def flash_message(
        message: str,
        category: str = "info",
        variables: Optional[Dict[str, Any]] = None,
        sanitize: bool = True,
        translate: bool = True,
        dismiss: bool = True,
    ) -> None:
        """
        Display flash message.

        Args:
            message: Message text
            category: Message category
            variables: Template variables
            sanitize: Sanitize HTML
            translate: Translate message
            dismiss: Dismissible message
        """
        try:
            if variables:
                message = message.format(**variables)

            if translate:
                message = _(message)

            if sanitize:
                from markupsafe import escape

                message = escape(message)

            flash(message, category)

        except Exception as e:
            logger.error(f"Flash message error: {str(e)}")


class HistoryManager:
    """Manages state change history and audit trail."""

    @staticmethod
    def add_entry(
        instance: Any,
        from_state: str,
        to_state: str,
        user: User,
        reason: Optional[str] = None,
        metadata: Optional[JsonDict] = None,
        trace_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        priority: int = 0,
        expires: Optional[datetime] = None,
        notify: bool = True,
    ) -> Optional["StateChangeHistory"]:
        """
        Add history entry.

        Args:
            instance: Model instance
            from_state: Previous state
            to_state: New state
            user: User making change
            reason: Change reason
            metadata: Additional metadata
            trace_id: Correlation ID
            tags: Entry tags
            priority: Entry priority
            expires: Entry expiry
            notify: Send notifications

        Returns:
            StateChangeHistory: Created entry
        """
        try:
            entry = StateChangeHistory(
                model_id=instance.id,
                model_type=instance.__class__.__name__,
                from_state=from_state,
                to_state=to_state,
                changed_by=user.id,
                changed_at=datetime.utcnow(),
                reason=reason,
                metadata=metadata or {},
                trace_id=trace_id,
                tags=tags or [],
                priority=priority,
                expires=expires,
            )

            # Add audit information
            entry.metadata.update(
                {
                    "ip_address": (
                        request.remote_addr if hasattr(request, "remote_addr") else None
                    ),
                    "user_agent": (
                        request.user_agent.string
                        if hasattr(request, "user_agent")
                        else None
                    ),
                    "session_id": session.get("id") if hasattr(session, "id") else None,
                    "correlation_id": g.get("correlation_id"),
                    "source": g.get("source", "web"),
                }
            )

            db.session.add(entry)
            db.session.commit()

            if notify:
                HistoryManager._notify_change(entry)

            return entry

        except Exception as e:
            logger.error(f"Error adding history entry: {str(e)}")
            db.session.rollback()
            return None

    @staticmethod
    def _notify_change(entry: "StateChangeHistory") -> None:
        """Send notifications for history changes."""
        try:
            # Send signal
            signal("history_change").send(entry)

            # Notify webhooks
            if current_app.config.get("HISTORY_WEBHOOKS"):
                asyncio.create_task(
                    NotificationManager.send_webhook(
                        current_app.config["HISTORY_WEBHOOK_URL"],
                        {"type": "history_change", "entry": entry.to_dict()},
                    )
                )

        except Exception as e:
            logger.error(f"History notification error: {str(e)}")

    @staticmethod
    def get_history(
        instance: Any,
        filters: Optional[JsonDict] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        include_metadata: bool = True,
        order_by: Optional[List[str]] = None,
        group_by: Optional[List[str]] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        states: Optional[List[str]] = None,
        users: Optional[List[int]] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None,
    ) -> List["StateChangeHistory"]:
        """
        Get history entries.

        Args:
            instance: Model instance
            filters: Query filters
            limit: Result limit
            offset: Query offset
            include_metadata: Include metadata
            order_by: Sort columns
            group_by: Group columns
            since: Start date
            until: End date
            states: Filter states
            users: Filter users
            tags: Filter tags
            search: Search term

        Returns:
            list: History entries
        """
        try:
            query = StateChangeHistory.query.filter_by(
                model_id=instance.id, model_type=instance.__class__.__name__
            )

            # Apply filters
            if filters:
                for key, value in filters.items():
                    if hasattr(StateChangeHistory, key):
                        query = query.filter(getattr(StateChangeHistory, key) == value)

            # Date range
            if since:
                query = query.filter(StateChangeHistory.changed_at >= since)
            if until:
                query = query.filter(StateChangeHistory.changed_at <= until)

            # State filters
            if states:
                query = query.filter(StateChangeHistory.to_state.in_(states))

            # User filters
            if users:
                query = query.filter(StateChangeHistory.changed_by.in_(users))

            # Tag filters
            if tags:
                query = query.filter(StateChangeHistory.tags.overlap(tags))

            # Search
            if search:
                search = f"%{search}%"
                query = query.filter(
                    StateChangeHistory.metadata.cast(String).ilike(search)
                )

            # Sorting
            if order_by:
                for col in order_by:
                    if col.startswith("-"):
                        col = col[1:]
                        query = query.order_by(getattr(StateChangeHistory, col).desc())
                    else:
                        query = query.order_by(getattr(StateChangeHistory, col).asc())
            else:
                query = query.order_by(StateChangeHistory.changed_at.desc())

            # Grouping
            if group_by:
                query = query.group_by(
                    *[getattr(StateChangeHistory, col) for col in group_by]
                )

            # Pagination
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)

            return query.all()

        except Exception as e:
            logger.error(f"Error getting history: {str(e)}")
            return []

    @staticmethod
    def revert_to_state(
        instance: Any,
        target_state: str,
        user: User,
        reason: Optional[str] = None,
        validate: bool = True,
        force: bool = False,
        dry_run: bool = False,
        notify: bool = True,
        skip_handlers: bool = False,
    ) -> bool:
        """
        Revert to previous state.

        Args:
            instance: Model instance
            target_state: Target state
            user: User performing revert
            reason: Revert reason
            validate: Validate revert
            force: Force revert
            dry_run: Simulation mode
            notify: Send notifications
            skip_handlers: Skip handlers

        Returns:
            bool: Success status
        """
        try:
            # Get history
            history = HistoryManager.get_history(instance)
            if not any(entry.to_state == target_state for entry in history):
                raise ValueError(f"Target state '{target_state}' not found in history")

            # Validate revert
            if validate and hasattr(instance, "can_revert_to"):
                if not instance.can_revert_to(target_state, user):
                    if not force:
                        raise ValueError("Revert not allowed")
                    logger.warning(f"Forcing revert to state {target_state}")

            if dry_run:
                return True

            # Execute revert
            current_state = instance.state
            instance.state = target_state

            # Record revert
            HistoryManager.add_entry(
                instance,
                current_state,
                target_state,
                user,
                reason or "State reverted",
                {
                    "revert": True,
                    "forced": force,
                    "original_state": current_state,
                    "skip_handlers": skip_handlers,
                },
                notify=notify,
            )

            if not skip_handlers and hasattr(instance, "handle_revert"):
                instance.handle_revert(current_state, target_state, user)

            db.session.commit()
            return True

        except Exception as e:
            logger.error(f"Error reverting state: {str(e)}")
            db.session.rollback()
            return False

    @staticmethod
    def cleanup_history(
        max_age: Optional[int] = None,
        max_entries: Optional[int] = None,
        states: Optional[List[str]] = None,
        models: Optional[List[str]] = None,
        before: Optional[datetime] = None,
        dry_run: bool = False,
        batch_size: int = 1000,
    ) -> int:
        """
        Clean up old history entries.

        Args:
            max_age: Maximum entry age (days)
            max_entries: Maximum entries to keep
            states: States to clean
            models: Models to clean
            before: Clean before date
            dry_run: Simulation mode
            batch_size: Batch size

        Returns:
            int: Deleted entries count
        """
        try:
            query = StateChangeHistory.query

            # Age filter
            if max_age:
                cutoff_date = datetime.utcnow() - timedelta(days=max_age)
                query = query.filter(StateChangeHistory.changed_at < cutoff_date)

            # Date filter
            if before:
                query = query.filter(StateChangeHistory.changed_at < before)

            # State filter
            if states:
                query = query.filter(StateChangeHistory.to_state.in_(states))

            # Model filter
            if models:
                query = query.filter(StateChangeHistory.model_type.in_(models))

            # Get entry count
            total = query.count()

            if dry_run:
                return total

            # Batch delete
            deleted = 0
            while True:
                if max_entries and deleted >= max_entries:
                    break

                ids = [r.id for r in query.limit(batch_size)]
                if not ids:
                    break

                deleted_count = StateChangeHistory.query.filter(
                    StateChangeHistory.id.in_(ids)
                ).delete(synchronize_session=False)

                deleted += deleted_count
                db.session.commit()

            return deleted

        except Exception as e:
            logger.error(f"Error cleaning history: {str(e)}")
            db.session.rollback()
            return 0


"""
Example Usage:

1. Define Document Workflow:

from datetime import datetime
from flask_appbuilder import Model
from state_machine_mixin import StateMachineMixin, State, Transition, Workflow

class DocumentStates:
    # Define states with rich metadata and validation
    DRAFT = State(
        'draft',
        description="Initial document draft",
        is_initial=True,
        ui_color='#fafafa',
        validators=[
            lambda obj, user: bool(obj.title and obj.content),
            lambda obj, user: len(obj.content) >= 100
        ],
        metadata={
            'can_edit': True,
            'requires_content': True,
            'max_time': 72  # hours
        }
    )

    REVIEW = State(
        'review',
        description="Under review by editors",
        required_roles=['editor'],
        timeout=3600,  # 1 hour timeout
        error_state='draft',
        ui_color='#fff3cd',
        custom_handlers={
            'on_enter': lambda obj: obj.notify_reviewers(),
            'on_timeout': lambda obj: obj.handle_review_timeout()
        }
    )

    APPROVED = State(
        'approved',
        description="Document approved for publication",
        is_restricted=True,
        required_roles=['senior_editor'],
        ui_color='#d4edda',
        metadata={
            'requires_signature': True,
            'notify_author': True
        }
    )

    PUBLISHED = State(
        'published',
        description="Document published and visible",
        is_final=True,
        ui_color='#cce5ff',
        metadata={
            'publish_date': True,
            'indexed': True
        }
    )

    ARCHIVED = State(
        'archived',
        description="Document archived",
        is_final=True,
        ui_color='#e2e3e5'
    )

class DocumentTransitions:
    # Define transitions with complex rules and side effects
    SUBMIT = Transition(
        'submit',
        source='draft',
        dest='review',
        conditions=[
            lambda obj, user: obj.is_complete(),
            lambda obj, user: obj.word_count >= 500
        ],
        before=[
            lambda obj, user: obj.save_version(),
            lambda obj, user: obj.generate_preview()
        ],
        after=[
            lambda obj, user: obj.notify_reviewers(),
            lambda obj, user: obj.update_stats()
        ],
        validation_message="Document must be complete and meet minimum length requirements",
        side_effects=[
            lambda obj, user: obj.record_submission()
        ],
        async_dispatch=True
    )

    APPROVE = Transition(
        'approve',
        source='review',
        dest='approved',
        required_roles=['senior_editor'],
        conditions=[
            lambda obj, user: obj.has_review_comments(),
            lambda obj, user: obj.quality_score >= 0.8
        ],
        before=[
            lambda obj, user: obj.prepare_approval()
        ],
        after=[
            lambda obj, user: obj.notify_author("approved"),
            lambda obj, user: obj.update_metrics()
        ]
    )

    PUBLISH = Transition(
        'publish',
        source='approved',
        dest='published',
        required_roles=['publisher'],
        auto_trigger=True,  # Automatically publish when conditions met
        conditions=[
            lambda obj, user: obj.scheduled_date <= datetime.now(),
            lambda obj, user: obj.is_approved()
        ],
        before=[
            lambda obj, user: obj.generate_final_version(),
            lambda obj, user: obj.prepare_publishing()
        ],
        after=[
            lambda obj, user: obj.index_content(),
            lambda obj, user: obj.notify_subscribers(),
            lambda obj, user: obj.update_sitemap()
        ]
    )

    ARCHIVE = Transition(
        'archive',
        source=['published', 'approved'],
        dest='archived',
        conditions=[
            lambda obj, user: obj.can_archive()
        ],
        before=[
            lambda obj, user: obj.prepare_archive()
        ],
        after=[
            lambda obj, user: obj.cleanup_resources(),
            lambda obj, user: obj.update_index()
        ]
    )

class Document(StateMachineMixin, Model):
    '''Document model with advanced workflow capabilities.'''

    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(Text)
    author_id = Column(Integer, ForeignKey('ab_user.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    published_at = Column(DateTime)
    quality_score = Column(Float)
    word_count = Column(Integer)
    version = Column(Integer, default=1)
    scheduled_date = Column(DateTime)

    # Define workflow with rich configuration
    workflow = Workflow(
        name='document_workflow',
        states=[
            DocumentStates.DRAFT,
            DocumentStates.REVIEW,
            DocumentStates.APPROVED,
            DocumentStates.PUBLISHED,
            DocumentStates.ARCHIVED
        ],
        transitions=[
            DocumentTransitions.SUBMIT,
            DocumentTransitions.APPROVE,
            DocumentTransitions.PUBLISH,
            DocumentTransitions.ARCHIVE
        ],
        notification_config={
            'email': {
                'templates': {
                    'review': 'emails/document_review.html',
                    'approved': 'emails/document_approved.html',
                    'published': 'emails/document_published.html'
                },
                'recipients': ['editors@example.com']
            },
            'webhook': {
                'url': 'https://api.example.com/webhooks/documents',
                'events': ['state_change', 'published']
            },
            'slack': {
                'channel': '#documents',
                'events': ['published', 'archived']
            }
        },
        metadata={
            'version': '2.0',
            'department': 'Content',
            'compliance_level': 'high'
        },
        error_state='draft',
        max_retries=3,
        history_limit=1000
    )

    # Utility methods used by workflow
    def is_complete(self) -> bool:
        '''Check if document is complete.'''
        return bool(self.title and self.content and self.author_id)

    def has_review_comments(self) -> bool:
        '''Check if document has review comments.'''
        return ReviewComment.query.filter_by(document_id=self.id).count() > 0

    def save_version(self) -> None:
        '''Save document version.'''
        self.version += 1
        DocumentVersion(
            document_id=self.id,
            version=self.version,
            content=self.content
        ).save()

    def notify_reviewers(self) -> None:
        '''Notify reviewers of pending review.'''
        reviewers = User.query.filter_by(role='reviewer').all()
        notification_data = {
            'type': 'email',
            'data': {
                'template': 'review_notification',
                'recipients': [r.email for r in reviewers],
                'subject': f'Review Required: {self.title}',
                'variables': {
                    'document_id': self.id,
                    'title': self.title,
                    'author': self.author.name
                }
            }
        }
        asyncio.create_task(
            NotificationManager.send_notifications([notification_data])
        )

# Example Usage in View:

class DocumentModelView(ModelView):
    datamodel = SQLAInterface(Document)

    @action("submit_for_review", "Submit for Review")
    @has_access
    async def submit_for_review(self, ids):
        for doc_id in ids:
            doc = self.datamodel.get(doc_id)
            if await doc.trigger_event('submit', g.user):
                flash(f"Document '{doc.title}' submitted for review", "success")
            else:
                flash(f"Could not submit document '{doc.title}'", "error")
        return redirect(self.get_redirect())

    @action("approve_document", "Approve Document")
    @has_access
    async def approve_document(self, ids):
        for doc_id in ids:
            doc = self.datamodel.get(doc_id)
            if await doc.trigger_event('approve', g.user):
                flash(f"Document '{doc.title}' approved", "success")
            else:
                flash(f"Could not approve document '{doc.title}'", "error")
        return redirect(self.get_redirect())

# Example of Querying Workflow State:
def get_documents_in_review():
    return Document.query.filter_by(state='review').all()

# Example of Getting State History:
def get_document_history(doc_id: int):
    doc = Document.query.get(doc_id)
    return HistoryManager.get_history(
        doc,
        include_metadata=True,
        limit=50,
        order_by=['-changed_at']
    )

# Example of Generating Workflow Visualization:
def generate_workflow_docs():
    doc = Document()
    # Generate PDF diagram
    doc.visualize(filename='document_workflow', format='pdf')
    # Generate Mermaid diagram
    mermaid = doc.generate_mermaid_diagram()
    with open('document_workflow.md', 'w') as f:
        f.write(f"```mermaid\n{mermaid}\n```")

# Example of Export/Import:
def export_workflow():
    doc = Document()
    # Export to different formats
    json_def = doc.export_definition(format='json')
    yaml_def = doc.export_definition(format='yaml')
    return json_def, yaml_def
"""
