"""
scheduling_mixin.py

This module provides a SchedulingMixin class for implementing scheduling
capabilities in SQLAlchemy models for Flask-AppBuilder applications.

The SchedulingMixin allows for complex scheduling of events or tasks,
supporting various recurrence patterns, time zones, and exceptions.

Dependencies:
    - SQLAlchemy
    - Flask-AppBuilder
    - dateutil
    - pytz

Author: Nyimbi Odero
Date: 25/08/2024
Version: 1.0
"""

from flask_appbuilder import Model
from sqlalchemy import Column, Integer, DateTime, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from dateutil.rrule import rrule, YEARLY, MONTHLY, WEEKLY, DAILY
from dateutil.parser import parse
import pytz
from datetime import datetime, timedelta
import json

class SchedulingMixin:
    """
    A mixin class for adding scheduling capabilities to SQLAlchemy models.

    This mixin provides fields and methods for scheduling events or tasks
    with complex recurrence patterns, time zone support, and exception handling.

    Attributes:
        start_time (DateTime): The start time of the event or task.
        end_time (DateTime): The end time of the event or task.
        timezone (String): The time zone for the event or task.
        recurrence_pattern (String): JSON string describing the recurrence pattern.
        is_recurring (Boolean): Whether the event or task is recurring.
        priority (Integer): Priority of the event or task (lower number = higher priority).
        dependencies (String): JSON string listing dependencies (IDs of other scheduled items).
    """

    @declared_attr
    def start_time(cls):
        return Column(DateTime(timezone=True), nullable=False)

    @declared_attr
    def end_time(cls):
        return Column(DateTime(timezone=True), nullable=False)

    @declared_attr
    def timezone(cls):
        return Column(String(50), default='UTC')

    @declared_attr
    def recurrence_pattern(cls):
        return Column(Text)

    @declared_attr
    def is_recurring(cls):
        return Column(Boolean, default=False)

    @declared_attr
    def priority(cls):
        return Column(Integer, default=0)

    @declared_attr
    def dependencies(cls):
        return Column(Text)

    @declared_attr
    def exceptions(cls):
        return relationship('ScheduleException', back_populates='scheduled_item', cascade='all, delete-orphan')

    def set_recurrence(self, freq, interval=1, count=None, until=None, byday=None, bymonthday=None, byyearday=None):
        """
        Set the recurrence pattern for the scheduled item.

        Args:
            freq (str): Frequency of recurrence ('YEARLY', 'MONTHLY', 'WEEKLY', 'DAILY').
            interval (int): Interval of recurrence.
            count (int, optional): Number of occurrences.
            until (datetime, optional): Date until which to repeat.
            byday (list, optional): Days of the week to repeat on (e.g., ['MO', 'WE', 'FR']).
            bymonthday (list, optional): Days of the month to repeat on.
            byyearday (list, optional): Days of the year to repeat on.
        """
        pattern = {
            'freq': freq,
            'interval': interval,
            'count': count,
            'until': until.isoformat() if until else None,
            'byday': byday,
            'bymonthday': bymonthday,
            'byyearday': byyearday
        }
        self.recurrence_pattern = json.dumps(pattern)
        self.is_recurring = True

    def get_occurrences(self, start, end):
        """
        Get all occurrences of the scheduled item between start and end dates.

        Args:
            start (datetime): Start date for occurrence calculation.
            end (datetime): End date for occurrence calculation.

        Returns:
            list: List of datetime objects representing occurrences.
        """
        if not self.is_recurring:
            if start <= self.start_time <= end:
                return [self.start_time]
            return []

        pattern = json.loads(self.recurrence_pattern)
        freq_map = {'YEARLY': YEARLY, 'MONTHLY': MONTHLY, 'WEEKLY': WEEKLY, 'DAILY': DAILY}
        
        rrule_kwargs = {
            'dtstart': self.start_time,
            'freq': freq_map[pattern['freq']],
            'interval': pattern['interval'],
            'until': parse(pattern['until']) if pattern['until'] else end,
        }
        
        if pattern['count']:
            rrule_kwargs['count'] = pattern['count']
        if pattern['byday']:
            rrule_kwargs['byday'] = pattern['byday']
        if pattern['bymonthday']:
            rrule_kwargs['bymonthday'] = pattern['bymonthday']
        if pattern['byyearday']:
            rrule_kwargs['byyearday'] = pattern['byyearday']

        occurrences = list(rrule(**rrule_kwargs))
        return [occ for occ in occurrences if start <= occ <= end]

    def is_active(self, check_time=None):
        """
        Check if the scheduled item is currently active.

        Args:
            check_time (datetime, optional): The time to check against. Defaults to current time.

        Returns:
            bool: True if the item is active, False otherwise.
        """
        if check_time is None:
            check_time = datetime.now(pytz.timezone(self.timezone))

        if self.is_recurring:
            occurrences = self.get_occurrences(check_time - timedelta(minutes=1), check_time + timedelta(minutes=1))
            return any(occ <= check_time < occ + (self.end_time - self.start_time) for occ in occurrences)
        else:
            return self.start_time <= check_time < self.end_time

    def add_exception(self, exception_date):
        """
        Add an exception date to the schedule.

        Args:
            exception_date (datetime): The date to be excepted from the schedule.
        """
        exception = ScheduleException(scheduled_item=self, exception_date=exception_date)
        self.exceptions.append(exception)

    def remove_exception(self, exception_date):
        """
        Remove an exception date from the schedule.

        Args:
            exception_date (datetime): The exception date to be removed.
        """
        self.exceptions = [e for e in self.exceptions if e.exception_date != exception_date]

    def set_dependencies(self, dependency_ids):
        """
        Set dependencies for the scheduled item.

        Args:
            dependency_ids (list): List of IDs of other scheduled items that this item depends on.
        """
        self.dependencies = json.dumps(dependency_ids)

    def get_dependencies(self):
        """
        Get the dependencies of the scheduled item.

        Returns:
            list: List of IDs of dependent scheduled items.
        """
        return json.loads(self.dependencies) if self.dependencies else []

    @classmethod
    def find_conflicts(cls, session, start_time, end_time):
        """
        Find conflicting scheduled items for a given time range.

        Args:
            session: SQLAlchemy session.
            start_time (datetime): Start of the time range to check.
            end_time (datetime): End of the time range to check.

        Returns:
            list: List of conflicting scheduled items.
        """
        return session.query(cls).filter(
            ((cls.start_time <= start_time) & (cls.end_time > start_time)) |
            ((cls.start_time < end_time) & (cls.end_time >= end_time)) |
            ((cls.start_time >= start_time) & (cls.end_time <= end_time))
        ).all()

