import datetime, enum
from flask_appbuilder import Model
from sqlalchemy import Column, Integer, Boolean, String, Float, Enum, ForeignKey, Date, DateTime, Text
from sqlalchemy.orm import relationship, backref


import os
import sys
import enum
import inspect
import datetime
import shutils
from datetime import timedelta, datetime, date

from sqlalchemy.orm import relationship, query, defer, deferred, column_property, mapper
from sqlalchemy.schema import FetchedValue
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy import (Column, Integer, String, ForeignKey,
    Sequence, Float, Text, BigInteger, Date, SmallInteger, BigInteger, 
    DateTime, Time, Boolean, Index, CheckConstraint, Interval, # MatchType  
    UniqueConstraint, ForeignKeyConstraint, Numeric, LargeBinary , Table, func, Enum,
    text)

# IMPORT Postgresql Specific Types
from sqlalchemy.dialects.postgresql import *
from sqlalchemy.dialects.postgresql import (
    ARRAY, BIGINT, BIT, BOOLEAN, BYTEA, CHAR, CIDR, DATE,
    DOUBLE_PRECISION, ENUM, FLOAT, HSTORE, INET, INTEGER,
    INTERVAL, JSON, JSONB, MACADDR, NUMERIC, OID, REAL, SMALLINT, TEXT,
    TIME, TIMESTAMP, UUID, VARCHAR, INT4RANGE, INT8RANGE, NUMRANGE,
    DATERANGE, TSRANGE, TSTZRANGE, TSVECTOR, aggregate_order_by )

from flask_appbuilder import Model
from flask_appbuilder.models.mixins import AuditMixin, FileColumn, ImageColumn, UserExtensionMixin
from flask_appbuilder.filemanager import ImageManager

from flask_appbuilder.models.decorators import renders
from sqlalchemy_utils import aggregated, force_auto_coercion, observes
from sqlalchemy_utils.types import TSVectorType   #Searchability look at DocMixin
from sqlalchemy.ext.associationproxy import association_proxy

from flask_appbuilder.security.sqla.models import User
from geoalchemy2 import Geometry

# To create GraphSQL API
# import graphene
# from graphene_sqlalchemy import SQLAlchemyObjectType

# Versioning Mixin
# from sqlalchemy_continuum import make_versioned
#Add __versioned__ = {}


# from sqlalchemy_searchable import make_searchable
# from flask_graphql import GraphQLView

# ActiveRecord Model Features
# from sqlalchemy_mixins import AllFeaturesMixin, ActiveRecordMixin


# from .model_mixins import *

# Here is how to extend the User model
#class UserExtended(Model, UserExtensionMixin):
#    contact_group_id = Column(Integer, ForeignKey('contact_group.id'), nullable=True)
#    contact_group = relationship('ContactGroup')

# UTILITY CLASSES
# import arrow,


# Initialize sqlalchemy_utils
#force_auto_coercion()
# Keep versions of all data
# make_versioned()
# make_searchable()




class t_agent_role(enum.Enum):
   AGENT = 'agent'
   SUB_AGENT = 'sub_agent'
   SUPER_AGENT = 'super_agent'
   AGGREGATOR = 'aggregator'

class t_card_trans_type(enum.Enum):
   PURCHASE = 'purchase'
   BALANCE = 'balance'
   REFUND = 'refund'
   CASH_ADVANCE = 'cash_advance'
   CASH_BACK = 'cash_back'
   PRE_AUTHORIZATION = 'pre_authorization'
   PRE_AUTHORIZATION_COMPLETION = 'pre_authorization_completion'
   CARD_VERIFICATION = 'card_verification'
   TRANSACTION = 'transaction'
   SETTLEMENT = 'settlement'

class t_date_macro(enum.Enum):
   ALL = 'All'
   TODAY = 'Today'
   THISWEEK = 'ThisWeek'
   THISWEEKTODATE = 'ThisWeekToDate'
   THISMONTH = 'ThisMonth'
   THISMONTHTODATE = 'ThisMonthToDate'
   THISCALENDARQUARTER = 'ThisCalendarQuarter'
   THISCALENDARQUARTERTODATE = 'ThisCalendarQuarterToDate'
   THISFISCALQUARTER = 'ThisFiscalQuarter'
   THISFISCALQUARTERTODATE = 'ThisFiscalQuarterToDate'
   THISCALENDARYEAR = 'ThisCalendarYear'
   THISCALENDARYEARTODATE = 'ThisCalendarYearToDate'
   THISFISCALYEAR = 'ThisFiscalYear'
   THISFISCALYEARTODATE = 'ThisFiscalYearToDate'
   YESTERDAY = 'Yesterday'
   LASTWEEK = 'LastWeek'
   LASTWEEKTODATE = 'LastWeekToDate'
   LASTMONTH = 'LastMonth'
   LASTMONTHTODATE = 'LastMonthToDate'
   LASTCALENDARQUARTER = 'LastCalendarQuarter'
   LASTCALENDARQUARTERTODATE = 'LastCalendarQuarterToDate'
   LASTFISCALQUARTER = 'LastFiscalQuarter'
   LASTFISCALQUARTERTODATE = 'LastFiscalQuarterToDate'
   LASTCALENDARYEAR = 'LastCalendarYear'
   LASTCALENDARYEARTODATE = 'LastCalendarYearToDate'
   LASTFISCALYEAR = 'LastFiscalYear'
   LASTFISCALYEARTODATE = 'LastFiscalYearToDate'
   NEXTWEEK = 'NextWeek'
   NEXTFOURWEEKS = 'NextFourWeeks'
   NEXTMONTH = 'NextMonth'
   NEXTCALENDARQUARTER = 'NextCalendarQuarter'
   NEXTCALENDARYEAR = 'NextCalendarYear'
   NEXTFISCALQUARTER = 'NextFiscalQuarter'
   NEXTFISCALYEAR = 'NextFiscalYear'

class t_doc_category(enum.Enum):
   IDENTIFICATION = 'Identification'
   CERTIFICATION = 'Certification'
   FINANCIAL = 'Financial'
   EDUCATIONAL = 'Educational'
   LEGAL_DOCUMENT = 'Legal_Document'
   UTILITY_BILL = 'Utility_Bill'
   MEDICAL_REPORT = 'Medical_Report'
   CONTRACT = 'Contract'
   INSURANCE_POLICY = 'Insurance_Policy'
   TAX_DOCUMENT = 'Tax_Document'

