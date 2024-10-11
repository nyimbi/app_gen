# from sqlalchemy_searchable import SearchQueryMixin
import humanize
import datetime
import hashlib
import math
import os
import sys
import inspect
from  base64 import b64encode, decode
from datetime import date, timedelta
from flask import Markup, escape
from flask_appbuilder import Model
from flask_appbuilder.models.decorators import renders
from flask_appbuilder.models.mixins import AuditMixin, FileColumn, ImageColumn
from geopy import Point, distance
from io import StringIO
from sqlalchemy import Column, String, text
from sqlalchemy.dialects.postgresql import *
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func, text
from sqlalchemy.sql import func, text
from sqlalchemy_utils import observes
from sqlalchemy_utils import TSVectorType

from sqlalchemy import (
    Boolean, CheckConstraint, Column, Date, DateTime, Float, ForeignKey, Integer, Numeric, String,
    Text, Interval
)

# We will inherit all our ModelMixins from this
class BaseModelMixin(object):

    @classmethod
    def mixin_model_cols(cls):
        return [column.name for column in cls.__table__.columns]

    @classmethod
    def mixin_cols(cls):
        # Get a list of all attributes
        attributes = dir(cls)

        # Filter out built-in methods and attributes
        user_defined_attributes = [attr for attr in attributes if not (attr.startswith('__') or attr.startswith('mixin_'))]

        # Get a list of user-defined data members
        data_members = [attribute for attribute in user_defined_attributes if
                        not inspect.isfunction(getattr(cls, attribute))]

        return data_members

    @classmethod
    def mixin_methods(cls):
        # Get a list of all attributes
        attributes = dir(cls)

        # Filter out built-in methods and attributes
        user_defined_attributes = [attr for attr in attributes if not attr.startswith('__')]

        # Get a list of user-defined methods
        methods = [method for method in user_defined_attributes if inspect.isfunction(getattr(cls, method)) and method.startswith('mixin_')]

        return methods

    @classmethod
    def mixin_attrs(cls):
        # Get a list of all attributes
        attributes = dir(cls)

        # Filter out built-in methods and attributes
        user_defined_attributes = [attr for attr in attributes if not attr.startswith('__')]

        return user_defined_attributes


### UTILITY Classes #####
class AuditMixinNullable(AuditMixin):
    """Altering the AuditMixin to use nullable fields
    Allows creating objects programmatically outside of CRUD
    TODO: Add Access tracking, Accessed_on, Seen_by etc
    """
    created_on = Column(
        DateTime, server_default=text("current_timestamp"), nullable=True
    )
    changed_on = Column(
        DateTime,
        server_default=text("current_timestamp"),
        onupdate=func.now(),
        nullable=True,
    )
    @declared_attr
    def created_by_fk(cls):  # noqa
        return Column(
            Integer, ForeignKey("ab_user.id"), default=cls.get_user_id, nullable=True
        )

    @declared_attr
    def changed_by_fk(cls):  # noqa
        return Column(
            Integer,
            ForeignKey("ab_user.id"),
            default=cls.get_user_id,
            onupdate=cls.get_user_id,
            nullable=True,
        )

    def _user_link(self, user):
        if not user:
            return ""
        url = "/prn/profile/{}/".format(user.username)
        return Markup('<a href="{}">{}</a>'.format(url, escape(user) or ""))

    @renders("created_by")
    def creator(self):  # noqa
        return self._user_link(self.created_by)

    @property
    def changed_by_(self):
        return self._user_link(self.changed_by)

    @renders("changed_on")
    def changed_on_(self):
        return Markup('<span class="no-wrap">{}</span>'.format(self.changed_on))

    @renders("changed_on")
    def modified(self):
        s = humanize.naturaltime(datetime.now() - self.changed_on)
        return Markup('<span class="no-wrap">{}</span>'.format(s))

    @property
    def icons(self):
        return """
        <a
                href="{self.datasource_edit_url}"
                data-toggle="tooltip"
                title="{self.datasource}">
            <i class="fa fa-database"></i>
        </a>
        """.format(
            **locals()
        )


