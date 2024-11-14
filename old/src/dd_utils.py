import re, string
from marshmallow import fields
from sqlalchemy import create_engine, inspect, MetaData, FetchedValue
from sqlalchemy.orm import relationship, DeclarativeBase, mapped_column, Mapped, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Enum, ForeignKey, ARRAY, JSON, PickleType, LargeBinary, Boolean, Date, DateTime, Float, Integer, Interval, Numeric,
    SmallInteger,
    String, Text, Time, BigInteger, Unicode, UnicodeText, CHAR, VARBINARY, TIMESTAMP, CLOB, BLOB, NCHAR, NVARCHAR,
    INTEGER, TEXT, VARCHAR,
    NUMERIC, BOOLEAN, Time, DECIMAL, Column
)
from sqlalchemy.dialects.postgresql import (
    ARRAY, BIGINT, BIT, BOOLEAN, BYTEA, CHAR, CIDR, CITEXT, DATE, DATEMULTIRANGE,
    DATERANGE, DOMAIN, DOUBLE_PRECISION, ENUM, FLOAT, HSTORE, INET, INT4MULTIRANGE,
    INT4RANGE, INT8MULTIRANGE, INT8RANGE, INTEGER, INTERVAL, JSON, JSONB, JSONPATH,
    MACADDR, MACADDR8, MONEY, NUMERIC, NUMMULTIRANGE, NUMRANGE, OID, REAL, REGCLASS,
    REGCONFIG, SMALLINT, TEXT, TIME, TIMESTAMP, TSMULTIRANGE, TSQUERY, TSRANGE,
    TSTZMULTIRANGE, TSTZRANGE, TSVECTOR, UUID, VARCHAR,
)

from .models import (app_Tables, app_Columns, app_Relations, app_Indexes, app_Views, app_Triggers, app_Sequences,
                     app_Procedures, app_Functions)


def pop_data_dict(metadata, inspector, session):
    # Populate Tables
    for table_name in metadata.tables:
        table = metadata.tables[table_name]
        table_entry = app_Tables(
            name=table_name,
            schema=table.schema,
            comment=inspector.get_table_comment(table_name)['text']
        )
        session.add(table_entry)

        # Columns
        for column in table.columns:
            column_entry = app_Columns(
                name=column.name,
                data_type=str(column.type),
                nullable=column.nullable,
                primary_key=column.primary_key,
                autoincrement=column.autoincrement,
                unique=column.unique,
                default=column.default,
                server_default=column.server_default,
                check_constraint=column.info.get('check_constraint', None),
                comment=column.comment,
                indexed=any(index for index in table.indexes if column in index.columns),
                table=table_entry
            )
            session.add(column_entry)

        # Indexes
        for index in table.indexes:
            index_entry = app_Indexes(
                name=index.name,
                unique=index.unique,
                table=table_entry
            )
            session.add(index_entry)

    # Relations (Foreign Keys)
    for table_name in metadata.tables:
        table = metadata.tables[table_name]
        # Retrieve the source table entry
        source_table_entry = session.query(app_Tables).filter_by(name=table_name).first()
        if not source_table_entry:
            continue
        # Retrieve the referred table and column entries
        referred_table_entry = session.query(app_Tables).filter_by(name=fk.column.table.name).first()
        if referred_table_entry is None:
            continue  # If the referred table entry doesn't exist, skip to the next foreign key

        referred_column_entry = session.query(app_Columns).filter_by(name=fk.column.name,
                                                                     table_id=referred_table_entry.id).first()
        if referred_column_entry is None:
            continue  # If the referred column entry doesn't exist, skip to the next foreign key
        for fk in table.foreign_keys:
            relation_entry = app_Relations(
                name=fk.name,
                source_table_id=source_table_entry.id,
                source_column_id=source_column_entry.id,
                referred_table_id=referred_table_entry.id,
                referred_column_id=referred_column_entry.id,
                # Additional fields can be set here as needed
            )
            session.add(relation_entry)

    session.commit()
