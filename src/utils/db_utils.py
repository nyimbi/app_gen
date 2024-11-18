import re
from marshmallow import fields
from sqlalchemy import create_engine, inspect, MetaData, FetchedValue
from sqlalchemy import (
    Enum, ForeignKey, ARRAY, JSON, PickleType, LargeBinary, Boolean, Date, DateTime, Float, Integer, Interval, Numeric,
    SmallInteger,
    String, Text, Time, BigInteger, Unicode, UnicodeText, CHAR, VARBINARY, TIMESTAMP, CLOB, BLOB, NCHAR, NVARCHAR,
    INTEGER, TEXT, VARCHAR,
    NUMERIC, BOOLEAN, Time, DECIMAL, Column
)
from sqlalchemy.sql import sqltypes
# from sqlalchemy.dialects.postgresql import (
#     ARRAY, BIGINT, BIT, BOOLEAN, BYTEA, CHAR, CIDR, CITEXT, DATE, DATEMULTIRANGE,
#     DATERANGE, DOMAIN, DOUBLE_PRECISION, ENUM, FLOAT, HSTORE, INET, INT4MULTIRANGE,
#     INT4RANGE, INT8MULTIRANGE, INT8RANGE, INTEGER, INTERVAL, JSON, JSONB, JSONPATH,
#     MACADDR, MACADDR8, MONEY, NUMERIC, NUMMULTIRANGE, NUMRANGE, OID, REAL, REGCLASS,
#     REGCONFIG, SMALLINT, TEXT, TIME, TIMESTAMP, TSMULTIRANGE, TSQUERY, TSRANGE,
#     TSTZMULTIRANGE, TSTZRANGE, TSVECTOR, UUID, VARCHAR,
# )


def map_dbml_datatypes(datatype: str):
    """
       Maps DBML datatypes to SQLAlchemy types.

       :param datatype: The DBML datatype as a string.
       :return: The corresponding SQLAlchemy type as a string.
       """
    mapping = {
        'int': 'Integer',
        'tinyint': 'Integer',
        'smallint': 'Integer',
        'mediumint': 'Integer',
        'bigint': 'BigInteger',
        'float': 'Float',
        'double': 'Float',
        'decimal': 'Numeric',
        'numeric': 'Numeric',
        'char': 'String',
        'varchar': 'String',
        'tinytext': 'String',
        'text': 'String',
        'mediumtext': 'String',
        'longtext': 'String',
        'date': 'Date',
        'datetime': 'DateTime',
        'timestamp': 'DateTime',
        'time': 'Time',
        'year': 'Integer',
    }
    return mapping.get(datatype.lower(), datatype.title())


def map_pgsql_datatypes(pg_type: str) -> str:
    """
        Maps PostgreSQL-specific datatypes to SQLAlchemy types.

        :param pg_type: The PostgreSQL datatype as a string.
        :return: The corresponding SQLAlchemy type as a string.
        """
    pg_type = pg_type.lower()
    if pg_type.startswith('interval'):
        return 'Interval'
    if pg_type == 'character varying' or pg_type == 'varchar':
        return 'String'
    if pg_type == 'json' or pg_type == 'jsonb':
        return 'JSON'
    elif pg_type.startswith('int'):
        return 'Integer'
    elif pg_type.startswith('smallint'):
        return 'SmallInteger'
    elif pg_type in ('bigint', 'bigserial'):
        return 'BigInteger'
    elif pg_type.startswith('varchar')or pg_type.startswith('char') :
        return 'String'
    elif pg_type in ('text', 'citext'):
        return 'Text'
    elif pg_type.startswith('bool'):
        return 'Boolean'
    elif pg_type in ('real', 'float4'):
        return 'Float'
    elif pg_type in ('double_precision', 'float8', 'double precision'):
        return 'Float'
    elif pg_type in ('numeric', 'decimal'):
        return 'Numeric'
    elif pg_type.startswith('numeric'):
        # Extract precision and scale from the PostgreSQL type
        match = re.match(r'numeric\((\d+),(\d+)\)', pg_type)
        if match:
            precision = int(match.group(1))
            scale = int(match.group(2))
            return f'Numeric(precision={precision}, scale={scale})'
        else:
            return 'Numeric'  # Default if precision and scale are not specified
    elif pg_type == 'money':
        return 'Currency'
    elif pg_type == 'date':
        return 'Date'
    elif pg_type in ('time', 'timetz'):
        return 'Time'
    elif pg_type.startswith('timestamp'):  # in ('timestamp', 'timestamptz'):
        return "DateTime"
        # return "DateTime, server_default=text('NOW()')"
    elif pg_type in ('bytea', 'byte', 'blob'):
        return 'LargeBinary'
    elif pg_type == 'uuid':
        return 'UUID'
    elif pg_type == 'inet':
        return 'IPAddressType()'
    elif pg_type == 'json' or pg_type == 'jsonb' :
        return 'String'
        # return 'JSONType()'
    elif pg_type == 'email':
        return 'EmailType()'
    elif pg_type == 'url':
        return 'URLType()'
    elif pg_type == 'phone':
        return 'PhoneNumberType()'
    elif pg_type == 'color':
        return 'ColorType()'
    elif pg_type == 'choice':
        return 'ChoiceType()'
    else:
        return pg_type