class RefTypeMixin(BaseModelMixin):
    # id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    code = Column(String(20), default="0000", index=True)
    description = Column(String(100))
    notes = Column(Text, default='')

    def __repr__(self):
        return self.name

    @classmethod
    def mixin_fieldset(cls):
        return[
            {
                "label": "Identification",
                "fields":[
                    "name",
                    "code",
                    "description",
                    "notes"
                ]
            }
        ]
    @classmethod

    def mixin_fields(cls):
        return ["name", "code", "description", "notes"]



##############################
# How to create a Two Table Mixin
##############################
# class CreateTwoTablesMixin:
#     @classmethod
#     def __init_subclass__(cls):
#         super().__init_subclass__()
#         cls.create_tables()
#
#     @classmethod
#     def create_tables(cls):
#         class Table1(Model):
#             __tablename__ = f"{cls.__tablename__}_table1"
#             id = Column(Integer, primary_key=True)
#             field1 = Column(String(50), nullable=False)
#             field2 = Column(String(50), nullable=False)
#
#         class Table2(Model):
#             __tablename__ = f"{cls.__tablename__}_table2"
#             id = Column(Integer, primary_key=True)
#             table1_id = Column(Integer, ForeignKey(f"{Table1.__tablename__}.id"))
#             field3 = Column(String(50), nullable=False)
#             field4 = Column(String(50), nullable=False)
#
#         cls.Table1 = Table1
#         cls.Table2 = Table2




# How to create a Mixin that takes an argument
#
# class MyMixin:
#     @classmethod
#     def add_field(cls, field_name):
#         setattr(cls, field_name, Column(String(50)))
#
#     def do_something(self):
#         # Use the field here
#         pass

# Instantiate thus
# class MyModel(db.Model, MyMixin):
#     __tablename__ = 'my_table'
#     id = Column(Integer, primary_key=True)
#     name = Column(String(50))
#     MyMixin.add_field('new_field')
#
# class MyModel(db.Model, MyMixin):
#     __tablename__ = 'my_table'
#     id = Column(Integer, primary_key=True)
#     name = Column(String(50))
#     MyMixin.add_field('new_field')
#
#     def do_something_else(self, value):
#         self.new_field = value
#         self.do_something()

# ALTERNATIVELY do it like this
# class MyMixin:
#     def __init__(self, field_name):
#         self.field_name = field_name
#         setattr(self.__class__, field_name, Column(String(50)))
#
#     def do_something(self):
#         # Use the field here
#         pass
#
# class MyModel(db.Model, MyMixin('new_field')):
#     __tablename__ = 'my_table'
#     id = Column(Integer, primary_key=True)
#     name = Column(String(50))





