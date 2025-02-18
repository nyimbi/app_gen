"""
business_rules_mixin.py - Advanced Business Rules Engine for Flask-AppBuilder

This module provides a comprehensive business rules engine that integrates with
Flask-AppBuilder models. It supports complex rule definitions, conditional logic,
action sequences, event handling, and full audit logging.

Key Features:
- Declarative rule definitions
- Complex conditions with AND/OR logic
- Sequential and parallel actions
- Rule priorities and metadata
- Event listeners and notifications
- Full audit logging
- PostgreSQL integration
- Async execution support
- Error handling and recovery
- Performance monitoring

Core Components:
- BusinessRuleMixin: Main mixin for adding rules to models
- BusinessRule: Rule definition with conditions and actions
- RuleEngine: Rule execution engine
- RuleCondition: Rule condition evaluator
- RuleAction: Rule action executor
- RuleListener: Event handler base class

Requirements:
- Python 3.8+
- Flask-AppBuilder
- PostgreSQL
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Callable
from functools import wraps

from flask import current_app
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

# Configure logging
logger = logging.getLogger(__name__)

class BusinessRuleMixin:
    """
    Adds business rules capabilities to Flask-AppBuilder models.

    Attributes:
        rules_metadata (Column): JSON column for rules metadata
        last_evaluation (Column): Last rule evaluation timestamp
        rule_count (Column): Total number of rule evaluations
    """

    rules_metadata = Column(JSONB, default={}, nullable=False)
    last_evaluation = Column(DateTime, nullable=True)
    rule_count = Column(Integer, default=0, nullable=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.business_rules = {}
        self.rule_conditions = {}
        self.rule_actions = {}
        self.rule_priorities = {}
        self.rule_metadata = {}
        self._engine = RuleEngine()

    def register_rule(self, name: str, condition: Callable, action: Callable,
                     priority: int = 0, metadata: Optional[Dict] = None,
                     async_execution: bool = False, retry_count: int = 3,
                     timeout: Optional[int] = None) -> None:
        """
        Register a new business rule.

        Args:
            name: Rule identifier
            condition: Rule condition function
            action: Rule action function
            priority: Rule priority (higher = higher priority)
            metadata: Additional rule metadata
            async_execution: Execute action asynchronously
            retry_count: Number of retry attempts
            timeout: Action timeout in seconds
        """
        self.business_rules[name] = {
            'condition': condition,
            'action': action,
            'priority': priority,
            'metadata': metadata or {},
            'async': async_execution,
            'retry_count': retry_count,
            'timeout': timeout,
            'created_at': datetime.utcnow()
        }

        # Update metadata
        self.rules_metadata.update({
            name: {
                'priority': priority,
                'metadata': metadata or {},
                'created_at': datetime.utcnow().isoformat()
            }
        })

    def get_rule(self, name: str) -> Optional[Dict]:
        """Get a registered rule by name."""
        return self.business_rules.get(name)

    def list_rules(self, include_metadata: bool = False) -> List[Dict]:
        """
        List all registered rules.

        Args:
            include_metadata: Include rule metadata in results

        Returns:
            list: Registered rules
        """
        rules = list(self.business_rules.keys())
        if include_metadata:
            return [{
                'name': name,
                'metadata': self.rules_metadata.get(name, {})
            } for name in rules]
        return rules

    async def evaluate_rule(self, name: str, context: Optional[Dict] = None,
                          raise_errors: bool = False) -> Any:
        """
        Evaluate a single rule.

        Args:
            name: Rule name to evaluate
            context: Evaluation context
            raise_errors: Raise or suppress errors

        Returns:
            Any: Rule evaluation result

        Raises:
            ValueError: If rule not found
            RuleEvaluationError: If evaluation fails
        """
        rule = self.get_rule(name)
        if not rule:
            raise ValueError(f"Rule {name} not found")

        context = context or {}
        try:
            if rule['condition'](self, context):
                if rule['async']:
                    return await self._execute_async_action(rule, context)
                return rule['action'](self, context)

        except Exception as e:
            logger.error(f"Rule evaluation error: {str(e)}")
            if raise_errors:
                raise RuleEvaluationError(str(e))
            return None
        finally:
            self._update_evaluation_stats(name)

    async def evaluate_all_rules(self, context: Optional[Dict] = None,
                               raise_errors: bool = False) -> List[tuple]:
        """
        Evaluate all rules in priority order.

        Args:
            context: Evaluation context
            raise_errors: Raise or suppress errors

        Returns:
            list: Rule results as (name, result) tuples
        """
        context = context or {}
        results = []

        sorted_rules = sorted(
            self.business_rules.items(),
            key=lambda x: x[1]['priority'],
            reverse=True
        )

        for name, rule in sorted_rules:
            try:
                result = await self.evaluate_rule(name, context, raise_errors)
                if result is not None:
                    results.append((name, result))
            except Exception as e:
                logger.error(f"Rule evaluation error: {str(e)}")
                if raise_errors:
                    raise

        return results

    async def _execute_async_action(self, rule: Dict, context: Dict) -> Any:
        """Execute rule action asynchronously with retry logic."""
        for attempt in range(rule['retry_count']):
            try:
                if rule['timeout']:
                    async with asyncio.timeout(rule['timeout']):
                        return await rule['action'](self, context)
                return await rule['action'](self, context)
            except Exception as e:
                if attempt == rule['retry_count'] - 1:
                    raise
                logger.warning(f"Retry attempt {attempt + 1} for {rule}: {str(e)}")
                await asyncio.sleep(min(2 ** attempt, 30))

    def _update_evaluation_stats(self, rule_name: str) -> None:
        """Update rule evaluation statistics."""
        self.last_evaluation = datetime.utcnow()
        self.rule_count += 1
        self.rules_metadata[rule_name]['last_evaluation'] = self.last_evaluation.isoformat()
        self.rules_metadata[rule_name]['evaluation_count'] = \
            self.rules_metadata[rule_name].get('evaluation_count', 0) + 1

class BusinessRule:
    """
    Represents a business rule definition with conditions and actions.

    Attributes:
        name: Rule identifier
        description: Rule description
        conditions: List of rule conditions
        actions: List of rule actions
        priority: Rule priority
        metadata: Additional metadata
        async_execution: Execute actions asynchronously
        retry_policy: Retry configuration
    """

    def __init__(self, name: str, description: Optional[str] = None,
                 async_execution: bool = False,
                 retry_policy: Optional[Dict] = None):
        self.name = name
        self.description = description
        self.conditions = []
        self.actions = []
        self.priority = 0
        self.metadata = {}
        self.async_execution = async_execution
        self.retry_policy = retry_policy or {
            'max_retries': 3,
            'delay': 1,
            'backoff': 2
        }
        self.created_at = datetime.utcnow()

    def add_condition(self, condition: 'RuleCondition') -> 'BusinessRule':
        """Add a condition to the rule."""
        self.conditions.append(condition)
        return self

    def add_action(self, action: 'RuleAction') -> 'BusinessRule':
        """Add an action to the rule."""
        self.actions.append(action)
        return self

    def set_priority(self, priority: int) -> 'BusinessRule':
        """Set rule priority."""
        self.priority = priority
        return self

    def set_metadata(self, metadata: Dict) -> 'BusinessRule':
        """Set rule metadata."""
        self.metadata = metadata
        return self

    async def evaluate(self, context: Dict) -> bool:
        """
        Evaluate rule conditions.

        Args:
            context: Evaluation context

        Returns:
            bool: True if all conditions met
        """
        try:
            return all(await condition(context) for condition in self.conditions)
        except Exception as e:
            logger.error(f"Rule evaluation error: {str(e)}")
            return False

    async def execute(self, context: Dict) -> List[Any]:
        """
        Execute rule actions.

        Args:
            context: Execution context

        Returns:
            list: Action results
        """
        results = []
        for action in self.actions:
            try:
                if self.async_execution:
                    result = await self._execute_with_retry(action, context)
                else:
                    result = action(context)
                results.append(result)
            except Exception as e:
                logger.error(f"Action execution error: {str(e)}")
                raise
        return results

    async def _execute_with_retry(self, action: 'RuleAction',
                                context: Dict) -> Any:
        """Execute action with retry logic."""
        max_retries = self.retry_policy['max_retries']
        delay = self.retry_policy['delay']
        backoff = self.retry_policy['backoff']

        for attempt in range(max_retries):
            try:
                return await action(context)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(delay * (backoff ** attempt))

class RuleEngine:
    """
    Business rules execution engine.

    Attributes:
        rules: Registered rules
        context: Execution context
        listeners: Event listeners
        metrics: Performance metrics
    """

    def __init__(self):
        self.rules = {}
        self.context = {}
        self.listeners = []
        self.metrics = {
            'total_executions': 0,
            'total_errors': 0,
            'execution_times': []
        }

    def register_rule(self, rule: BusinessRule) -> 'RuleEngine':
        """Register a business rule."""
        self.rules[rule.name] = rule
        return self

    def set_context(self, context: Dict) -> 'RuleEngine':
        """Set execution context."""
        self.context = context
        return self

    def add_listener(self, listener: 'RuleListener') -> 'RuleEngine':
        """Add rule execution listener."""
        self.listeners.append(listener)
        return self

    async def evaluate_rule(self, rule_name: str) -> Optional[List[Any]]:
        """
        Evaluate a single rule.

        Args:
            rule_name: Rule to evaluate

        Returns:
            list: Rule results if conditions met

        Raises:
            ValueError: If rule not found
        """
        start_time = datetime.utcnow()

        try:
            rule = self.rules.get(rule_name)
            if not rule:
                raise ValueError(f"Rule {rule_name} not found")

            # Check conditions
            conditions_met = await rule.evaluate(self.context)

            if conditions_met:
                # Execute actions
                results = await rule.execute(self.context)

                self._notify_listeners('rule_executed', {
                    'rule': rule,
                    'results': results,
                    'duration': datetime.utcnow() - start_time
                })

                return results

            return None

        except Exception as e:
            self.metrics['total_errors'] += 1
            self._notify_listeners('evaluation_error', {
                'rule': rule,
                'error': e
            })
            raise
        finally:
            duration = datetime.utcnow() - start_time
            self.metrics['total_executions'] += 1
            self.metrics['execution_times'].append(duration.total_seconds())

    async def evaluate_all(self) -> Dict[str, Any]:
        """
        Evaluate all rules.

        Returns:
            dict: Results by rule name
        """
        results = {}

        # Sort rules by priority
        sorted_rules = sorted(
            self.rules.values(),
            key=lambda r: r.priority,
            reverse=True
        )

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
                raise

        return results

    def get_metrics(self) -> Dict[str, Any]:
        """Get engine performance metrics."""
        return {
            **self.metrics,
            'avg_execution_time': (
                sum(self.metrics['execution_times']) /
                len(self.metrics['execution_times'])
                if self.metrics['execution_times'] else 0
            ),
            'error_rate': (
                self.metrics['total_errors'] / self.metrics['total_executions']
                if self.metrics['total_executions'] else 0
            )
        }

    def _notify_listeners(self, event: str, data: Dict) -> None:
        """Notify rule execution listeners."""
        for listener in self.listeners:
            try:
                listener(event, data)
            except Exception as e:
                logger.error(f"Listener error: {str(e)}")

class RuleCondition:
    """
    Represents a business rule condition.

    Attributes:
        condition_func: Condition evaluation function
        description: Condition description
        metadata: Additional metadata
    """

    def __init__(self, condition_func: Callable,
                 description: Optional[str] = None,
                 metadata: Optional[Dict] = None):
        self.condition_func = condition_func
        self.description = description
        self.metadata = metadata or {}

    async def __call__(self, context: Dict) -> bool:
        """Evaluate condition."""
        if asyncio.iscoroutinefunction(self.condition_func):
            return await self.condition_func(context)
        return self.condition_func(context)

    @staticmethod
    def all(*conditions: 'RuleCondition') -> 'RuleCondition':
        """
        Combine conditions with AND logic.

        Args:
            *conditions: Conditions to combine

        Returns:
            RuleCondition: Combined condition
        """
        async def combined_condition(context):
            results = await asyncio.gather(
                *(c(context) for c in conditions)
            )
            return all(results)
        return RuleCondition(combined_condition)

    @staticmethod
    def any(*conditions: 'RuleCondition') -> 'RuleCondition':
        """
        Combine conditions with OR logic.

        Args:
            *conditions: Conditions to combine

        Returns:
            RuleCondition: Combined condition
        """
        async def combined_condition(context):
            results = await asyncio.gather(
                *(c(context) for c in conditions)
            )
            return any(results)
        return RuleCondition(combined_condition)

class RuleAction:
    """
    Represents a business rule action.

    Attributes:
        action_func: Action execution function
        description: Action description
        metadata: Additional metadata
        timeout: Execution timeout
    """

    def __init__(self, action_func: Callable,
                 description: Optional[str] = None,
                 metadata: Optional[Dict] = None,
                 timeout: Optional[int] = None):
        self.action_func = action_func
        self.description = description
        self.metadata = metadata or {}
        self.timeout = timeout

    async def __call__(self, context: Dict) -> Any:
        """Execute action."""
        if self.timeout:
            async with asyncio.timeout(self.timeout):
                if asyncio.iscoroutinefunction(self.action_func):
                    return await self.action_func(context)
                return self.action_func(context)
        else:
            if asyncio.iscoroutinefunction(self.action_func):
                return await self.action_func(context)
            return self.action_func(context)

    @staticmethod
    def sequence(*actions: 'RuleAction') -> 'RuleAction':
        """
        Execute actions in sequence.

        Args:
            *actions: Actions to execute

        Returns:
            RuleAction: Sequential action
        """
        async def sequence_action(context):
            results = []
            for action in actions:
                result = await action(context)
                results.append(result)
            return results
        return RuleAction(sequence_action)

    @staticmethod
    def parallel(*actions: 'RuleAction') -> 'RuleAction':
        """
        Execute actions in parallel.

        Args:
            *actions: Actions to execute

        Returns:
            RuleAction: Parallel action
        """
        async def parallel_action(context):
            return await asyncio.gather(
                *(action(context) for action in actions)
            )
        return RuleAction(parallel_action)

class RuleListener:
    """
    Base class for rule execution listeners.

    Methods:
        on_rule_executed: Handle rule execution
        on_action_error: Handle action errors
        on_evaluation_error: Handle evaluation errors
    """

    def __call__(self, event: str, data: Dict) -> None:
        """Handle rule event."""
        method = getattr(self, f"on_{event}", None)
        if method:
            method(data)

    def on_rule_executed(self, data: Dict) -> None:
        """
        Handle rule execution event.

        Args:
            data: Event data including rule, results, duration
        """
        pass

    def on_action_error(self, data: Dict) -> None:
        """
        Handle action error event.

        Args:
            data: Event data including rule, error
        """
        pass

    def on_evaluation_error(self, data: Dict) -> None:
        """
        Handle evaluation error event.

        Args:
            data: Event data including rule, error
        """
        pass

class RuleEvaluationError(Exception):
    """Raised when rule evaluation fails."""
    pass

"""
# Example Usage:
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