class ScheduleException(Model):
    """
    Model to represent exceptions to a scheduled item.
    """
    __tablename__ = 'nx_schedule_exceptions'

    id = Column(Integer, primary_key=True)
    scheduled_item_id = Column(Integer, ForeignKey('your_scheduled_item_table.id'))
    exception_date = Column(DateTime(timezone=True), nullable=False)

    scheduled_item = relationship('YourScheduledItemModel', back_populates='exceptions')

# Example usage (commented out):
"""
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String
from mixins.scheduling_mixin import SchedulingMixin

class ScheduledTask(SchedulingMixin, Model):
    __tablename__ = 'nx_scheduled_tasks'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

# In your application code:

# Create a new scheduled task
new_task = ScheduledTask(
    name="Weekly Team Meeting",
    start_time=datetime(2024, 1, 1, 10, 0, tzinfo=pytz.UTC),
    end_time=datetime(2024, 1, 1, 11, 0, tzinfo=pytz.UTC),
    timezone='America/New_York'
)

# Set recurrence for every Monday
new_task.set_recurrence('WEEKLY', byday=['MO'])

# Add an exception for a holiday
new_task.add_exception(datetime(2024, 1, 15, tzinfo=pytz.UTC))

# Set task priority and dependencies
new_task.priority = 1
new_task.set_dependencies([1, 2, 3])  # Depends on tasks with IDs 1, 2, and 3

db.session.add(new_task)
db.session.commit()

# Check if the task is currently active
is_active = new_task.is_active()

# Get occurrences for the next month
from datetime import datetime, timedelta
start = datetime.now(pytz.UTC)
end = start + timedelta(days=30)
occurrences = new_task.get_occurrences(start, end)

# Find conflicts
conflicts = ScheduledTask.find_conflicts(db.session, start, end)
"""
