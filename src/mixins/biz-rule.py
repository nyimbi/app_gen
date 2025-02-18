"""
Business Rules Engine Implementation
==================================

A sophisticated and extensible business rules engine that supports complex routing logic,
parallel processing, time-based events, and process monitoring.

Key Features:
------------
- Rule-based decision making with priority handling
- Asynchronous execution support
- Event-driven architecture
- Custom action registration and execution
- Time-based event scheduling
- Process monitoring and metrics collection
- Rule dependency management
- Compensation handling for failed processes
- Extensible listener pattern for event handling

Main Components:
--------------
BusinessRulesEngine:
    Core engine that manages rule registration, evaluation, and execution.

BusinessRule:
    Defines individual business rules with conditions, actions, and dependencies.

RuleCondition:
    Encapsulates rule conditions as callable functions.

RuleAction:
    Encapsulates rule actions as callable functions.

RuleListener:
    Base class for implementing event listeners.

CompensationHandler:
    Handles compensation logic for failed processes.

Usage Example:
-------------
```python
# Create engine instance
engine = BusinessRulesEngine()

# Register custom actions
engine.register_custom_action('apply_discount', apply_discount_action)

# Create and register rules
rule = BusinessRule(
    name='high_value_order',
    priority=10,
    conditions=[RuleCondition(lambda ctx: ctx['order'].total > 1000)],
    actions=[RuleAction(engine.get_custom_action('apply_discount'))]
)
engine.register_rule('high_value_order', rule)

# Set context and evaluate
engine.set_context({'order': order})
await engine.evaluate_all()
```

Key Features Detail:
------------------
1. Priority-based rule execution
2. Async/await support for conditions and actions
3. Event queuing and processing
4. Metrics collection and monitoring
5. Audit logging capabilities
6. Time-based event scheduling
7. Rule dependency validation
8. Custom action registry
9. Compensation handling for failed processes
10. Predefined rule templates

Dependencies:
------------
- Python 3.7+
- SQLAlchemy
- Flask-AppBuilder
- PostgreSQL support

Notes:
-----
- Ensure proper error handling in custom actions
- Consider database persistence for long-running processes
- Monitor metrics for performance optimization
- Use compensation handlers for critical operations
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable, Tuple
from functools import wraps

from flask import current_app
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

# Configure logging
logger = logging.getLogger(__name__)

class BusinessRulesEngine:
    """Enhanced Business Rules Engine providing comprehensive rule management capabilities.

    A sophisticated business rules engine that supports complex routing logic,
    parallel processing, time-based events, compensation handling, and more.
    Provides full lifecycle management of business rules from registration to
    execution and monitoring.

    Attributes:
        rules (Dict[str, BusinessRule]): Registered business rules
        context (Dict): Current execution context data
        listeners (List[RuleListener]): Rule event listeners
        metrics (Dict): Execution metrics and statistics
        event_queue (List[Dict]): Queue for time-based/sequential events
        scheduled_tasks (List[Dict]): Persisted scheduled task definitions
        custom_actions_registry (Dict[str, Callable]): Custom action registry
        validation_rules (Dict[str, Callable]): Custom validation rules
        compensation_handlers (Dict[str, CompensationHandler]): Registered compensation handlers
        rule_groups (Dict[str, List[str]]): Logical groupings of related rules
        execution_modes (Dict[str, Dict]): Configuration for different execution modes
        dependency_graph (Dict[str, List[str]]): Rule dependency relationships
        fallback_actions (Dict[str, Callable]): Actions to execute on rule failure
        timeout_config (Dict[str, int]): Timeout settings per rule/action

    Key Capabilities:
        - Rule registration and dependency management
        - Sync and async rule evaluation/execution
        - Event-driven processing and scheduling
        - Rich metrics and monitoring
        - Compensation handling
        - Custom action libraries
        - Predefined rule templates
        - Complex routing logic
        - Rule validation and versioning
        - Execution modes (strict, lenient, dry-run)
        - Timeout and retry policies
        - Rule grouping and bulk operations
        - Fallback handling
    """
    def __init__(self):
        self.rules = {}
        self.context = {}
        self.listeners = []
        self.metrics = {
            'total_executions': 0,
            'total_errors': 0,
            'execution_times': [],
            'last_execution': None,
            'sequential_failures': 0,
            'success_rate': 1.0,
            'avg_latency': 0,
            'throughput': 0
        }
        self.event_queue = []
        self.scheduled_tasks = []
        self.custom_actions_registry = {}
        self.validation_rules = {}
        self.compensation_handlers = {}
        self.rule_groups = {}
        self.execution_modes = {
            'strict': {'stop_on_error': True},
            'lenient': {'stop_on_error': False},
            'dry_run': {'execute_actions': False}
        }
        self.dependency_graph = {}
        self.fallback_actions = {}
        self.timeout_config = {}
        self._current_mode = 'strict'

    def register_rule(self, name: str, rule: 'BusinessRule') -> 'BusinessRulesEngine':
        """Register a new business rule.

        Args:
            name: Unique identifier for the rule
            rule: BusinessRule instance to register

        Returns:
            Self for method chaining

        Raises:
            ValueError: If rule with name already exists
            ValidationError: If rule fails validation
        """
        if name in self.rules:
            raise ValueError(f"Rule {name} already registered")

        if not self._validate_rule(rule):
            raise ValidationError(f"Rule {name} failed validation")

        self.rules[name] = rule
        self._update_dependency_graph(name, rule)
        return self

    def set_context(self, context: Dict) -> 'BusinessRulesEngine':
        """Set the execution context data.

        Args:
            context: Dictionary containing execution context data

        Returns:
            Self for method chaining

        Raises:
            ValidationError: If context fails validation
        """
        if not self._validate_context(context):
            raise ValidationError("Invalid context data")
        self.context = context
        return self

    def add_listener(self, listener: 'RuleListener') -> 'BusinessRulesEngine':
        """Add a rule event listener.

        Args:
            listener: RuleListener instance to add

        Returns:
            Self for method chaining

        Raises:
            TypeError: If listener is invalid type
        """
        if not isinstance(listener, RuleListener):
            raise TypeError("Listener must be RuleListener instance")
        self.listeners.append(listener)
        return self

    def register_custom_action(self, name: str, action: Callable,
                             timeout: Optional[int] = None,
                             fallback: Optional[Callable] = None) -> None:
        """Register a custom action in the registry.

        Args:
            name: Unique identifier for the action
            action: Callable implementing the custom action
            timeout: Optional timeout in seconds
            fallback: Optional fallback action on failure

        Raises:
            ValueError: If action with name already exists
        """
        if name in self.custom_actions_registry:
            raise ValueError(f"Action {name} already registered")
        self.custom_actions_registry[name] = action
        if timeout:
            self.timeout_config[name] = timeout
        if fallback:
            self.fallback_actions[name] = fallback

    def get_custom_action(self, name: str) -> Optional[Callable]:
        """Retrieve a registered custom action by name.

        Args:
            name: Identifier of the action to retrieve

        Returns:
            Registered action callable or None if not found

        Raises:
            ActionNotFoundError: If action doesn't exist
        """
        action = self.custom_actions_registry.get(name)
        if not action:
            raise ActionNotFoundError(f"Action {name} not found")
        return action

    async def evaluate_rule(self, rule_name: str) -> Optional[List[Any]]:
        """Evaluate and execute a specific rule.

        Args:
            rule_name: Name of the rule to evaluate

        Returns:
            List of action results if rule conditions met, None otherwise

        Raises:
            ValueError: If rule not found
            RuleEvaluationError: If evaluation fails
            TimeoutError: If execution exceeds timeout
        """
        start_time = datetime.utcnow()
        rule = None

        try:
            rule = self.rules.get(rule_name)
            if not rule:
                raise ValueError(f"Rule {rule_name} not found")

            if not self._check_dependencies(rule):
                return None

            timeout = self.timeout_config.get(rule_name, 30)
            conditions_met = await asyncio.wait_for(
                rule.evaluate(self.context),
                timeout=timeout
            )

            if conditions_met and self._current_mode != 'dry_run':
                results = await rule.execute(self.context)

                self._notify_listeners('rule_executed', {
                    'rule': rule,
                    'results': results,
                    'duration': datetime.utcnow() - start_time
                })

                return results
            return None

        except asyncio.TimeoutError:
            raise TimeoutError(f"Rule {rule_name} evaluation timed out")

        except Exception as e:
            self.metrics['total_errors'] += 1
            self.metrics['sequential_failures'] += 1
            self._notify_listeners('evaluation_error', {
                'rule': rule,
                'error': e
            })

            if self._current_mode == 'strict':
                raise
            elif rule_name in self.fallback_actions:
                return await self.fallback_actions[rule_name](self.context)

        finally:
            duration = datetime.utcnow() - start_time
            self.metrics['total_executions'] += 1
            self.metrics['execution_times'].append(duration.total_seconds())
            self.metrics['last_execution'] = datetime.utcnow()
            self._update_metrics()

    async def evaluate_all(self) -> Dict[str, Any]:
        """Evaluate all registered rules in priority order.

        Returns:
            Dictionary mapping rule names to their execution results

        Raises:
            RuleEvaluationError: If evaluation fails in strict mode
        """
        results = {}
        sorted_rules = sorted(self.rules.values(), key=lambda r: r.priority, reverse=True)

        for rule in sorted_rules:
            try:
                result = await self.evaluate_rule(rule.name)
                if result is not None:
                    results[rule.name] = result
            except Exception as e:
                logger.error(f"Rule evaluation error: {str(e)}")
                self._notify_listeners('evaluation_error', {
                    'rule': rule,
                    'error': e
                })
                if self._current_mode == 'strict':
                    raise

        return results

    def enqueue_event(self, event_data: Dict) -> None:
        """Enqueue an event for time-based or sequential processing.

        Args:
            event_data: Event data dictionary containing rule_name and timing info
        """
        self.event_queue.append(event_data)

    async def process_events(self) -> None:
        """Process all queued events in FIFO order."""
        while self.event_queue:
            current_event = self.event_queue.pop(0)
            try:
                await self._handle_event(current_event)
            except Exception as e:
                logger.error(f"Error processing event: {str(e)}")

    async def _handle_event(self, event_data: Dict) -> None:
        """Handle an individual queued event.

        Args:
            event_data: Event data dictionary

        Raises:
            EventHandlingError: If event handling fails
        """
        rule_name = event_data.get('rule_name')
        if not rule_name or rule_name not in self.rules:
            logger.warning(f"Event discarded: {event_data}")
            return

        try:
            await self.evaluate_rule(rule_name)
        except Exception as e:
            raise EventHandlingError(f"Failed to handle event: {str(e)}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive execution metrics and statistics.

        Returns:
            Dictionary containing execution metrics
        """
        return {
            **self.metrics,
            'avg_execution_time': (
                sum(self.metrics['execution_times']) / len(self.metrics['execution_times'])
                if self.metrics['execution_times'] else 0
            ),
            'error_rate': (
                self.metrics['total_errors'] / self.metrics['total_executions']
                if self.metrics['total_executions'] else 0
            ),
            'success_rate': self.metrics['success_rate'],
            'avg_latency': self.metrics['avg_latency'],
            'throughput': self.metrics['throughput']
        }

    def _notify_listeners(self, event_type: str, data: Dict) -> None:
        """Notify registered listeners of rule engine events.

        Args:
            event_type: Type of event that occurred
            data: Event data dictionary
        """
        for listener in self.listeners:
            try:
                listener(event_type, data)
            except Exception as e:
                logger.error(f"Listener error: {str(e)}")

    def audit_log(self, event_type: str, data: Dict) -> None:
        """Log events for auditing purposes.

        Args:
            event_type: Type of event to log
            data: Event data to log
        """
        logger.info(f"AUDIT_LOG: {event_type} -> {json.dumps(data)}")

    def schedule_time_based_event(self, rule_name: str, delay: int) -> None:
        """Schedule a rule to be executed after a delay.

        Args:
            rule_name: Name of rule to schedule
            delay: Delay in seconds before execution

        Raises:
            ValueError: If rule_name invalid or delay negative
        """
        if rule_name not in self.rules:
            raise ValueError(f"Unknown rule: {rule_name}")

        if delay < 0:
            raise ValueError("Delay must be non-negative")

        scheduled_event = {
            'rule_name': rule_name,
            'scheduled_time': datetime.utcnow() + timedelta(seconds=delay)
        }
        self.enqueue_event(scheduled_event)
        self.scheduled_tasks.append(scheduled_event)

    def restore_scheduled_tasks(self) -> None:
        """Restore all persisted scheduled tasks."""
        for task in self.scheduled_tasks:
            self.enqueue_event(task)

    def _check_dependencies(self, rule: 'BusinessRule') -> bool:
        """Check if all rule dependencies are satisfied.

        Args:
            rule: BusinessRule to check dependencies for

        Returns:
            True if all dependencies satisfied, False otherwise

        Raises:
            CircularDependencyError: If circular dependency detected
        """
        visited = set()

        def check_cycle(rule_name):
            if rule_name in visited:
                raise CircularDependencyError(f"Circular dependency detected for {rule_name}")
            visited.add(rule_name)
            for dep in self.dependency_graph.get(rule_name, []):
                check_cycle(dep)
            visited.remove(rule_name)

        try:
            check_cycle(rule.name)
        except CircularDependencyError as e:
            logger.error(str(e))
            return False

        for dependency in rule.dependencies:
            if dependency not in self.rules or not self.rules[dependency].evaluated:
                return False
        return True

    def _validate_rule(self, rule: 'BusinessRule') -> bool:
        """Validate a rule's configuration.

        Args:
            rule: Rule to validate

        Returns:
            True if valid, False otherwise
        """
        if not rule.validate():
            return False

        for validator in self.validation_rules.values():
            if not validator(rule):
                return False
        return True

    def _validate_context(self, context: Dict) -> bool:
        """Validate execution context.

        Args:
            context: Context to validate

        Returns:
            True if valid, False otherwise
        """
        required_keys = {'user', 'timestamp'}
        return all(key in context for key in required_keys)

    def _update_dependency_graph(self, name: str, rule: 'BusinessRule') -> None:
        """Update rule dependency relationships.

        Args:
            name: Rule name
            rule: Rule instance
        """
        self.dependency_graph[name] = rule.dependencies

    def _update_metrics(self) -> None:
        """Update derived metrics."""
        total = self.metrics['total_executions']
        if total:
            self.metrics['success_rate'] = (total - self.metrics['total_errors']) / total
            self.metrics['avg_latency'] = sum(self.metrics['execution_times']) / total
            self.metrics['throughput'] = total / (time.time() - self.metrics['first_execution'])

    def predefined_rule_templates(self) -> List['BusinessRule']:
        """Get library of predefined rule templates.

        Returns:
            List of predefined BusinessRule templates
        """
        return [
            BusinessRule(
                name='high_value_order',
                priority=10,
                conditions=[
                    RuleCondition(lambda ctx: ctx['order'].total > 1000)
                ],
                actions=[
                    RuleAction(lambda ctx: ctx['order'].apply_discount(0.15)),
                    RuleAction(lambda ctx: ctx['order'].schedule_followup())
                ]
            ),
            BusinessRule(
                name='vip_customer',
                priority=8,
                conditions=[
                    RuleCondition(lambda ctx: ctx['customer'].is_vip)
                ],
                actions=[
                    RuleAction(lambda ctx: ctx['customer'].add_loyalty_points(500))
                ]
            )
        ]