def map_mysql_datatypes(mysql_type):
    """
    Maps a MySQL data type to a Flask-AppBuilder data type.
    """
    mysql_type = mysql_type.lower()
    if mysql_type.startswith('tinyint(1)'):
        return 'Boolean'
    elif mysql_type.startswith('tinyint') or mysql_type.startswith('smallint') or mysql_type.startswith(
            'mediumint') or mysql_type.startswith('int') or mysql_type.startswith('bigint') or mysql_type.startswith(
        'year'):
        return 'Integer'
    elif mysql_type.startswith('float') or mysql_type.startswith('double') or mysql_type.startswith('decimal'):
        return 'Numeric'
    elif mysql_type.startswith('char') or mysql_type.startswith('varchar') or mysql_type.startswith(
            'text') or mysql_type.startswith('mediumtext') or mysql_type.startswith('longtext'):
        return 'String'
    elif mysql_type.startswith('date') or mysql_type.startswith('datetime') or mysql_type.startswith(
            'timestamp') or mysql_type.startswith('time'):
        return 'DateTime'
    elif mysql_type.startswith('enum') or mysql_type.startswith('set'):
        return 'Enum'
    else:
        return 'String'


def map_oracle_datatypes(oracle_type):
    """
    Maps an Oracle data type to a Flask-AppBuilder data type.
    """
    oracle_type = oracle_type.upper()
    if oracle_type.startswith('NUMBER') or oracle_type.startswith('BINARY_FLOAT') or oracle_type.startswith(
            'BINARY_DOUBLE'):
        return 'Numeric'
    elif oracle_type.startswith('VARCHAR2') or oracle_type.startswith('NVARCHAR2') or oracle_type.startswith(
            'CHAR') or oracle_type.startswith('NCHAR') or oracle_type.startswith('CLOB') or oracle_type.startswith(
        'NCLOB'):
        return 'String'
    elif oracle_type.startswith('DATE') or oracle_type.startswith('TIMESTAMP') or oracle_type.startswith(
            'TIMESTAMP WITH TIME ZONE') or oracle_type.startswith('TIMESTAMP WITH LOCAL TIME ZONE'):
        return 'DateTime'
    elif oracle_type.startswith('INTERVAL YEAR TO MONTH') or oracle_type.startswith('INTERVAL DAY TO SECOND'):
        return 'Interval'
    elif oracle_type.startswith('FLOAT'):
        return 'Float'
    elif oracle_type.startswith('BLOB') or oracle_type.startswith('RAW') or oracle_type.startswith('LONG RAW'):
        return 'Binary'
    elif oracle_type.startswith('BOOLEAN'):
        return 'Boolean'
    else:
        return 'String'


def map_sqlite_datatypes(sqlite_type):
    """
    Maps a SQLite data type to a Flask-AppBuilder data type.
    """
    if sqlite_type.startswith('integer') or sqlite_type.startswith('tinyint') or sqlite_type.startswith(
            'smallint') or sqlite_type.startswith('mediumint') or sqlite_type.startswith(
        'int') or sqlite_type.startswith('bigint'):
        return 'Integer'
    elif sqlite_type.startswith('real') or sqlite_type.startswith('float') or sqlite_type.startswith(
            'double') or sqlite_type.startswith('decimal'):
        return 'Numeric'
    elif sqlite_type.startswith('char') or sqlite_type.startswith('varchar') or sqlite_type.startswith(
            'text') or sqlite_type.startswith('clob'):
        return 'String'
    elif sqlite_type.startswith('date') or sqlite_type.startswith('time') or sqlite_type.startswith('timestamp'):
        return 'DateTime'
    elif sqlite_type.startswith('blob') or sqlite_type.startswith('binary') or sqlite_type.startswith('varbinary'):
        return 'Binary'
    elif sqlite_type.startswith('boolean'):
        return 'Boolean'
    else:
        return 'String'


