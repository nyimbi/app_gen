import re

from marshmallow import fields
from sqlalchemy import (
    ARRAY,
    BLOB,
    BOOLEAN,
    CHAR,
    CLOB,
    DECIMAL,
    INTEGER,
    JSON,
    NCHAR,
    NUMERIC,
    NVARCHAR,
    TEXT,
    TIMESTAMP,
    VARBINARY,
    VARCHAR,
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    FetchedValue,
    Float,
    ForeignKey,
    Integer,
    Interval,
    LargeBinary,
    MetaData,
    Numeric,
    PickleType,
    SmallInteger,
    String,
    Text,
    Time,
    Unicode,
    UnicodeText,
    create_engine,
    inspect,
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
        "int": "Integer",
        "tinyint": "Integer",
        "smallint": "Integer",
        "mediumint": "Integer",
        "bigint": "BigInteger",
        "float": "Float",
        "double": "Float",
        "decimal": "Numeric",
        "numeric": "Numeric",
        "char": "String",
        "varchar": "String",
        "tinytext": "String",
        "text": "String",
        "mediumtext": "String",
        "longtext": "String",
        "date": "Date",
        "datetime": "DateTime",
        "timestamp": "DateTime",
        "time": "Time",
        "year": "Integer",
    }
    return mapping.get(datatype.lower(), datatype.title())


def map_pgsql_datatypes(pg_type: str) -> str:
    """
    Maps PostgreSQL-specific datatypes to SQLAlchemy types for use in Flask-AppBuilder model generation.

    This comprehensive function handles the conversion of PostgreSQL data types to their appropriate
    SQLAlchemy equivalents, supporting a wide range of native PostgreSQL types including arrays,
    ranges, network addresses, geometric types, full text search, and custom types.

    No external type mapping files or functions are required - all mappings are self-contained.

    Args:
        pg_type (str): The PostgreSQL datatype as a string (e.g. 'varchar', 'integer[]', 'jsonb')

    Returns:
        str: The corresponding SQLAlchemy type as a string (e.g. 'String', 'ARRAY(Integer)', 'JSON')

    Supported PostgreSQL Type Categories:
        - Basic Types (int, varchar, text, boolean, etc.)
        - Numeric Types (decimal, float, money, etc.)
        - Character Types (char, varchar, text)
        - Date/Time Types (timestamp, interval, etc.)
        - Array Types (int[], text[], etc.)
        - Range Types (daterange, numrange, etc.)
        - Network Address Types (inet, cidr, macaddr)
        - Geometric Types (point, line, polygon)
        - Full Text Search (tsvector, tsquery)
        - JSON Types (json, jsonb)
        - Binary Data Types (bytea, blob)
        - UUID Type
        - Custom Domain Types
        - Specialized Types (email, url, color, etc.)

    Examples:
        map_pgsql_datatypes('integer') -> 'Integer'
        map_pgsql_datatypes('character varying') -> 'String'
        map_pgsql_datatypes('integer[]') -> 'ARRAY(Integer)'
        map_pgsql_datatypes('numeric(10,2)') -> 'Numeric(precision=10,scale=2)'
    """
    # Convert to lowercase for case-insensitive matching
    pg_type = pg_type.lower().strip()

    # Type mapping dictionary for direct conversions
    type_map = {
        "bool": "Boolean",
        "boolean": "Boolean",
        "smallint": "SmallInteger",
        "integer": "Integer",
        "int": "Integer",
        "bigint": "BigInteger",
        "decimal": "Numeric",
        "numeric": "Numeric",
        "real": "Float",
        "float4": "Float",
        "float8": "Float",
        "double precision": "Float",
        "character varying": "String",
        "varchar": "String",
        "character": "String",
        "char": "String",
        "text": "Text",
        "citext": "Text",
        "json": "JSON",
        "jsonb": "JSON",
        "date": "Date",
        "time": "Time",
        "timetz": "Time",
        "timestamp": "DateTime",
        "timestamptz": "DateTime",
        "interval": "Interval",
        "bytea": "LargeBinary",
        "blob": "LargeBinary",
        "uuid": "UUID",
        "money": "Numeric",
    }

    # Handle array types first
    if pg_type.endswith("[]"):
        base_type = map_pgsql_datatypes(pg_type[:-2])
        return f"ARRAY({base_type})"

    # Handle numeric types with precision/scale
    if pg_type.startswith(("numeric", "decimal")):
        match = re.match(r"(?:numeric|decimal)\s*\((\d+)(?:,\s*(\d+))?\)", pg_type)
        if match:
            precision = int(match.group(1))
            scale = int(match.group(2)) if match.group(2) else 0
            return f"Numeric(precision={precision}, scale={scale})"

    # Handle character types with length
    if pg_type.startswith(("character varying", "varchar", "char")):
        match = re.match(r"(?:character varying|varchar|char)\s*\((\d+)\)", pg_type)
        if match:
            length = int(match.group(1))
            return f"String(length={length})"

    # Handle range types
    range_types = {
        "daterange": "DateRangeType",
        "tsrange": "DateTimeRangeType",
        "tstzrange": "DateTimeRangeType",
        "numrange": "NumericRangeType",
        "int4range": "IntegerRangeType",
        "int8range": "BigIntegerRangeType",
    }
    if pg_type in range_types:
        return range_types[pg_type]

    # Handle network address types
    if pg_type in ("inet", "cidr"):
        return "IPAddressType()"
    if pg_type in ("macaddr", "macaddr8"):
        return "MACAddressType()"

    # Handle geometric types
    geometric_types = ("point", "line", "lseg", "box", "path", "polygon", "circle")
    if pg_type in geometric_types:
        return f"Geometry({pg_type.upper()})"

    # Handle full text search types
    if pg_type == "tsvector":
        return "TSVectorType()"
    if pg_type == "tsquery":
        return "TSQueryType()"

    # Handle specialized types
    specialized_types = {
        "email": "EmailType()",
        "url": "URLType()",
        "phone": "PhoneNumberType()",
        "color": "ColorType()",
        "choice": "ChoiceType()",
    }
    if pg_type in specialized_types:
        return specialized_types[pg_type]

    # Check basic type map
    if pg_type in type_map:
        return type_map[pg_type]

    # Special cases for serial types
    if pg_type in ("serial", "serial4"):
        return "Integer"
    if pg_type in ("bigserial", "serial8"):
        return "BigInteger"
    if pg_type == "smallserial":
        return "SmallInteger"

    # Default fallback - return as String type
    return "String"