class Order(BusinessRuleMixin, Model):
    """Order model with advanced business rules."""

    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'))
    total = Column(Float, nullable=False)
    status = Column(String(50), default='new')
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    customer = relationship('Customer', backref='orders')

    def __init__(self):
        super().__init__()
        self.setup_rules()

    def setup_rules(self):
        """Setup business rules with advanced features."""
        # VIP customer rule with parallel actions
        self.register_rule(
            'vip_processing',
            condition=lambda obj, ctx: obj.customer.is_vip,
            action=RuleAction.parallel(
                RuleAction(lambda ctx: ctx['order'].apply_discount(0.2)),
                RuleAction(lambda ctx: ctx['order'].expedite_shipping()),
                RuleAction(lambda ctx: ctx['order'].add_gift())
            ),
            priority=10,
            metadata={
                'description': 'VIP customer order processing',
                'category': 'customer_service'
            },
            async_execution=True
        )

        # High value order rule with sequential actions
        self.register_rule(
            'high_value_order',
            condition=RuleCondition.all(
                RuleCondition(lambda ctx: ctx['order'].total > 1000),
                RuleCondition(lambda ctx: ctx['order'].items_count > 5)
            ),
            action=RuleAction.sequence(
                RuleAction(lambda ctx: ctx['order'].apply_discount(0.15)),
                RuleAction(lambda ctx: ctx['order'].add_loyalty_points(500)),
                RuleAction(lambda ctx: ctx['order'].schedule_followup())
            ),
            priority=5,
            metadata={'category': 'sales'}
        )