class ProjectMixin(BaseModelMixin):
    @classmethod
    def __init_subclass__(cls):
        super().__init_subclass__()
        cls.create_tables()

    @classmethod
    def create_tables(cls):
        class ProjectModel(Model):
            __tablename__ = f"{cls.__tablename__}_project"

            pj_id = Column(Integer, primary_key=True)
            project_name = Column(String(50), nullable=False)
            project_description = Column(Text, nullable=True)
            project_start_date = Column(DateTime)
            project_end_date = Column(DateTime)
            project_duration = Column(Interval)
            activities = relationship('ActivityModel', backref=cls.__tablename__)

            @property
            def actual_project_duration(self):
                earliest_activity = min(self.activities, key=lambda x: x.actual_start_date)
                latest_activity = max(self.activities, key=lambda x: x.actual_end_date_date)
                return (latest_activity.end_date - earliest_activity.start_date).days

            @property
            def planned_project_duration(self):
                earliest_activity = min(self.activities, key=lambda x: x.planned_start_date)
                latest_activity = max(self.activities, key=lambda x: x.planned_end_date_date)
                return (latest_activity.end_date - earliest_activity.start_date).days


        class ActivityModel(Model):
            __tablename__ = f"{cls.__tablename__}_activities"

            act_id = Column(Integer, primary_key=True)
            pj_id = Column(Integer, ForeignKey(f"{ProjectModel.__tablename__}.pj_id"))
            activity_name = Column(String(100))
            priority = Column(Integer, default=5)
            segment = Column(Integer)
            task_group = Column(Integer)
            sequence = Column(Integer)

            action = Column(String(40))
            activity_description = Column(Text)
            goal = Column(Text)
            status = Column(String(40))

            planned_start_date = Column(Date, default=func.now())
            actual_start_date = Column(Date, default=func.now())
            start_delay = Column(Interval)
            start_notes = Column(String(100))

            planned_end_date = Column(Date, default=func.now())
            actual_end_date = Column(DateTime, nullable=True, default=func.now())
            end_delay = Column(Interval)
            end_notes = Column(String(100))

            deadline = Column(Date, default=func.now())
            # Admin Stuff
            not_started = Column(Boolean, default=True)
            early_start = Column(Boolean, default=False)
            late_start = Column(Boolean, default=False)
            completed = Column(Boolean, default=False)
            early_end = Column(Boolean, default=False)
            late_end = Column(Boolean, default=False)
            deviation_expected = Column(Boolean, default=False)

            contingency_plan = Column(Text)

            # Money
            budget = Column(Numeric(10, 2), default=0.00)
            spend_td = Column(Numeric(10, 2), default=0.00)
            balance_avail = Column(Numeric(10, 2), default=0.00)
            over_budget = Column(Boolean, default=False)
            under_budget = Column(Boolean, default=False)

            CheckConstraint("actual_start_date >= actual_end_date")

            def __repr__(self):
                return self.action + ":" + str(self.actual_start)

            @observes("actual_start", "planned_start")
            def start_delay_observer(self, actual_start, planned_start):
                self.start_delay = planned_start - actual_start

            def before_insert(self):
                if self.actual_start_date and self.planned_start_date and self.actual_start_date < self.planned_start_date:
                    self.early_start = True

            def before_update(self):
                if self.actual_start_date and self.actual_start_date < self.planned_start_date:
                    self.early_start = True

            @validates('actual_start_date')
            def update_start_delay(self, key, value):
                self.start_delay = datetime.datetime(self.actual_start_date) - datetime.datetime(self.planned_start_date)
                if self.start_delay > 0:
                    self.late_start = True
                    self.early_start = False
                else:
                    self.late_start = False
                    self.early_start = True

            @validates('actual_end_date')
            def update_end_delay(self, key, value):
                self.end_delay = datetime.datetime(self.actual_end_date) - datetime.datetime(self.planned_end_date)
                if self.end_delay > 0:
                    self.late_end = True
                    self.early_end = False
                else:
                    self.late_end = False
                    self.early_end = True

            @renders('delay_of_start')
            def start_delay_(self):
                return humanize.naturaltime(self.start_delay)


            def get_overlapping_activities(self):
                overlapping_activities = []
                for activity in self.project.activities:
                    if activity.id != self.id and self.start_time < activity.end_time and activity.start_time < self.end_time:
                        overlapping_activities.append(activity)
                return overlapping_activities


            @renders("actual_start")
            def started(self):
                s = humanize.naturaltime(datetime.now() - self.actual_start_date)
                return Markup('<span class="no-wrap">Start: {}</span>'.format(s))

            @renders("delayed")
            def delayed(self):
                s = humanize.naturaltime(datetime.now() - self.planned_end_date)
                return Markup('<span class="no-wrap"> Delayed by: {}</span>'.format(s))

            @renders("duration")
            def lasted(self):
                dur = humanize.naturaltime(self.actual_end_date - self.actual_start_date)
                return Markup('<span class="no-wrap">Lasted: {}</span>'.format(dur))

        cls.Project = ProjectModel
        cls.Activities = ActivityModel

        @classmethod
        def get_pj_fieldset(cls):
            return [
                {
                    "label": "Project Summary",
                    "fields": [
                        "project_name",
                        "project_description",
                        "project_start_date",
                        "project_end_date",
                        "project_duration",
                    ],
                },
                {
                    "label": "Activity Details",
                    "fields": [
                        "activity_name",
                        "priority",
                        "segment",
                        "task_group",
                        "sequence",
                        "action",
                        "activity_description",
                        "goal",
                        "status",
                        "planned_start_date",
                        "actual_start_date",
                        "start_delay",
                        "start_notes",
                        "planned_end_date",
                        "actual_end_date",
                        "end_delay",
                        "end_notes",
                        "deadline",
                        "not_started",
                        "early_start",
                        "late_start",
                        "completed",
                        "early_end",
                        "late_end",
                        "deviation_expected",
                        "contingency_plan",

                    ],
                },
                {
                    "label": "Budget",
                    "fields": [
                        "budget",
                        "spend_td",
                        "balance_avail",
                        "over_budget",
                        "under_budget",
                    ]
                }
            ]


