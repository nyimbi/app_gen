"""
state_machine_mixin.py: Comprehensive State Machine Mixin for Flask-AppBuilder

This module provides a robust StateMachineMixin for use with SQLAlchemy models in Flask-AppBuilder applications.
It implements a flexible state machine with workflow capabilities, including complex state transitions,
event handling, notifications, and integration with Flask-AppBuilder's security model.

Key Features:
- Flexible state and transition definitions
- Complex workflow support with branching and sub-workflows
- Comprehensive event system with synchronous and asynchronous processing
- Multiple notification channels (email, SMS, signals, flash messages)
- Detailed audit trail and history tracking
- Visualization and reporting capabilities
- Time-based transitions and scheduling
- Extensible architecture for custom plugins and integrations

Classes:
- StateMachineMixin: Main mixin class to be used with SQLAlchemy models
- State: Represents a single state in the state machine
- Transition: Defines a transition between states
- Workflow: Represents a complete workflow with multiple states and transitions
- NotificationManager: Handles various types of notifications
- HistoryManager: Manages the state change history and audit trail

Usage:
    from state_machine_mixin import StateMachineMixin

    class MyModel(StateMachineMixin, db.Model):
        __tablename__ = 'my_model'
        id = db.Column(db.Integer, primary_key=True)

        # Define states
        states = [
            State('draft', initial=True),
            State('review'),
            State('published'),
            State('archived')
        ]

        # Define transitions
        transitions = [
            Transition('submit', 'draft', 'review'),
            Transition('approve', 'review', 'published'),
            Transition('reject', 'review', 'draft'),
            Transition('archive', 'published', 'archived')
        ]

        # Define a workflow
        workflow = Workflow('content_workflow', states, transitions)

Dependencies:
- Flask-AppBuilder
- SQLAlchemy
- Flask-Mail (for email notifications)
- Twilio (for SMS notifications)
- GraphViz (for state machine visualization)

Note: Ensure all dependencies are installed and properly configured in your Flask application.
"""

from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from flask_appbuilder.models.decorators import renders
from flask_appbuilder.security.sqla.models import User
from flask import current_app, flash
from flask_mail import Message
from twilio.rest import Client
from blinker import signal
import graphviz
from datetime import datetime, timedelta
import json
import yaml
import xml.etree.ElementTree as ET
import os
from sqlalchemy import Column, String, Text


class State:
    """
    Represents a state in the state machine.

    Attributes:
        name (str): The name of the state.
        description (str): A description of the state.
        metadata (dict): Additional metadata associated with the state.
        is_initial (bool): Whether this is the initial state.
        is_final (bool): Whether this is a final state.
        is_restricted (bool): Whether this state has restricted access.
    """

    def __init__(self, name, description="", metadata=None, is_initial=False, is_final=False, is_restricted=False):
        self.name = name
        self.description = description
        self.metadata = metadata or {}
        self.is_initial = is_initial
        self.is_final = is_final
        self.is_restricted = is_restricted


class Transition:
    """
    Represents a transition between states.

    Attributes:
        trigger (str): The event that triggers this transition.
        source (str or list): The source state(s) for this transition.
        dest (str): The destination state for this transition.
        conditions (list): List of conditions that must be met for the transition.
        before (list): List of callbacks to be executed before the transition.
        after (list): List of callbacks to be executed after the transition.
        priority (int): Priority of this transition (higher numbers have higher priority).
    """

    def __init__(self, trigger, source, dest, conditions=None, before=None, after=None, priority=0):
        self.trigger = trigger
        self.source = source if isinstance(source, list) else [source]
        self.dest = dest
        self.conditions = conditions or []
        self.before = before or []
        self.after = after or []
        self.priority = priority


class Workflow:
    """
    Represents a complete workflow with states and transitions.

    Attributes:
        name (str): The name of the workflow.
        states (list): List of State objects in this workflow.
        transitions (list): List of Transition objects in this workflow.
        sub_workflows (list): List of sub-workflows within this workflow.
    """

    def __init__(self, name, states, transitions, sub_workflows=None):
        self.name = name
        self.states = states
        self.transitions = transitions
        self.sub_workflows = sub_workflows or []