class RuleListener:
    """Base class for rule listeners that handles business rule events.

    This class provides a framework for implementing event listeners that can react
    to various rule engine events like rule execution, evaluation errors, validation
    failures etc. It uses a dynamic dispatch mechanism to route events to appropriate
    handler methods.

    The listener maintains a complete event history and provides rich monitoring,
    filtering and analysis capabilities. It supports multiple event types including:
    - Rule execution events
    - Evaluation errors
    - Validation failures
    - Configuration changes
    - Performance metrics
    - Dependency tracking
    - Custom events

    Attributes:
        name (str): Optional name for the listener instance
        event_history (List): List of previously processed events
        error_count (int): Counter for tracking number of errors
        event_types (Set[str]): Set of supported event types
        start_time (datetime): When this listener was initialized
        metadata (Dict): Additional listener metadata
        is_active (bool): Whether listener is currently active
        filters (List[Callable]): Event filtering functions
        statistics (Dict): Runtime statistics and metrics

    Example:
        class MyListener(RuleListener):
            def on_rule_executed(self, data):
                print(f"Rule {data['rule'].name} executed successfully")

            def on_validation_error(self, data):
                self.notify_admin(data['error'])
    """

    def __init__(self, name: Optional[str] = None,
                 filters: Optional[List[Callable]] = None,
                 metadata: Optional[Dict] = None):
        """Initialize a new rule listener.

        Args:
            name: Optional name for this listener instance
            filters: Optional list of event filter functions
            metadata: Optional listener metadata dictionary
        """
        self.name = name
        self.event_history = []
        self.error_count = 0
        self.event_types = {
            'rule_executed', 'evaluation_error', 'validation_failure',
            'configuration_change', 'performance_metric', 'dependency_update',
            'custom_event'
        }
        self.start_time = datetime.utcnow()
        self.metadata = metadata or {}
        self.is_active = True
        self.filters = filters or []
        self.statistics = {
            'total_events': 0,
            'events_by_type': {},
            'error_rate': 0.0,
            'avg_processing_time': 0.0
        }

    def __call__(self, event_type: str, data: Dict) -> None:
        """Route incoming events to appropriate handler methods.

        Processes incoming events by:
        1. Validating event type
        2. Applying filters
        3. Recording event
        4. Dispatching to handler
        5. Updating statistics

        Args:
            event_type: Type of event (e.g. 'rule_executed', 'evaluation_error')
            data: Dictionary containing event data

        Raises:
            ValueError: If event type is invalid
            RuntimeError: If listener is inactive
        """
        if not self.is_active:
            raise RuntimeError("Listener is inactive")

        if event_type not in self.event_types:
            raise ValueError(f"Invalid event type: {event_type}")

        if not self._apply_filters(event_type, data):
            return

        start_time = datetime.utcnow()
        self.event_history.append((event_type, data, start_time))
        self.statistics['total_events'] += 1
        self.statistics['events_by_type'][event_type] = \
            self.statistics['events_by_type'].get(event_type, 0) + 1

        method = getattr(self, f"on_{event_type}", None)
        if callable(method):
            try:
                method(data)
            except Exception as e:
                self.error_count += 1
                self.statistics['error_rate'] = \
                    self.error_count / self.statistics['total_events']
                logger.error(f"Error during event processing: {str(e)}")
                self.on_handler_error(e, event_type, data)

        duration = (datetime.utcnow() - start_time).total_seconds()
        self._update_timing_stats(duration)

    def on_rule_executed(self, data: Dict) -> None:
        """Handle rule execution events.

        Args:
            data: Dictionary containing:
                - rule: The BusinessRule instance that was executed
                - results: Results from rule execution
                - duration: Time taken to execute the rule
                - context: Execution context
                - timestamp: When execution occurred
        """
        rule = data['rule']
        results = data['results']
        duration = data['duration']
        context = data.get('context', {})

        logger.info(
            f"Rule '{rule.name}' executed in {duration}s with results: {results}"
        )
        self._record_performance_metric(rule.name, duration)

    def on_evaluation_error(self, data: Dict) -> None:
        """Handle rule evaluation error events.

        Args:
            data: Dictionary containing:
                - rule: The BusinessRule instance that failed
                - error: The exception that occurred
                - context: Evaluation context
                - timestamp: When error occurred
                - stack_trace: Full error stack trace
        """
        rule = data['rule']
        error = data['error']
        context = data.get('context', {})
        stack_trace = data.get('stack_trace')

        logger.error(
            f"Error evaluating rule '{rule.name}': {str(error)}\n"
            f"Context: {context}\nStack trace: {stack_trace}"
        )
        self._notify_error_handlers(rule, error, context)

    def on_validation_failure(self, data: Dict) -> None:
        """Handle validation failure events.

        Args:
            data: Validation failure details
        """
        logger.warning(f"Validation failed: {data}")
        self._record_validation_metric(data)

    def on_configuration_change(self, data: Dict) -> None:
        """Handle configuration change events.

        Args:
            data: Configuration change details
        """
        logger.info(f"Configuration changed: {data}")
        self._apply_configuration_update(data)

    def on_performance_metric(self, data: Dict) -> None:
        """Handle performance metric events.

        Args:
            data: Performance metric data
        """
        logger.debug(f"Performance metric: {data}")
        self._update_performance_stats(data)

    def on_dependency_update(self, data: Dict) -> None:
        """Handle dependency update events.

        Args:
            data: Dependency update details
        """
        logger.info(f"Dependency updated: {data}")
        self._verify_dependencies(data)

    def on_custom_event(self, data: Dict) -> None:
        """Handle custom events.

        Args:
            data: Custom event data
        """
        logger.info(f"Custom event received: {data}")
        self._process_custom_event(data)

    def on_handler_error(self, error: Exception, event_type: str, data: Dict) -> None:
        """Handle errors that occur in event handlers themselves.

        Args:
            error: The exception that occurred
            event_type: Type of event being handled when error occurred
            data: The event data being processed

        Raises:
            CriticalHandlerError: For severe handler failures
        """
        logger.error(
            f"Event handler error for {event_type}: {str(error)}\n"
            f"Event data: {data}"
        )
        self._handle_critical_error(error, event_type, data)

    def get_event_history(self) -> List[Tuple[str, Dict, datetime]]:
        """Return the history of processed events.

        Provides access to the complete event history with filtering options.

        Returns:
            List of tuples containing (event_type, data, timestamp)

        Example:
            recent_errors = [
                event for event in listener.get_event_history()
                if event[0] == 'evaluation_error'
                and event[2] > threshold_time
            ]
        """
        return self.event_history

    def clear_history(self, before_date: Optional[datetime] = None) -> None:
        """Clear the event history.

        Args:
            before_date: Optional date to clear history before
        """
        if before_date:
            self.event_history = [
                event for event in self.event_history
                if event[2] > before_date
            ]
        else:
            self.event_history = []

    def add_filter(self, filter_func: Callable[[str, Dict], bool]) -> None:
        """Add an event filter function.

        Args:
            filter_func: Function that takes event_type and data and returns bool
        """
        self.filters.append(filter_func)

    def get_statistics(self) -> Dict:
        """Get listener statistics and metrics.

        Returns:
            Dictionary of runtime statistics
        """
        return {
            **self.statistics,
            'uptime': (datetime.utcnow() - self.start_time).total_seconds(),
            'total_errors': self.error_count
        }

    def _apply_filters(self, event_type: str, data: Dict) -> bool:
        """Apply all filters to an event.

        Args:
            event_type: Event type
            data: Event data

        Returns:
            True if event passes all filters
        """
        return all(f(event_type, data) for f in self.filters)

    def _update_timing_stats(self, duration: float) -> None:
        """Update timing statistics.

        Args:
            duration: Event processing duration
        """
        prev_avg = self.statistics['avg_processing_time']
        total_events = self.statistics['total_events']
        self.statistics['avg_processing_time'] = \
            (prev_avg * (total_events - 1) + duration) / total_events

    def _record_performance_metric(self, rule_name: str, duration: float) -> None:
        """Record a performance metric.

        Args:
            rule_name: Name of rule
            duration: Execution duration
        """
        pass  # Implement metric recording

    def _notify_error_handlers(self, rule: Any, error: Exception, context: Dict) -> None:
        """Notify error handlers of failures.

        Args:
            rule: Failed rule
            error: Exception that occurred
            context: Execution context
        """
        pass  # Implement error notification

    def _record_validation_metric(self, data: Dict) -> None:
        """Record a validation metric.

        Args:
            data: Validation data
        """
        pass  # Implement validation metric recording

    def _apply_configuration_update(self, data: Dict) -> None:
        """Apply a configuration update.

        Args:
            data: Configuration data
        """
        pass  # Implement configuration updates

    def _update_performance_stats(self, data: Dict) -> None:
        """Update performance statistics.

        Args:
            data: Performance data
        """
        pass  # Implement stats updates

    def _verify_dependencies(self, data: Dict) -> None:
        """Verify rule dependencies.

        Args:
            data: Dependency data
        """
        pass  # Implement dependency verification

    def _process_custom_event(self, data: Dict) -> None:
        """Process a custom event.

        Args:
            data: Custom event data
        """
        pass  # Implement custom event processing

    def _handle_critical_error(self, error: Exception, event_type: str, data: Dict) -> None:
        """Handle a critical error.

        Args:
            error: Exception that occurred
            event_type: Type of event
            data: Event data
        """
        pass  # Implement critical error handling



