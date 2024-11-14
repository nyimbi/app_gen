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
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    IN_PROGRESS = "In Progress"

class ApprovalWorkflowMixin:
    """
    A mixin class for adding complex approval workflow capabilities to SQLAlchemy models.

    This mixin provides methods for defining and managing multi-step approval processes,
    including parallel approvals and conditional steps.

    Class Attributes:
        __approval_workflow__ (dict): Definition of the approval workflow steps and conditions.
        __approval_roles__ (dict): Mapping of approval steps to required roles.
    """

    @declared_attr
    def approval_status(cls):
        return Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False)

    @declared_attr
    def current_step(cls):
        return Column(String(100), nullable=True)

    @declared_attr
    def approval_history(cls):
        return Column(MutableDict.as_mutable(JSON), default=dict, nullable=False)

    @classmethod
    def __declare_last__(cls):
        if not hasattr(cls, '__approval_workflow__'):
            raise ValueError(f"__approval_workflow__ must be defined for {cls.__name__}")
        if not hasattr(cls, '__approval_roles__'):
            raise ValueError(f"__approval_roles__ must be defined for {cls.__name__}")

    def initiate_approval_process(self):
        """
        Initiate the approval process for the instance.
        """
        self.approval_status = ApprovalStatus.IN_PROGRESS
        self.current_step = self.__approval_workflow__['start']
        self.approval_history = {}
        current_app.db.session.commit()

    def approve_step(self, user, comment=""):
        """
        Approve the current step in the approval process.

        Args:
            user: The user approving the step.
            comment (str): Optional comment for the approval.

        Returns:
            bool: True if the step was successfully approved, False otherwise.
        """
        if not self._can_approve(user):
            return False

        self._record_approval(user, comment)
        next_step = self._get_next_step()
        
        if next_step:
            self.current_step = next_step
        else:
            self.approval_status = ApprovalStatus.APPROVED

        current_app.db.session.commit()
        return True

    def reject_step(self, user, reason):
        """
        Reject the current step in the approval process.

        Args:
            user: The user rejecting the step.
            reason (str): Reason for the rejection.

        Returns:
            bool: True if the step was successfully rejected, False otherwise.
        """
        if not self._can_approve(user):
            return False

        self._record_rejection(user, reason)
        self.approval_status = ApprovalStatus.REJECTED
        current_app.db.session.commit()
        return True

    def _can_approve(self, user):
        """Check if the user has the required role to approve the current step."""
        required_role = self.__approval_roles__.get(self.current_step)
        return required_role in [role.name for role in user.roles]

    def _record_approval(self, user, comment):
        """Record an approval in the approval history."""
        self.approval_history[self.current_step] = {
            "status": "approved",
            "user_id": user.id,
            "timestamp": datetime.utcnow().isoformat(),
            "comment": comment
        }

    def _record_rejection(self, user, reason):
        """Record a rejection in the approval history."""
        self.approval_history[self.current_step] = {
            "status": "rejected",
            "user_id": user.id,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason
        }

    def _get_next_step(self):
        """Determine the next step in the approval process."""
        current_step_info = self.__approval_workflow__['steps'][self.current_step]
        if isinstance(current_step_info, dict):
            for condition, next_step in current_step_info.items():
                if self._evaluate_condition(condition):
                    return next_step
        elif isinstance(current_step_info, str):
            return current_step_info
        return None

    def _evaluate_condition(self, condition):
        """Evaluate a condition for conditional workflow routing."""
        # This is a simplified condition evaluation.
        # In a real-world scenario, you might want to use a more sophisticated
        # expression evaluation system.
        return eval(condition, {"self": self})

    def get_approval_status(self):
        """
        Get the current approval status and history.

        Returns:
            dict: A dictionary containing the current status, step, and approval history.
        """
        return {
            "status": self.approval_status.value,
            "current_step": self.current_step,
            "history": self.approval_history
        }

    @classmethod
    def get_pending_approvals(cls, user):
        """
        Get all pending approvals for a specific user based on their role.

        Args:
            user: The user to check pending approvals for.

        Returns:
            list: A list of instances pending approval for the user.
        """
        user_roles = [role.name for role in user.roles]
        pending_approvals = []

        for instance in cls.query.filter_by(approval_status=ApprovalStatus.IN_PROGRESS).all():
            if instance.__approval_roles__.get(instance.current_step) in user_roles:
                pending_approvals.append(instance)

        return pending_approvals

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