class t_doc_status(enum.Enum):
   NOT_STARTED = 'Not_Started'
   DRAFT = 'Draft'
   IN_PROGRESS = 'In_Progress'
   AWAITING_REVIEW = 'Awaiting_Review'
   UNDER_REVIEW = 'Under_Review'
   REVIEW_COMPLETED = 'Review_Completed'
   REVISIONS_NEEDED = 'Revisions_Needed'
   SUBMITTED = 'Submitted'
   APPROVED = 'Approved'
   PARTIALLY_APPROVED = 'Partially_Approved'
   REJECTED = 'Rejected'
   CANCELLED = 'Cancelled'
   ARCHIVED = 'Archived'
   PUBLISHED = 'Published'
   SUSPENDED = 'Suspended'
   VOIDED = 'Voided'
   COMPLETED = 'Completed'
   EXPIRED = 'Expired'
   RENEWED = 'Renewed'
   LOCKED = 'Locked'
   MERGED = 'Merged'
   ROLLBACK = 'Rollback'
   CONFLICT = 'Conflict'
   QUEUED_FOR_REVIEW = 'Queued_for_Review'
   QUEUED_FOR_PUBLISH = 'Queued_for_Publish'
   DEPRECATED = 'Deprecated'
   UNPUBLISHED = 'Unpublished'
   IN_TRANSLATION = 'In_Translation'
   VALIDATION_FAILED = 'Validation_Failed'
   VALIDATION_PASSED = 'Validation_Passed'
   DIGITIZED = 'Digitized'
   IN_SIGNATURE_PROCESS = 'In_Signature_Process'
   SIGNATURE_COMPLETED = 'Signature_Completed'
   SIGNATURE_FAILED = 'Signature_Failed'
   IN_AUDIT = 'In_Audit'
   AUDIT_COMPLETED = 'Audit_Completed'
   IN_TRANSIT = 'In_Transit'
   RECEIVED = 'Received'
   SENT = 'Sent'

class t_gender(enum.Enum):
   MALE = 'Male'
   FEMALE = 'Female'
   NON_BINARY = 'Non_Binary'
   PREFER_NOT_TO_SAY = 'Prefer_Not_to_Say'
   OTHER = 'Other'

class t_interval(enum.Enum):
   NONE = 'None'
   PER_SECOND = 'Per_Second'
   PER_MINUTE = 'Per_Minute'
   HOURLY = 'Hourly'
   DAILY = 'Daily'
   WEEKLY = 'Weekly'
   BIWEEKLY = 'Biweekly'
   MONTHLY = 'Monthly'
   BIMONTHLY = 'Bimonthly'
   QUARTERLY = 'Quarterly'
   SEMI_ANNUALLY = 'Semi_Annually'
   ANNUALLY = 'Annually'
   CUSTOM = 'Custom'
   WORKDAYS = 'Workdays'
   WEEKENDS = 'Weekends'
   MONDAY = 'MONDAY'
   TUESDAY = 'TUESDAY'
   WEDNESDAY = 'WEDNESDAY'
   THURSDAY = 'THURSDAY'
   FRIDAY = 'FRIDAY'
   SATURDAY = 'SATURDAY'
   SUNDAY = 'SUNDAY'
   FIRST_DAY_MONTH = 'FIRST_DAY_MONTH'
   LAST_DAY_MONTH = 'LAST_DAY_MONTH'
   FIRST_WEEKDAY = 'FIRST_WEEKDAY'
   LAST_WEEKDAY = 'LAST_WEEKDAY'
   EVERY_X_DAYS = 'EVERY_X_DAYS'
   EVERY_X_WEEKS = 'EVERY_X_WEEKS'
   EVERY_X_MONTHS = 'EVERY_X_MONTHS'
   EVERY_X_YEARS = 'EVERY_X_YEARS'

class t_org_type(enum.Enum):
   INDIVIDUAL = 'Individual'
   BUSINESS_NAME = 'Business_Name'
   SOLE_PROPRIETORSHIP = 'Sole_Proprietorship'
   PRIVATE_LIMITED_COMPANY = 'Private_Limited_Company'
   PUBLIC_LIMITED_COMPANY = 'Public_Limited_Company'
   PUBLIC_COMPANY_LIMITED_BY_GUARANTEE = 'Public_Company_Limited_by_Guarantee'
   PRIVATE_UNLIMITED_COMPANY = 'Private_Unlimited_Company'
   PUBLIC_UNLIMITED_COMPANY = 'Public_Unlimited_Company'

class t_payment_method(enum.Enum):
   CASH = 'cash'
   CREDIT_CARD = 'credit_card'
   DEBIT_CARD = 'debit_card'
   PREPAID_CARD = 'prepaid_card'
   COMMERCIAL_CARD = 'commercial_card'
   DEBT = 'debt'
   BANK = 'bank'
   MOBILE = 'mobile'
   COUPON = 'coupon'
   ORDER = 'order'
   WITHDRAWAL = 'withdrawal'
   FUND_WALLET = 'fund_wallet'
   CHEQUE = 'cheque'
   BANK_TRANSFER = 'bank_transfer'
   CRYPTO = 'crypto'
   BARTER = 'barter'
   WIRE_TRANSFER = 'wire_transfer'
   CONTACTLESS = 'contactless'
   GIFT_CARD = 'gift_card'
   LOYALTY_POINTS = 'loyalty_points'
   MONEY_ORDER = 'money_order'
   ESCROW = 'escrow'
   INSTALLMENT = 'installment'
   INVOICE = 'invoice'
   PREPAID = 'prepaid'
   QR_CODE = 'qr_code'
   DIGITAL_WALLET = 'digital_wallet'
   AUTOMATIC_DEBIT = 'automatic_debit'
   CASH_ON_DELIVERY = 'cash_on_delivery'
   POSTPAID = 'postpaid'
   THIRD_PARTY = 'third_party'
   TRADE_CREDIT = 'trade_credit'

class t_person_role(enum.Enum):
   NEXT_OF_KIN = 'next_of_kin'
   COMPANY_DIRECTOR = 'company_director'
   POS_OPERATOR = 'pos_operator'
   FIELD_SUPPORT = 'field_support'
   CUSTOMER = 'customer'
   REFEREE = 'referee'
   SUPERVISOR = 'supervisor'

class t_severity_level(enum.Enum):
   INSIGNIFICANT = 'Insignificant'
   TRIVIAL = 'Trivial'
   LOW = 'Low'
   MODERATE = 'Moderate'
   SIGNIFICANT = 'Significant'
   HIGH = 'High'
   URGENT = 'Urgent'
   SEVERE = 'Severe'
   EXTREME = 'Extreme'
   CRITICAL = 'Critical'