class TransientMixin(BaseModelMixin):
    started_date = Column(DateTime, default=datetime.datetime.now())
    ended_date = Column(DateTime)
    is_active = Column(Boolean)
    is_suspended = Column(Boolean)
    active_from_date = Column(DateTime)
    deactivate_date = Column(DateTime)
    expiry_days = Column(Integer, default=365, nullable=False)
    expired = Column(Boolean, default=False)
    display = Column(Boolean)  # TODO Only display of between activate and deactivate dates
    extend_expiry_on_access = Column(Boolean, default=True)

    @hybrid_property
    def expiry_date(self):
        return self.started_date + timedelta(days=self.expiry_days)

    @hybrid_property
    def expired(self):
        return datetime.now() > self.expiry_date

    @hybrid_property
    def display(self):
        if self.expiry_date and self.expiry_date > datetime.now():
            return False

    @classmethod
    def get_transient_fieldset(cls):
        return [
            {
                "label": "Start",
                "fields": [
                    "started_date",
                    "is_active",
                    "is_suspended",
                    "active_from_date",
                    "expired",
                ],
            },
            {
                "label": "End",
                "fields": [
                    "ended_date",
                    "is_active",
                    "is_suspended",
                    "deactivate_date",
                    "expiry_days",
                ],
            },
            {
                "label": "Display",
                "fields": ["display", "extend_expiry_on_access"],
            },
        ]


