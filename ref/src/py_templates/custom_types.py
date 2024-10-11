from sqlalchemy.dialects.postgresql import (BYTEA)
from flask_appbuilder.models.mixins import AuditMixin, FileColumn, ImageColumn
from flask_appbuilder.fieldwidgets import BS3TextFieldWidget, BS3TextAreaFieldWidget, DatePickerWidget, DateTimePickerWidget
import sqlalchemy as sa
from sqlalchemy import (
    Boolean, CheckConstraint, Column, Date, DateTime,
    Float, ForeignKey, Integer, Numeric, String, Text, Interval,
)

postgresql_type_map = {
    'integer': 'Integer',
    'bigint': 'Integer',
    'smallint': 'Integer',
    'character varying': 'String',
    'text': 'Text',
    'real': 'Float',
    'numeric': 'Numeric',
    'boolean': 'Boolean',
    'timestamp without time zone': 'DateTime',
    'timestamp with time zone': 'DateTime',
    'time without time zone': 'Time',
    'time with time zone': 'Time',
    'bytea': 'LargeBinary',
    'interval': 'Interval',
    'date': 'Date',
    'uuid': 'UUID',
    'json': 'JSON',
    'jsonb': 'JSONB',
}



"""
This function takes a string representing a PostgreSQL type as input and returns the corresponding SQLAlchemy type 
as an instance of sa.types.TypeEngine. If the input string does not match any known PostgreSQL type, the function 
returns None.

Note that some PostgreSQL types, such as composite types, enums, and domains, require 
special handling in SQLAlchemy and are not included in this function.
"""
def pg_type_to_sa_type(pg_type: str) -> sa.types.TypeEngine:
    type_map = {
        'smallint': sa.types.SmallInteger,
        'integer': sa.types.Integer,
        'bigint': sa.types.BigInteger,
        'serial': sa.types.Integer,  # auto-incrementing integer
        'bigserial': sa.types.BigInteger,  # auto-incrementing bigint
        'decimal': sa.types.Numeric,
        'numeric': sa.types.Numeric,
        'real': sa.types.Float,
        'double precision': sa.types.Float,
        'smallserial': sa.types.SmallInteger,  # auto-incrementing smallint
        'varchar': sa.types.String,
        'text': sa.types.Text,
        'char': sa.types.CHAR,
        'bytea': sa.types.LargeBinary,
        'boolean': sa.types.Boolean,
        'date': sa.types.Date,
        'timestamp': sa.types.DateTime,
        'timestamptz': sa.types.DateTime(timezone=True),
        'time': sa.types.Time,
        'timetz': sa.types.Time(timezone=True),
        'interval': sa.types.Interval,
        'uuid': sa.types.UUID,
        'json': sa.dialects.postgresql.JSON,
        'jsonb': sa.dialects.postgresql.JSONB,
        'point': sa.dialects.postgresql.POINT,
        'line': sa.dialects.postgresql.LINE,
        'lseg': sa.dialects.postgresql.LSEG,
        'box': sa.dialects.postgresql.BOX,
        'circle': sa.dialects.postgresql.CIRCLE,
        'polygon': sa.dialects.postgresql.POLYGON,
        'inet': sa.dialects.postgresql.INET,
        'cidr': sa.dialects.postgresql.CIDR,
        'macaddr': sa.dialects.postgresql.MACADDR,
        'bit': sa.dialects.postgresql.BIT,
        'varbit': sa.dialects.postgresql.VARBIT,
        'xml': sa.dialects.postgresql.XML,
        'tsvector': sa.dialects.postgresql.TSVECTOR,
        'tsquery': sa.dialects.postgresql.TSQUERY,
        'int4range': sa.dialects.postgresql.INT4RANGE,
        'int8range': sa.dialects.postgresql.INT8RANGE,
        'numrange': sa.dialects.postgresql.NUMRANGE,
        'tsrange': sa.dialects.postgresql.TSRANGE,
        'tstzrange': sa.dialects.postgresql.TSTZRANGE,
        'interval': sa.types.Interval,
        'array': sa.types.ARRAY,
    }
    return type_map.get(pg_type, None)


def pg_type_to_fab_type(pg_type: str) -> str:
    type_map = {
        'smallint': 'IntegerField',
        'integer': 'IntegerField',
        'bigint': 'IntegerField',
        'serial': 'IntegerField',
        'bigserial': 'IntegerField',
        'decimal': 'DecimalField',
        'numeric': 'DecimalField',
        'real': 'FloatField',
        'double precision': 'FloatField',
        'smallserial': 'IntegerField',
        'varchar': 'StringField',
        'text': 'TextField',
        'char': 'StringField',
        'bytea': 'BinaryField',
        'boolean': 'BooleanField',
        'date': 'DateField',
        'timestamp': 'DateTimeField',
        'timestamptz': 'DateTimeField',
        'time': 'TimeField',
        'timetz': 'TimeField',
        'interval': 'TimeDeltaField',
        'uuid': 'StringField',
        'json': 'JSONField',
        'jsonb': 'JSONField',
        'point': 'StringField',
        'line': 'StringField',
        'lseg': 'StringField',
        'box': 'StringField',
        'circle': 'StringField',
        'polygon': 'StringField',
        'inet': 'StringField',
        'cidr': 'StringField',
        'macaddr': 'StringField',
        'bit': 'StringField',
        'varbit': 'StringField',
        'xml': 'TextField',
        'tsvector': 'StringField',
        'tsquery': 'StringField',
        'int4range': 'StringField',
        'int8range': 'StringField',
        'numrange': 'StringField',
        'tsrange': 'StringField',
        'tstzrange': 'StringField',
        'array': 'ListField',
    }
    return type_map.get(pg_type, 'StringField')

class MoneyType(String):
    """
    A custom SQLAlchemy type for storing money values as strings in the database.
    """
    def __init__(self, precision=2):
        self.precision = precision
        super(MoneyType, self).__init__()

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return dialect.type_descriptor(Integer())
        else:
            return dialect.type_descriptor(String(self.precision + 1))

    def process_bind_param(self, value, dialect):
        if value is not None:
            return "{:.{}f}".format(value, self.precision)

    def process_result_value(self, value, dialect):
        if value is not None:
            return float(value)

class MoneyForm(DynamicForm):
    """
    A custom Flask-AppBuilder form for entering money values.
    """
    amount = Integer(_('Amount'), widget=BS3TextFieldWidget())

    def pre_validate(self):
        """
        Convert the form's amount field to a float before validating.
        """
        if self.amount.data is not None:
            self.amount.data = float(self.amount.data)

# Use it like this
# from flask_appbuilder import Model
# from mixins import *
#
# class MyModel(Model):
#     id = Column(Integer, primary_key=True)
#     money_value = Column(MoneyType(precision=2))