def map_mysql_datatypes(mysql_type):
    """
    Maps a MySQL data type to a Flask-AppBuilder data type.
    """
    mysql_type = mysql_type.lower()
    if mysql_type.startswith("tinyint(1)"):
        return "Boolean"
    elif (
        mysql_type.startswith("tinyint")
        or mysql_type.startswith("smallint")
        or mysql_type.startswith("mediumint")
        or mysql_type.startswith("int")
        or mysql_type.startswith("bigint")
        or mysql_type.startswith("year")
    ):
        return "Integer"
    elif (
        mysql_type.startswith("float")
        or mysql_type.startswith("double")
        or mysql_type.startswith("decimal")
    ):
        return "Numeric"
    elif (
        mysql_type.startswith("char")
        or mysql_type.startswith("varchar")
        or mysql_type.startswith("text")
        or mysql_type.startswith("mediumtext")
        or mysql_type.startswith("longtext")
    ):
        return "String"
    elif (
        mysql_type.startswith("date")
        or mysql_type.startswith("datetime")
        or mysql_type.startswith("timestamp")
        or mysql_type.startswith("time")
    ):
        return "DateTime"
    elif mysql_type.startswith("enum") or mysql_type.startswith("set"):
        return "Enum"
    else:
        return "String"


def map_oracle_datatypes(oracle_type):
    """
    Maps an Oracle data type to a Flask-AppBuilder data type.
    """
    oracle_type = oracle_type.upper()
    if (
        oracle_type.startswith("NUMBER")
        or oracle_type.startswith("BINARY_FLOAT")
        or oracle_type.startswith("BINARY_DOUBLE")
    ):
        return "Numeric"
    elif (
        oracle_type.startswith("VARCHAR2")
        or oracle_type.startswith("NVARCHAR2")
        or oracle_type.startswith("CHAR")
        or oracle_type.startswith("NCHAR")
        or oracle_type.startswith("CLOB")
        or oracle_type.startswith("NCLOB")
    ):
        return "String"
    elif (
        oracle_type.startswith("DATE")
        or oracle_type.startswith("TIMESTAMP")
        or oracle_type.startswith("TIMESTAMP WITH TIME ZONE")
        or oracle_type.startswith("TIMESTAMP WITH LOCAL TIME ZONE")
    ):
        return "DateTime"
    elif oracle_type.startswith("INTERVAL YEAR TO MONTH") or oracle_type.startswith(
        "INTERVAL DAY TO SECOND"
    ):
        return "Interval"
    elif oracle_type.startswith("FLOAT"):
        return "Float"
    elif (
        oracle_type.startswith("BLOB")
        or oracle_type.startswith("RAW")
        or oracle_type.startswith("LONG RAW")
    ):
        return "Binary"
    elif oracle_type.startswith("BOOLEAN"):
        return "Boolean"
    else:
        return "String"


