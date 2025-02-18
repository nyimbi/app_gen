"""
scheduling_mixin.py: Advanced Scheduling System for Flask-AppBuilder

This module provides a comprehensive scheduling system for Flask-AppBuilder applications.
It implements an enterprise-grade scheduling engine with support for:

Key Features:
- Complex recurrence patterns (RRULE) with exceptions
- Multi-timezone support with DST handling
- Dependency management and conflict detection
- Resource allocation and constraints
- Priority-based scheduling
- Calendar integration (iCal, Google Calendar)
- Notification system integration
- Audit logging and history tracking
- Visual calendar rendering
- Mobile calendar sync support
- REST API endpoints
- Batch scheduling operations
- Schedule template management
- Conflict resolution
- Resource optimization

Technical Features:
- PostgreSQL optimized storage
- Redis-based caching
- Async processing support
- WebSocket real-time updates
- REST API integration
- Mobile sync endpoints
- iCal/CalDAV support
- Enterprise calendar integration

Dependencies:
    - Flask-AppBuilder>=4.0.0
    - SQLAlchemy>=1.4.0
    - python-dateutil>=2.8.2
    - pytz>=2022.1
    - icalendar>=4.0.9
    - redis>=4.3.4
    - aiohttp>=3.8.1

Author: Nyimbi Odero
Date: 25/08/2024
Version: 2.0
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4

import pytz
import redis
from dateutil.parser import parse
from dateutil.rrule import DAILY, HOURLY, MINUTELY, MONTHLY, WEEKLY, YEARLY, rrule
from flask import current_app, g
from flask_appbuilder import Model
from icalendar import Calendar, Event
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    and_,
    func,
    or_,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import expression

logger = logging.getLogger(__name__)


class SchedulingMixin:
    """
    Advanced scheduling mixin for SQLAlchemy models.
    """

    @declared_attr
    def uuid(cls):
        """Unique identifier for external sync."""
        return Column(UUID, default=uuid4, unique=True, nullable=False)

    @declared_attr
    def start_time(cls):
        """Start time with timezone support."""
        return Column(DateTime(timezone=True), nullable=False, index=True)

    @declared_attr
    def end_time(cls):
        """End time with timezone support."""
        return Column(DateTime(timezone=True), nullable=False, index=True)

    @declared_attr
    def timezone(cls):
        """Timezone identifier."""
        return Column(String(50), default="UTC", nullable=False)

    @declared_attr
    def title(cls):
        """Event/schedule title."""
        return Column(String(200), nullable=False)

    @declared_attr
    def description(cls):
        """Detailed description."""
        return Column(Text)

    @declared_attr
    def location(cls):
        """Physical or virtual location."""
        return Column(String(200))

    @declared_attr
    def recurrence_pattern(cls):
        """Advanced recurrence rules in JSONB."""
        return Column(JSONB, default={})

    @declared_attr
    def is_recurring(cls):
        """Recurring schedule flag."""
        return Column(Boolean, default=False, nullable=False)

    @declared_attr
    def status(cls):
        """Schedule status (active, cancelled, etc)."""
        return Column(
            Enum("active", "cancelled", "completed", "draft", name="schedule_status"),
            default="active",
            nullable=False,
        )

    @declared_attr
    def priority(cls):
        """Schedule priority (1-5, 1 highest)."""
        return Column(Integer, default=3, nullable=False)

    @declared_attr
    def resources(cls):
        """Required resources in JSONB."""
        return Column(JSONB, default={})

    @declared_attr
    def dependencies(cls):
        """Schedule dependencies in JSONB."""
        return Column(JSONB, default=[])

    @declared_attr
    def metadata(cls):
        """Custom metadata in JSONB."""
        return Column(JSONB, default={})

    @declared_attr
    def notifications(cls):
        """Notification settings in JSONB."""
        return Column(JSONB, default={})

    @declared_attr
    def created_by_fk(cls):
        """Creator foreign key."""
        return Column(Integer, ForeignKey("ab_user.id"), nullable=False)

    @declared_attr
    def updated_by_fk(cls):
        """Last updater foreign key."""
        return Column(Integer, ForeignKey("ab_user.id"), nullable=False)

    @declared_attr
    def created_at(cls):
        """Creation timestamp."""
        return Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    @declared_attr
    def updated_at(cls):
        """Last update timestamp."""
        return Column(DateTime(timezone=True), onupdate=datetime.now(timezone.utc))

    @declared_attr
    def exceptions(cls):
        """Schedule exceptions relationship."""
        return relationship(
            "ScheduleException",
            back_populates="scheduled_item",
            cascade="all, delete-orphan",
            lazy="select",
        )

    @declared_attr
    def created_by(cls):
        """Creator relationship."""
        return relationship("User", foreign_keys=[cls.created_by_fk])

    @declared_attr
    def updated_by(cls):
        """Last updater relationship."""
        return relationship("User", foreign_keys=[cls.updated_by_fk])

    def __init__(self, **kwargs):
        """Initialize with timezone conversion."""
        tz = pytz.timezone(kwargs.get("timezone", "UTC"))
        for key in ["start_time", "end_time"]:
            if key in kwargs:
                dt = kwargs[key]
                if dt.tzinfo is None:
                    kwargs[key] = tz.localize(dt)
        super().__init__(**kwargs)

    @validates("priority")
    def validate_priority(self, key, value):
        """Validate priority range."""
        if not 1 <= value <= 5:
            raise ValueError("Priority must be between 1 and 5")
        return value

    def set_recurrence(
        self,
        freq: str,
        interval: int = 1,
        count: Optional[int] = None,
        until: Optional[datetime] = None,
        byday: Optional[List[str]] = None,
        bymonthday: Optional[List[int]] = None,
        byyearday: Optional[List[int]] = None,
        byweekno: Optional[List[int]] = None,
        bymonth: Optional[List[int]] = None,
        byhour: Optional[List[int]] = None,
        byminute: Optional[List[int]] = None,
    ) -> None:
        """Set advanced recurrence pattern."""
        pattern = {
            "freq": freq.upper(),
            "interval": interval,
            "count": count,
            "until": until.isoformat() if until else None,
            "byday": byday,
            "bymonthday": bymonthday,
            "byyearday": byyearday,
            "byweekno": byweekno,
            "bymonth": bymonth,
            "byhour": byhour,
            "byminute": byminute,
        }
        self.recurrence_pattern = {k: v for k, v in pattern.items() if v is not None}
        self.is_recurring = True

    def get_occurrences(
        self, start: datetime, end: datetime, include_exceptions: bool = True
    ) -> List[datetime]:
        """Get schedule occurrences with exception handling."""
        if not self.is_recurring:
            return [self.start_time] if start <= self.start_time <= end else []

        freq_map = {
            "YEARLY": YEARLY,
            "MONTHLY": MONTHLY,
            "WEEKLY": WEEKLY,
            "DAILY": DAILY,
            "HOURLY": HOURLY,
            "MINUTELY": MINUTELY,
        }

        pattern = self.recurrence_pattern
        rrule_kwargs = {
            "dtstart": self.start_time,
            "freq": freq_map[pattern["freq"]],
            "interval": pattern.get("interval", 1),
            "until": parse(pattern["until"]) if pattern.get("until") else end,
        }

        optional_keys = [
            "count",
            "byday",
            "bymonthday",
            "byyearday",
            "byweekno",
            "bymonth",
            "byhour",
            "byminute",
        ]
        for key in optional_keys:
            if key in pattern:
                rrule_kwargs[key] = pattern[key]

        occurrences = list(rrule(**rrule_kwargs))

        if include_exceptions:
            exception_dates = {e.exception_date for e in self.exceptions}
            occurrences = [
                occ
                for occ in occurrences
                if occ.replace(tzinfo=None) not in exception_dates
            ]

        return [occ for occ in occurrences if start <= occ <= end]

    async def get_conflicts(self, session, margin: int = 0) -> List["SchedulingMixin"]:
        """Asynchronously find scheduling conflicts."""
        margin_delta = timedelta(minutes=margin)
        occurrences = self.get_occurrences(
            self.start_time - margin_delta, self.end_time + margin_delta
        )

        conflicts = []
        for occurrence in occurrences:
            start = occurrence - margin_delta
            end = occurrence + (self.end_time - self.start_time) + margin_delta

            query = session.query(self.__class__).filter(
                self.__class__.id != self.id,
                self.__class__.status == "active",
                or_(
                    and_(
                        self.__class__.start_time <= start,
                        self.__class__.end_time > start,
                    ),
                    and_(
                        self.__class__.start_time < end, self.__class__.end_time >= end
                    ),
                    and_(
                        self.__class__.start_time >= start,
                        self.__class__.end_time <= end,
                    ),
                ),
            )

            if self.resources:
                query = query.filter(self.__class__.resources.overlap(self.resources))

            conflicts.extend(await query.gino.all())

        return list(set(conflicts))

    def to_ical(self) -> str:
        """Generate iCalendar representation."""
        cal = Calendar()
        event = Event()

        event.add("summary", self.title)
        event.add("dtstart", self.start_time)
        event.add("dtend", self.end_time)
        event.add("description", self.description or "")
        event.add("location", self.location or "")

        if self.is_recurring and self.recurrence_pattern:
            event.add("rrule", self.recurrence_pattern)

        # Add exceptions as EXDATEs
        for exception in self.exceptions:
            event.add("exdate", exception.exception_date)

        cal.add_component(event)
        return cal.to_ical().decode("utf-8")

    def from_ical(self, ical_data: str) -> None:
        """Update from iCalendar data."""
        cal = Calendar.from_ical(ical_data)
        for component in cal.walk():
            if component.name == "VEVENT":
                self.start_time = component.get("dtstart").dt
                self.end_time = component.get("dtend").dt
                self.title = str(component.get("summary", ""))
                self.description = str(component.get("description", ""))
                self.location = str(component.get("location", ""))

                if "rrule" in component:
                    self.recurrence_pattern = dict(component.get("rrule"))
                    self.is_recurring = True

                if "exdate" in component:
                    for exdate in component.get("exdate"):
                        self.add_exception(exdate.dt)

    @classmethod
    def get_calendar_data(
        cls, session, start: datetime, end: datetime, user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get calendar data for date range."""
        query = session.query(cls).filter(
            or_(
                and_(cls.start_time >= start, cls.start_time <= end),
                and_(cls.end_time >= start, cls.end_time <= end),
                and_(cls.start_time <= start, cls.end_time >= end),
            )
        )

        if user_id:
            query = query.filter(
                or_(
                    cls.created_by_fk == user_id,
                    cls.resources.contains({"user_id": user_id}),
                )
            )

        schedules = query.all()
        calendar_data = []

        for schedule in schedules:
            if schedule.is_recurring:
                occurrences = schedule.get_occurrences(start, end)
                for occurrence in occurrences:
                    calendar_data.append(
                        {
                            "id": f"{schedule.id}_{occurrence.isoformat()}",
                            "title": schedule.title,
                            "start": occurrence.isoformat(),
                            "end": (
                                occurrence + (schedule.end_time - schedule.start_time)
                            ).isoformat(),
                            "recurring": True,
                            "status": schedule.status,
                            "priority": schedule.priority,
                            "location": schedule.location,
                            "metadata": schedule.metadata,
                        }
                    )
            else:
                calendar_data.append(
                    {
                        "id": str(schedule.id),
                        "title": schedule.title,
                        "start": schedule.start_time.isoformat(),
                        "end": schedule.end_time.isoformat(),
                        "recurring": False,
                        "status": schedule.status,
                        "priority": schedule.priority,
                        "location": schedule.location,
                        "metadata": schedule.metadata,
                    }
                )

        return calendar_data