class t_transaction_status(enum.Enum):
   PENDING = 'pending'
   AUTHORIZED = 'authorized'
   COMPLETED = 'completed'
   FAILED = 'failed'
   CANCELLED = 'cancelled'
   REFUNDED = 'refunded'
   REVERSED = 'reversed'
   HOLD = 'hold'
   SUSPENDED = 'suspended'
   DISPUTED = 'disputed'
   DELIVERED = 'delivered'
   SETTLEMENT_PENDING = 'settlement_pending'
   SETTLED = 'settled'
   REJECTED = 'rejected'
   EXPIRED = 'expired'
   PENDING_VERIFICATION = 'pending_verification'
   HOLD_FOR_REVIEW = 'hold_for_review'
   PARTIALLY_COMPLETED = 'partially_completed'
   PARTIALLY_REFUNDED = 'partially_refunded'
   PARTIALLY_REVERSED = 'partially_reversed'
   COMPLETED_WITH_ERRORS = 'completed_with_errors'
   BATCH_PROCESSING = 'batch_processing'
   DEFERRED = 'deferred'
   WAITING_FOR_AUTHORIZATION = 'waiting_for_authorization'
   PROCESSING = 'processing'
   PENDING_FUNDS_AVAILABILITY = 'pending_funds_availability'
   PENDING_REVIEW = 'pending_review'
   PENDING_CONFIRMATION = 'pending_confirmation'
   WAITING_FOR_SETTLEMENT = 'waiting_for_settlement'
   PENDING_RECONCILIATION = 'pending_reconciliation'
   PENDING_DISBURSEMENT = 'pending_disbursement'
   CHARGEBACK_INITIATED = 'chargeback_initiated'
   CHARGEBACK_RESOLVED = 'chargeback_resolved'
   PENDING_CAPTURE = 'pending_capture'
   CAPTURED = 'captured'
   VOIDED = 'voided'
   IN_QUEUE = 'in_queue'
   MANUAL_INTERVENTION_REQUIRED = 'manual_intervention_required'
   GATEWAY_TIMEOUT = 'gateway_timeout'
   FRAUD_ALERT = 'fraud_alert'
   UNDER_AUDIT = 'under_audit'
   AUDIT_COMPLETED = 'audit_completed'
   CURRENCY_CONVERSION = 'currency_conversion'
   CURRENCY_CONVERSION_COMPLETED = 'currency_conversion_completed'
   ESCALATED = 'escalated'
   DE_ESCALATED = 'de_escalated'
   PENDING_APPROVAL = 'pending_approval'
   APPROVED = 'approved'
   DECLINED = 'declined'
   RE_ATTEMPTED = 're_attempted'
   RE_SCHEDULED = 're_scheduled'
   INSUFFICIENT_FUNDS = 'insufficient_funds'
   VERIFICATION_FAILED = 'verification_failed'
   VERIFICATION_SUCCESSFUL = 'verification_successful'
   PENDING_CLEARANCE = 'pending_clearance'
   CLEARED = 'cleared'
   RE_INITIATED = 're_initiated'
   SPLIT_TRANSACTION = 'split_transaction'
   CONSOLIDATED = 'consolidated'

class t_verification_status(enum.Enum):
   PENDING = 'pending'
   KYC_SUBMITTED = 'kyc_submitted'
   KYC_APPROVED = 'kyc_approved'
   KYC_REJECTED = 'kyc_rejected'
   ESCALATED = 'escalated'
   CONTRACTED = 'contracted'
   ACTIVE = 'active'
   SUSPENDED = 'suspended'
   INACTIVE = 'inactive'
   CONTRACT_TERMINATED = 'contract_terminated'
   DOCS_EXPIRED = 'docs_expired'
   UNDER_REVIEW = 'under_review'
   LOCKED = 'locked'
   AWAITING_RENEWAL = 'awaiting_renewal'
   RENEWAL_REJECTED = 'renewal_rejected'
   VERIFICATION_FAILED = 'verification_failed'
class Tech_parameters(Model):
    __tablename__ = "Tech_Parameters"
    key = Column(String, primary_key=True, nullable=False)
    value = Column(Text)
    enabled = Column(Boolean)
    notes = Column(Text)


class Ab_permission(Model):
    __tablename__ = "ab_permission"
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)


class Ab_register_user(Model):
    __tablename__ = "ab_register_user"
    id = Column(Integer, primary_key=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    username = Column(String, nullable=False)
    password = Column(String)
    email = Column(String, nullable=False)
    registration_date = Column(DateTime, server_default=text('NOW()'))
    registration_hash = Column(String)


class Ab_role(Model):
    __tablename__ = "ab_role"
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)


class Ab_user(Model):
    __tablename__ = "ab_user"
    id = Column(Integer, primary_key=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    username = Column(String, nullable=False)
    password = Column(String)
    active = Column(Boolean)
    email = Column(String, nullable=False)
    last_login = Column(DateTime, server_default=text('NOW()'))
    login_count = Column(Integer)
    fail_login_count = Column(Integer)
    created_on = Column(DateTime, server_default=text('NOW()'))
    changed_on = Column(DateTime, server_default=text('NOW()'))
    created_by_fk = Column(Integer, ForeignKey("ab_user.id"))
    changed_by_fk = Column(Integer, ForeignKey("ab_user.id"))
    changed_by = relationship("Ab_user", remote_side=[id], backref="subordinates")
    created_by = relationship("Ab_user", remote_side=[id], backref="subordinates")


class Ab_view_menu(Model):
    __tablename__ = "ab_view_menu"
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)


class Agent_tier(Model):
    __tablename__ = "agent_tier"
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String)
    notes = Column(Text)


class Bank(Model):
    __tablename__ = "bank"
    id = Column(Integer, primary_key=True, nullable=False)
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    category = Column(Integer)
    swift_code = Column(String)
    sort_code = Column(String)
    iban = Column(String)
    cust_care_phone = Column(String)
    cust_care_email = Column(String)
    escalation_contact = Column(Text)
    created_on = Column(DateTime, server_default=text('NOW()'))
    updated_on = Column(DateTime, server_default=text('NOW()'))


class Biller_category(Model):
    __tablename__ = "biller_category"
    biller_cat_id = Column(Integer, primary_key=True, nullable=False)
    biller_cat_name = Column(String)
    biller_cat_notes = Column(Text)