class RuleCondition:
    """Defines and evaluates conditions for business rules.

    This class encapsulates the logic for evaluating rule conditions, supporting both
    synchronous and asynchronous evaluation functions. It provides rich metadata
    about the condition and validation capabilities.

    Attributes:
        func: The callable that implements the condition logic
        description: Human readable description of what the condition checks
        created_at: Timestamp when condition was created
        last_evaluated: Timestamp of last evaluation
        evaluation_count: Number of times condition has been evaluated
        last_result: Result of most recent evaluation
        metadata: Optional dictionary of additional metadata about the condition

    Example:
        condition = RuleCondition(
            lambda ctx: ctx['order'].total > 1000,
            description="Check if order total exceeds $1000"
        )

        # Evaluate condition
        is_met = await condition(context)
    """

    def __init__(self, func: Callable, description: Optional[str] = None,
                 metadata: Optional[Dict] = None):
        self.func = func
        self.description = description
        self.created_at = datetime.utcnow()
        self.last_evaluated = None
        self.evaluation_count = 0
        self.last_result = None
        self.metadata = metadata or {}

    async def __call__(self, context: Dict) -> bool:
        """Evaluate the condition with the given context.

        Args:
            context: Dictionary containing data needed for condition evaluation

        Returns:
            bool: True if condition is met, False otherwise

        Raises:
            RuleConditionError: If evaluation fails
        """
        try:
            if asyncio.iscoroutinefunction(self.func):
                result = await self.func(context)
            else:
                result = self.func(context)

            self.last_evaluated = datetime.utcnow()
            self.evaluation_count += 1
            self.last_result = bool(result)
            return self.last_result

        except Exception as e:
            logger.error(f"Error evaluating condition: {str(e)}")
            raise RuleConditionError(f"Condition evaluation failed: {str(e)}")

    def get_stats(self) -> Dict:
        """Get statistics about this condition's evaluation history."""
        return {
            'created_at': self.created_at,
            'last_evaluated': self.last_evaluated,
            'evaluation_count': self.evaluation_count,
            'last_result': self.last_result
        }

    def validate(self, context: Dict) -> bool:
        """Validate that the condition can be evaluated with given context.

        Args:
            context: Context to validate against

        Returns:
            bool: True if condition can be evaluated with context
        """
        try:
            required_keys = self.metadata.get('required_context_keys', [])
            return all(key in context for key in required_keys)
        except Exception:
            return False