class NotificationManager:
    """
    Manages notifications for state changes and events.

    Methods:
        send_email: Sends an email notification.
        send_sms: Sends an SMS notification.
        send_signal: Sends a Flask-Blinker signal.
        flash_message: Displays a flash message in the Flask-AppBuilder app.
    """

    @staticmethod
    def send_email(subject, recipients, body):
        """
        Sends an email notification.

        Args:
            subject (str): The subject of the email.
            recipients (list): List of email addresses to send the notification to.
            body (str): The body of the email.
        """
        msg = Message(subject, recipients=recipients, body=body)
        current_app.extensions['mail'].send(msg)

    @staticmethod
    def send_sms(to, body):
        """
        Sends an SMS notification.

        Args:
            to (str): The phone number to send the SMS to.
            body (str): The body of the SMS.
        """
        client = Client(current_app.config['TWILIO_ACCOUNT_SID'], current_app.config['TWILIO_AUTH_TOKEN'])
        client.messages.create(to=to, from_=current_app.config['TWILIO_PHONE_NUMBER'], body=body)

    @staticmethod
    def send_signal(signal_name, sender, **kwargs):
        """
        Sends a Flask-Blinker signal.

        Args:
            signal_name (str): The name of the signal to send.
            sender: The sender of the signal.
            **kwargs: Additional keyword arguments to pass with the signal.
        """
        custom_signal = signal(signal_name)
        custom_signal.send(sender, **kwargs)

    @staticmethod
    def flash_message(message, category="info"):
        """
        Displays a flash message in the Flask-AppBuilder app.

        Args:
            message (str): The message to display.
            category (str): The category of the message (e.g., "info", "error", "warning").
        """
        flash(message, category)


class HistoryManager:
    """
    Manages the history of state changes and provides an audit trail.

    Methods:
        add_entry: Adds a new entry to the state change history.
        get_history: Retrieves the state change history for a given instance.
        revert_to_state: Reverts an instance to a previous state.
    """

    @staticmethod
    def add_entry(instance, from_state, to_state, user, reason=None):
        """
        Adds a new entry to the state change history.

        Args:
            instance: The instance that changed state.
            from_state (str): The previous state.
            to_state (str): The new state.
            user: The user who initiated the state change.
            reason (str, optional): The reason for the state change.
        """
        entry = StateChangeHistory(
            model_id=instance.id,
            model_type=instance.__class__.__name__,
            from_state=from_state,
            to_state=to_state,
            changed_by=user.id,
            changed_at=datetime.utcnow(),
            reason=reason
        )
        db.session.add(entry)
        db.session.commit()

    @staticmethod
    def get_history(instance):
        """
        Retrieves the state change history for a given instance.

        Args:
            instance: The instance to get the history for.

        Returns:
            list: A list of StateChangeHistory objects.
        """
        return StateChangeHistory.query.filter_by(
            model_id=instance.id,
            model_type=instance.__class__.__name__
        ).order_by(StateChangeHistory.changed_at.desc()).all()

    @staticmethod
    def revert_to_state(instance, target_state, user, reason=None):
        """
        Reverts an instance to a previous state.

        Args:
            instance: The instance to revert.
            target_state (str): The state to revert to.
            user: The user initiating the revert action.
            reason (str, optional): The reason for reverting.

        Raises:
            ValueError: If the target state is not in the instance's history.
        """
        history = HistoryManager.get_history(instance)
        if not any(entry.to_state == target_state for entry in history):
            raise ValueError(f"Target state '{target_state}' not found in instance history.")

        current_state = instance.state
        instance.state = target_state
        HistoryManager.add_entry(instance, current_state, target_state, user, reason or "State reverted")
        db.session.commit()