class Contact_type(Model):
    __tablename__ = "contact_type"
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    is_digital = Column(Boolean)
    requires_verification = Column(Boolean)
    max_length = Column(Integer)
    icon_url = Column(String)
    created_at = Column(DateTime, server_default=text('NOW()'))
    updated_at = Column(DateTime, server_default=text('NOW()'))


class Country(Model):
    __tablename__ = "country"
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String)
    code = Column(String)
    phone_code = Column(Integer)


class Coupon(Model):
    __tablename__ = "coupon"
    coupon_id = Column(Integer, primary_key=True, nullable=False)
    coupon_value = Column(Numeric)
    active = Column(Boolean)
    used = Column(Boolean)
    used_date = Column(DateTime, server_default=text('NOW()'))
    primary_scan_code_label = Column(String)
    is_return_coupon = Column(Boolean)
    expiration_date = Column(Date)
    generation_date = Column(DateTime, server_default=text('NOW()'))
    activation_date = Column(DateTime, server_default=text('NOW()'))
    secondary_scan_code_label = Column(String)
    scan_code_img = Column(String)
    coupon_code = Column(String)
    return_coupon_reason = Column(String)
    is_valid = Column(Boolean)
    coupon_status = Column(String)
    discount_percentage = Column(Integer)
    coupon_count = Column(Integer)
    payment_method_status = Column(String, nullable=False)


class Currency(Model):
    __tablename__ = "currency"
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String)
    symbol = Column(String)
    numeric_code = Column(String)
    full_name = Column(String)
    decimal_places = Column(SmallInteger)
    internationalized_name_code = Column(String)


class Customer_segment(Model):
    __tablename__ = "customer_segment"
    cs_id = Column(Integer, primary_key=True, nullable=False)
    cs_name = Column(String)
    cs_notes = Column(Text)


class Doc_type(Model):
    __tablename__ = "doc_type"
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String)
    doc_category = Column(Enum(t_doc_category), info={"marshmallow_enum": {"by_value": False}})
    notes = Column(Text)
    required_information = Column(Text)
    is_serialized = Column(Boolean)
    serial_length = Column(Integer)
    expires = Column(Boolean)
    validity_period = Column(Integer)
    renewal_frequency = Column(Integer)
    is_government_issued = Column(Boolean)
    is_digital = Column(Boolean)
    template_url = Column(String)
    example_image_url = Column(String)
    created_at = Column(DateTime, server_default=text('NOW()'))
    updated_at = Column(DateTime, server_default=text('NOW()'))


class Mime_type(Model):
    __tablename__ = "mime_type"
    id = Column(Integer, primary_key=True, nullable=False)
    label = Column(String)
    mime_type = Column(String)
    file_extension = Column(String)


class Mime_type_map(Model):
    __tablename__ = "mime_type_map"
    id = Column(Integer, primary_key=True, nullable=False)
    extension = Column(String)
    mime_type = Column(String)


class Payment_card(Model):
    __tablename__ = "payment_card"
    id = Column(Integer, primary_key=True, nullable=False)
    bin = Column(String)
    pan = Column(String)
    credit_card_expired = Column(Boolean, nullable=False)
    card_token = Column(String, nullable=False)
    issue_number = Column(String, nullable=False)
    bill_to_city = Column(String)
    masked_number = Column(String, nullable=False)
    name = Column(String, nullable=False)
    company_name = Column(String)
    card_holder_name = Column(String, nullable=False)
    number_last_digits = Column(String, nullable=False)
    payment_card_type = Column(String, nullable=False)
    derived_card_type_code = Column(String)
    expiration_year = Column(Integer)
    expiration_month = Column(Integer)
    bill_to_street = Column(String)
    bill_to_street2 = Column(String)
    bill_to_first_name = Column(String)
    bill_to_last_name = Column(String)
    payment_method_status = Column(String)
    card_number = Column(String)
    cardholder_name = Column(String)
    card_expiration = Column(String)
    service_code = Column(String)
    cvv = Column(String)


class Promotion(Model):
    __tablename__ = "promotion"
    promo_id = Column(Integer, primary_key=True, nullable=False)
    promo_name = Column(String)
    promo_notes = Column(Text)
    promo_start_date = Column(DateTime, server_default=text('NOW()'))
    promo_end_date = Column(DateTime, server_default=text('NOW()'))


class Token_provider(Model):
    __tablename__ = "token_provider"
    token_provider_id = Column(Integer, primary_key=True, nullable=False)
    token_provider_name = Column(String, nullable=False)
    token_provioder_notes = Column(Text)
    token_provider_priv_key = Column(Text)
    token_provider_pub_key = Column(Text)
    token_provider_endpoint = Column(Text)
    token_provider_protocol = Column(Text)
    token_provider_auth = Column(Text)
    token_provider_ssl = Column(Text)
    token_provider_ip_whitelist = Column(Text)
    token_provider_password = Column(String)
    enabled = Column(Boolean)


class Trans_routing_thresholds(Model):
    __tablename__ = "trans_routing_thresholds"
    trans_route_id = Column(Integer, primary_key=True, nullable=False)
    trans_route_name = Column(String)
    trans_route_min = Column(Numeric)
    trans_route_max = Column(Numeric)
    trans_route_priority = Column(Integer)


class Trans_type(Model):
    __tablename__ = "trans_type"
    tt_id = Column(Integer, primary_key=True, nullable=False)
    tt_name = Column(String)
    tt_notes = Column(Text)


class User_ext(Model):
    __tablename__ = "user_ext"
    id = Column(Integer, primary_key=True, nullable=False)
    manager_id_fk = Column(Integer, ForeignKey("user_ext.id"))
    first_name = Column(String)
    middle_name = Column(String)
    surname = Column(String)
    employee_number = Column(String)
    job_title = Column(String)
    phone_number = Column(String)
    email = Column(String)
    user_data = Column(Text)
    manager = relationship("User_ext", remote_side=[id], backref="subordinates")


class Ab_permission_view(Model):
    __tablename__ = "ab_permission_view"
    id = Column(Integer, primary_key=True, nullable=False)
    permission_id = Column(Integer, ForeignKey("ab_permission.id"))
    view_menu_id = Column(Integer, ForeignKey("ab_view_menu.id"))
    view_menu = relationship("Ab_view_menu", backref="view_menu")
    permission = relationship("Ab_permission", backref="permission")


class Ab_user_role(Model):
    __tablename__ = "ab_user_role"
    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey("ab_user.id"))
    role_id = Column(Integer, ForeignKey("ab_role.id"))
    role = relationship("Ab_role", backref="role")
    user = relationship("Ab_user", backref="user")