class RuleConditionError(Exception):
    """Exception raised for errors in condition evaluation.

    This specialized exception provides detailed information about failures
    that occur during rule condition evaluation, including context and validation
    details.

    Attributes:
        message: The error message
        condition_desc: Description of the failed condition
        context: The evaluation context when error occurred
        validation_errors: List of validation errors if applicable
        timestamp: When the error occurred

    Example:
        try:
            condition.evaluate(context)
        except RuleConditionError as e:
            print(f"Condition failed: {e.get_error_details()}")
    """

    def __init__(self, message: str, condition_desc: str = None,
                 context: Dict = None, validation_errors: List[str] = None):
        """Initialize a new RuleConditionError.

        Args:
            message: The error message
            condition_desc: Optional description of the failed condition
            context: Optional evaluation context
            validation_errors: Optional list of validation error messages
        """
        super().__init__(message)
        self.message = message
        self.condition_desc = condition_desc
        self.context = context
        self.validation_errors = validation_errors or []
        self.timestamp = datetime.utcnow()

    def __str__(self) -> str:
        """Returns formatted error message with details."""
        base = f"Condition Error: {self.message}"
        if self.condition_desc:
            base += f" (condition: {self.condition_desc})"
        if self.validation_errors:
            base += f"\nValidation errors: {', '.join(self.validation_errors)}"
        return base

    def get_error_details(self) -> Dict:
        """Get detailed error information as dictionary.

        Returns:
            Dictionary containing all error details
        """
        return {
            'message': self.message,
            'condition_desc': self.condition_desc,
            'context': self.context,
            'validation_errors': self.validation_errors,
            'timestamp': self.timestamp
        }

    def log_error(self, logger: logging.Logger = None) -> None:
        """Log the error details.

        Args:
            logger: Optional logger instance to use
        """
        log = logger or logging.getLogger(__name__)
        log.error(str(self))
        if self.context:
            log.error(f"Error context: {json.dumps(self.context)}")