def map_sqlite_datatypes(sqlite_type):
    """
    Maps a SQLite data type to a Flask-AppBuilder data type.
    """
    if (
        sqlite_type.startswith("integer")
        or sqlite_type.startswith("tinyint")
        or sqlite_type.startswith("smallint")
        or sqlite_type.startswith("mediumint")
        or sqlite_type.startswith("int")
        or sqlite_type.startswith("bigint")
    ):
        return "Integer"
    elif (
        sqlite_type.startswith("real")
        or sqlite_type.startswith("float")
        or sqlite_type.startswith("double")
        or sqlite_type.startswith("decimal")
    ):
        return "Numeric"
    elif (
        sqlite_type.startswith("char")
        or sqlite_type.startswith("varchar")
        or sqlite_type.startswith("text")
        or sqlite_type.startswith("clob")
    ):
        return "String"
    elif (
        sqlite_type.startswith("date")
        or sqlite_type.startswith("time")
        or sqlite_type.startswith("timestamp")
    ):
        return "DateTime"
    elif (
        sqlite_type.startswith("blob")
        or sqlite_type.startswith("binary")
        or sqlite_type.startswith("varbinary")
    ):
        return "Binary"
    elif sqlite_type.startswith("boolean"):
        return "Boolean"
    else:
        return "String"