class PlaceMixin(BaseModelMixin):
    """
    if you declare:
    class MyModel(PlaceMixin, Model)

    you can then use clossest_instance like this:
    my_latitude = 37.7749
    my_longitude = -122.4194
    closest_instance = MyModel.find_closest_instance(my_latitude, my_longitude)

    """
    place_name = Column(String(40))
    place_description = Column(Text)

    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Float)
    map = Column(Text, default="")
    info = Column(Text, default="")
    pin = Column(Boolean)  # Do we put a pin
    pin_color = Column(String(20))
    pin_icon = Column(String(50))
    centered = Column(Boolean)
    nearest_feature = Column(String(100))

    def __repr__(self):
        return self.place_name

    def validate_latitude(self, latitude):
        if latitude < -90 or latitude > 90:
            raise ValueError('Latitude must be between -90 and 90 degrees')

    def validate_longitude(self, longitude):
        if longitude < -180 or longitude > 180:
            raise ValueError('Longitude must be between -180 and 180 degrees')

    def validate(self):
        self.validate_latitude(self.latitude)
        self.validate_longitude(self.longitude)

    @classmethod
    def find_closest_instance(cls, latitude, longitude):
        instances = cls.query.all()
        closest_instance = None
        closest_distance = float('inf')
        for instance in instances:
            distance = cls.haversine(latitude, longitude, instance.latitude, instance.longitude)
            if distance < closest_distance:
                closest_distance = distance
                closest_instance = instance
        return closest_instance

    @staticmethod
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371  # Radius of the earth in km
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        a = math.sin(dLat / 2) * math.sin(dLat / 2) + math.cos(math.radians(lat1)) * math.cos(
            math.radians(lat2)) * math.sin(dLon / 2) * math.sin(dLon / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        h_distance = R * c  # Distance in km
        return h_distance


class PersonCRMMixin(BaseModelMixin):
    net_worth = Column(Integer)
    yearly_income = Column(Integer)
    yearly_Income_range = Column(Text)
    tax_bracket_range = Column(Text)
    highest_education_level = Column(Text)
    ethnicity = Column(Text)
    children_count = Column(Integer)
    dependents_count = Column(Integer)

    marital_status = Column(Text)
    wedding_anniversary = Column(Date)
    should_forget = Column(Boolean)
    primary_hobby = Column(Text)
    hobbies = Column(Text)
    religion = Column(Text)
    influencer_rating = Column(Text)
    socio_economic_index = Column(Text)
    occupation = Column(Text)
    current_employer_name = Column(Text)

    consumer_credit_score = Column(Text)
    consumer_credit_score_provider_name = Column(Text)
    personality_model = Column(Text)
    main_personal_value_type = Column(Text)
    main_life_attitude_type = Column(Text)
    residence_capture_method = Column(Text)

    is_home_owner = Column(Boolean)
    is_car_owner = Column(Boolean)
    is_good_driver = Column(Boolean)
    is_good_student = Column(Boolean)
    is_high_risk_hobby = Column(Boolean)

    # Criminal History
    minor_citation_count = Column(Integer)
    major_citation_count = Column(Integer)
    convictions_count = Column(Integer)

    do_not_track = Column(Boolean)
    do_not_track_update_date = Column(DateTime)
    do_not_track_reason = Column(Text)

    do_not_market = Column(Boolean)
    do_not_market_update_date = Column(DateTime)
    do_not_market_reason = Column(Text)

    do_not_process = Column(Boolean)
    do_not_process_from_update = Column(Boolean)
    do_not_process_reason = Column(Text)

    do_not_profile = Column(Boolean)
    do_not_profile_from_update_date = Column(DateTime)
    do_not_profile_reason = Column(Text)

    do_not_merge = Column(Boolean)
    do_not_merge_from_update_date = Column(DateTime)
    do_not_merge_reason = Column(Text)

    forget_me = Column(Boolean)
    forget_me_date = Column(Date)


class PersonMixin(BaseModelMixin):
    salutation = Column(String(20))
    first_name = Column(String(40), nullable=False, index=True)
    other_names = Column(String(40), nullable=True, index=True)
    last_name = Column(String(40), nullable=False, index=True)
    suffix = Column(String(40))
    preferred_name = Column(String(40))
    pronouns = Column(Text)
    date_of_birth = Column(Date)

    country_of_residence = Column(Text)  # Attach to geonames
    country_of_citizenship = Column(Text)

    marital_status = Column(String(10))
    photo = Column(ImageColumn(thumbnail_size=(30, 30, True), size=(300, 300, True)))
    avatar = Column(ImageColumn(thumbnail_size=(30, 30, True), size=(300, 300, True)))
    language_code = Column(String(10))

    @property
    def age(self):
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))

    @property
    def is_adult(self):
        return self.age >= 18

    @property
    def age_today(self):
        today = date.today()
        delta = today - self.date_of_birth
        years = delta.days // 365
        days = delta.days % 365
        return f'<span class="no-wrap">{years} years, {days} days</span>'

    @property
    def days_to_birthday(self):
        today = date.today()
        birthday_this_year = date(today.year, self.date_of_birth.month, self.date_of_birth.day)
        if birthday_this_year < today:
            birthday_this_year = date(today.year + 1, self.date_of_birth.month, self.date_of_birth.day)
        delta = birthday_this_year - today
        return delta.days


    def ViewName(self):
        return self.__class__.__name__ + 'View.show'

    def __repr__(self):
        return '(' + str(self.id) + ') ' + self.firs_tname + ' ' + self.surname