class Biller(Model):
    __tablename__ = "biller"
    biller_id = Column(Integer, primary_key=True, nullable=False)
    biller_cat_id_fk = Column(Integer, ForeignKey("biller_category.biller_cat_id"))
    biller_code = Column(String, nullable=False)
    biller_name = Column(String)
    biller_url = Column(String)
    biller_note = Column(Text)
    biller_cat = relationship("Biller_category", backref="biller_cat")


class State(Model):
    __tablename__ = "state"
    country_id_fk = Column(Integer, ForeignKey("country.id"))
    id = Column(Integer, primary_key=True, nullable=False)
    state_code = Column(String)
    state_name = Column(String)
    state_desc = Column(Text)
    country = relationship("Country", backref="country")


class Token(Model):
    __tablename__ = "token"
    token_id = Column(Integer, primary_key=True, nullable=False)
    token_provider_id_fk = Column(Integer, ForeignKey("token_provider.token_provider_id"))
    token_name = Column(String)
    token_issue_date = Column(DateTime, server_default=text('NOW()'))
    token_expiry_date = Column(DateTime, server_default=text('NOW()'))
    token_validity = Column(Integer)
    token_expired = Column(Boolean)
    token_value = Column(String)
    token_username = Column(String)
    token_password = Column(String)
    token_notes = Column(Text)
    token_client_secret = Column(Text)
    enabled = Column(Boolean)
    token_provider = relationship("Token_provider", backref="token_provider")


class Ab_permission_view_role(Model):
    __tablename__ = "ab_permission_view_role"
    id = Column(Integer, primary_key=True, nullable=False)
    permission_view_id = Column(Integer, ForeignKey("ab_permission_view.id"))
    role_id = Column(Integer, ForeignKey("ab_role.id"))
    permission_view = relationship("Ab_permission_view", backref="permission_view")
    role = relationship("Ab_role", backref="role")


class Biller_offering(Model):
    __tablename__ = "biller_offering"
    biller_id_fk = Column(Integer, ForeignKey("biller.biller_id"))
    biller_offering_id = Column(Integer, primary_key=True, nullable=False)
    offering_name = Column(String)
    offering_description = Column(Text)
    offering_price = Column(Numeric)
    biller = relationship("Biller", backref="biller")


class Lga(Model):
    __tablename__ = "lga"
    id = Column(Integer, primary_key=True, nullable=False)
    state_id_fk = Column(Integer, ForeignKey("state.id"))
    code = Column(String)
    lga_name = Column(String)
    state = relationship("State", backref="state")


class Agent(Model):
    __tablename__ = "agent"
    id = Column(Integer, primary_key=True, nullable=False)
    aggregator_id_fk = Column(Integer, ForeignKey("agent.id"))
    is_aggregator = Column(Boolean)
    became_aggregator_date = Column(DateTime, server_default=text('NOW()'))
    assigned_pos_count = Column(Integer, nullable=False)
    aggregator_pos_threshold = Column(Integer)
    registration_status = Column(Enum(t_verification_status), info={"marshmallow_enum": {"by_value": False}})
    registration_status_notes = Column(Text)
    agent_type = Column(Enum(t_org_type), info={"marshmallow_enum": {"by_value": False}})
    agent_role = Column(Enum(t_agent_role), info={"marshmallow_enum": {"by_value": False}})
    agent_tier_id_fk = Column(Integer, ForeignKey("agent_tier.id"))
    account_manager_id_fk = Column(Integer, ForeignKey("user_ext.id"))
    agent_name = Column(String)
    alias = Column(String)
    phone_country_id_fk = Column(Integer, ForeignKey("country.id"))
    phone = Column(String, nullable=False)
    phone_ext = Column(String)
    alt_phone_country_id_fk = Column(Integer, ForeignKey("country.id"))
    alt_phone = Column(String)
    alt_phone_ext = Column(String)
    email = Column(String)
    alt_email = Column(String)
    bvn = Column(String)
    bvn_verified = Column(Boolean)
    bvn_verification_date = Column(DateTime, server_default=text('NOW()'))
    bvn_verification_code = Column(Text)
    tax_id = Column(String)
    bank_id_fk = Column(Integer, ForeignKey("bank.id"))
    bank_acc_no = Column(String)
    biz_name = Column(String)
    biz_state_id_fk = Column(Integer, ForeignKey("state.id"))
    biz_lga_id_fk = Column(Integer, ForeignKey("lga.id"))
    biz_city = Column(String)
    biz_city_area = Column(String)
    biz_street = Column(String)
    biz_building = Column(String)
    biz_address = Column(Text)
    biz_poa_img = Column(String)
    biz_poa_desc = Column(String)
    biz_poa_valid = Column(Boolean)
    biz_lat = Column(Float)
    biz_lon = Column(Float)
    biz_loc = Column(Text)
    biz_ggl_code = Column(String)
    company_name = Column(String)
    cac_number = Column(String)
    cac_reg_date = Column(Date)
    cac_cert_img = Column(String)
    cac_cert_no = Column(String)
    ref_code = Column(String)
    access_pin = Column(String)
    registered_by_fk = Column(Integer, ForeignKey("user_ext.id"))
    registration_date = Column(DateTime, server_default=text('NOW()'))
    reviewed_by_fk = Column(Integer, ForeignKey("user_ext.id"))
    review_date = Column(DateTime, server_default=text('NOW()'))
    approved_by_fk = Column(Integer, ForeignKey("user_ext.id"))
    approval_date = Column(DateTime, server_default=text('NOW()'))
    approval_narrative = Column(Text)
    kyc_submit_date = Column(DateTime, server_default=text('NOW()'))
    kyc_verification_status = Column(Enum(t_verification_status), info={"marshmallow_enum": {"by_value": False}})
    kyc_approval_date = Column(DateTime, server_default=text('NOW()'))
    kyc_ref_code = Column(String)
    kyc_rejection_narrative = Column(Text)
    kyc_rejection_by_fk = Column(Integer, ForeignKey("user_ext.id"))
    rejection_date = Column(DateTime, server_default=text('NOW()'))
    rejection_narrative = Column(Text)
    rejected_by_fk = Column(Integer, ForeignKey("user_ext.id"))
    face_matrix = Column(Text)
    finger_print_img = Column(Text)
    agent_public_key = Column(Text)
    agent_pj_expiry = Column(DateTime, server_default=text('NOW()'))
    agent_history = Column(Text)
    biz_state = relationship("State", backref="biz_state")
    kyc_rejection_by = relationship("User_ext", backref="kyc_rejection_by")
    biz_lga = relationship("Lga", backref="biz_lga")
    phone_country = relationship("Country", backref="phone_country")
    registered_by = relationship("User_ext", backref="registered_by")
    agent_tier = relationship("Agent_tier", backref="agent_tier")
    rejected_by = relationship("User_ext", backref="rejected_by")
    approved_by = relationship("User_ext", backref="approved_by")
    reviewed_by = relationship("User_ext", backref="reviewed_by")
    bank = relationship("Bank", backref="bank")
    aggregator = relationship("Agent", remote_side=[id], backref="subordinates")
    alt_phone_country = relationship("Country", backref="alt_phone_country")
    account_manager = relationship("User_ext", backref="account_manager")