def pg_to_fabtypes(postgres_type):
    postgres_type = postgres_type.lower()
    type_mapping = {
        "bigint": "BigInteger",
        "bigserial": "BigInteger",
        "boolean": "Boolean",
        "box": "String",
        "bytea": "LargeBinary",
        "character": "String",
        "character varying": "String",
        "cidr": "String",
        "circle": "String",
        "date": "Date",
        "double precision": "Float",
        "inet": "String",
        "integer": "Integer",
        "interval": "Interval",
        "json": "JSON",
        "jsonb": "JSON",
        "line": "String",
        "lseg": "String",
        "macaddr": "String",
        "money": "Float",
        "numeric": "Numeric",
        "path": "String",
        "pg_lsn": "String",
        "point": "String",
        "polygon": "String",
        "real": "Float",
        "smallint": "SmallInteger",
        "smallserial": "SmallInteger",
        "serial": "Integer",
        "text": "Text",
        "time": "Time",
        "timestamp": "DateTime",
        "tsquery": "String",
        "tsvector": "String",
        "txid_snapshot": "String",
        "uuid": "String",
        "varchar": "String",
        "xml": "String",
    }
    return type_mapping.get(postgres_type.lower(), "String")


### Using Marshmallow
def get_marshmallow_field_type(column_type):
    type_mapping = {
        String: fields.Str(),
        Text: fields.Str(),
        Unicode: fields.Str(),
        UnicodeText: fields.Str(),
        BIGINT: fields.Int(),
        BIT: fields.Str(),  # or a custom field for bit strings
        BOOLEAN: fields.Bool(),
        BYTEA: fields.Str(),  # or a custom field for binary data
        CHAR: fields.Str(),
        CIDR: fields.Str(),  # or a custom field for network addresses
        CITEXT: fields.Str(),
        DATEMULTIRANGE: fields.List(fields.Date()),  # or a custom field for date ranges
        DATERANGE: fields.Raw(),  # or a custom field for date ranges
        DOMAIN: fields.Raw(),  # handle as per specific domain type
        DOUBLE_PRECISION: fields.Float(),
        ENUM: fields.Str(),  # or a custom field handling specific enums
        FLOAT: fields.Float(),
        HSTORE: fields.Dict(fields.Str(), fields.Str()),
        INET: fields.Str(),  # or a custom field for IP addresses
        INT4MULTIRANGE: fields.List(fields.Int()),  # or a custom field for integer ranges
        INT4RANGE: fields.Raw(),  # or a custom field for integer ranges
        INT8MULTIRANGE: fields.List(fields.Int()),  # or a custom field for integer ranges
        INT8RANGE: fields.Raw(),  # or a custom field for integer ranges
        INTERVAL: fields.TimeDelta(),
        NCHAR: fields.Str(),
        NVARCHAR: fields.Str(),
        VARCHAR: fields.Str(),  # Explicitly handling VARCHAR
        VARBINARY: fields.Str(),  # or a custom field for binary data
        BLOB: fields.Str(),  # or a custom field for binary data
        CLOB: fields.Str(),
        JSONB: fields.Raw(),  # or a custom field for JSONB data
        JSONPATH: fields.Str(),  # or a custom field for JSONPath expressions
        MACADDR: fields.Str(),  # or a custom field for MAC addresses
        MACADDR8: fields.Str(),  # or a custom field for MAC addresses
        MONEY: fields.Decimal(),  # or a custom field for monetary values
        NUMERIC: fields.Decimal(),
        NUMMULTIRANGE: fields.List(fields.Decimal()),  # or a custom field for numeric ranges
        NUMRANGE: fields.Raw(),  # or a custom field for numeric ranges
        OID: fields.Int(),  # or a custom field for object identifiers
        REAL: fields.Float(),
        REGCLASS: fields.Str(),  # or a custom field for regclass type
        REGCONFIG: fields.Str(),  # or a custom field for regconfig type
        SMALLINT: fields.Int(),
        TEXT: fields.Str(),
        TIME: fields.Time(),
        TIMESTAMP: fields.DateTime(),
        TSMULTIRANGE: fields.Raw(),  # or a custom field for timestamp ranges
        TSQUERY: fields.Str(),  # or a custom field for text search queries
        TSRANGE: fields.Raw(),  # or a custom field for timestamp ranges
        TSTZMULTIRANGE: fields.Raw(),  # or a custom field for timestamp with time zone ranges
        TSTZRANGE: fields.Raw(),  # or a custom field for timestamp with time zone ranges
        TSVECTOR: fields.Str(),  # or a custom field for text search vectors
        UUID: fields.UUID(),
        LargeBinary: fields.Str(),  # or a custom field for binary data
        # Binary: fields.Str(),  # or a custom field for binary data
        Integer: fields.Int(),
        BigInteger: fields.Int(),
        SmallInteger: fields.Int(),
        Float: fields.Float(),
        Numeric: fields.Float(),
        DECIMAL: fields.Float(),
        Boolean: fields.Bool(),
        DateTime: fields.DateTime(),
        Date: fields.Date(),
        DATE: fields.Date(),
        Time: fields.Time(),
        INTEGER: fields.Int(),
        Interval: fields.TimeDelta(),
        JSON: fields.Raw(),  # or a custom field for handling JSON
        ARRAY: fields.List(fields.Raw()),  # Adjust the inner field type as needed
        PickleType: fields.Raw(),  # or a custom field for serialized data
        Enum: fields.Str(),  # or a custom field for enum handling

        # Add other SQLAlchemy types and corresponding field types as needed.
    }
    return type_mapping.get(type(column_type))