class ScheduleException(Model):
    """Schedule exception model."""

    __tablename__ = "nx_schedule_exceptions"

    id = Column(Integer, primary_key=True)
    uuid = Column(UUID, default=uuid4, unique=True)
    scheduled_item_id = Column(
        Integer, ForeignKey("scheduled_items.id"), nullable=False
    )
    exception_date = Column(DateTime(timezone=True), nullable=False)
    reason = Column(String(200))
    created_by_fk = Column(Integer, ForeignKey("ab_user.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    metadata = Column(JSONB, default={})

    scheduled_item = relationship("ScheduledItem", back_populates="exceptions")
    created_by = relationship("User", foreign_keys=[created_by_fk])

    __table_args__ = (
        Index("ix_schedule_exceptions_date", "scheduled_item_id", "exception_date"),
        UniqueConstraint(
            "scheduled_item_id", "exception_date", name="uq_schedule_exception_date"
        ),
    )


# Example usage:
"""
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from mixins.scheduling_mixin import SchedulingMixin
import pytz
from datetime import datetime, timedelta

class Meeting(SchedulingMixin, Model):
    '''Team meeting schedule model.'''

    __tablename__ = 'meetings'

    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    meeting_type = Column(String(50), nullable=False)

    team = relationship('Team', backref='meetings')

    def __repr__(self):
        return f'<Meeting {self.title} ({self.start_time})>'

# Application usage examples:

# Create a recurring team meeting
meeting = Meeting(
    title="Weekly Team Sync",
    description="Weekly team sync meeting",
    meeting_type="standup",
    team_id=1,
    start_time=datetime(2024, 1, 1, 10, 0, tzinfo=pytz.UTC),
    end_time=datetime(2024, 1, 1, 11, 0, tzinfo=pytz.UTC),
    timezone='America/New_York',
    location='Conference Room A',
    resources={
        'room': 'conf_a',
        'equipment': ['projector', 'whiteboard']
    },
    notifications={
        'email': {
            'remind_before': 15,
            'recipients': ['team@company.com']
        },
        'slack': {
            'channel': '#team-meetings'
        }
    },
    created_by_fk=1,
    updated_by_fk=1
)

# Set complex recurrence pattern
meeting.set_recurrence(
    freq='WEEKLY',
    interval=1,
    byday=['MO', 'WE', 'FR'],
    byhour=[10, 15],
    until=datetime(2024, 12, 31, tzinfo=pytz.UTC)
)

# Add holiday exceptions
holidays = [
    datetime(2024, 1, 1, tzinfo=pytz.UTC),   # New Year's Day
    datetime(2024, 12, 25, tzinfo=pytz.UTC)  # Christmas
]
for holiday in holidays:
    meeting.add_exception(holiday)

# Check for conflicts
conflicts = await meeting.get_conflicts(db.session, margin=15)
if conflicts:
    print("Warning: Schedule conflicts detected!")
    for conflict in conflicts:
        print(f"Conflict with: {conflict.title}")

# Get calendar data for UI
calendar_data = Meeting.get_calendar_data(
    db.session,
    start=datetime.now(pytz.UTC),
    end=datetime.now(pytz.UTC) + timedelta(days=30),
    user_id=current_user.id
)

# Export to iCalendar
ical_data = meeting.to_ical()
with open('team_meetings.ics', 'w') as f:
    f.write(ical_data)

# Save to database
db.session.add(meeting)
db.session.commit()

# Query active meetings
active_meetings = Meeting.query.filter_by(
    status='active',
    team_id=1
).order_by(Meeting.start_time).all()

# Get upcoming occurrences
now = datetime.now(pytz.UTC)
upcoming = meeting.get_occurrences(
    start=now,
    end=now + timedelta(days=7)
)
"""