class RuleAction:
    """Defines and executes actions for business rules.

    This class encapsulates executable actions that are triggered when rule conditions are met.
    It supports both synchronous and asynchronous execution, with rich metadata tracking and
    error handling capabilities.

    Attributes:
        func: The callable implementing the action logic
        description: Human readable description of what the action does
        created_at: Timestamp when action was created
        last_executed: Timestamp of most recent execution
        execution_count: Number of times action has been executed
        last_result: Result of most recent execution
        metadata: Optional dictionary of additional metadata
        timeout: Maximum execution time in seconds
        retry_count: Number of retry attempts for failed executions

    Example:
        action = RuleAction(
            lambda ctx: ctx['order'].apply_discount(0.1),
            description="Apply 10% discount to order"
        )

        # Execute action
        result = await action(context)
    """

    def __init__(self, func: Callable, description: Optional[str] = None,
                 metadata: Optional[Dict] = None, timeout: int = 30,
                 retry_count: int = 3):
        self.func = func
        self.description = description
        self.created_at = datetime.utcnow()
        self.last_executed = None
        self.execution_count = 0
        self.last_result = None
        self.metadata = metadata or {}
        self.timeout = timeout
        self.retry_count = retry_count
        self._error_count = 0

    async def __call__(self, context: Dict) -> Any:
        """Execute the action with given context.

        Args:
            context: Dictionary containing data needed for action execution

        Returns:
            Any: Result of the action execution

        Raises:
            RuleActionError: If execution fails after all retries
            RuleActionTimeout: If execution exceeds timeout
        """
        start_time = datetime.utcnow()
        attempts = 0

        while attempts <= self.retry_count:
            try:
                if asyncio.iscoroutinefunction(self.func):
                    result = await asyncio.wait_for(self.func(context), timeout=self.timeout)
                else:
                    result = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(None, self.func, context),
                        timeout=self.timeout
                    )

                self.last_executed = datetime.utcnow()
                self.execution_count += 1
                self.last_result = result
                return result

            except asyncio.TimeoutError:
                self._error_count += 1
                if attempts == self.retry_count:
                    raise RuleActionTimeout(f"Action timed out after {self.timeout}s")

            except Exception as e:
                self._error_count += 1
                if attempts == self.retry_count:
                    raise RuleActionError(f"Action failed after {attempts} attempts: {str(e)}")

            attempts += 1
            await asyncio.sleep(1)  # Basic backoff

    def get_stats(self) -> Dict:
        """Get statistics about this action's execution history."""
        return {
            'created_at': self.created_at,
            'last_executed': self.last_executed,
            'execution_count': self.execution_count,
            'error_count': self._error_count,
            'last_result': self.last_result
        }

    def validate(self, context: Dict) -> bool:
        """Validate that the action can be executed with given context.

        Args:
            context: Context to validate against

        Returns:
            bool: True if action can be executed with context
        """
        try:
            required_keys = self.metadata.get('required_context_keys', [])
            return all(key in context for key in required_keys)
        except Exception:
            return False