class StateChangeHistory(Model):
    """
    Model to store the history of state changes.

    Attributes:
        id (int): The primary key of the history entry.
        model_id (int): The ID of the model instance that changed state.
        model_type (str): The type of the model that changed state.
        from_state (str): The previous state.
        to_state (str): The new state.
        changed_by (int): The ID of the user who initiated the state change.
        changed_at (datetime): The timestamp of the state change.
        reason (str): The reason for the state change.
    """

    __tablename__ = 'state_change_history'

    id = Column(Integer, primary_key=True)
    model_id = Column(Integer, nullable=False)
    model_type = Column(String(100), nullable=False)
    from_state = Column(String(50), nullable=False)
    to_state = Column(String(50), nullable=False)
    changed_by = Column(Integer, ForeignKey('ab_user.id'), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    reason = Column(String(255))

    user = relationship(User, foreign_keys=[changed_by])


class StateMachineMixin:
    """
    A mixin that adds state machine functionality to SQLAlchemy models.

    This mixin provides comprehensive state machine capabilities, including:
    - State and transition management
    - Workflow definition and execution
    - Event handling and processing
    - Notification system integration
    - History tracking and audit trail
    - Visualization and reporting

    Attributes:
        state (Column): The current state of the instance.
        workflow (Workflow): The workflow definition for this model.

    Methods:
        trigger_event: Triggers a state transition event.
        can_transition: Checks if a transition is possible.
        get_available_transitions: Gets all available transitions from the current state.
        visualize: Generates a visual representation of the state machine.
        export_definition: Exports the state machine definition in various formats.
    """
    mermaid_diagram = Column(Text)  # New column to store the Mermaid diagram

    @declared_attr
    def state(cls):
        return Column(String(50), nullable=False)



    @classmethod
    def _validate_workflow(cls):
        """
        Validates the workflow definition for the model.

        Raises:
            ValueError: If the workflow definition is invalid.
        """
        if not isinstance(cls.workflow, Workflow):
            raise ValueError(f"'workflow' must be an instance of Workflow in {cls.__name__}")

        # Validate states and transitions
        state_names = {state.name for state in cls.workflow.states}
        for transition in cls.workflow.transitions:
            if not set(transition.source).issubset(state_names):
                raise ValueError(f"Invalid source state(s) in transition {transition.trigger}")
            if transition.dest not in state_names:
                raise ValueError(f"Invalid destination state in transition {transition.trigger}")

    @classmethod
    def _setup_event_listeners(cls):
        """
        Sets up SQLAlchemy event listeners for the model.
        """

        @event.listens_for(cls, 'before_insert')
        def set_initial_state(mapper, connection, target):
            if not target.state:
                initial_state = next((state for state in cls.workflow.states if state.is_initial), None)
                if initial_state:
                    target.state = initial_state.name
                else:
                    raise ValueError(f"No initial state defined for {cls.__name__}")

    def trigger_event(self, event, user, reason=None):
        """
        Triggers a state transition event.

        Args:
            event (str): The name of the event to trigger.
            user: The user triggering the event.
            reason (str, optional): The reason for the state change.

        Returns:
            bool: True if the transition was successful, False otherwise.

        Raises:
            ValueError: If the event is not valid for the current state.
        """
        transition = self._get_transition(event)
        if not transition:
            raise ValueError(f"Invalid event '{event}' for current state '{self.state}'")

        if not self.can_transition(transition, user):
            return False

        self._execute_transition(transition, user, reason)
        return True

    def _get_transition(self, event):
        """
        Gets the transition object for the given event.

        Args:
            event (str): The name of the event.

        Returns:
            Transition: The transition object, or None if not found.
        """
        return next((t for t in self.workflow.transitions
                     if t.trigger == event and self.state in t.source), None)

    def can_transition(self, transition, user):
        """
        Checks if a transition is possible.

        Args:
            transition (Transition): The transition to check.
            user: The user attempting the transition.

        Returns:
            bool: True if the transition is possible, False otherwise.
        """
        if self.state not in transition.source:
            return False

        for condition in transition.conditions:
            if not condition(self, user):
                return False

        return True

    def _execute_transition(self, transition, user, reason=None):
        """
        Executes a state transition.

        Args:
            transition (Transition): The transition to execute.
            user: The user executing the transition.
            reason (str, optional): The reason for the state change.
        """
        from_state = self.state
        to_state = transition.dest

        for callback in transition.before:
            callback(self, user)

        self.state = to_state
        db.session.commit()

        for callback in transition.after:
            callback(self, user)

        HistoryManager.add_entry(self, from_state, to_state, user, reason)
        self._send_notifications(from_state, to_state, user)

    def _send_notifications(self, from_state, to_state, user):
        """
        Sends notifications for a state change.

        Args:
            from_state (str): The previous state.
            to_state (str): The new state.
            user: The user who initiated the state change.
        """
        subject = f"State changed from {from_state} to {to_state}"
        body = f"The state of {self.__class__.__name__} (ID: {self.id}) has changed."

        NotificationManager.send_email(subject, [user.email], body)
        NotificationManager.send_signal('state_changed', self, from_state=from_state, to_state=to_state, user=user)
        NotificationManager.flash_message(f"State changed to {to_state}", "info")

    def get_available_transitions(self, user):
        """
        Gets all available transitions from the current state.

        Args:
            user: The user to check permissions against.

        Returns:
            list: A list of available Transition objects.
        """
        return [t for t in self.workflow.transitions
                if self.state in t.source and self.can_transition(t, user)]

    def visualize(self, filename='state_machine'):
        """
        Generates a visual representation of the state machine.

        Args:
            filename (str): The filename to save the visualization (without extension).

        Returns:
            str: The path to the generated visualization file.
        """
        dot = graphviz.Digraph(comment=f'State Machine for {self.__class__.__name__}')

        for state in self.workflow.states:
            dot.node(state.name, state.name)

        for transition in self.workflow.transitions:
            for source in transition.source:
                dot.edge(source, transition.dest, label=transition.trigger)

        dot.render(filename, view=True)
        return f"{filename}.pdf"

    def export_definition(self, format='json'):
        """
        Exports the state machine definition in various formats.

        Args:
            format (str): The export format ('json', 'yaml', or 'xml').

        Returns:
            str: The state machine definition in the specified format.

        Raises:
            ValueError: If an unsupported format is specified.
        """
        definition = {
            'states': [{'name': s.name, 'initial': s.is_initial, 'final': s.is_final}
                       for s in self.workflow.states],
            'transitions': [{'trigger': t.trigger, 'source': t.source, 'dest': t.dest}
                            for t in self.workflow.transitions]
        }

        if format == 'json':
            return json.dumps(definition, indent=2)
        elif format == 'yaml':
            return yaml.dump(definition)
        elif format == 'xml':
            root = ET.Element('state-machine')
            states = ET.SubElement(root, 'states')
            for state in definition['states']:
                state_elem = ET.SubElement(states, 'state')
                for key, value in state.items():
                    state_elem.set(key, str(value))
            transitions = ET.SubElement(root, 'transitions')
            for transition in definition['transitions']:
                trans_elem = ET.SubElement(transitions, 'transition')
                for key, value in transition.items():
                    if isinstance(value, list):
                        value = ','.join(value)
                    trans_elem.set(key, str(value))
            return ET.tostring(root, encoding='unicode', method='xml')
        else:
            raise ValueError(f"Unsupported export format: {format}")

    @classmethod
    def get_state_counts(cls):
        """
        Gets the count of instances in each state.

        Returns:
            dict: A dictionary with state names as keys and counts as values.
        """
        return db.session.query(cls.state, func.count(cls.id)).group_by(cls.state).all()

    def schedule_transition(self, event, user, execute_at):
        """
        Schedules a state transition to occur at a specified time.

        Args:
            event (str): The name of the event to trigger.
            user: The user scheduling the transition.
            execute_at (datetime): The time at which to execute the transition.

        Returns:
            ScheduledTransition: The scheduled transition object.
        """
        scheduled = ScheduledTransition(
            model_id=self.id,
            model_type=self.__class__.__name__,
            event=event,
            user_id=user.id,
            execute_at=execute_at
        )
        db.session.add(scheduled)
        db.session.commit()
        return scheduled

    def generate_mermaid_diagram(self):
        """
        Generates a Mermaid sequence diagram representation of the state machine.

        Returns:
            str: Mermaid code for the sequence diagram.
        """
        mermaid_code = ["sequenceDiagram"]

        # Add participants (states)
        for state in self.workflow.states:
            mermaid_code.append(f"    participant {state.name}")

        # Add transitions
        for transition in self.workflow.transitions:
            for source in transition.source:
                mermaid_code.append(f"    {source}->>+{transition.dest}: {transition.trigger}")
                mermaid_code.append(f"    {transition.dest}-->>-{source}: ")  # Empty return arrow for visual balance

        return "\n".join(mermaid_code)

    def update_mermaid_diagram(self):
        """
        Updates the stored Mermaid diagram representation.
        """
        self.mermaid_diagram = self.generate_mermaid_diagram()
        db.session.commit()

    def get_mermaid_diagram(self):
        """
        Retrieves the stored Mermaid diagram representation.
        If not available, generates and stores a new one.

        Returns:
            str: Mermaid code for the sequence diagram.
        """
        if not self.mermaid_diagram:
            self.update_mermaid_diagram()
        return self.mermaid_diagram

    def export_mermaid_diagram(self, filename='state_machine_diagram.md'):
        """
        Exports the Mermaid diagram to a Markdown file.

        Args:
            filename (str): The name of the file to save the diagram to.

        Returns:
            str: The path to the saved file.
        """
        diagram = self.get_mermaid_diagram()
        file_path = os.path.join(current_app.config['EXPORT_FOLDER'], filename)

        with open(file_path, 'w') as f:
            f.write("```mermaid\n")
            f.write(diagram)
            f.write("\n```")

        return file_path

    @classmethod
    def __declare_last__(cls):
        if not hasattr(cls, 'workflow'):
            raise AttributeError(f"StateMachineMixin requires a 'workflow' attribute to be defined on {cls.__name__}")

        cls._validate_workflow()
        cls._setup_event_listeners()

        # Generate and store the initial Mermaid diagram
        @event.listens_for(cls, 'after_insert')
        def generate_initial_diagram(mapper, connection, target):
            target.update_mermaid_diagram()




class ScheduledTransition(Model):
    """
    Model to store scheduled state transitions.

    Attributes:
        id (int): The primary key of the scheduled transition.
        model_id (int): The ID of the model instance to transition.
        model_type (str): The type of the model to transition.
        event (str): The event to trigger for the transition.
        user_id (int): The ID of the user who scheduled the transition.
        execute_at (datetime): The time at which to execute the transition.
        executed (bool): Whether the transition has been executed.
    """

    __tablename__ = 'scheduled_transitions'

    id = Column(Integer, primary_key=True)
    model_id = Column(Integer, nullable=False)
    model_type = Column(String(100), nullable=False)
    event = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey('ab_user.id'), nullable=False)
    execute_at = Column(DateTime, nullable=False)
    executed = Column(Boolean, default=False)

    user = relationship(User, foreign_keys=[user_id])