def pg_to_fabtypes(postgres_type):
    """
    Comprehensively maps PostgreSQL data types to Flask-AppBuilder model field types.

    This function handles conversion of PostgreSQL data types to their appropriate
    Flask-AppBuilder/SQLAlchemy model field types. It includes comprehensive support for:

    - Basic types (int, varchar, text, boolean, etc.)
    - Numeric types with precision/scale
    - Character types with length specifications
    - Date/Time types with timezone variants
    - Array types (recursively mapped)
    - Network address types
    - Geometric types
    - JSON types
    - Binary data types
    - UUID/XML/Other specialized types
    - Range and multirange types
    - Domain and enum types
    - Custom types

    The function is self-contained with no external dependencies beyond standard regex.
    It aims to be exhaustive in type coverage while providing safe fallbacks.

    Args:
        postgres_type (str): PostgreSQL data type name (e.g. 'varchar(255)', 'integer[]',
                           'numeric(10,2)', 'timestamp with time zone')

    Returns:
        str: Flask-AppBuilder/SQLAlchemy field type specification as a string
             (e.g. 'String(255)', 'Integer', 'Numeric(precision=10,scale=2)')

    Examples:
        >>> pg_to_fabtypes('varchar(50)')
        'String(50)'
        >>> pg_to_fabtypes('numeric(10,2)')
        'Numeric(precision=10,scale=2)'
        >>> pg_to_fabtypes('integer[]')
        'List(Integer)'
        >>> pg_to_fabtypes('timestamp with time zone')
        'DateTime'
    """
    if not postgres_type:
        return "String"

    # Normalize type string
    postgres_type = postgres_type.lower().strip()

    # Handle array types first
    if postgres_type.endswith("[]"):
        base = pg_to_fabtypes(postgres_type[:-2])
        return f"List({base})"

    # Extract type and any parameters
    match = re.match(
        r"([a-z_\s]+(?:\s+(?:with|without)\s+(?:time\s+)?zone)?)"  # Base type including time zones
        r"(?:\((\d+)(?:,\s*(\d+))?\))?"  # Optional length/precision
        r"(\[\])?",  # Array suffix
        postgres_type,
    )

    if not match:
        return "String"

    base_type = match.group(1).strip()
    length = match.group(2)
    scale = match.group(3)
    is_array = bool(match.group(4))

    # Comprehensive type mapping dictionary
    type_mapping = {
        # Numeric types
        "bigint": "BigInteger",
        "bigserial": "BigInteger",
        "integer": "Integer",
        "int": "Integer",
        "int4": "Integer",
        "int8": "BigInteger",
        "smallint": "SmallInteger",
        "smallserial": "SmallInteger",
        "serial": "Integer",
        "serial4": "Integer",
        "serial8": "BigInteger",
        "decimal": "Numeric",
        "double precision": "Float",
        "real": "Float",
        "float4": "Float",
        "float8": "Float",
        "money": "Numeric",
        "numeric": "Numeric",
        # Character types
        "character": "String",
        "char": "String",
        "character varying": "String",
        "varchar": "String",
        "text": "Text",
        "citext": "Text",
        # Date/Time types
        "date": "Date",
        "time": "Time",
        "time without time zone": "Time",
        "time with time zone": "Time",
        "timetz": "Time",
        "timestamp": "DateTime",
        "timestamp without time zone": "DateTime",
        "timestamp with time zone": "DateTime",
        "timestamptz": "DateTime",
        "interval": "Interval",
        # Boolean type
        "boolean": "Boolean",
        "bool": "Boolean",
        # Binary data
        "bytea": "LargeBinary",
        "blob": "LargeBinary",
        "binary": "LargeBinary",
        # Network address types
        "inet": "String",
        "cidr": "String",
        "macaddr": "String",
        "macaddr8": "String",
        # Geometric types
        "box": "String",
        "circle": "String",
        "line": "String",
        "lseg": "String",
        "path": "String",
        "point": "String",
        "polygon": "String",
        # JSON types
        "json": "JSON",
        "jsonb": "JSON",
        # Full text search
        "tsvector": "String",
        "tsquery": "String",
        # UUID type
        "uuid": "String",
        # XML type
        "xml": "String",
        # Other types
        "pg_lsn": "String",
        "txid_snapshot": "String",
        # Range types
        "daterange": "String",
        "tsrange": "String",
        "tstzrange": "String",
        "numrange": "String",
        "int4range": "String",
        "int8range": "String",
        # Multirange types
        "datemultirange": "String",
        "tsmultirange": "String",
        "tstzmultirange": "String",
        "nummultirange": "String",
        "int4multirange": "String",
        "int8multirange": "String",
        # Domain types default to underlying type or String
        "domain": "String",
        # Custom types
        "hstore": "JSON",
        "ltree": "String",
        "cube": "String",
    }

    # Special handling for types with parameters
    if base_type in ("numeric", "decimal") and length:
        precision = length
        if scale:
            return f"Numeric(precision={precision},scale={scale})"
        return f"Numeric(precision={precision})"

    if base_type in ("character", "char", "character varying", "varchar") and length:
        return f"String(length={length})"

    if base_type.startswith("time") or base_type.startswith("timestamp"):
        # Normalize timestamp/time with/without timezone to basic types
        if "timestamp" in base_type:
            return "DateTime"
        return "Time"

    # Get mapped type with fallback to String
    fab_type = type_mapping.get(base_type, "String")

    # Handle array types
    if is_array:
        return f"List({fab_type})"

    return fab_type


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
        INT4MULTIRANGE: fields.List(
            fields.Int()
        ),  # or a custom field for integer ranges
        INT4RANGE: fields.Raw(),  # or a custom field for integer ranges
        INT8MULTIRANGE: fields.List(
            fields.Int()
        ),  # or a custom field for integer ranges
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
        NUMMULTIRANGE: fields.List(
            fields.Decimal()
        ),  # or a custom field for numeric ranges
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
    """
    Remove ID suffix columns and clean up foreign key references while preserving meaningful names.

    Args:
        column_names (list): List of column names to process

    Returns:
        list: Cleaned column names with ID suffixes and foreign key references removed
    """
    cleaned_names = []
    seen_names = set()

    for name in column_names:
        cleaned_name = name.lower()

        # Handle various ID column patterns
        if cleaned_name.endswith("_id_fkey"):
            # Remove foreign key suffix
            cleaned_name = name.replace("_id_fkey", "")
        elif cleaned_name.endswith("_fkey"):
            # Remove just the foreign key indicator
            cleaned_name = name.replace("_fkey", "")
        elif cleaned_name.endswith("_id"):
            # Remove ID suffix
            cleaned_name = name[:-3]
        elif "_id_" in cleaned_name:
            # Handle embedded ID references
            cleaned_name = cleaned_name.replace("_id_", "_")
        elif cleaned_name == "id":
            # Skip standalone ID columns
            continue
        else:
            # Keep original name if no ID pattern matched
            cleaned_name = name

        # Handle compound foreign key names
        parts = cleaned_name.split("_")
        if len(parts) > 1 and parts[-1].isdigit():
            cleaned_name = "_".join(parts[:-1])

        # Ensure we don't add duplicates
        if cleaned_name and cleaned_name not in seen_names:
            seen_names.add(cleaned_name)
            cleaned_names.append(cleaned_name)

    return cleaned_names