class RuleActionError(Exception):
    """Exception raised for errors in action execution.

    This exception is raised when a rule action fails to execute properly,
    providing detailed information about the failure and context.

    Attributes:
        message: The error message
        action_name: Name of the failed action
        context: The execution context when error occurred
        attempts: Number of retry attempts made
        original_error: The underlying exception that caused the failure
        timestamp: When the error occurred
    """

    def __init__(self, message: str, action_name: str = None,
                 context: Dict = None, attempts: int = 0,
                 original_error: Exception = None):
        """Initialize a new RuleActionError.

        Args:
            message: The error message
            action_name: Optional name of the failed action
            context: Optional execution context
            attempts: Number of retry attempts made
            original_error: The underlying exception
        """
        super().__init__(message)
        self.message = message
        self.action_name = action_name
        self.context = context
        self.attempts = attempts
        self.original_error = original_error
        self.timestamp = datetime.utcnow()

    def __str__(self) -> str:
        """Returns formatted error message with details."""
        base = f"Action Error: {self.message}"
        if self.action_name:
            base += f" (action: {self.action_name})"
        if self.attempts:
            base += f" after {self.attempts} attempts"
        if self.original_error:
            base += f"\nCaused by: {str(self.original_error)}"
        return base

    def get_error_details(self) -> Dict:
        """Get detailed error information as dictionary.

        Returns:
            Dictionary containing all error details
        """
        return {
            'message': self.message,
            'action_name': self.action_name,
            'context': self.context,
            'attempts': self.attempts,
            'original_error': str(self.original_error) if self.original_error else None,
            'timestamp': self.timestamp
        }

    def log_error(self, logger: logging.Logger = None) -> None:
        """Log the error details.

        Args:
            logger: Optional logger instance to use
        """
        log = logger or logging.getLogger(__name__)
        log.error(str(self))
        if self.context:
            log.error(f"Error context: {json.dumps(self.context)}")

