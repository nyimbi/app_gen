"""
approval_workflow_mixin.py

This module provides an ApprovalWorkflowMixin class for implementing
complex approval workflows in SQLAlchemy models for Flask-AppBuilder applications.

The ApprovalWorkflowMixin allows for defining multi-step approval processes,
with support for parallel approvals, conditional steps, and role-based permissions.

Dependencies:
    - SQLAlchemy
    - Flask-AppBuilder
    - Flask-Login (for current user tracking)

Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.0
"""

from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship, declared_attr
from sqlalchemy.ext.mutable import MutableDict
from flask_login import current_user
from flask import current_app
from datetime import datetime
import enum
import json

class ApprovalStatus(enum.Enum):
    """
    Enum defining possible approval workflow statuses.

    Values:
        DRAFT: Initial draft status before workflow starts
        PENDING: Awaiting initial review
        IN_PROGRESS: Currently in approval workflow
        APPROVED: Fully approved
        REJECTED: Rejected at any step
        CANCELLED: Cancelled before completion
        ON_HOLD: Temporarily paused
    """
    DRAFT = "Draft"
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    CANCELLED = "Cancelled"
    ON_HOLD = "On Hold"

class ApprovalWorkflowMixin:
    """
    A mixin class for adding complex approval workflow capabilities to SQLAlchemy models.

    This mixin provides methods for defining and managing multi-step approval processes,
    including parallel approvals and conditional steps.

    Class Attributes:
        __approval_workflow__ (dict): Definition of the approval workflow steps and conditions.
            Required format:
            {
                'start': 'first_step_name',
                'steps': {
                    'step_name': 'next_step' or {
                        'condition': 'next_step',
                        ...
                    }
                }
            }

        __approval_roles__ (dict): Mapping of approval steps to required roles.
            Required format: {'step_name': 'required_role'}

        __timeout_config__ (dict, optional): Configuration for step timeouts.
            Format: {'step_name': timeout_hours}

        __auto_actions__ (dict, optional): Automatic actions on timeout.
            Format: {'step_name': 'approve'|'reject'|'escalate'}
    """

    # Columns
    @declared_attr
    def approval_status(cls):
        """Current approval status of the record."""
        return Column(
            "approval_status",
            Enum(ApprovalStatus, name="approval_status_enum"),
            default=ApprovalStatus.DRAFT,
            nullable=False,
            index=True,
            comment="Current status in approval workflow"
        )

    @declared_attr
    def current_step(cls):
        """Current step in the approval workflow."""
        return Column(
            "current_step",
            String(100),
            nullable=True,
            index=True,
            comment="Current step in approval workflow"
        )

    @declared_attr
    def approval_history(cls):
        """History of all approval actions."""
        return Column(
            "approval_history",
            MutableDict.as_mutable(JSON),
            default=lambda: dict(),
            nullable=False,
            comment="JSON history of approval workflow actions"
        )

    @declared_attr
    def last_action_date(cls):
        """Timestamp of last workflow action."""
        return Column(
            "last_action_date",
            DateTime,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
            nullable=False,
            index=True
        )

    @declared_attr
    def created_by_id(cls):
        """User who created the record."""
        return Column(
            Integer,
            ForeignKey("ab_user.id"),
            nullable=False,
            index=True
        )

    @declared_attr
    def created_by(cls):
        """Relationship to user who created record."""
        return relationship(
            "User",
            foreign_keys=[cls.created_by_id],
            backref=f"{cls.__name__.lower()}_created"
        )

    @classmethod
    def __declare_last__(cls):
        """Validate required class attributes on model declaration."""
        if not hasattr(cls, '__approval_workflow__'):
            raise ValueError(f"__approval_workflow__ must be defined for {cls.__name__}")
        if not hasattr(cls, '__approval_roles__'):
            raise ValueError(f"__approval_roles__ must be defined for {cls.__name__}")

        # Validate workflow structure
        if 'start' not in cls.__approval_workflow__:
            raise ValueError("Workflow must define 'start' step")
        if 'steps' not in cls.__approval_workflow__:
            raise ValueError("Workflow must define 'steps' dict")

        # Validate all steps have role mappings
        for step in cls.__approval_workflow__['steps'].keys():
            if step not in cls.__approval_roles__:
                raise ValueError(f"Missing role mapping for step '{step}'")

    def initiate_approval_process(self):
        """
        Initiate the approval process for the instance.

        Raises:
            ValueError: If process already initiated
            RuntimeError: If instance not yet saved
        """
        if not self.id:
            raise RuntimeError("Instance must be saved before initiating approval")

        if self.approval_status != ApprovalStatus.DRAFT:
            raise ValueError("Approval process already initiated")

        self.approval_status = ApprovalStatus.IN_PROGRESS
        self.current_step = self.__approval_workflow__['start']
        self.approval_history = {}
        self.last_action_date = datetime.utcnow()

        try:
            current_app.db.session.commit()
        except Exception as e:
            current_app.db.session.rollback()
            raise RuntimeError(f"Failed to initiate approval: {str(e)}")

    def approve_step(self, user, comment=""):
        """
        Approve the current step in the approval process.

        Args:
            user: The user approving the step
            comment (str): Optional comment for the approval

        Returns:
            bool: True if step was approved successfully

        Raises:
            ValueError: If invalid user or workflow state
            RuntimeError: For database errors
        """
        if not user or not user.id:
            raise ValueError("Valid user required for approval")

        if self.approval_status not in [ApprovalStatus.IN_PROGRESS, ApprovalStatus.PENDING]:
            raise ValueError(f"Cannot approve in status: {self.approval_status}")

        if not self._can_approve(user):
            raise ValueError("User not authorized for this approval step")

        try:
            self._record_approval(user, comment)
            next_step = self._get_next_step()

            if next_step:
                self.current_step = next_step
                self.approval_status = ApprovalStatus.IN_PROGRESS
            else:
                self.current_step = None
                self.approval_status = ApprovalStatus.APPROVED

            self.last_action_date = datetime.utcnow()
            current_app.db.session.commit()
            return True

        except Exception as e:
            current_app.db.session.rollback()
            raise RuntimeError(f"Approval failed: {str(e)}")

    def reject_step(self, user, reason):
        """
        Reject the current step in the approval process.

        Args:
            user: The user rejecting the step
            reason (str): Required reason for rejection

        Returns:
            bool: True if step was rejected successfully

        Raises:
            ValueError: If invalid user/reason or workflow state
            RuntimeError: For database errors
        """
        if not user or not user.id:
            raise ValueError("Valid user required for rejection")

        if not reason:
            raise ValueError("Reason required for rejection")

        if self.approval_status not in [ApprovalStatus.IN_PROGRESS, ApprovalStatus.PENDING]:
            raise ValueError(f"Cannot reject in status: {self.approval_status}")

        if not self._can_approve(user):
            raise ValueError("User not authorized for this approval step")

        try:
            self._record_rejection(user, reason)
            self.current_step = None
            self.approval_status = ApprovalStatus.REJECTED
            self.last_action_date = datetime.utcnow()
            current_app.db.session.commit()
            return True

        except Exception as e:
            current_app.db.session.rollback()
            raise RuntimeError(f"Rejection failed: {str(e)}")

    def cancel_workflow(self, user, reason):
        """
        Cancel the current approval workflow.

        Args:
            user: The user cancelling the workflow
            reason (str): Required reason for cancellation

        Raises:
            ValueError: If invalid state or unauthorized
        """
        if not self._can_cancel(user):
            raise ValueError("User not authorized to cancel workflow")

        if self.approval_status in [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED]:
            raise ValueError("Cannot cancel completed workflow")

        self.approval_status = ApprovalStatus.CANCELLED
        self.current_step = None
        self._record_cancellation(user, reason)
        self.last_action_date = datetime.utcnow()
        current_app.db.session.commit()

    def put_on_hold(self, user, reason):
        """
        Put the current workflow step on hold.

        Args:
            user: The user putting workflow on hold
            reason (str): Required reason for hold

        Raises:
            ValueError: If invalid state or unauthorized
        """
        if not self._can_approve(user):
            raise ValueError("User not authorized for this step")

        if self.approval_status != ApprovalStatus.IN_PROGRESS:
            raise ValueError("Can only put in-progress workflows on hold")

        self.approval_status = ApprovalStatus.ON_HOLD
        self._record_hold(user, reason)
        self.last_action_date = datetime.utcnow()
        current_app.db.session.commit()

    def resume_workflow(self, user, comment=""):
        """Resume a workflow that was on hold."""
        if not self._can_approve(user):
            raise ValueError("User not authorized for this step")

        if self.approval_status != ApprovalStatus.ON_HOLD:
            raise ValueError("Can only resume workflows that are on hold")

        self.approval_status = ApprovalStatus.IN_PROGRESS
        self._record_resume(user, comment)
        self.last_action_date = datetime.utcnow()
        current_app.db.session.commit()

    def _can_approve(self, user):
        """Check if user has required role for current step."""
        if not user or not hasattr(user, 'roles'):
            return False

        required_role = self.__approval_roles__.get(self.current_step)
        if not required_role:
            return False

        return required_role in [role.name for role in user.roles]

    def _can_cancel(self, user):
        """Check if user can cancel workflow."""
        if user.id == self.created_by_id:
            return True

        admin_role = current_app.config.get('APPROVAL_ADMIN_ROLE', 'Admin')
        return admin_role in [role.name for role in user.roles]

    def _record_approval(self, user, comment):
        """Record an approval action in history."""
        self.approval_history[self.current_step] = {
            "status": "approved",
            "user_id": user.id,
            "username": user.username,
            "timestamp": datetime.utcnow().isoformat(),
            "comment": comment or ""
        }

    def _record_rejection(self, user, reason):
        """Record a rejection action in history."""
        self.approval_history[self.current_step] = {
            "status": "rejected",
            "user_id": user.id,
            "username": user.username,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason
        }

    def _record_cancellation(self, user, reason):
        """Record workflow cancellation in history."""
        self.approval_history['cancelled'] = {
            "user_id": user.id,
            "username": user.username,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason
        }

    def _record_hold(self, user, reason):
        """Record workflow hold in history."""
        self.approval_history[f"{self.current_step}_hold"] = {
            "status": "on_hold",
            "user_id": user.id,
            "username": user.username,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason
        }

    def _record_resume(self, user, comment):
        """Record workflow resume in history."""
        self.approval_history[f"{self.current_step}_resume"] = {
            "status": "resumed",
            "user_id": user.id,
            "username": user.username,
            "timestamp": datetime.utcnow().isoformat(),
            "comment": comment
        }

    def _get_next_step(self):
        """
        Determine next workflow step based on conditions.

        Returns:
            str|None: Name of next step or None if workflow complete
        """
        current_step_info = self.__approval_workflow__['steps'].get(self.current_step)

        if not current_step_info:
            return None

        if isinstance(current_step_info, str):
            return current_step_info

        if isinstance(current_step_info, dict):
            for condition, next_step in current_step_info.items():
                try:
                    if self._evaluate_condition(condition):
                        return next_step
                except Exception as e:
                    current_app.logger.error(
                        f"Error evaluating condition '{condition}': {str(e)}"
                    )

        return None

    def _evaluate_condition(self, condition):
        """
        Safely evaluate a workflow condition.

        Args:
            condition (str): Python expression to evaluate

        Returns:
            bool: Result of condition evaluation

        Raises:
            ValueError: If condition is invalid
        """
        try:
            # Create safe evaluation context
            context = {
                "self": self,
                "datetime": datetime,
                "timedelta": datetime.timedelta,
                # Add other safe builtins as needed
            }

            return eval(condition, {"__builtins__": {}}, context)

        except Exception as e:
            raise ValueError(f"Invalid condition '{condition}': {str(e)}")

    def get_approval_status(self):
        """
        Get current workflow status and history.

        Returns:
            dict: Current status, step and full history
        """
        return {
            "status": self.approval_status.value,
            "current_step": self.current_step,
            "last_action": self.last_action_date.isoformat(),
            "history": self.approval_history,
            "created_by": {
                "id": self.created_by_id,
                "username": self.created_by.username
            }
        }

    @classmethod
    def get_pending_approvals(cls, user):
        """
        Get pending approvals for a user based on roles.

        Args:
            user: User to check approvals for

        Returns:
            list: Pending approval instances for user
        """
        if not user or not hasattr(user, 'roles'):
            return []

        user_roles = [role.name for role in user.roles]
        pending = []

        query = current_app.db.session.query(cls).filter(
            cls.approval_status.in_([
                ApprovalStatus.IN_PROGRESS,
                ApprovalStatus.PENDING
            ])
        )

        for instance in query.all():
            required_role = cls.__approval_roles__.get(instance.current_step)
            if required_role in user_roles:
                pending.append(instance)

        return pending

    @classmethod
    def get_approval_metrics(cls, start_date=None, end_date=None):
        """
        Get approval workflow metrics for reporting.

        Args:
            start_date (datetime): Optional start date filter
            end_date (datetime): Optional end date filter

        Returns:
            dict: Workflow metrics and statistics
        """
        query = current_app.db.session.query(cls)

        if start_date:
            query = query.filter(cls.last_action_date >= start_date)
        if end_date:
            query = query.filter(cls.last_action_date <= end_date)

        results = query.all()

        metrics = {
            "total": len(results),
            "status_counts": {},
            "avg_duration": None,
            "step_metrics": {}
        }

        for status in ApprovalStatus:
            metrics["status_counts"][status.value] = len([
                r for r in results if r.approval_status == status
            ])

        # Calculate other metrics
        durations = []
        for result in results:
            if result.approval_status in [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED]:
                first = min(result.approval_history.values(), key=lambda x: x["timestamp"])
                last = max(result.approval_history.values(), key=lambda x: x["timestamp"])
                duration = (
                    datetime.fromisoformat(last["timestamp"]) -
                    datetime.fromisoformat(first["timestamp"])
                )
                durations.append(duration.total_seconds())

        if durations:
            metrics["avg_duration"] = sum(durations) / len(durations)

        return metrics