# Remove columns that end in _id
def remove_id_columns(column_names):
    cleaned_names = []

    for name in column_names:

        if name.lower().endswith('_id_fkey'):
            # Remove _id_fkey and add
            cleaned_name = name.replace('_id_fkey', '')
            cleaned_names.append(cleaned_name)

        elif not name.endswith('_id'):
            cleaned_names.append(name)

    return cleaned_names




from sqlalchemy import String, Text

def get_display_column(columns):
    """
    Select an appropriate column or expression for display in __repr__ method.

    Args:
    columns (list): List of column dictionaries with 'name' and 'type' keys.

    Returns:
    tuple: (display_expr, is_expression)
        display_expr (str): Name of the selected display column or a custom expression.
        is_expression (bool): True if display_expr is a custom expression, False if it's a column name.
    """
    column_names = [col['name'] for col in columns]

    # Check for first_name and last_name combination
    if 'first_name' in column_names and 'last_name' in column_names:
        return 'f"{self.first_name} {self.last_name}"', True

    priority_names = [
        'name', 'full_name', 'username', 'email', 'title', 'label', 'code', 'slug',
        'description', 'display_name'
    ]

    # Check for priority names
    for name in priority_names:
        if name in column_names:
            return name, False

    # Check for custom naming patterns
    custom_patterns = [
        lambda x: x.endswith('_name'),
        lambda x: x.endswith('_title'),
        lambda x: x.endswith('_label'),
        lambda x: x.startswith('name_'),
        lambda x: x.startswith('title_'),
        lambda x: x.startswith('label_')
    ]

    for pattern in custom_patterns:
        matching_columns = [col['name'] for col in columns if pattern(col['name'])]
        if matching_columns:
            return matching_columns[0], False

    # Prefer string-based columns
    string_columns = [col['name'] for col in columns if isinstance(col['type'], (String, Text))]
    if string_columns:
        return string_columns[0], False

    # Fall back to the primary key or the first column
    primary_keys = [col['name'] for col in columns if col.get('primary_key', False)]
    if primary_keys:
        return primary_keys[0], False

    return columns[0]['name'], False

def is_association_table(table_name, inspector):
    """Improved detection of association tables.
    Check if a table is likely an association table.

    An association table typically has the following characteristics:
    0. The name ends in _assoc (our formal convention)
    1. Has at least two foreign keys
    2. May have additional columns for metadata (e.g., creation date, status)
    3. Usually has a relatively small number of columns compared to regular entity tables
    4. The name often follows a pattern like 'table1_table2' or 'table1_to_table2'

    Args:
            table_name (str): Name of the table to check
            inspector (sa.engine.reflection.Inspector): SQLAlchemy Inspector object

        Returns:
            bool: True if the table is likely an association table, False otherwise
    """
    if table_name.endswith("_assoc"):
        return True

    fks = inspector.get_foreign_keys(table_name)
    columns = inspector.get_columns(table_name)

    if len(fks) < 2:
        return False

    non_fk_columns = [col for col in columns if col['name'] not in
                      [c for fk in fks for c in fk['constrained_columns']]]

    # Allow for id, timestamps, and a couple of additional metadata columns
    allowed_extra = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']
    extra_columns = [col for col in non_fk_columns if col['name'] not in allowed_extra]

   # Check if the table name follows the pattern 'table1_table2' or 'table1_to_table2'
    name_parts = table_name.split('_')
    if len(name_parts) >= 2 and (name_parts[-1] in fks[0]['referred_table'] or name_parts[-1] in fks[1]['referred_table']):
        return True

    return len(extra_columns) <= 2