class Pos(Model):
    __tablename__ = "pos"
    id = Column(Integer, primary_key=True, nullable=False)
    serial_no = Column(String)
    imei = Column(String)
    mac_addr = Column(String)
    device_model = Column(String)
    device_make = Column(String)
    device_mfg = Column(String)
    os_version = Column(String)
    device_color = Column(String)
    device_condition = Column(String)
    status = Column(String)
    owner_type = Column(String)
    registration_date = Column(DateTime, server_default=text('NOW()'))
    assigned = Column(Boolean)
    assigned_date = Column(DateTime, server_default=text('NOW()'))
    assigned_narrative = Column(Text)
    active = Column(Boolean)
    activation_date = Column(DateTime, server_default=text('NOW()'))
    last_active = Column(DateTime, server_default=text('NOW()'))
    deployed = Column(Boolean)
    deploy_date = Column(DateTime, server_default=text('NOW()'))
    deploy_narrative = Column(Text)
    returned = Column(Boolean)
    return_date = Column(DateTime, server_default=text('NOW()'))
    return_narrative = Column(Text)
    return_received_date = Column(DateTime, server_default=text('NOW()'))
    return_received_by = Column(Integer, ForeignKey("user_ext.id"))
    state_id = Column(Integer, ForeignKey("state.id"))
    lga_id = Column(Integer, ForeignKey("lga.id"))
    street_address = Column(String)
    building_name = Column(String)
    contact_phone_num = Column(String)
    pos_user = Column(String)
    crypt_priv_key = Column(Text)
    crypt_pub_key = Column(Text)
    crypt_password = Column(Text)
    override_key = Column(Text)
    state = relationship("State", backref="state")
    lga = relationship("Lga", backref="lga")
    return_received_by = relationship("User_ext", backref="return_received_by")


class Agent_pos_link(Model):
    __tablename__ = "agent_pos_link"
    agent_id_fk = Column(Integer, ForeignKey("agent.id"), primary_key=True, nullable=False)
    pos_id_fk = Column(Integer, ForeignKey("pos.id"), primary_key=True, nullable=False)
    assigned_date = Column(DateTime, server_default=text('NOW()'))
    assigned_by = Column(String)
    received_by = Column(String)
    received_date = Column(DateTime, server_default=text('NOW()'))
    received_location = Column(String)
    delivery_note = Column(Text)
    delivery_note_printed = Column(Boolean)
    activated = Column(Boolean)
    activation_date = Column(DateTime, server_default=text('NOW()'))
    activation_otp = Column(String)
    otp_sent = Column(Boolean)
    otp_sent_time = Column(DateTime, server_default=text('NOW()'))
    otp_used = Column(Boolean)
    history = Column(Text)
    pos = relationship("Pos", backref="pos")
    agent = relationship("Agent", backref="agent")


class Comm_ref(Model):
    __tablename__ = "comm_ref"
    cr_id = Column(Integer, primary_key=True, nullable=False)
    agent_type = Column(Enum(t_org_type), info={"marshmallow_enum": {"by_value": False}})
    agent_tier_level = Column(Integer, ForeignKey("agent_tier.id"))
    agent_id_fk = Column(Integer, ForeignKey("agent.id"))
    state_id_fk = Column(Integer, ForeignKey("state.id"))
    lga_id_fk = Column(Integer, ForeignKey("lga.id"))
    biller_id_fk = Column(Integer, ForeignKey("biller.biller_id"))
    biller_offering_id_fk = Column(Integer, ForeignKey("biller_offering.biller_offering_id"))
    transaction_type_id_fk = Column(Integer, ForeignKey("trans_type.tt_id"))
    customer_segment_id_fk = Column(Integer, ForeignKey("customer_segment.cs_id"))
    special_promotion_id_fk = Column(Integer, ForeignKey("promotion.promo_id"))
    min_trans_amount = Column(Numeric)
    max_trans_amount = Column(Numeric)
    min_max_step = Column(Integer)
    min_comm_amount = Column(Numeric)
    max_comm_amount = Column(Numeric)
    commission_rate = Column(Numeric)
    start_time = Column(Time)
    end_time = Column(Time)
    start_date = Column(Date)
    end_date = Column(Date)
    agent_tier_level = relationship("Agent_tier", backref="agent_tier_level")
    biller_offering = relationship("Biller_offering", backref="biller_offering")
    customer_segment = relationship("Customer_segment", backref="customer_segment")
    state = relationship("State", backref="state")
    transaction_type = relationship("Trans_type", backref="transaction_type")
    lga = relationship("Lga", backref="lga")
    special_promotion = relationship("Promotion", backref="special_promotion")
    agent = relationship("Agent", backref="agent")
    biller = relationship("Biller", backref="biller")


class Person(Model):
    __tablename__ = "person"
    id = Column(Integer, primary_key=True, nullable=False)
    agent_id_fk = Column(Integer, ForeignKey("agent.id"))
    next_of_kin_id_fk = Column(Integer, ForeignKey("person.id"))
    person_role = Column(Enum(t_person_role), info={"marshmallow_enum": {"by_value": False}})
    first_name = Column(String)
    middle_name = Column(String)
    surname = Column(String)
    nick_name = Column(String)
    gender = Column(Enum(t_gender), info={"marshmallow_enum": {"by_value": False}})
    photo_img = Column(String)
    signature_img = Column(String)
    bvn_no = Column(String)
    bvn_verified = Column(Boolean)
    bvn_verification_date = Column(DateTime, server_default=text('NOW()'))
    bvn_verification_code = Column(Text)
    tax_id = Column(String)
    home_poa_img = Column(String)
    home_poa_desc = Column(String)
    home_poa_valid = Column(Boolean)
    home_lat = Column(Float)
    home_lon = Column(Float)
    home_loc = Column(Text)
    home_ggl_code = Column(String)
    agent = relationship("Agent", backref="agent")
    next_of_kin = relationship("Person", remote_side=[id], backref="subordinates")