class ContactMixin(BaseModelMixin):
    full_name = Column(String(100))
    nickname = Column(String(100))
    company = Column(String(100))
    job_title = Column(String(100))
    phone_home = Column(String(20))
    phone_work = Column(String(20))
    phone_mobile = Column(String(20))
    fax = Column(String(20))
    email_home = Column(String(100))
    email_work = Column(String(100))
    address_street = Column(String(100))
    address_city = Column(String(100))
    address_state = Column(String(50))
    address_postal_code = Column(String(20))
    address_country = Column(String(50))
    website = Column(String(100))
    social_linkedin = Column(String(100))
    social_facebook = Column(String(100))
    social_twitter = Column(String(100))
    social_instagram = Column(String(100))
    social_skype = Column(String(100))
    photo_url = Column(String(100))
    birthdate = Column(Date)
    anniversary = Column(Date)
    note = Column(String(200))
    title = Column(String(50))
    role = Column(String(50))
    organization = Column(String(100))
    department = Column(String(100))
    instant_messaging_skype = Column(String(100))
    instant_messaging_aim = Column(String(100))
    instant_messaging_whatsapp = Column(String(100))
    instant_messaging_vkontakt = Column(String(100))
    related_spouse = Column(String(100))
    related_children = Column(String(100))
    related_parents = Column(String(100))

    @hybrid_property
    def full_name(self):
        name_parts = []
        first_name = getattr(self, 'first_name', None)
        middle_name = getattr(self, 'middle_name', None)
        last_name = getattr(self, 'last_name', None)
        surname = getattr(self, 'surname_name', None)

        if first_name:
            name_parts.append(first_name)
        if middle_name:
            name_parts.append(middle_name)
        if last_name:
            name_parts.append(last_name)
        if surname:
            name_parts.append(surname)
        if not name_parts:
            return None
        return " ".join(name_parts)

    def to_vcard(self):
        output = StringIO()
        output.write("BEGIN:VCARD\n")
        output.write("VERSION:3.0\n")
        for field in self.__table__.columns:
            if field.name == 'id':
                continue
            value = getattr(self, field.name)
            if value is not None and value != '':
                output.write(f"{field.name.upper()}:{value}\n")
        output.write("END:VCARD\n")
        return output.getvalue()




class WebMixin(BaseModelMixin):
    # Where
    scheme = Column(String(10), default="http", nullable=False)
    domain = Column(String(300))
    web_netloc = Column(String(400))
    web_path = Column(String(1000))
    web_params = Column(String(1000))
    web_query = Column(String(1000))
    web_fragment = Column(String(1000))

    full_url = Column(String(1000))
    url = Column(
        String(1000), nullable=False
    )  # Use this to load the list of urls, we process url to get the other things
    canonical_link = Column(String(1000))
    link_hash = Column(String(128))  # So that we never re-crawl the link
    content_hash = Column(String(128))  # We don't want the same content over and over

    _salt = Column(String(12))

    @hybrid_property
    def salt(self):
        """Generates a cryptographically random salt and sets its Base64 encoded
        version to the salt column, and returns the encoded salt.
        """
        if not self.id and not self._salt:
            self._salt = b64encode(os.urandom(8))

        return self._salt

    # What
    title = Column(String(300))
    description = Column(String(200))
    html = Column(Text)
    txt = Column(Text)
    summary = Column(Text, default="")
    # keywords = Column(String(500))
    asset = Column(ImageColumn(thumbnail_size=(30, 30, True), size=(300, 300, True)))
    lang = Column(String(20))
    tags = Column(String(500))
    word_count = Column(Integer)
    category_count = Column(Integer)
    article_count = Column(Integer)
    link_count = Column(Integer)  # Number of links on the page
    apparent_encoding = Column(String(15))

    # Who : Setup in the model
    author = Column(String(500))

    # When
    publish_date = Column(DateTime)
    download_date = Column(DateTime, default=func.now())
    download_count = Column(Integer)
    edit_date = Column(DateTime, default=func.now())

    # Admin
    version = Column(String(20))
    is_downloaded = Column(Boolean, default=False)
    is_image = Column(Boolean, default=False)
    is_video = Column(Boolean, default=False)
    is_feed = Column(Boolean, default=False)
    is_text = Column(Boolean, default=False)
    has_risk_words = Column(Boolean)

    # Ranking
    of_interest = Column(Boolean, default=False)
    ranking = Column(Integer, CheckConstraint("(ranking >= 0) and (ranking <=10)"))
    for_review = Column(Boolean, default=False)

    # Trinary Ranking
    is_positive = Column(Boolean, default=False)
    is_negative = Column(Boolean, default=False)
    is_neutral = Column(Boolean, default=True)
    iterations = Column(Integer, default=0)

    # Sentiment Analysis
    sentiment = Column(String(100))
    sentiment_colour = Column(String(50))

    # Proper Nouns
    noun_count = Column(Integer)
    nouns = Column(Text)