# Example usage (commented out):
"""
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, Text
from mixins.approval_workflow_mixin import ApprovalWorkflowMixin

class ExpenseReport(ApprovalWorkflowMixin, Model):
    __tablename__ = 'nx_expense_reports'
    id = Column(Integer, primary_key=True)
    employee_name = Column(String(100), nullable=False)
    amount = Column(Integer, nullable=False)
    description = Column(Text)

    __approval_workflow__ = {
        'start': 'manager_approval',
        'steps': {
            'manager_approval': {
                'amount <= 1000': 'finance_approval',
                'amount > 1000': 'director_approval'
            },
            'director_approval': 'finance_approval',
            'finance_approval': None  # End of workflow
        }
    }

    __approval_roles__ = {
        'manager_approval': 'Manager',
        'director_approval': 'Director',
        'finance_approval': 'Finance'
    }

# In your application code:

# Creating a new expense report
report = ExpenseReport(employee_name="John Doe", amount=1500, description="Conference expenses")
db.session.add(report)
db.session.commit()

# Initiating the approval process
report.initiate_approval_process()

# Approving steps
manager_user = User.query.filter_by(username='manager1').first()
report.approve_step(manager_user, "Approved by manager")

director_user = User.query.filter_by(username='director1').first()
report.approve_step(director_user, "Approved by director")

finance_user = User.query.filter_by(username='finance1').first()
report.approve_step(finance_user, "Approved by finance")

# Checking approval status
status = report.get_approval_status()
print(f"Current status: {status['status']}")
print(f"Approval history: {status['history']}")

# Getting pending approvals for a user
finance_user = User.query.filter_by(username='finance1').first()
pending_approvals = ExpenseReport.get_pending_approvals(finance_user)
for approval in pending_approvals:
    print(f"Pending approval: Expense report {approval.id} for {approval.employee_name}")
"""