from sqlalchemy import String, Text


def get_display_column(columns):
    """
    Select an appropriate column or expression for display in __repr__ method.

    This function analyzes a table's columns to intelligently select the most meaningful
    display representation for use in generated __repr__ methods. It employs multiple
    sophisticated heuristics to identify suitable display columns or construct composite
    expressions.

    The function evaluates columns in order of decreasing semantic value:
    1. Common name combinations (first/last name, etc)
    2. Standard descriptive fields (name, title, label etc)
    3. Domain-specific identifiers and common patterns
    4. String/text columns with NOT NULL constraints
    5. Meaningful column combinations
    6. Primary keys and unique identifiers as fallback

    Args:
        columns (list): List of column dictionaries containing:
            - name (str): Column name
            - type (TypeEngine): SQLAlchemy column type
            - primary_key (bool): True if column is part of primary key
            - nullable (bool): True if column allows NULL values
            - foreign_keys (list): Foreign key references if any
            - unique (bool): True if column has unique constraint
            - default (Any): Default value if specified
            - comment (str): Column comment/description if any
            - autoincrement (bool): True if auto-incrementing
            - constraints (list): Any additional constraints

    Returns:
        tuple: (display_expr, is_expression)
            display_expr (str): Column name or f-string expression for __repr__
            is_expression (bool): True if result is an f-string expression,
                                False if plain column name

    Examples:
        >>> cols = [{"name": "first_name"}, {"name": "last_name"}]
        >>> get_display_column(cols)
        ('f"{self.first_name} {self.last_name}"', True)

        >>> cols = [{"name": "title", "type": String()}]
        >>> get_display_column(cols)
        ('title', False)
    """
    column_names = [col["name"] for col in columns]

    # Check for common personal name combinations
    name_combinations = [
        ("first_name", "last_name", 'f"{self.first_name} {self.last_name}"'),
        ("given_name", "family_name", 'f"{self.given_name} {self.family_name}"'),
        ("first", "last", 'f"{self.first} {self.last}"'),
        ("fname", "lname", 'f"{self.fname} {self.lname}"'),
        ("forename", "surname", 'f"{self.forename} {self.surname}"'),
        ("christian_name", "surname", 'f"{self.christian_name} {self.surname}"'),
        ("first_name", "middle_name", "last_name", 'f"{self.first_name} {self.middle_name} {self.last_name}"'),
        ("first_name", "middle_initial", "last_name", 'f"{self.first_name} {self.middle_initial}. {self.last_name}"'),
    ]

    # Check multi-part name combinations first
    for combo in name_combinations:
        if len(combo) == 3:  # Two column names plus expression
            if combo[0] in column_names and combo[1] in column_names:
                return combo[2], True
        elif len(combo) == 4:  # Three column names plus expression
            if all(c in column_names for c in combo[0:3]):
                return combo[3], True

    # Priority single column names by semantic importance
    priority_names = [
        "name",
        "full_name",
        "display_name",
        "username",
        "user_name",
        "email",
        "email_address",
        "title",
        "label",
        "code",
        "slug",
        "description",
        "short_description",
        "long_description",
        "identifier",
        "reference",
        "reference_number",
        "ref_num",
        "key",
        "public_id",
        "external_id",
        "account_number",
        "customer_number",
        "product_code",
        "sku",
        "article_number",
        "serial_number"
    ]

    # Check priority names with exact match
    for name in priority_names:
        if name in column_names:
            return name, False

    # Check priority names with case insensitive match
    column_names_lower = [c.lower() for c in column_names]
    for name in priority_names:
        if name.lower() in column_names_lower:
            idx = column_names_lower.index(name.lower())
            return column_names[idx], False

    # Business domain specific identifier patterns
    domain_patterns = [
        # Suffix patterns
        lambda x: x.endswith(("_name", "_title", "_label", "_code", "_ref", "_id", "_num",
                            "_key", "_identifier", "_description", "_text")),
        # Prefix patterns
        lambda x: x.startswith(("name_", "title_", "label_", "code_", "ref_", "id_",
                              "num_", "key_", "identifier_", "description_")),
        # Contains patterns
        lambda x: any(term in x.lower() for term in ["name", "title", "label", "code",
                                                    "identifier", "reference", "number",
                                                    "description", "text", "display"]),
        # Common business identifiers
        lambda x: any(term in x.lower() for term in ["account", "customer", "product",
                                                    "order", "invoice", "contract",
                                                    "project", "ticket", "case"])
    ]

    # Try each pattern in order
    for pattern in domain_patterns:
        matching = [col["name"] for col in columns if pattern(col["name"])]
        if matching:
            # Prefer non-null columns if available
            non_null = [c for c in matching if not [col for col in columns
                       if col["name"] == c and col.get("nullable", True)]]
            return (non_null[0] if non_null else matching[0]), False

    # Analyze column types and constraints - prefer non-nullable strings
    string_columns = [
        col["name"] for col in columns
        if isinstance(col["type"], (String, Text, Unicode, UnicodeText))
        and not col.get("nullable", True)
    ]
    if string_columns:
        return string_columns[0], False

    # Try to combine related columns meaningfully
    column_combinations = [
        # Description combinations
        ("short_description", "long_description"),
        ("description", "details"),
        ("summary", "description"),
        # Address combinations
        ("street", "city"),
        ("address_line_1", "city"),
        ("street_address", "city"),
        # Product combinations
        ("product_name", "product_code"),
        ("item_name", "item_code"),
        # Status combinations
        ("status", "status_description"),
        ("state", "state_description")
    ]

    for col1, col2 in column_combinations:
        if col1 in column_names and col2 in column_names:
            return f'f"{{self.{col1}}} - {{self.{col2}}}"', True

    # Fall back to unique identifiers
    primary_keys = [col["name"] for col in columns if col.get("primary_key")]
    if len(primary_keys) == 1:  # Only use single primary key
        return primary_keys[0], False

    unique_columns = [
        col["name"] for col in columns
        if col.get("unique") or "unique" in col["name"].lower()
    ]
    if unique_columns:
        return unique_columns[0], False

    # If all else fails, use first non-primary-key column
    non_pk_columns = [c["name"] for c in columns if not c.get("primary_key")]
    if non_pk_columns:
        return non_pk_columns[0], False

    # Ultimate fallback - first column
    return columns[0]["name"], False