class Wallet(Model):
    __tablename__ = "wallet"
    wallet_id = Column(Integer, primary_key=True, nullable=False)
    agent_id_fk = Column(Integer, ForeignKey("agent.id"))
    pos_id_fk = Column(Integer, ForeignKey("pos.id"))
    wallet_name = Column(String)
    wallet_balance = Column(Numeric)
    wallet_locked = Column(Boolean)
    wallet_active = Column(Boolean)
    wallet_code = Column(String)
    wallet_crypt = Column(Text)
    wallet_narrative = Column(Text)
    agent = relationship("Agent", backref="agent")
    pos = relationship("Pos", backref="pos")


class Agent_person_link(Model):
    __tablename__ = "agent_person_link"
    person_id_fk = Column(Integer, ForeignKey("person.id"), primary_key=True, nullable=False)
    agent_id_fk = Column(Integer, ForeignKey("agent.id"), primary_key=True, nullable=False)
    person = relationship("Person", backref="person")
    agent = relationship("Agent", backref="agent")


class Contact(Model):
    __tablename__ = "contact"
    id = Column(Integer, primary_key=True, nullable=False)
    person_id_fk = Column(Integer, ForeignKey("person.id"))
    agent_id_fk = Column(Integer, ForeignKey("agent.id"))
    contact_type_id_fk = Column(Integer, ForeignKey("contact_type.id"), nullable=False)
    contact = Column(String, nullable=False)
    priority = Column(Integer, nullable=False)
    best_time_to_contact_start = Column(Time)
    best_time_to_contact_end = Column(Time)
    active_from_date = Column(DateTime, server_default=text('NOW()'))
    active_to_date = Column(Date)
    for_business_use = Column(Boolean)
    for_personal_use = Column(Boolean)
    do_not_use = Column(Boolean)
    is_active = Column(Boolean)
    is_blocked = Column(Boolean)
    is_verified = Column(Boolean)
    notes = Column(Text)
    contact_type = relationship("Contact_type", backref="contact_type")
    person = relationship("Person", backref="person")
    agent = relationship("Agent", backref="agent")


class Doc(Model):
    __tablename__ = "doc"
    id = Column(Integer, primary_key=True, nullable=False)
    doc_type_id_fk = Column(Integer, ForeignKey("doc_type.id"))
    person_id_fk = Column(Integer, ForeignKey("person.id"))
    agent_id_fk = Column(Integer, ForeignKey("agent.id"))
    doc_name = Column(String)
    doc_content_type = Column(Integer, ForeignKey("mime_type.id"))
    doc_binaary = Column(Text)
    doc_url = Column(Text)
    doc_length = Column(Integer)
    doc_text = Column(Text)
    identification_number = Column(String)
    serial_number = Column(String)
    description = Column(Text)
    file_name = Column(String)
    page_count = Column(Integer)
    issued_on = Column(Date)
    issued_by_authority = Column(String)
    issued_at = Column(String)
    expires_on = Column(Date)
    expired = Column(Boolean)
    verified = Column(Boolean)
    verification_date = Column(DateTime, server_default=text('NOW()'))
    verification_code = Column(Text)
    uploaded_on = Column(DateTime, server_default=text('NOW()'))
    updated_on = Column(DateTime, server_default=text('NOW()'))
    doc_content_type = relationship("Mime_type", backref="doc_content_type")
    agent = relationship("Agent", backref="agent")
    person = relationship("Person", backref="person")
    doc_type = relationship("Doc_type", backref="doc_type")


class Person_additional_data(Model):
    __tablename__ = "person_additional_data"
    person_id_fk = Column(Integer, ForeignKey("person.id"), primary_key=True, nullable=False)
    Gender = Column(Enum(t_gender), info={"marshmallow_enum": {"by_value": False}})
    religion = Column(String)
    ethnicity = Column(String)
    consumer_credit_score = Column(Integer)
    is_home_owner = Column(Boolean)
    person_height = Column(Integer)
    person_weight = Column(Integer)
    person_height_unit_of_measure = Column(String)
    person_weight_unit_of_measure = Column(String)
    highest_education_level = Column(String)
    person_life_stage = Column(String)
    mothers_maiden_name = Column(String)
    Marital_Status_cd = Column(Integer)
    citizenship_fk = Column(Integer, ForeignKey("country.id"))
    From_whom = Column(String)
    Amount = Column(Numeric)
    Interest_rate_pa = Column(Numeric)
    Number_of_people_depending_on_overal_income = Column(Integer)
    YesNo_cd_Bank_account = Column(Integer)
    YesNo_cd_Business_plan_provided = Column(Integer)
    YesNo_cd_Access_to_internet = Column(Integer)
    Introduced_by = Column(String)
    Known_to_introducer_since = Column(String)
    Last_visited_by = Column(String)
    Last_visited_on = Column(Date, nullable=False)
    person = relationship("Person", backref="person")
    citizenship = relationship("Country", backref="citizenship")


class Person_admin_data(Model):
    __tablename__ = "person_admin_data"
    person_id_fk = Column(Integer, ForeignKey("person.id"), primary_key=True, nullable=False)
    creation_time = Column(DateTime, server_default=text('NOW()'))
    failed_login_count = Column(Integer)
    failed_login_timestamp = Column(DateTime, server_default=text('NOW()'))
    password_last_set_time = Column(DateTime, server_default=text('NOW()'))
    profile_picture = Column(String)
    awatar = Column(String)
    screen_name = Column(String)
    user_priv_cert = Column(Text)
    user_pub_cert = Column(Text)
    alt_security_identities = Column(Text)
    generated_UID = Column(UUID)
    do_not_email = Column(Boolean)
    do_not_phone = Column(Boolean)
    do_not_mail = Column(Boolean)
    do_not_sms = Column(Boolean)
    do_not_trade = Column(Boolean)
    opted_out = Column(Boolean)
    do_not_track_update_date = Column(Date)
    do_not_process_from_update_date = Column(Date)
    do_not_market_from_update_date = Column(Date)
    do_not_track_location_update_date = Column(Date)
    do_not_profile_from_update_date = Column(Date)
    do_forget_me_from_update_date = Column(Date)
    do_not_process_reason = Column(String)
    no_merge_reason = Column(String)
    do_extract_my_data_update_date = Column(Date)
    should_forget = Column(Boolean)
    consumer_credit_score_provider_name = Column(String)
    web_site_url = Column(String)
    ordering_name = Column(String)
    hospitalizations_last5_years_count = Column(Integer)
    surgeries_last5_years_count = Column(Integer)
    dependent_count = Column(Integer)
    account_locked = Column(Boolean)
    send_individual_data = Column(Boolean)
    influencer_rating = Column(Integer)
    person = relationship("Person", backref="person")