# Enhanced rule engine setup
engine = RuleEngine()

# Complex condition combining multiple checks
premium_customer = RuleCondition(
    lambda ctx: ctx['customer'].tier == 'premium',
    description="Check if customer is premium"
)
large_order = RuleCondition(
    lambda ctx: ctx['order'].total > 1000,
    description="Check if order is large"
)
repeat_customer = RuleCondition(
    lambda ctx: ctx['customer'].order_count > 5,
    description="Check if customer is repeat"
)

# Complex actions with error handling
async def apply_discount(ctx):
    """Apply discount with validation."""
    order = ctx['order']
    if order.can_apply_discount():
        return await order.apply_discount(0.15)
    raise ValueError("Cannot apply discount")

async def add_bonus_points(ctx):
    """Add bonus points with notification."""
    customer = ctx['customer']
    points = await customer.add_points(100)
    await customer.notify_points_added(points)
    return points

# Create complex rule with async execution
premium_rule = BusinessRule(
    "premium_treatment",
    "Special handling for premium customers",
    async_execution=True
)
premium_rule.add_condition(
    RuleCondition.all(premium_customer, large_order)
)
premium_rule.add_action(
    RuleAction.parallel(
        RuleAction(apply_discount, timeout=5),
        RuleAction(add_bonus_points, timeout=3),
        RuleAction(lambda ctx: ctx['order'].add_free_gift())
    )
)
premium_rule.set_priority(10)