# Setup Flask-APScheduler job to execute scheduled transitions
@scheduler.task('cron', id='execute_scheduled_transitions', minute='*')
def execute_scheduled_transitions():
    """
    Executes all pending scheduled transitions.
    """
    now = datetime.utcnow()
    scheduled = ScheduledTransition.query.filter(
        ScheduledTransition.execute_at <= now,
        ScheduledTransition.executed == False
    ).all()

    for transition in scheduled:
        model_class = db.Model._decl_class_registry.get(transition.model_type)
        if not model_class:
            continue

        instance = model_class.query.get(transition.model_id)
        if not instance:
            continue

        try:
            instance.trigger_event(transition.event, transition.user)
            transition.executed = True
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Error executing scheduled transition: {str(e)}")


# Example usage
# class MyModel(StateMachineMixin, Model):
#     __tablename__ = 'my_model'
#     id = Column(Integer, primary_key=True)
#     name = Column(String(100))
#
#     workflow = Workflow(
#         'my_workflow',
#         states=[
#             State('draft', is_initial=True),
#             State('review'),
#             State('published'),
#             State('archived', is_final=True)
#         ],
#         transitions=[
#             Transition('submit', 'draft', 'review'),
#             Transition('approve', 'review', 'published'),
#             Transition('reject', 'review', 'draft'),
#             Transition('archive', 'published', 'archived')
#         ]
#     )
#
#     def __repr__(self):
#         return f'<MyModel {self.id}: {self.name} ({self.state})>'