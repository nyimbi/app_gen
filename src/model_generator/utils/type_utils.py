"""
Author: Nyimbi Odero
Copyright: Nyimbi Odero, 2024
License: MIT

type_utils.py: Utilities for type mapping and conversion between PostgreSQL and SQLAlchemy.

This module provides functionality for mapping PostgreSQL data types to their corresponding
SQLAlchemy types, enabling accurate type conversion and representation in generated models.

Key Features:
    - Predefined mappings between PostgreSQL and SQLAlchemy types
    - Support for custom type registrations
    - Handling of array types with automatic element type resolution
    - Support for PostgreSQL enum types
    - Extensible type mapping system

Main Components:
    - POSTGRESQL_TO_SQLALCHEMY_TYPE_NAMES: Dictionary mapping PostgreSQL types to SQLAlchemy types
    - CUSTOM_TYPE_NAMES: Dictionary for user-defined type mappings
    - register_custom_type(): Function to add custom type mappings
    - get_sqlalchemy_type_name(): Function to resolve SQLAlchemy type names

Type Categories Supported:
    - Numeric types (smallint, integer, bigint, decimal, etc.)
    - Character types (varchar, char, text, etc.)
    - Date/Time types (timestamp, date, time, interval)
    - Boolean type
    - Geometric types (point, line, polygon, etc.)
    - Network address types (cidr, inet, macaddr)
    - JSON types (json, jsonb)
    - Range types (int4range, tsrange, etc.)
    - Special types (uuid, xml, hstore, etc.)
    - Array types (type[])
    - Enum types

Usage:
    >>> from model_generator.utils.type_utils import get_sqlalchemy_type_name
    >>> get_sqlalchemy_type_name('integer')
    'Integer'
    >>> get_sqlalchemy_type_name('character varying')
    'String'
    >>> get_sqlalchemy_type_name('integer[]')
    'ARRAY(Integer)'

Dependencies:
    - typing
    - decimal
    - datetime
    - uuid
    - ipaddress
    - enum
    - json
    - geoalchemy2
    - shapely.geometry

Note:
    This module is designed to be used as part of a larger model generation system
    and provides the type resolution functionality needed for creating SQLAlchemy models
    from PostgreSQL database schemas.
"""

from typing import Dict, Any, Tuple, Optional, Union, Type
from decimal import Decimal
from datetime import date, time, datetime, timedelta
from uuid import UUID
from ipaddress import IPv4Address, IPv6Address
from enum import Enum
import json
from geoalchemy2 import WKBElement
from geoalchemy2.shape import to_shape
from shapely.geometry import Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon
from typing import Dict, Optional

POSTGRESQL_TO_SQLALCHEMY_TYPE_NAMES: Dict[str, str] = {
    'smallint': 'SmallInteger',
    'integer': 'Integer',
    'bigint': 'BigInteger',
    'decimal': 'Numeric',
    'numeric': 'Numeric',
    'real': 'Float',
    'double precision': 'Float',
    'money': 'Numeric',
    'character varying': 'String',
    'varchar': 'String',
    'character': 'String',
    'char': 'String',
    'text': 'Text',
    'citext': 'Text',
    'bytea': 'LargeBinary',
    'timestamp': 'DateTime',
    'timestamp with time zone': 'DateTime',
    'date': 'Date',
    'time': 'Time',
    'time with time zone': 'Time',
    'interval': 'Interval',
    'boolean': 'Boolean',
    'point': 'Geometry',
    'line': 'Geometry',
    'lseg': 'Geometry',
    'box': 'Geometry',
    'path': 'Geometry',
    'polygon': 'Geometry',
    'circle': 'Geometry',
    'cidr': 'CIDR',
    'inet': 'INET',
    'macaddr': 'MACADDR',
    'tsvector': 'TSVector',
    'tsquery': 'TSQuery',
    'uuid': 'UUID',
    'xml': 'Text',
    'json': 'JSON',
    'jsonb': 'JSONB',
    'int4range': 'INT4RANGE',
    'int8range': 'INT8RANGE',
    'numrange': 'NUMRANGE',
    'tsrange': 'TSRANGE',
    'tstzrange': 'TSTZRANGE',
    'daterange': 'DATERANGE',
    'hstore': 'HSTORE',
    'bit': 'BIT',
    'varbit': 'BIT_VARYING',
}

CUSTOM_TYPE_NAMES: Dict[str, str] = {}

def register_custom_type(pg_type: str, sqlalchemy_type: str) -> None:
    """
    Register a custom mapping between a PostgreSQL type and an SQLAlchemy type.

    Args:
        pg_type (str): PostgreSQL type name
        sqlalchemy_type (str): SQLAlchemy type name

    Examples:
        >>> register_custom_type('user_id', 'UserId')
    """
    CUSTOM_TYPE_NAMES[pg_type] = sqlalchemy_type

def get_sqlalchemy_type_name(pg_type: str) -> str:
    """
    Get the corresponding SQLAlchemy type name for a PostgreSQL type.

    Args:
        pg_type (str): PostgreSQL type name

    Returns:
        str: Corresponding SQLAlchemy type name

    Raises:
        ValueError: If no matching SQLAlchemy type is found

    Examples:
        >>> get_sqlalchemy_type_name('integer')
        'Integer'
        >>> get_sqlalchemy_type_name('json')
        'JSON'
    """
    pg_type = pg_type.lower()

    if pg_type in CUSTOM_TYPE_NAMES:
        return CUSTOM_TYPE_NAMES[pg_type]

    if pg_type.endswith('[]'):
        element_type = pg_type[:-2]
        element_sqlalchemy_type = get_sqlalchemy_type_name(element_type)
        return f'ARRAY({element_sqlalchemy_type})'

    if pg_type.startswith('enum_'):
        enum_name = pg_type[5:]
        return f'Enum({enum_name})'

    if pg_type in POSTGRESQL_TO_SQLALCHEMY_TYPE_NAMES:
        return POSTGRESQL_TO_SQLALCHEMY_TYPE_NAMES[pg_type]

    raise ValueError(f"No matching SQLAlchemy type found for PostgreSQL type: {pg_type}")