# Add enhanced audit logging
class AuditLogger(RuleListener):
    """Advanced audit logging for rule execution."""

    def on_rule_executed(self, data):
        """Log successful rule execution with metrics."""
        rule = data['rule']
        results = data['results']
        duration = data['duration']
        logger.info(
            f"Rule {rule.name} executed successfully in {duration.total_seconds():.2f}s "
            f"with results: {results}"
        )

    def on_action_error(self, data):
        """Log action errors with context."""
        rule = data['rule']
        error = data['error']
        logger.error(
            f"Action error in rule {rule.name}: {str(error)}",
            extra={
                'rule_name': rule.name,
                'error_type': type(error).__name__,
                'timestamp': datetime.utcnow().isoformat()
            }
        )

# Register components
engine.register_rule(premium_rule)
engine.add_listener(AuditLogger())

# Example async execution
async def process_order(order):
    """Process order with rule engine."""
    try:
        engine.set_context({
            'order': order,
            'customer': order.customer
        })
        results = await engine.evaluate_all()

        # Get execution metrics
        metrics = engine.get_metrics()
        logger.info(
            f"Order processing completed with {len(results)} rules executed. "
            f"Avg execution time: {metrics['avg_execution_time']:.2f}s"
        )

        return results
    except Exception as e:
        logger.error(f"Order processing failed: {str(e)}")
        raise