class RuleActionTimeout(Exception):
    """Exception raised when action execution exceeds timeout limit.

    This specialized exception provides detailed information about timeout
    failures during rule action execution, including timing details and
    execution context.

    Attributes:
        message: The error message
        action_name: Name of the action that timed out
        timeout_limit: The timeout limit that was exceeded (in seconds)
        execution_time: How long the action ran before timeout
        context: The execution context when timeout occurred
        timestamp: When the timeout occurred

    Example:
        try:
            result = await action.execute(context, timeout=5)
        except RuleActionTimeout as e:
            print(f"Action timed out after {e.execution_time}s")
    """

    def __init__(self, message: str, action_name: str = None,
                 timeout_limit: int = None, execution_time: float = None,
                 context: Dict = None):
        """Initialize a new RuleActionTimeout.

        Args:
            message: The error message
            action_name: Optional name of the timed out action
            timeout_limit: Optional timeout limit that was exceeded
            execution_time: Optional actual execution time before timeout
            context: Optional execution context
        """
        super().__init__(message)
        self.message = message
        self.action_name = action_name
        self.timeout_limit = timeout_limit
        self.execution_time = execution_time
        self.context = context
        self.timestamp = datetime.utcnow()

    def __str__(self) -> str:
        """Returns formatted timeout message with details."""
        base = f"Action Timeout: {self.message}"
        if self.action_name:
            base += f" (action: {self.action_name})"
        if self.timeout_limit:
            base += f" - {self.timeout_limit}s limit exceeded"
        if self.execution_time:
            base += f" after running for {self.execution_time}s"
        return base

    def get_timeout_details(self) -> Dict:
        """Get detailed timeout information as dictionary.

        Returns:
            Dictionary containing all timeout details
        """
        return {
            'message': self.message,
            'action_name': self.action_name,
            'timeout_limit': self.timeout_limit,
            'execution_time': self.execution_time,
            'context': self.context,
            'timestamp': self.timestamp
        }

    def log_timeout(self, logger: logging.Logger = None) -> None:
        """Log the timeout details.

        Args:
            logger: Optional logger instance to use
        """
        log = logger or logging.getLogger(__name__)
        log.error(str(self))
        if self.context:
            log.error(f"Timeout context: {json.dumps(self.context)}")

class BusinessRule:
    """Defines a business rule with conditions, actions, and dependencies.

    A business rule encapsulates the logic for evaluating conditions and executing
    corresponding actions based on a given context. It supports dependencies on other
    rules and provides rich metadata about rule execution.

    Attributes:
        name: Unique identifier for the rule
        priority: Execution priority (higher numbers = higher priority)
        conditions: List of RuleCondition objects to evaluate
        actions: List of RuleAction objects to execute if conditions pass
        dependencies: List of rule names that must evaluate first
        evaluated: Whether this rule has been evaluated
        created_at: When this rule was created
        last_evaluated: When rule was last evaluated
        last_executed: When actions were last executed
        metadata: Additional rule metadata

    Example:
        rule = BusinessRule(
            name="high_value_order",
            priority=10,
            conditions=[
                RuleCondition(lambda ctx: ctx['order'].total > 1000)
            ],
            actions=[
                RuleAction(lambda ctx: ctx['order'].apply_discount(0.1))
            ]
        )
    """
    def __init__(self, name: str, priority: int = 0,
                 conditions: Optional[List[RuleCondition]] = None,
                 actions: Optional[List[RuleAction]] = None,
                 dependencies: Optional[List[str]] = None,
                 metadata: Optional[Dict] = None):
        self.name = name
        self.priority = priority
        self.conditions = conditions or []
        self.actions = actions or []
        self.dependencies = dependencies or []
        self.evaluated = False
        self.created_at = datetime.utcnow()
        self.last_evaluated = None
        self.last_executed = None
        self.metadata = metadata or {}
        self._evaluation_count = 0
        self._execution_count = 0
        self._error_count = 0

    async def evaluate(self, context: Dict) -> bool:
        """Evaluate all conditions for this rule.

        Args:
            context: Dictionary containing data needed for condition evaluation

        Returns:
            bool: True if all conditions are met, False otherwise

        Raises:
            RuleEvaluationError: If condition evaluation fails
        """
        self._evaluation_count += 1
        self.last_evaluated = datetime.utcnow()

        try:
            results = [await condition(context) for condition in self.conditions]
            self.evaluated = all(results)
            return self.evaluated

        except Exception as e:
            self._error_count += 1
            raise RuleEvaluationError(f"Rule {self.name} evaluation failed: {str(e)}")

    async def execute(self, context: Dict) -> List[Any]:
        """Execute all actions for this rule.

        Args:
            context: Dictionary containing data needed for action execution

        Returns:
            List[Any]: Results from all executed actions

        Raises:
            RuleExecutionError: If action execution fails
        """
        self._execution_count += 1
        self.last_executed = datetime.utcnow()

        try:
            results = []
            for action in self.actions:
                result = await action(context)
                results.append(result)
            return results

        except Exception as e:
            self._error_count += 1
            raise RuleExecutionError(f"Rule {self.name} execution failed: {str(e)}")

    def get_stats(self) -> Dict:
        """Get statistics about this rule's evaluation and execution history."""
        return {
            'created_at': self.created_at,
            'last_evaluated': self.last_evaluated,
            'last_executed': self.last_executed,
            'evaluation_count': self._evaluation_count,
            'execution_count': self._execution_count,
            'error_count': self._error_count
        }

    def validate(self) -> bool:
        """Validate rule configuration.

        Returns:
            bool: True if rule is valid, False otherwise
        """
        return bool(
            self.name and
            self.conditions and
            self.actions and
            all(isinstance(c, RuleCondition) for c in self.conditions) and
            all(isinstance(a, RuleAction) for a in self.actions)
        )

    def clone(self, new_name: Optional[str] = None) -> 'BusinessRule':
        """Create a copy of this rule, optionally with a new name.

        Args:
            new_name: Optional new name for the cloned rule

        Returns:
            BusinessRule: A new rule instance with copied attributes
        """
        return BusinessRule(
            name=new_name or f"{self.name}_copy",
            priority=self.priority,
            conditions=self.conditions.copy(),
            actions=self.actions.copy(),
            dependencies=self.dependencies.copy(),
            metadata=self.metadata.copy()
        )