class Trans(Model):
    __tablename__ = "trans"
    trans_id = Column(Integer, primary_key=True, nullable=False)
    coupon_id_fk = Column(Integer, ForeignKey("coupon.coupon_id"))
    customer_name = Column(String)
    trans_purpose = Column(Text)
    customer_id = Column(String)
    transaction_type = Column(Enum(t_payment_method), info={"marshmallow_enum": {"by_value": False}})
    card_trans_type = Column(Enum(t_card_trans_type), info={"marshmallow_enum": {"by_value": False}})
    agent_id_fk = Column(Integer, ForeignKey("agent.id"), nullable=False)
    payment_card_id_fk = Column(Integer, ForeignKey("payment_card.id"))
    pos_id_fk = Column(Integer, ForeignKey("pos.id"))
    wallet_id_fk = Column(Integer, ForeignKey("wallet.wallet_id"))
    biller_id_fk = Column(Integer, ForeignKey("biller.biller_id"))
    biller_offering_id_fk = Column(Integer, ForeignKey("biller_offering.biller_offering_id"))
    trans_time = Column(DateTime, server_default=text('NOW()'))
    currency_id_fk = Column(Integer, ForeignKey("currency.id"))
    trans_status = Column(Enum(t_transaction_status), info={"marshmallow_enum": {"by_value": False}})
    trans_route_id_fk = Column(Integer, ForeignKey("trans_routing_thresholds.trans_route_id"))
    origin_source = Column(Enum(t_payment_method), info={"marshmallow_enum": {"by_value": False}})
    origin_ref_code = Column(String)
    origin_trans_notes = Column(Text)
    origin_bank_id_fk = Column(Integer, ForeignKey("bank.id"))
    origin_institution_code = Column(String)
    origin_account_num = Column(String)
    origin_account_name = Column(String)
    origin_KYC_Level = Column(Integer)
    origin_Bank_Verification_Number = Column(String)
    origin_bvn = Column(String)
    session_ref = Column(String)
    transaction_ref = Column(String)
    channelCode = Column(Integer)
    name_enquiry_ref = Column(String)
    api_transactionid = Column(String)
    receipt_no = Column(String)
    pin_based = Column(Boolean)
    pin_code = Column(String)
    pin_option = Column(String)
    authorization_code = Column(String)
    acquirer_name = Column(String)
    currency = Column(String)
    transaction_location = Column(String)
    payment_reference = Column(String)
    response_code = Column(String)
    trans_dest = Column(Enum(t_payment_method), info={"marshmallow_enum": {"by_value": False}})
    bene_ref_code = Column(String)
    bene_trans_notes = Column(Text)
    bene_bank_id_fk = Column(Integer, ForeignKey("bank.id"))
    bene_account_num = Column(String)
    bene_institution_code = Column(String)
    bene_bank_verification_number = Column(String)
    bene_KYC_Level = Column(Integer)
    bene_account_name = Column(String)
    bene_phone_number = Column(String)
    bene_phone_denom = Column(String)
    bene_phone_product = Column(String)
    transaction_amount = Column(Numeric)
    available_balance = Column(Numeric)
    svc_fees = Column(Numeric)
    comm_total = Column(Numeric)
    comm_agent = Column(Numeric)
    comm_aggr = Column(Numeric)
    comm_ours = Column(Numeric)
    comm_other = Column(Numeric)
    comm_net_pct = Column(Float)
    tax = Column(Numeric)
    excise_duty = Column(Numeric)
    vat = Column(Numeric)
    transmit_amount = Column(Numeric)
    comm_narration = Column(Text)
    trans_currency = Column(String)
    trans_convert_currency = Column(String)
    trans_currency_exchange_rate = Column(Numeric)
    trans_date = Column(DateTime, server_default=text('NOW()'))
    customer_segment_id_fk = Column(Integer, ForeignKey("customer_segment.cs_id"))
    agent_tier_level_id_fk = Column(Integer, ForeignKey("agent_tier.id"))
    special_promotions_id_fk = Column(Integer, ForeignKey("promotion.promo_id"))
    fraud_marker = Column(Boolean)
    fraud_eval_outcome = Column(String)
    fraud_risk_score = Column(Float)
    fraud_prediction_explanations = Column(Text)
    fraud_rule_evaluations = Column(Text)
    fraud_event_num = Column(String)
    trans_narration = Column(Text)
    biller_offering = relationship("Biller_offering", backref="biller_offering")
    customer_segment = relationship("Customer_segment", backref="customer_segment")
    origin_bank = relationship("Bank", backref="origin_bank")
    pos = relationship("Pos", backref="pos")
    biller = relationship("Biller", backref="biller")
    currency = relationship("Currency", backref="currency")
    special_promotions = relationship("Promotion", backref="special_promotions")
    agent_tier_level = relationship("Agent_tier", backref="agent_tier_level")
    bene_bank = relationship("Bank", backref="bene_bank")
    payment_card = relationship("Payment_card", backref="payment_card")
    wallet = relationship("Wallet", backref="wallet")
    coupon = relationship("Coupon", backref="coupon")
    agent = relationship("Agent", backref="agent")
    trans_route = relationship("Trans_routing_thresholds", backref="trans_route")


class Agent_doc_link(Model):
    __tablename__ = "agent_doc_link"
    agent_id_fk = Column(Integer, ForeignKey("agent.id"), primary_key=True, nullable=False)
    doc_id_fk = Column(Integer, ForeignKey("doc.id"), primary_key=True, nullable=False)
    verification_status = Column(Enum(t_verification_status), info={"marshmallow_enum": {"by_value": False}})
    submit_date = Column(DateTime, server_default=text('NOW()'))
    notes = Column(Text)
    doc = relationship("Doc", backref="doc")
    agent = relationship("Agent", backref="agent")


class Person_doc_link(Model):
    __tablename__ = "person_doc_link"
    person_id_fk = Column(Integer, ForeignKey("person.id"), primary_key=True, nullable=False)
    doc_id_fk = Column(Integer, ForeignKey("doc.id"), primary_key=True, nullable=False)
    verification_status = Column(Enum(t_verification_status), info={"marshmallow_enum": {"by_value": False}})
    submit_date = Column(DateTime, server_default=text('NOW()'))
    doc = relationship("Doc", backref="doc")
    person = relationship("Person", backref="person")