""" +

"""
Here's a list of key files and their contents to implement this advanced workflow system:

```
src/
├── workflow/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── base.py           # Base classes and interfaces
│   │   ├── state.py          # State implementations
│   │   ├── transition.py     # Transition implementations
│   │   └── workflow.py       # Workflow engine
│   ├── gateways/
│   │   ├── __init__.py
│   │   ├── exclusive.py      # XOR gateway
│   │   ├── inclusive.py      # OR gateway
│   │   └── parallel.py       # AND gateway
│   ├── events/
│   │   ├── __init__.py
│   │   ├── timer.py         # Timer events
│   │   ├── message.py       # Message events
│   │   └── signal.py        # Signal events
│   ├── data/
│   │   ├── __init__.py
│   │   ├── variables.py     # Workflow variables
│   │   ├── objects.py       # Data objects
│   │   └── storage.py       # Data storage backends
│   ├── rules/
│   │   ├── __init__.py
│   │   ├── engine.py        # Rules engine
│   │   └── dsl.py          # Rule definition DSL
│   ├── process/
│   │   ├── __init__.py
│   │   ├── instance.py     # Process instances
│   │   └── monitor.py      # Process monitoring
│   ├── error/
│   │   ├── __init__.py
│   │   ├── boundary.py     # Error boundaries
│   │   └── handler.py      # Error handlers
│   └── utils/
│       ├── __init__.py
│       ├── visualization.py # Diagram generation
│       └── serialization.py # Import/export
└── tests/
    └── workflow/
        ├── test_core.py
        ├── test_gateways.py
        ├── test_events.py
        └── test_rules.py


"""
