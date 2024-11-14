from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from statemachine_mixin import StateMachineMixin, Workflow, State, Transition

class Notification(StateMachineMixin, Model):
    """
    Represents a notification in the system.

    Attributes:
        id (int): The primary key of the notification.
        user_id (int): The ID of the user this notification is for.
        message (str): The content of the notification.
        created_at (datetime): When the notification was created.
        updated_at (datetime): When the notification was last updated.
        state (str): The current state of the notification.
    """
    __tablename__ = 'nx_notifications'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('ab_user.id'), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship('User', backref='notifications')

    workflow = Workflow(
        'notification_workflow',
        states=[
            State('pending', is_initial=True),
            State('delivered'),
            State('read'),
            State('archived')
        ],
        transitions=[
            Transition('deliver', 'pending', 'delivered'),
            Transition('read', 'delivered', 'read'),
            Transition('archive', ['delivered', 'read'], 'archived')
        ]
    )

    def __repr__(self):
        return f'<Notification {self.id}: {self.state} for User {self.user_id}>'

class NotificationManager:
    """
    Manages the creation, sending, and querying of notifications.
    """

    @staticmethod
    def send_notification(user, message):
        """
        Creates and sends a new notification to a user.

        Args:
            user (User): The user to send the notification to.
            message (str): The content of the notification.

        Returns:
            Notification: The created notification object.
        """
        notification = Notification(user_id=user.id, message=message, state='pending')
        db.session.add(notification)
        db.session.commit()

        # Attempt to deliver the notification
        notification.trigger_event('deliver', user)

        return notification

    @staticmethod
    def get_user_notifications(user, state=None):
        """
        Retrieves notifications for a user, optionally filtered by state.

        Args:
            user (User): The user to get notifications for.
            state (str, optional): The state to filter notifications by.

        Returns:
            list: A list of Notification objects.
        """
        query = Notification.query.filter_by(user_id=user.id)
        if state:
            query = query.filter_by(state=state)
        return query.order_by(Notification.created_at.desc()).all()

    @staticmethod
    def mark_as_read(notification_id, user):
        """
        Marks a notification as read.

        Args:
            notification_id (int): The ID of the notification to mark as read.
            user (User): The user marking the notification as read.

        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        notification = Notification.query.get(notification_id)
        if notification and notification.user_id == user.id:
            return notification.trigger_event('read', user)
        return False

    @staticmethod
    def archive_notification(notification_id, user):
        """
        Archives a notification.

        Args:
            notification_id (int): The ID of the notification to archive.
            user (User): The user archiving the notification.

        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        notification = Notification.query.get(notification_id)
        if notification and notification.user_id == user.id:
            return notification.trigger_event('archive', user)
        return False

# Update the User model to include a relationship to notifications
from flask_appbuilder.security.sqla.models import User
User.notifications = relationship('Notification', back_populates='user')

# Update the existing NotificationManager in state_machine_mixin.py
class NotificationManager:
    @staticmethod
    def send_email(subject, recipients, body):
        # Existing email sending logic...
        pass

    @staticmethod
    def send_sms(to, body):
        # Existing SMS sending logic...
        pass

    @staticmethod
    def send_signal(signal_name, sender, **kwargs):
        # Existing signal sending logic...
        pass

    @staticmethod
    def flash_message(message, category="info"):
        # Existing flash message logic...
        pass

    @staticmethod
    def send_notification(user, message):
        return NotificationManager.send_notification(user, message)

# Example usage
def example_usage():
    user = User.query.first()  # Get a user
    
    # Send a notification
    notification = NotificationManager.send_notification(user, "Hello, this is a test notification!")
    
    # Get all pending notifications for the user
    pending_notifications = NotificationManager.get_user_notifications(user, state='pending')
    
    # Mark a notification as read
    NotificationManager.mark_as_read(notification.id, user)
    
    # Archive a notification
    NotificationManager.archive_notification(notification.id, user)
    
    # Get all notifications for the user
    all_notifications = NotificationManager.get_user_notifications(user)
    
    return all_notifications