def is_association_table(table_name, inspector):
    """Enhanced detection of association tables with multiple heuristics.

    This function determines if a table is likely an association/junction table by
    analyzing its structure, naming patterns, and relationships. It uses multiple
    heuristics including naming conventions, foreign key analysis, column patterns,
    and metadata characteristics.

    Characteristics checked:
    1. Naming conventions (_assoc, _junction, _map, _link suffixes)
    2. Multiple foreign key constraints (minimum 2)
    3. Column count and types analysis
    4. Relationship metadata patterns
    5. Primary key composition
    6. Table name patterns matching related tables
    7. Common metadata columns allowance
    8. Composite key analysis
    9. Column naming patterns
    10. Referenced table relationship checks
    11. Index analysis
    12. Column type patterns
    13. Referential action patterns
    14. Bridge table discovery
    15. Cross-reference validation

    Args:
        table_name (str): Name of the table to analyze
        inspector (sa.engine.reflection.Inspector): SQLAlchemy Inspector object

    Returns:
        bool: True if table matches association table patterns, False otherwise
    """
    # Check naming convention suffixes
    association_suffixes = (
        "_assoc",
        "_junction",
        "_map",
        "_link",
        "_bridge",
        "_join",
        "_xref",
        "_rel",
        "_relationship",
        "_mapping",
    )
    if any(table_name.endswith(suffix) for suffix in association_suffixes):
        return True

    # Get table structure details
    fks = inspector.get_foreign_keys(table_name)
    columns = inspector.get_columns(table_name)
    pks = inspector.get_pk_constraint(table_name)
    unique_constraints = inspector.get_unique_constraints(table_name)
    indices = inspector.get_indexes(table_name)

    # Require minimum number of foreign keys
    if len(fks) < 2:
        return False

    # Identify non-foreign key columns
    non_fk_columns = [
        col
        for col in columns
        if col["name"] not in [c for fk in fks for c in fk["constrained_columns"]]
    ]

    # Standard metadata columns to allow
    allowed_extra = [
        "id",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "valid_from",
        "valid_to",
        "version",
        "status",
        "active",
        "deleted",
        "sort_order",
        "display_order",
        "priority",
        "enabled",
        "is_default",
        "notes",
        "description",
        "metadata",
        "properties",
        "attributes",
    ]

    # Count true extra columns (non-FK, non-metadata)
    extra_columns = [
        col for col in non_fk_columns if col["name"].lower() not in allowed_extra
    ]

    # Analyze primary key composition
    pk_is_composite = len(pks["constrained_columns"]) > 1
    pk_columns = set(pks["constrained_columns"])
    fk_columns = set(c for fk in fks for c in fk["constrained_columns"])

    # Check if PK is composed entirely of FKs
    pk_matches_fks = pk_columns.issubset(fk_columns)

    # Check referential actions
    cascade_actions = ["CASCADE", "SET NULL", "SET DEFAULT"]
    has_cascade = any(fk.get("ondelete", "") in cascade_actions for fk in fks)

    # Analyze index patterns
    fk_indices = [
        idx for idx in indices if set(idx["column_names"]).issubset(fk_columns)
    ]
    has_covering_indices = len(fk_indices) >= len(fks)

    # Check table naming patterns
    name_parts = table_name.lower().split("_")
    referred_tables = [fk["referred_table"].lower() for fk in fks]

    # Enhanced pattern matching including "to", "has", "with" connectors
    connecting_words = ["to", "has", "with", "for", "by", "in", "on"]
    filtered_parts = [p for p in name_parts if p not in connecting_words]

    table_pattern_match = len(filtered_parts) >= 2 and any(
        part in referred_tables for part in filtered_parts
    )

    # Check column type patterns
    column_types = [col["type"].__class__.__name__ for col in columns]
    simple_types = all(
        t in ["Integer", "BigInteger", "SmallInteger"] for t in column_types
    )

    # Advanced heuristics for association table detection
    is_association = any(
        [
            # Composite key made of foreign keys
            (pk_is_composite and pk_matches_fks),
            # Simple join table with minimal extra columns
            (len(extra_columns) <= 2 and len(fks) >= 2),
            # Table name references both joined tables
            table_pattern_match and len(referred_tables) >= 2,
            # Has exactly required columns for many-to-many with metadata
            (len(columns) <= len(fks) + len(allowed_extra)),
            # All unique constraints involve foreign key columns
            all(
                set(uc["column_names"]).issubset(fk_columns)
                for uc in unique_constraints
            ),
            # Has appropriate index coverage
            has_covering_indices and simple_types,
            # Uses cascading referential actions
            has_cascade and len(fks) == 2,
            # Perfect bridge table pattern
            len(columns) == len(fks) and pk_is_composite,
        ]
    )

    return is_association
