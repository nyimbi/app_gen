"""
workflow_mixin.py

This module provides a WorkflowMixin class for implementing basic workflow
capabilities in SQLAlchemy models for Flask-AppBuilder applications.

The WorkflowMixin allows for defining states, transitions between states,
and actions to be performed on state changes. It also provides functionality
for tracking the history of state changes and visualizing the workflow.

Dependencies:
    - SQLAlchemy
    - Flask-AppBuilder
    - graphviz (for workflow visualization)

Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.0
"""

from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, event
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from datetime import datetime
import json
import graphviz

class WorkflowMixin:
    """
    A mixin class for adding workflow capabilities to SQLAlchemy models.

    This mixin provides methods for defining and managing workflow states,
    transitions between states, and actions to be performed on state changes.

    Class Attributes:
        __workflow_states__ (dict): Defines the possible states and their descriptions.
        __workflow_transitions__ (dict): Defines the possible transitions between states.
        __workflow_initial_state__ (str): The initial state for new instances.
    """

    __workflow_states__ = {}
    __workflow_transitions__ = {}
    __workflow_initial_state__ = None

    @declared_attr
    def current_state(cls):
        return Column(String(50), nullable=False)

    @declared_attr
    def state_history(cls):
        return relationship('WorkflowStateHistory', back_populates='model_instance', cascade='all, delete-orphan')

    @classmethod
    def __declare_last__(cls):
        if not cls.__workflow_states__:
            raise ValueError(f"__workflow_states__ must be defined for {cls.__name__}")
        if not cls.__workflow_transitions__:
            raise ValueError(f"__workflow_transitions__ must be defined for {cls.__name__}")
        if not cls.__workflow_initial_state__:
            raise ValueError(f"__workflow_initial_state__ must be defined for {cls.__name__}")

        event.listen(cls, 'before_insert', cls._set_initial_state)

    @staticmethod
    def _set_initial_state(mapper, connection, target):
        if target.current_state is None:
            target.current_state = target.__workflow_initial_state__

    def change_state(self, new_state, user_id=None, comment=None):
        """
        Change the current state of the instance.

        Args:
            new_state (str): The new state to transition to.
            user_id (int, optional): ID of the user making the change.
            comment (str, optional): Comment about the state change.

        Raises:
            ValueError: If the transition is not allowed.
        """
        if new_state not in self.__workflow_states__:
            raise ValueError(f"Invalid state: {new_state}")

        if new_state not in self.__workflow_transitions__.get(self.current_state, []):
            raise ValueError(f"Transition from {self.current_state} to {new_state} is not allowed")

        old_state = self.current_state
        self.current_state = new_state

        # Record state change in history
        history_entry = WorkflowStateHistory(
            model_instance=self,
            old_state=old_state,
            new_state=new_state,
            user_id=user_id,
            comment=comment
        )
        self.state_history.append(history_entry)

        # Trigger any defined actions for this transition
        self._trigger_transition_action(old_state, new_state)

    def _trigger_transition_action(self, old_state, new_state):
        """
        Trigger any defined actions for a state transition.

        Args:
            old_state (str): The previous state.
            new_state (str): The new state.
        """
        action_method_name = f'_on_transition_from_{old_state}_to_{new_state}'
        if hasattr(self, action_method_name):
            getattr(self, action_method_name)()

    def can_transition_to(self, state):
        """
        Check if a transition to the given state is allowed.

        Args:
            state (str): The state to check transition possibility.

        Returns:
            bool: True if the transition is allowed, False otherwise.
        """
        return state in self.__workflow_transitions__.get(self.current_state, [])

    def get_available_transitions(self):
        """
        Get all available transitions from the current state.

        Returns:
            list: List of states that can be transitioned to from the current state.
        """
        return self.__workflow_transitions__.get(self.current_state, [])

    @classmethod
    def get_workflow_graph(cls):
        """
        Generate a visual representation of the workflow as a graph.

        Returns:
            graphviz.Digraph: A graphviz graph object representing the workflow.
        """
        dot = graphviz.Digraph(comment=f'Workflow for {cls.__name__}')
        dot.attr(rankdir='LR', size='8,5')

        # Add states
        for state, description in cls.__workflow_states__.items():
            dot.node(state, f"{state}\n{description}")

        # Add transitions
        for from_state, to_states in cls.__workflow_transitions__.items():
            for to_state in to_states:
                dot.edge(from_state, to_state)

        return dot

    @classmethod
    def get_workflow_as_dict(cls):
        """
        Get a dictionary representation of the workflow.

        Returns:
            dict: A dictionary containing the workflow states and transitions.
        """
        return {
            'states': cls.__workflow_states__,
            'transitions': cls.__workflow_transitions__,
            'initial_state': cls.__workflow_initial_state__
        }

class WorkflowStateHistory(Model):
    """
    Model to represent the history of workflow state changes.
    """
    __tablename__ = 'nx_workflow_state_history'

    id = Column(Integer, primary_key=True)
    model_type = Column(String(100), nullable=False)
    model_id = Column(Integer, nullable=False)
    old_state = Column(String(50), nullable=False)
    new_state = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey('ab_user.id'), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    comment = Column(Text)

    @declared_attr
    def model_instance(cls):
        return relationship(WorkflowMixin, back_populates='state_history')

# Example usage (commented out):
"""
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String
from mixins.workflow_mixin import WorkflowMixin

class Task(WorkflowMixin, Model):
    __tablename__ = 'nx_tasks'
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)

    __workflow_states__ = {
        'draft': 'Task is in draft state',
        'in_progress': 'Task is being worked on',
        'review': 'Task is under review',
        'completed': 'Task has been completed',
        'archived': 'Task has been archived'
    }

    __workflow_transitions__ = {
        'draft': ['in_progress'],
        'in_progress': ['review', 'completed'],
        'review': ['in_progress', 'completed'],
        'completed': ['archived'],
        'archived': []
    }

    __workflow_initial_state__ = 'draft'

    def _on_transition_from_draft_to_in_progress(self):
        # Custom action when transitioning from draft to in_progress
        print(f"Task '{self.title}' has been started.")

    def _on_transition_from_in_progress_to_completed(self):
        # Custom action when transitioning from in_progress to completed
        print(f"Task '{self.title}' has been completed.")

# In your application code:

# Create a new task
new_task = Task(title="Implement new feature")
db.session.add(new_task)
db.session.commit()

print(new_task.current_state)  # Output: 'draft'

# Change state
new_task.change_state('in_progress', user_id=1, comment="Starting work on the task")
db.session.commit()

print(new_task.current_state)  # Output: 'in_progress'

# Check available transitions
print(new_task.get_available_transitions())  # Output: ['review', 'completed']

# Check if a specific transition is allowed
print(new_task.can_transition_to('completed'))  # Output: True
print(new_task.can_transition_to('draft'))  # Output: False

# Get workflow history
for history_entry in new_task.state_history:
    print(f"State changed from {history_entry.old_state} to {history_entry.new_state} "
          f"at {history_entry.timestamp} by user {history_entry.user_id}")

# Generate workflow graph
graph = Task.get_workflow_graph()
graph.render("task_workflow", format="png", cleanup=True)

# Get workflow as dictionary
workflow_dict = Task.get_workflow_as_dict()
print(json.dumps(workflow_dict, indent=2))
"""