# TODO Expand the DocumentMixin to make it searchable
# mixins.py





class DocMixin(BaseModelMixin):
    # query_class = DocQuery
    mime_type = Column(String(60), default="application/pdf")
    doc = Column(ImageColumn(thumbnail_size=(30, 30, True), size=(300, 300, True)))
    doc_text = Column(Text)
    doc_binary = Column(FileColumn)
    doc_title = Column(String(200))
    subject = Column(String(100))
    author = Column(String(100))
    keywords = Column(String(200))
    comments = Column(Text)

    # Metadata
    doc_type = Column(String(5), default="pdf")
    char_count = Column(Integer)
    word_count = Column(Integer)
    lines = Column(Integer)
    paragraphs = Column(Integer)
    gpt_token_count = Column(Integer)
    grammar_checked = Column(Boolean)
    doc_summary = Column(Boolean)
    doc_spell_checked = Column(Boolean)
    doc_prompt = Column(Text)
    doc_gpt_ver = Column(String(40))
    doc_maj_version = Column(Integer)
    doc_min_version = Column(Integer)
    doc_format = Column(String(40))
    doc_downloadable = Column(Boolean)
    doc_template = Column(Text)
    doc_rendered = Column(Boolean)
    doc_render = Column(FileColumn)

    file_size_bytes = Column(Integer)
    producer_prog = Column(String(40))
    immutable = Column(Boolean, default=False)

    page_size = Column(String(40))
    page_count = Column(Integer)
    hashx = Column(String(40))

    # if is Audio
    is_audio = Column(Boolean)
    audio_duration_secs = Column(Integer)
    audio_frame_rate = Column(Integer)
    audio_channels = Column(Integer)

    # search_vector = Column(TSVectorType("doc_text", "doc_title"))

    @declared_attr
    def search_vector(cls):
        return Column(
            TSVectorType("doc_title", "doc_content","comments", weights={"title": "A", "content": "B"}),
            nullable=False,
            index=True,
        )

    @validates('doc_text')
    def update_doc_info(self, key, value):
        # update doc_length
        self.doc_length = len(value)

        # update word_count
        word_list = value.split()
        self.word_count = len(word_list)

        return value

    @classmethod
    def search(cls, session, query, *, limit=None, offset=None):
        """
        Perform a full-text search on the doc_title, doc_content and comment fields.

        :param session: A SQLAlchemy session object.
        :param query: The search query.
        :param limit: The maximum number of results to return.
        :param offset: The starting index of the results.
        :return: A list of matching objects.
        """
        search_query = text("plainto_tsquery(:query)").params(query=query)
        results = (
            session.query(cls)
            .filter(cls.search_vector.match(search_query))
            .order_by(cls.search_vector.match(search_query).desc())
        )

        if limit is not None:
            results = results.limit(limit)
        if offset is not None:
            results = results.offset(offset)

        return results.all()