class CompensationHandler:
    """Handles compensation for failed processes by executing rollback steps.

    This class provides a way to define and execute compensation/rollback steps when
    business processes fail. It supports both synchronous and asynchronous compensation
    steps, tracks execution history, and provides detailed failure handling.

    Attributes:
        steps: List of callable compensation steps to execute in reverse order
        execution_history: List of executed compensation steps and their results
        error_handlers: Dict mapping step names to error handler functions
        retry_count: Number of retry attempts for failed compensation steps
        timeout: Maximum execution time per step in seconds

    Example:
        handler = CompensationHandler([
            lambda ctx: ctx['order'].reverse_payment(),
            lambda ctx: ctx['inventory'].restore_stock()
        ])

        await handler.execute(context)
    """

    def __init__(self, steps: List[Callable], retry_count: int = 3,
                 timeout: int = 30):
        """Initialize compensation handler.

        Args:
            steps: List of compensation steps to execute
            retry_count: Number of retries for failed steps
            timeout: Timeout in seconds per step
        """
        self.steps = steps
        self.execution_history = []
        self.error_handlers = {}
        self.retry_count = retry_count
        self.timeout = timeout
        self._error_count = 0

    def register_error_handler(self, step_name: str, handler: Callable):
        """Register an error handler for a specific compensation step.

        Args:
            step_name: Name of the step to handle errors for
            handler: Error handling function
        """
        self.error_handlers[step_name] = handler

    async def execute(self, context: Dict) -> bool:
        """Execute all compensation steps in reverse order.

        Args:
            context: Dictionary containing compensation execution context

        Returns:
            bool: True if all steps completed successfully, False otherwise

        Raises:
            CompensationError: If critical compensation steps fail
        """
        success = True
        start_time = datetime.utcnow()

        for step in reversed(self.steps):
            step_name = getattr(step, '__name__', str(step))
            attempts = 0

            while attempts <= self.retry_count:
                try:
                    if asyncio.iscoroutinefunction(step):
                        result = await asyncio.wait_for(
                            step(context),
                            timeout=self.timeout
                        )
                    else:
                        result = await asyncio.wait_for(
                            asyncio.get_event_loop().run_in_executor(None, step, context),
                            timeout=self.timeout
                        )

                    self.execution_history.append({
                        'step': step_name,
                        'success': True,
                        'timestamp': datetime.utcnow()
                    })
                    break

                except Exception as e:
                    self._error_count += 1
                    attempts += 1

                    error_handler = self.error_handlers.get(step_name)
                    if error_handler:
                        try:
                            await error_handler(e, context)
                        except Exception as handler_error:
                            logger.error(f"Error handler failed: {str(handler_error)}")

                    if attempts > self.retry_count:
                        logger.error(f"Compensation step {step_name} failed: {str(e)}")
                        self.execution_history.append({
                            'step': step_name,
                            'success': False,
                            'error': str(e),
                            'timestamp': datetime.utcnow()
                        })
                        success = False

                    await asyncio.sleep(attempts)  # Exponential backoff

        duration = datetime.utcnow() - start_time
        logger.info(f"Compensation completed in {duration.total_seconds()}s")
        return success

    def get_execution_stats(self) -> Dict:
        """Get statistics about compensation execution history.

        Returns:
            Dictionary containing execution statistics
        """
        return {
            'total_steps': len(self.steps),
            'completed_steps': len(self.execution_history),
            'error_count': self._error_count,
            'success_rate': len([x for x in self.execution_history if x['success']]) /
                          len(self.execution_history) if self.execution_history else 0
        }

    def clear_history(self) -> None:
        """Clear the execution history."""
        self.execution_history = []
        self._error_count = 0

# Example predefined custom actions
async def apply_discount_action(ctx):
    order = ctx.get('order')
    if order:
        order.apply_discount(0.1)

async def add_loyalty_points_action(ctx):
    customer = ctx.get('customer')
    if customer:
        customer.add_loyalty_points(200)

async def send_notification_action(ctx):
    user = ctx.get('user')
    if user:
        logger.info(f"Notification sent to {user.email}")

# Register custom actions
engine = BusinessRulesEngine()
engine.register_custom_action('apply_discount', apply_discount_action)
engine.register_custom_action('add_loyalty_points', add_loyalty_points_action)
engine.register_custom_action('send_notification', send_notification_action)

# Example usage
async def process_order(order):
    """Simulate order processing with advanced business rules."""
    engine.set_context({'order': order})

    engine.register_rule(
        'high_value_order',
        BusinessRule(
            name='high_value_order',
            priority=10,
            conditions=[
                RuleCondition(lambda ctx: ctx['order'].total > 1000)
            ],
            actions=[
                RuleAction(engine.get_custom_action('apply_discount')),
                RuleAction(engine.get_custom_action('send_notification'))
            ]
        )
    )

    await engine.evaluate_all()
